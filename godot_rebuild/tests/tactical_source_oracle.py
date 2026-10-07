"""Read-only oracle for the player tactical command layer.

`tactical_commands.py` imports without pygame, so this oracle runs the REAL
`TacticalCommandManager` against stub entities and records every mutation the
Godot port (`scripts/match/tactical_commands.gd`) must reproduce: command state
and timers, per-hero destination/follow/target values, feedback text and color,
the sound each order plays, the HOLD/tap lifecycle, the GATHER follow-up push
and the AUTO-PROTECT evaluation.

`_entity.credit_hero_damage` is extracted by AST because `_entity` imports pygame
at module scope; it feeds the ATTACK DAMAGE DEALER ranking.

The scenarios are declarative: `tests/tactical_checks.gd` replays the very same
`world` + `actions` payload against the native port and compares scalars exactly.
Coordinates are rounded to f32 where the rebuild stores them in a `Vector2`, and
are chosen with a clear margin from every radius threshold so `math.hypot`
(source) and `sqrt(dx*dx + dy*dy)` (native) cannot disagree.

Run: python godot_rebuild/tests/tactical_source_oracle.py
"""
import ast
import contextlib
import io
import json
import random
import struct
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
FIXTURE = TESTS / "fixtures" / "tactical_source.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tactical_commands as source_module  # noqa: E402  read-only source of truth

SOUNDS = []
ROLL = [0.99]
NOTIFICATIONS = []
EFFECTS = []


def _install_stubs() -> None:
    """Give the source's lazy imports something harmless to land on."""
    system = types.ModuleType("_system")

    class SoundManager:
        def play(self, name, volume_mult=1.0, **_kwargs):
            SOUNDS.append([str(name), float(volume_mult)])

    system.SoundManager = SoundManager
    sys.modules["_system"] = system

    mobile = types.ModuleType("mobile")
    mobile.__path__ = []
    sidepanel = types.ModuleType("mobile.sidepanel")
    sidepanel.beri_tahu_global = lambda text, color, duration: NOTIFICATIONS.append(
        [str(text), list(color), int(duration)]
    )
    mobile.sidepanel = sidepanel
    sys.modules["mobile"] = mobile
    sys.modules["mobile.sidepanel"] = sidepanel


class StubEntity:
    """Hero / minion / tower / castle / boss stand-in for the manager."""

    def __init__(self, spec, kind):
        self.kind = kind
        self.id = int(spec["id"])
        self.name = str(spec.get("name", kind))
        self.team = str(spec.get("team", "blue"))
        self.x = float(spec.get("x", 0.0))
        self.y = float(spec.get("y", 0.0))
        self.hp = float(spec.get("hp", 1000.0))
        self.max_hp = float(spec.get("max_hp", 1000.0))
        self.alive = bool(spec.get("alive", True))
        self.range = float(spec.get("range", 110.0))
        self.damage_dealt = int(spec.get("damage_dealt", 0))
        self.is_retreating = bool(spec.get("is_retreating", False))
        self.destination = None
        self.destination_auto = False
        self.follow_target = None
        self.target = None

    def move_to(self, x, y, auto=False):
        # _entity.py Hero.move_to (line 3571).
        self.destination = (float(x), float(y))
        self.destination_auto = bool(auto)
        self.follow_target = None
        self.is_retreating = False


class StubGame:
    def __init__(self, world):
        self.state = str(world.get("state", "playing"))
        self.wave_number = int(world.get("wave", 1))
        mouse = world.get("mouse", [0, 0])
        self.mouse_x = float(mouse[0])
        self.mouse_y = float(mouse[1])
        self.heroes = [StubEntity(spec, "hero") for spec in world.get("heroes", [])]
        self.minions = [StubEntity(spec, "minion") for spec in world.get("minions", [])]
        self.towers = [StubEntity(spec, "tower") for spec in world.get("towers", [])]
        self.ai = types.SimpleNamespace(
            heroes=[StubEntity(spec, "enemy_hero") for spec in world.get("enemy_heroes", [])]
        )
        blue = world.get("blue_castle")
        red = world.get("red_castle")
        self.blue_base = StubEntity(blue, "castle") if blue else None
        self.red_base = StubEntity(red, "castle") if red else None
        self.bases = [base for base in (self.blue_base, self.red_base) if base is not None]
        boss = world.get("boss")
        self.active_boss = StubEntity(boss, "boss") if boss else None
        selected = world.get("selected_hero")
        self.selected_hero = self.by_id().get(selected) if selected is not None else None
        self.effects = types.SimpleNamespace(
            add_damage_number=lambda *args, **kwargs: EFFECTS.append(["damage_number", list(args)]),
            add_death_explosion=lambda *args, **kwargs: EFFECTS.append(["explosion", list(args)]),
        )
        # `_render`'s UI.add_notification is a documented no-op in the source.
        self.ui = types.SimpleNamespace(add_notification=lambda *args, **kwargs: None)

    def by_id(self):
        registry = {}
        for group in (self.heroes, self.minions, self.towers, self.ai.heroes, self.bases):
            for entity in group:
                registry[entity.id] = entity
        if self.active_boss is not None:
            registry[self.active_boss.id] = self.active_boss
        return registry

    def spawn_boss(self, spec):
        self.active_boss = StubEntity(spec, "boss")
        return self.active_boss


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def entity_snapshot(entity):
    if entity is None:
        return None
    destination = None
    if entity.destination is not None:
        destination = [f32(entity.destination[0]), f32(entity.destination[1])]
    return {
        "id": entity.id,
        "x": f32(entity.x),
        "y": f32(entity.y),
        "hp": f32(entity.hp),
        "alive": bool(entity.alive),
        "destination": destination,
        "destination_auto": bool(entity.destination_auto),
        "follow": None if entity.follow_target is None else int(entity.follow_target.id),
        "target": None if entity.target is None else int(entity.target.id),
        "is_retreating": bool(entity.is_retreating),
        "damage_dealt": int(entity.damage_dealt),
    }


def state_snapshot(game, manager):
    gather = None
    if manager.gather_point is not None:
        gather = [float(manager.gather_point[0]), float(manager.gather_point[1])]
    return {
        "active_command": manager.active_command,
        "command_timer": int(manager.command_timer),
        "command_target": None if manager.command_target is None else int(manager.command_target.id),
        "gather_point": gather,
        "gather_point_timer": int(manager.gather_point_timer),
        "cooldown": int(manager.cooldown),
        "feedback_text": manager.feedback_text,
        "feedback_timer": int(manager.feedback_timer),
        "feedback_color": [int(channel) for channel in manager.feedback_color],
        "command_color": [int(channel) for channel in manager._get_command_color()],
        "status_text": manager.get_status_text(),
        "held_command": manager.held_command,
        "hold_elapsed": int(manager.hold_elapsed),
        "hold_has_fired": bool(manager._hold_has_fired),
        "gather_push_fired": bool(manager._gather_push_fired),
        "auto_check_timer": int(getattr(manager, "_auto_check_timer", 0)),
        "heroes": [entity_snapshot(hero) for hero in game.heroes],
        "red_heroes": [entity_snapshot(hero) for hero in game.ai.heroes],
        "threatened_tower": (
            None
            if manager._find_most_threatened_tower() is None
            else int(manager._find_most_threatened_tower().id)
        ),
        "nearest_enemy": (
            None
            if manager._find_nearest_enemy_target(*(manager.gather_point or (640.0, 360.0))) is None
            else int(
                manager._find_nearest_enemy_target(*(manager.gather_point or (640.0, 360.0))).id
            )
        ),
        "enemies_near_castle": (
            0
            if game.blue_base is None
            else manager._count_enemies_near(game.blue_base.x, game.blue_base.y, 300)
        ),
    }


def apply_action(game, manager, action, returned, trace):
    op = action[0]
    registry = game.by_id()
    if op == "hold":
        _, command, x, y, has_point, tower_id, follow_mouse = action
        args = []
        if has_point:
            args = [x, y]
        if command == "protect_tower" and int(tower_id) >= 0:
            args = [registry[int(tower_id)]]
        kwargs = {"follow_mouse": bool(follow_mouse)} if follow_mouse else {}
        returned.append(bool(manager.hold_start(command, *args, **kwargs)))
    elif op == "release":
        manager.hold_end(action[1] or None)
    elif op == "update":
        for _ in range(int(action[1])):
            manager.update()
    elif op == "snapshot":
        trace.append(state_snapshot(game, manager))
    elif op == "mouse":
        game.mouse_x = float(action[1])
        game.mouse_y = float(action[2])
    elif op == "select_hero":
        game.selected_hero = registry.get(action[1])
    elif op == "set_wave":
        game.wave_number = int(action[1])
    elif op == "state":
        game.state = str(action[1])
    elif op == "random":
        ROLL[0] = float(action[1])
    elif op == "hp":
        registry[int(action[1])].hp = float(action[2])
    elif op == "move":
        entity = registry[int(action[1])]
        entity.x = float(action[2])
        entity.y = float(action[3])
    elif op == "kill":
        entity = registry[int(action[1])]
        entity.alive = False
        entity.hp = 0.0
    elif op == "damage":
        registry[int(action[1])].damage_dealt = int(action[2])
    elif op == "spawn_boss":
        game.spawn_boss(action[1])
    else:
        raise AssertionError("unknown oracle action: %r" % (op,))


def run_scenario(scenario):
    game = StubGame(scenario["world"])
    manager = source_module.TacticalCommandManager(game)
    returned = []
    trace = []
    del SOUNDS[:]
    del NOTIFICATIONS[:]
    del EFFECTS[:]
    original_roll = random.random
    random.random = lambda: ROLL[0]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            for action in scenario["actions"]:
                apply_action(game, manager, action, returned, trace)
            final = state_snapshot(game, manager)
    finally:
        random.random = original_roll
    scenario["returned"] = returned
    scenario["sounds"] = [name for name, _volume in SOUNDS]
    scenario["sound_volumes"] = [volume for _name, volume in SOUNDS]
    scenario["notifications"] = [text for text, _color, _duration in NOTIFICATIONS]
    scenario["final"] = final
    scenario["trace"] = trace
    return scenario


# ── world building helpers (also the fixture vocabulary) ──
BLUE_CASTLE = {"id": 90, "name": "Blue Castle", "team": "blue", "x": 100, "y": 620,
               "hp": 5000, "max_hp": 5000}
RED_CASTLE = {"id": 91, "name": "Red Castle", "team": "red", "x": 1180, "y": 100,
              "hp": 5000, "max_hp": 5000}


def hero(entity_id, x, y, **overrides):
    spec = {"id": entity_id, "name": "Hero %d" % entity_id, "team": "blue", "x": x, "y": y,
            "hp": 1000, "max_hp": 1000, "range": 110, "alive": True}
    spec.update(overrides)
    return spec


def tower(entity_id, team, x, y, hp=800, max_hp=800, name=None):
    return {"id": entity_id, "name": name or ("Archer %d" % entity_id), "team": team,
            "x": x, "y": y, "hp": hp, "max_hp": max_hp, "alive": True}


def minion(entity_id, team, x, y, alive=True):
    return {"id": entity_id, "name": "Goblin %d" % entity_id, "team": team, "x": x, "y": y,
            "hp": 100, "max_hp": 100, "alive": alive}


def enemy_hero(entity_id, x, y, damage_dealt=0, name=None, alive=True):
    return {"id": entity_id, "name": name or ("Red %d" % entity_id), "team": "red", "x": x,
            "y": y, "hp": 1000, "max_hp": 1000, "range": 110, "alive": alive,
            "damage_dealt": damage_dealt}


def boss(entity_id, x, y, hp=8000, max_hp=8000, team="red", name="Gornak"):
    return {"id": entity_id, "name": name, "team": team, "x": x, "y": y, "hp": hp,
            "max_hp": max_hp, "alive": True, "range": 140}


def world(heroes=(), towers=(), minions=(), enemy_heroes=(), active_boss=None, wave=1,
          state="playing", mouse=(0, 0), selected_hero=None, blue_castle=BLUE_CASTLE,
          red_castle=RED_CASTLE):
    return {
        "state": state,
        "wave": wave,
        "mouse": list(mouse),
        "selected_hero": selected_hero,
        "heroes": list(heroes),
        "towers": list(towers),
        "minions": list(minions),
        "enemy_heroes": list(enemy_heroes),
        "boss": active_boss,
        "blue_castle": dict(blue_castle) if blue_castle else None,
        "red_castle": dict(red_castle) if red_castle else None,
    }


THREE_HEROES = (hero(1, 300, 400), hero(2, 340, 460), hero(3, 260, 480))
FOUR_HEROES = THREE_HEROES + (hero(4, 400, 300),)
BLUE_TOWERS = (tower(20, "blue", 300, 200), tower(21, "blue", 500, 340),
               tower(22, "blue", 640, 640))
RED_TOWERS = (tower(30, "red", 650, 90), tower(31, "red", 780, 400))


def scenarios():
    cases = []

    def add(name, world_spec, actions):
        cases.append({"name": name, "world": world_spec, "actions": actions})

    add(
        "gather_explicit_point",
        world(heroes=THREE_HEROES, towers=BLUE_TOWERS + RED_TOWERS,
              minions=(minion(40, "red", 900, 300),)),
        [["hold", "gather", 700, 400, True, -1, False], ["snapshot"],
         ["release", "gather"], ["snapshot"]],
    )
    add(
        "gather_default_selected_hero",
        world(heroes=THREE_HEROES, selected_hero=2),
        [["hold", "gather", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "gather_default_selected_dead_hero",
        world(heroes=(hero(1, 300, 400), hero(2, 340, 460, alive=False)), selected_hero=2),
        [["hold", "gather", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "gather_default_average_mix",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "gather_default_average_clamped",
        world(heroes=(hero(1, 1150, 90), hero(2, 1200, 120), hero(3, 1180, 80))),
        [["hold", "gather", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "gather_default_single_hero",
        world(heroes=(hero(1, 200, 600),)),
        [["hold", "gather", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "gather_no_heroes",
        world(heroes=(hero(1, 300, 400, alive=False),)),
        [["hold", "gather", 500, 400, True, -1, False], ["snapshot"]],
    )
    add(
        "gather_outside_arena_point",
        world(heroes=THREE_HEROES, mouse=(1400, 800)),
        [["hold", "gather", 1400, 800, True, -1, True], ["snapshot"]],
    )
    add(
        "gather_hold_follow_mouse_refresh",
        world(heroes=THREE_HEROES, mouse=(600, 300)),
        [["hold", "gather", 600, 300, True, -1, True], ["snapshot"],
         ["mouse", 720, 480], ["update", 30], ["snapshot"],
         ["update", 30], ["snapshot"]],
    )
    # Source quirk, locked by this fixture: a TAPPED gather can never reach the
    # `command_timer == 300` follow-up push, because the gather marker (and with
    # it `gather_point`) already expires at 150 ticks. Only the HOLD path
    # (`hold_elapsed >= GATHER_PUSH_DELAY_FRAMES`) pushes in the real game.
    add(
        "gather_tap_marker_expires_before_push",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410), hero(3, 700, 380)),
              towers=BLUE_TOWERS + RED_TOWERS, minions=(minion(40, "red", 900, 420),)),
        [["hold", "gather", 700, 400, True, -1, False], ["release", "gather"],
         ["update", 149], ["snapshot"], ["update", 1], ["snapshot"], ["update", 150],
         ["snapshot"], ["update", 300], ["snapshot"]],
    )
    add(
        "gather_push_waits_for_arrival",
        world(heroes=(hero(1, 200, 600), hero(2, 210, 610), hero(3, 700, 400)),
              minions=(minion(40, "red", 900, 420),)),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"],
         ["move", 1, 690, 405], ["move", 2, 715, 395], ["update", 30], ["snapshot"]],
    )
    add(
        "gather_hold_push_locks_target",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410), hero(3, 700, 380)),
              minions=(minion(40, "red", 900, 420),)),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"],
         ["move", 40, 950, 500], ["update", 60], ["snapshot"]],
    )
    add(
        "gather_hold_push_without_enemy_regroups",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410), hero(3, 700, 380)),
              minions=(minion(40, "red", 900, 420),), red_castle=None),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"],
         ["kill", 40], ["update", 40], ["snapshot"]],
    )
    add(
        "protect_tower_most_threatened",
        world(heroes=FOUR_HEROES,
              towers=(tower(20, "blue", 300, 200, hp=800), tower(21, "blue", 500, 340, hp=300),
                      tower(22, "blue", 640, 640, hp=800)) + RED_TOWERS,
              minions=(minion(40, "red", 520, 360), minion(41, "red", 540, 320))),
        [["hold", "protect_tower", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_tower_threat_sends_three",
        world(heroes=FOUR_HEROES,
              towers=(tower(20, "blue", 300, 200), tower(21, "blue", 500, 340, hp=700)),
              minions=(minion(40, "red", 520, 360), minion(41, "red", 540, 320),
                       minion(42, "red", 480, 380))),
        [["hold", "protect_tower", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_tower_explicit_target",
        world(heroes=FOUR_HEROES, towers=BLUE_TOWERS + RED_TOWERS,
              minions=(minion(40, "red", 660, 620),)),
        [["hold", "protect_tower", 0, 0, False, 22, False], ["snapshot"]],
    )
    add(
        "protect_tower_dead_explicit_reselects",
        world(heroes=THREE_HEROES,
              towers=(tower(20, "blue", 300, 200, hp=1), tower(21, "blue", 500, 340, hp=400)),
              minions=(minion(40, "red", 520, 360), minion(41, "red", 540, 320))),
        [["kill", 20], ["hold", "protect_tower", 0, 0, False, 20, False], ["snapshot"]],
    )
    add(
        "protect_tower_zero_threat_prefers_lowest_hp",
        world(heroes=THREE_HEROES,
              towers=(tower(20, "blue", 300, 200, hp=500), tower(21, "blue", 900, 340, hp=700))),
        [["hold", "protect_tower", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_tower_fallback_front_tower",
        world(heroes=THREE_HEROES,
              towers=(tower(20, "blue", 300, 200, hp=800), tower(21, "blue", 500, 340, hp=800),
                      tower(22, "blue", 640, 640, hp=800)),
              minions=(minion(40, "red", 660, 620),)),
        [["hold", "protect_tower", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_tower_none_available",
        world(heroes=THREE_HEROES, towers=RED_TOWERS),
        [["hold", "protect_tower", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_tower_no_heroes",
        world(heroes=(hero(1, 300, 400, alive=False),), towers=BLUE_TOWERS),
        [["hold", "protect_tower", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_castle_ring",
        world(heroes=FOUR_HEROES),
        [["hold", "protect_castle", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_castle_clamped_edge",
        world(heroes=(hero(1, 200, 600), hero(2, 220, 610), hero(3, 240, 620)),
              blue_castle={"id": 90, "name": "Blue Castle", "team": "blue", "x": 40, "y": 690,
                           "hp": 5000, "max_hp": 5000}),
        [["hold", "protect_castle", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "protect_castle_destroyed",
        world(heroes=THREE_HEROES,
              blue_castle={"id": 90, "name": "Blue Castle", "team": "blue", "x": 100, "y": 620,
                           "hp": 0, "max_hp": 5000, "alive": False}),
        [["hold", "protect_castle", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "attack_boss_focus",
        world(heroes=THREE_HEROES, active_boss=boss(60, 900, 300)),
        [["hold", "attack_boss", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "attack_boss_none",
        world(heroes=THREE_HEROES),
        [["hold", "attack_boss", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "attack_boss_dead",
        world(heroes=THREE_HEROES,
              active_boss={"id": 60, "name": "Gornak", "team": "red", "x": 900, "y": 300,
                           "hp": 0, "max_hp": 8000, "alive": False}),
        [["hold", "attack_boss", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "attack_damage_dealer_focus",
        world(heroes=THREE_HEROES,
              enemy_heroes=(enemy_hero(70, 1000, 200, damage_dealt=450),
                            enemy_hero(71, 900, 500, damage_dealt=900),
                            enemy_hero(72, 800, 300, damage_dealt=900))),
        [["hold", "attack_damage_dealer", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "attack_damage_dealer_skips_dead",
        world(heroes=THREE_HEROES,
              enemy_heroes=(enemy_hero(70, 1000, 200, damage_dealt=4500, alive=False),
                            enemy_hero(71, 900, 500, damage_dealt=120))),
        [["hold", "attack_damage_dealer", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "attack_damage_dealer_none",
        world(heroes=THREE_HEROES),
        [["hold", "attack_damage_dealer", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "hold_tap_keeps_duration",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 5],
         ["release", "gather"], ["snapshot"]],
    )
    add(
        "hold_long_release_clamps_timer",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 25], ["snapshot"],
         ["release", "gather"], ["snapshot"], ["update", 31], ["snapshot"]],
    )
    add(
        "hold_repeat_press_is_noop",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 2],
         ["hold", "gather", 700, 400, True, -1, False], ["snapshot"]],
    )
    add(
        "hold_release_other_command_ignored",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 700, 400, True, -1, False], ["release", "attack_boss"],
         ["snapshot"]],
    )
    add(
        "hold_armed_waits_for_boss",
        world(heroes=THREE_HEROES),
        [["hold", "attack_boss", 0, 0, False, -1, False], ["snapshot"], ["update", 15],
         ["spawn_boss", boss(60, 900, 300)], ["update", 1], ["snapshot"], ["update", 40],
         ["snapshot"]],
    )
    add(
        "cooldown_blocks_second_order",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 700, 400, True, -1, False],
         ["hold", "protect_castle", 0, 0, False, -1, False], ["snapshot"], ["update", 15],
         ["snapshot"], ["update", 16], ["snapshot"]],
    )
    add(
        "command_expiry_clears_state",
        world(heroes=THREE_HEROES, towers=BLUE_TOWERS),
        [["hold", "protect_tower", 0, 0, False, 21, False], ["release", "protect_tower"],
         ["update", 149], ["snapshot"], ["update", 1], ["snapshot"], ["update", 450],
         ["snapshot"]],
    )
    add(
        "stale_command_target_survives_gather",
        world(heroes=THREE_HEROES, towers=BLUE_TOWERS),
        [["hold", "protect_tower", 0, 0, False, 21, False], ["release", "protect_tower"],
         ["update", 31], ["hold", "gather", 700, 400, True, -1, False], ["snapshot"]],
    )
    add(
        "state_not_playing_blocks_orders",
        world(heroes=THREE_HEROES, state="victory"),
        [["hold", "gather", 700, 400, True, -1, False], ["snapshot"], ["update", 40],
         ["snapshot"]],
    )
    add(
        "auto_protect_castle",
        world(heroes=THREE_HEROES, towers=BLUE_TOWERS,
              minions=(minion(40, "red", 180, 600), minion(41, "red", 220, 560)),
              blue_castle={"id": 90, "name": "Blue Castle", "team": "blue", "x": 100, "y": 620,
                           "hp": 1500, "max_hp": 5000}),
        [["update", 89], ["snapshot"], ["update", 1], ["snapshot"]],
    )
    add(
        "auto_protect_castle_boss_counts_double",
        world(heroes=THREE_HEROES, active_boss=boss(60, 200, 560),
              blue_castle={"id": 90, "name": "Blue Castle", "team": "blue", "x": 100, "y": 620,
                           "hp": 1000, "max_hp": 5000}),
        [["update", 90], ["snapshot"]],
    )
    add(
        "auto_protect_tower_low_hp",
        world(heroes=THREE_HEROES,
              towers=(tower(20, "blue", 300, 200, hp=800), tower(21, "blue", 500, 340, hp=300)),
              minions=(minion(40, "red", 520, 360), minion(41, "red", 540, 320))),
        [["update", 90], ["snapshot"]],
    )
    add(
        "auto_protect_tower_swarm",
        world(heroes=THREE_HEROES, towers=(tower(21, "blue", 500, 340),),
              minions=(minion(40, "red", 520, 360), minion(41, "red", 540, 320),
                       minion(42, "red", 480, 380), minion(43, "red", 560, 300))),
        [["update", 90], ["snapshot"]],
    )
    add(
        "auto_protect_prefers_castle_over_tower",
        world(heroes=THREE_HEROES, towers=(tower(21, "blue", 500, 340, hp=300),),
              minions=(minion(40, "red", 520, 360), minion(41, "red", 540, 320),
                       minion(42, "red", 180, 600), minion(43, "red", 220, 560)),
              blue_castle={"id": 90, "name": "Blue Castle", "team": "blue", "x": 100, "y": 620,
                           "hp": 1000, "max_hp": 5000}),
        [["update", 90], ["snapshot"]],
    )
    add(
        "auto_attack_boss_roll_fires",
        world(heroes=THREE_HEROES, wave=11, active_boss=boss(60, 900, 300, hp=5000),
              minions=(minion(40, "red", 1200, 690),)),
        [["random", 0.1], ["update", 90], ["snapshot"]],
    )
    add(
        "auto_attack_boss_roll_skips",
        world(heroes=THREE_HEROES, wave=11, active_boss=boss(60, 900, 300, hp=5000),
              minions=(minion(40, "red", 1200, 690),)),
        [["random", 0.5], ["update", 90], ["snapshot"]],
    )
    add(
        "auto_attack_boss_needs_wave_eleven",
        world(heroes=THREE_HEROES, wave=10, active_boss=boss(60, 900, 300, hp=5000),
              minions=(minion(40, "red", 1200, 690),)),
        [["random", 0.0], ["update", 90], ["snapshot"]],
    )
    add(
        "auto_attack_boss_needs_damaged_boss",
        world(heroes=THREE_HEROES, wave=12, active_boss=boss(60, 900, 300, hp=7000),
              minions=(minion(40, "red", 1200, 690),)),
        [["random", 0.0], ["update", 90], ["snapshot"]],
    )
    add(
        "auto_check_pauses_while_command_active",
        world(heroes=THREE_HEROES, towers=BLUE_TOWERS),
        [["hold", "gather", 700, 400, True, -1, False], ["release", "gather"], ["update", 200],
         ["snapshot"]],
    )
    # `_find_nearest_enemy_target` is only consumed by the live HOLD push, so
    # every priority case runs through `hold_elapsed >= 240`.
    add(
        "nearest_enemy_boss_wins_distance_tie",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410)),
              towers=(tower(31, "red", 800, 400),), active_boss=boss(60, 600, 400),
              minions=(minion(40, "red", 700, 300),)),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"]],
    )
    add(
        "nearest_enemy_tower_closer_than_boss",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410)),
              towers=(tower(31, "red", 780, 400),), active_boss=boss(60, 1000, 400),
              minions=(minion(40, "red", 720, 400),)),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"]],
    )
    add(
        "nearest_enemy_hero_closer_than_tower",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410)),
              towers=(tower(31, "red", 900, 400),),
              enemy_heroes=(enemy_hero(70, 750, 400),), minions=(minion(40, "red", 720, 400),)),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"]],
    )
    add(
        "nearest_enemy_ignores_minions_while_bigger_target_lives",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410)),
              towers=(tower(31, "red", 900, 400),), minions=(minion(40, "red", 720, 400),)),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"]],
    )
    add(
        "nearest_enemy_falls_back_to_minion",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410)),
              minions=(minion(40, "red", 900, 420), minion(41, "red", 1000, 500))),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"]],
    )
    add(
        "nearest_enemy_falls_back_to_red_castle",
        world(heroes=(hero(1, 690, 400), hero(2, 710, 410))),
        [["hold", "gather", 700, 400, True, -1, False], ["update", 240], ["snapshot"]],
    )
    add(
        "feedback_banner_lifecycle",
        world(heroes=THREE_HEROES),
        [["hold", "gather", 700, 400, True, -1, False], ["release", "gather"], ["snapshot"],
         ["update", 150], ["snapshot"], ["update", 29], ["snapshot"], ["update", 1],
         ["snapshot"]],
    )
    add(
        "status_text_variants",
        world(heroes=THREE_HEROES, towers=BLUE_TOWERS, active_boss=boss(60, 900, 300)),
        [["snapshot"], ["hold", "protect_tower", 0, 0, False, 21, False], ["snapshot"],
         ["release", "protect_tower"], ["update", 601], ["snapshot"],
         ["state", "victory"], ["hold", "attack_boss", 0, 0, False, -1, False], ["snapshot"]],
    )
    add(
        "retreat_and_auto_destination_cleared",
        world(heroes=(hero(1, 300, 400, is_retreating=True),
                      hero(2, 340, 460, is_retreating=True)),
              towers=BLUE_TOWERS),
        [["hold", "gather", 700, 400, True, -1, False], ["snapshot"], ["update", 31],
         ["hold", "protect_castle", 0, 0, False, -1, False], ["snapshot"]],
    )
    return cases


def credit_function():
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"), filename="_entity.py")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "credit_hero_damage":
            namespace = {}
            exec(
                compile(ast.Module(body=[node], type_ignores=[]), "<credit_hero_damage>", "exec"),
                namespace,
            )
            return namespace["credit_hero_damage"]
    raise AssertionError("credit_hero_damage missing from _entity.py")


def credit_cases():
    credit = credit_function()
    amounts = [12.7, 40, 0.5, 0, -5.0, 7.25]
    totals = []
    attacker = types.SimpleNamespace(damage_dealt=0)
    for amount in amounts:
        credit(attacker, amount)
        totals.append(int(attacker.damage_dealt))
    untouched = types.SimpleNamespace(damage_dealt=25)
    credit(None, 500)
    credit(untouched, 0)
    fresh = types.SimpleNamespace()
    credit(fresh, 9.9)
    return {
        "amounts": amounts,
        "totals": totals,
        "none_source_total": int(untouched.damage_dealt),
        "missing_attribute_total": int(getattr(fresh, "damage_dealt", 0)),
    }


def source_fixture():
    _install_stubs()
    ROLL[0] = 0.99
    return {
        "constants": {
            "hold_tap_max_frames": source_module.HOLD_TAP_MAX_FRAMES,
            "hold_release_tail": source_module.HOLD_RELEASE_TAIL,
            "gather_push_delay_frames": source_module.GATHER_PUSH_DELAY_FRAMES,
            "cooldown_max": 30,
            "command_ticks": 600,
            "marker_ticks": 150,
            "feedback_ticks": 180,
            "blue_base": [source_module.BLUE_BASE_X, source_module.BLUE_BASE_Y],
            "red_base": [source_module.RED_BASE_X, source_module.RED_BASE_Y],
            "screen": [source_module.SCREEN_WIDTH, source_module.SCREEN_HEIGHT],
            "sound_volumes": {"ui_click": 0.8, "hero_skill": 0.9},
            "auto_check_ticks": 90,
            "auto_boss_roll": 0.2,
            "auto_boss_wave": 11,
        },
        "credit": credit_cases(),
        "scenarios": [run_scenario(dict(case)) for case in scenarios()],
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(
        "PASS: tactical source oracle — %d scenarios, %d snapshots, credit totals %s"
        % (
            len(fixture["scenarios"]),
            sum(len(case["trace"]) + 1 for case in fixture["scenarios"]),
            fixture["credit"]["totals"],
        )
    )


if __name__ == "__main__":
    main()
