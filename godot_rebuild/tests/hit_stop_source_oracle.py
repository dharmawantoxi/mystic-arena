"""Read-only AST oracle for the shared Python hit-stop contract.

Only the original HitStop class is executed, isolated from Pygame and the game.
The remainder is statically checked for the active Game.update/reset wiring and
source-defined skill-cast request values; no save files are read or written.
"""
import ast
import json
import operator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/hit_stop_source.json"
CAST_MODULES = {
    "kaizen": "heroes/kaizen_fx.py",
    "grimjaw": "heroes/grimjaw_fx.py",
    "sylara": "heroes/sylara_fx.py",
    "vex": "heroes/vex_fx.py",
}


def _number(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_number(node.operand)
    if isinstance(node, ast.BinOp):
        operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }
        operation = operations.get(type(node.op))
        if operation is not None:
            return float(operation(_number(node.left), _number(node.right)))
    raise AssertionError(f"Expected a source numeric constant at line {node.lineno}")


def _assignments(tree):
    result = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                result[target.id] = node.value
    return result


def _source_hit_stop():
    tree = ast.parse((ROOT / "heroes/combat_feel.py").read_text(encoding="utf-8"))
    assignments = _assignments(tree)
    global_names = ("HIT_STOP_ENABLED", "HIT_STOP_MIN", "HIT_STOP_MAX", "FIXED_DT")
    globals_for_class = {name: _number(assignments[name]) for name in global_names if name != "HIT_STOP_ENABLED"}
    globals_for_class["HIT_STOP_ENABLED"] = bool(ast.literal_eval(assignments["HIT_STOP_ENABLED"]))
    original = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "HitStop"
    )
    class_values = [
        node for node in original.body if isinstance(node, ast.Assign)
    ]
    wanted = {"__init__", "trigger", "consume_frame", "active", "clear"}
    methods = [
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    if {node.name for node in methods} != wanted:
        raise AssertionError("Re-audit combat_feel.HitStop before trusting this oracle")
    cls = ast.ClassDef(
        name="SourceHitStop", bases=[], keywords=[], body=class_values + methods, decorator_list=[]
    )
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = dict(globals_for_class)
    exec(compile(module, "<source HitStop>", "exec"), namespace)  # noqa: S102
    return namespace["SourceHitStop"], globals_for_class, tree


def _hit_stop_behavior(source_class):
    lower = source_class()
    lower.trigger(0.01)
    lower_clamp_frames = lower.frames

    tie = source_class()
    tie.trigger(0.075)
    half_tie_frames = tie.frames

    stronger = source_class()
    stronger.trigger(0.03)
    stronger.trigger(0.08)
    stronger_frames = stronger.frames
    sequence = [stronger.consume_frame() for _ in range(stronger_frames)]
    total_after_last_freeze = stronger.total
    empty_consume = stronger.consume_frame()
    total_after_empty_consume = stronger.total
    stronger.trigger("invalid")

    return {
        "low_clamp_frames": lower_clamp_frames,
        "half_tie_to_even_frames": half_tie_frames,
        "stronger_request_frames": stronger_frames,
        "consume_sequence": sequence,
        "total_after_last_freeze": total_after_last_freeze,
        "empty_consume": empty_consume,
        "total_after_empty_consume": total_after_empty_consume,
        "invalid_request_ignored": stronger.frames == 0 and stronger.total == 0,
    }


def _attribute_path(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.insert(0, node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.insert(0, node.id)
        return parts
    return []


def _member_call(node, path):
    return isinstance(node, ast.Call) and _attribute_path(node.func) == path


def _source_freeze_contract():
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    game = next(node for node in core.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    update = next(
        node for node in game.body if isinstance(node, ast.FunctionDef) and node.name == "update"
    )
    reset = next(
        node for node in game.body if isinstance(node, ast.FunctionDef) and node.name == "reset"
    )
    guard = next(
        (
            node
            for node in ast.walk(update)
            if isinstance(node, ast.If)
            and any(
                _member_call(candidate, ["_feel", "should_freeze_frame"])
                for candidate in ast.walk(node.test)
            )
        ),
        None,
    )
    if guard is None:
        return {name: False for name in _freeze_contract_fields()}
    guard_nodes = [candidate for statement in guard.body for candidate in ast.walk(statement)]
    game_speed_lines = [
        candidate.lineno
        for candidate in ast.walk(update)
        if isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Name)
        and candidate.func.id == "GameSettings"
    ]
    return {
        "checks_before_game_speed": bool(game_speed_lines) and guard.lineno < min(game_speed_lines),
        "uses_global_consumer": True,
        "advances_active_skill_timer": any(
            isinstance(candidate, ast.Attribute) and candidate.attr == "active_skill_timer"
            for candidate in guard_nodes
        ),
        "advances_skill_cooldowns": any(
            isinstance(candidate, ast.Attribute) and candidate.attr == "skill_cooldowns"
            for candidate in guard_nodes
        ),
        "ticks_tower_debuffs": any(
            _member_call(candidate, ["_h", "_tick_tower_debuffs"])
            for candidate in guard_nodes
        ),
        "updates_effects": any(
            _member_call(candidate, ["self", "effects", "update"])
            for candidate in guard_nodes
        ),
        "returns_before_regular_simulation": any(
            isinstance(candidate, ast.Return) for candidate in guard_nodes
        ),
        "reset_clears_shared_state": any(
            _member_call(candidate, ["_feel", "reset"])
            for candidate in ast.walk(reset)
        ),
    }


def _freeze_contract_fields():
    return (
        "checks_before_game_speed",
        "uses_global_consumer",
        "advances_active_skill_timer",
        "advances_skill_cooldowns",
        "ticks_tower_debuffs",
        "updates_effects",
        "returns_before_regular_simulation",
        "reset_clears_shared_state",
    )


def _skill_key(test):
    for node in ast.walk(test):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name):
            continue
        if node.left.id != "skill" or len(node.comparators) != 1:
            continue
        value = node.comparators[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    return None


def _direct_shared_bus_call(method):
    return method is not None and any(
        _member_call(candidate, ["_feel", "hit_stop"]) for candidate in ast.walk(method)
    )


def _source_dash_triggers():
    relative_path = CAST_MODULES["kaizen"]
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    directors = []
    for candidate in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        methods = {
            node.name: node for node in candidate.body if isinstance(node, ast.FunctionDef)
        }
        if "on_dash" in methods and "update" in methods:
            directors.append(methods)
    if len(directors) != 1:
        raise AssertionError("Re-audit the source Kaizen dash director")
    on_dash = directors[0]["on_dash"]
    requests = [
        node
        for node in ast.walk(on_dash)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "hit_stop"
    ]
    if len(requests) != 1 or len(requests[0].args) != 1:
        raise AssertionError("Re-audit the source Kaizen on_dash hit-stop request")
    update = directors[0]["update"]
    dispatched_on_dash_edge = any(
        isinstance(branch, ast.If)
        and any(
            isinstance(node, ast.Name) and node.id == "dashing"
            for node in ast.walk(branch.test)
        )
        and any(
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.Not)
            and isinstance(node.operand, ast.Attribute)
            and node.operand.attr == "_dash_seen"
            for node in ast.walk(branch.test)
        )
        and any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr == "on_dash"
            for statement in branch.body
            for node in ast.walk(statement)
        )
        for branch in ast.walk(update)
    )
    if not dispatched_on_dash_edge:
        raise AssertionError("Source Kaizen on_dash is no longer tied to the dash-state edge")
    return {"kaizen": {"q": _number(requests[0].args[0])}}


def _source_live_melee_impact_hook():
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "notify_melee_impact")
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "notify_melee_impact")
        )
        for node in ast.walk(tree)
    )


def _source_cast_triggers():
    result = {}
    wrappers = {}
    for hero, relative_path in CAST_MODULES.items():
        tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
        candidates = []
        for director in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            on_cast = next(
                (
                    node
                    for node in director.body
                    if isinstance(node, ast.FunctionDef) and node.name == "on_cast"
                ),
                None,
            )
            if on_cast is not None and any(
                isinstance(candidate, ast.Call)
                and isinstance(candidate.func, ast.Name)
                and candidate.func.id == "hit_stop"
                for candidate in ast.walk(on_cast)
            ):
                candidates.append(on_cast)
        if len(candidates) != 1:
            raise AssertionError(f"Re-audit the source {hero} cast director")
        on_cast = candidates[0]
        values = {}
        for branch in ast.walk(on_cast):
            if not isinstance(branch, ast.If):
                continue
            key = _skill_key(branch.test)
            if key is None:
                continue
            calls = [
                candidate
                for statement in branch.body
                for candidate in ast.walk(statement)
                if isinstance(candidate, ast.Call)
                and isinstance(candidate.func, ast.Name)
                and candidate.func.id == "hit_stop"
            ]
            if calls:
                if len(calls) != 1 or len(calls[0].args) != 1:
                    raise AssertionError(f"Review dynamic {hero} {key} hit-stop trigger")
                values[key] = ast.literal_eval(calls[0].args[0])
        if not values:
            raise AssertionError(f"No source on_cast hit-stop triggers found for {hero}")
        definitions = {
            node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        public_trigger = definitions.get("hit_stop")
        helper = definitions.get("_feel_hit_stop")
        delegates_to_helper = public_trigger is not None and any(
            isinstance(candidate, ast.Call)
            and isinstance(candidate.func, ast.Name)
            and candidate.func.id == "_feel_hit_stop"
            for candidate in ast.walk(public_trigger)
        )
        wrappers[hero] = _direct_shared_bus_call(public_trigger) or (
            delegates_to_helper and _direct_shared_bus_call(helper)
        )
        if not wrappers[hero]:
            raise AssertionError(f"Source {hero} cast wrapper no longer reaches combat_feel")
        result[hero] = values
    return result, wrappers


def _source_api_contract(tree):
    definitions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    singleton = any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "HITSTOP" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "HitStop"
        for node in tree.body
    )
    public_trigger = definitions.get("hit_stop")
    freeze_consumer = definitions.get("should_freeze_frame")
    return {
        "has_shared_singleton": singleton,
        "trigger_delegates_to_singleton": public_trigger is not None
        and any(_member_call(node, ["HITSTOP", "trigger"]) for node in ast.walk(public_trigger)),
        "consumer_delegates_to_singleton": freeze_consumer is not None
        and any(
            _member_call(node, ["HITSTOP", "consume_frame"])
            for node in ast.walk(freeze_consumer)
        ),
    }


def source_contract():
    source_class, globals_for_class, tree = _source_hit_stop()
    cast_triggers, cast_wrappers = _source_cast_triggers()
    dash_triggers = _source_dash_triggers()
    return {
        "bus": {
            "enabled": globals_for_class["HIT_STOP_ENABLED"],
            "min_seconds": globals_for_class["HIT_STOP_MIN"],
            "max_seconds": globals_for_class["HIT_STOP_MAX"],
            "fixed_dt": globals_for_class["FIXED_DT"],
            "max_frames": source_class.MAX_FRAMES,
            **_hit_stop_behavior(source_class),
        },
        "api": _source_api_contract(tree),
        "freeze_contract": _source_freeze_contract(),
        "cast_triggers": cast_triggers,
        "cast_wrappers": cast_wrappers,
        "dash_triggers": dash_triggers,
        "live_melee_impact_hook": _source_live_melee_impact_hook(),
    }


def main():
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    actual = source_contract()
    if actual != expected:
        raise AssertionError(
            "Python hit-stop source contract changed; review and refresh the fixture:\n"
            + json.dumps(actual, indent=2, sort_keys=True)
        )
    total = sum(len(value) if isinstance(value, dict) else 1 for value in actual.values())
    total += sum(len(hero_map) for hero_map in actual["cast_triggers"].values())
    total += sum(len(hero_map) for hero_map in actual["dash_triggers"].values())
    print(f"PASS: {total} hit-stop source checks")


if __name__ == "__main__":
    main()
