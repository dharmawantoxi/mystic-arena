"""Source oracle for the `lighting.py` port (layer 9aq).

`lighting.py` is the source's per-sprite lighting pass: a directional
gradient over the sprite box, a 1 px rim light on the light-facing contour
and a two-band terminator on the shadow contour, all derived from the alpha
mask with the light coming from the top-left (`LIGHT_DIR = (-1, -1)`).

godot_rebuild draws vectors, not pixel surfaces, so the port keeps the
MASK MATH exact (`contour_masks`, `_canonical`) and adds a vector adapter
(per-vertex gradient + per-edge rim/terminator) in `scripts/ui/
sprite_lighting.gd`. This oracle runs the REAL source functions under a tiny
pygame shim (Surface/Mask backed by plain dicts and sets - no pygame needed)
and records:

* every tunable constant (direction, rim/shade/band/gradient strengths),
* the 28x28 canonical gradient grids produced by `_canonical`,
* rim / shade / second-band pixel sets of `contour_masks` for small shapes,
* the "too small" rejection threshold (`solid.count() < 24`).

Run: python godot_rebuild/tests/sprite_lighting_source_oracle.py
"""
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "lighting.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sprite_lighting_source.json"


class _Error(Exception):
    pass


class _Rect:
    def __init__(self, x, y, w, h):
        self.left, self.top, self.width, self.height = x, y, w, h
        self.right, self.bottom = x + w, y + h


class _Surface:
    """Pixel store: (x, y) -> (r, g, b, a). Blits are not needed by the oracle."""

    def __init__(self, size, _flags=0):
        self._w, self._h = int(size[0]), int(size[1])
        self.pixels = {}

    def get_size(self):
        return (self._w, self._h)

    def get_width(self):
        return self._w

    def get_height(self):
        return self._h

    def set_at(self, pos, color):
        self.pixels[(int(pos[0]), int(pos[1]))] = tuple(int(c) for c in color)

    def get_at(self, pos):
        return self.pixels.get((int(pos[0]), int(pos[1])), (0, 0, 0, 0))


class _Mask:
    """Set-backed pygame.Mask covering exactly what lighting.py calls."""

    def __init__(self, size, cells=None):
        self._w, self._h = int(size[0]), int(size[1])
        self.cells = set(cells or ())

    def get_size(self):
        return (self._w, self._h)

    def count(self):
        return len(self.cells)

    def copy(self):
        return _Mask((self._w, self._h), self.cells)

    def draw(self, other, offset):
        dx, dy = int(offset[0]), int(offset[1])
        for (x, y) in other.cells:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self._w and 0 <= ny < self._h:
                self.cells.add((nx, ny))

    def erase(self, other, offset):
        dx, dy = int(offset[0]), int(offset[1])
        for (x, y) in other.cells:
            self.cells.discard((x + dx, y + dy))

    def get_bounding_rects(self):
        if not self.cells:
            return []
        xs = [c[0] for c in self.cells]
        ys = [c[1] for c in self.cells]
        return [_Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)]


def _from_surface(surface, threshold=127):
    w, h = surface.get_size()
    cells = {(x, y) for x in range(w) for y in range(h)
             if surface.get_at((x, y))[3] > threshold}
    return _Mask((w, h), cells)


def _load_lighting():
    shim = types.ModuleType("pygame")
    shim.SRCALPHA = 1
    shim.Surface = _Surface
    shim.Mask = _Mask
    shim.Rect = _Rect
    shim.error = _Error
    shim.mask = types.SimpleNamespace(from_surface=_from_surface)
    shim.transform = types.SimpleNamespace(smoothscale=lambda s, size: s)
    shim.BLEND_RGB_MULT = 1
    shim.BLEND_RGB_ADD = 2
    previous = sys.modules.get("pygame")
    sys.modules["pygame"] = shim
    try:
        namespace = {"__name__": "lighting_oracle_source", "__file__": str(SOURCE)}
        exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)
    finally:
        if previous is not None:
            sys.modules["pygame"] = previous
        else:
            del sys.modules["pygame"]
    return namespace


def _shape_surface(width, height, cells):
    surface = _Surface((width, height))
    for (x, y) in cells:
        surface.set_at((x, y), (200, 120, 80, 255))
    return surface


def _rect_cells(x, y, w, h):
    return {(cx, cy) for cx in range(x, x + w) for cy in range(y, y + h)}


SHAPES = {
    # 8x8 solid square inset in a 12x12 canvas: rim = top row + left column.
    "square": (12, 12, _rect_cells(2, 2, 8, 8)),
    # L shape: a 9x3 bar over a 3x9 column - inner corner gets both sides.
    "ell": (12, 12, _rect_cells(1, 1, 9, 3) | _rect_cells(1, 1, 3, 9)),
    # 4x5 = 20 solid cells: below the 24-cell floor -> contour_masks rejects.
    "tiny": (8, 8, _rect_cells(1, 1, 4, 5)),
}


def _cells(mask):
    return sorted([list(c) for c in mask.cells]) if mask is not None else None


def lighting_fixture():
    src = _load_lighting()
    n = src["_GRAD_STEPS"]
    mul, add = src["_canonical"](src["GRAD_DARK"], src["GRAD_LIGHT"], src["GRAD_SHEEN"])
    mul_grid = [mul.get_at((gx, gy))[0] for gy in range(n) for gx in range(n)]
    add_grid = [list(add.get_at((gx, gy))[:3]) for gy in range(n) for gx in range(n)]
    neutral = int(src["SHADE_MUL"])
    band2 = max(0, min(255, int(255 - (255 - neutral) * src["BAND2_RATIO"])))
    shapes = {}
    for name, (w, h, cells) in SHAPES.items():
        surface = _shape_surface(w, h, cells)
        rim, shade = src["contour_masks"](surface, alpha=src["MASK_ALPHA"])
        outer, inner = src["contour_masks"](surface, alpha=src["MASK_ALPHA"], width=2)
        wide = None
        if inner is not None and shade is not None:
            wide = inner.copy()
            wide.erase(shade.copy(), (0, 0))
        shapes[name] = {
            "width": w, "height": h, "solid": len(cells),
            "cells": sorted([list(c) for c in cells]),
            "rejected": rim is None,
            "rim": _cells(rim), "shade": _cells(shade),
            "outer_rim": _cells(outer), "band2": _cells(wide),
        }
    return {
        "source": "lighting.py (real functions under a dict/set pygame shim)",
        "light_dir": list(src["LIGHT_DIR"]),
        "rim_add": list(src["RIM_ADD"]),
        "shade_mul": neutral,
        "band2_ratio": src["BAND2_RATIO"],
        "band2_mul": band2,
        "mask_alpha": src["MASK_ALPHA"],
        "gradient_enabled": bool(src["GRADIENT_ENABLED"]),
        "grad_dark": src["GRAD_DARK"],
        "grad_light": src["GRAD_LIGHT"],
        "grad_sheen": src["GRAD_SHEEN"],
        "grad_steps": n,
        "min_solid": 24,
        "canonical_mul": mul_grid,
        "canonical_add": add_grid,
        "shapes": shapes,
    }


def main():
    fixture = lighting_fixture()
    assert fixture["light_dir"] == [-1, -1]
    assert fixture["canonical_mul"][0] == fixture["grad_light"]
    assert fixture["canonical_mul"][-1] == fixture["grad_dark"]
    assert fixture["shapes"]["tiny"]["rejected"] is True
    assert fixture["shapes"]["square"]["rejected"] is False
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)


if __name__ == "__main__":
    main()
