# ================================
# minions/__init__.py
# Registry semua minions renderer
# ================================

# ─── PENGGABUNGAN FILE ───
# Isi goblin.py, orc.py, troll.py, undead.py, dark_rider.py, base_renderer.py sekarang ada di minions/_bundle.py.
# Tiap minion dibungkus namespace sendiri karena PALETTE, _aacircle,
# _get_palette dan puluhan helper lain namanya sama di kelima file
# tapi isinya BERBEDA.
#
# Blok di bawah mendaftarkan nama submodul lama ke sys.modules,
# sehingga baris impor lama tetap jalan tanpa file fisiknya:
#
#     from minions.goblin import draw_goblin
#     import minions.dark_rider
#
import sys as _sys
import types as _types

from minions import _bundle as _b


def _install_aliases():
    """Daftarkan minions.<modul> ke sys.modules dari isi _bundle."""
    for _name in ['goblin', 'orc', 'troll', 'undead', 'dark_rider']:
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _ns = getattr(_b, "_NS_" + _name)
        _mod = _types.ModuleType(_full)
        _mod.__doc__ = "minions/%s.py (digabung ke _bundle.py)" % _name
        for _k in dir(_ns):
            if not _k.startswith("__"):
                setattr(_mod, _k, getattr(_ns, _k))
        for _k in dir(_b):
            if not _k.startswith("_") and not hasattr(_mod, _k):
                setattr(_mod, _k, getattr(_b, _k))
        _sys.modules[_full] = _mod
        setattr(_sys.modules[__name__], _name, _mod)

    for _name in ['base_renderer']:
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _mod = _types.ModuleType(_full)
        _mod.__doc__ = "minions/%s.py (digabung ke _bundle.py)" % _name
        for _k in dir(_b):
            if not _k.startswith("__"):
                setattr(_mod, _k, getattr(_b, _k))
        _sys.modules[_full] = _mod
        setattr(_sys.modules[__name__], _name, _mod)


_install_aliases()

from minions.goblin import draw_goblin
from minions.orc import draw_orc
from minions.troll import draw_troll
from minions.undead import draw_undead
from minions.dark_rider import draw_dark_rider

# Registry: type -> draw function
MINION_RENDERERS = {
    "goblin": draw_goblin,
    "orc": draw_orc,
    "troll": draw_troll,
    "undead": draw_undead,
    "dark_rider": draw_dark_rider,
}


def render_minion(minion_type, surface, minion, x, y):
    """
    Central dispatcher untuk render minions body.

    Args:
        minion_type: str - "goblin", "orc", "troll", etc
        surface: pygame surface
        minion: Minion object (untuk akses attributes)
        x, y: posisi center di screen
    """
    renderer = MINION_RENDERERS.get(minion_type)
    if renderer:
        # ── Cache sprite (opsional, lihat mobile/spritecache.py) ──
        try:
            from mobile.spritecache import render_minion_cached
            if render_minion_cached(minion_type, renderer, surface,
                                    minion, x, y):
                return
        except Exception:
            pass
        renderer(surface, minion, x, y)
    else:
        print(f"[WARNING] Unknown minions type: {minion_type}")