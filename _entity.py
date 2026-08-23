"""
_entity.py - semua entity (digabung dari 5 file)

  tower.py
  castle.py
  hero.py
  minion.py        (blok duplikat render_cache/performance di
                    ekornya DIHAPUS - identik, pakai versi kanonik)
  ai_player.py
"""
import pygame
import math
import random
from _core import *
from _system import SoundManager, FrustumCuller, query_enemies_in_range


# ====================================================================
# tower.py
# ====================================================================

# TOWER.PY - 4 Types + 6 Levels System
# ================================

import pygame
import math

try:
    from _system import SoundManager
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False


# Cache sprite peluru: (tipe, tim, arah_16_langkah) -> (surface, ax, ay)
_BULLET_SPRITE_CACHE = {}


class _DummyBulletTarget:
    __slots__ = ("x", "y", "alive")

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.alive = True


def _get_bullet_sprite(bullet):
    """Sprite peluru dari cache (render sekali, blit tiap frame)."""
    angle_k = 0
    if bullet.bullet_type == "normal":
        tgt = bullet.target
        if tgt is not None and getattr(tgt, "alive", True):
            ang = math.atan2(tgt.y - bullet.y, tgt.x - bullet.x)
        else:
            ang = 0.0
        angle_k = (int(ang / (math.pi * 2) * 16) + 16) % 16

    key = (bullet.bullet_type, bullet.team, angle_k)
    ent = _BULLET_SPRITE_CACHE.get(key)
    if ent is not None:
        return ent

    canvas = pygame.Surface((48, 48), pygame.SRCALPHA)
    cx = cy = 24
    bt = bullet.bullet_type
    if bt == "normal":
        saved = bullet.target
        bullet.target = _DummyBulletTarget(
            bullet.x + math.cos(angle_k * math.pi / 8) * 10,
            bullet.y + math.sin(angle_k * math.pi / 8) * 10)
        try:
            bullet._draw_hd_arrow(canvas, cx, cy)
        finally:
            bullet.target = saved
    elif bt == "cannon":
        pygame.draw.circle(canvas, (60, 60, 60), (cx, cy), 6)
        pygame.draw.circle(canvas, (100, 100, 100), (cx - 1, cy - 1), 4)
        pygame.draw.circle(canvas, (150, 150, 150), (cx - 2, cy - 2), 2)
        pygame.draw.circle(canvas, (255, 200, 50), (cx + 3, cy - 3), 2)
        pygame.draw.circle(canvas, (255, 255, 200), (cx + 3, cy - 3), 1)
    elif bt == "ice":
        pygame.draw.polygon(canvas, (150, 220, 255), [
            (cx, cy - 5), (cx + 3, cy), (cx, cy + 5), (cx - 3, cy)])
        pygame.draw.polygon(canvas, (200, 240, 255), [
            (cx, cy - 4), (cx + 2, cy), (cx, cy + 4), (cx - 2, cy)])
        pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 1)
    elif bt == "mage":
        color = (180, 80, 220)
        for r in range(6, 0, -1):
            alpha = 200 - r * 20
            if alpha > 0:
                pygame.draw.circle(canvas, color + (alpha,), (cx, cy), r)
        pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 2)
    else:
        pygame.draw.circle(canvas, bullet.color
                           if hasattr(bullet, "color") else (200, 200, 200),
                           (cx, cy), 3)

    rect = canvas.get_bounding_rect(min_alpha=8)
    if rect.width <= 0:
        rect = pygame.Rect(cx - 3, cy - 3, 6, 6)
    sub = canvas.subsurface(rect).copy()
    ent = (sub, cx - rect.x, cy - rect.y)
    if len(_BULLET_SPRITE_CACHE) > 200:
        _BULLET_SPRITE_CACHE.pop(next(iter(_BULLET_SPRITE_CACHE)))
    _BULLET_SPRITE_CACHE[key] = ent
    return ent


class Bullet:
    """Standard bullet (archer & basic)"""

    def __init__(self, x, y, target, damage, team, bullet_type="normal",
                 special_data=None):
        self.x = float(x)
        self.y = float(y)
        self.target = target
        self.damage = damage
        self.team = team
        self.speed = BULLET_SPEED
        self.active = True
        self.bullet_type = bullet_type
        self.special_data = special_data or {}

    def update(self, all_units=None):
        if not self.active:
            return
        if not self.target or not self.target.alive:
            self.active = False
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed + BULLET_RADIUS:
            self._on_hit(all_units)
            self.active = False
        else:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def _on_hit(self, all_units):
        """Apply damage & special effects on hit"""
        if not self.target or not self.target.alive:
            return

        self.target.take_damage(self.damage, self.team)

        # ─── SPECIAL EFFECTS ───
        if self.bullet_type == "cannon":
            # Splash damage + BURNING (debuff burn berlaku ke target
            # utama DAN semua unit yang kena splash)
            splash_radius = self.special_data.get('splash', 40)
            burn_dps = self.special_data.get('burn_dps', 0)
            burn_duration = self.special_data.get('burn_duration', 0)

            if burn_dps > 0 and hasattr(self.target, 'apply_debuff'):
                self.target.apply_debuff('burn', burn_dps, burn_duration,
                                         source_team=self.team)

            if all_units:
                for u in all_units:
                    if u == self.target:
                        continue
                    if u.team == self.team or not u.alive:
                        continue
                    d = math.hypot(u.x - self.target.x, u.y - self.target.y)
                    if d <= splash_radius:
                        u.take_damage(int(self.damage * 0.6), self.team)
                        if burn_dps > 0 and hasattr(u, 'apply_debuff'):
                            u.apply_debuff('burn', burn_dps, burn_duration,
                                           source_team=self.team)

        elif self.bullet_type == "ice":
            # Apply slow gerak (lama) + slow ATTACK SPEED (baru)
            slow_amount = self.special_data.get('slow', 0.2)
            slow_duration = self.special_data.get('slow_duration', 90)
            atk_slow = self.special_data.get('atk_slow', 0)
            if hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(slow_amount, slow_duration)
            if atk_slow > 0 and hasattr(self.target, 'apply_debuff'):
                self.target.apply_debuff('atk_slow', atk_slow,
                                         slow_duration)

            # AOE slow di level 6 (gerak + attack speed)
            if 'slow_aoe' in self.special_data and all_units:
                aoe = self.special_data['slow_aoe']
                for u in all_units:
                    if u == self.target or u.team == self.team or not u.alive:
                        continue
                    d = math.hypot(u.x - self.target.x,
                                   u.y - self.target.y)
                    if d <= aoe:
                        if hasattr(u, 'apply_slow'):
                            u.apply_slow(slow_amount, slow_duration)
                        if atk_slow > 0 and hasattr(u, 'apply_debuff'):
                            u.apply_debuff('atk_slow', atk_slow,
                                           slow_duration)

        elif self.bullet_type == "mage":
            # Debuff SKILL DAMAGE + ANTI-HEAL ke target (tiap bolt chain
            # adalah Bullet terpisah, jadi semua target chain kena).
            skill_down = self.special_data.get('skill_down', 0)
            anti_heal = self.special_data.get('anti_heal', 0)
            debuff_duration = self.special_data.get('debuff_duration', 120)
            if hasattr(self.target, 'apply_debuff'):
                if skill_down > 0:
                    self.target.apply_debuff('skill_down', skill_down,
                                             debuff_duration)
                if anti_heal > 0:
                    self.target.apply_debuff('anti_heal', anti_heal,
                                             debuff_duration)

        # Sound impact. Dulu hanya tim biru dan volume 0,25 (nyaris
        # tak terdengar). Sekarang SEMUA tim berbunyi dan lebih keras
        # supaya "kena panah" jelas terdengar.
        if SOUND_ENABLED:
            SoundManager().play('bullet_hit', volume_mult=0.55)

    def draw(self, surface):
        if not self.active:
            return

        # Sprite peluru DI-CACHE (16 arah untuk panah, statis untuk
        # tipe lain). Sebelumnya tiap peluru render belasan draw call
        # per frame - dengan 80+ peluru di late game itu >1 ms/frame.
        ent = _get_bullet_sprite(self)
        surface.blit(ent[0],
                     (int(self.x - ent[1]), int(self.y - ent[2])))

    def _draw_hd_arrow(self, surface, x, y):
        """HD Arrow projectile dengan trail"""
        # Calculate arrow angle
        if self.target and self.target.alive:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                angle = math.atan2(dy, dx)
            else:
                angle = 0
        else:
            angle = 0

        # Colors berdasarkan team
        if self.team == "blue":
            shaft_dark = (85, 55, 25)
            shaft_light = (155, 110, 60)
            feather_dark = (140, 30, 30)
            feather_mid = (200, 60, 60)
            feather_light = (240, 100, 100)
            head_dark = (60, 60, 70)
            head_mid = (140, 140, 155)
            head_light = (210, 210, 225)
            head_shine = (255, 255, 255)
        else:
            shaft_dark = (60, 30, 15)
            shaft_light = (120, 75, 40)
            feather_dark = (80, 15, 15)
            feather_mid = (140, 30, 30)
            feather_light = (200, 60, 60)
            head_dark = (40, 30, 30)
            head_mid = (100, 80, 80)
            head_light = (170, 145, 145)
            head_shine = (240, 220, 220)

        arrow_length = 14

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        perp_cos = -sin_a
        perp_sin = cos_a

        tail_x = x - cos_a * arrow_length // 2
        tail_y = y - sin_a * arrow_length // 2

        head_x = x + cos_a * arrow_length // 2
        head_y = y + sin_a * arrow_length // 2

        # ─── TRAIL ───
        for i in range(4):
            trail_offset = (i + 1) * 3
            trail_x = int(x - cos_a * trail_offset)
            trail_y = int(y - sin_a * trail_offset)
            trail_alpha = 100 - i * 25

            if trail_alpha > 0:
                trail_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf,
                                   (*shaft_light, trail_alpha),
                                   (3, 3), 2)
                surface.blit(trail_surf, (trail_x - 3, trail_y - 3))

        # ─── SHAFT ───
        shaft_start = (int(tail_x + cos_a * 2), int(tail_y + sin_a * 2))
        shaft_end = (int(head_x - cos_a * 2), int(head_y - sin_a * 2))

        pygame.draw.line(surface, (20, 15, 10),
                         shaft_start, shaft_end, 3)
        pygame.draw.line(surface, shaft_dark,
                         shaft_start, shaft_end, 2)
        shaft_hi_start = (int(shaft_start[0] + perp_cos * 0.5),
                          int(shaft_start[1] + perp_sin * 0.5))
        shaft_hi_end = (int(shaft_end[0] + perp_cos * 0.5),
                        int(shaft_end[1] + perp_sin * 0.5))
        pygame.draw.line(surface, shaft_light,
                         shaft_hi_start, shaft_hi_end, 1)

        # ─── ARROWHEAD ───
        head_tip_x = int(x + cos_a * arrow_length // 2 + cos_a * 3)
        head_tip_y = int(y + sin_a * arrow_length // 2 + sin_a * 3)

        head_base_x = int(x + cos_a * arrow_length // 2 - cos_a * 2)
        head_base_y = int(y + sin_a * arrow_length // 2 - sin_a * 2)

        base_top_x = int(head_base_x + perp_cos * 2.5)
        base_top_y = int(head_base_y + perp_sin * 2.5)
        base_bot_x = int(head_base_x - perp_cos * 2.5)
        base_bot_y = int(head_base_y - perp_sin * 2.5)

        pygame.draw.polygon(surface, (10, 8, 12), [
            (base_top_x, base_top_y),
            (head_tip_x, head_tip_y),
            (base_bot_x, base_bot_y),
        ])

        pygame.draw.polygon(surface, head_dark, [
            (base_top_x, base_top_y),
            (head_tip_x, head_tip_y),
            (base_bot_x, base_bot_y),
        ])

        mid_top_x = int(head_base_x + perp_cos * 1.5)
        mid_top_y = int(head_base_y + perp_sin * 1.5)
        pygame.draw.polygon(surface, head_mid, [
            (mid_top_x, mid_top_y),
            (head_tip_x, head_tip_y),
            (int(head_base_x + perp_cos * 0.5),
             int(head_base_y + perp_sin * 0.5)),
        ])

        pygame.draw.polygon(surface, head_light, [
            (mid_top_x, mid_top_y),
            (int(head_tip_x - cos_a * 2),
             int(head_tip_y - sin_a * 2)),
            (int(head_base_x + perp_cos * 1),
             int(head_base_y + perp_sin * 1)),
        ])

        pygame.draw.rect(surface, head_shine,
                         (head_tip_x - 1, head_tip_y - 1, 1, 1))

        # ─── FLETCHING ───
        fletching_len = 4

        # Left feather
        feather_l_tip_x = int(tail_x + perp_cos * 3 - cos_a * fletching_len)
        feather_l_tip_y = int(tail_y + perp_sin * 3 - sin_a * fletching_len)

        pygame.draw.polygon(surface, (30, 5, 5), [
            (int(tail_x + perp_cos * 0.5), int(tail_y + perp_sin * 0.5)),
            (feather_l_tip_x, feather_l_tip_y),
            (int(tail_x - cos_a * 3 + perp_cos * 1),
             int(tail_y - sin_a * 3 + perp_sin * 1)),
        ])
        pygame.draw.polygon(surface, feather_dark, [
            (int(tail_x + perp_cos * 0.5), int(tail_y + perp_sin * 0.5)),
            (feather_l_tip_x, feather_l_tip_y),
            (int(tail_x - cos_a * 2 + perp_cos * 0.5),
             int(tail_y - sin_a * 2 + perp_sin * 0.5)),
        ])
        pygame.draw.polygon(surface, feather_mid, [
            (int(tail_x + perp_cos * 0.5), int(tail_y + perp_sin * 0.5)),
            (int(feather_l_tip_x - cos_a * 0.5),
             int(feather_l_tip_y - sin_a * 0.5)),
            (int(tail_x - cos_a * 1),
             int(tail_y - sin_a * 1)),
        ])

        # Right feather
        feather_r_tip_x = int(tail_x - perp_cos * 3 - cos_a * fletching_len)
        feather_r_tip_y = int(tail_y - perp_sin * 3 - sin_a * fletching_len)

        pygame.draw.polygon(surface, (30, 5, 5), [
            (int(tail_x - perp_cos * 0.5), int(tail_y - perp_sin * 0.5)),
            (feather_r_tip_x, feather_r_tip_y),
            (int(tail_x - cos_a * 3 - perp_cos * 1),
             int(tail_y - sin_a * 3 - perp_sin * 1)),
        ])
        pygame.draw.polygon(surface, feather_dark, [
            (int(tail_x - perp_cos * 0.5), int(tail_y - perp_sin * 0.5)),
            (feather_r_tip_x, feather_r_tip_y),
            (int(tail_x - cos_a * 2 - perp_cos * 0.5),
             int(tail_y - sin_a * 2 - perp_sin * 0.5)),
        ])
        pygame.draw.polygon(surface, feather_mid, [
            (int(tail_x - perp_cos * 0.5), int(tail_y - perp_sin * 0.5)),
            (int(feather_r_tip_x - cos_a * 0.5),
             int(feather_r_tip_y - sin_a * 0.5)),
            (int(tail_x - cos_a * 1),
             int(tail_y - sin_a * 1)),
        ])

        # Highlight on feathers
        pygame.draw.rect(surface, feather_light,
                         (int(tail_x + perp_cos * 1) - 1,
                          int(tail_y + perp_sin * 1) - 1, 1, 1))


# ═══════════════════════════════════════════════════════
# TOWER CLASS
# ═══════════════════════════════════════════════════════

# Cache sprite body tower (statis per tipe/team/level/arah/state).
# Badan tower di-render penuh tiap frame dulu = mahal saat 10+ tower.
_TOWER_SPRITE_CACHE = {}


def _build_armor_crest(size, base_color, fill_ratio, bright):
    """Bangun sprite ARMOR CREST kecil (perisai heraldik) sebagai
    indikator shield — pengganti gelembung transparan yang jelek.

    size       : tinggi crest dalam pixel
    base_color : warna tim (biru/merah)
    fill_ratio : isi shield 0..1 (crest terisi dari bawah ke atas)
    bright     : True saat regen flash (crest menyala lebih terang)
    """
    w = int(size * 0.82)
    h = size
    surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    ox, oy = 2, 2

    # Outline crest: atas rata, sisi lurus, meruncing ke bawah
    pts = [
        (ox, oy),                      # kiri-atas
        (ox + w, oy),                  # kanan-atas
        (ox + w, oy + int(h * 0.55)),  # kanan-tengah
        (ox + w // 2, oy + h),         # ujung bawah
        (ox, oy + int(h * 0.55)),      # kiri-tengah
    ]

    dark = tuple(max(0, c - 90) for c in base_color)
    lite = tuple(min(255, c + (90 if bright else 40)) for c in base_color)

    # Plat dasar (gelap = bagian shield yang habis)
    pygame.draw.polygon(surf, (*dark, 235), pts)

    # Isi shield dari bawah sesuai ratio (clip pakai subsurface-rect)
    if fill_ratio > 0:
        fill_h = max(1, int(h * fill_ratio))
        clip = pygame.Rect(0, oy + h - fill_h, w + 4, fill_h + 2)
        surf.set_clip(clip)
        pygame.draw.polygon(surf, (*base_color, 245), pts)
        surf.set_clip(None)

    # Emblem: garis silang kecil di tengah crest
    cx0 = ox + w // 2
    cy0 = oy + int(h * 0.42)
    arm = max(2, size // 6)
    pygame.draw.line(surf, (*lite, 230), (cx0 - arm, cy0), (cx0 + arm, cy0), 2)
    pygame.draw.line(surf, (*lite, 230), (cx0, cy0 - arm), (cx0, cy0 + arm), 2)

    # Border crest
    pygame.draw.polygon(surf, (*lite, 255), pts, 2)
    return surf


def _draw_armor_crest(surface, cx, cy, size, base_color, fill_ratio,
                      bright=False):
    """Gambar armor crest kecil berpusat di (cx, cy). Di-cache per
    (size, warna, bucket ratio, bright) — jauh lebih murah daripada
    gelembung alpha lama."""
    ratio_b = min(10, max(0, int(fill_ratio * 10 + 0.5)))  # bucket 0..10
    key = ("armor_crest", size, base_color, ratio_b, bool(bright))
    crest = _TOWER_SPRITE_CACHE.get(key)
    if crest is None:
        crest = _build_armor_crest(size, base_color, ratio_b / 10.0, bright)
        if len(_TOWER_SPRITE_CACHE) > 500:
            _TOWER_SPRITE_CACHE.pop(next(iter(_TOWER_SPRITE_CACHE)))
        _TOWER_SPRITE_CACHE[key] = crest
    surface.blit(crest, (int(cx) - crest.get_width() // 2,
                         int(cy) - crest.get_height() // 2))


class Tower:
    def __init__(self, x, y, team, tower_kind="outer", lane=None):
        self.x = x
        self.y = y
        self.team = team
        self.lane = lane

        self.tower_type = "archer"
        self.level = 1
        self.is_player_built = (team == "blue")

        self._apply_level_stats()

        self.timer = 0
        self.bullets = []
        self.target = None
        self.alive = True
        self.selected = False
        self.angle = 0
        self.kills = 0
        self.gold_reward = 150 if tower_kind == "inner" else 100

        self.upgrade_flash = 0

        self.archer_offset_y = -30
        self.shoot_flash_timer = 0

        # ═══ Shield & Regen ═══
        self.no_damage_timer = 0
        self.shield_regen_flash = 0
        self.hp_regen_flash = 0
        # ═══ REGEN SHIELD (fitur berbayar) ═══
        # False default; aktif setelah pemain/AI membayar
        # (Tower.activate_regen_shield()). Saat aktif, shield regen.
        self.regen_shield_active = False

    def _apply_level_stats(self):
        """Apply stats berdasarkan tower_type & level"""
        levels = TOWER_UPGRADE_PATHS[self.tower_type]

        if self.level not in levels:
            if self.tower_type == "archer":
                stats = ARCHER_LEVELS[self.level]
            else:
                stats = ARCHER_LEVELS[1]
        else:
            stats = levels[self.level]

        old_max_hp = getattr(self, 'max_hp', 0)

        # Apply HP multiplier
        base_hp = stats["hp"]
        self.max_hp = int(base_hp * TOWER_HP_MULTIPLIER)
        self.damage = stats["damage"]
        self.range = stats["range"]
        self.attack_cooldown = stats["cd"]

        # HP: fresh HP saat level up
        self.hp = self.max_hp

        # Shield stats
        self.shield_max = int(self.max_hp * TOWER_SHIELD_HP_RATIO)
        self.shield = self.shield_max

        # Special abilities
        self.splash = stats.get("splash", 0)
        self.slow = stats.get("slow", 0)
        self.slow_duration = stats.get("slow_duration", 0)
        self.slow_aoe = stats.get("slow_aoe", 0)
        self.chain = stats.get("chain", 1)
        self.double_shot = stats.get("double_shot", False)

        # ═══ DEBUFF BARU (berlaku untuk pemain & AI enemy) ═══
        # Ice: debuff attack speed. Mage: skill damage down + anti-heal.
        # Cannon: burning (damage over time). Nilainya diskala per level
        # di tabel CANNON/ICE/MAGE_LEVELS (_core.py).
        self.atk_slow = stats.get("atk_slow", 0)
        self.skill_down = stats.get("skill_down", 0)
        self.anti_heal = stats.get("anti_heal", 0)
        self.debuff_duration = stats.get("debuff_duration", 0)
        self.burn_dps = stats.get("burn_dps", 0)
        self.burn_duration = stats.get("burn_duration", 0)

        # Colors
        colors = TOWER_TYPE_COLORS[self.tower_type]
        self.color = colors["main"]
        self.color_dark = colors["dark"]

        type_names = {"archer": "Archer", "cannon": "Cannon",
                      "ice": "Ice", "mage": "Mage"}
        self.name = f"{type_names[self.tower_type]}"

        # Archer offset
        if self.tower_type == "archer":
            self.archer_offset_y = -(38 + self.level * 2)
        elif self.tower_type == "cannon":
            self.archer_offset_y = 0
        elif self.tower_type == "ice":
            self.archer_offset_y = -(28 + self.level * 2)
        elif self.tower_type == "mage":
            self.archer_offset_y = -(30 + self.level * 2)

    def can_upgrade(self):
        return self.level < TOWER_MAX_LEVEL

    def upgrade_cost(self, target_type=None):
        if not self.can_upgrade():
            return 0

        next_level = self.level + 1

        if self.level == 1 and target_type:
            path = TOWER_UPGRADE_PATHS[target_type]
            return path[next_level]["cost"]
        else:
            path = TOWER_UPGRADE_PATHS[self.tower_type]
            return path[next_level]["cost"]

    def upgrade(self, target_type=None):
        if not self.can_upgrade():
            return False

        if self.level == 1:
            if target_type is None:
                return False
            if target_type not in TOWER_UPGRADE_PATHS:
                return False
            self.tower_type = target_type

        self.level += 1
        self._apply_level_stats()
        self.upgrade_flash = 30

        return True

    def sell_value(self):
        if not self.is_player_built:
            return 0

        total = 0
        path = TOWER_UPGRADE_PATHS[self.tower_type]
        for lvl in range(2, self.level + 1):
            if lvl in path:
                total += path[lvl]["cost"]

        # Refund separuh dari biaya Regen Shield kalau sudah dibeli.
        if getattr(self, "regen_shield_active", False):
            total += TOWER_REGEN_SHIELD_COST

        return int(total * 0.5)

    # ═══════════════════════════════════════
    # REGEN SHIELD (fitur berbayar)
    # ═══════════════════════════════════════
    def can_activate_regen_shield(self):
        """True kalau tower level cukup & regen shield belum aktif."""
        return (TOWER_REGEN_SHIELD_ENABLED
                and self.level >= TOWER_REGEN_SHIELD_MIN_LEVEL
                and not getattr(self, "regen_shield_active", False)
                and self.alive)

    def regen_shield_cost(self):
        """Harga aktivasi Regen Shield (setara upgrade tower level 5)."""
        return TOWER_REGEN_SHIELD_COST

    def activate_regen_shield(self):
        """Aktifkan regen shield. Kembalikan True kalau berhasil."""
        if not self.can_activate_regen_shield():
            return False
        self.regen_shield_active = True
        # Langsung isi shield penuh saat diaktifkan (efek instan).
        self.shield = self.shield_max
        self.shield_regen_flash = 6
        self.upgrade_flash = 30
        return True

    def update(self, all_units, all_towers, all_bases):
        if not self.alive:
            return

        if self.timer > 0:
            self.timer -= 1

        if self.upgrade_flash > 0:
            self.upgrade_flash -= 1

        if self.shoot_flash_timer > 0:
            self.shoot_flash_timer -= 1

        # ═══ Update regen system ═══
        self._update_regen()

        if self.shield_regen_flash > 0:
            self.shield_regen_flash -= 1
        if self.hp_regen_flash > 0:
            self.hp_regen_flash -= 1

        # Bullets
        for b in self.bullets:
            b.update(all_units)
        self.bullets = [b for b in self.bullets if b.active]

        # Targeting via spatial grid. Fallback scan hanya untuk true boss,
        # karena boss tidak dimasukkan ke grid unit biasa.
        try:
            from _system import query_enemies_in_range
            enemies = query_enemies_in_range(
                self.x, self.y, self.range, self.team)
        except Exception:
            enemies = [u for u in all_units
                       if u.team != self.team and u.alive]

        for u in all_units:
            if not getattr(u, "boss_type", None):
                continue
            if not u.alive or u.team == self.team:
                continue
            if math.hypot(u.x - self.x, u.y - self.y) <= self.range:
                if u not in enemies:
                    enemies.append(u)

        self.target = self._find_target(enemies)

        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            self.angle = math.atan2(dy, dx)

            if self.timer == 0:
                self._shoot(enemies)
                self.timer = self.attack_cooldown

    def _update_regen(self):
        """Update shield regen & HP regen"""
        self.no_damage_timer += 1

        if TOWER_HP_REGEN_ENABLED:
            if self.no_damage_timer >= TOWER_HP_REGEN_DELAY:
                max_regen_hp = self.max_hp * TOWER_HP_REGEN_MAX_RATIO
                if self.hp < max_regen_hp:
                    self.hp = min(max_regen_hp,
                                  self.hp + TOWER_HP_REGEN_RATE)
                    self.hp_regen_flash = 3

        # ═══ REGEN SHIELD (fitur berbayar) ═══
        # Shield regen otomatis setelah jeda tanpa damage, HANYA kalau
        # pemain/AI sudah membayar aktivasi Regen Shield.
        if (TOWER_REGEN_SHIELD_ENABLED
                and getattr(self, "regen_shield_active", False)):
            if self.no_damage_timer >= TOWER_REGEN_SHIELD_DELAY:
                if self.shield < self.shield_max:
                    self.shield = min(self.shield_max,
                                      self.shield + TOWER_REGEN_SHIELD_RATE)
                    self.shield_regen_flash = 3

    def _find_target(self, enemies):
        best = None
        best_dist = self.range
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= best_dist:
                best_dist = dist
                best = e
        return best

    def _shoot(self, enemies):
        if not self.target:
            return

        # Suara tembak PER JENIS menara: archer, cannon, ice, mage
        # masing-masing punya suara sendiri (lihat combat_audio.py).
        # Tim biru (punya pemain) sedikit lebih keras daripada tim merah.
        try:
            from mobile import combat_audio as _ca
            _ca.play(_ca.jenis_tower(self.tower_type),
                     volume_mult=1.0 if self.team == "blue" else 0.8)
        except Exception:
            pass

        if self.tower_type == "archer":
            self._shoot_archer(enemies)
        elif self.tower_type == "cannon":
            self._shoot_cannon()
        elif self.tower_type == "ice":
            self._shoot_ice()
        elif self.tower_type == "mage":
            self._shoot_mage(enemies)

    def _shoot_archer(self, enemies):
        """Archer shoot - sync dengan posisi bow di render"""
        face = 1 if self.target.x > self.x else -1

        from towers.archer_tower import get_archer_bow_position

        bow_x, bow_y = get_archer_bow_position(
            self.x, self.y, self.level, face)

        if self.level >= 5:
            num_shots = 2 if self.level == 5 else 3

            if num_shots == 2:
                offsets = [(-8, 0), (8, 0)]
            else:
                offsets = [(-11, 3), (0, -2), (11, 3)]

            targets = [self.target]
            for e in enemies:
                if len(targets) >= num_shots:
                    break
                if e == self.target or not e.alive:
                    continue
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist <= self.range:
                    targets.append(e)

            while len(targets) < num_shots:
                targets.append(self.target)

            SCALE = 0.7
            for i, (offset_x, offset_y) in enumerate(offsets):
                if i < len(targets):
                    shot_bow_x = bow_x + int(offset_x * SCALE)
                    shot_bow_y = bow_y + int(offset_y * SCALE)
                    self.bullets.append(Bullet(
                        shot_bow_x, shot_bow_y, targets[i],
                        self.damage, self.team, "normal"))
        else:
            self.bullets.append(Bullet(bow_x, bow_y, self.target,
                                       self.damage, self.team, "normal"))

            if self.double_shot:
                second_target = None
                for e in enemies:
                    if e == self.target or not e.alive:
                        continue
                    dist = math.hypot(e.x - self.x, e.y - self.y)
                    if dist <= self.range:
                        second_target = e
                        break

                if second_target:
                    face2 = 1 if second_target.x > self.x else -1
                    bow2_x, bow2_y = get_archer_bow_position(
                        self.x, self.y, self.level, face2)
                    self.bullets.append(Bullet(
                        bow2_x, bow2_y, second_target,
                        self.damage, self.team, "normal"))

        self.shoot_flash_timer = 8

    def _shoot_cannon(self):
        face = 1
        if self.target:
            face = 1 if self.target.x > self.x else -1

        recoil = 0
        if self.timer > self.attack_cooldown - 8:
            recoil_progress = (self.attack_cooldown - self.timer) / 8
            recoil = int(4 * (1 - recoil_progress)) * -face

        from towers.cannon_tower import get_cannon_muzzle_position

        bx, by = get_cannon_muzzle_position(
            self.x, self.y, self.level, face, recoil)

        special = {'splash': self.splash}
        if self.burn_dps > 0:
            special['burn_dps'] = self.burn_dps
            special['burn_duration'] = self.burn_duration

        self.bullets.append(Bullet(bx, by, self.target, self.damage,
                                   self.team, "cannon",
                                   special))

        self.shoot_flash_timer = 10
        # Suara tembak menara kini GLOBAL: semua jenis menara (archer,
        # cannon, ice, mage) memakai suara yang sama lewat
        # combat_audio.play(TOWER) di _shoot(). Dulu cannon punya
        # ledakan TAMBAHAN yang hanya berbunyi untuk tim biru -
        # tim merah bisu dan antar-menara tidak konsisten.

    def _shoot_ice(self):
        face = 1
        if self.target:
            face = 1 if self.target.x > self.x else -1

        from towers.ice_tower import get_ice_crystal_position

        crystal_x, crystal_y = get_ice_crystal_position(
            self.x, self.y, self.level, face)

        bx = crystal_x + math.cos(self.angle) * 5
        by = crystal_y + math.sin(self.angle) * 5

        special = {
            'slow': self.slow,
            'slow_duration': self.slow_duration,
        }
        # Debuff attack speed (buff baru ice tower)
        if self.atk_slow > 0:
            special['atk_slow'] = self.atk_slow
        if self.slow_aoe > 0:
            special['slow_aoe'] = self.slow_aoe

        self.bullets.append(Bullet(bx, by, self.target, self.damage,
                                   self.team, "ice", special))
        self.shoot_flash_timer = 8

    def _shoot_mage(self, enemies):
        from towers.mage_tower import get_mage_crystal_position

        face = 1
        if self.target:
            face = 1 if self.target.x > self.x else -1

        crystal_x, crystal_y = get_mage_crystal_position(
            self.x, self.y, self.level, face)

        bx = crystal_x + math.cos(self.angle) * 5
        by = crystal_y + math.sin(self.angle) * 5

        targets = [self.target]
        for e in enemies:
            if len(targets) >= self.chain:
                break
            if e in targets or not e.alive:
                continue
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= self.range:
                targets.append(e)

        # Debuff skill damage down + anti-heal (buff baru mage tower)
        special = {}
        if self.skill_down > 0:
            special['skill_down'] = self.skill_down
        if self.anti_heal > 0:
            special['anti_heal'] = self.anti_heal
        if special:
            special['debuff_duration'] = self.debuff_duration

        for tgt in targets:
            self.bullets.append(Bullet(bx, by, tgt, self.damage,
                                       self.team, "mage", special))

        self.shoot_flash_timer = 8

    def take_damage(self, damage, from_team):
        """Damage sistem dengan shield absorb"""
        self.no_damage_timer = 0

        remaining_damage = damage

        # Shield absorb first
        if self.shield > 0:
            if self.shield >= remaining_damage:
                self.shield -= remaining_damage
                remaining_damage = 0
            else:
                remaining_damage -= self.shield
                self.shield = 0

        # Then HP
        if remaining_damage > 0:
            self.hp -= remaining_damage
            if self.hp <= 0:
                self.hp = 0
                if self.alive:
                    self.alive = False
                    # Menara HANCUR: satu suara global untuk SEMUA
                    # jenis (archer/cannon/ice/mage sama).
                    try:
                        SoundManager().play('tower_destroyed',
                                            volume_mult=0.8)
                    except Exception:
                        pass

    def draw(self, surface):
        if not self.alive:
            return

        x, y = self.x, self.y

        # Selected range indicator - OPTIMIZED
        if self.selected:
            d = self.range * 2 + 4
            range_surf = pygame.Surface((d, d), pygame.SRCALPHA)
            center = d // 2
            r_color = (self.color[0], self.color[1], self.color[2], 40)
            pygame.draw.circle(range_surf, r_color,
                               (center, center), self.range)
            border_c = (self.color[0], self.color[1], self.color[2], 150)
            pygame.draw.circle(range_surf, border_c,
                               (center, center), self.range, 2)
            surface.blit(range_surf,
                         (int(x) - center, int(y) - center))

        # Upgrade flash
        if self.upgrade_flash > 0:
            flash_alpha = int((self.upgrade_flash / 30) * 200)
            flash_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 200, flash_alpha),
                               (40, 40), 30)
            surface.blit(flash_surf, (x - 40, y - 40))

        # Shield armor crest (pengganti bubble jelek)
        if TOWER_SHIELD_ENABLED and self.shield > 0:
            self._draw_shield_crest(surface, x, y)
        # CATATAN: dulu ada pulsing green ring saat regen_shield aktif —
        # dihapus karena mengganggu visual (lihat git history). Indikator
        # regen kini cukup lewat armor crest yang menyala (bright) + tanda
        # plus kecil di samping HP bar.

        # Draw tower body
        self._draw_tower_body(surface, x, y)

        # Muzzle flash (archer)
        if self.shoot_flash_timer > 0 and self.tower_type == "archer":
            from towers.archer_tower import get_archer_bow_position
            face = 1
            if self.target:
                face = 1 if self.target.x > self.x else -1

            flash_x, flash_y = get_archer_bow_position(
                self.x, self.y, self.level, face)

            intensity = self.shoot_flash_timer / 8.0
            size = int(5 * intensity)

            if size > 0:
                key = ("tower_flash", size)
                glow_surf = _TOWER_SPRITE_CACHE.get(key)
                if glow_surf is None:
                    glow_surf = pygame.Surface((size * 4, size * 4),
                                               pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf,
                                       (255, 240, 150,
                                        int(120 * intensity)),
                                       (size * 2, size * 2), size * 2)
                    pygame.draw.circle(glow_surf,
                                       (255, 255, 200,
                                        int(200 * intensity)),
                                       (size * 2, size * 2), size)
                    _TOWER_SPRITE_CACHE[key] = glow_surf
                surface.blit(glow_surf,
                             (flash_x - size * 2, flash_y - size * 2))

        # ═══ HP BAR + SHIELD BAR ═══
        bar_w = 44
        bar_h = 5
        bx = x - bar_w // 2

        # Fungsi top_y di-cache per tower (import di dalam draw
        # tiap frame itu mahal saat 10+ tower).
        if getattr(self, "_top_fn_type", None) != self.tower_type:
            if self.tower_type == "archer":
                from towers.archer_tower import get_archer_top_y
                self._top_fn = get_archer_top_y
            elif self.tower_type == "cannon":
                from towers.cannon_tower import get_cannon_top_y
                self._top_fn = get_cannon_top_y
            elif self.tower_type == "ice":
                from towers.ice_tower import get_ice_top_y
                self._top_fn = get_ice_top_y
            elif self.tower_type == "mage":
                from towers.mage_tower import get_mage_top_y
                self._top_fn = get_mage_top_y
            else:
                self._top_fn = None
            self._top_fn_type = self.tower_type

        if self._top_fn is not None:
            by = self._top_fn(self.x, self.y, self.level) - 14
        else:
            by = y - 26

        # Shield bar
        if TOWER_SHIELD_ENABLED:
            shield_bar_y = by - bar_h - 2
            pygame.draw.rect(surface, (30, 30, 50),
                             (bx, shield_bar_y, bar_w, bar_h))
            shield_ratio = (self.shield / self.shield_max
                            if self.shield_max > 0 else 0)
            shield_fill = int(bar_w * shield_ratio)
            if shield_fill > 0:
                shield_color = (SHIELD_COLOR_BLUE if self.team == "blue"
                                else SHIELD_COLOR_RED)
                if self.shield_regen_flash > 0:
                    pulse_color = (min(255, shield_color[0] + 50),
                                   min(255, shield_color[1] + 50),
                                   min(255, shield_color[2] + 50))
                    pygame.draw.rect(surface, pulse_color,
                                     (bx, shield_bar_y, shield_fill, bar_h))
                else:
                    pygame.draw.rect(surface, shield_color,
                                     (bx, shield_bar_y, shield_fill, bar_h))

                shine_h = max(1, bar_h // 2)
                shine_color = (min(255, shield_color[0] + 80),
                               min(255, shield_color[1] + 80),
                               min(255, shield_color[2] + 80))
                pygame.draw.rect(surface, shine_color,
                                 (bx, shield_bar_y, shield_fill, shine_h))

            pygame.draw.rect(surface, BLACK,
                             (bx, shield_bar_y, bar_w, bar_h), 1)

        # HP bar
        pygame.draw.rect(surface, (40, 0, 0), (bx, by, bar_w, bar_h))
        hp_ratio = self.hp / self.max_hp
        fill = int(bar_w * hp_ratio)
        if fill > 0:
            if hp_ratio > 0.6:
                hp_color = GREEN
            elif hp_ratio > 0.3:
                hp_color = YELLOW
            else:
                hp_color = RED

            if self.hp_regen_flash > 0:
                hp_color = (min(255, hp_color[0] + 50),
                            min(255, hp_color[1] + 80),
                            min(255, hp_color[2] + 50))

            pygame.draw.rect(surface, hp_color, (bx, by, fill, bar_h))

            shine_h = max(1, bar_h // 2)
            shine_color = (min(255, hp_color[0] + 60),
                           min(255, hp_color[1] + 60),
                           min(255, hp_color[2] + 60))
            pygame.draw.rect(surface, shine_color, (bx, by, fill, shine_h))

        pygame.draw.rect(surface, BLACK, (bx, by, bar_w, bar_h), 1)

        # Level indicator (teks di-cache per level)
        key = ("tower_lvl", self.level)
        lvl_surf = _TOWER_SPRITE_CACHE.get(key)
        if lvl_surf is None:
            from _render import get_font
            lvl_font = get_font(14)
            lvl_text = lvl_font.render(f"{self.level}", True, YELLOW)
            # BUG LAMA: lebar kotak dipatok 12 px. Begitu level dua
            # angka ("10"), teksnya lebih lebar dari kotaknya dan
            # terpotong. Sekarang kotak mengikuti lebar teks.
            _lw = max(12, lvl_text.get_width() + 6)
            _lh = max(bar_h + 2, lvl_text.get_height() + 2)
            lvl_surf = pygame.Surface((_lw, _lh), pygame.SRCALPHA)
            lvl_bg = lvl_surf.get_rect()
            pygame.draw.rect(lvl_surf, (0, 0, 0), lvl_bg,
                             border_radius=2)
            pygame.draw.rect(lvl_surf, YELLOW, lvl_bg, 1,
                             border_radius=2)
            lvl_surf.blit(lvl_text, lvl_text.get_rect(center=lvl_bg.center))
            _TOWER_SPRITE_CACHE[key] = lvl_surf
        # Ditempel rapat di kiri bar, mengikuti lebar kotak yang
        # sebenarnya (dulu selalu -14 walau kotaknya berubah).
        surface.blit(lvl_surf,
                     (bx - lvl_surf.get_width() - 2,
                      by + (bar_h - lvl_surf.get_height()) // 2))

        # Regen indicator
        if self.no_damage_timer >= TOWER_SHIELD_REGEN_DELAY:
            self._draw_regen_indicator(surface, bx + bar_w + 2, by)

        # Draw bullets
        for b in self.bullets:
            b.draw(surface)

    def _draw_shield_crest(self, surface, x, y):
        """ARMOR CREST kecil di samping tower sebagai indikator shield.

        Menggantikan gelembung transparan lama (jelek & mahal render).
        Crest terisi sesuai sisa shield dan menyala saat regen.
        """
        if self.shield <= 0 or self.shield_max <= 0:
            return

        shield_ratio = self.shield / self.shield_max
        if shield_ratio <= 0:
            return

        base_color = (SHIELD_COLOR_BLUE if self.team == "blue"
                      else SHIELD_COLOR_RED)

        # Posisi: sedikit di kanan-atas badan tower, dekat HP bar
        crest_size = 14
        crest_x = x + 26
        crest_y = y - 28 - self.level

        _draw_armor_crest(surface, crest_x, crest_y, crest_size,
                          base_color, shield_ratio,
                          bright=self.shield_regen_flash > 0)

    def _draw_regen_indicator(self, surface, x, y):
        """Small green plus icon showing regen active"""
        plus_color = (100, 255, 100)

        if self.hp >= self.max_hp and self.shield >= self.shield_max:
            return

        pulse = int(math.sin(self.timer * 0.2) * 2) + 2
        size = 3 + pulse // 2

        pygame.draw.rect(surface, plus_color,
                         (x + size - 1, y - size // 2, 2, size + 2))
        pygame.draw.rect(surface, plus_color,
                         (x + size // 2 - 1, y + size // 2 - 1,
                          size + 2, 2))
        pygame.draw.rect(surface, (200, 255, 200),
                         (x + size, y, 1, 1))

    def _draw_tower_body(self, surface, x, y):
        """Draw tower visual - delegate ke module towers/ (SPRITE CACHE)

        Cache luar di atas cache internal towers/: internal cache
        re-render tiap 2 frame saat menembak (state shoot_N) - itu
        biang ~0.1 ms/tower saat combat ramai. Di sini frame tembak
        dikuantisasi lebih kasar (//3) + arah hadap ikut key, jadi
        render ulang jauh lebih jarang, sisanya blit murah.
        """
        from towers import render_tower
        size = 18 + self.level
        face = 1 if (self.target is not None
                     and getattr(self.target, "alive", False)
                     and self.target.x > self.x) else 0
        shoot_b = self.shoot_flash_timer // 3
        key = ("tw", self.tower_type, self.team, self.level,
               face, shoot_b)
        ent = _TOWER_SPRITE_CACHE.get(key)
        if ent is None:
            canvas = pygame.Surface((220, 220), pygame.SRCALPHA)
            render_tower(self.tower_type, canvas, self, 110, 110, size)
            rect = canvas.get_bounding_rect(min_alpha=8)
            if rect.width > 0 and rect.height > 0:
                sub = canvas.subsurface(rect).copy()
                # Di HP, blit per-piksel-alpha ~244 ns/piksel. Sprite
                # yang sudah di-cache pun jadi mahal. Colorkey memakai
                # jalur RLE yang ~20x lebih murah.
                try:
                    from mobile.perf import Quality as _Qt, to_colorkey_sprite
                    if not _Qt.cheap_alpha:
                        sub = to_colorkey_sprite(sub)
                except Exception:
                    pass
                ent = (sub, 110 - rect.x, 110 - rect.y)
                if len(_TOWER_SPRITE_CACHE) > 500:
                    _TOWER_SPRITE_CACHE.pop(next(iter(_TOWER_SPRITE_CACHE)))
                _TOWER_SPRITE_CACHE[key] = ent
            else:
                # Renderer tidak menghasilkan piksel - fallback langsung
                render_tower(self.tower_type, surface, self, x, y, size)
                return
        surface.blit(ent[0],
                     (int(x - ent[1]), int(y - ent[2])))


# Outline color helper
PAL_OUTLINE_C = (24, 24, 32)


# ====================================================================
# castle.py
# ====================================================================

# CASTLE.PY - Evolution Castle System
# Match Reference - Kingdom Rush Style
# ================================

import pygame
import math
import random


# ═══════════════════════════════════════════════════════
# PALETTES
# ═══════════════════════════════════════════════════════

def _get_palette(team):
    if team == "blue":
        return {
            # Stone (chunky light gray)
            's_darkest': (75, 78, 88),
            's_dark': (110, 115, 128),
            's_mid': (155, 160, 172),
            's_light': (200, 205, 215),
            's_lightest': (240, 242, 248),
            's_shadow': (50, 52, 60),
            's_edge': (35, 38, 45),

            # Wood
            'w_darkest': (45, 25, 15),
            'w_dark': (85, 50, 25),
            'w_mid': (135, 85, 45),
            'w_light': (180, 125, 75),
            'w_high': (220, 165, 105),

            # Metal (iron)
            'm_darkest': (25, 28, 35),
            'm_dark': (55, 60, 72),
            'm_mid': (100, 108, 125),
            'm_light': (160, 168, 185),
            'm_lightest': (215, 220, 235),

            # Silver (shield)
            'sv_darkest': (90, 95, 105),
            'sv_dark': (140, 145, 155),
            'sv_mid': (185, 190, 200),
            'sv_light': (220, 225, 235),
            'sv_high': (245, 248, 252),

            # Gold (accents, spires)
            'b_darkest': (95, 60, 12),
            'b_dark': (150, 105, 25),
            'b_mid': (210, 160, 50),
            'b_light': (250, 215, 90),
            'b_lightest': (255, 245, 165),
            'b_shine': (255, 250, 200),

            # Blue roof tiles (SIGNATURE!)
            'r_darkest': (25, 55, 105),
            'r_dark': (40, 85, 155),
            'r_mid': (70, 130, 200),
            'r_light': (115, 175, 230),
            'r_lightest': (170, 210, 245),

            # Banner red (bright)
            'flag_darkest': (90, 15, 15),
            'flag_dark': (155, 30, 30),
            'flag_mid': (210, 55, 55),
            'flag_light': (245, 100, 100),
            'flag_high': (255, 150, 150),

            # Team accent (royal blue)
            'a_darkest': (15, 35, 85),
            'a_dark': (35, 60, 135),
            'a_mid': (60, 100, 190),
            'a_light': (110, 155, 235),
            'a_lightest': (180, 210, 255),

            # Ground (dirt path)
            'ground_dark': (95, 75, 45),
            'ground_mid': (145, 115, 70),
            'ground_light': (190, 155, 100),
            'ground_high': (225, 195, 140),

            # Grass
            'grass_dark': (45, 75, 30),
            'grass_mid': (70, 110, 45),
            'grass_light': (100, 155, 60),
            'grass_high': (145, 195, 90),

            # Utility
            'shine': (255, 255, 250),
            'shadow_soft': (0, 0, 0, 80),
            'shadow_hard': (10, 8, 15),

            # Fire (torch)
            'f_dark': (180, 45, 15),
            'f_mid': (255, 135, 40),
            'f_light': (255, 220, 95),
            'f_hot': (255, 250, 200),
        }
    else:
        return {
            's_darkest': (65, 45, 45),
            's_dark': (100, 75, 75),
            's_mid': (145, 110, 110),
            's_light': (185, 150, 150),
            's_lightest': (220, 190, 190),
            's_shadow': (45, 30, 30),
            's_edge': (30, 20, 20),

            'w_darkest': (40, 22, 12),
            'w_dark': (80, 45, 22),
            'w_mid': (125, 75, 40),
            'w_light': (170, 110, 62),
            'w_high': (215, 158, 100),

            'm_darkest': (28, 20, 20),
            'm_dark': (55, 40, 40),
            'm_mid': (95, 70, 70),
            'm_light': (150, 115, 115),
            'm_lightest': (200, 165, 165),

            'sv_darkest': (85, 70, 70),
            'sv_dark': (130, 108, 108),
            'sv_mid': (175, 148, 148),
            'sv_light': (210, 185, 185),
            'sv_high': (240, 220, 220),

            'b_darkest': (75, 42, 8),
            'b_dark': (125, 78, 20),
            'b_mid': (180, 122, 42),
            'b_light': (225, 172, 72),
            'b_lightest': (250, 210, 130),
            'b_shine': (255, 230, 180),

            # Dark red roof
            'r_darkest': (60, 15, 15),
            'r_dark': (105, 25, 25),
            'r_mid': (160, 45, 45),
            'r_light': (215, 80, 80),
            'r_lightest': (245, 140, 140),

            'flag_darkest': (30, 10, 10),
            'flag_dark': (65, 20, 20),
            'flag_mid': (110, 35, 35),
            'flag_light': (170, 65, 65),
            'flag_high': (215, 120, 120),

            'a_darkest': (70, 10, 10),
            'a_dark': (120, 20, 20),
            'a_mid': (180, 40, 40),
            'a_light': (220, 80, 80),
            'a_lightest': (255, 140, 140),

            'ground_dark': (75, 55, 40),
            'ground_mid': (115, 85, 60),
            'ground_light': (160, 120, 85),
            'ground_high': (200, 165, 120),

            'grass_dark': (55, 55, 30),
            'grass_mid': (85, 80, 45),
            'grass_light': (120, 115, 65),
            'grass_high': (165, 155, 90),

            'shine': (255, 240, 240),
            'shadow_soft': (0, 0, 0, 80),
            'shadow_hard': (8, 5, 5),

            'f_dark': (140, 20, 90),
            'f_mid': (220, 55, 180),
            'f_light': (255, 135, 240),
            'f_hot': (255, 220, 255),
        }


# ═══════════════════════════════════════════════════════
# CASTLE CLASS (Logic unchanged)
# ═══════════════════════════════════════════════════════

class Castle:
    """Castle - evolution visual per level + early shield (wave <10)"""

    def __init__(self, x, y, team):
        self.x = x
        self.y = y
        self.team = team

        self.level = 1
        self._apply_level_stats()

        self.timer = 0
        self.bullets = []
        self.alive = True
        self.angle = 0
        self.target = None
        self.pulse = 0

        self._render_cache = {}

        # ═══ CASTLE SHIELD SYSTEM (anti-smurf) ═══
        # Shield active before wave threshold, reduces damage and shows bubble.
        # Both teams get it - feature parity.
        try:
            self.shield_max = int(self.max_hp * CASTLE_SHIELD_HP_RATIO)
        except Exception:
            self.shield_max = int(self.max_hp * 0.6)
        self.shield = self.shield_max
        self.shield_active = True  # Will be updated by Game based on wave
        self.shield_no_damage_timer = 0
        self.shield_regen_flash = 0
        self.early_wave_threshold = 10
        try:
            self.early_wave_threshold = CASTLE_SHIELD_WAVE_THRESHOLD
        except Exception:
            pass
        self.damage_reduction = 0.75
        try:
            self.damage_reduction = CASTLE_SHIELD_DAMAGE_REDUCTION
        except Exception:
            pass

    def _apply_level_stats(self):
        data = NEXUS_LEVELS[self.level]
        old_max_hp = getattr(self, 'max_hp', 0)
        old_hp = getattr(self, 'hp', 0)

        self.max_hp = data["hp"]
        if old_max_hp > 0:
            hp_ratio = old_hp / old_max_hp
            self.hp = int(self.max_hp * hp_ratio) + (self.max_hp - old_max_hp)
            self.hp = min(self.max_hp, self.hp + 500)
        else:
            self.hp = self.max_hp

        self.damage = data["damage"]
        self.range = data["range"]
        self.attack_cooldown = data["attack_cooldown"]
        self.color_accent = data["color_accent"]

        self._render_cache = {}

    def upgrade(self):
        if self.level >= MAX_NEXUS_LEVEL:
            return False
        self.level += 1
        self._apply_level_stats()
        return True

    def upgrade_cost(self):
        if self.level >= MAX_NEXUS_LEVEL:
            return 0
        return NEXUS_LEVELS[self.level]["upgrade_cost"]

    def get_minion_composition(self):
        return NEXUS_WAVE_COMPOSITION[self.level]

    def update(self, all_units):
        if not self.alive:
            return

        self.pulse += 0.05
        if self.timer > 0:
            self.timer -= 1

        # ═══ Update castle shield regen ═══
        self._update_castle_shield()

        if getattr(self, 'shield_regen_flash', 0) > 0:
            self.shield_regen_flash -= 1

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]

        enemies = [u for u in all_units
                   if u.team != self.team and u.alive]

        self.target = self._find_target(enemies)

        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            self.angle = math.atan2(dy, dx)

            if self.timer == 0:
                self._shoot(self.target)
                self.timer = self.attack_cooldown

    def _update_castle_shield(self):
        """Regen shield when not taking damage, only if shield active"""
        if not getattr(self, 'shield_active', False):
            return
        self.shield_no_damage_timer += 1
        try:
            delay = CASTLE_SHIELD_REGEN_DELAY
        except Exception:
            delay = 120
        try:
            rate = CASTLE_SHIELD_REGEN_RATE
        except Exception:
            rate = 2.0
        if self.shield_no_damage_timer >= delay:
            if self.shield < self.shield_max:
                self.shield = min(self.shield_max, self.shield + rate)
                self.shield_regen_flash = 4

    def set_wave(self, wave_number):
        """Called by Game to enable/disable early shield"""
        try:
            thr = CASTLE_SHIELD_WAVE_THRESHOLD
        except Exception:
            thr = 10
        # Shield active before threshold
        was_active = getattr(self, 'shield_active', True)
        self.shield_active = wave_number < thr
        # When shield just expired, clear shield HP
        if was_active and not self.shield_active:
            self.shield = 0

    def _find_target(self, enemies):
        best = None
        best_dist = self.range
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= best_dist:
                best_dist = dist
                best = e
        return best

    def _shoot(self, target):
        # Shoot dari gate area
        self.bullets.append(
            Bullet(self.x, self.y - 25, target, self.damage, self.team)
        )

    def take_damage(self, damage, from_team, damage_type='normal'):
        # ═══ CASTLE SHIELD LOGIC (anti-smurf, wave <10) ═══
        # Both player and AI castles have shield before wave 10
        effective_damage = damage
        shield_absorbed = 0

        if getattr(self, 'shield_active', False):
            # Reset regen timer
            self.shield_no_damage_timer = 0

            # Shield absorbs first
            if getattr(self, 'shield', 0) > 0:
                if self.shield >= effective_damage:
                    shield_absorbed = effective_damage
                    self.shield -= effective_damage
                    effective_damage = 0
                else:
                    shield_absorbed = self.shield
                    effective_damage -= self.shield
                    self.shield = 0

            # Remaining damage reduced by % if shield still considered active
            # Even if shield HP depleted, early protection still reduces damage
            if effective_damage > 0:
                try:
                    reduction = CASTLE_SHIELD_DAMAGE_REDUCTION
                except Exception:
                    reduction = getattr(self, 'damage_reduction', 0.75)
                effective_damage = int(effective_damage * (1.0 - reduction))

        self.hp -= effective_damage

        try:
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                # Show shield absorb number if absorbed
                if shield_absorbed > 0:
                    game.effects.add_damage_number(
                        self.x, self.y - 60,
                        f"SHIELD -{shield_absorbed}",
                        is_critical=False,
                        damage_type='ice')
                if effective_damage > 0:
                    game.effects.add_damage_number(
                        self.x, self.y - 40,
                        effective_damage, is_critical=True,
                        damage_type='fire')
                shake_intensity = min(15, effective_damage / 20) if effective_damage > 0 else 0
                if shake_intensity > 1:
                    game.effects.shake_screen(shake_intensity)
                game.effects.add_hit_particles(
                    self.x, self.y, team=self.team, count=10)
        except Exception:
            pass

        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def apply_slow(self, amount, duration):
        pass

    def draw(self, surface):
        """Render castle - LARGER CANVAS"""
        palette = _get_palette(self.team)
        lvl = self.level

        # ═══ CANVAS - SMALLER SIZE ═══
        cw, ch = 180, 160  # KEMBALIKAN ke ukuran original

        cache_key = f"castle_{self.team}_L{lvl}"
        if cache_key not in self._render_cache:
            castle_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _render_castle_full(castle_canvas, self, cw // 2,
                                ch - 20, palette)
            self._render_cache[cache_key] = castle_canvas

        SCALE = 0.85  # Perkecil 15%
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)

        try:
            from mobile.perf import Quality as _Qc
            _cheap = _Qc.cheap_alpha
        except Exception:
            _cheap = True

        if _cheap:
            # ── Jalur asli (PC): salin, efek dinamis, lalu skala ──
            canvas = self._render_cache[cache_key].copy()
            _render_dynamic_effects(canvas, self, palette)
            scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))
        else:
            # ── Jalur HP ──
            # Dulu TIAP FRAME: copy 180x160 + efek + smoothscale.
            # smoothscale tidak punya jalur SIMD di ARM sehingga
            # memakan belasan ms; dua kastil saja = 47 ms/frame
            # padahal tidak ada unit lain di layar.
            # Sekarang hasil skala di-cache per (tim, level).
            skey = (self.team, lvl, new_w, new_h)
            scaled = _CASTLE_SCALED_CACHE.get(skey)
            if scaled is None:
                scaled = pygame.transform.smoothscale(
                    self._render_cache[cache_key], (new_w, new_h))
                try:
                    from mobile.perf import to_colorkey_sprite
                    scaled = to_colorkey_sprite(scaled)
                except Exception:
                    pass
                _CASTLE_SCALED_CACHE[skey] = scaled

        final_x = int(self.x - new_w // 2)
        final_y = int(self.y - new_h + 35)
        surface.blit(scaled, (final_x, final_y))

        # ═══ CASTLE SHIELD CREST (before wave 10) ═══
        if getattr(self, 'shield_active', False) and getattr(self, 'shield', 0) > 0:
            self._draw_castle_shield(surface, final_x + new_w//2, final_y - 10)

        if not _cheap:
            try:
                _render_dynamic_effects_direct(
                    surface, self, palette, final_x, final_y, SCALE)
            except Exception:
                pass

        self._draw_hp_bar(surface)

        for b in self.bullets:
            b.draw(surface)

    def _draw_castle_shield(self, surface, cx, cy):
        """ARMOR CREST kecil di atas castle sebagai indikator shield.

        Menggantikan gelembung multi-ring + glow lama yang jelek dan
        mahal render. Crest terisi sesuai sisa shield, berdenyut halus,
        dan menyala saat regen.
        """
        if not getattr(self, 'shield_active', False):
            return
        shield_ratio = self.shield / max(1, self.shield_max)
        if shield_ratio <= 0:
            return

        try:
            col = CASTLE_SHIELD_COLOR_BLUE if self.team == "blue" else CASTLE_SHIELD_COLOR_RED
        except Exception:
            col = (100, 200, 255) if self.team == "blue" else (255, 120, 120)

        # Denyut halus posisi vertikal (bukan alpha mahal)
        bob = int(math.sin(self.pulse * 1.2) * 2)
        crest_size = 18
        bright = getattr(self, 'shield_regen_flash', 0) > 0

        _draw_armor_crest(surface, cx, cy + bob, crest_size,
                          tuple(col), shield_ratio, bright=bright)

    def _draw_hp_bar(self, surface):
        """HP bar + shield bar - fixed layout no overlap"""
        # Draw shield bar above castle if active
        if getattr(self, 'shield_active', False) and getattr(self, 'shield_max', 0) > 0:
            bar_w = 60
            bar_h = 6
            bx = int(self.x - bar_w//2)
            by = int(self.y - 80)
            pygame.draw.rect(surface, (30, 30, 50), (bx, by, bar_w, bar_h), border_radius=3)
            ratio = self.shield / max(1, self.shield_max)
            fill = int(bar_w * ratio)
            if fill > 0:
                try:
                    col = CASTLE_SHIELD_COLOR_BLUE if self.team == "blue" else CASTLE_SHIELD_COLOR_RED
                except Exception:
                    col = (100, 200, 255) if self.team == "blue" else (255, 120, 120)
                pygame.draw.rect(surface, col, (bx, by, fill, bar_h), border_radius=3)
            pygame.draw.rect(surface, (0,0,0), (bx, by, bar_w, bar_h), 1, border_radius=3)
            # Label
            try:
                from _render import get_font
                f = get_font(10, 'body_bold')
                label = f.render(f"SHIELD {int(ratio*100)}%", True, (200,220,255))
                surface.blit(label, (bx, by - 12))
            except Exception:
                pass
# ═══════════════════════════════════════════════════════
# CASTLE FULL RENDER (dispatch per level)
# ═══════════════════════════════════════════════════════

def _render_castle_full(canvas, castle, cx, cy, palette):
    """Render castle berdasarkan level"""
    lvl = castle.level

    # Ground base (semua level)
    _draw_castle_ground(canvas, cx, cy, palette)

    if lvl == 1:
        _render_castle_lvl1(canvas, cx, cy - 15, palette)
    elif lvl == 2:
        _render_castle_lvl2(canvas, cx, cy - 15, palette)
    elif lvl == 3:
        _render_castle_lvl3(canvas, cx, cy - 15, palette)
    elif lvl == 4:
        _render_castle_lvl4(canvas, cx, cy - 15, palette)
    elif lvl == 5:
        _render_castle_lvl5(canvas, cx, cy - 15, palette)
    else:
        _render_castle_lvl6(canvas, cx, cy - 15, palette)

def _draw_castle_ground(canvas, cx, cy, palette):
    """Ground base - SMALLER"""
    ground_w = 160  # dari 200
    ground_h = 26   # dari 32

    # Shadow (soft)
    for i in range(5):
        alpha = 90 - i * 15
        if alpha <= 0:
            break
        w = ground_w + i * 4
        h = ground_h + i * 2
        shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                            (0, 0, w, h))
        canvas.blit(shadow_surf, (cx - w // 2, cy - h // 2 + 3))

    # Ground base (dirt)
    pygame.draw.ellipse(canvas, palette['ground_dark'],
                        (cx - ground_w // 2, cy,
                         ground_w, ground_h))
    pygame.draw.ellipse(canvas, palette['ground_mid'],
                        (cx - ground_w // 2 + 3, cy + 2,
                         ground_w - 6, ground_h - 6))
    pygame.draw.ellipse(canvas, palette['ground_light'],
                        (cx - ground_w // 2 + 6, cy + 4,
                         ground_w - 12, ground_h - 10))
    pygame.draw.ellipse(canvas, palette['ground_high'],
                        (cx - ground_w // 2 + 10, cy + 6,
                         ground_w - 20, ground_h - 16))

    # Cobblestone path
    random.seed(42)
    for _ in range(25):
        px = cx + random.randint(-ground_w // 2 + 8, ground_w // 2 - 8)
        py = cy + random.randint(4, ground_h - 6)
        s = random.randint(2, 5)
        pygame.draw.rect(canvas, palette['s_shadow'],
                         (px, py, s + 1, s // 2 + 2))
        pygame.draw.rect(canvas, palette['s_dark'],
                         (px, py, s, s // 2 + 1))
        pygame.draw.rect(canvas, palette['s_mid'],
                         (px, py, s - 1, s // 2))
        pygame.draw.rect(canvas, palette['s_light'],
                         (px, py, s - 2, 1))

    # Grass tufts (di edges)
    for _ in range(18):
        angle = random.uniform(0, math.pi * 2)
        r = random.uniform(ground_w // 2 - 15, ground_w // 2 - 3)
        gx = cx + int(math.cos(angle) * r)
        gy = cy + int(math.sin(angle) * ground_h // 3) + 5

        for blade_offset in [-1, 0, 1]:
            bx = gx + blade_offset
            pygame.draw.rect(canvas, palette['grass_dark'],
                             (bx, gy, 1, 3))
            pygame.draw.rect(canvas, palette['grass_mid'],
                             (bx, gy, 1, 2))
            pygame.draw.rect(canvas, palette['grass_light'],
                             (bx, gy, 1, 1))
        pygame.draw.rect(canvas, palette['grass_high'],
                         (gx, gy, 1, 1))

    # Small rocks
    for _ in range(10):
        rx = cx + random.randint(-ground_w // 2 + 5, ground_w // 2 - 5)
        ry = cy + random.randint(5, ground_h - 5)
        pygame.draw.rect(canvas, palette['s_shadow'],
                         (rx + 1, ry + 1, 3, 2))
        pygame.draw.rect(canvas, palette['s_dark'],
                         (rx, ry, 3, 2))
        pygame.draw.rect(canvas, palette['s_mid'],
                         (rx, ry, 2, 1))
        pygame.draw.rect(canvas, palette['s_lightest'],
                         (rx, ry, 1, 1))
    random.seed()
# ═══════════════════════════════════════════════════════
# LEVEL 1: OUTPOST (Simple wooden fort)
# ═══════════════════════════════════════════════════════

def _render_castle_lvl1(canvas, cx, cy, palette):
    """Simple wooden fort"""
    _draw_wooden_palisade(canvas, cx, cy + 10, palette)
    _draw_wooden_watchtower(canvas, cx, cy, palette,
                             height=40, width=26)  # dari 48, 32


def _draw_wooden_palisade(canvas, cx, cy, palette):
    """Wooden palisade wall - SMALLER"""
    palisade_w = 75  # dari 90

    for log_x in range(-palisade_w // 2, palisade_w // 2, 4):
        lx = cx + log_x
        log_h = 16 + random.Random(log_x).randint(-2, 2)  # dari 20

        pygame.draw.rect(canvas, palette['shadow_hard'],
                         (lx + 1, cy - log_h + 1, 4, log_h))
        pygame.draw.rect(canvas, palette['w_darkest'],
                         (lx, cy - log_h, 4, log_h))
        pygame.draw.rect(canvas, palette['w_dark'],
                         (lx, cy - log_h, 3, log_h))
        pygame.draw.rect(canvas, palette['w_mid'],
                         (lx, cy - log_h, 2, log_h - 1))
        pygame.draw.rect(canvas, palette['w_light'],
                         (lx, cy - log_h, 1, log_h - 2))

        # Pointed spike top
        pygame.draw.polygon(canvas, palette['w_darkest'], [
            (lx, cy - log_h),
            (lx + 2, cy - log_h - 4),
            (lx + 4, cy - log_h),
        ])
        pygame.draw.polygon(canvas, palette['w_dark'], [
            (lx, cy - log_h),
            (lx + 2, cy - log_h - 3),
            (lx + 3, cy - log_h),
        ])
        pygame.draw.polygon(canvas, palette['w_mid'], [
            (lx, cy - log_h),
            (lx + 2, cy - log_h - 3),
            (lx + 2, cy - log_h),
        ])


def _draw_wooden_watchtower(canvas, cx, cy, palette, height=48, width=32):
    """Central wooden watchtower - lvl 1"""
    tw = width
    th = height
    top = cy - th

    # Shadow
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - tw // 2 + 3, top + 3, tw, th))

    # Wooden body (log construction)
    pygame.draw.rect(canvas, palette['w_darkest'],
                     (cx - tw // 2, top, tw, th))
    pygame.draw.rect(canvas, palette['w_dark'],
                     (cx - tw // 2, top, tw - 2, th - 1))
    pygame.draw.rect(canvas, palette['w_mid'],
                     (cx - tw // 2 + 1, top, tw - 4, th - 2))
    pygame.draw.rect(canvas, palette['w_light'],
                     (cx - tw // 2 + 1, top, 4, th - 3))
    pygame.draw.rect(canvas, palette['w_high'],
                     (cx - tw // 2 + 2, top + 1, 2, th - 5))

    # Horizontal log lines (visible planks)
    for line_y in range(top + 6, top + th - 2, 7):
        pygame.draw.line(canvas, palette['w_darkest'],
                         (cx - tw // 2 + 1, line_y),
                         (cx + tw // 2 - 1, line_y), 1)
        pygame.draw.line(canvas, palette['w_high'],
                         (cx - tw // 2 + 1, line_y + 1),
                         (cx + tw // 2 - 1, line_y + 1), 1)

    # Simple door (wooden)
    dw, dh = 10, 16
    dx = cx - dw // 2
    dy = top + th - dh - 2

    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (dx - 1, dy - 1, dw + 2, dh + 2))
    pygame.draw.rect(canvas, (25, 15, 10),
                     (dx, dy, dw, dh))
    pygame.draw.rect(canvas, palette['w_darkest'],
                     (dx, dy, dw, dh))
    pygame.draw.rect(canvas, palette['w_dark'],
                     (dx, dy, dw - 1, dh - 1))

    # Door planks
    for plank_x in range(dx + 2, dx + dw - 1, 3):
        pygame.draw.line(canvas, palette['w_darkest'],
                         (plank_x, dy),
                         (plank_x, dy + dh), 1)

    # Metal handle
    pygame.draw.circle(canvas, palette['m_darkest'],
                       (dx + dw - 3, dy + dh // 2 + 2), 1)
    pygame.draw.circle(canvas, palette['b_mid'],
                       (dx + dw - 3, dy + dh // 2 + 2), 1)

    # Small window (top)
    win_y = top + 12
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - 3, win_y - 3, 6, 6))
    pygame.draw.rect(canvas, (20, 15, 10),
                     (cx - 3, win_y - 3, 6, 6))
    # Cross bars
    pygame.draw.rect(canvas, palette['w_darkest'],
                     (cx - 1, win_y - 3, 1, 6))
    pygame.draw.rect(canvas, palette['w_darkest'],
                     (cx - 3, win_y, 6, 1))

    # ═══ POINTED WOODEN ROOF ═══
    roof_h = 18
    roof_top_y = top - roof_h

    pygame.draw.polygon(canvas, palette['shadow_hard'], [
        (cx - tw // 2 - 3 + 2, top + 2),
        (cx + 2, roof_top_y + 2),
        (cx + tw // 2 + 3 + 2, top + 2),
    ])
    pygame.draw.polygon(canvas, palette['w_darkest'], [
        (cx - tw // 2 - 3, top),
        (cx, roof_top_y),
        (cx + tw // 2 + 3, top),
    ])
    pygame.draw.polygon(canvas, palette['w_dark'], [
        (cx - tw // 2 - 1, top - 1),
        (cx, roof_top_y + 1),
        (cx + tw // 2 + 1, top - 1),
    ])
    pygame.draw.polygon(canvas, palette['w_mid'], [
        (cx - tw // 2 + 1, top - 1),
        (cx, roof_top_y + 2),
        (cx + tw // 2 - 1, top - 1),
    ])
    # Left highlight
    pygame.draw.polygon(canvas, palette['w_light'], [
        (cx - tw // 2 + 1, top - 1),
        (cx, roof_top_y + 2),
        (cx - 2, top - 1),
    ])

    # Wood shingle lines
    for shingle_y in range(top - 2, roof_top_y + 3, 3):
        rel = (top - shingle_y) / roof_h
        w = int((tw // 2 + 2) * (1 - rel))
        pygame.draw.line(canvas, palette['w_darkest'],
                         (cx - w, shingle_y),
                         (cx + w, shingle_y), 1)

    # Red flag on top (basic)
    pygame.draw.rect(canvas, palette['w_darkest'],
                     (cx - 1, roof_top_y - 6, 2, 6))
    pygame.draw.rect(canvas, palette['w_mid'],
                     (cx, roof_top_y - 6, 1, 6))
    pygame.draw.polygon(canvas, palette['flag_darkest'], [
        (cx + 1, roof_top_y - 6),
        (cx + 6, roof_top_y - 5),
        (cx + 5, roof_top_y - 2),
        (cx + 1, roof_top_y - 3),
    ])
    pygame.draw.polygon(canvas, palette['flag_dark'], [
        (cx + 1, roof_top_y - 5),
        (cx + 5, roof_top_y - 4),
        (cx + 1, roof_top_y - 3),
    ])
    pygame.draw.polygon(canvas, palette['flag_mid'], [
        (cx + 1, roof_top_y - 5),
        (cx + 4, roof_top_y - 4),
        (cx + 1, roof_top_y - 4),
    ])


# ═══════════════════════════════════════════════════════
# LEVEL 2: WATCHTOWER (Stone + 1 side tower)
# ═══════════════════════════════════════════════════════

def _render_castle_lvl2(canvas, cx, cy, palette):
    """Watchtower + basic gate"""
    _draw_stone_corner_tower(canvas, cx - 35, cy - 12, palette,
                              height=36, has_roof=False)  # dari 42
    _draw_central_stone_wall(canvas, cx, cy, palette,
                              width=42, height=46,  # dari 50, 54
                              has_gate=True,
                              has_battlements=True)


def _draw_stone_corner_tower(canvas, cx, cy, palette, height=42,
                              has_roof=False, has_gold_spire=False,
                              has_gold_trim=False):
    """Stone corner tower (chunky bricks)"""
    tw = 26
    th = height
    top = cy - th

    # Shadow
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - tw // 2 + 2, top + 2, tw, th),
                     border_radius=3)

    # ═══ TOWER BODY (chunky stone) ═══
    pygame.draw.rect(canvas, palette['s_edge'],
                     (cx - tw // 2, top, tw, th),
                     border_radius=3)
    pygame.draw.rect(canvas, palette['s_darkest'],
                     (cx - tw // 2, top, tw - 2, th),
                     border_radius=3)
    pygame.draw.rect(canvas, palette['s_dark'],
                     (cx - tw // 2, top, tw - 4, th - 1),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_mid'],
                     (cx - tw // 2, top, tw - 6, th - 3),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_light'],
                     (cx - tw // 2 + 2, top + 1, 5, th - 4),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_lightest'],
                     (cx - tw // 2 + 3, top + 2, 2, th - 6))

    # ═══ CHUNKY BRICKS ═══
    brick_h = 6
    brick_w = 8
    for row in range(th // brick_h):
        row_y = top + 4 + row * brick_h
        offset = brick_w // 2 if row % 2 else 0

        for bx in range(-tw // 2 + 3 + offset, tw // 2 - 2, brick_w):
            block_x = cx + bx
            _draw_stone_brick(canvas, block_x, row_y,
                               brick_w - 1, brick_h - 1, palette)

    # ═══ BATTLEMENTS (crenellations) ═══
    for merlon_x in range(-tw // 2, tw // 2 - 1, 5):
        _draw_battlement_stone(canvas, cx + merlon_x, top - 6,
                                4, 8, palette)

    # ═══ SMALL WINDOW dengan glow ═══
    win_y = top + th // 2 + 4
    # Arch window
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - 3, win_y - 4, 6, 8))
    pygame.draw.circle(canvas, palette['shadow_hard'],
                       (cx, win_y - 4), 3)

    # Interior (dark with fire glow)
    pygame.draw.rect(canvas, (15, 10, 8),
                     (cx - 2, win_y - 4, 4, 7))
    pygame.draw.circle(canvas, (15, 10, 8), (cx, win_y - 4), 2)

    # Fire glow inside
    pygame.draw.rect(canvas, palette['f_dark'],
                     (cx - 2, win_y - 2, 4, 5))
    pygame.draw.rect(canvas, palette['f_mid'],
                     (cx - 1, win_y - 1, 2, 4))
    pygame.draw.rect(canvas, palette['f_light'],
                     (cx - 1, win_y, 1, 2))

    # Small glow outside window
    glow = pygame.Surface((12, 10), pygame.SRCALPHA)
    for r in range(6, 1, -1):
        alpha = 30 - r * 2
        if alpha > 0:
            pygame.draw.circle(glow,
                               (*palette['f_mid'], alpha),
                               (6, 5), r)
    canvas.blit(glow, (cx - 6, win_y - 5))

    # ═══ BLUE CONICAL ROOF (lvl 3+) ═══
    if has_roof:
        _draw_blue_conical_roof(canvas, cx, top, tw, palette,
                                 has_gold_spire=has_gold_spire,
                                 has_gold_trim=has_gold_trim)


def _draw_stone_brick(canvas, x, y, w, h, palette):
    """Individual chunky stone brick"""
    pygame.draw.rect(canvas, palette['s_shadow'],
                     (x, y, w, h), border_radius=1)
    pygame.draw.rect(canvas, palette['s_dark'],
                     (x, y, w - 1, h - 1), border_radius=1)
    pygame.draw.rect(canvas, palette['s_mid'],
                     (x, y, w - 2, h - 2), border_radius=1)
    pygame.draw.rect(canvas, palette['s_light'],
                     (x, y, w - 3, h // 2), border_radius=1)
    pygame.draw.rect(canvas, palette['s_lightest'],
                     (x + 1, y + 1, w - 4, 1))


def _draw_battlement_stone(canvas, x, y, w, h, palette):
    """Single crenellation stone"""
    # Shadow
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (x + 1, y + 1, w, h))

    # Stone layers
    pygame.draw.rect(canvas, palette['s_edge'],
                     (x, y, w, h))
    pygame.draw.rect(canvas, palette['s_darkest'],
                     (x, y, w - 1, h - 1))
    pygame.draw.rect(canvas, palette['s_dark'],
                     (x, y, w - 2, h - 2))
    pygame.draw.rect(canvas, palette['s_mid'],
                     (x, y, w - 3, h - 3))
    pygame.draw.rect(canvas, palette['s_light'],
                     (x, y, w - 4, h // 2))
    pygame.draw.rect(canvas, palette['s_lightest'],
                     (x + 1, y + 1, w - 5, 2))
    pygame.draw.rect(canvas, palette['shine'],
                     (x + 1, y + 1, 2, 1))


def _draw_blue_conical_roof(canvas, cx, top, tower_w, palette,
                             has_gold_spire=False,
                             has_gold_trim=False):
    """Blue conical roof (SIGNATURE - match reference)"""
    roof_h = 22
    roof_top_y = top - roof_h

    # Roof shadow
    pygame.draw.polygon(canvas, palette['shadow_hard'], [
        (cx - tower_w // 2 - 2 + 2, top - 2 + 2),
        (cx + 2, roof_top_y + 2),
        (cx + tower_w // 2 + 2 + 2, top - 2 + 2),
    ])

    # ═══ BLUE ROOF (5-tone gradient) ═══
    # Base darkest
    pygame.draw.polygon(canvas, palette['r_darkest'], [
        (cx - tower_w // 2 - 3, top - 2),
        (cx, roof_top_y),
        (cx + tower_w // 2 + 3, top - 2),
    ])

    # Dark layer
    pygame.draw.polygon(canvas, palette['r_dark'], [
        (cx - tower_w // 2 - 2, top - 2),
        (cx, roof_top_y + 1),
        (cx + tower_w // 2 + 2, top - 2),
    ])

    # Mid layer
    pygame.draw.polygon(canvas, palette['r_mid'], [
        (cx - tower_w // 2, top - 2),
        (cx, roof_top_y + 2),
        (cx + tower_w // 2, top - 2),
    ])

    # Light (left side highlight)
    pygame.draw.polygon(canvas, palette['r_light'], [
        (cx - tower_w // 2, top - 2),
        (cx, roof_top_y + 2),
        (cx - 2, top - 2),
    ])
    pygame.draw.polygon(canvas, palette['r_lightest'], [
        (cx - tower_w // 2 + 1, top - 2),
        (cx - 1, roof_top_y + 3),
        (cx - 3, top - 2),
    ])

    # ═══ BLUE TILE PATTERN (scale-like) ═══
    for tile_row in range(4):
        tile_y = top - 2 - tile_row * 5
        rel = (top - 2 - tile_y) / roof_h
        w = int((tower_w // 2 + 2) * (1 - rel))

        # Horizontal tile separator
        pygame.draw.line(canvas, palette['r_darkest'],
                         (cx - w, tile_y),
                         (cx + w, tile_y), 1)

        # Individual tiles (curved)
        for tx in range(-w + 2, w - 1, 4):
            tile_x = cx + tx
            # Scale pattern
            pygame.draw.arc(canvas, palette['r_darkest'],
                            (tile_x - 1, tile_y - 2, 4, 4),
                            0, math.pi, 1)

    # ═══ GOLD TRIM at bottom of roof ═══
    if has_gold_trim:
        pygame.draw.rect(canvas, palette['b_darkest'],
                         (cx - tower_w // 2 - 2, top - 3,
                          tower_w + 4, 2))
        pygame.draw.rect(canvas, palette['b_dark'],
                         (cx - tower_w // 2 - 2, top - 3,
                          tower_w + 4, 1))
        pygame.draw.rect(canvas, palette['b_mid'],
                         (cx - tower_w // 2 - 1, top - 3,
                          tower_w + 2, 1))
        # Highlight
        for dot_x in range(-tower_w // 2, tower_w // 2, 4):
            pygame.draw.rect(canvas, palette['b_light'],
                             (cx + dot_x, top - 3, 1, 1))

    # ═══ GOLD SPIRE on top (SIGNATURE!) ═══
    if has_gold_spire:
        spire_h = 12

        # Base ball
        pygame.draw.circle(canvas, palette['shadow_hard'],
                           (cx + 1, roof_top_y + 1), 3)
        pygame.draw.circle(canvas, palette['b_darkest'],
                           (cx, roof_top_y), 3)
        pygame.draw.circle(canvas, palette['b_dark'],
                           (cx, roof_top_y), 2)
        pygame.draw.circle(canvas, palette['b_mid'],
                           (cx - 1, roof_top_y - 1), 1)
        pygame.draw.rect(canvas, palette['b_light'],
                         (cx - 1, roof_top_y - 1, 1, 1))

        # Vertical rod
        pygame.draw.rect(canvas, palette['b_darkest'],
                         (cx - 1, roof_top_y - spire_h,
                          3, spire_h))
        pygame.draw.rect(canvas, palette['b_dark'],
                         (cx - 1, roof_top_y - spire_h,
                          2, spire_h))
        pygame.draw.rect(canvas, palette['b_mid'],
                         (cx, roof_top_y - spire_h,
                          1, spire_h))

        # Pointed tip (spear)
        pygame.draw.polygon(canvas, palette['b_darkest'], [
            (cx - 2, roof_top_y - spire_h),
            (cx, roof_top_y - spire_h - 6),
            (cx + 2, roof_top_y - spire_h),
        ])
        pygame.draw.polygon(canvas, palette['b_dark'], [
            (cx - 1, roof_top_y - spire_h),
            (cx, roof_top_y - spire_h - 5),
            (cx + 1, roof_top_y - spire_h),
        ])
        pygame.draw.polygon(canvas, palette['b_mid'], [
            (cx - 1, roof_top_y - spire_h),
            (cx, roof_top_y - spire_h - 4),
            (cx, roof_top_y - spire_h),
        ])
        pygame.draw.rect(canvas, palette['b_light'],
                         (cx, roof_top_y - spire_h - 3, 1, 2))
        pygame.draw.rect(canvas, palette['b_shine'],
                         (cx, roof_top_y - spire_h - 3, 1, 1))


def _draw_central_stone_wall(canvas, cx, cy, palette, width=60, height=50,
                              has_gate=True, has_battlements=True):
    """Central stone wall with gate"""
    ww = width
    wh = height
    top = cy - wh

    # Shadow
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - ww // 2 + 2, top + 2, ww, wh),
                     border_radius=2)

    # Wall body (chunky stone)
    pygame.draw.rect(canvas, palette['s_edge'],
                     (cx - ww // 2, top, ww, wh),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_darkest'],
                     (cx - ww // 2, top, ww - 2, wh),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_dark'],
                     (cx - ww // 2, top, ww - 4, wh - 1),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_mid'],
                     (cx - ww // 2, top, ww - 6, wh - 3),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_light'],
                     (cx - ww // 2 + 2, top + 1, 6, wh - 4),
                     border_radius=1)
    pygame.draw.rect(canvas, palette['s_lightest'],
                     (cx - ww // 2 + 3, top + 2, 3, wh - 6))

    # Chunky bricks
    brick_h = 6
    brick_w = 9
    for row in range(wh // brick_h):
        row_y = top + 4 + row * brick_h
        offset = brick_w // 2 if row % 2 else 0

        for bx in range(-ww // 2 + 4 + offset, ww // 2 - 3, brick_w):
            _draw_stone_brick(canvas, cx + bx, row_y,
                               brick_w - 1, brick_h - 1, palette)

    # Battlements on top
    if has_battlements:
        for merlon_x in range(-ww // 2, ww // 2 - 1, 5):
            _draw_battlement_stone(canvas, cx + merlon_x, top - 6,
                                    4, 8, palette)

    # ═══ GATE ═══
    if has_gate:
        _draw_castle_gate(canvas, cx, top + wh, palette,
                          gate_w=18, gate_h=26)


def _draw_castle_gate(canvas, cx, gate_bottom_y, palette,
                       gate_w=18, gate_h=26, has_studs=False,
                       has_portcullis=False):
    """Detailed gate with wooden door"""
    gw = gate_w
    gh = gate_h
    gx = cx - gw // 2
    gy = gate_bottom_y - gh

    # ═══ ARCH KEYSTONES around gate ═══
    for angle_deg in range(-90, 91, 20):
        angle = math.radians(angle_deg)
        px = cx + math.cos(angle) * (gw // 2 + 2)
        py = gy + gw // 2 - math.sin(angle) * (gw // 2 + 2)

        # Keystone
        pygame.draw.rect(canvas, palette['s_edge'],
                         (int(px) - 2, int(py) - 2, 4, 4))
        pygame.draw.rect(canvas, palette['s_darkest'],
                         (int(px) - 2, int(py) - 2, 3, 3))
        pygame.draw.rect(canvas, palette['s_dark'],
                         (int(px) - 1, int(py) - 1, 3, 3))
        pygame.draw.rect(canvas, palette['s_mid'],
                         (int(px) - 1, int(py) - 1, 2, 2))
        pygame.draw.rect(canvas, palette['s_light'],
                         (int(px) - 1, int(py) - 1, 1, 1))

    # ═══ GATE OPENING (dark) ═══
    # Rectangle bottom
    pygame.draw.rect(canvas, (10, 8, 12),
                     (gx, gy + gw // 2, gw, gh - gw // 2))
    # Arch top
    pygame.draw.circle(canvas, (10, 8, 12),
                       (cx, gy + gw // 2), gw // 2)

    # ═══ WOODEN DOOR (recessed) ═══
    door_w = gw - 2
    door_h = gh - gw // 2 - 2
    door_x = cx - door_w // 2
    door_y = gy + gw // 2 + 1

    # Door shadow
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (door_x + 1, door_y + 1, door_w, door_h))

    # Door base
    pygame.draw.rect(canvas, palette['w_darkest'],
                     (door_x, door_y, door_w, door_h))
    pygame.draw.rect(canvas, palette['w_dark'],
                     (door_x, door_y, door_w - 1, door_h - 1))
    pygame.draw.rect(canvas, palette['w_mid'],
                     (door_x + 1, door_y + 1, door_w - 3, door_h - 3))

    # Vertical wooden planks
    for plank_x in range(door_x + 2, door_x + door_w - 1, 3):
        pygame.draw.line(canvas, palette['w_darkest'],
                         (plank_x, door_y),
                         (plank_x, door_y + door_h - 1), 1)
        pygame.draw.line(canvas, palette['w_light'],
                         (plank_x + 1, door_y),
                         (plank_x + 1, door_y + door_h - 1), 1)

    # ═══ IRON REINFORCEMENT BANDS ═══
    for band_y in [door_y + 3, door_y + door_h - 5]:
        pygame.draw.rect(canvas, palette['m_darkest'],
                         (door_x, band_y, door_w, 2))
        pygame.draw.rect(canvas, palette['m_dark'],
                         (door_x, band_y, door_w, 1))
        pygame.draw.rect(canvas, palette['m_mid'],
                         (door_x + 1, band_y, door_w - 2, 1))

        # ═══ STUDS ═══
        if has_studs:
            for stud_x in range(door_x + 2, door_x + door_w - 1, 4):
                pygame.draw.circle(canvas, palette['m_darkest'],
                                   (stud_x, band_y + 1), 1)
                pygame.draw.rect(canvas, palette['m_lightest'],
                                 (stud_x, band_y, 1, 1))

    # Handle (metal ring)
    handle_y = door_y + door_h // 2 + 2
    pygame.draw.circle(canvas, palette['m_darkest'],
                       (cx + door_w // 3, handle_y), 2)
    pygame.draw.circle(canvas, palette['m_dark'],
                       (cx + door_w // 3, handle_y), 2)
    pygame.draw.circle(canvas, palette['m_mid'],
                       (cx + door_w // 3 - 1, handle_y - 1), 1)

    # ═══ PORTCULLIS (iron bars in front, lvl 4+) ═══
    if has_portcullis:
        port_top_y = gy + 2
        for bar_x in range(gx + 3, gx + gw - 2, 4):
            pygame.draw.rect(canvas, palette['m_darkest'],
                             (bar_x, port_top_y, 2, gw // 2 + 3))
            pygame.draw.rect(canvas, palette['m_dark'],
                             (bar_x, port_top_y, 1, gw // 2 + 2))
            pygame.draw.rect(canvas, palette['m_light'],
                             (bar_x, port_top_y, 1, 3))


# ═══════════════════════════════════════════════════════
# LEVEL 3: FORTRESS (2 corner towers + gate + partial roof)
# ═══════════════════════════════════════════════════════
def _render_castle_lvl3(canvas, cx, cy, palette):
    """Fortress dengan 2 corner towers"""
    _draw_stone_corner_tower(canvas, cx - 46, cy - 12, palette,
                              height=46, has_roof=True,  # dari 55
                              has_gold_spire=True)
    _draw_stone_corner_tower(canvas, cx + 46, cy - 12, palette,
                              height=46, has_roof=True,
                              has_gold_spire=True)

    _draw_central_stone_wall(canvas, cx, cy, palette,
                              width=60, height=50,  # dari 72, 58
                              has_gate=True,
                              has_battlements=True)
# ═══════════════════════════════════════════════════════
# LEVEL 4: STRONGHOLD (MATCH REFERENCE - full castle)
# ═══════════════════════════════════════════════════════
def _render_castle_lvl4(canvas, cx, cy, palette):
    """STRONGHOLD - match reference"""
    _draw_stone_corner_tower(canvas, cx - 50, cy - 12, palette,
                              height=52, has_roof=True,  # dari 62
                              has_gold_spire=True)
    _draw_stone_corner_tower(canvas, cx + 50, cy - 12, palette,
                              height=52, has_roof=True,
                              has_gold_spire=True)

    _draw_central_stone_wall(canvas, cx, cy, palette,
                              width=66, height=54,  # dari 80, 64
                              has_gate=True,
                              has_battlements=True)

    # Central gate roof
    _draw_central_gate_roof(canvas, cx, cy - 50, palette,
                             width=26, has_gold_spire=True)  # dari 32

    # Shield emblem
    _draw_silver_shield_emblem(canvas, cx, cy - 36, palette)

    # 2 banners
    _draw_hanging_banner(canvas, cx - 18, cy - 36, palette, side='left')
    _draw_hanging_banner(canvas, cx + 18, cy - 36, palette, side='right')


def _draw_central_gate_roof(canvas, cx, cy, palette, width=32,
                             has_gold_spire=False):
    """Small central roof above gate (match reference)"""
    rw = width
    rh = 16
    top = cy - rh

    # Base of roof (stone)
    pygame.draw.rect(canvas, palette['s_dark'],
                     (cx - rw // 2, cy - 2, rw, 3))
    pygame.draw.rect(canvas, palette['s_mid'],
                     (cx - rw // 2, cy - 2, rw - 1, 2))
    pygame.draw.rect(canvas, palette['s_light'],
                     (cx - rw // 2 + 1, cy - 2, rw - 3, 1))

    # Shadow
    pygame.draw.polygon(canvas, palette['shadow_hard'], [
        (cx - rw // 2 - 1 + 2, cy - 2 + 2),
        (cx + 2, top + 2),
        (cx + rw // 2 + 1 + 2, cy - 2 + 2),
    ])

    # Blue roof (peaked)
    pygame.draw.polygon(canvas, palette['r_darkest'], [
        (cx - rw // 2 - 1, cy - 2),
        (cx, top),
        (cx + rw // 2 + 1, cy - 2),
    ])
    pygame.draw.polygon(canvas, palette['r_dark'], [
        (cx - rw // 2, cy - 2),
        (cx, top + 1),
        (cx + rw // 2, cy - 2),
    ])
    pygame.draw.polygon(canvas, palette['r_mid'], [
        (cx - rw // 2 + 1, cy - 2),
        (cx, top + 2),
        (cx + rw // 2 - 1, cy - 2),
    ])
    # Left highlight
    pygame.draw.polygon(canvas, palette['r_light'], [
        (cx - rw // 2 + 1, cy - 2),
        (cx, top + 2),
        (cx - 3, cy - 2),
    ])
    pygame.draw.polygon(canvas, palette['r_lightest'], [
        (cx - rw // 2 + 2, cy - 2),
        (cx - 2, top + 3),
        (cx - 4, cy - 2),
    ])

    # Tile pattern
    for tile_y in range(cy - 2, top + 3, 4):
        rel = (cy - 2 - tile_y) / rh
        w = int((rw // 2 + 1) * (1 - rel))
        pygame.draw.line(canvas, palette['r_darkest'],
                         (cx - w, tile_y),
                         (cx + w, tile_y), 1)

    # Gold spire on top
    if has_gold_spire:
        spire_h = 8
        pygame.draw.circle(canvas, palette['b_darkest'],
                           (cx, top), 2)
        pygame.draw.circle(canvas, palette['b_mid'],
                           (cx, top), 1)

        pygame.draw.rect(canvas, palette['b_darkest'],
                         (cx - 1, top - spire_h, 2, spire_h))
        pygame.draw.rect(canvas, palette['b_mid'],
                         (cx - 1, top - spire_h, 1, spire_h))

        # Spike
        pygame.draw.polygon(canvas, palette['b_darkest'], [
            (cx - 2, top - spire_h),
            (cx, top - spire_h - 4),
            (cx + 2, top - spire_h),
        ])
        pygame.draw.polygon(canvas, palette['b_mid'], [
            (cx - 1, top - spire_h),
            (cx, top - spire_h - 3),
            (cx + 1, top - spire_h),
        ])
        pygame.draw.rect(canvas, palette['b_shine'],
                         (cx, top - spire_h - 2, 1, 1))


def _draw_silver_shield_emblem(canvas, cx, cy, palette):
    """Silver shield with crossed swords + gold frame (match reference)"""
    sw = 20
    sh = 22

    # Shadow
    pygame.draw.polygon(canvas, palette['shadow_hard'], [
        (cx - sw // 2 + 2, cy - sh // 2 + 2),
        (cx + sw // 2 + 2, cy - sh // 2 + 2),
        (cx + sw // 2 + 2, cy + 3),
        (cx + 2, cy + sh // 2 + 2),
        (cx - sw // 2 + 2, cy + 3),
    ])

    # ═══ GOLD FRAME (thick) ═══
    frame_pts = [
        (cx - sw // 2, cy - sh // 2),
        (cx + sw // 2, cy - sh // 2),
        (cx + sw // 2 + 1, cy + 1),
        (cx, cy + sh // 2),
        (cx - sw // 2 - 1, cy + 1),
    ]
    pygame.draw.polygon(canvas, palette['b_darkest'], frame_pts)
    pygame.draw.polygon(canvas, palette['b_dark'], [
        (cx - sw // 2 + 1, cy - sh // 2 + 1),
        (cx + sw // 2 - 1, cy - sh // 2 + 1),
        (cx + sw // 2, cy + 1),
        (cx, cy + sh // 2 - 1),
        (cx - sw // 2, cy + 1),
    ])
    pygame.draw.polygon(canvas, palette['b_mid'], [
        (cx - sw // 2 + 1, cy - sh // 2 + 1),
        (cx - sw // 2 + 5, cy - sh // 2 + 1),
        (cx - sw // 2 + 1, cy - 2),
    ])
    pygame.draw.polygon(canvas, palette['b_light'], [
        (cx - sw // 2 + 1, cy - sh // 2 + 1),
        (cx - sw // 2 + 3, cy - sh // 2 + 1),
        (cx - sw // 2 + 1, cy - sh // 2 + 4),
    ])

    # ═══ SILVER INTERIOR ═══
    inner_pts = [
        (cx - sw // 2 + 3, cy - sh // 2 + 3),
        (cx + sw // 2 - 3, cy - sh // 2 + 3),
        (cx + sw // 2 - 2, cy),
        (cx, cy + sh // 2 - 3),
        (cx - sw // 2 + 2, cy),
    ]
    pygame.draw.polygon(canvas, palette['sv_darkest'], inner_pts)
    pygame.draw.polygon(canvas, palette['sv_dark'], [
        (cx - sw // 2 + 4, cy - sh // 2 + 4),
        (cx + sw // 2 - 4, cy - sh // 2 + 4),
        (cx + sw // 2 - 3, cy - 1),
        (cx, cy + sh // 2 - 4),
        (cx - sw // 2 + 3, cy - 1),
    ])
    pygame.draw.polygon(canvas, palette['sv_mid'], [
        (cx - sw // 2 + 4, cy - sh // 2 + 4),
        (cx - 1, cy - sh // 2 + 4),
        (cx - sw // 2 + 4, cy - 2),
    ])
    pygame.draw.polygon(canvas, palette['sv_light'], [
        (cx - sw // 2 + 4, cy - sh // 2 + 4),
        (cx - sw // 2 + 7, cy - sh // 2 + 4),
        (cx - sw // 2 + 4, cy - sh // 2 + 7),
    ])
    pygame.draw.rect(canvas, palette['sv_high'],
                     (cx - sw // 2 + 4, cy - sh // 2 + 4, 2, 1))

    # ═══ CROSSED SWORDS (dark iron) ═══
    # Sword 1 (top-left to bottom-right)
    pygame.draw.line(canvas, palette['m_darkest'],
                     (cx - 5, cy - 7), (cx + 5, cy + 5), 3)
    pygame.draw.line(canvas, palette['m_dark'],
                     (cx - 5, cy - 7), (cx + 5, cy + 5), 2)
    pygame.draw.line(canvas, palette['m_light'],
                     (cx - 5, cy - 7), (cx + 5, cy + 5), 1)

    # Sword 2 (top-right to bottom-left)
    pygame.draw.line(canvas, palette['m_darkest'],
                     (cx + 5, cy - 7), (cx - 5, cy + 5), 3)
    pygame.draw.line(canvas, palette['m_dark'],
                     (cx + 5, cy - 7), (cx - 5, cy + 5), 2)
    pygame.draw.line(canvas, palette['m_light'],
                     (cx + 5, cy - 7), (cx - 5, cy + 5), 1)

    # Sword tips (bright)
    pygame.draw.rect(canvas, palette['sv_high'],
                     (cx - 6, cy - 8, 2, 2))
    pygame.draw.rect(canvas, palette['sv_high'],
                     (cx + 5, cy - 8, 2, 2))

    # Center shine (crossing point)
    pygame.draw.rect(canvas, palette['b_light'],
                     (cx - 1, cy - 1, 2, 2))
    pygame.draw.rect(canvas, palette['b_shine'],
                     (cx - 1, cy - 1, 1, 1))


def _draw_hanging_banner(canvas, cx, cy, palette, side='left'):
    """Red hanging banner (match reference)"""
    bw = 8
    bh = 18

    # Shadow
    pygame.draw.polygon(canvas, palette['shadow_hard'], [
        (cx - bw // 2 + 2, cy + 2),
        (cx + bw // 2 + 2, cy + 2),
        (cx + bw // 2 + 2, cy + bh - 4 + 2),
        (cx + 2, cy + bh + 2),
        (cx - bw // 2 + 2, cy + bh - 4 + 2),
    ])

    # Banner base
    pygame.draw.polygon(canvas, palette['flag_darkest'], [
        (cx - bw // 2, cy),
        (cx + bw // 2, cy),
        (cx + bw // 2, cy + bh - 4),
        (cx, cy + bh),
        (cx - bw // 2, cy + bh - 4),
    ])

    # Main red
    pygame.draw.polygon(canvas, palette['flag_dark'], [
        (cx - bw // 2 + 1, cy),
        (cx + bw // 2 - 1, cy),
        (cx + bw // 2 - 1, cy + bh - 4),
        (cx, cy + bh - 1),
        (cx - bw // 2 + 1, cy + bh - 4),
    ])
    pygame.draw.polygon(canvas, palette['flag_mid'], [
        (cx - bw // 2 + 1, cy + 1),
        (cx + bw // 2 - 2, cy + 1),
        (cx + bw // 2 - 2, cy + bh - 5),
        (cx, cy + bh - 2),
        (cx - bw // 2 + 1, cy + bh - 5),
    ])

    # Highlight (left edge)
    pygame.draw.polygon(canvas, palette['flag_light'], [
        (cx - bw // 2 + 1, cy + 1),
        (cx - bw // 2 + 2, cy + 1),
        (cx - bw // 2 + 1, cy + bh - 5),
    ])
    pygame.draw.polygon(canvas, palette['flag_high'], [
        (cx - bw // 2 + 1, cy + 2),
        (cx - bw // 2 + 2, cy + 2),
        (cx - bw // 2 + 1, cy + 6),
    ])

    # Gold top rod
    pygame.draw.rect(canvas, palette['b_darkest'],
                     (cx - bw // 2 - 1, cy - 1, bw + 2, 3))
    pygame.draw.rect(canvas, palette['b_dark'],
                     (cx - bw // 2 - 1, cy - 1, bw + 2, 2))
    pygame.draw.rect(canvas, palette['b_mid'],
                     (cx - bw // 2 - 1, cy - 1, bw + 2, 1))
    pygame.draw.rect(canvas, palette['b_light'],
                     (cx - bw // 2, cy - 1, bw, 1))

    # Gold ends
    pygame.draw.circle(canvas, palette['b_darkest'],
                       (cx - bw // 2 - 1, cy), 2)
    pygame.draw.circle(canvas, palette['b_mid'],
                       (cx - bw // 2 - 1, cy), 1)
    pygame.draw.circle(canvas, palette['b_darkest'],
                       (cx + bw // 2 + 1, cy), 2)
    pygame.draw.circle(canvas, palette['b_mid'],
                       (cx + bw // 2 + 1, cy), 1)


# ═══════════════════════════════════════════════════════
# LEVEL 5: ROYAL CASTLE (+gold trim + portcullis + more banners)
# ═══════════════════════════════════════════════════════
def _render_castle_lvl5(canvas, cx, cy, palette):
    """Royal Castle"""
    _draw_stone_corner_tower(canvas, cx - 52, cy - 12, palette,
                              height=56, has_roof=True,  # dari 68
                              has_gold_spire=True,
                              has_gold_trim=True)
    _draw_stone_corner_tower(canvas, cx + 52, cy - 12, palette,
                              height=56, has_roof=True,
                              has_gold_spire=True,
                              has_gold_trim=True)

    _draw_central_stone_wall(canvas, cx, cy, palette,
                              width=72, height=60,  # dari 86, 70
                              has_gate=True,
                              has_battlements=True)

    _draw_central_gate_roof(canvas, cx, cy - 58, palette,
                             width=30, has_gold_spire=True)

    _draw_wall_gold_band(canvas, cx, cy - 18, palette, width=72)

    _draw_silver_shield_emblem(canvas, cx, cy - 40, palette)

    _draw_hanging_banner(canvas, cx - 20, cy - 40, palette, side='left')
    _draw_hanging_banner(canvas, cx + 20, cy - 40, palette, side='right')

    _overlay_portcullis(canvas, cx, cy, palette, gate_w=16)

def _overlay_portcullis(canvas, cx, cy, palette, gate_w=18):
    """Draw iron portcullis bars over gate"""
    gate_bottom = cy - 8  # Adjust based on wall
    gate_h = 26
    gy = gate_bottom - gate_h

    for bar_x in range(cx - gate_w // 2 + 2, cx + gate_w // 2, 3):
        # Vertical bar
        pygame.draw.rect(canvas, palette['m_darkest'],
                         (bar_x, gy + 3, 2, gate_h - 5))
        pygame.draw.rect(canvas, palette['m_dark'],
                         (bar_x, gy + 3, 1, gate_h - 5))
        pygame.draw.rect(canvas, palette['m_light'],
                         (bar_x, gy + 3, 1, 3))

        # Sharp bottom tip
        pygame.draw.polygon(canvas, palette['m_darkest'], [
            (bar_x, gy + gate_h - 2),
            (bar_x + 1, gy + gate_h),
            (bar_x + 2, gy + gate_h - 2),
        ])


def _draw_wall_gold_band(canvas, cx, cy, palette, width=60):
    """Gold decorative band across wall"""
    # Shadow
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - width // 2 + 1, cy - 1 + 1, width, 6))

    # Base
    pygame.draw.rect(canvas, palette['b_darkest'],
                     (cx - width // 2, cy - 2, width, 6))
    pygame.draw.rect(canvas, palette['b_dark'],
                     (cx - width // 2, cy - 2, width, 5))
    pygame.draw.rect(canvas, palette['b_mid'],
                     (cx - width // 2, cy - 2, width, 3))
    pygame.draw.rect(canvas, palette['b_light'],
                     (cx - width // 2, cy - 2, width, 2))
    pygame.draw.rect(canvas, palette['b_lightest'],
                     (cx - width // 2, cy - 2, width, 1))

    # Studs (round decorations)
    for stud_x in range(-width // 2 + 5, width // 2 - 3, 8):
        pygame.draw.circle(canvas, palette['b_darkest'],
                           (cx + stud_x, cy + 1), 2)
        pygame.draw.circle(canvas, palette['b_dark'],
                           (cx + stud_x, cy + 1), 2)
        pygame.draw.circle(canvas, palette['b_mid'],
                           (cx + stud_x - 1, cy), 1)
        pygame.draw.rect(canvas, palette['b_shine'],
                         (cx + stud_x - 1, cy - 1, 1, 1))


# ═══════════════════════════════════════════════════════
# LEVEL 6: CITADEL (Ultimate + magic + central tower)
# ═══════════════════════════════════════════════════════
def _render_castle_lvl6(canvas, cx, cy, palette):
    """CITADEL - ultimate"""
    _draw_stone_corner_tower(canvas, cx - 56, cy - 12, palette,
                              height=62, has_roof=True,  # dari 75
                              has_gold_spire=True,
                              has_gold_trim=True)
    _draw_stone_corner_tower(canvas, cx + 56, cy - 12, palette,
                              height=62, has_roof=True,
                              has_gold_spire=True,
                              has_gold_trim=True)

    _draw_central_stone_wall(canvas, cx, cy, palette,
                              width=78, height=65,  # dari 92, 76
                              has_gate=True,
                              has_battlements=True)

    _draw_center_royal_tower(canvas, cx, cy - 63, palette)

    _draw_wall_gold_band(canvas, cx, cy - 20, palette, width=78)

    _draw_silver_shield_emblem(canvas, cx, cy - 44, palette)

    _draw_hanging_banner(canvas, cx - 22, cy - 44, palette, side='left')
    _draw_hanging_banner(canvas, cx + 22, cy - 44, palette, side='right')
    _draw_hanging_banner(canvas, cx - 12, cy - 24, palette, side='left')
    _draw_hanging_banner(canvas, cx + 12, cy - 24, palette, side='right')

    _overlay_portcullis(canvas, cx, cy, palette, gate_w=16)

def _draw_center_royal_tower(canvas, cx, cy, palette):
    """Central royal tower - SMALLER"""
    tw = 18  # dari 22
    th = 22  # dari 26
    top = cy - th

    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - tw // 2 + 2, top + 2, tw, th),
                     border_radius=2)

    pygame.draw.rect(canvas, palette['s_edge'],
                     (cx - tw // 2, top, tw, th),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_darkest'],
                     (cx - tw // 2, top, tw - 1, th),
                     border_radius=2)
    pygame.draw.rect(canvas, palette['s_dark'],
                     (cx - tw // 2, top, tw - 3, th - 1),
                     border_radius=1)
    pygame.draw.rect(canvas, palette['s_mid'],
                     (cx - tw // 2 + 1, top, tw - 5, th - 3))
    pygame.draw.rect(canvas, palette['s_light'],
                     (cx - tw // 2 + 1, top, 3, th - 4))
    pygame.draw.rect(canvas, palette['s_lightest'],
                     (cx - tw // 2 + 2, top + 1, 1, th - 6))

    for row in range(th // 6):
        row_y = top + 4 + row * 6
        offset = 4 if row % 2 else 0
        for bx in range(-tw // 2 + 3 + offset, tw // 2 - 2, 7):
            _draw_stone_brick(canvas, cx + bx, row_y, 6, 5, palette)

    for mx in range(-tw // 2, tw // 2 - 1, 4):
        _draw_battlement_stone(canvas, cx + mx, top - 5, 3, 6, palette)

    _draw_blue_conical_roof(canvas, cx, top - 5, tw, palette,
                             has_gold_spire=True,
                             has_gold_trim=True)
# ═══════════════════════════════════════════════════════
# DYNAMIC EFFECTS
# ═══════════════════════════════════════════════════════

_CASTLE_SCALED_CACHE = {}


def _render_dynamic_effects_direct(surface, castle, palette,
                                   off_x, off_y, scale):
    """Efek dinamis kastil langsung ke layar (tanpa canvas + skala)."""
    lvl = castle.level
    if lvl < 4:
        return
    timer = castle.timer
    cw, ch = 180, 160
    cx = int(off_x + (cw // 2) * scale)
    cy_base = int(off_y + (ch - 45) * scale)
    if lvl >= 4:
        _draw_gate_torch(surface, cx - int(16 * scale),
                         cy_base - int(5 * scale), timer, palette)
        _draw_gate_torch(surface, cx + int(16 * scale),
                         cy_base - int(5 * scale), timer, palette,
                         offset=5)
    if lvl >= 6:
        _draw_castle_magic_aura(surface, cx, cy_base - int(40 * scale),
                                palette, timer)


def _render_dynamic_effects(canvas, castle, palette):
    """Torches + magic aura per level"""
    lvl = castle.level
    timer = castle.timer
    cw, ch = canvas.get_size()
    cx = cw // 2
    cy_base = ch - 45

    # ═══ TORCHES di pillar gate (lvl 4+) ═══
    if lvl >= 4:
        # Left torch
        _draw_gate_torch(canvas, cx - 16, cy_base - 5, timer, palette)
        # Right torch
        _draw_gate_torch(canvas, cx + 16, cy_base - 5, timer, palette,
                         offset=5)

    # Magic aura (lvl 6)
    if lvl >= 6:
        _draw_castle_magic_aura(canvas, cx, cy_base - 40, palette, timer)


def _draw_gate_torch(canvas, cx, cy, timer, palette, offset=0):
    """Gate torch dengan basket holder + fire (match reference)"""
    # ═══ TORCH BASKET (wooden bowl on pillar) ═══
    # Pillar base
    pygame.draw.rect(canvas, palette['shadow_hard'],
                     (cx - 3 + 1, cy + 1, 6, 8))
    pygame.draw.rect(canvas, palette['s_darkest'],
                     (cx - 3, cy, 6, 8))
    pygame.draw.rect(canvas, palette['s_dark'],
                     (cx - 3, cy, 5, 8))
    pygame.draw.rect(canvas, palette['s_mid'],
                     (cx - 3, cy, 4, 6))
    pygame.draw.rect(canvas, palette['s_light'],
                     (cx - 3, cy, 2, 4))

    # Basket (wooden bowl at top)
    pygame.draw.ellipse(canvas, palette['shadow_hard'],
                        (cx - 4 + 1, cy - 3 + 1, 8, 4))
    pygame.draw.ellipse(canvas, palette['w_darkest'],
                        (cx - 4, cy - 3, 8, 4))
    pygame.draw.ellipse(canvas, palette['w_dark'],
                        (cx - 4, cy - 3, 8, 3))
    pygame.draw.ellipse(canvas, palette['w_mid'],
                        (cx - 3, cy - 3, 6, 2))

    # Metal rim
    pygame.draw.rect(canvas, palette['m_darkest'],
                     (cx - 4, cy - 3, 8, 1))
    pygame.draw.rect(canvas, palette['m_mid'],
                     (cx - 4, cy - 3, 6, 1))
    pygame.draw.rect(canvas, palette['m_light'],
                     (cx - 4, cy - 3, 3, 1))

    # ═══ BIG FLAME animated ═══
    flicker = int((timer * 0.4 + offset) % 5)
    fire_h = 12 + flicker

    # Outer flame (dark red base)
    pygame.draw.polygon(canvas, palette['f_dark'], [
        (cx - 5, cy - 3),
        (cx - 2, cy - fire_h + 2),
        (cx, cy - fire_h - 2),
        (cx + 2, cy - fire_h + 2),
        (cx + 5, cy - 3),
    ])

    # Mid flame (orange)
    pygame.draw.polygon(canvas, palette['f_mid'], [
        (cx - 4, cy - 4),
        (cx - 1, cy - fire_h + 3),
        (cx, cy - fire_h - 1),
        (cx + 1, cy - fire_h + 3),
        (cx + 4, cy - 4),
    ])

    # Inner flame (yellow)
    pygame.draw.polygon(canvas, palette['f_light'], [
        (cx - 2, cy - 5),
        (cx, cy - fire_h + 4),
        (cx + 2, cy - 5),
    ])

    # Hot core
    pygame.draw.rect(canvas, palette['f_hot'],
                     (cx, cy - fire_h + 4, 1, fire_h - 6))
    pygame.draw.rect(canvas, palette['shine'],
                     (cx, cy - fire_h + 5, 1, 3))

    # ═══ BIG GLOW ═══
    glow_surf = pygame.Surface((36, 40), pygame.SRCALPHA)
    for r in range(18, 3, -2):
        alpha = 50 - r * 2
        if alpha > 0:
            pygame.draw.circle(glow_surf,
                               (*palette['f_mid'][:3], alpha),
                               (18, 20), r)
    canvas.blit(glow_surf, (cx - 18, cy - 20))

    # Rising sparks
    for spark_i in range(3):
        spark_phase = (timer * 0.3 + spark_i * 4 + offset) % 15
        sy = cy - fire_h - int(spark_phase)
        sx = cx + int(math.sin(timer * 0.2 + spark_i) * 3)
        alpha = max(0, 200 - int(spark_phase * 15))
        if alpha > 0:
            pygame.draw.rect(canvas, palette['f_light'], (sx, sy, 1, 1))
            pygame.draw.rect(canvas, palette['f_hot'], (sx, sy, 1, 1))


def _draw_castle_magic_aura(canvas, cx, cy, palette, timer):
    """Magic aura around whole castle (lvl 6)"""
    pulse = math.sin(timer * 0.05) * 0.3 + 0.7

    # Multiple aura layers
    for r in range(90, 30, -8):
        alpha = int((90 - r) * 2 * pulse)
        if alpha > 0:
            aura_surf = pygame.Surface((r * 2, r), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf,
                                (*palette['a_light'][:3], alpha),
                                (0, 0, r * 2, r))
            canvas.blit(aura_surf, (cx - r, cy - r // 2))

    # Floating magic particles
    for i in range(8):
        angle = timer * 0.03 + i * (math.pi / 4)
        radius = 60 + int(math.sin(timer * 0.05 + i) * 8)
        px = cx + int(math.cos(angle) * radius)
        py = cy + int(math.sin(angle) * radius // 2)

        # Sparkle
        pygame.draw.rect(canvas, palette['a_lightest'], (px, py, 2, 2))
        pygame.draw.rect(canvas, palette['shine'], (px, py, 1, 1))

        # Cross sparkle
        pygame.draw.rect(canvas, palette['a_light'], (px - 1, py, 1, 1))
        pygame.draw.rect(canvas, palette['a_light'], (px + 2, py, 1, 1))
        pygame.draw.rect(canvas, palette['a_light'], (px, py - 1, 1, 1))
        pygame.draw.rect(canvas, palette['a_light'], (px, py + 2, 1, 1))



# ================================


# ====================================================================
# hero.py
# ====================================================================

# ================================
# HERO.PY
# ================================

import pygame
import math
from _system import SoundManager


# Cache kecil untuk surface UI hero yang nilainya jarang berubah
# (teks HEAL, ring range, dll.) - hindari alokasi Surface tiap frame.
_HERO_UI_CACHE = {}


class Hero(TowerDebuffMixin):
    # ── Property: skill_damage dipotong saat kena debuff Mage Tower ──
    # Semua skill (274 call site di hero_skills/ + Blade Fury di sini)
    # MEMBACA self.skill_damage, jadi debuff otomatis berlaku ke semua.
    @property
    def skill_damage(self):
        base = self._skill_damage_value
        if getattr(self, 'skill_down_timer', 0) > 0:
            f = max(0.0, 1.0 - getattr(self, 'skill_down_amount', 0.0))
            return int(round(base * f))
        return base

    @skill_damage.setter
    def skill_damage(self, value):
        self._skill_damage_value = value

    def __init__(self, hero_type, team, x=None, y=None):
        self.hero_type = hero_type
        self.team = team

        all_hero_types = get_all_hero_types()
        stats = all_hero_types[hero_type]
        self.name = stats["name"]
        self.title = stats["title"]
        self.role = stats["role"]
        self.description = stats["description"]

        self.base_hp = stats["hp"]
        self.base_damage = stats["damage"]
        self.speed = stats["speed"]
        self.range = stats["range"]
        self.attack_cooldown = stats["attack_cooldown"]

        self.color = stats["color"]
        self.color_dark = stats["color_dark"]

        self.skill_name = stats["skill_name"]
        self.skill_desc = stats["skill_desc"]
        self.skill_cooldown_max = stats["skill_cooldown"]
        self.skill_damage_base = stats["skill_damage"]
        self.skill_range = stats["skill_range"]
        self.skill_data = stats

        self.level = 1
        self._apply_level_stats()

        if x is None:
            if team == "blue":
                self.x = float(BLUE_BASE_X + 60)
                self.y = float(BLUE_BASE_Y - 30)
            else:
                self.x = float(RED_BASE_X - 60)
                self.y = float(RED_BASE_Y + 30)
        else:
            self.x = float(x)
            self.y = float(y)

        self.alive = True
        self.attack_timer = 0
        self.skill_timer = 0
        self.target = None
        self.radius = 16

        self.destination = None
        # ═══ JENIS DESTINATION ═══
        # False = perintah manual pemain (ketuk peta) - WAJIB ditaati.
        # True  = dipasang otak AI (mis. _assign_hero_lane) - BOLEH
        #         dibatalkan begitu ada musuh dalam aggro range,
        #         supaya hero AI tidak "berjalan ke titik tertentu
        #         dulu baru peduli target".
        self.destination_auto = False
        self.follow_target = None

        self.skill_active = False
        self.skill_active_timer = 0

        self.selected = False
        self.facing = 1 if team == "blue" else -1
        self.pulse = 0

        # ═══ VISUAL SKILL STATE (dibaca renderer heroes/*.py) ═══
        # Renderer pakai ini untuk memutuskan efek Q/W/E/R mana
        # yang digambar. Di-set oleh BaseSkill._set_active_skill().
        self.active_skill = None
        self.active_skill_timer = 0

        self.kills = 0
        self.deaths = 0
        # ═══ PROJECTILE SYSTEM (untuk ranged heroes) ═══
        self.projectiles = []
        # ═══ AUTO-CAST SETTINGS ═══
        # ═══ AUTO-CAST SELALU AKTIF (v27) ═══
        # Dulu default False dan pemain harus menekan Q/W/E/R sendiri.
        # Di layar sentuh itu merepotkan: empat tombol besar menutupi
        # sudut kanan bawah sementara jari yang sama dipakai menggeser
        # peta. Semua skill sekarang dicor otomatis oleh
        # _try_auto_cast(), yang hanya menembak kalau ADA musuh hidup
        # di dalam skill_range - jadi tidak ada skill terbuang.
        self.auto_cast_enabled = True
        # Pemeriksaan auto-cast dijadwal ulang tiap 20 langkah simulasi
        # (~0,33 detik). Dulu 40 langkah; terlalu lambat begitu skill
        # jadi satu-satunya jalur serangan khusus.
        self.auto_cast_check_timer = 0
        # ═══ UNIVERSAL SKILL STATE (BALANCED) ═══
        self.w_cooldown = 0
        self.w_cooldown_max = 240  # 4 detik (dari 3)
        self.e_cooldown = 0
        self.e_cooldown_max = 420  # 7 detik (dari 5)
        self.r_cooldown = 0
        self.r_cooldown_max = 900  # 15 detik (dari 10)

        # ═══ INIT SKILL HANDLER (delegate to hero_skills/) ═══
        from hero_skills import get_skill_handler
        self.skills = get_skill_handler(hero_type, self)
        if self.skills:
            self.skills.init_state()

        # ═══ AGGRO / HUNT / HEAL SETTINGS ═══
        # hunt_range: radius hero mencari target saat menganggur.
        # Dulu 600 - lebarnya cuma separuh peta, jadi hero yang baru
        # di-summon sering "berjalan ke titik tertentu" (dorongan
        # PUSH ke base musuh) dulu sebelum menyadari ada target.
        # 900 menutupi hampir seluruh area bermain (diagonal penuh
        # peta ≈ 1200 px), tapi hero di base sendiri tetap TIDAK
        # mengejar minion yang baru spawn di base musuh (jarak
        # base-ke-base 1199 px > 900) - tidak ada bunuh diri
        # menembus map.
        self.hunt_range = 900
        self.aggro_range = 250
        self.retreat_hp_ratio = 0.20       # mulai retreat saat HP < 20%
        self.heal_target_ratio = 0.80      # heal sampai 80% baru keluar lagi
        self.base_heal_rate = 3.0          # HP regen per frame saat di base
        self.passive_heal_rate = 0.15      # HP regen per frame di luar base (sangat kecil)
        self.is_retreating = False         # flag retreat state

        # ═══ DEBUFF MENARA (Ice/Mage/Cannon) ═══
        # Berlaku untuk hero starter maupun hero unlock (boss hero),
        # baik hero pemain maupun hero AI enemy.
        self._init_tower_debuffs()

    def _apply_level_stats(self):
        # Safety clamp level
        if self.level > MAX_HERO_LEVEL:
            self.level = MAX_HERO_LEVEL

        lvl_data = HERO_LEVELS[self.level]

        self.max_hp = int(self.base_hp * lvl_data["hp_mult"])
        self.damage = int(self.base_damage * lvl_data["dmg_mult"])
        self.skill_damage = int(self.skill_damage_base * lvl_data["skill_mult"])

        if not hasattr(self, 'hp'):
            self.hp = self.max_hp
        else:
            old_max = getattr(self, '_prev_max_hp', self.max_hp)
            hp_gained = self.max_hp - old_max
            self.hp = min(self.max_hp, self.hp + hp_gained)

        self._prev_max_hp = self.max_hp

    def upgrade(self):
        if self.level >= MAX_HERO_LEVEL:
            return False
        self.level += 1
        self._apply_level_stats()
        return True

    def upgrade_cost(self):
        if self.level >= MAX_HERO_LEVEL:
            return 0
        base = HERO_LEVELS[self.level]["upgrade_cost"]
        # BOSS HERO (unlock) UPGRADE LEBIH MAHAL daripada starter hero.
        # Berlaku sama untuk pemain & AI (parity).
        if self.skill_data.get("is_boss_hero"):
            base = int(base * BOSS_HERO_UPGRADE_COST_MULT)
        return base

    def move_to(self, x, y, auto=False):
        self.destination = (x, y)
        self.destination_auto = bool(auto)
        self.follow_target = None
        # Player command overrides retreat
        self.is_retreating = False

    def cast_skill(self, all_units, all_towers, all_bases,
                   skill_key='q'):
        """
        Cast skill - delegate ke skill handler.

        Args:
            all_units: list semua unit
            all_towers: list semua tower
            all_bases: list semua base/castle
            skill_key: 'q', 'w', 'e', atau 'r'

        Returns:
            True kalau skill berhasil cast, False kalau di-cooldown
        """
        if not self.skills:
            # Safety: kalau tidak ada handler (misal hero type baru)
            print(f"[WARNING] No skill handler for {self.hero_type}")
            return False

        # Delegate ke handler
        if skill_key == 'q':
            return self.skills.cast_q(all_units, all_towers, all_bases)
        elif skill_key == 'w':
            return self.skills.cast_w(all_units, all_towers, all_bases)
        elif skill_key == 'e':
            return self.skills.cast_e(all_units, all_towers, all_bases)
        elif skill_key == 'r':
            return self.skills.cast_r(all_units, all_towers, all_bases)

        return False
    # ═══════════════════════════════════════
    # ENEMY DETECTION
    # ═══════════════════════════════════════

    def _get_all_enemies(self, all_units, all_towers, all_bases):
        enemies = []
        for u in all_units:
            if u.team != self.team and u.alive:
                enemies.append(u)
        for t in all_towers:
            if t.team != self.team and t.alive:
                enemies.append(t)
        for b in all_bases:
            if b.team != self.team and b.alive:
                enemies.append(b)
        return enemies

    def _find_attack_target(self, enemies):
        """Cari musuh dalam attack range"""
        best = None
        best_dist = self.range
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= best_dist:
                best_dist = dist
                best = e
        return best

    def _find_hunt_target(self, enemies):
        """
        Cari target TERDEKAT tanpa peduli tipe.
        Prioritas murni: jarak terdekat dari hero.
        """
        best = None
        best_dist = self.hunt_range

        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist < best_dist:
                best_dist = dist
                best = e

        return best

    def _find_aggro_target(self, enemies):
        """Cari musuh TERDEKAT dalam aggro_range.

        Dipakai untuk MEMBATALKAN destination auto (perintah dari
        otak AI, bukan ketukan pemain) begitu ada musuh yang
        cukup dekat - supaya hero AI langsung menyergap target
        di jalannya, bukan berbaris dulu ke titik tujuan.
        """
        best = None
        best_dist = self.aggro_range
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist <= best_dist:
                best_dist = dist
                best = e
        return best

    def count_enemies_in_range(self, all_units, all_towers, all_bases,
                                range_val=None):
        if range_val is None:
            range_val = self.skill_range
        enemies = self._get_all_enemies(all_units, all_towers, all_bases)
        count = sum(1 for e in enemies
                    if math.hypot(e.x - self.x, e.y - self.y) <= range_val)
        return count

    # ═══════════════════════════════════════
    # HELPER
    # ═══════════════════════════════════════

    def _get_base_pos(self):
        if self.team == "blue":
            return BLUE_BASE_X, BLUE_BASE_Y
        else:
            return RED_BASE_X, RED_BASE_Y

    def _is_near_base(self):
        """Cek apakah hero dekat base sendiri"""
        bx, by = self._get_base_pos()
        return math.hypot(self.x - bx, self.y - by) < 100

    def _heal_at_base(self):
        """Heal hero saat di dekat base"""
        if self._is_near_base() and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.base_heal_rate)

    def _passive_heal(self):
        """Passive regen sangat kecil di luar base"""
        if self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.passive_heal_rate)

    def _move_toward(self, tx, ty):
        """Bergerak menuju titik tertentu"""
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            # _eff_speed: movement melambat saat kena slow Ice Tower
            sp = self._eff_speed()
            self.x += sp * dx / dist
            self.y += sp * dy / dist
            self.facing = 1 if dx > 0 else -1

    # ═══════════════════════════════════════
    # UPDATE (AGGRESSIVE + HEAL + RETREAT FIX)
    # ═══════════════════════════════════════

    def update(self, all_units, all_towers, all_bases):
        if not self.alive:
            return

        self.pulse += 0.1
        # ═══ TICK DEBUFF MENARA (Ice/Mage/Cannon) ═══
        self._tick_tower_debuffs()
        # ═══ AUTO-CAST SKILLS (jika enabled) ═══
        if self.auto_cast_enabled:
            self.auto_cast_check_timer -= 1
            if self.auto_cast_check_timer <= 0:
                self.auto_cast_check_timer = 20
                self._try_auto_cast(all_units, all_towers, all_bases)
        if self.skill_timer > 0:
            self.skill_timer -= 1
        # ═══ UPDATE PROJECTILES ═══
        # Projectile homing: tiap frame arah dihitung ulang ke posisi
        # target terbaru (tx, ty) lalu angle disimpan & dipakai renderer
        # supaya selalu terarah ke target (fix "projectile tidak terarah").
        for proj in self.projectiles:
            if not proj['alive']:
                continue

            target = proj['target']
            if target is None or not getattr(target, 'alive', False):
                proj['alive'] = False
                continue

            proj['age'] = proj.get('age', 0) + 1

            # Homing tiap frame ke target yang bergerak
            tx = target.x
            ty = target.y
            dx = tx - proj['x']
            dy = ty - proj['y']
            dist = math.hypot(dx, dy)

            # Simpan angle (dipakai renderer utk orientasi ujung)
            if dist > 0:
                proj['angle'] = math.atan2(dy, dx)

            if dist < proj['speed'] + 5:
                # HIT! (hanya damage > 0 yang mengenai target & bersuara;
                # projectile visual-only skill damage=0 diam saja)
                if proj['damage'] > 0:
                    target.take_damage(proj['damage'], proj['team'])

                    # Suara hentakan proyektil (panah/sihir hero ranged).
                    # Dulu TIDAK ada sama sekali - serangan jarak jauh
                    # hero terdengar bisu saat mengenai sasaran.
                    try:
                        SoundManager().play('bullet_hit', volume_mult=0.6)
                    except Exception:
                        pass

                    # Visual feedback
                    if proj['is_crit']:
                        try:
                            import __main__
                            if hasattr(__main__, 'game_instance'):
                                game = __main__.game_instance
                                game.effects.add_damage_number(
                                    target.x, target.y - 30,
                                    f"CRIT!", is_critical=True)
                        except Exception:
                            pass
                proj['alive'] = False
            else:
                proj['x'] += proj['speed'] * dx / dist
                proj['y'] += proj['speed'] * dy / dist

        # Clean dead projectiles
        self.projectiles = [p for p in self.projectiles if p['alive']]

        if self.attack_timer > 0:
            self.attack_timer -= 1

        # ═══ VISUAL SKILL TIMER (untuk renderer) ═══
        if self.active_skill_timer > 0:
            self.active_skill_timer -= 1
            if self.active_skill_timer <= 0:
                self.active_skill = None

        # ═══ UNIVERSAL SKILL COOLDOWNS ═══
        if self.w_cooldown > 0:
            self.w_cooldown -= 1
        if self.e_cooldown > 0:
            self.e_cooldown -= 1
        if self.r_cooldown > 0:
            self.r_cooldown -= 1

        # ═══ HERO-SPECIFIC TIMERS ═══
        if self.skills:
            self.skills.update_timers(all_units, all_towers, all_bases)
        # ─── Passive heal (sangat kecil, selalu aktif) ───
        self._passive_heal()

        # ─── Blade Fury active skill ───
        if self.skill_active:
            self.skill_active_timer -= 1
            if self.skill_active_timer <= 0:
                self.skill_active = False
            else:
                if self.skill_active_timer % 15 == 0:
                    enemies = self._get_all_enemies(
                        all_units, all_towers, all_bases)
                    for e in enemies:
                        dist = math.hypot(e.x - self.x, e.y - self.y)
                        if dist <= self.skill_data["skill_range"]:
                            e.take_damage(self.skill_damage, self.team)

        # ─── Validasi follow_target ───
        if self.follow_target:
            if not self.follow_target.alive or \
               self.follow_target.team == self.team:
                self.follow_target = None

        # ─── Get semua musuh ───
        enemies = self._get_all_enemies(all_units, all_towers, all_bases)

        # ═══════════════════════════════════════
        # RETREAT LOGIC (dengan heal di base)
        # ═══════════════════════════════════════

        hp_ratio = self.hp / self.max_hp

        # Masuk retreat mode saat HP rendah
        if hp_ratio < self.retreat_hp_ratio:
            self.is_retreating = True

        # Keluar retreat mode saat HP sudah cukup tinggi
        if self.is_retreating and hp_ratio >= self.heal_target_ratio:
            self.is_retreating = False

        # ═══════════════════════════════════════
        # STATE PRIORITY:
        # 1. RETREAT + HEAL (HP rendah → base → heal → kembali)
        # 2. PLAYER COMMAND: destination (klik map)
        # 3. PLAYER COMMAND: follow_target (klik musuh)
        # 4. ATTACK (musuh dalam attack range)
        # 5. HUNT (kejar musuh terdekat di map)
        # 6. PUSH (maju ke arah base musuh)
        # ═══════════════════════════════════════

        # ── 1. RETREAT + HEAL ──
        if self.is_retreating:
            base_x, base_y = self._get_base_pos()

            if self._is_near_base():
                # Di base: HEAL cepat
                self._heal_at_base()

                # Sambil heal, tetap serang musuh yang masuk range
                attack_target = self._find_attack_target(enemies)
                if attack_target:
                    self.target = attack_target
                    self._do_attack()
                else:
                    self.target = None
            else:
                # Belum sampai base: jalan ke base
                self.target = None
                self._move_toward(base_x, base_y)

                # Sambil retreat, tetap serang musuh dalam range
                attack_target = self._find_attack_target(enemies)
                if attack_target:
                    self.target = attack_target
                    self._do_attack()
            return

        # ── 2. COMMAND: move to destination ──
        # ═══ FIX: destination AUTO dibatalkan oleh aggro ═══
        # BUG LAMA: destination (yang dipasang otak AI lewat
        # _assign_hero_lane) diprioritaskan di atas SEMUA state
        # combat. Hero AI jadi berbaris lurus ke titik lane
        # (mis. x=600 atau posisi minion saat itu) sambil melewati
        # musuh-musuh di sekitarnya, dan BARU mulai mengejar target
        # setelah sampai di titik itu - persis keluhan
        # "hero pergi ke tempat tertentu dulu baru ke target".
        # Sekarang: kalau destination datang dari AI (auto) dan ada
        # musuh dalam aggro_range, destination dibuang dan hero
        # langsung lanjut ke state ATTACK/HUNT di frame yang sama.
        # Destination MANUAL (ketukan pemain) tetap ditaati penuh.
        if self.destination and self.destination_auto:
            if self._find_aggro_target(enemies) is not None:
                self.destination = None
                self.destination_auto = False

        if self.destination:
            dx = self.destination[0] - self.x
            dy = self.destination[1] - self.y
            dist = math.hypot(dx, dy)

            if dist < self.speed:
                self.x, self.y = self.destination
                self.destination = None
                self.destination_auto = False
            else:
                sp = self._eff_speed()
                self.x += sp * dx / dist
                self.y += sp * dy / dist
                self.facing = 1 if dx > 0 else -1

            # Sambil jalan, tetap serang musuh dalam range
            attack_target = self._find_attack_target(enemies)
            if attack_target:
                self.target = attack_target
                self._do_attack()
            return

        # ── 3. PLAYER COMMAND: follow & attack target ──
        if self.follow_target:
            self.target = self.follow_target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)

            if dist <= self.range:
                self.facing = 1 if dx > 0 else -1
                self._do_attack()
            else:
                sp = self._eff_speed()
                self.x += sp * dx / dist
                self.y += sp * dy / dist
                self.facing = 1 if dx > 0 else -1
            return

        # ── 4. ATTACK musuh dalam range ──
        attack_target = self._find_attack_target(enemies)
        if attack_target:
            self.target = attack_target
            dx = attack_target.x - self.x
            dy = attack_target.y - self.y
            self.facing = 1 if dx > 0 else -1
            self._do_attack()
            return

        # Kalau sudah punya target yang masih hidup dan dekat, TETAP kejar
        if self.target and self.target.alive:
            current_dist = math.hypot(
                self.target.x - self.x, self.target.y - self.y)
            # Hanya ganti target kalau target baru JAUH lebih dekat (>50 px)
            new_hunt = self._find_hunt_target(enemies)
            if new_hunt and new_hunt != self.target:
                new_dist = math.hypot(
                    new_hunt.x - self.x, new_hunt.y - self.y)
                if new_dist < current_dist - 50:
                    self.target = new_hunt
            # Kejar target saat ini
            hunt_target = self.target
        else:
            hunt_target = self._find_hunt_target(enemies)

        if hunt_target:
            self.target = hunt_target
            dx = hunt_target.x - self.x
            dy = hunt_target.y - self.y
            dist = math.hypot(dx, dy)

            if dist <= self.range:
                self.facing = 1 if dx > 0 else -1
                self._do_attack()
            else:
                sp = self._eff_speed()
                self.x += sp * dx / dist
                self.y += sp * dy / dist
                self.facing = 1 if dx > 0 else -1
            return

        # ── 6. PUSH ke base musuh ──
        self.target = None
        if self.team == "blue":
            push_x, push_y = RED_BASE_X, RED_BASE_Y
        else:
            push_x, push_y = BLUE_BASE_X, BLUE_BASE_Y

        dx = push_x - self.x
        dy = push_y - self.y
        dist = math.hypot(dx, dy)

        if dist > 80:
            sp = self._eff_speed()
            self.x += sp * 0.6 * dx / dist
            self.y += sp * 0.6 * dy / dist
            self.facing = 1 if dx > 0 else -1

    def _try_auto_cast(self, all_units, all_towers, all_bases):
        """
        Smart auto-cast skills berdasarkan situasi.

        ATURAN KETAT (anti buang skill ke area kosong):
        - Skill APAPUN hanya di-cast kalau ada musuh hidup dalam
          skill_range hero. Tidak ada musuh dekat = tidak cast sama
          sekali (tidak spam, tidak ada efek ke tempat kosong).
        - Target diambil dari musuh TERDEKAT dalam skill_range,
          bukan target serangan (yang bisa di luar skill_range).
        """
        # ═══ MUSUH DALAM SKILL RANGE ═══
        enemies = self._get_all_enemies(
            all_units, all_towers, all_bases)
        nearby = []
        for e in enemies:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d <= self.skill_range:
                nearby.append((d, e))

        # Tidak ada musuh dekat = jangan cast apapun
        if not nearby:
            return

        nearby.sort(key=lambda t: t[0])
        dist, nearest = nearby[0]
        nearby_count = len(nearby)

        # Arahkan target ke musuh terdekat supaya skill pasti kena
        self.target = nearest

        hp_ratio = self.hp / self.max_hp

        # ═══ PRIORITY R (Ultimate) ═══
        # Ultimate tidak boleh menunggu kondisi yang hampir tidak pernah
        # terjadi (3 musuh + HP kritis). Ini penyebab R terlihat tidak
        # pernah dipakai, terutama pada hero summon/boss hero. Selama ada
        # target valid dalam jangkauan dan cooldown siap, gunakan R.
        if self.is_skill_ready('r'):
            if self.cast_skill(all_units, all_towers, all_bases, 'r'):
                return

        # ═══ PRIORITY E ═══
        # Cast E kalau 2+ musuh dekat
        if self.is_skill_ready('e'):
            if nearby_count >= 2:
                self.cast_skill(all_units, all_towers,
                                all_bases, 'e')
                return

        # ═══ PRIORITY W ═══
        # Cast W kalau HP rendah (defensive) - tetap wajib ada musuh
        # dekat supaya tidak "buang" efek ke tempat kosong.
        if self.is_skill_ready('w'):
            if hp_ratio < 0.4:
                self.cast_skill(all_units, all_towers,
                                all_bases, 'w')
                return

        # ═══ PRIORITY Q (basic, paling sering) ═══
        # Cast Q kalau ada musuh dalam skill range DAN cooldown ready
        if self.is_skill_ready('q'):
            self.cast_skill(all_units, all_towers,
                            all_bases, 'q')
            return

    def _do_attack(self):
        """Lakukan serangan ke self.target jika dalam range"""
        if not self.target or not self.target.alive:
            return

        dist = math.hypot(self.target.x - self.x,
                           self.target.y - self.y)

        # ═══ VISUAL FEEDBACK saat target out of range ═══
        if dist <= self.range and self.attack_timer == 0:
            # ═══ DAMAGE MODIFIER ═══
            damage = self.damage
            is_crit = False

            if getattr(self, '_crit_buff_active', False):
                damage = int(damage * 2)
                is_crit = True

            # ═══ KUNCI ARAH SERANGAN (anti swing kacau) ═══
            # Dipakai heroes/_adapt_hero_to_boss supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi serangan.
            self._attack_facing = self.facing

            # Boss hero (morgath, ancient_apparition, dll.) render
            # pakai renderer boss yang SUDAH menggambar visual
            # serangannya sendiri (beam petir Morgath, shard es AA,
            # swing kapak Drakar, dll.). Projectile generik kecil
            # dari sistem hero malah bikin efek ganda & terlihat
            # "terpotong" 11px sebelum target. Jadi boss hero
            # serang INSTAN seperti versi boss aslinya.
            is_boss_hero = bool(self.skill_data.get("is_boss_hero"))

            # ═══ RANGED HEROES → spawn projectile ═══
            if self.hero_type in ('sylara', 'vex', 'zephyr',
                                  'morgath', 'ancient_apparition') \
                    and not is_boss_hero:
                self._spawn_projectile(damage, is_crit)
            else:
                # Melee / boss hero → instant damage
                self.target.take_damage(damage, self.team)

                if is_crit:
                    try:
                        import __main__
                        if hasattr(__main__, 'game_instance'):
                            game = __main__.game_instance
                            game.effects.add_damage_number(
                                self.target.x, self.target.y - 30,
                                f"CRIT!", is_critical=True)
                    except Exception:
                        pass

            # Attack cooldown efektif (dipanjangkan saat kena debuff
            # attack-speed dari Ice Tower)
            self.attack_timer = self._eff_attack_cd(self.attack_cooldown)

            # Suara serangan dasar: tebasan (melee) atau
            # petikan busur / lesatan sihir (ranged), dipilih
            # otomatis dari jangkauan hero.
            try:
                from mobile import combat_audio as _ca
                _ca.play_hero_basic(self)
            except Exception:
                pass

            # Visual crit indicator
            if is_crit:
                try:
                    import __main__
                    if hasattr(__main__, 'game_instance'):
                        game = __main__.game_instance
                        game.effects.add_damage_number(
                            self.target.x, self.target.y - 30,
                            f"CRIT!", is_critical=True)
                except Exception:
                    pass

    # ═══════════════════════════════════════
    # DAMAGE & RESPAWN
    # ═══════════════════════════════════════
    def _spawn_projectile(self, damage, is_crit=False, speed=None,
                          target=None, hero_type=None):
        """Spawn projectile homing yang terbang & MENGENAI target.

        Kecepatan default 9.5 (basic attack; dulu 6 terlalu lambat &
        terlihat melayang). Skill memakai 12-13 lewat param ``speed``.
        Tiap frame arah dihitung ulang ke posisi target terbaru
        (homing) jadi projectile selalu terarah & tidak meleset walau
        target bergerak. ``angle`` & ``age`` disimpan supaya renderer
        bisa menggambar ujung tepat di (px,py) mengarah ke target.
        """
        tgt = target if target is not None else self.target
        if tgt is None or not getattr(tgt, 'alive', False):
            return
        if speed is None:
            speed = 9.5

        # Arah awal langsung ke target (bukan facing hero) supaya
        # sejak frame pertama projectile sudah terarah.
        dx = tgt.x - self.x
        dy = (tgt.y - 5) - self.y
        start_angle = math.atan2(dy, dx) if (dx or dy) else 0.0

        self.projectiles.append({
            'x': float(self.x),
            'y': float(self.y - 5),  # sedikit di atas hero
            'target': tgt,
            'damage': damage,
            'speed': float(speed),
            'is_crit': is_crit,
            'alive': True,
            'hero_type': hero_type or self.hero_type,
            'team': self.team,
            'angle': start_angle,
            'age': 0,
        })

    def _spawn_skill_projectile(self, target, speed=13.0, hero_type=None):
        """Spawn projectile skill (visual homing, tanpa damage).

        Dipakai hero_skills supaya skill ranged hero punya visual
        ``terarah``: sebuah projectile homing terbang ke target skill.
        damage = 0 agar TIDAK menumpuk dengan damage instan skill
        (damage otoritatif tetap di hero_skills/_bundle.py); renderer
        update loop melewatkan efek hit saat damage == 0.
        """
        self._spawn_projectile(0, is_crit=False, speed=speed,
                               target=target, hero_type=hero_type)

    def take_damage(self, damage, from_team, damage_type='normal'):
        self.hp -= damage

        # Popup kecil untuk burn (Cannon Tower) supaya pemain sadar
        # hero-nya sedang terbakar. Damage biasa tetap silent seperti
        # desain lama (hero tidak menampilkan damage number).
        if damage_type == 'fire' and self.alive:
            try:
                import __main__
                if hasattr(__main__, 'game_instance'):
                    __main__.game_instance.effects.add_damage_number(
                        self.x, self.y - self.radius - 12,
                        damage, damage_type='fire')
            except Exception:
                pass

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.deaths += 1
            # Bersihkan semua debuff (burn/slow/dll.) saat mati
            self.clear_tower_debuffs()

    def respawn(self):
        # Bersihkan debuff DULU supaya set hp penuh tidak kepotong
        # anti-heal yang tersisa dari kehidupan sebelumnya.
        self.clear_tower_debuffs()
        self.alive = True
        self.hp = self.max_hp
        self.is_retreating = False
        if self.team == "blue":
            self.x = float(BLUE_BASE_X + 60)
            self.y = float(BLUE_BASE_Y - 30)
        else:
            self.x = float(RED_BASE_X - 60)
            self.y = float(RED_BASE_Y + 30)
        self.skill_active = False
        self.skill_timer = 0
        self.follow_target = None
        self.destination = None
        self.destination_auto = False
        self.target = None

        # Reset visual skill state biar efek tidak "nyangkut"
        # kebawa kalau hero mati di tengah cast.
        self.active_skill = None
        self.active_skill_timer = 0

    # ═══════════════════════════════════════
    # DRAWING
    # ═══════════════════════════════════════
    # ================================
    # PATCH untuk hero.py
    # Ganti method draw() yang boros Surface
    # ================================

    def draw(self, surface):
        """Draw hero - OPTIMIZED VERSION"""
        if not self.alive:
            return

        x, y = int(self.x), int(self.y)

        # ═══ SELECTION RING (hanya kalau selected) ═══
        if self.selected:
            # Gunakan circle langsung, bukan full-screen Surface
            pygame.draw.ellipse(surface, YELLOW,
                                (x - self.radius - 3,
                                 y + self.radius - 6,
                                 (self.radius + 3) * 2, 10), 2)

            # Range circle - surface di-cache per (range, color)
            key = ("range", self.range, self.color)
            range_surf = _HERO_UI_CACHE.get(key)
            if range_surf is None:
                range_d = self.range * 2
                range_surf = pygame.Surface((range_d + 4, range_d + 4),
                                            pygame.SRCALPHA)
                r_color = (*self.color, 30)
                border_c = (*self.color, 100)
                pygame.draw.circle(range_surf, r_color,
                                   (self.range + 2, self.range + 2),
                                   self.range)
                pygame.draw.circle(range_surf, border_c,
                                   (self.range + 2, self.range + 2),
                                   self.range, 2)
                _HERO_UI_CACHE[key] = range_surf
            surface.blit(range_surf,
                         (x - self.range - 2, y - self.range - 2))

        # ═══ GROUND SHADOW ═══
        pygame.draw.ellipse(surface, (0, 0, 0, 100),
                            (x - self.radius, y + self.radius - 4,
                             self.radius * 2, 8))

        # ═══ INDIKATOR DEBUFF MENARA (slow ring, burn api, pip ikon) ═══
        self._draw_tower_debuff_fx(surface, x, y, self.radius)

        # ═══ SKILL SPIN EFFECT (kalau active, surface di-cache) ═══
        if self.skill_active:
            spin_r = self.skill_data["skill_range"]
            spin_size = (spin_r + 10) * 2
            cx = spin_size // 2
            # Rotasi dikuantisasi 16 arah - cukup mulus, murah di-blit
            angle_step = int((self.pulse * 2) * 180 / math.pi) % 16
            key = ("spin", spin_r, angle_step)
            spin_surf = _HERO_UI_CACHE.get(key)
            if spin_surf is None:
                spin_surf = pygame.Surface((spin_size, spin_size),
                                           pygame.SRCALPHA)
                for i in range(8):
                    a = angle_step * math.pi / 8 + i * math.pi / 4
                    sx = cx + math.cos(a) * (spin_r - 10)
                    sy = cx + math.sin(a) * (spin_r - 10)
                    pygame.draw.line(spin_surf, (255, 100, 0, 150),
                                     (cx, cx), (int(sx), int(sy)), 3)
                _HERO_UI_CACHE[key] = spin_surf
            surface.blit(spin_surf, (x - cx, y - cx))

        # ═══ HERO SHAPE ═══
        self._draw_hero_shape(surface, x, y)

        # ═══ PROJECTILES ═══
        for proj in self.projectiles:
            if proj['alive']:
                self._draw_projectile(surface, proj)

        # ═══ LABEL ANCHOR ═══
        # Sprite boss-hero jauh lebih tinggi dari self.radius (16).
        # Ukur tinggi sprite asli supaya HP bar / nama / bintang
        # tidak menutupi kepala hero.
        try:
            from heroes import get_sprite_top_offset
            sprite_top = get_sprite_top_offset(self.hero_type)
        except Exception:
            sprite_top = self.radius
        label_anchor = y - max(self.radius, sprite_top) - 6

        # ═══ NAME BADGE DIBANGUN DULUAN ═══
        # Dipindah ke atas blok HP bar supaya posisi papan nama dan
        # indikator HEAL bisa dihitung DARI tinggi badge yang asli.
        # BUG LAMA: badge di-blit di "by - 24" padahal tingginya
        # 12 + (tinggi teks + 4) ≈ 33 px, jadi kotak hitam nama turun
        # sampai ±9 px DI ATAS HP bar dan menutupinya - HP bar hero
        # (termasuk hero musuh) jadi tidak kelihatan sama sekali.
        from _render import get_font
        if getattr(self, '_badge_level', None) != self.level:
            self._build_name_badge(get_font)

        # ═══ HP BAR ═══
        # Sengaja digambar SEBELUM papan nama (lihat blit badge di
        # bawah) dan posisinya jadi jangkar utama semua label.
        bar_w = 45
        bar_h = 6
        bx = x - bar_w // 2
        by = label_anchor

        pygame.draw.rect(surface, (40, 0, 0), (bx, by, bar_w, bar_h))
        hp_ratio = self.hp / self.max_hp
        fill = int(bar_w * hp_ratio)
        if fill > 0:
            hp_color = GREEN if hp_ratio > 0.5 else (
                YELLOW if hp_ratio > 0.25 else RED)
            pygame.draw.rect(surface, hp_color, (bx, by, fill, bar_h))
        pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 1)

        # ═══ PAPAN NAMA + BINTANG: TEPAT di atas HP bar ═══
        badge = getattr(self, '_badge_surf', None)
        badge_top = 0
        if badge is not None:
            # celah 3 px: bawah papan nama TIDAK PERNAH menyentuh
            # HP bar lagi
            badge_top = by - badge.get_height() - 3
            surface.blit(badge,
                         (x - badge.get_width() // 2, badge_top))

        # ═══ RETREAT INDICATOR (surface di-cache) ═══
        # Digambar DI ATAS papan nama (bukan offset tetap yang bisa
        # menimpa HP bar / nama).
        if self.is_retreating:
            retreat_surf = _HERO_UI_CACHE.get("retreat")
            if retreat_surf is None:
                retreat_text = get_font(18).render(
                    "HEAL", True, (100, 255, 100))
                bg_rect = retreat_text.get_rect().inflate(6, 2)
                s = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(s, (0, 60, 0),
                                 s.get_rect(), border_radius=3)
                pygame.draw.rect(s, (100, 255, 100),
                                 s.get_rect(), 1, border_radius=3)
                s.blit(retreat_text, (3, 1))
                _HERO_UI_CACHE["retreat"] = s
                retreat_surf = s
            surface.blit(
                retreat_surf,
                (x - retreat_surf.get_width() // 2,
                 badge_top - 3 - retreat_surf.get_height()))

        # ═══ SKILL COOLDOWN BAR ═══
        if self.skill_timer > 0:
            cd_ratio = 1 - (self.skill_timer / self.skill_cooldown_max)
            pygame.draw.rect(surface, DARK_GRAY, (bx, y + self.radius + 8, 45, 3))
            pygame.draw.rect(surface, ORANGE,
                             (bx, y + self.radius + 8,
                              int(45 * cd_ratio), 3))
        else:
            pygame.draw.rect(surface, YELLOW,
                             (bx, y + self.radius + 8, 45, 3))

    def _build_name_badge(self, get_font):
        """Bangun (ulang) papan nama + bintang level.

        Nama + bintang level digambar SEKALI ke surface kecil lalu
        di-blit tiap frame. Invalidasi otomatis saat level naik
        (draw() memanggil ini hanya kalau _badge_level != level).

        Kotak hitam mengikuti tinggi teks asli (bukan dipatok 14 px),
        dan draw() meletakkannya TEPAT di atas HP bar memakai tinggi
        surface ini - jadi papan nama tidak pernah lagi menutupi
        HP bar.
        """
        font = get_font(14)
        name_lbl = font.render(f"{self.name}", True, WHITE)
        star_w = (self.level * 10) if self.level <= 5 else 18
        bw = max(name_lbl.get_width(), star_w) + 8
        nh = name_lbl.get_height() + 4
        bh = 12 + nh
        badge = pygame.Surface((bw, bh), pygame.SRCALPHA)
        name_box = pygame.Rect(0, bh - nh, bw, nh)
        pygame.draw.rect(badge, (0, 0, 0), name_box, border_radius=2)
        badge.blit(name_lbl, name_lbl.get_rect(center=name_box.center))

        def _star(sx, sy, color=YELLOW):
            pygame.draw.polygon(badge, color, [
                (sx, sy - 3), (sx + 2, sy),
                (sx + 4, sy), (sx + 2, sy + 2),
                (sx + 3, sy + 5), (sx, sy + 3),
                (sx - 3, sy + 5), (sx - 2, sy + 2),
                (sx - 4, sy), (sx - 2, sy),
            ])

        if self.level <= 5:
            for i in range(self.level):
                sx = bw // 2 - (self.level - 1) * 5 + i * 10
                _star(sx, 5)
        else:
            lvl_font = get_font(13)
            lvl_txt = lvl_font.render(f"x{self.level}", True, YELLOW)
            total_w = 9 + lvl_txt.get_width()
            _star(bw // 2 - total_w // 2 + 4, 5)
            badge.blit(lvl_txt, (bw // 2 - total_w // 2 + 11, 0))
        self._badge_surf = badge
        self._badge_level = self.level

    def _draw_projectile(self, surface, proj):
        """Draw projectile berdasarkan hero type.

        Pakai ``angle`` yang sudah dihitung & disimpan saat update
        (homing tiap frame) supaya orientasi ujung selalu mengarah ke
        target. Ujung (tip) digambar TEPAT di (px, py) - bukan
        di-offset dari tengah - jadi projectile terlihat menyentuh
        target saat hit (tidak ``terpotong`` beberapa px sebelum target).
        """
        px = int(proj['x'])
        py = int(proj['y'])

        target = proj['target']
        if target is None or not getattr(target, 'alive', False):
            return

        angle = proj.get('angle', 0.0)
        age = proj.get('age', 0)

        if proj['hero_type'] == 'sylara':
            self._draw_arrow_projectile(surface, px, py, angle)
        elif proj['hero_type'] == 'vex':
            self._draw_magic_orb_projectile(surface, px, py, angle, age)
        elif proj['hero_type'] == 'zephyr':
            self._draw_magic_bolt_projectile(surface, px, py, angle, age)
        elif proj['hero_type'] == 'morgath':
            self._draw_lightning_projectile(surface, px, py, angle, age)
        elif proj['hero_type'] == 'ancient_apparition':
            self._draw_ice_shard_projectile(surface, px, py, angle)
        else:
            # Generic
            pygame.draw.circle(surface, self.color, (px, py), 3)

    def _draw_arrow_projectile(self, surface, px, py, angle):
        """Green arrow projectile (Sylara) - ujung TEPAT di (px,py)."""
        import pygame.gfxdraw

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Ujung (tip) TEPAT di (px, py); badan panah memanjang ke
        # belakang, jadi projectile menyentuh target tepat saat
        # (px,py) sampai - tidak terpotong / melayang di depannya.
        arrow_len = 11

        tip_x = px
        tip_y = py
        tail_x = px - int(cos_a * arrow_len)
        tail_y = py - int(sin_a * arrow_len)

        # ─── TRAIL (motion blur) ───
        for i in range(4):
            trail_offset = (i + 1) * 4
            trail_x = px - int(cos_a * trail_offset)
            trail_y = py - int(sin_a * trail_offset)
            trail_alpha = 150 - i * 30

            if trail_alpha > 0:
                trail_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf,
                                   (110, 220, 110, trail_alpha),
                                   (3, 3), 2)
                surface.blit(trail_surf,
                             (trail_x - 3, trail_y - 3))

        # ─── SHAFT (wooden) ───
        pygame.draw.line(surface, (100, 65, 30),
                         (tail_x, tail_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, (150, 105, 55),
                         (tail_x, tail_y), (tip_x, tip_y), 1)

        # ─── ARROWHEAD (green glowing) - tip di (px,py) ───
        perp_x = -sin_a
        perp_y = cos_a

        head_pts = [
            (tip_x, tip_y),
            (int(tip_x - cos_a * 5 + perp_x * 3),
             int(tip_y - sin_a * 5 + perp_y * 3)),
            (int(tip_x - cos_a * 5 - perp_x * 3),
             int(tip_y - sin_a * 5 - perp_y * 3)),
        ]

        pygame.draw.polygon(surface, (60, 140, 60), head_pts)
        pygame.draw.polygon(surface, (120, 220, 120), [
            (tip_x, tip_y),
            (int(tip_x - cos_a * 3 + perp_x * 2),
             int(tip_y - sin_a * 3 + perp_y * 2)),
            (int(tip_x - cos_a * 3),
             int(tip_y - sin_a * 3)),
        ])

        try:
            pygame.gfxdraw.aapolygon(surface, head_pts, (100, 200, 100))
        except:
            pass

        # Tip shine
        pygame.draw.rect(surface, (200, 255, 200),
                         (tip_x, tip_y, 1, 1))

        # ─── FLETCHING (green feathers at tail) ───
        for side in [-1, 1]:
            fletch_pts = [
                (tail_x, tail_y),
                (int(tail_x - cos_a * 3 + perp_x * 3 * side),
                 int(tail_y - sin_a * 3 + perp_y * 3 * side)),
                (int(tail_x - cos_a * 4),
                 int(tail_y - sin_a * 4)),
            ]
            pygame.draw.polygon(surface, (80, 160, 80), fletch_pts)

        # ─── GLOW around arrow ───
        glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (100, 220, 100, 80),
                           (8, 8), 6)
        surface.blit(glow_surf, (px - 8, py - 8))

    def _draw_magic_orb_projectile(self, surface, px, py, angle=0.0, age=0):
        """Purple magic orb (Vex) - core di (px,py) + trail belakang."""
        import pygame.gfxdraw

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # ─── TRAIL (jejak orb bercahaya ke arah belakang) ───
        for i in range(5):
            off = (i + 1) * 3
            trail_x = px - int(cos_a * off)
            trail_y = py - int(sin_a * off)
            trail_alpha = 120 - i * 22
            if trail_alpha > 0:
                trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf,
                                   (180, 100, 240, trail_alpha),
                                   (4, 4), max(1, 3 - i // 2))
                surface.blit(trail_surf,
                             (trail_x - 4, trail_y - 4))

        # Glow
        glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        for r in range(6, 0, -1):
            alpha = 200 - r * 25
            if alpha > 0:
                try:
                    pygame.gfxdraw.filled_circle(
                        glow_surf, 8, 8, r,
                        (180, 100, 240, alpha))
                except:
                    pass
        surface.blit(glow_surf, (px - 8, py - 8))

        # Core di (px, py)
        pygame.draw.circle(surface, (220, 180, 255), (px, py), 3)
        pygame.draw.circle(surface, (255, 255, 255), (px, py), 1)

    def _draw_magic_bolt_projectile(self, surface, px, py, angle=0.0, age=0):
        """Pink magic bolt (Zephyr) - core di (px,py) + trail belakang."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # ─── TRAIL (jejak bolt ke arah belakang) ───
        for i in range(5):
            off = (i + 1) * 3
            trail_x = px - int(cos_a * off)
            trail_y = py - int(sin_a * off)
            trail_alpha = 130 - i * 24
            if trail_alpha > 0:
                trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf,
                                   (230, 80, 200, trail_alpha),
                                   (4, 4), max(1, 3 - i // 2))
                surface.blit(trail_surf,
                             (trail_x - 4, trail_y - 4))

        # Glow
        glow_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (230, 80, 200, 120),
                           (7, 7), 5)
        surface.blit(glow_surf, (px - 7, py - 7))

        pygame.draw.circle(surface, (255, 130, 230), (px, py), 3)
        pygame.draw.circle(surface, (255, 255, 255), (px, py), 1)

    def _draw_lightning_projectile(self, surface, px, py, angle, age=0):
        """Lightning bolt (Morgath) - zigzag deterministik sin(age).

        Dulu memakai ``random`` tiap frame -> kilat berkedip/loncat
        acak & terlihat tidak terarah. Sekarang offset memakai
        ``sin(age)`` yang deterministik, jadi kilat stabil & tetap
        mengarah ke target. Titik awal (px,py) = ujung depan.
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Zigzag lightning (deterministik via sin(age))
        points = [(px, py)]
        for i in range(3):
            offset = int(math.sin(age * 0.6 + i * 1.7) * 3)
            nx = px + int(cos_a * (i + 1) * 5) + int(-sin_a * offset)
            ny = py + int(sin_a * (i + 1) * 5) + int(cos_a * offset)
            points.append((nx, ny))

        for i in range(len(points) - 1):
            pygame.draw.line(surface, (100, 130, 240),
                             points[i], points[i + 1], 3)
            pygame.draw.line(surface, (180, 210, 255),
                             points[i], points[i + 1], 1)

        # Glow
        glow_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (140, 180, 255, 120),
                           (7, 7), 5)
        surface.blit(glow_surf, (px - 7, py - 7))

    def _draw_ice_shard_projectile(self, surface, px, py, angle):
        """Ice shard (Ancient Apparition) - ujung TEPAT di (px,py)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        perp_x = -sin_a
        perp_y = cos_a

        # Ujung (tip) di (px, py); shard melebar ke belakang.
        tip_x = px
        tip_y = py
        base_x = px - int(cos_a * 10)
        base_y = py - int(sin_a * 10)

        shard_pts = [
            (tip_x, tip_y),
            (base_x + int(perp_x * 3), base_y + int(perp_y * 3)),
            (base_x, base_y),
            (base_x - int(perp_x * 3), base_y - int(perp_y * 3)),
        ]

        pygame.draw.polygon(surface, (100, 180, 240), shard_pts)
        pygame.draw.polygon(surface, (200, 230, 255), [
            (tip_x, tip_y),
            (base_x + int(perp_x * 2) + int(cos_a * 4),
             base_y + int(perp_y * 2) + int(sin_a * 4)),
            (base_x + int(cos_a * 4),
             base_y + int(sin_a * 4)),
        ])
        pygame.draw.rect(surface, (255, 255, 255), (px, py, 1, 1))

        # Glow
        glow_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (140, 210, 255, 100),
                           (7, 7), 5)
        surface.blit(glow_surf, (px - 7, py - 7))

    # ══════════════════════════════════════
    # BOSS-COMPAT ALIAS
    # Renderer di heroes/ ditulis pakai konvensi Boss
    # (direction / timer). Pakai property supaya selalu
    # sinkron tanpa duplikasi atribut.
    # ══════════════════════════════════════

    @property
    def direction(self):
        """Alias Boss.direction -> Hero.facing"""
        return self.facing

    @direction.setter
    def direction(self, value):
        self.facing = value

    @property
    def timer(self):
        """Alias Boss.timer -> Hero.attack_timer"""
        return self.attack_timer

    @timer.setter
    def timer(self, value):
        self.attack_timer = value

    @property
    def boss_type(self):
        """Alias Boss.boss_type -> Hero.hero_type"""
        return self.hero_type

    def _draw_hero_shape(self, surface, x, y):
        """Draw hero - delegate ke module heroes/"""
        from heroes import render_hero
        render_hero(self.hero_type, surface, self, x, y)

    # ═══════════════════════════════════════
    # SKILL SYSTEM DOCUMENTATION
    # ═══════════════════════════════════════

    def get_skill_cooldowns(self):
        """
        Get cooldowns semua skill dalam dict.
        Useful untuk UI display.

        Returns:
            dict: {'q': ratio, 'w': ratio, 'e': ratio, 'r': ratio}
            ratio: 0.0 (ready) sampai 1.0 (baru cast)
        """
        return {
            'q': self.skill_timer / self.skill_cooldown_max
                 if self.skill_cooldown_max > 0 else 0,
            'w': self.w_cooldown / self.w_cooldown_max
                 if self.w_cooldown_max > 0 else 0,
            'e': self.e_cooldown / self.e_cooldown_max
                 if self.e_cooldown_max > 0 else 0,
            'r': self.r_cooldown / self.r_cooldown_max
                 if self.r_cooldown_max > 0 else 0,
        }

    def is_skill_ready(self, skill_key):
        """Cek apakah skill tertentu ready untuk cast"""
        if skill_key == 'q':
            return self.skill_timer <= 0
        elif skill_key == 'w':
            return self.w_cooldown <= 0
        elif skill_key == 'e':
            return self.e_cooldown <= 0
        elif skill_key == 'r':
            return self.r_cooldown <= 0
        return False


# ====================================================================
# minion.py
# ====================================================================

# MINION.PY - With Procedural Animation
# ================================

import pygame
import math
from _system import SoundManager

class Minion(TowerDebuffMixin):
    def __init__(self, minion_type, team, lane, nexus_level=1, lane_path=None):
        self.minion_type = minion_type
        self.team = team
        self.lane = lane
        self.nexus_level = nexus_level

        stats = MINION_TYPES[minion_type]
        nexus_data = NEXUS_LEVELS[nexus_level]
        scale = nexus_data["minion_scale"]
        self.ai_level = nexus_data["minion_ai_level"]

        self.max_hp = int(stats["hp"] * scale)
        self.hp = self.max_hp
        self.damage = int(stats["damage"] * scale)
        self.speed = stats["speed"] * (1 + (scale - 1) * 0.3)
        self.range = stats["range"]
        self.attack_cooldown = max(10, int(stats["attack_cooldown"] / (1 + (scale - 1) * 0.2)))
        self.gold_reward = int(stats["gold_reward"] * scale)
        self.radius = stats["radius"]
        self.color = stats["color"]
        self.name = stats["name"]
        self.regen = stats.get("regen", 0) * scale
        # Slow effect (dari Ice Tower) + semua debuff menara lain:
        # atk_slow (Ice), skill_down & anti_heal (Mage), burn (Cannon)
        self._init_tower_debuffs()
        self.base_speed = self.speed

        # ═══ WAYPOINT PATHING ═══
        # Simpan path lane untuk follow
        self.lane_path = lane_path if lane_path else []

        # Set spawn position berdasarkan waypoint pertama/terakhir
        if self.lane_path and len(self.lane_path) > 0:
            if team == "blue":
                # Blue mulai dari awal path
                start_x, start_y = self.lane_path[0]
                self.x = float(start_x)
                self.y = float(start_y)
                self.direction = 1
                self.waypoint_index = 0  # target waypoint berikutnya
            else:
                # Red mulai dari akhir path
                start_x, start_y = self.lane_path[-1]
                self.x = float(start_x)
                self.y = float(start_y)
                self.direction = -1
                self.waypoint_index = len(self.lane_path) - 1
        else:
            # Fallback (jika path kosong)
            if team == "blue":
                self.x = float(BLUE_BASE_X + 40)
                self.y = float(BLUE_BASE_Y - 20)
                self.direction = 1
            else:
                self.x = float(RED_BASE_X - 40)
                self.y = float(RED_BASE_Y + 20)
                self.direction = -1
            self.waypoint_index = 0

        # Small random offset agar tidak semua minions overlap
        import random as _rnd
        self.x += _rnd.uniform(-8, 8)
        self.y += _rnd.uniform(-8, 8)

        # Offset berdasarkan lane biar spread
        lane_offset = {"top": -20, "mid": 0, "bot": 20}
        self.y += lane_offset.get(self.lane, 0)

        self.alive = True
        self.timer = 0
        self.target = None

        # ═══ ANIMATION STATE ═══
        self.anim_time = 0             # counter animasi umum
        self.walk_cycle = 0            # untuk walking bounce
        self.is_moving = False         # apakah sedang bergerak
        self.attack_anim_timer = 0     # timer animasi attack
        self.attack_anim_max = 24  # durasi total animasi attack
        self.slash_effects = []  # list slash effect aktif
        self.hurt_flash_timer = 0      # flash putih saat kena damage
        self.prev_hp = self.max_hp     # untuk deteksi damage
        self.spawn_anim = 20           # animasi spawn (grow-in)
        self.death_anim = 0            # animasi kematian
        self.death_started = False

        # Wobble (tetap dipakai untuk kompatibilitas)
        self.wobble = 0
        self.wobble_dir = 1

        # Play spawn sound
        if minion_type == "goblin":
            SoundManager().play('goblin_spawn', volume_mult=0.7)

    def _get_lane_y(self):
        return {
            "top": LANE_Y_TOP,
            "mid": LANE_Y_MID,
            "bot": LANE_Y_BOT,
        }[self.lane]

    def update(self, all_units, all_towers, all_bases):
        if not self.alive:
            # Animasi kematian
            if not self.death_started:
                self.death_started = True
                self.death_anim = 20
            return

        # Tick semua debuff menara (slow, atk_slow, skill_down,
        # anti_heal, burn). Countdown timer dikelola mixin; di sini
        # tinggal pakai hasilnya.
        self._tick_tower_debuffs()

        # Slow movement effect update
        if self.slow_timer > 0:
            self.speed = self.base_speed * (1 - self.slow_amount)
        else:
            self.slow_amount = 0
            self.speed = self.base_speed

        if self.timer > 0:
            self.timer -= 1

        if self.regen > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen)

        # ═══ Update animation state ═══
        self.anim_time += 1

        # Update slash effects
        for slash in self.slash_effects:
            slash['life'] -= 1
        self.slash_effects = [s for s in self.slash_effects if s['life'] > 0]

        # Deteksi damage untuk flash
        if self.hp < self.prev_hp:
            self.hurt_flash_timer = 8
        self.prev_hp = self.hp

        if self.hurt_flash_timer > 0:
            self.hurt_flash_timer -= 1

        # Attack animation countdown
        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= 1

        # Spawn animation countdown
        if self.spawn_anim > 0:
            self.spawn_anim -= 1

        # Reset moving flag (akan di-set true kalau bergerak)
        old_x, old_y = self.x, self.y

        # Wobble (legacy)
        self.wobble += 0.15 * self.wobble_dir
        if abs(self.wobble) > 2:
            self.wobble_dir *= -1

        enemies = self._get_enemies(all_units, all_towers, all_bases)
        self.target = self._find_target_smart(enemies)

        if self.target:
            dist = self._distance_to(self.target)
            if dist <= self.range:
                if self.timer == 0:
                    self.target.take_damage(self.damage, self.team)
                    # Attack cooldown efektif (dipanjangkan saat kena
                    # debuff attack-speed dari Ice Tower)
                    self.timer = self._eff_attack_cd(self.attack_cooldown)
                    self.attack_anim_timer = self.attack_anim_max  # trigger attack anim
                    self._spawn_slash_effect()
                    try:
                        from mobile import combat_audio as _ca
                        _ca.play(_ca.MINION_HIT)
                    except Exception:
                        pass
            else:
                self._move_toward(self.target.x, self.target.y)
        else:
            self._move_forward()

        # Deteksi apakah bergerak (untuk walking animation)
        dx = self.x - old_x
        dy = self.y - old_y
        self.is_moving = math.hypot(dx, dy) > 0.1

        # Update walking cycle
        if self.is_moving:
            self.walk_cycle += 0.25

    def apply_slow(self, amount, duration):
        """Apply slow effect (dari Ice Tower)"""
        # Apply slow terbesar
        if amount > self.slow_amount or self.slow_timer < duration:
            self.slow_amount = amount
            self.slow_timer = duration

    def _spawn_slash_effect(self):
        """Spawn slash effect visual + sound saat attack"""
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            angle = math.atan2(dy, dx)
        else:
            angle = 0 if self.direction > 0 else math.pi

        self.slash_effects.append({
            'life': 12,
            'max_life': 12,
            'angle': angle,
            'distance': self.radius + 8,
        })

        # Suara serangan minion TIDAK dimainkan di sini. Dulu hanya
        # goblin yang berbunyi (slash + teriakan goblin), sehingga
        # orc/troll/undead/dark_rider terdengar bisu. Sekarang SEMUA
        # minion memakai satu suara global yang sama, diputar lewat
        # combat_audio.play(MINION) tepat di blok serangan update().
        # Visual slash effect tetap berlaku untuk semua jenis.

    def _get_enemies(self, all_units, all_towers, all_bases):
        """Nearby enemy lookup; avoids scanning every minion for every minion."""
        radius = self.range + 30
        try:
            from _system import query_enemies_in_range
            enemies = query_enemies_in_range(
                self.x, self.y, radius, self.team)
        except Exception:
            enemies = [u for u in all_units
                       if u.team != self.team and u.alive]

        # Towers and bases are few enough for a direct check. Heroes, minions,
        # and true boss are already indexed in SpatialGrid.
        for entity in list(all_towers) + list(all_bases):
            if entity in enemies or not getattr(entity, "alive", False):
                continue
            if getattr(entity, "team", self.team) == self.team:
                continue
            if math.hypot(entity.x - self.x, entity.y - self.y) <= radius:
                enemies.append(entity)
        return enemies

    def _find_target_smart(self, enemies):
        in_range = []
        for e in enemies:
            dist = self._distance_to(e)
            if dist <= self.range:
                in_range.append((e, dist))

        if not in_range:
            best = None
            best_dist = self.range + 30
            for e in enemies:
                dist = self._distance_to(e)
                if dist < best_dist:
                    best_dist = dist
                    best = e
            return best

        if self.ai_level == 1:
            in_range.sort(key=lambda x: x[1])
            return in_range[0][0]
        elif self.ai_level == 2:
            for e, d in in_range:
                if isinstance(e, Minion) and e.lane == self.lane:
                    return e
            return in_range[0][0]
        elif self.ai_level == 3:
            in_range.sort(key=lambda x: x[0].hp)
            return in_range[0][0]
        elif self.ai_level == 4:
            minion_targets = [(e, d) for e, d in in_range if isinstance(e, Minion)]
            if minion_targets:
                minion_targets.sort(key=lambda x: x[0].hp)
                return minion_targets[0][0]
            in_range.sort(key=lambda x: x[1])
            return in_range[0][0]
        elif self.ai_level == 5:
            base_targets = [(e, d) for e, d in in_range
                            if hasattr(e, 'max_hp') and e.max_hp >= 1500]
            if base_targets:
                return base_targets[0][0]
            tower_targets = [(e, d) for e, d in in_range
                             if hasattr(e, 'tower_kind')]
            if tower_targets:
                tower_targets.sort(key=lambda x: x[0].hp)
                return tower_targets[0][0]
            minion_targets = [(e, d) for e, d in in_range if isinstance(e, Minion)]
            if minion_targets:
                minion_targets.sort(key=lambda x: x[0].hp)
                return minion_targets[0][0]
            return in_range[0][0]

        return in_range[0][0]

    def _distance_to(self, target):
        return math.hypot(target.x - self.x, target.y - self.y)

    def _move_forward(self):
        """Move mengikuti lane waypoints"""
        if not self.lane_path:
            # Fallback: jalan lurus
            self.x += self.speed * self.direction
            return

        # Get target waypoint
        if self.team == "blue":
            # Blue: waypoint index increment (dari awal ke akhir)
            if self.waypoint_index >= len(self.lane_path):
                # Sudah sampai ujung, keep going lurus ke red base
                target_x = RED_BASE_X
                target_y = RED_BASE_Y
            else:
                target_x, target_y = self.lane_path[self.waypoint_index]
        else:
            # Red: waypoint index decrement (dari akhir ke awal)
            if self.waypoint_index < 0:
                target_x = BLUE_BASE_X
                target_y = BLUE_BASE_Y
            else:
                target_x, target_y = self.lane_path[self.waypoint_index]

        # Bergerak ke target waypoint
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        # Kalau sudah dekat waypoint, lanjut ke waypoint berikutnya
        reach_threshold = 15
        if dist < reach_threshold:
            if self.team == "blue":
                self.waypoint_index += 1
            else:
                self.waypoint_index -= 1
            return  # skip movement frame ini

        # Move toward waypoint
        if dist > 0:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def _move_toward(self, tx, ty):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def take_damage(self, damage, from_team, damage_type='normal'):
        self.hp -= damage

        # ═══ TAMBAH: Damage number popup ═══
        # Import dilakukan lazily untuk avoid circular import
        try:
            from _core import Game
            # Access effects via global
            import __main__
            if hasattr(__main__, 'game_instance'):
                game = __main__.game_instance
                is_crit = damage > self.max_hp * 0.2  # 20%+ = crit
                game.effects.add_damage_number(
                    self.x, self.y - self.radius - 5,
                    damage, is_critical=is_crit,
                    damage_type=damage_type)

                # Hit particles
                game.effects.add_hit_particles(
                    self.x, self.y, team=self.team, count=4)
        except Exception:
            pass

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            # Bersihkan semua debuff (burn/slow/dll.) saat mati
            self.clear_tower_debuffs()
            # Suara kematian GLOBAL: semua jenis minion (goblin, orc,
            # troll, undead, dark_rider) memakai satu suara yang sama.
            SoundManager().play('minion_death', volume_mult=0.7)

            # ═══ TAMBAH: Death explosion ═══
            try:
                import __main__
                if hasattr(__main__, 'game_instance'):
                    game = __main__.game_instance
                    game.effects.add_death_explosion(
                        self.x, self.y, team=self.team, size='medium')
            except Exception:
                pass

    def draw(self, surface):
        """Draw minion - OPTIMIZED"""
        if not self.alive:
            if self.death_anim > 0:
                # Cek culling untuk death anim juga
                from _system import FrustumCuller
                if FrustumCuller.is_visible(self.x, self.y, self.radius):
                    self._draw_death_animation(surface)
                    self.death_anim -= 1
            return

        # ← EARLY EXIT: skip draw kalau off-screen
        from _system import FrustumCuller
        if not FrustumCuller.is_visible(self.x, self.y, self.radius):
            return

        x = int(self.x)
        y = int(self.y)

        # ═══ ICE/SLOW EFFECT (kalau di-slow) ═══
        if self.slow_timer > 0:
            # Blue tint aura
            ice_surf = pygame.Surface(
                (self.radius * 3, self.radius * 3), pygame.SRCALPHA)
            pygame.draw.circle(ice_surf, (150, 220, 255, 80),
                               (self.radius * 3 // 2,
                                self.radius * 3 // 2),
                               self.radius + 2)
            surface.blit(ice_surf,
                         (x - self.radius * 3 // 2,
                          y - self.radius * 3 // 2))
            # Ice particles rotating
            for i in range(3):
                angle = self.anim_time * 0.1 + i * 2
                ix = x + int(math.cos(angle) * (self.radius + 3))
                iy = y + int(math.sin(angle) * (self.radius + 3))
                pygame.draw.rect(surface, (200, 240, 255), (ix, iy, 2, 2))

        # ═══ INDIKATOR DEBUFF MENARA (burn api + pip ikon) ═══
        # include_rings=False: aura es minion sudah digambar di atas.
        self._draw_tower_debuff_fx(surface, x, y, self.radius,
                                   include_rings=False)

        # ═══ DELEGATE ke module minions/ (SELALU di-call) ═══
        from minions import render_minion
        render_minion(self.minion_type, surface, self, x, y)

    def _draw_death_animation(self, surface):
        """Death animation - pure code fade out dengan dust"""
        x = int(self.x)
        y = int(self.y)

        progress = 1.0 - (self.death_anim / 20.0)
        alpha = int((1 - progress) * 255)

        if alpha < 10:
            return

        # Fade + shrink + fall
        scale = 1.0 - progress * 0.3
        fall_y = int(progress * 5)

        # ═══ DUST PARTICLES rising ═══
        if self.death_anim > 10:
            for i in range(4):
                angle = i * math.pi / 2
                px = x + int(math.cos(angle) * (20 - self.death_anim) * 2)
                py = y - (20 - self.death_anim) * 2
                r = max(1, self.death_anim // 5)

                # Dust particle
                dust_surf = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
                pygame.draw.circle(dust_surf, (150, 130, 100, alpha),
                                   (r * 3 // 2, r * 3 // 2), r)
                surface.blit(dust_surf, (int(px) - r, int(py) - r))

        # ═══ FADING SILHOUETTE ═══
        body_surf = pygame.Surface((self.radius * 3, self.radius * 3),
                                   pygame.SRCALPHA)
        center = self.radius * 3 // 2

        # Dark body shape (silhouette)
        fade_color = (50, 40, 40, alpha // 2)
        pygame.draw.circle(body_surf, fade_color,
                           (center, center),
                           int(self.radius * scale))

        # Red flash (dying)
        if progress < 0.5:
            red_alpha = int((0.5 - progress) * 300)
            red_alpha = max(0, min(200, red_alpha))
            pygame.draw.circle(body_surf, (255, 50, 50, red_alpha),
                               (center, center),
                               int(self.radius * scale))

        surface.blit(body_surf,
                     (x - center, y - center + fall_y))

        # ═══ SKULL X eyes (khas dead!) ═══
        if progress < 0.7:
            eye_alpha = int((0.7 - progress) * 400)
            eye_alpha = max(0, min(255, eye_alpha))

            eye_surf = pygame.Surface((16, 8), pygame.SRCALPHA)
            # Left X eye
            pygame.draw.line(eye_surf, (255, 255, 255, eye_alpha),
                             (2, 2), (6, 6), 1)
            pygame.draw.line(eye_surf, (255, 255, 255, eye_alpha),
                             (6, 2), (2, 6), 1)
            # Right X eye
            pygame.draw.line(eye_surf, (255, 255, 255, eye_alpha),
                             (10, 2), (14, 6), 1)
            pygame.draw.line(eye_surf, (255, 255, 255, eye_alpha),
                             (14, 2), (10, 6), 1)

            surface.blit(eye_surf, (x - 8, y - 4 + fall_y))




# ================================
# performance.py


# ====================================================================
# ai_player.py
# ====================================================================

# AI_PLAYER.PY
# ================================

import random
import math


class AIPlayer:
    def __init__(self, team="red", level_number=1, enemy_scaling_enabled=False):
        self.team = team
        self.level_number = level_number
        self.enemy_scaling_enabled = enemy_scaling_enabled
        self.gold = STARTING_GOLD

        self.think_timer = AI_THINK_INTERVAL

        self.total_built = 0
        self.total_upgraded = 0
        self.total_sold = 0
        self.total_nexus_upgrades = 0
        self.total_heroes_bought = 0
        self.total_hero_upgrades = 0
        self.total_skills_cast = 0

        self.heroes = []

    def _ai_brain(self):
        """Tingkat kecerdasan DASAR AI: 0.0 (level 1) -> 1.0 (level ~20).

        Mengatur peluang build/upgrade/beli hero. BUKAN batas akhir
        kepintaran AI - lihat _ai_elite() untuk peningkatan di level 20+.
        """
        lvl = max(1, int(getattr(self, "level_number", 1) or 1))
        return min(1.0, (lvl - 1) / 19.0)

    def _ai_elite(self):
        """Tingkat ELITE AI: 0.0 (level 20) -> 1.0 (level terakhir).

        AI terus berkembang MELEBIHI otak dasar setelah level 20:
        berpikir makin cepat & melakukan beberapa aksi sekaligus per
        tick berpikir. Tanpa ini AI akan "stuck" / datar di level 20,
        sehingga level 21-54 terasa membosankan. Rentang elite mengikuti
        jumlah level game (54) supaya kepintaran terus naik sampai akhir.
        Hanya aktif jika enemy_scaling_enabled == True (Hard Mode).
        """
        if not getattr(self, "enemy_scaling_enabled", False):
            return 0.0
        lvl = max(1, int(getattr(self, "level_number", 1) or 1))
        elite_start = 20
        try:
            from levels import get_level_count
            elite_end = max(elite_start + 1, get_level_count())
        except Exception:
            elite_end = 54
        if lvl <= elite_start:
            return 0.0
        return min(1.0, (lvl - elite_start) /
                   max(1, (elite_end - elite_start)))

    def _ai_reserve(self):
        """Gold cadangan AI. HANDICAP DIHAPUS SEPENUHNYA: AI memakai
        SELURUH emasnya untuk semua fitur (build, hero, upgrade,
        Regen Shield), sama seperti pemain - tidak menahan emas sama
        sekali."""
        return 0

    def update(self, all_towers, all_minions, all_heroes, my_nexus,
               all_bases, build_slots=None):
        self._control_heroes(all_minions, all_heroes, all_towers, all_bases)

        self.think_timer -= 1
        if self.think_timer > 0:
            return

        brain = self._ai_brain()
        elite = self._ai_elite()

        # AI makin pintar makin cepat berpikir. AI ELITE (level 20+)
        # berpikir JAUH lebih cepat lagi - lantai interval diturunkan
        # oleh elite - supaya level 21-54 tetap menantang (tidak datar).
        self.think_timer = max(
            8, int(AI_THINK_INTERVAL * (1.0 - 0.65 * brain)
                   - 22 * elite))

        # AI ELITE bisa melakukan beberapa aksi sekaligus per tick
        # berpikir (level 20 = 1 aksi, level terakhir = 3 aksi). Ini
        # membuat AI terus bertambah tangguh sepanjang 50+ level,
        # bukan mentok di level 20.
        actions = 1 + int(round(2 * elite))
        for _ in range(actions):
            if not self._ai_step(all_towers, build_slots,
                                 my_nexus, brain, elite):
                break

    def _ai_step(self, all_towers, build_slots, my_nexus, brain, elite):
        """Satu putar prioritas AI. Return True kalau ada aksi yang
        dilakukan, False kalau tidak ada yang layak dikerjakan.

        Peluang tiap aksi DITINGKATKAN oleh tier ELITE (level 20+)
        supaya AI bertindak lebih pasti / decisive di level tinggi -
        tidak lagi membuang peluang secara acak.
        """
        my_towers = [t for t in all_towers
                     if t.team == self.team and t.alive and t.can_upgrade()]
        all_my_towers = [t for t in all_towers
                         if t.team == self.team and t.alive]

        # Elite menambah peluang setiap aksi (cap 0.98 supaya tetap
        # ada sedikit variasi, bukan robot sempurna).
        def roll(base):
            return random.random() < min(0.98, base + 0.45 * elite)

        # ═══ Priority 0: Build new tower ═══
        if build_slots:
            empty_slots = [s for s in build_slots if not s['taken']]
            if empty_slots and self.gold >= 150:
                if roll(0.4 + 0.45 * brain):
                    if self._try_build_tower(empty_slots):
                        return True

        # Priority 1: Buy hero (maks AI_MAX_HEROES)
        if len(self.heroes) < AI_MAX_HEROES:
            if roll(AI_HERO_BUY_PRIORITY * (0.55 + 0.9 * brain)):
                if self._try_buy_hero():
                    return True

        # Priority 2: Upgrade hero
        if self.heroes and roll(AI_HERO_UPGRADE_PRIORITY
                                * (0.7 + 0.6 * brain)):
            if self._try_upgrade_hero():
                return True

        # Priority 3: Upgrade tower
        if my_towers and roll(AI_UPGRADE_TOWER_CHANCE + 0.5 * brain):
            if self._try_upgrade_tower_new(my_towers):
                return True

        # Priority 3b: Regen Shield (lvl 4+, parity dengan pemain).
        # Pakai SEMUA tower tim karena tower level 6 (max) tetap bisa
        # beli Regen Shield.
        if all_my_towers and self._try_activate_regen_shield(all_my_towers):
            return True

        # Priority 4: Upgrade nexus
        if roll(AI_NEXUS_UPGRADE_PRIORITY * (0.7 + 0.6 * brain)):
            if self._try_upgrade_nexus(my_nexus):
                return True

        return False

    def _try_build_tower(self, empty_slots):
        """AI build tower di slot random"""
        if not empty_slots:
            return False

        cost = 100
        if self.gold < cost + self._ai_reserve():
            return False

        # Pilih slot random
        slot = random.choice(empty_slots)

        # AI preference: variasi tower
        tower_types = ['archer', 'cannon', 'ice', 'mage']
        weights = [0.35, 0.25, 0.20, 0.20]  # archer paling sering
        chosen_type = random.choices(tower_types, weights=weights)[0]

        # Build
        new_tower = Tower(slot['x'], slot['y'], self.team,
                          "outer", slot['lane'])

        if chosen_type != "archer":
            new_tower.tower_type = chosen_type
            new_tower._apply_level_stats()

        # Add ke game (via callback atau langsung)
        self._towers_ref.append(new_tower)  # kita perlu reference
        slot['taken'] = True
        self.gold -= cost
        self.total_built += 1

        return True

    def _try_upgrade_tower_new(self, my_towers):
        """AI upgrade tower - prioritas tower yang paling banyak kill"""
        # Sort by kills (favorite tower dulu)
        my_towers.sort(key=lambda t: -t.kills)

        # AI preference: variasi tower
        # Kalau semua tower level 1, coba upgrade path
        preferred_paths = ["cannon", "ice", "archer", "mage"]

        for tower in my_towers:
            if tower.level == 1:
                # Pilih path random dari preferred
                for path in preferred_paths:
                    cost = tower.upgrade_cost(path)
                    if self.gold >= cost + self._ai_reserve():
                        if tower.upgrade(path):
                            self.gold -= cost
                            self.total_upgraded += 1
                            return True
            else:
                # Upgrade linear
                cost = tower.upgrade_cost()
                if self.gold >= cost + self._ai_reserve():
                    if tower.upgrade():
                        self.gold -= cost
                        self.total_upgraded += 1
                        return True

        return False

    def _try_activate_regen_shield(self, my_towers):
        """AI beli Regen Shield untuk tower yang eligible (lvl 4+, parity)."""
        # Hanya tower level 4+ yang belum punya regen shield.
        candidates = [t for t in my_towers
                      if t.can_activate_regen_shield()]
        if not candidates:
            return False
        # Prioritaskan tower paling banyak kill (paling berharga).
        candidates.sort(key=lambda t: -t.kills)
        for tower in candidates:
            cost = tower.regen_shield_cost()
            if self.gold >= cost + self._ai_reserve():
                if tower.activate_regen_shield():
                    self.gold -= cost
                    return True
        return False

    def _control_heroes(self, all_minions, all_heroes, all_towers, all_bases):
        for hero in self.heroes:
            if not hero.alive:
                continue

            # AI harus memakai jalur auto-cast yang sama dengan pemain.
            # Jalur lama memanggil cast_skill() tanpa key, yang default-nya
            # selalu Q; akibatnya W/E/R hero enemy tidak pernah dipilih.
            if hero.skill_timer == 0:
                before = hero.active_skill_timer
                hero._try_auto_cast(all_minions + all_heroes,
                                     all_towers, all_bases)
                if hero.active_skill_timer > before:
                    self.total_skills_cast += 1

            if not hero.target and not hero.destination:
                self._assign_hero_lane(hero, all_minions, all_heroes, all_towers)

    def _assign_hero_lane(self, hero, all_minions, all_heroes, all_towers):
        lane_threats = {"top": 0, "mid": 0, "bot": 0}
        lane_ys = {"top": LANE_Y_TOP, "mid": LANE_Y_MID, "bot": LANE_Y_BOT}

        for m in all_minions:
            if m.team != self.team and m.alive:
                lane_threats[m.lane] += 1

        max_lane = max(lane_threats.items(), key=lambda x: x[1])

        if max_lane[1] > 0:
            target_y = lane_ys[max_lane[0]]

            if self.team == "red":
                lane_minions = [m for m in all_minions
                                if m.team == "blue" and m.alive
                                and m.lane == max_lane[0]]
                if lane_minions:
                    # ═══ FIX JALUR AI ═══
                    # Dulu diurutkan by x (reverse) -> hero berlari ke
                    # minion PALING DALAM, melewati semua musuh lain
                    # (terlihat seperti "pergi ke tempat tertentu dulu
                    # baru ke target"). Sekarang pilih minion TERDEKAT
                    # dari posisi hero di lane itu, dan tandai `auto`
                    # supaya hero tetap menyergap musuh yang ditemui
                    # di perjalanan (lihat Hero.update state 2).
                    lane_minions.sort(
                        key=lambda m: math.hypot(
                            m.x - hero.x, m.y - hero.y))
                    target_x = lane_minions[0].x
                    hero.move_to(target_x, target_y, auto=True)
                else:
                    hero.move_to(600, target_y, auto=True)
        else:
            if self.team == "red":
                # Cari blue tower terdekat sebagai target
                blue_towers = [t for t in all_towers
                               if t.team == "blue" and t.alive]
                if blue_towers:
                    # Sort by distance dari hero (bukan by x)
                    blue_towers.sort(key=lambda t: math.hypot(
                        t.x - hero.x, t.y - hero.y))
                    target = blue_towers[0]
                    # Move ke arah tower tapi berhenti agak jauh
                    dx = hero.x - target.x
                    dy = hero.y - target.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        offset_x = target.x + (dx / dist) * 60
                        offset_y = target.y + (dy / dist) * 60
                        hero.move_to(offset_x, offset_y, auto=True)

    def _get_hero_pool(self):
        """Pool hero AI: starter + boss hero dari level DI BAWAH
        level saat ini (level 1 = hanya starter)."""
        pool = list(AI_HERO_PREFERENCES)
        boss_pool = []
        if getattr(self, "level_number", 1) >= 2:
            try:
                from levels import get_level_config
                catalog = get_all_hero_types()
                for n in range(1, self.level_number):
                    cfg = get_level_config(n)
                    if not cfg:
                        continue
                    bosses = list(cfg.get("mini_bosses", {}).values())
                    tb = cfg.get("true_boss")
                    if tb:
                        bosses.append(tb)
                    for bt in bosses:
                        if (bt in catalog
                                and catalog[bt].get("is_boss_hero")
                                and bt not in pool
                                and bt not in boss_pool):
                            boss_pool.append(bt)
            except Exception:
                pass
        # Boss hero level sebelumnya diprioritaskan agar level 2 benar-benar
        # membawa mini boss/true boss level 1 sebagai summon hero, bukan
        # hanya kadang terbeli karena pilihan acak.
        return boss_pool + pool

    def _try_buy_hero(self):
        owned_types = [h.hero_type for h in self.heroes]
        available = [ht for ht in self._get_hero_pool()
                     if ht not in owned_types]

        if not available:
            return False

        try:
            catalog = get_all_hero_types()
        except Exception:
            catalog = {}

        for hero_type in available:
            stats = catalog.get(hero_type) or HERO_TYPES.get(                hero_type, {})
            cost = stats.get("cost", 400)
            if self.gold >= cost + self._ai_reserve():
                offset = len(self.heroes) * 40 - 40
                new_hero = Hero(hero_type, self.team,
                                RED_BASE_X - 60, RED_BASE_Y + 30 + offset)
                self.heroes.append(new_hero)
                self.gold -= cost
                self.total_heroes_bought += 1
                return True

        return False

    def _try_upgrade_hero(self):
        upgradeable = [h for h in self.heroes if h.level < MAX_HERO_LEVEL]
        if not upgradeable:
            return False

        upgradeable.sort(key=lambda h: h.kills, reverse=True)

        for hero in upgradeable:
            cost = hero.upgrade_cost()
            if self.gold >= cost + self._ai_reserve():
                if hero.upgrade():
                    self.gold -= cost
                    self.total_hero_upgrades += 1
                    return True

        return False

    def _try_upgrade_nexus(self, nexus):
        if nexus.level >= MAX_NEXUS_LEVEL:
            return False
        cost = nexus.upgrade_cost()
        if self.gold >= cost + self._ai_reserve():
            if nexus.upgrade():
                self.gold -= cost
                self.total_nexus_upgrades += 1
                return True
        return False



# ================================
