#!/usr/bin/env python3
"""Active-project localization parity smoke gate.

The legacy godot/ GDScript-table parser was retired when the active port moved
to godot_rebuild/ and a generated JSON contract. Exact byte parity now lives in
tools/prepare_godot_localization.py --check and the native suite
(godot_rebuild/tests/LocalizationParityTest.gd). This script remains a cheap
source-side check that does not need pygame or Godot.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import localization  # noqa: E402
import prepare_godot_localization as prep  # noqa: E402

PROJECT = ROOT / "godot_rebuild"
NATIVE_FILES = [
    PROJECT / "scripts/core/Localization.gd",
    PROJECT / "data/localization.json",
    PROJECT / "tests/LocalizationParityTest.gd",
    PROJECT / "tests/fixtures/localization_parity.json",
]


def main() -> int:
    for path in NATIVE_FILES:
        if not path.is_file():
            print(f"Missing native localization file: {path}", file=sys.stderr)
            return 1
    with prep.source_module() as module:
        contract = prep.build_contract(module)
        oracle = prep.build_oracle(module)
    tracked = json.loads((PROJECT / "data/localization.json").read_text(encoding="utf-8"))
    fixture = json.loads((PROJECT / "tests/fixtures/localization_parity.json").read_text(encoding="utf-8"))
    if tracked != contract or fixture != oracle:
        print("Stale localization contract/fixture; run tools/prepare_godot_localization.py", file=sys.stderr)
        return 1
    assert localization.set_language("en") == "en"
    assert localization.tr("forge_queued", item="Moon Shard", hero="Aldric") == \
        "Moon Shard for Aldric will be delivered after respawn!"
    assert localization.set_language("id") == "id"
    assert localization.tr("forge_queued", item="Moon Shard", hero="Aldric") == \
        "Moon Shard untuk Aldric dikirim setelah respawn!"
    assert localization.set_language("invalid") == "id"
    print(f"Localization parity OK: {contract['key_count']} keys x {len(contract['languages'])} languages")
    print("Exact gate: python3 tools/prepare_godot_localization.py --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
