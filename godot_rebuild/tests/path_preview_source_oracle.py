"""Source oracle for the PathPreview port.

`import _render` fails today with a pre-existing circular import and the Python
sources are read-only, so this oracle extracts `class PathPreview` from
`_render.py` and executes it verbatim.

The presentation maths lives inside `draw()`: the fade in / hold / fade out
alpha curve, the moving dash offset, and the per-arrow pulse that picks a size
and an alpha. Re-implementing those here would make the fixture a copy of my
own guess, so `draw()` is run against a tiny pygame shim and `sys.settrace`
reads the real locals off the frame at two fixed lines. No third-party package
is needed: CI has no pygame.

Not captured (and therefore not ported): the arrow triangle points. They are
pygame-surface geometry — offsets around the centre of a 20x20 blit surface —
so a Godot renderer would re-centre them anyway. The captured data is the
state machine plus the timing/colour decisions the renderer needs.

Run: python godot_rebuild/tests/path_preview_source_oracle.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "path_preview_source.json"

TAG = "_render.py:PathPreview"

TOTAL_STEPS = 130
# Straight lane: five arrows (range(0, len - 1, 8) over 40 points).
LANE_PATH = [[index * 10, 100] for index in range(40)]
# Exercises the `len(lane_path) < 2` early-continue.
STUB_PATH = [[0, 0]]
PATHS = [LANE_PATH, STUB_PATH]

# Timer values chosen to sit on each side of the fade in / hold / fade out
# boundaries (fade in above 100, hold 40..100, fade out below 40).
SAMPLE_TIMERS = [119, 110, 101, 100, 60, 41, 40, 20, 1]
SAMPLE_TIMES = [0.0, 2.5, 7.0, 13.7]


class _SurfaceShim:
    def __init__(self, *args, **kwargs):
        pass

    def blit(self, *args, **kwargs):
        pass


class _DrawShim:
    @staticmethod
    def polygon(*args, **kwargs):
        pass


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    draw = _DrawShim


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class PathPreview:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {"math": math, "pygame": _PygameShim}
    exec(compile(block, TAG, "exec"), namespace)
    return namespace, block


def _capture_lines(block):
    """Line numbers (1-based, relative to the compiled block) to read locals on."""
    found = {}
    for index, line in enumerate(block.splitlines()):
        stripped = line.strip()
        if stripped.startswith("for lane_path in self.paths:"):
            found["alpha"] = index + 1
        elif stripped.startswith("pygame.draw.polygon("):
            found["arrow"] = index + 1
    missing = {"alpha", "arrow"} - set(found)
    assert not missing, "PathPreview.draw() capture lines missing: %s" % sorted(missing)
    return found


def _trace_draw(item, lines, animation_time):
    """Run draw() and read alpha / offset / per-arrow pulse off the real frame."""
    captured = {"alpha": [], "arrow": []}

    def tracer(frame, event, arg):
        if event == "call":
            return tracer if frame.f_code.co_filename == TAG else None
        if event == "line" and frame.f_code.co_filename == TAG:
            local = frame.f_locals
            if frame.f_lineno == lines["alpha"]:
                captured["alpha"].append([local["alpha"], local["offset"]])
            elif frame.f_lineno == lines["arrow"]:
                captured["arrow"].append(
                    [local["pulse_i"], local["arrow_size"], local["arrow_color"][3]]
                )
        return tracer

    sys.settrace(tracer)
    try:
        item.draw(_SurfaceShim(), animation_time)
    finally:
        sys.settrace(None)
    return captured


def source_fixture():
    namespace, block = _load_class()
    cls = namespace["PathPreview"]
    lines = _capture_lines(block)

    preview = cls()
    preview.show(PATHS)

    steps = []
    for _ in range(TOTAL_STEPS):
        preview.update()
        if not preview.active:
            steps.append([0, preview.timer, None])
            continue
        captured = _trace_draw(preview, lines, 0.0)
        steps.append([1, preview.timer, captured["alpha"][0][0]])

    samples = []
    for timer in SAMPLE_TIMERS:
        preview.active = True
        preview.paths = PATHS
        preview.timer = timer
        for animation_time in SAMPLE_TIMES:
            captured = _trace_draw(preview, lines, animation_time)
            if not captured["alpha"]:
                samples.append(
                    {"timer": timer, "animation_time": animation_time, "alpha": None, "arrows": []}
                )
                continue
            samples.append(
                {
                    "timer": timer,
                    "animation_time": animation_time,
                    "alpha": captured["alpha"][0][0],
                    "dash_offset": captured["alpha"][0][1],
                    "arrows": captured["arrow"],
                }
            )

    # Which points along the lane each captured arrow was drawn at, so the
    # native suite can replay pulse_index without hard-coding the stride.
    point_indices = list(range(0, len(LANE_PATH) - 1, 8))

    return {
        "source": "_render.py::PathPreview",
        "duration": preview.duration,
        "point_indices": point_indices,
        "steps": steps,
        "samples": samples,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    live = [step for step in fixture["steps"] if step[2] is not None]
    print("path_preview: %d steps, %d live, duration %d"
          % (len(fixture["steps"]), len(live), fixture["duration"]))
    print("  first live: %s" % (live[0],))
    print("  last live:  %s" % (live[-1],))
    print("  samples: %d" % len(fixture["samples"]))
    for sample in fixture["samples"]:
        if sample["alpha"] is None or sample["animation_time"] != SAMPLE_TIMES[0]:
            continue
        print(
            "    timer %3d -> alpha %3s dash %s arrows %s"
            % (
                sample["timer"],
                sample["alpha"],
                sample.get("dash_offset"),
                sample["arrows"],
            )
        )
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
