# ================================
# heroes/__init__.py
# Registry untuk hero rendering
# Dispatch ke individual hero renderers
# ================================

import pygame
import math
import time as _time

# Pass cahaya bersama untuk SEMUA sprite hero (dipakai _finish_hd_sprite).
# Impornya di sini, bukan di tiap renderer: satu titik ubah untuk 200+ unit.
try:
    import lighting as _lighting
except Exception:                            # pragma: no cover
    _lighting = None
    HD_LIGHTING_BROKEN = True

# ═══ Hero renderers (starter heroes) ═══
HERO_RENDERERS = {}

# ─── PENGGABUNGAN FILE ───
# Isi grimjaw, kaizen, sylara, thorne, vex, zephyr
# sekarang ada di heroes/_bundle.py.
#
# Blok di bawah mendaftarkan nama submodul lama ke sys.modules,
# sehingga baris impor lama tetap jalan tanpa file fisiknya.
# Aman dipanggil berulang kali.
import sys as _sys
import types as _types

from heroes import _bundle as _b

_EXTRA = {
    'grimjaw': [
        'HAS_AACIRCLE', 'HAS_AALINES', 'PALETTE',
        '_aacircle', '_aaline', '_blade_angle',
        '_blade_grip_local', '_blade_len', '_blade_tip_local',
        '_clamp', '_detect_moving', '_draw_blade_fury_rings',
        '_draw_critical_strike_burst', '_draw_elite_flame_blade', '_draw_elite_flame_mane',
        '_draw_elite_mane_front', '_draw_elite_mask', '_draw_fire_aura',
        '_draw_fire_mist', '_draw_fire_particles_orbit', '_draw_fire_platform',
        '_draw_fire_slash_arc', '_draw_grimjaw_attack', '_draw_grimjaw_blade_fury',
        '_draw_grimjaw_body', '_draw_grimjaw_elite', '_draw_grimjaw_ghost',
        '_draw_grimjaw_idle', '_draw_grimjaw_masterwork_details', '_draw_grimjaw_omnislash',
        '_draw_grimjaw_walk', '_draw_heal_aura', '_draw_healing_ward_ground',
        '_draw_healing_ward_totem', '_draw_omnislash_ground', '_draw_omnislash_slashes',
        '_draw_shadow', '_poly', '_rect',
        '_target_position', '_update_attack_anim', 'draw_grimjaw',
        'draw_hero', 'math', 'pygame',
        'random',
    ],
    'sylara': [
        'HAS_AACIRCLE', 'PALETTE', 'RIG_H',
        'RIG_OX', 'RIG_OY', 'RIG_W',
        'ShackleProjectile', 'WindArrowProjectile', '_aacircle',
        '_aaline', '_bow_frame', '_bow_nock',
        '_bow_point', '_clamp', '_detect_moving',
        '_draw_bow_release_flash', '_draw_elite_arrow', '_draw_elite_bow',
        '_draw_floating_wind', '_draw_focus_fire_effect', '_draw_focus_fire_ground',
        '_draw_leaf', '_draw_powershot_charge', '_draw_ranger_silhouette_glow',
        '_draw_shackle_ground', '_draw_shadow', '_draw_sylara_attack',
        '_draw_sylara_body', '_draw_sylara_elite', '_draw_sylara_idle',
        '_draw_sylara_masterwork_details', '_draw_sylara_rig', '_draw_sylara_walk',
        '_draw_sylara_windrun', '_draw_wind_arc', '_draw_wind_aura',
        '_draw_wind_platform', '_draw_windrun_ground', '_draw_windrun_trail',
        '_ellipse', '_manage_projectiles', '_poly',
        '_rect', '_spawn_arrow', '_spawn_focus_fire_volley',
        '_spawn_shackle', '_target_position', '_update_attack_anim',
        '_world_to_local', 'draw_boss', 'draw_sylara',
        # Skill FX v2.1 world-space helpers
        'SKILL_VISUAL_DURATION', '_STATIC_SURFACES', '_static', '_hash01',
        '_mix', '_fx_scale', '_ring_r', '_spark_star', '_chevron',
        '_dashed_ring', '_jagged_crack', '_tuft_points',
    ],
    'kaizen': [
        'HAS_AACIRCLE', 'PALETTE', 'WindSlashProjectile',
        '_aacircle', '_aaline', '_clamp',
        '_detect_moving', '_draw_dash_effect', '_draw_dash_ground',
        '_draw_floating_wind', '_draw_kaizen_attack', '_draw_kaizen_body',
        '_draw_kaizen_elite', '_draw_kaizen_idle', '_draw_kaizen_walk',
        '_draw_shadow', '_draw_storm_aura', '_draw_sweep_effect',
        '_draw_sweep_ground', '_draw_tornado', '_draw_tornado_ground',
        '_draw_wind_arc', '_draw_wind_aura', '_draw_wind_platform',
        '_draw_wind_swirl', '_draw_wind_wall', '_draw_elite_katana',
        '_draw_swordsman_rim_light', '_ellipse', '_manage_projectiles',
        '_poly', '_rect', '_spawn_wind_slash', '_target_position',
        '_update_attack_anim', '_world_to_local', 'draw_boss',
        'draw_kaizen', 'math', 'pygame',
        # Skill FX v3 world-space helpers (standar Thorne / Grimjaw)
        '_STATIC_SURFACES', '_static', '_hash01', '_mix', '_fx_scale',
        '_spark_star', '_chevron', '_dashed_ring', '_aoe_marks', '_jagged_crack',
        '_tuft_points', '_dither_dots', '_attack_pose', '_katana_angle',
        'SKILL_VISUAL_DURATION', '_ring_r', '_skill_progress',
        '_katana_tip_local', '_draw_katana_swing_trail', '_filled_crescent',
        '_scratch', '_SCRATCH_POOL',
    ],
    'thorne': [
        'GooProjectile', 'HAS_AACIRCLE', 'PALETTE',
        'QuillProjectile', '_aacircle', '_aaline',
        '_clamp', '_detect_moving', '_draw_arc_pair',
        '_draw_bristleback_effect', '_draw_club_swing_trail', '_draw_dust_aura',
        '_draw_floating_dust', '_draw_ground_platform', '_draw_quill',
        '_draw_quill_spray_ground', '_draw_rage_aura', '_draw_shadow',
        '_draw_thorne_attack', '_draw_thorne_body', '_draw_thorne_idle',
        '_draw_thorne_walk', '_draw_viscous_charge', '_draw_viscous_ground',
        '_draw_warpath_effect', '_ellipse', '_handle_quill_spray_skill',
        '_manage_projectiles', '_poly', '_rect',
        '_spawn_goo', '_spawn_quill_spray', '_target_position',
        '_update_attack_anim', 'draw_boss', 'draw_thorne',
        'math', 'pygame',
    ],
    'vex': [
        'ArcaneOrbProjectile', 'AstralOrbProjectile', 'HAS_AACIRCLE',
        'PALETTE', '_aacircle', '_aaline',
        '_clamp', '_detect_moving', '_draw_arcane_orb_charge',
        '_draw_astral_indicator', '_draw_elite_crown', '_draw_elite_hood',
        '_draw_elite_staff', '_draw_essence_flux', '_draw_essence_flux_ground',
        '_draw_floating_void', '_draw_glow_orb', '_draw_orb_release_flash',
        '_draw_rune_ring', '_draw_sanity_eclipse', '_draw_sanity_eclipse_ground',
        '_draw_shadow', '_draw_vex_attack', '_draw_vex_body',
        '_draw_vex_elite', '_draw_vex_idle', '_draw_vex_masterwork_details',
        '_draw_vex_walk', '_draw_void_aura', '_draw_void_platform',
        '_ellipse', '_handle_astral_skill', '_manage_projectiles',
        '_orb_tip_local', '_poly', '_rect',
        '_spawn_arcane_orb', '_spawn_astral_orb', '_staff_butt_local',
        '_staff_grip_local', '_staff_orb_position', '_target_position',
        '_update_attack_anim', 'draw_boss', 'draw_vex',
        # Vex v2.1 skill FX helpers (public alias compatibility)
        'RIG_SCALE', 'SKILL_VISUAL_DURATION', '_STATIC_SURFACES', '_static',
        '_mix', '_hash01', '_fx_scale', '_ring_r', '_spark_star', '_chevron',
        '_dashed_ring', '_jagged_crack', '_tuft_points', '_draw_arc_pair',
        '_draw_arcane_orb_telegraph', '_draw_staff_smear',
        '_draw_staff_impact_flash', '_skill_progress',
        'math', 'pygame',
    ],
    'zephyr': [
        'CasketProjectile', 'HAS_AACIRCLE', 'MagicBoltProjectile',
        'PALETTE', '_aacircle', '_aaline',
        '_clamp', '_detect_moving', '_draw_bedlam',
        '_draw_bedlam_ground', '_draw_bramble_ground', '_draw_bramble_maze',
        '_draw_butterfly', '_draw_casket_indicator', '_draw_cast_flash',
        '_draw_fey_aura', '_draw_fey_platform', '_draw_floating_sparkles',
        '_draw_mini_fairy', '_draw_petal', '_draw_shadow',
        '_draw_shadow_realm', '_draw_shadow_realm_ground', '_draw_zephyr_attack',
        '_draw_zephyr_body', '_draw_zephyr_idle', '_draw_zephyr_walk',
        '_ellipse', '_handle_casket_skill', '_manage_projectiles',
        '_poly', '_rect', '_spawn_casket',
        '_spawn_magic_bolt', '_target_position', '_update_attack_anim',
        'draw_boss', 'draw_zephyr', 'math',
        'pygame',
        # ── v3: swing arc, weapon trail, animation controller, debug ──
        'ATTACK_ANTICIPATION_END', 'ATTACK_WINDUP_END', 'ATTACK_SWING_END',
        'ATTACK_IMPACT_END', 'ATTACK_FOLLOW_END', 'ATTACK_ACTIVE_WINDOW',
        'ATTACK_IMPACT_FRAME', 'ATTACK_ARC_START', 'ATTACK_ARC_SWEEP',
        'ATTACK_ARC_END', 'STAFF_PIVOT', 'STAFF_R_REST', 'STAFF_R_WINDUP',
        'STAFF_R_STRIKE', 'STAFF_R_FOLLOW', 'ANIM_STATES',
        'DEBUG_CHARACTER', '_resolve_anim_state', '_swing_hitbox',
        '_ease_in', '_ease_out', '_ease_in_out', '_staff_arc_pose',
        '_staff_tip_local', '_staff_grip_local', '_staff_bottom_local',
        '_staff_orb_position', '_staff_trail_samples',
        '_draw_staff_swing_trail', '_draw_debug',
    ],
}

_PLAIN_SYMS = {}


def _install_aliases():
    for _name, _syms in _EXTRA.items():
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _ns = getattr(_b, "_NS_" + _name, None)
        if _ns is None:
            continue
        _m = _types.ModuleType(_full)
        _m.__doc__ = "heroes/" + _name + ".py (digabung ke _bundle.py)"
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
        _m.__doc__ = "heroes/" + _name + ".py (digabung ke _bundle.py)"
        for _k in _syms:
            if hasattr(_b, _k):
                setattr(_m, _k, getattr(_b, _k))
        _sys.modules[_full] = _m
        setattr(_sys.modules[__name__], _name, _m)


_install_aliases()

try:
    from heroes.grimjaw import draw_grimjaw
    HERO_RENDERERS["grimjaw"] = draw_grimjaw
except ImportError as e:
    print(f"[HERO WARNING] grimjaw failed: {e}")

try:
    from heroes.kaizen import draw_kaizen
    HERO_RENDERERS["kaizen"] = draw_kaizen
except ImportError as e:
    print(f"[HERO WARNING] kaizen failed: {e}")

try:
    from heroes.sylara import draw_sylara
    HERO_RENDERERS["sylara"] = draw_sylara
except ImportError as e:
    print(f"[HERO WARNING] sylara failed: {e}")

try:
    from heroes.thorne import draw_thorne
    HERO_RENDERERS["thorne"] = draw_thorne
except ImportError as e:
    print(f"[HERO WARNING] thorne failed: {e}")

try:
    from heroes.vex import draw_vex
    HERO_RENDERERS["vex"] = draw_vex
except ImportError as e:
    print(f"[HERO WARNING] vex failed: {e}")

try:
    from heroes.zephyr import draw_zephyr
    HERO_RENDERERS["zephyr"] = draw_zephyr
except ImportError as e:
    print(f"[HERO WARNING] zephyr failed: {e}")

# ═══════════════════════════════════════════════════════
# Boss hero renderers - AUTO-REGISTER dari boss_data
#
# Dulu 28 boss di-import satu per satu dengan
# `try: ... except ImportError: pass`. Pola itu MENYEMBUNYIKAN
# bug: kalau nama fungsi di file tidak cocok (mis. gravefang.py
# isinya draw_morgath), import gagal diam-diam dan boss render
# jadi lingkaran generic tanpa pesan apa pun.
#
# Sekarang: loop dinamis dari boss_data + WARNING eksplisit.
# Tambah boss baru = cukup daftar di boss_data.py.
# ═══════════════════════════════════════════════════════

BOSS_RENDERERS = {}

# Boss yang nama fungsinya beda dari nama file.
# Kalau bisa, perbaiki nama fungsi di file-nya; ini jaring pengaman.
_BOSS_FUNC_ALIAS = {
    "ancient_apparition": ["draw_ancient_apparition", "draw_apparition"],
    "ignis_drachorn": ["draw_ignis_drachorn", "draw_ignis"],
    "gravefang": ["draw_gravefang", "draw_morgath"],
}

# Diisi _register_boss_renderers(), berguna untuk debug.
BOSS_RENDERER_ERRORS = {}


def _resolve_boss_draw_func(module, boss_type):
    """Cari fungsi draw yang cocok di dalam module boss."""
    candidates = _BOSS_FUNC_ALIAS.get(boss_type,
                                      [f"draw_{boss_type}"])
    for name in candidates:
        func = getattr(module, name, None)
        if callable(func):
            return func, name

    # Fallback longgar HANYA untuk modul per-boss (satu boss per file).
    # Modul gabungan bosses/levelN.py berisi 4 boss sekaligus, jadi
    # menebak "draw_* apa pun" bisa mengembalikan boss yang SALAH.
    if not getattr(module, "_IS_LEVEL_BUNDLE", False):
        for name in dir(module):
            if name.startswith("draw_") and name != "draw_boss":
                func = getattr(module, name)
                if callable(func):
                    return func, name

    if not getattr(module, "_IS_LEVEL_BUNDLE", False):
        func = getattr(module, "draw_boss", None)
        if callable(func):
            return func, "draw_boss"

    return None, None


def _boss_level_candidates(boss_type):
    """Urutan level yang dicoba saat mencari renderer sebuah boss.

    Kalau paket `levels` bisa dibaca, level yang tepat dicoba lebih
    dulu supaya cepat. Kalau tidak, semua level 1..8 dicoba.
    """
    order = []
    try:
        from levels import ALL_LEVELS
        for cfg in ALL_LEVELS:
            types = set(cfg.get("mini_bosses", {}).values())
            tb = cfg.get("true_boss")
            if tb:
                types.add(tb)
            if boss_type in types:
                order.append(cfg.get("level_number"))
    except Exception:
        pass
    for n in range(1, 21):
        if n not in order:
            order.append(n)
    return [n for n in order if isinstance(n, int)]


def _module_has_boss(module, boss_type):
    """True kalau module benar-benar punya fungsi draw untuk boss ini."""
    for name in _BOSS_FUNC_ALIAS.get(boss_type, [f"draw_{boss_type}"]):
        if callable(getattr(module, name, None)):
            return True
    return False


def _register_boss_renderers_eager():
    """Versi lama: impor SEMUA modul boss saat start (lambat).

    Dipertahankan untuk debugging: MYSTIC_EAGER_BOSS=1 python main.py
    """
    import importlib

    try:
        from bosses.boss_data import (
            MINI_BOSS_TYPES, TRUE_BOSS_TYPES)
    except ImportError as e:
        print(f"[HERO WARNING] boss_data tidak bisa di-import: {e}")
        return

    all_types = list(MINI_BOSS_TYPES.keys()) + \
        list(TRUE_BOSS_TYPES.keys())

    for boss_type in all_types:
        module = None
        last_err = None

        # (a) file per-boss lama, kalau masih ada
        try:
            module = importlib.import_module(f"bosses.{boss_type}")
        except ImportError:
            module = None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            module = None

        # (b) file gabungan bosses/levelN.py
        if module is None:
            for lvl in _boss_level_candidates(boss_type):
                try:
                    cand = importlib.import_module(f"bosses.level{lvl}")
                except ImportError as e:
                    last_err = f"import gagal: {e}"
                    continue
                except Exception as e:
                    last_err = f"{type(e).__name__}: {e}"
                    continue
                if _module_has_boss(cand, boss_type):
                    module = cand
                    break

        if module is None:
            BOSS_RENDERER_ERRORS[boss_type] = (
                last_err or "renderer tidak ditemukan")
            print(f"[HERO WARNING] renderer {boss_type} tidak ketemu "
                  f"di bosses/{boss_type}.py maupun bosses/levelN.py: "
                  f"{last_err or 'tidak ada fungsi draw_%s()' % boss_type}")
            continue

        func, func_name = _resolve_boss_draw_func(module, boss_type)

        if func is None:
            BOSS_RENDERER_ERRORS[boss_type] = "tidak ada fungsi draw_*"
            print(f"[HERO WARNING] bosses/{boss_type}.py tidak punya "
                  f"fungsi draw_{boss_type}() -> boss ini akan "
                  f"render sebagai bentuk generic!")
            continue

        BOSS_RENDERERS[boss_type] = func

        expected = f"draw_{boss_type}"
        if func_name != expected:
            print(f"[HERO NOTE] {boss_type}: pakai {func_name}() "
                  f"(diharapkan {expected}())")

    print(f"[HERO] Boss renderer terdaftar: "
          f"{len(BOSS_RENDERERS)}/{len(all_types)}")


# ═══════════════════════════════════════════════════════
# REGISTRASI MALAS (LAZY) - optimasi start-up Android
#
# Dulu: 54 modul bosses/level*.py (±4 MB kode) diimpor saat start
#       hanya untuk mencari fungsi draw_*(). Di HP ini memakan
#       beberapa detik dan puluhan MB RAM.
# Kini: dipakai indeks statis bosses/_boss_index.py; modul boss
#       diimpor pada pemakaian pertama saja.
#
# Buat ulang indeks setelah menambah boss:
#     python tools/gen_boss_index.py
# ═══════════════════════════════════════════════════════
class _LazyBossRenderer:
    """Proxy yang meng-impor modul boss saat pertama kali dipanggil."""

    __slots__ = ("boss_type", "_func")

    def __init__(self, boss_type):
        self.boss_type = boss_type
        self._func = None

    def _resolve(self):
        import importlib
        try:
            from bosses._boss_index import BOSS_INDEX
        except ImportError:
            BOSS_INDEX = {}

        entry = BOSS_INDEX.get(self.boss_type)
        if entry:
            mod_name, func_name = entry
            try:
                module = importlib.import_module("bosses." + mod_name)
                func = getattr(module, func_name, None)
                if callable(func):
                    self._func = func
                    BOSS_RENDERERS[self.boss_type] = func
                    return func
            except Exception as exc:
                BOSS_RENDERER_ERRORS[self.boss_type] = (
                    "%s: %s" % (type(exc).__name__, exc))

        # Cadangan: pencarian lama (berkas per-boss / tebak levelN)
        module = None
        try:
            module = importlib.import_module("bosses." + self.boss_type)
        except Exception:
            module = None
        if module is None:
            for lvl in _boss_level_candidates(self.boss_type):
                try:
                    cand = importlib.import_module("bosses.level%d" % lvl)
                except Exception:
                    continue
                if _module_has_boss(cand, self.boss_type):
                    module = cand
                    break
        if module is not None:
            func, _name = _resolve_boss_draw_func(module, self.boss_type)
            if callable(func):
                self._func = func
                BOSS_RENDERERS[self.boss_type] = func
                return func

        BOSS_RENDERER_ERRORS.setdefault(
            self.boss_type, "renderer tidak ditemukan")
        print("[HERO WARNING] renderer %s tidak ketemu" % self.boss_type)
        self._func = False
        return None

    def __call__(self, surface, boss, x, y, *args, **kwargs):
        func = self._func
        if func is None:
            func = self._resolve()
        if not func:
            return None
        return func(surface, boss, x, y, *args, **kwargs)

    def __repr__(self):
        state = "belum dimuat" if self._func is None else "siap"
        return "<LazyBossRenderer %s (%s)>" % (self.boss_type, state)


def _register_boss_renderers_lazy():
    """Daftarkan proxy malas untuk semua boss - nol impor modul boss."""
    try:
        from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
        all_types = list(MINI_BOSS_TYPES.keys()) + list(TRUE_BOSS_TYPES.keys())
    except ImportError as exc:
        print("[HERO WARNING] boss_data tidak bisa di-import: %s" % exc)
        return

    try:
        from bosses._boss_index import BOSS_INDEX
    except ImportError:
        BOSS_INDEX = {}
        print("[HERO WARNING] bosses/_boss_index.py belum dibuat - "
              "jalankan: python tools/gen_boss_index.py")

    for boss_type in all_types:
        BOSS_RENDERERS[boss_type] = _LazyBossRenderer(boss_type)

    known = sum(1 for t in all_types if t in BOSS_INDEX)
    print("[HERO] Boss renderer siap (lazy): %d/%d terindeks"
          % (known, len(all_types)))


def preload_boss_renderers(boss_types):
    """Muat renderer di depan (mis. saat layar loading level)."""
    for boss_type in boss_types or ():
        renderer = BOSS_RENDERERS.get(boss_type)
        if isinstance(renderer, _LazyBossRenderer):
            renderer._resolve()


import os as _os

if _os.environ.get("MYSTIC_EAGER_BOSS") == "1":
    _register_boss_renderers_eager()
else:
    _register_boss_renderers_lazy()


# ═══════════════════════════════════════════════════════
# HERO → BOSS ATTRIBUTE ADAPTER
# ═══════════════════════════════════════════════════════

def _adapt_hero_to_boss(hero):
    """
    Sync Hero attributes ke Boss-compatible names.

    Aman dipanggil untuk:
    - Hero asli (punya property alias, assignment jadi no-op sinkron)
    - Fake entity dari ui_components/hero_portraits.py
    - Mock object dari test harness
    """
    # facing -> direction (Hero punya property, jadi idempotent).
    # Dibungkus try/except: kalau object punya property read-only,
    # nilainya memang sudah benar, tidak perlu di-set.
    #
    # FIX SWING KACAU: selama jendela serangan (attack_timer > 0),
    # arah hadap DIKUNCI ke arah saat serangan dimulai
    # (hero._attack_facing, di-set oleh _do_attack). Tanpa ini,
    # hero yang kena hit lalu retreat/chase akan membalik pose
    # swing setiap frame karena facing diubah kode gerakan.
    try:
        if hasattr(hero, 'facing'):
            locked = getattr(hero, '_attack_facing', None)
            attack_remaining = int(getattr(hero, 'attack_timer', 0) or 0)
            if locked is not None and attack_remaining > 0:
                hero.direction = locked
            else:
                hero.direction = hero.facing
        elif not hasattr(hero, 'direction'):
            hero.direction = 1
    except AttributeError:
        pass

    # attack_timer -> timer
    try:
        if hasattr(hero, 'attack_timer'):
            hero.timer = hero.attack_timer
        elif not hasattr(hero, 'timer'):
            hero.timer = 0
    except AttributeError:
        pass

    # Atribut yang wajib ada untuk renderer boss-style
    if not hasattr(hero, 'pulse'):
        hero.pulse = 0.0
    if not hasattr(hero, 'active_skill'):
        hero.active_skill = None
    if not hasattr(hero, 'active_skill_timer'):
        hero.active_skill_timer = 0
    if not hasattr(hero, 'attack_cooldown'):
        hero.attack_cooldown = 45

    # hero_type -> boss_type
    if not hasattr(hero, 'boss_type'):
        hero.boss_type = getattr(hero, 'hero_type', 'unknown')

    if not hasattr(hero, 'boss_class'):
        hero.boss_class = "mini"


# ═══════════════════════════════════════════════════════
# HERO SCALE SYSTEM
# Boss renderer didesain untuk boss (besar).
# Saat dipakai sebagai hero, perlu di-scale down.
# ═══════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
# HERO SIZE NORMALISATION
#
# Starter hero (kaizen/thorne/vex/...) digambar ~119 px tinggi.
# Boss renderer ukurannya beragam (83 - 175 px), jadi kalau
# dipakai sebagai hero ada yang kelihatan raksasa.
#
# Target: SEMUA hero (starter maupun boss-hero, tim biru maupun
# merah) punya tinggi visual yang sama.
# ═══════════════════════════════════════════════════════

# ═══ BEAM PASS (boss ranged yang beam-nya digambar di layar, skala 1.0) ═══
# Untuk boss-hero di daftar ini, beam serangan TIDAK ikut di-scale di
# canvas. Body di-scale seperti biasa, lalu beam digambar ulang
# langsung ke layar pada skala 1.0 -> tampilannya PERSIS sama seperti
# saat entity ini jadi mini boss (jalur kode yang sama, tanpa
# smoothscale). Tambah hero_type lain di sini bila renderer-nya sudah
# punya hook _beam_pass_only (lihat bosses/level1.py, _NS_morgath).
_BEAM_PASS_HEROES = {"morgath"}

# ═══════════════════════════════════════════════════════
# LIVE FX PASS
#
# Sprite hero DI-CACHE (lihat render_hero). Konsekuensinya semua yang
# harus bergerak 60 fps sejati - trail senjata, partikel, projectile,
# impact - tidak boleh hidup di dalam canvas cache: hasilnya akan ikut
# beku selama pose yang sama dipakai ulang.
#
# Hero di daftar ini punya modul FX terpisah yang digambar LANGSUNG ke
# layar pada skala 1.0 setiap frame:
#   pre   -> GROUND FX + BACK PARTICLES (di bawah sprite)
#   post  -> TRAIL / PROJECTILE / FRONT PARTICLES / SKILL / IMPACT
#
# Modul yang sama juga dipakai jalur BOSS (lihat _NS_gornak.draw_gornak),
# jadi satu karakter punya satu bahasa efek di arena maupun di lane.
#
# Vex (heroes/vex_fx.py) mengikuti pola yang sama: arc ayunan staff,
# partikel void, proyektil serpihan, spike crystal W, kurungan astral E,
# ledakan Essence Flux R, impact, hit-stop, dan shake — semuanya hidup
# di luar cache sprite supaya tetap mulus 60 fps.
# Krobellus (heroes/krobellus_fx.py) — The Death Prophet: ribbon trail
# sabit spectral dari histori posisi bilah, soul bolt modular (inti +
# glow + bentuk directional + trail + jiwa), partikel jiwa/serpihan,
# skill FX Q Exorcism (blade-burst) / W Silence (bolt void + hex) /
# E Spirit Siphon (arus jiwa + vortex) / R Crypt Swarm (erupsi + ghost
# wave), impact flash + shockwave, hit-stop 0.03-0.08 s, dan shake —
# semua hidup di luar cache sprite.
# ═══════════════════════════════════════════════════════
# Sylara (heroes/sylara_fx.py) melengkapi daftar ini: pita sapuan busur
# arc-based, panah angin prosedural dengan lifecycle penuh, daun/gust
# particle system, sulur Shackle, siklon Windrun, gale Powershot, impact,
# hit-stop, dan shake — semua hidup di luar cache sprite.
# Gorath (heroes/gorath_fx.py) menutup pola yang sama: trail sabit darah
# dari histori ujung kukri, bolt darah modular, particle system, skill FX
# Q/W/E/R (pilar, voli, jejak lompat, rantai+ledakan), impact, hit-stop,
# dan shake — semua hidup di luar cache sprite.
# Alchemist (heroes/alchemist_fx.py) menyusul pola yang sama untuk duo
# ogre-goblin: trail cleaver busur, botol asam modular dengan lifecycle
# penuh, semburan droplet Acid Spray, badai koin Greevil's Greed,
# uap Chemical Rage, impact, hit-stop, dan shake.
# Ancient Apparition (heroes/ancient_apparition_fx.py): arc ayunan cakar
# kristal, trail sapuan ribbon, particle system salju/es/mist, proyektil
# shard & bolt modular, vortex Q / beam gerigi W / Ice Blast E / erupsi
# Cold Feet R, impact flash + shockwave + debris, shatter kematian,
# hit-stop, dan shake — semuanya hidup di luar cache sprite.
# Nyzrak (heroes/nyzrak_fx.py): rig pixel-art wyvern rider dari level3
# (canvas ter-cache) + lapisan hidup berisi pita sapuan tombak dari
# histori posisi blade, proyektil lanset es modular, beam Arctic Burn
# bergerigi, kerucut Splinter Blast, kurungan kristal Winter's Curse,
# nova + kubah Cold Embrace, impact flash + shockwave + serpihan,
# hit-stop 0.03-0.08 s, dan shake — 60 fps di luar cache sprite.
# Zharok (heroes/zharok_fx.py): rig pemanah tulang berkerudung dari
# level4 (canvas ter-cache) + lapisan hidup berisi pita sapuan busur
# dari histori posisi bilah saat Ember Cleave, anak panah api modular
# (inti + glow + sirip + trail + bara), koridor bidik Strafe, kolam
# asap Skeleton Walk, pentagram + berkas jiwa Death Pact, retakan
# magma + pilar api Burning Army, impact flash + shockwave + serpihan,
# hit-stop 0.03-0.08 s, dan shake — semuanya di luar cache sprite.
# Vhalzun (heroes/vhalzun_fx.py) melengkapi daftar untuk The Reaper of
# Souls: pita sapuan sabit dari histori ujung bilah (busur reaper
# ANTICIPATION->RECOVERY), death pulse & gelombang Reaper's Scythe
# modular (inti + glow + bentuk directional + trail + partikel jiwa),
# nova jiwa bergerigi Death Pulse, sigil heks + leech Heartstopper,
# wraith + cangkang spektral Ghost Shroud, impact flash + shockwave +
# serpihan tulang, afterimage, hit-stop 0.03-0.08 s, dan shake —
# semua hidup di luar cache sprite.
# Nyxara (heroes/nyxara_fx.py) menutup daftar untuk The Nether Matron:
# pita sapuan tongkat dari histori kepala tongkat (busur ANTICIPATION->
# RECOVERY), nether orb & Nether Blast modular (inti + glow + bentuk
# directional + cangkang bergerigi berputar + trail + bara), nova
# bergerigi Nether Blast, kurva kutukan + sigil heks Decrepify, totem
# tengkorak + busur nether Nether Ward, tether jiwa berpilin Life Drain,
# impact flash + shockwave + serpihan tulang, afterimage, hit-stop
# 0.03-0.08 s, dan shake — semua hidup di luar cache sprite.
# Gravefang (heroes/gravefang_fx.py) melengkapi daftar untuk The Bone
# Devourer: pita hantaman gada dari histori kepala gada (busur
# ANTICIPATION->RECOVERY), pecahan tulang & Rolling Boulder modular
# (bilah bergerigi berputar + batu bergulir + trail debu + afterimage),
# nova bergerigi + pilar batu Boulder Smash, jalur gilasan Rolling
# Boulder, pasak tulang + rantai energi Geomagnetic Grip, orbit batu
# tersedot Magnetize, impact flash + shockwave + retakan tanah +
# puing, hit-stop 0.03-0.08 s, dan shake — semua di luar cache sprite.
# Khalros (heroes/khalros_fx.py) - The Beastlord. BADANNya digambar
# renderer boss (bosses/level2._NS_khalros, rig v2); modul ini hanya lapisan
# hidup: pita ayunan dari histori UJUNG BILAH rig (bukan perkiraan bahu),
# kapak berputar & elang penyelam, debu bantingan + jejak cakar di lantai,
# gemuruh Call of the Wild, impact flash + shockwave + bara, hit-stop
# 0.03-0.08 s, dan shake — semua di luar cache sprite. Tanpa entri ini lane
# hero memasang lapisan (attach -> renderer menyerahkan FX sendiri) namun
# tidak ada yang men-tick-nya, sehingga Q/W/E/R hilang di lane.
_LIVE_FX_HEROES = {"zephyr", "gornak", "grimjaw", "kaizen", "vex",
                   "sylara", "abaddon", "gorath", "razak", "khalros",
                   "alchemist", "ancient_apparition", "nyzrak",
                   "xerathis", "varkul", "ignis_drachorn", "zharok",
                   "vokrahn", "pyrenth", "krobellus", "vhalzun",
                   "nyxara", "gravefang", "thalgryn", "kunkka",
                   "syrentha", "gravewake"}
_LIVE_FX_MODULES = {}

_LIVE_FX_PATHS = {
    "zephyr": "heroes.zephyr_fx",
    "gornak": "heroes.gornak_fx",
    "grimjaw": "heroes.grimjaw_fx",
    "kaizen": "heroes.kaizen_fx",
    "vex": "heroes.vex_fx",
    "sylara": "heroes.sylara_fx",
    "abaddon": "heroes.abaddon_fx",
    "gorath": "heroes.gorath_fx",
    "razak": "heroes.razak_fx",
    "khalros": "heroes.khalros_fx",
    "alchemist": "heroes.alchemist_fx",
    "ancient_apparition": "heroes.ancient_apparition_fx",
    "nyzrak": "heroes.nyzrak_fx",
    "xerathis": "heroes.xerathis_fx",
    "varkul": "heroes.varkul_fx",
    "ignis_drachorn": "heroes.ignis_drachorn_fx",
    "zharok": "heroes.zharok_fx",
    "vokrahn": "heroes.vokrahn_fx",
    "pyrenth": "heroes.pyrenth_fx",
    "krobellus": "heroes.krobellus_fx",
    "vhalzun": "heroes.vhalzun_fx",
    "nyxara": "heroes.nyxara_fx",
    "gravefang": "heroes.gravefang_fx",
    "thalgryn": "heroes.thalgryn_fx",
    "kunkka": "heroes.kunkka_fx",
    "syrentha": "heroes.syrentha_fx",
    "gravewake": "heroes.gravewake_fx",
}


def _live_fx_module(hero_type):
    """Ambil modul FX hidup untuk hero_type (lazy import, cached)."""
    if hero_type not in _LIVE_FX_HEROES:
        return None
    mod = _LIVE_FX_MODULES.get(hero_type)
    if mod is None:
        try:
            import importlib
            path = _LIVE_FX_PATHS.get(hero_type)
            if path is None:                           # pragma: no cover
                raise ImportError("no live FX module for %s" % hero_type)
            mod = importlib.import_module(path)
        except Exception as _e:                      # pragma: no cover
            print(f"[HERO WARNING] live FX {hero_type} failed: {_e}")
            mod = False
        _LIVE_FX_MODULES[hero_type] = mod
    if mod:
        _install_global_fx_caps(mod)
    return mod or None


# ── CAP SPAWN GLOBAL (semua hero live-FX, tanpa edit 27 *_fx.py) ──
# ParticleSystem.spawn / ProjectileSystem.spawn di tiap modul di-wrap
# sekali setelah impor. Token di-claim SEBELUM spawn asli; dikembalikan
# kalau jumlah hidup tidak bertambah (director menolak / pool penuh).
# Particle.spawn (factory instance) TIDAK di-wrap — itu dipanggil dari
# ParticleSystem dan akan double-count.
_FX_WRAP_FLAG = "_mystic_global_fx_cap"


def _fx_sys_live_count(sys):
    """Jumlah partikel/proyektil hidup di satu sistem FX."""
    cnt = getattr(sys, "count", None)
    if callable(cnt):
        try:
            return int(cnt())
        except Exception:
            pass
    for attr in ("_live", "live", "items", "projectiles", "projs"):
        v = getattr(sys, attr, None)
        if isinstance(v, list):
            return len(v)
    pool = getattr(sys, "particles", None)
    if isinstance(pool, list):
        n = 0
        for p in pool:
            if getattr(p, "active", True):
                n += 1
        return n
    return -1


def _wrap_fx_spawn(orig, kind):
    """Bungkus spawn: claim token dulu, refund kalau spawn gagal."""

    def spawn(self, *args, **kwargs):
        try:
            from mobile import perf as _p
            if not getattr(_p, "_FX_TOKENS_ACTIVE", False):
                return orig(self, *args, **kwargs)
            if kind == "particle":
                claim, refund = _p.claim_fx_particle, _p.refund_fx_particle
            else:
                claim, refund = _p.claim_fx_projectile, _p.refund_fx_projectile
        except Exception:
            return orig(self, *args, **kwargs)
        if not claim():
            return None
        before = _fx_sys_live_count(self)
        out = orig(self, *args, **kwargs)
        after = _fx_sys_live_count(self)
        if before >= 0 and after <= before:
            refund()
        return out

    spawn.__name__ = getattr(orig, "__name__", "spawn")
    spawn.__doc__ = getattr(orig, "__doc__", None)
    setattr(spawn, _FX_WRAP_FLAG, True)
    return spawn


def _install_global_fx_caps(mod):
    """Pasang wrap spawn pada ParticleSystem / ProjectileSystem modul ini."""
    if not mod or getattr(mod, _FX_WRAP_FLAG, False):
        return
    for cls_name, kind in (("ParticleSystem", "particle"),
                           ("ProjectileSystem", "projectile")):
        cls = getattr(mod, cls_name, None)
        if cls is None:
            continue
        for name, attr in list(vars(cls).items()):
            if not name.startswith("spawn") or not callable(attr):
                continue
            if getattr(attr, _FX_WRAP_FLAG, False):
                continue
            setattr(cls, name, _wrap_fx_spawn(attr, kind))
    setattr(mod, _FX_WRAP_FLAG, True)


# ── GOVERNOR BEBAN FX COMBAT ─────────────────────────────
# Saat banyak hero bertarung sekaligus, setiap hero live-FX menggambar
# partikel/trail/ring sendiri tiap frame. Tanpa batas global, biaya draw
# naik linear dengan jumlah hero -> FPS ambruk -> game terasa slow-motion,
# dan glow/ring additive yang menumpuk menutupi sprite hero.
#
# _core.py memanggil begin_fx_frame() sekali per frame dengan jumlah hero
# yang sedang aktif. fx_load() (mobile/perf.py) lalu menurunkan intensitas
# FX global: partikel menyusut lewat Quality.particle_ratio, yang dibaca
# SEMUA modul heroes/*_fx.py tanpa perlu diubah satu per satu.
#
# ⚠ Lapisan FX TIDAK PERNAH dilewati antar-frame. Versi pertama governor
#   ini menyelingi draw (1 dari 2 frame, lalu 1 dari 3 saat beban ekstrem)
#   supaya blit per frame lebih sedikit. Akibatnya skill FX berkedip
#   (kedap-kedip) dan tiap hero berkedip pada fase berbeda karena offset
#   id(hero) — persis keluhan "skill fx kedap kedip tidak stabil".
#   Menghemat biaya dengan membuang frame = efek hilang-muncul, jadi satu-
#   satunya tuas yang benar adalah INTENSITAS (jumlah partikel / ukuran
#   glow), bukan frekuensi gambar.
_FX_FRAME = 0
# Jumlah unit live-FX yang sedang aktif pada frame terakhir. Diisi oleh
# begin_fx_frame(); dibaca oleh _skill_quant() untuk menyesuaikan
# granularitas pose skill dengan beban combat.
_FX_BUSY_COUNT = 0


def _skill_quant():
    """Granularitas pose skill: makin ramai combat, makin kasar.

    Ini inti dari perbaikan lag "saat wave besar / banyak hero".

    Angka terukur (tools/bench_hero_cache.py, 10 hero + 120 minion):

        skill quant 2  : 10.00 ms/frame, hit rate 78.5%, 600 entri
        skill quant 12 :  5.38 ms/frame, hit rate 95.2%, 343 entri

    Kenapa bisa sejauh itu: ``active_skill_timer`` berjalan 0..240.
    Dengan quant 2 satu cast menghasilkan sampai 120 pose unik, dan
    tiap pose cuma dipakai 2 frame — jadi hit rate maksimal secara
    matematis hanya ~50%, dan sisanya bayar cache-MISS 4.12 ms
    (lebih mahal daripada render langsung 3.07 ms).

    Tapi quant kasar tidak boleh dipatok permanen: saat combat sepi
    (1-2 hero) tidak ada alasan mengorbankan kehalusan animasi.
    Maka granularitas mengikuti jumlah unit yang sedang bertarung —
    persis pola governor FX yang sudah dipakai untuk partikel.
    """
    n = _FX_BUSY_COUNT
    if n <= 2:
        return HERO_SKILL_QUANT           # 2  - combat sepi, animasi halus
    if n <= 4:
        return 4
    if n <= 6:
        return 8
    return 12                             # wave besar: FPS diprioritaskan


def begin_fx_frame(active_count=0):
    """Panggil SEKALI per frame (dari Game.draw) untuk menyetel beban FX."""
    global _FX_FRAME, _FX_BUSY_COUNT
    _FX_FRAME += 1
    try:
        _FX_BUSY_COUNT = max(0, int(active_count or 0))
    except Exception:
        _FX_BUSY_COUNT = 0
    try:
        from mobile import perf as _perf
        _perf.set_fx_load(active_count)
    except Exception:
        pass
    for _mod in _LIVE_FX_MODULES.values():
        if _mod:
            _install_global_fx_caps(_mod)


def fx_frame():
    """Nomor frame governor saat ini (debug / overlay HUD)."""
    return _FX_FRAME


def _fx_busy(hero):
    """True kalau hero sedang memproduksi FX (serang / skill / proyektil).

    Juga dipakai untuk BOSS (mini/true) sejak boss memakai lapisan FX
    hidup yang sama lewat ``render_boss`` — nama atribut timer serangan
    boss adalah ``timer``, hero ``attack_timer``.
    """
    if getattr(hero, "active_skill", None):
        return True
    if int(getattr(hero, "attack_timer", 0) or 0) > 0:
        return True
    if int(getattr(hero, "timer", 0) or 0) > 0:
        return True
    projs = getattr(hero, "projectiles", None)
    if projs:
        for p in projs:
            if p.get("alive"):
                return True
    return False


def count_busy_fx_heroes(heroes):
    """Jumlah unit live-FX yang sedang aktif (untuk governor beban).

    Menerima hero MAUPUN boss: boss tidak punya ``hero_type`` melainkan
    ``boss_type``, dan sejak ``render_boss`` memakai lapisan FX hidup
    yang sama, bebannya harus ikut dihitung supaya governor menurunkan
    intensitas partikel saat boss sedang bertarung ramai.
    """
    n = 0
    for h in heroes:
        kind = getattr(h, "hero_type", None) or getattr(h, "boss_type", None)
        if kind not in _LIVE_FX_HEROES:
            continue
        if getattr(h, "alive", True) and _fx_busy(h):
            n += 1
    return n


def _live_fx_pre(hero_type, surface, hero, x, y):
    """Lapisan FX di BAWAH sprite hero (ground FX, back particles).

    Selalu digambar tiap frame. Lihat catatan "GOVERNOR BEBAN FX COMBAT":
    melewatkan frame membuat skill FX berkedip, jadi penghematan beban
    dilakukan lewat intensitas partikel (Quality.particle_ratio), bukan
    lewat frekuensi gambar.
    """
    if hero_type not in _LIVE_FX_HEROES:
        return
    if getattr(hero, "_portrait_hd", False):
        return
    mod = _live_fx_module(hero_type)
    if mod is None:
        return
    try:
        mod.draw_ground_layer(surface, hero, x, y)
    except Exception:
        pass


def _live_fx_post(hero_type, surface, hero, x, y):
    """Lapisan FX di ATAS sprite hero (trail, projectile, skill, impact).

    Selalu digambar tiap frame — alasan sama seperti ``_live_fx_pre``.
    """
    if hero_type not in _LIVE_FX_HEROES:
        return
    if getattr(hero, "_portrait_hd", False):
        return
    mod = _live_fx_module(hero_type)
    if mod is None:
        return
    try:
        mod.draw_live_layer(surface, hero, x, y)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
# CONTROLLER POSE PER-FRAME (di luar sprite cache)
# ═══════════════════════════════════════════════════════
#
# Sebagian renderer MEMUTASI state animasi di dalam fungsi draw-nya.
# Gorath: ``_update_gorath_attack_anim`` mengisi ``_gor_attack_frame``,
# ``_gor_prev_timer``, dan ``_gor_attack_active`` setiap dipanggil.
#
# Masalahnya sprite hero di-cache dengan key ``attack_timer // 2``.
# Serangan pertama mengisi bucket 16..0, jadi renderer jalan dan
# animasi terlihat.  Pada serangan BERIKUTNYA bucket yang sama sudah
# terisi -> cache hit -> renderer dilewati -> controller tidak maju
# lagi dan pose membeku di fase terakhir.  Gejala di layar: Gorath
# mengayun sekali lalu tidak pernah mengayun lagi.
#
# Karena itu controller pose dijalankan SETIAP frame di sini, sebelum
# cache diperiksa.  Renderer yang bersangkutan lalu melewatinya di
# jalur hero lane supaya tidak maju dua kali dalam satu frame.

_POSE_CONTROLLER_SPECS = {
    # hero_type: (nama modul, nama namespace, nama fungsi)
    #
    # Diisi dari audit tools/test_hero_pose_cache.py: hero yang urutan
    # fase serangnya BERBEDA antara sprite-cache aktif (kondisi game)
    # dan cache dimatikan (referensi).  Hero yang tidak ada di sini
    # pose-nya murni fungsi attack_timer, jadi aman di-cache.
    "abaddon":        ("bosses.level1", "_NS_abaddon",
                       "_update_attack_anim"),
    "alchemist":      ("bosses.level2", "_NS_alchemist",
                       "_update_attack_anim"),
    "gorath":         ("bosses.level2", "_NS_gorath",
                       "_update_gorath_attack_anim"),
    "gornak":         ("bosses.level1", "_NS_gornak",
                       "_update_gnk_attack_anim"),
    "gravefang":      ("bosses.level5", "_NS_gravefang",
                       "_update_gravefang_anim"),
    "gravewake":      ("bosses.level6", "_NS_gravewake",
                       "_update_gravewake_attack_anim"),
    "ignis_drachorn": ("bosses.level4", "_NS_ignis_drachorn",
                       "_update_attack_anim"),
    "krobellus":      ("bosses.level5", "_NS_krobellus",
                       "_update_krb_anim"),
    "kunkka":         ("bosses.level6", "_NS_kunkka",
                       "_update_kunkka_attack_anim"),
    "nyxara":         ("bosses.level5", "_NS_nyxara",
                       "_update_nyxara_anim"),
    "pyrenth":        ("bosses.level4", "_NS_pyrenth",
                       "_update_attack_anim"),
    "razak":          ("bosses.level2", "_NS_razak",
                       "_update_attack_anim"),
    "sylara":         ("heroes._bundle", "_NS_sylara",
                       "_update_attack_anim"),
    "syrentha":       ("bosses.level6", "_NS_syrentha",
                       "_update_syrentha_attack_anim"),
    "thalgryn":       ("bosses.level6", "_NS_thalgryn",
                       "_update_thalgryn_attack_anim"),
    "varkul":         ("bosses.level3", "_NS_varkul",
                       "_update_attack_anim"),
    "vhalzun":        ("bosses.level5", "_NS_vhalzun",
                       "_update_vhalzun_anim"),
    "vokrahn":        ("bosses.level4", "_NS_vokrahn",
                       "_update_attack_anim"),
    "xerathis":       ("bosses.level3", "_NS_xerathis",
                       "_update_attack_anim"),
    "zephyr":         ("heroes._bundle", "_NS_zephyr",
                       "_update_attack_anim"),
    "zharok":         ("bosses.level4", "_NS_zharok",
                       "_update_attack_anim"),
}

_POSE_CONTROLLER_CACHE = {}


def _pose_controller(hero_type):
    """Ambil controller pose sebuah hero (di-resolve sekali, lalu cache).

    Return ``None`` kalau hero tidak punya controller atau modulnya
    gagal dimuat -- pemanggil lalu tidak melakukan apa-apa.
    """
    if hero_type in _POSE_CONTROLLER_CACHE:
        return _POSE_CONTROLLER_CACHE[hero_type]
    fn = None
    spec = _POSE_CONTROLLER_SPECS.get(hero_type)
    if spec is not None:
        mod_name, ns_name, fn_name = spec
        try:
            import importlib
            ns = getattr(importlib.import_module(mod_name), ns_name, None)
            fn = getattr(ns, fn_name, None)
        except Exception:
            fn = None
    _POSE_CONTROLLER_CACHE[hero_type] = fn
    return fn


def _tick_pose_controller(hero_type, hero):
    """Majukan controller pose SEKALI per frame, di luar sprite cache.

    Aman dipanggil untuk hero tanpa controller (no-op).  Exception
    ditelan: pose yang gagal maju tidak boleh mematikan render hero.
    """
    fn = _pose_controller(hero_type)
    if fn is None:
        return
    try:
        fn(hero)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
# SPRITE PROBE
# Entity minimal + cache tinggi sprite, dipakai untuk
# normalisasi ukuran dan penempatan label (HP bar / nama).
# ═══════════════════════════════════════════════════════

_SPRITE_TOP_CACHE = {}

# Dipakai kalau pengukuran gagal (mis. pygame belum init).
_FALLBACK_TOP = 46


class _ProbeEntity:
    """Entity minimal untuk mengukur sprite."""

    def __init__(self, hero_type, x, y):
        self.hero_type = hero_type
        self.boss_type = hero_type
        self.boss_class = "mini"
        self.team = "blue"
        self.x = float(x)
        self.y = float(y)
        self.facing = 1
        self.direction = 1
        self.attack_timer = 0
        self.timer = 0
        self.pulse = 0.0
        self.anim_time = 0
        self.active_skill = None
        self.active_skill_timer = 0
        self.hp = 100
        self.max_hp = 100
        self.damage = 10
        self.base_damage = 10
        self.attack_cooldown = 45
        self.range = 100
        self.speed = 1.0
        self.radius = 16
        self.level = 1
        self.selected = False
        self.alive = True
        self.target = None
        self.color = (180, 60, 60)
        self.color_dark = (90, 30, 30)
        self.skill_damage = 10
        self.is_retreating = False


def get_sprite_top_offset(hero_type):
    """
    Berapa piksel sprite menjulang DI ATAS titik (x, y).

    Dipakai supaya HP bar / nama / bintang tidak menutupi kepala.
    Hasil di-cache per hero_type.
    """
    cached = _SPRITE_TOP_CACHE.get(hero_type)
    if cached is not None:
        return cached

    top = _FALLBACK_TOP
    try:
        size = 340
        cx = cy = size // 2
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        render_hero(hero_type, canvas, _ProbeEntity(hero_type, cx, cy),
                    cx, cy)
        rect = canvas.get_bounding_rect(min_alpha=10)
        if rect.height > 0:
            top = max(0, cy - rect.y)
    except Exception:
        top = _FALLBACK_TOP

    _SPRITE_TOP_CACHE[hero_type] = top
    return top


def clear_sprite_metrics_cache():
    """Panggil kalau renderer/scale berubah saat runtime."""
    _SPRITE_TOP_CACHE.clear()


# ═══ PENGATURAN UKURAN GLOBAL ═══
# Ubah SATU angka ini untuk memperbesar/mengecilkan SEMUA hero
# sekaligus (player maupun enemy, starter maupun boss-hero).
#   1.0  = ukuran normal
#   0.85 = 15% lebih kecil
#   1.2  = 20% lebih besar
#
# HD readability pass: sebelumnya 0.65 membuat badan 65 px turun lagi
# menjadi sekitar 42 px. Detail wajah, armor, dan senjata prosedural
# akhirnya hilang saat dilihat di layar 720p. 0.78 menjaga hero tetap
# kompak di lane, tetapi memberi sekitar 51 px badan agar detailnya
# terbaca tanpa mengubah collision radius atau gameplay.
HERO_GLOBAL_SCALE = 0.78

# Tinggi BADAN (kepala sampai kaki) semua hero, dalam piksel.
# Yang diukur hanya badan padat - efek tanah & aura tipis di atas
# kepala TIDAK ikut dihitung (lihat _measure_native_size).
HERO_TARGET_HEIGHT = 65

# Garis kaki saat pengukuran: piksel di bawah titik jangkar (x, y)
# dianggap efek tanah dan tidak dihitung sebagai badan.
_FEET_LINE = 16

# Ambang alpha untuk memisahkan BADAN PADAT dari aura/efek tipis
# (rage mist, flame aura, dll. biasanya alpha < 100; badan >= 200).
_BODY_ALPHA_THRESHOLD = 100

# Aspek lebar:tinggi referensi untuk target diagonal (hanya dipakai
# kalau HERO_SIZE_WIDTH_WEIGHT > 0).
_HERO_REF_ASPECT = 1.6

# Bobot lebar dalam normalisasi. 0.0 = murni tinggi (semua karakter
# setinggi HERO_TARGET_HEIGHT, lebar tetap proporsional) - dipakai
# supaya boss-hero bertubuh lebar (drakar, pyrenth) TIDAK dikecilkan
# berlebihan sampai lebih mungil dari starter hero.
HERO_SIZE_WIDTH_WEIGHT = 0.0

# Override manual per hero, kalau ada yang perlu perlakuan khusus.
# Isi dengan scale absolut, mis. {"gornak": 0.55}.
_HERO_SCALE_OVERRIDE = {}

# Fallback kalau pengukuran gagal.
_DEFAULT_HERO_SCALE = 0.65

# scale hasil pengukuran, per hero_type
_MEASURED_SCALE = {}


def set_hero_global_scale(value):
    """
    Ubah ukuran SEMUA hero saat runtime.

    Contoh: set_hero_global_scale(0.9) -> semua hero 10% lebih kecil.
    Cache sprite otomatis dibersihkan supaya perubahan langsung
    terlihat.
    """
    global HERO_GLOBAL_SCALE
    HERO_GLOBAL_SCALE = max(0.3, min(2.0, float(value)))
    _MEASURED_SCALE.clear()
    _SPRITE_TOP_CACHE.clear()
    clear_hero_sprite_cache()
    return HERO_GLOBAL_SCALE


def _measure_native_size(hero_type, renderer):
    """
    Ukur ukuran asli BADAN sprite (sebelum di-scale).

    Dua lapis:
    1) Piksel di bawah garis kaki (_FEET_LINE) dibuang (ground FX).
    2) Aura tipis di ATAS kepala (rage mist, flame, dll.) dibuang
       dengan mask alpha >= _BODY_ALPHA_THRESHOLD - kalau ikut
       dihitung, tinggi ter-inflasi dan boss-hero ter-scale terlalu
       kecil (keluhan: boss hero lebih mungil dari starter).

    Fallback ke ukuran clip lama kalau hasil mask terlalu kecil
    (boss "hantu" seperti xirthalis yang digambar alpha rendah).

    Return (width, height) atau None.
    """
    size = 360
    cx = cy = size // 2
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    probe = _ProbeEntity(hero_type, cx, cy)
    _adapt_hero_to_boss(probe)

    try:
        _call_renderer_on_canvas(renderer, canvas, probe, cx, cy)
    except Exception:
        return None

    full_rect = canvas.get_bounding_rect(min_alpha=10)

    # Buang efek tanah di bawah garis kaki
    body_line = cy + _FEET_LINE
    canvas.fill((0, 0, 0, 0), (0, body_line, size, size - body_line))
    clip_rect = canvas.get_bounding_rect(min_alpha=10)

    if clip_rect.height <= 0 or clip_rect.width <= 0:
        clip_rect = full_rect

    # ── Mask solid (buang aura tipis di atas kepala) ──
    mask = pygame.mask.from_surface(canvas, _BODY_ALPHA_THRESHOLD)
    rects = mask.get_bounding_rects()
    if rects:
        x0 = min(r.x for r in rects)
        y0 = min(r.y for r in rects)
        x1 = max(r.right for r in rects)
        y1 = max(r.bottom for r in rects)
        solid_rect = pygame.Rect(x0, y0, x1 - x0, y1 - y0)
    else:
        solid_rect = pygame.Rect(0, 0, 0, 0)

    # Pakai ukuran solid kalau masuk akal (kepala-ke-kaki 40-130 px),
    # kalau tidak fallback ke clip (boss "hantu" ber-alpha rendah
    # seperti vaerith/xirthalis mask-nya terlalu kecil).
    if 40 <= solid_rect.height <= 130 and \
            16 <= solid_rect.width <= 200:
        rect = solid_rect
    else:
        rect = clip_rect

    if rect.height <= 0 or rect.width <= 0:
        return None
    return rect.width, rect.height


def _get_hero_scale(hero_type):
    """
    Scale supaya "bobot visual" hero_type seragam.

    Diukur sekali per hero_type lalu di-cache, jadi hero/boss baru
    otomatis ternormalisasi tanpa tabel manual.
    """
    if hero_type in _HERO_SCALE_OVERRIDE:
        return _HERO_SCALE_OVERRIDE[hero_type] * HERO_GLOBAL_SCALE

    cached = _MEASURED_SCALE.get(hero_type)
    if cached is not None:
        return cached

    renderer = HERO_RENDERERS.get(hero_type) or \
        BOSS_RENDERERS.get(hero_type)

    scale = _DEFAULT_HERO_SCALE
    if renderer is not None:
        size = _measure_native_size(hero_type, renderer)
        if size:
            w, h = size
            # Ukuran efektif = campuran tinggi murni dan diagonal.
            # Hero lebar jadi ikut mengecil, bukan cuma yang tinggi.
            diag = math.hypot(w, h)
            target_diag = math.hypot(
                HERO_TARGET_HEIGHT, HERO_TARGET_HEIGHT * _HERO_REF_ASPECT)
            s_h = HERO_TARGET_HEIGHT / float(h)
            s_d = target_diag / diag
            wgt = max(0.0, min(1.0, HERO_SIZE_WIDTH_WEIGHT))
            scale = s_h * (1.0 - wgt) + s_d * wgt
            scale = max(0.40, min(1.70, scale))

    scale *= HERO_GLOBAL_SCALE
    _MEASURED_SCALE[hero_type] = scale
    return scale


# ═══════════════════════════════════════════════════════
# HERO SPRITE CACHE
#
# Sebelumnya SETIAP hero digambar ulang dari nol tiap frame
# (1.3 - 4.2 ms per hero). Dengan 6 hero itu 8-25 ms, padahal
# budget 60 FPS cuma 16.7 ms -> lag.
#
# Minion sudah punya cache (minions/base_renderer.py), hero belum.
# Di sini hero dapat cache yang sama konsepnya:
#   key = (type, team, level, facing, skill, fase animasi)
# Frame dengan key sama -> blit surface lama, tidak render ulang.
#
# Animasi TIDAK hilang: pulse/anim di-quantise ke beberapa fase,
# jadi tetap bergerak, hanya jumlah render unik yang dibatasi.
# ═══════════════════════════════════════════════════════

# Berapa fase animasi idle yang di-cache per kombinasi.
# Makin besar = animasi makin halus tapi cache makin banyak.
HERO_ANIM_PHASES = 12

# ═══ CACHE TERKUANTISASI UNTUK KOMBAT ═══
# Sebelumnya hero yang sedang menyerang/cast skill TIDAK di-cache
# sama sekali (render penuh tiap frame). Di wave 15+, hampir semua
# hero selalu bertarung -> 9 hero x ~1.3 ms = ~12 ms/frame (60%+ dari
# total draw) -> FPS ambruk.
# Sekarang animasi serang/skill IKUT di-cache dengan granularitas:
#   HERO_ATK_QUANT   = 2  -> fase serang baru tiap 2 frame (anim 30fps)
#   HERO_SKILL_QUANT = 2  -> fase skill baru tiap 2 frame
# Hasil: render penuh hanya saat fase berganti (setengah frekuensi),
# sisanya blit murah. Visual tetap terasa mulus karena fase 30fps.
HERO_ATK_QUANT = 2
HERO_SKILL_QUANT = 2

# Ukuran canvas cache (cukup untuk sprite terbesar + efek).
_HERO_CANVAS = 240

# ═══ CANVAS ADAPTIF UNTUK SERANGAN RANGED ═══
# Beam/proyektil boss ranged (Morgath, Ancient Apparition, dll.)
# menjulur sampai sejauh range serangan. Canvas 240 akan MEMOTONG
# beam di tepinya -> serangan terlihat "terpotong" tidak sampai
# target. Maka canvas diperbesar mengikuti range hero.
def _canvas_size_for(hero):
    """Ukuran canvas harus menjangkau target TERTJAUH di range serang.

    BUGFIX (orb acak / projectile terpotong): canvas hero di-blit
    dengan skala _render_scale, jadi 1 px canvas = _render_scale px
    dunia. Target berjarak ``range`` (dunia) berada di
    ``range / _render_scale`` px canvas dari pusat. Rumus lama
    ``2*(range+60)`` px canvas TIDAK cukup untuk hero yang
    menyusut banyak (mis. Zephyr scale 0.612: range 130 dunia butuh
    212 px canvas, padahal canvas cuma 190) -> proyektil renderer
    terpotong di tepi canvas & terlihat "melayang ke tempat random".
    Minimum canvas tetap 240 px (2 x max(120, ...)).
    """
    rng = int(getattr(hero, 'range', 50) or 50)
    try:
        scale = _get_hero_scale(getattr(hero, 'hero_type', '') or '') or 1.0
    except Exception:
        scale = 1.0
    half = max(120, int(rng / scale) + 40)
    return 2 * half

# Matikan kalau mau render langsung (debug).
HERO_CACHE_ENABLED = True

# ═══ LRU, BUKAN FIFO (v26) ═══
# Dulu dict biasa dan pembuangan memakai `pop(next(iter(...)))` =
# FIFO. Menyimpan ulang kunci yang sudah ada TIDAK memindahkannya ke
# belakang, jadi pose yang paling sering dipakai justru bisa terbuang
# lebih dulu. Terukur di HP: hit rate 77% dengan 600 entri penuh.
# OrderedDict + move_to_end memberi LRU sejati: ukuran cache sama,
# hit rate naik, tanpa perubahan tampilan sama sekali.
from collections import OrderedDict as _OD
_hero_sprite_cache = _OD()
_HERO_CACHE_MAX = 600
_hero_cache_stats = {'hits': 0, 'misses': 0}

# ═══ DUA CACHE TERPISAH: POSE BIASA vs POSE SKILL (v31) ═══
# Terukur (tools/bench_hero_cache.py, 10 hero + 120 minion, PC):
#
#     satu cache 600 entri : 10.00 ms/frame, hit 78.5%, 600 entri penuh
#     skill dipisah        :  5.38 ms/frame, hit 95.2%, 343 entri
#
# Penyebabnya: pose SKILL memonopoli cache. active_skill_timer
# berjalan 0..240 dan di-kuantisasi tiap 2 frame -> sampai 120 pose
# unik per hero per arah hadap. Sepuluh hero yang sedang cast
# menghasilkan 463 entri skill dari 600 slot, padahal pose itu hanya
# dipakai sekali lalu tidak pernah diminta lagi sampai cooldown
# berikutnya (240-900 frame kemudian) — jauh setelah ter-evict.
#
# Korbannya pose ATTACK, yang justru dipakai ulang terus-menerus
# (tiap 28-46 frame sekali serang). Begitu pose attack terbuang,
# frame berikutnya bayar cache-MISS 4.12 ms — LEBIH MAHAL daripada
# render langsung tanpa cache (3.07 ms). Jadi thrashing di sini
# bukan sekadar "tidak untung", tapi rugi bersih.
#
# Dengan cache terpisah, pose skill tidak pernah bisa mengusir pose
# attack. Granularitas animasi TIDAK diubah (tetap quant 2), jadi
# tampilan identik — yang berubah hanya siapa yang boleh menginap.
_hero_skill_cache = _OD()
_HERO_SKILL_CACHE_MAX = 320


def _cache_for(key):
    """Pilih cache sesuai jenis pose pada key.

    ``key[4]`` adalah state yang ditulis ``_hero_cache_key``:
    'skill' | 'atk' | 'idle'. Lihat komentar DI ATAS untuk alasan
    pemisahan ini.
    """
    if key[4] == 'skill':
        return _hero_skill_cache, _HERO_SKILL_CACHE_MAX
    return _hero_sprite_cache, _HERO_CACHE_MAX


def hero_cache_bytes():
    """Perkiraan pemakaian memori cache sprite hero, dalam MB."""
    total = 0
    for cache in (_hero_sprite_cache, _hero_skill_cache):
        for entry in cache.values():
            try:
                total += _sprite_pixels(entry) * 4
            except Exception:
                pass
    return total / (1024.0 * 1024.0)


def hero_cache_stats():
    """Statistik cache, berguna untuk cek efektivitas."""
    h = _hero_cache_stats['hits']
    m = _hero_cache_stats['misses']
    tot = h + m
    return {
        'entries': len(_hero_sprite_cache) + len(_hero_skill_cache),
        'hits': h,
        'misses': m,
        'hit_rate': f"{(h / tot * 100) if tot else 0:.1f}%",
    }


def clear_hero_sprite_cache():
    """Panggil saat ganti level / resolusi berubah."""
    _hero_sprite_cache.clear()
    _hero_skill_cache.clear()
    _hero_cache_stats['hits'] = 0
    _hero_cache_stats['misses'] = 0


# ═══ PARK RENDERER PROJECTILES SAAT CANVAS CACHE ═══
# Renderer boss/starter menyimpan FX di list bertanda `_` (mis.
# `_sy_projectiles`, `_aa_beams`, `_vk_chain_orbs`, `_gw_effects`,
# `_alch_patches`, `_zh_arrows`, `_pyr_chains`). Saat hero digambar
# ke canvas cache di pusat (c, c) — BUKAN koordinat dunia — list itu
# ikut di-update & di-blit, lalu sprite di-cache. Akibatnya orb/panah
# “acak” menempel di sekitar badan hero setiap cache hit.
# Gameplay pakai `hero.projectiles` (tanpa `_`) yang digambar di
# dunia oleh _entity.py; list itu JANGAN di-park.
# Suffix sengaja dibuat lengkap: FX renderer menggunakan berbagai
# akhiran (effects/patches/coins/arrows/skulls/arcs/chains/bursts/eclipse
# beams/trail_samples/projs), bukan cuma projectiles/beams/shards.
_RENDERER_FX_SUFFIXES = (
    "_projectiles",
    "_chain_orbs",
    "_beams",
    "_shards",
    "_effects",
    "_patches",
    "_coins",
    "_arrows",
    "_skulls",
    "_arcs",
    "_chains",
    "_bursts",
    "_eclipse_beams",
    "_trail_samples",
    "_projs",
)


def _park_renderer_fx(entity):
    """Kosongkan list FX renderer selama gambar ke canvas cache.

    Return dict atribut yang di-park (untuk restore). Aman untuk
    objek tanpa __dict__ (no-op).
    """
    parked = {}
    try:
        items = list(vars(entity).items())
    except TypeError:
        entity._skip_renderer_projectiles = True
        return parked
    for name, val in items:
        if not name.startswith("_"):
            continue
        if not isinstance(val, list):
            continue
        if any(name.endswith(s) for s in _RENDERER_FX_SUFFIXES):
            parked[name] = val
            setattr(entity, name, [])
    entity._skip_renderer_projectiles = True
    return parked


def _restore_renderer_fx(entity, parked):
    for name, val in parked.items():
        setattr(entity, name, val)
    entity._skip_renderer_projectiles = False


def _boss_has_renderer_fx(boss):
    """Ada proyektil/FX renderer yang sedang aktif di objek ini?"""
    try:
        items = vars(boss).items()
    except TypeError:
        return False
    for name, val in items:
        if not name.startswith("_") or not isinstance(val, list):
            continue
        if val and any(name.endswith(sfx)
                       for sfx in _RENDERER_FX_SUFFIXES):
            return True
    return False


def _boss_fx_parkable(boss_type):
    """Bolehkah FX proyektil renderer di-park untuk tipe ini?

    Park hanya benar kalau ada lapisan HIDUP yang menggambarnya ulang
    tiap frame (lihat _BOSS_LIVE_STEP_SPECS / _BOSS_LIVE_DRAW_SPECS).
    Untuk tipe lain proyektil renderer adalah bagian dari gambar: kalau
    di-park, FX serangan itu HILANG dari layar (regresi visual nyata,
    mis. krobellus/atk) karena tidak ada yang menggantikannya.
    """
    return (boss_type in _BOSS_LIVE_STEP_SPECS
            or boss_type in _BOSS_LIVE_DRAW_SPECS)


def _call_renderer_on_canvas(renderer, canvas, entity, x, y):
    """Panggil renderer ke canvas cache tanpa FX projectile renderer."""
    parked = _park_renderer_fx(entity)
    try:
        return renderer(canvas, entity, x, y)
    finally:
        _restore_renderer_fx(entity, parked)


def _hero_cache_key(hero_type, hero):
    """
    Key cache. Hero dengan key sama = gambar identik.

    State yang MENGUBAH gambar harus masuk key. State yang tidak
    (posisi, hp) tidak perlu.

    Animasi serang & skill di-cache TERKUANTISASI (tiap 2 frame)
    supaya hero yang selalu bertarung tidak lagi render penuh
    tiap frame.
    """
    timer = int(getattr(hero, 'attack_timer', 0) or 0)
    skill = getattr(hero, 'active_skill', None)
    skill_t = int(getattr(hero, 'active_skill_timer', 0) or 0)
    level = int(getattr(hero, 'level', 1) or 1)
    facing = 1 if getattr(hero, 'facing', 1) >= 0 else -1
    team = getattr(hero, 'team', 'blue')

    # Di perangkat lambat, kuantisasi digandakan: pose diperbarui
    # lebih jarang -> hit rate naik, render penuh jauh berkurang.
    try:
        from mobile.perf import Quality as _Qk
        _q = 1 if _Qk.cheap_alpha else 2
    except Exception:
        _q = 1

    if skill:
        return (hero_type, team, level, facing, 'skill', skill,
                skill_t // (_skill_quant() * _q))
    if timer > 0:
        # _pose_variant: varian pose yang dipilih renderer sendiri
        # (mis. Sylara memilih sapuan melee vs tembakan tergantung jarak
        # target).  Tanpa ini, dua pose berbeda memakai key yang sama
        # dan cache menyajikan sprite basi.
        return (hero_type, team, level, facing, 'atk',
                timer // (HERO_ATK_QUANT * _q),
                int(getattr(hero, '_pose_variant', 0) or 0))

    phase = int(getattr(hero, 'pulse', 0.0) * 2.0) % HERO_ANIM_PHASES
    return (hero_type, team, level, facing, 'idle', phase,
            bool(getattr(hero, '_moving_cached', False)))


def _render_hero_raw(hero_type, surface, hero, x, y):
    """Render hero tanpa cache (jalur lama)."""
    renderer = HERO_RENDERERS.get(hero_type)
    if renderer:
        _adapt_hero_to_boss(hero)
        scale = _get_hero_scale(hero_type)

        if abs(scale - 1.0) < 0.02:
            hero._render_scale = 1.0
            renderer(surface, hero, x, y)
            return True

        canvas_w = _canvas_size_for(hero)
        canvas = pygame.Surface((canvas_w, canvas_w), pygame.SRCALPHA)
        c = canvas_w // 2
        hero._render_scale = scale
        _call_renderer_on_canvas(renderer, canvas, hero, c, c)
        _blit_scaled(surface, canvas, c, c, scale, x, y,
                     getattr(hero, 'team', 'blue'))
        return True

    boss_renderer = BOSS_RENDERERS.get(hero_type)
    if boss_renderer:
        _adapt_hero_to_boss(hero)
        scale = _get_hero_scale(hero_type)

        if abs(scale - 1.0) < 0.02:
            hero._render_scale = 1.0
            boss_renderer(surface, hero, x, y)
            return True

        canvas_w = _canvas_size_for(hero)
        canvas = pygame.Surface((canvas_w, canvas_w), pygame.SRCALPHA)
        c = canvas_w // 2

        # ═══ TWO-PASS BEAM RENDER ═══
        # Boss-hero tertentu (mis. morgath) menggambar beam serangan
        # TERPISAH langsung di layar pada skala 1.0, supaya beam
        # tampil PERSIS seperti versi mini boss (tidak mengecil /
        # diredupkan oleh smoothscale). Body & FX lain tetap
        # di-scale normal seperti hero lain.
        if hero_type in _BEAM_PASS_HEROES:
            hero._render_scale = scale
            hero._skip_beam = True
            try:
                _call_renderer_on_canvas(boss_renderer, canvas, hero, c, c)
            finally:
                hero._skip_beam = False
            _blit_scaled(surface, canvas, c, c, scale, x, y,
                     getattr(hero, 'team', 'blue'))

            # Offset target terkunci tersimpan dalam ruang DUNIA
            # (bosses/level1.py) - beam pass di layar memakainya
            # apa adanya pada skala 1.0, jadi tanpa konversi.
            saved_scale = getattr(hero, "_render_scale", 1.0)
            hero._render_scale = 1.0
            hero._beam_pass_only = True
            try:
                boss_renderer(surface, hero, x, y)
            finally:
                hero._beam_pass_only = False
                hero._render_scale = saved_scale
            return True

        hero._render_scale = scale
        _call_renderer_on_canvas(boss_renderer, canvas, hero, c, c)
        _blit_scaled(surface, canvas, c, c, scale, x, y,
                     getattr(hero, 'team', 'blue'))
        return True

    return False


# ═══════════════════════════════════════════════════════
# HD EDGE PASS
#
# Renderer prosedural menggambar pada resolusi asli (umumnya 90-130 px)
# lalu sprite diperkecil ke ukuran arena. Smoothscale memberi anti-alias
# yang bagus, tetapi juga melembutkan outline gelap hingga menyatu dengan
# map. Pass murah ini dijalankan HANYA saat cache miss: bentuk solid
# (alpha >= 180, jadi aura/transparansi tidak ikut) diberi outline 1 px
# setelah resize. Hasil akhirnya tetap procedural, tajam, dan cache hit
# berikutnya tetap hanya satu blit.
# ═══════════════════════════════════════════════════════
HD_HERO_EDGE_ENABLED = True
_HD_EDGE_ALPHA = 180

# Pass cahaya (rim light + terminator) - lihat lighting.py. Dijalankan di
# tempat yang sama seperti outline HD, yaitu HANYA saat cache miss dan di
# atas sprite HASIL resize, sehingga rim-nya benar-benar 1 px pada resolusi
# layar. Karena ditaruh di satu choke point ini, keenam hero masterwork dan
# Gornak ikut terpenuhi tanpa satu pun renderer diubah.
HD_LIGHTING_ENABLED = True
_HD_RIM_ADD = (34, 30, 48)          # tim biru: rim dingin-netral
_HD_SHADE_MUL = 162
_HD_RIM_ADD_RED = (48, 26, 22)      # tim merah: rim lebih hangat
_HD_SHADE_MUL_RED = 158


def _finish_hd_sprite(sprite, team='blue'):
    """Cahaya + outline pasca-scale tanpa mengubah isi/ukuran badan.

    Urutan penting: LIGHTING dulu, outline belakangan. Kalau dibalik, rim
    1 px muncul persis di piksel yang lalu ditimpa outline gelap, sehingga
    hasilnya nol (ini terjadi pada percobaan pertama).

    Return ``(surface, pad)``. ``pad`` dipakai untuk mengoreksi anchor
    karena canvas hasil dibuat satu piksel lebih lebar di setiap sisi.
    """
    if not HD_HERO_EDGE_ENABLED or sprite.get_width() <= 1 or \
            sprite.get_height() <= 1:
        return sprite, 0

    try:
        solid = pygame.mask.from_surface(sprite, _HD_EDGE_ALPHA)
        if solid.count() == 0:
            return sprite, 0

        if HD_LIGHTING_ENABLED and _lighting is not None:
            red = team == 'red'
            _lighting.apply_to_rig(
                sprite,
                rim_add=_HD_RIM_ADD_RED if red else _HD_RIM_ADD,
                shade_mul=_HD_SHADE_MUL_RED if red else _HD_SHADE_MUL)

        w, h = sprite.get_size()
        expanded = pygame.mask.Mask((w + 2, h + 2))
        for ox, oy in ((0, 0), (1, 0), (2, 0),
                       (0, 1),         (2, 1),
                       (0, 2), (1, 2), (2, 2)):
            expanded.draw(solid, (ox, oy))

        core = pygame.mask.Mask((w + 2, h + 2))
        core.draw(solid, (1, 1))
        expanded.erase(core, (0, 0))

        # Sedikit bias warna tim: tetap hampir hitam agar tidak
        # mengubah desain hero, tetapi siluet biru/merah lebih mudah
        # dibaca saat dua tim bertumpuk.
        edge = (7, 22, 34, 235) if team != 'red' else (38, 8, 13, 235)
        result = expanded.to_surface(
            setcolor=edge, unsetcolor=(0, 0, 0, 0))
        result.blit(sprite, (1, 1))
        return result, 1
    except (pygame.error, ValueError):
        # Renderer tidak boleh gagal hanya karena backend SDL tertentu
        # tidak mendukung operasi mask/to_surface.
        return sprite, 0


def _blit_scaled(surface, canvas, cx, cy, scale, x, y, team='blue'):
    """
    Scale canvas lalu blit sehingga titik (cx, cy) di canvas
    mendarat tepat di (x, y) pada surface.

    Hanya area terpakai yang di-scale (bukan seluruh 240x240),
    jadi jauh lebih murah dari versi lama.
    """
    rect = canvas.get_bounding_rect(min_alpha=8)
    if rect.width <= 0 or rect.height <= 0:
        return

    sub = canvas.subsurface(rect)
    nw = max(1, int(rect.width * scale))
    nh = max(1, int(rect.height * scale))
    scaled = pygame.transform.smoothscale(sub, (nw, nh))
    scaled, edge_pad = _finish_hd_sprite(scaled, team)

    # Offset anchor relatif terhadap titik tengah. HD edge menambah
    # padding, jadi kurangi lagi agar anchor dunia tidak bergeser 1 px.
    off_x = (rect.x - cx) * scale - edge_pad
    off_y = (rect.y - cy) * scale - edge_pad
    surface.blit(scaled, (int(x + off_x), int(y + off_y)))


def render_hero(hero_type, surface, hero, x, y):
    """
    Render hero berdasarkan hero_type.

    Pakai sprite cache TERKUANTISASI: idle/walk/serang/skill semua
    di-cache (fase baru tiap N frame), jadi hero yang selalu
    bertarung tidak lagi render penuh tiap frame.

    Args:
        hero_type: string hero type (e.g. 'kaizen', 'ignis_drachorn')
        surface: pygame surface untuk draw
        hero: Hero object
        x, y: position
    """
    if not HERO_CACHE_ENABLED:
        # Tanpa cache renderer jalan tiap frame, jadi renderer sendiri
        # yang memajukan controller pose.
        _live_fx_pre(hero_type, surface, hero, x, y)
        if not _render_hero_raw(hero_type, surface, hero, x, y):
            _draw_generic_hero(surface, hero, x, y)
        _live_fx_post(hero_type, surface, hero, x, y)
        return

    key = _hero_cache_key(hero_type, hero)
    # Pose skill dan pose biasa punya cache sendiri (lihat _cache_for).
    cache, cache_max = _cache_for(key)
    entry = cache.get(key)

    # Controller pose harus maju SETIAP frame.  Pada frame cache-MISS
    # renderer yang menjalankannya (dia dipanggil di bawah); pada frame
    # cache-HIT renderer dilewati, jadi kita yang menjalankan di sini.
    # Dengan begitu controller maju tepat sekali per frame tanpa perlu
    # mengubah renderer mana pun.  Lihat CONTROLLER POSE PER-FRAME.
    if entry is not None:
        _tick_pose_controller(hero_type, hero)

    # Lapisan FX hidup (ground) HARUS di bawah sprite -> digambar dulu.
    _live_fx_pre(hero_type, surface, hero, x, y)

    if entry is not None:
        _hero_cache_stats['hits'] += 1
        sprite, ax, ay = entry[0], entry[1], entry[2]
        uses = entry[3] if len(entry) > 3 else 1

        # Konversi colorkey ditunda sampai pose terbukti dipakai ulang
        # (konversi = 1 operasi per-piksel, ~3,6 ms untuk sprite hero
        # di HP uji). Ada juga anggaran per frame.
        if uses == 1:
            try:
                from mobile.perf import (Quality as _Qh, can_convert,
                                         to_colorkey_sprite)
                # v23: hanya kalau alpha memang tak terjangkau.
                # Jalur cepat SDL membuat konversi ini merugikan -
                # menghemat 0,29 ms per hero tapi merusak tepi sprite.
                if _Qh.use_colorkey_sprites and can_convert():
                    sprite = to_colorkey_sprite(sprite)
            except Exception:
                pass
        cache[key] = (sprite, ax, ay, uses + 1)
        cache.move_to_end(key)      # LRU: tandai baru dipakai

        surface.blit(sprite, (int(x - ax), int(y - ay)))
    else:
        # Cache miss -> render ke canvas sendiri, simpan
        _hero_cache_stats['misses'] += 1
        canvas_w = _canvas_size_for(hero)
        canvas = pygame.Surface((canvas_w, canvas_w), pygame.SRCALPHA)
        c = canvas_w // 2

        renderer = HERO_RENDERERS.get(hero_type) or \
            BOSS_RENDERERS.get(hero_type)

        if renderer is None:
            _draw_generic_hero(surface, hero, x, y)
        else:
            _adapt_hero_to_boss(hero)
            try:
                hero._render_scale = _get_hero_scale(hero_type)
                # Beam-pass hero: beam TIDAK ikut di-cache -
                # digambar live (pixel-perfect seperti mini boss).
                hero._skip_beam = hero_type in _BEAM_PASS_HEROES
                _call_renderer_on_canvas(renderer, canvas, hero, c, c)
            except Exception:
                _draw_generic_hero(surface, hero, x, y)
            finally:
                hero._skip_beam = False

            rect = canvas.get_bounding_rect(min_alpha=8)
            if rect.width <= 0 or rect.height <= 0:
                _live_fx_post(hero_type, surface, hero, x, y)
                return

            scale = _get_hero_scale(hero_type)
            sub = canvas.subsurface(rect).copy()
            if abs(scale - 1.0) >= 0.02:
                nw = max(1, int(rect.width * scale))
                nh = max(1, int(rect.height * scale))
                sub = pygame.transform.smoothscale(sub, (nw, nh))

            # Outline dibuat SETELAH smoothscale agar tepinya benar-benar
            # 1 px tajam pada resolusi layar, bukan ikut diredupkan resize.
            sub, edge_pad = _finish_hd_sprite(
                sub, getattr(hero, 'team', 'blue'))

            # anchor = posisi titik (c, c) di dalam sprite hasil.
            # Tambahkan padding edge supaya posisi kaki tidak bergeser.
            ax = (c - rect.x) * scale + edge_pad
            ay = (c - rect.y) * scale + edge_pad

            if len(cache) >= cache_max:
                cache.pop(next(iter(cache)))

            # Simpan apa adanya dulu; konversi colorkey menyusul pada
            # pemakaian kedua (lihat jalur "hit" di atas).
            cache[key] = (sub, ax, ay, 1)
            surface.blit(sub, (int(x - ax), int(y - ay)))

    # ═══ BEAM PASS LIVE (hero ranged seperti morgath) ═══
    # Beam digambar langsung ke layar skala 1.0 setiap frame ->
    # tetap pixel-perfect dengan mini boss dan mulus 60fps, sementara
    # body tetap murah (blit sprite cache).
    if hero_type in _BEAM_PASS_HEROES:
        boss_renderer = BOSS_RENDERERS.get(hero_type)
        if boss_renderer is not None:
            saved_scale = getattr(hero, '_render_scale', 1.0)
            try:
                hero._render_scale = 1.0
                hero._beam_pass_only = True
                boss_renderer(surface, hero, x, y)
            except Exception:
                pass
            finally:
                hero._beam_pass_only = False
                hero._render_scale = saved_scale

    # ═══ LIVE FX PASS (Zephyr) ═══
    # Trail ayunan, projectile, partikel, dan impact digambar setelah
    # sprite supaya berada di depan badan - dan di luar cache supaya
    # tetap bergerak 60 fps walau pose sprite sedang dipakai ulang.
    _live_fx_post(hero_type, surface, hero, x, y)


# ═══════════════════════════════════════════════════════
# CACHE SPRITE BOSS — PARITAS MINI BOSS / TRUE BOSS DENGAN HERO
# ═══════════════════════════════════════════════════════
#
# MASALAH (terukur — tools/bench_boss_vs_hero.py, pygame-ce 2.5.8, PC):
#
#   Karakter yang SAMA persis (rig, renderer, palette) punya dua jalur
#   gambar yang berbeda:
#
#     jadi HERO unlock -> heroes.render_hero()
#                         badan dirender ke canvas HANYA saat pose
#                         berganti (kunci terkuantisasi), frame lainnya
#                         satu blit murah          = 0,66-0,74 ms/frame
#     jadi MINI/TRUE BOSS -> Boss.draw() -> draw_<boss>()
#                         renderer prosedural dipanggil LANGSUNG ke
#                         layar SETIAP frame        = 1,9-7,0 ms/frame
#                                                   (median 2,2 ms dari
#                                                    216 boss)
#
#   Jadi boss 3-5x lebih mahal daripada versi hero-nya. Di HP (CPU 3-5x
#   lebih lambat dari PC) satu boss memakan 7-35 ms dari budget 16,7 ms
#   -> FPS jatuh, dan yang paling terlihat justru boss itu sendiri:
#   gerakannya patah-patah dan animasinya tidak selancar versi hero.
#   Ukur adegan penuh (tools/bench_boss_vs_hero.py --scene):
#     level 1 + BOSS gornak  : 5,95 ms/frame
#     level 1 + HERO gornak  : 2,77 ms/frame   (2,15x lebih ringan)
#
# SOLUSI: boss memakai pipeline cache yang SAMA dengan hero, pada skala
# NATIF boss (1.0 — ukuran & tampilan boss tidak berubah):
#   * badan dirender ke canvas hanya saat kunci pose berganti,
#   * lapisan FX hidup (heroes/*_fx.py) TETAP digambar setiap frame di
#     luar cache (ground sebelum sprite, live sesudahnya) -> 60 fps,
#   * controller pose dimajukan SEKALI per frame walau cache hit, jadi
#     animasi serangan tidak pernah membeku (pola yang sama dengan
#     _tick_pose_controller di jalur hero),
#   * beam morgath & proyektil canvas drakar tetap hidup per frame.
#
# Kunci cache memakai state BOSS (timer/direction/boss_class/...), bukan
# state hero (attack_timer/facing/level) — lihat _boss_cache_key.
#
# Matikan untuk membandingkan: MYSTIC_BOSS_CACHE=0 python main.py
# ═══════════════════════════════════════════════════════

BOSS_CACHE_ENABLED = _os.environ.get("MYSTIC_BOSS_CACHE", "1") != "0"

# Granularitas pose idle disamakan dengan hero supaya dua jalur terasa
# sama. Untuk pose SERANGAN & SKILL berlaku aturan global:
#   * tipe DENGAN lapisan FX hidup (_LIVE_FX_HEROES): FX-nya sudah jalan
#     60 fps di luar cache, jadi badan cukup terkuantisasi seperti hero
#     (2 frame) — paritas penuh dengan versi hero unlock-nya.
#   * tipe TANPA lapisan FX hidup (±185 dari 216 boss): ayunan senjata,
#     proyektil, dan FX skill digambar DI DALAM render badan. Kalau
#     badan diquantisasi 2 frame, seluruh FX itu bergerak 30 fps sementara
#     hero starter/unlock 60 fps — inilah "swing/projectile/skill FX boss
#     tidak sefluid hero". Maka pose serang/skill mereka maju 1 frame
#     (60 fps). Dampak cache terbatas: kunci tetap dipakai ulang pada
#     serangan/cast berikutnya, dan governor biaya (render_boss) tetap
#     mengembalikan renderer ringan ke jalur langsung bila cache tidak
#     menguntungkan.
BOSS_ANIM_PHASES = HERO_ANIM_PHASES
BOSS_ATK_QUANT = HERO_ATK_QUANT
BOSS_SKILL_QUANT = HERO_SKILL_QUANT
BOSS_FX_FRAME_QUANT = 1     # pose swing/skill per frame (60 fps)

_boss_sprite_cache = _OD()
_BOSS_CACHE_MAX = 200
# Anggaran total piksel sprite (Android: 4 byte/px). 8 juta px ~= 32 MB
# batas atas; evict LRU jalan begitu salah satu anggaran terlampaui.
_BOSS_CACHE_PIXEL_BUDGET = 8 * 1000 * 1000
_boss_cache_pixels = [0]
_boss_cache_stats = {"hits": 0, "misses": 0, "fallback": 0,
                     "grow": 0, "unsafe": 0, "nocache": 0,
                     "probefail": 0, "uncache": 0}

# Canvas boss harus memuat badan + FX canvas (aura/rune/telegraph dekat
# badan). Pengukuran tools/_diag_boss_bbox.py:
#   idle/walk/attack  p50=85  p90=99  p99=279 px (setengah ukuran)
#   skill             p50=160 p90=357 max 552 px
# Canvas mulai kecil (hemat memori & murah di-blit) dan MEMBESAR otomatis
# kalau konten menyentuh tepinya. Kalau sudah mentok di batas atas, pose
# itu ditandai TIDAK AMAN di-cache dan digambar langsung ke layar seperti
# sebelumnya (FX jauh tidak boleh terpotong tepi canvas).
BOSS_CANVAS_MIN_HALF = 150
BOSS_CANVAS_MAX_HALF = 460
# Sprite lebih besar dari ini tidak di-cache: blit-nya sudah tidak lebih
# murah daripada menggambar langsung (dan memakan memori besar di HP).
BOSS_SPRITE_MAX_SIDE = 900
# Rect crop disimpan PER (TIPE, POSE) dan tidak dihitung ulang tiap miss:
#   * get_bounding_rect() itu mahal (0,30 ms di canvas 300px, 1,58 ms di
#     640px) — dulu dipanggil setiap cache miss,
#   * rect tetap = anchor tetap = tidak ada pergeseran 1 px antar pose,
#   * per pose (bukan per tipe) supaya skill yang melebar tidak membuat
#     sprite idle/walk ikut besar.
# Deteksi "konten keluar rect" memakai 4 strip 2 px (0,02 ms), dan rect
# hanya dihitung ulang saat strip itu benar-benar kena tinta.
BOSS_CROP_MARGIN = 24
_BOSS_GEOM = {}
_BOSS_UNSAFE = set()

# Boss yang proyektil/beam-nya milik renderer (bukan modul FX hidup) dan
# HARUS tetap bergerak 60 fps di luar cache sprite.
#   drakar  : _drk_projs (gelombang tebasan, chip, ember) — di-step dan
#             digambar sendiri tiap frame; saat canvas render list ini
#             di-park supaya tidak terpanggang beku.
#   morgath : beam serangan (lihat _BEAM_PASS_HEROES) — digambar live di
#             layar pada skala 1.0.
_BOSS_LIVE_STEP_SPECS = {
    "drakar": ("bosses.level1", "_NS_drakar", "_drk_step_projectiles"),
}
_BOSS_LIVE_DRAW_SPECS = {
    "drakar": ("bosses.level1", "_NS_drakar", "_drk_draw_projectiles"),
}
_BOSS_LIVE_STEP_FN = {}
_BOSS_LIVE_DRAW_FN = {}


def boss_cache_stats():
    """Statistik cache sprite boss (debug overlay / alat uji)."""
    h = _boss_cache_stats["hits"]
    m = _boss_cache_stats["misses"]
    tot = h + m
    return {
        "entries": len(_boss_sprite_cache),
        "hits": h,
        "misses": m,
        "hit_rate": f"{(h / tot * 100) if tot else 0:.1f}%",
        "fallback": _boss_cache_stats["fallback"],
        "grow": _boss_cache_stats["grow"],
        "unsafe": _boss_cache_stats["unsafe"],
        "nocache": _boss_cache_stats["nocache"],
        "enabled": BOSS_CACHE_ENABLED,
    }


def boss_cache_bytes():
    """Perkiraan memori cache sprite boss, dalam MB."""
    total = 0
    for entry in _boss_sprite_cache.values():
        try:
            surf = entry[0]
            total += surf.get_width() * surf.get_height() * 4
        except Exception:
            pass
    return total / (1024.0 * 1024.0)


def clear_boss_sprite_cache():
    """Panggil saat ganti level / resolusi berubah (paritas hero)."""
    _boss_sprite_cache.clear()
    _BOSS_GEOM.clear()
    _BOSS_UNSAFE.clear()
    _BOSS_PROBE_FAIL.clear()
    _BOSS_PROBE_TRY.clear()
    _BOSS_PROBE_ERRORS.clear()
    _BOSS_KIND_HM.clear()
    _BOSS_MISS_MS.clear()
    _BOSS_DIRECT_DRIFT.clear()
    _boss_cache_pixels[0] = 0
    _boss_cache_stats["hits"] = 0
    _boss_cache_stats["misses"] = 0
    _boss_cache_stats["fallback"] = 0
    _boss_cache_stats["grow"] = 0
    _boss_cache_stats["unsafe"] = 0
    _boss_cache_stats["nocache"] = 0


def _boss_cache_key(boss_type, boss):
    """Kunci cache sprite boss. State yang mengubah gambar harus masuk.

    Paritas dengan ``_hero_cache_key``, tapi membaca atribut BOSS:
      * ``timer``            (hero: attack_timer)
      * ``direction``        (hero: facing)
      * ``boss_class``       (true boss punya rig/aura berbeda)
      * ``hurt_flash_timer`` diquantisasi 2 frame — flash putih harus
        tetap terlihat sebagai feedback damage, tapi tidak boleh
        membuat cache miss setiap frame.
    Posisi & HP tidak masuk kunci (tidak mengubah gambar).
    """
    try:
        from mobile.perf import Quality as _Qb
        _q = 1 if _Qb.cheap_alpha else 2
    except Exception:
        _q = 1

    # Kuantisasi pose serang/skill (lihat BOSS_FX_FRAME_QUANT): tipe
    # tanpa lapisan FX hidup memajukan swing/proyektil/skill FX per
    # frame seperti FX hidup hero; tipe berlapisan hidup tetap pada
    # kuantisasi hero (FX-nya sudah 60 fps di luar cache).
    if boss_type in _LIVE_FX_HEROES:
        _q_atk = BOSS_ATK_QUANT * _q
        _q_skill = BOSS_SKILL_QUANT * _q
    else:
        _q_atk = BOSS_FX_FRAME_QUANT * _q
        _q_skill = BOSS_FX_FRAME_QUANT * _q

    timer = int(getattr(boss, "timer", 0) or 0)
    skill = getattr(boss, "active_skill", None)
    skill_t = int(getattr(boss, "active_skill_timer", 0) or 0)
    facing = 1 if int(getattr(boss, "direction", -1) or -1) >= 0 else -1
    klass = getattr(boss, "boss_class", "mini")
    team = getattr(boss, "team", "red")
    hurt = min(4, int(getattr(boss, "hurt_flash_timer", 0) or 0) // 2)
    rage = 1 if (getattr(boss, "is_enraged", False)
                 or getattr(boss, "rage_active", False)) else 0
    ability = 1 if getattr(boss, "ability_active", False) else 0
    alive = 1 if getattr(boss, "alive", True) else 0
    moving = bool(getattr(boss, "_moving_cached", False))

    head = (boss_type, "B", klass, team, facing, hurt, rage, alive)

    # Proyektil milik renderer yang TIDAK punya lapisan hidup pengganti
    # harus digambar jalur langsung (lihat render_boss): kalau masuk
    # sprite, proyektil yang terbang jauh dari badan akan terpotong crop
    # dan hilang dari layar.
    proj = 1 if (not _boss_fx_parkable(boss_type)
                 and _boss_has_renderer_fx(boss)) else 0
    # Fase jam dinding TIDAK masuk kunci: memasukkannya membuat tipe
    # ber-jam dinding (gornak dkk.) miss tiap frame dan justru lebih
    # lambat daripada tanpa cache (terukur di smoke test). Membekukan
    # animasi dinding seumur jendela pose adalah perilaku kuantisasi
    # yang sama dengan pose hero, dan perbandingan visual
    # tools/_diag_boss_pixel_parity.py memakai jam virtual per shot
    # sehingga kedua jalur tetap dibandingkan pada fase yang sama.
    if skill:
        return head + ("skill", skill,
                       skill_t // _q_skill, ability, proj)
    if timer > 0:
        return head + ("atk", timer // _q_atk, ability, proj)
    phase = int(getattr(boss, "pulse", 0.0) * 2.0) % BOSS_ANIM_PHASES
    return head + ("idle", phase, moving, ability, proj)


def _boss_namespace(boss_type):
    """Cari kelas namespace ``_NS_<boss>`` milik renderer sebuah boss.

    Return ``None`` kalau tidak ketemu (pemanggil lalu tidak melakukan
    apa-apa). Hasil di-cache di ``_BOSS_NS_CACHE``.
    """
    if boss_type in _BOSS_NS_CACHE:
        return _BOSS_NS_CACHE[boss_type]
    ns = None
    try:
        import importlib
        from bosses._boss_index import BOSS_INDEX
        entry = BOSS_INDEX.get(boss_type)
        if entry:
            module = importlib.import_module("bosses." + entry[0])
            ns = getattr(module, "_NS_" + boss_type, None)
            if ns is None:
                # Nama namespace tidak selalu sama dengan nama boss
                # (mis. bundle level yang menamai ulang). Cari kelas
                # _NS_* yang benar-benar punya fungsi draw boss ini.
                draw_name = entry[1]
                for name in dir(module):
                    if not name.startswith("_NS_"):
                        continue
                    cand = getattr(module, name, None)
                    if callable(getattr(cand, draw_name, None)):
                        ns = cand
                        break
    except Exception:
        ns = None
    _BOSS_NS_CACHE[boss_type] = ns
    return ns


_BOSS_NS_CACHE = {}
_BOSS_POSE_TICK_CACHE = {}


def _boss_pose_tick(boss_type):
    """Controller pose sebuah boss (di-resolve sekali, lalu di-cache).

    Urutan pilihan:
      1. tabel ``_POSE_CONTROLLER_SPECS`` (sudah diaudit untuk jalur
         hero — tools/test_hero_pose_cache.py),
      2. ``_update_attack_anim`` di namespace boss (konvensi umum;
         untuk 7 boss yang punya dua fungsi ``_update_*_anim``, nama
         ini adalah alias yang mendelegasikan ke controller asli),
      3. satu-satunya ``_update_*_anim`` yang ada.

    Hanya SATU fungsi yang dipanggil supaya state tidak maju dua kali
    dalam satu frame.
    """
    if boss_type in _BOSS_POSE_TICK_CACHE:
        return _BOSS_POSE_TICK_CACHE[boss_type]
    fn = _pose_controller(boss_type)
    if fn is None:
        ns = _boss_namespace(boss_type)
        if ns is not None:
            cand = getattr(ns, "_update_attack_anim", None)
            if not callable(cand):
                alts = sorted(
                    n for n in dir(ns)
                    if n.startswith("_update_") and n.endswith("_anim")
                    and callable(getattr(ns, n, None)))
                cand = getattr(ns, alts[0]) if len(alts) == 1 else None
            fn = cand if callable(cand) else None
    _BOSS_POSE_TICK_CACHE[boss_type] = fn
    return fn


def _tick_boss_pose(boss_type, boss):
    """Majukan controller pose boss SEKALI per frame (juga saat cache hit).

    Tanpa ini, renderer yang memutar state animasi di dalam fungsi
    draw-nya (215 dari 216 boss punya ``_update_*_anim``) akan membeku
    di frame cache-hit — persis bug "Gorath mengayun sekali lalu tidak
    pernah mengayun lagi" yang sudah diperbaiki di jalur hero.
    """
    fn = _boss_pose_tick(boss_type)
    if fn is None:
        return
    try:
        fn(boss)
    except Exception:
        pass


def _boss_live_hook(cache, specs, boss_type):
    """Resolve satu hook FX hidup milik renderer (lazy + cache)."""
    if boss_type in cache:
        return cache[boss_type]
    fn = None
    spec = specs.get(boss_type)
    if spec is not None:
        try:
            import importlib
            mod_name, ns_name, fn_name = spec
            ns = getattr(importlib.import_module(mod_name), ns_name, None)
            cand = getattr(ns, fn_name, None)
            fn = cand if callable(cand) else None
        except Exception:
            fn = None
    cache[boss_type] = fn
    return fn


def _boss_live_step(boss_type, boss):
    """Step FX milik renderer yang harus maju SETIAP frame.

    Dipanggil sebelum render/blit. Pada frame cache-MISS renderer ikut
    memanggil fungsi yang sama, tapi list-nya sedang di-park (kosong)
    sehingga tidak maju dua kali.
    """
    fn = _boss_live_hook(_BOSS_LIVE_STEP_FN, _BOSS_LIVE_STEP_SPECS,
                         boss_type)
    if fn is None:
        return
    try:
        fn(boss)
    except Exception:
        pass


def _boss_live_draw(boss_type, surface, boss, x, y):
    """Gambar FX milik renderer langsung ke layar (di luar cache)."""
    fn = _boss_live_hook(_BOSS_LIVE_DRAW_FN, _BOSS_LIVE_DRAW_SPECS,
                         boss_type)
    if fn is not None:
        try:
            fn(surface, boss, x, y)
        except Exception:
            pass
    # Beam pass (morgath): sama seperti jalur hero — body di-cache,
    # beam digambar live di layar skala 1.0 supaya tidak mengecil /
    # terpanggang beku.
    if boss_type in _BEAM_PASS_HEROES:
        renderer = BOSS_RENDERERS.get(boss_type)
        if renderer is not None:
            saved_scale = getattr(boss, "_render_scale", None)
            had_scale = hasattr(boss, "_render_scale")
            boss._render_scale = 1.0
            boss._beam_pass_only = True
            try:
                renderer(surface, boss, x, y)
            except Exception:
                pass
            finally:
                boss._beam_pass_only = False
                if had_scale:
                    boss._render_scale = saved_scale
                else:
                    try:
                        del boss._render_scale
                    except AttributeError:
                        pass


def _boss_geom(boss_type, kind, boss):
    """Geometri cache satu (tipe boss, pose): ``[half_canvas, rect|None]``.

    ``rect_crop`` dihitung SEKALI (dari bounding rect render pertama pose
    itu) lalu dipakai ulang, sehingga
      * ``get_bounding_rect()`` yang mahal tidak dipanggil tiap miss,
      * anchor sprite tidak bergeser antar frame,
      * pose skill yang melebar tidak membesarkan sprite idle/walk.
    """
    gk = (boss_type, kind)
    g = _BOSS_GEOM.get(gk)
    if g is None:
        r = int(getattr(boss, "radius", 30) or 30)
        half = max(BOSS_CANVAS_MIN_HALF, min(BOSS_CANVAS_MAX_HALF,
                                             r + 110))
        g = _BOSS_GEOM[gk] = [half, None]
    return g


_BOSS_CANVAS_POOL = {}


def _boss_get_canvas(size):
    """Canvas pakai-ulang per ukuran (alokasi Surface ~0,4 ms di HP)."""
    canvas = _BOSS_CANVAS_POOL.get(size)
    if canvas is None:
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        _BOSS_CANVAS_POOL[size] = canvas
    canvas.fill((0, 0, 0, 0))
    return canvas


def _boss_render_sprite_fast(boss_type, boss, draw_fn, kind):
    """Render badan boss ke sprite cache (1 render ke canvas SRCALPHA).

    Return ``(sprite, ax, ay)`` atau ``None``.

    Hanya dipakai untuk (tipe, pose) yang probe paritasnya membuktikan
    canvas SRCALPHA == render langsung (tidak ada pygame.draw.* ber-alpha
    / blend aditif yang berubah makna di canvas).

    ``ax``/``ay`` = posisi titik jangkar di dalam sprite, sehingga blit
    di ``(x - ax, y - ay)`` mendarat PERSIS di ``(x, y)`` — skala 1.0
    membuat semua angka ini bilangan bulat, jadi tidak ada pergeseran
    sub-piksel antar pose. FX yang melebar jauh tetap dijaga: canvas
    membesar otomatis, dan kalau mentok pose didaftarkan ke
    ``_BOSS_UNSAFE`` (jalur langsung).
    """
    geom = _boss_geom(boss_type, kind + "~f", boss)
    half = geom[0]
    size = half * 2
    canvas = _boss_get_canvas(size)
    c = half

    had_scale = hasattr(boss, "_render_scale")
    saved_scale = getattr(boss, "_render_scale", None)
    # _render_scale = penanda "jalur lane" untuk renderer: lapisan
    # FX hidup di-attach (bukan digambar) sehingga tidak terpanggang
    # ke cache, dan FX canvas fallback diserahkan ke lapisan hidup.
    # Nilai 1.0 -> ukuran & kompensasi world-space tidak berubah.
    if boss_type in _LIVE_FX_HEROES:
        boss._render_scale = 1.0
    pakai_lane = boss_type in _LIVE_FX_HEROES
    # Penanda "cache native boss": renderer TIDAK boleh melewati
    # pass cahayanya sendiri (di jalur hero pass itu diambil alih
    # heroes._finish_hd_sprite; di sini tidak ada HD pass karena
    # boss digambar 1:1 seperti sebelumnya).
    boss._boss_native_cache = True
    if boss_type in _BEAM_PASS_HEROES:
        boss._skip_beam = True
    try:
        if _boss_fx_parkable(boss_type):
            _call_renderer_on_canvas(draw_fn, canvas, boss, c, c)
        else:
            draw_fn(canvas, boss, c, c)
    except Exception:
        _boss_cache_stats["fallback"] += 1
        return None
    finally:
        boss._boss_native_cache = False
        boss._skip_beam = False
        if pakai_lane:
            if had_scale:
                boss._render_scale = saved_scale
            else:
                try:
                    del boss._render_scale
                except AttributeError:
                    pass

    box = canvas.get_bounding_rect(min_alpha=8)
    rect = geom[1]
    if (rect is not None and box.width > 0 and box.height > 0
            and box.left >= rect.left + 2 and box.top >= rect.top + 2
            and box.right <= rect.right - 3
            and box.bottom <= rect.bottom - 3):
        # Kasus cepat: SELURUH konten masih di dalam rect crop yang
        # tersimpan. (Memeriksa cincin tepi rect saja tidak cukup:
        # halo bisa melebar ke luar rect tanpa menyentuh cincin itu,
        # lalu FX-nya terpotong dari sprite.)
        return (canvas.subsurface(rect).copy(), c - rect.x, c - rect.y)

    if box.width <= 0 or box.height <= 0:
        return None
    if (box.left <= BOSS_CROP_MARGIN or box.top <= BOSS_CROP_MARGIN
            or box.right >= size - 1 - BOSS_CROP_MARGIN
            or box.bottom >= size - 1 - BOSS_CROP_MARGIN):
        # Konten + margin crop menyentuh tepi canvas: sprite akan punya
        # tinta di pinggirnya (FX terpotong) -> canvas membesar dulu.
        if half < BOSS_CANVAS_MAX_HALF:
            geom[0] = min(BOSS_CANVAS_MAX_HALF, half + 55)
            geom[1] = None
            _boss_cache_stats["grow"] += 1
        else:
            # Mentok: pose ini tidak aman di-cache. Gambar langsung
            # (jalur lama) supaya FX jauh tetap utuh.
            _BOSS_UNSAFE.add((boss_type, kind))
            _boss_cache_stats["fallback"] += 1
            _boss_cache_stats["unsafe"] += 1
        return None

    new_rect = box.inflate(BOSS_CROP_MARGIN * 2,
                           BOSS_CROP_MARGIN * 2)
    full = canvas.get_rect()
    # clip (irisan), BUKAN clamp: clamp menggeser rect yang lebih besar
    # dari canvas sehingga konten bisa pindah ke luar rect = terpotong.
    new_rect = new_rect.clip(full)
    if new_rect.width <= 0 or new_rect.height <= 0:
        _boss_dbg(boss_type, kind, f"new_rect kosong {new_rect} full={full}")
        return None
    if max(new_rect.width, new_rect.height) > BOSS_SPRITE_MAX_SIDE:
        # Terlalu besar untuk di-cache: gambar langsung saja.
        _boss_dbg(boss_type, kind, f"sprite terlalu besar {new_rect.size}")
        _BOSS_UNSAFE.add((boss_type, kind))
        _boss_cache_stats["fallback"] += 1
        _boss_cache_stats["unsafe"] += 1
        return None
    if rect is not None:
        # Rect berubah -> anchor sprite lama tidak berlaku lagi. Buang
        # semuanya (dan kembalikan anggaran pikselnya) supaya evict LRU
        # tidak makin agresif seiring waktu.
        for k in [k for k in _boss_sprite_cache
                  if k[0] == boss_type and k[8] == kind]:
            _old = _boss_sprite_cache.pop(k)
            _boss_cache_pixels[0] -= (_old[0].get_width()
                                      * _old[0].get_height())
    geom[1] = new_rect
    return (canvas.subsurface(new_rect).copy(),
            c - new_rect.x, c - new_rect.y)


# ═══ PROBE PARITAS PIKSEL (sekali per tipe boss) ═══════════════════
# Sprite cache memakai jalur CEPAT (1 render ke canvas SRCALPHA).
# Renderer yang memakai operasi yang berubah makna di canvas bisa
# mengubah tampilan, jadi setiap (tipe, pose) di-probe SEKALI: hasil
# "sprite + blit" dibanding dengan render langsung ala jalur lama.
# Kalau selisihnya melewati toleransi, pose itu digambar langsung
# seperti sebelumnya (perbaikan gerak & jam animasi tetap berlaku).
#
# PENTING: probe TANPA numpy. numpy tidak ikut bundle Android
# (buildozer.spec: python3,pygame-ce,pyjnius,android), dan versi probe
# lama yang memakai pygame.surfarray SELALU gagal di perangkat ->
# seluruh cache boss mati total tepat di tempat kelancaran paling
# dibutuhkan. Selisih piksel dihitung murni di level C pygame
# (_surf_mean_abs_diff) sehingga probe jalan di mana-mana.
BOSS_PARITY_TOLERANCE = 0.35
# Kalau dua render LANGSUNG berturut-turut (tanpa update di antaranya)
# sudah berbeda lebih dari ini, renderer punya jam animasi/state acak
# internal yang maju per draw (mis. krobellus: fase sapuan & orb ikut
# jam itu). Sprite cache akan membekukan jam tersebut dan tampilannya
# menyimpang dari jalur langsung, jadi pose seperti itu tidak di-cache.
BOSS_STATEFUL_DRIFT = 0.08
_BOSS_PARITY_DIFF = {}
# Tipe yang secara permanen TIDAK di-cache sprite, dengan alasan terukur
# (lihat tools/_diag_boss_pixel_parity.py):
#   krobellus: state FX hidup (trail sabit, star flash, orb) berada di
#     namespace MODUL dan maju per panggilan renderer; dibekukan ke
#     sprite membuat FX serangan hilang/bergeser (selisih visual 1.5).
#     Render langsungnya murah (~0.6 ms) jadi tidak ada yang dikorbankan.
_BOSS_CACHE_DENY = {
    "krobellus",
    # FX serangan satu-shot yang KONSUMSI-per-draw: gambar gelombang/
    # tebasan hanya muncul pada panggilan renderer yang pertama, lalu
    # state-nya habis. Dibekukan ke sprite = FX hilang di layar
    # (terukur tools/_diag_boss_pixel_parity.py: selisih 0.7-1.7).
    "gravewake", "kunkka", "syrentha", "vhalzun",
}
_BOSS_PROBE_FAIL = {}      # (tipe,pose) -> alasan probe gagal
_BOSS_PROBE_TRY = {}       # (tipe,pose) -> jumlah percobaan probe
_BOSS_MISS_MS = {}         # (tipe,pose) -> [total ms miss, jumlah miss]
_BOSS_DIRECT_DRIFT = {}    # (tipe,pose) -> selisih jalur langsung vs
                           #   dirinya sendiri tanpa update (jam animasi
                           #   internal renderer yang maju per draw)
_PROBE_TICK = 1000000      # tick virtual probe: semua render referensi
                           #   dalam satu probe melihat get_ticks() yang
                           #   sama supaya renderer ber-jam dinding
                           #   (gornak dkk.) dibandingkan secara adil
_BOSS_DIRECT_MS = {}       # tipe -> ms render langsung (diukur saat probe)
# Hit/miss per (tipe, pose) untuk governor biaya adaptif: pose yang
# terbukti tidak dihemat cache dikembalikan ke jalur langsung.
_BOSS_KIND_HM = {}
# List proyektil milik renderer yang dikosongkan selama probe supaya
# kedua sisi dibandingkan pada keadaan FX yang sama.
_BOSS_LIVE_LIST_SPECS = {
    "drakar": ("bosses.level1", "_NS_drakar", "_drk_projs"),
}


def _boss_probe_park(boss_type):
    """Kosongkan list proyektil renderer; return state untuk unpark."""
    spec = _BOSS_LIVE_LIST_SPECS.get(boss_type)
    if not spec:
        return None
    try:
        import importlib
        ns = getattr(importlib.import_module(spec[0]), spec[1], None)
        if ns is None:
            return None
        saved = getattr(ns, spec[2], None)
        setattr(ns, spec[2], [])
        return (ns, spec[2], saved)
    except Exception:
        return None


def _boss_probe_unpark(state):
    if not state:
        return
    try:
        ns, attr, saved = state
        setattr(ns, attr, saved)
    except Exception:
        pass


def _surf_mean_abs_diff(sa, sb):
    """Selisih rata-rata |a-b| dua permukaan (skala 0-255 per channel).

    TANPA numpy/surfarray (tidak tersedia di bundle Android — lihat
    catatan probe): |a-b| per channel dirakit dari blit SUB dua arah
    lalu MAX (semua di level C SDL), lalu rata-ratanya dihitung EKSAK
    dari sum() bita RGB-nya. Metriknya identik dengan
    ``abs(a - b).mean()`` per channel — bukan perkiraan — sehingga
    semua ambang probe (BOSS_PARITY_TOLERANCE / BOSS_STATEFUL_DRIFT)
    tetap berlaku persis seperti saat diukur dengan numpy.
    """
    if sa.get_size() != sb.get_size():
        return 9.9
    d1 = sa.copy()
    d1.blit(sb, (0, 0), special_flags=pygame.BLEND_RGB_SUB)   # max(0, a-b)
    d2 = sb.copy()
    d2.blit(sa, (0, 0), special_flags=pygame.BLEND_RGB_SUB)   # max(0, b-a)
    d1.blit(d2, (0, 0), special_flags=pygame.BLEND_RGB_MAX)   # |a-b|
    buf = pygame.image.tobytes(d1, "RGB")
    return sum(buf) / float(len(buf))


def _boss_probe_diff_direct(boss_type, boss, draw_fn, sprite,
                            ax, ay, size, kind="idle"):
    """Selisih rata-rata |langsung - sprite| pada panel uji."""
    c = size // 2
    bg = (24, 20, 30)
    ref = pygame.Surface((size, size))
    ref.fill(bg)
    had_beam = boss_type in _BEAM_PASS_HEROES
    park = _boss_probe_park(boss_type)   # kedua sisi tanpa proyektil live
    if had_beam:
        boss._skip_beam = True
    _jam_asli = pygame.time.get_ticks
    pygame.time.get_ticks = lambda: _PROBE_TICK
    try:
        _t0 = _time.perf_counter()
        draw_fn(ref, boss, c, c)
        _dt = (_time.perf_counter() - _t0) * 1000.0
        lama = _BOSS_DIRECT_MS.get(boss_type)
        if lama is None or _dt < lama:
            _BOSS_DIRECT_MS[boss_type] = _dt
        # Jam/state animasi internal? Render kedua pada tick virtual
        # SAMA: kalau hasilnya sudah berbeda, renderer maju per draw
        # (state/acak internal) dan tidak aman dibekukan ke sprite.
        ref2 = pygame.Surface((size, size))
        ref2.fill(bg)
        draw_fn(ref2, boss, c, c)
        _BOSS_DIRECT_DRIFT[(boss_type, kind)] = _surf_mean_abs_diff(ref,
                                                                    ref2)
    finally:
        pygame.time.get_ticks = _jam_asli
        if had_beam:
            boss._skip_beam = False
        _boss_probe_unpark(park)
    new = pygame.Surface((size, size))
    new.fill(bg)
    new.blit(sprite, (c - ax, c - ay))
    return _surf_mean_abs_diff(ref, new)


_BOSS_PROBE_ERRORS = {}    # (tipe,pose) -> pesan error terakhir


def _boss_probe_parity(boss_type, boss, draw_fn, kind="idle"):
    """Uji jalur cache untuk satu (tipe, pose) + ukur selisihnya.

    Render sprite lewat jalur cepat (1 render) lalu bandingkan dengan
    render langsung. Kalau selisihnya kecil, pose itu boleh di-cache;
    kalau tidak, pose itu digambar langsung seperti sebelumnya.

    Return ``(selisih, aman)`` atau ``None`` kalau sprite belum bisa
    dibuat (geometri canvas sedang tumbuh).
    """
    size = 320
    grow0 = _boss_cache_stats["grow"]
    park = _boss_probe_park(boss_type)
    # Lapisan FX hidup DIMATIKAN selama probe: pertukaran "FX canvas
    # baked" -> "lapisan hidup" untuk tipe terdaftar adalah perilaku
    # paritas-hero yang DISENGAJA (FX itu harus bergerak 60 fps, tidak
    # boleh terpanggang ke pose). Probe hanya menilai fidelitas BADAN +
    # lapisan canvas terhadap jalur langsung.
    pakai_live = boss_type in _LIVE_FX_HEROES
    if pakai_live:
        _LIVE_FX_HEROES.discard(boss_type)
    try:
        out = _boss_render_sprite_fast(boss_type, boss, draw_fn, kind)
        if out is None:
            # None karena canvas sedang membesar = coba lagi frame depan.
            # None tanpa pertumbuhan = sprite memang tidak bisa dibuat
            # (renderer tidak cocok dengan canvas) -> jangan di-cache.
            if _boss_cache_stats["grow"] == grow0:
                _BOSS_PROBE_ERRORS[(boss_type, kind)] = "fast: sprite None"
                return 9.9, False
            return None
        diff = _boss_probe_diff_direct(boss_type, boss, draw_fn,
                                       out[0], out[1], out[2],
                                       size, kind)
        if _BOSS_DIRECT_DRIFT.get((boss_type, kind), 0.0) \
                > BOSS_STATEFUL_DRIFT:
            return diff, False          # jam internal: jangan di-cache
        aman = diff <= BOSS_PARITY_TOLERANCE
        if aman:
            _BOSS_PARITY_DIFF[(boss_type, kind)] = diff
        return diff, aman
    except Exception as exc:
        _BOSS_PROBE_ERRORS[(boss_type, kind)] = f"{type(exc).__name__}: {exc}"
        return None
    finally:
        if pakai_live:
            _LIVE_FX_HEROES.add(boss_type)
        _boss_probe_unpark(park)


def _boss_dbg(boss_type, kind, pesan):
    """Catat alasan sprite gagal dibuat (aktif lewat MYSTIC_BOSS_DEBUG)."""
    _BOSS_PROBE_ERRORS[(boss_type, kind)] = pesan
    if _BOSS_DEBUG:
        print(f"[BOSS-DBG] {boss_type}/{kind}: {pesan}")


_BOSS_DEBUG = bool(_os.environ.get("MYSTIC_BOSS_DEBUG"))


def _sprite_edges_inked(sprite, strip=2, min_alpha=8):
    """True kalau ada tinta di cincin 2 px tepi sprite (FX terpotong)."""
    w, h = sprite.get_width(), sprite.get_height()
    if w < strip * 4 or h < strip * 4:
        return False
    for r in (pygame.Rect(0, 0, w, strip), pygame.Rect(0, h - strip, w, strip),
              pygame.Rect(0, 0, strip, h), pygame.Rect(w - strip, 0, strip, h)):
        try:
            if sprite.subsurface(r).get_bounding_rect(min_alpha=min_alpha).width:
                return True
        except Exception:
            return True
    return False


def _sprite_pixels(entry):
    """Jumlah piksel sprite satu entri cache (hero maupun boss)."""
    surf = entry[0]
    return surf.get_width() * surf.get_height()


def _boss_cache_store(key, sprite, ax, ay):
    """Simpan sprite dengan anggaran jumlah entri DAN total piksel."""
    entry = (sprite, ax, ay)
    _boss_cache_pixels[0] += _sprite_pixels(entry)
    while (len(_boss_sprite_cache) >= _BOSS_CACHE_MAX
           or _boss_cache_pixels[0] > _BOSS_CACHE_PIXEL_BUDGET):
        if not _boss_sprite_cache:
            break
        _boss_cache_pixels[0] -= _sprite_pixels(
            _boss_sprite_cache.popitem(last=False)[1])
    _boss_sprite_cache[key] = entry


def render_boss(boss_type, surface, boss, x, y, draw_fn=None):
    """Render mini boss / true boss lewat cache sprite (paritas hero).

    Return ``True`` kalau gambar sudah ditangani di sini; ``False``
    berarti pemanggil harus memakai jalur lama (renderer langsung ke
    layar) — dipakai sebagai jaring pengaman supaya boss tetap tampil
    apa pun yang terjadi.

    Urutan lapisan sama persis dengan Boss.draw lama:
        GROUND FX -> BADAN (sprite cache) -> FX RENDERER -> LIVE FX ATAS
    """
    if not BOSS_CACHE_ENABLED:
        return False
    if getattr(boss, "_portrait_hd", False):
        return False                      # portrait Hero Shop: jalur sendiri
    fn = draw_fn if callable(draw_fn) else BOSS_RENDERERS.get(boss_type)
    if fn is None or not callable(fn):
        return False

    if boss_type in _BOSS_CACHE_DENY:
        # Renderer tipe ini terbukti berubah tampilan saat dibekukan ke
        # sprite (FX konsumsi-per-draw / state modul yang maju per
        # render): pakai jalur langsung selamanya.
        return False

    key = _boss_cache_key(boss_type, boss)
    kind = key[8]
    if (boss_type, kind) in _BOSS_PROBE_FAIL:
        # Probe gagal (renderer error di canvas / geometri mentok):
        # jangan diulang tiap frame — pakai jalur langsung selamanya.
        return False
    if (boss_type, kind) in _BOSS_UNSAFE:
        # Pose FX melebar (skill jarak jauh / beam): jalur langsung
        # supaya tidak ada yang terpotong canvas.
        return False

    if (boss_type, kind) not in _BOSS_PARITY_DIFF:
        # Probe sekali per (tipe, pose) (~2 render): pastikan badan yang
        # di-cache terlihat SAMA dengan jalur langsung sebelum cache
        # dipakai. Pose berbeda memakai FX berbeda (skill paling rawan),
        # jadi masing-masing di-probe sendiri.
        grow0 = _boss_cache_stats["grow"]
        diff = _boss_probe_parity(boss_type, boss, fn, kind)
        if diff is None:
            gk0 = (boss_type, kind)
            if _boss_cache_stats["grow"] != grow0:
                return False        # canvas sedang membesar: bukan kegagalan
            n = _BOSS_PROBE_TRY[gk0] = _BOSS_PROBE_TRY.get(gk0, 0) + 1
            if n >= 8:
                # 3x gagal = bukan sekadar geometri yang sedang tumbuh;
                # hentikan percobaan supaya tidak ada biaya tersembunyi
                # tiap frame (jalur langsung = tampilan lama, aman).
                _BOSS_PROBE_FAIL[gk0] = _BOSS_PROBE_ERRORS.get(gk0,
                                                               "sprite None")
                _boss_cache_stats["probefail"] += 1
            return False
        if not diff[1]:
            # Pose ini tidak bisa dipakai cache (renderer tidak cocok
            # dengan canvas, atau selisihnya terlalu besar di kedua
            # jalur). Batasi per POSE supaya pose lain dari tipe yang
            # sama tetap bisa di-cache.
            _BOSS_UNSAFE.add((boss_type, kind))
            _boss_cache_stats["nocache"] += 1
            return False
    if key[-1]:
        # FX proyektil renderer aktif tanpa lapisan hidup pengganti:
        # gambar jalur langsung supaya FX-nya utuh & bergerak tiap frame.
        return False
    gk = (boss_type, kind)
    hm = _BOSS_KIND_HM.setdefault(gk, [0, 0])
    entry = _boss_sprite_cache.get(key)
    if entry is not None:
        sprite, ax, ay = entry
        _boss_cache_stats["hits"] += 1
        hm[0] += 1
        _boss_sprite_cache.move_to_end(key)     # LRU: tandai baru dipakai
    else:
        _t0 = _time.perf_counter()
        out = _boss_render_sprite_fast(boss_type, boss, fn, kind)
        _dt = (_time.perf_counter() - _t0) * 1000.0
        if out is None:
            return False                        # fallback jalur langsung
        sprite, ax, ay = out
        if _sprite_edges_inked(sprite):
            # Garansi keras: sprite dengan tinta di pinggiran 2 px
            # berarti ada FX yang terpotong crop -> pose ini tidak
            # boleh di-cache (jalur langsung = tampilan lama utuh).
            _BOSS_UNSAFE.add(gk)
            _boss_cache_stats["unsafe"] += 1
            _boss_dbg(boss_type, kind, "sprite punya tinta di tepi")
            return False
        hm[1] += 1
        mm = _BOSS_MISS_MS.setdefault(gk, [0.0, 0])
        mm[0] += _dt
        mm[1] += 1
        _boss_cache_stats["misses"] += 1
        _boss_cache_store(key, sprite, ax, ay)

    # Kebijakan adaptif berbasis BIAYA TERUKUR. Cache baru menguntungkan
    # kalau penghematan saat hit (render langsung tidak jalan) lebih
    # besar daripada kerugian saat miss (render sprite + tetap harus
    # menunggu). Untuk boss yang renderer-nya sudah ringan, cache bisa
    # jadi lebih lambat -> kembalikan ke jalur langsung.
    if hm[0] + hm[1] >= 20:
        _langsung = _BOSS_DIRECT_MS.get(boss_type)
        _mm = _BOSS_MISS_MS.get(gk)
        if _langsung and _mm and _mm[1]:
            _h = hm[0] / float(hm[0] + hm[1])
            _miss = _mm[0] / _mm[1]
            _untung = (_h * (_langsung - 0.10)
                       - (1.0 - _h) * max(0.0, _miss - _langsung))
            if _untung <= 0.0:
                _BOSS_UNSAFE.add(gk)
                _boss_cache_stats["uncache"] += 1
                return False

    # FX milik renderer yang harus maju tiap frame (proyektil drakar).
    _boss_live_step(boss_type, boss)

    if entry is not None:
        # Cache HIT: renderer dilewati, jadi controller pose diurus di
        # sini (paritas dengan hero: cache HIT tidak menghentikan anim).
        _tick_boss_pose(boss_type, boss)

    # Lapisan FX hidup di BAWAH sprite (ground FX, back particles) —
    # SETIAP frame, di luar cache, sama seperti jalur hero.
    _live_fx_pre(boss_type, surface, boss, x, y)

    surface.blit(sprite, (int(x - ax), int(y - ay)))

    # FX milik renderer (proyektil drakar) + beam (morgath) di layar.
    _boss_live_draw(boss_type, surface, boss, x, y)

    # Lapisan FX hidup di ATAS sprite (trail, proyektil, skill, impact).
    _live_fx_post(boss_type, surface, boss, x, y)
    return True


def _draw_generic_hero(surface, hero, x, y):
    """Fallback generic hero shape."""
    r = hero.radius
    color = hero.color
    color_dark = hero.color_dark

    # Shadow
    pygame.draw.ellipse(surface, (0, 0, 0, 100),
                        (x - r, y + r - 4, r * 2, 8))

    # Body
    pygame.draw.circle(surface, (0, 0, 0), (x + 1, y + 1), r + 2)
    pygame.draw.circle(surface, color, (x, y), r)
    pygame.draw.circle(surface, color_dark, (x, y), r, 2)

    # Highlight
    hl = tuple(min(255, c + 50) for c in color)
    pygame.draw.circle(surface, hl, (x - r // 3, y - r // 3), r // 2)

    # Eyes
    eye_color = (255, 50, 50) if hero.team == "red" else (100, 200, 255)
    pygame.draw.circle(surface, (0, 0, 0), (x - r // 3, y - r // 4), 3)
    pygame.draw.circle(surface, (0, 0, 0), (x + r // 3, y - r // 4), 3)
    pygame.draw.circle(surface, eye_color, (x - r // 3, y - r // 4), 2)
    pygame.draw.circle(surface, eye_color, (x + r // 3, y - r // 4), 2)
