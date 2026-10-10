"""Source oracle for `_render.py::RenderCache`.

The source module is not imported. This oracle extracts the real RenderCache
class and executes it with pygame and font shims. Surface dimensions, clamped
circle colours, glow layer metadata, cache reuse and clear semantics therefore
come from the source class without requiring pygame or porting pixel drawing.

Run: python godot_rebuild/tests/render_cache_source_oracle.py
"""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "render_cache_source.json"
SOURCE_TAG = "_render.py:RenderCache"


CASES = [
    {
        "name": "font_and_shape_reuse",
        "operations": [
            {"op": "font", "size": 6, "style": "body", "bold": False},
            {"op": "font", "size": 300, "style": "title", "bold": True},
            {"op": "font", "size": 6, "style": "body", "bold": False},
            {"op": "font", "size": 16, "style": "body", "bold": True},
            {"op": "circle", "radius": 10, "color": [-20, 128, 300], "width": 0},
            {"op": "circle", "radius": 10, "color": [0, 128, 255], "width": 0},
            {"op": "circle", "radius": 10, "color": [0, 128, 255, 999], "width": 2},
            {"op": "circle", "radius": 10, "color": [0, 128, 255, 999], "width": 2},
            {"op": "glow", "radius": 12, "color": [40, 80, 120, 10], "layers": 4},
            {"op": "glow", "radius": 12, "color": [40, 80, 120, 220], "layers": 4},
            {"op": "glow", "radius": 3, "color": [200, 100, 50], "layers": 5},
            {"op": "stats"},
            {"op": "clear"},
            {"op": "stats"},
            {"op": "font", "size": 6, "style": "body", "bold": False},
            {"op": "circle", "radius": 10, "color": [0, 128, 255], "width": 0},
        ],
    },
    {
        "name": "style_and_layer_keys",
        "operations": [
            {"op": "font", "size": 20, "style": "body_medium", "bold": False},
            {"op": "font", "size": 20, "style": "body_medium", "bold": True},
            {"op": "font", "size": 20, "style": "body_medium", "bold": False},
            {"op": "circle", "radius": 0, "color": [255, 0, 0, 10], "width": 0},
            {"op": "circle", "radius": 0, "color": [255, 0, 0, 10], "width": 1},
            {"op": "glow", "radius": 10, "color": [10, 20, 30], "layers": 1},
            {"op": "glow", "radius": 10, "color": [10, 20, 30], "layers": 2},
            {"op": "stats"},
        ],
    },
]


class _FontShim:
    def __init__(self, size, style, bold, serial):
        self.size = size
        self.style = style
        self.bold = bool(bold)
        self.serial = serial


class _SurfaceShim:
    def __init__(self, size=(1, 1), _flags=0):
        self.width = int(size[0])
        self.height = int(size[1])
        self.draw_calls = []


class _DrawShim:
    @staticmethod
    def circle(surface, color, center, radius, width=0):
        surface.draw_calls.append(
            {
                "color": list(color),
                "center": list(center),
                "radius": int(radius),
                "width": int(width),
            }
        )


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim
    draw = _DrawShim()


def _class_block(lines, name):
    start = next(i for i, line in enumerate(lines) if line.startswith(f"class {name}:"))
    end = next(
        i for i in range(start + 1, len(lines)) if lines[i] == "_cache = RenderCache()"
    )
    return "\n".join(lines[start:end])


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    font_calls = []

    def make_font(size, style, bold=False):
        font = _FontShim(size, style, bold, len(font_calls) + 1)
        font_calls.append(font)
        return font

    namespace = {"pygame": _PygameShim(), "_make_font": make_font}
    exec(compile(_class_block(lines, "RenderCache"), SOURCE_TAG, "exec"), namespace)
    return namespace["RenderCache"], font_calls


def _tuple_key(value):
    if isinstance(value, list):
        return tuple(_tuple_key(item) for item in value)
    return value


def _font_summary(font):
    return {
        "size": int(font.size),
        "style": font.style,
        "bold": bool(font.bold),
    }


def _surface_summary(surface):
    return {
        "width": surface.width,
        "height": surface.height,
        "draw_calls": surface.draw_calls,
    }


def _run_case(cls, case, font_calls):
    cls._instance = None
    font_calls.clear()
    cache = cls()
    outputs = []

    for operation in case["operations"]:
        op = operation["op"]
        if op == "font":
            result = cache.get_font(
                operation["size"], operation["style"], operation["bold"]
            )
            output = {"font": _font_summary(result)}
        elif op == "circle":
            result = cache.get_circle_surface(
                operation["radius"],
                _tuple_key(operation["color"]),
                operation["width"],
            )
            output = {"surface": _surface_summary(result)}
        elif op == "glow":
            result = cache.get_glow_surface(
                operation["radius"],
                _tuple_key(operation["color"]),
                operation["layers"],
            )
            output = {"surface": _surface_summary(result)}
        elif op == "clear":
            cache.clear()
            output = {}
        elif op == "stats":
            output = {}
        else:
            raise ValueError(op)
        output["font_calls"] = len(font_calls)
        output["stats"] = cache.get_stats()
        outputs.append(output)

    return {
        "name": case["name"],
        "operations": case["operations"],
        "outputs": outputs,
    }


def source_fixture():
    cls, font_calls = _load_class()
    first = cls()
    second = cls()
    singleton_same_instance = first is second
    return {
        "source": "_render.py::RenderCache",
        "font_min": 8,
        "font_max": 220,
        "singleton_same_instance": singleton_same_instance,
        "cases": [_run_case(cls, case, font_calls) for case in CASES],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    main()
