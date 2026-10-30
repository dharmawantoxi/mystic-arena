#!/usr/bin/env python3
"""Read-only source oracle for ``mobile/hud.py`` (layer 9bv21).

The real ``TouchButton`` / ``TouchHUD`` classes are compiled from the AST and
run under a pygame shim (``Rect`` only), a ``platform_utils`` stub that feeds
the safe area and the right-panel flag, and a ``levels`` stub for
``get_next_level``. Recorded per case:

* the built touch buttons - rect, hit rect (24 px inflate, then the 80 px
  minimum), label, sub label, shape, colour and font size;
* the visibility of every button for a grid of match states, cinematics,
  dock-present and next-level availability;
* the press-animation decay (0.12 per sync);
* ``hit_test`` / ``blocks`` answers for positions inside and outside buttons,
  including a hidden button and the last-drawn-wins order;
* ``apply_hud_action``'s intent for every action.

Drawing is not recorded here: the painters need font and surface shims, and
the port's layer 9bv21 covers layout, state and input routing.

Run:
    python godot_rebuild/tests/touch_hud_source_oracle.py            # verify
    python godot_rebuild/tests/touch_hud_source_oracle.py --write    # refresh
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mobile" / "hud.py"
FIXTURE = Path(__file__).with_name("fixtures") / "touch_hud_source.json"

LOGICAL_W, LOGICAL_H = 1280, 720
SAFE_TOUCH = (28, 10, 1224, 700)
SAFE_DESKTOP = (0, 0, 1280, 720)


class Rect:
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Rect):
            args = args[0].tuple()
        elif len(args) == 1:
            args = tuple(args[0])
        self.x, self.y, self.width, self.height = [int(value) for value in args]

    left = property(lambda self: self.x)
    top = property(lambda self: self.y)
    right = property(lambda self: self.x + self.width)
    bottom = property(lambda self: self.y + self.height)
    center = property(lambda self: (self.x + self.width // 2, self.y + self.height // 2))
    topleft = property(lambda self: (self.x, self.y))
    size = property(lambda self: (self.width, self.height))
    w = property(lambda self: self.width)
    h = property(lambda self: self.height)

    def tuple(self):
        return (self.x, self.y, self.width, self.height)

    def copy(self):
        return Rect(self.x, self.y, self.width, self.height)

    def inflate(self, dx, dy):
        return Rect(self.x - dx // 2, self.y - dy // 2, self.width + dx, self.height + dy)

    def collidepoint(self, pos):
        px, py = pos
        return self.x <= px < self.right and self.y <= py < self.bottom


def _platform_stub(safe, panel):
    stub = types.SimpleNamespace()
    stub.LOGICAL_WIDTH = LOGICAL_W
    stub.LOGICAL_HEIGHT = LOGICAL_H
    stub.get_safe_area = lambda: Rect(*safe)
    stub.get_panel_rect = lambda: (Rect(*panel) if panel else None)
    return stub


def _source_namespace(safe, panel):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        or (isinstance(node, ast.ClassDef) and node.name in {"TouchButton", "TouchHUD"})
        or (isinstance(node, ast.FunctionDef) and node.name == "apply_hud_action")
    ]
    pygame = types.SimpleNamespace(Rect=Rect, K_SPACE=32, K_ESCAPE=27, K_LEFT=1073741904)
    quality = types.SimpleNamespace(cheap_alpha=False)
    ui_theme = types.SimpleNamespace(_radial=lambda *args, **kwargs: None)
    env = {
        "pygame": pygame,
        "math": __import__("math"),
        "plat": _platform_stub(safe, panel),
        "Quality": quality,
        "ui_theme": ui_theme,
    }
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, "<source hud>", "exec"), env)
    return env


def _rect_dict(rect):
    return list(rect.tuple())


def _button(button):
    return {
        "action": button.action,
        "rect": _rect_dict(button.rect),
        "hit_rect": _rect_dict(button.hit_rect),
        "label": button.label,
        "sub": button.sub,
        "shape": button.shape,
        "color": [int(value) for value in button.color],
        "font_size": int(button.font_size),
        "visible": bool(button.visible),
    }


class Game:
    def __init__(self, state="playing", level=1, tactical=None, tower=None):
        self.state = state
        self.level_number = level
        self.tactical = tactical if tactical is not None else Tactical()
        self.selected_tower = tower
        self.replay_requested = False
        self.next_level_requested = False
        self.return_to_menu_requested = False
        self.level_intro = types.SimpleNamespace(handle_skip=lambda key=None: None)


class Tactical:
    def __init__(self):
        self.calls = []

    def hold_start(self, action, tower=None):
        self.calls.append({"action": action, "tower": None if tower is None else tower.team})


class Tower:
    def __init__(self, team):
        self.team = team


def _layout_fixture(font_factory):
    rows = []
    for touch in (True, False):
        for panel in (None, (1280, 0, 344, 720)):
            env = _source_namespace(SAFE_TOUCH if touch else SAFE_DESKTOP, panel)
            hud = env["TouchHUD"](font_factory)
            rows.append(
                {
                    "touch_mode": touch,
                    "panel": None if panel is None else list(panel),
                    "panel_present": panel is not None,
                    "buttons": {name: _button(btn) for name, btn in hud.buttons.items()},
                }
            )
    return rows


SYNC_CASES = [
    {"label": "playing_no_panel", "state": "game", "game": "playing", "cinematic": False,
     "panel": None, "level": 1},
    {"label": "playing_with_panel", "state": "game", "game": "playing", "cinematic": False,
     "panel": (1280, 0, 344, 720), "level": 1},
    {"label": "playing_cinematic", "state": "game", "game": "playing", "cinematic": True,
     "panel": None, "level": 1},
    {"label": "victory_first_level", "state": "game", "game": "victory", "cinematic": False,
     "panel": None, "level": 1},
    {"label": "victory_last_level", "state": "game", "game": "victory", "cinematic": False,
     "panel": (1280, 0, 344, 720), "level": 3},
    {"label": "defeat", "state": "game", "game": "defeat", "cinematic": False,
     "panel": None, "level": 1},
    {"label": "menu_state", "state": "menu", "game": "playing", "cinematic": False,
     "panel": None, "level": 1},
]


def _sync_fixture(font_factory):
    rows = []
    for spec in SYNC_CASES:
        env = _source_namespace(SAFE_DESKTOP, spec["panel"])
        hud = env["TouchHUD"](font_factory)
        game = Game(state=spec["game"], level=spec["level"])
        hud.buttons["pause"].press_anim = 1.0
        hud.sync(game, spec["state"], cinematic_active=spec["cinematic"])
        rows.append(
            {
                "label": spec["label"],
                "state": spec["state"],
                "game_state": spec["game"],
                "cinematic": spec["cinematic"],
                "panel_present": spec["panel"] is not None,
                "level": spec["level"],
                "visible": {name: bool(btn.visible) for name, btn in hud.buttons.items()},
                "press_anim": round(float(hud.buttons["pause"].press_anim), 6),
            }
        )
    return rows


HIT_CASES = [
    {"label": "pause_center", "state": "game", "panel": None, "pos": (60, 184)},
    {"label": "pause_tap_padding", "state": "game", "panel": None, "pos": (24, 150)},
    {"label": "debug_center", "state": "game", "panel": None, "pos": (132, 184)},
    {"label": "pause_on_dock_layout", "state": "game", "panel": (1280, 0, 344, 720),
     "pos": (60, 184)},
    {"label": "skip_hidden_while_playing", "state": "game", "panel": None,
     "pos": (1160, 665)},
    {"label": "skip_cinematic", "state": "game", "cinematic": True, "panel": None,
     "pos": (1160, 665)},
    {"label": "replay_victory", "state": "game", "game": "victory", "panel": None,
     "pos": (400, 640)},
    {"label": "next_level_victory", "state": "game", "game": "victory", "panel": None,
     "pos": (620, 640)},
    {"label": "next_level_on_last_level", "state": "game", "game": "victory", "panel": None,
     "level": 3, "pos": (620, 640)},
    {"label": "menu_victory", "state": "game", "game": "victory", "panel": None,
     "pos": (830, 640)},
    {"label": "replay_while_playing", "state": "game", "panel": None, "pos": (400, 640)},
    {"label": "back_never_shown_by_sync", "state": "menu", "panel": None, "pos": (80, 44)},
    {"label": "empty_map", "state": "game", "panel": None, "pos": (640, 300)},
]


def _hit_fixture(font_factory):
    rows = []
    for spec in HIT_CASES:
        env = _source_namespace(SAFE_DESKTOP, spec["panel"])
        hud = env["TouchHUD"](font_factory)
        game = Game(state=spec.get("game", "playing"), level=spec.get("level", 1))
        hud.sync(game, spec["state"], cinematic_active=bool(spec.get("cinematic", False)))
        action = hud.hit_test(tuple(spec["pos"]))
        pressed = sorted(
            name for name, btn in hud.buttons.items() if float(btn.press_anim) > 0.0
        )
        rows.append(
            {
                "label": spec["label"],
                "state": spec["state"],
                "game_state": spec.get("game", "playing"),
                "level": spec.get("level", 1),
                "cinematic": bool(spec.get("cinematic", False)),
                "panel_present": spec["panel"] is not None,
                "pos": list(spec["pos"]),
                "action": action,
                "pressed": pressed,
                "blocks": bool(hud.blocks(tuple(spec["pos"]))),
            }
        )
    return rows


ACTION_CASES = ["pause", "debug", "skip", "replay", "next_level", "menu", "back",
                "gather", "protect_tower", "attack_boss", "unknown"]


def _action_fixture(font_factory):
    rows = []
    for action in ACTION_CASES:
        for tower_team in (None, "blue", "red"):
            env = _source_namespace(SAFE_DESKTOP, None)
            game = Game(tower=Tower(tower_team) if tower_team else None)
            debug = types.SimpleNamespace(toggled=0)

            def toggle(debug=debug):
                debug.toggled += 1

            debug.toggle = toggle
            ctx = {"game": game, "menu": types.SimpleNamespace(
                handle_key=lambda key: ctx.setdefault("menu_key", key)), "debug": debug}
            handled = bool(env["apply_hud_action"](action, ctx))
            rows.append(
                {
                    "action": action,
                    "tower": tower_team,
                    "handled": handled,
                    "request_pause": bool(ctx.get("request_pause", False)),
                    "debug_toggles": int(debug.toggled),
                    "debug_toggled": int(debug.toggled),
                    "replay": bool(game.replay_requested),
                    "next_level": bool(game.next_level_requested),
                    "menu": bool(game.return_to_menu_requested),
                    "menu_key": ctx.get("menu_key"),
                    "tactical": list(game.tactical.calls),
                }
            )
    return rows


def source_fixture():
    # `TouchHUD.sync` does `from levels import get_next_level`; install the stub
    # only while the fixture is built so no other oracle sees it.
    previous = sys.modules.get("levels")
    sys.modules["levels"] = types.SimpleNamespace(
        get_next_level=lambda number: (number + 1) if number < 3 else None
    )
    try:
        return _build_fixture()
    finally:
        if previous is None:
            sys.modules.pop("levels", None)
        else:
            sys.modules["levels"] = previous


def _build_fixture():
    def font_factory(size, style="body"):
        return types.SimpleNamespace(size=size, style=style)

    return {
        "source": "mobile/hud.py",
        "min_tap": 80,
        "press_decay": 0.12,
        "logical_width": LOGICAL_W,
        "logical_height": LOGICAL_H,
        "layout": _layout_fixture(font_factory),
        "sync": _sync_fixture(font_factory),
        "hits": _hit_fixture(font_factory),
        "actions": _action_fixture(font_factory),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {FIXTURE}")
        return
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit("FAIL: touch HUD source fixture drift")
    buttons = sum(len(row["buttons"]) for row in actual["layout"])
    print(
        "PASS: touch HUD — %d layouts (%d buttons), %d states, %d hits, %d actions"
        % (len(actual["layout"]), buttons, len(actual["sync"]), len(actual["hits"]),
           len(actual["actions"]))
    )


if __name__ == "__main__":
    main()
