"""Source oracle for `_render.py::DeathExplosion`.

The module cannot be imported because `_render.py` has a pre-existing circular
import. This oracle extracts the real `HitParticle` dependency and the real
`DeathExplosion` class, then executes both with a pygame shim. The fixture's
particle colours, velocities, lifetimes, sizes, update snapshots and flash
locals therefore come from the source implementation, not a copied formula.

No pygame package is required. The source `draw()` is called with the shim so
its central-flash locals are captured with `sys.settrace`; no pixel drawing is
ported to Godot.

Run: python godot_rebuild/tests/death_explosion_source_oracle.py
"""
import json
import math
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "death_explosion_source.json"
HIT_TAG = "_render.py:HitParticle"
DEATH_TAG = "_render.py:DeathExplosion"
SNAPSHOT_TICKS = (0, 1, 8, 20, 35, 36)

CASES = [
    {"name": "red_small", "x": 120.0, "y": 80.0, "team": "red", "size": "small", "seed": 1729},
    {"name": "blue_medium", "x": 320.0, "y": 180.0, "team": "blue", "size": "medium", "seed": 2718},
    {"name": "blue_large", "x": 640.0, "y": 360.0, "team": "blue", "size": "large", "seed": 31415},
]


class _SurfaceShim:
    def __init__(self, size=(1, 1), _flags=0):
        self._size = tuple(size) if hasattr(size, "__iter__") else (size, size)

    def get_size(self):
        return self._size

    def convert_alpha(self):
        return self

    def set_alpha(self, *_args, **_kwargs):
        return None

    def fill(self, *_args, **_kwargs):
        return None

    def blit(self, *_args, **_kwargs):
        return None

    def get_rect(self, **_kwargs):
        return _Rect()


class _Rect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.width = w
        self.height = h


class _DrawShim:
    @staticmethod
    def circle(*_args, **_kwargs):
        return None


class _TransformShim:
    @staticmethod
    def rotate(surface, *_args, **_kwargs):
        return surface

    @staticmethod
    def scale(surface, *_args, **_kwargs):
        return surface


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    draw = _DrawShim()
    transform = _TransformShim()


def _class_block(lines, name):
    start = next(i for i, line in enumerate(lines) if line.startswith(f"class {name}:"))
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("class ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _load_classes():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    namespace = {"math": math, "random": random, "pygame": _PygameShim()}
    exec(compile(_class_block(lines, "HitParticle"), HIT_TAG, "exec"), namespace)
    exec(compile(_class_block(lines, "DeathExplosion"), DEATH_TAG, "exec"), namespace)
    return namespace["DeathExplosion"]


def _round(value):
    return round(float(value), 6)


def _particle_snapshot(particle):
    return {
        "x": _round(particle.x),
        "y": _round(particle.y),
        "vx": _round(particle.vx),
        "vy": _round(particle.vy),
        "lifetime": particle.lifetime,
        "max_lifetime": particle.max_lifetime,
        "size": particle.size,
        "alive": bool(particle.alive),
        "color": list(particle.color),
    }


def _draw_flash(explosion):
    """Capture the source draw locals without reimplementing draw()."""
    captured = {}

    def tracer(frame, event, _arg):
        if (
            event == "line"
            and frame.f_code.co_filename == DEATH_TAG
            and frame.f_code.co_name == "draw"
            and frame.f_locals.get("self") is explosion
        ):
            locals_ = frame.f_locals
            if "intensity" in locals_:
                captured["intensity"] = _round(locals_["intensity"])
            if "size" in locals_:
                captured["size"] = int(locals_["size"])
        return tracer

    sys.settrace(tracer)
    try:
        explosion.draw(_SurfaceShim((1280, 720)))
    finally:
        sys.settrace(None)
    if "intensity" not in captured:
        return None
    return captured


def _snapshot(explosion, tick):
    particles = [_particle_snapshot(particle) for particle in explosion.particles]
    return {
        "tick": tick,
        "particle_count": len(particles),
        "flash_timer": explosion.flash_timer,
        "alive": bool(explosion.alive),
        "first": particles[0] if particles else None,
        "last": particles[-1] if particles else None,
        "draw_flash": _draw_flash(explosion),
    }


def _trace_case(cls, case):
    random.seed(case["seed"])
    explosion = cls(case["x"], case["y"], case["team"], case["size"])
    initial = [_particle_snapshot(particle) for particle in explosion.particles]
    specs = [
        {
            "color": particle["color"],
            "vx": particle["vx"],
            "vy": particle["vy"],
            "lifetime": particle["lifetime"],
            "size": particle["size"],
        }
        for particle in initial
    ]
    snapshots = [_snapshot(explosion, 0)]
    for tick in range(1, max(SNAPSHOT_TICKS) + 1):
        explosion.update()
        if tick in SNAPSHOT_TICKS:
            snapshots.append(_snapshot(explosion, tick))
    return {
        "name": case["name"],
        "config": {key: case[key] for key in ("x", "y", "team", "size")},
        "seed": case["seed"],
        "particle_specs": specs,
        "snapshots": snapshots,
    }


def source_fixture():
    cls = _load_classes()
    return {
        "source": "_render.py::DeathExplosion",
        "flash_max": 8,
        "snapshot_ticks": list(SNAPSHOT_TICKS),
        "cases": [_trace_case(cls, case) for case in CASES],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    sys.exit(main())
