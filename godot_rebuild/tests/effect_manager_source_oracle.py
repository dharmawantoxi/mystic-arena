"""Source oracle for `_render.py::EffectManager`.

The source module is not imported. This oracle extracts the real EffectManager
class and its effect dependencies, then executes them with pygame, settings
and quality shims. Random constructor data is recorded as replay specs so the
Godot suite checks manager orchestration rather than a rewritten random model.
Drawing methods are not called: the port is state/getter-only.

Run: python godot_rebuild/tests/effect_manager_source_oracle.py
"""
import json
import math
import random
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "effect_manager_source.json"
SOURCE_TAG = "_render.py:EffectManager"


CASES = [
    {
        "name": "basic_effect_flow",
        "seed": 1729,
        "settings": {
            "damage_numbers_enabled": True,
            "particles": True,
            "particle_ratio": 1.0,
            "max_damage_numbers": 300,
            "screen_shake_enabled": True,
        },
        "operations": [
            {"op": "damage", "x": 100, "y": 200, "damage": 25, "damage_type": "normal"},
            {"op": "damage", "x": 120, "y": 210, "damage": 40, "is_critical": True},
            {"op": "damage", "x": 140, "y": 220, "damage": 8, "damage_type": "heal"},
            {"op": "damage", "x": 160, "y": 230, "damage": 12, "damage_type": "fire"},
            {"op": "damage", "x": 180, "y": 240, "damage": 13, "damage_type": "ice"},
            {"op": "damage", "x": 200, "y": 250, "damage": 14, "damage_type": "magic"},
            {"op": "gold", "x": 250, "y": 300, "amount": 75},
            {"op": "particles", "x": 300, "y": 320, "team": "red", "count": 3},
            {"op": "particles", "x": 340, "y": 360, "team": "blue", "count": 2},
            {"op": "explosion", "x": 400, "y": 380, "team": "blue", "size": "small"},
            {"op": "shake", "intensity": 7},
            {"op": "path", "paths": [[[0, 100], [100, 110]], [[0, 300], [100, 300]]]},
            {"op": "wave", "wave_num": 4},
            {"op": "achievement", "title": "First Blood", "description": "Win a duel", "icon": "skull"},
            {"op": "kill", "killer": "Tower", "victim": "Enemy", "team": "blue"},
            {"op": "update", "steps": 1},
            {"op": "update", "steps": 20},
            {
                "op": "settings",
                "damage_numbers_enabled": False,
                "particles": False,
                "particle_ratio": 0.0,
                "max_damage_numbers": 8,
                "screen_shake_enabled": False,
                "sync": True,
            },
            {"op": "damage", "x": 500, "y": 500, "damage": 99, "damage_type": "normal"},
            {"op": "particles", "x": 500, "y": 500, "team": "red", "count": 5},
            {"op": "shake", "intensity": 12},
            {"op": "update", "steps": 5},
        ],
    },
    {
        "name": "quality_caps_and_expiry",
        "seed": 2718,
        "settings": {
            "damage_numbers_enabled": True,
            "particles": True,
            "particle_ratio": 0.4,
            "max_damage_numbers": 2,
            "screen_shake_enabled": True,
        },
        "operations": [
            {"op": "damage", "x": 10, "y": 20, "damage": 1, "damage_type": "normal"},
            {"op": "damage", "x": 20, "y": 30, "damage": 2, "damage_type": "normal"},
            {"op": "damage", "x": 30, "y": 40, "damage": 3, "damage_type": "normal"},
            {"op": "particles", "x": 50, "y": 60, "team": "blue", "count": 5},
            {"op": "explosion", "x": 80, "y": 90, "team": "red", "size": "small"},
            {"op": "shake", "intensity": 3},
            {"op": "update", "steps": 12},
            {"op": "update", "steps": 50},
        ],
    },
]


class _FontShim:
    def render(self, *_args, **_kwargs):
        return _SurfaceShim((1, 1))


class _SurfaceShim:
    def __init__(self, size=(1, 1), _flags=0):
        self.width = int(size[0])
        self.height = int(size[1])

    def set_alpha(self, *_args, **_kwargs):
        return None

    def blit(self, *_args, **_kwargs):
        return None

    def get_rect(self, **_kwargs):
        return _Rect()


class _Rect:
    def __init__(self):
        self.center = (0, 0)


class _DrawShim:
    @staticmethod
    def circle(*_args, **_kwargs):
        return None


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    draw = _DrawShim()


class _GameSettings:
    damage_numbers_enabled = True
    screen_shake_enabled = True


class _Quality:
    max_damage_numbers = 300
    particles = True
    particle_ratio = 1.0


def _install_modules():
    core = types.ModuleType("_core")
    core.GameSettings = _GameSettings
    mobile = types.ModuleType("mobile")
    mobile.__path__ = []
    perf = types.ModuleType("mobile.perf")
    perf.Quality = _Quality
    sidepanel = types.ModuleType("mobile.sidepanel")
    mobile.perf = perf
    mobile.sidepanel = sidepanel
    sys.modules.update(
        {
            "_core": core,
            "mobile": mobile,
            "mobile.perf": perf,
            "mobile.sidepanel": sidepanel,
        }
    )


def _class_block(lines, name):
    start = next(i for i, line in enumerate(lines) if line.startswith(f"class {name}:"))
    if name == "AchievementPopup":
        end = next(i for i in range(start + 1, len(lines)) if lines[i] == "# effects_death.py")
    else:
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("class ")),
            len(lines),
        )
    return "\n".join(lines[start:end])


def _load_class():
    _install_modules()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    namespace = {
        "math": math,
        "random": random,
        "pygame": _PygameShim(),
        "get_font": lambda *_args, **_kwargs: _FontShim(),
    }
    for name in ("FloatingText", "HitParticle", "DeathExplosion", "ScreenShake"):
        exec(compile(_class_block(lines, name), f"_render.py:{name}", "exec"), namespace)
    exec(compile(_class_block(lines, "EffectManager"), SOURCE_TAG, "exec"), namespace)
    for name in ("ComboCounter", "WaveAnnouncer", "KillFeed", "PathPreview", "AchievementPopup"):
        exec(compile(_class_block(lines, name), f"_render.py:{name}", "exec"), namespace)
    return namespace["EffectManager"]


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _color(value):
    return _jsonable(value)


def _floating_snapshot(value):
    return {
        "x": round(float(value.x), 6),
        "y": round(float(value.y), 6),
        "text": value.text,
        "color": _color(value.color),
        "velocity_x": round(float(value.velocity_x), 6),
        "velocity_y": round(float(value.velocity_y), 6),
        "lifetime": value.lifetime,
        "max_lifetime": value.max_lifetime,
        "alive": bool(value.alive),
        "critical": bool(value.critical),
        "font_size": value.font_size,
        "x_drift": round(float(value.x_drift), 6),
        "scale": round(float(value.scale), 6),
        "target_scale": round(float(value.target_scale), 6),
    }


def _particle_snapshot(value):
    return {
        "x": round(float(value.x), 6),
        "y": round(float(value.y), 6),
        "color": _color(value.color),
        "vx": round(float(value.vx), 6),
        "vy": round(float(value.vy), 6),
        "lifetime": value.lifetime,
        "max_lifetime": value.max_lifetime,
        "size": value.size,
        "alive": bool(value.alive),
    }


def _explosion_snapshot(value):
    return {
        "x": value.x,
        "y": value.y,
        "flash_timer": value.flash_timer,
        "flash_max": value.flash_max,
        "particle_count": len(value.particles),
        "alive": bool(value.alive),
    }


def _nested_snapshot(manager):
    combo = manager.combo_counter
    wave = manager.wave_announcer
    path = manager.path_preview
    achievement = manager.achievement
    return {
        "combo": {
            "count": combo.count,
            "timer": combo.timer,
            "max_timer": combo.max_timer,
            "display_scale": round(float(combo.display_scale), 6),
            "target_scale": round(float(combo.target_scale), 6),
            "color_flash": combo.color_flash,
            "last_combo": combo.last_combo,
        },
        "wave": {
            "active": bool(wave.active),
            "wave_num": wave.wave_num,
            "timer": wave.timer,
            "duration": wave.duration,
        },
        "kill_feed": _jsonable(manager.kill_feed.entries),
        "path_preview": {
            "active": bool(path.active),
            "paths": _jsonable(path.paths),
            "timer": path.timer,
            "duration": path.duration,
        },
        "achievement": {
            "queue": _jsonable(achievement.queue),
            "current": _jsonable(achievement.current),
            "timer": achievement.timer,
            "duration": achievement.duration,
        },
    }


def _snapshot(manager):
    return {
        "floating_count": len(manager.floating_texts),
        "particle_count": len(manager.particles),
        "explosion_count": len(manager.explosions),
        "floating": [_floating_snapshot(value) for value in manager.floating_texts],
        "particles": [_particle_snapshot(value) for value in manager.particles],
        "explosions": [_explosion_snapshot(value) for value in manager.explosions],
        "screen_shake": {
            "intensity": round(float(manager.screen_shake.intensity), 6),
            "enabled": bool(manager.screen_shake.enabled),
        },
        **_nested_snapshot(manager),
    }


def _set_settings(values):
    _GameSettings.damage_numbers_enabled = values.get("damage_numbers_enabled", True)
    _GameSettings.screen_shake_enabled = values.get("screen_shake_enabled", True)
    _Quality.particles = values.get("particles", True)
    _Quality.particle_ratio = values.get("particle_ratio", 1.0)
    _Quality.max_damage_numbers = values.get("max_damage_numbers", 300)


def _damage_replay(manager, before_count):
    if len(manager.floating_texts) == 0 or len(manager.floating_texts) == before_count == 0:
        return None
    value = manager.floating_texts[-1]
    return {
        "offset_x": round(float(value.x - _current_operation["x"]), 6),
        "offset_y": round(float(value.y - _current_operation["y"]), 6),
        "drift": round(float(value.x_drift), 6),
    }


_current_operation = None


def _run_case(cls, case):
    global _current_operation
    random.seed(case["seed"])
    _set_settings(case["settings"])
    manager = cls()
    outputs = []
    for operation in case["operations"]:
        _current_operation = operation
        op = operation["op"]
        replay = None
        if op == "settings":
            _set_settings(operation)
            if operation.get("sync", False):
                manager.sync_settings()
        elif op == "damage":
            before = len(manager.floating_texts)
            manager.add_damage_number(
                operation["x"],
                operation["y"],
                operation["damage"],
                operation.get("is_critical", False),
                operation.get("damage_type", "normal"),
            )
            if _GameSettings.damage_numbers_enabled and len(manager.floating_texts) > 0:
                value = manager.floating_texts[-1]
                replay = {
                    "offset_x": round(float(value.x - operation["x"]), 6),
                    "offset_y": round(float(value.y - operation["y"]), 6),
                    "drift": round(float(value.x_drift), 6),
                    "created": len(manager.floating_texts) != before or before > 0,
                }
        elif op == "gold":
            manager.add_gold_popup(operation["x"], operation["y"], operation["amount"])
            value = manager.floating_texts[-1]
            replay = {"drift": round(float(value.x_drift), 6)}
        elif op == "particles":
            before = len(manager.particles)
            manager.add_hit_particles(
                operation["x"],
                operation["y"],
                operation["team"],
                operation["count"],
            )
            if _Quality.particles and len(manager.particles) > before:
                replay = {
                    "specs": [
                        {
                            "color": _color(value.color),
                            "vx": round(float(value.vx), 6),
                            "vy": round(float(value.vy), 6),
                            "lifetime": value.lifetime,
                            "size": value.size,
                        }
                        for value in manager.particles[-max(1, len(manager.particles) - before):]
                    ]
                }
        elif op == "explosion":
            manager.add_death_explosion(
                operation["x"], operation["y"], operation["team"], operation["size"]
            )
            value = manager.explosions[-1]
            replay = {
                "specs": [
                    {
                        "color": _color(particle.color),
                        "vx": round(float(particle.vx), 6),
                        "vy": round(float(particle.vy), 6),
                        "lifetime": particle.lifetime,
                        "size": particle.size,
                    }
                    for particle in value.particles
                ]
            }
        elif op == "shake":
            manager.shake_screen(operation["intensity"])
        elif op == "path":
            manager.show_path_preview(_as_array(operation["paths"]))
        elif op == "wave":
            manager.announce_wave(operation["wave_num"])
        elif op == "achievement":
            manager.unlock_achievement(operation["title"], operation["description"], operation["icon"])
        elif op == "kill":
            manager.register_kill(operation["killer"], operation["victim"], operation["team"])
        elif op == "update":
            for _index in range(operation["steps"]):
                manager.update()
        else:
            raise ValueError(op)
        outputs.append({"replay": replay, "snapshot": _snapshot(manager)})
    return {
        "name": case["name"],
        "seed": case["seed"],
        "settings": case["settings"],
        "operations": case["operations"],
        "outputs": outputs,
    }


def _as_array(value):
    if isinstance(value, list):
        return [_as_array(item) for item in value]
    return value


def source_fixture():
    cls = _load_class()
    return {
        "source": "_render.py::EffectManager",
        "max_floating": 300,
        "max_particles": 500,
        "max_explosions": 80,
        "cases": [_run_case(cls, case) for case in CASES],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    main()
