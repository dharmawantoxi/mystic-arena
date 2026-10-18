"""Headless pygame boot shared by the art bake scripts.

The bake scripts run the ORIGINAL pygame art code (read-only) and write PNG
atlases plus JSON manifests under ``godot_rebuild/``. Nothing here writes into
the Python source tree: the game's save directory is redirected to a scratch
folder before any game module is imported.

Run with an interpreter that has ``pygame``, ``numpy`` and ``Pillow``:
    python godot_rebuild/bake/bake_map_overlay.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GODOT = REPO / "godot_rebuild"
ART_DIR = GODOT / "assets" / "art"
DATA_DIR = GODOT / "data" / "art"
SCREEN = (1280, 720)


def boot():
    """Return ``(pygame, _core, screen)`` with the real game modules loaded."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("MYSTIC_FORCE_TOUCH", "0")
    sys.path.insert(0, str(REPO))
    os.chdir(REPO)
    import storage_paths

    storage_paths._PROJECT_ROOT = tempfile.mkdtemp(prefix="mystic_bake_saves_")
    import pygame
    import _core

    pygame.init()
    screen = pygame.display.set_mode(SCREEN)
    return pygame, _core, screen


def write_png(path: Path, rgba) -> dict:
    """Write an HxWx4 uint8 array deterministically; return its manifest entry."""
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.fromarray(rgba, "RGBA")
    image.save(path, format="PNG", optimize=True, compress_level=9)
    data = path.read_bytes()
    return {
        "size": [image.width, image.height],
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _dump(value, indent: int = 0) -> str:
    """JSON with one dict entry per line and every list kept on a single line."""
    if isinstance(value, dict) and value:
        pad = " " * (indent + 1)
        rows = [
            f"{pad}{json.dumps(key)}: {_dump(item, indent + 1)}"
            for key, item in sorted(value.items())
        ]
        return "{\n" + ",\n".join(rows) + "\n" + " " * indent + "}"
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def write_manifest(name: str, payload: dict) -> Path:
    import pygame

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"pygame": pygame.version.ver, **payload}
    target = DATA_DIR / f"{name}.json"
    target.write_text(_dump(payload) + "\n", encoding="utf-8")
    return target
