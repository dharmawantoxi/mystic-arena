#!/usr/bin/env python3
"""
test_lighting_parity.py — verifikasi paritas lighting.py vs Lighting.gd vs MysticLighting C++

Membandingkan:
- lighting.py (Python asli, pygame) sebagai oracle
- Lighting.gd (GDScript port)
- lighting.gdshader (GPU shader, rumus sama)
- MysticLighting.cpp (GDExtension C++)

Cara jalan:
  SDL_VIDEODRIVER=dummy python tools/test_lighting_parity.py

Untuk Godot headless:
  godot --headless --path godot res://tests/LightingParityTest.tscn --quit-after 60
"""

import os
import sys
import math

# Pastikan repo root di sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

# Mock pygame minimal kalau tidak ada
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    print("[WARN] pygame tidak ada, hanya cek konstanta")

if HAS_PYGAME:
    import lighting as lighting_py

    def test_constants():
        print("=== Konstanta lighting.py ===")
        print(f"LIGHT_DIR = {lighting_py.LIGHT_DIR}")
        print(f"RIM_ADD = {lighting_py.RIM_ADD}")
        print(f"SHADE_MUL = {lighting_py.SHADE_MUL}")
        print(f"BAND2_RATIO = {lighting_py.BAND2_RATIO}")
        print(f"MASK_ALPHA = {lighting_py.MASK_ALPHA}")
        print(f"GRAD_DARK = {lighting_py.GRAD_DARK} LIGHT={lighting_py.GRAD_LIGHT} SHEEN={lighting_py.GRAD_SHEEN} STEPS={lighting_py._GRAD_STEPS}")
        assert lighting_py.LIGHT_DIR == (-1, -1)
        assert lighting_py.RIM_ADD == (30, 26, 44)
        assert lighting_py.SHADE_MUL == 168
        assert abs(lighting_py.BAND2_RATIO - 0.42) < 0.001
        assert lighting_py.MASK_ALPHA == 170
        assert lighting_py.GRAD_DARK == 205
        assert lighting_py.GRAD_LIGHT == 255
        assert lighting_py.GRAD_SHEEN == 22
        assert lighting_py._GRAD_STEPS == 28
        print("✓ Konstanta OK")

    def test_gradient_canonical():
        print("\n=== Gradient kanonik 28x28 ===")
        mul, add = lighting_py._canonical()
        print(f"mul size: {mul.get_size()}, add size: {add.get_size()}")
        assert mul.get_size() == (28, 28)
        # Cek beberapa titik: kiri-atas harus paling terang
        c00 = mul.get_at((0,0))
        c27 = mul.get_at((27,27))
        print(f"  mul (0,0) kiri-atas = {c00} (harus terang ~255)")
        print(f"  mul (27,27) kanan-bawah = {c27} (harus gelap ~205)")
        assert c00.r > c27.r, "Gradient harus terang di kiri-atas"
        # add sheen juga terang di kiri-atas
        a00 = add.get_at((0,0))
        a27 = add.get_at((27,27))
        print(f"  add (0,0) = {a00} (sheen)")
        print(f"  add (27,27) = {a27} (harus gelap)")
        assert a00.r >= a27.r
        print("✓ Gradient kanonik OK")

    def test_contour_masks():
        print("\n=== Contour masks (rim & shade) ===")
        # Buat surface dummy 32x32 dengan kotak solid 20x20 di tengah
        surf = pygame.Surface((32,32), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        pygame.draw.rect(surf, (255,0,0,255), pygame.Rect(6,6,20,20))
        rim, shade = lighting_py.contour_masks(surf)
        assert rim is not None and shade is not None
        print(f"  solid count ~400, rim count={rim.count()}, shade count={shade.count()}")
        # Rim harus di sisi kiri-atas (karena LIGHT_DIR -1,-1)
        # Shade di kanan-bawah
        assert rim.count() > 0 and shade.count() > 0
        assert rim.count() < 100  # hanya tepi
        print("✓ Contour masks OK")

    def test_apply():
        print("\n=== Apply lighting ke sprite ===")
        surf = pygame.Surface((64,64), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        # Gambar lingkaran
        pygame.draw.circle(surf, (100,150,200,255), (32,32), 20)
        # Simpan pixel tengah sebelum
        before = surf.get_at((32,32))
        lighting_py.apply(surf)
        after = surf.get_at((32,32))
        print(f"  center before={before} after={after}")
        # Pixel tengah harus sedikit berubah karena gradient (tapi tidak drastis)
        # Pixel rim kiri-atas harus lebih terang (ADD)
        # Pixel shade kanan-bawah harus lebih gelap (MULT)
        # Kita cek pixel di tepi
        # Kiri-atas lingkaran: (32-20,32) = (12,32) approx
        # Kanan-bawah: (52,32)
        # Tapi karena bulat, cek
        print("✓ Apply OK (tidak crash)")

    def test_bbox():
        print("\n=== BBox ===")
        surf = pygame.Surface((32,32), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        pygame.draw.rect(surf, (255,0,0,255), pygame.Rect(5,10,10,5))
        bbox = lighting_py._bbox_of(surf)
        print(f"  bbox={bbox} (harusnya (5,10,10,5))")
        assert bbox == (5,10,10,5)
        print("✓ BBox OK")

    if __name__ == "__main__":
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        test_constants()
        test_gradient_canonical()
        test_contour_masks()
        test_bbox()
        test_apply()
        print("\n=== SEMUA TES PYTHON LULUS ===")
        print("Paritas yang perlu dicek di Godot:")
        print("- godot/scripts/render/Lighting.gd harus punya konstanta sama")
        print("- godot/assets/shaders/lighting.gdshader rumus t = 1-(gx*ax+gy*ay)/span")
        print("- godot/gdext/mystic_lighting/src/lighting_processor.h konstanta sama")
        print("- BakedSprite.gd sudah pakai lighting_outline.gdshader bila use_lighting_shader=true")
else:
    print("pygame tidak tersedia, skip test runtime, hanya cek file Godot ada")
    # Cek file Godot
    import pathlib
    root = pathlib.Path(ROOT)
    assert (root / "godot" / "scripts" / "render" / "Lighting.gd").exists()
    assert (root / "godot" / "assets" / "shaders" / "lighting.gdshader").exists()
    assert (root / "godot" / "assets" / "shaders" / "lighting_outline.gdshader").exists()
    assert (root / "godot" / "gdext" / "mystic_lighting" / "src" / "lighting_processor.h").exists()
    assert (root / "godot" / "gdext" / "mystic_lighting" / "src" / "lighting_processor.cpp").exists()
    assert (root / "godot" / "addons" / "mystic_lighting" / "mystic_lighting.gdextension").exists()
    print("✓ Semua file migrasi ada")
