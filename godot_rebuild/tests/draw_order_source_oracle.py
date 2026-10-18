"""Source oracle for the paint ORDER of the world effects and the screen overlays (layer 9bi).

Layers 9bb-9bh ported what each overlay looks like; this one pins WHERE it sits in
the stack, read straight from the source with `ast` (nothing is run):

* `_core.py::Game.draw`: the order of `map_renderer.draw`, `effects.draw`,
  `tactical.draw_world`, `boss_intro.draw`, `effects.draw_ui`, `level_intro.draw`
  and `boss_death.draw`. The source comment says the boss banner is drawn BEFORE
  `effects.draw_ui` so the wave announcer is never covered, and the boss death
  animation is the very last call, above every HUD layer.
* `_render.py::EffectManager.draw` (path preview, explosions, particles, floating
  texts) and `draw_ui` (wave announcer, achievement): loop variables are resolved
  to the list they walk, so the names match the attributes of the Godot port.

Run: python godot_rebuild/tests/draw_order_source_oracle.py
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "_core.py"
RENDER = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "draw_order_source.json"

# `Game.draw` calls that matter here, with the token the fixture uses for each.
GAME_CALLS = {
    "self.map_renderer.draw": "map",
    "self.effects.draw": "effects",
    "self.tactical.draw_world": "tactical_world",
    "self.boss_intro.draw": "boss_intro",
    "self.effects.draw_ui": "effects_ui",
    "self.level_intro.draw": "level_intro",
    "self.boss_death.draw": "boss_death",
}


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _game_draw(tree, text):
    for node in ast.walk(tree):
        if (isinstance(node, ast.FunctionDef) and node.name == "draw"
                and "self.boss_death.draw(" in ast.get_source_segment(text, node)):
            return node
    raise AssertionError("Game.draw not found in _core.py")


def game_order():
    text = CORE.read_text(encoding="utf-8")
    draw = _game_draw(ast.parse(text), text)
    seen = {}
    for node in ast.walk(draw):
        if isinstance(node, ast.Call) and _dotted(node.func) in GAME_CALLS:
            token = GAME_CALLS[_dotted(node.func)]
            place = (node.lineno, node.col_offset)
            seen[token] = min(seen.get(token, place), place)
    missing = set(GAME_CALLS.values()) - set(seen)
    if missing:
        raise AssertionError("Game.draw lost calls: %s" % sorted(missing))
    return [token for token, _place in sorted(seen.items(), key=lambda item: item[1])]


def _effect_method(tree, name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "EffectManager":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    return item
    raise AssertionError("EffectManager.%s not found" % name)


def effect_order(name):
    """Attributes `EffectManager.<name>` draws, in order (a loop counts as its list)."""
    tree = ast.parse(RENDER.read_text(encoding="utf-8"))
    order = []
    for statement in _effect_method(tree, name).body:
        if isinstance(statement, ast.For) and isinstance(statement.target, ast.Name):
            drawn = [_dotted(node.func) for node in ast.walk(statement)
                     if isinstance(node, ast.Call)]
            if "%s.draw" % statement.target.id in drawn:
                order.append(_dotted(statement.iter).replace("self.", "", 1))
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            target = _dotted(statement.value.func)
            if target.startswith("self.") and target.endswith(".draw"):
                order.append(target[len("self."):-len(".draw")])
    return order


def source_fixture():
    return {
        "source": "_core.py::Game.draw + _render.py::EffectManager.draw / draw_ui",
        "game_draw": game_order(),
        "effects_draw": effect_order("draw"),
        "effects_draw_ui": effect_order("draw_ui"),
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%s)" % (FIXTURE.relative_to(ROOT), " > ".join(fixture["game_draw"])))


if __name__ == "__main__":
    main()
