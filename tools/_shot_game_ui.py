# Screenshot UI in-game (panel hero, toko item, popup) untuk review.
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import _core  # noqa: E402
from _core import Game  # noqa: E402
from _entity import Hero  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots_game")
os.makedirs(out, exist_ok=True)

g = Game(screen, level_number=1)
import __main__
__main__.game_instance = g
for nm in ("level_intro", "boss_intro"):
    o = getattr(g, nm, None)
    if o is not None and hasattr(o, "handle_skip"):
        try:
            o.handle_skip(key=pygame.K_SPACE)
        except Exception:
            pass
g.gold = 99999
g.heroes.append(Hero("grimjaw", "blue", 300, 380))
for _ in range(20):
    g.update()


def grab(name):
    g.draw()
    pygame.image.save(screen, os.path.join(out, name))
    print("saved", name)


# 1. Gameplay biasa
grab("01_gameplay.png")

# 2. Panel hero (hero terseleksi)
g.selected_hero = g.heroes[0]
g.selected_hero.selected = True
grab("02_hero_panel.png")

# 3. Item shop (Item Forge)
g.item_shop_open = True
grab("03_item_shop.png")
g.item_shop_open = False

# 4. Build popup (slot kosong base biru)
try:
    slots = [s for s in g.build_slots_blue if not s["taken"]]
    if slots:
        g.open_build_popup(slots[0])
        grab("04_build_popup.png")
        g.close_build_popup()
except Exception as e:
    print("build popup skip:", e)

# 5. Popup upgrade tower (bangun dulu satu tower)
try:
    g.try_build_tower("archer")
    g.update()
    tw = [t for t in g.towers if t.team == "blue"]
    if tw:
        g.open_popup(tw[-1], "tower")
        grab("05_tower_popup.png")
        g.close_popup()
except Exception as e:
    print("tower popup skip:", e)

print("done")
