"""Static guard for bare helper calls in GDScript (layer 9cq).

`gdparse` only checks syntax: a call to a helper that is not defined in the file (or in
the script it `extends`) parses fine and only fails when Godot compiles the scene that
preloads it. That is exactly how `scripts/ui/tower_popup_layout.gd` shipped with six
missing helpers and broke `scenes/prototype/prototype_view.gd`.

Two rules, both deliberately narrow so the report stays at zero false positives:

  * ``private`` - a bare call to a name that starts with ``_`` (and is not a Godot virtual)
    must be defined in the file or anywhere in its ``extends`` chain. Godot built-ins are
    never prefixed with ``_`` in call position.
  * ``sibling`` - a bare call to a name that another ``.gd`` file in the same directory
    defines (for example the three copies of ``letter``) must be defined in this file or
    its chain; the file may not reach across siblings implicitly.

Run: python godot_rebuild/tests/gdscript_call_guard.py [--json]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("scripts", "scenes")
VIRTUALS = {
    "_init", "_ready", "_process", "_physics_process", "_draw", "_input", "_gui_input",
    "_unhandled_input", "_unhandled_key_input", "_notification", "_enter_tree", "_exit_tree",
    "_to_string", "_get", "_set", "_get_property_list", "_property_can_revert",
    "_property_get_revert", "_validate_property", "_structured_text_parser", "_shortcut_input",
}
IDENTIFIER_CALL = re.compile(r"(?<![\w.$@])([A-Za-z_][A-Za-z_0-9]*)\s*\(")
DEFINED = re.compile(
    r"^\s*(?:static\s+)?func\s+([A-Za-z_0-9]+)\s*\(|"
    r"^\s*(?:static\s+)?var\s+([A-Za-z_0-9]+)|"
    r"^\s*const\s+([A-Za-z_0-9]+)|"
    r"^\s*signal\s+([A-Za-z_0-9]+)|"
    r"^\s*enum\s+([A-Za-z_0-9]+)",
    re.M,
)


def strip_code(text):
    """Drop comments and string literals so prose never looks like a call."""
    text = re.sub(r'"""[\s\S]*?"""', '""', text)
    text = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', text)
    text = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", text)
    return re.sub(r"#[^\n]*", "", text)


def defined_names(text):
    names = set()
    for groups in DEFINED.findall(text):
        names.update(name for name in groups if name)
    names.update(re.findall(r"for\s+([A-Za-z_0-9]+)\s+in\s", text))
    return names


def bare_calls(text):
    return set(IDENTIFIER_CALL.findall(text))


def parent_path(path, text):
    """The `extends` target as a file path, following `const X = preload(...)` aliases."""
    match = re.search(r"^extends\s+(.+)$", text, re.M)
    if not match:
        return None
    target = match.group(1).strip()
    quoted = re.fullmatch(r'"(res://[^"]+)"', target)
    if quoted:
        return _resolve(quoted.group(1))
    alias = re.search(r'^const\s+%s\s*:?=\s*preload\("(res://[^"]+)"\)' % re.escape(target), text, re.M)
    if alias:
        return _resolve(alias.group(1))
    return None


def _resolve(url):
    return ROOT / url[len("res://"):] if url.startswith("res://") else None


def chain_names(path, seen=None):
    """Every name defined by `path` or by any script in its `extends` chain."""
    seen = seen or set()
    if path is None or not path.is_file() or path in seen:
        return set()
    seen.add(path)
    raw = path.read_text(encoding="utf-8")
    names = defined_names(strip_code(raw))
    names |= chain_names(parent_path(path, raw), seen)
    return names


def scan():
    problems = []
    files = [path for scope in SCOPES
             for path in sorted((ROOT / scope).rglob("*.gd"))]
    sibling_defs = {}
    for path in files:
        text = strip_code(path.read_text(encoding="utf-8"))
        for name in re.findall(r"^static\s+func\s+([A-Za-z_0-9]+)\s*\(", text, re.M):
            sibling_defs.setdefault((path.parent, name), set()).add(path)

    for path in files:
        text = strip_code(path.read_text(encoding="utf-8"))
        local = chain_names(path)
        for name in sorted(bare_calls(text)):
            if name in local:
                continue
            if name.startswith("_") and name not in VIRTUALS:
                problems.append({"file": _rel(path), "call": name, "rule": "private"})
            elif (path.parent, name) in sibling_defs:
                problems.append({"file": _rel(path), "call": name, "rule": "sibling"})
    return problems


def _rel(path):
    return "godot_rebuild/" + str(path.relative_to(ROOT))


def main():
    problems = scan()
    if "--json" in sys.argv[1:]:
        print(json.dumps(problems, indent=1))
    else:
        for row in problems:
            print("%s: bare call `%s(` is not defined here (%s rule)"
                  % (row["file"], row["call"], row["rule"]))
    print("%s: %d unresolved helper calls" % ("FAIL" if problems else "PASS", len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
