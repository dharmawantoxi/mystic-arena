"""
bosses/level28.py - Semua boss Level 28

Berisi:
  - morthyrax    (mini boss - MELEE ever-rotting prophet, decay)
  - sanguiveth   (mini boss - MELEE bloodbound famine, bone wings)
  - xerakhotep   (mini boss - RANGED sunborne sovereign, solar magic)
  - nyrethzalv   (TRUE BOSS - RANGED forsaken empress of shadow-chains)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _sng_ (sanguiveth), _xer_ (xerakhotep) sudah unik.
  - _mor_ (morthyrax) di-rename -> _mth_ (bentrok dengan Morgath level 1),
    termasuk atribut _last_x/_last_y.
  - _nyz_ (nyrethzalv) di-rename -> _nzl_ (bentrok dengan nyzrak level 3),
    termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# MORTHYRAX (EVER-ROTTING PROPHET) - Mini Boss
# ====================================================================

class _NS_morthyrax:
    """Namespace morthyrax - undead lich mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Rotting flesh (skin)
        "flesh_darkest": (18, 25, 15),
        "flesh_dark": (45, 55, 35),
        "flesh_mid": (85, 95, 65),
        "flesh_light": (135, 145, 105),
        "flesh_shine": (185, 190, 150),
        # Bone (skull, ribs, horns)
        "bone_darkest": (35, 30, 20),
        "bone_dark": (85, 75, 55),
        "bone_mid": (155, 140, 105),
        "bone_light": (220, 205, 165),
        "bone_shine": (250, 240, 210),
        # Toxic green (aura, eyes, magic)
        "toxic_darkest": (10, 25, 5),
        "toxic_dark": (30, 75, 15),
        "toxic_mid": (90, 175, 35),
        "toxic_light": (160, 240, 80),
        "toxic_hot": (210, 255, 130),
        "toxic_shine": (245, 255, 200),
        # Rust brown (chains, armor plates)
        "rust_darkest": (25, 15, 8),
        "rust_dark": (55, 35, 20),
        "rust_mid": (95, 65, 40),
        "rust_light": (140, 100, 65),
        # Blood/gore (accents)
        "gore_dark": (40, 8, 8),
        "gore_mid": (90, 20, 15),
        "gore_light": (140, 40, 30),
        # Dark leather/cloth
        "cloth_darkest": (8, 10, 8),
        "cloth_dark": (25, 28, 22),
        "cloth_mid": (50, 55, 40),
        # Eye glow (bright toxic)
        "eye_socket": (2, 5, 2),
        "eye_dark": (20, 60, 10),
        "eye_mid": (110, 220, 50),
        "eye_light": (200, 255, 120),
        "eye_glow": (240, 255, 200),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morthyrax._clamp(color)
        if _NS_morthyrax.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morthyrax._clamp(color)
        if _NS_morthyrax.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morthyrax._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morthyrax(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morthyrax._detect_moving(boss)
        _NS_morthyrax._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_mth_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_morthyrax._draw_death_aura(surface, x, y, pulse)
        _NS_morthyrax._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":
            _NS_morthyrax._draw_tombstone_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morthyrax._draw_fleshgolem_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_morthyrax._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_morthyrax._draw_float_move(surface, boss, x, y)
        else:
            _NS_morthyrax._draw_float_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_morthyrax._draw_decay_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morthyrax._draw_soulrip_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morthyrax._draw_tombstone_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morthyrax._draw_fleshgolem_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mth_previous_timer", 0))
        active = bool(getattr(boss, "_mth_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._mth_attack_active = True
            boss._mth_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mth_attack_frame = int(getattr(boss, "_mth_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mth_attack_active = False
            boss._mth_attack_frame = 0
            active = False
        boss._mth_previous_timer = timer
        boss._mth_attack_progress = (
            min(1.0, getattr(boss, "_mth_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_mth_last_x"):
            boss._mth_last_x = boss.x
            boss._mth_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mth_last_x)
        dy = abs(boss.y - boss._mth_last_y)
        boss._mth_last_x = boss.x
        boss._mth_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.7) * 5) - 8
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_morthyrax._draw_float_shadow(surface, x + sway, y + 50, boss.pulse)
        _NS_morthyrax._draw_plague_mist(surface, x + sway, y + 40, boss.pulse)
        _NS_morthyrax._draw_body(surface, x + sway, y + hover,
                                 boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        hover = int(math.sin(phase * 0.9) * 6) - 9
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_morthyrax._draw_float_shadow(surface, x + sway, y + 50, phase)
        _NS_morthyrax._draw_plague_mist(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_morthyrax._draw_body(surface, x + sway, y + hover,
                                 boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Melee attack — big claw swing forward."""
        progress = getattr(boss, "_mth_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 20)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(15 * (1 - t)) * boss.direction
            lift = int(-2 + t * 4)
        hover = int(math.sin(boss.pulse * 0.7) * 3) - 6
        _NS_morthyrax._draw_float_shadow(surface, x + lunge, y + 50, boss.pulse)
        _NS_morthyrax._draw_plague_mist(surface, x + lunge, y + 40,
                                        boss.pulse, intense=True)
        _NS_morthyrax._draw_body(surface, x + lunge, y + hover - lift,
                                 boss.direction, boss.pulse,
                                 "attack", progress)
        _NS_morthyrax._draw_claw_swing(surface, boss, x + lunge,
                                       y + hover - lift, progress)
    # ============================================================
    # BODY - Undead Lich figure
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Chains hanging behind first
        _NS_morthyrax._draw_back_chains(surface, cx, cy, facing, phase)
        # Torn cloth cape
        _NS_morthyrax._draw_torn_cape(surface, cx, cy, facing, phase, action)
        # Torso (exposed ribcage)
        _NS_morthyrax._draw_ribcage_torso(surface, cx, cy, facing, phase)
        # Legs (dangling/tattered)
        _NS_morthyrax._draw_undead_legs(surface, cx, cy + 8, facing, phase, action)
        # Back arm
        _NS_morthyrax._draw_back_arm(surface, cx, cy - 2, facing, phase, action,
                                     attack_progress)
        # Head with horns and skull face
        _NS_morthyrax._draw_horned_skull(surface, cx, cy - 20, facing, phase, action,
                                         attack_progress)
        # Front arm (claw/spellcast)
        _NS_morthyrax._draw_claw_arm(surface, cx, cy - 2, facing, phase, action,
                                     attack_progress)
    def _draw_back_chains(surface, cx, cy, facing, phase):
        """Rusted chains hanging behind body."""
        sway = math.sin(phase * 0.5) * 2
        # 3 chains hanging back
        for i, (base_off_x, base_off_y, length) in enumerate([
            (-facing * 3, -6, 24),
            (-facing * 5, 0, 30),
            (-facing * 2, 4, 20),
        ]):
            base_x = cx + base_off_x
            base_y = cy + base_off_y
            prev = (base_x, base_y)
            for step in range(1, 8):
                t = step / 7
                seg_x = base_x + int(math.sin(phase * 0.4 + i + t * 2) * (sway + t * 2))
                seg_y = base_y + int(t * length)
                # Chain link (small oval)
                if step % 2 == 0:
                    # Full circle link
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                                     (seg_x - 1, seg_y - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_darkest"],
                                     (seg_x - 1, seg_y - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                                     (seg_x - 1, seg_y - 1, 2, 2))
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_mid"],
                                     (seg_x, seg_y - 1, 1, 1))
                else:
                    # Small connection
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_darkest"],
                                     (seg_x, seg_y, 2, 2))
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                                     (seg_x, seg_y, 1, 1))
                prev = (seg_x, seg_y)
    def _draw_torn_cape(surface, cx, cy, facing, phase, action):
        """Ragged dark cloth cape."""
        wind = math.sin(phase * 0.6) * 3
        sway = math.sin(phase * 0.4) * 2
        back = -facing
        cape_pts = [
            (cx - facing * 2, cy - 4),
            (cx + back * 4, cy - 2),
            (cx + back * 8, cy + 4 + int(wind)),
            (cx + back * 11, cy + 12 + int(sway)),
            (cx + back * 13, cy + 20 + int(sway * 1.2)),
            (cx + back * 10, cy + 28 + int(sway * 0.8)),
            # Torn edges
            (cx + back * 8, cy + 26),
            (cx + back * 6, cy + 30 + int(sway * 0.6)),
            (cx + back * 4, cy + 26),
            (cx + back * 2, cy + 30 + int(sway * 0.5)),
            (cx, cy + 24),
            (cx + facing * 2, cy + 8),
        ]
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in cape_pts])
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["cloth_darkest"], cape_pts)
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["cloth_dark"], [
            (cx + back * 2, cy - 2),
            (cx + back * 6, cy + 2 + int(wind)),
            (cx + back * 9, cy + 12 + int(sway * 0.8)),
            (cx + back * 10, cy + 22 + int(sway * 0.8)),
            (cx + back * 6, cy + 24),
            (cx + back * 3, cy + 22),
            (cx, cy + 6),
        ])
        # Green magical glow at bottom edges of cape
        for edge_x in [cx + back * 10, cx + back * 6, cx + back * 2]:
            edge_y = cy + 26 + int(sway * 0.6)
            glow_alpha = _NS_morthyrax._alpha(120 + math.sin(phase * 2) * 40)
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["toxic_dark"], glow_alpha),
                             (edge_x, edge_y, 1, 2))
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["toxic_light"], glow_alpha),
                             (edge_x, edge_y, 1, 1))
    def _draw_ribcage_torso(surface, cx, cy, facing, phase):
        """Exposed ribcage torso - undead lich body."""
        breath = math.sin(phase * 0.7) * 1
        # Base torso silhouette (dark flesh)
        torso_pts = [
            (cx - 10, cy - 6),
            (cx - 11, cy - 1),
            (cx - 10, cy + 6),
            (cx - 7, cy + 11),
            (cx + 7, cy + 11),
            (cx + 10, cy + 6),
            (cx + 11, cy - 1),
            (cx + 10, cy - 6),
        ]
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["flesh_darkest"], torso_pts)
        # Rotting flesh layer
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["flesh_dark"], [
            (cx - 9, cy - 5),
            (cx - 10, cy),
            (cx - 9, cy + 5),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 9, cy + 5),
            (cx + 10, cy),
            (cx + 9, cy - 5),
        ])
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["flesh_mid"], [
            (cx - 7, cy - 3),
            (cx - 8, cy + 1),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 8, cy + 1),
            (cx + 7, cy - 3),
        ])
        # EXPOSED RIBS (bone showing through center)
        # Sternum
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (cx - 1, cy - 4, 3, 12))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                         (cx - 1, cy - 4, 2, 12))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_dark"],
                         (cx - 1, cy - 4, 2, 11))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_mid"],
                         (cx, cy - 4, 1, 11))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_light"],
                         (cx, cy - 3, 1, 9))
        # RIB BONES arching on both sides
        for i, rib_y in enumerate([-2, 1, 4, 7]):
            # Left rib
            _NS_morthyrax._draw_rib(surface, cx, cy + rib_y, -1, phase, i)
            # Right rib
            _NS_morthyrax._draw_rib(surface, cx, cy + rib_y, 1, phase, i)
        # Green glow between ribs (chest cavity)
        cavity_pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_morthyrax._alpha(80 * (6 - r) / 6 * cavity_pulse)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                    (cx, cy + 2), r)
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_hot"], (cx, cy + 2, 1, 1))
        # CHAIN across chest (bandolier style)
        for i, (cx_off, cy_off) in enumerate([
            (-8, -3), (-5, 0), (-2, 3), (2, 3), (5, 0), (8, -3),
        ]):
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                             (cx + cx_off, cy + cy_off, 2, 2))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_darkest"],
                             (cx + cx_off, cy + cy_off, 2, 2))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                             (cx + cx_off, cy + cy_off, 1, 1))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_mid"],
                             (cx + cx_off, cy + cy_off, 1, 1))
        # SHOULDER SPIKES (like Undying's shoulder pauldrons with horns)
        for side in (-1, 1):
            spike_x = cx + side * 10
            spike_y = cy - 6
            # Base plate
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"], [
                (spike_x - 3, spike_y),
                (spike_x + 3, spike_y),
                (spike_x + 3, spike_y + 5),
                (spike_x - 3, spike_y + 5),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_darkest"], [
                (spike_x - 3, spike_y - 1),
                (spike_x + 3, spike_y - 1),
                (spike_x + 3, spike_y + 4),
                (spike_x - 3, spike_y + 4),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_dark"], [
                (spike_x - 2, spike_y - 1),
                (spike_x + 2, spike_y - 1),
                (spike_x + 2, spike_y + 3),
                (spike_x - 2, spike_y + 3),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_mid"], [
                (spike_x - 2, spike_y),
                (spike_x + 2, spike_y),
                (spike_x + 1, spike_y + 2),
                (spike_x - 1, spike_y + 2),
            ])
            # Spike on top
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_darkest"], [
                (spike_x - 2, spike_y),
                (spike_x + 2, spike_y),
                (spike_x, spike_y - 6),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_dark"], [
                (spike_x - 1, spike_y),
                (spike_x + 1, spike_y),
                (spike_x, spike_y - 5),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_light"], [
                (spike_x - 1, spike_y - 1),
                (spike_x + 1, spike_y - 1),
                (spike_x, spike_y - 4),
            ])
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_shine"],
                             (spike_x, spike_y - 5, 1, 1))
    def _draw_rib(surface, cx, cy, side, phase, i):
        """Individual rib bone curving from sternum."""
        # Rib curves from center outward
        start_x = cx + side * 1
        start_y = cy
        end_x = cx + side * 6
        end_y = cy + 1
        # Rib arc points
        mid_x = cx + side * 4
        mid_y = cy - 1
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (start_x + 1, start_y + 1),
                         (mid_x + 1, mid_y + 1), 2)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (mid_x + 1, mid_y + 1),
                         (end_x + 1, end_y + 1), 2)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                         (start_x, start_y), (mid_x, mid_y), 2)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                         (mid_x, mid_y), (end_x, end_y), 2)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_dark"],
                         (start_x, start_y), (mid_x, mid_y), 1)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_dark"],
                         (mid_x, mid_y), (end_x, end_y), 1)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_mid"],
                         (start_x, start_y - 1), (mid_x, mid_y - 1), 1)
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_light"],
                         (mid_x, mid_y - 1, 1, 1))
    def _draw_undead_legs(surface, cx, cy, facing, phase, action):
        """Tattered undead legs dangling because floating."""
        sway = math.sin(phase * 0.9) * 1.5
        for side in (-1, 1):
            leg_x_top = cx + side * 4
            leg_x_bot = cx + side * 5 + int(sway * side * 0.5)
            leg_y_top = cy
            leg_y_bot = cy + 15
            # Rotting flesh leg
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                             (leg_x_top + 1, leg_y_top + 1),
                             (leg_x_bot + 1, leg_y_bot + 1), 6)
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_darkest"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 5)
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_dark"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 4)
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_mid"],
                             (leg_x_top - side, leg_y_top),
                             (leg_x_bot - side, leg_y_bot), 2)
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_light"],
                             (leg_x_top - side, leg_y_top + 1),
                             (leg_x_bot - side, leg_y_bot - 1), 1)
            # Exposed bone at joints
            knee_y = leg_y_top + 8
            knee_x = leg_x_top + int((leg_x_bot - leg_x_top) * 0.5)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_dark"],
                             (knee_x - 1, knee_y, 3, 2))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_mid"],
                             (knee_x, knee_y, 2, 1))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_light"],
                             (knee_x, knee_y, 1, 1))
            # Tattered wraps at bottom
            wrap_x = leg_x_bot
            wrap_y = leg_y_bot
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"], [
                (wrap_x - 3, wrap_y - 2),
                (wrap_x + 3, wrap_y - 2),
                (wrap_x + 4, wrap_y + 2),
                (wrap_x + 2, wrap_y + 4),
                (wrap_x - 2, wrap_y + 4),
                (wrap_x - 4, wrap_y + 2),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["cloth_darkest"], [
                (wrap_x - 3, wrap_y - 3),
                (wrap_x + 3, wrap_y - 3),
                (wrap_x + 3, wrap_y + 2),
                (wrap_x - 3, wrap_y + 2),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["cloth_dark"], [
                (wrap_x - 3, wrap_y - 3),
                (wrap_x + 3, wrap_y - 3),
                (wrap_x + 2, wrap_y),
                (wrap_x - 2, wrap_y),
            ])
            # Torn strips hanging
            for strip_x_off in (-2, 0, 2):
                strip_len = 2 + (strip_x_off + 2) % 3
                pygame.draw.line(surface, _NS_morthyrax.PALETTE["cloth_dark"],
                                 (wrap_x + strip_x_off, wrap_y + 2),
                                 (wrap_x + strip_x_off, wrap_y + 2 + strip_len), 1)
            # Green glow (souls escaping)
            if action != "attack":
                glow_alpha = _NS_morthyrax._alpha(80 + math.sin(phase * 2 + side) * 30)
                pygame.draw.rect(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_light"], glow_alpha),
                                 (wrap_x, wrap_y + 2, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (holding lantern like Undying reference)."""
        back_shoulder_x = cx - facing * 5
        back_shoulder_y = cy - 2
        # Arm hangs down
        arm_angle = math.pi * 0.4 + math.sin(phase * 0.5) * 0.1
        arm_length = 12
        hand_x = back_shoulder_x - int(math.cos(arm_angle) * arm_length) * facing
        hand_y = back_shoulder_y + int(math.sin(arm_angle) * arm_length)
        elbow_x = back_shoulder_x - int(math.cos(arm_angle) * (arm_length * 0.5)) * facing
        elbow_y = back_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.5))
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_mid"],
                         (back_shoulder_x - 1, back_shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 5)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_mid"],
                         (elbow_x - 1, elbow_y), (hand_x - 1, hand_y), 1)
        # LANTERN in back hand
        _NS_morthyrax._draw_soul_lantern(surface, hand_x, hand_y + 2, phase)
    def _draw_soul_lantern(surface, lx, ly, phase):
        """Small green-glowing soul lantern."""
        # Chain from hand to lantern top
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["rust_dark"],
                         (lx, ly - 2), (lx, ly + 2), 1)
        # Lantern frame
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (lx - 3, ly + 2, 6, 7))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_darkest"],
                         (lx - 3, ly + 2, 6, 6))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                         (lx - 3, ly + 2, 6, 1))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                         (lx - 3, ly + 7, 6, 1))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                         (lx - 3, ly + 2, 1, 6))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                         (lx + 2, ly + 2, 1, 6))
        # Green soul flame inside
        flame_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_morthyrax._alpha(200 * (4 - r) / 4 * flame_pulse)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                    (lx, ly + 5), r)
        _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_mid"],
                                (lx, ly + 5), 2)
        _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_light"],
                                (lx, ly + 5), 1)
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_shine"],
                         (lx, ly + 5, 1, 1))
        # Green glow around lantern
        for r in range(8, 2, -1):
            alpha = _NS_morthyrax._alpha(60 * (8 - r) / 8 * flame_pulse)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                    (lx, ly + 5), r)
    def _draw_claw_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with big claws — main attack limb."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 2
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.4 * t  # raise up/back
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.4 + math.pi * 1.0 * t  # swing down/forward
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.6 * (1 - t) - math.pi * 0.1 * t
        else:
            # Casting pose — arm extended forward, palm out
            arm_angle = math.pi * 0.05 + math.sin(phase * 0.6) * 0.1
        arm_length = 13
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 4
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 2
        # Upper arm (muscular flesh)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 6)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_mid"],
                         (shoulder_x - 1, shoulder_y), (elbow_x - 1, elbow_y), 3)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_light"],
                         (shoulder_x - 1, shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Forearm
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 6)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 5)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["flesh_mid"],
                         (elbow_x - 1, elbow_y), (hand_x - 1, hand_y), 3)
        # Bracer (rusted iron on forearm)
        forearm_mid_x = int((elbow_x + hand_x) / 2)
        forearm_mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_darkest"],
                         (forearm_mid_x - 3, forearm_mid_y - 2, 6, 4))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_dark"],
                         (forearm_mid_x - 3, forearm_mid_y - 2, 6, 3))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_mid"],
                         (forearm_mid_x - 2, forearm_mid_y - 2, 4, 2))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["rust_light"],
                         (forearm_mid_x - 2, forearm_mid_y - 2, 4, 1))
        # PALM (open hand for casting/claw)
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (hand_x - 2, hand_y - 1, 5, 5))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["flesh_darkest"],
                         (hand_x - 2, hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["flesh_dark"],
                         (hand_x - 2, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["flesh_mid"],
                         (hand_x - 1, hand_y - 1, 3, 2))
        # LONG CLAWS on hand fingers
        for i in range(4):
            claw_angle = arm_angle - math.pi * 0.15 + i * math.pi * 0.1
            claw_len = 7
            claw_tip_x = hand_x + int(math.cos(claw_angle) * claw_len) * facing
            claw_tip_y = hand_y + int(math.sin(claw_angle) * claw_len) + 1
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                             (hand_x + 1, hand_y + 1),
                             (claw_tip_x + 1, claw_tip_y + 1), 3)
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_dark"],
                             (hand_x, hand_y),
                             (claw_tip_x, claw_tip_y), 2)
            pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_mid"],
                             (hand_x, hand_y),
                             (claw_tip_x, claw_tip_y), 1)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_light"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            # Green tip (magic infusion)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_mid"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_light"],
                             (claw_tip_x, claw_tip_y, 1, 1))
        # GREEN CASTING GLOW on palm (idle only)
        if action != "attack":
            palm_pulse = math.sin(phase * 2) * 0.4 + 0.6
            for r in range(6, 0, -1):
                alpha = _NS_morthyrax._alpha(150 * (6 - r) / 6 * palm_pulse)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                        (hand_x + facing * 3, hand_y + 1), r)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_light"],
                                    (hand_x + facing * 3, hand_y + 1), 2)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_shine"],
                             (hand_x + facing * 3, hand_y + 1, 1, 1))
    def _draw_horned_skull(surface, cx, cy, facing, phase, action, attack_progress):
        """Massive skull head with curved horns (like Undying)."""
        # Skull shape
        skull_pts = [
            (cx - 9, cy + 4),
            (cx - 11, cy),
            (cx - 10, cy - 6),
            (cx - 6, cy - 10),
            (cx + 6, cy - 10),
            (cx + 10, cy - 6),
            (cx + 11, cy),
            (cx + 9, cy + 4),
            (cx + 5, cy + 8),   # jaw
            (cx, cy + 10),
            (cx - 5, cy + 8),
        ]
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in skull_pts])
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_darkest"], skull_pts)
        # Bone layers
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_dark"], [
            (cx - 8, cy + 3),
            (cx - 10, cy),
            (cx - 9, cy - 5),
            (cx - 5, cy - 9),
            (cx + 5, cy - 9),
            (cx + 9, cy - 5),
            (cx + 10, cy),
            (cx + 8, cy + 3),
            (cx + 4, cy + 7),
            (cx, cy + 9),
            (cx - 4, cy + 7),
        ])
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_mid"], [
            (cx - 6, cy + 1),
            (cx - 8, cy - 1),
            (cx - 7, cy - 5),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 7, cy - 5),
            (cx + 8, cy - 1),
            (cx + 6, cy + 1),
            (cx + 3, cy + 5),
            (cx, cy + 6),
            (cx - 3, cy + 5),
        ])
        # Highlights
        _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_light"], [
            (cx - 4, cy - 3),
            (cx - 5, cy - 5),
            (cx - 2, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 4),
            (cx + 3, cy - 2),
            (cx - 2, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_shine"],
                         (cx + facing * 2, cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_shine"],
                         (cx - facing * 1, cy - 5, 1, 1))
        # Skull cracks (gothic detail)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                         (cx - 3, cy - 7), (cx - 1, cy - 3), 1)
        pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                         (cx + 4, cy - 6), (cx + 2, cy - 2), 1)
        # HUGE CURVED HORNS (like Undying reference)
        _NS_morthyrax._draw_curved_horns(surface, cx, cy - 8, facing, phase)
        # DEEP EYE SOCKETS with glowing green eyes
        _NS_morthyrax._draw_skull_eyes(surface, cx, cy - 3, facing, phase, action)
        # NOSE HOLE (skull nose)
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                         (cx - 1, cy, 2, 3))
        pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                         (cx - 1, cy, 2, 2))
        # SKULL JAW with teeth (opens on attack)
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 5)
        _NS_morthyrax._draw_skull_jaw(surface, cx, cy + 5, facing, phase, mouth_open)
    def _draw_curved_horns(surface, cx, cy, facing, phase):
        """Two massive curved horns coming from the skull."""
        sway = math.sin(phase * 0.3) * 0.5
        for side in (-1, 1):
            # Horn base at top of skull
            base_x = cx + side * 4
            base_y = cy
            # Horn curves out then up
            mid_x = cx + side * 9
            mid_y = cy - 2
            tip_x = cx + side * 12
            tip_y = cy - 10 + int(sway * side)
            # Horn shape (curved triangle)
            perp_offset = 2
            # Draw as thick segmented curve
            segments = 5
            prev_a = (base_x + side, base_y + 1)
            prev_b = (base_x - side, base_y - 1)
            for step in range(1, segments + 1):
                t = step / segments
                # Bezier interpolation
                bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x)
                by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y)
                thickness = max(1, int(3 - t * 2))
                # Perpendicular for horn width
                dx = bx - prev_a[0] if step == 1 else bx - int((1 - (t - 1/segments)) ** 2 * base_x + 2 * (1 - (t - 1/segments)) * (t - 1/segments) * mid_x + (t - 1/segments) ** 2 * tip_x)
                dy = by - prev_a[1] if step == 1 else by - int((1 - (t - 1/segments)) ** 2 * base_y + 2 * (1 - (t - 1/segments)) * (t - 1/segments) * mid_y + (t - 1/segments) ** 2 * tip_y)
                seg_len = max(1, math.hypot(dx, dy))
                perp_x = -dy / seg_len * thickness
                perp_y = dx / seg_len * thickness
                a = (int(bx + perp_x), int(by + perp_y))
                b = (int(bx - perp_x), int(by - perp_y))
                _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                                    [prev_a, prev_b, (b[0] + 1, b[1] + 1),
                                     (a[0] + 1, a[1] + 1)])
                _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_darkest"],
                                    [prev_a, prev_b, b, a])
                # Inner shading
                inner_a = (int((prev_a[0] + a[0]) / 2), int((prev_a[1] + a[1]) / 2))
                inner_b = (int((prev_b[0] + b[0]) / 2), int((prev_b[1] + b[1]) / 2))
                _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_dark"],
                                    [prev_a, prev_b, inner_b, inner_a])
                # Highlight along top edge
                pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_mid"],
                                 prev_a, a, 1)
                if step > 1:
                    pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_light"],
                                     prev_a, a, 1)
                prev_a = a
                prev_b = b
            # Sharp tip
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_dark"],
                                [prev_a, prev_b, (tip_x, tip_y)])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["bone_light"], [
                prev_a,
                (int((prev_a[0] + tip_x) / 2), int((prev_a[1] + tip_y) / 2)),
                (tip_x, tip_y),
            ])
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_shine"],
                             (tip_x, tip_y, 1, 1))
    def _draw_skull_eyes(surface, cx, cy, facing, phase, action):
        """Two deep sockets with glowing toxic green eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_intensity = 1.5 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy
            # Deep socket
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                             (ex - 2, ey - 2, 5, 4))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["eye_socket"],
                             (ex - 2, ey - 2, 5, 4))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow"],
                             (ex - 1, ey - 1, 4, 3))
            # Glow halo
            for radius in range(6, 0, -1):
                alpha = _NS_morthyrax._alpha(100 * (6 - radius) / 6 * pulse * eye_intensity)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["eye_mid"], alpha),
                                        (ex, ey), radius)
            # Eye core (bright toxic green)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_skull_jaw(surface, cx, cy, facing, phase, mouth_open):
        """Skull jaw with sharp teeth."""
        jaw_y = cy
        if mouth_open > 0:
            # Open jaw cavity
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["shadow_deep"], [
                (cx - 5, jaw_y),
                (cx + 5, jaw_y),
                (cx + 4, jaw_y + int(mouth_open) + 1),
                (cx - 4, jaw_y + int(mouth_open) + 1),
            ])
            _NS_morthyrax._poly(surface, _NS_morthyrax.PALETTE["eye_socket"], [
                (cx - 4, jaw_y + 1),
                (cx + 4, jaw_y + 1),
                (cx + 3, jaw_y + int(mouth_open)),
                (cx - 3, jaw_y + int(mouth_open)),
            ])
            # Green glow inside mouth
            glow_r = int(2 + mouth_open * 0.3)
            for r in range(glow_r + 2, 0, -1):
                alpha = _NS_morthyrax._alpha(200 * (glow_r + 2 - r) / (glow_r + 2))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                        (cx, jaw_y + int(mouth_open * 0.6)), r)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_mid"],
                                    (cx, jaw_y + int(mouth_open * 0.6)),
                                    max(1, glow_r - 1))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_light"],
                             (cx, jaw_y + int(mouth_open * 0.6), 1, 1))
            # Upper teeth
            for i, x_off in enumerate((-4, -2, 0, 2, 4)):
                fang_x = cx + x_off
                fang_tip_y = jaw_y + int(mouth_open * 0.7)
                pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_dark"],
                                 (fang_x, jaw_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_light"],
                                 (fang_x, fang_tip_y, 1, 1))
            # Lower teeth
            for i, x_off in enumerate((-3, -1, 1, 3)):
                fang_x = cx + x_off
                fang_bot_y = jaw_y + int(mouth_open)
                fang_top_y = fang_bot_y - 2
                pygame.draw.line(surface, _NS_morthyrax.PALETTE["bone_dark"],
                                 (fang_x, fang_bot_y), (fang_x, fang_top_y), 1)
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_mid"],
                                 (fang_x, fang_top_y, 1, 1))
        else:
            # Closed jaw - grinning teeth
            teeth_y = jaw_y
            for i, x_off in enumerate((-4, -2, 0, 2, 4)):
                fang_x = cx + x_off
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["shadow_deep"],
                                 (fang_x, teeth_y, 1, 3))
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_mid"],
                                 (fang_x, teeth_y, 1, 2))
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["bone_light"],
                                 (fang_x, teeth_y, 1, 1))
    # ============================================================
    # MELEE CLAW SWING
    # ============================================================
    def _draw_claw_swing(surface, boss, x, y, progress):
        """Green necrotic slash arc during melee attack."""
        if progress < 0.4 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.45
        t = min(1.0, max(0.0, t))
        center_x = x + facing * 8
        center_y = y - 4
        radius = 22 + int(t * 10)
        start_angle = -0.9 + t * 0.4
        end_angle = 0.9 - (1 - t) * 0.4
        # Multiple slash arcs (3 claw marks)
        num_slashes = 3
        for slash_i in range(num_slashes):
            offset_angle = (slash_i - 1) * 0.15
            for sub in range(5):
                slash_t = sub / 4
                angle = start_angle + (end_angle - start_angle) * slash_t + offset_angle
                slash_inner_x = center_x + int(math.cos(angle) * (radius - 10)) * facing
                slash_inner_y = center_y + int(math.sin(angle) * (radius - 10))
                slash_outer_x = center_x + int(math.cos(angle) * (radius + 4)) * facing
                slash_outer_y = center_y + int(math.sin(angle) * (radius + 4))
                alpha = _NS_morthyrax._alpha(220 * (1 - t * 0.5))
                pygame.draw.line(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_darkest"], alpha),
                                 (slash_inner_x, slash_inner_y),
                                 (slash_outer_x, slash_outer_y), 3)
                pygame.draw.line(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                 (slash_inner_x, slash_inner_y),
                                 (slash_outer_x, slash_outer_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                 (slash_inner_x, slash_inner_y),
                                 (slash_outer_x, slash_outer_y), 1)
                pygame.draw.rect(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                 (slash_outer_x, slash_outer_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_shine"], alpha),
                                 (slash_outer_x, slash_outer_y, 1, 1))
        # Rotting particles fly out
        for i in range(10):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 9)
            drop_dist = radius + 8 + int(t * 14)
            drop_x = center_x + int(math.cos(drop_angle) * drop_dist) * facing
            drop_y = center_y + int(math.sin(drop_angle) * drop_dist)
            alpha = _NS_morthyrax._alpha(220 * (1 - t))
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["flesh_dark"], alpha),
                             (drop_x, drop_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                             (drop_x, drop_y, 1, 1))
    # ============================================================
    # PLAGUE MIST (ambient)
    # ============================================================
    def _draw_plague_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(36, 3, -3):
            alpha = _NS_morthyrax._alpha((36 - radius) * 2.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_morthyrax.PALETTE["toxic_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_morthyrax._alpha((24 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising toxic bubbles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_morthyrax._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                    (sx, sy), 3)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                    (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["toxic_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Soul wisps (souls escaping)
        for i in range(5):
            wisp_t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx - 20 + i * 10 + int(math.sin(phase * 1.5 + i) * 5)
            wy = cy + 8 - int(wisp_t * 22)
            alpha = _NS_morthyrax._alpha(200 * (1 - wisp_t) * strength)
            if alpha > 0:
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_shine"],
                                 (wx, wy, 1, 1))
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_morthyrax._alpha(150 - i * 22)
                if alpha <= 0:
                    continue
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 110 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (2, 5, 2, 170), (10, 8, 110, 10))
        pygame.draw.ellipse(shadow, (15, 40, 10, 110), (18, 10, 94, 6))
        surface.blit(shadow, (x - 65, y - 12 + hover_offset))
    def _draw_death_aura(surface, x, y, phase):
        """Massive toxic death aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((230, 190), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_morthyrax._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morthyrax._aacircle(aura,
                                        (*_NS_morthyrax.PALETTE["toxic_darkest"], alpha),
                                        (115, 95), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_morthyrax._alpha((65 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morthyrax._aacircle(aura,
                                        (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                        (115, 95), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_morthyrax._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_morthyrax._aacircle(aura,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                        (115, 95), radius)
        surface.blit(aura, (x - 115, y - 95))
        # Floating soul wisps
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Rune circle on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morthyrax.PALETTE["toxic_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_morthyrax.PALETTE["toxic_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_morthyrax.PALETTE["toxic_mid"], 200),
                            (25, 22, 120, 18), 1)
        # Necromancy runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morthyrax.PALETTE["toxic_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_morthyrax.PALETTE["toxic_hot"],
                                 _NS_morthyrax._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: DECAY (projectile with slow effect)
    # ============================================================
    def _draw_decay_foreground(surface, boss, x, y, timer, phase):
        """Green decaying projectile from hand to target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morthyrax._target_position(boss, x, y)
        if progress < 0.25:
            # Charge in hand
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 6
            cr = int(3 + t * 7)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_morthyrax._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_darkest"], alpha),
                                        (hand_x, hand_y), r)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_dark"],
                                    (hand_x, hand_y), cr - 1)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_mid"],
                                    (hand_x, hand_y), max(1, cr - 3))
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_light"],
                                    (hand_x, hand_y), max(1, cr - 4))
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_shine"],
                             (hand_x, hand_y, 1, 1))
        else:
            # Projectile flies
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 24
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Trail (skull-shaped particles)
            for i in range(9):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_morthyrax._alpha(240 - i * 25)
                size = max(1, 7 - i)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_darkest"], alpha),
                                        (px, py), size)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                        (px, py), max(1, size - 3))
                if i < 4:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                        pygame.draw.rect(surface,
                                         (*_NS_morthyrax.PALETTE["toxic_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Head
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_darkest"], (bx, by), 8)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_dark"], (bx, by), 6)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_mid"], (bx, by), 4)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_light"], (bx, by), 3)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_hot"], (bx, by), 2)
            _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_morthyrax.PALETTE["white"], (bx, by, 1, 1))
            for r in range(12, 3, -2):
                alpha = _NS_morthyrax._alpha(80 * (12 - r) / 12)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                        (bx, by), r)
            # Impact + lingering DoT cloud
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(10 + st * 22)
                alpha = _NS_morthyrax._alpha(240 * (1 - st))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], alpha),
                                        (tx, ty), max(1, radius - 5), 2)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                        (tx, ty), max(1, radius - 10), 1)
                # Rising rot particles
                for i in range(8):
                    rise_t = (phase * 2 + i * 0.15) % 1.0
                    rx = tx + int(math.sin(i) * 12)
                    ry = ty - int(rise_t * 20)
                    alpha_r = _NS_morthyrax._alpha(200 * (1 - rise_t))
                    pygame.draw.rect(surface,
                                     (*_NS_morthyrax.PALETTE["toxic_mid"], alpha_r),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_morthyrax.PALETTE["toxic_hot"], alpha_r),
                                     (rx, ry, 1, 1))
    # ============================================================
    # SKILL W: SOUL RIP (drain beam)
    # ============================================================
    def _draw_soulrip_foreground(surface, boss, x, y, timer, phase):
        """Continuous green soul drain beam from hand to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morthyrax._target_position(boss, x, y)
        # Hand position
        hand_x = x + facing * 22
        hand_y = y - 6
        # Beam intensity waves
        intensity = math.sin(phase * 4) * 0.2 + 0.8
        # Draw multi-layer beam
        for layer_i, (width, color) in enumerate([
            (7, _NS_morthyrax.PALETTE["toxic_darkest"]),
            (5, _NS_morthyrax.PALETTE["toxic_dark"]),
            (3, _NS_morthyrax.PALETTE["toxic_mid"]),
            (2, _NS_morthyrax.PALETTE["toxic_light"]),
            (1, _NS_morthyrax.PALETTE["toxic_shine"]),
        ]):
            alpha = _NS_morthyrax._alpha(230 * intensity)
            pygame.draw.line(surface, (*color, alpha),
                             (hand_x, hand_y), (tx, ty), width)
        # Wavy energy along beam
        beam_len = math.hypot(tx - hand_x, ty - hand_y)
        if beam_len > 5:
            dx = (tx - hand_x) / beam_len
            dy = (ty - hand_y) / beam_len
            perp_x = -dy
            perp_y = dx
            # Wave particles
            for i in range(int(beam_len / 6)):
                seg_dist = i * 6
                sx = int(hand_x + dx * seg_dist)
                sy = int(hand_y + dy * seg_dist)
                wave = math.sin(phase * 6 + i * 0.5) * 4
                sx += int(perp_x * wave)
                sy += int(perp_y * wave)
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_hot"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_shine"],
                                 (sx, sy, 1, 1))
            # Soul particles traveling BACK to boss (draining)
            for i in range(8):
                soul_t = (phase * 0.8 + i * 0.125) % 1.0
                sx = int(tx + (hand_x - tx) * soul_t)
                sy = int(ty + (hand_y - ty) * soul_t)
                # Slight arc
                sy -= int(math.sin(soul_t * math.pi) * 6)
                alpha_s = _NS_morthyrax._alpha(240 * (1 - soul_t * 0.3))
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_dark"], alpha_s),
                                        (sx, sy), 3)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_light"], alpha_s),
                                        (sx, sy), 2)
                pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_shine"],
                                 (sx, sy, 1, 1))
        # Origin glow at hand
        for r in range(8, 0, -1):
            alpha = _NS_morthyrax._alpha(150 * (8 - r) / 8 * intensity)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_light"], alpha),
                                    (hand_x, hand_y), r)
        # Target drain glow
        for r in range(10, 0, -1):
            alpha = _NS_morthyrax._alpha(140 * (10 - r) / 10 * intensity)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_dark"], alpha),
                                    (tx, ty), r)
        _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_mid"], (tx, ty), 4)
        _NS_morthyrax._aacircle(surface, _NS_morthyrax.PALETTE["toxic_hot"], (tx, ty), 2)
    # ============================================================
    # SKILL E: TOMBSTONE (summon)
    # ============================================================
    def _draw_tombstone_ground(surface, boss, x, y, timer, phase):
        """Circle on ground around tombstone."""
        tx, ty = _NS_morthyrax._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(35 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_morthyrax.PALETTE["toxic_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_morthyrax.PALETTE["toxic_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_morthyrax.PALETTE["toxic_mid"], 130),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_tombstone_foreground(surface, boss, x, y, timer, phase):
        """Green glowing tombstone at target."""
        tx, ty = _NS_morthyrax._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Rising from ground
            t = progress / 0.25
            _NS_morthyrax._draw_tombstone(surface, tx, ty, phase, t)
        else:
            # Fully formed
            _NS_morthyrax._draw_tombstone(surface, tx, ty, phase, 1.0)
            # Zombie hands rising periodically
            zombie_phase = (progress - 0.25) / 0.75
            for i in range(4):
                spawn_t = (zombie_phase * 2 + i * 0.25) % 1.0
                if spawn_t > 0.7:
                    continue
                zx = tx + int(math.cos(i * math.pi / 2) * 20)
                zy = ty + int(math.sin(i * math.pi / 2) * 8) - int(spawn_t * 10)
                alpha_z = _NS_morthyrax._alpha(200 * (1 - spawn_t / 0.7))
                # Simple zombie hand (small claw)
                pygame.draw.rect(surface,
                                 (*_NS_morthyrax.PALETTE["flesh_darkest"], alpha_z),
                                 (zx - 2, zy, 4, 3))
                pygame.draw.rect(surface,
                                 (*_NS_morthyrax.PALETTE["flesh_dark"], alpha_z),
                                 (zx - 1, zy, 3, 2))
                # Fingers
                for fx_off in (-1, 0, 1):
                    pygame.draw.line(surface,
                                     (*_NS_morthyrax.PALETTE["bone_dark"], alpha_z),
                                     (zx + fx_off, zy),
                                     (zx + fx_off, zy - 2), 1)
    def _draw_tombstone(surface, tx, ty, phase, form_progress):
        """Green glowing tombstone."""
        alpha_base = int(255 * min(1.0, form_progress * 1.5))
        h = int(28 * form_progress)
        base_y = ty
        top_y = ty - h
        # Base (wider bottom)
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["shadow_deep"], alpha_base), [
            (tx - 10, base_y + 2),
            (tx + 10, base_y + 2),
            (tx + 8, base_y - 2),
            (tx - 8, base_y - 2),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["bone_darkest"], alpha_base), [
            (tx - 10, base_y),
            (tx + 10, base_y),
            (tx + 8, base_y - 4),
            (tx - 8, base_y - 4),
        ])
        # Tombstone body
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["shadow_deep"], alpha_base), [
            (tx - 8, base_y - 2),
            (tx + 8, base_y - 2),
            (tx + 8, top_y + 6),
            (tx + 6, top_y + 2),
            (tx + 4, top_y),
            (tx - 4, top_y),
            (tx - 6, top_y + 2),
            (tx - 8, top_y + 6),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["bone_darkest"], alpha_base), [
            (tx - 7, base_y - 3),
            (tx + 7, base_y - 3),
            (tx + 7, top_y + 5),
            (tx + 5, top_y + 1),
            (tx + 3, top_y - 1),
            (tx - 3, top_y - 1),
            (tx - 5, top_y + 1),
            (tx - 7, top_y + 5),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["bone_dark"], alpha_base), [
            (tx - 6, base_y - 4),
            (tx + 6, base_y - 4),
            (tx + 6, top_y + 5),
            (tx + 4, top_y + 1),
            (tx + 2, top_y - 1),
            (tx - 2, top_y - 1),
            (tx - 4, top_y + 1),
            (tx - 6, top_y + 5),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["bone_mid"], alpha_base), [
            (tx - 4, base_y - 6),
            (tx + 4, base_y - 6),
            (tx + 4, top_y + 3),
            (tx + 2, top_y),
            (tx - 2, top_y),
            (tx - 4, top_y + 3),
        ])
        # Green cross carved into tombstone (glowing)
        cross_center_y = ty - h // 2
        pulse = math.sin(phase * 2) * 0.4 + 0.6
        cross_alpha = _NS_morthyrax._alpha(220 * pulse * form_progress)
        pygame.draw.line(surface,
                         (*_NS_morthyrax.PALETTE["toxic_dark"], cross_alpha),
                         (tx, cross_center_y - 4),
                         (tx, cross_center_y + 4), 2)
        pygame.draw.line(surface,
                         (*_NS_morthyrax.PALETTE["toxic_light"], cross_alpha),
                         (tx, cross_center_y - 4),
                         (tx, cross_center_y + 4), 1)
        pygame.draw.line(surface,
                         (*_NS_morthyrax.PALETTE["toxic_dark"], cross_alpha),
                         (tx - 3, cross_center_y - 1),
                         (tx + 3, cross_center_y - 1), 2)
        pygame.draw.line(surface,
                         (*_NS_morthyrax.PALETTE["toxic_light"], cross_alpha),
                         (tx - 3, cross_center_y - 1),
                         (tx + 3, cross_center_y - 1), 1)
        pygame.draw.rect(surface,
                         (*_NS_morthyrax.PALETTE["toxic_shine"], cross_alpha),
                         (tx, cross_center_y - 1, 1, 1))
        # Glow aura around tombstone
        aura_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(18, 3, -3):
            aura_alpha = _NS_morthyrax._alpha(80 * (18 - r) / 18 * aura_pulse * form_progress)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_mid"], aura_alpha),
                                    (tx, ty - h // 2), r)
    # ============================================================
    # SKILL R: FLESH GOLEM (transform target)
    # ============================================================
    def _draw_fleshgolem_ground(surface, boss, x, y, timer, phase):
        """Circle at target location during transformation."""
        tx, ty = _NS_morthyrax._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_morthyrax.PALETTE["toxic_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_morthyrax.PALETTE["toxic_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_morthyrax.PALETTE["gore_mid"], 150),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Necromancy pentagram lines
            for i in range(5):
                angle = phase * 0.3 + i * math.pi * 2 / 5
                x1 = tx + int(math.cos(angle) * r)
                y1 = ty + int(math.sin(angle) * r * 0.4)
                x2 = tx + int(math.cos(angle + math.pi * 4 / 5) * r)
                y2 = ty + int(math.sin(angle + math.pi * 4 / 5) * r * 0.4)
                pygame.draw.line(surface, _NS_morthyrax.PALETTE["toxic_light"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_fleshgolem_foreground(surface, boss, x, y, timer, phase):
        """Beam from boss + growing flesh golem at target."""
        facing = boss.direction
        tx, ty = _NS_morthyrax._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Beam from boss hand to target during first half
        hand_x = x + facing * 22
        hand_y = y - 6
        if progress < 0.5:
            # Transformation beam (thick, chaotic)
            t = progress / 0.5
            beam_intensity = math.sin(phase * 5) * 0.2 + 0.8
            for layer_i, (width, color) in enumerate([
                (10, _NS_morthyrax.PALETTE["gore_dark"]),
                (7, _NS_morthyrax.PALETTE["toxic_darkest"]),
                (5, _NS_morthyrax.PALETTE["toxic_dark"]),
                (3, _NS_morthyrax.PALETTE["toxic_mid"]),
                (1, _NS_morthyrax.PALETTE["toxic_shine"]),
            ]):
                alpha = _NS_morthyrax._alpha(230 * beam_intensity)
                pygame.draw.line(surface, (*color, alpha),
                                 (hand_x, hand_y), (tx, ty), width)
            # Sparks
            beam_len = math.hypot(tx - hand_x, ty - hand_y)
            if beam_len > 5:
                dx = (tx - hand_x) / beam_len
                dy = (ty - hand_y) / beam_len
                perp_x = -dy
                perp_y = dx
                for i in range(int(beam_len / 5)):
                    seg_dist = i * 5
                    sx = int(hand_x + dx * seg_dist)
                    sy = int(hand_y + dy * seg_dist)
                    wave = math.sin(phase * 8 + i) * 5
                    sx += int(perp_x * wave)
                    sy += int(perp_y * wave)
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["toxic_hot"],
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, _NS_morthyrax.PALETTE["gore_light"],
                                     (sx, sy, 1, 1))
        else:
            # Golem forms and stands
            t = (progress - 0.5) / 0.5
            _NS_morthyrax._draw_flesh_golem(surface, tx, ty, phase, t)
    def _draw_flesh_golem(surface, gx, gy, phase, form_progress):
        """Big hulking flesh golem."""
        alpha_base = int(255 * min(1.0, form_progress * 1.5))
        size_mult = min(1.0, form_progress * 1.5)
        # Body (fat/hulking)
        body_h = int(30 * size_mult)
        body_w = int(16 * size_mult)
        # Base body oval
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["shadow_deep"], alpha_base), [
            (gx - body_w, gy - body_h + 8),
            (gx - body_w - 2, gy - body_h // 2),
            (gx - body_w, gy),
            (gx + body_w, gy),
            (gx + body_w + 2, gy - body_h // 2),
            (gx + body_w, gy - body_h + 8),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["flesh_darkest"], alpha_base), [
            (gx - body_w + 1, gy - body_h + 8),
            (gx - body_w - 1, gy - body_h // 2),
            (gx - body_w + 1, gy - 1),
            (gx + body_w - 1, gy - 1),
            (gx + body_w + 1, gy - body_h // 2),
            (gx + body_w - 1, gy - body_h + 8),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["flesh_dark"], alpha_base), [
            (gx - body_w + 2, gy - body_h + 8),
            (gx - body_w, gy - body_h // 2),
            (gx - body_w + 2, gy - 2),
            (gx + body_w - 2, gy - 2),
            (gx + body_w, gy - body_h // 2),
            (gx + body_w - 2, gy - body_h + 8),
        ])
        _NS_morthyrax._poly(surface,
                            (*_NS_morthyrax.PALETTE["flesh_mid"], alpha_base), [
            (gx - body_w + 4, gy - body_h + 10),
            (gx - body_w + 2, gy - body_h // 2),
            (gx - body_w + 4, gy - 4),
            (gx + body_w - 4, gy - 4),
            (gx + body_w - 2, gy - body_h // 2),
            (gx + body_w - 4, gy - body_h + 10),
        ])
        # Green glowing wounds
        for wx_off, wy_off in [(-6, -14), (4, -18), (-2, -8), (6, -12)]:
            wpulse = math.sin(phase * 2 + wx_off) * 0.4 + 0.6
            walpha = _NS_morthyrax._alpha(200 * wpulse * form_progress)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_mid"], walpha),
                                    (gx + wx_off, gy + wy_off), 3)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["toxic_light"], walpha),
                                    (gx + wx_off, gy + wy_off), 2)
            pygame.draw.rect(surface,
                             (*_NS_morthyrax.PALETTE["toxic_shine"], walpha),
                             (gx + wx_off, gy + wy_off, 1, 1))
        # Small angry head on top
        head_y = gy - body_h + 4
        _NS_morthyrax._aacircle(surface,
                                (*_NS_morthyrax.PALETTE["shadow_deep"], alpha_base),
                                (gx, head_y), 5)
        _NS_morthyrax._aacircle(surface,
                                (*_NS_morthyrax.PALETTE["flesh_darkest"], alpha_base),
                                (gx, head_y), 5)
        _NS_morthyrax._aacircle(surface,
                                (*_NS_morthyrax.PALETTE["flesh_dark"], alpha_base),
                                (gx, head_y), 4)
        _NS_morthyrax._aacircle(surface,
                                (*_NS_morthyrax.PALETTE["flesh_mid"], alpha_base),
                                (gx - 1, head_y - 1), 3)
        # Glowing angry eyes
        pygame.draw.rect(surface,
                         (*_NS_morthyrax.PALETTE["toxic_light"], alpha_base),
                         (gx - 2, head_y, 1, 1))
        pygame.draw.rect(surface,
                         (*_NS_morthyrax.PALETTE["toxic_shine"], alpha_base),
                         (gx + 2, head_y, 1, 1))
        # Big fists at sides
        for side in (-1, 1):
            fist_x = gx + side * (body_w + 3)
            fist_y = gy - 4
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["shadow_deep"], alpha_base),
                                    (fist_x, fist_y), 4)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["flesh_darkest"], alpha_base),
                                    (fist_x, fist_y), 4)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["flesh_dark"], alpha_base),
                                    (fist_x, fist_y), 3)
            _NS_morthyrax._aacircle(surface,
                                    (*_NS_morthyrax.PALETTE["flesh_mid"], alpha_base),
                                    (fist_x - side, fist_y - 1), 2)
        # Green aura around golem
        if form_progress < 0.7:
            aura_alpha = _NS_morthyrax._alpha(200 * (1 - form_progress / 0.7))
            for r in range(25, 3, -3):
                a = _NS_morthyrax._alpha(aura_alpha * (25 - r) / 25)
                _NS_morthyrax._aacircle(surface,
                                        (*_NS_morthyrax.PALETTE["toxic_mid"], a),
                                        (gx, gy - body_h // 2), r)



# ====================================================================
# SANGUIVETH (BLOODBOUND FAMINE) - Mini Boss
# ====================================================================

class _NS_sanguiveth:
    """Namespace sanguiveth - vampiric hunger mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Pale vampire skin
        "skin_darkest": (55, 45, 55),
        "skin_dark": (110, 95, 110),
        "skin_mid": (170, 155, 170),
        "skin_light": (215, 200, 215),
        "skin_shine": (240, 230, 235),
        # Silver-white hair
        "hair_darkest": (60, 55, 70),
        "hair_dark": (120, 115, 135),
        "hair_mid": (180, 175, 195),
        "hair_light": (225, 220, 235),
        "hair_shine": (250, 248, 255),
        # Dark leather armor
        "leather_darkest": (10, 5, 8),
        "leather_dark": (30, 18, 22),
        "leather_mid": (60, 40, 45),
        "leather_light": (95, 70, 75),
        "leather_edge": (130, 100, 105),
        # Crimson blood red (main theme)
        "blood_darkest": (35, 3, 8),
        "blood_dark": (90, 10, 20),
        "blood_mid": (170, 20, 40),
        "blood_light": (230, 40, 65),
        "blood_hot": (255, 90, 110),
        "blood_shine": (255, 180, 190),
        # Red glowing eyes
        "eye_socket": (8, 2, 4),
        "eye_dark": (100, 10, 20),
        "eye_mid": (220, 30, 45),
        "eye_light": (255, 100, 100),
        "eye_glow": (255, 200, 180),
        # Bone white (fangs, wing bones, claws)
        "bone_dark": (90, 75, 65),
        "bone_mid": (180, 165, 145),
        "bone_light": (235, 225, 205),
        "bone_shine": (255, 250, 235),
        # Wing membrane (dark crimson translucent)
        "membrane_dark": (25, 5, 12),
        "membrane_mid": (75, 15, 25),
        "membrane_light": (140, 30, 50),
        "membrane_glow": (210, 60, 80),
        # Blood mist
        "mist_dark": (30, 5, 10),
        "mist_mid": (95, 15, 25),
        "mist_light": (180, 40, 60),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sanguiveth._clamp(color)
        if _NS_sanguiveth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_sanguiveth._clamp(color)
        if _NS_sanguiveth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_sanguiveth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_sanguiveth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sanguiveth._detect_moving(boss)
        _NS_sanguiveth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_sng_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_sanguiveth._draw_blood_aura(surface, x, y, pulse)
        _NS_sanguiveth._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_sanguiveth._draw_ripandtear_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sanguiveth._draw_certaindeath_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sanguiveth._draw_headbutt_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — always floating
        if attacking:
            _NS_sanguiveth._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_sanguiveth._draw_float_move(surface, boss, x, y)
        else:
            _NS_sanguiveth._draw_float_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_sanguiveth._draw_bloodfeast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sanguiveth._draw_ripandtear_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sanguiveth._draw_headbutt_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sanguiveth._draw_certaindeath_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sng_previous_timer", 0))
        active = bool(getattr(boss, "_sng_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._sng_attack_active = True
            boss._sng_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._sng_attack_frame = int(getattr(boss, "_sng_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._sng_attack_active = False
            boss._sng_attack_frame = 0
            active = False
        boss._sng_previous_timer = timer
        boss._sng_attack_progress = (
            min(1.0, getattr(boss, "_sng_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_sng_last_x"):
            boss._sng_last_x = boss.x
            boss._sng_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sng_last_x)
        dy = abs(boss.y - boss._sng_last_y)
        boss._sng_last_x = boss.x
        boss._sng_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        # Floating: constant hover with slow bob
        hover = int(math.sin(boss.pulse * 0.8) * 5) - 6
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_sanguiveth._draw_float_shadow(surface, x + sway, y + 50, boss.pulse)
        _NS_sanguiveth._draw_blood_mist(surface, x + sway, y + 34, boss.pulse)
        _NS_sanguiveth._draw_body(surface, x + sway, y + hover,
                                  boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        # Floating movement: wider bob and tilt
        hover = int(math.sin(phase * 0.9) * 6) - 7
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_sanguiveth._draw_float_shadow(surface, x + sway, y + 50, phase)
        _NS_sanguiveth._draw_blood_mist(surface, x + sway, y + 34, phase,
                                        trail=True, facing=boss.direction)
        _NS_sanguiveth._draw_body(surface, x + sway, y + hover,
                                  boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_sng_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # MELEE SWING: wind up → swing → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction  # pull back
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 18)) * boss.direction  # forward swing
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(13 * (1 - t)) * boss.direction
            lift = int(-2 + t * 4)
        hover = int(math.sin(boss.pulse * 0.8) * 3) - 4
        _NS_sanguiveth._draw_float_shadow(surface, x + lunge, y + 50, boss.pulse)
        _NS_sanguiveth._draw_blood_mist(surface, x + lunge, y + 34,
                                        boss.pulse, intense=True)
        _NS_sanguiveth._draw_body(surface, x + lunge, y + hover - lift,
                                  boss.direction, boss.pulse,
                                  "attack", progress)
        _NS_sanguiveth._draw_claw_swing(surface, boss, x + lunge,
                                        y + hover - lift, progress)
    # ============================================================
    # BODY - Vampire female figure
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw floating vampire body."""
        # Wings first (behind body)
        _NS_sanguiveth._draw_bone_wings(surface, cx, cy - 8, facing, phase, action,
                                        attack_progress)
        # Torso + hips (main body)
        _NS_sanguiveth._draw_torso(surface, cx, cy, facing, phase)
        # Legs (dangling because floating)
        _NS_sanguiveth._draw_legs(surface, cx, cy + 8, facing, phase, action)
        # Arms
        _NS_sanguiveth._draw_arms(surface, cx, cy - 2, facing, phase, action,
                                  attack_progress)
        # Head + hair
        _NS_sanguiveth._draw_head(surface, cx, cy - 18, facing, phase, action,
                                  attack_progress)
    def _draw_bone_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Two bone-and-membrane wings spreading behind."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 1.4) * 4
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),
            (1, 0.75, 0.8),
        ]):
            base_x = cx - facing * 2
            base_y = cy
            spar1_len = int(30 * size_mult)
            spar1_angle = math.pi * 0.6 * side_mult - math.radians(beat)
            spar2_len = int(34 * size_mult)
            spar2_angle = math.pi * 0.8 * side_mult - math.radians(beat * 0.8)
            spar3_len = int(28 * size_mult)
            spar3_angle = math.pi * 1.0 * side_mult - math.radians(beat * 0.5)
            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)
            membrane_points = [
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
            wing_surf = pygame.Surface((180, 110), pygame.SRCALPHA)
            offset_x = base_x - 90
            offset_y = base_y - 55
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in membrane_points]
            # Membrane fill (dark crimson translucent)
            _NS_sanguiveth._poly(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["membrane_dark"],
                                  int(210 * alpha_mult)),
                                 local_points)
            # Inner darker
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_local * 0.18),
                     int(p[1] * 0.82 + cy_local * 0.18))
                )
            _NS_sanguiveth._poly(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["membrane_mid"],
                                  int(180 * alpha_mult)),
                                 inner_pts)
            # Glowing membrane veins
            _NS_sanguiveth._poly(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_dark"],
                                  int(120 * alpha_mult)),
                                 inner_pts)
            # BONE spars (white bone with dark outline)
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                pygame.draw.line(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["shadow_deep"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 4)
                pygame.draw.line(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["bone_dark"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["bone_mid"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["bone_light"],
                                  int(220 * alpha_mult)),
                                 bone_base, tip, 1)
                # Sharp claw at wing tip
                _NS_sanguiveth._aacircle(wing_surf,
                                         (*_NS_sanguiveth.PALETTE["shadow_deep"],
                                          int(240 * alpha_mult)),
                                         tip, 3)
                _NS_sanguiveth._aacircle(wing_surf,
                                         (*_NS_sanguiveth.PALETTE["bone_light"],
                                          int(240 * alpha_mult)),
                                         tip, 2)
                pygame.draw.rect(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_light"],
                                  int(220 * alpha_mult)),
                                 (tip[0], tip[1], 1, 1))
            # Blood drips from wing edges
            for i, tip in enumerate([(tip1_x - offset_x, tip1_y - offset_y),
                                     (tip3_x - offset_x, tip3_y - offset_y)]):
                drip_t = (phase * 0.4 + i * 0.5) % 1.0
                drip_y = tip[1] + int(drip_t * 12)
                drip_alpha = _NS_sanguiveth._alpha(200 * (1 - drip_t) * alpha_mult)
                pygame.draw.rect(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_dark"], drip_alpha),
                                 (tip[0], drip_y, 1, 2))
                pygame.draw.rect(wing_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_light"], drip_alpha),
                                 (tip[0], drip_y, 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Female torso with dark leather corset."""
        breath = math.sin(phase * 0.7) * 1
        # Chest/torso shape
        torso_pts = [
            (cx - 8, cy - 4),   # left shoulder
            (cx - 9, cy),       # left side
            (cx - 8, cy + 6),   # left waist
            (cx - 6, cy + 10),  # left hip
            (cx + 6, cy + 10),  # right hip
            (cx + 8, cy + 6),   # right waist
            (cx + 9, cy),       # right side
            (cx + 8, cy - 4),   # right shoulder
        ]
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        # Base skin (visible at neck, arms area)
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_dark"], torso_pts)
        # Dark leather corset (main body)
        corset_pts = [
            (cx - 8, cy - 2),
            (cx - 9, cy + 1),
            (cx - 8, cy + 6),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 8, cy + 6),
            (cx + 9, cy + 1),
            (cx + 8, cy - 2),
        ]
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["leather_darkest"], corset_pts)
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["leather_dark"], [
            (cx - 7, cy - 1),
            (cx - 8, cy + 1),
            (cx - 7, cy + 5),
            (cx - 4, cy + 8),
            (cx + 4, cy + 8),
            (cx + 7, cy + 5),
            (cx + 8, cy + 1),
            (cx + 7, cy - 1),
        ])
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["leather_mid"], [
            (cx - 6, cy),
            (cx - 7, cy + 2),
            (cx - 6, cy + 5),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 5),
            (cx + 7, cy + 2),
            (cx + 6, cy),
        ])
        # Highlight on corset
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["leather_light"],
                         (cx - 5, cy + 1), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["leather_light"],
                         (cx + 5, cy + 1), (cx + 5, cy + 6), 1)
        # Corset lacing (crimson threads)
        for i in range(3):
            ly = cy + 1 + i * 2
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                             (cx - 2, ly), (cx + 2, ly + 1), 1)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["blood_mid"],
                             (cx - 2, ly + 1), (cx + 2, ly), 1)
        # Skin cleavage/collar area
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 2, cy - 1),
            (cx - 2, cy - 1),
        ])
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 1, cy - 2),
            (cx - 1, cy - 2),
        ])
        # Belt at waist
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["leather_darkest"],
                         (cx - 7, cy + 7, 14, 2))
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["leather_light"],
                         (cx - 7, cy + 7, 14, 1))
        # Belt buckle
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                         (cx - 1, cy + 7, 2, 2))
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_light"],
                         (cx - 1, cy + 7, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Legs dangling because floating."""
        # Legs slightly swaying because of hover
        sway = math.sin(phase * 0.9) * 1.5
        for side in (-1, 1):
            leg_x_top = cx + side * 3
            leg_x_bot = cx + side * 4 + int(sway * side * 0.5)
            leg_y_top = cy
            leg_y_bot = cy + 14
            # Thigh (pale skin)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                             (leg_x_top + 1, leg_y_top + 1),
                             (leg_x_bot + 1, leg_y_bot + 1), 5)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_darkest"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 4)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_dark"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 3)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_mid"],
                             (leg_x_top - side, leg_y_top),
                             (leg_x_bot - side, leg_y_bot), 2)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_light"],
                             (leg_x_top - side, leg_y_top + 1),
                             (leg_x_bot - side, leg_y_bot - 1), 1)
            # Boots at bottom (dark leather with crimson trim)
            boot_x = leg_x_bot
            boot_y = leg_y_bot
            _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["shadow_deep"], [
                (boot_x - 3, boot_y - 1),
                (boot_x + 3, boot_y - 1),
                (boot_x + 4, boot_y + 3),
                (boot_x - 4, boot_y + 3),
            ])
            _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["leather_darkest"], [
                (boot_x - 3, boot_y - 2),
                (boot_x + 3, boot_y - 2),
                (boot_x + 3, boot_y + 2),
                (boot_x - 3, boot_y + 2),
            ])
            _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["leather_dark"], [
                (boot_x - 2, boot_y - 2),
                (boot_x + 2, boot_y - 2),
                (boot_x + 2, boot_y + 1),
                (boot_x - 2, boot_y + 1),
            ])
            # Boot highlight
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["leather_edge"],
                             (boot_x - 2, boot_y - 2, 4, 1))
            # Crimson trim
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                             (boot_x - 3, boot_y - 1),
                             (boot_x + 3, boot_y - 1), 1)
            # Knee shadow
            knee_y = leg_y_top + 7
            knee_x = leg_x_top + int((leg_x_bot - leg_x_top) * 0.5)
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["skin_darkest"],
                             (knee_x, knee_y, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Arms — one holds slightly ready, one at side."""
        # Both arms visible in profile
        # BACK arm (behind body)
        back_shoulder_x = cx - facing * 4
        back_shoulder_y = cy - 2
        # FRONT arm (near viewer - the "claw" arm)
        front_shoulder_x = cx + facing * 4
        front_shoulder_y = cy - 2
        # Attack: front arm swings forward with claws
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.3 * t  # pull back
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.3 + math.pi * 0.9 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.6 * (1 - t) - math.pi * 0.1 * t
        else:
            arm_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.1
        # BACK arm (simpler, hanging)
        back_hand_x = back_shoulder_x - facing * 3
        back_hand_y = back_shoulder_y + 10
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 4)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (back_hand_x, back_hand_y), 2)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_mid"],
                         (back_shoulder_x - 1, back_shoulder_y),
                         (back_hand_x - 1, back_hand_y), 1)
        # Back hand claws
        for i in range(3):
            claw_x = back_hand_x - facing * i
            claw_y = back_hand_y + 2
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                             (claw_x, claw_y, 1, 2))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["bone_dark"],
                             (claw_x, claw_y, 1, 1))
        # FRONT arm (main claw arm)
        arm_length = 12
        front_hand_x = front_shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        front_hand_y = front_shoulder_y + int(math.sin(arm_angle) * arm_length) + 4
        # Upper arm
        elbow_x = front_shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = front_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 2
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                         (front_shoulder_x + 1, front_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_darkest"],
                         (front_shoulder_x, front_shoulder_y),
                         (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_dark"],
                         (front_shoulder_x, front_shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_mid"],
                         (front_shoulder_x - 1, front_shoulder_y),
                         (elbow_x - 1, elbow_y), 2)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_light"],
                         (front_shoulder_x - 1, front_shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Forearm
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (front_hand_x + 1, front_hand_y + 1), 5)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y),
                         (front_hand_x, front_hand_y), 4)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_dark"],
                         (elbow_x, elbow_y),
                         (front_hand_x, front_hand_y), 3)
        pygame.draw.line(surface, _NS_sanguiveth.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y),
                         (front_hand_x - 1, front_hand_y), 2)
        # Wristband (leather bracer)
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["leather_darkest"],
                         (front_hand_x - 2, front_hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["leather_dark"],
                         (front_hand_x - 2, front_hand_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                         (front_hand_x - 2, front_hand_y - 1, 4, 1))
        # LONG CLAWS on front hand
        for i in range(4):
            angle_offset = arm_angle + math.pi * 0.15 - i * math.pi * 0.08
            claw_len = 6
            claw_tip_x = front_hand_x + int(math.cos(angle_offset) * claw_len) * facing
            claw_tip_y = front_hand_y + int(math.sin(angle_offset) * claw_len) + 2
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                             (front_hand_x + 1, front_hand_y + 1),
                             (claw_tip_x + 1, claw_tip_y + 1), 3)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["bone_dark"],
                             (front_hand_x, front_hand_y),
                             (claw_tip_x, claw_tip_y), 2)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["bone_light"],
                             (front_hand_x, front_hand_y),
                             (claw_tip_x, claw_tip_y), 1)
            # Blood tip
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_light"],
                             (claw_tip_x, claw_tip_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Vampire head with long silver hair, red eyes, fangs."""
        # Head shape (oval)
        head_pts = [
            (cx - 6, cy),
            (cx - 7, cy - 3),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 3, cy - 9),
            (cx + 6, cy - 6),
            (cx + 7, cy - 2),
            (cx + 6 * facing + 2, cy + 3),
            (cx + 2, cy + 5),
            (cx - 3, cy + 4),
            (cx - 6, cy + 1),
        ]
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_pts])
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_darkest"], head_pts)
        # Face base (pale skin)
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 5, cy - 5),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 6, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 1, cy + 4),
            (cx - 3, cy + 3),
        ])
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 3, cy - 5),
            (cx, cy - 7),
            (cx + 3, cy - 7),
            (cx + 5, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx, cy + 3),
            (cx - 2, cy + 2),
        ])
        # Highlight cheeks
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["skin_light"], [
            (cx + 1, cy - 5),
            (cx + 3, cy - 5),
            (cx + 4, cy - 3),
            (cx + 2, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["skin_shine"],
                         (cx + 2 * facing, cy - 4, 1, 1))
        # LONG SILVER HAIR (behind + around head, flowing)
        _NS_sanguiveth._draw_hair(surface, cx, cy, facing, phase)
        # RED EYES (glowing)
        _NS_sanguiveth._draw_vampire_eyes(surface, cx, cy - 3, facing, phase)
        # Nose shadow
        pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["skin_darkest"],
                         (cx + 2 * facing, cy - 1, 1, 1))
        # MOUTH with FANGS
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 4)
        _NS_sanguiveth._draw_vampire_mouth(surface, cx, cy + 2, facing, phase, mouth_open)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Long silver hair flowing behind."""
        # Hair sway
        sway = math.sin(phase * 0.5) * 2
        # Hair behind head (bulk)
        hair_bulk = [
            (cx - 7, cy - 5),
            (cx - 9, cy - 3),
            (cx - 11, cy + 2),
            (cx - 12, cy + 8),
            (cx - 10, cy + 14 + int(sway)),
            (cx - 6, cy + 16 + int(sway)),
            (cx - 2, cy + 15 + int(sway * 0.7)),
            (cx + 3, cy + 12 + int(sway * 0.5)),
            (cx + 6, cy + 8),
            (cx + 7, cy + 3),
            (cx + 6, cy - 3),
            (cx + 3, cy - 8),
            (cx - 2, cy - 9),
            (cx - 6, cy - 7),
        ]
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in hair_bulk])
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["hair_darkest"], hair_bulk)
        # Hair mid tone
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["hair_dark"], [
            (cx - 6, cy - 4),
            (cx - 8, cy - 2),
            (cx - 10, cy + 3),
            (cx - 10, cy + 10),
            (cx - 7, cy + 13 + int(sway * 0.8)),
            (cx - 2, cy + 12 + int(sway * 0.6)),
            (cx + 3, cy + 10),
            (cx + 6, cy + 5),
            (cx + 6, cy - 1),
            (cx + 3, cy - 6),
            (cx - 2, cy - 7),
            (cx - 5, cy - 5),
        ])
        _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["hair_mid"], [
            (cx - 5, cy - 3),
            (cx - 8, cy),
            (cx - 9, cy + 5),
            (cx - 8, cy + 10),
            (cx - 3, cy + 10 + int(sway * 0.6)),
            (cx + 2, cy + 8),
            (cx + 5, cy + 3),
            (cx + 5, cy - 2),
            (cx + 1, cy - 5),
            (cx - 3, cy - 5),
        ])
        # Hair highlights (silver shine strands)
        for i, (x_off, y_off_start, length) in enumerate([
            (-6, -2, 8), (-3, -4, 10), (2, -5, 9), (5, -2, 7),
        ]):
            for dy in range(length):
                if dy % 3 == 0:
                    hx = cx + x_off + int(math.sin(phase * 0.3 + i) * 0.5)
                    hy = cy + y_off_start + dy
                    pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["hair_light"],
                                     (hx, hy, 1, 1))
                elif dy % 5 == 0:
                    hx = cx + x_off
                    hy = cy + y_off_start + dy
                    pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["hair_shine"],
                                     (hx, hy, 1, 1))
        # Hair bangs falling over forehead
        for i in range(5):
            bx = cx - 4 + i * 2
            by_top = cy - 8
            by_bot = cy - 4 + (i % 2)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["hair_darkest"],
                             (bx, by_top), (bx, by_bot), 1)
            pygame.draw.line(surface, _NS_sanguiveth.PALETTE["hair_dark"],
                             (bx + 1, by_top), (bx + 1, by_bot - 1), 1)
    def _draw_vampire_eyes(surface, cx, cy, facing, phase):
        """Two glowing red eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Both eyes visible (frontal-ish view for face)
        for eye_side in (-1, 1):
            ex = cx + eye_side * 2 + (1 if facing == 1 else -1)
            ey = cy
            # Socket shadow
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Red glow halo
            for radius in range(4, 0, -1):
                alpha = _NS_sanguiveth._alpha(80 * (4 - radius) / 4 * pulse)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["eye_mid"], alpha),
                                         (ex, ey), radius)
            # Eye core
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
    def _draw_vampire_mouth(surface, cx, cy, facing, phase, mouth_open):
        """Mouth with vampire fangs."""
        mouth_x = cx
        mouth_y = cy
        if mouth_open > 0:
            # Open mouth cavity (dark red)
            _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["shadow_deep"], [
                (mouth_x - 3, mouth_y),
                (mouth_x + 3, mouth_y),
                (mouth_x + 2, mouth_y + int(mouth_open)),
                (mouth_x - 2, mouth_y + int(mouth_open)),
            ])
            _NS_sanguiveth._poly(surface, _NS_sanguiveth.PALETTE["blood_darkest"], [
                (mouth_x - 2, mouth_y + 1),
                (mouth_x + 2, mouth_y + 1),
                (mouth_x + 1, mouth_y + int(mouth_open) - 1),
                (mouth_x - 1, mouth_y + int(mouth_open) - 1),
            ])
            # Tongue
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                             (mouth_x - 1, mouth_y + 1, 2, max(1, int(mouth_open) - 1)))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_mid"],
                             (mouth_x, mouth_y + 2, 1, max(1, int(mouth_open) - 2)))
            # UPPER FANGS (2 long)
            for x_off in (-2, 2):
                fang_x = mouth_x + x_off
                fang_tip_y = mouth_y + int(mouth_open * 0.9)
                pygame.draw.line(surface, _NS_sanguiveth.PALETTE["bone_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["bone_light"],
                                 (fang_x, fang_tip_y, 1, 1))
                # Blood drip
                if mouth_open > 2:
                    drip_y = fang_tip_y + 1
                    pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_mid"],
                                     (fang_x, drip_y, 1, 1))
                    pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_light"],
                                     (fang_x, drip_y, 1, 1))
        else:
            # Closed mouth line (with visible fang tips)
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_darkest"],
                             (mouth_x - 2, mouth_y, 4, 1))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                             (mouth_x - 1, mouth_y, 2, 1))
            # Fang tips peeking
            for x_off in (-2, 1):
                pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["bone_light"],
                                 (mouth_x + x_off, mouth_y + 1, 1, 1))
    # ============================================================
    # MELEE ATTACK CLAW SWING
    # ============================================================
    def _draw_claw_swing(surface, boss, x, y, progress):
        """Blood claw slash arc during melee swing."""
        if progress < 0.4 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.45
        t = min(1.0, max(0.0, t))
        # Swing arc center
        center_x = x + facing * 8
        center_y = y - 4
        # Arc sweep radius
        radius = 20 + int(t * 8)
        # Arc angles (going from -0.7 to +0.7 rad relative to forward)
        start_angle = -0.9 + t * 0.4
        end_angle = 0.9 - (1 - t) * 0.4
        # Draw arc as series of blood slashes
        num_slashes = 5
        for i in range(num_slashes):
            slash_t = i / max(1, num_slashes - 1)
            angle = start_angle + (end_angle - start_angle) * slash_t
            slash_inner_x = center_x + int(math.cos(angle) * (radius - 8)) * facing
            slash_inner_y = center_y + int(math.sin(angle) * (radius - 8))
            slash_outer_x = center_x + int(math.cos(angle) * (radius + 4)) * facing
            slash_outer_y = center_y + int(math.sin(angle) * (radius + 4))
            alpha = _NS_sanguiveth._alpha(230 * (1 - t * 0.5))
            # Slash line
            pygame.draw.line(surface,
                             (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                             (slash_inner_x, slash_inner_y),
                             (slash_outer_x, slash_outer_y), 4)
            pygame.draw.line(surface,
                             (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                             (slash_inner_x, slash_inner_y),
                             (slash_outer_x, slash_outer_y), 3)
            pygame.draw.line(surface,
                             (*_NS_sanguiveth.PALETTE["blood_mid"], alpha),
                             (slash_inner_x, slash_inner_y),
                             (slash_outer_x, slash_outer_y), 2)
            pygame.draw.line(surface,
                             (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                             (slash_inner_x, slash_inner_y),
                             (slash_outer_x, slash_outer_y), 1)
            # Tip spark
            pygame.draw.rect(surface,
                             (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                             (slash_outer_x, slash_outer_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_sanguiveth.PALETTE["blood_shine"], alpha),
                             (slash_outer_x, slash_outer_y, 1, 1))
        # Blood droplets flying out
        for i in range(8):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 7)
            drop_dist = radius + 8 + int(t * 12)
            drop_x = center_x + int(math.cos(drop_angle) * drop_dist) * facing
            drop_y = center_y + int(math.sin(drop_angle) * drop_dist)
            alpha = _NS_sanguiveth._alpha(220 * (1 - t))
            pygame.draw.rect(surface,
                             (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                             (drop_x, drop_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_sanguiveth.PALETTE["blood_mid"], alpha),
                             (drop_x, drop_y, 1, 1))
    # ============================================================
    # BLOOD MIST (ambient)
    # ============================================================
    def _draw_blood_mist(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Crimson mist floating below vampire."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(36, 3, -3):
            alpha = _NS_sanguiveth._alpha((36 - radius) * 2.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sanguiveth.PALETTE["mist_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_sanguiveth._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sanguiveth.PALETTE["mist_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising blood droplets
        for i, offset in enumerate((-24, -16, -8, 0, 8, 16, 24, -30, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_sanguiveth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_sanguiveth._aacircle(surface,
                                     (*_NS_sanguiveth.PALETTE["mist_dark"], alpha),
                                     (sx, sy), 3)
            _NS_sanguiveth._aacircle(surface,
                                     (*_NS_sanguiveth.PALETTE["mist_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Trail behind (when moving)
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_sanguiveth._alpha(150 - i * 22)
                if alpha <= 0:
                    continue
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["mist_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["mist_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT (aura, shadow, ring)
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Elongated shadow (smaller because floating)."""
        # Shadow pulses slightly with hover
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 3, 160), (10, 8, 100, 10))
        pygame.draw.ellipse(shadow, (30, 5, 10, 100), (18, 10, 84, 6))
        surface.blit(shadow, (x - 60, y - 12 + hover_offset))
    def _draw_blood_aura(surface, x, y, phase):
        """Blood-red aura behind vampire."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_sanguiveth._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sanguiveth._aacircle(aura,
                                         (*_NS_sanguiveth.PALETTE["mist_dark"], alpha),
                                         (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_sanguiveth._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_sanguiveth._aacircle(aura,
                                         (*_NS_sanguiveth.PALETTE["mist_mid"], alpha),
                                         (100, 85), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_sanguiveth._alpha((30 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_sanguiveth._aacircle(aura,
                                         (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                                         (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))
        # Blood embers
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 36 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_sanguiveth.PALETTE["mist_dark"], 190),
                            (5, 16, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_sanguiveth.PALETTE["blood_darkest"], 210),
                            (12, 18, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_sanguiveth.PALETTE["blood_dark"], 220),
                            (22, 20, 116, 16), 1)
        # Runes (crimson)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 44)
            y1 = 28 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_sanguiveth.PALETTE["blood_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_sanguiveth.PALETTE["blood_hot"],
                                 _NS_sanguiveth._alpha(150 * pulse)),
                                (12, 10, 136, 36), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL: Q - BLOOD FEAST (fast bite lunge line)
    # ============================================================
    def _draw_bloodfeast(surface, boss, x, y, timer, phase):
        """Fast forward lunge with blood spear line."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sanguiveth._target_position(boss, x, y)
        if progress < 0.3:
            # Wind-up: gathering blood
            t = progress / 0.3
            mouth_x = x + facing * 6
            mouth_y = y - 16
            cr = int(3 + t * 5)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_sanguiveth._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                                         (mouth_x, mouth_y), r)
            _NS_sanguiveth._aacircle(surface, _NS_sanguiveth.PALETTE["blood_dark"],
                                     (mouth_x, mouth_y), cr - 1)
            _NS_sanguiveth._aacircle(surface, _NS_sanguiveth.PALETTE["blood_mid"],
                                     (mouth_x, mouth_y), max(1, cr - 3))
            _NS_sanguiveth._aacircle(surface, _NS_sanguiveth.PALETTE["blood_light"],
                                     (mouth_x, mouth_y), max(1, cr - 4))
        else:
            # LUNGE LINE: blood spear extends to target
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 10
            start_y = y - 12
            # Extend gradually
            end_t = min(1.0, t * 1.5)
            bx = int(start_x + (tx - start_x) * end_t)
            by = int(start_y + (ty - start_y) * end_t)
            # Draw thick blood beam
            for layer_i, (width, color) in enumerate([
                (6, _NS_sanguiveth.PALETTE["blood_darkest"]),
                (4, _NS_sanguiveth.PALETTE["blood_dark"]),
                (2, _NS_sanguiveth.PALETTE["blood_mid"]),
                (1, _NS_sanguiveth.PALETTE["blood_light"]),
            ]):
                alpha = _NS_sanguiveth._alpha(230 * (1 - t * 0.3))
                pygame.draw.line(surface, (*color, alpha),
                                 (start_x, start_y), (bx, by), width)
            # Sparks along beam
            beam_len = math.hypot(bx - start_x, by - start_y)
            if beam_len > 0:
                dx = (bx - start_x) / beam_len
                dy = (by - start_y) / beam_len
                for i in range(int(beam_len / 8)):
                    spark_dist = i * 8 + (phase * 5) % 8
                    if spark_dist > beam_len:
                        break
                    sx = int(start_x + dx * spark_dist)
                    sy = int(start_y + dy * spark_dist)
                    perp_x = -dy
                    perp_y = dx
                    offset = math.sin(phase * 4 + i) * 3
                    sx += int(perp_x * offset)
                    sy += int(perp_y * offset)
                    pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_hot"],
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_shine"],
                                     (sx, sy, 1, 1))
            # Impact splash at target
            if t > 0.6:
                st = (t - 0.6) / 0.4
                radius = int(6 + st * 20)
                alpha = _NS_sanguiveth._alpha(240 * (1 - st))
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                                         (tx, ty), radius + 2, 3)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                                         (tx, ty), radius, 2)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_mid"], alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                                         (tx, ty), max(1, radius - 10), 1)
                # Radial blood splatter
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.75)
                    pygame.draw.rect(surface,
                                     (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_sanguiveth.PALETTE["blood_shine"], alpha),
                                     (ex, ey, 1, 1))
                # Healing sparks going BACK to boss (lifesteal visual)
                for i in range(6):
                    heal_t = (phase * 0.8 + i * 0.16) % 1.0
                    hx = int(tx + (start_x - tx) * heal_t)
                    hy = int(ty + (start_y - ty) * heal_t) - int(math.sin(heal_t * math.pi) * 8)
                    alpha_h = _NS_sanguiveth._alpha(240 * (1 - heal_t * 0.5))
                    pygame.draw.rect(surface,
                                     (*_NS_sanguiveth.PALETTE["blood_light"], alpha_h),
                                     (hx, hy, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_sanguiveth.PALETTE["blood_shine"], alpha_h),
                                     (hx, hy, 1, 1))
    # ============================================================
    # SKILL: W - RIP AND TEAR (spinning claw circle)
    # ============================================================
    def _draw_ripandtear_ground(surface, boss, x, y, timer, phase):
        """Ground marker for spin AoE."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_sanguiveth.PALETTE["blood_darkest"], 200),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_sanguiveth.PALETTE["blood_dark"], 180),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_sanguiveth.PALETTE["blood_mid"], 130),
                                (x - r + 8, y + 40 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_ripandtear_foreground(surface, boss, x, y, timer, phase):
        """Spinning claw slashes around boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        radius = int(40 * min(1.0, progress * 3))
        # Rotating slashes (multiple at once, spinning fast)
        spin_speed = 8
        num_slashes = 6
        for i in range(num_slashes):
            base_angle = phase * spin_speed + i * (math.pi * 2 / num_slashes)
            for sub in range(3):  # multi-arc per slash
                angle = base_angle + sub * 0.15
                inner_x = x + int(math.cos(angle) * (radius - 10))
                inner_y = y - 4 + int(math.sin(angle) * (radius - 10) * 0.6)
                outer_x = x + int(math.cos(angle) * (radius + 4))
                outer_y = y - 4 + int(math.sin(angle) * (radius + 4) * 0.6)
                alpha = _NS_sanguiveth._alpha(230 - sub * 60)
                # Slash trail
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 4)
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 3)
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_mid"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 1)
                # Sparks at tip
                pygame.draw.rect(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                                 (outer_x, outer_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_shine"], alpha),
                                 (outer_x, outer_y, 1, 1))
        # Ring of blood droplets orbiting
        for i in range(16):
            angle = -phase * 4 + i * math.pi / 8
            dx = x + int(math.cos(angle) * radius)
            dy = y - 4 + int(math.sin(angle) * radius * 0.6)
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_dark"], (dx, dy, 2, 2))
            pygame.draw.rect(surface, _NS_sanguiveth.PALETTE["blood_mid"], (dx, dy, 1, 1))
    # ============================================================
    # SKILL: E - HEAD BUTT (charge forward)
    # ============================================================
    def _draw_headbutt_ground(surface, boss, x, y, timer, phase):
        """Streak marks on ground during charge."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.9:
            # Speed lines behind
            for i in range(6):
                line_t = (phase * 2 + i * 0.2) % 1.0
                lx_start = x - facing * (10 + i * 8)
                lx_end = lx_start - facing * 14
                ly = y + 40 + int(math.sin(i) * 3)
                alpha = _NS_sanguiveth._alpha(180 * (1 - line_t) * (1 - progress * 0.3))
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                                 (lx_start, ly), (lx_end, ly), 2)
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                                 (lx_start, ly), (lx_end, ly), 1)
    def _draw_headbutt_foreground(surface, boss, x, y, timer, phase):
        """Charge streak + skull impact effect at forward hit."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sanguiveth._target_position(boss, x, y)
        if progress < 0.5:
            # Wind-up: skull glow at boss position
            t = progress / 0.5
            glow_r = int(6 + t * 6)
            for r in range(glow_r + 3, 0, -1):
                alpha = _NS_sanguiveth._alpha(180 * (glow_r + 3 - r) / (glow_r + 3))
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                                         (x + facing * 6, y - 18), r)
            _NS_sanguiveth._aacircle(surface, _NS_sanguiveth.PALETTE["blood_light"],
                                     (x + facing * 6, y - 18), glow_r - 2)
        else:
            # Charge dash trail
            t = (progress - 0.5) / 0.5
            # Speed streaks
            for i in range(8):
                streak_t = (phase * 3 + i * 0.15) % 1.0
                sy = y - 10 + int(math.sin(i * 0.7) * 8)
                sx_start = x + facing * int(i * 8)
                sx_end = sx_start - facing * 16
                alpha = _NS_sanguiveth._alpha(220 * (1 - streak_t) * (1 - t * 0.5))
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                                 (sx_start, sy), (sx_end, sy), 2)
                pygame.draw.line(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                                 (sx_start, sy), (sx_end, sy - 1), 1)
            # Impact at target when reaching
            if t > 0.5:
                impact_t = (t - 0.5) / 0.5
                impact_r = int(8 + impact_t * 22)
                alpha = _NS_sanguiveth._alpha(240 * (1 - impact_t))
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                                         (tx, ty), impact_r + 2, 3)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_dark"], alpha),
                                         (tx, ty), impact_r, 2)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_mid"], alpha),
                                         (tx, ty), max(1, impact_r - 5), 2)
                _NS_sanguiveth._aacircle(surface,
                                         (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                                         (tx, ty), max(1, impact_r - 10), 1)
                # Stun stars
                for i in range(5):
                    star_angle = phase * 2 + i * math.pi * 2 / 5
                    sx = tx + int(math.cos(star_angle) * (impact_r + 6))
                    sy = ty - 15 + int(math.sin(star_angle) * 4)
                    pygame.draw.rect(surface,
                                     (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                                     (sx, sy, 3, 3))
                    pygame.draw.rect(surface,
                                     (*_NS_sanguiveth.PALETTE["blood_shine"], alpha),
                                     (sx, sy + 1, 1, 1))
    # ============================================================
    # SKILL: R - CERTAIN DEATH (dome suppress)
    # ============================================================
    def _draw_certaindeath_ground(surface, boss, x, y, timer, phase):
        """Massive blood pool under dome."""
        tx, ty = _NS_sanguiveth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_sanguiveth.PALETTE["blood_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_sanguiveth.PALETTE["blood_dark"], 200),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_sanguiveth.PALETTE["blood_mid"], 150),
                                (tx - r + 10, ty - r // 3 + 4,
                                 r * 2 - 20, r * 2 // 3 - 8))
            # Rune circle
            for i in range(12):
                angle = phase * 0.5 + i * math.pi / 6
                x1 = tx + int(math.cos(angle) * r)
                y1 = ty + int(math.sin(angle) * r * 0.4)
                x2 = tx + int(math.cos(angle) * (r - 8))
                y2 = ty + int(math.sin(angle) * (r - 8) * 0.4)
                pygame.draw.line(surface, _NS_sanguiveth.PALETTE["blood_hot"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_certaindeath_foreground(surface, boss, x, y, timer, phase):
        """Dome of blood with cage bars, suppressing enemies."""
        tx, ty = _NS_sanguiveth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2))
        if r < 5:
            return
        # Dome surface (translucent)
        dome_surf = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        cx_local, cy_local = r + 15, r + 15
        # Dome bubble outline
        for thickness, alpha_val in [(4, 100), (3, 140), (2, 180), (1, 220)]:
            _NS_sanguiveth._aacircle(dome_surf,
                                     (*_NS_sanguiveth.PALETTE["blood_dark"], alpha_val),
                                     (cx_local, cy_local), r, thickness)
            _NS_sanguiveth._aacircle(dome_surf,
                                     (*_NS_sanguiveth.PALETTE["blood_mid"], alpha_val),
                                     (cx_local, cy_local), r - 1, 1)
        # CAGE BARS (radiating from center like a cage)
        num_bars = 16
        for i in range(num_bars):
            angle = i * math.pi * 2 / num_bars + phase * 0.2
            # Bar goes from just inside dome to just outside
            bar_inner_x = cx_local + int(math.cos(angle) * (r * 0.3))
            bar_inner_y = cy_local + int(math.sin(angle) * (r * 0.3))
            bar_outer_x = cx_local + int(math.cos(angle) * r)
            bar_outer_y = cy_local + int(math.sin(angle) * r)
            # Wavy bar
            segments = 6
            prev = (bar_inner_x, bar_inner_y)
            for s in range(1, segments + 1):
                st = s / segments
                # Wave perpendicular
                perp = angle + math.pi / 2
                wave = math.sin(phase * 3 + i * 0.3 + s * 0.4) * 2
                seg_x = int(bar_inner_x + (bar_outer_x - bar_inner_x) * st)
                seg_y = int(bar_inner_y + (bar_outer_y - bar_inner_y) * st)
                seg_x += int(math.cos(perp) * wave)
                seg_y += int(math.sin(perp) * wave)
                alpha = _NS_sanguiveth._alpha(200)
                pygame.draw.line(dome_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_darkest"], alpha),
                                 prev, (seg_x, seg_y), 3)
                pygame.draw.line(dome_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_mid"], alpha),
                                 prev, (seg_x, seg_y), 2)
                pygame.draw.line(dome_surf,
                                 (*_NS_sanguiveth.PALETTE["blood_light"], alpha),
                                 prev, (seg_x, seg_y), 1)
                prev = (seg_x, seg_y)
            # Bar tip spark
            pygame.draw.rect(dome_surf, _NS_sanguiveth.PALETTE["blood_hot"],
                             (bar_outer_x, bar_outer_y, 2, 2))
            pygame.draw.rect(dome_surf, _NS_sanguiveth.PALETTE["blood_shine"],
                             (bar_outer_x, bar_outer_y, 1, 1))
        # Sparkles orbiting dome
        for i in range(20):
            angle = -phase * 1.5 + i * math.pi / 10
            sx = cx_local + int(math.cos(angle) * r)
            sy = cy_local + int(math.sin(angle) * r)
            pygame.draw.rect(dome_surf, _NS_sanguiveth.PALETTE["blood_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(dome_surf, _NS_sanguiveth.PALETTE["blood_shine"], (sx, sy, 1, 1))
        surface.blit(dome_surf, (tx - r - 15, ty - r - 15))
        # Central blood pillar of light (menacing)
        if progress > 0.4:
            pillar_intensity = math.sin((progress - 0.4) * math.pi * 2) * 0.3 + 0.7
            for layer_i, (width, alpha_val) in enumerate([
                (10, 80), (6, 130), (3, 180), (1, 240),
            ]):
                actual_alpha = _NS_sanguiveth._alpha(alpha_val * pillar_intensity)
                colors = [
                    _NS_sanguiveth.PALETTE["blood_darkest"],
                    _NS_sanguiveth.PALETTE["blood_dark"],
                    _NS_sanguiveth.PALETTE["blood_mid"],
                    _NS_sanguiveth.PALETTE["blood_light"],
                ]
                color = colors[min(layer_i, 3)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - width // 2, ty - 80, width, 80))
            # Rising sparks in pillar
            for i in range(10):
                spark_t = (phase * 1.5 + i * 0.15) % 1.0
                sy = ty - int(spark_t * 70)
                sx = tx + int(math.sin(phase * 3 + i) * 4)
                alpha = _NS_sanguiveth._alpha(240 * (1 - spark_t))
                pygame.draw.rect(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_sanguiveth.PALETTE["blood_shine"], alpha),
                                 (sx, sy, 1, 1))



# ====================================================================
# XERAKHOTEP (SUNBORNE SOVEREIGN) - Mini Boss
# ====================================================================

class _NS_xerakhotep:
    """Namespace xerakhotep - ascended emperor mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Golden armor (main body)
        "gold_darkest": (55, 35, 8),
        "gold_dark": (110, 75, 15),
        "gold_mid": (185, 140, 35),
        "gold_light": (240, 200, 75),
        "gold_shine": (255, 235, 150),
        "gold_glare": (255, 250, 210),
        # Dark bronze (accents, deep armor)
        "bronze_darkest": (20, 12, 5),
        "bronze_dark": (55, 35, 15),
        "bronze_mid": (95, 65, 30),
        "bronze_light": (140, 100, 50),
        # Royal purple (cape, cloth)
        "purple_darkest": (20, 8, 30),
        "purple_dark": (50, 20, 65),
        "purple_mid": (95, 45, 120),
        "purple_light": (150, 90, 180),
        "purple_shine": (200, 150, 220),
        # Turquoise gems
        "gem_dark": (10, 60, 70),
        "gem_mid": (30, 140, 155),
        "gem_light": (90, 220, 230),
        "gem_shine": (200, 255, 250),
        # Sand/dust
        "sand_darkest": (60, 40, 10),
        "sand_dark": (120, 85, 25),
        "sand_mid": (200, 155, 60),
        "sand_light": (245, 215, 130),
        "sand_hot": (255, 235, 170),
        "sand_shine": (255, 250, 220),
        # Dark skin (Shurima warrior)
        "skin_darkest": (35, 20, 15),
        "skin_dark": (75, 45, 30),
        "skin_mid": (120, 80, 55),
        "skin_light": (170, 125, 90),
        # Eyes (golden glow)
        "eye_socket": (5, 3, 2),
        "eye_dark": (80, 55, 10),
        "eye_mid": (200, 160, 40),
        "eye_light": (255, 220, 100),
        "eye_glow": (255, 245, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xerakhotep._clamp(color)
        if _NS_xerakhotep.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xerakhotep._clamp(color)
        if _NS_xerakhotep.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xerakhotep._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xerakhotep(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xerakhotep._detect_moving(boss)
        _NS_xerakhotep._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xer_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_xerakhotep._draw_solar_aura(surface, x, y, pulse)
        _NS_xerakhotep._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_xerakhotep._draw_summon_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xerakhotep._draw_divideconquer_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xerakhotep._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_xerakhotep._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_xerakhotep._draw_float_move(surface, boss, x, y)
        else:
            _NS_xerakhotep._draw_float_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_xerakhotep._draw_conqueringsands(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xerakhotep._draw_summon_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xerakhotep._draw_dash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xerakhotep._draw_divideconquer_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xer_previous_timer", 0))
        active = bool(getattr(boss, "_xer_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._xer_attack_active = True
            boss._xer_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xer_attack_frame = int(getattr(boss, "_xer_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._xer_attack_active = False
            boss._xer_attack_frame = 0
            active = False
        boss._xer_previous_timer = timer
        boss._xer_attack_progress = (
            min(1.0, getattr(boss, "_xer_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_xer_last_x"):
            boss._xer_last_x = boss.x
            boss._xer_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xer_last_x)
        dy = abs(boss.y - boss._xer_last_y)
        boss._xer_last_x = boss.x
        boss._xer_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.7) * 5) - 8
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_xerakhotep._draw_float_shadow(surface, x + sway, y + 50, boss.pulse)
        _NS_xerakhotep._draw_sand_swirl(surface, x + sway, y + 40, boss.pulse)
        _NS_xerakhotep._draw_body(surface, x + sway, y + hover,
                                  boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        hover = int(math.sin(phase * 0.9) * 6) - 9
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_xerakhotep._draw_float_shadow(surface, x + sway, y + 50, phase)
        _NS_xerakhotep._draw_sand_swirl(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_xerakhotep._draw_body(surface, x + sway, y + hover,
                                  boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Ranged attack — scepter thrust launching sand projectile."""
        progress = getattr(boss, "_xer_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Ranged pose: pull scepter back, thrust forward, release
        if progress < 0.4:
            t = progress / 0.4
            body_lean = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            body_lean = int((-3 + t * 8)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            body_lean = int(5 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        hover = int(math.sin(boss.pulse * 0.7) * 3) - 6
        _NS_xerakhotep._draw_float_shadow(surface, x + body_lean, y + 50, boss.pulse)
        _NS_xerakhotep._draw_sand_swirl(surface, x + body_lean, y + 40,
                                        boss.pulse, intense=True)
        _NS_xerakhotep._draw_body(surface, x + body_lean, y + hover - lift,
                                  boss.direction, boss.pulse,
                                  "attack", progress)
        # Sand projectile
        _NS_xerakhotep._draw_sand_projectile(surface, boss, x + body_lean,
                                             y + hover - lift, progress)
    # ============================================================
    # BODY - Emperor figure
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw floating emperor body."""
        # Cape first (behind body)
        _NS_xerakhotep._draw_royal_cape(surface, cx, cy, facing, phase, action)
        # Torso + hips
        _NS_xerakhotep._draw_armor_torso(surface, cx, cy, facing, phase)
        # Legs (dangling because floating)
        _NS_xerakhotep._draw_armor_legs(surface, cx, cy + 8, facing, phase, action)
        # BACK arm (small, less visible)
        _NS_xerakhotep._draw_back_arm(surface, cx, cy - 2, facing, phase)
        # Head with falcon helm
        _NS_xerakhotep._draw_falcon_helm(surface, cx, cy - 18, facing, phase, action,
                                         attack_progress)
        # FRONT arm holding scepter (drawn LAST so scepter is on top)
        _NS_xerakhotep._draw_scepter_arm(surface, cx, cy - 2, facing, phase, action,
                                         attack_progress)
    def _draw_royal_cape(surface, cx, cy, facing, phase, action):
        """Long royal purple cape flowing behind."""
        sway = math.sin(phase * 0.6) * 3
        wind = math.sin(phase * 0.4) * 2
        # Cape flows opposite of facing direction
        back = -facing
        cape_pts = [
            (cx - facing * 2, cy - 6),          # top attach at shoulder
            (cx + back * 5, cy - 4),            # upper back
            (cx + back * 10, cy + 2 + int(wind)),
            (cx + back * 13, cy + 10 + int(sway)),
            (cx + back * 14, cy + 18 + int(sway * 1.2)),
            (cx + back * 12, cy + 26 + int(sway * 0.8)),
            (cx + back * 8, cy + 30 + int(sway * 0.6)),
            (cx + back * 3, cy + 28),
            (cx - facing * 2, cy + 18),
            (cx + facing * 2, cy + 5),
        ]
        # Shadow behind
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in cape_pts])
        # Main cape
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["purple_darkest"], cape_pts)
        # Fold darker
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["purple_dark"], [
            (cx + back * 2, cy - 3),
            (cx + back * 8, cy + 1 + int(wind)),
            (cx + back * 11, cy + 10 + int(sway * 0.9)),
            (cx + back * 11, cy + 22 + int(sway * 0.8)),
            (cx + back * 6, cy + 26),
            (cx + back * 1, cy + 22),
            (cx, cy + 8),
        ])
        # Mid tone highlight (folds)
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["purple_mid"], [
            (cx + back * 3, cy - 1),
            (cx + back * 7, cy + 4 + int(wind * 0.8)),
            (cx + back * 8, cy + 14 + int(sway * 0.8)),
            (cx + back * 6, cy + 20),
            (cx + back * 2, cy + 16),
            (cx + back, cy + 6),
        ])
        # Bright highlight strand
        for i, seg in enumerate([
            (cx + back * 4, cy),
            (cx + back * 6, cy + 8 + int(wind * 0.7)),
            (cx + back * 5, cy + 16 + int(sway * 0.7)),
            (cx + back * 3, cy + 22),
        ]):
            if i > 0:
                pygame.draw.line(surface, _NS_xerakhotep.PALETTE["purple_light"],
                                 prev, seg, 1)
            prev = seg
        # Gold trim along top edge of cape
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (cx + facing, cy - 6),
                         (cx + back * 5, cy - 4), 2)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                         (cx + facing, cy - 6),
                         (cx + back * 5, cy - 4), 1)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                         (cx + facing, cy - 6),
                         (cx + back * 3, cy - 5), 1)
    def _draw_armor_torso(surface, cx, cy, facing, phase):
        """Ornate golden armor chest."""
        breath = math.sin(phase * 0.7) * 1
        torso_pts = [
            (cx - 9, cy - 5),
            (cx - 10, cy),
            (cx - 9, cy + 6),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 9, cy + 6),
            (cx + 10, cy),
            (cx + 9, cy - 5),
        ]
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        # Base bronze
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["bronze_darkest"], torso_pts)
        # Golden armor plates
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"], [
            (cx - 8, cy - 4),
            (cx - 9, cy + 1),
            (cx - 8, cy + 5),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 8, cy + 5),
            (cx + 9, cy + 1),
            (cx + 8, cy - 4),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
            (cx - 7, cy - 3),
            (cx - 8, cy + 1),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 8, cy + 1),
            (cx + 7, cy - 3),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_mid"], [
            (cx - 6, cy - 2),
            (cx - 7, cy + 1),
            (cx - 6, cy + 3),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 6, cy + 3),
            (cx + 7, cy + 1),
            (cx + 6, cy - 2),
        ])
        # Chest plate center highlight
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_light"], [
            (cx - 3, cy - 1),
            (cx + 3, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                         (cx - 1, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_glare"],
                         (cx, cy - 1, 1, 1))
        # Turquoise CENTRAL GEM on chest
        gem_cx = cx
        gem_cy = cy + 3
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (gem_cx - 2, gem_cy - 2, 4, 4))
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gem_dark"], [
            (gem_cx, gem_cy - 2),
            (gem_cx + 2, gem_cy),
            (gem_cx, gem_cy + 2),
            (gem_cx - 2, gem_cy),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gem_mid"], [
            (gem_cx, gem_cy - 1),
            (gem_cx + 1, gem_cy),
            (gem_cx, gem_cy + 1),
            (gem_cx - 1, gem_cy),
        ])
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_light"],
                         (gem_cx, gem_cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_shine"],
                         (gem_cx, gem_cy - 1, 1, 1))
        # Shoulder pauldrons (ornate golden)
        for side in (-1, 1):
            paul_x = cx + side * 9
            paul_y = cy - 5
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"], [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 4, paul_y + 4),
                (paul_x + 2, paul_y + 6),
                (paul_x - 2, paul_y + 6),
                (paul_x - 4, paul_y + 4),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"], [
                (paul_x - 3, paul_y - 1),
                (paul_x + 3, paul_y - 1),
                (paul_x + 4, paul_y + 3),
                (paul_x + 2, paul_y + 5),
                (paul_x - 2, paul_y + 5),
                (paul_x - 4, paul_y + 3),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
                (paul_x - 2, paul_y - 1),
                (paul_x + 2, paul_y - 1),
                (paul_x + 3, paul_y + 2),
                (paul_x + 1, paul_y + 4),
                (paul_x - 1, paul_y + 4),
                (paul_x - 3, paul_y + 2),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_mid"], [
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
                (paul_x + 2, paul_y + 3),
                (paul_x - 2, paul_y + 3),
            ])
            # Shoulder spike (upward like AZIR feathers)
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
                (paul_x, paul_y - 4),
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_light"], [
                (paul_x, paul_y - 3),
                (paul_x - 1, paul_y),
                (paul_x + 1, paul_y),
            ])
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                             (paul_x, paul_y - 3, 1, 1))
            # Small gem on shoulder
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_mid"],
                             (paul_x, paul_y + 2, 1, 1))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_light"],
                             (paul_x, paul_y + 2, 1, 1))
        # Waist belt (dark bronze with gold trim)
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["bronze_darkest"],
                         (cx - 8, cy + 7, 16, 3))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (cx - 8, cy + 7, 16, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_light"],
                         (cx - 8, cy + 7, 16, 1))
        # Belt buckle
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                         (cx - 2, cy + 8, 4, 2))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                         (cx - 1, cy + 8, 2, 1))
    def _draw_armor_legs(surface, cx, cy, facing, phase, action):
        """Armored legs — dangling because floating."""
        sway = math.sin(phase * 0.9) * 1.5
        for side in (-1, 1):
            leg_x_top = cx + side * 4
            leg_x_bot = cx + side * 5 + int(sway * side * 0.5)
            leg_y_top = cy
            leg_y_bot = cy + 14
            # Thigh armor (bronze)
            pygame.draw.line(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                             (leg_x_top + 1, leg_y_top + 1),
                             (leg_x_bot + 1, leg_y_bot + 1), 6)
            pygame.draw.line(surface, _NS_xerakhotep.PALETTE["bronze_darkest"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 5)
            pygame.draw.line(surface, _NS_xerakhotep.PALETTE["bronze_dark"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 4)
            pygame.draw.line(surface, _NS_xerakhotep.PALETTE["bronze_mid"],
                             (leg_x_top - side, leg_y_top),
                             (leg_x_bot - side, leg_y_bot), 3)
            pygame.draw.line(surface, _NS_xerakhotep.PALETTE["bronze_light"],
                             (leg_x_top - side, leg_y_top + 1),
                             (leg_x_bot - side, leg_y_bot - 1), 1)
            # Gold trim/knee accent
            knee_y = leg_y_top + 7
            knee_x = leg_x_top + int((leg_x_bot - leg_x_top) * 0.5)
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                             (knee_x - 2, knee_y, 4, 1))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_light"],
                             (knee_x - 1, knee_y, 2, 1))
            # Ornate greaves at bottom (gold)
            boot_x = leg_x_bot
            boot_y = leg_y_bot
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"], [
                (boot_x - 3, boot_y - 1),
                (boot_x + 3, boot_y - 1),
                (boot_x + 4, boot_y + 3),
                (boot_x - 4, boot_y + 3),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"], [
                (boot_x - 3, boot_y - 2),
                (boot_x + 3, boot_y - 2),
                (boot_x + 3, boot_y + 2),
                (boot_x - 3, boot_y + 2),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
                (boot_x - 2, boot_y - 2),
                (boot_x + 2, boot_y - 2),
                (boot_x + 2, boot_y + 1),
                (boot_x - 2, boot_y + 1),
            ])
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                             (boot_x - 2, boot_y - 2, 4, 1))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_light"],
                             (boot_x - 2, boot_y - 2, 4, 1))
            # Point/upturned tip (pharaoh boot style)
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                             (boot_x + 2, boot_y - 1, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm hanging naturally."""
        back_shoulder_x = cx - facing * 5
        back_shoulder_y = cy - 2
        back_hand_x = back_shoulder_x - facing * 2
        back_hand_y = back_shoulder_y + 12
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 4)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (back_hand_x, back_hand_y), 2)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                         (back_shoulder_x - 1, back_shoulder_y + 1),
                         (back_hand_x - 1, back_hand_y - 1), 1)
        # Fist (small)
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["skin_dark"],
                         (back_hand_x - 1, back_hand_y, 2, 2))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["skin_mid"],
                         (back_hand_x - 1, back_hand_y, 1, 1))
    def _draw_scepter_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding golden scepter (long staff)."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 2
        # Attack: thrust scepter forward
        if action == "attack":
            if attack_progress < 0.4:
                t = attack_progress / 0.4
                arm_angle = -math.pi * 0.15 - t * math.pi * 0.15  # pull back/up
            elif attack_progress < 0.6:
                t = (attack_progress - 0.4) / 0.2
                arm_angle = -math.pi * 0.3 + t * math.pi * 0.5  # thrust forward
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.2 * (1 - t) - math.pi * 0.1 * t
        else:
            # Hold scepter naturally at side
            arm_angle = -math.pi * 0.05 + math.sin(phase * 0.6) * 0.05
        arm_length = 10
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 6
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 3
        # Upper arm (golden armor)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                         (shoulder_x, shoulder_y),
                         (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (shoulder_x, shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                         (shoulder_x - 1, shoulder_y),
                         (elbow_x - 1, elbow_y), 2)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_light"],
                         (shoulder_x - 1, shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Forearm
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 5)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                         (elbow_x, elbow_y),
                         (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (elbow_x, elbow_y),
                         (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                         (elbow_x - 1, elbow_y),
                         (hand_x - 1, hand_y), 2)
        # Gauntlet (bright gold)
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (hand_x - 2, hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (hand_x - 2, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                         (hand_x - 2, hand_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_light"],
                         (hand_x - 2, hand_y - 1, 4, 1))
        # SCEPTER (long staff pointing up from hand)
        _NS_xerakhotep._draw_scepter(surface, hand_x, hand_y, facing, phase,
                                     action, attack_progress, arm_angle)
    def _draw_scepter(surface, hand_x, hand_y, facing, phase, action,
                      attack_progress, arm_angle):
        """Long golden scepter with sun disc + spear top."""
        # Scepter angle: points UP by default, forward during attack
        if action == "attack" and 0.4 <= attack_progress <= 0.7:
            # Thrust forward
            scepter_angle = arm_angle
        else:
            # Point mostly upward
            scepter_angle = -math.pi * 0.45
        # Scepter length
        length_up = 30
        length_down = 8
        top_x = hand_x + int(math.cos(scepter_angle) * length_up) * facing
        top_y = hand_y + int(math.sin(scepter_angle) * length_up)
        bot_x = hand_x - int(math.cos(scepter_angle) * length_down) * facing
        bot_y = hand_y - int(math.sin(scepter_angle) * length_down)
        # Shaft (dark bronze core)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (bot_x + 1, bot_y + 1), (top_x + 1, top_y + 1), 5)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["bronze_darkest"],
                         (bot_x, bot_y), (top_x, top_y), 4)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                         (bot_x, bot_y), (top_x, top_y), 3)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                         (bot_x, bot_y), (top_x, top_y), 2)
        pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_light"],
                         (bot_x, bot_y), (top_x, top_y), 1)
        # Gold bands along shaft
        for band_t in (0.3, 0.55, 0.75):
            bx = int(bot_x + (top_x - bot_x) * band_t)
            by = int(bot_y + (top_y - bot_y) * band_t)
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                             (bx - 2, by - 2, 4, 4))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                             (bx - 2, by - 2, 4, 3))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                             (bx - 2, by - 2, 4, 1))
        # Bottom pommel
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                                 (bot_x, bot_y), 3)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                                 (bot_x, bot_y), 3)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                                 (bot_x, bot_y), 2)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_light"],
                                 (bot_x, bot_y), 1)
        # TOP: sun disc + spear tip
        _NS_xerakhotep._draw_scepter_head(surface, top_x, top_y, scepter_angle,
                                          facing, phase, action)
    def _draw_scepter_head(surface, top_x, top_y, angle, facing, phase, action):
        """Sun disc emblem + spear tip on top of scepter."""
        # Perpendicular direction for spear width
        perp = angle + math.pi / 2
        # Direction of the tip
        tip_offset = 10
        tip_x = top_x + int(math.cos(angle) * tip_offset) * facing
        tip_y = top_y + int(math.sin(angle) * tip_offset)
        # Sun disc at base of tip
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                                 (top_x, top_y), 6)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                                 (top_x, top_y), 5)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_dark"],
                                 (top_x, top_y), 4)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_mid"],
                                 (top_x, top_y), 3)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_light"],
                                 (top_x, top_y), 2)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                                 (top_x, top_y), 1)
        # Sun rays around disc (small tri points)
        for i in range(8):
            ray_angle = i * math.pi / 4 + phase * 0.2
            ray_x = top_x + int(math.cos(ray_angle) * 8)
            ray_y = top_y + int(math.sin(ray_angle) * 8)
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                             (ray_x, ray_y, 1, 1))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_glare"],
                             (ray_x, ray_y, 1, 1))
        # Spear tip (elongated triangle)
        perp_x_off = int(math.cos(perp) * 3)
        perp_y_off = int(math.sin(perp) * 3)
        base_a = (top_x + perp_x_off, top_y + perp_y_off)
        base_b = (top_x - perp_x_off, top_y - perp_y_off)
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1),
            (base_a[0] + 1, base_a[1] + 1),
            (base_b[0] + 1, base_b[1] + 1),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"],
                             [(tip_x, tip_y), base_a, base_b])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
            (tip_x, tip_y),
            (int((tip_x + base_a[0]) / 2), int((tip_y + base_a[1]) / 2)),
            (top_x, top_y),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_mid"], [
            (tip_x, tip_y),
            (int((tip_x + top_x) / 2), int((tip_y + top_y) / 2)),
            (top_x, top_y),
        ])
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_glare"],
                         (tip_x, tip_y, 1, 1))
        # Turquoise gem in center of sun disc
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_dark"],
                         (top_x - 1, top_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_light"],
                         (top_x, top_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gem_shine"],
                         (top_x, top_y - 1, 1, 1))
        # Glow around scepter head (magic aura)
        glow_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for radius in range(10, 0, -1):
            alpha = _NS_xerakhotep._alpha(60 * (10 - radius) / 10 * glow_pulse)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["gold_light"], alpha),
                                     (top_x, top_y), radius)
    def _draw_falcon_helm(surface, cx, cy, facing, phase, action, attack_progress):
        """Ornate golden falcon-head helm."""
        # Base helm shape (rounded top with beak forward)
        helm_pts = [
            (cx - 6, cy + 4),
            (cx - 8, cy),
            (cx - 7, cy - 5),
            (cx - 3, cy - 9),
            (cx + 2, cy - 9),
            (cx + 6, cy - 6),
            (cx + 8, cy - 2),      # back of head
            (cx + 8 * facing + 4, cy + 1),  # beak protrusion
            (cx + 10 * facing, cy + 5),   # beak tip area
            (cx + 4, cy + 6),
            (cx - 2, cy + 6),
        ]
        # Convert facing to actual coordinates
        helm_shape = [
            (cx - 7 * facing, cy + 4),
            (cx - 9 * facing, cy),
            (cx - 8 * facing, cy - 5),
            (cx - 3 * facing, cy - 9),
            (cx + 3 * facing, cy - 9),
            (cx + 7 * facing, cy - 6),
            (cx + 9 * facing, cy - 1),
            (cx + 12 * facing, cy + 2),  # beak forward
            (cx + 10 * facing, cy + 5),  # beak tip
            (cx + 4 * facing, cy + 6),
            (cx - 4 * facing, cy + 6),
        ]
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in helm_shape])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["bronze_darkest"], helm_shape)
        # Gold helm layers
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"], [
            (cx - 6 * facing, cy + 3),
            (cx - 8 * facing, cy - 1),
            (cx - 7 * facing, cy - 5),
            (cx - 2 * facing, cy - 8),
            (cx + 3 * facing, cy - 8),
            (cx + 7 * facing, cy - 5),
            (cx + 8 * facing, cy),
            (cx + 11 * facing, cy + 2),
            (cx + 9 * facing, cy + 4),
            (cx + 4 * facing, cy + 5),
            (cx - 3 * facing, cy + 5),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
            (cx - 6 * facing, cy + 2),
            (cx - 7 * facing, cy - 1),
            (cx - 6 * facing, cy - 5),
            (cx - 1 * facing, cy - 7),
            (cx + 3 * facing, cy - 7),
            (cx + 6 * facing, cy - 4),
            (cx + 7 * facing, cy),
            (cx + 10 * facing, cy + 2),
            (cx + 4 * facing, cy + 4),
            (cx - 3 * facing, cy + 4),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_mid"], [
            (cx - 4 * facing, cy),
            (cx - 5 * facing, cy - 3),
            (cx, cy - 6),
            (cx + 4 * facing, cy - 5),
            (cx + 5 * facing, cy - 2),
            (cx + 5 * facing, cy + 1),
            (cx, cy + 2),
            (cx - 3 * facing, cy + 2),
        ])
        # Top highlight (crown of helm)
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_light"], [
            (cx - 2 * facing, cy - 4),
            (cx + 2 * facing, cy - 5),
            (cx + 3 * facing, cy - 3),
            (cx, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                         (cx + facing, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_glare"],
                         (cx + facing, cy - 4, 1, 1))
        # BEAK (sharp golden point extending forward)
        beak_base_x = cx + 8 * facing
        beak_tip_x = cx + 12 * facing
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"], [
            (beak_base_x + 1, cy + 1),
            (beak_tip_x + 1, cy + 4),
            (beak_base_x + 1, cy + 5),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"], [
            (beak_base_x, cy),
            (beak_tip_x, cy + 3),
            (beak_base_x, cy + 5),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
            (beak_base_x, cy + 1),
            (beak_tip_x - 1 * facing, cy + 3),
            (beak_base_x, cy + 4),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_light"], [
            (beak_base_x + 1 * facing, cy + 2),
            (beak_tip_x - 2 * facing, cy + 3),
            (beak_base_x + 1 * facing, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                         (beak_tip_x - 1 * facing, cy + 3, 1, 1))
        # CROWN FEATHERS/PLUMES on top of helm (like pharaoh crown)
        _NS_xerakhotep._draw_crown_feathers(surface, cx, cy - 8, facing, phase)
        # SIDE CHEEK PIECES (jaw guard)
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
            (cx - 7 * facing, cy + 1),
            (cx - 6 * facing, cy + 4),
            (cx - 4 * facing, cy + 5),
            (cx - 4 * facing, cy + 2),
        ])
        _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_mid"], [
            (cx - 6 * facing, cy + 2),
            (cx - 5 * facing, cy + 4),
            (cx - 4 * facing, cy + 4),
        ])
        # GOLDEN GLOWING EYE (fierce)
        eye_x = cx + 2 * facing
        eye_y = cy - 2
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Eye socket
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["shadow_deep"],
                         (eye_x - 2, eye_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["eye_socket"],
                         (eye_x - 1, eye_y - 1, 3, 3))
        # Glow halo
        for radius in range(5, 0, -1):
            alpha = _NS_xerakhotep._alpha(90 * (5 - radius) / 5 * pulse)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["eye_mid"], alpha),
                                     (eye_x, eye_y), radius)
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["eye_dark"],
                         (eye_x - 1, eye_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["eye_mid"],
                         (eye_x, eye_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["eye_light"],
                         (eye_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["eye_glow"],
                         (eye_x + 1, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_glare"],
                         (eye_x + 1, eye_y, 1, 1))
    def _draw_crown_feathers(surface, cx, cy, facing, phase):
        """Golden plume/feathers on top of falcon helm."""
        # Center main plume + 2 side plumes
        for i, (x_off, height, angle_off) in enumerate([
            (-3, 8, 0.15),   # left plume
            (0, 12, 0.0),    # center tall plume
            (3, 8, -0.15),   # right plume
        ]):
            sway = math.sin(phase * 0.5 + i * 0.4) * 1
            base_x = cx + x_off
            base_y = cy
            tip_x = cx + x_off + int(math.sin(angle_off) * height) + int(sway)
            tip_y = cy - height
            # Plume shape
            perp_x = -math.cos(angle_off)
            pa_x = base_x + 2
            pa_y = base_y
            pb_x = base_x - 2
            pb_y = base_y
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pa_x + 1, pa_y + 1),
                (pb_x + 1, pb_y + 1),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_darkest"], [
                (tip_x, tip_y), (pa_x, pa_y), (pb_x, pb_y),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_dark"], [
                (tip_x, tip_y),
                (int((tip_x + pa_x) / 2), int((tip_y + pa_y) / 2)),
                (base_x, base_y),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["gold_light"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x + 1, base_y),
            ])
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_glare"],
                             (tip_x, tip_y, 1, 1))
    # ============================================================
    # RANGED ATTACK - SAND PROJECTILE
    # ============================================================
    def _draw_sand_projectile(surface, boss, x, y, progress):
        """Golden sand projectile with sun-ray trail."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_xerakhotep._target_position(boss, x, y)
        # Launch from scepter tip
        start_x = x + facing * 22
        start_y = y - 20
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail (golden sand streaks)
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_xerakhotep._alpha(240 - i * 25)
            size = max(1, 7 - i)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_darkest"], alpha),
                                     (px, py), size)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                     (px, py), max(1, size - 2))
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                     (px, py), max(1, size - 3))
            # Sand sparks
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Head (bright golden orb)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_darkest"], (bx, by), 8)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_dark"], (bx, by), 6)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_mid"], (bx, by), 4)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_light"], (bx, by), 3)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_hot"], (bx, by), 2)
        _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["white"], (bx, by, 1, 1))
        # Radial glow around head
        for r in range(12, 3, -2):
            alpha = _NS_xerakhotep._alpha(80 * (12 - r) / 12)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                     (bx, by), r)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_xerakhotep._alpha(240 * (1 - st))
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                     (tx, ty), radius, 3)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                     (tx, ty), max(1, radius - 4), 2)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                     (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SAND SWIRL (ambient below floating boss)
    # ============================================================
    def _draw_sand_swirl(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Golden sand swirling below floating emperor."""
        strength = 1.5 if intense else 1.0
        # Sand cloud
        swirl = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -3):
            alpha = _NS_xerakhotep._alpha((34 - radius) * 2.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    swirl, (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_xerakhotep._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    swirl, (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(swirl, (cx - 75, cy - 10))
        # Rising sand particles swirling
        for i in range(9):
            spiral_t = (phase * 0.6 + i * 0.15) % 1.0
            angle = spiral_t * math.pi * 4 + i
            radius = 20 * (1 - spiral_t)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + 4 - int(spiral_t * 24)
            alpha = _NS_xerakhotep._alpha(230 * (1 - spiral_t) * strength)
            if alpha <= 0:
                continue
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                     (sx, sy), 3)
            _NS_xerakhotep._aacircle(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xerakhotep.PALETTE["sand_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Golden sparkles
        for i in range(8):
            ember_t = (phase * 0.7 + i * 0.15) % 1.0
            ex = cx - 26 + i * 8 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 22)
            alpha = _NS_xerakhotep._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_xerakhotep._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 110 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (10, 5, 3, 160), (10, 8, 110, 10))
        pygame.draw.ellipse(shadow, (40, 25, 10, 100), (18, 10, 94, 6))
        surface.blit(shadow, (x - 65, y - 12 + hover_offset))
    def _draw_solar_aura(surface, x, y, phase):
        """Golden sun aura behind emperor."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 190), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_xerakhotep._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_xerakhotep._aacircle(aura,
                                         (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                         (110, 95), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_xerakhotep._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_xerakhotep._aacircle(aura,
                                         (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                         (110, 95), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_xerakhotep._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xerakhotep._aacircle(aura,
                                         (*_NS_xerakhotep.PALETTE["gold_darkest"], alpha),
                                         (110, 95), radius)
        surface.blit(aura, (x - 110, y - 95))
        # Sun rays radiating out
        for i in range(12):
            angle = phase * 0.15 + i * math.pi / 6
            ray_start_r = 40
            ray_end_r = 70 + int(math.sin(phase + i) * 8)
            start_x = x + int(math.cos(angle) * ray_start_r)
            start_y = y - 5 + int(math.sin(angle) * ray_start_r * 0.5)
            end_x = x + int(math.cos(angle) * ray_end_r)
            end_y = y - 5 + int(math.sin(angle) * ray_end_r * 0.5)
            alpha = _NS_xerakhotep._alpha(120 * pulse)
            pygame.draw.line(surface,
                             (*_NS_xerakhotep.PALETTE["gold_mid"], alpha),
                             (start_x, start_y), (end_x, end_y), 2)
            pygame.draw.line(surface,
                             (*_NS_xerakhotep.PALETTE["gold_light"], alpha),
                             (start_x, start_y), (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                             (end_x, end_y, 1, 1))
        # Floating gold particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["gold_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring — golden Shurima runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xerakhotep.PALETTE["sand_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_xerakhotep.PALETTE["gold_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_xerakhotep.PALETTE["gold_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_xerakhotep.PALETTE["gold_mid"], 180),
                            (40, 24, 90, 14), 1)
        # Golden runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_xerakhotep.PALETTE["gold_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_xerakhotep.PALETTE["gold_shine"],
                                 _NS_xerakhotep._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: CONQUERING SANDS (sand line projectile)
    # ============================================================
    def _draw_conqueringsands(surface, boss, x, y, timer, phase):
        """Elongated sand spear line traveling to target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xerakhotep._target_position(boss, x, y)
        if progress < 0.25:
            # Wind up at scepter
            t = progress / 0.25
            gather_x = x + facing * 22
            gather_y = y - 20
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_xerakhotep._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_darkest"], alpha),
                                         (gather_x, gather_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_xerakhotep._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                         (gather_x, gather_y), r)
            _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_mid"],
                                     (gather_x, gather_y), cr - 2)
            _NS_xerakhotep._aacircle(surface, _NS_xerakhotep.PALETTE["sand_light"],
                                     (gather_x, gather_y), max(1, cr - 4))
        else:
            # LINE PROJECTILE
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 24
            start_y = y - 20
            end_t = min(1.0, t * 1.4)
            end_x = int(start_x + (tx - start_x) * end_t)
            end_y = int(start_y + (ty - start_y) * end_t)
            # Elongated spear-line shape (perpendicular thickness)
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.hypot(dx, dy)
            if length > 1:
                nx = dx / length
                ny = dy / length
                perp_x = -ny
                perp_y = nx
                # Multi-layer beam
                for layer_i, (thickness, color) in enumerate([
                    (7, _NS_xerakhotep.PALETTE["sand_darkest"]),
                    (5, _NS_xerakhotep.PALETTE["sand_dark"]),
                    (3, _NS_xerakhotep.PALETTE["sand_mid"]),
                    (2, _NS_xerakhotep.PALETTE["sand_light"]),
                    (1, _NS_xerakhotep.PALETTE["sand_hot"]),
                ]):
                    alpha = _NS_xerakhotep._alpha(230)
                    pygame.draw.line(surface, (*color, alpha),
                                     (start_x, start_y),
                                     (end_x, end_y), thickness)
                # Sand particles along beam
                for i in range(int(length / 6)):
                    seg_t = i * 6 / length
                    if seg_t > end_t:
                        break
                    sx = int(start_x + dx * seg_t)
                    sy = int(start_y + dy * seg_t)
                    offset = math.sin(phase * 5 + i) * 4
                    sx += int(perp_x * offset)
                    sy += int(perp_y * offset)
                    pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["sand_hot"],
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["sand_shine"],
                                     (sx, sy, 1, 1))
                # Sharp tip
                tip_len = 8
                tip_a = (end_x + int(perp_x * 3), end_y + int(perp_y * 3))
                tip_b = (end_x - int(perp_x * 3), end_y - int(perp_y * 3))
                tip_p = (end_x + int(nx * tip_len), end_y + int(ny * tip_len))
                _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["sand_dark"],
                                     [tip_p, tip_a, tip_b])
                _NS_xerakhotep._poly(surface, _NS_xerakhotep.PALETTE["sand_light"], [
                    tip_p,
                    (int((tip_p[0] + tip_a[0]) / 2), int((tip_p[1] + tip_a[1]) / 2)),
                    (end_x, end_y),
                ])
                pygame.draw.rect(surface, _NS_xerakhotep.PALETTE["sand_shine"],
                                 (tip_p[0], tip_p[1], 1, 1))
            # Impact
            if end_t > 0.75:
                st = (end_t - 0.75) / 0.25
                radius = int(10 + st * 20)
                alpha = _NS_xerakhotep._alpha(240 * (1 - st))
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_darkest"], alpha),
                                         (tx, ty), radius + 3, 3)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                         (tx, ty), radius, 3)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                         (tx, ty), max(1, radius - 10), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_xerakhotep.PALETTE["sand_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W: SOLDIER OF SHURIMA (summon soldier)
    # ============================================================
    def _draw_summon_ground(surface, boss, x, y, timer, phase):
        """Rising sand at summon location."""
        tx, ty = _NS_xerakhotep._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(30 * min(1.0, progress * 4))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["sand_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["sand_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["sand_mid"], 130),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            # Rune circle around summon spot
            for i in range(8):
                angle = phase * 0.5 + i * math.pi / 4
                x1 = tx + int(math.cos(angle) * r)
                y1 = ty + int(math.sin(angle) * r * 0.4)
                x2 = tx + int(math.cos(angle) * (r - 6))
                y2 = ty + int(math.sin(angle) * (r - 6) * 0.4)
                pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_light"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_summon_foreground(surface, boss, x, y, timer, phase):
        """Sand soldier materializing at target."""
        tx, ty = _NS_xerakhotep._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Rising sand column
            t = progress / 0.3
            col_h = int(t * 30)
            for i in range(col_h):
                col_y = ty - i
                alpha = _NS_xerakhotep._alpha(200 * (1 - i / max(1, col_h)))
                width = int(6 + math.sin(phase * 4 + i * 0.3) * 2)
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                 (tx - width // 2, col_y, width, 1))
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                 (tx, col_y, 1, 1))
        else:
            # Soldier forms
            t = (progress - 0.3) / 0.7
            _NS_xerakhotep._draw_sand_soldier(surface, tx, ty, phase, t, boss.direction)
    def _draw_sand_soldier(surface, sx, sy, phase, form_progress, facing):
        """Small sand soldier figure with spear."""
        alpha_base = int(255 * min(1.0, form_progress * 1.5))
        # Body silhouette (small warrior)
        # Head
        _NS_xerakhotep._aacircle(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_darkest"], alpha_base),
                                 (sx, sy - 20), 4)
        _NS_xerakhotep._aacircle(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_dark"], alpha_base),
                                 (sx, sy - 20), 3)
        _NS_xerakhotep._aacircle(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_mid"], alpha_base),
                                 (sx - 1, sy - 20), 2)
        # Helm feather
        pygame.draw.line(surface,
                         (*_NS_xerakhotep.PALETTE["gold_dark"], alpha_base),
                         (sx, sy - 24), (sx, sy - 20), 2)
        pygame.draw.line(surface,
                         (*_NS_xerakhotep.PALETTE["gold_light"], alpha_base),
                         (sx, sy - 24), (sx, sy - 21), 1)
        # Torso
        _NS_xerakhotep._poly(surface,
                             (*_NS_xerakhotep.PALETTE["gold_darkest"], alpha_base), [
            (sx - 4, sy - 16),
            (sx + 4, sy - 16),
            (sx + 3, sy - 6),
            (sx - 3, sy - 6),
        ])
        _NS_xerakhotep._poly(surface,
                             (*_NS_xerakhotep.PALETTE["gold_dark"], alpha_base), [
            (sx - 3, sy - 15),
            (sx + 3, sy - 15),
            (sx + 2, sy - 7),
            (sx - 2, sy - 7),
        ])
        _NS_xerakhotep._poly(surface,
                             (*_NS_xerakhotep.PALETTE["gold_mid"], alpha_base), [
            (sx - 2, sy - 14),
            (sx + 2, sy - 14),
            (sx + 1, sy - 8),
            (sx - 1, sy - 8),
        ])
        # Legs
        pygame.draw.line(surface,
                         (*_NS_xerakhotep.PALETTE["gold_dark"], alpha_base),
                         (sx - 2, sy - 6), (sx - 2, sy), 2)
        pygame.draw.line(surface,
                         (*_NS_xerakhotep.PALETTE["gold_dark"], alpha_base),
                         (sx + 2, sy - 6), (sx + 2, sy), 2)
        # SPEAR (tall)
        spear_x = sx + facing * 5
        pygame.draw.line(surface,
                         (*_NS_xerakhotep.PALETTE["gold_darkest"], alpha_base),
                         (spear_x, sy - 28), (spear_x, sy + 2), 2)
        pygame.draw.line(surface,
                         (*_NS_xerakhotep.PALETTE["gold_light"], alpha_base),
                         (spear_x, sy - 28), (spear_x, sy + 2), 1)
        # Spear tip
        _NS_xerakhotep._poly(surface,
                             (*_NS_xerakhotep.PALETTE["gold_dark"], alpha_base), [
            (spear_x, sy - 32),
            (spear_x - 2, sy - 28),
            (spear_x + 2, sy - 28),
        ])
        _NS_xerakhotep._poly(surface,
                             (*_NS_xerakhotep.PALETTE["gold_light"], alpha_base), [
            (spear_x, sy - 31),
            (spear_x - 1, sy - 28),
            (spear_x + 1, sy - 28),
        ])
        pygame.draw.rect(surface,
                         (*_NS_xerakhotep.PALETTE["gold_shine"], alpha_base),
                         (spear_x, sy - 31, 1, 1))
        # Golden glow around soldier when forming
        if form_progress < 0.6:
            glow_alpha = _NS_xerakhotep._alpha(150 * (1 - form_progress / 0.6))
            for r in range(15, 3, -2):
                a = _NS_xerakhotep._alpha(glow_alpha * (15 - r) / 15)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_hot"], a),
                                         (sx, sy - 12), r)
    # ============================================================
    # SKILL E: EMPEROR'S DASH
    # ============================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Streak marks under boss during dash."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.9:
            for i in range(6):
                line_t = (phase * 2 + i * 0.2) % 1.0
                lx_start = x - facing * (10 + i * 8)
                lx_end = lx_start - facing * 16
                ly = y + 40 + int(math.sin(i) * 3)
                alpha = _NS_xerakhotep._alpha(200 * (1 - line_t) * (1 - progress * 0.3))
                pygame.draw.line(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                 (lx_start, ly), (lx_end, ly), 2)
                pygame.draw.line(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                 (lx_start, ly), (lx_end, ly), 1)
    def _draw_dash_foreground(surface, boss, x, y, timer, phase):
        """Sand dash streak with afterimages."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xerakhotep._target_position(boss, x, y)
        if progress < 0.3:
            # Wind up: swirling sand at feet
            t = progress / 0.3
            for i in range(8):
                angle = phase * 3 + i * math.pi / 4
                r = int(15 * t)
                sx = x + int(math.cos(angle) * r)
                sy = y + 30 + int(math.sin(angle) * r * 0.4)
                alpha = _NS_xerakhotep._alpha(200 * t)
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_hot"], alpha),
                                 (sx, sy, 2, 2))
        else:
            t = (progress - 0.3) / 0.7
            # Speed streaks
            for i in range(10):
                streak_t = (phase * 4 + i * 0.1) % 1.0
                sy = y - 15 + int(math.sin(i * 0.7) * 10)
                sx_start = x + facing * int(i * 6)
                sx_end = sx_start - facing * 18
                alpha = _NS_xerakhotep._alpha(220 * (1 - streak_t) * (1 - t * 0.5))
                pygame.draw.line(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                 (sx_start, sy), (sx_end, sy), 2)
                pygame.draw.line(surface,
                                 (*_NS_xerakhotep.PALETTE["sand_hot"], alpha),
                                 (sx_start, sy), (sx_end, sy - 1), 1)
            # Impact
            if t > 0.5:
                impact_t = (t - 0.5) / 0.5
                impact_r = int(10 + impact_t * 22)
                alpha = _NS_xerakhotep._alpha(240 * (1 - impact_t))
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_darkest"], alpha),
                                         (tx, ty), impact_r + 2, 3)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_dark"], alpha),
                                         (tx, ty), impact_r, 2)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_mid"], alpha),
                                         (tx, ty), max(1, impact_r - 5), 2)
                _NS_xerakhotep._aacircle(surface,
                                         (*_NS_xerakhotep.PALETTE["sand_light"], alpha),
                                         (tx, ty), max(1, impact_r - 10), 1)
    # ============================================================
    # SKILL R: DIVIDE AND CONQUER (soldier ring)
    # ============================================================
    def _draw_divideconquer_ground(surface, boss, x, y, timer, phase):
        """Ring of runes at boss's location."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["sand_darkest"], 200),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["sand_dark"], 180),
                                (x - r + 4, y + 40 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["gold_dark"], 220),
                                (x - r + 8, y + 40 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_xerakhotep.PALETTE["gold_light"], 180),
                                (x - r + 12, y + 40 - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12), 1)
            # Runes around ring
            for i in range(16):
                angle = phase * 0.4 + i * math.pi / 8
                x1 = x + int(math.cos(angle) * r)
                y1 = y + 40 + int(math.sin(angle) * r * 0.4)
                x2 = x + int(math.cos(angle) * (r - 8))
                y2 = y + 40 + int(math.sin(angle) * (r - 8) * 0.4)
                pygame.draw.line(surface, _NS_xerakhotep.PALETTE["gold_shine"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_divideconquer_foreground(surface, boss, x, y, timer, phase):
        """Ring of sand soldiers with spears facing outward."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        radius = int(70 * min(1.0, progress * 2))
        if radius < 10:
            return
        # 8 sand soldiers in a ring
        num_soldiers = 8
        for i in range(num_soldiers):
            angle = i * math.pi * 2 / num_soldiers + phase * 0.05
            sx = x + int(math.cos(angle) * radius)
            sy = y + 30 + int(math.sin(angle) * radius * 0.4)
            # Facing outward from center
            face_dir = 1 if math.cos(angle) > 0 else -1
            # Soldier forming animation
            form_t = min(1.0, progress * 2)
            _NS_xerakhotep._draw_sand_soldier(surface, sx, sy, phase + i,
                                              form_t, face_dir)
        # Golden barrier lines connecting soldiers
        for i in range(num_soldiers):
            a1 = i * math.pi * 2 / num_soldiers + phase * 0.05
            a2 = (i + 1) * math.pi * 2 / num_soldiers + phase * 0.05
            x1 = x + int(math.cos(a1) * radius)
            y1 = y + 30 + int(math.sin(a1) * radius * 0.4)
            x2 = x + int(math.cos(a2) * radius)
            y2 = y + 30 + int(math.sin(a2) * radius * 0.4)
            alpha = _NS_xerakhotep._alpha(180 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface,
                             (*_NS_xerakhotep.PALETTE["gold_light"], alpha),
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(surface,
                             (*_NS_xerakhotep.PALETTE["gold_shine"], alpha),
                             (x1, y1 - 1), (x2, y2 - 1), 1)
        # Central golden pillar (boss channel)
        if progress > 0.3:
            pillar_intensity = math.sin((progress - 0.3) * math.pi * 2) * 0.3 + 0.7
            for layer_i, (width, color) in enumerate([
                (10, _NS_xerakhotep.PALETTE["sand_darkest"]),
                (6, _NS_xerakhotep.PALETTE["sand_dark"]),
                (3, _NS_xerakhotep.PALETTE["sand_mid"]),
                (1, _NS_xerakhotep.PALETTE["sand_shine"]),
            ]):
                alpha = _NS_xerakhotep._alpha(150 * pillar_intensity)
                pygame.draw.rect(surface, (*color, alpha),
                                 (x - width // 2, y - 70, width, 70))
            # Rising sparkles
            for i in range(10):
                spark_t = (phase * 1.5 + i * 0.15) % 1.0
                sy_up = y - int(spark_t * 60)
                sx_up = x + int(math.sin(phase * 3 + i) * 4)
                alpha = _NS_xerakhotep._alpha(240 * (1 - spark_t))
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_shine"], alpha),
                                 (sx_up, sy_up, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_xerakhotep.PALETTE["gold_glare"], alpha),
                                 (sx_up, sy_up, 1, 1))



# ====================================================================
# NYRETHZALV (FORSAKEN EMPRESS OF SHADOW-CHAINS) - TRUE BOSS
# ====================================================================

class _NS_nyrethzalv:
    """Namespace nyrethzalv - fallen dark angel TRUE BOSS."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Deep purple robe/dress
        "robe_darkest": (15, 5, 25),
        "robe_dark": (35, 15, 55),
        "robe_mid": (70, 35, 100),
        "robe_light": (110, 65, 155),
        "robe_shine": (170, 120, 210),
        # Magenta magic (main theme - shadow purple with pink)
        "magic_darkest": (20, 5, 30),
        "magic_dark": (65, 15, 90),
        "magic_mid": (145, 40, 180),
        "magic_light": (210, 90, 235),
        "magic_hot": (240, 140, 255),
        "magic_shine": (255, 210, 255),
        # Black feathered wings
        "feather_darkest": (5, 3, 10),
        "feather_dark": (20, 12, 35),
        "feather_mid": (45, 30, 65),
        "feather_light": (85, 65, 110),
        "feather_edge": (130, 100, 165),
        # Pale skin
        "skin_darkest": (75, 55, 65),
        "skin_dark": (135, 105, 115),
        "skin_mid": (185, 155, 165),
        "skin_light": (225, 200, 205),
        "skin_shine": (245, 225, 225),
        # Black hair
        "hair_darkest": (5, 3, 12),
        "hair_dark": (20, 12, 30),
        "hair_mid": (45, 30, 55),
        "hair_light": (85, 65, 95),
        "hair_shine": (130, 105, 145),
        # Gold accents (crown, trim, jewelry)
        "gold_dark": (75, 55, 15),
        "gold_mid": (155, 120, 40),
        "gold_light": (220, 185, 90),
        "gold_shine": (255, 235, 160),
        # Purple/magenta glowing eyes
        "eye_socket": (5, 2, 8),
        "eye_dark": (80, 20, 100),
        "eye_mid": (200, 60, 220),
        "eye_light": (240, 130, 255),
        "eye_glow": (255, 200, 255),
        # Chain (shadow chains)
        "chain_darkest": (10, 5, 15),
        "chain_dark": (30, 15, 45),
        "chain_mid": (75, 40, 100),
        "chain_light": (140, 80, 175),
        # Nether accents
        "void_darkest": (2, 0, 5),
        "void_dark": (10, 3, 20),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyrethzalv._clamp(color)
        if _NS_nyrethzalv.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyrethzalv._clamp(color)
        if _NS_nyrethzalv.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyrethzalv._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyrethzalv(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyrethzalv._detect_moving(boss)
        _NS_nyrethzalv._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nzl_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (TRUE BOSS = bigger)
        _NS_nyrethzalv._draw_shadow_aura(surface, x, y, pulse)
        _NS_nyrethzalv._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_nyrethzalv._draw_torrent_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyrethzalv._draw_soulshackles_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyrethzalv._draw_blackshield_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_nyrethzalv._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_nyrethzalv._draw_float_move(surface, boss, x, y)
        else:
            _NS_nyrethzalv._draw_float_idle(surface, boss, x, y)
        # E - Black Shield bubble around body
        if active_skill == "e":
            _NS_nyrethzalv._draw_blackshield_bubble(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_nyrethzalv._draw_darkbinding_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyrethzalv._draw_torrent_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyrethzalv._draw_soulshackles_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nzl_previous_timer", 0))
        active = bool(getattr(boss, "_nzl_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nzl_attack_active = True
            boss._nzl_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nzl_attack_frame = int(getattr(boss, "_nzl_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nzl_attack_active = False
            boss._nzl_attack_frame = 0
            active = False
        boss._nzl_previous_timer = timer
        boss._nzl_attack_progress = (
            min(1.0, getattr(boss, "_nzl_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nzl_last_x"):
            boss._nzl_last_x = boss.x
            boss._nzl_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nzl_last_x)
        dy = abs(boss.y - boss._nzl_last_y)
        boss._nzl_last_x = boss.x
        boss._nzl_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.7) * 5) - 10
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_nyrethzalv._draw_float_shadow(surface, x + sway, y + 52, boss.pulse)
        _NS_nyrethzalv._draw_shadow_mist(surface, x + sway, y + 42, boss.pulse)
        _NS_nyrethzalv._draw_body(surface, x + sway, y + hover,
                                  boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        hover = int(math.sin(phase * 0.9) * 6) - 11
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_nyrethzalv._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_nyrethzalv._draw_shadow_mist(surface, x + sway, y + 42, phase,
                                         trail=True, facing=boss.direction)
        _NS_nyrethzalv._draw_body(surface, x + sway, y + hover,
                                  boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Ranged: shadow orb from extended palm."""
        progress = getattr(boss, "_nzl_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Pull back → extend palm → recovery
        if progress < 0.4:
            t = progress / 0.4
            lean = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            lean = int((-3 + t * 8)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(5 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        hover = int(math.sin(boss.pulse * 0.7) * 3) - 8
        _NS_nyrethzalv._draw_float_shadow(surface, x + lean, y + 52, boss.pulse)
        _NS_nyrethzalv._draw_shadow_mist(surface, x + lean, y + 42,
                                         boss.pulse, intense=True)
        _NS_nyrethzalv._draw_body(surface, x + lean, y + hover - lift,
                                  boss.direction, boss.pulse,
                                  "attack", progress)
        _NS_nyrethzalv._draw_shadow_projectile(surface, boss, x + lean,
                                               y + hover - lift, progress)
    # ============================================================
    # BODY - Fallen dark angel
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Wings first (behind body)
        _NS_nyrethzalv._draw_feathered_wings(surface, cx, cy - 6, facing, phase, action,
                                             attack_progress)
        # Trailing chains behind
        _NS_nyrethzalv._draw_shadow_chains(surface, cx, cy, facing, phase)
        # Robe torso + hips
        _NS_nyrethzalv._draw_robe_torso(surface, cx, cy, facing, phase)
        # Long flowing skirt (dangling because floating)
        _NS_nyrethzalv._draw_flowing_skirt(surface, cx, cy + 8, facing, phase, action)
        # Back arm (subtle)
        _NS_nyrethzalv._draw_back_arm(surface, cx, cy - 2, facing, phase, action)
        # Head with crown + long black hair
        _NS_nyrethzalv._draw_dark_angel_head(surface, cx, cy - 20, facing, phase,
                                             action, attack_progress)
        # FRONT arm (casting hand — drawn LAST for priority)
        _NS_nyrethzalv._draw_casting_arm(surface, cx, cy - 2, facing, phase, action,
                                         attack_progress)
    def _draw_feathered_wings(surface, cx, cy, facing, phase, action,
                              attack_progress):
        """Large black-purple feathered angel wings."""
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 1.0) * 4
        # Draw both wings — far one bigger, near one smaller
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing
            (1, 0.75, 0.85),  # near wing (partial)
        ]):
            base_x = cx - facing * 4
            base_y = cy - 2
            # Wing spans (3 main "bone arcs")
            spar1_len = int(38 * size_mult)
            spar1_angle = math.pi * 0.55 * side_mult - math.radians(beat)
            spar2_len = int(42 * size_mult)
            spar2_angle = math.pi * 0.78 * side_mult - math.radians(beat * 0.8)
            spar3_len = int(34 * size_mult)
            spar3_angle = math.pi * 1.02 * side_mult - math.radians(beat * 0.5)
            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)
            # Main wing silhouette
            wing_shape = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                (int(tip1_x * 0.55 + tip2_x * 0.45),
                 int(tip1_y * 0.55 + tip2_y * 0.45) + int(4 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.55 + tip3_x * 0.45),
                 int(tip2_y * 0.55 + tip3_y * 0.45) + int(5 * size_mult)),
                (tip3_x, tip3_y),
                (base_x - facing * 4, base_y + int(8 * size_mult)),
            ]
            wing_surf = pygame.Surface((200, 130), pygame.SRCALPHA)
            offset_x = base_x - 100
            offset_y = base_y - 65
            local_pts = [(p[0] - offset_x, p[1] - offset_y) for p in wing_shape]
            # Layered feathered body
            _NS_nyrethzalv._poly(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["feather_darkest"],
                                  int(240 * alpha_mult)),
                                 local_pts)
            # Inner layer (slightly smaller)
            inner_pts = []
            cx_local = sum(p[0] for p in local_pts) / len(local_pts)
            cy_local = sum(p[1] for p in local_pts) / len(local_pts)
            for p in local_pts:
                inner_pts.append(
                    (int(p[0] * 0.85 + cx_local * 0.15),
                     int(p[1] * 0.85 + cy_local * 0.15))
                )
            _NS_nyrethzalv._poly(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["feather_dark"],
                                  int(220 * alpha_mult)),
                                 inner_pts)
            # Feather "rows" — draw multiple feather rows from base outward
            _NS_nyrethzalv._draw_feather_rows(
                wing_surf, base_x - offset_x, base_y - offset_y,
                (tip1_x - offset_x, tip1_y - offset_y),
                (tip2_x - offset_x, tip2_y - offset_y),
                (tip3_x - offset_x, tip3_y - offset_y),
                alpha_mult, size_mult, side_mult,
            )
            # Purple/magenta magic glow along top edge
            for i in range(3):
                pygame.draw.line(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["magic_mid"],
                                  int(180 * alpha_mult)),
                                 (base_x - offset_x, base_y - offset_y),
                                 (tip1_x - offset_x, tip1_y - offset_y), 1)
            pygame.draw.line(wing_surf,
                             (*_NS_nyrethzalv.PALETTE["magic_light"],
                              int(200 * alpha_mult)),
                             (base_x - offset_x, base_y - offset_y),
                             (tip1_x - offset_x + 1, tip1_y - offset_y - 1), 1)
            # Sparkle at each wing tip
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                _NS_nyrethzalv._aacircle(wing_surf,
                                         (*_NS_nyrethzalv.PALETTE["magic_dark"],
                                          int(220 * alpha_mult)),
                                         tip, 2)
                pygame.draw.rect(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["magic_light"],
                                  int(240 * alpha_mult)),
                                 (tip[0], tip[1], 1, 1))
                pygame.draw.rect(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["magic_shine"],
                                  int(240 * alpha_mult)),
                                 (tip[0], tip[1], 1, 1))
            # Falling feather particles from wing tip
            for i in range(3):
                fall_t = (phase * 0.5 + i * 0.35) % 1.0
                fx = tip3_x - offset_x + int(math.sin(fall_t * 2) * 4)
                fy = tip3_y - offset_y + int(fall_t * 20)
                falpha = _NS_nyrethzalv._alpha(200 * (1 - fall_t) * alpha_mult)
                pygame.draw.rect(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["feather_dark"], falpha),
                                 (fx, fy, 2, 3))
                pygame.draw.rect(wing_surf,
                                 (*_NS_nyrethzalv.PALETTE["magic_mid"], falpha),
                                 (fx, fy, 1, 1))
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_feather_rows(surface, bx, by, tip1, tip2, tip3, alpha_mult,
                           size_mult, side_mult):
        """Draw individual feathers overlapping in rows."""
        # 3 rows of feathers, each row has multiple feathers along wing edge
        # Row 1: base → tip1 (upper edge feathers)
        for i in range(1, 5):
            t = i / 5
            fx = int(bx + (tip1[0] - bx) * t)
            fy = int(by + (tip1[1] - by) * t)
            feather_len = int((12 - i * 2) * size_mult)
            feather_end_x = fx + int((tip1[0] - bx) / max(1, abs(tip1[0] - bx))
                                     * feather_len * 0.5) if tip1[0] != bx else fx
            feather_end_y = fy + int(feather_len * 0.8)
            _NS_nyrethzalv._poly(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_darkest"],
                                  int(240 * alpha_mult)), [
                (fx, fy),
                (fx - 3, feather_end_y),
                (fx + 3, feather_end_y),
            ])
            _NS_nyrethzalv._poly(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_dark"],
                                  int(230 * alpha_mult)), [
                (fx, fy),
                (fx - 2, feather_end_y - 1),
                (fx + 2, feather_end_y - 1),
            ])
            # Feather highlight
            pygame.draw.line(surface,
                             (*_NS_nyrethzalv.PALETTE["feather_mid"],
                              int(230 * alpha_mult)),
                             (fx, fy), (fx, feather_end_y - 2), 1)
            pygame.draw.rect(surface,
                             (*_NS_nyrethzalv.PALETTE["feather_edge"],
                              int(200 * alpha_mult)),
                             (fx, fy + 2, 1, 1))
        # Row 2: middle bone → tip2
        for i in range(1, 6):
            t = i / 6
            fx = int(bx + (tip2[0] - bx) * t)
            fy = int(by + (tip2[1] - by) * t)
            feather_len = int((14 - i * 2) * size_mult)
            _NS_nyrethzalv._poly(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_darkest"],
                                  int(240 * alpha_mult)), [
                (fx, fy),
                (fx - 4, fy + feather_len),
                (fx + 4, fy + feather_len),
            ])
            _NS_nyrethzalv._poly(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_dark"],
                                  int(230 * alpha_mult)), [
                (fx, fy),
                (fx - 3, fy + feather_len - 1),
                (fx + 3, fy + feather_len - 1),
            ])
            pygame.draw.line(surface,
                             (*_NS_nyrethzalv.PALETTE["feather_mid"],
                              int(220 * alpha_mult)),
                             (fx, fy), (fx, fy + feather_len - 2), 1)
        # Row 3: LONGEST bottom feathers (tail feathers) → tip3
        for i in range(1, 5):
            t = i / 5
            fx = int(bx + (tip3[0] - bx) * t)
            fy = int(by + (tip3[1] - by) * t)
            feather_len = int((18 - i * 2) * size_mult)
            _NS_nyrethzalv._poly(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_darkest"],
                                  int(240 * alpha_mult)), [
                (fx, fy),
                (fx - 4, fy + feather_len),
                (fx + 4, fy + feather_len),
            ])
            _NS_nyrethzalv._poly(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_dark"],
                                  int(220 * alpha_mult)), [
                (fx, fy + 1),
                (fx - 3, fy + feather_len - 1),
                (fx + 3, fy + feather_len - 1),
            ])
            pygame.draw.line(surface,
                             (*_NS_nyrethzalv.PALETTE["feather_mid"],
                              int(220 * alpha_mult)),
                             (fx, fy), (fx, fy + feather_len - 2), 1)
    def _draw_shadow_chains(surface, cx, cy, facing, phase):
        """Chains hanging from waist/back — trailing behind."""
        sway = math.sin(phase * 0.5) * 2
        for i, (base_off_x, base_off_y, length) in enumerate([
            (-facing * 4, 4, 22),
            (-facing * 6, 8, 26),
            (facing * 3, 6, 20),  # front side
        ]):
            base_x = cx + base_off_x
            base_y = cy + base_off_y
            for step in range(1, 6):
                t = step / 5
                seg_x = base_x + int(math.sin(phase * 0.4 + i + t * 2) * (sway + t * 2))
                seg_y = base_y + int(t * length)
                if step % 2 == 0:
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["shadow_deep"],
                                     (seg_x - 1, seg_y - 1, 3, 3))
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["chain_darkest"],
                                     (seg_x - 1, seg_y - 1, 3, 3))
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["chain_dark"],
                                     (seg_x - 1, seg_y - 1, 2, 2))
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["chain_mid"],
                                     (seg_x, seg_y - 1, 1, 1))
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["chain_light"],
                                     (seg_x, seg_y - 1, 1, 1))
                else:
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["chain_darkest"],
                                     (seg_x, seg_y, 2, 2))
                    pygame.draw.rect(surface,
                                     _NS_nyrethzalv.PALETTE["chain_dark"],
                                     (seg_x, seg_y, 1, 1))
    def _draw_robe_torso(surface, cx, cy, facing, phase):
        """Female torso with corset/dark robe."""
        breath = math.sin(phase * 0.7) * 1
        # Base torso silhouette
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
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_dark"], torso_pts)
        # Corset/robe covering (dark purple)
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_darkest"], [
            (cx - 8, cy - 3),
            (cx - 9, cy + 1),
            (cx - 8, cy + 6),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 8, cy + 6),
            (cx + 9, cy + 1),
            (cx + 8, cy - 3),
        ])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_dark"], [
            (cx - 7, cy - 2),
            (cx - 8, cy + 1),
            (cx - 7, cy + 5),
            (cx - 4, cy + 8),
            (cx + 4, cy + 8),
            (cx + 7, cy + 5),
            (cx + 8, cy + 1),
            (cx + 7, cy - 2),
        ])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_mid"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 1),
            (cx - 6, cy + 4),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 4),
            (cx + 7, cy + 1),
            (cx + 6, cy - 1),
        ])
        # Highlights (folds)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["robe_light"],
                         (cx - 5, cy), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["robe_light"],
                         (cx + 5, cy), (cx + 5, cy + 6), 1)
        # Skin cleavage/collar area (pale)
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_mid"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_light"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 1, cy - 3),
            (cx - 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_shine"],
                         (cx, cy - 4, 1, 1))
        # Gold trim collar (V-shape)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_dark"],
                         (cx - 4, cy - 3), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_dark"],
                         (cx, cy - 1), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_mid"],
                         (cx - 4, cy - 3), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_light"],
                         (cx - 3, cy - 3), (cx, cy - 2), 1)
        # Central gem (magenta)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                         (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                         (cx, cy, 2, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                         (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                         (cx, cy, 1, 1))
        # Corset lacing (gold threads)
        for i in range(3):
            ly = cy + 2 + i * 2
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_dark"],
                             (cx - 2, ly), (cx + 2, ly + 1), 1)
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_light"],
                             (cx - 2, ly + 1), (cx + 2, ly), 1)
        # Gold belt at waist
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_dark"],
                         (cx - 6, cy + 8, 12, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_mid"],
                         (cx - 6, cy + 8, 12, 1))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_light"],
                         (cx - 5, cy + 8, 10, 1))
        # Buckle (magenta gem)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                         (cx - 1, cy + 8, 3, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                         (cx, cy + 8, 1, 1))
        # SHOULDER SPIKES (dark angel shoulder guards)
        for side in (-1, 1):
            paul_x = cx + side * 9
            paul_y = cy - 5
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"], [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 3, paul_y + 5),
                (paul_x - 3, paul_y + 5),
            ])
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_darkest"], [
                (paul_x - 3, paul_y - 1),
                (paul_x + 3, paul_y - 1),
                (paul_x + 3, paul_y + 4),
                (paul_x - 3, paul_y + 4),
            ])
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_dark"], [
                (paul_x - 2, paul_y - 1),
                (paul_x + 2, paul_y - 1),
                (paul_x + 2, paul_y + 3),
                (paul_x - 2, paul_y + 3),
            ])
            # Gold trim
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["gold_mid"],
                             (paul_x - 3, paul_y - 1),
                             (paul_x + 3, paul_y - 1), 1)
            # Small spike upward
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"], [
                (paul_x, paul_y - 5),
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
            ])
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_darkest"], [
                (paul_x, paul_y - 4),
                (paul_x - 1, paul_y),
                (paul_x + 1, paul_y),
            ])
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["chain_light"], [
                (paul_x, paul_y - 3),
                (paul_x, paul_y),
                (paul_x + 1, paul_y),
            ])
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_shine"],
                             (paul_x, paul_y - 3, 1, 1))
    def _draw_flowing_skirt(surface, cx, cy, facing, phase, action):
        """Long flowing gothic skirt (dangling)."""
        sway1 = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7) * 2
        # Skirt shape - flares outward and hangs down
        skirt_pts = [
            (cx - 7, cy),
            (cx - 10 + int(sway1 * 0.3), cy + 8),
            (cx - 13 + int(sway1 * 0.6), cy + 18),
            (cx - 15 + int(sway1), cy + 26),
            (cx - 12 + int(sway1 * 0.9), cy + 32),
            (cx - 6 + int(sway2 * 0.5), cy + 36),
            (cx + int(sway2), cy + 38),
            (cx + 6 + int(sway2 * 0.5), cy + 36),
            (cx + 12 + int(sway1 * 0.9), cy + 32),
            (cx + 15 + int(sway1), cy + 26),
            (cx + 13 + int(sway1 * 0.6), cy + 18),
            (cx + 10 + int(sway1 * 0.3), cy + 8),
            (cx + 7, cy),
        ]
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in skirt_pts])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_darkest"], skirt_pts)
        # Inner layer (slightly smaller)
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["robe_dark"], [
            (cx - 6, cy + 1),
            (cx - 9 + int(sway1 * 0.3), cy + 8),
            (cx - 11 + int(sway1 * 0.6), cy + 18),
            (cx - 12 + int(sway1), cy + 26),
            (cx - 9 + int(sway1 * 0.9), cy + 30),
            (cx - 4 + int(sway2 * 0.5), cy + 34),
            (cx + int(sway2), cy + 35),
            (cx + 4 + int(sway2 * 0.5), cy + 34),
            (cx + 9 + int(sway1 * 0.9), cy + 30),
            (cx + 12 + int(sway1), cy + 26),
            (cx + 11 + int(sway1 * 0.6), cy + 18),
            (cx + 9 + int(sway1 * 0.3), cy + 8),
            (cx + 6, cy + 1),
        ])
        # Vertical fold highlights
        for fold_x_off in (-8, -4, 0, 4, 8):
            fold_x_top = cx + fold_x_off
            fold_x_bot = cx + fold_x_off + int(sway1 * (abs(fold_x_off) / 8))
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["robe_mid"],
                             (fold_x_top, cy + 4), (fold_x_bot, cy + 32), 1)
            if fold_x_off in (-4, 4):
                pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["robe_light"],
                                 (fold_x_top, cy + 4),
                                 (fold_x_bot, cy + 28), 1)
        # Bottom hem (torn tattered edge)
        for i, ex in enumerate(range(-13, 15, 3)):
            ex_x = cx + ex + int(sway1 * 0.8)
            ex_y = cy + 34 + int(math.sin(i) * 2)
            # Tatters
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["robe_darkest"],
                             (ex_x, ex_y), (ex_x, ex_y + 3 + (i % 2)), 1)
        # Gold trim at bottom hem
        for i, ex in enumerate(range(-12, 14, 4)):
            ex_x = cx + ex + int(sway1 * 0.8)
            ex_y = cy + 33
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_dark"],
                             (ex_x, ex_y, 2, 1))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_light"],
                             (ex_x, ex_y, 1, 1))
        # Magic glow at bottom edges
        for edge_x_off in (-13, -6, 0, 6, 13):
            edge_x = cx + edge_x_off + int(sway1 * 0.7)
            edge_y = cy + 34
            glow_alpha = _NS_nyrethzalv._alpha(120 + math.sin(phase * 2 + edge_x_off) * 40)
            pygame.draw.rect(surface,
                             (*_NS_nyrethzalv.PALETTE["magic_dark"], glow_alpha),
                             (edge_x, edge_y, 1, 2))
            pygame.draw.rect(surface,
                             (*_NS_nyrethzalv.PALETTE["magic_light"], glow_alpha),
                             (edge_x, edge_y + 1, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm — hanging or gesturing subtly."""
        back_shoulder_x = cx - facing * 5
        back_shoulder_y = cy - 2
        # Slight gesture
        arm_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.1
        arm_length = 12
        back_hand_x = back_shoulder_x - int(math.cos(arm_angle) * arm_length) * facing
        back_hand_y = back_shoulder_y + int(math.sin(arm_angle) * arm_length)
        elbow_x = back_shoulder_x - int(math.cos(arm_angle) * (arm_length * 0.5)) * facing
        elbow_y = back_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.5))
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 4)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_mid"],
                         (back_shoulder_x - 1, back_shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 4)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 2)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (back_hand_x - 1, back_hand_y), 1)
        # Small hand (pale skin)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_dark"],
                         (back_hand_x - 1, back_hand_y, 3, 3))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_mid"],
                         (back_hand_x - 1, back_hand_y, 2, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_light"],
                         (back_hand_x, back_hand_y, 1, 1))
        # Small magic wisp at hand
        magic_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_nyrethzalv._alpha(100 * (3 - r) / 3 * magic_pulse)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                     (back_hand_x, back_hand_y + 1), r)
    def _draw_casting_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - extended forward with palm out for casting."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 2
        if action == "attack":
            if attack_progress < 0.4:
                t = attack_progress / 0.4
                arm_angle = -math.pi * 0.15 * (1 - t) - math.pi * 0.3 * t
            elif attack_progress < 0.6:
                t = (attack_progress - 0.4) / 0.2
                arm_angle = -math.pi * 0.3 + math.pi * 0.4 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.1 * (1 - t)
        else:
            # Extended palm-out casting pose
            arm_angle = math.pi * 0.05 + math.sin(phase * 0.5) * 0.08
        arm_length = 14
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 2
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 1
        # Upper arm
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_mid"],
                         (shoulder_x - 1, shoulder_y), (elbow_x - 1, elbow_y), 2)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_light"],
                         (shoulder_x - 1, shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Forearm
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 5)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (hand_x - 1, hand_y), 2)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_light"],
                         (elbow_x - 1, elbow_y + 1),
                         (hand_x - 1, hand_y - 1), 1)
        # Palm (open hand facing forward)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                         (hand_x - 2, hand_y - 1, 5, 5))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                         (hand_x - 2, hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_dark"],
                         (hand_x - 2, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_mid"],
                         (hand_x - 1, hand_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_light"],
                         (hand_x, hand_y - 1, 2, 1))
        # Slim fingers
        for i in range(3):
            finger_x = hand_x + facing * (2 + i)
            finger_y = hand_y + i
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                             (hand_x + facing * 1, hand_y + i),
                             (finger_x, finger_y - 1), 1)
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_light"],
                             (finger_x, finger_y - 1, 1, 1))
        # MAGIC ORB in palm (glowing purple)
        orb_x = hand_x + facing * 3
        orb_y = hand_y + 1
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Idle: small glow / Attack: bigger charge glow
        if action == "attack":
            orb_size = int(3 + math.sin(attack_progress * math.pi) * 4)
        else:
            orb_size = 3
        for r in range(orb_size + 5, 0, -1):
            alpha = _NS_nyrethzalv._alpha(150 * (orb_size + 5 - r) / (orb_size + 5) * pulse)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                     (orb_x, orb_y), r)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                                 (orb_x, orb_y), orb_size)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                                 (orb_x, orb_y), orb_size - 1)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                                 (orb_x, orb_y), max(1, orb_size - 2))
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                 (orb_x, orb_y), max(1, orb_size - 3))
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_hot"],
                                 (orb_x, orb_y), max(1, orb_size - 4))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                         (orb_x, orb_y, 1, 1))
        # Sparkles around orb
        for i in range(4):
            spark_angle = phase * 3 + i * math.pi / 2
            sx = orb_x + int(math.cos(spark_angle) * (orb_size + 3))
            sy = orb_y + int(math.sin(spark_angle) * (orb_size + 3))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_hot"],
                             (sx, sy, 1, 1))
    def _draw_dark_angel_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Beautiful female head with long black hair + crown."""
        # Head oval
        head_pts = [
            (cx - 6, cy + 2),
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 3, cy - 9),
            (cx + 6, cy - 6),
            (cx + 7, cy - 2),
            (cx + 6, cy + 3),
            (cx + 3, cy + 6),
            (cx - 2, cy + 6),
            (cx - 5, cy + 4),
        ]
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_pts])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_darkest"], head_pts)
        # Face (pale skin)
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_dark"], [
            (cx - 5, cy + 1),
            (cx - 5, cy - 5),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 5, cy - 5),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 2, cy + 5),
            (cx - 3, cy + 5),
        ])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 3, cy - 5),
            (cx, cy - 7),
            (cx + 3, cy - 7),
            (cx + 5, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx, cy + 4),
            (cx - 2, cy + 2),
        ])
        # Highlights
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["skin_light"], [
            (cx + 1, cy - 5),
            (cx + 3, cy - 5),
            (cx + 4, cy - 3),
            (cx + 2, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_shine"],
                         (cx + facing * 2, cy - 4, 1, 1))
        # LONG BLACK HAIR (long, flowing behind and around)
        _NS_nyrethzalv._draw_long_hair(surface, cx, cy, facing, phase)
        # SMALL HORN CROWN
        _NS_nyrethzalv._draw_horn_crown(surface, cx, cy - 5, facing, phase)
        # GLOWING PURPLE EYES
        _NS_nyrethzalv._draw_fallen_eyes(surface, cx, cy - 3, facing, phase, action)
        # Nose shadow
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["skin_darkest"],
                         (cx + facing, cy - 1, 1, 1))
        # LIPS (dark purple)
        _NS_nyrethzalv._draw_lips(surface, cx, cy + 3, facing, phase, action, attack_progress)
    def _draw_long_hair(surface, cx, cy, facing, phase):
        """Long flowing black hair."""
        sway1 = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7) * 2
        # Main hair mass (behind + around head, flows down)
        hair_bulk = [
            (cx - 7, cy - 6),
            (cx - 10, cy - 3),
            (cx - 12, cy + 3),
            (cx - 13, cy + 10 + int(sway2 * 0.5)),
            (cx - 12, cy + 18 + int(sway2)),
            (cx - 9, cy + 24 + int(sway1)),
            (cx - 4, cy + 26 + int(sway1 * 0.8)),
            (cx + 2, cy + 25 + int(sway1 * 0.6)),
            (cx + 7, cy + 22 + int(sway1 * 0.5)),
            (cx + 10, cy + 16 + int(sway2)),
            (cx + 11, cy + 8 + int(sway2 * 0.5)),
            (cx + 8, cy + 2),
            (cx + 7, cy - 3),
            (cx + 4, cy - 8),
            (cx - 2, cy - 9),
            (cx - 6, cy - 8),
        ]
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in hair_bulk])
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["hair_darkest"], hair_bulk)
        # Mid tone
        _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["hair_dark"], [
            (cx - 6, cy - 5),
            (cx - 9, cy - 2),
            (cx - 11, cy + 3),
            (cx - 11, cy + 10 + int(sway2 * 0.4)),
            (cx - 10, cy + 18 + int(sway2 * 0.8)),
            (cx - 7, cy + 22 + int(sway1 * 0.8)),
            (cx - 3, cy + 22 + int(sway1 * 0.6)),
            (cx + 2, cy + 20 + int(sway1 * 0.5)),
            (cx + 7, cy + 15 + int(sway2 * 0.8)),
            (cx + 9, cy + 8 + int(sway2 * 0.4)),
            (cx + 8, cy + 3),
            (cx + 6, cy - 4),
            (cx + 3, cy - 7),
            (cx - 2, cy - 8),
        ])
        # Highlight strands
        for i, (x_off, y_start, length) in enumerate([
            (-8, -2, 20), (-4, -6, 24), (2, -6, 22), (6, -3, 18),
        ]):
            for dy in range(length):
                if dy % 4 == 0:
                    hx = cx + x_off + int(math.sin(phase * 0.3 + i + dy * 0.2) * 0.5)
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["hair_mid"],
                                     (hx, hy, 1, 1))
                elif dy % 7 == 0:
                    hx = cx + x_off
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["hair_light"],
                                     (hx, hy, 1, 1))
                elif dy % 11 == 0:
                    hx = cx + x_off
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["hair_shine"],
                                     (hx, hy, 1, 1))
        # Bangs falling over forehead
        for i in range(4):
            bx = cx - 3 + i * 2
            by_top = cy - 8
            by_bot = cy - 4 + (i % 2)
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["hair_darkest"],
                             (bx, by_top), (bx, by_bot), 1)
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["hair_dark"],
                             (bx + 1, by_top), (bx + 1, by_bot - 1), 1)
    def _draw_horn_crown(surface, cx, cy, facing, phase):
        """Small gold crown/horn accents on head."""
        # Central taller spike + 2 side spikes
        for i, (x_off, height) in enumerate([
            (-4, 4), (-2, 6), (0, 7), (2, 6), (4, 4),
        ]):
            sway = math.sin(phase * 0.4 + i * 0.3) * 0.5
            base_x = cx + x_off
            base_y = cy
            tip_x = cx + x_off + int(sway)
            tip_y = cy - height
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x - 1, base_y + 1),
                (base_x + 2, base_y + 1),
            ])
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["gold_dark"], [
                (tip_x, tip_y), (base_x - 1, base_y), (base_x + 1, base_y),
            ])
            _NS_nyrethzalv._poly(surface, _NS_nyrethzalv.PALETTE["gold_mid"], [
                (tip_x, tip_y),
                (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)),
                (base_x, base_y),
            ])
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["gold_shine"],
                             (tip_x, tip_y, 1, 1))
        # Central gem on crown band
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_dark"], (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_mid"], (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_light"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"], (cx, cy, 1, 1))
    def _draw_fallen_eyes(surface, cx, cy, facing, phase, action):
        """Both purple glowing eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.5 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 2 + (1 if facing == 1 else -1)
            ey = cy
            # Socket shadow
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Purple glow halo
            for radius in range(5, 0, -1):
                alpha = _NS_nyrethzalv._alpha(90 * (5 - radius) / 5 * pulse * intensity)
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["eye_mid"], alpha),
                                         (ex, ey), radius)
            # Eye
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
        # Eye shadow / makeup (dark eyeshadow under eyes)
        pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                         (cx - 3, cy - 2), (cx + 3, cy - 2), 1)
    def _draw_lips(surface, cx, cy, facing, phase, action, attack_progress):
        """Dark purple lips."""
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 2)
        if mouth_open > 0:
            # Slightly open (casting)
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                             (cx - 2, cy, 4, int(mouth_open) + 1))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                             (cx - 2, cy, 4, int(mouth_open)))
        # Lips (always visible)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                         (cx - 2, cy - 1, 4, 1))
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                         (cx - 1, cy - 1, 3, 1))
        # Highlight center of lip
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                         (cx, cy - 1, 1, 1))
    # ============================================================
    # RANGED ATTACK — SHADOW ORB PROJECTILE
    # ============================================================
    def _draw_shadow_projectile(surface, boss, x, y, progress):
        """Purple shadow orb with comet trail from palm."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_nyrethzalv._target_position(boss, x, y)
        # Launch from palm
        start_x = x + facing * 22
        start_y = y - 4
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Long comet trail
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyrethzalv._alpha(240 - i * 24)
            size = max(1, 8 - i)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                                     (px, py), size)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                     (px, py), max(1, size - 2))
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                     (px, py), max(1, size - 3))
            # Sparks
            if i < 5:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright head
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                                 (bx, by), 9)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                                 (bx, by), 7)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                                 (bx, by), 5)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                 (bx, by), 3)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_hot"],
                                 (bx, by), 2)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                                 (bx, by), 1)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["white"], (bx, by, 1, 1))
        for r in range(14, 3, -2):
            alpha = _NS_nyrethzalv._alpha(80 * (14 - r) / 14)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                     (bx, by), r)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 26)
            alpha = _NS_nyrethzalv._alpha(240 * (1 - st))
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                     (tx, ty), radius, 3)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                     (tx, ty), max(1, radius - 5), 2)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                     (tx, ty), max(1, radius - 12), 1)
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SHADOW MIST (ambient)
    # ============================================================
    def _draw_shadow_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 55), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(40, 3, -3):
            alpha = _NS_nyrethzalv._alpha((40 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                    (80 - radius * 2, 27 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(26, 3, -2):
            alpha = _NS_nyrethzalv._alpha((26 - radius) * 3.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                    (80 - radius, 27 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 12))
        # Rising purple wisps
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_nyrethzalv._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                     (sx, sy), 3)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Sparkles
        for i in range(10):
            ember_t = (phase * 0.6 + i * 0.15) % 1.0
            ex = cx - 28 + i * 6 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 24)
            alpha = _NS_nyrethzalv._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 1, 1))
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyrethzalv._alpha(160 - i * 24)
                if alpha <= 0:
                    continue
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                                         (sx, sy), max(2, 7 - i))
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                         (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT (TRUE BOSS scale)
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        for radius in range(15, 0, -1):
            alpha = max(0, (15 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 130 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 2, 10, 170), (10, 10, 130, 12))
        pygame.draw.ellipse(shadow, (25, 8, 45, 110), (18, 12, 114, 8))
        surface.blit(shadow, (x - 75, y - 15 + hover_offset))
    def _draw_shadow_aura(surface, x, y, phase):
        """Massive shadow purple aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_nyrethzalv._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyrethzalv._aacircle(aura,
                                         (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                                         (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_nyrethzalv._alpha((70 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nyrethzalv._aacircle(aura,
                                         (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                         (120, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_nyrethzalv._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyrethzalv._aacircle(aura,
                                         (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                         (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Falling feathers (ambient)
        for i in range(8):
            fall_t = (phase * 0.3 + i * 0.12) % 1.0
            fx = x - 60 + i * 15 + int(math.sin(phase + i) * 8)
            fy = y - 40 + int(fall_t * 80)
            alpha = _NS_nyrethzalv._alpha(200 * (1 - fall_t))
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["feather_dark"], alpha),
                                 (fx, fy, 2, 3))
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                 (fx, fy, 1, 1))
        # Floating magic particles
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large ground rune ring (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyrethzalv.PALETTE["magic_darkest"], 210),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_nyrethzalv.PALETTE["magic_dark"], 230),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_nyrethzalv.PALETTE["magic_mid"], 220),
                            (25, 24, 130, 20), 1)
        # Pentagram-like runes
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 32 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 32 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_nyrethzalv.PALETTE["magic_light"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_nyrethzalv.PALETTE["magic_hot"],
                                 _NS_nyrethzalv._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q: DARK BINDING (chain to target)
    # ============================================================
    def _draw_darkbinding_foreground(surface, boss, x, y, timer, phase):
        """Chain projectile that binds target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyrethzalv._target_position(boss, x, y)
        if progress < 0.25:
            # Charge in palm
            t = progress / 0.25
            palm_x = x + facing * 22
            palm_y = y - 4
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_nyrethzalv._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                                         (palm_x, palm_y), r)
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                                     (palm_x, palm_y), cr - 1)
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                                     (palm_x, palm_y), max(1, cr - 3))
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                     (palm_x, palm_y), max(1, cr - 4))
        elif progress < 0.75:
            # Chain extends to target
            t = (progress - 0.25) / 0.5
            start_x = x + facing * 24
            start_y = y - 4
            end_t = min(1.0, t * 1.5)
            end_x = int(start_x + (tx - start_x) * end_t)
            end_y = int(start_y + (ty - start_y) * end_t)
            # Draw chain (segmented links)
            _NS_nyrethzalv._draw_chain_beam(surface, start_x, start_y, end_x, end_y, phase)
            # Star burst at target when arrived
            if end_t >= 0.99:
                _NS_nyrethzalv._draw_star_stun(surface, tx, ty, phase)
        else:
            # Hold/stun phase - chain persistent
            t = (progress - 0.75) / 0.25
            start_x = x + facing * 24
            start_y = y - 4
            _NS_nyrethzalv._draw_chain_beam(surface, start_x, start_y, tx, ty, phase)
            _NS_nyrethzalv._draw_star_stun(surface, tx, ty, phase)
    def _draw_chain_beam(surface, sx, sy, ex, ey, phase):
        """Chain of dark magic links from sx,sy to ex,ey."""
        length = math.hypot(ex - sx, ey - sy)
        if length < 5:
            return
        dx = (ex - sx) / length
        dy = (ey - sy) / length
        perp_x = -dy
        perp_y = dx
        num_links = max(3, int(length / 8))
        for i in range(num_links):
            t = i / max(1, num_links - 1)
            lx = int(sx + (ex - sx) * t)
            ly = int(sy + (ey - sy) * t)
            # Slight wave
            wave = math.sin(phase * 4 + i * 0.5) * 2
            lx += int(perp_x * wave)
            ly += int(perp_y * wave)
            # Chain link (small oval)
            if i % 2 == 0:
                _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["shadow_deep"],
                                         (lx, ly), 3)
                _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                                         (lx, ly), 3)
                _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                                         (lx, ly), 2)
                pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                 (lx, ly, 1, 1))
                pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                                 (lx, ly, 1, 1))
            else:
                _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                                         (lx, ly), 2)
                _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                                         (lx, ly), 1)
        # Glow along chain path
        for i in range(num_links * 2):
            gt = i / max(1, num_links * 2 - 1)
            gx = int(sx + (ex - sx) * gt)
            gy = int(sy + (ey - sy) * gt)
            spark_alpha = _NS_nyrethzalv._alpha(120 + math.sin(phase * 6 + i) * 60)
            pygame.draw.rect(surface,
                             (*_NS_nyrethzalv.PALETTE["magic_hot"], spark_alpha),
                             (gx, gy, 1, 1))
    def _draw_star_stun(surface, tx, ty, phase):
        """Purple star above stunned target."""
        # Big star shape
        star_y = ty - 20
        pulse = math.sin(phase * 3) * 0.4 + 0.6
        # 5-point star
        for i in range(5):
            angle = -math.pi / 2 + i * math.pi * 2 / 5
            inner_angle = angle + math.pi / 5
            outer_x = tx + int(math.cos(angle) * 8)
            outer_y = star_y + int(math.sin(angle) * 8)
            inner_x = tx + int(math.cos(inner_angle) * 4)
            inner_y = star_y + int(math.sin(inner_angle) * 4)
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                             (tx, star_y), (outer_x, outer_y), 3)
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                             (tx, star_y), (outer_x, outer_y), 2)
            pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                             (tx, star_y), (outer_x, outer_y), 1)
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                             (outer_x, outer_y, 1, 1))
        # Center glow
        for r in range(6, 0, -1):
            alpha = _NS_nyrethzalv._alpha(180 * (6 - r) / 6 * pulse)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                     (tx, star_y), r)
        _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                                 (tx, star_y), 2)
        pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["white"], (tx, star_y, 1, 1))
    # ============================================================
    # SKILL W: TORRENT OF SHADOWS (AoE at target)
    # ============================================================
    def _draw_torrent_ground(surface, boss, x, y, timer, phase):
        """Ground vortex at target."""
        tx, ty = _NS_nyrethzalv._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            # Vortex ellipse
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["magic_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["magic_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["magic_mid"], 150),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["void_dark"], 200),
                                (tx - r + 15, ty - r // 3 + 8,
                                 r * 2 - 30, r * 2 // 3 - 16))
            # Spiral runes
            for i in range(12):
                angle = phase * 3 + i * math.pi / 6
                spiral_r = int(r * (0.4 + (i % 3) * 0.15))
                x1 = tx + int(math.cos(angle) * spiral_r)
                y1 = ty + int(math.sin(angle) * spiral_r * 0.4)
                pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                 (x1, y1, 2, 2))
                pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                                 (x1, y1, 1, 1))
    def _draw_torrent_foreground(surface, boss, x, y, timer, phase):
        """Spiraling shadow tendrils rising from the vortex."""
        tx, ty = _NS_nyrethzalv._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r < 5:
            return
        # Rising shadow tendrils (spiral upward)
        num_tendrils = 8
        for i in range(num_tendrils):
            for layer in range(6):
                layer_t = (phase * 0.8 + i * 0.15 + layer * 0.15) % 1.0
                tendril_angle = i * math.pi * 2 / num_tendrils + phase * 2 + layer_t * math.pi
                spiral_r = r * (1 - layer_t * 0.4)
                tx_offset = int(math.cos(tendril_angle) * spiral_r * 0.6)
                ty_offset = int(math.sin(tendril_angle) * spiral_r * 0.25)
                ty_up = ty + ty_offset - int(layer_t * 22)
                tx_final = tx + tx_offset
                alpha = _NS_nyrethzalv._alpha(220 * (1 - layer_t))
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_darkest"], alpha),
                                         (tx_final, ty_up), 4)
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                         (tx_final, ty_up), 3)
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                         (tx_final, ty_up), 2)
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                 (tx_final, ty_up, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                                 (tx_final, ty_up - 1, 1, 1))
        # Central dark energy (void core)
        core_pulse = math.sin(phase * 4) * 0.3 + 0.7
        for r_core in range(10, 0, -1):
            alpha = _NS_nyrethzalv._alpha(200 * (10 - r_core) / 10 * core_pulse)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["void_dark"], alpha),
                                     (tx, ty), r_core)
        # Damage numbers (rising 75 like screenshot)
        for i in range(3):
            num_t = (phase * 0.5 + i * 0.35) % 1.0
            nx = tx - 20 + i * 20
            ny = ty - 20 - int(num_t * 30)
            alpha = _NS_nyrethzalv._alpha(240 * (1 - num_t))
            # Simulated number "impact indicator"
            pygame.draw.rect(surface, (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                             (nx, ny, 3, 3))
            pygame.draw.rect(surface, (*_NS_nyrethzalv.PALETTE["magic_shine"], alpha),
                             (nx, ny, 2, 2))
    # ============================================================
    # SKILL E: BLACK SHIELD (bubble around boss)
    # ============================================================
    def _draw_blackshield_ground(surface, boss, x, y, timer, phase):
        """Rings under boss during shield."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(35 + i * 10 + math.sin(phase * 2) * 4)
            alpha = _NS_nyrethzalv._alpha(220 - i * 60)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha),
                                     (x, y + 42), r, 2)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                     (x, y + 42), r, 1)
    def _draw_blackshield_bubble(surface, boss, x, y, timer, phase):
        """Purple bubble shield around boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Multi-ring shield
        for i, (thickness, alpha_val) in enumerate([
            (3, 130), (2, 170), (1, 210),
        ]):
            _NS_nyrethzalv._aacircle(bubble,
                                     (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha_val),
                                     center, r - i, thickness)
            _NS_nyrethzalv._aacircle(bubble,
                                     (*_NS_nyrethzalv.PALETTE["magic_mid"], alpha_val),
                                     center, r - i - 1, 1)
        # Rotating sparkles
        for i in range(22):
            angle = phase * 1.5 + i * math.pi / 11
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_nyrethzalv.PALETTE["magic_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_nyrethzalv.PALETTE["magic_hot"], (sx, sy, 1, 1))
        # Inner runes/stars orbiting
        for i in range(6):
            angle = -phase * 0.8 + i * math.pi / 3
            inner_r = r - 12
            sx = center[0] + int(math.cos(angle) * inner_r)
            sy = center[1] + int(math.sin(angle) * inner_r)
            # Small star
            for a in range(4):
                sa = angle * 0.5 + a * math.pi / 2
                spx = sx + int(math.cos(sa) * 2)
                spy = sy + int(math.sin(sa) * 2)
                pygame.draw.rect(bubble, _NS_nyrethzalv.PALETTE["magic_light"],
                                 (spx, spy, 1, 1))
            pygame.draw.rect(bubble, _NS_nyrethzalv.PALETTE["magic_shine"], (sx, sy, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Central mystic ball inside shield
        core_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r_core in range(6, 0, -1):
            alpha = _NS_nyrethzalv._alpha(200 * (6 - r_core) / 6 * core_pulse)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_hot"], alpha),
                                     (x, y - 8), r_core)
    # ============================================================
    # SKILL R: SOUL SHACKLES (multi-chain to enemies)
    # ============================================================
    def _draw_soulshackles_ground(surface, boss, x, y, timer, phase):
        """Ground rune network."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["magic_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["magic_dark"], 200),
                                (x - r + 4, y + 40 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_nyrethzalv.PALETTE["magic_mid"], 220),
                                (x - r + 10, y + 40 - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 2)
            # Rune spokes
            for i in range(16):
                angle = phase * 0.4 + i * math.pi / 8
                x1 = x + int(math.cos(angle) * r)
                y1 = y + 40 + int(math.sin(angle) * r * 0.4)
                x2 = x + int(math.cos(angle) * (r - 10))
                y2 = y + 40 + int(math.sin(angle) * (r - 10) * 0.4)
                pygame.draw.line(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_soulshackles_foreground(surface, boss, x, y, timer, phase):
        """Multiple chains extending from boss to 3-4 target points around."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Center is boss's palm
        cx_hand = x + boss.direction * 22
        cy_hand = y - 4
        # 4 shackle points arranged in a ring around boss
        num_shackles = 4
        radius = 80 + int(math.sin(phase * 1.5) * 8)
        for i in range(num_shackles):
            angle = phase * 0.3 + i * math.pi * 2 / num_shackles
            ex = x + int(math.cos(angle) * radius)
            ey = y + int(math.sin(angle) * radius * 0.5)
            # Draw chain from hand to shackle point
            _NS_nyrethzalv._draw_chain_beam(surface, cx_hand, cy_hand, ex, ey, phase + i)
            # Shackle sphere at end (dark orb)
            for r in range(8, 0, -1):
                alpha = _NS_nyrethzalv._alpha(180 * (8 - r) / 8)
                _NS_nyrethzalv._aacircle(surface,
                                         (*_NS_nyrethzalv.PALETTE["magic_dark"], alpha),
                                         (ex, ey), r)
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_darkest"],
                                     (ex, ey), 5)
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_dark"],
                                     (ex, ey), 3)
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_mid"],
                                     (ex, ey), 2)
            _NS_nyrethzalv._aacircle(surface, _NS_nyrethzalv.PALETTE["magic_light"],
                                     (ex, ey), 1)
            pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"], (ex, ey, 1, 1))
        # Draw connecting chains BETWEEN shackle points (forms a ring/pentagon)
        for i in range(num_shackles):
            a1 = phase * 0.3 + i * math.pi * 2 / num_shackles
            a2 = phase * 0.3 + (i + 1) * math.pi * 2 / num_shackles
            p1_x = x + int(math.cos(a1) * radius)
            p1_y = y + int(math.sin(a1) * radius * 0.5)
            p2_x = x + int(math.cos(a2) * radius)
            p2_y = y + int(math.sin(a2) * radius * 0.5)
            _NS_nyrethzalv._draw_chain_beam(surface, p1_x, p1_y, p2_x, p2_y,
                                            phase * 2 + i)
        # Central hand glow (channeling)
        for r in range(10, 0, -1):
            alpha = _NS_nyrethzalv._alpha(180 * (10 - r) / 10)
            _NS_nyrethzalv._aacircle(surface,
                                     (*_NS_nyrethzalv.PALETTE["magic_light"], alpha),
                                     (cx_hand, cy_hand), r)
        # Damage pulses along all chains
        pulse_intensity = math.sin(phase * 5) * 0.5 + 0.5
        if pulse_intensity > 0.7:
            # Chain "flash" effect
            for i in range(num_shackles):
                angle = phase * 0.3 + i * math.pi * 2 / num_shackles
                ex = x + int(math.cos(angle) * radius)
                ey = y + int(math.sin(angle) * radius * 0.5)
                # Extra spark
                for spark_i in range(4):
                    sa = spark_i * math.pi / 2
                    sx_off = ex + int(math.cos(sa) * 4)
                    sy_off = ey + int(math.sin(sa) * 4)
                    pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_hot"],
                                     (sx_off, sy_off, 2, 2))
                    pygame.draw.rect(surface, _NS_nyrethzalv.PALETTE["magic_shine"],
                                     (sx_off, sy_off, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_morthyrax(surface, boss, x, y):
    """Entry point morthyrax."""
    return _NS_morthyrax.draw_morthyrax(surface, boss, x, y)


def draw_sanguiveth(surface, boss, x, y):
    """Entry point sanguiveth."""
    return _NS_sanguiveth.draw_sanguiveth(surface, boss, x, y)


def draw_xerakhotep(surface, boss, x, y):
    """Entry point xerakhotep."""
    return _NS_xerakhotep.draw_xerakhotep(surface, boss, x, y)


def draw_nyrethzalv(surface, boss, x, y):
    """Entry point nyrethzalv."""
    return _NS_nyrethzalv.draw_nyrethzalv(surface, boss, x, y)
