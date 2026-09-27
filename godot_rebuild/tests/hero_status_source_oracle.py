"""Source interactions required by the new kits: anti-heal, burn and Shadow Realm.

Actual TowerDebuffMixin.hp property and burn tick, not a simplified HP receipt.
"""
import json
import sys
from pathlib import Path
from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import targets

FIXTURE = Path(__file__).parent / "fixtures/hero_status_source.json"


def source_fixture():
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    result = dict(heals=[], burn=[])
    for kind, key in (("zephyr", "w"), ("morgath", "e"), ("morgath", "r"),
                      ("drakar", "q"), ("abaddon", "w"), ("alchemist", "e"),
                      ("nyzrak", "r"),
                      ("ignis_drachorn", "e"), ("ignis_drachorn", "r")):
        for missing in (1, 300):
            for reduction in (0, 0.75, 1):
                h = H(kind, "red", 500, 340)
                h.hp = h.max_hp - missing
                h.anti_heal_amount, h.anti_heal_timer = reduction, 900
                enemies = targets([(550, 340)])
                assert getattr(h.skills, "cast_"+key)(enemies, [], [])
                after = h.hp
                h.skills.update_timers(enemies, [], [])
                result["heals"].append(dict(hero=kind, key=key, missing=missing,
                    reduction=reduction, cast_hp=after, tick_hp=h.hp))
    # Real world order: debuff/burn before kit clocks. Test realm final frame.
    h = H("zephyr", "red", 500, 340)
    h.hp = 300
    h.skills.cast_w([], [], [])
    h.apply_debuff("burn", 60, 210, source_team="blue")
    for tick in range(1, 211):
        h._tick_tower_debuffs()
        env["tick_clocks"](h)
        h.skills.update_timers([], [], [])
        if tick in (29, 30, 179, 180, 181, 209, 210):
            result["burn"].append(dict(tick=tick, hp=h.hp, burn_timer=h.burn_timer,
                burn_accum=h.burn_accum, realm=h._shadow_realm_timer))
    return result


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, indent=2)+"\n")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Hero status source drift"
    print("PASS: real anti-heal HP setter and Shadow Realm burn/expiry order")
