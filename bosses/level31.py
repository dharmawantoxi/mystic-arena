"""
bosses/level31.py - Semua boss Level 31

Berisi:
  - celwynn   (mini boss - RANGED star caretaker, cosmic light)
  - rynvara   (mini boss - MELEE wild onslaught, primal fire)
  - syrindra  (mini boss - RANGED dark sovereign, shadow magic)
  - ravokkar  (TRUE BOSS - RANGED outlaw king, gunfighter)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _cw_ (celwynn), _rv_ (rynvara), _rk_ (ravokkar) sudah unik.
  - _sy_ (syrindra) di-rename -> _syn_ (bentrok dengan syrentha
    level 6), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# CELWYNN (STAR CARETAKER) - Mini Boss
# ====================================================================

class _NS_celwynn:
    """Namespace celwynn - Star Caretaker mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale, weathered — cosmic being)
        "skin_darkest": (60, 40, 45),
        "skin_dark": (130, 95, 100),
        "skin_mid": (195, 160, 165),
        "skin_light": (235, 210, 210),
        "skin_shine": (255, 240, 240),
        # Beard/hair (fluffy white)
        "hair_darkest": (70, 70, 80),
        "hair_dark": (135, 135, 145),
        "hair_mid": (200, 200, 210),
        "hair_light": (240, 240, 245),
        "hair_shine": (255, 255, 255),
        # Robe (deep red — Bard signature)
        "robe_darkest": (35, 8, 12),
        "robe_dark": (85, 20, 30),
        "robe_mid": (155, 45, 55),
        "robe_light": (215, 90, 95),
        "robe_shine": (245, 155, 155),
        # Leather (belt, straps — dark brown)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (55, 35, 18),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 110, 65),
        # Gold ornaments (rich)
        "gold_darkest": (60, 40, 5),
        "gold_dark": (110, 80, 15),
        "gold_mid": (200, 155, 35),
        "gold_light": (245, 215, 85),
        "gold_shine": (255, 245, 165),
        # Staff metal (dark iron)
        "metal_dark": (20, 20, 25),
        "metal_mid": (60, 60, 70),
        "metal_light": (130, 130, 145),
        # Cosmic gold (chimes, staff orb, aura — signature)
        "chime_darkest": (50, 35, 5),
        "chime_dark": (140, 100, 15),
        "chime_mid": (230, 175, 40),
        "chime_light": (255, 220, 100),
        "chime_hot": (255, 240, 170),
        "chime_shine": (255, 250, 220),
        # Cosmic blue (Q cosmic binding)
        "cosmic_darkest": (5, 15, 55),
        "cosmic_dark": (20, 50, 130),
        "cosmic_mid": (60, 130, 230),
        "cosmic_light": (140, 200, 255),
        "cosmic_hot": (200, 235, 255),
        "cosmic_shine": (240, 250, 255),
        # Cosmic purple (R magical journey portal)
        "portal_darkest": (15, 5, 40),
        "portal_dark": (45, 20, 95),
        "portal_mid": (95, 55, 175),
        "portal_light": (170, 120, 240),
        "portal_hot": (220, 190, 255),
        # Blue meep (small orb companion)
        "meep_dark": (10, 45, 90),
        "meep_mid": (50, 130, 210),
        "meep_light": (140, 210, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_celwynn._clamp(color)
        if _NS_celwynn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_celwynn._clamp(color)
        if _NS_celwynn.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_celwynn._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_celwynn(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_celwynn._detect_moving(boss)
        _NS_celwynn._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_cw_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (starry cosmic)
        _NS_celwynn._draw_cosmic_aura(surface, x, y, pulse)
        _NS_celwynn._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_celwynn._draw_shrine_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_celwynn._draw_tempered_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_celwynn._draw_journey_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_celwynn._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_celwynn._draw_walk(surface, boss, x, y)
        else:
            _NS_celwynn._draw_idle(surface, boss, x, y)
        # Orbiting chimes/meeps
        _NS_celwynn._draw_orbiting_chimes(surface, boss, x, y, pulse)
        # Foreground skill FX
        if active_skill == "q":
            _NS_celwynn._draw_cosmic_binding(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_celwynn._draw_shrine_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_celwynn._draw_tempered_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_celwynn._draw_journey_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_cw_previous_timer", 0))
        active = bool(getattr(boss, "_cw_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._cw_attack_active = True
            boss._cw_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._cw_attack_frame = int(getattr(boss, "_cw_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._cw_attack_active = False
            boss._cw_attack_frame = 0
            active = False
        boss._cw_previous_timer = timer
        boss._cw_attack_progress = (
            min(1.0, getattr(boss, "_cw_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_cw_last_x"):
            boss._cw_last_x = boss.x
            boss._cw_last_y = boss.y
            return False
        dx = abs(boss.x - boss._cw_last_x)
        dy = abs(boss.y - boss._cw_last_y)
        boss._cw_last_x = boss.x
        boss._cw_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 4)
        _NS_celwynn._draw_shadow(surface, x, y + 50)
        _NS_celwynn._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Floating - smooth bob + star sparkles trail
        phase = boss.pulse * 1.8
        float_bob = int(math.sin(phase * 1.0) * 6)
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_celwynn._draw_shadow(surface, x + sway, y + 50, faded=True)
        _NS_celwynn._draw_star_trail(surface, x + sway, y + 40, phase,
                                      boss.direction)
        _NS_celwynn._draw_body(surface, x + sway, y + float_bob - 4,
                                boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_cw_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Ranged cast — raise staff → release bolt → recovery
        if progress < 0.4:
            # Charge — pull staff back slightly, lift
            t = progress / 0.4
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            # Fire — push forward
            t = (progress - 0.4) / 0.20
            lunge = int((-2 + t * 6)) * boss.direction
            lift = int(3 - t * 2)
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            lunge = int(4 * (1 - t)) * boss.direction
            lift = int(1 - t * 1)
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_celwynn._draw_shadow(surface, x + lunge, y + 50)
        _NS_celwynn._draw_body(surface, x + lunge, y - lift + bob,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_celwynn._draw_basic_bolt(surface, boss, x + lunge, y - lift + bob,
                                      progress)
    # ============================================================
    # BODY (Chubby caretaker with staff)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered: back arm → legs → robe → torso → beard → head → staff arm + staff."""
        # Rear arm (behind)
        _NS_celwynn._draw_rear_arm(surface, cx, cy, facing, phase, action)
        # Legs (small stubby)
        _NS_celwynn._draw_legs(surface, cx, cy + 14, facing, phase, action)
        # Robe body (chubby round)
        _NS_celwynn._draw_robe_body(surface, cx, cy, facing, phase)
        # Belt + ornaments
        _NS_celwynn._draw_belt(surface, cx, cy + 10, facing, phase)
        # Head (small compared to body)
        _NS_celwynn._draw_head(surface, cx + facing * 1, cy - 8, facing,
                                phase, action)
        # BIG fluffy beard (covers most of face and chest)
        _NS_celwynn._draw_big_beard(surface, cx, cy - 4, facing, phase)
        # Front arm holds STAFF (main weapon)
        _NS_celwynn._draw_staff_arm(surface, cx, cy, facing, phase, action,
                                     attack_progress)
    def _draw_rear_arm(surface, cx, cy, facing, phase, action):
        """Back arm — usually gestures or holds a chime."""
        back = -facing
        shoulder = (cx + back * 5, cy - 4)
        gesture = math.sin(phase * 0.8) * 2
        elbow = (shoulder[0] + back * 3, shoulder[1] + 4 + int(gesture))
        hand = (elbow[0] + back * 3, elbow[1] + 4)
        # Robe sleeve
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["robe_darkest"],
                             shoulder, elbow, 5)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["robe_dark"],
                             shoulder, elbow, 4)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["robe_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Forearm (leather bracer)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_darkest"],
                             elbow, hand, 4)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_dark"],
                             elbow, hand, 3)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_mid"],
                             (elbow[0], elbow[1] - 1),
                             (hand[0], hand[1] - 1), 1)
        # Gold trim
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["gold_mid"],
                         (hand[0] - 2, hand[1] - 1, 4, 1))
        # Hand holding a small chime
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["skin_dark"], hand, 2)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["skin_mid"], hand, 1)
        # Floating chime near hand
        chime_x = hand[0] + back * 3
        chime_y = hand[1] - 1 + int(math.sin(phase * 1.5) * 1)
        for r in range(4, 0, -1):
            a = _NS_celwynn._alpha(180 * (4 - r) / 4 * pulse)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_mid"], a),
                                   (chime_x, chime_y), r)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_light"],
                               (chime_x, chime_y), 2)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_hot"],
                               (chime_x, chime_y), 1)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_shine"],
                         (chime_x, chime_y, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Stubby short legs (mostly hidden under robe)."""
        sway = math.sin(phase * 0.8) * 1
        for side in (-1, 1):
            hip_x = cx + side * 3
            hip_y = cy - 2
            foot_x = hip_x + int(sway * side)
            foot_y = hip_y + 8
            # Small leg peeking under robe
            _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["shadow_deep"],
                                 (hip_x + 1, hip_y + 1),
                                 (foot_x + 1, foot_y + 1), 5)
            _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_darkest"],
                                 (hip_x, hip_y), (foot_x, foot_y), 4)
            _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_dark"],
                                 (hip_x, hip_y), (foot_x, foot_y), 3)
            # Boot
            boot_pts = [
                (foot_x - 3, foot_y - 1),
                (foot_x + 4, foot_y - 1),
                (foot_x + 5, foot_y + 2),
                (foot_x + 3, foot_y + 3),
                (foot_x - 3, foot_y + 3),
                (foot_x - 4, foot_y + 1),
            ]
            _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in boot_pts])
            _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["leather_darkest"],
                              boot_pts)
            _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["leather_dark"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 4, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["leather_mid"], [
                (foot_x - 1, foot_y - 1),
                (foot_x + 2, foot_y - 1),
                (foot_x + 3, foot_y),
                (foot_x - 1, foot_y),
            ])
            # Gold buckle
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["gold_mid"],
                             (foot_x, foot_y, 2, 1))
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["gold_shine"],
                             (foot_x + 1, foot_y, 1, 1))
    def _draw_robe_body(surface, cx, cy, facing, phase):
        """Chubby round robe body (deep red with gold trim)."""
        breath = math.sin(phase * 0.7) * 1
        # Main robe shape (rounded, wide bottom)
        robe = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 13, cy - 1),
            (cx + 14, cy + 6),
            (cx + 12, cy + 14),
            (cx + 8, cy + 18),
            (cx - 8, cy + 18),
            (cx - 12, cy + 14),
            (cx - 14, cy + 6),
            (cx - 13, cy - 1),
        ]
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in robe])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["robe_darkest"], robe)
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["robe_dark"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 12, cy - 1), (cx + 13, cy + 6),
            (cx + 11, cy + 13), (cx + 7, cy + 17),
            (cx - 7, cy + 17), (cx - 11, cy + 13),
            (cx - 13, cy + 6), (cx - 12, cy - 1),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["robe_mid"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3),
            (cx + 10, cy), (cx + 11, cy + 6),
            (cx + 9, cy + 12), (cx + 6, cy + 15),
            (cx - 6, cy + 15), (cx - 9, cy + 12),
            (cx - 11, cy + 6), (cx - 10, cy),
        ])
        # Highlight (chest area)
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["robe_light"], [
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 5, cy + 2),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 5, cy + 2),
        ])
        # Gold trim along robe edges (bottom hem)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_darkest"],
                         (cx - 12, cy + 14), (cx + 12, cy + 14), 2)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_mid"],
                         (cx - 12, cy + 15), (cx + 12, cy + 15), 1)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_shine"],
                         (cx - 8, cy + 15), (cx + 8, cy + 15), 1)
        # Gold trim along neck/collar
        pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_darkest"],
                         (cx - 6, cy - 5), (cx + 6, cy - 5), 2)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_mid"],
                         (cx - 6, cy - 4), (cx + 6, cy - 4), 1)
        # Vertical robe fold lines
        for fold_x in (-6, -2, 2, 6):
            pygame.draw.line(surface, _NS_celwynn.PALETTE["robe_darkest"],
                             (cx + fold_x, cy + 2),
                             (cx + fold_x + fold_x // 2, cy + 15), 1)
        # Small cosmic runes on robe
        rune_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, (rx_off, ry_off) in enumerate([(-4, 5), (4, 8), (0, 11)]):
            rx = cx + rx_off
            ry = cy + ry_off
            for r in range(3, 0, -1):
                a = _NS_celwynn._alpha(140 * (3 - r) / 3 * rune_pulse)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["chime_mid"], a),
                                       (rx, ry), r)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                             (rx, ry, 1, 1))
    def _draw_belt(surface, cx, cy, facing, phase):
        """Wide leather belt with big gold buckle."""
        # Belt band
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["shadow_deep"],
                         (cx - 12, cy + 1, 24, 5))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["leather_darkest"],
                         (cx - 12, cy, 24, 4))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["leather_dark"],
                         (cx - 12, cy, 24, 3))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["leather_mid"],
                         (cx - 12, cy, 24, 1))
        # Big central buckle (ornate)
        buckle_pts = [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 7, cy + 1),
            (cx + 5, cy + 5),
            (cx - 5, cy + 5),
            (cx - 7, cy + 1),
        ]
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["gold_darkest"], buckle_pts)
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["gold_dark"], [
            (cx - 4, cy - 1), (cx + 4, cy - 1),
            (cx + 6, cy + 1), (cx + 4, cy + 4),
            (cx - 4, cy + 4), (cx - 6, cy + 1),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["gold_mid"], [
            (cx - 3, cy), (cx + 3, cy),
            (cx + 5, cy + 1), (cx + 3, cy + 3),
            (cx - 3, cy + 3), (cx - 5, cy + 1),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["gold_light"], [
            (cx - 2, cy + 1), (cx + 2, cy + 1),
            (cx + 3, cy + 2), (cx - 3, cy + 2),
        ])
        # Central gem (cosmic)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            a = _NS_celwynn._alpha(200 * (3 - r) / 3 * pulse)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["cosmic_mid"], a),
                                   (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["cosmic_hot"],
                         (cx, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["cosmic_shine"],
                         (cx, cy + 1, 1, 1))
        # Side ornaments (small gold discs)
        for side in (-1, 1):
            disc_x = cx + side * 9
            disc_y = cy + 2
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_dark"],
                                   (disc_x, disc_y), 2)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_mid"],
                                   (disc_x, disc_y), 1)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["gold_shine"],
                             (disc_x, disc_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Small head — mostly covered by beard and hood-like hair."""
        # Head shape (small, round)
        head = [
            (cx - 4, cy - 2),
            (cx - 5, cy - 5),
            (cx - 3, cy - 7),
            (cx, cy - 8),
            (cx + 3, cy - 7),
            (cx + 5, cy - 5),
            (cx + 5, cy - 1),
            (cx + 4, cy + 2),
            (cx - 4, cy + 2),
        ]
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["skin_darkest"], head)
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["skin_dark"], [
            (cx - 3, cy - 2), (cx - 4, cy - 5),
            (cx - 2, cy - 6), (cx, cy - 7),
            (cx + 2, cy - 6), (cx + 4, cy - 5),
            (cx + 4, cy - 1), (cx + 3, cy + 1),
            (cx - 3, cy + 1),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["skin_mid"], [
            (cx - 2, cy - 3), (cx - 2, cy - 5),
            (cx + 2, cy - 5), (cx + 3, cy - 3),
        ])
        # Nose (bulbous like Bard)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["skin_dark"],
                         (cx - 1, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["skin_mid"],
                         (cx, cy - 3, 2, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["skin_light"],
                         (cx + facing, cy - 3, 1, 1))
        # HAIR (bushy on top)
        hair_wave = math.sin(phase * 0.4) * 1
        hair_pts = [
            (cx - 5, cy - 4),
            (cx - 6, cy - 7),
            (cx - 5, cy - 10 + int(hair_wave)),
            (cx - 2, cy - 11 + int(hair_wave)),
            (cx + 2, cy - 11 + int(hair_wave)),
            (cx + 5, cy - 10 + int(hair_wave)),
            (cx + 6, cy - 7),
            (cx + 6, cy - 4),
            (cx + 4, cy - 6),
            (cx, cy - 8),
            (cx - 4, cy - 6),
        ]
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_darkest"],
                          hair_pts)
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_dark"], [
            (cx - 5, cy - 6),
            (cx - 4, cy - 9),
            (cx, cy - 10),
            (cx + 4, cy - 9),
            (cx + 5, cy - 6),
            (cx + 3, cy - 8),
            (cx, cy - 9),
            (cx - 3, cy - 8),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_mid"], [
            (cx - 3, cy - 8),
            (cx, cy - 9),
            (cx + 3, cy - 8),
            (cx + 2, cy - 7),
            (cx - 2, cy - 7),
        ])
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["hair_light"],
                         (cx, cy - 9, 1, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["hair_shine"],
                         (cx + facing, cy - 9, 1, 1))
        # EYES - bright cosmic gold
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Sockets
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 2, 2))
        # Whites
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["skin_shine"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["skin_shine"],
                         (cx + 1, cy - 5, 2, 2))
        # Cosmic pupils
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_darkest"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_darkest"],
                         (cx + 2, cy - 5, 1, 2))
        # Glow
        for r in range(3, 0, -1):
            a = _NS_celwynn._alpha(80 * (3 - r) / 3 * eye_pulse)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_light"], a),
                                   (cx - 2, cy - 4), r)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_light"], a),
                                   (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                         (cx + 2, cy - 4, 1, 1))
    def _draw_big_beard(surface, cx, cy, facing, phase):
        """MASSIVE fluffy white beard that covers mouth and cascades down chest."""
        wave = math.sin(phase * 0.4) * 1
        wave2 = math.sin(phase * 0.6 + 1) * 1
        # Beard is very wide and fluffy, cascading
        beard_pts = [
            (cx - 8, cy),
            (cx - 10, cy + 3),
            (cx - 11, cy + 8 + int(wave)),
            (cx - 10, cy + 13 + int(wave)),
            (cx - 7, cy + 16 + int(wave2)),
            (cx - 3, cy + 18 + int(wave)),
            (cx, cy + 19 + int(wave2)),
            (cx + 3, cy + 18 + int(wave)),
            (cx + 7, cy + 16 + int(wave2)),
            (cx + 10, cy + 13 + int(wave)),
            (cx + 11, cy + 8 + int(wave)),
            (cx + 10, cy + 3),
            (cx + 8, cy),
            (cx + 5, cy + 2),
            (cx - 5, cy + 2),
        ]
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in beard_pts])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_darkest"],
                          beard_pts)
        # Layered shading
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_dark"], [
            (cx - 7, cy + 1),
            (cx - 9, cy + 4),
            (cx - 9, cy + 12),
            (cx - 6, cy + 15),
            (cx - 2, cy + 17),
            (cx + 2, cy + 17),
            (cx + 6, cy + 15),
            (cx + 9, cy + 12),
            (cx + 9, cy + 4),
            (cx + 7, cy + 1),
            (cx + 4, cy + 3),
            (cx - 4, cy + 3),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_mid"], [
            (cx - 6, cy + 2),
            (cx - 7, cy + 5),
            (cx - 7, cy + 11),
            (cx - 4, cy + 14),
            (cx, cy + 15),
            (cx + 4, cy + 14),
            (cx + 7, cy + 11),
            (cx + 7, cy + 5),
            (cx + 6, cy + 2),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_celwynn._poly(surface, _NS_celwynn.PALETTE["hair_light"], [
            (cx - 4, cy + 4),
            (cx - 5, cy + 8),
            (cx - 3, cy + 12),
            (cx, cy + 13),
            (cx + 3, cy + 12),
            (cx + 5, cy + 8),
            (cx + 4, cy + 4),
        ])
        # Highlight streaks (individual hair strands)
        for i, (sx_off, sy_off_start, sy_off_end) in enumerate([
            (-3, 5, 12),
            (-1, 4, 14),
            (1, 4, 14),
            (3, 5, 12),
        ]):
            pygame.draw.line(surface, _NS_celwynn.PALETTE["hair_shine"],
                             (cx + sx_off, cy + sy_off_start),
                             (cx + sx_off, cy + sy_off_end), 1)
        # Mustache (part of beard, above lip)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["hair_dark"],
                         (cx - 4, cy - 1), (cx - 1, cy + 1), 2)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["hair_dark"],
                         (cx + 4, cy - 1), (cx + 1, cy + 1), 2)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["hair_mid"],
                         (cx - 4, cy - 1), (cx - 1, cy + 1), 1)
        pygame.draw.line(surface, _NS_celwynn.PALETTE["hair_mid"],
                         (cx + 4, cy - 1), (cx + 1, cy + 1), 1)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["hair_light"],
                         (cx - 3, cy, 1, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["hair_light"],
                         (cx + 3, cy, 1, 1))
    def _draw_staff_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding the cosmic staff (main weapon)."""
        shoulder = (cx + facing * 5, cy - 4)
        if action == "attack":
            if attack_progress < 0.4:
                # Charge — raise staff high
                t = attack_progress / 0.4
                elbow_off_x = facing * (3 + int(t * 3))
                elbow_off_y = -2 - int(t * 4)
                hand_off_x = facing * (7 + int(t * 3))
                hand_off_y = -6 - int(t * 6)
            elif attack_progress < 0.6:
                # Fire — thrust staff forward
                t = (attack_progress - 0.4) / 0.2
                elbow_off_x = facing * (6 + int(t * 4))
                elbow_off_y = int(-6 + t * 4)
                hand_off_x = facing * (10 + int(t * 4))
                hand_off_y = int(-12 + t * 8)
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                elbow_off_x = facing * (10 - int(t * 5))
                elbow_off_y = int(-2 + t * 2)
                hand_off_x = facing * (14 - int(t * 6))
                hand_off_y = int(-4 + t * 4)
        else:
            # Idle — staff held up-forward casually
            sway = math.sin(phase * 0.6) * 1
            elbow_off_x = facing * 5
            elbow_off_y = -3 + int(sway)
            hand_off_x = facing * 8
            hand_off_y = -6 + int(sway)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # Robe sleeve (upper arm)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["robe_darkest"],
                             shoulder, elbow, 5)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["robe_dark"],
                             shoulder, elbow, 4)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["robe_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Gold cuff at elbow
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_dark"],
                               elbow, 3)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_mid"],
                               elbow, 2)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["gold_shine"],
                         (elbow[0], elbow[1], 1, 1))
        # Forearm (leather bracer)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_darkest"],
                             elbow, hand, 4)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_dark"],
                             elbow, hand, 3)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["leather_mid"],
                             (elbow[0], elbow[1] - 1),
                             (hand[0], hand[1] - 1), 1)
        # Hand gauntlet
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["leather_darkest"],
                         (hand[0] - 2, hand[1] - 1, 5, 4))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["leather_dark"],
                         (hand[0] - 2, hand[1] - 1, 5, 3))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["gold_mid"],
                         (hand[0] - 1, hand[1], 3, 1))
        # STAFF
        _NS_celwynn._draw_staff(surface, hand[0], hand[1], facing, phase,
                                 action, attack_progress)
    def _draw_staff(surface, hx, hy, facing, phase, action, attack_progress):
        """Cosmic staff — long dark shaft with golden orb on top."""
        # Staff angle
        if action == "attack":
            if attack_progress < 0.4:
                angle = -math.pi / 2 - (attack_progress / 0.4) * 0.15
            elif attack_progress < 0.6:
                t = (attack_progress - 0.4) / 0.2
                angle = -math.pi / 2 - 0.15 + t * 0.4
            else:
                t = (attack_progress - 0.6) / 0.4
                angle = -math.pi / 2 + 0.25 - t * 0.1
        else:
            angle = -math.pi / 2 + math.sin(phase * 0.4) * 0.05
        # Staff length (up)
        staff_len = 32
        top_x = hx + int(math.cos(angle) * staff_len) * facing
        top_y = hy + int(math.sin(angle) * staff_len)
        # Bottom (short below hand)
        bot_x = hx - int(math.cos(angle) * 6) * facing
        bot_y = hy - int(math.sin(angle) * 6)
        # Shaft
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["shadow_deep"],
                             (bot_x + 1, bot_y + 1),
                             (top_x + 1, top_y + 1), 4)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["metal_dark"],
                             (bot_x, bot_y), (top_x, top_y), 3)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["metal_mid"],
                             (bot_x, bot_y), (top_x, top_y), 2)
        _NS_celwynn._aaline(surface, _NS_celwynn.PALETTE["metal_light"],
                             (bot_x, bot_y), (top_x, top_y), 1)
        # Gold rings along shaft
        for wrap_t in (0.25, 0.5, 0.75):
            wx = int(bot_x + (top_x - bot_x) * wrap_t)
            wy = int(bot_y + (top_y - bot_y) * wrap_t)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_darkest"],
                                   (wx, wy), 2)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_mid"],
                                   (wx, wy), 1)
        # ORB on top (big cosmic ball with holder)
        # Holder claws (3 prongs)
        for i, prong_angle_off in enumerate((-0.3, 0, 0.3)):
            p_angle = angle + prong_angle_off
            p_len = 5
            p_x = top_x + int(math.cos(p_angle) * p_len) * facing
            p_y = top_y + int(math.sin(p_angle) * p_len)
            pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_darkest"],
                             (top_x, top_y), (p_x, p_y), 2)
            pygame.draw.line(surface, _NS_celwynn.PALETTE["gold_mid"],
                             (top_x, top_y), (p_x, p_y), 1)
        # Orb position
        orb_x = top_x + int(math.cos(angle) * 4) * facing
        orb_y = top_y + int(math.sin(angle) * 4)
        orb_r = 6
        # Halo around orb (big glow)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(orb_r + 8, orb_r, -2):
            a = _NS_celwynn._alpha(140 * (orb_r + 8 - r) / 8 * pulse)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_mid"], a),
                                   (orb_x, orb_y), r)
        # Orb itself
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["shadow_deep"],
                               (orb_x + 1, orb_y + 1), orb_r)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_darkest"],
                               (orb_x, orb_y), orb_r)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_dark"],
                               (orb_x, orb_y), orb_r - 1)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["gold_mid"],
                               (orb_x, orb_y), orb_r - 2)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_light"],
                               (orb_x, orb_y), orb_r - 3)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_hot"],
                               (orb_x, orb_y), orb_r - 4)
        # Highlight
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_shine"],
                         (orb_x - 1, orb_y - 2, 2, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"],
                         (orb_x - 1, orb_y - 2, 1, 1))
        # Small face/mouth on orb (like Bard's staff — friendly face)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["shadow_deep"],
                         (orb_x - 2, orb_y, 1, 1))
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["shadow_deep"],
                         (orb_x + 1, orb_y, 1, 1))
        pygame.draw.line(surface, _NS_celwynn.PALETTE["shadow_deep"],
                         (orb_x - 1, orb_y + 2),
                         (orb_x + 1, orb_y + 2), 1)
        # Star sparkles around orb
        for i in range(4):
            angle_s = phase * 2 + i * math.pi / 2
            sx = orb_x + int(math.cos(angle_s) * (orb_r + 4))
            sy = orb_y + int(math.sin(angle_s) * (orb_r + 4))
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_shine"],
                             (sx, sy, 1, 1))
            # Little 4-point star
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                             (sx - 1, sy, 3, 1))
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                             (sx, sy - 1, 1, 3))
    # ============================================================
    # ORBITING CHIMES/MEEPS (companion orbs)
    # ============================================================
    def _draw_orbiting_chimes(surface, boss, x, y, phase):
        """Small friendly orbs (chimes/meeps) orbiting the caretaker."""
        # 3 gold chimes + 1 blue meep
        for i, (orbit_r_base, speed, color_set) in enumerate([
            (28, 0.6, "chime"),
            (32, 0.5, "chime"),
            (26, 0.7, "chime"),
            (30, 0.55, "meep"),
        ]):
            angle = phase * speed + i * math.pi / 2
            orbit_r = orbit_r_base + int(math.sin(phase + i) * 4)
            cx = x + int(math.cos(angle) * orbit_r)
            cy_pos = y - 8 + int(math.sin(angle) * orbit_r * 0.55)
            if color_set == "chime":
                dark = _NS_celwynn.PALETTE["chime_dark"]
                mid = _NS_celwynn.PALETTE["chime_mid"]
                light = _NS_celwynn.PALETTE["chime_light"]
                hot = _NS_celwynn.PALETTE["chime_hot"]
            else:
                dark = _NS_celwynn.PALETTE["meep_dark"]
                mid = _NS_celwynn.PALETTE["meep_mid"]
                light = _NS_celwynn.PALETTE["meep_light"]
                hot = _NS_celwynn.PALETTE["cosmic_hot"]
            # Glow halo
            pulse = math.sin(phase * 2 + i) * 0.3 + 0.7
            for r in range(5, 0, -1):
                a = _NS_celwynn._alpha(160 * (5 - r) / 5 * pulse)
                _NS_celwynn._aacircle(surface, (*mid, a), (cx, cy_pos), r + 1)
            # Body
            _NS_celwynn._aacircle(surface, dark, (cx, cy_pos), 3)
            _NS_celwynn._aacircle(surface, mid, (cx, cy_pos), 2)
            _NS_celwynn._aacircle(surface, light, (cx, cy_pos), 1)
            pygame.draw.rect(surface, hot, (cx, cy_pos, 1, 1))
            # Small dangling wispy tail below
            for tail_i in range(2):
                tx = cx + int(math.sin(phase * 2 + i + tail_i) * 1)
                ty = cy_pos + 3 + tail_i * 2
                a = _NS_celwynn._alpha(180 - tail_i * 60)
                pygame.draw.rect(surface, (*mid, a), (tx, ty, 1, 2))
            # Tiny sparkle
            sparkle_x = cx + int(math.sin(phase * 3 + i) * 3)
            sparkle_y = cy_pos - 3
            pygame.draw.rect(surface, hot, (sparkle_x, sparkle_y, 1, 1))
    # ============================================================
    # BASIC ATTACK — small cosmic bolt
    # ============================================================
    def _draw_basic_bolt(surface, boss, x, y, progress):
        """Small cosmic bolt (gold-blue) — basic ranged attack."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        # Launch from staff orb (up-forward)
        start_x = x + facing * 20
        start_y = y - 22
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(7):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_celwynn._alpha(220 - i * 25)
            size = max(1, 5 - i)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_dark"], alpha),
                                   (px, py), size + 1)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_mid"], alpha),
                                   (px, py), size)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_light"], alpha),
                                   (px, py), max(1, size - 2))
        # Head
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_dark"],
                               (bx, by), 5)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_mid"],
                               (bx, by), 3)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_light"],
                               (bx, by), 2)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_hot"],
                               (bx, by), 1)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"], (bx, by, 1, 1))
        # Sparkles around
        for i in range(3):
            angle = t * 8 + i * math.pi * 2 / 3
            sx = bx + int(math.cos(angle) * 5)
            sy = by + int(math.sin(angle) * 5)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_shine"],
                             (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((110, 26), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(12, 0, -1):
            alpha = int(max(0, (12 - radius) * 18) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 13 - radius,
                                 94 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, int(160 * mult)),
                            (4, 6, 102, 14))
        surface.blit(shadow, (x - 55, y - 13))
    def _draw_cosmic_aura(surface, x, y, phase):
        """Warm gold cosmic aura with star sparkles."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_celwynn._alpha((85 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_celwynn._aacircle(aura,
                                       (*_NS_celwynn.PALETTE["chime_darkest"], alpha),
                                       (100, 80), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_celwynn._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_celwynn._aacircle(aura,
                                       (*_NS_celwynn.PALETTE["chime_dark"], alpha),
                                       (100, 80), radius)
        for radius in range(30, 5, -2):
            alpha = _NS_celwynn._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_celwynn._aacircle(aura,
                                       (*_NS_celwynn.PALETTE["chime_mid"], alpha),
                                       (100, 80), radius)
        surface.blit(aura, (x - 100, y - 80))
        # Floating stars (4-point sparkles)
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            # 4-point star
            color = _NS_celwynn.PALETTE["chime_hot"] if i % 2 == 0 \
                else _NS_celwynn.PALETTE["cosmic_light"]
            pygame.draw.rect(surface, color, (sx - 1, sy, 3, 1))
            pygame.draw.rect(surface, color, (sx, sy - 1, 1, 3))
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with cosmic runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_celwynn.PALETTE["chime_darkest"], 200),
                            (5, 18, 150, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_celwynn.PALETTE["chime_dark"], 210),
                            (14, 20, 132, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_celwynn.PALETTE["chime_mid"], 220),
                            (24, 22, 112, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_celwynn.PALETTE["cosmic_dark"], 170),
                            (40, 24, 80, 14), 1)
        # Star runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 66)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_celwynn.PALETTE["chime_hot"], 220),
                             (x1, y1), (x2, y2), 1)
            # Star at tip
            pygame.draw.rect(ring, (*_NS_celwynn.PALETTE["chime_shine"], 240),
                             (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_celwynn.PALETTE["chime_shine"],
                                       _NS_celwynn._alpha(150 * pulse)),
                                (15, 12, 130, 36), 1)
        surface.blit(ring, (x - 80, y - 25))
    def _draw_star_trail(surface, cx, cy, phase, facing):
        """Star sparkle trail behind floating body."""
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            wx = cx + int(math.sin(phase + i) * 10) - facing * i * 3
            wy = cy + int(t * 10)
            alpha = _NS_celwynn._alpha(200 * (1 - t))
            if alpha > 0:
                # Small star sparkle
                color = _NS_celwynn.PALETTE["chime_mid"] if i % 2 == 0 \
                    else _NS_celwynn.PALETTE["cosmic_mid"]
                hot = _NS_celwynn.PALETTE["chime_hot"] if i % 2 == 0 \
                    else _NS_celwynn.PALETTE["cosmic_hot"]
                pygame.draw.rect(surface, (*color, alpha), (wx - 1, wy, 3, 1))
                pygame.draw.rect(surface, (*color, alpha), (wx, wy - 1, 1, 3))
                pygame.draw.rect(surface, (*hot, alpha), (wx, wy, 1, 1))
    # ============================================================
    # SKILL: Q - COSMIC BINDING (blue cosmic bolt with stun)
    # ============================================================
    def _draw_cosmic_binding(surface, boss, x, y, timer, phase):
        """Blue cosmic bolt with sparkle trail (stuns on hit)."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        if progress < 0.25:
            # Charge at staff orb
            t = progress / 0.25
            mx = x + facing * 20
            my = y - 22
            cr = int(3 + t * 9)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_celwynn._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_dark"], alpha),
                                       (mx, my), r)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_mid"],
                                   (mx, my), cr - 2)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_light"],
                                   (mx, my), max(1, cr - 4))
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_hot"],
                                   (mx, my), max(1, cr - 6))
            # Sparks
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = mx + int(math.cos(angle) * (cr + 3))
                sy = my + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_celwynn.PALETTE["cosmic_shine"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 22
            start_y = y - 22
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Long sparkling trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_celwynn._alpha(230 - i * 20)
                size = max(1, 8 - i)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_darkest"], alpha),
                                       (px, py), size + 1)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_dark"], alpha),
                                       (px, py), size)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_light"], alpha),
                                       (px, py), max(1, size - 3))
                if i < 5:
                    # 4-point star sparkles
                    for s in range(2):
                        sp_ang = t * 6 + i + s * math.pi
                        sp_x = px + int(math.cos(sp_ang) * (size + 2))
                        sp_y = py + int(math.sin(sp_ang) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_celwynn.PALETTE["cosmic_hot"], alpha),
                                         (sp_x - 1, sp_y, 3, 1))
                        pygame.draw.rect(surface,
                                         (*_NS_celwynn.PALETTE["cosmic_hot"], alpha),
                                         (sp_x, sp_y - 1, 1, 3))
            # Bright head
            for r in range(12, 3, -2):
                alpha = _NS_celwynn._alpha(100 * (12 - r) / 12)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_light"], alpha),
                                       (bx, by), r)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_darkest"],
                                   (bx, by), 6)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_dark"],
                                   (bx, by), 5)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_mid"],
                                   (bx, by), 3)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["cosmic_light"],
                                   (bx, by), 2)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"], (bx, by, 1, 1))
            # Impact stun burst
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 22)
                alpha = _NS_celwynn._alpha(240 * (1 - st))
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_dark"], alpha),
                                       (tx, ty), radius + 3, 3)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_mid"], alpha),
                                       (tx, ty), radius, 2)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["cosmic_light"], alpha),
                                       (tx, ty), max(1, radius - 6), 1)
                # Stun stars around target
                for i in range(6):
                    angle_s = i * math.pi / 3 + phase
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_celwynn.PALETTE["cosmic_hot"], alpha),
                                     (ex - 1, ey, 3, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_celwynn.PALETTE["cosmic_hot"], alpha),
                                     (ex, ey - 1, 1, 3))
    # ============================================================
    # SKILL: W - CARETAKER'S SHRINE (heal shrine at ground)
    # ============================================================
    def _draw_shrine_ground(surface, boss, x, y, timer, phase):
        """Ground base for shrine (gold circle)."""
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(24 * min(1.0, progress * 3))
        if r > 3:
            # Base gold ring
            pygame.draw.ellipse(surface, (*_NS_celwynn.PALETTE["chime_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_celwynn.PALETTE["chime_dark"], 210),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_celwynn.PALETTE["chime_mid"], 200),
                                (tx - r + 6, ty - r // 3 + 3,
                                 r * 2 - 12, r * 2 // 3 - 6), 1)
    def _draw_shrine_foreground(surface, boss, x, y, timer, phase):
        """Vertical gold beam/shrine rising from ground."""
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Beam height grows then holds
        max_h = 48
        if progress < 0.3:
            h = int(max_h * progress / 0.3)
        else:
            h = max_h + int(math.sin(phase * 2) * 2)
        if h < 3:
            return
        # Vertical beam layers (getting brighter toward center)
        for layer_i, (width, alpha_val) in enumerate([
            (12, 100), (8, 140), (5, 180), (3, 220), (1, 255),
        ]):
            colors = [
                _NS_celwynn.PALETTE["chime_darkest"],
                _NS_celwynn.PALETTE["chime_dark"],
                _NS_celwynn.PALETTE["chime_mid"],
                _NS_celwynn.PALETTE["chime_light"],
                _NS_celwynn.PALETTE["chime_shine"],
            ]
            color = colors[min(layer_i, 4)]
            pygame.draw.rect(surface, (*color, alpha_val),
                             (tx - width // 2, ty - h, width, h))
        # Bright orb at top
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(8, 0, -1):
            a = _NS_celwynn._alpha(200 * (8 - r) / 8 * pulse)
            _NS_celwynn._aacircle(surface,
                                   (*_NS_celwynn.PALETTE["chime_mid"], a),
                                   (tx, ty - h), r)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_light"],
                               (tx, ty - h), 3)
        _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_hot"],
                               (tx, ty - h), 2)
        pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_shine"],
                         (tx, ty - h, 1, 1))
        # Rising sparkles along beam
        for i in range(6):
            rise_t = (phase * 0.8 + i * 0.15) % 1.0
            rx = tx + int(math.sin(phase + i) * 4)
            ry = ty - int(rise_t * h)
            alpha = _NS_celwynn._alpha(220 * (1 - rise_t))
            pygame.draw.rect(surface,
                             (*_NS_celwynn.PALETTE["chime_hot"], alpha),
                             (rx - 1, ry, 3, 1))
            pygame.draw.rect(surface,
                             (*_NS_celwynn.PALETTE["chime_hot"], alpha),
                             (rx, ry - 1, 1, 3))
        # Radiating sparkles at base
        for i in range(8):
            angle = phase * 1.5 + i * math.pi / 4
            sr = 16
            sx = tx + int(math.cos(angle) * sr)
            sy = ty + int(math.sin(angle) * sr * 0.3)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_shine"],
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL: E - TEMPERED FATE (slow area + arrow)
    # ============================================================
    def _draw_tempered_ground(surface, boss, x, y, timer, phase):
        """Slow area ring at target."""
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.4:
            # Slow field
            r = int(28 + math.sin(phase * 2) * 3)
            alpha = _NS_celwynn._alpha(200)
            for ring_i in range(3):
                ring_r = r - ring_i * 5
                pygame.draw.ellipse(surface,
                                    (*_NS_celwynn.PALETTE["chime_dark"], alpha - ring_i * 40),
                                    (tx - ring_r, ty - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_celwynn.PALETTE["chime_mid"], alpha - ring_i * 40),
                                    (tx - ring_r + 2, ty - ring_r // 3 + 1,
                                     ring_r * 2 - 4, ring_r * 2 // 3 - 2), 1)
            # Rotating sparkles
            for i in range(8):
                angle = phase * 1.2 + i * math.pi / 4
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                                 (sx - 1, sy, 3, 1))
                pygame.draw.rect(surface, _NS_celwynn.PALETTE["chime_hot"],
                                 (sx, sy - 1, 1, 3))
    def _draw_tempered_foreground(surface, boss, x, y, timer, phase):
        """Arrow-shaped magic energy launched."""
        facing = boss.direction
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        if progress < 0.4:
            # Arrow travels to target
            t = progress / 0.4
            start_x = x + facing * 22
            start_y = y - 18
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Arrow trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_celwynn._alpha(240 - i * 20)
                size = max(1, 6 - i)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["chime_dark"], alpha),
                                       (px, py), size + 1)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["chime_mid"], alpha),
                                       (px, py), size)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["chime_light"], alpha),
                                       (px, py), max(1, size - 2))
            # Arrow-shaped head (elongated)
            dx = tx - start_x
            dy = ty - start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                ux = dx / length
                uy = dy / length
                # Arrow tip
                for i in range(6):
                    ax = bx + int(ux * i)
                    ay = by + int(uy * i)
                    a = _NS_celwynn._alpha(240 * (6 - i) / 6)
                    _NS_celwynn._aacircle(surface,
                                           (*_NS_celwynn.PALETTE["chime_hot"], a),
                                           (ax, ay), max(1, 3 - i // 2))
            # Bright head
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["chime_shine"],
                                   (bx, by), 2)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"], (bx, by, 1, 1))
    # ============================================================
    # SKILL: R - MAGICAL JOURNEY (portal purple)
    # ============================================================
    def _draw_journey_ground(surface, boss, x, y, timer, phase):
        """Portal base rings."""
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Portal at both boss and target locations
        for portal_x, portal_y in ((x, y + 40), (tx, ty)):
            r = int(20 + math.sin(phase * 2) * 3)
            alpha = _NS_celwynn._alpha(200 * min(1.0, progress * 2))
            pygame.draw.ellipse(surface,
                                (*_NS_celwynn.PALETTE["portal_darkest"], alpha),
                                (portal_x - r, portal_y - r // 3,
                                 r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_celwynn.PALETTE["portal_dark"], alpha),
                                (portal_x - r + 2, portal_y - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_celwynn.PALETTE["portal_mid"], alpha),
                                (portal_x - r + 4, portal_y - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 1)
    def _draw_journey_foreground(surface, boss, x, y, timer, phase):
        """Two purple portals — one at boss, one at target."""
        tx, ty = _NS_celwynn._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Portal size grows
        max_r = 22
        r = int(max_r * min(1.0, progress * 2))
        if r < 3:
            return
        for portal_x, portal_y in ((x, y), (tx, ty - 15)):
            # Outer glow
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            for glow_r in range(r + 8, r, -2):
                a = _NS_celwynn._alpha(120 * (r + 8 - glow_r) / 8 * pulse)
                _NS_celwynn._aacircle(surface,
                                       (*_NS_celwynn.PALETTE["portal_mid"], a),
                                       (portal_x, portal_y), glow_r)
            # Portal ring (main circle)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["portal_dark"],
                                   (portal_x, portal_y), r, 3)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["portal_mid"],
                                   (portal_x, portal_y), r, 2)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["portal_light"],
                                   (portal_x, portal_y), r, 1)
            # Inner darkness (portal interior)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["portal_darkest"],
                                   (portal_x, portal_y), r - 3)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["shadow_deep"],
                                   (portal_x, portal_y), r - 5)
            # Swirling energy inside
            for i in range(8):
                angle = phase * 3 + i * math.pi / 4
                inner_r = r - 4
                sx = portal_x + int(math.cos(angle) * inner_r)
                sy = portal_y + int(math.sin(angle) * inner_r)
                a = _NS_celwynn._alpha(220)
                pygame.draw.rect(surface,
                                 (*_NS_celwynn.PALETTE["portal_light"], a),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_celwynn.PALETTE["portal_hot"], a),
                                 (sx, sy, 1, 1))
            # Star sparkles around portal edge
            for i in range(12):
                angle = phase * 1.5 + i * math.pi / 6
                sr = r + 2
                sx = portal_x + int(math.cos(angle) * sr)
                sy = portal_y + int(math.sin(angle) * sr)
                pygame.draw.rect(surface, _NS_celwynn.PALETTE["portal_hot"],
                                 (sx - 1, sy, 3, 1))
                pygame.draw.rect(surface, _NS_celwynn.PALETTE["portal_hot"],
                                 (sx, sy - 1, 1, 3))
                pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"],
                                 (sx, sy, 1, 1))
            # Central bright core (portal vortex center)
            _NS_celwynn._aacircle(surface, _NS_celwynn.PALETTE["portal_hot"],
                                   (portal_x, portal_y), 2)
            pygame.draw.rect(surface, _NS_celwynn.PALETTE["white"],
                             (portal_x, portal_y, 1, 1))
        # Connection line between portals (subtle)
        if r >= max_r:
            for i in range(5):
                seg_t = i / 5 + (phase * 0.5) % 0.2
                cx = int(x + (tx - x) * seg_t)
                cy = int(y + (ty - 15 - y) * seg_t)
                alpha = _NS_celwynn._alpha(150)
                pygame.draw.rect(surface,
                                 (*_NS_celwynn.PALETTE["portal_light"], alpha),
                                 (cx, cy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_celwynn.PALETTE["portal_hot"], alpha),
                                 (cx, cy, 1, 1))



# ====================================================================
# RYNVARA (WILD ONSLAUGHT) - Mini Boss
# ====================================================================

class _NS_rynvara:
    """Namespace rynvara - Wild Onslaught mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tanned, weathered warrior)
        "skin_darkest": (55, 30, 22),
        "skin_dark": (115, 75, 55),
        "skin_mid": (180, 130, 95),
        "skin_light": (225, 180, 140),
        "skin_shine": (250, 220, 185),
        # Hair (wild blonde/golden — Masha signature)
        "hair_darkest": (60, 40, 15),
        "hair_dark": (130, 90, 30),
        "hair_mid": (210, 165, 65),
        "hair_light": (245, 215, 120),
        "hair_shine": (255, 245, 190),
        # Top (dark brown/black leather bra)
        "top_darkest": (15, 10, 8),
        "top_dark": (35, 25, 20),
        "top_mid": (65, 50, 40),
        "top_light": (110, 90, 75),
        # Pants (leather brown)
        "pants_darkest": (20, 12, 8),
        "pants_dark": (55, 35, 20),
        "pants_mid": (95, 65, 38),
        "pants_light": (150, 110, 70),
        # Gauntlet metal (dark iron with silver highlight)
        "gauntlet_darkest": (10, 12, 15),
        "gauntlet_dark": (30, 35, 42),
        "gauntlet_mid": (70, 78, 88),
        "gauntlet_light": (140, 150, 165),
        "gauntlet_shine": (210, 220, 235),
        "gauntlet_edge": (255, 245, 220),
        # Gold ornaments
        "gold_dark": (95, 65, 15),
        "gold_mid": (195, 150, 35),
        "gold_light": (245, 210, 90),
        "gold_shine": (255, 240, 160),
        # Chain (dark iron)
        "chain_dark": (20, 18, 22),
        "chain_mid": (55, 52, 60),
        "chain_light": (110, 108, 118),
        # Leather (belt, straps)
        "leather_darkest": (20, 12, 8),
        "leather_dark": (55, 35, 18),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 110, 65),
        # FIRE (signature aura — orange/red)
        "fire_darkest": (40, 8, 5),
        "fire_dark": (120, 30, 10),
        "fire_mid": (230, 100, 20),
        "fire_light": (255, 175, 55),
        "fire_hot": (255, 220, 120),
        "fire_shine": (255, 250, 200),
        # Eye (fierce green-yellow)
        "eye_dark": (30, 60, 10),
        "eye_mid": (140, 210, 60),
        "eye_hot": (220, 255, 140),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_rynvara._clamp(color)
        if _NS_rynvara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_rynvara._clamp(color)
        if _NS_rynvara.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_rynvara._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_rynvara(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_rynvara._detect_moving(boss)
        _NS_rynvara._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_rv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (fiery)
        _NS_rynvara._draw_fire_aura(surface, x, y, pulse)
        _NS_rynvara._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":  # Howl Shock
            _NS_rynvara._draw_howl_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":  # Wild Charge
            _NS_rynvara._draw_charge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":  # Lightning Trample
            _NS_rynvara._draw_trample_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_rynvara._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_rynvara._draw_walk(surface, boss, x, y)
        else:
            _NS_rynvara._draw_idle(surface, boss, x, y)
        # Wild Power buff aura
        if active_skill == "q":
            _NS_rynvara._draw_wild_power(surface, boss, x, y, skill_timer, pulse)
        # Foreground skill FX
        if active_skill == "w":
            _NS_rynvara._draw_howl_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_rynvara._draw_charge_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_rynvara._draw_trample_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_rv_previous_timer", 0))
        active = bool(getattr(boss, "_rv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._rv_attack_active = True
            boss._rv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._rv_attack_frame = int(getattr(boss, "_rv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._rv_attack_active = False
            boss._rv_attack_frame = 0
            active = False
        boss._rv_previous_timer = timer
        boss._rv_attack_progress = (
            min(1.0, getattr(boss, "_rv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_rv_last_x"):
            boss._rv_last_x = boss.x
            boss._rv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._rv_last_x)
        dy = abs(boss.y - boss._rv_last_y)
        boss._rv_last_x = boss.x
        boss._rv_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_rynvara._draw_shadow(surface, x, y + 50)
        _NS_rynvara._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Floating with fierce charge feel
        phase = boss.pulse * 1.8
        float_bob = int(math.sin(phase * 1.0) * 5)
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_rynvara._draw_shadow(surface, x + sway, y + 50, faded=True)
        _NS_rynvara._draw_ember_trail(surface, x + sway, y + 40, phase,
                                       boss.direction)
        _NS_rynvara._draw_body(surface, x + sway, y + float_bob - 3,
                                boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_rv_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Gauntlet SWING: wind-up → forward punch → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 4)
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            lunge = int((-4 + t * 22)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(18 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_rynvara._draw_shadow(surface, x + lunge, y + 50)
        _NS_rynvara._draw_body(surface, x + lunge, y - lift,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_rynvara._draw_gauntlet_trail(surface, boss, x + lunge, y - lift,
                                          progress)
    # ============================================================
    # BODY (Barbarian woman with spiked gauntlet)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered: rear hair → chain (behind) → legs → torso → rear arm → head+hair → gauntlet arm."""
        # Trailing wild hair BEHIND (back)
        _NS_rynvara._draw_back_hair(surface, cx, cy - 14, facing, phase)
        # Hanging chain behind body
        _NS_rynvara._draw_hanging_chain(surface, cx, cy, facing, phase)
        # Legs
        _NS_rynvara._draw_legs(surface, cx, cy + 12, facing, phase, action)
        # Torso
        _NS_rynvara._draw_torso(surface, cx, cy, facing, phase, action)
        # Rear arm (offhand, smaller)
        _NS_rynvara._draw_rear_arm(surface, cx, cy, facing, phase, action,
                                    attack_progress)
        # Head + wild lion mane hair
        _NS_rynvara._draw_head(surface, cx + facing * 1, cy - 14, facing,
                                phase, action)
        # FRONT ARM with MASSIVE SPIKED GAUNTLET (weapon hand)
        _NS_rynvara._draw_gauntlet_arm(surface, cx, cy, facing, phase, action,
                                        attack_progress)
    def _draw_back_hair(surface, cx, cy, facing, phase):
        """Wild trailing hair behind head (looks like lion mane / wind-blown)."""
        back = -facing
        wave = math.sin(phase * 0.6) * 2
        # Multiple hair strands flowing back
        for i in range(5):
            base_x = cx + back * 4
            base_y = cy - 4 + i * 3
            end_x = cx + back * (10 + i * 2)
            end_y = cy - 8 + i * 4 + int(wave)
            # Curved hair strand
            mid_x = int((base_x + end_x) / 2) + back * 2
            mid_y = int((base_y + end_y) / 2) - 2
            pygame.draw.line(surface, _NS_rynvara.PALETTE["shadow_deep"],
                             (base_x + 1, base_y + 1),
                             (mid_x + 1, mid_y + 1), 4)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_darkest"],
                             (base_x, base_y), (mid_x, mid_y), 3)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_darkest"],
                             (mid_x, mid_y), (end_x, end_y), 3)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_dark"],
                             (base_x, base_y), (mid_x, mid_y), 2)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_dark"],
                             (mid_x, mid_y), (end_x, end_y), 2)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_mid"],
                             (base_x, base_y - 1), (mid_x, mid_y - 1), 1)
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["hair_light"],
                             (end_x, end_y, 1, 1))
    def _draw_hanging_chain(surface, cx, cy, facing, phase):
        """Chain hanging from back — swings slightly."""
        back = -facing
        sway = math.sin(phase * 0.5) * 2
        # Chain from shoulder area going down-back
        base_x = cx + back * 6
        base_y = cy - 6
        end_x = cx + back * (10 + int(sway))
        end_y = cy + 14
        # Chain links
        num_links = 6
        for i in range(num_links):
            t = i / max(1, num_links - 1)
            link_x = int(base_x + (end_x - base_x) * t)
            link_y = int(base_y + (end_y - base_y) * t)
            # Link (small oval)
            _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["shadow_deep"],
                                   (link_x + 1, link_y + 1), 2)
            _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["chain_dark"],
                                   (link_x, link_y), 2)
            _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["chain_mid"],
                                   (link_x, link_y), 1)
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_rynvara.PALETTE["chain_light"],
                                 (link_x, link_y, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Muscular legs — floating with slight sway."""
        sway = math.sin(phase * 0.8) * 2
        for side_i, side in enumerate((-1, 1)):
            hip_x = cx + side * 4
            hip_y = cy - 2
            knee_x = hip_x + int(sway * side * 0.4)
            knee_y = hip_y + 9
            foot_x = knee_x - side * 1
            foot_y = knee_y + 9
            # Thigh
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["shadow_deep"],
                                 (hip_x + 1, hip_y + 1),
                                 (knee_x + 1, knee_y + 1), 7)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["pants_darkest"],
                                 (hip_x, hip_y), (knee_x, knee_y), 6)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["pants_dark"],
                                 (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["pants_mid"],
                                 (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["pants_light"],
                                 (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Leather wraps on thigh
            for wrap_y in (hip_y + 3, hip_y + 6):
                pygame.draw.line(surface, _NS_rynvara.PALETTE["leather_dark"],
                                 (hip_x - 3, wrap_y),
                                 (hip_x + 3, wrap_y), 1)
            # Shin (skin — barbarian shows skin)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["shadow_deep"],
                                 (knee_x + 1, knee_y + 1),
                                 (foot_x + 1, foot_y + 1), 5)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_darkest"],
                                 (knee_x, knee_y), (foot_x, foot_y), 4)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_dark"],
                                 (knee_x, knee_y), (foot_x, foot_y), 3)
            _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_mid"],
                                 (knee_x - 1, knee_y), (foot_x - 1, foot_y), 1)
            # Leather boot wraps
            for wrap_y in (knee_y + 3, knee_y + 6):
                pygame.draw.line(surface, _NS_rynvara.PALETTE["leather_dark"],
                                 (knee_x - 2, wrap_y),
                                 (knee_x + 2, wrap_y), 1)
                pygame.draw.line(surface, _NS_rynvara.PALETTE["leather_mid"],
                                 (knee_x - 2, wrap_y),
                                 (knee_x + 2, wrap_y), 1)
            # Boot
            boot_pts = [
                (foot_x - 3, foot_y - 1),
                (foot_x + 4, foot_y - 1),
                (foot_x + 5, foot_y + 2),
                (foot_x + 3, foot_y + 3),
                (foot_x - 3, foot_y + 3),
                (foot_x - 4, foot_y + 1),
            ]
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in boot_pts])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["leather_darkest"],
                              boot_pts)
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["leather_dark"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 4, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            # Metal spike on boot
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_mid"],
                             (foot_x + 2, foot_y - 2, 2, 2))
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_shine"],
                             (foot_x + 2, foot_y - 2, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Muscular female torso with dark leather top."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape (athletic hourglass)
        torso = [
            (cx - 8, cy - 8),
            (cx + 8, cy - 8),
            (cx + 10, cy - 3),
            (cx + 8, cy + 3),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 8, cy + 3),
            (cx - 10, cy - 3),
        ]
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in torso])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_darkest"], torso)
        # Skin base
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_dark"], [
            (cx - 7, cy - 7), (cx + 7, cy - 7),
            (cx + 9, cy - 3), (cx + 7, cy + 2),
            (cx + 5, cy + 10), (cx - 5, cy + 10),
            (cx - 7, cy + 2), (cx - 9, cy - 3),
        ])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 7, cy - 2), (cx + 5, cy + 2),
            (cx + 4, cy + 8), (cx - 4, cy + 8),
            (cx - 5, cy + 2), (cx - 7, cy - 2),
        ])
        # Highlight (torso lit)
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_light"], [
            (cx - 2 * facing, cy - 3),
            (cx + 3 * facing, cy - 4),
            (cx + 4 * facing, cy - 1),
            (cx + 1 * facing, cy),
        ])
        # Abs subtle shading
        pygame.draw.line(surface, _NS_rynvara.PALETTE["skin_darkest"],
                         (cx, cy + 2), (cx, cy + 8), 1)
        for ab_y in (cy + 4, cy + 7):
            pygame.draw.line(surface, _NS_rynvara.PALETTE["skin_darkest"],
                             (cx - 2, ab_y), (cx + 2, ab_y), 1)
        # DARK LEATHER TOP (bra-like top)
        top_pts = [
            (cx - 8, cy - 7),
            (cx + 8, cy - 7),
            (cx + 9, cy - 4),
            (cx + 6, cy - 2),
            (cx + 2, cy - 1),
            (cx - 2, cy - 1),
            (cx - 6, cy - 2),
            (cx - 9, cy - 4),
        ]
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                          [(p[0], p[1] + 1) for p in top_pts])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["top_darkest"], top_pts)
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["top_dark"], [
            (cx - 7, cy - 6), (cx + 7, cy - 6),
            (cx + 8, cy - 4), (cx + 5, cy - 3),
            (cx + 1, cy - 2), (cx - 1, cy - 2),
            (cx - 5, cy - 3), (cx - 8, cy - 4),
        ])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["top_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 6, cy - 4), (cx + 4, cy - 3),
            (cx - 4, cy - 3), (cx - 6, cy - 4),
        ])
        # Gold trim on top
        pygame.draw.line(surface, _NS_rynvara.PALETTE["gold_dark"],
                         (cx - 8, cy - 7), (cx + 8, cy - 7), 1)
        pygame.draw.line(surface, _NS_rynvara.PALETTE["gold_mid"],
                         (cx - 6, cy - 7), (cx + 6, cy - 7), 1)
        # Chest strap crossing
        pygame.draw.line(surface, _NS_rynvara.PALETTE["leather_darkest"],
                         (cx - 7, cy - 5), (cx + 7, cy - 3), 2)
        pygame.draw.line(surface, _NS_rynvara.PALETTE["leather_dark"],
                         (cx - 7, cy - 5), (cx + 7, cy - 3), 1)
        # Small gold pendant at center
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pend_x = cx
        pend_y = cy - 3
        for r in range(3, 0, -1):
            a = _NS_rynvara._alpha(180 * (3 - r) / 3 * pulse)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_mid"], a),
                                   (pend_x, pend_y), r)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gold_dark"],
                               (pend_x, pend_y), 2)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gold_mid"],
                               (pend_x, pend_y), 1)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_hot"],
                         (pend_x, pend_y, 1, 1))
        # Belt
        belt_y = cy + 11
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["shadow_deep"],
                         (cx - 7, belt_y + 1, 14, 3))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["leather_darkest"],
                         (cx - 7, belt_y, 14, 3))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["leather_dark"],
                         (cx - 7, belt_y, 14, 2))
        # Buckle
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gold_dark"],
                         (cx - 2, belt_y - 1, 4, 5))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gold_mid"],
                         (cx - 1, belt_y, 3, 3))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gold_shine"],
                         (cx, belt_y + 1, 1, 1))
        # Star mark on skin (Masha's iconic mark on leg/thigh area — small tribal mark)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_dark"],
                         (cx - 4, cy + 6, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_dark"],
                         (cx - 5, cy + 5, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_dark"],
                         (cx - 3, cy + 5, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_mid"],
                         (cx - 4, cy + 5, 1, 1))
        # Battle scars on skin (small marks)
        for scar in ((cx + 3, cy + 3), (cx - 2, cy + 5)):
            pygame.draw.line(surface, _NS_rynvara.PALETTE["skin_darkest"],
                             (scar[0], scar[1]), (scar[0] + 1, scar[1] + 2), 1)
    def _draw_rear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm — muscular, smaller than gauntlet arm. Bare skin."""
        back = -facing
        shoulder = (cx + back * 6, cy - 6)
        if action == "attack":
            # Arm swings back for counterbalance during punch
            if attack_progress < 0.35:
                swing_off = int(attack_progress / 0.35 * 3)
                elbow_off_x = back * (3 + swing_off)
                elbow_off_y = 4
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = back * int(6 + t * 3)
                elbow_off_y = int(4 + t * 2)
            else:
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = back * int(9 - t * 6)
                elbow_off_y = int(6 - t * 2)
        else:
            swing = math.sin(phase * 0.8) * 2
            elbow_off_x = back * 3
            elbow_off_y = 4 + int(swing)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (elbow[0] + back * 2, elbow[1] + 6)
        # Upper arm (bare muscular skin)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_darkest"],
                             shoulder, elbow, 5)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_dark"],
                             shoulder, elbow, 4)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Small shoulder armor pad
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                               shoulder, 3)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_dark"],
                               shoulder, 2)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                         (shoulder[0], shoulder[1] - 1, 1, 1))
        # Forearm
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_darkest"],
                             elbow, hand, 4)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_dark"],
                             elbow, hand, 3)
        # Leather wrist wrap
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["leather_darkest"],
                         (hand[0] - 2, hand[1] - 2, 5, 4))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["leather_dark"],
                         (hand[0] - 2, hand[1] - 2, 5, 3))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gold_mid"],
                         (hand[0] - 1, hand[1] - 1, 3, 1))
        # Clenched fist
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["shadow_deep"],
                               (hand[0] + 1, hand[1] + 1), 3)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["skin_darkest"],
                               hand, 3)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["skin_dark"],
                               hand, 2)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["skin_mid"],
                               hand, 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Fierce female barbarian face with WILD golden lion mane hair."""
        # Head shape
        head = [
            (cx - 4, cy - 2),
            (cx - 5, cy - 5),
            (cx - 3, cy - 8),
            (cx, cy - 9),
            (cx + 3, cy - 8),
            (cx + 5, cy - 5),
            (cx + 5, cy - 1),
            (cx + 4, cy + 2),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
            (cx - 4, cy + 2),
        ]
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_darkest"], head)
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_dark"], [
            (cx - 3, cy - 2), (cx - 4, cy - 4),
            (cx - 2, cy - 7), (cx, cy - 8),
            (cx + 2, cy - 7), (cx + 4, cy - 4),
            (cx + 4, cy - 1), (cx + 3, cy + 1),
            (cx + 1, cy + 3), (cx - 1, cy + 3),
            (cx - 3, cy + 1),
        ])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_mid"], [
            (cx - 2, cy - 3), (cx - 2, cy - 6),
            (cx, cy - 7), (cx + 2, cy - 6),
            (cx + 3, cy - 3),
        ])
        # Highlight side
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["skin_light"], [
            (cx + facing, cy - 5),
            (cx + 3 * facing, cy - 4),
            (cx + 3 * facing, cy - 2),
            (cx + facing, cy - 2),
        ])
        # WILD MANE HAIR (big and messy — like lion mane)
        hair_wave = math.sin(phase * 0.5) * 2
        hair_wave2 = math.sin(phase * 0.4 + 1) * 1
        # Big volumetric hair around head
        hair_pts = [
            (cx - 7, cy - 3),
            (cx - 9, cy - 7),
            (cx - 8, cy - 12 + int(hair_wave)),
            (cx - 5, cy - 14 + int(hair_wave)),
            (cx - 1, cy - 15 + int(hair_wave2)),
            (cx + 3, cy - 14 + int(hair_wave)),
            (cx + 7, cy - 12 + int(hair_wave2)),
            (cx + 9, cy - 8),
            (cx + 8, cy - 4),
            (cx + 6, cy - 2),
            (cx + 5, cy - 5),
            (cx + 2, cy - 7),
            (cx - 2, cy - 8),
            (cx - 5, cy - 6),
            (cx - 6, cy - 3),
        ]
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["hair_darkest"],
                          hair_pts)
        # Layered shading
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["hair_dark"], [
            (cx - 7, cy - 5),
            (cx - 7, cy - 11),
            (cx - 4, cy - 13),
            (cx, cy - 14),
            (cx + 4, cy - 13),
            (cx + 7, cy - 11),
            (cx + 7, cy - 5),
            (cx + 5, cy - 7),
            (cx, cy - 9),
            (cx - 5, cy - 7),
        ])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["hair_mid"], [
            (cx - 5, cy - 9),
            (cx - 3, cy - 12),
            (cx, cy - 13),
            (cx + 3, cy - 12),
            (cx + 5, cy - 9),
            (cx + 3, cy - 8),
            (cx, cy - 9),
            (cx - 3, cy - 8),
        ])
        # Bright highlights (sun-kissed)
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["hair_light"], [
            (cx - 2, cy - 11),
            (cx, cy - 12),
            (cx + 2, cy - 11),
            (cx + 1, cy - 10),
            (cx - 1, cy - 10),
        ])
        # Shine strands
        for hx_off in (-3, 0, 2):
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["hair_shine"],
                             (cx + hx_off, cy - 12, 1, 1))
        # WILD LOCKS sticking out (spiky mane look)
        for i, (base_off_x, base_off_y, tip_off_x, tip_off_y) in enumerate([
            (-8, -8, -11, -12),
            (-5, -14, -6, -18),
            (-1, -15, 0, -19),
            (3, -14, 5, -18),
            (7, -10, 10, -14),
            (8, -5, 11, -6),
            (-8, -4, -11, -3),
        ]):
            wave_off = math.sin(phase * 0.7 + i) * 1
            tip_x = cx + tip_off_x + int(wave_off)
            tip_y = cy + tip_off_y
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_darkest"],
                             (cx + base_off_x, cy + base_off_y),
                             (tip_x, tip_y), 3)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_dark"],
                             (cx + base_off_x, cy + base_off_y),
                             (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_mid"],
                             (cx + base_off_x, cy + base_off_y),
                             (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))
        # EYES — fierce green-yellow
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Furrowed brow (angry)
        pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_darkest"],
                         (cx - 4, cy - 6), (cx - 1, cy - 5), 1)
        pygame.draw.line(surface, _NS_rynvara.PALETTE["hair_darkest"],
                         (cx + 4, cy - 6), (cx + 1, cy - 5), 1)
        # Eye sockets
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 2, 2))
        # Whites
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["skin_shine"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["skin_shine"],
                         (cx + 1, cy - 5, 2, 2))
        # Fierce green pupils
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["eye_dark"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["eye_dark"],
                         (cx + 2, cy - 5, 1, 2))
        # Glow
        for r in range(3, 0, -1):
            a = _NS_rynvara._alpha(80 * (3 - r) / 3 * eye_pulse)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["eye_mid"], a),
                                   (cx - 2, cy - 4), r)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["eye_mid"], a),
                                   (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["eye_hot"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["eye_hot"],
                         (cx + 2, cy - 4, 1, 1))
        # Nose
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["skin_darkest"],
                         (cx, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["skin_light"],
                         (cx + facing, cy - 2, 1, 1))
        # Angry snarl mouth (open — battle cry)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["shadow_deep"],
                         (cx - 2, cy + 1, 5, 2))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_darkest"],
                         (cx - 2, cy + 1, 5, 2))
        # Teeth
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["skin_shine"],
                         (cx - 1, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["skin_shine"],
                         (cx + 1, cy + 1, 1, 1))
        # War paint stripe across nose/cheek
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_dark"],
                         (cx - 3, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_mid"],
                         (cx - 3, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_mid"],
                         (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_dark"],
                         (cx + 1, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_mid"],
                         (cx + 2, cy - 1, 1, 1))
    def _draw_gauntlet_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """FRONT ARM with MASSIVE SPIKED GAUNTLET (weapon hand — MAIN feature)."""
        shoulder = (cx + facing * 6, cy - 6)
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up — pull fist back
                t = attack_progress / 0.35
                elbow_off_x = facing * int(3 - t * 5)
                elbow_off_y = int(3 - t * 5)
                hand_off_x = facing * int(6 - t * 8)
                hand_off_y = int(6 - t * 10)
            elif attack_progress < 0.55:
                # PUNCH forward hard
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = facing * int(-2 + t * 14)
                elbow_off_y = int(-2 + t * 6)
                hand_off_x = facing * int(-2 + t * 26)
                hand_off_y = int(-4 + t * 6)
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = facing * int(12 - t * 8)
                elbow_off_y = int(4 - t * 2)
                hand_off_x = facing * int(24 - t * 16)
                hand_off_y = int(2 + t * 2)
        else:
            # Idle — gauntlet held ready in front
            sway = math.sin(phase * 0.6) * 1
            elbow_off_x = facing * 6
            elbow_off_y = int(2 + sway)
            hand_off_x = facing * 12
            hand_off_y = int(4 + sway)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # SHOULDER PAULDRON (spiked)
        _NS_rynvara._draw_pauldron(surface, shoulder[0], shoulder[1], facing,
                                    phase)
        # Upper arm (bare skin — muscular)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 7)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_darkest"],
                             shoulder, elbow, 6)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_dark"],
                             shoulder, elbow, 5)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 3)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["skin_light"],
                             (shoulder[0], shoulder[1] - 2),
                             (elbow[0], elbow[1] - 2), 1)
        # Elbow armor plate
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                               elbow, 4)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_dark"],
                               elbow, 3)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_mid"],
                               elbow, 2)
        # Spike on elbow
        elbow_spike_x = elbow[0] - facing * 2
        elbow_spike_y = elbow[1] - 3
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_darkest"], [
            (elbow_spike_x, elbow_spike_y),
            (elbow[0] - facing * 3, elbow[1] - 1),
            (elbow[0] - facing, elbow[1] - 1),
        ])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_mid"], [
            (elbow_spike_x, elbow_spike_y),
            (elbow[0] - facing * 2, elbow[1] - 1),
            (elbow[0] - facing, elbow[1] - 1),
        ])
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                         (elbow_spike_x, elbow_spike_y, 1, 1))
        # MASSIVE GAUNTLET on forearm+hand
        _NS_rynvara._draw_gauntlet(surface, elbow[0], elbow[1], hand[0], hand[1],
                                    facing, phase, action, attack_progress)
    def _draw_pauldron(surface, sx, sy, facing, phase):
        """Spiked shoulder pauldron."""
        paul_pts = [
            (sx - 4, sy - 1),
            (sx + 4, sy - 1),
            (sx + 5, sy + 3),
            (sx + 3, sy + 5),
            (sx - 3, sy + 5),
            (sx - 5, sy + 3),
        ]
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in paul_pts])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                          paul_pts)
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_dark"], [
            (sx - 3, sy), (sx + 3, sy),
            (sx + 4, sy + 2), (sx + 2, sy + 4),
            (sx - 2, sy + 4), (sx - 4, sy + 2),
        ])
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_mid"], [
            (sx - 2, sy + 1), (sx + 2, sy + 1),
            (sx + 3, sy + 3), (sx - 3, sy + 3),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                         (sx - 1, sy + 1, 2, 1))
        # Big spike on top
        pygame.draw.line(surface, _NS_rynvara.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (sx, sy - 6), 3)
        pygame.draw.line(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                         (sx, sy), (sx, sy - 6), 2)
        pygame.draw.line(surface, _NS_rynvara.PALETTE["gauntlet_mid"],
                         (sx, sy), (sx, sy - 5), 1)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                         (sx, sy - 6, 1, 1))
        # Two smaller spikes on sides
        for spike_x_off in (-2, 2):
            pygame.draw.line(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                             (sx + spike_x_off, sy), (sx + spike_x_off, sy - 3), 2)
            pygame.draw.line(surface, _NS_rynvara.PALETTE["gauntlet_mid"],
                             (sx + spike_x_off, sy), (sx + spike_x_off, sy - 3), 1)
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                             (sx + spike_x_off, sy - 3, 1, 1))
    def _draw_gauntlet(surface, ex, ey, hx, hy, facing, phase, action,
                        attack_progress):
        """MASSIVE SPIKED GAUNTLET covering forearm and fist."""
        # Angle from elbow to hand
        dx = hx - ex
        dy = hy - ey
        angle = math.atan2(dy, dx)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)
        # Forearm gauntlet plate (thick armor cylinder)
        # Base along arm — 4 corners
        forearm_len = math.sqrt(dx * dx + dy * dy)
        # Points along arm
        c1 = (int(ex + perp_x * 4), int(ey + perp_y * 4))
        c2 = (int(hx + perp_x * 5), int(hy + perp_y * 5))
        c3 = (int(hx - perp_x * 5), int(hy - perp_y * 5))
        c4 = (int(ex - perp_x * 4), int(ey - perp_y * 4))
        # Shadow
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"],
                          [(c1[0] + 2, c1[1] + 2), (c2[0] + 2, c2[1] + 2),
                           (c3[0] + 2, c3[1] + 2), (c4[0] + 2, c4[1] + 2)])
        # Forearm plate base
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                          [c1, c2, c3, c4])
        # Inner shading
        cx_local = (c1[0] + c2[0] + c3[0] + c4[0]) / 4
        cy_local = (c1[1] + c2[1] + c3[1] + c4[1]) / 4
        inner_pts = []
        for p in (c1, c2, c3, c4):
            inner_pts.append((int(p[0] * 0.8 + cx_local * 0.2),
                              int(p[1] * 0.8 + cy_local * 0.2)))
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_dark"],
                          inner_pts)
        # Mid tone
        mid_pts = []
        for p in (c1, c2, c3, c4):
            mid_pts.append((int(p[0] * 0.65 + cx_local * 0.35),
                            int(p[1] * 0.65 + cy_local * 0.35)))
        _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_mid"],
                          mid_pts)
        # Bright edge along top
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["gauntlet_light"],
                             c1, c2, 2)
        _NS_rynvara._aaline(surface, _NS_rynvara.PALETTE["gauntlet_shine"],
                             c1, c2, 1)
        # ROWS OF SPIKES on top of gauntlet (2 rows)
        # Direction along arm
        along_x = math.cos(angle)
        along_y = math.sin(angle)
        for spike_i in range(5):
            spike_t = 0.15 + spike_i * 0.18
            base_x = int(ex + dx * spike_t + perp_x * 4)
            base_y = int(ey + dy * spike_t + perp_y * 4)
            tip_x = int(base_x + perp_x * 5)
            tip_y = int(base_y + perp_y * 5)
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x - int(along_x * 2) + 1, base_y - int(along_y * 2) + 1),
                (base_x + int(along_x * 2) + 1, base_y + int(along_y * 2) + 1),
            ])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_darkest"], [
                (tip_x, tip_y),
                (base_x - int(along_x * 2), base_y - int(along_y * 2)),
                (base_x + int(along_x * 2), base_y + int(along_y * 2)),
            ])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_mid"], [
                (tip_x, tip_y),
                (base_x - int(along_x), base_y - int(along_y)),
                (base_x + int(along_x), base_y + int(along_y)),
            ])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_light"], [
                (tip_x, tip_y),
                (base_x, base_y),
                (base_x + int(along_x), base_y + int(along_y)),
            ])
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                             (tip_x, tip_y, 1, 1))
        # Plate joints (lines across)
        for j in (0.35, 0.7):
            j_c1 = (int(ex + dx * j + perp_x * 4),
                    int(ey + dy * j + perp_y * 4))
            j_c2 = (int(ex + dx * j - perp_x * 4),
                    int(ey + dy * j - perp_y * 4))
            pygame.draw.line(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                             j_c1, j_c2, 1)
        # FIST (big clenched fist at end)
        # Bigger circle at hand
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["shadow_deep"],
                               (hx + 2, hy + 2), 7)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                               (hx, hy), 7)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_dark"],
                               (hx, hy), 6)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_mid"],
                               (hx, hy), 4)
        # Highlight
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_light"],
                               (hx - facing, hy - 2), 2)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["gauntlet_shine"],
                               (hx - facing, hy - 2), 1)
        # BIG SPIKES on fist (4 in cross pattern)
        for spike_angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            adjusted = spike_angle + angle - math.pi / 2
            spike_dir_x = math.cos(adjusted)
            spike_dir_y = math.sin(adjusted)
            base_x = int(hx + spike_dir_x * 5)
            base_y = int(hy + spike_dir_y * 5)
            tip_x = int(hx + spike_dir_x * 10)
            tip_y = int(hy + spike_dir_y * 10)
            perp2_x = -spike_dir_y
            perp2_y = spike_dir_x
            pb_a = (int(base_x + perp2_x * 2), int(base_y + perp2_y * 2))
            pb_b = (int(base_x - perp2_x * 2), int(base_y - perp2_y * 2))
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (pb_a[0] + 1, pb_a[1] + 1),
                (pb_b[0] + 1, pb_b[1] + 1),
            ])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_darkest"],
                              [(tip_x, tip_y), pb_a, pb_b])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_mid"], [
                (tip_x, tip_y),
                (int((pb_a[0] + hx) / 2), int((pb_a[1] + hy) / 2)),
                (hx, hy),
            ])
            _NS_rynvara._poly(surface, _NS_rynvara.PALETTE["gauntlet_light"], [
                (tip_x, tip_y),
                (int((tip_x + hx) / 2), int((tip_y + hy) / 2)),
                (hx, hy),
            ])
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["gauntlet_edge"],
                             (tip_x, tip_y, 1, 1))
        # Central rune on fist (fire glow)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            a = _NS_rynvara._alpha(200 * (4 - r) / 4 * pulse)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_mid"], a),
                                   (hx, hy), r)
        _NS_rynvara._aacircle(surface, _NS_rynvara.PALETTE["fire_hot"],
                               (hx, hy), 2)
        pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_shine"],
                         (hx, hy, 1, 1))
    # ============================================================
    # GAUNTLET SWING TRAIL
    # ============================================================
    def _draw_gauntlet_trail(surface, boss, x, y, progress):
        """Fire arc trail during gauntlet punch."""
        if not (0.35 <= progress <= 0.7):
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.35
        # Straight punch trail
        punch_x_end = x + facing * 26
        punch_y_end = y - 2
        punch_x_start = x + facing * 8
        punch_y_start = y - 4
        # Number of trail segments
        num_segs = 10
        max_seg = int(num_segs * min(1.0, t * 1.3))
        for i in range(max_seg):
            seg_t = i / num_segs
            # Interpolate
            px = int(punch_x_start + (punch_x_end - punch_x_start) * seg_t)
            py = int(punch_y_start + (punch_y_end - punch_y_start) * seg_t)
            # Add slight upward arc
            arc_off = int(math.sin(seg_t * math.pi) * 5)
            py -= arc_off
            fade = (max_seg - i) / max(1, max_seg)
            alpha = _NS_rynvara._alpha(230 * fade)
            size = max(1, 5 - i // 3)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_darkest"], alpha),
                                   (px, py), size + 2)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                   (px, py), size + 1)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                   (px, py), size)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_light"], alpha),
                                   (px, py), max(1, size - 2))
            pygame.draw.rect(surface,
                             (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                             (px, py, 1, 1))
        # Impact burst at end
        if 0.5 < progress < 0.65:
            imp_t = (progress - 0.5) / 0.15
            imp_x = x + facing * 30
            imp_y = y
            imp_r = int(6 + imp_t * 14)
            alpha = _NS_rynvara._alpha(240 * (1 - imp_t))
            for r in range(imp_r, 0, -2):
                a = _NS_rynvara._alpha(alpha * r / imp_r)
                _NS_rynvara._aacircle(surface,
                                       (*_NS_rynvara.PALETTE["fire_mid"], a),
                                       (imp_x, imp_y), r, 2)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                   (imp_x, imp_y), max(1, imp_r // 3))
            for i in range(10):
                angle = i * math.pi / 5
                ex = imp_x + int(math.cos(angle) * imp_r)
                ey = imp_y + int(math.sin(angle) * imp_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(12, 0, -1):
            alpha = int(max(0, (12 - radius) * 18) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 13 - radius,
                                 104 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, int(160 * mult)),
                            (4, 6, 112, 14))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_fire_aura(surface, x, y, phase):
        """Warm fire aura (orange/red)."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_rynvara._alpha((85 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_rynvara._aacircle(aura,
                                       (*_NS_rynvara.PALETTE["fire_darkest"], alpha),
                                       (100, 80), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_rynvara._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_rynvara._aacircle(aura,
                                       (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                       (100, 80), radius)
        for radius in range(30, 5, -2):
            alpha = _NS_rynvara._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_rynvara._aacircle(aura,
                                       (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                       (100, 80), radius)
        surface.blit(aura, (x - 100, y - 80))
        # Floating embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fiery ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_rynvara.PALETTE["fire_darkest"], 210),
                            (5, 18, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_rynvara.PALETTE["fire_dark"], 220),
                            (14, 20, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_rynvara.PALETTE["fire_mid"], 230),
                            (24, 22, 112, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 46)
            y1 = 28 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 66)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_rynvara.PALETTE["fire_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_rynvara.PALETTE["fire_shine"],
                                       _NS_rynvara._alpha(150 * pulse)),
                                (15, 12, 130, 36), 1)
        surface.blit(ring, (x - 80, y - 25))
    def _draw_ember_trail(surface, cx, cy, phase, facing):
        """Fire ember trail during floating movement."""
        for i in range(8):
            t = (phase * 0.5 + i * 0.14) % 1.0
            wx = cx + int(math.sin(phase + i) * 10) - facing * i * 3
            wy = cy + int(t * 10)
            alpha = _NS_rynvara._alpha(200 * (1 - t))
            if alpha > 0:
                _NS_rynvara._aacircle(surface,
                                       (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                       (wx, wy), 3)
                _NS_rynvara._aacircle(surface,
                                       (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # SKILL 1: WILD POWER (buff aura)
    # ============================================================
    def _draw_wild_power(surface, boss, x, y, timer, phase):
        """Intense fire aura wrapping the boss."""
        r = 42
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        # Big flaming aura
        aura = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Wavy fire boundary
        for i, (thick, alpha_val) in enumerate([
            (4, 100), (3, 140), (2, 180), (1, 220),
        ]):
            a = _NS_rynvara._alpha(alpha_val * pulse)
            _NS_rynvara._aacircle(aura,
                                   (*_NS_rynvara.PALETTE["fire_dark"], a),
                                   center, r - i, thick)
            _NS_rynvara._aacircle(aura,
                                   (*_NS_rynvara.PALETTE["fire_mid"], a),
                                   center, r - i - 1, 1)
        # Rising flames around aura edge
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            fx = center[0] + int(math.cos(angle) * r)
            fy = center[1] + int(math.sin(angle) * r)
            # Small flame tongue
            flame_h = 4 + int(math.sin(phase * 3 + i) * 2)
            pygame.draw.line(aura,
                             (*_NS_rynvara.PALETTE["fire_mid"], 220),
                             (fx, fy), (fx, fy - flame_h), 2)
            pygame.draw.line(aura,
                             (*_NS_rynvara.PALETTE["fire_hot"], 240),
                             (fx, fy), (fx, fy - flame_h), 1)
            pygame.draw.rect(aura, (*_NS_rynvara.PALETTE["fire_shine"], 240),
                             (fx, fy - flame_h, 1, 1))
        # Rotating fire orbs inside
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            inner_r = r - 8
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            _NS_rynvara._aacircle(aura, _NS_rynvara.PALETTE["fire_mid"],
                                   (bx, by), 3)
            _NS_rynvara._aacircle(aura, _NS_rynvara.PALETTE["fire_hot"],
                                   (bx, by), 1)
        surface.blit(aura, (x - r - 10, y - r - 10))
        # Rising ember columns
        for i in range(8):
            col_angle = i * math.pi / 4 + phase * 0.3
            col_dist = r - 5
            col_x = x + int(math.cos(col_angle) * col_dist)
            col_y_base = y + int(math.sin(col_angle) * col_dist * 0.5)
            for layer in range(4):
                layer_t = (phase * 0.8 + i * 0.2 + layer * 0.2) % 1.0
                layer_y = col_y_base - int(layer_t * 15)
                layer_alpha = _NS_rynvara._alpha(200 * (1 - layer_t))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_mid"], layer_alpha),
                                 (col_x, layer_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_hot"], layer_alpha),
                                 (col_x, layer_y, 1, 1))
    # ============================================================
    # SKILL 2: HOWL SHOCK (AoE ring around boss)
    # ============================================================
    def _draw_howl_ground(surface, boss, x, y, timer, phase):
        """Expanding fire shockwave ring."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Expanding ring
        max_r = 70
        r = int(max_r * progress)
        alpha = _NS_rynvara._alpha(240 * (1 - progress * 0.5))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_darkest"], alpha),
                                (x - r, y + 40 - r // 3,
                                 r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                (x - r + 6, y + 40 - r // 3 + 3,
                                 r * 2 - 12, r * 2 // 3 - 6), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                (x - r + 10, y + 40 - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 1)
    def _draw_howl_foreground(surface, boss, x, y, timer, phase):
        """Sound waves + rising flames from howl."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Sound wave arcs emanating outward
        for wave_i in range(3):
            wave_start = wave_i * 0.15
            wave_end = wave_start + 0.5
            if progress < wave_start or progress > wave_end:
                continue
            w_t = (progress - wave_start) / (wave_end - wave_start)
            wave_r = int(20 + w_t * 55)
            alpha = _NS_rynvara._alpha(220 * (1 - w_t))
            # Ring
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                   (x, y), wave_r, 2)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                   (x, y), wave_r, 1)
        # Rising flame columns around boss
        for i in range(10):
            col_angle = i * math.pi / 5 + phase * 0.4
            col_dist = 35
            col_x = x + int(math.cos(col_angle) * col_dist)
            col_y_base = y + int(math.sin(col_angle) * col_dist * 0.5) + 10
            for layer in range(5):
                layer_t = (phase * 0.7 + i * 0.15 + layer * 0.18) % 1.0
                layer_y = col_y_base - int(layer_t * 18)
                layer_alpha = _NS_rynvara._alpha(220 * (1 - layer_t) * (1 - progress * 0.3))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_dark"], layer_alpha),
                                 (col_x - 1, layer_y, 3, 2))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_mid"], layer_alpha),
                                 (col_x, layer_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_hot"], layer_alpha),
                                 (col_x, layer_y, 1, 1))
    # ============================================================
    # SKILL 3: WILD CHARGE (dash line + afterimages)
    # ============================================================
    def _draw_charge_ground(surface, boss, x, y, timer, phase):
        """Charge path streak on ground."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        path_len = int(180 * min(1.0, progress * 2))
        for i in range(0, path_len, 4):
            px = x + facing * (25 + i)
            py = y + 45 + int(math.sin(phase * 2 + i * 0.2) * 2)
            fade = 1 - i / max(1, path_len)
            alpha = _NS_rynvara._alpha(220 * fade)
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_darkest"], alpha),
                                (px - 5, py - 2, 10, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                (px - 4, py - 1, 8, 3))
            pygame.draw.ellipse(surface,
                                (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                (px - 3, py, 6, 2))
            if i % 8 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                 (px, py, 2, 2))
    def _draw_charge_foreground(surface, boss, x, y, timer, phase):
        """Afterimages + speed lines."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Afterimages behind
        for i in range(4):
            offset = -(i + 1) * 16 * facing
            alpha = _NS_rynvara._alpha(160 - i * 32)
            if alpha <= 0:
                continue
            silh = pygame.Surface((50, 80), pygame.SRCALPHA)
            for r in range(14, 4, -3):
                a = _NS_rynvara._alpha(alpha * (14 - r) / 14)
                _NS_rynvara._aacircle(silh,
                                       (*_NS_rynvara.PALETTE["fire_mid"], a),
                                       (25, 40), r)
            surface.blit(silh, (x + offset - 25, y - 40))
        # Speed lines
        for i in range(8):
            line_y = y - 25 + i * 6
            line_alpha = _NS_rynvara._alpha(200 - abs(4 - i) * 30)
            line_len = 25 + i * 3
            pygame.draw.line(surface,
                             (*_NS_rynvara.PALETTE["fire_mid"], line_alpha),
                             (x - facing * 16, line_y),
                             (x - facing * (16 + line_len), line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_rynvara.PALETTE["fire_hot"], line_alpha),
                             (x - facing * 16, line_y),
                             (x - facing * (16 + line_len // 2), line_y), 1)
    # ============================================================
    # SKILL 4: LIGHTNING TRAMPLE (leap slam + knock up)
    # ============================================================
    def _draw_trample_ground(surface, boss, x, y, timer, phase):
        """Big impact ring at target."""
        tx, ty = _NS_rynvara._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning circle grows
            t = progress / 0.4
            r = int(55 * t)
        else:
            r = 55 + int(math.sin(phase * 2) * 4)
        alpha = _NS_rynvara._alpha(220 * min(1.0, progress * 2))
        pygame.draw.ellipse(surface, (*_NS_rynvara.PALETTE["fire_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 3)
        pygame.draw.ellipse(surface, (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                            (tx - r + 8, ty - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 2)
        pygame.draw.ellipse(surface, (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                            (tx - r + 14, ty - r // 3 + 6,
                             r * 2 - 28, r * 2 // 3 - 12), 1)
        # Rotating runes
        for i in range(10):
            angle = phase * 1.5 + i * math.pi / 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_hot"],
                             (sx - 1, sy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_rynvara.PALETTE["fire_shine"],
                             (sx, sy, 1, 1))
    def _draw_trample_foreground(surface, boss, x, y, timer, phase):
        """Boss leaps + slam impact with knock up (rising particles)."""
        tx, ty = _NS_rynvara._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Wind-up — energy gathering
            t = progress / 0.4
            for i in range(8):
                angle = phase + i * math.pi / 4
                rise_t = (phase + i * 0.15) % 1.0
                rx = x + int(math.cos(angle) * 20)
                ry = y - int(rise_t * 30)
                alpha = _NS_rynvara._alpha(220 * t * (1 - rise_t))
                if alpha > 0:
                    _NS_rynvara._aacircle(surface,
                                           (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                           (rx, ry), 3)
                    _NS_rynvara._aacircle(surface,
                                           (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                           (rx, ry), 2)
        elif progress < 0.7:
            # SLAM — massive impact
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)
            # Big explosion
            imp_r = int(25 + t * 40)
            alpha = _NS_rynvara._alpha(240 * intensity)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_darkest"], alpha),
                                   (tx, ty), imp_r + 4, 4)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                   (tx, ty), imp_r, 3)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                   (tx, ty), max(1, imp_r - 8), 2)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_light"], alpha),
                                   (tx, ty), max(1, imp_r - 15), 1)
            _NS_rynvara._aacircle(surface,
                                   (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                   (tx, ty), max(1, imp_r // 4))
            # Radial shockwave
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * imp_r)
                ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                pygame.draw.line(surface,
                                 (*_NS_rynvara.PALETTE["fire_light"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_rynvara.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
            # KNOCK UP particles rising
            for i in range(12):
                p_angle = i * math.pi / 6
                p_dist = int(imp_r * 0.5)
                px_pos = tx + int(math.cos(p_angle) * p_dist)
                py_base = ty + int(math.sin(p_angle) * p_dist * 0.5)
                for layer in range(3):
                    l_t = (phase * 1.5 + i * 0.1 + layer * 0.3) % 1.0
                    py_pos = py_base - int(l_t * 20)
                    a = _NS_rynvara._alpha(alpha * (1 - l_t))
                    pygame.draw.rect(surface,
                                     (*_NS_rynvara.PALETTE["fire_hot"], a),
                                     (px_pos, py_pos, 2, 2))
        else:
            # Aftermath — smoke/embers
            t = (progress - 0.7) / 0.3
            for i in range(14):
                rise_t = (phase * 0.7 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 35)
                alpha = _NS_rynvara._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_rynvara._aacircle(surface,
                                           (*_NS_rynvara.PALETTE["fire_dark"], alpha),
                                           (rx, ry), 3)
                    _NS_rynvara._aacircle(surface,
                                           (*_NS_rynvara.PALETTE["fire_mid"], alpha),
                                           (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_rynvara.PALETTE["fire_hot"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# SYRINDRA (DARK SOVEREIGN) - Mini Boss
# ====================================================================

class _NS_syrindra:
    """Namespace syrindra - Dark Sovereign mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale, ghostly)
        "skin_darkest": (65, 50, 65),
        "skin_dark": (130, 105, 125),
        "skin_mid": (195, 170, 185),
        "skin_light": (235, 215, 225),
        "skin_shine": (255, 240, 245),
        # Hair (silver/white with slight purple tint)
        "hair_darkest": (60, 55, 75),
        "hair_dark": (120, 115, 140),
        "hair_mid": (185, 180, 200),
        "hair_light": (230, 225, 240),
        "hair_shine": (255, 250, 255),
        # Dress/gown (deep purple-black)
        "gown_darkest": (12, 5, 20),
        "gown_dark": (35, 15, 55),
        "gown_mid": (70, 30, 105),
        "gown_light": (130, 70, 175),
        "gown_shine": (185, 130, 220),
        # Dark accent (near-black)
        "black_dark": (8, 5, 15),
        "black_mid": (25, 15, 35),
        # Gold trim (ornaments, tiara)
        "gold_dark": (85, 60, 15),
        "gold_mid": (185, 145, 40),
        "gold_light": (235, 205, 90),
        "gold_shine": (255, 240, 160),
        # Silver/white metal (armor bits)
        "silver_dark": (55, 55, 70),
        "silver_mid": (120, 120, 140),
        "silver_light": (200, 200, 215),
        "silver_shine": (245, 245, 255),
        # DARK PURPLE MAGIC (signature — spheres, aura)
        "dark_darkest": (15, 5, 30),
        "dark_dark": (55, 15, 90),
        "dark_mid": (130, 45, 190),
        "dark_light": (195, 110, 235),
        "dark_hot": (230, 170, 255),
        "dark_shine": (250, 220, 255),
        # Bright violet (inner sphere glow)
        "violet_dark": (75, 20, 130),
        "violet_mid": (160, 60, 230),
        "violet_light": (220, 140, 255),
        # Eye glow (bright violet)
        "eye_dark": (60, 15, 120),
        "eye_mid": (170, 70, 240),
        "eye_hot": (230, 180, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_syrindra._clamp(color)
        if _NS_syrindra.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_syrindra._clamp(color)
        if _NS_syrindra.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_syrindra._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_syrindra(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_syrindra._detect_moving(boss)
        _NS_syrindra._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_syn_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient dark magic
        _NS_syrindra._draw_dark_aura(surface, x, y, pulse)
        _NS_syrindra._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":
            _NS_syrindra._draw_scatter_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_syrindra._draw_unleashed_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_syrindra._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_syrindra._draw_walk(surface, boss, x, y)
        else:
            _NS_syrindra._draw_idle(surface, boss, x, y)
        # Orbiting dark spheres (always present around body)
        _NS_syrindra._draw_orbiting_spheres(surface, boss, x, y, pulse)
        # Foreground skill FX
        if active_skill == "q":
            _NS_syrindra._draw_dark_sphere_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_syrindra._draw_force_of_will(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_syrindra._draw_scatter_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_syrindra._draw_unleashed_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_syn_previous_timer", 0))
        active = bool(getattr(boss, "_syn_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._syn_attack_active = True
            boss._syn_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._syn_attack_frame = int(getattr(boss, "_syn_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._syn_attack_active = False
            boss._syn_attack_frame = 0
            active = False
        boss._syn_previous_timer = timer
        boss._syn_attack_progress = (
            min(1.0, getattr(boss, "_syn_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_syn_last_x"):
            boss._syn_last_x = boss.x
            boss._syn_last_y = boss.y
            return False
        dx = abs(boss.x - boss._syn_last_x)
        dy = abs(boss.y - boss._syn_last_y)
        boss._syn_last_x = boss.x
        boss._syn_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating — elegant sorceress hover)
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_syrindra._draw_shadow(surface, x, y + 52)
        _NS_syrindra._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                 "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Elegant floating hover
        phase = boss.pulse * 1.6
        float_bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.5) * 3)
        _NS_syrindra._draw_shadow(surface, x + sway, y + 52, faded=True)
        _NS_syrindra._draw_dark_wisps(surface, x + sway, y + 44, phase,
                                       boss.direction)
        _NS_syrindra._draw_body(surface, x + sway, y + float_bob - 4,
                                 boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_syn_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Cast pose — sphere gathers → thrown → recovery
        if progress < 0.4:
            # Charge — pull hand back slightly with gathering sphere
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            # Thrust — release
            t = (progress - 0.4) / 0.2
            lunge = int((-3 + t * 10)) * boss.direction
            lift = int(3 - t * 3)
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            lunge = int(7 * (1 - t)) * boss.direction
            lift = int(-t)
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_syrindra._draw_shadow(surface, x + lunge, y + 52)
        _NS_syrindra._draw_body(surface, x + lunge, y - lift + bob,
                                 boss.direction, boss.pulse, "attack", progress)
        _NS_syrindra._draw_basic_dark_bolt(surface, boss, x + lunge,
                                            y - lift + bob, progress)
    # ============================================================
    # BODY (Elegant sorceress with flowing gown)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered: back hair → gown skirt (bottom flow) → gown top → arms → head + tiara."""
        # Back hair (behind, long)
        _NS_syrindra._draw_back_hair(surface, cx, cy - 12, facing, phase)
        # Flowing gown skirt (bottom, wide)
        _NS_syrindra._draw_gown_skirt(surface, cx, cy + 8, facing, phase, action)
        # Torso (upper gown + skin)
        _NS_syrindra._draw_torso(surface, cx, cy, facing, phase, action)
        # Rear arm (offhand)
        _NS_syrindra._draw_rear_arm(surface, cx, cy, facing, phase, action,
                                     attack_progress)
        # Head + face
        _NS_syrindra._draw_head(surface, cx + facing * 1, cy - 14, facing,
                                 phase, action)
        # TIARA/CROWN (spiky horn crown)
        _NS_syrindra._draw_tiara(surface, cx + facing * 1, cy - 20, facing,
                                  phase)
        # Front arm (casting hand)
        _NS_syrindra._draw_cast_arm(surface, cx, cy, facing, phase, action,
                                     attack_progress)
    def _draw_back_hair(surface, cx, cy, facing, phase):
        """Long silver hair flowing down back."""
        back = -facing
        wave = math.sin(phase * 0.5) * 2
        wave2 = math.sin(phase * 0.4 + 1) * 2
        # Main hair mass behind (long, flowing to waist level)
        hair_pts = [
            (cx - 6, cy),
            (cx - 8, cy + 4),
            (cx - 10, cy + 10 + int(wave)),
            (cx - 9, cy + 18 + int(wave)),
            (cx - 6, cy + 24 + int(wave2)),
            (cx - 2, cy + 28 + int(wave)),
            (cx + 2, cy + 28 + int(wave2)),
            (cx + 6, cy + 24 + int(wave)),
            (cx + 9, cy + 18 + int(wave2)),
            (cx + 10, cy + 10 + int(wave)),
            (cx + 8, cy + 4),
            (cx + 6, cy),
        ]
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in hair_pts])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_darkest"],
                           hair_pts)
        # Shading
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_dark"], [
            (cx - 5, cy + 1),
            (cx - 7, cy + 6),
            (cx - 8, cy + 16),
            (cx - 5, cy + 22),
            (cx - 1, cy + 25),
            (cx + 1, cy + 25),
            (cx + 5, cy + 22),
            (cx + 8, cy + 16),
            (cx + 7, cy + 6),
            (cx + 5, cy + 1),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_mid"], [
            (cx - 4, cy + 2),
            (cx - 5, cy + 10),
            (cx - 4, cy + 18),
            (cx - 1, cy + 22),
            (cx + 1, cy + 22),
            (cx + 4, cy + 18),
            (cx + 5, cy + 10),
            (cx + 4, cy + 2),
        ])
        # Highlight strands (light hair)
        for i, (sx_off, sy_start, sy_end) in enumerate([
            (-3, 3, 20),
            (-1, 3, 24),
            (1, 3, 24),
            (3, 3, 20),
        ]):
            wave_off = int(math.sin(phase * 0.4 + i) * 1)
            pygame.draw.line(surface, _NS_syrindra.PALETTE["hair_light"],
                             (cx + sx_off + wave_off, cy + sy_start),
                             (cx + sx_off + wave_off, cy + sy_end), 1)
        # Bright single strand
        pygame.draw.line(surface, _NS_syrindra.PALETTE["hair_shine"],
                         (cx, cy + 4), (cx, cy + 22), 1)
    def _draw_gown_skirt(surface, cx, cy, facing, phase, action):
        """Long flowing gown skirt — wide bottom, dark purple."""
        wave = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.5 + 1) * 2
        # Skirt shape (wide flowing bottom)
        skirt = [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 12, cy + 4),
            (cx + 18, cy + 14 + int(wave)),
            (cx + 22, cy + 22 + int(wave2)),
            (cx + 20, cy + 28),
            (cx + 12, cy + 30 + int(wave)),
            (cx + 4, cy + 32 + int(wave2)),
            (cx - 4, cy + 32 + int(wave)),
            (cx - 12, cy + 30 + int(wave2)),
            (cx - 20, cy + 28),
            (cx - 22, cy + 22 + int(wave)),
            (cx - 18, cy + 14 + int(wave2)),
            (cx - 12, cy + 4),
        ]
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in skirt])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_darkest"], skirt)
        # Inner shading layer
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_dark"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3),
            (cx + 11, cy + 4), (cx + 17, cy + 14),
            (cx + 20, cy + 22), (cx + 18, cy + 27),
            (cx + 10, cy + 28), (cx + 3, cy + 30),
            (cx - 3, cy + 30), (cx - 10, cy + 28),
            (cx - 18, cy + 27), (cx - 20, cy + 22),
            (cx - 17, cy + 14), (cx - 11, cy + 4),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_mid"], [
            (cx - 5, cy - 1), (cx + 5, cy - 1),
            (cx + 9, cy + 5), (cx + 13, cy + 15),
            (cx + 15, cy + 22), (cx + 12, cy + 25),
            (cx + 4, cy + 26), (cx - 4, cy + 26),
            (cx - 12, cy + 25), (cx - 15, cy + 22),
            (cx - 13, cy + 15), (cx - 9, cy + 5),
        ])
        # Highlight along center front (vertical fold)
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_light"], [
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 3, cy + 6),
            (cx + 2, cy + 20),
            (cx - 2, cy + 20),
            (cx - 3, cy + 6),
        ])
        # Vertical fold lines
        for fold_x_off in (-9, -5, 5, 9):
            base_x = cx + fold_x_off
            end_x = cx + fold_x_off + fold_x_off // 3
            pygame.draw.line(surface, _NS_syrindra.PALETTE["gown_darkest"],
                             (base_x, cy + 2), (end_x, cy + 26), 1)
        # Gold trim along bottom hem
        pygame.draw.line(surface, _NS_syrindra.PALETTE["gold_dark"],
                         (cx - 20, cy + 27), (cx + 20, cy + 27), 2)
        pygame.draw.line(surface, _NS_syrindra.PALETTE["gold_mid"],
                         (cx - 20, cy + 28), (cx + 20, cy + 28), 1)
        # Bright edge highlights
        for hi_x in range(-16, 17, 8):
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["gold_shine"],
                             (cx + hi_x, cy + 28, 2, 1))
        # Small purple magic runes on skirt
        rune_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, (rx_off, ry_off) in enumerate([(-8, 12), (8, 15), (0, 20)]):
            rx = cx + rx_off
            ry = cy + ry_off
            for r in range(3, 0, -1):
                a = _NS_syrindra._alpha(180 * (3 - r) / 3 * rune_pulse)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_mid"], a),
                                        (rx, ry), r)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (rx, ry, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Upper body — gown top with skin details."""
        # Torso shape (slim elegant)
        torso = [
            (cx - 6, cy - 6),
            (cx + 6, cy - 6),
            (cx + 8, cy - 2),
            (cx + 8, cy + 5),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 8, cy + 5),
            (cx - 8, cy - 2),
        ]
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in torso])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_darkest"], torso)
        # Gown top layers
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_dark"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 7, cy - 2), (cx + 7, cy + 4),
            (cx + 5, cy + 9), (cx - 5, cy + 9),
            (cx - 7, cy + 4), (cx - 7, cy - 2),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_mid"], [
            (cx - 3, cy - 3), (cx + 3, cy - 3),
            (cx + 5, cy), (cx + 4, cy + 6),
            (cx + 2, cy + 8), (cx - 2, cy + 8),
            (cx - 4, cy + 6), (cx - 5, cy),
        ])
        # Highlight (vertical center)
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_light"], [
            (cx - 1, cy - 2),
            (cx + 1, cy - 2),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
        ])
        # Skin V neckline
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["skin_dark"], [
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx, cy - 2),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["skin_mid"], [
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["skin_light"],
                         (cx, cy - 4, 1, 1))
        # Gold collar/necklace
        pygame.draw.line(surface, _NS_syrindra.PALETTE["gold_dark"],
                         (cx - 5, cy - 5), (cx + 5, cy - 5), 1)
        pygame.draw.line(surface, _NS_syrindra.PALETTE["gold_mid"],
                         (cx - 3, cy - 5), (cx + 3, cy - 5), 1)
        # Central gem/pendant
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            a = _NS_syrindra._alpha(200 * (3 - r) / 3 * pulse)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], a),
                                    (cx, cy - 3), r)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                         (cx, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                         (cx, cy - 3, 1, 1))
        # Shoulder armor spikes (small)
        for side in (-1, 1):
            sp_x = cx + side * 7
            sp_y = cy - 6
            # Small metal shoulder cap
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["silver_dark"],
                                    (sp_x, sp_y), 2)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["silver_light"],
                             (sp_x, sp_y - 1, 1, 1))
            # Small spike above
            pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_dark"],
                             (sp_x, sp_y - 1), (sp_x, sp_y - 4), 2)
            pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_light"],
                             (sp_x, sp_y - 1), (sp_x, sp_y - 4), 1)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["silver_shine"],
                             (sp_x, sp_y - 4, 1, 1))
        # Corset lines (X-pattern lacing in center)
        for i, (y1, y2) in enumerate([(cy - 1, cy + 2), (cy + 2, cy + 5),
                                       (cy + 5, cy + 8)]):
            pygame.draw.line(surface, _NS_syrindra.PALETTE["gold_dark"],
                             (cx - 2, y1), (cx + 2, y2), 1)
            pygame.draw.line(surface, _NS_syrindra.PALETTE["gold_dark"],
                             (cx + 2, y1), (cx - 2, y2), 1)
        # Belt
        belt_y = cy + 9
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["gold_dark"],
                         (cx - 6, belt_y, 12, 2))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["gold_mid"],
                         (cx - 6, belt_y, 12, 1))
        # Belt central buckle
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["gold_mid"],
                         (cx - 2, belt_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_mid"],
                         (cx - 1, belt_y, 2, 2))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                         (cx, belt_y, 1, 1))
    def _draw_rear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm — usually gestures gracefully, holds a floating sphere."""
        back = -facing
        shoulder = (cx + back * 5, cy - 4)
        gesture = math.sin(phase * 0.7) * 2
        if action == "attack":
            # Slight movement during cast
            if attack_progress < 0.4:
                elbow_off_x = back * 3
                elbow_off_y = 2 - int(attack_progress / 0.4 * 2)
            else:
                elbow_off_x = back * 3
                elbow_off_y = 0
        else:
            elbow_off_x = back * 3
            elbow_off_y = 2 + int(gesture)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (elbow[0] + back * 3, elbow[1] + 5)
        # Long draped sleeve (upper arm — gown sleeve)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["gown_darkest"],
                              shoulder, elbow, 5)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["gown_dark"],
                              shoulder, elbow, 4)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["gown_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 2)
        # Draped hanging sleeve fabric below elbow
        drape_x = elbow[0] + back * 2
        drape_y_end = elbow[1] + 12 + int(math.sin(phase * 0.6) * 2)
        drape_pts = [
            (elbow[0], elbow[1]),
            (elbow[0] + back * 2, elbow[1] + 3),
            (elbow[0] + back * 4, elbow[1] + 8),
            (drape_x, drape_y_end),
            (elbow[0], drape_y_end - 2),
            (elbow[0], elbow[1] + 4),
        ]
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_darkest"],
                           drape_pts)
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_dark"], [
            (elbow[0] + back, elbow[1] + 1),
            (elbow[0] + back * 3, elbow[1] + 8),
            (elbow[0] + back * 2, drape_y_end - 3),
            (elbow[0], drape_y_end - 3),
        ])
        # Forearm (bare pale skin peeking)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 4)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["skin_darkest"],
                              elbow, hand, 3)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["skin_dark"],
                              elbow, hand, 2)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["skin_mid"],
                              (elbow[0], elbow[1] - 1),
                              (hand[0], hand[1] - 1), 1)
        # Slender hand with gesture
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["skin_dark"],
                                hand, 2)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["skin_mid"],
                                hand, 1)
        # Small floating dark sphere near hand (companion sphere)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        sphere_x = hand[0] + back * 3 + int(math.sin(phase * 1.2) * 1)
        sphere_y = hand[1] - 2 + int(math.cos(phase * 1.5) * 1)
        _NS_syrindra._draw_small_sphere(surface, sphere_x, sphere_y, 4, pulse)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Elegant sorceress face — pale skin, glowing violet eyes."""
        # Head shape (slender oval)
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
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["skin_darkest"], head)
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["skin_dark"], [
            (cx - 3, cy - 2), (cx - 4, cy - 4),
            (cx - 2, cy - 7), (cx, cy - 8),
            (cx + 2, cy - 7), (cx + 4, cy - 4),
            (cx + 4, cy - 1), (cx + 3, cy + 2),
            (cx + 1, cy + 4), (cx - 1, cy + 4), (cx - 3, cy + 2),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["skin_mid"], [
            (cx - 3, cy - 3), (cx - 2, cy - 6),
            (cx, cy - 7), (cx + 2, cy - 6),
            (cx + 3, cy - 3),
        ])
        # Highlight (elegant)
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["skin_light"], [
            (cx + facing, cy - 5),
            (cx + 3 * facing, cy - 4),
            (cx + 3 * facing, cy - 2),
            (cx + facing, cy - 2),
        ])
        # HAIR bangs framing face
        hair_wave = math.sin(phase * 0.4) * 1
        # Left side bang
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_darkest"], [
            (cx - 5, cy - 5),
            (cx - 6, cy - 8),
            (cx - 5, cy - 10 + int(hair_wave)),
            (cx - 3, cy - 8),
            (cx - 4, cy - 5),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_dark"], [
            (cx - 5, cy - 6),
            (cx - 5, cy - 9),
            (cx - 4, cy - 9),
            (cx - 4, cy - 6),
        ])
        # Right side bang
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_darkest"], [
            (cx + 5, cy - 5),
            (cx + 6, cy - 8),
            (cx + 5, cy - 10 + int(hair_wave)),
            (cx + 3, cy - 8),
            (cx + 4, cy - 5),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_dark"], [
            (cx + 5, cy - 6),
            (cx + 5, cy - 9),
            (cx + 4, cy - 9),
            (cx + 4, cy - 6),
        ])
        # Center forehead bang
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_darkest"], [
            (cx - 3, cy - 7),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
            (cx + 3, cy - 7),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["hair_dark"], [
            (cx - 2, cy - 7),
            (cx - 1, cy - 8),
            (cx + 1, cy - 8),
            (cx + 2, cy - 7),
        ])
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["hair_mid"],
                         (cx, cy - 8, 1, 1))
        # Trailing bangs at side (long strand)
        for side in (-1, 1):
            strand_x = cx + side * 5
            strand_y_start = cy - 4
            strand_y_end = cy + 4
            wave_off = int(math.sin(phase * 0.5 + side) * 1)
            pygame.draw.line(surface, _NS_syrindra.PALETTE["hair_darkest"],
                             (strand_x, strand_y_start),
                             (strand_x + wave_off, strand_y_end), 2)
            pygame.draw.line(surface, _NS_syrindra.PALETTE["hair_dark"],
                             (strand_x, strand_y_start),
                             (strand_x + wave_off, strand_y_end), 1)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["hair_light"],
                             (strand_x + wave_off, strand_y_end, 1, 1))
        # EYES — bright violet magic glow
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Sockets
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 2, 2))
        # Whites
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["skin_shine"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["skin_shine"],
                         (cx + 1, cy - 5, 2, 2))
        # Violet pupils
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["eye_dark"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["eye_dark"],
                         (cx + 2, cy - 5, 1, 2))
        # Glow halo
        for r in range(4, 0, -1):
            a = _NS_syrindra._alpha(120 * (4 - r) / 4 * eye_pulse)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["eye_mid"], a),
                                    (cx - 2, cy - 4), r)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["eye_mid"], a),
                                    (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["eye_hot"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["eye_hot"],
                         (cx + 2, cy - 4, 1, 1))
        # Nose (small, elegant)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["skin_darkest"],
                         (cx, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["skin_light"],
                         (cx + facing, cy - 2, 1, 1))
        # Lips (dark purple)
        pygame.draw.line(surface, _NS_syrindra.PALETTE["gown_mid"],
                         (cx - 1, cy + 2), (cx + 1, cy + 2), 1)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_light"],
                         (cx, cy + 2, 1, 1))
        # Small dark tattoo/mark on forehead (like Syndra's tiara jewel base)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_mid"],
                         (cx, cy - 6, 1, 1))
    def _draw_tiara(surface, cx, cy, facing, phase):
        """Spiky crown/tiara with center jewel — Syndra signature."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Base band across forehead
        pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_dark"],
                         (cx - 5, cy + 5), (cx + 5, cy + 5), 2)
        pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_mid"],
                         (cx - 5, cy + 5), (cx + 5, cy + 5), 1)
        pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_shine"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
        # Spike horns (Syndra's iconic — 2 big curving up)
        for side in (-1, 1):
            # Base of horn
            base_x = cx + side * 4
            base_y = cy + 4
            # Curve outward-up
            mid_x = cx + side * 7
            mid_y = cy - 1
            tip_x = cx + side * 5
            tip_y = cy - 6
            # Horn shape (curved triangle)
            horn_pts = [
                (base_x, base_y),
                (base_x + side, base_y - 1),
                (mid_x, mid_y),
                (tip_x, tip_y),
                (tip_x - side, tip_y + 1),
                (mid_x - side * 2, mid_y + 1),
                (base_x - side, base_y),
            ]
            _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 1) for p in horn_pts])
            _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["silver_dark"],
                               horn_pts)
            _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["silver_mid"], [
                (base_x, base_y),
                (mid_x - side, mid_y),
                (tip_x, tip_y),
                (tip_x - side, tip_y + 1),
                (mid_x - side * 2, mid_y + 1),
            ])
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["silver_shine"],
                             (tip_x, tip_y, 1, 1))
        # CENTER JEWEL (big violet orb — glowing)
        jewel_x = cx
        jewel_y = cy + 3
        # Glow halo
        for r in range(6, 0, -1):
            a = _NS_syrindra._alpha(180 * (6 - r) / 6 * pulse)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], a),
                                    (jewel_x, jewel_y), r)
        # Jewel body
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                (jewel_x, jewel_y), 3)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                (jewel_x, jewel_y), 2)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_mid"],
                                (jewel_x, jewel_y), 1)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                         (jewel_x, jewel_y, 1, 1))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                         (jewel_x, jewel_y, 1, 1))
        # Small back spikes (3 smaller)
        for i, (x_off, tip_off_y) in enumerate([(-2, -3), (0, -4), (2, -3)]):
            spike_x = cx + x_off
            spike_base_y = cy + 3
            spike_tip_y = cy + tip_off_y
            pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_dark"],
                             (spike_x, spike_base_y),
                             (spike_x, spike_tip_y), 2)
            pygame.draw.line(surface, _NS_syrindra.PALETTE["silver_mid"],
                             (spike_x, spike_base_y),
                             (spike_x, spike_tip_y), 1)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["silver_shine"],
                             (spike_x, spike_tip_y, 1, 1))
    def _draw_cast_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front casting arm — main spellcasting hand."""
        shoulder = (cx + facing * 5, cy - 4)
        if action == "attack":
            if attack_progress < 0.4:
                # Charge — pull hand back with gathering sphere
                t = attack_progress / 0.4
                elbow_off_x = facing * int(3 - t * 2)
                elbow_off_y = int(2 - t * 3)
                hand_off_x = facing * int(6 + t * 2)
                hand_off_y = int(3 - t * 5)
            elif attack_progress < 0.6:
                # THRUST — release forward
                t = (attack_progress - 0.4) / 0.2
                elbow_off_x = facing * int(1 + t * 6)
                elbow_off_y = int(-1 + t * 2)
                hand_off_x = facing * int(8 + t * 10)
                hand_off_y = int(-2 + t * 3)
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                elbow_off_x = facing * int(7 - t * 3)
                elbow_off_y = int(1 - t)
                hand_off_x = facing * int(18 - t * 12)
                hand_off_y = int(1 - t)
        else:
            # Idle — hand held forward gracefully
            sway = math.sin(phase * 0.6) * 1
            elbow_off_x = facing * 4
            elbow_off_y = int(1 + sway)
            hand_off_x = facing * 8
            hand_off_y = int(3 + sway)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # Gown sleeve (upper arm)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["gown_darkest"],
                              shoulder, elbow, 5)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["gown_dark"],
                              shoulder, elbow, 4)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["gown_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 2)
        # Draped sleeve fabric hanging below elbow
        drape_x_end = elbow[0] + facing * 2 + int(math.sin(phase * 0.6) * 1)
        drape_y_end = elbow[1] + 10 + int(math.sin(phase * 0.5) * 1)
        drape_pts = [
            (elbow[0], elbow[1]),
            (elbow[0] + facing * 3, elbow[1] + 3),
            (elbow[0] + facing * 4, elbow[1] + 7),
            (drape_x_end, drape_y_end),
            (elbow[0] - facing, drape_y_end - 2),
            (elbow[0] - facing, elbow[1] + 3),
        ]
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_darkest"],
                           drape_pts)
        _NS_syrindra._poly(surface, _NS_syrindra.PALETTE["gown_dark"], [
            (elbow[0] + facing, elbow[1] + 1),
            (elbow[0] + facing * 3, elbow[1] + 6),
            (drape_x_end - facing, drape_y_end - 2),
            (elbow[0], drape_y_end - 2),
        ])
        # Forearm (bare pale skin)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 4)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["skin_darkest"],
                              elbow, hand, 3)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["skin_dark"],
                              elbow, hand, 2)
        _NS_syrindra._aaline(surface, _NS_syrindra.PALETTE["skin_mid"],
                              (elbow[0], elbow[1] - 1),
                              (hand[0], hand[1] - 1), 1)
        # Slender hand (fingers spread for cast)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["skin_dark"],
                                hand, 3)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["skin_mid"],
                                hand, 2)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["skin_light"],
                                hand, 1)
        # DARK SPHERE at casting hand (main sphere she conjures)
        sphere_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Size grows during charge
        if action == "attack" and attack_progress < 0.4:
            sphere_size = 4 + int(attack_progress / 0.4 * 3)
        elif action == "attack" and 0.4 <= attack_progress < 0.6:
            sphere_size = 7  # ready to throw
        else:
            sphere_size = 5
        sphere_x = hand[0] + facing * 3
        sphere_y = hand[1] - 1
        _NS_syrindra._draw_dark_sphere(surface, sphere_x, sphere_y,
                                        sphere_size, sphere_pulse, phase)
    def _draw_small_sphere(surface, sx, sy, size, pulse):
        """Small dark sphere (for offhand or nearby orbits)."""
        # Halo
        for r in range(size + 3, size, -1):
            a = _NS_syrindra._alpha(120 * (size + 3 - r) / 3 * pulse)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], a),
                                    (sx, sy), r)
        # Sphere body
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["shadow_deep"],
                                (sx + 1, sy + 1), size)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                (sx, sy), size)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                (sx, sy), size - 1)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_dark"],
                                (sx, sy), max(1, size - 2))
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_mid"],
                                (sx, sy), max(1, size - 3))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                         (sx, sy, 1, 1))
    def _draw_dark_sphere(surface, sx, sy, size, pulse, phase):
        """Main dark sphere with more elaborate glow + swirling particles."""
        # Big halo
        for r in range(size + 6, size, -1):
            a = _NS_syrindra._alpha(150 * (size + 6 - r) / 6 * pulse)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], a),
                                    (sx, sy), r)
        # Sphere layers
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["shadow_deep"],
                                (sx + 1, sy + 1), size + 1)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                (sx, sy), size)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                (sx, sy), size - 1)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_dark"],
                                (sx, sy), max(1, size - 2))
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_mid"],
                                (sx, sy), max(1, size - 3))
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_light"],
                                (sx, sy), max(1, size - 4))
        # Bright core
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                         (sx, sy, 1, 1))
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                         (sx, sy, 1, 1))
        # Swirling particles around sphere
        for i in range(5):
            angle = phase * 3 + i * math.pi * 2 / 5
            pr = size + 2
            px = sx + int(math.cos(angle) * pr)
            py = sy + int(math.sin(angle) * pr)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (px, py, 1, 1))
        # Wispy trail lines
        for i in range(3):
            wisp_angle = phase * 1.5 + i * math.pi * 2 / 3
            end_x = sx + int(math.cos(wisp_angle) * (size + 4))
            end_y = sy + int(math.sin(wisp_angle) * (size + 4))
            pygame.draw.line(surface, _NS_syrindra.PALETTE["dark_light"],
                             (sx, sy), (end_x, end_y), 1)
    # ============================================================
    # ORBITING SPHERES (4 dark spheres around body — always visible)
    # ============================================================
    def _draw_orbiting_spheres(surface, boss, x, y, phase):
        """4 dark spheres orbiting the sorceress."""
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            orbit_r = 34 + int(math.sin(phase + i) * 4)
            sx = x + int(math.cos(angle) * orbit_r)
            sy = y - 8 + int(math.sin(angle) * orbit_r * 0.55)
            pulse = math.sin(phase * 2 + i * 0.5) * 0.3 + 0.7
            _NS_syrindra._draw_small_sphere(surface, sx, sy, 5, pulse)
            # Extra swirling particle
            spark_angle = phase * 4 + i
            spark_x = sx + int(math.cos(spark_angle) * 7)
            spark_y = sy + int(math.sin(spark_angle) * 7)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (spark_x, spark_y, 1, 1))
    # ============================================================
    # BASIC ATTACK — dark bolt
    # ============================================================
    def _draw_basic_dark_bolt(surface, boss, x, y, progress):
        """Small dark sphere bolt — basic ranged attack."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_syrindra._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 5
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_syrindra._alpha(230 - i * 25)
            size = max(1, 6 - i)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                                    (px, py), size + 1)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                    (px, py), size)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["violet_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["violet_mid"], alpha),
                                    (px, py), max(1, size - 2))
        # Bright head
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                (bx, by), 6)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                (bx, by), 5)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_dark"],
                                (bx, by), 4)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_mid"],
                                (bx, by), 2)
        _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_light"],
                                (bx, by), 1)
        pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                         (bx, by, 1, 1))
        # Swirling sparks
        for i in range(4):
            angle = t * 8 + i * math.pi / 2
            sx = bx + int(math.cos(angle) * 6)
            sy = by + int(math.sin(angle) * 6)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (sx, sy, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 15)
            alpha = _NS_syrindra._alpha(240 * (1 - st))
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                    (tx, ty), radius, 2)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["violet_light"], alpha),
                                    (tx, ty), max(1, radius - 5), 1)
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((130, 28), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(13, 0, -1):
            alpha = int(max(0, (13 - radius) * 17) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (8 - radius, 14 - radius,
                                 114 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 3, 8, int(160 * mult)),
                            (4, 6, 122, 16))
        pygame.draw.ellipse(shadow, (30, 10, 45, int(120 * mult)),
                            (10, 8, 110, 12))
        surface.blit(shadow, (x - 65, y - 14))
    def _draw_dark_aura(surface, x, y, phase):
        """Dark purple aura pulsing."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_syrindra._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_syrindra._aacircle(aura,
                                        (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                                        (110, 90), radius)
        for radius in range(60, 5, -3):
            alpha = _NS_syrindra._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_syrindra._aacircle(aura,
                                        (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                        (110, 90), radius)
        for radius in range(35, 5, -2):
            alpha = _NS_syrindra._alpha((35 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_syrindra._aacircle(aura,
                                        (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                        (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating dark particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 44 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Purple ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_syrindra.PALETTE["dark_darkest"], 210),
                            (5, 20, 160, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_syrindra.PALETTE["dark_dark"], 220),
                            (14, 22, 142, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_syrindra.PALETTE["dark_mid"], 230),
                            (25, 24, 120, 20), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 48)
            y1 = 32 + int(math.sin(angle) * 9)
            x2 = 85 + int(math.cos(angle) * 70)
            y2 = 32 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_syrindra.PALETTE["dark_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_syrindra.PALETTE["dark_shine"],
                                       _NS_syrindra._alpha(150 * pulse)),
                                (15, 12, 140, 42), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_dark_wisps(surface, cx, cy, phase, facing):
        """Dark wisps trail during floating."""
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            wx = cx + int(math.sin(phase + i) * 10) - facing * i * 3
            wy = cy + int(t * 12)
            alpha = _NS_syrindra._alpha(200 * (1 - t))
            if alpha > 0:
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                        (wx, wy), 3)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # SKILL Q - DARK SPHERE (single big sphere projectile)
    # ============================================================
    def _draw_dark_sphere_skill(surface, boss, x, y, timer, phase):
        """Big dark sphere projectile."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_syrindra._target_position(boss, x, y)
        if progress < 0.25:
            # Charge at hand
            t = progress / 0.25
            mx = x + facing * 18
            my = y - 4
            cr = int(4 + t * 10)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_syrindra._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                                        (mx, my), r)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                    (mx, my), cr - 2)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_dark"],
                                    (mx, my), max(1, cr - 4))
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_mid"],
                                    (mx, my), max(1, cr - 6))
            # Sparks
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = mx + int(math.cos(angle) * (cr + 3))
                sy = my + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                                 (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 22
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Long trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_syrindra._alpha(240 - i * 20)
                size = max(1, 9 - i)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                                        (px, py), size + 1)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                        (px, py), size)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["violet_dark"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["violet_mid"], alpha),
                                        (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(3):
                        sp_angle = t * 8 + i + s * math.pi * 2 / 3
                        sp_x = px + int(math.cos(sp_angle) * (size + 2))
                        sp_y = py + int(math.sin(sp_angle) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                         (sp_x, sp_y, 1, 1))
            # Big head with halo
            for r in range(14, 3, -2):
                alpha = _NS_syrindra._alpha(120 * (14 - r) / 14)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                        (bx, by), r)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                    (bx, by), 8)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                    (bx, by), 6)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_dark"],
                                    (bx, by), 4)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_mid"],
                                    (bx, by), 2)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["violet_light"],
                             (bx, by, 1, 1))
            # Shatter impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 25)
                alpha = _NS_syrindra._alpha(240 * (1 - st))
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                        (tx, ty), radius, 2)
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["violet_light"], alpha),
                                        (tx, ty), max(1, radius - 6), 1)
                # Shatter fragments (radiating lines)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_syrindra.PALETTE["dark_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - FORCE OF WILL (throw all orbiting spheres at target)
    # ============================================================
    def _draw_force_of_will(surface, boss, x, y, timer, phase):
        """All 4 orbiting spheres fly to target in fan pattern."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_syrindra._target_position(boss, x, y)
        if progress < 0.2:
            # Gather — spheres come close to boss
            t = progress / 0.2
            for i in range(4):
                start_angle = i * math.pi / 2
                orbit_r = int(34 * (1 - t) + 10 * t)
                sx = x + int(math.cos(start_angle) * orbit_r)
                sy = y - 8 + int(math.sin(start_angle) * orbit_r * 0.55)
                _NS_syrindra._draw_small_sphere(surface, sx, sy, 6, 0.9)
        else:
            # LAUNCH — spheres fly in fan
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 12
            start_y = y - 4
            for i in range(4):
                fan_off_y = int((i - 1.5) * 22)
                effective_ty = ty + fan_off_y
                sphere_t = min(1.0, t * 1.1)
                if sphere_t <= 0:
                    continue
                bx = int(start_x + (tx - start_x) * sphere_t)
                by = int(start_y + (effective_ty - start_y) * sphere_t)
                # Trail
                for tr in range(5):
                    trail_t = max(0.0, sphere_t - tr * 0.06)
                    px = int(start_x + (tx - start_x) * trail_t)
                    py = int(start_y + (effective_ty - start_y) * trail_t)
                    alpha = _NS_syrindra._alpha(220 - tr * 35)
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                            (px, py), max(1, 5 - tr))
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["violet_mid"], alpha),
                                            (px, py), max(1, 3 - tr))
                # Head
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                        (bx, by), 6)
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_dark"],
                                        (bx, by), 5)
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_dark"],
                                        (bx, by), 3)
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_light"],
                                        (bx, by), 1)
                pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                                 (bx, by, 1, 1))
            # Impact aftermath
            if t > 0.85:
                st = (t - 0.85) / 0.15
                alpha = _NS_syrindra._alpha(220 * (1 - st))
                for offset_i in range(4):
                    fan_off_y = int((offset_i - 1.5) * 22)
                    impact_r = int(10 + st * 12)
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                            (tx, ty + fan_off_y), impact_r, 2)
                    for j in range(6):
                        angle = j * math.pi / 3
                        ex = tx + int(math.cos(angle) * impact_r)
                        ey = ty + fan_off_y + int(math.sin(angle) * impact_r * 0.7)
                        pygame.draw.rect(surface,
                                         (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                         (ex, ey, 2, 2))
    # ============================================================
    # SKILL E - SCATTER THE WEAK (push wave)
    # ============================================================
    def _draw_scatter_ground(surface, boss, x, y, timer, phase):
        """Ground push wave in front of boss."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Expanding cone/wave in front
        if progress > 0.2:
            wave_progress = (progress - 0.2) / 0.8
            wave_dist = int(80 * wave_progress)
            for offset in range(0, wave_dist, 4):
                px = x + facing * (25 + offset)
                py = y + 45 + int(math.sin(phase * 2 + offset * 0.2) * 2)
                fade = 1 - offset / max(1, wave_dist)
                alpha = _NS_syrindra._alpha(220 * fade)
                pygame.draw.ellipse(surface,
                                    (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                    (px - 6, py - 2, 12, 4))
                pygame.draw.ellipse(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                    (px - 4, py - 1, 8, 3))
                if offset % 8 == 0:
                    pygame.draw.rect(surface,
                                     (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                     (px, py, 2, 2))
    def _draw_scatter_foreground(surface, boss, x, y, timer, phase):
        """Push wave — curved arcs radiating forward from hand."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Gather energy at hand
            t = progress / 0.2
            hand_x = x + facing * 18
            hand_y = y - 4
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                a = _NS_syrindra._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_syrindra._aacircle(surface,
                                        (*_NS_syrindra.PALETTE["dark_mid"], a),
                                        (hand_x, hand_y), r)
            _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_mid"],
                                    (hand_x, hand_y), cr - 2)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (hand_x, hand_y, 1, 1))
        else:
            # PUSH WAVE — arcing radial energy forward
            t = (progress - 0.2) / 0.8
            hand_x = x + facing * 18
            hand_y = y - 4
            # Multiple curved arc trails going outward
            num_arcs = 5
            for arc_i in range(num_arcs):
                arc_angle_off = (arc_i - num_arcs / 2) * 0.35
                arc_len = int(70 * min(1.0, t * 1.4))
                # Draw arc as curved trail
                num_segs = 12
                max_seg = int(num_segs * min(1.0, t * 1.3))
                for seg_i in range(max_seg):
                    seg_t = seg_i / num_segs
                    # Straight line with slight curve
                    seg_dist = int(seg_t * arc_len)
                    curve_off = int(math.sin(seg_t * math.pi) * 4)
                    px = hand_x + facing * seg_dist
                    py = hand_y + int(seg_dist * arc_angle_off) - curve_off
                    fade = (max_seg - seg_i) / max(1, max_seg)
                    alpha = _NS_syrindra._alpha(230 * fade * (1 - t * 0.3))
                    size = max(1, 5 - seg_i // 3)
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                            (px, py), size + 1)
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                            (px, py), size)
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["violet_mid"], alpha),
                                            (px, py), max(1, size - 2))
                    pygame.draw.rect(surface,
                                     (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                     (px, py, 1, 1))
    # ============================================================
    # SKILL R - UNLEASHED POWER (all spheres explode into target)
    # ============================================================
    def _draw_unleashed_ground(surface, boss, x, y, timer, phase):
        """Massive impact zone at target."""
        tx, ty = _NS_syrindra._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growing warning circle
        if progress < 0.35:
            t = progress / 0.35
            r = int(50 * t)
        else:
            r = 50 + int(math.sin(phase * 2) * 4)
        alpha = _NS_syrindra._alpha(220 * min(1.0, progress * 2))
        # Multi-ring
        pygame.draw.ellipse(surface, (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 3)
        pygame.draw.ellipse(surface, (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                            (tx - r + 8, ty - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 2)
        pygame.draw.ellipse(surface, (*_NS_syrindra.PALETTE["violet_mid"], alpha),
                            (tx - r + 14, ty - r // 3 + 6,
                             r * 2 - 28, r * 2 // 3 - 12), 1)
        # Rotating runes
        for i in range(10):
            angle = phase * 1.5 + i * math.pi / 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_hot"],
                             (sx - 1, sy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                             (sx, sy, 1, 1))
    def _draw_unleashed_foreground(surface, boss, x, y, timer, phase):
        """All spheres gather → massive barrage at target."""
        facing = boss.direction
        tx, ty = _NS_syrindra._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Gather — many spheres orbit closer around boss
            t = progress / 0.3
            num_orbs = 8
            for i in range(num_orbs):
                angle = phase * 2 + i * math.pi * 2 / num_orbs
                orbit_r = int(45 * (1 - t) + 15 * t)
                sx = x + int(math.cos(angle) * orbit_r)
                sy = y - 8 + int(math.sin(angle) * orbit_r * 0.6)
                _NS_syrindra._draw_small_sphere(surface, sx, sy, 6, 0.9)
        elif progress < 0.8:
            # BARRAGE — spheres fire to target in fan
            t = (progress - 0.3) / 0.5
            num_orbs = 8
            start_x = x
            start_y = y - 4
            for i in range(num_orbs):
                orb_t = min(1.0, max(0.0, t * 1.4 - i * 0.05))
                if orb_t <= 0:
                    continue
                fan_off_y = int((i - num_orbs / 2 + 0.5) * 14)
                effective_ty = ty + fan_off_y
                bx = int(start_x + (tx - start_x) * orb_t)
                by = int(start_y + (effective_ty - start_y) * orb_t)
                # Trail
                for tr in range(4):
                    trail_t = max(0.0, orb_t - tr * 0.08)
                    px = int(start_x + (tx - start_x) * trail_t)
                    py = int(start_y + (effective_ty - start_y) * trail_t)
                    alpha = _NS_syrindra._alpha(220 - tr * 40)
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                            (px, py), max(1, 4 - tr))
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["violet_mid"], alpha),
                                            (px, py), max(1, 3 - tr))
                # Head
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_darkest"],
                                        (bx, by), 5)
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["dark_mid"],
                                        (bx, by), 3)
                _NS_syrindra._aacircle(surface, _NS_syrindra.PALETTE["violet_light"],
                                        (bx, by), 1)
                pygame.draw.rect(surface, _NS_syrindra.PALETTE["dark_shine"],
                                 (bx, by, 1, 1))
        else:
            # Aftermath — big impact
            t = (progress - 0.8) / 0.2
            imp_r = int(35 + t * 30)
            alpha = _NS_syrindra._alpha(240 * (1 - t))
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_darkest"], alpha),
                                    (tx, ty), imp_r + 4, 4)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_dark"], alpha),
                                    (tx, ty), imp_r, 3)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_mid"], alpha),
                                    (tx, ty), max(1, imp_r - 8), 2)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["violet_light"], alpha),
                                    (tx, ty), max(1, imp_r - 15), 1)
            _NS_syrindra._aacircle(surface,
                                    (*_NS_syrindra.PALETTE["dark_shine"], alpha),
                                    (tx, ty), max(1, imp_r // 4))
            # Shatter fragments radiating
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * imp_r)
                ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                pygame.draw.line(surface,
                                 (*_NS_syrindra.PALETTE["dark_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_syrindra.PALETTE["dark_shine"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_syrindra.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))
            # Rising dark wisps
            for i in range(10):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 30)
                a = _NS_syrindra._alpha(220 * (1 - t) * (1 - rise_t))
                if a > 0:
                    _NS_syrindra._aacircle(surface,
                                            (*_NS_syrindra.PALETTE["dark_dark"], a),
                                            (rx, ry), 3)
                    pygame.draw.rect(surface,
                                     (*_NS_syrindra.PALETTE["dark_hot"], a),
                                     (rx, ry, 1, 1))



# ====================================================================
# RAVOKKAR (OUTLAW KING) - TRUE BOSS
# ====================================================================

class _NS_ravokkar:
    """Namespace ravokkar - Outlaw King true boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (weathered outlaw tan)
        "skin_darkest": (55, 30, 22),
        "skin_dark": (110, 70, 50),
        "skin_mid": (170, 115, 80),
        "skin_light": (215, 165, 120),
        "skin_shine": (245, 210, 170),
        # Hair/beard (dark brown-black)
        "hair_darkest": (12, 8, 8),
        "hair_dark": (30, 20, 18),
        "hair_mid": (65, 45, 35),
        "hair_light": (105, 75, 55),
        # Cape (deep blood red — Graves signature)
        "cape_darkest": (30, 8, 10),
        "cape_dark": (75, 15, 20),
        "cape_mid": (150, 35, 40),
        "cape_light": (215, 75, 75),
        "cape_shine": (245, 140, 140),
        "cape_edge": (255, 210, 200),
        # Coat/jacket (very dark leather)
        "coat_darkest": (5, 5, 8),
        "coat_dark": (18, 15, 20),
        "coat_mid": (40, 32, 35),
        "coat_light": (75, 60, 55),
        "coat_shine": (115, 95, 80),
        # Pants/legs (dark brown)
        "pants_darkest": (15, 10, 8),
        "pants_dark": (40, 25, 15),
        "pants_mid": (75, 50, 30),
        "pants_light": (115, 80, 50),
        # Leather (belt, boots, straps)
        "leather_darkest": (20, 12, 8),
        "leather_dark": (55, 35, 18),
        "leather_mid": (95, 65, 35),
        "leather_light": (150, 110, 65),
        # Gold ornaments (belt buckle, bullet casings)
        "gold_darkest": (60, 40, 5),
        "gold_dark": (115, 80, 15),
        "gold_mid": (200, 155, 40),
        "gold_light": (245, 215, 90),
        "gold_shine": (255, 245, 170),
        # Gun metal (dark iron)
        "gun_darkest": (5, 5, 8),
        "gun_dark": (18, 18, 25),
        "gun_mid": (50, 50, 60),
        "gun_light": (105, 105, 120),
        "gun_shine": (180, 180, 200),
        # Wood (gun stock — dark rich)
        "wood_dark": (35, 20, 10),
        "wood_mid": (75, 45, 22),
        "wood_light": (135, 90, 50),
        "wood_shine": (200, 155, 100),
        # FIRE (muzzle flash, aura — bright orange)
        "fire_darkest": (40, 8, 5),
        "fire_dark": (120, 30, 10),
        "fire_mid": (230, 100, 20),
        "fire_light": (255, 175, 55),
        "fire_hot": (255, 220, 120),
        "fire_shine": (255, 250, 200),
        # Smoke (dark grey)
        "smoke_darkest": (25, 25, 30),
        "smoke_dark": (60, 60, 65),
        "smoke_mid": (120, 118, 125),
        "smoke_light": (190, 188, 195),
        # Eye (glowing orange — intimidating)
        "eye_dark": (60, 20, 8),
        "eye_mid": (220, 90, 15),
        "eye_hot": (255, 200, 90),
        # Cigar
        "cigar_dark": (40, 22, 10),
        "cigar_mid": (85, 55, 25),
        "cigar_tip": (255, 150, 30),
        "cigar_hot": (255, 240, 120),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ravokkar._clamp(color)
        if _NS_ravokkar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_ravokkar._clamp(color)
        if _NS_ravokkar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_ravokkar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 280 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_ravokkar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_ravokkar._detect_moving(boss)
        _NS_ravokkar._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_rk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (BIG for TRUE BOSS)
        _NS_ravokkar._draw_ember_aura(surface, x, y, pulse)
        _NS_ravokkar._draw_ground_ring(surface, x, y + 54, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":  # Smoke Screen
            _NS_ravokkar._draw_smoke_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":  # Collateral Damage
            _NS_ravokkar._draw_collateral_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":  # Quickdraw
            _NS_ravokkar._draw_quickdraw_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_ravokkar._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_ravokkar._draw_walk(surface, boss, x, y)
        else:
            _NS_ravokkar._draw_idle(surface, boss, x, y)
        # Ambient cigar smoke (always present when idle)
        if not attacking and not moving:
            _NS_ravokkar._draw_cigar_smoke(surface, x, y, pulse, boss.direction)
        # Foreground skill FX
        if active_skill == "q":
            _NS_ravokkar._draw_end_of_line(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_ravokkar._draw_smoke_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ravokkar._draw_quickdraw_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ravokkar._draw_collateral_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_rk_previous_timer", 0))
        active = bool(getattr(boss, "_rk_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._rk_attack_active = True
            boss._rk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._rk_attack_frame = int(getattr(boss, "_rk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._rk_attack_active = False
            boss._rk_attack_frame = 0
            active = False
        boss._rk_previous_timer = timer
        boss._rk_attack_progress = (
            min(1.0, getattr(boss, "_rk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_rk_last_x"):
            boss._rk_last_x = boss.x
            boss._rk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._rk_last_x)
        dy = abs(boss.y - boss._rk_last_y)
        boss._rk_last_x = boss.x
        boss._rk_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.4) * 3)
        _NS_ravokkar._draw_shadow(surface, x, y + 55)
        _NS_ravokkar._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                 "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Floating movement
        phase = boss.pulse * 1.6
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.5) * 3)
        _NS_ravokkar._draw_shadow(surface, x + sway, y + 55, faded=True)
        _NS_ravokkar._draw_ember_trail(surface, x + sway, y + 44, phase,
                                        boss.direction)
        _NS_ravokkar._draw_body(surface, x + sway, y + float_bob - 3,
                                 boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_rk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Ranged shotgun blast: aim → fire (recoil) → recovery
        if progress < 0.35:
            # Aim — stabilize gun
            t = progress / 0.35
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 2)
        elif progress < 0.55:
            # FIRE — recoil (kick back)
            t = (progress - 0.35) / 0.20
            lunge = int((-2 - t * 6)) * boss.direction  # kick back
            lift = int(2 + t * 3)
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            lunge = int(-8 * (1 - t)) * boss.direction
            lift = int(5 - t * 5)
        _NS_ravokkar._draw_shadow(surface, x + lunge, y + 55)
        _NS_ravokkar._draw_body(surface, x + lunge, y - lift,
                                 boss.direction, boss.pulse, "attack", progress)
        _NS_ravokkar._draw_basic_shell(surface, boss, x + lunge, y - lift,
                                        progress)
    # ============================================================
    # BODY (Massive outlaw with big shotgun)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered: cape (behind) → legs → torso/coat → rear arm → head+hat → front arm+shotgun."""
        # Cape flowing back
        _NS_ravokkar._draw_cape(surface, cx, cy, facing, phase, action)
        # Legs (wide stance)
        _NS_ravokkar._draw_legs(surface, cx, cy + 14, facing, phase, action)
        # Torso + coat
        _NS_ravokkar._draw_torso_coat(surface, cx, cy, facing, phase, action)
        # Bullet straps across chest
        _NS_ravokkar._draw_bullet_straps(surface, cx, cy, facing, phase)
        # Belt with bullets
        _NS_ravokkar._draw_belt(surface, cx, cy + 12, facing, phase)
        # Rear arm (offhand — supports shotgun or holds ammo)
        _NS_ravokkar._draw_rear_arm(surface, cx, cy, facing, phase, action,
                                     attack_progress)
        # Head + face + hair
        _NS_ravokkar._draw_head(surface, cx + facing * 1, cy - 16, facing,
                                 phase, action)
        # Front arm + MASSIVE SHOTGUN (main feature)
        _NS_ravokkar._draw_shotgun_arm(surface, cx, cy, facing, phase, action,
                                        attack_progress)
    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Long flowing blood-red cape behind."""
        wave = math.sin(phase * 1.0) * 4
        wave2 = math.sin(phase * 0.8 + 1) * 3
        back = -facing
        base_top = (cx + back * 5, cy - 16)
        base_bot = (cx + back * 3, cy - 8)
        cape_points = [
            base_top,
            (cx + back * 12, cy - 20 + int(wave)),
            (cx + back * 20, cy - 14 + int(wave2)),
            (cx + back * 26, cy - 4 + int(wave)),
            (cx + back * 30, cy + 8 + int(wave2)),
            (cx + back * 28, cy + 20 + int(wave)),
            (cx + back * 22, cy + 28 + int(wave2)),
            (cx + back * 12, cy + 30),
            (cx + back * 4, cy + 22),
            (cx + back * 2, cy + 12),
            base_bot,
        ]
        # Shadow
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in cape_points])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["cape_darkest"],
                           cape_points)
        # Inner darker fold
        cx_c = sum(p[0] for p in cape_points) / len(cape_points)
        cy_c = sum(p[1] for p in cape_points) / len(cape_points)
        inner = [(int(p[0] * 0.85 + cx_c * 0.15),
                  int(p[1] * 0.85 + cy_c * 0.15)) for p in cape_points]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["cape_dark"], inner)
        # Mid layer
        mid = [(int(p[0] * 0.7 + cx_c * 0.3),
                int(p[1] * 0.7 + cy_c * 0.3)) for p in cape_points]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["cape_mid"], mid)
        # Fold highlights
        for i in range(len(cape_points) - 1):
            p1 = cape_points[i]
            p2 = cape_points[i + 1]
            if i % 2 == 0:
                mid_pt = (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))
                inner_pt = (int(mid_pt[0] * 0.75 + cx_c * 0.25),
                            int(mid_pt[1] * 0.75 + cy_c * 0.25))
                _NS_ravokkar._aaline(surface,
                                      _NS_ravokkar.PALETTE["cape_light"],
                                      mid_pt, inner_pt, 2)
        # Edge trim
        for i in range(len(cape_points) - 1):
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["cape_shine"],
                                  cape_points[i], cape_points[i + 1], 1)
        # Shoulder clasp (gold skull-like ornament)
        clasp_x = cx + back * 4
        clasp_y = cy - 14
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                                (clasp_x, clasp_y), 4)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gold_dark"],
                                (clasp_x, clasp_y), 3)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gold_mid"],
                                (clasp_x, clasp_y), 2)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                         (clasp_x - 1, clasp_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (clasp_x, clasp_y, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Wide muscular legs in dark pants + boots."""
        sway = math.sin(phase * 0.7) * 2
        for side_i, side in enumerate((-1, 1)):
            hip_x = cx + side * 5
            hip_y = cy - 4
            knee_x = hip_x + int(sway * side * 0.4)
            knee_y = hip_y + 10
            foot_x = knee_x - side * 1
            foot_y = knee_y + 10
            # Thigh (thick)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                                  (hip_x + 1, hip_y + 1),
                                  (knee_x + 1, knee_y + 1), 9)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_darkest"],
                                  (hip_x, hip_y), (knee_x, knee_y), 8)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_dark"],
                                  (hip_x, hip_y), (knee_x, knee_y), 6)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_mid"],
                                  (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_light"],
                                  (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Shin
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                                  (knee_x + 1, knee_y + 1),
                                  (foot_x + 1, foot_y + 1), 7)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_darkest"],
                                  (knee_x, knee_y), (foot_x, foot_y), 6)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_dark"],
                                  (knee_x, knee_y), (foot_x, foot_y), 4)
            _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["pants_mid"],
                                  (knee_x, knee_y), (foot_x, foot_y), 2)
            # Leather boot wrap
            for wrap_y in (knee_y + 4, knee_y + 8):
                pygame.draw.line(surface, _NS_ravokkar.PALETTE["leather_dark"],
                                 (knee_x - 3, wrap_y),
                                 (knee_x + 3, wrap_y), 1)
                pygame.draw.line(surface, _NS_ravokkar.PALETTE["leather_mid"],
                                 (knee_x - 3, wrap_y),
                                 (knee_x + 3, wrap_y), 1)
            # BIG BOOT (cowboy style)
            boot_pts = [
                (foot_x - 4, foot_y - 2),
                (foot_x + 5, foot_y - 2),
                (foot_x + 6, foot_y + 2),
                (foot_x + 4, foot_y + 4),
                (foot_x - 4, foot_y + 4),
                (foot_x - 5, foot_y + 2),
            ]
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 1) for p in boot_pts])
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                               boot_pts)
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_dark"], [
                (foot_x - 3, foot_y - 2),
                (foot_x + 4, foot_y - 2),
                (foot_x + 5, foot_y + 1),
                (foot_x - 3, foot_y + 1),
            ])
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_mid"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 4, foot_y),
                (foot_x - 2, foot_y),
            ])
            # Gold buckle on boot
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_dark"],
                             (foot_x, foot_y, 3, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                             (foot_x, foot_y, 2, 1))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                             (foot_x + 1, foot_y, 1, 1))
            # Spur on back of boot
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                             (foot_x - 5, foot_y + 1, 2, 1))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_light"],
                             (foot_x - 5, foot_y + 1, 1, 1))
    def _draw_torso_coat(surface, cx, cy, facing, phase, action):
        """Massive muscular torso in dark leather coat."""
        breath = math.sin(phase * 0.6) * 1
        # Coat shape (broad, imposing)
        coat = [
            (cx - 12, cy - 10),
            (cx + 12, cy - 10),
            (cx + 15, cy - 4),
            (cx + 14, cy + 6),
            (cx + 10, cy + 14),
            (cx - 10, cy + 14),
            (cx - 14, cy + 6),
            (cx - 15, cy - 4),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in coat])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_darkest"], coat)
        # Coat layers
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_dark"], [
            (cx - 11, cy - 9), (cx + 11, cy - 9),
            (cx + 14, cy - 4), (cx + 13, cy + 5),
            (cx + 9, cy + 13), (cx - 9, cy + 13),
            (cx - 13, cy + 5), (cx - 14, cy - 4),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_mid"], [
            (cx - 8, cy - 7), (cx + 8, cy - 7),
            (cx + 12, cy - 3), (cx + 11, cy + 4),
            (cx + 7, cy + 11), (cx - 7, cy + 11),
            (cx - 11, cy + 4), (cx - 12, cy - 3),
        ])
        # Coat highlight (chest lit)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_light"], [
            (cx - 3 * facing, cy - 5),
            (cx + 4 * facing, cy - 4),
            (cx + 5 * facing, cy),
            (cx + 2 * facing, cy + 4),
            (cx - 2 * facing, cy + 2),
        ])
        # Coat lapel/collar (V-shape opening)
        lapel_pts = [
            (cx - 6, cy - 10),
            (cx, cy - 4),
            (cx + 6, cy - 10),
            (cx + 5, cy - 8),
            (cx, cy - 2),
            (cx - 5, cy - 8),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_darkest"],
                           lapel_pts)
        # Skin visible in V-neck
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["skin_dark"],
                         (cx - 3, cy - 6), (cx, cy - 3), 2)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["skin_dark"],
                         (cx + 3, cy - 6), (cx, cy - 3), 2)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["skin_mid"],
                         (cx - 2, cy - 5), (cx, cy - 4), 1)
        # Coat button line down center
        for btn_y in (cy - 2, cy + 2, cy + 6, cy + 10):
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                             (cx, btn_y, 2, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_dark"],
                             (cx, btn_y, 2, 1))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                             (cx, btn_y, 1, 1))
        # SHOULDER PAULDRONS (heavy leather with metal)
        for side in (-1, 1):
            paul_x = cx + side * 12
            paul_y = cy - 10
            paul_pts = [
                (paul_x - 3, paul_y - 1),
                (paul_x + 3, paul_y - 1),
                (paul_x + 5, paul_y + 3),
                (paul_x + 3, paul_y + 6),
                (paul_x - 3, paul_y + 6),
                (paul_x - 5, paul_y + 3),
            ]
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 1) for p in paul_pts])
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_darkest"],
                               paul_pts)
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_dark"], [
                (paul_x - 2, paul_y), (paul_x + 2, paul_y),
                (paul_x + 4, paul_y + 3), (paul_x + 2, paul_y + 5),
                (paul_x - 2, paul_y + 5), (paul_x - 4, paul_y + 3),
            ])
            _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["coat_mid"], [
                (paul_x - 1, paul_y + 1), (paul_x + 1, paul_y + 1),
                (paul_x + 3, paul_y + 3), (paul_x - 3, paul_y + 3),
            ])
            # Metal cap on top
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                             (paul_x - 3, paul_y - 1, 6, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                             (paul_x - 2, paul_y - 1, 4, 1))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_shine"],
                             (paul_x, paul_y - 1, 1, 1))
            # Rivets
            for rvt_x in (-2, 2):
                pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                                 (paul_x + rvt_x, paul_y + 3, 1, 1))
    def _draw_bullet_straps(surface, cx, cy, facing, phase):
        """Two bullet bandoliers crossing chest."""
        # Strap 1 (diagonal top-left to bottom-right)
        strap1_pts = [
            (cx - 12, cy - 5),
            (cx + 12, cy + 4),
            (cx + 12, cy + 6),
            (cx - 12, cy - 3),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                           strap1_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_dark"], [
            (cx - 11, cy - 4), (cx + 11, cy + 5),
            (cx + 11, cy + 5), (cx - 11, cy - 3),
        ])
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["leather_mid"],
                         (cx - 11, cy - 4), (cx + 11, cy + 5), 1)
        # Bullets on strap 1 (gold casings)
        for t in (0.15, 0.35, 0.55, 0.75):
            bx = int(cx - 12 + 24 * t)
            by = int(cy - 5 + 9 * t)
            # Bullet body
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                             (bx - 1, by, 3, 3))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_dark"],
                             (bx - 1, by, 3, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                             (bx, by, 2, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                             (bx, by, 1, 1))
        # Strap 2 (diagonal top-right to bottom-left)
        strap2_pts = [
            (cx + 12, cy - 5),
            (cx - 12, cy + 4),
            (cx - 12, cy + 6),
            (cx + 12, cy - 3),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                           strap2_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["leather_dark"], [
            (cx + 11, cy - 4), (cx - 11, cy + 5),
            (cx - 11, cy + 5), (cx + 11, cy - 3),
        ])
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["leather_mid"],
                         (cx + 11, cy - 4), (cx - 11, cy + 5), 1)
        # Bullets on strap 2
        for t in (0.15, 0.35, 0.55, 0.75):
            bx = int(cx + 12 - 24 * t)
            by = int(cy - 5 + 9 * t)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                             (bx - 1, by, 3, 3))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_dark"],
                             (bx - 1, by, 3, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                             (bx, by, 2, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                             (bx, by, 1, 1))
        # Central junction (small badge/skull)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                                (cx, cy + 1), 3)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gold_dark"],
                                (cx, cy + 1), 2)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_mid"],
                                (cx, cy + 1), 1)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_hot"],
                         (cx, cy + 1, 1, 1))
    def _draw_belt(surface, cx, cy, facing, phase):
        """Wide leather belt with bullets and big buckle."""
        # Belt band
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (cx - 14, cy + 1, 28, 5))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                         (cx - 14, cy, 28, 4))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["leather_dark"],
                         (cx - 14, cy, 28, 3))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["leather_mid"],
                         (cx - 14, cy, 28, 1))
        # Bullets around belt
        for bt_x in (-11, -8, -5, 5, 8, 11):
            bx = cx + bt_x
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                             (bx - 1, cy + 4, 3, 3))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_dark"],
                             (bx - 1, cy + 4, 3, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                             (bx, cy + 4, 2, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                             (bx, cy + 4, 1, 1))
        # BIG central buckle (ornate skull-like)
        buckle_pts = [
            (cx - 4, cy - 2),
            (cx + 4, cy - 2),
            (cx + 6, cy + 1),
            (cx + 5, cy + 4),
            (cx - 5, cy + 4),
            (cx - 6, cy + 1),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in buckle_pts])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["gold_darkest"],
                           buckle_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["gold_dark"], [
            (cx - 3, cy - 1), (cx + 3, cy - 1),
            (cx + 5, cy + 1), (cx + 4, cy + 3),
            (cx - 4, cy + 3), (cx - 5, cy + 1),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["gold_mid"], [
            (cx - 2, cy), (cx + 2, cy),
            (cx + 3, cy + 1), (cx + 2, cy + 2),
            (cx - 2, cy + 2), (cx - 3, cy + 1),
        ])
        # Central gem (fire)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            a = _NS_ravokkar._alpha(200 * (3 - r) / 3 * pulse)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_mid"], a),
                                    (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_hot"],
                         (cx, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                         (cx - 1, cy, 1, 1))
    def _draw_rear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm — supports shotgun from bottom during aim/fire."""
        back = -facing
        shoulder = (cx + back * 8, cy - 8)
        # Arm position — reaches forward to support gun
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                elbow_off_x = int(back * 2 + facing * 2)
                elbow_off_y = int(3 - t)
                hand_off_x = facing * (2 + int(t * 3))
                hand_off_y = int(0)
            elif attack_progress < 0.55:
                # Kick back during fire
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = int(back * (2 + int(t * 2)))
                elbow_off_y = int(2 + int(t * 2))
                hand_off_x = facing * int(4 - t * 3)
                hand_off_y = int(t * 2)
            else:
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = int(back * (4 - int(t * 2)))
                elbow_off_y = int(4 - int(t * 2))
                hand_off_x = facing * int(1 + t * 3)
                hand_off_y = int(2 - t * 2)
        else:
            gesture = math.sin(phase * 0.6) * 1
            elbow_off_x = int(back * 2)
            elbow_off_y = int(2 + gesture)
            hand_off_x = facing * 3
            hand_off_y = int(gesture)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # Upper arm (coat sleeve)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["coat_darkest"],
                              shoulder, elbow, 5)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["coat_dark"],
                              shoulder, elbow, 4)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["coat_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 2)
        # Forearm (leather gauntlet)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 5)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                              elbow, hand, 4)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["leather_dark"],
                              elbow, hand, 3)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["leather_mid"],
                              (elbow[0], elbow[1] - 1),
                              (hand[0], hand[1] - 1), 1)
        # Gauntlet studs
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                         (int((elbow[0] + hand[0]) / 2) - 1,
                          int((elbow[1] + hand[1]) / 2) - 1, 3, 2))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_shine"],
                         (int((elbow[0] + hand[0]) / 2),
                          int((elbow[1] + hand[1]) / 2) - 1, 1, 1))
        # Hand gripping shotgun
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                                (hand[0] + 1, hand[1] + 1), 3)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["skin_darkest"],
                                hand, 3)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["skin_dark"],
                                hand, 2)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["skin_mid"],
                                hand, 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Big rugged outlaw face with slicked-back hair, thick beard, cigar."""
        # Head shape (broader jaw)
        head = [
            (cx - 5, cy - 2),
            (cx - 6, cy - 6),
            (cx - 4, cy - 9),
            (cx, cy - 10),
            (cx + 4, cy - 9),
            (cx + 6, cy - 6),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 5, cy + 3),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["skin_darkest"], head)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["skin_dark"], [
            (cx - 4, cy - 2), (cx - 5, cy - 5),
            (cx - 3, cy - 8), (cx, cy - 9),
            (cx + 3, cy - 8), (cx + 5, cy - 5),
            (cx + 5, cy - 1), (cx + 4, cy + 2),
            (cx + 2, cy + 5), (cx - 2, cy + 5), (cx - 4, cy + 2),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["skin_mid"], [
            (cx - 3, cy - 3), (cx - 3, cy - 6),
            (cx, cy - 7), (cx + 3, cy - 6),
            (cx + 4, cy - 3),
        ])
        # Highlight
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["skin_light"], [
            (cx + facing, cy - 5),
            (cx + 3 * facing, cy - 4),
            (cx + 3 * facing, cy - 2),
            (cx + facing, cy - 2),
        ])
        # SLICKED BACK HAIR (dark, combed back)
        back = -facing
        hair_pts = [
            (cx - 5, cy - 5),
            (cx - 6, cy - 8),
            (cx - 4, cy - 10),
            (cx, cy - 11),
            (cx + 4, cy - 10),
            (cx + 6, cy - 8),
            (cx + 7, cy - 5),
            (cx + 5 * (-back) - back * 2, cy - 6),  # combed toward back
            (cx + 3, cy - 7),
            (cx, cy - 8),
            (cx - 3, cy - 7),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                           hair_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["hair_dark"], [
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 3, cy - 8),
            (cx, cy - 9),
            (cx - 3, cy - 8),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["hair_mid"], [
            (cx - 2, cy - 8),
            (cx, cy - 9),
            (cx + 2, cy - 8),
        ])
        # Hair combed to back (few strands trailing)
        for i in range(3):
            strand_x = cx + back * (5 + i)
            strand_y = cy - 7 + i * 2
            end_x = strand_x + back * 2
            end_y = strand_y + 3
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                             (strand_x, strand_y), (end_x, end_y), 2)
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_dark"],
                             (strand_x, strand_y), (end_x, end_y), 1)
        # THICK BEARD (covers jaw)
        beard_pts = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 5, cy + 5),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 5, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy + 1),
            (cx - 3, cy + 1),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                           beard_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["hair_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx - 4, cy + 4),
            (cx - 1, cy + 6),
            (cx + 1, cy + 6),
            (cx + 4, cy + 4),
            (cx + 5, cy + 2),
            (cx + 4, cy),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["hair_mid"], [
            (cx - 3, cy + 2),
            (cx, cy + 5),
            (cx + 3, cy + 2),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        # Mustache (part of beard)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                         (cx - 4, cy - 1), (cx - 1, cy), 2)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                         (cx + 4, cy - 1), (cx + 1, cy), 2)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_dark"],
                         (cx - 4, cy - 1), (cx - 1, cy), 1)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_dark"],
                         (cx + 4, cy - 1), (cx + 1, cy), 1)
        # EYES — fierce orange glow
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Heavy brow (angry)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                         (cx - 4, cy - 6), (cx - 1, cy - 6), 2)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_darkest"],
                         (cx + 1, cy - 6), (cx + 4, cy - 6), 2)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_dark"],
                         (cx - 4, cy - 7), (cx - 1, cy - 7), 1)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["hair_dark"],
                         (cx + 1, cy - 7), (cx + 4, cy - 7), 1)
        # Eye sockets
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 2, 2))
        # Whites
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["skin_shine"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["skin_shine"],
                         (cx + 1, cy - 5, 2, 2))
        # Fierce orange pupils
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["eye_dark"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["eye_dark"],
                         (cx + 2, cy - 5, 1, 2))
        # Eye glow halo
        for r in range(4, 0, -1):
            a = _NS_ravokkar._alpha(100 * (4 - r) / 4 * eye_pulse)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["eye_mid"], a),
                                    (cx - 2, cy - 4), r)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["eye_mid"], a),
                                    (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["eye_hot"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["eye_hot"],
                         (cx + 2, cy - 4, 1, 1))
        # Big nose
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["skin_darkest"],
                         (cx, cy - 2, 1, 3))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["skin_dark"],
                         (cx - 1, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["skin_light"],
                         (cx + facing, cy - 2, 1, 1))
        # SCAR across face (outlaw look)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["skin_darkest"],
                         (cx + 3, cy - 4), (cx + 4, cy + 1), 1)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["skin_light"],
                         (cx + 4, cy - 2, 1, 1))
        # CIGAR in mouth (signature)
        cigar_x = cx + facing * 3
        cigar_y = cy + 3
        # Cigar body
        for i in range(4):
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["cigar_dark"],
                             (cigar_x + facing * i, cigar_y, 1, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["cigar_mid"],
                             (cigar_x + facing * i, cigar_y, 1, 1))
        # Cigar TIP (glowing hot)
        tip_x = cigar_x + facing * 4
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["cigar_dark"],
                         (tip_x, cigar_y, 1, 2))
        # Glowing tip
        cigar_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for r in range(3, 0, -1):
            a = _NS_ravokkar._alpha(200 * (3 - r) / 3 * cigar_pulse)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["cigar_tip"], a),
                                    (tip_x, cigar_y + 1), r)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["cigar_tip"],
                         (tip_x, cigar_y, 1, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["cigar_hot"],
                         (tip_x, cigar_y, 1, 1))
    def _draw_shotgun_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding the MASSIVE DOUBLE-BARREL SHOTGUN."""
        shoulder = (cx + facing * 8, cy - 8)
        # Recoil animation
        if action == "attack":
            if attack_progress < 0.35:
                # Aim steady
                t = attack_progress / 0.35
                elbow_off_x = facing * (6 + int(t * 1))
                elbow_off_y = int(-1)
                hand_off_x = facing * (14 + int(t * 2))
                hand_off_y = int(-3)
            elif attack_progress < 0.55:
                # RECOIL — arm kicks back
                t = (attack_progress - 0.35) / 0.2
                elbow_off_x = facing * int(7 - t * 5)
                elbow_off_y = int(-1 + t * 3)
                hand_off_x = facing * int(16 - t * 8)
                hand_off_y = int(-3 + t * 4)
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = facing * int(2 + t * 5)
                elbow_off_y = int(2 - t * 2)
                hand_off_x = facing * int(8 + t * 8)
                hand_off_y = int(1 - t * 3)
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_off_x = facing * 6
            elbow_off_y = int(-1 + sway)
            hand_off_x = facing * 14
            hand_off_y = int(-3 + sway)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # Upper arm (coat sleeve)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                              (shoulder[0] + 1, shoulder[1] + 1),
                              (elbow[0] + 1, elbow[1] + 1), 7)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["coat_darkest"],
                              shoulder, elbow, 6)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["coat_dark"],
                              shoulder, elbow, 5)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["coat_mid"],
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 2)
        # Elbow armor
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                                (elbow[0] + 1, elbow[1] + 1), 3)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gun_dark"],
                                elbow, 3)
        _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gun_mid"],
                                elbow, 2)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_shine"],
                         (elbow[0], elbow[1] - 1, 1, 1))
        # Forearm (leather + metal gauntlet)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                              (elbow[0] + 1, elbow[1] + 1),
                              (hand[0] + 1, hand[1] + 1), 6)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                              elbow, hand, 5)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["leather_dark"],
                              elbow, hand, 4)
        _NS_ravokkar._aaline(surface, _NS_ravokkar.PALETTE["leather_mid"],
                              (elbow[0], elbow[1] - 1),
                              (hand[0], hand[1] - 1), 1)
        # Gauntlet metal plates
        for j_t in (0.3, 0.65):
            jx = int(elbow[0] + (hand[0] - elbow[0]) * j_t)
            jy = int(elbow[1] + (hand[1] - elbow[1]) * j_t)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                             (jx - 2, jy - 2, 4, 4))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                             (jx - 1, jy - 1, 3, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_shine"],
                             (jx, jy - 1, 1, 1))
        # Hand grip
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (hand[0] - 2, hand[1] - 2, 6, 5))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["leather_darkest"],
                         (hand[0] - 2, hand[1] - 2, 6, 5))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["leather_dark"],
                         (hand[0] - 2, hand[1] - 2, 6, 4))
        # MASSIVE DOUBLE-BARREL SHOTGUN
        _NS_ravokkar._draw_shotgun(surface, hand[0], hand[1], facing, phase,
                                    action, attack_progress)
    def _draw_shotgun(surface, hx, hy, facing, phase, action, attack_progress):
        """MASSIVE DOUBLE-BARREL SHOTGUN — THE main feature."""
        # Shotgun extends horizontally forward
        # Recoil offset during fire
        recoil_off = 0
        if action == "attack" and 0.35 <= attack_progress < 0.5:
            recoil_off = int((attack_progress - 0.35) / 0.15 * 3)
        elif action == "attack" and 0.5 <= attack_progress < 0.55:
            recoil_off = int(3 - (attack_progress - 0.5) / 0.05 * 3)
        # Stock (rear wood)
        stock_x = hx - facing * (4 + recoil_off)
        stock_y = hy
        stock_pts = [
            (stock_x - facing * 6, stock_y - 3),
            (stock_x, stock_y - 3),
            (stock_x, stock_y + 3),
            (stock_x - facing * 6, stock_y + 4),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in stock_pts])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["wood_dark"],
                           stock_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["wood_mid"], [
            (stock_x - facing * 5, stock_y - 2),
            (stock_x - facing, stock_y - 2),
            (stock_x - facing, stock_y + 2),
            (stock_x - facing * 5, stock_y + 3),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["wood_light"], [
            (stock_x - facing * 4, stock_y - 1),
            (stock_x - facing * 2, stock_y - 1),
            (stock_x - facing * 2, stock_y),
            (stock_x - facing * 4, stock_y),
        ])
        # Wood grain
        for gy_off in (-1, 1):
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["wood_shine"],
                             (stock_x - facing * 5, stock_y + gy_off),
                             (stock_x - facing, stock_y + gy_off), 1)
        # Receiver (metal middle section)
        recv_x = stock_x
        recv_pts = [
            (recv_x, stock_y - 4),
            (recv_x + facing * 8, stock_y - 4),
            (recv_x + facing * 8, stock_y + 4),
            (recv_x, stock_y + 4),
        ]
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in recv_pts])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                           recv_pts)
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["gun_dark"], [
            (recv_x + facing, stock_y - 3),
            (recv_x + facing * 7, stock_y - 3),
            (recv_x + facing * 7, stock_y + 3),
            (recv_x + facing, stock_y + 3),
        ])
        _NS_ravokkar._poly(surface, _NS_ravokkar.PALETTE["gun_mid"], [
            (recv_x + facing * 2, stock_y - 2),
            (recv_x + facing * 6, stock_y - 2),
            (recv_x + facing * 6, stock_y + 2),
            (recv_x + facing * 2, stock_y + 2),
        ])
        # Highlight top
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_light"],
                         (recv_x + facing, stock_y - 3),
                         (recv_x + facing * 7, stock_y - 3), 1)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_shine"],
                         (recv_x + facing * 3, stock_y - 3),
                         (recv_x + facing * 5, stock_y - 3), 1)
        # Gold ornament on receiver (fancy)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_dark"],
                         (recv_x + facing * 3, stock_y, 3, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_mid"],
                         (recv_x + facing * 3, stock_y, 2, 1))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gold_shine"],
                         (recv_x + facing * 4, stock_y, 1, 1))
        # Trigger guard
        trig_x = recv_x + facing * 4
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                         (trig_x, stock_y + 4, 3, 3))
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                         (trig_x, stock_y + 4),
                         (trig_x, stock_y + 7), 1)
        pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                         (trig_x + facing * 2, stock_y + 4),
                         (trig_x + facing * 2, stock_y + 7), 1)
        # Trigger
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                         (trig_x + facing, stock_y + 5, 1, 2))
        # ========== DOUBLE BARRELS (Signature — 2 stacked barrels) ==========
        barrel_start_x = recv_x + facing * 8
        barrel_len = 24
        # Top barrel
        top_barrel_y = stock_y - 3
        _NS_ravokkar._draw_barrel(surface, barrel_start_x, top_barrel_y,
                                   barrel_len, facing)
        # Bottom barrel
        bot_barrel_y = stock_y + 2
        _NS_ravokkar._draw_barrel(surface, barrel_start_x, bot_barrel_y,
                                   barrel_len, facing)
        # Barrel connecting bracket
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                         (barrel_start_x + facing * 6, top_barrel_y - 1,
                          3, bot_barrel_y - top_barrel_y + 5))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                         (barrel_start_x + facing * 6, top_barrel_y,
                          2, bot_barrel_y - top_barrel_y + 3))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                         (barrel_start_x + facing * 6, top_barrel_y + 1,
                          1, bot_barrel_y - top_barrel_y + 1))
        # End bracket / muzzle brace
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                         (barrel_start_x + facing * (barrel_len - 3),
                          top_barrel_y - 1,
                          3, bot_barrel_y - top_barrel_y + 5))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                         (barrel_start_x + facing * (barrel_len - 3),
                          top_barrel_y,
                          2, bot_barrel_y - top_barrel_y + 3))
        # MUZZLE FIRE FLASH (during fire)
        if action == "attack" and 0.35 <= attack_progress < 0.5:
            flash_t = (attack_progress - 0.35) / 0.15
            flash_intensity = math.sin(flash_t * math.pi)
            # Fire from BOTH barrels
            for barrel_y in (top_barrel_y, bot_barrel_y + 2):
                muzzle_x = barrel_start_x + facing * barrel_len
                # Big flame
                for r in range(8, 0, -1):
                    a = _NS_ravokkar._alpha(240 * (8 - r) / 8 * flash_intensity)
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["fire_darkest"], a),
                                            (muzzle_x, barrel_y), r + 2)
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["fire_dark"], a),
                                            (muzzle_x, barrel_y), r + 1)
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["fire_mid"], a),
                                            (muzzle_x, barrel_y), r)
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["fire_light"], a),
                                            (muzzle_x, barrel_y), max(1, r - 2))
                _NS_ravokkar._aacircle(surface,
                                        _NS_ravokkar.PALETTE["fire_hot"],
                                        (muzzle_x, barrel_y), 3)
                _NS_ravokkar._aacircle(surface,
                                        _NS_ravokkar.PALETTE["fire_shine"],
                                        (muzzle_x, barrel_y), 1)
                # Flame tongues
                for i in range(6):
                    angle = -math.pi / 6 + i * math.pi / 15
                    flame_len = int(15 * flash_intensity)
                    fx = muzzle_x + int(math.cos(angle) * flame_len) * facing
                    fy = barrel_y + int(math.sin(angle) * flame_len)
                    a = _NS_ravokkar._alpha(200 * flash_intensity)
                    pygame.draw.line(surface,
                                     (*_NS_ravokkar.PALETTE["fire_mid"], a),
                                     (muzzle_x, barrel_y), (fx, fy), 3)
                    pygame.draw.line(surface,
                                     (*_NS_ravokkar.PALETTE["fire_hot"], a),
                                     (muzzle_x, barrel_y), (fx, fy), 1)
                # Sparks flying out
                for spark_i in range(8):
                    sp_angle = flash_t * 10 + spark_i * math.pi / 4
                    sp_dist = 5 + int(math.sin(sp_angle) * 5)
                    sp_x = muzzle_x + int(math.cos(sp_angle) * sp_dist) * facing
                    sp_y = barrel_y + int(math.sin(sp_angle) * sp_dist)
                    pygame.draw.rect(surface,
                                     _NS_ravokkar.PALETTE["fire_hot"],
                                     (sp_x, sp_y, 1, 1))
                    pygame.draw.rect(surface,
                                     _NS_ravokkar.PALETTE["fire_shine"],
                                     (sp_x, sp_y, 1, 1))
            # Smoke puff behind muzzle
            for smoke_i in range(6):
                sm_t = (phase * 2 + smoke_i * 0.2) % 1.0
                sm_x = barrel_start_x + facing * (barrel_len + int(sm_t * 15))
                sm_y = (top_barrel_y + bot_barrel_y) // 2 + int(math.sin(smoke_i) * 3)
                sm_alpha = _NS_ravokkar._alpha(180 * (1 - sm_t) * flash_intensity)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_dark"], sm_alpha),
                                        (sm_x, sm_y), 3)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_mid"], sm_alpha),
                                        (sm_x, sm_y), 2)
    def _draw_barrel(surface, bx, by, length, facing):
        """Single shotgun barrel."""
        # Barrel body
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (bx + 1, by + 1, length, 3))
        if facing > 0:
            barrel_rect = (bx, by, length, 3)
        else:
            barrel_rect = (bx - length, by, length, 3)
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                         barrel_rect)
        # Inner darker
        if facing > 0:
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                             (bx, by, length, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                             (bx, by, length, 1))
            # Highlight streak
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_light"],
                             (bx + 2, by), (bx + length - 3, by), 1)
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_shine"],
                             (bx + 5, by), (bx + length - 8, by), 1)
        else:
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_dark"],
                             (bx - length, by, length, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_mid"],
                             (bx - length, by, length, 1))
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_light"],
                             (bx - length + 3, by), (bx - 2, by), 1)
            pygame.draw.line(surface, _NS_ravokkar.PALETTE["gun_shine"],
                             (bx - length + 8, by), (bx - 5, by), 1)
        # Muzzle end (opening)
        muzzle_x = bx + facing * length
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (muzzle_x - facing, by - 1, 2, 5))
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                         (muzzle_x - facing, by, 2, 3))
        # Dark barrel hole
        pygame.draw.rect(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                         (muzzle_x, by + 1, 1, 1))
    # ============================================================
    # AMBIENT CIGAR SMOKE
    # ============================================================
    def _draw_cigar_smoke(surface, x, y, phase, facing):
        """Wispy smoke rising from cigar (when idle)."""
        base_x = x + facing * 4
        base_y = y - 13
        for i in range(5):
            t = (phase * 0.5 + i * 0.2) % 1.0
            sx = base_x + int(math.sin(phase + i) * 4) + facing * i
            sy = base_y - int(t * 20)
            alpha = _NS_ravokkar._alpha(120 * (1 - t))
            if alpha > 0:
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_dark"], alpha),
                                        (sx, sy), 3)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_mid"], alpha),
                                        (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["smoke_light"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # BASIC ATTACK — shotgun shell projectile
    # ============================================================
    def _draw_basic_shell(surface, boss, x, y, progress):
        """Shotgun shell burst — spread shot with multiple pellets."""
        if progress < 0.45:
            return
        facing = boss.direction
        tx, ty = _NS_ravokkar._target_position(boss, x, y)
        start_x = x + facing * 40
        start_y = y - 6
        t = (progress - 0.45) / 0.55
        t = min(1.0, t)
        # Multiple pellets in spread pattern (shotgun)
        num_pellets = 5
        for pellet_i in range(num_pellets):
            spread_off_y = int((pellet_i - num_pellets / 2 + 0.5) * 6)
            spread_off_x = int(abs(pellet_i - num_pellets / 2 + 0.5) * 3) * -facing
            effective_ty = ty + spread_off_y
            bx = int(start_x + (tx - start_x) * t + spread_off_x * t)
            by = int(start_y + (effective_ty - start_y) * t)
            # Trail for each pellet
            for tr in range(4):
                trail_t = max(0.0, t - tr * 0.05)
                px = int(start_x + (tx - start_x) * trail_t + spread_off_x * trail_t)
                py = int(start_y + (effective_ty - start_y) * trail_t)
                alpha = _NS_ravokkar._alpha(230 - tr * 45)
                size = max(1, 3 - tr)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                        (px, py), size + 1)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                        (px, py), size)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                        (px, py), max(1, size - 1))
            # Head
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_dark"],
                                    (bx, by), 3)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_mid"],
                                    (bx, by), 2)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_hot"],
                                    (bx, by), 1)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["white"],
                             (bx, by, 1, 1))
    # ============================================================
    # AMBIENT / GROUND (BIG scale — TRUE BOSS)
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(14, 0, -1):
            alpha = int(max(0, (14 - radius) * 15) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 3, 2, int(170 * mult)),
                            (5, 7, 140, 16))
        pygame.draw.ellipse(shadow, (35, 15, 5, int(120 * mult)),
                            (12, 9, 126, 12))
        surface.blit(shadow, (x - 75, y - 15))
    def _draw_ember_aura(surface, x, y, phase):
        """Massive fire/ember aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        # Outer aura (very large)
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(115, 5, -6):
            alpha = _NS_ravokkar._alpha((115 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_ravokkar._aacircle(aura,
                                        (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                        (130, 110), radius)
        for radius in range(75, 5, -4):
            alpha = _NS_ravokkar._alpha((75 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_ravokkar._aacircle(aura,
                                        (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                        (130, 110), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_ravokkar._alpha((45 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_ravokkar._aacircle(aura,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                        (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Floating embers
        for i in range(18):
            angle = phase * 0.3 + i * math.pi / 9
            radius = 48 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Big fire ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_ravokkar.PALETTE["fire_darkest"], 210),
                            (5, 22, 190, 30), 4)
        pygame.draw.ellipse(ring, (*_NS_ravokkar.PALETTE["fire_dark"], 220),
                            (14, 24, 172, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_ravokkar.PALETTE["fire_mid"], 230),
                            (25, 26, 150, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_ravokkar.PALETTE["gold_mid"], 180),
                            (42, 28, 116, 18), 1)
        # Bullet-like runes
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 54)
            y1 = 34 + int(math.sin(angle) * 10)
            x2 = 100 + int(math.cos(angle) * 82)
            y2 = 34 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_ravokkar.PALETTE["fire_hot"], 230),
                             (x1, y1), (x2, y2), 1)
            # Bullet at tip
            pygame.draw.rect(ring, (*_NS_ravokkar.PALETTE["gold_shine"], 240),
                             (x2, y2, 2, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_ravokkar.PALETTE["fire_shine"],
                                       _NS_ravokkar._alpha(160 * pulse)),
                                (15, 14, 170, 44), 1)
        surface.blit(ring, (x - 100, y - 30))
    def _draw_ember_trail(surface, cx, cy, phase, facing):
        """Ember trail during floating movement."""
        for i in range(10):
            t = (phase * 0.5 + i * 0.13) % 1.0
            wx = cx + int(math.sin(phase + i) * 10) - facing * i * 3
            wy = cy + int(t * 12)
            alpha = _NS_ravokkar._alpha(200 * (1 - t))
            if alpha > 0:
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                        (wx, wy), 3)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                        (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # SKILL Q - END OF THE LINE (piercing long-range shell)
    # ============================================================
    def _draw_end_of_line(surface, boss, x, y, timer, phase):
        """Big piercing shell that flies through and pushes back."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_ravokkar._target_position(boss, x, y)
        if progress < 0.2:
            # Charge — glow builds at muzzle
            t = progress / 0.2
            mx = x + facing * 42
            my = y - 6
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_ravokkar._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                        (mx, my), r)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_dark"],
                                    (mx, my), cr - 2)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_mid"],
                                    (mx, my), max(1, cr - 4))
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_hot"],
                                    (mx, my), max(1, cr - 6))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 44
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # LONG piercing shell — elongated bullet shape
            # Long trail (many afterimages)
            for i in range(14):
                trail_t = max(0.0, t - i * 0.03)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_ravokkar._alpha(240 - i * 18)
                size = max(1, 8 - i // 2)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                        (px, py), size + 1)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                        (px, py), size)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                        (px, py), max(1, size - 3))
            # Bright bullet head (elongated)
            dx = tx - start_x
            dy = ty - start_y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                ux = dx / length
                uy = dy / length
                for i in range(8):
                    ax = bx + int(ux * i * 1.5)
                    ay = by + int(uy * i * 1.5)
                    a = _NS_ravokkar._alpha(240 * (8 - i) / 8)
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["fire_hot"], a),
                                            (ax, ay), max(1, 4 - i // 2))
            # Bright core
            for r in range(12, 3, -2):
                a = _NS_ravokkar._alpha(120 * (12 - r) / 12)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_light"], a),
                                        (bx, by), r)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_shine"],
                                    (bx, by), 3)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["white"],
                             (bx, by, 1, 1))
            # BIG impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 25)
                alpha = _NS_ravokkar._alpha(240 * (1 - st))
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                        (tx, ty), radius + 3, 3)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                        (tx, ty), radius, 3)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                        (tx, ty), max(1, radius - 6), 2)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                        (tx, ty), max(1, radius // 3))
                # Radial fire lines
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_ravokkar.PALETTE["fire_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_ravokkar.PALETTE["fire_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - SMOKE SCREEN (smoke bomb area)
    # ============================================================
    def _draw_smoke_ground(surface, boss, x, y, timer, phase):
        """Smoke area on ground."""
        tx, ty = _NS_ravokkar._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_ravokkar.PALETTE["smoke_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_ravokkar.PALETTE["smoke_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_smoke_foreground(surface, boss, x, y, timer, phase):
        """Rising smoke clouds — big billowy smoke."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_ravokkar._target_position(boss, x, y)
        if progress < 0.15:
            # Bomb flying to target
            t = progress / 0.15
            start_x = x + facing * 44
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t - int(math.sin(t * math.pi) * 20))
            # Bomb (dark ball with fuse)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                                    (bx + 1, by + 1), 4)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                                    (bx, by), 4)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gun_dark"],
                                    (bx, by), 3)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gun_mid"],
                                    (bx, by), 2)
            # Fuse spark
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_hot"],
                             (bx, by - 4, 1, 1))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_shine"],
                             (bx, by - 4, 1, 1))
        else:
            # Smoke billowing out
            t = (progress - 0.15) / 0.85
            smoke_size = int(60 * min(1.0, t * 2))
            # Multiple smoke clouds billowing
            num_clouds = 8
            for i in range(num_clouds):
                cloud_angle = i * math.pi / 4 + phase * 0.2
                cloud_dist = int(smoke_size * (0.4 + 0.4 * math.sin(phase + i)))
                cloud_x = tx + int(math.cos(cloud_angle) * cloud_dist)
                cloud_y = ty + int(math.sin(cloud_angle) * cloud_dist * 0.5)
                # Rising motion
                rise_off = int(math.sin(phase * 1.5 + i) * 5)
                cloud_y -= rise_off + int(t * 10)
                cloud_size = 8 + int(math.sin(phase * 2 + i) * 3)
                cloud_alpha = _NS_ravokkar._alpha(220 * (1 - t * 0.3))
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_darkest"], cloud_alpha),
                                        (cloud_x, cloud_y), cloud_size + 1)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_dark"], cloud_alpha),
                                        (cloud_x, cloud_y), cloud_size)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_mid"], cloud_alpha),
                                        (cloud_x - 1, cloud_y - 1),
                                        max(2, cloud_size - 3))
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["smoke_light"], cloud_alpha),
                                        (cloud_x - 2, cloud_y - 2),
                                        max(1, cloud_size - 6))
    # ============================================================
    # SKILL E - QUICKDRAW (dash + auto-attack empowered)
    # ============================================================
    def _draw_quickdraw_ground(surface, boss, x, y, timer, phase):
        """Dash path streak."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        path_len = int(150 * min(1.0, progress * 2))
        for i in range(0, path_len, 4):
            px = x + facing * (30 + i)
            py = y + 50 + int(math.sin(phase * 2 + i * 0.2) * 2)
            fade = 1 - i / max(1, path_len)
            alpha = _NS_ravokkar._alpha(220 * fade)
            pygame.draw.ellipse(surface,
                                (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                (px - 5, py - 2, 10, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                (px - 4, py - 1, 8, 3))
            if i % 8 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                 (px, py, 2, 2))
    def _draw_quickdraw_foreground(surface, boss, x, y, timer, phase):
        """Afterimages + reload effect + empowered shell prep."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Afterimages
        for i in range(4):
            offset = -(i + 1) * 18 * facing
            alpha = _NS_ravokkar._alpha(180 - i * 35)
            if alpha <= 0:
                continue
            silh = pygame.Surface((60, 90), pygame.SRCALPHA)
            for r in range(16, 4, -3):
                a = _NS_ravokkar._alpha(alpha * (16 - r) / 16)
                _NS_ravokkar._aacircle(silh,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], a),
                                        (30, 45), r)
            surface.blit(silh, (x + offset - 30, y - 45))
        # Speed lines
        for i in range(8):
            line_y = y - 30 + i * 7
            line_alpha = _NS_ravokkar._alpha(200 - abs(4 - i) * 30)
            line_len = 30 + i * 3
            pygame.draw.line(surface,
                             (*_NS_ravokkar.PALETTE["fire_light"], line_alpha),
                             (x - facing * 20, line_y),
                             (x - facing * (20 + line_len), line_y), 2)
            pygame.draw.line(surface,
                             (*_NS_ravokkar.PALETTE["fire_hot"], line_alpha),
                             (x - facing * 20, line_y),
                             (x - facing * (20 + line_len // 2), line_y), 1)
        # Ejecting bullet shells (spent casings)
        if progress > 0.5:
            for i in range(2):
                shell_t = ((progress - 0.5) * 2 + i * 0.3) % 1.0
                shell_x = x + facing * (15 + int(shell_t * 15))
                shell_y = y - 15 - int(shell_t * 20) + int(shell_t * shell_t * 30)
                shell_alpha = _NS_ravokkar._alpha(240 * (1 - shell_t))
                # Bullet casing
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["gold_dark"], shell_alpha),
                                 (shell_x - 1, shell_y, 3, 2))
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["gold_mid"], shell_alpha),
                                 (shell_x, shell_y, 2, 1))
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["gold_shine"], shell_alpha),
                                 (shell_x, shell_y, 1, 1))
    # ============================================================
    # SKILL R - COLLATERAL DAMAGE (massive explosive shell)
    # ============================================================
    def _draw_collateral_ground(surface, boss, x, y, timer, phase):
        """Big impact zone at target."""
        tx, ty = _NS_ravokkar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning circle grows
            t = progress / 0.4
            r = int(55 * t)
        else:
            r = 55 + int(math.sin(phase * 2) * 4)
        alpha = _NS_ravokkar._alpha(220 * min(1.0, progress * 2))
        pygame.draw.ellipse(surface, (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 3)
        pygame.draw.ellipse(surface, (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                            (tx - r + 8, ty - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 2)
        pygame.draw.ellipse(surface, (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                            (tx - r + 14, ty - r // 3 + 6,
                             r * 2 - 28, r * 2 // 3 - 12), 1)
        # Rotating runes
        for i in range(12):
            angle = phase * 1.5 + i * math.pi / 6
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_hot"],
                             (sx - 1, sy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_shine"],
                             (sx, sy, 1, 1))
    def _draw_collateral_foreground(surface, boss, x, y, timer, phase):
        """Big explosive shell that fires and detonates."""
        facing = boss.direction
        tx, ty = _NS_ravokkar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Charge — big glow at muzzle
            t = progress / 0.15
            mx = x + facing * 44
            my = y - 6
            cr = int(6 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_ravokkar._alpha(240 * (cr + 6 - r) / (cr + 6))
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                        (mx, my), r)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_dark"],
                                    (mx, my), cr - 2)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_mid"],
                                    (mx, my), max(1, cr - 4))
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_hot"],
                                    (mx, my), max(1, cr - 6))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_shine"],
                             (mx, my, 1, 1))
            # Sparks
            for i in range(10):
                angle = phase * 4 + i * math.pi / 5
                sx = mx + int(math.cos(angle) * (cr + 4))
                sy = my + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_hot"],
                                 (sx, sy, 2, 2))
        elif progress < 0.5:
            # Shell flying
            t = (progress - 0.15) / 0.35
            start_x = x + facing * 44
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t - int(math.sin(t * math.pi) * 15))
            # HUGE explosive shell trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t - int(math.sin(trail_t * math.pi) * 15))
                alpha = _NS_ravokkar._alpha(240 - i * 22)
                size = max(2, 10 - i)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                        (px, py), size + 2)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                        (px, py), size + 1)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                        (px, py), size)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                        (px, py), max(1, size - 3))
            # BIG shell body (dark iron ball with fire glow)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["shadow_deep"],
                                    (bx + 1, by + 1), 8)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["gun_darkest"],
                                    (bx, by), 8)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_dark"],
                                    (bx, by), 6)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_mid"],
                                    (bx, by), 4)
            _NS_ravokkar._aacircle(surface, _NS_ravokkar.PALETTE["fire_hot"],
                                    (bx, by), 2)
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["fire_shine"],
                             (bx, by, 1, 1))
            pygame.draw.rect(surface, _NS_ravokkar.PALETTE["white"],
                             (bx, by, 1, 1))
            # Glow halo
            for r in range(14, 5, -2):
                a = _NS_ravokkar._alpha(120 * (14 - r) / 14)
                _NS_ravokkar._aacircle(surface,
                                        (*_NS_ravokkar.PALETTE["fire_light"], a),
                                        (bx, by), r)
        elif progress < 0.85:
            # DETONATE — MASSIVE EXPLOSION
            t = (progress - 0.5) / 0.35
            intensity = math.sin(t * math.pi)
            imp_r = int(30 + t * 50)
            alpha = _NS_ravokkar._alpha(240 * intensity)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_darkest"], alpha),
                                    (tx, ty), imp_r + 5, 5)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_dark"], alpha),
                                    (tx, ty), imp_r, 4)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                    (tx, ty), max(1, imp_r - 10), 3)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_light"], alpha),
                                    (tx, ty), max(1, imp_r - 20), 2)
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                    (tx, ty), max(1, imp_r // 4))
            _NS_ravokkar._aacircle(surface,
                                    (*_NS_ravokkar.PALETTE["fire_shine"], alpha),
                                    (tx, ty), max(1, imp_r // 8))
            # Radial fire lines (shrapnel)
            for i in range(20):
                angle_s = i * math.pi / 10
                ex = tx + int(math.cos(angle_s) * imp_r)
                ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                pygame.draw.line(surface,
                                 (*_NS_ravokkar.PALETTE["fire_light"], alpha),
                                 (tx, ty), (ex, ey), 3)
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
            # Shell fragments flying
            for frag_i in range(12):
                frag_angle = frag_i * math.pi / 6 + phase
                frag_dist = int(imp_r * (0.6 + 0.4 * math.sin(phase + frag_i)))
                fx = tx + int(math.cos(frag_angle) * frag_dist)
                fy = ty + int(math.sin(frag_angle) * frag_dist * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["gun_dark"], alpha),
                                 (fx - 1, fy - 1, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_ravokkar.PALETTE["fire_hot"], alpha),
                                 (fx, fy, 1, 1))
        else:
            # Aftermath — smoke rising
            t = (progress - 0.85) / 0.15
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.09) % 1.0
                rx = tx + int(math.sin(phase + i) * 35)
                ry = ty - int(rise_t * 40)
                alpha = _NS_ravokkar._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["smoke_dark"], alpha),
                                            (rx, ry), 4)
                    _NS_ravokkar._aacircle(surface,
                                            (*_NS_ravokkar.PALETTE["smoke_mid"], alpha),
                                            (rx, ry), 3)
                    pygame.draw.rect(surface,
                                     (*_NS_ravokkar.PALETTE["fire_mid"], alpha),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_celwynn(surface, boss, x, y):
    """Entry point celwynn."""
    return _NS_celwynn.draw_celwynn(surface, boss, x, y)


def draw_rynvara(surface, boss, x, y):
    """Entry point rynvara."""
    return _NS_rynvara.draw_rynvara(surface, boss, x, y)


def draw_syrindra(surface, boss, x, y):
    """Entry point syrindra."""
    return _NS_syrindra.draw_syrindra(surface, boss, x, y)


def draw_ravokkar(surface, boss, x, y):
    """Entry point ravokkar."""
    return _NS_ravokkar.draw_ravokkar(surface, boss, x, y)
