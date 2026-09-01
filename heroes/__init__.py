# ================================
# heroes/__init__.py
# Registry untuk hero rendering
# Dispatch ke individual hero renderers
# ================================

import pygame
import math

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
# ═══════════════════════════════════════════════════════
_LIVE_FX_HEROES = {"zephyr", "gornak"}
_LIVE_FX_MODULES = {}

_LIVE_FX_PATHS = {
    "zephyr": "heroes.zephyr_fx",
    "gornak": "heroes.gornak_fx",
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
    return mod or None


def _live_fx_pre(hero_type, surface, hero, x, y):
    """Lapisan FX di BAWAH sprite hero (ground FX, back particles)."""
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
    """Lapisan FX di ATAS sprite hero (trail, projectile, impact)."""
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


def hero_cache_bytes():
    """Perkiraan pemakaian memori cache sprite hero, dalam MB."""
    total = 0
    for entry in _hero_sprite_cache.values():
        try:
            surf = entry[0]
            total += surf.get_width() * surf.get_height() * 4
        except Exception:
            pass
    return total / (1024.0 * 1024.0)


def hero_cache_stats():
    """Statistik cache, berguna untuk cek efektivitas."""
    h = _hero_cache_stats['hits']
    m = _hero_cache_stats['misses']
    tot = h + m
    return {
        'entries': len(_hero_sprite_cache),
        'hits': h,
        'misses': m,
        'hit_rate': f"{(h / tot * 100) if tot else 0:.1f}%",
    }


def clear_hero_sprite_cache():
    """Panggil saat ganti level / resolusi berubah."""
    _hero_sprite_cache.clear()
    _hero_cache_stats['hits'] = 0
    _hero_cache_stats['misses'] = 0


# ═══ PARK RENDERER PROJECTILES SAAT CANVAS CACHE ═══
# Renderer boss/starter menyimpan FX di list bertanda `_` (mis.
# `_sy_projectiles`, `_aa_beams`, `_vk_chain_orbs`). Saat hero
# digambar ke canvas cache di pusat (c, c) — BUKAN koordinat dunia —
# list itu ikut di-update & di-blit, lalu sprite di-cache. Akibatnya
# orb/panah “acak” menempel di sekitar badan hero setiap cache hit.
# Gameplay pakai `hero.projectiles` (tanpa `_`) yang digambar di
# dunia oleh _entity.py; list itu JANGAN di-park.
_RENDERER_FX_SUFFIXES = (
    "_projectiles",
    "_chain_orbs",
    "_beams",
    "_shards",
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
                skill_t // (HERO_SKILL_QUANT * _q))
    if timer > 0:
        return (hero_type, team, level, facing, 'atk',
                timer // (HERO_ATK_QUANT * _q))

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
    # Lapisan FX hidup (ground) HARUS di bawah sprite -> digambar dulu.
    _live_fx_pre(hero_type, surface, hero, x, y)

    if not HERO_CACHE_ENABLED:
        if not _render_hero_raw(hero_type, surface, hero, x, y):
            _draw_generic_hero(surface, hero, x, y)
        _live_fx_post(hero_type, surface, hero, x, y)
        return

    key = _hero_cache_key(hero_type, hero)

    entry = _hero_sprite_cache.get(key)
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
        _hero_sprite_cache[key] = (sprite, ax, ay, uses + 1)
        _hero_sprite_cache.move_to_end(key)      # LRU: tandai baru dipakai

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

            if len(_hero_sprite_cache) >= _HERO_CACHE_MAX:
                _hero_sprite_cache.pop(next(iter(_hero_sprite_cache)))

            # Simpan apa adanya dulu; konversi colorkey menyusul pada
            # pemakaian kedua (lihat jalur "hit" di atas).
            _hero_sprite_cache[key] = (sub, ax, ay, 1)
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
