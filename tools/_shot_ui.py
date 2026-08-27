# Render screenshot seluruh UI menu untuk review (headless).
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import _core  # noqa: E402
from _core import Menu, MenuState  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT))
menu = Menu(screen)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(out, exist_ok=True)


def grab(name, frames=40):
    for _ in range(frames):
        menu.update()
    menu.draw()
    pygame.image.save(screen, os.path.join(out, name))
    print("saved", name)


# 1. Main menu
menu.state = MenuState.MAIN
grab("01_main_menu.png")

# 2. Level select
menu.state = MenuState.LEVEL_SELECT
grab("02_level_select.png")

# 3. Hero shop
menu.state = MenuState.HERO_SHOP
grab("03_hero_shop.png")

# 4. Settings
menu.state = MenuState.SETTINGS
grab("04_settings.png")

# 5. How to play
menu.state = MenuState.HOW_TO_PLAY
grab("05_how_to_play.png")

# 6. Credits
menu.state = MenuState.CREDITS
grab("06_credits.png")

# 7. Slot select
menu.state = MenuState.SLOT_SELECT
grab("08_slot_select.png")

# 8. Dialog: konfirmasi delete slot
menu.slot_delete_confirm = 1
menu.draw()
pygame.image.save(screen, os.path.join(out, "09_dialog_delete.png"))
menu.slot_delete_confirm = None

# 9. Dialog: konfirmasi reset (dari Settings)
menu.state = MenuState.SETTINGS
menu.reset_confirm = True
menu.draw()
pygame.image.save(screen, os.path.join(out, "10_dialog_reset.png"))
menu.reset_confirm = False

# 10. Dialog: konfirmasi cloud upload (dari Settings)
menu.cloud_confirm = "upload"
menu.draw()
pygame.image.save(screen, os.path.join(out, "11_dialog_cloud.png"))
menu.cloud_confirm = None

# 11. Dialog: konfirmasi keluar (dari Main menu)
menu.state = MenuState.MAIN
menu.exit_confirm = "quit"
menu.draw()
pygame.image.save(screen, os.path.join(out, "12_dialog_quit.png"))
menu.exit_confirm = None

# 12. Pause menu (di atas latar gelap)
menu.state = MenuState.PAUSE
menu.pause_mode = True
grab("07_pause.png")

print("done")
