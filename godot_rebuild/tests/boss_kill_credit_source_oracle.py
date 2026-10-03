"""Read-only source oracle for boss defeat attribution (Game._process_boss_kill).

Executes the real `Boss.take_damage` lethal branch (the only place that stores
`_killed_by`) together with the real `Game._killer_is_hero`,
`Game._process_boss_kill` and `Game._unlock_achievement` methods from
`_core.py`, against a stub game object that records the source's achievement
call payload. Boss classes and helpers come from `boss_core_source_oracle`, so
`bosses/boss_data.py`, `bosses/base_boss.py` and `hero_archetypes` are imported
unchanged and no pygame/game import happens.

Four scenarios are recorded per boss type: a blue hero landing the lethal blow,
a lethal blow with no source at all (cleave/burn), a non-hero blue attacker and
a same-team hero. `--write` rewrites the fixture from the source.
"""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from boss_core_source_oracle import boss_class as core_boss_class  # noqa: E402
from boss_core_source_oracle import namespace as core_namespace  # noqa: E402
from bosses.boss_data import get_all_boss_types  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/boss_kill_credit_source.json"

GAME_METHODS = ("_killer_is_hero", "_process_boss_kill", "_unlock_achievement")

# (label, killer kind, killer team). `None` means `Boss.take_damage(source=None)`,
# which is how the source calls cleave splash and the burn tick.
KILLER_CASES = (
    ("blue_hero_lethal_hit", "hero", "blue"),
    ("source_omitted_lethal_hit", "none", None),
    ("minion_lethal_hit", "minion", "blue"),
    ("same_team_hero_lethal_hit", "hero", "red"),
)


class RecordingEffects:
    """Stands in for `EffectManager`; records the source's FX call payload."""

    def __init__(self):
        self.unlock_calls = []
        self.damage_numbers = []

    def unlock_achievement(self, title, description, icon_type="star"):
        self.unlock_calls.append(
            {"title": title, "description": description, "icon_type": icon_type}
        )

    def add_damage_number(self, x, y, text, is_critical=False, damage_type="normal"):
        self.damage_numbers.append(
            {
                "x": float(x),
                "y": float(y),
                "text": text,
                "is_critical": bool(is_critical),
                "damage_type": damage_type,
            }
        )


class SilentSound:
    def __init__(self, *args, **kwargs):
        pass

    def play(self, *args, **kwargs):
        pass


def game_class():
    """Exec the real Game kill-attribution methods on a base-less class."""
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Game")
    body = [
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name in GAME_METHODS
    ]
    assert {node.name for node in body} == set(GAME_METHODS), "Game kill-credit methods drifted"
    cls = ast.ClassDef(name="SourceGameKillCredit", bases=[], keywords=[], body=body, decorator_list=[])
    env = {"SoundManager": SilentSound}
    exec(  # noqa: S102 - executing the original source methods
        compile(
            ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
            "<source boss kill credit>",
            "exec",
        ),
        env,
    )
    return env["SourceGameKillCredit"]


def credit_game(cls):
    """Fresh stub Game: only the state `_process_boss_kill` touches."""
    game = cls()
    game.achievements_unlocked = set()
    game.effects = RecordingEffects()
    game.miniboss_kill_count = 0
    game.trueboss_kill_count = 0
    return game


def killer_of(kind, team):
    if kind == "none":
        return None
    if kind == "minion":
        # Source Minion/Tower/Castle carry neither `hero_type` nor `skills`.
        return SimpleNamespace(team=team, kills=0)
    # Source Hero: `hero_type` + `skills` are exactly `_killer_is_hero`'s gate.
    return SimpleNamespace(
        team=team,
        kills=0,
        name="Kaizen",
        hero_type="kaizen",
        skills=["q", "w", "e", "r"],
    )


def achievement_row(game):
    if not game.effects.unlock_calls:
        return None
    call = game.effects.unlock_calls[0]
    floating = game.effects.damage_numbers[0] if game.effects.damage_numbers else None
    row = dict(call)
    row["achievement_id"] = sorted(game.achievements_unlocked)[0]
    row["floating_text"] = None if floating is None else [floating["x"], floating["y"], floating["text"]]
    return row


def kill_credit_cases(env, boss_cls, lane_path, game_cls):
    result = []
    for boss_type in sorted(get_all_boss_types()):
        for label, kind, team in KILLER_CASES:
            boss = boss_cls(boss_type, lane_path)
            boss.hp = 1
            killer = killer_of(kind, team)
            game = credit_game(game_cls)
            boss.take_damage(
                int(boss.damage), boss.team, damage_type="normal", source=killer, school="physical"
            )
            assert not boss.alive and boss.defeated, "lethal case must defeat the boss"
            assert getattr(boss, "_killed_by", "missing") is killer, "Boss._killed_by drifted"
            kills_before = 0 if killer is None else int(killer.kills)
            game._process_boss_kill(boss)
            result.append(
                {
                    "boss_type": boss_type,
                    "label": label,
                    "boss_class": str(boss.boss_class),
                    "killer_kind": kind,
                    "killer_team": team,
                    "killed_by_present": boss._killed_by is not None,
                    "credited_kills": (0 if killer is None else int(killer.kills)) - kills_before,
                    "miniboss_kill_count": int(game.miniboss_kill_count),
                    "trueboss_kill_count": int(game.trueboss_kill_count),
                    "achievement": achievement_row(game),
                }
            )
    return result


def source_fixture():
    env = core_namespace()
    boss_cls = core_boss_class(env)
    game_cls = game_class()
    from check_source_contract import source_lanes

    lane_path = source_lanes()["mid"]
    cases = kill_credit_cases(env, boss_cls, lane_path, game_cls)
    return {"killer_cases": cases}


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["killer_cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss kill credit source drift"
        print(
            "PASS: Boss kill credit — %d deadly-hit cases across %d boss types"
            % (len(actual["killer_cases"]), len({row["boss_type"] for row in actual["killer_cases"]}))
        )


if __name__ == "__main__":
    main()
