"""
minions/_bundle.py - semua renderer minion

Gabungan dari 6 file:
  - base_renderer.py         level modul
  - goblin.py                namespace _NS_goblin
  - orc.py                   namespace _NS_orc
  - troll.py                 namespace _NS_troll
  - undead.py                namespace _NS_undead
  - dark_rider.py            namespace _NS_dark_rider

Modul yang dibungkus kelas `_NS_<nama>` supaya simbol
bernama sama TIDAK saling menimpa. Ini sudah diukur:
LEVEL_CONFIGS di 4 file tower isinya berbeda semua,
begitu juga PALETTE dan HAS_AACIRCLE di minions.

Modul di level modul (tidak dibungkus) karena kodenya
merujuk simbolnya sendiri saat modul dimuat, sehingga
nama kelas namespace belum terikat:
  base_renderer

File asli tetap ada sebagai jembatan kecil, jadi semua
baris `from minions.<modul> import ...` yang sudah ada
TETAP JALAN tanpa perubahan apa pun.
"""
import pygame
import math


# ====================================================================
# base_renderer.py  (modul bersama)
# ====================================================================
# ================================
# minions/base_renderer.py
# Shared utilities untuk semua minions
# ================================


OUTLINE = (24, 20, 25)
SHADOW = (0, 0, 0)

# Saat True, overlay yang nilainya berubah tiap frame (HP bar,
# slash effect) tidak digambar. Dipakai ketika render ke sprite
# cache supaya nilainya tidak ikut "beku" di dalam sprite.
_RENDERING_TO_CACHE = False


# ═══════════════════════════════════════════════════════
# UTILITIES (dipakai semua minions)
# ═══════════════════════════════════════════════════════

def draw_shadow(surface, x, y, w, h=4, alpha=100):
    """Draw ground shadow di bawah minion"""
    shadow_surf = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                        (0, 0, max(1, w), max(1, h)))
    surface.blit(shadow_surf, (x - w // 2, y - h // 2))


def draw_hp_bar(surface, x, y, w, hp_ratio, team):
    """Draw HP bar di atas minion (skip saat render ke cache)"""
    if _RENDERING_TO_CACHE:
        return
    hp_ratio = max(0.0, min(1.0, hp_ratio))
    bar_h = 4
    bx = x - w // 2

    # Latar & border ikut warna tim: biru = minion player,
    # merah = minion musuh. Sekilas langsung terbaca tanpa
    # elemen tambahan di map.
    if team == "blue":
        bg_color = (12, 22, 44)
        border_color = (90, 165, 255)
    else:
        bg_color = (44, 12, 10)
        border_color = (255, 95, 85)

    pygame.draw.rect(surface, bg_color, (bx, y, w, bar_h))

    fill = int(w * hp_ratio)
    if fill > 0:
        if hp_ratio > 0.6:
            col = (70, 200, 80)
        elif hp_ratio > 0.3:
            col = (225, 190, 60)
        else:
            col = (215, 60, 55)
        pygame.draw.rect(surface, col, (bx, y, fill, bar_h))

    pygame.draw.rect(surface, border_color, (bx, y, w, bar_h), 1)




def draw_slow_effect(surface, x, y, radius, timer):
    """Ice/slow aura di sekitar minion"""
    ice_surf = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
    c = radius * 3 // 2
    pygame.draw.circle(ice_surf, (150, 220, 255, 70), (c, c), radius + 2)
    surface.blit(ice_surf, (x - c, y - c))

    for i in range(3):
        angle = timer * 0.1 + i * 2.1
        ix = x + int(math.cos(angle) * (radius + 3))
        iy = y + int(math.sin(angle) * (radius + 3))
        pygame.draw.rect(surface, (200, 240, 255), (ix, iy, 2, 2))


def draw_slash_effects(surface, cx, cy, slash_effects):
    """Slash arc saat minion menyerang (skip saat render ke cache)"""
    if _RENDERING_TO_CACHE:
        return
    for slash in slash_effects:
        life = slash.get('life', 0)
        max_life = max(1, slash.get('max_life', 12))
        if life <= 0:
            continue

        progress = 1.0 - (life / max_life)
        alpha = int(220 * (1.0 - progress))
        if alpha <= 0:
            continue

        angle = slash.get('angle', 0.0)
        dist = slash.get('distance', 18)

        span = 1.1
        steps = 7
        pts = []
        for i in range(steps):
            a = angle - span / 2 + (span * i / (steps - 1))
            r = dist + progress * 6
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))

        size = int(dist * 2 + 24)
        if size <= 0:
            continue
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        ox, oy = size // 2 - cx, size // 2 - cy
        shifted = [(p[0] + ox, p[1] + oy) for p in pts]

        try:
            pygame.draw.lines(surf, (255, 255, 255, alpha), False,
                              shifted, 3)
            pygame.draw.lines(surf, (255, 230, 180, alpha), False,
                              shifted, 1)
        except Exception:
            pass
        surface.blit(surf, (cx - size // 2, cy - size // 2))


def apply_hurt_flash(color, timer):
    """Warna jadi lebih terang saat kena damage"""
    if timer > 0:
        return tuple(min(255, c + 90) for c in color[:3])
    return color


def calculate_animation_offsets(minion):
    """Offset animasi standar (bob, sway, phase)"""
    phase = getattr(minion, 'walk_cycle', 0.0)
    if getattr(minion, 'is_moving', False):
        bob = int(abs(math.sin(phase * 1.2)) * 2)
        sway = int(math.sin(phase) * 1)
    else:
        bob = int(math.sin(getattr(minion, 'anim_time', 0) * 0.05) * 1)
        sway = 0
    return bob, sway, phase


# ═══════════════════════════════════════════════════════
# SPRITE CACHE
#
# Canvas render 120x120, tapi sprite minion cuma mengisi
# ~35% area (goblin 68x53, undead 68x51, dst). Kalau canvas
# penuh yang di-blit, ~65% piksel terbuang percuma.
# Dengan 80 minion di layar itu beberapa ms hilang tiap frame.
#
# Solusi: simpan versi TER-CROP + anchor, jadi yang di-blit
# hanya area berisi. Diukur: 2.89 ms -> ~1.0 ms per 100 blit.
#
# HP bar & slash effect TIDAK ikut di-cache (nilainya berubah
# terus), digambar live setelah body di-blit.
# ═══════════════════════════════════════════════════════

_CANVAS_W = 120
_CANVAS_H = 120

# Set False untuk kembali ke render langsung (debug).
MINION_CACHE_ENABLED = True


def _minion_cache_key(minion):
    """
    Key cache. Minion dengan key sama = gambar body identik.

    HP tidak masuk key karena HP bar digambar di luar cache.
    """
    mt = minion.minion_type
    lvl = int(getattr(minion, 'nexus_level', 1) or 1)

    atk = int(getattr(minion, 'attack_anim_timer', 0) or 0)
    if atk > 0:
        # Fase animasi serang (dikelompokkan biar cache tidak meledak)
        state = ('atk', atk // 2)
    elif getattr(minion, 'is_moving', False):
        state = ('walk', int(getattr(minion, 'walk_cycle', 0) * 2) % 8)
    else:
        state = ('idle', int(getattr(minion, 'anim_time', 0) * 0.05) % 4)

    return (
        mt,
        minion.team,
        lvl,
        state,
        1 if getattr(minion, 'direction', 1) >= 0 else -1,
        getattr(minion, 'hurt_flash_timer', 0) > 0,
        int(getattr(minion, 'bleed_stacks', 0) or 0),
        bool(getattr(minion, 'death_charge_active', False)),
        bool(getattr(minion, 'regen_active', False)),
        getattr(minion, 'slow_timer', 0) > 0,
    )


def cached_minion_draw(surface, minion, x, y, draw_func):
    """
    Draw minion lewat sprite cache.

    draw_func(surface, minion, x, y) = renderer body asli.
    """
    if not MINION_CACHE_ENABLED:
        draw_func(surface, minion, x, y)
        return

    try:
        from sprite_cache import get_cached_sprite_cropped
    except Exception:
        draw_func(surface, minion, x, y)
        return

    key = _minion_cache_key(minion)
    cx, cy = _CANVAS_W // 2, _CANVAS_H // 2

    def _render(surf):
        global _RENDERING_TO_CACHE
        _RENDERING_TO_CACHE = True
        try:
            draw_func(surf, minion, cx, cy)
        finally:
            _RENDERING_TO_CACHE = False

        # ═══ PEWARNAAN ULANG TIM (full-body recolor) ═══
        # Identitas tim TIDAK lagi pakai cincin di kaki (terlihat
        # berantakan). Sekarang seluruh body diwarnai ulang sekali
        # saat sprite masuk cache:
        #   - Tim musuh (red)  : geser semua warna ke merah karat
        #                        (hijau/biru diredam, merah dinaikkan).
        #                        Mata kuning otomatis jadi oranye
        #                        menyala - khas musuh.
        #   - Tim player (blue): dibiarkan warna aslinya yang hidup.
        # Kontrasnya jauh lebih besar dan bersih dari cincin.
        # Bayangan tetap hitam (perkalian murni tidak mengubah 0)
        # dan alpha dipertahankan.
        if getattr(minion, "team", "blue") == "red":
            try:
                import numpy as _np
                _alpha = pygame.surfarray.array_alpha(surf).copy()
                _arr = pygame.surfarray.array3d(surf).astype(_np.int32)
                _r = _arr[..., 0]
                _g = _arr[..., 1]
                _b = _arr[..., 2]
                _nr = _np.minimum(255, (_r * 1.35 + _b * 0.25))
                _ng = _np.minimum(255, _g * 0.55)
                _nb = _np.minimum(255, _b * 0.55)
                _out = _np.stack([_nr, _ng, _nb], axis=-1).astype(_np.uint8)
                pygame.surfarray.blit_array(surf, _out)
                pygame.surfarray.pixels_alpha(surf)[:] = _alpha
                del _alpha, _arr, _out
            except Exception:
                # Fallback tanpa numpy: redam hijau/biru + tambah merah.
                try:
                    surf.fill((255, 168, 158, 0),
                              special_flags=pygame.BLEND_RGB_MULT)
                    surf.fill((62, 10, 8, 0),
                              special_flags=pygame.BLEND_RGB_ADD)
                except Exception:
                    pass

    try:
        sprite, ax, ay = get_cached_sprite_cropped(
            key, _CANVAS_W, _CANVAS_H, _render)
    except Exception:
        draw_func(surface, minion, x, y)
        return

    surface.blit(sprite, (x - ax, y - ay))

    # ─── Overlay dinamis, digambar LIVE (tidak di-cache) ───
    if minion.slash_effects:
        draw_slash_effects(surface, x, y, minion.slash_effects)

    radius = getattr(minion, 'radius', 14)
    bar_w = radius * 2 + 6
    by = y - radius - 18
    max_hp = max(1, getattr(minion, 'max_hp', 1))
    draw_hp_bar(surface, x, by, bar_w,
                minion.hp / max_hp, minion.team)


# ====================================================================
# goblin.py
# ====================================================================
class _NS_goblin:
    """Namespace goblin - isi asli tidak diubah."""

    # ================================
    # minions/goblin.py
    # HD Goblin Assassin - The Scurvy Cutpurse
    # Hooded green goblin with curved dagger + Deadly Nick passive (bleed stacks)
    # ================================



    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')
    HAS_AALINES = hasattr(pygame.draw, 'aalines')


    def _clamp_color(color):
        if len(color) == 3:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
            )
        elif len(color) == 4:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))),
            )
        return color


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_goblin._clamp_color(color)
        if _NS_goblin.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aaline(surface, color, start, end, width=1):
        color = _NS_goblin._clamp_color(color)
        if width == 1 and _NS_goblin.HAS_AALINES:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.line(surface, color, start, end, width)
        except (TypeError, ValueError):
            pass


    def _aapolygon(surface, color, points):
        color = _NS_goblin._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    def _blend_alpha(surface, color, rect_pts):
        if len(rect_pts) < 3:
            return
        xs = [p[0] for p in rect_pts]
        ys = [p[1] for p in rect_pts]
        minx, miny = min(xs) - 2, min(ys) - 2
        maxx, maxy = max(xs) + 2, max(ys) + 2
        w, h = maxx - minx, maxy - miny
        if w <= 0 or h <= 0:
            return
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        shifted = [(p[0] - minx, p[1] - miny) for p in rect_pts]
        pygame.draw.polygon(tmp, _NS_goblin._clamp_color(color), shifted)
        surface.blit(tmp, (minx, miny))


    # ═══════════════════════════════════════════════════════
    # PALETTE - Goblin Assassin
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            # ═══ BLUE TEAM (Vibrant green - alive/friendly) ═══
            return {
                # Skin (vibrant green - match reference)
                'skin_darkest': (28, 65, 22),
                'skin_dark': (55, 105, 40),
                'skin_mid': (100, 160, 62),
                'skin_light': (150, 210, 92),
                'skin_high': (195, 240, 130),
                'skin_shine': (225, 250, 180),

                # Muscle shadow
                'muscle_dark': (18, 45, 15),
                'muscle_mid': (40, 78, 28),

                # Leather (warm brown - assassin gear)
                'leather_darkest': (30, 18, 8),
                'leather_dark': (68, 42, 22),
                'leather_mid': (110, 72, 38),
                'leather_light': (155, 108, 58),
                'leather_high': (200, 150, 90),

                # Pants (dark leather)
                'pants_darkest': (22, 14, 8),
                'pants_dark': (48, 30, 16),
                'pants_mid': (78, 52, 28),
                'pants_light': (115, 82, 48),

                # Metal (silver dagger, buckles)
                'metal_darkest': (28, 32, 40),
                'metal_dark': (60, 68, 82),
                'metal_mid': (115, 128, 148),
                'metal_light': (180, 195, 215),
                'metal_high': (225, 235, 250),
                'metal_shine': (255, 255, 255),

                # Blade
                'blade_dark': (50, 55, 68),
                'blade_mid': (110, 122, 142),
                'blade_light': (180, 195, 215),
                'blade_high': (230, 240, 255),
                'blade_shine': (255, 255, 255),

                # Gold accents (hilt guard, buckle)
                'gold_darkest': (90, 60, 12),
                'gold_dark': (150, 110, 25),
                'gold_mid': (215, 165, 55),
                'gold_light': (250, 210, 95),
                'gold_high': (255, 240, 160),

                # HOOD (red - match reference)
                'hood_darkest': (55, 15, 15),
                'hood_dark': (105, 32, 28),
                'hood_mid': (160, 55, 45),
                'hood_light': (205, 90, 70),
                'hood_high': (240, 135, 100),

                # Hair (orange peek)
                'hair_darkest': (95, 40, 12),
                'hair_dark': (150, 75, 22),
                'hair_mid': (210, 120, 40),
                'hair_light': (245, 170, 75),
                'hair_high': (255, 215, 130),

                # DEADLY NICK (purple magic - bleed, matches passive icon)
                'bleed_darkest': (30, 8, 55),
                'bleed_dark': (70, 22, 115),
                'bleed_mid': (125, 50, 185),
                'bleed_light': (175, 100, 230),
                'bleed_bright': (215, 155, 250),
                'bleed_hot': (245, 215, 255),
                'bleed_white': (255, 245, 255),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 5, 8),
                'eye_black': (10, 15, 5),
                'eye_yellow': (255, 220, 50),
                'eye_bright': (255, 250, 200),
                'mouth_dark': (55, 15, 15),
                'tooth': (250, 245, 210),
            }
        else:
            # ═══ RED TEAM (Sickly darker green - evil) ═══
            return {
                'skin_darkest': (20, 42, 18),
                'skin_dark': (42, 78, 32),
                'skin_mid': (72, 120, 52),
                'skin_light': (108, 160, 78),
                'skin_high': (150, 200, 110),
                'skin_shine': (190, 230, 150),

                'muscle_dark': (16, 35, 14),
                'muscle_mid': (32, 62, 24),

                'leather_darkest': (25, 15, 7),
                'leather_dark': (55, 32, 15),
                'leather_mid': (90, 55, 25),
                'leather_light': (135, 88, 42),
                'leather_high': (180, 128, 70),

                'pants_darkest': (18, 10, 6),
                'pants_dark': (38, 22, 12),
                'pants_mid': (65, 42, 22),
                'pants_light': (95, 65, 38),

                'metal_darkest': (25, 20, 20),
                'metal_dark': (55, 48, 48),
                'metal_mid': (105, 88, 88),
                'metal_light': (165, 145, 145),
                'metal_high': (215, 195, 195),
                'metal_shine': (245, 235, 235),

                'blade_dark': (42, 42, 52),
                'blade_mid': (95, 95, 110),
                'blade_light': (160, 160, 180),
                'blade_high': (215, 215, 230),
                'blade_shine': (248, 248, 255),

                'gold_darkest': (65, 42, 10),
                'gold_dark': (110, 78, 20),
                'gold_mid': (165, 120, 40),
                'gold_light': (210, 170, 75),
                'gold_high': (240, 208, 130),

                # Dark red hood
                'hood_darkest': (48, 12, 12),
                'hood_dark': (95, 25, 22),
                'hood_mid': (145, 45, 38),
                'hood_light': (190, 78, 58),
                'hood_high': (225, 120, 88),

                'hair_darkest': (75, 25, 8),
                'hair_dark': (125, 50, 18),
                'hair_mid': (175, 85, 32),
                'hair_light': (215, 128, 62),
                'hair_high': (245, 175, 100),

                'bleed_darkest': (35, 8, 55),
                'bleed_dark': (80, 22, 120),
                'bleed_mid': (135, 55, 190),
                'bleed_light': (180, 105, 232),
                'bleed_bright': (218, 160, 250),
                'bleed_hot': (246, 218, 255),
                'bleed_white': (255, 240, 255),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 3, 5),
                'eye_black': (12, 5, 5),
                'eye_yellow': (255, 210, 50),
                'eye_bright': (255, 240, 195),
                'mouth_dark': (48, 12, 12),
                'tooth': (248, 238, 208),
            }


    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_goblin(surface, minion, x, y):
        """Draw goblin - CACHED"""
        from minions.base_renderer import cached_minion_draw
        cached_minion_draw(surface, minion, x, y, _NS_goblin._draw_goblin_full)


    def _draw_goblin_full(surface, minion, x, y):
        """Original goblin render (dipanggil oleh cache)"""
        palette = _NS_goblin._get_palette(minion.team)

        walk_phase = minion.walk_cycle
        is_running = minion.is_moving
        anim_time = minion.anim_time

        # Deadly Nick proc - triggered on hit
        deadly_nick_proc = getattr(minion, 'deadly_nick_proc_timer', 0)

        # Attack anim
        attack_progress = 0
        is_attacking = False
        if minion.attack_anim_timer > 0:
            attack_progress = 1.0 - (minion.attack_anim_timer /
                                      minion.attack_anim_max)
            is_attacking = True

        # Small quick bob (sneaky assassin)
        if is_running:
            body_bob = int(math.sin(walk_phase * 1.5) * 2)
        else:
            body_bob = int(math.sin(anim_time * 0.06) * 1)

        # Attack lunge
        attack_offset_x = 0
        if is_attacking:
            if attack_progress < 0.25:
                p = attack_progress / 0.25
                attack_offset_x = int(-p * 3) * minion.direction
            elif attack_progress < 0.55:
                p = (attack_progress - 0.25) / 0.30
                ease = p * p * (3 - 2 * p)
                attack_offset_x = int((-3 + ease * 10)) * minion.direction
            else:
                p = (attack_progress - 0.55) / 0.45
                ease = 1 - (1 - p) * (1 - p)
                attack_offset_x = int((7 - ease * 7)) * minion.direction

        # Spawn scale
        spawn_scale = 1.0
        if minion.spawn_anim > 0:
            spawn_scale = 1.0 - (minion.spawn_anim / 20.0) * 0.5
            spawn_scale = max(0.3, spawn_scale)

        draw_x = x + attack_offset_x
        draw_y = y + body_bob

        # Ground shadow
        _NS_goblin._draw_ground_shadow(surface, x, y + minion.radius + 6, minion.radius)

        # Bleed aura on ground (when Deadly Nick proc active)
        if deadly_nick_proc > 0:
            _NS_goblin._draw_bleed_ground_aura(surface, x, y + minion.radius + 4,
                                    minion.radius, anim_time, palette,
                                    deadly_nick_proc)

        # Slow FX
        if minion.slow_timer > 0:
            draw_slow_effect(surface, x, y, minion.radius, anim_time)

        # Main body per level
        level = minion.nexus_level
        if level == 1:
            _NS_goblin._draw_goblin_lvl1(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        elif level == 2:
            _NS_goblin._draw_goblin_lvl2(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        elif level == 3:
            _NS_goblin._draw_goblin_lvl3(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        elif level == 4:
            _NS_goblin._draw_goblin_lvl4(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        else:
            _NS_goblin._draw_goblin_lvl5(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)

        # Champion aura for lvl 5
        if level >= 5:
            _NS_goblin._draw_master_aura(surface, x, y, anim_time, palette)

        # Deadly Nick proc particles (rising purple droplets on body)
        if deadly_nick_proc > 0:
            _NS_goblin._draw_bleed_particles(surface, x, y, minion.radius,
                                  anim_time, palette, deadly_nick_proc)

        # Bleed stacks icon above head (matches reference passive icon)
        bleed_stacks = getattr(minion, 'bleed_stacks', 0)
        if bleed_stacks > 0:
            _NS_goblin._draw_bleed_stacks_icons(surface, x, y - minion.radius - 30,
                                      bleed_stacks, anim_time, palette)

        # Attack swing arc (purple Deadly Nick crescent - match reference)
        if is_attacking and 0.30 <= attack_progress <= 0.72:
            _NS_goblin._draw_deadly_nick_arc(surface, draw_x, draw_y, minion.direction,
                                  attack_progress, palette)

        # Impact sparkle at peak (only if proc-active this attack)
        if is_attacking and 0.50 <= attack_progress <= 0.63 and deadly_nick_proc > 0:
            _NS_goblin._draw_deadly_nick_impact(surface, draw_x, draw_y, minion.direction,
                                      attack_progress, palette)

        # Slash effects
        if minion.slash_effects:
            draw_slash_effects(surface, draw_x, draw_y, minion.slash_effects)


        # HP bar
        bar_w = minion.radius * 2 + 6
        by = y - minion.radius - 18
        draw_hp_bar(surface, x, by, bar_w,
                    minion.hp / minion.max_hp, minion.team)

        # Level stars
        if minion.nexus_level >= 3:
            for i in range(minion.nexus_level - 2):
                star_x = x - 5 + i * 5
                star_y = by - 5
                _NS_goblin._aacircle(surface, palette['bleed_light'], (star_x, star_y), 2)
                pygame.draw.rect(surface, palette['shine'],
                                 (star_x, star_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # GROUND SHADOW
    # ═══════════════════════════════════════════════════════

    def _draw_ground_shadow(surface, x, y, radius):
        shadow_surf = pygame.Surface((radius * 5, 12), pygame.SRCALPHA)
        for r in range(6, 0, -1):
            alpha = (6 - r) * 22
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                                (6 - r, 6 - r,
                                 radius * 5 - (6 - r) * 2, r * 2))
        surface.blit(shadow_surf, (x - radius * 5 // 2, y - 6))


    # ═══════════════════════════════════════════════════════
    # LEVEL 1: SCOUT (basic, no hood)
    # ═══════════════════════════════════════════════════════

    def _draw_goblin_lvl1(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_goblin._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_goblin._draw_torso_simple(surface, bx, y - 2, face, palette, hurt)
        _NS_goblin._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=False)
        _NS_goblin._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_hood=False, has_scar=False)
        _NS_goblin._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='dagger_small', has_bracer=False)


    # ═══════════════════════════════════════════════════════
    # LEVEL 2: CUTPURSE (+red hood + leather vest)
    # ═══════════════════════════════════════════════════════

    def _draw_goblin_lvl2(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_goblin._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_goblin._draw_torso_vest(surface, bx, y - 2, face, palette, hurt)
        _NS_goblin._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_goblin._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_hood=True, has_scar=False)
        _NS_goblin._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='dagger_small', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 3: ASSASSIN (+shoulder spike +scar +bigger dagger)
    # ═══════════════════════════════════════════════════════

    def _draw_goblin_lvl3(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_goblin._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_goblin._draw_torso_vest(surface, bx, y - 2, face, palette, hurt)
        _NS_goblin._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_goblin._draw_spiked_pauldron(surface, bx - r + 1, y - 3, palette)
        _NS_goblin._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_hood=True, has_scar=True)
        _NS_goblin._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='dagger_big', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 4: MASTER CUTPURSE (+both pauldrons +extra scars)
    # ═══════════════════════════════════════════════════════

    def _draw_goblin_lvl4(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_goblin._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_goblin._draw_torso_vest(surface, bx, y - 2, face, palette, hurt)
        _NS_goblin._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_goblin._draw_spiked_pauldron(surface, bx - r + 1, y - 3, palette)
        _NS_goblin._draw_spiked_pauldron(surface, bx + r - 1, y - 3, palette, mirror=True)
        _NS_goblin._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_hood=True, has_scar=True, extra_scar=True)
        _NS_goblin._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='dagger_big', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 5: CHAMPION (dual-wield + armored + crown)
    # ═══════════════════════════════════════════════════════

    def _draw_goblin_lvl5(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_goblin._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_goblin._draw_torso_armored(surface, bx, y - 2, face, palette, hurt)
        # Off-hand also holds dagger (dual wield)
        _NS_goblin._draw_arm_offhand_dagger(surface, bx - r + 2, y, face, walk_phase,
                                  attack_progress, is_running, is_attacking,
                                  palette)
        _NS_goblin._draw_spiked_pauldron(surface, bx - r + 1, y - 3, palette)
        _NS_goblin._draw_spiked_pauldron(surface, bx + r - 1, y - 3, palette, mirror=True)
        _NS_goblin._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_hood=True, has_scar=True, extra_scar=True, has_crown=True)
        _NS_goblin._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='dagger_big', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEGS + BOOTS (small goblin legs, chunky boots)
    # ═══════════════════════════════════════════════════════

    def _draw_legs(surface, cx, cy, phase, is_running, palette):
        """Two short goblin legs with heavy boots."""
        if is_running:
            swing_l = math.sin(phase * 2) * 3
            swing_r = -swing_l
        else:
            idle = math.sin(phase * 0.8) * 0.4
            swing_l = idle
            swing_r = -idle

        for side, swing in [(-1, swing_l), (1, swing_r)]:
            hip_x = cx + side * 3
            hip_y = cy - 2

            knee_x = hip_x + int(swing * 0.4)
            knee_y = cy + 3

            foot_x = hip_x + int(swing)
            foot_y = cy + 8

            # Shadow
            _NS_goblin._aaline(surface, palette['shadow_deep'],
                    (hip_x + 1, hip_y + 1), (foot_x + 1, foot_y + 1), 5)

            # Pants (dark leather)
            _NS_goblin._aaline(surface, palette['pants_darkest'],
                    (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_goblin._aaline(surface, palette['pants_dark'],
                    (hip_x, hip_y), (knee_x, knee_y), 4)
            _NS_goblin._aaline(surface, palette['pants_mid'],
                    (hip_x, hip_y), (knee_x, knee_y), 2)

            _NS_goblin._aaline(surface, palette['pants_darkest'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 5)
            _NS_goblin._aaline(surface, palette['pants_dark'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 4)
            _NS_goblin._aaline(surface, palette['pants_mid'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 2)

            # Knee patch (leather)
            _NS_goblin._aacircle(surface, palette['leather_dark'], (knee_x, knee_y), 2)
            _NS_goblin._aacircle(surface, palette['leather_mid'], (knee_x, knee_y), 1)

            # BOOT (chunky leather with metal toe)
            _NS_goblin._draw_boot(surface, foot_x, foot_y, palette)


    def _draw_boot(surface, fx, fy, palette):
        """Chunky leather boot with metal toe cap."""
        boot_pts = [
            (fx - 4, fy - 4),
            (fx + 4, fy - 4),
            (fx + 5, fy - 1),
            (fx + 4, fy + 1),
            (fx - 4, fy + 1),
            (fx - 5, fy - 1),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in boot_pts])
        _NS_goblin._aapolygon(surface, palette['leather_darkest'], boot_pts)
        _NS_goblin._aapolygon(surface, palette['leather_dark'], [
            (fx - 3, fy - 3), (fx + 3, fy - 3),
            (fx + 4, fy - 1), (fx + 3, fy),
            (fx - 3, fy), (fx - 4, fy - 1),
        ])
        _NS_goblin._aapolygon(surface, palette['leather_mid'], [
            (fx - 3, fy - 3), (fx + 2, fy - 3),
            (fx + 3, fy - 2), (fx + 2, fy - 1),
            (fx - 3, fy - 1),
        ])
        _NS_goblin._aaline(surface, palette['leather_light'],
                (fx - 2, fy - 3), (fx + 1, fy - 3), 1)

        # Metal toe cap
        pygame.draw.rect(surface, palette['metal_darkest'],
                         (fx + 2, fy - 2, 3, 3))
        pygame.draw.rect(surface, palette['metal_dark'],
                         (fx + 2, fy - 2, 3, 2))
        pygame.draw.rect(surface, palette['metal_mid'],
                         (fx + 2, fy - 2, 2, 1))
        pygame.draw.rect(surface, palette['metal_high'],
                         (fx + 2, fy - 2, 1, 1))

        # Boot strap + buckle
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (fx - 3, fy - 2, 5, 1))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (fx - 1, fy - 2, 1, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (fx - 1, fy - 2, 1, 1))


    # ═══════════════════════════════════════════════════════
    # TORSO VARIANTS
    # ═══════════════════════════════════════════════════════

    def _draw_torso_simple(surface, cx, cy, face, palette, hurt):
        """Level 1 - simple shirt/vest."""
        body_w = 16
        body_h = 14

        if hurt:
            skin_mid = (255, 255, 255)
            skin_light = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']
            skin_light = palette['skin_light']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=3)

        # Skin base
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=3)
        pygame.draw.rect(surface, palette['skin_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=3)
        pygame.draw.rect(surface, skin_mid,
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=3)

        # Asymmetric leather half-vest (assassin style)
        vest_pts = [
            (cx - body_w // 2, cy + 1),
            (cx + body_w // 2 - 2, cy + 1),
            (cx + body_w // 2 - 3, cy + body_h - 4),
            (cx - body_w // 2, cy + body_h - 4),
        ]
        _NS_goblin._aapolygon(surface, palette['leather_darkest'], vest_pts)
        _NS_goblin._aapolygon(surface, palette['leather_dark'], [
            (cx - body_w // 2 + 1, cy + 2),
            (cx + body_w // 2 - 3, cy + 2),
            (cx + body_w // 2 - 4, cy + body_h - 5),
            (cx - body_w // 2 + 1, cy + body_h - 5),
        ])
        _NS_goblin._aaline(surface, palette['leather_mid'],
                (cx - body_w // 2 + 2, cy + 3),
                (cx + body_w // 2 - 4, cy + 3), 1)

        # Muscle def
        pygame.draw.line(surface, palette['muscle_dark'],
                         (cx - 2, cy + 4), (cx - 2, cy + body_h - 6), 1)

        # Basic leather belt
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, cy + body_h - 3, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, cy + body_h - 3, body_w - 1, 2))
        # Small buckle
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 2, cy + body_h - 3, 3, 3))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 2, cy + body_h - 3, 2, 2))


    def _draw_torso_vest(surface, cx, cy, face, palette, hurt):
        """Level 2-4 - full leather vest with baldric & buckles."""
        body_w = 18
        body_h = 16

        if hurt:
            skin_mid = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=3)

        # Skin base
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=3)
        pygame.draw.rect(surface, skin_mid,
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=3)

        # Leather vest layers
        vest_outer = [
            (cx - body_w // 2 + 1, cy + 1),
            (cx + body_w // 2 - 1, cy + 1),
            (cx + body_w // 2 - 1, cy + body_h - 1),
            (cx - body_w // 2 + 1, cy + body_h - 1),
        ]
        _NS_goblin._aapolygon(surface, palette['leather_darkest'], vest_outer)
        _NS_goblin._aapolygon(surface, palette['leather_dark'], [
            (cx - body_w // 2 + 2, cy + 2),
            (cx + body_w // 2 - 2, cy + 2),
            (cx + body_w // 2 - 2, cy + body_h - 2),
            (cx - body_w // 2 + 2, cy + body_h - 2),
        ])
        _NS_goblin._aapolygon(surface, palette['leather_mid'], [
            (cx - body_w // 2 + 2, cy + 2),
            (cx + body_w // 2 - 3, cy + 2),
            (cx + body_w // 2 - 3, cy + body_h - 3),
            (cx - body_w // 2 + 2, cy + body_h - 3),
        ])
        # Highlight top
        pygame.draw.rect(surface, palette['leather_light'],
                         (cx - body_w // 2 + 2, cy + 2, body_w - 5, 2))
        pygame.draw.rect(surface, palette['leather_high'],
                         (cx - body_w // 2 + 2, cy + 2, 3, 1))

        # V-neck showing skin
        pygame.draw.polygon(surface, palette['skin_dark'], [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx, cy + 5),
        ])
        pygame.draw.polygon(surface, skin_mid, [
            (cx - 1, cy + 1),
            (cx + 1, cy + 1),
            (cx, cy + 4),
        ])
        _NS_goblin._aaline(surface, palette['leather_darkest'],
                (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

        # Diagonal baldric strap
        _NS_goblin._aaline(surface, palette['leather_darkest'],
                (cx - body_w // 2 + 2, cy + 3),
                (cx + body_w // 2 - 3, cy + body_h - 5), 3)
        _NS_goblin._aaline(surface, palette['leather_dark'],
                (cx - body_w // 2 + 2, cy + 3),
                (cx + body_w // 2 - 3, cy + body_h - 5), 2)
        _NS_goblin._aaline(surface, palette['leather_light'],
                (cx - body_w // 2 + 2, cy + 3),
                (cx + body_w // 2 - 3, cy + body_h - 5), 1)
        # Buckle on baldric
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 2, cy + 6, 3, 2))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 2, cy + 6, 2, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 2, cy + 6, 1, 1))

        # BIG belt with gold buckle
        belt_y = cy + body_h - 5
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - body_w // 2, belt_y + 1, body_w, 4))
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 4))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 3))
        pygame.draw.rect(surface, palette['leather_mid'],
                         (cx - body_w // 2, belt_y, body_w - 2, 1))

        # Belt buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 3, belt_y - 1 + 1, 6, 5))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 3, belt_y - 1, 6, 5))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 3, belt_y - 1, 5, 4))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 3, belt_y - 1, 4, 3))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 3, belt_y - 1, 2, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 3, belt_y - 1, 1, 1))

        # Small pouches on belt
        for side_x in [-6, 5]:
            _NS_goblin._aapolygon(surface, palette['leather_darkest'], [
                (cx + side_x - 1, belt_y - 1),
                (cx + side_x + 1, belt_y - 1),
                (cx + side_x + 2, belt_y + 3),
                (cx + side_x - 2, belt_y + 3),
            ])
            _NS_goblin._aapolygon(surface, palette['leather_dark'], [
                (cx + side_x - 1, belt_y),
                (cx + side_x + 1, belt_y),
                (cx + side_x + 1, belt_y + 2),
                (cx + side_x - 1, belt_y + 2),
            ])


    def _draw_torso_armored(surface, cx, cy, face, palette, hurt):
        """Level 5 - leather + metal chest plates + Deadly Nick emblem."""
        body_w = 20
        body_h = 17

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=3)

        # Metal chestplate over leather
        pygame.draw.rect(surface, palette['metal_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=3)
        pygame.draw.rect(surface, palette['metal_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=3)
        pygame.draw.rect(surface, palette['metal_mid'],
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=3)
        pygame.draw.rect(surface, palette['metal_light'],
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=2)
        pygame.draw.rect(surface, palette['metal_high'],
                         (cx - body_w // 2, cy, 5, 3), border_radius=1)

        # Gold trim
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - body_w // 2, cy, body_w, 2))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - body_w // 2, cy, body_w - 1, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - body_w // 2 + 1, cy, 3, 1))

        # DEADLY NICK EMBLEM on chest (purple dagger + gem, matches passive icon)
        # Dagger shape
        _NS_goblin._aapolygon(surface, palette['gold_dark'], [
            (cx - 3, cy + 4), (cx + 3, cy + 6),
            (cx - 3, cy + 8), (cx + 3, cy + 10),
        ])
        # Central purple gem
        _NS_goblin._aacircle(surface, palette['bleed_darkest'], (cx, cy + 7), 3)
        _NS_goblin._aacircle(surface, palette['bleed_dark'], (cx, cy + 7), 2)
        _NS_goblin._aacircle(surface, palette['bleed_bright'], (cx - 1, cy + 6), 1)
        pygame.draw.rect(surface, palette['bleed_hot'], (cx - 1, cy + 6, 1, 1))

        # Rivets
        for rx in [-body_w // 2 + 2, body_w // 2 - 3]:
            for ry in [2, body_h - 5]:
                _NS_goblin._aacircle(surface, palette['metal_darkest'],
                          (cx + rx, cy + ry), 1)
                pygame.draw.rect(surface, palette['metal_high'],
                                 (cx + rx, cy + ry - 1, 1, 1))

        # Belt
        belt_y = cy + body_h - 4
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 2))
        # Big buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 4, belt_y - 1 + 1, 8, 5))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 4, belt_y - 1, 8, 5))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 4, belt_y - 1, 7, 4))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 4, belt_y - 1, 5, 3))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 4, belt_y - 1, 3, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 4, belt_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # HEAD (Green goblin with red hood)
    # ═══════════════════════════════════════════════════════

    def _draw_head(surface, cx, cy, face, palette, hurt,
                   has_hood=False, has_scar=False, extra_scar=False,
                   has_crown=False):
        """Green goblin head with optional red assassin hood."""
        if hurt:
            skin_mid = (255, 255, 255)
            skin_light = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']
            skin_light = palette['skin_light']

        head_r = 8

        # ═══ POINTY EARS ═══
        # Back ear (partial visible)
        ear_b_pts = [
            (cx - head_r + 2, cy - 1),
            (cx - head_r - 4, cy - 7),
            (cx - head_r + 3, cy - 3),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in ear_b_pts])
        _NS_goblin._aapolygon(surface, palette['skin_darkest'], ear_b_pts)
        _NS_goblin._aapolygon(surface, palette['skin_dark'], [
            (cx - head_r + 2, cy - 1),
            (cx - head_r - 3, cy - 6),
            (cx - head_r + 3, cy - 3),
        ])
        _NS_goblin._aapolygon(surface, skin_mid, [
            (cx - head_r + 2, cy - 2),
            (cx - head_r - 1, cy - 5),
            (cx - head_r + 3, cy - 3),
        ])

        # Front ear (BIG, prominent, pointing up-forward)
        ear_f_pts = [
            (cx + head_r - 2, cy - 2),
            (cx + head_r + 6, cy - 10),
            (cx + head_r + 1, cy - 3),
            (cx + head_r - 1, cy),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in ear_f_pts])
        _NS_goblin._aapolygon(surface, palette['skin_darkest'], ear_f_pts)
        _NS_goblin._aapolygon(surface, palette['skin_dark'], [
            (cx + head_r - 2, cy - 2),
            (cx + head_r + 5, cy - 9),
            (cx + head_r + 1, cy - 3),
            (cx + head_r - 1, cy),
        ])
        _NS_goblin._aapolygon(surface, skin_mid, [
            (cx + head_r - 2, cy - 2),
            (cx + head_r + 3, cy - 7),
            (cx + head_r + 1, cy - 3),
        ])
        _NS_goblin._aaline(surface, skin_light,
                (cx + head_r - 1, cy - 2),
                (cx + head_r + 3, cy - 6), 1)
        _NS_goblin._aaline(surface, palette['skin_high'],
                (cx + head_r, cy - 3),
                (cx + head_r + 2, cy - 5), 1)

        # ═══ HEAD SHAPE ═══
        _NS_goblin._aacircle(surface, palette['shadow_deep'], (cx + 1, cy + 1), head_r)
        _NS_goblin._aacircle(surface, palette['skin_darkest'], (cx, cy), head_r)
        _NS_goblin._aacircle(surface, palette['skin_dark'], (cx, cy), head_r - 1)
        _NS_goblin._aacircle(surface, skin_mid, (cx - 1, cy - 1), head_r - 2)
        _NS_goblin._aacircle(surface, skin_light, (cx - 2, cy - 2), head_r - 4)
        _NS_goblin._aacircle(surface, palette['skin_high'], (cx - 2, cy - 2),
                  max(1, head_r - 5))

        # ═══ LONG CROOKED NOSE (goblin signature) ═══
        nose_pts = [
            (cx + 2, cy + 1),
            (cx + 8, cy + 4),
            (cx + 7, cy + 5),
            (cx + 2, cy + 4),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in nose_pts])
        _NS_goblin._aapolygon(surface, palette['skin_darkest'], nose_pts)
        _NS_goblin._aapolygon(surface, palette['skin_dark'], [
            (cx + 2, cy + 2),
            (cx + 7, cy + 4),
            (cx + 6, cy + 5),
            (cx + 2, cy + 4),
        ])
        _NS_goblin._aapolygon(surface, skin_mid, [
            (cx + 3, cy + 2),
            (cx + 6, cy + 3),
            (cx + 5, cy + 4),
        ])
        pygame.draw.rect(surface, skin_light, (cx + 4, cy + 3, 1, 1))
        # Nose bump
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx + 5, cy + 2, 1, 1))

        # ═══ ANGRY BROW ═══
        _NS_goblin._aaline(surface, palette['muscle_dark'],
                (cx - 5, cy - 3), (cx + 2, cy - 1), 2)
        _NS_goblin._aaline(surface, palette['shadow'],
                (cx - 5, cy - 3), (cx + 2, cy - 1), 1)

        # ═══ EYE (yellow evil) ═══
        _NS_goblin._aacircle(surface, palette['muscle_dark'], (cx - 1, cy), 3)
        _NS_goblin._aacircle(surface, palette['eye_black'], (cx - 1, cy), 2)
        _NS_goblin._aacircle(surface, palette['eye_yellow'], (cx, cy), 2)
        pygame.draw.rect(surface, palette['eye_black'], (cx, cy - 1, 1, 2))
        pygame.draw.rect(surface, palette['eye_bright'],
                         (cx - 1, cy - 1, 1, 1))

        # Small back eye
        pygame.draw.rect(surface, palette['muscle_dark'], (cx - 5, cy, 2, 1))
        pygame.draw.rect(surface, palette['eye_yellow'], (cx - 4, cy, 1, 1))

        # ═══ SNARL / MOUTH with FANG ═══
        mouth_y = cy + 5
        pygame.draw.rect(surface, palette['mouth_dark'],
                         (cx - 3, mouth_y, 5, 2))
        _NS_goblin._aaline(surface, palette['shadow'],
                (cx - 3, mouth_y), (cx + 2, mouth_y), 1)
        # Fang
        _NS_goblin._aapolygon(surface, palette['tooth'], [
            (cx + 1, mouth_y),
            (cx + 3, mouth_y),
            (cx + 2, mouth_y + 3),
        ])
        pygame.draw.rect(surface, palette['shine'],
                         (cx + 2, mouth_y + 1, 1, 1))
        # Small tooth
        _NS_goblin._aapolygon(surface, palette['tooth'], [
            (cx - 2, mouth_y),
            (cx - 1, mouth_y),
            (cx - 2, mouth_y + 2),
        ])

        # ═══ SCARS (level 3+) ═══
        if has_scar:
            _NS_goblin._aaline(surface, palette['muscle_dark'],
                    (cx - 4, cy + 1), (cx - 2, cy + 4), 1)
            _NS_goblin._aaline(surface, palette['skin_darkest'],
                    (cx - 4, cy + 1), (cx - 2, cy + 4), 1)
            for i in range(3):
                sx = cx - 4 + i
                sy = cy + 1 + i
                pygame.draw.rect(surface, palette['skin_high'], (sx, sy, 1, 1))

        if extra_scar:
            _NS_goblin._aaline(surface, palette['muscle_dark'],
                    (cx + 1, cy - 4), (cx + 1, cy - 1), 1)
            _NS_goblin._aaline(surface, palette['skin_darkest'],
                    (cx + 1, cy - 4), (cx + 1, cy - 1), 1)
            pygame.draw.rect(surface, palette['skin_high'], (cx + 1, cy - 3, 1, 1))

        # ═══ RED HOOD (level 2+) ═══
        if has_hood:
            _NS_goblin._draw_red_hood(surface, cx, cy, head_r, palette)

        # ═══ CROWN on top of hood (level 5) ═══
        if has_crown:
            _NS_goblin._draw_crown(surface, cx, cy - head_r - 3, palette)


    def _draw_red_hood(surface, cx, cy, head_r, palette):
        """Red assassin hood with pointy top + stitching."""
        hood_outer = [
            (cx - head_r - 1, cy + 2),
            (cx - head_r - 2, cy - 2),
            (cx - head_r, cy - head_r + 1),
            (cx - 4, cy - head_r - 2),
            (cx + 2, cy - head_r - 3),
            (cx + head_r - 1, cy - head_r + 2),
            (cx + head_r + 1, cy - 2),
            (cx + head_r, cy + 1),
            (cx + 4, cy - 2),
            (cx - 3, cy - 3),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in hood_outer])
        _NS_goblin._aapolygon(surface, palette['hood_darkest'], hood_outer)

        _NS_goblin._aapolygon(surface, palette['hood_dark'], [
            (cx - head_r, cy + 1),
            (cx - head_r - 1, cy - 2),
            (cx - head_r + 1, cy - head_r + 2),
            (cx - 3, cy - head_r - 1),
            (cx + 2, cy - head_r - 2),
            (cx + head_r - 2, cy - head_r + 3),
            (cx + head_r, cy - 2),
            (cx + head_r - 1, cy),
            (cx + 3, cy - 2),
            (cx - 2, cy - 2),
        ])

        _NS_goblin._aapolygon(surface, palette['hood_mid'], [
            (cx - head_r + 1, cy - 1),
            (cx - head_r, cy - 3),
            (cx - head_r + 2, cy - head_r + 3),
            (cx - 2, cy - head_r),
            (cx + 2, cy - head_r - 1),
            (cx + head_r - 3, cy - head_r + 3),
            (cx + head_r - 1, cy - 2),
        ])

        # Highlight front
        _NS_goblin._aapolygon(surface, palette['hood_light'], [
            (cx - 2, cy - head_r),
            (cx + 1, cy - head_r - 1),
            (cx + 3, cy - head_r + 2),
            (cx, cy - head_r + 1),
        ])
        pygame.draw.rect(surface, palette['hood_high'],
                         (cx - 1, cy - head_r, 2, 1))

        # ═══ POINTY HOOD TIP (backward-up) ═══
        tip_base_x = cx - 3
        tip_base_y = cy - head_r
        tip_end_x = cx - 8
        tip_end_y = cy - head_r - 5

        _NS_goblin._aapolygon(surface, palette['shadow_deep'], [
            (tip_base_x - 2, tip_base_y + 2),
            (tip_base_x + 2, tip_base_y + 1),
            (tip_end_x + 1, tip_end_y + 1),
        ])
        _NS_goblin._aapolygon(surface, palette['hood_darkest'], [
            (tip_base_x - 2, tip_base_y + 1),
            (tip_base_x + 2, tip_base_y),
            (tip_end_x, tip_end_y),
        ])
        _NS_goblin._aapolygon(surface, palette['hood_dark'], [
            (tip_base_x - 2, tip_base_y + 1),
            (tip_base_x + 1, tip_base_y + 1),
            (tip_end_x, tip_end_y + 1),
        ])
        _NS_goblin._aapolygon(surface, palette['hood_mid'], [
            (tip_base_x - 1, tip_base_y + 1),
            (tip_base_x + 1, tip_base_y + 1),
            (tip_end_x + 1, tip_end_y + 1),
        ])
        _NS_goblin._aaline(surface, palette['hood_light'],
                (tip_base_x, tip_base_y),
                (tip_end_x + 1, tip_end_y + 1), 1)

        # ═══ STITCHING details ═══
        stitches = [
            (cx - 5, cy - head_r + 1),
            (cx - 2, cy - head_r - 1),
            (cx + 1, cy - head_r - 1),
            (cx + 4, cy - head_r + 1),
            (cx + 5, cy - 1),
            (cx - 5, cy - 1),
        ]
        for sx, sy in stitches:
            pygame.draw.rect(surface, palette['hood_darkest'], (sx, sy, 1, 1))
            pygame.draw.rect(surface, palette['hood_high'], (sx, sy - 1, 1, 1))

        # X-pattern stitch
        _NS_goblin._aaline(surface, palette['hood_darkest'],
                (cx - 2, cy - head_r + 3), (cx + 2, cy - head_r + 3), 1)
        _NS_goblin._aaline(surface, palette['hood_high'],
                (cx - 2, cy - head_r + 3), (cx + 2, cy - head_r + 3), 1)

        # ═══ Hair tuft peeking at front ═══
        tuft_x = cx - 4
        tuft_y = cy - head_r + 2
        for i, (hx, hy_off) in enumerate([(-1, -2), (0, -3), (1, -2)]):
            base_x = tuft_x + hx
            _NS_goblin._aapolygon(surface, palette['hair_darkest'], [
                (base_x - 1, tuft_y),
                (base_x + hy_off // 2, tuft_y + hy_off),
                (base_x + 1, tuft_y),
            ])
            _NS_goblin._aapolygon(surface, palette['hair_dark'], [
                (base_x, tuft_y),
                (base_x + hy_off // 2, tuft_y + hy_off + 1),
                (base_x + 1, tuft_y),
            ])
            _NS_goblin._aaline(surface, palette['hair_light'],
                    (base_x, tuft_y - 1),
                    (base_x + hy_off // 2, tuft_y + hy_off + 1), 1)


    def _draw_crown(surface, cx, cy, palette):
        """Gold assassin crown (thin band with small spikes)."""
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 5, cy + 1, 10, 2))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 5, cy + 1, 9, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 4, cy + 1, 3, 1))

        for i, sx_off in enumerate([-3, 0, 3]):
            sx = cx + sx_off
            _NS_goblin._aapolygon(surface, palette['gold_darkest'], [
                (sx - 1, cy + 1),
                (sx, cy - 3),
                (sx + 1, cy + 1),
            ])
            _NS_goblin._aapolygon(surface, palette['gold_dark'], [
                (sx - 1, cy + 1),
                (sx, cy - 2),
                (sx + 1, cy + 1),
            ])
            _NS_goblin._aapolygon(surface, palette['gold_mid'], [
                (sx - 1, cy + 1),
                (sx, cy - 1),
                (sx, cy + 1),
            ])
            pygame.draw.rect(surface, palette['gold_high'], (sx, cy - 1, 1, 1))

        # Center purple gem (matches Deadly Nick)
        _NS_goblin._aacircle(surface, palette['bleed_darkest'], (cx, cy + 2), 2)
        _NS_goblin._aacircle(surface, palette['bleed_dark'], (cx, cy + 2), 1)
        pygame.draw.rect(surface, palette['bleed_bright'], (cx, cy + 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # SPIKED PAULDRON
    # ═══════════════════════════════════════════════════════

    def _draw_spiked_pauldron(surface, x, y, palette, mirror=False):
        direction = -1 if mirror else 1

        pad_pts = [
            (x - 4 * direction, y),
            (x + 3 * direction, y),
            (x + 4 * direction, y + 4),
            (x + 1 * direction, y + 6),
            (x - 4 * direction, y + 5),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in pad_pts])
        _NS_goblin._aapolygon(surface, palette['metal_darkest'], pad_pts)
        _NS_goblin._aapolygon(surface, palette['metal_dark'], [
            (x - 3 * direction, y + 1),
            (x + 2 * direction, y + 1),
            (x + 3 * direction, y + 4),
            (x, y + 5),
            (x - 3 * direction, y + 4),
        ])
        _NS_goblin._aapolygon(surface, palette['metal_mid'], [
            (x - 3 * direction, y + 1),
            (x + 1 * direction, y + 1),
            (x + 2 * direction, y + 3),
            (x - 1 * direction, y + 4),
            (x - 3 * direction, y + 3),
        ])
        _NS_goblin._aapolygon(surface, palette['metal_light'], [
            (x - 3 * direction, y + 1),
            (x - 1 * direction, y + 1),
            (x - 2 * direction, y + 3),
        ])
        pygame.draw.rect(surface, palette['metal_high'],
                         (x - 3 * direction, y + 1, 1, 1))

        # Gold trim bottom
        _NS_goblin._aaline(surface, palette['gold_dark'],
                (x - 4 * direction, y + 5),
                (x + 3 * direction, y + 5), 2)
        _NS_goblin._aaline(surface, palette['gold_mid'],
                (x - 4 * direction, y + 5),
                (x + 2 * direction, y + 5), 1)

        # 3 iron spikes on top
        for spike_i in range(3):
            sx = x + (-3 + spike_i * 3) * direction
            sy = y

            _NS_goblin._aapolygon(surface, palette['shadow_deep'], [
                (sx - 1, sy + 1), (sx, sy - 5), (sx + 1, sy + 1),
            ])
            _NS_goblin._aapolygon(surface, palette['metal_darkest'], [
                (sx - 1, sy), (sx, sy - 5), (sx + 1, sy),
            ])
            _NS_goblin._aapolygon(surface, palette['metal_dark'], [
                (sx - 1, sy), (sx, sy - 4), (sx + 1, sy),
            ])
            _NS_goblin._aapolygon(surface, palette['metal_mid'], [
                (sx - 1, sy), (sx, sy - 3), (sx, sy),
            ])
            pygame.draw.rect(surface, palette['metal_high'], (sx, sy - 3, 1, 2))
            pygame.draw.rect(surface, palette['metal_shine'], (sx, sy - 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # ARMS
    # ═══════════════════════════════════════════════════════

    def _draw_arm_offhand(surface, sx, sy, face, walk_phase, is_running,
                          palette, has_bracer=False):
        """Empty off-hand (fist)."""
        if is_running:
            arm_swing = math.sin(walk_phase) * 0.4
        else:
            arm_swing = math.sin(walk_phase * 0.5) * 0.1

        arm_angle = arm_swing * (-face)

        upper_len = 5
        elbow_x = sx + int(math.cos(arm_angle + math.pi / 2) * upper_len) * (-face)
        elbow_y = sy + int(math.sin(arm_angle + math.pi / 2) * upper_len) + 2

        _NS_goblin._draw_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = arm_angle * 1.4
        hand_x = elbow_x + int(math.cos(forearm_angle) * 5) * (-face)
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_goblin._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        if has_bracer:
            _NS_goblin._draw_bracer(surface, elbow_x, elbow_y, palette)

        _NS_goblin._draw_fist(surface, hand_x, hand_y, palette)


    def _draw_arm_offhand_dagger(surface, sx, sy, face, walk_phase,
                                  attack_progress, is_running, is_attacking,
                                  palette):
        """Off-hand also holds a dagger (lvl 5 dual wield)."""
        if is_attacking:
            if attack_progress < 0.25:
                t = attack_progress / 0.25
                swing_angle = -math.pi * 0.3 * t
                hand_extend = -t * 2
            elif attack_progress < 0.55:
                t = (attack_progress - 0.25) / 0.30
                swing_angle = -math.pi * 0.3 + t * math.pi * 0.5
                hand_extend = -2 + t * 5
            else:
                t = (attack_progress - 0.55) / 0.45
                swing_angle = math.pi * 0.2 - t * math.pi * 0.2
                hand_extend = 3 - t * 3
        elif is_running:
            swing_angle = math.sin(walk_phase) * 0.3
            hand_extend = 0
        else:
            swing_angle = math.sin(walk_phase * 0.5) * 0.1
            hand_extend = 0

        upper_len = 5
        base_angle = math.pi / 2 + swing_angle * (-face)
        elbow_x = sx + int(math.cos(base_angle) * upper_len) * (-face)
        elbow_y = sy + int(math.sin(base_angle) * upper_len) + 2

        _NS_goblin._draw_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = base_angle + swing_angle * 0.7 * (-face)
        hand_x = elbow_x + int(math.cos(forearm_angle) * (5 + hand_extend)) * (-face)
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_goblin._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)
        _NS_goblin._draw_bracer(surface, elbow_x, elbow_y, palette)
        _NS_goblin._draw_fist(surface, hand_x, hand_y, palette)

        weapon_angle = forearm_angle - math.pi / 2
        _NS_goblin._draw_dagger(surface, hand_x, hand_y, weapon_angle, -face,
                     palette, size='small')


    def _draw_arm_weapon(surface, sx, sy, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='dagger_small', has_bracer=False):
        """Main weapon-hand with full swing."""
        if is_attacking:
            if attack_progress < 0.25:
                t = attack_progress / 0.25
                t = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.6 * t
                hand_extend = -t * 3
            elif attack_progress < 0.55:
                t = (attack_progress - 0.25) / 0.30
                t = t ** 2
                swing_angle = -math.pi * 0.6 + t * math.pi * 1.0
                hand_extend = -3 + t * 10
            else:
                t = (attack_progress - 0.55) / 0.45
                t = 1 - (1 - t) ** 2
                swing_angle = math.pi * 0.4 - t * math.pi * 0.4
                hand_extend = 7 - t * 7
        elif is_running:
            swing_angle = math.sin(walk_phase + math.pi) * 0.3
            hand_extend = 0
        else:
            swing_angle = math.sin(walk_phase * 0.5) * 0.1
            hand_extend = 0

        upper_len = 5
        base_angle = math.pi / 2 + swing_angle * face
        elbow_x = sx + int(math.cos(base_angle) * upper_len) * face
        elbow_y = sy + int(math.sin(base_angle) * upper_len) + 2

        _NS_goblin._draw_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = base_angle + swing_angle * 0.7 * face
        hand_x = elbow_x + int(math.cos(forearm_angle) * (5 + hand_extend)) * face
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_goblin._draw_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        if has_bracer:
            _NS_goblin._draw_bracer(surface, elbow_x, elbow_y, palette)

        _NS_goblin._draw_fist(surface, hand_x, hand_y, palette)

        weapon_angle = forearm_angle - math.pi / 2
        glowing = is_attacking and 0.25 <= attack_progress <= 0.65

        if weapon == 'dagger_small':
            _NS_goblin._draw_dagger(surface, hand_x, hand_y, weapon_angle, face,
                         palette, size='small', glowing=glowing)
        elif weapon == 'dagger_big':
            _NS_goblin._draw_dagger(surface, hand_x, hand_y, weapon_angle, face,
                         palette, size='big', glowing=glowing)

        if is_attacking and 0.25 <= attack_progress <= 0.65:
            _NS_goblin._draw_swing_blur(surface, sx, sy, face, attack_progress,
                             hand_x, hand_y, palette)


    def _draw_arm(surface, x1, y1, x2, y2, palette):
        """Green arm segment."""
        _NS_goblin._aaline(surface, palette['shadow_deep'],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
        _NS_goblin._aaline(surface, palette['skin_darkest'], (x1, y1), (x2, y2), 5)
        _NS_goblin._aaline(surface, palette['skin_dark'], (x1, y1), (x2, y2), 4)
        _NS_goblin._aaline(surface, palette['skin_mid'], (x1, y1), (x2, y2), 3)
        _NS_goblin._aaline(surface, palette['skin_light'], (x1, y1), (x2, y2), 1)


    def _draw_bracer(surface, x, y, palette):
        """Leather bracer with metal stud."""
        _NS_goblin._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 4)
        _NS_goblin._aacircle(surface, palette['leather_darkest'], (x, y), 4)
        _NS_goblin._aacircle(surface, palette['leather_dark'], (x, y), 3)
        _NS_goblin._aacircle(surface, palette['leather_mid'], (x - 1, y - 1), 2)
        _NS_goblin._aacircle(surface, palette['leather_light'], (x - 1, y - 1), 1)

        _NS_goblin._aacircle(surface, palette['metal_dark'], (x, y), 1)
        pygame.draw.rect(surface, palette['metal_high'], (x, y - 1, 1, 1))

        _NS_goblin._aaline(surface, palette['gold_dark'],
                (x - 3, y + 2), (x + 3, y + 2), 1)
        _NS_goblin._aaline(surface, palette['gold_mid'],
                (x - 2, y + 2), (x + 2, y + 2), 1)


    def _draw_fist(surface, x, y, palette):
        """Green fist."""
        _NS_goblin._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 3)
        _NS_goblin._aacircle(surface, palette['skin_darkest'], (x, y), 3)
        _NS_goblin._aacircle(surface, palette['skin_dark'], (x, y), 2)
        _NS_goblin._aacircle(surface, palette['skin_mid'], (x - 1, y - 1), 1)
        pygame.draw.rect(surface, palette['skin_light'], (x - 1, y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # DAGGER (curved with gold cross-guard)
    # ═══════════════════════════════════════════════════════

    def _draw_dagger(surface, x, y, angle, face, palette, size='small',
                     glowing=False):
        """Curved goblin dagger with gold cross-guard."""
        blade_len = 7 if size == 'small' else 10

        cos_a = math.cos(angle) * face
        sin_a = math.sin(angle)
        perp_cos = -sin_a
        perp_sin = cos_a

        # HANDLE (leather-wrapped)
        handle_start_x = x - int(cos_a * 2)
        handle_start_y = y - int(sin_a * 2)
        handle_end_x = x + int(cos_a * 1)
        handle_end_y = y + int(sin_a * 1)

        _NS_goblin._aaline(surface, palette['shadow_deep'],
                (handle_start_x + 1, handle_start_y + 1),
                (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_goblin._aaline(surface, palette['leather_darkest'],
                (handle_start_x, handle_start_y),
                (handle_end_x, handle_end_y), 3)
        _NS_goblin._aaline(surface, palette['leather_dark'],
                (handle_start_x, handle_start_y),
                (handle_end_x, handle_end_y), 2)

        # Pommel (gold)
        _NS_goblin._aacircle(surface, palette['gold_darkest'],
                  (handle_start_x, handle_start_y), 2)
        _NS_goblin._aacircle(surface, palette['gold_dark'],
                  (handle_start_x, handle_start_y), 1)
        pygame.draw.rect(surface, palette['gold_high'],
                         (handle_start_x, handle_start_y - 1, 1, 1))

        # GOLD CROSS-GUARD
        guard_w = 3 if size == 'small' else 4
        guard_pts = [
            (int(x + perp_cos * guard_w), int(y + perp_sin * guard_w)),
            (int(x - perp_cos * guard_w), int(y - perp_sin * guard_w)),
            (int(x - perp_cos * guard_w + cos_a * 2),
             int(y - perp_sin * guard_w + sin_a * 2)),
            (int(x + perp_cos * guard_w + cos_a * 2),
             int(y + perp_sin * guard_w + sin_a * 2)),
        ]
        _NS_goblin._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in guard_pts])
        _NS_goblin._aapolygon(surface, palette['gold_darkest'], guard_pts)
        _NS_goblin._aapolygon(surface, palette['gold_dark'], [
            (int(x + perp_cos * (guard_w - 1)),
             int(y + perp_sin * (guard_w - 1))),
            (int(x - perp_cos * (guard_w - 1)),
             int(y - perp_sin * (guard_w - 1))),
            (int(x - perp_cos * (guard_w - 1) + cos_a * 1),
             int(y - perp_sin * (guard_w - 1) + sin_a * 1)),
            (int(x + perp_cos * (guard_w - 1) + cos_a * 1),
             int(y + perp_sin * (guard_w - 1) + sin_a * 1)),
        ])
        _NS_goblin._aapolygon(surface, palette['gold_mid'], [
            (int(x + perp_cos * (guard_w - 1)),
             int(y + perp_sin * (guard_w - 1))),
            (int(x - perp_cos * 1), int(y - perp_sin * 1)),
            (int(x + perp_cos * (guard_w - 1) + cos_a * 1),
             int(y + perp_sin * (guard_w - 1) + sin_a * 1)),
        ])
        pygame.draw.rect(surface, palette['gold_high'],
                         (int(x + perp_cos * (guard_w - 1)),
                          int(y + perp_sin * (guard_w - 1)), 1, 1))

        # CURVED BLADE
        blade_tip_x = x + int(cos_a * (blade_len + 2))
        blade_tip_y = y + int(sin_a * (blade_len + 2))
        blade_base_x = x + int(cos_a * 2)
        blade_base_y = y + int(sin_a * 2)

        # Curve: one edge slightly bowed
        curve_offset = 1 if size == 'small' else 2
        mid_x = (blade_base_x + blade_tip_x) // 2 + int(perp_cos * curve_offset)
        mid_y = (blade_base_y + blade_tip_y) // 2 + int(perp_sin * curve_offset)

        blade_w = 2 if size == 'small' else 3

        # Outline
        _NS_goblin._aapolygon(surface, palette['shadow'], [
            (int(blade_base_x + perp_cos * (blade_w + 1)),
             int(blade_base_y + perp_sin * (blade_w + 1))),
            (mid_x + int(perp_cos * 0.5), mid_y + int(perp_sin * 0.5)),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * (blade_w + 1)),
             int(blade_base_y - perp_sin * (blade_w + 1))),
        ])

        # Blade dark
        _NS_goblin._aapolygon(surface, palette['blade_dark'], [
            (int(blade_base_x + perp_cos * blade_w),
             int(blade_base_y + perp_sin * blade_w)),
            (mid_x, mid_y),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * blade_w),
             int(blade_base_y - perp_sin * blade_w)),
        ])

        # Blade mid
        _NS_goblin._aapolygon(surface, palette['blade_mid'], [
            (int(blade_base_x + perp_cos * (blade_w - 1)),
             int(blade_base_y + perp_sin * (blade_w - 1))),
            (mid_x, mid_y),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * (blade_w - 1)),
             int(blade_base_y - perp_sin * (blade_w - 1))),
        ])

        # Edge highlight (curved)
        _NS_goblin._aaline(surface, palette['blade_high'],
                (int(blade_base_x + perp_cos * (blade_w - 1)),
                 int(blade_base_y + perp_sin * (blade_w - 1))),
                (mid_x, mid_y), 1)
        _NS_goblin._aaline(surface, palette['blade_high'],
                (mid_x, mid_y), (blade_tip_x, blade_tip_y), 1)
        _NS_goblin._aaline(surface, palette['blade_shine'],
                (int(blade_base_x + perp_cos * (blade_w - 2)),
                 int(blade_base_y + perp_sin * (blade_w - 2))),
                (blade_tip_x, blade_tip_y), 1)

        # Sharp tip
        _NS_goblin._aacircle(surface, palette['shine'], (blade_tip_x, blade_tip_y), 1)

        # Deadly Nick purple glow when swinging
        if glowing:
            for r in (6, 4, 2):
                _NS_goblin._blend_alpha(surface,
                             (*palette['bleed_mid'], max(0, 150 - r * 20)),
                             [
                                 (blade_tip_x - r, blade_tip_y - r),
                                 (blade_tip_x + r, blade_tip_y - r),
                                 (blade_tip_x + r, blade_tip_y + r),
                                 (blade_tip_x - r, blade_tip_y + r),
                             ])
            _NS_goblin._aacircle(surface, palette['bleed_hot'],
                      (blade_tip_x, blade_tip_y), 2)
            # Purple sparks along blade
            _NS_goblin._aacircle(surface, palette['bleed_bright'], (mid_x, mid_y), 2)
            _NS_goblin._aacircle(surface, palette['bleed_hot'], (mid_x, mid_y), 1)


    def _draw_swing_blur(surface, sx, sy, face, progress, hand_x, hand_y,
                         palette):
        """Purple motion blur during swing."""
        for ghost_i in range(3):
            ghost_progress = progress - (ghost_i + 1) * 0.05
            if ghost_progress < 0.25:
                continue

            alpha = max(0, min(255, 90 - ghost_i * 25))
            if alpha <= 0:
                continue

            blur_surf = pygame.Surface((22, 22), pygame.SRCALPHA)
            _NS_goblin._aacircle(blur_surf, (*palette['bleed_dark'], alpha),
                      (11, 11), 5)
            _NS_goblin._aacircle(blur_surf, (*palette['bleed_mid'], alpha),
                      (11, 11), 3)
            _NS_goblin._aacircle(blur_surf, (*palette['bleed_bright'], alpha // 2),
                      (11, 11), 1)
            surface.blit(blur_surf,
                         (hand_x - 11 - ghost_i * 2 * face, hand_y - 11))


    # ═══════════════════════════════════════════════════════
    # DEADLY NICK ARC (Purple crescent - matches reference)
    # ═══════════════════════════════════════════════════════

    def _draw_deadly_nick_arc(surface, cx, cy, face, progress, palette):
        """Sweeping purple slash arc."""
        t = (progress - 0.30) / 0.40
        t = max(0.0, min(1.0, t))

        start_angle = math.radians(-100)
        end_angle = math.radians(60)
        current = start_angle + (end_angle - start_angle) * t

        center_x = cx + 6 * face
        center_y = cy - 4
        radius = 24

        # Multi-layer trail
        for i in range(14):
            offset = i * 0.11
            seg_t = t - offset * 0.05
            if seg_t < 0:
                continue
            seg_angle = start_angle + (end_angle - start_angle) * seg_t

            alpha_fade = 1.0 - offset
            alpha = max(0, min(255, int(220 * alpha_fade * math.sin(t * math.pi))))
            if alpha <= 0:
                continue

            for r_offset, blade_color, w in [
                (0, palette['bleed_darkest'], 5),
                (0, palette['bleed_dark'], 4),
                (0, palette['bleed_mid'], 3),
                (0, palette['bleed_light'], 2),
                (0, palette['bleed_bright'], 1),
            ]:
                inner_r = radius - 5 + r_offset
                outer_r = radius + 3 + r_offset

                ix = center_x + int(math.cos(seg_angle) * inner_r) * face
                iy = center_y + int(math.sin(seg_angle) * inner_r)
                ox = center_x + int(math.cos(seg_angle) * outer_r) * face
                oy = center_y + int(math.sin(seg_angle) * outer_r)

                _NS_goblin._blend_alpha(surface, (*blade_color, alpha), [
                    (ix, iy), (ox, oy),
                    (ox + 1, oy + 1), (ix + 1, iy + 1),
                ])
                _NS_goblin._aaline(surface, (*blade_color, alpha),
                        (ix, iy), (ox, oy), w)

        # Leading bright tip
        lead_alpha = int(240 * math.sin(t * math.pi))
        lead_x = center_x + int(math.cos(current) * radius) * face
        lead_y = center_y + int(math.sin(current) * radius)
        _NS_goblin._aacircle(surface, palette['bleed_bright'], (lead_x, lead_y), 4)
        _NS_goblin._aacircle(surface, palette['bleed_hot'], (lead_x, lead_y), 2)
        _NS_goblin._aacircle(surface, palette['shine'], (lead_x, lead_y), 1)

        # Purple droplets flying off
        for i in range(3):
            drop_a = current + i * 0.3
            drop_r = radius + 5 + i * 3
            dx = center_x + int(math.cos(drop_a) * drop_r) * face
            dy = center_y + int(math.sin(drop_a) * drop_r)
            _NS_goblin._aacircle(surface, palette['bleed_mid'], (dx, dy), 2)
            _NS_goblin._aacircle(surface, palette['bleed_hot'], (dx, dy), 1)


    def _draw_deadly_nick_impact(surface, cx, cy, face, progress, palette):
        """Purple sparkle burst at impact when Deadly Nick procs."""
        t = (progress - 0.50) / 0.13
        t = max(0.0, min(1.0, t))

        impact_x = cx + 22 * face
        impact_y = cy - 3

        # 4-pointed sparkle star
        star_r = int(5 + t * 8)
        alpha = int(240 * (1 - t))

        for angle_deg in [0, 45, 90, 135]:
            angle = math.radians(angle_deg)
            ox1 = impact_x + int(math.cos(angle) * star_r)
            oy1 = impact_y + int(math.sin(angle) * star_r)
            ox2 = impact_x - int(math.cos(angle) * star_r)
            oy2 = impact_y - int(math.sin(angle) * star_r)

            _NS_goblin._aaline(surface, (*palette['bleed_dark'], alpha),
                    (ox1, oy1), (ox2, oy2), 3)
            _NS_goblin._aaline(surface, (*palette['bleed_light'], alpha),
                    (ox1, oy1), (ox2, oy2), 2)
            _NS_goblin._aaline(surface, (*palette['bleed_hot'], alpha),
                    (ox1, oy1), (ox2, oy2), 1)

        # Central bright core
        core_alpha = int(255 * (1 - t))
        _NS_goblin._aacircle(surface, (*palette['bleed_bright'], core_alpha),
                  (impact_x, impact_y), 3)
        _NS_goblin._aacircle(surface, (*palette['bleed_hot'], core_alpha),
                  (impact_x, impact_y), 2)
        _NS_goblin._aacircle(surface, palette['shine'], (impact_x, impact_y),
                  max(1, int(1 + (1 - t))))


    # ═══════════════════════════════════════════════════════
    # BLEED PARTICLES + GROUND AURA + STACKS
    # ═══════════════════════════════════════════════════════

    def _draw_bleed_ground_aura(surface, x, y, radius, timer, palette,
                                 proc_intensity):
        """Small purple ground aura when bleeding proc is on target."""
        pulse = math.sin(timer * 0.15) * 0.3 + 0.7
        fade = min(1.0, proc_intensity / 60.0)  # fade based on proc timer

        aura_w = radius * 4
        aura_h = radius
        aura_surf = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)

        for r in range(radius, 3, -2):
            alpha = int((radius - r) * 4 * pulse * fade)
            alpha = max(0, min(150, alpha))
            if alpha > 0:
                pygame.draw.ellipse(aura_surf,
                                    (*palette['bleed_dark'], alpha),
                                    (aura_w // 2 - r * 2,
                                     aura_h // 2 - r // 3,
                                     r * 4, r // 2))

        inner_alpha = int(150 * pulse * fade)
        pygame.draw.ellipse(aura_surf,
                            (*palette['bleed_bright'], inner_alpha),
                            (aura_w // 2 - radius,
                             aura_h // 2 - radius // 4,
                             radius * 2, radius // 2), 1)

        surface.blit(aura_surf, (x - aura_w // 2, y - aura_h // 2))


    def _draw_bleed_particles(surface, x, y, radius, timer, palette,
                               proc_intensity):
        """Rising purple droplets from body when bleeding is applied."""
        fade = min(1.0, proc_intensity / 60.0)

        for i in range(6):
            phase = (timer * 0.04 + i * 0.16) % 1.0
            # Circle around body
            angle = i * math.pi * 2 / 6 + timer * 0.02
            base_x = x + int(math.cos(angle) * radius * 1.1)

            # Rise upward
            rise = int(phase * (radius * 2 + 8))
            py = y + radius - rise + int(math.sin(timer * 0.06 + i) * 2)

            alpha_fade = math.sin(phase * math.pi) * fade
            alpha = max(0, min(255, int(220 * alpha_fade)))
            if alpha <= 0:
                continue

            size = max(1, int(2 * alpha_fade))

            # Droplet shape (small circle)
            _NS_goblin._aacircle(surface, (*palette['bleed_dark'], alpha),
                      (base_x, py), size + 1)
            _NS_goblin._aacircle(surface, (*palette['bleed_bright'], alpha),
                      (base_x, py), size)
            _NS_goblin._aacircle(surface, (*palette['bleed_hot'], alpha),
                      (base_x, py), max(1, size - 1))


    def _draw_bleed_stacks_icons(surface, cx, cy, stacks, timer, palette):
        """Purple droplet icons above head showing bleed stacks (max 3)."""
        # Matches the reference: small purple flame/droplet icons above HP bar
        stacks = min(3, stacks)

        for i in range(stacks):
            icon_x = cx - (stacks - 1) * 6 + i * 12
            icon_y = cy + int(math.sin(timer * 0.15 + i * 0.5) * 1)

            # Small droplet shape
            pulse = math.sin(timer * 0.2 + i * 0.7) * 0.2 + 0.8

            # Shadow
            _NS_goblin._aapolygon(surface, palette['shadow'], [
                (icon_x - 3, icon_y + 1),
                (icon_x + 3, icon_y + 1),
                (icon_x + 2, icon_y - 3),
                (icon_x, icon_y - 6),
                (icon_x - 2, icon_y - 3),
            ])

            # Frame (dark rectangle)
            pygame.draw.rect(surface, palette['bleed_darkest'],
                             (icon_x - 4, icon_y - 6, 8, 9))
            pygame.draw.rect(surface, palette['bleed_dark'],
                             (icon_x - 4, icon_y - 6, 8, 9), 1)

            # Droplet body
            _NS_goblin._aapolygon(surface, palette['bleed_dark'], [
                (icon_x - 2, icon_y + 1),
                (icon_x + 2, icon_y + 1),
                (icon_x + 2, icon_y - 2),
                (icon_x, icon_y - 5),
                (icon_x - 2, icon_y - 2),
            ])
            _NS_goblin._aapolygon(surface, palette['bleed_mid'], [
                (icon_x - 1, icon_y),
                (icon_x + 1, icon_y),
                (icon_x + 1, icon_y - 2),
                (icon_x, icon_y - 4),
                (icon_x - 1, icon_y - 2),
            ])
            _NS_goblin._aapolygon(surface, palette['bleed_bright'], [
                (icon_x - 1, icon_y - 1),
                (icon_x, icon_y - 1),
                (icon_x, icon_y - 3),
                (icon_x - 1, icon_y - 2),
            ])
            pygame.draw.rect(surface, palette['bleed_hot'],
                             (icon_x - 1, icon_y - 3, 1, 1))

            # Glow
            glow_r = int(4 * pulse)
            if glow_r > 0:
                glow_surf = pygame.Surface((glow_r * 4, glow_r * 4),
                                            pygame.SRCALPHA)
                for gr in range(glow_r, 0, -1):
                    alpha = (glow_r - gr) * 30
                    alpha = max(0, min(120, alpha))
                    pygame.draw.circle(glow_surf,
                                       (*palette['bleed_mid'], alpha),
                                       (glow_r * 2, glow_r * 2), gr)
                surface.blit(glow_surf,
                             (icon_x - glow_r * 2, icon_y - 3 - glow_r * 2))


    # ═══════════════════════════════════════════════════════
    # MASTER AURA (Lvl 5)
    # ═══════════════════════════════════════════════════════

    def _draw_master_aura(surface, x, y, timer, palette):
        """Purple aura around Champion Cutpurse."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_r = 22
        aura_surf = pygame.Surface((aura_r * 3, aura_r * 3), pygame.SRCALPHA)

        for r in range(aura_r, 3, -2):
            alpha = int((aura_r - r) * 4 * pulse)
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                _NS_goblin._aacircle(aura_surf, (*palette['bleed_mid'], alpha),
                          (aura_r * 3 // 2, aura_r * 3 // 2), r)

        surface.blit(aura_surf,
                     (x - aura_r * 3 // 2, y - aura_r * 3 // 2))

        # Orbiting purple sparks
        for i in range(4):
            angle = timer * 0.06 + i * math.pi / 2
            sx = x + int(math.cos(angle) * 18)
            sy = y + int(math.sin(angle) * 12)
            _NS_goblin._aacircle(surface, palette['bleed_bright'], (sx, sy), 2)
            _NS_goblin._aacircle(surface, palette['bleed_hot'], (sx, sy), 1)

# ====================================================================
# orc.py
# ====================================================================
class _NS_orc:
    """Namespace orc - isi asli tidak diubah."""

    # ================================
    # minions/orc.py
    # HD Orc Warrior - The Brute of the Wastes
    # Melee brute with axe & Brutal Blows passive (red crit + slow)
    # ================================



    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')
    HAS_AALINES = hasattr(pygame.draw, 'aalines')


    def _clamp_color(color):
        if len(color) == 3:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
            )
        elif len(color) == 4:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))),
            )
        return color


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_orc._clamp_color(color)
        if _NS_orc.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aaline(surface, color, start, end, width=1):
        color = _NS_orc._clamp_color(color)
        if width == 1 and _NS_orc.HAS_AALINES:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.line(surface, color, start, end, width)
        except (TypeError, ValueError):
            pass


    def _aapolygon(surface, color, points):
        color = _NS_orc._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    def _blend_alpha(surface, color, rect_pts):
        """Draw a polygon with alpha blending."""
        if len(rect_pts) < 3:
            return
        xs = [p[0] for p in rect_pts]
        ys = [p[1] for p in rect_pts]
        minx, miny = min(xs) - 2, min(ys) - 2
        maxx, maxy = max(xs) + 2, max(ys) + 2
        w, h = maxx - minx, maxy - miny
        if w <= 0 or h <= 0:
            return
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        shifted = [(p[0] - minx, p[1] - miny) for p in rect_pts]
        pygame.draw.polygon(tmp, _NS_orc._clamp_color(color), shifted)
        surface.blit(tmp, (minx, miny))


    # ═══════════════════════════════════════════════════════
    # PALETTE - Orc Warrior (match reference)
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            # ═══ BLUE TEAM (Vibrant green orc - friendly) ═══
            return {
                # Skin (bright green - orc reference)
                'skin_darkest': (28, 65, 22),
                'skin_dark': (55, 105, 38),
                'skin_mid': (95, 155, 62),
                'skin_light': (140, 200, 88),
                'skin_high': (180, 230, 125),
                'skin_shine': (215, 245, 175),

                # Muscle shadow (deep)
                'muscle_dark': (18, 45, 15),
                'muscle_mid': (38, 78, 28),

                # Leather (warm brown)
                'leather_darkest': (32, 20, 10),
                'leather_dark': (68, 42, 22),
                'leather_mid': (110, 72, 38),
                'leather_light': (155, 108, 58),
                'leather_high': (200, 150, 90),

                # Pants (dark leather)
                'pants_darkest': (22, 14, 8),
                'pants_dark': (48, 30, 16),
                'pants_mid': (78, 52, 28),
                'pants_light': (115, 82, 48),

                # Metal (axe, buckles, boot caps)
                'metal_darkest': (28, 32, 40),
                'metal_dark': (60, 68, 82),
                'metal_mid': (115, 128, 148),
                'metal_light': (180, 195, 215),
                'metal_high': (225, 235, 250),
                'metal_shine': (255, 255, 255),

                # Axe blade
                'blade_dark': (48, 55, 68),
                'blade_mid': (108, 122, 142),
                'blade_light': (180, 195, 215),
                'blade_high': (230, 240, 255),
                'blade_shine': (255, 255, 255),

                # Gold (accents on shoulder)
                'gold_darkest': (90, 60, 12),
                'gold_dark': (150, 110, 25),
                'gold_mid': (215, 165, 55),
                'gold_light': (250, 210, 95),
                'gold_high': (255, 240, 160),

                # Shoulder pad (RED heraldry - match reference)
                'pad_darkest': (55, 15, 12),
                'pad_dark': (105, 30, 25),
                'pad_mid': (160, 55, 42),
                'pad_light': (205, 90, 70),
                'pad_high': (240, 135, 105),

                # Hair / topknot (dark)
                'hair_darkest': (18, 15, 15),
                'hair_dark': (38, 32, 32),
                'hair_mid': (65, 55, 52),
                'hair_light': (100, 88, 82),
                'hair_high': (145, 130, 120),

                # Tusks (ivory)
                'tusk_dark': (155, 140, 105),
                'tusk_mid': (215, 205, 175),
                'tusk_light': (245, 240, 220),
                'tusk_shine': (255, 253, 240),

                # Passive: BRUTAL BLOWS (blood red magic)
                'blood_darkest': (60, 8, 8),
                'blood_dark': (120, 20, 20),
                'blood_mid': (185, 40, 35),
                'blood_light': (230, 75, 60),
                'blood_bright': (255, 130, 100),
                'blood_hot': (255, 200, 180),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 5, 8),
                'eye_black': (10, 15, 5),
                'eye_yellow': (255, 220, 50),
                'eye_bright': (255, 250, 200),
                'mouth_dark': (55, 15, 15),
            }
        else:
            # ═══ RED TEAM (Darker sickly green - enemy) ═══
            return {
                'skin_darkest': (20, 45, 18),
                'skin_dark': (42, 80, 30),
                'skin_mid': (72, 122, 50),
                'skin_light': (108, 165, 75),
                'skin_high': (150, 205, 108),
                'skin_shine': (190, 235, 148),

                'muscle_dark': (14, 32, 12),
                'muscle_mid': (30, 58, 22),

                'leather_darkest': (25, 15, 7),
                'leather_dark': (55, 32, 15),
                'leather_mid': (90, 55, 25),
                'leather_light': (135, 88, 42),
                'leather_high': (180, 128, 70),

                'pants_darkest': (18, 10, 6),
                'pants_dark': (38, 22, 12),
                'pants_mid': (65, 42, 22),
                'pants_light': (95, 65, 38),

                'metal_darkest': (25, 20, 20),
                'metal_dark': (55, 48, 48),
                'metal_mid': (105, 88, 88),
                'metal_light': (165, 145, 145),
                'metal_high': (215, 195, 195),
                'metal_shine': (245, 235, 235),

                'blade_dark': (42, 42, 52),
                'blade_mid': (95, 95, 110),
                'blade_light': (160, 160, 180),
                'blade_high': (215, 215, 230),
                'blade_shine': (248, 248, 255),

                'gold_darkest': (65, 42, 10),
                'gold_dark': (110, 78, 20),
                'gold_mid': (165, 120, 40),
                'gold_light': (210, 170, 75),
                'gold_high': (240, 208, 130),

                # Darker shoulder pad
                'pad_darkest': (48, 12, 10),
                'pad_dark': (92, 25, 20),
                'pad_mid': (140, 45, 35),
                'pad_light': (185, 78, 55),
                'pad_high': (220, 118, 88),

                'hair_darkest': (15, 12, 12),
                'hair_dark': (32, 28, 28),
                'hair_mid': (58, 48, 45),
                'hair_light': (92, 80, 75),
                'hair_high': (135, 120, 110),

                'tusk_dark': (140, 125, 92),
                'tusk_mid': (200, 190, 158),
                'tusk_light': (238, 232, 210),
                'tusk_shine': (255, 250, 235),

                'blood_darkest': (55, 5, 5),
                'blood_dark': (115, 15, 15),
                'blood_mid': (180, 35, 30),
                'blood_light': (225, 70, 55),
                'blood_bright': (250, 125, 95),
                'blood_hot': (255, 195, 175),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 3, 5),
                'eye_black': (12, 5, 5),
                'eye_yellow': (255, 210, 50),
                'eye_bright': (255, 240, 195),
                'mouth_dark': (48, 12, 12),
            }


    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_orc(surface, minion, x, y):
        """Draw orc - CACHED"""
        from minions.base_renderer import cached_minion_draw
        cached_minion_draw(surface, minion, x, y, _NS_orc._draw_orc_full)


    def _draw_orc_full(surface, minion, x, y):
        """Original orc render (dipanggil oleh cache)"""
        palette = _NS_orc._get_palette(minion.team)

        walk_phase = minion.walk_cycle
        is_running = minion.is_moving
        anim_time = minion.anim_time

        # Attack anim
        attack_progress = 0
        is_attacking = False
        if minion.attack_anim_timer > 0:
            attack_progress = 1.0 - (minion.attack_anim_timer /
                                      minion.attack_anim_max)
            is_attacking = True

        # Body bob (heavier for orc)
        if is_running:
            body_bob = int(math.sin(walk_phase * 1.5) * 2)
        else:
            body_bob = int(math.sin(anim_time * 0.05) * 1)

        # Attack body lunge (bigger than goblin - orc is powerful)
        attack_offset_x = 0
        if is_attacking:
            if attack_progress < 0.25:
                p = attack_progress / 0.25
                attack_offset_x = int(-p * 4) * minion.direction
            elif attack_progress < 0.55:
                p = (attack_progress - 0.25) / 0.30
                ease = p * p * (3 - 2 * p)
                attack_offset_x = int((-4 + ease * 12)) * minion.direction
            else:
                p = (attack_progress - 0.55) / 0.45
                ease = 1 - (1 - p) * (1 - p)
                attack_offset_x = int((8 - ease * 8)) * minion.direction

        # Spawn scale (kept for compat)
        spawn_scale = 1.0
        if minion.spawn_anim > 0:
            spawn_scale = 1.0 - (minion.spawn_anim / 20.0) * 0.5
            spawn_scale = max(0.3, spawn_scale)

        draw_x = x + attack_offset_x
        draw_y = y + body_bob

        # Ground shadow (bigger for orc)
        _NS_orc._draw_ground_shadow(surface, x, y + minion.radius + 7, minion.radius)

        # Slow FX
        if minion.slow_timer > 0:
            draw_slow_effect(surface, x, y, minion.radius, anim_time)

        # Main body per level
        level = minion.nexus_level
        if level == 1:
            _NS_orc._draw_orc_lvl1(surface, minion, draw_x, draw_y,
                           walk_phase, attack_progress,
                           is_running, is_attacking, palette)
        elif level == 2:
            _NS_orc._draw_orc_lvl2(surface, minion, draw_x, draw_y,
                           walk_phase, attack_progress,
                           is_running, is_attacking, palette)
        elif level == 3:
            _NS_orc._draw_orc_lvl3(surface, minion, draw_x, draw_y,
                           walk_phase, attack_progress,
                           is_running, is_attacking, palette)
        elif level == 4:
            _NS_orc._draw_orc_lvl4(surface, minion, draw_x, draw_y,
                           walk_phase, attack_progress,
                           is_running, is_attacking, palette)
        else:
            _NS_orc._draw_orc_lvl5(surface, minion, draw_x, draw_y,
                           walk_phase, attack_progress,
                           is_running, is_attacking, palette)

        # Warchief aura for lvl 5
        if level >= 5:
            _NS_orc._draw_warchief_aura(surface, x, y, anim_time, palette)

        # Brutal Blows passive arc (during mid-swing)
        if is_attacking and 0.28 <= attack_progress <= 0.72:
            _NS_orc._draw_brutal_blows_arc(surface, draw_x, draw_y, minion.direction,
                                   attack_progress, palette)

        # Brutal Blows impact burst (at peak of swing)
        if is_attacking and 0.48 <= attack_progress <= 0.62:
            _NS_orc._draw_brutal_impact(surface, draw_x, draw_y, minion.direction,
                                attack_progress, palette)

        # Slash effects
        if minion.slash_effects:
            draw_slash_effects(surface, draw_x, draw_y, minion.slash_effects)


        # HP bar
        bar_w = minion.radius * 2 + 8
        by = y - minion.radius - 18
        draw_hp_bar(surface, x, by, bar_w,
                    minion.hp / minion.max_hp, minion.team)

        # Level stars
        if minion.nexus_level >= 3:
            for i in range(minion.nexus_level - 2):
                star_x = x - 5 + i * 5
                star_y = by - 5
                _NS_orc._aacircle(surface, palette['gold_light'], (star_x, star_y), 2)
                pygame.draw.rect(surface, palette['shine'],
                                 (star_x, star_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # GROUND SHADOW
    # ═══════════════════════════════════════════════════════

    def _draw_ground_shadow(surface, x, y, radius):
        """Big shadow for heavy orc."""
        shadow_surf = pygame.Surface((radius * 6, 14), pygame.SRCALPHA)
        for r in range(7, 0, -1):
            alpha = (7 - r) * 22
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                                (7 - r, 7 - r,
                                 radius * 6 - (7 - r) * 2, r * 2))
        pygame.draw.ellipse(shadow_surf, (10, 8, 5, 180),
                            (3, 3, radius * 6 - 6, 6))
        surface.blit(shadow_surf, (x - radius * 3, y - 7))


    # ═══════════════════════════════════════════════════════
    # LEVEL 1: GRUNT (basic bare-chested)
    # ═══════════════════════════════════════════════════════

    def _draw_orc_lvl1(surface, minion, x, y, walk_phase,
                       attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_orc._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_orc._draw_torso_bare(surface, bx, y - 2, face, palette, hurt)
        _NS_orc._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=False)
        _NS_orc._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_topknot=False, has_scar=False, has_warpaint=False)
        _NS_orc._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='axe_small', has_bracer=False)


    # ═══════════════════════════════════════════════════════
    # LEVEL 2: RAIDER (+leather harness +topknot)
    # ═══════════════════════════════════════════════════════

    def _draw_orc_lvl2(surface, minion, x, y, walk_phase,
                       attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_orc._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_orc._draw_torso_harness(surface, bx, y - 2, face, palette, hurt)
        _NS_orc._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_orc._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_topknot=True, has_scar=False, has_warpaint=False)
        _NS_orc._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='axe_small', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 3: WARRIOR (+RED shoulder pad +scar +bigger axe)
    # ═══════════════════════════════════════════════════════

    def _draw_orc_lvl3(surface, minion, x, y, walk_phase,
                       attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_orc._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_orc._draw_torso_harness(surface, bx, y - 2, face, palette, hurt)
        _NS_orc._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        # RED spiked shoulder pad (signature)
        _NS_orc._draw_red_shoulder_pad(surface, bx - r + 1, y - 4, palette,
                                has_spike=True)
        _NS_orc._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_topknot=True, has_scar=True, has_warpaint=False)
        _NS_orc._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='axe_big', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 4: BERSERKER (+war paint +both pads)
    # ═══════════════════════════════════════════════════════

    def _draw_orc_lvl4(surface, minion, x, y, walk_phase,
                       attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_orc._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_orc._draw_torso_harness(surface, bx, y - 2, face, palette, hurt)
        _NS_orc._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_orc._draw_red_shoulder_pad(surface, bx - r + 1, y - 4, palette,
                                has_spike=True)
        _NS_orc._draw_red_shoulder_pad(surface, bx + r - 1, y - 4, palette,
                                has_spike=True, mirror=True)
        _NS_orc._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_topknot=True, has_scar=True, has_warpaint=True)
        _NS_orc._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='axe_big', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 5: WARCHIEF (full armor + horned helm + huge axe)
    # ═══════════════════════════════════════════════════════

    def _draw_orc_lvl5(surface, minion, x, y, walk_phase,
                       attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_orc._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_orc._draw_torso_armored(surface, bx, y - 2, face, palette, hurt)
        _NS_orc._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_orc._draw_red_shoulder_pad(surface, bx - r + 1, y - 4, palette,
                                has_spike=True)
        _NS_orc._draw_red_shoulder_pad(surface, bx + r - 1, y - 4, palette,
                                has_spike=True, mirror=True)
        _NS_orc._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   has_topknot=True, has_scar=True, has_warpaint=True,
                   has_horns=True)
        _NS_orc._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='axe_huge', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEGS + BOOTS (heavy orc stance)
    # ═══════════════════════════════════════════════════════

    def _draw_legs(surface, cx, cy, phase, is_running, palette):
        """Two thick orc legs with heavy boots."""
        if is_running:
            swing_l = math.sin(phase * 2) * 3.5
            swing_r = -swing_l
        else:
            idle = math.sin(phase * 0.8) * 0.4
            swing_l = idle
            swing_r = -idle

        for side, swing in [(-1, swing_l), (1, swing_r)]:
            hip_x = cx + side * 4
            hip_y = cy - 2

            knee_x = hip_x + int(swing * 0.4)
            knee_y = cy + 3

            foot_x = hip_x + int(swing)
            foot_y = cy + 9

            # Shadow
            _NS_orc._aaline(surface, palette['shadow_deep'],
                    (hip_x + 1, hip_y + 1), (foot_x + 1, foot_y + 1), 6)

            # Thick pants (leather wraps)
            _NS_orc._aaline(surface, palette['pants_darkest'],
                    (hip_x, hip_y), (knee_x, knee_y), 6)
            _NS_orc._aaline(surface, palette['pants_dark'],
                    (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_orc._aaline(surface, palette['pants_mid'],
                    (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_orc._aaline(surface, palette['pants_light'],
                    (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)

            _NS_orc._aaline(surface, palette['pants_darkest'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 6)
            _NS_orc._aaline(surface, palette['pants_dark'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 5)
            _NS_orc._aaline(surface, palette['pants_mid'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 3)

            # Leather wrap bindings on shin
            for wy_off in [1, 4]:
                wy = knee_y + wy_off
                wx = hip_x + int(swing * (0.4 + wy_off * 0.15))
                _NS_orc._aaline(surface, palette['leather_darkest'],
                        (wx - 3, wy), (wx + 3, wy), 2)
                _NS_orc._aaline(surface, palette['leather_dark'],
                        (wx - 3, wy), (wx + 3, wy), 1)
                _NS_orc._aaline(surface, palette['leather_light'],
                        (wx - 2, wy), (wx + 1, wy), 1)

            # Knee guard (leather)
            _NS_orc._aacircle(surface, palette['leather_darkest'], (knee_x, knee_y), 3)
            _NS_orc._aacircle(surface, palette['leather_dark'], (knee_x, knee_y), 2)
            _NS_orc._aacircle(surface, palette['leather_mid'], (knee_x - 1, knee_y - 1), 1)

            # BIG BOOT
            _NS_orc._draw_heavy_boot(surface, foot_x, foot_y, palette)


    def _draw_heavy_boot(surface, fx, fy, palette):
        """Chunky orc boot with metal cap + straps."""
        # Main boot
        boot_pts = [
            (fx - 5, fy - 4),
            (fx + 5, fy - 4),
            (fx + 6, fy - 1),
            (fx + 5, fy + 1),
            (fx - 5, fy + 1),
            (fx - 6, fy - 1),
        ]
        _NS_orc._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in boot_pts])
        _NS_orc._aapolygon(surface, palette['leather_darkest'], boot_pts)
        _NS_orc._aapolygon(surface, palette['leather_dark'], [
            (fx - 4, fy - 3), (fx + 4, fy - 3),
            (fx + 5, fy - 1), (fx + 4, fy),
            (fx - 4, fy), (fx - 5, fy - 1),
        ])
        _NS_orc._aapolygon(surface, palette['leather_mid'], [
            (fx - 4, fy - 3), (fx + 3, fy - 3),
            (fx + 4, fy - 2), (fx + 3, fy - 1),
            (fx - 4, fy - 1),
        ])
        # Highlight
        _NS_orc._aaline(surface, palette['leather_light'],
                (fx - 3, fy - 3), (fx + 2, fy - 3), 1)

        # Metal toe cap (big)
        pygame.draw.rect(surface, palette['metal_darkest'],
                         (fx + 3, fy - 2, 4, 3))
        pygame.draw.rect(surface, palette['metal_dark'],
                         (fx + 3, fy - 2, 4, 2))
        pygame.draw.rect(surface, palette['metal_mid'],
                         (fx + 3, fy - 2, 3, 1))
        pygame.draw.rect(surface, palette['metal_high'],
                         (fx + 3, fy - 2, 1, 1))

        # Boot straps (crossing)
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (fx - 4, fy - 3, 7, 1))
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (fx - 4, fy - 1, 7, 1))
        # Gold buckle
        pygame.draw.rect(surface, palette['gold_dark'],
                         (fx - 1, fy - 3, 2, 3))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (fx - 1, fy - 3, 1, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (fx - 1, fy - 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # TORSO VARIANTS
    # ═══════════════════════════════════════════════════════

    def _draw_torso_bare(surface, cx, cy, face, palette, hurt):
        """Level 1 - bare chested muscular orc."""
        body_w = 20
        body_h = 16

        if hurt:
            skin_mid = (255, 255, 255)
            skin_light = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']
            skin_light = palette['skin_light']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=4)

        # Skin base (broad chest)
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=4)
        pygame.draw.rect(surface, palette['skin_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=4)
        pygame.draw.rect(surface, skin_mid,
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=4)
        pygame.draw.rect(surface, skin_light,
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=3)
        pygame.draw.rect(surface, palette['skin_high'],
                         (cx - body_w // 2 + 1, cy + 1, 4, 3),
                         border_radius=2)

        # Chest muscle definition (pecs)
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx, cy + 2), (cx, cy + 8), 2)
        # Pec shading
        _NS_orc._aacircle(surface, palette['skin_dark'], (cx - 4, cy + 5), 3)
        _NS_orc._aacircle(surface, palette['skin_mid'], (cx - 4, cy + 4), 2)
        _NS_orc._aacircle(surface, palette['skin_light'], (cx - 5, cy + 3), 1)

        _NS_orc._aacircle(surface, palette['skin_dark'], (cx + 4, cy + 5), 3)
        _NS_orc._aacircle(surface, palette['skin_mid'], (cx + 4, cy + 4), 2)

        # Ab lines (subtle)
        for ab_y in [cy + 8, cy + 11]:
            _NS_orc._aaline(surface, palette['muscle_dark'],
                    (cx - 3, ab_y), (cx + 3, ab_y), 1)
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx, cy + 8), (cx, cy + 13), 1)

        # Simple leather waistband
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, cy + body_h - 3, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, cy + body_h - 3, body_w - 1, 2))
        # Small buckle
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 2, cy + body_h - 3, 4, 3))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 2, cy + body_h - 3, 3, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 2, cy + body_h - 3, 1, 1))


    def _draw_torso_harness(surface, cx, cy, face, palette, hurt):
        """Level 2-4 - leather harness/vest with straps."""
        body_w = 22
        body_h = 17

        if hurt:
            skin_mid = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=4)

        # Skin base
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=4)
        pygame.draw.rect(surface, palette['skin_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=4)
        pygame.draw.rect(surface, skin_mid,
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=4)

        # Pec shading (still visible with harness)
        _NS_orc._aacircle(surface, palette['skin_dark'], (cx - 4, cy + 5), 3)
        _NS_orc._aacircle(surface, palette['skin_light'], (cx - 5, cy + 3), 1)
        _NS_orc._aacircle(surface, palette['skin_dark'], (cx + 4, cy + 5), 3)

        # Leather harness (X-strap across chest)
        _NS_orc._aaline(surface, palette['leather_darkest'],
                (cx - body_w // 2 + 2, cy + 2),
                (cx + body_w // 2 - 3, cy + body_h - 5), 4)
        _NS_orc._aaline(surface, palette['leather_dark'],
                (cx - body_w // 2 + 2, cy + 2),
                (cx + body_w // 2 - 3, cy + body_h - 5), 3)
        _NS_orc._aaline(surface, palette['leather_mid'],
                (cx - body_w // 2 + 2, cy + 2),
                (cx + body_w // 2 - 3, cy + body_h - 5), 1)

        _NS_orc._aaline(surface, palette['leather_darkest'],
                (cx + body_w // 2 - 3, cy + 2),
                (cx - body_w // 2 + 2, cy + body_h - 5), 4)
        _NS_orc._aaline(surface, palette['leather_dark'],
                (cx + body_w // 2 - 3, cy + 2),
                (cx - body_w // 2 + 2, cy + body_h - 5), 3)
        _NS_orc._aaline(surface, palette['leather_mid'],
                (cx + body_w // 2 - 3, cy + 2),
                (cx - body_w // 2 + 2, cy + body_h - 5), 1)

        # Central medallion (steel/iron)
        _NS_orc._aacircle(surface, palette['shadow'], (cx, cy + 7), 4)
        _NS_orc._aacircle(surface, palette['metal_darkest'], (cx, cy + 7), 4)
        _NS_orc._aacircle(surface, palette['metal_dark'], (cx, cy + 7), 3)
        _NS_orc._aacircle(surface, palette['metal_mid'], (cx - 1, cy + 6), 2)
        _NS_orc._aacircle(surface, palette['metal_high'], (cx - 1, cy + 6), 1)
        # Rune mark
        pygame.draw.rect(surface, palette['metal_darkest'], (cx - 1, cy + 6, 2, 3))
        pygame.draw.rect(surface, palette['blood_dark'], (cx, cy + 6, 1, 3))
        pygame.draw.rect(surface, palette['blood_bright'], (cx, cy + 7, 1, 1))

        # BIG belt
        belt_y = cy + body_h - 5
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - body_w // 2, belt_y + 1, body_w, 5))
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 5))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 4))
        pygame.draw.rect(surface, palette['leather_mid'],
                         (cx - body_w // 2, belt_y, body_w - 2, 2))
        _NS_orc._aaline(surface, palette['leather_light'],
                (cx - body_w // 2 + 1, belt_y),
                (cx + body_w // 2 - 3, belt_y), 1)

        # Big central gold buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 4, belt_y - 1 + 1, 8, 6))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 4, belt_y - 1, 8, 6))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 4, belt_y - 1, 7, 5))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 4, belt_y - 1, 5, 4))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 4, belt_y - 1, 3, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 4, belt_y - 1, 1, 1))

        # Small pouch on side
        _NS_orc._aapolygon(surface, palette['leather_darkest'], [
            (cx + 6, belt_y - 1),
            (cx + 9, belt_y - 1),
            (cx + 10, belt_y + 3),
            (cx + 5, belt_y + 3),
        ])
        _NS_orc._aapolygon(surface, palette['leather_dark'], [
            (cx + 6, belt_y),
            (cx + 9, belt_y),
            (cx + 9, belt_y + 2),
            (cx + 6, belt_y + 2),
        ])


    def _draw_torso_armored(surface, cx, cy, face, palette, hurt):
        """Level 5 - full plate + red heraldry."""
        body_w = 24
        body_h = 18

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=4)

        # Iron chestplate
        pygame.draw.rect(surface, palette['metal_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=4)
        pygame.draw.rect(surface, palette['metal_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=4)
        pygame.draw.rect(surface, palette['metal_mid'],
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=4)
        pygame.draw.rect(surface, palette['metal_light'],
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=3)
        pygame.draw.rect(surface, palette['metal_high'],
                         (cx - body_w // 2, cy, 6, 3), border_radius=1)

        # Gold trim top
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - body_w // 2, cy, body_w, 2))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - body_w // 2, cy, body_w - 1, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - body_w // 2 + 1, cy, 3, 1))

        # BIG red heraldry emblem (wolf/skull motif)
        # Shield shape
        _NS_orc._aapolygon(surface, palette['pad_darkest'], [
            (cx - 5, cy + 3),
            (cx + 5, cy + 3),
            (cx + 5, cy + 9),
            (cx + 2, cy + 12),
            (cx - 2, cy + 12),
            (cx - 5, cy + 9),
        ])
        _NS_orc._aapolygon(surface, palette['pad_dark'], [
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 4, cy + 8),
            (cx + 2, cy + 11),
            (cx - 2, cy + 11),
            (cx - 4, cy + 8),
        ])
        _NS_orc._aapolygon(surface, palette['pad_mid'], [
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 3, cy + 8),
            (cx, cy + 10),
            (cx - 3, cy + 8),
        ])
        # Wolf/skull symbol
        _NS_orc._aapolygon(surface, palette['pad_darkest'], [
            (cx - 2, cy + 6),
            (cx + 2, cy + 6),
            (cx + 1, cy + 9),
            (cx - 1, cy + 9),
        ])
        pygame.draw.rect(surface, palette['blood_bright'], (cx - 1, cy + 7, 2, 1))

        # Rivets
        for rx in [-body_w // 2 + 2, body_w // 2 - 3]:
            for ry in [2, body_h - 5]:
                _NS_orc._aacircle(surface, palette['metal_darkest'],
                          (cx + rx, cy + ry), 1)
                pygame.draw.rect(surface, palette['metal_high'],
                                 (cx + rx, cy + ry - 1, 1, 1))

        # Belt
        belt_y = cy + body_h - 4
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 2))

        # Big gold buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 5, belt_y - 1 + 1, 10, 5))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 5, belt_y - 1, 10, 5))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 5, belt_y - 1, 9, 4))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 5, belt_y - 1, 6, 3))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 5, belt_y - 1, 3, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 5, belt_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # HEAD (Orc - green, tusks, topknot)
    # ═══════════════════════════════════════════════════════

    def _draw_head(surface, cx, cy, face, palette, hurt,
                   has_topknot=False, has_scar=False, has_warpaint=False,
                   has_horns=False):
        """Orc head - big skull, prominent tusks."""
        if hurt:
            skin_mid = (255, 255, 255)
            skin_light = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']
            skin_light = palette['skin_light']

        head_r = 9  # bigger than goblin

        # ═══ EARS (smaller than goblin, more human-like) ═══
        # Back ear
        ear_b_pts = [
            (cx - head_r + 1, cy - 1),
            (cx - head_r - 3, cy - 4),
            (cx - head_r + 2, cy - 2),
        ]
        _NS_orc._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in ear_b_pts])
        _NS_orc._aapolygon(surface, palette['skin_darkest'], ear_b_pts)
        _NS_orc._aapolygon(surface, palette['skin_dark'], [
            (cx - head_r + 1, cy - 1),
            (cx - head_r - 2, cy - 3),
            (cx - head_r + 2, cy - 2),
        ])

        # Front ear (pointed slightly)
        ear_f_pts = [
            (cx + head_r - 1, cy - 1),
            (cx + head_r + 4, cy - 5),
            (cx + head_r + 1, cy - 2),
            (cx + head_r - 1, cy + 1),
        ]
        _NS_orc._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in ear_f_pts])
        _NS_orc._aapolygon(surface, palette['skin_darkest'], ear_f_pts)
        _NS_orc._aapolygon(surface, palette['skin_dark'], [
            (cx + head_r - 1, cy - 1),
            (cx + head_r + 3, cy - 4),
            (cx + head_r + 1, cy - 2),
        ])
        _NS_orc._aapolygon(surface, skin_mid, [
            (cx + head_r - 1, cy - 1),
            (cx + head_r + 2, cy - 3),
            (cx + head_r, cy - 2),
        ])
        _NS_orc._aaline(surface, skin_light,
                (cx + head_r, cy - 2), (cx + head_r + 2, cy - 3), 1)

        # ═══ HEAD SHAPE (big square-ish orc skull) ═══
        _NS_orc._aacircle(surface, palette['shadow_deep'], (cx + 1, cy + 1), head_r)
        _NS_orc._aacircle(surface, palette['skin_darkest'], (cx, cy), head_r)
        _NS_orc._aacircle(surface, palette['skin_dark'], (cx, cy), head_r - 1)
        _NS_orc._aacircle(surface, skin_mid, (cx - 1, cy - 1), head_r - 2)
        _NS_orc._aacircle(surface, skin_light, (cx - 2, cy - 2), head_r - 4)
        _NS_orc._aacircle(surface, palette['skin_high'], (cx - 3, cy - 3),
                  max(1, head_r - 6))

        # Strong jaw line
        _NS_orc._aaline(surface, palette['skin_darkest'],
                (cx - head_r + 1, cy + 4), (cx + head_r - 1, cy + 4), 1)
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx - head_r + 2, cy + 5), (cx - 2, cy + 6), 1)
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx + 2, cy + 6), (cx + head_r - 2, cy + 5), 1)

        # ═══ HEAVY BROW RIDGE ═══
        # Big protruding brow
        _NS_orc._aapolygon(surface, palette['skin_darkest'], [
            (cx - head_r + 1, cy - 3),
            (cx + head_r - 1, cy - 3),
            (cx + head_r - 2, cy - 1),
            (cx - head_r + 2, cy - 1),
        ])
        _NS_orc._aapolygon(surface, palette['skin_dark'], [
            (cx - head_r + 2, cy - 3),
            (cx + head_r - 2, cy - 3),
            (cx + head_r - 3, cy - 2),
            (cx - head_r + 3, cy - 2),
        ])
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx - head_r + 2, cy - 1), (cx + head_r - 2, cy - 1), 1)
        # Angry frown line
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx - 3, cy - 2), (cx, cy), 1)
        _NS_orc._aaline(surface, palette['muscle_dark'],
                (cx + 3, cy - 2), (cx, cy), 1)

        # ═══ EYES (small, deep-set, angry) ═══
        for eye_side, eye_x in [(-1, cx - 3), (1, cx + 3)]:
            # Socket
            _NS_orc._aacircle(surface, palette['shadow'], (eye_x, cy), 2)
            _NS_orc._aacircle(surface, palette['eye_black'], (eye_x, cy), 1)
            # Yellow eye
            pygame.draw.rect(surface, palette['eye_yellow'],
                             (eye_x, cy, 1, 1))
            # Shine
            if eye_side == -1:
                pygame.draw.rect(surface, palette['eye_bright'],
                                 (eye_x, cy - 1, 1, 1))

        # ═══ FLAT / WIDE NOSE ═══
        nose_pts = [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ]
        _NS_orc._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in nose_pts])
        _NS_orc._aapolygon(surface, palette['skin_darkest'], nose_pts)
        _NS_orc._aapolygon(surface, palette['skin_dark'], [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Nostrils
        pygame.draw.rect(surface, palette['shadow'], (cx - 2, cy + 3, 1, 1))
        pygame.draw.rect(surface, palette['shadow'], (cx + 1, cy + 3, 1, 1))

        # ═══ MOUTH with TUSKS ═══
        mouth_y = cy + 5
        # Mouth line
        pygame.draw.rect(surface, palette['mouth_dark'],
                         (cx - 4, mouth_y, 8, 1))
        _NS_orc._aaline(surface, palette['shadow'],
                (cx - 4, mouth_y + 1), (cx + 4, mouth_y + 1), 1)

        # TUSKS (big, pointing up-out - signature orc feature)
        # Left tusk
        _NS_orc._aapolygon(surface, palette['shadow_deep'], [
            (cx - 3, mouth_y),
            (cx - 4, mouth_y - 3),
            (cx - 2, mouth_y - 4),
            (cx - 2, mouth_y),
        ])
        _NS_orc._aapolygon(surface, palette['tusk_dark'], [
            (cx - 3, mouth_y),
            (cx - 4, mouth_y - 3),
            (cx - 2, mouth_y - 3),
            (cx - 2, mouth_y),
        ])
        _NS_orc._aapolygon(surface, palette['tusk_mid'], [
            (cx - 3, mouth_y),
            (cx - 3, mouth_y - 2),
            (cx - 2, mouth_y - 3),
            (cx - 2, mouth_y),
        ])
        _NS_orc._aapolygon(surface, palette['tusk_light'], [
            (cx - 3, mouth_y),
            (cx - 3, mouth_y - 2),
            (cx - 2, mouth_y - 2),
        ])
        pygame.draw.rect(surface, palette['tusk_shine'],
                         (cx - 3, mouth_y - 1, 1, 1))

        # Right tusk (bigger, more prominent)
        _NS_orc._aapolygon(surface, palette['shadow_deep'], [
            (cx + 2, mouth_y),
            (cx + 2, mouth_y - 4),
            (cx + 4, mouth_y - 3),
            (cx + 3, mouth_y),
        ])
        _NS_orc._aapolygon(surface, palette['tusk_dark'], [
            (cx + 2, mouth_y),
            (cx + 2, mouth_y - 3),
            (cx + 4, mouth_y - 3),
            (cx + 3, mouth_y),
        ])
        _NS_orc._aapolygon(surface, palette['tusk_mid'], [
            (cx + 2, mouth_y),
            (cx + 2, mouth_y - 3),
            (cx + 3, mouth_y - 3),
            (cx + 3, mouth_y),
        ])
        _NS_orc._aapolygon(surface, palette['tusk_light'], [
            (cx + 2, mouth_y),
            (cx + 2, mouth_y - 2),
            (cx + 3, mouth_y - 2),
        ])
        pygame.draw.rect(surface, palette['tusk_shine'],
                         (cx + 2, mouth_y - 1, 1, 1))

        # ═══ WAR PAINT (lvl 4+) ═══
        if has_warpaint:
            # Vertical stripes across face
            for stripe_x_off in [-5, -2, 1, 4]:
                sx = cx + stripe_x_off
                _NS_orc._aaline(surface, palette['blood_dark'],
                        (sx, cy + 1), (sx, cy + 5), 1)
                pygame.draw.rect(surface, palette['blood_mid'], (sx, cy + 2, 1, 1))
            # Horizontal band under eyes
            pygame.draw.rect(surface, palette['blood_dark'],
                             (cx - 5, cy + 1, 10, 1))

        # ═══ SCAR (lvl 3+) ═══
        if has_scar:
            # Diagonal scar across eye
            _NS_orc._aaline(surface, palette['muscle_dark'],
                    (cx - 4, cy - 3), (cx - 2, cy + 3), 1)
            _NS_orc._aaline(surface, palette['skin_darkest'],
                    (cx - 4, cy - 3), (cx - 2, cy + 3), 1)
            # Stitches
            for i in range(3):
                sx = cx - 4 + i
                sy = cy - 2 + i * 2
                pygame.draw.rect(surface, palette['skin_high'], (sx, sy, 1, 1))

        # ═══ TOPKNOT / MOHAWK (lvl 2+) ═══
        if has_topknot:
            _NS_orc._draw_topknot(surface, cx, cy - head_r + 1, palette)

        # ═══ HORNS (lvl 5 warchief) ═══
        if has_horns:
            _NS_orc._draw_horns(surface, cx, cy - head_r + 2, palette)


    def _draw_topknot(surface, cx, cy, palette):
        """Spiky black topknot / mohawk hair."""
        # Base band (leather tie)
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - 3, cy + 1, 6, 2))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - 3, cy + 1, 5, 1))

        # Spiky hair strands
        strands = [
            (-3, -6, -0.4),
            (-1, -8, -0.15),
            (0, -9, 0.05),
            (1, -8, 0.2),
            (3, -5, 0.5),
            (4, -3, 0.7),
        ]

        for hx_off, height, lean in strands:
            base_x = cx + hx_off
            tip_x = base_x + int(lean * abs(height))
            tip_y = cy + height

            # Shadow
            _NS_orc._aapolygon(surface, palette['shadow_deep'], [
                (base_x - 2, cy + 2),
                (tip_x + 1, tip_y + 1),
                (base_x + 2, cy + 2),
            ])
            # Hair layers
            _NS_orc._aapolygon(surface, palette['hair_darkest'], [
                (base_x - 2, cy + 1),
                (tip_x, tip_y),
                (base_x + 2, cy + 1),
            ])
            _NS_orc._aapolygon(surface, palette['hair_dark'], [
                (base_x - 1, cy + 1),
                (tip_x, tip_y + 1),
                (base_x + 1, cy + 1),
            ])
            _NS_orc._aapolygon(surface, palette['hair_mid'], [
                (base_x - 1, cy + 1),
                (tip_x, tip_y + 2),
                (base_x, cy + 1),
            ])
            _NS_orc._aaline(surface, palette['hair_light'],
                    (base_x, cy),
                    (tip_x, tip_y + 2), 1)


    def _draw_horns(surface, cx, cy, palette):
        """Iron horns coming out from helmet (lvl 5)."""
        for side in (-1, 1):
            # Base at side of head
            base_x = cx + side * 5
            base_y = cy
            # Horn curves outward and up
            mid_x = base_x + side * 4
            mid_y = cy - 2
            tip_x = base_x + side * 6
            tip_y = cy - 6

            # Shadow
            _NS_orc._aapolygon(surface, palette['shadow_deep'], [
                (base_x - 1, base_y + 1),
                (mid_x + 1, mid_y + 1),
                (tip_x + 1, tip_y + 1),
            ])

            # Horn layers (bone/iron)
            _NS_orc._aapolygon(surface, palette['tusk_dark'], [
                (base_x - 1, base_y),
                (base_x + 1, base_y),
                (mid_x, mid_y),
                (tip_x, tip_y),
            ])
            _NS_orc._aapolygon(surface, palette['tusk_mid'], [
                (base_x, base_y),
                (base_x + 1, base_y),
                (mid_x, mid_y),
                (tip_x, tip_y),
            ])
            _NS_orc._aaline(surface, palette['tusk_light'],
                    (base_x, base_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, palette['tusk_shine'],
                             (tip_x, tip_y, 1, 1))

        # Gold band across forehead
        pygame.draw.rect(surface, palette['gold_dark'], (cx - 5, cy, 10, 2))
        pygame.draw.rect(surface, palette['gold_mid'], (cx - 5, cy, 9, 1))
        pygame.draw.rect(surface, palette['gold_high'], (cx - 4, cy, 3, 1))

        # Red gem in center
        _NS_orc._aacircle(surface, palette['blood_darkest'], (cx, cy + 1), 2)
        _NS_orc._aacircle(surface, palette['blood_dark'], (cx, cy + 1), 1)
        pygame.draw.rect(surface, palette['blood_bright'], (cx, cy, 1, 1))


    # ═══════════════════════════════════════════════════════
    # RED SHOULDER PAD (with spikes - signature)
    # ═══════════════════════════════════════════════════════

    def _draw_red_shoulder_pad(surface, x, y, palette, has_spike=True,
                                mirror=False):
        """Big red shoulder pad with iron spikes (match reference)."""
        direction = -1 if mirror else 1

        # Curved pauldron shape (rounded top)
        pad_pts = [
            (x - 5 * direction, y),
            (x + 4 * direction, y),
            (x + 5 * direction, y + 3),
            (x + 4 * direction, y + 6),
            (x - 1 * direction, y + 7),
            (x - 5 * direction, y + 5),
        ]

        # Shadow
        _NS_orc._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in pad_pts])

        # Red pad layers
        _NS_orc._aapolygon(surface, palette['pad_darkest'], pad_pts)
        _NS_orc._aapolygon(surface, palette['pad_dark'], [
            (x - 4 * direction, y + 1),
            (x + 3 * direction, y + 1),
            (x + 4 * direction, y + 3),
            (x + 3 * direction, y + 5),
            (x - 1 * direction, y + 6),
            (x - 4 * direction, y + 4),
        ])
        _NS_orc._aapolygon(surface, palette['pad_mid'], [
            (x - 4 * direction, y + 1),
            (x + 2 * direction, y + 1),
            (x + 3 * direction, y + 3),
            (x + 1 * direction, y + 5),
            (x - 3 * direction, y + 4),
        ])
        _NS_orc._aapolygon(surface, palette['pad_light'], [
            (x - 4 * direction, y + 1),
            (x, y + 1),
            (x, y + 3),
            (x - 3 * direction, y + 3),
        ])
        pygame.draw.rect(surface, palette['pad_high'],
                         (x - 3 * direction, y + 1, 1, 1))

        # Iron rim / trim (bottom)
        _NS_orc._aaline(surface, palette['metal_darkest'],
                (x - 5 * direction, y + 6),
                (x + 4 * direction, y + 6), 2)
        _NS_orc._aaline(surface, palette['metal_dark'],
                (x - 5 * direction, y + 6),
                (x + 3 * direction, y + 6), 1)
        _NS_orc._aaline(surface, palette['metal_light'],
                (x - 5 * direction, y + 6),
                (x - 2 * direction, y + 6), 1)

        # Rivets on rim
        for rvx in [-3, 0, 3]:
            rvx_pos = x + rvx * direction
            _NS_orc._aacircle(surface, palette['metal_darkest'], (rvx_pos, y + 6), 1)
            pygame.draw.rect(surface, palette['metal_high'],
                             (rvx_pos, y + 5, 1, 1))

        # ═══ IRON SPIKES on top ═══
        if has_spike:
            for spike_i in range(3):
                sx = x + (-3 + spike_i * 3) * direction
                sy = y

                # Shadow
                _NS_orc._aapolygon(surface, palette['shadow_deep'], [
                    (sx - 1, sy + 1),
                    (sx, sy - 5),
                    (sx + 1, sy + 1),
                ])
                # Spike layers
                _NS_orc._aapolygon(surface, palette['metal_darkest'], [
                    (sx - 1, sy),
                    (sx, sy - 5),
                    (sx + 1, sy),
                ])
                _NS_orc._aapolygon(surface, palette['metal_dark'], [
                    (sx - 1, sy),
                    (sx, sy - 4),
                    (sx + 1, sy),
                ])
                _NS_orc._aapolygon(surface, palette['metal_mid'], [
                    (sx - 1, sy),
                    (sx, sy - 3),
                    (sx, sy),
                ])
                pygame.draw.rect(surface, palette['metal_high'], (sx, sy - 3, 1, 2))
                pygame.draw.rect(surface, palette['metal_shine'], (sx, sy - 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # ARMS
    # ═══════════════════════════════════════════════════════

    def _draw_arm_offhand(surface, sx, sy, face, walk_phase, is_running,
                          palette, has_bracer=False):
        """Empty off-hand (fist)."""
        if is_running:
            arm_swing = math.sin(walk_phase) * 0.4
        else:
            arm_swing = math.sin(walk_phase * 0.5) * 0.1

        arm_angle = arm_swing * (-face)

        upper_len = 6
        elbow_x = sx + int(math.cos(arm_angle + math.pi / 2) * upper_len) * (-face)
        elbow_y = sy + int(math.sin(arm_angle + math.pi / 2) * upper_len) + 2

        _NS_orc._draw_muscular_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = arm_angle * 1.4
        hand_x = elbow_x + int(math.cos(forearm_angle) * 5) * (-face)
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_orc._draw_muscular_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        if has_bracer:
            _NS_orc._draw_bracer(surface, elbow_x, elbow_y, palette)

        _NS_orc._draw_fist(surface, hand_x, hand_y, palette)


    def _draw_arm_weapon(surface, sx, sy, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='axe_small', has_bracer=False):
        """Weapon-hand with heavy axe swing."""
        if is_attacking:
            if attack_progress < 0.25:
                # Wind-up (raise axe overhead)
                t = attack_progress / 0.25
                t = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.7 * t
                hand_extend = -t * 3
            elif attack_progress < 0.55:
                # Chop down (fast)
                t = (attack_progress - 0.25) / 0.30
                t = t ** 2
                swing_angle = -math.pi * 0.7 + t * math.pi * 1.1
                hand_extend = -3 + t * 11
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                t = 1 - (1 - t) ** 2
                swing_angle = math.pi * 0.4 - t * math.pi * 0.4
                hand_extend = 8 - t * 8
        elif is_running:
            swing_angle = math.sin(walk_phase + math.pi) * 0.3
            hand_extend = 0
        else:
            swing_angle = math.sin(walk_phase * 0.5) * 0.1
            hand_extend = 0

        upper_len = 6
        base_angle = math.pi / 2 + swing_angle * face
        elbow_x = sx + int(math.cos(base_angle) * upper_len) * face
        elbow_y = sy + int(math.sin(base_angle) * upper_len) + 2

        _NS_orc._draw_muscular_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = base_angle + swing_angle * 0.7 * face
        hand_x = elbow_x + int(math.cos(forearm_angle) * (5 + hand_extend)) * face
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_orc._draw_muscular_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        if has_bracer:
            _NS_orc._draw_bracer(surface, elbow_x, elbow_y, palette)

        _NS_orc._draw_fist(surface, hand_x, hand_y, palette)

        weapon_angle = forearm_angle - math.pi / 2
        glowing = is_attacking and 0.25 <= attack_progress <= 0.65

        if weapon == 'axe_small':
            _NS_orc._draw_axe(surface, hand_x, hand_y, weapon_angle, face,
                      palette, size='small', glowing=glowing)
        elif weapon == 'axe_big':
            _NS_orc._draw_axe(surface, hand_x, hand_y, weapon_angle, face,
                      palette, size='big', glowing=glowing)
        elif weapon == 'axe_huge':
            _NS_orc._draw_axe(surface, hand_x, hand_y, weapon_angle, face,
                      palette, size='huge', glowing=glowing)

        if is_attacking and 0.25 <= attack_progress <= 0.65:
            _NS_orc._draw_swing_blur(surface, sx, sy, face, attack_progress,
                             hand_x, hand_y, palette)


    def _draw_muscular_arm(surface, x1, y1, x2, y2, palette):
        """Thick orc arm."""
        _NS_orc._aaline(surface, palette['shadow_deep'],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_orc._aaline(surface, palette['skin_darkest'], (x1, y1), (x2, y2), 6)
        _NS_orc._aaline(surface, palette['skin_dark'], (x1, y1), (x2, y2), 5)
        _NS_orc._aaline(surface, palette['skin_mid'], (x1, y1), (x2, y2), 3)
        _NS_orc._aaline(surface, palette['skin_light'], (x1, y1), (x2, y2), 1)


    def _draw_bracer(surface, x, y, palette):
        """Leather bracer with metal stud + gold trim."""
        _NS_orc._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 4)
        _NS_orc._aacircle(surface, palette['leather_darkest'], (x, y), 4)
        _NS_orc._aacircle(surface, palette['leather_dark'], (x, y), 3)
        _NS_orc._aacircle(surface, palette['leather_mid'], (x - 1, y - 1), 2)
        _NS_orc._aacircle(surface, palette['leather_light'], (x - 1, y - 1), 1)

        # Central metal stud
        _NS_orc._aacircle(surface, palette['metal_dark'], (x, y), 1)
        pygame.draw.rect(surface, palette['metal_high'], (x, y - 1, 1, 1))

        # Gold band
        _NS_orc._aaline(surface, palette['gold_dark'],
                (x - 3, y + 2), (x + 3, y + 2), 1)
        _NS_orc._aaline(surface, palette['gold_mid'],
                (x - 2, y + 2), (x + 2, y + 2), 1)


    def _draw_fist(surface, x, y, palette):
        """Big green fist."""
        _NS_orc._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 3)
        _NS_orc._aacircle(surface, palette['skin_darkest'], (x, y), 3)
        _NS_orc._aacircle(surface, palette['skin_dark'], (x, y), 2)
        _NS_orc._aacircle(surface, palette['skin_mid'], (x - 1, y - 1), 1)
        pygame.draw.rect(surface, palette['skin_light'], (x - 1, y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # AXE (single-bladed orcish battle axe)
    # ═══════════════════════════════════════════════════════

    def _draw_axe(surface, x, y, angle, face, palette, size='small',
                  glowing=False):
        """Single-bladed orc axe with wooden handle."""
        if size == 'small':
            haft_len = 10
            blade_size = 4
        elif size == 'big':
            haft_len = 12
            blade_size = 5
        else:  # huge
            haft_len = 14
            blade_size = 6

        cos_a = math.cos(angle) * face
        sin_a = math.sin(angle)
        perp_cos = -sin_a
        perp_sin = cos_a

        # ═══ WOODEN HAFT (handle) ═══
        haft_start_x = x - int(cos_a * 3)
        haft_start_y = y - int(sin_a * 3)
        haft_end_x = x + int(cos_a * haft_len)
        haft_end_y = y + int(sin_a * haft_len)

        # Shadow
        _NS_orc._aaline(surface, palette['shadow_deep'],
                (haft_start_x + 1, haft_start_y + 1),
                (haft_end_x + 1, haft_end_y + 1), 3)

        # Wood layers
        _NS_orc._aaline(surface, palette['leather_darkest'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 3)
        _NS_orc._aaline(surface, palette['leather_dark'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 2)
        _NS_orc._aaline(surface, palette['leather_light'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 1)

        # Leather wrap on grip
        grip_mx = haft_start_x + int(cos_a * 1)
        grip_my = haft_start_y + int(sin_a * 1)
        _NS_orc._aacircle(surface, palette['leather_darkest'], (grip_mx, grip_my), 2)
        _NS_orc._aacircle(surface, palette['leather_dark'], (grip_mx, grip_my), 1)

        # Pommel (metal cap at base)
        _NS_orc._aacircle(surface, palette['metal_darkest'],
                  (haft_start_x, haft_start_y), 2)
        _NS_orc._aacircle(surface, palette['metal_dark'],
                  (haft_start_x, haft_start_y), 1)
        pygame.draw.rect(surface, palette['metal_high'],
                         (haft_start_x, haft_start_y - 1, 1, 1))

        # ═══ AXE HEAD (at end of haft) ═══
        # Blade center at haft end
        bcx = haft_end_x
        bcy = haft_end_y

        # Axe head shape - crescent single-bladed
        # Blade points perpendicular to haft, on one side
        blade_dir = 1  # front side

        # Blade points (crescent shape)
        b1_x = bcx + int(perp_cos * blade_size * blade_dir)
        b1_y = bcy + int(perp_sin * blade_size * blade_dir)
        b2_x = bcx + int(perp_cos * blade_size * 1.3 * blade_dir) - int(cos_a * blade_size * 0.5)
        b2_y = bcy + int(perp_sin * blade_size * 1.3 * blade_dir) - int(sin_a * blade_size * 0.5)
        b3_x = bcx + int(perp_cos * blade_size * 1.3 * blade_dir) + int(cos_a * blade_size * 0.5)
        b3_y = bcy + int(perp_sin * blade_size * 1.3 * blade_dir) + int(sin_a * blade_size * 0.5)

        # Back edge (opposite spike / smaller)
        back_x = bcx - int(perp_cos * blade_size * 0.4 * blade_dir)
        back_y = bcy - int(perp_sin * blade_size * 0.4 * blade_dir)

        blade_pts = [
            (bcx + int(cos_a * 2), bcy + int(sin_a * 2)),
            (b3_x, b3_y),
            (b1_x, b1_y),
            (b2_x, b2_y),
            (bcx - int(cos_a * 2), bcy - int(sin_a * 2)),
            (back_x, back_y),
        ]

        # Shadow
        _NS_orc._aapolygon(surface, palette['shadow'],
                   [(p[0] + 1, p[1] + 1) for p in blade_pts])
        # Outline
        _NS_orc._aapolygon(surface, palette['blade_dark'], blade_pts)

        # Inner blade (mid tone)
        inner_pts = [
            (bcx + int(cos_a * 1), bcy + int(sin_a * 1)),
            (int((b3_x + b1_x) / 2), int((b3_y + b1_y) / 2)),
            (int((b1_x + b2_x) / 2), int((b1_y + b2_y) / 2)),
            (bcx - int(cos_a * 1), bcy - int(sin_a * 1)),
        ]
        _NS_orc._aapolygon(surface, palette['blade_mid'], inner_pts)

        # Bright edge highlight (crescent)
        _NS_orc._aaline(surface, palette['blade_high'], (b2_x, b2_y), (b1_x, b1_y), 1)
        _NS_orc._aaline(surface, palette['blade_high'], (b1_x, b1_y), (b3_x, b3_y), 1)
        _NS_orc._aaline(surface, palette['blade_shine'],
                (int((b1_x + b2_x) / 2), int((b1_y + b2_y) / 2)),
                (b1_x, b1_y), 1)

        # Iron mount / bindings around haft where blade attaches
        _NS_orc._aacircle(surface, palette['metal_darkest'], (bcx, bcy), 3)
        _NS_orc._aacircle(surface, palette['metal_dark'], (bcx, bcy), 2)
        _NS_orc._aacircle(surface, palette['metal_mid'], (bcx - 1, bcy - 1), 1)
        pygame.draw.rect(surface, palette['metal_high'], (bcx - 1, bcy - 1, 1, 1))

        # Sharp edge shine
        _NS_orc._aacircle(surface, palette['shine'], (b1_x, b1_y), 1)

        # Brutal Blows red glow around axe when swinging
        if glowing:
            for r in (8, 5, 3):
                _NS_orc._blend_alpha(surface,
                             (*palette['blood_mid'], max(0, 130 - r * 12)),
                             [
                                 (b1_x - r, b1_y - r),
                                 (b1_x + r, b1_y - r),
                                 (b1_x + r, b1_y + r),
                                 (b1_x - r, b1_y + r),
                             ])
            _NS_orc._aacircle(surface, palette['blood_bright'], (b1_x, b1_y), 3)
            _NS_orc._aacircle(surface, palette['blood_hot'], (b1_x, b1_y), 2)
            _NS_orc._aacircle(surface, palette['shine'], (b1_x, b1_y), 1)


    def _draw_swing_blur(surface, sx, sy, face, progress, hand_x, hand_y,
                         palette):
        """Motion blur during swing (red tinted for Brutal Blows)."""
        for ghost_i in range(4):
            ghost_progress = progress - (ghost_i + 1) * 0.05
            if ghost_progress < 0.25:
                continue

            alpha = max(0, min(255, 100 - ghost_i * 22))
            if alpha <= 0:
                continue

            blur_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            _NS_orc._aacircle(blur_surf, (*palette['blood_dark'], alpha),
                      (12, 12), 6)
            _NS_orc._aacircle(blur_surf, (*palette['blood_mid'], alpha),
                      (12, 12), 4)
            _NS_orc._aacircle(blur_surf, (*palette['blood_bright'], alpha // 2),
                      (12, 12), 2)
            surface.blit(blur_surf,
                         (hand_x - 12 - ghost_i * 2 * face, hand_y - 12))


    # ═══════════════════════════════════════════════════════
    # BRUTAL BLOWS ARC (Passive - red crescent slash)
    # ═══════════════════════════════════════════════════════

    def _draw_brutal_blows_arc(surface, cx, cy, face, progress, palette):
        """Sweeping red slash arc - the Brutal Blows passive."""
        t = (progress - 0.28) / 0.44
        t = max(0.0, min(1.0, t))

        # Arc sweeps top-back to bottom-front (chop motion)
        start_angle = math.radians(-105)
        end_angle = math.radians(55)
        current = start_angle + (end_angle - start_angle) * t

        center_x = cx + 8 * face
        center_y = cy - 6
        radius = 26

        # Multi-layered slash trail
        for i in range(16):
            offset = i * 0.09
            seg_t = t - offset * 0.05
            if seg_t < 0:
                continue
            seg_angle = start_angle + (end_angle - start_angle) * seg_t

            alpha_fade = 1.0 - offset
            alpha = max(0, min(255, int(230 * alpha_fade * math.sin(t * math.pi))))
            if alpha <= 0:
                continue

            for r_offset, blade_color, w in [
                (0, palette['blood_darkest'], 6),
                (0, palette['blood_dark'], 5),
                (0, palette['blood_mid'], 3),
                (0, palette['blood_light'], 2),
                (0, palette['blood_bright'], 1),
            ]:
                inner_r = radius - 6 + r_offset
                outer_r = radius + 4 + r_offset

                ix = center_x + int(math.cos(seg_angle) * inner_r) * face
                iy = center_y + int(math.sin(seg_angle) * inner_r)
                ox = center_x + int(math.cos(seg_angle) * outer_r) * face
                oy = center_y + int(math.sin(seg_angle) * outer_r)

                _NS_orc._blend_alpha(surface, (*blade_color, alpha), [
                    (ix, iy), (ox, oy),
                    (ox + 1, oy + 1), (ix + 1, iy + 1),
                ])
                _NS_orc._aaline(surface, (*blade_color, alpha),
                        (ix, iy), (ox, oy), w)

        # Leading bright edge (tip of slash)
        lead_alpha = int(250 * math.sin(t * math.pi))
        lead_angle = current
        lead_x = center_x + int(math.cos(lead_angle) * radius) * face
        lead_y = center_y + int(math.sin(lead_angle) * radius)
        _NS_orc._aacircle(surface, palette['blood_bright'], (lead_x, lead_y), 5)
        _NS_orc._aacircle(surface, palette['blood_hot'], (lead_x, lead_y), 3)
        _NS_orc._aacircle(surface, palette['shine'], (lead_x, lead_y), 1)

        # Small blood droplets flying off
        for i in range(4):
            drop_a = lead_angle + i * 0.25
            drop_r = radius + 6 + i * 3
            dx = center_x + int(math.cos(drop_a) * drop_r) * face
            dy = center_y + int(math.sin(drop_a) * drop_r)
            _NS_orc._aacircle(surface, palette['blood_dark'], (dx, dy), 2)
            _NS_orc._aacircle(surface, palette['blood_bright'], (dx, dy), 1)


    def _draw_brutal_impact(surface, cx, cy, face, progress, palette):
        """Red impact burst at the peak of the swing (Brutal Blows crit visual)."""
        t = (progress - 0.48) / 0.14
        t = max(0.0, min(1.0, t))

        # Impact location - in front of orc where axe lands
        impact_x = cx + 22 * face
        impact_y = cy - 2

        # Expanding shockwave
        shock_r = int(4 + t * 14)
        alpha_ring = int(200 * (1 - t))

        # Ring shockwave
        ring_surf = pygame.Surface((shock_r * 3, shock_r * 3), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*palette['blood_bright'], alpha_ring),
                           (shock_r * 3 // 2, shock_r * 3 // 2), shock_r, 2)
        pygame.draw.circle(ring_surf, (*palette['blood_hot'], alpha_ring // 2),
                           (shock_r * 3 // 2, shock_r * 3 // 2), shock_r - 1, 1)
        surface.blit(ring_surf,
                     (impact_x - shock_r * 3 // 2,
                      impact_y - shock_r * 3 // 2))

        # Radial spikes (like the passive icon)
        spike_count = 8
        for i in range(spike_count):
            angle = i * math.pi * 2 / spike_count + t * 0.3
            s_inner = 3 + int(t * 4)
            s_outer = 6 + int(t * 10)
            ix = impact_x + int(math.cos(angle) * s_inner)
            iy = impact_y + int(math.sin(angle) * s_inner)
            ox = impact_x + int(math.cos(angle) * s_outer)
            oy = impact_y + int(math.sin(angle) * s_outer)

            alpha = max(0, min(255, int(230 * (1 - t))))
            _NS_orc._blend_alpha(surface, (*palette['blood_darkest'], alpha), [
                (ix - 1, iy - 1), (ox - 1, oy - 1),
                (ox + 1, oy + 1), (ix + 1, iy + 1),
            ])
            _NS_orc._aaline(surface, (*palette['blood_dark'], alpha), (ix, iy), (ox, oy), 3)
            _NS_orc._aaline(surface, (*palette['blood_light'], alpha),
                    (ix, iy), (ox, oy), 2)
            _NS_orc._aaline(surface, (*palette['blood_hot'], alpha), (ix, iy), (ox, oy), 1)

        # Central bright burst
        core_alpha = int(255 * (1 - t))
        _NS_orc._aacircle(surface, (*palette['blood_bright'], core_alpha),
                  (impact_x, impact_y), 4)
        _NS_orc._aacircle(surface, (*palette['blood_hot'], core_alpha),
                  (impact_x, impact_y), 2)
        _NS_orc._aacircle(surface, palette['shine'], (impact_x, impact_y),
                  max(1, int(1 + (1 - t))))


    # ═══════════════════════════════════════════════════════
    # WARCHIEF AURA (Lvl 5)
    # ═══════════════════════════════════════════════════════

    def _draw_warchief_aura(surface, x, y, timer, palette):
        """Red rage aura around warchief."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_r = 24
        aura_surf = pygame.Surface((aura_r * 3, aura_r * 3), pygame.SRCALPHA)

        for r in range(aura_r, 3, -2):
            alpha = int((aura_r - r) * 4 * pulse)
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                _NS_orc._aacircle(aura_surf, (*palette['blood_mid'], alpha),
                          (aura_r * 3 // 2, aura_r * 3 // 2), r)

        surface.blit(aura_surf,
                     (x - aura_r * 3 // 2, y - aura_r * 3 // 2))

        # Orbiting red embers
        for i in range(4):
            angle = timer * 0.05 + i * math.pi / 2
            sx = x + int(math.cos(angle) * 20)
            sy = y + int(math.sin(angle) * 14)
            _NS_orc._aacircle(surface, palette['blood_bright'], (sx, sy), 2)
            _NS_orc._aacircle(surface, palette['blood_hot'], (sx, sy), 1)

# ====================================================================
# troll.py
# ====================================================================
class _NS_troll:
    """Namespace troll - isi asli tidak diubah."""

    # ================================
    # minions/troll.py
    # HD Troll - The Savage of the Jungle
    # Melee brute with spiked mace & Regeneration passive (green heal)
    # ================================



    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')
    HAS_AALINES = hasattr(pygame.draw, 'aalines')


    def _clamp_color(color):
        if len(color) == 3:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
            )
        elif len(color) == 4:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))),
            )
        return color


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_troll._clamp_color(color)
        if _NS_troll.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aaline(surface, color, start, end, width=1):
        color = _NS_troll._clamp_color(color)
        if width == 1 and _NS_troll.HAS_AALINES:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.line(surface, color, start, end, width)
        except (TypeError, ValueError):
            pass


    def _aapolygon(surface, color, points):
        color = _NS_troll._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    def _blend_alpha(surface, color, rect_pts):
        if len(rect_pts) < 3:
            return
        xs = [p[0] for p in rect_pts]
        ys = [p[1] for p in rect_pts]
        minx, miny = min(xs) - 2, min(ys) - 2
        maxx, maxy = max(xs) + 2, max(ys) + 2
        w, h = maxx - minx, maxy - miny
        if w <= 0 or h <= 0:
            return
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        shifted = [(p[0] - minx, p[1] - miny) for p in rect_pts]
        pygame.draw.polygon(tmp, _NS_troll._clamp_color(color), shifted)
        surface.blit(tmp, (minx, miny))


    # ═══════════════════════════════════════════════════════
    # PALETTE - Troll (blue-teal skin, red mohawk)
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            # ═══ BLUE TEAM (Bright teal - alive/friendly) ═══
            return {
                # Skin (blue-teal - match reference)
                'skin_darkest': (15, 45, 55),
                'skin_dark': (32, 82, 95),
                'skin_mid': (58, 125, 138),
                'skin_light': (95, 170, 180),
                'skin_high': (145, 210, 218),
                'skin_shine': (195, 235, 240),

                # Muscle shadow
                'muscle_dark': (10, 32, 40),
                'muscle_mid': (22, 60, 72),

                # Leather (worn brown)
                'leather_darkest': (30, 20, 12),
                'leather_dark': (62, 42, 22),
                'leather_mid': (105, 72, 40),
                'leather_light': (150, 108, 62),
                'leather_high': (195, 148, 92),

                # Pants (dark leather wrap)
                'pants_darkest': (20, 14, 8),
                'pants_dark': (45, 30, 16),
                'pants_mid': (78, 52, 28),
                'pants_light': (115, 82, 48),

                # Metal (spikes, buckles) - dark iron
                'metal_darkest': (24, 26, 30),
                'metal_dark': (55, 60, 68),
                'metal_mid': (105, 115, 128),
                'metal_light': (170, 180, 195),
                'metal_high': (220, 228, 240),
                'metal_shine': (255, 255, 255),

                # Wood (mace haft)
                'wood_darkest': (28, 18, 10),
                'wood_dark': (60, 38, 18),
                'wood_mid': (95, 65, 32),
                'wood_light': (140, 100, 55),
                'wood_high': (185, 145, 90),

                # Mace head (stone/bone)
                'stone_darkest': (55, 45, 30),
                'stone_dark': (95, 78, 55),
                'stone_mid': (145, 125, 90),
                'stone_light': (195, 175, 135),
                'stone_high': (235, 220, 185),

                # Gold accents
                'gold_darkest': (85, 55, 12),
                'gold_dark': (145, 105, 25),
                'gold_mid': (210, 160, 55),
                'gold_light': (245, 205, 95),
                'gold_high': (255, 235, 160),

                # HAIR / MOHAWK (bright red - signature)
                'hair_darkest': (80, 15, 15),
                'hair_dark': (140, 30, 25),
                'hair_mid': (200, 55, 42),
                'hair_light': (240, 95, 70),
                'hair_high': (255, 145, 110),

                # Tusks (ivory - bottom-up fangs)
                'tusk_dark': (150, 135, 100),
                'tusk_mid': (210, 200, 170),
                'tusk_light': (245, 240, 220),
                'tusk_shine': (255, 253, 240),

                # PASSIVE: REGENERATION (green healing)
                'heal_darkest': (18, 55, 15),
                'heal_dark': (40, 115, 35),
                'heal_mid': (75, 180, 62),
                'heal_light': (130, 230, 105),
                'heal_bright': (185, 250, 155),
                'heal_hot': (225, 255, 205),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 8, 10),
                'eye_black': (10, 15, 5),
                'eye_yellow': (255, 220, 50),
                'eye_bright': (255, 250, 200),
                'mouth_dark': (35, 10, 15),
            }
        else:
            # ═══ RED TEAM (Darker sickly teal) ═══
            return {
                'skin_darkest': (12, 32, 42),
                'skin_dark': (25, 62, 75),
                'skin_mid': (48, 100, 115),
                'skin_light': (80, 145, 158),
                'skin_high': (125, 185, 198),
                'skin_shine': (175, 218, 228),

                'muscle_dark': (8, 22, 30),
                'muscle_mid': (18, 45, 55),

                'leather_darkest': (25, 15, 7),
                'leather_dark': (55, 32, 15),
                'leather_mid': (90, 55, 25),
                'leather_light': (135, 88, 42),
                'leather_high': (180, 128, 70),

                'pants_darkest': (18, 10, 6),
                'pants_dark': (38, 22, 12),
                'pants_mid': (65, 42, 22),
                'pants_light': (95, 65, 38),

                'metal_darkest': (22, 22, 22),
                'metal_dark': (50, 45, 45),
                'metal_mid': (98, 88, 88),
                'metal_light': (160, 148, 148),
                'metal_high': (215, 205, 205),
                'metal_shine': (248, 240, 240),

                'wood_darkest': (25, 15, 8),
                'wood_dark': (52, 32, 15),
                'wood_mid': (85, 55, 28),
                'wood_light': (125, 88, 48),
                'wood_high': (170, 128, 78),

                'stone_darkest': (48, 38, 25),
                'stone_dark': (85, 68, 48),
                'stone_mid': (130, 110, 80),
                'stone_light': (178, 158, 120),
                'stone_high': (218, 200, 170),

                'gold_darkest': (65, 42, 10),
                'gold_dark': (110, 78, 20),
                'gold_mid': (165, 120, 40),
                'gold_light': (210, 170, 75),
                'gold_high': (240, 208, 130),

                # Darker red mohawk
                'hair_darkest': (65, 12, 12),
                'hair_dark': (120, 25, 22),
                'hair_mid': (175, 48, 38),
                'hair_light': (215, 82, 60),
                'hair_high': (245, 128, 95),

                'tusk_dark': (140, 125, 92),
                'tusk_mid': (200, 190, 158),
                'tusk_light': (238, 232, 210),
                'tusk_shine': (255, 250, 235),

                'heal_darkest': (15, 45, 12),
                'heal_dark': (35, 95, 28),
                'heal_mid': (65, 160, 52),
                'heal_light': (115, 210, 92),
                'heal_bright': (170, 240, 140),
                'heal_hot': (215, 250, 195),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 3, 5),
                'eye_black': (12, 5, 5),
                'eye_yellow': (255, 210, 50),
                'eye_bright': (255, 240, 195),
                'mouth_dark': (32, 8, 12),
            }


    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_troll(surface, minion, x, y):
        """Draw troll - CACHED"""
        from minions.base_renderer import cached_minion_draw
        cached_minion_draw(surface, minion, x, y, _NS_troll._draw_troll_full)


    def _draw_troll_full(surface, minion, x, y):
        """Original troll render (dipanggil oleh cache)"""
        palette = _NS_troll._get_palette(minion.team)

        walk_phase = minion.walk_cycle
        is_running = minion.is_moving
        anim_time = minion.anim_time

        # Regeneration active? (out of combat)
        is_regenerating = getattr(minion, 'is_regenerating', False)

        # Attack anim
        attack_progress = 0
        is_attacking = False
        if minion.attack_anim_timer > 0:
            attack_progress = 1.0 - (minion.attack_anim_timer /
                                      minion.attack_anim_max)
            is_attacking = True

        # Body bob (heavy stomping troll)
        if is_running:
            body_bob = int(math.sin(walk_phase * 1.5) * 2)
        else:
            # Slight breathing
            body_bob = int(math.sin(anim_time * 0.05) * 1)

        # Attack body lunge
        attack_offset_x = 0
        if is_attacking:
            if attack_progress < 0.25:
                p = attack_progress / 0.25
                attack_offset_x = int(-p * 3) * minion.direction
            elif attack_progress < 0.55:
                p = (attack_progress - 0.25) / 0.30
                ease = p * p * (3 - 2 * p)
                attack_offset_x = int((-3 + ease * 11)) * minion.direction
            else:
                p = (attack_progress - 0.55) / 0.45
                ease = 1 - (1 - p) * (1 - p)
                attack_offset_x = int((8 - ease * 8)) * minion.direction

        # Spawn scale
        spawn_scale = 1.0
        if minion.spawn_anim > 0:
            spawn_scale = 1.0 - (minion.spawn_anim / 20.0) * 0.5
            spawn_scale = max(0.3, spawn_scale)

        draw_x = x + attack_offset_x
        draw_y = y + body_bob

        # Ground shadow (big troll)
        _NS_troll._draw_ground_shadow(surface, x, y + minion.radius + 7, minion.radius)

        # Regen aura on ground (behind body)
        if is_regenerating:
            _NS_troll._draw_regen_ground_aura(surface, x, y + minion.radius + 4,
                                    minion.radius, anim_time, palette)

        # Slow FX
        if minion.slow_timer > 0:
            draw_slow_effect(surface, x, y, minion.radius, anim_time)

        # Main body per level
        level = minion.nexus_level
        if level == 1:
            _NS_troll._draw_troll_lvl1(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        elif level == 2:
            _NS_troll._draw_troll_lvl2(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        elif level == 3:
            _NS_troll._draw_troll_lvl3(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        elif level == 4:
            _NS_troll._draw_troll_lvl4(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        else:
            _NS_troll._draw_troll_lvl5(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)

        # Champion aura for lvl 5
        if level >= 5:
            _NS_troll._draw_champion_aura(surface, x, y, anim_time, palette)

        # Regen particles ON BODY (floating up)
        if is_regenerating:
            _NS_troll._draw_regen_particles(surface, x, y, minion.radius,
                                  anim_time, palette)
            # Green cross icon above head
            _NS_troll._draw_regen_cross_icon(surface, x, y - minion.radius - 26,
                                   anim_time, palette)

        # Attack swing arc (green swipe - match reference)
        if is_attacking and 0.30 <= attack_progress <= 0.72:
            _NS_troll._draw_swing_arc(surface, draw_x, draw_y, minion.direction,
                            attack_progress, palette)

        # Impact sparkle at peak
        if is_attacking and 0.50 <= attack_progress <= 0.65:
            _NS_troll._draw_impact_sparkle(surface, draw_x, draw_y, minion.direction,
                                 attack_progress, palette)

        # Slash effects
        if minion.slash_effects:
            draw_slash_effects(surface, draw_x, draw_y, minion.slash_effects)


        # HP bar
        bar_w = minion.radius * 2 + 8
        by = y - minion.radius - 18
        draw_hp_bar(surface, x, by, bar_w,
                    minion.hp / minion.max_hp, minion.team)

        # Level stars
        if minion.nexus_level >= 3:
            for i in range(minion.nexus_level - 2):
                star_x = x - 5 + i * 5
                star_y = by - 5
                _NS_troll._aacircle(surface, palette['gold_light'], (star_x, star_y), 2)
                pygame.draw.rect(surface, palette['shine'],
                                 (star_x, star_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # GROUND SHADOW
    # ═══════════════════════════════════════════════════════

    def _draw_ground_shadow(surface, x, y, radius):
        """Big shadow for heavy troll."""
        shadow_surf = pygame.Surface((radius * 6, 14), pygame.SRCALPHA)
        for r in range(7, 0, -1):
            alpha = (7 - r) * 22
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                                (7 - r, 7 - r,
                                 radius * 6 - (7 - r) * 2, r * 2))
        pygame.draw.ellipse(shadow_surf, (10, 8, 5, 180),
                            (3, 3, radius * 6 - 6, 6))
        surface.blit(shadow_surf, (x - radius * 3, y - 7))


    # ═══════════════════════════════════════════════════════
    # LEVEL 1: WHELP (basic bare)
    # ═══════════════════════════════════════════════════════

    def _draw_troll_lvl1(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_troll._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_troll._draw_torso_bare(surface, bx, y - 2, face, palette, hurt)
        _NS_troll._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=False)
        _NS_troll._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   mohawk_size='small', has_scars=False,
                   has_shoulder_spike=False)
        _NS_troll._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='club_small', has_bracer=False)


    # ═══════════════════════════════════════════════════════
    # LEVEL 2: RAIDER (+bigger mohawk +harness)
    # ═══════════════════════════════════════════════════════

    def _draw_troll_lvl2(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_troll._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_troll._draw_torso_harness(surface, bx, y - 2, face, palette, hurt)
        _NS_troll._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_troll._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   mohawk_size='medium', has_scars=False,
                   has_shoulder_spike=False)
        _NS_troll._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='club_small', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 3: BRUISER (+shoulder spike +scars +bigger mace)
    # ═══════════════════════════════════════════════════════

    def _draw_troll_lvl3(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_troll._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_troll._draw_torso_harness(surface, bx, y - 2, face, palette, hurt)
        _NS_troll._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        # LEFT spiked shoulder
        _NS_troll._draw_spiked_pauldron(surface, bx - r + 1, y - 4, palette)
        _NS_troll._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   mohawk_size='big', has_scars=True,
                   has_shoulder_spike=False)
        _NS_troll._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='mace_spiked', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 4: SAVAGE (+both pads +bone necklace)
    # ═══════════════════════════════════════════════════════

    def _draw_troll_lvl4(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_troll._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_troll._draw_torso_harness_bones(surface, bx, y - 2, face, palette, hurt)
        _NS_troll._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_troll._draw_spiked_pauldron(surface, bx - r + 1, y - 4, palette)
        _NS_troll._draw_spiked_pauldron(surface, bx + r - 1, y - 4, palette, mirror=True)
        _NS_troll._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   mohawk_size='big', has_scars=True,
                   has_shoulder_spike=True)
        _NS_troll._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='mace_spiked', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEVEL 5: CHIEFTAIN (full armor + huge mace + war paint)
    # ═══════════════════════════════════════════════════════

    def _draw_troll_lvl5(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_troll._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette)
        _NS_troll._draw_torso_armored(surface, bx, y - 2, face, palette, hurt)
        _NS_troll._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_bracer=True)
        _NS_troll._draw_spiked_pauldron(surface, bx - r + 1, y - 4, palette)
        _NS_troll._draw_spiked_pauldron(surface, bx + r - 1, y - 4, palette, mirror=True)
        _NS_troll._draw_head(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                   mohawk_size='huge', has_scars=True,
                   has_shoulder_spike=True, has_warpaint=True)
        _NS_troll._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='mace_huge', has_bracer=True)


    # ═══════════════════════════════════════════════════════
    # LEGS (thick troll legs, hunched stance)
    # ═══════════════════════════════════════════════════════

    def _draw_legs(surface, cx, cy, phase, is_running, palette):
        """Two thick troll legs - hunched, powerful."""
        if is_running:
            swing_l = math.sin(phase * 2) * 3.5
            swing_r = -swing_l
        else:
            idle = math.sin(phase * 0.8) * 0.4
            swing_l = idle
            swing_r = -idle

        for side, swing in [(-1, swing_l), (1, swing_r)]:
            hip_x = cx + side * 4
            hip_y = cy - 2

            knee_x = hip_x + int(swing * 0.4) + side * 1  # bowed out
            knee_y = cy + 3

            foot_x = hip_x + int(swing)
            foot_y = cy + 9

            # Shadow
            _NS_troll._aaline(surface, palette['shadow_deep'],
                    (hip_x + 1, hip_y + 1), (foot_x + 1, foot_y + 1), 7)

            # Thick blue skin thigh
            _NS_troll._aaline(surface, palette['skin_darkest'],
                    (hip_x, hip_y), (knee_x, knee_y), 7)
            _NS_troll._aaline(surface, palette['skin_dark'],
                    (hip_x, hip_y), (knee_x, knee_y), 6)
            _NS_troll._aaline(surface, palette['skin_mid'],
                    (hip_x - side, hip_y), (knee_x - side, knee_y), 3)
            _NS_troll._aaline(surface, palette['skin_light'],
                    (hip_x - side, hip_y), (knee_x - side, knee_y), 1)

            # Leather wrap on lower leg
            _NS_troll._aaline(surface, palette['pants_darkest'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 6)
            _NS_troll._aaline(surface, palette['pants_dark'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 5)
            _NS_troll._aaline(surface, palette['pants_mid'],
                    (knee_x, knee_y), (foot_x, foot_y - 2), 3)

            # Leather straps around shin
            for wy_off in [1, 4]:
                wy = knee_y + wy_off
                wx = hip_x + int(swing * (0.4 + wy_off * 0.15))
                _NS_troll._aaline(surface, palette['leather_darkest'],
                        (wx - 3, wy), (wx + 3, wy), 2)
                _NS_troll._aaline(surface, palette['leather_dark'],
                        (wx - 3, wy), (wx + 3, wy), 1)
                _NS_troll._aaline(surface, palette['leather_light'],
                        (wx - 2, wy), (wx + 1, wy), 1)

            # Knee guard (leather cap)
            _NS_troll._aacircle(surface, palette['leather_darkest'], (knee_x, knee_y), 3)
            _NS_troll._aacircle(surface, palette['leather_dark'], (knee_x, knee_y), 2)
            _NS_troll._aacircle(surface, palette['leather_mid'], (knee_x - 1, knee_y - 1), 1)

            # BARE FOOT with troll claws
            _NS_troll._draw_troll_foot(surface, foot_x, foot_y, side, palette)


    def _draw_troll_foot(surface, fx, fy, side, palette):
        """Bare troll foot with claws."""
        # Foot main (blue skin)
        foot_pts = [
            (fx - 4, fy - 3),
            (fx + 4, fy - 3),
            (fx + 5, fy - 1),
            (fx + 4, fy + 1),
            (fx - 4, fy + 1),
            (fx - 5, fy - 1),
        ]
        _NS_troll._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in foot_pts])
        _NS_troll._aapolygon(surface, palette['skin_darkest'], foot_pts)
        _NS_troll._aapolygon(surface, palette['skin_dark'], [
            (fx - 3, fy - 2), (fx + 3, fy - 2),
            (fx + 4, fy - 1), (fx + 3, fy),
            (fx - 3, fy), (fx - 4, fy - 1),
        ])
        _NS_troll._aapolygon(surface, palette['skin_mid'], [
            (fx - 3, fy - 2), (fx + 2, fy - 2),
            (fx + 3, fy - 1), (fx + 2, fy),
            (fx - 3, fy),
        ])
        # Highlight
        _NS_troll._aaline(surface, palette['skin_light'],
                (fx - 2, fy - 2), (fx + 1, fy - 2), 1)

        # Toe claws (3 pointing forward)
        for toe_i in range(3):
            tx = fx + 3 + toe_i
            # White claw
            _NS_troll._aapolygon(surface, palette['tusk_dark'], [
                (tx, fy - 1),
                (tx + 2, fy),
                (tx, fy + 1),
            ])
            _NS_troll._aapolygon(surface, palette['tusk_mid'], [
                (tx, fy - 1),
                (tx + 1, fy),
                (tx, fy + 1),
            ])
            pygame.draw.rect(surface, palette['tusk_light'], (tx, fy, 1, 1))


    # ═══════════════════════════════════════════════════════
    # TORSO VARIANTS
    # ═══════════════════════════════════════════════════════

    def _draw_torso_bare(surface, cx, cy, face, palette, hurt):
        """Level 1 - bare hunched troll torso."""
        body_w = 22
        body_h = 17

        if hurt:
            skin_mid = (255, 255, 255)
            skin_light = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']
            skin_light = palette['skin_light']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=5)

        # Broad muscular chest
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=5)
        pygame.draw.rect(surface, palette['skin_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=5)
        pygame.draw.rect(surface, skin_mid,
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=5)
        pygame.draw.rect(surface, skin_light,
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=3)
        pygame.draw.rect(surface, palette['skin_high'],
                         (cx - body_w // 2 + 1, cy + 1, 4, 3),
                         border_radius=2)

        # Big pec definition
        _NS_troll._aaline(surface, palette['muscle_dark'],
                (cx, cy + 2), (cx, cy + 9), 2)
        # Left pec
        _NS_troll._aacircle(surface, palette['skin_dark'], (cx - 5, cy + 5), 3)
        _NS_troll._aacircle(surface, palette['skin_mid'], (cx - 5, cy + 4), 2)
        _NS_troll._aacircle(surface, palette['skin_light'], (cx - 6, cy + 3), 1)
        # Right pec
        _NS_troll._aacircle(surface, palette['skin_dark'], (cx + 5, cy + 5), 3)
        _NS_troll._aacircle(surface, palette['skin_mid'], (cx + 5, cy + 4), 2)

        # Ab shading
        for ab_y in [cy + 9, cy + 12]:
            _NS_troll._aaline(surface, palette['muscle_dark'],
                    (cx - 4, ab_y), (cx + 4, ab_y), 1)
        _NS_troll._aaline(surface, palette['muscle_dark'],
                (cx, cy + 9), (cx, cy + 14), 1)

        # Simple leather waistband
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, cy + body_h - 3, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, cy + body_h - 3, body_w - 1, 2))
        # Buckle
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 2, cy + body_h - 3, 4, 3))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 2, cy + body_h - 3, 3, 2))


    def _draw_torso_harness(surface, cx, cy, face, palette, hurt):
        """Level 2-3 - leather harness with straps."""
        body_w = 23
        body_h = 18

        if hurt:
            skin_mid = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=5)

        # Skin base
        pygame.draw.rect(surface, palette['skin_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=5)
        pygame.draw.rect(surface, palette['skin_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=5)
        pygame.draw.rect(surface, skin_mid,
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=5)

        # Pec definition
        _NS_troll._aacircle(surface, palette['skin_dark'], (cx - 5, cy + 5), 3)
        _NS_troll._aacircle(surface, palette['skin_light'], (cx - 6, cy + 3), 1)
        _NS_troll._aacircle(surface, palette['skin_dark'], (cx + 5, cy + 5), 3)

        # Cross-strap leather harness
        _NS_troll._aaline(surface, palette['leather_darkest'],
                (cx - body_w // 2 + 2, cy + 2),
                (cx + body_w // 2 - 3, cy + body_h - 5), 4)
        _NS_troll._aaline(surface, palette['leather_dark'],
                (cx - body_w // 2 + 2, cy + 2),
                (cx + body_w // 2 - 3, cy + body_h - 5), 3)
        _NS_troll._aaline(surface, palette['leather_mid'],
                (cx - body_w // 2 + 2, cy + 2),
                (cx + body_w // 2 - 3, cy + body_h - 5), 1)

        _NS_troll._aaline(surface, palette['leather_darkest'],
                (cx + body_w // 2 - 3, cy + 2),
                (cx - body_w // 2 + 2, cy + body_h - 5), 4)
        _NS_troll._aaline(surface, palette['leather_dark'],
                (cx + body_w // 2 - 3, cy + 2),
                (cx - body_w // 2 + 2, cy + body_h - 5), 3)
        _NS_troll._aaline(surface, palette['leather_mid'],
                (cx + body_w // 2 - 3, cy + 2),
                (cx - body_w // 2 + 2, cy + body_h - 5), 1)

        # Central iron plate/medallion
        _NS_troll._aacircle(surface, palette['shadow'], (cx, cy + 7), 4)
        _NS_troll._aacircle(surface, palette['metal_darkest'], (cx, cy + 7), 4)
        _NS_troll._aacircle(surface, palette['metal_dark'], (cx, cy + 7), 3)
        _NS_troll._aacircle(surface, palette['metal_mid'], (cx - 1, cy + 6), 2)
        _NS_troll._aacircle(surface, palette['metal_high'], (cx - 1, cy + 6), 1)
        # Tribal rune
        pygame.draw.rect(surface, palette['metal_darkest'], (cx - 1, cy + 6, 2, 3))
        pygame.draw.rect(surface, palette['heal_bright'], (cx, cy + 7, 1, 1))

        # Big belt
        belt_y = cy + body_h - 5
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - body_w // 2, belt_y + 1, body_w, 5))
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 5))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 4))
        pygame.draw.rect(surface, palette['leather_mid'],
                         (cx - body_w // 2, belt_y, body_w - 2, 2))
        _NS_troll._aaline(surface, palette['leather_light'],
                (cx - body_w // 2 + 1, belt_y),
                (cx + body_w // 2 - 3, belt_y), 1)

        # Big gold buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 4, belt_y - 1 + 1, 8, 6))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 4, belt_y - 1, 8, 6))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 4, belt_y - 1, 7, 5))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 4, belt_y - 1, 5, 4))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 4, belt_y - 1, 3, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 4, belt_y - 1, 1, 1))


    def _draw_torso_harness_bones(surface, cx, cy, face, palette, hurt):
        """Level 4 - harness + bone necklace."""
        _NS_troll._draw_torso_harness(surface, cx, cy, face, palette, hurt)

        # Bone necklace across neck/chest
        for i in range(5):
            bone_x = cx - 5 + i * 2 + int(math.sin(i * 0.7) * 1)
            bone_y = cy - 1 + int(math.cos(i * 0.5) * 1)
            # Small bone/tooth pendant
            _NS_troll._aapolygon(surface, palette['shadow_deep'], [
                (bone_x - 1, bone_y),
                (bone_x + 1, bone_y),
                (bone_x, bone_y + 3),
            ])
            _NS_troll._aapolygon(surface, palette['tusk_dark'], [
                (bone_x - 1, bone_y - 1),
                (bone_x + 1, bone_y - 1),
                (bone_x, bone_y + 2),
            ])
            _NS_troll._aapolygon(surface, palette['tusk_mid'], [
                (bone_x - 1, bone_y - 1),
                (bone_x, bone_y - 1),
                (bone_x, bone_y + 1),
            ])
            pygame.draw.rect(surface, palette['tusk_light'], (bone_x, bone_y, 1, 1))

        # String across
        _NS_troll._aaline(surface, palette['leather_dark'],
                (cx - 6, cy - 1), (cx + 6, cy - 1), 1)


    def _draw_torso_armored(surface, cx, cy, face, palette, hurt):
        """Level 5 - iron plate armor with tribal engraving."""
        body_w = 24
        body_h = 19

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=5)

        # Iron chestplate
        pygame.draw.rect(surface, palette['metal_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=5)
        pygame.draw.rect(surface, palette['metal_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=5)
        pygame.draw.rect(surface, palette['metal_mid'],
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=5)
        pygame.draw.rect(surface, palette['metal_light'],
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=3)
        pygame.draw.rect(surface, palette['metal_high'],
                         (cx - body_w // 2, cy, 6, 3), border_radius=1)

        # Gold trim top
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - body_w // 2, cy, body_w, 2))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - body_w // 2, cy, body_w - 1, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - body_w // 2 + 1, cy, 3, 1))

        # Tribal green heal emblem (cross - matches passive icon)
        _NS_troll._aapolygon(surface, palette['gold_dark'], [
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 4, cy + 11),
            (cx - 4, cy + 11),
        ])
        _NS_troll._aapolygon(surface, palette['gold_darkest'], [
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 4, cy + 5),
            (cx - 4, cy + 5),
        ])
        # Green cross
        pygame.draw.rect(surface, palette['heal_darkest'], (cx - 3, cy + 6, 6, 5))
        pygame.draw.rect(surface, palette['heal_dark'], (cx - 2, cy + 7, 4, 3))
        # Cross bars
        pygame.draw.rect(surface, palette['heal_bright'], (cx - 1, cy + 5, 2, 5))
        pygame.draw.rect(surface, palette['heal_bright'], (cx - 3, cy + 7, 6, 2))
        pygame.draw.rect(surface, palette['heal_hot'], (cx, cy + 6, 1, 3))
        pygame.draw.rect(surface, palette['heal_hot'], (cx - 2, cy + 8, 4, 1))

        # Rivets
        for rx in [-body_w // 2 + 2, body_w // 2 - 3]:
            for ry in [2, body_h - 5]:
                _NS_troll._aacircle(surface, palette['metal_darkest'],
                          (cx + rx, cy + ry), 1)
                pygame.draw.rect(surface, palette['metal_high'],
                                 (cx + rx, cy + ry - 1, 1, 1))

        # Belt
        belt_y = cy + body_h - 4
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 2))
        # Big buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 5, belt_y - 1 + 1, 10, 5))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 5, belt_y - 1, 10, 5))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 5, belt_y - 1, 9, 4))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 5, belt_y - 1, 6, 3))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 5, belt_y - 1, 3, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 5, belt_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # HEAD (blue troll - big lower tusks, red mohawk)
    # ═══════════════════════════════════════════════════════

    def _draw_head(surface, cx, cy, face, palette, hurt,
                   mohawk_size='medium', has_scars=False,
                   has_shoulder_spike=False, has_warpaint=False):
        """Troll head with red mohawk + upward-pointing tusks."""
        if hurt:
            skin_mid = (255, 255, 255)
            skin_light = (255, 255, 255)
        else:
            skin_mid = palette['skin_mid']
            skin_light = palette['skin_light']

        head_r = 9

        # ═══ POINTY EARS (like elf ears, sticking out horizontal) ═══
        # Back ear
        ear_b_pts = [
            (cx - head_r + 1, cy - 1),
            (cx - head_r - 5, cy - 5),
            (cx - head_r + 2, cy - 2),
        ]
        _NS_troll._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in ear_b_pts])
        _NS_troll._aapolygon(surface, palette['skin_darkest'], ear_b_pts)
        _NS_troll._aapolygon(surface, palette['skin_dark'], [
            (cx - head_r + 1, cy - 1),
            (cx - head_r - 4, cy - 4),
            (cx - head_r + 2, cy - 2),
        ])
        _NS_troll._aapolygon(surface, skin_mid, [
            (cx - head_r + 2, cy - 2),
            (cx - head_r - 2, cy - 3),
            (cx - head_r + 2, cy - 2),
        ])

        # Front ear (BIG - troll's signature)
        ear_f_pts = [
            (cx + head_r - 1, cy - 1),
            (cx + head_r + 6, cy - 5),
            (cx + head_r + 2, cy - 2),
            (cx + head_r - 1, cy + 1),
        ]
        _NS_troll._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in ear_f_pts])
        _NS_troll._aapolygon(surface, palette['skin_darkest'], ear_f_pts)
        _NS_troll._aapolygon(surface, palette['skin_dark'], [
            (cx + head_r - 1, cy - 1),
            (cx + head_r + 5, cy - 4),
            (cx + head_r + 2, cy - 2),
            (cx + head_r - 1, cy + 1),
        ])
        _NS_troll._aapolygon(surface, skin_mid, [
            (cx + head_r - 1, cy - 1),
            (cx + head_r + 3, cy - 3),
            (cx + head_r + 1, cy - 1),
        ])
        _NS_troll._aaline(surface, skin_light,
                (cx + head_r, cy - 2), (cx + head_r + 3, cy - 4), 1)

        # Ear piercing (gold ring on front ear)
        if has_shoulder_spike:  # lvl 4+ has piercing
            _NS_troll._aacircle(surface, palette['gold_dark'],
                      (cx + head_r + 3, cy - 2), 1)
            pygame.draw.rect(surface, palette['gold_high'],
                             (cx + head_r + 3, cy - 3, 1, 1))

        # ═══ HEAD SHAPE (big troll skull, slightly elongated) ═══
        _NS_troll._aacircle(surface, palette['shadow_deep'], (cx + 1, cy + 1), head_r)
        _NS_troll._aacircle(surface, palette['skin_darkest'], (cx, cy), head_r)
        _NS_troll._aacircle(surface, palette['skin_dark'], (cx, cy), head_r - 1)
        _NS_troll._aacircle(surface, skin_mid, (cx - 1, cy - 1), head_r - 2)
        _NS_troll._aacircle(surface, skin_light, (cx - 2, cy - 2), head_r - 4)
        _NS_troll._aacircle(surface, palette['skin_high'], (cx - 3, cy - 3),
                  max(1, head_r - 6))

        # ═══ HEAVY BROW RIDGE (angry troll) ═══
        _NS_troll._aapolygon(surface, palette['skin_darkest'], [
            (cx - head_r + 1, cy - 4),
            (cx + head_r - 1, cy - 4),
            (cx + head_r - 2, cy - 1),
            (cx - head_r + 2, cy - 1),
        ])
        _NS_troll._aapolygon(surface, palette['skin_dark'], [
            (cx - head_r + 2, cy - 4),
            (cx + head_r - 2, cy - 4),
            (cx + head_r - 3, cy - 2),
            (cx - head_r + 3, cy - 2),
        ])
        _NS_troll._aaline(surface, palette['muscle_dark'],
                (cx - head_r + 2, cy - 1), (cx + head_r - 2, cy - 1), 1)
        # Angry frown
        _NS_troll._aaline(surface, palette['muscle_dark'],
                (cx - 3, cy - 3), (cx, cy - 1), 1)
        _NS_troll._aaline(surface, palette['muscle_dark'],
                (cx + 3, cy - 3), (cx, cy - 1), 1)

        # ═══ EYES (small angry, deep-set yellow) ═══
        for eye_side, eye_x in [(-1, cx - 3), (1, cx + 3)]:
            _NS_troll._aacircle(surface, palette['shadow'], (eye_x, cy), 2)
            _NS_troll._aacircle(surface, palette['eye_black'], (eye_x, cy), 1)
            pygame.draw.rect(surface, palette['eye_yellow'],
                             (eye_x, cy, 1, 1))
            if eye_side == -1:
                pygame.draw.rect(surface, palette['eye_bright'],
                                 (eye_x, cy - 1, 1, 1))

        # ═══ FLAT NOSE ═══
        nose_pts = [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ]
        _NS_troll._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in nose_pts])
        _NS_troll._aapolygon(surface, palette['skin_darkest'], nose_pts)
        _NS_troll._aapolygon(surface, palette['skin_dark'], [
            (cx - 2, cy + 1),
            (cx + 2, cy + 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Nostrils
        pygame.draw.rect(surface, palette['shadow'], (cx - 2, cy + 3, 1, 1))
        pygame.draw.rect(surface, palette['shadow'], (cx + 1, cy + 3, 1, 1))

        # Nose ring (bull ring - lvl 3+)
        if has_scars:
            _NS_troll._aacircle(surface, palette['gold_dark'], (cx, cy + 4), 2, 1)
            pygame.draw.rect(surface, palette['gold_high'], (cx - 1, cy + 3, 1, 1))

        # ═══ MOUTH with UPWARD TUSKS (troll signature) ═══
        mouth_y = cy + 5
        # Mouth line
        pygame.draw.rect(surface, palette['mouth_dark'],
                         (cx - 4, mouth_y, 8, 2))
        _NS_troll._aaline(surface, palette['shadow'],
                (cx - 4, mouth_y), (cx + 4, mouth_y), 1)

        # LOWER TUSKS pointing UP (troll signature - unlike orc which points up too but troll has bigger)
        # Left tusk
        _NS_troll._aapolygon(surface, palette['shadow_deep'], [
            (cx - 4, mouth_y + 1),
            (cx - 5, mouth_y - 3),
            (cx - 3, mouth_y - 4),
            (cx - 2, mouth_y + 1),
        ])
        _NS_troll._aapolygon(surface, palette['tusk_dark'], [
            (cx - 4, mouth_y),
            (cx - 5, mouth_y - 3),
            (cx - 3, mouth_y - 3),
            (cx - 2, mouth_y),
        ])
        _NS_troll._aapolygon(surface, palette['tusk_mid'], [
            (cx - 4, mouth_y),
            (cx - 4, mouth_y - 2),
            (cx - 3, mouth_y - 3),
            (cx - 2, mouth_y),
        ])
        _NS_troll._aapolygon(surface, palette['tusk_light'], [
            (cx - 4, mouth_y),
            (cx - 4, mouth_y - 2),
            (cx - 3, mouth_y - 2),
        ])
        pygame.draw.rect(surface, palette['tusk_shine'],
                         (cx - 4, mouth_y - 1, 1, 1))

        # Right tusk (larger, more prominent)
        _NS_troll._aapolygon(surface, palette['shadow_deep'], [
            (cx + 2, mouth_y + 1),
            (cx + 3, mouth_y - 5),
            (cx + 5, mouth_y - 4),
            (cx + 4, mouth_y + 1),
        ])
        _NS_troll._aapolygon(surface, palette['tusk_dark'], [
            (cx + 2, mouth_y),
            (cx + 3, mouth_y - 4),
            (cx + 5, mouth_y - 4),
            (cx + 4, mouth_y),
        ])
        _NS_troll._aapolygon(surface, palette['tusk_mid'], [
            (cx + 2, mouth_y),
            (cx + 3, mouth_y - 4),
            (cx + 4, mouth_y - 3),
            (cx + 4, mouth_y),
        ])
        _NS_troll._aapolygon(surface, palette['tusk_light'], [
            (cx + 2, mouth_y),
            (cx + 3, mouth_y - 3),
            (cx + 4, mouth_y - 2),
        ])
        pygame.draw.rect(surface, palette['tusk_shine'],
                         (cx + 3, mouth_y - 2, 1, 1))

        # ═══ SCARS (lvl 3+) ═══
        if has_scars:
            # Diagonal scar across cheek
            _NS_troll._aaline(surface, palette['muscle_dark'],
                    (cx - 5, cy + 2), (cx - 3, cy + 5), 1)
            _NS_troll._aaline(surface, palette['skin_darkest'],
                    (cx - 5, cy + 2), (cx - 3, cy + 5), 1)
            # Small stitches
            for i in range(2):
                sx = cx - 5 + i
                sy = cy + 2 + i * 2
                pygame.draw.rect(surface, palette['skin_high'], (sx, sy, 1, 1))

        # ═══ WAR PAINT (lvl 5) ═══
        if has_warpaint:
            # Green tribal marks below eyes (heal-themed)
            for stripe_x_off in [-4, 4]:
                sx = cx + stripe_x_off
                _NS_troll._aaline(surface, palette['heal_dark'],
                        (sx, cy + 1), (sx, cy + 4), 1)
                pygame.draw.rect(surface, palette['heal_bright'], (sx, cy + 2, 1, 1))
            # Horizontal band
            pygame.draw.rect(surface, palette['heal_dark'],
                             (cx - 4, cy + 1, 9, 1))

        # ═══ SHOULDER SPIKE on left (lvl 4+) - single dagger-like spike ═══
        # (handled in level function via _NS_troll._draw_spiked_pauldron)

        # ═══ RED MOHAWK ═══
        _NS_troll._draw_mohawk(surface, cx, cy - head_r + 1, mohawk_size, palette)


    def _draw_mohawk(surface, cx, cy, size, palette):
        """Red spiky mohawk - troll signature."""
        if size == 'small':
            strands = [
                (-2, -4, -0.3),
                (0, -5, 0),
                (2, -4, 0.3),
            ]
        elif size == 'medium':
            strands = [
                (-3, -5, -0.4),
                (-1, -7, -0.15),
                (1, -7, 0.15),
                (3, -5, 0.4),
            ]
        elif size == 'big':
            strands = [
                (-3, -6, -0.4),
                (-1, -9, -0.15),
                (1, -10, 0.05),
                (3, -8, 0.3),
                (5, -5, 0.6),
            ]
        else:  # huge
            strands = [
                (-4, -6, -0.5),
                (-2, -9, -0.25),
                (0, -11, 0),
                (2, -10, 0.2),
                (4, -8, 0.4),
                (5, -5, 0.7),
            ]

        # Base (leather band)
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - 4, cy + 1, 8, 2))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - 4, cy + 1, 7, 1))

        for hx_off, height, lean in strands:
            base_x = cx + hx_off
            tip_x = base_x + int(lean * abs(height))
            tip_y = cy + height

            # Shadow
            _NS_troll._aapolygon(surface, palette['shadow_deep'], [
                (base_x - 2, cy + 2),
                (tip_x + 1, tip_y + 1),
                (base_x + 2, cy + 2),
            ])
            # Hair layers (bright red)
            _NS_troll._aapolygon(surface, palette['hair_darkest'], [
                (base_x - 2, cy + 1),
                (tip_x, tip_y),
                (base_x + 2, cy + 1),
            ])
            _NS_troll._aapolygon(surface, palette['hair_dark'], [
                (base_x - 1, cy + 1),
                (tip_x, tip_y + 1),
                (base_x + 1, cy + 1),
            ])
            _NS_troll._aapolygon(surface, palette['hair_mid'], [
                (base_x - 1, cy + 1),
                (tip_x, tip_y + 2),
                (base_x, cy + 1),
            ])
            _NS_troll._aaline(surface, palette['hair_light'],
                    (base_x, cy),
                    (tip_x, tip_y + 2), 1)
            # Bright tip highlight
            pygame.draw.rect(surface, palette['hair_high'], (tip_x, tip_y, 1, 1))


    # ═══════════════════════════════════════════════════════
    # SPIKED PAULDRON (single big spike + rim)
    # ═══════════════════════════════════════════════════════

    def _draw_spiked_pauldron(surface, x, y, palette, mirror=False):
        """Big shoulder pad with 1 huge iron spike (troll style)."""
        direction = -1 if mirror else 1

        # Round leather pad base
        pad_pts = [
            (x - 5 * direction, y + 1),
            (x + 4 * direction, y + 1),
            (x + 5 * direction, y + 4),
            (x + 3 * direction, y + 7),
            (x - 2 * direction, y + 7),
            (x - 5 * direction, y + 5),
        ]

        # Shadow
        _NS_troll._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in pad_pts])

        # Leather layers
        _NS_troll._aapolygon(surface, palette['leather_darkest'], pad_pts)
        _NS_troll._aapolygon(surface, palette['leather_dark'], [
            (x - 4 * direction, y + 2),
            (x + 3 * direction, y + 2),
            (x + 4 * direction, y + 4),
            (x + 2 * direction, y + 6),
            (x - 2 * direction, y + 6),
            (x - 4 * direction, y + 4),
        ])
        _NS_troll._aapolygon(surface, palette['leather_mid'], [
            (x - 4 * direction, y + 2),
            (x + 2 * direction, y + 2),
            (x + 3 * direction, y + 4),
            (x + 1 * direction, y + 5),
            (x - 3 * direction, y + 4),
        ])
        _NS_troll._aapolygon(surface, palette['leather_light'], [
            (x - 4 * direction, y + 2),
            (x, y + 2),
            (x, y + 4),
            (x - 3 * direction, y + 4),
        ])
        pygame.draw.rect(surface, palette['leather_high'],
                         (x - 3 * direction, y + 2, 1, 1))

        # Metal rim
        _NS_troll._aaline(surface, palette['metal_darkest'],
                (x - 5 * direction, y + 5),
                (x + 4 * direction, y + 5), 2)
        _NS_troll._aaline(surface, palette['metal_dark'],
                (x - 5 * direction, y + 5),
                (x + 3 * direction, y + 5), 1)
        _NS_troll._aaline(surface, palette['metal_light'],
                (x - 5 * direction, y + 5),
                (x - 2 * direction, y + 5), 1)

        # Rivets on rim
        for rvx in [-3, 0, 3]:
            rvx_pos = x + rvx * direction
            _NS_troll._aacircle(surface, palette['metal_darkest'], (rvx_pos, y + 5), 1)
            pygame.draw.rect(surface, palette['metal_high'],
                             (rvx_pos, y + 4, 1, 1))

        # ═══ ONE BIG IRON SPIKE (troll style - single dagger-like) ═══
        sx = x + 0 * direction
        sy = y + 1

        # Shadow
        _NS_troll._aapolygon(surface, palette['shadow_deep'], [
            (sx - 2, sy + 1),
            (sx, sy - 7),
            (sx + 2, sy + 1),
        ])
        # Spike layers (bigger than orc spikes)
        _NS_troll._aapolygon(surface, palette['metal_darkest'], [
            (sx - 2, sy),
            (sx, sy - 7),
            (sx + 2, sy),
        ])
        _NS_troll._aapolygon(surface, palette['metal_dark'], [
            (sx - 1, sy),
            (sx, sy - 6),
            (sx + 2, sy),
        ])
        _NS_troll._aapolygon(surface, palette['metal_mid'], [
            (sx - 1, sy),
            (sx, sy - 5),
            (sx + 1, sy),
        ])
        _NS_troll._aapolygon(surface, palette['metal_light'], [
            (sx - 1, sy),
            (sx, sy - 4),
            (sx, sy),
        ])
        pygame.draw.rect(surface, palette['metal_high'], (sx, sy - 4, 1, 2))
        pygame.draw.rect(surface, palette['metal_shine'], (sx, sy - 4, 1, 1))

        # 2 smaller side spikes
        for spk_off in [-3, 3]:
            ssx = x + spk_off * direction
            ssy = y + 1
            _NS_troll._aapolygon(surface, palette['shadow_deep'], [
                (ssx - 1, ssy + 1),
                (ssx, ssy - 4),
                (ssx + 1, ssy + 1),
            ])
            _NS_troll._aapolygon(surface, palette['metal_darkest'], [
                (ssx - 1, ssy),
                (ssx, ssy - 4),
                (ssx + 1, ssy),
            ])
            _NS_troll._aapolygon(surface, palette['metal_dark'], [
                (ssx - 1, ssy),
                (ssx, ssy - 3),
                (ssx + 1, ssy),
            ])
            pygame.draw.rect(surface, palette['metal_light'], (ssx, ssy - 3, 1, 2))
            pygame.draw.rect(surface, palette['metal_high'], (ssx, ssy - 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # ARMS
    # ═══════════════════════════════════════════════════════

    def _draw_arm_offhand(surface, sx, sy, face, walk_phase, is_running,
                          palette, has_bracer=False):
        """Empty off-hand (fist)."""
        if is_running:
            arm_swing = math.sin(walk_phase) * 0.4
        else:
            arm_swing = math.sin(walk_phase * 0.5) * 0.1

        arm_angle = arm_swing * (-face)

        upper_len = 6
        elbow_x = sx + int(math.cos(arm_angle + math.pi / 2) * upper_len) * (-face)
        elbow_y = sy + int(math.sin(arm_angle + math.pi / 2) * upper_len) + 2

        _NS_troll._draw_muscular_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = arm_angle * 1.4
        hand_x = elbow_x + int(math.cos(forearm_angle) * 5) * (-face)
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_troll._draw_muscular_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        if has_bracer:
            _NS_troll._draw_bracer(surface, elbow_x, elbow_y, palette)

        _NS_troll._draw_fist(surface, hand_x, hand_y, palette)


    def _draw_arm_weapon(surface, sx, sy, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='club_small', has_bracer=False):
        """Weapon-hand with heavy overhead swing."""
        if is_attacking:
            if attack_progress < 0.25:
                # Wind-up (raise overhead)
                t = attack_progress / 0.25
                t = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.7 * t
                hand_extend = -t * 3
            elif attack_progress < 0.55:
                # Slam down
                t = (attack_progress - 0.25) / 0.30
                t = t ** 2
                swing_angle = -math.pi * 0.7 + t * math.pi * 1.1
                hand_extend = -3 + t * 11
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                t = 1 - (1 - t) ** 2
                swing_angle = math.pi * 0.4 - t * math.pi * 0.4
                hand_extend = 8 - t * 8
        elif is_running:
            swing_angle = math.sin(walk_phase + math.pi) * 0.3
            hand_extend = 0
        else:
            swing_angle = math.sin(walk_phase * 0.5) * 0.1
            hand_extend = 0

        upper_len = 6
        base_angle = math.pi / 2 + swing_angle * face
        elbow_x = sx + int(math.cos(base_angle) * upper_len) * face
        elbow_y = sy + int(math.sin(base_angle) * upper_len) + 2

        _NS_troll._draw_muscular_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = base_angle + swing_angle * 0.7 * face
        hand_x = elbow_x + int(math.cos(forearm_angle) * (5 + hand_extend)) * face
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_troll._draw_muscular_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        if has_bracer:
            _NS_troll._draw_bracer(surface, elbow_x, elbow_y, palette)

        _NS_troll._draw_fist(surface, hand_x, hand_y, palette)

        weapon_angle = forearm_angle - math.pi / 2

        if weapon == 'club_small':
            _NS_troll._draw_mace(surface, hand_x, hand_y, weapon_angle, face,
                       palette, size='small')
        elif weapon == 'mace_spiked':
            _NS_troll._draw_mace(surface, hand_x, hand_y, weapon_angle, face,
                       palette, size='medium')
        elif weapon == 'mace_huge':
            _NS_troll._draw_mace(surface, hand_x, hand_y, weapon_angle, face,
                       palette, size='huge')

        if is_attacking and 0.25 <= attack_progress <= 0.65:
            _NS_troll._draw_swing_blur(surface, sx, sy, face, attack_progress,
                             hand_x, hand_y, palette)


    def _draw_muscular_arm(surface, x1, y1, x2, y2, palette):
        """Thick blue troll arm."""
        _NS_troll._aaline(surface, palette['shadow_deep'],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_troll._aaline(surface, palette['skin_darkest'], (x1, y1), (x2, y2), 6)
        _NS_troll._aaline(surface, palette['skin_dark'], (x1, y1), (x2, y2), 5)
        _NS_troll._aaline(surface, palette['skin_mid'], (x1, y1), (x2, y2), 3)
        _NS_troll._aaline(surface, palette['skin_light'], (x1, y1), (x2, y2), 1)


    def _draw_bracer(surface, x, y, palette):
        """Leather bracer with metal stud."""
        _NS_troll._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 4)
        _NS_troll._aacircle(surface, palette['leather_darkest'], (x, y), 4)
        _NS_troll._aacircle(surface, palette['leather_dark'], (x, y), 3)
        _NS_troll._aacircle(surface, palette['leather_mid'], (x - 1, y - 1), 2)
        _NS_troll._aacircle(surface, palette['leather_light'], (x - 1, y - 1), 1)

        _NS_troll._aacircle(surface, palette['metal_dark'], (x, y), 1)
        pygame.draw.rect(surface, palette['metal_high'], (x, y - 1, 1, 1))

        _NS_troll._aaline(surface, palette['gold_dark'],
                (x - 3, y + 2), (x + 3, y + 2), 1)
        _NS_troll._aaline(surface, palette['gold_mid'],
                (x - 2, y + 2), (x + 2, y + 2), 1)


    def _draw_fist(surface, x, y, palette):
        """Big blue fist with claws."""
        _NS_troll._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 3)
        _NS_troll._aacircle(surface, palette['skin_darkest'], (x, y), 3)
        _NS_troll._aacircle(surface, palette['skin_dark'], (x, y), 2)
        _NS_troll._aacircle(surface, palette['skin_mid'], (x - 1, y - 1), 1)
        pygame.draw.rect(surface, palette['skin_light'], (x - 1, y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # MACE / CLUB (spiked bone/wood weapon)
    # ═══════════════════════════════════════════════════════

    def _draw_mace(surface, x, y, angle, face, palette, size='small'):
        """Spiked club / mace - troll signature weapon."""
        if size == 'small':
            haft_len = 9
            head_r = 4
            spike_count = 5
        elif size == 'medium':
            haft_len = 12
            head_r = 5
            spike_count = 7
        else:  # huge
            haft_len = 15
            head_r = 6
            spike_count = 8

        cos_a = math.cos(angle) * face
        sin_a = math.sin(angle)
        perp_cos = -sin_a
        perp_sin = cos_a

        # ═══ WOODEN HAFT ═══
        haft_start_x = x - int(cos_a * 3)
        haft_start_y = y - int(sin_a * 3)
        haft_end_x = x + int(cos_a * haft_len)
        haft_end_y = y + int(sin_a * haft_len)

        # Shadow
        _NS_troll._aaline(surface, palette['shadow_deep'],
                (haft_start_x + 1, haft_start_y + 1),
                (haft_end_x + 1, haft_end_y + 1), 4)

        # Wood layers
        _NS_troll._aaline(surface, palette['wood_darkest'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 4)
        _NS_troll._aaline(surface, palette['wood_dark'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 3)
        _NS_troll._aaline(surface, palette['wood_mid'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 2)
        _NS_troll._aaline(surface, palette['wood_light'],
                (haft_start_x, haft_start_y),
                (haft_end_x, haft_end_y), 1)

        # Leather grip wrap (multiple bands)
        for grip_t in [0.15, 0.30, 0.45]:
            grip_x = haft_start_x + int(cos_a * haft_len * grip_t)
            grip_y = haft_start_y + int(sin_a * haft_len * grip_t)
            _NS_troll._aacircle(surface, palette['leather_darkest'], (grip_x, grip_y), 3)
            _NS_troll._aacircle(surface, palette['leather_dark'], (grip_x, grip_y), 2)
            _NS_troll._aacircle(surface, palette['leather_mid'], (grip_x - 1, grip_y - 1), 1)

        # Pommel (metal cap)
        _NS_troll._aacircle(surface, palette['metal_darkest'],
                  (haft_start_x, haft_start_y), 2)
        _NS_troll._aacircle(surface, palette['metal_dark'],
                  (haft_start_x, haft_start_y), 1)
        pygame.draw.rect(surface, palette['metal_high'],
                         (haft_start_x, haft_start_y - 1, 1, 1))

        # ═══ MACE HEAD (round with spikes) ═══
        hx = haft_end_x
        hy = haft_end_y

        # Shadow orb
        _NS_troll._aacircle(surface, palette['shadow'], (hx + 1, hy + 1), head_r + 1)

        # Bone/stone orb
        _NS_troll._aacircle(surface, palette['stone_darkest'], (hx, hy), head_r)
        _NS_troll._aacircle(surface, palette['stone_dark'], (hx, hy), head_r - 1)
        _NS_troll._aacircle(surface, palette['stone_mid'], (hx - 1, hy - 1), head_r - 2)
        _NS_troll._aacircle(surface, palette['stone_light'], (hx - 1, hy - 1),
                  max(1, head_r - 3))
        _NS_troll._aacircle(surface, palette['stone_high'], (hx - 1, hy - 1),
                  max(1, head_r - 4))

        # Metal band around orb
        _NS_troll._aacircle(surface, palette['metal_dark'], (hx, hy), head_r, 1)

        # ═══ SPIKES radiating outward ═══
        for spike_i in range(spike_count):
            # Skip the direction pointing back to haft
            spike_angle = spike_i * 2 * math.pi / spike_count

            # Point outward from head center
            sx1 = hx + int(math.cos(spike_angle) * (head_r - 1))
            sy1 = hy + int(math.sin(spike_angle) * (head_r - 1))
            sx_tip = hx + int(math.cos(spike_angle) * (head_r + 3))
            sy_tip = hy + int(math.sin(spike_angle) * (head_r + 3))

            # Perpendicular for spike width
            perp_x = -math.sin(spike_angle)
            perp_y = math.cos(spike_angle)

            # Shadow
            _NS_troll._aapolygon(surface, palette['shadow'], [
                (sx1 + int(perp_x * 1.5) + 1, sy1 + int(perp_y * 1.5) + 1),
                (sx_tip + 1, sy_tip + 1),
                (sx1 - int(perp_x * 1.5) + 1, sy1 - int(perp_y * 1.5) + 1),
            ])
            # Metal spike layers
            _NS_troll._aapolygon(surface, palette['metal_darkest'], [
                (sx1 + int(perp_x * 1.5), sy1 + int(perp_y * 1.5)),
                (sx_tip, sy_tip),
                (sx1 - int(perp_x * 1.5), sy1 - int(perp_y * 1.5)),
            ])
            _NS_troll._aapolygon(surface, palette['metal_dark'], [
                (sx1 + int(perp_x * 1), sy1 + int(perp_y * 1)),
                (sx_tip, sy_tip),
                (sx1 - int(perp_x * 1), sy1 - int(perp_y * 1)),
            ])
            _NS_troll._aaline(surface, palette['metal_light'],
                    (sx1, sy1), (sx_tip, sy_tip), 1)
            # Tip shine
            pygame.draw.rect(surface, palette['metal_high'], (sx_tip, sy_tip, 1, 1))

        # Iron mount where head meets haft
        _NS_troll._aacircle(surface, palette['metal_darkest'], (hx, hy), 2)
        _NS_troll._aacircle(surface, palette['metal_dark'], (hx, hy), 1)


    def _draw_swing_blur(surface, sx, sy, face, progress, hand_x, hand_y,
                         palette):
        """Motion blur during swing (green-tinted for troll heal theme)."""
        for ghost_i in range(4):
            ghost_progress = progress - (ghost_i + 1) * 0.05
            if ghost_progress < 0.25:
                continue

            alpha = max(0, min(255, 95 - ghost_i * 22))
            if alpha <= 0:
                continue

            blur_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            _NS_troll._aacircle(blur_surf, (*palette['skin_dark'], alpha),
                      (12, 12), 6)
            _NS_troll._aacircle(blur_surf, (*palette['skin_mid'], alpha),
                      (12, 12), 4)
            _NS_troll._aacircle(blur_surf, (*palette['skin_light'], alpha // 2),
                      (12, 12), 2)
            surface.blit(blur_surf,
                         (hand_x - 12 - ghost_i * 2 * face, hand_y - 12))


    # ═══════════════════════════════════════════════════════
    # SWING ARC (green crescent - matches reference attack VFX)
    # ═══════════════════════════════════════════════════════

    def _draw_swing_arc(surface, cx, cy, face, progress, palette):
        """Green crescent swipe arc (match reference)."""
        t = (progress - 0.30) / 0.42
        t = max(0.0, min(1.0, t))

        start_angle = math.radians(-95)
        end_angle = math.radians(60)
        current = start_angle + (end_angle - start_angle) * t

        center_x = cx + 8 * face
        center_y = cy - 5
        radius = 26

        # Multi-layered crescent trail
        for i in range(14):
            offset = i * 0.10
            seg_t = t - offset * 0.05
            if seg_t < 0:
                continue
            seg_angle = start_angle + (end_angle - start_angle) * seg_t

            alpha_fade = 1.0 - offset
            alpha = max(0, min(255, int(210 * alpha_fade * math.sin(t * math.pi))))
            if alpha <= 0:
                continue

            for r_offset, blade_color, w in [
                (0, palette['heal_darkest'], 5),
                (0, palette['heal_dark'], 4),
                (0, palette['heal_mid'], 3),
                (0, palette['heal_light'], 2),
                (0, palette['heal_bright'], 1),
            ]:
                inner_r = radius - 5 + r_offset
                outer_r = radius + 4 + r_offset

                ix = center_x + int(math.cos(seg_angle) * inner_r) * face
                iy = center_y + int(math.sin(seg_angle) * inner_r)
                ox = center_x + int(math.cos(seg_angle) * outer_r) * face
                oy = center_y + int(math.sin(seg_angle) * outer_r)

                _NS_troll._blend_alpha(surface, (*blade_color, alpha), [
                    (ix, iy), (ox, oy),
                    (ox + 1, oy + 1), (ix + 1, iy + 1),
                ])
                _NS_troll._aaline(surface, (*blade_color, alpha),
                        (ix, iy), (ox, oy), w)

        # Leading bright tip
        lead_alpha = int(240 * math.sin(t * math.pi))
        lead_x = center_x + int(math.cos(current) * radius) * face
        lead_y = center_y + int(math.sin(current) * radius)
        _NS_troll._aacircle(surface, palette['heal_bright'], (lead_x, lead_y), 4)
        _NS_troll._aacircle(surface, palette['heal_hot'], (lead_x, lead_y), 2)
        _NS_troll._aacircle(surface, palette['shine'], (lead_x, lead_y), 1)


    def _draw_impact_sparkle(surface, cx, cy, face, progress, palette):
        """Impact sparkle at peak of swing (like the star in reference)."""
        t = (progress - 0.50) / 0.15
        t = max(0.0, min(1.0, t))

        impact_x = cx + 24 * face
        impact_y = cy - 3

        # 4-pointed star spikes
        star_r = int(6 + t * 8)
        alpha = int(240 * (1 - t))

        for angle_deg in [0, 45, 90, 135]:
            angle = math.radians(angle_deg)
            ix = impact_x + int(math.cos(angle) * 2)
            iy = impact_y + int(math.sin(angle) * 2)
            ox1 = impact_x + int(math.cos(angle) * star_r)
            oy1 = impact_y + int(math.sin(angle) * star_r)
            ox2 = impact_x - int(math.cos(angle) * star_r)
            oy2 = impact_y - int(math.sin(angle) * star_r)

            _NS_troll._aaline(surface, (*palette['heal_dark'], alpha),
                    (ox1, oy1), (ox2, oy2), 3)
            _NS_troll._aaline(surface, (*palette['heal_light'], alpha),
                    (ox1, oy1), (ox2, oy2), 2)
            _NS_troll._aaline(surface, (*palette['heal_hot'], alpha),
                    (ox1, oy1), (ox2, oy2), 1)

        # Central bright core
        core_alpha = int(255 * (1 - t))
        _NS_troll._aacircle(surface, (*palette['heal_bright'], core_alpha),
                  (impact_x, impact_y), 4)
        _NS_troll._aacircle(surface, (*palette['heal_hot'], core_alpha),
                  (impact_x, impact_y), 2)
        _NS_troll._aacircle(surface, palette['shine'], (impact_x, impact_y),
                  max(1, int(1 + (1 - t))))


    # ═══════════════════════════════════════════════════════
    # REGENERATION EFFECTS
    # ═══════════════════════════════════════════════════════

    def _draw_regen_ground_aura(surface, x, y, radius, timer, palette):
        """Green circle aura on ground when regenerating."""
        pulse = math.sin(timer * 0.1) * 0.3 + 0.7
        aura_w = radius * 4
        aura_h = radius
        aura_surf = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)

        for r in range(radius, 3, -2):
            alpha = int((radius - r) * 5 * pulse)
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                pygame.draw.ellipse(aura_surf,
                                    (*palette['heal_dark'], alpha),
                                    (aura_w // 2 - r * 2,
                                     aura_h // 2 - r // 2,
                                     r * 4, r))

        # Bright inner ring
        inner_alpha = int(180 * pulse)
        pygame.draw.ellipse(aura_surf,
                            (*palette['heal_bright'], inner_alpha),
                            (aura_w // 2 - radius,
                             aura_h // 2 - radius // 4,
                             radius * 2, radius // 2), 1)

        surface.blit(aura_surf, (x - aura_w // 2, y - aura_h // 2))


    def _draw_regen_particles(surface, x, y, radius, timer, palette):
        """Green healing particles floating up around body."""
        for i in range(8):
            phase = (timer * 0.02 + i * 0.13) % 1.0
            # Circle around body
            angle = i * math.pi * 2 / 8 + timer * 0.02
            base_x = x + int(math.cos(angle) * radius * 1.2)

            # Rise upward
            rise = int(phase * (radius * 2 + 10))
            py = y + radius - rise + int(math.sin(timer * 0.05 + i) * 2)

            # Fade in and out
            alpha_fade = math.sin(phase * math.pi)
            alpha = max(0, min(255, int(230 * alpha_fade)))
            if alpha <= 0:
                continue

            size = max(1, int(3 * alpha_fade))

            # Small green cross particle
            particle_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            cx_p = size * 2
            cy_p = size * 2

            # Cross shape
            _NS_troll._aacircle(particle_surf, (*palette['heal_dark'], alpha),
                      (cx_p, cy_p), size + 1)
            _NS_troll._aacircle(particle_surf, (*palette['heal_mid'], alpha),
                      (cx_p, cy_p), size)
            _NS_troll._aacircle(particle_surf, (*palette['heal_bright'], alpha),
                      (cx_p, cy_p), max(1, size - 1))
            _NS_troll._aacircle(particle_surf, (*palette['heal_hot'], alpha),
                      (cx_p, cy_p), max(1, size - 2))

            surface.blit(particle_surf, (base_x - cx_p, py - cy_p))

        # Bigger sparkles at feet
        for i in range(4):
            phase = (timer * 0.03 + i * 0.25) % 1.0
            angle = i * math.pi / 2 + timer * 0.03
            px = x + int(math.cos(angle) * radius)
            py = y + radius - 2 + int(math.sin(angle) * 3)

            rise_alpha = int(220 * (1 - phase))
            if rise_alpha <= 0:
                continue

            # Sparkle plus
            _NS_troll._aaline(surface, (*palette['heal_bright'], rise_alpha),
                    (px - 2, py), (px + 2, py), 1)
            _NS_troll._aaline(surface, (*palette['heal_bright'], rise_alpha),
                    (px, py - 2), (px, py + 2), 1)
            _NS_troll._aacircle(surface, (*palette['heal_hot'], rise_alpha),
                      (px, py), 1)


    def _draw_regen_cross_icon(surface, x, y, timer, palette):
        """Small green healing cross icon above head."""
        pulse = math.sin(timer * 0.1) * 0.25 + 0.75
        size = int(4 * pulse)
        if size < 2:
            size = 2

        # Icon background (dark rounded square)
        icon_size = 10
        icon_surf = pygame.Surface((icon_size * 2, icon_size * 2), pygame.SRCALPHA)
        ics = icon_size
        # Shadow
        pygame.draw.rect(icon_surf, (0, 0, 0, 180),
                         (ics - 6, ics - 6, 12, 12), border_radius=2)
        # Frame
        pygame.draw.rect(icon_surf, palette['heal_darkest'],
                         (ics - 5, ics - 5, 10, 10), border_radius=2)
        pygame.draw.rect(icon_surf, palette['heal_dark'],
                         (ics - 5, ics - 5, 10, 10), 1, border_radius=2)

        # Green cross
        pygame.draw.rect(icon_surf, palette['heal_light'],
                         (ics - 1, ics - 4, 2, 8))
        pygame.draw.rect(icon_surf, palette['heal_light'],
                         (ics - 4, ics - 1, 8, 2))
        pygame.draw.rect(icon_surf, palette['heal_hot'],
                         (ics - 1, ics - 3, 2, 6))
        pygame.draw.rect(icon_surf, palette['heal_hot'],
                         (ics - 3, ics - 1, 6, 2))
        pygame.draw.rect(icon_surf, palette['shine'],
                         (ics - 1, ics - 3, 1, 2))

        surface.blit(icon_surf, (x - icon_size, y - icon_size))

        # Sparkles orbiting the icon
        for i in range(3):
            angle = timer * 0.12 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * 10)
            sy = y + int(math.sin(angle) * 6)
            alpha = int(180 * pulse)
            _NS_troll._aacircle(surface, (*palette['heal_bright'], alpha), (sx, sy), 2)
            _NS_troll._aacircle(surface, (*palette['heal_hot'], alpha), (sx, sy), 1)


    # ═══════════════════════════════════════════════════════
    # CHAMPION AURA (Lvl 5)
    # ═══════════════════════════════════════════════════════

    def _draw_champion_aura(surface, x, y, timer, palette):
        """Green rage aura around chieftain."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_r = 24
        aura_surf = pygame.Surface((aura_r * 3, aura_r * 3), pygame.SRCALPHA)

        for r in range(aura_r, 3, -2):
            alpha = int((aura_r - r) * 4 * pulse)
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                _NS_troll._aacircle(aura_surf, (*palette['heal_mid'], alpha),
                          (aura_r * 3 // 2, aura_r * 3 // 2), r)

        surface.blit(aura_surf,
                     (x - aura_r * 3 // 2, y - aura_r * 3 // 2))

        # Orbiting green embers
        for i in range(4):
            angle = timer * 0.05 + i * math.pi / 2
            sx = x + int(math.cos(angle) * 20)
            sy = y + int(math.sin(angle) * 14)
            _NS_troll._aacircle(surface, palette['heal_bright'], (sx, sy), 2)
            _NS_troll._aacircle(surface, palette['heal_hot'], (sx, sy), 1)

# ====================================================================
# undead.py
# ====================================================================
class _NS_undead:
    """Namespace undead - isi asli tidak diubah."""

    # ================================
    # minions/undead.py
    # HD Undead - The Rise of the Dead
    # Skeleton knight with sword & shield + Unholy Aura passive
    # ================================



    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')
    HAS_AALINES = hasattr(pygame.draw, 'aalines')


    def _clamp_color(color):
        if len(color) == 3:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
            )
        elif len(color) == 4:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))),
            )
        return color


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_undead._clamp_color(color)
        if _NS_undead.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aaline(surface, color, start, end, width=1):
        color = _NS_undead._clamp_color(color)
        if width == 1 and _NS_undead.HAS_AALINES:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.line(surface, color, start, end, width)
        except (TypeError, ValueError):
            pass


    def _aapolygon(surface, color, points):
        color = _NS_undead._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    def _blend_alpha(surface, color, rect_pts):
        if len(rect_pts) < 3:
            return
        xs = [p[0] for p in rect_pts]
        ys = [p[1] for p in rect_pts]
        minx, miny = min(xs) - 2, min(ys) - 2
        maxx, maxy = max(xs) + 2, max(ys) + 2
        w, h = maxx - minx, maxy - miny
        if w <= 0 or h <= 0:
            return
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        shifted = [(p[0] - minx, p[1] - miny) for p in rect_pts]
        pygame.draw.polygon(tmp, _NS_undead._clamp_color(color), shifted)
        surface.blit(tmp, (minx, miny))


    # ═══════════════════════════════════════════════════════
    # PALETTE - Undead skeleton knight
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            # ═══ BLUE TEAM (Bluish steel armor - "friendly" undead) ═══
            return {
                # Bone (skull, ribs)
                'bone_darkest': (65, 60, 55),
                'bone_dark': (110, 100, 88),
                'bone_mid': (165, 155, 140),
                'bone_light': (210, 200, 185),
                'bone_high': (240, 235, 220),
                'bone_shine': (255, 252, 240),

                # Dark iron armor (bluish tinted)
                'armor_darkest': (18, 22, 32),
                'armor_dark': (40, 48, 62),
                'armor_mid': (75, 88, 108),
                'armor_light': (130, 145, 175),
                'armor_high': (185, 200, 225),
                'armor_shine': (230, 240, 255),

                # Dark leather (straps)
                'leather_darkest': (22, 15, 10),
                'leather_dark': (48, 32, 20),
                'leather_mid': (80, 55, 32),
                'leather_light': (120, 88, 55),

                # Cloth / cape (dark purple)
                'cloth_darkest': (25, 12, 40),
                'cloth_dark': (50, 25, 75),
                'cloth_mid': (85, 45, 125),
                'cloth_light': (130, 80, 175),

                # Metal (blade)
                'blade_dark': (48, 55, 68),
                'blade_mid': (108, 122, 142),
                'blade_light': (180, 195, 215),
                'blade_high': (230, 240, 255),
                'blade_shine': (255, 255, 255),

                # Gold trim
                'gold_darkest': (85, 55, 12),
                'gold_dark': (145, 105, 25),
                'gold_mid': (210, 160, 55),
                'gold_light': (245, 205, 95),
                'gold_high': (255, 235, 160),

                # UNHOLY (purple magic - aura, eyes, souls)
                'unholy_darkest': (30, 8, 55),
                'unholy_dark': (70, 22, 115),
                'unholy_mid': (125, 50, 185),
                'unholy_light': (175, 100, 230),
                'unholy_bright': (215, 155, 250),
                'unholy_hot': (245, 215, 255),
                'unholy_white': (255, 245, 255),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 5, 10),
            }
        else:
            # ═══ RED TEAM (Rusted armor - evil undead) ═══
            return {
                'bone_darkest': (55, 48, 42),
                'bone_dark': (95, 82, 70),
                'bone_mid': (150, 135, 115),
                'bone_light': (195, 180, 155),
                'bone_high': (230, 220, 200),
                'bone_shine': (250, 245, 230),

                # Rusted dark iron
                'armor_darkest': (20, 15, 15),
                'armor_dark': (45, 35, 32),
                'armor_mid': (82, 68, 60),
                'armor_light': (135, 115, 100),
                'armor_high': (185, 165, 145),
                'armor_shine': (225, 210, 195),

                'leather_darkest': (18, 12, 8),
                'leather_dark': (42, 28, 15),
                'leather_mid': (72, 48, 25),
                'leather_light': (110, 78, 45),

                'cloth_darkest': (28, 10, 15),
                'cloth_dark': (58, 22, 30),
                'cloth_mid': (98, 40, 55),
                'cloth_light': (145, 72, 88),

                'blade_dark': (42, 42, 52),
                'blade_mid': (95, 95, 110),
                'blade_light': (160, 160, 180),
                'blade_high': (215, 215, 230),
                'blade_shine': (248, 248, 255),

                'gold_darkest': (65, 42, 10),
                'gold_dark': (110, 78, 20),
                'gold_mid': (165, 120, 40),
                'gold_light': (210, 170, 75),
                'gold_high': (240, 208, 130),

                'unholy_darkest': (35, 8, 55),
                'unholy_dark': (80, 22, 120),
                'unholy_mid': (135, 55, 190),
                'unholy_light': (180, 105, 232),
                'unholy_bright': (218, 160, 250),
                'unholy_hot': (246, 218, 255),
                'unholy_white': (255, 240, 255),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 3, 5),
            }


    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_undead(surface, minion, x, y):
        """Draw undead - CACHED"""
        from minions.base_renderer import cached_minion_draw
        cached_minion_draw(surface, minion, x, y, _NS_undead._draw_undead_full)


    def _draw_undead_full(surface, minion, x, y):
        """Original undead render."""
        palette = _NS_undead._get_palette(minion.team)

        walk_phase = minion.walk_cycle
        is_running = minion.is_moving
        anim_time = minion.anim_time

        # Unholy Aura always ON (it's a passive)
        aura_active = getattr(minion, 'unholy_aura_active', True)

        # Attack anim
        attack_progress = 0
        is_attacking = False
        if minion.attack_anim_timer > 0:
            attack_progress = 1.0 - (minion.attack_anim_timer /
                                      minion.attack_anim_max)
            is_attacking = True

        # Slow, stiff undead bob
        if is_running:
            body_bob = int(math.sin(walk_phase * 1.5) * 2)
        else:
            body_bob = int(math.sin(anim_time * 0.04) * 1)

        # Attack lunge
        attack_offset_x = 0
        if is_attacking:
            if attack_progress < 0.25:
                p = attack_progress / 0.25
                attack_offset_x = int(-p * 3) * minion.direction
            elif attack_progress < 0.55:
                p = (attack_progress - 0.25) / 0.30
                ease = p * p * (3 - 2 * p)
                attack_offset_x = int((-3 + ease * 10)) * minion.direction
            else:
                p = (attack_progress - 0.55) / 0.45
                ease = 1 - (1 - p) * (1 - p)
                attack_offset_x = int((7 - ease * 7)) * minion.direction

        # Spawn scale
        spawn_scale = 1.0
        if minion.spawn_anim > 0:
            spawn_scale = 1.0 - (minion.spawn_anim / 20.0) * 0.5
            spawn_scale = max(0.3, spawn_scale)

        draw_x = x + attack_offset_x
        draw_y = y + body_bob

        # Ground shadow
        _NS_undead._draw_ground_shadow(surface, x, y + minion.radius + 6, minion.radius)

        # UNHOLY AURA on ground (behind body)
        if aura_active:
            _NS_undead._draw_unholy_ground_aura(surface, x, y + minion.radius + 4,
                                      minion.radius, anim_time, palette)

        # Slow FX
        if minion.slow_timer > 0:
            draw_slow_effect(surface, x, y, minion.radius, anim_time)

        # Main body per level
        level = minion.nexus_level
        if level == 1:
            _NS_undead._draw_undead_lvl1(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        elif level == 2:
            _NS_undead._draw_undead_lvl2(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        elif level == 3:
            _NS_undead._draw_undead_lvl3(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        elif level == 4:
            _NS_undead._draw_undead_lvl4(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)
        else:
            _NS_undead._draw_undead_lvl5(surface, minion, draw_x, draw_y,
                              walk_phase, attack_progress,
                              is_running, is_attacking, palette)

        # Death Knight aura for lvl 5
        if level >= 5:
            _NS_undead._draw_death_knight_aura(surface, x, y, anim_time, palette)

        # UNHOLY floating soul skulls (aura visual)
        if aura_active:
            _NS_undead._draw_floating_souls(surface, x, y, minion.radius, anim_time,
                                 minion.nexus_level, palette)
            # Aura sparkles rising
            _NS_undead._draw_aura_sparkles(surface, x, y, minion.radius, anim_time, palette)

        # Attack swing arc (purple crescent - match reference)
        if is_attacking and 0.30 <= attack_progress <= 0.72:
            _NS_undead._draw_unholy_arc(surface, draw_x, draw_y, minion.direction,
                             attack_progress, palette)

        # Impact sparkle at peak
        if is_attacking and 0.48 <= attack_progress <= 0.62:
            _NS_undead._draw_unholy_impact(surface, draw_x, draw_y, minion.direction,
                                attack_progress, palette)

        # Slash effects
        if minion.slash_effects:
            draw_slash_effects(surface, draw_x, draw_y, minion.slash_effects)


        # HP bar
        bar_w = minion.radius * 2 + 8
        by = y - minion.radius - 18
        draw_hp_bar(surface, x, by, bar_w,
                    minion.hp / minion.max_hp, minion.team)

        # Level stars
        if minion.nexus_level >= 3:
            for i in range(minion.nexus_level - 2):
                star_x = x - 5 + i * 5
                star_y = by - 5
                _NS_undead._aacircle(surface, palette['unholy_light'], (star_x, star_y), 2)
                pygame.draw.rect(surface, palette['shine'],
                                 (star_x, star_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # GROUND SHADOW
    # ═══════════════════════════════════════════════════════

    def _draw_ground_shadow(surface, x, y, radius):
        shadow_surf = pygame.Surface((radius * 5, 12), pygame.SRCALPHA)
        for r in range(6, 0, -1):
            alpha = (6 - r) * 22
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                                (6 - r, 6 - r,
                                 radius * 5 - (6 - r) * 2, r * 2))
        surface.blit(shadow_surf, (x - radius * 5 // 2, y - 6))


    # ═══════════════════════════════════════════════════════
    # LEVEL 1: SKELETON (basic, no shield)
    # ═══════════════════════════════════════════════════════

    def _draw_undead_lvl1(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_undead._draw_cape(surface, bx, y - 5, walk_phase, palette, size='small')
        _NS_undead._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette,
                   armored=False)
        _NS_undead._draw_torso_ribs(surface, bx, y - 2, face, palette, hurt)
        _NS_undead._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_shield=False)
        _NS_undead._draw_head_skull(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                         has_helm=False, has_horns=False, has_crown=False)
        _NS_undead._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='sword_small')


    # ═══════════════════════════════════════════════════════
    # LEVEL 2: RISEN SOLDIER (+basic helm +chestplate)
    # ═══════════════════════════════════════════════════════

    def _draw_undead_lvl2(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_undead._draw_cape(surface, bx, y - 5, walk_phase, palette, size='medium')
        _NS_undead._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette,
                   armored=False)
        _NS_undead._draw_torso_chestplate(surface, bx, y - 2, face, palette, hurt,
                                has_emblem=False)
        _NS_undead._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_shield=False)
        _NS_undead._draw_head_skull(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                         has_helm=True, has_horns=False, has_crown=False)
        _NS_undead._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='sword_small')


    # ═══════════════════════════════════════════════════════
    # LEVEL 3: KNIGHT (+shield +bigger sword)
    # ═══════════════════════════════════════════════════════

    def _draw_undead_lvl3(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_undead._draw_cape(surface, bx, y - 5, walk_phase, palette, size='medium')
        _NS_undead._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette,
                   armored=True)
        _NS_undead._draw_torso_chestplate(surface, bx, y - 2, face, palette, hurt,
                                has_emblem=True)
        _NS_undead._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_shield=True)
        _NS_undead._draw_head_skull(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                         has_helm=True, has_horns=False, has_crown=False)
        _NS_undead._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='sword_big')


    # ═══════════════════════════════════════════════════════
    # LEVEL 4: DEATH GUARD (+horns +better shield)
    # ═══════════════════════════════════════════════════════

    def _draw_undead_lvl4(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_undead._draw_cape(surface, bx, y - 5, walk_phase, palette, size='big')
        _NS_undead._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette,
                   armored=True)
        _NS_undead._draw_torso_chestplate(surface, bx, y - 2, face, palette, hurt,
                                has_emblem=True, ornate=True)
        _NS_undead._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_shield=True, ornate_shield=True)
        _NS_undead._draw_shoulder_spikes(surface, bx - r + 1, y - 4, palette)
        _NS_undead._draw_shoulder_spikes(surface, bx + r - 1, y - 4, palette, mirror=True)
        _NS_undead._draw_head_skull(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                         has_helm=True, has_horns=True, has_crown=False)
        _NS_undead._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='sword_big')


    # ═══════════════════════════════════════════════════════
    # LEVEL 5: DEATH KNIGHT (crown + huge sword + full armor)
    # ═══════════════════════════════════════════════════════

    def _draw_undead_lvl5(surface, minion, x, y, walk_phase,
                          attack_progress, is_running, is_attacking, palette):
        r = minion.radius
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        body_sway = int(math.sin(walk_phase * 2) * 1) if is_running else 0
        head_bob = int(math.sin(walk_phase * 2 + math.pi/4) * 1) if is_running else 0
        bx = x + body_sway

        _NS_undead._draw_cape(surface, bx, y - 5, walk_phase, palette, size='huge')
        _NS_undead._draw_legs(surface, bx, y + r - 2, walk_phase, is_running, palette,
                   armored=True)
        _NS_undead._draw_torso_chestplate(surface, bx, y - 2, face, palette, hurt,
                                has_emblem=True, ornate=True, has_gold_trim=True)
        _NS_undead._draw_arm_offhand(surface, bx - r + 2, y, face, walk_phase,
                           is_running, palette, has_shield=True, ornate_shield=True)
        _NS_undead._draw_shoulder_spikes(surface, bx - r + 1, y - 4, palette)
        _NS_undead._draw_shoulder_spikes(surface, bx + r - 1, y - 4, palette, mirror=True)
        _NS_undead._draw_head_skull(surface, bx, y - r - 4 + head_bob, face, palette, hurt,
                         has_helm=True, has_horns=True, has_crown=True)
        _NS_undead._draw_arm_weapon(surface, bx + r - 2, y, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='sword_huge')


    # ═══════════════════════════════════════════════════════
    # CAPE (dark purple flowing)
    # ═══════════════════════════════════════════════════════

    def _draw_cape(surface, cx, cy, phase, palette, size='medium'):
        """Dark purple cape flowing behind."""
        sway1 = int(math.sin(phase * 0.7) * 2)
        sway2 = int(math.sin(phase * 0.9 + 0.5) * 2)

        if size == 'small':
            length = 12
            width = 8
        elif size == 'medium':
            length = 16
            width = 10
        elif size == 'big':
            length = 20
            width = 12
        else:  # huge
            length = 24
            width = 14

        # Cape shape (from shoulders down, flowing)
        cape_outer = [
            (cx - width, cy),
            (cx + width, cy),
            (cx + width - 1, cy + length // 3),
            (cx + width - 2 + sway1, cy + length * 2 // 3),
            (cx + width - 4 + sway2, cy + length),
            (cx - 2, cy + length + 1),
            (cx - width + 4 - sway1, cy + length),
            (cx - width + 2 - sway2, cy + length * 2 // 3),
            (cx - width + 1, cy + length // 3),
        ]
        # Shadow
        _NS_undead._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in cape_outer])
        # Layers
        _NS_undead._aapolygon(surface, palette['cloth_darkest'], cape_outer)

        cape_mid = [
            (cx - width + 1, cy + 1),
            (cx + width - 1, cy + 1),
            (cx + width - 2, cy + length // 3),
            (cx + width - 3 + sway1, cy + length * 2 // 3),
            (cx - 2, cy + length),
            (cx - width + 3 - sway1, cy + length * 2 // 3),
            (cx - width + 2, cy + length // 3),
        ]
        _NS_undead._aapolygon(surface, palette['cloth_dark'], cape_mid)

        cape_inner = [
            (cx - width + 2, cy + 2),
            (cx + width - 2, cy + 2),
            (cx + width - 4, cy + length // 2),
            (cx - 1, cy + length - 2),
            (cx - width + 4, cy + length // 2),
        ]
        _NS_undead._aapolygon(surface, palette['cloth_mid'], cape_inner)

        # Highlight streaks
        for streak_x_off in [-width // 2, 0, width // 2]:
            sx = cx + streak_x_off
            _NS_undead._aaline(surface, palette['cloth_light'],
                    (sx, cy + 2), (sx + sway1, cy + length - 3), 1)

        # Torn/tattered bottom
        for i in range(5):
            tx = cx - width + 2 + i * (width // 3)
            ty = cy + length + int(math.sin(phase * 1.5 + i) * 2)
            _NS_undead._aapolygon(surface, palette['cloth_darkest'], [
                (tx - 1, cy + length - 2),
                (tx + 1, cy + length - 2),
                (tx, ty + 2),
            ])


    # ═══════════════════════════════════════════════════════
    # LEGS (armored / bare)
    # ═══════════════════════════════════════════════════════

    def _draw_legs(surface, cx, cy, phase, is_running, palette, armored=False):
        """Legs - either bare bone or armored greaves."""
        if is_running:
            swing_l = math.sin(phase * 2) * 3
            swing_r = -swing_l
        else:
            idle = math.sin(phase * 0.8) * 0.4
            swing_l = idle
            swing_r = -idle

        for side, swing in [(-1, swing_l), (1, swing_r)]:
            hip_x = cx + side * 3
            hip_y = cy - 2

            knee_x = hip_x + int(swing * 0.4)
            knee_y = cy + 3

            foot_x = hip_x + int(swing)
            foot_y = cy + 9

            # Shadow
            _NS_undead._aaline(surface, palette['shadow_deep'],
                    (hip_x + 1, hip_y + 1), (foot_x + 1, foot_y + 1), 6)

            if armored:
                # Armored greaves
                _NS_undead._aaline(surface, palette['armor_darkest'],
                        (hip_x, hip_y), (knee_x, knee_y), 6)
                _NS_undead._aaline(surface, palette['armor_dark'],
                        (hip_x, hip_y), (knee_x, knee_y), 5)
                _NS_undead._aaline(surface, palette['armor_mid'],
                        (hip_x, hip_y), (knee_x, knee_y), 3)
                _NS_undead._aaline(surface, palette['armor_light'],
                        (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)

                _NS_undead._aaline(surface, palette['armor_darkest'],
                        (knee_x, knee_y), (foot_x, foot_y - 2), 6)
                _NS_undead._aaline(surface, palette['armor_dark'],
                        (knee_x, knee_y), (foot_x, foot_y - 2), 5)
                _NS_undead._aaline(surface, palette['armor_mid'],
                        (knee_x, knee_y), (foot_x, foot_y - 2), 3)
                _NS_undead._aaline(surface, palette['armor_light'],
                        (knee_x - 1, knee_y), (foot_x - 1, foot_y - 2), 1)

                # Knee guard (spiked plate)
                _NS_undead._aacircle(surface, palette['armor_darkest'], (knee_x, knee_y), 3)
                _NS_undead._aacircle(surface, palette['armor_dark'], (knee_x, knee_y), 2)
                _NS_undead._aacircle(surface, palette['armor_light'], (knee_x - 1, knee_y - 1), 1)
                # Small spike
                _NS_undead._aapolygon(surface, palette['armor_darkest'], [
                    (knee_x - 1, knee_y - 3),
                    (knee_x, knee_y - 5),
                    (knee_x + 1, knee_y - 3),
                ])
                _NS_undead._aapolygon(surface, palette['armor_mid'], [
                    (knee_x - 1, knee_y - 3),
                    (knee_x, knee_y - 4),
                    (knee_x + 1, knee_y - 3),
                ])
            else:
                # Bare bone leg
                _NS_undead._aaline(surface, palette['bone_darkest'],
                        (hip_x, hip_y), (knee_x, knee_y), 4)
                _NS_undead._aaline(surface, palette['bone_dark'],
                        (hip_x, hip_y), (knee_x, knee_y), 3)
                _NS_undead._aaline(surface, palette['bone_mid'],
                        (hip_x, hip_y), (knee_x, knee_y), 2)
                _NS_undead._aaline(surface, palette['bone_light'],
                        (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)

                _NS_undead._aaline(surface, palette['bone_darkest'],
                        (knee_x, knee_y), (foot_x, foot_y - 2), 4)
                _NS_undead._aaline(surface, palette['bone_dark'],
                        (knee_x, knee_y), (foot_x, foot_y - 2), 3)
                _NS_undead._aaline(surface, palette['bone_mid'],
                        (knee_x, knee_y), (foot_x, foot_y - 2), 2)

                # Knee joint (bone)
                _NS_undead._aacircle(surface, palette['bone_darkest'], (knee_x, knee_y), 2)
                _NS_undead._aacircle(surface, palette['bone_mid'], (knee_x, knee_y), 1)

            # BOOT (armored or basic)
            _NS_undead._draw_armor_boot(surface, foot_x, foot_y, palette, armored)


    def _draw_armor_boot(surface, fx, fy, palette, armored):
        """Iron sabaton boot."""
        boot_pts = [
            (fx - 4, fy - 4),
            (fx + 5, fy - 4),
            (fx + 6, fy - 1),
            (fx + 5, fy + 1),
            (fx - 4, fy + 1),
            (fx - 5, fy - 1),
        ]
        _NS_undead._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in boot_pts])
        _NS_undead._aapolygon(surface, palette['armor_darkest'], boot_pts)
        _NS_undead._aapolygon(surface, palette['armor_dark'], [
            (fx - 3, fy - 3), (fx + 4, fy - 3),
            (fx + 5, fy - 1), (fx + 4, fy),
            (fx - 3, fy), (fx - 4, fy - 1),
        ])
        _NS_undead._aapolygon(surface, palette['armor_mid'], [
            (fx - 3, fy - 3), (fx + 3, fy - 3),
            (fx + 4, fy - 2), (fx + 3, fy - 1),
            (fx - 3, fy - 1),
        ])
        _NS_undead._aaline(surface, palette['armor_light'],
                (fx - 3, fy - 3), (fx + 2, fy - 3), 1)

        # Pointed toe
        _NS_undead._aapolygon(surface, palette['armor_darkest'], [
            (fx + 5, fy - 2),
            (fx + 7, fy),
            (fx + 5, fy),
        ])
        _NS_undead._aapolygon(surface, palette['armor_dark'], [
            (fx + 5, fy - 1),
            (fx + 6, fy),
            (fx + 5, fy),
        ])

        # Gold trim strap
        if armored:
            pygame.draw.rect(surface, palette['gold_dark'],
                             (fx - 3, fy - 2, 6, 1))
            pygame.draw.rect(surface, palette['gold_mid'],
                             (fx - 3, fy - 2, 5, 1))
            pygame.draw.rect(surface, palette['gold_high'],
                             (fx - 2, fy - 2, 1, 1))


    # ═══════════════════════════════════════════════════════
    # TORSO VARIANTS
    # ═══════════════════════════════════════════════════════

    def _draw_torso_ribs(surface, cx, cy, face, palette, hurt):
        """Level 1 - exposed rib cage."""
        body_w = 18
        body_h = 15

        if hurt:
            bone_mid = (255, 255, 255)
        else:
            bone_mid = palette['bone_mid']

        # Shadow silhouette
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=4)

        # Dark background (rib cavity)
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=4)
        pygame.draw.rect(surface, palette['bone_darkest'],
                         (cx - body_w // 2 + 1, cy + 1, body_w - 2, body_h - 2),
                         border_radius=3)

        # Spine (vertical center)
        for spine_y in range(cy + 1, cy + body_h - 1, 2):
            pygame.draw.rect(surface, palette['bone_dark'], (cx - 1, spine_y, 2, 1))
            pygame.draw.rect(surface, palette['bone_light'], (cx, spine_y, 1, 1))

        # Ribs (curved lines on each side)
        for i, rib_y in enumerate([cy + 2, cy + 5, cy + 8, cy + 11]):
            # Left ribs
            _NS_undead._aaline(surface, palette['bone_darkest'],
                    (cx - body_w // 2 + 2, rib_y),
                    (cx - 1, rib_y + 1), 2)
            _NS_undead._aaline(surface, palette['bone_dark'],
                    (cx - body_w // 2 + 2, rib_y),
                    (cx - 1, rib_y + 1), 1)
            _NS_undead._aaline(surface, bone_mid,
                    (cx - body_w // 2 + 3, rib_y),
                    (cx - 2, rib_y + 1), 1)
            # Right ribs
            _NS_undead._aaline(surface, palette['bone_darkest'],
                    (cx + 1, rib_y + 1),
                    (cx + body_w // 2 - 2, rib_y), 2)
            _NS_undead._aaline(surface, palette['bone_dark'],
                    (cx + 1, rib_y + 1),
                    (cx + body_w // 2 - 2, rib_y), 1)
            _NS_undead._aaline(surface, bone_mid,
                    (cx + 2, rib_y + 1),
                    (cx + body_w // 2 - 3, rib_y), 1)

        # Waist band (leather rope)
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, cy + body_h - 3, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, cy + body_h - 3, body_w - 1, 2))


    def _draw_torso_chestplate(surface, cx, cy, face, palette, hurt,
                                has_emblem=False, ornate=False,
                                has_gold_trim=False):
        """Level 2-5 - iron chestplate."""
        body_w = 20 if not ornate else 22
        body_h = 17 if not ornate else 18

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=4)

        # Iron chestplate
        pygame.draw.rect(surface, palette['armor_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=4)
        pygame.draw.rect(surface, palette['armor_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=4)
        pygame.draw.rect(surface, palette['armor_mid'],
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=4)
        pygame.draw.rect(surface, palette['armor_light'],
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=3)
        pygame.draw.rect(surface, palette['armor_high'],
                         (cx - body_w // 2 + 1, cy + 1, 5, 3),
                         border_radius=2)

        # Central abdomen groove (like segmented plate)
        for seg_y in [cy + 3, cy + 7, cy + 11]:
            _NS_undead._aaline(surface, palette['armor_darkest'],
                    (cx - body_w // 2 + 2, seg_y),
                    (cx + body_w // 2 - 2, seg_y), 1)

        # Gold trim (top)
        if has_gold_trim:
            pygame.draw.rect(surface, palette['gold_dark'],
                             (cx - body_w // 2, cy, body_w, 2))
            pygame.draw.rect(surface, palette['gold_mid'],
                             (cx - body_w // 2, cy, body_w - 1, 1))
            pygame.draw.rect(surface, palette['gold_high'],
                             (cx - body_w // 2 + 1, cy, 3, 1))

        # PURPLE SKULL EMBLEM on chest (matches passive icon)
        if has_emblem:
            _NS_undead._draw_chest_emblem(surface, cx, cy + 6, palette, ornate)

        # Rivets
        for rx in [-body_w // 2 + 2, body_w // 2 - 3]:
            for ry in [2, body_h - 5]:
                _NS_undead._aacircle(surface, palette['armor_darkest'],
                          (cx + rx, cy + ry), 1)
                pygame.draw.rect(surface, palette['armor_high'],
                                 (cx + rx, cy + ry - 1, 1, 1))

        # Waist / belt
        belt_y = cy + body_h - 4
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (cx - body_w // 2, belt_y, body_w, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (cx - body_w // 2, belt_y, body_w - 1, 2))

        # Belt buckle
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 3, belt_y - 1 + 1, 6, 5))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 3, belt_y - 1, 6, 5))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 3, belt_y - 1, 5, 4))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 3, belt_y - 1, 4, 3))
        pygame.draw.rect(surface, palette['gold_light'],
                         (cx - 3, belt_y - 1, 2, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 3, belt_y - 1, 1, 1))


    def _draw_chest_emblem(surface, cx, cy, palette, ornate=False):
        """Purple skull emblem on chest (matches Unholy Aura passive icon)."""
        # Frame background
        frame_size = 5 if not ornate else 6
        _NS_undead._aapolygon(surface, palette['shadow_deep'], [
            (cx - frame_size + 1, cy + 1),
            (cx + frame_size + 1, cy + 1),
            (cx + frame_size + 1, cy + frame_size + 2),
            (cx - frame_size + 1, cy + frame_size + 2),
        ])
        # Gold frame
        _NS_undead._aapolygon(surface, palette['gold_dark'], [
            (cx - frame_size, cy),
            (cx + frame_size, cy),
            (cx + frame_size, cy + frame_size + 1),
            (cx - frame_size, cy + frame_size + 1),
        ])
        _NS_undead._aapolygon(surface, palette['gold_mid'], [
            (cx - frame_size + 1, cy + 1),
            (cx + frame_size - 1, cy + 1),
            (cx + frame_size - 1, cy + frame_size),
            (cx - frame_size + 1, cy + frame_size),
        ])
        # Purple background inside frame
        _NS_undead._aapolygon(surface, palette['unholy_darkest'], [
            (cx - frame_size + 1, cy + 2),
            (cx + frame_size - 1, cy + 2),
            (cx + frame_size - 1, cy + frame_size),
            (cx - frame_size + 1, cy + frame_size),
        ])

        # Small skull
        skull_y = cy + 3
        _NS_undead._aacircle(surface, palette['unholy_bright'], (cx, skull_y), 2)
        # Eye sockets
        pygame.draw.rect(surface, palette['unholy_darkest'],
                         (cx - 1, skull_y - 1, 1, 1))
        pygame.draw.rect(surface, palette['unholy_darkest'],
                         (cx + 1, skull_y - 1, 1, 1))
        # Jaw
        pygame.draw.rect(surface, palette['unholy_light'], (cx - 1, skull_y + 1, 3, 1))

        # Purple glow around emblem
        for r in (frame_size + 3, frame_size + 5):
            alpha = 60 - (r - frame_size) * 8
            alpha = max(0, alpha)
            glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*palette['unholy_mid'], alpha),
                               (r * 2, r * 2), r)
            surface.blit(glow_surf, (cx - r * 2, cy + 3 - r * 2))


    # ═══════════════════════════════════════════════════════
    # HEAD (Skull with glowing purple eyes)
    # ═══════════════════════════════════════════════════════

    def _draw_head_skull(surface, cx, cy, face, palette, hurt,
                         has_helm=False, has_horns=False, has_crown=False):
        """Skull head with glowing purple eyes."""
        if hurt:
            bone_mid = (255, 255, 255)
            bone_light = (255, 255, 255)
        else:
            bone_mid = palette['bone_mid']
            bone_light = palette['bone_light']

        head_r = 8

        # ═══ SKULL BASE ═══
        _NS_undead._aacircle(surface, palette['shadow_deep'], (cx + 1, cy + 1), head_r)
        _NS_undead._aacircle(surface, palette['bone_darkest'], (cx, cy), head_r)
        _NS_undead._aacircle(surface, palette['bone_dark'], (cx, cy), head_r - 1)
        _NS_undead._aacircle(surface, bone_mid, (cx - 1, cy - 1), head_r - 2)
        _NS_undead._aacircle(surface, bone_light, (cx - 2, cy - 2), head_r - 4)
        _NS_undead._aacircle(surface, palette['bone_high'], (cx - 3, cy - 3),
                  max(1, head_r - 6))

        # ═══ EYE SOCKETS (dark holes with GLOWING PURPLE eyes) ═══
        for eye_side, eye_x in [(-1, cx - 3), (1, cx + 3)]:
            # Dark socket
            _NS_undead._aacircle(surface, palette['shadow'], (eye_x, cy - 1), 3)
            _NS_undead._aacircle(surface, palette['shadow_deep'], (eye_x, cy - 1), 2)

            # Purple glowing eye
            _NS_undead._aacircle(surface, palette['unholy_dark'], (eye_x, cy - 1), 2)
            _NS_undead._aacircle(surface, palette['unholy_mid'], (eye_x, cy - 1), 1)
            pygame.draw.rect(surface, palette['unholy_bright'],
                             (eye_x, cy - 1, 1, 1))

            # Outer glow
            for glow_r in (4, 3):
                alpha = 100 - glow_r * 15
                alpha = max(0, alpha)
                glow_surf = pygame.Surface((glow_r * 4, glow_r * 4),
                                            pygame.SRCALPHA)
                pygame.draw.circle(glow_surf,
                                   (*palette['unholy_light'], alpha),
                                   (glow_r * 2, glow_r * 2), glow_r)
                surface.blit(glow_surf,
                             (eye_x - glow_r * 2, cy - 1 - glow_r * 2))

        # ═══ NASAL CAVITY (triangular hole) ═══
        _NS_undead._aapolygon(surface, palette['shadow'], [
            (cx - 1, cy + 1),
            (cx + 1, cy + 1),
            (cx, cy + 4),
        ])
        _NS_undead._aapolygon(surface, palette['shadow_deep'], [
            (cx - 1, cy + 2),
            (cx + 1, cy + 2),
            (cx, cy + 3),
        ])

        # ═══ TEETH ROW (grinning mouth) ═══
        mouth_y = cy + 5
        # Base dark mouth
        pygame.draw.rect(surface, palette['shadow'],
                         (cx - 4, mouth_y, 8, 2))
        # Individual teeth
        for tooth_x_off in range(-3, 4, 1):
            tooth_x = cx + tooth_x_off
            pygame.draw.rect(surface, palette['bone_light'],
                             (tooth_x, mouth_y, 1, 2))
            # Dark gaps between teeth
            if tooth_x_off % 2 == 0:
                pygame.draw.rect(surface, palette['shadow'],
                                 (tooth_x, mouth_y + 1, 1, 1))

        # Highlight top teeth
        _NS_undead._aaline(surface, palette['bone_shine'],
                (cx - 3, mouth_y), (cx + 3, mouth_y), 1)

        # ═══ HELM (lvl 2+) ═══
        if has_helm:
            _NS_undead._draw_helm(surface, cx, cy, head_r, palette, has_horns, has_crown)


    def _draw_helm(surface, cx, cy, head_r, palette, has_horns, has_crown):
        """Iron helm covering top of skull."""
        # Helm cap (dome over top of head)
        helm_outer = [
            (cx - head_r - 1, cy - 2),
            (cx - head_r, cy - 5),
            (cx - head_r + 3, cy - head_r - 1),
            (cx, cy - head_r - 3),
            (cx + head_r - 3, cy - head_r - 1),
            (cx + head_r, cy - 5),
            (cx + head_r + 1, cy - 2),
            (cx + head_r, cy),
            (cx - head_r, cy),
        ]
        # Shadow
        _NS_undead._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in helm_outer])

        # Iron layers
        _NS_undead._aapolygon(surface, palette['armor_darkest'], helm_outer)
        _NS_undead._aapolygon(surface, palette['armor_dark'], [
            (cx - head_r, cy - 2),
            (cx - head_r + 1, cy - 5),
            (cx - head_r + 3, cy - head_r),
            (cx, cy - head_r - 2),
            (cx + head_r - 3, cy - head_r),
            (cx + head_r - 1, cy - 5),
            (cx + head_r, cy - 2),
            (cx + head_r - 1, cy - 1),
            (cx - head_r + 1, cy - 1),
        ])
        _NS_undead._aapolygon(surface, palette['armor_mid'], [
            (cx - head_r + 1, cy - 3),
            (cx - head_r + 2, cy - 5),
            (cx - head_r + 4, cy - head_r + 1),
            (cx, cy - head_r - 1),
            (cx + head_r - 4, cy - head_r + 1),
            (cx + head_r - 2, cy - 5),
            (cx + head_r - 1, cy - 3),
        ])
        # Highlight
        _NS_undead._aapolygon(surface, palette['armor_light'], [
            (cx - head_r + 2, cy - 4),
            (cx - 3, cy - head_r),
            (cx - 1, cy - head_r - 1),
            (cx - 2, cy - 5),
        ])
        pygame.draw.rect(surface, palette['armor_high'],
                         (cx - 2, cy - head_r - 1, 2, 1))

        # Center helm ridge (going front to back)
        _NS_undead._aaline(surface, palette['armor_darkest'],
                (cx, cy - head_r - 2), (cx, cy), 1)

        # Nose guard (going down between eyes)
        _NS_undead._aapolygon(surface, palette['armor_darkest'], [
            (cx - 1, cy - 2),
            (cx + 1, cy - 2),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
        ])
        _NS_undead._aapolygon(surface, palette['armor_dark'], [
            (cx - 1, cy - 1),
            (cx, cy - 1),
            (cx, cy + 1),
            (cx - 1, cy + 1),
        ])
        pygame.draw.rect(surface, palette['armor_light'], (cx - 1, cy - 1, 1, 1))

        # Side cheek guards
        for side in (-1, 1):
            _NS_undead._aapolygon(surface, palette['armor_darkest'], [
                (cx + side * (head_r - 1), cy - 1),
                (cx + side * (head_r + 1), cy - 2),
                (cx + side * (head_r + 1), cy + 2),
                (cx + side * (head_r - 1), cy + 3),
            ])
            _NS_undead._aapolygon(surface, palette['armor_dark'], [
                (cx + side * (head_r - 1), cy),
                (cx + side * (head_r), cy - 1),
                (cx + side * (head_r), cy + 1),
                (cx + side * (head_r - 1), cy + 2),
            ])

        # ═══ HORNS (lvl 4+) ═══
        if has_horns:
            for side in (-1, 1):
                # Curved horn base at side of helm
                base_x = cx + side * (head_r - 1)
                base_y = cy - 4
                mid_x = base_x + side * 3
                mid_y = cy - head_r
                tip_x = base_x + side * 5
                tip_y = cy - head_r - 3

                # Shadow
                _NS_undead._aapolygon(surface, palette['shadow_deep'], [
                    (base_x + 1, base_y + 1),
                    (mid_x + 1, mid_y + 1),
                    (tip_x + 1, tip_y + 1),
                ])

                # Bone horn layers
                _NS_undead._aapolygon(surface, palette['bone_darkest'], [
                    (base_x - 1, base_y),
                    (base_x + 1, base_y),
                    (mid_x, mid_y),
                    (tip_x, tip_y),
                ])
                _NS_undead._aapolygon(surface, palette['bone_dark'], [
                    (base_x, base_y),
                    (base_x + 1, base_y),
                    (mid_x, mid_y),
                    (tip_x, tip_y),
                ])
                _NS_undead._aaline(surface, palette['bone_mid'],
                        (base_x, base_y), (tip_x, tip_y), 1)
                pygame.draw.rect(surface, palette['bone_light'],
                                 (tip_x, tip_y, 1, 1))

        # ═══ CROWN (lvl 5) ═══
        if has_crown:
            _NS_undead._draw_crown(surface, cx, cy - head_r, palette)


    def _draw_crown(surface, cx, cy, palette):
        """Dark gold spiked crown for Death Knight."""
        # Base band
        pygame.draw.rect(surface, palette['shadow'], (cx - 6, cy + 1, 12, 3))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 6, cy, 12, 3))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 6, cy, 11, 2))
        pygame.draw.rect(surface, palette['gold_mid'],
                         (cx - 6, cy, 10, 1))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 5, cy, 3, 1))

        # 3 spikes going up
        for spike_x_off in [-4, 0, 4]:
            sx = cx + spike_x_off
            # Shadow
            _NS_undead._aapolygon(surface, palette['shadow_deep'], [
                (sx - 2, cy + 1),
                (sx, cy - 4),
                (sx + 2, cy + 1),
            ])
            # Spike layers
            _NS_undead._aapolygon(surface, palette['gold_darkest'], [
                (sx - 2, cy),
                (sx, cy - 4),
                (sx + 2, cy),
            ])
            _NS_undead._aapolygon(surface, palette['gold_dark'], [
                (sx - 1, cy),
                (sx, cy - 3),
                (sx + 2, cy),
            ])
            _NS_undead._aapolygon(surface, palette['gold_mid'], [
                (sx - 1, cy),
                (sx, cy - 2),
                (sx + 1, cy),
            ])
            pygame.draw.rect(surface, palette['gold_light'], (sx, cy - 2, 1, 1))
            pygame.draw.rect(surface, palette['gold_high'], (sx, cy - 2, 1, 1))

        # Purple gem in center
        _NS_undead._aacircle(surface, palette['shadow'], (cx, cy + 1), 2)
        _NS_undead._aacircle(surface, palette['unholy_darkest'], (cx, cy + 1), 2)
        _NS_undead._aacircle(surface, palette['unholy_dark'], (cx, cy + 1), 1)
        pygame.draw.rect(surface, palette['unholy_bright'], (cx, cy, 1, 1))
        pygame.draw.rect(surface, palette['unholy_hot'], (cx, cy, 1, 1))


    # ═══════════════════════════════════════════════════════
    # SHOULDER SPIKES
    # ═══════════════════════════════════════════════════════

    def _draw_shoulder_spikes(surface, x, y, palette, mirror=False):
        """Iron pauldron with spikes."""
        direction = -1 if mirror else 1

        pad_pts = [
            (x - 4 * direction, y),
            (x + 3 * direction, y),
            (x + 4 * direction, y + 3),
            (x + 2 * direction, y + 6),
            (x - 4 * direction, y + 5),
        ]

        _NS_undead._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in pad_pts])
        _NS_undead._aapolygon(surface, palette['armor_darkest'], pad_pts)
        _NS_undead._aapolygon(surface, palette['armor_dark'], [
            (x - 3 * direction, y + 1),
            (x + 2 * direction, y + 1),
            (x + 3 * direction, y + 3),
            (x + 1 * direction, y + 5),
            (x - 3 * direction, y + 4),
        ])
        _NS_undead._aapolygon(surface, palette['armor_mid'], [
            (x - 3 * direction, y + 1),
            (x + 1 * direction, y + 1),
            (x + 2 * direction, y + 3),
            (x - 2 * direction, y + 4),
        ])
        _NS_undead._aapolygon(surface, palette['armor_light'], [
            (x - 3 * direction, y + 1),
            (x - 1 * direction, y + 1),
            (x - 2 * direction, y + 3),
        ])
        pygame.draw.rect(surface, palette['armor_high'],
                         (x - 3 * direction, y + 1, 1, 1))

        # Gold trim bottom
        _NS_undead._aaline(surface, palette['gold_dark'],
                (x - 4 * direction, y + 5),
                (x + 3 * direction, y + 5), 2)
        _NS_undead._aaline(surface, palette['gold_mid'],
                (x - 4 * direction, y + 5),
                (x + 2 * direction, y + 5), 1)

        # 3 spikes on top
        for spike_i in range(3):
            sx = x + (-3 + spike_i * 3) * direction
            sy = y

            _NS_undead._aapolygon(surface, palette['shadow_deep'], [
                (sx - 1, sy + 1), (sx, sy - 5), (sx + 1, sy + 1),
            ])
            _NS_undead._aapolygon(surface, palette['armor_darkest'], [
                (sx - 1, sy), (sx, sy - 5), (sx + 1, sy),
            ])
            _NS_undead._aapolygon(surface, palette['armor_dark'], [
                (sx - 1, sy), (sx, sy - 4), (sx + 1, sy),
            ])
            _NS_undead._aapolygon(surface, palette['armor_mid'], [
                (sx - 1, sy), (sx, sy - 3), (sx, sy),
            ])
            pygame.draw.rect(surface, palette['armor_light'], (sx, sy - 3, 1, 2))
            pygame.draw.rect(surface, palette['armor_high'], (sx, sy - 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # ARMS
    # ═══════════════════════════════════════════════════════

    def _draw_arm_offhand(surface, sx, sy, face, walk_phase, is_running,
                          palette, has_shield=False, ornate_shield=False):
        """Off-hand - can hold shield."""
        if is_running:
            arm_swing = math.sin(walk_phase) * 0.3
        else:
            arm_swing = math.sin(walk_phase * 0.5) * 0.1

        arm_angle = arm_swing * (-face)

        upper_len = 5
        elbow_x = sx + int(math.cos(arm_angle + math.pi / 2) * upper_len) * (-face)
        elbow_y = sy + int(math.sin(arm_angle + math.pi / 2) * upper_len) + 2

        _NS_undead._draw_armored_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = arm_angle * 1.4
        hand_x = elbow_x + int(math.cos(forearm_angle) * 5) * (-face)
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_undead._draw_armored_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        # Gauntlet
        _NS_undead._draw_gauntlet(surface, hand_x, hand_y, palette)

        # SHIELD
        if has_shield:
            _NS_undead._draw_shield(surface, hand_x - 3, hand_y - 2, palette, ornate_shield)


    def _draw_arm_weapon(surface, sx, sy, face, walk_phase,
                         attack_progress, is_running, is_attacking,
                         palette, weapon='sword_small'):
        """Weapon hand with heavy sword swing."""
        if is_attacking:
            if attack_progress < 0.25:
                t = attack_progress / 0.25
                t = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.6 * t
                hand_extend = -t * 3
            elif attack_progress < 0.55:
                t = (attack_progress - 0.25) / 0.30
                t = t ** 2
                swing_angle = -math.pi * 0.6 + t * math.pi * 1.0
                hand_extend = -3 + t * 10
            else:
                t = (attack_progress - 0.55) / 0.45
                t = 1 - (1 - t) ** 2
                swing_angle = math.pi * 0.4 - t * math.pi * 0.4
                hand_extend = 7 - t * 7
        elif is_running:
            swing_angle = math.sin(walk_phase + math.pi) * 0.3
            hand_extend = 0
        else:
            swing_angle = math.sin(walk_phase * 0.5) * 0.1
            hand_extend = 0

        upper_len = 5
        base_angle = math.pi / 2 + swing_angle * face
        elbow_x = sx + int(math.cos(base_angle) * upper_len) * face
        elbow_y = sy + int(math.sin(base_angle) * upper_len) + 2

        _NS_undead._draw_armored_arm(surface, sx, sy, elbow_x, elbow_y, palette)

        forearm_angle = base_angle + swing_angle * 0.7 * face
        hand_x = elbow_x + int(math.cos(forearm_angle) * (5 + hand_extend)) * face
        hand_y = elbow_y + int(math.sin(forearm_angle) * 5) + 2

        _NS_undead._draw_armored_arm(surface, elbow_x, elbow_y, hand_x, hand_y, palette)

        _NS_undead._draw_gauntlet(surface, hand_x, hand_y, palette)

        weapon_angle = forearm_angle - math.pi / 2
        glowing = is_attacking and 0.25 <= attack_progress <= 0.65

        if weapon == 'sword_small':
            _NS_undead._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='small', glowing=glowing)
        elif weapon == 'sword_big':
            _NS_undead._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='big', glowing=glowing)
        elif weapon == 'sword_huge':
            _NS_undead._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='huge', glowing=glowing)

        if is_attacking and 0.25 <= attack_progress <= 0.65:
            _NS_undead._draw_swing_blur(surface, sx, sy, face, attack_progress,
                             hand_x, hand_y, palette)


    def _draw_armored_arm(surface, x1, y1, x2, y2, palette):
        """Iron armored arm segment."""
        _NS_undead._aaline(surface, palette['shadow_deep'],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
        _NS_undead._aaline(surface, palette['armor_darkest'], (x1, y1), (x2, y2), 5)
        _NS_undead._aaline(surface, palette['armor_dark'], (x1, y1), (x2, y2), 4)
        _NS_undead._aaline(surface, palette['armor_mid'], (x1, y1), (x2, y2), 2)
        _NS_undead._aaline(surface, palette['armor_light'], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_gauntlet(surface, x, y, palette):
        """Iron gauntlet."""
        _NS_undead._aacircle(surface, palette['shadow_deep'], (x + 1, y + 1), 3)
        _NS_undead._aacircle(surface, palette['armor_darkest'], (x, y), 3)
        _NS_undead._aacircle(surface, palette['armor_dark'], (x, y), 2)
        _NS_undead._aacircle(surface, palette['armor_mid'], (x - 1, y - 1), 1)
        pygame.draw.rect(surface, palette['armor_high'], (x - 1, y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # SHIELD (with skull emblem)
    # ═══════════════════════════════════════════════════════

    def _draw_shield(surface, x, y, palette, ornate=False):
        """Iron shield with purple skull emblem."""
        if ornate:
            w, h = 12, 14
        else:
            w, h = 10, 12

        # Shield shape (kite/heater style)
        shield_pts = [
            (x - w // 2, y - h // 2),
            (x + w // 2, y - h // 2),
            (x + w // 2, y + h // 4),
            (x, y + h // 2),
            (x - w // 2, y + h // 4),
        ]

        # Shadow
        _NS_undead._aapolygon(surface, palette['shadow'],
                   [(p[0] + 1, p[1] + 1) for p in shield_pts])

        # Metal layers
        _NS_undead._aapolygon(surface, palette['armor_darkest'], shield_pts)
        _NS_undead._aapolygon(surface, palette['armor_dark'], [
            (x - w // 2 + 1, y - h // 2 + 1),
            (x + w // 2 - 1, y - h // 2 + 1),
            (x + w // 2 - 1, y + h // 4),
            (x, y + h // 2 - 1),
            (x - w // 2 + 1, y + h // 4),
        ])
        _NS_undead._aapolygon(surface, palette['armor_mid'], [
            (x - w // 2 + 2, y - h // 2 + 2),
            (x + w // 2 - 2, y - h // 2 + 2),
            (x + w // 2 - 2, y + h // 4 - 1),
            (x, y + h // 2 - 2),
            (x - w // 2 + 2, y + h // 4 - 1),
        ])
        # Highlight (top-left)
        _NS_undead._aapolygon(surface, palette['armor_light'], [
            (x - w // 2 + 2, y - h // 2 + 2),
            (x - 1, y - h // 2 + 2),
            (x - 2, y - 2),
            (x - w // 2 + 2, y),
        ])
        pygame.draw.rect(surface, palette['armor_high'],
                         (x - w // 2 + 2, y - h // 2 + 2, 2, 1))

        # Gold rim
        _NS_undead._aaline(surface, palette['gold_dark'],
                (x - w // 2, y - h // 2), (x + w // 2, y - h // 2), 1)
        _NS_undead._aaline(surface, palette['gold_mid'],
                (x - w // 2, y - h // 2), (x + w // 2 - 1, y - h // 2), 1)

        if ornate:
            # Extra gold trim on sides
            _NS_undead._aaline(surface, palette['gold_dark'],
                    (x - w // 2, y - h // 2), (x - w // 2, y + h // 4), 1)
            _NS_undead._aaline(surface, palette['gold_dark'],
                    (x + w // 2, y - h // 2), (x + w // 2, y + h // 4), 1)
            _NS_undead._aaline(surface, palette['gold_mid'],
                    (x + w // 2, y - h // 2), (x + w // 2, y + h // 4 - 1), 1)

        # PURPLE SKULL EMBLEM in center of shield
        sk_cx, sk_cy = x, y - 1
        # Skull head
        _NS_undead._aacircle(surface, palette['unholy_darkest'], (sk_cx, sk_cy), 3)
        _NS_undead._aacircle(surface, palette['unholy_dark'], (sk_cx, sk_cy), 2)
        _NS_undead._aacircle(surface, palette['unholy_light'], (sk_cx - 1, sk_cy - 1), 1)
        # Eye sockets
        pygame.draw.rect(surface, palette['shadow'],
                         (sk_cx - 1, sk_cy - 1, 1, 1))
        pygame.draw.rect(surface, palette['shadow'],
                         (sk_cx + 1, sk_cy - 1, 1, 1))
        # Bright eye glow
        pygame.draw.rect(surface, palette['unholy_bright'],
                         (sk_cx - 1, sk_cy - 1, 1, 1))
        pygame.draw.rect(surface, palette['unholy_bright'],
                         (sk_cx + 1, sk_cy - 1, 1, 1))

        # Jaw
        pygame.draw.rect(surface, palette['unholy_darkest'],
                         (sk_cx - 2, sk_cy + 2, 5, 2))
        # Teeth
        for tooth_x in range(-2, 3, 1):
            pygame.draw.rect(surface, palette['unholy_light'],
                             (sk_cx + tooth_x, sk_cy + 2, 1, 1))


    # ═══════════════════════════════════════════════════════
    # SWORD (straight knight sword)
    # ═══════════════════════════════════════════════════════

    def _draw_sword(surface, x, y, angle, face, palette, size='small',
                    glowing=False):
        """Straight double-edged sword."""
        if size == 'small':
            blade_len = 10
            blade_w = 2
        elif size == 'big':
            blade_len = 13
            blade_w = 3
        else:  # huge
            blade_len = 16
            blade_w = 3

        cos_a = math.cos(angle) * face
        sin_a = math.sin(angle)
        perp_cos = -sin_a
        perp_sin = cos_a

        # ═══ HANDLE ═══
        handle_start_x = x - int(cos_a * 3)
        handle_start_y = y - int(sin_a * 3)
        handle_end_x = x + int(cos_a * 1)
        handle_end_y = y + int(sin_a * 1)

        _NS_undead._aaline(surface, palette['shadow_deep'],
                (handle_start_x + 1, handle_start_y + 1),
                (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_undead._aaline(surface, palette['leather_darkest'],
                (handle_start_x, handle_start_y),
                (handle_end_x, handle_end_y), 3)
        _NS_undead._aaline(surface, palette['leather_dark'],
                (handle_start_x, handle_start_y),
                (handle_end_x, handle_end_y), 2)

        # Pommel (gold ball)
        _NS_undead._aacircle(surface, palette['gold_darkest'],
                  (handle_start_x, handle_start_y), 2)
        _NS_undead._aacircle(surface, palette['gold_dark'],
                  (handle_start_x, handle_start_y), 1)
        pygame.draw.rect(surface, palette['gold_high'],
                         (handle_start_x, handle_start_y - 1, 1, 1))

        # ═══ CROSS-GUARD (gold) ═══
        guard_w = 4 if size == 'small' else 5
        guard_pts = [
            (int(x + perp_cos * guard_w), int(y + perp_sin * guard_w)),
            (int(x - perp_cos * guard_w), int(y - perp_sin * guard_w)),
            (int(x - perp_cos * guard_w + cos_a * 2),
             int(y - perp_sin * guard_w + sin_a * 2)),
            (int(x + perp_cos * guard_w + cos_a * 2),
             int(y + perp_sin * guard_w + sin_a * 2)),
        ]
        _NS_undead._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in guard_pts])
        _NS_undead._aapolygon(surface, palette['gold_darkest'], guard_pts)
        _NS_undead._aapolygon(surface, palette['gold_dark'], [
            (int(x + perp_cos * (guard_w - 1)),
             int(y + perp_sin * (guard_w - 1))),
            (int(x - perp_cos * (guard_w - 1)),
             int(y - perp_sin * (guard_w - 1))),
            (int(x - perp_cos * (guard_w - 1) + cos_a * 1),
             int(y - perp_sin * (guard_w - 1) + sin_a * 1)),
            (int(x + perp_cos * (guard_w - 1) + cos_a * 1),
             int(y + perp_sin * (guard_w - 1) + sin_a * 1)),
        ])
        _NS_undead._aapolygon(surface, palette['gold_mid'], [
            (int(x + perp_cos * (guard_w - 1)),
             int(y + perp_sin * (guard_w - 1))),
            (int(x - perp_cos * 1), int(y - perp_sin * 1)),
            (int(x + perp_cos * (guard_w - 1) + cos_a * 1),
             int(y + perp_sin * (guard_w - 1) + sin_a * 1)),
        ])
        pygame.draw.rect(surface, palette['gold_high'],
                         (int(x + perp_cos * (guard_w - 1)),
                          int(y + perp_sin * (guard_w - 1)), 1, 1))

        # ═══ BLADE (straight, double-edged) ═══
        blade_tip_x = x + int(cos_a * (blade_len + 2))
        blade_tip_y = y + int(sin_a * (blade_len + 2))
        blade_base_x = x + int(cos_a * 2)
        blade_base_y = y + int(sin_a * 2)

        # Outline
        _NS_undead._aapolygon(surface, palette['shadow'], [
            (int(blade_base_x + perp_cos * (blade_w + 1)),
             int(blade_base_y + perp_sin * (blade_w + 1))),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * (blade_w + 1)),
             int(blade_base_y - perp_sin * (blade_w + 1))),
        ])

        # Blade dark
        _NS_undead._aapolygon(surface, palette['blade_dark'], [
            (int(blade_base_x + perp_cos * blade_w),
             int(blade_base_y + perp_sin * blade_w)),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * blade_w),
             int(blade_base_y - perp_sin * blade_w)),
        ])

        # Blade mid
        _NS_undead._aapolygon(surface, palette['blade_mid'], [
            (int(blade_base_x + perp_cos * (blade_w - 1)),
             int(blade_base_y + perp_sin * (blade_w - 1))),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * (blade_w - 1)),
             int(blade_base_y - perp_sin * (blade_w - 1))),
        ])

        # Center fuller (groove)
        _NS_undead._aaline(surface, palette['blade_dark'],
                (blade_base_x, blade_base_y),
                (blade_tip_x, blade_tip_y), 1)

        # Edge highlights
        _NS_undead._aaline(surface, palette['blade_high'],
                (int(blade_base_x + perp_cos * (blade_w - 1)),
                 int(blade_base_y + perp_sin * (blade_w - 1))),
                (blade_tip_x, blade_tip_y), 1)
        _NS_undead._aaline(surface, palette['blade_shine'],
                (int(blade_base_x + perp_cos * (blade_w - 1)),
                 int(blade_base_y + perp_sin * (blade_w - 1))),
                (blade_tip_x, blade_tip_y), 1)

        # Sharp tip
        _NS_undead._aacircle(surface, palette['shine'], (blade_tip_x, blade_tip_y), 1)

        # Unholy glow when swinging
        if glowing:
            for r in (7, 5, 3):
                _NS_undead._blend_alpha(surface,
                             (*palette['unholy_mid'], max(0, 140 - r * 15)),
                             [
                                 (blade_tip_x - r, blade_tip_y - r),
                                 (blade_tip_x + r, blade_tip_y - r),
                                 (blade_tip_x + r, blade_tip_y + r),
                                 (blade_tip_x - r, blade_tip_y + r),
                             ])
            _NS_undead._aacircle(surface, palette['unholy_bright'],
                      (blade_tip_x, blade_tip_y), 2)


    def _draw_swing_blur(surface, sx, sy, face, progress, hand_x, hand_y,
                         palette):
        """Motion blur (purple tinted for unholy theme)."""
        for ghost_i in range(4):
            ghost_progress = progress - (ghost_i + 1) * 0.05
            if ghost_progress < 0.25:
                continue

            alpha = max(0, min(255, 100 - ghost_i * 22))
            if alpha <= 0:
                continue

            blur_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            _NS_undead._aacircle(blur_surf, (*palette['unholy_dark'], alpha),
                      (12, 12), 6)
            _NS_undead._aacircle(blur_surf, (*palette['unholy_mid'], alpha),
                      (12, 12), 4)
            _NS_undead._aacircle(blur_surf, (*palette['unholy_bright'], alpha // 2),
                      (12, 12), 2)
            surface.blit(blur_surf,
                         (hand_x - 12 - ghost_i * 2 * face, hand_y - 12))


    # ═══════════════════════════════════════════════════════
    # UNHOLY ARC (Purple crescent slash - matches reference)
    # ═══════════════════════════════════════════════════════

    def _draw_unholy_arc(surface, cx, cy, face, progress, palette):
        """Purple crescent swipe (match reference attack VFX)."""
        t = (progress - 0.30) / 0.42
        t = max(0.0, min(1.0, t))

        start_angle = math.radians(-100)
        end_angle = math.radians(55)
        current = start_angle + (end_angle - start_angle) * t

        center_x = cx + 8 * face
        center_y = cy - 5
        radius = 26

        for i in range(15):
            offset = i * 0.10
            seg_t = t - offset * 0.05
            if seg_t < 0:
                continue
            seg_angle = start_angle + (end_angle - start_angle) * seg_t

            alpha_fade = 1.0 - offset
            alpha = max(0, min(255, int(220 * alpha_fade * math.sin(t * math.pi))))
            if alpha <= 0:
                continue

            for r_offset, blade_color, w in [
                (0, palette['unholy_darkest'], 5),
                (0, palette['unholy_dark'], 4),
                (0, palette['unholy_mid'], 3),
                (0, palette['unholy_light'], 2),
                (0, palette['unholy_bright'], 1),
            ]:
                inner_r = radius - 5 + r_offset
                outer_r = radius + 4 + r_offset

                ix = center_x + int(math.cos(seg_angle) * inner_r) * face
                iy = center_y + int(math.sin(seg_angle) * inner_r)
                ox = center_x + int(math.cos(seg_angle) * outer_r) * face
                oy = center_y + int(math.sin(seg_angle) * outer_r)

                _NS_undead._blend_alpha(surface, (*blade_color, alpha), [
                    (ix, iy), (ox, oy),
                    (ox + 1, oy + 1), (ix + 1, iy + 1),
                ])
                _NS_undead._aaline(surface, (*blade_color, alpha),
                        (ix, iy), (ox, oy), w)

        # Leading bright tip
        lead_alpha = int(240 * math.sin(t * math.pi))
        lead_x = center_x + int(math.cos(current) * radius) * face
        lead_y = center_y + int(math.sin(current) * radius)
        _NS_undead._aacircle(surface, palette['unholy_bright'], (lead_x, lead_y), 4)
        _NS_undead._aacircle(surface, palette['unholy_hot'], (lead_x, lead_y), 2)
        _NS_undead._aacircle(surface, palette['shine'], (lead_x, lead_y), 1)


    def _draw_unholy_impact(surface, cx, cy, face, progress, palette):
        """Purple sparkle burst at swing peak (match reference)."""
        t = (progress - 0.48) / 0.14
        t = max(0.0, min(1.0, t))

        impact_x = cx + 24 * face
        impact_y = cy - 3

        # 4-pointed unholy star spikes
        star_r = int(6 + t * 10)
        alpha = int(240 * (1 - t))

        for angle_deg in [0, 45, 90, 135]:
            angle = math.radians(angle_deg)
            ox1 = impact_x + int(math.cos(angle) * star_r)
            oy1 = impact_y + int(math.sin(angle) * star_r)
            ox2 = impact_x - int(math.cos(angle) * star_r)
            oy2 = impact_y - int(math.sin(angle) * star_r)

            _NS_undead._aaline(surface, (*palette['unholy_dark'], alpha),
                    (ox1, oy1), (ox2, oy2), 3)
            _NS_undead._aaline(surface, (*palette['unholy_light'], alpha),
                    (ox1, oy1), (ox2, oy2), 2)
            _NS_undead._aaline(surface, (*palette['unholy_hot'], alpha),
                    (ox1, oy1), (ox2, oy2), 1)

        # Central bright core
        core_alpha = int(255 * (1 - t))
        _NS_undead._aacircle(surface, (*palette['unholy_bright'], core_alpha),
                  (impact_x, impact_y), 4)
        _NS_undead._aacircle(surface, (*palette['unholy_hot'], core_alpha),
                  (impact_x, impact_y), 2)
        _NS_undead._aacircle(surface, palette['unholy_white'], (impact_x, impact_y),
                  max(1, int(1 + (1 - t))))


    # ═══════════════════════════════════════════════════════
    # UNHOLY AURA (Ground circle, floating souls, sparkles)
    # ═══════════════════════════════════════════════════════

    def _draw_unholy_ground_aura(surface, x, y, radius, timer, palette):
        """Purple circle aura on ground."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_w = radius * 5
        aura_h = int(radius * 1.5)
        aura_surf = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)

        # Outer ring
        for r in range(radius + 2, 3, -2):
            alpha = int((radius + 2 - r) * 6 * pulse)
            alpha = max(0, min(180, alpha))
            if alpha > 0:
                pygame.draw.ellipse(aura_surf,
                                    (*palette['unholy_dark'], alpha),
                                    (aura_w // 2 - r * 2,
                                     aura_h // 2 - r // 2,
                                     r * 4, r))

        # Bright inner ring outline
        inner_alpha = int(200 * pulse)
        pygame.draw.ellipse(aura_surf,
                            (*palette['unholy_bright'], inner_alpha),
                            (aura_w // 2 - radius - 2,
                             aura_h // 2 - radius // 3,
                             radius * 2 + 4, int(radius * 0.7)), 1)
        pygame.draw.ellipse(aura_surf,
                            (*palette['unholy_light'], inner_alpha),
                            (aura_w // 2 - radius,
                             aura_h // 2 - radius // 4,
                             radius * 2, radius // 2), 1)

        surface.blit(aura_surf, (x - aura_w // 2, y - aura_h // 2))


    def _draw_aura_sparkles(surface, x, y, radius, timer, palette):
        """Purple sparkles rising from feet."""
        for i in range(6):
            phase = (timer * 0.02 + i * 0.16) % 1.0
            # Circle around body
            angle = i * math.pi * 2 / 6 + timer * 0.015
            base_x = x + int(math.cos(angle) * radius * 1.3)

            # Rise
            rise = int(phase * (radius * 2 + 6))
            py = y + radius - rise + int(math.sin(timer * 0.05 + i) * 2)

            alpha_fade = math.sin(phase * math.pi)
            alpha = max(0, min(255, int(200 * alpha_fade)))
            if alpha <= 0:
                continue

            size = max(1, int(2 * alpha_fade))

            _NS_undead._aacircle(surface, (*palette['unholy_dark'], alpha),
                      (base_x, py), size + 1)
            _NS_undead._aacircle(surface, (*palette['unholy_bright'], alpha),
                      (base_x, py), size)
            _NS_undead._aacircle(surface, (*palette['unholy_hot'], alpha),
                      (base_x, py), max(1, size - 1))


    def _draw_floating_souls(surface, x, y, radius, timer, level, palette):
        """Small purple skull souls floating around undead (aura visual)."""
        # More souls for higher level
        soul_count = 1 + level  # 2 at lvl 1, up to 6 at lvl 5

        for i in range(soul_count):
            phase = timer * 0.03 + i * (2 * math.pi / soul_count)
            # Orbit
            orbit_r = radius + 6
            sx = x + int(math.cos(phase) * orbit_r)
            sy = y - 8 + int(math.sin(phase * 1.3) * 6 - 2)

            _NS_undead._draw_soul_skull(surface, sx, sy, timer + i * 10, palette)


    def _draw_soul_skull(surface, cx, cy, timer, palette):
        """A tiny floating purple skull."""
        pulse = math.sin(timer * 0.1) * 0.2 + 0.8

        # Glow behind skull
        glow_r = int(5 * pulse)
        if glow_r > 0:
            glow_surf = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
            for gr in range(glow_r, 0, -1):
                alpha = (glow_r - gr) * 30
                alpha = max(0, min(150, alpha))
                pygame.draw.circle(glow_surf, (*palette['unholy_mid'], alpha),
                                   (glow_r * 2, glow_r * 2), gr)
            surface.blit(glow_surf, (cx - glow_r * 2, cy - glow_r * 2))

        # Skull head
        _NS_undead._aacircle(surface, palette['unholy_darkest'], (cx, cy), 3)
        _NS_undead._aacircle(surface, palette['unholy_dark'], (cx, cy), 2)
        _NS_undead._aacircle(surface, palette['unholy_light'], (cx - 1, cy - 1), 1)

        # Eye sockets (dark)
        pygame.draw.rect(surface, palette['shadow'], (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, palette['shadow'], (cx + 1, cy - 1, 1, 1))
        # Bright eye glow
        pygame.draw.rect(surface, palette['unholy_hot'],
                         (cx - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, palette['unholy_hot'],
                         (cx + 1, cy - 1, 1, 1))

        # Small jaw
        pygame.draw.rect(surface, palette['unholy_darkest'], (cx - 1, cy + 1, 3, 1))
        pygame.draw.rect(surface, palette['unholy_light'], (cx, cy + 1, 1, 1))

        # Wispy trail below skull
        for i in range(3):
            wisp_y = cy + 3 + i * 2
            wisp_alpha = 150 - i * 40
            wisp_alpha = max(0, wisp_alpha)
            wisp_surf = pygame.Surface((6, 4), pygame.SRCALPHA)
            pygame.draw.ellipse(wisp_surf,
                                (*palette['unholy_mid'], wisp_alpha),
                                (0, 0, 6, 4))
            surface.blit(wisp_surf, (cx - 3, wisp_y))


    # ═══════════════════════════════════════════════════════
    # DEATH KNIGHT AURA (Lvl 5)
    # ═══════════════════════════════════════════════════════

    def _draw_death_knight_aura(surface, x, y, timer, palette):
        """Big pulsing purple aura for Death Knight."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_r = 26
        aura_surf = pygame.Surface((aura_r * 3, aura_r * 3), pygame.SRCALPHA)

        for r in range(aura_r, 3, -2):
            alpha = int((aura_r - r) * 4 * pulse)
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                _NS_undead._aacircle(aura_surf, (*palette['unholy_mid'], alpha),
                          (aura_r * 3 // 2, aura_r * 3 // 2), r)

        surface.blit(aura_surf,
                     (x - aura_r * 3 // 2, y - aura_r * 3 // 2))

# ====================================================================
# dark_rider.py
# ====================================================================
class _NS_dark_rider:
    """Namespace dark_rider - isi asli tidak diubah."""

    # ================================
    # minions/dark_rider.py
    # HD Dark Rider - The Cursed Cavalry
    # Undead cavalry with cursed steed + Death Charge passive
    # ================================



    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')
    HAS_AALINES = hasattr(pygame.draw, 'aalines')


    def _clamp_color(color):
        if len(color) == 3:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
            )
        elif len(color) == 4:
            return (
                max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))),
            )
        return color


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_dark_rider._clamp_color(color)
        if _NS_dark_rider.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aaline(surface, color, start, end, width=1):
        color = _NS_dark_rider._clamp_color(color)
        if width == 1 and _NS_dark_rider.HAS_AALINES:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.line(surface, color, start, end, width)
        except (TypeError, ValueError):
            pass


    def _aapolygon(surface, color, points):
        color = _NS_dark_rider._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    def _blend_alpha(surface, color, rect_pts):
        if len(rect_pts) < 3:
            return
        xs = [p[0] for p in rect_pts]
        ys = [p[1] for p in rect_pts]
        minx, miny = min(xs) - 2, min(ys) - 2
        maxx, maxy = max(xs) + 2, max(ys) + 2
        w, h = maxx - minx, maxy - miny
        if w <= 0 or h <= 0:
            return
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        shifted = [(p[0] - minx, p[1] - miny) for p in rect_pts]
        pygame.draw.polygon(tmp, _NS_dark_rider._clamp_color(color), shifted)
        surface.blit(tmp, (minx, miny))


    # ═══════════════════════════════════════════════════════
    # PALETTE - Dark Rider
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            return {
                # Dark armor (blue-black steel)
                'armor_darkest': (12, 15, 25),
                'armor_dark': (30, 38, 55),
                'armor_mid': (60, 72, 100),
                'armor_light': (110, 130, 170),
                'armor_high': (170, 190, 225),
                'armor_shine': (225, 235, 255),

                # Horse coat (dark black-purple)
                'horse_darkest': (12, 8, 20),
                'horse_dark': (28, 20, 42),
                'horse_mid': (55, 42, 78),
                'horse_light': (95, 78, 128),
                'horse_high': (145, 128, 175),

                # Leather (dark)
                'leather_darkest': (18, 12, 10),
                'leather_dark': (40, 28, 20),
                'leather_mid': (72, 52, 32),
                'leather_light': (110, 82, 52),

                # Cape / mane (dark purple)
                'cloth_darkest': (25, 10, 45),
                'cloth_dark': (52, 22, 88),
                'cloth_mid': (90, 42, 145),
                'cloth_light': (140, 78, 195),

                # Blade
                'blade_dark': (48, 55, 68),
                'blade_mid': (108, 122, 142),
                'blade_light': (180, 195, 215),
                'blade_high': (230, 240, 255),
                'blade_shine': (255, 255, 255),

                # Gold accents
                'gold_darkest': (85, 55, 12),
                'gold_dark': (145, 105, 25),
                'gold_mid': (210, 160, 55),
                'gold_light': (245, 205, 95),
                'gold_high': (255, 235, 160),

                # Bone (horns, teeth)
                'bone_dark': (95, 82, 70),
                'bone_mid': (155, 140, 120),
                'bone_light': (210, 195, 175),
                'bone_high': (245, 235, 215),

                # CURSE FLAME (purple magic - signature!)
                'flame_darkest': (30, 8, 55),
                'flame_dark': (70, 22, 115),
                'flame_mid': (125, 50, 185),
                'flame_light': (175, 100, 230),
                'flame_bright': (215, 155, 250),
                'flame_hot': (245, 215, 255),
                'flame_white': (255, 245, 255),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 5, 10),
            }
        else:
            return {
                'armor_darkest': (15, 12, 15),
                'armor_dark': (38, 32, 35),
                'armor_mid': (70, 60, 65),
                'armor_light': (125, 108, 115),
                'armor_high': (185, 170, 175),
                'armor_shine': (225, 215, 220),

                'horse_darkest': (15, 8, 12),
                'horse_dark': (32, 18, 25),
                'horse_mid': (60, 38, 48),
                'horse_light': (105, 75, 90),
                'horse_high': (155, 125, 140),

                'leather_darkest': (16, 10, 8),
                'leather_dark': (38, 25, 15),
                'leather_mid': (68, 48, 28),
                'leather_light': (105, 78, 48),

                'cloth_darkest': (30, 8, 12),
                'cloth_dark': (60, 20, 25),
                'cloth_mid': (105, 40, 50),
                'cloth_light': (155, 75, 85),

                'blade_dark': (42, 42, 52),
                'blade_mid': (95, 95, 110),
                'blade_light': (160, 160, 180),
                'blade_high': (215, 215, 230),
                'blade_shine': (248, 248, 255),

                'gold_darkest': (65, 42, 10),
                'gold_dark': (110, 78, 20),
                'gold_mid': (165, 120, 40),
                'gold_light': (210, 170, 75),
                'gold_high': (240, 208, 130),

                'bone_dark': (85, 72, 60),
                'bone_mid': (145, 128, 108),
                'bone_light': (200, 185, 165),
                'bone_high': (235, 225, 205),

                'flame_darkest': (35, 8, 55),
                'flame_dark': (80, 22, 120),
                'flame_mid': (135, 55, 190),
                'flame_light': (180, 105, 232),
                'flame_bright': (218, 160, 250),
                'flame_hot': (246, 218, 255),
                'flame_white': (255, 240, 255),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (5, 3, 5),
            }


    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_dark_rider(surface, minion, x, y):
        """Draw dark rider - CACHED"""
        from minions.base_renderer import cached_minion_draw
        cached_minion_draw(surface, minion, x, y, _NS_dark_rider._draw_dark_rider_full)


    def _draw_dark_rider_full(surface, minion, x, y):
        """Original dark rider render."""
        palette = _NS_dark_rider._get_palette(minion.team)

        walk_phase = minion.walk_cycle
        is_running = minion.is_moving
        anim_time = minion.anim_time

        # Death Charge active (after attack for 2 sec = 120 frames)
        death_charge_active = getattr(minion, 'death_charge_active', False)

        # Attack anim
        attack_progress = 0
        is_attacking = False
        if minion.attack_anim_timer > 0:
            attack_progress = 1.0 - (minion.attack_anim_timer /
                                      minion.attack_anim_max)
            is_attacking = True

        # Body bob (subtle - horse gallop)
        if is_running:
            body_bob = int(math.sin(walk_phase * 2.5) * 2)
        else:
            body_bob = int(math.sin(anim_time * 0.05) * 1)

        # Attack lunge forward
        attack_offset_x = 0
        if is_attacking:
            if attack_progress < 0.25:
                p = attack_progress / 0.25
                attack_offset_x = int(-p * 3) * minion.direction
            elif attack_progress < 0.55:
                p = (attack_progress - 0.25) / 0.30
                ease = p * p * (3 - 2 * p)
                attack_offset_x = int((-3 + ease * 14)) * minion.direction
            else:
                p = (attack_progress - 0.55) / 0.45
                ease = 1 - (1 - p) * (1 - p)
                attack_offset_x = int((11 - ease * 11)) * minion.direction

        # Spawn scale
        spawn_scale = 1.0
        if minion.spawn_anim > 0:
            spawn_scale = 1.0 - (minion.spawn_anim / 20.0) * 0.5
            spawn_scale = max(0.3, spawn_scale)

        draw_x = x + attack_offset_x
        draw_y = y + body_bob

        # Ground shadow (BIG - horse takes lots of space)
        _NS_dark_rider._draw_ground_shadow(surface, x, y + minion.radius + 8, minion.radius)

        # Cursed flame aura on ground (behind body - always visible)
        _NS_dark_rider._draw_curse_ground_aura(surface, x, y + minion.radius + 6,
                                minion.radius, anim_time, palette)

        # DEATH CHARGE speed trail (when active)
        if death_charge_active or is_running:
            intensity = 1.5 if death_charge_active else 0.8
            _NS_dark_rider._draw_speed_trail(surface, x, y, minion.radius, minion.direction,
                              anim_time, palette, intensity)

        # Slow FX
        if minion.slow_timer > 0:
            draw_slow_effect(surface, x, y, minion.radius, anim_time)

        # Main body per level (horse + rider)
        level = minion.nexus_level
        if level == 1:
            _NS_dark_rider._draw_rider_lvl1(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        elif level == 2:
            _NS_dark_rider._draw_rider_lvl2(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        elif level == 3:
            _NS_dark_rider._draw_rider_lvl3(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        elif level == 4:
            _NS_dark_rider._draw_rider_lvl4(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)
        else:
            _NS_dark_rider._draw_rider_lvl5(surface, minion, draw_x, draw_y,
                             walk_phase, attack_progress,
                             is_running, is_attacking, palette)

        # HOOF FLAMES (purple - signature, always active)
        _NS_dark_rider._draw_hoof_flames(surface, draw_x, draw_y + minion.radius,
                          minion.radius, minion.direction, anim_time, palette,
                          is_running or death_charge_active)

        # Champion aura for lvl 5
        if level >= 5:
            _NS_dark_rider._draw_dread_lord_aura(surface, x, y, anim_time, palette)

        # Attack swing arc (purple curved slash - match reference)
        if is_attacking and 0.28 <= attack_progress <= 0.72:
            _NS_dark_rider._draw_curse_arc(surface, draw_x, draw_y, minion.direction,
                            attack_progress, palette)

        # Impact sparkle at peak
        if is_attacking and 0.48 <= attack_progress <= 0.63:
            _NS_dark_rider._draw_curse_impact(surface, draw_x, draw_y, minion.direction,
                               attack_progress, palette)

        # Death Charge icon above head (when active)
        if death_charge_active:
            _NS_dark_rider._draw_death_charge_icon(surface, x, y - minion.radius - 30,
                                     anim_time, palette)

        # Slash effects
        if minion.slash_effects:
            draw_slash_effects(surface, draw_x, draw_y, minion.slash_effects)


        # HP bar
        bar_w = minion.radius * 2 + 12
        by = y - minion.radius - 22
        draw_hp_bar(surface, x, by, bar_w,
                    minion.hp / minion.max_hp, minion.team)

        # Level stars
        if minion.nexus_level >= 3:
            for i in range(minion.nexus_level - 2):
                star_x = x - 5 + i * 5
                star_y = by - 5
                _NS_dark_rider._aacircle(surface, palette['flame_light'], (star_x, star_y), 2)
                pygame.draw.rect(surface, palette['shine'],
                                 (star_x, star_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # GROUND SHADOW & GROUND AURA
    # ═══════════════════════════════════════════════════════

    def _draw_ground_shadow(surface, x, y, radius):
        """Big elongated shadow for horse+rider."""
        shadow_surf = pygame.Surface((radius * 8, 14), pygame.SRCALPHA)
        for r in range(7, 0, -1):
            alpha = (7 - r) * 22
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha),
                                (7 - r, 7 - r,
                                 radius * 8 - (7 - r) * 2, r * 2))
        surface.blit(shadow_surf, (x - radius * 4, y - 7))


    def _draw_curse_ground_aura(surface, x, y, radius, timer, palette):
        """Faint purple aura circle beneath rider."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_w = radius * 7
        aura_h = int(radius * 1.5)
        aura_surf = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)

        for r in range(radius + 4, 3, -3):
            alpha = int((radius + 4 - r) * 4 * pulse)
            alpha = max(0, min(120, alpha))
            if alpha > 0:
                pygame.draw.ellipse(aura_surf,
                                    (*palette['flame_darkest'], alpha),
                                    (aura_w // 2 - r * 3,
                                     aura_h // 2 - r // 2,
                                     r * 6, r))

        # Bright inner ring
        inner_alpha = int(140 * pulse)
        pygame.draw.ellipse(aura_surf,
                            (*palette['flame_mid'], inner_alpha),
                            (aura_w // 2 - radius * 2,
                             aura_h // 2 - radius // 3,
                             radius * 4, int(radius * 0.7)), 1)

        surface.blit(aura_surf, (x - aura_w // 2, y - aura_h // 2))


    # ═══════════════════════════════════════════════════════
    # HOOF FLAMES (purple flames under horse hooves)
    # ═══════════════════════════════════════════════════════

    def _draw_hoof_flames(surface, cx, cy, radius, face, timer, palette,
                          intense):
        """Purple curse flames under each hoof."""
        # 4 hoof positions
        hoof_positions = [
            (-radius - 2, 0),      # back-back
            (-radius + 4, 2),      # back-front
            (radius - 4, 2),       # front-back
            (radius + 2, 0),       # front-front
        ]

        flame_strength = 1.4 if intense else 1.0

        for hx_off, hy_off in hoof_positions:
            hx = cx + hx_off
            hy = cy + hy_off

            # Multiple flame layers
            for i in range(4):
                phase_offset = i * 0.3
                flame_phase = (timer * 0.15 + phase_offset + hx * 0.05) % 1.0

                # Flame height animates
                flame_h = int((6 + math.sin(timer * 0.2 + i) * 2) * flame_strength)
                flame_w = 4

                # Wavy flame
                waver = int(math.sin(timer * 0.3 + i * 0.7) * 1)

                # Flame outer glow
                flame_surf = pygame.Surface((flame_w * 3, flame_h * 2),
                                             pygame.SRCALPHA)

                # Outer flame
                _NS_dark_rider._aapolygon(flame_surf, palette['flame_dark'], [
                    (flame_w * 3 // 2 - flame_w + waver, flame_h * 2 - 1),
                    (flame_w * 3 // 2 + waver, flame_h * 2 - flame_h),
                    (flame_w * 3 // 2 + flame_w + waver, flame_h * 2 - 1),
                ])
                # Mid flame
                _NS_dark_rider._aapolygon(flame_surf, palette['flame_mid'], [
                    (flame_w * 3 // 2 - flame_w + 1 + waver, flame_h * 2 - 1),
                    (flame_w * 3 // 2 + waver, flame_h * 2 - flame_h + 1),
                    (flame_w * 3 // 2 + flame_w - 1 + waver, flame_h * 2 - 1),
                ])
                # Bright inner
                _NS_dark_rider._aapolygon(flame_surf, palette['flame_bright'], [
                    (flame_w * 3 // 2 - 1 + waver, flame_h * 2 - 1),
                    (flame_w * 3 // 2 + waver, flame_h * 2 - flame_h + 2),
                    (flame_w * 3 // 2 + 1 + waver, flame_h * 2 - 1),
                ])
                # Hot core
                pygame.draw.line(flame_surf, palette['flame_hot'],
                                 (flame_w * 3 // 2 + waver, flame_h * 2 - 1),
                                 (flame_w * 3 // 2 + waver,
                                  flame_h * 2 - flame_h + 3), 1)

                surface.blit(flame_surf,
                             (hx - flame_w * 3 // 2, hy - flame_h * 2 + 3))


    # ═══════════════════════════════════════════════════════
    # SPEED TRAIL (Death Charge visual)
    # ═══════════════════════════════════════════════════════

    def _draw_speed_trail(surface, cx, cy, radius, face, timer, palette,
                          intensity=1.0):
        """Purple speed trail streaks behind rider."""
        for i in range(6):
            offset = (i + 1) * 4
            trail_x = cx - offset * face
            trail_y = cy + int(math.sin(timer * 0.2 + i) * 2)

            alpha = int(max(0, (140 - i * 20) * intensity))
            if alpha <= 0:
                continue

            # Streak
            streak_len = int((10 + i * 3) * intensity)
            streak_w = max(1, int((4 - i // 2) * intensity))

            streak_surf = pygame.Surface((streak_len + 4, streak_w * 2 + 4),
                                          pygame.SRCALPHA)

            for r_off in range(3):
                color_layer = [palette['flame_dark'],
                              palette['flame_mid'],
                              palette['flame_light']][r_off]
                # Clamp 0..255. Tanpa ini, saat intensity < 1.0
                # (is_running tanpa death charge) nilai bisa negatif
                # -> ValueError: invalid color argument.
                layer_alpha = max(0, min(255, alpha - r_off * 20))
                if layer_alpha <= 0:
                    continue
                pygame.draw.rect(streak_surf,
                                 (*color_layer, layer_alpha),
                                 (2, streak_w + 2 - streak_w // 2 + r_off,
                                  streak_len, max(1, streak_w - r_off)))

            # Bright center
            pygame.draw.rect(streak_surf,
                             (*palette['flame_bright'],
                              max(0, min(255, alpha))),
                             (2, streak_w + 2, streak_len, 1))

            surface.blit(streak_surf,
                         (trail_x - (streak_len + 4) // 2 if face < 0 else trail_x - 2,
                          trail_y - streak_w - 2))


    # ═══════════════════════════════════════════════════════
    # LEVEL 1: SCOUT RIDER (basic)
    # ═══════════════════════════════════════════════════════

    def _draw_rider_lvl1(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        # Horse first
        _NS_dark_rider._draw_horse(surface, x, y + 4, face, walk_phase, is_running, palette,
                    barding=False, has_horn=False)

        # Rider on top
        rider_y = y - 12  # Rider sits above horse body
        _NS_dark_rider._draw_cape(surface, x, rider_y - 2, walk_phase, palette, size='small')
        _NS_dark_rider._draw_rider_body_light(surface, x, rider_y, face, palette, hurt)
        _NS_dark_rider._draw_rider_head(surface, x, rider_y - 12, face, palette, hurt,
                         has_horns='small', has_crown=False)
        _NS_dark_rider._draw_rider_weapon(surface, x + 8 * face, rider_y - 2, face,
                           walk_phase, attack_progress, is_running,
                           is_attacking, palette, weapon='sword_small')


    # ═══════════════════════════════════════════════════════
    # LEVEL 2: DEATH RIDER
    # ═══════════════════════════════════════════════════════

    def _draw_rider_lvl2(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        _NS_dark_rider._draw_horse(surface, x, y + 4, face, walk_phase, is_running, palette,
                    barding=False, has_horn=False)

        rider_y = y - 12
        _NS_dark_rider._draw_cape(surface, x, rider_y - 2, walk_phase, palette, size='medium')
        _NS_dark_rider._draw_rider_body_armored(surface, x, rider_y, face, palette, hurt,
                                  has_emblem=False)
        _NS_dark_rider._draw_rider_head(surface, x, rider_y - 12, face, palette, hurt,
                         has_horns='medium', has_crown=False)
        _NS_dark_rider._draw_rider_weapon(surface, x + 8 * face, rider_y - 2, face,
                           walk_phase, attack_progress, is_running,
                           is_attacking, palette, weapon='sword_medium')


    # ═══════════════════════════════════════════════════════
    # LEVEL 3: BLACK KNIGHT (+horse barding)
    # ═══════════════════════════════════════════════════════

    def _draw_rider_lvl3(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        _NS_dark_rider._draw_horse(surface, x, y + 4, face, walk_phase, is_running, palette,
                    barding=True, has_horn=False)

        rider_y = y - 12
        _NS_dark_rider._draw_cape(surface, x, rider_y - 2, walk_phase, palette, size='medium')
        _NS_dark_rider._draw_rider_body_armored(surface, x, rider_y, face, palette, hurt,
                                  has_emblem=True)
        _NS_dark_rider._draw_shoulder_spikes(surface, x - 8, rider_y - 4, palette)
        _NS_dark_rider._draw_rider_head(surface, x, rider_y - 12, face, palette, hurt,
                         has_horns='big', has_crown=False)
        _NS_dark_rider._draw_rider_weapon(surface, x + 8 * face, rider_y - 2, face,
                           walk_phase, attack_progress, is_running,
                           is_attacking, palette, weapon='sword_big')


    # ═══════════════════════════════════════════════════════
    # LEVEL 4: DREAD RIDER (+horse horn +both pauldrons)
    # ═══════════════════════════════════════════════════════

    def _draw_rider_lvl4(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        _NS_dark_rider._draw_horse(surface, x, y + 4, face, walk_phase, is_running, palette,
                    barding=True, has_horn=True)

        rider_y = y - 12
        _NS_dark_rider._draw_cape(surface, x, rider_y - 2, walk_phase, palette, size='big')
        _NS_dark_rider._draw_rider_body_armored(surface, x, rider_y, face, palette, hurt,
                                  has_emblem=True, ornate=True)
        _NS_dark_rider._draw_shoulder_spikes(surface, x - 8, rider_y - 4, palette)
        _NS_dark_rider._draw_shoulder_spikes(surface, x + 8, rider_y - 4, palette, mirror=True)
        _NS_dark_rider._draw_rider_head(surface, x, rider_y - 12, face, palette, hurt,
                         has_horns='big', has_crown=False)
        _NS_dark_rider._draw_rider_weapon(surface, x + 8 * face, rider_y - 2, face,
                           walk_phase, attack_progress, is_running,
                           is_attacking, palette, weapon='sword_big')


    # ═══════════════════════════════════════════════════════
    # LEVEL 5: DREAD LORD (crown + huge sword + full ornate)
    # ═══════════════════════════════════════════════════════

    def _draw_rider_lvl5(surface, minion, x, y, walk_phase,
                         attack_progress, is_running, is_attacking, palette):
        face = minion.direction
        hurt = minion.hurt_flash_timer > 0

        _NS_dark_rider._draw_horse(surface, x, y + 4, face, walk_phase, is_running, palette,
                    barding=True, has_horn=True, ornate=True)

        rider_y = y - 12
        _NS_dark_rider._draw_cape(surface, x, rider_y - 2, walk_phase, palette, size='huge')
        _NS_dark_rider._draw_rider_body_armored(surface, x, rider_y, face, palette, hurt,
                                  has_emblem=True, ornate=True,
                                  has_gold_trim=True)
        _NS_dark_rider._draw_shoulder_spikes(surface, x - 8, rider_y - 4, palette)
        _NS_dark_rider._draw_shoulder_spikes(surface, x + 8, rider_y - 4, palette, mirror=True)
        _NS_dark_rider._draw_rider_head(surface, x, rider_y - 12, face, palette, hurt,
                         has_horns='huge', has_crown=True)
        _NS_dark_rider._draw_rider_weapon(surface, x + 8 * face, rider_y - 2, face,
                           walk_phase, attack_progress, is_running,
                           is_attacking, palette, weapon='sword_huge')


    # ═══════════════════════════════════════════════════════
    # HORSE (side-view profile)
    # ═══════════════════════════════════════════════════════

    def _draw_horse(surface, cx, cy, face, phase, is_running, palette,
                    barding=False, has_horn=False, ornate=False):
        """Cursed steed - dark horse in profile view."""
        # Gallop bob
        if is_running:
            gallop = math.sin(phase * 2.5) * 2
        else:
            gallop = 0

        # ═══ HORSE BODY (torso) ═══
        body_w = 22
        body_h = 12
        bx = cx
        by = cy - int(gallop * 0.5)

        # Body shadow
        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'], [
            (bx - body_w // 2 + 1, by - body_h // 2 + 1),
            (bx + body_w // 2 + 2, by - body_h // 2 + 2),
            (bx + body_w // 2 + 2, by + body_h // 2 + 2),
            (bx - body_w // 2 + 1, by + body_h // 2 + 2),
        ])

        # Main body (elongated ellipse)
        body_pts = [
            (bx - body_w // 2 - 2, by - 2),           # rear top
            (bx - body_w // 2, by - body_h // 2),     # rear upper
            (bx + body_w // 2 - 2, by - body_h // 2), # front upper
            (bx + body_w // 2 + 2, by),               # front chest
            (bx + body_w // 2, by + body_h // 2),     # belly front
            (bx - body_w // 2 + 2, by + body_h // 2 + 1),  # belly rear
            (bx - body_w // 2 - 1, by + 2),           # rear bottom
        ]
        _NS_dark_rider._aapolygon(surface, palette['horse_darkest'], body_pts)
        _NS_dark_rider._aapolygon(surface, palette['horse_dark'], [
            (bx - body_w // 2 - 1, by - 1),
            (bx - body_w // 2 + 1, by - body_h // 2 + 1),
            (bx + body_w // 2 - 3, by - body_h // 2 + 1),
            (bx + body_w // 2 + 1, by + 1),
            (bx + body_w // 2 - 1, by + body_h // 2 - 1),
            (bx - body_w // 2 + 3, by + body_h // 2),
        ])
        _NS_dark_rider._aapolygon(surface, palette['horse_mid'], [
            (bx - body_w // 2, by),
            (bx - body_w // 2 + 2, by - body_h // 2 + 2),
            (bx + body_w // 2 - 4, by - body_h // 2 + 2),
            (bx + body_w // 2 - 1, by),
            (bx + body_w // 2 - 2, by + body_h // 2 - 2),
            (bx - body_w // 2 + 4, by + body_h // 2 - 1),
        ])
        # Highlight top
        _NS_dark_rider._aaline(surface, palette['horse_light'],
                (bx - body_w // 2 + 2, by - body_h // 2 + 2),
                (bx + body_w // 2 - 4, by - body_h // 2 + 2), 1)

        # ═══ HORSE HEAD (front, facing 'face' direction) ═══
        head_x = bx + int((body_w // 2 + 4) * face)
        head_y = by - 2

        # Neck
        _NS_dark_rider._aaline(surface, palette['horse_darkest'],
                (bx + int((body_w // 2 - 2) * face), by - body_h // 2 + 1),
                (head_x - int(4 * face), head_y + 2), 6)
        _NS_dark_rider._aaline(surface, palette['horse_dark'],
                (bx + int((body_w // 2 - 2) * face), by - body_h // 2 + 1),
                (head_x - int(4 * face), head_y + 2), 5)
        _NS_dark_rider._aaline(surface, palette['horse_mid'],
                (bx + int((body_w // 2 - 2) * face), by - body_h // 2 + 1),
                (head_x - int(4 * face), head_y + 2), 3)

        # Head shape (elongated)
        head_pts = [
            (head_x - 3 * face, head_y - 3),
            (head_x + 4 * face, head_y - 2),
            (head_x + 6 * face, head_y),
            (head_x + 5 * face, head_y + 3),
            (head_x - 2 * face, head_y + 3),
            (head_x - 4 * face, head_y + 1),
        ]
        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_dark_rider._aapolygon(surface, palette['horse_darkest'], head_pts)
        _NS_dark_rider._aapolygon(surface, palette['horse_dark'], [
            (head_x - 2 * face, head_y - 2),
            (head_x + 3 * face, head_y - 1),
            (head_x + 5 * face, head_y),
            (head_x + 4 * face, head_y + 2),
            (head_x - 2 * face, head_y + 2),
            (head_x - 3 * face, head_y + 1),
        ])
        _NS_dark_rider._aapolygon(surface, palette['horse_mid'], [
            (head_x - 1 * face, head_y - 1),
            (head_x + 2 * face, head_y),
            (head_x + 4 * face, head_y + 1),
            (head_x - 1 * face, head_y + 1),
        ])
        _NS_dark_rider._aaline(surface, palette['horse_light'],
                (head_x - 1 * face, head_y - 1),
                (head_x + 3 * face, head_y), 1)

        # Horse mane (dark purple flowing on top of neck)
        for i in range(3):
            mane_x = bx + int((body_w // 2 - 4 + i * 3) * face)
            mane_y = by - body_h // 2 - 1
            mane_sway = int(math.sin(phase * 2 + i) * 1)
            _NS_dark_rider._aapolygon(surface, palette['cloth_darkest'], [
                (mane_x - 2, mane_y),
                (mane_x + mane_sway, mane_y - 4 - i),
                (mane_x + 2, mane_y),
            ])
            _NS_dark_rider._aapolygon(surface, palette['cloth_dark'], [
                (mane_x - 1, mane_y),
                (mane_x + mane_sway, mane_y - 3 - i),
                (mane_x + 1, mane_y),
            ])
            _NS_dark_rider._aaline(surface, palette['cloth_mid'],
                    (mane_x, mane_y),
                    (mane_x + mane_sway, mane_y - 3 - i), 1)

        # Horse eye (glowing purple - like undead)
        eye_x = head_x + int(2 * face)
        eye_y = head_y
        _NS_dark_rider._aacircle(surface, palette['shadow'], (eye_x, eye_y), 1)
        pygame.draw.rect(surface, palette['flame_bright'], (eye_x, eye_y, 1, 1))

        # Horse ear
        _NS_dark_rider._aapolygon(surface, palette['horse_darkest'], [
            (head_x - 3 * face, head_y - 3),
            (head_x - 4 * face, head_y - 6),
            (head_x - 1 * face, head_y - 3),
        ])
        _NS_dark_rider._aapolygon(surface, palette['horse_dark'], [
            (head_x - 3 * face, head_y - 3),
            (head_x - 3 * face, head_y - 5),
            (head_x - 1 * face, head_y - 3),
        ])

        # Horse nose/muzzle detail
        pygame.draw.rect(surface, palette['shadow'],
                         (head_x + int(5 * face), head_y + 1, 1, 1))

        # Mouth line
        _NS_dark_rider._aaline(surface, palette['shadow'],
                (head_x + int(3 * face), head_y + 2),
                (head_x + int(5 * face), head_y + 2), 1)

        # ═══ HORN on horse forehead (lvl 4+ - demon horse) ═══
        if has_horn:
            horn_x = head_x - int(1 * face)
            horn_y = head_y - 3
            # Curved horn going back
            _NS_dark_rider._aapolygon(surface, palette['shadow_deep'], [
                (horn_x, horn_y),
                (horn_x - int(4 * face), horn_y - 6),
                (horn_x - int(2 * face), horn_y),
            ])
            _NS_dark_rider._aapolygon(surface, palette['bone_dark'], [
                (horn_x, horn_y),
                (horn_x - int(3 * face), horn_y - 5),
                (horn_x - int(1 * face), horn_y),
            ])
            _NS_dark_rider._aapolygon(surface, palette['bone_mid'], [
                (horn_x, horn_y),
                (horn_x - int(2 * face), horn_y - 4),
                (horn_x, horn_y),
            ])
            _NS_dark_rider._aaline(surface, palette['bone_light'],
                    (horn_x, horn_y),
                    (horn_x - int(3 * face), horn_y - 5), 1)
            pygame.draw.rect(surface, palette['bone_high'],
                             (horn_x - int(3 * face), horn_y - 5, 1, 1))

        # ═══ HORSE TAIL (back of body) ═══
        tail_x = bx - int((body_w // 2 + 2) * face)
        for i in range(5):
            wave = math.sin(phase * 1.5 + i * 0.3) * 2
            tx = tail_x - int(i * 1 * face)
            ty = by + int(i * 2 + wave)
            _NS_dark_rider._aapolygon(surface, palette['cloth_darkest'], [
                (tx + 1, ty - 1),
                (tx - int(2 * face), ty + 2),
                (tx + 1, ty + 2),
            ])
            _NS_dark_rider._aapolygon(surface, palette['cloth_dark'], [
                (tx + 1, ty - 1),
                (tx - int(1 * face), ty + 1),
                (tx + 1, ty + 1),
            ])
            _NS_dark_rider._aaline(surface, palette['cloth_mid'],
                    (tx, ty), (tx - int(1 * face), ty + 1), 1)

        # ═══ 4 HORSE LEGS (with gallop animation) ═══
        _NS_dark_rider._draw_horse_legs(surface, bx, by + body_h // 2, face, phase,
                         is_running, palette)

        # ═══ HORSE BARDING (armor) - lvl 3+ ═══
        if barding:
            _NS_dark_rider._draw_horse_barding(surface, bx, by, face, palette, ornate)


    def _draw_horse_legs(surface, cx, cy, face, phase, is_running, palette):
        """4 horse legs with gallop animation."""
        if is_running:
            # Gallop cycle - front & back legs alternate
            fl_swing = math.sin(phase * 2.5) * 4
            bl_swing = math.sin(phase * 2.5 + math.pi) * 4
            fr_swing = math.sin(phase * 2.5 + math.pi / 2) * 4
            br_swing = math.sin(phase * 2.5 + 3 * math.pi / 2) * 4
        else:
            # Slight idle sway
            idle = math.sin(phase * 0.8) * 0.4
            fl_swing = idle
            bl_swing = -idle
            fr_swing = idle
            br_swing = -idle

        # Leg positions (relative to body center, along horse length)
        # Front legs (near head)
        # Back legs (near tail)
        legs = [
            (int(9 * face), fl_swing),    # front-left
            (int(6 * face), fr_swing),    # front-right (slightly behind)
            (int(-6 * face), bl_swing),   # back-left
            (int(-9 * face), br_swing),   # back-right
        ]

        for leg_x_off, swing in legs:
            hip_x = cx + leg_x_off
            hip_y = cy - 1

            knee_x = hip_x + int(swing * 0.4)
            knee_y = cy + 4

            hoof_x = hip_x + int(swing)
            hoof_y = cy + 10

            # Shadow
            _NS_dark_rider._aaline(surface, palette['shadow_deep'],
                    (hip_x + 1, hip_y + 1), (hoof_x + 1, hoof_y + 1), 4)

            # Upper leg (thigh) - thicker
            _NS_dark_rider._aaline(surface, palette['horse_darkest'],
                    (hip_x, hip_y), (knee_x, knee_y), 4)
            _NS_dark_rider._aaline(surface, palette['horse_dark'],
                    (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_dark_rider._aaline(surface, palette['horse_mid'],
                    (hip_x, hip_y), (knee_x, knee_y), 1)

            # Lower leg (shank) - thinner
            _NS_dark_rider._aaline(surface, palette['horse_darkest'],
                    (knee_x, knee_y), (hoof_x, hoof_y - 1), 3)
            _NS_dark_rider._aaline(surface, palette['horse_dark'],
                    (knee_x, knee_y), (hoof_x, hoof_y - 1), 2)

            # Hoof (dark/black)
            pygame.draw.rect(surface, palette['shadow'],
                             (hoof_x - 2, hoof_y - 1, 4, 2))
            pygame.draw.rect(surface, palette['horse_darkest'],
                             (hoof_x - 2, hoof_y - 1, 4, 1))


    def _draw_horse_barding(surface, cx, cy, face, palette, ornate=False):
        """Iron armor plating over horse."""
        body_w = 22
        body_h = 12

        # Chest plate (front of body)
        chest_x = cx + int((body_w // 2 - 4) * face)
        chest_y = cy

        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'], [
            (chest_x, chest_y - 4),
            (chest_x + int(5 * face), chest_y - 2),
            (chest_x + int(4 * face), chest_y + 4),
            (chest_x, chest_y + 4),
        ])
        _NS_dark_rider._aapolygon(surface, palette['armor_darkest'], [
            (chest_x, chest_y - 4),
            (chest_x + int(5 * face), chest_y - 2),
            (chest_x + int(4 * face), chest_y + 4),
            (chest_x, chest_y + 4),
        ])
        _NS_dark_rider._aapolygon(surface, palette['armor_dark'], [
            (chest_x, chest_y - 3),
            (chest_x + int(4 * face), chest_y - 1),
            (chest_x + int(3 * face), chest_y + 3),
            (chest_x, chest_y + 3),
        ])
        _NS_dark_rider._aapolygon(surface, palette['armor_mid'], [
            (chest_x + int(1 * face), chest_y - 2),
            (chest_x + int(3 * face), chest_y - 1),
            (chest_x + int(2 * face), chest_y + 2),
            (chest_x + int(1 * face), chest_y + 2),
        ])
        _NS_dark_rider._aaline(surface, palette['armor_light'],
                (chest_x + int(1 * face), chest_y - 2),
                (chest_x + int(3 * face), chest_y - 1), 1)

        # Back barding (behind rider saddle)
        saddle_x = cx - int(2 * face)
        saddle_y = cy - body_h // 2 - 1
        pygame.draw.rect(surface, palette['leather_darkest'],
                         (saddle_x - 6, saddle_y, 12, 3))
        pygame.draw.rect(surface, palette['leather_dark'],
                         (saddle_x - 6, saddle_y, 11, 2))
        pygame.draw.rect(surface, palette['leather_mid'],
                         (saddle_x - 6, saddle_y, 8, 1))

        # Gold accent on saddle
        if ornate:
            pygame.draw.rect(surface, palette['gold_dark'],
                             (saddle_x - 2, saddle_y - 1, 4, 1))
            pygame.draw.rect(surface, palette['gold_mid'],
                             (saddle_x - 1, saddle_y - 1, 2, 1))

        # Side barding plates (small metal squares along body)
        for i in range(2):
            plate_x = cx - int((3 + i * 4) * face)
            plate_y = cy + 1
            pygame.draw.rect(surface, palette['armor_darkest'],
                             (plate_x - 2, plate_y - 1, 4, 3))
            pygame.draw.rect(surface, palette['armor_dark'],
                             (plate_x - 2, plate_y - 1, 3, 2))
            pygame.draw.rect(surface, palette['armor_mid'],
                             (plate_x - 2, plate_y - 1, 2, 1))
            pygame.draw.rect(surface, palette['armor_light'],
                             (plate_x - 2, plate_y - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # RIDER CAPE
    # ═══════════════════════════════════════════════════════

    def _draw_cape(surface, cx, cy, phase, palette, size='medium'):
        """Purple flowing cape behind rider."""
        sway1 = int(math.sin(phase * 0.7) * 2)
        sway2 = int(math.sin(phase * 0.9 + 0.5) * 2)

        if size == 'small':
            length = 14
            width = 7
        elif size == 'medium':
            length = 18
            width = 9
        elif size == 'big':
            length = 22
            width = 11
        else:
            length = 26
            width = 13

        cape_outer = [
            (cx - width, cy),
            (cx + width, cy),
            (cx + width - 1, cy + length // 3),
            (cx + width - 2 + sway1, cy + length * 2 // 3),
            (cx + width - 4 + sway2, cy + length),
            (cx - 2, cy + length + 1),
            (cx - width + 4 - sway1, cy + length),
            (cx - width + 2 - sway2, cy + length * 2 // 3),
            (cx - width + 1, cy + length // 3),
        ]
        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in cape_outer])
        _NS_dark_rider._aapolygon(surface, palette['cloth_darkest'], cape_outer)

        cape_mid = [
            (cx - width + 1, cy + 1),
            (cx + width - 1, cy + 1),
            (cx + width - 2, cy + length // 3),
            (cx + width - 3 + sway1, cy + length * 2 // 3),
            (cx - 2, cy + length),
            (cx - width + 3 - sway1, cy + length * 2 // 3),
            (cx - width + 2, cy + length // 3),
        ]
        _NS_dark_rider._aapolygon(surface, palette['cloth_dark'], cape_mid)

        cape_inner = [
            (cx - width + 2, cy + 2),
            (cx + width - 2, cy + 2),
            (cx + width - 4, cy + length // 2),
            (cx - 1, cy + length - 2),
            (cx - width + 4, cy + length // 2),
        ]
        _NS_dark_rider._aapolygon(surface, palette['cloth_mid'], cape_inner)

        # Highlight streaks
        for streak_x_off in [-width // 2, 0, width // 2]:
            sx = cx + streak_x_off
            _NS_dark_rider._aaline(surface, palette['cloth_light'],
                    (sx, cy + 2), (sx + sway1, cy + length - 3), 1)

        # Tattered bottom
        for i in range(5):
            tx = cx - width + 2 + i * (width // 3)
            ty = cy + length + int(math.sin(phase * 1.5 + i) * 2)
            _NS_dark_rider._aapolygon(surface, palette['cloth_darkest'], [
                (tx - 1, cy + length - 2),
                (tx + 1, cy + length - 2),
                (tx, ty + 2),
            ])


    # ═══════════════════════════════════════════════════════
    # RIDER BODY VARIANTS
    # ═══════════════════════════════════════════════════════

    def _draw_rider_body_light(surface, cx, cy, face, palette, hurt):
        """Level 1 - basic armor."""
        body_w = 12
        body_h = 12

        if hurt:
            armor_mid = (255, 255, 255)
        else:
            armor_mid = palette['armor_mid']

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=3)

        # Body
        pygame.draw.rect(surface, palette['armor_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=3)
        pygame.draw.rect(surface, palette['armor_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=3)
        pygame.draw.rect(surface, armor_mid,
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=3)
        pygame.draw.rect(surface, palette['armor_light'],
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=2)


    def _draw_rider_body_armored(surface, cx, cy, face, palette, hurt,
                                  has_emblem=False, ornate=False,
                                  has_gold_trim=False):
        """Level 2-5 - dark plate armor."""
        body_w = 14 if not ornate else 15
        body_h = 14 if not ornate else 15

        # Shadow
        pygame.draw.rect(surface, palette['shadow_deep'],
                         (cx - body_w // 2 + 1, cy + 1, body_w, body_h),
                         border_radius=3)

        # Dark plate
        pygame.draw.rect(surface, palette['armor_darkest'],
                         (cx - body_w // 2, cy, body_w, body_h),
                         border_radius=3)
        pygame.draw.rect(surface, palette['armor_dark'],
                         (cx - body_w // 2, cy, body_w - 1, body_h - 1),
                         border_radius=3)
        pygame.draw.rect(surface, palette['armor_mid'],
                         (cx - body_w // 2, cy, body_w - 2, body_h - 3),
                         border_radius=3)
        pygame.draw.rect(surface, palette['armor_light'],
                         (cx - body_w // 2, cy, body_w - 4, body_h // 2),
                         border_radius=2)
        pygame.draw.rect(surface, palette['armor_high'],
                         (cx - body_w // 2 + 1, cy + 1, 3, 2),
                         border_radius=1)

        # Segmented plate lines
        for seg_y in [cy + 3, cy + 7, cy + 10]:
            _NS_dark_rider._aaline(surface, palette['armor_darkest'],
                    (cx - body_w // 2 + 2, seg_y),
                    (cx + body_w // 2 - 2, seg_y), 1)

        # Gold trim top
        if has_gold_trim:
            pygame.draw.rect(surface, palette['gold_dark'],
                             (cx - body_w // 2, cy, body_w, 2))
            pygame.draw.rect(surface, palette['gold_mid'],
                             (cx - body_w // 2, cy, body_w - 1, 1))
            pygame.draw.rect(surface, palette['gold_high'],
                             (cx - body_w // 2 + 1, cy, 2, 1))

        # Purple skull emblem
        if has_emblem:
            _NS_dark_rider._draw_chest_emblem(surface, cx, cy + 5, palette, ornate)

        # Rivets
        for rx in [-body_w // 2 + 2, body_w // 2 - 3]:
            for ry in [2, body_h - 4]:
                _NS_dark_rider._aacircle(surface, palette['armor_darkest'],
                          (cx + rx, cy + ry), 1)
                pygame.draw.rect(surface, palette['armor_high'],
                                 (cx + rx, cy + ry - 1, 1, 1))


    def _draw_chest_emblem(surface, cx, cy, palette, ornate=False):
        """Purple skull emblem (matches Death Charge icon)."""
        frame_size = 3 if not ornate else 4
        # Gold frame
        _NS_dark_rider._aapolygon(surface, palette['gold_dark'], [
            (cx - frame_size, cy),
            (cx + frame_size, cy),
            (cx + frame_size, cy + frame_size + 1),
            (cx - frame_size, cy + frame_size + 1),
        ])
        _NS_dark_rider._aapolygon(surface, palette['gold_mid'], [
            (cx - frame_size + 1, cy + 1),
            (cx + frame_size - 1, cy + 1),
            (cx + frame_size - 1, cy + frame_size),
            (cx - frame_size + 1, cy + frame_size),
        ])
        # Small skull
        _NS_dark_rider._aacircle(surface, palette['flame_bright'], (cx, cy + 2), 1)
        if ornate:
            pygame.draw.rect(surface, palette['flame_hot'], (cx, cy + 2, 1, 1))


    # ═══════════════════════════════════════════════════════
    # RIDER HEAD (Horned helm - match reference)
    # ═══════════════════════════════════════════════════════

    def _draw_rider_head(surface, cx, cy, face, palette, hurt,
                         has_horns='small', has_crown=False):
        """Horned helm with glowing purple eyes."""
        head_r = 6

        # Head shadow
        _NS_dark_rider._aacircle(surface, palette['shadow_deep'], (cx + 1, cy + 1), head_r)

        # Dark helm base
        _NS_dark_rider._aacircle(surface, palette['armor_darkest'], (cx, cy), head_r)
        _NS_dark_rider._aacircle(surface, palette['armor_dark'], (cx, cy), head_r - 1)
        _NS_dark_rider._aacircle(surface, palette['armor_mid'], (cx - 1, cy - 1), head_r - 2)
        _NS_dark_rider._aacircle(surface, palette['armor_light'], (cx - 2, cy - 2), head_r - 4)

        # Face plate (dark opening for eyes)
        _NS_dark_rider._aapolygon(surface, palette['shadow'], [
            (cx - 3, cy - 1),
            (cx + 3, cy - 1),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'], [
            (cx - 2, cy),
            (cx + 2, cy),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])

        # Glowing PURPLE eyes (like undead)
        for eye_x_off in [-2, 2]:
            eye_x = cx + eye_x_off
            eye_y = cy + 1

            _NS_dark_rider._aacircle(surface, palette['flame_dark'], (eye_x, eye_y), 1)
            pygame.draw.rect(surface, palette['flame_bright'], (eye_x, eye_y, 1, 1))

            # Outer glow
            for glow_r in (3, 2):
                alpha = 100 - glow_r * 20
                alpha = max(0, alpha)
                glow_surf = pygame.Surface((glow_r * 4, glow_r * 4),
                                            pygame.SRCALPHA)
                pygame.draw.circle(glow_surf,
                                   (*palette['flame_light'], alpha),
                                   (glow_r * 2, glow_r * 2), glow_r)
                surface.blit(glow_surf,
                             (eye_x - glow_r * 2, eye_y - glow_r * 2))

        # Nose guard (vertical line)
        _NS_dark_rider._aaline(surface, palette['armor_darkest'],
                (cx, cy + 2), (cx, cy + 5), 1)

        # Chin guard
        _NS_dark_rider._aapolygon(surface, palette['armor_dark'], [
            (cx - 2, cy + 3),
            (cx + 2, cy + 3),
            (cx + 1, cy + 5),
            (cx - 1, cy + 5),
        ])

        # ═══ HORNS (two big horns curving upward) ═══
        horn_size_map = {
            'small': (3, 4),
            'medium': (4, 6),
            'big': (5, 8),
            'huge': (6, 10),
        }
        horn_w, horn_h = horn_size_map.get(has_horns, (4, 6))

        for side in (-1, 1):
            base_x = cx + side * (head_r - 1)
            base_y = cy - 2
            mid_x = base_x + side * (horn_w - 1)
            mid_y = cy - horn_h // 2 - 1
            tip_x = base_x + side * horn_w
            tip_y = cy - horn_h

            # Shadow
            _NS_dark_rider._aapolygon(surface, palette['shadow_deep'], [
                (base_x + 1, base_y + 1),
                (mid_x + 1, mid_y + 1),
                (tip_x + 1, tip_y + 1),
            ])

            # Bone horn layers
            _NS_dark_rider._aapolygon(surface, palette['bone_dark'], [
                (base_x - 1, base_y),
                (base_x + 1, base_y),
                (mid_x, mid_y),
                (tip_x, tip_y),
            ])
            _NS_dark_rider._aapolygon(surface, palette['bone_mid'], [
                (base_x, base_y),
                (base_x + 1, base_y),
                (mid_x, mid_y),
                (tip_x, tip_y),
            ])
            _NS_dark_rider._aaline(surface, palette['bone_light'],
                    (base_x, base_y), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, palette['bone_high'],
                             (tip_x, tip_y, 1, 1))

        # ═══ CROWN (lvl 5 - dread lord) ═══
        if has_crown:
            _NS_dark_rider._draw_crown(surface, cx, cy - head_r + 1, palette)


    def _draw_crown(surface, cx, cy, palette):
        """Dark gold crown for Dread Lord."""
        pygame.draw.rect(surface, palette['shadow'], (cx - 5, cy + 1, 10, 3))
        pygame.draw.rect(surface, palette['gold_darkest'],
                         (cx - 5, cy, 10, 3))
        pygame.draw.rect(surface, palette['gold_dark'],
                         (cx - 5, cy, 9, 2))
        pygame.draw.rect(surface, palette['gold_high'],
                         (cx - 4, cy, 3, 1))

        for spike_x_off in [-3, 0, 3]:
            sx = cx + spike_x_off
            _NS_dark_rider._aapolygon(surface, palette['gold_darkest'], [
                (sx - 1, cy),
                (sx, cy - 3),
                (sx + 1, cy),
            ])
            _NS_dark_rider._aapolygon(surface, palette['gold_dark'], [
                (sx - 1, cy),
                (sx, cy - 2),
                (sx + 1, cy),
            ])
            pygame.draw.rect(surface, palette['gold_high'], (sx, cy - 2, 1, 1))

        _NS_dark_rider._aacircle(surface, palette['flame_dark'], (cx, cy + 1), 1)
        pygame.draw.rect(surface, palette['flame_bright'], (cx, cy + 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # SHOULDER SPIKES
    # ═══════════════════════════════════════════════════════

    def _draw_shoulder_spikes(surface, x, y, palette, mirror=False):
        """Iron pauldron with spikes."""
        direction = -1 if mirror else 1

        pad_pts = [
            (x - 3 * direction, y),
            (x + 2 * direction, y),
            (x + 3 * direction, y + 2),
            (x + 1 * direction, y + 5),
            (x - 3 * direction, y + 4),
        ]

        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in pad_pts])
        _NS_dark_rider._aapolygon(surface, palette['armor_darkest'], pad_pts)
        _NS_dark_rider._aapolygon(surface, palette['armor_dark'], [
            (x - 2 * direction, y + 1),
            (x + 1 * direction, y + 1),
            (x + 2 * direction, y + 2),
            (x, y + 4),
            (x - 2 * direction, y + 3),
        ])
        _NS_dark_rider._aapolygon(surface, palette['armor_mid'], [
            (x - 2 * direction, y + 1),
            (x + 1 * direction, y + 1),
            (x + 1 * direction, y + 2),
            (x - 1 * direction, y + 3),
        ])
        pygame.draw.rect(surface, palette['armor_light'],
                         (x - 2 * direction, y + 1, 1, 1))

        # 2 spikes on top
        for spike_i in range(2):
            sx = x + (-2 + spike_i * 3) * direction
            sy = y

            _NS_dark_rider._aapolygon(surface, palette['shadow_deep'], [
                (sx - 1, sy + 1), (sx, sy - 4), (sx + 1, sy + 1),
            ])
            _NS_dark_rider._aapolygon(surface, palette['armor_darkest'], [
                (sx - 1, sy), (sx, sy - 4), (sx + 1, sy),
            ])
            _NS_dark_rider._aapolygon(surface, palette['armor_dark'], [
                (sx - 1, sy), (sx, sy - 3), (sx + 1, sy),
            ])
            pygame.draw.rect(surface, palette['armor_high'], (sx, sy - 3, 1, 2))


    # ═══════════════════════════════════════════════════════
    # RIDER WEAPON (sword aimed forward like a lance)
    # ═══════════════════════════════════════════════════════

    def _draw_rider_weapon(surface, sx, sy, face, walk_phase,
                           attack_progress, is_running, is_attacking,
                           palette, weapon='sword_medium'):
        """Rider's sword extended forward (like a jousting position)."""
        # Base position: sword held forward
        if is_attacking:
            if attack_progress < 0.25:
                # Wind-up back
                t = attack_progress / 0.25
                t = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.4 * t
                extend = 5 - t * 2
            elif attack_progress < 0.55:
                # Thrust forward
                t = (attack_progress - 0.25) / 0.30
                t = t ** 2
                swing_angle = -math.pi * 0.4 + t * math.pi * 0.8
                extend = 3 + t * 8
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                t = 1 - (1 - t) ** 2
                swing_angle = math.pi * 0.4 - t * math.pi * 0.4
                extend = 11 - t * 6
        elif is_running:
            swing_angle = math.sin(walk_phase * 2) * 0.15
            extend = 5
        else:
            swing_angle = math.sin(walk_phase * 0.5) * 0.08
            extend = 5

        # Sword tip position
        weapon_angle = swing_angle
        hand_x = sx
        hand_y = sy
        tip_offset_x = int(math.cos(weapon_angle) * extend) * face
        tip_offset_y = int(math.sin(weapon_angle) * extend) - 1

        # Draw arm from body to hand
        _NS_dark_rider._aaline(surface, palette['shadow_deep'],
                (sx - face * 4 + 1, sy + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_dark_rider._aaline(surface, palette['armor_darkest'],
                (sx - face * 4, sy), (hand_x, hand_y), 4)
        _NS_dark_rider._aaline(surface, palette['armor_dark'],
                (sx - face * 4, sy), (hand_x, hand_y), 3)
        _NS_dark_rider._aaline(surface, palette['armor_mid'],
                (sx - face * 4, sy), (hand_x, hand_y), 1)

        # Gauntlet
        _NS_dark_rider._aacircle(surface, palette['armor_darkest'], (hand_x, hand_y), 2)
        _NS_dark_rider._aacircle(surface, palette['armor_mid'], (hand_x, hand_y), 1)

        glowing = is_attacking and 0.25 <= attack_progress <= 0.65

        if weapon == 'sword_small':
            _NS_dark_rider._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='small', glowing=glowing)
        elif weapon == 'sword_medium':
            _NS_dark_rider._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='medium', glowing=glowing)
        elif weapon == 'sword_big':
            _NS_dark_rider._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='big', glowing=glowing)
        elif weapon == 'sword_huge':
            _NS_dark_rider._draw_sword(surface, hand_x, hand_y, weapon_angle, face,
                        palette, size='huge', glowing=glowing)

        # Motion blur during attack
        if is_attacking and 0.25 <= attack_progress <= 0.65:
            _NS_dark_rider._draw_sword_blur(surface, hand_x, hand_y, face, attack_progress,
                             palette)


    def _draw_sword(surface, x, y, angle, face, palette, size='small',
                    glowing=False):
        """Sword blade extended forward."""
        if size == 'small':
            blade_len = 12
            blade_w = 2
        elif size == 'medium':
            blade_len = 15
            blade_w = 2
        elif size == 'big':
            blade_len = 18
            blade_w = 3
        else:  # huge
            blade_len = 22
            blade_w = 3

        cos_a = math.cos(angle) * face
        sin_a = math.sin(angle)
        perp_cos = -sin_a
        perp_sin = cos_a

        # Cross-guard (gold)
        guard_w = 3 if size == 'small' else 4
        guard_pts = [
            (int(x + perp_cos * guard_w), int(y + perp_sin * guard_w)),
            (int(x - perp_cos * guard_w), int(y - perp_sin * guard_w)),
            (int(x - perp_cos * guard_w + cos_a * 2),
             int(y - perp_sin * guard_w + sin_a * 2)),
            (int(x + perp_cos * guard_w + cos_a * 2),
             int(y + perp_sin * guard_w + sin_a * 2)),
        ]
        _NS_dark_rider._aapolygon(surface, palette['shadow_deep'],
                   [(p[0] + 1, p[1] + 1) for p in guard_pts])
        _NS_dark_rider._aapolygon(surface, palette['gold_darkest'], guard_pts)
        _NS_dark_rider._aapolygon(surface, palette['gold_dark'], [
            (int(x + perp_cos * (guard_w - 1)),
             int(y + perp_sin * (guard_w - 1))),
            (int(x - perp_cos * (guard_w - 1)),
             int(y - perp_sin * (guard_w - 1))),
            (int(x - perp_cos * (guard_w - 1) + cos_a * 1),
             int(y - perp_sin * (guard_w - 1) + sin_a * 1)),
            (int(x + perp_cos * (guard_w - 1) + cos_a * 1),
             int(y + perp_sin * (guard_w - 1) + sin_a * 1)),
        ])
        _NS_dark_rider._aapolygon(surface, palette['gold_mid'], [
            (int(x + perp_cos * (guard_w - 1)),
             int(y + perp_sin * (guard_w - 1))),
            (int(x - perp_cos * 1), int(y - perp_sin * 1)),
            (int(x + perp_cos * (guard_w - 1) + cos_a * 1),
             int(y + perp_sin * (guard_w - 1) + sin_a * 1)),
        ])
        pygame.draw.rect(surface, palette['gold_high'],
                         (int(x + perp_cos * (guard_w - 1)),
                          int(y + perp_sin * (guard_w - 1)), 1, 1))

        # Blade
        blade_tip_x = x + int(cos_a * (blade_len + 2))
        blade_tip_y = y + int(sin_a * (blade_len + 2))
        blade_base_x = x + int(cos_a * 2)
        blade_base_y = y + int(sin_a * 2)

        _NS_dark_rider._aapolygon(surface, palette['shadow'], [
            (int(blade_base_x + perp_cos * (blade_w + 1)),
             int(blade_base_y + perp_sin * (blade_w + 1))),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * (blade_w + 1)),
             int(blade_base_y - perp_sin * (blade_w + 1))),
        ])

        _NS_dark_rider._aapolygon(surface, palette['blade_dark'], [
            (int(blade_base_x + perp_cos * blade_w),
             int(blade_base_y + perp_sin * blade_w)),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * blade_w),
             int(blade_base_y - perp_sin * blade_w)),
        ])

        _NS_dark_rider._aapolygon(surface, palette['blade_mid'], [
            (int(blade_base_x + perp_cos * (blade_w - 1)),
             int(blade_base_y + perp_sin * (blade_w - 1))),
            (blade_tip_x, blade_tip_y),
            (int(blade_base_x - perp_cos * (blade_w - 1)),
             int(blade_base_y - perp_sin * (blade_w - 1))),
        ])

        # Center fuller
        _NS_dark_rider._aaline(surface, palette['blade_dark'],
                (blade_base_x, blade_base_y),
                (blade_tip_x, blade_tip_y), 1)

        # Edge highlights
        _NS_dark_rider._aaline(surface, palette['blade_high'],
                (int(blade_base_x + perp_cos * (blade_w - 1)),
                 int(blade_base_y + perp_sin * (blade_w - 1))),
                (blade_tip_x, blade_tip_y), 1)
        _NS_dark_rider._aaline(surface, palette['blade_shine'],
                (int(blade_base_x + perp_cos * (blade_w - 1)),
                 int(blade_base_y + perp_sin * (blade_w - 1))),
                (blade_tip_x, blade_tip_y), 1)

        # Sharp tip
        _NS_dark_rider._aacircle(surface, palette['shine'], (blade_tip_x, blade_tip_y), 1)

        # Purple curse glow when attacking
        if glowing:
            for r in (7, 5, 3):
                _NS_dark_rider._blend_alpha(surface,
                             (*palette['flame_mid'], max(0, 140 - r * 15)),
                             [
                                 (blade_tip_x - r, blade_tip_y - r),
                                 (blade_tip_x + r, blade_tip_y - r),
                                 (blade_tip_x + r, blade_tip_y + r),
                                 (blade_tip_x - r, blade_tip_y + r),
                             ])
            _NS_dark_rider._aacircle(surface, palette['flame_bright'],
                      (blade_tip_x, blade_tip_y), 2)


    def _draw_sword_blur(surface, hand_x, hand_y, face, progress, palette):
        """Purple motion blur during attack."""
        for ghost_i in range(4):
            ghost_progress = progress - (ghost_i + 1) * 0.05
            if ghost_progress < 0.25:
                continue

            alpha = max(0, min(255, 100 - ghost_i * 22))
            if alpha <= 0:
                continue

            blur_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            _NS_dark_rider._aacircle(blur_surf, (*palette['flame_dark'], alpha),
                      (12, 12), 6)
            _NS_dark_rider._aacircle(blur_surf, (*palette['flame_mid'], alpha),
                      (12, 12), 4)
            _NS_dark_rider._aacircle(blur_surf, (*palette['flame_bright'], alpha // 2),
                      (12, 12), 2)
            surface.blit(blur_surf,
                         (hand_x + face * 8 - 12 - ghost_i * 2 * face, hand_y - 12))


    # ═══════════════════════════════════════════════════════
    # CURSE ARC (Purple curved slash - matches reference)
    # ═══════════════════════════════════════════════════════

    def _draw_curse_arc(surface, cx, cy, face, progress, palette):
        """Purple crescent swipe extending forward."""
        t = (progress - 0.28) / 0.44
        t = max(0.0, min(1.0, t))

        # Wide sweeping arc from top-back to bottom-front
        start_angle = math.radians(-90)
        end_angle = math.radians(60)
        current = start_angle + (end_angle - start_angle) * t

        center_x = cx + 12 * face
        center_y = cy - 5
        radius = 32

        for i in range(18):
            offset = i * 0.08
            seg_t = t - offset * 0.05
            if seg_t < 0:
                continue
            seg_angle = start_angle + (end_angle - start_angle) * seg_t

            alpha_fade = 1.0 - offset
            alpha = max(0, min(255, int(220 * alpha_fade * math.sin(t * math.pi))))
            if alpha <= 0:
                continue

            for r_offset, blade_color, w in [
                (0, palette['flame_darkest'], 6),
                (0, palette['flame_dark'], 5),
                (0, palette['flame_mid'], 3),
                (0, palette['flame_light'], 2),
                (0, palette['flame_bright'], 1),
            ]:
                inner_r = radius - 6 + r_offset
                outer_r = radius + 5 + r_offset

                ix = center_x + int(math.cos(seg_angle) * inner_r) * face
                iy = center_y + int(math.sin(seg_angle) * inner_r)
                ox = center_x + int(math.cos(seg_angle) * outer_r) * face
                oy = center_y + int(math.sin(seg_angle) * outer_r)

                _NS_dark_rider._blend_alpha(surface, (*blade_color, alpha), [
                    (ix, iy), (ox, oy),
                    (ox + 1, oy + 1), (ix + 1, iy + 1),
                ])
                _NS_dark_rider._aaline(surface, (*blade_color, alpha),
                        (ix, iy), (ox, oy), w)

        # Leading bright edge
        lead_alpha = int(240 * math.sin(t * math.pi))
        lead_x = center_x + int(math.cos(current) * radius) * face
        lead_y = center_y + int(math.sin(current) * radius)
        _NS_dark_rider._aacircle(surface, palette['flame_bright'], (lead_x, lead_y), 4)
        _NS_dark_rider._aacircle(surface, palette['flame_hot'], (lead_x, lead_y), 2)
        _NS_dark_rider._aacircle(surface, palette['shine'], (lead_x, lead_y), 1)


    def _draw_curse_impact(surface, cx, cy, face, progress, palette):
        """Purple sparkle star at impact point."""
        t = (progress - 0.48) / 0.15
        t = max(0.0, min(1.0, t))

        impact_x = cx + 32 * face
        impact_y = cy - 3

        star_r = int(7 + t * 12)
        alpha = int(240 * (1 - t))

        # 4-pointed star
        for angle_deg in [0, 45, 90, 135]:
            angle = math.radians(angle_deg)
            ox1 = impact_x + int(math.cos(angle) * star_r)
            oy1 = impact_y + int(math.sin(angle) * star_r)
            ox2 = impact_x - int(math.cos(angle) * star_r)
            oy2 = impact_y - int(math.sin(angle) * star_r)

            _NS_dark_rider._aaline(surface, (*palette['flame_dark'], alpha),
                    (ox1, oy1), (ox2, oy2), 4)
            _NS_dark_rider._aaline(surface, (*palette['flame_light'], alpha),
                    (ox1, oy1), (ox2, oy2), 2)
            _NS_dark_rider._aaline(surface, (*palette['flame_hot'], alpha),
                    (ox1, oy1), (ox2, oy2), 1)

        # Central bright core
        core_alpha = int(255 * (1 - t))
        _NS_dark_rider._aacircle(surface, (*palette['flame_bright'], core_alpha),
                  (impact_x, impact_y), 5)
        _NS_dark_rider._aacircle(surface, (*palette['flame_hot'], core_alpha),
                  (impact_x, impact_y), 3)
        _NS_dark_rider._aacircle(surface, palette['flame_white'], (impact_x, impact_y),
                  max(1, int(1 + (1 - t))))


    # ═══════════════════════════════════════════════════════
    # DEATH CHARGE ICON (above head when passive active)
    # ═══════════════════════════════════════════════════════

    def _draw_death_charge_icon(surface, cx, cy, timer, palette):
        """Purple skull comet icon above head (matches passive icon)."""
        pulse = math.sin(timer * 0.15) * 0.25 + 0.75

        icon_size = 12
        icon_surf = pygame.Surface((icon_size * 2, icon_size * 2), pygame.SRCALPHA)
        ics = icon_size

        # Frame background
        pygame.draw.rect(icon_surf, (0, 0, 0, 200),
                         (ics - 7, ics - 7, 14, 14), border_radius=2)
        pygame.draw.rect(icon_surf, palette['flame_darkest'],
                         (ics - 6, ics - 6, 12, 12), border_radius=2)
        pygame.draw.rect(icon_surf, palette['gold_dark'],
                         (ics - 6, ics - 6, 12, 12), 1, border_radius=2)

        # Comet trail (behind skull)
        for i in range(3):
            trail_x = ics + 3 + i * 2
            trail_y = ics + 2 + i
            pygame.draw.rect(icon_surf,
                             (*palette['flame_dark'],
                              int(150 - i * 40)),
                             (trail_x, trail_y, 3 - i, 1))
            pygame.draw.rect(icon_surf,
                             (*palette['flame_light'],
                              int(180 - i * 40)),
                             (trail_x, trail_y, 2 - i // 2, 1))

        # Skull head
        sk_cx, sk_cy = ics - 1, ics
        _NS_dark_rider._aacircle(icon_surf, palette['flame_darkest'], (sk_cx, sk_cy), 3)
        _NS_dark_rider._aacircle(icon_surf, palette['flame_dark'], (sk_cx, sk_cy), 2)
        _NS_dark_rider._aacircle(icon_surf, palette['flame_bright'], (sk_cx - 1, sk_cy - 1), 1)
        # Eye sockets
        pygame.draw.rect(icon_surf, (0, 0, 0), (sk_cx - 1, sk_cy - 1, 1, 1))
        pygame.draw.rect(icon_surf, (0, 0, 0), (sk_cx + 1, sk_cy - 1, 1, 1))
        pygame.draw.rect(icon_surf, palette['flame_hot'],
                         (sk_cx - 1, sk_cy - 1, 1, 1))
        pygame.draw.rect(icon_surf, palette['flame_hot'],
                         (sk_cx + 1, sk_cy - 1, 1, 1))
        # Small teeth
        pygame.draw.rect(icon_surf, palette['flame_light'],
                         (sk_cx - 1, sk_cy + 1, 3, 1))

        surface.blit(icon_surf, (cx - icon_size, cy - icon_size))

        # Sparkles orbiting icon
        for i in range(3):
            angle = timer * 0.15 + i * math.pi * 2 / 3
            sx = cx + int(math.cos(angle) * 12)
            sy = cy + int(math.sin(angle) * 6)
            alpha = int(200 * pulse)
            _NS_dark_rider._aacircle(surface, (*palette['flame_bright'], alpha), (sx, sy), 2)
            _NS_dark_rider._aacircle(surface, (*palette['flame_hot'], alpha), (sx, sy), 1)


    # ═══════════════════════════════════════════════════════
    # DREAD LORD AURA (Lvl 5)
    # ═══════════════════════════════════════════════════════

    def _draw_dread_lord_aura(surface, x, y, timer, palette):
        """Big pulsing purple aura for Dread Lord."""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7
        aura_r = 30
        aura_surf = pygame.Surface((aura_r * 3, aura_r * 3), pygame.SRCALPHA)

        for r in range(aura_r, 3, -2):
            alpha = int((aura_r - r) * 3 * pulse)
            alpha = max(0, min(255, alpha))
            if alpha > 0:
                _NS_dark_rider._aacircle(aura_surf, (*palette['flame_mid'], alpha),
                          (aura_r * 3 // 2, aura_r * 3 // 2), r)

        surface.blit(aura_surf,
                     (x - aura_r * 3 // 2, y - aura_r * 3 // 2))

        # Orbiting purple embers
        for i in range(5):
            angle = timer * 0.06 + i * math.pi * 2 / 5
            sx = x + int(math.cos(angle) * 24)
            sy = y + int(math.sin(angle) * 14)
            _NS_dark_rider._aacircle(surface, palette['flame_bright'], (sx, sy), 2)
            _NS_dark_rider._aacircle(surface, palette['flame_hot'], (sx, sy), 1)


