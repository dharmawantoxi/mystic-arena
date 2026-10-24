"""Source oracle for the top-left gold HUD (layer 9bv2).

`_core.py::Game._draw_gold_hud` runs from `Game.draw` while the wide-screen side panel is off
(`if not _PANEL_AKTIF()`), after the shop hints and before the boss banner. It paints:
  * the gold chip at (18, 22): 40 px high, `max(150, val_w + inc_w + 78)` wide, radius 20,
    filled with `ui_theme._vgrad((44, 38, 18) -> (24, 20, 9))` when `ui_theme.cheap_alpha()`
    (solid (26, 22, 10) otherwise), a 2 px GOLD border, the `coin` icon at (x + 24, centre)
    s = 0.9, `f"{gold:,}"` in 24 px body_bold at (x + 44, y + 5), a hairline at gx - 6 and
    `+rate/s` in 17 px body_medium at (gx, y + 11), with gx = x + 44 + val_w + 12;
  * the mode badge at (x, y + 46): 24 px high, label width + 24 wide, radius 12, the `swords`
    icon at (x + 15, centre) s = 0.55 and EASY / NORMAL / HARD in 18 px body_semibold.
The REAL `_draw_gold_hud` (harvested from the `Game` class), `format_gold_rate` and
`ui_theme.draw_icon` run under the recording pygame shim of `draw_recorder.py` (text measured
with its fake `0.55 * size` glyphs); `ui_theme._vgrad` is recorded as one `vgrad` op.
Run: python godot_rebuild/tests/gold_hud_draw_source_oracle.py
"""
import ast
import json
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "_core.py"
UI_THEME = ROOT / "ui_theme.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gold_hud_draw_source.json"
# (label, gold, gold_per_second, difficulty, cheap_alpha)
FRAMES = [
    ("opening_normal", 1000, 3.0, "normal", True),
    ("broke_easy_min_width", 0, 5.7, "easy", True),
    ("hard_rounded_rate", 12345, 3.75, "hard", True),
    ("rich_solid", 987654, 12.0, "normal", False),
    ("hard_solid", 250, 4.26, "hard", False),
    ("million_unknown_mode", 1500000, 0.5, "nightmare", True),
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


def _ui_theme(pygame, cheap):
    module = types.ModuleType("ui_theme")
    module.pygame = pygame
    module.GOLD = _constant(UI_THEME, "GOLD")
    module.cheap_alpha = lambda: cheap

    def vgrad(w, h, top, bottom, radius=0):
        surface = rec.Surface((w, h))
        surface.ops.append({"kind": "vgrad", "rect": [0, 0, int(w), int(h)], "top": list(top),
                            "bottom": list(bottom), "radius": int(radius), "mult": 255})
        return surface

    module._vgrad = vgrad
    for segment in rec.harvest(UI_THEME, ["draw_icon"]):
        exec(compile(segment, UI_THEME.name, "exec"), module.__dict__)
    return module


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    frames = []
    with rec.installed({"pygame": pygame}):
        for label, gold, rate, difficulty, cheap in FRAMES:
            namespace = {"pygame": pygame, "ui_theme": _ui_theme(pygame, cheap),
                         "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
                         "GOLD_PER_SECOND": _constant(CORE, "GOLD_PER_SECOND")}
            for segment in rec.harvest(CORE, ["format_gold_rate"]):
                exec(compile(segment, CORE.name, "exec"), namespace)
            exec(compile(_method(CORE, "Game", "_draw_gold_hud"), CORE.name, "exec"), namespace)
            game = SimpleNamespace(gold=gold, gold_per_second=rate, difficulty=difficulty)
            screen = rec.Surface((1280, 720))
            namespace["_draw_gold_hud"](game, screen)
            frames.append({"label": label, "gold": gold, "rate": rate, "difficulty": difficulty,
                           "cheap_alpha": cheap, "ops": screen.ops})
    return {
        "source": "_core.py::Game._draw_gold_hud (+ ui_theme.draw_icon, format_gold_rate)",
        "glyph_factor": rec.GLYPH_FACTOR,
        "frames": frames,
    }


def main():
    data = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ops = sum(len(frame["ops"]) for frame in data["frames"])
    print("gold HUD oracle: %d frames, %d ops -> %s" % (len(data["frames"]), ops, FIXTURE.name))


if __name__ == "__main__":
    main()
