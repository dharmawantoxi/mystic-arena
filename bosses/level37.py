"""
bosses/level37.py - Semua boss Level 37

Berisi:
  - kazreth    (mini boss - MELEE blood reaver, demon wings)
  - varkuthar  (mini boss - MELEE bloodfire zealot)
  - zhyvrek    (mini boss - MELEE void reaper)
  - xelnarath  (TRUE BOSS - RANGED void sovereign, void wings)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _zv_ (zhyvrek), _xn_ (xelnarath) sudah unik.
  - _kz_ (kazreth) di-rename -> _kzt_ (bentrok dengan khalzaredh
    level 24), termasuk atribut _last_x/_last_y.
  - _vk_ (varkuthar) di-rename -> _vkt_ (bentrok dengan vulkareth
    level 25 & valekris level 33), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KAZRETH (BLOOD REAVER) - Mini Boss
# ====================================================================

class _NS_kazreth:
    """Namespace kazreth - Blood Reaver demon boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark armor (charcoal/black)
        "armor_darkest": (5, 3, 5),
        "armor_dark": (18, 12, 15),
        "armor_mid": (40, 30, 35),
        "armor_light": (80, 65, 70),
        "armor_shine": (140, 120, 125),
        # Blood red glow (cracks, blade, magic)
        "blood_darkest": (30, 3, 5),
        "blood_dark": (80, 10, 15),
        "blood_mid": (170, 25, 30),
        "blood_light": (230, 60, 55),
        "blood_hot": (255, 120, 100),
        "blood_shine": (255, 200, 170),
        # Wing membrane (dark red translucent)
        "membrane_dark": (30, 8, 12),
        "membrane_mid": (75, 20, 25),
        "membrane_light": (145, 40, 45),
        "membrane_glow": (210, 70, 65),
        # Bone/spike (aged dark bone)
        "bone_dark": (30, 25, 25),
        "bone_mid": (85, 75, 70),
        "bone_light": (160, 145, 135),
        "bone_shine": (220, 205, 190),
        # Eye (bright red demon eye)
        "eye_socket": (10, 2, 3),
        "eye_dark": (60, 5, 10),
        "eye_mid": (200, 30, 30),
        "eye_light": (255, 90, 70),
        "eye_glow": (255, 200, 160),
        # Sword blade (dark metal with red core)
        "blade_dark": (25, 20, 25),
        "blade_mid": (65, 55, 60),
        "blade_light": (130, 115, 120),
        "blade_shine": (210, 195, 195),
        # Ember/fire particles
        "ember_dark": (60, 15, 5),
        "ember_mid": (200, 60, 20),
        "ember_hot": (255, 140, 40),
        "ember_shine": (255, 230, 150),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 2),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kazreth._clamp(color)
        if _NS_kazreth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kazreth._clamp(color)
        if _NS_kazreth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_kazreth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kazreth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kazreth._detect_moving(boss)
        _NS_kazreth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kzt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_kazreth._draw_blood_aura(surface, x, y, pulse)
        _NS_kazreth._draw_ground_rift(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX
        if active_skill == "w":
            _NS_kazreth._draw_chains_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kazreth._draw_shadowstep_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kazreth._draw_apocalypse_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating - though heavy demon, gives ominous vibe)
        if attacking:
            _NS_kazreth._draw_kzt_attack(surface, boss, x, y)
        elif moving:
            _NS_kazreth._draw_kzt_float_move(surface, boss, x, y)
        else:
            _NS_kazreth._draw_kzt_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_kazreth._draw_crimson_reaver(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kazreth._draw_chains_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kazreth._draw_shadowstep_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kazreth._draw_apocalypse_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kzt_previous_timer", 0))
        active = bool(getattr(boss, "_kzt_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kzt_attack_active = True
            boss._kzt_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kzt_attack_frame = int(getattr(boss, "_kzt_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kzt_attack_active = False
            boss._kzt_attack_frame = 0
            active = False
        boss._kzt_previous_timer = timer
        boss._kzt_attack_progress = (
            min(1.0, getattr(boss, "_kzt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kzt_last_x"):
            boss._kzt_last_x = boss.x
            boss._kzt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kzt_last_x)
        dy = abs(boss.y - boss._kzt_last_y)
        boss._kzt_last_x = boss.x
        boss._kzt_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_kzt_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.45) * 4)
        _NS_kazreth._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_kazreth._draw_blood_embers(surface, x, y + 40, boss.pulse)
        _NS_kazreth._draw_kzt_body(surface, x, y + bob,
                                   boss.direction, boss.pulse, "idle")
    def _draw_kzt_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.4
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_kazreth._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_kazreth._draw_blood_embers(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_kazreth._draw_kzt_body(surface, x + sway, y + bob,
                                   boss.direction, phase, "float")
    def _draw_kzt_attack(surface, boss, x, y):
        """Great sword horizontal swing animation."""
        progress = getattr(boss, "_kzt_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up (pull sword back) → swing forward → recovery
        if progress < 0.35:
            t = progress / 0.35
            body_shift = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            t = (progress - 0.35) / 0.3
            body_shift = int((-5 + t * 16)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.65) / 0.35
            body_shift = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.45) * 3)
        _NS_kazreth._draw_float_shadow(surface, x + body_shift, y + 52, boss.pulse)
        _NS_kazreth._draw_blood_embers(surface, x + body_shift, y + 40, boss.pulse,
                                        intense=True)
        _NS_kazreth._draw_kzt_body(surface, x + body_shift, y - lift + bob,
                                   boss.direction, boss.pulse, "attack", progress)
        # Sword swing arc
        _NS_kazreth._draw_sword_swing_arc(surface, boss, x + body_shift,
                                           y - lift + bob, progress)
    # ============================================================
    # BODY - Darkin Demon (wings, armor body, greatsword, horned head)
    # ============================================================
    def _draw_kzt_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Darkin demon: wings, armored torso, arms with sword, horned head."""
        # Wings first (behind)
        _NS_kazreth._draw_demon_wings(surface, cx, cy - 6, facing, phase, action,
                                       attack_progress)
        # Trailing dark cloth/tail
        _NS_kazreth._draw_dark_cloth(surface, cx, cy + 8, facing, phase)
        # Legs/lower body (armored)
        _NS_kazreth._draw_lower_body(surface, cx, cy + 4, facing, phase)
        # Torso armor
        _NS_kazreth._draw_torso_armor(surface, cx, cy - 6, facing, phase)
        # Arms + greatsword (main weapon)
        sword_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                sword_swing = -int(attack_progress / 0.35 * 10) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.35) / 0.3
                sword_swing = int((-10 + t * 26)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                sword_swing = int(16 * (1 - t)) * facing
        _NS_kazreth._draw_arms_and_sword(surface, cx, cy - 4, facing, phase,
                                          sword_swing, action, attack_progress)
        # Head with horns
        _NS_kazreth._draw_demon_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_demon_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Massive bat-like demon wings."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 0.7) * 3
        # Draw both wings (far bigger, near partial)
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),
            (1, 0.72, 0.72),
        ]):
            base_x = cx - facing * 5
            base_y = cy - 4
            # 4 spars forming bat-wing
            spar_configs = [
                (math.pi * 0.7, 40),   # top spar (tallest)
                (math.pi * 0.92, 46),  # second (widest reach)
                (math.pi * 1.12, 40),  # third
                (math.pi * 1.32, 30),  # bottom short
            ]
            tips = []
            for angle_off, base_len in spar_configs:
                spar_len = int(base_len * size_mult)
                spar_angle = angle_off * side_mult - math.radians(beat)
                tip_x = base_x + int(math.cos(spar_angle) * spar_len) * (-facing)
                tip_y = base_y - int(math.sin(spar_angle) * spar_len)
                tips.append((tip_x, tip_y))
            # Membrane shape with jagged edges (dips between spars)
            def midpoint_dip(a, b, dip):
                return (int((a[0] + b[0]) / 2),
                        int((a[1] + b[1]) / 2) + int(dip * size_mult))
            membrane_points = [
                (base_x, base_y),
                tips[0],
                midpoint_dip(tips[0], tips[1], 5),
                tips[1],
                midpoint_dip(tips[1], tips[2], 6),
                tips[2],
                midpoint_dip(tips[2], tips[3], 5),
                tips[3],
                (base_x - facing * 4, base_y + int(7 * size_mult)),
            ]
            wing_surf = pygame.Surface((220, 140), pygame.SRCALPHA)
            offset_x = base_x - 110
            offset_y = base_y - 70
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]
            # Shadow layer
            _NS_kazreth._poly(wing_surf,
                              (*_NS_kazreth.PALETTE["shadow_deep"],
                               int(220 * alpha_mult)),
                              [(p[0] + 2, p[1] + 2) for p in local_points])
            # Base dark
            _NS_kazreth._poly(wing_surf,
                              (*_NS_kazreth.PALETTE["armor_darkest"],
                               int(240 * alpha_mult)),
                              local_points)
            # Inner darker fill
            cx_l = sum(p[0] for p in local_points) / len(local_points)
            cy_l = sum(p[1] for p in local_points) / len(local_points)
            inner_pts = []
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_l * 0.18),
                     int(p[1] * 0.82 + cy_l * 0.18))
                )
            _NS_kazreth._poly(wing_surf,
                              (*_NS_kazreth.PALETTE["membrane_dark"],
                               int(220 * alpha_mult)),
                              inner_pts)
            # Mid membrane
            inner_pts2 = []
            for p in local_points:
                inner_pts2.append(
                    (int(p[0] * 0.62 + cx_l * 0.38),
                     int(p[1] * 0.62 + cy_l * 0.38))
                )
            _NS_kazreth._poly(wing_surf,
                              (*_NS_kazreth.PALETTE["membrane_mid"],
                               int(160 * alpha_mult)),
                              inner_pts2)
            # Wing bones (spars) - dark with red glow
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip_p in tips:
                tp = (tip_p[0] - offset_x, tip_p[1] - offset_y)
                # Bone shadow
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["shadow_deep"],
                                  int(240 * alpha_mult)),
                                 (bone_base[0] + 1, bone_base[1] + 1),
                                 (tp[0] + 1, tp[1] + 1), 4)
                # Bone dark
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["armor_darkest"],
                                  int(255 * alpha_mult)),
                                 bone_base, tp, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["armor_dark"],
                                  int(255 * alpha_mult)),
                                 bone_base, tp, 2)
                # Red glowing crack along bone
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["blood_dark"],
                                  int(230 * alpha_mult)),
                                 bone_base, tp, 1)
                # Sharp claw at tip
                perp_a = math.atan2(tp[1] - bone_base[1], tp[0] - bone_base[0])
                hook_len = 5
                hook_x = tp[0] + int(math.cos(perp_a + math.pi * 0.3) * hook_len)
                hook_y = tp[1] + int(math.sin(perp_a + math.pi * 0.3) * hook_len)
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["armor_darkest"],
                                  int(240 * alpha_mult)),
                                 tp, (hook_x, hook_y), 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["bone_dark"],
                                  int(240 * alpha_mult)),
                                 tp, (hook_x, hook_y), 1)
                # Bright claw tip
                _NS_kazreth._aacircle(wing_surf,
                                      (*_NS_kazreth.PALETTE["bone_light"],
                                       int(240 * alpha_mult)),
                                      (hook_x, hook_y), 2)
                pygame.draw.rect(wing_surf,
                                 (*_NS_kazreth.PALETTE["bone_shine"],
                                  int(255 * alpha_mult)),
                                 (hook_x, hook_y, 1, 1))
            # Red hot cracks running through membrane (like lava veins)
            for i, tip_p in enumerate(tips[:3]):
                tp = (tip_p[0] - offset_x, tip_p[1] - offset_y)
                mid_x = int((bone_base[0] + tp[0]) / 2)
                mid_y = int((bone_base[1] + tp[1]) / 2)
                # Small red glowing line branching off
                branch_x = mid_x + int(math.sin(phase + i) * 6)
                branch_y = mid_y + int(math.cos(phase + i) * 4)
                pygame.draw.line(wing_surf,
                                 (*_NS_kazreth.PALETTE["blood_mid"],
                                  int(180 * alpha_mult)),
                                 (mid_x, mid_y), (branch_x, branch_y), 1)
                pygame.draw.rect(wing_surf,
                                 (*_NS_kazreth.PALETTE["blood_hot"],
                                  int(230 * alpha_mult)),
                                 (branch_x, branch_y, 1, 1))
            # Top edge red glow
            pygame.draw.line(wing_surf,
                             (*_NS_kazreth.PALETTE["membrane_glow"],
                              int(180 * alpha_mult)),
                             bone_base,
                             (tips[0][0] - offset_x, tips[0][1] - offset_y), 1)
            # Ember sparks on membrane
            for i in range(4):
                sp_x = int(cx_l + math.cos(phase + i * 1.5) * 32)
                sp_y = int(cy_l + math.sin(phase + i * 1.5) * 22)
                pygame.draw.rect(wing_surf,
                                 (*_NS_kazreth.PALETTE["blood_hot"],
                                  int(230 * alpha_mult)),
                                 (sp_x, sp_y, 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_dark_cloth(surface, cx, cy, facing, phase):
        """Trailing dark cloth/tabard."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        cloth_pts = [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 12, cy + 10),
            (cx + 14 + int(wave1), cy + 22),
            (cx + 12 + int(wave2), cy + 34),
            (cx + 6, cy + 42),
            (cx - 6, cy + 42),
            (cx - 12 + int(wave2), cy + 34),
            (cx - 14 + int(wave1), cy + 22),
            (cx - 12, cy + 10),
        ]
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in cloth_pts])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], cloth_pts)
        # Second layer
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
            (cx - 7, cy + 2),
            (cx + 7, cy + 2),
            (cx + 10, cy + 12),
            (cx + 12 + int(wave1 * 0.7), cy + 24),
            (cx + 9 + int(wave2 * 0.7), cy + 34),
            (cx + 4, cy + 40),
            (cx - 4, cy + 40),
            (cx - 9 + int(wave2 * 0.7), cy + 34),
            (cx - 12 + int(wave1 * 0.7), cy + 24),
            (cx - 10, cy + 12),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_mid"], [
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 8, cy + 16),
            (cx + 8, cy + 30),
            (cx + 3, cy + 38),
            (cx - 3, cy + 38),
            (cx - 8, cy + 30),
            (cx - 8, cy + 16),
        ])
        # Central red glow vein down the middle
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, y_off in enumerate((6, 12, 20, 28, 34)):
            alpha = _NS_kazreth._alpha(200 * pulse)
            pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_dark"],
                             (cx - 1, cy + y_off), (cx + 1, cy + y_off), 1)
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                             (cx, cy + y_off, 1, 1))
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_shine"],
                             (cx, cy + y_off, 1, 1))
        # Cracks radiating outward
        for i, (start_x, start_y, end_x, end_y) in enumerate([
            (-3, 12, -8, 22), (3, 12, 8, 22),
            (-4, 24, -9, 34), (4, 24, 9, 34),
        ]):
            pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_dark"],
                             (cx + start_x, cy + start_y),
                             (cx + end_x, cy + end_y), 1)
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                             (cx + end_x, cy + end_y, 1, 1))
    def _draw_lower_body(surface, cx, cy, facing, phase):
        """Armored lower body (loin/hips area)."""
        # Hip armor
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], [
            (cx - 10, cy - 1), (cx + 10, cy - 1),
            (cx + 11, cy + 5), (cx - 11, cy + 5),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], [
            (cx - 10, cy - 2), (cx + 10, cy - 2),
            (cx + 10, cy + 4), (cx - 10, cy + 4),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
            (cx - 9, cy - 1), (cx + 9, cy - 1),
            (cx + 9, cy + 3), (cx - 9, cy + 3),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_mid"], [
            (cx - 7, cy), (cx + 7, cy),
            (cx + 7, cy + 2), (cx - 7, cy + 2),
        ])
        # Central buckle (red gem)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["bone_dark"],
                         (cx - 2, cy, 4, 3))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_kazreth._alpha(140 * (4 - r) / 4 * pulse)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_light"], alpha),
                                  (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_dark"],
                         (cx - 1, cy, 2, 2))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_shine"],
                         (cx, cy, 1, 1))
        # Side spikes
        for side in (-1, 1):
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], [
                (cx + side * 10, cy),
                (cx + side * 14, cy - 2),
                (cx + side * 12, cy + 2),
            ])
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
                (cx + side * 10, cy + 1),
                (cx + side * 13, cy),
                (cx + side * 11, cy + 2),
            ])
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["bone_light"],
                             (cx + side * 13, cy - 1, 1, 1))
    def _draw_torso_armor(surface, cx, cy, facing, phase):
        """Bulky armored torso with cracks."""
        # Torso shape (broad shoulders)
        torso_pts = [
            (cx - 12, cy - 4),
            (cx - 14, cy),
            (cx - 12, cy + 8),
            (cx + 12, cy + 8),
            (cx + 14, cy),
            (cx + 12, cy - 4),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ]
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_pts])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], torso_pts)
        # Second armor layer
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
            (cx - 11, cy - 3),
            (cx - 13, cy),
            (cx - 11, cy + 7),
            (cx + 11, cy + 7),
            (cx + 13, cy),
            (cx + 11, cy - 3),
            (cx + 7, cy - 5),
            (cx - 7, cy - 5),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_mid"], [
            (cx - 9, cy - 2),
            (cx - 11, cy),
            (cx - 9, cy + 5),
            (cx + 9, cy + 5),
            (cx + 11, cy),
            (cx + 9, cy - 2),
            (cx + 5, cy - 4),
            (cx - 5, cy - 4),
        ])
        # Highlights
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_light"],
                         (cx - 5, cy - 3), (cx + 5, cy - 3), 1)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_light"],
                         (cx - 8, cy + 1), (cx + 8, cy + 1), 1)
        # HUGE central chest cavity (glowing red heart/core)
        # Frame
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 4, cy + 5),
            (cx - 4, cy + 5),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        # Glowing core
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(7, 0, -1):
            alpha = _NS_kazreth._alpha(150 * (7 - r) / 7 * pulse)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_light"], alpha),
                                  (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_darkest"],
                         (cx - 2, cy - 1, 4, 4))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_dark"],
                         (cx - 1, cy, 2, 3))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (cx, cy, 1, 2))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_shine"],
                         (cx, cy, 1, 1))
        # Cracks radiating from core
        for i, (dx1, dy1, dx2, dy2) in enumerate([
            (-3, -3, -7, -4), (3, -3, 7, -4),
            (-4, 4, -8, 5), (4, 4, 8, 5),
        ]):
            pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_dark"],
                             (cx + dx1, cy + dy1), (cx + dx2, cy + dy2), 1)
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                             (cx + dx2, cy + dy2, 1, 1))
        # Shoulder pauldrons (massive spiked)
        for side in (-1, 1):
            # Shoulder base
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], [
                (cx + side * 9, cy - 6),
                (cx + side * 16, cy - 5),
                (cx + side * 17, cy),
                (cx + side * 13, cy + 2),
                (cx + side * 9, cy),
            ])
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], [
                (cx + side * 9, cy - 7),
                (cx + side * 15, cy - 6),
                (cx + side * 16, cy),
                (cx + side * 12, cy + 1),
                (cx + side * 9, cy - 1),
            ])
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
                (cx + side * 10, cy - 6),
                (cx + side * 14, cy - 5),
                (cx + side * 15, cy - 1),
                (cx + side * 11, cy),
            ])
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_mid"], [
                (cx + side * 11, cy - 5),
                (cx + side * 13, cy - 4),
                (cx + side * 14, cy - 2),
                (cx + side * 12, cy - 1),
            ])
            # Highlight
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["armor_light"],
                             (cx + side * 12, cy - 4, 2, 1))
            # Big spikes on shoulder (2 spikes per side)
            for spike_off_x, spike_off_y, spike_h in [
                (11, -8, 6), (14, -6, 4),
            ]:
                sp_x = cx + side * spike_off_x
                sp_y = cy + spike_off_y
                sp_tip_y = sp_y - spike_h
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], [
                    (sp_x + 1, sp_tip_y + 1),
                    (sp_x - 2 + 1, sp_y + 1),
                    (sp_x + 2 + 1, sp_y + 1),
                ])
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], [
                    (sp_x, sp_tip_y),
                    (sp_x - 2, sp_y),
                    (sp_x + 2, sp_y),
                ])
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
                    (sp_x, sp_tip_y + 1),
                    (sp_x - 1, sp_y),
                    (sp_x + 1, sp_y),
                ])
                # Red glow at tip
                pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                                 (sp_x, sp_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_shine"],
                                 (sp_x, sp_tip_y, 1, 1))
    def _draw_arms_and_sword(surface, cx, cy, facing, phase, sword_swing, action,
                              attack_progress):
        """Arms holding a massive greatsword."""
        wave = math.sin(phase * 0.6) * 1
        # Sword is held in both hands (or one) diagonally across body
        # During attack: sword swings horizontally
        # Front arm (holds sword handle)
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 2
        elbow_x = cx + facing * 16 + sword_swing // 2
        elbow_y = cy + 4 + int(wave)
        hand_x = cx + facing * 20 + sword_swing
        hand_y = cy + 2 + int(wave)
        # Back arm (supports sword)
        b_shoulder_x = cx - facing * 6
        b_shoulder_y = cy - 2
        b_elbow_x = cx + facing * 2 + sword_swing // 3
        b_elbow_y = cy + 4 + int(wave)
        b_hand_x = cx + facing * 10 + sword_swing // 2
        b_hand_y = cy + 2 + int(wave)
        # Back arm first (behind body)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["shadow_deep"],
                            (b_shoulder_x + 1, b_shoulder_y + 1),
                            (b_elbow_x + 1, b_elbow_y + 1), 5)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_darkest"],
                            (b_shoulder_x, b_shoulder_y),
                            (b_elbow_x, b_elbow_y), 4)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_dark"],
                            (b_shoulder_x, b_shoulder_y),
                            (b_elbow_x, b_elbow_y), 3)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_mid"],
                            (b_shoulder_x, b_shoulder_y - 1),
                            (b_elbow_x, b_elbow_y - 1), 2)
        # Back forearm
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["shadow_deep"],
                            (b_elbow_x + 1, b_elbow_y + 1),
                            (b_hand_x + 1, b_hand_y + 1), 5)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_darkest"],
                            (b_elbow_x, b_elbow_y),
                            (b_hand_x, b_hand_y), 4)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_dark"],
                            (b_elbow_x, b_elbow_y),
                            (b_hand_x, b_hand_y), 3)
        # Front arm upper
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 5)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)
        # Elbow spike
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_darkest"],
                         (elbow_x, elbow_y), (elbow_x, elbow_y + 4), 2)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (elbow_x, elbow_y + 3, 1, 1))
        # Front forearm
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_kazreth._aaline(surface, _NS_kazreth.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        # NOW DRAW THE GREATSWORD
        _NS_kazreth._draw_greatsword(surface, hand_x, hand_y, facing, phase,
                                      sword_swing, action)
    def _draw_greatsword(surface, hand_x, hand_y, facing, phase, swing, action):
        """Massive dark greatsword with red glowing edge."""
        # Sword angle depends on swing
        # Base orientation: sword points forward and slightly down
        # During swing: rotates through arc
        # Calculate sword direction
        # Rest position: tip goes forward-up
        # After swing: forward-down
        base_angle = -math.pi * 0.15  # slight upward angle
        # Add swing rotation
        swing_rot = swing * 0.06  # convert to rotation
        angle = base_angle + swing_rot
        angle_facing = angle * facing if facing == 1 else math.pi - angle
        sword_len = 40
        # Handle direction (goes back into hand)
        handle_angle = angle_facing + math.pi
        handle_x = hand_x + int(math.cos(handle_angle) * 6)
        handle_y = hand_y + int(math.sin(handle_angle) * 6)
        # Blade tip
        tip_x = hand_x + int(math.cos(angle_facing) * sword_len)
        tip_y = hand_y + int(math.sin(angle_facing) * sword_len)
        # Perpendicular for blade width
        perp_a = angle_facing + math.pi / 2
        blade_w = 4
        # Handle guard
        guard_a1_x = hand_x + int(math.cos(perp_a) * 6)
        guard_a1_y = hand_y + int(math.sin(perp_a) * 6)
        guard_a2_x = hand_x - int(math.cos(perp_a) * 6)
        guard_a2_y = hand_y - int(math.sin(perp_a) * 6)
        # Blade shape: pointed diamond
        blade_base_a_x = hand_x + int(math.cos(perp_a) * blade_w)
        blade_base_a_y = hand_y + int(math.sin(perp_a) * blade_w)
        blade_base_b_x = hand_x - int(math.cos(perp_a) * blade_w)
        blade_base_b_y = hand_y - int(math.sin(perp_a) * blade_w)
        # Mid-blade (widest)
        mid_x = hand_x + int(math.cos(angle_facing) * sword_len * 0.5)
        mid_y = hand_y + int(math.sin(angle_facing) * sword_len * 0.5)
        blade_mid_a_x = mid_x + int(math.cos(perp_a) * (blade_w + 2))
        blade_mid_a_y = mid_y + int(math.sin(perp_a) * (blade_w + 2))
        blade_mid_b_x = mid_x - int(math.cos(perp_a) * (blade_w + 2))
        blade_mid_b_y = mid_y - int(math.sin(perp_a) * (blade_w + 2))
        # Shadow
        blade_shadow = [
            (blade_base_a_x + 2, blade_base_a_y + 2),
            (blade_mid_a_x + 2, blade_mid_a_y + 2),
            (tip_x + 2, tip_y + 2),
            (blade_mid_b_x + 2, blade_mid_b_y + 2),
            (blade_base_b_x + 2, blade_base_b_y + 2),
        ]
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], blade_shadow)
        # Base dark blade
        blade_pts = [
            (blade_base_a_x, blade_base_a_y),
            (blade_mid_a_x, blade_mid_a_y),
            (tip_x, tip_y),
            (blade_mid_b_x, blade_mid_b_y),
            (blade_base_b_x, blade_base_b_y),
        ]
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["blade_dark"], blade_pts)
        # Mid blade fill (darker inner shape)
        inner_pts = []
        cx_b = (blade_base_a_x + blade_base_b_x + tip_x) // 3
        cy_b = (blade_base_a_y + blade_base_b_y + tip_y) // 3
        for p in blade_pts:
            inner_pts.append(
                (int(p[0] * 0.7 + cx_b * 0.3),
                 int(p[1] * 0.7 + cy_b * 0.3))
            )
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["blade_mid"], inner_pts)
        # Central fuller (highlight line down middle)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["blade_light"],
                         (hand_x, hand_y), (tip_x, tip_y), 1)
        # GLOWING RED EDGE (top edge of blade)
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        edge_alpha = _NS_kazreth._alpha(240 * pulse)
        # Red glowing cracks running along blade
        pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_dark"],
                         (blade_base_a_x, blade_base_a_y),
                         (blade_mid_a_x, blade_mid_a_y), 2)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_mid"],
                         (blade_base_a_x, blade_base_a_y),
                         (blade_mid_a_x, blade_mid_a_y), 1)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_dark"],
                         (blade_mid_a_x, blade_mid_a_y),
                         (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (blade_mid_a_x, blade_mid_a_y),
                         (tip_x, tip_y), 1)
        # Bright blade tip
        _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_light"],
                              (tip_x, tip_y), 2)
        _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_shine"],
                              (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Small ember sparks along blade during idle/attack
        for i in range(3):
            spark_t = (phase + i * 0.4) % 1.0
            sp_dist = sword_len * spark_t
            spx = hand_x + int(math.cos(angle_facing) * sp_dist) \
                + int(math.sin(phase + i) * 3)
            spy = hand_y + int(math.sin(angle_facing) * sp_dist)
            alpha_sp = _NS_kazreth._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_kazreth.PALETTE["ember_hot"], alpha_sp),
                             (spx, spy, 1, 1))
        # GUARD (crossguard - horned)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["shadow_deep"],
                         (guard_a1_x + 1, guard_a1_y + 1),
                         (guard_a2_x + 1, guard_a2_y + 1), 3)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_darkest"],
                         (guard_a1_x, guard_a1_y),
                         (guard_a2_x, guard_a2_y), 3)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_dark"],
                         (guard_a1_x, guard_a1_y),
                         (guard_a2_x, guard_a2_y), 2)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["bone_mid"],
                         (guard_a1_x, guard_a1_y),
                         (guard_a2_x, guard_a2_y), 1)
        # Curved guard tips (like horns)
        guard_hook_angle = math.pi * 0.15
        for gp, gside in [((guard_a1_x, guard_a1_y), 1), ((guard_a2_x, guard_a2_y), -1)]:
            hook_x = gp[0] + int(math.cos(perp_a + guard_hook_angle * gside) * 3)
            hook_y = gp[1] + int(math.sin(perp_a + guard_hook_angle * gside) * 3)
            pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_darkest"],
                             gp, (hook_x, hook_y), 2)
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                             (hook_x, hook_y, 1, 1))
        # HANDLE (wrapped grip)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1),
                         (handle_x + 1, handle_y + 1), 4)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_darkest"],
                         (hand_x, hand_y), (handle_x, handle_y), 3)
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_dark"],
                         (hand_x, hand_y), (handle_x, handle_y), 2)
        # Handle wrap segments
        for seg_t in (0.3, 0.6):
            sxx = int(hand_x + (handle_x - hand_x) * seg_t)
            syy = int(hand_y + (handle_y - hand_y) * seg_t)
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["bone_dark"],
                             (sxx - 1, syy - 1, 3, 2))
        # POMMEL (red glowing gem at end)
        _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["armor_darkest"],
                              (handle_x, handle_y), 3)
        for r in range(4, 0, -1):
            alpha = _NS_kazreth._alpha(150 * (4 - r) / 4 * pulse)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_light"], alpha),
                                  (handle_x, handle_y), r)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_dark"],
                         (handle_x - 1, handle_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (handle_x, handle_y, 1, 1))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_shine"],
                         (handle_x, handle_y, 1, 1))
    def _draw_demon_head(surface, cx, cy, facing, phase, action):
        """Horned demon head with glowing red eyes."""
        # Helmet shape (elongated with horn crown)
        head_pts = [
            (cx - 6, cy + 6),
            (cx - 7, cy),
            (cx - 5, cy - 6),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
            (cx + 5, cy - 6),
            (cx + 7, cy - 1),
            (cx + 6, cy + 4),
            (cx + 3, cy + 7),
            (cx - 3, cy + 7),
        ]
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in head_pts])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], head_pts)
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
            (cx - 5, cy + 5),
            (cx - 6, cy),
            (cx - 4, cy - 5),
            (cx - 1, cy - 8),
            (cx + 1, cy - 8),
            (cx + 4, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
        ])
        _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy),
            (cx - 3, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 3, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 1, cy + 5),
            (cx - 1, cy + 5),
        ])
        # Face highlight
        pygame.draw.line(surface, _NS_kazreth.PALETTE["armor_light"],
                         (cx - 2, cy - 5), (cx + 2, cy - 5), 1)
        # HORNS (massive curved horns like Aatrox)
        _NS_kazreth._draw_demon_horns(surface, cx, cy, facing, phase)
        # GLOWING RED EYES
        _NS_kazreth._draw_demon_eyes(surface, cx, cy - 2, facing, phase)
        # Face plate crack (jaw slit glow)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pygame.draw.line(surface, _NS_kazreth.PALETTE["shadow_deep"],
                         (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_dark"],
                         (cx - 2, cy + 3, 4, 1))
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (cx - 1, cy + 3, 2, 1))
        # Face crack running vertically
        pygame.draw.line(surface, _NS_kazreth.PALETTE["blood_darkest"],
                         (cx, cy - 6), (cx, cy - 3), 1)
        pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                         (cx, cy - 5, 1, 1))
    def _draw_demon_horns(surface, cx, cy, facing, phase):
        """Multiple horns crown (like Aatrox's helmet)."""
        sway = math.sin(phase * 0.4) * 1
        # Multiple horns per side curving up and back
        for side in (-1, 1):
            for i, (base_off_x, base_off_y, angle_off, length) in enumerate([
                (-3 * side, -8, math.pi * 0.55, 10),  # short outer
                (-1 * side, -9, math.pi * 0.7, 14),   # tallest middle
                (2 * side, -8, math.pi * 0.85, 11),   # inner curved
            ]):
                base_x = cx + base_off_x
                base_y = cy + base_off_y
                dir_mult = side
                tip_x = base_x + int(math.cos(angle_off) * length) * dir_mult
                tip_y = base_y - int(math.sin(angle_off) * length) + int(sway)
                # Horn triangle
                perp_x = -math.sin(angle_off) * dir_mult
                perp_y = math.cos(angle_off)
                pa_x = base_x + int(perp_x * 2)
                pa_y = base_y + int(perp_y * 2)
                pb_x = base_x - int(perp_x * 2)
                pb_y = base_y - int(perp_y * 2)
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (pa_x + 1, pa_y + 1),
                    (pb_x + 1, pb_y + 1),
                ])
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"],
                                  [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                    (base_x, base_y),
                ])
                _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["bone_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                    (base_x, base_y),
                ])
                # Bone tip
                pygame.draw.rect(surface, _NS_kazreth.PALETTE["bone_light"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kazreth.PALETTE["bone_shine"],
                                 (tip_x, tip_y, 1, 1))
    def _draw_demon_eyes(surface, cx, cy, facing, phase):
        """Bright glowing red eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy
            # Deep socket
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_kazreth._alpha(130 * (5 - r) / 5 * pulse)
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["eye_mid"], alpha),
                                      (ex, ey), r)
            # Core
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["eye_mid"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
    # ============================================================
    # MELEE SWING ARC (FIXED)
    # ============================================================
    def _draw_sword_swing_arc(surface, boss, x, y, progress):
        """Bright red crescent arc trail from sword swing (Q - Crimson Reaver)."""
        if progress < 0.35 or progress > 0.72:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.37
        # Arc pusat di depan boss
        arc_cx = x + facing * 20
        arc_cy = y
        arc_radius = 40
        # Angle sweep: dari ATAS (-90°) melalui DEPAN (0°) ke BAWAH (+90°)
        # Sudut diukur dari sumbu horizontal depan (ke arah facing)
        # -math.pi/2 = atas, 0 = depan, +math.pi/2 = bawah
        start_a = -math.pi * 0.55   # mulai dari atas-depan
        end_a = math.pi * 0.55      # akhir di bawah-depan
        # Layered arcs untuk glow effect
        for layer_i, (thick, alpha_val, color) in enumerate([
            (5, 100, _NS_kazreth.PALETTE["blood_dark"]),
            (4, 150, _NS_kazreth.PALETTE["blood_mid"]),
            (3, 200, _NS_kazreth.PALETTE["blood_light"]),
            (2, 240, _NS_kazreth.PALETTE["blood_hot"]),
            (1, 255, _NS_kazreth.PALETTE["blood_shine"]),
        ]):
            arc_points = []
            for seg in range(20):
                seg_t = seg / 19
                # Hanya tampilkan bagian arc sampai t sekarang
                if seg_t > t + 0.15:
                    break
                a = start_a + (end_a - start_a) * seg_t
                # cos(a) = arah horizontal (depan), dikali facing supaya kanan/kiri benar
                # sin(a) = arah vertikal (atas negatif, bawah positif)
                ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                ay = arc_cy + int(math.sin(a) * arc_radius)
                arc_points.append((ax, ay))
            if len(arc_points) >= 2:
                for i in range(len(arc_points) - 1):
                    fade = 1 - i / max(1, len(arc_points))
                    actual_alpha = _NS_kazreth._alpha(alpha_val * fade)
                    pygame.draw.line(surface, (*color, actual_alpha),
                                     arc_points[i], arc_points[i + 1], thick)
        # Sparks di ujung arc (leading edge)
        if 0.4 < t < 0.8:
            tip_a = start_a + (end_a - start_a) * t
            tip_x_arc = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
            tip_y_arc = arc_cy + int(math.sin(tip_a) * arc_radius)
            for r in range(8, 0, -1):
                alpha = _NS_kazreth._alpha(200 * (8 - r) / 8)
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                                      (tip_x_arc, tip_y_arc), r)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_shine"],
                                  (tip_x_arc, tip_y_arc), 2)
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["white"],
                             (tip_x_arc, tip_y_arc, 1, 1))
            # Spark trails ke arah luar
            for i in range(6):
                sp_a = tip_a + (i - 3) * 0.15
                sp_len = 8 + i
                spx = tip_x_arc + int(math.cos(sp_a) * sp_len * facing)
                spy = tip_y_arc + int(math.sin(sp_a) * sp_len)
                pygame.draw.rect(surface, _NS_kazreth.PALETTE["ember_hot"], (spx, spy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = _NS_kazreth._alpha((15 - radius) * 14 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius // 2,
                 130 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (10, 3, 5, 170), (10, 10, 130, 12))
        pygame.draw.ellipse(shadow, (80, 15, 20, 100), (18, 12, 114, 8))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_blood_embers(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blood red embers floating below."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -3):
            alpha = _NS_kazreth._alpha((34 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_kazreth._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising ember particles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_kazreth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["ember_dark"], alpha),
                                  (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_kazreth.PALETTE["ember_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_kazreth.PALETTE["ember_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Blood particles
        for i in range(8):
            spark_t = (phase * 0.7 + i * 0.13) % 1.0
            ex = cx - 26 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_kazreth._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["blood_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kazreth._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                                      (sx, sy), max(2, 7 - i))
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                      (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_blood_aura(surface, x, y, phase):
        """Massive blood aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_kazreth._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kazreth._aacircle(aura,
                                      (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                                      (120, 105), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_kazreth._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kazreth._aacircle(aura,
                                      (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                      (120, 105), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kazreth._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kazreth._aacircle(aura,
                                      (*_NS_kazreth.PALETTE["blood_mid"], alpha),
                                      (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # Floating ember embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_kazreth.PALETTE["blood_hot"] if i % 2 == 0 \
                else _NS_kazreth.PALETTE["ember_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["ember_shine"], (sx, sy, 1, 1))
    def _draw_ground_rift(surface, x, y, phase, skill):
        """Cracked ground with red glow."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        # Portal rings
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        # Cracks radiating
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_kazreth.PALETTE["blood_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kazreth.PALETTE["blood_light"],
                                 _NS_kazreth._alpha(180 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - CRIMSON REAVER (FIXED)
    # ============================================================
    def _draw_crimson_reaver(surface, boss, x, y, timer, phase):
        """Extended crescent slash covering an area."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kazreth._target_position(boss, x, y)
        if progress < 0.3:
            # Wind up glow di tangan
            t = progress / 0.3
            hand_x = x + facing * 20
            hand_y = y - 4
            cr = int(6 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kazreth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_light"],
                                  (hand_x, hand_y), cr - 2)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_shine"],
                                  (hand_x, hand_y), max(1, cr - 5))
        else:
            # Massive crescent slash meluas ke depan
            t = (progress - 0.3) / 0.7
            arc_cx = x + facing * 15
            arc_cy = y - 4
            arc_radius = int(50 + t * 40)
            # Sudut: dari atas-depan ke bawah-depan (crescent vertikal di depan boss)
            start_a = -math.pi * 0.65   # atas-depan
            end_a = math.pi * 0.65      # bawah-depan
            # Multiple arc layers
            for layer_i, (thick, alpha_mult, color) in enumerate([
                (6, 0.4, _NS_kazreth.PALETTE["blood_darkest"]),
                (5, 0.6, _NS_kazreth.PALETTE["blood_dark"]),
                (4, 0.8, _NS_kazreth.PALETTE["blood_mid"]),
                (3, 1.0, _NS_kazreth.PALETTE["blood_light"]),
                (2, 1.0, _NS_kazreth.PALETTE["blood_hot"]),
                (1, 1.0, _NS_kazreth.PALETTE["blood_shine"]),
            ]):
                arc_alpha = _NS_kazreth._alpha(240 * alpha_mult * (1 - t * 0.5))
                prev_pt = None
                for seg in range(24):
                    seg_t = seg / 23
                    a = start_a + (end_a - start_a) * seg_t
                    ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                    ay = arc_cy + int(math.sin(a) * arc_radius)
                    if prev_pt:
                        pygame.draw.line(surface, (*color, arc_alpha),
                                         prev_pt, (ax, ay), thick)
                    prev_pt = (ax, ay)
            # SWEET SPOT: burst di tengah arc (di depan, sejajar)
            if t > 0.3:
                sweet_a = 0  # tengah = 0° = tepat di depan
                sweet_x = arc_cx + int(math.cos(sweet_a) * arc_radius * facing)
                sweet_y = arc_cy + int(math.sin(sweet_a) * arc_radius)
                st = (t - 0.3) / 0.7
                burst_r = int(12 + st * 20)
                burst_alpha = _NS_kazreth._alpha(240 * (1 - st))
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_darkest"], burst_alpha),
                                      (sweet_x, sweet_y), burst_r + 3, 3)
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_dark"], burst_alpha),
                                      (sweet_x, sweet_y), burst_r, 3)
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_mid"], burst_alpha),
                                      (sweet_x, sweet_y), max(1, burst_r - 4), 2)
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_light"], burst_alpha),
                                      (sweet_x, sweet_y), max(1, burst_r - 8), 1)
                # Radial sparks
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = sweet_x + int(math.cos(angle_s) * burst_r)
                    ey = sweet_y + int(math.sin(angle_s) * burst_r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_kazreth.PALETTE["blood_hot"], burst_alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_kazreth.PALETTE["blood_shine"], burst_alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - HELLFIRE CHAINS (chain projectile)
    # ============================================================
    def _draw_chains_ground(surface, boss, x, y, timer, phase):
        """Ground marks."""
        tx, ty = _NS_kazreth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_kazreth.PALETTE["blood_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kazreth.PALETTE["blood_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_chains_foreground(surface, boss, x, y, timer, phase):
        """Fiery chain shooting toward target."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kazreth._target_position(boss, x, y)
        # Chain origin (from hand)
        start_x = x + facing * 20
        start_y = y - 4
        if progress < 0.25:
            # Charge
            t = progress / 0.25
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kazreth._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                      (start_x, start_y), r)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_hot"],
                                  (start_x, start_y), cr - 2)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_shine"],
                                  (start_x, start_y), max(1, cr - 4))
        elif progress < 0.6:
            # Chain extends
            t = (progress - 0.25) / 0.35
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
            # Draw chain segments
            segments = int(20 * t)
            for i in range(segments):
                seg_t = i / max(1, segments)
                sx = int(start_x + (end_x - start_x) * seg_t)
                sy = int(start_y + (end_y - start_y) * seg_t)
                # Sag
                sag = math.sin(seg_t * math.pi) * 3
                sy += int(sag)
                # Chain link (small circles alternating)
                if i % 2 == 0:
                    _NS_kazreth._aacircle(surface,
                                          _NS_kazreth.PALETTE["shadow_deep"],
                                          (sx + 1, sy + 1), 3)
                    _NS_kazreth._aacircle(surface,
                                          _NS_kazreth.PALETTE["armor_darkest"],
                                          (sx, sy), 3)
                    _NS_kazreth._aacircle(surface,
                                          _NS_kazreth.PALETTE["armor_dark"],
                                          (sx, sy), 2)
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                                     (sx, sy, 1, 1))
                else:
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["armor_darkest"],
                                     (sx - 1, sy - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["armor_dark"],
                                     (sx - 1, sy, 3, 2))
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                                     (sx, sy, 1, 1))
                # Fire embers on chain
                if i % 3 == 0:
                    for e in range(2):
                        ex = sx + int(math.sin(phase * 3 + i + e) * 3)
                        ey = sy - int(math.cos(phase * 3 + i + e) * 3)
                        pygame.draw.rect(surface, _NS_kazreth.PALETTE["ember_hot"], (ex, ey, 1, 1))
            # Chain end (spike/anchor)
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["shadow_deep"], [
                (end_x + facing * 5 + 1, end_y + 1),
                (end_x - facing * 3 + 1, end_y - 3 + 1),
                (end_x - facing * 3 + 1, end_y + 3 + 1),
            ])
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["armor_darkest"], [
                (end_x + facing * 5, end_y),
                (end_x - facing * 3, end_y - 3),
                (end_x - facing * 3, end_y + 3),
            ])
            _NS_kazreth._poly(surface, _NS_kazreth.PALETTE["blood_mid"], [
                (end_x + facing * 4, end_y),
                (end_x - facing * 2, end_y - 2),
                (end_x - facing * 2, end_y + 2),
            ])
            pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_shine"],
                             (end_x + facing * 4, end_y, 1, 1))
        else:
            # PULL PHASE: enemies pulled toward center
            t = (progress - 0.6) / 0.4
            # Static chain locked
            segments = 20
            for i in range(segments):
                seg_t = i / segments
                sx = int(start_x + (tx - start_x) * seg_t)
                sy = int(start_y + (ty - start_y) * seg_t)
                sag = math.sin(seg_t * math.pi) * (3 * (1 - t))
                sy += int(sag)
                if i % 2 == 0:
                    _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["armor_darkest"],
                                          (sx, sy), 3)
                    _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["armor_dark"],
                                          (sx, sy), 2)
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                                     (sx, sy, 1, 1))
                else:
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["armor_darkest"],
                                     (sx - 1, sy - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"],
                                     (sx, sy, 1, 1))
            # Pull impact at target
            pull_r = int(15 + t * 20)
            alpha = _NS_kazreth._alpha(220 * (1 - t))
            _NS_kazreth._aacircle(surface, (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                                  (tx, ty), pull_r + 3, 3)
            _NS_kazreth._aacircle(surface, (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                  (tx, ty), pull_r, 2)
            _NS_kazreth._aacircle(surface, (*_NS_kazreth.PALETTE["blood_light"], alpha),
                                  (tx, ty), max(1, pull_r - 6), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * pull_r)
                ey = ty + int(math.sin(angle_s) * pull_r * 0.7)
                pygame.draw.rect(surface, (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL E - SHADOWSTEP (dash)
    # ============================================================
    def _draw_shadowstep_ground(surface, boss, x, y, timer, phase):
        """Trail marks on ground during dash."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground streak
        streak_len = int(80 * progress)
        for i in range(streak_len // 5):
            sx = x - facing * (i * 5)
            alpha = _NS_kazreth._alpha(200 * (1 - i * 5 / streak_len))
            pygame.draw.line(surface, (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                             (sx, y + 45), (sx - facing * 3, y + 45), 2)
            pygame.draw.rect(surface, (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                             (sx, y + 45, 2, 1))
    def _draw_shadowstep_foreground(surface, boss, x, y, timer, phase):
        """Motion blur / afterimages during dash."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Draw afterimage silhouettes
        for i in range(1, 5):
            afterimage_x = x - facing * (i * 12)
            alpha = _NS_kazreth._alpha(150 - i * 30)
            # Simple silhouette (body outline)
            afterimage_surf = pygame.Surface((60, 100), pygame.SRCALPHA)
            for r in range(20, 0, -2):
                aa = _NS_kazreth._alpha(alpha * (20 - r) / 20)
                _NS_kazreth._aacircle(afterimage_surf,
                                      (*_NS_kazreth.PALETTE["blood_dark"], aa),
                                      (30, 50), r)
            surface.blit(afterimage_surf, (afterimage_x - 30, y - 50))
        # Blade trail streak
        blade_start_x = x + facing * 20
        blade_start_y = y - 4
        for i in range(6):
            trail_alpha = _NS_kazreth._alpha(220 - i * 30)
            trail_x = blade_start_x - facing * (i * 15)
            pygame.draw.line(surface,
                             (*_NS_kazreth.PALETTE["blood_hot"], trail_alpha),
                             (trail_x, blade_start_y - 5),
                             (trail_x - facing * 12, blade_start_y - 5), 3)
            pygame.draw.line(surface,
                             (*_NS_kazreth.PALETTE["blood_shine"], trail_alpha),
                             (trail_x, blade_start_y - 5),
                             (trail_x - facing * 12, blade_start_y - 5), 1)
    # ============================================================
    # SKILL R - APOCALYPSE (leap and slam)
    # ============================================================
    def _draw_apocalypse_ground(surface, boss, x, y, timer, phase):
        """Massive impact circle on ground."""
        tx, ty = _NS_kazreth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Warning
            t = progress / 0.5
            r = int(70 * t)
            alpha = _NS_kazreth._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_kazreth.PALETTE["blood_hot"], (sx, sy, 2, 2))
        else:
            # Impact aftermath
            t = (progress - 0.5) / 0.5
            r = int(70 + t * 15)
            alpha = _NS_kazreth._alpha(240 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_kazreth.PALETTE["blood_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                                (*_NS_kazreth.PALETTE["blood_mid"], alpha),
                                (tx - r + 12, ty - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12))
    def _draw_apocalypse_foreground(surface, boss, x, y, timer, phase):
        """Vertical crash beam + spikes."""
        tx, ty = _NS_kazreth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Leap up phase: gathering energy from sky
            t = progress / 0.5
            gather_y = ty - int((1 - t) * 100 + 20)
            gather_r = int(6 + t * 10)
            for r in range(gather_r + 5, 0, -1):
                alpha = _NS_kazreth._alpha(180 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_kazreth._aacircle(surface,
                                      (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                      (tx, gather_y), r)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_light"],
                                  (tx, gather_y), gather_r - 2)
            _NS_kazreth._aacircle(surface, _NS_kazreth.PALETTE["blood_shine"],
                                  (tx, gather_y), max(1, gather_r - 5))
            # Warning glow at target
            alpha_warn = _NS_kazreth._alpha(180 * t)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_hot"], alpha_warn),
                                  (tx, ty), 8, 1)
        elif progress < 0.75:
            # CRASH DOWN - beam impact
            t = (progress - 0.5) / 0.25
            intensity = math.sin(t * math.pi)
            beam_top_y = max(0, ty - 220)
            # Multi-layer beam
            for layer_i, (width, alpha_val, color) in enumerate([
                (16, 100, _NS_kazreth.PALETTE["blood_darkest"]),
                (12, 140, _NS_kazreth.PALETTE["blood_dark"]),
                (8, 180, _NS_kazreth.PALETTE["blood_mid"]),
                (4, 220, _NS_kazreth.PALETTE["blood_light"]),
                (2, 255, _NS_kazreth.PALETTE["blood_hot"]),
                (1, 255, _NS_kazreth.PALETTE["blood_shine"]),
            ]):
                actual_alpha = _NS_kazreth._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, beam_top_y,
                                  width, ty - beam_top_y))
                # Sparks along beam
            for i in range(18):
                spark_t = (phase * 2 + i * 0.12) % 1.0
                spark_y = ty - int(spark_t * (ty - beam_top_y))
                spark_x = tx + int(math.sin(phase * 5 + i) * 8)
                alpha = _NS_kazreth._alpha(240 * intensity * (1 - spark_t * 0.4))
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["ember_shine"], alpha),
                                 (spark_x, spark_y, 1, 1))
                # Impact explosion at ground
            impact_r = int(20 + t * 30)
            impact_alpha = _NS_kazreth._alpha(240 * intensity)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_darkest"], impact_alpha),
                                  (tx, ty), impact_r + 4, 3)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_dark"], impact_alpha),
                                  (tx, ty), impact_r, 3)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_mid"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 6), 2)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_light"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 12), 1)
            _NS_kazreth._aacircle(surface,
                                  (*_NS_kazreth.PALETTE["blood_shine"], impact_alpha),
                                  (tx, ty), max(1, impact_r // 4))
            # RADIAL BLOOD SPIKES erupting outward (Aatrox R signature)
            num_spikes = 16
            for i in range(num_spikes):
                spike_angle = i * math.pi * 2 / num_spikes
                spike_dist = int(impact_r * 0.5 + t * 30)
                spike_base_x = tx + int(math.cos(spike_angle) * spike_dist)
                spike_base_y = ty + int(math.sin(spike_angle) * spike_dist * 0.5)
                # Spike shape (pointing outward)
                spike_tip_x = spike_base_x + int(math.cos(spike_angle) * 12)
                spike_tip_y = spike_base_y + int(math.sin(spike_angle) * 12 * 0.5)
                # Perpendicular for spike width
                perp = spike_angle + math.pi / 2
                pa_x = spike_base_x + int(math.cos(perp) * 3)
                pa_y = spike_base_y + int(math.sin(perp) * 3 * 0.5)
                pb_x = spike_base_x - int(math.cos(perp) * 3)
                pb_y = spike_base_y - int(math.sin(perp) * 3 * 0.5)
                _NS_kazreth._poly(surface,
                                  (*_NS_kazreth.PALETTE["shadow_deep"], impact_alpha),
                                  [(spike_tip_x + 1, spike_tip_y + 1),
                                   (pa_x + 1, pa_y + 1), (pb_x + 1, pb_y + 1)])
                _NS_kazreth._poly(surface,
                                  (*_NS_kazreth.PALETTE["blood_darkest"], impact_alpha),
                                  [(spike_tip_x, spike_tip_y),
                                   (pa_x, pa_y), (pb_x, pb_y)])
                _NS_kazreth._poly(surface,
                                  (*_NS_kazreth.PALETTE["blood_dark"], impact_alpha),
                                  [(spike_tip_x, spike_tip_y),
                                   (int((spike_tip_x + pa_x) / 2),
                                    int((spike_tip_y + pa_y) / 2)),
                                   (spike_base_x, spike_base_y)])
                _NS_kazreth._poly(surface,
                                  (*_NS_kazreth.PALETTE["blood_mid"], impact_alpha),
                                  [(spike_tip_x, spike_tip_y),
                                   (int((spike_tip_x + spike_base_x) / 2),
                                    int((spike_tip_y + spike_base_y) / 2)),
                                   (spike_base_x, spike_base_y)])
                # Bright tip
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["blood_hot"], impact_alpha),
                                 (spike_tip_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_kazreth.PALETTE["blood_shine"], impact_alpha),
                                 (spike_tip_x, spike_tip_y, 1, 1))
            # Radial cracks on ground
            for i in range(12):
                crack_angle = i * math.pi / 6
                cx1 = tx + int(math.cos(crack_angle) * 8)
                cy1 = ty + int(math.sin(crack_angle) * 4)
                cx2 = tx + int(math.cos(crack_angle) * (impact_r + 10))
                cy2 = ty + int(math.sin(crack_angle) * (impact_r + 10) * 0.5)
                pygame.draw.line(surface,
                                 (*_NS_kazreth.PALETTE["blood_hot"], impact_alpha),
                                 (cx1, cy1), (cx2, cy2), 2)
                pygame.draw.line(surface,
                                 (*_NS_kazreth.PALETTE["blood_shine"], impact_alpha),
                                 (cx1, cy1), (cx2, cy2), 1)
        else:
            # Aftermath: lingering embers
            t = (progress - 0.75) / 0.25
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 28)
                ry = ty - int(rise_t * 45)
                alpha = _NS_kazreth._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_kazreth._aacircle(surface,
                                          (*_NS_kazreth.PALETTE["blood_dark"], alpha),
                                          (rx, ry), 3)
                    _NS_kazreth._aacircle(surface,
                                          (*_NS_kazreth.PALETTE["blood_hot"], alpha),
                                          (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_kazreth.PALETTE["blood_shine"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# VARKUTHAR (BLOODFIRE ZEALOT) - Mini Boss
# ====================================================================

class _NS_varkuthar:
    """Namespace varkuthar - Bloodfire Zealot tribal warrior boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tribal green/teal)
        "skin_darkest": (10, 25, 25),
        "skin_dark": (25, 65, 65),
        "skin_mid": (55, 115, 115),
        "skin_light": (110, 175, 165),
        "skin_shine": (170, 220, 210),
        # Bone/skull (aged bone)
        "bone_darkest": (35, 25, 15),
        "bone_dark": (85, 70, 45),
        "bone_mid": (170, 150, 105),
        "bone_light": (230, 215, 175),
        "bone_shine": (255, 245, 215),
        # Red hair/loincloth/cape (tribal red)
        "red_darkest": (40, 5, 5),
        "red_dark": (110, 15, 15),
        "red_mid": (200, 35, 30),
        "red_light": (255, 90, 65),
        "red_hot": (255, 150, 100),
        "red_shine": (255, 220, 180),
        # Fire (orange/yellow flames)
        "fire_dark": (100, 30, 10),
        "fire_mid": (240, 100, 25),
        "fire_hot": (255, 180, 60),
        "fire_shine": (255, 240, 160),
        # Gold accents (armor rings, spear tip)
        "gold_dark": (85, 60, 15),
        "gold_mid": (180, 140, 45),
        "gold_light": (240, 205, 100),
        "gold_shine": (255, 240, 180),
        # Metal spear shaft
        "metal_dark": (35, 25, 20),
        "metal_mid": (90, 80, 65),
        "metal_light": (170, 155, 130),
        "metal_shine": (230, 220, 200),
        # Eye (red glowing)
        "eye_socket": (5, 2, 2),
        "eye_dark": (60, 10, 10),
        "eye_mid": (200, 40, 40),
        "eye_light": (255, 100, 80),
        "eye_glow": (255, 210, 170),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 1),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_varkuthar._clamp(color)
        if _NS_varkuthar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_varkuthar._clamp(color)
        if _NS_varkuthar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_varkuthar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_varkuthar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_varkuthar._detect_moving(boss)
        _NS_varkuthar._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_vkt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_varkuthar._draw_fire_aura(surface, x, y, pulse)
        _NS_varkuthar._draw_ground_embers(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX
        if active_skill == "w":
            _NS_varkuthar._draw_crimson_rite_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_varkuthar._draw_soulpierce_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_varkuthar._draw_vkt_attack(surface, boss, x, y)
        elif moving:
            _NS_varkuthar._draw_vkt_float_move(surface, boss, x, y)
        else:
            _NS_varkuthar._draw_vkt_idle(surface, boss, x, y)
        # Fire aura overlay (W skill active)
        if active_skill == "w":
            _NS_varkuthar._draw_crimson_rite_overlay(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_varkuthar._draw_ignis_spear(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_varkuthar._draw_blood_frenzy(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_varkuthar._draw_soulpierce_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vkt_previous_timer", 0))
        active = bool(getattr(boss, "_vkt_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vkt_attack_active = True
            boss._vkt_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vkt_attack_frame = int(getattr(boss, "_vkt_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vkt_attack_active = False
            boss._vkt_attack_frame = 0
            active = False
        boss._vkt_previous_timer = timer
        boss._vkt_attack_progress = (
            min(1.0, getattr(boss, "_vkt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_vkt_last_x"):
            boss._vkt_last_x = boss.x
            boss._vkt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vkt_last_x)
        dy = abs(boss.y - boss._vkt_last_y)
        boss._vkt_last_x = boss.x
        boss._vkt_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_vkt_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_varkuthar._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_varkuthar._draw_fire_wisps(surface, x, y + 40, boss.pulse)
        _NS_varkuthar._draw_vkt_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle")
    def _draw_vkt_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_varkuthar._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_varkuthar._draw_fire_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_varkuthar._draw_vkt_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")
    def _draw_vkt_attack(surface, boss, x, y):
        """Ranged spear throw animation."""
        progress = getattr(boss, "_vkt_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up (pull spear back) → throw forward → recovery
        if progress < 0.4:
            t = progress / 0.4
            body_shift = -int(t * 4) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            body_shift = int((-4 + t * 12)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            body_shift = int(8 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_varkuthar._draw_float_shadow(surface, x + body_shift, y + 52, boss.pulse)
        _NS_varkuthar._draw_fire_wisps(surface, x + body_shift, y + 40, boss.pulse,
                                        intense=True)
        _NS_varkuthar._draw_vkt_body(surface, x + body_shift, y - lift + bob,
                                     boss.direction, boss.pulse, "attack", progress)
        # Spear throw projectile
        _NS_varkuthar._draw_spear_throw_projectile(surface, boss,
                                                     x + body_shift, y - lift + bob,
                                                     progress)
    # ============================================================
    # BODY - Tribal Warrior with skull mask, spear, red mane
    # ============================================================
    def _draw_vkt_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Warrior body: cape, loincloth, torso, arms holding spear, skull mask head, mane."""
        # Cape (behind body)
        _NS_varkuthar._draw_red_cape(surface, cx, cy - 4, facing, phase)
        # Long red mane at back (flowing hair)
        _NS_varkuthar._draw_red_mane(surface, cx, cy - 20, facing, phase)
        # Loincloth/lower body
        _NS_varkuthar._draw_loincloth(surface, cx, cy + 8, facing, phase)
        # Torso (skin)
        _NS_varkuthar._draw_torso(surface, cx, cy - 4, facing, phase)
        # Back arm (holds spear back-position)
        # Spear position depends on attack phase
        # Idle: spear pointing down-forward
        # Attack wind-up: spear pulled back overhead
        # Attack throw: spear extended forward
        spear_phase = 0
        if action == "attack":
            if attack_progress < 0.4:
                spear_phase = attack_progress / 0.4  # 0 → 1 (winding up)
            elif attack_progress < 0.6:
                spear_phase = 1 - (attack_progress - 0.4) / 0.2  # 1 → 0 (throwing)
            else:
                spear_phase = 0  # thrown
        # Front arm (holds spear front-position)
        _NS_varkuthar._draw_front_arm_with_spear(surface, cx, cy - 4, facing, phase,
                                                   action, attack_progress, spear_phase)
        # Back arm (mostly hidden or slightly visible)
        _NS_varkuthar._draw_back_arm(surface, cx, cy - 4, facing, phase)
        # Head with skull mask
        _NS_varkuthar._draw_skull_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_red_cape(surface, cx, cy, facing, phase):
        """Red flowing cape behind body."""
        wave1 = math.sin(phase * 0.7) * 3
        wave2 = math.sin(phase * 0.7 + 1.5) * 3
        # Cape shape (flowing back and down)
        # Cape is BEHIND boss, so mirror based on facing
        back = -facing
        cape_pts = [
            (cx + back * 3, cy - 4),
            (cx + back * 8, cy - 2),
            (cx + back * 14 + int(wave1), cy + 8),
            (cx + back * 18 + int(wave2), cy + 20),
            (cx + back * 20 + int(wave1), cy + 32),
            (cx + back * 16, cy + 42),
            (cx + back * 8, cy + 46),
            (cx + back * 2, cy + 44),
            (cx + back * 2, cy + 20),
            (cx + back * 4, cy + 4),
        ]
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in cape_pts])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_darkest"], cape_pts)
        # Cape mid tone
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_dark"], [
            (cx + back * 4, cy - 3),
            (cx + back * 8, cy - 1),
            (cx + back * 12 + int(wave1 * 0.7), cy + 10),
            (cx + back * 16 + int(wave2 * 0.7), cy + 22),
            (cx + back * 16 + int(wave1 * 0.7), cy + 32),
            (cx + back * 12, cy + 40),
            (cx + back * 6, cy + 42),
            (cx + back * 3, cy + 40),
            (cx + back * 3, cy + 20),
        ])
        # Cape light tone (highlight)
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_mid"], [
            (cx + back * 5, cy - 1),
            (cx + back * 8, cy + 1),
            (cx + back * 12, cy + 16),
            (cx + back * 12, cy + 30),
            (cx + back * 8, cy + 38),
            (cx + back * 5, cy + 38),
            (cx + back * 4, cy + 20),
        ])
        # Cape ripples (fabric folds)
        for i, y_off in enumerate((8, 18, 28)):
            fold_x = cx + back * (6 + int(math.sin(phase + i) * 2))
            pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_darkest"],
                             (fold_x, cy + y_off),
                             (fold_x + back * 6, cy + y_off + 3), 1)
            pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_light"],
                             (fold_x - back, cy + y_off),
                             (fold_x + back * 5, cy + y_off + 3), 1)
    def _draw_red_mane(surface, cx, cy, facing, phase):
        """Long red mane flowing back (like Huskar's mohawk-mane)."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        back = -facing
        # Mane goes up and back from head
        # Upper spike (mohawk top)
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + back * 1 + int(wave1 * 0.3), cy - 14),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_darkest"], [
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + back * 1 + int(wave1 * 0.3), cy - 15),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_dark"], [
            (cx - 1, cy - 4),
            (cx + 1, cy - 4),
            (cx + back * 1, cy - 13),
        ])
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_mid"],
                         (cx, cy - 3), (cx + back, cy - 12), 1)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_hot"],
                         (cx + back, cy - 12, 1, 1))
        # Long mane flowing back and down (multiple strands)
        for i, (start_off_x, start_off_y, curl_amount) in enumerate([
            (0, -2, 12), (-2, 0, 14), (2, 0, 14), (-3, 2, 12), (3, 2, 12),
        ]):
            start_x = cx + start_off_x
            start_y = cy + start_off_y
            # Strand curves back and down
            for seg in range(6):
                seg_t = seg / 5
                # Position: back and down
                strand_x = start_x + int(back * curl_amount * seg_t)
                strand_y = start_y + int(seg_t * 24) + int(math.sin(phase * 0.8 + i + seg_t * 2) * 2)
                # Draw strand segments
                if seg > 0:
                    thick = max(1, 4 - seg)
                    prev_x = start_x + int(back * curl_amount * (seg - 1) / 5)
                    prev_y = start_y + int((seg - 1) / 5 * 24) + \
                        int(math.sin(phase * 0.8 + i + (seg - 1) / 5 * 2) * 2)
                    _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                                           (prev_x + 1, prev_y + 1),
                                           (strand_x + 1, strand_y + 1), thick + 1)
                    _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["red_darkest"],
                                           (prev_x, prev_y),
                                           (strand_x, strand_y), thick)
                    _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["red_dark"],
                                           (prev_x, prev_y),
                                           (strand_x, strand_y), max(1, thick - 1))
                    _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["red_mid"],
                                           (prev_x, prev_y - 1),
                                           (strand_x, strand_y - 1), max(1, thick - 2))
            # Bright tip
            end_x = start_x + int(back * curl_amount)
            end_y = start_y + 24
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_light"],
                             (end_x, end_y, 1, 1))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_hot"],
                             (end_x, end_y, 1, 1))
    def _draw_loincloth(surface, cx, cy, facing, phase):
        """Teal-blue loincloth with red trim (tribal style)."""
        wave = math.sin(phase * 0.7) * 2
        # Loincloth base
        loin_pts = [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 10, cy + 6),
            (cx + 12 + int(wave), cy + 18),
            (cx + 8, cy + 30),
            (cx - 8, cy + 30),
            (cx - 12 + int(wave), cy + 18),
            (cx - 10, cy + 6),
        ]
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in loin_pts])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["skin_darkest"], loin_pts)
        # Teal mid
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["skin_dark"], [
            (cx - 7, cy + 1),
            (cx + 7, cy + 1),
            (cx + 9, cy + 6),
            (cx + 10, cy + 18),
            (cx + 6, cy + 28),
            (cx - 6, cy + 28),
            (cx - 10, cy + 18),
            (cx - 9, cy + 6),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["skin_mid"], [
            (cx - 6, cy + 2),
            (cx + 6, cy + 2),
            (cx + 8, cy + 8),
            (cx + 8, cy + 20),
            (cx + 4, cy + 26),
            (cx - 4, cy + 26),
            (cx - 8, cy + 20),
            (cx - 8, cy + 8),
        ])
        # Central highlight
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["skin_light"],
                         (cx - 3, cy + 4), (cx + 3, cy + 4), 1)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["skin_shine"],
                         (cx - 1, cy + 6), (cx + 1, cy + 6), 1)
        # Red loincloth strip in front (hanging piece)
        wave2 = math.sin(phase * 0.7 + 1) * 2
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_darkest"], [
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 5 + int(wave2), cy + 15),
            (cx + 3, cy + 28),
            (cx - 3, cy + 28),
            (cx - 5 + int(wave2), cy + 15),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_dark"], [
            (cx - 3, cy + 1),
            (cx + 3, cy + 1),
            (cx + 4 + int(wave2 * 0.7), cy + 15),
            (cx + 2, cy + 26),
            (cx - 2, cy + 26),
            (cx - 4 + int(wave2 * 0.7), cy + 15),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_mid"], [
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 2, cy + 22),
            (cx - 2, cy + 22),
        ])
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_hot"],
                         (cx, cy + 12, 1, 2))
        # Belt (gold horizontal)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx - 9, cy + 1), (cx + 9, cy + 1), 3)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["gold_dark"],
                         (cx - 9, cy), (cx + 9, cy), 3)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["gold_mid"],
                         (cx - 9, cy), (cx + 9, cy), 2)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["gold_light"],
                         (cx - 9, cy - 1), (cx + 9, cy - 1), 1)
        # Skull ornament at belt center
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                                (cx + 1, cy + 1), 3)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["bone_darkest"],
                                (cx, cy), 3)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["bone_dark"],
                                (cx, cy), 2)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["bone_mid"],
                                (cx, cy - 1), 1)
        # Skull eye holes
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx - 1, cy, 1, 1))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx + 1, cy, 1, 1))
        # Leg armor / knee guards
        for side in (-1, 1):
            _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["gold_dark"], [
                (cx + side * 5, cy + 22),
                (cx + side * 9, cy + 22),
                (cx + side * 8, cy + 28),
                (cx + side * 5, cy + 28),
            ])
            _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["gold_mid"], [
                (cx + side * 6, cy + 23),
                (cx + side * 8, cy + 23),
                (cx + side * 7, cy + 27),
                (cx + side * 6, cy + 27),
            ])
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_light"],
                             (cx + side * 7, cy + 24, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular teal-blue tribal torso."""
        # Torso shape (broad chest, tapered waist)
        torso_pts = [
            (cx - 11, cy - 6),
            (cx + 11, cy - 6),
            (cx + 12, cy - 2),
            (cx + 10, cy + 5),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 10, cy + 5),
            (cx - 12, cy - 2),
        ]
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["skin_darkest"], torso_pts)
        # Skin mid tone
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["skin_dark"], [
            (cx - 10, cy - 5),
            (cx + 10, cy - 5),
            (cx + 11, cy - 2),
            (cx + 9, cy + 4),
            (cx + 7, cy + 9),
            (cx - 7, cy + 9),
            (cx - 9, cy + 4),
            (cx - 11, cy - 2),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["skin_mid"], [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 9, cy - 1),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
            (cx - 9, cy - 1),
        ])
        # Chest muscle definition (highlights)
        # Pectoral shadows (split down middle)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["skin_darkest"],
                         (cx, cy - 3), (cx, cy + 5), 1)
        # Pec highlights
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["skin_light"],
                         (cx - 5, cy - 2), (cx - 3, cy + 1), 1)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["skin_light"],
                         (cx + 3, cy - 2), (cx + 5, cy + 1), 1)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["skin_shine"],
                         (cx - 4, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["skin_shine"],
                         (cx + 3, cy - 2, 2, 1))
        # Ab definition
        for i in range(2):
            y_ab = cy + 2 + i * 3
            pygame.draw.line(surface, _NS_varkuthar.PALETTE["skin_darkest"],
                             (cx - 4, y_ab), (cx + 4, y_ab), 1)
        # Gold shoulder plates (both sides)
        for side in (-1, 1):
            # Shoulder pauldron
            _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"], [
                (cx + side * 9, cy - 6),
                (cx + side * 14, cy - 5),
                (cx + side * 15, cy),
                (cx + side * 11, cy + 2),
                (cx + side * 9, cy),
            ])
            _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["gold_dark"], [
                (cx + side * 9, cy - 7),
                (cx + side * 13, cy - 6),
                (cx + side * 14, cy),
                (cx + side * 10, cy + 1),
                (cx + side * 9, cy - 1),
            ])
            _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["gold_mid"], [
                (cx + side * 10, cy - 6),
                (cx + side * 12, cy - 5),
                (cx + side * 13, cy - 1),
                (cx + side * 11, cy),
            ])
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_light"],
                             (cx + side * 11, cy - 5, 2, 1))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_shine"],
                             (cx + side * 11, cy - 5, 1, 1))
        # Chest ornament / necklace with skull (Huskar-style)
        # Necklace beads
        for i, x_off in enumerate((-4, -2, 0, 2, 4)):
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_dark"],
                             (cx + x_off, cy - 5, 1, 1))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_mid"],
                             (cx + x_off, cy - 5, 1, 1))
        # Small skull pendant hanging from necklace
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                                (cx + 1, cy - 1), 2)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["bone_dark"],
                                (cx, cy - 2), 2)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["bone_mid"],
                                (cx, cy - 2), 1)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx - 1, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx + 1, cy - 2, 1, 1))
    def _draw_front_arm_with_spear(surface, cx, cy, facing, phase, action,
                                     attack_progress, spear_phase):
        """Front arm holds/throws the spear."""
        wave = math.sin(phase * 0.7) * 1
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 3
        # Hand position varies based on attack phase
        if action == "attack":
            if attack_progress < 0.4:
                # Wind up: hand goes UP and BACK (raising spear overhead)
                t = attack_progress / 0.4
                hand_x = int(cx + facing * (8 - t * 12))  # goes back
                hand_y = int(cy - t * 10)  # goes up
            elif attack_progress < 0.6:
                # Throw: hand rockets FORWARD
                t = (attack_progress - 0.4) / 0.2
                hand_x = int(cx + facing * (-4 + t * 22))
                hand_y = int(cy - 10 + t * 12)
            else:
                # Recovery: hand extends forward
                t = (attack_progress - 0.6) / 0.4
                hand_x = int(cx + facing * (18 - t * 4))
                hand_y = int(cy + 2 - t * 2)
        else:
            # Idle: hand holds spear at side, spear pointing forward
            hand_x = cx + facing * 14
            hand_y = cy + int(wave)
        elbow_x = (shoulder_x + hand_x) // 2 + facing * 2
        elbow_y = (shoulder_y + hand_y) // 2 + 2
        # Upper arm
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        # Gold bracer
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_dark"],
                         (elbow_x - 2, elbow_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_mid"],
                         (elbow_x - 2, elbow_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_light"],
                         (elbow_x - 1, elbow_y - 1, 2, 1))
        # Forearm
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 5)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Wrist bracer
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_dark"],
                         (hand_x - facing * 2 - 1, hand_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_mid"],
                         (hand_x - facing * 2 - 1, hand_y - 1, 3, 2))
        # Hand
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["skin_dark"],
                                (hand_x, hand_y), 3)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["skin_mid"],
                                (hand_x, hand_y), 2)
        # DRAW SPEAR (only if not in throw motion or just after throw)
        # During throw motion (0.4-0.55), spear is being thrown so shown mid-air by projectile
        show_spear = True
        if action == "attack" and 0.5 < attack_progress < 0.9:
            show_spear = False  # spear is now a projectile
        if show_spear:
            _NS_varkuthar._draw_spear(surface, hand_x, hand_y, facing, phase,
                                        action, attack_progress, spear_phase)
    def _draw_spear(surface, hand_x, hand_y, facing, phase, action, attack_progress,
                     spear_phase):
        """Ornate tribal spear with red-orange glowing tip."""
        # Spear orientation depends on phase
        # Idle: pointing forward-horizontal
        # Wind up (spear_phase near 1): pointing UP-BACK (over shoulder)
        # Throw: transitions to forward
        # Base angle (idle = pointing forward horizontal)
        # spear_phase 0 = horizontal forward, spear_phase 1 = up-back
        base_angle = spear_phase * math.pi * 0.65  # 0 → up-back rotation
        # Direction from hand
        if facing == 1:
            spear_angle = -base_angle  # rotate up-left (back)
        else:
            spear_angle = math.pi + base_angle  # mirror
        # Spear length
        spear_forward_len = 30  # front portion (from hand to tip)
        spear_back_len = 15     # back portion (butt)
        # Tip position (forward)
        tip_x = hand_x + int(math.cos(spear_angle) * spear_forward_len)
        tip_y = hand_y + int(math.sin(spear_angle) * spear_forward_len)
        # Butt position (backward)
        butt_x = hand_x - int(math.cos(spear_angle) * spear_back_len)
        butt_y = hand_y - int(math.sin(spear_angle) * spear_back_len)
        # Draw shaft (metal/wooden)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                              (butt_x + 1, butt_y + 1), (tip_x + 1, tip_y + 1), 4)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_dark"],
                              (butt_x, butt_y), (tip_x, tip_y), 3)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_mid"],
                              (butt_x, butt_y), (tip_x, tip_y), 2)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_light"],
                              (butt_x, butt_y - 1), (tip_x, tip_y - 1), 1)
        # Shaft wrappings (grip)
        for seg_t in (0.35, 0.5, 0.65):
            sxx = int(butt_x + (tip_x - butt_x) * seg_t)
            syy = int(butt_y + (tip_y - butt_y) * seg_t)
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_dark"],
                             (sxx - 1, syy - 1, 3, 2))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_mid"],
                             (sxx, syy, 1, 1))
        # Gold band near tip (spearhead base decoration)
        band_t = 0.78
        band_x = int(butt_x + (tip_x - butt_x) * band_t)
        band_y = int(butt_y + (tip_y - butt_y) * band_t)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_dark"],
                         (band_x - 2, band_y - 2, 5, 4))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_mid"],
                         (band_x - 1, band_y - 2, 3, 3))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_light"],
                         (band_x, band_y - 2, 1, 2))
        # SPEARHEAD (leaf-shaped, glowing)
        # Perpendicular for width
        perp = spear_angle + math.pi / 2
        head_len = 12
        head_width = 4
        head_base_x = int(butt_x + (tip_x - butt_x) * 0.82)
        head_base_y = int(butt_y + (tip_y - butt_y) * 0.82)
        head_mid_x = int(butt_x + (tip_x - butt_x) * 0.92)
        head_mid_y = int(butt_y + (tip_y - butt_y) * 0.92)
        # Spearhead polygon (leaf shape)
        base_a_x = head_base_x + int(math.cos(perp) * 2)
        base_a_y = head_base_y + int(math.sin(perp) * 2)
        base_b_x = head_base_x - int(math.cos(perp) * 2)
        base_b_y = head_base_y - int(math.sin(perp) * 2)
        mid_a_x = head_mid_x + int(math.cos(perp) * head_width)
        mid_a_y = head_mid_y + int(math.sin(perp) * head_width)
        mid_b_x = head_mid_x - int(math.cos(perp) * head_width)
        mid_b_y = head_mid_y - int(math.sin(perp) * head_width)
        spearhead_pts = [
            (base_a_x, base_a_y),
            (mid_a_x, mid_a_y),
            (tip_x, tip_y),
            (mid_b_x, mid_b_y),
            (base_b_x, base_b_y),
        ]
        # Shadow
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in spearhead_pts])
        # Base
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["metal_dark"], spearhead_pts)
        # Mid highlight
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["metal_mid"], [
            (base_a_x, base_a_y),
            (int((mid_a_x + head_mid_x) / 2), int((mid_a_y + head_mid_y) / 2)),
            (tip_x, tip_y),
            (int((mid_b_x + head_mid_x) / 2), int((mid_b_y + head_mid_y) / 2)),
            (base_b_x, base_b_y),
        ])
        # Central fuller (highlight line)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["metal_light"],
                         (head_base_x, head_base_y), (tip_x, tip_y), 1)
        # GLOWING ORANGE/RED EDGE
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        # Red glow along one edge
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_dark"],
                         (base_a_x, base_a_y), (mid_a_x, mid_a_y), 1)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_hot"],
                         (mid_a_x, mid_a_y), (tip_x, tip_y), 1)
        # Bright tip
        for r in range(4, 0, -1):
            alpha = _NS_varkuthar._alpha(200 * (4 - r) / 4 * pulse)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                    (tip_x, tip_y), r)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_shine"],
                                (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Fire embers along spearhead
        for i in range(3):
            ember_t = (phase + i * 0.4) % 1.0
            ex = tip_x - int(math.cos(spear_angle) * 6 * ember_t)
            ey = tip_y - int(math.sin(spear_angle) * 6 * ember_t)
            ex += int(math.sin(phase * 4 + i) * 3)
            ey += int(math.cos(phase * 4 + i) * 3)
            alpha_e = _NS_varkuthar._alpha(220 * (1 - ember_t))
            pygame.draw.rect(surface,
                             (*_NS_varkuthar.PALETTE["fire_hot"], alpha_e),
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_varkuthar.PALETTE["fire_shine"], alpha_e),
                             (ex, ey, 1, 1))
        # BUTT (back end of spear with feather/tassel)
        # Small feather tuft
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_darkest"], [
            (butt_x, butt_y),
            (butt_x - int(math.cos(spear_angle) * 4),
             butt_y - int(math.sin(spear_angle) * 4) - 2),
            (butt_x - int(math.cos(spear_angle) * 4),
             butt_y - int(math.sin(spear_angle) * 4) + 2),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_dark"], [
            (butt_x, butt_y),
            (butt_x - int(math.cos(spear_angle) * 3),
             butt_y - int(math.sin(spear_angle) * 3) - 1),
            (butt_x - int(math.cos(spear_angle) * 3),
             butt_y - int(math.sin(spear_angle) * 3) + 1),
        ])
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm (partial visibility)."""
        wave = math.sin(phase * 0.7) * 1
        back = -facing
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 2
        elbow_x = cx + back * 8
        elbow_y = cy + 4 + int(wave)
        hand_x = cx + back * 6
        hand_y = cy + 10 + int(wave)
        # Upper arm
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 4)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        # Bracer
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_dark"],
                         (elbow_x - 1, elbow_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_mid"],
                         (elbow_x - 1, elbow_y - 1, 3, 2))
        # Forearm
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Fist
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["skin_mid"],
                                (hand_x, hand_y), 1)
    def _draw_skull_head(surface, cx, cy, facing, phase, action):
        """Skull mask head with tribal markings."""
        # Skull mask base (rounded, with jaw)
        skull_pts = [
            (cx - 6, cy + 6),   # bottom left
            (cx - 7, cy),        # left back
            (cx - 6, cy - 5),    # upper left
            (cx - 2, cy - 8),    # forehead left
            (cx + 2, cy - 8),    # forehead right
            (cx + 6, cy - 5),    # upper right
            (cx + 7, cy),        # right back
            (cx + 6, cy + 6),    # bottom right
            (cx + 3, cy + 8),    # jaw right
            (cx - 3, cy + 8),    # jaw left
        ]
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in skull_pts])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_darkest"], skull_pts)
        # Bone tone (aged)
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_dark"], [
            (cx - 5, cy + 5),
            (cx - 6, cy),
            (cx - 5, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 5, cy + 5),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy),
            (cx - 4, cy - 3),
            (cx - 1, cy - 6),
            (cx + 1, cy - 6),
            (cx + 4, cy - 3),
            (cx + 5, cy),
            (cx + 4, cy + 4),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
        ])
        # Highlights on skull (light source from above)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["bone_light"],
                         (cx - 2, cy - 6), (cx + 2, cy - 6), 1)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["bone_shine"],
                         (cx - 1, cy - 6), (cx + 1, cy - 6), 1)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_light"],
                         (cx - 4, cy - 3, 8, 1))
        # RED TRIBAL MARKING (vertical line through center)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_darkest"],
                         (cx, cy - 8), (cx, cy - 5), 1)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_dark"],
                         (cx, cy - 8, 1, 1))
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_hot"],
                         (cx, cy - 7, 1, 1))
        # Red war paint stripes below eyes
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_darkest"],
                             (cx + side * 3, cy + 2), (cx + side * 3, cy + 5), 1)
            pygame.draw.line(surface, _NS_varkuthar.PALETTE["red_mid"],
                             (cx + side * 3, cy + 2), (cx + side * 3, cy + 4), 1)
        # EYE SOCKETS (deep dark with red glow)
        for eye_off in (-3, 3):
            ex = cx + eye_off
            ey = cy - 2
            # Deep socket
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 3))
            # Glowing red eye inside socket
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            for r in range(3, 0, -1):
                alpha = _NS_varkuthar._alpha(180 * (3 - r) / 3 * pulse)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
        # NOSE HOLE (upside-down triangle)
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["shadow_deep"], [
            (cx, cy + 2), (cx - 1, cy), (cx + 1, cy),
        ])
        # TEETH ROW (bared teeth)
        for i, x_off in enumerate((-3, -1, 1, 3)):
            tx = cx + x_off
            # Tooth
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_light"],
                             (tx, cy + 5, 1, 2))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_shine"],
                             (tx, cy + 5, 1, 1))
        # Teeth divisions
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx - 4, cy + 5), (cx + 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                         (cx - 4, cy + 7), (cx + 4, cy + 7), 1)
        # Small horns/decorative bones on head
        # Left horn
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_darkest"], [
            (cx - 6, cy - 5), (cx - 8, cy - 8), (cx - 5, cy - 7),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_dark"], [
            (cx - 5, cy - 5), (cx - 7, cy - 7), (cx - 5, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_mid"],
                         (cx - 7, cy - 7, 1, 1))
        # Right horn
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_darkest"], [
            (cx + 6, cy - 5), (cx + 8, cy - 8), (cx + 5, cy - 7),
        ])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["bone_dark"], [
            (cx + 5, cy - 5), (cx + 7, cy - 7), (cx + 5, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["bone_mid"],
                         (cx + 7, cy - 7, 1, 1))
        # Ear ornaments (rings)
        for side in (-1, 1):
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_dark"],
                             (cx + side * 7, cy + 2, 1, 1))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_mid"],
                             (cx + side * 7, cy + 3, 1, 2))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["gold_light"],
                             (cx + side * 7, cy + 3, 1, 1))
    # ============================================================
    # RANGED PROJECTILE - Spear throw (basic attack)
    # ============================================================
    def _draw_spear_throw_projectile(surface, boss, x, y, progress):
        """Spear projectile flying to target after throw."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_varkuthar._target_position(boss, x, y)
        # Launch point at hand
        start_x = x + facing * 24
        start_y = y - 8
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Spear angle
        angle_to = math.atan2(ty - start_y, tx - start_x)
        # Draw spear as an elongated shape flying
        spear_len = 20
        # Tip
        tip_x = bx + int(math.cos(angle_to) * spear_len // 2)
        tip_y = by + int(math.sin(angle_to) * spear_len // 2)
        # Butt
        butt_x = bx - int(math.cos(angle_to) * spear_len // 2)
        butt_y = by - int(math.sin(angle_to) * spear_len // 2)
        # Fire trail behind spear
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_varkuthar._alpha(230 - i * 25)
            size = max(1, 6 - i)
            _NS_varkuthar._aacircle(surface, (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                    (px, py), size)
            _NS_varkuthar._aacircle(surface, (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_varkuthar._aacircle(surface, (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                    (px, py), max(1, size - 2))
            pygame.draw.rect(surface, (*_NS_varkuthar.PALETTE["fire_shine"], alpha),
                             (px, py, 1, 1))
        # Draw spear body
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                              (butt_x + 1, butt_y + 1), (tip_x + 1, tip_y + 1), 3)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_dark"],
                              (butt_x, butt_y), (tip_x, tip_y), 2)
        _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_mid"],
                              (butt_x, butt_y), (tip_x, tip_y), 1)
        # Glowing tip
        for r in range(5, 0, -1):
            alpha = _NS_varkuthar._alpha(220 * (5 - r) / 5)
            _NS_varkuthar._aacircle(surface, (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                    (tip_x, tip_y), r)
        _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_shine"],
                                (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_varkuthar.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Butt feather
        perp = angle_to + math.pi / 2
        f1_x = butt_x + int(math.cos(perp) * 3)
        f1_y = butt_y + int(math.sin(perp) * 3)
        f2_x = butt_x - int(math.cos(perp) * 3)
        f2_y = butt_y - int(math.sin(perp) * 3)
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_dark"],
                            [(butt_x, butt_y), (f1_x, f1_y),
                             (butt_x - int(math.cos(angle_to) * 4),
                              butt_y - int(math.sin(angle_to) * 4))])
        _NS_varkuthar._poly(surface, _NS_varkuthar.PALETTE["red_mid"],
                            [(butt_x, butt_y), (f2_x, f2_y),
                             (butt_x - int(math.cos(angle_to) * 4),
                              butt_y - int(math.sin(angle_to) * 4))])
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 20)
            alpha = _NS_varkuthar._alpha(240 * (1 - st))
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                    (tx, ty), radius, 2)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                    (tx, ty), max(1, radius - 5), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_varkuthar.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = _NS_varkuthar._alpha((14 - radius) * 15 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius // 2,
                 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (15, 3, 3, 170), (10, 10, 120, 10))
        pygame.draw.ellipse(shadow, (100, 20, 15, 100), (18, 12, 104, 6))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_fire_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Fire embers rising below boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((140, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_varkuthar._alpha((30 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                    (70 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(20, 3, -2):
            alpha = _NS_varkuthar._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_varkuthar.PALETTE["red_dark"], alpha),
                    (70 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising fire embers
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.6 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_varkuthar._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_varkuthar.PALETTE["fire_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Red blood particles
        for i in range(6):
            spark_t = (phase * 0.7 + i * 0.16) % 1.0
            ex = cx - 26 + i * 10 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_varkuthar._alpha(200 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_varkuthar.PALETTE["red_hot"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_varkuthar.PALETTE["red_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_varkuthar._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_fire_aura(surface, x, y, phase):
        """Big fire aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_varkuthar._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_varkuthar._aacircle(aura,
                                        (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                        (120, 105), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_varkuthar._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_varkuthar._aacircle(aura,
                                        (*_NS_varkuthar.PALETTE["red_dark"], alpha),
                                        (120, 105), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_varkuthar._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_varkuthar._aacircle(aura,
                                        (*_NS_varkuthar.PALETTE["red_mid"], alpha),
                                        (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # Floating fire embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_varkuthar.PALETTE["fire_hot"] if i % 2 == 0 \
                else _NS_varkuthar.PALETTE["red_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["fire_shine"], (sx, sy, 1, 1))
    def _draw_ground_embers(surface, x, y, phase, skill):
        """Ground ember ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_varkuthar.PALETTE["red_darkest"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_varkuthar.PALETTE["red_dark"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_varkuthar.PALETTE["fire_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_varkuthar.PALETTE["fire_shine"],
                                 _NS_varkuthar._alpha(180 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - IGNIS SPEAR (extra big flaming spear projectile)
    # ============================================================
    def _draw_ignis_spear(surface, boss, x, y, timer, phase):
        """Enhanced fire spear with big trail + splash damage burn."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_varkuthar._target_position(boss, x, y)
        if progress < 0.25:
            # Charge at hand
            t = progress / 0.25
            hand_x = x + facing * 24
            hand_y = y - 8
            cr = int(5 + t * 10)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_varkuthar._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_mid"],
                                    (hand_x, hand_y), cr - 1)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_hot"],
                                    (hand_x, hand_y), max(1, cr - 3))
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_shine"],
                                    (hand_x, hand_y), max(1, cr - 5))
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_varkuthar.PALETTE["fire_shine"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 30
            start_y = y - 8
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            angle_to = math.atan2(ty - start_y, tx - start_x)
            # Large fire trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_varkuthar._alpha(240 - i * 20)
                size = max(1, 9 - i)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_darkest"], alpha),
                                        (px, py), size)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                        (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_varkuthar.PALETTE["fire_shine"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Draw large flaming spear head
            spear_len = 24
            tip_x = bx + int(math.cos(angle_to) * spear_len // 2)
            tip_y = by + int(math.sin(angle_to) * spear_len // 2)
            butt_x = bx - int(math.cos(angle_to) * spear_len // 2)
            butt_y = by - int(math.sin(angle_to) * spear_len // 2)
            _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["shadow_deep"],
                                  (butt_x + 1, butt_y + 1),
                                  (tip_x + 1, tip_y + 1), 4)
            _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_dark"],
                                  (butt_x, butt_y), (tip_x, tip_y), 3)
            _NS_varkuthar._aaline(surface, _NS_varkuthar.PALETTE["metal_mid"],
                                  (butt_x, butt_y), (tip_x, tip_y), 2)
            # Big bright fire head at tip
            for r in range(14, 3, -2):
                alpha = _NS_varkuthar._alpha(100 * (14 - r) / 14)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                        (tip_x, tip_y), r)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_dark"], (tip_x, tip_y), 8)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_mid"], (tip_x, tip_y), 5)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_hot"], (tip_x, tip_y), 3)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["fire_shine"], (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["white"], (tip_x, tip_y, 1, 1))
            # Big impact with burn splash
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_varkuthar._alpha(240 * (1 - st))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_darkest"], alpha),
                                        (tx, ty), radius + 4, 3)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_varkuthar.PALETTE["fire_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - CRIMSON RITE (self buff - flame aura)
    # ============================================================
    def _draw_crimson_rite_ground(surface, boss, x, y, timer, phase):
        """Fire circle under boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_varkuthar._alpha(200 - i * 50)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                    (x, y + 42), r, 2)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                    (x, y + 42), r, 1)
    def _draw_crimson_rite_overlay(surface, boss, x, y, timer, phase):
        """Fire overlay engulfing boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Rising flames around boss body
        for i in range(15):
            angle = phase * 1.5 + i * math.pi / 7.5
            base_r = 30
            fx = x + int(math.cos(angle) * base_r)
            fy_base = y + 20 + int(math.sin(angle) * base_r * 0.5)
            # Flame rises upward
            rise_t = (phase * 1.2 + i * 0.15) % 1.0
            fy = fy_base - int(rise_t * 40)
            alpha = _NS_varkuthar._alpha(220 * (1 - rise_t))
            # Flame shape
            flame_size = 5 - int(rise_t * 3)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_dark"], alpha),
                                    (fx, fy), flame_size + 1)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_mid"], alpha),
                                    (fx, fy), flame_size)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["fire_hot"], alpha),
                                    (fx, fy), max(1, flame_size - 1))
            pygame.draw.rect(surface,
                             (*_NS_varkuthar.PALETTE["fire_shine"], alpha),
                             (fx, fy - 1, 1, 1))
    # ============================================================
    # SKILL E - BLOOD FRENZY (blood spear thrust)
    # ============================================================
    def _draw_blood_frenzy(surface, boss, x, y, timer, phase):
        """Piercing blood-red spear projectile."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_varkuthar._target_position(boss, x, y)
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            hand_x = x + facing * 24
            hand_y = y - 4
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_varkuthar._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_mid"],
                                    (hand_x, hand_y), cr - 2)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_hot"],
                                    (hand_x, hand_y), max(1, cr - 4))
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_shine"],
                                    (hand_x, hand_y), max(1, cr - 6))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 26
            start_y = y - 4
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
            angle_to = math.atan2(ty - start_y, tx - start_x)
            # Thick blood beam layered
            for layer_i, (thick, alpha_val, color) in enumerate([
                (7, 100, _NS_varkuthar.PALETTE["red_darkest"]),
                (5, 150, _NS_varkuthar.PALETTE["red_dark"]),
                (3, 200, _NS_varkuthar.PALETTE["red_mid"]),
                (2, 240, _NS_varkuthar.PALETTE["red_hot"]),
                (1, 255, _NS_varkuthar.PALETTE["red_shine"]),
            ]):
                pygame.draw.line(surface, (*color, alpha_val),
                                 (start_x, start_y), (end_x, end_y), thick)
            # Blood spearhead at tip
            for r in range(10, 0, -1):
                alpha = _NS_varkuthar._alpha(200 * (10 - r) / 10)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_light"], alpha),
                                        (end_x, end_y), r)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_darkest"],
                                    (end_x, end_y), 5)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_hot"],
                                    (end_x, end_y), 3)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_shine"],
                                    (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_varkuthar.PALETTE["white"], (end_x, end_y, 1, 1))
            # Blood droplet sparks along beam
            perp = angle_to + math.pi / 2
            for i in range(8):
                sp_t = (phase * 3 + i * 0.13) % 1.0
                spx = int(start_x + (end_x - start_x) * sp_t)
                spy = int(start_y + (end_y - start_y) * sp_t)
                spx += int(math.cos(perp) * math.sin(phase * 5 + i) * 4)
                spy += int(math.sin(perp) * math.sin(phase * 5 + i) * 4)
                pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_hot"], (spx, spy, 1, 1))
                pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_shine"], (spx, spy, 1, 1))
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                impact_r = int(12 + st * 22)
                alpha = _NS_varkuthar._alpha(230 * (1 - st))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_dark"], alpha),
                                        (tx, ty), impact_r + 3, 3)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_mid"], alpha),
                                        (tx, ty), impact_r, 2)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_hot"], alpha),
                                        (tx, ty), max(1, impact_r - 6), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * impact_r)
                    ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                    pygame.draw.rect(surface, (*_NS_varkuthar.PALETTE["red_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL R - SOULPIERCE (massive blood siphon beam)
    # ============================================================
    def _draw_soulpierce_ground(surface, boss, x, y, timer, phase):
        """Ground marks."""
        tx, ty = _NS_varkuthar._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_varkuthar.PALETTE["red_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_varkuthar.PALETTE["red_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_soulpierce_foreground(surface, boss, x, y, timer, phase):
        """Massive blood beam + tendrils siphoning life from target back to boss."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_varkuthar._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            cr = int(6 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_varkuthar._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_darkest"], alpha),
                                        (start_x, start_y), r)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_hot"],
                                    (start_x, start_y), max(1, cr - 5))
            _NS_varkuthar._aacircle(surface, _NS_varkuthar.PALETTE["red_shine"],
                                    (start_x, start_y), max(1, cr - 7))
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = start_x + int(math.cos(angle) * (cr + 4))
                sy = start_y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_varkuthar.PALETTE["red_shine"], (sx, sy, 1, 1))
        elif progress < 0.85:
            # SUSTAINED BEAM (siphon)
            t = (progress - 0.2) / 0.65
            intensity = math.sin(t * math.pi) if t < 0.9 else 0.8
            angle_to = math.atan2(ty - start_y, tx - start_x)
            perp = angle_to + math.pi / 2
            # Multi-layer beam
            for layer_i, (thick, alpha_val, color) in enumerate([
                (12, 100, _NS_varkuthar.PALETTE["red_darkest"]),
                (9, 140, _NS_varkuthar.PALETTE["red_dark"]),
                (6, 180, _NS_varkuthar.PALETTE["red_mid"]),
                (4, 220, _NS_varkuthar.PALETTE["red_hot"]),
                (2, 250, _NS_varkuthar.PALETTE["red_shine"]),
                (1, 255, _NS_varkuthar.PALETTE["white"]),
            ]):
                actual_alpha = _NS_varkuthar._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (tx, ty), thick)
            # Blood tendrils spiraling around beam (siphoning effect)
            beam_len = math.sqrt((tx - start_x) ** 2 + (ty - start_y) ** 2)
            for i in range(int(beam_len / 8)):
                seg_t = i * 8 / beam_len
                if seg_t > 1:
                    break
                bx = start_x + (tx - start_x) * seg_t
                by = start_y + (ty - start_y) * seg_t
                # Spiral offset
                spiral_a = phase * 4 + seg_t * math.pi * 4
                offset = math.sin(spiral_a) * 8
                px = int(bx + math.cos(perp) * offset)
                py = int(by + math.sin(perp) * offset)
                alpha_p = _NS_varkuthar._alpha(220 * intensity)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_darkest"], alpha_p),
                                        (px, py), 3)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_mid"], alpha_p),
                                        (px, py), 2)
                pygame.draw.rect(surface,
                                 (*_NS_varkuthar.PALETTE["red_shine"], alpha_p),
                                 (px, py, 1, 1))
            # Blood particles FLOWING from target back to source (siphon)
            for i in range(10):
                flow_t = (phase * 1.5 + i * 0.1) % 1.0
                # From target (flow_t=0) to source (flow_t=1)
                fx = int(tx + (start_x - tx) * flow_t)
                fy = int(ty + (start_y - ty) * flow_t)
                # Small wiggle
                fx += int(math.sin(phase * 3 + i) * 4)
                fy += int(math.cos(phase * 3 + i) * 4)
                alpha_f = _NS_varkuthar._alpha(230 * intensity * (1 - flow_t * 0.5))
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_dark"], alpha_f),
                                        (fx, fy), 3)
                _NS_varkuthar._aacircle(surface,
                                        (*_NS_varkuthar.PALETTE["red_hot"], alpha_f),
                                        (fx, fy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_varkuthar.PALETTE["red_shine"], alpha_f),
                                 (fx, fy, 1, 1))
            # Impact burst at target (continuous)
            burst_r = int(15 + math.sin(phase * 3) * 4)
            burst_alpha = _NS_varkuthar._alpha(220 * intensity)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["red_darkest"], burst_alpha),
                                    (tx, ty), burst_r + 3, 3)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["red_dark"], burst_alpha),
                                    (tx, ty), burst_r, 3)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["red_mid"], burst_alpha),
                                    (tx, ty), max(1, burst_r - 5), 2)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["red_hot"], burst_alpha),
                                    (tx, ty), max(1, burst_r - 10), 1)
            _NS_varkuthar._aacircle(surface,
                                    (*_NS_varkuthar.PALETTE["red_shine"], burst_alpha),
                                    (tx, ty), max(1, burst_r // 4))
            # Radial sparks at impact
            for i in range(10):
                spark_a = i * math.pi / 5 + phase * 2
                ex = tx + int(math.cos(spark_a) * burst_r)
                ey = ty + int(math.sin(spark_a) * burst_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_varkuthar.PALETTE["red_shine"], burst_alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath: fading blood mist
            t = (progress - 0.85) / 0.15
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 35)
                alpha = _NS_varkuthar._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_varkuthar._aacircle(surface,
                                            (*_NS_varkuthar.PALETTE["red_dark"], alpha),
                                            (rx, ry), 3)
                    _NS_varkuthar._aacircle(surface,
                                            (*_NS_varkuthar.PALETTE["red_hot"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_varkuthar.PALETTE["red_shine"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# ZHYVREK (VOID REAPER) - Mini Boss
# ====================================================================

class _NS_zhyvrek:
    """Namespace zhyvrek - Shadow Reaper assassin boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark armor (charcoal shadow)
        "armor_darkest": (5, 5, 12),
        "armor_dark": (18, 18, 30),
        "armor_mid": (40, 40, 60),
        "armor_light": (85, 85, 115),
        "armor_shine": (150, 150, 180),
        # Cyan/blue shadow magic (main glow)
        "shadow_darkest": (5, 10, 30),
        "shadow_dark": (15, 40, 90),
        "shadow_mid": (40, 110, 200),
        "shadow_light": (100, 180, 255),
        "shadow_hot": (170, 220, 255),
        "shadow_shine": (220, 245, 255),
        # Red accents (Rhaast side - scythe blade tip, cracks)
        "red_dark": (60, 8, 12),
        "red_mid": (170, 25, 30),
        "red_hot": (240, 80, 70),
        "red_shine": (255, 180, 150),
        # Skin (pale, deathly)
        "skin_shadow": (75, 65, 75),
        "skin_dark": (130, 110, 115),
        "skin_mid": (185, 165, 165),
        "skin_light": (225, 205, 200),
        "skin_shine": (245, 230, 225),
        # Hair (raven black)
        "hair_darkest": (3, 3, 8),
        "hair_dark": (15, 15, 25),
        "hair_mid": (35, 35, 55),
        "hair_light": (70, 75, 100),
        "hair_shine": (130, 140, 170),
        # Scythe blade (dark metal + glow)
        "blade_dark": (20, 20, 30),
        "blade_mid": (55, 55, 75),
        "blade_light": (110, 115, 145),
        "blade_shine": (200, 210, 235),
        # Eye (blue glowing - assassin eye)
        "eye_socket": (5, 8, 20),
        "eye_dark": (20, 50, 100),
        "eye_mid": (70, 160, 240),
        "eye_light": (170, 220, 255),
        "eye_glow": (230, 250, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zhyvrek._clamp(color)
        if _NS_zhyvrek.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zhyvrek._clamp(color)
        if _NS_zhyvrek.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_zhyvrek._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zhyvrek(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zhyvrek._detect_moving(boss)
        _NS_zhyvrek._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_zv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_zhyvrek._draw_shadow_aura(surface, x, y, pulse)
        _NS_zhyvrek._draw_ground_runes(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX
        if active_skill == "w":
            _NS_zhyvrek._draw_phantom_pierce_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zhyvrek._draw_shadow_veil_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zhyvrek._draw_void_reap_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (skip body during R untargetable phase)
        is_untargetable = (active_skill == "r" and skill_timer > 30
                          and skill_timer < 80)
        if not is_untargetable:
            if attacking:
                _NS_zhyvrek._draw_zv_attack(surface, boss, x, y)
            elif moving:
                _NS_zhyvrek._draw_zv_float_move(surface, boss, x, y)
            else:
                _NS_zhyvrek._draw_zv_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_zhyvrek._draw_reaping_arc(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zhyvrek._draw_phantom_pierce_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zhyvrek._draw_shadow_veil_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zhyvrek._draw_void_reap_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zv_previous_timer", 0))
        active = bool(getattr(boss, "_zv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._zv_attack_active = True
            boss._zv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._zv_attack_frame = int(getattr(boss, "_zv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._zv_attack_active = False
            boss._zv_attack_frame = 0
            active = False
        boss._zv_previous_timer = timer
        boss._zv_attack_progress = (
            min(1.0, getattr(boss, "_zv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zv_last_x"):
            boss._zv_last_x = boss.x
            boss._zv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zv_last_x)
        dy = abs(boss.y - boss._zv_last_y)
        boss._zv_last_x = boss.x
        boss._zv_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_zv_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_zhyvrek._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_zhyvrek._draw_shadow_wisps(surface, x, y + 40, boss.pulse)
        _NS_zhyvrek._draw_zv_body(surface, x, y + bob,
                                   boss.direction, boss.pulse, "idle")
    def _draw_zv_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_zhyvrek._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_zhyvrek._draw_shadow_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_zhyvrek._draw_zv_body(surface, x + sway, y + bob,
                                   boss.direction, phase, "float")
    def _draw_zv_attack(surface, boss, x, y):
        """Scythe swing melee attack."""
        progress = getattr(boss, "_zv_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up (pull scythe back) → swing forward → recovery
        if progress < 0.35:
            t = progress / 0.35
            body_shift = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            t = (progress - 0.35) / 0.3
            body_shift = int((-5 + t * 16)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.65) / 0.35
            body_shift = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_zhyvrek._draw_float_shadow(surface, x + body_shift, y + 52, boss.pulse)
        _NS_zhyvrek._draw_shadow_wisps(surface, x + body_shift, y + 40, boss.pulse,
                                        intense=True)
        _NS_zhyvrek._draw_zv_body(surface, x + body_shift, y - lift + bob,
                                   boss.direction, boss.pulse, "attack", progress)
        # Scythe swing arc trail
        _NS_zhyvrek._draw_scythe_swing_arc(surface, boss, x + body_shift,
                                            y - lift + bob, progress)
    # ============================================================
    # BODY - Shadow Assassin (torso, arms, scythe, head, hair)
    # ============================================================
    def _draw_zv_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Assassin figure with massive scythe."""
        # Long trailing coat/cloak bottom
        _NS_zhyvrek._draw_cloak_bottom(surface, cx, cy + 6, facing, phase)
        # Long back hair
        _NS_zhyvrek._draw_back_hair(surface, cx, cy - 22, facing, phase)
        # Torso armor
        _NS_zhyvrek._draw_torso_armor(surface, cx, cy - 4, facing, phase)
        # Scythe (main weapon - held to the back-side, arcs forward when attacking)
        scythe_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                scythe_swing = -int(attack_progress / 0.35 * 10) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.35) / 0.3
                scythe_swing = int((-10 + t * 26)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                scythe_swing = int(16 * (1 - t)) * facing
        # Back arm holds the scythe shaft (drawn first, behind body)
        _NS_zhyvrek._draw_back_arm_with_scythe(surface, cx, cy - 4, facing, phase,
                                                scythe_swing, action, attack_progress)
        # Front arm (free arm, poised)
        _NS_zhyvrek._draw_front_arm(surface, cx, cy - 4, facing, phase, action,
                                     attack_progress)
        # Head + hair front
        _NS_zhyvrek._draw_assassin_head(surface, cx, cy - 24, facing, phase, action)
    def _draw_cloak_bottom(surface, cx, cy, facing, phase):
        """Trailing dark cloak with cyan-red split (representing Kayn's duality)."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        # Main cloak silhouette
        cloak_pts = [
            (cx - 9, cy),
            (cx + 9, cy),
            (cx + 13, cy + 10),
            (cx + 16 + int(wave1), cy + 22),
            (cx + 14 + int(wave2), cy + 34),
            (cx + 8, cy + 44),
            (cx - 8, cy + 44),
            (cx - 14 + int(wave2), cy + 34),
            (cx - 16 + int(wave1), cy + 22),
            (cx - 13, cy + 10),
        ]
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in cloak_pts])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_darkest"], cloak_pts)
        # Second layer
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_dark"], [
            (cx - 8, cy + 2),
            (cx + 8, cy + 2),
            (cx + 11, cy + 12),
            (cx + 13 + int(wave1 * 0.7), cy + 24),
            (cx + 10 + int(wave2 * 0.7), cy + 34),
            (cx + 4, cy + 42),
            (cx - 4, cy + 42),
            (cx - 10 + int(wave2 * 0.7), cy + 34),
            (cx - 13 + int(wave1 * 0.7), cy + 24),
            (cx - 11, cy + 12),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_mid"], [
            (cx - 6, cy + 4),
            (cx + 6, cy + 4),
            (cx + 9, cy + 16),
            (cx + 8, cy + 30),
            (cx + 3, cy + 38),
            (cx - 3, cy + 38),
            (cx - 8, cy + 30),
            (cx - 9, cy + 16),
        ])
        # Cyan glow strip on one side (left/back)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, y_off in enumerate((8, 14, 20, 28, 34)):
            alpha = _NS_zhyvrek._alpha(200 * pulse)
            pygame.draw.line(surface, _NS_zhyvrek.PALETTE["shadow_dark"],
                             (cx - 3, cy + y_off), (cx - 5, cy + y_off), 1)
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                             (cx - 4, cy + y_off, 1, 1))
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_shine"],
                             (cx - 4, cy + y_off, 1, 1))
        # Red glow strip on other side (Rhaast side)
        for i, y_off in enumerate((10, 16, 22, 30)):
            pygame.draw.line(surface, _NS_zhyvrek.PALETTE["red_dark"],
                             (cx + 3, cy + y_off), (cx + 5, cy + y_off), 1)
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["red_hot"],
                             (cx + 4, cy + y_off, 1, 1))
        # Belt (across waist)
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["armor_darkest"],
                         (cx - 9, cy + 4), (cx + 9, cy + 4), 3)
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["armor_dark"],
                         (cx - 9, cy + 4), (cx + 9, cy + 4), 2)
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["armor_light"],
                         (cx - 9, cy + 4), (cx + 9, cy + 4), 1)
        # Belt buckle
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["armor_darkest"],
                         (cx - 2, cy + 3, 4, 3))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                         (cx, cy + 4, 1, 1))
    def _draw_torso_armor(surface, cx, cy, facing, phase):
        """Athletic assassin torso with light armor pieces."""
        # Torso base (chiseled)
        torso_pts = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 11, cy),
            (cx + 10, cy + 8),
            (cx - 10, cy + 8),
            (cx - 11, cy),
        ]
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_pts])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_darkest"], torso_pts)
        # Chest armor
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_dark"], [
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 10, cy),
            (cx + 9, cy + 7),
            (cx - 9, cy + 7),
            (cx - 10, cy),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_mid"], [
            (cx - 7, cy - 4),
            (cx + 7, cy - 4),
            (cx + 8, cy),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
            (cx - 8, cy),
        ])
        # Skin peek (bare chest / muscle definition)
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_shadow"], [
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
            (cx + 4, cy - 1),
            (cx - 4, cy - 1),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_dark"], [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 3, cy - 1),
            (cx - 3, cy - 1),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                         (cx - 2, cy - 3, 4, 1))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["skin_light"],
                         (cx - 1, cy - 3, 2, 1))
        # Center chest crystal (glowing)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_zhyvrek._alpha(130 * (5 - r) / 5 * pulse)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_light"], alpha),
                                  (cx, cy + 2), r)
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_darkest"],
                         (cx - 1, cy + 1, 3, 3))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_dark"],
                         (cx - 1, cy + 1, 2, 2))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                         (cx, cy + 2, 1, 1))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_shine"],
                         (cx, cy + 2, 1, 1))
        # Shoulder pauldron on ONE side (asymmetric - massive spiked shoulder like Kayn)
        # Kayn has one big shoulder pauldron and one bare
        # We'll put it on facing-side (visible)
        pd_side = facing
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"], [
            (cx + pd_side * 8, cy - 7),
            (cx + pd_side * 15, cy - 6),
            (cx + pd_side * 17, cy - 1),
            (cx + pd_side * 13, cy + 2),
            (cx + pd_side * 8, cy),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_darkest"], [
            (cx + pd_side * 8, cy - 8),
            (cx + pd_side * 14, cy - 7),
            (cx + pd_side * 16, cy - 1),
            (cx + pd_side * 12, cy + 1),
            (cx + pd_side * 8, cy - 1),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_dark"], [
            (cx + pd_side * 9, cy - 7),
            (cx + pd_side * 13, cy - 6),
            (cx + pd_side * 15, cy - 1),
            (cx + pd_side * 11, cy),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_mid"], [
            (cx + pd_side * 10, cy - 6),
            (cx + pd_side * 12, cy - 5),
            (cx + pd_side * 14, cy - 2),
            (cx + pd_side * 11, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["armor_light"],
                         (cx + pd_side * 11, cy - 5, 2, 1))
        # Spike on shoulder pauldron
        sp_x = cx + pd_side * 12
        sp_y = cy - 8
        sp_tip_y = sp_y - 5
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"], [
            (sp_x + 1, sp_tip_y + 1),
            (sp_x - 2 + 1, sp_y + 1),
            (sp_x + 2 + 1, sp_y + 1),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_darkest"], [
            (sp_x, sp_tip_y),
            (sp_x - 2, sp_y),
            (sp_x + 2, sp_y),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["armor_dark"], [
            (sp_x, sp_tip_y + 1),
            (sp_x - 1, sp_y),
            (sp_x + 1, sp_y),
        ])
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                         (sp_x, sp_tip_y, 1, 1))
        # Back shoulder (partial, exposed muscle/skin)
        b_side = -facing
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_shadow"], [
            (cx + b_side * 8, cy - 6),
            (cx + b_side * 11, cy - 5),
            (cx + b_side * 12, cy),
            (cx + b_side * 9, cy),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_dark"], [
            (cx + b_side * 9, cy - 5),
            (cx + b_side * 11, cy - 4),
            (cx + b_side * 11, cy),
            (cx + b_side * 9, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                         (cx + b_side * 10, cy - 4, 1, 2))
    def _draw_back_arm_with_scythe(surface, cx, cy, facing, phase, swing, action,
                                    attack_progress):
        """Back arm holds the scythe."""
        wave = math.sin(phase * 0.7) * 1
        # Back-arm (holds scythe shaft)
        # In idle, arm rests down-back; in attack, arm swings forward
        b_side = -facing  # scythe hand is on back side normally
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 2
        # Hand position changes with swing
        if action == "attack":
            # Hand sweeps from back to forward
            hand_x = cx + facing * (12 + swing // 3)
            hand_y = cy + 4 + int(wave)
        else:
            # Idle: hand rests near hip on back side
            hand_x = cx - facing * 4
            hand_y = cy + 8 + int(wave)
        # Elbow
        elbow_x = (shoulder_x + hand_x) // 2
        elbow_y = (shoulder_y + hand_y) // 2 + 2
        # Draw arm
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 5)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_shadow"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 2)
        # Gold bracer
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["armor_darkest"],
                         (elbow_x - 2, elbow_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["armor_mid"],
                         (elbow_x - 2, elbow_y - 1, 4, 2))
        # Forearm
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 5)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_shadow"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        # Hand
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["skin_dark"],
                              (hand_x, hand_y), 3)
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                              (hand_x, hand_y), 2)
        # DRAW SCYTHE from hand
        _NS_zhyvrek._draw_scythe(surface, hand_x, hand_y, facing, phase, swing, action)
    def _draw_scythe(surface, hand_x, hand_y, facing, phase, swing, action):
        """Massive curved scythe with cyan-blue glowing blade tipped with red."""
        # Scythe orientation:
        # - Idle: shaft goes up-back, blade curves forward-up
        # - Attack: swings horizontally forward
        # Shaft angle
        # Idle: shaft goes up-and-back (angle ~120 degrees from horizontal)
        # Attack: shaft rotates to be more horizontal-forward
        base_shaft_angle = math.pi * 0.75  # up-back direction (from hand)
        swing_rot = swing * 0.05  # convert swing to rotation
        # For facing=1, shaft goes back-up-left; for facing=-1, mirrored
        shaft_angle = base_shaft_angle - swing_rot
        if facing == 1:
            shaft_angle_f = math.pi - shaft_angle  # mirror to make back = left
        else:
            shaft_angle_f = shaft_angle
        shaft_len = 50
        # Shaft direction (from hand outward)
        shaft_dx = math.cos(shaft_angle_f)
        shaft_dy = -math.sin(shaft_angle_f)  # negative because y flipped
        shaft_end_x = hand_x + int(shaft_dx * shaft_len)
        shaft_end_y = hand_y + int(shaft_dy * shaft_len)
        # Draw shaft (long staff)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                            (hand_x + 1, hand_y + 1),
                            (shaft_end_x + 1, shaft_end_y + 1), 4)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["armor_darkest"],
                            (hand_x, hand_y), (shaft_end_x, shaft_end_y), 3)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["armor_dark"],
                            (hand_x, hand_y), (shaft_end_x, shaft_end_y), 2)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["armor_light"],
                            (hand_x, hand_y - 1),
                            (shaft_end_x, shaft_end_y - 1), 1)
        # Shaft wrappings (grip)
        for seg_t in (0.15, 0.3, 0.45):
            sxx = int(hand_x + shaft_dx * shaft_len * seg_t)
            syy = int(hand_y + shaft_dy * shaft_len * seg_t)
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_dark"],
                             (sxx - 1, syy - 1, 3, 2))
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                             (sxx, syy, 1, 1))
        # BLADE (curved crescent shape at shaft end)
        # Blade curves perpendicular to shaft, forward direction
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Blade curve: from shaft_end, curves outward like a scythe
        # Perpendicular direction (blade curves toward FRONT of character)
        perp_dx = -shaft_dy  # perpendicular
        perp_dy = shaft_dx
        # Adjust so blade curves toward facing direction
        if perp_dx * facing < 0:
            perp_dx *= -1
            perp_dy *= -1
        # Blade base (attached to shaft)
        blade_base_x = shaft_end_x
        blade_base_y = shaft_end_y
        # Curve the blade with several points forming a crescent
        blade_curve_len = 32
        blade_points_outer = []  # outer edge (sharp)
        blade_points_inner = []  # inner edge (blunt)
        for seg in range(8):
            seg_t = seg / 7
            # Position along curve (parametric)
            # Curve tightens as we go
            curve_angle = seg_t * math.pi * 0.85  # 0 to ~150 degrees
            # Offset along shaft direction (blade sweeps back a bit)
            along_shaft = -math.sin(curve_angle) * blade_curve_len * 0.4
            # Offset perpendicular (blade goes out)
            along_perp = (1 - math.cos(curve_angle)) * blade_curve_len
            bx = blade_base_x + int(shaft_dx * along_shaft + perp_dx * along_perp)
            by = blade_base_y + int(shaft_dy * along_shaft + perp_dy * along_perp)
            blade_points_outer.append((bx, by))
            # Inner edge (offset toward shaft slightly)
            inner_offset = 5 - seg  # thicker at base, thinner at tip
            inner_offset = max(1, inner_offset)
            ibx = bx - int(perp_dx * inner_offset)
            iby = by - int(perp_dy * inner_offset)
            blade_points_inner.append((ibx, iby))
        # Draw blade as filled polygon
        blade_poly = blade_points_outer + list(reversed(blade_points_inner))
        # Shadow
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in blade_poly])
        # Base
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["blade_dark"], blade_poly)
        # Highlight inner strip
        blade_highlight = []
        for i, (op, ip) in enumerate(zip(blade_points_outer, blade_points_inner)):
            mid_x = int((op[0] + ip[0]) / 2)
            mid_y = int((op[1] + ip[1]) / 2)
            blade_highlight.append((mid_x, mid_y))
        # Draw mid strip
        if len(blade_points_outer) >= 2:
            _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["blade_mid"],
                              blade_points_outer[:4] + list(reversed(blade_highlight[:4])))
        # GLOWING CYAN edge along outer edge (sharp side)
        for i in range(len(blade_points_outer) - 1):
            # Layer thickness
            for thick, color, alpha_v in [
                (3, _NS_zhyvrek.PALETTE["shadow_dark"], 180),
                (2, _NS_zhyvrek.PALETTE["shadow_mid"], 220),
                (1, _NS_zhyvrek.PALETTE["shadow_hot"], 255),
            ]:
                pygame.draw.line(surface, (*color, _NS_zhyvrek._alpha(alpha_v * pulse)),
                                 blade_points_outer[i],
                                 blade_points_outer[i + 1], thick)
        # RED accent near tip (Rhaast influence)
        if len(blade_points_outer) >= 3:
            tip_area = blade_points_outer[-3:]
            for i in range(len(tip_area) - 1):
                pygame.draw.line(surface,
                                 (*_NS_zhyvrek.PALETTE["red_mid"],
                                  _NS_zhyvrek._alpha(200 * pulse)),
                                 tip_area[i], tip_area[i + 1], 2)
                pygame.draw.line(surface,
                                 (*_NS_zhyvrek.PALETTE["red_hot"],
                                  _NS_zhyvrek._alpha(240 * pulse)),
                                 tip_area[i], tip_area[i + 1], 1)
        # Sharp tip
        if blade_points_outer:
            tip = blade_points_outer[-1]
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["red_hot"], tip, 2)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["red_shine"], tip, 1)
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["white"], (tip[0], tip[1], 1, 1))
        # Blade base connector (where blade meets shaft) - decorative
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                              (blade_base_x + 1, blade_base_y + 1), 3)
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["armor_darkest"],
                              (blade_base_x, blade_base_y), 3)
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["armor_mid"],
                              (blade_base_x, blade_base_y), 2)
        # Cyan gem at connector
        for r in range(4, 0, -1):
            alpha = _NS_zhyvrek._alpha(150 * (4 - r) / 4 * pulse)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_light"], alpha),
                                  (blade_base_x, blade_base_y), r)
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                         (blade_base_x, blade_base_y, 1, 1))
        # Small energy sparks along blade
        for i in range(3):
            spark_t = (phase + i * 0.4) % 1.0
            idx = int(spark_t * (len(blade_points_outer) - 1))
            if idx < len(blade_points_outer):
                bp = blade_points_outer[idx]
                sx = bp[0] + int(math.sin(phase * 4 + i) * 3)
                sy = bp[1] + int(math.cos(phase * 4 + i) * 3)
                alpha_sp = _NS_zhyvrek._alpha(220 * (1 - spark_t))
                pygame.draw.rect(surface,
                                 (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha_sp),
                                 (sx, sy, 1, 1))
    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm (free hand - clenched fist)."""
        wave = math.sin(phase * 0.7) * 1
        shoulder_x = cx + facing * 8
        shoulder_y = cy - 2
        elbow_x = cx + facing * 12
        elbow_y = cy + 4 + int(wave)
        hand_x = cx + facing * 10
        hand_y = cy + 10 + int(wave)
        # Upper arm (bare skin - assassin's exposed arm)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 4)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_shadow"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)
        # Forearm
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (hand_x + 1, hand_y + 1), 4)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_shadow"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_zhyvrek._aaline(surface, _NS_zhyvrek.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Bracer / bandage on forearm
        mid_x = (elbow_x + hand_x) // 2
        mid_y = (elbow_y + hand_y) // 2
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["armor_darkest"],
                         (mid_x - 2, mid_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["armor_dark"],
                         (mid_x - 2, mid_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                         (mid_x, mid_y, 1, 1))
        # Fist
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["skin_dark"],
                              (hand_x, hand_y), 3)
        _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["skin_mid"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["skin_light"],
                         (hand_x, hand_y - 1, 1, 1))
    def _draw_back_hair(surface, cx, cy, facing, phase):
        """Long flowing back hair."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        hair_pts = [
            (cx - 7, cy + 2),
            (cx + 7, cy + 2),
            (cx + 10, cy + 8),
            (cx + 12 + int(wave1), cy + 18),
            (cx + 10 + int(wave2), cy + 28),
            (cx + 4, cy + 36),
            (cx - 4, cy + 36),
            (cx - 10 + int(wave2), cy + 28),
            (cx - 12 + int(wave1), cy + 18),
            (cx - 10, cy + 8),
        ]
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in hair_pts])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["hair_darkest"], hair_pts)
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["hair_dark"], [
            (cx - 6, cy + 4),
            (cx + 6, cy + 4),
            (cx + 8, cy + 10),
            (cx + 9 + int(wave1 * 0.7), cy + 20),
            (cx + 7, cy + 30),
            (cx - 7, cy + 30),
            (cx - 9 + int(wave1 * 0.7), cy + 20),
            (cx - 8, cy + 10),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["hair_mid"], [
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 6, cy + 14),
            (cx + 4, cy + 24),
            (cx - 4, cy + 24),
            (cx - 6, cy + 14),
        ])
        # Hair strand highlights
        for i, x_off in enumerate((-5, 0, 4)):
            strand_x = cx + x_off + int(math.sin(phase * 0.7 + i) * 2)
            pygame.draw.line(surface, _NS_zhyvrek.PALETTE["hair_light"],
                             (strand_x, cy + 6),
                             (strand_x + int(math.sin(phase + i)), cy + 24), 1)
    def _draw_assassin_head(surface, cx, cy, facing, phase, action):
        """Kayn-inspired assassin head with glowing eye."""
        # Face shape
        face_pts = [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 5, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
            (cx - 5, cy + 4),
            (cx - 6, cy),
        ]
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in face_pts])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_shadow"], face_pts)
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_dark"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 3),
            (cx - 5, cy),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["skin_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
            (cx - 4, cy),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["skin_light"],
                         (cx - 1, cy - 2, 3, 2))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["skin_shine"],
                         (cx, cy - 2, 1, 1))
        # HAIR FRONT (bangs falling over one side of face - Kayn style)
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["hair_darkest"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 5, cy - 2),
            (cx + 2, cy),
            (cx - 5, cy + 1),
            (cx - 6, cy - 2),
        ])
        _NS_zhyvrek._poly(surface, _NS_zhyvrek.PALETTE["hair_dark"], [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 4, cy - 2),
            (cx + 1, cy - 1),
            (cx - 4, cy),
            (cx - 5, cy - 2),
        ])
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["hair_light"],
                         (cx - 3, cy - 3), (cx - 1, cy - 1), 1)
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["hair_light"],
                         (cx + 1, cy - 3), (cx + 3, cy - 1), 1)
        # GLOWING BLUE EYE (assassin's mark - one visible)
        # Show only front-facing eye (dramatic single-eye look)
        eye_x = cx + facing * 2
        eye_y = cy + 1
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Socket
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_deep"],
                         (eye_x - 1, eye_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["eye_socket"],
                         (eye_x - 1, eye_y - 1, 3, 2))
        # Glow halo
        for r in range(5, 0, -1):
            alpha = _NS_zhyvrek._alpha(140 * (5 - r) / 5 * pulse)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["eye_mid"], alpha),
                                  (eye_x, eye_y), r)
        # Core
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["eye_dark"],
                         (eye_x - 1, eye_y, 3, 1))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["eye_mid"],
                         (eye_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["eye_light"],
                         (eye_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["eye_glow"],
                         (eye_x, eye_y, 1, 1))
        # Other eye (covered by hair) - hint of shadow
        eye2_x = cx - facing * 2
        pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["hair_darkest"],
                         (eye2_x - 1, eye_y - 1, 2, 2))
        # Nose (subtle)
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["skin_shadow"],
                         (cx, cy + 2), (cx, cy + 4), 1)
        # Lips (grim)
        pygame.draw.line(surface, _NS_zhyvrek.PALETTE["hair_darkest"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
    # ============================================================
    # MELEE SWING ARC (FIXED - atas ke bawah)
    # ============================================================
    def _draw_scythe_swing_arc(surface, boss, x, y, progress):
        """Cyan crescent arc trail from scythe swing (dari ATAS ke BAWAH)."""
        if progress < 0.35 or progress > 0.72:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.37
        arc_cx = x + facing * 20
        arc_cy = y
        arc_radius = 45
        # Swing dari ATAS ke BAWAH:
        # start_a = -math.pi * 0.6 (atas-depan)
        # end_a   = +math.pi * 0.6 (bawah-depan)
        # Semakin t naik, semakin swing bergerak dari atas ke bawah
        start_a = -math.pi * 0.6   # ATAS-depan (mulai dari sini)
        end_a = math.pi * 0.6      # BAWAH-depan (berakhir di sini)
        # Layered arc untuk glow effect
        for layer_i, (thick, alpha_val, color) in enumerate([
            (6, 90, _NS_zhyvrek.PALETTE["shadow_darkest"]),
            (5, 130, _NS_zhyvrek.PALETTE["shadow_dark"]),
            (4, 180, _NS_zhyvrek.PALETTE["shadow_mid"]),
            (3, 220, _NS_zhyvrek.PALETTE["shadow_light"]),
            (2, 245, _NS_zhyvrek.PALETTE["shadow_hot"]),
            (1, 255, _NS_zhyvrek.PALETTE["shadow_shine"]),
        ]):
            # Draw trail: bagian yang SUDAH dilalui sabit
            # Ujung terbaru (leading edge) = posisi saat ini
            # Ekor trail (tail) = mundur beberapa langkah
            arc_points = []
            trail_length = 0.4  # panjang ekor trail (0.0 - 1.0)
            # Range dari (t - trail_length) sampai t
            start_seg_t = max(0.0, t - trail_length)
            end_seg_t = min(1.0, t)
            num_segments = 22
            for seg in range(num_segments):
                seg_t = start_seg_t + (end_seg_t - start_seg_t) * (seg / (num_segments - 1))
                a = start_a + (end_a - start_a) * seg_t
                ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                ay = arc_cy + int(math.sin(a) * arc_radius)
                arc_points.append((ax, ay))
            if len(arc_points) >= 2:
                for i in range(len(arc_points) - 1):
                    # Fade: yang paling ujung (leading) = full alpha
                    # yang paling belakang (tail) = fade out
                    fade = i / max(1, len(arc_points) - 1)  # 0=tail, 1=leading
                    actual_alpha = _NS_zhyvrek._alpha(alpha_val * fade)
                    pygame.draw.line(surface, (*color, actual_alpha),
                                     arc_points[i], arc_points[i + 1], thick)
        # Bright tip di leading edge (posisi paling depan swing sekarang)
        if 0.05 < t < 0.95:
            tip_a = start_a + (end_a - start_a) * t
            tip_x_arc = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
            tip_y_arc = arc_cy + int(math.sin(tip_a) * arc_radius)
            for r in range(9, 0, -1):
                alpha = _NS_zhyvrek._alpha(220 * (9 - r) / 9)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha),
                                      (tip_x_arc, tip_y_arc), r)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_shine"],
                                  (tip_x_arc, tip_y_arc), 2)
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["white"],
                             (tip_x_arc, tip_y_arc, 1, 1))
            # Sparks di sekitar tip
            for i in range(6):
                sp_a = tip_a + (i - 3) * 0.15
                sp_len = 8 + i
                spx = tip_x_arc + int(math.cos(sp_a) * sp_len * facing)
                spy = tip_y_arc + int(math.sin(sp_a) * sp_len)
                pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_shine"], (spx, spy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = _NS_zhyvrek._alpha((14 - radius) * 15 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius // 2,
                 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (5, 5, 15, 170), (10, 10, 120, 10))
        pygame.draw.ellipse(shadow, (30, 60, 110, 100), (18, 12, 104, 6))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_shadow_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blue shadow wisps floating below."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -3):
            alpha = _NS_zhyvrek._alpha((34 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_zhyvrek._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising shadow particles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_zhyvrek._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                  (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_zhyvrek.PALETTE["shadow_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Red embers (Rhaast side)
        for i in range(4):
            spark_t = (phase * 0.7 + i * 0.25) % 1.0
            ex = cx + 8 + i * 6 + int(math.sin(phase + i) * 3)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_zhyvrek._alpha(200 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_zhyvrek.PALETTE["red_hot"], alpha),
                                 (ex, ey, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_zhyvrek._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                                      (sx, sy), max(2, 7 - i))
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                      (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_shadow_aura(surface, x, y, phase):
        """Massive shadow aura with cyan glow."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_zhyvrek._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zhyvrek._aacircle(aura,
                                      (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                                      (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_zhyvrek._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zhyvrek._aacircle(aura,
                                      (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                      (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_zhyvrek._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zhyvrek._aacircle(aura,
                                      (*_NS_zhyvrek.PALETTE["shadow_mid"], alpha),
                                      (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating cyan + red embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_zhyvrek.PALETTE["shadow_hot"] if i % 3 != 0 \
                else _NS_zhyvrek.PALETTE["red_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_shine"], (sx, sy, 1, 1))
    def _draw_ground_runes(surface, x, y, phase, skill):
        """Ground runic ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_zhyvrek.PALETTE["shadow_mid"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_zhyvrek.PALETTE["shadow_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_zhyvrek.PALETTE["shadow_light"],
                                 _NS_zhyvrek._alpha(180 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - REAPING ARC (FIXED - atas ke bawah)
    # ============================================================
    def _draw_reaping_arc(surface, boss, x, y, timer, phase):
        """Massive extended crescent slash dari ATAS ke BAWAH."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Wind up glow at hand
            t = progress / 0.25
            hand_x = x - facing * 4
            hand_y = y - 4
            cr = int(5 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_zhyvrek._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_light"],
                                  (hand_x, hand_y), cr - 2)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_shine"],
                                  (hand_x, hand_y), max(1, cr - 5))
        else:
            t = (progress - 0.25) / 0.75
            arc_cx = x + facing * 12
            arc_cy = y - 4
            arc_radius = int(55 + t * 45)
            # Swing dari ATAS ke BAWAH
            start_a = -math.pi * 0.7   # atas-depan
            end_a = math.pi * 0.7      # bawah-depan
            # Draw trail: hanya bagian yang sudah dilalui
            trail_length = 0.5
            start_seg_t = max(0.0, t - trail_length)
            end_seg_t = min(1.0, t)
            for layer_i, (thick, alpha_mult, color) in enumerate([
                (7, 0.3, _NS_zhyvrek.PALETTE["shadow_darkest"]),
                (6, 0.5, _NS_zhyvrek.PALETTE["shadow_dark"]),
                (5, 0.7, _NS_zhyvrek.PALETTE["shadow_mid"]),
                (4, 0.9, _NS_zhyvrek.PALETTE["shadow_light"]),
                (3, 1.0, _NS_zhyvrek.PALETTE["shadow_hot"]),
                (2, 1.0, _NS_zhyvrek.PALETTE["shadow_shine"]),
                (1, 1.0, _NS_zhyvrek.PALETTE["white"]),
            ]):
                arc_alpha_base = _NS_zhyvrek._alpha(240 * alpha_mult * (1 - t * 0.4))
                arc_points = []
                num_segments = 26
                for seg in range(num_segments):
                    seg_t = start_seg_t + (end_seg_t - start_seg_t) * (seg / (num_segments - 1))
                    a = start_a + (end_a - start_a) * seg_t
                    ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                    ay = arc_cy + int(math.sin(a) * arc_radius)
                    arc_points.append((ax, ay))
                if len(arc_points) >= 2:
                    for i in range(len(arc_points) - 1):
                        fade = i / max(1, len(arc_points) - 1)  # 0=tail, 1=leading
                        actual_alpha = _NS_zhyvrek._alpha(arc_alpha_base * fade)
                        pygame.draw.line(surface, (*color, actual_alpha),
                                         arc_points[i], arc_points[i + 1], thick)
            # Sparks di leading edge
            if 0.05 < t < 0.95:
                tip_a = start_a + (end_a - start_a) * t
                tip_x = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
                tip_y = arc_cy + int(math.sin(tip_a) * arc_radius)
                # Random sparks
                for i in range(8):
                    spark_a = tip_a + (i - 4) * 0.1
                    spark_r = arc_radius + int(math.sin(phase * 3 + i) * 6)
                    sx = arc_cx + int(math.cos(spark_a) * spark_r * facing)
                    sy = arc_cy + int(math.sin(spark_a) * spark_r)
                    alpha = _NS_zhyvrek._alpha(240)
                    pygame.draw.rect(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_shine"], alpha),
                                     (sx, sy, 2, 2))
            # Impact burst di posisi tengah arc (front-center) SETELAH swing melewati tengah
            if t > 0.55:
                sweet_a = 0  # tengah = tepat di depan
                sweet_x = arc_cx + int(math.cos(sweet_a) * arc_radius * facing)
                sweet_y = arc_cy + int(math.sin(sweet_a) * arc_radius)
                st = (t - 0.55) / 0.45
                burst_r = int(10 + st * 22)
                burst_alpha = _NS_zhyvrek._alpha(240 * (1 - st))
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_darkest"], burst_alpha),
                                      (sweet_x, sweet_y), burst_r + 3, 3)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_dark"], burst_alpha),
                                      (sweet_x, sweet_y), burst_r, 2)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_light"], burst_alpha),
                                      (sweet_x, sweet_y), max(1, burst_r - 6), 1)
                # Radial sparks
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = sweet_x + int(math.cos(angle_s) * burst_r)
                    ey = sweet_y + int(math.sin(angle_s) * burst_r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_hot"], burst_alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_shine"], burst_alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - PHANTOM PIERCE (dash-thrust piercing line)
    # ============================================================
    def _draw_phantom_pierce_ground(surface, boss, x, y, timer, phase):
        """Ground marks along dash path."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhyvrek._target_position(boss, x, y)
        if progress > 0.3:
            t = min(1.0, (progress - 0.3) / 0.5)
            # Line from boss to target
            start_x = x + facing * 20
            start_y = y + 40
            end_x = start_x + int((tx - start_x) * t)
            end_y = ty + 5
            # Ground streak
            pygame.draw.line(surface, (*_NS_zhyvrek.PALETTE["shadow_dark"], 180),
                             (start_x, start_y), (end_x, end_y), 4)
            pygame.draw.line(surface, (*_NS_zhyvrek.PALETTE["shadow_hot"], 220),
                             (start_x, start_y), (end_x, end_y), 2)
    def _draw_phantom_pierce_foreground(surface, boss, x, y, timer, phase):
        """Elongated piercing shadow spear projectile."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhyvrek._target_position(boss, x, y)
        if progress < 0.3:
            # Charge
            t = progress / 0.3
            hand_x = x + facing * 20
            hand_y = y - 6
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_zhyvrek._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_light"],
                                  (hand_x, hand_y), cr - 2)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_shine"],
                                  (hand_x, hand_y), max(1, cr - 4))
        else:
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 22
            start_y = y - 4
            # Elongated spear from start to current progress
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
            # Draw thick beam (spear-like)
            angle_to = math.atan2(ty - start_y, tx - start_x)
            perp = angle_to + math.pi / 2
            # Layered beam
            for layer_i, (thick, alpha_val, color) in enumerate([
                (7, 100, _NS_zhyvrek.PALETTE["shadow_darkest"]),
                (5, 150, _NS_zhyvrek.PALETTE["shadow_dark"]),
                (3, 200, _NS_zhyvrek.PALETTE["shadow_mid"]),
                (2, 240, _NS_zhyvrek.PALETTE["shadow_hot"]),
                (1, 255, _NS_zhyvrek.PALETTE["shadow_shine"]),
            ]):
                pygame.draw.line(surface, (*color, alpha_val),
                                 (start_x, start_y), (end_x, end_y), thick)
            # Sharp spear tip
            for r in range(10, 0, -1):
                alpha = _NS_zhyvrek._alpha(200 * (10 - r) / 10)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_light"], alpha),
                                      (end_x, end_y), r)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_darkest"],
                                  (end_x, end_y), 5)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_hot"],
                                  (end_x, end_y), 3)
            _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["shadow_shine"],
                                  (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["white"], (end_x, end_y, 1, 1))
            # Sparks along beam
            for i in range(8):
                sp_t = (phase * 2 + i * 0.13) % 1.0
                spx = int(start_x + (end_x - start_x) * sp_t)
                spy = int(start_y + (end_y - start_y) * sp_t)
                spx += int(math.cos(perp) * math.sin(phase * 4 + i) * 4)
                spy += int(math.sin(perp) * math.sin(phase * 4 + i) * 4)
                pygame.draw.rect(surface, _NS_zhyvrek.PALETTE["shadow_shine"], (spx, spy, 1, 1))
            # Impact at target
            if t > 0.85:
                st = (t - 0.85) / 0.15
                impact_r = int(10 + st * 22)
                alpha = _NS_zhyvrek._alpha(230 * (1 - st))
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["red_dark"], alpha),
                                      (tx, ty), impact_r + 3, 3)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["red_mid"], alpha),
                                      (tx, ty), impact_r, 2)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["red_hot"], alpha),
                                      (tx, ty), max(1, impact_r - 6), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * impact_r)
                    ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                    pygame.draw.rect(surface, (*_NS_zhyvrek.PALETTE["red_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL E - SHADOW VEIL (teleport w/ vortex)
    # ============================================================
    def _draw_shadow_veil_ground(surface, boss, x, y, timer, phase):
        """Ground portal marks."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(40 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_zhyvrek.PALETTE["shadow_darkest"], 200),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_zhyvrek.PALETTE["shadow_dark"], 180),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_shadow_veil_foreground(surface, boss, x, y, timer, phase):
        """Vortex portal effect around boss (translucent/veiled)."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Swirling vortex around body
        vortex_r = 40
        for i in range(20):
            spiral_t = (phase * 2 + i * 0.1) % 1.0
            angle = phase * 4 + i * math.pi / 10 + spiral_t * math.pi * 2
            dist = vortex_r * spiral_t
            sx = x + int(math.cos(angle) * dist)
            sy = y + int(math.sin(angle) * dist * 0.7)
            alpha = _NS_zhyvrek._alpha(220 * spiral_t)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                  (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_zhyvrek.PALETTE["shadow_shine"], alpha),
                             (sx, sy, 1, 1))
        # Central portal ring
        for r_o in range(vortex_r, vortex_r - 10, -1):
            alpha = _NS_zhyvrek._alpha(180)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                                  (x, y), r_o, 1)
        for r_o in range(vortex_r - 3, vortex_r - 15, -2):
            alpha = _NS_zhyvrek._alpha(220)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_mid"], alpha),
                                  (x, y), r_o, 1)
    # ============================================================
    # SKILL R - VOID REAP (dive & burst)
    # ============================================================
    def _draw_void_reap_ground(surface, boss, x, y, timer, phase):
        """Massive marks at boss AND target."""
        tx, ty = _NS_zhyvrek._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Circle at boss origin (dive point)
        if progress < 0.3:
            t = progress / 0.3
            r = int(45 * t)
            alpha = _NS_zhyvrek._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        # Circle at target (emerge point)
        if progress > 0.4:
            t = min(1.0, (progress - 0.4) / 0.5)
            r = int(50 * t)
            alpha = _NS_zhyvrek._alpha(220 * (1 - t * 0.3))
            pygame.draw.ellipse(surface,
                                (*_NS_zhyvrek.PALETTE["red_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_void_reap_foreground(surface, boss, x, y, timer, phase):
        """Dive into shadow → burst out at target with damage explosion."""
        tx, ty = _NS_zhyvrek._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Dive phase - shadow tendrils envelop boss
            t = progress / 0.3
            # Tendrils spiral around boss and pull down
            for i in range(12):
                spiral_t = (phase * 2 + i * 0.1) % 1.0
                angle = phase * 4 + i * math.pi / 6
                dist = 30 * (1 - t)
                sx = x + int(math.cos(angle) * dist)
                sy = y + int(math.sin(angle) * dist * 0.7)
                alpha = _NS_zhyvrek._alpha(230 * t)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                                      (sx, sy), 3)
                _NS_zhyvrek._aacircle(surface,
                                      (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                      (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha),
                                 (sx, sy, 1, 1))
        elif progress < 0.8:
            # Untargetable phase - shadow trail from boss to target
            t = (progress - 0.3) / 0.5
            # Trail of shadow between origin and target
            for i in range(15):
                trail_t = i / 14
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t)
                # Wavy path
                px += int(math.sin(phase * 3 + trail_t * math.pi * 2) * 8)
                py += int(math.cos(phase * 3 + trail_t * math.pi * 2) * 5)
                alpha = _NS_zhyvrek._alpha(200 * (1 - abs(trail_t - t) * 3))
                if alpha > 0:
                    _NS_zhyvrek._aacircle(surface,
                                          (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha),
                                          (px, py), 5)
                    _NS_zhyvrek._aacircle(surface,
                                          (*_NS_zhyvrek.PALETTE["shadow_dark"], alpha),
                                          (px, py), 3)
                    pygame.draw.rect(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha),
                                     (px, py, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_shine"], alpha),
                                     (px, py, 1, 1))
            # Gathering energy at target (charging)
            if t > 0.4:
                gather_t = (t - 0.4) / 0.6
                for r in range(int(15 * gather_t), 0, -1):
                    alpha = _NS_zhyvrek._alpha(180 * gather_t * (15 - r) / 15)
                    _NS_zhyvrek._aacircle(surface,
                                          (*_NS_zhyvrek.PALETTE["red_dark"], alpha),
                                          (tx, ty), r)
                _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["red_mid"],
                                      (tx, ty), max(1, int(8 * gather_t)))
                _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["red_hot"],
                                      (tx, ty), max(1, int(5 * gather_t)))
                _NS_zhyvrek._aacircle(surface, _NS_zhyvrek.PALETTE["red_shine"],
                                      (tx, ty), max(1, int(3 * gather_t)))
        else:
            # BURST OUT - massive explosion at target
            t = (progress - 0.8) / 0.2
            intensity = math.sin(t * math.pi)
            burst_r = int(20 + t * 45)
            burst_alpha = _NS_zhyvrek._alpha(240 * intensity)
            # Layered explosion
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["red_dark"], burst_alpha),
                                  (tx, ty), burst_r + 4, 3)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["red_mid"], burst_alpha),
                                  (tx, ty), burst_r, 3)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["red_hot"], burst_alpha),
                                  (tx, ty), max(1, burst_r - 6), 2)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_light"], burst_alpha),
                                  (tx, ty), max(1, burst_r - 14), 2)
            _NS_zhyvrek._aacircle(surface,
                                  (*_NS_zhyvrek.PALETTE["shadow_shine"], burst_alpha),
                                  (tx, ty), max(1, burst_r // 4))
            # Radial shockwave
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * burst_r)
                ey = ty + int(math.sin(angle_s) * burst_r * 0.7)
                pygame.draw.line(surface, (*_NS_zhyvrek.PALETTE["red_hot"], burst_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_zhyvrek.PALETTE["shadow_shine"], burst_alpha),
                                 (ex, ey, 2, 2))
            # Shadow tendrils shooting outward
            for i in range(8):
                tendril_angle = i * math.pi / 4 + phase * 0.5
                tendril_len = int(burst_r * 1.3)
                prev_x = tx
                prev_y = ty
                for seg in range(1, 6):
                    seg_t = seg / 5
                    wx = tx + int(math.cos(tendril_angle) * tendril_len * seg_t)
                    wy = ty + int(math.sin(tendril_angle) * tendril_len * seg_t * 0.7)
                    wx += int(math.sin(phase * 3 + seg + i) * 5)
                    alpha_t = _NS_zhyvrek._alpha(220 * intensity * (1 - seg_t * 0.5))
                    pygame.draw.line(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_darkest"], alpha_t),
                                     (prev_x, prev_y), (wx, wy), 3)
                    pygame.draw.line(surface,
                                     (*_NS_zhyvrek.PALETTE["shadow_hot"], alpha_t),
                                     (prev_x, prev_y), (wx, wy), 1)
                    prev_x = wx
                    prev_y = wy



# ====================================================================
# XELNARATH (VOID SOVEREIGN) - TRUE BOSS
# ====================================================================

class _NS_xelnarath:
    """Namespace xelnarath - Void Empress boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Deep void purple (main body, wings)
        "void_darkest": (8, 3, 15),
        "void_dark": (25, 10, 45),
        "void_mid": (55, 25, 90),
        "void_light": (100, 55, 155),
        "void_bright": (155, 95, 210),
        "void_shine": (210, 165, 245),
        # Hot magenta (magic, glow, cracks)
        "magenta_darkest": (35, 5, 40),
        "magenta_dark": (90, 20, 110),
        "magenta_mid": (170, 45, 190),
        "magenta_light": (230, 100, 240),
        "magenta_hot": (255, 160, 255),
        "magenta_shine": (255, 220, 255),
        # Wing membrane (translucent purple)
        "membrane_dark": (30, 15, 55),
        "membrane_mid": (75, 40, 120),
        "membrane_light": (145, 90, 195),
        "membrane_glow": (200, 140, 240),
        # Chitin/carapace (dark blue-purple)
        "chitin_darkest": (5, 5, 20),
        "chitin_dark": (20, 20, 45),
        "chitin_mid": (55, 50, 95),
        "chitin_light": (110, 105, 165),
        "chitin_shine": (180, 175, 220),
        # Gold accents (armor trim, ornaments)
        "gold_dark": (85, 60, 15),
        "gold_mid": (180, 140, 45),
        "gold_light": (240, 205, 100),
        "gold_shine": (255, 240, 180),
        # Eye (glowing pink/magenta)
        "eye_socket": (10, 5, 15),
        "eye_dark": (60, 15, 80),
        "eye_mid": (180, 50, 200),
        "eye_light": (240, 130, 250),
        "eye_glow": (255, 210, 255),
        # Void portal/darkness
        "abyss_dark": (2, 0, 8),
        "abyss_mid": (15, 5, 30),
        # Star sparkles
        "star_dim": (140, 100, 180),
        "star_mid": (200, 170, 240),
        "star_bright": (255, 240, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 0, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xelnarath._clamp(color)
        if _NS_xelnarath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xelnarath._clamp(color)
        if _NS_xelnarath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_xelnarath._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xelnarath(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xelnarath._detect_moving(boss)
        _NS_xelnarath._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xn_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_xelnarath._draw_void_aura(surface, x, y, pulse)
        _NS_xelnarath._draw_ground_portal(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX (behind body)
        if active_skill == "w":
            _NS_xelnarath._draw_abyssal_vortex_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xelnarath._draw_void_spikes_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xelnarath._draw_endless_devour_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_xelnarath._draw_xn_attack(surface, boss, x, y)
        elif moving:
            _NS_xelnarath._draw_xn_float_move(surface, boss, x, y)
        else:
            _NS_xelnarath._draw_xn_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_xelnarath._draw_void_lance(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xelnarath._draw_abyssal_vortex_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xelnarath._draw_void_spikes_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xelnarath._draw_endless_devour_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xn_previous_timer", 0))
        active = bool(getattr(boss, "_xn_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._xn_attack_active = True
            boss._xn_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xn_attack_frame = int(getattr(boss, "_xn_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._xn_attack_active = False
            boss._xn_attack_frame = 0
            active = False
        boss._xn_previous_timer = timer
        boss._xn_attack_progress = (
            min(1.0, getattr(boss, "_xn_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_xn_last_x"):
            boss._xn_last_x = boss.x
            boss._xn_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xn_last_x)
        dy = abs(boss.y - boss._xn_last_y)
        boss._xn_last_x = boss.x
        boss._xn_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_xn_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_xelnarath._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_xelnarath._draw_void_wisps(surface, x, y + 42, boss.pulse)
        _NS_xelnarath._draw_xn_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle")
    def _draw_xn_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_xelnarath._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_xelnarath._draw_void_wisps(surface, x + sway, y + 42, phase,
                                        trail=True, facing=boss.direction)
        _NS_xelnarath._draw_xn_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")
    def _draw_xn_attack(surface, boss, x, y):
        """Melee: sweeping wing/claw swing animation."""
        progress = getattr(boss, "_xn_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wing sweep attack
        if progress < 0.3:
            # Wind up (pull wings back)
            t = progress / 0.3
            thrust = -int(t * 6) * boss.direction
            lift = int(t * 5)
        elif progress < 0.6:
            # Forward sweep
            t = (progress - 0.3) / 0.3
            thrust = int((-6 + t * 18)) * boss.direction
            lift = int(5 - t * 8)
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            thrust = int(12 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_xelnarath._draw_float_shadow(surface, x + thrust, y + 52, boss.pulse)
        _NS_xelnarath._draw_void_wisps(surface, x + thrust, y + 42, boss.pulse,
                                        intense=True)
        _NS_xelnarath._draw_xn_body(surface, x + thrust, y - lift + bob,
                                     boss.direction, boss.pulse, "attack", progress)
        # Slash trail effect
        _NS_xelnarath._draw_swing_slash(surface, boss, x + thrust, y - lift + bob,
                                         progress)
    # ============================================================
    # BODY - Void Empress (wings, robed body, head, crown-horns)
    # ============================================================
    def _draw_xn_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Empress: wings (huge), robed body, arms, head, void aura."""
        # Wings first (behind body)
        _NS_xelnarath._draw_void_wings(surface, cx, cy - 4, facing, phase, action,
                                        attack_progress)
        # Long trailing robe/tail bottom
        _NS_xelnarath._draw_robe_bottom(surface, cx, cy + 6, facing, phase)
        # Main torso/body
        _NS_xelnarath._draw_void_torso(surface, cx, cy, facing, phase)
        # Arms (claws)
        arm_sweep = 0
        if action == "attack":
            if attack_progress < 0.3:
                arm_sweep = -int(attack_progress / 0.3 * 8) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.3) / 0.3
                arm_sweep = int((-8 + t * 20)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_sweep = int(12 * (1 - t)) * facing
        _NS_xelnarath._draw_claw_arms(surface, cx, cy - 2, facing, phase, arm_sweep,
                                       action)
        # Head + horned crown
        _NS_xelnarath._draw_void_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_void_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Massive void wings behind body (like Bel'Veth spread wings)."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 0.8) * 4
        # Draw both wings (far bigger visible, near smaller)
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing
            (1, 0.72, 0.75),   # near wing
        ]):
            base_x = cx - facing * 5
            base_y = cy - 4
            # Wing structure: 4 spars fanning out
            # Top spar (goes up-back, tallest)
            spar1_len = int(38 * size_mult)
            spar1_angle = math.pi * 0.75 * side_mult - math.radians(beat)
            # Second spar
            spar2_len = int(42 * size_mult)
            spar2_angle = math.pi * 0.95 * side_mult - math.radians(beat * 0.85)
            # Third spar (wider)
            spar3_len = int(38 * size_mult)
            spar3_angle = math.pi * 1.15 * side_mult - math.radians(beat * 0.65)
            # Fourth spar (bottom, curves down)
            spar4_len = int(28 * size_mult)
            spar4_angle = math.pi * 1.35 * side_mult - math.radians(beat * 0.4)
            # Calculate tips
            def tip(a, l):
                return (base_x + int(math.cos(a) * l) * (-facing),
                        base_y - int(math.sin(a) * l))
            tip1 = tip(spar1_angle, spar1_len)
            tip2 = tip(spar2_angle, spar2_len)
            tip3 = tip(spar3_angle, spar3_len)
            tip4 = tip(spar4_angle, spar4_len)
            # Membrane shape (jagged with dips)
            def midpoint_dip(a, b, dip=4):
                return (int((a[0] + b[0]) / 2),
                        int((a[1] + b[1]) / 2) + int(dip * size_mult))
            membrane_points = [
                (base_x, base_y),
                tip1,
                midpoint_dip(tip1, tip2, 4),
                tip2,
                midpoint_dip(tip2, tip3, 5),
                tip3,
                midpoint_dip(tip3, tip4, 4),
                tip4,
                (base_x - facing * 4, base_y + int(6 * size_mult)),
            ]
            # Draw to alpha surface for translucency
            wing_surf = pygame.Surface((200, 130), pygame.SRCALPHA)
            offset_x = base_x - 100
            offset_y = base_y - 60
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]
            # Base dark membrane
            _NS_xelnarath._poly(wing_surf,
                                (*_NS_xelnarath.PALETTE["shadow_deep"],
                                 int(220 * alpha_mult)),
                                [(p[0] + 2, p[1] + 2) for p in local_points])
            _NS_xelnarath._poly(wing_surf,
                                (*_NS_xelnarath.PALETTE["void_darkest"],
                                 int(240 * alpha_mult)),
                                local_points)
            # Inner darker (concave fill)
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            inner_pts = []
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_local * 0.18),
                     int(p[1] * 0.82 + cy_local * 0.18))
                )
            _NS_xelnarath._poly(wing_surf,
                                (*_NS_xelnarath.PALETTE["void_dark"],
                                 int(220 * alpha_mult)),
                                inner_pts)
            # Membrane color (mid purple)
            inner_pts2 = []
            for p in local_points:
                inner_pts2.append(
                    (int(p[0] * 0.65 + cx_local * 0.35),
                     int(p[1] * 0.65 + cy_local * 0.35))
                )
            _NS_xelnarath._poly(wing_surf,
                                (*_NS_xelnarath.PALETTE["membrane_mid"],
                                 int(160 * alpha_mult)),
                                inner_pts2)
            # Wing bones (spars) - detailed with gold tint
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip_p in [tip1, tip2, tip3, tip4]:
                tp = (tip_p[0] - offset_x, tip_p[1] - offset_y)
                # Shadow
                pygame.draw.line(wing_surf,
                                 (*_NS_xelnarath.PALETTE["shadow_deep"],
                                  int(240 * alpha_mult)),
                                 (bone_base[0] + 1, bone_base[1] + 1),
                                 (tp[0] + 1, tp[1] + 1), 4)
                # Bone dark
                pygame.draw.line(wing_surf,
                                 (*_NS_xelnarath.PALETTE["chitin_darkest"],
                                  int(255 * alpha_mult)),
                                 bone_base, tp, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_xelnarath.PALETTE["chitin_dark"],
                                  int(255 * alpha_mult)),
                                 bone_base, tp, 2)
                # Gold accent along bone
                pygame.draw.line(wing_surf,
                                 (*_NS_xelnarath.PALETTE["gold_dark"],
                                  int(220 * alpha_mult)),
                                 bone_base, tp, 1)
                # Curved tip (claw-like hook)
                perp_a = math.atan2(tp[1] - bone_base[1], tp[0] - bone_base[0])
                hook_len = 4
                hook_x = tp[0] + int(math.cos(perp_a + math.pi * 0.3) * hook_len)
                hook_y = tp[1] + int(math.sin(perp_a + math.pi * 0.3) * hook_len)
                pygame.draw.line(wing_surf,
                                 (*_NS_xelnarath.PALETTE["chitin_darkest"],
                                  int(240 * alpha_mult)),
                                 tp, (hook_x, hook_y), 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_xelnarath.PALETTE["gold_mid"],
                                  int(220 * alpha_mult)),
                                 tp, (hook_x, hook_y), 1)
                # Sharp tip claw
                _NS_xelnarath._aacircle(wing_surf,
                                        (*_NS_xelnarath.PALETTE["gold_light"],
                                         int(240 * alpha_mult)),
                                        (hook_x, hook_y), 2)
                pygame.draw.rect(wing_surf,
                                 (*_NS_xelnarath.PALETTE["gold_shine"],
                                  int(255 * alpha_mult)),
                                 (hook_x, hook_y, 1, 1))
            # Magenta glow along top edge
            pygame.draw.line(wing_surf,
                             (*_NS_xelnarath.PALETTE["magenta_light"],
                              int(180 * alpha_mult)),
                             bone_base,
                             (tip1[0] - offset_x, tip1[1] - offset_y), 1)
            # Scattered star sparkles on membrane
            for i in range(5):
                sp_x = int(cx_local + math.cos(phase + i * 1.3) * 30)
                sp_y = int(cy_local + math.sin(phase + i * 1.3) * 20)
                pygame.draw.rect(wing_surf,
                                 (*_NS_xelnarath.PALETTE["magenta_hot"],
                                  int(220 * alpha_mult)),
                                 (sp_x, sp_y, 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_robe_bottom(surface, cx, cy, facing, phase):
        """Long trailing void robe (like Bel'Veth's body)."""
        wave1 = math.sin(phase * 0.7) * 3
        wave2 = math.sin(phase * 0.7 + 1.5) * 3
        # Robe silhouette (narrows then widens like a dress)
        robe_pts = [
            (cx - 10, cy),
            (cx + 10, cy),
            (cx + 14, cy + 10),
            (cx + 18 + int(wave1), cy + 22),
            (cx + 22 + int(wave2), cy + 34),
            (cx + 18, cy + 44),
            (cx + 8, cy + 48),
            (cx - 8, cy + 48),
            (cx - 18, cy + 44),
            (cx - 22 + int(wave1), cy + 34),
            (cx - 18 + int(wave2), cy + 22),
            (cx - 14, cy + 10),
        ]
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in robe_pts])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_darkest"], robe_pts)
        # Second robe layer
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_dark"], [
            (cx - 9, cy + 2),
            (cx + 9, cy + 2),
            (cx + 12, cy + 12),
            (cx + 16 + int(wave1 * 0.7), cy + 24),
            (cx + 18 + int(wave2 * 0.7), cy + 34),
            (cx + 14, cy + 42),
            (cx - 14, cy + 42),
            (cx - 18 + int(wave1 * 0.7), cy + 34),
            (cx - 16 + int(wave2 * 0.7), cy + 24),
            (cx - 12, cy + 12),
        ])
        # Mid layer
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_mid"], [
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 10, cy + 16),
            (cx + 12, cy + 30),
            (cx + 6, cy + 40),
            (cx - 6, cy + 40),
            (cx - 12, cy + 30),
            (cx - 10, cy + 16),
        ])
        # Central highlight
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_light"], [
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 4, cy + 22),
            (cx + 2, cy + 34),
            (cx - 2, cy + 34),
            (cx - 4, cy + 22),
        ])
        # Central magenta glow strip (like the character has a glowing core)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, y_off in enumerate((8, 14, 20, 26)):
            alpha = _NS_xelnarath._alpha(180 * pulse)
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_dark"],
                             (cx - 1, cy + y_off, 2, 3))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_light"],
                             (cx, cy + y_off, 1, 2))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                             (cx, cy + y_off, 1, 1))
        # Gold trim at bottom edges
        for i, (rx, ry) in enumerate([(-16, 42), (16, 42), (-8, 46), (8, 46)]):
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_dark"],
                             (cx + rx, cy + ry, 3, 2))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_light"],
                             (cx + rx + 1, cy + ry, 1, 1))
        # Void particles rising from robe
        for i in range(6):
            spark_t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 12 + int((i % 3) * 10) + int(math.sin(phase + i) * 2)
            sy = cy + 12 + int(spark_t * 32)
            alpha = _NS_xelnarath._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_shine"], (sx, sy, 1, 1))
    def _draw_void_torso(surface, cx, cy, facing, phase):
        """Chitinous armored torso."""
        # Torso plate
        torso_pts = [
            (cx - 10, cy - 10),
            (cx + 10, cy - 10),
            (cx + 12, cy - 4),
            (cx + 11, cy + 4),
            (cx - 11, cy + 4),
            (cx - 12, cy - 4),
        ]
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_darkest"], torso_pts)
        # Chitin plates
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_dark"], [
            (cx - 9, cy - 9),
            (cx + 9, cy - 9),
            (cx + 11, cy - 4),
            (cx + 10, cy + 3),
            (cx - 10, cy + 3),
            (cx - 11, cy - 4),
        ])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_mid"], [
            (cx - 8, cy - 7),
            (cx + 8, cy - 7),
            (cx + 9, cy - 3),
            (cx + 7, cy + 2),
            (cx - 7, cy + 2),
            (cx - 9, cy - 3),
        ])
        # Central chest crystal (like glowing V-shape)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # V-crystal shape
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"], [
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 3, cy - 2),
            (cx, cy + 2),
            (cx - 3, cy - 2),
        ])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["magenta_darkest"], [
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 2, cy - 2),
            (cx, cy + 1),
            (cx - 2, cy - 2),
        ])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["magenta_dark"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 1, cy - 2),
            (cx, cy),
            (cx - 1, cy - 2),
        ])
        # Glow
        for r in range(6, 0, -1):
            alpha = _NS_xelnarath._alpha(120 * (6 - r) / 6 * pulse)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                    (cx, cy - 3), r)
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"], (cx, cy - 4, 1, 2))
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_shine"], (cx, cy - 4, 1, 1))
        # Shoulder pauldrons (chitin)
        for side in (-1, 1):
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"], [
                (cx + side * 8, cy - 11),
                (cx + side * 14, cy - 10),
                (cx + side * 15, cy - 5),
                (cx + side * 11, cy - 3),
                (cx + side * 8, cy - 5),
            ])
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_darkest"], [
                (cx + side * 8, cy - 11),
                (cx + side * 13, cy - 10),
                (cx + side * 14, cy - 5),
                (cx + side * 10, cy - 3),
                (cx + side * 8, cy - 5),
            ])
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_dark"], [
                (cx + side * 9, cy - 10),
                (cx + side * 12, cy - 9),
                (cx + side * 13, cy - 5),
                (cx + side * 10, cy - 4),
            ])
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_mid"], [
                (cx + side * 10, cy - 9),
                (cx + side * 12, cy - 8),
                (cx + side * 12, cy - 6),
                (cx + side * 10, cy - 6),
            ])
            # Gold trim
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["gold_dark"],
                             (cx + side * 9, cy - 10),
                             (cx + side * 13, cy - 10), 1)
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["gold_light"],
                             (cx + side * 10, cy - 10),
                             (cx + side * 12, cy - 10), 1)
            # Spike on shoulder
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_darkest"], [
                (cx + side * 11, cy - 14),
                (cx + side * 10, cy - 10),
                (cx + side * 13, cy - 10),
            ])
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_light"], [
                (cx + side * 11, cy - 13),
                (cx + side * 11, cy - 10),
                (cx + side * 12, cy - 10),
            ])
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                             (cx + side * 11, cy - 13, 1, 1))
    def _draw_claw_arms(surface, cx, cy, facing, phase, sweep, action):
        """Two clawed arms extending outward."""
        # Front arm (extends forward, sweeps)
        wave = math.sin(phase * 0.7) * 1
        # Front arm
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 2
        elbow_x = cx + facing * 16 + sweep // 2
        elbow_y = cy + 2 + int(wave)
        claw_x = cx + facing * 24 + sweep
        claw_y = cy - 3 + int(wave)
        # Upper arm (chitinous)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1),
                               (elbow_x + 1, elbow_y + 1), 5)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_dark"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_mid"],
                               (shoulder_x, shoulder_y - 1),
                               (elbow_x, elbow_y - 1), 2)
        # Gold band on upper arm
        mid_up_x = (shoulder_x + elbow_x) // 2
        mid_up_y = (shoulder_y + elbow_y) // 2
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_dark"],
                         (mid_up_x - 2, mid_up_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_light"],
                         (mid_up_x - 1, mid_up_y - 1, 2, 1))
        # Forearm
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                               (elbow_x + 1, elbow_y + 1),
                               (claw_x + 1, claw_y + 1), 4)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                               (elbow_x, elbow_y), (claw_x, claw_y), 3)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_dark"],
                               (elbow_x, elbow_y), (claw_x, claw_y), 2)
        # CLAW (3 sharp talons)
        for i, spread in enumerate((-3, 0, 3)):
            claw_tip_x = claw_x + facing * 5
            claw_tip_y = claw_y + spread
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                             (claw_x + 1, claw_y + 1),
                             (claw_tip_x + 1, claw_tip_y + 1), 2)
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                             (claw_x, claw_y), (claw_tip_x, claw_tip_y), 2)
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["chitin_mid"],
                             (claw_x, claw_y), (claw_tip_x, claw_tip_y), 1)
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_light"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                             (claw_tip_x, claw_tip_y, 1, 1))
        # Back arm (smaller, partial)
        back_shoulder_x = cx - facing * 8
        back_shoulder_y = cy - 1
        back_elbow_x = cx - facing * 14
        back_elbow_y = cy + 4 - int(wave)
        back_claw_x = cx - facing * 18
        back_claw_y = cy + 1 - int(wave)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                               (back_shoulder_x + 1, back_shoulder_y + 1),
                               (back_elbow_x + 1, back_elbow_y + 1), 4)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                               (back_shoulder_x, back_shoulder_y),
                               (back_elbow_x, back_elbow_y), 3)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_dark"],
                               (back_shoulder_x, back_shoulder_y),
                               (back_elbow_x, back_elbow_y), 2)
        _NS_xelnarath._aaline(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                               (back_elbow_x, back_elbow_y),
                               (back_claw_x, back_claw_y), 2)
        # Small back claws
        for i, spread in enumerate((-2, 2)):
            ct_x = back_claw_x - facing * 3
            ct_y = back_claw_y + spread
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                             (back_claw_x, back_claw_y), (ct_x, ct_y), 1)
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_mid"], (ct_x, ct_y, 1, 1))
    def _draw_void_head(surface, cx, cy, facing, phase, action):
        """Elongated void head with horns/crown and glowing eyes."""
        # Head shape (helmet-like, elongated top)
        head_pts = [
            (cx - 6, cy + 6),   # bottom back
            (cx - 7, cy),        # side back
            (cx - 5, cy - 6),    # upper back
            (cx - 2, cy - 10),   # crown back
            (cx + 2, cy - 10),   # crown front
            (cx + 5, cy - 6),    # upper front
            (cx + 7, cy - 1),    # face front
            (cx + 6, cy + 4),    # chin front
            (cx + 3, cy + 8),    # chin bottom
            (cx - 3, cy + 8),    # chin back
        ]
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_pts])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_darkest"], head_pts)
        # Head plate mid
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_dark"], [
            (cx - 5, cy + 5),
            (cx - 6, cy),
            (cx - 4, cy - 5),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
            (cx + 4, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
        ])
        _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy),
            (cx - 3, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 3, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 1, cy + 6),
            (cx - 1, cy + 6),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_xelnarath.PALETTE["chitin_light"],
                         (cx - 2, cy - 6), (cx + 2, cy - 6), 1)
        pygame.draw.line(surface, _NS_xelnarath.PALETTE["chitin_light"],
                         (cx - 3, cy - 3), (cx + 3, cy - 3), 1)
        # HORNS (2 pairs, curving back like Bel'Veth)
        _NS_xelnarath._draw_head_horns(surface, cx, cy, facing, phase)
        # GLOWING EYES (magenta, sinister)
        _NS_xelnarath._draw_void_eyes(surface, cx, cy - 2, facing, phase, action)
        # Mouth/jaw slit (glowing)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        alpha_jaw = _NS_xelnarath._alpha(200 * pulse)
        pygame.draw.line(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                         (cx - 2, cy + 4), (cx + 2, cy + 4), 1)
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_dark"],
                         (cx - 2, cy + 4, 4, 1))
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                         (cx - 1, cy + 4, 2, 1))
    def _draw_head_horns(surface, cx, cy, facing, phase):
        """Curved horns crown."""
        sway = math.sin(phase * 0.4) * 1
        # 3 horns per side curving upward and back
        for side in (-1, 1):
            for i, (base_off_x, base_off_y, angle_off, length) in enumerate([
                (-3 * side, -8, math.pi * 0.55, 8),   # short outer
                (-1 * side, -10, math.pi * 0.65, 12), # tall middle
                (1 * side, -9, math.pi * 0.75, 10),   # inner
            ]):
                base_x = cx + base_off_x
                base_y = cy + base_off_y
                # Horn curves outward for outer, inward for inner
                dir_mult = side
                tip_x = base_x + int(math.cos(angle_off) * length) * dir_mult
                tip_y = base_y - int(math.sin(angle_off) * length) + int(sway)
                # Horn triangle
                perp_x = -math.sin(angle_off) * dir_mult
                perp_y = math.cos(angle_off)
                pa_x = base_x + int(perp_x * 2)
                pa_y = base_y + int(perp_y * 2)
                pb_x = base_x - int(perp_x * 2)
                pb_y = base_y - int(perp_y * 2)
                _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"], [
                    (tip_x + 1, tip_y + 1),
                    (pa_x + 1, pa_y + 1),
                    (pb_x + 1, pb_y + 1),
                ])
                _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_darkest"],
                                     [(tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y)])
                _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_dark"], [
                    (tip_x, tip_y),
                    (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                    (base_x, base_y),
                ])
                _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["chitin_mid"], [
                    (tip_x, tip_y),
                    (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                    (base_x, base_y),
                ])
                # Gold tip
                pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_mid"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_xelnarath.PALETTE["gold_light"],
                                 (tip_x, tip_y, 1, 1))
    def _draw_void_eyes(surface, cx, cy, facing, phase, action):
        """Two glowing magenta eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy
            # Socket
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_xelnarath._alpha(120 * (5 - r) / 5 * pulse)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            # Core
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["eye_mid"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
    # ============================================================
    # MELEE SWING SLASH
    # ============================================================
    def _draw_swing_slash(surface, boss, x, y, progress):
        """Arc slash effect during melee swing."""
        if progress < 0.3 or progress > 0.7:
            return
        facing = boss.direction
        t = (progress - 0.3) / 0.4
        # Arc slash centered at claw
        arc_cx = x + facing * 22
        arc_cy = y - 4
        # Draw arc slash with fading trail
        for arc_i in range(8):
            arc_t = t - arc_i * 0.04
            if arc_t < 0 or arc_t > 1:
                continue
            # Arc position (sweeps from up to down)
            angle_start = math.pi * 0.15 * facing
            angle_end = math.pi * 0.85 * facing
            angle = angle_start + (angle_end - angle_start) * arc_t
            arc_r = 28
            ax = arc_cx + int(math.cos(angle) * arc_r) * facing
            ay = arc_cy - int(math.sin(angle) * arc_r)
            alpha = _NS_xelnarath._alpha(240 - arc_i * 30)
            size = max(1, 6 - arc_i)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_darkest"], alpha),
                                    (ax, ay), size + 1)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                    (ax, ay), size)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_mid"], alpha),
                                    (ax, ay), max(1, size - 1))
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                    (ax, ay), max(1, size - 2))
            pygame.draw.rect(surface,
                             (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                             (ax, ay, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xelnarath.PALETTE["magenta_shine"], alpha),
                             (ax, ay, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Shadow (floating)."""
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = _NS_xelnarath._alpha((14 - radius) * 14 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius // 2,
                 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (10, 5, 20, 160), (10, 10, 120, 10))
        pygame.draw.ellipse(shadow, (50, 20, 80, 100), (18, 12, 104, 6))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_void_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Purple void wisps floating below."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(36, 3, -3):
            alpha = _NS_xelnarath._alpha((36 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_xelnarath._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xelnarath.PALETTE["void_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising void particles (magenta)
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_xelnarath._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_xelnarath._aacircle(surface, (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                                    (sx, sy), 3)
            _NS_xelnarath._aacircle(surface, (*_NS_xelnarath.PALETTE["void_light"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Star sparkles
        for i in range(8):
            spark_t = (phase * 0.6 + i * 0.15) % 1.0
            ex = cx - 26 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(spark_t * 24)
            alpha = _NS_xelnarath._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_xelnarath.PALETTE["star_mid"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_xelnarath.PALETTE["star_bright"], alpha),
                                 (ex, ey, 1, 1))
        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_xelnarath._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["void_mid"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_void_aura(surface, x, y, phase):
        """Large void aura with stars."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_xelnarath._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_xelnarath._aacircle(aura,
                                        (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                                        (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_xelnarath._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xelnarath._aacircle(aura,
                                        (*_NS_xelnarath.PALETTE["void_mid"], alpha),
                                        (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_xelnarath._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xelnarath._aacircle(aura,
                                        (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                        (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating star embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 40 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_xelnarath.PALETTE["magenta_hot"] if i % 2 == 0 \
                else _NS_xelnarath.PALETTE["star_bright"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_shine"], (sx, sy, 1, 1))
    def _draw_ground_portal(surface, x, y, phase, skill):
        """Void portal ring on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        # Multiple portal rings
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        # Runes/void spikes around
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_xelnarath.PALETTE["magenta_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_xelnarath.PALETTE["magenta_light"],
                                 _NS_xelnarath._alpha(150 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - VOID LANCE (dash projectile)
    # ============================================================
    def _draw_void_lance(surface, boss, x, y, timer, phase):
        """Fast void lance projectile."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        if progress < 0.2:
            # Charge at claw
            t = progress / 0.2
            hand_x = x + facing * 26
            hand_y = y - 6
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_xelnarath._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_darkest"], alpha),
                                        (hand_x, hand_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_xelnarath._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_mid"],
                                    (hand_x, hand_y), cr - 2)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                                    (hand_x, hand_y), max(1, cr - 4))
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_shine"],
                                    (hand_x, hand_y), max(1, cr - 6))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 30
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # LANCE SHAPE - draw an elongated shape (streak)
            # Direction vector
            angle_to = math.atan2(ty - start_y, tx - start_x)
            perp = angle_to + math.pi / 2
            # Long lance trail
            for i in range(14):
                trail_t = max(0.0, t - i * 0.03)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xelnarath._alpha(240 - i * 18)
                size = max(1, 9 - i)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_darkest"], alpha),
                                        (px, py), size)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                        (px, py), max(1, size - 3))
                if i < 6:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # BIG HEAD (bright)
            for r in range(16, 3, -2):
                alpha = _NS_xelnarath._alpha(100 * (16 - r) / 16)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                        (bx, by), r)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_darkest"], (bx, by), 11)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_dark"], (bx, by), 8)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_mid"], (bx, by), 6)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_light"], (bx, by), 4)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_hot"], (bx, by), 2)
            _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["white"], (bx, by, 1, 1))
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(14 + st * 30)
                alpha = _NS_xelnarath._alpha(240 * (1 - st))
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_darkest"], alpha),
                                        (tx, ty), radius + 4, 3)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                        (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - ABYSSAL VORTEX (galaxy swirl pull + knockup)
    # ============================================================
    def _draw_abyssal_vortex_ground(surface, boss, x, y, timer, phase):
        """Galaxy swirl at target."""
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r > 3:
            for i, (mult, alpha_val) in enumerate([
                (1.0, 220), (0.85, 200), (0.7, 180),
                (0.55, 160), (0.4, 140), (0.25, 120),
            ]):
                cur_r = int(r * mult)
                rot = phase * 2 + i * 0.5
                offset_x = int(math.cos(rot) * 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_xelnarath.PALETTE["void_dark"], alpha_val),
                                    (tx - cur_r + offset_x, ty - cur_r // 3,
                                     cur_r * 2, cur_r * 2 // 3), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_dark"], alpha_val),
                                    (tx - cur_r + offset_x + 1, ty - cur_r // 3 + 1,
                                     cur_r * 2 - 2, cur_r * 2 // 3 - 2), 1)
    def _draw_abyssal_vortex_foreground(surface, boss, x, y, timer, phase):
        """Spiral galaxy stars pulled to center."""
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r < 5:
            return
        # Spiral galaxy stars (dense)
        for i in range(35):
            spiral_t = (phase * 1.5 + i * 0.09) % 1.0
            dist = r * (1 - spiral_t * 0.9)
            angle = phase * 3 + i * math.pi / 17 + spiral_t * math.pi * 3
            sx = tx + int(math.cos(angle) * dist)
            sy = ty + int(math.sin(angle) * dist * 0.55)
            alpha = _NS_xelnarath._alpha(240 * spiral_t)
            if i % 3 == 0:
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                        (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                 (sx, sy, 1, 1))
            else:
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["star_bright"], alpha),
                                 (sx, sy, 1, 1))
        # Center glow
        for r_inner in range(10, 0, -1):
            alpha = _NS_xelnarath._alpha(150 * (10 - r_inner) / 10)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                    (tx, ty), r_inner)
        _NS_xelnarath._aacircle(surface, _NS_xelnarath.PALETTE["magenta_shine"], (tx, ty), 2)
        pygame.draw.rect(surface, _NS_xelnarath.PALETTE["white"], (tx, ty, 1, 1))
        # Knockup arrows (upward)
        if progress > 0.5:
            for i in range(6):
                angle = i * math.pi / 3
                ax = tx + int(math.cos(angle) * r * 0.6)
                ay = ty + int(math.sin(angle) * r * 0.3)
                # Upward arrow
                pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                                 (ax, ay), (ax, ay - 12), 2)
                pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_shine"],
                                 (ax, ay - 12), (ax - 2, ay - 8), 1)
                pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_shine"],
                                 (ax, ay - 12), (ax + 2, ay - 8), 1)
    # ============================================================
    # SKILL E - VOID SPIKES (crystal spikes from ground)
    # ============================================================
    def _draw_void_spikes_ground(surface, boss, x, y, timer, phase):
        """Ground crack marks."""
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))
        if r > 3:
            # Ground cracks
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.1
                x1 = tx + int(math.cos(angle) * 8)
                y1 = ty + int(math.sin(angle) * 5)
                x2 = tx + int(math.cos(angle) * r)
                y2 = ty + int(math.sin(angle) * r * 0.5)
                pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_dark"],
                                 (x1, y1), (x2, y2), 2)
                pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                                 (x1, y1), (x2, y2), 1)
    def _draw_void_spikes_foreground(surface, boss, x, y, timer, phase):
        """Crystal spikes erupting from ground."""
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Warning: growing circle
            t = progress / 0.2
            r = int(35 * t)
            alpha = _NS_xelnarath._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            return
        # Erupt phase: crystal spikes rise
        t = (progress - 0.2) / 0.8
        # Erupt intensity
        rise_t = min(1.0, t * 3)
        fade_t = max(0, (t - 0.7) / 0.3)
        # Multiple crystal spikes in cluster
        spike_configs = [
            (0, 0, 28, 8),      # center tallest
            (-14, 3, 20, 6),
            (14, 3, 20, 6),
            (-22, 6, 15, 5),
            (22, 6, 15, 5),
            (-8, -2, 22, 6),
            (8, -2, 22, 6),
        ]
        for dx, dy, max_h, width in spike_configs:
            spike_x = tx + dx
            spike_y = ty + dy
            cur_h = int(max_h * rise_t)
            if cur_h < 2:
                continue
            spike_tip_y = spike_y - cur_h
            # Spike triangle
            alpha_s = _NS_xelnarath._alpha(240 * (1 - fade_t))
            spike_surf_pts_shadow = [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - width + 1, spike_y + 1),
                (spike_x + width + 1, spike_y + 1),
            ]
            spike_surf_pts = [
                (spike_x, spike_tip_y),
                (spike_x - width, spike_y),
                (spike_x + width, spike_y),
            ]
            # Shadow
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["shadow_deep"],
                                 spike_surf_pts_shadow)
            # Dark
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_darkest"],
                                 spike_surf_pts)
            # Mid
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - width + 1, spike_y),
                (spike_x + width - 1, spike_y),
            ])
            _NS_xelnarath._poly(surface, _NS_xelnarath.PALETTE["void_mid"], [
                (spike_x, spike_tip_y + 1),
                (spike_x - width + 2, spike_y),
                (spike_x + width - 2, spike_y),
            ])
            # Magenta core (glowing crack down middle)
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_dark"],
                             (spike_x, spike_tip_y + 2),
                             (spike_x, spike_y - 1), 1)
            pygame.draw.line(surface, _NS_xelnarath.PALETTE["magenta_hot"],
                             (spike_x, spike_tip_y + 3),
                             (spike_x, spike_y - 2), 1)
            # Bright tip
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_shine"],
                             (spike_x, spike_tip_y, 1, 2))
            pygame.draw.rect(surface, _NS_xelnarath.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))
            # Sparkles around spike
            for i in range(3):
                spark_angle = phase * 3 + i * math.pi / 1.5
                sxx = spike_x + int(math.cos(spark_angle) * (width + 3))
                syy = spike_y - cur_h // 2 + int(math.sin(spark_angle) * (cur_h // 2))
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_hot"], alpha_s),
                                 (sxx, syy, 1, 1))
    # ============================================================
    # SKILL R - ENDLESS DEVOUR (massive void consumption)
    # ============================================================
    def _draw_endless_devour_ground(surface, boss, x, y, timer, phase):
        """Massive void field."""
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Warning grows
            t = progress / 0.3
            r = int(75 * t)
            alpha = _NS_xelnarath._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_xelnarath.PALETTE["void_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            # Active field
            t = (progress - 0.3) / 0.7
            r = 75 + int(t * 10)
            alpha = _NS_xelnarath._alpha(240 * (1 - t * 0.4))
            pygame.draw.ellipse(surface,
                                (*_NS_xelnarath.PALETTE["abyss_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_xelnarath.PALETTE["void_darkest"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                                (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                                (tx - r + 10, ty - r // 3 + 6,
                                 r * 2 - 20, r * 2 // 3 - 12))
    def _draw_endless_devour_foreground(surface, boss, x, y, timer, phase):
        """Massive void portal with consuming tendrils."""
        tx, ty = _NS_xelnarath._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Gathering
            t = progress / 0.3
            for i in range(12):
                angle = phase * 2 + i * math.pi / 6
                gather_r = int(40 * (1 - t))
                gx = tx + int(math.cos(angle) * gather_r)
                gy = ty + int(math.sin(angle) * gather_r * 0.5)
                alpha = _NS_xelnarath._alpha(200 * t)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                        (gx, gy), 3)
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                 (gx, gy, 1, 1))
        elif progress < 0.85:
            # Devour phase - huge portal + tendrils
            t = (progress - 0.3) / 0.55
            intensity = math.sin(t * math.pi)
            # Massive portal in the sky
            portal_r = int(50 + intensity * 20)
            portal_y = ty - 30
            # Outer dark ring
            for r_o in range(portal_r, portal_r - 8, -1):
                alpha = _NS_xelnarath._alpha(200 * intensity)
                _NS_xelnarath._aacircle(surface,
                                        (*_NS_xelnarath.PALETTE["abyss_dark"], alpha),
                                        (tx, portal_y), r_o)
            # Portal interior (dark abyss)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["abyss_dark"], 240),
                                    (tx, portal_y), portal_r - 8)
            _NS_xelnarath._aacircle(surface,
                                    (*_NS_xelnarath.PALETTE["void_darkest"], 220),
                                    (tx, portal_y), portal_r - 12)
            # Swirling energy inside portal
            for i in range(20):
                spiral_t = (phase * 2 + i * 0.1) % 1.0
                dist = (portal_r - 10) * spiral_t
                sangle = phase * 4 + i * math.pi / 10 + spiral_t * math.pi * 2
                sx = tx + int(math.cos(sangle) * dist)
                sy = portal_y + int(math.sin(sangle) * dist * 0.9)
                alpha = _NS_xelnarath._alpha(230 * (1 - spiral_t))
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Portal edge glow
            for i in range(24):
                angle = i * math.pi / 12
                ex = tx + int(math.cos(angle) * portal_r)
                ey = portal_y + int(math.sin(angle) * portal_r)
                pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_hot"], (ex, ey, 2, 2))
                pygame.draw.rect(surface, _NS_xelnarath.PALETTE["magenta_shine"], (ex, ey, 1, 1))
            # Tendrils reaching down to consume enemies
            for i in range(8):
                tendril_angle = i * math.pi / 4 + phase * 0.5
                tendril_len = int(50 * intensity)
                # Wavy tendril
                prev_x = tx
                prev_y = portal_y
                for seg in range(1, 8):
                    seg_t = seg / 7
                    wx = tx + int(math.cos(tendril_angle) * tendril_len * seg_t)
                    wy = portal_y + int(seg_t * (ty - portal_y) * 1.5)
                    wx += int(math.sin(phase * 3 + seg + i) * 4)
                    alpha = _NS_xelnarath._alpha(220 * intensity * (1 - seg_t * 0.5))
                    pygame.draw.line(surface,
                                     (*_NS_xelnarath.PALETTE["magenta_dark"], alpha),
                                     (prev_x, prev_y), (wx, wy), 3)
                    pygame.draw.line(surface,
                                     (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                     (prev_x, prev_y), (wx, wy), 1)
                    prev_x = wx
                    prev_y = wy
            # Ground impact sparks
            impact_r = int(20 + intensity * 30)
            for i in range(15):
                angle_s = i * math.pi / 7.5
                sx = tx + int(math.cos(angle_s) * impact_r)
                sy = ty + int(math.sin(angle_s) * impact_r * 0.5)
                alpha = _NS_xelnarath._alpha(240 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                 (sx, sy, 2, 2))
        else:
            # Aftermath
            t = (progress - 0.85) / 0.15
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 45)
                alpha = _NS_xelnarath._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_xelnarath._aacircle(surface,
                                            (*_NS_xelnarath.PALETTE["void_dark"], alpha),
                                            (rx, ry), 3)
                    _NS_xelnarath._aacircle(surface,
                                            (*_NS_xelnarath.PALETTE["magenta_light"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_xelnarath.PALETTE["magenta_hot"], alpha),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kazreth(surface, boss, x, y):
    """Entry point kazreth."""
    return _NS_kazreth.draw_kazreth(surface, boss, x, y)


def draw_varkuthar(surface, boss, x, y):
    """Entry point varkuthar."""
    return _NS_varkuthar.draw_varkuthar(surface, boss, x, y)


def draw_zhyvrek(surface, boss, x, y):
    """Entry point zhyvrek."""
    return _NS_zhyvrek.draw_zhyvrek(surface, boss, x, y)


def draw_xelnarath(surface, boss, x, y):
    """Entry point xelnarath."""
    return _NS_xelnarath.draw_xelnarath(surface, boss, x, y)
