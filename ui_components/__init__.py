# ui_components/__init__.py
# Registry untuk semua UI components
# ================================
#
# Semua component pakai lazy import (try/except).
# Kalau ada error di 1 component, yang lain tetap jalan.
# ================================

# ═══ Import semua component (dengan safety) ═══

# ─── PENGGABUNGAN FILE ───
# Isi base_ui, build_popup, build_slots, hero_panel, hero_portraits, hero_shop, hover_indicators, notification, overlay, popup_renderer, shop_hints
# sekarang ada di ui_components/_bundle.py.
#
# Blok di bawah mendaftarkan nama submodul lama ke sys.modules,
# sehingga baris impor lama tetap jalan tanpa file fisiknya.
# Aman dipanggil berulang kali.
import sys as _sys
import types as _types

from ui_components import _bundle as _b

_EXTRA = {'hero_portraits': ['HeroPortraits', '_FakeEntity', '_make_fake_boss', '_make_fake_hero', 'math', 'pygame'], 'build_popup': ['BaseUIComponent', 'BuildPopup', 'pygame'], 'build_slots': ['BaseUIComponent', 'BuildSlots', 'math', 'pygame'], 'hero_panel': ['BaseUIComponent', 'HeroPanel', 'HeroPortraits', '_FakeEntity', '_make_fake_boss', '_make_fake_hero', 'math', 'pygame'], 'hero_shop': ['BaseUIComponent', 'HeroPortraits', 'HeroShop', 'pygame'], 'hover_indicators': ['BaseUIComponent', 'HoverIndicators', 'Notification', 'math', 'pygame'], 'notification': ['BaseUIComponent', 'Notification'], 'overlay': ['BaseUIComponent', 'Overlay', 'math', 'pygame'], 'popup_renderer': ['BaseUIComponent', 'PopupRenderer', 'pygame'], 'shop_hints': ['BaseUIComponent', 'ShopHints', 'math', 'pygame']}
_PLAIN_SYMS = {'base_ui': ['BaseUIComponent', 'math', 'pygame']}


def _install_aliases():
    for _name, _syms in _EXTRA.items():
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _ns = getattr(_b, "_NS_" + _name, None)
        if _ns is None:
            continue
        _m = _types.ModuleType(_full)
        _m.__doc__ = "ui_components/" + _name + ".py (digabung ke _bundle.py)"
        for _k in dir(_ns):
            if not _k.startswith("__"):
                setattr(_m, _k, getattr(_ns, _k))
        for _k in _syms:
            if not hasattr(_m, _k) and hasattr(_b, _k):
                setattr(_m, _k, getattr(_b, _k))
        _sys.modules[_full] = _m
        setattr(_sys.modules[__name__], _name, _m)

    for _name, _syms in _PLAIN_SYMS.items():
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _m = _types.ModuleType(_full)
        _m.__doc__ = "ui_components/" + _name + ".py (digabung ke _bundle.py)"
        for _k in _syms:
            if hasattr(_b, _k):
                setattr(_m, _k, getattr(_b, _k))
        _sys.modules[_full] = _m
        setattr(_sys.modules[__name__], _name, _m)


_install_aliases()

try:
    from ui_components.hover_indicators import HoverIndicators
except ImportError as e:
    print(f"[UI WARNING] HoverIndicators failed: {e}")
    HoverIndicators = None

try:
    from ui_components.build_slots import BuildSlots
except ImportError as e:
    print(f"[UI WARNING] BuildSlots failed: {e}")
    BuildSlots = None

try:
    from ui_components.shop_hints import ShopHints
except ImportError as e:
    print(f"[UI WARNING] ShopHints failed: {e}")
    ShopHints = None

try:
    from ui_components.build_popup import BuildPopup
except ImportError as e:
    print(f"[UI WARNING] BuildPopup failed: {e}")
    BuildPopup = None

try:
    from ui_components.popup_renderer import PopupRenderer
except ImportError as e:
    print(f"[UI WARNING] PopupRenderer failed: {e}")
    PopupRenderer = None

try:
    from ui_components.hero_panel import HeroPanel
except ImportError as e:
    print(f"[UI WARNING] HeroPanel failed: {e}")
    HeroPanel = None

try:
    from ui_components.hero_shop import HeroShop
except ImportError as e:
    print(f"[UI WARNING] HeroShop failed: {e}")
    HeroShop = None

try:
    from ui_components.overlay import Overlay
except ImportError as e:
    print(f"[UI WARNING] Overlay failed: {e}")
    Overlay = None

try:
    from ui_components.notification import Notification
except ImportError as e:
    print(f"[UI WARNING] Notification failed: {e}")
    Notification = None

# ═══ HeroPortraits (helper - dipakai HeroShop) ═══
try:
    from ui_components.hero_portraits import HeroPortraits
except ImportError as e:
    print(f"[UI WARNING] HeroPortraits failed: {e}")
    HeroPortraits = None


# ═══ Export list untuk cek availability ═══
__all__ = [
    'HoverIndicators',
    'BuildSlots',
    'ShopHints',
    'BuildPopup',
    'PopupRenderer',
    'HeroPanel',
    'HeroShop',
    'Overlay',
    'HeroPortraits',
]





# ================================
