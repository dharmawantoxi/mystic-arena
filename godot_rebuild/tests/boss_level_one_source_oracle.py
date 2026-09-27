"""Execute actual BossHeroSkills recipes (not boss AI and not invented generic kits).

Read-only Hero/source clocks/projectile/respawn harness shared with starter tests.
The source dispatcher, target gate and all four recipes run for each registered ID.
"""
import json
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env, state as starter_state
from sylara_source_oracle import Target

FIXTURE = Path(__file__).parent / "fixtures/boss_level_one_source.json"
IDS = ("gornak", "morgath", "drakar", "abaddon")


def targets(coords):
    result = [Target(*p) for p in coords]
    for target in result:
        target.max_hp = 10000
    return result


def state(hero, enemies):
    result = starter_state(hero, enemies)
    for native, source in (("rage_timer", "rage_timer"), ("defense_timer", "defense_timer"),
                           ("flux_timer", "flux_active_timer"), ("clones_timer", "clones_active_timer")):
        result[native] = getattr(hero, source)
    result["flux_target_id"] = enemies.index(hero.flux_target) if hero.flux_target in enemies else -1
    result["target_id"] = enemies.index(hero.target) if hero.target in enemies else -1
    result["blink_from"] = [hero.blink_from_x, hero.blink_from_y]
    result["mana_void_origin"] = [hero.mana_void_x, hero.mana_void_y]
    return result


def source_fixture():
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result = dict(casts=[], traces=[], attacks=[], respawn=[], execute=[], defense=[], catalog={})
    for kind in IDS:
        h = H(kind, "red", 500, 340)
        recipe = h.skills._SKILL_REGISTRY[kind]
        assert len(recipe) == 4 and all(hasattr(h.skills, method) for method in recipe.values())
        result["catalog"][kind] = dict(recipe=recipe, damage=env["get_all_hero_types"]()[kind]["damage"])
        for key in "qwer":
            for coords, selected in [([], -1), ([(620, 340), (550, 340), (600, 340),
                 (601, 340), (590, 340), (591, 340), (640, 340), (680, 340), (681, 340)], 0),
                 ([(450, 340), (550, 340)], -1), ([(900, 340), (550, 340)], 0),
                 ([(500, 340)], 0), ([(510, 340)], 0)]:
                _cast_case(result, H, kind, key, coords, selected)
            reach = max(int(h.skill_range), 140)
            for radius in (reach-1, reach, reach+1):
                _cast_case(result, H, kind, key, [(500+radius, 340)], -1)
            for mode in ("normal", "move_upgrade", "target_dies", "retarget"):
                hero = H(kind, "red", 500, 340)
                hero.hp = 500
                coords = [(550, 340), (600, 340), (590, 340), (610, 340), (580, 340)]
                enemies = targets(coords)
                hero.target = enemies[0]
                enemies[0].attack_timer = 90
                assert getattr(hero.skills, "cast_"+key)(enemies, [], [])
                rows = []
                for tick in range(1, 482):
                    if tick == 2 and mode == "move_upgrade":
                        hero.x += 100
                        enemies[0].x += 200
                        assert hero.upgrade()
                    if tick == 2 and mode == "target_dies":
                        enemies[0].alive = False
                    if tick == 2 and mode == "retarget":
                        hero.target = enemies[1]
                    env["tick_clocks"](hero)
                    hero.skills.update_timers(enemies, [], [])
                    if tick in (1, 2, 29, 30, 39, 40, 179, 180, 239, 240, 299, 300, 479, 480, 481):
                        rows.append(dict(tick=tick, state=state(hero, enemies)))
                result["traces"].append(dict(hero=kind, key=key, mode=mode, positions=coords,
                    length=481, rows=rows))
        hero = H(kind, "red", 500, 340)
        enemy = targets([(560, 340)])[0]
        hero.target = enemy
        hero._do_attack()
        rows = []
        for tick in range(18):
            if tick:
                env["tick_projectiles"](hero)
                env["tick_clocks"](hero)
            rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=hero.attack_timer,
                positions=[[p['x'], p['y']] for p in hero.projectiles]))
        result["attacks"].append(dict(hero=kind, target_position=[560, 340], rows=rows))
        hero = H(kind, "red", 500, 340)
        enemies = targets([(550, 340)])
        for key in "qwer":
            assert getattr(hero.skills, "cast_"+key)(enemies, [], [])
        hero.attack_timer = 17
        hero.hp, hero.alive = 0, False
        env["respawn"](hero)
        result["respawn"].append(dict(hero=kind, state=state(hero, enemies)))
    # Execute is strict <30%, with int before doubling; leveled odd values tested.
    for level in (1, 2, 15):
        for hp in (2999, 3000, 3001):
            hero = H("drakar", "red", 500, 340)
            while hero.level < level:
                assert hero.upgrade()
            enemy = targets([(550, 340)])[0]
            enemy.hp = hp
            assert hero.skills.cast_r([enemy], [], [])
            result["execute"].append(dict(level=level, hp=hp, after=max(0, enemy.hp)))
    for kind in IDS:
        for school in ("physical", "magic"):
            hero = H(kind, "red", 500, 340)
            hero.skills.cast_e(targets([(550, 340)]), [], [])
            before = hero.hp
            hero.take_damage(100, "blue", school=school)
            result["defense"].append(dict(hero=kind, school=school, before=before, hp=hero.hp))
    return json.loads(json.dumps(result))


def _cast_case(result, H, kind, key, coords, selected):
    hero = H(kind, "red", 500, 340)
    hero.hp = 500
    enemies = targets(coords)
    if selected >= 0:
        hero.target = enemies[selected]
    ok = getattr(hero.skills, "cast_"+key)(enemies, [], [])
    repeat = getattr(hero.skills, "cast_"+key)(enemies, [], [])
    result["casts"].append(dict(hero=kind, key=key, positions=coords, target=selected,
        ok=ok, repeat=repeat, state=state(hero, enemies)))


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Level-one boss source drift"
    print("PASS: four real boss recipes, gates, timers, basic attacks, respawn, execute and flags")
