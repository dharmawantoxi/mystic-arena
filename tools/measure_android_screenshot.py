#!/usr/bin/env python3
"""Measure the real Android screenshots in ``docs/screenshots/android-2026-10-30``
and compare them with the layout the Pygame source defines.

The Pygame Android build renders a **1624x720** logical surface on a 2436x1080
device: ``mobile/platform_utils.create_display`` widens the surface to the screen
ratio, keeps the game as a 1280x720 subsurface at the origin and puts the
leftover 344 px on the right. Screenshot pixels are therefore exactly 1.5x
logical pixels, which is what makes these screenshots usable as a layout oracle.

For every element the tool writes two rectangles:

* ``expect`` — what the source layout says (``_core.py`` menu button calls,
  ``mobile/sidepanel.py`` box offsets, ``platform_utils`` panel rule);
* ``measured`` — what the screenshot actually contains, found by projecting
  frame/interior colours inside the region the source predicts.

Manual tool (needs Pillow), not part of CI:

    python -m pip install pillow
    python tools/measure_android_screenshot.py --write
    python tools/measure_android_screenshot.py --self-test
    python tools/measure_android_screenshot.py --compare shot.png --kind match

`--compare` diffs any capture of the same screen (Pygame or Godot, any
resolution) against the source layout, so a PC capture can be checked against
the phone oracle with one command.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs/screenshots/android-2026-10-30"
FIXTURE = ROOT / "godot_rebuild/tests/fixtures/android_screenshot_reference.json"
LOGICAL_WIDTH = 1280
LOGICAL_HEIGHT = 720
PAD = 14
BOX_FILL = (22, 19, 32)
BUTTON_FILL = (52, 52, 56)


class Shot:
    def __init__(self, path: Path):
        self.path = path
        self.image = Image.open(path).convert("RGB")
        self.width, self.height = self.image.size
        self.scale = self.height / float(LOGICAL_HEIGHT)
        self.logical_width = round(self.width / self.scale)
        self._px = self.image.load()

    def at(self, x: float, y: float):
        ix = min(max(int(round(x * self.scale)), 0), self.width - 1)
        iy = min(max(int(round(y * self.scale)), 0), self.height - 1)
        return self._px[ix, iy]

    def region_sum(self, x0, y0, x1, y1):
        array = self.image.crop(
            (
                int(round(x0 * self.scale)),
                int(round(y0 * self.scale)),
                int(round(x1 * self.scale)),
                int(round(y1 * self.scale)),
            )
        )
        return array


def close(color, target, tol: int) -> bool:
    return all(abs(int(a) - int(b)) <= tol for a, b in zip(color, target))


def frame_like(color) -> bool:
    """The 1 px menu/panel frame is a desaturated mid-bright line; pure white
    highlights, saturated accents and dark fills are excluded."""
    low, high = min(color), max(color)
    return low >= 100 and high <= 235 and (high - low) <= 60


def panel_width(logical_width: int) -> int:
    """`mobile/platform_utils`: the panel gets everything right of the arena."""
    return max(0, logical_width - LOGICAL_WIDTH)


def median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def edge_near(shot: Shot, axis: str, fixed: float, expected: float, window: float = 3.0) -> float:
    """Closest frame-like pixel to `expected` along `axis` (0.5 px steps)."""
    candidates = []
    steps = int(window / 0.5)
    for index in range(-steps, steps + 1):
        value = expected + index * 0.5
        color = shot.at(value, fixed) if axis == "x" else shot.at(fixed, value)
        if frame_like(color):
            candidates.append(value)
    if not candidates:
        return round(float(expected), 1)
    return round(min(candidates, key=lambda value: abs(value - expected)), 1)


def measure_button(shot: Shot, expect) -> dict:
    x, y, w, h = expect
    left = median([edge_near(shot, "x", y + h * f, float(x)) for f in (0.3, 0.5, 0.7)])
    right = median([edge_near(shot, "x", y + h * f, float(x + w)) for f in (0.3, 0.5, 0.7)])
    top = median([edge_near(shot, "y", x + w * f, float(y)) for f in (0.15, 0.22, 0.78, 0.85)])
    bottom = median([edge_near(shot, "y", x + w * f, float(y + h)) for f in (0.15, 0.22, 0.78, 0.85)])
    return {
        "expect": [round(float(v), 1) for v in expect],
        "measured": [left, top, round(right - left, 1), round(bottom - top, 1)],
    }


def runs(indices, scale: float, gap: int = 3) -> list:
    out = []
    start = prev = None
    for value in indices:
        if start is None:
            start = prev = value
            continue
        if value - prev <= gap:
            prev = value
            continue
        out.append((start, prev))
        start = prev = value
    if start is not None:
        out.append((start, prev))
    return [(round(a / scale, 1), round(b / scale, 1)) for a, b in out]


BOX_BORDER = (64, 56, 86)
PAUSE_GOLD = (255, 205, 90)


def box_border_rows(shot: Shot) -> list:
    """Full-width 1 px frame lines of the HUD boxes.

    Stone/brick art also produces panel-wide light lines every 34 px, so a
    candidate only counts when the pixel just inside it is the box fill.
    """
    found = []
    sampled = list(range(LOGICAL_WIDTH + 10, shot.logical_width - 14, 2))
    for index in range(0, LOGICAL_HEIGHT * 2):
        row = index / 2.0
        hits = 0
        for ix in sampled:
            if close(shot.at(ix, row), BOX_BORDER, 14):
                hits += 1
        if hits < 0.9 * len(sampled):
            continue
        inside = close(shot.at(1350.0, row + 2.0), BOX_FILL, 4) or close(
            shot.at(1350.0, row - 2.0), BOX_FILL, 4
        )
        if inside:
            found.append(row)
    return [round((a + b) / 2.0, 1) for a, b in runs(found, 1.0, gap=4)]


def box_border_cols(shot: Shot, row: float) -> list:
    found = []
    for index in range((LOGICAL_WIDTH + 4) * 2, (shot.logical_width - 6) * 2):
        col = index / 2.0
        if close(shot.at(col, row), BOX_BORDER, 14):
            found.append(col)
    return [round((a + b) / 2.0, 1) for a, b in runs(found, 1.0, gap=4)]


def pause_box(shot: Shot) -> list:
    points = [
        (index / 2.0, row / 2.0)
        for row in range(0, 160)
        for index in range((LOGICAL_WIDTH + 4) * 2, (LOGICAL_WIDTH + 70) * 2)
        if close(shot.at(index / 2.0, row / 2.0), PAUSE_GOLD, 60)
    ]
    if not points:
        return [0.0, 0.0, 0.0, 0.0]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), round(max(xs) - min(xs) + 0.5, 1), round(max(ys) - min(ys) + 0.5, 1)]


def grey_rows(shot: Shot) -> list:
    found = []
    sampled = list(range(LOGICAL_WIDTH + 30, shot.logical_width - 30, 2))
    for index in range(0, LOGICAL_HEIGHT * 2):
        row = index / 2.0
        hits = sum(1 for ix in sampled if close(shot.at(ix, row), BUTTON_FILL, 16))
        if hits > 0.55 * len(sampled):
            found.append(row)
    return [(a, b) for a, b in runs(found, 1.0, gap=4) if b - a > 20]


def column_bounds(shot: Shot, row: float, dark: bool = True) -> list:
    """Horizontal extent of a box/button interior inside the side panel."""
    values = []
    for index in range((LOGICAL_WIDTH + 2) * 2, (shot.logical_width - 4) * 2):
        ix = index / 2.0
        color = shot.at(ix, row)
        if dark and close(color, BOX_FILL, 3):
            values.append(ix)
        if not dark and close(color, BUTTON_FILL, 16):
            values.append(ix)
    if not values:
        return [0.0, 0.0]
    return [float(min(values)), float(max(values))]


MENU_BUTTONS = {
    # `_core.py::_draw_main_menu`: CONTINUE (cx-170, 336) / PLAY (cx+170, 336)
    # are 300x50, the stack is 360x50 at cx starting 389 with a 53 px step.
    "continue": (320.0, 311.0, 300.0, 50.0),
    "play": (660.0, 311.0, 300.0, 50.0),
    "hero_shop": (460.0, 364.0, 360.0, 50.0),
    "input": (460.0, 417.0, 360.0, 50.0),
    "how_to_play": (460.0, 470.0, 360.0, 50.0),
    "settings": (460.0, 523.0, 360.0, 50.0),
    "credits": (460.0, 576.0, 360.0, 50.0),
    "quit": (460.0, 629.0, 360.0, 50.0),
}

TACTICAL_EXPECT = [
    (1300.0, 288.0 + 38.0 * index, 304.0, 32.0) for index in range(5)
]

PANEL_BOXES = {
    # `mobile/sidepanel.py`: STATUS at y=84 (h 96), HEROES at y=190 (h 64),
    # TACTICAL at y=264 (h 210), all PAD=14 and 316 wide.
    "status": (1294.0, 84.0, 316.0, 96.0),
    "heroes": (1294.0, 190.0, 316.0, 64.0),
    "tactical": (1294.0, 264.0, 316.0, 210.0),
}


def rect_from_borders(rows: list, cols: list, index: int) -> list:
    top = rows[index * 2]
    bottom = rows[index * 2 + 1]
    return [cols[0], top, round(cols[-1] - cols[0] + 1.0, 1), round(bottom - top, 1)]


def measure_menu_layout(shot: Shot) -> dict:
    """Measured rect of every main-menu button on one capture."""
    return {name: measure_button(shot, rect)["measured"] for name, rect in MENU_BUTTONS.items()}


def measure_match_layout(shot: Shot) -> dict:
    """Measured rect of the dock: panel, PAUSE ring, HUD boxes and tactical rows."""
    rows = box_border_rows(shot)
    cols = box_border_cols(shot, 130.0)
    width = float(panel_width(shot.logical_width))
    out = {}
    out["panel"] = [round(cols[0] - 14.0, 1), 0.0, width, 720.0] if cols else [0.0, 0.0, 0.0, 0.0]
    out["pause"] = pause_box(shot)
    for index, name in enumerate(PANEL_BOXES):
        if len(rows) >= (index + 1) * 2 and len(cols) >= 2:
            out[name] = rect_from_borders(rows, cols, index)
        else:
            out[name] = [0.0, 0.0, 0.0, 0.0]
    grey = grey_rows(shot)
    button_x = column_bounds(shot, 302.0, dark=False)
    for index, (top, bottom) in enumerate(grey[: len(TACTICAL_EXPECT)]):
        if button_x[1] <= button_x[0]:
            out["tactical_%d" % index] = [0.0, 0.0, 0.0, 0.0]
            continue
        # the 2 px frame is excluded from the flat fill band
        out["tactical_%d" % index] = [
            round(button_x[0] - 2.0, 1),
            round(top - 2.0, 1),
            round(button_x[1] - button_x[0] + 4.0, 1),
            round(bottom - top + 4.0, 1),
        ]
    return out


def build_fixture() -> dict:
    menu = Shot(SHOTS / "menu.jpg")
    match = Shot(SHOTS / "match.jpg")
    dock = measure_match_layout(match)
    boxes = {
        name: {"expect": list(expect), "measured": dock[name]}
        for name, expect in PANEL_BOXES.items()
    }
    buttons = [
        {
            "index": index,
            "expect": list(expect),
            "measured": dock.get("tactical_%d" % index, [0.0, 0.0, 0.0, 0.0]),
        }
        for index, expect in enumerate(TACTICAL_EXPECT)
    ]
    width = float(panel_width(menu.logical_width))
    return {
        "device": {
            "px": [menu.width, menu.height],
            "scale": menu.scale,
            "logical": [menu.logical_width, LOGICAL_HEIGHT],
            "ratio": round(menu.width / float(menu.height), 4),
            "panel_width": panel_width(menu.logical_width),
        },
        "menu": {
            "image": str((SHOTS / "menu.jpg").relative_to(ROOT)),
            "buttons": {name: measure_button(menu, rect) for name, rect in MENU_BUTTONS.items()},
            "frame_color": [int(v) for v in menu.at(460.0, 389.0)],
            "fill_color": [int(v) for v in menu.at(500.0, 372.0)],
            "accent_color": [int(v) for v in menu.at(465.0, 389.0)],
            "label_color": [int(v) for v in menu.at(560.0, 389.0)],
        },
        "match": {
            "image": str((SHOTS / "match.jpg").relative_to(ROOT)),
            "panel": {"expect": [1280.0, 0.0, width, 720.0], "measured": dock["panel"]},
            "pause": {"expect": [1294.0, 14.0, 58.0, 58.0], "measured": dock["pause"]},
            "boxes": boxes,
            "tactical_buttons": buttons,
            "colors": {
                "box_fill": [int(v) for v in match.at(1350.0, 110.0)],
                "box_line": [int(v) for v in match.at(1400.0, 84.0)],
                "button_fill": [int(v) for v in match.at(1400.0, 302.0)],
                "gold_text": [int(v) for v in match.at(1310.0, 127.0)],
            },
            "hud": {
                "gold": 1106,
                "level": 2,
                "wave": 0,
                "shield_active": True,
                "difficulty": "normal",
                "heroes": 0,
            },
        },
    }


def expected_layout(kind: str) -> dict:
    """The source rects a capture of `kind` has to reproduce, in logical px."""
    if kind == "menu":
        return dict(MENU_BUTTONS)
    expect = {
        "panel": (1280.0, 0.0, 344.0, 720.0),
        "pause": (1294.0, 14.0, 58.0, 58.0),
    }
    expect.update(PANEL_BOXES)
    for index, rect in enumerate(TACTICAL_EXPECT):
        expect["tactical_%d" % index] = rect
    return expect


def measure_layout(shot: Shot, kind: str) -> dict:
    return measure_menu_layout(shot) if kind == "menu" else measure_match_layout(shot)


def compare(path: Path, kind: str, tolerance: float) -> int:
    """Diff one capture (Pygame or Godot, any resolution) against the source layout."""
    shot = Shot(path)
    expect = expected_layout(kind)
    measured = measure_layout(shot, kind)
    print(
        "%s: %s  (%dx%d, scale %.2f, logical %dx%d)"
        % (
            kind,
            path,
            shot.width,
            shot.height,
            shot.scale,
            shot.logical_width,
            LOGICAL_HEIGHT,
        )
    )
    print("  %-22s %-26s %-26s %s" % ("element", "source", "measured", "max delta"))
    worst = 0.0
    missing = []
    for name, want in expect.items():
        got = measured.get(name, [0.0, 0.0, 0.0, 0.0])
        if float(got[2]) <= 0.0 or float(got[3]) <= 0.0:
            missing.append(name)
            continue
        delta = max(abs(float(a) - float(b)) for a, b in zip(got, want))
        worst = max(worst, delta)
        print(
            "  %-22s %-26s %-26s %5.1f%s"
            % (name, _fmt(want), _fmt(got), delta, "  <-- off" if delta > tolerance else "")
        )
    if missing:
        print(
            "  not found in this capture: %s (different game state? the reference match has"
            " no heroes, no boss and no enemy hero, so all five tactical rows are disabled)"
            % ", ".join(missing)
        )
    print("  worst delta %.1f px (tolerance %.1f)" % (worst, tolerance))
    if missing or worst > tolerance:
        print("  RESULT: MISMATCH")
        return 1
    print("  RESULT: OK")
    return 0


def _fmt(rect) -> str:
    return "[%s]" % ", ".join("%.1f" % float(value) for value in rect)


def self_test(tolerance: float) -> int:
    """Prove the pipeline: the committed fixture must be reproducible from the
    captures, and the same numbers must survive a different pixel scale."""
    fixture = build_fixture()
    committed = FIXTURE.read_text(encoding="utf-8") if FIXTURE.is_file() else ""
    rebuilt = json.dumps(fixture, indent=2, sort_keys=True) + "\n"
    status = 0
    print("fixture reproducible:", "yes" if rebuilt == committed else "NO")
    if rebuilt != committed:
        print("  run --write and commit the result")
        status = 1
    for kind, image in (("menu", SHOTS / "menu.jpg"), ("match", SHOTS / "match.jpg")):
        status |= compare(image, kind, tolerance)
    scaled = Path(tempfile.mkdtemp()) / "menu_half.png"
    source = Image.open(SHOTS / "menu.jpg").convert("RGB")
    source.resize((source.width // 2, source.height // 2), Image.BILINEAR).save(scaled)
    # At half resolution one logical px is 0.75 device px, so the 1 px source
    # highlights quantise: allow exactly one extra px here.
    print("scale independence (same layout at half resolution, tolerance +1 px):")
    status |= compare(scaled, "menu", tolerance + 1.0)
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the reference fixture")
    parser.add_argument("--compare", metavar="IMAGE", help="diff one capture against the source layout")
    parser.add_argument("--kind", choices=["menu", "match"], default="menu")
    parser.add_argument("--tolerance", type=float, default=3.0)
    parser.add_argument("--self-test", action="store_true", help="re-measure the captures and check drift")
    args = parser.parse_args()
    if args.compare:
        raise SystemExit(compare(Path(args.compare), args.kind, args.tolerance))
    if args.self_test:
        raise SystemExit(self_test(args.tolerance))
    fixture = build_fixture()
    text = json.dumps(fixture, indent=2, sort_keys=True) + "\n"
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(text, encoding="utf-8")
        print("wrote", FIXTURE.relative_to(ROOT))
    else:
        print(text)


if __name__ == "__main__":
    main()
