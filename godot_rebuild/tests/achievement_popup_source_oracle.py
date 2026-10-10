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
class _RectShim:
    x = 0
    y = 0

    def __init__(self, *args, **kwargs):
        pass


class _SurfaceShim:
    def __init__(self, *args, **kwargs):
        pass

    def set_alpha(self, *args, **kwargs):
        pass

    def get_rect(self, **kwargs):
        return _RectShim()

    def blit(self, *args, **kwargs):
        pass


class _FontShim:
    def __init__(self, *args, **kwargs):
        pass

    def render(self, *args, **kwargs):
        return _SurfaceShim()


class _ThemeShim:
    def corner_ticks(self, *args, **kwargs):
        pass

    def gradient_text(self, *args, **kwargs):
        return _SurfaceShim()

    def letter(self, text):
        return text

    def fit_ellipsis(self, font, text, max_w):
        return text


class _DrawShim:
    @staticmethod
    def rect(*args, **kwargs):
        pass

    @staticmethod
    def line(*args, **kwargs):
        pass

    @staticmethod
    def circle(*args, **kwargs):
        pass

    @staticmethod
    def polygon(*args, **kwargs):
        pass


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    Rect = _RectShim
    draw = _DrawShim


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

    return {
        "source": "_render.py::AchievementPopup",
        "duration": popup.duration,
        "unlocks": [list(entry) for entry in UNLOCKS],
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
