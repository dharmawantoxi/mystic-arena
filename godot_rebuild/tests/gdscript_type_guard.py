"""Static guard for the typed-GDScript rules Godot 4.7 enforces (layer 9cr).

Godot 4.7 promotes `INFERENCE_ON_VARIANT` and "cannot infer the type" to **errors**, so
`var x := <Variant expression>` stops the whole project from loading while `gdparse` and
`gdlint` stay silent. That is exactly how the 4.7 upgrade surfaced:

    var metrics := measure.call(...)        # Callable.call -> Variant
    var lower := floor(value)               # @GlobalScope.floor -> Variant
    var dc := key2.split("|")[0]            # Variant receiver -> Variant
    var definition := parked[key]           # Dictionary index -> Variant
    for class_name in suites:               # reserved word as a loop variable

The guard only reports what it can prove from the file itself (types are resolved per
function, so one function's `var state: Variant` cannot poison another's `state: Dictionary`):

  * `var NAME := EXPR` where EXPR is `X.call(...)`, `X.get(...)`, a Variant-typed global
    math call (`floor`/`round`/`ceil`/`abs`/`sign`/`min`/`max`/`clamp`), an index into an
    untyped container, a method call on a Variant receiver, or a call to a local function
    that declares no return type;
  * a loop variable that is a GDScript keyword (`for class_name in ...`);
  * a local that shadows a local of an enclosing block in the same function.

Run: python godot_rebuild/tests/gdscript_type_guard.py [--json|--self-test]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("scripts", "scenes", "tests", "app")
KEYWORDS = {
    "if", "else", "elif", "for", "while", "match", "when", "return", "break", "continue",
    "pass", "and", "or", "not", "in", "is", "as", "true", "false", "null", "self", "super",
    "await", "yield", "func", "var", "const", "enum", "class", "class_name", "extends",
    "signal", "static", "void", "namespace", "trait", "uses", "breakpoint",
}
# @GlobalScope helpers declared `(Variant) -> Variant`: `:=` from them is an error.
VARIANT_GLOBALS = {
    "floor", "ceil", "round", "abs", "sign", "min", "max", "clamp", "wrap", "nearest_po2",
}
TYPED_CASTS = {
    "int", "float", "String", "bool", "str", "StringName", "NodePath", "Color", "Color8",
    "Vector2", "Vector2i", "Vector3", "Rect2", "Rect2i", "Transform2D", "Basis", "Array",
    "Dictionary", "PackedStringArray", "PackedInt32Array", "PackedFloat32Array",
    "PackedVector2Array", "PackedColorArray", "PackedByteArray", "maxi", "mini", "maxf",
    "minf", "clampi", "clampf", "absf", "absi", "signf", "signi", "roundi", "roundf",
    "floori", "floorf", "ceili", "ceilf", "lerpf", "snappedf", "sqrt", "sin", "cos", "tan",
    "atan2", "pow", "fmod", "fposmod", "deg_to_rad", "rad_to_deg", "ease", "move_toward",
    "lerp",
}
# `Array` methods whose result is a Variant, so `:=` from them is an error.
VARIANT_METHODS = {"pop_back", "pop_front", "pick_random", "back", "front", "keys", "values"}
LOOP_TYPES = {"range": "int", "search_all": "RegExMatch", "split": "String",
              "rsplit": "String", "keys": "Variant", "values": "Variant"}

NATIVE_FIXTURE = ROOT / "tests/fixtures/godot_native_classes.json"
MEMBER_DECL = re.compile(r"^(?:const|var|static var|signal|enum|class_name)\s+([A-Za-z_0-9]+)")

VAR_DECL = re.compile(r"^(\s*)var\s+([A-Za-z_0-9]+)\s*(?::\s*([A-Za-z0-9_\[\], ]+?))?\s*(:?=)\s*(.*)$")
FOR_DECL = re.compile(r"^\s*for\s+([^\n]+?)\s+in\s+(.+)$")


def strip_code(text):
    text = re.sub(r'"""[\s\S]*?"""', '""', text)
    text = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', text)
    text = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", text)
    return re.sub(r"#[^\n]*", "", text)


def signature(code, start):
    """The `func` signature of the block that begins at line `start`, params included."""
    text = "\n".join(code.splitlines()[start:start + 12])
    open_paren = text.find("(")
    depth = 0
    for index in range(open_paren, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                tail = text[index + 1:text.find("\n", index + 1) if text.find("\n", index + 1) > 0 else len(text)]
                returns = re.search(r"->\s*([A-Za-z0-9_\[\]]+)", tail)
                return text[open_paren + 1:index], (returns.group(1) if returns else None)
    return "", None


def blocks(code):
    """`(start, end)` line ranges of every function, header included."""
    lines = code.splitlines()
    spans = []
    index = 0
    while index < len(lines):
        if re.match(r"^(static\s+)?func\s", lines[index]):
            end = index + 1
            while end < len(lines) and (not lines[end].strip() or lines[end][0].isspace()):
                end += 1
            spans.append((index, end))
            index = end
        else:
            index += 1
    return spans


def returns_of(code):
    """Local function name -> declared return type (None when unannotated)."""
    found = {}
    lines = code.splitlines()
    for start, _ in blocks(code):
        name = re.match(r"^\s*(?:static\s+)?func\s+([A-Za-z_0-9]+)", lines[start])
        if name:
            found.setdefault(name.group(1), signature(code, start)[1])
    return found


def literals(code):
    """Const/local literals that pin a type without an annotation."""
    types = {}
    for name, value in re.findall(r"^\s*const\s+([A-Za-z_0-9]+)\s*:?=\s*(.+)$", code, re.M):
        value = value.strip()
        if re.fullmatch(r'""|"[\s\S]*"|\'[\s\S]*\'', value):
            types.setdefault(name, "String")
        elif re.fullmatch(r"-?\d+", value):
            types.setdefault(name, "int")
        elif re.fullmatch(r"-?\d+\.\d*", value):
            types.setdefault(name, "float")
        elif value.startswith("[") and value.endswith("]"):
            types.setdefault(name, "Array")
        elif value.startswith("{") and value.endswith("}"):
            types.setdefault(name, "Dictionary")
        elif value in ("true", "false"):
            types.setdefault(name, "bool")
    return types


def members(code):
    """Class-level `var NAME: T` / `const NAME: T` outside every function."""
    found = {}
    for start, end in blocks(code):
        pass
    inside = set()
    for start, end in blocks(code):
        inside.update(range(start, end))
    for number, line in enumerate(code.splitlines()):
        if number in inside:
            continue
        match = re.match(r"^var\s+([A-Za-z_0-9]+)\s*:\s*([A-Za-z0-9_\[\]]+)", line)
        if match:
            found.setdefault(match.group(1), match.group(2))
    return found


def param_types(params):
    found = {}
    depth = 0
    part = ""
    for char in params:
        if char == "," and depth == 0:
            add_param(found, part)
            part = ""
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        part += char
    add_param(found, part)
    return found


def add_param(found, part):
    match = re.match(r"\s*([A-Za-z_0-9]+)\s*:\s*=?\s*([A-Za-z0-9_\[\]]+)", part)
    if match:
        found.setdefault(match.group(1), match.group(2))


def loop_var_type(expr, types, func_returns=None):
    expr = expr.strip()
    element = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9.()\"' ]+?)\s*\.\s*([a-z_0-9]+)\(.*\)", expr)
    if element and element.group(2) in LOOP_TYPES:
        return LOOP_TYPES[element.group(2)]
    call = re.match(r"([a-z_0-9]+)\(", expr)
    if call and call.group(1) in LOOP_TYPES:
        return LOOP_TYPES[call.group(1)]
    if call and func_returns:
        declared = func_returns.get(call.group(1))
        match = re.fullmatch(r"Array\[([A-Za-z0-9_]+)\]", declared or "")
        if match:
            return match.group(1)
    base = re.fullmatch(r"([A-Za-z_0-9.]+)", expr)
    if base:
        kind = types.get(base.group(1).split(".")[0])
        if kind in ("String", "StringName"):
            return "String"
        match = re.fullmatch(r"Array\[([A-Za-z0-9_]+)\]", kind or "")
        if match:
            return match.group(1)
        if kind and kind.startswith("Packed"):
            return "typed"
        if kind == "Array":
            return "Variant"
        if kind == "Dictionary":
            return "Variant"
    return "Variant"


def depth_before(expr, index):
    return expr[:index].count("(") - expr[:index].count(")")


def top_level_call(expr, name):
    for match in re.finditer(r"\.%s\(" % name, expr):
        if depth_before(expr, match.start()) == 0 and expr.rstrip().endswith(")"):
            return expr[:match.start()].strip() != ""
    return False


def declared_kind(container):
    if container is None:
        return None
    if container in ("Array", "Dictionary", "Variant", ""):
        return None
    if re.fullmatch(r"Array\[[A-Za-z0-9_]+\]", container):
        return "typed"
    if container in ("String", "StringName", "NodePath") or container.startswith("Packed"):
        return "typed"
    return None


def native_classes():
    """The native class names Godot 4.7.2 ships, from the pinned fixture."""
    try:
        payload = json.loads(NATIVE_FIXTURE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return set(payload.get("classes", []))


def scan_file(path, native=None):
    raw = path.read_text(encoding="utf-8")
    code = strip_code(raw)
    func_returns = returns_of(code)
    file_consts = literals(code)
    class_members = members(code)
    lines = code.splitlines()
    problems = []
    native = native_classes() if native is None else native
    for number, line in enumerate(lines, 1):
        declared = MEMBER_DECL.match(line)
        if declared and declared.group(1) in native:
            # Godot 4.7: "The member X shadows a native class" is a parse error, so a
            # `const Popup = preload(...)` hides every other error in the file.
            problems.append((number, "native-class-member", declared.group(1)))

    for start, end in blocks(code):
        params, _ = signature(code, start)
        types = dict(file_consts)
        types.update(class_members)
        types.update(param_types(params))
        scopes = []
        pending = None
        for number in range(start, end):
            line = lines[number]
            indent = len(line) - len(line.lstrip("\t"))
            while scopes and scopes[-1][0] > indent:
                scopes.pop()
            if pending is not None and indent == pending:
                # `if:` / `else:` / `for:` / `case` opens a fresh block: a declaration
                # here may legally repeat a name from the sibling block above it.
                if scopes and scopes[-1][0] == indent:
                    scopes[-1] = (indent, {})
                pending = None
            stripped = line.strip()
            if stripped.endswith(":") and not stripped.startswith(("var ", "const ", "signal ")):
                pending = indent + 1

            loop = FOR_DECL.match(line)
            if loop:
                name = loop.group(1).strip()
                if name in KEYWORDS:
                    problems.append((number + 1, "keyword-loop-var", name))
                    continue
                if re.fullmatch(r"[A-Za-z_0-9]+", name):
                    kind = loop_var_type(loop.group(2).strip().rstrip(":"), types, func_returns)
                    types[name] = kind
                    # The loop variable lives in the body block, one level deeper, and
                    # that body is a fresh scope (a later sibling `var` may reuse the name).
                    body = indent + 1
                    if scopes and scopes[-1][0] == body:
                        scopes[-1] = (body, {})
                    push(scopes, body, name, number + 1)
                    pending = body
                continue

            match = VAR_DECL.match(line)
            if not match:
                continue
            name, annotation, operator, expr = match.group(2), match.group(3), match.group(4), match.group(5).strip()
            previous = next((seen[name] for level, seen in reversed(scopes) if name in seen), None)
            if previous is not None:
                problems.append((number + 1, "duplicate-local", "%s (first at %d)" % (name, previous)))
            if annotation:
                types[name] = annotation.strip()
                push(scopes, indent, name, number + 1)
                continue
            if operator != ":=":
                continue
            reason = infer_problem(expr, types, func_returns)
            if reason:
                problems.append((number + 1, reason, expr[:70]))
            types[name] = inferred_decl(expr) or "unknown"
            push(scopes, indent, name, number + 1)
    return problems


def push(scopes, indent, name, line):
    if scopes and scopes[-1][0] == indent:
        scopes[-1][1][name] = line
    else:
        scopes.append((indent, {name: line}))


def inferred_decl(expr):
    """Type of a `:=` initialiser the file makes obvious; None when it stays unknown."""
    expr = expr.strip()
    cast = re.fullmatch(r"([A-Za-z_0-9]+)\(.*\)", expr)
    if cast and cast.group(1) in TYPED_CASTS:
        return cast.group(1) if cast.group(1) != "str" else "String"
    instantiate = re.fullmatch(r"([A-Za-z_0-9]+)\.new\(.*\)", expr)
    if instantiate:
        return instantiate.group(1)
    if re.fullmatch(r'"[\s\S]*"|\'[\s\S]*\'', expr):
        return "String"
    if re.fullmatch(r"-?\d+", expr):
        return "int"
    if re.fullmatch(r"-?\d*\.\d+", expr):
        return "float"
    if expr in ("true", "false"):
        return "bool"
    if expr.startswith("[") and expr.endswith("]"):
        return "Array"
    if expr.startswith("{") and expr.endswith("}"):
        return "Dictionary"
    if re.fullmatch(r"-?[A-Za-z_0-9.]+", expr):
        return None
    return None


def infer_problem(expr, types, func_returns):
    if top_level_call(expr, "call"):
        return "callable-call"
    if top_level_call(expr, "get"):
        return "dictionary-get"
    math_call = re.fullmatch(r"([a-z_0-9]+)\(.*\)", expr)
    if math_call and math_call.group(1) in VARIANT_GLOBALS:
        return "variant-math:" + math_call.group(1)
    cast = re.fullmatch(r"([A-Za-z_0-9]+)\(.*\)", expr)
    if cast and cast.group(1) not in TYPED_CASTS and func_returns.get(cast.group(1), "missing") is None:
        return "untyped-func:" + cast.group(1)
    method = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_0-9]+)\(.*\)", expr)
    if method and types.get(method.group(1)) == "Variant":
        return "variant-receiver:" + method.group(2)
    index = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9.]*)\s*\[[^\]]+\]", expr)
    if index:
        base = index.group(1).split(".")[0]
        kind = types.get(base)
        if kind in ("Array", "Dictionary", "Variant"):
            return "index-from-%s" % kind
    if expr.endswith("]") and ")" in expr:
        head = expr.rpartition("[")[0].strip()
        call = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9.]*)\.([A-Za-z_0-9]+)\(.*\)", head)
        if call:
            receiver = types.get(call.group(1).split(".")[0])
            if receiver == "Variant" or call.group(2) in ("keys", "values"):
                return "index-from-%s.%s" % (receiver, call.group(2))
    return None


def scan():
    problems = []
    native = native_classes()
    for scope in SCOPES:
        for path in sorted((ROOT / scope).rglob("*.gd")):
            for number, reason, detail in scan_file(path, native):
                problems.append({
                    "file": "godot_rebuild/" + str(path.relative_to(ROOT)),
                    "line": number,
                    "rule": reason,
                    "expr": detail,
                })
    return problems


BROKEN = """extends RefCounted
const TYPES := ["archer", "cannon"]
const Popup = preload("res://scripts/ui/popup_animation.gd")

func _bad(loadout: Dictionary, measure: Callable, value: float, key_var: Variant) -> void:
	var metrics := measure.call("X", 12)
	var lower := floor(value)
	var dc := key_var.split("|")[0]
	var definition := loadout["boss_class"]
	var first := TYPES[0]
	var again := _untyped(3)
	for class_name in TYPES:
		var label := String(class_name)
	var box: Array = []
	for row in TYPES:
		var box := String(row)


func _untyped(value: int):
	return value
"""

FIXED = """extends RefCounted
const TYPES := ["archer", "cannon"]
const PopupAnim = preload("res://scripts/ui/popup_animation.gd")

func _good(loadout: Dictionary, measure: Callable, value: float, key_var: Variant) -> void:
	var metrics: Vector2 = measure.call("X", 12)
	var lower: float = floor(value)
	var dc := String(key_var).get_slice("|", 0)
	var definition: Variant = loadout["boss_class"]
	var first := String(TYPES[0])
	var label := String(loadout.get("label", ""))
	var name := String(loadout.keys()[0])
	var tower_type := name.split("_")[0]
	for suite_name in TYPES:
		var entry := String(suite_name)
	for row in TYPES:
		var box := String(row)
	var body := "abc"
	for character in body:
		var code := character.unicode_at(0)
"""


def self_test():
    """Every rule must fire on BROKEN and stay silent on FIXED."""
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        counts = {}
        for label, source in (("broken", BROKEN), ("fixed", FIXED)):
            path = Path(folder) / (label + ".gd")
            path.write_text(source, encoding="utf-8")
            rules = scan_file(path)
            counts[label] = rules
        expected = 9
        if len(counts["broken"]) != expected:
            print("FAIL: broken sample should raise %d findings, got %d: %s"
                  % (expected, len(counts["broken"]), counts["broken"]))
            return 1
        if counts["fixed"]:
            print("FAIL: fixed sample should stay silent, got %s" % counts["fixed"])
            return 1
    print("PASS: %d findings fire on the broken sample, 0 on the fixed one" % expected)
    return 0


def main():
    if "--self-test" in sys.argv[1:]:
        return self_test()
    problems = scan()
    if "--json" in sys.argv[1:]:
        print(json.dumps(problems, indent=1))
    else:
        for row in problems:
            print("%s:%d: %s (%s)" % (row["file"], row["line"], row["expr"], row["rule"]))
    print("%s: %d typed-inference problems" % ("FAIL" if problems else "PASS", len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
