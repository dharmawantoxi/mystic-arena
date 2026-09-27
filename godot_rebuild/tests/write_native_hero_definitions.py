"""Fold ORIGINAL source constructor data into explicit native .tres hero assets.

Read-only against Python: it reuses the audited `hero_combat_stats.json`
baselines (real `Hero.__init__` numbers after melee normalization and the
hero_balance pass) plus `settings.get_all_hero_types()` for the raw catalog
damage and the boss title. It never invents stats and never edits Python.

Usage (from godot_rebuild/tests):
    python write_native_hero_definitions.py vhalzun krobellus
"""
import sys

from source_shared_boss_oracle import write_native_definitions
from starter_finish_source_oracle import source_env


def main() -> None:
    ids = sys.argv[1:]
    if not ids:
        raise SystemExit("usage: python write_native_hero_definitions.py <hero_id>...")
    env = source_env()
    write_native_definitions(env, ids, write_membership=False)
    print(f"WROTE {len(ids)} native hero definitions: {', '.join(ids)}")


if __name__ == "__main__":
    main()
