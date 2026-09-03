#!/usr/bin/env python3
"""Regresi: ayunan (swing) hero lane tidak boleh beku karena sprite cache.

Bug
---
Banyak renderer hero MEMUTASI state animasi serangan di dalam fungsi
draw-nya -- ``_update_<x>_attack_anim`` mengisi ``_.._attack_frame``,
``_.._prev_timer``, dan ``_.._attack_active`` setiap dipanggil.

Tetapi ``heroes.render_hero`` men-cache sprite hero dengan key
``attack_timer // 2``.  Serangan pertama mengisi semua bucket key, jadi
renderer jalan dan animasi terlihat normal.  Pada serangan BERIKUTNYA
bucket yang sama sudah terisi -> cache hit -> renderer dilewati ->
controller tidak pernah maju lagi -> pose membeku di fase terakhir dan
flag ``attack_active`` tidak pernah mati.

Gejala di layar: hero mengayun sekali lalu tidak pernah mengayun lagi.
Dilaporkan pertama kali untuk Gorath; audit menemukan 21 hero terdampak.

Perbaikan
---------
Controller pose dijalankan tepat SEKALI per frame:
  * frame cache-MISS -> renderer yang menjalankan (dia dipanggil);
  * frame cache-HIT  -> ``heroes._tick_pose_controller`` yang menjalankan.
Tidak ada renderer yang perlu diubah, dan sprite cache tetap berfungsi.

Test ini memakai sprite cache dalam keadaan AKTIF -- persis kondisi
game.  Test terakhir mengaudit SEMUA hero, jadi kalau ada hero baru
yang pose-nya ber-state tapi lupa didaftarkan, test itu gagal.
"""

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import _core                                             # noqa: F401,E402
import _entity as E                                      # noqa: E402
import heroes                                            # noqa: E402

FULL_CYCLE = ("ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW",
              "RECOVERY")
SURF = pygame.Surface((320, 320), pygame.SRCALPHA)


def _phase_of(hero):
    """Nama fase serangan hero, atau None kalau hero tak punya."""
    for attr in dir(hero):
        if attr.endswith("_attack_phase") or attr.endswith("_atk_phase"):
            val = getattr(hero, attr, None)
            if isinstance(val, str) and val:
                return val
    return None


def _transitions(seq):
    out = []
    for v in seq:
        if not out or out[-1] != v:
            out.append(v)
    return out


def _run(hero_type, clear_cache_each_frame):
    """Jalankan 3 siklus serangan; kembalikan urutan transisi fase."""
    heroes.clear_hero_sprite_cache()
    hero = E.Hero(hero_type, "biru", 160, 200)
    hero.alive = True
    cd = max(2, int(getattr(hero, "attack_cooldown", 30) or 30))
    seq = []
    for _frame in range(cd * 3):
        if hero.attack_timer == 0:
            hero.attack_timer = cd
        else:
            hero.attack_timer -= 1
        if clear_cache_each_frame:
            heroes.clear_hero_sprite_cache()
        SURF.fill((0, 0, 0, 0))
        try:
            heroes.render_hero(hero_type, SURF, hero, 160, 200)
        except Exception:
            break
        seq.append(_phase_of(hero) or "-")
    return hero, _transitions(seq)


# ── 1. Sanity: cache harus aktif, kalau tidak test ini vacuous ────────
def test_cache_sprite_aktif():
    assert heroes.HERO_CACHE_ENABLED, (
        "HERO_CACHE_ENABLED False -> test ini tidak menguji apa-apa"
    )


# ── 2. Registry harus resolve ke fungsi yang bisa dipanggil ──────────
def test_registry_pose_controller_resolve():
    specs = heroes._POSE_CONTROLLER_SPECS
    assert len(specs) >= 21, (
        "registry menyusut jadi %d entri" % len(specs)
    )
    bad = []
    for hero_type, (mod_name, ns_name, fn_name) in sorted(specs.items()):
        try:
            fn = getattr(getattr(importlib.import_module(mod_name),
                                 ns_name), fn_name)
            assert callable(fn)
        except Exception as exc:
            bad.append("%s: %s: %s" % (hero_type, type(exc).__name__, exc))
    assert not bad, "entri registry gagal resolve:\n  " + "\n  ".join(bad)

    # Hero di luar registry harus no-op, dan tidak boleh melempar.
    heroes._POSE_CONTROLLER_CACHE.clear()
    assert heroes._pose_controller("kaizen") is None
    heroes._tick_pose_controller("kaizen", None)
    heroes._tick_pose_controller("tidak_ada_hero_ini", None)


# ── 3. Setiap hero terdampak: pose harus berulang di jalur game ──────
def test_pose_semua_hero_terdaftar_berulang():
    broken = []
    for hero_type in sorted(heroes._POSE_CONTROLLER_SPECS):
        _hero, trans = _run(hero_type, False)
        missing = [p for p in FULL_CYCLE if p not in trans]
        if missing or len(trans) <= len(FULL_CYCLE):
            broken.append("%s: fase hilang %s, urutan %s"
                          % (hero_type, missing, " -> ".join(trans[:9])))
    assert not broken, (
        "pose beku / tidak berulang:\n  " + "\n  ".join(broken)
    )


# ── 4. Controller maju tepat satu langkah per frame (gorath) ─────────
def test_controller_maju_tepat_satu_langkah_per_frame():
    """Kurang = controller jarang jalan (gejala bug lama: setengah
    kecepatan lalu beku).  Lebih = maju dua kali pada frame cache-miss
    (controller dipanggil dari dua tempat)."""
    heroes.clear_hero_sprite_cache()
    hero = E.Hero("gorath", "biru", 160, 200)
    hero.alive = True
    cd = max(2, int(hero.attack_cooldown))
    starts = []
    anim = []
    for f in range(cd * 2 + 6):
        if hero.attack_timer == 0:
            hero.attack_timer = cd
            starts.append(f)
        else:
            hero.attack_timer -= 1
        SURF.fill((0, 0, 0, 0))
        heroes.render_hero("gorath", SURF, hero, 160, 200)
        anim.append(int(getattr(hero, "_gor_attack_frame", 0)))
    bad = []
    for f, frame in enumerate(anim):
        start = max((s for s in starts if s <= f), default=None)
        if start is not None and frame != f - start:
            bad.append((f, frame, f - start))
    assert not bad, (
        "%d frame meleset (frame, dapat, harus): %s" % (len(bad), bad[:8])
    )


# ── 5. Audit SEMUA hero: registry harus lengkap ──────────────────────
def test_tidak_ada_hero_ber_state_yang_terlewat():
    """Bandingkan urutan fase cache-AKTIF (kondisi game) vs cache
    DIMATIKAN (referensi).  Hero yang hasilnya berbeda tapi TIDAK ada di
    registry berarti masih kena bug."""
    registered = set(getattr(heroes, "_POSE_CONTROLLER_SPECS", {}) or {})
    missed = []
    checked = 0
    for hero_type in sorted(E.get_all_hero_types()):
        heroes.clear_hero_sprite_cache()
        try:
            probe = E.Hero(hero_type, "biru", 0, 0)
        except Exception:
            continue
        if _phase_of(probe) is None:
            SURF.fill((0, 0, 0, 0))
            try:
                heroes.render_hero(hero_type, SURF, probe, 160, 200)
            except Exception:
                pass
            if _phase_of(probe) is None:
                continue          # hero ini tidak punya pose bernama
        checked += 1
        with_cache = _run(hero_type, False)[1]
        reference = _run(hero_type, True)[1]
        if with_cache != reference and hero_type not in registered:
            missed.append("%s\n      cache : %s\n      benar : %s"
                          % (hero_type, " -> ".join(with_cache[:8]),
                             " -> ".join(reference[:8])))
    assert checked > 15, (
        "hanya %d hero punya fase bernama -- audit tidak jalan" % checked
    )
    assert not missed, (
        "hero ini pose-nya beku tapi belum didaftarkan di "
        "_POSE_CONTROLLER_SPECS:\n  " + "\n  ".join(missed)
    )


# ── 6. Jalur mini boss tidak boleh berubah ───────────────────────────
def test_jalur_mini_boss_tetap_jalan():
    """Mini boss digambar tiap frame tanpa cache -> controller tetap
    dijalankan dari renderer, bukan dari heroes/__init__."""
    import bosses.level2 as L2
    from bosses.base_boss import Boss

    boss = Boss("gorath")
    boss.entrance_timer = 0
    boss.stun_timer = 0
    assert not hasattr(boss, "_render_scale"), (
        "mini boss tidak boleh terdeteksi sebagai hero lane"
    )
    big = pygame.Surface((400, 400), pygame.SRCALPHA)
    cd = max(2, int(boss.attack_cooldown))
    seq = []
    for _f in range(cd * 3):
        if boss.timer == 0:
            boss.timer = cd
        else:
            boss.timer -= 1
        big.fill((0, 0, 0, 0))
        L2.draw_gorath(big, boss, 200, 200)
        seq.append(getattr(boss, "_gor_attack_phase", "NONE"))
    trans = _transitions(seq)
    assert len(trans) > len(FULL_CYCLE), (
        "animasi mini boss tidak berulang (%d transisi): %s"
        % (len(trans), " -> ".join(trans[:9]))
    )


if __name__ == "__main__":
    tests = [
        test_cache_sprite_aktif,
        test_registry_pose_controller_resolve,
        test_pose_semua_hero_terdaftar_berulang,
        test_controller_maju_tepat_satu_langkah_per_frame,
        test_tidak_ada_hero_ber_state_yang_terlewat,
        test_jalur_mini_boss_tetap_jalan,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL  %s\n      %s: %s"
                  % (t.__name__, type(exc).__name__, exc))
    print("\n%d/%d lolos" % (len(tests) - failed, len(tests)))
    sys.exit(1 if failed else 0)
