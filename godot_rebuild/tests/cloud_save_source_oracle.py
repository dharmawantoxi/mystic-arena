"""Read-only source oracle for the Android cloud-save payload contract.

Only pure checksum/parser/summary functions are executed. This file never
calls build_payload, apply_payload, or the manager, so it never opens Python
save or settings files.
"""
import ast
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mobile/cloud_save.py"
FIXTURE = Path(__file__).parent / "fixtures/cloud_save_source.json"


def _function(tree, name):
    return next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _constant(tree, name):
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    )
    return ast.literal_eval(assignment.value)


def _calls(node, dotted_name):
    return any(
        isinstance(call, ast.Call)
        and _attribute_path(call.func) == dotted_name.split(".")
        for call in ast.walk(node)
    )


def _attribute_path(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.insert(0, node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.insert(0, node.id)
        return parts
    return []


def _source_namespace():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    functions = [_function(tree, name) for name in ("compute_checksum", "parse_payload", "get_payload_summary")]
    code = compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), str(SOURCE), "exec")
    values = {
        "json": json,
        "hashlib": hashlib,
        "time": time,
        "PAYLOAD_MAGIC": _constant(tree, "PAYLOAD_MAGIC"),
        "PAYLOAD_VERSION": _constant(tree, "PAYLOAD_VERSION"),
    }
    exec(code, values)  # noqa: S102 - execute only the original pure source functions
    return tree, values


def build_fixture():
    tree, source = _source_namespace()
    payloads = [
        {
            "magic": source["PAYLOAD_MAGIC"],
            "version": source["PAYLOAD_VERSION"],
            "exported_at": 1700000000.125,
            "slots": {
                "1": {
                    "completed_levels": [1, 2, 3.0, 4],
                    "meta_gold": 24500,
                    "profile": 'Naga "Áruna"\\東\nline',
                    "flags": [True, False, None],
                },
                "3": {"completed_levels": [], "meta_gold": 0, "slot_last_played": 1699999999.5},
            },
            "settings": {"game_speed": 1.5, "fps_limit": 120.0, "language": "id"},
        },
        {
            "magic": source["PAYLOAD_MAGIC"],
            "version": source["PAYLOAD_VERSION"],
            "exported_at": 0,
            "slots": {"2": {"completed_levels": [1], "meta_gold": 1}},
            "settings": {},
        },
        {
            "magic": source["PAYLOAD_MAGIC"],
            "version": source["PAYLOAD_VERSION"],
            "exported_at": -0.0,
            "slots": {
                "1": {
                    "completed_levels": [1],
                    "meta_gold": 0,
                    "float_1e-5": 1e-5,
                    "float_1e-4": 1e-4,
                    "float_1e-7": 1e-7,
                    "float_1e15": 1e15,
                    "float_1e16": 1e16,
                    "float_scientific": 1.23456789e20,
                    "negative_zero": -0.0,
                },
            },
            "settings": {"game_speed": 1.0},
        },
    ]
    cases = []
    for payload in payloads:
        with_checksum = dict(payload)
        with_checksum["checksum"] = source["compute_checksum"](payload)
        raw = json.dumps(with_checksum, ensure_ascii=False, separators=(",", ":"))
        parsed, error = source["parse_payload"](raw)
        summary = source["get_payload_summary"](parsed)
        cases.append({
            "payload_json": raw,
            "expected_checksum": with_checksum["checksum"],
            "expected_error": error,
            "summary": {
                key: summary[key]
                for key in ("highest_level", "meta_gold", "slot_count", "exported_at", "newest_played")
            },
        })

    invalid_inputs = [
        ("invalid_json", "{", "File corrupt (not valid JSON)"),
        ("non_object", "[]", "File corrupt (unexpected structure)"),
    ]
    invalid = []
    for label, raw, expected_error in invalid_inputs:
        _, error = source["parse_payload"](raw)
        invalid.append({"label": label, "payload_json": raw, "expected_error": error})
        assert error == expected_error

    mutated = dict(payloads[0])
    mutated["magic"] = "NOT_MYSTIC_ARENA"
    wrong_magic, wrong_magic_error = source["parse_payload"](json.dumps(mutated))
    mutated = dict(payloads[0])
    mutated["version"] = source["PAYLOAD_VERSION"] + 1
    wrong_version, wrong_version_error = source["parse_payload"](json.dumps(mutated))
    empty = {
        "magic": source["PAYLOAD_MAGIC"], "version": source["PAYLOAD_VERSION"],
        "exported_at": 0, "slots": {}, "settings": {},
    }
    empty["checksum"] = source["compute_checksum"](empty)
    _, empty_error = source["parse_payload"](json.dumps(empty))
    bad_checksum = dict(payloads[0])
    bad_checksum["checksum"] = "0" * 64
    _, checksum_error = source["parse_payload"](json.dumps(bad_checksum))

    save_tree = ast.parse((ROOT / "_system.py").read_text(encoding="utf-8"))
    save_manager = next(
        node for node in save_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SaveManager"
    )
    save_method = next(
        node for node in save_manager.body
        if isinstance(node, ast.FunctionDef) and node.name == "save"
    )
    manager = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "CloudSaveManager"
    )
    apply_payload = _function(tree, "apply_payload")
    build_payload = _function(tree, "build_payload")
    return {
        "payload_magic": source["PAYLOAD_MAGIC"],
        "payload_version": source["PAYLOAD_VERSION"],
        "cloud_magic": _constant(tree, "CLOUD_MAGIC"),
        "cloud_version": _constant(tree, "CLOUD_VERSION"),
        "slot_count": _constant(tree, "NUM_SLOTS"),
        "cases": cases,
        "invalid": invalid,
        "expected_errors": {
            "wrong_magic": wrong_magic_error,
            "wrong_version": wrong_version_error,
            "empty_slots": empty_error,
            "bad_checksum": checksum_error,
        },
        "contract": {
            "build_includes_settings": "settings" in ast.unparse(build_payload),
            "restore_uses_temp_and_replace": ".tmp" in ast.unparse(apply_payload) and _calls(apply_payload, "os.replace"),
            "restore_clears_missing_slots": "os.remove" in ast.unparse(apply_payload),
            "manager_async_poll": all(name in {node.name for node in manager.body if isinstance(node, ast.FunctionDef)}
                                       for name in ("upload_payload", "download_payload", "poll", "auto_upload")),
            "save_auto_upload": "auto_upload" in ast.unparse(save_method),
        },
    }


def main():
    actual = build_fixture()
    if "--write" in __import__("sys").argv:
        FIXTURE.write_text(json.dumps(actual, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("WROTE: cloud-save source payload fixture")
        return
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert actual == expected, "Cloud-save source contract drift"
    print("PASS: Cloud-save source payload/checksum contract")


if __name__ == "__main__":
    main()
