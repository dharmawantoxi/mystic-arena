import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, "/home/user/mystic-arena")
import pygame
pygame.init()
import _core
from _core import Game
from _entity import Hero

screen = pygame.display.set_mode((_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT))
out = "/home/user/mystic-arena/tools/shots_game"


def make_game():
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
    for _ in range(30):
        g.update()
    return g


g = make_game()

# VICTORY
g.state = "victory"
g.score = 12345
g.wave_number = 12
g.total_kills = 87
g.max_combo = 7
g.meta_reward_earned = 3000
g.new_best_score = True
g.new_best_time = False
g.draw()
pygame.image.save(screen, os.path.join(out, "10_victory.png"))
print("saved victory")

# DEFEAT
g2 = make_game()
g2.state = "defeat"
g2.score = 4321
g2.wave_number = 5
g2.draw()
pygame.image.save(screen, os.path.join(out, "11_defeat.png"))
print("saved defeat")

# CASTLE POPUP (nexus_blue)
g3 = make_game()
g3.open_popup(g3.blue_base, "nexus_blue")
g3.draw()
pygame.image.save(screen, os.path.join(out, "12_castle_popup.png"))
print("saved castle popup; buttons:",
      [k for k in g3.ui_buttons if k.startswith("popup")])

# IN-GAME HERO SHOP (tombol H)
g4 = make_game()
g4.shop_open = True
g4.draw()
pygame.image.save(screen, os.path.join(out, "13_heroshop_ingame.png"))
print("saved in-game hero shop")
