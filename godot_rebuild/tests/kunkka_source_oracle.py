"""Execute Kunkka' actual recipes; no copied skill arithmetic in the oracle.

The existing source_env executes balanced _core catalogs, Hero construction,
BossHeroSkills, HP setter, projectile update, clocks and respawn read-only.
"""
import json
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import source_fixture as boss_fixture, _cast_case, state, targets
from source_shared_boss_oracle import write_native_definitions

FIXTURE = Path(__file__).parent / "fixtures/kunkka_source.json"
KIND = "kunkka"


def source_fixture():
    result = boss_fixture((KIND,))
    env = source_env()
    H = env["SourceHero"]
    sample = H(KIND, "red", 500, 340)
    result["definition"] = {
        native: getattr(sample, source) for native, source in (
            ("max_hp", "base_hp"), ("damage", "base_damage"),
            ("speed_px_per_tick", "speed"), ("attack_range_px", "range"),
            ("attack_cooldown_ticks", "attack_cooldown"),
            ("base_skill", "skill_damage_base"), ("skill_range_px", "skill_range"),
            ("skill_cooldown_max", "skill_cooldown_max"),
            ("dmg_school", "dmg_school"), ("is_melee", "is_melee_hero"),
            ("w_cooldown_max", "w_cooldown_max"),
            ("e_cooldown_max", "e_cooldown_max"), ("r_cooldown_max", "r_cooldown_max"))}
    result.update(clocks=[], healing=[], selection=[])
    for key in "qwer":
        # Exact radial boundaries, including behind/vertical, exact and +1.
        coords = [(550, 340), (619, 340), (620, 340), (621, 340),
                  (629, 340), (630, 340), (631, 340),
                  (649, 340), (650, 340), (651, 340), (699, 340),
                  (700, 340), (701, 340), (350, 340), (500, 490), (500, 491)]
        _cast_case(result, H, KIND, key, coords, 0)
        # Directional strips (strict projection/width); mirrored/vertical/diagonal.
        for coords in (
            [(550, 340), (499, 340), (500, 340), (501, 340),
             (749, 340), (750, 340), (751, 340), (799, 340), (800, 340), (801, 340),
             (600, 409), (600, 410), (600, 411), (600, 419), (600, 420), (600, 421)],
            [(500, 390), (500, 589), (500, 590), (500, 639), (500, 640),
             (569, 440), (570, 440), (579, 440), (580, 440)],
            [(450, 340), (251, 340), (250, 340), (201, 340), (200, 340)],
            [(530, 380), (530, 395), (510, 330), (575, 440), (700, 500)],
            # Target-centred W120 and R200, not centered on the caster.
            [(620, 340), (739, 340), (740, 340), (741, 340),
             (819, 340), (820, 340), (821, 340), (419, 340), (420, 340), (421, 340)],
        ):
            _cast_case(result, H, KIND, key, coords, 0)
        h = H(KIND, "red", 500, 340)
        enemies = targets([(550, 340)])
        called = []
        recipe = h.skills._SKILL_REGISTRY[KIND][key]
        original = getattr(h.skills, recipe)
        # Preserve method arity: source dispatch inspects the callable signature.
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
        assert result == json.loads(FIXTURE.read_text()), "Kunkka source behavior drift"
    print("PASS: Kunkka real QWER, dispatch, radii, clocks/recast, heal/anti-heal, target quirks, attacks, respawn, upgrades")
