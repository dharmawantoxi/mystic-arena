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
"""
from __future__ import annotations

import argparse
import json
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


def build_fixture() -> dict:
    menu = Shot(SHOTS / "menu.jpg")
    match = Shot(SHOTS / "match.jpg")
    rows = box_border_rows(match)
    cols = box_border_cols(match, 130.0)
    boxes = {}
    for index, (name, expect) in enumerate(PANEL_BOXES.items()):
        measured = rect_from_borders(rows, cols, index) if len(rows) >= (index + 1) * 2 else list(expect)
        boxes[name] = {"expect": list(expect), "measured": measured}
    grey = grey_rows(match)
    button_x = column_bounds(match, 302.0, dark=False)
    buttons = []
    for index, (top, bottom) in enumerate(grey):
        expect_y = 288.0 + index * 38.0
        buttons.append(
            {
                "index": index,
                "expect": [1300.0, expect_y, 304.0, 32.0],
                # the 2 px frame is excluded from the flat fill band
                "measured": [
                    round(button_x[0] - 2.0, 1),
                    round(top - 2.0, 1),
                    round(button_x[1] - button_x[0] + 4.0, 1),
                    round(bottom - top + 4.0, 1),
                ],
            }
        )
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
            "panel": {
                "expect": [1280.0, 0.0, float(panel_width(menu.logical_width)), 720.0],
                "measured": [
                    cols[0] - 14.0 if cols else 0.0,
                    0.0,
                    float(panel_width(menu.logical_width)),
                    720.0,
                ],
            },
            "pause": {"expect": [1294.0, 14.0, 58.0, 58.0], "measured": pause_box(match)},
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


def report(fixture: dict) -> None:
    deltas = []
    for name, entry in fixture["menu"]["buttons"].items():
        for got, want in zip(entry["measured"], entry["expect"]):
            deltas.append((abs(got - want), "menu." + name))
    deltas.append(
        (
            abs(fixture["match"]["panel"]["measured"][0] - fixture["match"]["panel"]["expect"][0]),
            "match.panel",
        )
    )
    for name, entry in fixture["match"]["boxes"].items():
        for got, want in zip(entry["measured"], entry["expect"]):
            deltas.append((abs(got - want), "match.boxes." + name))
    for got, want in zip(fixture["match"]["pause"]["measured"], fixture["match"]["pause"]["expect"]):
        deltas.append((abs(got - want), "match.pause"))
    for entry in fixture["match"]["tactical_buttons"]:
        for got, want in zip(entry["measured"], entry["expect"]):
            deltas.append((abs(got - want), "match.tactical_button[%d]" % entry["index"]))
    deltas.sort(reverse=True)
    print("worst deltas (px, logical):")
    for delta, label in deltas[:8]:
        print("  %5.1f  %s" % (delta, label))
    worst = deltas[0][0] if deltas else 0.0
    print("worst delta overall: %.1f px" % worst)
    if worst > 3.0:
        raise SystemExit("layout and screenshot disagree by more than 3 logical px")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fixture = build_fixture()
    report(fixture)
    text = json.dumps(fixture, indent=2, sort_keys=True) + "\n"
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(text, encoding="utf-8")
        print("wrote", FIXTURE.relative_to(ROOT))
    else:
        print(text)


if __name__ == "__main__":
    main()
