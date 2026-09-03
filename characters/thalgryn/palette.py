"""Thalgryn Color Palette - Procedural Pixel Art Style"""

import pygame

CHARACTER_PALETTE = {
    # Core colors
    "outline": (10, 10, 15),
    "shadow": (20, 15, 25),
    "dark": (40, 30, 50),
    "body": (80, 50, 120),
    "mid": (120, 80, 160),
    "light": (160, 120, 200),
    "highlight": (200, 160, 240),
    
    # Weapon colors
    "weapon_dark": (50, 40, 60),
    "weapon_mid": (100, 80, 120),
    "weapon_light": (150, 130, 170),
    "weapon_edge": (220, 180, 100),
    
    # Armor
    "armor_dark": (60, 50, 70),
    "armor_mid": (100, 90, 120),
    "armor_highlight": (180, 170, 200),
    
    # Effects
    "fx_dark_purple": (80, 20, 120),
    "fx_bright_purple": (200, 100, 255),
    "fx_glow": (150, 80, 200),
    "fx_spark": (255, 200, 100),
    "fx_impact": (255, 100, 100),
    "fx_smoke": (100, 100, 120),
    
    # Blood
    "blood": (150, 30, 40),
    
    # Transparent
    "transparent": (0, 0, 0, 0),
}

def get_color(name, alpha=255):
    """Get color from palette with optional alpha"""
    color = CHARACTER_PALETTE.get(name, (255, 255, 255))
    if isinstance(color, tuple) and len(color) == 4:
        return color
    if isinstance(color, tuple) and len(color) == 3:
        return (*color, alpha)
    return (255, 255, 255, alpha)
