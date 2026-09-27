"""Per-ID real Hero-v-Hero school/attribution, not an unmitigated hit receipt."""
import json
import sys
from pathlib import Path
from starter_finish_source_oracle import source_env
from source_shared_boss_oracle import eligible_ids

FIXTURE = Path(__file__).parent / "fixtures/hero_school_source.json"


def source_fixture():
    env = source_env()
    sys.modules["settings"].get_all_hero_types = env["get_all_hero_types"]
    H = env["SourceHero"]
    rows = []
    for kind in eligible_ids(env) + ["vex", "zephyr", "gornak", "morgath", "drakar", "abaddon"]:
        for key in "qwer":
            h = H(kind, "red", 500, 340)
            target = H("thorne", "blue", 550, 340)
            assert target.skills.cast_w([], [], [])
            assert getattr(h.skills, "cast_"+key)([target], [], [])
            rows.append(dict(hero=kind, key=key, victim="hero", hp=h.hp, target_hp=target.hp,
                target_alive=target.alive))
            h = H(kind, "red", 500, 340)
            target = env["SourceTower"](550, 340, "blue")
            target.timer = 17
            assert getattr(h.skills, "cast_"+key)([], [target], [])
            rows.append(dict(hero=kind, key=key, victim="tower", hp=h.hp, target_hp=target.hp,
                target_alive=target.alive, shield=target.shield, clock=target.timer))
    return rows


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Real hero school/reflect source drift"
    print("PASS: 1248 per-ID Hero-v-Hero/Tower mitigation/reflect/source attribution checks")
