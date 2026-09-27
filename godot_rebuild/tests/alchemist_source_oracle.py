"""Actual Alchemist recipe and shared source BossHeroSkills lifecycle."""
import json
import sys
from pathlib import Path
from starter_finish_source_oracle import source_env
from boss_level_one_source_oracle import source_fixture as boss_fixture, _cast_case, targets

FIXTURE = Path(__file__).parent / "fixtures/alchemist_source.json"


def source_fixture():
    result = boss_fixture(("alchemist",))
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    _cast_case(result, H, "alchemist", "w", [(620, 340), (720, 340), (721, 340), (519, 340)], 0)
    result["kills"] = []
    for reduction in (0, 0.75, 1):
        h = H("alchemist", "red", 500, 340)
        h.hp = 500
        h.anti_heal_amount, h.anti_heal_timer = reduction, 900
        enemies = targets([(550, 340), (650, 340), (700, 340), (701, 340)])
        for index in (0, 2, 3):
            enemies[index].hp = 1
        assert h.skills.cast_r(enemies, [], [])
        result["kills"].append(dict(reduction=reduction, hp=h.hp,
            enemies=[dict(hp=max(0, e.hp), alive=e.alive) for e in enemies]))
    return json.loads(json.dumps(result))


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Alchemist source drift"
    print("PASS: source Alchemist QWER, target-centered burst, rage expiry/upgrade, kill heal")
