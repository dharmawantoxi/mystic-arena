"""Thalgryn Character Module"""

CHARACTER_NAME = "thalgryn"

from .renderer import ThalgrynRenderer
from .animation import ThalgrynAnimation, AnimationState
from .attack import SwingAttack
from .projectile import Projectile, ProjectileSystem
from .skill import SkillFX
from .particle import Particle, ParticleSystem
from .character import Thalgryn

__all__ = [
    "CHARACTER_NAME",
    "ThalgrynRenderer",
    "ThalgrynAnimation",
    "AnimationState",
    "SwingAttack",
    "Projectile",
    "ProjectileSystem",
    "SkillFX",
    "Particle",
    "ParticleSystem",
    "Thalgryn",
]
