"""Execute actual Ancient Apparition and Nyzrak hero recipes from hero_skills/_bundle.py.

Uses same harness as boss_level_one: real SourceHero, real timers, real projectile loop,
target gate, slow/stun, respawn and level 1-15.
"""
import json
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env, state as starter_state
from sylara_source_oracle import Target
from boss_level_one_source_oracle import source_fixture as _boss_one_fixture, _cast_case, targets

FIXTURE = Path(__file__).parent / "fixtures/boss_level_three_source.json"
IDS = ("ancient_apparition", "nyzrak")


def state(hero, enemies):
    result = starter_state(hero, enemies)
    # level-one style timers
    for native, source in (
        ("vortex_timer", "vortex_active_timer"),
        ("shield_timer", "shield_timer"),
    ):
        if hasattr(hero, source):
            result[native] = getattr(hero, source)
    if hasattr(hero, "vortex_x") and hasattr(hero, "vortex_y"):
        result["vortex_origin"] = [hero.vortex_x, hero.vortex_y]
    if hasattr(hero, "shield_active"):
        result["shield_active"] = bool(hero.shield_active)
    # target tracking
    if hasattr(hero, "target"):
        result["target_id"] = enemies.index(hero.target) if hero.target in enemies else -1
    else:
        result["target_id"] = -1
    # position for AA Q fallback
    result["position"] = [hero.x, hero.y]
    # w_dir / r_dir not needed for parity but capture if present
    if hasattr(hero, "w_dir_x"):
        result["w_dir"] = [hero.w_dir_x, hero.w_dir_y]
    if hasattr(hero, "r_dir_x"):
        result["r_dir"] = [hero.r_dir_x, hero.r_dir_y]
    return result


def source_fixture(ids=IDS):
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result = dict(casts=[], traces=[], attacks=[], respawn=[], catalog={}, levels={})
    for kind in ids:
        h = H(kind, "red", 500, 340)
        recipe = h.skills._SKILL_REGISTRY[kind]
        assert len(recipe) == 4 and all(hasattr(h.skills, method) for method in recipe.values())
        result["catalog"][kind] = dict(recipe=recipe, damage=env["get_all_hero_types"]()[kind]["damage"])
        for key in "qwer":
            for coords, selected in [
                ([], -1),
                ([(620, 340), (550, 340), (600, 340), (601, 340), (590, 340), (591, 340), (640, 340), (680, 340), (681, 340)], 0),
                ([(450, 340), (550, 340)], -1),
                ([(900, 340), (550, 340)], 0),
                ([(500, 340)], 0),
                ([(510, 340)], 0),
            ]:
                _cast_case(result, H, kind, key, coords, selected)
            reach = max(int(h.skill_range), 140)
            for radius in (reach - 1, reach, reach + 1):
                _cast_case(result, H, kind, key, [(500 + radius, 340)], -1)
            for mode in ("normal", "move_upgrade", "target_dies", "retarget"):
                hero = H(kind, "red", 500, 340)
                hero.hp = 500
                coords = [(550, 340), (600, 340), (590, 340), (610, 340), (580, 340)]
                enemies = targets(coords)
                hero.target = enemies[0]
                enemies[0].attack_timer = 90
                assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
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
                    if tick in (1, 2, 19, 20, 29, 30, 39, 40, 59, 60, 89, 90, 119, 120, 149, 150, 179, 180, 239, 240, 299, 300, 359, 360, 479, 480, 481):
                        rows.append(dict(tick=tick, state=state(hero, enemies)))
                result["traces"].append(dict(hero=kind, key=key, mode=mode, positions=coords, length=481, rows=rows))
        hero = H(kind, "red", 500, 340)
        enemy = targets([(560, 340)])[0]
        hero.target = enemy
        hero._do_attack()
        rows = []
        for tick in range(18):
            if tick:
                env["tick_projectiles"](hero)
                env["tick_clocks"](hero)
            rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=hero.attack_timer, positions=[[p['x'], p['y']] for p in hero.projectiles]))
        result["attacks"].append(dict(hero=kind, target_position=[560, 340], rows=rows))
        hero = H(kind, "red", 500, 340)
        enemies = targets([(550, 340)])
        for key in "qwer":
            assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        hero.attack_timer = 17
        hero.hp, hero.alive = 0, False
        env["respawn"](hero)
        result["respawn"].append(dict(hero=kind, state=state(hero, enemies)))
        h = H(kind, "red", 500, 340)
        h.hp = 1
        result["levels"][kind] = []
        for level in range(1, 16):
            result["levels"][kind].append(dict(level=level, hp=h.hp, damage=h.damage, max_hp=h.max_hp, skill_value=h.skill_damage, price=h.upgrade_cost()))
            assert h.upgrade() == (level < 15)
    return json.loads(json.dumps(result))


def _cast_case_local(result, H, kind, key, coords, selected):
    return _cast_case(result, H, kind, key, coords, selected)


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Level-three boss source drift"
    print("PASS: Ancient Apparition + Nyzrak real recipes, gates, timers, attacks, respawn")
