#!/usr/bin/env python3
"""Read-only oracle for the real ``_system.py::SaveManager`` slot lifecycle.

The class is compiled from its AST with isolated temporary paths and a fixed
clock. No Pygame module, game bootstrap, real save directory, or cloud service
is imported. The fixture locks three-slot selection, save metadata, slot cards,
delete semantics, legacy migration, and source time formatting.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_system.py"
FIXTURE = Path(__file__).with_name("fixtures") / "save_slot_source.json"


class Clock:
    def __init__(self, now=1_700_000_000.0):
        self.now = float(now)

    def time(self):
        return self.now

    @staticmethod
    def localtime(value):
        import time
        return time.gmtime(value)

    @staticmethod
    def strftime(pattern, value):
        import time
        return time.strftime(pattern, value)


class CloudProbe:
    def __init__(self):
        self.uploads = 0

    def auto_upload(self):
        self.uploads += 1


def _source_manager(save_dir, clock, cloud):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(
        item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "SaveManager"
    )
    env = {
        "os": os,
        "json": json,
        "time": clock,
        "SAVE_DIR": str(save_dir),
        "LEGACY_SAVE_FILE": str(Path(save_dir) / "progress.json"),
        "NUM_SLOTS": 3,
        "print": lambda *args, **kwargs: None,
    }
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, "<source SaveManager>", "exec"), env)
    return env["SaveManager"]


@contextmanager
def _isolated_cloud_module(cloud):
    missing = object()
    previous_mobile = sys.modules.get("mobile", missing)
    previous_cloud = sys.modules.get("mobile.cloud_save", missing)
    mobile = types.ModuleType("mobile")
    cloud_module = types.ModuleType("mobile.cloud_save")
    cloud_module.manager = cloud
    mobile.cloud_save = cloud_module
    sys.modules["mobile"] = mobile
    sys.modules["mobile.cloud_save"] = cloud_module
    try:
        yield
    finally:
        if previous_mobile is missing:
            sys.modules.pop("mobile", None)
        else:
            sys.modules["mobile"] = previous_mobile
        if previous_cloud is missing:
            sys.modules.pop("mobile.cloud_save", None)
        else:
            sys.modules["mobile.cloud_save"] = previous_cloud


def _json_value(value):
    return json.loads(json.dumps(value, sort_keys=True))


def source_fixture():
    clock = Clock()
    cloud = CloudProbe()
    with (
        tempfile.TemporaryDirectory(prefix="mystic-save-slot-oracle-") as directory,
        _isolated_cloud_module(cloud),
    ):
        save_dir = Path(directory)
        manager = _source_manager(save_dir, clock, cloud)
        empty = manager.get_empty_save()

        state = {
            "meta_gold": 7250,
            "completed_levels": [1, 2, 4],
            "last_played_level": 4,
            "purchased_heroes": ["kaizen", "thorne"],
            "unlocked_bosses": ["gornak"],
            "slot_playtime_seconds": 3665,
        }
        manager.set_current_slot(2)
        manager.set_current_slot(0)
        manager.set_current_slot(4)
        manager.save(state)
        first_info = manager.get_slot_info(2)
        all_info = manager.get_all_slot_info()

        clock.now += 125.0
        state["meta_gold"] = 8000
        manager.save(state, 2)
        second_info = manager.get_slot_info(2)
        deleted_once = manager.delete_slot(2)
        deleted_twice = manager.delete_slot(2)

        legacy = {
            "meta_gold": 99,
            "completed_levels": [1],
            "last_played_level": 1,
            "purchased_heroes": ["kaizen"],
            "unlocked_bosses": [],
        }
        (save_dir / "progress.json").write_text(json.dumps(legacy), encoding="utf-8")
        migrated_once = manager.migrate_legacy_save()
        migrated_state = manager.load(1)
        migrated_twice = manager.migrate_legacy_save()

        return _json_value(
            {
                "policy": {
                    "slot_count": 3,
                    "initial_slot": 1,
                    "selected_after_invalid": manager.get_current_slot(),
                    "slot_names": [Path(manager.get_slot_file(i)).name for i in range(1, 4)],
                },
                "empty": empty,
                "save": {
                    "first_info": first_info,
                    "all_info": all_info,
                    "second_info": second_info,
                    "cloud_uploads": cloud.uploads,
                },
                "delete": {
                    "first": deleted_once,
                    "second": deleted_twice,
                    "remaining_info": manager.get_slot_info(2),
                },
                "migration": {
                    "first": migrated_once,
                    "second": migrated_twice,
                    "state": migrated_state,
                    "legacy_exists": (save_dir / "progress.json").exists(),
                    "backup_exists": (save_dir / "progress_backup.json.old").exists(),
                },
                "format": {
                    "playtime_59": manager.format_playtime(59),
                    "playtime_3665": manager.format_playtime(3665),
                    "time_0": manager.format_time(0),
                    "time_125": manager.format_time(125),
                    "last_zero": manager.format_last_played(0),
                    "last_125": manager.format_last_played(clock.now - 125),
                },
            }
        )


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("FAIL: SaveManager source fixture drift")
    print("PASS: save-slot source lifecycle — 3 slots, metadata, delete, migration")


if __name__ == "__main__":
    main()
