"""
bosses/level2.py - Semua boss Level 2 (REBUILD: Procedural Masterwork)

Gabungan dari 4 file terpisah:
  - razak                (mini boss)  - goblin rider di atas beast kelelawar
  - khalros              (mini boss)  - Beastlord bertanduk, dual axe
  - gorath               (mini boss)  - Bloodwarden iblis merah, curved blade
  - alchemist            (TRUE BOSS)  - ogre + goblin rider, cleaver + acid

Semua boss dibangun ulang di atas mesin bone-rig bersama
``bosses/_masterwork.py`` mengikuti standar Kaizen / Gornak / Drakar:

* SATU bone rig 2D berlapis - sendi (pinggul, lutut, mata kaki, bahu, siku,
  pergelangan) dihitung tiap frame dari ``phase``/``action``.
* Telapak kaki DIPATOK ke ``GROUND_DY`` sementara badan bernapas/bob.
* Senjata POSE-DRIVEN: sudut senjata diturunkan dari garis lengan per-frame.
* Idle bob >= 4 px terlihat; walk alternating stride + lift + sway;
  attack windup + lunge + impact yang distinktif.
* Skill FX: ground ring + partikel + kilat dramatis per fase
  (charge / burst / afterglow).
* Portrait HD (``_portrait_hd=True``): aura/ground FX dibuang, rig dipusatkan.
* Kedua arah (kiri/kanan) benar.

Entry point publik ada di bagian paling bawah file.
"""

import math

import pygame

from bosses import _masterwork as MW

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
_IS_LEVEL_BUNDLE = True


# ======================================================================
# Helper bersama antar-namespace (grip lengan humanoid)
# ======================================================================
def _humanoid_grips(action, ap, phase, rest_f=2, rest_b=3, compact=False):
    """(front_grip, back_grip) ruang lokal - tabel pose lengan."""
    if compact:
        return (12, rest_f + 2), (-13, rest_b + 3)
    if action == "attack":
        if ap < 0.26:
            t = min(1.0, ap / 0.26) ** 0.9
            return (int(15 - 13 * t), int(rest_f - 27 * t)), \
                   (int(-19 - 5 * t), int(rest_b - 24 * t))
        if ap < 0.79:
            t = (ap - 0.26) / 0.53
            return (int(2 + 21 * t), int(rest_f - 27 + 33 * t)), \
                   (int(-24 - 3 * t), int(rest_b - 24 + 30 * t))
        t = (ap - 0.79) / 0.18
        return (int(23 - 8 * t), int(rest_f + 6 - 4 * t)), \
               (int(-27 + 8 * t), int(rest_b + 6 - 3 * t))
    if action in ("q", "surge"):
        return (23, rest_f + 3), (-21, rest_b - 3)
    if action in ("e", "ward"):
        return (14, rest_f - 9), (-20, rest_b - 11)
    if action in ("r", "void"):
        return (19, rest_f - 15), (-21, rest_b - 14)
    if action in ("w", "blink"):
        return (16, rest_f - 2), (-20, rest_b - 1)
    if action == "walk":
        s = math.sin(phase * 1.72)
        return (int(15 + s * 3), int(rest_f - s * 2)), \
               (int(-19 + s * 3), int(rest_b + s * 2))
    # idle = stance "siap": lengan depan diangkat setinggi bahu ke depan &
    # lengan belakang mở ke belakang, supaya garis lengan (dan bilah yang
    # mengikutinya) horizontal -> menambah LEBAR siluet (bukan tiang sempit).
    w = math.sin(phase * 0.5) * 1
    return (int(20 + w), int(rest_f - 13)), (int(-18 - w), int(rest_b - 9))


SHOULDER_Y = -14
SHOULDER_FRONT = (12, SHOULDER_Y)
SHOULDER_BACK = (-11, SHOULDER_Y - 1)
HEAD_Y = -24


# ====================================================================
# RAZAK - goblin rider di atas beast kelelawar (fire)
# ====================================================================
class _NS_razak:
    """Namespace razak - Procedural Masterwork."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    SCALE = 1.25
    LIFT = 4
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT
    RIG_W, RIG_H = 190, 184
    RIG_OX, RIG_OY = 95, 104
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)
    SKILL_DUR = {"q": 40, "w": 50, "e": 35, "r": 90}

    PALETTE = {
        "gob_darkest": (25, 45, 20), "gob_dark": (55, 95, 38),
        "gob_mid": (95, 145, 55), "gob_light": (140, 190, 78),
        "gob_high": (185, 225, 120), "gob_shine": (225, 250, 175),
        "bat_darkest": (35, 15, 10), "bat_dark": (95, 32, 18),
        "bat_mid": (155, 62, 25), "bat_light": (210, 95, 38),
        "bat_high": (240, 140, 65), "bat_shine": (255, 180, 100),
        "belly_dark": (105, 55, 25), "belly_mid": (170, 105, 55),
        "belly_light": (215, 155, 85),
        "wing_darkest": (30, 12, 8), "wing_dark": (75, 25, 15),
        "wing_mid": (135, 45, 22), "wing_light": (190, 78, 35),
        "leather_darkest": (22, 14, 8), "leather_dark": (50, 32, 18),
        "leather_mid": (95, 62, 32), "leather_light": (150, 100, 55),
        "metal_darkest": (18, 15, 18), "metal_dark": (48, 42, 48),
        "metal_mid": (95, 88, 95), "metal_light": (160, 152, 165),
        "metal_shine": (225, 220, 225),
        "brass_dark": (80, 50, 15), "brass_mid": (155, 108, 40),
        "brass_light": (210, 170, 80), "brass_shine": (250, 220, 140),
        "fire_darkest": (55, 12, 5), "fire_dark": (135, 30, 8),
        "fire_mid": (215, 80, 15), "fire_bright": (255, 130, 30),
        "fire_hot": (255, 180, 60), "fire_glow": (255, 220, 130),
        "fire_white": (255, 250, 210),
        "blue_dark": (15, 35, 75), "blue_mid": (45, 95, 165),
        "blue_light": (95, 165, 230), "blue_shine": (170, 220, 255),
        "eye_dark": (15, 25, 8), "eye_bright": (255, 220, 100),
        "eye_hot": (255, 250, 200),
        "bone_dark": (110, 95, 70), "bone_light": (220, 210, 175),
        "shadow": (0, 0, 0), "shadow_deep": (5, 3, 3),
        "white": (255, 255, 255),
    }

    _CFG = MW.RigConfig("razak", PALETTE, SCALE, LIFT, FEET_DY,
                        RIG_W, RIG_H, RIG_OX, RIG_OY, SKILL_DUR)

    # ------------------------------------------------------------------
    def _paint_rig(P):
        p = P.cfg.PALETTE
        f = P.f
        # 1. Sayap kelelawar di belakang (flap oleh phase)
        _NS_razak._wings(P)
        # 2. Kaki beast menapak
        legcols = {"shadow_deep": p["shadow_deep"], "thigh": p["bat_dark"],
                   "thigh_light": p["bat_mid"], "shin": p["bat_darkest"],
                   "shin_light": p["bat_dark"], "knee": p["bat_mid"],
                   "boot": p["bat_darkest"], "boot_edge": p["bat_mid"]}
        for side in (-1, 1):
            MW.draw_leg(P, side, legcols, stance=6, stride_amt=7,
                        lift_amt=4, thigh_w=6, shin_w=5)
        # 3. Badan beast
        _NS_razak._beast_body(P)
        # 4. Kepala beast
        _NS_razak._beast_head(P)
        # 5. Goblin rider (torso kecil + kepala + lengan dengan machete)
        _NS_razak._rider(P)
        # 6. Rim light api
        _NS_razak._rim(P)

    def _wings(P):
        p = P.cfg.PALETTE
        flap = math.sin(P.phase * (2.5 if P.action == "walk" else 1.2)) * 0.35
        for side in (-1, 1):
            base = P.pt(side * 8, -6)
            tip = P.pt(side * (30 + int(math.cos(flap) * 5)),
                       -20 + int(math.sin(flap) * 7))
            mid = P.pt(side * 24, -10 + int(math.sin(flap) * 5))
            low = P.pt(side * 20, 2 + int(math.sin(flap) * 3))
            root = P.pt(side * 4, -2)
            shape = [base, tip, (mid[0], mid[1] - 2), mid, low, root]
            P.poly_free(p["wing_darkest"], shape)
            P.poly_free(p["wing_dark"], [base, (tip[0] - P.f * 2, tip[1] + 1),
                                         mid, low, root], outline=False)
            MW.aaline(P.surface, p["wing_mid"], base, tip, 2)
            MW.aaline(P.surface, p["wing_mid"], base, mid, 1)
            MW.aaline(P.surface, p["wing_light"], base, low, 1)

    def _beast_body(P):
        p = P.cfg.PALETTE
        b = int(P.breath * 1.2)
        body = [(-16, 6 - b), (14, 4 - b), (16, 12 - b), (2, 18), (-14, 16)]
        P.poly_free(p["bat_darkest"], [P.pt(*q) for q in body])
        P.poly_free(p["bat_mid"], [P.pt(*q) for q in
                    [(-12, 6 - b), (10, 5 - b), (12, 11 - b), (0, 15), (-10, 13)]],
                    outline=False)
        P.poly_free(p["belly_mid"], [P.pt(*q) for q in
                    [(-8, 12 - b), (8, 11 - b), (6, 16), (-6, 16)]], outline=False)

    def _beast_head(P):
        p = P.cfg.PALETTE
        hx, hy = P.pt(16, 0)
        MW.aacircle(P.surface, p["shadow_deep"], (hx + P.f, hy + 1), P._s(7) + 1)
        MW.aacircle(P.surface, p["bat_mid"], (hx, hy), P._s(7))
        MW.aacircle(P.surface, p["bat_light"], (hx - P.f, hy - 1), P._s(4))
        # telinga
        ear = [P.pt(14, -6), P.pt(12, -12), P.pt(17, -7)]
        P.poly_free(p["bat_dark"], ear)
        # mata
        ex, ey = P.pt(18, -1)
        MW.aacircle(P.surface, p["eye_bright"], (ex, ey), 1)

    def _rider(P):
        p = P.cfg.PALETTE
        # torso goblin di atas beast
        torso = [(-6, -14), (6, -14), (7, -6), (-7, -6)]
        P.poly_free(p["gob_dark"], [P.pt(*q) for q in torso])
        P.poly_free(p["gob_mid"], [P.pt(*q) for q in
                    [(-4, -13), (3, -13), (4, -8), (-4, -8)]], outline=False)
        # kepala goblin + goggles + telinga
        hx, hy = P.pt(0, -22)
        MW.aacircle(P.surface, p["shadow_deep"], (hx + P.f, hy + 1), P._s(6) + 1)
        MW.aacircle(P.surface, p["gob_mid"], (hx, hy), P._s(6))
        MW.aacircle(P.surface, p["gob_light"], (hx - P.f, hy - 1), P._s(3))
        ear = [P.pt(-4, -24), P.pt(-9, -27), P.pt(-4, -21)]
        P.poly_free(p["gob_dark"], ear)
        # goggles biru
        gx, gy = P.pt(3, -23)
        MW.aacircle(P.surface, p["blue_mid"], (gx, gy), P._s(2))
        MW.aacircle(P.surface, p["blue_shine"], (gx, gy), 1)
        # lengan + machete pose-driven
        fg, bg = _humanoid_grips(P.action, P.ap, P.phase, rest_f=-8,
                                 rest_b=-7, compact=P.detail)
        armcols = {"shadow_deep": p["shadow_deep"], "upper": p["gob_dark"],
                   "fore": p["gob_mid"], "hand": p["gob_light"]}
        sh_b = (-6, -13)
        sh_f = (6, -13)
        MW.draw_arm(P, sh_b, bg, 4.0, armcols)
        MW.draw_arm(P, sh_f, fg, -4.0, armcols,
                    weapon={"len": 26, "tilt": 0.5, "w": 3,
                            "blade": p["metal_mid"], "edge": p["metal_shine"],
                            "glow": p["fire_bright"]})

    def _rim(P):
        p = P.cfg.PALETTE
        MW.aaline(P.surface, (*p["fire_bright"], 120), P.pt(-14, 4),
                  P.pt(-12, 14), 1)

    # ------------------------------------------------------------------
    def draw_razak(surface, boss, x, y):
        NS = _NS_razak
        MW.update_attack_anim(boss, "_rz", 40)
        moving = MW.detect_moving(boss, "_rz")
        action, phase, ap = MW.resolve_pose(boss, "_rz", moving)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = MW.alpha(170 * (getattr(boss, "hurt_flash_timer", 0) / 8.0))
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))

        if not portrait:
            MW.draw_shadow(surface, x, y + NS.GROUND_DY, NS._CFG)
            if skill:
                MW.draw_skill_fx(surface, x, y, NS._CFG, timer,
                                 NS.SKILL_DUR.get(skill, 60),
                                 {"ring": NS.PALETTE["fire_mid"],
                                  "hot": NS.PALETTE["fire_bright"],
                                  "shine": NS.PALETTE["fire_white"]},
                                 phase=phase, radius=48)
        buf = MW.compose(NS._CFG, NS._paint_rig, facing, phase, action, ap,
                         portrait, flash, hero_lane)
        MW.blit_rig(surface, NS._CFG, buf, x, y, portrait)


# ====================================================================
# KHALROS - Beastlord bertanduk, dual axe
# ====================================================================
class _NS_khalros:
    """Namespace khalros - Procedural Masterwork."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    SCALE = 1.32
    LIFT = 4
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT
    RIG_W, RIG_H = 190, 184
    RIG_OX, RIG_OY = 95, 100
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)
    SKILL_DUR = {"q": 50, "w": 60, "e": 45, "r": 70}

    PALETTE = {
        "skin_darkest": (55, 30, 20), "skin_dark": (115, 68, 45),
        "skin_mid": (170, 108, 72), "skin_light": (215, 158, 108),
        "skin_high": (240, 200, 155), "skin_shine": (255, 230, 195),
        "hair_darkest": (18, 12, 8), "hair_dark": (48, 32, 20),
        "hair_mid": (85, 58, 35), "hair_high": (135, 95, 55),
        "leather_darkest": (25, 15, 8), "leather_dark": (55, 32, 15),
        "leather_mid": (95, 62, 32), "leather_light": (150, 100, 55),
        "leather_high": (200, 148, 88),
        "metal_darkest": (18, 16, 18), "metal_dark": (52, 48, 55),
        "metal_mid": (105, 100, 108), "metal_light": (170, 165, 175),
        "metal_shine": (225, 220, 225), "metal_edge": (250, 245, 250),
        "gold_dark": (90, 60, 15), "gold_mid": (170, 130, 40),
        "gold_light": (230, 190, 80), "gold_shine": (255, 230, 150),
        "fire_dark": (75, 20, 5), "fire_mid": (185, 60, 15),
        "fire_bright": (235, 120, 30), "fire_hot": (255, 180, 60),
        "fire_glow": (255, 220, 130), "fire_white": (255, 245, 200),
        "red_dark": (85, 15, 12), "red_mid": (170, 30, 25),
        "red_bright": (225, 55, 45), "red_hot": (255, 100, 80),
        "boar_darkest": (30, 18, 12), "boar_dark": (65, 40, 22),
        "boar_mid": (110, 72, 42), "boar_light": (160, 110, 68),
        "boar_high": (200, 150, 100),
        "wolf_darkest": (25, 22, 25), "wolf_dark": (55, 52, 58),
        "wolf_mid": (95, 92, 100), "wolf_light": (150, 148, 155),
        "wolf_high": (200, 198, 205),
        "bone_dark": (115, 100, 78), "bone_light": (220, 210, 180),
        "shadow": (0, 0, 0), "shadow_deep": (5, 3, 3),
        "white": (255, 255, 255),
    }

    _CFG = MW.RigConfig("khalros", PALETTE, SCALE, LIFT, FEET_DY,
                        RIG_W, RIG_H, RIG_OX, RIG_OY, SKILL_DUR)

    def _paint_rig(P):
        p = P.cfg.PALETTE
        # kaki
        legcols = {"shadow_deep": p["shadow_deep"], "thigh": p["skin_dark"],
                   "thigh_light": p["skin_mid"], "shin": p["leather_dark"],
                   "shin_light": p["leather_mid"], "knee": p["leather_mid"],
                   "boot": p["leather_darkest"], "boot_edge": p["leather_mid"]}
        for side in (-1, 1):
            MW.draw_leg(P, side, legcols, stance=5)
        # wolf pelt di punggung (belakang)
        _NS_khalros._pelt(P)
        # torso
        MW.draw_torso(P, {"shadow_deep": p["shadow_deep"],
                          "pelvis": p["leather_dark"],
                          "chest": p["skin_mid"],
                          "chest_light": p["skin_light"]})
        # sabuk
        P.poly_free(p["leather_mid"], [P.pt(-11, 1), P.pt(11, 1),
                                       P.pt(10, 5), P.pt(-10, 5)])
        P.dot(0, 3, 1.6, p["gold_mid"])
        # lengan belakang + axe
        fg, bg = _humanoid_grips(P.action, P.ap, P.phase, compact=P.detail)
        armcols = {"shadow_deep": p["shadow_deep"], "upper": p["skin_dark"],
                   "upper_light": p["skin_mid"], "fore": p["skin_mid"],
                   "fore_light": p["skin_light"], "hand": p["skin_light"]}
        axe = {"len": 30, "tilt": 0.4, "w": 3, "blade": p["metal_mid"],
               "edge": p["metal_edge"], "glow": None}
        MW.draw_arm(P, SHOULDER_BACK, bg, 5.0, armcols, weapon=axe)
        # pauldron
        P.dot(-11, SHOULDER_Y, 4.5, p["leather_mid"])
        P.dot(12, SHOULDER_Y, 4.5, p["boar_mid"])
        # kepala bertanduk
        _NS_khalros._head(P)
        # lengan depan + axe
        MW.draw_arm(P, SHOULDER_FRONT, fg, -4.5, armcols, weapon=axe)
        # rim
        MW.aaline(P.surface, (*p["gold_light"], 110), P.pt(-12, -12),
                  P.pt(-10, 2), 1)

    def _pelt(P):
        p = P.cfg.PALETTE
        sway = int(math.sin(P.phase * 1.05) * 2)
        outer = [(-13, -16), (-17, -4), (-19 + sway, 8), (-13 + sway, 13),
                 (-8 + sway, 7), (-4, -6), (-3, -16)]
        P.poly_free(p["wolf_darkest"], [P.pt(*q) for q in outer])
        P.poly_free(p["wolf_dark"], [P.pt(*q) for q in
                    [(-12, -14), (-15, -4), (-16 + sway, 6), (-11 + sway, 10),
                     (-8, -4), (-6, -14)]], outline=False)
        MW.aaline(P.surface, p["wolf_light"], P.pt(-12, -12),
                  P.pt(-14 + sway, 4), 1)

    def _head(P):
        p = P.cfg.PALETTE
        hx, hy = P.pt(0, HEAD_Y)
        MW.aacircle(P.surface, p["shadow_deep"], (hx + P.f, hy + 1), P._s(7) + 1)
        MW.aacircle(P.surface, p["skin_mid"], (hx, hy), P._s(7))
        MW.aacircle(P.surface, p["skin_light"], (hx - P.f, hy - 1), P._s(4))
        # helm
        P.poly_free(p["metal_dark"], [P.pt(-6, -28), P.pt(6, -28),
                                      P.pt(5, -24), P.pt(-5, -24)])
        # tanduk
        P.poly_free(p["bone_dark"], [P.pt(-5, -28), P.pt(-11, -33),
                                     P.pt(-4, -26)])
        P.poly_free(p["bone_dark"], [P.pt(5, -28), P.pt(11, -33),
                                     P.pt(4, -26)])
        # mata
        ex, ey = P.pt(3, -24)
        MW.aacircle(P.surface, p["fire_bright"], (ex, ey), 1)

    def draw_khalros(surface, boss, x, y):
        NS = _NS_khalros
        MW.update_attack_anim(boss, "_kh", 42)
        moving = MW.detect_moving(boss, "_kh")
        action, phase, ap = MW.resolve_pose(boss, "_kh", moving)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = MW.alpha(170 * (getattr(boss, "hurt_flash_timer", 0) / 8.0))
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        if not portrait:
            MW.draw_shadow(surface, x, y + NS.GROUND_DY, NS._CFG)
            if skill:
                MW.draw_skill_fx(surface, x, y, NS._CFG, timer,
                                 NS.SKILL_DUR.get(skill, 60),
                                 {"ring": NS.PALETTE["gold_mid"],
                                  "hot": NS.PALETTE["fire_bright"],
                                  "shine": NS.PALETTE["fire_white"]},
                                 phase=phase, radius=50)
        buf = MW.compose(NS._CFG, NS._paint_rig, facing, phase, action, ap,
                         portrait, flash, hero_lane)
        MW.blit_rig(surface, NS._CFG, buf, x, y, portrait)


# ====================================================================
# GORATH - Bloodwarden iblis merah, curved blade
# ====================================================================
class _NS_gorath:
    """Namespace gorath - Procedural Masterwork."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    SCALE = 1.32
    LIFT = 4
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT
    RIG_W, RIG_H = 190, 184
    RIG_OX, RIG_OY = 95, 100
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)
    SKILL_DUR = {"q": 90, "w": 60, "e": 35, "r": 90}

    PALETTE = {
        "skin_darkest": (35, 10, 10), "skin_dark": (78, 22, 20),
        "skin_mid": (125, 45, 35), "skin_light": (175, 78, 55),
        "skin_high": (215, 130, 90), "skin_shine": (245, 185, 140),
        "blood_darkest": (25, 3, 5), "blood_dark": (72, 6, 10),
        "blood_mid": (135, 15, 20), "blood_bright": (195, 25, 30),
        "blood_hot": (235, 55, 50), "blood_glow": (255, 100, 85),
        "blood_light": (255, 165, 140),
        "hair_darkest": (10, 8, 12), "hair_dark": (28, 22, 30),
        "hair_mid": (55, 45, 58), "hair_high": (95, 82, 100),
        "leather_darkest": (18, 12, 8), "leather_dark": (45, 28, 18),
        "leather_mid": (85, 55, 30), "leather_light": (135, 90, 50),
        "leather_high": (185, 135, 80),
        "bone_darkest": (55, 45, 35), "bone_dark": (115, 100, 78),
        "bone_mid": (175, 160, 130), "bone_light": (220, 210, 180),
        "bone_shine": (245, 240, 220),
        "metal_darkest": (18, 15, 18), "metal_dark": (48, 42, 48),
        "metal_mid": (95, 88, 95), "metal_light": (155, 148, 155),
        "metal_shine": (215, 210, 215),
        "eye_dark": (80, 5, 8), "eye_mid": (180, 20, 25),
        "eye_bright": (240, 55, 50), "eye_hot": (255, 130, 100),
        "eye_white": (255, 220, 200),
        "shadow": (0, 0, 0), "shadow_deep": (5, 2, 3),
        "white": (255, 255, 255),
    }

    _CFG = MW.RigConfig("gorath", PALETTE, SCALE, LIFT, FEET_DY,
                        RIG_W, RIG_H, RIG_OX, RIG_OY, SKILL_DUR)

    def _paint_rig(P):
        p = P.cfg.PALETTE
        legcols = {"shadow_deep": p["shadow_deep"], "thigh": p["skin_dark"],
                   "thigh_light": p["skin_mid"], "shin": p["skin_darkest"],
                   "shin_light": p["skin_dark"], "knee": p["skin_mid"],
                   "boot": p["leather_darkest"], "boot_edge": p["leather_mid"]}
        for side in (-1, 1):
            MW.draw_leg(P, side, legcols, stance=5)
        MW.draw_torso(P, {"shadow_deep": p["shadow_deep"],
                          "pelvis": p["leather_dark"],
                          "chest": p["skin_mid"],
                          "chest_light": p["skin_light"]})
        # tato darah di dada
        MW.aaline(P.surface, p["blood_mid"], P.pt(-4, -10), P.pt(2, -4), 1)
        P.poly_free(p["leather_mid"], [P.pt(-11, 1), P.pt(11, 1),
                                       P.pt(10, 5), P.pt(-10, 5)])
        P.dot(0, 3, 1.6, p["bone_mid"])
        fg, bg = _humanoid_grips(P.action, P.ap, P.phase, compact=P.detail)
        armcols = {"shadow_deep": p["shadow_deep"], "upper": p["skin_dark"],
                   "upper_light": p["skin_mid"], "fore": p["skin_mid"],
                   "fore_light": p["skin_light"], "hand": p["skin_light"]}
        blade = {"len": 32, "tilt": 0.6, "w": 3, "blade": p["metal_mid"],
                 "edge": p["metal_shine"], "glow": p["blood_bright"]}
        MW.draw_arm(P, SHOULDER_BACK, bg, 5.0, armcols, weapon=blade)
        P.dot(-11, SHOULDER_Y, 4.5, p["bone_dark"])
        P.dot(12, SHOULDER_Y, 4.5, p["bone_dark"])
        _NS_gorath._head(P)
        MW.draw_arm(P, SHOULDER_FRONT, fg, -4.5, armcols, weapon=blade)
        # tetesan darah
        _NS_gorath._drips(P)
        MW.aaline(P.surface, (*p["blood_bright"], 120), P.pt(-12, -12),
                  P.pt(-10, 2), 1)

    def _head(P):
        p = P.cfg.PALETTE
        hx, hy = P.pt(0, HEAD_Y)
        MW.aacircle(P.surface, p["shadow_deep"], (hx + P.f, hy + 1), P._s(7) + 1)
        MW.aacircle(P.surface, p["skin_mid"], (hx, hy), P._s(7))
        MW.aacircle(P.surface, p["skin_light"], (hx - P.f, hy - 1), P._s(4))
        # rambut berduri
        for i, dx in enumerate((-5, -2, 1, 4)):
            P.poly_free(p["hair_dark"], [P.pt(dx, -28), P.pt(dx + 1, -34 - (i % 2)),
                                         P.pt(dx + 3, -28)])
        # mata merah menyala
        ex, ey = P.pt(3, -24)
        MW.aacircle(P.surface, p["eye_bright"], (ex, ey), 1)

    def _drips(P):
        p = P.cfg.PALETTE
        t = P.phase * 0.8
        for i in range(3):
            tt = (t + i * 0.33) % 1.0
            dx = -6 + i * 5
            dy = 6 + int(tt * 10)
            MW.aacircle(P.surface, (*p["blood_bright"], MW.alpha(160 * (1 - tt))),
                        P.pt(dx, dy), 1)

    def draw_gorath(surface, boss, x, y):
        NS = _NS_gorath
        MW.update_attack_anim(boss, "_go", 38)
        moving = MW.detect_moving(boss, "_go")
        action, phase, ap = MW.resolve_pose(boss, "_go", moving)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = MW.alpha(170 * (getattr(boss, "hurt_flash_timer", 0) / 8.0))
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        if not portrait:
            MW.draw_shadow(surface, x, y + NS.GROUND_DY, NS._CFG)
            if skill:
                MW.draw_skill_fx(surface, x, y, NS._CFG, timer,
                                 NS.SKILL_DUR.get(skill, 60),
                                 {"ring": NS.PALETTE["blood_mid"],
                                  "hot": NS.PALETTE["blood_bright"],
                                  "shine": NS.PALETTE["blood_light"]},
                                 phase=phase, radius=50)
        buf = MW.compose(NS._CFG, NS._paint_rig, facing, phase, action, ap,
                         portrait, flash, hero_lane)
        MW.blit_rig(surface, NS._CFG, buf, x, y, portrait)


# ====================================================================
# ALCHEMIST - ogre + goblin rider (TRUE BOSS)
# ====================================================================
class _NS_alchemist:
    """Namespace alchemist - Procedural Masterwork."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    SCALE = 1.4
    LIFT = 4
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT
    RIG_W, RIG_H = 200, 194
    RIG_OX, RIG_OY = 100, 104
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)
    SKILL_DUR = {"q": 40, "w": 60, "e": 60, "r": 90}

    PALETTE = {
        "ogre_darkest": (55, 30, 10), "ogre_dark": (120, 65, 20),
        "ogre_mid": (185, 115, 40), "ogre_light": (225, 165, 65),
        "ogre_high": (245, 205, 110), "ogre_shine": (255, 235, 175),
        "gob_darkest": (35, 20, 50), "gob_dark": (75, 45, 105),
        "gob_mid": (125, 80, 160), "gob_light": (180, 130, 210),
        "gob_high": (220, 175, 235),
        "acid_darkest": (18, 50, 10), "acid_dark": (55, 115, 20),
        "acid_mid": (110, 190, 30), "acid_bright": (170, 240, 55),
        "acid_hot": (215, 255, 100), "acid_glow": (240, 255, 170),
        "acid_white": (250, 255, 220),
        "gold_darkest": (60, 38, 10), "gold_dark": (135, 90, 15),
        "gold_mid": (215, 170, 40), "gold_light": (250, 220, 90),
        "gold_shine": (255, 245, 175),
        "leather_darkest": (22, 14, 8), "leather_dark": (55, 35, 20),
        "leather_mid": (100, 68, 35), "leather_light": (155, 108, 62),
        "metal_darkest": (18, 18, 22), "metal_dark": (48, 48, 55),
        "metal_mid": (95, 95, 105), "metal_light": (160, 158, 170),
        "metal_shine": (215, 215, 225), "metal_edge": (250, 250, 255),
        "brass_dark": (85, 55, 15), "brass_mid": (160, 115, 42),
        "brass_light": (215, 175, 82), "brass_shine": (250, 225, 145),
        "glass_dark": (25, 60, 20), "glass_mid": (65, 130, 35),
        "glass_light": (130, 200, 65), "glass_shine": (200, 245, 145),
        "bone_dark": (110, 95, 70), "bone_mid": (185, 170, 130),
        "bone_light": (235, 225, 190),
        "eye_dark": (5, 35, 5), "eye_hot": (255, 240, 100),
        "shadow": (0, 0, 0), "shadow_deep": (5, 3, 3),
        "white": (255, 255, 255), "red": (200, 40, 30),
    }

    _CFG = MW.RigConfig("alchemist", PALETTE, SCALE, LIFT, FEET_DY,
                        RIG_W, RIG_H, RIG_OX, RIG_OY, SKILL_DUR)

    def _paint_rig(P):
        p = P.cfg.PALETTE
        # backpack botol di punggung (belakang)
        _NS_alchemist._backpack(P)
        legcols = {"shadow_deep": p["shadow_deep"], "thigh": p["ogre_dark"],
                   "thigh_light": p["ogre_mid"], "shin": p["ogre_darkest"],
                   "shin_light": p["ogre_dark"], "knee": p["ogre_mid"],
                   "boot": p["leather_darkest"], "boot_edge": p["leather_mid"]}
        for side in (-1, 1):
            MW.draw_leg(P, side, legcols, stance=8, thigh_w=7, shin_w=6)
        MW.draw_torso(P, {"shadow_deep": p["shadow_deep"],
                          "pelvis": p["leather_dark"],
                          "chest": p["ogre_mid"],
                          "chest_light": p["ogre_light"]}, w=16)
        # perut ogre besar (bruise) menambah lebar siluet
        P.poly_free(p["ogre_dark"], [P.pt(-14, 0), P.pt(14, 0),
                                     P.pt(12, 8), P.pt(-12, 8)])
        # sabuk emas
        P.poly_free(p["leather_mid"], [P.pt(-13, 1), P.pt(13, 1),
                                       P.pt(12, 6), P.pt(-12, 6)])
        P.dot(0, 3, 2.0, p["gold_mid"])
        fg, bg = _humanoid_grips(P.action, P.ap, P.phase, compact=P.detail)
        armcols = {"shadow_deep": p["shadow_deep"], "upper": p["ogre_dark"],
                   "upper_light": p["ogre_mid"], "fore": p["ogre_mid"],
                   "fore_light": p["ogre_light"], "hand": p["ogre_light"]}
        cleaver = {"len": 36, "tilt": -0.55, "w": 4, "blade": p["metal_mid"],
                   "edge": p["metal_edge"], "glow": None}
        sh_b = (-13, SHOULDER_Y - 1)
        sh_f = (14, SHOULDER_Y)
        MW.draw_arm(P, sh_b, bg, 5.0, armcols,
                    weapon={"len": 22, "tilt": 0.5, "w": 3,
                            "blade": p["glass_mid"], "edge": p["glass_shine"],
                            "glow": p["acid_bright"]})
        P.dot(-14, SHOULDER_Y, 5.5, p["ogre_dark"])
        P.dot(15, SHOULDER_Y, 5.5, p["ogre_dark"])
        _NS_alchemist._head(P)
        _NS_alchemist._goblin_rider(P)
        MW.draw_arm(P, sh_f, fg, -4.5, armcols, weapon=cleaver)
        MW.aaline(P.surface, (*p["acid_bright"], 120), P.pt(-13, -12),
                  P.pt(-11, 3), 1)

    def _backpack(P):
        p = P.cfg.PALETTE
        sway = int(math.sin(P.phase * 1.05) * 1)
        P.poly_free(p["leather_darkest"], [P.pt(-16, -14), P.pt(-10, -16),
                                           P.pt(-9 + sway, 0), P.pt(-16 + sway, 0)])
        for i, dy in enumerate((-14, -9)):
            MW.aacircle(P.surface, p["glass_mid"], P.pt(-13 + sway, dy), P._s(2))
            MW.aacircle(P.surface, p["glass_shine"], P.pt(-13 + sway, dy), 1)

    def _head(P):
        p = P.cfg.PALETTE
        hx, hy = P.pt(1, HEAD_Y)
        MW.aacircle(P.surface, p["shadow_deep"], (hx + P.f, hy + 1), P._s(8) + 1)
        MW.aacircle(P.surface, p["ogre_mid"], (hx, hy), P._s(8))
        MW.aacircle(P.surface, p["ogre_light"], (hx - P.f, hy - 1), P._s(5))
        # taring
        P.poly_free(p["bone_light"], [P.pt(4, -20), P.pt(5, -16), P.pt(2, -19)])
        # mata
        ex, ey = P.pt(4, -25)
        MW.aacircle(P.surface, p["eye_hot"], (ex, ey), 1)

    def _goblin_rider(P):
        p = P.cfg.PALETTE
        # goblin ungu di bahu
        gx, gy = P.pt(-6, -32)
        MW.aacircle(P.surface, p["shadow_deep"], (gx + P.f, gy + 1), P._s(4) + 1)
        MW.aacircle(P.surface, p["gob_mid"], (gx, gy), P._s(4))
        # topi
        P.poly_free(p["gob_dark"], [P.pt(-9, -34), P.pt(-4, -40), P.pt(-2, -33)])
        ex, ey = P.pt(-4, -32)
        MW.aacircle(P.surface, p["eye_hot"], (ex, ey), 1)
        # botol kecil di tangan goblin
        MW.aacircle(P.surface, p["glass_mid"], P.pt(-1, -30), P._s(1.5))

    def draw_alchemist(surface, boss, x, y):
        NS = _NS_alchemist
        MW.update_attack_anim(boss, "_al", 46)
        moving = MW.detect_moving(boss, "_al")
        action, phase, ap = MW.resolve_pose(boss, "_al", moving)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = MW.alpha(170 * (getattr(boss, "hurt_flash_timer", 0) / 8.0))
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        if not portrait:
            MW.draw_shadow(surface, x, y + NS.GROUND_DY, NS._CFG, w=40)
            if skill:
                MW.draw_skill_fx(surface, x, y, NS._CFG, timer,
                                 NS.SKILL_DUR.get(skill, 60),
                                 {"ring": NS.PALETTE["acid_mid"],
                                  "hot": NS.PALETTE["acid_bright"],
                                  "shine": NS.PALETTE["acid_white"]},
                                 phase=phase, radius=56)
        buf = MW.compose(NS._CFG, NS._paint_rig, facing, phase, action, ap,
                         portrait, flash, hero_lane)
        MW.blit_rig(surface, NS._CFG, buf, x, y, portrait)


# ====================================================================
# Entry point publik
# ====================================================================
def draw_razak(surface, boss, x, y):
    _NS_razak.draw_razak(surface, boss, x, y)


def draw_khalros(surface, boss, x, y):
    _NS_khalros.draw_khalros(surface, boss, x, y)


def draw_gorath(surface, boss, x, y):
    _NS_gorath.draw_gorath(surface, boss, x, y)


def draw_alchemist(surface, boss, x, y):
    _NS_alchemist.draw_alchemist(surface, boss, x, y)
