"""Per-ID real Hero-v-Hero school/attribution, not an unmitigated hit receipt."""
import json
import sys
from pathlib import Path
from starter_finish_source_oracle import source_env
from source_shared_boss_oracle import eligible_ids

FIXTURE = Path(__file__).parent / "fixtures/hero_school_source.json"


def source_fixture():
    env = source_env()
    H = env["SourceHero"]
    rows = []
    for kind in eligible_ids(env):
        for key in "qwer":
            h = H(kind, "red", 500, 340)
            target = H("thorne", "blue", 550, 340)
            assert target.skills.cast_w([], [], [])
            assert getattr(h.skills, "cast_"+key)([target], [], [])
            rows.append(dict(hero=kind, key=key, hp=h.hp, target_hp=target.hp,
                target_alive=target.alive))
    return rows


if __name__ == "__main__":
    result = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    else:
        assert result == json.loads(FIXTURE.read_text()), "Real hero school/reflect source drift"
    print("PASS: 600 per-ID Hero-v-Hero mitigation/reflect/source attribution checks")
