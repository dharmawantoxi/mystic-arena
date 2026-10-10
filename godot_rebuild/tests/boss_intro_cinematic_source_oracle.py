"""Source oracle for the BossIntroCinematic port.

`import _render` fails with a pre-existing circular import and the Python
sources are read-only, so this oracle extracts `class BossIntroCinematic`
verbatim from `_render.py` and executes it.

The fade, slide-in, HP-bar and tag numbers all live inside `draw()`. They are
not re-implemented here: the real `draw()` runs against a minimal pygame /
font / theme shim, `sys.settrace` reads `alpha`, `x_offset`, `banner_x`,
`banner_y`, `tag_text`, `tag_color` and `fill` off the frame, and the shim
records every `pygame.draw.rect` call so the banner and bar rectangles are
the source's own.

Boss objects are built from the real `bosses/boss_data.py` entries (pure
data, loaded by file path). Only the six attributes the class reads are copied.

Run: python godot_rebuild/tests/boss_intro_cinematic_source_oracle.py
"""
import importlib.util
import json
import math
import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
BOSS_DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_intro_cinematic_source.json"

TAG = "_render.py:BossIntroCinematic"
SCREEN_W = 1280
SCREEN_H = 720
TIMELINE_BOSS = "abaddon"
SAMPLE_TICKS = [1, 12, 18, 40, 80, 88, 99]
SKIP_INPUTS = [
    ("space", "K_SPACE"),
    ("escape", "K_ESCAPE"),
    ("letter_a", "K_a"),
    ("click", None),
]


# --------------------------------------------------------------------------
# Shims. Nothing from pygame, _core or mobile is imported.
# --------------------------------------------------------------------------
class _Rect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    @property
    def size(self):
        return (self.width, self.height)

    def inflate(self, dw, dh):
        return _Rect(self.x, self.y, self.width + dw, self.height + dh)


RECTS = []


class _Surface:
    def __init__(self, *args, **kwargs):
        pass

    def set_alpha(self, *args, **kwargs):
        pass

    def blit(self, *args, **kwargs):
        pass

    def fill(self, *args, **kwargs):
        pass

    def get_at(self, pos):
        return (0, 0, 0, 0)

    def get_rect(self, **kwargs):
        return _Rect(0, 0, 10, 10)


class _FontShim:
    def __init__(self, *args, **kwargs):
        pass

    def render(self, *args, **kwargs):
        return _Surface()


class _ThemeShim:
    def letter(self, text):
        return text

    def draw_icon(self, *args, **kwargs):
        pass

    def corner_ticks(self, *args, **kwargs):
        pass


class _DrawShim:
    @staticmethod
    def rect(*args, **kwargs):
        RECTS.append((tuple(args[1]), [int(v) for v in args[2]]))

    @staticmethod
    def line(*args, **kwargs):
        pass

    @staticmethod
    def circle(*args, **kwargs):
        pass

    @staticmethod
    def polygon(*args, **kwargs):
        pass


class _TimeShim:
    @staticmethod
    def get_ticks():
        return 0


class _PygameShim:
    SRCALPHA = 1
    K_SPACE = 32
    K_ESCAPE = 27
    K_a = 97
    Surface = _Surface
    Rect = _Rect
    draw = _DrawShim
    time = _TimeShim


class _Quality:
    cheap_alpha = True


class _Pool:
    def get(self, w, h):
        return _Surface()

    def release(self, surface):
        pass


def _install_stubs():
    # `mobile` is a bare package so `from mobile import ...` fails cleanly and
    # `mobile.perf` resolves to the stub. The class's own imports from `_system`
    # and `_core` fail inside their try/except, as they do without pygame.
    mobile = types.ModuleType("mobile")
    mobile.__path__ = []
    perf = types.ModuleType("mobile.perf")
    perf.Quality = _Quality
    perf.POOL = _Pool()
    perf.blit_overlay = lambda surface, overlay, rect: None
    mobile.perf = perf
    sys.modules["mobile"] = mobile
    sys.modules["mobile.perf"] = perf


def _load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _slice(lines, start_pred, end_pred):
    start = next(i for i, line in enumerate(lines) if start_pred(line))
    end = next(i for i, line in enumerate(lines) if i > start and end_pred(line))
    return "\n".join(lines[start:end])


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    class_block = _slice(
        lines,
        lambda line: line.startswith("class BossIntroCinematic:"),
        lambda line: line.startswith("# ===="),
    )
    namespace = {
        "math": math,
        "pygame": _PygameShim,
        "ui_theme": _ThemeShim(),
        "get_font": _FontShim,
        "title_font": _FontShim,
    }
    exec(compile(class_block, TAG, "exec"), namespace)
    return namespace, class_block


def _capture_lines(block):
    """1-based line numbers inside the class block to read locals on."""
    prefixes = {
        "banner": "surface.blit(bg, (banner_x, banner_y))",
        "tag": "tag = self.font_small.render(tag_text, True, tag_color)",
        "fill": "pygame.draw.rect(surface, (255, 255, 255),",
    }
    found = {}
    stripped = [line.strip() for line in block.splitlines()]
    # Only lines inside draw(): the `_draw_*` helpers below it repeat some
    # prefixes but are never called from draw().
    draw_start = stripped.index("def draw(self, surface):")
    draw_end = next(i for i, line in enumerate(stripped)
                    if i > draw_start and line.startswith("def _draw_"))
    for key, prefix in prefixes.items():
        hits = [i + 1 for i, line in enumerate(stripped)
                if draw_start < i < draw_end and line.startswith(prefix)]
        assert len(hits) == 1, "%s matched %d times in draw()" % (prefix, len(hits))
        found[key] = hits[0]
    return found


def _trace_draw(cinematic, lines):
    """Run draw() once and read the source's locals and rectangles."""
    rec = {}

    def tracer(frame, event, arg):
        if event == "call":
            return tracer if frame.f_code.co_filename == TAG else None
        if event == "line" and frame.f_code.co_filename == TAG:
            at = frame.f_lineno
            local = frame.f_locals
            if at == lines["banner"]:
                rec["alpha"] = local["alpha"]
                rec["x_offset"] = local["x_offset"]
                rec["banner_x"] = local["banner_x"]
                rec["banner_y"] = local["banner_y"]
            elif at == lines["tag"]:
                rec["tag_text"] = local["tag_text"]
                rec["tag_color"] = list(local["tag_color"])
            elif at == lines["fill"]:
                rec["fill"] = local["fill"]
        return tracer

    RECTS.clear()
    sys.settrace(tracer)
    try:
        cinematic.draw(_Surface())
    finally:
        sys.settrace(None)
    rects = list(RECTS)
    rec["bg_alpha"] = rects[0][0][3]
    rec["border_alpha"] = rects[1][0][3]
    rec["border_rgb"] = list(rects[1][0][:3])
    rec["banner_w"] = rects[0][1][2]
    rec["banner_h"] = rects[0][1][3]
    rec["hp_bar"] = list(rects[2][1])
    return rec


def _boss_snapshot(boss):
    return {
        "name": boss["name"],
        "title": boss["title"],
        "boss_class": boss["boss_class"],
        "color": list(boss["color"]),
        "color_dark": list(boss["color_dark"]),
        "entrance_color": list(boss["entrance_color"]),
    }


def _boss_object(snapshot):
    """Stand-in for the live Boss object: exactly the attributes the class reads."""
    return SimpleNamespace(
        name=snapshot["name"],
        title=snapshot["title"],
        boss_class=snapshot["boss_class"],
        color=tuple(snapshot["color"]),
        color_dark=tuple(snapshot["color_dark"]),
        entrance_color=tuple(snapshot["entrance_color"]),
    )


def _row(cinematic, rec):
    return {
        "timer": cinematic.timer,
        "active": cinematic.is_active(),
        "alpha": rec["alpha"],
        "x_offset": rec["x_offset"],
        "banner_x": rec["banner_x"],
        "banner_y": rec["banner_y"],
        "bg_alpha": rec["bg_alpha"],
        "border_alpha": rec["border_alpha"],
        "banner_w": rec["banner_w"],
        "banner_h": rec["banner_h"],
        "fill": rec["fill"],
        "hp_bar": rec["hp_bar"],
        "border_rgb": rec["border_rgb"],
        "tag_text": rec["tag_text"],
        "tag_color": rec["tag_color"],
    }


def source_fixture():
    _install_stubs()
    namespace, class_block = _load_class()
    cls = namespace["BossIntroCinematic"]
    lines = _capture_lines(class_block)
    boss_data = _load_file("boss_data", BOSS_DATA)
    bosses = boss_data.get_all_boss_types()

    # 1. Full timeline on one true boss, one draw per tick while active.
    snapshot = _boss_snapshot(bosses[TIMELINE_BOSS])
    cinematic = cls(_boss_object(snapshot), SCREEN_W, SCREEN_H)
    duration = cinematic.duration
    timeline = []
    sound_steps = []
    for tick in range(1, duration + 1):
        cinematic.update()
        if tick == 1:
            sound_steps.append(bool(cinematic._sound_played))
        if cinematic.is_active():
            timeline.append(_row(cinematic, _trace_draw(cinematic, lines)))
        else:
            timeline.append({"timer": cinematic.timer, "active": False})

    # 2. Skip table, each input on a fresh instance after 50 ticks.
    skips = []
    for name, key in SKIP_INPUTS:
        fresh = cls(_boss_object(snapshot), SCREEN_W, SCREEN_H)
        for _ in range(50):
            fresh.update()
        if name == "click":
            result = fresh.handle_skip(click=True)
        else:
            result = fresh.handle_skip(key=getattr(_PygameShim, key))
        skips.append([name, result, fresh.is_active()])
    inactive = cls(_boss_object(snapshot), SCREEN_W, SCREEN_H)
    inactive.active = False
    skips.append(["inactive", inactive.handle_skip(key=_PygameShim.K_SPACE), False])

    # 3. Every boss in the table, sampled at fixed ticks.
    boss_rows = []
    for key in sorted(bosses):
        boss_snap = _boss_snapshot(bosses[key])
        instance = cls(_boss_object(boss_snap), SCREEN_W, SCREEN_H)
        samples = []
        for tick in range(1, duration + 1):
            instance.update()
            if tick in SAMPLE_TICKS and instance.is_active():
                rec = _trace_draw(instance, lines)
                samples.append([
                    tick, instance.timer, rec["alpha"], rec["x_offset"],
                    rec["banner_x"], rec["bg_alpha"], rec["fill"],
                ])
        boss_rows.append({"key": key, "boss": boss_snap, "samples": samples})

    return {
        "source": "_render.py::BossIntroCinematic",
        "duration": duration,
        "fade_in_ticks": 12,
        "fade_out_ticks": 20,
        "slide_ticks": 18,
        "hp_span": 0.85,
        "sample_ticks": SAMPLE_TICKS,
        "sound_on_first_update": sound_steps,
        "timeline_boss": TIMELINE_BOSS,
        "timeline_boss_snapshot": snapshot,
        "timeline": timeline,
        "skips": skips,
        "bosses": boss_rows,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    drawn = [row for row in fixture["timeline"] if row.get("active")]
    print("boss_intro_cinematic: %d timeline ticks (%d drawn), %d skip inputs, %d bosses"
          % (len(fixture["timeline"]), len(drawn), len(fixture["skips"]),
             len(fixture["bosses"])))
    print("  tick 12: alpha %s, x_offset %s; tick 99: alpha %s"
          % (fixture["timeline"][11]["alpha"], fixture["timeline"][11]["x_offset"],
             fixture["timeline"][98].get("alpha")))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
