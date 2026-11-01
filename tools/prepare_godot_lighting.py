#!/usr/bin/env python3
"""Export lighting.py to the active Godot project with a pygame pixel oracle.

The runtime is pure GDScript/Image APIs. Python is used only here, with pygame's
GENERIC smoothscale backend pinned for reproducible integer resampling. --check
is an exact-byte, fail-closed gate; it never regenerates files in check mode.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "lighting.py"
CONTRACT = PROJECT / "data/lighting.json"
FIXTURE = PROJECT / "tests/fixtures/lighting_parity.json"
PYGAME_VERSION = "2.6.1"


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise AssertionError(f"Non-finite lighting value: {value!r}")
    return value


def _text(value: dict) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2,
                      allow_nan=False, sort_keys=True) + "\n"


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@contextlib.contextmanager
def source_module():
    """Import the real lighting module; no display, audio, assets or game UI."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    if pygame.version.ver != PYGAME_VERSION:
        raise AssertionError(f"Lighting oracle requires pygame=={PYGAME_VERSION}, got {pygame.version.ver}")
    previous_backend = pygame.transform.get_smoothscale_backend()
    pygame.transform.set_smoothscale_backend("GENERIC")
    previous = sys.modules.get("mystic_lighting_export")
    try:
        spec = importlib.util.spec_from_file_location("mystic_lighting_export", SOURCE)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Cannot load {SOURCE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module._CANON_CACHE.clear()
        module.reset_gradient_cache()
        yield module
    finally:
        module_caches = sys.modules.get("mystic_lighting_export")
        if module_caches is not None:
            module_caches._CANON_CACHE.clear()
            module_caches._SIZE_CACHE.clear()
        if previous is None:
            sys.modules.pop("mystic_lighting_export", None)
        else:
            sys.modules["mystic_lighting_export"] = previous
        pygame.transform.set_smoothscale_backend(previous_backend)


def build_contract(module) -> dict:
    import pygame
    n = int(module._GRAD_STEPS)
    if n < 2:
        raise AssertionError("Lighting gradient grid must contain at least two samples")
    for name in ("SHADE_MUL", "GRAD_DARK", "GRAD_LIGHT", "GRAD_SHEEN", "MASK_ALPHA"):
        value = int(getattr(module, name))
        if not 0 <= value <= 255:
            raise AssertionError(f"Lighting byte constant out of range: {name}={value}")
    if not 0.0 <= float(module.BAND2_RATIO) <= 1.0:
        raise AssertionError("BAND2_RATIO must be in [0, 1]")
    mul, add = module._canonical(module.GRAD_DARK, module.GRAD_LIGHT, module.GRAD_SHEEN)
    if mul.get_size() != (n, n) or add.get_size() != (n, n):
        raise AssertionError("Canonical lighting grid size mismatch")
    return _jsonable({
        "schema": 1,
        "source": "lighting.py",
        "source_sha256": _sha(SOURCE.read_bytes()),
        "light_dir": module.LIGHT_DIR,
        "rim_add": module.RIM_ADD,
        "shade_mul": module.SHADE_MUL,
        "band2_ratio": module.BAND2_RATIO,
        "mask_alpha": module.MASK_ALPHA,
        "gradient_enabled": module.GRADIENT_ENABLED,
        "grad_dark": module.GRAD_DARK,
        "grad_light": module.GRAD_LIGHT,
        "grad_sheen": module.GRAD_SHEEN,
        "grad_steps": n,
        "size_cache_limit": 65,
        "resampler": "pygame-smoothscale-generic-fixed-point",
        "canonical_mul_rgb": list(pygame.image.tobytes(mul, "RGB")),
        "canonical_add_rgb": list(pygame.image.tobytes(add, "RGB")),
    })


def _surface(pygame, kind: str, width: int, height: int):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    if kind == "square":
        pygame.draw.rect(surface, (180, 130, 80, 255), (6, 6, width - 12, height - 12))
        pygame.draw.rect(surface, (90, 170, 210, 171), (10, 10, 7, 9))
        pygame.draw.rect(surface, (0, 0, 0, 0), (16, 16, 5, 5))
    elif kind == "circle":
        pygame.draw.circle(surface, (100, 150, 200, 255), (width // 2, height // 2), min(width, height) // 3)
        pygame.draw.circle(surface, (220, 180, 90, 170), (width // 2, height // 2), min(width, height) // 5, 2)
    elif kind == "islands":
        pygame.draw.rect(surface, (210, 90, 70, 255), (3, 5, 9, 12))
        pygame.draw.rect(surface, (70, 200, 130, 255), (width - 15, height - 17, 11, 10))
        pygame.draw.rect(surface, (80, 90, 220, 171), (width // 2 - 3, height // 2 - 3, 7, 7))
    elif kind == "threshold":
        for x in range(width):
            alpha = 169 + x % 3
            for y in range(height):
                surface.set_at((x, y), (120, 160, 200, alpha))
    elif kind == "sparse":
        for index in range(23):
            surface.set_at((2 + index % 5, 2 + index // 5), (255, 200, 80, 255))
    elif kind == "translucent":
        pygame.draw.rect(surface, (200, 100, 20, 128), (4, 4, width - 8, height - 8))
        pygame.draw.rect(surface, (80, 180, 220, 255), (8, 8, width - 16, height - 16))
    elif kind == "transparent_rgb":
        surface.fill((40, 80, 120, 0))
        pygame.draw.rect(surface, (190, 140, 90, 255), (8, 8, width - 16, height - 16))
    elif kind == "tiny":
        surface.fill((200, 100, 50, 255))
    return surface


def _mask_row(mask) -> dict:
    if mask is None:
        return {"count": 0, "bits": ""}
    width, height = mask.get_size()
    bits = bytes(mask.get_at((x, y)) for y in range(height) for x in range(width))
    return {"count": mask.count(), "bits": _b64(bits)}


def build_oracle(module) -> dict:
    import pygame
    contour_cases = []
    for kind, size, alpha, width in [
        ("square", 32, 170, 1), ("square", 32, 170, 2), ("circle", 48, 170, 1),
        ("islands", 40, 170, 1), ("threshold", 30, 170, 1), ("sparse", 24, 170, 1),
        ("tiny", 2, 170, 1), ("square", 32, 170, 0),
    ]:
        surface = _surface(pygame, kind, size, size)
        rim, shade = module.contour_masks(surface, alpha=alpha, width=width)
        contour_cases.append({
            "name": f"{kind}_{size}_{alpha}_{width}", "kind": kind, "width": size, "height": size,
            "alpha": alpha, "band_width": width, "rim": _mask_row(rim), "shade": _mask_row(shade),
            "bbox": list(module._bbox_of(surface, alpha=alpha) or (0, 0, 0, 0)),
            "before_rgba": _b64(pygame.image.tobytes(surface, "RGBA")),
        })

    gradient_cases = []
    sizes = [(3, 3), (7, 11), (27, 28), (28, 28), (29, 31), (48, 64),
             (80, 80), (90, 120), (167, 164), (255, 129)]
    configs = [(205, 255, 22), (180, 255, 40), (205, 240, 0), (255, 205, 22)]
    for dark, light, sheen in configs:
        for width, height in sizes:
            mul, add = module._canonical(dark, light, sheen)
            mul = pygame.transform.smoothscale(mul, (width, height))
            add = pygame.transform.smoothscale(add, (width, height))
            gradient_cases.append({
                "width": width, "height": height, "dark": dark, "light": light, "sheen": sheen,
                "mul_rgb_sha256": _sha(pygame.image.tobytes(mul, "RGB")),
                "add_rgb_sha256": _sha(pygame.image.tobytes(add, "RGB")),
                "mul_first": list(mul.get_at((0, 0)))[:3],
                "mul_last": list(mul.get_at((width - 1, height - 1)))[:3],
                "add_first": list(add.get_at((0, 0)))[:3],
                "add_last": list(add.get_at((width - 1, height - 1)))[:3],
            })

    apply_cases = []
    scenarios = [
        ("square", 32, {}), ("circle", 48, {}), ("islands", 40, {}),
        ("threshold", 30, {}), ("sparse", 24, {}), ("tiny", 2, {}),
        ("translucent", 32, {}), ("transparent_rgb", 32, {}),
        ("square", 32, {"gradient": False}), ("square", 32, {"two_band": False}),
        ("square", 32, {"gradient": False, "two_band": False}),
        ("square", 40, {"rim_add": (48, 26, 22), "shade_mul": 158}),
        ("square", 40, {"rim_add": (34, 30, 48), "shade_mul": 162}),
        ("square", 40, {"rim_add": (-20, 300, 12), "shade_mul": 999}),
        ("square", 40, {"shade_mul": -10, "alpha": 180}),
        ("islands", 48, {"box": (4, 6, 30, 28)}),
        ("islands", 48, {"box": (4, 6, 999, 999)}),
        ("islands", 48, {"box": (-1, 0, 20, 20), "safe": True}),
        ("square", 32, {"enabled": False}),
    ]
    for index, (kind, size, options) in enumerate(scenarios):
        surface = _surface(pygame, kind, size, size)
        before = pygame.image.tobytes(surface, "RGBA")
        kwargs = {key: value for key, value in options.items() if key not in ("safe", "enabled")}
        if options.get("safe", False):
            module.apply_to_rig(surface, **kwargs)
        else:
            module.apply_to_rig(surface, enabled=options.get("enabled", True), **kwargs)
        after = pygame.image.tobytes(surface, "RGBA")
        rim, shade = module.contour_masks(surface, alpha=int(options.get("alpha", module.MASK_ALPHA)))
        apply_cases.append({
            "name": f"{index:02d}_{kind}", "kind": kind, "width": size, "height": size,
            "options": kwargs, "enabled": options.get("enabled", True),
            "before_rgba": _b64(before), "after_rgba": _b64(after),
            "bbox": list(module._bbox_of(surface) or (0, 0, 0, 0)),
            "rim_count": rim.count() if rim is not None else 0,
            "shade_count": shade.count() if shade is not None else 0,
            "changed": before != after,
        })
    return _jsonable({
        "schema": 1,
        "source_sha256": _sha(SOURCE.read_bytes()),
        "pygame_version": pygame.version.ver,
        "smoothscale_backend": pygame.transform.get_smoothscale_backend(),
        "contour_cases": contour_cases,
        "gradient_cases": gradient_cases,
        "apply_cases": apply_cases,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {}
    try:
        with source_module() as module:
            contract = build_contract(module)
            oracle = build_oracle(module)
        outputs = {CONTRACT: _text(contract), FIXTURE: _text(oracle)}
        if args.check:
            stale = [str(path.relative_to(ROOT)) for path, text in outputs.items()
                     if not path.is_file() or path.read_text(encoding="utf-8") != text]
            if stale:
                parser.exit(1, "Stale lighting data: %s; run tools/prepare_godot_lighting.py\n" % ", ".join(stale))
        else:
            for path, text in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_text(text, encoding="utf-8")
                temporary.replace(path)
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError, RuntimeError) as exc:
        parser.exit(1, f"Lighting preparation failed: {exc}\n")
    digest = _sha(outputs[CONTRACT].encode())[:12]
    print(f"{'Verified' if args.check else 'Prepared'} lighting: {len(oracle['apply_cases'])} pixel cases, "
          f"{len(oracle['gradient_cases'])} gradient cases; sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
