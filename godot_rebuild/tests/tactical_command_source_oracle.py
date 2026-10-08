#!/usr/bin/env python3
"""Execute the real read-only tactical command manager against source-shaped actors.

The fixture locks command selection, formation, hold/release timing, armed retries,
gather follow-up, and automatic castle protection without importing pygame.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("fixtures") / "tactical_command_source.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tactical_commands import (  # noqa: E402
    GATHER_PUSH_DELAY_FRAMES,
    HOLD_RELEASE_TAIL,
    HOLD_TAP_MAX_FRAMES,
    TacticalCommand,
    TacticalCommandManager,
)


class Actor:
    def __init__(self, label, x, y, team="blue", hp=1000, max_hp=1000, alive=True):
        self.label = label
        self.name = label
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.hp = float(hp)
        self.max_hp = float(max_hp)
        self.alive = alive


class Hero(Actor):
    def __init__(self, label, x, y, team="blue", damage_dealt=0, attack_range=100):
        super().__init__(label, x, y, team)
        self.damage_dealt = damage_dealt
        self.range = attack_range
        self.destination = None
        self.destination_auto = False
        self.follow_target = None
        self.target = None
        self.is_retreating = True

    def move_to(self, x, y, auto=False):
        self.destination = (float(x), float(y))
        self.destination_auto = bool(auto)
        self.follow_target = None
        self.is_retreating = False


class Effects:
    def add_damage_number(self, *_args, **_kwargs):
        pass

    def add_death_explosion(self, *_args, **_kwargs):
        pass


class Game:
    def __init__(self, heroes=()):
        self.state = "playing"
        self.heroes = list(heroes)
        self.towers = []
        self.minions = []
        self.ai = SimpleNamespace(heroes=[])
        self.active_boss = None
        self.blue_base = Actor("blue_castle", 100, 620, "blue", 2000, 2000)
        self.red_base = Actor("red_castle", 1180, 100, "red", 2000, 2000)
        self.selected_hero = None
        self.selected_tower = None
        self.effects = Effects()
        self.wave_number = 1
        self.mouse_x = 640
        self.mouse_y = 360


class QuietManager(TacticalCommandManager):
    """Presentation callback remains source-equivalent but avoids optional imports."""

    def _set_feedback(self, text, color=(255, 220, 100)):
        self.feedback_text = text
        self.feedback_timer = 180
        self.feedback_color = color


def _point(value):
    if value is None:
        return None
    return [round(float(value[0]), 6), round(float(value[1]), 6)]


def _label(value):
    return None if value is None else value.label


def _snapshot(manager, game):
    return {
        "active": manager.active_command,
        "timer": manager.command_timer,
        "cooldown": manager.cooldown,
        "target": _label(manager.command_target),
        "point": _point(manager.gather_point),
        "point_timer": manager.gather_point_timer,
        "held": manager.held_command,
        "hold_elapsed": manager.hold_elapsed,
        "hold_fired": manager._hold_has_fired,
        "gather_push": manager._gather_push_fired,
        "feedback": manager.feedback_text,
        "heroes": [
            {
                "id": hero.label,
                "destination": _point(hero.destination),
                "follow": _label(hero.follow_target),
                "target": _label(hero.target),
                "retreating": hero.is_retreating,
            }
            for hero in game.heroes
        ],
    }


def _heroes(count, origin=(100, 200)):
    return [Hero(f"blue_{i}", origin[0] + i * 100, origin[1] + i * 20) for i in range(count)]


def source_fixture():
    cases = []

    heroes = _heroes(4)
    game = Game(heroes)
    manager = QuietManager(game)
    accepted = manager.command_gather(640, 360, silent=True)
    cases.append({"label": "gather_explicit", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = [
        Hero("blue_0", 250, 300),
        Hero("blue_1", 280, 300),
        Hero("blue_2", 500, 500),
        Hero("blue_3", 800, 600),
        Hero("blue_4", 1000, 100),
    ]
    game = Game(heroes)
    threatened = Actor("outer_tower", 300, 300, "blue", 500, 1000)
    safe = Actor("inner_tower", 800, 500, "blue", 1000, 1000)
    game.towers = [threatened, safe]
    game.minions = [Actor("red_minion_0", 320, 300, "red"), Actor("red_minion_1", 330, 310, "red")]
    game.active_boss = Actor("boss", 350, 300, "red")
    manager = QuietManager(game)
    accepted = manager.command_protect_tower(silent=True)
    cases.append({"label": "protect_most_threatened", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(4)
    game = Game(heroes)
    manager = QuietManager(game)
    accepted = manager.command_protect_castle(silent=True)
    cases.append({"label": "protect_castle", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(3)
    game = Game(heroes)
    game.active_boss = Actor("boss", 700, 300, "red")
    manager = QuietManager(game)
    accepted = manager.command_attack_boss(silent=True)
    cases.append({"label": "attack_boss", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(3)
    game = Game(heroes)
    game.ai.heroes = [
        Hero("dealer_low", 750, 250, "red", damage_dealt=125),
        Hero("dealer_high", 800, 300, "red", damage_dealt=900),
        Hero("dealer_dead", 810, 320, "red", damage_dealt=5000),
    ]
    game.ai.heroes[-1].alive = False
    manager = QuietManager(game)
    accepted = manager.command_attack_damage_dealer(silent=True)
    cases.append({"label": "attack_damage_dealer", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = _heroes(2)
    game = Game(heroes)
    manager = QuietManager(game)
    manager.hold_start(TacticalCommand.GATHER, 600, 350)
    for _ in range(5):
        manager.update()
    manager.hold_end(TacticalCommand.GATHER)
    cases.append({"label": "quick_tap_keeps_duration", "accepted": True, "state": _snapshot(manager, game)})

    heroes = _heroes(2)
    game = Game(heroes)
    manager = QuietManager(game)
    manager.hold_start(TacticalCommand.PROTECT_CASTLE)
    for _ in range(35):
        manager.update()
    manager.hold_end(TacticalCommand.PROTECT_CASTLE)
    cases.append({"label": "long_hold_release_tail", "accepted": True, "state": _snapshot(manager, game)})

    heroes = _heroes(2)
    game = Game(heroes)
    manager = QuietManager(game)
    accepted = manager.hold_start(TacticalCommand.ATTACK_BOSS)
    for _ in range(10):
        manager.update()
    game.active_boss = Actor("late_boss", 700, 300, "red")
    for _ in range(5):
        manager.update()
    cases.append({"label": "armed_hold_waits_for_boss", "accepted": accepted, "state": _snapshot(manager, game)})

    heroes = [Hero("blue_0", 640, 360), Hero("blue_1", 650, 360), Hero("blue_2", 630, 360)]
    game = Game(heroes)
    game.active_boss = Actor("far_boss", 700, 360, "red")
    game.towers = [Actor("near_tower", 665, 360, "red")]
    game.ai.heroes = [Hero("enemy_hero", 680, 360, "red", damage_dealt=20)]
    manager = QuietManager(game)
    manager.hold_start(TacticalCommand.GATHER, 640, 360)
    for _ in range(GATHER_PUSH_DELAY_FRAMES):
        manager.update()
    cases.append({"label": "held_gather_push", "accepted": True, "state": _snapshot(manager, game)})

    heroes = _heroes(3)
    game = Game(heroes)
    game.blue_base.hp = 600
    game.blue_base.max_hp = 2000
    game.minions = [Actor("red_minion_0", 120, 600, "red"), Actor("red_minion_1", 140, 610, "red")]
    manager = QuietManager(game)
    manager._auto_check_timer = 89
    manager.update()
    cases.append({"label": "auto_protect_castle", "accepted": True, "state": _snapshot(manager, game)})

    return {
        "policy": {
            "duration": 600,
            "cooldown": 30,
            "hold_tap_max": HOLD_TAP_MAX_FRAMES,
            "hold_release_tail": HOLD_RELEASE_TAIL,
            "gather_push_delay": GATHER_PUSH_DELAY_FRAMES,
            "commands": [
                TacticalCommand.GATHER,
                TacticalCommand.PROTECT_TOWER,
                TacticalCommand.PROTECT_CASTLE,
                TacticalCommand.ATTACK_BOSS,
                TacticalCommand.ATTACK_DAMAGE_DEALER,
            ],
        },
        "cases": cases,
    }


def main():
    with redirect_stdout(StringIO()):
        actual = source_fixture()
    expected = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    if expected != actual:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        if expected is not None:
            raise SystemExit("FAIL: tactical command source fixture drift (fixture refreshed)")
    print(f"PASS: {len(actual['cases'])} tactical command source cases")


if __name__ == "__main__":
    main()
