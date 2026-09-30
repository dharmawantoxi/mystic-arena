"""AST oracle for Boss entrance rendering and death-effect presentation.

Only the source presentation boundaries are exercised here: the original
`_draw_entrance` method records its draw/text commands against a tiny fake
pygame surface, and the original `take_damage` method records the effect calls
made by the death branch. The Godot view uses the same scalar contract while
remaining renderer-native.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURE = Path(__file__).parent / "fixtures/boss_presentation_source.json"
ACTIVE_RECORD = []


class FakeRect:
    def __init__(self, center, width=100, height=30):
        self.x = int(center[0] - width / 2)
        self.y = int(center[1] - height / 2)


class FakeText:
    def __init__(self, text, color, record):
        self.text = text
        self.color = color
        self.alpha = 255
        self.record = record

    def set_alpha(self, alpha):
        self.alpha = int(alpha)

    def get_rect(self, center):
        return FakeRect(center, max(20, len(self.text) * 12), 30)


class FakeFont:
    def __init__(self, record):
        self.record = record

    def size(self, text):
        return (len(text) * 12, 30)

    def render(self, text, _antialias, color):
        return FakeText(text, color, self.record)


class FakeSurface:
    def __init__(self, record, size=(0, 0)):
        self.record = record
        self.size = size

    def blit(self, source, position):
        if isinstance(source, FakeText):
            self.record.append(
                {
                    "op": "text",
                    "text": source.text,
                    "color": list(source.color),
                    "alpha": source.alpha,
                    "x": int(position.x) if hasattr(position, "x") else int(position[0]),
                    "y": int(position.y) if hasattr(position, "y") else int(position[1]),
                }
            )
        else:
            self.record.append({"op": "surface", "size": list(source.size)})


class FakeDraw:
    def __init__(self, record):
        self.record = record

    def circle(self, _surface, color, _center, radius, *args):
        self.record.append({"op": "circle", "color": list(color), "radius": int(radius)})


class DynamicPygame:
    SRCALPHA = 1

    @property
    def draw(self):
        return FakeDraw(ACTIVE_RECORD)

    def Surface(self, size, _flags=0):
        return FakeSurface(ACTIVE_RECORD, size)


def _module(*nodes):
    return compile(
        ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[])),
        "<source boss presentation>",
        "exec",
    )


def source_methods():
    tree = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    wanted = {"_draw_entrance", "take_damage"}
    methods = [
        node for node in original.body if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    assert len(methods) == 2, "Re-audit Boss presentation methods before trusting this oracle"
    cls = ast.ClassDef(
        name="SourceBossPresentation",
        bases=[],
        keywords=[],
        body=methods,
        decorator_list=[],
    )
    env = {
        "math": math,
        "random": random,
        "SCREEN_WIDTH": 1280,
        "get_font": lambda *_args, **_kwargs: FakeFont(ACTIVE_RECORD),
        "pygame": DynamicPygame(),
    }
    exec(_module(cls), env)  # noqa: S102 - execute original source methods
    return env["SourceBossPresentation"]


def entrance_case(cls, label, boss_class, timer, maximum, text):
    global ACTIVE_RECORD
    record = []
    ACTIVE_RECORD = record
    boss = cls()
    boss.entrance_timer = timer
    boss.entrance_color = (120, 210, 190)
    boss.radius = 40 if boss_class == "mini" else 60
    boss.boss_class = boss_class
    boss.anim_time = 7
    boss.entrance_text = text
    boss._draw_entrance(FakeSurface(record), 640, 300, maximum)
    return {"label": label, "commands": record}


class Effects:
    def __init__(self):
        self.calls = []

    def add_damage_number(self, *args, **kwargs):
        self.calls.append({"name": "damage_number", "args": list(args), "kwargs": kwargs})

    def add_hit_particles(self, *args, **kwargs):
        self.calls.append({"name": "hit_particles", "args": list(args), "kwargs": kwargs})

    def add_death_explosion(self, *args, **kwargs):
        self.calls.append({"name": "death_explosion", "args": list(args), "kwargs": kwargs})

    def shake_screen(self, *args, **kwargs):
        self.calls.append({"name": "shake_screen", "args": list(args), "kwargs": kwargs})


class Game:
    def __init__(self):
        self.effects = Effects()


def death_case(cls, label, boss_class, hp, cap):
    game = Game()
    sys.modules["__main__"].game_instance = game
    stub = sys.modules.setdefault("_entity", ModuleType("_entity"))
    stub.resolve_damage_school = lambda _damage_type, _source, school: school
    stub.credit_hero_damage = lambda _source, _damage: None
    boss = cls()
    boss.damage_reduction = 0.20 if boss_class == "mini" else 0.30
    boss.defense_boost = False
    boss.max_damage_per_hit = cap
    boss.max_hp = 10000
    boss.hp = hp
    boss.hurt_flash_timer = 0
    boss.armor = 0
    boss.magic_resist = 0.0
    boss.dmg_amp_timer = 0
    boss.dmg_amp_amount = 0.0
    boss.armor_shred_amount = 0.0
    boss.alive = True
    boss.defeated = False
    boss.team = "red"
    boss.boss_class = boss_class
    boss.boss_type = "gornak" if boss_class == "mini" else "abaddon"
    boss.x = 100.0
    boss.y = 200.0
    boss.radius = 40
    boss.clear_calls = 0
    boss.clear_tower_debuffs = lambda: setattr(boss, "clear_calls", boss.clear_calls + 1)
    boss.take_damage(99999, "blue", "normal", None, "physical")
    return {
        "label": label,
        "alive": bool(boss.alive),
        "defeated": bool(boss.defeated),
        "hp": int(boss.hp),
        "hurt_flash_timer": int(boss.hurt_flash_timer),
        "clear_calls": int(boss.clear_calls),
        "effects": game.effects.calls,
    }


def source_fixture():
    cls = source_methods()
    return {
        "entrance": [
            entrance_case(cls, "mini_full", "mini", 120, 120, "Gornak awakens"),
            entrance_case(cls, "mini_mid", "mini", 60, 120, "Gornak awakens"),
            entrance_case(cls, "true_full", "true", 180, 180, "Abaddon descends"),
            entrance_case(cls, "true_early", "true", 45, 180, "Abaddon descends"),
        ],
        "death": [
            death_case(cls, "mini_death", "mini", 1200, 1200),
            death_case(cls, "true_death", "true", 800, 800),
        ],
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: boss entrance/death presentation source fixture")
    else:
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assert actual == expected, "Boss presentation source drift"
        print("PASS: Boss presentation — entrance draw gate and death effects")


if __name__ == "__main__":
    main()
