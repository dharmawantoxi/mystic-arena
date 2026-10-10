"""Source oracle for the KillFeed port.

`import _render` fails today with a pre-existing circular import and the
Python sources are read-only, so this oracle extracts the real
`class KillFeed` block from `_render.py` and executes it verbatim.

Neither add_kill nor update touches pygame (only draw does), so the whole
state machine is deterministic and this oracle needs no third-party package.

Run: python godot_rebuild/tests/kill_feed_source_oracle.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "kill_feed_source.json"

# (tick, killer, victim, team) applied at the start of that tick.
SCRIPT = [
    [0, "Kaizen", "Grimjaw", "blue"],
    [3, "Thorne", "Vex", "red"],
    [6, "Sylara", "Zephyr", "blue"],
    [9, "Grimjaw", "Sylara", "red"],
    [12, "Vex", "Thorne", "blue"],
    [15, "Zephyr", "Kaizen", "red"],  # sixth entry: exercises the 5-entry cap
]
TOTAL_STEPS = 200


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class KillFeed:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {}
    exec(compile(block, "_render.py:KillFeed", "exec"), namespace)
    return namespace["KillFeed"]


def source_fixture():
    cls = _load_class()
    feed = cls()
    steps = []
    for tick in range(TOTAL_STEPS):
        for tick_index, killer, victim, team in SCRIPT:
            if int(tick_index) == tick:
                feed.add_kill(killer, victim, team)
        feed.update()
        steps.append([
            [
                str(entry["text"]),
                int(entry["lifetime"]),
                round(entry["y_offset"], 8),
                round(entry["target_y"], 8),
            ]
            for entry in feed.entries
        ])
    return {
        "source": "_render.py::KillFeed",
        "script": SCRIPT,
        "steps": steps,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d steps)" % (FIXTURE, len(fixture["steps"])))


if __name__ == "__main__":
    sys.exit(main())
