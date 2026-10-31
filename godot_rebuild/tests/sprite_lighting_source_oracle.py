"""Source oracle for the `lighting.py` port (layer 9aq).

`lighting.py` is the source's per-sprite lighting pass: a directional
gradient over the sprite box, a 1 px rim light on the light-facing contour
and a two-band terminator on the shadow contour, all derived from the alpha
mask with the light coming from the top-left (`LIGHT_DIR = (-1, -1)`).

godot_rebuild draws vectors, not pixel surfaces, so the port keeps the
MASK MATH exact (`contour_masks`, `_canonical`) and adds a vector adapter
(per-vertex gradient + per-edge rim/terminator) in `scripts/ui/
sprite_lighting.gd`. This oracle runs the REAL source functions under a tiny
pygame shim (Surface/Mask/Mask.to_surface/blit with the SDL RGB blend modes -
no pygame needed) and records:

* every tunable constant (direction, rim/shade/band/gradient strengths),
* the 28x28 canonical gradient grids produced by `_canonical`,
* rim / shade / second-band pixel sets of `contour_masks` for small shapes,
* the "too small" rejection threshold (`solid.count() < 24`),
* the finished `apply()` output pixels for a 28x28 box (gradient resample is
  the identity there, so the whole pass is exact) and for a gradient-free
  12x12 sprite, plus the "2 px wide" and "no solid pixels" guards,
* `_bbox_of` boxes and the `_sized` / `reset_gradient_cache` grid identity.

Run: python godot_rebuild/tests/sprite_lighting_source_oracle.py [--check]
"""
import ast
import json
import math
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


def _clamp8(value):
    return max(0, min(255, int(value)))


class _View:
    """pygame `subsurface`: a rectangle of another surface, sharing pixels."""

    def __init__(self, parent, rect):
        self._parent = parent
        self._ox, self._oy = int(rect.left), int(rect.top)
        self._w, self._h = int(rect.width), int(rect.height)

    def get_size(self):
        return (self._w, self._h)

    def get_width(self):
        return self._w

    def get_height(self):
        return self._h

    def get_at(self, pos):
        return self._parent.get_at((self._ox + int(pos[0]), self._oy + int(pos[1])))

    def set_at(self, pos, color):
        self._parent.set_at((self._ox + int(pos[0]), self._oy + int(pos[1])), color)

    def blit(self, source, dest=(0, 0), area=None, special_flags=0):
        _blit(self, source, dest, area, special_flags)


class _Surface:
    """Pixel store: (x, y) -> (r, g, b, a) with the SDL blit modes the pass uses."""

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
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self._w and 0 <= y < self._h:
            self.pixels[(x, y)] = tuple(int(c) for c in color)

    def get_at(self, pos):
        return self.pixels.get((int(pos[0]), int(pos[1])), (0, 0, 0, 0))

    def copy(self):
        clone = _Surface((self._w, self._h))
        clone.pixels = dict(self.pixels)
        return clone

    def fill(self, color):
        color = tuple(int(c) for c in color)
        for y in range(self._h):
            for x in range(self._w):
                self.pixels[(x, y)] = color

    def subsurface(self, rect):
        return _View(self, rect)

    def blit(self, source, dest=(0, 0), area=None, special_flags=0):
        _blit(self, source, dest, area, special_flags)

    def solid_pixels(self):
        return {
            cell: color for cell, color in self.pixels.items() if color[3] > 0
        }


def _blit(dest, source, origin, area, special_flags):
    """Copy / BLEND_RGB_MULT (`d*s/255`) / BLEND_RGB_ADD (`min(255, d+s)`)."""
    ox, oy = int(origin[0]), int(origin[1])
    sx0, sy0 = (0, 0) if area is None else (int(area.left), int(area.top))
    sw, sh = source.get_size()
    if area is not None:
        sw, sh = int(area.width), int(area.height)
    for y in range(sh):
        for x in range(sw):
            src = source.get_at((sx0 + x, sy0 + y))
            if src[3] == 0:
                continue
            dst = dest.get_at((ox + x, oy + y))
            if special_flags == 0:
                out = src
            elif special_flags == 1:          # BLEND_RGB_MULT
                out = tuple(src[c] * dst[c] // 255 for c in range(3)) + (dst[3],)
            elif special_flags == 2:          # BLEND_RGB_ADD
                out = tuple(_clamp8(src[c] + dst[c]) for c in range(3)) + (dst[3],)
            else:
                raise _Error("unsupported blend flag")
            dest.set_at((ox + x, oy + y), out)


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

    def to_surface(self, setcolor=None, unsetcolor=None):
        surface = _Surface((self._w, self._h))
        surface.fill(unsetcolor or (0, 0, 0, 0))
        for cell in self.cells:
            surface.set_at(cell, setcolor or (255, 255, 255, 255))
        return surface


def _from_surface(surface, threshold=127):
    w, h = surface.get_size()
    cells = {(x, y) for x in range(w) for y in range(h)
             if surface.get_at((x, y))[3] > threshold}
    return _Mask((w, h), cells)


def _axis(index, size, steps):
    """Bilinear sample position of dest index: (a, b, fraction)."""
    src = (index + 0.5) * steps / size - 0.5
    low = math.floor(src)
    a = max(0, min(steps - 1, low))
    b = max(0, min(steps - 1, low + 1))
    return a, b, src - low


def _rnd(value):
    """pygame's 8-bit rounding is half up; GDScript `roundf` matches."""
    return int(math.floor(value + 0.5))


def _smoothscale(surface, size):
    """Bilinear resample - the native `sized_grid` sampler (see D2)."""
    w, h = int(size[0]), int(size[1])
    sw, sh = surface.get_size()
    out = _Surface((w, h))
    for y in range(h):
        y0, y1, fy = _axis(y, h, sh)
        for x in range(w):
            x0, x1, fx = _axis(x, w, sw)
            p00, p01 = surface.get_at((x0, y0)), surface.get_at((x1, y0))
            p10, p11 = surface.get_at((x0, y1)), surface.get_at((x1, y1))
            color = []
            for channel in range(4):
                top = p00[channel] + (p01[channel] - p00[channel]) * fx
                bottom = p10[channel] + (p11[channel] - p10[channel]) * fx
                color.append(_clamp8(_rnd(top + (bottom - top) * fy)))
            out.set_at((x, y), tuple(color))
    return out


def _load_lighting():
    shim = types.ModuleType("pygame")
    shim.SRCALPHA = 1
    shim.Surface = _Surface
    shim.Mask = _Mask
    shim.Rect = _Rect
    shim.error = _Error
    shim.mask = types.SimpleNamespace(from_surface=_from_surface)
    shim.transform = types.SimpleNamespace(smoothscale=_smoothscale)
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


TARGET = "scripts/ui/sprite_lighting.gd"
CLASSIFICATION = {
    # Constants: every tunable lands as a `const` with the source value.
    "LIGHT_DIR": ("data", TARGET, "const LIGHT_DIR := Vector2i(-1, -1)"),
    "RIM_ADD": ("data", TARGET, "const RIM_ADD := Vector3i(30, 26, 44)"),
    "SHADE_MUL": ("data", TARGET, "const SHADE_MUL := 168"),
    "BAND2_RATIO": ("data", TARGET, "const BAND2_RATIO := 0.42"),
    "MASK_ALPHA": ("data", TARGET, "const MASK_ALPHA := 170"),
    "GRADIENT_ENABLED": ("data", TARGET, "const GRADIENT_ENABLED := true"),
    "GRAD_DARK": ("data", TARGET, "const GRAD_DARK := 205"),
    "GRAD_LIGHT": ("data", TARGET, "const GRAD_LIGHT := 255"),
    "GRAD_SHEEN": ("data", TARGET, "const GRAD_SHEEN := 22"),
    "_GRAD_STEPS": ("data", TARGET, "const GRAD_STEPS := 28"),
    # Caches: the resampled-box cache is ported, the canonical one is not.
    "_SIZE_CACHE": ("ported", TARGET, "static var _size_cache: Dictionary = {}"),
    "_CANON_CACHE": ("deviation", "", ""),
    # Functions.
    "_shifted_mask": ("ported", TARGET, "static func rim_shade_cells("),
    "_canonical": ("ported", TARGET, "static func canonical_table("),
    "_sized": ("ported", TARGET, "static func sized_grid("),
    "reset_gradient_cache": ("ported", TARGET, "static func reset_gradient_cache("),
    "contour_masks": ("ported", TARGET, "static func contour_masks("),
    "apply": ("ported", TARGET, "static func apply("),
    "_bbox_of": ("ported", TARGET, "static func bbox_of("),
    "apply_to_rig": ("ported", TARGET, "static func apply_to_rig("),
    # The pygame binding itself: the rebuild has no pixel API to bind to.
    "import:pygame": ("folded", TARGET, "## Port of `lighting.py`"),
}
DEVIATIONS = ["_CANON_CACHE"]


def _inventory():
    """Line/function/constant counts of the 239-line module."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    assigns = [target.id for node in tree.body if isinstance(node, ast.Assign)
               for target in node.targets if isinstance(target, ast.Name)]
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    lines = len(SOURCE.read_text(encoding="utf-8").splitlines())
    return functions, assigns, len(imports), lines


def _symbols():
    """Every callable + constant + the module import, classified once."""
    functions, assigns, imports, lines = _inventory()
    rows = {}
    for name in functions + assigns:
        assert name in CLASSIFICATION, "simbol belum terklasifikasi: %s" % name
        rows[name] = CLASSIFICATION[name]
    assert imports, "lighting.py imports pygame"
    rows["import:pygame"] = CLASSIFICATION["import:pygame"]
    kinds = {}
    for row in rows.values():
        kinds[row[0]] = kinds.get(row[0], 0) + 1
    return {
        "file": {
            "file": "lighting.py",
            "lines": lines,
            "classes": 0,
            "functions": len(functions),
            "assigns": len(assigns),
            "imports": imports,
            "symbols": len(rows),
        },
        "symbols": {"count": len(rows), "kinds": kinds, "items": sorted(rows)},
        "classification": {
            symbol: {"kind": kind, "target": target, "token": token}
            for symbol, (kind, target, token) in rows.items()
        },
        "deviations": DEVIATIONS,
    }


def _pixels(surface):
    """Every non-transparent pixel as [x, y, r, g, b], row-major order."""
    out = []
    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            color = surface.get_at((x, y))
            if color[3] > 0:
                out.append([x, y, color[0], color[1], color[2]])
    return out


def _alpha_ok(surface):
    return all(color[3] == 255 for color in surface.pixels.values() if color[3] > 0)


def _apply_cases(src):
    """The finished `apply()` pass: two exact cases plus the source guards."""
    cases = {}
    # 28x28: `_sized(28, 28)` is the identity, so the gradient resample never
    # enters the comparison - the whole pass is exact.
    wide = _shape_surface(28, 28, _rect_cells(4, 4, 20, 20))
    before = _pixels(wide)
    src["apply"](wide)
    cases["gradient28"] = {
        "width": 28, "height": 28, "gradient": True,
        "cells": sorted([list(c) for c in _rect_cells(4, 4, 20, 20)]),
        "input": before, "output": _pixels(wide), "alpha_kept": _alpha_ok(wide),
    }
    # 12x12 with the gradient off: terminator + rim only, no resample at all.
    flat = _shape_surface(12, 12, SHAPES["square"][2])
    before_flat = _pixels(flat)
    src["apply"](flat, gradient=False)
    cases["flat12"] = {
        "width": 12, "height": 12, "gradient": False,
        "cells": sorted([list(c) for c in SHAPES["square"][2]]),
        "input": before_flat, "output": _pixels(flat), "alpha_kept": _alpha_ok(flat),
    }
    # 40x40 sprite lit through a 28x28 reference box at the origin: the box
    # is exactly the canonical size, so the resample stays the identity while
    # the gradient only covers the top-left corner (source `box` argument).
    boxed = _shape_surface(40, 40, _rect_cells(2, 2, 36, 36))
    boxed_before = _pixels(boxed)
    src["apply"](boxed, box=(0, 0, 28, 28))
    cases["box28"] = {
        "width": 40, "height": 40, "gradient": True,
        "cells": sorted([list(c) for c in _rect_cells(2, 2, 36, 36)]),
        "box": [0, 0, 28, 28],
        "input": boxed_before, "output": _pixels(boxed), "alpha_kept": _alpha_ok(boxed),
    }
    # Guards: 2 px wide, no solid pixel, and below the 24-cell floor.
    thin = _shape_surface(2, 6, _rect_cells(0, 0, 2, 6))
    thin_before = _pixels(thin)
    src["apply"](thin)
    cases["guard_thin"] = {
        "width": 2, "height": 6, "gradient": True,
        "cells": sorted([list(c) for c in _rect_cells(0, 0, 2, 6)]),
        "input": thin_before, "output": _pixels(thin), "alpha_kept": _alpha_ok(thin),
    }
    empty = _shape_surface(12, 12, set())
    src["apply"](empty)
    cases["guard_empty"] = {
        "width": 12, "height": 12, "gradient": True, "cells": [],
        "input": [], "output": _pixels(empty), "alpha_kept": True,
    }
    tiny = _shape_surface(8, 8, _rect_cells(1, 1, 4, 5))
    tiny_before = _pixels(tiny)
    src["apply"](tiny)
    cases["guard_tiny"] = {
        "width": 8, "height": 8, "gradient": True,
        "cells": sorted([list(c) for c in _rect_cells(1, 1, 4, 5)]),
        "input": tiny_before, "output": _pixels(tiny), "alpha_kept": _alpha_ok(tiny),
    }
    return cases


def _bbox_cases(src):
    cases = {}
    for name, (w, h, cells) in SHAPES.items():
        surface = _shape_surface(w, h, cells)
        box = src["_bbox_of"](surface, src["MASK_ALPHA"])
        cases[name] = list(box) if box is not None else None
    empty = src["_bbox_of"](_shape_surface(12, 12, set()), src["MASK_ALPHA"])
    cases["empty"] = list(empty) if empty is not None else None
    return cases


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
        "apply": _apply_cases(src),
        "bbox": _bbox_cases(src),
        "inventory": _symbols(),
        "sized_identity": {
            "steps": n,
            "grid_28": [mul_grid[index] for index in range(16)],
            "grid_12": [src["_sized"](12, 12)[0].get_at((x, y))[0]
                        for y in range(4) for x in range(4)],
        },
    }


def main(argv):
    fixture = lighting_fixture()
    assert fixture["light_dir"] == [-1, -1]
    assert fixture["canonical_mul"][0] == fixture["grad_light"]
    assert fixture["canonical_mul"][-1] == fixture["grad_dark"]
    assert fixture["shapes"]["tiny"]["rejected"] is True
    assert fixture["shapes"]["square"]["rejected"] is False
    # The finished pass really moves pixels and keeps every alpha byte.
    gradient = fixture["apply"]["gradient28"]
    assert gradient["alpha_kept"] is True
    assert gradient["input"] != gradient["output"]
    for name in ("guard_thin", "guard_empty", "guard_tiny"):
        case = fixture["apply"][name]
        assert case["input"] == case["output"], name
    assert fixture["bbox"]["square"] == [2, 2, 8, 8]
    assert fixture["bbox"]["empty"] is None
    assert fixture["sized_identity"]["grid_28"][0] == fixture["grad_light"]
    text = json.dumps(fixture, indent=2) + "\n"
    if "--check" in argv:
        current = FIXTURE.read_text(encoding="utf-8") if FIXTURE.exists() else ""
        print("OK" if current == text else "MISMATCH %s" % FIXTURE)
        return 0 if current == text else 1
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(text, encoding="utf-8")
    print("wrote", FIXTURE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
