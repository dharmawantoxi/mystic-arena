"""Execute Krobellus' actual recipes; no copied skill arithmetic in the oracle.

The existing source_env executes balanced _core catalogs, Hero construction,
BossHeroSkills, HP setter, projectile update, clocks and respawn read-only.
"""
import json
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import source_fixture as boss_fixture, _cast_case, state, targets
from source_shared_boss_oracle import write_native_definitions

FIXTURE = Path(__file__).parent / "fixtures/krobellus_source.json"
KIND = "krobellus"


def source_fixture():
    result = boss_fixture((KIND,))
    env = source_env()
    H = env["SourceHero"]
    result.update(clocks=[], healing=[], selection=[])
    for key in "qwer":
        # All three radial boundaries, including behind/vertical, exact and +1.
        coords = [(550, 340), (619, 340), (620, 340), (621, 340),
                  (649, 340), (650, 340), (651, 340), (699, 340),
                  (700, 340), (701, 340), (350, 340), (500, 490), (500, 491)]
        _cast_case(result, H, KIND, key, coords, 0)
        h = H(KIND, "red", 500, 340)
        enemies = targets([(550, 340)])
        called = []
        recipe = h.skills._SKILL_REGISTRY[KIND][key]
        original = getattr(h.skills, recipe)
        # Preserve method arity: source dispatch inspects the callable signature.
        if key == "e":
            def tracked(hero):
                called.append(recipe)
                return original(hero)
        else:
            def tracked(hero, opponents):
                called.append(recipe)
                return original(hero, opponents)
        setattr(h.skills, recipe, tracked)
        assert getattr(h.skills, "cast_" + key)(enemies, [], [])
        assert called == [recipe], "Must execute the original custom recipe, not fallback"
        timer = dict(q="skill_timer", w="w_cooldown", e="e_cooldown", r="r_cooldown")[key]
        duration = getattr(h, timer)
        rows = []
        for tick in range(1, duration + 1):
            env["tick_clocks"](h)
            h.skills.update_timers(enemies, [], [])
            if tick in (1, duration - 1, duration):
                rows.append(dict(tick=tick, state=state(h, enemies)))
                if tick < duration:
                    assert not getattr(h.skills, "cast_" + key)(enemies, [], [])
        assert getattr(h.skills, "cast_" + key)(enemies, [], [])
        result["clocks"].append(dict(key=key, duration=duration, rows=rows, recast=state(h, enemies)))
        for mode in ("dead_selected", "friendly_unselected", "stun_max"):
            h = H(KIND, "red", 500, 340)
            enemies = targets([(550, 340), (600, 340), (540, 340)])
            h.target = enemies[0]
            if mode == "dead_selected":
                enemies[0].alive = False
            if mode == "friendly_unselected":
                enemies[1].team = "red"
            if mode == "stun_max":
                enemies[0].attack_timer = 200
            assert getattr(h.skills, "cast_" + key)(enemies, [], [])
            result["selection"].append(dict(key=key, mode=mode, state=state(h, enemies)))
    for key in "er":
        for level in (1, 2, 15):
            for reduction in (0, 0.75, 1):
                for near_cap in (False, True):
                    h = H(KIND, "red", 500, 340)
                    while h.level < level:
                        assert h.upgrade()
                    h.hp = h.max_hp - 1 if near_cap else 500
                    initial = h.hp
                    h.anti_heal_amount, h.anti_heal_timer = reduction, 900
                    enemies = targets([(550, 340)])
                    enemies[0].hp = enemies[0].max_hp = 100000
                    assert getattr(h.skills, "cast_" + key)(enemies, [], [])
                    result["healing"].append(dict(key=key, level=level, reduction=reduction,
                        initial=initial, hp=h.hp, enemy_hp=enemies[0].hp))
    return json.loads(json.dumps(result))


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":")) + "\n")
        write_native_definitions(source_env(), (KIND,), write_membership=False)
    else:
        assert result == json.loads(FIXTURE.read_text()), "Krobellus source behavior drift"
    print("PASS: Krobellus real QWER, dispatch, radii, clocks/recast, heal/anti-heal, target quirks, attacks, respawn, upgrades")
