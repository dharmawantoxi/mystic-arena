# ================================
# towers/__init__.py
# Registrasi semua tower renderer
# ================================
#
# CATATAN PENGGABUNGAN FILE
# Isi archer_tower.py, cannon_tower.py, ice_tower.py, mage_tower.py
# dan base_renderer.py sekarang ada di towers/_bundle.py.
#
# Blok _install_aliases() di bawah mendaftarkan nama submodul lama ke
# sys.modules, sehingga baris impor lama tetap jalan tanpa perlu file
# fisiknya:
#
#     from towers.archer_tower import draw_archer, get_archer_top_y
#     import towers.mage_tower
#
# Tiap tower dibungkus namespace sendiri di _bundle.py karena
# LEVEL_CONFIGS dan puluhan helper (_draw_main_tower, _render_effects,
# _draw_shield, ...) namanya sama persis di keempat file tapi ISINYA
# BERBEDA. Digabung mentah, yang terakhir akan menimpa semuanya.

import sys as _sys
import types as _types

from towers import _bundle as _b


def _install_aliases():
    """Daftarkan towers.<modul> ke sys.modules dari isi _bundle."""
    _wrapped = ['archer_tower', 'cannon_tower', 'ice_tower', 'mage_tower']
    _plain = ['base_renderer']

    for _name in _wrapped:
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _ns = getattr(_b, "_NS_" + _name)
        _mod = _types.ModuleType(_full)
        _mod.__doc__ = "towers/%s.py (digabung ke _bundle.py)" % _name
        for _k in dir(_ns):
            if not _k.startswith("__"):
                setattr(_mod, _k, getattr(_ns, _k))
        # simbol dari import asli modul ini (mis. dipakai lewat modul)
        for _k in dir(_b):
            if not _k.startswith("_") and not hasattr(_mod, _k):
                setattr(_mod, _k, getattr(_b, _k))
        _sys.modules[_full] = _mod
        setattr(_sys.modules[__name__], _name, _mod)

    for _name in _plain:
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _mod = _types.ModuleType(_full)
        _mod.__doc__ = "towers/%s.py (digabung ke _bundle.py)" % _name
        for _k in dir(_b):
            if not _k.startswith("__"):
                setattr(_mod, _k, getattr(_b, _k))
        _sys.modules[_full] = _mod
        setattr(_sys.modules[__name__], _name, _mod)


_install_aliases()

from towers.archer_tower import draw_archer
from towers.cannon_tower import draw_cannon
from towers.ice_tower import draw_ice
from towers.mage_tower import draw_mage

# Registry: type -> draw function
TOWER_RENDERERS = {
    "archer": draw_archer,
    "cannon": draw_cannon,
    "ice": draw_ice,
    "mage": draw_mage,
}


def render_tower(tower_type, surface, tower, x, y, size):
    """
    Central dispatcher untuk render tower body.

    Args:
        tower_type: str - "archer", "cannon", "ice", "mage"
        surface: pygame surface
        tower: Tower object (untuk akses self.team, self.level, dll)
        x, y: posisi center
        size: base size
    """
    renderer = TOWER_RENDERERS.get(tower_type)
    if renderer:
        renderer(surface, tower, x, y, size)
    else:
        print(f"[WARNING] Unknown tower type: {tower_type}")
