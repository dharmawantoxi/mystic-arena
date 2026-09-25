"""Execute original Archer upgrade/refund/muzzle/volley methods, without pygame.
Presentation import is injected with the original numeric bow-position helper.
"""
import ast
import json
import math
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from structure_source_oracle import ROOT, namespace, source_classes

FIXTURE = Path(__file__).parent / "fixtures/archer_upgrade_source.json"


def source_fixture():
    env = namespace()
    tower_type = source_classes(env)["Tower"]
    tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    tower = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Tower")
    names = {"can_upgrade", "upgrade_cost", "upgrade", "sell_value", "_shoot_archer"}
    for method in tower.body:
        if isinstance(method, ast.FunctionDef) and method.name in names:
            exec(compile(ast.Module(body=[method], type_ignores=[]), "<original Archer method>", "exec"), env)
            setattr(tower_type, method.name, env[method.name])
    bundle = ast.parse((ROOT / "towers/_bundle.py").read_text(encoding="utf-8"))
    archer = next(n for n in bundle.body if isinstance(n, ast.ClassDef) and n.name == "_NS_archer_tower")
    config = next(n.value for n in archer.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LEVEL_CONFIGS" for t in n.targets))
    helper = next(n for n in archer.body if isinstance(n, ast.FunctionDef) and n.name == "get_archer_bow_position")
    helper.decorator_list = []
    env["_NS_archer_tower"] = SimpleNamespace(LEVEL_CONFIGS=ast.literal_eval(config))
    exec(compile(ast.Module(body=[helper], type_ignores=[]), "<original muzzle>", "exec"), env)
    env["math"] = math
    env["Bullet"] = lambda x, y, target, damage, team, kind: dict(position=[x, y], target=target.id, damage=damage)
    stub = ModuleType("towers.archer_tower")
    stub.get_archer_bow_position = env["get_archer_bow_position"]
    obj = tower_type(500, 340, "blue")
    rows = []
    with patch.dict(sys.modules, {"towers": ModuleType("towers"), "towers.archer_tower": stub}):
        for level in range(1, 7):
            price = 0
            if level > 1:
                price = obj.upgrade_cost("archer")
                obj.hp, obj.shield, obj.timer, obj.no_damage_timer = 1, 0, 17, 9
                assert obj.upgrade("archer")
            row = dict(level=level, price=price, hp=obj.hp, max_hp=obj.max_hp,
                shield=obj.shield, damage=obj.damage, range=obj.range, cooldown=obj.attack_cooldown,
                armor=obj.armor, refund=obj.sell_value() or 50, next_price=obj.upgrade_cost("archer"),
                timer=obj.timer, no_damage_timer=obj.no_damage_timer, volleys=[])
            for side in (-1, 1):
                for count in (1, 2, 4):
                    # Primary target is NOT the first in source enemy order. Include dead/out-of-range candidates.
                    primary = SimpleNamespace(id=1, x=500 + side * 60, y=340, alive=True)
                    candidates = [SimpleNamespace(id=90, x=501, y=340, alive=False),
                                  SimpleNamespace(id=91, x=1500, y=340, alive=True)]
                    candidates += [SimpleNamespace(id=i + 2, x=500 + side * (70 + i * 10), y=340, alive=True)
                                   for i in range(count - 1)]
                    candidates.append(primary)
                    obj.target, obj.bullets = primary, []
                    obj._shoot_archer(candidates)
                    row["volleys"].append(dict(side=side, count=count, shots=obj.bullets))
            rows.append(row)
        assert not obj.upgrade("archer")
    return rows


def main():
    assert source_fixture() == json.loads(FIXTURE.read_text()), "Archer upgrade/source contract drift"
    print("PASS: original Archer levels 1–6, upgrade/reset/refund and 36 volley scenarios.")


if __name__ == "__main__":
    main()
