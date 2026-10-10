"""Source oracle for the ComboCounter port.

`import _render` fails today with a pre-existing circular import and the
Python sources are read-only, so this oracle extracts the real
`class ComboCounter` block from `_render.py` and executes it verbatim.

`add_kill()` tries to notify a Python-only side panel
(`from mobile import sidepanel`) inside a try/except. In the oracle that
import simply fails and the source swallows it, so the state machine runs
exactly as it does in the game. That side effect is intentionally NOT part
of the port.

Neither add_kill nor update touches pygame, so this oracle needs no
third-party package.

Run: python godot_rebuild/tests/combo_counter_source_oracle.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "combo_counter_source.json"

# add_kill is called at the start of these ticks, before that tick's update.
KILL_TICKS = [0, 1, 2, 40, 41]
TOTAL_STEPS = 220


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class ComboCounter:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {}
    exec(compile(block, "_render.py:ComboCounter", "exec"), namespace)
    return namespace["ComboCounter"]


def source_fixture():
    cls = _load_class()
    item = cls()
    steps = []
    for tick in range(TOTAL_STEPS):
        if tick in KILL_TICKS:
            item.add_kill()
        item.update()
        steps.append([
            item.count,
            item.timer,
            round(item.display_scale, 8),
            round(item.target_scale, 8),
            item.color_flash,
            item.last_combo,
        ])
    return {
        "source": "_render.py::ComboCounter",
        "max_timer": item.max_timer,
        "kill_ticks": KILL_TICKS,
        "steps": steps,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d steps)" % (FIXTURE, len(fixture["steps"])))


if __name__ == "__main__":
    sys.exit(main())
