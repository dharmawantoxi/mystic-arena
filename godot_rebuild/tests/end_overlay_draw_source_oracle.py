"""Source oracle for the victory / defeat overlay (layer 9bv5).

`Game.draw` paints `ui.draw_overlay(screen, title, color, subtitle, action)` once the match is
won (`VICTORY! LV.n`, GOLD) or lost (`DEFEAT LV.n`, RED), after the popups and before the
input hint bar. `ui_components/_bundle.py::Overlay.draw` (cheap-alpha branch) stacks:
  * the cached backdrop: one (10, 10, 20, a) line per row, a = int(180 * (1 - |i - 360| /
    360 * 0.3));
  * `_draw_rays`: 12 (color, 30) triangles from the centre, t = animation_time * 0.05;
  * `_draw_central_glow`: circles r = 200..60 step -20, alpha int((200 - r) / 200 * 60);
  * `_draw_title`: `_radial(760, 190)` glow and the Cinzel `outline_text` (3 px outline,
    gold or red body gradient), size int(round(88 * pulse / 4) * 4);
  * `_draw_sparkles` (victory only), `_draw_stats` (shadow, gradient panel, 2 px border,
    corner ticks, five rows, NEW BEST badges), the level unlock popup (victory, recorded here
    as one `unlock_popup` marker), `_draw_action_hint` (keycap chips parsed from `[KEY] Desc`)
    and `_draw_achievements` (trophy icon + count).
The REAL `draw` and helpers (harvested from `Overlay`), `ui_theme.draw_icon` and
`ui_theme.corner_ticks` run under the recording pygame shim of `draw_recorder.py` (fake
`0.55 * size` glyphs). `cached_render`, `_radial`, `_shadow`, `_vgrad` and `outline_text` are
recorded as one op each. Every helper call is preceded by a `section` op.
Run: python godot_rebuild/tests/end_overlay_draw_source_oracle.py
"""
import ast
import json
import math
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "ui_components" / "_bundle.py"
CORE = ROOT / "_core.py"
UI_THEME = ROOT / "ui_theme.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "end_overlay_draw_source.json"
SECTIONS = ("_draw_rays", "_draw_central_glow", "_draw_title", "_draw_sparkles", "_draw_stats",
            "_draw_level_unlock_popup", "_draw_action_hint", "_draw_achievements")
HARVESTED = ("draw", "_update_unlock_popup") + SECTIONS
NOW = 1_700_000_000.0
# (label, victory, level, action, animation_time, get_ticks, stats, achievements)
# stats = (score, match seconds, waves, kills, combo, new best score, new best time)
FRAMES = [
    ("victory_next", True, 3, "[N] Next Level  [R] Replay  [ESC] Menu", 600, 1000,
     (12345, 125, 7, 88, 12, True, False), 2),
    ("victory_last_level", True, 30, "[R] Replay  [ESC] Menu  (You cleared all levels!)", 1234,
     2500, (987654, 3599, 30, 1500, 45, True, True), 0),
    ("defeat", False, 5, "[R] Retry  [ESC] Menu", 77, 4321, (420, 61, 4, 19, 3, False, False),
     1),
    ("victory_controller", True, 1, "[RB] Next Level  [X] Replay  [VIEW] Menu", 0, 0,
     (0, 0, 1, 0, 0, False, False), 0),
]


def _constant(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, path.name))


def _overlay_class(namespace):
    text = BUNDLE.read_text(encoding="utf-8")
    owner = next((n for n in ast.walk(ast.parse(text))
                  if isinstance(n, ast.ClassDef) and n.name == "Overlay"), None)
    if owner is None:
        raise AssertionError("Overlay not found in %s" % BUNDLE.name)
    found = {n.name: n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name in HARVESTED}
    missing = set(HARVESTED) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.Overlay" % (sorted(missing), BUNDLE.name))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in HARVESTED)
    exec(compile("class Overlay:\n%s" % body, BUNDLE.name, "exec"), namespace)
    cls = namespace["Overlay"]
    for name in SECTIONS:
        original = getattr(cls, name)

        def wrapped(self, surface, *args, _original=original, _name=name):
            surface.ops.append({"kind": "section", "name": _name})
            if _name == "_draw_level_unlock_popup":
                surface.ops.append({"kind": "unlock_popup"})
                return None
            return _original(self, surface, *args)

        setattr(cls, name, wrapped)
    return cls


def _surface_with(op, w, h):
    surface = rec.Surface((w, h))
    surface.ops.append(op)
    return surface


def _ui_theme(pygame):
    module = types.ModuleType("ui_theme")
    module.pygame = pygame
    module.GOLD_BRIGHT = _constant(UI_THEME, "GOLD_BRIGHT")
    module.cheap_alpha = lambda: True

    def radial(w, h, color, alpha):
        a = max(4, min(120, int(alpha) // 8 * 8))
        return _surface_with({"kind": "radial", "rect": [0, 0, int(w), int(h)],
                              "color": list(color), "alpha": a, "mult": 255}, w, h)

    def shadow(w, h, radius=12, alpha=110, spread=4):
        sw, sh = int(w) + spread * 2, int(h) + spread * 2
        return _surface_with({"kind": "shadow", "rect": [0, 0, sw, sh], "radius": int(radius),
                              "alpha": int(alpha), "mult": 255}, sw, sh)

    def vgrad(w, h, top, bottom, radius=0):
        return _surface_with({"kind": "vgrad", "rect": [0, 0, int(w), int(h)], "top": list(top),
                              "bottom": list(bottom), "radius": int(radius), "mult": 255}, w, h)

    def outline_text(screen, font, text, color, center, outline=(8, 9, 18), width=2,
                     body_top=None, body_bottom=None):
        w, h = font.size(text)
        x, y = int(center[0]) - w // 2, int(center[1]) - h // 2
        screen.ops.append({"kind": "outline_text", "text": text, "size": font.font_size,
                           "style": font.style, "pos": [x, y], "outline": list(outline),
                           "width": int(width), "top": list(body_top),
                           "bottom": list(body_bottom), "mult": 255})
        return rec.Rect(x, y, w, h)

    module._radial, module._shadow, module._vgrad = radial, shadow, vgrad
    module.outline_text = outline_text
    for segment in rec.harvest(UI_THEME, ["draw_icon", "corner_ticks"]):
        exec(compile(segment, UI_THEME.name, "exec"), module.__dict__)
    return module


def _perf():
    module = types.ModuleType("mobile.perf")
    module.Quality = SimpleNamespace(cheap_alpha=True)
    module.POOL = SimpleNamespace(get=lambda w, h: rec.Surface((w, h)), release=lambda s: None)

    def cached_render(_key, w, h, paint):
        lines = rec.Surface((w, h))
        paint(lines)
        rows = [op["color"][3] for op in lines.ops]
        if [op["a"][1] for op in lines.ops] != list(range(h)):
            raise AssertionError("end gradient must paint one line per row")
        return _surface_with({"kind": "end_gradient", "rect": [0, 0, w, h],
                              "color": list(lines.ops[0]["color"][:3]), "rows": rows,
                              "mult": 255}, w, h)

    module.cached_render = cached_render
    module.darken = lambda surface, amount: None
    return module


def source_fixture():
    clock = {"ticks": 0}
    pygame = rec.make_pygame(clock)
    gold, red = _constant(CORE, "GOLD"), _constant(CORE, "RED")
    fake_time = types.ModuleType("time")
    fake_time.time = lambda: NOW
    mobile = types.ModuleType("mobile")
    perf = _perf()
    mobile.perf = perf
    frames = []
    with rec.installed({"pygame": pygame, "mobile": mobile, "mobile.perf": perf}):
        namespace = {"pygame": pygame, "math": math, "ui_theme": _ui_theme(pygame),
                     "SCREEN_WIDTH": _constant(CORE, "SCREEN_WIDTH"),
                     "SCREEN_HEIGHT": _constant(CORE, "SCREEN_HEIGHT"),
                     "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
                     "title_font": lambda size, bold=True: rec.Font(
                         max(8, min(int(size), 220)), "title")}
        cls = _overlay_class(namespace)
        for label, victory, level, action, anim, ticks, stats, achievements in FRAMES:
            clock["ticks"] = ticks
            score, seconds, waves, kills, combo, best_score, best_time = stats
            overlay = cls.__new__(cls)
            overlay.unlock_popup_delay, overlay.unlock_popup_timer = 90, 0
            overlay.game = SimpleNamespace(
                animation_time=anim, score=score, match_start_time=NOW - seconds,
                wave_number=waves, total_kills=kills, max_combo=combo,
                new_best_score=best_score, new_best_time=best_time,
                achievements_unlocked=["a%d" % i for i in range(achievements)])
            title = ("VICTORY! LV.%d" if victory else "DEFEAT LV.%d") % level
            screen = rec.Surface((1280, 720))
            with rec.installed({"time": fake_time}):
                overlay.draw(screen, title, gold if victory else red, "", action)
            frames.append({"label": label, "title": title, "action": action,
                           "animation_time": anim, "ticks": ticks, "stats": list(stats),
                           "achievements": achievements, "ops": screen.ops})
    return {
        "source": "ui_components/_bundle.py::Overlay.draw (cheap-alpha branch)",
        "glyph_factor": rec.GLYPH_FACTOR,
        "colors": {"victory": list(gold), "defeat": list(red)},
        "frames": frames,
    }


def main():
    data = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ops = sum(len(frame["ops"]) for frame in data["frames"])
    print("end overlay oracle: %d frames, %d ops -> %s" % (len(data["frames"]), ops, FIXTURE.name))


if __name__ == "__main__":
    main()
