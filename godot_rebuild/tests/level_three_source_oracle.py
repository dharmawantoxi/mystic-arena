"""Actual level-three recipes: Ancient Apparition vortex beam kit and Nyzrak.

The four registry methods run from the original Python class; nothing is
re-implemented here. Extra state records what the source writes on the Hero
object, including the two Nyzrak shield flags that the original Hero class
never reads back.
"""
import json
import sys
from pathlib import Path

import boss_level_one_source_oracle as level_one
from boss_level_one_source_oracle import source_fixture as boss_fixture, targets
from starter_finish_source_oracle import source_env
from source_shared_boss_oracle import write_native_definitions

FIXTURE = Path(__file__).parent / "fixtures/level_three_source.json"
IDS = ("ancient_apparition", "nyzrak")
SAMPLES = (1, 19, 20, 21, 39, 40, 41, 99, 100, 101, 159, 160, 161,
           179, 180, 181, 200, 219, 220, 240, 260, 280, 300)


def apparition_state(hero):
    return dict(vortex=[hero.vortex_x, hero.vortex_y],
                vortex_active_timer=hero.vortex_active_timer,
                w_dir=[hero.w_dir_x, hero.w_dir_y],
                r_dir=[hero.r_dir_x, hero.r_dir_y])


def nyzrak_state(hero):
    # init_state never defines these, so an unread source attribute is False/0.
    return dict(shield_active=getattr(hero, "shield_active", False),
                shield_timer=getattr(hero, "shield_timer", 0))


level_one.STATE_EXTRAS["ancient_apparition"] = apparition_state
level_one.STATE_EXTRAS["nyzrak"] = nyzrak_state


def source_fixture():
    result = boss_fixture(IDS)
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result["dot"] = vortex_dot(env, H)
    result["shield"] = shield_flag(env, H)
    return json.loads(json.dumps(result))


def vortex_dot(env, H):
    """Real update_timers DOT: 180 tick clock, one hit every 20, then silence."""
    rows = []
    for mode in ("armed", "recast", "beam_only"):
        hero = H("ancient_apparition", "red", 500, 340)
        hero.hp = 500
        enemies = targets([(560, 340), (600, 340)])
        hero.target = enemies[0]
        key = "r" if mode == "beam_only" else "q"
        assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        samples = []
        for tick in range(1, 301):
            env["tick_clocks"](hero)
            hero.skills.update_timers(enemies, [], [])
            if tick == 100 and mode == "recast":
                # A real recast after the source Q cooldown has elapsed.
                hero.skill_timer = 0
                assert hero.skills.cast_q(enemies, [], [])
            if tick in SAMPLES:
                samples.append(dict(tick=tick, timer=hero.vortex_active_timer,
                    enemies=[dict(hp=e.hp, slow=e.slow_amount, slow_timer=e.slow_timer)
                             for e in enemies]))
        rows.append(dict(mode=mode, key=key, positions=[[560, 340], [600, 340]],
            length=300, rows=samples))
    return rows


def shield_flag(env, H):
    """The R shield flags are written but never consumed by the source Hero."""
    rows = []
    for school in ("physical", "magic"):
        for reduction in (0, 0.75):
            hero = H("nyzrak", "red", 500, 340)
            hero.hp = 400
            hero.anti_heal_amount, hero.anti_heal_timer = reduction, 900
            enemy = targets([(550, 340)])[0]
            hero.target = enemy
            assert hero.skills.cast_r([enemy], [], [])
            before = hero.hp
            hero.take_damage(100, "blue", school=school)
            rows.append(dict(school=school, reduction=reduction, before=before, hp=hero.hp,
                shield_active=hero.shield_active, shield_timer=hero.shield_timer,
                enemy_hp=enemy.hp, enemy_slow=enemy.slow_amount,
                enemy_slow_timer=enemy.slow_timer))
    return rows


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":")) + "\n")
        write_native_definitions(source_env(), list(IDS), write_membership=False)
    else:
        assert result == json.loads(FIXTURE.read_text()), "Level-three boss source drift"
    print("PASS: Ancient Apparition QWER + real vortex DOT, Nyzrak QWER, heal and unconsumed shield flag")
