"""Source oracle for the WaveAnnouncer port.

`import _render` fails today with a pre-existing circular import and the Python
sources are read-only, so this oracle extracts two blocks verbatim from
`_render.py` and executes them:

* the module-level easing helpers (`_ease_out_back` / `_ease_in_back`) that the
  banner's slide phases call, and
* `class WaveAnnouncer` itself.

Unlike the earlier effect slices, the interesting maths here lives inside
`draw()`: the three phase boundaries (0.2 / 0.7), the eased `x_offset` and the
`alpha` ramp. Re-implementing those in this file would make the fixture a copy
of my own guess, so instead `draw()` is run against a tiny pygame/theme shim and
`sys.settrace` reads the real `x_offset` / `alpha` locals off the frame at the
`cx = screen_w // 2 + x_offset` line. The pygame shim means no third-party
package is needed: CI has no pygame.

Run: python godot_rebuild/tests/wave_announcer_source_oracle.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "wave_announcer_source.json"

TAG = "_render.py:WaveAnnouncer"
EASING_TAG = "_render.py:easings"

SCREEN_W = 1280
SCREEN_H = 720
WAVE_NUM = 7
TOTAL_STEPS = 130


# --------------------------------------------------------------------------
# Minimal shims: the banner only blits/rects past the point we capture, but
# draw() still has to run to completion without a real pygame or font stack.
# --------------------------------------------------------------------------
class _RectShim:
    # draw() builds one of these as pygame.Rect(x, y, w, h) for the corner
    # ticks; the attributes are what the blits read afterwards.
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


class _DrawShim:
    @staticmethod
    def rect(*args, **kwargs):
        pass

    @staticmethod
    def line(*args, **kwargs):
        pass


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    Rect = _RectShim
    draw = _DrawShim


def _slice(lines, start_pred, end_pred):
    start = next(i for i, line in enumerate(lines) if start_pred(line))
    end = next(i for i, line in enumerate(lines) if i > start and end_pred(line))
    return "\n".join(lines[start:end]), start


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()

    easing_block, _ = _slice(
        lines,
        lambda line: line.startswith("def _ease_out_back("),
        lambda line: line.startswith("class "),
    )
    class_block, _ = _slice(
        lines,
        lambda line: line.startswith("class WaveAnnouncer:"),
        lambda line: line.startswith("class "),
    )

    namespace = {
        "math": math,
        "pygame": _PygameShim,
        "ui_theme": _ThemeShim(),
        "title_font": _FontShim,
        "get_font": _FontShim,
    }
    exec(compile(easing_block, EASING_TAG, "exec"), namespace)
    exec(compile(class_block, TAG, "exec"), namespace)
    return namespace, class_block


def _capture_line(class_block):
    """Line number (1-based, relative to the compiled block) to read locals on."""
    for index, line in enumerate(class_block.splitlines()):
        if line.strip().startswith("cx = screen_w // 2 + x_offset"):
            return index + 1
    raise AssertionError("WaveAnnouncer.draw() capture line not found")


def _trace_draw(item, line):
    """Run draw() and read (progress, x_offset, alpha) off the real frame."""
    captured = []

    def tracer(frame, event, arg):
        if event == "call":
            return tracer if frame.f_code.co_filename == TAG else None
        if (
            event == "line"
            and frame.f_code.co_filename == TAG
            and frame.f_lineno == line
        ):
            local = frame.f_locals
            captured.append(
                [local["progress"], local["x_offset"], local["alpha"]]
            )
        return tracer

    sys.settrace(tracer)
    try:
        item.draw(_SurfaceShim(), SCREEN_W, SCREEN_H)
    finally:
        sys.settrace(None)
    return captured[0] if captured else None


def source_fixture():
    namespace, class_block = _load_class()
    cls = namespace["WaveAnnouncer"]
    line = _capture_line(class_block)

    banner = cls()
    banner.announce(WAVE_NUM)

    steps = []
    for _ in range(TOTAL_STEPS):
        banner.update()
        if not banner.active:
            steps.append([0, banner.timer, None])
            continue
        progress, offset_x, alpha = _trace_draw(banner, line)
        steps.append([1, banner.timer, [round(progress, 8), offset_x, alpha]])

    return {
        "source": "_render.py::WaveAnnouncer",
        "duration": banner.duration,
        "wave_num": WAVE_NUM,
        "screen_w": SCREEN_W,
        "steps": steps,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    live = [step for step in fixture["steps"] if step[2] is not None]
    print("wave_announcer: %d steps, %d live, duration %d"
          % (len(fixture["steps"]), len(live), fixture["duration"]))
    print("  first live: %s" % (live[0],))
    print("  last live:  %s" % (live[-1],))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
