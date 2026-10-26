"""Source oracle for the user-authorized Urgharun R-AI extension (slice 9bq13).

The Python project has Urgharun's R damage/cooldown data and R presentation, but no Urgharun AI
recipe: it is absent from `Boss.update` and has no `_smart_ai_urgharun`. Since the user explicitly
authorized the simulation addition, the Godot port adds one R-only recipe without changing that
Python source. Its trigger/radius/timer shape is deliberately the already-shipped Gravefang R
recipe, harvested here from `Boss._smart_ai_gravefang`, while damage/cooldown come from Urgharun's
existing normalized boss data. This fixture documents the informed extension; it is not a claim of
Python gameplay parity.

Run: python godot_rebuild/tests/urgharun_ai_skill_source_oracle.py
"""
import ast
import importlib.util
import json
from pathlib import Path

from urgharun_ai_reach_source_oracle import source_fixture as reach_fixture

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "bosses" / "base_boss.py"
DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "urgharun_ai_skill_source.json"


def _boss_class():
    tree = ast.parse(BASE.read_text(encoding="utf-8"))
    return next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == "Boss")


def _method(name):
    owner = _boss_class()
    return next(node for node in owner.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def _boss_data():
    spec = importlib.util.spec_from_file_location("boss_data", DATA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_all_boss_types()


def _has_compare(method, left_name, op_type, value):
    for node in ast.walk(method):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not (isinstance(node.left, ast.Name) and node.left.id == left_name):
            continue
        if not isinstance(node.ops[0], op_type) or len(node.comparators) != 1:
            continue
        right = node.comparators[0]
        if isinstance(right, ast.Constant) and right.value == value:
            return True
    return False


def _r_radius(method):
    radii = []
    for node in ast.walk(method):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.LtE) or len(node.comparators) != 1:
            continue
        if not isinstance(node.comparators[0], ast.Constant):
            continue
        if isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Attribute):
            if (isinstance(node.left.func.value, ast.Name)
                    and node.left.func.value.id == "math"
                    and node.left.func.attr == "hypot"):
                radii.append(node.comparators[0].value)
    return sorted(set(radii))


def _r_branch(method):
    for node in ast.walk(method):
        if not isinstance(node, ast.If):
            continue
        if any(
            isinstance(inner, ast.Assign)
            and isinstance(inner.value, ast.Constant)
            and inner.value.value == "r"
            and any(
                isinstance(target, ast.Attribute) and target.attr == "active_skill"
                for target in inner.targets
            )
            for inner in ast.walk(node)
        ):
            return node
    raise AssertionError("Gravefang's active R branch disappeared")


def _assigned_constant(method, attr):
    for node in ast.walk(method):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        if any(isinstance(target, ast.Attribute) and target.attr == attr
               for target in node.targets):
            return node.value.value
    return None


def _stats_get(method, key):
    for node in ast.walk(method):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "get" or not node.args:
            continue
        if isinstance(node.args[0], ast.Constant) and node.args[0].value == key:
            return node.args[1].value if len(node.args) > 1 and isinstance(
                node.args[1], ast.Constant) else None
    return None


def source_fixture():
    reach = reach_fixture()
    if reach["dispatch_has_subject"] or reach["smart_ai_has_subject"]:
        raise AssertionError("Python source now has an Urgharun AI recipe; re-audit 9bq13")
    gravefang = _method("_smart_ai_gravefang")
    r_branch = _r_branch(gravefang)
    stats = _boss_data()["urgharun"]
    result = {
        "subject": "urgharun",
        "python_recipe_exists": False,
        "urgharun_r": {
            "damage": int(stats["skill_r_damage"]),
            "cooldown": int(stats["skill_r_cooldown"]),
            "boss_class": str(stats["boss_class"]),
        },
        "reference": {
            "boss": "gravefang",
            "crowd_threshold": 3,
            "crowd_shape_found": _has_compare(r_branch, "nearby", ast.GtE, 3),
            "low_hp_ratio": 0.35,
            "low_hp_shape_found": any(
                isinstance(node, ast.Compare)
                and isinstance(node.ops[0], ast.Lt)
                and len(node.comparators) == 1
                and isinstance(node.comparators[0], ast.Constant)
                and node.comparators[0].value == 0.35
                for node in ast.walk(r_branch) if isinstance(node, ast.Compare)
            ),
            "radius": 180,
            "r_radii_found": _r_radius(r_branch),
            "active_skill": "r",
            "active_skill_timer": _assigned_constant(r_branch, "active_skill_timer"),
            "r_cooldown_default": _stats_get(r_branch, "skill_r_cooldown"),
            "r_damage_default": _stats_get(r_branch, "skill_r_damage"),
        },
    }
    ref = result["reference"]
    if not ref["crowd_shape_found"] or not ref["low_hp_shape_found"]:
        raise AssertionError("Gravefang R trigger changed; re-audit the Urgharun adaptation")
    if ref["r_radii_found"] != [180] or ref["active_skill_timer"] != 100:
        raise AssertionError("Gravefang R area/timer changed; re-audit the Urgharun adaptation")
    if ref["r_cooldown_default"] != 620 or ref["r_damage_default"] != 380:
        raise AssertionError("Gravefang R fallback stats changed; re-audit the Urgharun adaptation")
    return result


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
