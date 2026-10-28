"""Source oracle for the UI font style map (layer 9bv17).

`_render.py` bundles five TTFs and resolves `get_font(size, style)` through
`_STYLE_FONT_MAP` / `_font_path(style)`. Earlier migration slices repeatedly
recorded that Godot drew every text op with Barlow-SemiBold because only
Regular / SemiBold / Cinzel had been copied into `godot_rebuild/assets/fonts`.
This oracle harvests the maps with `ast`, hashes every source TTF, and proves
each Godot copy is byte-identical to the source asset.

Run: python godot_rebuild/tests/source_fonts_source_oracle.py
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "_render.py"
SOURCE_FONTS = ROOT / "assets" / "fonts"
GODOT_FONTS = ROOT / "godot_rebuild" / "assets" / "fonts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "source_fonts_source.json"


def _assignments(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = node.value
    return out


def _font_path_default(tree):
    """The fallback literal in `_font_path`'s `_STYLE_FONT_MAP.get(style, X)`."""
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_font_path":
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue
            if call.func.attr != "get" or len(call.args) != 2:
                continue
            if not isinstance(call.args[1], ast.Constant):
                continue
            return call.args[1].value
    raise AssertionError("_font_path fallback literal not found")


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fixture():
    tree = ast.parse(RENDER.read_text(encoding="utf-8"))
    assigns = _assignments(tree)
    body_files = ast.literal_eval(assigns["_BODY_FONT_FILES"])
    style_files = ast.literal_eval(assigns["_STYLE_FONT_MAP"])
    title_file = ast.literal_eval(assigns["_TITLE_FONT_FILE"])
    default_file = _font_path_default(tree)

    assert style_files["title"] == title_file
    assert default_file == body_files["body"]
    assert set(style_files.values()) == set(body_files.values()) | {title_file}

    names = sorted(set(style_files.values()) | {default_file})
    source_hashes = {name: _sha256(SOURCE_FONTS / name) for name in names}
    godot_hashes = {name: _sha256(GODOT_FONTS / name) for name in names}
    assert source_hashes == godot_hashes, "a Godot font copy drifted from the source"

    return {
        "body_font_files": dict(sorted(body_files.items())),
        "style_font_map": dict(sorted(style_files.items())),
        "title_font_file": title_file,
        "font_path_default": default_file,
        "source_font_sha256": source_hashes,
        "godot_font_sha256": godot_hashes,
        "copies_match": True,
    }


if __name__ == "__main__":
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    data = source_fixture()
    FIXTURE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE.relative_to(ROOT)}: {len(data['style_font_map'])} styles, "
          f"{len(data['godot_font_sha256'])} TTF copies")
