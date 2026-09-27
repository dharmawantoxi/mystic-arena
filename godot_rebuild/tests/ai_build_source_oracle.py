"""Read-only AST oracle for AIPlayer build and Tower Lv1 fallback/shot/upgrade.

Source RNG is replaced by controlled selection probes; no claim that Godot's seeded
stream matches Python's. Only source methods are executed, not pygame/Game imports.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ai_upgrade_source_oracle import compile_subset
from structure_source_oracle import ROOT, namespace

FIXTURE = Path(__file__).parent / "fixtures/ai_build_source.json"


class BulletReceipt:
    def __init__(self, x, y, target, damage, team, kind, special=None):
        self.damage = damage
        self.kind = kind
        self.special = special or {}


def source_fixture():
    env = namespace()
    env["TOWER_UPGRADE_PATHS"] = {
        path: env[path.upper() + "_LEVELS"] for path in ("archer", "cannon", "ice", "mage")
    }
    env.update(Bullet=BulletReceipt, math=math)
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower_type = compile_subset(tree, "Tower", (
        "__init__", "_apply_level_stats", "can_upgrade", "upgrade_cost", "upgrade",
        "_shoot", "_shoot_archer", "_shoot_cannon", "_shoot_ice", "_shoot_mage"), env)
    ai_type = compile_subset(tree, "AIPlayer", ("__init__", "_ai_reserve", "_try_build_tower"), env)
    result = {"attempts": [], "levels": [], "sampling": []}
    types = ["archer", "cannon", "ice", "mage"]
    weights = [0.35, 0.25, 0.20, 0.20]
    for draw in (0.0, 0.349999999, 0.35, 0.599999999, 0.60,
                 0.799999999, 0.80, 0.999999999):
        picker = random.Random(0)
        with patch.object(picker, "random", return_value=draw):
            result["sampling"].append(dict(draw=draw,
                chosen=picker.choices(types, weights=weights)[0]))

    # Shot helper imports are presentation geometry, not combat. Existing cannon,
    # ice, mage oracles exercise the real helpers separately; isolate shot semantics.
    helpers = {
        "towers.archer_tower": SimpleNamespace(get_archer_bow_position=lambda *args: (0, 0)),
        "towers.cannon_tower": SimpleNamespace(get_cannon_muzzle_position=lambda *args: (0, 0)),
        "towers.ice_tower": SimpleNamespace(get_ice_crystal_position=lambda *args: (0, 0)),
        "towers.mage_tower": SimpleNamespace(get_mage_crystal_position=lambda *args: (0, 0)),
    }
    with patch.dict(sys.modules, helpers):
        for path in ("archer", "cannon", "ice", "mage"):
            for reserve in (0, 400):
                for gold in (99 + reserve, 100 + reserve, 149 + reserve, 150 + reserve):
                    for empty in (0, 1, 3):
                        player = ai_type()
                        player.gold = gold
                        player._hero_purchase_target = "kaizen" if reserve else None
                        player._hero_purchase_target_cost = reserve
                        player._towers_ref = []
                        slots = [dict(x=500 + i * 20, y=340, lane="mid", taken=False)
                                 for i in range(empty)]
                        picks = []

                        def choice(candidates):
                            picks.append(["slot", len(candidates)])
                            return candidates[-1]

                        def choices(candidates, weights):
                            picks.append(["type", list(candidates), list(weights)])
                            return [path]

                        env["random"] = SimpleNamespace(choice=choice, choices=choices)
                        success = player._try_build_tower(slots)
                        tower = player._towers_ref[0] if success else None
                        result["attempts"].append(dict(
                            path=path, reserve=reserve, gold=gold, empty=empty,
                            success=success, after=player.gold, count=player.total_built,
                            picked=picks, taken=[s["taken"] for s in slots],
                            identity=tower.tower_type if tower else None,
                            level=tower.level if tower else None))
            tower = tower_type(500, 340, "red")
            tower.tower_type = path
            tower._apply_level_stats()
            target = SimpleNamespace(x=540, y=340, alive=True)
            tower.target = target
            tower.angle = 0.0
            tower._shoot([target])
            shot = tower.bullets[0]
            before = dict(
                path=tower.tower_type, level=tower.level, max_hp=tower.max_hp, hp=tower.hp,
                shield_max=tower.shield_max, shield=tower.shield, damage=tower.damage,
                range=tower.range, cd=tower.attack_cooldown, armor=tower.armor,
                splash=tower.splash, slow=tower.slow, chain=tower.chain,
                shot=dict(kind=shot.kind, damage=shot.damage, special=shot.special,
                          count=len(tower.bullets)))
            tower.hp, tower.shield = 1, 0
            # Lv1 path identity does NOT force the Lv2 upgrade path: AI tries cannon first.
            price = tower.upgrade_cost("cannon")
            upgraded = tower.upgrade("cannon")
            result["levels"].append(dict(before=before, price=price, upgraded=upgraded,
                after=dict(path=tower.tower_type, level=tower.level, max_hp=tower.max_hp,
                           hp=tower.hp, shield=tower.shield, damage=tower.damage)))
    return result


if __name__ == "__main__":
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "AI build source drift"
    print(f"PASS: AI build source oracle — {len(actual['attempts'])} attempts, "
          f"{len(actual['levels'])} level-1 paths")
