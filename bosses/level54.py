"""
bosses/level54.py - Semua boss Level 54

Berisi:
  - obanai     (mini boss - MELEE serpent hashira, serpent breathing)
  - sanguire   (mini boss - RANGED blood manipulator, blood magic)
  - sasori     (mini boss - MELEE red sand puppeteer, puppet arts)
  - hollowbane (TRUE BOSS - MELEE substitute shinigami, zanpakuto)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================================================
# OBANAI - MINI BOSS
# ====================================================================================================

class _NS_obanai:
    """Namespace Obanai Iguro."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Uniform & Hair (Deep black/blue-ish gray)
        "darkest": (5, 5, 8),
        "dark": (15, 18, 25),
        "mid": (35, 40, 50),
        "light": (60, 65, 80),

        # Haori (Black & White stripes)
        "haori_white": (230, 235, 240),
        "haori_shadow": (160, 170, 185),
        "haori_black": (10, 12, 15),

        # Skin & Bandages
        "skin_dark": (160, 120, 100),
        "skin_mid": (210, 170, 140),
        "skin_light": (245, 215, 190),
        "bandage": (215, 215, 220),

        # Kaburamaru (White Snake)
        "snake_dark": (140, 145, 155),
        "snake_mid": (200, 205, 215),
        "snake_light": (245, 250, 255),
        "snake_eye": (255, 30, 40),

        # Serpent Sword (Silver with bluish tint)
        "blade_dark": (40, 45, 60),
        "blade_mid": (110, 120, 140),
        "blade_light": (190, 200, 220),
        "blade_shine": (240, 245, 255),

        # Serpent Breathing Aura (Poisonous Purple)
        "aura_darkest": (20, 5, 30),
        "aura_dark": (60, 15, 90),
        "aura_mid": (120, 40, 180),
        "aura_light": (180, 100, 240),
        "aura_glow": (230, 180, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    @staticmethod
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    @staticmethod
    def _alpha(v):
        return max(0, min(255, int(v)))

    @staticmethod
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_obanai._clamp(color)
        if _NS_obanai.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    @staticmethod
    def _aaline(surface, color, start, end, width=1):
        color = _NS_obanai._clamp(color)
        if _NS_obanai.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    @staticmethod
    def _poly(surface, color, points, width=0):
        pygame.draw.polygon(surface, _NS_obanai._clamp(color), points, width)

    @staticmethod
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 150 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    @staticmethod
    def draw_obanai(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_obanai._detect_moving(boss)

        _NS_obanai._update_attack_anim(boss)
        attacking = getattr(boss, "_attack_active", False)

        # Efek menghilang untuk skill D (Hidden Serpent)
        fade_alpha = 255
        if active_skill == "d":
            progress = max(0.0, min(1.0, 1 - skill_timer / 70.0))
            if progress < 0.2:
                fade_alpha = int(255 * (1 - progress / 0.2))
            elif progress < 0.8:
                fade_alpha = 0
            else:
                fade_alpha = int(255 * ((progress - 0.8) / 0.2))

        if fade_alpha > 0:
            _NS_obanai._draw_shadow(surface, x, y + 50)
            _NS_obanai._draw_aura(surface, x, y, pulse, fade_alpha)

            # Gambar Tubuh Obanai (Hanya jika tidak invisible)
            boss_surface = pygame.Surface((160, 160), pygame.SRCALPHA)
            bx, by = 80, 100  # Center of local surface

            if attacking:
                _NS_obanai._draw_pose_attack(boss_surface, boss, bx, by)
            elif moving:
                _NS_obanai._draw_pose_walk(boss_surface, boss, bx, by)
            else:
                _NS_obanai._draw_pose_idle(boss_surface, boss, bx, by)

            if fade_alpha < 255:
                boss_surface.set_alpha(fade_alpha)

            surface.blit(boss_surface, (x - 80, y - 100))

            # Melee Arc ditaruh di surface utama agar tidak terpotong
            if attacking:
                progress = getattr(boss, "_attack_progress", 0.0)
                _NS_obanai._draw_melee_slash(surface, boss, x, y, progress)

        # GROUND & FOREGROUND SKILLS
        if active_skill == "q":
            _NS_obanai._draw_skill_q(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_obanai._draw_skill_w(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_obanai._draw_skill_e(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_obanai._draw_skill_r(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_obanai._draw_skill_d(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    @staticmethod
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 30)))
        if getattr(boss, "trigger_attack", False):
            boss._attack_active = True
            boss._attack_frame = 0
            boss.trigger_attack = False

        active = getattr(boss, "_attack_active", False)
        if active:
            boss._attack_frame = getattr(boss, "_attack_frame", 0) + 1
            if boss._attack_frame >= cooldown:
                boss._attack_active = False
                boss._attack_frame = 0
                active = False

        boss._attack_progress = min(1.0, getattr(boss, "_attack_frame", 0) / max(1, cooldown)) if active else 0.0

    @staticmethod
    def _detect_moving(boss):
        if not hasattr(boss, "_last_x"):
            boss._last_x, boss._last_y = boss.x, boss.y
            return False
        dx = abs(boss.x - boss._last_x)
        dy = abs(boss.y - boss._last_y)
        boss._last_x, boss._last_y = boss.x, boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSES (Digambar di local surface)
    # ============================================================
    @staticmethod
    def _draw_pose_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_obanai._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")

    @staticmethod
    def _draw_pose_walk(surface, boss, x, y):
        phase = boss.pulse * 2.5
        bob = int(math.sin(phase) * 3)
        _NS_obanai._draw_body(surface, x, y + bob, boss.direction, phase, "walk")

    @staticmethod
    def _draw_pose_attack(surface, boss, x, y):
        progress = getattr(boss, "_attack_progress", 0.0)
        facing = boss.direction

        if progress < 0.3:
            lunge = -int((progress / 0.3) * 4) * facing
            lift = 2
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((t * 12) - 4) * facing
            lift = -2
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(8 * (1 - t)) * facing
            lift = 0

        _NS_obanai._draw_body(surface, x + lunge, y + lift, facing, boss.pulse, "attack", progress)

    # ============================================================
    # BODY PARTS
    # ============================================================
    @staticmethod
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        _NS_obanai._draw_legs(surface, cx, cy + 20, facing, phase, action)
        _NS_obanai._draw_torso_and_haori(surface, cx, cy + 2, facing, phase, action)

        arm_lift = 0
        if action == "attack":
            if attack_progress < 0.3:
                arm_lift = int((attack_progress / 0.3) * 10)
            elif attack_progress < 0.6:
                arm_lift = 10 - int(((attack_progress - 0.3) / 0.3) * 15)
            else:
                arm_lift = -5 + int(((attack_progress - 0.6) / 0.4) * 5)

        _NS_obanai._draw_arms_and_sword(surface, cx, cy, facing, phase, action, arm_lift, attack_progress)
        _NS_obanai._draw_kaburamaru(surface, cx, cy - 14, facing, phase, action)  # Ular di leher
        _NS_obanai._draw_head(surface, cx, cy - 18, facing)

    @staticmethod
    def _draw_legs(surface, cx, cy, facing, phase, action):
        step = int(math.sin(phase) * 6) if action == "walk" else 0
        # Leg 1 (Back)
        pygame.draw.rect(surface, _NS_obanai.PALETTE["darkest"], (cx - 4 - step, cy, 6, 12))
        pygame.draw.rect(surface, _NS_obanai.PALETTE["bandage"], (cx - 4 - step, cy + 6, 6, 4))
        # Leg 2 (Front)
        pygame.draw.rect(surface, _NS_obanai.PALETTE["dark"], (cx + 1 + step, cy, 7, 13))
        pygame.draw.rect(surface, _NS_obanai.PALETTE["bandage"], (cx + 1 + step, cy + 7, 7, 4))

    @staticmethod
    def _draw_torso_and_haori(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.8) * 3

        # Base Uniform
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["dark"], [
            (cx - 7, cy - 12), (cx + 7, cy - 12), (cx + 9, cy + 6), (cx - 9, cy + 6)
        ])

        # Haori (Striped Jacket)
        haori_shape = [
            (cx - 10, cy - 12), (cx - 14 + int(sway), cy + 12),
            (cx - 6 + int(sway), cy + 15), (cx + 8 - int(sway), cy + 15),
            (cx + 12 - int(sway), cy + 12), (cx + 8, cy - 12)
        ]
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["haori_white"], haori_shape)

        # Gambar garis-garis hitam (Stripes)
        for y_off in range(-8, 14, 5):
            x_start = cx - 12 + int(sway * (y_off + 10) / 20)
            x_end = cx + 10 - int(sway * (y_off + 10) / 20)
            _NS_obanai._aaline(surface, _NS_obanai.PALETTE["haori_black"], (x_start, cy + y_off),
                               (x_end, cy + y_off + 2), 3)

    @staticmethod
    def _draw_head(surface, cx, cy, facing):
        # Face base
        head = [
            (cx - 6, cy - 4), (cx - 8, cy - 8), (cx - 5, cy - 12),
            (cx + 5, cy - 12), (cx + 8, cy - 8), (cx + 6, cy - 4),
            (cx + 4, cy + 2), (cx - 4, cy + 2)
        ]
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["skin_dark"], head)
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["skin_mid"], [(x, y - 1) for x, y in head])

        # Bandages over mouth
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["bandage"], [
            (cx - 5, cy - 3), (cx + 5, cy - 3), (cx + 4, cy + 2), (cx - 4, cy + 2)
        ])
        pygame.draw.line(surface, _NS_obanai.PALETTE["haori_shadow"], (cx - 4, cy - 1), (cx + 4, cy - 1), 1)

        # Eye (Kiri Kuning/Teal, Kanan tertutup poni)
        # Kita gambar satu mata yang terlihat jelas berdasarkan arah hadap
        eye_x = cx + facing * 3
        eye_y = cy - 6
        pygame.draw.rect(surface, _NS_obanai.PALETTE["white"], (eye_x - 1, eye_y, 3, 2))
        pygame.draw.rect(surface, (200, 180, 50), (eye_x, eye_y, 1, 2))  # Yellow eye

        # Messy Black Hair (Menutupi sisi wajah)
        hair = [
            (cx - 9, cy - 6), (cx - 10, cy - 12), (cx - 6, cy - 16),
            (cx + 6, cy - 16), (cx + 10, cy - 12), (cx + 9, cy - 5),
            (cx + 6, cy - 10), (cx + 2, cy - 4), (cx - 2, cy - 10), (cx - 6, cy - 4)
        ]
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["darkest"], hair)
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["dark"], [(x, y - 1) for x, y in hair])

    @staticmethod
    def _draw_kaburamaru(surface, cx, cy, facing, phase, action):
        """Ular putih melilit di pundak."""
        bob = math.sin(phase * 1.5) * 2

        # Badan melilit
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["snake_dark"], [
            (cx - 10, cy + 4), (cx - 12, cy + 8), (cx - 5, cy + 12),
            (cx + 5, cy + 12), (cx + 12, cy + 8), (cx + 10, cy + 4)
        ])
        _NS_obanai._poly(surface, _NS_obanai.PALETTE["snake_light"], [
            (cx - 8, cy + 5), (cx - 10, cy + 8), (cx - 4, cy + 10),
            (cx + 4, cy + 10), (cx + 10, cy + 8), (cx + 8, cy + 5)
        ])

        # Kepala ular mengintip dari pundak depan
        head_x = cx + facing * 9
        head_y = cy + 2 + bob
        _NS_obanai._aacircle(surface, _NS_obanai.PALETTE["snake_mid"], (head_x, head_y), 4)
        _NS_obanai._aacircle(surface, _NS_obanai.PALETTE["snake_light"], (head_x, head_y - 1), 3)
        # Mata merah
        pygame.draw.rect(surface, _NS_obanai.PALETTE["snake_eye"], (head_x + facing, head_y - 2, 2, 1))
        # Lidah bercabang kecil
        if action == "attack":
            pygame.draw.line(surface, (200, 50, 100), (head_x + facing * 3, head_y), (head_x + facing * 6, head_y), 1)

    @staticmethod
    def _draw_arms_and_sword(surface, cx, cy, facing, phase, action, arm_lift, attack_progress):
        shoulder_x = cx + facing * 4
        shoulder_y = cy - 8

        extend = 8
        if action == "attack":
            if attack_progress < 0.3:
                extend = 2
            elif attack_progress < 0.6:
                extend = 16
            else:
                extend = 10

        elbow_x = shoulder_x + facing * (extend // 2)
        elbow_y = shoulder_y + 4 - arm_lift // 2
        hand_x = shoulder_x + facing * extend
        hand_y = shoulder_y + 6 - arm_lift

        # Lengan dengan lengan Haori
        _NS_obanai._aaline(surface, _NS_obanai.PALETTE["haori_white"], (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_obanai._aaline(surface, _NS_obanai.PALETTE["haori_black"], (shoulder_x, shoulder_y + 2),
                           (elbow_x, elbow_y + 2), 2)  # Stripe
        _NS_obanai._aaline(surface, _NS_obanai.PALETTE["dark"], (elbow_x, elbow_y), (hand_x, hand_y), 4)

        # Tangan
        _NS_obanai._aacircle(surface, _NS_obanai.PALETTE["skin_mid"], (hand_x, hand_y), 3)

        # Pedang Meliuk (Serpent Sword)
        tip_x = hand_x + facing * (15 if action != "attack" else 25)
        tip_y = hand_y - (15 if action != "attack" else 5 - arm_lift)
        _NS_obanai._draw_serpent_sword(surface, hand_x, hand_y, tip_x, tip_y, phase)

    @staticmethod
    def _draw_serpent_sword(surface, hx, hy, tx, ty, phase):
        """Menggambar pedang dengan mata pisau meliuk/bergelombang."""
        dist = math.hypot(tx - hx, ty - hy)
        angle = math.atan2(ty - hy, tx - hx)

        # Gagang (Tsuka)
        hilt_x = hx - int(math.cos(angle) * 5)
        hilt_y = hy - int(math.sin(angle) * 5)
        pygame.draw.line(surface, (100, 30, 40), (hx, hy), (hilt_x, hilt_y), 3)
        pygame.draw.circle(surface, (200, 180, 50), (hx, hy), 2)  # Tsuba (Guard)

        # Mata Pisau meliuk
        pts = []
        segments = 10
        for i in range(segments + 1):
            t = i / segments
            base_px = hx + (tx - hx) * t
            base_py = hy + (ty - hy) * t

            # Efek liukan menggunakan sinus berlawanan arah dengan sudut
            wave = math.sin(t * math.pi * 3) * 2
            perp_angle = angle + math.pi / 2
            px = base_px + math.cos(perp_angle) * wave
            py = base_py + math.sin(perp_angle) * wave
            pts.append((px, py))

        for i in range(len(pts) - 1):
            width = 2 if i < segments - 2 else 1
            pygame.draw.line(surface, _NS_obanai.PALETTE["blade_dark"], pts[i], pts[i + 1], width + 1)
            pygame.draw.line(surface, _NS_obanai.PALETTE["blade_shine"], pts[i], pts[i + 1], width)

    # ============================================================
    # MELEE ATTACK (BASIC SLASH)
    # ============================================================
    @staticmethod
    def _draw_melee_slash(surface, boss, x, y, progress):
        """Efek tebasan berbentuk meliuk/ular berwarna ungu."""
        if progress < 0.3 or progress > 0.7: return

        facing = boss.direction
        t = (progress - 0.3) / 0.4

        start_angle = -math.pi * 0.7 if facing == 1 else -math.pi * 0.3
        sweep = math.pi * 1.4 * facing
        curr_angle = start_angle + sweep * t

        radius = 50
        pts = []
        steps = 15
        for i in range(steps + 1):
            st = i / steps
            a = start_angle + (curr_angle - start_angle) * st
            # Liukan pada efek tebasan
            wave = math.sin(st * math.pi * 4 - progress * 10) * 5
            r = radius + wave - (1 - math.sin(st * math.pi)) * 10
            px = x + math.cos(a) * r
            py = y - 10 + math.sin(a) * r
            pts.append((px, py))

        if len(pts) > 2:
            # Poly harus convex atau minimal line array. Kita pakai ketebalan garis saja agar liukannya terlihat jelas.
            for w, alpha, col in [(8, 100, "aura_dark"), (4, 200, "aura_mid"), (2, 255, "aura_light"),
                                  (1, 255, "white")]:
                for i in range(len(pts) - 1):
                    color = (*_NS_obanai.PALETTE[col], _NS_obanai._alpha(alpha * (1 - t * 0.5)))
                    _NS_obanai._aaline(surface, color, pts[i], pts[i + 1], w)

    # ============================================================
    # SKILL Q: SERPENTINE SLASH
    # ============================================================
    @staticmethod
    def _draw_skill_q(surface, boss, x, y, timer, phase):
        """Tebasan raksasa berbentuk sabit ungu tebal menyapu ke depan."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress < 0.2: return

        t = (progress - 0.2) / 0.8
        tx, ty = _NS_obanai._target_position(boss, x, y)

        # Posisi proyektil sabit
        cx = x + facing * 30 + (tx - x) * t
        cy = y - 10 + (ty - y + 10) * t

        # Gambar crescent besar
        radius = 45 + int(t * 15)
        pts_outer = []
        pts_inner = []
        steps = 20
        start_a = -math.pi / 2 if facing == 1 else math.pi / 2
        sweep = math.pi * 0.8 * facing

        for i in range(steps + 1):
            st = i / steps
            a = start_a + sweep * st - (math.pi * 0.2 * facing * t)  # Rotasi
            wave = math.sin(st * math.pi * 5 - phase * 5) * 6
            r_out = radius + wave
            r_in = radius - 15 - wave
            pts_outer.append((cx + math.cos(a) * r_out, cy + math.sin(a) * r_out))
            pts_inner.insert(0, (cx + math.cos(a) * r_in, cy + math.sin(a) * r_in))

        poly_pts = pts_outer + pts_inner
        alpha = _NS_obanai._alpha(255 * (1 - t))

        _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["aura_mid"], alpha), poly_pts)
        _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["aura_light"], alpha), poly_pts, 3)
        _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["aura_glow"], alpha), poly_pts, 1)

    # ============================================================
    # SKILL W: COILING SERPENT
    # ============================================================
    @staticmethod
    def _draw_skill_w(surface, boss, x, y, timer, phase):
        """Ular putih memanjang mengikat target."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_obanai._target_position(boss, x, y)

        dist = math.hypot(tx - x, ty - y)
        angle = math.atan2(ty - y, tx - x)

        if progress < 0.4:
            # Ular meluncur
            t = progress / 0.4
            length = dist * t

            pts = []
            segs = 20
            for i in range(segs):
                st = i / segs
                px = x + math.cos(angle) * (length * st)
                py = y - 15 + math.sin(angle) * (length * st)
                wave = math.sin(st * math.pi * 6 - phase * 10) * 15 * st
                perp = angle + math.pi / 2
                pts.append((px + math.cos(perp) * wave, py + math.sin(perp) * wave))

            if len(pts) > 2:
                for i in range(len(pts) - 1):
                    w = int(4 + st * 4)
                    _NS_obanai._aaline(surface, _NS_obanai.PALETTE["snake_dark"], pts[i], pts[i + 1], w + 2)
                    _NS_obanai._aaline(surface, _NS_obanai.PALETTE["snake_light"], pts[i], pts[i + 1], w)

                # Kepala
                head = pts[-1]
                _NS_obanai._aacircle(surface, _NS_obanai.PALETTE["snake_light"], head, 6)
                pygame.draw.rect(surface, _NS_obanai.PALETTE["snake_eye"], (head[0], head[1] - 2, 3, 2))

        else:
            # Ular melilit target
            t = (progress - 0.4) / 0.6
            alpha = _NS_obanai._alpha(255 * (1 - t * 0.8))

            coils = 4
            for i in range(60):
                st = i / 60
                a = st * math.pi * 2 * coils - phase * 5
                r = 15 - st * 5
                cx = tx + math.cos(a) * r
                cy = ty + 10 - st * 30 + math.sin(a) * 5

                s_color = (*_NS_obanai.PALETTE["snake_light"], alpha)
                _NS_obanai._aacircle(surface, s_color, (cx, cy), 4)

    # ============================================================
    # SKILL E: POISON BITE
    # ============================================================
    @staticmethod
    def _draw_skill_e(surface, boss, x, y, timer, phase):
        """Kepala ular raksasa hantu putih menggigit target, racun ungu."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_obanai._target_position(boss, x, y)

        if progress > 0.2 and progress < 0.8:
            t = (progress - 0.2) / 0.6
            alpha = _NS_obanai._alpha(200 * math.sin(t * math.pi))

            # Kepala Ular Hantu Besar dari atas target
            hx = tx
            hy = ty - 40 + int(t * 30)

            # Mulut menganga lalu menutup
            mouth_open = math.sin(t * math.pi) * 20

            # Rahang Atas
            _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["snake_mid"], alpha), [
                (hx - 15, hy), (hx + 15, hy), (hx + 20, hy + 10), (hx, hy + 25), (hx - 20, hy + 10)
            ])
            # Rahang Bawah
            _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["snake_dark"], alpha), [
                (hx - 10, hy + 10 + mouth_open), (hx + 10, hy + 10 + mouth_open),
                (hx, hy + 25 + mouth_open)
            ])

            # Taring & Mata
            _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["white"], alpha),
                             [(hx - 10, hy + 15), (hx - 8, hy + 25), (hx - 6, hy + 15)])
            _NS_obanai._poly(surface, (*_NS_obanai.PALETTE["white"], alpha),
                             [(hx + 10, hy + 15), (hx + 8, hy + 25), (hx + 6, hy + 15)])

            pygame.draw.rect(surface, (*_NS_obanai.PALETTE["snake_eye"], alpha), (hx - 8, hy + 5, 4, 3))
            pygame.draw.rect(surface, (*_NS_obanai.PALETTE["snake_eye"], alpha), (hx + 4, hy + 5, 4, 3))

            # Racun ungu menyebar di bawah
            if t > 0.5:
                pt = (t - 0.5) / 0.5
                pr = int(pt * 40)
                p_alpha = _NS_obanai._alpha(180 * (1 - pt))
                pygame.draw.ellipse(surface, (*_NS_obanai.PALETTE["aura_mid"], p_alpha),
                                    (tx - pr, ty - pr // 3, pr * 2, pr * 2 // 3))

                # Gelembung racun
                for i in range(5):
                    gx = tx + math.cos(i * math.pi * 0.4) * pr * 0.6
                    gy = ty - int(pt * 20) + math.sin(i * math.pi * 0.4) * 10
                    _NS_obanai._aacircle(surface, (*_NS_obanai.PALETTE["aura_light"], p_alpha), (gx, gy), 4)

    # ============================================================
    # SKILL R: SERPENT BREATH
    # ============================================================
    @staticmethod
    def _draw_skill_r(surface, boss, x, y, timer, phase):
        """Banyak kepala ular melesat dalam bentuk cone (kerucut) ke depan."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress < 0.2:
            r = int((progress / 0.2) * 30)
            _NS_obanai._aacircle(surface, (*_NS_obanai.PALETTE["aura_mid"], 150), (x + facing * 20, y), r, 2)
            return

        t = (progress - 0.2) / 0.8
        alpha = _NS_obanai._alpha(255 * (1 - t))
        num_snakes = 5

        for i in range(num_snakes):
            # Sudut menyebar ke depan
            angle_offset = (i - num_snakes // 2) * 0.3
            base_angle = 0 if facing == 1 else math.pi
            angle = base_angle + angle_offset

            length = 150 * t * (0.8 + 0.2 * (i % 2))  # Variasi panjang

            pts = []
            segs = 10
            for j in range(segs + 1):
                st = j / segs
                px = x + math.cos(angle) * (length * st)
                py = y - 10 + math.sin(angle) * (length * st)
                wave = math.sin(st * math.pi * 4 - phase * 8 + i) * 10 * st
                perp = angle + math.pi / 2
                pts.append((px + math.cos(perp) * wave, py + math.sin(perp) * wave))

            if len(pts) > 2:
                for j in range(len(pts) - 1):
                    w = int(3 + st * 5)
                    _NS_obanai._aaline(surface, (*_NS_obanai.PALETTE["aura_mid"], alpha), pts[j], pts[j + 1], w + 4)
                    _NS_obanai._aaline(surface, (*_NS_obanai.PALETTE["snake_light"], alpha), pts[j], pts[j + 1], w)

                head = pts[-1]
                _NS_obanai._aacircle(surface, (*_NS_obanai.PALETTE["snake_light"], alpha), head, 7)
                pygame.draw.rect(surface, (*_NS_obanai.PALETTE["snake_eye"], alpha),
                                 (head[0] + facing * 2, head[1] - 3, 3, 2))

    # ============================================================
    # SKILL D: HIDDEN SERPENT
    # ============================================================
    @staticmethod
    def _draw_skill_d(surface, boss, x, y, timer, phase):
        """Teleportasi bayangan dan tebasan kejutan di target."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_obanai._target_position(boss, x, y)

        # Asap ungu di tempat asli
        if progress < 0.5:
            t = progress / 0.5
            alpha = _NS_obanai._alpha(200 * (1 - t))
            for i in range(10):
                a = i * math.pi * 2 / 10 + phase
                r = t * 40 + random.randint(-5, 5)
                px = x + math.cos(a) * r
                py = y + math.sin(a) * r
                _NS_obanai._aacircle(surface, (*_NS_obanai.PALETTE["aura_darkest"], alpha), (px, py), 15)
                _NS_obanai._aacircle(surface, (*_NS_obanai.PALETTE["aura_mid"], alpha), (px, py), 8)

        # Tebasan X ungu besar di target
        if progress > 0.4:
            t = (progress - 0.4) / 0.6
            alpha = _NS_obanai._alpha(255 * (1 - t))
            size = int(30 + t * 20)

            # Garis X 1
            p1 = (tx - size, ty - size)
            p2 = (tx + size, ty + size)
            _NS_obanai._aaline(surface, (*_NS_obanai.PALETTE["aura_light"], alpha), p1, p2, 5)
            _NS_obanai._aaline(surface, (*_NS_obanai.PALETTE["white"], alpha), p1, p2, 2)

            # Garis X 2
            p3 = (tx - size, ty + size)
            p4 = (tx + size, ty - size)
            _NS_obanai._aaline(surface, (*_NS_obanai.PALETTE["aura_light"], alpha), p3, p4, 5)
            _NS_obanai._aaline(surface, (*_NS_obanai.PALETTE["white"], alpha), p3, p4, 2)

    # ============================================================
    # AMBIENT
    # ============================================================
    @staticmethod
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((80, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 150), (0, 0, 80, 20))
        surface.blit(shadow, (x - 40, y - 10))

    @staticmethod
    def _draw_aura(surface, x, y, phase, max_alpha=255):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((120, 120), pygame.SRCALPHA)
        for r in range(40, 5, -5):
            alpha = _NS_obanai._alpha((40 - r) * 2 * pulse)
            alpha = min(alpha, max_alpha)
            if alpha > 0:
                _NS_obanai._aacircle(aura, (*_NS_obanai.PALETTE["aura_darkest"], alpha), (60, 60), r)
        surface.blit(aura, (x - 60, y - 60))


# ====================================================================================================
# SANGUIRE - MINI BOSS
# ====================================================================================================

class _NS_sanguire:
    """Namespace sanguire - Blood Manipulator inspired mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Coat/robe - deep black with purple sheen
        "coat_darkest": (5, 3, 10),
        "coat_dark": (18, 12, 28),
        "coat_mid": (35, 25, 48),
        "coat_light": (60, 45, 78),
        "coat_edge": (95, 75, 115),

        # Fur trim (spiky shoulder collar)
        "fur_dark": (12, 8, 20),
        "fur_mid": (30, 22, 40),
        "fur_light": (55, 42, 70),
        "fur_edge": (90, 70, 110),

        # Skin (pale)
        "skin_shadow": (110, 85, 90),
        "skin_dark": (170, 135, 130),
        "skin_mid": (215, 180, 170),
        "skin_light": (245, 215, 200),
        "skin_shine": (255, 235, 220),

        # Hair (black-purple)
        "hair_darkest": (5, 3, 12),
        "hair_dark": (18, 12, 28),
        "hair_mid": (40, 28, 55),
        "hair_light": (75, 55, 95),
        "hair_shine": (130, 100, 150),

        # BLOOD MAGIC (magenta-purple - iconic)
        "blood_darkest": (40, 5, 30),
        "blood_dark": (95, 15, 75),
        "blood_mid": (170, 35, 145),
        "blood_light": (230, 80, 200),
        "blood_hot": (255, 130, 235),
        "blood_shine": (255, 200, 250),

        # Deep scarlet (for curtain skill)
        "scarlet_darkest": (35, 2, 8),
        "scarlet_dark": (95, 8, 25),
        "scarlet_mid": (170, 20, 55),
        "scarlet_light": (230, 50, 90),
        "scarlet_hot": (255, 100, 130),

        # Chain metal (dark iron with purple tint)
        "chain_dark": (15, 10, 20),
        "chain_mid": (55, 40, 65),
        "chain_light": (110, 90, 125),
        "chain_shine": (180, 160, 195),

        # Eye (purple glow)
        "eye_white": (240, 235, 245),
        "eye_iris": (95, 45, 130),
        "eye_pupil": (10, 5, 15),
        "eye_glow": (200, 100, 240),

        # Gem/pendant
        "gem_dark": (55, 10, 45),
        "gem_mid": (140, 30, 120),
        "gem_light": (220, 90, 200),
        "gem_shine": (255, 180, 240),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sanguire._clamp(color)
        if _NS_sanguire.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_sanguire._clamp(color)
        if _NS_sanguire.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_sanguire._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_sanguire(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sanguire._detect_moving(boss)
        _NS_sanguire._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_sg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_sanguire._draw_blood_aura(surface, x, y, pulse)
        _NS_sanguire._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_sanguire._draw_blood_prison_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sanguire._draw_blood_rain_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_sanguire._draw_scarlet_curtain_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_sanguire._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_sanguire._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_sanguire._draw_idle_pose(surface, boss, x, y)

        # Foreground FX (over body)
        if active_skill == "q":
            _NS_sanguire._draw_blood_lance(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sanguire._draw_blood_prison_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sanguire._draw_blood_rain_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sanguire._draw_blood_chain(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_sanguire._draw_scarlet_curtain_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sg_previous_timer", 0))
        active = bool(getattr(boss, "_sg_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._sg_attack_active = True
            boss._sg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._sg_attack_frame = int(getattr(boss, "_sg_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._sg_attack_active = False
            boss._sg_attack_frame = 0
            active = False

        boss._sg_previous_timer = timer
        boss._sg_attack_progress = (
            min(1.0, getattr(boss, "_sg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_sg_last_x"):
            boss._sg_last_x = boss.x
            boss._sg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sg_last_x)
        dy = abs(boss.y - boss._sg_last_y)
        boss._sg_last_x = boss.x
        boss._sg_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_sanguire._draw_shadow(surface, x, y + 50)
        _NS_sanguire._draw_blood_droplets(surface, x, y + 20, boss.pulse)
        _NS_sanguire._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                 "idle", 0)

    def _draw_walk_pose(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_sanguire._draw_shadow(surface, x + sway, y + 50)
        _NS_sanguire._draw_blood_droplets(surface, x + sway, y + 20, phase,
                                          trail=True, facing=boss.direction)
        _NS_sanguire._draw_body(surface, x + sway, y + bob, boss.direction, phase,
                                 "walk", 0)

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_sg_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Ranged caster - subtle arm extension forward
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 2)
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-2 + t * 6)) * boss.direction
            lift = int(2 - t * 3)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(4 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)

        _NS_sanguire._draw_shadow(surface, x + lunge, y + 50)
        _NS_sanguire._draw_blood_droplets(surface, x + lunge, y + 20, boss.pulse,
                                          intense=True)
        _NS_sanguire._draw_body(surface, x + lunge, y - lift, boss.direction,
                                 boss.pulse, "attack", progress)

        # Basic ranged attack: blood shard projectile
        _NS_sanguire._draw_blood_shard_projectile(surface, boss, x + lunge,
                                                    y - lift, progress)

    # ============================================================
    # BODY (Humanoid caster with dark coat)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress):
        # Legs
        _NS_sanguire._draw_legs(surface, cx, cy + 20, facing, phase, action,
                                 attack_progress)

        # Long coat (flowing)
        _NS_sanguire._draw_coat(surface, cx, cy, facing, phase, action)

        # Torso
        _NS_sanguire._draw_torso(surface, cx, cy - 4, facing, phase)

        # Fur collar (spiky)
        _NS_sanguire._draw_fur_collar(surface, cx, cy - 8, facing, phase)

        # Back arm
        _NS_sanguire._draw_back_arm(surface, cx, cy - 2, facing, phase, action,
                                      attack_progress)

        # Head with wild hair
        _NS_sanguire._draw_head(surface, cx, cy - 24, facing, phase)

        # Front arm (casting hand with blood magic)
        _NS_sanguire._draw_casting_arm(surface, cx, cy - 2, facing, phase, action,
                                         attack_progress)

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress):
        if action == "walk":
            leg_swing = math.sin(phase * 1.5) * 4
        else:
            leg_swing = 0

        # Back leg
        back_leg_x = cx - 5 + int(-leg_swing * 0.5)
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["shadow_deep"], [
            (back_leg_x - 3, cy + 2),
            (back_leg_x + 3, cy + 2),
            (back_leg_x + 4, cy + 12),
            (back_leg_x - 4, cy + 12),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_darkest"], [
            (back_leg_x - 3, cy),
            (back_leg_x + 3, cy),
            (back_leg_x + 4, cy + 11),
            (back_leg_x - 4, cy + 11),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_dark"], [
            (back_leg_x - 2, cy + 1),
            (back_leg_x + 2, cy + 1),
            (back_leg_x + 3, cy + 10),
            (back_leg_x - 3, cy + 10),
        ])
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["shadow_deep"],
                         (back_leg_x - 4, cy + 10, 8, 3))

        # Front leg
        front_leg_x = cx + 5 + int(leg_swing * 0.5)
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["shadow_deep"], [
            (front_leg_x - 3, cy + 2),
            (front_leg_x + 3, cy + 2),
            (front_leg_x + 4, cy + 12),
            (front_leg_x - 4, cy + 12),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_dark"], [
            (front_leg_x - 3, cy),
            (front_leg_x + 3, cy),
            (front_leg_x + 4, cy + 11),
            (front_leg_x - 4, cy + 11),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_mid"], [
            (front_leg_x - 2, cy + 1),
            (front_leg_x + 2, cy + 1),
            (front_leg_x + 3, cy + 10),
            (front_leg_x - 3, cy + 10),
        ])
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["shadow_deep"],
                         (front_leg_x - 4, cy + 10, 8, 3))

    def _draw_coat(surface, cx, cy, facing, phase, action):
        flow = math.sin(phase * 0.6) * 3

        # Long coat shape (flares heavily at bottom, longer than shihakusho)
        coat_shape = [
            (cx - 11, cy - 8),
            (cx - 13, cy),
            (cx - 15 + int(flow * facing), cy + 12),
            (cx - 18 + int(flow * facing), cy + 24),
            (cx - 14, cy + 26),
            (cx + 14, cy + 26),
            (cx + 18 - int(flow * facing), cy + 24),
            (cx + 15 - int(flow * facing), cy + 12),
            (cx + 13, cy),
            (cx + 11, cy - 8),
        ]
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in coat_shape])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_darkest"], coat_shape)

        # Coat mid tone
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_dark"], [
            (cx - 10, cy - 6),
            (cx - 12, cy),
            (cx - 14 + int(flow * facing), cy + 14),
            (cx - 16 + int(flow * facing), cy + 22),
            (cx - 10, cy + 24),
            (cx + 10, cy + 24),
            (cx + 16 - int(flow * facing), cy + 22),
            (cx + 14 - int(flow * facing), cy + 14),
            (cx + 12, cy),
            (cx + 10, cy - 6),
        ])

        # Highlight on chest
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_mid"], [
            (cx - 7, cy - 4),
            (cx + 7, cy - 4),
            (cx + 9, cy + 6),
            (cx - 9, cy + 6),
        ])

        # Vertical fold lines
        for x_off in (-7, 0, 7):
            pygame.draw.line(surface, _NS_sanguire.PALETTE["coat_darkest"],
                             (cx + x_off, cy + 2),
                             (cx + x_off + int(flow * facing * 0.5), cy + 22), 1)

        # Purple trim along bottom edge (glow)
        for i in range(-14, 15, 3):
            edge_y = cy + 26 + int(math.sin(phase + i * 0.3) * 1)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_dark"],
                             (cx + i, edge_y, 2, 1))

        # PURPLE GEM PENDANT on chest
        gem_x = cx
        gem_y = cy + 2
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_sanguire._alpha(180 * (4 - r) / 4 * gem_pulse)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (gem_x, gem_y), r + 1)
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["gem_dark"], [
            (gem_x, gem_y - 3),
            (gem_x + 2, gem_y),
            (gem_x, gem_y + 3),
            (gem_x - 2, gem_y),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["gem_mid"], [
            (gem_x, gem_y - 2),
            (gem_x + 1, gem_y),
            (gem_x, gem_y + 2),
            (gem_x - 1, gem_y),
        ])
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["gem_shine"],
                         (gem_x, gem_y - 1, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        # Shoulders
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_darkest"], [
            (cx - 12, cy),
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 12, cy),
            (cx + 11, cy + 2),
            (cx - 11, cy + 2),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["coat_dark"], [
            (cx - 11, cy - 1),
            (cx - 9, cy - 3),
            (cx + 9, cy - 3),
            (cx + 11, cy - 1),
        ])

    def _draw_fur_collar(surface, cx, cy, facing, phase):
        """Spiky fur collar around shoulders/neck."""
        # Fur base ring
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["fur_dark"], [
            (cx - 13, cy + 4),
            (cx - 12, cy),
            (cx - 8, cy - 3),
            (cx + 8, cy - 3),
            (cx + 12, cy),
            (cx + 13, cy + 4),
            (cx + 8, cy + 5),
            (cx - 8, cy + 5),
        ])

        # Spiky fur points around collar
        spikes = [
            (-13, 0, -16, -3),
            (-11, -2, -14, -6),
            (-8, -3, -10, -8),
            (-4, -4, -5, -9),
            (0, -4, 0, -10),
            (4, -4, 5, -9),
            (8, -3, 10, -8),
            (11, -2, 14, -6),
            (13, 0, 16, -3),
        ]
        for base_x, base_y, tip_x, tip_y in spikes:
            wave = math.sin(phase * 0.5 + base_x * 0.3) * 1
            actual_tip_y = tip_y + int(wave)

            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["fur_dark"], [
                (cx + base_x - 1, cy + base_y + 1),
                (cx + tip_x, cy + actual_tip_y),
                (cx + base_x + 2, cy + base_y + 1),
            ])
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["fur_mid"], [
                (cx + base_x, cy + base_y),
                (cx + tip_x, cy + actual_tip_y),
                (cx + base_x + 1, cy + base_y),
            ])
            # Highlight tip
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["fur_light"],
                             (cx + tip_x, cy + actual_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["fur_edge"],
                             (cx + tip_x, cy + actual_tip_y, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        # Neck
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["skin_dark"],
                         (cx - 2, cy + 8, 4, 4))
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["skin_mid"],
                         (cx - 2, cy + 8, 3, 3))

        # Head shape (oval)
        head_shape = [
            (cx - 6, cy + 6),
            (cx - 8, cy + 2),
            (cx - 8, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 8, cy - 4),
            (cx + 8, cy + 2),
            (cx + 6, cy + 6),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in head_shape])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["skin_shadow"], head_shape)

        # Face
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["skin_dark"], [
            (cx - 6, cy + 4),
            (cx - 7, cy),
            (cx - 6, cy - 6),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 7, cy - 4),
            (cx + 7, cy + 2),
            (cx + 5, cy + 6),
            (cx - 2, cy + 7),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["skin_mid"], [
            (cx - 5, cy + 2),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 3, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 3),
            (cx - 2, cy + 5),
        ])
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["skin_light"],
                         (cx + 3 * facing, cy - 1, 2, 2))

        # PURPLE GLOWING EYES
        _NS_sanguire._draw_eyes(surface, cx, cy - 2, facing, phase)

        # Serious mouth
        pygame.draw.line(surface, _NS_sanguire.PALETTE["skin_shadow"],
                         (cx - 2, cy + 4), (cx + 2, cy + 4), 1)

        # WILD BLACK-PURPLE HAIR
        _NS_sanguire._draw_hair(surface, cx, cy, facing, phase)

    def _draw_hair(surface, cx, cy, facing, phase):
        """Wild black hair with purple highlights (Chrollo/Juhabach style)."""
        wave = math.sin(phase * 0.4) * 1

        # Hair base
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["hair_darkest"], [
            (cx - 9, cy - 3),
            (cx - 10, cy - 8),
            (cx - 7, cy - 13),
            (cx - 3, cy - 14),
            (cx + 3, cy - 14),
            (cx + 8, cy - 12),
            (cx + 10, cy - 7),
            (cx + 9, cy - 3),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ])
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["hair_dark"], [
            (cx - 8, cy - 4),
            (cx - 9, cy - 8),
            (cx - 6, cy - 12),
            (cx - 2, cy - 13),
            (cx + 3, cy - 13),
            (cx + 7, cy - 11),
            (cx + 9, cy - 6),
            (cx + 8, cy - 4),
        ])

        # Wild spikes (upward + sideways)
        spikes = [
            (-9, -4, -12, -10 + int(wave)),
            (-6, -8, -8, -14 + int(wave)),
            (-3, -12, -4, -18 + int(wave)),
            (0, -13, 1, -19 + int(wave)),
            (3, -12, 5, -17 + int(wave)),
            (6, -10, 9, -14 + int(wave)),
            (9, -6, 12, -10 + int(wave)),
        ]
        for base_x, base_y, tip_x, tip_y in spikes:
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["hair_darkest"], [
                (cx + base_x - 1, cy + base_y),
                (cx + tip_x, cy + tip_y),
                (cx + base_x + 2, cy + base_y),
            ])
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["hair_dark"], [
                (cx + base_x, cy + base_y),
                (cx + tip_x, cy + tip_y),
                (cx + base_x + 1, cy + base_y),
            ])
            # Purple highlight
            mid_x = int((base_x + tip_x) / 2)
            mid_y = int((base_y + tip_y) / 2)
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["hair_mid"], [
                (cx + mid_x, cy + mid_y),
                (cx + tip_x, cy + tip_y),
                (cx + mid_x + 1, cy + mid_y),
            ])
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["hair_light"],
                             (cx + tip_x, cy + tip_y, 1, 1))
            # Purple shine on some tips
            if abs(base_x) < 5:
                pygame.draw.rect(surface, _NS_sanguire.PALETTE["hair_shine"],
                                 (cx + tip_x, cy + tip_y, 1, 1))

        # Bangs over forehead (partial)
        _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["hair_dark"], [
            (cx - 6, cy - 6),
            (cx - 5, cy - 3),
            (cx - 2, cy - 4),
            (cx + 2, cy - 3),
            (cx + 5, cy - 4),
            (cx + 6, cy - 6),
        ])

    def _draw_eyes(surface, cx, cy, facing, phase):
        """Glowing purple eyes."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7

        # Socket shadow
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["skin_shadow"],
                         (cx - 5, cy, 3, 2))
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["skin_shadow"],
                         (cx + 2, cy, 3, 2))

        # Eye white
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["eye_white"],
                         (cx - 4, cy, 2, 2))
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["eye_white"],
                         (cx + 3, cy, 2, 2))

        # Glow behind iris
        for r in range(3, 0, -1):
            alpha = _NS_sanguire._alpha(180 * (3 - r) / 3 * pulse)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (cx - 3, cy + 1), r)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (cx + 3, cy + 1), r)

        # Purple iris
        iris_offset = 0 if facing > 0 else -1
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["eye_iris"],
                         (cx - 4 + iris_offset, cy, 1, 2))
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["eye_iris"],
                         (cx + 3 + iris_offset, cy, 1, 2))

        # Bright pupils
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["eye_glow"],
                         (cx - 4 + iris_offset, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["eye_glow"],
                         (cx + 3 + iris_offset, cy + 1, 1, 1))

        # Eyebrows (calculating/cold)
        pygame.draw.line(surface, _NS_sanguire.PALETTE["hair_darkest"],
                         (cx - 5, cy - 2), (cx - 2, cy - 1), 1)
        pygame.draw.line(surface, _NS_sanguire.PALETTE["hair_darkest"],
                         (cx + 2, cy - 1), (cx + 5, cy - 2), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        arm_x = cx - facing * 9
        arm_y = cy

        # Shoulder
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["coat_darkest"],
                                (arm_x, arm_y - 2), 4)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["coat_dark"],
                                (arm_x, arm_y - 2), 3)

        # Upper arm
        pygame.draw.line(surface, _NS_sanguire.PALETTE["coat_darkest"],
                         (arm_x, arm_y - 1), (arm_x - facing * 2, arm_y + 8), 5)
        pygame.draw.line(surface, _NS_sanguire.PALETTE["coat_dark"],
                         (arm_x, arm_y - 1), (arm_x - facing * 2, arm_y + 8), 3)

        # Hand at side (visible fingers)
        hand_x = arm_x - facing * 2
        hand_y = arm_y + 10
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["skin_shadow"],
                                (hand_x, hand_y), 2)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["skin_dark"],
                                (hand_x, hand_y), 1)

    def _draw_casting_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Casting hand - extended forward with blood magic glow."""
        shoulder_x = cx + facing * 9
        shoulder_y = cy - 2

        # Arm position varies with action
        if action == "attack":
            if attack_progress < 0.4:
                t = attack_progress / 0.4
                arm_angle = math.pi * 0.1 - t * 0.15
                arm_extend = 9 + t * 3
            elif attack_progress < 0.7:
                t = (attack_progress - 0.4) / 0.3
                arm_angle = math.pi * -0.05 + t * 0.05
                arm_extend = 12 + t * 3
            else:
                t = (attack_progress - 0.7) / 0.3
                arm_angle = math.pi * 0 + t * 0.1
                arm_extend = 15 - t * 5
        elif action == "walk":
            arm_angle = math.pi * 0.15 + math.sin(phase * 1.5) * 0.05
            arm_extend = 8
        else:
            # Idle: casting pose
            arm_angle = math.pi * 0.1 + math.sin(phase * 0.5) * 0.05
            arm_extend = 10

        # Hand position (facing forward-ish)
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_extend * facing)
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_extend)

        # Shoulder
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["coat_darkest"],
                                (shoulder_x, shoulder_y), 5)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["coat_dark"],
                                (shoulder_x, shoulder_y), 4)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["coat_mid"],
                                (shoulder_x - 1, shoulder_y - 1), 2)

        # Upper arm to elbow
        elbow_x = int((shoulder_x + hand_x) / 2) + int(facing * 1)
        elbow_y = int((shoulder_y + hand_y) / 2) + 2

        _NS_sanguire._aaline(surface, _NS_sanguire.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 6)
        _NS_sanguire._aaline(surface, _NS_sanguire.PALETTE["coat_darkest"],
                              (shoulder_x, shoulder_y),
                              (elbow_x, elbow_y), 5)
        _NS_sanguire._aaline(surface, _NS_sanguire.PALETTE["coat_dark"],
                              (shoulder_x, shoulder_y),
                              (elbow_x, elbow_y), 4)

        # Forearm to hand
        _NS_sanguire._aaline(surface, _NS_sanguire.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_sanguire._aaline(surface, _NS_sanguire.PALETTE["coat_dark"],
                              (elbow_x, elbow_y),
                              (hand_x, hand_y), 3)

        # Hand (skin - fingers spread for casting)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["skin_shadow"],
                                (hand_x, hand_y), 3)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["skin_mid"],
                         (hand_x - 1, hand_y - 1, 2, 2))

        # Draw fingers extending
        for finger_i in range(3):
            f_angle = arm_angle - 0.3 + finger_i * 0.3
            fx = hand_x + int(math.cos(f_angle) * 3 * facing)
            fy = hand_y + int(math.sin(f_angle) * 3)
            pygame.draw.line(surface, _NS_sanguire.PALETTE["skin_dark"],
                             (hand_x, hand_y), (fx, fy), 1)

        # BLOOD MAGIC GLOW around casting hand
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        glow_size = 5
        if action == "attack":
            glow_size = 5 + int(attack_progress * 4)

        for r in range(glow_size + 3, 0, -1):
            alpha = _NS_sanguire._alpha(180 * (glow_size + 3 - r) / (glow_size + 3) * glow_pulse)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_darkest"], alpha),
                                    (hand_x, hand_y), r)
        for r in range(glow_size, 0, -1):
            alpha = _NS_sanguire._alpha(200 * (glow_size - r) / glow_size * glow_pulse)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                    (hand_x, hand_y), r)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_mid"],
                                (hand_x, hand_y), max(1, glow_size - 2))
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_light"],
                                (hand_x, hand_y), max(1, glow_size - 4))
        pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_shine"],
                         (hand_x, hand_y, 1, 1))

        # Floating blood droplets around hand
        for i in range(4):
            drop_angle = phase * 2 + i * math.pi / 2
            drop_r = 8
            dx = hand_x + int(math.cos(drop_angle) * drop_r)
            dy = hand_y + int(math.sin(drop_angle) * drop_r)
            alpha = _NS_sanguire._alpha(220 * glow_pulse)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                    (dx, dy), 2)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (dx, dy, 1, 1))

    # ============================================================
    # BASIC RANGED ATTACK: Blood Shard Projectile
    # ============================================================
    def _draw_blood_shard_projectile(surface, boss, x, y, progress):
        """Small blood shard projectile."""
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_sanguire._target_position(boss, x, y)

        # Launch from casting hand
        start_x = x + facing * 22
        start_y = y - 2

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Comet trail
        for i in range(7):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_sanguire._alpha(220 - i * 30)
            size = max(1, 6 - i)

            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_darkest"], alpha),
                                    (px, py), size)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (px, py), max(1, size - 2))

        # Shard head
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_darkest"],
                                (bx, by), 6)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_dark"],
                                (bx, by), 4)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_mid"],
                                (bx, by), 3)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_light"],
                                (bx, by), 2)
        _NS_sanguire._aacircle(surface, _NS_sanguire.PALETTE["blood_shine"],
                                (bx, by), 1)

        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(6 + st * 18)
            alpha = _NS_sanguire._alpha(220 * (1 - st))
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                    (tx, ty), radius, 2)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (tx, ty), max(1, radius - 3), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["blood_hot"], alpha),
                                 (ex, ey, 2, 2))

    # ============================================================
    # AMBIENT / DROPLETS
    # ============================================================
    def _draw_blood_droplets(surface, cx, cy, phase, trail=False, facing=1,
                              intense=False):
        """Floating blood droplets around body."""
        strength = 1.5 if intense else 1.0

        num_drops = 8 if intense else 6
        for i in range(num_drops):
            drop_t = (phase * 0.4 + i * 0.15) % 1.0
            angle = i * math.pi * 2 / num_drops + phase * 0.3
            radius = 20 + int(math.sin(phase + i) * 5)
            dx = cx + int(math.cos(angle) * radius)
            dy = cy + int(math.sin(angle) * radius * 0.6) - int(drop_t * 12)

            alpha = _NS_sanguire._alpha(220 * (1 - drop_t) * strength)
            if alpha <= 0:
                continue

            # Teardrop shape (rounded top, pointed bottom)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_darkest"], alpha),
                                    (dx, dy), 3)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                    (dx, dy), 2)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (dx, dy - 1), 1)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (dx, dy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_shine"],
                             (dx, dy - 2, 1, 1))
            # Trailing tail below droplet
            pygame.draw.line(surface,
                             (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                             (dx, dy + 1), (dx, dy + 3), 1)

        # Trail behind if moving
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = _NS_sanguire._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_sanguire._aacircle(surface,
                                        (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                        (sx, sy), max(2, 5 - i))
                _NS_sanguire._aacircle(surface,
                                        (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                        (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["blood_hot"], alpha),
                                 (sx, sy, 1, 1))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 4, 170), (5, 6, 90, 12))
        pygame.draw.ellipse(shadow, (30, 5, 25, 110), (12, 8, 76, 8))
        surface.blit(shadow, (x - 50, y - 12))

    def _draw_blood_aura(surface, x, y, phase):
        """Purple/magenta blood aura."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_sanguire._alpha((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sanguire._aacircle(aura,
                                        (*_NS_sanguire.PALETTE["blood_darkest"], alpha),
                                        (90, 80), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_sanguire._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_sanguire._aacircle(aura,
                                        (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                        (90, 80), radius)
        for radius in range(28, 5, -3):
            alpha = _NS_sanguire._alpha((28 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_sanguire._aacircle(aura,
                                        (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                        (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))

        # Floating blood embers
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 30 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_shine"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_sanguire.PALETTE["blood_darkest"], 200),
                            (5, 14, 130, 22), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_sanguire.PALETTE["blood_dark"], 220),
                            (14, 16, 112, 18), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_sanguire.PALETTE["blood_mid"], 230),
                            (25, 18, 90, 14), 1)

        # Rune marks
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 70 + int(math.cos(angle) * 38)
            y1 = 25 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 25 + int(math.sin(angle) * 10)
            pygame.draw.line(ring,
                             (*_NS_sanguire.PALETTE["blood_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_sanguire.PALETTE["blood_hot"],
                                 _NS_sanguire._alpha(150 * pulse)),
                                (15, 8, 110, 32), 1)
        surface.blit(ring, (x - 70, y - 23))

    # ============================================================
    # SKILL: Q - BLOOD LANCE (piercing projectile)
    # ============================================================
    def _draw_blood_lance(surface, boss, x, y, timer, phase):
        """Long piercing blood spear."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sanguire._target_position(boss, x, y)

        if progress < 0.25:
            # Form lance at hand
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 2

            # Lance forms - elongated shape
            lance_length = int(t * 25)
            perp_dir = math.atan2(ty - hand_y, tx - hand_x)
            end_x = hand_x + int(math.cos(perp_dir) * lance_length)
            end_y = hand_y + int(math.sin(perp_dir) * lance_length)

            # Multiple layers for depth
            for width, color in [
                (6, _NS_sanguire.PALETTE["blood_darkest"]),
                (4, _NS_sanguire.PALETTE["blood_dark"]),
                (2, _NS_sanguire.PALETTE["blood_mid"]),
                (1, _NS_sanguire.PALETTE["blood_hot"]),
            ]:
                pygame.draw.line(surface, color, (hand_x, hand_y), (end_x, end_y),
                                 width)

            # Sparkles around forming lance
            for i in range(5):
                sp_angle = phase * 3 + i * math.pi / 2.5
                sp_r = 8
                sx = hand_x + int(math.cos(sp_angle) * sp_r)
                sy = hand_y + int(math.sin(sp_angle) * sp_r)
                pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_shine"],
                                 (sx, sy, 2, 2))
        else:
            # Launch lance - long piercing shape traveling
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 22
            start_y = y - 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Lance direction
            direction = math.atan2(ty - start_y, tx - start_x)
            lance_length = 30

            # Lance head position
            head_x = bx
            head_y = by
            tail_x = bx - int(math.cos(direction) * lance_length)
            tail_y = by - int(math.sin(direction) * lance_length)

            # Perpendicular for lance width
            perp_x = -math.sin(direction)
            perp_y = math.cos(direction)

            # Lance shape (elongated diamond)
            lance_width = 6
            mid_x = (head_x + tail_x) / 2
            mid_y = (head_y + tail_y) / 2

            lance_pts = [
                (head_x, head_y),  # tip
                (int(mid_x + perp_x * lance_width),
                 int(mid_y + perp_y * lance_width)),
                (tail_x, tail_y),  # tail
                (int(mid_x - perp_x * lance_width),
                 int(mid_y - perp_y * lance_width)),
            ]

            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["blood_darkest"],
                                lance_pts)

            # Inner lance
            inner_pts = [
                (head_x, head_y),
                (int(mid_x + perp_x * (lance_width - 2)),
                 int(mid_y + perp_y * (lance_width - 2))),
                (tail_x, tail_y),
                (int(mid_x - perp_x * (lance_width - 2)),
                 int(mid_y - perp_y * (lance_width - 2))),
            ]
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["blood_dark"],
                                inner_pts)

            # Central bright line
            pygame.draw.line(surface, _NS_sanguire.PALETTE["blood_mid"],
                             (head_x, head_y), (tail_x, tail_y), 2)
            pygame.draw.line(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (head_x, head_y), (tail_x, tail_y), 1)

            # Bright tip
            for r in range(5, 0, -1):
                alpha = _NS_sanguire._alpha(200 * (5 - r) / 5)
                _NS_sanguire._aacircle(surface,
                                        (*_NS_sanguire.PALETTE["blood_light"], alpha),
                                        (head_x, head_y), r)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_shine"],
                             (head_x, head_y, 2, 2))
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["white"],
                             (head_x, head_y, 1, 1))

            # Trailing droplets
            for i in range(5):
                trail_t = t - i * 0.05
                if trail_t < 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_sanguire._alpha(160 - i * 25)
                _NS_sanguire._aacircle(surface,
                                        (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                        (px, py), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["blood_hot"], alpha),
                                 (px, py, 1, 1))

            # Impact spike burst
            if t > 0.85:
                st = (t - 0.85) / 0.15
                # Spike burst - lines outward from target
                for i in range(10):
                    angle_s = i * math.pi / 5
                    burst_len = int(15 + st * 20)
                    ex = tx + int(math.cos(angle_s) * burst_len)
                    ey = ty + int(math.sin(angle_s) * burst_len)
                    alpha = _NS_sanguire._alpha(240 * (1 - st))
                    pygame.draw.line(surface,
                                     (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                     (tx, ty), (ex, ey), 3)
                    pygame.draw.line(surface,
                                     (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.line(surface,
                                     (*_NS_sanguire.PALETTE["blood_hot"], alpha),
                                     (tx, ty), (ex, ey), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_sanguire.PALETTE["blood_shine"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - BLOOD PRISON (chain cage around target)
    # ============================================================
    def _draw_blood_prison_ground(surface, boss, x, y, timer, phase):
        """Ground circle marking prison location."""
        tx, ty = _NS_sanguire._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(35 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_darkest"], 200),
                                 (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_dark"], 180),
                                 (tx - r + 3, ty - r // 3 + 2,
                                  r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_mid"], 100),
                                 (tx - r + 8, ty - r // 3 + 4,
                                  r * 2 - 16, r * 2 // 3 - 8))

    def _draw_blood_prison_foreground(surface, boss, x, y, timer, phase):
        """Cage of blood chains around target."""
        tx, ty = _NS_sanguire._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        cage_r = 28
        cage_h = 40
        rotation = phase * 0.3

        # Vertical chain bars around cage (like prison bars)
        num_bars = 8
        for i in range(num_bars):
            bar_angle = i * math.pi * 2 / num_bars + rotation
            bar_x = tx + int(math.cos(bar_angle) * cage_r)
            bar_top_y = ty - cage_h + int(math.sin(bar_angle) * cage_r * 0.4)
            bar_bot_y = ty + int(math.sin(bar_angle) * cage_r * 0.4)

            # Fade based on progress
            alpha_bar = _NS_sanguire._alpha(230 * min(1.0, progress * 2))

            # Chain link segments
            num_links = 8
            for link in range(num_links):
                link_t = link / num_links
                link_y = int(bar_top_y + (bar_bot_y - bar_top_y) * link_t)

                # Alternating chain link orientation
                if link % 2 == 0:
                    # Horizontal oval
                    pygame.draw.ellipse(surface,
                                         (*_NS_sanguire.PALETTE["chain_dark"], alpha_bar),
                                         (bar_x - 3, link_y - 2, 6, 4), 1)
                    pygame.draw.ellipse(surface,
                                         (*_NS_sanguire.PALETTE["chain_mid"], alpha_bar),
                                         (bar_x - 2, link_y - 1, 4, 2), 1)
                else:
                    # Vertical oval
                    pygame.draw.ellipse(surface,
                                         (*_NS_sanguire.PALETTE["chain_dark"], alpha_bar),
                                         (bar_x - 2, link_y - 3, 4, 6), 1)
                    pygame.draw.ellipse(surface,
                                         (*_NS_sanguire.PALETTE["chain_mid"], alpha_bar),
                                         (bar_x - 1, link_y - 2, 2, 4), 1)
                    # Highlight on chain
                    pygame.draw.rect(surface,
                                     (*_NS_sanguire.PALETTE["chain_shine"], alpha_bar),
                                     (bar_x, link_y - 1, 1, 1))

        # Top and bottom rings of prison
        for ring_y_off in [-cage_h, 0]:
            ring_y = ty + ring_y_off
            # Draw ellipse
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_dark"],
                                  _NS_sanguire._alpha(220 * min(1.0, progress * 2))),
                                 (tx - cage_r, ring_y - cage_r // 3 - 2,
                                  cage_r * 2, cage_r * 2 // 3 + 4), 2)
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_mid"],
                                  _NS_sanguire._alpha(220 * min(1.0, progress * 2))),
                                 (tx - cage_r + 2, ring_y - cage_r // 3,
                                  cage_r * 2 - 4, cage_r * 2 // 3), 1)

        # Blood energy pulsing inside cage
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            r_in = int(cage_r * 0.5)
            ix = tx + int(math.cos(angle) * r_in)
            iy = ty - int(cage_h * 0.4) + int(math.sin(angle) * r_in * 0.4)
            alpha = _NS_sanguire._alpha(180 * pulse)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                                    (ix, iy), 3)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                                    (ix, iy), 2)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (ix, iy, 1, 1))

        # Chain from boss to cage (link)
        boss_hand_x = x + boss.direction * 22
        boss_hand_y = y - 2
        chain_pts = [(boss_hand_x, boss_hand_y)]
        num_chain_segs = 6
        for i in range(1, num_chain_segs + 1):
            t = i / num_chain_segs
            cx_seg = int(boss_hand_x + (tx - boss_hand_x) * t)
            cy_seg = int(boss_hand_y + (ty - boss_hand_y) * t)
            wave = math.sin(phase * 2 + t * 3) * 3
            cy_seg += int(wave)
            chain_pts.append((cx_seg, cy_seg))

        for i in range(len(chain_pts) - 1):
            alpha_c = _NS_sanguire._alpha(200 * min(1.0, progress * 2))
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["chain_dark"], alpha_c),
                                    chain_pts[i], 3)
            pygame.draw.line(surface,
                             (*_NS_sanguire.PALETTE["chain_mid"], alpha_c),
                             chain_pts[i], chain_pts[i + 1], 2)

    # ============================================================
    # SKILL: E - BLOOD RAIN (droplets falling from sky)
    # ============================================================
    def _draw_blood_rain_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_sanguire._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_darkest"], 180),
                                 (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_dark"], 150),
                                 (tx - r + 3, ty - r // 3 + 2,
                                  r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_mid"], 100),
                                 (tx - r + 8, ty - r // 3 + 4,
                                  r * 2 - 16, r * 2 // 3 - 8))

    def _draw_blood_rain_foreground(surface, boss, x, y, timer, phase):
        """Falling blood droplets in target area."""
        tx, ty = _NS_sanguire._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = 60

        # Rain droplets falling
        num_drops = 20
        for i in range(num_drops):
            # Random position within area (deterministic based on i and phase)
            drop_x = tx + int(math.cos(i * 1.7 + phase * 0.2) * r * 0.9)
            drop_offset_x = int(math.sin(i * 2.3) * r * 0.5)
            drop_start_x = tx + drop_offset_x

            # Falling animation
            fall_t = (phase * 1.2 + i * 0.11) % 1.0
            fall_start_y = ty - 60
            fall_end_y = ty - int(math.sin(i * 3.1) * 6)  # slight variance for ground

            drop_y = int(fall_start_y + (fall_end_y - fall_start_y) * fall_t)

            alpha = _NS_sanguire._alpha(240 * min(1.0, progress * 2))
            if fall_t > 0.9:
                alpha = int(alpha * (1 - (fall_t - 0.9) * 10))

            # Elongated droplet (motion blur)
            drop_len = 6
            pygame.draw.line(surface,
                             (*_NS_sanguire.PALETTE["blood_darkest"], alpha),
                             (drop_start_x, drop_y - drop_len),
                             (drop_start_x, drop_y), 3)
            pygame.draw.line(surface,
                             (*_NS_sanguire.PALETTE["blood_dark"], alpha),
                             (drop_start_x, drop_y - drop_len),
                             (drop_start_x, drop_y), 2)
            pygame.draw.line(surface,
                             (*_NS_sanguire.PALETTE["blood_mid"], alpha),
                             (drop_start_x, drop_y - drop_len // 2),
                             (drop_start_x, drop_y), 1)
            # Bright tip
            pygame.draw.rect(surface,
                             (*_NS_sanguire.PALETTE["blood_hot"], alpha),
                             (drop_start_x, drop_y, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_sanguire.PALETTE["blood_shine"], alpha),
                             (drop_start_x, drop_y - 1, 1, 1))

            # Splash on ground when about to hit
            if fall_t > 0.85 and fall_t < 0.95:
                splash_alpha = _NS_sanguire._alpha(200)
                for s in range(3):
                    sp_angle = s * math.pi / 1.5
                    spx = drop_start_x + int(math.cos(sp_angle) * 3)
                    spy = fall_end_y + int(math.sin(sp_angle) * 1)
                    pygame.draw.rect(surface,
                                     (*_NS_sanguire.PALETTE["blood_hot"], splash_alpha),
                                     (spx, spy, 1, 1))

        # Small pool spots on ground
        for i in range(8):
            pool_angle = i * math.pi / 4 + phase * 0.1
            pool_r = int(r * 0.7)
            px = tx + int(math.cos(pool_angle) * pool_r)
            py = ty + int(math.sin(pool_angle) * pool_r * 0.4)
            alpha_pool = _NS_sanguire._alpha(200 * min(1.0, progress * 2))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["blood_dark"], alpha_pool),
                                 (px - 3, py - 1, 6, 3))
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_mid"],
                             (px - 1, py, 3, 1))

    # ============================================================
    # SKILL: R - BLOOD CHAIN (grab and pull)
    # ============================================================
    def _draw_blood_chain(surface, boss, x, y, timer, phase):
        """Chain flies toward target and pulls."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sanguire._target_position(boss, x, y)

        start_x = x + facing * 22
        start_y = y - 2

        if progress < 0.5:
            # Chain flies out toward target
            t = progress / 0.5
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)

            # Draw chain segments from boss to end point
            num_segs = 10
            prev = (start_x, start_y)
            for i in range(1, num_segs + 1):
                seg_t = i / num_segs
                sx = int(start_x + (end_x - start_x) * seg_t)
                sy = int(start_y + (end_y - start_y) * seg_t)
                wave = math.sin(phase * 3 + seg_t * 4) * 2
                sy += int(wave)

                # Chain link (alternating orientation)
                if i % 2 == 0:
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_dark"],
                                         (sx - 3, sy - 2, 6, 4), 1)
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_mid"],
                                         (sx - 2, sy - 1, 4, 2), 1)
                else:
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_dark"],
                                         (sx - 2, sy - 3, 4, 6), 1)
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_mid"],
                                         (sx - 1, sy - 2, 2, 4), 1)
                pygame.draw.rect(surface,
                                 _NS_sanguire.PALETTE["chain_shine"],
                                 (sx, sy - 1, 1, 1))
                prev = (sx, sy)

            # Chain head - spike/hook
            head_len = 8
            angle = math.atan2(end_y - start_y, end_x - start_x)
            spike_tip_x = end_x + int(math.cos(angle) * head_len)
            spike_tip_y = end_y + int(math.sin(angle) * head_len)

            perp_x = -math.sin(angle)
            perp_y = math.cos(angle)

            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["chain_dark"], [
                (spike_tip_x, spike_tip_y),
                (end_x + int(perp_x * 3), end_y + int(perp_y * 3)),
                (end_x - int(perp_x * 3), end_y - int(perp_y * 3)),
            ])
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["blood_dark"], [
                (spike_tip_x, spike_tip_y),
                (end_x + int(perp_x * 2), end_y + int(perp_y * 2)),
                (end_x - int(perp_x * 2), end_y - int(perp_y * 2)),
            ])
            _NS_sanguire._poly(surface, _NS_sanguire.PALETTE["blood_mid"], [
                (spike_tip_x, spike_tip_y),
                (end_x + int(perp_x * 1), end_y + int(perp_y * 1)),
                (end_x - int(perp_x * 1), end_y - int(perp_y * 1)),
            ])

            # Bright tip
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (spike_tip_x, spike_tip_y, 2, 2))
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_shine"],
                             (spike_tip_x, spike_tip_y, 1, 1))
        else:
            # Chain hooked - pulling animation (tension pulses)
            t = (progress - 0.5) / 0.5
            end_x = tx
            end_y = ty

            # Chain taught with pulse
            pulse = math.sin(phase * 5) * 2

            num_segs = 12
            for i in range(1, num_segs + 1):
                seg_t = i / num_segs
                sx = int(start_x + (end_x - start_x) * seg_t)
                sy = int(start_y + (end_y - start_y) * seg_t)
                # Slight tension wave
                wave = math.sin(phase * 6 + seg_t * 5) * (1 + pulse * 0.5)
                sy += int(wave)

                if i % 2 == 0:
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_dark"],
                                         (sx - 3, sy - 2, 6, 4), 1)
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_mid"],
                                         (sx - 2, sy - 1, 4, 2), 1)
                else:
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_dark"],
                                         (sx - 2, sy - 3, 4, 6), 1)
                    pygame.draw.ellipse(surface,
                                         _NS_sanguire.PALETTE["chain_mid"],
                                         (sx - 1, sy - 2, 2, 4), 1)
                # Blood energy flowing along chain
                if int(phase * 5 + i) % 3 == 0:
                    pygame.draw.rect(surface,
                                     _NS_sanguire.PALETTE["blood_hot"],
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface,
                                     _NS_sanguire.PALETTE["blood_shine"],
                                     (sx, sy, 1, 1))

            # Hook stuck in target with blood spurt
            _NS_sanguire._aacircle(surface,
                                    _NS_sanguire.PALETTE["blood_darkest"],
                                    (end_x, end_y), 6)
            _NS_sanguire._aacircle(surface,
                                    _NS_sanguire.PALETTE["blood_dark"],
                                    (end_x, end_y), 4)
            _NS_sanguire._aacircle(surface,
                                    _NS_sanguire.PALETTE["blood_mid"],
                                    (end_x, end_y), 2)

            # Blood spurt around impact
            for i in range(8):
                sp_angle = i * math.pi / 4 + phase * 0.5
                sp_r = 8 + int(math.sin(phase * 4 + i) * 3)
                spx = end_x + int(math.cos(sp_angle) * sp_r)
                spy = end_y + int(math.sin(sp_angle) * sp_r)
                alpha = _NS_sanguire._alpha(220)
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["blood_hot"], alpha),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["blood_shine"], alpha),
                                 (spx, spy, 1, 1))

    # ============================================================
    # SKILL: D - SCARLET CURTAIN (large screen barrier)
    # ============================================================
    def _draw_scarlet_curtain_ground(surface, boss, x, y, timer, phase):
        """Ground marking of curtain area."""
        facing = boss.direction
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wide rectangular area in front of boss
        curtain_x = x + facing * 60
        curtain_y = y + 40
        width = int(120 * min(1.0, progress * 2))
        height = 12

        if width > 5:
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["scarlet_darkest"], 200),
                                 (curtain_x - width // 2, curtain_y - height // 2,
                                  width, height))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["scarlet_dark"], 180),
                                 (curtain_x - width // 2 + 3,
                                  curtain_y - height // 2 + 1,
                                  width - 6, height - 2))
            pygame.draw.ellipse(surface,
                                 (*_NS_sanguire.PALETTE["scarlet_mid"], 130),
                                 (curtain_x - width // 2 + 8,
                                  curtain_y - height // 2 + 3,
                                  width - 16, height - 6))

    def _draw_scarlet_curtain_foreground(surface, boss, x, y, timer, phase):
        """Massive vertical curtain of blood."""
        facing = boss.direction
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))

        curtain_x = x + facing * 60
        curtain_ground_y = y + 40

        # Curtain rises up and drapes
        max_height = 80
        rise_t = min(1.0, progress * 2.5)
        current_height = int(max_height * rise_t)
        curtain_top_y = curtain_ground_y - current_height

        curtain_width = 130

        # Draw curtain as multiple vertical strips (like fabric folds)
        num_strips = 12
        for strip_i in range(num_strips):
            strip_t = strip_i / num_strips
            strip_x = int(curtain_x - curtain_width // 2 + strip_t * curtain_width)

            # Wave motion for fabric-like effect
            wave = math.sin(phase * 1.5 + strip_t * 5) * 3
            wave_top = math.sin(phase * 1.2 + strip_t * 4) * 2

            strip_top_x = strip_x + int(wave_top)
            strip_bot_x = strip_x + int(wave)

            alpha = _NS_sanguire._alpha(220)
            # Strip shape (tapered slightly)
            strip_shape = [
                (strip_top_x - 1, curtain_top_y),
                (strip_top_x + 6, curtain_top_y),
                (strip_bot_x + 8, curtain_ground_y),
                (strip_bot_x, curtain_ground_y),
            ]
            _NS_sanguire._poly(surface,
                                (*_NS_sanguire.PALETTE["scarlet_darkest"], alpha),
                                strip_shape)

            # Inner darker
            inner_shape = [
                (strip_top_x, curtain_top_y + 2),
                (strip_top_x + 5, curtain_top_y + 2),
                (strip_bot_x + 7, curtain_ground_y - 2),
                (strip_bot_x + 1, curtain_ground_y - 2),
            ]
            _NS_sanguire._poly(surface,
                                (*_NS_sanguire.PALETTE["scarlet_dark"], alpha),
                                inner_shape)

            # Highlight strip (middle brighter)
            for h in range(0, current_height, 8):
                y_h = curtain_top_y + h
                pygame.draw.line(surface,
                                 (*_NS_sanguire.PALETTE["scarlet_mid"], alpha),
                                 (strip_top_x + 3, y_h),
                                 (strip_top_x + 4 + int(wave * 0.5), y_h + 4), 1)

            # Sparkle at top edge
            if strip_i % 2 == 0:
                sparkle_alpha = _NS_sanguire._alpha(220 * (math.sin(phase * 2 + strip_i) * 0.5 + 0.5))
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["scarlet_hot"], sparkle_alpha),
                                 (strip_top_x + 2, curtain_top_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_sanguire.PALETTE["blood_shine"], sparkle_alpha),
                                 (strip_top_x + 2, curtain_top_y - 1, 1, 1))

        # Blood dripping from bottom
        for i in range(15):
            drip_x = curtain_x - curtain_width // 2 + int(i * curtain_width / 15)
            drip_t = (phase * 0.8 + i * 0.13) % 1.0
            drip_y = curtain_ground_y + int(drip_t * 15)
            alpha_drip = _NS_sanguire._alpha(200 * (1 - drip_t))
            pygame.draw.line(surface,
                             (*_NS_sanguire.PALETTE["scarlet_dark"], alpha_drip),
                             (drip_x, curtain_ground_y),
                             (drip_x, drip_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_sanguire.PALETTE["scarlet_hot"], alpha_drip),
                             (drip_x, drip_y, 1, 1))

        # Top ripple effect
        for i in range(8):
            ripple_angle = i * math.pi / 4 + phase * 0.5
            rx = curtain_x + int(math.cos(ripple_angle) * curtain_width // 3)
            ry = curtain_top_y + int(math.sin(ripple_angle) * 4)
            alpha_r = _NS_sanguire._alpha(180)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha_r),
                                    (rx, ry), 3)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["scarlet_mid"], alpha_r),
                                    (rx, ry), 2)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["scarlet_hot"],
                             (rx, ry, 1, 1))

        # Boss's arms raised (implied) - blood connects to curtain top
        boss_hand_x = x + facing * 22
        boss_hand_y = y - 4
        for i in range(5):
            connect_t = i / 5
            cx_con = int(boss_hand_x + (curtain_x - boss_hand_x) * connect_t)
            cy_con = int(boss_hand_y + (curtain_top_y - boss_hand_y) * connect_t)
            alpha_con = _NS_sanguire._alpha(180)
            _NS_sanguire._aacircle(surface,
                                    (*_NS_sanguire.PALETTE["blood_dark"], alpha_con),
                                    (cx_con, cy_con), 2)
            pygame.draw.rect(surface, _NS_sanguire.PALETTE["blood_hot"],
                             (cx_con, cy_con, 1, 1))


# ====================================================================================================
# SASORI - MINI BOSS
# ====================================================================================================

class _NS_sasori:
    """Namespace sasori - Akasuna no Sasori."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        "hair_darkest": (60, 15, 10),
        "hair_dark": (110, 30, 20),
        "hair_mid": (170, 55, 35),
        "hair_light": (220, 90, 55),
        "hair_shine": (250, 140, 90),

        "skin_darkest": (90, 65, 50),
        "skin_dark": (150, 115, 90),
        "skin_mid": (200, 165, 135),
        "skin_light": (235, 205, 175),
        "skin_shine": (250, 230, 210),

        "cloak_darkest": (5, 5, 8),
        "cloak_dark": (20, 18, 25),
        "cloak_mid": (45, 40, 55),
        "cloak_light": (75, 65, 85),
        "cloud_dark": (100, 15, 15),
        "cloud_mid": (170, 30, 30),
        "cloud_light": (220, 60, 60),
        "cloud_edge": (255, 200, 200),

        "wood_darkest": (30, 20, 12),
        "wood_dark": (65, 45, 25),
        "wood_mid": (115, 85, 50),
        "wood_light": (170, 135, 90),
        "wood_shine": (215, 185, 140),

        "iron_darkest": (10, 8, 12),
        "iron_dark": (35, 30, 40),
        "iron_mid": (75, 65, 80),
        "iron_light": (135, 125, 145),
        "iron_shine": (200, 195, 210),

        "blade_dark": (60, 60, 70),
        "blade_mid": (140, 140, 155),
        "blade_light": (210, 210, 220),
        "blade_shine": (255, 255, 255),

        "string_darkest": (60, 5, 10),
        "string_dark": (140, 15, 20),
        "string_mid": (220, 30, 40),
        "string_light": (255, 80, 90),
        "string_glow": (255, 180, 180),

        "aura_darkest": (15, 5, 25),
        "aura_dark": (45, 20, 70),
        "aura_mid": (90, 45, 130),
        "aura_light": (160, 100, 210),
        "aura_glow": (220, 180, 255),

        "eye_socket": (5, 3, 3),
        "eye_dark": (30, 20, 15),
        "eye_mid": (80, 55, 40),
        "eye_light": (140, 110, 85),
        "eye_shine": (200, 180, 160),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sasori._clamp(color)
        if _NS_sasori.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_sasori._clamp(color)
        if _NS_sasori.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points, width=0):
        pygame.draw.polygon(surface, _NS_sasori._clamp(color), points, width)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_sasori(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sasori._detect_moving(boss)

        # Update state attack
        _NS_sasori._update_sasori_attack_anim(boss)
        attacking = getattr(boss, "_sasori_attack_active", False)

        _NS_sasori._draw_akatsuki_aura(surface, x, y, pulse)
        _NS_sasori._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Ground FX
        if active_skill == "e":
            _NS_sasori._draw_puppet_horde_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sasori._draw_hiruko_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_sasori._draw_sasori_attack(surface, boss, x, y)
        elif moving:
            _NS_sasori._draw_sasori_walk(surface, boss, x, y)
        else:
            _NS_sasori._draw_sasori_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_sasori._draw_iron_sand_kunai(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sasori._draw_third_kazekage(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sasori._draw_puppet_horde_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sasori._draw_hiruko_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE (Telah diperbaiki agar trigger bekerja)
    # ============================================================
    def _update_sasori_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))

        # Menerima trigger dari file test
        if getattr(boss, "trigger_attack", False):
            boss._sasori_attack_active = True
            boss._sasori_attack_frame = 0
            boss.trigger_attack = False

        active = getattr(boss, "_sasori_attack_active", False)

        if active:
            boss._sasori_attack_frame = getattr(boss, "_sasori_attack_frame", 0) + 1
            if boss._sasori_attack_frame >= cooldown:
                boss._sasori_attack_active = False
                boss._sasori_attack_frame = 0
                active = False

        boss._sasori_attack_progress = (
            min(1.0, getattr(boss, "_sasori_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_sasori_last_x"):
            boss._sasori_last_x = boss.x
            boss._sasori_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sasori_last_x)
        dy = abs(boss.y - boss._sasori_last_y)
        boss._sasori_last_x = boss.x
        boss._sasori_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_sasori_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_sasori._draw_shadow(surface, x, y + 50)
        _NS_sasori._draw_akatsuki_mist(surface, x, y + 34, boss.pulse)
        _NS_sasori._draw_sasori_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle")

    def _draw_sasori_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_sasori._draw_shadow(surface, x + sway, y + 50)
        _NS_sasori._draw_akatsuki_mist(surface, x + sway, y + 34, phase,
                                       trail=True, facing=boss.direction)
        _NS_sasori._draw_sasori_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk")

    def _draw_sasori_attack(surface, boss, x, y):
        progress = getattr(boss, "_sasori_attack_progress", 0.0)

        # Cek Jarak Target
        tx, ty = _NS_sasori._target_position(boss, x, y)
        dist = math.hypot(tx - x, ty - y)
        is_melee = dist < 120  # Jika jarak < 120px, maka Melee Swing

        # Cast animation: raise hands, release strings
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-3 + t * 8)) * boss.direction
            lift = int(3 - t * 4)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(5 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)

        _NS_sasori._draw_shadow(surface, x + lunge, y + 50)
        _NS_sasori._draw_akatsuki_mist(surface, x + lunge, y + 34, boss.pulse, intense=True)
        _NS_sasori._draw_sasori_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)

        # Panggil efek animasi tergantung jarak
        if is_melee:
            _NS_sasori._draw_melee_swing(surface, boss, x + lunge, y - lift, progress)
        else:
            _NS_sasori._draw_kunai_projectile(surface, boss, x + lunge, y - lift, progress)

    # ============================================================
    # EFEK MELEE SWING (CHAKRA ARC)
    # ============================================================
    def _draw_melee_swing(surface, boss, x, y, progress):
        """Tebasan busur chakra merah untuk serangan jarak dekat."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        hand_x = x + facing * 20
        hand_y = y - 4

        t = (progress - 0.35) / 0.40
        start_angle = -math.pi * 0.6 if facing == 1 else -math.pi * 0.4
        sweep = math.pi * 1.2 * facing
        current_angle = start_angle + sweep * t

        radius = 45

        # Permukaan untuk gambar busur (Crescent slash)
        arc_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        cx, cy = 60, 60
        pts = [(cx, cy)]
        steps = 15

        for i in range(steps + 1):
            st = i / steps
            a = start_angle + (current_angle - start_angle) * st
            r = radius - (1 - math.sin(st * math.pi)) * 12
            pts.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))

        if len(pts) > 2:
            _NS_sasori._poly(arc_surf, (*_NS_sasori.PALETTE["string_darkest"], 150), pts)

            # Layer lebih terang
            pts_inner = [(cx, cy)]
            for i in range(steps + 1):
                st = i / steps
                a = start_angle + (current_angle - start_angle) * st
                r = (radius - 5) - (1 - math.sin(st * math.pi)) * 8
                pts_inner.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
            _NS_sasori._poly(arc_surf, (*_NS_sasori.PALETTE["string_light"], 220), pts_inner)
            _NS_sasori._poly(arc_surf, (*_NS_sasori.PALETTE["string_glow"], 255), pts_inner, 2)

        surface.blit(arc_surf, (hand_x - cx, hand_y - cy))

        # Partikel terang di ujung tebasan
        tip_x = hand_x + int(math.cos(current_angle) * radius)
        tip_y = hand_y + int(math.sin(current_angle) * radius)
        pygame.draw.rect(surface, _NS_sasori.PALETTE["white"], (tip_x, tip_y, 2, 2))
        _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["string_glow"], (tip_x, tip_y), 4, 1)
    # ============================================================
    # PROJECTILE (RANGED ATTACK)
    # ============================================================
    def _draw_kunai_projectile(surface, boss, x, y, progress):
        """Single kunai flying to target."""
        if progress < 0.4:
            return

        facing = boss.direction
        tx, ty = _NS_sasori._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 4

        t = (progress - 0.4) / 0.6
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail
        for i in range(5):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_sasori._alpha(200 - i * 35)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_dark"], alpha),
                                 (px, py), max(1, 3 - i // 2))

        # Kunai shape
        angle = math.atan2(ty - start_y, tx - start_x)
        tip_x = bx + int(math.cos(angle) * 5)
        tip_y = by + int(math.sin(angle) * 5)
        back_x = bx - int(math.cos(angle) * 4)
        back_y = by - int(math.sin(angle) * 4)
        perp = angle + math.pi / 2
        wing_a = (bx + int(math.cos(perp) * 2), by + int(math.sin(perp) * 2))
        wing_b = (bx - int(math.cos(perp) * 2), by - int(math.sin(perp) * 2))

        _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1), (wing_a[0] + 1, wing_a[1] + 1),
            (back_x + 1, back_y + 1), (wing_b[0] + 1, wing_b[1] + 1),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["blade_dark"],
                         [(tip_x, tip_y), wing_a, (back_x, back_y), wing_b])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["blade_mid"], [
            (tip_x, tip_y),
            (int((tip_x + wing_a[0]) / 2), int((tip_y + wing_a[1]) / 2)),
            (bx, by),
            (int((tip_x + wing_b[0]) / 2), int((tip_y + wing_b[1]) / 2)),
        ])
        pygame.draw.rect(surface, _NS_sasori.PALETTE["blade_shine"],
                         (tip_x, tip_y, 1, 1))

        # Impact splash
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(6 + st * 12)
            alpha = _NS_sasori._alpha(200 * (1 - st))
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_dark"], alpha),
                                 (tx, ty), radius, 2)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_light"], alpha),
                                 (tx, ty), max(1, radius - 4), 1)

    # ============================================================
    # BODY (Humanoid Puppeteer) - DESAIN ASLI (TIDAK DIUBAH)
    # ============================================================
    def _draw_sasori_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        _NS_sasori._draw_akatsuki_cloak(surface, cx, cy + 8, facing, phase, action)
        _NS_sasori._draw_legs_hint(surface, cx, cy + 22, facing, phase, action)
        _NS_sasori._draw_torso(surface, cx, cy + 4, facing, phase)

        arm_lift = 0
        if action == "attack":
            if attack_progress < 0.4:
                arm_lift = int(attack_progress / 0.4 * 6)
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                arm_lift = int(6 - t * 4)
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_lift = int(2 * (1 - t))
        elif action == "walk":
            arm_lift = int(math.sin(phase * 0.9) * 2)
        else:
            arm_lift = int(math.sin(phase * 0.5) * 1)

        _NS_sasori._draw_arms_with_strings(surface, cx, cy + 2, facing, phase,
                                           action, arm_lift, attack_progress)
        _NS_sasori._draw_head(surface, cx, cy - 16, facing, phase, action)

    def _draw_akatsuki_cloak(surface, cx, cy, facing, phase, action):
        sway = math.sin(phase * 0.6) * 2
        if action == "walk":
            sway = math.sin(phase * 0.9) * 3

        cloak_shape = [
            (cx - 14, cy - 12),
            (cx - 16, cy - 4),
            (cx - 18 + int(sway), cy + 8),
            (cx - 20 + int(sway), cy + 20),
            (cx - 18 + int(sway), cy + 26),
            (cx - 8, cy + 28),
            (cx + 8, cy + 28),
            (cx + 18 - int(sway), cy + 26),
            (cx + 20 - int(sway), cy + 20),
            (cx + 18 - int(sway), cy + 8),
            (cx + 16, cy - 4),
            (cx + 14, cy - 12),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in cloak_shape])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["cloak_darkest"], cloak_shape)

        inner_shape = [
            (cx - 12, cy - 10),
            (cx - 14, cy - 3),
            (cx - 16 + int(sway), cy + 8),
            (cx - 17 + int(sway), cy + 22),
            (cx - 7, cy + 25),
            (cx + 7, cy + 25),
            (cx + 17 - int(sway), cy + 22),
            (cx + 16 - int(sway), cy + 8),
            (cx + 14, cy - 3),
            (cx + 12, cy - 10),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["cloak_dark"], inner_shape)

        _NS_sasori._poly(surface, _NS_sasori.PALETTE["cloak_mid"], [
            (cx - 8, cy - 5), (cx - 6, cy + 15),
            (cx - 3, cy + 20), (cx - 4, cy - 5),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["cloak_mid"], [
            (cx + 4, cy - 5), (cx + 3, cy + 20),
            (cx + 6, cy + 15), (cx + 8, cy - 5),
        ])
        pygame.draw.line(surface, _NS_sasori.PALETTE["cloak_darkest"],
                         (cx, cy - 8), (cx, cy + 25), 1)

        _NS_sasori._draw_akatsuki_cloud(surface, cx - 10, cy + 2, 5)
        _NS_sasori._draw_akatsuki_cloud(surface, cx + 8, cy + 8, 4)
        _NS_sasori._draw_akatsuki_cloud(surface, cx - 5, cy + 18, 4)

        pygame.draw.line(surface, _NS_sasori.PALETTE["cloak_light"],
                         (cx - 16 + int(sway), cy + 26),
                         (cx + 16 - int(sway), cy + 26), 1)

    def _draw_akatsuki_cloud(surface, cx, cy, size):
        pygame.draw.ellipse(surface, _NS_sasori.PALETTE["cloud_dark"],
                            (cx - size, cy - size, size * 2, size * 2))
        pygame.draw.ellipse(surface, _NS_sasori.PALETTE["cloud_mid"],
                            (cx - size + 1, cy - size + 1,
                             size * 2 - 2, size * 2 - 2))
        pygame.draw.ellipse(surface, _NS_sasori.PALETTE["cloud_light"],
                            (cx - size + 2, cy - size + 1, size, size))
        pygame.draw.ellipse(surface, _NS_sasori.PALETTE["cloud_edge"],
                            (cx - size, cy - size, size * 2, size * 2), 1)
        pygame.draw.rect(surface, _NS_sasori.PALETTE["cloud_dark"],
                         (cx - size - 1, cy + size - 2, 2, 2))

    def _draw_legs_hint(surface, cx, cy, facing, phase, action):
        step = 0
        if action == "walk":
            step = int(math.sin(phase * 0.9) * 2)

        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"],
                         (cx - 6, cy + 4, 6, 3))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["cloak_darkest"],
                         (cx - 5, cy + 4, 5, 2))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"],
                         (cx + 1, cy + 4 - abs(step), 6, 3))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["cloak_darkest"],
                         (cx + 1, cy + 4 - abs(step), 5, 2))

    def _draw_torso(surface, cx, cy, facing, phase):
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["cloak_darkest"], [
            (cx - 8, cy - 10), (cx - 6, cy - 14), (cx + 6, cy - 14),
            (cx + 8, cy - 10), (cx + 6, cy - 6), (cx - 6, cy - 6),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["cloak_dark"], [
            (cx - 6, cy - 12), (cx - 5, cy - 13), (cx + 5, cy - 13),
            (cx + 6, cy - 12), (cx + 5, cy - 8), (cx - 5, cy - 8),
        ])
        pygame.draw.line(surface, _NS_sasori.PALETTE["cloak_mid"],
                         (cx - 5, cy - 13), (cx + 5, cy - 13), 1)

    def _draw_arms_with_strings(surface, cx, cy, facing, phase, action,
                                arm_lift, attack_progress):
        for side_mult in (-1, 1):
            shoulder_x = cx + side_mult * 6
            shoulder_y = cy - 6

            extend = 8 if action == "attack" else 6
            elbow_x = shoulder_x + facing * (extend - 2)
            elbow_y = shoulder_y + 2 - arm_lift // 2

            hand_x = shoulder_x + facing * (extend + 6)
            hand_y = shoulder_y + 4 - arm_lift

            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 5)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["cloak_darkest"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["cloak_dark"],
                               (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 3)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["cloak_mid"],
                               (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["cloak_darkest"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 3)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["cloak_dark"],
                               (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)

            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["shadow_deep"], (hand_x + 1, hand_y + 1), 3)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["skin_darkest"], (hand_x, hand_y), 3)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["skin_dark"], (hand_x, hand_y), 2)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["skin_mid"], (hand_x, hand_y - 1), 1)
            pygame.draw.rect(surface, _NS_sasori.PALETTE["skin_light"], (hand_x, hand_y - 1, 1, 1))

            _NS_sasori._draw_chakra_strings(surface, hand_x, hand_y, facing,
                                            phase, action, attack_progress, side_mult)

    def _draw_chakra_strings(surface, hx, hy, facing, phase, action, attack_progress, side_mult):
        num_strings = 5
        base_length = 20
        if action == "attack":
            base_length = int(20 + attack_progress * 15)

        for i in range(num_strings):
            angle_spread = (i - 2) * 0.15
            angle = angle_spread + math.sin(phase * 1.5 + i) * 0.05
            segments = 6
            points = [(hx, hy)]
            for s in range(1, segments + 1):
                t = s / segments
                base_x = hx + facing * int(t * base_length)
                base_y = hy + int(t * base_length * angle)
                wave = math.sin(phase * 3 + s * 0.5 + i) * 2 * t
                points.append((base_x, base_y + int(wave)))

            for seg_i in range(len(points) - 1):
                _NS_sasori._aaline(surface, _NS_sasori.PALETTE["string_darkest"],
                                   points[seg_i], points[seg_i + 1], 2)
                _NS_sasori._aaline(surface, _NS_sasori.PALETTE["string_dark"],
                                   points[seg_i], points[seg_i + 1], 1)
                _NS_sasori._aaline(surface, _NS_sasori.PALETTE["string_mid"],
                                   points[seg_i], points[seg_i + 1], 1)

            if points:
                end = points[-1]
                pygame.draw.rect(surface, _NS_sasori.PALETTE["string_light"], (end[0], end[1], 1, 1))
                pygame.draw.rect(surface, _NS_sasori.PALETTE["string_glow"], (end[0], end[1], 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, action):
        head_shape = [
            (cx - 7, cy - 2), (cx - 8, cy - 5), (cx - 6, cy - 9),
            (cx - 2, cy - 11), (cx + 2, cy - 11), (cx + 6, cy - 9),
            (cx + 8, cy - 5), (cx + 7, cy - 2), (cx + 6, cy + 2),
            (cx + 3, cy + 5), (cx - 3, cy + 5), (cx - 6, cy + 2),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"], [(px + 1, py + 2) for px, py in head_shape])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["skin_darkest"], head_shape)

        _NS_sasori._poly(surface, _NS_sasori.PALETTE["skin_dark"], [
            (cx - 6, cy - 2), (cx - 7, cy - 4), (cx - 5, cy - 7),
            (cx + 5, cy - 7), (cx + 7, cy - 4), (cx + 6, cy - 2),
            (cx + 5, cy + 3), (cx - 5, cy + 3),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["skin_mid"], [
            (cx - 5, cy - 1), (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 5, cy - 1), (cx + 4, cy + 2), (cx - 4, cy + 2),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["skin_light"], [
            (cx - 3, cy - 2), (cx + 3, cy - 2), (cx + 2, cy + 1), (cx - 2, cy + 1),
        ])

        _NS_sasori._draw_red_hair(surface, cx, cy, facing, phase)
        _NS_sasori._draw_puppet_eyes(surface, cx, cy, facing, phase)

        pygame.draw.line(surface, _NS_sasori.PALETTE["shadow_deep"], (cx - 2, cy + 3), (cx + 2, cy + 3), 1)

    def _draw_red_hair(surface, cx, cy, facing, phase):
        hair_base = [
            (cx - 8, cy - 8), (cx - 9, cy - 5), (cx - 7, cy - 10),
            (cx - 4, cy - 13), (cx - 1, cy - 12), (cx + 3, cy - 13),
            (cx + 6, cy - 12), (cx + 8, cy - 10), (cx + 9, cy - 6),
            (cx + 7, cy - 4), (cx - 7, cy - 4),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["hair_darkest"], hair_base)
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["hair_dark"], [
            (cx - 7, cy - 6), (cx - 6, cy - 10), (cx - 3, cy - 12),
            (cx + 3, cy - 12), (cx + 6, cy - 10), (cx + 7, cy - 6),
            (cx + 5, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["hair_mid"], [
            (cx - 5, cy - 8), (cx - 2, cy - 11), (cx + 2, cy - 11),
            (cx + 5, cy - 8), (cx + 3, cy - 6), (cx - 3, cy - 6),
        ])

        spikes = [
            (cx - 6, cy - 10, cx - 7, cy - 13),
            (cx - 3, cy - 12, cx - 2, cy - 15),
            (cx, cy - 12, cx + 1, cy - 15),
            (cx + 3, cy - 12, cx + 4, cy - 14),
            (cx + 6, cy - 10, cx + 7, cy - 12),
        ]
        for base_x, base_y, tip_x, tip_y in spikes:
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["hair_darkest"], [
                (base_x - 1, base_y), (tip_x, tip_y), (base_x + 1, base_y),
            ])
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["hair_mid"], [
                (base_x, base_y), (tip_x, tip_y + 1), (base_x + 1, base_y),
            ])
            pygame.draw.rect(surface, _NS_sasori.PALETTE["hair_light"], (tip_x, tip_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_sasori.PALETTE["hair_shine"], (tip_x, tip_y, 1, 1))

        pygame.draw.line(surface, _NS_sasori.PALETTE["hair_light"], (cx - 3, cy - 8), (cx - 1, cy - 10), 1)
        pygame.draw.line(surface, _NS_sasori.PALETTE["hair_light"], (cx + 2, cy - 9), (cx + 4, cy - 8), 1)

    def _draw_puppet_eyes(surface, cx, cy, facing, phase):
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx - 4, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx + 1, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["eye_dark"], (cx - 3, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["eye_dark"], (cx + 2, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["eye_mid"], (cx - 3, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["eye_mid"], (cx + 2, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow"], (cx - 3, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow"], (cx + 2, cy - 3, 1, 1))

        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        alpha = _NS_sasori._alpha(80 * pulse)
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_dark"], alpha), (cx - 3, cy - 2, 2, 1))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_dark"], alpha), (cx + 2, cy - 2, 2, 1))

    # ============================================================
    # EFEK AMBIENT & SKILL LENGKAP (TIDAK DIUBAH DARI VERSI AWAL)
    # ============================================================
    def _draw_akatsuki_mist(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_sasori._alpha((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sasori.PALETTE["aura_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3, radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_sasori._alpha((24 - radius) * 3.0 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sasori.PALETTE["aura_dark"], alpha),
                    (75 - radius, 25 - radius // 4, radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))

        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_sasori._alpha(200 * (1 - t) * strength)
            if alpha <= 0: continue
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_dark"], alpha), (sx, sy), 3)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_sasori.PALETTE["aura_light"], alpha), (sx, sy - 1, 1, 1))

        for i in range(6):
            spark_t = (phase * 0.6 + i * 0.17) % 1.0
            ex = cx - 26 + i * 10 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(spark_t * 22)
            alpha = _NS_sasori._alpha(220 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_mid"], alpha), (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_glow"], alpha), (ex, ey - 1, 1, 1))

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_sasori._alpha(140 - i * 25)
                if alpha <= 0: continue
                _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_dark"], alpha), (sx, sy), max(2, 6 - i))
                _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_mid"], alpha), (sx, sy), max(1, 4 - i))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 3, 5, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 15, 50, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_akatsuki_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_sasori._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sasori._aacircle(aura, (*_NS_sasori.PALETTE["aura_darkest"], alpha), (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_sasori._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_sasori._aacircle(aura, (*_NS_sasori.PALETTE["aura_dark"], alpha), (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_sasori._alpha((35 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_sasori._aacircle(aura, (*_NS_sasori.PALETTE["aura_mid"], alpha), (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_sasori.PALETTE["string_mid"] if i % 2 == 0 else _NS_sasori.PALETTE["aura_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sasori.PALETTE["string_glow"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_sasori.PALETTE["aura_darkest"], 200), (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_sasori.PALETTE["aura_dark"], 220), (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_sasori.PALETTE["aura_mid"], 200), (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_sasori.PALETTE["string_dark"], 180), (40, 24, 90, 14), 1)

        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_sasori.PALETTE["string_mid"], 220), (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_sasori.PALETTE["string_light"], _NS_sasori._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    def _draw_iron_sand_kunai(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sasori._target_position(boss, x, y)

        if progress < 0.25:
            t = progress / 0.25
            for i in range(15):
                angle = phase * 3 + i * math.pi * 2 / 15
                r = int(30 * (1 - t) + 8)
                sx = x + int(math.cos(angle) * r)
                sy = y - 10 + int(math.sin(angle) * r * 0.4)
                alpha = _NS_sasori._alpha(200 * t)
                pygame.draw.rect(surface, (*_NS_sasori.PALETTE["iron_dark"], alpha), (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_sasori.PALETTE["iron_light"], alpha), (sx, sy, 1, 1))
        else:
            t = (progress - 0.25) / 0.75
            num_kunai = 12
            for k in range(num_kunai):
                k_progress = min(1.0, max(0.0, t * 1.5 - k * 0.05))
                if k_progress <= 0: continue
                start_x = x + facing * (60 + k * 8)
                start_y = y - 120 - k * 6
                end_x = tx + (k - num_kunai // 2) * 6
                end_y = ty
                kx = int(start_x + (end_x - start_x) * k_progress)
                ky = int(start_y + (end_y - start_y) * k_progress)
                angle = math.atan2(end_y - start_y, end_x - start_x)

                for trail_i in range(4):
                    trail_t = max(0.0, k_progress - trail_i * 0.05)
                    if trail_t <= 0: continue
                    tpx = int(start_x + (end_x - start_x) * trail_t)
                    tpy = int(start_y + (end_y - start_y) * trail_t)
                    talpha = _NS_sasori._alpha(180 - trail_i * 40)
                    _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["string_dark"], talpha),
                                         (tpx, tpy), max(1, 2 - trail_i // 2))

                tip_x = kx + int(math.cos(angle) * 4)
                tip_y = ky + int(math.sin(angle) * 4)
                back_x = kx - int(math.cos(angle) * 3)
                back_y = ky - int(math.sin(angle) * 3)
                perp = angle + math.pi / 2
                wa = (kx + int(math.cos(perp) * 2), ky + int(math.sin(perp) * 2))
                wb = (kx - int(math.cos(perp) * 2), ky - int(math.sin(perp) * 2))

                _NS_sasori._poly(surface, _NS_sasori.PALETTE["iron_darkest"],
                                 [(tip_x, tip_y), wa, (back_x, back_y), wb])
                _NS_sasori._poly(surface, _NS_sasori.PALETTE["iron_mid"], [
                    (tip_x, tip_y), (int((tip_x + wa[0]) / 2), int((tip_y + wa[1]) / 2)),
                    (kx, ky), (int((tip_x + wb[0]) / 2), int((tip_y + wb[1]) / 2)),
                ])
                pygame.draw.rect(surface, _NS_sasori.PALETTE["iron_shine"], (tip_x, tip_y, 1, 1))

                if k_progress > 0.85:
                    imp_t = (k_progress - 0.85) / 0.15
                    imp_r = int(4 + imp_t * 10)
                    imp_alpha = _NS_sasori._alpha(230 * (1 - imp_t))
                    _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["string_mid"], imp_alpha), (end_x, end_y), imp_r,
                                         2)
                    _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_light"], imp_alpha), (end_x, end_y),
                                         max(1, imp_r - 3), 1)

    def _draw_third_kazekage(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        px = x + facing * 40
        py = y

        if progress < 0.25:
            t = progress / 0.25
            for i in range(20):
                angle = phase * 2 + i * math.pi * 2 / 20
                r = int(20 * (1 - t) + 5)
                sx = px + int(math.cos(angle) * r)
                sy = py + int(math.sin(angle) * r * 0.5)
                alpha = _NS_sasori._alpha(200)
                _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_dark"], alpha), (sx, sy), 4)
                _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_mid"], alpha), (sx, sy), 2)
        else:
            appear_t = min(1.0, (progress - 0.25) / 0.15)
            if appear_t > 0:
                _NS_sasori._draw_kazekage_puppet(surface, px, py, facing, phase, appear_t, progress)
            if progress > 0.5:
                attack_t = (progress - 0.5) / 0.5
                _NS_sasori._draw_kazekage_attack(surface, boss, px, py, facing, attack_t, phase)

    def _draw_kazekage_puppet(surface, cx, cy, facing, phase, appear_t, progress):
        alpha_mult = appear_t
        body = [
            (cx - 10, cy - 8), (cx - 12, cy - 2), (cx - 10, cy + 12),
            (cx - 6, cy + 18), (cx + 6, cy + 18), (cx + 10, cy + 12),
            (cx + 12, cy - 2), (cx + 10, cy - 8),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in body])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_darkest"], body)
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_dark"], [
            (cx - 9, cy - 6), (cx - 10, cy), (cx - 8, cy + 12),
            (cx + 8, cy + 12), (cx + 10, cy), (cx + 9, cy - 6),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_mid"], [
            (cx - 6, cy - 4), (cx - 7, cy + 2), (cx - 4, cy + 8),
            (cx + 4, cy + 8), (cx + 7, cy + 2), (cx + 6, cy - 4),
        ])
        pygame.draw.line(surface, _NS_sasori.PALETTE["wood_darkest"], (cx - 10, cy + 4), (cx + 10, cy + 4), 1)
        pygame.draw.line(surface, _NS_sasori.PALETTE["wood_darkest"], (cx - 8, cy + 12), (cx + 8, cy + 12), 1)

        head = [
            (cx - 6, cy - 12), (cx - 7, cy - 14), (cx - 5, cy - 18),
            (cx - 2, cy - 19), (cx + 2, cy - 19), (cx + 5, cy - 18),
            (cx + 7, cy - 14), (cx + 6, cy - 12), (cx + 4, cy - 10), (cx - 4, cy - 10),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_darkest"], head)
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_dark"], [
            (cx - 5, cy - 13), (cx - 4, cy - 17), (cx + 4, cy - 17),
            (cx + 5, cy - 13), (cx + 3, cy - 11), (cx - 3, cy - 11),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_mid"], [
            (cx - 3, cy - 15), (cx + 3, cy - 15), (cx + 2, cy - 12), (cx - 2, cy - 12),
        ])

        alpha = _NS_sasori._alpha(230 * alpha_mult)
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx - 3, cy - 15, 2, 1))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx + 1, cy - 15, 2, 1))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_mid"], alpha), (cx - 3, cy - 15, 2, 1))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_mid"], alpha), (cx + 1, cy - 15, 2, 1))

        for side in (-1, 1):
            shoulder_x = cx + side * 10
            shoulder_y = cy - 4
            fist_x = shoulder_x + side * 6
            fist_y = cy + 4
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["wood_darkest"], (shoulder_x, shoulder_y), (fist_x, fist_y),
                               5)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["wood_dark"], (shoulder_x, shoulder_y - 1),
                               (fist_x, fist_y - 1), 3)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["wood_darkest"], (fist_x, fist_y + 2), 4)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["wood_dark"], (fist_x, fist_y + 2), 3)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["wood_mid"], (fist_x, fist_y + 1), 2)

        sasori_hand_x = cx - facing * 40 + facing * 14
        sasori_hand_y = cy + 2
        for si in range(3):
            offset = (si - 1) * 3
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["string_darkest"],
                               (sasori_hand_x, sasori_hand_y + offset), (cx, cy - 4 + offset), 2)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["string_mid"],
                               (sasori_hand_x, sasori_hand_y + offset), (cx, cy - 4 + offset), 1)

    def _draw_kazekage_attack(surface, boss, cx, cy, facing, t, phase):
        tx, ty = _NS_sasori._target_position(boss, cx, cy)
        for i in range(25):
            angle = phase * 2 + i * math.pi * 2 / 25
            spread = int(30 + t * 40)
            sx = cx + facing * 15 + int(math.cos(angle) * spread * (0.5 + t * 0.5))
            sy = cy + int(math.sin(angle) * spread * 0.5)
            alpha = _NS_sasori._alpha(220 * (1 - t * 0.3))
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_dark"], alpha), (sx, sy), 3)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_mid"], alpha), (sx, sy), 2)
            pygame.draw.rect(surface, _NS_sasori.PALETTE["iron_shine"], (sx, sy, 1, 1))

        if t > 0.3:
            bt = (t - 0.3) / 0.7
            br = int(15 + bt * 25)
            b_alpha = _NS_sasori._alpha(220 * (1 - bt * 0.5))
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_darkest"], b_alpha), (cx + facing * 40, cy),
                                 br + 2, 3)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["iron_dark"], b_alpha), (cx + facing * 40, cy), br, 2)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["string_mid"], b_alpha), (cx + facing * 40, cy),
                                 max(1, br - 6), 1)

    def _draw_puppet_horde_ground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        for i in range(3):
            r = int(60 + i * 15 + math.sin(phase * 2) * 4)
            alpha = _NS_sasori._alpha(120 - i * 30)
            offset_x = facing * 40
            pygame.draw.ellipse(surface, (*_NS_sasori.PALETTE["aura_dark"], alpha),
                                (x + offset_x - r, y + 30 - r // 3, r * 2, r * 2 // 3), 2)

    def _draw_puppet_horde_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        num_puppets = 25

        rng_state = random.getstate()
        random.seed(42)

        for i in range(num_puppets):
            row = i // 8
            col = i % 8
            base_x = x + facing * (30 + col * 15 + row * 5)
            base_y = y + (row - 1) * 10 + random.randint(-4, 4)

            appear_progress = progress * 2.5 - i * 0.02
            if appear_progress <= 0: continue
            appear_progress = min(1.0, appear_progress)

            bob = int(math.sin(phase * 2 + i * 0.5) * 2)
            cx, cy = base_x, base_y

            pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx - 3, cy - 6 + bob, 6, 8))
            pygame.draw.rect(surface, _NS_sasori.PALETTE["wood_darkest"], (cx - 3, cy - 6 + bob, 6, 7))
            pygame.draw.rect(surface, _NS_sasori.PALETTE["wood_dark"], (cx - 2, cy - 5 + bob, 4, 6))
            pygame.draw.rect(surface, _NS_sasori.PALETTE["wood_mid"], (cx - 1, cy - 4 + bob, 2, 4))
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["wood_darkest"], (cx, cy - 8 + bob), 3)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["wood_dark"], (cx, cy - 8 + bob), 2)
            pygame.draw.rect(surface, _NS_sasori.PALETTE["string_mid"], (cx - 1, cy - 8 + bob, 1, 1))
            pygame.draw.rect(surface, _NS_sasori.PALETTE["string_mid"], (cx + 1, cy - 8 + bob, 1, 1))
            pygame.draw.line(surface, _NS_sasori.PALETTE["wood_darkest"], (cx - 3, cy - 4 + bob),
                             (cx - 5, cy - 2 + bob), 1)
            pygame.draw.line(surface, _NS_sasori.PALETTE["wood_darkest"], (cx + 3, cy - 4 + bob),
                             (cx + 5, cy - 2 + bob), 1)

        random.setstate(rng_state)

        sasori_hand_x = x + facing * 14
        sasori_hand_y = y + 2
        rng_state = random.getstate()
        random.seed(42)
        for i in range(0, num_puppets, 3):
            row = i // 8
            col = i % 8
            base_x = x + facing * (30 + col * 15 + row * 5)
            base_y = y + (row - 1) * 10 + random.randint(-4, 4)

            appear_progress = progress * 2.5 - i * 0.02
            if appear_progress <= 0: continue

            alpha = _NS_sasori._alpha(120 * min(1.0, appear_progress))
            pygame.draw.line(surface, (*_NS_sasori.PALETTE["string_mid"], alpha),
                             (sasori_hand_x, sasori_hand_y), (base_x, base_y - 6), 1)
        random.setstate(rng_state)

    def _draw_hiruko_ground(surface, boss, x, y, timer, phase):
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(3):
            r = int(70 + i * 10 + pulse * 5)
            alpha = _NS_sasori._alpha(180 - i * 40)
            pygame.draw.ellipse(surface, (*_NS_sasori.PALETTE["aura_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_sasori.PALETTE["string_dark"], alpha),
                                (x - r + 4, y + 40 - r // 3 + 2, r * 2 - 8, r * 2 // 3 - 4), 1)

    def _draw_hiruko_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            t = progress / 0.3
            for i in range(30):
                angle = phase * 2 + i * math.pi * 2 / 30
                r = int(50 * (1 - t) + 15)
                sx = x + int(math.cos(angle) * r)
                sy = y + int(math.sin(angle) * r * 0.6)
                alpha = _NS_sasori._alpha(220)
                _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_dark"], alpha), (sx, sy), 5)
                _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["aura_mid"], alpha), (sx, sy), 3)
                pygame.draw.rect(surface, _NS_sasori.PALETTE["aura_light"], (sx, sy, 1, 1))
        else:
            appear_t = min(1.0, (progress - 0.3) / 0.2)
            _NS_sasori._draw_hiruko_puppet(surface, x, y, facing, phase, appear_t)
            if progress > 0.55:
                attack_t = (progress - 0.55) / 0.45
                _NS_sasori._draw_hiruko_attack(surface, boss, x, y, facing, attack_t, phase)

    def _draw_hiruko_puppet(surface, cx, cy, facing, phase, appear_t):
        body = [
            (cx - 25, cy + 10), (cx - 28, cy), (cx - 22, cy - 12),
            (cx - 10, cy - 20), (cx + 10, cy - 20), (cx + 22, cy - 12),
            (cx + 28, cy), (cx + 25, cy + 10), (cx + 15, cy + 15), (cx - 15, cy + 15),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in body])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_darkest"], body)
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_dark"], [
            (cx - 22, cy + 8), (cx - 25, cy), (cx - 20, cy - 10),
            (cx - 8, cy - 17), (cx + 8, cy - 17), (cx + 20, cy - 10),
            (cx + 25, cy), (cx + 22, cy + 8), (cx + 12, cy + 12), (cx - 12, cy + 12),
        ])
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_mid"], [
            (cx - 15, cy + 4), (cx - 18, cy - 4), (cx - 5, cy - 14),
            (cx + 5, cy - 14), (cx + 18, cy - 4), (cx + 15, cy + 4),
            (cx + 8, cy + 8), (cx - 8, cy + 8),
        ])

        for py in (-8, -2, 4, 10):
            pygame.draw.line(surface, _NS_sasori.PALETTE["wood_darkest"], (cx - 20, cy + py), (cx + 20, cy + py), 1)
            pygame.draw.line(surface, _NS_sasori.PALETTE["wood_light"], (cx - 18, cy + py - 1), (cx + 18, cy + py - 1),
                             1)

        head_shape = [
            (cx - 8, cy - 15), (cx - 9, cy - 18), (cx - 5, cy - 22),
            (cx + 5, cy - 22), (cx + 9, cy - 18), (cx + 8, cy - 15),
        ]
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_darkest"], head_shape)
        _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_dark"], [
            (cx - 7, cy - 16), (cx - 4, cy - 21), (cx + 4, cy - 21), (cx + 7, cy - 16),
        ])

        alpha = _NS_sasori._alpha(240 * appear_t)
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx - 5, cy - 19, 3, 2))
        pygame.draw.rect(surface, _NS_sasori.PALETTE["shadow_deep"], (cx + 2, cy - 19, 3, 2))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_dark"], alpha), (cx - 5, cy - 19, 3, 2))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_dark"], alpha), (cx + 2, cy - 19, 3, 2))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_mid"], alpha), (cx - 4, cy - 19, 2, 1))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_mid"], alpha), (cx + 3, cy - 19, 2, 1))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_glow"], alpha), (cx - 4, cy - 19, 1, 1))
        pygame.draw.rect(surface, (*_NS_sasori.PALETTE["string_glow"], alpha), (cx + 3, cy - 19, 1, 1))

        spike_positions = [
            (-24, -6, -30, -10), (-20, -14, -26, -20), (-10, -20, -12, -28),
            (0, -22, 0, -30), (10, -20, 12, -28), (20, -14, 26, -20),
            (24, -6, 30, -10), (-20, 4, -28, 4), (20, 4, 28, 4),
        ]
        for bx_off, by_off, tx_off, ty_off in spike_positions:
            base_x = cx + bx_off
            base_y = cy + by_off
            tip_x = cx + tx_off
            tip_y = cy + ty_off
            perp_angle = math.atan2(tip_y - base_y, tip_x - base_x) + math.pi / 2
            pa = (base_x + int(math.cos(perp_angle) * 2), base_y + int(math.sin(perp_angle) * 2))
            pb = (base_x - int(math.cos(perp_angle) * 2), base_y - int(math.sin(perp_angle) * 2))
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"],
                             [(tip_x + 1, tip_y + 1), (pa[0] + 1, pa[1] + 1), (pb[0] + 1, pb[1] + 1)])
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_darkest"], [(tip_x, tip_y), pa, pb])
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_dark"],
                             [(tip_x, tip_y), (int((tip_x + base_x) / 2), int((tip_y + base_y) / 2)), (base_x, base_y)])
            pygame.draw.rect(surface, _NS_sasori.PALETTE["wood_light"], (tip_x, tip_y, 1, 1))

        _NS_sasori._draw_hiruko_tail(surface, cx, cy, facing, phase)

    def _draw_hiruko_tail(surface, cx, cy, facing, phase):
        segments = 8
        base_x = cx - facing * 15
        base_y = cy + 5
        wave = math.sin(phase * 1.5) * 3
        points = [(base_x, base_y)]

        for i in range(1, segments + 1):
            t = i / segments
            angle = -math.pi * 0.4 - t * math.pi * 0.9
            px = base_x - facing * int((1 - math.cos(angle)) * 20 * t)
            py = base_y + int(math.sin(angle) * 30 * t) + int(wave * t)
            points.append((px, py))

        for i in range(len(points) - 1):
            thickness = max(2, 8 - i)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["shadow_deep"], (points[i][0] + 1, points[i][1] + 1),
                               (points[i + 1][0] + 1, points[i + 1][1] + 1), thickness + 1)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["wood_darkest"], points[i], points[i + 1], thickness)
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["wood_dark"], points[i], points[i + 1],
                               max(1, thickness - 2))
            _NS_sasori._aaline(surface, _NS_sasori.PALETTE["wood_mid"], (points[i][0], points[i][1] - 1),
                               (points[i + 1][0], points[i + 1][1] - 1), max(1, thickness - 4))

        if len(points) >= 2:
            end = points[-1]
            prev = points[-2]
            angle = math.atan2(end[1] - prev[1], end[0] - prev[0])
            stinger_tip = (end[0] + int(math.cos(angle) * 8), end[1] + int(math.sin(angle) * 8))
            perp = angle + math.pi / 2
            base_a = (end[0] + int(math.cos(perp) * 3), end[1] + int(math.sin(perp) * 3))
            base_b = (end[0] - int(math.cos(perp) * 3), end[1] - int(math.sin(perp) * 3))
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["shadow_deep"],
                             [(stinger_tip[0] + 1, stinger_tip[1] + 1), (base_a[0] + 1, base_a[1] + 1),
                              (base_b[0] + 1, base_b[1] + 1)])
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_darkest"], [stinger_tip, base_a, base_b])
            _NS_sasori._poly(surface, _NS_sasori.PALETTE["wood_dark"], [stinger_tip,
                                                                        (int((stinger_tip[0] + base_a[0]) / 2),
                                                                         int((stinger_tip[1] + base_a[1]) / 2)), end])
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["string_dark"], stinger_tip, 2)
            _NS_sasori._aacircle(surface, _NS_sasori.PALETTE["string_mid"], stinger_tip, 1)
            pygame.draw.rect(surface, _NS_sasori.PALETTE["string_glow"], (stinger_tip[0], stinger_tip[1], 1, 1))

    def _draw_hiruko_attack(surface, boss, cx, cy, facing, t, phase):
        tx, ty = _NS_sasori._target_position(boss, cx, cy)
        num_strings = 8
        for i in range(num_strings):
            end_x = tx + int((i - num_strings / 2) * 15)
            end_y = ty
            segments = 6
            for seg in range(segments):
                s1_t = seg / segments
                s2_t = (seg + 1) / segments
                s1x = cx + int((end_x - cx) * s1_t)
                s1y = cy + int((end_y - cy) * s1_t) + int(math.sin(phase * 3 + i + seg) * 3)
                s2x = cx + int((end_x - cx) * s2_t)
                s2y = cy + int((end_y - cy) * s2_t) + int(math.sin(phase * 3 + i + seg + 1) * 3)
                alpha = _NS_sasori._alpha(220 * t)
                _NS_sasori._aaline(surface, (*_NS_sasori.PALETTE["string_darkest"], alpha), (s1x, s1y), (s2x, s2y), 2)
                _NS_sasori._aaline(surface, (*_NS_sasori.PALETTE["string_mid"], alpha), (s1x, s1y), (s2x, s2y), 1)

        if t > 0.3:
            imp_t = (t - 0.3) / 0.7
            imp_r = int(15 + imp_t * 20)
            imp_alpha = _NS_sasori._alpha(220 * (1 - imp_t * 0.5))
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["string_dark"], imp_alpha), (tx, ty), imp_r, 2)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["string_mid"], imp_alpha), (tx, ty), max(1, imp_r - 5),
                                 1)
            _NS_sasori._aacircle(surface, (*_NS_sasori.PALETTE["string_glow"], imp_alpha), (tx, ty), max(1, imp_r // 3))


# ====================================================================================================
# HOLLOWBANE - TRUE BOSS
# ====================================================================================================

class _NS_hollowbane:
    """Namespace hollowbane - Ichigo Kurosaki inspired mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Shinigami robe (shihakusho) - deep black with blue tint
        "robe_darkest": (5, 5, 10),
        "robe_dark": (18, 18, 28),
        "robe_mid": (38, 38, 52),
        "robe_light": (65, 65, 82),
        "robe_edge": (95, 95, 115),

        # Skin (young human)
        "skin_shadow": (145, 95, 75),
        "skin_dark": (200, 150, 120),
        "skin_mid": (235, 185, 150),
        "skin_light": (255, 215, 180),
        "skin_shine": (255, 235, 210),

        # Orange hair (iconic Ichigo)
        "hair_darkest": (85, 35, 5),
        "hair_dark": (155, 70, 15),
        "hair_mid": (220, 110, 25),
        "hair_light": (255, 155, 55),
        "hair_shine": (255, 200, 110),

        # Zangetsu blade - dark steel
        "blade_darkest": (15, 15, 20),
        "blade_dark": (55, 55, 70),
        "blade_mid": (110, 110, 130),
        "blade_light": (180, 180, 200),
        "blade_shine": (240, 240, 250),

        # Blade wrap (red/brown cloth)
        "wrap_dark": (55, 20, 15),
        "wrap_mid": (110, 40, 25),
        "wrap_light": (170, 70, 45),

        # Spiritual energy (orange fire - Getsuga)
        "spirit_darkest": (60, 15, 0),
        "spirit_dark": (140, 45, 5),
        "spirit_mid": (230, 95, 15),
        "spirit_light": (255, 155, 45),
        "spirit_hot": (255, 210, 100),
        "spirit_shine": (255, 245, 200),

        # Hollow mask (bone white with red)
        "mask_dark": (60, 55, 45),
        "mask_mid": (180, 170, 150),
        "mask_light": (240, 235, 220),
        "mask_shine": (255, 255, 245),
        "mask_red": (180, 25, 30),
        "mask_red_bright": (255, 60, 60),

        # Hollow black energy
        "hollow_black": (8, 5, 15),
        "hollow_dark": (25, 15, 35),
        "hollow_purple": (65, 25, 85),

        # Eye
        "eye_white": (245, 240, 230),
        "eye_iris": (95, 60, 25),
        "eye_pupil": (10, 5, 5),
        "eye_glow": (255, 180, 60),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_hollowbane._clamp(color)
        if _NS_hollowbane.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_hollowbane._clamp(color)
        if _NS_hollowbane.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_hollowbane._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_hollowbane(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_hollowbane._detect_moving(boss)
        _NS_hollowbane._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_hb_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Hollow mask state (R skill toggles it)
        hollow_form = active_skill == "r" or getattr(boss, "_hb_hollow_form", False)

        # Ambient behind
        _NS_hollowbane._draw_spirit_aura(surface, x, y, pulse, hollow_form)
        _NS_hollowbane._draw_ground_ring(surface, x, y + 46, pulse, active_skill, hollow_form)

        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_hollowbane._draw_repulse_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_hollowbane._draw_bankai_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_hollowbane._draw_attack_pose(surface, boss, x, y, hollow_form)
        elif moving:
            _NS_hollowbane._draw_walk_pose(surface, boss, x, y, hollow_form)
        else:
            _NS_hollowbane._draw_idle_pose(surface, boss, x, y, hollow_form)

        # Foreground FX
        if active_skill == "q":
            _NS_hollowbane._draw_getsuga_tensho(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_hollowbane._draw_zangetsu_slash(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_hollowbane._draw_repulse_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_hollowbane._draw_hollow_mask_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "d":
            _NS_hollowbane._draw_bankai_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_hb_previous_timer", 0))
        active = bool(getattr(boss, "_hb_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._hb_attack_active = True
            boss._hb_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._hb_attack_frame = int(getattr(boss, "_hb_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._hb_attack_active = False
            boss._hb_attack_frame = 0
            active = False

        boss._hb_previous_timer = timer
        boss._hb_attack_progress = (
            min(1.0, getattr(boss, "_hb_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_hb_last_x"):
            boss._hb_last_x = boss.x
            boss._hb_last_y = boss.y
            return False
        dx = abs(boss.x - boss._hb_last_x)
        dy = abs(boss.y - boss._hb_last_y)
        boss._hb_last_x = boss.x
        boss._hb_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y, hollow_form):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_hollowbane._draw_shadow(surface, x, y + 50)
        _NS_hollowbane._draw_spirit_wisps(surface, x, y + 20, boss.pulse, hollow_form)
        _NS_hollowbane._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                   "idle", 0, hollow_form)

    def _draw_walk_pose(surface, boss, x, y, hollow_form):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_hollowbane._draw_shadow(surface, x + sway, y + 50)
        _NS_hollowbane._draw_spirit_wisps(surface, x + sway, y + 20, phase, hollow_form,
                                          trail=True, facing=boss.direction)
        _NS_hollowbane._draw_body(surface, x + sway, y + bob, boss.direction, phase,
                                   "walk", 0, hollow_form)

    def _draw_attack_pose(surface, boss, x, y, hollow_form):
        progress = getattr(boss, "_hb_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Wind-up → swing → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_hollowbane._draw_shadow(surface, x + lunge, y + 50)
        _NS_hollowbane._draw_spirit_wisps(surface, x + lunge, y + 20, boss.pulse,
                                          hollow_form, intense=True)
        _NS_hollowbane._draw_body(surface, x + lunge, y - lift, boss.direction,
                                   boss.pulse, "attack", progress, hollow_form)

        # Sword swing trail (melee attack)
        _NS_hollowbane._draw_sword_swing_trail(surface, boss, x + lunge, y - lift,
                                                progress, hollow_form)

    # ============================================================
    # BODY (Humanoid Shinigami)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress,
                   hollow_form):
        """Draw humanoid body: legs, robe, torso, arms, head, sword."""
        # Legs (behind robe)
        _NS_hollowbane._draw_legs(surface, cx, cy + 20, facing, phase, action,
                                   attack_progress)

        # Robe/Shihakusho (main body cloth)
        _NS_hollowbane._draw_robe(surface, cx, cy, facing, phase, action)

        # Torso/chest
        _NS_hollowbane._draw_torso(surface, cx, cy - 4, facing, phase)

        # Back arm (holding sword pommel)
        _NS_hollowbane._draw_back_arm(surface, cx, cy - 2, facing, phase, action,
                                       attack_progress)

        # Head with hair
        _NS_hollowbane._draw_head(surface, cx, cy - 24, facing, phase, action,
                                   hollow_form)

        # Front arm + Zangetsu (BIG sword)
        _NS_hollowbane._draw_sword_arm(surface, cx, cy - 2, facing, phase, action,
                                        attack_progress, hollow_form)

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress):
        """Two legs in hakama pants."""
        # Leg animation
        if action == "walk":
            leg_swing = math.sin(phase * 1.5) * 4
        elif action == "attack":
            leg_swing = math.sin(attack_progress * math.pi) * 3 * facing
        else:
            leg_swing = 0

        # Back leg
        back_leg_x = cx - 5 + int(-leg_swing * 0.5)
        # Robe covers most of legs, only show boots/lower
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["shadow_deep"], [
            (back_leg_x - 3, cy + 2),
            (back_leg_x + 3, cy + 2),
            (back_leg_x + 4, cy + 12),
            (back_leg_x - 4, cy + 12),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_darkest"], [
            (back_leg_x - 3, cy),
            (back_leg_x + 3, cy),
            (back_leg_x + 4, cy + 11),
            (back_leg_x - 4, cy + 11),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_dark"], [
            (back_leg_x - 2, cy + 1),
            (back_leg_x + 2, cy + 1),
            (back_leg_x + 3, cy + 10),
            (back_leg_x - 3, cy + 10),
        ])
        # Boot/foot
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                         (back_leg_x - 4, cy + 10, 8, 3))

        # Front leg
        front_leg_x = cx + 5 + int(leg_swing * 0.5)
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["shadow_deep"], [
            (front_leg_x - 3, cy + 2),
            (front_leg_x + 3, cy + 2),
            (front_leg_x + 4, cy + 12),
            (front_leg_x - 4, cy + 12),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_dark"], [
            (front_leg_x - 3, cy),
            (front_leg_x + 3, cy),
            (front_leg_x + 4, cy + 11),
            (front_leg_x - 4, cy + 11),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_mid"], [
            (front_leg_x - 2, cy + 1),
            (front_leg_x + 2, cy + 1),
            (front_leg_x + 3, cy + 10),
            (front_leg_x - 3, cy + 10),
        ])
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                         (front_leg_x - 4, cy + 10, 8, 3))

    def _draw_robe(surface, cx, cy, facing, phase, action):
        """Flowing shihakusho robe (main body)."""
        flow = math.sin(phase * 0.6) * 2

        # Robe shape (flares out at bottom)
        robe_shape = [
            (cx - 10, cy - 8),
            (cx - 12, cy),
            (cx - 14 + int(flow * facing), cy + 10),
            (cx - 16 + int(flow * facing), cy + 22),
            (cx - 12, cy + 24),
            (cx + 12, cy + 24),
            (cx + 16 - int(flow * facing), cy + 22),
            (cx + 14 - int(flow * facing), cy + 10),
            (cx + 12, cy),
            (cx + 10, cy - 8),
        ]
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in robe_shape])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_darkest"], robe_shape)

        # Robe folds (mid tone)
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_dark"], [
            (cx - 9, cy - 6),
            (cx - 11, cy),
            (cx - 13 + int(flow * facing), cy + 12),
            (cx - 14 + int(flow * facing), cy + 20),
            (cx - 8, cy + 22),
            (cx + 8, cy + 22),
            (cx + 14 - int(flow * facing), cy + 20),
            (cx + 13 - int(flow * facing), cy + 12),
            (cx + 11, cy),
            (cx + 9, cy - 6),
        ])

        # Highlight on chest area
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_mid"], [
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 8, cy + 5),
            (cx - 8, cy + 5),
        ])

        # Vertical fold lines
        for x_off in (-6, 0, 6):
            pygame.draw.line(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                             (cx + x_off, cy + 2),
                             (cx + x_off + int(flow * facing * 0.5), cy + 20), 1)

        # White under-robe visible at collar
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["mask_light"], [
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])

        # Belt (obi)
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["wrap_dark"],
                         (cx - 10, cy + 8, 20, 3))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["wrap_mid"],
                         (cx - 10, cy + 8, 20, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Upper torso (mostly hidden by robe, just shoulders/collar)."""
        # Shoulders
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_darkest"], [
            (cx - 11, cy),
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 11, cy),
            (cx + 10, cy + 2),
            (cx - 10, cy + 2),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["robe_dark"], [
            (cx - 10, cy - 1),
            (cx - 8, cy - 3),
            (cx + 8, cy - 3),
            (cx + 10, cy - 1),
        ])

    def _draw_head(surface, cx, cy, facing, phase, action, hollow_form):
        """Head with orange spiky hair."""
        # Neck
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["skin_dark"],
                         (cx - 2, cy + 8, 4, 4))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["skin_mid"],
                         (cx - 2, cy + 8, 3, 3))

        # Head shape (oval)
        head_shape = [
            (cx - 6, cy + 6),
            (cx - 8, cy + 2),
            (cx - 8, cy - 4),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 8, cy - 4),
            (cx + 8, cy + 2),
            (cx + 6, cy + 6),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in head_shape])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["skin_shadow"], head_shape)

        # Face (main skin)
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["skin_dark"], [
            (cx - 6, cy + 4),
            (cx - 7, cy),
            (cx - 6, cy - 6),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 7, cy - 4),
            (cx + 7, cy + 2),
            (cx + 5, cy + 6),
            (cx - 2, cy + 7),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["skin_mid"], [
            (cx - 5, cy + 2),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 3, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 3),
            (cx - 2, cy + 5),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["skin_light"],
                         (cx + 3 * facing, cy - 1, 2, 2))

        # HOLLOW MASK (if hollow form active)
        if hollow_form:
            _NS_hollowbane._draw_hollow_mask(surface, cx, cy, facing, phase)
        else:
            # Normal face - eyes
            _NS_hollowbane._draw_eyes(surface, cx, cy - 2, facing, phase)
            # Mouth (serious)
            pygame.draw.line(surface, _NS_hollowbane.PALETTE["skin_shadow"],
                             (cx - 2, cy + 4), (cx + 2, cy + 4), 1)

        # ORANGE SPIKY HAIR (iconic Ichigo)
        _NS_hollowbane._draw_hair(surface, cx, cy, facing, phase, hollow_form)

    def _draw_hair(surface, cx, cy, facing, phase, hollow_form):
        """Orange spiky hair - Ichigo signature."""
        wave = math.sin(phase * 0.4) * 1

        # Hair base (on top of head)
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_darkest"], [
            (cx - 8, cy - 4),
            (cx - 9, cy - 8),
            (cx - 6, cy - 12),
            (cx - 2, cy - 13),
            (cx + 3, cy - 13),
            (cx + 7, cy - 11),
            (cx + 9, cy - 6),
            (cx + 8, cy - 3),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy - 8),
            (cx - 5, cy - 11),
            (cx - 1, cy - 12),
            (cx + 3, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy - 4),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_mid"], [
            (cx - 6, cy - 6),
            (cx - 6, cy - 9),
            (cx - 3, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 9),
            (cx + 6, cy - 6),
        ])

        # SPIKES (Ichigo's characteristic hair)
        spikes = [
            (-7, -6, -9, -13 + int(wave)),
            (-4, -9, -5, -15 + int(wave)),
            (-1, -11, -2, -16 + int(wave)),
            (2, -11, 3, -17 + int(wave)),
            (5, -10, 6, -15 + int(wave)),
            (7, -8, 9, -13 + int(wave)),
        ]
        for base_x, base_y, tip_x, tip_y in spikes:
            _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_darkest"], [
                (cx + base_x - 1, cy + base_y),
                (cx + tip_x, cy + tip_y),
                (cx + base_x + 2, cy + base_y),
            ])
            _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_dark"], [
                (cx + base_x, cy + base_y),
                (cx + tip_x, cy + tip_y),
                (cx + base_x + 1, cy + base_y),
            ])
            _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_mid"], [
                (cx + int((base_x + tip_x) / 2), cy + int((base_y + tip_y) / 2)),
                (cx + tip_x, cy + tip_y),
                (cx + int((base_x + tip_x) / 2) + 1,
                 cy + int((base_y + tip_y) / 2)),
            ])
            # Highlight at tip
            pygame.draw.rect(surface, _NS_hollowbane.PALETTE["hair_light"],
                             (cx + tip_x, cy + tip_y, 1, 1))
            if hollow_form:
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["hair_shine"],
                                 (cx + tip_x, cy + tip_y, 1, 1))

        # Bangs over forehead
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_dark"], [
            (cx - 6, cy - 6),
            (cx - 4, cy - 3),
            (cx - 1, cy - 4),
            (cx + 2, cy - 3),
            (cx + 5, cy - 4),
            (cx + 6, cy - 6),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["hair_mid"], [
            (cx - 5, cy - 6),
            (cx - 3, cy - 4),
            (cx + 4, cy - 4),
            (cx + 5, cy - 6),
        ])

    def _draw_eyes(surface, cx, cy, facing, phase):
        """Normal Ichigo brown eyes with intense gaze."""
        # Eye socket shadow
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["skin_shadow"],
                         (cx - 5, cy, 3, 2))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["skin_shadow"],
                         (cx + 2, cy, 3, 2))

        # Eye whites
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["eye_white"],
                         (cx - 4, cy, 2, 2))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["eye_white"],
                         (cx + 3, cy, 2, 2))

        # Iris (brown)
        iris_offset = 0 if facing > 0 else -1
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["eye_iris"],
                         (cx - 4 + iris_offset, cy, 1, 2))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["eye_iris"],
                         (cx + 3 + iris_offset, cy, 1, 2))

        # Pupil
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["eye_pupil"],
                         (cx - 4 + iris_offset, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["eye_pupil"],
                         (cx + 3 + iris_offset, cy + 1, 1, 1))

        # Eyebrows (angry/serious)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["hair_darkest"],
                         (cx - 5, cy - 2), (cx - 2, cy - 1), 1)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["hair_darkest"],
                         (cx + 2, cy - 1), (cx + 5, cy - 2), 1)

    def _draw_hollow_mask(surface, cx, cy, facing, phase):
        """Hollow mask over face - bone white with red stripes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Mask base
        mask_shape = [
            (cx - 6, cy + 4),
            (cx - 7, cy),
            (cx - 6, cy - 5),
            (cx - 2, cy - 7),
            (cx + 3, cy - 7),
            (cx + 7, cy - 4),
            (cx + 7, cy + 2),
            (cx + 5, cy + 5),
            (cx - 2, cy + 6),
        ]
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in mask_shape])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["mask_dark"], mask_shape)
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["mask_mid"], [
            (cx - 5, cy + 3),
            (cx - 6, cy),
            (cx - 5, cy - 4),
            (cx - 1, cy - 6),
            (cx + 3, cy - 6),
            (cx + 6, cy - 3),
            (cx + 6, cy + 1),
            (cx + 4, cy + 4),
        ])
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["mask_light"], [
            (cx - 4, cy + 2),
            (cx - 5, cy - 1),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 1),
            (cx + 4, cy + 3),
        ])

        # RED STRIPES on mask (iconic hollow mark)
        red_alpha = _NS_hollowbane._alpha(255 * pulse)
        # Vertical stripe over left eye
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["mask_red"],
                         (cx - 3, cy - 5), (cx - 3, cy + 3), 2)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["mask_red_bright"],
                         (cx - 3, cy - 5), (cx - 3, cy + 3), 1)
        # Horizontal stripe
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["mask_red"],
                         (cx - 5, cy - 2), (cx + 5, cy - 2), 1)

        # HOLLOW EYES (black + yellow glow)
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["hollow_black"],
                         (cx - 4, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["hollow_black"],
                         (cx + 2, cy - 1, 3, 2))
        # Glowing yellow pupils
        for r in range(3, 0, -1):
            alpha = _NS_hollowbane._alpha(200 * (3 - r) / 3 * pulse)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["eye_glow"], alpha),
                                     (cx - 3, cy), r)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["eye_glow"], alpha),
                                     (cx + 3, cy), r)
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_hot"],
                         (cx - 3, cy, 1, 1))
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_hot"],
                         (cx + 3, cy, 1, 1))

        # Hollow mask teeth grin
        for i, x_off in enumerate((-3, -1, 1, 3)):
            pygame.draw.rect(surface, _NS_hollowbane.PALETTE["mask_light"],
                             (cx + x_off, cy + 3, 1, 2))
            pygame.draw.line(surface, _NS_hollowbane.PALETTE["mask_dark"],
                             (cx + x_off, cy + 3),
                             (cx + x_off, cy + 4), 1)

        # Black energy tendrils around mask
        for i in range(5):
            angle = phase * 1.5 + i * math.pi / 2.5
            tx = cx + int(math.cos(angle) * 10)
            ty = cy + int(math.sin(angle) * 10)
            alpha = _NS_hollowbane._alpha(180 * pulse)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["hollow_black"], alpha),
                                     (tx, ty), 2)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["hollow_purple"], alpha),
                                     (tx, ty), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (partially visible behind body)."""
        arm_x = cx - facing * 8
        arm_y = cy

        # Shoulder
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                                 (arm_x, arm_y - 2), 4)
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["robe_dark"],
                                 (arm_x, arm_y - 2), 3)

        # Upper arm (behind torso, partial)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                         (arm_x, arm_y - 1), (arm_x - facing * 3, arm_y + 6), 4)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["robe_dark"],
                         (arm_x, arm_y - 1), (arm_x - facing * 3, arm_y + 6), 3)

    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress,
                        hollow_form):
        """Front arm holding Zangetsu - the BIG sword."""
        # Base position at shoulder
        shoulder_x = cx + facing * 8
        shoulder_y = cy - 2

        # Sword position depends on action
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: sword goes back and up
                t = attack_progress / 0.35
                sword_angle = math.pi * 0.75 + t * 0.3  # from ~135° up
                arm_extend = 8 + t * 3
            elif attack_progress < 0.6:
                # Swing: sword swings forward and down
                t = (attack_progress - 0.35) / 0.25
                sword_angle = math.pi * 1.05 - t * 1.4  # sweep down
                arm_extend = 11 + t * 4
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                sword_angle = math.pi * -0.35 + t * 0.5
                arm_extend = 15 - t * 5
        elif action == "walk":
            sword_angle = math.pi * 0.9 + math.sin(phase * 1.5) * 0.1
            arm_extend = 9
        else:
            # Idle: sword rested on shoulder
            sword_angle = math.pi * 0.85 + math.sin(phase * 0.5) * 0.05
            arm_extend = 9

        # Hand position
        hand_x = shoulder_x + int(math.cos(sword_angle) * arm_extend * facing)
        hand_y = shoulder_y + int(math.sin(sword_angle) * arm_extend)

        # Shoulder
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                                 (shoulder_x, shoulder_y), 5)
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["robe_dark"],
                                 (shoulder_x, shoulder_y), 4)
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["robe_mid"],
                                 (shoulder_x - 1, shoulder_y - 1), 2)

        # Upper arm (sleeve)
        elbow_x = int((shoulder_x + hand_x) / 2)
        elbow_y = int((shoulder_y + hand_y) / 2)

        _NS_hollowbane._aaline(surface, _NS_hollowbane.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1),
                               (elbow_x + 1, elbow_y + 1), 6)
        _NS_hollowbane._aaline(surface, _NS_hollowbane.PALETTE["robe_darkest"],
                               (shoulder_x, shoulder_y),
                               (elbow_x, elbow_y), 5)
        _NS_hollowbane._aaline(surface, _NS_hollowbane.PALETTE["robe_dark"],
                               (shoulder_x, shoulder_y),
                               (elbow_x, elbow_y), 4)

        # Forearm (skin visible if sleeve rolled)
        _NS_hollowbane._aaline(surface, _NS_hollowbane.PALETTE["shadow_deep"],
                               (elbow_x + 1, elbow_y + 1),
                               (hand_x + 1, hand_y + 1), 4)
        _NS_hollowbane._aaline(surface, _NS_hollowbane.PALETTE["robe_dark"],
                               (elbow_x, elbow_y),
                               (hand_x, hand_y), 3)

        # Hand
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["skin_shadow"],
                                 (hand_x, hand_y), 3)
        _NS_hollowbane._aacircle(surface, _NS_hollowbane.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 2)

        # ZANGETSU SWORD (big cleaver/khyber knife style)
        _NS_hollowbane._draw_zangetsu(surface, hand_x, hand_y, facing, sword_angle,
                                       phase, hollow_form)

    def _draw_zangetsu(surface, hx, hy, facing, angle, phase, hollow_form):
        """Draw Zangetsu - large cleaver-shaped sword."""
        # Blade extends from hand
        blade_length = 34
        blade_width = 6

        # Tip of blade
        tip_x = hx + int(math.cos(angle) * blade_length * facing)
        tip_y = hy + int(math.sin(angle) * blade_length)

        # Perpendicular direction for blade width
        perp_angle = angle + math.pi / 2
        perp_x = math.cos(perp_angle) * facing
        perp_y = math.sin(perp_angle)

        # Blade shape (cleaver - wider at tip)
        # Guard side (near hand)
        guard_a_x = hx + int(perp_x * blade_width * 0.4)
        guard_a_y = hy + int(perp_y * blade_width * 0.4)
        guard_b_x = hx - int(perp_x * blade_width * 0.4)
        guard_b_y = hy - int(perp_y * blade_width * 0.4)

        # Tip side (wider)
        # Cleaver shape: narrow near guard, wider toward tip, then angled to point
        mid_x = hx + int(math.cos(angle) * blade_length * 0.7 * facing)
        mid_y = hy + int(math.sin(angle) * blade_length * 0.7)

        mid_a_x = mid_x + int(perp_x * blade_width)
        mid_a_y = mid_y + int(perp_y * blade_width)
        mid_b_x = mid_x - int(perp_x * blade_width * 0.6)
        mid_b_y = mid_y - int(perp_y * blade_width * 0.6)

        # Blade polygon
        blade_shape = [
            (guard_a_x, guard_a_y),
            (mid_a_x, mid_a_y),
            (tip_x, tip_y),
            (mid_b_x, mid_b_y),
            (guard_b_x, guard_b_y),
        ]

        # Shadow
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in blade_shape])

        # Blade dark base
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["blade_darkest"],
                             blade_shape)

        # Blade mid
        inner_shape = [
            (int(guard_a_x * 0.7 + hx * 0.3), int(guard_a_y * 0.7 + hy * 0.3)),
            (int(mid_a_x * 0.85 + mid_x * 0.15),
             int(mid_a_y * 0.85 + mid_y * 0.15)),
            (tip_x, tip_y),
            (int(mid_b_x * 0.85 + mid_x * 0.15),
             int(mid_b_y * 0.85 + mid_y * 0.15)),
            (int(guard_b_x * 0.7 + hx * 0.3), int(guard_b_y * 0.7 + hy * 0.3)),
        ]
        _NS_hollowbane._poly(surface, _NS_hollowbane.PALETTE["blade_dark"],
                             inner_shape)

        # Blade highlight edge (top edge shines)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["blade_light"],
                         (guard_a_x, guard_a_y), (mid_a_x, mid_a_y), 1)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["blade_light"],
                         (mid_a_x, mid_a_y), (tip_x, tip_y), 1)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["blade_shine"],
                         (int(mid_a_x * 0.5 + tip_x * 0.5),
                          int(mid_a_y * 0.5 + tip_y * 0.5)),
                         (tip_x, tip_y), 1)

        # Blade central highlight strip
        strip_start_x = int(hx * 0.7 + tip_x * 0.3)
        strip_start_y = int(hy * 0.7 + tip_y * 0.3)
        strip_end_x = int(hx * 0.3 + tip_x * 0.7)
        strip_end_y = int(hy * 0.3 + tip_y * 0.7)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["blade_mid"],
                         (strip_start_x, strip_start_y),
                         (strip_end_x, strip_end_y), 1)

        # Tip highlight
        pygame.draw.rect(surface, _NS_hollowbane.PALETTE["blade_shine"],
                         (tip_x, tip_y, 1, 1))

        # HOLLOW FORM: black-red energy along blade
        if hollow_form:
            energy_pulse = math.sin(phase * 3) * 0.3 + 0.7
            for i in range(6):
                t = i / 5
                ex = int(hx + (tip_x - hx) * t)
                ey = int(hy + (tip_y - hy) * t)
                alpha = _NS_hollowbane._alpha(180 * energy_pulse)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["hollow_black"], alpha),
                                         (ex, ey), 3)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (ex, ey), 2)
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_hot"],
                                 (ex, ey, 1, 1))

        # HANDLE WRAP (red cloth wrapping)
        # Handle extends back from hand a bit
        handle_back_x = hx - int(math.cos(angle) * 6 * facing)
        handle_back_y = hy - int(math.sin(angle) * 6)

        pygame.draw.line(surface, _NS_hollowbane.PALETTE["wrap_dark"],
                         (hx, hy), (handle_back_x, handle_back_y), 3)
        pygame.draw.line(surface, _NS_hollowbane.PALETTE["wrap_mid"],
                         (hx, hy), (handle_back_x, handle_back_y), 2)

        # Wrap detail (diagonal lines)
        for i in range(3):
            t = (i + 1) / 4
            wx = int(hx + (handle_back_x - hx) * t)
            wy = int(hy + (handle_back_y - hy) * t)
            pygame.draw.rect(surface, _NS_hollowbane.PALETTE["wrap_light"],
                             (wx, wy, 1, 1))

        # Long red ribbon/chain hanging from pommel (Zangetsu's cloth)
        ribbon_sway = math.sin(phase * 0.7) * 4
        ribbon_end_x = handle_back_x + int(ribbon_sway)
        ribbon_end_y = handle_back_y + 14

        prev = (handle_back_x, handle_back_y)
        for i in range(1, 5):
            t = i / 4
            wave = math.sin(phase * 0.7 + t * 2) * 3
            rx = int(handle_back_x + (ribbon_end_x - handle_back_x) * t + wave)
            ry = int(handle_back_y + (ribbon_end_y - handle_back_y) * t)
            pygame.draw.line(surface, _NS_hollowbane.PALETTE["wrap_dark"],
                             prev, (rx, ry), 2)
            pygame.draw.line(surface, _NS_hollowbane.PALETTE["wrap_mid"],
                             prev, (rx, ry), 1)
            prev = (rx, ry)

    def _draw_sword_swing_trail(surface, boss, x, y, progress, hollow_form):
        """Orange energy trail during sword swing."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        t = (progress - 0.35) / 0.4

        # Arc of swing
        cx = x + facing * 10
        cy = y - 4

        # Multiple arc segments showing motion trail
        num_arcs = 8
        for i in range(num_arcs):
            arc_t = t - i * 0.06
            if arc_t < 0 or arc_t > 1:
                continue
            angle = math.pi * 1.05 - arc_t * 1.4
            radius = 32
            end_x = cx + int(math.cos(angle) * radius * facing)
            end_y = cy + int(math.sin(angle) * radius)

            alpha = _NS_hollowbane._alpha(220 - i * 25)
            width = max(1, 5 - i // 2)

            # Draw arc segment
            mid_angle = math.pi * 1.05 - (arc_t - 0.05) * 1.4
            mid_x = cx + int(math.cos(mid_angle) * radius * facing)
            mid_y = cy + int(math.sin(mid_angle) * radius)

            color = _NS_hollowbane.PALETTE["spirit_mid"]
            if hollow_form:
                color = _NS_hollowbane.PALETTE["hollow_black"]

            pygame.draw.line(surface, (*color, alpha),
                             (mid_x, mid_y), (end_x, end_y), width + 1)
            pygame.draw.line(surface, (*_NS_hollowbane.PALETTE["spirit_light"], alpha),
                             (mid_x, mid_y), (end_x, end_y), width)
            pygame.draw.line(surface, (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                             (mid_x, mid_y), (end_x, end_y), max(1, width - 2))

            # Sparks along trail
            for s in range(2):
                spark_offset = s * 3
                spark_x = end_x + int(math.sin(t * 5 + i + s) * 3)
                spark_y = end_y + int(math.cos(t * 5 + i + s) * 3)
                pygame.draw.rect(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_shine"], alpha),
                                 (spark_x, spark_y, 1, 1))

    # ============================================================
    # SPIRIT WISPS (ambient particles)
    # ============================================================
    def _draw_spirit_wisps(surface, cx, cy, phase, hollow_form, trail=False,
                            facing=1, intense=False):
        """Orange spirit particles floating around body."""
        strength = 1.5 if intense else 1.0

        num_wisps = 10 if intense else 7
        for i in range(num_wisps):
            wisp_t = (phase * 0.4 + i * 0.13) % 1.0
            angle = i * math.pi * 2 / num_wisps + phase * 0.3
            radius = 22 + int(math.sin(phase + i) * 6)
            wx = cx + int(math.cos(angle) * radius)
            wy = cy + int(math.sin(angle) * radius * 0.6) - int(wisp_t * 15)

            alpha = _NS_hollowbane._alpha(220 * (1 - wisp_t) * strength)
            if alpha <= 0:
                continue

            color_dark = _NS_hollowbane.PALETTE["spirit_dark"]
            color_mid = _NS_hollowbane.PALETTE["spirit_mid"]
            color_hot = _NS_hollowbane.PALETTE["spirit_hot"]

            if hollow_form:
                color_dark = _NS_hollowbane.PALETTE["hollow_black"]
                color_mid = _NS_hollowbane.PALETTE["hollow_purple"]

            _NS_hollowbane._aacircle(surface, (*color_dark, alpha), (wx, wy), 3)
            _NS_hollowbane._aacircle(surface, (*color_mid, alpha), (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*color_hot, alpha), (wx, wy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_shine"],
                             (wx, wy - 2, 1, 1))

        # Trail behind if moving
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = _NS_hollowbane._alpha(180 - i * 30)
                if alpha <= 0:
                    continue
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (sx, sy), max(2, 5 - i))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                         (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 2, 2, 170), (5, 6, 90, 12))
        pygame.draw.ellipse(shadow, (30, 15, 5, 110), (12, 8, 76, 8))
        surface.blit(shadow, (x - 50, y - 12))

    def _draw_spirit_aura(surface, x, y, phase, hollow_form):
        """Orange spirit energy aura around Ichigo."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        aura = pygame.Surface((180, 160), pygame.SRCALPHA)

        color1 = _NS_hollowbane.PALETTE["spirit_darkest"]
        color2 = _NS_hollowbane.PALETTE["spirit_dark"]
        color3 = _NS_hollowbane.PALETTE["spirit_mid"]

        if hollow_form:
            color1 = _NS_hollowbane.PALETTE["hollow_black"]
            color2 = _NS_hollowbane.PALETTE["hollow_dark"]
            color3 = _NS_hollowbane.PALETTE["hollow_purple"]

        # Outer aura
        for radius in range(80, 5, -5):
            alpha = _NS_hollowbane._alpha((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_hollowbane._aacircle(aura, (*color1, alpha), (90, 80), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_hollowbane._alpha((50 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_hollowbane._aacircle(aura, (*color2, alpha), (90, 80), radius)
        for radius in range(28, 5, -3):
            alpha = _NS_hollowbane._alpha((28 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_hollowbane._aacircle(aura, (*color3, alpha), (90, 80), radius)

        surface.blit(aura, (x - 90, y - 80))

        # Floating embers
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 30 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            ember_color = _NS_hollowbane.PALETTE["spirit_hot"]
            if hollow_form:
                ember_color = _NS_hollowbane.PALETTE["hollow_purple"]
            pygame.draw.rect(surface, ember_color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_shine"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill, hollow_form):
        """Ground ring under Ichigo."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75

        ring = pygame.Surface((140, 46), pygame.SRCALPHA)

        color1 = _NS_hollowbane.PALETTE["spirit_darkest"]
        color2 = _NS_hollowbane.PALETTE["spirit_dark"]
        color3 = _NS_hollowbane.PALETTE["spirit_mid"]

        if hollow_form:
            color1 = _NS_hollowbane.PALETTE["hollow_black"]
            color3 = _NS_hollowbane.PALETTE["hollow_purple"]

        pygame.draw.ellipse(ring, (*color1, 200), (5, 14, 130, 22), 3)
        pygame.draw.ellipse(ring, (*color2, 220), (14, 16, 112, 18), 2)
        pygame.draw.ellipse(ring, (*color3, 230), (25, 18, 90, 14), 1)

        # Rune marks
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 70 + int(math.cos(angle) * 38)
            y1 = 25 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 25 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_hollowbane.PALETTE["spirit_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_hollowbane.PALETTE["spirit_hot"],
                                        _NS_hollowbane._alpha(150 * pulse)),
                                (15, 8, 110, 32), 1)
        surface.blit(ring, (x - 70, y - 23))

    # ============================================================
    # SKILL: Q - GETSUGA TENSHO (crescent wave projectile)
    # ============================================================
    def _draw_getsuga_tensho(surface, boss, x, y, timer, phase):
        """Massive crescent moon-shaped spirit wave."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_hollowbane._target_position(boss, x, y)

        if progress < 0.25:
            # Charge up on sword
            t = progress / 0.25
            charge_x = x + facing * 25
            charge_y = y - 4
            cr = int(6 + t * 14)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_hollowbane._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_darkest"],
                                          alpha), (charge_x, charge_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_hollowbane._alpha(220 * (cr + 2 - r) / (cr + 2))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (charge_x, charge_y), r)
            _NS_hollowbane._aacircle(surface,
                                     _NS_hollowbane.PALETTE["spirit_mid"],
                                     (charge_x, charge_y), cr - 2)
            _NS_hollowbane._aacircle(surface,
                                     _NS_hollowbane.PALETTE["spirit_light"],
                                     (charge_x, charge_y), max(1, cr - 4))
            _NS_hollowbane._aacircle(surface,
                                     _NS_hollowbane.PALETTE["spirit_shine"],
                                     (charge_x, charge_y), max(1, cr - 6))

            # Sparks
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface,
                                 _NS_hollowbane.PALETTE["spirit_hot"],
                                 (sx, sy, 2, 2))
        else:
            # Launch crescent wave
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 32
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # CRESCENT SHAPE (moon)
            crescent_size = 22
            crescent_alpha = _NS_hollowbane._alpha(255 * (1 - t * 0.3))

            # Multiple crescent layers for depth
            for layer_i, (offset, alpha_mult, size_mult) in enumerate([
                (4, 0.4, 1.3),   # Outer glow
                (2, 0.7, 1.1),   # Middle
                (0, 1.0, 1.0),   # Core
            ]):
                cs = int(crescent_size * size_mult)
                actual_alpha = _NS_hollowbane._alpha(crescent_alpha * alpha_mult)

                # Draw crescent as two overlapping circles
                # Full circle
                colors = [
                    _NS_hollowbane.PALETTE["spirit_darkest"],
                    _NS_hollowbane.PALETTE["spirit_mid"],
                    _NS_hollowbane.PALETTE["spirit_light"],
                ]
                color = colors[min(layer_i, 2)]

                # Crescent shape using points
                crescent_pts = []
                num_pts = 16
                # Outer arc
                for i in range(num_pts):
                    ang = math.pi * 0.3 + i * math.pi * 1.4 / num_pts
                    px = bx + int(math.cos(ang) * cs * facing)
                    py = by + int(math.sin(ang) * cs)
                    crescent_pts.append((px, py))
                # Inner arc (cutout)
                for i in range(num_pts, -1, -1):
                    ang = math.pi * 0.3 + i * math.pi * 1.4 / num_pts
                    inner_cs = cs * 0.65
                    px = bx + int(math.cos(ang) * inner_cs * facing) + int(4 * facing)
                    py = by + int(math.sin(ang) * inner_cs)
                    crescent_pts.append((px, py))

                if len(crescent_pts) > 2:
                    try:
                        _NS_hollowbane._poly(surface, (*color, actual_alpha),
                                              crescent_pts)
                    except Exception:
                        pass

            # Inner bright core along crescent edge
            for i in range(12):
                ang = math.pi * 0.35 + i * math.pi * 1.3 / 12
                px = bx + int(math.cos(ang) * crescent_size * facing)
                py = by + int(math.sin(ang) * crescent_size)
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_hot"],
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_shine"],
                                 (px, py, 1, 1))

            # Comet trail behind
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_hollowbane._alpha(180 - i * 25)
                size = max(2, 8 - i)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (px, py), size)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                         (px, py), max(1, size - 2))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_light"], alpha),
                                         (px, py), max(1, size - 4))

            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_hollowbane._alpha(240 * (1 - st))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_darkest"],
                                          alpha), (tx, ty), radius + 3, 3)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                         (tx, ty), radius, 3)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_light"], alpha),
                                         (tx, ty), max(1, radius - 8), 2)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - ZANGETSU SLASH (wide horizontal slash)
    # ============================================================
    def _draw_zangetsu_slash(surface, boss, x, y, timer, phase):
        """Wide horizontal slash arc in front of Ichigo."""
        facing = boss.direction
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Slash from top to bottom in wide arc
        cx = x + facing * 15
        cy = y - 4

        if progress < 0.3:
            # Wind-up glow
            t = progress / 0.3
            glow_r = int(8 + t * 6)
            for r in range(glow_r + 3, 0, -1):
                alpha = _NS_hollowbane._alpha(180 * (glow_r + 3 - r) / (glow_r + 3) * t)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (cx, cy), r)
        else:
            # SLASH ARC
            t = (progress - 0.3) / 0.7
            arc_progress = min(1.0, t * 1.5)

            # Big wide arc slash
            radius = 55
            start_angle = -math.pi / 2.5  # top
            end_angle = math.pi / 2.5    # bottom
            current_angle = start_angle + (end_angle - start_angle) * arc_progress

            # Draw arc trail
            num_segments = 12
            for i in range(num_segments):
                seg_t = arc_progress - i * 0.06
                if seg_t < 0:
                    continue
                seg_angle = start_angle + (end_angle - start_angle) * seg_t
                seg_x = cx + int(math.cos(seg_angle) * radius * facing)
                seg_y = cy + int(math.sin(seg_angle) * radius)

                prev_t = arc_progress - (i + 1) * 0.06
                if prev_t < 0:
                    prev_t = 0
                prev_angle = start_angle + (end_angle - start_angle) * prev_t
                prev_x = cx + int(math.cos(prev_angle) * radius * facing)
                prev_y = cy + int(math.sin(prev_angle) * radius)

                alpha = _NS_hollowbane._alpha(240 - i * 20)
                width = max(2, 7 - i)

                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_darkest"], alpha),
                                 (prev_x, prev_y), (seg_x, seg_y), width + 2)
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                 (prev_x, prev_y), (seg_x, seg_y), width + 1)
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                 (prev_x, prev_y), (seg_x, seg_y), width)
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_light"], alpha),
                                 (prev_x, prev_y), (seg_x, seg_y), max(1, width - 2))
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                 (prev_x, prev_y), (seg_x, seg_y), max(1, width - 4))

                # Sparks
                for s in range(3):
                    spark_x = seg_x + int(math.sin(t * 6 + i + s) * 4)
                    spark_y = seg_y + int(math.cos(t * 6 + i + s) * 4)
                    pygame.draw.rect(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_shine"], alpha),
                                     (spark_x, spark_y, 2, 2))

            # Leading edge (brightest point at current angle)
            lead_x = cx + int(math.cos(current_angle) * radius * facing)
            lead_y = cy + int(math.sin(current_angle) * radius)
            for r in range(6, 0, -1):
                alpha = _NS_hollowbane._alpha(200 * (6 - r) / 6)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                         (lead_x, lead_y), r)
            pygame.draw.rect(surface, _NS_hollowbane.PALETTE["white"],
                             (lead_x, lead_y, 2, 2))

    # ============================================================
    # SKILL: E - SOUL REPULSE (spiritual pressure burst)
    # ============================================================
    def _draw_repulse_ground(surface, boss, x, y, timer, phase):
        """Expanding ring on ground."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Expanding rings
        for i in range(3):
            ring_t = (progress * 2 - i * 0.2) % 1.0
            if ring_t < 0 or ring_t > 1:
                continue
            r = int(15 + ring_t * 60)
            alpha = _NS_hollowbane._alpha(200 * (1 - ring_t))
            pygame.draw.ellipse(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                 (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                 (x - r + 2, y + 40 - r // 3 + 1,
                                  r * 2 - 4, r * 2 // 3 - 2), 2)
            pygame.draw.ellipse(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_light"], alpha),
                                 (x - r + 5, y + 40 - r // 3 + 2,
                                  r * 2 - 10, r * 2 // 3 - 4), 1)

    def _draw_repulse_foreground(surface, boss, x, y, timer, phase):
        """Radial burst of spiritual pressure."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        cx = x + facing * 12
        cy = y - 2

        if progress < 0.2:
            # Charge
            t = progress / 0.2
            cr = int(4 + t * 10)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_hollowbane._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (cx, cy), r)
        else:
            # BURST - many rays outward
            t = (progress - 0.2) / 0.8
            burst_r = int(40 + t * 50)

            # Central bright core
            core_r = int(15 * (1 - t * 0.5))
            for r in range(core_r + 3, 0, -1):
                alpha = _NS_hollowbane._alpha(240 * (core_r + 3 - r) / (core_r + 3) * (1 - t * 0.5))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                         (cx, cy), r)
            _NS_hollowbane._aacircle(surface,
                                     _NS_hollowbane.PALETTE["spirit_mid"],
                                     (cx, cy), max(1, core_r - 2))
            _NS_hollowbane._aacircle(surface,
                                     _NS_hollowbane.PALETTE["spirit_light"],
                                     (cx, cy), max(1, core_r - 4))
            _NS_hollowbane._aacircle(surface,
                                     _NS_hollowbane.PALETTE["spirit_shine"],
                                     (cx, cy), max(1, core_r - 6))

            # Rays shooting outward
            num_rays = 16
            for i in range(num_rays):
                angle = i * math.pi * 2 / num_rays + phase * 0.5
                ray_len = burst_r + int(math.sin(phase * 4 + i) * 8)
                ex = cx + int(math.cos(angle) * ray_len)
                ey = cy + int(math.sin(angle) * ray_len)

                alpha = _NS_hollowbane._alpha(240 * (1 - t))
                # Thick ray
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_darkest"], alpha),
                                 (cx, cy), (ex, ey), 4)
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                 (cx, cy), (ex, ey), 3)
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                 (cx, cy), (ex, ey), 2)
                pygame.draw.line(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                 (cx, cy), (ex, ey), 1)

                # Tip spark
                pygame.draw.rect(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_shine"], alpha),
                                 (ex, ey, 2, 2))

            # Wave ring
            wave_r = int(burst_r * 0.8)
            wave_alpha = _NS_hollowbane._alpha(200 * (1 - t))
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_light"], wave_alpha),
                                     (cx, cy), wave_r, 2)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_hot"], wave_alpha),
                                     (cx, cy), wave_r - 1, 1)

    # ============================================================
    # SKILL: R - HOLLOW MASK (transformation buff)
    # ============================================================
    def _draw_hollow_mask_fx(surface, boss, x, y, timer, phase):
        """FX around Ichigo when hollow mask is active - black energy tendrils."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Black energy tendrils rising
        for i in range(12):
            angle = phase * 0.6 + i * math.pi / 6
            radius_out = 25 + int(math.sin(phase * 2 + i) * 10)
            wx = x + int(math.cos(angle) * radius_out)
            wy = y + int(math.sin(angle) * radius_out * 0.6)

            # Tendril curling upward
            for j in range(4):
                t = j / 4
                curl_x = wx + int(math.sin(phase * 3 + i + t * 3) * 5)
                curl_y = wy - int(t * 15)
                alpha = _NS_hollowbane._alpha(220 * (1 - t) * pulse)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["hollow_black"], alpha),
                                         (curl_x, curl_y), max(1, 3 - j))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["hollow_purple"], alpha),
                                         (curl_x, curl_y), max(1, 2 - j))
                pygame.draw.rect(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                 (curl_x, curl_y, 1, 1))

        # Screaming aura pulse rings
        for ring_i in range(2):
            ring_t = (phase * 0.4 + ring_i * 0.5) % 1.0
            ring_r = int(40 + ring_t * 30)
            ring_alpha = _NS_hollowbane._alpha(180 * (1 - ring_t))
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["hollow_black"], ring_alpha),
                                     (x, y), ring_r, 2)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_dark"], ring_alpha),
                                     (x, y), ring_r - 1, 1)

        # Set hollow form flag on boss
        boss._hb_hollow_form = True

    # ============================================================
    # SKILL: D - BANKAI TENSA ZANGETSU (ultimate)
    # ============================================================
    def _draw_bankai_ground(surface, boss, x, y, timer, phase):
        """Massive circular energy field on ground during Bankai."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple massive rings
        for i in range(4):
            ring_r = int(30 + i * 20 + math.sin(phase * 2 + i) * 5)
            alpha = _NS_hollowbane._alpha(220 - i * 40)
            pygame.draw.ellipse(surface,
                                 (*_NS_hollowbane.PALETTE["hollow_black"], alpha),
                                 (x - ring_r, y + 40 - ring_r // 3,
                                  ring_r * 2, ring_r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_dark"], alpha),
                                 (x - ring_r + 3, y + 40 - ring_r // 3 + 2,
                                  ring_r * 2 - 6, ring_r * 2 // 3 - 4), 2)

        # Ground cracks/runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = x + int(math.cos(angle) * 20)
            y1 = y + 40 + int(math.sin(angle) * 8)
            x2 = x + int(math.cos(angle) * 60)
            y2 = y + 40 + int(math.sin(angle) * 20)
            pygame.draw.line(surface,
                             _NS_hollowbane.PALETTE["spirit_mid"],
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(surface,
                             _NS_hollowbane.PALETTE["spirit_hot"],
                             (x1, y1), (x2, y2), 1)

    def _draw_bankai_foreground(surface, boss, x, y, timer, phase):
        """Bankai ultimate - massive slash across screen, chains + energy."""
        facing = boss.direction
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_hollowbane._target_position(boss, x, y)

        if progress < 0.3:
            # WIND-UP: massive energy gathering, chains appearing
            t = progress / 0.3
            gather_r = int(10 + t * 20)

            # Energy spiral
            for i in range(20):
                spiral_t = i / 20 + phase * 0.5
                spiral_angle = spiral_t * math.pi * 4
                spiral_r = int((1 - spiral_t) * gather_r)
                sx = x + int(math.cos(spiral_angle) * spiral_r)
                sy = y + int(math.sin(spiral_angle) * spiral_r)
                alpha = _NS_hollowbane._alpha(220 * t)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["hollow_black"], alpha),
                                         (sx, sy), 3)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["spirit_mid"], alpha),
                                         (sx, sy), 2)
                pygame.draw.rect(surface,
                                 _NS_hollowbane.PALETTE["spirit_shine"],
                                 (sx, sy, 1, 1))

            # Chains from ground
            for i in range(6):
                chain_angle = i * math.pi / 3 + phase * 0.2
                chain_x = x + int(math.cos(chain_angle) * (30 * t))
                chain_y = y + 30 - int(t * 40)

                # Chain links
                for link in range(4):
                    lx = chain_x + int(math.sin(phase + i + link) * 2)
                    ly = chain_y + link * 4
                    alpha = _NS_hollowbane._alpha(220 * t)
                    _NS_hollowbane._aacircle(surface,
                                             (*_NS_hollowbane.PALETTE["blade_dark"],
                                              alpha), (lx, ly), 2)
                    _NS_hollowbane._aacircle(surface,
                                             (*_NS_hollowbane.PALETTE["blade_light"],
                                              alpha), (lx, ly), 1)

        elif progress < 0.6:
            # MASSIVE SLASH across screen
            t = (progress - 0.3) / 0.3
            intensity = math.sin(t * math.pi)

            # Giant crescent slash
            slash_cx = x + facing * 20
            slash_cy = y - 10
            slash_r = int(70 + t * 20)

            # Multi-layer massive crescent
            for layer_i, (offset_mult, alpha_mult) in enumerate([
                (1.3, 0.4), (1.15, 0.7), (1.0, 1.0),
            ]):
                actual_r = int(slash_r * offset_mult)
                actual_alpha = _NS_hollowbane._alpha(255 * intensity * alpha_mult)

                colors = [
                    _NS_hollowbane.PALETTE["hollow_black"],
                    _NS_hollowbane.PALETTE["spirit_dark"],
                    _NS_hollowbane.PALETTE["spirit_mid"],
                ]
                color = colors[min(layer_i, 2)]

                crescent_pts = []
                num_pts = 20
                for i in range(num_pts):
                    ang = math.pi * 0.2 + i * math.pi * 1.6 / num_pts
                    px = slash_cx + int(math.cos(ang) * actual_r * facing)
                    py = slash_cy + int(math.sin(ang) * actual_r)
                    crescent_pts.append((px, py))
                for i in range(num_pts, -1, -1):
                    ang = math.pi * 0.2 + i * math.pi * 1.6 / num_pts
                    inner_r = actual_r * 0.6
                    px = slash_cx + int(math.cos(ang) * inner_r * facing) + int(6 * facing)
                    py = slash_cy + int(math.sin(ang) * inner_r)
                    crescent_pts.append((px, py))

                if len(crescent_pts) > 2:
                    try:
                        _NS_hollowbane._poly(surface, (*color, actual_alpha),
                                              crescent_pts)
                    except Exception:
                        pass

            # Bright edge highlights
            for i in range(15):
                ang = math.pi * 0.25 + i * math.pi * 1.5 / 15
                px = slash_cx + int(math.cos(ang) * slash_r * facing)
                py = slash_cy + int(math.sin(ang) * slash_r)
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_hot"],
                                 (px, py, 3, 3))
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["spirit_shine"],
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, _NS_hollowbane.PALETTE["white"],
                                 (px, py, 1, 1))

            # Sparks flying everywhere
            for i in range(30):
                spark_ang = i * math.pi / 15 + phase * 2
                spark_r = int(slash_r * (0.5 + (i % 3) * 0.3))
                sx = slash_cx + int(math.cos(spark_ang) * spark_r * facing)
                sy = slash_cy + int(math.sin(spark_ang) * spark_r)
                alpha = _NS_hollowbane._alpha(240 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_hot"], alpha),
                                 (sx, sy, 2, 2))
        else:
            # AFTERMATH: lingering energy + chains fading
            t = (progress - 0.6) / 0.4

            # Fading chains around
            for i in range(8):
                chain_angle = i * math.pi / 4 + phase * 0.3
                chain_r = 40 + int(math.sin(phase + i) * 8)
                chain_x = x + int(math.cos(chain_angle) * chain_r)
                chain_y = y + int(math.sin(chain_angle) * chain_r * 0.5)

                alpha = _NS_hollowbane._alpha(200 * (1 - t))
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["blade_dark"], alpha),
                                         (chain_x, chain_y), 3)
                _NS_hollowbane._aacircle(surface,
                                         (*_NS_hollowbane.PALETTE["blade_light"], alpha),
                                         (chain_x, chain_y), 2)

            # Impact aftermath at target
            impact_r = int(20 + t * 40)
            impact_alpha = _NS_hollowbane._alpha(220 * (1 - t))
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["hollow_black"],
                                      impact_alpha), (tx, ty), impact_r + 3, 3)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_mid"],
                                      impact_alpha), (tx, ty), impact_r, 3)
            _NS_hollowbane._aacircle(surface,
                                     (*_NS_hollowbane.PALETTE["spirit_light"],
                                      impact_alpha), (tx, ty), max(1, impact_r - 6), 2)

            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_hollowbane.PALETTE["spirit_hot"], impact_alpha),
                                 (ex, ey, 2, 2))


# ====================================================================================================
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ====================================================================================================
def draw_obanai(surface, boss, x, y):
    """Entry point obanai."""
    return _NS_obanai.draw_obanai(surface, boss, x, y)

def draw_sanguire(surface, boss, x, y):
    """Entry point sanguire."""
    return _NS_sanguire.draw_sanguire(surface, boss, x, y)

def draw_sasori(surface, boss, x, y):
    """Entry point sasori."""
    return _NS_sasori.draw_sasori(surface, boss, x, y)

def draw_hollowbane(surface, boss, x, y):
    """Entry point hollowbane."""
    return _NS_hollowbane.draw_hollowbane(surface, boss, x, y)
