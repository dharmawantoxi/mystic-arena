"""Headless oracle for FloatingText motion and cached draw presentation.

The module `_render` cannot be imported because of a pre-existing circular
import, so execute the original class block directly. Fake font/surface objects
record draw calls while preserving the source's cache-scale/alpha/anchor path.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "floating_text_source.json"
STEPS = 60
SAMPLE_TICKS = [0, 1, 3, 7, 15, 29, 44]
CASES = [
    {
        "name": "normal_medium", "x": 100.0, "y": 200.0, "text": "123",
        "color": [255, 220, 50], "size": "medium", "velocity": [0.0, -2.0],
        "lifetime": 45, "critical": False,
    },
    {
        "name": "critical_large", "x": 50.0, "y": 60.0, "text": "999!",
        "color": [255, 220, 50], "size": "large", "velocity": [0.0, -2.5],
        "lifetime": 30, "critical": True,
    },
    {
        "name": "heal_small", "x": 10.0, "y": 20.0, "text": "+40",
        "color": [100, 255, 100], "size": "small", "velocity": [1.0, -1.0],
        "lifetime": 20, "critical": False,
    },
]


class _RectShim:
    def __init__(self, width, height, center):
        self.width = width
        self.height = height
        self.center = tuple(center)
        self.x = int(center[0] - width / 2)
        self.y = int(center[1] - height / 2)


class _SurfaceShim:
    def __init__(self, width=0, height=0, text="", color=None, style="", record=False):
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.style = style
        self.alpha = 255
        self.record = record
        self.blits = []

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def set_alpha(self, alpha):
        self.alpha = alpha

    def get_rect(self, center=(0, 0)):
        return _RectShim(self.width, self.height, center)

    def blit(self, source, rect):
        if self.record:
            self.blits.append({
                "text": source.text,
                "center": list(rect.center),
                "size": [source.width, source.height],
                "font_size": source.height,
                "style": source.style,
                "color": list(source.color),
                "alpha": source.alpha,
            })


class _FontShim:
    def __init__(self, size, style):
        self.size = size
        self.style = style

    def render(self, text, _antialias, color):
        width = max(1, int(len(text) * self.size * 0.6))
        return _SurfaceShim(width, self.size, text, color, self.style)


class _TransformShim:
    @staticmethod
    def scale(surface, size):
        return _SurfaceShim(
            size[0], size[1], surface.text, surface.color, surface.style
        )


class _PygameShim:
    transform = _TransformShim()


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class FloatingText:"))
    end = next(i for i, line in enumerate(lines) if i > start and line.startswith("class "))
    block = "\n".join(lines[start:end])
    namespace = {
        "random": random,
        "get_font": lambda size, style="body": _FontShim(size, style),
        "pygame": _PygameShim(),
    }
    exec(compile(block, "_render.py::FloatingText", "exec"), namespace)
    return namespace["FloatingText"]


def _trace(cls, case):
    random.seed(20240917)
    item = cls(
        case["x"], case["y"], case["text"], tuple(case["color"]), case["size"],
        tuple(case["velocity"]), case["lifetime"], case["critical"],
    )
    drift = item.x_drift
    steps = []
    draw_samples = []
    for index in range(STEPS):
        item.update()
        ratio = min(1.0, item.lifetime / (item.max_lifetime * 0.5))
        steps.append([
            round(item.x, 6), round(item.y, 6), round(item.velocity_y, 6),
            round(item.scale, 6), item.lifetime, 1 if item.alive else 0,
            int(255 * ratio),
        ])
        if index in SAMPLE_TICKS:
            target = _SurfaceShim(record=True)
            item.draw(target)
            draw_samples.append({"tick": index, "blits": target.blits})
    return drift, item.font_size, draw_samples, steps


def source_fixture():
    cls = _load_class()
    cases = []
    for case in CASES:
        drift, font_size, draw_samples, steps = _trace(cls, case)
        cases.append({
            "name": case["name"],
            "config": {key: case[key] for key in (
                "x", "y", "text", "color", "size", "velocity", "lifetime", "critical"
            )},
            "x_drift": round(drift, 6),
            "font_size": font_size,
            "draw_samples": draw_samples,
            "steps": steps,
        })
    return {"source": "_render.py::FloatingText", "cases": cases}


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases, %d draw ticks)" %
          (FIXTURE, len(fixture["cases"]), len(SAMPLE_TICKS)))


if __name__ == "__main__":
    main()
