"""Source oracle for `_render.py::MapRenderer`.

The renderer module is not imported. This oracle extracts the real coordinator
class and executes its constructor with pygame and map-component shims. The
fixture therefore records source initialization, delegated lane/river and
-decoration state, shop getters and click hit-testing without requiring pygame
or porting any drawing.

Run: python godot_rebuild/tests/map_renderer_source_oracle.py
"""
import json
import math
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "map_renderer_source.json"
SOURCE_TAG = "_render.py:MapRenderer"


CASES = [
    {
        "name": "forest_fixture",
        "theme_name": "forest",
        "theme": {"name": "forest", "ambient_tint": [18, 24, 30, 90]},
        "lanes": {
            "top": [[0, 120], [320, 150], [640, 180], [960, 210], [1280, 240]],
            "mid": [[0, 360], [320, 360], [640, 360], [960, 360], [1280, 360]],
            "bot": [[0, 600], [320, 570], [640, 540], [960, 510], [1280, 480]],
        },
        "river": [[500, 0], [540, 180], [560, 360], [540, 540], [500, 720]],
        "decorations": {
            "trees": [[100, 100], [1120, 620]],
            "rocks": [[250, 280], [880, 430]],
            "ruins": [[720, 140]],
        },
        "clicks": [[340, 540], [400, 540], [401, 540], [940, 180], [940, 241], [940, 241.1], [640, 360]],
    },
    {
        "name": "desert_fixture",
        "theme_name": "desert",
        "theme": {"name": "desert", "ambient_tint": None},
        "lanes": {
            "top": [[0, 90], [640, 140], [1280, 190]],
            "mid": [[0, 350], [640, 360], [1280, 370]],
            "bot": [[0, 630], [640, 580], [1280, 530]],
        },
        "river": [[620, 0], [600, 240], [620, 480], [650, 720]],
        "decorations": {
            "cacti": [[180, 180], [1080, 540]],
            "dunes": [[400, 200], [800, 500]],
        },
        "clicks": [[340, 540], [940, 180], [0, 0], [340, 479.9]],
    },
]


class _SurfaceShim:
    def __init__(self, size=(1, 1), _flags=0):
        self.width = int(size[0])
        self.height = int(size[1])
        self.layers = []

    def blit(self, *_args, **_kwargs):
        return None

    def fill(self, *_args, **_kwargs):
        return None


class _PygameShim:
    SRCALPHA = 1
    BLEND_RGB_MULT = 2
    Surface = _SurfaceShim


def _class_block(lines, name):
    start = next(i for i, line in enumerate(lines) if line.startswith(f"class {name}:"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "# effects.py")
    return "\n".join(lines[start:end])


def _as_tuple(value):
    if isinstance(value, list):
        return tuple(_as_tuple(item) for item in value)
    if isinstance(value, dict):
        return {key: _as_tuple(item) for key, item in value.items()}
    return value


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _install_stubs(case):
    map_components = types.ModuleType("map_components")
    map_components.__path__ = []
    themes = types.ModuleType("map_components.themes")
    generators = types.ModuleType("map_components.generators")
    static_renderer = types.ModuleType("map_components.static_renderer")
    decoration_renderer = types.ModuleType("map_components.decoration_renderer")
    shop_renderer = types.ModuleType("map_components.shop_renderer")
    dynamic_renderer = types.ModuleType("map_components.dynamic_renderer")

    theme_data = _as_tuple(case["theme"])

    def get_theme(theme_name):
        assert theme_name == case["theme_name"]
        return dict(theme_data)

    class PathGenerator:
        @staticmethod
        def generate_lanes(_width, _height):
            lanes = case["lanes"]
            return tuple(_as_tuple(lanes[name]) for name in ("top", "mid", "bot"))

        @staticmethod
        def generate_river(_width, _height):
            return _as_tuple(case["river"])

    class DecorationGenerator:
        def __init__(self, _width, _height, _lane_points, _river_points, _shops):
            pass

        def generate_all(self):
            return _as_tuple(case["decorations"])

    def _record(name):
        def draw(surface, *_args, **_kwargs):
            surface.layers.append(name)

        return staticmethod(draw)

    class StaticRenderer:
        draw_terrain = _record("terrain")
        draw_terrain_details = _record("terrain_details")
        draw_river = _record("river")
        draw_lane = _record("lane")
        draw_border_wall = _record("border_wall")

    class DecorationRenderer:
        draw_all = _record("decorations")

    class ShopRenderer:
        draw = _record("shops")

    class DynamicRenderer:
        def __init__(self, renderer):
            self.renderer = renderer

        def draw(self, *_args, **_kwargs):
            return None

    themes.get_theme = get_theme
    generators.PathGenerator = PathGenerator
    generators.DecorationGenerator = DecorationGenerator
    static_renderer.StaticRenderer = StaticRenderer
    decoration_renderer.DecorationRenderer = DecorationRenderer
    shop_renderer.ShopRenderer = ShopRenderer
    dynamic_renderer.DynamicRenderer = DynamicRenderer
    sys.modules.update(
        {
            "map_components": map_components,
            "map_components.themes": themes,
            "map_components.generators": generators,
            "map_components.static_renderer": static_renderer,
            "map_components.decoration_renderer": decoration_renderer,
            "map_components.shop_renderer": shop_renderer,
            "map_components.dynamic_renderer": dynamic_renderer,
        }
    )


def _load_class(case):
    _install_stubs(case)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    namespace = {
        "SCREEN_WIDTH": 1280,
        "SCREEN_HEIGHT": 720,
        "pygame": _PygameShim(),
        "math": math,
    }
    exec(compile(_class_block(lines, "MapRenderer"), SOURCE_TAG, "exec"), namespace)
    return namespace["MapRenderer"]


def _snapshot(renderer):
    return {
        "map_width": renderer.map_width,
        "map_height": renderer.map_height,
        "theme_name": renderer.theme_name,
        "theme": _jsonable(renderer.theme),
        "shop_positions": _jsonable(renderer.get_shop_positions()),
        "lanes": {
            "top": _jsonable(renderer.top_lane_points),
            "mid": _jsonable(renderer.mid_lane_points),
            "bot": _jsonable(renderer.bot_lane_points),
        },
        "river": _jsonable(renderer.river_points),
        "decorations": {
            key: _jsonable(value)
            for key, value in renderer.__dict__.items()
            if key in ("trees", "rocks", "ruins", "cacti", "dunes")
        },
        "static_layers": list(renderer.static_map.layers),
        "static_map_ready": isinstance(renderer.static_map, _SurfaceShim),
        "dynamic_ready": renderer.dynamic.renderer is renderer,
    }


def _run_case(cls, case):
    renderer = cls(object(), case["theme_name"])
    outputs = []
    for click in case["clicks"]:
        x, y = click
        outputs.append(
            {
                "click": [x, y],
                "is_shop": bool(renderer.is_click_on_shop(x, y)),
                "clicked_shop": renderer.get_clicked_shop(x, y),
            }
        )
    return {
        "name": case["name"],
        "theme_name": case["theme_name"],
        "lanes": case["lanes"],
        "river": case["river"],
        "decorations": case["decorations"],
        "snapshot": _snapshot(renderer),
        "lane_queries": {
            name: _jsonable(renderer.get_lane_path(name))
            for name in ("top", "mid", "bot", "unknown")
        },
        "clicks": outputs,
    }


def source_fixture():
    cases = []
    for case in CASES:
        cls = _load_class(case)
        cases.append(_run_case(cls, case))
    return {
        "source": "_render.py::MapRenderer",
        "map_width": 1280,
        "map_height": 720,
        "shop_size": 60,
        "shop_positions": {"radiant": [340, 540], "dire": [940, 180]},
        "cases": cases,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    main()
