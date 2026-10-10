"""Source oracle for `_render.py::SpriteCache`.

The source module is not imported. This oracle extracts the real SpriteCache
class text and executes it with a pygame Surface shim, so cache hit/miss,
cropping, eviction, invalidation and statistics remain source-derived without
requiring pygame or porting any pixel drawing.

Run: python godot_rebuild/tests/sprite_cache_source_oracle.py
"""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sprite_cache_source.json"
SOURCE_TAG = "_render.py:SpriteCache"


CASES = [
    {
        "name": "basic_cache_lifecycle",
        "max_cache": 2000,
        "operations": [
            {
                "op": "full",
                "key": ["unit", "red", 1],
                "width": 64,
                "height": 80,
                "marker": "full-first",
                "bounds": [5, 6, 10, 20],
            },
            {
                "op": "full",
                "key": ["unit", "red", 1],
                "width": 12,
                "height": 14,
                "marker": "full-hit-must-not-render",
                "bounds": [1, 2, 3, 4],
            },
            {
                "op": "full",
                "key": "string-key",
                "width": 32,
                "height": 24,
                "marker": "string-entry",
                "bounds": [0, 0, 0, 0],
            },
            {
                "op": "cropped",
                "key": ["crop", "blue"],
                "width": 100,
                "height": 80,
                "marker": "crop-first",
                "bounds": [10, 20, 30, 40],
            },
            {
                "op": "cropped",
                "key": ["crop", "blue"],
                "width": 4,
                "height": 5,
                "marker": "crop-hit-must-not-render",
                "bounds": [1, 2, 3, 4],
            },
            {
                "op": "cropped",
                "key": ["empty", "bounds"],
                "width": 20,
                "height": 30,
                "marker": "empty-bounds",
                "bounds": [0, 0, 0, 0],
                "anchor": [2, 3],
            },
            {
                "op": "full",
                "key": ["prefix", "shared"],
                "width": 50,
                "height": 50,
                "marker": "prefix-full",
                "bounds": [0, 0, 10, 10],
            },
            {
                "op": "cropped",
                "key": ["prefix", "shared"],
                "width": 50,
                "height": 50,
                "marker": "prefix-cropped",
                "bounds": [4, 5, 6, 7],
            },
            {
                "op": "cropped",
                "key": ["prefix", "cropped-only"],
                "width": 40,
                "height": 40,
                "marker": "cropped-only",
                "bounds": [2, 3, 4, 5],
            },
            {
                "op": "full",
                "key": "prefix",
                "width": 40,
                "height": 40,
                "marker": "string-prefix",
                "bounds": [0, 0, 8, 8],
            },
            {"op": "invalidate", "prefix": "prefix"},
            {"op": "stats"},
            {
                "op": "cropped",
                "key": ["prefix", "cropped-only"],
                "width": 40,
                "height": 40,
                "marker": "cropped-only-after-invalidate",
                "bounds": [2, 3, 4, 5],
            },
            {
                "op": "full",
                "key": ["prefix", "shared"],
                "width": 50,
                "height": 50,
                "marker": "prefix-full-after-invalidate",
                "bounds": [0, 0, 10, 10],
            },
            {"op": "clear"},
            {"op": "stats"},
        ],
    },
    {
        "name": "small_capacity_eviction",
        "max_cache": 3,
        "operations": [
            {
                "op": "full",
                "key": ["full", 0],
                "width": 10,
                "height": 11,
                "marker": "full-0",
                "bounds": [0, 0, 1, 1],
            },
            {
                "op": "full",
                "key": ["full", 1],
                "width": 12,
                "height": 13,
                "marker": "full-1",
                "bounds": [0, 0, 1, 1],
            },
            {
                "op": "full",
                "key": ["full", 2],
                "width": 14,
                "height": 15,
                "marker": "full-2",
                "bounds": [0, 0, 1, 1],
            },
            {
                "op": "full",
                "key": ["full", 0],
                "width": 99,
                "height": 99,
                "marker": "full-0-after-eviction",
                "bounds": [0, 0, 1, 1],
            },
            {
                "op": "cropped",
                "key": ["cropped", 0],
                "width": 60,
                "height": 60,
                "marker": "cropped-0",
                "bounds": [3, 4, 20, 21],
            },
            {
                "op": "cropped",
                "key": ["cropped", 1],
                "width": 62,
                "height": 62,
                "marker": "cropped-1",
                "bounds": [3, 4, 20, 21],
            },
            {
                "op": "cropped",
                "key": ["cropped", 2],
                "width": 64,
                "height": 64,
                "marker": "cropped-2",
                "bounds": [3, 4, 20, 21],
            },
            {
                "op": "cropped",
                "key": ["cropped", 0],
                "width": 99,
                "height": 99,
                "marker": "cropped-0-after-eviction",
                "bounds": [3, 4, 20, 21],
            },
            {"op": "clear"},
            {"op": "stats"},
        ],
    },
]


class _Rect:
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)


class _SurfaceShim:
    def __init__(self, size=(1, 1), _flags=0):
        self.width, self.height = (int(size[0]), int(size[1]))
        self.bounds = _Rect()
        self.marker = None

    def get_bounding_rect(self, min_alpha=0):
        return self.bounds

    def subsurface(self, rect):
        cropped = _SurfaceShim((rect.width, rect.height))
        cropped.bounds = _Rect(0, 0, rect.width, rect.height)
        cropped.marker = self.marker
        return cropped

    def copy(self):
        copied = _SurfaceShim((self.width, self.height))
        copied.bounds = _Rect(self.bounds.x, self.bounds.y, self.bounds.width, self.bounds.height)
        copied.marker = self.marker
        return copied


class _PygameShim:
    SRCALPHA = 1
    Surface = _SurfaceShim


def _class_block(lines, name):
    start = next(i for i, line in enumerate(lines) if line.startswith(f"class {name}:"))
    if name == "SpriteCache":
        end = next(i for i in range(start + 1, len(lines)) if lines[i] == "_sprite_cache = SpriteCache()")
    else:
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("class ")),
            len(lines),
        )
    return "\n".join(lines[start:end])


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    namespace = {"pygame": _PygameShim()}
    exec(compile(_class_block(lines, "SpriteCache"), SOURCE_TAG, "exec"), namespace)
    return namespace["SpriteCache"]


def _tuple_key(value):
    if isinstance(value, list):
        return tuple(_tuple_key(item) for item in value)
    return value


def _surface_summary(surface):
    return {
        "width": surface.width,
        "height": surface.height,
        "marker": surface.marker,
    }


def _stats(cache):
    return cache.get_stats()


def _run_case(cls, case):
    cls._instance = None
    cache = cls()
    cache._max_cache = case["max_cache"]
    render_calls = 0
    outputs = []

    for operation in case["operations"]:
        op = operation["op"]
        if op in ("full", "cropped"):
            marker = operation["marker"]
            bounds = operation.get("bounds", [0, 0, 0, 0])

            def render(surface, marker=marker, bounds=bounds):
                nonlocal render_calls
                render_calls += 1
                surface.marker = marker
                surface.bounds = _Rect(*bounds)

            key = _tuple_key(operation["key"])
            if op == "full":
                result = cache.get_or_render(
                    key,
                    operation["width"],
                    operation["height"],
                    render,
                )
                output = {"surface": _surface_summary(result)}
            else:
                anchor = operation.get("anchor")
                if anchor is not None:
                    anchor = tuple(anchor)
                result = cache.get_or_render_cropped(
                    key,
                    operation["width"],
                    operation["height"],
                    render,
                    anchor,
                )
                output = {
                    "surface": _surface_summary(result[0]),
                    "anchor": [result[1], result[2]],
                }
            output["render_calls"] = render_calls
            output["stats"] = _stats(cache)
            outputs.append(output)
        elif op == "invalidate":
            cache.invalidate(operation.get("prefix"))
            outputs.append({"render_calls": render_calls, "stats": _stats(cache)})
        elif op == "clear":
            cache.clear()
            outputs.append({"render_calls": render_calls, "stats": _stats(cache)})
        elif op == "stats":
            outputs.append({"render_calls": render_calls, "stats": _stats(cache)})
        else:
            raise ValueError(op)

    return {
        "name": case["name"],
        "max_cache": case["max_cache"],
        "operations": case["operations"],
        "outputs": outputs,
    }


def source_fixture():
    cls = _load_class()
    first = cls()
    second = cls()
    return {
        "source": "_render.py::SpriteCache",
        "default_max_cache": 2000,
        "singleton_same_instance": first is second,
        "cases": [_run_case(cls, case) for case in CASES],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    main()
