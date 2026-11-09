#!/usr/bin/env python3
"""Transpile ONLY the game-feel slice of five starter FX directors.

No rig, particle, trail or projectile geometry is claimed here. Python AST
retains branch order and numeric formulas; fixtures execute the same slice.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
OUT = PROJECT / "scripts/entities/generated/HeroFeedback.gd"
FIXTURE = PROJECT / "tests/fixtures/hero_feedback.json"
STARTERS = ("grimjaw", "kaizen", "sylara", "vex", "zephyr")
NAMES = {"shake", "hit_stop"}


def sliced(body):
    result = []
    for node in body:
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id in NAMES):
            result.append(copy.deepcopy(node))
        elif isinstance(node, ast.If):
            yes, no = sliced(node.body), sliced(node.orelse)
            if yes or no:
                result.append(ast.If(test=copy.deepcopy(node.test),
                                     body=yes or [ast.Pass()], orelse=no))
        elif any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id in NAMES for n in ast.walk(node)):
            raise ValueError("Feedback moved into unsupported control flow: " + ast.dump(node))
    return result


def expression(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return str(node.value).lower()
        return json.dumps(node.value)
    if isinstance(node, ast.Name) and node.id in ("power", "crit", "skill", "damage"):
        return node.id
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}[type(node.op)]
        return f"({expression(node.left)} {op} {expression(node.right)})"
    if isinstance(node, ast.IfExp):
        return f"({expression(node.body)} if {expression(node.test)} else {expression(node.orelse)})"
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
        op = "==" if isinstance(node.ops[0], ast.Eq) else "!="
        return f"{expression(node.left)} {op} {expression(node.comparators[0])}"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float":
        return "float(" + expression(node.args[0]) + ")"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("min", "max"):
        return node.func.id + "f(" + ", ".join(expression(a) for a in node.args) + ")"
    raise ValueError(f"Unsupported feedback expression, fail closed: {ast.dump(node)}")


def statements(body, depth):
    result = []
    indent = "\t" * depth
    for node in body:
        if isinstance(node, ast.Expr):
            call = node.value
            result.append(indent + "bus." + call.func.id + "(" + ", ".join(expression(a) for a in call.args) + ")")
        elif isinstance(node, ast.If):
            result.append(indent + "if " + expression(node.test) + ":")
            result.extend(statements(node.body, depth + 1))
            if node.orelse:
                result.append(indent + "else:")
                result.extend(statements(node.orelse, depth + 1))
        elif isinstance(node, ast.Pass):
            result.append(indent + "pass")
        else:
            raise ValueError(ast.dump(node))
    return result


def methods():
    result = {}
    for hero in STARTERS:
        source = ROOT / "heroes" / (hero + "_fx.py")
        tree = ast.parse(source.read_text())
        director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name.endswith("FXDirector"))
        result[hero] = {}
        for method in ("on_cast", "on_impact"):
            original = next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == method)
            body = sliced(original.body)
            if not body:
                raise ValueError(f"Missing feel slice: {hero}.{method}")
            # Validate every retained node against the deliberately tiny emitter.
            statements(body, 0)
            result[hero][method] = body
    return result


def oracle(body, params):
    events = []
    env = dict(params, shake=lambda *a: events.append(["shake", list(a)]),
               hit_stop=lambda *a: events.append(["hit_stop", list(a)]))
    module = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(body), type_ignores=[]))
    exec(compile(module, "<actual-python-feedback-slice>", "exec"), env)
    return events


def build():
    source_methods = methods()
    lines = ["class_name HeroFeedback", "extends RefCounted", "", "## Generated game-feel slice only. Do not edit; no particle/rig parity claimed."]
    fixture = {"schema": 1, "sources": {}, "cases": []}
    for method, signature in (
            ("on_cast", "cast(bus: HeroCombatFeel, hero: String, skill: String)"),
            ("on_impact", "impact(bus: HeroCombatFeel, hero: String, power: float, crit: bool)")):
        lines.extend(["", "", "static func " + signature + " -> void:", "\tmatch hero:"])
        for hero in STARTERS:
            body = source_methods[hero][method]
            lines.append('\t\t"' + hero + '":')
            lines.extend(statements(body, 3))
            if method == "on_cast":
                samples = [{"skill": key} for key in ("q", "w", "e", "r")]
            else:
                samples = [{"power": p, "crit": c} for p in (0.0, 0.7, 1.0, 1.5, 2.3) for c in (False, True)]
            for params in samples:
                fixture["cases"].append({"hero": hero, "method": method, "params": params,
                                          "events": oracle(body, params)})
        lines.extend(["\t\t_:", "\t\t\tpass"])
    lines.extend(["", "", "static func projectile_hit(bus: HeroCombatFeel, hero: String, damage: float, crit: bool) -> void:", "\tmatch hero:"])
    for hero in ("sylara", "vex", "zephyr"):
        tree = ast.parse((ROOT / "heroes" / (hero + "_fx.py")).read_text())
        hook = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "notify_projectile_impact")
        attempt = next(n for n in hook.body if isinstance(n, ast.Try))
        assign = next(n for n in attempt.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "power")
        lines.extend(['\t\t"' + hero + '":', "\t\t\tvar power := " + expression(assign.value),
                      "\t\t\timpact(bus, hero, power, crit)"])
        for damage in (0.0, 45.0, 180.0):
            for crit in (False, True):
                params = {"damage": damage, "crit": crit}
                fixture["cases"].append({"hero": hero, "method": "projectile_hit", "params": params,
                    "events": oracle([assign] + source_methods[hero]["on_impact"], params)})
    lines.extend(["\t\t_:", "\t\t\tpass"])
    for hero in STARTERS:
        path = ROOT / "heroes" / (hero + "_fx.py")
        fixture["sources"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return "\n".join(lines) + "\n", json.dumps(fixture, indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    script, fixture = build()
    # Match repository formatting without making gdtoolkit a preparation dependency.
    for path, text in ((OUT, script), (FIXTURE, fixture)):
        if args.check:
            if not path.exists() or path.read_text() != text:
                parser.exit(1, f"feedback artifact drift: {path.relative_to(ROOT)}\n")
        else:
            path.write_text(text)
    print("hero feedback slices and Python oracle OK")


if __name__ == "__main__":
    main()
