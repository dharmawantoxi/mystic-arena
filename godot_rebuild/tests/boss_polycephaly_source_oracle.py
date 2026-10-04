"""9a: execute source Polycephaly; contrast its native pre-9a epsilon sort.

Proof: hero_items.py:2629 sorts exact distances; native
hero_item_inventory.gd:997 formerly treated gaps <= .001 as ties.
With units at 10, 20.0005 and boss last at 20, the second slot was wrong.
Python gameplay files are read-only. Four layouts per all 216 boss types.
"""
import ast
import json
from functools import cmp_to_key
from pathlib import Path
from boss_item_cleave_chain_source_oracle import (
    _build_runtime, _prepare_boss, _DummyOwner, _DummyUnit, _method_node, _func_node,
    SOURCE_STATS,
)

FIXTURE = Path(__file__).parent / 'fixtures/boss_polycephaly_source.json'
LAYOUTS = {
    'nearer_boss_takes_last_slot': [10.0, 20.0005, 20.0],
    'exact_tie_keeps_unit_slot': [10.0, 20.0, 20.0],
    'boss_first_despite_insertion': [20.0005, 30.0, 20.0],
    'farther_boss_stays_out': [10.0, 20.0, 20.0005],
}


def source_fixture():
    catalog, inv_cls, boss_cls = _build_runtime()
    original = inv_cls._on_hit_common
    original.__globals__["_MIASMA"] = {}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[_func_node("_apply_miasma", "hero_items.py")], type_ignores=[])),
        "<source-miasma>", "exec"), original.__globals__)
    node = _method_node('HeroItemInventory', '_on_hit_common', 'hero_items.py')
    text = ast.unparse(node)
    shape = 'extras.sort(key=lambda x: x[0])' in text
    # Only replace the sorting key for the counterfactual; same real on-hit arm.
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) \
                and isinstance(child.func.value, ast.Name) \
                and child.func.value.id == 'extras' and child.func.attr == 'sort':
            child.keywords[0].value = ast.Name(id='legacy_key', ctx=ast.Load())
    env = dict(original.__globals__)
    env['legacy_key'] = cmp_to_key(lambda a, b: 0 if abs(a[0] - b[0]) <= .001
                                 else (-1 if a[0] < b[0] else 1))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 '<pre-9a-sort>', 'exec'), env)
    cases = []
    for boss_type in sorted(SOURCE_STATS):
        for scenario, offsets in LAYOUTS.items():
            row = {'boss_type': boss_type, 'scenario': scenario, 'offsets': offsets}
            for key, method in [('expected', original),
                                ('expected_without_exact_sort', env['_on_hit_common'])]:
                boss = _prepare_boss(boss_cls, boss_type, offsets[2])
                target = _DummyUnit(10, 1, 0)
                owner = _DummyOwner(target)
                owner.is_melee_hero = False
                owner.range = 200
                units = [_DummyUnit(11, 1, offsets[0]), _DummyUnit(12, 1, offsets[1]), boss]
                hits = []
                for role, unit in zip(['unit_a', 'unit_b', 'boss'], units):
                    unit.take_damage = lambda damage, team, school, role=role: hits.append(
                        [role, int(damage), school])
                inv = inv_cls(owner)
                assert inv.add('basilisk_breath')
                inv_cls._on_hit_common = method
                inv.on_basic_attack_hit(target, 50, [target] + units)
                row[key] = hits
            cases.append(row)
    inv_cls._on_hit_common = original
    return {'source': {'exact_distance_sort': shape,
                       'multishot': catalog['basilisk_breath']['multishot']},
            'cases': cases}


if __name__ == '__main__':
    import sys
    fixture = source_fixture()
    assert len(fixture['cases']) == 864
    assert fixture['source']['exact_distance_sort']
    for row in fixture['cases']:
        differs = row['expected'] != row['expected_without_exact_sort']
        assert differs == (row['scenario'] in ('nearer_boss_takes_last_slot',
                                               'boss_first_despite_insertion'))
    if '--write' in sys.argv:
        FIXTURE.write_text(json.dumps(fixture, indent=2) + '\n')
    print('PASS: 864 Polycephaly source cases')
