#!/usr/bin/env python3
"""Export ui_theme.py to the active Godot project with a pygame oracle.

The contract is AST/text anchored. The oracle exercises the real pygame theme:
primitive icon geometry, cached surface formulas, text layout, and every menu
component in both alpha quality modes. --check is byte-exact and fail-closed.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "ui_theme.py"
CONTRACT = PROJECT / "data/ui_theme.json"
FIXTURE = PROJECT / "tests/fixtures/ui_theme_parity.json"
PYGAME_VERSION = "2.6.1"
sys.path.insert(0, str(ROOT))

ICON_NAMES = [
    "play", "continue", "coin", "pad", "help", "gear", "star", "quit", "lock",
    "speaker", "swords", "monitor", "cloud", "warn", "heart", "check", "back",
    "chevron_l", "chevron_r", "plus", "minus", "skull", "bolt", "crown", "gem",
    "trophy", "shield", "upload", "download",
]
ANCHORS = [
    "return gap.join(list(text))",
    'ell = "…" if _has_glyph(font, "…") else "..."',
    "while len(text) > 1:",
    "t = y / max(1, h - 1)",
    "a = max(4, min(120, int(alpha) // 8 * 8))",
    "aa = int(a * (1 - d) ** 2)",
    "sw, sh = max(4, w // 8), max(4, h // 8)",
    "if len(_GRAD_TEXT_CACHE) > 400:",
    "rect = base.inflate(18, 8) if hover else base",
    "left_min = rect.x + 56",
    "right_max = rect.right - 10",
    "text_cx = base.x + w // 2 + 14",
    "text_cx = (left_min + right_max) / 2",
    "if hover and enabled:",
    "if enabled:\n        btns[bid] = r",
    'if align == "right":',
    "total_w += 10 + font.size(value)[0]",
    "tw = font.size(title)[0] + 28",
    "return tuple(int(c * f) for c in color)",
    "kx = r.right - knob - 6 if is_on else r.x + 6",
    "fill_w = int(w * max(0.0, min(1.0, value)))",
    "if fill_w > 4:",
    "vw = max(110, value_font.size(value)[0] + 26)",
    "vw = min(vw, width - 66)",
    "vx = x + width - vw - 56",
    "return max(min_w, font.size(letter(label))[0] + 36)",
    "thumb_h = max(18, int(height * ratio))",
    "thumb_y = y + int((height - thumb_h) * (scroll_pos / max_scroll))",
    "fw = int(w * max(0.0, min(1.0, ratio)))",
    "if fw > 3:",
    "fw = int(w * max(0.0, min(1.0, frac)))",
    "btns[bid] = rect",
]


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise AssertionError(f"Non-finite ui_theme value: {value!r}")
    return value


def _text(value) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2,
                      allow_nan=False, sort_keys=True) + "\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def _fn(name: str):
    for node in _tree().body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Missing ui_theme function: {name}")


def _palette() -> dict:
    result = {}
    for node in _tree().body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                value = ast.literal_eval(node.value)
                if not isinstance(value, (tuple, list)) or len(value) != 3:
                    continue
                if any(not isinstance(c, int) or not 0 <= c <= 255 for c in value):
                    raise AssertionError(f"Invalid ui_theme palette color: {target.id}")
                result[target.id.lower()] = list(value)
    if len(result) != 32:
        raise AssertionError(f"Expected 32 ui_theme palette colors, got {len(result)}")
    return result


def _expr(fn_name: str, code: str):
    wanted = ast.unparse(ast.parse(code).body[0].value)
    for node in ast.walk(_fn(fn_name)):
        try:
            value = ast.literal_eval(node)
        except (ValueError, TypeError, SyntaxError):
            continue
        if ast.unparse(node) == wanted:
            return _jsonable(value)
    raise AssertionError(f"Missing literal {code!r} in ui_theme.{fn_name}")


def _defaults(fn_name: str) -> dict:
    fn = _fn(fn_name)
    args = fn.args
    positional = args.posonlyargs + args.args
    values = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    palette = _palette()
    result = {}
    for arg, value in zip(positional, values):
        if value is None:
            continue
        if isinstance(value, ast.Name) and value.id.lower() in palette:
            result[arg.arg] = palette[value.id.lower()]
        else:
            try:
                result[arg.arg] = _jsonable(ast.literal_eval(value))
            except (ValueError, TypeError):
                result[arg.arg] = ast.unparse(value)
    for arg, value in zip(args.kwonlyargs, args.kw_defaults):
        if value is not None:
            try:
                result[arg.arg] = _jsonable(ast.literal_eval(value))
            except (ValueError, TypeError):
                result[arg.arg] = ast.unparse(value)
    return result


def _pill_colors() -> dict:
    palette = _palette()
    fn = _fn("pill")
    node = next(n for n in ast.walk(fn) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "colors" for t in n.targets))
    result = {}
    for key, value in zip(node.value.keys, node.value.values):
        row = []
        for item in value.elts:
            if isinstance(item, ast.Name):
                row.append(palette[item.id.lower()])
            else:
                row.append(_jsonable(ast.literal_eval(item)))
        result[ast.literal_eval(key)] = row
    return result


def build_contract() -> dict:
    source_text = SOURCE.read_text(encoding="utf-8")
    for anchor in ANCHORS:
        if anchor not in source_text:
            raise AssertionError(f"ui_theme source anchor drifted: {anchor!r}")
    discovered = set()
    for node in ast.walk(_fn("draw_icon")):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "name":
            for comparator in node.comparators:
                try:
                    value = ast.literal_eval(comparator)
                except (ValueError, TypeError):
                    continue
                discovered.update(value if isinstance(value, tuple) else [value])
    if discovered != set(ICON_NAMES):
        raise AssertionError(f"ui_theme icon set drifted: {discovered ^ set(ICON_NAMES)}")
    perf = ast.parse((ROOT / "mobile/perf.py").read_text(encoding="utf-8"))
    quality = next(n for n in perf.body if isinstance(n, ast.ClassDef) and n.name == "_Quality")
    init = next(n for n in quality.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    cheap_default = None
    for node in ast.walk(init):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "cheap_alpha":
                    cheap_default = ast.literal_eval(node.value)
    if cheap_default is not True:
        raise AssertionError("ui_theme cheap_alpha default must stay True")
    cfg = {
        "surface": {
            "min_size": _expr("_vgrad", "2"), "radial_min": _expr("_radial", "8"),
            "radial_alpha_min": _expr("_radial", "4"), "radial_alpha_max": _expr("_radial", "120"),
            "radial_alpha_step": _expr("_radial", "8"), "radial_pixel_step": _expr("_radial", "2"),
            "shadow_div": _expr("_shadow", "8"), "shadow_min": _expr("_shadow", "4"),
            "gradient_text_cache_limit": _expr("gradient_text", "400"),
        },
        "text": {
            "shadow_color": _expr("draw_text", "(5, 6, 12)"),
            "outline_color": _expr("outline_text", "(8, 9, 18)"),
            "outline_body_bottom": _expr("outline_text", "(196, 138, 40)"),
            "ellipsis": _expr("fit_ellipsis", '"…"'), "ellipsis_fallback": _expr("fit_ellipsis", '"..."'),
        },
        "ticks": {"color": _palette()["gold"]},
        "panel": {
            "radius": _expr("panel", "12"), "shadow_color": _expr("panel", "(6, 7, 14)"),
            "shadow_move": [3, 4], "shadow_offset": [-4, -4],
        },
        "button": {
            "hover_inflate": [_expr("button", "18"), _expr("button", "8")],
            "glow_pad": [44, 36], "glow_offset": [-22, -18], "glow_alpha": _expr("button", "74"),
            "cheap_glow_inflate": [10, 10], "cheap_glow_width": _expr("button", "2"),
            "cheap_glow_radius": _expr("button", "14"), "shadow_offset": [-2, -2],
            "top_hover": _expr("button", "(44, 52, 86)"), "top_normal": _expr("button", "(34, 41, 70)"),
            "bot_hover": _expr("button", "(24, 29, 52)"), "bot_normal": _expr("button", "(17, 21, 38)"),
            "highlight": _expr("button", "(255, 255, 255)"), "highlight_inset": _expr("button", "12"),
            "accent_rect": [6, 10, 4, 20], "accent_radius": _expr("button", "2"),
            "accent_glow_rect": [4, 8, 8, 16], "accent_glow_alpha": _expr("button", "70"),
            "accent_glow_radius": _expr("button", "3"),
            "badge_center_x": _expr("button", "34"), "badge_radius": _expr("button", "17"),
            "badge_bg": _expr("button", "(12, 14, 26)"), "badge_width": _expr("button", "2"),
            "icon_scale": _expr("button", "0.9"), "label_left": _expr("button", "56"),
            "label_right": _expr("button", "10"), "label_shift": _expr("button", "14"),
        },
        "pill": {
            "colors": _pill_colors(),
            "radius": _expr("pill", "7"), "hover_top": _expr("pill", "18"), "hover_bot": _expr("pill", "14"),
            "glow_pad": [30, 24], "glow_offset": [-15, -12], "glow_alpha": _expr("pill", "66"),
            "icon_x": _expr("pill", "22"), "icon_scale": _expr("pill", "0.8"),
        },
        "chip": {
            "base_w": _expr("chip", "26"), "icon_w": _expr("chip", "22"), "height": _expr("chip", "30"),
            "top": _expr("chip", "(32, 38, 64)"), "bottom": _expr("chip", "(18, 22, 40)"),
            "cheap_fill": _expr("chip", "(22, 26, 46)"), "icon_x": _expr("chip", "14"),
            "icon_scale": _expr("chip", "0.75"), "text_y": _expr("chip", "7"), "value_gap": _expr("chip", "10"),
        },
        "header": {
            "icon_offset": [10, 11], "icon_scale": _expr("section_header", "0.9"),
            "text_x": _expr("section_header", "28"), "rule_gap": _expr("section_header", "14"),
            "rule_y": _expr("section_header", "14"), "underline_y": _expr("section_header", "26"),
            "return_y": _expr("section_header", "34"), "dim_factor": _expr("_dim", "0.55"),
        },
        "toggle": {
            "on_top": _expr("toggle", "(70, 190, 96)"), "on_top_hover": _expr("toggle", "(92, 214, 118)"),
            "on_bot": _expr("toggle", "(34, 116, 58)"), "on_bot_hover": _expr("toggle", "(46, 138, 70)"),
            "on_edge": _expr("toggle", "(120, 235, 145)"), "on_edge_hover": _expr("toggle", "(160, 255, 180)"),
            "off_top": _expr("toggle", "(74, 78, 100)"), "off_top_hover": _expr("toggle", "(92, 96, 118)"),
            "off_bot": _expr("toggle", "(44, 48, 68)"), "off_bot_hover": _expr("toggle", "(56, 60, 80)"),
            "off_edge": _expr("toggle", "(120, 126, 150)"), "off_edge_hover": _expr("toggle", "(150, 156, 180)"),
            "knob": _expr("toggle", "18"), "knob_inset": _expr("toggle", "6"),
            "knob_shadow": _expr("toggle", "(12, 14, 24)"), "knob_fill": _expr("toggle", "(245, 248, 255)"),
            "label_offset": _expr("toggle", "8"), "on_text": _expr("toggle", "(210, 255, 220)"),
        },
        "slider": {
            "track_h": _expr("slider", "8"), "track_color": _expr("slider", "(34, 38, 58)"),
            "border_color": _expr("slider", "(120, 110, 86)"), "radius": _expr("slider", "4"),
            "min_fill": _expr("slider", "4"), "fill_bottom": _expr("slider", "(196, 138, 40)"),
            "glow_size": _expr("slider", "36"), "glow_alpha": _expr("slider", "80"),
            "knob_shadow": _expr("slider", "(12, 14, 24)"), "knob_fill": _expr("slider", "(245, 248, 255)"),
            "knob_outer": _expr("slider", "11"), "knob_inner": _expr("slider", "8"),
        },
        "cycler": {
            "label_y": _expr("option_cycler", "10"), "min_vw": _expr("option_cycler", "110"),
            "value_pad": _expr("option_cycler", "26"), "width_reserve": _expr("option_cycler", "66"),
            "right_reserve": _expr("option_cycler", "56"), "vy": _expr("option_cycler", "7"),
            "vh": _expr("option_cycler", "30"), "radius": _expr("option_cycler", "6"),
            "top": _expr("option_cycler", "(40, 48, 80)"), "bottom": _expr("option_cycler", "(20, 24, 44)"),
            "cheap_fill": _expr("option_cycler", "(28, 34, 58)"), "edge": _expr("option_cycler", "(96, 106, 138)"),
            "chevron_w": _expr("option_cycler", "24"), "chevron_gap": _expr("option_cycler", "6"),
            "chevron_top_hover": _expr("option_cycler", "(64, 74, 110)"),
            "chevron_top": _expr("option_cycler", "(42, 48, 74)"),
            "chevron_bottom": _expr("option_cycler", "(26, 30, 52)"),
            "chevron_edge_hover": _expr("option_cycler", "(150, 160, 196)"),
            "chevron_icon": _expr("option_cycler", "(200, 210, 240)"), "icon_scale": _expr("option_cycler", "0.6"),
        },
        "tab": {
            "min_w": _expr("tab_width", "150"), "padding": _expr("tab_width", "36"), "radius": _expr("tab", "8"),
            "active_top": _expr("tab", "(46, 56, 92)"), "active_bot": _expr("tab", "(26, 32, 58)"),
            "underline": [8, 4, 16, 3], "underline_radius": _expr("tab", "1"),
            "hover_top": _expr("tab", "(34, 39, 62)"), "normal_top": _expr("tab", "(22, 26, 44)"),
            "hover_bot": _expr("tab", "(20, 24, 42)"), "normal_bot": _expr("tab", "(15, 18, 32)"),
            "hover_edge": _expr("tab", "(120, 130, 160)"), "normal_edge": _expr("tab", "(72, 80, 106)"),
        },
        "title": {
            "font_size": _expr("screen_title", "64"), "sub_font_size": _expr("screen_title", "30"),
            "glow_size": [620, 150], "glow_color": _expr("screen_title", "(255, 205, 90)"),
            "glow_alpha": _expr("screen_title", "46"), "glow_offset": [-310, -62],
            "ornament_y": _expr("screen_title", "52"), "line_outer": _expr("screen_title", "220"),
            "line_inner": _expr("screen_title", "18"), "diamond_x": _expr("screen_title", "8"),
            "diamond_y": _expr("screen_title", "7"), "dot_x": _expr("screen_title", "230"),
            "dot_radius": _expr("screen_title", "3"), "sub_pad": _expr("screen_title", "56"),
            "sub_y": _expr("screen_title", "12"), "sub_h": _expr("screen_title", "44"),
            "sub_radius": _expr("screen_title", "10"), "sub_top": _expr("screen_title", "(26, 32, 58)"),
            "sub_bottom": _expr("screen_title", "(14, 18, 34)"), "sub_cheap": _expr("screen_title", "(16, 20, 38)"),
            "sub_ticks": [8, 1, 3],
        },
        "back": {"width": _expr("back_button", "200"), "height": _expr("back_button", "42"),
                 "font_size": _expr("back_button", "26")},
        "scroll": {"width": _expr("scroll_indicator", "6"), "radius": _expr("scroll_indicator", "3"),
                   "track_color": _expr("scroll_indicator", "(28, 32, 52)"), "min_thumb": _expr("scroll_indicator", "18"),
                   "fill_bottom": _expr("scroll_indicator", "(196, 138, 40)")},
        "hp": {"track_color": _expr("hp_bar", "(16, 18, 30)"), "border_color": _expr("hp_bar", "(86, 92, 120)"),
               "lighten": _expr("hp_bar", "50"), "min_fill": _expr("hp_bar", "3")},
        "progress": {"track_color": _expr("progress_bar", "(30, 34, 54)"), "border_color": _expr("progress_bar", "(96, 96, 126)"),
                     "lighten": _expr("progress_bar", "40"), "min_fill": _expr("progress_bar", "3"),
                     "height": _expr("progress_bar", "8")},
    }
    palette = _palette()
    defaults = {name: _defaults(name) for name in (
        "letter", "draw_text", "outline_text", "draw_icon", "corner_ticks", "panel",
        "panel_solid", "button", "pill", "chip", "section_header", "_dim", "toggle",
        "slider", "option_cycler", "tab_width", "tab", "screen_title", "back_button",
        "scroll_indicator", "hp_bar", "progress_bar")}
    return {
        "schema": 1, "source": "ui_theme.py", "source_sha256": _sha(SOURCE.read_bytes()),
        "pygame_version": PYGAME_VERSION, "palette": palette, "config": cfg,
        "defaults": defaults, "icons": ICON_NAMES, "cheap_alpha_default": cheap_default,
        "anchors": ANCHORS,
        "functions": [n.name for n in _tree().body if isinstance(n, ast.FunctionDef)],
    }


class FakeFont:
    def __init__(self, size):
        self.size_value = int(size)

    def size(self, text):
        return (len(str(text)) * self.size_value // 2, self.size_value)

    def render(self, text, aa, color):
        width, height = self.size(text)
        surf = _TRACK_SURFACE((max(1, width), max(1, height)), 0x00008000)
        surf.meta = {"op": "text", "text": str(text), "color": list(color), "shadow": False}
        return surf


_TRACK_SURFACE = None


def _rect(value):
    import pygame
    r = pygame.Rect(value)
    return [r.x, r.y, r.w, r.h]


def _point(value):
    return [float(value[0]), float(value[1])]


def build_oracle() -> dict:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    import pygame
    pygame.init()
    if pygame.__version__ != PYGAME_VERSION:
        raise AssertionError(f"pygame {pygame.__version__} != pinned {PYGAME_VERSION}")
    module = importlib.import_module("ui_theme")
    global _TRACK_SURFACE
    palette = _palette()

    class TrackSurface(pygame.Surface):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.ops = []
            self.meta = None

        def blit(self, src, dest=None, *args, **kwargs):
            pos = dest if dest is not None else (0, 0)
            if hasattr(pos, "x"):
                pos = (pos.x, pos.y)
            meta = getattr(src, "meta", None)
            if meta is not None:
                row = dict(meta)
                if row["op"] == "text":
                    row["center"] = [int(pos[0]) + src.get_width() // 2,
                                     int(pos[1]) + src.get_height() // 2]
                else:
                    row["pos"] = _point(pos)
                self.ops.append(row)
            return pygame.Surface.blit(self, src, dest, *args, **kwargs)

    _TRACK_SURFACE = TrackSurface
    screen = TrackSurface((1280, 720), pygame.SRCALPHA)
    font = FakeFont(24)

    def surface_stub(kind, w, h, **extra):
        w, h = max(2, int(w)), max(2, int(h))
        stub = TrackSurface((w, h), pygame.SRCALPHA)
        stub.meta = {"op": kind, "size": [w, h], **extra}
        return stub

    def fake_vgrad(w, h, top, bottom, radius=0):
        return surface_stub("gradient", w, h, top=list(top), bottom=list(bottom), radius=int(radius))

    def fake_shadow(w, h, radius=12, alpha=110, spread=4):
        return surface_stub("shadow", int(w) + spread * 2, int(h) + spread * 2,
                            radius=int(radius), alpha=int(alpha), spread=int(spread))

    def fake_radial(w, h, color, alpha):
        return surface_stub("radial", max(8, int(w)), max(8, int(h)), color=list(color), alpha=int(alpha))

    def fake_text(screen, font, text, color, center=None, topleft=None, shadow=True, offset=(2, 2)):
        screen.ops.append({"op": "text", "text": str(text), "color": list(color),
                           "center": _point(center) if center is not None else None,
                           "topleft": _point(topleft) if topleft is not None else None,
                           "shadow": bool(shadow), "offset": list(offset), "font_size": font.size_value})
        return font.render(text, True, color)

    def fake_icon(screen, name, cx, cy, color, s=1.0):
        screen.ops.append({"op": "icon", "name": name, "center": [float(cx), float(cy)],
                           "color": list(color), "scale": float(s)})

    def fake_ticks(screen, rect, color, length=11, width=2, inset=2):
        screen.ops.append({"op": "ticks", "rect": _rect(rect), "color": list(color),
                           "length": int(length), "width": int(width), "inset": int(inset)})

    def fake_outline(screen, font, text, color, center, outline=(8, 9, 18), width=2,
                     body_top=None, body_bottom=None):
        screen.ops.append({"op": "outline", "text": str(text), "center": _point(center),
                           "outline": list(outline), "width": int(width),
                           "body_top": list(body_top) if body_top else None,
                           "body_bottom": list(body_bottom) if body_bottom else None,
                           "font_size": font.size_value})

    primitive_ops = []
    capture_ops = None

    def record(op):
        def wrapper(surface, *args, **kwargs):
            target = capture_ops if capture_ops is not None else primitive_ops
            if op == "rect":
                color, box = args[0], args[1]
                target.append({"op": op, "color": list(color), "rect": _rect(box),
                                      "width": int(args[2]) if len(args) > 2 else int(kwargs.get("width", 0)),
                                      "radius": int(kwargs.get("border_radius", 0))})
            elif op == "line":
                color, start, end = args[:3]
                target.append({"op": op, "color": list(color), "start": _point(start),
                                      "end": _point(end), "width": int(args[3]) if len(args) > 3 else 1})
            elif op == "circle":
                color, center, radius = args[:3]
                target.append({"op": op, "color": list(color), "center": _point(center),
                                      "radius": float(radius), "width": int(args[3]) if len(args) > 3 else 0})
            elif op == "polygon":
                color, points = args[:2]
                target.append({"op": op, "color": list(color), "points": [_point(p) for p in points],
                                      "width": int(args[2]) if len(args) > 2 else 0})
            elif op == "arc":
                color, box, start, end = args[:4]
                target.append({"op": op, "color": list(color), "rect": _rect(box),
                                      "start": float(start), "end": float(end),
                                      "width": int(args[4]) if len(args) > 4 else 1})
            return getattr(pygame.draw, "_orig_" + op)(surface, *args, **kwargs)
        return wrapper

    draw_patches = {}
    for op in ("rect", "line", "circle", "polygon", "arc"):
        setattr(pygame.draw, "_orig_" + op, getattr(pygame.draw, op))
        draw_patches[op] = record(op)

    def component(name, cheap, *args, **kwargs):
        nonlocal capture_ops
        screen.ops.clear()
        capture_ops = screen.ops
        btns = kwargs.pop("btns", {})
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(module, "cheap_alpha", lambda: cheap))
            stack.enter_context(mock.patch.object(module, "_vgrad", fake_vgrad))
            stack.enter_context(mock.patch.object(module, "_shadow", fake_shadow))
            stack.enter_context(mock.patch.object(module, "_radial", fake_radial))
            stack.enter_context(mock.patch.object(module, "draw_text", fake_text))
            stack.enter_context(mock.patch.object(module, "draw_icon", fake_icon))
            stack.enter_context(mock.patch.object(module, "corner_ticks", fake_ticks))
            stack.enter_context(mock.patch.object(module, "outline_text", fake_outline))
            stack.enter_context(mock.patch.dict(sys.modules, {"_core": SimpleNamespace(
                get_font=lambda size, style=None: FakeFont(size), title_font=lambda size: FakeFont(size))}))
            for op, fn in draw_patches.items():
                stack.enter_context(mock.patch.object(pygame.draw, op, fn))
            try:
                if name in ("button", "pill", "toggle", "option_cycler", "tab", "back_button"):
                    result = getattr(module, name)(screen, btns, *args, **kwargs)
                else:
                    result = getattr(module, name)(screen, *args, **kwargs)
                ops = list(screen.ops)
            finally:
                capture_ops = None
        if isinstance(result, pygame.Rect):
            result = _rect(result)
        clean_args = [{"font_size": a.size_value} if isinstance(a, FakeFont) else a for a in args]
        clean_kwargs = {k: ({"font_size": v.size_value} if isinstance(v, FakeFont) else v) for k, v in kwargs.items()}
        return {"name": name, "cheap_alpha": cheap, "args": _jsonable(clean_args), "kwargs": _jsonable(clean_kwargs),
                "ops": ops, "result": result, "btns": {k: _rect(v) for k, v in btns.items()}}

    # Helper oracles use the real implementations, not the component stubs.
    text_cases = []
    for text in ("", "PLAY", "Indonesia", "é☀", "A  B"):
        text_cases.append({"text": text, "gap": " ", "result": module.letter(text)})
    ellipsis = []
    for glyph in (True, False):
        for width in (0, 5, 24, 60, 200):
            with mock.patch.object(module, "_has_glyph", lambda font, ch: glyph):
                ellipsis.append({"text": "LONG LABEL", "max_w": width, "glyph": glyph,
                                 "result": module.fit_ellipsis(font, "LONG LABEL", width)})
    gradients = []
    for w, h, radius in ((2, 2, 0), (40, 30, 12), (1, 1, 7), (17, 9, 4)):
        module.clear_caches()
        # Sample the unmasked gradient formula; rounded masking is a native
        # raster approximation and is not part of the row-color oracle.
        surf = module._vgrad(w, h, (10, 20, 30), (200, 150, 100), 0)
        rows = [[y, *surf.get_at((0, y))[:3]] for y in range(surf.get_height())]
        gradients.append({"w": w, "h": h, "top": [10, 20, 30], "bottom": [200, 150, 100],
                          "radius": radius, "size": list(surf.get_size()), "rows": rows})
    radials = []
    for w, h, alpha in ((8, 8, 0), (36, 36, 80), (120, 60, 46), (17, 13, 255)):
        module.clear_caches()
        primitive_ops.clear()
        with contextlib.ExitStack() as stack:
            for op, fn in draw_patches.items():
                stack.enter_context(mock.patch.object(pygame.draw, op, fn))
            surf = module._radial(w, h, (255, 205, 85), alpha)
        radials.append({"w": w, "h": h, "color": [255, 205, 85], "alpha": alpha,
                        "size": list(surf.get_size()), "blocks": list(primitive_ops)})
    shadows = []
    for w, h, radius, alpha, spread in ((20, 10, 12, 110, 4), (300, 50, 12, 110, 4), (2, 2, 3, 40, 0)):
        module.clear_caches()
        primitive_ops.clear()
        with contextlib.ExitStack() as stack:
            for op, fn in draw_patches.items():
                stack.enter_context(mock.patch.object(pygame.draw, op, fn))
            surf = module._shadow(w, h, radius, alpha, spread)
        shadows.append({"w": w, "h": h, "radius": radius, "alpha": alpha, "spread": spread,
                        "size": list(surf.get_size()), "small_ops": list(primitive_ops)})
    icons = []
    for name in ICON_NAMES + ["unknown"]:
        for scale in (0.6, 1.0, 1.5):
            primitive_ops.clear()
            with contextlib.ExitStack() as stack:
                for op, fn in draw_patches.items():
                    stack.enter_context(mock.patch.object(pygame.draw, op, fn))
                module.draw_icon(screen, name, 100, 80, (110, 195, 255), scale)
            icons.append({"name": name, "center": [100, 80], "color": [110, 195, 255],
                          "scale": scale, "ops": list(primitive_ops)})
    ticks = []
    primitive_ops.clear()
    with contextlib.ExitStack() as stack:
        for op, fn in draw_patches.items():
            stack.enter_context(mock.patch.object(pygame.draw, op, fn))
        module.corner_ticks(screen, pygame.Rect(10, 20, 200, 80), palette["gold"])
    ticks.append({"rect": [10, 20, 200, 80], "color": palette["gold"], "ops": list(primitive_ops)})

    components = []
    for cheap in (True, False):
        for ticks_on in (True, False):
            for shadow_on in (True, False):
                components.append(component("panel", cheap, (10, 20, 240, 120), ticks=ticks_on, shadow=shadow_on))
        components.append(component("panel_solid", cheap, (10, 20, 240, 120)))
        for hover in (False, True):
            for icon in (None, "play"):
                for gap in (False, True):
                    components.append(component("button", cheap, "play", "PLAY", 320, 200, palette["cyan"], font,
                                                icon=icon, hover=hover, letter_gap=gap, btns={}))
        components.append(component("button", cheap, "small", "VERY LONG LABEL", 100, 100, palette["gold"], font,
                                    w=150, icon="coin", hover=True, btns={}))
        components.append(component("button", cheap, "fs", "PLAY", 320, 200, palette["cyan"], font,
                                    font_size=30, btns={}))
        for kind in ("gold", "success", "danger", "locked", "owned", "neutral", "violet", "cyan", "unknown"):
            for enabled, hover in ((True, False), (True, True), (False, True)):
                components.append(component("pill", cheap, "a", "PLAY", (20, 30, 160, 40), kind, font,
                                            hover=hover, enabled=enabled, icon="back", btns={}))
        for align in ("left", "right"):
            for icon in (None, "coin"):
                for value in (None, "123"):
                    components.append(component("chip", cheap, (900, 40), "GOLD", palette["gold"], font,
                                                icon=icon, value=value, align=align))
        components.append(component("section_header", cheap, 30, 50, "HEROES", "star", palette["gold"], font))
        for is_on in (False, True):
            for hover in (False, True):
                components.append(component("toggle", cheap, "t", (20, 30, 110, 36), is_on, font, hover=hover, btns={}))
        for value in (-0.2, 0.0, 0.02, 0.5, 1.0, 1.2):
            for hover in (False, True):
                components.append(component("slider", cheap, 100, 200, 240, value, knob_hover=hover))
        for hover in (None, "lang_prev", "lang_next"):
            components.append(component("option_cycler", cheap, "lang", "Language", "Bahasa Indonesia",
                                        30, 60, 420, font, font, hover=hover, btns={}))
        for active in (False, True):
            for hover in (False, True):
                components.append(component("tab", cheap, "tab", (20, 30, 170, 44), "HEROES", palette["cyan"],
                                            font, active, hover=hover, btns={}))
        for glow in (False, True):
            for sub in (None, "SUBTITLE"):
                components.append(component("screen_title", cheap, "ARENA", 640, 100, glow=glow, sub=sub))
        for hover in (False, True):
            components.append(component("back_button", cheap, "back", 640, 650, hover=hover, font=font, btns={}))
        for max_scroll in (0, 200):
            components.append(component("scroll_indicator", cheap, 10, 20, 300, 100, max_scroll))
        for ratio in (-0.1, 0.0, 0.02, 0.5, 1.0, 1.1):
            components.append(component("hp_bar", cheap, 10, 20, 200, 12, ratio))
            components.append(component("progress_bar", cheap, 10, 20, 200, ratio))
    tab_widths = [{"label": label, "min_w": min_w, "result": module.tab_width(font, label, min_w)}
                  for label in ("A", "HEROES", "LONG CATEGORY") for min_w in (100, 150)]
    return {
        "schema": 1, "source": "ui_theme.py", "source_sha256": _sha(SOURCE.read_bytes()),
        "pygame_version": PYGAME_VERSION, "font_size": font.size_value,
        "text": {"letter": text_cases, "ellipsis": ellipsis},
        "surfaces": {"gradient": gradients, "radial": radials, "shadow": shadows},
        "icons": icons, "ticks": ticks, "components": components, "tab_widths": tab_widths,
    }


def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else _text(value), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked bytes without writing")
    args = parser.parse_args()
    try:
        contract = build_contract()
        oracle = build_oracle()
        expected = {CONTRACT: _text(contract), FIXTURE: _text(oracle)}
        if args.check:
            for path, text in expected.items():
                if not path.is_file() or path.read_text(encoding="utf-8") != text:
                    raise AssertionError(f"stale or missing {path.relative_to(ROOT)}; run tools/prepare_godot_ui_theme.py")
        else:
            for path, text in expected.items():
                _write(path, text)
        print(f"Verified ui_theme: {len(contract['palette'])} colors, {len(contract['icons'])} icons, "
              f"{len(oracle['components'])} component cases; sha256={contract['source_sha256'][:12]}")
        return 0
    except (AssertionError, OSError, ValueError, ImportError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
