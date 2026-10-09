"""Read-only AST oracle for Python language persistence and translation data."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "godot_rebuild"
CATALOG = PROJECT / "data/localization_catalog.json"
CONTRACT = PROJECT / "tests/fixtures/localization_source_contract.json"


def _literal(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        return {_literal(key): _literal(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.Tuple):
        return tuple(_literal(value) for value in node.elts)
    if isinstance(node, ast.List):
        return [_literal(value) for value in node.elts]
    if isinstance(node, ast.Set):
        return {_literal(value) for value in node.elts}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left) + _literal(node.right)
    raise AssertionError(f"Unsupported localization data expression at line {node.lineno}")


def _assignment(tree, name):
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return node.value
    raise AssertionError(f"Missing localization assignment {name}")


def _class(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def _method(class_node, name):
    return next(
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _self_assignment(function, name):
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing GameSettings.{name} default")



def _source_data():
    localization_path = ROOT / "localization.py"
    core_path = ROOT / "_core.py"
    localization = ast.parse(
        localization_path.read_text(encoding="utf-8"), filename=str(localization_path)
    )
    core = ast.parse(core_path.read_text(encoding="utf-8"), filename=str(core_path))
    settings = _class(core, "GameSettings")
    defaults = _method(settings, "_init_defaults")
    language_setter = _method(settings, "set_language")
    language_loader = _method(settings, "_load")
    language_ids = list(_literal(_assignment(localization, "LANGUAGES")))
    labels = _literal(_assignment(localization, "LANGUAGE_LABELS"))
    texts = _literal(_assignment(localization, "_TEXT"))
    setter_ast = ast.unparse(language_setter)
    loader_ast = ast.unparse(language_loader)
    locale_set = next(
        node for node in localization.body
        if isinstance(node, ast.FunctionDef) and node.name == "set_language"
    )
    locale_set_ast = ast.unparse(locale_set)
    translator = next(
        node for node in localization.body
        if isinstance(node, ast.FunctionDef) and node.name == "tr"
    )
    translator_ast = ast.unparse(translator)
    return {
        "source": "localization.py:_TEXT + _core.py:GameSettings",
        "default_language": _self_assignment(defaults, "language"),
        "languages": language_ids,
        "language_labels": labels,
        "texts": texts,
        "contract": {
            "settings_setter_saves_valid_choice": (
                "if language in ('id', 'en')" in setter_ast and "self.save()" in setter_ast
            ),
            "settings_load_validates_and_applies": (
                "if self.language not in ('id', 'en')" in loader_ast
                and "set_language(self.language)" in loader_ast
            ),
            "global_invalid_language_falls_back_to_id": (
                "LANGUAGES else 'id'" in locale_set_ast
            ),
            "unknown_translation_falls_back_to_key": (
                "_TEXT['id'].get(key, key)" in translator_ast
            ),
            "formats_named_placeholders": (
                "template.format(**values)" in translator_ast
            ),
        },
    }


def source_fixture():
    return _source_data()


def verify():
    actual = source_fixture()
    expected_catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected_contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if actual != expected_catalog:
        raise AssertionError("Localization catalog drift; re-audit Python translation tables")
    contract = {key: value for key, value in actual.items() if key != "texts"}
    if contract != expected_contract:
        raise AssertionError("Language persistence/fallback contract drift")
    if actual["default_language"] != "id" or actual["languages"] != ["id", "en"]:
        raise AssertionError("Python language default or cycle order changed")
    if set(actual["texts"]) != set(actual["languages"]):
        raise AssertionError("Python localization catalogs no longer cover each language")
    if not all(actual["contract"].values()):
        raise AssertionError("Python language save/fallback behavior changed")
    return len(actual["texts"]["id"]) + len(actual["texts"]["en"]) + 5


if __name__ == "__main__":
    print(f"PASS: {verify()} read-only localization source checks")
