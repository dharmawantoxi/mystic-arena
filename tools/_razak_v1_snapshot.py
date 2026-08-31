#!/usr/bin/env python3
"""SNAPSHOT renderer razak v1 (sebelum upgrade Pixel Masterwork v2).

Dibuat otomatis sebelum rewrite `_NS_razak` di bosses/level2.py.
Dipakai tools/_audit_razak_v2.py untuk lembar before/after -
jangan diedit manual; kalau perlu regenerasi, ambil dari git history.
"""
import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None


class _NS_razak:
    """Namespace razak - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    # Lapisan mahal yang hasilnya identik antar-frame di-cache supaya
    # render penuh tetap murah. Aura/denyut via set_alpha (blit NORMAL
    # menghormati alpha; blit ADD tidak), shadow cache + reaktif, flame
    # dikunci per (size, phase-bucket). Daftar rect shadow direkam saat
    # hurt-flash supaya flash badan tidak ikut menyalakan bayangan tanah.
    _shadow_cache = None
    _aura_cache = None
    _flame_cache = {}
    _flash_buf = None
    _record_shadow = None
    _body_buf = None        # buffer badan untuk outline+lighting

    # ---------------------------------------------------------------------------
    # HD Palette - Fire orange / green goblin / red bat mount
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Goblin skin - green
        "gob_darkest":    (25,  45,  20),
        "gob_dark":       (55,  95,  38),
        "gob_mid":        (95, 145,  55),
        "gob_light":      (140, 190, 78),
        "gob_high":       (185, 225, 120),
        "gob_shine":      (225, 250, 175),

        # Bat/dragon mount - red-orange
        "bat_darkest":    (35,  15,  10),
        "bat_dark":       (95,  32,  18),
        "bat_mid":        (155, 62,  25),
        "bat_light":      (210, 95,  38),
        "bat_high":       (240, 140, 65),
        "bat_shine":      (255, 180, 100),

        # Bat belly (lighter)
        "belly_dark":     (105, 55,  25),
        "belly_mid":      (170, 105, 55),
        "belly_light":    (215, 155, 85),

        # Wing membrane
        "wing_darkest":   (30,  12,   8),
        "wing_dark":      (75,  25,  15),
        "wing_mid":       (135, 45,  22),
        "wing_light":     (190, 78,  35),

        # Leather / gear
        "leather_darkest": (22, 14,  8),
        "leather_dark":   (50,  32,  18),
        "leather_mid":    (95,  62,  32),
        "leather_light":  (150, 100, 55),

        # Metal
        "metal_darkest":  (18,  15,  18),
        "metal_dark":     (48,  42,  48),
        "metal_mid":      (95,  88,  95),
        "metal_light":    (160, 152, 165),
        "metal_shine":    (225, 220, 225),

        # Brass / bronze (gun parts)
        "brass_dark":     (80,  50,  15),
        "brass_mid":      (155, 108, 40),
        "brass_light":    (210, 170, 80),
        "brass_shine":    (250, 220, 140),

        # Fire - orange/yellow
        "fire_darkest":   (55,  12,   5),
        "fire_dark":      (135, 30,   8),
        "fire_mid":       (215, 80,  15),
        "fire_bright":    (255, 130, 30),
        "fire_hot":       (255, 180, 60),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 250, 210),

        # Blue (goggles)
        "blue_dark":      (15,  35,  75),
        "blue_mid":       (45,  95, 165),
        "blue_light":     (95, 165, 230),
        "blue_shine":     (170, 220, 255),

        # Eyes
        "eye_dark":       (15,  25,   8),
        "eye_bright":     (255, 220, 100),
        "eye_hot":        (255, 250, 200),

        # Teeth / claws
        "bone_dark":      (110, 95,  70),
        "bone_light":     (220, 210, 175),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_razak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_razak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_razak._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])), width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3],
                         (rect[0], rect[1], int(rect[2]), int(rect[3])),
                         border_radius=border_radius)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # FIRE PARTICLE / FLAME DRAWING
    # ---------------------------------------------------------------------------
    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        """Draw a single flame with layered fire colors.

        ORIGINAL-MAX: flame per (size, phase-bucket, alpha-bucket) di-cache
        ke sprite piksel-identik; gerak api yang besar (amplitudo) tetap
        kontinu, hanya wobble kecil sub-piksel yang di-kuantisasi ke bucket
        - bukan cache bucket untuk gerak besar seperti helix dulu.
        """
        NS = _NS_razak
        pb = int(phase * 4) % 8
        ab = int(alpha / 32) * 32
        key = (int(size), pb, ab)
        spr = NS._flame_cache.get(key)
        if spr is None:
            height = int(size * 2)
            spr = pygame.Surface((int(size * 2) + 6, height + 4),
                                 pygame.SRCALPHA)
            base = int(size) + 3
            # Sprite api menunjuk ke ATAS: baris h=0 (terlebar) di dasar
            # (sprite-y height+1), puncak h=height-1 di atas (sprite-y 2).
            for h in range(height):
                t = h / max(1, height)
                w = int(size * (1 - t * 0.7))
                fx = base + int(math.sin((pb / 4.0) * 3 + t * 4) * 2)
                fy = height + 1 - h
                a = int(ab * (1 - t * 0.4))
                if t < 0.3:
                    color = NS.PALETTE["fire_darkest"]
                elif t < 0.55:
                    color = NS.PALETTE["fire_mid"]
                elif t < 0.8:
                    color = NS.PALETTE["fire_bright"]
                else:
                    color = NS.PALETTE["fire_hot"]
                NS._aacircle(spr, (*color, a), (fx, fy), max(1, w))
            # Core menyala: original di cy-height//3 & cy-height//4 -> sprite
            # y = (world_y - blit_y) = (height+1) - height//3 dsb.
            NS._aacircle(spr, (*NS.PALETTE["fire_glow"], ab),
                         (base, height + 1 - height // 3), size // 2)
            NS._aacircle(spr, (*NS.PALETTE["fire_white"], ab),
                         (base, height + 1 - height // 4), max(1, size // 4))
            NS._flame_cache[key] = spr
        # base (h=0, sprite-y height+1) dipatok ke cy
        surface.blit(spr, (cx - (spr.get_width() // 2), cy - (height + 1)))


    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha), (cx, cy), size + 1)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (cx, cy), size)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], min(255, alpha)), (cx, cy), 1)


    def _draw_fire_ground_patch(surface, cx, cy, radius, phase, alpha=255):
        """Ground fire patch - Sticky Napalm effect."""
        # Base scorch
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_darkest"], int(alpha * 0.9)),
                 (cx - radius, cy - radius // 3, radius * 2, radius // 1.5))
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_dark"], int(alpha * 0.8)),
                 (cx - radius + 3, cy - radius // 3 + 2,
                  radius * 2 - 6, radius // 1.5 - 4))

        # Flames on top
        flame_count = max(3, radius // 4)
        for i in range(flame_count):
            angle = i * math.pi * 2 / flame_count + phase * 0.3
            r = radius - 4
            fx = cx + int(math.cos(angle) * r)
            fy = cy + int(math.sin(angle) * r // 3)
            size = 3 + (i % 3)
            _NS_razak._draw_flame(surface, fx, fy, size, phase + i, alpha=alpha)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class NapalmProjectile:
        """Sticky napalm — arcing fireball."""
        def __init__(self, sx, sy, tx, ty, arc_height=40):
            self.start_x = float(sx)
            self.start_y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.arc_height = arc_height
            self.alive = True
            self.age = 0
            self.max_age = 40
            self.x = float(sx)
            self.y = float(sy)
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.3
            t = self.age / self.max_age
            if t >= 1.0:
                self.alive = False
                self.x, self.y = self.tx, self.ty
                return
            self.x = self.start_x + (self.tx - self.start_x) * t
            # Parabolic arc
            arc = -4 * self.arc_height * t * (1 - t)
            self.y = self.start_y + (self.ty - self.start_y) * t + arc
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)

        def draw(self, surface, phase):
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(60 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha), (tx, ty), r + 2)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (tx, ty), r)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (tx, ty), max(1, r - 1))
            if self.alive:
                px, py = int(self.x), int(self.y)
                # Fireball
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], 200), (px, py), 8)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_mid"], 220), (px, py), 6)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], 240), (px, py), 5)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], 255), (px, py), 3)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (px, py), 2)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255), (px - 1, py - 1), 1)
                # Flame licks
                for i in range(3):
                    angle = self.spin + i * math.pi * 2 / 3
                    fx = px + int(math.cos(angle) * 5)
                    fy = py + int(math.sin(angle) * 5)
                    _NS_razak._draw_ember(surface, fx, fy, 2, 220)


    class NapalmPatch:
        """Persistent burning ground patch."""
        def __init__(self, x, y, radius=25, life=90):
            self.x = x
            self.y = y
            self.radius = radius
            self.age = 0
            self.life = life
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            t = self.age / self.life
            # Grow then fade
            if t < 0.15:
                r = int(self.radius * (t / 0.15))
                alpha = int(255 * (t / 0.15))
            elif t < 0.7:
                r = self.radius
                alpha = 255
            else:
                r = self.radius
                alpha = int(255 * (1 - (t - 0.7) / 0.3))
            if r <= 0 or alpha <= 0:
                return
            _NS_razak._draw_fire_ground_patch(surface, self.x, self.y, r, phase, alpha=alpha)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_razak_last_x"):
            boss._razak_last_x = boss.x
            boss._razak_last_y = boss.y
            return False
        dx = abs(boss.x - boss._razak_last_x)
        dy = abs(boss.y - boss._razak_last_y)
        boss._razak_last_x = boss.x
        boss._razak_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_razak_prev_timer", 0))
        active = bool(getattr(boss, "_razak_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._razak_attack_active = True
            boss._razak_attack_frame = 0
            active = True
        elif active:
            boss._razak_attack_frame = int(getattr(boss, "_razak_attack_frame", 0)) + 1
            if boss._razak_attack_frame > cooldown:
                boss._razak_attack_active = False
                boss._razak_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._razak_attack_active = False
            boss._razak_attack_frame = 0
            active = False

        boss._razak_prev_timer = timer
        boss._razak_attack_progress = (
            min(1.0, getattr(boss, "_razak_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        if not hasattr(boss, "_razak_patches"):
            boss._razak_patches = []

        for proj in boss._razak_projectiles:
            proj.update()
            if not proj.alive:
                # Spawn napalm patch at landing point
                boss._razak_patches.append(
                    _NS_razak.NapalmPatch(int(proj.x), int(proj.y), radius=28, life=100))
            proj.draw(surface, phase)
        boss._razak_projectiles = [p for p in boss._razak_projectiles
                                    if p.alive or p.age < 3]

        # Draw patches BEHIND everything (but they're called from foreground here)
        for patch in boss._razak_patches:
            patch.update()
            patch.draw(surface, phase)
        boss._razak_patches = [p for p in boss._razak_patches if p.alive]


    def _spawn_napalm(boss, sx, sy, tx, ty, arc_height=40):
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        boss._razak_projectiles.append(
            _NS_razak.NapalmProjectile(sx, sy, tx, ty, arc_height=arc_height))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_razak(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_razak._detect_moving(boss)
        _NS_razak._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_razak_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # Background
        _NS_razak._draw_fire_aura(surface, x, y, pulse, active_skill)

        # Ground patches (behind character)
        if hasattr(boss, "_razak_patches"):
            for patch in boss._razak_patches:
                patch.draw(surface, pulse)

        # Skill ground effects
        if active_skill == "r":
            _NS_razak._draw_firestorm_ground(surface, boss, x, y, skill_timer, pulse)

        # PERTAGAS: gelombang kejut aktivasi skill (12 frame pertama)
        if active_skill in ("q", "w", "r"):
            dur = {"q": 40, "w": 50, "r": 90}[active_skill]
            age = dur - skill_timer
            if 0 <= age < 12:
                _NS_razak._draw_shockwave(surface, x, y + 52, age, 12,
                                          _NS_razak.PALETTE["fire_hot"],
                                          _NS_razak.PALETTE["fire_glow"])

        # ORIGINAL-MAX hurt flash: saat kena hit, pose dirender ke buffer,
        # lalu siluet badannya dibanjiri putih-hangat. Bayangan tanah TIDAK
        # ikut menyala (rect shadow direkam dan dikeluarkan dari flash).
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            B = _NS_razak
            if B._flash_buf is None:
                B._flash_buf = pygame.Surface((240, 260), pygame.SRCALPHA)
            B._flash_buf.fill((0, 0, 0, 0))
            B._record_shadow = []
            _tgt, _tx, _ty = B._flash_buf, 120, 135

        # Character
        if active_skill == "e":
            _NS_razak._draw_razak_dashing(_tgt, boss, _tx, _ty, skill_timer, pulse)
        elif attacking:
            _NS_razak._draw_razak_attack(_tgt, boss, _tx, _ty)
        elif moving:
            _NS_razak._draw_razak_walk(_tgt, boss, _tx, _ty)
        else:
            _NS_razak._draw_razak_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            B = _NS_razak
            surface.blit(B._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(B._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (B._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            B._record_shadow = None

        # Update / draw projectiles
        _NS_razak._manage_projectiles_no_patches(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_razak._draw_sticky_napalm(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_razak._draw_flamebreak(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_razak._draw_firestorm(surface, boss, x, y, skill_timer, pulse)


    def _draw_shockwave(surface, x, y, age, total, c1, c2):
        """Gelombang kejut aktivasi skill - 12 frame pertama, membesar &
        memudar. Ring radial target-anchored di tanah (y = titik tanah)."""
        t = age / float(total)
        ease = 1 - (1 - t) ** 2
        r = int(14 + ease * 60)
        a = max(0, min(255, int(235 * (1 - t))))
        pygame.draw.ellipse(surface, (*c1, a),
                            (x - r, y - r // 3, r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface, (*c2, a),
                            (x - r // 2, y - r // 6, r, r // 3), 1)
        # lingkaran dalam yang menyala
        ri = max(3, r // 2)
        _NS_razak._aacircle(surface, (*c1, int(a * 0.8)),
                            (x, y - (r // 6)), ri)


    def _manage_projectiles_no_patches(boss, surface, phase):
        """Same as manage_projectiles but patches are drawn separately (before character)."""
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        if not hasattr(boss, "_razak_patches"):
            boss._razak_patches = []

        for proj in boss._razak_projectiles:
            proj.update()
            if not proj.alive and proj.age > 0:
                # Spawn napalm patch at landing point
                boss._razak_patches.append(
                    _NS_razak.NapalmPatch(int(proj.tx), int(proj.ty), radius=28, life=100))
                proj.age = -1  # prevent re-spawn
            if proj.age >= 0:
                proj.draw(surface, phase)
        boss._razak_projectiles = [p for p in boss._razak_projectiles
                                    if p.alive]

        # Update patches (drawing was done earlier)
        for patch in boss._razak_patches:
            patch.update()
        boss._razak_patches = [p for p in boss._razak_patches if p.alive]


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_razak_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 3)  # Bat hovers with bigger bob
        _NS_razak._draw_shadow(surface, x, y + 52)
        _NS_razak._draw_fire_wisps(surface, x, y + 38, boss.pulse)
        _NS_razak._draw_razak_full(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_razak_walk(surface, boss, x, y):
        phase = boss.pulse * 2.5
        bob = int(math.sin(phase * 1.2) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_razak._draw_shadow(surface, x + sway, y + 52)
        _NS_razak._draw_fire_wisps(surface, x + sway, y + 38, phase, trail=True,
                         facing=boss.direction)
        _NS_razak._draw_razak_full(surface, x + sway, y + bob, boss.direction, phase, "walk")


    def _draw_razak_attack(surface, boss, x, y):
        progress = getattr(boss, "_razak_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        lunge = int(math.sin(progress * math.pi) * 4) * boss.direction

        # ─── Fireball serangan biasa ───
        # Razak itu unit RANGED (range 130) tapi dulu animasi
        # serangannya cuma ayunan machete tanpa proyektil apa pun,
        # jadi damage terasa datang entah dari mana. Spawn fireball
        # kecil di puncak ayunan, pola sama seperti boss ranged lain.
        if 0.34 < progress < 0.46 and not getattr(
                boss, "_razak_proj_spawned", False):
            tx, ty = _NS_razak._target_position(boss, x, y)
            sx = x + 20 * boss.direction + lunge
            sy = y + bob - 6
            _NS_razak._spawn_napalm(boss, sx, sy, tx, ty, arc_height=22)
            boss._razak_proj_spawned = True
        if progress < 0.12 or progress > 0.9:
            boss._razak_proj_spawned = False

        _NS_razak._draw_shadow(surface, x + lunge, y + 52)
        _NS_razak._draw_fire_wisps(surface, x + lunge, y + 38, boss.pulse, intense=True)
        _NS_razak._draw_razak_full(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                         "attack", progress)
        _NS_razak._draw_machete_swing_arc(surface, x + lunge, y + bob, boss.direction, progress)


    def _draw_razak_dashing(surface, boss, x, y, timer, phase):
        """Firefly dash - bat flies forward with flame trail."""
        bob = int(math.sin(phase * 1.5) * 2)
        _NS_razak._draw_shadow(surface, x, y + 52)
        _NS_razak._draw_fire_wisps(surface, x, y + 38, phase, intense=True)

        # Motion blur behind (afterimage langsung, tanpa outline/lighting)
        for i in range(4):
            offset = (i + 1) * 8 * -boss.direction
            alpha = int(150 - i * 30)
            temp = pygame.Surface((160, 160), pygame.SRCALPHA)
            _NS_razak._draw_razak_full_raw(temp, 80, 80, boss.direction, phase, "dash")
            temp.set_alpha(alpha)
            surface.blit(temp, (x + offset - 80, y + bob - 80))

        _NS_razak._draw_razak_full(surface, x, y + bob, boss.direction, phase, "dash")


    # ===================================================================
    # FULL COMPOSITE
    # ===================================================================
    def _draw_razak_full_raw(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw bat mount + goblin rider (langsung, tanpa outline/lighting)."""
        # Wings behind body first
        _NS_razak._draw_bat_wings(surface, cx, cy, facing, phase, action)

        # Bat body
        _NS_razak._draw_bat_body(surface, cx, cy + 5, facing, phase)

        # Bat head
        _NS_razak._draw_bat_head(surface, cx + 18 * facing, cy + 3, facing, phase)

        # Goblin rider on top of bat
        _NS_razak._draw_goblin_rider(surface, cx - 2, cy - 12, facing, phase, action,
                           attack_progress)

        # Front wings overlay (bring wings forward if attack)
        if action == "attack":
            _NS_razak._draw_bat_wings_front(surface, cx, cy, facing, phase)


    def _draw_razak_full(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Komposit ORIGINAL-MAX: badan dirender ke buffer tetap, di-crop
        rapat, diberi outline siluet gelap 1 px + pass pencahayaan murah
        (rim/shade), lalu di-blit ke posisi dunia yang sama. Seni per
        bagian tidak diubah - buffer hanya menampung hasil pose."""
        NS = _NS_razak
        B = 200
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((B, B), pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_razak_full_raw(buf, B // 2, B // 2, facing, phase, action,
                                attack_progress)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        # Blit origin: titik jangkar badan di buffer (B//2,B//2) harus
        # jatuh di posisi dunia (cx,cy) -> ox = cx - (B//2) + used.left.
        ox = int(cx) - (B // 2) + used.left
        oy = int(cy) - (B // 2) + used.top
        # Outline siluet (konvensi level1: edge gelap 1 px, 4 arah)
        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        # Pass pencahayaan (rim kiri-atas + shade terminator) pada crop rapat
        if _lighting is not None:
            _lighting.apply_to_rig(sub, rim_add=(34, 26, 22), shade_mul=168)
        surface.blit(sub, (ox, oy))


    def _draw_bat_wings(surface, cx, cy, facing, phase, action):
        """Bat mount wings (background, spread out)."""
        flap = math.sin(phase * (2.5 if action == "walk" else 1.2)) * 0.35
        if action == "dash":
            flap = math.sin(phase * 4) * 0.5

        for side in (-1, 1):
            wing_base_x = cx + side * 8
            wing_base_y = cy - 2
            wing_tip_x = cx + side * (32 + int(math.cos(flap) * 6))
            wing_tip_y = cy - 15 + int(math.sin(flap) * 8)
            wing_mid_x = cx + side * 24
            wing_mid_y = cy - 6 + int(math.sin(flap) * 6)
            wing_low_x = cx + side * 20
            wing_low_y = cy + 12 + int(math.sin(flap) * 3)

            # Wing membrane (large triangle)
            wing_shape = [
                (wing_base_x, wing_base_y),
                (wing_tip_x, wing_tip_y),
                (cx + side * 30, cy - 4 + int(math.sin(flap) * 5)),
                (wing_mid_x, wing_mid_y),
                (cx + side * 27, cy + 3 + int(math.sin(flap) * 4)),
                (wing_low_x, wing_low_y),
                (cx + side * 4, cy + 8),
            ]

            # Shadow
            _NS_razak._poly(surface, _NS_razak.PALETTE["shadow_deep"],
                  [(p[0] + 2, p[1] + 2) for p in wing_shape])
            _NS_razak._poly(surface, _NS_razak.PALETTE["wing_darkest"], wing_shape)
            # Inner membrane (lighter)
            inner_shape = [
                (wing_base_x + side, wing_base_y + 1),
                (wing_tip_x - side * 2, wing_tip_y + 1),
                (wing_mid_x - side, wing_mid_y),
                (wing_low_x - side, wing_low_y - 1),
                (cx + side * 4, cy + 7),
            ]
            _NS_razak._poly(surface, _NS_razak.PALETTE["wing_dark"], inner_shape)
            _NS_razak._poly(surface, _NS_razak.PALETTE["wing_mid"], [
                (wing_base_x + side * 2, wing_base_y + 2),
                (cx + side * 20, wing_mid_y + 1),
                (wing_low_x - side * 2, wing_low_y - 2),
                (cx + side * 5, cy + 6),
            ])

            # Wing bones (finger struts)
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (wing_tip_x, wing_tip_y), 2)
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (wing_mid_x, wing_mid_y), 2)
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (wing_low_x, wing_low_y), 2)

            # Claw at wing tip
            _NS_razak._poly(surface, _NS_razak.PALETTE["bone_dark"], [
                (wing_tip_x, wing_tip_y),
                (wing_tip_x + side * 3, wing_tip_y - 2),
                (wing_tip_x + side * 1, wing_tip_y + 1),
            ])
            _NS_razak._aacircle(surface, _NS_razak.PALETTE["bone_light"],
                      (wing_tip_x + side * 2, wing_tip_y - 1), 1)


    def _draw_bat_wings_front(surface, cx, cy, facing, phase):
        """Overlay wing detail during attack."""
        # Just add some highlights
        for side in (-1, 1):
            _NS_razak._aaline(surface, _NS_razak.PALETTE["wing_light"],
                    (cx + side * 10, cy),
                    (cx + side * 25, cy - 8), 1)


    def _draw_bat_body(surface, cx, cy, facing, phase):
        """Red bat/dragon body."""
        # Shadow
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["shadow_deep"],
                 (cx - 15, cy - 3, 32, 20))

        # Main body (elongated)
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_darkest"], (cx - 14, cy - 5, 30, 18))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_dark"], (cx - 12, cy - 4, 26, 15))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_mid"], (cx - 10, cy - 3, 22, 12))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_light"], (cx - 8, cy - 4, 18, 8))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_high"], (cx - 6, cy - 4, 12, 4))

        # Belly (lighter underside)
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["belly_dark"], (cx - 8, cy + 6, 18, 6))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["belly_mid"], (cx - 6, cy + 7, 14, 4))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["belly_light"], (cx - 4, cy + 7, 10, 2))

        # Back spikes
        for i, sx_off in enumerate((-6, -2, 2, 6)):
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], [
                (cx + sx_off - 1, cy - 4),
                (cx + sx_off + 1, cy - 4),
                (cx + sx_off, cy - 8),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_mid"], [
                (cx + sx_off, cy - 4),
                (cx + sx_off + 1, cy - 4),
                (cx + sx_off, cy - 7),
            ])

        # Legs (small, tucked)
        for side in (-1, 1):
            lx = cx + side * 7
            ly = cy + 10
            _NS_razak._aacircle(surface, _NS_razak.PALETTE["bat_darkest"], (lx, ly), 3)
            _NS_razak._aacircle(surface, _NS_razak.PALETTE["bat_dark"], (lx, ly), 2)
            # Claws
            for c in (-1, 0, 1):
                _NS_razak._poly(surface, _NS_razak.PALETTE["bone_dark"], [
                    (lx + c, ly + 2),
                    (lx + c + side, ly + 4),
                    (lx + c, ly + 3),
                ])

        # Tail
        tail_end_x = cx - 18 * facing
        tail_end_y = cy + 4
        _NS_razak._aaline(surface, _NS_razak.PALETTE["bat_darkest"], (cx - facing * 12, cy + 2),
                (tail_end_x, tail_end_y), 4)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["bat_dark"], (cx - facing * 12, cy + 2),
                (tail_end_x, tail_end_y), 2)
        # Arrow-tipped tail
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], [
            (tail_end_x, tail_end_y - 2),
            (tail_end_x - facing * 4, tail_end_y),
            (tail_end_x, tail_end_y + 2),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_mid"], [
            (tail_end_x, tail_end_y - 1),
            (tail_end_x - facing * 3, tail_end_y),
            (tail_end_x, tail_end_y + 1),
        ])


    def _draw_bat_head(surface, cx, cy, facing, phase):
        """Dragon-like bat head."""
        # Shadow
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"], (cx + 1, cy + 1), 8)

        # Head base (elongated snout)
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_darkest"], (cx - 7, cy - 5, 14, 12))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_dark"], (cx - 6, cy - 4, 12, 10))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_mid"], (cx - 5, cy - 3, 10, 7))
        _NS_razak._ellipse(surface, _NS_razak.PALETTE["bat_light"], (cx - 4, cy - 3, 8, 4))

        # Snout extending forward
        snout = [
            (cx, cy - 1),
            (cx + facing * 8, cy - 2),
            (cx + facing * 10, cy + 1),
            (cx + facing * 8, cy + 3),
            (cx, cy + 3),
        ]
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], snout)
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_dark"], [
            (cx + 1, cy),
            (cx + facing * 7, cy - 1),
            (cx + facing * 9, cy + 1),
            (cx + facing * 7, cy + 2),
            (cx + 1, cy + 2),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["bat_mid"], [
            (cx + 2, cy),
            (cx + facing * 6, cy),
            (cx + facing * 8, cy + 1),
            (cx + facing * 6, cy + 2),
        ])

        # Fangs
        for tooth_off in (0, 3):
            _NS_razak._poly(surface, _NS_razak.PALETTE["bone_light"], [
                (cx + facing * (5 + tooth_off), cy + 2),
                (cx + facing * (5 + tooth_off) + facing, cy + 4),
                (cx + facing * (6 + tooth_off), cy + 2),
            ])

        # Nostril
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"],
                  (cx + facing * 8, cy - 1), 1)

        # Glowing yellow eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"],
                  (cx + facing * 2, cy - 2), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["fire_dark"], (cx + facing * 2, cy - 2), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["fire_hot"], (cx + facing * 2, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["fire_glow"], (cx + facing * 2, cy - 2), 1)

        # Horns / ears on top
        for i, off in enumerate((-3, 0, 3)):
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_darkest"], [
                (cx + off - 1, cy - 4),
                (cx + off + 1, cy - 4),
                (cx + off, cy - 8 - i % 2),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["bat_dark"], [
                (cx + off, cy - 4),
                (cx + off + 1, cy - 4),
                (cx + off, cy - 7),
            ])


    def _draw_goblin_rider(surface, cx, cy, facing, phase, action, attack_progress):
        """Goblin sitting on bat, holding weapon."""
        sway = int(math.sin(phase * 0.6) * 1)
        if action == "walk":
            sway += int(math.sin(phase * 2) * 1)

        # Legs (straddling bat)
        for side in (-1, 1):
            lx = cx + side * 4
            ly = cy + 10
            # Thigh
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (lx - 2, ly, 4, 6),
                  border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (lx - 2, ly, 4, 5))
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_mid"], (lx - 1, ly + 1, 3, 3))
            # Boot
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (lx - 3, ly + 6, 6, 4),
                  border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (lx - 3, ly + 6, 6, 3))
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_dark"], (lx - 3, ly + 6, 6, 1))

        # Torso
        _NS_razak._draw_goblin_torso(surface, cx + sway, cy, facing, phase)

        # Head
        _NS_razak._draw_goblin_head(surface, cx + sway, cy - 12, facing, phase)

        # Backpack / fuel tanks
        _NS_razak._draw_fuel_tanks(surface, cx + sway - facing * 6, cy - 4, phase)

        # Arms with weapons
        if action == "attack":
            _NS_razak._draw_goblin_attack_arms(surface, cx + sway, cy - 4, facing, phase,
                                     attack_progress)
        elif action in ("q_cast", "w_cast"):
            _NS_razak._draw_goblin_gun_arms(surface, cx + sway, cy - 4, facing, phase)
        else:
            _NS_razak._draw_goblin_idle_arms(surface, cx + sway, cy - 4, facing, phase)


    def _draw_goblin_torso(surface, cx, cy, facing, phase):
        """Small goblin torso in armor/vest."""
        # Shadow
        _NS_razak._poly(surface, _NS_razak.PALETTE["shadow_deep"], [
            (cx - 7 + 1, cy - 5 + 1), (cx + 7 + 1, cy - 5 + 1),
            (cx + 6 + 1, cy + 10 + 1), (cx - 6 + 1, cy + 10 + 1),
        ])

        # Torso base (green skin)
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_darkest"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 10), (cx - 6, cy + 10),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_dark"], [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 5, cy + 9), (cx - 5, cy + 9),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_mid"], [
            (cx - 5, cy - 3), (cx + 5, cy - 3),
            (cx + 4, cy + 7), (cx - 4, cy + 7),
        ])

        # Leather chest armor
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 8, cy - 2, 16, 8),
              border_radius=2)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (cx - 7, cy - 1, 14, 6),
              border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_mid"], (cx - 6, cy, 12, 3))

        # Chest strap X
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 6, cy - 2), (cx + 6, cy + 4), 2)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_darkest"], (cx + 6, cy - 2), (cx - 6, cy + 4), 2)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_mid"], (cx - 6, cy - 2), (cx + 6, cy + 4), 1)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_mid"], (cx + 6, cy - 2), (cx - 6, cy + 4), 1)

        # Brass buckle center
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_dark"], (cx, cy + 1), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_mid"], (cx, cy + 1), 1)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_shine"], (cx, cy), 1)


    def _draw_goblin_head(surface, cx, cy, facing, phase):
        """Goblin head with pilot goggles."""
        # Shadow
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["shadow_deep"], (cx + 1, cy + 1), 8)

        # Head base
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_darkest"], (cx, cy), 7)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_dark"], (cx - 1, cy - 1), 6)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_mid"], (cx - 1, cy - 2), 4)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_light"], (cx - 2, cy - 3), 2)

        # Long pointy ears
        for side in (-1, 1):
            _NS_razak._poly(surface, _NS_razak.PALETTE["gob_darkest"], [
                (cx + side * 6, cy - 1),
                (cx + side * 11, cy - 4),
                (cx + side * 7, cy + 2),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["gob_dark"], [
                (cx + side * 6, cy),
                (cx + side * 9, cy - 3),
                (cx + side * 7, cy + 1),
            ])
            _NS_razak._poly(surface, _NS_razak.PALETTE["gob_mid"], [
                (cx + side * 7, cy),
                (cx + side * 9, cy - 2),
                (cx + side * 7, cy),
            ])

        # Big nose (goblin trait)
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_dark"], [
            (cx + facing * 2, cy),
            (cx + facing * 5, cy + 1),
            (cx + facing * 5, cy + 3),
            (cx + facing * 2, cy + 3),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["gob_mid"], [
            (cx + facing * 2, cy + 1),
            (cx + facing * 4, cy + 2),
            (cx + facing * 2, cy + 2),
        ])

        # Mouth with fang
        _NS_razak._rect(surface, _NS_razak.PALETTE["shadow_deep"], (cx - 2, cy + 4, 4, 1))
        _NS_razak._poly(surface, _NS_razak.PALETTE["bone_light"], [
            (cx + 1, cy + 4),
            (cx + 2, cy + 6),
            (cx + 2, cy + 4),
        ])

        # Blue goggles (Batrider signature!)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 6, cy - 5, 12, 4),
              border_radius=1)
        # Left goggle lens
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["leather_dark"], (cx - 3, cy - 3), 3)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_dark"], (cx - 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_mid"], (cx - 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_light"], (cx - 4, cy - 4), 1)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_shine"], (cx - 4, cy - 4), 1)
        # Right goggle lens
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["leather_dark"], (cx + 3, cy - 3), 3)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_dark"], (cx + 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_mid"], (cx + 3, cy - 3), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["blue_light"], (cx + 2, cy - 4), 1)

        # Helmet on top
        _NS_razak._poly(surface, _NS_razak.PALETTE["leather_darkest"], [
            (cx - 7, cy - 5),
            (cx - 5, cy - 8),
            (cx + 5, cy - 8),
            (cx + 7, cy - 5),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["leather_dark"], [
            (cx - 6, cy - 5),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 6, cy - 5),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["leather_mid"], [
            (cx - 5, cy - 5),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 5),
        ])
        # Rivets
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_light"], (cx - 4, cy - 6), 1)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["brass_light"], (cx + 4, cy - 6), 1)


    def _draw_fuel_tanks(surface, cx, cy, phase):
        """Fuel tanks on goblin's back."""
        # Two brass tanks
        for i, off in enumerate((-2, 2)):
            _NS_razak._rect(surface, _NS_razak.PALETTE["shadow_deep"],
                  (cx - 2 + off + 1, cy - 4 + 1, 3, 10), border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_dark"], (cx - 2 + off, cy - 4, 3, 10),
                  border_radius=1)
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_mid"], (cx - 1 + off, cy - 3, 2, 8))
            _NS_razak._rect(surface, _NS_razak.PALETTE["brass_light"], (cx - 1 + off, cy - 3, 1, 6))
            # Cap on top
            _NS_razak._rect(surface, _NS_razak.PALETTE["metal_dark"], (cx - 2 + off, cy - 5, 3, 2))
            _NS_razak._rect(surface, _NS_razak.PALETTE["metal_light"], (cx - 2 + off, cy - 5, 3, 1))

        # Connecting hose
        _NS_razak._aaline(surface, _NS_razak.PALETTE["leather_darkest"], (cx - 1, cy - 3), (cx + 3, cy - 2), 2)


    def _draw_goblin_idle_arms(surface, cx, cy, facing, phase):
        """Idle - holding gun in one arm, machete in other."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm - holding machete
        back_side = -facing
        bs_x = cx + back_side * 5
        bs_y = cy - 2
        bh_x = bs_x + back_side * 4
        bh_y = cy + 4 + int(sway)
        _NS_razak._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)
        _NS_razak._draw_machete_held(surface, bh_x, bh_y, back_side, phase)

        # Front arm - gun
        fs_x = cx + facing * 5
        fs_y = cy - 2
        fh_x = fs_x + facing * 8
        fh_y = cy - 1 + int(sway)
        _NS_razak._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)
        _NS_razak._draw_flame_gun(surface, fh_x, fh_y, facing, phase)


    def _draw_goblin_gun_arms(surface, cx, cy, facing, phase):
        """Both arms holding gun forward, firing."""
        fs_x = cx + facing * 5
        fs_y = cy - 2
        fh_x = fs_x + facing * 10
        fh_y = cy - 1
        _NS_razak._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)

        # Back arm supporting gun
        bs_x = cx - facing * 3
        bs_y = cy - 1
        bh_x = fh_x - facing * 4
        bh_y = fh_y
        _NS_razak._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)

        _NS_razak._draw_flame_gun(surface, fh_x, fh_y, facing, phase, firing=True)


    def _draw_goblin_attack_arms(surface, cx, cy, facing, phase, progress):
        """One arm swings machete, other holds gun."""
        # Back arm - gun at rest
        back_side = -facing
        bs_x = cx + back_side * 3
        bs_y = cy - 2
        bh_x = bs_x + back_side * 6
        bh_y = cy + 1
        _NS_razak._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)
        _NS_razak._draw_flame_gun(surface, bh_x, bh_y, back_side, phase)

        # Front arm swings machete
        fs_x = cx + facing * 5
        fs_y = cy - 2

        if progress < 0.25:
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.3 + 0.3 * t
        elif progress < 0.55:
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.0 + 2.2 * t
        else:
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 1.0 * t

        arm_len = 10
        fh_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fh_y = fs_y + int(math.sin(arm_angle) * arm_len)

        _NS_razak._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)

        # Machete swinging
        blade_angle = arm_angle + math.pi / 4 * facing
        _NS_razak._draw_machete_swinging(surface, fh_x, fh_y, facing, blade_angle)


    def _draw_goblin_arm(surface, x1, y1, x2, y2):
        """Small goblin arm."""
        _NS_razak._aaline(surface, _NS_razak.PALETTE["shadow_deep"], (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["gob_darkest"], (x1, y1), (x2, y2), 4)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["gob_dark"], (x1, y1), (x2, y2), 3)
        _NS_razak._aaline(surface, _NS_razak.PALETTE["gob_mid"], (x1, y1), (x2, y2), 1)
        # Hand
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_darkest"], (x2, y2), 2)
        _NS_razak._aacircle(surface, _NS_razak.PALETTE["gob_mid"], (x2, y2), 1)


    def _draw_flame_gun(surface, hx, hy, facing, phase, firing=False):
        """Brass flamethrower / rifle."""
        # Handle/grip
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (hx - 1, hy - 2, 3, 5),
              border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (hx - 1, hy - 2, 3, 4))

        # Barrel (extending forward)
        barrel_len = 12
        end_x = hx + facing * barrel_len
        end_y = hy - 1

        # Wide brass barrel
        _NS_razak._rect(surface, _NS_razak.PALETTE["shadow_deep"],
              (min(hx, end_x) + 1, hy - 3 + 1, barrel_len, 5), border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["brass_dark"],
              (min(hx, end_x), hy - 3, barrel_len, 5), border_radius=1)
        _NS_razak._rect(surface, _NS_razak.PALETTE["brass_mid"],
              (min(hx, end_x), hy - 2, barrel_len, 3))
        _NS_razak._rect(surface, _NS_razak.PALETTE["brass_light"],
              (min(hx, end_x), hy - 2, barrel_len, 1))

        # Muzzle (flared)
        _NS_razak._poly(surface, _NS_razak.PALETTE["brass_dark"], [
            (end_x, hy - 4),
            (end_x + facing * 4, hy - 5),
            (end_x + facing * 4, hy + 3),
            (end_x, hy + 2),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["brass_mid"], [
            (end_x, hy - 3),
            (end_x + facing * 3, hy - 4),
            (end_x + facing * 3, hy + 2),
            (end_x, hy + 1),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["brass_light"], [
            (end_x + facing * 1, hy - 2),
            (end_x + facing * 3, hy - 3),
            (end_x + facing * 3, hy + 1),
        ])

        # Ignition pilot flame at muzzle
        if not firing:
            px = end_x + facing * 5
            py = hy - 1
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], 200), (px, py), 2)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], 220), (px, py), 1)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (px, py - 1), 1)


    def _draw_machete_held(surface, hx, hy, side, phase):
        """Machete at rest (blade forward)."""
        # Blade
        blade_end_x = hx + side * 14
        blade_end_y = hy - 6

        _NS_razak._aaline(surface, _NS_razak.PALETTE["shadow_deep"],
                (hx + 1, hy + 1), (blade_end_x + 1, blade_end_y + 1), 4)
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_darkest"], [
            (hx, hy - 1),
            (hx + side * 3, hy - 3),
            (blade_end_x, blade_end_y),
            (blade_end_x - side * 2, blade_end_y + 2),
            (hx, hy + 1),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_dark"], [
            (hx + side, hy - 1),
            (hx + side * 3, hy - 2),
            (blade_end_x - side, blade_end_y + 1),
            (hx + side, hy),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_mid"], [
            (hx + side * 2, hy - 1),
            (blade_end_x - side * 2, blade_end_y + 1),
            (hx + side * 2, hy),
        ])
        _NS_razak._aaline(surface, _NS_razak.PALETTE["metal_shine"],
                (hx + side * 3, hy - 2), (blade_end_x - side, blade_end_y + 1), 1)

        # Handle
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_darkest"], (hx - 1, hy, 3, 4))
        _NS_razak._rect(surface, _NS_razak.PALETTE["leather_dark"], (hx, hy, 2, 3))


    def _draw_machete_swinging(surface, hx, hy, facing, angle):
        """Machete in motion — angled with fire trail."""
        blade_len = 20
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle) * facing

        end_x = hx + int(dx * blade_len)
        end_y = hy + int(dy * blade_len)

        # Shadow
        _NS_razak._aaline(surface, _NS_razak.PALETTE["shadow_deep"], (hx + 2, hy + 2),
                (end_x + 2, end_y + 2), 4)

        # Blade shape
        blade_pts = [
            (hx + int(perp_x * 2), hy + int(perp_y * 2)),
            (hx + int(dx * blade_len * 0.5) + int(perp_x * 3),
             hy + int(dy * blade_len * 0.5) + int(perp_y * 3)),
            (end_x, end_y),
            (hx + int(dx * blade_len * 0.5) - int(perp_x * 1),
             hy + int(dy * blade_len * 0.5) - int(perp_y * 1)),
            (hx - int(perp_x * 1), hy - int(perp_y * 1)),
        ]
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_darkest"], blade_pts)
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_dark"], [
            (hx + int(perp_x), hy + int(perp_y)),
            (hx + int(dx * blade_len * 0.5) + int(perp_x * 2),
             hy + int(dy * blade_len * 0.5) + int(perp_y * 2)),
            (end_x, end_y),
            (hx + int(dx * blade_len * 0.5), hy + int(dy * blade_len * 0.5)),
        ])
        _NS_razak._poly(surface, _NS_razak.PALETTE["metal_mid"], [
            (hx + int(perp_x * 2), hy + int(perp_y * 2)),
            (hx + int(dx * blade_len * 0.4) + int(perp_x * 2),
             hy + int(dy * blade_len * 0.4) + int(perp_y * 2)),
            (end_x, end_y),
        ])

        # Sharp edge
        _NS_razak._aaline(surface, _NS_razak.PALETTE["metal_shine"],
                (hx + int(perp_x * 3), hy + int(perp_y * 3)),
                (end_x, end_y), 1)

        # FIRE aura on blade (Batrider machete on fire!)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], 180), (end_x, end_y), 5)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], 220), (end_x, end_y), 3)
        _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (end_x, end_y), 1)


    # ===================================================================
    # EFFECTS - Wisps, aura, shadow
    # ===================================================================
    def _draw_fire_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Fire wisps below bat (replaces legs)."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((140, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.25 + 0.75
        for radius in range(34, 3, -4):
            alpha = int((34 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_razak.PALETTE["fire_darkest"], min(255, alpha)),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 70, cy - 11))

        # Rising fire wisps
        for i, offset in enumerate((-24, -10, 6, 20)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 26)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha), (sx, sy), 5)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (sx, sy - 2), 3)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (sx, sy - 3), 2)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], alpha), (sx, sy - 3), 1)

        # Ember particles
        for i in range(7):
            angle = phase * 1.0 + i * math.pi * 2 / 7
            r = 25 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_razak._draw_ember(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 13 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 150 - i * 25)
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha),
                          (sx, sy), max(1, 4 - i))
                _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha // 2),
                          (sx, sy), max(1, 2 - i))


    def _draw_shadow(surface, x, y, lift=0):
        # ORIGINAL-MAX: tekstur gradien di-cache (piksel identik dengan
        # draw asli) lalu dirender ulang per frame dengan blit murah.
        # Saat badan terangkat (lift>0) bayangan MENYUSUT tapi dasar
        # tetap menapak tanah (bottom-anchored) - bayangan reaktif.
        NS = _NS_razak
        if NS._shadow_cache is None:
            shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["fire_dark"], 60),
                                (10, 5, 90, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w = spr.get_width()
        h = spr.get_height()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h          # bottom tetap di y+11 (menapak)
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(
                pygame.Rect(bx, by, w, h))


    def _draw_fire_aura(surface, x, y, phase, active_skill):
        # ORIGINAL-MAX: gradien aura dirender SEKALI ke cache (piksel
        # identik), denyut & kekuatan skill lewat set_alpha (blit NORMAL).
        # Hasil visual setara, tapi tanpa 20 aacircle tiap frame.
        NS = _NS_razak
        if NS._aura_cache is None:
            aura = pygame.Surface((200, 170), pygame.SRCALPHA)
            for radius in range(80, 5, -4):
                alpha = int((80 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["fire_darkest"],
                                        min(255, alpha)), (100, 85), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "r") else 1.0
        a = int(255 * min(1.0, pulse * strength))
        spr = NS._aura_cache.copy()
        spr.set_alpha(a)
        surface.blit(spr, (x - 100, y - 85))


    def _draw_machete_swing_arc(surface, x, y, facing, progress):
        """Fire trail of machete swing."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((140, 100), pygame.SRCALPHA)
        for i in range(18):
            t = i / 17
            angle = -math.pi * 0.85 + t * math.pi
            px = 70 + int(math.cos(angle) * 48) * facing
            py = 50 + int(math.sin(angle) * 36)
            alpha = int((220 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_darkest"], alpha), (px, py), 8)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_mid"], alpha), (px, py), 6)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_bright"], alpha), (px, py), 4)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_hot"], alpha), (px, py), 2)
            _NS_razak._aacircle(arc, (*_NS_razak.PALETTE["fire_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 70, y - 50))


    # ===================================================================
    # SKILL Q: STICKY NAPALM (arcing fire projectile)
    # ===================================================================
    def _draw_sticky_napalm(surface, boss, x, y, timer, phase):
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_razak._target_position(boss, x, y)

        # Spawn projectile at start
        if progress < 0.15 and not getattr(boss, "_razak_napalm_spawned", False):
            sx = x + 18 * boss.direction
            sy = y - 5
            _NS_razak._spawn_napalm(boss, sx, sy, tx, ty)
            boss._razak_napalm_spawned = True
        if progress > 0.7:
            boss._razak_napalm_spawned = False

        # Muzzle flash while casting (ORIGINAL-MAX: orb lebih besar/terang)
        if progress < 0.3:
            flash_intensity = 1 - progress / 0.3
            fx = x + 22 * boss.direction
            fy = y - 5
            alpha = int(255 * flash_intensity)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_darkest"], alpha), (fx, fy), 15)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], alpha), (fx, fy), 10)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], alpha), (fx, fy), 6)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], alpha), (fx, fy), 3)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], min(255, alpha)), (fx, fy), 2)

            # Sparks
            for i in range(7):
                angle = progress * 6 + i * math.pi * 2 / 5
                ex = fx + int(math.cos(angle) * 12)
                ey = fy + int(math.sin(angle) * 12)
                _NS_razak._draw_ember(surface, ex, ey, 2, alpha)

        # Impact ring di target saat proyektil datang (orb target-anchored)
        if 0.55 < progress < 0.9:
            imp = 1 - abs(progress - 0.72) / 0.17
            imp = max(0.0, min(1.0, imp))
            ir = int(6 + imp * 22)
            ia = int(220 * imp)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], ia),
                                (int(tx), int(ty)), ir)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], ia),
                                (int(tx), int(ty)), max(2, ir - 3))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], ia),
                                (int(tx), int(ty)), max(1, ir - 5))


    # ===================================================================
    # SKILL W: FLAMEBREAK (flame cone/stream)
    # ===================================================================
    def _draw_flamebreak(surface, boss, x, y, timer, phase):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_razak._target_position(boss, x, y)

        # Continuous flame stream forward
        if progress < 0.85:
            start_x = x + 22 * boss.direction
            start_y = y - 5

            # Direction toward target
            dx = tx - start_x
            dy = ty - start_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                dist = 1
            dir_x = dx / dist
            dir_y = dy / dist
            perp_x = -dir_y
            perp_y = dir_x

            # Cone length grows quickly, then stays
            if progress < 0.2:
                flame_len = int(180 * (progress / 0.2))
            else:
                flame_len = 180

            # Draw many flame particles in a cone
            for i in range(35):
                t = i / 35
                # Base position along cone
                base_x = start_x + dir_x * flame_len * t
                base_y = start_y + dir_y * flame_len * t
                # Spread perpendicular (wider at end)
                spread = t * 18
                offset = math.sin(phase * 4 + i * 1.7) * spread
                fx = int(base_x + perp_x * offset)
                fy = int(base_y + perp_y * offset)

                size = int(6 + t * 4)
                alpha_t = 1 - t * 0.3
                alpha = int(220 * alpha_t)

                # Layer flame colors based on distance
                if t < 0.15:
                    color_outer = _NS_razak.PALETTE["fire_white"]
                    color_inner = _NS_razak.PALETTE["fire_glow"]
                elif t < 0.4:
                    color_outer = _NS_razak.PALETTE["fire_hot"]
                    color_inner = _NS_razak.PALETTE["fire_bright"]
                elif t < 0.75:
                    color_outer = _NS_razak.PALETTE["fire_bright"]
                    color_inner = _NS_razak.PALETTE["fire_mid"]
                else:
                    color_outer = _NS_razak.PALETTE["fire_dark"]
                    color_inner = _NS_razak.PALETTE["fire_darkest"]

                _NS_razak._aacircle(surface, (*color_outer, alpha), (fx, fy), size)
                _NS_razak._aacircle(surface, (*color_inner, alpha), (fx, fy), max(1, size - 2))

            # Extra bright core near muzzle
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255), (int(start_x), int(start_y)), 5)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255),
                      (int(start_x + dir_x * 5), int(start_y + dir_y * 5)), 4)

            # ORIGINAL-MAX: impact ring menyala di target (target-anchored)
            it = 1 - abs(progress - 0.5) / 0.3
            it = max(0.0, min(1.0, it))
            ir = int(8 + it * 30)
            ia = int(230 * it)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], ia),
                                (int(tx), int(ty)), ir)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], ia),
                                (int(tx), int(ty)), max(2, ir - 3))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], ia),
                                (int(tx), int(ty)), max(1, ir - 6))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], ia),
                                (int(tx), int(ty)), max(1, ir - 8))


    # ===================================================================
    # SKILL R: FIRESTORM (columns of fire around target)
    # ===================================================================
    def _draw_firestorm_ground(surface, boss, x, y, timer, phase):
        """Ground circle warning."""
        tx, ty = _NS_razak._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        radius = int(45 + progress * 20)
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_darkest"], int(200 * pulse)),
                 (tx - radius, ty - radius // 3, radius * 2, radius // 1.5), 3)
        _NS_razak._ellipse(surface, (*_NS_razak.PALETTE["fire_dark"], int(180 * pulse)),
                 (tx - radius + 5, ty - radius // 3 + 2,
                  radius * 2 - 10, radius // 1.5 - 4), 2)
        # Rune-like marks
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.2
            rx = tx + int(math.cos(angle) * (radius - 5))
            ry = ty + int(math.sin(angle) * (radius // 3 - 2))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_bright"], int(200 * pulse)), (rx, ry), 2)


    def _draw_firestorm(surface, boss, x, y, timer, phase):
        """Multiple pillars of fire rising around target."""
        tx, ty = _NS_razak._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            return

        # 6 fire pillars around target
        for i in range(6):
            angle = i * math.pi * 2 / 6 + phase * 0.15
            r = 35
            px = tx + int(math.cos(angle) * r)
            py = ty + int(math.sin(angle) * r * 0.5)

            # Delay each pillar
            pillar_progress = (progress - 0.15 - i * 0.05) / 0.5
            if pillar_progress <= 0:
                continue
            pillar_progress = min(1.0, pillar_progress)

            # Grow then shrink
            if pillar_progress < 0.3:
                height_ratio = pillar_progress / 0.3
            elif pillar_progress < 0.7:
                height_ratio = 1.0
            else:
                height_ratio = 1.0 - (pillar_progress - 0.7) / 0.3

            pillar_h = int(62 * height_ratio)
            if pillar_h <= 0:
                continue

            # Draw fire pillar (tall flame) - ORIGINAL-MAX lebih besar/terang
            for h in range(pillar_h):
                t = h / max(1, pillar_h)
                w = int(9 * (1 - t * 0.5))
                fx = px + int(math.sin(phase * 4 + h * 0.3 + i) * 2)
                fy = py - h
                alpha = int(250 * (1 - t * 0.3))
                if t < 0.25:
                    color = _NS_razak.PALETTE["fire_darkest"]
                elif t < 0.5:
                    color = _NS_razak.PALETTE["fire_mid"]
                elif t < 0.75:
                    color = _NS_razak.PALETTE["fire_bright"]
                else:
                    color = _NS_razak.PALETTE["fire_hot"]
                _NS_razak._aacircle(surface, (*color, alpha), (fx, fy), max(1, w))

            # Bright core
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 240),
                      (px, py - pillar_h // 2), 4)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255),
                      (px, py - pillar_h // 3), 3)

            # Embers around base
            for j in range(3):
                ea = phase * 2 + j * 2
                ex = px + int(math.cos(ea) * 8)
                ey = py + int(math.sin(ea) * 3)
                _NS_razak._draw_ember(surface, ex, ey, 2, 200)

        # ORIGINAL-MAX: ring kejut menyala di target saat pilar meletus
        if progress > 0.15:
            ring_t = min(1.0, (progress - 0.15) / 0.35)
            ring_t = 1 - (1 - ring_t) ** 2
            rr = int(12 + ring_t * 50)
            ra = int(230 * (1 - ring_t * 0.4))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_dark"], ra),
                                (int(tx), int(ty)), rr)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_hot"], ra),
                                (int(tx), int(ty)), max(2, rr - 4))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], ra),
                                (int(tx), int(ty)), max(1, rr - 8))

        # Central big flame
        center_h = int(60 * min(1.0, progress / 0.4) *
                        (1.0 if progress < 0.7 else 1 - (progress - 0.7) / 0.3))
        if center_h > 0:
            for h in range(center_h):
                t = h / max(1, center_h)
                w = int(9 * (1 - t * 0.4))
                fx = tx + int(math.sin(phase * 3 + h * 0.2) * 2)
                fy = ty - h
                alpha = int(240 * (1 - t * 0.3))
                if t < 0.25:
                    color = _NS_razak.PALETTE["fire_dark"]
                elif t < 0.55:
                    color = _NS_razak.PALETTE["fire_bright"]
                else:
                    color = _NS_razak.PALETTE["fire_hot"]
                _NS_razak._aacircle(surface, (*color, alpha), (fx, fy), max(1, w))
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_glow"], 255), (tx, ty - center_h // 2), 5)
            _NS_razak._aacircle(surface, (*_NS_razak.PALETTE["fire_white"], 255), (tx, ty - center_h // 3), 3)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_razak.draw_razak(surface, boss, x, y)
