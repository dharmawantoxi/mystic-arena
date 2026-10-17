"""Source oracle for the `mobile/sidepanel.py` port (layer 9as).

The source right-hand panel exists only on screens wider than 16:9: the
leftover width (>= 120 px, display capped at 2200 px) becomes a stone panel
at x >= 1280 holding the PAUSE button, a STATUS box (gold / mode / level /
wave), the HEROES list (name, level, HP bar, Q/W/E/R dots) and the TACTICAL
COMMANDS buttons. Notifications and the kill feed were removed from it by
the user (no-ops in the source).

This oracle runs the REAL `SidePanel` under a recording pygame shim (Rect
math, draw calls and text renders are captured, fonts measure 7 px per
glyph) against scripted fake games, and writes every layout number, string,
colour and hit-test decision so `scripts/ui/side_panel_layout.gd` replays
them exactly.

Run: python godot_rebuild/tests/side_panel_source_oracle.py
"""
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mobile" / "sidepanel.py"
PLATFORM = ROOT / "mobile" / "platform_utils.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "side_panel_source.json"

GLYPH_W = 7
LOGICAL_W, LOGICAL_H = 1280, 720


class Rect:
    def __init__(self, *args):
        if len(args) == 1:
            args = tuple(args[0]) if not isinstance(args[0], Rect) else args[0].tuple()
        if len(args) == 2:
            (x, y), (w, h) = args
            args = (x, y, w, h)
        self.x, self.y, self.width, self.height = [int(v) for v in args]

    def tuple(self):
        return (self.x, self.y, self.width, self.height)

    right = property(lambda s: s.x + s.width)
    bottom = property(lambda s: s.y + s.height)
    topleft = property(lambda s: (s.x, s.y))
    size = property(lambda s: (s.width, s.height))
    centerx = property(lambda s: s.x + s.width // 2)
    centery = property(lambda s: s.y + s.height // 2)
    center = property(lambda s: (s.centerx, s.centery))

    def inflate(self, dx, dy):
        return Rect(self.x - dx // 2, self.y - dy // 2, self.width + dx, self.height + dy)

    def move(self, dx, dy):
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def collidepoint(self, pos):
        px, py = pos
        return self.x <= px < self.right and self.y <= py < self.bottom

    def clip(self, other):
        x1, y1 = max(self.x, other.x), max(self.y, other.y)
        x2, y2 = min(self.right, other.right), min(self.bottom, other.bottom)
        if x2 <= x1 or y2 <= y1:
            return Rect(0, 0, 0, 0)
        return Rect(x1, y1, x2 - x1, y2 - y1)

    def __eq__(self, other):
        return isinstance(other, Rect) and self.tuple() == other.tuple()

    def __ne__(self, other):
        return not self.__eq__(other)


class Text:
    def __init__(self, text, color):
        self.text, self.color = text, tuple(color)
        self.w, self.h = GLYPH_W * len(text), 12

    def get_width(self):
        return self.w

    def get_rect(self, **anchors):
        r = Rect(0, 0, self.w, self.h)
        if "center" in anchors:
            cx, cy = anchors["center"]
            r.x, r.y = cx - self.w // 2, cy - self.h // 2
        if "midright" in anchors:
            rx, cy = anchors["midright"]
            r.x, r.y = rx - self.w, cy - self.h // 2
        return r


class Font:
    def __init__(self, size, style):
        self.size, self.style = size, style

    def render(self, text, _aa, color):
        return Text(str(text), color)


class Surface:
    def __init__(self, size):
        self.size = tuple(size)
        self.log = []

    def get_size(self):
        return self.size

    def convert(self):
        return self

    def fill(self, color, rect=None):
        self.log.append(("fill", tuple(color)))

    def blit(self, src, dest):
        if isinstance(src, Text):
            pos = dest.tuple()[:2] if isinstance(dest, Rect) else tuple(dest)
            self.log.append(("text", src.text, src.color, pos))
        else:
            self.log.append(("blit",))


class Draw:
    def __init__(self):
        self.log = []

    def rect(self, surface, color, rect, width=0, border_radius=0):
        surface.log.append(("rect", tuple(color), Rect(rect).tuple(), width, border_radius))

    def circle(self, surface, color, center, radius):
        surface.log.append(("circle", tuple(color), tuple(center), radius))

    def line(self, surface, color, a, b, width=1):
        surface.log.append(("line",))


class Clock:
    ms = 0


def _load(panel_width):
    pygame = types.ModuleType("pygame")
    pygame.Rect = Rect
    pygame.Surface = Surface
    pygame.draw = Draw()
    pygame.time = types.SimpleNamespace(get_ticks=lambda: Clock.ms)
    plat = types.ModuleType("mobile.platform_utils")
    panel = Rect(LOGICAL_W, 0, panel_width, LOGICAL_H) if panel_width else None
    plat.get_panel_rect = lambda: panel
    plat.get_full_surface = lambda: (_ for _ in ()).throw(RuntimeError("no display"))
    # Real zone constant from platform_utils.
    for line in PLATFORM.read_text(encoding="utf-8").splitlines():
        if line.startswith("ZONA_BAWAH_H"):
            plat.ZONA_BAWAH_H = int(line.split("=")[1].strip())
    mobile = types.ModuleType("mobile")
    mobile.platform_utils = plat
    saved = {k: sys.modules.get(k) for k in ("pygame", "mobile", "mobile.platform_utils")}
    sys.modules.update({"pygame": pygame, "mobile": mobile, "mobile.platform_utils": plat})
    try:
        ns = {"__name__": "sidepanel_oracle", "__file__": str(SOURCE)}
        exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), ns)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return ns, pygame


class Hero:
    def __init__(self, name, alive=True, level=3, hp=100.0, max_hp=100.0, ready=("q", "w")):
        self.name, self.alive, self.level = name, alive, level
        self.hp, self.max_hp, self.team = hp, max_hp, "blue"
        self._ready = set(ready)

    def is_skill_ready(self, key):
        return key in self._ready


class Game:
    def __init__(self, heroes, gold=1234, difficulty="normal", wave=3, level=2,
                 shield=True, boss_alive=False, enemy_alive=False, state="playing",
                 held=None, popup=False):
        self.heroes = heroes
        self.gold, self.difficulty = gold, difficulty
        self.wave_number, self.level_number = wave, level
        self.blue_base = types.SimpleNamespace(shield_active=shield)
        self.active_boss = types.SimpleNamespace(alive=True) if boss_alive else None
        self.ai = types.SimpleNamespace(
            heroes=[types.SimpleNamespace(alive=True, team="red")] if enemy_alive else [])
        self.state = state
        self.tactical = types.SimpleNamespace(held_command=held)
        self.popup_target = object() if popup else None
        self.build_popup_slot = None
        self.selected_hero = None

    def get_all_heroes(self):
        return list(self.heroes) + list(self.ai.heroes)


def _font_factory(size, style="body"):
    return Font(size, style)


def _snapshot(panel, game, panel_width):
    buf = Surface((panel_width, LOGICAL_H))
    y_status = panel._gambar_status(buf, game, 84)
    y_hero = panel._gambar_hero(buf, game, y_status)
    y_tac = panel._gambar_tactical(buf, game, y_hero)
    texts = [{"text": e[1], "color": list(e[2]), "pos": list(e[3])} for e in buf.log if e[0] == "text"]
    rects = [{"color": list(e[1]), "rect": list(e[2]), "width": e[3], "radius": e[4]}
             for e in buf.log if e[0] == "rect"]
    circles = [{"color": list(e[1]), "center": list(e[2]), "radius": e[3]}
               for e in buf.log if e[0] == "circle"]
    buttons = {}
    for key, b in panel.buttons.items():
        buttons[key] = {"rect": list(b.rect.tuple()), "hit_rect": list(b.hit_rect.tuple()),
                        "visible": bool(b.visible), "label": b.label, "color": list(b.warna)}
    return {"y_after_status": y_status, "y_after_heroes": y_hero, "y_after_tactical": y_tac,
            "texts": texts, "rects": rects, "circles": circles, "buttons": buttons}


def source_fixture():
    width = 344
    ns, _ = _load(width)
    panel = ns["SidePanel"](_font_factory)
    heroes5 = [Hero("Kaizen"), Hero("Thorne the Long", level=7, hp=30.0, ready=("q", "w", "e", "r")),
               Hero("Vex", alive=False, hp=0.0, ready=()), Hero("Sylara", hp=60.0),
               Hero("Grimjaw", hp=10.0, ready=("r",))]
    scenarios = {
        "empty": Game([], gold=0, wave=None, level=None, difficulty="easy"),
        "three": Game(heroes5[:3], gold=98765, wave=12, level=5, difficulty="hard",
                      boss_alive=True, enemy_alive=True, held="attack_boss"),
        "five": Game(heroes5, gold=4321, wave=1, level=1, shield=True),
        "seven": Game(heroes5 + [Hero("Morgath"), Hero("Zephyr")], gold=10000, wave=10,
                      level=3, shield=False, enemy_alive=True),
        "victory": Game(heroes5[:2], state="victory"),
    }
    snapshots = {}
    for name, game in scenarios.items():
        snap = _snapshot(panel, game, width)
        snap["input"] = {
            "state": game.state, "gold": game.gold, "difficulty": game.difficulty,
            "wave": -1 if game.wave_number is None else game.wave_number,
            "level": -1 if game.level_number is None else game.level_number,
            "shield_active": bool(game.blue_base.shield_active),
            "heroes": [{"name": h.name, "alive": h.alive, "level": h.level, "hp": h.hp,
                        "max_hp": h.max_hp, "ready": sorted(h._ready)} for h in game.heroes],
            "has_boss": game.active_boss is not None,
            "has_enemy_hero": bool(game.ai.heroes),
            "held": game.tactical.held_command or "",
        }
        snapshots[name] = snap

    # Hit tests on the "five" layout (buttons left as drawn by the last
    # scenario, so redraw it first).
    _snapshot(panel, scenarios["five"], width)
    hits = []
    for label, pos, game in (
        ("pause_center", (1280 + 14 + 29, 14 + 29), scenarios["five"]),
        ("pause_pad", (1280 + 14 - 10, 14 - 10), scenarios["five"]),
        ("pause_outside", (1280 + 14 + 58 + 12, 14), scenarios["five"]),
        ("gather", (1280 + 14 + 6 + 20, None), scenarios["five"]),
        ("gather_pad", (1280 + 14 + 6 - 2, None), scenarios["five"]),
        ("between", (1280 + 14 + 6 + 20, "gap"), scenarios["five"]),
        ("gather_popup", (1280 + 14 + 6 + 20, None), scenarios["five"]),
        ("pause_popup", (1280 + 14 + 29, 14 + 29), scenarios["five"]),
        ("arena", (640, 360), scenarios["five"]),
    ):
        x, y = pos
        gather = panel.buttons["gather"].rect
        if y is None:
            y = gather.y + 5
        elif y == "gap":
            y = gather.bottom + 4  # 3 px pad -> first px past the padded box
        if label.endswith("_popup"):
            game.popup_target = object()
        hit = panel.hit_test((x, y), game=game)
        if label.endswith("_popup"):
            game.popup_target = None
        hits.append({"case": label, "pos": [x, y], "action": hit,
                     "blocks": bool(panel.blocks((x, y)))})
        for b in panel.buttons.values():
            b.press_anim = 0.0

    # Non-gameplay: draw() must hide every button.
    full = Surface((LOGICAL_W + width, LOGICAL_H))
    panel.draw(full, Game([], state="menu"), None)
    hidden = all(not b.visible for b in panel.buttons.values())

    # Panel width rule: leftover below 120 px -> no panel.
    ns_none, _ = _load(0)
    inactive = ns_none["SidePanel"](_font_factory)

    def display_width(ratio):
        usul = int(round(LOGICAL_H * ratio))
        w = max(LOGICAL_W, min(2200, usul))
        return w - w % 2

    return {
        "source": "mobile/sidepanel.py + platform_utils display rules (real module under a recording shim)",
        "glyph_width": GLYPH_W,
        "refresh_ms": ns["JEDA_SEGAR_MS"],
        "min_tap": ns["MIN_TAP"],
        "zona_bawah": ns["ZONA_BAWAH"],
        "colors": {k: list(ns[k]) for k in ("FG", "DIM", "EMAS", "OK", "BAHAYA", "BIRU", "UNGU")},
        "panel_width": width,
        "min_panel_width": 120,
        "display_width": {str(r): display_width(r) for r in (16 / 9, 2.0, 2.1667, 2.26, 3.2, 1.3333)},
        "inactive_without_panel": not inactive.aktif,
        "tactical_keys": list(ns["SidePanel"].TACTICAL_KEYS),
        "snapshots": snapshots,
        "hits": hits,
        "menu_hides_buttons": hidden,
    }


def main():
    fixture = source_fixture()
    assert fixture["snapshots"]["five"]["buttons"]["gather"]["visible"] is True
    assert fixture["snapshots"]["victory"]["buttons"]["gather"]["visible"] is False
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)


if __name__ == "__main__":
    main()
