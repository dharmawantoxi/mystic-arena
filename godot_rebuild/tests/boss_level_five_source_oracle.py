"""Execute the actual Krobellus and Vhalzun recipes from hero_skills/_bundle.py.

Level 5 batch. Both IDs own four registry methods, so they must never join the
150-ID `_fallback_cast` group. Same read-only harness as boss_level_one/three/
four (real SourceHero, real Hero.update clocks, real projectile loop, real
respawn, real upgrade prices) and it additionally records:

* the exact per-slot AOE radius edges of each recipe (E is single target),
* target retention/retarget rules of BossHeroSkills._generic_cast,
* exact recast ticks for q/w/e/r (220/240/420/900 for these two heroes),
* self-heal semantics through the source hp property setter: cap first, then
  anti-heal reduction (Krobellus E + R, Vhalzun R),
* ranged homing basic attacks, respawn retention and levels 1-15.
"""
import json
import sys
from pathlib import Path

from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import state, targets, _cast_case

FIXTURE = Path(__file__).parent / "fixtures/boss_level_five_source.json"
IDS = ("krobellus", "vhalzun")
# Exact radii read from the source recipes; 0 = single-target recipe (E).
RADII = {
    "krobellus": {"q": 150, "w": 120, "e": 0, "r": 200},
    "vhalzun": {"q": 130, "w": 150, "e": 0, "r": 150},
}
# Slots that heal the caster, and which source value the heal is derived from.
HEALS = {
    "krobellus": {"e": "skill_damage", "r": "max_hp"},
    "vhalzun": {"r": "max_hp"},
}
ANTI_HEAL = (0.0, 0.5, 1.0)
HP_MODES = ("partial", "full", "one")
TRACE_TICKS = (1, 2, 19, 20, 29, 30, 39, 40, 59, 60, 89, 90, 119, 120,
               149, 150, 179, 180, 219, 220, 221, 239, 240, 241, 299, 300,
               359, 360, 419, 420, 421, 479, 480, 481, 599, 600, 601)


def _cooldowns(hero):
    return {"q": hero.skill_cooldown_max, "w": hero.w_cooldown_max,
            "e": hero.e_cooldown_max, "r": hero.r_cooldown_max}


def _radius_coords(radius):
    """Coordinates that straddle one exact radial boundary of a recipe."""
    if not radius:
        return [(500, 340), (510, 340), (560, 340)]
    return [(500, 340), (500 + radius - 1, 340), (500 + radius, 340),
            (500 + radius + 1, 340), (500, 340 + radius),
            (500, 340 - radius - 1), (500 - radius, 340),
            (500 - radius - 1, 340)]


def _dead_target_case(result, H, kind, key, coords, dead):
    """A dead current target must be replaced by the nearest living enemy."""
    hero = H(kind, "red", 500, 340)
    hero.hp = 500
    enemies = targets(coords)
    hero.target = enemies[dead]
    enemies[dead].alive = False
    ok = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    repeat = getattr(hero.skills, "cast_" + key)(enemies, [], [])
    result["casts"].append(dict(hero=kind, key=key, positions=coords, target=dead,
        dead=True, ok=ok, repeat=repeat, state=state(hero, enemies)))


def source_fixture(ids=IDS):
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result = dict(casts=[], traces=[], recasts=[], heals=[], attacks=[],
                  respawn=[], catalog={}, levels={})
    for kind in ids:
        h = H(kind, "red", 500, 340)
        recipe = h.skills._SKILL_REGISTRY[kind]
        assert len(recipe) == 4 and all(hasattr(h.skills, m) for m in recipe.values())
        result["catalog"][kind] = dict(
            recipe=recipe,
            damage=env["get_all_hero_types"]()[kind]["damage"],
            cost=env["get_all_hero_types"]()[kind]["cost"],
            visual={key: h.skills._get_visual_duration(key) for key in "qwer"},
            cooldowns=_cooldowns(h),
            radius=RADII[kind],
            school=h.dmg_school, melee=bool(h.is_melee_hero),
            skill_range=h.skill_range)
        for key in "qwer":
            # Gate: no enemy, auto-target, retained far target, exact radius edges.
            for coords, selected in [
                ([], -1),
                (_radius_coords(RADII[kind][key]), -1),
                (_radius_coords(RADII[kind][key]), 0),
                ([(500 + max(int(h.skill_range), 140) - 40, 340), (520, 340)], 0),
                ([(450, 340), (550, 340)], -1),
                ([(450, 340), (550, 340)], 1),
                ([(900, 340), (550, 340)], 0),
                ([(500, 340)], 0),
            ]:
                _cast_case(result, H, kind, key, coords, selected)
            _dead_target_case(result, H, kind, key, [(540, 340), (600, 340)], 0)
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
                for tick in range(1, 602):
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
                result["traces"].append(dict(hero=kind, key=key, mode=mode,
                    positions=coords, length=601, rows=rows))
            # Exact recast boundary: cooldown-1 refuses, cooldown fires again.
            hero = H(kind, "red", 500, 340)
            hero.hp = 500
            enemies = targets([(550, 340)])
            cooldown = _cooldowns(hero)[key]
            assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
            rows = []
            for tick in range(1, cooldown + 3):
                env["tick_clocks"](hero)
                if tick >= cooldown - 1:
                    ok = getattr(hero.skills, "cast_" + key)(enemies, [], [])
                    rows.append(dict(tick=tick, ok=ok, state=state(hero, enemies)))
            result["recasts"].append(dict(hero=kind, key=key, cooldown=cooldown,
                length=cooldown + 2, rows=rows))
        # Self heal through the source hp property: cap first, then anti-heal.
        for key in sorted(HEALS[kind]):
            for hp_mode in HP_MODES:
                for anti in ANTI_HEAL:
                    hero = H(kind, "red", 500, 340)
                    enemies = targets([(550, 340)])
                    if hp_mode == "partial":
                        hero.hp = 500
                    elif hp_mode == "full":
                        hero.hp = hero.max_hp
                    else:
                        hero.hp = 1
                    if anti:
                        hero.apply_debuff("anti_heal", anti, 600)
                    before = hero.hp
                    assert getattr(hero.skills, "cast_" + key)(enemies, [], [])
                    result["heals"].append(dict(hero=kind, key=key, hp_mode=hp_mode,
                        anti_heal=anti, source=HEALS[kind][key], before=before,
                        hp=hero.hp, max_hp=hero.max_hp, enemy_hp=enemies[0].hp,
                        anti_heal_amount=hero.anti_heal_amount,
                        anti_heal_timer=hero.anti_heal_timer))
        # Both heroes are ranged: the real source homing projectile loop runs.
        for point in ([560, 340], [620, 340]):
            hero = H(kind, "red", 500, 340)
            enemy = targets([tuple(point)])[0]
            hero.target = enemy
            hero._do_attack()
            rows = []
            for tick in range(24):
                if tick:
                    env["tick_projectiles"](hero)
                    env["tick_clocks"](hero)
                rows.append(dict(tick=tick, hp=enemy.hp, attack_timer=hero.attack_timer,
                    positions=[[p['x'], p['y']] for p in hero.projectiles]))
            result["attacks"].append(dict(hero=kind, target_position=point, rows=rows))
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
            result["levels"][kind].append(dict(level=level, hp=h.hp, damage=h.damage,
                max_hp=h.max_hp, skill_value=h.skill_damage, price=h.upgrade_cost()))
            assert h.upgrade() == (level < 15)
    return json.loads(json.dumps(result))


if __name__ == "__main__":
    data = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(data, separators=(",", ":")) + "\n")
        print(f"WROTE {FIXTURE} {len(json.dumps(data))} bytes PASS: Krobellus + Vhalzun "
              "real recipes, radius edges, recast ticks, heals, attacks, respawn")
    else:
        assert data == json.loads(FIXTURE.read_text()), "Level-five boss source drift"
        print("PASS: Krobellus + Vhalzun real recipes, radius edges, recast ticks, "
              "heals, attacks, respawn")
