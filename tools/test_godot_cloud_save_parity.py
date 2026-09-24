#!/usr/bin/env python3
"""Cross-engine fixture for the Godot Google Play Games cloud-save port.

    python3 tools/test_godot_cloud_save_parity.py                  # verify
    python3 tools/test_godot_cloud_save_parity.py --write-fixture  # refresh

Payload/checksum rules come from mobile/cloud_save.py (the Pygame oracle).
The generated raw JSON strings preserve integer/float spellings so
CloudSaveParityTest.tscn can run the real GDScript parser and SHA-256 code.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mobile.cloud_save as cloud_save  # noqa: E402

FIXTURE = ROOT / "godot/tests/fixtures/cloud_save_parity.json"


def build_fixture() -> dict:
    raw_payloads = [
        {
            "magic": cloud_save.PAYLOAD_MAGIC,
            "version": cloud_save.PAYLOAD_VERSION,
            "exported_at": 1700000000.125,
            "slots": {
                "1": {
                    "completed_levels": [1, 2, 3.0, 4],
                    "integer_value": 7,
                    "float_value": 7.0,
                    "scientific_small": 1e-7,
                    "scientific_large": 1e20,
                    "cutoff_float": 9.999999999999998e-5,
                    "high_precision_float": 1.2345678901234567,
                    "negative_zero": -0.0,
                    "meta_gold": 24500,
                    "profile": 'Naga "Áruna"\\東\nline',
                    "control_text": "tab\t vertical\v",
                    "flags": [True, False, None],
                },
                "3": {
                    "completed_levels": [],
                    "meta_gold": 0,
                    "slot_last_played": 1699999999.5,
                },
            },
            "settings": {
                "master_volume": 0.7,
                "sfx_volume": 0.6,
                "bgm_volume": 0.35,
                "difficulty": "hard",
                "screen_shake_enabled": False,
                "damage_numbers_enabled": True,
                "game_speed": 1.5,
                "fps_limit": 120.0,
                "language": "id",
            },
        },
        {
            "magic": cloud_save.PAYLOAD_MAGIC,
            "version": cloud_save.PAYLOAD_VERSION,
            "exported_at": 0,
            "slots": {"2": {"completed_levels": [1], "meta_gold": 1}},
            "settings": {},
        },
    ]
    cases = []
    for payload in raw_payloads:
        expected_checksum = cloud_save.compute_checksum(payload)
        body = {key: value for key, value in payload.items()
                if key != "checksum"}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False)
        payload_with_checksum = dict(payload)
        payload_with_checksum["checksum"] = expected_checksum
        raw_json = json.dumps(payload_with_checksum, ensure_ascii=False,
                              separators=(",", ":"))
        cases.append({
            "payload_json": raw_json,
            "expected_checksum": expected_checksum,
            "expected_canonical": canonical,
        })
    return {
        "generated_from": "mobile/cloud_save.py",
        "case_count": len(cases),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixture", action="store_true",
                        help="regenerate the Godot cloud-save parity fixture")
    args = parser.parse_args()
    fixture = build_fixture()
    output = json.dumps(fixture, indent=2, ensure_ascii=False,
                        sort_keys=True) + "\n"
    if args.write_fixture:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(output, encoding="utf-8")
        print("[oracle] wrote %s (%d cases)" %
              (FIXTURE.relative_to(ROOT), fixture["case_count"]))
        return 0
    if not FIXTURE.is_file():
        raise AssertionError(
            "Fixture missing: %s; run python3 tools/%s --write-fixture" %
            (FIXTURE.relative_to(ROOT), Path(__file__).name))
    current = FIXTURE.read_text(encoding="utf-8")
    if current != output:
        raise AssertionError(
            "Cloud-save fixture is stale; run python3 tools/%s --write-fixture"
            % Path(__file__).name)
    source = (ROOT / "godot/scripts/autoload/CloudSaveManager.gd").read_text(
        encoding="utf-8")
    for symbol in ("compute_checksum", "canonical_json", "parse_payload",
                   "upload_payload", "download_payload", "apply_payload",
                   "use_bridge_for_testing"):
        if "func " + symbol + "(" not in source:
            raise AssertionError("CloudSaveManager.gd missing %s()" % symbol)
    print("[oracle] cloud save payload/checksum fixture fresh: %d cases" %
          fixture["case_count"])
    print("Cloud-save parity fixture: OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print("FAIL: %s" % exc)
        raise SystemExit(1)
