# ================================
# hero_skills/__init__.py
# Registry semua skill handlers + auto-register boss heroes
# ================================

# ─── PENGGABUNGAN FILE ───
# Isi base_skill, boss_hero_skills, grimjaw_skills, kaizen_skills, sylara_skills, thorne_skills, vex_skills, zephyr_skills
# sekarang ada di hero_skills/_bundle.py.
#
# Blok di bawah mendaftarkan nama submodul lama ke sys.modules,
# sehingga baris impor lama tetap jalan tanpa file fisiknya.
# Aman dipanggil berulang kali.
import sys as _sys
import types as _types

from hero_skills import _bundle as _b

_EXTRA = {'boss_hero_skills': ['BaseSkill', 'BossHeroSkills', 'math'], 'grimjaw_skills': ['BaseSkill', 'GrimjawSkills', 'math'], 'kaizen_skills': ['BaseSkill', 'KaizenSkills', 'math'], 'sylara_skills': ['BaseSkill', 'HERO_TYPES', 'SylaraSkills', 'math'], 'thorne_skills': ['BaseSkill', 'ThorneSkills', 'math'], 'vex_skills': ['BaseSkill', 'VexSkills', 'math'], 'zephyr_skills': ['BaseSkill', 'ZephyrSkills', 'math']}
_PLAIN_SYMS = {'base_skill': ['BaseSkill', 'SoundManager', 'math']}


def _install_aliases():
    for _name, _syms in _EXTRA.items():
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _ns = getattr(_b, "_NS_" + _name, None)
        if _ns is None:
            continue
        _m = _types.ModuleType(_full)
        _m.__doc__ = "hero_skills/" + _name + ".py (digabung ke _bundle.py)"
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
        _m.__doc__ = "hero_skills/" + _name + ".py (digabung ke _bundle.py)"
        for _k in _syms:
            if hasattr(_b, _k):
                setattr(_m, _k, getattr(_b, _k))
        _sys.modules[_full] = _m
        setattr(_sys.modules[__name__], _name, _m)


_install_aliases()

SKILL_HANDLERS = {}


def register_handler(hero_type, handler_class):
    """Register skill handler untuk hero type"""
    SKILL_HANDLERS[hero_type] = handler_class


def get_skill_handler(hero_type, hero):
    """
    Get skill handler untuk hero type tertentu.
    Return None kalau hero type tidak ada handler.
    """
    handler_class = SKILL_HANDLERS.get(hero_type)
    if handler_class:
        return handler_class(hero)
    return None


# ═══════════════════════════════════════
# AUTO-REGISTER BASE HEROES
# ═══════════════════════════════════════

_BASE_HERO_MODULES = [
    ("kaizen", "kaizen_skills", "KaizenSkills"),
    ("grimjaw", "grimjaw_skills", "GrimjawSkills"),
    ("sylara", "sylara_skills", "SylaraSkills"),
    ("vex", "vex_skills", "VexSkills"),
    ("thorne", "thorne_skills", "ThorneSkills"),
    ("zephyr", "zephyr_skills", "ZephyrSkills"),
]

for hero_type, module_name, class_name in _BASE_HERO_MODULES:
    try:
        module = __import__(
            f"hero_skills.{module_name}",
            fromlist=[class_name])
        handler_class = getattr(module, class_name)
        register_handler(hero_type, handler_class)
    except ImportError:
        pass
    except Exception as e:
        print(f"[SKILLS] Failed to load {hero_type}: {e}")


# ═══════════════════════════════════════
# AUTO-REGISTER BOSS HEROES (dynamic!)
# ═══════════════════════════════════════

def _auto_register_boss_hero_skills():
    """
    Auto-register generic skill handler untuk SEMUA boss types
    dari boss_data.py.
    """
    try:
        from bosses.boss_data import (
            MINI_BOSS_TYPES, TRUE_BOSS_TYPES)
        from hero_skills.boss_hero_skills import BossHeroSkills

        all_boss_types = list(MINI_BOSS_TYPES.keys()) + \
                         list(TRUE_BOSS_TYPES.keys())

        for boss_type in all_boss_types:
            register_handler(boss_type, BossHeroSkills)
            print(f"[SKILLS] Auto-registered boss hero: "
                  f"{boss_type}")

    except ImportError as e:
        print(f"[SKILLS] BossHeroSkills auto-register "
              f"failed: {e}")


# Run auto-register on module import
_auto_register_boss_hero_skills()