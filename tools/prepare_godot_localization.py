#!/usr/bin/env python3
"""Export localization.py to the active Godot project with a pure-string oracle.

No pygame or Godot is required: localization.py is data + str.format. --check is
an exact-byte, fail-closed gate and never regenerates files in check mode.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "localization.py"
CONTRACT = PROJECT / "data/localization.json"
FIXTURE = PROJECT / "tests/fixtures/localization_parity.json"
SAMPLE_VALUES = {
    "count": 3,
    "page": 2,
    "hero": "Aldric",
    "item": "Moon Shard",
    "items": "Moon Shard, Aegis",
}
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _text(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False,
                      sort_keys=True) + "\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@contextlib.contextmanager
def source_module():
    previous_language = None
    spec = importlib.util.spec_from_file_location("mystic_localization_export", SOURCE)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    previous_language = module.get_language()
    module.set_language("id")
    try:
        yield module
    finally:
        module.set_language(previous_language)
        sys.modules.pop(spec.name, None)


def _placeholders(template: str) -> list[str]:
    if "{{" in template or "}}" in template:
        raise AssertionError(f"Escaped braces are outside the native format subset: {template!r}")
    names = []
    for match in _PLACEHOLDER.finditer(template):
        names.append(match.group(1))
    # Reject any brace that is not a plain named placeholder.
    stripped = _PLACEHOLDER.sub("", template)
    if "{" in stripped or "}" in stripped:
        raise AssertionError(f"Unsupported format template: {template!r}")
    return names


def build_contract(module) -> dict:
    languages = list(module.LANGUAGES)
    if languages != ["id", "en"]:
        raise AssertionError(f"Unexpected localization languages: {languages}")
    labels = dict(module.LANGUAGE_LABELS)
    if set(labels) != set(languages):
        raise AssertionError("LANGUAGE_LABELS must cover exactly LANGUAGES")
    texts = {lang: dict(table) for lang, table in module._TEXT.items()}
    if set(texts) != set(languages):
        raise AssertionError("_TEXT must cover exactly LANGUAGES")
    key_order = list(texts["id"])
    if list(texts["en"]) != key_order:
        raise AssertionError("id/en localization key order drifted")
    placeholders = {}
    for key in key_order:
        names = _placeholders(texts["id"][key])
        for lang in languages:
            value = texts[lang][key]
            if not isinstance(value, str):
                raise AssertionError(f"Non-string localization value: {lang}/{key}")
            if _placeholders(value) != names:
                raise AssertionError(f"Placeholder drift for {key} in {lang}")
        placeholders[key] = names
    core_path = PROJECT / "data/core_data.json"
    if core_path.is_file():
        core = json.loads(core_path.read_text(encoding="utf-8"))
        if core.get("localization") != texts:
            raise AssertionError("Stale core localization table; run prepare_godot_core.py")
    return {
        "schema": 1,
        "source": "localization.py",
        "source_sha256": _sha(SOURCE.read_bytes()),
        "default_language": "id",
        "languages": languages,
        "language_labels": labels,
        "key_order": key_order,
        "key_count": len(key_order),
        "placeholder_subset": "plain-named-braces",
        "placeholders": placeholders,
        "texts": texts,
    }


def build_oracle(module) -> dict:
    contract = build_contract(module)
    tr_cases = []
    missing_cases = []
    for lang in contract["languages"]:
        module.set_language(lang)
        for key in contract["key_order"]:
            names = contract["placeholders"][key]
            args = {name: SAMPLE_VALUES[name] for name in names}
            expected = module.tr(key, **args)
            tr_cases.append({"key": key, "language": lang, "args": args,
                             "expected": expected})
            if names:
                missing_cases.append({"key": key, "language": lang,
                                      "expected": contract["texts"][lang][key]})
    language_cases = []
    for candidate in ("id", "en", "fr", "", "EN"):
        returned = module.set_language(candidate)
        language_cases.append({
            "input": candidate,
            "returned": returned,
            "active": module.get_language(),
            "label": module.get_language_label(),
        })
    module.set_language("en")
    label_cases = [
        {"input": "", "expected": module.get_language_label()},
        {"input": "en", "expected": module.get_language_label("en")},
        {"input": "id", "expected": module.get_language_label("id")},
        {"input": "fr", "expected": module.get_language_label("fr")},
    ]
    edge_specs = [
        ("no_such_localization_key", "id", {}),
        ("queued", "en", {}),
        ("queued", "en", {"count": 7, "extra": "ignored"}),
        ("forge_purchase", "en", {"hero": "Aldric"}),
    ]
    edge_cases = []
    for key, lang, args in edge_specs:
        module.set_language(lang)
        edge_cases.append({"key": key, "language": lang, "args": args,
                           "expected": module.tr(key, **args)})
    return {
        "source_sha256": contract["source_sha256"],
        "tr_cases": tr_cases,
        "missing_args_cases": missing_cases,
        "language_cases": language_cases,
        "label_cases": label_cases,
        "edge_cases": edge_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify tracked files without writing")
    args = parser.parse_args()
    try:
        with source_module() as module:
            contract = build_contract(module)
            oracle = build_oracle(module)
        contract_text = _text(contract)
        oracle_text = _text(oracle)
        if args.check:
            if not CONTRACT.is_file() or not FIXTURE.is_file():
                raise AssertionError("Missing localization contract/fixture; run prepare first")
            if CONTRACT.read_text(encoding="utf-8") != contract_text:
                raise AssertionError("Stale localization contract")
            if FIXTURE.read_text(encoding="utf-8") != oracle_text:
                raise AssertionError("Stale localization oracle fixture")
        else:
            CONTRACT.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE.parent.mkdir(parents=True, exist_ok=True)
            CONTRACT.write_text(contract_text, encoding="utf-8")
            FIXTURE.write_text(oracle_text, encoding="utf-8")
    except (AssertionError, ValueError, TypeError, KeyError, OSError) as exc:
        print(f"localization preparation failed: {exc}", file=sys.stderr)
        return 1
    print(f"{'Verified' if args.check else 'Prepared'} localization: "
          f"{contract['key_count']} keys x {len(contract['languages'])} languages; "
          f"sha256={contract['source_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
