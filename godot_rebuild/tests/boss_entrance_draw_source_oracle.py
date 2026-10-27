"""Source oracle for `bosses/base_boss.py::Boss._draw_entrance` (layer 9bq11).

`Boss.draw` hands the ENTIRE frame to the entrance while the timer runs:

    if self.entrance_timer > 0:
        max_entrance = 180 if is_true else 120
        self._draw_entrance(surface, x, y, max_entrance)
        return

so nothing else about the boss exists on those frames. The method itself:

    progress = 1 - entrance_timer / max_timer
    size     = int(radius * progress * 2)
    size > 0 -> filled circle (*entrance_color, clamp(int(200 * (1 - progress)))) on a
                `size * 3` square surface blitted at `x - size * 3 // 2`, i.e. centred on the boss
    entrance_timer > max_timer // 2 ->
        pulse = sin(anim_time * 0.2) * 0.3 + 0.7
        alpha = clamp(int(255 * pulse)), shadow = clamp(int(200 * pulse))
        greedy word wrap of `entrance_text` at 1000 px with the font's own metrics
        start_y = 84 - (len(lines) - 1) * 18, 34 px per line, each line a black shadow at
        `(x + 2, y + 2)` then the text, both centred on `(SCREEN_WIDTH // 2, ly)`

The REAL method is harvested with `ast` and compiled under the recording pygame shim of
`draw_recorder.py`, whose fonts measure `int(size * GLYPH_FACTOR) x size` - the same metric the
GDScript suite feeds `boss_entrance_layout.gd`, so the wrap decisions are pinned by the source.

Run: python godot_rebuild/tests/boss_entrance_draw_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bosses" / "base_boss.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_entrance_draw_source.json"
OWNER = "Boss"
HARVESTED = ("_draw_entrance",)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SHORT_TEXT = "[ URGHARUN ]"
LONG_TEXT = ("Penjaga gerbang terakhir telah bangkit dari abu kota yang dibakar "
             "dan tidak ada satu pun pasukan yang sanggup menghentikan langkahnya")
LONGEST_WORD_TEXT = "Pertempuran Supercalifragilisticexpialidocious Dan Kawan Kawan"


class _Boss:
    """Stand-in for the attributes `_draw_entrance` reads."""

    def __init__(self, entrance_timer, max_timer, radius, entrance_color, entrance_text,
                 boss_class, anim_time):
        self.entrance_timer = entrance_timer
        self.max_timer = max_timer
        self.radius = radius
        self.entrance_color = entrance_color
        self.entrance_text = entrance_text
        self.boss_class = boss_class
        self.anim_time = anim_time


def _harvest(pygame, get_font):
    text = SOURCE.read_text(encoding="utf-8")
    owner = next((node for node in ast.parse(text).body
                  if isinstance(node, ast.ClassDef) and node.name == OWNER), None)
    if owner is None:
        raise AssertionError("%s not found in %s" % (OWNER, SOURCE.name))
    found = {}
    for node in owner.body:
        if isinstance(node, ast.FunctionDef) and node.name in HARVESTED:
            found[node.name] = node
    missing = set(HARVESTED) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.%s" % (sorted(missing), SOURCE.name, OWNER))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in HARVESTED)
    namespace = {
        "pygame": pygame,
        "math": math,
        "get_font": get_font,
        "SCREEN_WIDTH": SCREEN_WIDTH,
    }
    exec(compile("class %s:\n%s" % (OWNER, body), SOURCE.name, "exec"), namespace)
    return namespace[OWNER]


# (label, boss_class, radius, entrance_timer, anim_time, entrance_text, entrance_color)
FRAMES = [
    ("fresh_body", "body", 32, 120, 0.0, SHORT_TEXT, (255, 200, 60)),
    ("quarter_body", "body", 32, 90, 4.0, SHORT_TEXT, (255, 200, 60)),
    ("half_body_text_gone", "body", 32, 60, 7.0, SHORT_TEXT, (255, 200, 60)),
    ("late_body", "body", 32, 10, 11.0, SHORT_TEXT, (255, 200, 60)),
    ("fresh_true", "true", 48, 180, 0.0, SHORT_TEXT, (200, 90, 255)),
    ("third_true", "true", 48, 120, 9.0, SHORT_TEXT, (200, 90, 255)),
    ("wrapped_body", "body", 32, 120, 2.5, LONG_TEXT, (255, 200, 60)),
    ("long_word_true", "true", 48, 176, 30.0, LONGEST_WORD_TEXT, (200, 90, 255)),
]


def _record(pygame, get_font, boss_type, frames):
    out = []
    for label, boss_class, radius, timer, anim, text, color in frames:
        screen = rec.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        max_timer = 180 if boss_class == "true" else 120
        boss = _Boss(timer, max_timer, radius, color, text, boss_class, anim)
        boss_type._draw_entrance(boss, screen, 640, 360, max_timer)
        out.append({
            "label": label,
            "boss_class": boss_class,
            "radius": radius,
            "entrance_timer": timer,
            "max_timer": max_timer,
            "anim_time": anim,
            "entrance_text": text,
            "entrance_color": list(color),
            "anchor": [640, 360],
            "ops": screen.ops,
        })
    return out


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    with rec.installed({"pygame": pygame}):
        get_font = lambda size, style="body", bold=False: rec.Font(size, style)
        boss_type = _harvest(pygame, get_font)
        return {
            "screen": [SCREEN_WIDTH, SCREEN_HEIGHT],
            "glyph_factor": rec.GLYPH_FACTOR,
            "frames": _record(pygame, get_font, boss_type, FRAMES),
        }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
