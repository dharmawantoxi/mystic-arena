"""Source oracle for the controller hint bar (layer 9bv4).

`Game.draw` calls `_draw_input_hints` after the victory / defeat overlay and before the level
intro and boss death. It only paints in controller mode, never while the level intro, boss
intro or boss celebration runs, with the context victory / defeat / shop / game, through
`ControllerManager.draw_hint_bar(surface, context)` (defaults: `get_font(19)`,
y = SCREEN_HEIGHT - 30, centred):
  * every (label, desc) item is `label_w + 2 * key_pad + 5 + desc_w` wide, items 16 px apart,
    the row starts at `(SCREEN_WIDTH - total_w) // 2`;
  * a (0, 0, 0, 140) SRCALPHA strip `total_w + 14` x `font_h + 8` at (x - 7, y - 4);
  * per item a radius-4 key box (48, 52, 70) at (x, y - 1), `label_w + 10` x `font_h + 2`,
    edged 1 px (120, 130, 165), the label (255, 235, 140) at (x + 5, y) and the description
    (205, 210, 225) at (x + key_w + 5, y).
The REAL `draw_hint_bar` (harvested from `ControllerManager`) runs under the recording pygame
shim of `draw_recorder.py` (text measured with its fake `0.55 * size` glyphs, `font_h = size`);
`get_hints` is a stand-in returning each frame's list.
Run: python godot_rebuild/tests/input_hint_draw_source_oracle.py
"""
import ast
import json
import textwrap
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "input_hint_draw_source.json"
# (label, hints). "overflow" is wider than the screen with an odd leftover, so the start x
# pins Python's floor division on a negative number.
FRAMES = [
    ("game", [["LS", "Cursor"], ["A", "Select"], ["RT", "Move Hero"], ["START", "Pause"]]),
    ("shop", [["A", "Buy"], ["B", "Close"], ["RS/D-PAD", "Scroll"], ["R3", "Snap"]]),
    ("victory", [["Y", "Next Level"], ["X", "Replay"], ["VIEW", "Menu"]]),
    ("single", [["A", "Skip"]]),
    ("empty", []),
    ("overflow", [["LB", "Previous hero"]] * 8 + [["RB", "Next"]]),
]


def _method(path, owner, name):
    text = path.read_text(encoding="utf-8")
    cls = next(node for node in ast.parse(text).body
               if isinstance(node, ast.ClassDef) and node.name == owner)
    func = next((node for node in cls.body
                 if isinstance(node, ast.FunctionDef) and node.name == name), None)
    if func is None:
        raise AssertionError("%s.%s not found in %s" % (owner, name, path.name))
    return textwrap.dedent(ast.get_source_segment(text, func, padded=True))


def _constant(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, path.name))


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    frames = []
    with rec.installed({"pygame": pygame}):
        namespace = {"pygame": pygame,
                     "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
                     "SCREEN_WIDTH": _constant(CORE, "SCREEN_WIDTH"),
                     "SCREEN_HEIGHT": _constant(CORE, "SCREEN_HEIGHT")}
        exec(compile(_method(CORE, "ControllerManager", "draw_hint_bar"), CORE.name, "exec"),
             namespace)
        for label, hints in FRAMES:
            manager = SimpleNamespace(get_hints=lambda context, hints=hints: [tuple(h) for h in hints])
            screen = rec.Surface((1280, 720))
            namespace["draw_hint_bar"](manager, screen, label)
            frames.append({"label": label, "hints": hints, "ops": screen.ops})
    return {
        "source": "_core.py::ControllerManager.draw_hint_bar (Game._draw_input_hints)",
        "glyph_factor": rec.GLYPH_FACTOR,
        "frames": frames,
    }


def main():
    data = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ops = sum(len(frame["ops"]) for frame in data["frames"])
    print("input hint oracle: %d frames, %d ops -> %s" % (len(data["frames"]), ops, FIXTURE.name))


if __name__ == "__main__":
    main()
