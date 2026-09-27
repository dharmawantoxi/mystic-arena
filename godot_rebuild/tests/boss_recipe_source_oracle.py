"""Own-recipe BossHeroSkills beyond the level-one group, batch by batch.

The ID list is explicit AND cross-checked against the handoff manifest, so a
newly enabled hero can never slip in without a source oracle. Every ID here
keeps its own four registry methods: the source `_SKILL_REGISTRY` is read from
the real class and the shared `_fallback_cast` is never acceptable.
"""
import json
import sys
from pathlib import Path

import boss_level_one_source_oracle as level_one
from boss_level_one_source_oracle import source_fixture as boss_fixture, targets
from starter_finish_source_oracle import source_env
from source_shared_boss_oracle import write_native_definitions

FIXTURE = Path(__file__).parent / "fixtures/boss_recipe_source.json"
HANDLER = "boss_recipe_skills.gd"
IDS = ("ignis_drachorn",)
SAMPLES = (1, 99, 100, 101, 179, 199, 200, 201, 299, 300, 301, 479, 480, 481, 499, 500, 501, 599, 600, 601, 620)


def ignis_state(hero):
    return dict(dragon_form_active=hero.dragon_form_active,
                dragon_form_timer=hero.dragon_form_timer,
                dragon_blood_active=hero.dragon_blood_active,
                dragon_blood_timer=hero.dragon_blood_timer)


level_one.STATE_EXTRAS.update({kind: ignis_state for kind in IDS})


def manifest_ids():
    manifest = json.loads(
        (Path(__file__).parents[1] / "data/ai/hero_migration_status.json").read_text())
    return tuple(sorted(k for k, v in manifest["heroes"].items()
                        if v.get("native_handler") == HANDLER))


def check_ids(env):
    from hero_skills.boss_hero_skills import BossHeroSkills
    registry = BossHeroSkills._SKILL_REGISTRY
    assert manifest_ids() == tuple(sorted(IDS)), (
        "Manifest/oracle ID drift: " + str(manifest_ids()) + " vs " + str(tuple(sorted(IDS))))
    for kind in IDS:
        recipe = registry.get(kind)
        assert recipe and len(recipe) == 4, (kind, "missing own source recipe")
        assert all(hasattr(BossHeroSkills, name) for name in recipe.values()), (kind, recipe)
        assert kind in env["get_all_hero_types"](), kind
    return BossHeroSkills


def source_fixture():
    result = boss_fixture(IDS)
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    check_ids(env)
    H = env["SourceHero"]
    result["dragon"] = dragon_lifecycle(env, H)
    return json.loads(json.dumps(result))


def dragon_lifecycle(env, H):
    """Two buffs with different clocks, different resets and different damage."""
    # mode, first key, second key, tick the second skill lands, upgrade tick, length
    plans = (
        ("blood", "e", "", 0, 0, 500),
        ("form", "r", "", 0, 0, 620),
        ("blood_then_form", "e", "r", 500, 0, 620),
        ("form_then_blood", "r", "e", 100, 0, 620),
        ("blood_upgraded", "e", "", 0, 200, 500),
        ("form_upgraded", "r", "", 0, 300, 620),
    )
    rows = []
    for name, key, later, later_at, upgrade_at, length in plans:
        hero = H("ignis_drachorn", "red", 500, 340)
        hero.hp = 500
        enemies = targets([(560, 340), (700, 340)])
        hero.target = enemies[0]
        assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
        samples = []
        for tick in range(1, length + 1):
            if tick == later_at:
                assert getattr(hero.skills, "cast_" + later)(enemies, [], [])
            if tick == upgrade_at:
                assert hero.upgrade()
            env["tick_clocks"](hero)
            hero.skills.update_timers(enemies, [], [])
            if tick in SAMPLES:
                samples.append(dict(tick=tick, damage=hero.damage, hp=hero.hp,
                    level=hero.level, form=hero.dragon_form_active,
                    form_timer=hero.dragon_form_timer,
                    blood=hero.dragon_blood_active,
                    blood_timer=hero.dragon_blood_timer,
                    enemies=[dict(hp=e.hp, stun=e.attack_timer) for e in enemies]))
        rows.append(dict(mode=name, key=key, later=later, later_at=later_at,
            upgrade_at=upgrade_at, positions=[[560, 340], [700, 340]],
            length=length, catalog=env["get_all_hero_types"]()["ignis_drachorn"]["damage"],
            rows=samples))
    return rows


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":")) + "\n")
        write_native_definitions(source_env(), list(IDS), write_membership=False)
    else:
        assert result == json.loads(FIXTURE.read_text()), "Boss recipe source drift"
    print("PASS: own-recipe boss batch " + ", ".join(IDS) + " with QWER, cone/sweep, buffs and basic attacks")
