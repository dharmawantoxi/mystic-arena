"""Source oracle for the ambient tint of `MapRenderer.draw()` (layer 9bh).

`_render.py::MapRenderer` already has its state ported (`scripts/ui/map_renderer.gd`,
`map_renderer_source_oracle.py`); its terrain / river / lane / wall layers are
cached textures. What the Godot view never drew is the last step of `draw()`: the
per-theme ambient tint laid over the whole map, under the units. With
`Quality.cheap_alpha` (the PC default) the tint is a screen-sized SRCALPHA surface
filled with the theme's `(r, g, b, a)` and blitted; without it the screen is
multiplied by `255 - (255 - c) * a / 255` per channel (`BLEND_RGB_MULT`). Themes
without `ambient_tint` (forest, or an unknown name that falls back to forest) draw
nothing.

The REAL `MapRenderer.draw` is harvested from `_render.py` with `ast` and run under
the recording pygame shim of `draw_recorder.py` on an instance built without its
heavy `__init__` (static map and dynamic renderer are inert stand-ins). The tint of
every theme is read from the real theme dictionaries of `map_components/_bundle.py`
(`THEMES` plus each `*_THEME` literal), also with `ast`, since that module cannot
be imported without pygame.

Run: python godot_rebuild/tests/map_tint_draw_source_oracle.py
"""
import ast
import json
import math
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
BUNDLE = ROOT / "map_components" / "_bundle.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "map_tint_draw_source.json"
SIZE = (1280, 720)


def theme_tints():
    """{theme name: [r, g, b, a] or None} from the real theme literals."""
    tree = ast.parse(BUNDLE.read_text(encoding="utf-8"))
    literals, registry = {}, None
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        if name == "THEMES":
            registry = {ast.literal_eval(key): value.id
                        for key, value in zip(node.value.keys, node.value.values)}
        elif name.endswith("_THEME") and isinstance(node.value, ast.Dict):
            literals[name] = node.value
    tints = {}
    for theme, variable in registry.items():
        tint = None  # `theme.get("ambient_tint")` of a theme without the key
        for key, value in zip(literals[variable].keys, literals[variable].values):
            if isinstance(key, ast.Constant) and key.value == "ambient_tint":
                tint = ast.literal_eval(value)
        tints[theme] = None if tint is None else [int(channel) for channel in tint]
    return tints


def _load_class(pygame):
    namespace = {"math": math, "pygame": pygame}
    for segment in rec.harvest(SOURCE, ["MapRenderer"]):
        exec(compile(segment, "_render.py", "exec"), namespace)
    return namespace["MapRenderer"]


def _modules():
    pygame = rec.make_pygame({"ticks": 0})
    perf = rec.make_perf(True)
    mobile = SimpleNamespace(perf=perf)
    return {"pygame": pygame, "mobile": mobile, "mobile.perf": perf}


def _renderer(cls, tint):
    renderer = cls.__new__(cls)
    renderer.map_width, renderer.map_height = SIZE
    renderer.static_map = rec.Surface(SIZE)
    renderer.dynamic = SimpleNamespace(draw=lambda surface, animation_time: None)
    renderer.theme = {"ambient_tint": None if tint is None else tuple(tint)}
    return renderer


def source_fixture():
    modules = _modules()
    tints = theme_tints()
    with rec.installed(modules):
        cls = _load_class(modules["pygame"])
        frames = []
        for theme, tint in tints.items():
            for cheap_alpha in (True, False):
                modules["mobile.perf"].Quality.cheap_alpha = cheap_alpha
                screen = rec.Surface(SIZE)
                _renderer(cls, tint).draw(screen, 0)
                frames.append({"theme": theme, "cheap_alpha": cheap_alpha, "ops": screen.ops})
    return {
        "source": "_render.py::MapRenderer.draw (ambient tint)",
        "screen": list(SIZE),
        "tints": tints,
        "frames": frames,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d themes, %d frames, %d ops)" % (
        FIXTURE.relative_to(ROOT), len(fixture["tints"]), len(fixture["frames"]), drawn))


if __name__ == "__main__":
    main()
