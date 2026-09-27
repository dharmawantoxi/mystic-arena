"""Execute actual Kunkka, Gravewake, Syrentha and Thalgryn recipes (level 6).

Capture engine: boss_level_source_oracle. Fixtures are compared, never
replicated: every number comes from the real BossHeroSkills methods.
"""
import json
from pathlib import Path

from boss_level_source_oracle import source_fixture as level_fixture

FIXTURE = Path(__file__).parent / "fixtures/boss_level_six_source.json"
IDS = ("kunkka", "gravewake", "syrentha", "thalgryn")


def source_fixture():
    return level_fixture(IDS)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = source_fixture()
    if args.write:
        FIXTURE.write_text(json.dumps(data, separators=(",", ":")) + "\n")
        print(
            f"WROTE {FIXTURE} {len(json.dumps(data))} bytes "
            "PASS: level 6 real recipes, gates, timers, attacks, respawn"
        )
    else:
        expected = json.loads(FIXTURE.read_text())
        assert data == expected, "fixture drift"
        print("PASS: level 6 real recipes, gates, timers, attacks, respawn")


if __name__ == "__main__":
    main()
