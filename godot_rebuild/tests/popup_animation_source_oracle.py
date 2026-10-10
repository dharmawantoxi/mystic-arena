"""Source oracle for the PopupAnimation port.

`import _render` fails today with a pre-existing circular import and the
Python sources are read-only, so this oracle extracts the source block from
`class PopupAnimation:` up to the next top-level class and executes it
verbatim. That block also defines the module-level easing helpers the class
calls (`_ease_out_back`), so `get_scale()` runs the real source easing.

The class touches no pygame and no RNG, so this oracle needs no third-party
package at all.

Run: python godot_rebuild/tests/popup_animation_source_oracle.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "popup_animation_source.json"

SHOW_STEPS = 40
HIDE_STEPS = 70


def _load_block():
    """Execute the real PopupAnimation block plus its easing helpers."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class PopupAnimation:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {"math": math}
    exec(compile(block, "_render.py:PopupAnimation", "exec"), namespace)
    return namespace


def _trace(item, count):
    steps = []
    for _ in range(count):
        item.update()
        steps.append([
            round(item.progress, 8),
            round(item.get_scale(), 8),
            item.get_offset_y(),
        ])
    return steps


def source_fixture():
    namespace = _load_block()
    cls = namespace["PopupAnimation"]

    opening = cls()
    opening.show()
    shown = _trace(opening, SHOW_STEPS)

    closing = cls()
    closing.show()
    _trace(closing, SHOW_STEPS)
    closing.hide()
    hidden = _trace(closing, HIDE_STEPS)

    # `warmup` lets the native suite replay the same starting state without
    # hard-coding how many ticks the oracle spent settling.
    return {
        "source": "_render.py::PopupAnimation",
        "speed": opening.speed,
        "cases": [
            {"name": "show_and_settle", "action": "show", "warmup": 0, "steps": shown},
            {
                "name": "hide_from_settled",
                "action": "hide",
                "warmup": SHOW_STEPS,
                "steps": hidden,
            },
        ],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    sys.exit(main())
