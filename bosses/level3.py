"""
bosses/level3.py - Semua boss Level 3

Gabungan dari 4 file terpisah:
  - varkul               (mini boss)
  - xerathis             (mini boss)
  - nyzrak               (mini boss)
  - ancient_apparition   (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import pygame

try:                     # pass cahaya bersama; opsional supaya file boss
    import lighting as _lighting          # tetap bisa di-load sendiri
except Exception:        # pragma: no cover
    _lighting = None

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True


def _composite_boss_body(surface, ns, raw, cx, cy, facing, phase, action,
                         attack_progress=0, rim_add=(30, 26, 44), bsize=180):
    """Komposit ORIGINAL-MAX untuk boss level3.

    Badan dirender ke buffer tetap, di-crop rapat, diberi outline siluet
    gelap 1 px (4 arah) lalu pass pencahayaan rim/shade dari lighting.py.
    Anchor (cx, cy) tetap jatuh di titik yang sama dengan sebelumnya, jadi
    pose & posisi dunia tidak berubah.
    """
    if getattr(ns, "_body_buf", None) is None:
        ns._body_buf = pygame.Surface((bsize, bsize), pygame.SRCALPHA)
    buf = ns._body_buf
    buf.fill((0, 0, 0, 0))
    raw(buf, bsize // 2, bsize // 2, facing, phase, action, attack_progress)
    used = buf.get_bounding_rect(min_alpha=1)
    if used.width <= 2 or used.height <= 2:
        return
    used.inflate_ip(4, 4)
    used.clamp_ip(buf.get_rect())
    sub = buf.subsurface(used).copy()
    ox = int(cx) - (bsize // 2) + used.left
    oy = int(cy) - (bsize // 2) + used.top
    edge = sub.copy()
    edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        surface.blit(edge, (ox + ddx, oy + ddy))
    if _lighting is not None:
        # Boss sprite level3 sudah punya gradasi nilai di-author yang cukup;
        # matikan gradien global agar idle tetap < 2.2 ms (rim + terminator
        # 1px tetap terlihat, arah cahaya dari lighting.py).
        _lighting.apply_to_rig(sub, rim_add=rim_add, shade_mul=168,
                               gradient=False, two_band=False)
    surface.blit(sub, (ox, oy))


# ====================================================================
# VARKUL
# ====================================================================
class _NS_varkul:
    """Namespace varkul - isi asli tidak diubah."""

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    # Buffer badan untuk outline+lighting, buffer hurt flash, dan catatan
    # rect shadow supaya flash tidak ikut menyalakan bayangan tanah.
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Lich inspired frost blue / undead purple
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin / bone (undead pale blue)
        "skin_darkest":   (30,  45,  70),
        "skin_dark":      (60,  85, 115),
        "skin_mid":       (110, 145, 175),
        "skin_light":     (165, 200, 225),
        "skin_high":      (210, 235, 250),

        # Bone / skull
        "bone_dark":      (85, 100, 120),
        "bone_mid":       (155, 175, 195),
        "bone_light":     (215, 230, 240),
        "bone_shine":     (245, 250, 255),

        # Robe – dark purple
        "robe_darkest":   (18,  12,  35),
        "robe_dark":      (38,  25,  68),
        "robe_mid":       (68,  45, 115),
        "robe_light":     (105, 78, 160),
        "robe_high":      (145, 115, 200),

        # Armor trim / shoulders (dark blue metal)
        "armor_darkest":  (15,  25,  55),
        "armor_dark":     (30,  55,  95),
        "armor_mid":      (55,  90, 140),
        "armor_light":    (110, 150, 195),
        "armor_shine":    (180, 210, 240),

        # Gold trim
        "gold_dark":      (95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 235, 165),

        # Frost / ice energy
        "ice_darkest":    (10,  30,  75),
        "ice_dark":       (25,  70, 145),
        "ice_mid":        (70, 140, 225),
        "ice_light":      (140, 200, 250),
        "ice_bright":     (195, 230, 255),
        "ice_hot":        (225, 245, 255),
        "ice_white":      (245, 252, 255),

        # Eye glow (bright blue)
        "eye_dark":       (20,  60, 140),
        "eye_mid":        (70, 140, 240),
        "eye_light":      (150, 210, 255),
        "eye_hot":        (220, 245, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_varkul._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_varkul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_varkul._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_varkul._clamp(color)
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
        color = _NS_varkul._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_varkul._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


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
    # Ice / frost visual helpers
    # ---------------------------------------------------------------------------
    def _draw_ice_shard(surface, cx, cy, size, angle, color_dark, color_mid,
                        color_light, color_hot):
        """Draw a single sharp ice crystal shard."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.35
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.35
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.35
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.35

        _NS_varkul._poly(surface, color_dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        # Inner highlight
        _NS_varkul._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_varkul._aaline(surface, color_light, (cx, cy), (tip_x, tip_y), 1)
        _NS_varkul._aacircle(surface, color_hot, (int(tip_x), int(tip_y)), 1)


    def _draw_snowflake(surface, cx, cy, size, phase, color=None):
        """Small rotating snowflake."""
        if color is None:
            color = _NS_varkul.PALETTE["ice_bright"]
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            x1 = cx + int(math.cos(angle) * size)
            y1 = cy + int(math.sin(angle) * size)
            _NS_varkul._aaline(surface, color, (cx, cy), (x1, y1), 1)
            # Small branches
            bx = cx + int(math.cos(angle) * size * 0.6)
            by = cy + int(math.sin(angle) * size * 0.6)
            for b in (-1, 1):
                ba = angle + b * 0.5
                ex = bx + int(math.cos(ba) * size * 0.3)
                ey = by + int(math.sin(ba) * size * 0.3)
                _NS_varkul._aaline(surface, color, (bx, by), (ex, ey), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_hot"], (cx, cy), 1)


    def _draw_frost_particles(surface, cx, cy, phase, radius=25, count=8):
        """Frosty motes swirling around a point."""
        for i in range(count):
            angle = phase * 0.6 + i * math.pi * 2 / count
            r = radius + int(math.sin(phase + i * 0.9) * 6)
            px = cx + int(math.cos(angle) * r)
            py = cy + int(math.sin(angle) * r * 0.6)
            alpha = int(140 + math.sin(phase * 1.4 + i) * 80)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_hot"], alpha), (px, py), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM – Frost Orb
    # ---------------------------------------------------------------------------
    class FrostProjectile:
        """Frost orb projectile that travels toward a target."""
        def __init__(self, sx, sy, tx, ty, speed=5.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail - frost mist
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Outer frost aura
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 90), (px, py), 15)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 140), (px, py), 11)
                # Core orb
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (px, py), 7)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (px, py), 5)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (px - 1, py - 1), 3)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (px - 1, py - 1), 1)
                # Ice shards protruding
                for i in range(4):
                    angle = phase * 3 + i * math.pi / 2
                    _NS_varkul._draw_ice_shard(surface, px, py, 8, angle,
                                    _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                                    _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    # ---------------------------------------------------------------------------
    # Chain Frost bouncing orb
    # ---------------------------------------------------------------------------
    class ChainFrostOrb:
        """Chain frost that bounces around."""
        def __init__(self, sx, sy, tx, ty, bounces=3):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = 4.5
            self.alive = True
            self.age = 0
            self.bounces_left = bounces
            self.trail = []

        def update(self, boss):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 3:
                if self.bounces_left > 0:
                    self.bounces_left -= 1
                    # Random new target direction
                    angle = self.age * 0.7
                    self.tx = self.x + math.cos(angle) * 120
                    self.ty = self.y + math.sin(angle) * 60
                else:
                    self.alive = False
                    return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 20:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 10)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (tx, ty), r + 1)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha // 2), (tx, ty), r)
            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 120), (px, py), 13)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 180), (px, py), 9)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (px, py), 6)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (px, py), 4)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (px - 1, py - 1), 2)
                # Rotating shards
                for i in range(5):
                    angle = phase * 4 + i * math.pi * 2 / 5
                    _NS_varkul._draw_ice_shard(surface, px, py, 7, angle,
                                    _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                                    _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_vk_last_x"):
            boss._vk_last_x = boss.x
            boss._vk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vk_last_x)
        dy = abs(boss.y - boss._vk_last_y)
        boss._vk_last_x = boss.x
        boss._vk_last_y = boss.y
        return dx + dy > 0.3

    def _update_attack_anim(boss):
        """Track ranged attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vk_prev_timer", -1))
        active = bool(getattr(boss, "_vk_attack_active", False))

        # Trigger conditions:
        # 1. timer melonjak ke nilai tinggi (>= cooldown-1) dari nilai rendah
        # 2. timer baru saja di-reset dari tinggi ke rendah (wrap-around)
        trigger = False
        if previous < 0:
            # First frame - jangan trigger
            pass
        elif timer >= cooldown - 1 and previous < cooldown - 1:
            trigger = True
        elif previous >= cooldown - 2 and timer <= 1:
            # timer wrapped from high to low - attack fires now
            trigger = True

        if trigger and not active:
            boss._vk_attack_active = True
            boss._vk_attack_frame = 0
            active = True

        if active:
            boss._vk_attack_frame = int(getattr(boss, "_vk_attack_frame", 0)) + 1
            if boss._vk_attack_frame > cooldown:
                boss._vk_attack_active = False
                boss._vk_attack_frame = 0
                active = False

        boss._vk_prev_timer = timer
        boss._vk_attack_progress = (
            min(1.0, getattr(boss, "_vk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_vk_projectiles"):
            boss._vk_projectiles = []
        for proj in boss._vk_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._vk_projectiles = [p for p in boss._vk_projectiles if p.alive or p.age < 8]


    def _manage_chain_orbs(boss, surface, phase):
        if not hasattr(boss, "_vk_chain_orbs"):
            boss._vk_chain_orbs = []
        for orb in boss._vk_chain_orbs:
            orb.update(boss)
            orb.draw(surface, phase)
        boss._vk_chain_orbs = [o for o in boss._vk_chain_orbs if o.alive or o.age < 8]


    def _spawn_projectile(boss, x, y):
        if not hasattr(boss, "_vk_projectiles"):
            boss._vk_projectiles = []
        tx, ty = _NS_varkul._target_position(boss, x, y)
        # Staff tip position - Lich holds staff on off-hand side
        facing = getattr(boss, "direction", 1)
        sx = x - 20 * facing  # staff hand
        sy = y - 20
        boss._vk_projectiles.append(_NS_varkul.FrostProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_varkul(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_varkul._detect_moving(boss)
        _NS_varkul._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_vk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_varkul._draw_frost_aura(surface, x, y, pulse)
        _NS_varkul._draw_ice_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_varkul._draw_frost_blast_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_varkul._draw_sacrifice_circle(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_varkul._draw_chain_frost_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        # ORIGINAL-MAX hurt flash: saat kena hit, pose dirender ke buffer,
        # lalu siluet badannya dibanjiri putih-hangat. Bayangan tanah TIDAK
        # ikut menyala (rect shadow direkam dan dikeluarkan dari flash).
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            NS = _NS_varkul
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        if attacking:
            _NS_varkul._draw_varkul_attack(_tgt, boss, _tx, _ty)
        elif moving:
            _NS_varkul._draw_varkul_walk(_tgt, boss, _tx, _ty)
        else:
            _NS_varkul._draw_varkul_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            NS = _NS_varkul
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ---------- Projectiles ----------
        _NS_varkul._manage_projectiles(boss, surface, pulse)
        _NS_varkul._manage_chain_orbs(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_varkul._draw_frost_blast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_varkul._draw_frostbite(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_varkul._draw_sacrifice_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_varkul._draw_chain_frost(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_varkul_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_varkul._draw_shadow(surface, x, y + 48)
        _NS_varkul._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_varkul._draw_varkul_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_varkul_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_varkul._draw_shadow(surface, x + sway, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_varkul._draw_varkul_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_varkul_attack(surface, boss, x, y):
        progress = getattr(boss, "_vk_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn projectile at the right moment
        if 0.30 < progress < 0.40 and not getattr(boss, "_vk_proj_spawned", False):
            _NS_varkul._spawn_projectile(boss, x, y)
            boss._vk_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._vk_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_varkul._draw_shadow(surface, x + recoil, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_varkul._draw_varkul_body(surface, x + recoil, y, boss.direction, boss.pulse,
                          "attack", progress)
        _NS_varkul._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Lich
    # ===================================================================
    def _draw_varkul_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Komposit ORIGINAL-MAX: badak ke buffer tetap, outline siluet
        gelap 1 px + pass pencahayaan rim/shade, lalu blit ke posisi sama."""
        _composite_boss_body(
            surface, _NS_varkul, _NS_varkul._draw_varkul_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(70, 120, 210), bsize=180)

    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """ORIGINAL-MAX detail pass: rim kiri-atas + pemisah bagian + detail
        wajah/emblem agar tetap terbaca saat downscale."""
        P = _NS_varkul.PALETTE
        pygame.draw.circle(surface, P["bone_shine"], (cx - 10, cy - 36), 1)
        pygame.draw.circle(surface, P["bone_light"], (cx - 9, cy - 34), 2)
        for side in (-1, 1):
            pygame.draw.circle(surface, P["bone_shine"], (cx + side * 8, cy - 44), 1)
            pygame.draw.circle(surface, P["ice_white"], (cx + side * 7, cy - 45), 1)
        pygame.draw.line(surface, P["shadow_deep"], (cx - 6, cy - 20), (cx + 6, cy - 20), 1)
        pygame.draw.line(surface, P["shadow_deep"], (cx - 10, cy - 1), (cx + 10, cy - 1), 1)
        pygame.draw.line(surface, P["robe_darkest"], (cx - 13, cy + 27), (cx + 13, cy + 27), 1)
        pygame.draw.circle(surface, P["bone_shine"], (cx - 1, cy - 8), 1)
        pygame.draw.line(surface, P["gold_light"], (cx - 10, cy - 14), (cx, cy - 9), 1)
        orb_x = cx - 20 * facing
        orb_y = cy - 20
        pygame.draw.circle(surface, P["ice_hot"], (orb_x - 1, orb_y - 2), 2)
        pygame.draw.circle(surface, P["ice_white"], (orb_x - 1, orb_y - 2), 1)


    def _draw_varkul_body_raw(surface, cx, cy, facing, phase, action,
                              attack_progress=0):
        # Cape / robe back
        _NS_varkul._draw_robe_back(surface, cx, cy, facing, phase, action)

        # Lower robes (floating)
        _NS_varkul._draw_lower_robes(surface, cx, cy + 5, phase)

        # Torso robes with skull
        _NS_varkul._draw_torso(surface, cx, cy - 8, phase)

        # Pauldrons
        _NS_varkul._draw_pauldrons(surface, cx, cy - 18, phase)

        # Arms – staff arm and casting arm
        if action == "attack":
            _NS_varkul._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_varkul._draw_idle_arms(surface, cx, cy - 8, facing, phase, action)

        # Skull head with crown
        _NS_varkul._draw_skull_head(surface, cx, cy - 30, phase)

        # Floating frost particles
        _NS_varkul._draw_body_particles(surface, cx, cy, phase)

        # ORIGINAL-MAX detail pass (rim + separator + emblem)
        _NS_varkul._masterwork_finish(surface, cx, cy, facing, phase, action,
                                      attack_progress)


    def _draw_robe_back(surface, cx, cy, facing, phase, action):
        """Back of robe / cape."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cape
        cape_outer = [
            (cx - 15, cy - 12),
            (cx - 20, cy + 5),
            (cx - 26 - int(wave), cy + 28),
            (cx - 18 - int(wave2), cy + 42),
            (cx - 5, cy + 46),
            (cx + 5, cy + 46),
            (cx + 18 + int(wave2), cy + 42),
            (cx + 26 + int(wave), cy + 28),
            (cx + 20, cy + 5),
            (cx + 15, cy - 12),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], cape_outer)

        cape_mid = [
            (cx - 13, cy - 10),
            (cx - 17, cy + 5),
            (cx - 22 - int(wave * 0.7), cy + 26),
            (cx - 14, cy + 38),
            (cx, cy + 40),
            (cx + 14, cy + 38),
            (cx + 22 + int(wave * 0.7), cy + 26),
            (cx + 17, cy + 5),
            (cx + 13, cy - 10),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], cape_mid)

        # Inner lining (lighter purple)
        cape_inner = [
            (cx - 10, cy - 6),
            (cx - 13, cy + 5),
            (cx - 16, cy + 22),
            (cx - 8, cy + 32),
            (cx + 8, cy + 32),
            (cx + 16, cy + 22),
            (cx + 13, cy + 5),
            (cx + 10, cy - 6),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], cape_inner)

        # Ice crystals on cape edges
        for i, (px, py) in enumerate([(cx - 24, cy + 24), (cx + 24, cy + 24),
                                        (cx - 18, cy + 38), (cx + 18, cy + 38)]):
            size = 4 + int(math.sin(phase + i) * 1)
            _NS_varkul._draw_ice_shard(surface, px, py, size, -math.pi / 2 + math.sin(phase) * 0.1,
                            _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                            _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_lower_robes(surface, cx, cy, phase):
        """Floating lower body with tattered robes (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        # Outer robe
        robe_outer = [
            (cx - 17, cy),
            (cx + 17, cy),
            (cx + 21 + sway, cy + 14),
            (cx + 15, cy + 24),
            (cx + 8, cy + 30),
            (cx + 3, cy + 32),
            (cx - 3, cy + 32),
            (cx - 8, cy + 30),
            (cx - 15, cy + 24),
            (cx - 21 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], robe_outer)

        robe_mid = [
            (cx - 14, cy + 2),
            (cx + 14, cy + 2),
            (cx + 17 + sway, cy + 14),
            (cx + 11, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 11, cy + 22),
            (cx - 17 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], robe_mid)

        robe_inner = [
            (cx - 10, cy + 4),
            (cx + 10, cy + 4),
            (cx + 13 + sway, cy + 14),
            (cx + 7, cy + 20),
            (cx - 7, cy + 20),
            (cx - 13 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], robe_inner)

        # Tattered bottom
        for i in range(7):
            tx = cx - 15 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 3)
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 4), (tx - 1, ty + 4),
            ])

        # Gold belt
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_dark"], (cx - 18, cy - 1, 36, 5))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_mid"], (cx - 16, cy, 32, 3))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_light"], (cx - 13, cy + 1, 26, 1))

        # Belt center gem – ice
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_darkest"], (cx, cy + 1), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (cx, cy + 1), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (cx - 1, cy), 2)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Torso with robes and a skull emblem."""
        # Shadow
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow_deep"], [
            (cx - 13 + 2, cy - 10 + 2), (cx + 13 + 2, cy - 10 + 2),
            (cx + 11 + 2, cy + 14 + 2), (cx + 5 + 2, cy + 19 + 2),
            (cx - 5 + 2, cy + 19 + 2), (cx - 11 + 2, cy + 14 + 2),
        ])
        # Main torso
        torso = [
            (cx - 13, cy - 10), (cx + 13, cy - 10),
            (cx + 11, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 11, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], torso)
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 9, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 9, cy + 12),
        ])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], [
            (cx - 8, cy - 5), (cx + 8, cy - 5),
            (cx + 6, cy + 8), (cx + 3, cy + 12),
            (cx - 3, cy + 12), (cx - 6, cy + 8),
        ])

        # Center skull emblem (bone)
        sk_cx, sk_cy = cx, cy + 2
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (sk_cx, sk_cy - 2), 5)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (sk_cx, sk_cy - 2), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (sk_cx - 1, sk_cy - 3), 2)
        # Eye sockets on emblem
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (sk_cx - 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (sk_cx + 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (sk_cx - 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (sk_cx + 2, sk_cy - 3), 1)
        # Jaw
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_dark"], (sk_cx - 2, sk_cy + 1, 4, 3))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_mid"], (sk_cx - 2, sk_cy + 1, 4, 2))

        # Gold V-neck trim
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_dark"], (cx - 11, cy - 8), (cx, cy - 2), 2)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_dark"], (cx + 11, cy - 8), (cx, cy - 2), 2)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_mid"], (cx - 10, cy - 7), (cx, cy - 3), 1)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_mid"], (cx + 10, cy - 7), (cx, cy - 3), 1)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Ice-crowned shoulder pauldrons."""
        for side in (-1, 1):
            sx = cx + side * 15
            # Shadow
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow_deep"], (sx + 2, cy + 2), 10)
            # Metal pauldron base
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_darkest"], (sx, cy), 9)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_dark"], (sx - side, cy - 1), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_mid"], (sx - side * 2, cy - 2), 5)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_light"], (sx - side * 2, cy - 3), 2)

            # Gold trim
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (sx, cy), 9, 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (sx, cy), 8, 1)

            # Ice crystal spikes on top of pauldron
            for i, off_a in enumerate([-0.4, 0.0, 0.4]):
                spike_angle = -math.pi / 2 + off_a
                size = 6 if i == 1 else 4
                _NS_varkul._draw_ice_shard(surface, sx, cy - 4, size,
                                spike_angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Arms - one holds staff, one has orb of frost."""
        sway = int(math.sin(phase * 0.7) * 1)

        # LEFT (staff arm - opposite of facing)
        staff_side = -facing
        ss_x = cx + staff_side * 13
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy + 12 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y + 10
        _NS_varkul._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_varkul._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Draw staff
        _NS_varkul._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # RIGHT (orb hand - facing direction)
        orb_side = facing
        os_x = cx + orb_side * 13
        os_y = cy + 2
        oe_x = os_x + orb_side * 8
        oe_y = cy + 10 + sway
        oh_x = oe_x + orb_side * 5
        oh_y = oe_y + 8
        _NS_varkul._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_varkul._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        # Skeletal hand
        _NS_varkul._draw_skeletal_hand(surface, oh_x, oh_y)
        # Frost orb in hand
        _NS_varkul._draw_hand_orb(surface, oh_x + orb_side * 4, oh_y + 2, phase, 5)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose - staff raised for casting."""
        # STAFF arm rises up during cast
        staff_side = -facing
        ss_x = cx + staff_side * 13
        ss_y = cy + 2

        # Wind up then thrust
        if progress < 0.3:
            t = progress / 0.3
            arm_angle = math.pi / 2 + 0.8 * t  # raising up
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = math.pi / 2 + 0.8 - 0.6 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = math.pi / 2 + 0.2 + 0.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 10) * staff_side
        se_y = ss_y - int(math.sin(arm_angle) * 10)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * staff_side
        sh_y = se_y - int(math.sin(arm_angle) * 10)

        _NS_varkul._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_varkul._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_varkul._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # ORB hand extends forward
        orb_side = facing
        os_x = cx + orb_side * 13
        os_y = cy + 2

        if progress < 0.35:
            t = progress / 0.35
            ext = t
        elif progress < 0.55:
            ext = 1.0
        else:
            t = (progress - 0.55) / 0.45
            ext = 1.0 - t * 0.7

        oe_x = os_x + orb_side * int(6 + ext * 6)
        oe_y = cy + int(10 - ext * 6)
        oh_x = oe_x + orb_side * int(5 + ext * 5)
        oh_y = oe_y + int(8 - ext * 6)

        _NS_varkul._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_varkul._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_varkul._draw_skeletal_hand(surface, oh_x, oh_y)

        # Larger, glowing orb during cast
        orb_size = 6 + int(math.sin(progress * math.pi) * 5)
        _NS_varkul._draw_hand_orb(surface, oh_x + orb_side * 4, oh_y + 2, phase, orb_size)

        # Frost trail from hand during launch
        if 0.25 < progress < 0.55:
            intensity = math.sin((progress - 0.25) / 0.3 * math.pi)
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                ex = oh_x + int(math.cos(angle) * 12 * intensity) * facing
                ey = oh_y + int(math.sin(angle) * 10 * intensity)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], 180),
                          (ex, ey), max(1, int(3 * intensity)))
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], 200),
                          (ex, ey), max(1, int(2 * intensity)))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 7)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_dark"], (x1, y1), (x2, y2), 5)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_mid"], (x1, y1), (x2, y2), 3)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)
        # Gold cuff at joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (mx, my), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (mx, my), 3)


    def _draw_skeletal_hand(surface, x, y):
        """Small bony hand."""
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (x, y), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (x, y), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (x - 1, y - 1), 1)


    def _draw_hand_orb(surface, x, y, phase, size=5):
        """Frost orb hovering in hand."""
        pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        s = int(size * pulse)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 90), (x, y), s + 6)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 150), (x, y), s + 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (x, y), s)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (x - 1, y - 1), max(1, s - 2))
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (x - 1, y - 1), max(1, s - 4))

        # Tiny snowflakes floating around
        for i in range(3):
            angle = phase * 2 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_varkul._rect(surface, _NS_varkul.PALETTE["ice_bright"], (sx, sy, 2, 2))


    def _draw_staff(surface, x, y, phase, side, casting=False, progress=0):
        """The frost staff with ice crystal head."""
        # Staff pole - long
        top_x = x + side * -2
        top_y = y - 40
        bot_x = x + side * 4
        bot_y = y + 20

        # Shadow
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wood/metal staff
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_darkest"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_dark"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_mid"], (top_x, top_y), (bot_x, bot_y), 1)

        # Gold rings on staff
        for t in (0.3, 0.6, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (rx, ry), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (rx, ry), 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_light"], (rx - 1, ry - 1), 1)

        # Staff head - crystal cluster
        head_x, head_y = top_x, top_y - 4

        # Cast glow
        glow_size = 8
        if casting:
            glow_size = 8 + int(math.sin(progress * math.pi) * 10)

        # Backing glow
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 100), (head_x, head_y), glow_size + 4)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 160), (head_x, head_y), glow_size)

        # Metal claws holding the crystal
        for offset_a in (-1.2, -0.4, 0.4, 1.2):
            cx1 = head_x + int(math.cos(math.pi / 2 + offset_a) * 3)
            cy1 = head_y + int(math.sin(math.pi / 2 + offset_a) * 3)
            cx2 = head_x + int(math.cos(math.pi / 2 + offset_a) * 8)
            cy2 = head_y + int(math.sin(math.pi / 2 + offset_a) * 8) - 4
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_darkest"], (cx1, cy1), (cx2, cy2), 3)
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Main ice crystal
        _NS_varkul._draw_ice_shard(surface, head_x, head_y, 8, -math.pi / 2,
                        _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        # Center gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (head_x, head_y - 2), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (head_x, head_y - 2), int(3 * pulse) + 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (head_x, head_y - 3), 2)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (head_x, head_y - 3), 1)


    def _draw_skull_head(surface, cx, cy, phase):
        """Lich skull head with horned crown."""
        # Shadow
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Skull main
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (cx, cy), 11)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (cx - 1, cy - 1), 9)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (cx - 2, cy - 3), 5)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_shine"], (cx - 3, cy - 4), 2)

        # Skull cheekbones angular
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
            (cx - 10, cy + 2), (cx - 7, cy + 8), (cx - 4, cy + 6)
        ])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
            (cx + 10, cy + 2), (cx + 7, cy + 8), (cx + 4, cy + 6)
        ])

        # Eye sockets
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (cx - 4, cy - 1), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (cx + 4, cy - 1), 3)

        # Glowing blue eyes
        eye_pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        er = max(1, int(2 * eye_pulse))
        for eox in (-4, 4):
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["eye_dark"], 200), (cx + eox, cy - 1), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_mid"], (cx + eox, cy - 1), er + 1)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_light"], (cx + eox, cy - 1), er)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (cx + eox, cy - 1), max(1, er - 1))

        # Eye light streaks/aura
        for eox in (-4, 4):
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["eye_light"], int(80 * eye_pulse)),
                      (cx + eox, cy - 1), 5)

        # Nasal cavity
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow"], [
            (cx - 1, cy + 2), (cx + 1, cy + 2),
            (cx + 2, cy + 5), (cx - 2, cy + 5),
        ])

        # Teeth / jaw
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_dark"], (cx - 5, cy + 6, 10, 4))
        for i in range(5):
            tx = cx - 4 + i * 2
            _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_light"], (tx, cy + 6, 1, 3))
        # Jaw shadow line
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow"], (cx - 5, cy + 6), (cx + 5, cy + 6), 1)

        # Horned crown - big antler-like horns
        for side in (-1, 1):
            # Main horn curving outward
            base_x = cx + side * 6
            base_y = cy - 8

            # Base of horn
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
                (base_x - 2, base_y),
                (base_x + 2, base_y),
                (base_x + side * 4, base_y - 4),
                (base_x + side * 2, base_y - 5),
            ])

            # Curving horn segments
            for i, (dx, dy, w) in enumerate([
                (side * 4, -6, 3),
                (side * 7, -10, 2),
                (side * 10, -14, 2),
            ]):
                hx = base_x + dx
                hy = base_y + dy
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (hx, hy), w)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (hx - 1, hy - 1), w - 1)

            # Horn tip
            tip_x = base_x + side * 12
            tip_y = base_y - 16
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_light"], [
                (base_x + side * 10, base_y - 13),
                (base_x + side * 12, base_y - 13),
                (tip_x, tip_y),
            ])

            # Ice crystal at horn base
            _NS_varkul._draw_ice_shard(surface, base_x + side * 3, base_y + 1, 4,
                            -math.pi / 2 + side * 0.3,
                            _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                            _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

        # Central crown ice crystal
        _NS_varkul._draw_ice_shard(surface, cx, cy - 12, 6, -math.pi / 2,
                        _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

        # Small side crystals on top
        _NS_varkul._draw_ice_shard(surface, cx - 3, cy - 10, 4, -math.pi / 2 - 0.3,
                        _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        _NS_varkul._draw_ice_shard(surface, cx + 3, cy - 10, 4, -math.pi / 2 + 0.3,
                        _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating frost particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (px, py), 1)

        # Falling snowflakes
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 30 + i * 20 + int(math.sin(phase + i) * 5)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_varkul._draw_snowflake(surface, fx, fy, 3,
                            phase + i, (*_NS_varkul.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Frost mist beneath floating Lich."""
        NS = _NS_varkul
        if NS._mist_cache is None:
            mist = pygame.Surface((120, 40), pygame.SRCALPHA)
            for radius in range(30, 3, -4):
                alpha = int((30 - radius) * 2.8)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*NS.PALETTE["ice_dark"], min(255, alpha)),
                        (60 - radius * 2, 20 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            NS._mist_cache = mist
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 60, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting frost crystals
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (sx, sy), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (sx, sy), 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y, lift=0):
        """Ground shadow beneath floating entity (cache + reaktif saat lift)."""
        NS = _NS_varkul
        if NS._shadow_cache is None:
            shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 16)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["ice_dark"], 40), (8, 4, 84, 10))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 10) - h          # dasar tetap menapak di y+10
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase):
        """Large background frost aura (basis di-cache, denyut via alpha)."""
        NS = _NS_varkul
        if NS._aura_cache is None:
            aura = pygame.Surface((180, 160), pygame.SRCALPHA)
            for radius in range(70, 5, -4):
                alpha = int((70 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                                 (90, 80), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.2, min(1.0, pulse))))
        surface.blit(spr, (x - 90, y - 80))


    def _draw_ice_platform(surface, x, y, phase, skill):
        """Ice circle / snowflake pattern on the ground (basis di-cache)."""
        NS = _NS_varkul
        if NS._ground_cache is None:
            ring = pygame.Surface((130, 44), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 150),
                                (5, 10, 120, 24), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 180),
                                (20, 14, 90, 16), 2)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = 65 + int(math.cos(angle) * 20)
                y1 = 22 + int(math.sin(angle) * 4)
                x2 = 65 + int(math.cos(angle) * 55)
                y2 = 22 + int(math.sin(angle) * 10)
                pygame.draw.line(ring, (*NS.PALETTE["ice_light"], 170),
                                 (x1, y1), (x2, y2), 1)
            for angle_deg in (0, 90, 180, 270):
                angle = math.radians(angle_deg)
                sx = 65 + int(math.cos(angle) * 50)
                sy = 22 + int(math.sin(angle) * 9)
                pygame.draw.circle(ring, (*NS.PALETTE["ice_bright"], 200), (sx, sy), 2)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 65, y - 22))
        if skill:
            pygame.draw.ellipse(surface, (*NS.PALETTE["ice_bright"], int(80 * pulse)),
                                (x - 50, y - 14, 100, 28), 1)


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)

        # Flash from staff (opposite side)
        flash_x = x - 20 * facing
        flash_y = y - 20

        alpha = int(180 * intensity)
        radius = int(6 + intensity * 15)

        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        # Snowflake burst
        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_varkul._draw_snowflake(surface, ex, ey, 3, progress,
                            (*_NS_varkul.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # SKILL Q: FROST BLAST
    # ===================================================================
    def _draw_frost_blast_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 50))
        # Ground warning circle at impact
        radius = int(20 + progress * 40)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 100), (tx, ty), radius, 2)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 80), (tx, ty), radius + 5, 1)


    def _draw_frost_blast(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 50))

        start_x = x - 20 * boss.direction
        start_y = y - 20

        if progress < 0.4:
            # Traveling beam of frost
            travel_t = progress / 0.4
            cur_x = start_x + (tx - start_x) * travel_t
            cur_y = start_y + (ty - start_y) * travel_t

            # Comet trail
            for i in range(8):
                t = travel_t - i * 0.05
                if t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * t)
                py = int(start_y + (ty - start_y) * t)
                size = max(2, 10 - i)
                alpha = max(0, 200 - i * 25)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (px, py), size + 4)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (px, py), size + 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha), (px, py), size)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (px, py), max(1, size - 3))

            # Head of comet
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (int(cur_x), int(cur_y)), 14)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (int(cur_x), int(cur_y)), 10)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (int(cur_x), int(cur_y)), 4)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)

            # Ice shards around comet
            for i in range(5):
                angle = phase * 4 + i * math.pi * 2 / 5
                _NS_varkul._draw_ice_shard(surface, int(cur_x), int(cur_y), 8, angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        else:
            # Impact explosion
            exp_t = (progress - 0.4) / 0.6
            exp_r = int(40 * exp_t)
            alpha = int(255 * (1 - exp_t))

            # Explosion rings
            for i in range(3):
                r = exp_r - i * 5
                if r > 0:
                    _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha),
                              (tx, ty), r, 2)
                    _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha),
                              (tx, ty), max(1, r - 3), 1)

            # Radiating ice shards
            for i in range(12):
                angle = i * math.pi / 6
                dist = 15 + int(exp_r * 0.8)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.7)
                _NS_varkul._draw_ice_shard(surface, sx, sy, 8 + int(math.sin(phase) * 2),
                                angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

            # Central flash
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (tx, ty), 10)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha), (tx, ty), 15)


    # ===================================================================
    # SKILL W: FROSTBITE (encase target in ice)
    # ===================================================================
    def _draw_frostbite(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        if progress < 0.3:
            # Frost projectile flying to target
            t = progress / 0.3
            cur_x = x - 20 * boss.direction + (tx - (x - 20 * boss.direction)) * t
            cur_y = y - 20 + (ty - (y - 20)) * t

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 150),
                      (int(cur_x), int(cur_y)), 10)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (int(cur_x), int(cur_y)), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 5)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)
        else:
            # Ice prison forming
            t = (progress - 0.3) / 0.7
            size = int(20 + t * 15)

            # Ice block base
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_dark"], 200), [
                (tx - size, ty + size),
                (tx - size + 5, ty - size),
                (tx + size - 5, ty - size),
                (tx + size, ty + size),
            ])
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_mid"], 220), [
                (tx - size + 3, ty + size - 3),
                (tx - size + 7, ty - size + 3),
                (tx + size - 7, ty - size + 3),
                (tx + size - 3, ty + size - 3),
            ])
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_light"], 180), [
                (tx - size + 6, ty + size - 6),
                (tx - size + 10, ty - size + 6),
                (tx + size - 10, ty - size + 6),
                (tx + size - 6, ty + size - 6),
            ])

            # Ice shards around
            for i in range(8):
                angle = phase * 0.5 + i * math.pi / 4
                sx = tx + int(math.cos(angle) * size)
                sy = ty + int(math.sin(angle) * size * 0.7) - 5
                _NS_varkul._draw_ice_shard(surface, sx, sy,
                                6 + int(math.sin(phase + i) * 2),
                                angle - math.pi / 2,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

            # Shine on top
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["ice_hot"],
                    (tx - size + 8, ty - size + 4),
                    (tx - 2, ty - size + 4), 2)


    # ===================================================================
    # SKILL E: SACRIFICE (drain circle)
    # ===================================================================
    def _draw_sacrifice_circle(surface, boss, x, y, timer, phase):
        """Pentagram circle on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 50))
        radius = int(35 + progress * 25)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        circle = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Pentagram base circle
        pygame.draw.ellipse(circle, (*_NS_varkul.PALETTE["ice_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(circle, (*_NS_varkul.PALETTE["ice_mid"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Pentagram star
        star_points = []
        for i in range(5):
            a = -math.pi / 2 + i * math.pi * 2 / 5 + phase * 0.1
            px = cx + int(math.cos(a) * (radius - 8))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            star_points.append((px, py))
        for i in range(5):
            p1 = star_points[i]
            p2 = star_points[(i + 2) % 5]
            pygame.draw.line(circle, (*_NS_varkul.PALETTE["ice_light"], int(200 * pulse)),
                             p1, p2, 2)

        surface.blit(circle, (x - cx, y + 30 - cy))


    def _draw_sacrifice_foreground(surface, boss, x, y, timer, phase):
        """Rising soul energy from ground to Lich (lifecycle ikut timer AI)."""
        duration = 50
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        # Rising skull energy
        for i in range(6):
            t = (phase * 0.4 + i * 0.15) % 1.0
            offset_x = math.sin(phase + i * 0.7) * 15
            rx = x + int(offset_x)
            ry = y + 35 - int(t * 55)
            alpha = int(200 * (1 - t))
            size = 4 + int(t * 3)

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (rx, ry), size + 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (rx, ry), size)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (rx, ry), max(1, size - 2))


    # ===================================================================
    # SKILL R: CHAIN FROST
    # ===================================================================
    def _draw_chain_frost_ground(surface, boss, x, y, timer, phase):
        """Warning glow before launch."""
        progress = max(0.0, min(1.0, 1 - timer / 80))
        if progress < 0.3:
            # Charge up
            radius = int(15 + progress * 30)
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], int(150 * pulse)),
                      (x, y - 20), radius, 2)


    def _draw_chain_frost(surface, boss, x, y, timer, phase):
        """Draw chain frost orb + charging."""
        progress = max(0.0, min(1.0, 1 - timer / 80))

        if progress < 0.35:
            # Charging in hand
            charge = progress / 0.35
            cx, cy = x + boss.direction * 18, y - 15
            r = int(6 + charge * 10)

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 150), (cx, cy), r + 6)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 200), (cx, cy), r + 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (cx, cy), r)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (cx, cy), max(1, r - 3))
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (cx, cy), max(1, r - 5))

            # Ice shards forming
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                _NS_varkul._draw_ice_shard(surface, cx, cy, int(6 + charge * 4), angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        elif progress < 0.45 and not getattr(boss, "_vk_chain_launched", False):
            # Launch
            tx, ty = _NS_varkul._target_position(boss, x, y)
            if not hasattr(boss, "_vk_chain_orbs"):
                boss._vk_chain_orbs = []
            boss._vk_chain_orbs.append(
                _NS_varkul.ChainFrostOrb(x + boss.direction * 18, y - 15, tx, ty, bounces=4)
            )
            boss._vk_chain_launched = True

        if progress > 0.9:
            boss._vk_chain_launched = False


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_varkul.draw_varkul(surface, boss, x, y)


# ====================================================================
# XERATHIS
# ====================================================================
class _NS_xerathis:
    """Namespace xerathis - isi asli tidak diubah."""

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Crystal Maiden inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin
        "skin_darkest":   (150, 105,  85),
        "skin_dark":      (200, 150, 120),
        "skin_mid":       (235, 195, 165),
        "skin_light":     (250, 220, 195),
        "skin_high":      (255, 240, 220),

        # Hair (blonde)
        "hair_darkest":   (105,  75,  30),
        "hair_dark":      (165, 125,  55),
        "hair_mid":       (215, 175,  95),
        "hair_light":     (245, 215, 145),
        "hair_shine":     (255, 240, 195),

        # Robe – blue/purple
        "robe_darkest":   (18,  22,  58),
        "robe_dark":      (35,  50, 110),
        "robe_mid":       (65,  90, 175),
        "robe_light":     (110, 140, 220),
        "robe_high":      (160, 190, 245),

        # Cloak – deep purple
        "cloak_darkest":  (22,  15,  50),
        "cloak_dark":     (48,  32,  95),
        "cloak_mid":      (80,  55, 145),
        "cloak_light":    (125, 95, 195),

        # Fur trim (white)
        "fur_dark":       (155, 175, 200),
        "fur_mid":        (210, 225, 240),
        "fur_light":      (240, 248, 255),

        # Gold
        "gold_dark":      (95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 235, 165),

        # Ice / crystal
        "ice_darkest":    (10,  30,  75),
        "ice_dark":       (25,  70, 145),
        "ice_mid":        (70, 140, 225),
        "ice_light":      (140, 200, 250),
        "ice_bright":     (195, 230, 255),
        "ice_hot":        (225, 245, 255),
        "ice_white":      (245, 252, 255),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       (85, 145, 220),
        "eye_iris_light": (150, 200, 255),
        "eye_pupil":      (15,  30,  60),

        # Lips
        "lips_dark":      (170,  75,  85),
        "lips_mid":       (215, 115, 125),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xerathis._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_xerathis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_xerathis._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_xerathis._clamp(color)
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
        color = _NS_xerathis._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_xerathis._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


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
    # Ice / crystal visual helpers
    # ---------------------------------------------------------------------------
    def _draw_ice_shard(surface, cx, cy, size, angle, color_dark, color_mid,
                        color_light, color_hot):
        """Draw a single sharp ice crystal shard."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.35
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.35
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.35
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.35

        _NS_xerathis._poly(surface, color_dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        _NS_xerathis._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_xerathis._aaline(surface, color_light, (cx, cy), (tip_x, tip_y), 1)
        _NS_xerathis._aacircle(surface, color_hot, (int(tip_x), int(tip_y)), 1)


    def _draw_snowflake(surface, cx, cy, size, phase, color=None):
        """Small rotating snowflake."""
        if color is None:
            color = _NS_xerathis.PALETTE["ice_bright"]
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            x1 = cx + int(math.cos(angle) * size)
            y1 = cy + int(math.sin(angle) * size)
            _NS_xerathis._aaline(surface, color, (cx, cy), (x1, y1), 1)
            bx = cx + int(math.cos(angle) * size * 0.6)
            by = cy + int(math.sin(angle) * size * 0.6)
            for b in (-1, 1):
                ba = angle + b * 0.5
                ex = bx + int(math.cos(ba) * size * 0.3)
                ey = by + int(math.sin(ba) * size * 0.3)
                _NS_xerathis._aaline(surface, color, (bx, by), (ex, ey), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_hot"], (cx, cy), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Ice Shard Arrow
    # ---------------------------------------------------------------------------
    class IceShardProjectile:
        """Ice shard arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=6.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail - frost mist
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Glow
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (px, py), 12)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 150), (px, py), 8)

                # Ice arrow body - shard shape
                ca, sa = math.cos(self.angle), math.sin(self.angle)
                length = 14
                width = 4
                tip_x = px + ca * length
                tip_y = py + sa * length
                tail_x = px - ca * length * 0.7
                tail_y = py - sa * length * 0.7
                # Perpendicular offsets
                perp_x = -sa * width
                perp_y = ca * width

                # Dark outline
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                    (tip_x, tip_y),
                    (px + perp_x, py + perp_y),
                    (tail_x, tail_y),
                    (px - perp_x, py - perp_y),
                ])
                # Mid layer
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                    (tip_x - ca * 1, tip_y - sa * 1),
                    (px + perp_x * 0.7, py + perp_y * 0.7),
                    (tail_x + ca * 1, tail_y + sa * 1),
                    (px - perp_x * 0.7, py - perp_y * 0.7),
                ])
                # Light layer
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_light"], [
                    (tip_x - ca * 2, tip_y - sa * 2),
                    (px + perp_x * 0.4, py + perp_y * 0.4),
                    (tail_x + ca * 2, tail_y + sa * 2),
                    (px - perp_x * 0.4, py - perp_y * 0.4),
                ])
                # Bright core
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                        (px - ca * length * 0.5, py - sa * length * 0.5),
                        (tip_x, tip_y), 2)
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_white"],
                        (px, py), (tip_x - ca * 2, tip_y - sa * 2), 1)
                # Tip sparkle
                _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (int(tip_x), int(tip_y)), 2)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_xr_last_x"):
            boss._xr_last_x = boss.x
            boss._xr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xr_last_x)
        dy = abs(boss.y - boss._xr_last_y)
        boss._xr_last_x = boss.x
        boss._xr_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Backward-compatible alias ke controller V2."""
        return _NS_xerathis._update_xerathis_anim(
            boss, _NS_xerathis._detect_moving(boss))


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_xr_projectiles"):
            boss._xr_projectiles = []
        for proj in boss._xr_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._xr_projectiles = [p for p in boss._xr_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, x, y):
        if not hasattr(boss, "_xr_projectiles"):
            boss._xr_projectiles = []
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Staff tip position (front-facing side, raised up)
        sx = x + 26 * facing
        sy = y - 18
        boss._xr_projectiles.append(_NS_xerathis.IceShardProjectile(sx, sy, tx, ty, speed=6.5))


    # ===================================================================
    # V2 ANIMATION CONTROLLER + LIVE FX BRIDGE
    # ===================================================================

    #: Fase serangan (fraksi 0..1 dari durasi serangan).
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.16),
        ("WINDUP",       0.16, 0.32),
        ("SWING",        0.32, 0.50),
        ("IMPACT",       0.50, 0.64),
        ("FOLLOW",       0.64, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif (dipakai debug & game feel).
    ATTACK_ACTIVE_WINDOW = (0.38, 0.64)
    ATTACK_IMPACT_FRAME = 0.52

    #: Prioritas state. Angka besar menang; DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "SKILL": 50,
        "SPECIAL": 55,
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: Aktifkan hitbox/hurtbox/jangkauan/state di arena.
    DEBUG_CHARACTER = False

    #: Modul FX layar (diisi malas). False = percobaan gagal -> canvas.
    _LIVE_MOD = None

    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_xerathis.ATTACK_PHASES)

    def attack_phase(progress):
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_xerathis.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _live_module():
        """Muat ``heroes.xerathis_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_xerathis
        if NS._LIVE_MOD is None:
            try:
                from heroes import xerathis_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "XERATHIS_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        return _NS_xerathis._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini.

        Return ``(mod, owned)``. ``want_draw`` True pada jalur BOSS (draw
        dipanggil tiap frame tanpa cache sprite).
        """
        NS = _NS_xerathis
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    def _update_xerathis_anim(boss, moving=False):
        """ANIMATION CONTROLLER Xerathis - state, fase, timing, delta-time.

        Satu-satunya sumber kebenaran untuk SEMUA state karakter; lapisan
        hidup (heroes/xerathis_fx) serta alat uji membacanya dari sini.
        """
        G = _NS_xerathis

        # ── delta time nyata (dipakai FX & transisi state) ──────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                      # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_xr_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._xr_last_ms = now
        boss._xr_dt = dt

        # ── timeline serangan ───────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 59)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xr_previous_timer", 0))
        active = bool(getattr(boss, "_xr_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._xr_attack_active = True
            boss._xr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xr_attack_frame = int(getattr(boss, "_xr_attack_frame",
                                                0)) + 1
        elif timer <= 0 and active:
            # serangan manual (alat audit / probe): majukan sampai selesai
            boss._xr_attack_frame = int(getattr(boss, "_xr_attack_frame",
                                                0)) + 1
            if int(getattr(boss, "_xr_attack_frame", 0)) > cooldown:
                boss._xr_attack_active = False
                boss._xr_attack_frame = 0
                active = False

        boss._xr_previous_timer = timer
        if active:
            prog = min(1.0, int(getattr(boss, "_xr_attack_frame", 0))
                       / max(1, cooldown))
        else:
            prog = 0.0
        boss._xr_attack_progress = prog
        boss._xr_attack_raw = prog
        boss._xr_attack_phase = G.attack_phase(prog) if active else "NONE"
        boss._xr_hit_active = active and (G.ATTACK_ACTIVE_WINDOW[0] <= prog <
                                          G.ATTACK_ACTIVE_WINDOW[1])
        boss._xr_impact_frame = active and abs(prog - G.ATTACK_IMPACT_FRAME) < 0.025

        # ── hurt / hit flash ────────────────────────────────────────
        hurt = int(getattr(boss, "_xr_hurt_frames", 0) or 0)
        if hurt > 0:
            hurt -= 1
        if int(getattr(boss, "hurt_flash_timer", 0) or 0) > 0:
            hurt = max(hurt, 7)
        boss._xr_hurt_frames = hurt

        # ── resolve state ───────────────────────────────────────────
        if not getattr(boss, "alive", True):
            state = "DEATH"
        elif hurt > 0:
            state = "HURT"
        elif getattr(boss, "active_skill", None) is not None:
            state = ("SPECIAL" if getattr(boss, "active_skill", None) == "r"
                     else "SKILL")
        elif active:
            ph = boss._xr_attack_phase
            if ph in ("ANTICIPATION", "WINDUP"):
                state = "CHARGE"
            elif ph in ("SWING", "IMPACT"):
                state = "SWING"
            else:
                state = "ATTACK"
        elif moving:
            state = ("RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2
                     else "WALK")
        else:
            state = "IDLE"

        old = getattr(boss, "_xr_state", None)
        boss._xr_state_prev = old or state
        if old != state:
            boss._xr_state_time = 0.0
        else:
            boss._xr_state_time = (float(getattr(boss, "_xr_state_time", 0.0))
                                   + dt)
        boss._xr_state = state

    def _resolve_pose(boss, moving=False):
        """(action, phase, attack_progress) untuk renderer & FX."""
        skill = getattr(boss, "active_skill", None)
        active = bool(getattr(boss, "_xr_attack_active", False))
        if skill:
            action = "cast"
        elif active:
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        ap = (float(getattr(boss, "_xr_attack_progress", 0.0) or 0.0)
              if active else 0.0)
        return action, phase, ap

    def _staff_tip_screen(boss, x, y):
        """Titik kepala kristal staff untuk FX (semua FX memakai modul
        hidup, yang membacanya dari ``_resolve_pose``)."""
        action = getattr(boss, "_xr_pose_action", "idle")
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        if action == "attack":
            t = float(getattr(boss, "_xr_attack_progress", 0.0) or 0.0)
            ext = 1.0 if t < 0.5 else 0.55
            return (x + facing * (24 + ext * 10), y - 18)
        return (x + facing * 24, y - 54)

    def _draw_xerathis_debug(surface, boss, x, y):
        """Overlay DEBUG_CHARACTER: hitbox, state, frame, FPS."""
        NS = _NS_xerathis
        import pygame as _pg
        r = max(6, int(getattr(boss, "radius", 16)))
        _pg.draw.rect(surface, (80, 170, 255, 150),
                      _pg.Rect(int(x) - r, int(y) - r - 8, r * 2, r * 2), 1)
        rng = max(10, int(getattr(boss, "range", 200) * 0.7))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        _pg.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                      (int(x + rng * f), int(y)), 1)
        _pg.draw.rect(surface, (255, 210, 60, 110),
                      _pg.Rect(int(x + rng * f) - 5, int(y) - 7, 10, 14), 1)
        hb = None
        if getattr(boss, "_xr_hit_active", False):
            reach = int(rng)
            top = int(y - 38)
            left = int(x) if f > 0 else int(x) - reach
            hb = _pg.Rect(left, top, max(8, reach), max(10, 72))
            _pg.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            _pg.draw.rect(surface, (255, 70, 70, 60), hb)
        state = getattr(boss, "_xr_state", "IDLE")
        ph = getattr(boss, "_xr_attack_phase", "NONE")
        frames = int(getattr(boss, "_xr_attack_frame", 0))
        prog = float(getattr(boss, "_xr_attack_progress", 0.0))
        hurt = int(getattr(boss, "_xr_hurt_frames", 0))
        fps = getattr(boss, "_xr_fps", 60.0)
        dtv = float(getattr(boss, "_xr_dt", 1.0 / 60.0))
        inst = 1.0 / dtv if dtv > 0 else 60.0
        fps = fps + (inst - fps) * 0.1
        boss._xr_fps = fps
        lines = [
            f"XERATHIS {state} {ph}",
            f"frame {frames} t={prog:.2f} hurt={hurt}",
            f"hit={'Y' if hb else 'N'} fps={fps:.0f}",
            f"dt={dtv:.4f} proj={len(getattr(boss, '_xr_projectiles', []))}",
        ]
        font = None
        try:
            from _render import get_font
            font = get_font(14)
        except Exception:
            pass
        if font is None:
            return
        px, py = int(x) - 80, int(y) + 36
        for i, line in enumerate(lines):
            s = font.render(line, True, (220, 255, 230))
            surface.blit(s, (px, py + i * 14))

    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_xerathis(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan lapisan: GROUND -> SHADOW -> BODY/ARMOR/HEAD -> WEAPON ->
        ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL FX ->
        IMPACT FX -> DEBUG. Trail, proyektil, impact, hit-stop & shake
        hidup di ``heroes/xerathis_fx.py`` (lapisan layar 1:1).
        """
        NS = _NS_xerathis
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_xerathis_anim(boss, moving)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._xr_pose_action = action
        boss._xr_phase = phase
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)

        # ── lapisan hidup (boss jalur 1:1; lane dipicu heroes/__init__)
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)
        boss._xr_suppress_canvas_projectile = owned

        # ── GROUND LAYERS ──────────────────────────────────────────
        if not portrait:
            NS._draw_frost_aura(surface, x, y, pulse)
            NS._draw_ice_platform(surface, x, y + 40, pulse, active_skill)
            if active_skill == "q":
                NS._draw_crystal_nova_ground(surface, boss, x, y,
                                             skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_arcane_aura_ground(surface, boss, x, y,
                                            skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_freezing_field_ground(surface, boss, x, y,
                                               skill_timer, pulse)

        # ── CHARACTER BODY (dengan hurt-flash mask) ────────────────
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        if action == "attack":
            NS._draw_xerathis_attack(_tgt, boss, _tx, _ty)
        elif action in ("walk", "run"):
            NS._draw_xerathis_walk(_tgt, boss, _tx, _ty)
        else:
            NS._draw_xerathis_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ── FOREGROUND SKILL FX (canvas fallback) ──────────────────
        if not portrait:
            if active_skill == "q":
                NS._draw_crystal_nova(surface, boss, x, y, skill_timer,
                                      pulse)
            elif active_skill == "w":
                NS._draw_frostbite(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_arcane_aura_foreground(surface, boss, x, y,
                                                skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_freezing_field(surface, boss, x, y, skill_timer,
                                        pulse)

        # ── LIVE TOP LAYER (trail / projectile / impact / particle) ─
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_xerathis_debug(surface, boss, x, y)

    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_xerathis_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_xerathis._draw_shadow(surface, x, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_xerathis._draw_xerathis_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_xerathis_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_xerathis._draw_shadow(surface, x + sway, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_xerathis._draw_xerathis_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_xerathis_attack(surface, boss, x, y):
        progress = getattr(boss, "_xr_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.32 < progress < 0.42 and not getattr(boss, "_xr_proj_spawned", False):
            if not getattr(boss, "_xr_suppress_canvas_projectile", False):
                _NS_xerathis._spawn_projectile(boss, x, y)
            else:
                try:
                    from heroes import xerathis_fx as _xfx
                    _xfx.notify_projectile_cast(boss, x, y)
                except Exception:
                    pass
            boss._xr_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._xr_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_xerathis._draw_shadow(surface, x + recoil, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_xerathis._draw_xerathis_body(surface, x + recoil, y, boss.direction, boss.pulse,
                            "attack", progress)
        _NS_xerathis._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Crystal Maiden
    # ===================================================================
    def _draw_xerathis_body(surface, cx, cy, facing, phase, action,
                            attack_progress=0):
        """Komposit ORIGINAL-MAX: buffer tetap + outline + lighting."""
        _composite_boss_body(
            surface, _NS_xerathis, _NS_xerathis._draw_xerathis_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(110, 150, 240), bsize=180)

    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """ORIGINAL-MAX detail pass: wajah lebih terbaca + rim kiri-atas."""
        P = _NS_xerathis.PALETTE
        for ex in (-3, 3):
            pygame.draw.rect(surface, P["eye_white"], (cx + ex - 2, cy - 25, 4, 3))
            pygame.draw.rect(surface, P["eye_iris"], (cx + ex - 2, cy - 25, 3, 3))
            pygame.draw.rect(surface, P["eye_iris_light"], (cx + ex - 1, cy - 26, 1, 2))
            pygame.draw.line(surface, P["hair_darkest"], (cx + ex - 3, cy - 27), (cx + ex + 1, cy - 27), 1)
        pygame.draw.line(surface, P["hair_darkest"], (cx - 1, cy - 18), (cx + 1, cy - 18), 1)
        pygame.draw.rect(surface, P["lips_mid"], (cx - 2, cy - 16, 4, 2))
        pygame.draw.rect(surface, P["skin_light"], (cx - 1, cy - 16, 2, 1))
        for xo, yo in ((-9, -10), (-6, -14), (10, -8), (12, 2)):
            pygame.draw.circle(surface, P["fur_light"], (cx + xo, cy + yo), 2)
        pygame.draw.line(surface, P["fur_light"], (cx - 11, cy - 12), (cx - 13, cy + 6), 1)
        pygame.draw.line(surface, P["robe_high"], (cx - 9, cy - 12), (cx - 8, cy + 2), 1)
        pygame.draw.circle(surface, P["gold_shine"], (cx - 1, cy - 9), 1)
        st_x = cx + 24 * facing
        st_y = cy - 54
        pygame.draw.circle(surface, P["ice_hot"], (st_x - 1, st_y - 2), 2)
        pygame.draw.circle(surface, P["ice_white"], (st_x - 1, st_y - 2), 1)


    def _draw_xerathis_body_raw(surface, cx, cy, facing, phase, action,
                                attack_progress=0):
        # Cape/cloak behind
        _NS_xerathis._draw_cloak(surface, cx, cy, facing, phase, action)

        # Floating lower body (dress/skirt)
        _NS_xerathis._draw_dress(surface, cx, cy + 5, phase)

        # Torso
        _NS_xerathis._draw_torso(surface, cx, cy - 8, phase)

        # Arms
        if action == "attack":
            _NS_xerathis._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_xerathis._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head with hood
        _NS_xerathis._draw_head_hood(surface, cx, cy - 28, facing, phase)

        # Body frost particles
        _NS_xerathis._draw_body_particles(surface, cx, cy, phase)

        # ORIGINAL-MAX detail pass (wajah + rim)
        _NS_xerathis._masterwork_finish(surface, cx, cy, facing, phase, action,
                                        attack_progress)


    def _draw_cloak(surface, cx, cy, facing, phase, action):
        """Flowing purple cloak behind."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cloak
        cloak_outer = [
            (cx - 16, cy - 14),
            (cx - 22, cy + 5),
            (cx - 28 - int(wave), cy + 30),
            (cx - 20 - int(wave2), cy + 44),
            (cx - 5, cy + 48),
            (cx + 5, cy + 48),
            (cx + 20 + int(wave2), cy + 44),
            (cx + 28 + int(wave), cy + 30),
            (cx + 22, cy + 5),
            (cx + 16, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], cloak_outer)

        cloak_mid = [
            (cx - 14, cy - 12),
            (cx - 19, cy + 5),
            (cx - 24 - int(wave * 0.7), cy + 28),
            (cx - 15, cy + 40),
            (cx, cy + 42),
            (cx + 15, cy + 40),
            (cx + 24 + int(wave * 0.7), cy + 28),
            (cx + 19, cy + 5),
            (cx + 14, cy - 12),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], cloak_mid)

        # Inner (lighter)
        cloak_inner = [
            (cx - 11, cy - 8),
            (cx - 14, cy + 5),
            (cx - 18, cy + 24),
            (cx - 8, cy + 34),
            (cx + 8, cy + 34),
            (cx + 18, cy + 24),
            (cx + 14, cy + 5),
            (cx + 11, cy - 8),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_mid"], cloak_inner)

        # Fur trim on edges
        for i, (px, py) in enumerate([
            (cx - 22, cy - 8), (cx - 26, cy + 15), (cx - 22, cy + 38),
            (cx + 22, cy - 8), (cx + 26, cy + 15), (cx + 22, cy + 38),
        ]):
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_dark"], (px, py), 4)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_mid"], (px - 1, py - 1), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_light"], (px - 1, py - 1), 2)


    def _draw_dress(surface, cx, cy, phase):
        """Floating lower dress (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        # Outer skirt
        skirt = [
            (cx - 16, cy),
            (cx + 16, cy),
            (cx + 20 + sway, cy + 14),
            (cx + 15, cy + 24),
            (cx + 7, cy + 30),
            (cx + 2, cy + 32),
            (cx - 2, cy + 32),
            (cx - 7, cy + 30),
            (cx - 15, cy + 24),
            (cx - 20 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in skirt])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], skirt)

        skirt_mid = [
            (cx - 13, cy + 2),
            (cx + 13, cy + 2),
            (cx + 16 + sway, cy + 14),
            (cx + 10, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 10, cy + 22),
            (cx - 16 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_dark"], skirt_mid)

        skirt_inner = [
            (cx - 9, cy + 4),
            (cx + 9, cy + 4),
            (cx + 12 + sway, cy + 14),
            (cx + 6, cy + 20),
            (cx - 6, cy + 20),
            (cx - 12 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_mid"], skirt_inner)

        # Skirt highlight lines
        for i in range(3):
            lx = cx - 8 + i * 8
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"],
                    (lx, cy + 5), (lx + int(sway * 0.3), cy + 25), 1)

        # Tattered bottom (dress fringe)
        for i in range(7):
            tx = cx - 14 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 2)
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 3), (tx - 1, ty + 3),
            ])

        # Gold belt with buckle
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_dark"], (cx - 17, cy - 1, 34, 5))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_mid"], (cx - 15, cy, 30, 3))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_light"], (cx - 13, cy + 1, 26, 1))

        # Belt center gem
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_darkest"], (cx, cy + 1), 4)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_dark"], (cx, cy + 1), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_light"], (cx - 1, cy), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Blue corset/bodice."""
        # Shadow
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"], [
            (cx - 11 + 2, cy - 8 + 2), (cx + 11 + 2, cy - 8 + 2),
            (cx + 10 + 2, cy + 14 + 2), (cx + 4 + 2, cy + 18 + 2),
            (cx - 4 + 2, cy + 18 + 2), (cx - 10 + 2, cy + 14 + 2),
        ])
        # Corset base
        torso = [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 10, cy + 14), (cx + 4, cy + 18),
            (cx - 4, cy + 18), (cx - 10, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], torso)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_dark"], [
            (cx - 10, cy - 7), (cx + 10, cy - 7),
            (cx + 8, cy + 12), (cx + 3, cy + 15),
            (cx - 3, cy + 15), (cx - 8, cy + 12),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 10), (cx + 2, cy + 12),
            (cx - 2, cy + 12), (cx - 6, cy + 10),
        ])

        # Chest/skin area (top of bodice)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_dark"], [
            (cx - 7, cy - 9), (cx + 7, cy - 9),
            (cx + 5, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_mid"], [
            (cx - 6, cy - 9), (cx + 6, cy - 9),
            (cx + 4, cy - 6), (cx - 4, cy - 6),
        ])
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["skin_light"],
                (cx - 4, cy - 8), (cx + 4, cy - 8), 1)

        # Corset lacing (X pattern)
        for i in range(3):
            y_off = cy - 3 + i * 5
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"],
                    (cx - 3, y_off), (cx + 3, y_off + 3), 1)
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"],
                    (cx + 3, y_off), (cx - 3, y_off + 3), 1)

        # Center gem on chest
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["gold_dark"], (cx, cy - 1), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_mid"], (cx, cy - 1), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (cx, cy - 2), 1)

        # Side highlights on corset
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"],
                (cx - 9, cy - 5), (cx - 8, cy + 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle arms - one holds staff, other rests."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm (facing side - holding staff up)
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy - 4 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y - 4
        _NS_xerathis._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_xerathis._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_xerathis._draw_hand(surface, sh_x, sh_y)
        # Staff
        _NS_xerathis._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # OTHER arm (opposite side - resting)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 5
        oe_y = cy + 10 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 8
        _NS_xerathis._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_xerathis._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_xerathis._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose - staff aimed forward for casting."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm extends forward for aim/cast
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2

        # Aim/thrust motion
        if progress < 0.3:
            t = progress / 0.3
            ext = t * 0.4  # slight windup
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            ext = 0.4 + t * 0.6  # thrust forward
        else:
            t = (progress - 0.5) / 0.5
            ext = 1.0 - t * 0.6

        # Aim angle - slight upward
        aim_angle = -0.15
        se_x = ss_x + int((6 + ext * 4) * math.cos(aim_angle)) * staff_side
        se_y = ss_y + int((6 + ext * 4) * math.sin(aim_angle)) - 2
        sh_x = se_x + int((6 + ext * 6) * math.cos(aim_angle)) * staff_side
        sh_y = se_y + int((6 + ext * 6) * math.sin(aim_angle)) - 4

        _NS_xerathis._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_xerathis._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_xerathis._draw_hand(surface, sh_x, sh_y)
        _NS_xerathis._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # OTHER arm (steadying - held out slightly)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 6
        oe_y = cy + 6 + sway
        oh_x = oe_x + other_side * 4
        oh_y = oe_y + 6
        _NS_xerathis._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_xerathis._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_xerathis._draw_hand(surface, oh_x, oh_y)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 6)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_dark"], (x1, y1), (x2, y2), 4)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_mid"], (x1, y1), (x2, y2), 2)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Small skin-colored hand."""
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_darkest"], (x, y), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_mid"], (x, y), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (x - 1, y - 1), 1)


    def _draw_staff(surface, x, y, phase, side, casting=False, progress=0):
        """The crystal staff."""
        # Staff pole - long, from hand upward and behind
        top_x = x + side * 4
        top_y = y - 38
        bot_x = x - side * 2
        bot_y = y + 16

        # Shadow
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wooden staff (gold-colored)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_dark"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_light"], (top_x, top_y), (bot_x, bot_y), 1)

        # Wraps/rings on staff
        for t in (0.35, 0.65, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["cloak_dark"], (rx, ry), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["cloak_mid"], (rx, ry), 2)

        # Staff head - crystal cluster
        head_x, head_y = top_x, top_y - 4

        glow_size = 8
        if casting:
            glow_size = 8 + int(math.sin(progress * math.pi) * 12)

        # Backing glow
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (head_x, head_y), glow_size + 4)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 160), (head_x, head_y), glow_size)

        # Gold claws holding the crystal
        for offset_a in (-1.0, -0.3, 0.3, 1.0):
            cx1 = head_x + int(math.cos(math.pi / 2 + offset_a) * 3)
            cy1 = head_y + int(math.sin(math.pi / 2 + offset_a) * 3)
            cx2 = head_x + int(math.cos(math.pi / 2 + offset_a) * 8)
            cy2 = head_y + int(math.sin(math.pi / 2 + offset_a) * 8) - 3
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_dark"], (cx1, cy1), (cx2, cy2), 3)
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Large main ice crystal - vertical
        crystal_h = 10
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
            (head_x - 4, head_y),
            (head_x + 4, head_y),
            (head_x + 3, head_y - crystal_h + 2),
            (head_x, head_y - crystal_h),
            (head_x - 3, head_y - crystal_h + 2),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
            (head_x - 3, head_y - 1),
            (head_x + 3, head_y - 1),
            (head_x + 2, head_y - crystal_h + 3),
            (head_x, head_y - crystal_h + 1),
            (head_x - 2, head_y - crystal_h + 3),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
            (head_x - 2, head_y - 2),
            (head_x + 2, head_y - 2),
            (head_x + 1, head_y - crystal_h + 4),
            (head_x, head_y - crystal_h + 2),
            (head_x - 1, head_y - crystal_h + 4),
        ])
        # Bright highlight
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                (head_x - 1, head_y - crystal_h + 3),
                (head_x - 1, head_y - 2), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (head_x - 1, head_y - crystal_h + 4), 1)

        # Small side crystals
        _NS_xerathis._draw_ice_shard(surface, head_x - 3, head_y - 3, 4, -math.pi / 2 - 0.4,
                        _NS_xerathis.PALETTE["ice_dark"], _NS_xerathis.PALETTE["ice_mid"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])
        _NS_xerathis._draw_ice_shard(surface, head_x + 3, head_y - 3, 4, -math.pi / 2 + 0.4,
                        _NS_xerathis.PALETTE["ice_dark"], _NS_xerathis.PALETTE["ice_mid"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

        # Pulsing glow
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(80 * pulse)),
                  (head_x, head_y - 4), int(6 * pulse))


    def _draw_head_hood(surface, cx, cy, facing, phase):
        """Crystal Maiden's face with hood and hair."""
        # Hood back (behind head)
        hood_back = [
            (cx - 12, cy - 6),
            (cx - 14, cy + 4),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 14, cy + 4),
            (cx + 12, cy - 6),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in hood_back])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], hood_back)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], [
            (cx - 11, cy - 5),
            (cx - 13, cy + 4),
            (cx - 11, cy + 11),
            (cx + 11, cy + 11),
            (cx + 13, cy + 4),
            (cx + 11, cy - 5),
            (cx + 7, cy - 13),
            (cx - 7, cy - 13),
        ])

        # Hair fringe (blonde, visible under hood)
        hair_points = [
            (cx - 8, cy - 6),
            (cx - 9, cy - 2),
            (cx - 7, cy + 1),
            (cx - 3, cy - 1),
            (cx, cy),
            (cx + 3, cy - 1),
            (cx + 7, cy + 1),
            (cx + 9, cy - 2),
            (cx + 8, cy - 6),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_darkest"], hair_points)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy - 2),
            (cx - 6, cy),
            (cx - 2, cy - 1),
            (cx + 2, cy - 1),
            (cx + 6, cy),
            (cx + 8, cy - 2),
            (cx + 7, cy - 5),
        ])
        # Hair highlight
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx - 5, cy - 4), (cx - 3, cy - 2), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_light"],
                (cx + 3, cy - 4), (cx + 5, cy - 3), 1)

        # Face (skin)
        face_points = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx - 2, cy + 10),
            (cx + 2, cy + 10),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 6, cy),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_darkest"],
              [(p[0] + 1, p[1] + 1) for p in face_points])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_dark"], face_points)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_mid"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 4, cy + 7),
            (cx - 2, cy + 9),
            (cx + 2, cy + 9),
            (cx + 4, cy + 7),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
        ])
        # Cheek highlights
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (cx - 3, cy + 5), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (cx + 3, cy + 5), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_high"], (cx - 3, cy + 5), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_high"], (cx + 3, cy + 5), 1)

        # Eyes
        for eye_x in (-3, 3):
            # Eye white
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_white"], (cx + eye_x - 1, cy + 3, 2, 2))
            # Iris
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_iris"], (cx + eye_x - 1, cy + 3, 2, 2))
            # Bright center
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_iris_light"], (cx + eye_x, cy + 3, 1, 1))

        # Eyelashes/brows
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_darkest"],
                (cx - 5, cy + 2), (cx - 1, cy + 2), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_darkest"],
                (cx + 1, cy + 2), (cx + 5, cy + 2), 1)

        # Nose (subtle)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_darkest"], (cx, cy + 6), 1)

        # Lips
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["lips_dark"], (cx - 2, cy + 8, 4, 1))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["lips_mid"], (cx - 1, cy + 8, 2, 1))

        # Hood top (in front, framing the face)
        hood_top = [
            (cx - 11, cy - 5),
            (cx - 13, cy - 2),
            (cx - 10, cy + 2),
            (cx - 8, cy - 2),
            (cx - 6, cy - 8),
            (cx, cy - 12),
            (cx + 6, cy - 8),
            (cx + 8, cy - 2),
            (cx + 10, cy + 2),
            (cx + 13, cy - 2),
            (cx + 11, cy - 5),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], hood_top)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], [
            (cx - 10, cy - 4),
            (cx - 11, cy - 2),
            (cx - 9, cy + 1),
            (cx - 8, cy - 3),
            (cx - 6, cy - 7),
            (cx, cy - 11),
            (cx + 6, cy - 7),
            (cx + 8, cy - 3),
            (cx + 9, cy + 1),
            (cx + 11, cy - 2),
            (cx + 10, cy - 4),
            (cx + 7, cy - 13),
            (cx - 7, cy - 13),
        ])
        # Hood mid highlight
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_mid"], [
            (cx - 8, cy - 6),
            (cx - 9, cy - 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 6),
            (cx, cy - 9),
            (cx + 5, cy - 6),
            (cx + 7, cy - 1),
            (cx + 9, cy - 3),
            (cx + 8, cy - 6),
            (cx + 6, cy - 11),
            (cx - 6, cy - 11),
        ])

        # White fur trim on hood
        for i in range(9):
            angle = -math.pi + i * math.pi / 8
            fx = cx + int(math.cos(angle) * 12)
            fy = cy - 4 + int(math.sin(angle) * 9)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_dark"], (fx, fy), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_mid"], (fx - 1, fy - 1), 2)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_light"], (fx - 1, fy - 1), 1)

        # Ice crystal on top of hood
        _NS_xerathis._draw_ice_shard(surface, cx, cy - 15, 5, -math.pi / 2,
                        _NS_xerathis.PALETTE["ice_darkest"], _NS_xerathis.PALETTE["ice_dark"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

        # Small ear/hair strands on sides
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx - 8, cy + 2), (cx - 10, cy + 6), (cx - 7, cy + 8)
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx + 8, cy + 2), (cx + 10, cy + 6), (cx + 7, cy + 8)
        ])
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx - 8, cy + 3), (cx - 9, cy + 6), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx + 8, cy + 3), (cx + 9, cy + 6), 1)


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating frost particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], alpha), (px, py), 1)

        # Falling snowflakes
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 30 + i * 20 + int(math.sin(phase + i) * 5)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_xerathis._draw_snowflake(surface, fx, fy, 3,
                            phase + i, (*_NS_xerathis.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Frost mist beneath floating Xerathis."""
        NS = _NS_xerathis
        if NS._mist_cache is None:
            mist = pygame.Surface((120, 40), pygame.SRCALPHA)
            for radius in range(30, 3, -4):
                alpha = int((30 - radius) * 2.8)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*NS.PALETTE["ice_dark"], min(255, alpha)),
                        (60 - radius * 2, 20 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            NS._mist_cache = mist
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 60, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting frost crystals
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_mid"], (sx, sy), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (sx, sy), 2)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y, lift=0):
        """Ground shadow (cache + reaktif saat lift)."""
        NS = _NS_xerathis
        if NS._shadow_cache is None:
            shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 16)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["ice_dark"], 40), (8, 4, 84, 10))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 10) - h          # dasar tetap menapak di y+10
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase):
        """Large background aura (basis di-cache, denyut via alpha)."""
        NS = _NS_xerathis
        if NS._aura_cache is None:
            aura = pygame.Surface((180, 160), pygame.SRCALPHA)
            for radius in range(70, 5, -4):
                alpha = int((70 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                                 (90, 80), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.2, min(1.0, pulse))))
        surface.blit(spr, (x - 90, y - 80))


    def _draw_ice_platform(surface, x, y, phase, skill):
        """Ice snowflake pattern on the ground (basis di-cache)."""
        NS = _NS_xerathis
        if NS._ground_cache is None:
            ring = pygame.Surface((130, 44), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 150),
                                (5, 10, 120, 24), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 180),
                                (20, 14, 90, 16), 2)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = 65 + int(math.cos(angle) * 20)
                y1 = 22 + int(math.sin(angle) * 4)
                x2 = 65 + int(math.cos(angle) * 55)
                y2 = 22 + int(math.sin(angle) * 10)
                pygame.draw.line(ring, (*NS.PALETTE["ice_light"], 170),
                                 (x1, y1), (x2, y2), 1)
            for angle_deg in (0, 90, 180, 270):
                angle = math.radians(angle_deg)
                sx = 65 + int(math.cos(angle) * 50)
                sy = 22 + int(math.sin(angle) * 9)
                pygame.draw.circle(ring, (*NS.PALETTE["ice_bright"], 200), (sx, sy), 2)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 65, y - 22))
        if skill:
            pygame.draw.ellipse(surface, (*NS.PALETTE["ice_bright"], int(80 * pulse)),
                                (x - 50, y - 14, 100, 28), 1)


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack (at staff tip)."""
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)

        flash_x = x + 26 * facing
        flash_y = y - 18

        alpha = int(180 * intensity)
        radius = int(6 + intensity * 15)

        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_xerathis._draw_snowflake(surface, ex, ey, 3, progress,
                            (*_NS_xerathis.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # SKILL Q: CRYSTAL NOVA (AoE ice explosion at target)
    # ===================================================================
    def _draw_crystal_nova_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))
        # Warning circle
        radius = int(25 + progress * 45)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (tx, ty), radius, 2)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 80), (tx, ty), radius + 6, 1)


    def _draw_crystal_nova(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        if progress < 0.35:
            # Casting phase - energy gathering above target
            t = progress / 0.35
            # Rising energy above target
            for i in range(5):
                offset = i * 0.15
                it = min(1.0, t + offset)
                gy = ty - int(it * 30)
                alpha = int(180 * (1 - offset))
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha),
                          (tx, gy), max(1, 4 - i))
        else:
            # Nova explosion phase
            t = (progress - 0.35) / 0.65

            # Central burst
            burst_r = int(20 + t * 25)
            alpha = int(220 * (1 - t))

            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (tx, ty), burst_r + 4)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha), (tx, ty), burst_r)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (tx, ty), burst_r // 2)

            # Radial ice crystals rising from ground
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.05
                dist = int(15 + t * 30)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.6)

                # Rising crystal
                grow = min(1.0, t * 2.0)
                size = int(12 * grow)

                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                    (sx - 4, sy + size // 2),
                    (sx + 4, sy + size // 2),
                    (sx + 2, sy - size),
                    (sx, sy - size - 2),
                    (sx - 2, sy - size),
                ])
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
                    (sx - 3, sy + size // 2 - 1),
                    (sx + 3, sy + size // 2 - 1),
                    (sx + 1, sy - size + 1),
                    (sx, sy - size - 1),
                    (sx - 1, sy - size + 1),
                ])
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                    (sx - 2, sy + size // 2 - 2),
                    (sx + 2, sy + size // 2 - 2),
                    (sx + 1, sy - size + 2),
                    (sx - 1, sy - size + 2),
                ])
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                        (sx, sy + size // 2 - 2), (sx, sy - size + 2), 1)
                _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (sx, sy - size), 1)

            # Ring shockwave
            ring_r = int(40 + t * 30)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], int(150 * (1 - t))),
                      (tx, ty), ring_r, 2)


    # ===================================================================
    # SKILL W: FROSTBITE
    # ===================================================================
    def _draw_frostbite(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 50))

        start_x = x + 26 * boss.direction
        start_y = y - 18

        if progress < 0.35:
            # Frost bolt flying to target
            t = progress / 0.35
            cur_x = start_x + (tx - start_x) * t
            cur_y = start_y + (ty - start_y) * t

            # Trail
            for i in range(6):
                tt = t - i * 0.05
                if tt <= 0:
                    continue
                px = int(start_x + (tx - start_x) * tt)
                py = int(start_y + (ty - start_y) * tt)
                alpha = max(0, 200 - i * 30)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (px, py), 6 - i // 2)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (px, py), 3)

            # Bolt head
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 200),
                      (int(cur_x), int(cur_y)), 12)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 7)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (int(cur_x), int(cur_y)), 4)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)
        else:
            # Target is frozen - ice encasing
            t = (progress - 0.35) / 0.65
            size = int(18 + t * 8)

            # Ice block encasing target
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_dark"], 220), [
                (tx - size, ty + size),
                (tx - size + 4, ty - size),
                (tx + size - 4, ty - size),
                (tx + size, ty + size),
            ])
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_mid"], 200), [
                (tx - size + 3, ty + size - 3),
                (tx - size + 6, ty - size + 3),
                (tx + size - 6, ty - size + 3),
                (tx + size - 3, ty + size - 3),
            ])
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_light"], 160), [
                (tx - size + 6, ty + size - 6),
                (tx - size + 9, ty - size + 6),
                (tx + size - 9, ty - size + 6),
                (tx + size - 6, ty + size - 6),
            ])

            # Ice crystals sticking out
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                sx = tx + int(math.cos(angle) * size)
                sy = ty + int(math.sin(angle) * size * 0.7) - 3
                _NS_xerathis._draw_ice_shard(surface, sx, sy,
                                5 + int(math.sin(phase + i) * 1),
                                angle - math.pi / 2,
                                _NS_xerathis.PALETTE["ice_darkest"], _NS_xerathis.PALETTE["ice_dark"],
                                _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

            # Shine highlight
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_hot"],
                    (tx - size + 8, ty - size + 4),
                    (tx - 2, ty - size + 4), 2)


    # ===================================================================
    # SKILL E: ARCANE AURA (buffs self)
    # ===================================================================
    def _draw_arcane_aura_ground(surface, boss, x, y, timer, phase):
        """Aura circle around Xerathis on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 20)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        aura = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Ring
        pygame.draw.ellipse(aura, (*_NS_xerathis.PALETTE["ice_mid"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(aura, (*_NS_xerathis.PALETTE["ice_bright"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runic marks around aura
        for i in range(8):
            a = phase * 0.3 + i * math.pi / 4
            px = cx + int(math.cos(a) * (radius - 5))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            pygame.draw.circle(aura, (*_NS_xerathis.PALETTE["ice_hot"], int(220 * pulse)),
                               (px, py), 3)
            pygame.draw.circle(aura, (*_NS_xerathis.PALETTE["ice_white"], int(220 * pulse)),
                               (px, py), 1)

        surface.blit(aura, (x - cx, y + 30 - cy))


    def _draw_arcane_aura_foreground(surface, boss, x, y, timer, phase):
        """Rising magical energy around Xerathis."""
        duration = 90
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        # Rising energy particles all around body
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.3
            dist = 20 + int(math.sin(phase + i) * 5)
            sx = x + int(math.cos(angle) * dist)
            sy = y + 30 - int(t * 70)
            alpha = int(200 * (1 - t))
            size = 3 + int(t * 3)

            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (sx, sy), size + 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (sx, sy), size)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], alpha), (sx, sy), max(1, size - 2))

        # Pulsing halo around body
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        halo_r = int(40 * pulse)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(60 * pulse)),
                  (x, y - 10), halo_r, 2)


    # ===================================================================
    # SKILL R: FREEZING FIELD
    # ===================================================================
    def _draw_freezing_field_ground(surface, boss, x, y, timer, phase):
        """Large ice field around Xerathis."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        radius = int(60 + progress * 30)
        pulse = math.sin(phase * 1.2) * 0.2 + 0.8

        field = pygame.Surface((radius * 2 + 30, radius + 30), pygame.SRCALPHA)
        cx, cy = radius + 15, (radius + 30) // 2

        # Base ice ring
        pygame.draw.ellipse(field, (*_NS_xerathis.PALETTE["ice_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 20, radius + 20), 4)
        pygame.draw.ellipse(field, (*_NS_xerathis.PALETTE["ice_mid"], int(140 * pulse)),
                            (20, 12, radius * 2 - 10, radius + 6), 2)

        # Frost pattern
        for i in range(12):
            a = phase * 0.2 + i * math.pi / 6
            x1 = cx + int(math.cos(a) * 15)
            y1 = cy + int(math.sin(a) * 5)
            x2 = cx + int(math.cos(a) * (radius - 5))
            y2 = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.line(field, (*_NS_xerathis.PALETTE["ice_light"], int(150 * pulse)),
                             (x1, y1), (x2, y2), 1)

        surface.blit(field, (x - cx, y + 30 - cy))


    def _draw_freezing_field(surface, boss, x, y, timer, phase):
        """Randomly exploding ice crystals in the field."""
        duration = 100
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        # Deterministic random positions using phase
        for i in range(8):
            # Each crystal has its own life cycle
            crystal_phase = (phase * 0.4 + i * 0.35) % 1.0
            angle = i * math.pi / 4 + i * 0.7
            dist_r = 40 + (i * 13) % 30
            px = x + int(math.cos(angle) * dist_r)
            py = y + 25 + int(math.sin(angle) * dist_r * 0.3)

            # Grow then shrink cycle
            if crystal_phase < 0.5:
                grow = crystal_phase / 0.5
            else:
                grow = 1.0 - (crystal_phase - 0.5) / 0.5

            size = int(14 * grow)
            if size < 2:
                continue

            # Ice crystal spike shooting up
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                (px - 5, py + size // 2),
                (px + 5, py + size // 2),
                (px + 3, py - size),
                (px, py - size - 3),
                (px - 3, py - size),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
                (px - 4, py + size // 2 - 1),
                (px + 4, py + size // 2 - 1),
                (px + 2, py - size + 1),
                (px, py - size - 2),
                (px - 2, py - size + 1),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                (px - 3, py + size // 2 - 2),
                (px + 3, py + size // 2 - 2),
                (px + 1, py - size + 2),
                (px, py - size - 1),
                (px - 1, py - size + 2),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_light"], [
                (px - 2, py + size // 2 - 3),
                (px + 2, py + size // 2 - 3),
                (px + 1, py - size + 3),
                (px - 1, py - size + 3),
            ])
            # Highlight
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                    (px, py + size // 2 - 3), (px, py - size + 3), 1)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (px, py - size), 1)

            # Impact glow at base
            if grow > 0.3:
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(150 * grow)),
                          (px, py + size // 2), int(size * 0.8))

        # Continuous swirling frost energy
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            r = 55
            sx = x + int(math.cos(angle) * r)
            sy = y + 25 + int(math.sin(angle) * r * 0.35)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], 180), (sx, sy), 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], 220), (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_xerathis.draw_xerathis(surface, boss, x, y)


# ====================================================================
# NYZRAK  —  FULL REWRITE (pixel-art rig + animation controller + arc swing)
#
# Wyvern Rider "The Hollow Blizzard".  Seluruh visual prosedural: rig
# digambar pada canvas LOW-RES (110x110) lalu di-nearest-scale 2x ->
# piksel chunky 2x2 dengan tepi keras, band cel-shading 3 nada, siluet
# kuat.  Gerak dikendalikan _NyzAnimController (state + prioritas +
# sub-fase timing anticipation->recovery).  Serangan tombak berbasis
# ARC (bukan teleport posisi).  Efek 60fps (trail, partikel, beam,
# impact, hit-stop, shake) hidup di heroes/nyzrak_fx.py — canvas di
# sini hanya fallback saat modul itu tidak tersedia (portrait/tools).
# ====================================================================
class _NS_nyzrak:
    """Namespace nyzrak — rig pixel-art + animasi + swing arc."""

    # ── Buffer cache (dibangun lazy, dipakai ulang antar frame) ──────
    _body_buf = None        # canvas komposit 220x220 (outline+lighting)
    _rig_buf = None         # canvas rig low-res (pixel-art asli)
    _scale_buf = None       # target scale 2x (dipakai ulang, tanpa alloc)
    _flash_buf = None       # buffer hurt-flash
    _record_shadow = None   # rect bayangan -> dikecualikan dari flash
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    #: Ukuran "fat pixel" — rig digambar setengah resolusi lalu di-scale.
    PIXEL = 2
    RIG_SIZE = 110          # sisi canvas rig low-res
    GROUND_DY = 55          # jangkar -> garis tanah (piksel layar)
    LIFT = 4                # tinggi hover wyvern di atas bayangan

    #: Penanda varian serangan aktif untuk _spear_pose_geom (stateless).
    _pose_variant_now = "thrust"

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # PALETTE — winter wyvern (satu sumber kebenaran warna untuk rig,
    # FX canvas, dan heroes/nyzrak_fx.py via _sync_palette)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Wyvern body - teal/cyan
        "wy_darkest":     (5,   30,  40),
        "wy_dark":        (18,  70,  90),
        "wy_mid":         (45, 135, 155),
        "wy_light":       (95, 190, 210),
        "wy_high":        (155, 225, 235),
        "wy_shine":       (215, 245, 250),

        # Wyvern belly (lighter)
        "belly_dark":     (85, 140, 155),
        "belly_mid":      (140, 195, 210),
        "belly_light":    (200, 235, 245),

        # Wing membrane (blue-purple)
        "wing_darkest":   (18,  20,  55),
        "wing_dark":      (45,  55, 115),
        "wing_mid":       (85, 100, 175),
        "wing_light":     (140, 165, 220),

        # Rider - purple/blue robe
        "robe_darkest":   (25,  20,  55),
        "robe_dark":      (55,  50, 105),
        "robe_mid":       (95,  90, 155),
        "robe_light":     (150, 145, 200),
        "robe_high":      (200, 195, 235),

        # Fur trim (white)
        "fur_dark":       (155, 165, 185),
        "fur_mid":        (210, 220, 235),
        "fur_light":      (245, 250, 255),

        # Rider skin (fair)
        "skin_dark":      (185, 145, 130),
        "skin_mid":       (230, 195, 175),
        "skin_light":     (250, 225, 210),

        # Hair (blonde/white)
        "hair_dark":      (185, 155, 100),
        "hair_mid":       (225, 200, 145),
        "hair_light":     (250, 235, 190),

        # Ice / crystal
        "ice_darkest":    (8,   35,  75),
        "ice_dark":       (30,  85, 155),
        "ice_mid":        (75, 155, 220),
        "ice_light":      (150, 210, 245),
        "ice_bright":     (200, 235, 250),
        "ice_hot":        (230, 245, 255),
        "ice_pure":       (250, 253, 255),

        # Purple frost (Q skill)
        "frost_darkest":  (25,  10,  60),
        "frost_dark":     (65,  30, 130),
        "frost_mid":      (125, 75, 200),
        "frost_light":    (175, 130, 240),
        "frost_bright":   (215, 180, 255),
        "frost_hot":      (240, 220, 255),

        # Metal (spear/armor)
        "metal_darkest":  (18,  18,  25),
        "metal_dark":     (48,  55,  70),
        "metal_mid":      (105, 115, 135),
        "metal_light":    (170, 180, 200),
        "metal_shine":    (225, 230, 245),

        # Gold accents (small)
        "gold_mid":       (200, 165,  60),
        "gold_light":     (240, 210, 110),

        # Eyes
        "eye_dark":       (10,  30,  60),
        "eye_bright":     (140, 210, 255),
        "eye_hot":        (220, 240, 255),

        # Wyvern eye (orange/red - fierce)
        "wy_eye_dark":    (85,  25,  10),
        "wy_eye_bright":  (255, 130,  40),
        "wy_eye_hot":     (255, 210, 120),

        # Teeth
        "bone_dark":      (155, 145, 115),
        "bone_light":     (240, 230, 200),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   5,  10),
        "white":          (255, 255, 255),
    }

    # ===================================================================
    # ANIMATION CONTROLLER
    #
    # Pose adalah fungsi MURNI dari atribut simulasi — pipeline hero
    # meng-cache sprite, jadi controller tidak boleh menyimpan state
    # antar-gambar.  "Delta time" = langkah tetap 1/60 s yang sudah
    # diintegrasi game ke boss.pulse (+0.05/step), timer serangan, dan
    # timer skill (frame @60fps).
    # ===================================================================
    STATE_IDLE = "IDLE"
    STATE_WALK = "WALK"
    STATE_RUN = "RUN"
    STATE_ATTACK = "ATTACK"      # varian thrust (ranged)
    STATE_SWING = "SWING"        # varian sweep (melee)
    STATE_CAST = "CAST"
    STATE_SKILL = "SKILL"
    STATE_HIT = "HIT"
    STATE_HURT = "HURT"
    STATE_DEATH = "DEATH"
    STATE_CHARGE = "CHARGE"
    STATE_SPECIAL = "SPECIAL"

    #: Prioritas — state bernilai tinggi menang selama durasinya.
    STATE_PRIORITY = {
        "IDLE": 0, "WALK": 10, "RUN": 20, "CHARGE": 45, "CAST": 50,
        "ATTACK": 55, "SWING": 60, "SPECIAL": 65, "SKILL": 70,
        "HIT": 80, "HURT": 90, "DEATH": 100,
    }

    #: Durasi bingkai (detik) per state untuk frame-index controller.
    FRAME_DUR = {
        "IDLE": 0.125, "WALK": 0.083, "RUN": 0.058, "ATTACK": 0.016,
        "SWING": 0.016, "CAST": 0.10, "SKILL": 0.033, "CHARGE": 0.066,
        "HIT": 0.033, "HURT": 0.10, "DEATH": 0.05, "SPECIAL": 0.033,
    }
    FRAME_COUNT = {"IDLE": 8, "WALK": 8, "RUN": 8}

    #: Timing serangan (progress 0..1).  Jendela ACTIVE = hitbox hidup.
    ATTACK_PHASES = (
        ("anticipation", 0.00, 0.22),   # coil: badan mundur, tombak naik
        ("windup",       0.22, 0.40),   # hold di apex, embun beku mengumpul
        ("swing",        0.40, 0.56),   # sapuan/entakan cepat (aktif)
        ("impact",       0.56, 0.64),   # bingkai benturan + recoil
        ("follow",       0.64, 0.80),   # momentum terbawa melewati target
        ("recovery",     0.80, 1.00),   # kembali ke pose siaga
    )
    #: Jendela hit aktif (inklusif) — dipakai swing hitbox & debug.
    ATTACK_ACTIVE = (0.40, 0.64)
    #: Progres saat proyektil dasar diluncurkan (varian thrust).
    ATTACK_RELEASE = 0.46

    #: Durasi skill (frame @60fps) — identik dengan AI base_boss.
    SKILL_DUR = {"q": 50, "w": 50, "e": 70, "r": 90}

    #: Sub-fase lifecycle skill: cast->charge->release->area->after.
    SKILL_PHASES = (
        ("cast",    0.00, 0.18),
        ("charge",  0.18, 0.38),
        ("release", 0.38, 0.50),
        ("area",    0.50, 0.78),
        ("after",   0.78, 1.00),
    )

    class _NyzAnimController:
        """Controller animasi stateless untuk Nyzrak.

        resolve() memetakan atribut unit -> dict pose.  Tidak ada
        mutasi boss di sini (aman untuk render ter-cache); penulisan
        atribut kerja hanya terjadi di _update_attack_anim /
        _detect_moving yang dipanggil sekali per draw jalur boss.
        """

        #: Transisi yang diizinkan (dokumentasi & debug overlay).
        TRANSITIONS = {
            "IDLE":    {"WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                        "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"},
            "WALK":    {"IDLE", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                        "HIT", "HURT", "DEATH"},
            "RUN":     {"IDLE", "WALK", "ATTACK", "SWING", "CAST", "SKILL",
                        "HIT", "HURT", "DEATH"},
            "CHARGE":  {"SKILL", "CAST", "IDLE", "HIT", "HURT", "DEATH"},
            "CAST":    {"SKILL", "IDLE", "WALK", "HIT", "HURT", "DEATH"},
            "ATTACK":  {"IDLE", "WALK", "RUN", "SWING", "HIT", "DEATH"},
            "SWING":   {"IDLE", "WALK", "RUN", "ATTACK", "HIT", "DEATH"},
            "SPECIAL": {"IDLE", "WALK", "SKILL", "HIT", "DEATH"},
            "SKILL":   {"IDLE", "WALK", "RUN", "HIT", "DEATH"},
            "HIT":     {"IDLE", "WALK", "RUN", "HURT", "DEATH"},
            "HURT":    {"IDLE", "WALK", "HIT", "DEATH"},
            "DEATH":   set(),
        }

        @classmethod
        def frame_index(cls, state, phase):
            """Index bingkai animasi looping (idle/walk/run)."""
            n = _NS_nyzrak.FRAME_COUNT.get(state, 1)
            dur = max(1e-3, _NS_nyzrak.FRAME_DUR.get(state, 0.1))
            t = (phase * 0.05) / dur          # pulse: +0.05 per 1/60 s
            return int(t * n) % n

        @classmethod
        def attack_stage(cls, ap):
            """(nama_subfase, t_lokal) dari progress serangan 0..1."""
            ap = min(1.0, max(0.0, ap))
            for name, a, b in _NS_nyzrak.ATTACK_PHASES:
                if ap < b:
                    return name, min(1.0, max(0.0, (ap - a) / max(1e-3, b - a)))
            return "recovery", 1.0

        @classmethod
        def attack_active(cls, ap):
            a0, a1 = _NS_nyzrak.ATTACK_ACTIVE
            return a0 <= ap <= a1

        @classmethod
        def skill_stage(cls, t01):
            """(nama_subfase, t_lokal) dari progress skill 0..1."""
            t01 = min(1.0, max(0.0, t01))
            for name, a, b in _NS_nyzrak.SKILL_PHASES:
                if t01 < b:
                    return name, min(1.0, max(0.0, (t01 - a) / max(1e-3, b - a)))
            return "after", 1.0

        @classmethod
        def resolve(cls, boss, moving=False, run=False):
            """Resolve pose saat ini dari atribut sim."""
            phase = float(getattr(boss, "pulse", 0.0) or 0.0)
            ap = min(1.0, max(0.0,
                       float(getattr(boss, "_nyz_attack_progress", 0.0) or 0.0)))
            attack_on = bool(getattr(boss, "_nyz_attack_active", False))
            skill = getattr(boss, "active_skill", None)
            skill_timer = int(getattr(boss, "active_skill_timer", 0) or 0)
            hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)
            alive = bool(getattr(boss, "alive", True))
            hp = float(getattr(boss, "hp", 1.0) or 0.0)

            if not alive or hp <= 0.0:
                death_t = min(1.0,
                              float(getattr(boss, "_nyz_death_age", 0)) / 60.0)
                return {"state": "DEATH", "action": "death", "phase": phase,
                        "ap": death_t, "skill": None, "skill_t01": 0.0,
                        "stage": "collapse", "death_t": death_t}
            if hurt > 0:
                return {"state": "HIT", "action": "hit", "phase": phase,
                        "ap": min(1.0, hurt / 8.0), "skill": None,
                        "skill_t01": 0.0, "stage": "flinch", "death_t": 0.0}
            if skill in ("q", "w", "e", "r"):
                dur = float(_NS_nyzrak.SKILL_DUR.get(skill, 50))
                t01 = min(1.0, max(0.0, 1.0 - skill_timer / dur))
                stage, _t = cls.skill_stage(t01)
                return {"state": "SKILL", "action": "cast_" + skill,
                        "phase": phase, "ap": t01, "skill": skill,
                        "skill_t01": t01, "stage": stage, "death_t": 0.0}
            if attack_on:
                variant = "sweep" if int(getattr(boss, "_pose_variant", 0) or 0) == 1 else "thrust"
                stage, _t = cls.attack_stage(ap)
                return {"state": "SWING" if variant == "sweep" else "ATTACK",
                        "action": "attack", "phase": phase, "ap": ap,
                        "skill": None, "skill_t01": 0.0, "stage": stage,
                        "death_t": 0.0}
            if moving and run:
                return {"state": "RUN", "action": "run", "phase": phase,
                        "ap": 0.0, "skill": None, "skill_t01": 0.0,
                        "stage": "stride", "death_t": 0.0}
            if moving:
                return {"state": "WALK", "action": "walk", "phase": phase,
                        "ap": 0.0, "skill": None, "skill_t01": 0.0,
                        "stage": "step", "death_t": 0.0}
            return {"state": "IDLE", "action": "idle", "phase": phase,
                    "ap": 0.0, "skill": None, "skill_t01": 0.0,
                    "stage": "breathe", "death_t": 0.0}

    # ===================================================================
    # MATEMATIKA EASING & GEOMETRI SERANGAN (arc, bukan teleport)
    # ===================================================================
    @staticmethod
    def _ease_out_cubic(t):
        t = min(1.0, max(0.0, t))
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_out(t):
        t = min(1.0, max(0.0, t))
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _seg_t(ap, a, b):
        """t lokal 0..1 di dalam segmen [a, b)."""
        if ap <= a:
            return 0.0
        if ap >= b:
            return 1.0
        return (ap - a) / max(1e-3, b - a)

    @staticmethod
    def _spear_pose_geom(action, ap, phase):
        """Geometri tombak (rig-local, y ke bawah) untuk pose ini.

        Return (angle_deg, reach_px, grip_dx, grip_dy).
        angle 0 = lurus ke depan; negatif = terangkat ke atas.
        """
        NS = _NS_nyzrak
        base_ang, base_reach = -62.0, 22.0
        grip_x, grip_y = 7.0, -22.0

        if action == "attack":
            variant = getattr(NS, "_pose_variant_now", "thrust")
            if variant == "sweep":
                # ── sapuan melee: arc lewat atas lalu menghunjam ──
                if ap < 0.22:            # anticipation
                    t = NS._ease_out_cubic(ap / 0.22)
                    ang = -20.0 - 95.0 * t
                    reach = base_reach + 2.0 * t
                    grip_x = 7.0 - 3.0 * t
                elif ap < 0.40:          # windup: apex + tremor es
                    ang = -115.0 + math.sin(phase * 26.0) * 2.5
                    reach = 24.0
                    grip_x = 4.0
                elif ap < 0.56:          # swing: sapuan cepat (AKTIF)
                    t = NS._ease_out_cubic((ap - 0.40) / 0.16)
                    ang = -115.0 + 155.0 * t
                    reach = 24.0 + 6.0 * t
                    grip_x = 4.0 + 5.0 * t
                elif ap < 0.64:          # impact: recoil
                    t = (ap - 0.56) / 0.08
                    ang = 40.0 - 7.0 * t
                    reach = 30.0 - 1.0 * t
                    grip_x = 9.0
                elif ap < 0.80:          # follow: momentum terbawa
                    t = NS._ease_in_out((ap - 0.64) / 0.16)
                    ang = 33.0 + 10.0 * t
                    reach = 29.0 - 2.0 * t
                    grip_x = 9.0 - 2.0 * t
                else:                    # recovery
                    t = NS._ease_in_out((ap - 0.80) / 0.20)
                    ang = 43.0 + (base_ang - 43.0) * t
                    reach = 27.0 + (base_reach - 27.0) * t
                    grip_x = 7.0
                return ang, reach, grip_x, grip_y
            # ── thrust ranged: tarik -> entak -> tahan -> kembali ──
            if ap < 0.22:
                t = NS._ease_out_cubic(ap / 0.22)
                ang = -62.0 - 28.0 * t
                reach = 22.0 - 6.0 * t
                grip_x = 7.0 - 4.0 * t
            elif ap < 0.40:
                ang = -90.0 + 4.0 * math.sin(phase * 22.0)
                reach = 16.0
                grip_x = 3.0
            elif ap < 0.56:
                t = NS._ease_out_cubic((ap - 0.40) / 0.16)
                ang = -90.0 + 86.0 * t
                reach = 16.0 + 16.0 * t
                grip_x = 3.0 + 7.0 * t
            elif ap < 0.64:
                t = (ap - 0.56) / 0.08
                ang = -4.0 - 3.0 * t
                reach = 32.0 - 1.5 * t
                grip_x = 10.0 - t
            elif ap < 0.80:
                t = (ap - 0.64) / 0.16
                ang = -7.0 - 2.0 * t
                reach = 30.5 - 2.5 * t
                grip_x = 9.0 - t
            else:
                t = NS._ease_in_out((ap - 0.80) / 0.20)
                ang = -9.0 + (base_ang + 9.0) * t
                reach = 28.0 + (base_reach - 28.0) * t
                grip_x = 8.0 - t
            return ang, reach, grip_x, grip_y

        if action == "cast_q":         # Arctic Burn: bidik + recoil
            if ap < 0.38:
                k = NS._ease_out_cubic(ap / 0.38)
                ang = -62.0 + 54.0 * k
                reach = 22.0 + 9.0 * k
                grip_x = 7.0 + 2.0 * k
            else:
                rec = math.sin(min(1.0, (ap - 0.38) / 0.2) * math.pi) * 6.0
                ang = -8.0 + rec * 0.4
                reach = 31.0 - rec * 0.3
                grip_x = 9.0
            return ang, reach, grip_x, grip_y
        if action == "cast_w":         # Splinter Blast: kibasan keluar
            if ap < 0.35:
                t = NS._ease_out_cubic(ap / 0.35)
                ang = -62.0 - 58.0 * t
                reach = 22.0 - 5.0 * t
                grip_x = 7.0 - 4.0 * t
            else:
                t = NS._ease_out_cubic((ap - 0.35) / 0.15)
                ang = -120.0 + 112.0 * t
                reach = 17.0 + 13.0 * t
                grip_x = 3.0 + 6.0 * t
            return ang, reach, grip_x, grip_y
        if action == "cast_e":         # Winter's Curse: angkat tinggi
            if ap < 0.3:
                t = NS._ease_out_cubic(ap / 0.3)
                ang = -62.0 - 48.0 * t
                reach = 22.0 + 3.0 * t
                grip_x = 7.0 + t
            elif ap < 0.5:
                ang = -110.0 + 3.0 * math.sin(phase * 18.0)
                reach = 25.0
                grip_x = 8.0
            else:
                t = NS._ease_in_out((ap - 0.5) / 0.5)
                ang = -110.0 + 48.0 * t
                reach = 25.0 - 3.0 * t
                grip_x = 8.0 - t
            return ang, reach, grip_x, grip_y
        if action == "cast_r":         # Cold Embrace: angkat -> tebar
            if ap < 0.25:
                t = NS._ease_out_cubic(ap / 0.25)
                ang = -62.0 - 38.0 * t
                reach = 22.0 + 2.0 * t
                grip_x = 7.0 + t
            elif ap < 0.42:
                ang = -100.0 - 4.0 * math.sin(phase * 14.0)
                reach = 24.0
                grip_x = 8.0
            elif ap < 0.55:
                t = NS._ease_out_cubic((ap - 0.42) / 0.13)
                ang = -100.0 + 82.0 * t
                reach = 24.0 + 6.0 * t
                grip_x = 8.0 + 2.0 * t
            else:
                t = NS._ease_in_out((ap - 0.55) / 0.45)
                ang = -18.0 + (base_ang + 18.0) * t
                reach = 30.0 + (base_reach - 30.0) * t
                grip_x = 10.0 - 3.0 * t
            return ang, reach, grip_x, grip_y
        if action == "hit":
            flinch = math.sin(min(1.0, ap) * math.pi)
            return (base_ang - 14.0 * flinch,
                    base_reach - 3.0 * flinch,
                    7.0 - 2.0 * flinch, grip_y)
        if action == "death":
            return base_ang + 55.0, base_reach - 6.0, 5.0, -18.0
        if action == "run":
            return (base_ang + 12.0 + math.sin(phase * 2.4) * 7.0,
                    base_reach + 1.0, 8.0, -21.0)
        if action == "walk":
            return (base_ang + math.sin(phase * 1.6) * 2.0,
                    base_reach, 7.0, -22.0)
        # idle: napas + ayunan senjata halus
        return base_ang + math.sin(phase * 0.9) * 3.0, base_reach, 7.0, -22.0

    # ===================================================================
    # RIG POSE — seluruh parameter gerak satu bingkai rig
    # ===================================================================
    @staticmethod
    def _rig_pose(action, phase, ap):
        """Hitung pose rig (unit rig low-res, y ke bawah)."""
        NS = _NS_nyzrak
        pose = {
            "bob": 0, "lean": 0, "pitch": 0, "rear": 0.0,
            "flap": math.sin(phase * 1.3), "flap_amp": 0.42,
            "tail": phase * 0.8, "legs": phase * 2.2, "charge": 0.0,
            "variant": "thrust", "death_t": 0.0,
        }
        if action == "idle":
            pose["bob"] = math.sin(phase * 0.8) * 1.2      # breathing
            pose["tail"] = phase * 0.6
        elif action == "walk":
            pose["bob"] = math.sin(phase * 1.2) * 1.6
            pose["flap"] = math.sin(phase * 2.1)
            pose["flap_amp"] = 0.5
            pose["tail"] = phase * 1.1
            pose["legs"] = phase * 3.0
        elif action == "run":
            pose["bob"] = math.sin(phase * 2.2) * 2.0
            pose["lean"] = 2
            pose["flap"] = math.sin(phase * 3.4)
            pose["flap_amp"] = 0.62
            pose["tail"] = phase * 1.8
            pose["legs"] = phase * 4.4
        elif action == "attack":
            pose["variant"] = getattr(NS, "_pose_variant_now", "thrust")
            if pose["variant"] == "sweep":
                if ap < 0.22:
                    t = ap / 0.22
                    pose["rear"] = -0.35 * t
                    pose["flap"] = 0.5 + 0.5 * t
                    pose["flap_amp"] = 0.36
                elif ap < 0.40:
                    pose["rear"] = -0.35
                    pose["flap"] = 1.0
                    pose["flap_amp"] = 0.3
                elif ap < 0.64:
                    t = NS._ease_out_cubic((ap - 0.40) / 0.24)
                    pose["rear"] = -0.35 + 0.75 * t
                    pose["lean"] = int(3 * t)
                    pose["flap"] = 1.0 - 1.6 * t
                    pose["flap_amp"] = 0.55
                else:
                    t = NS._ease_in_out((ap - 0.64) / 0.36)
                    pose["rear"] = 0.4 - 0.4 * t
                    pose["lean"] = int(3 * (1 - t))
                    pose["flap"] = -0.6 + 0.6 * t
                    pose["flap_amp"] = 0.5
            else:
                if ap < 0.22:
                    t = ap / 0.22
                    pose["rear"] = -0.3 * t
                    pose["flap"] = 0.4 + 0.6 * t
                elif ap < 0.40:
                    pose["rear"] = -0.3
                    pose["flap"] = 1.0
                    pose["flap_amp"] = 0.32
                    pose["charge"] = (ap - 0.22) / 0.18
                elif ap < 0.64:
                    t = NS._ease_out_cubic((ap - 0.40) / 0.24)
                    pose["rear"] = -0.3 + 0.6 * t
                    pose["lean"] = int(4 * t)
                    pose["flap"] = 1.0 - 1.4 * t
                    pose["flap_amp"] = 0.5
                    pose["charge"] = max(0.0, 1.0 - (ap - 0.40) / 0.08)
                else:
                    t = NS._ease_in_out((ap - 0.64) / 0.36)
                    pose["rear"] = 0.3 - 0.3 * t
                    pose["lean"] = int(4 * (1 - t))
                    pose["flap"] = -0.4 + 0.4 * t
        elif action.startswith("cast"):
            pose["flap"] = math.sin(phase * 1.7)
            pose["flap_amp"] = 0.55
            pose["bob"] = math.sin(phase * 1.0) * 1.4
            if action in ("cast_q", "cast_w"):
                if ap < 0.38:
                    pose["charge"] = ap / 0.38
                    pose["rear"] = -0.2 * pose["charge"]
                else:
                    pose["rear"] = -0.2 + 0.35 * NS._ease_out_cubic(
                        (ap - 0.38) / 0.2)
                    pose["lean"] = 2
            elif action == "cast_e":
                pose["charge"] = min(1.0, ap / 0.3)
            else:  # cast_r
                if ap < 0.42:
                    pose["charge"] = ap / 0.42
                    pose["rear"] = -0.25 * pose["charge"]
                elif ap < 0.55:
                    pose["rear"] = 0.5
                    pose["flap"] = 1.2
                    pose["flap_amp"] = 0.7
                else:
                    t = NS._ease_in_out((ap - 0.55) / 0.45)
                    pose["rear"] = 0.5 - 0.5 * t
        elif action == "hit":
            flinch = math.sin(min(1.0, ap) * math.pi)
            pose["rear"] = -0.3 * flinch
            pose["flap"] = -0.9 * flinch
            pose["flap_amp"] = 0.6
        elif action == "death":
            pose["death_t"] = min(1.0, ap)
            pose["flap"] = -0.4
            pose["flap_amp"] = 0.2
            pose["rear"] = -0.5 + 0.2 * pose["death_t"]
            pose["bob"] = 6.0 * pose["death_t"]
        return pose

    # ===================================================================
    # HELPERS GAMBAR RIG (low-res, koordinat int, tepi keras)
    # ===================================================================
    @staticmethod
    def _rp(surface, color, points):
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)

    @staticmethod
    def _rc(surface, color, c, r):
        if r >= 1:
            pygame.draw.circle(surface, color, (int(c[0]), int(c[1])), int(r))

    @staticmethod
    def _rl(surface, color, rect):
        x, y, w, h = rect
        w = max(1, int(w))
        h = max(1, int(h))
        if w > 0 and h > 0:
            pygame.draw.rect(surface, color, (int(x), int(y), w, h))

    @staticmethod
    def _rline(surface, color, a, b, w=1):
        pygame.draw.line(surface, color, (int(a[0]), int(a[1])),
                         (int(b[0]), int(b[1])), max(1, int(w)))

    # ---------------------------------------------------------------------------
    # DRAW PRIMITIVES (layar, alpha-safe) — FX canvas fallback
    # ---------------------------------------------------------------------------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyzrak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_nyzrak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyzrak._clamp(color)
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
        color = _NS_nyzrak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = int(max(xs) - min_x + 4)
            h = int(max(ys) - min_y + 4)
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_nyzrak._clamp(color)
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
        color = _NS_nyzrak._clamp(color)
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
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                   * getattr(boss, "direction", 1)), int(y)


    @staticmethod
    def _melee_variant(boss):
        """True kalau target cukup dekat untuk sapuan melee."""
        tgt = getattr(boss, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            return False
        try:
            d = math.hypot(tgt.x - getattr(boss, "x", 0),
                           tgt.y - getattr(boss, "y", 0))
        except Exception:
            return False
        return d <= 115.0

    # ===================================================================
    # RIG PIXEL-ART — komposit wyvern + rider per layer
    # ===================================================================
    @staticmethod
    def _draw_rig(surface, cx, cy, facing, pose, action, phase, ap):
        """Gambar seluruh rig ke canvas low-res.

        Urutan layer (siluet kuat, band cel 3 nada):
            back wing -> tail -> hind legs -> body -> belly plates ->
            neck/head -> rider body -> rider armor -> rider head ->
            weapon (tombak) -> front wing -> highlights
        """
        NS = _NS_nyzrak
        F = 1 if facing >= 0 else -1

        def mx(dx):
            return cx + int(dx) * F

        bob = int(pose.get("bob", 0))
        lean = int(pose.get("lean", 0)) * F
        rear = float(pose.get("rear", 0.0))
        pitch = float(pose.get("pitch", 0.0)) + rear * 6.0
        by = cy + bob + int(-rear * 3)

        # geometri tombak dihitung SEKALI — rider & spear pakai sama
        ang_deg, reach, gx, gy = NS._spear_pose_geom(action, ap, phase)
        grip_ax = mx(gx) + lean
        grip_ay = cy + gy + bob

        # 1. sayap belakang (jauh, paling gelap)
        NS._draw_wing(surface, mx(-4) + lean, by - 8, F,
                      pose["flap"], pose["flap_amp"], back=True, spread=0.92)

        # 2. ekor bersegmen + spatade es
        NS._draw_tail(surface, mx(-16) + lean, by + 2, F,
                      pose["tail"], pose.get("death_t", 0.0))

        # 3. kaki belakang gantung
        NS._draw_legs(surface, mx(-6) + lean, by + 12, F, pose["legs"])

        # 4. badan wyvern (band pixel-art)
        NS._draw_wy_body(surface, mx(0) + lean, by, F, pitch)

        # 5. leher + kepala (maju saat lunge)
        head_lunge = 0.0
        if action == "attack":
            head_lunge = NS._ease_out_cubic(NS._seg_t(ap, 0.40, 0.64)) \
                - NS._seg_t(ap, 0.80, 1.0) * 0.8
        elif action.startswith("cast"):
            head_lunge = 0.3 * NS._seg_t(ap, 0.38, 0.55)
        NS._draw_wy_head(surface, mx(16) + lean + int(head_lunge * 5) * F,
                         by - 6 + int(-rear * 4), F, phase, action)

        # 6-8. rider: jubah -> torso+armor -> kepala (lengan ke grip)
        NS._draw_rider(surface, mx(-3) + lean, by - 16, F, phase, action,
                       (grip_ax, grip_ay))

        # 9. SENJATA: tombak es (rotasi penuh dari kurva arc)
        NS._draw_spear(surface, grip_ax, grip_ay, F,
                       math.radians(ang_deg), reach,
                       pose.get("charge", 0.0))

        # 10. sayap depan (dekat, lebih terang)
        NS._draw_wing(surface, mx(2) + lean, by - 6, F,
                      pose["flap"], pose["flap_amp"], back=False, spread=1.0)

        # 11. highlights: rim punggung + kilang es
        NS._draw_rim_highlights(surface, mx(0) + lean, by, F, phase)

    @staticmethod
    def _draw_wing(surface, sx, sy, facing, flap, amp, back=False,
                   spread=1.0):
        """Satu sayap kelelawar: membrane 3 nada + jari-jari tulang."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        rot = flap * amp
        c, s = math.cos(rot), math.sin(rot)

        def pt(dx, dy):
            dx *= spread
            rx = dx * c - dy * s
            ry = dx * s + dy * c
            return (int(sx + rx * facing), int(sy + ry))

        t1 = pt(26, -22)      # jari atas
        t2 = pt(34, -2)       # jari tengah
        t3 = pt(27, 13)       # jari bawah
        root = (int(sx), int(sy))
        root_low = (int(sx + 2 * facing), int(sy + 7))

        if back:
            mem_d, mem_m, mem_l = ("wing_darkest", "wing_darkest", "wing_dark")
            bone, bone_hi = "wy_darkest", "wy_dark"
        else:
            mem_d, mem_m, mem_l = ("wing_darkest", "wing_dark", "wing_mid")
            bone, bone_hi = "wy_darkest", "wy_mid"
        # membrane dasar (scallop trailing edge)
        NS._rp(surface, P[mem_d], [
            root, t1,
            (t1[0] - 3 * facing, t1[1] + 5), (t2[0], t2[1] + 4),
            (t3[0] - 2 * facing, t3[1] + 4), root_low,
        ])
        # band tengah
        NS._rp(surface, P[mem_m], [
            (root[0] + 2 * facing, root[1] + 1), t1,
            (t2[0] - 2 * facing, t2[1] + 2),
            (t3[0] - 4 * facing, t3[1] + 2), root_low,
        ])
        # band terang dekat bahu
        k = pt(15, -8)
        NS._rp(surface, P[mem_l], [
            (root[0] + 2 * facing, root[1] + 1), k,
            (k[0] - 2 * facing, k[1] + 6), root_low,
        ])
        # tulang jari
        for tip in (t1, t2, t3):
            NS._rline(surface, P[bone], root, tip, 2)
        NS._rline(surface, P[bone_hi], root, t1, 1)
        # cakar ujung jari atas
        NS._rp(surface, P["bone_dark"], [
            (t1[0], t1[1]), (t1[0] + 2 * facing, t1[1] - 2),
            (t1[0] + facing, t1[1] + 1),
        ])
        NS._rl(surface, P["bone_light"],
               (t1[0] + facing, t1[1] - 2, 1, 1))

    @staticmethod
    def _draw_tail(surface, x, y, facing, wave, death_t):
        """Ekor bersegmen (rect mengecil) + spatade es."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        px, py = float(x), float(y)
        for i in range(6):
            t = i / 5.0
            curve = math.sin(t * 2.2 + wave * 0.5)
            step = 5.5 - t * 2.0
            # dominan ke belakang + lengkung sinus + droop saat mati
            px += -facing * step * (0.85 + 0.3 * curve)
            py += step * 0.35 * curve + (step * 0.3 if death_t > 0 else 0.0)
            w = max(2, 6 - i)
            NS._rl(surface, P["wy_dark" if i % 2 else "wy_darkest"],
                   (int(px - w // 2), int(py - w // 2), w, w))
            if i == 2:
                NS._rl(surface, P["wy_mid"],
                       (int(px - w // 2), int(py - w // 2) - 1, w - 1, 1))
        tx, ty = int(px), int(py)
        NS._rp(surface, P["ice_darkest"], [
            (tx - 3, ty - 1), (tx + 3, ty - 1),
            (tx + 2 * facing, ty - 7), (tx - 2 * facing, ty - 7),
        ])
        NS._rp(surface, P["ice_dark"], [
            (tx - 2, ty - 1), (tx + 2, ty - 1),
            (tx + facing, ty - 6), (tx - facing, ty - 6),
        ])
        NS._rl(surface, P["ice_light"], (tx - 1, ty - 6, 1, 3))

    @staticmethod
    def _draw_legs(surface, x, y, facing, cycle):
        """Dua kaki belakang gantung; alternating saat bergerak."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        for side, ph in ((-1, 0.0), (1, math.pi)):
            swing = math.sin(cycle + ph)
            lx = x + side * 5 * facing
            ly = y + int(swing * 2)
            NS._rl(surface, P["wy_darkest"], (lx - 2, ly, 4, 6))
            NS._rl(surface, P["wy_dark"], (lx - 1, ly, 2, 5))
            NS._rl(surface, P["wy_mid"], (lx - 1, ly, 1, 4))
            for c in (-2, 0, 2):
                NS._rp(surface, P["bone_dark"], [
                    (lx + c, ly + 6), (lx + c + 2, ly + 6),
                    (lx + c + 1, ly + 8),
                ])
            NS._rl(surface, P["bone_light"], (lx, ly + 6, 1, 1))

    @staticmethod
    def _draw_wy_body(surface, x, y, facing, pitch):
        """Badan wyvern: band horizontal pixel-art + punggung berduri."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        rows = [
            (-8, 26, "wy_darkest"), (-6, 36, "wy_dark"),
            (-4, 42, "wy_mid"), (-1, 44, "wy_mid"),
            (2, 43, "belly_dark"), (5, 40, "belly_mid"),
            (8, 32, "belly_mid"), (11, 22, "belly_light"),
            (13, 12, "belly_light"),
        ]
        for dy, w, key in rows:
            wy = y + dy + int(pitch * (1.0 if dy < 0 else 0.4))
            NS._rl(surface, P[key],
                   (x - w // 2 + 2 * facing, wy, w, 3))
        # leher: dua segmen naik ke depan
        NS._rl(surface, P["wy_darkest"], (x + 12 * facing, y - 10, 6, 6))
        NS._rl(surface, P["wy_dark"], (x + 13 * facing, y - 10, 4, 5))
        NS._rl(surface, P["wy_dark"], (x + 15 * facing, y - 14, 6, 6))
        NS._rl(surface, P["wy_mid"], (x + 16 * facing, y - 14, 3, 5))
        # duri punggung
        for i, dx in enumerate((-16, -10, -4, 2, 8)):
            sxp = x + dx * facing
            syp = y - 9 - int(pitch * 1.2)
            h = 3 - (i % 2)
            NS._rp(surface, P["wy_darkest"], [
                (sxp - 2, syp + 1), (sxp + 2, syp + 1), (sxp, syp - h),
            ])
            NS._rl(surface, P["wy_light"], (sxp, syp - h, 1, 1))
        # pelat perut
        for i in range(3):
            gy = y + 3 + i * 3
            NS._rl(surface, P["belly_dark"], (x - 12 + 2 * facing, gy, 26, 1))
        # bahu armor es
        NS._rl(surface, P["ice_darkest"], (x - 6 * facing, y - 8, 12, 3))
        NS._rl(surface, P["ice_dark"], (x - 5 * facing, y - 8, 10, 1))
        NS._rl(surface, P["ice_light"], (x - 4 * facing, y - 8, 3, 1))

    @staticmethod
    def _draw_wy_head(surface, x, y, facing, phase, action):
        """Kepala wyvern chunky: tengkorak blok + rahang + tanduk."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        F = facing
        NS._rl(surface, P["wy_darkest"], (x - 4 * F, y - 6, 10, 9))
        NS._rl(surface, P["wy_dark"], (x - 3 * F, y - 5, 8, 7))
        NS._rl(surface, P["wy_mid"], (x - 3 * F, y - 5, 4, 3))
        # moncong
        NS._rl(surface, P["wy_darkest"], (x + 5 * F, y - 3, 8, 5))
        NS._rl(surface, P["wy_dark"], (x + 5 * F, y - 3, 6, 3))
        NS._rl(surface, P["wy_mid"], (x + 6 * F, y - 3, 3, 2))
        # rahang terbuka + taring
        open_j = 3 if (action == "attack" or action.startswith("cast")) else 2
        NS._rp(surface, P["shadow_deep"], [
            (x + 5 * F, y + 2), (x + 12 * F, y + 2),
            (x + 11 * F, y + 2 + open_j), (x + 5 * F, y + 3),
        ])
        NS._rp(surface, P["wy_darkest"], [
            (x + 5 * F, y + 2 + open_j), (x + 12 * F, y + 2 + open_j),
            (x + 12 * F, y + 4 + open_j), (x + 6 * F, y + 4 + open_j),
        ])
        for tx in (7, 10):
            NS._rp(surface, P["bone_light"], [
                (x + tx * F, y + 2), (x + (tx + 1) * F, y + 2),
                (x + (tx + 1) * F, y + 4),
            ])
        # napas dingin
        bp = int(math.sin(phase * 3.0) * 1.2)
        NS._rl(surface, P["ice_light"], (x + 13 * F, y + bp, 2, 2))
        NS._rl(surface, P["ice_hot"], (x + 15 * F, y + bp + 1, 1, 1))
        # mata oranye garang
        NS._rl(surface, P["wy_eye_dark"], (x + F, y - 4, 3, 3))
        glow = 0.6 + 0.4 * math.sin(phase * 2.2)
        NS._rl(surface,
               P["wy_eye_bright"] if glow > 0.6 else P["wy_eye_dark"],
               (x + 2 * F, y - 3, 2, 1))
        NS._rl(surface, P["wy_eye_hot"], (x + 2 * F, y - 3, 1, 1))
        NS._rl(surface, P["wy_darkest"], (x + F, y - 6, 6, 1))
        # tanduk kembar
        for side in (0, 2):
            hx = x + (side - 1) * F
            NS._rline(surface, P["bone_dark"],
                      (hx, y - 6), (hx - 3 * F, y - 14), 2)
            NS._rline(surface, P["bone_light"],
                      (hx, y - 6), (hx - 2 * F, y - 12), 1)
            NS._rl(surface, P["ice_hot"], (hx - 3 * F, y - 15, 1, 1))
        # sirip tengkorak belakang
        NS._rp(surface, P["wing_dark"], [
            (x - 4 * F, y - 5), (x - 9 * F, y - 9), (x - 8 * F, y - 3),
        ])
        NS._rp(surface, P["wing_mid"], [
            (x - 4 * F, y - 5), (x - 8 * F, y - 8), (x - 7 * F, y - 4),
        ])

    @staticmethod
    def _draw_rider(surface, cx, cy, facing, phase, action, grip):
        """Rider berjubah: jubah, torso armor, kepala berhood, lengan."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        F = facing
        rx, ry = cx, cy + int(math.sin(phase * 0.8))     # breathing

        # jubah bawah
        NS._rp(surface, P["robe_darkest"], [
            (rx - 7 * F, ry - 4), (rx + 7 * F, ry - 4),
            (rx + 10 * F, ry + 8), (rx + 3 * F, ry + 11),
            (rx - 3 * F, ry + 11), (rx - 10 * F, ry + 8),
        ])
        NS._rp(surface, P["robe_dark"], [
            (rx - 6 * F, ry - 3), (rx + 6 * F, ry - 3),
            (rx + 8 * F, ry + 7), (rx - 8 * F, ry + 7),
        ])
        NS._rp(surface, P["robe_mid"], [
            (rx - 4 * F, ry - 2), (rx + 4 * F, ry - 2),
            (rx + 5 * F, ry + 5), (rx - 5 * F, ry + 5),
        ])
        # bulu tepi jubah (piksel chunky)
        for i in range(-3, 4):
            NS._rl(surface, P["fur_dark"], (rx + i * 3 * F - 1, ry + 10, 2, 2))
            NS._rl(surface, P["fur_mid"], (rx + i * 3 * F - 1, ry + 9, 2, 1))

        # torso + armor dada
        NS._rl(surface, P["robe_darkest"], (rx - 5 * F, ry - 12, 10, 9))
        NS._rl(surface, P["robe_dark"], (rx - 4 * F, ry - 11, 8, 7))
        NS._rl(surface, P["robe_mid"], (rx - 3 * F, ry - 11, 5, 4))
        # armor bahu es
        NS._rl(surface, P["ice_darkest"], (rx - 6 * F, ry - 13, 5, 3))
        NS._rl(surface, P["ice_dark"], (rx - 5 * F, ry - 13, 3, 2))
        NS._rl(surface, P["ice_mid"], (rx - 5 * F, ry - 13, 2, 1))
        NS._rl(surface, P["ice_darkest"], (rx + 2 * F, ry - 13, 4, 3))
        NS._rl(surface, P["ice_dark"], (rx + 2 * F, ry - 13, 2, 2))
        # kerah bulu
        NS._rl(surface, P["fur_dark"], (rx - 5 * F, ry - 14, 10, 3))
        NS._rl(surface, P["fur_mid"], (rx - 4 * F, ry - 14, 8, 1))
        NS._rl(surface, P["fur_light"], (rx - 3 * F, ry - 15, 4, 1))
        # ikang pinggang + permata es
        NS._rl(surface, P["metal_darkest"], (rx - 5 * F, ry - 4, 10, 2))
        NS._rl(surface, P["metal_dark"], (rx - 4 * F, ry - 4, 8, 1))
        NS._rl(surface, P["ice_dark"], (rx - F, ry - 5, 3, 3))
        NS._rl(surface, P["ice_bright"], (rx - F, ry - 5, 1, 1))

        # lengan tombak: bahu -> siku -> grip tombak (2 segmen)
        shx, shy = rx + 4 * F, ry - 10
        hx, hy = grip
        ex = shx + (hx - shx) * 0.45
        ey = shy + (hy - shy) * 0.45 - 2
        NS._rline(surface, P["robe_darkest"], (shx, shy), (ex, ey), 3)
        NS._rline(surface, P["robe_dark"], (shx, shy), (ex, ey), 2)
        NS._rline(surface, P["robe_darkest"], (ex, ey), (hx, hy), 3)
        NS._rline(surface, P["robe_dark"], (ex, ey), (hx, hy), 2)
        NS._rc(surface, P["robe_darkest"], (hx + 1, hy + 1), 2)
        NS._rc(surface, P["skin_dark"], (hx, hy), 2)
        NS._rl(surface, P["skin_mid"], (hx - 1, hy - 1, 1, 1))

        # lengan depan: merentang saat cast, santai saat lain
        if action.startswith("cast"):
            fx2, fy2 = rx + 5 * F, ry - 8
        else:
            fx2 = rx - 5 * F
            fy2 = ry - 2 + int(math.sin(phase * 1.1))
        NS._rline(surface, P["robe_dark"], (rx - 3 * F, ry - 9), (fx2, fy2), 2)
        NS._rline(surface, P["robe_mid"], (rx - 3 * F, ry - 9), (fx2, fy2), 1)
        NS._rc(surface, P["skin_dark"], (fx2, fy2), 2)
        NS._rl(surface, P["skin_mid"], (fx2 - 1, fy2 - 1, 1, 1))
        # bola mantra di tangan depan saat cast
        if action.startswith("cast"):
            pk = 0.6 + 0.4 * math.sin(phase * 5)
            r = max(1, int(2 * pk))
            col = P["frost_bright"] if action == "cast_q" else P["ice_bright"]
            NS._rc(surface, P["frost_dark"] if action == "cast_q"
                   else P["ice_dark"], (fx2 + F, fy2 - 1), r + 1)
            NS._rc(surface, col, (fx2 + F, fy2 - 1), r)

        # kepala berhood + wajah berbayang + mata menyala
        hyy = ry - 20
        NS._rp(surface, P["robe_darkest"], [
            (rx - 4 * F, hyy + 4), (rx + 4 * F, hyy + 4),
            (rx + 4 * F, hyy - 3), (rx + 2 * F, hyy - 6),
            (rx - 2 * F, hyy - 6), (rx - 4 * F, hyy - 3),
        ])
        NS._rp(surface, P["robe_dark"], [
            (rx - 3 * F, hyy + 4), (rx + 3 * F, hyy + 4),
            (rx + 3 * F, hyy - 2), (rx + F, hyy - 5),
            (rx - F, hyy - 5), (rx - 3 * F, hyy - 2),
        ])
        NS._rl(surface, P["shadow_deep"], (rx + F, hyy - 2, 2, 4))
        if (int(phase * 2.0) % 7) != 0:      # kedip
            NS._rl(surface, P["eye_bright"], (rx + F, hyy - 1, 2, 1))
        NS._rl(surface, P["eye_hot"], (rx + 2 * F, hyy - 1, 1, 1))
        # rambut pirang keluar dari hood
        NS._rl(surface, P["hair_dark"], (rx - 2 * F, hyy + 3, 2, 3))
        NS._rl(surface, P["hair_mid"], (rx - 2 * F, hyy + 3, 1, 2))
        NS._rl(surface, P["ice_mid"], (rx - F, hyy - 5, 1, 1))

    @staticmethod
    def _draw_spear(surface, gx, gy, facing, angle, reach, charge):
        """Tombak es: poros, cincin emas, mata kristal 4 faset."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        F = facing
        dx, dy = math.cos(angle) * F, math.sin(angle)
        tipx, tipy = gx + dx * reach, gy + dy * reach
        nx, ny = -dy, dx
        # poros (quad 2px)
        NS._rp(surface, P["metal_darkest"], [
            (int(gx - nx), int(gy - ny)), (int(tipx - nx), int(tipy - ny)),
            (int(tipx + nx), int(tipy + ny)), (int(gx + nx), int(gy + ny)),
        ])
        NS._rline(surface, P["metal_dark"], (gx, gy), (tipx, tipy), 1)
        NS._rline(surface, P["metal_light"],
                  (gx - nx, gy - ny), (tipx - nx, tipy - ny), 1)
        # cincin emas
        for t in (0.3, 0.68):
            rxp, ryp = gx + dx * reach * t, gy + dy * reach * t
            NS._rline(surface, P["gold_mid"],
                      (rxp - nx * 2, ryp - ny * 2),
                      (rxp + nx * 2, ryp + ny * 2), 2)
            NS._rl(surface, P["gold_light"], (int(rxp) - 1, int(ryp) - 1, 1, 1))
        # mata kristal es
        bx, by = tipx, tipy
        p_tip = (int(bx + dx * 9), int(by + dy * 9))
        p_up = (int(bx - nx * 4 + dx * 2), int(by - ny * 4 + dy * 2))
        p_dn = (int(bx + nx * 4 + dx * 2), int(by + ny * 4 + dy * 2))
        p_base = (int(bx - dx * 2), int(by - dy * 2))
        NS._rp(surface, P["ice_darkest"], [p_base, p_up, p_tip, p_dn])
        NS._rp(surface, P["ice_dark"], [
            p_base,
            (p_up[0] - (p_up[0] - p_tip[0]) // 3,
             p_up[1] - (p_up[1] - p_tip[1]) // 3),
            (int(p_tip[0] - dx), int(p_tip[1] - dy)),
            (p_dn[0] - (p_dn[0] - p_tip[0]) // 3,
             p_dn[1] - (p_dn[1] - p_tip[1]) // 3),
        ])
        NS._rp(surface, P["ice_mid"], [
            p_base, ((p_up[0] + p_tip[0]) // 2, (p_up[1] + p_tip[1]) // 2),
            p_tip,
        ])
        NS._rl(surface, P["ice_bright"],
               (int(bx + dx * 2), int(by + dy * 2), 1, 1))
        NS._rl(surface, P["ice_pure"], (p_tip[0], p_tip[1], 1, 1))
        # nyala windup
        if charge > 0.05:
            r = 2 + int(charge * 3)
            NS._rc(surface, P["ice_bright"], (int(tipx), int(tipy)), r)
            NS._rc(surface, P["ice_hot"], (int(tipx), int(tipy)),
                   max(1, r - 2))

    @staticmethod
    def _draw_rim_highlights(surface, x, y, facing, phase):
        """Pass akhir: rim cahaya dingin di punggung + kilang baju."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        F = facing
        tw = 0.6 + 0.4 * math.sin(phase * 1.7)
        for i, (dx, dy) in enumerate(((-18, -8), (-12, -10), (-6, -11),
                                      (0, -11), (6, -10))):
            if (i % 2) == 0 or tw > 0.75:
                NS._rl(surface, P["wy_high"] if tw > 0.75 else P["wy_light"],
                       (x + dx * F, y + dy, 2, 1))
        NS._rl(surface, P["ice_light"], (x - 4 * F, y - 8, 2, 1))

    # ===================================================================
    # STATE MANAGEMENT (sekali per draw jalur boss)
    # ===================================================================
    def _detect_moving(boss):
        if not hasattr(boss, "_nyz_last_x"):
            boss._nyz_last_x = boss.x
            boss._nyz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nyz_last_x)
        dy = abs(boss.y - boss._nyz_last_y)
        mag = dx + dy
        boss._nyz_last_x = boss.x
        boss._nyz_last_y = boss.y
        boss._nyz_move_mag = mag
        return mag > 0.3

    def _update_attack_anim(boss):
        """Kemajuan serangan dari timer simulasi (frame @60fps)."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyz_prev_timer", 0))
        active = bool(getattr(boss, "_nyz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nyz_attack_active = True
            boss._nyz_attack_frame = 0
            boss._pose_variant = 1 if _NS_nyzrak._melee_variant(boss) else 0
            active = True
        elif active:
            boss._nyz_attack_frame = int(getattr(boss, "_nyz_attack_frame", 0)) + 1
            if boss._nyz_attack_frame > cooldown:
                boss._nyz_attack_active = False
                boss._nyz_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._nyz_attack_active = False
            boss._nyz_attack_frame = 0
            active = False

        boss._nyz_prev_timer = timer
        boss._nyz_attack_progress = (
            min(1.0, getattr(boss, "_nyz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
        boss._pose_variant_now = \
            "sweep" if int(getattr(boss, "_pose_variant", 0) or 0) == 1 else "thrust"
        if not getattr(boss, "alive", True) or getattr(boss, "hp", 1) <= 0:
            boss._nyz_death_age = int(getattr(boss, "_nyz_death_age", 0)) + 1
        else:
            boss._nyz_death_age = 0

    @staticmethod
    def _resolve_pose(boss):
        """(action, phase, ap) pose SAAT INI — dipakai fx layer & debug."""
        moving = bool(getattr(boss, "_nyz_move_mag", 0) > 0.3)
        run = float(getattr(boss, "_nyz_move_mag", 0)) > 2.4
        info = _NS_nyzrak._NyzAnimController.resolve(boss, moving, run)
        _NS_nyzrak._pose_variant_now = \
            "sweep" if int(getattr(boss, "_pose_variant", 0) or 0) == 1 else "thrust"
        return info["action"], info["phase"], info["ap"]

    @staticmethod
    def _spear_state(boss, x, y):
        """Geometri tombak layar-lokal untuk lapisan FX (trail/muzzle)."""
        NS = _NS_nyzrak
        action, phase, ap = NS._resolve_pose(boss)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        ang_deg, reach, gx, gy = NS._spear_pose_geom(action, ap, phase)
        ang = math.radians(ang_deg)
        scale = NS.render_scale_of(boss)
        grip = pygame.Vector2(x + gx * NS.PIXEL * facing * scale,
                              y + gy * NS.PIXEL * scale)
        d = pygame.Vector2(math.cos(ang) * facing, math.sin(ang))
        tip = grip + d * (reach * NS.PIXEL * scale)
        active = (action == "attack"
                  and NS.ATTACK_ACTIVE[0] <= ap <= NS.ATTACK_ACTIVE[1])
        return {"grip": grip, "tip": tip, "angle": ang, "action": action,
                "ap": ap, "facing": facing, "active": active}

    @staticmethod
    def render_scale_of(boss):
        """Faktor skala pipeline hero (jalur boss = 1.0)."""
        v = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return max(0.05, min(1.6, v if v > 0.02 else 1.0))

    # ===================================================================
    # PROJECTILE CANVAS FALLBACK (hidup saat modul FX tak tersedia)
    # ===================================================================
    class IceProjectile:
        """Pecahan es berputar — serangan dasar (fallback canvas)."""
        def __init__(self, sx, sy, tx, ty, speed=7.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            self.spin = 0.0
            self.angle = math.atan2(ty - sy, tx - sx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.4
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            NS = _NS_nyzrak
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 18)
                NS._aacircle(surface, (*P["ice_dark"], alpha), (tx, ty), 2)
                NS._aacircle(surface, (*P["ice_light"], alpha), (tx, ty), 1)
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            dx, dy = math.cos(self.angle), math.sin(self.angle)
            nx, ny = -dy, dx
            NS._poly(surface, P["ice_darkest"], [
                (px + int(dx * 8), py + int(dy * 8)),
                (px + int(nx * 3), py + int(ny * 3)),
                (px - int(dx * 3), py - int(dy * 3)),
                (px - int(nx * 3), py - int(ny * 3)),
            ])
            NS._poly(surface, P["ice_mid"], [
                (px + int(dx * 6), py + int(dy * 6)),
                (px + int(nx * 2), py + int(ny * 2)),
                (px - int(dx * 2), py - int(dy * 2)),
                (px - int(nx * 2), py - int(ny * 2)),
            ])
            NS._poly(surface, P["ice_bright"], [
                (px + int(dx * 5), py + int(dy * 5)),
                (px, py), (px - dx, py - dy),
            ])
            NS._draw_snowflake(surface, px, py, 4, 200, rotate=self.spin)


    class SplinterShard:
        """Splinter Blast (W) — serpihan cepat keluar (fallback canvas)."""
        def __init__(self, x, y, dir_x, dir_y, speed=6.0, life=25):
            self.x = float(x)
            self.y = float(y)
            self.dir_x = dir_x
            self.dir_y = dir_y
            self.speed = speed
            self.life = life
            self.age = 0
            self.alive = True
            self.angle = math.atan2(dir_y, dir_x)
            self.trail = []

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 5:
                self.trail.pop(0)
            self.x += self.dir_x * self.speed
            self.y += self.dir_y * self.speed

        def draw(self, surface, phase):
            NS = _NS_nyzrak
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 22)
                NS._aacircle(surface, (*P["ice_light"], alpha), (tx, ty), 1)
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            dx, dy = self.dir_x, self.dir_y
            nx, ny = -dy, dx
            NS._poly(surface, P["ice_darkest"], [
                (px + int(dx * 8), py + int(dy * 8)),
                (px + int(nx * 2), py + int(ny * 2)),
                (px - int(dx * 4), py - int(dy * 4)),
                (px - int(nx * 2), py - int(ny * 2)),
            ])
            NS._poly(surface, P["ice_dark"], [
                (px + int(dx * 7), py + int(dy * 7)),
                (px + int(nx), py + int(ny)),
                (px - int(dx * 3), py - int(dy * 3)),
                (px - int(nx), py - int(ny)),
            ])
            NS._poly(surface, P["ice_bright"], [
                (px + int(dx * 6), py + int(dy * 6)),
                (px, py), (px - int(dx * 2), py - int(dy * 2)),
            ])


    class ArcticBurnBeam:
        """Q — beam frost ungu menerjang target (fallback canvas)."""
        def __init__(self, sx, sy, tx, ty, life=45):
            self.sx = sx
            self.sy = sy
            self.tx = tx
            self.ty = ty
            self.life = life
            self.age = 0
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            NS = _NS_nyzrak
            P = NS.PALETTE
            t = self.age / self.life
            if t < 0.15:
                a_scale = t / 0.15
            elif t < 0.75:
                a_scale = 1.0
            else:
                a_scale = 1 - (t - 0.75) / 0.25
            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.hypot(dx, dy)
            if dist < 1:
                return
            ux, uy = dx / dist, dy / dist
            nx, ny = -uy, ux
            beam_len = dist * min(1.0, t / 0.3)
            steps = max(2, int(beam_len / 5))
            edge_top, edge_bot, core = [], [], []
            for i in range(steps + 1):
                tp = i / steps
                w = 3.0 + 2.0 * math.sin(phase * 6 + tp * 9)
                wav = math.sin(phase * 6 + tp * 12) * 2.0
                bx = self.sx + ux * beam_len * tp
                by = self.sy + uy * beam_len * tp
                edge_top.append((bx + nx * (w + wav), by + ny * (w + wav)))
                edge_bot.append((bx - nx * (w - wav), by - ny * (w - wav)))
                core.append((bx, by))
            NS._poly(surface, (*P["frost_dark"], int(150 * a_scale)),
                     edge_top + edge_bot[::-1])
            NS._poly(surface, (*P["frost_mid"], int(190 * a_scale)),
                     [(cx_ + nx * 1.6, cy_ + ny * 1.6) for cx_, cy_ in core]
                     + [(cx_ - nx * 1.6, cy_ - ny * 1.6)
                        for cx_, cy_ in core[::-1]])
            NS._poly(surface, (*P["frost_hot"], int(220 * a_scale)),
                     [(cx_ + nx * 0.7, cy_ + ny * 0.7) for cx_, cy_ in core]
                     + [(cx_ - nx * 0.7, cy_ - ny * 0.7)
                        for cx_, cy_ in core[::-1]])
            for i in range(5):
                tp = (phase * 0.5 + i * 0.2) % 1.0
                if tp > beam_len / dist:
                    continue
                fx = self.sx + ux * dist * tp + nx * 6
                fy = self.sy + uy * dist * tp + ny * 6
                NS._draw_snowflake(surface, int(fx), int(fy), 2,
                                   int(210 * a_scale), rotate=phase * 2 + i)
            if 0.3 < t < 0.85:
                k = math.sin((t - 0.3) / 0.55 * math.pi)
                ex = int(self.sx + ux * beam_len)
                ey = int(self.sy + uy * beam_len)
                for r, col in ((18, "frost_dark"), (11, "frost_bright"),
                               (5, "ice_pure")):
                    NS._aacircle(surface, (*P[col], int(200 * k)),
                                 (ex, ey), max(1, int(r * k)))
                for i in range(6):
                    a = i * math.pi / 3 + phase
                    cx2 = ex + int(math.cos(a) * 14)
                    cy2 = ey + int(math.sin(a) * 7)
                    NS._draw_crystal_spike(surface, cx2, cy2,
                                           cy2 - max(2, int(13 * k)), 2,
                                           int(220 * k), "frost")

    # ------------------------------------------------------------------
    # Manajemen projectile canvas fallback
    # ------------------------------------------------------------------
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_nyz_projectiles"):
            boss._nyz_projectiles = []
        if not hasattr(boss, "_nyz_shards"):
            boss._nyz_shards = []
        if not hasattr(boss, "_nyz_beams"):
            boss._nyz_beams = []

        for p in boss._nyz_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._nyz_projectiles = [p for p in boss._nyz_projectiles
                                 if p.alive or p.age < 3]

        for s in boss._nyz_shards:
            s.update()
            s.draw(surface, phase)
        boss._nyz_shards = [s for s in boss._nyz_shards if s.alive]

        for b in boss._nyz_beams:
            b.update()
            b.draw(surface, phase)
        boss._nyz_beams = [b for b in boss._nyz_beams if b.alive]


    def _spawn_ice_projectile(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_nyz_projectiles"):
            boss._nyz_projectiles = []
        boss._nyz_projectiles.append(_NS_nyzrak.IceProjectile(sx, sy, tx, ty))


    def _spawn_splinter_burst(boss, x, y, count=8):
        if not hasattr(boss, "_nyz_shards"):
            boss._nyz_shards = []
        for i in range(count):
            angle = i * math.pi * 2 / count
            boss._nyz_shards.append(_NS_nyzrak.SplinterShard(
                x, y, math.cos(angle), math.sin(angle) * 0.7, speed=5.5, life=28
            ))


    def _spawn_arctic_burn(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_nyz_beams"):
            boss._nyz_beams = []
        boss._nyz_beams.append(_NS_nyzrak.ArcticBurnBeam(sx, sy, tx, ty))

    # ===================================================================
    # SNOWFLAKE / CRYSTAL HELPERS
    # ===================================================================
    @staticmethod
    def _draw_snowflake(surface, cx, cy, size=3, alpha=255, rotate=0.0):
        """Bintang salju 6 lengan — 1px, alpha-safe."""
        P = _NS_nyzrak.PALETTE
        cx, cy = int(cx), int(cy)
        for i in range(6):
            a = rotate + i * math.pi / 3
            ex = cx + int(math.cos(a) * size)
            ey = cy + int(math.sin(a) * size)
            _NS_nyzrak._aaline(surface, (*P["ice_hot"], alpha), (cx, cy),
                               (ex, ey), 1)
            mx = cx + int(math.cos(a) * max(1, size - 1))
            my = cy + int(math.sin(a) * max(1, size - 1))
            tt = a + math.pi / 2
            _NS_nyzrak._aaline(surface, (*P["ice_bright"], alpha),
                               (mx, my),
                               (mx + int(math.cos(tt)), my + int(math.sin(tt))),
                               1)
        pygame.draw.rect(surface, (*P["ice_pure"], alpha), (cx, cy, 1, 1))


    @staticmethod
    def _draw_crystal_spike(surface, cx, base_y, tip_y, width=4, alpha=255,
                            color_set="ice"):
        """Paku kristal es tumbuh ke atas — band 3 nada."""
        if color_set == "ice":
            colors = ["ice_darkest", "ice_dark", "ice_mid", "ice_light",
                      "ice_bright"]
        else:
            colors = ["frost_darkest", "frost_dark", "frost_mid",
                      "frost_light", "frost_bright"]
        P = _NS_nyzrak.PALETTE
        _NS_nyzrak._poly(surface, (*P["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1), (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[0]], alpha), [
            (cx - width, base_y), (cx + width, base_y), (cx, tip_y),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[1]], alpha), [
            (cx - max(1, width - 1), base_y), (cx + max(1, width - 1), base_y),
            (cx, tip_y + (base_y - tip_y) // 4),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[2]], alpha), [
            (cx - max(1, width // 2), base_y), (cx + 1, base_y),
            (cx, tip_y + (base_y - tip_y) // 2),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[4]], alpha), [
            (cx, tip_y), (cx + 1, tip_y + (base_y - tip_y) // 3), (cx, base_y),
        ])

    # ===================================================================
    # GROUND / SHADOW / AURA (ruang layar)
    # ===================================================================
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan kontak reaktif: mengecil saat terangkat, dasar menapak."""
        NS = _NS_nyzrak
        if NS._shadow_cache is None:
            shadow = pygame.Surface((120, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 98 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["ice_dark"], 80),
                                (10, 5, 100, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h          # dasar tetap menapak di y+11
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase, active_skill):
        """Halo dingin lembut di belakang karakter (cached)."""
        NS = _NS_nyzrak
        if NS._aura_cache is None:
            NS._aura_cache = {}
        key = "q" if active_skill == "q" else "base"
        if key not in NS._aura_cache:
            aura = pygame.Surface((220, 200), pygame.SRCALPHA)
            color = NS.PALETTE["frost_darkest"] if key == "q" \
                else NS.PALETTE["ice_darkest"]
            for radius in range(90, 5, -4):
                alpha = int((90 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*color, min(255, alpha)),
                                 (110, 100), radius)
            NS._aura_cache[key] = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "e", "r") else 1.0
        spr = NS._aura_cache[key]
        spr.set_alpha(int(255 * max(0.15, min(1.0, pulse * strength))))
        surface.blit(spr, (x - 110, y - 100))


    def _draw_ground_frost(surface, x, y, phase, active_skill):
        """Beku tanah chunky: patch es + kristal kecil (cached)."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        if NS._ground_cache is None:
            g = pygame.Surface((150, 40), pygame.SRCALPHA)
            for i, (dx, w) in enumerate(((-48, 16), (-28, 22), (-4, 26),
                                         (24, 18), (46, 12))):
                yy = 18 + (i % 2) * 3
                pygame.draw.rect(g, (*P["ice_darkest"], 90),
                                 (75 + dx, yy, w, 2))
                pygame.draw.rect(g, (*P["ice_dark"], 120),
                                 (75 + dx + 2, yy, w - 4, 1))
            for dx, h in ((-40, 5), (-10, 7), (18, 6), (40, 4)):
                pygame.draw.polygon(g, (*P["ice_mid"], 150),
                                    [(75 + dx - 2, 20), (75 + dx + 2, 20),
                                     (75 + dx, 20 - h)])
            NS._ground_cache = g
        spr = NS._ground_cache
        pulse = math.sin(phase * 0.9) * 0.25 + 0.75
        spr.set_alpha(int(255 * pulse * (1.5 if active_skill else 1.0)))
        surface.blit(spr, (x - 75, y - 10))


    def _draw_frost_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Kabut dingin + salju melayang di bawah wyvern."""
        NS = _NS_nyzrak
        if NS._mist_cache is None:
            mist = pygame.Surface((150, 45), pygame.SRCALPHA)
            for radius in range(36, 3, -4):
                alpha = int((36 - radius) * 2.5)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                        (75 - radius * 2, 22 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            NS._mist_cache = mist
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 75, cy - 11))

        for i, offset in enumerate((-18, 0, 18)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 28)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            NS._aacircle(surface, (*NS.PALETTE["ice_dark"], alpha),
                         (sx, sy), 4)
            NS._aacircle(surface, (*NS.PALETTE["ice_hot"], alpha),
                         (sx, sy - 3), 1)
        for i in range(3):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = phase * 0.5 + i * math.pi * 2 / 5
            r = 24 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9) - int(t * 8)
            alpha = int(230 * (1 - t * 0.5) * strength)
            NS._draw_snowflake(surface, sx, sy, 2,
                               max(0, min(255, alpha)), rotate=phase + i)
        if trail:
            for i in range(3):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                NS._aacircle(surface, (*NS.PALETTE["ice_mid"], alpha),
                             (sx, sy), max(2, 5 - i))
                NS._aacircle(surface, (*NS.PALETTE["ice_light"], alpha),
                             (sx, sy), max(1, 3 - i))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Kilat lepas serangan: bintang 4 arah chunky."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        k = 0.0
        if 0.40 <= progress <= 0.64:
            k = math.sin((progress - 0.40) / 0.24 * math.pi)
        if k <= 0.02:
            return
        fx = x + 26 * facing
        fy = y - 12
        for r, col in ((10, "ice_dark"), (6, "ice_bright")):
            NS._aacircle(surface, (*P[col], int(120 * k)), (fx, fy),
                         max(1, int(r * k)))
        for a in (0, math.pi / 2, math.pi, math.pi * 1.5):
            ex = fx + int(math.cos(a) * 14 * k)
            ey = fy + int(math.sin(a) * 14 * k)
            NS._aaline(surface, (*P["ice_hot"], int(200 * k)), (fx, fy),
                       (ex, ey), 2)

    # ===================================================================
    # SWING ARC TRAIL — fallback canvas (deterministik dari kurva arc)
    # ===================================================================
    def _draw_swing_arc(surface, boss, x, y, action, ap, phase, facing):
        """Jejak sapuan tombak (canvas fallback, tanpa histori runtime).

        Posisi blade dihitung dari kurva _spear_pose_geom pada progress
        lampau -> quad sapuan memudar mengikuti arah serangan.
        """
        NS = _NS_nyzrak
        if action != "attack":
            return
        a0, a1 = NS.ATTACK_ACTIVE
        if not (a0 <= ap <= a1 + 0.12):
            return
        scale = NS.render_scale_of(boss)
        samples = []
        for i in range(6):
            back_ap = ap - i * 0.035
            if back_ap < a0:
                break
            ang_deg, reach, gx, gy = NS._spear_pose_geom(action, back_ap,
                                                         phase)
            ang = math.radians(ang_deg)
            grip = pygame.Vector2(x + gx * NS.PIXEL * facing * scale,
                                  y + gy * NS.PIXEL * scale)
            d = pygame.Vector2(math.cos(ang) * facing, math.sin(ang))
            samples.append(grip + d * (reach * NS.PIXEL * scale))
        if len(samples) < 3:
            return
        P = NS.PALETTE
        for i in range(len(samples) - 1):
            k = 1.0 - i / float(len(samples))
            p0, p1 = samples[i], samples[i + 1]
            nx = -(p1.y - p0.y)
            ny = (p1.x - p0.x)
            ln = max(1.0, math.hypot(nx, ny))
            nx, ny = nx / ln * 3.0, ny / ln * 3.0
            NS._poly(surface, (*P["ice_mid"], int(90 * k)), [
                (p0.x + nx, p0.y + ny), (p1.x + nx, p1.y + ny),
                (p1.x - nx, p1.y - ny), (p0.x - nx, p0.y - ny),
            ])
            NS._poly(surface, (*P["ice_bright"], int(150 * k)), [
                (p0.x + nx * 0.4, p0.y + ny * 0.4),
                (p1.x + nx * 0.4, p1.y + ny * 0.4),
                (p1.x - nx * 0.4, p1.y - ny * 0.4),
                (p0.x - nx * 0.4, p0.y - ny * 0.4),
            ])

    # ===================================================================
    # SKILL FX CANVAS — telegraph tanah + foreground (fallback)
    # ===================================================================
    def _draw_winters_curse_ground(surface, boss, x, y, timer, phase):
        """E: telegraph tanah — cincin es dash chunky menyempit."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        radius = int(25 + progress * 12)
        for i in range(12):
            a = i * math.pi * 2 / 12 + phase * 0.6
            ex = tx + math.cos(a) * radius
            ey = ty + math.sin(a) * radius * 0.45
            dx = -math.sin(a) * 3
            dy = math.cos(a) * 1.4
            NS._aaline(surface, (*P["ice_dark"], int(160 * pulse)),
                       (ex - dx, ey - dy), (ex + dx, ey + dy), 2)
        NS._ellipse(surface, (*P["ice_mid"], int(90 * pulse)),
                    (tx - radius, ty - radius // 3, radius * 2,
                     radius // 1.5), 2)


    def _draw_winters_curse_foreground(surface, boss, x, y, timer, phase):
        """E: penjara es kristal di sekitar target."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            for i in range(10):
                angle = phase * 2 + i * math.pi / 5
                r = 46 * (1 - progress / 0.15)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                NS._draw_snowflake(surface, sx, sy, 2, 200,
                                   rotate=phase * 4)
            return

        form_t = min(1.0, (progress - 0.15) / 0.3)
        tomb_w = int(26 * form_t)
        tomb_h = int(42 * form_t)
        if tomb_h <= 0:
            return
        NS._poly(surface, (*P["ice_darkest"], 200), [
            (tx - tomb_w, ty + 5), (tx - tomb_w, ty - tomb_h + 7),
            (tx - tomb_w // 2, ty - tomb_h), (tx + tomb_w // 2, ty - tomb_h),
            (tx + tomb_w, ty - tomb_h + 7), (tx + tomb_w, ty + 5),
        ])
        NS._poly(surface, (*P["ice_dark"], 180), [
            (tx - tomb_w + 2, ty + 4), (tx - tomb_w + 2, ty - tomb_h + 9),
            (tx - tomb_w // 2 + 2, ty - tomb_h + 2),
            (tx + tomb_w // 2 - 2, ty - tomb_h + 2),
            (tx + tomb_w - 2, ty - tomb_h + 9), (tx + tomb_w - 2, ty + 4),
        ])
        NS._poly(surface, (*P["ice_mid"], 150), [
            (tx - tomb_w + 4, ty + 3), (tx - tomb_w + 4, ty - tomb_h + 12),
            (tx - tomb_w // 2 + 4, ty - tomb_h + 5),
            (tx + tomb_w // 2 - 4, ty - tomb_h + 5),
            (tx + tomb_w - 6, ty - tomb_h + 12), (tx + tomb_w - 6, ty + 3),
        ])
        for i in range(3):
            NS._aaline(surface, (*P["ice_light"], 170),
                       (tx - tomb_w + 4, ty - i * 10),
                       (tx - tomb_w // 2, ty - tomb_h + i * 5 + 4), 1)
            NS._aaline(surface, (*P["ice_light"], 170),
                       (tx + tomb_w - 4, ty - i * 10),
                       (tx + tomb_w // 2, ty - tomb_h + i * 5 + 4), 1)
        NS._aaline(surface, (*P["ice_hot"], 220),
                   (tx, ty - tomb_h + 3), (tx, ty - 4), 1)
        for off in (-tomb_w + 2, 0, tomb_w - 2):
            NS._draw_crystal_spike(surface, tx + off, ty - tomb_h + 4,
                                   ty - tomb_h - 10, 3, 240, "ice")
        for i in range(5):
            angle = phase + i * math.pi * 2 / 5
            r = tomb_w + 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty - tomb_h // 2 + int(math.sin(angle) * tomb_h // 2)
            NS._draw_snowflake(surface, sx, sy, 2, 220,
                               rotate=phase * 2 + i)


    def _draw_cold_embrace_ground(surface, boss, x, y, timer, phase):
        """R: lingkaran tanah 3 cincin dash chunky."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        duration = 90
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(3):
            r = int(48 + i * 12 + math.sin(phase + i) * 4)
            segs = 14 + i * 4
            for s in range(segs):
                a = s * math.pi * 2 / segs - phase * (0.4 + i * 0.2)
                ex = x + math.cos(a) * r
                ey = (y + 45) + math.sin(a) * r * 0.32
                dx = -math.sin(a) * 3
                dy = math.cos(a)
                NS._aaline(surface, (*P["ice_bright"], int(110 * pulse)),
                           (ex - dx, ey - dy), (ex + dx, ey + dy), 1)


    def _draw_cold_embrace_foreground(surface, boss, x, y, timer, phase):
        """R: cincin paku kristal + kubah faset + ledakan salju."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        rise_t = min(1.0, progress / 0.3)
        ring_radius = 52

        for i in range(12):
            angle = i * math.pi * 2 / 12
            sxp = x + int(math.cos(angle) * ring_radius)
            syp = y + 18 + int(math.sin(angle) * ring_radius * 0.3)
            h = int(22 * rise_t * (0.7 + 0.3 * math.sin(i * 2.4)))
            NS._draw_crystal_spike(surface, sxp, syp, syp - h, 3,
                                   int(230 * (1 - progress * 0.5)), "ice")
        if progress > 0.25:
            dome_k = min(1.0, (progress - 0.25) / 0.2)
            fade = max(0.0, 1.0 - max(0.0, (progress - 0.75) / 0.25))
            R = int(46 * dome_k)
            if R > 4 and fade > 0:
                for i in range(7):
                    a0 = i * math.pi / 7
                    a1 = (i + 1) * math.pi / 7
                    p0 = (x + int(math.cos(a0) * R),
                          y - 6 + int(math.sin(a0) * R * 0.9))
                    p1 = (x + int(math.cos(a1) * R),
                          y - 6 + int(math.sin(a1) * R * 0.9))
                    col = P["ice_dark"] if i % 2 else P["ice_mid"]
                    NS._poly(surface, (*col, int(70 * fade)),
                             [(x, y - 6), p0, p1])
                NS._ellipse(surface, (*P["ice_bright"], int(90 * fade)),
                            (x - R, y - 6 - int(R * 0.92), R * 2,
                             int(R * 1.84)), 2)
        if 0.38 < progress < 0.7:
            k = 1 - (progress - 0.38) / 0.32
            for i in range(8):
                a = i * math.pi / 4 + phase * 0.8
                rr = 30 + (1 - k) * 60
                sx = x + int(math.cos(a) * rr)
                sy = y - 8 + int(math.sin(a) * rr * 0.5)
                NS._draw_snowflake(surface, sx, sy, 3, int(230 * k),
                                   rotate=phase * 3 + i)

    # ===================================================================
    # LIVE FX BRIDGE — heroes/nyzrak_fx.py (lazy, opsional)
    # ===================================================================
    _live_mod = None

    @staticmethod
    def _live_module():
        """Modul FX hidup atau None (lazy import + fail-safe)."""
        NS = _NS_nyzrak
        if NS._live_mod is None:
            try:
                from heroes import nyzrak_fx as mod
                NS._live_mod = mod
            except Exception:
                NS._live_mod = False
        return NS._live_mod or None

    # ===================================================================
    # SKILL SPAWN (canvas fallback — dilewati jika FX hidup mengambil alih)
    # ===================================================================
    def _handle_skill_projectiles(boss, x, y, active_skill, timer, owned):
        """Pemicu proyektil skill Q/W pada progres yang tepat."""
        NS = _NS_nyzrak
        tx, ty = NS._target_position(boss, x, y)

        if active_skill == "q":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_q_spawned", False):
                if not owned:
                    NS._spawn_arctic_burn(boss, x + 25 * boss.direction,
                                          y - 15, tx, ty)
                boss._nyz_q_spawned = True
            if progress > 0.7:
                boss._nyz_q_spawned = False

        elif active_skill == "w":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_w_spawned", False):
                sx = x + 25 * boss.direction
                sy = y - 10
                base_angle = math.atan2(ty - sy, (tx - sx) or 1)
                if not owned:
                    for i in range(5):
                        spread = (i - 2) * 0.25
                        a = base_angle + spread
                        if not hasattr(boss, "_nyz_shards"):
                            boss._nyz_shards = []
                        boss._nyz_shards.append(NS.SplinterShard(
                            sx, sy, math.cos(a), math.sin(a), speed=6.0,
                            life=35))
                boss._nyz_w_spawned = True
            if progress > 0.7:
                boss._nyz_w_spawned = False

    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_nyzrak(surface, boss, x, y):
        """Entry point render Nyzrak (jalur boss & pipeline hero)."""
        NS = _NS_nyzrak
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_attack_anim(boss)

        portrait = bool(getattr(boss, "_portrait_hd", False))
        canvas_pass = bool(getattr(boss, "_skip_renderer_projectiles", False))
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1

        info = NS._NyzAnimController.resolve(
            boss, moving, float(getattr(boss, "_nyz_move_mag", 0)) > 2.4)
        action, ap = info["action"], info["ap"]

        # ── lapisan FX hidup (pre): ground FX + attach ────────────────
        owned = False
        live = None
        if not portrait and not canvas_pass:
            live = NS._live_module()
            if live is not None:
                try:
                    live.draw_ground_layer(surface, boss, x, y)
                    owned = bool(live.owns(boss))
                except Exception:
                    owned = False

        # ── latar: aura + tanah beku + telegraph skill ────────────────
        NS._draw_frost_aura(surface, x, y, pulse, active_skill)
        NS._draw_ground_frost(surface, x, y + 46, pulse, active_skill)
        if active_skill == "e":
            NS._draw_winters_curse_ground(surface, boss, x, y,
                                          skill_timer, pulse)
        elif active_skill == "r":
            NS._draw_cold_embrace_ground(surface, boss, x, y,
                                         skill_timer, pulse)

        # ── bayangan + kabut dingin ───────────────────────────────────
        lift = NS.LIFT + (2.0 if action in ("run", "attack") else 0.0)
        NS._draw_shadow(surface, x, y + NS.GROUND_DY - 2, int(lift))
        NS._draw_frost_wisps(surface, x, y + 40, pulse,
                             trail=(action in ("walk", "run")),
                             facing=facing,
                             intense=(action == "attack"
                                      or action.startswith("cast")))

        # ── badan (rig pixel-art, komposit outline + lighting) ────────
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        tgt, tx, ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((240, 260), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            tgt, tx, ty = NS._flash_buf, 120, 140

        NS._draw_nyz_full(tgt, tx, ty, facing, pulse, action, ap)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - tx, y - ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - tx, y - ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ── FX canvas fallback (dilewati saat FX hidup aktif) ─────────
        if not owned and not canvas_pass:
            NS._draw_swing_arc(surface, boss, x, y, action, ap, pulse, facing)
            if action == "attack":
                NS._draw_cast_flash(surface, x, y, facing, ap)
                if (0.44 <= ap <= 0.50
                        and not getattr(boss, "_nyz_atk_spawned", False)
                        and getattr(NS, "_pose_variant_now", "thrust") == "thrust"):
                    txx, tyy = NS._target_position(boss, x, y)
                    spear = NS._spear_state(boss, x, y)
                    tip = spear["tip"]
                    NS._spawn_ice_projectile(boss, tip.x, tip.y, txx, tyy)
                    boss._nyz_atk_spawned = True
                if ap < 0.1 or ap > 0.9:
                    boss._nyz_atk_spawned = False

        NS._handle_skill_projectiles(boss, x, y, active_skill, skill_timer,
                                     owned)

        if not owned and not canvas_pass:
            NS._manage_projectiles(boss, surface, pulse)

        # ── foreground skill canvas ───────────────────────────────────
        if not owned:
            if active_skill == "e":
                NS._draw_winters_curse_foreground(surface, boss, x, y,
                                                  skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_cold_embrace_foreground(surface, boss, x, y,
                                                 skill_timer, pulse)

        # ── lapisan FX hidup (post): trail/proyektil/partikel/debug ───
        if live is not None and not portrait and not canvas_pass:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

    # ===================================================================
    # KOMPOSIT BADAN (buffer -> outline -> lighting)
    # ===================================================================
    def _draw_nyz_full(surface, cx, cy, facing, phase, action,
                       attack_progress=0.0):
        """Komposit ORIGINAL-MAX: rig low-res 2x + outline + rim light."""
        NS = _NS_nyzrak
        _composite_boss_body(
            surface, NS, NS._draw_nyz_full_raw,
            cx, cy, 1 if facing >= 0 else -1, phase, action,
            attack_progress,
            rim_add=(130, 220, 250), bsize=220)


    def _draw_nyz_full_raw(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0):
        """Raw rig: gambar low-res lalu nearest-scale 2x (chunky pixel)."""
        NS = _NS_nyzrak
        if NS._rig_buf is None:
            NS._rig_buf = pygame.Surface((NS.RIG_SIZE, NS.RIG_SIZE),
                                         pygame.SRCALPHA)
            NS._scale_buf = pygame.Surface(
                (NS.RIG_SIZE * NS.PIXEL, NS.RIG_SIZE * NS.PIXEL),
                pygame.SRCALPHA)
        rig = NS._rig_buf
        rig.fill((0, 0, 0, 0))
        pose = NS._rig_pose(action, phase, attack_progress)
        NS._draw_rig(rig, NS.RIG_SIZE // 2, NS.RIG_SIZE // 2, facing, pose,
                     action, phase, attack_progress)
        big = NS.RIG_SIZE * NS.PIXEL
        pygame.transform.scale(rig, (big, big), NS._scale_buf)
        surface.blit(NS._scale_buf, (cx - big // 2, cy - big // 2))

    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_nyzrak.draw_nyzrak(surface, boss, x, y)



# ====================================================================
# ANCIENT_APPARITION
# ====================================================================
class _NS_ancient_apparition:
    """Namespace ancient_apparition — FULL REWRITE visual & animasi.

    TRUE BOSS Level 3: wraith es purba.  Seluruh visual prosedural
    (pygame.draw + Surface + transform), tanpa satu pun aset eksternal.

    Arsitektur render (layer, urutan kontrak proyek):

        GROUND FX (aura beku, platform, telegraph skill)
          -> SHADOW (reaktif, dasar menapak)
          -> BACK ARM + BACK ORBIT
          -> SKIRT (jubah shard)
          -> TORSO -> ARMOR (pauldron) -> HEAD -> CROWN
          -> FRONT ARM + CLAW (senjata) -> FRONT ORBIT
          -> HIGHLIGHTS (rim + glint)
          -> ATTACK FX (flash cakar, trail canvas fallback)
          -> SKILL FX / PROJECTILE (fallback canvas)
          -> LIVE FX LAYER (heroes/ancient_apparition_fx — layar 1:1)
          -> DEBUG OVERLAY

    GAYA PIXEL ART: rig digambar di buffer setengah resolusi lalu
    di-upscale 2x nearest-neighbor (PIXEL = 2) sehingga piksel chunky,
    tepi keras, palet terbatas, highlight/shadow per-piksel — bukan
    vektor halus.

    Kontrak API lama dipertahankan (dipakai tools/test_level3_masterwork,
    heroes/__init__, bosses/_boss_index): draw_apparition / draw_boss /
    draw_ancient_apparition, _draw_shadow(lift), _draw_aa_body[_raw],
    _update_attack_anim, _detect_moving, durasi FX == AI.
    """

    # ── switch debug (hitbox/hurtbox/range/state/FPS/partikel) ──
    DEBUG_CHARACTER = False

    # ── cache komposit (piksel-identik, dibangun lazy) ──
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None
    _rig_lo = None          # buffer rig resolusi rendah (pixel art)
    _rig_px = None          # hasil upscale 2x (chunky)

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    #: Skala pixel art chunky (semua bagian badan digambar di 1/PIXEL).
    PIXEL = 2

    #: Geometri lengan (px penuh, relatif jangkar badan) — MIRROR dari
    #: heroes/ancient_apparition_fx (_SHOULDER/_UPPER/_FORE/_CLAW).
    #: Jangan ubah satu sisi saja: trail layar menempel pada angka ini.
    SHOULDER_OFF = (13.0, -6.0)
    UPPER_LEN = 10.0
    FORE_LEN = 11.0
    CLAW_LEN = 8.0

    #: Fase serangan (progress 0..1) — MIRROR heroes/ancient_apparition_fx.
    ATK_PHASES = {
        "anticipation": (0.00, 0.20),
        "windup":       (0.20, 0.38),
        "swing":        (0.38, 0.55),
        "follow":       (0.55, 0.75),
        "recovery":     (0.75, 1.00),
    }

    # ---------------------------------------------------------------------------
    # HD Ice Palette (dark fantasy, terbatas, kontras)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # ── kontrak inti ──
        "outline":     (6, 10, 20),
        "shadow":      (2, 5, 12),
        "dark":        (18, 38, 78),
        "body":        (30, 62, 112),
        "mid":         (55, 110, 180),
        "light":       (115, 175, 230),
        "highlight":   (170, 215, 250),
        "weapon":      (170, 215, 250),
        "fx":          (150, 225, 255),

        # ── ramp es ──
        "ice_darkest": (8, 20, 55),
        "ice_dark":    (22, 55, 115),
        "ice_mid":     (55, 110, 180),
        "ice_light":   (115, 175, 230),
        "ice_bright":  (170, 215, 250),
        "ice_hot":     (220, 240, 255),
        "ice_pure":    (245, 252, 255),

        # ── aksen ──
        "cyan_dark":   (15, 75, 110),
        "cyan_mid":    (55, 155, 195),
        "shadow_ice":  (12, 25, 55),
        "face_dark":   (30, 70, 130),
        "face_mid":    (95, 175, 230),
        "face_bright": (180, 230, 255),
        "face_hot":    (230, 248, 255),
        "frost_dark":  (30, 75, 130),
        "frost_mid":   (95, 165, 220),
        "frost_light": (170, 220, 250),
        "shadow_deep": (2, 5, 12),
        "white":       (255, 255, 255),
    }

    # ===================================================================
    # UTIL GAMBAR
    # ===================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ancient_apparition._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_ancient_apparition.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_ancient_apparition._clamp(color)
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
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey),
                         max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_ancient_apparition._clamp(color)
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
        color = _NS_ancient_apparition._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4),
                                  pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])),
                            width)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale pipeline hero (lihat catatan lama).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0)
                                   or 1.0)
                   * getattr(boss, "direction", 1)), int(y)

    def _hash01(seed):
        seed &= 0xFFFFFFFF
        seed = (seed * 2654435761) & 0xFFFFFFFF
        seed ^= seed >> 13
        seed = (seed * 1274126177) & 0xFFFFFFFF
        return ((seed ^ (seed >> 16)) & 0xFFFF) / 65535.0

    # ===================================================================
    # ANIMATION CONTROLLER
    # ===================================================================
    # State: IDLE / WALK / RUN / ATTACK / CAST / SKILL / HIT / HURT /
    #        DEATH / CHARGE / SPECIAL.
    # Sumber kebenaran state tetap atribut gameplay (timer, active_skill,
    # hurt_flash_timer) — renderer hanya menerjemahkan, tidak menyimpan.

    def _ease_in_out(t):
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        if t < 0.5:
            return 2.0 * t * t
        return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)

    def _ease_in(t):
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return t * t

    def _ease_out(t):
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return 1.0 - (1.0 - t) * (1.0 - t)

    def _attack_phase(progress):
        p = 0.0 if progress <= 0.0 else (1.0 if progress >= 1.0
                                         else progress)
        for name in ("anticipation", "windup", "swing", "follow",
                     "recovery"):
            lo, hi = _NS_ancient_apparition.ATK_PHASES[name]
            if p < hi:
                return name
        return "recovery"

    def _detect_moving(boss):
        """Deteksi gerak + kecepatan (px/frame) untuk pemisahan WALK/RUN."""
        NS = _NS_ancient_apparition
        if not hasattr(boss, "_aa_last_x"):
            boss._aa_last_x = boss.x
            boss._aa_last_y = boss.y
            boss._aa_speed = 0.0
            return False
        dx = boss.x - boss._aa_last_x
        dy = boss.y - boss._aa_last_y
        boss._aa_last_x = boss.x
        boss._aa_last_y = boss.y
        boss._aa_speed = math.hypot(dx, dy)
        return dx + dy > 0.3 or dx + dy < -0.3

    def _update_attack_anim(boss):
        """Jendela serangan dari timer gameplay (pola lama, tetap)."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aa_prev_timer", 0))
        active = bool(getattr(boss, "_aa_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aa_attack_active = True
            boss._aa_attack_frame = 0
            active = True
        elif active:
            boss._aa_attack_frame = int(
                getattr(boss, "_aa_attack_frame", 0)) + 1
            if boss._aa_attack_frame > cooldown:
                boss._aa_attack_active = False
                boss._aa_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._aa_attack_active = False
            boss._aa_attack_frame = 0
            active = False

        boss._aa_prev_timer = timer
        boss._aa_attack_progress = (
            min(1.0, getattr(boss, "_aa_attack_frame", 0)
                / max(1, cooldown - 1))
            if active else 0.0)

    def _resolve_state(boss, moving):
        """Pilih state animasi (prioritas: hurt > skill > attack > gerak)."""
        NS = _NS_ancient_apparition
        if not getattr(boss, "alive", True):
            return "death"
        if int(getattr(boss, "hurt_flash_timer", 0) or 0) > 3:
            return "hurt"
        skill = getattr(boss, "active_skill", None)
        if skill in ("q", "w", "e", "r"):
            return "cast_" + skill
        if getattr(boss, "_aa_attack_active", False):
            return "attack"
        speed = float(getattr(boss, "_moving_speed", None)
                      or getattr(boss, "_aa_speed", 0.0))
        if moving and speed > 1.35:
            return "run"
        if moving:
            return "walk"
        return "idle"

    # ===================================================================
    # GEOMETRI LENGAN (dipakai renderer + lapisan FX — satu sumber)
    # ===================================================================
    def arc_angle(progress, action, phase):
        """Sudut lengan depan (radian; 0 = depan, positif = naik).

        ANTICIPATION -> WIND-UP -> SWING -> FOLLOW -> RECOVERY: ayunan
        berbasis arc penuh (tidak ada teleport posisi awal ke akhir).
        """
        NS = _NS_ancient_apparition
        p = 0.0 if progress <= 0.0 else (1.0 if progress >= 1.0
                                         else progress)
        if action == "attack":
            if p < 0.20:                       # ANTICIPATION — tarik mundur
                return 0.35 + (-0.55 - 0.35) * NS._ease_in_out(p / 0.20)
            if p < 0.38:                       # WIND-UP — angkat ke belakang
                return -0.55 + (-1.62 - -0.55) * \
                    NS._ease_in_out((p - 0.20) / 0.18)
            if p < 0.55:                       # SWING — sapuan cepat
                return -1.62 + (0.55 - -1.62) * \
                    NS._ease_in((p - 0.38) / 0.17)
            if p < 0.75:                       # FOLLOW THROUGH
                return 0.55 + (0.75 - 0.55) * (p - 0.55) / 0.20
            return 0.75 + (0.35 - 0.75) * \
                NS._ease_out((p - 0.75) / 0.25)     # RECOVERY
        if action == "cast_w":                 # dua tangan mendorong depan
            return 0.05 + math.sin(phase * 26.0) * 0.03
        if action == "cast_e":                 # gather di dada
            return -0.12
        if action == "cast_q":                 # menyalurkan vortex
            return 0.28
        if action == "cast_r":                 # ULT: kedua tangan terangkat
            return 1.85
        if action == "run":
            return 0.15 + math.sin(phase * 5.2) * 0.5
        if action == "walk":
            return 0.35 + math.sin(phase * 2.6) * 0.22
        return 0.35 + math.sin(phase * 0.7) * 0.08

    def arm_geometry(facing, action, phase, progress=0.0):
        """(bahu, siku, tangan, ujung cakar) — offset px dari jangkar.

        Dipakai _rig_front_arm (//PIXEL) DAN heroes/ancient_apparition_fx
        (layar 1:1) supaya trail & asal shard menempel di cakar.
        """
        NS = _NS_ancient_apparition
        ang = NS.arc_angle(progress, action, phase)
        sx = NS.SHOULDER_OFF[0] * facing
        sy = NS.SHOULDER_OFF[1]
        bend = 0.55 if action == "attack" else 0.42
        ex = sx + math.cos(ang - bend) * NS.UPPER_LEN * facing
        ey = sy - math.sin(ang - bend) * NS.UPPER_LEN
        hx = ex + math.cos(ang) * NS.FORE_LEN * facing
        hy = ey - math.sin(ang) * NS.FORE_LEN
        tx = hx + math.cos(ang) * NS.CLAW_LEN * facing
        ty = hy - math.sin(ang) * NS.CLAW_LEN
        return ((sx, sy), (ex, ey), (hx, hy), (tx, ty))

    # ===================================================================
    # RIG PIXEL ART (buffer setengah resolusi -> upscale 2x chunky)
    # ===================================================================
    RIG_W = 64
    RIG_H = 76
    RIG_AX = 32            # jangkar low-res
    RIG_AY = 34

    def _rig_buffers():
        NS = _NS_ancient_apparition
        if NS._rig_lo is None:
            NS._rig_lo = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                        pygame.SRCALPHA)
            NS._rig_px = pygame.Surface((NS.RIG_W * NS.PIXEL,
                                         NS.RIG_H * NS.PIXEL),
                                        pygame.SRCALPHA)
        return NS._rig_lo, NS._rig_px

    # ----------------------------- SKIRT -----------------------------
    def _rig_skirt(buf, phase, action, lean):
        """Jubah shard mengambang: massa + 6 shard hem bergantian.

        WALK: shard hem kiri/kanan menendang bergantian (foot timing),
        hem bergoyang; RUN: amplitude lebih besar dan condong.
        """
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        f = 1.6 if action in ("run",) else (1.0 if action in ("walk",)
                                            else 0.6)
        sway = math.sin(phase * (2.6 if action != "idle" else 0.7)) * f

        # massa utama (panggul)
        pygame.draw.polygon(buf, P["shadow_ice"], [
            (ax - 11, ay + 2), (ax + 11, ay + 2),
            (ax + 9, ay + 13), (ax - 9, ay + 13)])
        pygame.draw.polygon(buf, P["ice_darkest"], [
            (ax - 10, ay + 2), (ax + 10, ay + 2),
            (ax + 8, ay + 12), (ax - 8, ay + 12)])
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 8, ay + 3), (ax + 8, ay + 3),
            (ax + 6, ay + 11), (ax - 6, ay + 11)])
        pygame.draw.polygon(buf, P["ice_mid"], [
            (ax - 5, ay + 4), (ax + 5, ay + 4),
            (ax + 4, ay + 9), (ax - 4, ay + 9)])
        # garis facet vertikal
        for lx in (-4, 0, 4):
            pygame.draw.line(buf, P["ice_light"],
                             (ax + lx, ay + 4), (ax + lx, ay + 9), 1)

        # shard hem bergantian (kiri & kanan berlawanan fase = langkah)
        hem = ((-10, 6, 0), (-6, 9, math.pi), (-2, 7, 0),
               (2, 10, math.pi), (6, 8, 0), (10, 6, math.pi))
        for off, hgt, ph_off in hem:
            kick = math.sin(phase * 2.6 + ph_off) * (2.0 * f)
            bx = ax + off + int(kick + sway * off * 0.12)
            top = ay + 11
            tipx = bx + int(kick * 0.6 + lean * 0.5)
            tipy = top + hgt + (1 if math.sin(phase * 2.6 + ph_off) > 0
                                else 0)
            pygame.draw.polygon(buf, P["shadow_deep"], [
                (bx - 2 + 1, top + 1), (bx + 2 + 1, top + 1),
                (tipx + 1, tipy + 1)])
            pygame.draw.polygon(buf, P["ice_darkest"], [
                (bx - 2, top), (bx + 2, top), (tipx, tipy)])
            pygame.draw.polygon(buf, P["ice_dark"], [
                (bx - 1, top), (bx + 1, top), (tipx, tipy - 1)])
            pygame.draw.line(buf, P["ice_bright"],
                             (bx, top + 1), (tipx, tipy - 1), 1)
            buf.set_at((int(tipx), int(tipy) - 1), P["ice_hot"])

    # ----------------------------- TORSO -----------------------------
    def _rig_torso(buf, phase, action, core_hot):
        """Dada kristal heksagonal + inti menyala + pauldron."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        # torso heksagonal
        pygame.draw.polygon(buf, P["shadow_ice"], [
            (ax - 9, ay - 9), (ax + 9, ay - 9), (ax + 11, ay - 1),
            (ax + 6, ay + 3), (ax - 6, ay + 3), (ax - 11, ay - 1)])
        pygame.draw.polygon(buf, P["ice_darkest"], [
            (ax - 8, ay - 8), (ax + 8, ay - 8), (ax + 10, ay - 1),
            (ax + 5, ay + 2), (ax - 5, ay + 2), (ax - 10, ay - 1)])
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 6, ay - 7), (ax + 6, ay - 7), (ax + 8, ay - 1),
            (ax + 4, ay + 1), (ax - 4, ay + 1), (ax - 8, ay - 1)])
        # inti dada (jantung es) — denyut
        pulse = 0.7 + 0.3 * math.sin(phase * 1.5)
        core = P["ice_bright"] if core_hot else P["ice_light"]
        pygame.draw.rect(buf, P["shadow_deep"], (ax - 2, ay - 4, 4, 4))
        pygame.draw.rect(buf, core, (ax - 2, ay - 4, 3, 3))
        buf.set_at((ax - 1, ay - 3), P["ice_hot"])
        if core_hot or pulse > 0.85:
            buf.set_at((ax, ay - 3), P["ice_pure"])
        # facet diagonal
        pygame.draw.line(buf, P["ice_mid"], (ax - 6, ay - 6),
                         (ax - 3, ay + 1), 1)
        pygame.draw.line(buf, P["ice_mid"], (ax + 6, ay - 6),
                         (ax + 3, ay + 1), 1)
        pygame.draw.line(buf, P["ice_bright"], (ax - 5, ay - 6),
                         (ax - 4, ay - 3), 1)

        # pauldron (armor bahu): 3 paku per sisi
        for side in (-1, 1):
            base = [(ax + side * 8, ay - 8), (ax + side * 12, ay - 9),
                    (ax + side * 10, ay - 5)]
            pygame.draw.polygon(buf, P["ice_darkest"], base)
            pygame.draw.polygon(buf, P["ice_dark"], [
                (ax + side * 8, ay - 8), (ax + side * 11, ay - 9),
                (ax + side * 9, ay - 6)])
            for i, (dx, dy, hgt) in enumerate(((9, -9, 4), (11, -8, 6),
                                               (10, -6, 3))):
                bx = ax + side * dx
                by = ay + dy
                pygame.draw.polygon(buf, P["ice_mid"], [
                    (bx - 1, by), (bx + 1, by), (bx, by - hgt)])
                buf.set_at((bx, by - hgt), P["ice_hot"])

    # ----------------------------- HEAD ------------------------------
    def _rig_head(buf, phase, tilt, facing, hurt):
        """Kepala berhood berongga: wajah glow, mata menyala, dagu shard."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax = NS.RIG_AX + int(tilt)
        ay = NS.RIG_AY - 13 + (1 if math.sin(phase * 0.8) > 0.4 else 0)
        breath = 1 if math.sin(phase * 1.6) > 0.2 else 0

        # hood
        pygame.draw.polygon(buf, P["ice_darkest"], [
            (ax - 6, ay - 6), (ax + 6, ay - 6), (ax + 8, ay),
            (ax + 7, ay + 5), (ax - 7, ay + 5), (ax - 8, ay)])
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 5, ay - 5), (ax + 5, ay - 5), (ax + 7, ay),
            (ax + 6, ay + 4), (ax - 6, ay + 4), (ax - 7, ay)])
        # puncak hood melengkung (breathing)
        pygame.draw.polygon(buf, P["ice_mid"], [
            (ax - 3, ay - 5), (ax + 3, ay - 5), (ax, ay - 7 - breath)])
        # wajah berongga
        pygame.draw.rect(buf, P["shadow_deep"], (ax - 4, ay - 3, 8, 6))
        pygame.draw.rect(buf, P["face_dark"], (ax - 3, ay - 2, 6, 4))
        # mata menyala (pixel 1x2, flicker)
        flick = 0 if hurt else (1 if math.sin(phase * 7.0) > 0.93 else 0)
        for side in (-1, 1):
            ex = ax + side * 2
            buf.set_at((ex, ay - 1), P["face_hot"])
            buf.set_at((ex, ay), P["face_bright"] if not flick
                       else P["white"])
        # mulut berongga glow
        pygame.draw.rect(buf, P["face_mid"], (ax - 1, ay + 2, 2, 1))
        # duri hood samping
        for side in (-1, 1):
            pygame.draw.polygon(buf, P["ice_darkest"], [
                (ax + side * 7, ay - 3), (ax + side * 10, ay - 5),
                (ax + side * 8, ay - 1)])
            pygame.draw.line(buf, P["ice_bright"],
                             (ax + side * 7, ay - 3),
                             (ax + side * 9, ay - 4), 1)
        # dagu shard
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 1, ay + 5), (ax + 1, ay + 5), (ax, ay + 8)])
        buf.set_at((ax, ay + 7), P["ice_bright"])

    # ----------------------------- CROWN -----------------------------
    def _rig_crown(buf, phase, flare):
        """Mahkota es: 5 paku tinggi, ujung menyala, bergoyang halus."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax = NS.RIG_AX
        ay = NS.RIG_AY - 19      # puncak hood
        sway = int(math.sin(phase * 0.9) * 1)
        spikes = ((0, 13), (-3, 10), (3, 10), (-6, 8), (6, 8))
        for off, hgt in spikes:
            bx = ax + off + (sway if abs(off) > 3 else sway // 2)
            tip = (bx + (1 if off > 0 else -1 if off < 0 else 0)
                   + sway // 2, ay - hgt)
            pygame.draw.polygon(buf, P["shadow_deep"], [
                (bx - 2 + 1, ay + 1), (bx + 2 + 1, ay + 1),
                (tip[0] + 1, tip[1] + 1)])
            pygame.draw.polygon(buf, P["ice_darkest"], [
                (bx - 2, ay), (bx + 2, ay), tip])
            pygame.draw.polygon(buf, P["ice_dark"], [
                (bx - 1, ay), (bx + 1, ay), (tip[0], tip[1] + 1)])
            pygame.draw.line(buf, P["ice_bright"], (bx, ay),
                             (tip[0], tip[1] + 1), 1)
            buf.set_at((int(tip[0]), int(tip[1])),
                       P["ice_pure"] if flare else P["ice_hot"])

    # ----------------------------- ARMS ------------------------------
    def _rig_arm(buf, facing, action, phase, progress, back):
        """Satu lengan kristal: lengan atas + bawah + cakar 3 jari."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        if back:
            facing = -facing
            phase = phase + math.pi          # fase berlawanan
            if action == "attack":
                action = "idle"              # lengan belakang santai
            elif action.startswith("cast_") and action != "cast_r":
                action = "idle"
            progress = 0.0
        (sx, sy), (ex, ey), (hx, hy), (tx, ty) = NS.arm_geometry(
            facing, action, phase, progress)
        dark = P["ice_darkest"] if back else P["ice_dark"]
        mid = P["ice_dark"] if back else P["ice_mid"]
        bri = P["ice_mid"] if back else P["ice_bright"]

        def seg(x1, y1, x2, y2, w):
            pygame.draw.line(buf, dark, (x1 // 2 + ax, y1 // 2 + ay),
                             (x2 // 2 + ax, y2 // 2 + ay), w)

        # lengan atas & bawah (lebar 3 px low-res = 6 px chunky)
        seg(sx, sy, ex, ey, 3)
        seg(ex, ey, hx, hy, 3)
        # highlight atas lengan
        pygame.draw.line(buf, mid,
                         (sx // 2 + ax, sy // 2 + ay - 1),
                         (ex // 2 + ax, ey // 2 + ay - 1), 1)
        pygame.draw.line(buf, mid,
                         (ex // 2 + ax, ey // 2 + ay - 1),
                         (hx // 2 + ax, hy // 2 + ay - 1), 1)
        # telapak
        px_, py_ = int(hx // 2 + ax), int(hy // 2 + ay)
        pygame.draw.rect(buf, dark, (px_ - 1, py_ - 1, 3, 3))
        buf.set_at((px_, py_), mid)
        # cakar 3 jari mengarah ujung
        ang = math.atan2(-(ty - hy), (tx - hx) * facing)
        for da in (-0.45, 0.0, 0.45):
            fx = px_ + int(math.cos(ang + da) * 3 * facing)
            fy = py_ - int(math.sin(ang + da) * 3)
            pygame.draw.line(buf, bri, (px_, py_), (fx, fy), 1)
            buf.set_at((fx, fy), P["ice_hot"] if not back
                       else P["ice_mid"])

    # --------------------------- ORBIT -------------------------------
    def _rig_orbit(buf, phase, action, progress, facing):
        """3 splinter es mengorbit — sumber visual shard basic attack."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        base_r = 21
        for i in range(3):
            spd = (1.1, -0.8, 1.6)[i]
            r = base_r + (3, -2, 5)[i] + int(math.sin(phase * 1.3 + i) * 2)
            ang = phase * spd + i * math.tau / 3.0
            oy = ay - 4 + (i - 1) * 5 + int(math.sin(phase + i * 2) * 2)
            ox = ax + int(math.cos(ang) * r)
            # saat menyerang, splinter depan menyusul tangan (maju)
            if action == "attack" and 0.3 < progress < 0.6 and i == 2:
                ox += int(6 * facing)
            ln = 4 + (i % 2) * 2
            dx_, dy_ = math.cos(ang + math.pi / 2), math.sin(ang
                                                             + math.pi / 2)
            pygame.draw.line(buf, P["ice_darkest"],
                             (ox - int(dx_ * ln), oy - int(dy_ * ln)),
                             (ox + int(dx_ * ln), oy + int(dy_ * ln)), 2)
            pygame.draw.line(buf, P["ice_light"],
                             (ox - int(dx_ * (ln - 1)),
                              oy - int(dy_ * (ln - 1))),
                             (ox + int(dx_ * (ln - 1)),
                              oy + int(dy_ * (ln - 1))), 1)
            buf.set_at((ox + int(dx_ * ln), oy + int(dy_ * ln)),
                       P["ice_hot"])

    # ------------------------ MASTERWORK (full-res) ------------------
    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Pass detail full-res: halo mata, glow inti, glint mahkota."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        flick = 0.5 + 0.5 * math.sin(phase * 7.0)
        cast = action.startswith("cast_")
        hot = 1.35 if cast else 1.0
        # halo mata (dua titik glow kecil)
        for side in (-1, 1):
            ex = cx + int(tilt_head(phase)) + side * 4
            ey = cy - 27
            NS._aacircle(surface, (*P["face_dark"], int(110 * hot)),
                         (ex, ey), 4)
            NS._aacircle(surface, (*P["face_bright"], int(60 * hot * flick)),
                         (ex, ey), 6)
        # glow inti dada
        pulse = 0.7 + 0.3 * math.sin(phase * 1.5)
        NS._aacircle(surface, (*P["ice_light"], int(120 * pulse * hot)),
                     (cx, cy - 1), 7)
        NS._aacircle(surface, (*P["ice_hot"], int(70 * pulse * hot)),
                     (cx, cy - 1), 4)
        # glint ujung mahkota (2 titik berkedip)
        for off, k in ((0, 0), (-5, 2), (5, 3)):
            gx = cx + off
            gy = cy - 47 - (9 if off == 0 else 6)
            tw = 0.5 + 0.5 * math.sin(phase * 3.0 + k * 1.7)
            NS._aacircle(surface, (*P["ice_hot"], int(150 * tw)),
                         (gx, gy), 2)
        # rim kiri-atas: 3 piksel terang di tepi hood/torso
        pygame.draw.line(surface, P["ice_bright"],
                         (cx - 9, cy - 30), (cx - 8, cy - 27), 1)
        pygame.draw.line(surface, P["ice_bright"],
                         (cx - 12, cy - 12), (cx - 11, cy - 9), 1)
        del cast

    # ===================================================================
    # BODY RENDER (komposit: rig chunky + outline + lighting)
    # ===================================================================
    def _draw_aa_body(surface, cx, cy, facing, phase, action,
                      attack_progress=0):
        """Komposit ORIGINAL-MAX: buffer tetap + outline + lighting."""
        _composite_boss_body(
            surface, _NS_ancient_apparition,
            _NS_ancient_apparition._draw_aa_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(150, 225, 255), bsize=200)

    def _draw_aa_body_raw(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Rig pixel art: low-res -> upscale 2x -> blit pada jangkar."""
        NS = _NS_ancient_apparition
        hurt = action == "hurt"
        ap = attack_progress if action == "attack" else 0.0
        ph = NS._attack_phase(ap) if ap > 0 else ""

        # ── bob & lean per state ──
        if action == "walk":
            bob = -abs(int(math.sin(phase * 2.6) * 2))
            lean = 1
        elif action == "run":
            bob = -abs(int(math.sin(phase * 5.2) * 3))
            lean = 3
        elif action == "attack":
            if ph == "anticipation":
                bob = -1
                lean = -2
            elif ph == "windup":
                bob = 1
                lean = -3
            elif ph == "swing":
                bob = -1
                lean = 5
            elif ph == "follow":
                bob = 0
                lean = 6
            else:
                bob = 0
                lean = 2
        elif action.startswith("cast_"):
            bob = -int(abs(math.sin(phase * 1.2)) * 2)
            lean = 2 if action != "cast_r" else 0
        else:
            bob = -int(abs(math.sin(phase * 0.8)) * 1)   # breathing
            lean = 0
        if hurt:
            lean = -2
            bob = 0

        lo, px = NS._rig_buffers()
        lo.fill((0, 0, 0, 0))
        core_hot = action.startswith("cast_") or \
            (ap > 0.35 and ap < 0.6)
        tilt = (2 if hurt else 0) + (1 if ph == "swing" else 0)

        # URUTAN LAYER RIG (back -> front)
        NS._rig_arm(lo, facing, action, phase, ap, back=True)
        NS._rig_orbit(lo, phase, action, ap, facing)
        NS._rig_skirt(lo, phase, action, lean)
        NS._rig_torso(lo, phase, action, core_hot)
        NS._rig_head(lo, phase, tilt, facing, hurt)
        NS._rig_crown(lo, phase, core_hot)
        NS._rig_arm(lo, facing, action, phase, ap, back=False)

        # upscale 2x nearest-neighbor -> piksel chunky keras
        pygame.transform.scale(lo, px.get_size(), px)
        ox = int(cx) - NS.RIG_AX * NS.PIXEL
        oy = int(cy) - NS.RIG_AY * NS.PIXEL + bob * NS.PIXEL
        surface.blit(px, (ox, oy))

        # pass detail full-res (glow/glint) pada posisi yang sama
        NS._masterwork_finish(surface, cx + lean, cy + bob, facing, phase,
                              action, attack_progress)

    # ===================================================================
    # CANVAS PROJECTILE SYSTEM (fallback tanpa lapisan hidup)
    # ===================================================================
    class IceShardProjectile:
        """Cold Touch kecil — cepat, homing ringan (canvas space).

        Bidang lengkap: position/velocity/speed/damage/lifetime/target/
        radius/rotation/trail/particles/active.
        """
        SPEED = 7.5

        def __init__(self, sx, sy, tx, ty, target=None):
            self.position = [float(sx), float(sy)]
            self.tx, self.ty = float(tx), float(ty)
            dx, dy = float(tx) - sx, float(ty) - sy
            d = max(1.0, math.hypot(dx, dy))
            self.velocity = [dx / d * self.SPEED, dy / d * self.SPEED]
            self.speed = float(self.SPEED)
            self.damage = 0
            self.lifetime = 90.0
            self.age = 0.0
            self.target = target
            self.radius = 4
            self.rotation = math.atan2(dy, dx)
            self.trail = []
            self.particles = True
            self.alive = True

        def update(self, dt=1.0 / 60.0):
            self.age += dt
            if self.age > self.lifetime:
                self.alive = False
                return
            # target tracking: titik tujuan mengikuti target hidup
            if self.target is not None and getattr(self.target, "alive",
                                                   True):
                tx = getattr(self.target, "x", None)
                ty = getattr(self.target, "y", None)
                if tx is not None and ty is not None:
                    self.tx, self.ty = float(tx), float(ty)
            dx = self.tx - self.position[0]
            dy = self.ty - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.position[0]), int(self.position[1])))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.position[0] += dx / dist * self.speed
            self.position[1] += dy / dist * self.speed
            self.rotation = math.atan2(dy, dx)

        def draw(self, surface, phase):
            NS = _NS_ancient_apparition
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                a = int(60 + i * 14)
                r = max(1, 3 - (len(self.trail) - i))
                NS._aacircle(surface, (*P["ice_dark"], a), (tx, ty), r + 1)
                NS._aacircle(surface, (*P["ice_light"], a), (tx, ty),
                             max(1, r - 1))
            if not self.alive:
                return
            px, py = int(self.position[0]), int(self.position[1])
            dx, dy = math.cos(self.rotation), math.sin(self.rotation)
            pxp, pyp = -dy, dx
            shard = [(px + int(dx * 8), py + int(dy * 8)),
                     (px + int(pxp * 4), py + int(pyp * 4)),
                     (px - int(dx * 5), py - int(dy * 5)),
                     (px - int(pxp * 4), py - int(pyp * 4))]
            NS._poly(surface, P["ice_darkest"], shard)
            NS._poly(surface, P["ice_mid"], [
                (p[0] - dx * 2, p[1] - dy * 2) for p in shard[:3]])
            NS._aaline(surface, P["ice_pure"],
                       (px + int(dx * 6), py + int(dy * 6)),
                       (px - int(dx * 3), py - int(dy * 3)), 1)
            NS._aacircle(surface, (*P["ice_light"], 110), (px, py), 9)
            NS._aacircle(surface, (*P["ice_bright"], 70), (px, py), 5)

    class IceBoltProjectile:
        """Ice Blast (E) — bolt besar lambat + shard pengorbit."""
        SPEED = 5.0

        def __init__(self, sx, sy, tx, ty, target=None):
            self.position = [float(sx), float(sy)]
            self.tx, self.ty = float(tx), float(ty)
            dx, dy = float(tx) - sx, float(ty) - sy
            d = max(1.0, math.hypot(dx, dy))
            self.velocity = [dx / d * self.SPEED, dy / d * self.SPEED]
            self.speed = float(self.SPEED)
            self.damage = 0
            self.lifetime = 140.0
            self.age = 0.0
            self.target = target
            self.radius = 8
            self.rotation = math.atan2(dy, dx)
            self.trail = []
            self.particles = True
            self.alive = True

        def update(self, dt=1.0 / 60.0):
            self.age += dt
            if self.age > self.lifetime:
                self.alive = False
                return
            dx = self.tx - self.position[0]
            dy = self.ty - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < self.speed + 6:
                self.alive = False
                return
            self.trail.append((int(self.position[0]), int(self.position[1])))
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.position[0] += dx / dist * self.speed
            self.position[1] += dy / dist * self.speed

        def draw(self, surface, phase):
            NS = _NS_ancient_apparition
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                a = int(50 + i * 13)
                r = max(1, 5 - (len(self.trail) - i))
                NS._aacircle(surface, (*P["ice_dark"], a), (tx, ty), r + 2)
                NS._aacircle(surface, (*P["ice_mid"], a), (tx, ty), r)
            if not self.alive:
                return
            px, py = int(self.position[0]), int(self.position[1])
            dx, dy = math.cos(self.rotation), math.sin(self.rotation)
            pxp, pyp = -dy, dx
            shard = [(px + int(dx * 14), py + int(dy * 14)),
                     (px + int(pxp * 7), py + int(pyp * 7)),
                     (px - int(dx * 9), py - int(dy * 9)),
                     (px - int(pxp * 7), py - int(pyp * 7))]
            NS._poly(surface, P["shadow_deep"],
                     [(p[0] + 2, p[1] + 2) for p in shard])
            NS._poly(surface, P["ice_darkest"], shard)
            NS._poly(surface, P["ice_dark"], [
                (p[0] - dx * 2, p[1] - dy * 2) for p in shard])
            NS._poly(surface, P["ice_mid"], [
                (p[0] - dx * 5, p[1] - dy * 5) for p in shard[:3]])
            NS._aaline(surface, P["ice_pure"],
                       (px + int(dx * 12), py + int(dy * 12)),
                       (px - int(dx * 6), py - int(dy * 6)), 1)
            NS._aacircle(surface, (*P["ice_light"], 130), (px, py), 15)
            NS._aacircle(surface, (*P["ice_bright"], 90), (px, py), 9)
            for i in range(3):
                ang = phase * 3 + i * math.tau / 3.0
                ox = px + int(math.cos(ang) * 12)
                oy = py + int(math.sin(ang) * 12)
                NS._draw_snowflake(surface, ox, oy, 2, 190, rotate=phase)

    class FrostBeam:
        """Chilling Touch (W) — beam gerigi bergerak (canvas fallback)."""
        def __init__(self, sx, sy, tx, ty, life=45):
            self.sx, self.sy = int(sx), int(sy)
            self.tx, self.ty = int(tx), int(ty)
            self.life = life
            self.age = 0
            self.alive = True
            self.rotation = math.atan2(self.ty - self.sy,
                                       self.tx - self.sx)

        def update(self, dt=1.0 / 60.0):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            NS = _NS_ancient_apparition
            P = NS.PALETTE
            t = self.age / self.life
            a_scale = t / 0.15 if t < 0.15 else (
                1.0 - (t - 0.7) / 0.3 if t > 0.7 else 1.0)
            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.hypot(dx, dy)
            if dist < 1 or a_scale <= 0:
                return
            dx /= dist
            dy /= dist
            pxp, pyp = -dy, dx
            steps = int(dist / 7)
            for i in range(steps):
                tp = i / max(1, steps - 1)
                bx = self.sx + dx * dist * tp
                by = self.sy + dy * dist * tp
                wave = math.sin(phase * 6 + tp * 14) * 3.5
                fx = int(bx + pxp * wave)
                fy = int(by + pyp * wave)
                a = int(200 * a_scale * (1.0 - tp * 0.35))
                w = int(4 + 2 * math.sin(math.pi * tp))
                NS._aacircle(surface, (*P["ice_dark"], a), (fx, fy), w + 2)
                NS._aacircle(surface, (*P["ice_mid"], a), (fx, fy), w)
                NS._aacircle(surface, (*P["ice_hot"], a), (fx, fy),
                             max(1, w - 2))
                if i % 2 == 0:
                    gx = int(fx + pxp * (w + 3))
                    gy = int(fy + pyp * (w + 3))
                    ex = int(gx + pxp * 4 + dx * (2 if i % 4 == 0 else -2))
                    ey = int(gy + pyp * 4 + dy * (2 if i % 4 == 0 else -2))
                    NS._aaline(surface, (*P["ice_bright"], a), (gx, gy),
                               (ex, ey), 1)
            for i in range(7):
                tp = (phase * 0.35 + i * 0.15) % 1.0
                sx = int(self.sx + dx * dist * tp)
                sy = int(self.sy + dy * dist * tp)
                NS._draw_snowflake(surface, sx + int(pxp * 7),
                                   sy + int(pyp * 7), 2,
                                   int(220 * a_scale),
                                   rotate=phase * 2 + i)

    # ===================================================================
    # STATE MANAGEMENT + SPAWN
    # ===================================================================
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        if not hasattr(boss, "_aa_beams"):
            boss._aa_beams = []
        for proj in boss._aa_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._aa_projectiles = [p for p in boss._aa_projectiles
                                if p.alive or p.age < 0.08]
        for beam in boss._aa_beams:
            beam.update()
            beam.draw(surface, phase)
        boss._aa_beams = [b for b in boss._aa_beams if b.alive]

    def _spawn_ice_shard(boss, sx, sy, tx, ty):
        # Saat Ancient Apparition DIMAINKAN sebagai hero, basic attack
        # menembakkan homing shard dari sistem Hero — shard internal
        # canvas ini dimatikan supaya tidak dobel (lihat _entity.py).
        if getattr(boss, "_aa_hero_basic_shard", False):
            return
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        boss._aa_projectiles.append(
            _NS_ancient_apparition.IceShardProjectile(
                sx, sy, tx, ty, target=getattr(boss, "target", None)))

    def _spawn_ice_bolt(boss, sx, sy, tx, ty):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        boss._aa_projectiles.append(
            _NS_ancient_apparition.IceBoltProjectile(
                sx, sy, tx, ty, target=getattr(boss, "target", None)))

    def _spawn_frost_beam(boss, sx, sy, tx, ty):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_aa_beams"):
            boss._aa_beams = []
        boss._aa_beams.append(
            _NS_ancient_apparition.FrostBeam(sx, sy, tx, ty, life=45))

    # ===================================================================
    # GROUND FX + SHADOW
    # ===================================================================
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan reaktif: mengecil saat terangkat, dasar menapak."""
        NS = _NS_ancient_apparition
        if NS._shadow_cache is None:
            shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 88 + radius * 2,
                     radius * 2))
            pygame.draw.ellipse(shadow,
                                (*NS.PALETTE["ice_dark"], 80),
                                (10, 5, 90, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))

    def _draw_frost_aura(surface, x, y, phase, active_skill):
        """Aura dingin halus di belakang badan (cached)."""
        NS = _NS_ancient_apparition
        if NS._aura_cache is None:
            aura = pygame.Surface((200, 180), pygame.SRCALPHA)
            for radius in range(80, 5, -4):
                alpha = int((80 - radius) * 1.15)
                if alpha > 0:
                    NS._aacircle(
                        aura,
                        (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                        (100, 90), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.4 if active_skill in ("q", "w", "e", "r") else 1.0
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.15, min(1.0, pulse * strength))))
        surface.blit(spr, (x - 100, y - 90))

    def _draw_ground_frost(surface, x, y, phase, active_skill):
        """Platform beku di bawah kaki (cached) + denyut skill."""
        NS = _NS_ancient_apparition
        if NS._ground_cache is None:
            ring = pygame.Surface((140, 46), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 160),
                                (5, 10, 130, 26), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 190),
                                (20, 14, 100, 18), 2)
            for i in range(10):
                angle = i * math.pi / 5
                x1 = 70 + int(math.cos(angle) * 32)
                y1 = 23 + int(math.sin(angle) * 7)
                x2 = 70 + int(math.cos(angle) * 60)
                y2 = 23 + int(math.sin(angle) * 11)
                pygame.draw.line(
                    ring, (*NS.PALETTE["ice_bright"], 180),
                    (x1, y1), (x2, y2), 1)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 70, y - 23 + 30))
        if active_skill:
            NS._ellipse(surface,
                        (*NS.PALETTE["ice_hot"], int(80 * pulse)),
                        (x - 55, y - 15 + 30, 110, 30), 1)

    def _draw_ice_wisps(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Mist beku + salju melayang (versi ringan; partikel hidup ada
        di lapisan FX — fungsi ini fallback canvas)."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        if NS._mist_cache is None:
            mist = pygame.Surface((140, 42), pygame.SRCALPHA)
            for radius in range(34, 3, -4):
                alpha = int((34 - radius) * 2.2)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*P["frost_dark"], min(255, alpha)),
                        (70 - radius * 2, 21 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            NS._mist_cache = mist
        strength = 1.4 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 70, cy - 10))
        for i, offset in enumerate((-16, 0, 16)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha > 0:
                NS._aacircle(surface, (*P["frost_dark"], alpha),
                             (sx, sy), 4)
                NS._aacircle(surface, (*P["ice_hot"], alpha),
                             (sx, sy - 3), 1)
        for i in range(3):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = phase * 0.5 + i * math.tau / 5.0
            r = 22 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9) - int(t * 8)
            alpha = int(210 * (1 - t * 0.5) * strength)
            NS._draw_snowflake(surface, sx, sy, 2,
                               max(0, min(255, alpha)),
                               rotate=phase + i)
        if trail:
            for i in range(3):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 130 - i * 25)
                NS._aacircle(surface, (*P["frost_mid"], alpha),
                             (sx, sy), max(2, 4 - i))

    # ===================================================================
    # ICE / SNOWFLAKE HELPERS (dipakai skill fallback)
    # ===================================================================
    def _draw_snowflake(surface, cx, cy, size=3, alpha=255, rotate=0):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        for i in range(6):
            angle = rotate + i * math.pi / 3
            ex = cx + int(math.cos(angle) * size)
            ey = cy + int(math.sin(angle) * size)
            NS._aaline(surface, (*P["ice_hot"], alpha), (cx, cy),
                       (ex, ey), 1)
            mx = cx + int(math.cos(angle) * (size - 1))
            my = cy + int(math.sin(angle) * (size - 1))
            t1 = angle + math.pi / 2
            t2 = angle - math.pi / 2
            NS._aaline(surface, (*P["ice_bright"], alpha), (mx, my),
                       (mx + int(math.cos(t1)), my + int(math.sin(t1))), 1)
            NS._aaline(surface, (*P["ice_bright"], alpha), (mx, my),
                       (mx + int(math.cos(t2)), my + int(math.sin(t2))), 1)
        NS._aacircle(surface, (*P["ice_pure"], alpha), (cx, cy), 1)

    def _draw_frost_crystal_spike(surface, cx, base_y, tip_y, width=4,
                                  alpha=255, phase=0):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        height = base_y - tip_y
        if height <= 0:
            return
        NS._poly(surface, (*P["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1), (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1)])
        NS._poly(surface, (*P["ice_darkest"], alpha), [
            (cx - width, base_y), (cx + width, base_y), (cx, tip_y)])
        for i, ck in enumerate(("ice_dark", "ice_mid", "ice_light",
                                "ice_bright")):
            shrink = (i + 1) * 0.15
            w = int(width * (1 - shrink))
            NS._poly(surface, (*P[ck], alpha), [
                (cx - w, base_y - 1), (cx + w, base_y - 1),
                (cx, tip_y + int(height * shrink * 0.2))])
        NS._aaline(surface, (*P["ice_hot"], alpha),
                   (cx, base_y - 2), (cx, tip_y + 2), 1)
        NS._aacircle(surface, (*P["ice_pure"], alpha), (cx, tip_y + 1), 1)

    # ===================================================================
    # SWING TRAIL (canvas fallback — histori posisi cakar)
    # ===================================================================
    def _draw_swing_trail(surface, boss, x, y, facing, progress):
        """Ribbon sapuan cakar dari histori posisi (fallback canvas)."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ph = NS._attack_phase(progress)
        if ph not in ("swing", "follow"):
            if hasattr(boss, "_aa_trail"):
                boss._aa_trail.clear()
            return
        if not hasattr(boss, "_aa_trail"):
            boss._aa_trail = []
        (_, _, hand, tip) = NS.arm_geometry(facing, "attack",
                                            getattr(boss, "pulse", 0.0),
                                            progress)
        boss._aa_trail.append((x + hand[0], y + hand[1],
                               x + tip[0], y + tip[1]))
        if len(boss._aa_trail) > 10:
            boss._aa_trail.pop(0)
        n = len(boss._aa_trail)
        if n < 2:
            return
        for i in range(n - 1):
            bx0, by0, tx0, ty0 = boss._aa_trail[i]
            bx1, by1, tx1, ty1 = boss._aa_trail[i + 1]
            k = i / max(1, n - 1)
            a = int(120 * (0.3 + 0.7 * k))
            ix0 = bx0 + (tx0 - bx0) * 0.3
            iy0 = by0 + (ty0 - by0) * 0.3
            ix1 = bx1 + (tx1 - bx1) * 0.3
            iy1 = by1 + (ty1 - by1) * 0.3
            NS._poly(surface, (*P["ice_mid"], a),
                     [(ix0, iy0), (ix1, iy1), (tx1, ty1), (tx0, ty0)])
            NS._aaline(surface, (*P["ice_hot"], int(a * 0.9)),
                       (tx0, ty0), (tx1, ty1), 1)

    # ===================================================================
    # CAST FLASH (canvas fallback)
    # ===================================================================
    def _draw_cast_flash(surface, x, y, facing, progress):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        if progress < 0.32 or progress > 0.62:
            return
        t = (progress - 0.32) / 0.30
        intensity = math.sin(t * math.pi)
        (_, _, hand, tip) = NS.arm_geometry(facing, "attack",
                                            0.0, progress)
        fx = x + tip[0]
        fy = y + tip[1]
        alpha = int(220 * intensity)
        radius = int(5 + intensity * 11)
        NS._aacircle(surface, (*P["ice_dark"], 140 * intensity // 1),
                     (fx, fy), radius + 4)
        NS._aacircle(surface, (*P["ice_mid"], alpha), (fx, fy), radius + 2)
        NS._aacircle(surface, (*P["ice_bright"], alpha), (fx, fy), radius)
        NS._aacircle(surface, (*P["ice_hot"], alpha), (fx, fy),
                     max(1, radius - 2))
        NS._aacircle(surface, (*P["ice_pure"], alpha), (fx, fy),
                     max(1, radius - 4))
        for i in range(5):
            ang = i * math.tau / 5 + progress * 6.0
            ex = fx + int(math.cos(ang) * radius * 1.5)
            ey = fy + int(math.sin(ang) * radius * 1.5)
            NS._draw_snowflake(surface, ex, ey, 2, alpha,
                               rotate=progress * 5)

    # ===================================================================
    # SKILL Q: ICE VORTEX (ground + foreground, canvas fallback)
    # ===================================================================
    def _draw_ice_vortex_ground(surface, boss, x, y, timer, phase):
        """Riak tanah di bawah vortex."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i in range(4):
            r = int(15 + i * 12 + progress * 20
                    + math.sin(phase * 2 + i) * 3)
            NS._ellipse(surface, (*P["ice_dark"], int(150 * pulse)),
                        (tx - r, ty - r // 3, r * 2, r // 1.5), 2)
            NS._ellipse(surface, (*P["ice_mid"], int(100 * pulse)),
                        (tx - r + 3, ty - r // 3 + 2, r * 2 - 6,
                         r // 1.5 - 4), 1)

    def _draw_ice_vortex(surface, boss, x, y, timer, phase):
        """Tornado es berputar di target (fallback canvas)."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            return
        if progress < 0.5:
            height = int(60 * (progress - 0.15) / 0.35)
        else:
            height = int(60 * (1 - (progress - 0.85) / 0.15)) \
                if progress > 0.85 else 60
        if height <= 0:
            return
        max_width = 28
        ring_count = height // 3
        for i in range(ring_count):
            h_ratio = i / max(1, ring_count)
            y_offset = -int(h_ratio * height)
            width = int(max_width * (1 - h_ratio * 0.4))
            rotation = phase * 4 + h_ratio * 8
            for j in range(8):
                a1 = rotation + j * math.pi / 4
                a2 = a1 + 0.5
                x1 = tx + int(math.cos(a1) * width)
                y1 = ty + y_offset + int(math.sin(a1) * width * 0.3)
                x2 = tx + int(math.cos(a2) * width)
                y2 = ty + y_offset + int(math.sin(a2) * width * 0.3)
                alpha = int(200 * (1 - h_ratio * 0.3))
                NS._aaline(surface, (*P["ice_dark"], alpha),
                           (x1, y1), (x2, y2), 3)
                NS._aaline(surface, (*P["ice_bright"], alpha),
                           (x1, y1), (x2, y2), 1)
            for j in range(3):
                sa = rotation + j * math.tau / 3
                sx = tx + int(math.cos(sa) * width)
                sy = ty + y_offset + int(math.sin(sa) * width * 0.3)
                NS._aacircle(surface, (*P["ice_hot"], 220), (sx, sy), 3)
                NS._aacircle(surface, (*P["ice_pure"], 250), (sx, sy), 1)
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            r = max_width - 3
            sx = tx + int(math.cos(angle) * r)
            sy = ty - height // 2 + int(math.sin(angle) * 15)
            NS._draw_snowflake(surface, sx, sy, 3, 230,
                               rotate=phase * 3)
        NS._ellipse(surface, (*P["ice_bright"], 180),
                    (tx - max_width, ty - max_width // 3,
                     max_width * 2, max_width // 1.5), 2)

    # ===================================================================
    # SKILL R: COLD FEET (ground telegraph + erupsi, canvas fallback)
    # ===================================================================
    def _draw_cold_feet_ground(surface, boss, x, y, timer, phase):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        if progress < 0.4:
            radius = int(40 + progress * 20)
            NS._ellipse(surface, (*P["ice_dark"], int(200 * pulse)),
                        (tx - radius, ty - radius // 3, radius * 2,
                         radius // 1.5), 3)
            NS._ellipse(surface, (*P["ice_mid"], int(150 * pulse)),
                        (tx - radius + 4, ty - radius // 3 + 2,
                         radius * 2 - 8, radius // 1.5 - 4), 2)

    def _draw_cold_feet_spikes(surface, boss, x, y, timer, phase):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                r = 60 * (1 - progress / 0.3)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                NS._draw_snowflake(surface, sx, sy, 3, 200,
                                   rotate=phase * 4)
            return
        erupt_t = min(1.0, (progress - 0.3) / 0.3)
        num_spikes = 12
        ring_r = 50
        for i in range(num_spikes):
            angle = i * math.tau / num_spikes
            spike_x = tx + int(math.cos(angle) * ring_r)
            spike_y = ty + int(math.sin(angle) * ring_r * 0.5)
            spike_h = int(25 * erupt_t)
            NS._draw_frost_crystal_spike(surface, spike_x, spike_y,
                                         spike_y - spike_h, 3, 240, phase)
        center_h = int(35 * erupt_t)
        NS._draw_frost_crystal_spike(surface, tx, ty, ty - center_h, 5,
                                     250, phase)
        for i in range(num_spikes):
            angle = (i + 0.5) * math.tau / num_spikes
            spike_x = tx + int(math.cos(angle) * (ring_r * 0.6))
            spike_y = ty + int(math.sin(angle) * (ring_r * 0.6) * 0.5)
            spike_h = int(18 * erupt_t)
            NS._draw_frost_crystal_spike(surface, spike_x, spike_y,
                                         spike_y - spike_h, 2, 230, phase)
        for i in range(10):
            angle = i * math.pi / 5 + phase * 2
            r = ring_r + int(math.sin(phase * 3 + i) * 10)
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.5) - int(erupt_t * 15)
            NS._draw_snowflake(surface, sx, sy, 2, int(230 * erupt_t),
                               rotate=phase * 3 + i)
        for i in range(5):
            angle = phase * 0.5 + i * math.tau / 5
            r = ring_r + 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.5)
            NS._aacircle(surface, (*P["frost_light"], int(120 * erupt_t)),
                         (sx, sy), 8)

    # ===================================================================
    # SKILL PROJECTILE TRIGGER (durasi HARUS == AI: w=45, e=50)
    # ===================================================================
    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        """Spawn proyektil skill pada titik progress yang tepat."""
        NS = _NS_ancient_apparition
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        tx, ty = NS._target_position(boss, x, y)

        if active_skill == "e":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss,
                                                      "_aa_e_spawned",
                                                      False):
                NS._spawn_ice_bolt(boss, x + 25 * boss.direction, y - 5,
                                   tx, ty)
                boss._aa_e_spawned = True
            if progress > 0.7:
                boss._aa_e_spawned = False

        elif active_skill == "w":
            duration = 45
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.3 < progress < 0.4 and not getattr(boss,
                                                    "_aa_w_spawned",
                                                    False):
                NS._spawn_frost_beam(boss, x + 25 * boss.direction, y - 5,
                                     tx, ty)
                boss._aa_w_spawned = True
            if progress > 0.7:
                boss._aa_w_spawned = False

    # ===================================================================
    # LAPISAN FX HIDUP (heroes/ancient_apparition_fx)
    # ===================================================================
    _LIVE_MOD = None

    def _live_module():
        """Muat heroes.ancient_apparition_fx sekali; None kalau gagal."""
        NS = _NS_ancient_apparition
        if NS._LIVE_MOD is None:
            try:
                from heroes import ancient_apparition_fx as mod
                NS._LIVE_MOD = mod if getattr(
                    mod, "APPARITION_FX_ENABLED", True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup bisa dipakai (dipakai tooling)."""
        return _NS_ancient_apparition._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Return (mod, owned): mod None = tanpa lapisan hidup.

        want_draw True pada jalur BOSS (draw tiap frame, tanpa cache).
        Jalur HERO penggambaran dilakukan heroes/__init__.py; di sini
        hanya dipasang penanda agar renderer melewati salinan canvas.
        """
        NS = _NS_ancient_apparition
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_apparition(surface, boss, x, y):
        NS = _NS_ancient_apparition
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        # Deteksi gerak: preferensi cache direktur FX (diperbarui tiap
        # frame).  Fallback _detect_moving untuk jalur tanpa lapisan
        # hidup — jalur hero hanya memanggil renderer saat cache miss,
        # jadi sampling posisi di sini tidak beraturan.
        NS._detect_moving(boss)
        cached_moving = getattr(boss, "_moving_cached", None)
        moving = bool(cached_moving) if cached_moving is not None \
            else bool(getattr(boss, "_aa_speed", 0.0) > 0.3)
        NS._update_attack_anim(boss)

        attacking = (getattr(boss, "_aa_attack_active", False)
                     or getattr(boss, "timer", 0)
                     > getattr(boss, "attack_cooldown", 50) - 15)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = (hasattr(boss, "_render_scale") and not portrait)

        # ── lapisan FX hidup: BOSS digambar tiap frame -> draw di sini;
        #    HERO digambar heroes/__init__ (di luar cache sprite) ──
        live, owned = NS._live_fx(boss, surface, x, y,
                                  want_draw=not hero_lane, portrait=portrait)

        state = NS._resolve_state(boss, moving)
        action = state if state != "death" else "idle"
        ap = getattr(boss, "_aa_attack_progress", 0.0) \
            if attacking else 0.0

        # ═══ 1. GROUND FX (belakang segalanya) ═══
        if not portrait:
            NS._draw_frost_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_frost(surface, x, y + 22, pulse, active_skill)
            NS._draw_ice_wisps(surface, x, y + 34, pulse,
                               trail=(state in ("walk", "run")),
                               facing=facing,
                               intense=bool(active_skill) or attacking)
            if not owned:
                if active_skill == "q":
                    NS._draw_ice_vortex_ground(surface, boss, x, y,
                                               skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_cold_feet_ground(surface, boss, x, y,
                                              skill_timer, pulse)

        # ═══ 2. SHADOW (di luar flash buffer — kontrak) ═══
        hover = 2 if state.startswith("cast_r") else 0
        NS._draw_shadow(surface, x, y + 52, lift=hover)

        # ═══ 3. KARAKTER (ke flash buffer saat hurt) ═══
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240),
                                               pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        NS._draw_aa_body(_tgt, _tx, _ty, facing, pulse, action, ap)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(
                setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ═══ 4. ATTACK FX + SKILL FX + PROJECTILE (fallback canvas) ═══
        if not portrait and not owned:
            if attacking and not hero_lane:
                NS._draw_swing_trail(surface, boss, x, y, facing, ap)
                NS._draw_cast_flash(surface, x, y, facing, ap)
            NS._handle_skill_projectiles(boss, x, y, active_skill,
                                         skill_timer)
            NS._manage_projectiles(boss, surface, pulse)
            if active_skill == "q":
                NS._draw_ice_vortex(surface, boss, x, y, skill_timer,
                                    pulse)
            elif active_skill == "r":
                NS._draw_cold_feet_spikes(surface, boss, x, y,
                                          skill_timer, pulse)

        # ═══ 5. LAPISAN HIDUP (depan) + DEBUG ═══
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_aa_debug(surface, boss, x, y, action, owned)

    # ===================================================================
    # DEBUG OVERLAY  (DEBUG_CHARACTER = True)
    # ===================================================================
    def _draw_aa_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state, FPS — murni baca state."""
        NS = _NS_ancient_apparition
        # hurtbox = radius unit
        r = max(8, int(getattr(boss, "radius", 30)))
        pygame.draw.circle(surface, (80, 170, 255), (int(x), int(y)), r, 1)
        # jangkauan serangan
        rng = max(10, int(getattr(boss, "range", 150)))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60), (int(x), int(y)),
                         (int(x) + rng * f, int(y)), 1)
        # hitbox ayunan (jendela aktif)
        ap = float(getattr(boss, "_aa_attack_progress", 0.0) or 0.0)
        if getattr(boss, "_aa_attack_active", False) and \
                NS.ATK_PHASES["swing"][0] <= ap <= 0.62:
            hb = pygame.Rect(int(x) + (14 if f > 0 else -58),
                             int(y) - 30, 44, 36)
            pygame.draw.rect(surface, (255, 70, 70), hb, 2)
        # tabrakan proyektil lapisan hidup
        if owned:
            try:
                mod = NS._LIVE_MOD
                for p in mod.projectiles_for(boss):
                    pr = max(3, int(p.hit_radius))
                    pygame.draw.circle(surface, (255, 120, 255),
                                       (int(p.position.x),
                                        int(p.position.y)), pr, 1)
            except Exception:
                pass
        try:
            font = pygame.font.Font(None, 15)
        except Exception:
            return
        try:
            fps = int(pygame.time.Clock().get_fps())
        except Exception:
            fps = 0
        lines = [
            "AA %s ap=%.2f" % (action, ap),
            "skill %s t=%d" % (getattr(boss, "active_skill", None),
                               int(getattr(boss, "active_skill_timer", 0))),
            "owned=%d fps=%d" % (1 if owned else 0, fps),
        ]
        for i, txt in enumerate(lines):
            img = font.render(txt, True, (200, 245, 255))
            surface.blit(img, (x - 56, y - 108 + i * 13))

    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_ancient_apparition.draw_apparition(surface, boss, x, y)

    def draw_ancient_apparition(surface, boss, x, y):
        """Entry point resmi untuk Ancient Apparition."""
        _NS_ancient_apparition.draw_apparition(surface, boss, x, y)


def tilt_head(phase):
    """Goyangan kepala ringan (dipakai _masterwork_finish)."""
    return math.sin(phase * 0.8) * 1.0


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_varkul(surface, boss, x, y):
    """Entry point varkul."""
    return _NS_varkul.draw_varkul(surface, boss, x, y)

def draw_xerathis(surface, boss, x, y):
    """Entry point xerathis."""
    return _NS_xerathis.draw_xerathis(surface, boss, x, y)

def draw_nyzrak(surface, boss, x, y):
    """Entry point nyzrak."""
    return _NS_nyzrak.draw_nyzrak(surface, boss, x, y)

def draw_ancient_apparition(surface, boss, x, y):
    """Entry point ancient_apparition."""
    return _NS_ancient_apparition.draw_ancient_apparition(surface, boss, x, y)
