# Render screenshot UI top up untuk review (headless).
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import _core  # noqa: E402
from _core import Menu, MenuState, TOPUP_PACKAGES  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT))
menu = Menu(screen)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(out, exist_ok=True)


def grab(name):
    pygame.image.save(screen, os.path.join(out, name))
    print("saved", name)


# 1. Hero shop (tombol + TOP UP terlihat)
menu.state = MenuState.HERO_SHOP
menu.draw()
grab("01_hero_shop.png")

# 2. Dialog fase select
menu._on_button_click("topup_open")
menu.draw()
grab("02_topup_select.png")

# 3. Dialog fase processing
menu._on_button_click("topup_pkg_0")
menu._on_button_click("topup_pay")
for _ in range(20):
    menu.update()
menu.draw()
grab("03_topup_processing.png")

# 4. Dialog fase success
for _ in range(60 * 3):
    menu.update()
    if menu.topup_phase == "success":
        break
menu.draw()
grab("04_topup_success.png")

print("gold sekarang:", menu.meta_gold)
