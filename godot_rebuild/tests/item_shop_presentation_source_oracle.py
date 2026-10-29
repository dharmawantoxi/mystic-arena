"""Source-derived presentation data for the pygame ITEM FORGE.

The data comes from hero_items.py via its AST source oracle, so the Godot UI
can display the same labels, copy, colours, restrictions and icon filenames
without importing pygame at runtime.
"""
from pathlib import Path
import json
import shutil

from ai_item_source_oracle import source_namespace

ROOT = Path(__file__).resolve().parents[2]
GODOT = ROOT / "godot_rebuild"
PRESENTATION = GODOT / "data/ui/item_shop_presentation.json"
ICON_DIR = GODOT / "assets/art/items"


def presentation_data():
    env = source_namespace(with_forge=True)
    classes = {
        class_id: {"label": label, "color": list(color)}
        for class_id, (label, color) in env["ITEM_CLASS_INFO"].items()
    }
    items = {}
    for item_id, source in env["ITEM_CATALOG"].items():
        class_id = env["get_item_class"](item_id)
        category = source["category"]
        category_label, category_color = env["CATEGORY_INFO"][category]
        item = dict(source)
        item.update({
            "class": class_id,
            "class_label": env["ITEM_CLASS_INFO"][class_id][0],
            "class_color": list(env["ITEM_CLASS_INFO"][class_id][1]),
            "category_label": category_label,
            "category_color": list(category_color),
        })
        items[item_id] = item
    return json.loads(json.dumps({"classes": classes, "items": items}))


def write_presentation():
    """Regenerate the data and source item textures copied into res://."""
    expected = presentation_data()
    PRESENTATION.parent.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    PRESENTATION.write_text(
        json.dumps(expected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for item in expected["items"].values():
        source_icon = ROOT / "assets/items" / item["icon"]
        if not source_icon.is_file():
            raise FileNotFoundError(source_icon)
        shutil.copyfile(source_icon, ICON_DIR / item["icon"])
    return expected


if __name__ == "__main__":
    write_presentation()
