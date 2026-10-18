"""Source oracle for `DeathExplosion.draw()` and `HitParticle.draw()` (layer 9bg).

`_render.py::DeathExplosion` and `HitParticle` already have their state ported
(`death_explosion.gd`, `hit_particle.gd`, `death_explosion_source_oracle.py`,
`hit_particle_source_oracle.py`); this oracle pins the DRAW of both. The central
flash is two discs drawn onto one SRCALPHA surface WITHOUT blending, so the inner
`size // 2` disc (white, `255 * intensity`) overwrites the middle of the outer
`size` disc (`(255, 255, 200, 200 * intensity)`), and the surface is blitted so
the discs sit on `int(x), int(y)`. Every spark is a `HitParticle`: its sprite
(a colour disc of radius `base` with a white core of `max(1, base // 2)` that
overwrites the middle) is scaled to `max(1, int(size * life ratio))` and blitted
at `int(x), int(y)` with surface alpha `int(255 * life ratio)`.

The REAL `DeathExplosion` and `HitParticle` classes are harvested from `_render.py`
with `ast` and `draw()` runs under the recording pygame shim of `draw_recorder.py`
(`pygame.transform.scale` is modelled on the sprite's circle geometry). The random
sparks of each explosion are seeded and their created values stored, so the Godot
port replays them through `configure(..., particle_specs)` and ticks `update()`.

Run: python godot_rebuild/tests/death_explosion_draw_source_oracle.py
"""
import json
import math
import random
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "death_explosion_draw_source.json"

# (label, x, y, team, size, seed, ticks drawn after N update() calls). Fractional anchors
# prove the `int()` truncation; ticks 0-7 carry the flash, 8 is the first frame without it.
EXPLOSIONS = [
    ("red_small", 120.5, 80.25, "red", "small", 1729, [0, 1, 4, 7, 8, 18, 25]),
    ("blue_medium", 320.0, 180.75, "blue", "medium", 2718, [0, 3, 7, 12, 22, 30]),
    ("blue_large", 640.9, 360.0, "blue", "large", 31415, [0, 1, 5, 8, 15, 28, 34]),
]
# Standalone HitParticles: (x, y, colour, velocity, lifetime, size). Sizes 1, 2, 3 and 6 reach
# the unscaled sprite (size == current size) and the scaled one; lifetime 8 ends before tick 9.
SPARKS = ("sparks", [
    (200.4, 150.6, (255, 200, 100), (1.0, -1.0), 15, 2),
    (210.0, 150.0, (100, 200, 255), (0.5, 0.0), 10, 1),
    (220.7, 151.2, (255, 100, 100), (-1.0, -0.5), 20, 6),
    (230.2, 149.9, (200, 240, 255), (0.0, -2.0), 8, 3),
], [0, 2, 5, 7, 9])


def _load_classes(pygame):
    namespace = {"math": math, "random": random, "pygame": pygame}
    for segment in rec.harvest(SOURCE, ["HitParticle", "DeathExplosion"]):
        exec(compile(segment, "_render.py", "exec"), namespace)
    return namespace["HitParticle"], namespace["DeathExplosion"]


def _spark_spec(particle):
    return {"x": particle.x, "y": particle.y, "color": list(particle.color),
            "vx": particle.vx, "vy": particle.vy, "lifetime": int(particle.max_lifetime),
            "size": int(particle.size)}


def _explosion_frame(label, tick, explosion, size):
    screen = rec.Surface(size)
    explosion.draw(screen)
    return {"label": label, "tick": tick,
            "state": {"flash_timer": int(explosion.flash_timer),
                      "particles": len(explosion.particles)},
            "ops": screen.ops}


def _spark_frame(label, tick, particles, size):
    screen = rec.Surface(size)
    for particle in particles:
        particle.draw(screen)
    return {"label": label, "tick": tick,
            "state": {"alive": [bool(particle.alive) for particle in particles]},
            "ops": screen.ops}


def source_fixture():
    modules = {"pygame": rec.make_pygame({"ticks": 0})}
    random_state = random.getstate()
    screen = (1280, 720)
    try:
        with rec.installed(modules):
            hit_particle, death_explosion = _load_classes(modules["pygame"])
            scenarios, frames = [], []
            for label, x, y, team, size, seed, ticks in EXPLOSIONS:
                random.seed(seed)
                explosion = death_explosion(x, y, team, size)
                scenarios.append({
                    "label": label, "kind": "explosion", "x": x, "y": y, "team": team,
                    "size": size, "ticks": list(ticks),
                    "particles": [_spark_spec(p) for p in explosion.particles],
                })
                for tick in range(max(ticks) + 1):
                    if tick in ticks:
                        frames.append(_explosion_frame(label, tick, explosion, screen))
                    explosion.update()
            label, specs, ticks = SPARKS
            particles = [hit_particle(x, y, color, velocity, lifetime=lifetime, size=size)
                         for x, y, color, velocity, lifetime, size in specs]
            scenarios.append({"label": label, "kind": "sparks", "ticks": list(ticks),
                              "particles": [_spark_spec(p) for p in particles]})
            for tick in range(max(ticks) + 1):
                if tick in ticks:
                    frames.append(_spark_frame(label, tick, particles, screen))
                for particle in particles:
                    particle.update()
            return {
                "source": "_render.py::DeathExplosion.draw + HitParticle.draw",
                "flash_frames": 8,
                "scenarios": scenarios,
                "frames": frames,
            }
    finally:
        random.setstate(random_state)


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(fixture["frames"]),
                                            drawn))


if __name__ == "__main__":
    main()
