"""Uji regresi: penanda build slot harus tergambar di peta.

Bug yang pernah terjadi: saat file-file UI digabung ke
`ui_components/_bundle.py`, kelas `BuildSlots` ikut menempel di dalam
namespace `_NS_build_popup` sehingga namespace `_NS_build_slots` tidak
pernah terbentuk. Akibatnya `ui_components/__init__.py` gagal mengimpor
`ui_components.build_slots`, `BuildSlots = None`, dan
`UIRenderer.draw_build_slots()` tidak menggambar apa-apa - penanda (+)
build tower hilang total dari map tanpa error mencolok (hanya baris
"[UI WARNING] BuildSlots failed" di log).

Test ini memastikan:
  1. `ui_components.build_slots` bisa diimpor dan BuildSlots bukan None;
  2. `UIRenderer.build_slots_component` terpasang (bukan None);
  3. Setelah `Game.draw()`, piksel di tiap slot kosong benar-benar
     berubah dibanding gambar peta saja (marker benar-benar terblit).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()

import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
import ui_components  # noqa: E402


def test_import_build_slots():
    # Regresi inti: dulu import ini gagal dengan
    # "No module named 'ui_components.build_slots'".
    from ui_components.build_slots import BuildSlots  # noqa: F401
    assert ui_components.BuildSlots is not None


def test_component_terpasang():
    screen = pygame.display.set_mode(
        (_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT))
    g = Game(screen, level_number=1)
    assert g.ui.build_slots_component is not None, \
        "build_slots_component None -> penanda tidak akan digambar"
    assert g.build_slots_blue and g.build_slots_red, \
        "daftar slot kosong -> tidak ada yang bisa digambar"
    return g, screen


def test_marker_tergambar(g, screen):
    for nm in ("level_intro", "boss_intro"):
        o = getattr(g, nm, None)
        if o is not None and hasattr(o, "handle_skip"):
            try:
                o.handle_skip(key=pygame.K_SPACE)
            except Exception:
                pass
    for _ in range(3):
        g.update()

    # Render penuh (peta + UI) vs peta saja.
    g.draw()
    full = screen.copy()

    peta = pygame.Surface(screen.get_size())
    g.map_renderer.draw(peta, g.animation_time)

    def berbeda(surface_a, surface_b, x, y):
        # Cek beberapa piksel di sekitar pusat slot; marker berisi
        # lingkaran batu + ikon plus sehingga pasti ada selisih.
        for dx, dy in ((0, 0), (0, 3), (-4, 0), (4, 0)):
            if surface_a.get_at((x + dx, y + dy))[:3] != \
                    surface_b.get_at((x + dx, y + dy))[:3]:
                return True
        return False

    for slot in g.build_slots_blue:
        x, y = int(slot["x"]), int(slot["y"])
        assert berbeda(full, peta, x, y), \
            f"marker slot biru ({x},{y}) tidak tergambar"
    for slot in g.build_slots_red:
        x, y = int(slot["x"]), int(slot["y"])
        assert berbeda(full, peta, x, y), \
            f"marker slot merah ({x},{y}) tidak tergambar"


def main():
    test_import_build_slots()
    g, screen = test_component_terpasang()
    test_marker_tergambar(g, screen)
    print("HASIL: LULUS. Penanda build slot tergambar di semua slot.")


if __name__ == "__main__":
    main()
