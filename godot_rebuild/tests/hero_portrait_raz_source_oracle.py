"""Source oracle for the final roster portrait (slice 9c215), Raz — The Heat of Despair.

The 9c64-9c214 art batch deliberately left Raz on the generic fallback. The user has now requested
all remaining migration work, so this slice promotes that last roster entry to a source-informed
native portrait. The oracle harvests Raz's Fire Monk role/name from `bosses/boss_data.py` and the
skin, hair, cloth, sash and fire palette from `_NS_raz.PALETTE` in `bosses/level10.py`. It does not
claim pixel parity with the animated boss renderer.

Run: python godot_rebuild/tests/hero_portrait_raz_source_oracle.py
"""
import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVEL10 = ROOT / "bosses" / "level10.py"
BOSS_DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hero_portrait_raz_source.json"
PALETTE_KEYS = (
    "skin_mid", "hair_mid", "cloth_darkest", "cloth_dark", "red_darkest", "red_mid",
    "fire_mid", "fire_hot", "gold_mid",
)


def _raz_palette():
    tree = ast.parse(LEVEL10.read_text(encoding="utf-8"))
    namespace = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "_NS_raz"
    )
    assignment = next(
        node for node in namespace.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "PALETTE" for target in node.targets)
    )
    return ast.literal_eval(assignment.value)


def _raz_hero_data():
    spec = importlib.util.spec_from_file_location("boss_data", BOSS_DATA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    boss = module.get_all_boss_types()["raz"]
    return boss["hero_unlock"]


def source_fixture():
    hero = _raz_hero_data()
    palette = _raz_palette()
    return {
        "hero_type": "raz",
        "name": hero["name"],
        "title": hero["title"],
        "role": hero["role"],
        "palette": {key: list(palette[key]) for key in PALETTE_KEYS},
    }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
