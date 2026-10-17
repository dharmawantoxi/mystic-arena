"""Source oracle for the AchievementPopup port.

`import _render` fails today with a pre-existing circular import and the Python
sources are read-only, so this oracle extracts two blocks verbatim from
`_render.py` and executes them:

* the module-level easing helper (`_ease_out_back`) the slide-in phase calls,
* `class AchievementPopup` itself.

As with the wave banner, the presentation maths lives inside `draw()`: the
0.15 / 0.85 phase boundaries, the eased `x_offset`, the `alpha` ramp and the
short-lived `glow_alpha`. Rather than re-implement that here (which would make
the fixture a copy of my own guess), `draw()` is run against a minimal
pygame/theme shim and `sys.settrace` reads the real `x_offset` / `alpha` /
`glow_alpha` locals off the frame at fixed lines. The shim means no
third-party package is needed: CI has no pygame.

Run: python godot_rebuild/tests/achievement_popup_source_oracle.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "achievement_popup_source.json"

TAG = "_render.py:AchievementPopup"
EASING_TAG = "_render.py:easings"

SCREEN_W = 1280
SCREEN_H = 720
# Four popups of 180 ticks each; run past the end so the queue drains and
# the idle branch is exercised too.
TOTAL_STEPS = 760

# Unlocks scripted across the run: the second and third land while a popup is
# already on screen (so the queue builds up behind it), the fourth lands after
# the queue has started draining.
UNLOCKS = [
    (0, "First Blood", "Kill your first enemy", "star"),
    (10, "Sharpshooter", "Land 100 hits", "sword"),
    (20, "Untouchable", "Win a match without dying", "shield"),
    (190, "Champion", "Win the match", "gold"),
]


# --------------------------------------------------------------------------
# Minimal shims so draw() runs to completion without pygame or a font stack.
# --------------------------------------------------------------------------
_RECORD_DRAW = False


class _RectShim:
    def __init__(self, *args, **kwargs):
        values = args[0] if args and isinstance(args[0], (list, tuple)) else args
        self.x = int(values[0]) if len(values) >= 1 else 0
        self.y = int(values[1]) if len(values) >= 2 else 0
        self.width = int(values[2]) if len(values) >= 4 else 0
        self.height = int(values[3]) if len(values) >= 4 else 0
        self.center = kwargs.get("center", (self.x + self.width // 2, self.y + self.height // 2))
        self.right = self.x + self.width
        self.bottom = self.y + self.height


class _SurfaceShim:
    def __init__(self, *args, **kwargs):
        self.size = args[0] if args and isinstance(args[0], (list, tuple)) else (0, 0)
        self.width = int(self.size[0]) if len(self.size) >= 2 else 0
        self.height = int(self.size[1]) if len(self.size) >= 2 else 0
        self.ops = []
        self.text = None
        self.font_size = 0
        self.style = ""
        self.color = None
        self.alpha = 255
        self.record = bool(kwargs.get("record", _RECORD_DRAW))

    def set_alpha(self, alpha, *args, **kwargs):
        self.alpha = alpha

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rect(self, **kwargs):
        return _RectShim((0, 0, self.width, self.height), center=kwargs.get("center", (0, 0)))

    def blit(self, source, dest, *args, **kwargs):
        if isinstance(dest, _RectShim):
            dx, dy = dest.x, dest.y
            center = [dest.center[0], dest.center[1]]
            use_center = True
        elif isinstance(dest, (list, tuple)):
            dx, dy = dest[0], dest[1]
            center = None
            use_center = False
        else:
            dx, dy, center, use_center = 0, 0, None, False
        if not self.record:
            return
        for operation in source.ops:
            shifted = dict(operation)
            kind = shifted["type"]
            if kind == "circle":
                shifted["center"] = [shifted["center"][0] + dx, shifted["center"][1] + dy]
            elif kind == "rect":
                bounds = shifted["rect"]
                shifted["rect"] = [bounds[0] + dx, bounds[1] + dy, bounds[2], bounds[3]]
            elif kind == "polygon":
                shifted["points"] = [[point[0] + dx, point[1] + dy] for point in shifted["points"]]
            elif kind == "line":
                shifted["points"] = [[point[0] + dx, point[1] + dy] for point in shifted["points"]]
            elif kind == "text":
                key = "center" if "center" in shifted else "position"
                shifted[key] = [shifted[key][0] + dx, shifted[key][1] + dy]
            self.ops.append(shifted)
        if source.text is not None:
            operation = {
                "type": "text", "text": source.text, "size": source.font_size,
                "color": _rgba(source.color),
            }
            if use_center:
                operation["center"] = center
            else:
                operation["position"] = [dx, dy]
                operation["alpha"] = source.alpha
                operation["style"] = source.style
            self.ops.append(operation)



class _FontShim:
    def __init__(self, size=0, style="body_semibold", *args, **kwargs):
        self.font_size = size
        self.style = style

    def size_text(self, text):
        return (int(len(text) * self.font_size * 0.55), self.font_size)

    def size(self, text):
        return self.size_text(text)

    def render(self, text, antialias=True, color=None, *args, **kwargs):
        width, height = self.size_text(text)
        surface = _SurfaceShim((width, height))
        surface.text = text
        surface.font_size = self.font_size
        surface.style = self.style
        surface.color = color
        return surface


class _ThemeShim:
    def corner_ticks(self, surface, rect, color, length=11, width=2, inset=2):
        anchors = [
            (rect.x + inset, rect.y + inset, 1, 1),
            (rect.right - inset, rect.y + inset, -1, 1),
            (rect.x + inset, rect.bottom - inset, 1, -1),
            (rect.right - inset, rect.bottom - inset, -1, -1),
        ]
        if surface.record:
            for x, y, dx, dy in anchors:
                surface.ops.append({
                    "type": "line", "points": [[x, y], [x + dx * length, y]],
                    "color": _rgba(color), "width": width,
                })
                surface.ops.append({
                    "type": "line", "points": [[x, y], [x, y + dy * length]],
                    "color": _rgba(color), "width": width,
                })

    def gradient_text(self, *args, **kwargs):
        return _SurfaceShim()

    def letter(self, text):
        return " ".join(list(text))

    def fit_ellipsis(self, font, text, max_w):
        if font.size(text)[0] <= max_w:
            return text
        suffix = "…"
        while len(text) > 1:
            candidate = text[:-1]
            if font.size(candidate + suffix)[0] <= max_w:
                return candidate + suffix
            text = candidate
        return suffix


class _DrawShim:
    @staticmethod
    def rect(surface, color, rect, width=0, *args, **kwargs):
        if not surface.record:
            return
        values = list(rect)
        surface.ops.append({
            "type": "rect", "rect": [values[0], values[1], values[2], values[3]],
            "color": _rgba(color), "width": width,
            "radius": kwargs.get("border_radius", 0),
        })

    @staticmethod
    def line(surface, color, start, end, width=1, *args, **kwargs):
        if not surface.record:
            return
        surface.ops.append({
            "type": "line", "points": [list(start), list(end)],
            "color": _rgba(color), "width": width,
        })

    @staticmethod
    def circle(surface, color, center, radius, width=0, *args, **kwargs):
        if not surface.record:
            return
        surface.ops.append({
            "type": "circle", "center": list(center), "radius": radius,
            "color": _rgba(color), "width": width,
        })

    @staticmethod
    def polygon(surface, color, points, width=0, *args, **kwargs):
        if not surface.record:
            return
        surface.ops.append({
            "type": "polygon", "points": [list(point) for point in points],
            "color": _rgba(color), "width": width,
        })


def _rgba(color):
    if color is None:
        return [255, 255, 255, 255]
    values = list(color)
    return values if len(values) == 4 else values + [255]


class _ImageShim:
    @staticmethod
    def tobytes(surface, pixel_format):
        # Barlow has a real ellipsis glyph; the sentinel is intentionally absent.
        if surface.text == "￀":
            return b"missing-glyph"
        if surface.text == "…":
            return b"rendered-ellipsis-glyph"
        return str(surface.text).encode("utf-8")


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    Rect = _RectShim
    draw = _DrawShim
    image = _ImageShim


def _slice(lines, start_pred, end_pred):
    start = next(i for i, line in enumerate(lines) if start_pred(line))
    end = next(i for i, line in enumerate(lines) if i > start and end_pred(line))
    return "\n".join(lines[start:end])


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()

    easing_block = _slice(
        lines,
        lambda line: line.startswith("def _ease_out_back("),
        lambda line: line.startswith("class "),
    )
    # The class is followed by a "# Boss Death Animation" banner that re-imports
    # pygame at module level (line 1581); stop before it so the block stays a
    # single class and never imports pygame for real.
    class_block = _slice(
        lines,
        lambda line: line.startswith("class AchievementPopup:"),
        lambda line: line.startswith("import "),
    )

    namespace = {
        "math": math,
        "pygame": _PygameShim,
        "ui_theme": _ThemeShim(),
        "get_font": _FontShim,
    }
    exec(compile(easing_block, EASING_TAG, "exec"), namespace)
    exec(compile(class_block, TAG, "exec"), namespace)
    return namespace, class_block


def _capture_lines(block):
    """Line numbers (1-based, relative to the compiled block) to read locals on."""
    found = {}
    for index, line in enumerate(block.splitlines()):
        stripped = line.strip()
        if stripped.startswith("panel_x = screen_w - panel_w - 20 + x_offset"):
            found["curve"] = index + 1
        elif stripped.startswith("glow_surf = pygame.Surface("):
            found["glow"] = index + 1
    missing = {"curve", "glow"} - set(found)
    assert not missing, "AchievementPopup.draw() capture lines missing: %s" % sorted(missing)
    return found


def _trace_draw(item, lines):
    """Run draw() and read (progress, x_offset, alpha, glow_alpha) off the frame."""
    captured = {"curve": [], "glow": []}

    def tracer(frame, event, arg):
        if event == "call":
            return tracer if frame.f_code.co_filename == TAG else None
        if event == "line" and frame.f_code.co_filename == TAG:
            local = frame.f_locals
            if frame.f_lineno == lines["curve"]:
                captured["curve"].append([local["progress"], local["x_offset"], local["alpha"]])
            elif frame.f_lineno == lines["glow"]:
                captured["glow"].append(local["glow_alpha"])
        return tracer

    sys.settrace(tracer)
    try:
        item.draw(_SurfaceShim(), SCREEN_W, SCREEN_H)
    finally:
        sys.settrace(None)
    return captured


def _capture_panel_visual(cls, timer, title="Champion", description="Victory earned"):
    global _RECORD_DRAW
    popup = cls()
    popup.current = {"title": title, "description": description, "icon_type": "gold"}
    popup.timer = timer
    _RECORD_DRAW = True
    try:
        surface = _SurfaceShim((1280, 720), record=True)
        popup.draw(surface, SCREEN_W, SCREEN_H)
    finally:
        _RECORD_DRAW = False
    return {"timer": timer, "ops": surface.ops}


def source_fixture():
    namespace, class_block = _load_class()
    cls = namespace["AchievementPopup"]
    lines = _capture_lines(class_block)

    popup = cls()
    by_tick = {}
    for tick, title, description, icon in UNLOCKS:
        by_tick[tick] = (title, description, icon)

    steps = []
    for index in range(TOTAL_STEPS):
        if index in by_tick:
            title, description, icon = by_tick[index]
            popup.unlock(title, description, icon)
        popup.update()
        if not popup.current:
            steps.append([0, popup.timer, len(popup.queue), None, None])
            continue
        captured = _trace_draw(popup, lines)
        curve = captured["curve"][0]
        glow = captured["glow"][0] if captured["glow"] else None
        steps.append(
            [
                1,
                popup.timer,
                len(popup.queue),
                [round(curve[0], 8), curve[1], curve[2], glow],
                popup.current["title"],
            ]
        )

    global _RECORD_DRAW
    icons = {}
    _RECORD_DRAW = True
    try:
        for icon_type in ["star", "sword", "skull", "shield", "gold", "unknown"]:
            surface = _SurfaceShim((280, 60), record=True)
            popup._draw_icon(surface, 15, 30, icon_type, 117)
            icons[icon_type] = surface.ops
    finally:
        _RECORD_DRAW = False
    panel_visuals = [
        _capture_panel_visual(cls, 160),
        _capture_panel_visual(cls, 126),
        _capture_panel_visual(
            cls, 126, "Champion of the Eternal Mystic Arena",
            "A legendary victory awarded for mastering the ancient battlefield",
        ),
    ]

    return {
        "source": "_render.py::AchievementPopup",
        "duration": popup.duration,
        "unlocks": [list(entry) for entry in UNLOCKS],
        "icons": icons,
        "panel_visuals": panel_visuals,
        "steps": steps,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    live = [step for step in fixture["steps"] if step[3] is not None]
    glowing = [step for step in live if step[3][3] is not None]
    print("achievement_popup: %d steps, %d showing, %d glowing"
          % (len(fixture["steps"]), len(live), len(glowing)))
    print("  first: %s" % (live[0],))
    print("  queue peaks at %d" % max(step[2] for step in fixture["steps"]))
    print("  glow last: %s" % (glowing[-1],))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
