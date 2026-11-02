#!/usr/bin/env python3
"""Prepare the native main.py port: metadata + assets, without pygame/ffmpeg.

Run from any directory: python3 tools/prepare_godot_main.py
Use --check in CI to verify tracked fonts/images and generated level metadata.
Audio copies are ignored by Git and are optional at runtime.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
FIELDS = ("level_number", "name", "description", "map_theme", "bgm_track", "unlock_after_level")
IMAGES = ("logo.png", "icon.png")
# Optional splash logo variants, in splash_screen.LOGO_PATHS order.
SPLASH_LOGO_VARIANTS = ("splash_logo.png", "logo.jpg", "logo.jpeg")


def level_catalog() -> list[dict]:
    tree = ast.parse((ROOT / "levels/level_data.py").read_text(encoding="utf-8"))
    levels = {}
    order = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id.startswith("LEVEL_") and target.id[6:].isdigit():
                row = ast.literal_eval(node.value)
                levels[target.id] = {key: row.get(key) for key in FIELDS}
            elif target.id == "ALL_LEVELS" and isinstance(node.value, ast.List):
                order = [element.id for element in node.value.elts if isinstance(element, ast.Name)]
    if not order:
        order = sorted(levels, key=lambda name: int(name[6:]))
    result = [levels[name] for name in order]
    numbers = [row["level_number"] for row in result]
    if not result or len(numbers) != len(set(numbers)) or any(not isinstance(n, int) for n in numbers):
        raise ValueError("Level catalog must be nonempty with unique integer IDs")
    if any(not row.get("name") for row in result):
        raise ValueError("Every level needs a name")
    return result


def audio_extension(path: Path) -> str:
    header = path.read_bytes()[:4096]
    if header.startswith(b"OggS"):
        return "ogg"
    if header.startswith(b"ID3") or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return "wav"
    raise ValueError(f"Unsupported audio container: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Require existing exact copies; write nothing")
    args = parser.parse_args()
    jobs: list[tuple[Path, Path]] = []
    for font in sorted((ROOT / "assets/fonts").glob("*.ttf")):
        jobs.append((font, PROJECT / "assets/fonts" / font.name))
    for name in IMAGES:
        jobs.append((ROOT / "assets" / name, PROJECT / "assets" / name))
    for name in SPLASH_LOGO_VARIANTS:
        source = ROOT / "assets" / name
        if source.is_file():
            jobs.append((source, PROJECT / "assets" / name))
    for sound in sorted((ROOT / "assets/sounds").glob("*.wav")):
        jobs.append((sound, PROJECT / "assets/sounds" / f"{sound.stem}.{audio_extension(sound)}"))
    license_file = ROOT / "assets/sounds/LISENSI_DAN_SUMBER.txt"
    if license_file.exists():
        jobs.append((license_file, PROJECT / "assets/sounds" / license_file.name))
    catalog = json.dumps(level_catalog(), ensure_ascii=False, indent=2) + "\n"
    stale = []
    for source, destination in jobs:
        if args.check:
            if not destination.exists() or hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(destination.read_bytes()).digest():
                stale.append(str(destination.relative_to(ROOT)))
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    target = PROJECT / "data/levels.json"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != catalog:
            stale.append(str(target.relative_to(ROOT)))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(catalog, encoding="utf-8")
    if stale:
        parser.exit(1, "Stale/missing copies. Run tools/prepare_godot_main.py:\n" + "\n".join(stale) + "\n")
    print(f"{'Verified' if args.check else 'Prepared'} {len(level_catalog())} levels, {len(jobs)} asset files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
