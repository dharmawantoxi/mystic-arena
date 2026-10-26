"""Source oracle for the reachability of Urgharun's skill FX (layer 9bq12).

`bosses/level40.py::_NS_urgharun.draw_urgharun` paints the Q/W/E/R layers only while
`getattr(boss, "active_skill", None)` names that key. Layers 9bq4-9bq9 ported those layers, so the
only question left is WHO sets `active_skill` in the source - and the answer decides whether an AI
recipe may be added without inventing gameplay.

`Boss._update` (`bosses/base_boss.py`) ends its attack branch with one long chain

    if self.boss_type == "abaddon":
        self._smart_ai_abaddon(enemies, dist)
    elif self.boss_type == "alchemist":
        ...

and every `self.active_skill = 'q'/'w'/'e'/'r'` in the file lives inside one of those
`_smart_ai_*` methods. This oracle harvests the chain and the writers with `ast` and pins the fact
that `"urgharun"` appears in neither: the boss owns skill stats but no recipe, so its four skill
layers are unreachable in the source as well, and the rebuild must stay equally quiet.

Run: python godot_rebuild/tests/urgharun_ai_reach_source_oracle.py
"""
import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "bosses" / "base_boss.py"
DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "urgharun_ai_reach_source.json"
OWNER = "Boss"
SUBJECT = "urgharun"
SKILL_KEYS = (
    "skill_q_damage", "skill_q_cooldown",
    "skill_w_damage", "skill_w_cooldown",
    "skill_e_damage", "skill_e_cooldown",
    "skill_r_damage", "skill_r_cooldown",
)


def _owner():
    tree = ast.parse(BASE.read_text(encoding="utf-8"))
    return next((node for node in tree.body
                 if isinstance(node, ast.ClassDef) and node.name == OWNER), None)


def _is_boss_type_test(node):
    if not isinstance(node, ast.Compare) or len(node.comparators) != 1:
        return None
    left, right = node.left, node.comparators[0]
    if (isinstance(left, ast.Attribute) and left.attr == "boss_type"
            and isinstance(right, ast.Constant) and isinstance(right.value, str)):
        return right.value
    return None


def dispatch_types():
    """Every `elif self.boss_type == "<type>"` arm of the smart-AI chain, in source order."""
    owner = _owner()
    update = next((node for node in owner.body
                   if isinstance(node, ast.FunctionDef) and node.name == "update"), None)
    # The chain is nested inside the attack branch, so every `if` of `update` is a candidate and
    # the source order is recovered from the line numbers.
    if update is None:
        raise AssertionError("Boss.update not found in %s" % BASE.name)
    found = []
    for node in ast.walk(update):
        if not isinstance(node, ast.If):
            continue
        name = _is_boss_type_test(node.test)
        if name is not None:
            found.append((node.lineno, name))
    return [name for _line, name in sorted(found)]
    return found


def smart_ai_methods():
    owner = _owner()
    return sorted(node.name for node in owner.body
                  if isinstance(node, ast.FunctionDef) and node.name.startswith("_smart_ai_"))


def active_skill_writers():
    """`{function: [literal keys]}` for every `self.active_skill = <literal>` assignment."""
    owner = _owner()
    writers = {}
    for node in owner.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        values = []
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Assign):
                continue
            for target in inner.targets:
                if (isinstance(target, ast.Attribute) and target.attr == "active_skill"
                        and isinstance(inner.value, ast.Constant)):
                    values.append(inner.value.value)
        if values:
            writers[node.name] = values
    return writers


def urgharun_stats():
    spec = importlib.util.spec_from_file_location("boss_data", DATA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.get_all_boss_types()
    if isinstance(rows, dict):
        row = rows[SUBJECT]
    else:
        row = next(item for item in rows if item.get("id", item.get("type")) == SUBJECT)
    return row


def source_fixture():
    chain = dispatch_types()
    methods = smart_ai_methods()
    writers = active_skill_writers()
    skill_writers = {name: values for name, values in writers.items()
                     if any(value is not None for value in values)}
    if SUBJECT in chain:
        raise AssertionError("%s is in the smart-AI chain" % SUBJECT)
    if "_smart_ai_%s" % SUBJECT in methods:
        raise AssertionError("%s owns a smart-AI recipe" % SUBJECT)
    # Recipes write the key inline or through `_cast_*`/`_<boss>_q` helpers, so the pin is not
    # "only `_smart_ai_*` writes" but "no writer belongs to the subject".
    subject_writers = sorted(name for name in writers if "urg" in name.lower())
    if subject_writers:
        raise AssertionError("%s writes active_skill: %s" % (SUBJECT, subject_writers))
    row = urgharun_stats()
    return {
        "subject": SUBJECT,
        "dispatch_count": len(chain),
        "dispatch_has_subject": SUBJECT in chain,
        "dispatch_head": chain[:5],
        "dispatch_tail": chain[-5:],
        "smart_ai_method_count": len(methods),
        "smart_ai_has_subject": ("_smart_ai_%s" % SUBJECT) in methods,
        "active_skill_writer_count": len(writers),
        "active_skill_keys": sorted({value for values in skill_writers.values()
                                     for value in values if value is not None}),
        "subject_writers": subject_writers,
        "subject_reset_count": len(writers.get("_tick_l9_timers", []))
        + len(writers.get("_init_l9_timers", [])),
        "stats": {
            "boss_class": row["boss_class"],
            "skill_keys": [key for key in SKILL_KEYS if key in row],
            "skill_count": sum(1 for key in SKILL_KEYS if key in row),
            "skill_q_cooldown": row.get("skill_q_cooldown"),
            "skill_r_damage": row.get("skill_r_damage"),
        },
    }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
