"""Recording pygame shim shared by the draw-source oracles of layers 9be-9bi.

The real draw methods are harvested from the source files with `ast` and run
against these stand-ins. Every draw call lands in `Surface.ops`; blitting an
off-screen surface flattens its ops into the destination (coordinates shifted,
surface alpha folded into `mult`), so a fixture holds screen-space ops in
source order:
  rect {rect, color, mult, width, radius}; circle {center, radius, color, mult, width}
  line {a, b, color, mult, width}; polygon {points, color, mult, width}
  fill {rect, color, mult, blend}; darken / flash {alpha, mult}
  text {text, size, style, color, mult, pos(top-left)}
`color` is RGBA 0..255 and `mult` the surface alpha (255 = opaque). Text is
measured with `int(size * GLYPH_FACTOR)` px per glyph and a height of `size`,
the same fake metrics the level intro oracle uses; the layouts take the
measure function as a parameter, so the view can pass the real font.
"""
import ast
import contextlib
import sys
import types
from pathlib import Path

GLYPH_FACTOR = 0.55
SRCALPHA = 65536
BLEND_RGB_ADD = 1
BLEND_RGB_MULT = 3


def num(value):
    value = float(value)
    return int(value) if value.is_integer() else value


def rgba(color):
    values = [num(channel) for channel in color]
    return values if len(values) == 4 else values + [255]


def glyph_width(size):
    return int(size * GLYPH_FACTOR)


class Rect:
    def __init__(self, x, y=None, w=None, h=None):
        if y is None:
            x, y, w, h = x
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    width = property(lambda s: s.w)
    height = property(lambda s: s.h)
    left = property(lambda s: s.x)
    top = property(lambda s: s.y)
    right = property(lambda s: s.x + s.w)
    bottom = property(lambda s: s.y + s.h)
    centerx = property(lambda s: s.x + s.w // 2)
    centery = property(lambda s: s.y + s.h // 2)
    size = property(lambda s: (s.w, s.h))

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))


class Surface:
    def __init__(self, size, *_args, **_kwargs):
        self.w, self.h = int(size[0]), int(size[1])
        self.ops = []
        self.alpha = 255

    def get_size(self):
        return (self.w, self.h)

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def set_alpha(self, value):
        self.alpha = int(value)

    def fill(self, color, rect=None, special_flags=0):
        box = [0, 0, self.w, self.h] if rect is None else list(Rect(rect))
        self.ops.append({"kind": "fill", "rect": box, "color": rgba(color),
                         "mult": 255, "blend": int(special_flags)})

    def get_rect(self, **anchors):
        x, y = 0, 0
        if "center" in anchors:
            x = int(anchors["center"][0]) - self.w // 2
            y = int(anchors["center"][1]) - self.h // 2
        elif "topleft" in anchors:
            x, y = int(anchors["topleft"][0]), int(anchors["topleft"][1])
        return Rect(x, y, self.w, self.h)

    def blit(self, src, dest, *_args, **_kwargs):
        dx, dy = (dest.x, dest.y) if isinstance(dest, Rect) else (int(dest[0]), int(dest[1]))
        if isinstance(src, Text):
            self.ops.append({"kind": "text", "text": src.text, "size": src.font_size,
                             "style": src.style, "color": rgba(src.color),
                             "mult": src.alpha, "pos": [dx, dy]})
            return
        for op in src.ops:
            moved = dict(op)
            moved["mult"] = int(op["mult"] * src.alpha / 255)
            if "rect" in op:
                moved["rect"] = [op["rect"][0] + dx, op["rect"][1] + dy, op["rect"][2],
                                 op["rect"][3]]
            if "center" in op:
                moved["center"] = [num(op["center"][0] + dx), num(op["center"][1] + dy)]
            if "a" in op:
                moved["a"] = [num(op["a"][0] + dx), num(op["a"][1] + dy)]
                moved["b"] = [num(op["b"][0] + dx), num(op["b"][1] + dy)]
            if "points" in op:
                moved["points"] = [[num(p[0] + dx), num(p[1] + dy)] for p in op["points"]]
            if "pos" in op:
                moved["pos"] = [op["pos"][0] + dx, op["pos"][1] + dy]
            self.ops.append(moved)


class Text(Surface):
    def __init__(self, text, font_size, style, color):
        super().__init__((glyph_width(font_size) * len(text), font_size))
        self.text, self.font_size, self.style, self.color = text, font_size, style, color


class Font:
    def __init__(self, font_size, style):
        self.font_size, self.style = font_size, style

    def render(self, text, _antialias, color):
        return Text(text, self.font_size, self.style, color)


class Draw:
    @staticmethod
    def rect(surface, color, rect, width=0, border_radius=0, **_kwargs):
        surface.ops.append({"kind": "rect", "rect": list(Rect(rect)), "color": rgba(color),
                            "mult": 255, "width": int(width), "radius": int(border_radius)})

    @staticmethod
    def circle(surface, color, center, radius, width=0, **_kwargs):
        surface.ops.append({"kind": "circle", "center": [num(center[0]), num(center[1])],
                            "radius": num(radius), "color": rgba(color), "mult": 255,
                            "width": int(width)})

    @staticmethod
    def line(surface, color, start, end, width=1):
        surface.ops.append({"kind": "line", "a": [num(start[0]), num(start[1])],
                            "b": [num(end[0]), num(end[1])], "color": rgba(color),
                            "mult": 255, "width": int(width)})

    @staticmethod
    def polygon(surface, color, points, width=0):
        surface.ops.append({"kind": "polygon",
                            "points": [[num(p[0]), num(p[1])] for p in points],
                            "color": rgba(color), "mult": 255, "width": int(width)})


class Transform:
    @staticmethod
    def scale(surface, size):
        """Uniform nearest-neighbour scale, modelled on the geometry of circle ops."""
        factor = size[0] / surface.w
        scaled = Surface(size)
        for op in surface.ops:
            if op["kind"] != "circle":
                raise NotImplementedError("scale() only models circle ops, got " + op["kind"])
            moved = dict(op)
            moved["center"] = [num(op["center"][0] * factor), num(op["center"][1] * factor)]
            moved["radius"] = num(op["radius"] * factor)
            scaled.ops.append(moved)
        return scaled


def make_pygame(clock):
    """`clock["ticks"]` backs `pygame.time.get_ticks()`."""
    module = types.ModuleType("pygame")
    module.Surface, module.Rect, module.draw = Surface, Rect, Draw
    module.transform = Transform
    module.SRCALPHA, module.BLEND_RGB_MULT, module.BLEND_RGB_ADD = (
        SRCALPHA, BLEND_RGB_MULT, BLEND_RGB_ADD)
    module.K_SPACE, module.K_ESCAPE = 32, 27
    module.time = types.SimpleNamespace(get_ticks=lambda: clock["ticks"])
    return module


def make_perf(cheap_alpha=True):
    """`mobile.perf` stand-in: darken / flash become one op each (alpha 0 = none)."""
    module = types.ModuleType("mobile.perf")

    def screen_op(kind):
        def paint(target, alpha, *_rest):
            value = max(0, min(255, int(alpha)))
            if value > 0:
                target.ops.append({"kind": kind, "alpha": value, "mult": 255})
        return paint

    class Quality:
        pass

    Quality.cheap_alpha = bool(cheap_alpha)
    module.darken, module.flash, module.Quality = screen_op("darken"), screen_op("flash"), Quality
    return module


def harvest(path, names, kind=(ast.FunctionDef, ast.ClassDef)):
    """Source segments of the named top-level functions / classes of `path`."""
    text = Path(path).read_text(encoding="utf-8")
    found = {node.name: ast.get_source_segment(text, node) for node in ast.parse(text).body
             if isinstance(node, kind) and getattr(node, "name", None) in names}
    missing = set(names) - set(found)
    if missing:
        raise AssertionError("%s not found in %s" % (sorted(missing), Path(path).name))
    return [found[name] for name in names]


@contextlib.contextmanager
def installed(modules):
    """Temporarily put stand-in modules into `sys.modules`, then restore."""
    saved = {name: sys.modules.get(name) for name in modules}
    sys.modules.update(modules)
    try:
        yield
    finally:
        for name, old in saved.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
