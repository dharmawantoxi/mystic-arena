# Render screenshot ITEM FORGE + popup detail item untuk review (headless).
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import _core  # noqa: E402  (font & ui_theme nyata)
import hero_items as hi  # noqa: E402
from hero_items import ItemShopUI, HeroItemInventory  # noqa: E402

pygame.init()
surf = pygame.Surface((1280, 720))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(out, exist_ok=True)


class FakeHero:
    def __init__(self, name, rng=40, role="Assassin"):
        self.name = name
        self.level = 5
        self.color = (90, 160, 255)
        self.alive = True
        self.range = rng
        self.role = role
        self.damage = 60
        self.base_hp = 700
        self.max_hp = 700
        self.hp = 700
        self.items = HeroItemInventory(self)


class FakeUI:
    def add_notification(self, text, color):
        pass


class FakeGame:
    def __init__(self):
        self.heroes = []
        self.gold = 25000
        self.selected_hero = None
        self.item_shop_open = True
        self.itemshop_target_hero = None
        self.itemshop_inspect_item = None
        self.itemshop_page = 0
        self.ui_buttons = {}
        self.ui = FakeUI()


g = FakeGame()
g.heroes = [FakeHero("Vex", rng=130, role="Mage"),
            FakeHero("Grimjaw", rng=45, role="Fighter")]
g.itemshop_target_hero = g.heroes[0]
g.heroes[0].items.add("octarine_core")

# 1. Grid biasa (PHYSICAL 1/2)
ItemShopUI.draw(surf, g)
pygame.image.save(surf, os.path.join(out, "forge_01_grid.png"))
print("saved forge_01_grid.png")

# 2. Detail item panjang: Searbrand (paling banyak mekanik)
g.itemshop_inspect_item = "searbrand"
ItemShopUI.draw(surf, g)
pygame.image.save(surf, os.path.join(out, "forge_02_detail_searbrand.png"))
print("saved forge_02_detail_searbrand.png")

# 3. Detail item MAGIC ONLY: Astral Codex (syarat + banyak efek)
g.itemshop_inspect_item = "astral_codex"
ItemShopUI.draw(surf, g)
pygame.image.save(surf, os.path.join(out, "forge_03_detail_astral.png"))
print("saved forge_03_detail_astral.png")

# 4. Detail item MELEE ONLY: Cleave Axe
g.itemshop_inspect_item = "cleave_axe"
ItemShopUI.draw(surf, g)
pygame.image.save(surf, os.path.join(out, "forge_04_detail_cleave.png"))
print("saved forge_04_detail_cleave.png")

# 5. Detail item sederhana: Moon Shard
g.itemshop_inspect_item = "moon_shard"
ItemShopUI.draw(surf, g)
pygame.image.save(surf, os.path.join(out, "forge_05_detail_moonshard.png"))
print("saved forge_05_detail_moonshard.png")

# 6. Detail Scarlet Bulwark (block + active + aura sekutu)
g.itemshop_inspect_item = "scarlet_bulwark"
ItemShopUI.draw(surf, g)
pygame.image.save(surf, os.path.join(out, "forge_06_detail_bulwark.png"))
print("saved forge_06_detail_bulwark.png")
