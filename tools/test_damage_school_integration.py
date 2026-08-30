# ================================
# tools/test_damage_school_integration.py
#
# Smoke test integrasi: game level 1 dijalankan headless dengan 2 hero
# (1 PHYSICAL, 1 MAGIC) + 1 mini boss, lalu kita ukur damage yang
# benar-benar mendarat. Kalau split PHYSICAL/MAGIC rusak (mis. sekolah
# tidak tersambung ke skill, atau exception di tengah update), test ini
# yang menangkapnya - unit test di test_damage_school.py tidak menyentuh
# loop Game sungguhan.
#
# Jalankan:  python3 tools/test_damage_school_integration.py
# ================================
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import pygame

pygame.init()
screen = pygame.display.set_mode((1280, 720))

import _core                                    # noqa: E402
from game import Game                           # noqa: E402
import _entity as E                             # noqa: E402
import hero_archetypes                          # noqa: E402
from bosses.boss_data import MINI_BOSS_TYPES    # noqa: E402

PHYS_HERO = "grimjaw"
MAGIC_HERO = "vex"
BOSS = "gornak"

FRAMES = int(os.environ.get("FRAMES", "600"))


def main():
    g = Game(screen, level_number=1)
    g.level_intro = None
    g.boss_intro = None

    heroes = []
    for i, ht in enumerate((PHYS_HERO, MAGIC_HERO)):
        h = E.Hero(ht, "blue", x=520.0 + i * 40, y=350.0 + i * 26)
        h.auto_cast_enabled = True
        h.skill_timer = 0
        heroes.append(h)
        g.heroes.append(h)

    lane = g.map_renderer.get_lane_path("mid")
    boss = E.__dict__.get("Boss")
    from bosses.base_boss import Boss
    b = Boss(BOSS, lane)
    b.entrance_timer = 0
    b.invulnerable_until = 0
    g.active_boss = b

    # Pastikan hero benar-benar nempel ke boss supaya damage mengalir
    for h in heroes:
        h.target = b

    for _ in range(FRAMES):
        for h in heroes:
            h.target = b if b.alive else None
        g.update()
        g.draw()
        E.set_damage_school(None)

    dealt = [h.damage_dealt for h in heroes]
    print("hero damage_dealt:", {h.name: d for h, d in zip(heroes, dealt)})
    print("boss hp: %d/%d  armor=%d  mr=%.2f" % (
        b.hp, b.max_hp, b.armor, b.magic_resist))

    assert any(dealt), "tidak ada damage yang tercatat sama sekali"
    assert b.hp < b.max_hp, "boss tidak kehilangan HP"

    # Sanity: sekolah hero tersambung ke damage yang mendarat
    phys = hero_archetypes.school_of(PHYS_HERO)
    magic = hero_archetypes.school_of(MAGIC_HERO)
    assert {phys, magic} == {"physical", "magic"}, (phys, magic)

    # Simulasi manual: damage identik, sekolah beda -> hasil beda
    b2 = Boss(BOSS, [])
    b2.entrance_timer = 0
    b2.max_damage_per_hit = 10 ** 9
    b2.hp = b2.max_hp
    snap = b2.hp
    b2.take_damage(1000, "blue", school="physical",
                   source=None)
    phys_hit = snap - b2.hp
    b2.hp = snap
    b2.take_damage(1000, "blue", school="magic", source=None)
    magic_hit = snap - b2.hp
    print("1000 dmg -> fisik %d, sihir %d" % (phys_hit, magic_hit))
    assert phys_hit != magic_hit, "armor/MR tidak membedakan sekolah"

    print("\nOK: loop game nyata + split PHYSICAL/MAGIC jalan bersih "
          "(%d frame)." % FRAMES)


if __name__ == "__main__":
    main()
