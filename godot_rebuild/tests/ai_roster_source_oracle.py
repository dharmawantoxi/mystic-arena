"""Read-only oracle for AIPlayer hero ownership and scene-roster separation."""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTITY = ROOT / "_entity.py"
CORE = ROOT / "_core.py"
PROTOTYPE = ROOT / "godot_rebuild/scripts/match/prototype_battle.gd"
SESSION = ROOT / "godot_rebuild/scripts/simulation/prototype_session.gd"
FIXTURE = Path(__file__).parent / "fixtures/ai_roster_source.json"


def _method(path: Path, class_name: str, method_name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError(f"Missing {class_name}.{method_name} in {path}")


def _is_self_heroes(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "heroes"
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _empty_heroes_assignment(function: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Assign)
        and any(_is_self_heroes(target) for target in node.targets)
        and isinstance(node.value, ast.List)
        and not node.value.elts
        for node in ast.walk(function)
    )


def _hero_cap_uses_roster(function: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Lt)
        and isinstance(node.left, ast.Call)
        and isinstance(node.left.func, ast.Name)
        and node.left.func.id == "len"
        and len(node.left.args) == 1
        and _is_self_heroes(node.left.args[0])
        for node in ast.walk(function)
    )


def _controls_owned_roster(function: ast.FunctionDef) -> bool:
    return any(isinstance(node, ast.For) and _is_self_heroes(node.iter) for node in ast.walk(function))


def _purchase_appends_to_roster(function: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
        and _is_self_heroes(node.func.value)
        for node in ast.walk(function)
    )


def _game_roster_union(function: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.BinOp)
        and isinstance(node.value.op, ast.Add)
        and _is_self_heroes(node.value.left)
        and isinstance(node.value.right, ast.Attribute)
        and node.value.right.attr == "heroes"
        and isinstance(node.value.right.value, ast.Attribute)
        and node.value.right.value.attr == "ai"
        and isinstance(node.value.right.value.value, ast.Name)
        and node.value.right.value.value.id == "self"
        for node in ast.walk(function)
    )


def _playable_match_starts_empty() -> bool:
    prototype = PROTOTYPE.read_text(encoding="utf-8")
    session = SESSION.read_text(encoding="utf-8")
    setup = re.search(r"func setup_arena\([^)]*\) -> bool:(.*?)(?=\nfunc )", prototype, re.DOTALL)
    gated_mirrors = bool(
        setup
        and re.search(
            r"if not spawn_legacy_hero_mirrors:\s*return true", setup.group(1)
        )
        and "match_world.setup_arena(false)" in session
    )
    return gated_mirrors


def source_fixture() -> dict:
    game_init = _method(CORE, "Game", "reset")
    ai_init = _method(ENTITY, "AIPlayer", "__init__")
    ai_step = _method(ENTITY, "AIPlayer", "_ai_step")
    ai_control = _method(ENTITY, "AIPlayer", "_control_heroes")
    ai_purchase = _method(ENTITY, "AIPlayer", "_try_buy_hero")
    game_rosters = _method(CORE, "Game", "get_all_heroes")

    player_initial_empty = _empty_heroes_assignment(game_init)
    initial_empty = _empty_heroes_assignment(ai_init)
    cap_uses_roster = _hero_cap_uses_roster(ai_step)
    control_uses_roster = _controls_owned_roster(ai_control)
    purchase_registers = _purchase_appends_to_roster(ai_purchase)
    game_keeps_rosters_separate = _game_roster_union(game_rosters)
    playable_start_empty = _playable_match_starts_empty()

    assert player_initial_empty, "Game must start with an empty player hero list"
    assert initial_empty, "AIPlayer must start with its own empty heroes list"
    assert cap_uses_roster, "AI hero cap must count AIPlayer.heroes"
    assert control_uses_roster, "AI control must iterate AIPlayer.heroes"
    assert purchase_registers, "Successful AI purchases must append to AIPlayer.heroes"
    assert game_keeps_rosters_separate, "Game keeps player heroes and AI heroes as separate rosters"
    assert playable_start_empty, "The playable Godot session must not free-spawn hero mirrors"

    return {
        "source": {
            "initial_player_hero_count": 0,
            "initial_ai_hero_count": 0,
            "hero_cap_uses_ai_roster": cap_uses_roster,
            "control_uses_ai_roster": control_uses_roster,
            "purchase_registers_ai_hero": purchase_registers,
            "game_rosters_are_separate": game_keeps_rosters_separate,
            "playable_startup_is_empty": playable_start_empty,
        },
        "scenario": {
            "initial_player_hero_count": 0,
            "initial_red_scene_hero_count": 0,
            "source_ai_roster_before_purchase": 0,
        },
    }


if __name__ == "__main__":
    import sys

    fixture = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    else:
        assert fixture == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "AI roster ownership source fixture drift"
        )
    print("PASS: playable Godot and pygame start with empty live hero rosters; AI ownership stays separate")
