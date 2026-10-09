"""Source oracle for the ScreenShake port.

`import _render` fails today with a pre-existing circular import and the
Python sources are read-only, so this oracle extracts the real
`class ScreenShake` block from `_render.py` and executes it verbatim with
`random` in scope.

`get_offset()` draws from `random.randint`, so the exact offsets cannot be
replayed in GDScript. The oracle therefore records two things: the fully
deterministic intensity decay, and the sampled offsets together with the
intensity they were drawn at, so the native suite can assert the real
invariant (each component is an integer inside +/- int(intensity)).

Nothing here needs a third-party package.

Run: python godot_rebuild/tests/screen_shake_source_oracle.py
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "screen_shake_source.json"

STEPS = 40


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class ScreenShake:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {"random": random}
    exec(compile(block, "_render.py:ScreenShake", "exec"), namespace)
    return namespace["ScreenShake"]


def _decay(cls, shake, steps=STEPS):
    random.seed(908172)
    item = cls()
    item.add_shake(shake)
    trace = []
    for _ in range(steps):
        item.update()
        trace.append(round(item.intensity, 8))
    return trace


def _offsets(cls, shake, steps=STEPS):
    random.seed(112358)
    item = cls()
    item.add_shake(shake)
    samples = []
    for _ in range(steps):
        item.update()
        if item.intensity <= 0:
            continue
        ox, oy = item.get_offset()
        samples.append([ox, oy, int(item.intensity)])
    return samples


def source_fixture():
    cls = _load_class()

    random.seed(1)
    probe = cls()
    decay = probe.decay

    stacking = cls()
    stacking.add_shake(5)
    stacking.add_shake(12)
    after_bigger = stacking.intensity
    stacking.add_shake(3)
    after_smaller = stacking.intensity

    disabled = cls()
    disabled.enabled = False
    disabled.add_shake(9)
    disabled_intensity = disabled.intensity

    return {
        "source": "_render.py::ScreenShake",
        "decay": decay,
        "cases": [
            {"name": "decay_from_12", "shake": 12, "intensity": _decay(cls, 12)},
            {"name": "decay_from_3", "shake": 3, "intensity": _decay(cls, 3)},
        ],
        "offset_samples": _offsets(cls, 12),
        "stacking": {"after_bigger": after_bigger, "after_smaller": after_smaller},
        "disabled_intensity": disabled_intensity,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s" % FIXTURE)


if __name__ == "__main__":
    sys.exit(main())
