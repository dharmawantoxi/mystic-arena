"""
towers/_bundle.py - semua renderer tower

Gabungan dari 5 file:
  - base_renderer.py         level modul
  - archer_tower.py          namespace _NS_archer_tower
  - cannon_tower.py          namespace _NS_cannon_tower
  - ice_tower.py             namespace _NS_ice_tower
  - mage_tower.py            namespace _NS_mage_tower

Modul yang dibungkus kelas `_NS_<nama>` supaya simbol
bernama sama TIDAK saling menimpa. Ini sudah diukur:
LEVEL_CONFIGS di 4 file tower isinya berbeda semua,
begitu juga PALETTE dan HAS_AACIRCLE di minions.

Modul di level modul (tidak dibungkus) karena kodenya
merujuk simbolnya sendiri saat modul dimuat, sehingga
nama kelas namespace belum terikat:
  base_renderer

File asli tetap ada sebagai jembatan kecil, jadi semua
baris `from towers.<modul> import ...` yang sudah ada
TETAP JALAN tanpa perubahan apa pun.
"""
import pygame
import math
import random


# ====================================================================
# base_renderer.py  (modul bersama)
# ====================================================================
# ================================
# towers/base_renderer.py
# Shared utilities & palette untuk semua tower
# ================================


# ═══════════════════════════════════════
# GLOBAL PALETTE (dipakai semua tower)
# ═══════════════════════════════════════
OUTLINE = (30, 25, 35)

# Fire (untuk torch di semua tower)
FIRE_ORANGE = (255, 150, 40)
FIRE_YELLOW = (255, 220, 100)
FIRE_PURPLE = (200, 40, 100)  # untuk red team
FIRE_PINK = (255, 100, 200)


def get_team_palette(team):
    """
    Return dict palette lengkap berdasarkan team.
    Semua tower bisa akses palette yang konsisten.
    """
    if team == "blue":
        return {
            # Stone
            'STONE_DARK': (100, 100, 110),
            'STONE_MID': (160, 160, 170),
            'STONE_LIGHT': (210, 210, 220),
            'STONE_HIGH': (240, 240, 245),

            # Wood
            'WOOD_DARK': (90, 55, 30),
            'WOOD_MID': (140, 90, 50),
            'WOOD_LIGHT': (180, 130, 80),

            # Metal
            'METAL_DARK': (55, 60, 70),
            'METAL_MID': (95, 100, 115),
            'METAL_LIGHT': (150, 155, 170),
            'METAL_HIGH': (210, 215, 225),

            # Roof (blue tiles)
            'ROOF_DARK': (50, 80, 130),
            'ROOF_MID': (80, 120, 180),
            'ROOF_LIGHT': (130, 170, 220),

            # Team accent (blue)
            'ACCENT_MAIN': (60, 130, 220),
            'ACCENT_DARK': (30, 80, 170),
            'ACCENT_LIGHT': (120, 180, 255),

            # Shield
            'SHIELD_MAIN': (60, 130, 220),
            'SHIELD_DARK': (30, 80, 170),
            'SHIELD_LIGHT': (120, 180, 255),

            # Cannon (silver dark)
            'CANNON_DARK': (45, 45, 55),
            'CANNON_MID': (85, 85, 95),
            'CANNON_LIGHT': (140, 140, 150),
            'CANNON_HIGH': (200, 200, 210),

            # Character (archer/gunner)
            'CHAR_MAIN': (60, 130, 70),  # green archer
            'CHAR_DARK': (30, 80, 40),
            'CHAR_LIGHT': (90, 160, 100),

            # Gunner (military blue)
            'GUNNER_MAIN': (40, 60, 100),
            'GUNNER_DARK': (20, 30, 60),
            'GUNNER_LIGHT': (80, 110, 160),

            # Weather (snow)
            'SNOW': (230, 240, 250),
            'SNOW_SHADOW': (170, 190, 210),

            # Sandbag
            'SANDBAG': (180, 160, 100),
            'SANDBAG_DARK': (130, 115, 70),

            # Hazard stripes
            'HAZARD_YELLOW': (240, 200, 40),
            'HAZARD_DARK': (30, 25, 15),

            # Skin
            'SKIN': (240, 200, 160),

            # Gold
            'GOLD_C': (240, 200, 60),
            'GOLD_LIGHT': (255, 230, 130),

            # Fire (normal orange)
            'FIRE_OUTER': FIRE_ORANGE,
            'FIRE_INNER': FIRE_YELLOW,
            'FIRE_GLOW': (255, 200, 100, 60),

            # Eye color
            'EYE': (30, 30, 50),

            # Flag
            'FLAG_MAIN': (60, 130, 220),
            'FLAG_DARK': (30, 80, 170),
            'FLAG_LIGHT': (120, 180, 255),
        }
    else:  # red team
        return {
            'STONE_DARK': (75, 60, 65),
            'STONE_MID': (120, 95, 100),
            'STONE_LIGHT': (165, 135, 140),
            'STONE_HIGH': (195, 170, 175),

            'WOOD_DARK': (55, 30, 20),
            'WOOD_MID': (95, 55, 35),
            'WOOD_LIGHT': (140, 85, 55),

            'METAL_DARK': (50, 30, 30),
            'METAL_MID': (95, 55, 55),
            'METAL_LIGHT': (140, 85, 85),
            'METAL_HIGH': (180, 130, 130),

            'ROOF_DARK': (100, 25, 25),
            'ROOF_MID': (150, 40, 40),
            'ROOF_LIGHT': (200, 70, 70),

            'ACCENT_MAIN': (150, 30, 30),
            'ACCENT_DARK': (90, 15, 15),
            'ACCENT_LIGHT': (200, 60, 60),

            'SHIELD_MAIN': (100, 30, 30),
            'SHIELD_DARK': (60, 15, 15),
            'SHIELD_LIGHT': (160, 50, 50),

            'CANNON_DARK': (25, 20, 25),
            'CANNON_MID': (55, 45, 50),
            'CANNON_LIGHT': (95, 80, 85),
            'CANNON_HIGH': (140, 120, 125),

            'CHAR_MAIN': (100, 30, 40),  # red evil archer
            'CHAR_DARK': (60, 15, 20),
            'CHAR_LIGHT': (150, 60, 70),

            'GUNNER_MAIN': (100, 25, 25),
            'GUNNER_DARK': (60, 10, 10),
            'GUNNER_LIGHT': (150, 50, 50),

            'SNOW': (80, 70, 65),
            'SNOW_SHADOW': (50, 40, 40),

            'SANDBAG': (130, 100, 80),
            'SANDBAG_DARK': (85, 65, 50),

            'HAZARD_YELLOW': (180, 140, 30),
            'HAZARD_DARK': (25, 15, 10),

            'SKIN': (180, 150, 130),

            'GOLD_C': (180, 130, 40),
            'GOLD_LIGHT': (220, 170, 70),

            'FIRE_OUTER': FIRE_PURPLE,
            'FIRE_INNER': FIRE_PINK,
            'FIRE_GLOW': (255, 100, 200, 60),

            'EYE': (255, 50, 50),

            'FLAG_MAIN': (180, 30, 30),
            'FLAG_DARK': (110, 15, 15),
            'FLAG_LIGHT': (230, 70, 70),
        }


# ═══════════════════════════════════════
# SHARED DRAWING HELPERS
# ═══════════════════════════════════════

def draw_torch(surface, x, y, timer, palette, team, side_offset=0):
    """
    Draw torch dengan animated fire.
    Bisa dipakai semua tower.
    """
    # Bracket
    pygame.draw.rect(surface, palette['WOOD_DARK'],
                     (x - 1, y, 2, 4))
    # Bowl
    pygame.draw.rect(surface, palette['WOOD_MID'],
                     (x - 2, y - 2, 4, 2))
    pygame.draw.rect(surface, OUTLINE,
                     (x - 2, y - 2, 4, 2), 1)

    # Fire
    flicker = (timer + side_offset) % 4
    fire_h = 5 + flicker

    pygame.draw.polygon(surface, palette['FIRE_OUTER'], [
        (x - 2, y - 2),
        (x, y - 2 - fire_h),
        (x + 2, y - 2),
    ])
    pygame.draw.polygon(surface, palette['FIRE_INNER'], [
        (x - 1, y - 3),
        (x, y - 2 - fire_h + 1),
        (x + 1, y - 3),
    ])

    # Glow
    glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, palette['FIRE_GLOW'], (8, 8), 6)
    surface.blit(glow_surf, (x - 8, y - 10))


def draw_aura(surface, x, y, team, size=32):
    """Draw glowing aura di sekitar karakter."""
    aura_col = (100, 200, 255, 40) if team == "blue" \
        else (255, 100, 100, 40)

    aura_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(aura_surf, aura_col,
                       (size // 2, size // 2), size // 2 - 2)
    pygame.draw.circle(aura_surf, aura_col,
                       (size // 2, size // 2), size // 3)
    surface.blit(aura_surf, (x - size // 2, y - size // 2))


def draw_shield_emblem(surface, x, y, team, palette):
    """
    Draw shield emblem (dengan simbol berbeda per team).
    Blue: arrow up
    Red: skull
    """
    # Shield outline
    pygame.draw.polygon(surface, OUTLINE, [
        (x - 5, y - 5), (x + 5, y - 5),
        (x + 5, y + 2), (x, y + 7), (x - 5, y + 2),
    ])
    # Gold trim
    pygame.draw.polygon(surface, palette['GOLD_C'], [
        (x - 5, y - 5), (x + 5, y - 5),
        (x + 5, y + 2), (x, y + 7), (x - 5, y + 2),
    ])
    # Shield main
    pygame.draw.polygon(surface, palette['SHIELD_MAIN'], [
        (x - 4, y - 4), (x + 4, y - 4),
        (x + 4, y + 1), (x, y + 5), (x - 4, y + 1),
    ])
    # Highlight
    pygame.draw.polygon(surface, palette['SHIELD_LIGHT'], [
        (x - 4, y - 4), (x - 1, y - 4), (x - 3, y),
    ])

    # Symbol
    if team == "blue":
        # Cross/arrow up
        pygame.draw.rect(surface, palette['GOLD_C'],
                         (x - 1, y - 3, 2, 6))
        pygame.draw.rect(surface, palette['GOLD_C'],
                         (x - 3, y - 1, 6, 2))
        pygame.draw.rect(surface, palette['GOLD_LIGHT'],
                         (x - 1, y - 3, 1, 3))
    else:
        # Skull
        pygame.draw.circle(surface, palette['GOLD_C'], (x, y - 1), 2)
        pygame.draw.rect(surface, OUTLINE, (x - 1, y - 1, 1, 1))
        pygame.draw.rect(surface, OUTLINE, (x + 1, y - 1, 1, 1))
        pygame.draw.rect(surface, palette['GOLD_C'],
                         (x - 2, y + 2, 5, 1))


def draw_muzzle_flash(surface, x, y, intensity, size=6, color_style="normal"):
    """
    Draw muzzle flash effect.
    color_style: "normal" (yellow), "cannon" (big explosion),
                 "ice" (blue), "magic" (purple)
    """
    if size <= 0 or intensity <= 0:
        return

    # Color palette based on style
    if color_style == "cannon":
        colors = [
            (255, 150, 50, int(60 * intensity)),
            (255, 200, 100, int(120 * intensity)),
            (255, 240, 180, int(200 * intensity)),
            (255, 255, 240, int(255 * intensity)),
        ]
        radii = [size * 2, int(size * 1.5), size, size // 2]
    elif color_style == "ice":
        colors = [
            (100, 200, 255, int(80 * intensity)),
            (150, 220, 255, int(150 * intensity)),
            (200, 240, 255, int(220 * intensity)),
            (255, 255, 255, int(255 * intensity)),
        ]
        radii = [size * 2, int(size * 1.5), size, size // 2]
    elif color_style == "magic":
        colors = [
            (180, 80, 220, int(80 * intensity)),
            (220, 140, 240, int(150 * intensity)),
            (240, 200, 255, int(220 * intensity)),
            (255, 255, 255, int(255 * intensity)),
        ]
        radii = [size * 2, int(size * 1.5), size, size // 2]
    else:  # normal (yellow)
        colors = [
            (255, 200, 50, int(80 * intensity)),
            (255, 240, 150, int(150 * intensity)),
            (255, 255, 220, int(220 * intensity)),
            (255, 255, 255, int(255 * intensity)),
        ]
        radii = [size * 2, int(size * 1.5), size, size // 2]

    glow_size = size * 5
    glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
    for c, r in zip(colors, radii):
        pygame.draw.circle(glow_surf, c,
                           (glow_size // 2, glow_size // 2), r)
    surface.blit(glow_surf, (x - glow_size // 2, y - glow_size // 2))


def draw_sparks(surface, x, y, count=4, length=10, color=(255, 255, 200)):
    """Draw radial sparks (rays) untuk shooting effect."""
    import math as _m
    for i in range(count):
        angle = i * _m.pi * 2 / count
        lx = x + _m.cos(angle) * length
        ly = y + _m.sin(angle) * length
        pygame.draw.line(surface, color,
                         (x, y), (int(lx), int(ly)), 1)


def draw_ground_shadow(surface, x, y, w, h=6):
    """Draw shadow di bawah tower."""
    pygame.draw.ellipse(surface, (10, 10, 15),
                        (x - w, y - h // 2, w * 2, h))


def draw_stone_block_pattern(surface, x, y, w, h, palette, brick_h=5):
    """
    Draw stone brick pattern (offset per row).
    Cocok untuk main tower body.
    """
    for row in range(h // brick_h):
        block_y = y + row * brick_h + 2
        offset = brick_h if row % 2 else 0

        # Horizontal seam
        pygame.draw.line(surface, palette['STONE_DARK'],
                         (x - w + 1, block_y),
                         (x + w - 1, block_y), 1)

        # Vertical seams
        for bx in range(-w + 3 + offset, w - 2, brick_h * 2):
            pygame.draw.line(surface, palette['STONE_DARK'],
                             (x + bx, block_y),
                             (x + bx, block_y + brick_h), 1)


def draw_rivet(surface, x, y, palette):
    """Draw single metal rivet."""
    pygame.draw.rect(surface, OUTLINE, (x, y, 1, 1))
    pygame.draw.rect(surface, palette['METAL_HIGH'], (x, y, 1, 1))


def draw_metal_plate(surface, x, y, w, h, palette):
    """Draw metal plate dengan rivets di 4 corner."""
    # Plate
    pygame.draw.rect(surface, OUTLINE, (x - 1, y - 1, w + 2, h + 2))
    pygame.draw.rect(surface, palette['METAL_MID'], (x, y, w, h))
    pygame.draw.rect(surface, palette['METAL_LIGHT'], (x, y, w, 2))
    pygame.draw.rect(surface, palette['METAL_HIGH'], (x, y, w, 1))
    pygame.draw.rect(surface, palette['METAL_DARK'], (x, y + h - 1, w, 1))

    # Rivets di 4 corners
    for rx, ry in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        draw_rivet(surface, x + rx, y + ry, palette)

# ====================================================================
# archer_tower.py
# ====================================================================
class _NS_archer_tower:
    """Namespace archer_tower - isi asli tidak diubah."""

    # ================================
    # towers/archer_tower.py
    # HD Isometric Archer Tower - Original Size
    # ================================


    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')


    def _clamp_color(color):
        if len(color) == 3:
            return (max(0, min(255, int(color[0]))),
                    max(0, min(255, int(color[1]))),
                    max(0, min(255, int(color[2]))))
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_archer_tower._clamp_color(color)
        if _NS_archer_tower.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aapoly(surface, color, points):
        color = _NS_archer_tower._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    # ═══════════════════════════════════════════════════════
    # CACHE
    # ═══════════════════════════════════════════════════════

    _BASE_CACHE = {}


    # ═══════════════════════════════════════════════════════
    # PALETTE
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            return {
                'stone_darkest': (110, 115, 125),
                'stone_dark': (150, 155, 168),
                'stone_mid': (190, 195, 205),
                'stone_light': (220, 225, 235),
                'stone_lightest': (245, 248, 252),
                'stone_shadow': (75, 80, 90),
                'stone_edge': (55, 60, 70),

                'wood_darkest': (55, 32, 15),
                'wood_dark': (100, 60, 28),
                'wood_mid': (150, 95, 48),
                'wood_light': (200, 145, 82),
                'wood_high': (240, 190, 130),

                'metal_dark': (55, 60, 72),
                'metal_mid': (110, 118, 135),
                'metal_light': (175, 183, 200),
                'metal_high': (225, 232, 245),

                'gold_dark': (140, 95, 20),
                'gold_mid': (210, 160, 45),
                'gold_light': (250, 215, 90),
                'gold_high': (255, 245, 165),

                'roof_dark': (40, 70, 140),
                'roof_mid': (75, 115, 195),
                'roof_light': (125, 170, 235),
                'roof_high': (185, 220, 250),

                'red_darkest': (100, 15, 15),
                'red_dark': (170, 30, 30),
                'red_mid': (215, 55, 55),
                'red_light': (245, 95, 95),
                'red_high': (255, 155, 155),

                'green_darkest': (25, 55, 20),
                'green_dark': (50, 95, 40),
                'green_mid': (85, 145, 60),
                'green_light': (130, 190, 95),
                'green_high': (175, 225, 135),

                'skin_dark': (170, 120, 85),
                'skin_mid': (215, 165, 125),
                'skin_light': (245, 200, 165),

                'fire_dark': (180, 45, 15),
                'fire_mid': (255, 130, 40),
                'fire_light': (255, 220, 95),
                'fire_hot': (255, 250, 200),

                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (15, 12, 20),
            }
        else:
            return {
                'stone_darkest': (85, 65, 65),
                'stone_dark': (125, 100, 100),
                'stone_mid': (170, 140, 140),
                'stone_light': (205, 175, 175),
                'stone_lightest': (235, 210, 210),
                'stone_shadow': (55, 42, 42),
                'stone_edge': (38, 28, 28),

                'wood_darkest': (40, 22, 12),
                'wood_dark': (80, 45, 22),
                'wood_mid': (125, 75, 40),
                'wood_light': (170, 110, 62),
                'wood_high': (215, 158, 100),

                'metal_dark': (50, 38, 38),
                'metal_mid': (100, 78, 78),
                'metal_light': (160, 128, 128),
                'metal_high': (210, 180, 180),

                'gold_dark': (110, 72, 20),
                'gold_mid': (170, 118, 42),
                'gold_light': (215, 168, 75),
                'gold_high': (245, 208, 130),

                'roof_dark': (95, 20, 25),
                'roof_mid': (155, 45, 50),
                'roof_light': (210, 80, 85),
                'roof_high': (245, 135, 140),

                'red_darkest': (60, 10, 12),
                'red_dark': (110, 22, 25),
                'red_mid': (165, 42, 45),
                'red_light': (215, 75, 78),
                'red_high': (245, 130, 130),

                'green_darkest': (55, 15, 20),
                'green_dark': (95, 25, 30),
                'green_mid': (145, 45, 50),
                'green_light': (190, 75, 80),
                'green_high': (225, 115, 120),

                'skin_dark': (150, 105, 85),
                'skin_mid': (190, 145, 125),
                'skin_light': (220, 180, 160),

                'fire_dark': (140, 20, 90),
                'fire_mid': (220, 55, 180),
                'fire_light': (255, 135, 240),
                'fire_hot': (255, 220, 255),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (10, 5, 8),
            }


    # ═══════════════════════════════════════════════════════
    # LEVEL CONFIG
    # ═══════════════════════════════════════════════════════

    LEVEL_CONFIGS = {
        1: {'tower_w': 46, 'tower_h': 38, 'annex': False,
            'roof_center': False, 'num_flags': 2, 'has_shield': False,
            'num_torches': 1, 'archer_tier': 'basic'},
        2: {'tower_w': 50, 'tower_h': 42, 'annex': True,
            'roof_center': False, 'num_flags': 2, 'has_shield': True,
            'num_torches': 1, 'archer_tier': 'ranger'},
        3: {'tower_w': 54, 'tower_h': 46, 'annex': True,
            'roof_center': False, 'num_flags': 4, 'has_shield': True,
            'num_torches': 2, 'archer_tier': 'marksman'},
        4: {'tower_w': 58, 'tower_h': 52, 'annex': True,
            'roof_center': True, 'num_flags': 4, 'has_shield': True,
            'num_torches': 2, 'archer_tier': 'elite'},
        5: {'tower_w': 62, 'tower_h': 56, 'annex': True,
            'roof_center': True, 'num_flags': 4, 'has_shield': True,
            'num_torches': 2, 'archer_tier': 'elite_twin'},
        6: {'tower_w': 68, 'tower_h': 62, 'annex': True,
            'roof_center': True, 'num_flags': 4, 'has_shield': True,
            'num_torches': 2, 'archer_tier': 'legendary'},
    }


    # ═══════════════════════════════════════════════════════
    # HELPER: Get archer bow position in world coordinates
    # ═══════════════════════════════════════════════════════

    def get_archer_bow_position(tower_x, tower_y, level, face=1):
        """
        Return real-world (x, y) position of archer's bow
        for bullet spawn point.

        Args:
            tower_x, tower_y: world position of tower center
            level: tower level (1-6)
            face: 1 for right, -1 for left

        Returns:
            (bow_x, bow_y) - world coordinates for bullet spawn
        """
        lvl = max(1, min(6, level))
        config = _NS_archer_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        # Calculate archer position in canvas (same logic as _NS_archer_tower.draw_archer)
        canvas_cy = ch - 12  # ground base y in canvas
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5
        archer_y_canvas = tower_top_y_canvas - 5  # 5px above platform
        archer_x_canvas = cw // 2

        # Bow position in canvas (relative to archer center)
        # From _NS_archer_tower._draw_bow: bow_x = bx + (body_w + 2 if face > 0 else -3)
        # body_w = int(9 * 1.0) = 9
        body_w = 9
        bx_canvas = archer_x_canvas - body_w // 2
        bow_x_canvas = bx_canvas + (body_w + 2 if face > 0 else -3)
        bow_y_canvas = archer_y_canvas - 4 + 3  # by + 3, by = cy - 4

        # Convert canvas → scaled position
        new_h = int(ch * SCALE)

        # Final render offset (from _NS_archer_tower.draw_archer)
        final_y_offset = -new_h + int(30 * SCALE)  # = -115 + 21 = -94

        # Scale from canvas to world
        bow_x_world = tower_x + (bow_x_canvas - cw // 2) * SCALE
        bow_y_world = tower_y + final_y_offset + bow_y_canvas * SCALE

        return int(bow_x_world), int(bow_y_world)


    def get_archer_top_y(tower_x, tower_y, level):
        """
        Return real-world Y position of archer's HEAD TOP
        (untuk placement HP bar di atasnya).

        Args:
            tower_x: not used (untuk konsistensi)
            tower_y: world Y position of tower center
            level: tower level (1-6)

        Returns:
            top_y - world Y coordinate of archer's head top
        """
        lvl = max(1, min(6, level))
        config = _NS_archer_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        # Same calculation as _NS_archer_tower.draw_archer
        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5
        archer_y_canvas = tower_top_y_canvas - 5

        # Archer HEAD position in canvas
        # From _NS_archer_tower._draw_archer: hy = cy - int(11 * scale)
        # scale = 1.0 for main archer, but legendary has extra offset
        head_scale = 1.0
        archer_head_top_canvas = archer_y_canvas - int(11 * head_scale)

        # Untuk lvl 6 (legendary), ada mushroom crown/wings di atas helmet
        # Kasih extra padding 5px
        if lvl == 6:
            archer_head_top_canvas -= 8
        elif lvl >= 4:
            # Elite helmet ada horns/spikes
            archer_head_top_canvas -= 4

        # Convert canvas → world coordinates
        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)  # = -94

        top_y_world = tower_y + final_y_offset + archer_head_top_canvas * SCALE

        return int(top_y_world)
    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_archer(surface, tower, x, y, size):
        """Main archer tower render - CACHED"""
        from sprite_cache import get_cached_sprite_cropped

        lvl = max(1, min(6, tower.level))

        # Tentukan state untuk cache
        if tower.shoot_flash_timer > 0:
            flash_frame = tower.shoot_flash_timer // 2
            state = f"shoot_{flash_frame}"
        else:
            state = "idle"

        # Facing direction
        face = 1
        if tower.target and tower.target.alive:
            face = 1 if tower.target.x > tower.x else -1

        cache_key = (
            'archer_full',
            tower.team,
            lvl,
            state,
            face,
            tower.timer % 4,  # flame animation frame
        )

        sprite_w = 120
        sprite_h = 140

        # Pakai versi ter-crop: canvas 120x140 tapi menara cuma
        # mengisi sebagian, sisanya piksel transparan yang percuma
        # ikut di-blit tiap frame.
        cached, anchor_x, anchor_y = get_cached_sprite_cropped(
            cache_key, sprite_w, sprite_h,
            lambda surf: _NS_archer_tower._draw_archer_full(surf, tower,
                                            sprite_w // 2,
                                            sprite_h - 30,
                                            size)
            ,
            anchor=(sprite_w // 2, sprite_h - 30)
        )

        surface.blit(cached, (x - anchor_x, y - anchor_y))


    def _draw_archer_full(surface, tower, x, y, size):
        """Original archer render"""
        palette = _NS_archer_tower._get_palette(tower.team)
        lvl = max(1, min(6, tower.level))
        config = _NS_archer_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"archer_{tower.team}_L{lvl}"
        if cache_key not in _NS_archer_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_archer_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_archer_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_archer_tower._BASE_CACHE[cache_key].copy()

        tower_top_y = ch - 12 - config['tower_h'] - 5
        archer_y = tower_top_y - 5

        _NS_archer_tower._render_archer(canvas, tower, cw // 2, archer_y, palette, config)
        _NS_archer_tower._render_effects(canvas, tower, palette, cw, ch, archer_y)

        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))

        lvl = max(1, min(6, tower.level))
        config = _NS_archer_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"archer_{tower.team}_L{lvl}"
        if cache_key not in _NS_archer_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_archer_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_archer_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_archer_tower._BASE_CACHE[cache_key].copy()

        # Character - POSITIONED CLOSER TO TOWER
        tower_top_y = ch - 12 - config['tower_h'] - 5
        archer_y = tower_top_y - 5  # Close to tower platform!

        _NS_archer_tower._render_archer(canvas, tower, cw // 2, archer_y, palette, config)

        _NS_archer_tower._render_effects(canvas, tower, palette, cw, ch, archer_y)

        # Scale down (original 0.7)
        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))


    # ═══════════════════════════════════════════════════════
    # BASE BUILDING
    # ═══════════════════════════════════════════════════════

    def _render_base(canvas, cx, cy, palette, config, lvl, timer):
        """Full tower base"""
        tw = config['tower_w']
        th = config['tower_h']

        _NS_archer_tower._draw_shadow(canvas, cx, cy + 12, tw + 30)
        _NS_archer_tower._draw_ground_base(canvas, cx, cy + 5, tw + 16, palette)

        if config['annex']:
            _NS_archer_tower._draw_annex(canvas, cx - tw // 2 - 5,
                        cy - th // 2 - 3, palette, timer)

        _NS_archer_tower._draw_main_tower(canvas, cx, cy, tw, th, palette, lvl)

        if config['has_shield']:
            _NS_archer_tower._draw_shield(canvas, cx + 4, cy - th // 2 - 3, palette)

        torch_positions = [(-tw // 2 - 3, cy - th // 4)]
        if config['num_torches'] >= 2:
            torch_positions.append((tw // 2 + 3, cy - th // 4))
        for tx, ty in torch_positions:
            _NS_archer_tower._draw_torch(canvas, cx + tx, ty, palette, timer)

        if lvl >= 2:
            _NS_archer_tower._draw_arrow_bucket_ground(canvas, cx + tw // 2 - 3, cy,
                                       palette, min(lvl + 2, 5))

        # Top rim
        top_y = cy - th - 3
        _NS_archer_tower._draw_battlements(canvas, cx, top_y, tw, palette, config)

        # Flags
        _NS_archer_tower._draw_flags(canvas, cx, top_y - 2, tw, palette,
                    config['num_flags'])

        # Platform
        plat_y = top_y - 2
        _NS_archer_tower._draw_platform(canvas, cx, plat_y, tw - 8, palette)

        # Barrel (left of platform)
        _NS_archer_tower._draw_barrel(canvas, cx - tw // 2 + 8, plat_y - 10, palette)

        # Scroll (right, lvl 3+)
        if lvl >= 3:
            _NS_archer_tower._draw_scroll(canvas, cx + tw // 2 - 8, plat_y - 3, palette)

        # Center peaked roof (lvl 4+)
        if config['roof_center']:
            _NS_archer_tower._draw_center_roof(canvas, cx + 10, plat_y - 14, palette, lvl)


    def _draw_shadow(canvas, cx, cy, width):
        for i in range(12):
            alpha = 130 - i * 10
            if alpha <= 0:
                break
            w = width - i * 3
            h = 12 - i // 2
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, w, h))
            canvas.blit(s, (cx - w // 2, cy - h // 2))


    def _draw_ground_base(canvas, cx, cy, width, palette):
        pygame.draw.ellipse(canvas, palette['stone_edge'],
                            (cx - width // 2, cy, width, 12))
        pygame.draw.ellipse(canvas, palette['stone_darkest'],
                            (cx - width // 2 + 1, cy + 1, width - 2, 10))
        pygame.draw.ellipse(canvas, palette['stone_dark'],
                            (cx - width // 2 + 2, cy + 2, width - 4, 8))
        pygame.draw.ellipse(canvas, palette['stone_mid'],
                            (cx - width // 2 + 3, cy + 3, width - 6, 6))

        random.seed(42)
        for _ in range(12):
            px = cx + random.randint(-width // 2 + 4, width // 2 - 4)
            py = cy + random.randint(2, 8)
            s = random.randint(2, 4)
            pygame.draw.rect(canvas, palette['stone_light'],
                             (px, py, s, s // 2 + 1))
            pygame.draw.rect(canvas, palette['stone_lightest'],
                             (px, py, s - 1, 1))
        random.seed()


    def _draw_main_tower(canvas, cx, cy, w, h, palette, lvl):
        """Stone tower with chunky bricks"""
        top = cy - h

        # Shadow
        for i in range(3):
            alpha = 130 - i * 30
            s = pygame.Surface((w + i * 2, h + i), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, alpha),
                             (0, 0, w + i * 2, h + i),
                             border_radius=6)
            canvas.blit(s, (cx - w // 2 + i, top + 2 + i))

        # Main body (cylinder shading)
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - w // 2, top, w, h), border_radius=6)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - w // 2, top, w - 2, h), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - w // 2, top, w - 4, h - 1), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - w // 2, top, w - 7, h - 3), border_radius=4)
        # Left highlight
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - w // 2 + 2, top + 1, 8, h - 4),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (cx - w // 2 + 3, top + 2, 4, h - 6),
                         border_radius=2)

        # ═══ CHUNKY BRICKS ═══
        brick_h = 8
        brick_w = 11
        num_rows = h // brick_h

        for row in range(num_rows):
            row_y = top + 5 + row * brick_h
            offset = brick_w // 2 if row % 2 else 0

            for bx in range(-w // 2 + 4 + offset, w // 2 - 3, brick_w):
                block_x = cx + bx
                curve_offset = int(math.sin(
                    (bx + w // 2) / w * math.pi) * 1.5)
                block_y = row_y - curve_offset

                _NS_archer_tower._draw_chunky_brick(canvas, block_x, block_y,
                                    brick_w - 2, brick_h - 2, palette)


    def _draw_chunky_brick(canvas, x, y, w, h, palette):
        """Individual chunky stone brick"""
        pygame.draw.rect(canvas, palette['stone_shadow'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 3, h // 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 4, 1))


    def _draw_battlements(canvas, cx, cy, tower_w, palette, config):
        """Top battlements (crenellations)"""
        rim_w = tower_w + 4

        # Bottom rim
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - rim_w // 2, cy + 2, rim_w, 8),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - rim_w // 2, cy + 2, rim_w, 7),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - rim_w // 2, cy + 2, rim_w - 1, 5),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - rim_w // 2, cy + 2, rim_w - 2, 3))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - rim_w // 2 + 1, cy + 3, rim_w - 4, 1))

        # Merlons (teeth on top)
        merlon_w = 7
        spacing = 9
        for i in range((rim_w + spacing) // spacing):
            mx = cx - rim_w // 2 + i * spacing
            if mx + merlon_w > cx + rim_w // 2:
                continue
            _NS_archer_tower._draw_merlon(canvas, mx, cy - 6, merlon_w, 8, palette)


    def _draw_merlon(canvas, x, y, w, h, palette):
        """Single crenellation"""
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 3, h - 3))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 4, h // 2))
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 5, 2))
        pygame.draw.rect(canvas, palette['shine'],
                         (x + 1, y + 1, 2, 1))


    def _draw_platform(canvas, cx, cy, w, palette):
        """Wooden top platform"""
        plat_h = 6

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - w // 2 + 1, cy + 1, w, plat_h),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - w // 2, cy, w, plat_h), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - w // 2, cy, w - 1, plat_h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - w // 2, cy, w - 2, 4))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - w // 2, cy, w - 3, 2))
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - w // 2 + 1, cy + 1, w - 5, 1))

        # Planks
        for plank_x in range(-w // 2 + 4, w // 2 - 3, 6):
            pygame.draw.line(canvas, palette['wood_darkest'],
                             (cx + plank_x, cy),
                             (cx + plank_x, cy + plat_h - 1), 1)

        # Metal corners
        for corner_x in [-w // 2, w // 2 - 3]:
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (cx + corner_x, cy, 3, plat_h))
            pygame.draw.rect(canvas, palette['metal_mid'],
                             (cx + corner_x, cy, 2, plat_h - 1))
            pygame.draw.rect(canvas, palette['metal_light'],
                             (cx + corner_x, cy, 1, 2))
            _NS_archer_tower._aacircle(canvas, palette['gold_dark'],
                      (cx + corner_x + 1, cy + plat_h // 2), 1)
            pygame.draw.rect(canvas, palette['gold_high'],
                             (cx + corner_x + 1, cy + plat_h // 2, 1, 1))


    def _draw_flags(canvas, cx, cy, tower_w, palette, num_flags):
        """Flag poles with red flags"""
        rim_w = tower_w + 4

        if num_flags == 2:
            positions = [
                (-rim_w // 2 + 4, -1, -1),
                (rim_w // 2 - 6, -1, 1),
            ]
        else:
            positions = [
                (-rim_w // 2 + 3, -1, -1),
                (rim_w // 2 - 5, -1, 1),
                (-rim_w // 2 + 8, 4, -1),
                (rim_w // 2 - 10, 4, 1),
            ]

        for pole_x_off, pole_y_off, flag_dir in positions:
            pole_x = cx + pole_x_off
            pole_bot = cy + pole_y_off
            pole_top = pole_bot - 20

            _NS_archer_tower._draw_single_flag(canvas, pole_x, pole_top, pole_bot,
                               flag_dir, palette)


    def _draw_single_flag(canvas, pole_x, pole_top, pole_bot, flag_dir, palette):
        """Single flag pole + flag"""
        # Pole
        pygame.draw.line(canvas, palette['shadow_deep'],
                         (pole_x + 1, pole_top),
                         (pole_x + 1, pole_bot), 2)
        pygame.draw.line(canvas, palette['wood_darkest'],
                         (pole_x - 1, pole_top),
                         (pole_x - 1, pole_bot), 1)
        pygame.draw.line(canvas, palette['wood_dark'],
                         (pole_x, pole_top),
                         (pole_x, pole_bot), 1)
        pygame.draw.line(canvas, palette['wood_light'],
                         (pole_x, pole_top + 2),
                         (pole_x, pole_top + 15), 1)

        # Gold ball + spear tip
        _NS_archer_tower._aacircle(canvas, palette['gold_dark'], (pole_x, pole_top - 1), 2)
        _NS_archer_tower._aacircle(canvas, palette['gold_mid'], (pole_x, pole_top - 1), 1)
        pygame.draw.rect(canvas, palette['gold_high'],
                         (pole_x - 1, pole_top - 2, 1, 1))

        _NS_archer_tower._aapoly(canvas, palette['gold_dark'], [
            (pole_x - 2, pole_top - 3),
            (pole_x, pole_top - 8),
            (pole_x + 2, pole_top - 3),
        ])
        _NS_archer_tower._aapoly(canvas, palette['gold_mid'], [
            (pole_x - 1, pole_top - 3),
            (pole_x, pole_top - 7),
            (pole_x + 1, pole_top - 3),
        ])
        _NS_archer_tower._aapoly(canvas, palette['gold_light'], [
            (pole_x - 1, pole_top - 3),
            (pole_x, pole_top - 6),
            (pole_x, pole_top - 3),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (pole_x, pole_top - 6, 1, 3))
        pygame.draw.rect(canvas, palette['shine'],
                         (pole_x, pole_top - 5, 1, 1))

        # Red flag (triangular)
        flag_y = pole_top + 2
        flag_len = 10

        _NS_archer_tower._aapoly(canvas, palette['shadow_deep'], [
            (pole_x + 1 + 1, flag_y + 1),
            (pole_x + 1 + flag_len * flag_dir + 1, flag_y + 1 + 1),
            (pole_x + 1 + int(flag_len * 0.6) * flag_dir + 1, flag_y + 5 + 1),
            (pole_x + 1 + 1, flag_y + 6 + 1),
        ])

        _NS_archer_tower._aapoly(canvas, palette['red_darkest'], [
            (pole_x + 1, flag_y),
            (pole_x + 1 + flag_len * flag_dir, flag_y + 1),
            (pole_x + 1 + int(flag_len * 0.6) * flag_dir, flag_y + 5),
            (pole_x + 1, flag_y + 6),
        ])

        _NS_archer_tower._aapoly(canvas, palette['red_dark'], [
            (pole_x + 1, flag_y + 1),
            (pole_x + 1 + (flag_len - 1) * flag_dir, flag_y + 2),
            (pole_x + 1 + int((flag_len - 1) * 0.6) * flag_dir, flag_y + 4),
            (pole_x + 1, flag_y + 5),
        ])
        _NS_archer_tower._aapoly(canvas, palette['red_mid'], [
            (pole_x + 1, flag_y + 1),
            (pole_x + 1 + int(flag_len * 0.5) * flag_dir, flag_y + 2),
            (pole_x + 1 + int(flag_len * 0.3) * flag_dir, flag_y + 4),
            (pole_x + 1, flag_y + 4),
        ])
        pygame.draw.line(canvas, palette['red_light'],
                         (pole_x + 1, flag_y + 1),
                         (pole_x + 1 + int(flag_len * 0.4) * flag_dir,
                          flag_y + 1), 1)


    def _draw_shield(canvas, cx, cy, palette):
        """Red shield with gold UP arrow"""
        sw = 13
        sh = 16

        _NS_archer_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy + 2),
            (cx + 1, cy + sh // 2 + 1),
            (cx - sw // 2 + 1, cy + 2),
        ])

        _NS_archer_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - sw // 2, cy - sh // 2),
            (cx + sw // 2, cy - sh // 2),
            (cx + sw // 2 + 1, cy + 1),
            (cx, cy + sh // 2),
            (cx - sw // 2 - 1, cy + 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 - 1, cy - sh // 2 + 1),
            (cx + sw // 2, cy + 1),
            (cx, cy + sh // 2 - 1),
            (cx - sw // 2, cy + 1),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - sw // 2 + 1, cy - sh // 2 + 1, 2, 1))

        # Red interior
        _NS_archer_tower._aapoly(canvas, palette['red_darkest'], [
            (cx - sw // 2 + 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy),
            (cx, cy + sh // 2 - 3),
            (cx - sw // 2 + 3, cy),
        ])
        _NS_archer_tower._aapoly(canvas, palette['red_dark'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - 1),
            (cx, cy + sh // 2 - 4),
            (cx - sw // 2 + 4, cy - 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['red_mid'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx - 1, cy - sh // 2 + 4),
            (cx - sw // 2 + 4, cy - 2),
        ])

        # Gold UP arrow
        ay = cy - 1
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 1, ay - 2, 2, 6))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 1, ay - 2, 2, 5))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - 1, ay - 2, 1, 4))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - 1, ay - 2, 1, 2))

        _NS_archer_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - 3, ay - 1),
            (cx, ay - 5),
            (cx + 3, ay - 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - 2, ay - 1),
            (cx, ay - 4),
            (cx + 2, ay - 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['gold_light'], [
            (cx - 2, ay - 1),
            (cx, ay - 4),
            (cx, ay - 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['gold_high'], [
            (cx - 1, ay - 2),
            (cx, ay - 4),
            (cx, ay - 2),
        ])

        # Fletching
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 2, ay + 3, 1, 2))
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx + 1, ay + 3, 1, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 2, ay + 3, 1, 1))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx + 1, ay + 3, 1, 1))


    def _draw_torch(canvas, cx, cy, palette, timer):
        """Wall torch with flame"""
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 1 + 1, cy + 1, 2, 5))
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - 1, cy, 2, 5))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - 1, cy, 1, 4))

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 3 + 1, cy - 2 + 1, 6, 3))
        pygame.draw.rect(canvas, palette['metal_dark'],
                         (cx - 3, cy - 2, 6, 3))
        pygame.draw.rect(canvas, palette['metal_mid'],
                         (cx - 3, cy - 2, 6, 2))
        pygame.draw.rect(canvas, palette['metal_light'],
                         (cx - 3, cy - 2, 5, 1))

        flicker = int(timer * 0.4) % 4
        fire_h = 6 + flicker

        _NS_archer_tower._aapoly(canvas, palette['fire_dark'], [
            (cx - 3, cy - 2),
            (cx, cy - 2 - fire_h),
            (cx + 3, cy - 2),
        ])
        _NS_archer_tower._aapoly(canvas, palette['fire_mid'], [
            (cx - 2, cy - 3),
            (cx, cy - 2 - fire_h + 1),
            (cx + 2, cy - 3),
        ])
        _NS_archer_tower._aapoly(canvas, palette['fire_light'], [
            (cx - 1, cy - 4),
            (cx, cy - 2 - fire_h + 2),
            (cx + 1, cy - 4),
        ])
        pygame.draw.rect(canvas, palette['fire_hot'],
                         (cx, cy - 5, 1, 3))

        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        for r in range(10, 3, -2):
            alpha = 45 - r * 2
            if alpha > 0:
                _NS_archer_tower._aacircle(glow, (*palette['fire_mid'], alpha),
                          (11, 11), r)
        canvas.blit(glow, (cx - 11, cy - 9))


    def _draw_arrow_bucket_ground(canvas, cx, cy, palette, num_arrows):
        """Arrow bucket on ground"""
        bw = 9
        bh = 9

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - bw // 2 + 1, cy + 1, bw, bh),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - bw // 2, cy, bw, bh), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - bw // 2, cy, bw, bh - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - bw // 2, cy, bw - 1, 5))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - bw // 2, cy, 4, 2))
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - bw // 2, cy, 2, 1))

        for band_y in [cy + 2, cy + bh - 3]:
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (cx - bw // 2, band_y, bw, 1))

        for i in range(min(num_arrows, 4)):
            arr_x = cx - 3 + i * 2
            arr_h = 5 + (i % 2) * 2
            pygame.draw.rect(canvas, palette['wood_light'],
                             (arr_x, cy - arr_h, 1, arr_h))
            _NS_archer_tower._aapoly(canvas, palette['metal_dark'], [
                (arr_x - 1, cy - arr_h),
                (arr_x + 1, cy - arr_h),
                (arr_x, cy - arr_h - 2),
            ])
            _NS_archer_tower._aapoly(canvas, palette['metal_light'], [
                (arr_x, cy - arr_h),
                (arr_x + 1, cy - arr_h),
                (arr_x, cy - arr_h - 1),
            ])
            pygame.draw.rect(canvas, palette['red_dark'],
                             (arr_x - 1, cy - 2, 2, 2))
            pygame.draw.rect(canvas, palette['red_light'],
                             (arr_x - 1, cy - 2, 1, 1))


    def _draw_barrel(canvas, cx, cy, palette):
        """Barrel with arrows on platform"""
        bw = 8
        bh = 10

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - bw // 2 + 1, cy + 1, bw, bh),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - bw // 2, cy, bw, bh), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - bw // 2, cy, bw, bh - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - bw // 2, cy, bw - 1, 5))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - bw // 2, cy, 4, 3))
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - bw // 2, cy, 2, 1))

        for band_y in [cy + 2, cy + bh - 3]:
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (cx - bw // 2, band_y, bw, 1))
            pygame.draw.rect(canvas, palette['metal_light'],
                             (cx - bw // 2, band_y, bw // 2, 1))

        for i in range(3):
            arr_x = cx - 2 + i * 2
            pygame.draw.rect(canvas, palette['wood_light'],
                             (arr_x, cy - 4, 1, 4))
            pygame.draw.rect(canvas, palette['red_dark'],
                             (arr_x - 1, cy - 5, 1, 2))
            pygame.draw.rect(canvas, palette['red_light'],
                             (arr_x - 1, cy - 4, 1, 1))


    def _draw_scroll(canvas, cx, cy, palette):
        """Rolled scroll"""
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 4 + 1, cy + 1, 8, 3),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - 4, cy, 8, 3), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - 4, cy, 8, 2), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - 4, cy, 6, 1))
        pygame.draw.rect(canvas, (250, 240, 210),
                         (cx - 3, cy + 1, 5, 1))

        _NS_archer_tower._aacircle(canvas, palette['wood_darkest'], (cx - 4, cy + 1), 2)
        _NS_archer_tower._aacircle(canvas, palette['wood_dark'], (cx - 4, cy + 1), 1)
        _NS_archer_tower._aacircle(canvas, palette['wood_darkest'], (cx + 3, cy + 1), 2)
        _NS_archer_tower._aacircle(canvas, palette['wood_dark'], (cx + 3, cy + 1), 1)


    def _draw_center_roof(canvas, cx, cy, palette, lvl):
        """Peaked roof center (lvl 4+)"""
        rw = 16
        rh = 12

        _NS_archer_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - rw // 2 + 1, cy + rh + 1),
            (cx + 1, cy - 4 + 1),
            (cx + rw // 2 + 1, cy + rh + 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['roof_dark'], [
            (cx - rw // 2, cy + rh),
            (cx, cy - 4),
            (cx + rw // 2, cy + rh),
        ])
        _NS_archer_tower._aapoly(canvas, palette['roof_mid'], [
            (cx - rw // 2 + 1, cy + rh - 1),
            (cx, cy - 3),
            (cx + rw // 2 - 1, cy + rh - 1),
        ])
        _NS_archer_tower._aapoly(canvas, palette['roof_light'], [
            (cx - rw // 2 + 1, cy + rh - 1),
            (cx, cy - 3),
            (cx - 1, cy + rh - 1),
        ])

        for tile_y in [cy + 2, cy + 6]:
            left_x = cx - int((tile_y - cy + 4) / (rh + 4) * rw // 2)
            right_x = cx + int((tile_y - cy + 4) / (rh + 4) * rw // 2)
            pygame.draw.line(canvas, palette['roof_dark'],
                             (left_x, tile_y), (right_x, tile_y), 1)

        _NS_archer_tower._aacircle(canvas, palette['gold_dark'], (cx, cy - 4), 2)
        _NS_archer_tower._aacircle(canvas, palette['gold_light'], (cx, cy - 4), 1)
        pygame.draw.rect(canvas, palette['gold_high'], (cx, cy - 5, 1, 1))


    def _draw_annex(canvas, cx, cy, palette, timer):
        """Blue tile roof annex with ladder"""
        annex_w = 14
        annex_h = 8

        # Pillars
        for pillar_x in [0, annex_w - 2]:
            pygame.draw.rect(canvas, palette['shadow_deep'],
                             (cx + pillar_x + 1, cy + 12, 2, 22))
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (cx + pillar_x, cy + 12, 2, 22))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (cx + pillar_x, cy + 12, 1, 20))
            pygame.draw.rect(canvas, palette['wood_light'],
                             (cx + pillar_x, cy + 12, 1, 8))

        # Blue tile roof
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 1 + 1, cy + 1, annex_w + 2, annex_h + 2))

        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - 2, cy + annex_h + 1, annex_w + 4, 2))
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - 2, cy + annex_h + 1, annex_w + 4, 1))

        for row in range(2):
            for col in range(4):
                tx = cx - 1 + col * 4
                ty = cy + row * 3
                pygame.draw.rect(canvas, palette['roof_dark'],
                                 (tx, ty, 4, 3))
                pygame.draw.rect(canvas, palette['roof_mid'],
                                 (tx, ty, 4, 2))
                pygame.draw.rect(canvas, palette['roof_light'],
                                 (tx, ty, 3, 1))
                pygame.draw.rect(canvas, palette['roof_high'],
                                 (tx, ty, 1, 1))

        # Gold cap
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx + annex_w // 2 - 2, cy + 1, 3, 3))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx + annex_w // 2 - 2, cy + 1, 2, 2))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx + annex_w // 2 - 2, cy + 1, 1, 1))

        # Ladder
        lx = cx + 5
        ly = cy + 14
        lh = 18

        for rail_x_off in [0, 5]:
            pygame.draw.rect(canvas, palette['shadow_deep'],
                             (lx + rail_x_off + 1, ly + 1, 1, lh))
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (lx + rail_x_off, ly, 1, lh))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (lx + rail_x_off, ly, 1, lh // 2))

        for rung_y in range(2, lh - 1, 4):
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (lx, ly + rung_y, 6, 1))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (lx, ly + rung_y, 6, 1))
            pygame.draw.rect(canvas, palette['wood_light'],
                             (lx, ly + rung_y, 3, 1))


    # ═══════════════════════════════════════════════════════
    # ARCHER CHARACTER (properly sized)
    # ═══════════════════════════════════════════════════════

    def _render_archer(canvas, tower, cx, cy, palette, config):
        """Render archer character on platform"""
        tier = config['archer_tier']

        face = 1
        if tower.target:
            face = 1 if tower.target.x > tower.x else -1

        # Base shadow (on platform)
        pygame.draw.ellipse(canvas, palette['shadow_deep'],
                            (cx - 12, cy + 12, 24, 4))

        if tier == 'elite_twin':
            _NS_archer_tower._draw_archer(canvas, cx - 8, cy, face, palette, 'elite', tower,
                         scale=0.85)
            _NS_archer_tower._draw_archer(canvas, cx + 8, cy, face, palette, 'elite', tower,
                         scale=0.85, alt_timing=True)
        elif tier == 'legendary':
            _NS_archer_tower._draw_archer(canvas, cx, cy - 2, face, palette, 'legendary',
                         tower, scale=1.0)
            _NS_archer_tower._draw_archer(canvas, cx - 11, cy + 3, face, palette, 'elite',
                         tower, scale=0.7, alt_timing=True)
            _NS_archer_tower._draw_archer(canvas, cx + 11, cy + 3, face, palette, 'elite',
                         tower, scale=0.7, alt_timing=True)
            _NS_archer_tower._draw_magic_aura(canvas, cx, cy, palette, tower.timer)
        else:
            _NS_archer_tower._draw_archer(canvas, cx, cy, face, palette, tier, tower, scale=1.0)


    def _draw_archer(canvas, cx, cy, face, palette, tier, tower,
                     scale=1.0, alt_timing=False):
        """Draw single archer character"""

        body_w = int(9 * scale)
        body_h = int(11 * scale)
        head_w = int(8 * scale)
        head_h = int(8 * scale)

        # LEGS
        leg_y = cy + int(4 * scale)
        leg_h = int(6 * scale)
        for leg_off in [-3, 1]:
            pygame.draw.rect(canvas, palette['shadow_deep'],
                             (cx + leg_off + 1, leg_y + 1, 3, leg_h))
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (cx + leg_off, leg_y, 3, leg_h))
            pygame.draw.rect(canvas, palette['wood_dark'],
                             (cx + leg_off, leg_y, 3, leg_h - 1))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (cx + leg_off, leg_y, 2, leg_h - 1))
            pygame.draw.rect(canvas, palette['wood_light'],
                             (cx + leg_off, leg_y, 1, leg_h - 2))

            # Boots
            boot_y = leg_y + leg_h - 1
            pygame.draw.rect(canvas, palette['shadow'],
                             (cx + leg_off - 1, boot_y, 4, 3))
            pygame.draw.rect(canvas, (50, 25, 12),
                             (cx + leg_off - 1, boot_y, 4, 2))
            pygame.draw.rect(canvas, (85, 50, 25),
                             (cx + leg_off - 1, boot_y, 3, 1))
            pygame.draw.rect(canvas, (120, 75, 40),
                             (cx + leg_off - 1, boot_y, 1, 1))

            if tier in ('marksman', 'elite', 'legendary'):
                pygame.draw.rect(canvas, palette['gold_mid'],
                                 (cx + leg_off + 1, boot_y, 1, 1))

        # BODY (green tunic)
        bx = cx - body_w // 2
        by = cy - int(4 * scale)

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (bx + 1, by + 1, body_w, body_h),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['green_darkest'],
                         (bx, by, body_w, body_h), border_radius=2)
        pygame.draw.rect(canvas, palette['green_dark'],
                         (bx, by, body_w - 1, body_h - 1), border_radius=2)
        pygame.draw.rect(canvas, palette['green_mid'],
                         (bx, by, body_w - 2, body_h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['green_light'],
                         (bx, by, 3, body_h - 2))
        pygame.draw.rect(canvas, palette['green_high'],
                         (bx, by, 2, body_h - 3))
        pygame.draw.rect(canvas, palette['shine'],
                         (bx, by, 1, 3))

        # ARMOR
        if tier == 'ranger':
            pygame.draw.rect(canvas, (60, 32, 18),
                             (bx, by + 2, body_w, 5))
            pygame.draw.rect(canvas, (100, 60, 30),
                             (bx, by + 2, body_w, 4))
            pygame.draw.rect(canvas, (140, 88, 45),
                             (bx, by + 2, body_w - 1, 2))
            pygame.draw.rect(canvas, (180, 120, 65),
                             (bx, by + 2, 3, 1))
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (bx + 1, by + 3, 1, 4))
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (bx + body_w - 2, by + 3, 1, 4))
        elif tier == 'marksman':
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (bx, by + 1, body_w, 7))
            pygame.draw.rect(canvas, palette['metal_mid'],
                             (bx, by + 1, body_w, 5))
            pygame.draw.rect(canvas, palette['metal_light'],
                             (bx, by + 1, body_w - 2, 2))
            pygame.draw.rect(canvas, palette['metal_high'],
                             (bx, by + 1, 3, 1))
            for rx, ry in [(0, 2), (body_w - 1, 2),
                           (0, 6), (body_w - 1, 6)]:
                pygame.draw.rect(canvas, palette['gold_mid'],
                                 (bx + rx, by + ry, 1, 1))
        elif tier == 'elite':
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (bx - 1, by, body_w + 2, 8))
            pygame.draw.rect(canvas, palette['metal_mid'],
                             (bx - 1, by, body_w + 2, 6))
            pygame.draw.rect(canvas, palette['metal_light'],
                             (bx - 1, by, body_w + 2, 3))
            pygame.draw.rect(canvas, palette['metal_high'],
                             (bx - 1, by, body_w + 2, 1))
            # Red emblem
            _NS_archer_tower._aapoly(canvas, palette['red_dark'], [
                (cx, by + 3),
                (cx + 2, by + 5),
                (cx, by + 7),
                (cx - 2, by + 5),
            ])
            _NS_archer_tower._aapoly(canvas, palette['red_mid'], [
                (cx, by + 4),
                (cx + 1, by + 5),
                (cx, by + 6),
                (cx - 1, by + 5),
            ])
            # Shoulders
            for sh_x in [-body_w // 2 - 1, body_w // 2]:
                pygame.draw.rect(canvas, palette['metal_dark'],
                                 (bx + sh_x, by, 2, 3))
                pygame.draw.rect(canvas, palette['metal_light'],
                                 (bx + sh_x, by, 1, 2))
        elif tier == 'legendary':
            pygame.draw.rect(canvas, palette['gold_dark'],
                             (bx - 1, by, body_w + 2, 8))
            pygame.draw.rect(canvas, palette['gold_mid'],
                             (bx - 1, by, body_w + 2, 6))
            pygame.draw.rect(canvas, palette['gold_light'],
                             (bx - 1, by, body_w + 2, 3))
            pygame.draw.rect(canvas, palette['gold_high'],
                             (bx - 1, by, body_w + 2, 1))
            pygame.draw.rect(canvas, palette['shine'],
                             (bx, by, body_w // 2, 1))
            # Star
            _NS_archer_tower._aapoly(canvas, (255, 255, 180), [
                (cx, by + 2),
                (cx + 1, by + 4),
                (cx + 3, by + 4),
                (cx + 2, by + 5),
                (cx + 2, by + 7),
                (cx, by + 6),
                (cx - 2, by + 7),
                (cx - 2, by + 5),
                (cx - 3, by + 4),
                (cx - 1, by + 4),
            ])
            # Spike shoulders
            for sh_x in [-body_w // 2 - 2, body_w // 2 + 1]:
                pygame.draw.rect(canvas, palette['gold_dark'],
                                 (bx + sh_x, by - 1, 2, 4))
                pygame.draw.rect(canvas, palette['gold_light'],
                                 (bx + sh_x, by - 1, 1, 3))
                _NS_archer_tower._aapoly(canvas, palette['gold_mid'], [
                    (bx + sh_x, by - 1),
                    (bx + sh_x + 1, by - 3),
                    (bx + sh_x + 2, by - 1),
                ])

        # BELT
        if tier in ('basic', 'ranger'):
            pygame.draw.rect(canvas, (40, 20, 10),
                             (bx, by + body_h - 3, body_w, 2))
            pygame.draw.rect(canvas, (70, 40, 20),
                             (bx, by + body_h - 3, body_w, 1))
            pygame.draw.rect(canvas, palette['gold_dark'],
                             (cx - 1, by + body_h - 3, 2, 2))
            pygame.draw.rect(canvas, palette['gold_light'],
                             (cx - 1, by + body_h - 3, 1, 1))

        # CAPE
        if tier in ('elite', 'legendary'):
            _NS_archer_tower._draw_cape(canvas, bx, by, body_w, body_h, face, palette)

        # HEAD
        hx = cx - head_w // 2
        hy = cy - int(11 * scale)

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (hx + 1, hy + 1, head_w, head_h),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['skin_dark'],
                         (hx, hy, head_w, head_h), border_radius=1)
        pygame.draw.rect(canvas, palette['skin_mid'],
                         (hx, hy, head_w - 1, head_h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['skin_light'],
                         (hx, hy + 1, 3, head_h - 3))

        # HOOD/HELMET
        if tier in ('basic', 'ranger', 'marksman'):
            _NS_archer_tower._draw_hood(canvas, hx, hy, head_w, head_h, cx, palette)
        elif tier == 'elite':
            _NS_archer_tower._draw_helmet_iron(canvas, hx, hy, head_w, head_h, cx, palette)
        else:
            _NS_archer_tower._draw_helmet_golden(canvas, hx, hy, head_w, head_h, cx, palette)

        # Eyes
        eye_y = hy + head_h // 2 + 1
        if tier in ('basic', 'ranger', 'marksman'):
            pygame.draw.rect(canvas, palette['shadow'],
                             (hx + 2, eye_y, 1, 1))
            pygame.draw.rect(canvas, palette['shadow'],
                             (hx + head_w - 3, eye_y, 1, 1))
            pygame.draw.rect(canvas, palette['skin_dark'],
                             (cx, eye_y + 2, 1, 1))
        elif tier == 'legendary':
            pygame.draw.rect(canvas, (120, 220, 255),
                             (hx + 2, eye_y, 1, 1))
            pygame.draw.rect(canvas, (120, 220, 255),
                             (hx + head_w - 3, eye_y, 1, 1))
        else:
            pygame.draw.rect(canvas, palette['shadow'],
                             (hx + 2, eye_y, 1, 1))
            pygame.draw.rect(canvas, palette['shadow'],
                             (hx + head_w - 3, eye_y, 1, 1))

        # QUIVER
        _NS_archer_tower._draw_quiver(canvas, bx, by, body_w, face, palette, tier)

        # BOW
        _NS_archer_tower._draw_bow(canvas, cx, cy, face, palette, tier, tower,
                  scale, alt_timing)


    def _draw_hood(canvas, hx, hy, head_w, head_h, cx, palette):
        """Green pointed hood"""
        hood_top_y = hy - 4

        _NS_archer_tower._aapoly(canvas, palette['shadow_deep'], [
            (hx - 1 + 1, hy + 1),
            (cx + 1, hood_top_y + 1),
            (hx + head_w + 1 + 1, hy + 1),
            (hx + head_w + 1 + 1, hy + head_h - 2 + 1),
            (hx - 1 + 1, hy + head_h - 2 + 1),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_darkest'], [
            (hx - 1, hy),
            (cx, hood_top_y),
            (hx + head_w + 1, hy),
            (hx + head_w + 1, hy + head_h - 2),
            (hx - 1, hy + head_h - 2),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_dark'], [
            (hx, hy),
            (cx, hood_top_y + 1),
            (hx + head_w, hy),
            (hx + head_w, hy + head_h - 3),
            (hx, hy + head_h - 3),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_mid'], [
            (hx, hy),
            (cx - 1, hood_top_y + 1),
            (hx + 2, hy + 1),
            (hx + 2, hy + head_h - 3),
            (hx, hy + head_h - 3),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_light'], [
            (hx, hy),
            (cx - 2, hood_top_y + 2),
            (hx + 1, hy + 1),
            (hx + 1, hy + head_h - 3),
            (hx, hy + head_h - 3),
        ])

        pygame.draw.rect(canvas, palette['green_high'],
                         (cx - 1, hood_top_y + 1, 1, 1))
        pygame.draw.rect(canvas, palette['shine'],
                         (cx - 1, hood_top_y + 2, 1, 1))

        # Face shadow
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (hx + 1, hy + 1, head_w - 2, 2))


    def _draw_helmet_iron(canvas, hx, hy, head_w, head_h, cx, palette):
        """Iron helmet"""
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (hx - 1 + 1, hy - 3 + 1, head_w + 2, head_h + 1))
        pygame.draw.rect(canvas, palette['metal_dark'],
                         (hx - 1, hy - 3, head_w + 2, head_h + 1))
        pygame.draw.rect(canvas, palette['metal_mid'],
                         (hx - 1, hy - 3, head_w + 2, head_h - 1))
        pygame.draw.rect(canvas, palette['metal_light'],
                         (hx - 1, hy - 3, head_w + 2, 3))
        pygame.draw.rect(canvas, palette['metal_high'],
                         (hx - 1, hy - 3, head_w // 2 + 1, 1))

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (hx, hy + head_h // 2, head_w, 2))

        for rx in [-1, head_w]:
            pygame.draw.rect(canvas, palette['gold_mid'],
                             (hx + rx, hy - 1, 1, 1))


    def _draw_helmet_golden(canvas, hx, hy, head_w, head_h, cx, palette):
        """Golden winged helmet"""
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (hx - 1 + 1, hy - 3 + 1, head_w + 2, head_h + 1))
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (hx - 1, hy - 3, head_w + 2, head_h + 1))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (hx - 1, hy - 3, head_w + 2, head_h - 1))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (hx - 1, hy - 3, head_w + 2, 3))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (hx - 1, hy - 3, head_w + 2, 1))
        pygame.draw.rect(canvas, palette['shine'],
                         (hx, hy - 3, head_w // 2, 1))

        # Wings
        for wing_side in [-1, 1]:
            wx = hx - 2 if wing_side < 0 else hx + head_w
            _NS_archer_tower._aapoly(canvas, palette['gold_dark'], [
                (wx, hy - 2),
                (wx + 3 * wing_side, hy - 5),
                (wx + 4 * wing_side, hy - 3),
                (wx + 3 * wing_side, hy - 1),
                (wx + 1 * wing_side, hy),
            ])
            _NS_archer_tower._aapoly(canvas, palette['gold_mid'], [
                (wx, hy - 2),
                (wx + 2 * wing_side, hy - 4),
                (wx + 3 * wing_side, hy - 3),
                (wx + 2 * wing_side, hy - 1),
            ])
            _NS_archer_tower._aapoly(canvas, palette['gold_light'], [
                (wx, hy - 2),
                (wx + 2 * wing_side, hy - 4),
                (wx + 1 * wing_side, hy - 2),
            ])

        # Central jewel
        pygame.draw.rect(canvas, palette['shadow'],
                         (cx - 1, hy - 5, 3, 3))
        _NS_archer_tower._aapoly(canvas, (200, 40, 40), [
            (cx, hy - 5),
            (cx + 1, hy - 4),
            (cx, hy - 3),
            (cx - 1, hy - 4),
        ])
        pygame.draw.rect(canvas, (255, 100, 100),
                         (cx, hy - 5, 1, 1))

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (hx, hy + head_h // 2, head_w, 2))


    def _draw_cape(canvas, bx, by, body_w, body_h, face, palette):
        """Green cape"""
        cape_x = bx + (body_w if face < 0 else -3)

        _NS_archer_tower._aapoly(canvas, palette['shadow_deep'], [
            (cape_x + 1, by + 1),
            (cape_x + 1 + int(2 * face), by + body_h + 3),
            (cape_x + 1 + int(3 * face), by + body_h + 6),
            (cape_x + 1 - int(2 * face), by + body_h + 5),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_darkest'], [
            (cape_x, by),
            (cape_x + int(2 * face), by + body_h + 2),
            (cape_x + int(3 * face), by + body_h + 5),
            (cape_x - int(2 * face), by + body_h + 4),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_dark'], [
            (cape_x, by + 1),
            (cape_x + int(1 * face), by + body_h + 1),
            (cape_x + int(2 * face), by + body_h + 3),
            (cape_x - int(1 * face), by + body_h + 3),
        ])

        _NS_archer_tower._aapoly(canvas, palette['green_mid'], [
            (cape_x, by + 1),
            (cape_x, by + body_h + 1),
            (cape_x - int(1 * face), by + body_h),
        ])


    def _draw_quiver(canvas, bx, by, body_w, face, palette, tier):
        """Quiver on back"""
        qx = bx + (-3 if face > 0 else body_w + 1)
        qy = by - 1

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (qx + 1, qy + 1, 3, 8))
        pygame.draw.rect(canvas, (40, 20, 10),
                         (qx, qy, 3, 8))
        pygame.draw.rect(canvas, (80, 45, 20),
                         (qx, qy, 3, 7))
        pygame.draw.rect(canvas, (110, 65, 30),
                         (qx, qy, 2, 6))
        pygame.draw.rect(canvas, (150, 90, 45),
                         (qx, qy, 1, 4))

        if tier in ('elite', 'legendary'):
            pygame.draw.rect(canvas, palette['gold_dark'],
                             (qx, qy + 4, 3, 1))
            pygame.draw.rect(canvas, palette['gold_light'],
                             (qx, qy + 4, 2, 1))

        num = {'basic': 3, 'ranger': 3, 'marksman': 4,
               'elite': 5, 'legendary': 6}.get(tier, 3)

        for i in range(num):
            arr_x = qx + i % 3
            arr_y_off = i // 3
            pygame.draw.rect(canvas, palette['wood_light'],
                             (arr_x, qy - 2 - arr_y_off, 1, 3))
            if tier == 'legendary':
                pygame.draw.rect(canvas, palette['gold_light'],
                                 (arr_x, qy - 3 - arr_y_off, 1, 2))
            elif tier == 'elite':
                pygame.draw.rect(canvas, (255, 100, 30),
                                 (arr_x, qy - 3 - arr_y_off, 1, 2))
                pygame.draw.rect(canvas, (255, 200, 50),
                                 (arr_x, qy - 3 - arr_y_off, 1, 1))
            else:
                pygame.draw.rect(canvas, palette['red_dark'],
                                 (arr_x, qy - 3 - arr_y_off, 1, 2))
                pygame.draw.rect(canvas, palette['red_light'],
                                 (arr_x, qy - 3 - arr_y_off, 1, 1))


    def _draw_bow(canvas, cx, cy, face, palette, tier, tower, scale=1.0,
                  alt_timing=False):
        """Bow with animation"""
        bow_size = int(9 * scale)
        body_w = int(9 * scale)
        bx = cx - body_w // 2
        by = cy - int(4 * scale)

        bow_x = bx + (body_w + 2 if face > 0 else -3)
        bow_y = by + 3

        if tier == 'basic':
            bow_d = palette['wood_darkest']
            bow_m = palette['wood_dark']
            bow_l = palette['wood_mid']
        elif tier == 'ranger':
            bow_d = (40, 20, 10)
            bow_m = (85, 55, 25)
            bow_l = (135, 90, 55)
        elif tier == 'marksman':
            bow_d = palette['metal_dark']
            bow_m = palette['metal_mid']
            bow_l = palette['metal_light']
        elif tier == 'elite':
            bow_d = (50, 28, 15)
            bow_m = (105, 68, 38)
            bow_l = palette['metal_light']
        else:
            bow_d = palette['gold_dark']
            bow_m = palette['gold_mid']
            bow_l = palette['gold_high']

        # Bow curve
        for i in range(-bow_size, bow_size + 1):
            curve = int(math.cos(i / bow_size * math.pi / 2) * 3)
            curve_x = bow_x + (curve - 3) * face
            curve_y = bow_y + i

            if -bow_size + 1 <= i <= bow_size - 1:
                pygame.draw.rect(canvas, palette['shadow_deep'],
                                 (curve_x + 1, curve_y + 1, 2, 1))
                pygame.draw.rect(canvas, bow_d,
                                 (curve_x, curve_y, 2, 1))
                pygame.draw.rect(canvas, bow_m,
                                 (curve_x + (1 if face < 0 else 0),
                                  curve_y, 1, 1))
                if abs(i) < bow_size - 3:
                    pygame.draw.rect(canvas, bow_l,
                                     (curve_x + (1 if face < 0 else 0),
                                      curve_y, 1, 1))

        # Bow tips
        for tip_y in [bow_y - bow_size, bow_y + bow_size]:
            pygame.draw.rect(canvas, bow_d,
                             (bow_x - 2 * face, tip_y - 1, 2, 2))
            pygame.draw.rect(canvas, bow_m,
                             (bow_x - 2 * face, tip_y - 1, 1, 1))

        if tier == 'legendary':
            pygame.draw.rect(canvas, palette['shine'],
                             (bow_x - 1 * face, bow_y - bow_size + 2, 1, 3))
            pygame.draw.rect(canvas, palette['shine'],
                             (bow_x - 1 * face, bow_y + bow_size - 4, 1, 3))

        # Bowstring
        string_x = bow_x - 3 * face
        string_top = bow_y - bow_size + 1
        string_bot = bow_y + bow_size - 1

        timing = 12 if alt_timing else 0
        is_shooting = (tower.timer + timing) > tower.attack_cooldown - 20
        string_off = -4 * face if is_shooting else 0

        if string_off != 0:
            pygame.draw.line(canvas, palette['stone_lightest'],
                             (string_x, string_top),
                             (string_x + string_off, bow_y), 1)
            pygame.draw.line(canvas, palette['stone_lightest'],
                             (string_x + string_off, bow_y),
                             (string_x, string_bot), 1)
        else:
            pygame.draw.line(canvas, palette['stone_lightest'],
                             (string_x, string_top),
                             (string_x, string_bot), 1)

        # Arrow
        if is_shooting:
            arr_start = string_x + string_off
            arr_end = string_x + int(8 * scale) * face

            pygame.draw.line(canvas, palette['wood_light'],
                             (arr_start, bow_y),
                             (arr_end, bow_y), 1)
            pygame.draw.line(canvas, palette['wood_high'],
                             (arr_start, bow_y + 1),
                             (arr_end, bow_y + 1), 1)

            if tier == 'elite':
                _NS_archer_tower._draw_flame_head(canvas, arr_end, bow_y, face, palette,
                                  tower.timer)
            elif tier == 'legendary':
                _NS_archer_tower._draw_magic_head(canvas, arr_end, bow_y, face, palette,
                                  tower.timer)
            else:
                _NS_archer_tower._aapoly(canvas, palette['metal_dark'], [
                    (arr_end, bow_y - 1),
                    (arr_end + 3 * face, bow_y),
                    (arr_end, bow_y + 2),
                ])
                _NS_archer_tower._aapoly(canvas, palette['metal_light'], [
                    (arr_end, bow_y),
                    (arr_end + 2 * face, bow_y),
                    (arr_end, bow_y + 1),
                ])

            feather = palette['red_dark']
            if tier == 'elite':
                feather = (255, 100, 30)
            elif tier == 'legendary':
                feather = (150, 100, 255)

            pygame.draw.rect(canvas, feather,
                             (arr_start - face, bow_y - 1, 1, 3))


    def _draw_flame_head(canvas, x, y, face, palette, timer):
        _NS_archer_tower._aapoly(canvas, palette['metal_dark'], [
            (x, y - 1),
            (x + 3 * face, y),
            (x, y + 2),
        ])
        _NS_archer_tower._aapoly(canvas, palette['metal_light'], [
            (x, y),
            (x + 2 * face, y),
            (x, y + 1),
        ])

        flicker = int(timer * 0.5) % 4
        for i in range(3):
            fx = x + (i * 2 * face)
            fs = 2 - i // 2
            _NS_archer_tower._aapoly(canvas, (200, 60, 20), [
                (fx - 1, y - fs - flicker // 2),
                (fx + 2 * face, y),
                (fx - 1, y + fs + flicker // 2),
            ])
            _NS_archer_tower._aapoly(canvas, (255, 150, 30), [
                (fx, y - fs + 1),
                (fx + 1 * face, y),
                (fx, y + fs - 1),
            ])
            pygame.draw.rect(canvas, (255, 240, 100), (fx, y, 1, 1))

        glow = pygame.Surface((14, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 100, 30, 100), (0, 0, 14, 8))
        canvas.blit(glow, (x - 3, y - 4))


    def _draw_magic_head(canvas, x, y, face, palette, timer):
        _NS_archer_tower._aapoly(canvas, (80, 40, 150), [
            (x, y - 1),
            (x + 3 * face, y),
            (x, y + 2),
        ])
        _NS_archer_tower._aapoly(canvas, (150, 100, 220), [
            (x, y),
            (x + 2 * face, y),
            (x, y + 1),
        ])
        pygame.draw.rect(canvas, (220, 200, 255),
                         (x + 1 * face, y, 1, 1))

        pulse = math.sin(timer * 0.2) * 0.5 + 0.5
        for i in range(3):
            angle = timer * 0.15 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * 3)
            sy = y + int(math.sin(angle) * 2)
            pygame.draw.rect(canvas, (200, 150, 255), (sx, sy, 1, 1))

        glow = pygame.Surface((14, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (150, 100, 255, int(120 * pulse)),
                            (0, 0, 14, 8))
        canvas.blit(glow, (x - 3, y - 4))


    def _draw_magic_aura(canvas, cx, cy, palette, timer):
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        for i in range(3):
            r = 22 + i * 4 + int(pulse * 2)
            alpha = int(40 * (1 - i / 3) * pulse)
            if alpha > 0:
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (150, 100, 255, alpha),
                                   (r, r), r, 2)
                canvas.blit(s, (cx - r, cy - r))

        for i in range(4):
            angle = timer * 0.05 + i * math.pi / 2
            rx = cx + int(math.cos(angle) * 18)
            ry = cy + int(math.sin(angle) * 13)

            pygame.draw.rect(canvas, (100, 60, 200),
                             (rx - 1, ry - 1, 3, 3))
            pygame.draw.rect(canvas, (200, 150, 255),
                             (rx, ry, 1, 1))

            glow = pygame.Surface((8, 8), pygame.SRCALPHA)
            _NS_archer_tower._aacircle(glow, (150, 100, 255, 100), (4, 4), 3)
            canvas.blit(glow, (rx - 4, ry - 4))


    def _render_effects(canvas, tower, palette, cw, ch, archer_y):
        """Shooting flash"""
        if tower.shoot_flash_timer > 0:
            intensity = tower.shoot_flash_timer / 8.0
            face = 1 if tower.target and tower.target.x > tower.x else -1
            cx = cw // 2

            bow_x = cx + (8 * face)
            bow_y = archer_y + 3

            size = int(6 * intensity)
            if size > 0:
                flash = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                _NS_archer_tower._aacircle(flash, (*palette['fire_light'], int(120 * intensity)),
                          (size * 2, size * 2), size * 2)
                _NS_archer_tower._aacircle(flash, (*palette['fire_hot'], int(200 * intensity)),
                          (size * 2, size * 2), size)
                canvas.blit(flash, (bow_x - size * 2, bow_y - size * 2))

# ====================================================================
# cannon_tower.py
# ====================================================================
class _NS_cannon_tower:
    """Namespace cannon_tower - isi asli tidak diubah."""

    # ================================
    # towers/cannon_tower.py
    # HD Isometric Cannon Tower - Kingdom Rush Style
    # ================================


    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')


    def _clamp_color(color):
        if len(color) == 3:
            return (max(0, min(255, int(color[0]))),
                    max(0, min(255, int(color[1]))),
                    max(0, min(255, int(color[2]))))
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_cannon_tower._clamp_color(color)
        if _NS_cannon_tower.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aapoly(surface, color, points):
        color = _NS_cannon_tower._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    # ═══════════════════════════════════════════════════════
    # CACHE
    # ═══════════════════════════════════════════════════════

    _BASE_CACHE = {}


    # ═══════════════════════════════════════════════════════
    # PALETTE
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            return {
                'stone_darkest': (110, 115, 125),
                'stone_dark': (150, 155, 168),
                'stone_mid': (190, 195, 205),
                'stone_light': (220, 225, 235),
                'stone_lightest': (245, 248, 252),
                'stone_shadow': (75, 80, 90),
                'stone_edge': (55, 60, 70),

                'wood_darkest': (55, 32, 15),
                'wood_dark': (100, 60, 28),
                'wood_mid': (150, 95, 48),
                'wood_light': (200, 145, 82),
                'wood_high': (240, 190, 130),

                # Cannon iron (dark black metal)
                'iron_darkest': (18, 20, 25),
                'iron_dark': (40, 45, 55),
                'iron_mid': (75, 82, 95),
                'iron_light': (130, 138, 155),
                'iron_high': (185, 192, 210),

                'metal_dark': (55, 60, 72),
                'metal_mid': (110, 118, 135),
                'metal_light': (175, 183, 200),
                'metal_high': (225, 232, 245),

                # Gold (bright brass)
                'gold_darkest': (95, 60, 12),
                'gold_dark': (150, 105, 25),
                'gold_mid': (210, 160, 50),
                'gold_light': (250, 215, 90),
                'gold_high': (255, 245, 165),

                # Blue tiles (annex roof)
                'roof_dark': (40, 70, 140),
                'roof_mid': (75, 115, 195),
                'roof_light': (125, 170, 235),
                'roof_high': (185, 220, 250),

                # Blue shield (with gold cross)
                'shield_darkest': (25, 45, 100),
                'shield_dark': (45, 80, 155),
                'shield_mid': (75, 120, 200),
                'shield_light': (125, 170, 235),

                # Snow drips (on merlons)
                'snow_dark': (200, 220, 235),
                'snow_mid': (230, 240, 250),
                'snow_light': (250, 253, 255),

                # Cannonball (dark iron)
                'ball_dark': (25, 28, 35),
                'ball_mid': (55, 62, 75),
                'ball_light': (95, 105, 120),
                'ball_shine': (170, 180, 195),

                # Fire (torch flame)
                'fire_dark': (180, 45, 15),
                'fire_mid': (255, 130, 40),
                'fire_light': (255, 220, 95),
                'fire_hot': (255, 250, 200),

                # Smoke (post-shoot)
                'smoke_dark': (60, 60, 70),
                'smoke_mid': (140, 140, 155),
                'smoke_light': (200, 200, 210),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (15, 12, 20),
            }
        else:
            # RED TEAM (dark cursed)
            return {
                'stone_darkest': (85, 65, 65),
                'stone_dark': (125, 100, 100),
                'stone_mid': (170, 140, 140),
                'stone_light': (205, 175, 175),
                'stone_lightest': (235, 210, 210),
                'stone_shadow': (55, 42, 42),
                'stone_edge': (38, 28, 28),

                'wood_darkest': (40, 22, 12),
                'wood_dark': (80, 45, 22),
                'wood_mid': (125, 75, 40),
                'wood_light': (170, 110, 62),
                'wood_high': (215, 158, 100),

                'iron_darkest': (25, 15, 18),
                'iron_dark': (50, 30, 32),
                'iron_mid': (90, 60, 62),
                'iron_light': (140, 105, 108),
                'iron_high': (195, 160, 162),

                'metal_dark': (50, 38, 38),
                'metal_mid': (100, 78, 78),
                'metal_light': (160, 128, 128),
                'metal_high': (210, 180, 180),

                'gold_darkest': (75, 42, 8),
                'gold_dark': (125, 78, 20),
                'gold_mid': (180, 122, 42),
                'gold_light': (225, 172, 72),
                'gold_high': (250, 210, 130),

                'roof_dark': (95, 20, 25),
                'roof_mid': (155, 45, 50),
                'roof_light': (210, 80, 85),
                'roof_high': (245, 135, 140),

                'shield_darkest': (75, 15, 20),
                'shield_dark': (130, 30, 35),
                'shield_mid': (185, 55, 60),
                'shield_light': (225, 100, 105),

                'snow_dark': (200, 210, 220),
                'snow_mid': (225, 232, 240),
                'snow_light': (245, 248, 252),

                'ball_dark': (30, 15, 18),
                'ball_mid': (60, 35, 38),
                'ball_light': (105, 75, 78),
                'ball_shine': (175, 145, 148),

                'fire_dark': (140, 20, 90),
                'fire_mid': (220, 55, 180),
                'fire_light': (255, 135, 240),
                'fire_hot': (255, 220, 255),

                'smoke_dark': (60, 45, 55),
                'smoke_mid': (140, 115, 125),
                'smoke_light': (200, 175, 185),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (10, 5, 8),
            }


    # ═══════════════════════════════════════════════════════
    # LEVEL CONFIG
    # ═══════════════════════════════════════════════════════

    LEVEL_CONFIGS = {
        1: {'tower_w': 46, 'tower_h': 38, 'annex': False,
            'has_shield': False, 'num_torches': 1,
            'has_ammo': False, 'snow_drips': False,
            'cannon_tier': 'basic'},
        2: {'tower_w': 50, 'tower_h': 42, 'annex': True,
            'has_shield': True, 'num_torches': 1,
            'has_ammo': False, 'snow_drips': False,
            'cannon_tier': 'basic'},
        3: {'tower_w': 54, 'tower_h': 46, 'annex': True,
            'has_shield': True, 'num_torches': 2,
            'has_ammo': True, 'snow_drips': False,
            'cannon_tier': 'bronze'},
        4: {'tower_w': 58, 'tower_h': 52, 'annex': True,
            'has_shield': True, 'num_torches': 2,
            'has_ammo': True, 'snow_drips': True,
            'cannon_tier': 'iron'},
        5: {'tower_w': 62, 'tower_h': 56, 'annex': True,
            'has_shield': True, 'num_torches': 2,
            'has_ammo': True, 'snow_drips': True,
            'cannon_tier': 'twin'},
        6: {'tower_w': 68, 'tower_h': 62, 'annex': True,
            'has_shield': True, 'num_torches': 2,
            'has_ammo': True, 'snow_drips': True,
            'cannon_tier': 'legendary'},
    }


    # ═══════════════════════════════════════════════════════
    # HELPER: Get cannon muzzle position for bullet spawn
    # ═══════════════════════════════════════════════════════
    def get_cannon_muzzle_position(tower_x, tower_y, level, face=1,
                                   recoil=0):
        """Return real-world (x, y) position of cannon's muzzle"""
        lvl = max(1, min(6, level))
        config = _NS_cannon_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5
        cannon_y_canvas = tower_top_y_canvas - 2

        tier = config['cannon_tier']

        # Barrel length per tier (MATCH _NS_cannon_tower._draw_cannon_v2)
        if tier == 'basic':
            barrel_len = 20
        elif tier == 'bronze':
            barrel_len = 22
        elif tier == 'twin':
            barrel_len = int(22 * 0.85)  # scaled
        elif tier == 'iron':
            barrel_len = 24
        else:  # legendary
            barrel_len = 26

        cannon_cx_canvas = cw // 2 + int(recoil / SCALE)
        # cy for cannon in _NS_cannon_tower._render_cannon is (cy - 4), and barrel_y = cy - 3
        cannon_y_offset = -4 - 3  # -7 from base
        cannon_center_y = cannon_y_canvas + cannon_y_offset

        # Muzzle at front of barrel (0.85 of barrel_len forward)
        muzzle_x_canvas = cannon_cx_canvas + int(barrel_len * 0.85) * face
        muzzle_y_canvas = cannon_center_y

        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)

        muzzle_x_world = tower_x + (muzzle_x_canvas - cw // 2) * SCALE
        muzzle_y_world = tower_y + final_y_offset + muzzle_y_canvas * SCALE

        return int(muzzle_x_world), int(muzzle_y_world)


    def get_cannon_top_y(tower_x, tower_y, level):
        """Get world Y of cannon top"""
        lvl = max(1, min(6, level))
        config = _NS_cannon_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5

        # Cannon barrel top is at (cannon_y - 3 - barrel_h/2) - 4
        # cannon_y = tower_top - 2, then -4 for _NS_cannon_tower._draw_cannon_v2 offset
        # barrel_top = barrel_y - barrel_h/2, barrel_y = cy - 3
        # so top = tower_top - 2 - 4 - 3 - barrel_h/2

        tier = config['cannon_tier']
        if tier == 'basic':
            barrel_h = 10
        elif tier == 'bronze' or tier == 'twin':
            barrel_h = 11
        elif tier == 'iron':
            barrel_h = 12
        else:
            barrel_h = 13

        cannon_top_canvas = tower_top_y_canvas - 2 - 4 - 3 - barrel_h // 2 - 3

        # Extra padding for legendary gem
        if tier == 'legendary':
            cannon_top_canvas -= 6

        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)

        top_y_world = tower_y + final_y_offset + cannon_top_canvas * SCALE
        return int(top_y_world)
    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_cannon(surface, tower, x, y, size):
        """Main cannon tower render - CACHED"""
        from sprite_cache import get_cached_sprite_cropped

        lvl = max(1, min(6, tower.level))

        if tower.shoot_flash_timer > 0:
            flash_frame = tower.shoot_flash_timer // 2
            state = f"shoot_{flash_frame}"
        else:
            state = "idle"

        face = 1
        if tower.target and tower.target.alive:
            face = 1 if tower.target.x > tower.x else -1

        recoil_frame = 0
        if tower.shoot_flash_timer > 0:
            recoil_frame = tower.shoot_flash_timer // 2

        cache_key = (
            'cannon_full',
            tower.team,
            lvl,
            state,
            face,
            recoil_frame,
            tower.timer % 4,
        )

        sprite_w = 120
        sprite_h = 140

        # Pakai versi ter-crop: canvas 120x140 tapi menara cuma
        # mengisi sebagian, sisanya piksel transparan yang percuma
        # ikut di-blit tiap frame.
        cached, anchor_x, anchor_y = get_cached_sprite_cropped(
            cache_key, sprite_w, sprite_h,
            lambda surf: _NS_cannon_tower._draw_cannon_full(surf, tower,
                                            sprite_w // 2,
                                            sprite_h - 30,
                                            size)
            ,
            anchor=(sprite_w // 2, sprite_h - 30)
        )

        surface.blit(cached, (x - anchor_x, y - anchor_y))


    def _draw_cannon_full(surface, tower, x, y, size):
        """Original cannon render"""
        palette = _NS_cannon_tower._get_palette(tower.team)
        lvl = max(1, min(6, tower.level))
        config = _NS_cannon_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"cannon_{tower.team}_L{lvl}"
        if cache_key not in _NS_cannon_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_cannon_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_cannon_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_cannon_tower._BASE_CACHE[cache_key].copy()

        tower_top_y = ch - 12 - config['tower_h'] - 5
        cannon_y = tower_top_y - 2

        recoil = 0
        if tower.shoot_flash_timer > 0:
            recoil_progress = tower.shoot_flash_timer / 8.0
            face = 1
            if tower.target:
                face = 1 if tower.target.x > tower.x else -1
            recoil = int(4 * recoil_progress) * -face

        _NS_cannon_tower._render_cannon(canvas, tower, cw // 2 + recoil, cannon_y,
                       palette, config)
        _NS_cannon_tower._render_effects(canvas, tower, palette, cw, ch, cannon_y)

        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))

        lvl = max(1, min(6, tower.level))
        config = _NS_cannon_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"cannon_{tower.team}_L{lvl}"
        if cache_key not in _NS_cannon_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_cannon_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_cannon_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_cannon_tower._BASE_CACHE[cache_key].copy()

        # Cannon (animated with recoil)
        tower_top_y = ch - 12 - config['tower_h'] - 5
        cannon_y = tower_top_y - 2

        # Calculate recoil
        recoil = 0
        if tower.shoot_flash_timer > 0:
            recoil_progress = tower.shoot_flash_timer / 8.0
            face = 1
            if tower.target:
                face = 1 if tower.target.x > tower.x else -1
            recoil = int(4 * recoil_progress) * -face

        _NS_cannon_tower._render_cannon(canvas, tower, cw // 2 + recoil, cannon_y,
                       palette, config)

        # Effects (muzzle flash + smoke)
        _NS_cannon_tower._render_effects(canvas, tower, palette, cw, ch, cannon_y)

        # Scale & blit
        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))


    # ═══════════════════════════════════════════════════════
    # BASE BUILDING
    # ═══════════════════════════════════════════════════════

    def _render_base(canvas, cx, cy, palette, config, lvl, timer):
        """Full tower base"""
        tw = config['tower_w']
        th = config['tower_h']

        _NS_cannon_tower._draw_shadow(canvas, cx, cy + 12, tw + 30)
        _NS_cannon_tower._draw_ground_base(canvas, cx, cy + 5, tw + 16, palette)

        # Ammo storage (right side, lvl 3+)
        if config['has_ammo']:
            _NS_cannon_tower._draw_ammo_storage(canvas, cx + tw // 2 + 3,
                                cy - 8, palette)

        # Cannonball crate (bottom left, lvl 2+)
        if lvl >= 2:
            _NS_cannon_tower._draw_cannonball_crate(canvas, cx - tw // 2 - 4,
                                    cy - 2, palette)

        # Blue tile annex (left, lvl 2+)
        if config['annex']:
            _NS_cannon_tower._draw_annex(canvas, cx - tw // 2 - 5,
                        cy - th // 2 - 3, palette, timer)

        # Main tower
        _NS_cannon_tower._draw_main_tower(canvas, cx, cy, tw, th, palette, lvl)

        # Blue shield with gold CROSS (center - match reference)
        if config['has_shield']:
            _NS_cannon_tower._draw_shield(canvas, cx + 4, cy - th // 2 - 3, palette)

        # Wall torches
        torch_positions = [(-tw // 2 - 3, cy - th // 4)]
        if config['num_torches'] >= 2:
            torch_positions.append((tw // 2 + 3, cy - th // 4))
        for tx, ty in torch_positions:
            _NS_cannon_tower._draw_torch(canvas, cx + tx, ty, palette, timer)

        # Arched door
        _NS_cannon_tower._draw_arched_door(canvas, cx, cy - 8, palette)

        # Top rim + battlements
        top_y = cy - th - 3
        _NS_cannon_tower._draw_battlements(canvas, cx, top_y, tw, palette, config)


    def _draw_shadow(canvas, cx, cy, width):
        for i in range(12):
            alpha = 130 - i * 10
            if alpha <= 0:
                break
            w = width - i * 3
            h = 12 - i // 2
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, w, h))
            canvas.blit(s, (cx - w // 2, cy - h // 2))


    def _draw_ground_base(canvas, cx, cy, width, palette):
        pygame.draw.ellipse(canvas, palette['stone_edge'],
                            (cx - width // 2, cy, width, 12))
        pygame.draw.ellipse(canvas, palette['stone_darkest'],
                            (cx - width // 2 + 1, cy + 1, width - 2, 10))
        pygame.draw.ellipse(canvas, palette['stone_dark'],
                            (cx - width // 2 + 2, cy + 2, width - 4, 8))
        pygame.draw.ellipse(canvas, palette['stone_mid'],
                            (cx - width // 2 + 3, cy + 3, width - 6, 6))

        random.seed(42)
        for _ in range(12):
            px = cx + random.randint(-width // 2 + 4, width // 2 - 4)
            py = cy + random.randint(2, 8)
            s = random.randint(2, 4)
            pygame.draw.rect(canvas, palette['stone_light'],
                             (px, py, s, s // 2 + 1))
            pygame.draw.rect(canvas, palette['stone_lightest'],
                             (px, py, s - 1, 1))
        random.seed()


    def _draw_main_tower(canvas, cx, cy, w, h, palette, lvl):
        """Stone tower with chunky bricks"""
        top = cy - h

        # Shadow
        for i in range(3):
            alpha = 130 - i * 30
            s = pygame.Surface((w + i * 2, h + i), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, alpha),
                             (0, 0, w + i * 2, h + i),
                             border_radius=6)
            canvas.blit(s, (cx - w // 2 + i, top + 2 + i))

        # Main body
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - w // 2, top, w, h), border_radius=6)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - w // 2, top, w - 2, h), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - w // 2, top, w - 4, h - 1), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - w // 2, top, w - 7, h - 3), border_radius=4)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - w // 2 + 2, top + 1, 8, h - 4),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (cx - w // 2 + 3, top + 2, 4, h - 6),
                         border_radius=2)

        # Chunky bricks
        brick_h = 8
        brick_w = 11
        num_rows = h // brick_h

        for row in range(num_rows):
            row_y = top + 5 + row * brick_h
            offset = brick_w // 2 if row % 2 else 0

            for bx in range(-w // 2 + 4 + offset, w // 2 - 3, brick_w):
                block_x = cx + bx
                curve_offset = int(math.sin(
                    (bx + w // 2) / w * math.pi) * 1.5)
                block_y = row_y - curve_offset

                _NS_cannon_tower._draw_chunky_brick(canvas, block_x, block_y,
                                    brick_w - 2, brick_h - 2, palette)


    def _draw_chunky_brick(canvas, x, y, w, h, palette):
        """Individual chunky stone brick"""
        pygame.draw.rect(canvas, palette['stone_shadow'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 3, h // 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 4, 1))


    def _draw_battlements(canvas, cx, cy, tower_w, palette, config):
        """Top battlements with optional snow drips"""
        rim_w = tower_w + 4

        # Bottom rim (stone band)
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - rim_w // 2, cy + 2, rim_w, 8),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - rim_w // 2, cy + 2, rim_w, 7),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - rim_w // 2, cy + 2, rim_w - 1, 5),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - rim_w // 2, cy + 2, rim_w - 2, 3))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - rim_w // 2 + 1, cy + 3, rim_w - 4, 1))

        # Gold trim (top of rim)
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - rim_w // 2 + 2, cy + 8, rim_w - 4, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - rim_w // 2 + 2, cy + 8, rim_w - 5, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - rim_w // 2 + 3, cy + 8, 3, 1))

        # Merlons
        merlon_w = 7
        spacing = 9
        num_merlons = (rim_w + spacing) // spacing

        for i in range(num_merlons):
            mx = cx - rim_w // 2 + i * spacing
            if mx + merlon_w > cx + rim_w // 2:
                continue
            has_snow = config['snow_drips'] and (i % 2 == 0)
            _NS_cannon_tower._draw_merlon(canvas, mx, cy - 6, merlon_w, 8, palette,
                         has_snow=has_snow)


    def _draw_merlon(canvas, x, y, w, h, palette, has_snow=False):
        """Single crenellation with optional snow drip"""
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 3, h - 3))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 4, h // 2))
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 5, 2))
        pygame.draw.rect(canvas, palette['shine'],
                         (x + 1, y + 1, 2, 1))

        # Snow drip on top
        if has_snow:
            pygame.draw.rect(canvas, palette['snow_dark'],
                             (x, y - 2, w - 1, 2), border_radius=1)
            pygame.draw.rect(canvas, palette['snow_mid'],
                             (x, y - 2, w - 2, 1), border_radius=1)
            pygame.draw.rect(canvas, palette['snow_light'],
                             (x + 1, y - 2, w - 4, 1))
            # Drip
            pygame.draw.rect(canvas, palette['snow_mid'],
                             (x + 2, y, 1, 3))
            pygame.draw.rect(canvas, palette['snow_light'],
                             (x + 2, y, 1, 2))


    def _draw_shield(canvas, cx, cy, palette):
        """Blue shield with GOLD CROSS (match reference)"""
        sw = 13
        sh = 16

        # Shadow
        _NS_cannon_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy + 2),
            (cx + 1, cy + sh // 2 + 1),
            (cx - sw // 2 + 1, cy + 2),
        ])

        # Gold border
        _NS_cannon_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - sw // 2, cy - sh // 2),
            (cx + sw // 2, cy - sh // 2),
            (cx + sw // 2 + 1, cy + 1),
            (cx, cy + sh // 2),
            (cx - sw // 2 - 1, cy + 1),
        ])
        _NS_cannon_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 - 1, cy - sh // 2 + 1),
            (cx + sw // 2, cy + 1),
            (cx, cy + sh // 2 - 1),
            (cx - sw // 2, cy + 1),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - sw // 2 + 1, cy - sh // 2 + 1, 2, 1))

        # Blue interior
        _NS_cannon_tower._aapoly(canvas, palette['shield_darkest'], [
            (cx - sw // 2 + 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy),
            (cx, cy + sh // 2 - 3),
            (cx - sw // 2 + 3, cy),
        ])
        _NS_cannon_tower._aapoly(canvas, palette['shield_dark'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - 1),
            (cx, cy + sh // 2 - 4),
            (cx - sw // 2 + 4, cy - 1),
        ])
        _NS_cannon_tower._aapoly(canvas, palette['shield_mid'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx - 1, cy - sh // 2 + 4),
            (cx - sw // 2 + 4, cy - 2),
        ])

        # ═══ GOLD CROSS (signature - match reference) ═══
        # Vertical bar
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 1, cy - 4, 2, 8))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 1, cy - 4, 2, 7))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - 1, cy - 4, 1, 6))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - 1, cy - 4, 1, 3))

        # Horizontal bar (upper part of cross)
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 3, cy - 2, 6, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 3, cy - 2, 6, 1))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - 3, cy - 2, 4, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - 3, cy - 2, 2, 1))


    def _draw_torch(canvas, cx, cy, palette, timer):
        """Wall torch with flame"""
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 1 + 1, cy + 1, 2, 5))
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - 1, cy, 2, 5))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - 1, cy, 1, 4))

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 3 + 1, cy - 2 + 1, 6, 3))
        pygame.draw.rect(canvas, palette['metal_dark'],
                         (cx - 3, cy - 2, 6, 3))
        pygame.draw.rect(canvas, palette['metal_mid'],
                         (cx - 3, cy - 2, 6, 2))
        pygame.draw.rect(canvas, palette['metal_light'],
                         (cx - 3, cy - 2, 5, 1))

        flicker = int(timer * 0.4) % 4
        fire_h = 6 + flicker

        _NS_cannon_tower._aapoly(canvas, palette['fire_dark'], [
            (cx - 3, cy - 2),
            (cx, cy - 2 - fire_h),
            (cx + 3, cy - 2),
        ])
        _NS_cannon_tower._aapoly(canvas, palette['fire_mid'], [
            (cx - 2, cy - 3),
            (cx, cy - 2 - fire_h + 1),
            (cx + 2, cy - 3),
        ])
        _NS_cannon_tower._aapoly(canvas, palette['fire_light'], [
            (cx - 1, cy - 4),
            (cx, cy - 2 - fire_h + 2),
            (cx + 1, cy - 4),
        ])
        pygame.draw.rect(canvas, palette['fire_hot'],
                         (cx, cy - 5, 1, 3))

        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        for r in range(10, 3, -2):
            alpha = 45 - r * 2
            if alpha > 0:
                _NS_cannon_tower._aacircle(glow, (*palette['fire_mid'], alpha),
                          (11, 11), r)
        canvas.blit(glow, (cx - 11, cy - 9))


    def _draw_arched_door(canvas, cx, cy, palette):
        """Arched door with stairs"""
        door_w = 10
        door_h = 12

        # Stairs
        for step_i in range(2):
            step_y = cy + step_i * 2
            step_w = door_w + 4 + step_i * 3
            pygame.draw.rect(canvas, palette['stone_edge'],
                             (cx - step_w // 2 - 1, step_y, step_w + 2, 3))
            pygame.draw.rect(canvas, palette['stone_dark'],
                             (cx - step_w // 2, step_y, step_w, 2))
            pygame.draw.rect(canvas, palette['stone_mid'],
                             (cx - step_w // 2, step_y, step_w, 1))

        # Arch keystones
        for angle_deg in range(-90, 91, 30):
            angle = math.radians(angle_deg)
            px = cx + math.cos(angle) * (door_w // 2 + 1)
            py = cy - door_h + door_w // 2 - math.sin(angle) * (door_w // 2 + 1)
            pygame.draw.rect(canvas, palette['stone_dark'],
                             (int(px) - 1, int(py) - 1, 2, 2))
            pygame.draw.rect(canvas, palette['stone_mid'],
                             (int(px) - 1, int(py) - 1, 1, 1))

        # Door opening (dark)
        dx = cx - door_w // 2
        dy = cy - door_h
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (dx, dy + door_w // 2, door_w, door_h))
        pygame.draw.circle(canvas, palette['shadow_deep'],
                           (cx, dy + door_w // 2), door_w // 2)

        # Wooden door
        inner_w = door_w - 3
        inner_h = door_h - 2
        ix = cx - inner_w // 2
        iy = dy + door_w // 2 + 1

        pygame.draw.circle(canvas, palette['wood_darkest'],
                           (cx, iy + inner_w // 2), inner_w // 2)
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (ix, iy + inner_w // 2, inner_w, inner_h - 2))
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (ix, iy + inner_w // 2, inner_w - 1, inner_h - 3))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (ix, iy + inner_w // 2, 2, inner_h - 3))

        # Planks
        for plank_x in range(ix + 2, ix + inner_w - 1, 2):
            pygame.draw.line(canvas, palette['wood_darkest'],
                             (plank_x, iy + inner_w // 2),
                             (plank_x, iy + inner_h - 3), 1)

        # Handle
        pygame.draw.circle(canvas, palette['gold_dark'],
                           (ix + inner_w - 2, iy + inner_h // 2 + 2), 1)
        pygame.draw.rect(canvas, palette['gold_high'],
                         (ix + inner_w - 2, iy + inner_h // 2 + 2, 1, 1))


    def _draw_cannonball_crate(canvas, cx, cy, palette):
        """Wooden crate with cannonballs (bottom left)"""
        cw = 12
        ch = 8

        # Shadow
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - cw // 2 + 1, cy + 1, cw, ch))

        # Wood crate
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - cw // 2, cy, cw, ch), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - cw // 2, cy, cw - 1, ch - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - cw // 2, cy, cw - 2, 4))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - cw // 2, cy, 4, 2))
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - cw // 2, cy, 2, 1))

        # Gold trim (top rim)
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - cw // 2, cy, cw, 1))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - cw // 2, cy, cw // 2, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - cw // 2 + 1, cy, 2, 1))

        # Cannonballs (3 balls stacked)
        ball_positions = [(-3, -1), (0, -2), (3, -1)]
        for bx_off, by_off in ball_positions:
            bx = cx + bx_off
            by = cy + by_off
            # Shadow
            _NS_cannon_tower._aacircle(canvas, palette['shadow'], (bx + 1, by + 1), 2)
            # Ball
            _NS_cannon_tower._aacircle(canvas, palette['ball_dark'], (bx, by), 2)
            _NS_cannon_tower._aacircle(canvas, palette['ball_mid'], (bx, by), 2)
            _NS_cannon_tower._aacircle(canvas, palette['ball_light'], (bx - 1, by - 1), 1)
            pygame.draw.rect(canvas, palette['ball_shine'],
                             (bx - 1, by - 1, 1, 1))


    def _draw_ammo_storage(canvas, cx, cy, palette):
        """Ammo storage: barrel + sack + kettle (right side)"""
        # Powder barrel
        bw = 8
        bh = 10
        bx = cx
        by = cy

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (bx - bw // 2 + 1, by + 1, bw, bh))
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (bx - bw // 2, by, bw, bh), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (bx - bw // 2, by, bw, bh - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (bx - bw // 2, by, bw - 1, 5))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (bx - bw // 2, by, 3, 2))

        # Metal bands
        for band_y in [by + 2, by + bh - 3]:
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (bx - bw // 2, band_y, bw, 1))
            pygame.draw.rect(canvas, palette['metal_light'],
                             (bx - bw // 2, band_y, bw // 2, 1))

        # Cannonball on top of barrel
        _NS_cannon_tower._aacircle(canvas, palette['ball_dark'], (bx, by - 1), 2)
        _NS_cannon_tower._aacircle(canvas, palette['ball_mid'], (bx - 1, by - 2), 1)

        # Sack behind (offset right)
        sx = cx + 6
        sy = cy - 2
        _NS_cannon_tower._aapoly(canvas, palette['shadow_deep'], [
            (sx - 3 + 1, sy + 1),
            (sx + 3 + 1, sy + 1),
            (sx + 4 + 1, sy + 5 + 1),
            (sx - 4 + 1, sy + 5 + 1),
        ])
        _NS_cannon_tower._aapoly(canvas, (180, 165, 130), [
            (sx - 3, sy),
            (sx + 3, sy),
            (sx + 4, sy + 5),
            (sx - 4, sy + 5),
        ])
        _NS_cannon_tower._aapoly(canvas, (215, 200, 165), [
            (sx - 2, sy + 1),
            (sx + 2, sy + 1),
            (sx + 3, sy + 4),
            (sx - 3, sy + 4),
        ])
        _NS_cannon_tower._aapoly(canvas, (240, 225, 190), [
            (sx - 2, sy + 1),
            (sx, sy + 1),
            (sx - 1, sy + 3),
            (sx - 2, sy + 3),
        ])
        # Sack tie
        pygame.draw.rect(canvas, (120, 100, 60),
                         (sx - 1, sy - 1, 2, 2))
        pygame.draw.rect(canvas, palette['shine'],
                         (sx - 1, sy - 1, 1, 1))

        # Small kettle (bottom)
        kx = cx + 1
        ky = cy + 9
        _NS_cannon_tower._aacircle(canvas, palette['shadow_deep'], (kx + 1, ky + 1), 3)
        _NS_cannon_tower._aacircle(canvas, palette['iron_darkest'], (kx, ky), 3)
        _NS_cannon_tower._aacircle(canvas, palette['iron_dark'], (kx, ky), 3)
        _NS_cannon_tower._aacircle(canvas, palette['iron_mid'], (kx - 1, ky - 1), 2)
        pygame.draw.rect(canvas, palette['iron_high'],
                         (kx - 1, ky - 1, 1, 1))


    def _draw_annex(canvas, cx, cy, palette, timer):
        """Blue tile roof annex with ladder"""
        annex_w = 14
        annex_h = 8

        # Pillars
        for pillar_x in [0, annex_w - 2]:
            pygame.draw.rect(canvas, palette['shadow_deep'],
                             (cx + pillar_x + 1, cy + 12, 2, 22))
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (cx + pillar_x, cy + 12, 2, 22))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (cx + pillar_x, cy + 12, 1, 20))
            pygame.draw.rect(canvas, palette['wood_light'],
                             (cx + pillar_x, cy + 12, 1, 8))

        # Blue tile roof
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 1 + 1, cy + 1, annex_w + 2, annex_h + 2))

        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - 2, cy + annex_h + 1, annex_w + 4, 2))
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - 2, cy + annex_h + 1, annex_w + 4, 1))

        for row in range(2):
            for col in range(4):
                tx = cx - 1 + col * 4
                ty = cy + row * 3
                pygame.draw.rect(canvas, palette['roof_dark'],
                                 (tx, ty, 4, 3))
                pygame.draw.rect(canvas, palette['roof_mid'],
                                 (tx, ty, 4, 2))
                pygame.draw.rect(canvas, palette['roof_light'],
                                 (tx, ty, 3, 1))
                pygame.draw.rect(canvas, palette['roof_high'],
                                 (tx, ty, 1, 1))

        # Gold cap
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx + annex_w // 2 - 2, cy + 1, 3, 3))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx + annex_w // 2 - 2, cy + 1, 2, 2))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx + annex_w // 2 - 2, cy + 1, 1, 1))

        # Ladder
        lx = cx + 5
        ly = cy + 14
        lh = 18

        for rail_x_off in [0, 5]:
            pygame.draw.rect(canvas, palette['shadow_deep'],
                             (lx + rail_x_off + 1, ly + 1, 1, lh))
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (lx + rail_x_off, ly, 1, lh))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (lx + rail_x_off, ly, 1, lh // 2))

        for rung_y in range(2, lh - 1, 4):
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (lx, ly + rung_y, 6, 1))
            pygame.draw.rect(canvas, palette['wood_mid'],
                             (lx, ly + rung_y, 6, 1))
            pygame.draw.rect(canvas, palette['wood_light'],
                             (lx, ly + rung_y, 3, 1))


    # ═══════════════════════════════════════════════════════
    # CANNON RENDER (Top - signature)
    # ═══════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════
    # CANNON RENDER (Top - dengan perbedaan JELAS per tier)
    # ═══════════════════════════════════════════════════════

    def _render_cannon(canvas, tower, cx, cy, palette, config):
        """Render cannon on top of tower - BIG and horizontal"""
        tier = config['cannon_tier']

        face = 1
        if tower.target:
            face = 1 if tower.target.x > tower.x else -1

        # Wooden platform BIGGER
        plat_w = 36
        if tier == 'twin':
            plat_w = 42
        elif tier == 'legendary':
            plat_w = 44

        _NS_cannon_tower._draw_cannon_platform(canvas, cx, cy + 8, palette, tier, plat_w)

        # Small cannonball crate di kiri belakang (lvl 3+)
        if tier in ('bronze', 'iron', 'legendary'):
            _NS_cannon_tower._draw_small_cannonball_crate(canvas, cx - 15, cy + 4, palette)

        if tier == 'twin':
            # 2 cannons berjajar
            _NS_cannon_tower._draw_cannon_v2(canvas, cx - 8, cy - 4, face, palette, 'bronze',
                            scale=0.85, tower=tower)
            _NS_cannon_tower._draw_cannon_v2(canvas, cx + 8, cy - 4, face, palette, 'bronze',
                            scale=0.85, tower=tower, alt_timing=True)
        else:
            _NS_cannon_tower._draw_cannon_v2(canvas, cx, cy - 4, face, palette, tier,
                            scale=1.0, tower=tower)

    def _draw_cannon_platform(canvas, cx, cy, palette, tier, pw=30):
        """Wooden platform where cannon sits"""
        ph = 5

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - pw // 2 + 1, cy + 1, pw, ph),
                         border_radius=1)

        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - pw // 2, cy, pw, ph), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - pw // 2, cy, pw - 1, ph - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - pw // 2, cy, pw - 2, 3))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - pw // 2, cy, pw - 3, 1))

        # Planks
        for plank_x in range(-pw // 2 + 3, pw // 2 - 2, 5):
            pygame.draw.line(canvas, palette['wood_darkest'],
                             (cx + plank_x, cy),
                             (cx + plank_x, cy + ph - 1), 1)

    def _draw_cannon_v2(canvas, cx, cy, face, palette, tier, scale=1.0,
                        alt_timing=False, tower=None):
        """BIG HORIZONTAL cannon - match reference"""

        # ═══ TIER-SPECIFIC (BIGGER SIZES!) ═══
        if tier == 'basic':
            cannon_darkest = (35, 40, 48)
            cannon_dark = (65, 72, 85)
            cannon_mid = (110, 118, 135)
            cannon_light = (170, 178, 195)
            cannon_high = (220, 228, 240)
            barrel_len = int(20 * scale)   # BESAR!
            barrel_h = int(10 * scale)     # BESAR!
            num_bands = 0
            has_spikes = False
            has_gem = False
            has_wheels = False

        elif tier == 'bronze':
            cannon_darkest = (60, 30, 15)
            cannon_dark = (105, 55, 25)
            cannon_mid = (155, 90, 45)
            cannon_light = (200, 130, 70)
            cannon_high = (240, 175, 105)
            barrel_len = int(22 * scale)
            barrel_h = int(11 * scale)
            num_bands = 2
            has_spikes = False
            has_gem = False
            has_wheels = True

        elif tier == 'iron':
            cannon_darkest = (18, 20, 25)
            cannon_dark = (40, 45, 55)
            cannon_mid = (75, 82, 95)
            cannon_light = (130, 138, 155)
            cannon_high = (185, 192, 210)
            barrel_len = int(24 * scale)
            barrel_h = int(12 * scale)
            num_bands = 3
            has_spikes = True
            has_gem = False
            has_wheels = True

        else:  # legendary
            cannon_darkest = (15, 18, 25)
            cannon_dark = (38, 42, 55)
            cannon_mid = (75, 82, 100)
            cannon_light = (135, 145, 165)
            cannon_high = (200, 210, 230)
            barrel_len = int(26 * scale)   # SUPER BESAR!
            barrel_h = int(13 * scale)
            num_bands = 3
            has_spikes = True
            has_gem = True
            has_wheels = True

        # ═══ WOODEN CARRIAGE (support cannon) ═══
        carr_w = int(20 * scale)
        carr_h = int(10 * scale)
        carr_y = cy + 8

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - carr_w // 2 + 1, carr_y + 1, carr_w, carr_h),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - carr_w // 2, carr_y, carr_w, carr_h),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - carr_w // 2, carr_y, carr_w - 1, carr_h - 1),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - carr_w // 2, carr_y, carr_w - 2, 5))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - carr_w // 2, carr_y, carr_w - 3, 2))
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - carr_w // 2 + 1, carr_y + 1, 4, 1))

        # Gold reinforcements at corners
        if tier in ('bronze', 'iron', 'legendary'):
            for corner_x in [-carr_w // 2, carr_w // 2 - 3]:
                pygame.draw.rect(canvas, palette['gold_dark'],
                                 (cx + corner_x, carr_y, 3, carr_h))
                pygame.draw.rect(canvas, palette['gold_mid'],
                                 (cx + corner_x, carr_y, 2, carr_h - 1))
                pygame.draw.rect(canvas, palette['gold_light'],
                                 (cx + corner_x, carr_y, 1, 4))
                pygame.draw.rect(canvas, palette['gold_high'],
                                 (cx + corner_x, carr_y, 1, 2))

        # Wheels di samping carriage (lvl 3+)
        if has_wheels:
            for wheel_x_off in [-carr_w // 2 - 2, carr_w // 2 + 2]:
                wx = cx + wheel_x_off
                wy = carr_y + carr_h - 1
                _NS_cannon_tower._aacircle(canvas, palette['shadow_deep'], (wx + 1, wy + 1), 3)
                _NS_cannon_tower._aacircle(canvas, palette['iron_darkest'], (wx, wy), 3)
                _NS_cannon_tower._aacircle(canvas, palette['iron_dark'], (wx, wy), 3)
                _NS_cannon_tower._aacircle(canvas, palette['iron_mid'], (wx, wy), 2)
                # Spokes
                pygame.draw.line(canvas, palette['iron_darkest'],
                                 (wx - 2, wy), (wx + 2, wy), 1)
                pygame.draw.line(canvas, palette['iron_darkest'],
                                 (wx, wy - 2), (wx, wy + 2), 1)
                _NS_cannon_tower._aacircle(canvas, palette['gold_mid'], (wx, wy), 1)

        # ═══ CANNON PIVOT MECHANISM ═══
        pivot_y = cy + 4
        _NS_cannon_tower._aacircle(canvas, palette['shadow_deep'], (cx + 1, pivot_y + 1), 3)
        _NS_cannon_tower._aacircle(canvas, cannon_darkest, (cx, pivot_y), 3)
        _NS_cannon_tower._aacircle(canvas, cannon_dark, (cx, pivot_y), 3)
        _NS_cannon_tower._aacircle(canvas, cannon_mid, (cx - 1, pivot_y - 1), 2)

        # Gold side plates on pivot
        if tier != 'basic':
            for side in [-1, 1]:
                px = cx + side * 6
                pygame.draw.rect(canvas, palette['gold_dark'],
                                 (px - 1, pivot_y - 2, 2, 5))
                pygame.draw.rect(canvas, palette['gold_mid'],
                                 (px - 1, pivot_y - 2, 1, 4))
                pygame.draw.rect(canvas, palette['gold_high'],
                                 (px - 1, pivot_y - 2, 1, 2))

        # ═══ CANNON BARREL - HORIZONTAL BIG ═══
        barrel_y = cy - 3

        # Barrel extends far to face direction
        back_x = cx - int(barrel_len * 0.35) * face
        front_x = cx + int(barrel_len * 0.85) * face

        barrel_top = barrel_y - barrel_h // 2
        barrel_bot = barrel_y + barrel_h // 2

        if face > 0:
            bx_start = back_x
            bx_end = front_x
        else:
            bx_start = front_x
            bx_end = back_x

        # ═══ BARREL SHADOW (BIG) ═══
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (bx_start + 2, barrel_top + 2,
                          bx_end - bx_start, barrel_h),
                         border_radius=4)

        # ═══ BARREL BODY (cylinder shading - CHUNKY) ═══
        # Base darkest
        pygame.draw.rect(canvas, cannon_darkest,
                         (bx_start, barrel_top,
                          bx_end - bx_start, barrel_h),
                         border_radius=4)
        # Dark layer
        pygame.draw.rect(canvas, cannon_dark,
                         (bx_start, barrel_top,
                          bx_end - bx_start - 1, barrel_h - 1),
                         border_radius=4)
        # Mid layer
        pygame.draw.rect(canvas, cannon_mid,
                         (bx_start, barrel_top + 1,
                          bx_end - bx_start - 2, barrel_h - 3),
                         border_radius=3)
        # Light top (cylinder curve)
        pygame.draw.rect(canvas, cannon_light,
                         (bx_start + 2, barrel_top + 1,
                          bx_end - bx_start - 5, 3),
                         border_radius=2)
        # High shine
        pygame.draw.rect(canvas, cannon_high,
                         (bx_start + 3, barrel_top + 1,
                          bx_end - bx_start - 8, 2),
                         border_radius=1)
        # Shine line
        pygame.draw.rect(canvas, palette['shine'],
                         (bx_start + 4, barrel_top + 1,
                          bx_end - bx_start - 12, 1))

        # ═══ GOLD BANDS (THICK - match reference) ═══
        if num_bands > 0:
            if num_bands == 2:
                band_positions = [0.35, 0.7]
            else:  # 3 bands
                band_positions = [0.25, 0.55, 0.8]

            band_thick = 4 if tier == 'legendary' else 3

            for band_t in band_positions:
                band_x = int(bx_start + (bx_end - bx_start) * band_t)

                # Wide gold band that wraps barrel
                for w_off in range(-band_thick // 2, band_thick // 2 + 1):
                    bx_line = band_x + w_off
                    pygame.draw.rect(canvas, palette['gold_darkest'],
                                     (bx_line, barrel_top - 1, 1, barrel_h + 2))

                # Main gold
                pygame.draw.rect(canvas, palette['gold_dark'],
                                 (band_x - band_thick // 2,
                                  barrel_top - 1,
                                  band_thick, barrel_h + 2))
                pygame.draw.rect(canvas, palette['gold_mid'],
                                 (band_x - band_thick // 2,
                                  barrel_top,
                                  band_thick - 1, barrel_h))
                pygame.draw.rect(canvas, palette['gold_light'],
                                 (band_x - band_thick // 2 + 1,
                                  barrel_top + 1,
                                  1, barrel_h // 2))
                pygame.draw.rect(canvas, palette['gold_high'],
                                 (band_x - band_thick // 2 + 1,
                                  barrel_top + 1, 1, 2))
                pygame.draw.rect(canvas, palette['shine'],
                                 (band_x - band_thick // 2 + 1,
                                  barrel_top + 1, 1, 1))

        # ═══ MUZZLE BAND (front rim - THICK gold) ═══
        if tier != 'basic':
            muzzle_band_thick = 5 if tier == 'legendary' else 4
            muzzle_band_x = front_x - muzzle_band_thick * face

            for offset in range(muzzle_band_thick):
                bx_line = muzzle_band_x + offset * face
                pygame.draw.rect(canvas, palette['gold_darkest'],
                                 (bx_line, barrel_top - 1, 1, barrel_h + 2))

            # Main gold rim
            rim_x = muzzle_band_x if face > 0 else muzzle_band_x
            pygame.draw.rect(canvas, palette['gold_dark'],
                             (min(muzzle_band_x, muzzle_band_x + muzzle_band_thick * face),
                              barrel_top,
                              muzzle_band_thick, barrel_h))
            pygame.draw.rect(canvas, palette['gold_mid'],
                             (min(muzzle_band_x, muzzle_band_x + (muzzle_band_thick - 1) * face),
                              barrel_top + 1,
                              muzzle_band_thick - 1, barrel_h - 2))
            # Highlight
            pygame.draw.line(canvas, palette['gold_light'],
                             (muzzle_band_x, barrel_top + 1),
                             (muzzle_band_x, barrel_top + 4), 1)
            pygame.draw.line(canvas, palette['gold_high'],
                             (muzzle_band_x, barrel_top + 1),
                             (muzzle_band_x, barrel_top + 3), 1)
            pygame.draw.rect(canvas, palette['shine'],
                             (muzzle_band_x, barrel_top + 1, 1, 1))

        # ═══ MUZZLE OPENING (dark hole) ═══
        muzzle_x = front_x
        muzzle_y = barrel_y
        muzzle_r = max(3, barrel_h // 2 - 1)

        _NS_cannon_tower._aacircle(canvas, palette['shadow'],
                  (muzzle_x - 1 * face, muzzle_y), muzzle_r + 1)
        _NS_cannon_tower._aacircle(canvas, cannon_darkest,
                  (muzzle_x - 1 * face, muzzle_y), muzzle_r)
        # Deep dark interior
        _NS_cannon_tower._aacircle(canvas, (3, 3, 5),
                  (muzzle_x - 2 * face, muzzle_y), muzzle_r - 1)
        _NS_cannon_tower._aacircle(canvas, (0, 0, 0),
                  (muzzle_x - 2 * face, muzzle_y), muzzle_r - 2)

        # Rim highlight (visible edge)
        pygame.draw.rect(canvas, cannon_high,
                         (muzzle_x - 2 * face, muzzle_y - muzzle_r + 1, 1, 1))
        pygame.draw.rect(canvas, palette['shine'],
                         (muzzle_x - 3 * face, muzzle_y - muzzle_r + 1, 1, 1))

        # ═══ BACK END (breech) ═══
        back_end_x = bx_start + (2 if face > 0 else -2)
        _NS_cannon_tower._aacircle(canvas, palette['shadow_deep'],
                  (back_end_x + 1, barrel_y + 1), 3)
        _NS_cannon_tower._aacircle(canvas, cannon_darkest, (back_end_x, barrel_y), 3)
        _NS_cannon_tower._aacircle(canvas, cannon_dark, (back_end_x, barrel_y), 3)
        _NS_cannon_tower._aacircle(canvas, cannon_mid, (back_end_x, barrel_y), 2)
        _NS_cannon_tower._aacircle(canvas, cannon_light, (back_end_x - 1, barrel_y - 1), 1)
        pygame.draw.rect(canvas, cannon_high,
                         (back_end_x - 1, barrel_y - 1, 1, 1))

        # ═══ SPIKES on back (lvl 4+) ═══
        if has_spikes:
            for spike_i in range(3):
                sx = bx_start - (3 + spike_i * 2) * face
                sy_base = barrel_top + spike_i * 3
                spike_len = 4

                # Gold spike
                _NS_cannon_tower._aapoly(canvas, palette['shadow_deep'], [
                    (sx + 1, sy_base + 1),
                    (sx - spike_len * face + 1, sy_base + 1),
                    (sx + 1, sy_base + 2 + 1),
                ])
                _NS_cannon_tower._aapoly(canvas, palette['gold_dark'], [
                    (sx, sy_base),
                    (sx - spike_len * face, sy_base + 1),
                    (sx, sy_base + 2),
                ])
                _NS_cannon_tower._aapoly(canvas, palette['gold_mid'], [
                    (sx, sy_base),
                    (sx - (spike_len - 1) * face, sy_base + 1),
                    (sx, sy_base + 1),
                ])
                _NS_cannon_tower._aapoly(canvas, palette['gold_high'], [
                    (sx, sy_base),
                    (sx - 2 * face, sy_base + 1),
                    (sx, sy_base + 1),
                ])
                pygame.draw.rect(canvas, palette['shine'],
                                 (sx - 1 * face, sy_base, 1, 1))

        # ═══ LEGENDARY GEM on top (glowing) ═══
        if has_gem:
            pulse = math.sin((tower.timer if tower else 0) * 0.1) * 0.3 + 0.7
            gem_x = cx + int(barrel_len * 0.15) * face
            gem_y = barrel_top - 3

            # BIG glow
            for glow_r in range(7, 0, -1):
                alpha = int(160 * pulse - glow_r * 22)
                if alpha > 0:
                    glow = pygame.Surface((16, 16), pygame.SRCALPHA)
                    _NS_cannon_tower._aacircle(glow, (255, 200, 50, alpha), (8, 8), glow_r)
                    canvas.blit(glow, (gem_x - 8, gem_y - 8))

            # Gem
            _NS_cannon_tower._aacircle(canvas, palette['shadow'], (gem_x + 1, gem_y + 1), 3)
            _NS_cannon_tower._aacircle(canvas, palette['gold_darkest'], (gem_x, gem_y), 3)
            _NS_cannon_tower._aacircle(canvas, palette['gold_dark'], (gem_x, gem_y), 2)
            _NS_cannon_tower._aacircle(canvas, (255, 220, 100), (gem_x, gem_y), 1)
            pygame.draw.rect(canvas, palette['shine'], (gem_x, gem_y, 1, 1))

            # Extra ornate stars on barrel
            for extra_t in [0.45, 0.7]:
                ex = int(bx_start + (bx_end - bx_start) * extra_t)
                pygame.draw.rect(canvas, palette['gold_high'],
                                 (ex, barrel_top - 1, 1, barrel_h + 2))
                pygame.draw.rect(canvas, palette['shine'],
                                 (ex, barrel_top, 1, 1))

    def _draw_small_cannonball_crate(canvas, cx, cy, palette):
        """Small crate with cannonballs on platform"""
        cw = 7
        ch = 5

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - cw // 2 + 1, cy + 1, cw, ch))

        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - cw // 2, cy, cw, ch))
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - cw // 2, cy, cw - 1, ch - 1))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - cw // 2, cy, cw - 2, 2))

        # Gold trim
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - cw // 2, cy, cw, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - cw // 2, cy, cw // 2, 1))

        # Cannonballs
        for bx_off in [-2, 0, 2]:
            bx = cx + bx_off
            by = cy - 1
            _NS_cannon_tower._aacircle(canvas, palette['ball_dark'], (bx, by), 1)
            pygame.draw.rect(canvas, palette['ball_shine'],
                             (bx - 1, by - 1, 1, 1))


    # ═══════════════════════════════════════════════════════
    # EFFECTS (muzzle flash + smoke)
    # ═══════════════════════════════════════════════════════

    def _render_effects(canvas, tower, palette, cw, ch, cannon_y):
        """Muzzle flash + smoke puff"""
        if tower.shoot_flash_timer > 0:
            intensity = tower.shoot_flash_timer / 8.0
            face = 1 if tower.target and tower.target.x > tower.x else -1

            lvl = max(1, min(6, tower.level))
            config = _NS_cannon_tower.LEVEL_CONFIGS[lvl]
            tier = config['cannon_tier']

            if tier == 'legendary':
                barrel_len = 16
            elif tier in ('bronze', 'iron'):
                barrel_len = 15
            else:
                barrel_len = 13

            # Muzzle position in canvas
            cx = cw // 2
            muzzle_x = cx + (barrel_len + 2) * face
            muzzle_y = cannon_y - 3

            # ═══ MUZZLE FLASH (big burst) ═══
            size = int(10 * intensity)
            if size > 0:
                flash = pygame.Surface((size * 5, size * 5), pygame.SRCALPHA)
                # Outer glow
                _NS_cannon_tower._aacircle(flash, (255, 150, 50, int(100 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          int(size * 2.5))
                # Mid fire
                _NS_cannon_tower._aacircle(flash, (255, 200, 80, int(180 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          int(size * 1.5))
                # Hot core
                _NS_cannon_tower._aacircle(flash, (255, 250, 200, int(240 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          size)
                canvas.blit(flash,
                            (muzzle_x - size * 2 - size // 2,
                             muzzle_y - size * 2 - size // 2))

                # Radiating sparks
                for i in range(6):
                    angle = i * math.pi / 3 + tower.timer * 0.1
                    spark_len = size * 3
                    sx1 = muzzle_x + int(math.cos(angle) * size)
                    sy1 = muzzle_y + int(math.sin(angle) * size)
                    sx2 = muzzle_x + int(math.cos(angle) * spark_len)
                    sy2 = muzzle_y + int(math.sin(angle) * spark_len)
                    pygame.draw.line(canvas, (255, 220, 100),
                                     (sx1, sy1), (sx2, sy2), 2)
                    pygame.draw.line(canvas, palette['shine'],
                                     (sx1, sy1), (sx2, sy2), 1)

            # ═══ SMOKE PUFFS (after flash) ═══
            if intensity < 0.6:
                smoke_progress = 1 - intensity / 0.6
                for i in range(3):
                    sm_x = muzzle_x + int(6 * face * smoke_progress) + i * 3 * face
                    sm_y = muzzle_y - int(3 * smoke_progress) - i * 2
                    sm_r = int(3 + smoke_progress * 4)
                    sm_alpha = int(150 * (1 - smoke_progress))
                    if sm_alpha > 0:
                        smoke = pygame.Surface((sm_r * 3, sm_r * 3),
                                                pygame.SRCALPHA)
                        _NS_cannon_tower._aacircle(smoke,
                                  (*palette['smoke_light'], sm_alpha // 2),
                                  (sm_r * 3 // 2, sm_r * 3 // 2), sm_r)
                        _NS_cannon_tower._aacircle(smoke,
                                  (*palette['smoke_mid'], sm_alpha),
                                  (sm_r * 3 // 2, sm_r * 3 // 2),
                                  max(1, sm_r - 1))
                        canvas.blit(smoke,
                                    (sm_x - sm_r * 3 // 2,
                                     sm_y - sm_r * 3 // 2))

# ====================================================================
# ice_tower.py
# ====================================================================
class _NS_ice_tower:
    """Namespace ice_tower - isi asli tidak diubah."""

    # ================================
    # towers/ice_tower.py
    # HD Isometric Ice Tower - Kingdom Rush Style
    # ================================


    # ═══════════════════════════════════════════════════════
    # PYGAME CE FEATURE DETECTION
    # ═══════════════════════════════════════════════════════

    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')


    def _clamp_color(color):
        if len(color) == 3:
            return (max(0, min(255, int(color[0]))),
                    max(0, min(255, int(color[1]))),
                    max(0, min(255, int(color[2]))))
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ice_tower._clamp_color(color)
        if _NS_ice_tower.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aapoly(surface, color, points):
        color = _NS_ice_tower._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    # ═══════════════════════════════════════════════════════
    # CACHE
    # ═══════════════════════════════════════════════════════

    _BASE_CACHE = {}


    # ═══════════════════════════════════════════════════════
    # PALETTE (Ice/Frost theme)
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            return {
                # Stone (blue-tinted gray)
                'stone_darkest': (95, 110, 130),
                'stone_dark': (135, 150, 175),
                'stone_mid': (175, 190, 215),
                'stone_light': (210, 225, 240),
                'stone_lightest': (240, 248, 255),
                'stone_shadow': (65, 78, 100),
                'stone_edge': (45, 55, 75),

                # Crystal (BRIGHT BLUE - signature!)
                'crystal_darkest': (25, 80, 160),
                'crystal_dark': (55, 130, 220),
                'crystal_mid': (100, 180, 250),
                'crystal_light': (160, 220, 255),
                'crystal_high': (210, 240, 255),
                'crystal_shine': (245, 252, 255),

                # Crystal glow (ethereal aura)
                'glow_dark': (40, 100, 200),
                'glow_mid': (80, 170, 240),
                'glow_light': (140, 210, 255),
                'glow_hot': (200, 235, 255),

                # Snow drips
                'snow_dark': (200, 220, 240),
                'snow_mid': (230, 240, 250),
                'snow_light': (250, 253, 255),

                # Wood (rare - for door frame)
                'wood_darkest': (55, 32, 15),
                'wood_dark': (100, 60, 28),
                'wood_mid': (150, 95, 48),
                'wood_light': (200, 145, 82),

                # Gold trim (accent)
                'gold_darkest': (95, 60, 12),
                'gold_dark': (150, 105, 25),
                'gold_mid': (210, 160, 50),
                'gold_light': (250, 215, 90),
                'gold_high': (255, 245, 165),

                # Blue shield (with snowflake)
                'shield_darkest': (20, 40, 90),
                'shield_dark': (40, 75, 150),
                'shield_mid': (70, 115, 200),
                'shield_light': (120, 165, 235),

                # Door interior (blue glow)
                'door_glow_dark': (30, 80, 180),
                'door_glow_mid': (80, 160, 240),
                'door_glow_light': (150, 210, 255),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (10, 15, 30),
            }
        else:
            # RED TEAM (cursed frost - purple/red tint)
            return {
                'stone_darkest': (100, 80, 110),
                'stone_dark': (140, 120, 150),
                'stone_mid': (180, 160, 190),
                'stone_light': (215, 195, 220),
                'stone_lightest': (240, 225, 245),
                'stone_shadow': (65, 50, 75),
                'stone_edge': (45, 30, 55),

                'crystal_darkest': (100, 20, 60),
                'crystal_dark': (170, 40, 100),
                'crystal_mid': (220, 80, 150),
                'crystal_light': (245, 130, 200),
                'crystal_high': (255, 190, 225),
                'crystal_shine': (255, 235, 250),

                'glow_dark': (140, 30, 90),
                'glow_mid': (200, 70, 140),
                'glow_light': (240, 130, 190),
                'glow_hot': (255, 200, 230),

                'snow_dark': (210, 200, 220),
                'snow_mid': (235, 225, 240),
                'snow_light': (250, 245, 252),

                'wood_darkest': (40, 22, 12),
                'wood_dark': (80, 45, 22),
                'wood_mid': (125, 75, 40),
                'wood_light': (170, 110, 62),

                'gold_darkest': (75, 42, 8),
                'gold_dark': (125, 78, 20),
                'gold_mid': (180, 122, 42),
                'gold_light': (225, 172, 72),
                'gold_high': (250, 210, 130),

                'shield_darkest': (80, 15, 40),
                'shield_dark': (140, 30, 70),
                'shield_mid': (195, 55, 115),
                'shield_light': (235, 100, 165),

                'door_glow_dark': (140, 20, 80),
                'door_glow_mid': (210, 60, 140),
                'door_glow_light': (245, 130, 200),

                'shine': (255, 240, 250),
                'shadow': (0, 0, 0),
                'shadow_deep': (15, 5, 15),
            }


    # ═══════════════════════════════════════════════════════
    # LEVEL CONFIG
    # ═══════════════════════════════════════════════════════

    LEVEL_CONFIGS = {
        1: {'tower_w': 46, 'tower_h': 40,
            'has_shield': False, 'num_torches': 0,
            'ground_crystals': 0, 'corner_spikes': 0,
            'icicle_rim': False, 'crystal_tier': 'small'},
        2: {'tower_w': 50, 'tower_h': 44,
            'has_shield': True, 'num_torches': 0,
            'ground_crystals': 2, 'corner_spikes': 0,
            'icicle_rim': False, 'crystal_tier': 'small'},
        3: {'tower_w': 54, 'tower_h': 48,
            'has_shield': True, 'num_torches': 0,
            'ground_crystals': 4, 'corner_spikes': 4,
            'icicle_rim': False, 'crystal_tier': 'medium'},
        4: {'tower_w': 58, 'tower_h': 54,
            'has_shield': True, 'num_torches': 2,
            'ground_crystals': 4, 'corner_spikes': 4,
            'icicle_rim': True, 'crystal_tier': 'medium'},
        5: {'tower_w': 62, 'tower_h': 58,
            'has_shield': True, 'num_torches': 2,
            'ground_crystals': 6, 'corner_spikes': 4,
            'icicle_rim': True, 'crystal_tier': 'twin'},
        6: {'tower_w': 68, 'tower_h': 64,
            'has_shield': True, 'num_torches': 2,
            'ground_crystals': 8, 'corner_spikes': 4,
            'icicle_rim': True, 'crystal_tier': 'legendary'},
    }


    # ═══════════════════════════════════════════════════════
    # HELPER: Get crystal top position for bullet spawn
    # ═══════════════════════════════════════════════════════

    def get_ice_crystal_position(tower_x, tower_y, level, face=1):
        """Return real-world (x, y) of crystal top for bullet spawn"""
        lvl = max(1, min(6, level))
        config = _NS_ice_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5

        # Crystal position (top of tower)
        crystal_y_canvas = tower_top_y_canvas - 5
        crystal_x_canvas = cw // 2

        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)

        crystal_x_world = tower_x + (crystal_x_canvas - cw // 2) * SCALE
        crystal_y_world = tower_y + final_y_offset + crystal_y_canvas * SCALE

        return int(crystal_x_world), int(crystal_y_world)

    def get_ice_top_y(tower_x, tower_y, level):
        """Get world Y of ice crystal top (for HP bar)"""
        lvl = max(1, min(6, level))
        config = _NS_ice_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5

        # Crystal top height per tier (updated for new cluster sizes)
        tier = config['crystal_tier']
        if tier == 'small':
            crystal_h = 16  # LVL 1-2
        elif tier == 'medium':
            crystal_h = 22  # LVL 3-4 (bigger center crystal)
        elif tier == 'twin':
            crystal_h = 18  # LVL 5
        else:  # legendary
            crystal_h = 32  # LVL 6 (MASSIVE + star gem)

        top_canvas = tower_top_y_canvas - 5 - crystal_h

        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)

        top_y_world = tower_y + final_y_offset + top_canvas * SCALE
        return int(top_y_world)
    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_ice(surface, tower, x, y, size):
        """Main ice tower render - CACHED"""
        from sprite_cache import get_cached_sprite_cropped

        lvl = max(1, min(6, tower.level))

        if tower.shoot_flash_timer > 0:
            state = f"shoot_{tower.shoot_flash_timer // 2}"
        else:
            state = "idle"

        # Crystal pulse frame (lambat)
        pulse_frame = (tower.timer // 8) % 6

        cache_key = (
            'ice_full',
            tower.team,
            lvl,
            state,
            pulse_frame,
        )

        sprite_w = 120
        sprite_h = 140

        # Pakai versi ter-crop: canvas 120x140 tapi menara cuma
        # mengisi sebagian, sisanya piksel transparan yang percuma
        # ikut di-blit tiap frame.
        cached, anchor_x, anchor_y = get_cached_sprite_cropped(
            cache_key, sprite_w, sprite_h,
            lambda surf: _NS_ice_tower._draw_ice_full(surf, tower,
                                         sprite_w // 2,
                                         sprite_h - 30,
                                         size)
            ,
            anchor=(sprite_w // 2, sprite_h - 30)
        )

        surface.blit(cached, (x - anchor_x, y - anchor_y))


    def _draw_ice_full(surface, tower, x, y, size):
        """Original ice render"""
        palette = _NS_ice_tower._get_palette(tower.team)
        lvl = max(1, min(6, tower.level))
        config = _NS_ice_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"ice_{tower.team}_L{lvl}"
        if cache_key not in _NS_ice_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_ice_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_ice_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_ice_tower._BASE_CACHE[cache_key].copy()

        tower_top_y = ch - 12 - config['tower_h'] - 5
        crystal_y = tower_top_y - 5

        _NS_ice_tower._render_crystal_cluster(canvas, tower, cw // 2, crystal_y,
                                palette, config)
        _NS_ice_tower._render_effects(canvas, tower, palette, cw, ch, crystal_y)

        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))

        lvl = max(1, min(6, tower.level))
        config = _NS_ice_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"ice_{tower.team}_L{lvl}"
        if cache_key not in _NS_ice_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_ice_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_ice_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_ice_tower._BASE_CACHE[cache_key].copy()

        # Crystal cluster on top (animated pulse)
        tower_top_y = ch - 12 - config['tower_h'] - 5
        crystal_y = tower_top_y - 5

        _NS_ice_tower._render_crystal_cluster(canvas, tower, cw // 2, crystal_y,
                                palette, config)

        # Effects
        _NS_ice_tower._render_effects(canvas, tower, palette, cw, ch, crystal_y)

        # Scale & blit
        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))


    # ═══════════════════════════════════════════════════════
    # BASE BUILDING
    # ═══════════════════════════════════════════════════════

    def _render_base(canvas, cx, cy, palette, config, lvl, timer):
        """Full tower base"""
        tw = config['tower_w']
        th = config['tower_h']

        _NS_ice_tower._draw_shadow(canvas, cx, cy + 12, tw + 40)
        _NS_ice_tower._draw_ground_base(canvas, cx, cy + 5, tw + 20, palette)

        # ═══ GROUND CRYSTALS (around base - match reference) ═══
        if config['ground_crystals'] > 0:
            _NS_ice_tower._draw_ground_crystals(canvas, cx, cy + 2, tw,
                                  config['ground_crystals'], palette,
                                  timer)

        # Main tower body
        _NS_ice_tower._draw_main_tower(canvas, cx, cy, tw, th, palette, lvl)

        # Blue shield with snowflake (center)
        if config['has_shield']:
            _NS_ice_tower._draw_shield(canvas, cx, cy - th // 2 - 3, palette)

        # Blue crystal torches (lvl 4+)
        if config['num_torches'] >= 2:
            _NS_ice_tower._draw_crystal_torch(canvas, cx - tw // 2 - 3,
                                cy - th // 4, palette, timer)
            _NS_ice_tower._draw_crystal_torch(canvas, cx + tw // 2 + 3,
                                cy - th // 4, palette, timer, offset=5)

        # Arched door with blue glow
        _NS_ice_tower._draw_glowing_door(canvas, cx, cy - 8, palette, timer)

        # Top rim + battlements
        top_y = cy - th - 3
        _NS_ice_tower._draw_battlements(canvas, cx, top_y, tw, palette, config)

        # Corner crystal spikes (lvl 3+)
        if config['corner_spikes'] >= 4:
            _NS_ice_tower._draw_corner_spikes(canvas, cx, top_y - 2, tw, palette,
                                timer)


    def _draw_shadow(canvas, cx, cy, width):
        """Ground shadow"""
        for i in range(12):
            alpha = 130 - i * 10
            if alpha <= 0:
                break
            w = width - i * 3
            h = 14 - i // 2
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, w, h))
            canvas.blit(s, (cx - w // 2, cy - h // 2))


    def _draw_ground_base(canvas, cx, cy, width, palette):
        """Icy stone ground"""
        pygame.draw.ellipse(canvas, palette['stone_edge'],
                            (cx - width // 2, cy, width, 12))
        pygame.draw.ellipse(canvas, palette['stone_darkest'],
                            (cx - width // 2 + 1, cy + 1, width - 2, 10))
        pygame.draw.ellipse(canvas, palette['stone_dark'],
                            (cx - width // 2 + 2, cy + 2, width - 4, 8))
        pygame.draw.ellipse(canvas, palette['stone_mid'],
                            (cx - width // 2 + 3, cy + 3, width - 6, 6))

        # Frosty highlights
        random.seed(42)
        for _ in range(12):
            px = cx + random.randint(-width // 2 + 4, width // 2 - 4)
            py = cy + random.randint(2, 8)
            s = random.randint(2, 4)
            pygame.draw.rect(canvas, palette['stone_light'],
                             (px, py, s, s // 2 + 1))
            pygame.draw.rect(canvas, palette['stone_lightest'],
                             (px, py, s - 1, 1))
        random.seed()


    def _draw_ground_crystals(canvas, cx, cy, tower_w, count, palette, timer):
        """Blue crystals growing from ground (match reference)"""
        # Positions around tower base
        if count == 2:
            positions = [(-tower_w // 2 - 8, 4, 6),
                         (tower_w // 2 + 8, 4, 6)]
        elif count == 4:
            positions = [(-tower_w // 2 - 10, 4, 7),
                         (-tower_w // 2 - 4, 8, 4),
                         (tower_w // 2 + 4, 8, 4),
                         (tower_w // 2 + 10, 4, 7)]
        elif count == 6:
            positions = [(-tower_w // 2 - 12, 4, 8),
                         (-tower_w // 2 - 5, 8, 5),
                         (-tower_w // 2 - 8, 12, 4),
                         (tower_w // 2 + 8, 12, 4),
                         (tower_w // 2 + 5, 8, 5),
                         (tower_w // 2 + 12, 4, 8)]
        else:  # 8
            positions = [(-tower_w // 2 - 14, 3, 9),
                         (-tower_w // 2 - 8, 6, 6),
                         (-tower_w // 2 - 4, 10, 4),
                         (-tower_w // 2 - 10, 14, 3),
                         (tower_w // 2 + 10, 14, 3),
                         (tower_w // 2 + 4, 10, 4),
                         (tower_w // 2 + 8, 6, 6),
                         (tower_w // 2 + 14, 3, 9)]

        for px_off, py_off, size in positions:
            _NS_ice_tower._draw_single_crystal(canvas, cx + px_off, cy + py_off,
                                 size, palette, timer)


    def _draw_single_crystal(canvas, cx, cy, size, palette, timer,
                             pulse_offset=0):
        """Draw single blue crystal spike"""
        # Pulsing glow
        pulse = math.sin(timer * 0.08 + pulse_offset) * 0.3 + 0.7

        # ═══ GLOW AURA ═══
        glow_r = size + 3
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -1):
            alpha = int((glow_r - r) * 5 * pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(glow, (*palette['glow_mid'], alpha),
                          (glow_r, glow_r), r)
        canvas.blit(glow, (cx - glow_r, cy - glow_r))

        # ═══ CRYSTAL SHAPE (diamond/spike) ═══
        # Shadow at base
        pygame.draw.ellipse(canvas, palette['shadow_deep'],
                            (cx - size // 2, cy + size - 1,
                             size, 3))

        # Main crystal points
        top_x, top_y = cx, cy - size
        bot_x, bot_y = cx, cy + size // 2
        left_x, left_y = cx - size // 3, cy - size // 3
        right_x, right_y = cx + size // 3, cy - size // 3

        # Base shadow
        _NS_ice_tower._aapoly(canvas, palette['crystal_darkest'], [
            (top_x, top_y),
            (right_x + 1, right_y + 1),
            (bot_x + 1, bot_y + 1),
            (left_x + 1, right_y + 1),
        ])

        # Main crystal (darker side)
        _NS_ice_tower._aapoly(canvas, palette['crystal_dark'], [
            (top_x, top_y),
            (right_x, right_y),
            (bot_x, bot_y),
            (left_x, right_y),
        ])

        # Right facet (mid)
        _NS_ice_tower._aapoly(canvas, palette['crystal_mid'], [
            (top_x, top_y),
            (right_x, right_y),
            (bot_x, bot_y),
        ])

        # Left facet (light - hit by light)
        _NS_ice_tower._aapoly(canvas, palette['crystal_light'], [
            (top_x, top_y),
            (left_x, right_y),
            (bot_x, bot_y),
        ])

        # Center highlight line
        pygame.draw.line(canvas, palette['crystal_high'],
                         (top_x, top_y), (bot_x, bot_y), 1)

        # Top tip shine
        pygame.draw.rect(canvas, palette['crystal_shine'],
                         (top_x, top_y, 1, 2))

        # Extra sparkle
        if size >= 5:
            pygame.draw.rect(canvas, palette['shine'],
                             (top_x - 1, top_y + 1, 1, 1))


    def _draw_main_tower(canvas, cx, cy, w, h, palette, lvl):
        """Stone tower with icy blue tint"""
        top = cy - h

        # Shadow
        for i in range(3):
            alpha = 130 - i * 30
            s = pygame.Surface((w + i * 2, h + i), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, alpha),
                             (0, 0, w + i * 2, h + i),
                             border_radius=6)
            canvas.blit(s, (cx - w // 2 + i, top + 2 + i))

        # Main body
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - w // 2, top, w, h), border_radius=6)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - w // 2, top, w - 2, h), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - w // 2, top, w - 4, h - 1), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - w // 2, top, w - 7, h - 3), border_radius=4)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - w // 2 + 2, top + 1, 8, h - 4),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (cx - w // 2 + 3, top + 2, 4, h - 6),
                         border_radius=2)

        # Chunky bricks
        brick_h = 8
        brick_w = 11
        num_rows = h // brick_h

        for row in range(num_rows):
            row_y = top + 5 + row * brick_h
            offset = brick_w // 2 if row % 2 else 0

            for bx in range(-w // 2 + 4 + offset, w // 2 - 3, brick_w):
                block_x = cx + bx
                curve_offset = int(math.sin(
                    (bx + w // 2) / w * math.pi) * 1.5)
                block_y = row_y - curve_offset

                _NS_ice_tower._draw_chunky_brick(canvas, block_x, block_y,
                                   brick_w - 2, brick_h - 2, palette)


    def _draw_chunky_brick(canvas, x, y, w, h, palette):
        """Individual chunky stone brick (blue-tinted)"""
        pygame.draw.rect(canvas, palette['stone_shadow'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 3, h // 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 4, 1))


    def _draw_battlements(canvas, cx, cy, tower_w, palette, config):
        """Top battlements with optional icicle drips"""
        rim_w = tower_w + 4

        # Bottom rim
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - rim_w // 2, cy + 2, rim_w, 8),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - rim_w // 2, cy + 2, rim_w, 7),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - rim_w // 2, cy + 2, rim_w - 1, 5),
                         border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - rim_w // 2, cy + 2, rim_w - 2, 3))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - rim_w // 2 + 1, cy + 3, rim_w - 4, 1))

        # Gold trim on rim
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - rim_w // 2 + 2, cy + 8, rim_w - 4, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - rim_w // 2 + 2, cy + 8, rim_w - 5, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - rim_w // 2 + 3, cy + 8, 3, 1))

        # Merlons
        merlon_w = 7
        spacing = 9
        num_merlons = (rim_w + spacing) // spacing

        for i in range(num_merlons):
            mx = cx - rim_w // 2 + i * spacing
            if mx + merlon_w > cx + rim_w // 2:
                continue
            has_icicle = config['icicle_rim']
            _NS_ice_tower._draw_merlon(canvas, mx, cy - 6, merlon_w, 8, palette,
                         has_icicle=has_icicle)


    def _draw_merlon(canvas, x, y, w, h, palette, has_icicle=False):
        """Single crenellation with optional icicle"""
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 3, h - 3))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 4, h // 2))
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 5, 2))
        pygame.draw.rect(canvas, palette['shine'],
                         (x + 1, y + 1, 2, 1))

        # Icicle drip (hanging down)
        if has_icicle:
            icicle_x = x + w // 2 - 1
            # Icicle tip pointing down
            _NS_ice_tower._aapoly(canvas, palette['crystal_darkest'], [
                (icicle_x - 1, y + h),
                (icicle_x + 1, y + h),
                (icicle_x, y + h + 4),
            ])
            _NS_ice_tower._aapoly(canvas, palette['crystal_dark'], [
                (icicle_x - 1, y + h),
                (icicle_x + 1, y + h),
                (icicle_x, y + h + 3),
            ])
            _NS_ice_tower._aapoly(canvas, palette['crystal_mid'], [
                (icicle_x - 1, y + h),
                (icicle_x, y + h + 3),
                (icicle_x + 1, y + h),
            ])
            _NS_ice_tower._aapoly(canvas, palette['crystal_light'], [
                (icicle_x, y + h),
                (icicle_x, y + h + 2),
                (icicle_x - 1, y + h),
            ])
            pygame.draw.rect(canvas, palette['crystal_shine'],
                             (icicle_x - 1, y + h, 1, 1))


    def _draw_corner_spikes(canvas, cx, cy, tower_w, palette, timer):
        """Corner crystal spikes on rim (4 corners - match reference)"""
        rim_w = tower_w + 4

        positions = [
            (-rim_w // 2 + 4, -3),
            (rim_w // 2 - 6, -3),
            (-rim_w // 2 + 8, 3),
            (rim_w // 2 - 10, 3),
        ]

        for i, (px_off, py_off) in enumerate(positions):
            _NS_ice_tower._draw_crystal_spike(canvas, cx + px_off, cy + py_off,
                                palette, timer, pulse_offset=i * 0.5)


    def _draw_crystal_spike(canvas, cx, cy, palette, timer, pulse_offset=0):
        """Tall crystal spike (corner decoration)"""
        pulse = math.sin(timer * 0.08 + pulse_offset) * 0.3 + 0.7
        spike_h = 12
        spike_w = 4

        # Glow aura
        glow_r = 8
        glow = pygame.Surface((glow_r * 2, spike_h + glow_r * 2),
                              pygame.SRCALPHA)
        for r in range(glow_r, 0, -1):
            alpha = int((glow_r - r) * 6 * pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(glow, (*palette['glow_mid'], alpha),
                          (glow_r, spike_h // 2 + glow_r), r)
        canvas.blit(glow, (cx - glow_r, cy - spike_h))

        # Base stone anchor
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - spike_w // 2 - 1, cy + 1, spike_w + 2, 2))
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - spike_w // 2 - 1, cy, spike_w + 2, 2))
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - spike_w // 2, cy, spike_w, 1))

        # Crystal spike (elongated triangle pointing up)
        top_x, top_y = cx, cy - spike_h
        bot_l = (cx - spike_w // 2, cy)
        bot_r = (cx + spike_w // 2, cy)

        # Shadow
        _NS_ice_tower._aapoly(canvas, palette['shadow_deep'], [
            (top_x + 1, top_y + 1),
            (bot_r[0] + 1, bot_r[1] + 1),
            (bot_l[0] + 1, bot_l[1] + 1),
        ])

        # Darkest base
        _NS_ice_tower._aapoly(canvas, palette['crystal_darkest'], [
            (top_x, top_y),
            (bot_r[0], bot_r[1]),
            (bot_l[0], bot_l[1]),
        ])

        # Dark
        _NS_ice_tower._aapoly(canvas, palette['crystal_dark'], [
            (top_x, top_y + 1),
            (bot_r[0] - 1, bot_r[1]),
            (bot_l[0] + 1, bot_l[1]),
        ])

        # Mid facet (right side)
        _NS_ice_tower._aapoly(canvas, palette['crystal_mid'], [
            (top_x, top_y),
            (bot_r[0] - 1, bot_r[1]),
            (top_x + 1, top_y + spike_h // 2),
        ])

        # Light facet (left - hit by light)
        _NS_ice_tower._aapoly(canvas, palette['crystal_light'], [
            (top_x, top_y),
            (bot_l[0] + 1, bot_l[1]),
            (top_x - 1, top_y + spike_h // 2),
        ])

        # Center line highlight
        pygame.draw.line(canvas, palette['crystal_high'],
                         (top_x, top_y),
                         (top_x, cy - 1), 1)

        # Top shine
        pygame.draw.rect(canvas, palette['crystal_shine'],
                         (top_x, top_y, 1, 3))
        pygame.draw.rect(canvas, palette['shine'],
                         (top_x - 1, top_y + 1, 1, 1))


    def _draw_shield(canvas, cx, cy, palette):
        """Blue shield with SNOWFLAKE (match reference)"""
        sw = 13
        sh = 16

        # Shadow
        _NS_ice_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy + 2),
            (cx + 1, cy + sh // 2 + 1),
            (cx - sw // 2 + 1, cy + 2),
        ])

        # Gold border
        _NS_ice_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - sw // 2, cy - sh // 2),
            (cx + sw // 2, cy - sh // 2),
            (cx + sw // 2 + 1, cy + 1),
            (cx, cy + sh // 2),
            (cx - sw // 2 - 1, cy + 1),
        ])
        _NS_ice_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 - 1, cy - sh // 2 + 1),
            (cx + sw // 2, cy + 1),
            (cx, cy + sh // 2 - 1),
            (cx - sw // 2, cy + 1),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - sw // 2 + 1, cy - sh // 2 + 1, 2, 1))

        # Blue interior
        _NS_ice_tower._aapoly(canvas, palette['shield_darkest'], [
            (cx - sw // 2 + 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy),
            (cx, cy + sh // 2 - 3),
            (cx - sw // 2 + 3, cy),
        ])
        _NS_ice_tower._aapoly(canvas, palette['shield_dark'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - 1),
            (cx, cy + sh // 2 - 4),
            (cx - sw // 2 + 4, cy - 1),
        ])
        _NS_ice_tower._aapoly(canvas, palette['shield_mid'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx - 1, cy - sh // 2 + 4),
            (cx - sw // 2 + 4, cy - 2),
        ])

        # ═══ SNOWFLAKE (white - match reference) ═══
        # 6-point star pattern
        sn_y = cy - 1

        # Center
        pygame.draw.rect(canvas, palette['crystal_shine'], (cx, sn_y, 1, 1))
        pygame.draw.rect(canvas, palette['shine'], (cx, sn_y, 1, 1))

        # Vertical arm
        pygame.draw.rect(canvas, palette['crystal_high'],
                         (cx, sn_y - 3, 1, 7))
        pygame.draw.rect(canvas, palette['crystal_shine'],
                         (cx, sn_y - 3, 1, 5))
        # Vertical tips
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx - 1, sn_y - 3, 1, 1))
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx + 1, sn_y - 3, 1, 1))
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx - 1, sn_y + 3, 1, 1))
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx + 1, sn_y + 3, 1, 1))

        # Horizontal arm
        pygame.draw.rect(canvas, palette['crystal_high'],
                         (cx - 3, sn_y, 7, 1))
        pygame.draw.rect(canvas, palette['crystal_shine'],
                         (cx - 3, sn_y, 5, 1))
        # Horizontal tips
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx - 3, sn_y - 1, 1, 1))
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx - 3, sn_y + 1, 1, 1))
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx + 3, sn_y - 1, 1, 1))
        pygame.draw.rect(canvas, palette['crystal_light'],
                         (cx + 3, sn_y + 1, 1, 1))

        # Diagonal arms (X pattern)
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            pygame.draw.rect(canvas, palette['crystal_high'],
                             (cx + dx, sn_y + dy, 1, 1))
            pygame.draw.rect(canvas, palette['crystal_high'],
                             (cx + dx * 2, sn_y + dy * 2, 1, 1))


    def _draw_crystal_torch(canvas, cx, cy, palette, timer, offset=0):
        """Blue crystal torch (glowing crystal instead of fire)"""
        # Wooden bracket
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 1 + 1, cy + 1, 2, 5))
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - 1, cy, 2, 5))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - 1, cy, 1, 4))

        # Gold cup
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 3 + 1, cy - 2 + 1, 6, 3))
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 3, cy - 2, 6, 3))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 3, cy - 2, 6, 2))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - 3, cy - 2, 5, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - 3, cy - 2, 3, 1))

        # ═══ CRYSTAL ORB (glowing blue) ═══
        pulse = math.sin(timer * 0.15 + offset) * 0.3 + 0.7

        # Big glow
        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        for r in range(10, 1, -2):
            alpha = int((10 - r) * 12 * pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(glow, (*palette['glow_mid'], alpha),
                          (11, 11), r)
        canvas.blit(glow, (cx - 11, cy - 10))

        # Crystal orb
        _NS_ice_tower._aacircle(canvas, palette['crystal_darkest'], (cx, cy - 4), 3)
        _NS_ice_tower._aacircle(canvas, palette['crystal_dark'], (cx, cy - 4), 3)
        _NS_ice_tower._aacircle(canvas, palette['crystal_mid'], (cx, cy - 4), 2)
        _NS_ice_tower._aacircle(canvas, palette['crystal_light'], (cx - 1, cy - 5), 1)
        pygame.draw.rect(canvas, palette['crystal_shine'],
                         (cx - 1, cy - 5, 1, 1))
        pygame.draw.rect(canvas, palette['shine'], (cx - 1, cy - 5, 1, 1))


    def _draw_glowing_door(canvas, cx, cy, palette, timer):
        """Arched door with blue glow interior (match reference)"""
        door_w = 10
        door_h = 12

        # Stairs
        for step_i in range(2):
            step_y = cy + step_i * 2
            step_w = door_w + 4 + step_i * 3
            pygame.draw.rect(canvas, palette['stone_edge'],
                             (cx - step_w // 2 - 1, step_y, step_w + 2, 3))
            pygame.draw.rect(canvas, palette['stone_dark'],
                             (cx - step_w // 2, step_y, step_w, 2))
            pygame.draw.rect(canvas, palette['stone_mid'],
                             (cx - step_w // 2, step_y, step_w, 1))

        # Arch keystones
        for angle_deg in range(-90, 91, 30):
            angle = math.radians(angle_deg)
            px = cx + math.cos(angle) * (door_w // 2 + 1)
            py = cy - door_h + door_w // 2 - math.sin(angle) * (door_w // 2 + 1)
            pygame.draw.rect(canvas, palette['stone_dark'],
                             (int(px) - 1, int(py) - 1, 2, 2))
            pygame.draw.rect(canvas, palette['stone_mid'],
                             (int(px) - 1, int(py) - 1, 1, 1))

        # Door opening
        dx = cx - door_w // 2
        dy = cy - door_h

        # Dark opening
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (dx, dy + door_w // 2, door_w, door_h))
        pygame.draw.circle(canvas, palette['shadow_deep'],
                           (cx, dy + door_w // 2), door_w // 2)

        # ═══ BLUE GLOW INTERIOR (match reference!) ═══
        pulse = math.sin(timer * 0.1) * 0.2 + 0.8

        # Inner glow (blue portal-like)
        inner_w = door_w - 3
        inner_h = door_h - 2
        ix = cx - inner_w // 2
        iy = dy + door_w // 2 + 1

        # Base dark blue
        pygame.draw.rect(canvas, palette['door_glow_dark'],
                         (ix, iy + inner_w // 2, inner_w, inner_h - 2))
        pygame.draw.circle(canvas, palette['door_glow_dark'],
                           (cx, iy + inner_w // 2), inner_w // 2)

        # Mid glow
        pygame.draw.rect(canvas, palette['door_glow_mid'],
                         (ix + 1, iy + inner_w // 2 + 1,
                          inner_w - 2, inner_h - 4))

        # Bright center
        center_h = int((inner_h - 5) * pulse)
        if center_h > 0:
            pygame.draw.rect(canvas, palette['door_glow_light'],
                             (ix + 2, iy + inner_w // 2 + 2,
                              inner_w - 4, center_h))
            pygame.draw.rect(canvas, palette['crystal_shine'],
                             (ix + 3, iy + inner_w // 2 + 2,
                              inner_w - 6, max(1, center_h - 2)))

        # Outer glow around door
        glow = pygame.Surface((door_w + 10, door_h + 6), pygame.SRCALPHA)
        for r in range(6, 1, -1):
            alpha = int((6 - r) * 15 * pulse)
            if alpha > 0:
                pygame.draw.ellipse(glow,
                                    (*palette['glow_mid'], alpha),
                                    (5 - r, 5 - r,
                                     door_w + r * 2, door_h + r * 2))
        canvas.blit(glow, (cx - door_w // 2 - 5, dy - 3))

    # ═══════════════════════════════════════════════════════
    # CRYSTAL CLUSTER (BIG differences per level)
    # ═══════════════════════════════════════════════════════

    def _render_crystal_cluster(canvas, tower, cx, cy, palette, config):
        """Big crystal cluster - DRAMATIC differences per level"""
        tier = config['crystal_tier']

        # Base platform (size berbeda per tier)
        if tier == 'legendary':
            base_w = 22
        elif tier == 'twin':
            base_w = 20
        else:
            base_w = 16

        _NS_ice_tower._draw_crystal_base(canvas, cx, cy + 3, palette, base_w)

        # DISPATCH per tier - very different visuals!
        if tier == 'small':
            # LVL 1-2: Tiny cluster, light blue, 3 small crystals
            _NS_ice_tower._draw_cluster_tier1(canvas, cx, cy, palette, tower.timer)
        elif tier == 'medium':
            # LVL 3-4: Medium cluster, cyan blue, 5 crystals + circle ring
            _NS_ice_tower._draw_cluster_tier2(canvas, cx, cy, palette, tower.timer)
        elif tier == 'twin':
            # LVL 5: TWO clusters berjajar dengan warna deep blue
            _NS_ice_tower._draw_cluster_tier3(canvas, cx, cy, palette, tower.timer)
        else:
            # LVL 6: MEGA legendary, white-blue with floating shards + aura
            _NS_ice_tower._draw_cluster_tier4(canvas, cx, cy, palette, tower.timer, tower)


    def _draw_cluster_tier1(canvas, cx, cy, palette, timer):
        """LVL 1-2: SIMPLE small cluster (light blue)"""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        # Small aura
        aura_size = 10
        aura = pygame.Surface((aura_size * 3, aura_size * 3),
                              pygame.SRCALPHA)
        for r in range(aura_size, 3, -2):
            alpha = int((aura_size - r) * 3 * pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(aura, (*palette['glow_light'], alpha),
                          (aura_size * 3 // 2, aura_size * 3 // 2), r)
        canvas.blit(aura, (cx - aura_size * 3 // 2,
                            cy - aura_size * 3 // 2))

        # Colors: LIGHT BLUE (basic)
        c_dark = palette['crystal_mid']
        c_mid = palette['crystal_light']
        c_light = palette['crystal_high']
        c_shine = palette['crystal_shine']

        # 3 small crystals
        crystals = [
            (0, 0, 12, 4),      # center (medium)
            (-4, 3, 7, 3),      # left small
            (4, 3, 7, 3),       # right small
        ]

        for cx_off, cy_off, h, w in crystals:
            _NS_ice_tower._draw_simple_crystal(canvas, cx + cx_off, cy + cy_off,
                                  h, w, c_dark, c_mid, c_light, c_shine,
                                  palette)


    def _draw_cluster_tier2(canvas, cx, cy, palette, timer):
        """LVL 3-4: MEDIUM cluster (CYAN BLUE) + surrounding ring"""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        # Bigger aura
        aura_size = 15
        aura = pygame.Surface((aura_size * 3, aura_size * 3),
                              pygame.SRCALPHA)
        for r in range(aura_size, 3, -2):
            alpha = int((aura_size - r) * 4 * pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(aura, (*palette['glow_mid'], alpha),
                          (aura_size * 3 // 2, aura_size * 3 // 2), r)
        canvas.blit(aura, (cx - aura_size * 3 // 2,
                            cy - aura_size * 3 // 2))

        # Colors: CYAN BLUE (brighter, more saturated)
        # Use crystal_dark for deeper contrast
        c_dark = palette['crystal_dark']
        c_mid = palette['crystal_mid']
        c_light = palette['crystal_light']
        c_shine = palette['crystal_shine']

        # 5 crystals - taller center
        crystals = [
            (0, -3, 18, 5),      # BIG center
            (-5, 1, 12, 4),      # left tall
            (5, 1, 12, 4),       # right tall
            (-2, 5, 6, 3),       # front small left
            (3, 5, 6, 3),        # front small right
        ]

        # Sort by y so back drawn first
        crystals.sort(key=lambda c: -c[1])

        for cx_off, cy_off, h, w in crystals:
            _NS_ice_tower._draw_simple_crystal(canvas, cx + cx_off, cy + cy_off,
                                  h, w, c_dark, c_mid, c_light, c_shine,
                                  palette)

        # ═══ RING OF SMALL CRYSTALS around base (unique tier2 feature) ═══
        for angle_deg in [-90, -45, 45, 90, 135, -135]:
            angle = math.radians(angle_deg)
            rx = cx + int(math.cos(angle) * 11)
            ry = cy + 3 + int(math.sin(angle) * 3)
            _NS_ice_tower._draw_mini_crystal(canvas, rx, ry, palette, timer,
                               offset=angle * 0.5)


    def _draw_cluster_tier3(canvas, cx, cy, palette, timer):
        """LVL 5: TWIN clusters side by side (DEEP BLUE)"""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        # Two auras
        for aura_cx in [cx - 7, cx + 7]:
            aura_size = 12
            aura = pygame.Surface((aura_size * 3, aura_size * 3),
                                  pygame.SRCALPHA)
            for r in range(aura_size, 3, -2):
                alpha = int((aura_size - r) * 4 * pulse)
                if alpha > 0:
                    _NS_ice_tower._aacircle(aura, (*palette['glow_dark'], alpha),
                              (aura_size * 3 // 2, aura_size * 3 // 2), r)
            canvas.blit(aura, (aura_cx - aura_size * 3 // 2,
                                cy - aura_size * 3 // 2))

        # Colors: DEEP BLUE (darker, more mystical)
        c_dark = palette['crystal_darkest']
        c_mid = palette['crystal_dark']
        c_light = palette['crystal_mid']
        c_shine = palette['crystal_light']

        # LEFT cluster (3 crystals)
        left_crystals = [
            (-7, -1, 14, 4),     # left tall
            (-10, 3, 8, 3),      # far left short
            (-4, 4, 8, 3),       # near left short
        ]
        for cx_off, cy_off, h, w in left_crystals:
            _NS_ice_tower._draw_simple_crystal(canvas, cx + cx_off, cy + cy_off,
                                  h, w, c_dark, c_mid, c_light, c_shine,
                                  palette)

        # RIGHT cluster (3 crystals)
        right_crystals = [
            (7, -1, 14, 4),      # right tall
            (10, 3, 8, 3),       # far right short
            (4, 4, 8, 3),        # near right short
        ]
        for cx_off, cy_off, h, w in right_crystals:
            _NS_ice_tower._draw_simple_crystal(canvas, cx + cx_off, cy + cy_off,
                                  h, w, c_dark, c_mid, c_light, c_shine,
                                  palette)

        # Connecting energy line between clusters
        energy_pulse = math.sin(timer * 0.2) * 0.5 + 0.5
        energy_alpha = int(150 * energy_pulse)
        if energy_alpha > 0:
            energy_surf = pygame.Surface((16, 4), pygame.SRCALPHA)
            pygame.draw.rect(energy_surf,
                             (*palette['crystal_shine'], energy_alpha),
                             (0, 1, 16, 2))
            pygame.draw.rect(energy_surf,
                             (*palette['shine'], energy_alpha),
                             (0, 2, 16, 1))
            canvas.blit(energy_surf, (cx - 8, cy - 3))


    def _draw_cluster_tier4(canvas, cx, cy, palette, timer, tower):
        """LVL 6: MEGA LEGENDARY (WHITE-BLUE + floating shards + rings)"""
        pulse = math.sin(timer * 0.06) * 0.3 + 0.7
        fast_pulse = math.sin(timer * 0.15) * 0.4 + 0.6

        # ═══ HUGE OUTER AURA (multiple layers) ═══
        aura_size = 24
        aura = pygame.Surface((aura_size * 3, aura_size * 3),
                              pygame.SRCALPHA)
        for r in range(aura_size, 3, -2):
            alpha = int((aura_size - r) * 4 * pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(aura, (*palette['glow_mid'], alpha),
                          (aura_size * 3 // 2, aura_size * 3 // 2), r)
        canvas.blit(aura, (cx - aura_size * 3 // 2,
                            cy - aura_size * 3 // 2 - 4))

        # Inner bright aura
        aura2_size = 14
        aura2 = pygame.Surface((aura2_size * 3, aura2_size * 3),
                               pygame.SRCALPHA)
        for r in range(aura2_size, 2, -2):
            alpha = int((aura2_size - r) * 8 * fast_pulse)
            if alpha > 0:
                _NS_ice_tower._aacircle(aura2, (*palette['crystal_shine'], alpha),
                          (aura2_size * 3 // 2, aura2_size * 3 // 2), r)
        canvas.blit(aura2, (cx - aura2_size * 3 // 2,
                             cy - aura2_size * 3 // 2 - 8))

        # ═══ ORBITING RING (energy circle) ═══
        ring_r = 18
        for i in range(12):
            angle = timer * 0.05 + i * (math.pi * 2 / 12)
            rx = cx + int(math.cos(angle) * ring_r)
            ry = cy + int(math.sin(angle) * ring_r // 2) - 4
            alpha = int(180 + math.sin(timer * 0.1 + i) * 75)
            alpha = max(0, min(255, alpha))
            ring_surf = pygame.Surface((3, 3), pygame.SRCALPHA)
            _NS_ice_tower._aacircle(ring_surf, (*palette['crystal_shine'], alpha),
                      (1, 1), 1)
            canvas.blit(ring_surf, (rx - 1, ry - 1))

        # Colors: WHITE-BLUE (ultimate legendary)
        c_dark = palette['crystal_dark']
        c_mid = palette['crystal_light']
        c_light = palette['crystal_high']
        c_shine = palette['crystal_shine']

        # HUGE crystal formation (8 crystals - massive)
        crystals = [
            (0, -8, 26, 6),      # MASSIVE center
            (-7, -3, 18, 5),     # left tall
            (7, -3, 18, 5),      # right tall
            (-11, 2, 12, 4),     # far left
            (11, 2, 12, 4),      # far right
            (-4, 4, 9, 3),       # left front
            (4, 4, 9, 3),        # right front
            (0, 6, 7, 3),        # front center
        ]

        # Sort by y position (back to front for proper layering)
        crystals.sort(key=lambda c: -c[1])

        for cx_off, cy_off, h, w in crystals:
            _NS_ice_tower._draw_simple_crystal(canvas, cx + cx_off, cy + cy_off,
                                  h, w, c_dark, c_mid, c_light, c_shine,
                                  palette)

        # ═══ FLOATING SHARDS around ═══
        for i in range(8):
            angle = timer * 0.03 + i * (math.pi * 2 / 8)
            radius = 28 + int(math.sin(timer * 0.05 + i) * 4)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * 10) - 6

            # Small shard
            _NS_ice_tower._aapoly(canvas, palette['crystal_dark'], [
                (sx, sy - 3),
                (sx + 2, sy),
                (sx, sy + 3),
                (sx - 2, sy),
            ])
            _NS_ice_tower._aapoly(canvas, palette['crystal_mid'], [
                (sx, sy - 2),
                (sx + 1, sy),
                (sx, sy + 2),
                (sx - 1, sy),
            ])
            _NS_ice_tower._aapoly(canvas, palette['crystal_light'], [
                (sx, sy - 2),
                (sx + 1, sy),
                (sx, sy + 1),
            ])
            pygame.draw.rect(canvas, palette['crystal_shine'],
                             (sx, sy, 1, 1))
            pygame.draw.rect(canvas, palette['shine'],
                             (sx, sy, 1, 1))

            # Shard glow
            glow = pygame.Surface((10, 10), pygame.SRCALPHA)
            _NS_ice_tower._aacircle(glow, (*palette['glow_mid'], 120), (5, 5), 4)
            canvas.blit(glow, (sx - 5, sy - 5))

        # ═══ CENTRAL GEM ON TOP (glowing star) ═══
        gem_x = cx
        gem_y = cy - 14

        # Star glow
        for glow_r in range(6, 0, -1):
            alpha = int(180 * fast_pulse - glow_r * 25)
            if alpha > 0:
                glow = pygame.Surface((14, 14), pygame.SRCALPHA)
                _NS_ice_tower._aacircle(glow, (255, 255, 200, alpha), (7, 7), glow_r)
                canvas.blit(glow, (gem_x - 7, gem_y - 7))

        # Star shape (4-point)
        _NS_ice_tower._aapoly(canvas, palette['crystal_darkest'], [
            (gem_x, gem_y - 3),
            (gem_x + 3, gem_y),
            (gem_x, gem_y + 3),
            (gem_x - 3, gem_y),
        ])
        _NS_ice_tower._aapoly(canvas, palette['crystal_mid'], [
            (gem_x, gem_y - 2),
            (gem_x + 2, gem_y),
            (gem_x, gem_y + 2),
            (gem_x - 2, gem_y),
        ])
        _NS_ice_tower._aapoly(canvas, palette['crystal_shine'], [
            (gem_x, gem_y - 1),
            (gem_x + 1, gem_y),
            (gem_x, gem_y + 1),
            (gem_x - 1, gem_y),
        ])
        pygame.draw.rect(canvas, palette['shine'], (gem_x, gem_y, 1, 1))


    def _draw_simple_crystal(canvas, cx, cy, height, width,
                              c_dark, c_mid, c_light, c_shine, palette):
        """Simple faceted crystal spike with given colors"""
        # Shadow
        pygame.draw.ellipse(canvas, palette['shadow_deep'],
                            (cx - width // 2, cy + height // 2 - 1,
                             width, 3))

        top_x, top_y = cx, cy - height
        bot_l = (cx - width // 2, cy + 1)
        bot_r = (cx + width // 2, cy + 1)
        mid_l = (cx - width // 3, cy - height // 3)
        mid_r = (cx + width // 3, cy - height // 3)

        # Base darkest outline
        _NS_ice_tower._aapoly(canvas, palette['shadow'], [
            (top_x + 1, top_y + 1),
            (bot_r[0] + 1, bot_r[1] + 1),
            (bot_l[0] + 1, bot_l[1] + 1),
        ])

        # Right facet (darker)
        _NS_ice_tower._aapoly(canvas, c_dark, [
            (top_x, top_y),
            (mid_r[0], mid_r[1]),
            (bot_r[0], bot_r[1]),
            (cx, cy),
        ])
        _NS_ice_tower._aapoly(canvas, c_mid, [
            (top_x, top_y + 1),
            (mid_r[0] - 1, mid_r[1]),
            (bot_r[0] - 1, bot_r[1]),
            (cx, cy),
        ])

        # Left facet (light - primary lighting)
        _NS_ice_tower._aapoly(canvas, c_mid, [
            (top_x, top_y),
            (mid_l[0], mid_l[1]),
            (bot_l[0], bot_l[1]),
            (cx, cy),
        ])
        _NS_ice_tower._aapoly(canvas, c_light, [
            (top_x, top_y + 1),
            (mid_l[0] + 1, mid_l[1]),
            (bot_l[0] + 1, bot_l[1]),
            (cx, cy),
        ])

        # Extra bright edge on left
        if height >= 8:
            _NS_ice_tower._aapoly(canvas, c_shine, [
                (top_x, top_y + 2),
                (mid_l[0] + 2, mid_l[1] + 1),
                (cx - 1, cy - 1),
            ])

        # Center line highlight (down middle)
        pygame.draw.line(canvas, c_shine,
                         (top_x, top_y),
                         (cx, cy - 1), 1)

        # Top tip shine
        pygame.draw.rect(canvas, c_shine, (top_x, top_y, 1, 3))
        pygame.draw.rect(canvas, palette['shine'], (top_x, top_y, 1, 2))

        # Extra sparkle for tall crystals
        if height >= 12:
            pygame.draw.rect(canvas, palette['shine'],
                             (top_x - 1, top_y + 3, 1, 1))
            pygame.draw.rect(canvas, c_shine,
                             (top_x + 1, top_y + 5, 1, 1))


    def _draw_mini_crystal(canvas, cx, cy, palette, timer, offset=0):
        """Very small crystal (for ring decoration in tier 2)"""
        pulse = math.sin(timer * 0.1 + offset) * 0.3 + 0.7

        # Tiny glow
        alpha = int(80 * pulse)
        if alpha > 0:
            glow = pygame.Surface((6, 6), pygame.SRCALPHA)
            _NS_ice_tower._aacircle(glow, (*palette['glow_mid'], alpha), (3, 3), 3)
            canvas.blit(glow, (cx - 3, cy - 3))

        # Small crystal diamond
        _NS_ice_tower._aapoly(canvas, palette['crystal_dark'], [
            (cx, cy - 3),
            (cx + 2, cy),
            (cx, cy + 2),
            (cx - 2, cy),
        ])
        _NS_ice_tower._aapoly(canvas, palette['crystal_mid'], [
            (cx, cy - 2),
            (cx + 1, cy),
            (cx, cy + 1),
            (cx - 1, cy),
        ])
        _NS_ice_tower._aapoly(canvas, palette['crystal_light'], [
            (cx, cy - 2),
            (cx + 1, cy),
            (cx, cy + 1),
        ])
        pygame.draw.rect(canvas, palette['crystal_shine'], (cx, cy - 1, 1, 1))
        pygame.draw.rect(canvas, palette['shine'], (cx, cy - 1, 1, 1))

    def _draw_crystal_base(canvas, cx, cy, palette, base_w=16):
        """Small stone/gold platform under crystals (adjustable width)"""
        # Stone base
        pygame.draw.ellipse(canvas, palette['shadow_deep'],
                            (cx - base_w // 2 + 1, cy + 1, base_w, 4))
        pygame.draw.ellipse(canvas, palette['stone_darkest'],
                            (cx - base_w // 2, cy, base_w, 4))
        pygame.draw.ellipse(canvas, palette['stone_dark'],
                            (cx - base_w // 2, cy, base_w, 3))
        pygame.draw.ellipse(canvas, palette['stone_mid'],
                            (cx - base_w // 2 + 1, cy, base_w - 2, 2))
        pygame.draw.ellipse(canvas, palette['stone_light'],
                            (cx - base_w // 2 + 2, cy, base_w - 4, 1))

        # Gold rim
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - base_w // 2 + 1, cy - 1, base_w - 2, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - base_w // 2 + 1, cy - 1, base_w - 3, 1))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - base_w // 2 + 1, cy - 1, base_w // 2, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - base_w // 2 + 2, cy - 1, 3, 1))

        # Gold rim
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 7, cy - 1, 14, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 7, cy - 1, 13, 1))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - 7, cy - 1, 8, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - 6, cy - 1, 3, 1))


    # ═══════════════════════════════════════════════════════
    # EFFECTS (shoot pulse)
    # ═══════════════════════════════════════════════════════

    def _render_effects(canvas, tower, palette, cw, ch, crystal_y):
        """Ice shard shoot flash"""
        if tower.shoot_flash_timer > 0:
            intensity = tower.shoot_flash_timer / 8.0

            cx = cw // 2
            cy = crystal_y - 8  # near crystal top

            # Big ice burst
            size = int(9 * intensity)
            if size > 0:
                flash = pygame.Surface((size * 5, size * 5),
                                       pygame.SRCALPHA)
                # Outer glow
                _NS_ice_tower._aacircle(flash, (*palette['glow_light'], int(120 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          int(size * 2.5))
                # Mid ice
                _NS_ice_tower._aacircle(flash, (*palette['crystal_light'], int(180 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          int(size * 1.5))
                # Hot core
                _NS_ice_tower._aacircle(flash, (*palette['crystal_shine'], int(240 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          size)
                canvas.blit(flash,
                            (cx - size * 2 - size // 2,
                             cy - size * 2 - size // 2))

                # Ice shards flying out
                for i in range(6):
                    angle = i * math.pi / 3 + tower.timer * 0.1
                    shard_len = size * 3
                    sx1 = cx + int(math.cos(angle) * size)
                    sy1 = cy + int(math.sin(angle) * size)
                    sx2 = cx + int(math.cos(angle) * shard_len)
                    sy2 = cy + int(math.sin(angle) * shard_len)
                    pygame.draw.line(canvas, palette['crystal_light'],
                                     (sx1, sy1), (sx2, sy2), 2)
                    pygame.draw.line(canvas, palette['shine'],
                                     (sx1, sy1), (sx2, sy2), 1)

# ====================================================================
# mage_tower.py
# ====================================================================
class _NS_mage_tower:
    """Namespace mage_tower - isi asli tidak diubah."""

    # ================================
    # towers/mage_tower.py
    # HD Isometric Mage Tower - Kingdom Rush Style
    # ================================


    HAS_AACIRCLE = hasattr(pygame.draw, 'aacircle')


    def _clamp_color(color):
        if len(color) == 3:
            return (max(0, min(255, int(color[0]))),
                    max(0, min(255, int(color[1]))),
                    max(0, min(255, int(color[2]))))
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(color[3]))))


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_mage_tower._clamp_color(color)
        if _NS_mage_tower.HAS_AACIRCLE and radius > 1 and width == 0:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except (TypeError, ValueError):
                pass
        try:
            pygame.draw.circle(surface, color, center, radius, width)
        except (TypeError, ValueError):
            pass


    def _aapoly(surface, color, points):
        color = _NS_mage_tower._clamp_color(color)
        try:
            pygame.draw.polygon(surface, color, points)
        except (TypeError, ValueError):
            pass


    _BASE_CACHE = {}


    # ═══════════════════════════════════════════════════════
    # PALETTE (Purple/Magical theme)
    # ═══════════════════════════════════════════════════════

    def _get_palette(team):
        if team == "blue":
            return {
                # Stone (light gray with purple tint)
                'stone_darkest': (100, 95, 115),
                'stone_dark': (140, 135, 160),
                'stone_mid': (180, 175, 200),
                'stone_light': (215, 210, 230),
                'stone_lightest': (240, 238, 250),
                'stone_shadow': (70, 65, 85),
                'stone_edge': (50, 45, 65),

                # Purple magic (SIGNATURE!)
                'magic_darkest': (60, 20, 100),
                'magic_dark': (110, 40, 170),
                'magic_mid': (170, 80, 220),
                'magic_light': (215, 130, 245),
                'magic_high': (245, 190, 255),
                'magic_shine': (255, 230, 255),

                # Magic glow
                'glow_dark': (100, 30, 150),
                'glow_mid': (170, 70, 220),
                'glow_light': (220, 140, 250),
                'glow_hot': (250, 200, 255),

                # Roof (blue-purple tiles)
                'roof_darkest': (30, 40, 90),
                'roof_dark': (55, 75, 140),
                'roof_mid': (95, 120, 190),
                'roof_light': (140, 175, 230),
                'roof_high': (190, 220, 250),

                # Wood (warm brown for alchemy items)
                'wood_darkest': (55, 32, 15),
                'wood_dark': (100, 60, 28),
                'wood_mid': (150, 95, 48),
                'wood_light': (200, 145, 82),
                'wood_high': (240, 190, 130),

                # Gold (rich)
                'gold_darkest': (95, 60, 12),
                'gold_dark': (150, 105, 25),
                'gold_mid': (210, 160, 50),
                'gold_light': (250, 215, 90),
                'gold_high': (255, 245, 165),

                # Metal (dark iron for cauldron)
                'metal_dark': (40, 40, 55),
                'metal_mid': (85, 85, 105),
                'metal_light': (145, 145, 170),
                'metal_high': (200, 200, 220),

                # Purple flag
                'flag_darkest': (60, 20, 90),
                'flag_dark': (100, 40, 145),
                'flag_mid': (155, 75, 205),
                'flag_light': (205, 130, 235),

                # Potion colors (variety)
                'potion_green': (80, 220, 130),
                'potion_green_dark': (30, 140, 60),
                'potion_teal': (80, 200, 220),
                'potion_teal_dark': (30, 130, 150),

                # Utility
                'shine': (255, 255, 255),
                'shadow': (0, 0, 0),
                'shadow_deep': (10, 5, 15),
            }
        else:
            # RED TEAM (dark evil red-purple)
            return {
                'stone_darkest': (90, 75, 80),
                'stone_dark': (130, 110, 115),
                'stone_mid': (170, 150, 155),
                'stone_light': (210, 190, 195),
                'stone_lightest': (240, 220, 225),
                'stone_shadow': (60, 45, 50),
                'stone_edge': (40, 25, 30),

                'magic_darkest': (100, 15, 30),
                'magic_dark': (170, 30, 60),
                'magic_mid': (220, 60, 100),
                'magic_light': (250, 120, 160),
                'magic_high': (255, 180, 210),
                'magic_shine': (255, 230, 240),

                'glow_dark': (140, 20, 50),
                'glow_mid': (215, 55, 90),
                'glow_light': (250, 130, 170),
                'glow_hot': (255, 200, 220),

                'roof_darkest': (80, 20, 30),
                'roof_dark': (135, 40, 55),
                'roof_mid': (195, 65, 90),
                'roof_light': (240, 115, 145),
                'roof_high': (255, 175, 200),

                'wood_darkest': (40, 22, 12),
                'wood_dark': (80, 45, 22),
                'wood_mid': (125, 75, 40),
                'wood_light': (170, 110, 62),
                'wood_high': (215, 158, 100),

                'gold_darkest': (75, 42, 8),
                'gold_dark': (125, 78, 20),
                'gold_mid': (180, 122, 42),
                'gold_light': (225, 172, 72),
                'gold_high': (250, 210, 130),

                'metal_dark': (45, 35, 40),
                'metal_mid': (95, 75, 80),
                'metal_light': (155, 130, 135),
                'metal_high': (210, 180, 185),

                'flag_darkest': (80, 15, 25),
                'flag_dark': (135, 30, 45),
                'flag_mid': (195, 60, 80),
                'flag_light': (240, 115, 140),

                'potion_green': (220, 80, 120),
                'potion_green_dark': (140, 30, 60),
                'potion_teal': (220, 80, 100),
                'potion_teal_dark': (150, 30, 50),

                'shine': (255, 240, 240),
                'shadow': (0, 0, 0),
                'shadow_deep': (15, 5, 10),
            }


    # ═══════════════════════════════════════════════════════
    # LEVEL CONFIG (Big visual differences per level!)
    # ═══════════════════════════════════════════════════════

    LEVEL_CONFIGS = {
        1: {'tower_w': 46, 'tower_h': 45,
            'has_shield': False, 'num_side_towers': 0,
            'num_ground_crystals': 0, 'has_alchemy': False,
            'has_cauldron': False, 'num_torches': 0,
            'has_flags': False, 'crystal_tier': 'small'},
        2: {'tower_w': 50, 'tower_h': 48,
            'has_shield': True, 'num_side_towers': 0,
            'num_ground_crystals': 3, 'has_alchemy': False,
            'has_cauldron': True, 'num_torches': 0,
            'has_flags': False, 'crystal_tier': 'small'},
        3: {'tower_w': 54, 'tower_h': 52,
            'has_shield': True, 'num_side_towers': 1,
            'num_ground_crystals': 4, 'has_alchemy': True,
            'has_cauldron': True, 'num_torches': 0,
            'has_flags': True, 'crystal_tier': 'medium'},
        4: {'tower_w': 58, 'tower_h': 56,
            'has_shield': True, 'num_side_towers': 2,
            'num_ground_crystals': 6, 'has_alchemy': True,
            'has_cauldron': True, 'num_torches': 2,
            'has_flags': True, 'crystal_tier': 'medium'},
        5: {'tower_w': 62, 'tower_h': 60,
            'has_shield': True, 'num_side_towers': 2,
            'num_ground_crystals': 6, 'has_alchemy': True,
            'has_cauldron': True, 'num_torches': 2,
            'has_flags': True, 'crystal_tier': 'twin'},
        6: {'tower_w': 68, 'tower_h': 66,
            'has_shield': True, 'num_side_towers': 2,
            'num_ground_crystals': 8, 'has_alchemy': True,
            'has_cauldron': True, 'num_torches': 2,
            'has_flags': True, 'crystal_tier': 'legendary'},
    }


    # ═══════════════════════════════════════════════════════
    # HELPER FUNCTIONS
    # ═══════════════════════════════════════════════════════

    def get_mage_crystal_position(tower_x, tower_y, level, face=1):
        """Return real-world (x, y) of crystal top for bullet spawn"""
        lvl = max(1, min(6, level))
        config = _NS_mage_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5

        # Crystal position (on top of roof)
        crystal_y_canvas = tower_top_y_canvas - 10
        crystal_x_canvas = cw // 2

        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)

        crystal_x_world = tower_x + (crystal_x_canvas - cw // 2) * SCALE
        crystal_y_world = tower_y + final_y_offset + crystal_y_canvas * SCALE

        return int(crystal_x_world), int(crystal_y_world)


    def get_mage_top_y(tower_x, tower_y, level):
        """Get world Y of mage crystal top (for HP bar)"""
        lvl = max(1, min(6, level))
        config = _NS_mage_tower.LEVEL_CONFIGS[lvl]

        SCALE = 0.7
        cw, ch = 140, 165

        canvas_cy = ch - 12
        tower_top_y_canvas = canvas_cy - config['tower_h'] - 5

        tier = config['crystal_tier']
        if tier == 'small':
            crystal_h = 22
        elif tier == 'medium':
            crystal_h = 26
        elif tier == 'twin':
            crystal_h = 24
        else:  # legendary
            crystal_h = 34

        top_canvas = tower_top_y_canvas - 5 - crystal_h

        new_h = int(ch * SCALE)
        final_y_offset = -new_h + int(30 * SCALE)

        top_y_world = tower_y + final_y_offset + top_canvas * SCALE
        return int(top_y_world)


    # ═══════════════════════════════════════════════════════
    # MAIN ENTRY
    # ═══════════════════════════════════════════════════════

    def draw_mage(surface, tower, x, y, size):
        """Main mage tower render - CACHED"""
        from sprite_cache import get_cached_sprite_cropped

        lvl = max(1, min(6, tower.level))

        if tower.shoot_flash_timer > 0:
            state = f"shoot_{tower.shoot_flash_timer // 2}"
        else:
            state = "idle"

        pulse_frame = (tower.timer // 8) % 6

        cache_key = (
            'mage_full',
            tower.team,
            lvl,
            state,
            pulse_frame,
        )

        sprite_w = 120
        sprite_h = 140

        # Pakai versi ter-crop: canvas 120x140 tapi menara cuma
        # mengisi sebagian, sisanya piksel transparan yang percuma
        # ikut di-blit tiap frame.
        cached, anchor_x, anchor_y = get_cached_sprite_cropped(
            cache_key, sprite_w, sprite_h,
            lambda surf: _NS_mage_tower._draw_mage_full(surf, tower,
                                          sprite_w // 2,
                                          sprite_h - 30,
                                          size)
            ,
            anchor=(sprite_w // 2, sprite_h - 30)
        )

        surface.blit(cached, (x - anchor_x, y - anchor_y))


    def _draw_mage_full(surface, tower, x, y, size):
        """Original mage render"""
        palette = _NS_mage_tower._get_palette(tower.team)
        lvl = max(1, min(6, tower.level))
        config = _NS_mage_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"mage_{tower.team}_L{lvl}"
        if cache_key not in _NS_mage_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_mage_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_mage_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_mage_tower._BASE_CACHE[cache_key].copy()

        tower_top_y = ch - 12 - config['tower_h'] - 5
        crystal_y = tower_top_y - 10

        _NS_mage_tower._render_top_crystal(canvas, tower, cw // 2, crystal_y,
                            palette, config)
        _NS_mage_tower._render_effects(canvas, tower, palette, cw, ch, crystal_y)

        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))

        lvl = max(1, min(6, tower.level))
        config = _NS_mage_tower.LEVEL_CONFIGS[lvl]

        cw, ch = 140, 165

        cache_key = f"mage_{tower.team}_L{lvl}"
        if cache_key not in _NS_mage_tower._BASE_CACHE:
            base_canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            _NS_mage_tower._render_base(base_canvas, cw // 2, ch - 12,
                         palette, config, lvl, tower.timer)
            _NS_mage_tower._BASE_CACHE[cache_key] = base_canvas

        canvas = _NS_mage_tower._BASE_CACHE[cache_key].copy()

        # Crystal on top (animated)
        tower_top_y = ch - 12 - config['tower_h'] - 5
        crystal_y = tower_top_y - 10

        _NS_mage_tower._render_top_crystal(canvas, tower, cw // 2, crystal_y,
                            palette, config)

        _NS_mage_tower._render_effects(canvas, tower, palette, cw, ch, crystal_y)

        SCALE = 0.7
        new_w = int(cw * SCALE)
        new_h = int(ch * SCALE)
        scaled = pygame.transform.smoothscale(canvas, (new_w, new_h))

        final_x = x - new_w // 2
        final_y = y - new_h + int(30 * SCALE)
        surface.blit(scaled, (final_x, final_y))


    # ═══════════════════════════════════════════════════════
    # BASE BUILDING
    # ═══════════════════════════════════════════════════════

    def _render_base(canvas, cx, cy, palette, config, lvl, timer):
        """Full mage tower base"""
        tw = config['tower_w']
        th = config['tower_h']

        _NS_mage_tower._draw_shadow(canvas, cx, cy + 12, tw + 45)
        _NS_mage_tower._draw_ground_base(canvas, cx, cy + 5, tw + 22, palette)

        # Ground crystals
        if config['num_ground_crystals'] > 0:
            _NS_mage_tower._draw_ground_crystals(canvas, cx, cy + 2, tw,
                                  config['num_ground_crystals'],
                                  palette, timer)

        # Alchemy table (left, lvl 3+)
        if config['has_alchemy']:
            _NS_mage_tower._draw_alchemy_table(canvas, cx - tw // 2 - 8,
                                cy - 3, palette)

        # Cauldron (right, lvl 2+)
        if config['has_cauldron']:
            _NS_mage_tower._draw_cauldron(canvas, cx + tw // 2 + 6, cy - 2,
                           palette, timer)

        # Side towers (lvl 3+ = 1, lvl 4+ = 2)
        if config['num_side_towers'] >= 1:
            _NS_mage_tower._draw_side_tower(canvas, cx - tw // 2 - 3,
                             cy - th // 2 + 3, palette, config,
                             timer, is_left=True)
        if config['num_side_towers'] >= 2:
            _NS_mage_tower._draw_side_tower(canvas, cx + tw // 2 + 3,
                             cy - th // 2 + 3, palette, config,
                             timer, is_left=False)

        # Main tower
        _NS_mage_tower._draw_main_tower(canvas, cx, cy, tw, th, palette, lvl)

        # Purple shield with gold moon (center)
        if config['has_shield']:
            _NS_mage_tower._draw_shield(canvas, cx, cy - th // 2 - 3, palette)

        # Crystal torches (lvl 4+)
        if config['num_torches'] >= 2:
            _NS_mage_tower._draw_magic_torch(canvas, cx - tw // 2 - 5,
                              cy - th // 4 - 2, palette, timer)
            _NS_mage_tower._draw_magic_torch(canvas, cx + tw // 2 + 5,
                              cy - th // 4 - 2, palette, timer, offset=5)

        # Glowing door
        _NS_mage_tower._draw_glowing_door(canvas, cx, cy - 8, palette, timer)

        # Main tower roof (conical)
        top_y = cy - th - 3
        _NS_mage_tower._draw_main_roof(canvas, cx, top_y, tw, palette, config, timer)


    def _draw_shadow(canvas, cx, cy, width):
        for i in range(12):
            alpha = 130 - i * 10
            if alpha <= 0:
                break
            w = width - i * 3
            h = 14 - i // 2
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, w, h))
            canvas.blit(s, (cx - w // 2, cy - h // 2))


    def _draw_ground_base(canvas, cx, cy, width, palette):
        pygame.draw.ellipse(canvas, palette['stone_edge'],
                            (cx - width // 2, cy, width, 12))
        pygame.draw.ellipse(canvas, palette['stone_darkest'],
                            (cx - width // 2 + 1, cy + 1, width - 2, 10))
        pygame.draw.ellipse(canvas, palette['stone_dark'],
                            (cx - width // 2 + 2, cy + 2, width - 4, 8))
        pygame.draw.ellipse(canvas, palette['stone_mid'],
                            (cx - width // 2 + 3, cy + 3, width - 6, 6))

        random.seed(42)
        for _ in range(12):
            px = cx + random.randint(-width // 2 + 4, width // 2 - 4)
            py = cy + random.randint(2, 8)
            s = random.randint(2, 4)
            pygame.draw.rect(canvas, palette['stone_light'],
                             (px, py, s, s // 2 + 1))
            pygame.draw.rect(canvas, palette['stone_lightest'],
                             (px, py, s - 1, 1))
        random.seed()


    def _draw_ground_crystals(canvas, cx, cy, tower_w, count, palette,
                              timer):
        """Purple crystals from ground"""
        if count == 3:
            positions = [(-tower_w // 2 - 6, 5, 5),
                         (tower_w // 2 + 6, 5, 5),
                         (0, 12, 4)]
        elif count == 4:
            positions = [(-tower_w // 2 - 10, 4, 6),
                         (-tower_w // 2 - 4, 8, 4),
                         (tower_w // 2 + 4, 8, 4),
                         (tower_w // 2 + 10, 4, 6)]
        elif count == 6:
            positions = [(-tower_w // 2 - 12, 4, 7),
                         (-tower_w // 2 - 6, 8, 5),
                         (-tower_w // 2 - 2, 12, 4),
                         (tower_w // 2 + 2, 12, 4),
                         (tower_w // 2 + 6, 8, 5),
                         (tower_w // 2 + 12, 4, 7)]
        else:  # 8
            positions = [(-tower_w // 2 - 14, 3, 8),
                         (-tower_w // 2 - 8, 6, 6),
                         (-tower_w // 2 - 3, 10, 4),
                         (-tower_w // 2 - 10, 14, 4),
                         (tower_w // 2 + 10, 14, 4),
                         (tower_w // 2 + 3, 10, 4),
                         (tower_w // 2 + 8, 6, 6),
                         (tower_w // 2 + 14, 3, 8)]

        for i, (px_off, py_off, size) in enumerate(positions):
            _NS_mage_tower._draw_ground_crystal(canvas, cx + px_off, cy + py_off,
                                 size, palette, timer, offset=i * 0.3)


    def _draw_ground_crystal(canvas, cx, cy, size, palette, timer,
                             offset=0):
        """Purple ground crystal spike"""
        pulse = math.sin(timer * 0.08 + offset) * 0.3 + 0.7

        # Glow
        glow_r = size + 3
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -1):
            alpha = int((glow_r - r) * 5 * pulse)
            if alpha > 0:
                _NS_mage_tower._aacircle(glow, (*palette['glow_mid'], alpha),
                          (glow_r, glow_r), r)
        canvas.blit(glow, (cx - glow_r, cy - glow_r))

        # Crystal spike
        top_x, top_y = cx, cy - size
        bot_l = (cx - size // 3, cy)
        bot_r = (cx + size // 3, cy)

        # Shadow
        _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
            (top_x + 1, top_y + 1),
            (bot_r[0] + 1, bot_r[1] + 1),
            (bot_l[0] + 1, bot_l[1] + 1),
        ])

        _NS_mage_tower._aapoly(canvas, palette['magic_darkest'], [
            (top_x, top_y), bot_r, bot_l
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_dark'], [
            (top_x, top_y + 1),
            (bot_r[0] - 1, bot_r[1]),
            (bot_l[0] + 1, bot_l[1]),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_mid'], [
            (top_x, top_y), bot_r,
            (top_x + 1, top_y + size // 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_light'], [
            (top_x, top_y), bot_l,
            (top_x - 1, top_y + size // 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_high'], [
            (top_x, top_y + 1),
            (bot_l[0] + 1, bot_l[1] - 1),
            (top_x, top_y + size // 3),
        ])

        pygame.draw.rect(canvas, palette['magic_shine'],
                         (top_x, top_y, 1, 2))
        pygame.draw.rect(canvas, palette['shine'],
                         (top_x, top_y, 1, 1))


    def _draw_main_tower(canvas, cx, cy, w, h, palette, lvl):
        """Main stone tower body"""
        top = cy - h

        # Shadow
        for i in range(3):
            alpha = 130 - i * 30
            s = pygame.Surface((w + i * 2, h + i), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, alpha),
                             (0, 0, w + i * 2, h + i),
                             border_radius=6)
            canvas.blit(s, (cx - w // 2 + i, top + 2 + i))

        # Main body
        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - w // 2, top, w, h), border_radius=6)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - w // 2, top, w - 2, h), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - w // 2, top, w - 4, h - 1), border_radius=5)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - w // 2, top, w - 7, h - 3), border_radius=4)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - w // 2 + 2, top + 1, 8, h - 4),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (cx - w // 2 + 3, top + 2, 4, h - 6),
                         border_radius=2)

        # Chunky bricks
        brick_h = 8
        brick_w = 11
        num_rows = h // brick_h

        for row in range(num_rows):
            row_y = top + 5 + row * brick_h
            offset = brick_w // 2 if row % 2 else 0

            for bx in range(-w // 2 + 4 + offset, w // 2 - 3, brick_w):
                block_x = cx + bx
                curve_offset = int(math.sin(
                    (bx + w // 2) / w * math.pi) * 1.5)
                block_y = row_y - curve_offset

                _NS_mage_tower._draw_chunky_brick(canvas, block_x, block_y,
                                   brick_w - 2, brick_h - 2, palette)

        # Small purple windows/glows on tower
        window_positions = [(-w // 4, -h // 3), (w // 4, -h // 3)]
        for wx_off, wy_off in window_positions:
            _NS_mage_tower._draw_purple_window(canvas, cx + wx_off, cy + wy_off, palette)


    def _draw_chunky_brick(canvas, x, y, w, h, palette):
        pygame.draw.rect(canvas, palette['stone_shadow'],
                         (x, y, w, h), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (x, y, w - 1, h - 1), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (x, y, w - 2, h - 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (x, y, w - 3, h // 2), border_radius=1)
        pygame.draw.rect(canvas, palette['stone_lightest'],
                         (x + 1, y + 1, w - 4, 1))


    def _draw_purple_window(canvas, cx, cy, palette):
        """Small purple glowing arch window"""
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 2, cy - 3, 4, 5))
        pygame.draw.rect(canvas, palette['magic_darkest'],
                         (cx - 2, cy - 2, 4, 4))
        pygame.draw.rect(canvas, palette['magic_dark'],
                         (cx - 2, cy - 1, 4, 3))
        pygame.draw.rect(canvas, palette['magic_mid'],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(canvas, palette['magic_light'],
                         (cx - 1, cy, 1, 1))
        pygame.draw.rect(canvas, palette['magic_shine'],
                         (cx - 1, cy, 1, 1))


    def _draw_main_roof(canvas, cx, cy, tower_w, palette, config, timer):
        """Conical roof on main tower (blue tiles)"""
        roof_w = tower_w + 6
        roof_h = 16

        # Roof shape (conical/dome)
        # Shadow
        _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - roof_w // 2 + 1, cy + roof_h - 3 + 1),
            (cx + 1, cy - 3 + 1),
            (cx + roof_w // 2 + 1, cy + roof_h - 3 + 1),
        ])

        # Base layers
        _NS_mage_tower._aapoly(canvas, palette['roof_darkest'], [
            (cx - roof_w // 2, cy + roof_h - 3),
            (cx, cy - 3),
            (cx + roof_w // 2, cy + roof_h - 3),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_dark'], [
            (cx - roof_w // 2 + 1, cy + roof_h - 4),
            (cx, cy - 2),
            (cx + roof_w // 2 - 1, cy + roof_h - 4),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_mid'], [
            (cx - roof_w // 2 + 2, cy + roof_h - 5),
            (cx, cy - 1),
            (cx + roof_w // 2 - 2, cy + roof_h - 5),
        ])

        # Left highlight (hit by light)
        _NS_mage_tower._aapoly(canvas, palette['roof_light'], [
            (cx - roof_w // 2 + 2, cy + roof_h - 5),
            (cx, cy - 1),
            (cx - 2, cy + roof_h - 5),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_high'], [
            (cx - roof_w // 2 + 3, cy + roof_h - 6),
            (cx, cy),
            (cx - 3, cy + roof_h - 6),
        ])

        # Tile lines
        for tile_y in [cy + 3, cy + 7, cy + 11]:
            rel = (tile_y - cy + 3) / (roof_h + 3)
            left_x = cx - int(rel * roof_w // 2)
            right_x = cx + int(rel * roof_w // 2)
            pygame.draw.line(canvas, palette['roof_darkest'],
                             (left_x, tile_y), (right_x, tile_y), 1)
            # highlight above the line
            pygame.draw.line(canvas, palette['roof_light'],
                             (left_x, tile_y - 1), (cx, tile_y - 1), 1)

        # Gold trim at bottom edge
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - roof_w // 2, cy + roof_h - 3,
                          roof_w, 3))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - roof_w // 2, cy + roof_h - 3,
                          roof_w - 1, 2))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - roof_w // 2, cy + roof_h - 3,
                          roof_w - 2, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - roof_w // 2 + 1, cy + roof_h - 3, 4, 1))

        # Gold triangular ornament at front (arch pointing up)
        _NS_mage_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - 3, cy + roof_h - 3),
            (cx, cy + roof_h - 8),
            (cx + 3, cy + roof_h - 3),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - 2, cy + roof_h - 3),
            (cx, cy + roof_h - 7),
            (cx + 2, cy + roof_h - 3),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_light'], [
            (cx - 1, cy + roof_h - 4),
            (cx, cy + roof_h - 7),
            (cx, cy + roof_h - 4),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx, cy + roof_h - 6, 1, 2))


    def _draw_side_tower(canvas, cx, cy, palette, config, timer,
                         is_left=True):
        """Small side tower with conical roof + flag"""
        st_w = 12
        st_h = 22

        # Tower body
        top = cy - st_h

        # Shadow
        for i in range(2):
            alpha = 100 - i * 30
            s = pygame.Surface((st_w + i, st_h + i), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, alpha),
                             (0, 0, st_w + i, st_h + i),
                             border_radius=3)
            canvas.blit(s, (cx - st_w // 2 + i, top + 1 + i))

        pygame.draw.rect(canvas, palette['stone_edge'],
                         (cx - st_w // 2, top, st_w, st_h),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - st_w // 2, top, st_w - 1, st_h),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - st_w // 2, top, st_w - 2, st_h - 1),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - st_w // 2, top, st_w - 3, st_h - 2),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['stone_light'],
                         (cx - st_w // 2 + 1, top + 1, 3, st_h - 3),
                         border_radius=2)

        # Tiny brick lines
        for row in range(st_h // 5):
            row_y = top + 4 + row * 5
            pygame.draw.line(canvas, palette['stone_shadow'],
                             (cx - st_w // 2 + 2, row_y),
                             (cx + st_w // 2 - 2, row_y), 1)

        # Small window (glowing yellow)
        win_y = top + st_h // 2
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 2, win_y - 1, 4, 4))
        pygame.draw.rect(canvas, (100, 60, 20), (cx - 2, win_y, 4, 3))
        pygame.draw.rect(canvas, (200, 130, 40), (cx - 2, win_y, 3, 2))
        pygame.draw.rect(canvas, (255, 200, 100), (cx - 1, win_y, 2, 1))
        pygame.draw.rect(canvas, palette['shine'], (cx - 1, win_y, 1, 1))

        # Small glow around window
        glow = pygame.Surface((10, 8), pygame.SRCALPHA)
        _NS_mage_tower._aacircle(glow, (255, 180, 50, 80), (5, 4), 4)
        canvas.blit(glow, (cx - 5, win_y - 2))

        # Conical roof
        roof_h = 10
        _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - st_w // 2 - 1 + 1, top + 1),
            (cx + 1, top - roof_h + 1),
            (cx + st_w // 2 + 1 + 1, top + 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_darkest'], [
            (cx - st_w // 2 - 1, top),
            (cx, top - roof_h),
            (cx + st_w // 2 + 1, top),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_dark'], [
            (cx - st_w // 2, top - 1),
            (cx, top - roof_h + 1),
            (cx + st_w // 2, top - 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_mid'], [
            (cx - st_w // 2 + 1, top - 1),
            (cx, top - roof_h + 2),
            (cx + st_w // 2 - 1, top - 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_light'], [
            (cx - st_w // 2 + 1, top - 1),
            (cx, top - roof_h + 2),
            (cx - 1, top - 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['roof_high'], [
            (cx - st_w // 2 + 2, top - 2),
            (cx - 1, top - roof_h + 3),
            (cx - 2, top - 1),
        ])

        # Gold spire tip
        tip_y = top - roof_h
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 1, tip_y - 2, 2, 3))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx, tip_y - 2, 1, 2))
        # Point
        _NS_mage_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - 1, tip_y - 2),
            (cx, tip_y - 5),
            (cx + 1, tip_y - 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_light'], [
            (cx - 1, tip_y - 2),
            (cx, tip_y - 4),
            (cx, tip_y - 2),
        ])
        pygame.draw.rect(canvas, palette['gold_high'], (cx, tip_y - 4, 1, 1))

        # Purple flag (waving)
        if config['has_flags']:
            wave = int(math.sin(timer * 0.08 +
                                (0 if is_left else 1)) * 1)
            flag_dir = -1 if is_left else 1
            flag_y = tip_y - 1
            flag_len = 6

            _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
                (cx + 1 + 1, flag_y + 1),
                (cx + 1 + flag_len * flag_dir + wave + 1, flag_y + 1 + 1),
                (cx + 1 + int(flag_len * 0.6) * flag_dir + 1,
                 flag_y + 4 + 1),
                (cx + 1 + 1, flag_y + 5 + 1),
            ])
            _NS_mage_tower._aapoly(canvas, palette['flag_darkest'], [
                (cx + 1, flag_y),
                (cx + 1 + flag_len * flag_dir + wave, flag_y + 1),
                (cx + 1 + int(flag_len * 0.6) * flag_dir, flag_y + 4),
                (cx + 1, flag_y + 5),
            ])
            _NS_mage_tower._aapoly(canvas, palette['flag_dark'], [
                (cx + 1, flag_y + 1),
                (cx + 1 + (flag_len - 1) * flag_dir + wave, flag_y + 2),
                (cx + 1 + int(flag_len * 0.5) * flag_dir, flag_y + 3),
                (cx + 1, flag_y + 4),
            ])
            _NS_mage_tower._aapoly(canvas, palette['flag_mid'], [
                (cx + 1, flag_y + 1),
                (cx + 1 + int(flag_len * 0.5) * flag_dir + wave // 2, flag_y + 2),
                (cx + 1, flag_y + 3),
            ])
            pygame.draw.line(canvas, palette['flag_light'],
                             (cx + 1, flag_y + 1),
                             (cx + 1 + int(flag_len * 0.4) * flag_dir,
                              flag_y + 1), 1)


    def _draw_shield(canvas, cx, cy, palette):
        """Purple shield with gold moon crescent"""
        sw = 13
        sh = 16

        _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 + 1, cy + 2),
            (cx + 1, cy + sh // 2 + 1),
            (cx - sw // 2 + 1, cy + 2),
        ])

        _NS_mage_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - sw // 2, cy - sh // 2),
            (cx + sw // 2, cy - sh // 2),
            (cx + sw // 2 + 1, cy + 1),
            (cx, cy + sh // 2),
            (cx - sw // 2 - 1, cy + 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - sw // 2 + 1, cy - sh // 2 + 1),
            (cx + sw // 2 - 1, cy - sh // 2 + 1),
            (cx + sw // 2, cy + 1),
            (cx, cy + sh // 2 - 1),
            (cx - sw // 2, cy + 1),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - sw // 2 + 1, cy - sh // 2 + 1, 2, 1))

        # Purple interior
        _NS_mage_tower._aapoly(canvas, palette['magic_darkest'], [
            (cx - sw // 2 + 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy - sh // 2 + 3),
            (cx + sw // 2 - 3, cy),
            (cx, cy + sh // 2 - 3),
            (cx - sw // 2 + 3, cy),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_dark'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - sh // 2 + 4),
            (cx + sw // 2 - 4, cy - 1),
            (cx, cy + sh // 2 - 4),
            (cx - sw // 2 + 4, cy - 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_mid'], [
            (cx - sw // 2 + 4, cy - sh // 2 + 4),
            (cx - 1, cy - sh // 2 + 4),
            (cx - sw // 2 + 4, cy - 2),
        ])

        # Gold crescent moon
        moon_cx = cx
        moon_cy = cy - 1

        # Outer crescent
        _NS_mage_tower._aacircle(canvas, palette['gold_dark'], (moon_cx, moon_cy), 4)
        _NS_mage_tower._aacircle(canvas, palette['gold_mid'], (moon_cx, moon_cy), 3)
        _NS_mage_tower._aacircle(canvas, palette['gold_light'], (moon_cx - 1, moon_cy - 1), 2)
        pygame.draw.rect(canvas, palette['gold_high'],
                         (moon_cx - 1, moon_cy - 1, 1, 1))

        # Inner cutout (make crescent shape)
        _NS_mage_tower._aacircle(canvas, palette['magic_darkest'],
                  (moon_cx + 1, moon_cy - 1), 3)
        _NS_mage_tower._aacircle(canvas, palette['magic_dark'],
                  (moon_cx + 1, moon_cy - 1), 2)
        _NS_mage_tower._aacircle(canvas, palette['magic_mid'],
                  (moon_cx + 1, moon_cy - 1), 1)


    def _draw_magic_torch(canvas, cx, cy, palette, timer, offset=0):
        """Purple magic torch (crystal flame)"""
        # Base column
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - 2 + 1, cy + 1, 4, 6))
        pygame.draw.rect(canvas, palette['stone_darkest'],
                         (cx - 2, cy, 4, 6))
        pygame.draw.rect(canvas, palette['stone_dark'],
                         (cx - 2, cy, 3, 5))
        pygame.draw.rect(canvas, palette['stone_mid'],
                         (cx - 2, cy, 2, 4))

        # Gold cup
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - 2, cy - 2, 4, 2))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - 2, cy - 2, 3, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - 2, cy - 2, 2, 1))

        # Purple flame
        flicker = int(timer * 0.4 + offset) % 5
        flame_h = 8 + flicker

        # Glow
        glow = pygame.Surface((22, 24), pygame.SRCALPHA)
        for r in range(10, 3, -2):
            alpha = 50 - r * 3
            if alpha > 0:
                _NS_mage_tower._aacircle(glow, (*palette['glow_mid'], alpha),
                          (11, 12), r)
        canvas.blit(glow, (cx - 11, cy - 12))

        # Flame layers
        _NS_mage_tower._aapoly(canvas, palette['magic_darkest'], [
            (cx - 3, cy - 2),
            (cx, cy - 2 - flame_h),
            (cx + 3, cy - 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_dark'], [
            (cx - 2, cy - 3),
            (cx, cy - 2 - flame_h + 1),
            (cx + 2, cy - 3),
        ])
        _NS_mage_tower._aapoly(canvas, palette['magic_mid'], [
            (cx - 1, cy - 4),
            (cx, cy - 2 - flame_h + 2),
            (cx + 1, cy - 4),
        ])
        pygame.draw.rect(canvas, palette['magic_high'],
                         (cx, cy - 2 - flame_h + 3, 1, flame_h - 5))
        pygame.draw.rect(canvas, palette['magic_shine'],
                         (cx, cy - 2 - flame_h + 3, 1, flame_h - 6))
        pygame.draw.rect(canvas, palette['shine'],
                         (cx, cy - 2 - flame_h + 4, 1, 2))


    def _draw_glowing_door(canvas, cx, cy, palette, timer):
        """Purple glowing portal door"""
        door_w = 10
        door_h = 12

        # Stairs
        for step_i in range(2):
            step_y = cy + step_i * 2
            step_w = door_w + 4 + step_i * 3
            pygame.draw.rect(canvas, palette['stone_edge'],
                             (cx - step_w // 2 - 1, step_y, step_w + 2, 3))
            pygame.draw.rect(canvas, palette['stone_dark'],
                             (cx - step_w // 2, step_y, step_w, 2))
            pygame.draw.rect(canvas, palette['stone_mid'],
                             (cx - step_w // 2, step_y, step_w, 1))

        # Arch keystones
        for angle_deg in range(-90, 91, 30):
            angle = math.radians(angle_deg)
            px = cx + math.cos(angle) * (door_w // 2 + 1)
            py = cy - door_h + door_w // 2 - math.sin(angle) * (door_w // 2 + 1)
            pygame.draw.rect(canvas, palette['stone_dark'],
                             (int(px) - 1, int(py) - 1, 2, 2))
            pygame.draw.rect(canvas, palette['stone_mid'],
                             (int(px) - 1, int(py) - 1, 1, 1))

        dx = cx - door_w // 2
        dy = cy - door_h

        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (dx, dy + door_w // 2, door_w, door_h))
        pygame.draw.circle(canvas, palette['shadow_deep'],
                           (cx, dy + door_w // 2), door_w // 2)

        # Purple portal glow
        pulse = math.sin(timer * 0.1) * 0.2 + 0.8

        inner_w = door_w - 3
        inner_h = door_h - 2
        ix = cx - inner_w // 2
        iy = dy + door_w // 2 + 1

        pygame.draw.rect(canvas, palette['magic_darkest'],
                         (ix, iy + inner_w // 2, inner_w, inner_h - 2))
        pygame.draw.circle(canvas, palette['magic_darkest'],
                           (cx, iy + inner_w // 2), inner_w // 2)
        pygame.draw.rect(canvas, palette['magic_dark'],
                         (ix + 1, iy + inner_w // 2 + 1,
                          inner_w - 2, inner_h - 4))

        center_h = int((inner_h - 5) * pulse)
        if center_h > 0:
            pygame.draw.rect(canvas, palette['magic_mid'],
                             (ix + 2, iy + inner_w // 2 + 2,
                              inner_w - 4, center_h))
            pygame.draw.rect(canvas, palette['magic_light'],
                             (ix + 3, iy + inner_w // 2 + 2,
                              inner_w - 6, max(1, center_h - 2)))

        # Portal outer glow
        glow = pygame.Surface((door_w + 12, door_h + 8), pygame.SRCALPHA)
        for r in range(7, 1, -1):
            alpha = int((7 - r) * 15 * pulse)
            if alpha > 0:
                pygame.draw.ellipse(glow,
                                    (*palette['glow_mid'], alpha),
                                    (6 - r, 6 - r,
                                     door_w + r * 2, door_h + r * 2))
        canvas.blit(glow, (cx - door_w // 2 - 6, dy - 4))


    def _draw_alchemy_table(canvas, cx, cy, palette):
        """Wooden alchemy table with potions"""
        tw = 12
        th = 9

        # Shadow
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - tw // 2 + 1, cy + 1, tw, th))

        # Table body
        pygame.draw.rect(canvas, palette['wood_darkest'],
                         (cx - tw // 2, cy, tw, th))
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - tw // 2, cy, tw - 1, th - 1))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - tw // 2, cy, tw - 2, 4))
        pygame.draw.rect(canvas, palette['wood_light'],
                         (cx - tw // 2, cy, tw - 3, 2))
        pygame.draw.rect(canvas, palette['wood_high'],
                         (cx - tw // 2 + 1, cy + 1, 3, 1))

        # Table top surface
        pygame.draw.rect(canvas, palette['wood_dark'],
                         (cx - tw // 2 - 1, cy - 1, tw + 2, 2))
        pygame.draw.rect(canvas, palette['wood_mid'],
                         (cx - tw // 2 - 1, cy - 1, tw + 1, 1))

        # Legs
        for leg_x in [-tw // 2 + 1, tw // 2 - 2]:
            pygame.draw.rect(canvas, palette['wood_darkest'],
                             (cx + leg_x, cy + th - 1, 1, 2))

        # Small potions on table
        # Green potion
        px = cx - 3
        py = cy - 3
        pygame.draw.rect(canvas, palette['shadow'], (px + 1, py + 1, 2, 3))
        pygame.draw.rect(canvas, palette['potion_green_dark'],
                         (px, py, 2, 3))
        pygame.draw.rect(canvas, palette['potion_green'], (px, py, 2, 2))
        pygame.draw.rect(canvas, palette['shine'], (px, py, 1, 1))
        # Bottle neck
        pygame.draw.rect(canvas, palette['stone_dark'], (px, py - 1, 2, 1))

        # Teal potion
        px = cx
        py = cy - 3
        pygame.draw.rect(canvas, palette['shadow'], (px + 1, py + 1, 2, 3))
        pygame.draw.rect(canvas, palette['potion_teal_dark'],
                         (px, py, 2, 3))
        pygame.draw.rect(canvas, palette['potion_teal'], (px, py, 2, 2))
        pygame.draw.rect(canvas, palette['shine'], (px, py, 1, 1))
        pygame.draw.rect(canvas, palette['stone_dark'], (px, py - 1, 2, 1))

        # Scroll (right side)
        sx = cx + 3
        sy = cy - 2
        pygame.draw.rect(canvas, palette['wood_darkest'], (sx, sy, 3, 2))
        pygame.draw.rect(canvas, (245, 235, 200), (sx, sy, 3, 1))
        _NS_mage_tower._aacircle(canvas, palette['wood_darkest'], (sx, sy + 1), 1)
        _NS_mage_tower._aacircle(canvas, palette['wood_darkest'], (sx + 3, sy + 1), 1)


    def _draw_cauldron(canvas, cx, cy, palette, timer):
        """Iron cauldron with purple bubbling"""
        cw = 10
        ch = 8

        # Shadow
        pygame.draw.rect(canvas, palette['shadow_deep'],
                         (cx - cw // 2 + 1, cy + 1, cw, ch),
                         border_radius=2)

        # Iron cauldron body (rounded)
        pygame.draw.rect(canvas, palette['metal_dark'],
                         (cx - cw // 2, cy, cw, ch),
                         border_radius=4)
        pygame.draw.rect(canvas, palette['metal_mid'],
                         (cx - cw // 2, cy, cw - 1, ch - 1),
                         border_radius=3)
        pygame.draw.rect(canvas, palette['metal_light'],
                         (cx - cw // 2, cy, cw - 3, 3),
                         border_radius=2)
        pygame.draw.rect(canvas, palette['metal_high'],
                         (cx - cw // 2 + 1, cy + 1, 3, 1))

        # Rim (darker top)
        pygame.draw.rect(canvas, palette['metal_dark'],
                         (cx - cw // 2 - 1, cy - 1, cw + 2, 2))
        pygame.draw.rect(canvas, palette['metal_light'],
                         (cx - cw // 2, cy - 1, cw, 1))

        # Legs
        for leg_x in [-3, 3]:
            pygame.draw.rect(canvas, palette['metal_dark'],
                             (cx + leg_x, cy + ch - 1, 2, 2))
            pygame.draw.rect(canvas, palette['shadow'],
                             (cx + leg_x, cy + ch + 1, 2, 1))

        # Purple bubble (inside)
        bubble_h = int(math.sin(timer * 0.1) * 1) + 3
        pygame.draw.rect(canvas, palette['magic_darkest'],
                         (cx - cw // 2 + 1, cy, cw - 2, 2))
        pygame.draw.rect(canvas, palette['magic_dark'],
                         (cx - cw // 2 + 1, cy - 1, cw - 2, 1))

        # Rising purple smoke
        for i in range(3):
            smoke_offset = (timer * 0.5 + i * 4) % 12
            sy = cy - 3 - int(smoke_offset)
            sx = cx + int(math.sin(timer * 0.1 + i) * 2)
            alpha = int(180 - smoke_offset * 12)
            if alpha > 0:
                smoke = pygame.Surface((6, 5), pygame.SRCALPHA)
                _NS_mage_tower._aacircle(smoke, (*palette['magic_mid'], alpha), (3, 2), 2)
                _NS_mage_tower._aacircle(smoke, (*palette['magic_light'], alpha),
                          (3, 2), 1)
                canvas.blit(smoke, (sx - 3, sy - 2))

        # Bubble on surface
        bubble_pulse = int(timer * 0.15) % 4
        if bubble_pulse < 2:
            pygame.draw.rect(canvas, palette['magic_high'],
                             (cx - 1, cy, 1, 1))
            pygame.draw.rect(canvas, palette['shine'],
                             (cx - 1, cy, 1, 1))


    # ═══════════════════════════════════════════════════════
    # TOP CRYSTAL (Signature - big differences per tier!)
    # ═══════════════════════════════════════════════════════

    def _render_top_crystal(canvas, tower, cx, cy, palette, config):
        """Purple crystal on top of tower (with gold horn holder)"""
        tier = config['crystal_tier']

        # Gold horn holder (crescent moon shape - match reference)
        _NS_mage_tower._draw_horn_holder(canvas, cx, cy + 4, palette,
                          big=(tier in ('twin', 'legendary')))

        if tier == 'small':
            _NS_mage_tower._draw_crystal_small(canvas, cx, cy, palette, tower.timer)
        elif tier == 'medium':
            _NS_mage_tower._draw_crystal_medium(canvas, cx, cy, palette, tower.timer)
        elif tier == 'twin':
            _NS_mage_tower._draw_crystal_twin(canvas, cx, cy, palette, tower.timer)
        else:  # legendary
            _NS_mage_tower._draw_crystal_legendary(canvas, cx, cy, palette, tower.timer,
                                    tower)


    def _draw_horn_holder(canvas, cx, cy, palette, big=False):
        """Gold crescent horns holding crystal (match reference)"""
        h = 5 if big else 4
        w = 8 if big else 6

        # Base ring
        pygame.draw.rect(canvas, palette['shadow'],
                         (cx - w // 2 + 1, cy + 1, w, 3))
        pygame.draw.rect(canvas, palette['gold_dark'],
                         (cx - w // 2, cy, w, 3))
        pygame.draw.rect(canvas, palette['gold_mid'],
                         (cx - w // 2, cy, w - 1, 2))
        pygame.draw.rect(canvas, palette['gold_light'],
                         (cx - w // 2, cy, w // 2, 1))
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - w // 2 + 1, cy, 3, 1))

        # Left horn (curved up)
        _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx - w // 2 + 1, cy + 1),
            (cx - w // 2 - 1 + 1, cy - h + 1),
            (cx - w // 2 + 1 + 1, cy - h // 2 + 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_dark'], [
            (cx - w // 2, cy),
            (cx - w // 2 - 1, cy - h),
            (cx - w // 2 + 1, cy - h // 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_mid'], [
            (cx - w // 2, cy),
            (cx - w // 2, cy - h + 1),
            (cx - w // 2 + 1, cy - h // 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_light'], [
            (cx - w // 2, cy),
            (cx - w // 2, cy - h + 1),
            (cx - w // 2, cy - 1),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx - w // 2, cy - h + 1, 1, 1))

        # Right horn (curved up)
        _NS_mage_tower._aapoly(canvas, palette['shadow_deep'], [
            (cx + w // 2 - 1 + 1, cy + 1),
            (cx + w // 2 + 1 + 1, cy - h + 1),
            (cx + w // 2 - 1 - 1 + 1, cy - h // 2 + 1),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_dark'], [
            (cx + w // 2 - 1, cy),
            (cx + w // 2 + 1, cy - h),
            (cx + w // 2 - 2, cy - h // 2),
        ])
        _NS_mage_tower._aapoly(canvas, palette['gold_mid'], [
            (cx + w // 2 - 1, cy),
            (cx + w // 2, cy - h + 1),
            (cx + w // 2 - 2, cy - h // 2),
        ])
        pygame.draw.rect(canvas, palette['gold_high'],
                         (cx + w // 2, cy - h + 1, 1, 1))


    def _draw_crystal_small(canvas, cx, cy, palette, timer):
        """LVL 1-2: Single small purple crystal"""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        # Aura
        aura_size = 10
        aura = pygame.Surface((aura_size * 3, aura_size * 3),
                              pygame.SRCALPHA)
        for r in range(aura_size, 3, -2):
            alpha = int((aura_size - r) * 4 * pulse)
            if alpha > 0:
                _NS_mage_tower._aacircle(aura, (*palette['glow_mid'], alpha),
                          (aura_size * 3 // 2, aura_size * 3 // 2), r)
        canvas.blit(aura, (cx - aura_size * 3 // 2,
                           cy - aura_size * 3 // 2))

        # Single tall crystal
        _NS_mage_tower._draw_faceted_crystal(canvas, cx, cy, 14, 5, palette,
                              color_tier='light')


    def _draw_crystal_medium(canvas, cx, cy, palette, timer):
        """LVL 3-4: Bigger crystal with 2 small side crystals"""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        # Bigger aura
        aura_size = 14
        aura = pygame.Surface((aura_size * 3, aura_size * 3),
                              pygame.SRCALPHA)
        for r in range(aura_size, 3, -2):
            alpha = int((aura_size - r) * 4 * pulse)
            if alpha > 0:
                _NS_mage_tower._aacircle(aura, (*palette['glow_mid'], alpha),
                          (aura_size * 3 // 2, aura_size * 3 // 2), r)
        canvas.blit(aura, (cx - aura_size * 3 // 2,
                           cy - aura_size * 3 // 2))

        # Central bigger crystal
        _NS_mage_tower._draw_faceted_crystal(canvas, cx, cy - 2, 18, 6, palette,
                              color_tier='mid')

        # 2 small side crystals
        _NS_mage_tower._draw_faceted_crystal(canvas, cx - 5, cy + 2, 8, 3, palette,
                              color_tier='light')
        _NS_mage_tower._draw_faceted_crystal(canvas, cx + 5, cy + 2, 8, 3, palette,
                              color_tier='light')


    def _draw_crystal_twin(canvas, cx, cy, palette, timer):
        """LVL 5: TWIN crystals (2 medium side by side)"""
        pulse = math.sin(timer * 0.08) * 0.3 + 0.7

        # Two auras
        for aura_cx in [cx - 6, cx + 6]:
            aura_size = 11
            aura = pygame.Surface((aura_size * 3, aura_size * 3),
                                  pygame.SRCALPHA)
            for r in range(aura_size, 3, -2):
                alpha = int((aura_size - r) * 4 * pulse)
                if alpha > 0:
                    _NS_mage_tower._aacircle(aura, (*palette['glow_mid'], alpha),
                              (aura_size * 3 // 2, aura_size * 3 // 2), r)
            canvas.blit(aura, (aura_cx - aura_size * 3 // 2,
                               cy - aura_size * 3 // 2))

        # LEFT crystal
        _NS_mage_tower._draw_faceted_crystal(canvas, cx - 6, cy, 14, 5, palette,
                              color_tier='dark')
        # RIGHT crystal
        _NS_mage_tower._draw_faceted_crystal(canvas, cx + 6, cy, 14, 5, palette,
                              color_tier='dark')

        # Energy connection between crystals
        energy_pulse = math.sin(timer * 0.2) * 0.5 + 0.5
        energy_alpha = int(180 * energy_pulse)
        if energy_alpha > 0:
            for wave_i in range(2):
                energy_surf = pygame.Surface((14, 4), pygame.SRCALPHA)
                pygame.draw.rect(energy_surf,
                                 (*palette['magic_shine'],
                                  energy_alpha // (wave_i + 1)),
                                 (0, 1, 14, 2))
                pygame.draw.rect(energy_surf,
                                 (*palette['shine'], energy_alpha),
                                 (0, 2, 14, 1))
                canvas.blit(energy_surf, (cx - 7, cy - 4))

        # Small floating orb in middle
        mid_pulse = int(timer * 0.15) % 6
        if mid_pulse < 4:
            _NS_mage_tower._aacircle(canvas, palette['magic_high'], (cx, cy - 4), 2)
            _NS_mage_tower._aacircle(canvas, palette['magic_shine'], (cx, cy - 4), 1)


    def _draw_crystal_legendary(canvas, cx, cy, palette, timer, tower):
        """LVL 6: MEGA crystal + orbiting runes + magic circle"""
        pulse = math.sin(timer * 0.06) * 0.3 + 0.7
        fast_pulse = math.sin(timer * 0.15) * 0.4 + 0.6

        # HUGE outer aura
        aura_size = 22
        aura = pygame.Surface((aura_size * 3, aura_size * 3),
                              pygame.SRCALPHA)
        for r in range(aura_size, 3, -2):
            alpha = int((aura_size - r) * 4 * pulse)
            if alpha > 0:
                _NS_mage_tower._aacircle(aura, (*palette['glow_mid'], alpha),
                          (aura_size * 3 // 2, aura_size * 3 // 2), r)
        canvas.blit(aura, (cx - aura_size * 3 // 2,
                           cy - aura_size * 3 // 2 - 4))

        # Inner bright aura
        aura2_size = 12
        aura2 = pygame.Surface((aura2_size * 3, aura2_size * 3),
                               pygame.SRCALPHA)
        for r in range(aura2_size, 2, -2):
            alpha = int((aura2_size - r) * 8 * fast_pulse)
            if alpha > 0:
                _NS_mage_tower._aacircle(aura2, (*palette['magic_shine'], alpha),
                          (aura2_size * 3 // 2, aura2_size * 3 // 2), r)
        canvas.blit(aura2, (cx - aura2_size * 3 // 2,
                            cy - aura2_size * 3 // 2 - 6))

        # ═══ ORBITING RUNES (magic circle) ═══
        ring_r = 16
        for i in range(8):
            angle = timer * 0.04 + i * (math.pi * 2 / 8)
            rx = cx + int(math.cos(angle) * ring_r)
            ry = cy + int(math.sin(angle) * ring_r // 2) - 3

            # Rune symbol
            alpha = int(200 + math.sin(timer * 0.1 + i) * 55)
            alpha = max(100, min(255, alpha))

            rune_surf = pygame.Surface((5, 5), pygame.SRCALPHA)
            pygame.draw.rect(rune_surf,
                             (*palette['magic_high'], alpha),
                             (1, 1, 3, 3))
            pygame.draw.rect(rune_surf,
                             (*palette['magic_shine'], alpha),
                             (2, 2, 1, 1))
            canvas.blit(rune_surf, (rx - 2, ry - 2))

        # ═══ MEGA central crystal ═══
        _NS_mage_tower._draw_faceted_crystal(canvas, cx, cy - 4, 26, 7, palette,
                              color_tier='high')

        # 4 side crystals (smaller)
        _NS_mage_tower._draw_faceted_crystal(canvas, cx - 7, cy + 1, 12, 4, palette,
                              color_tier='mid')
        _NS_mage_tower._draw_faceted_crystal(canvas, cx + 7, cy + 1, 12, 4, palette,
                              color_tier='mid')
        _NS_mage_tower._draw_faceted_crystal(canvas, cx - 4, cy + 4, 7, 3, palette,
                              color_tier='light')
        _NS_mage_tower._draw_faceted_crystal(canvas, cx + 4, cy + 4, 7, 3, palette,
                              color_tier='light')

        # Floating magic particles
        for i in range(6):
            angle = timer * 0.03 + i * (math.pi * 2 / 6)
            radius = 24 + int(math.sin(timer * 0.05 + i) * 3)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * 8) - 6

            # Sparkle
            pygame.draw.rect(canvas, palette['magic_high'], (sx, sy, 1, 1))
            pygame.draw.rect(canvas, palette['shine'], (sx, sy, 1, 1))

            # Cross sparkle
            pygame.draw.rect(canvas, palette['magic_shine'], (sx - 1, sy, 1, 1))
            pygame.draw.rect(canvas, palette['magic_shine'], (sx + 1, sy, 1, 1))
            pygame.draw.rect(canvas, palette['magic_shine'], (sx, sy - 1, 1, 1))
            pygame.draw.rect(canvas, palette['magic_shine'], (sx, sy + 1, 1, 1))


    def _draw_faceted_crystal(canvas, cx, cy, height, width, palette,
                              color_tier='mid'):
        """Purple faceted crystal spike"""
        if color_tier == 'light':
            c_dark = palette['magic_mid']
            c_mid = palette['magic_light']
            c_light = palette['magic_high']
            c_shine = palette['magic_shine']
        elif color_tier == 'mid':
            c_dark = palette['magic_dark']
            c_mid = palette['magic_mid']
            c_light = palette['magic_light']
            c_shine = palette['magic_high']
        elif color_tier == 'dark':
            c_dark = palette['magic_darkest']
            c_mid = palette['magic_dark']
            c_light = palette['magic_mid']
            c_shine = palette['magic_light']
        else:  # high (legendary)
            c_dark = palette['magic_dark']
            c_mid = palette['magic_light']
            c_light = palette['magic_high']
            c_shine = palette['magic_shine']

        # Shadow
        pygame.draw.ellipse(canvas, palette['shadow_deep'],
                            (cx - width // 2, cy + height // 2 - 1,
                             width, 3))

        top_x, top_y = cx, cy - height
        bot_l = (cx - width // 2, cy + 1)
        bot_r = (cx + width // 2, cy + 1)
        mid_l = (cx - width // 3, cy - height // 3)
        mid_r = (cx + width // 3, cy - height // 3)

        # Outline
        _NS_mage_tower._aapoly(canvas, palette['shadow'], [
            (top_x + 1, top_y + 1),
            (bot_r[0] + 1, bot_r[1] + 1),
            (bot_l[0] + 1, bot_l[1] + 1),
        ])

        # Right facet (dark)
        _NS_mage_tower._aapoly(canvas, c_dark, [
            (top_x, top_y), mid_r, bot_r, (cx, cy)
        ])
        _NS_mage_tower._aapoly(canvas, c_mid, [
            (top_x, top_y + 1),
            (mid_r[0] - 1, mid_r[1]),
            (bot_r[0] - 1, bot_r[1]),
            (cx, cy),
        ])

        # Left facet (light)
        _NS_mage_tower._aapoly(canvas, c_mid, [
            (top_x, top_y), mid_l, bot_l, (cx, cy)
        ])
        _NS_mage_tower._aapoly(canvas, c_light, [
            (top_x, top_y + 1),
            (mid_l[0] + 1, mid_l[1]),
            (bot_l[0] + 1, bot_l[1]),
            (cx, cy),
        ])

        if height >= 10:
            _NS_mage_tower._aapoly(canvas, c_shine, [
                (top_x, top_y + 2),
                (mid_l[0] + 2, mid_l[1] + 1),
                (cx - 1, cy - 1),
            ])

        # Center line
        pygame.draw.line(canvas, c_shine, (top_x, top_y), (cx, cy - 1), 1)

        # Top tip shine
        pygame.draw.rect(canvas, c_shine, (top_x, top_y, 1, 3))
        pygame.draw.rect(canvas, palette['shine'], (top_x, top_y, 1, 2))

        # Extra sparkle
        if height >= 14:
            pygame.draw.rect(canvas, palette['shine'],
                             (top_x - 1, top_y + 3, 1, 1))


    # ═══════════════════════════════════════════════════════
    # EFFECTS
    # ═══════════════════════════════════════════════════════

    def _render_effects(canvas, tower, palette, cw, ch, crystal_y):
        """Magic burst effect"""
        if tower.shoot_flash_timer > 0:
            intensity = tower.shoot_flash_timer / 8.0
            cx = cw // 2
            cy = crystal_y - 6

            size = int(9 * intensity)
            if size > 0:
                flash = pygame.Surface((size * 5, size * 5),
                                       pygame.SRCALPHA)
                _NS_mage_tower._aacircle(flash, (*palette['glow_light'], int(120 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          int(size * 2.5))
                _NS_mage_tower._aacircle(flash, (*palette['magic_light'], int(180 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2),
                          int(size * 1.5))
                _NS_mage_tower._aacircle(flash, (*palette['magic_shine'], int(240 * intensity)),
                          (size * 2 + size // 2, size * 2 + size // 2), size)
                canvas.blit(flash,
                            (cx - size * 2 - size // 2,
                             cy - size * 2 - size // 2))

                # Magic sparks radiating
                for i in range(6):
                    angle = i * math.pi / 3 + tower.timer * 0.1
                    spark_len = size * 3
                    sx1 = cx + int(math.cos(angle) * size)
                    sy1 = cy + int(math.sin(angle) * size)
                    sx2 = cx + int(math.cos(angle) * spark_len)
                    sy2 = cy + int(math.sin(angle) * spark_len)
                    pygame.draw.line(canvas, palette['magic_light'],
                                     (sx1, sy1), (sx2, sy2), 2)
                    pygame.draw.line(canvas, palette['shine'],
                                     (sx1, sy1), (sx2, sy2), 1)

