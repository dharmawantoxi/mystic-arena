#!/usr/bin/env python3
"""Close-up review render untuk KAIZEN DOODLE - skala besar (zoom)."""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
from types import SimpleNamespace

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_kaizen as K

try:
    from heroes import kaizen_fx as _kzfx
    _kzfx.KAIZEN_FX_ENABLED = False
    K._LIVE_MOD = False
except Exception:
    pass

screen = pygame.Surface((900, 640))
screen.fill((250, 246, 236))
f_title = pygame.font.Font(None, 36)
f_note = pygame.font.Font(None, 18)
screen.blit(f_title.render("KAIZEN — DOODLE CLOSE-UP", True, (20, 17, 22)), (30, 20))

# render large native hero then upscale crop 2x
base = pygame.Surface((360, 430), pygame.SRCALPHA)
h = _ProbeEntity("kaizen", 180, 250)
h.pulse = 1.25
h.direction = 1
h.facing = 1
K._draw_swordsman_rim_light(base, 180, 238, h.pulse)
K._draw_wind_platform(base, 180, 308, h.pulse, None)
K._draw_kaizen_idle(base, h, 180, 260)

# crop tight bbox
rect = base.get_bounding_rect(min_alpha=4).inflate(24, 24)
crop = base.subsurface(rect.clip(base.get_rect()))
zoom = pygame.transform.scale(crop, (crop.get_width() * 3, crop.get_height() * 3))
screen.blit(zoom, (30, 70))
screen.blit(f_note.render("boiling ink outline • spidol bercelah kertas • "
                          "arsiran pensil • gel-pen shine", True, (80, 74, 90)),
            (30, 610))

out = os.path.join(ROOT, "docs", "kaizen_doodle_closeup.png")
pygame.image.save(screen, out)
print(out)
