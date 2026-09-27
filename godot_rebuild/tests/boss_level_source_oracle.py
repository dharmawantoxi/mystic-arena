"""Execute the REAL level 5+ boss recipes from hero_skills/_bundle.py.

Shared capture engine for the per-level boss oracles (level five, six, ...).
It runs the actual source dispatcher (`BossHeroSkills._generic_cast`), the real
target gate, the real recipe method, the real cooldown trigger, the real
`update_timers`, the real basic attack and the real respawn for every ID it is
given. No kit arithmetic is replicated here: the per-level oracle only names
its own IDs, so a shared capture engine is never a shared hero kit.
"""
import json
import sys

from starter_finish_source_oracle import source_env, state as starter_state
from boss_level_one_source_oracle import targets

# Cast geometry cases: empty field, mixed cluster with an explicit target,
# target behind the hero, far target, point-blank, and the exact gate edges.
CAST_CASES = (
    ([], -1),
    (
        [
            (620, 340),
            (550, 340),
            (600, 340),
            (601, 340),
            (590, 340),
            (591, 340),
            (640, 340),
            (680, 340),
            (681, 340),
        ],
        0,
    ),
    ([(450, 340), (550, 340)], -1),
    ([(900, 340), (550, 340)], 0),
    ([(500, 340)], 0),
    ([(510, 340)], 0),
    ([(700, 340), (690, 340), (710, 340), (900, 340)], 0),
)
# Trace modes: plain expiry, upgrade while the effect is live, target death
# and explicit retarget (source recipes read h.target at cast time only).
MODES = ("normal", "move_upgrade", "target_dies", "retarget")
LENGTH = 601
TRACE_TICKS = (
    1,
    2,
    29,
    30,
    59,
    60,
    119,
    120,
    179,
    180,
    299,
    300,
    479,
    480,
    481,
    599,
    600,
    601,
)
TRACE_POSITIONS = [(550, 340), (600, 340), (590, 340), (610, 340), (580, 340)]


def state(hero, enemies):
    result = starter_state(hero, enemies)
    for native, source in (("rage_timer", "rage_timer"), ("defense_timer", "defense_timer")):
        if hasattr(hero, source):
            result[native] = getattr(hero, source)
    # rage_active/defense_boost are intentionally NOT captured: the native
    # state models them as "timer > 0" exactly like the other boss suites, so
    # only the timers and the damage they reset are observable.
    result["damage"] = hero.damage
    result["facing"] = hero.facing
    result["position"] = [hero.x, hero.y]
    result["target_id"] = enemies.index(hero.target) if hero.target in enemies else -1
    return result


def source_fixture(ids):
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result = dict(casts=[], traces=[], attacks=[], respawn=[], catalog={}, levels={})
    for kind in ids:
        probe = H(kind, "red", 500, 340)
        recipe = probe.skills._SKILL_REGISTRY[kind]
        assert len(recipe) == 4 and all(
            hasattr(probe.skills, method) for method in recipe.values()
        ), f"Re-audit source registry: {kind}"
        result["catalog"][kind] = dict(
            recipe=recipe, damage=env["get_all_hero_types"]()[kind]["damage"]
        )
        reach = max(int(probe.skill_range), 140)
        for key in "qwer":
            for coords, selected in CAST_CASES:
                _cast_case(result, H, kind, key, coords, selected)
            for radius in (reach - 1, reach, reach + 1):
                _cast_case(result, H, kind, key, [(500 + radius, 340)], -1)
            for mode in MODES:
                hero = H(kind, "red", 500, 340)
                hero.hp = 500
                enemies = targets(TRACE_POSITIONS)
                hero.target = enemies[0]
                enemies[0].attack_timer = 90
                assert getattr(hero.skills, "cast_" + key)(
                    enemies, [], []
                ), f"Source cast refused: {kind} {key}"
                rows = []
                for tick in range(1, LENGTH + 1):
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
                    if tick in TRACE_TICKS:
                        rows.append(dict(tick=tick, state=state(hero, enemies)))
                result["traces"].append(
                    dict(
                        hero=kind,
                        key=key,
                        mode=mode,
                        positions=TRACE_POSITIONS,
                        length=LENGTH,
                        rows=rows,
                    )
                )
        hero = H(kind, "red", 500, 340)
        enemy = targets([(560, 340)])[0]
        hero.target = enemy
        hero._do_attack()
        rows = []
        for tick in range(18):
            if tick:
                env["tick_projectiles"](hero)
                env["tick_clocks"](hero)
            rows.append(
                dict(
                    tick=tick,
                    hp=enemy.hp,
                    attack_timer=hero.attack_timer,
                    positions=[[p["x"], p["y"]] for p in hero.projectiles],
                )
            )
        result["attacks"].append(dict(hero=kind, target_position=[560, 340], rows=rows))
        hero = H(kind, "red", 500, 340)
        enemies = targets([(550, 340)])
        for key in "qwer":
            assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        hero.attack_timer = 17
        hero.hp, hero.alive = 0, False
        env["respawn"](hero)
        result["respawn"].append(dict(hero=kind, state=state(hero, enemies)))
        hero = H(kind, "red", 500, 340)
        hero.hp = 1
        result["levels"][kind] = []
        for level in range(1, 16):
            result["levels"][kind].append(
                dict(
                    level=level,
                    hp=hero.hp,
                    damage=hero.damage,
                    max_hp=hero.max_hp,
                    skill_value=hero.skill_damage,
                    price=hero.upgrade_cost(),
                )
            )
            assert hero.upgrade() == (level < 15)
    return json.loads(json.dumps(result))


def _cast_case(result, H, kind, key, coords, selected):
    """Same harness as the earlier boss oracles but with this engine's state."""
    hero = H(kind, "red", 500, 340)
    hero.hp = 500
    enemies = targets(coords)
    if selected >= 0:
        hero.target = enemies[selected]
    ok = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    repeat = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    result["casts"].append(
        dict(
            hero=kind,
            key=key,
            positions=coords,
            target=selected,
            ok=ok,
            repeat=repeat,
            state=state(hero, enemies),
        )
    )
