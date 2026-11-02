#!/usr/bin/env python3
"""Source-side smoke tests for lighting.py and the active Godot port.

The exact pixel-parity gate lives in tools/prepare_godot_lighting.py and
godot_rebuild/tests/LightingParityTest.gd. This script only checks the Python
oracle and that the native files exist under godot_rebuild/.
"""

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NATIVE_FILES = [
    ROOT / "godot_rebuild" / "scripts" / "render" / "Lighting.gd",
    ROOT / "godot_rebuild" / "scripts" / "render" / "LightingResampler.gd",
    ROOT / "godot_rebuild" / "data" / "lighting.json",
    ROOT / "godot_rebuild" / "tests" / "LightingParityTest.gd",
    ROOT / "godot_rebuild" / "tests" / "fixtures" / "lighting_parity.json",
]


def test_native_files():
    for path in NATIVE_FILES:
        assert path.is_file(), f"Missing native lighting file: {path}"
    print("✓ File Lighting.gd / resampler / kontrak / fixture ada")


try:
    import pygame
except ImportError:
    pygame = None

if pygame is not None:
    import lighting as lighting_py

    def test_constants():
        assert lighting_py.LIGHT_DIR == (-1, -1)
        assert lighting_py.RIM_ADD == (30, 26, 44)
        assert lighting_py.SHADE_MUL == 168
        assert abs(lighting_py.BAND2_RATIO - 0.42) < 0.001
        assert lighting_py.MASK_ALPHA == 170
        assert lighting_py.GRAD_DARK == 205
        assert lighting_py.GRAD_LIGHT == 255
        assert lighting_py.GRAD_SHEEN == 22
        assert lighting_py._GRAD_STEPS == 28
        print("✓ Konstanta lighting.py OK")

    def test_gradient_canonical():
        mul, add = lighting_py._canonical(lighting_py.GRAD_DARK, lighting_py.GRAD_LIGHT, lighting_py.GRAD_SHEEN)
        assert mul.get_size() == (28, 28)
        assert mul.get_at((0, 0)).r > mul.get_at((27, 27)).r
        assert add.get_at((0, 0)).r >= add.get_at((27, 27)).r
        print("✓ Gradient kanonik 28x28 OK")

    def test_contour_masks():
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, (255, 0, 0, 255), pygame.Rect(6, 6, 20, 20))
        rim, shade = lighting_py.contour_masks(surf)
        assert rim is not None and shade is not None
        assert 0 < rim.count() < 100 and shade.count() > 0
        print("✓ Contour masks OK")

    def test_bbox():
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, (255, 0, 0, 255), pygame.Rect(5, 10, 10, 5))
        assert lighting_py._bbox_of(surf) == (5, 10, 10, 5)
        print("✓ BBox OK")

    def test_apply():
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        pygame.draw.circle(surf, (100, 150, 200, 255), (32, 32), 20)
        lighting_py.apply(surf)
        print("✓ Apply tidak crash")

    if __name__ == "__main__":
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        pygame.init()
        test_constants()
        test_gradient_canonical()
        test_contour_masks()
        test_bbox()
        test_apply()
        test_native_files()
        print("\n=== TES SUMBER LIGHTING LULUS ===")
        print("Paritas pixel exact: python3 tools/prepare_godot_lighting.py --check")
        print("Native suite: godot_rebuild/tests/LightingParityTest.gd via run_all.gd")
else:
    print("pygame tidak tersedia; hanya cek file native Godot")
    test_native_files()
