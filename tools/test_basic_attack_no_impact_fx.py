#!/usr/bin/env python3
"""Regresi: SERANGAN DASAR tidak boleh memicu impact FX.

Kontrak yang dikunci (permintaan owner):

    "skill fx untuk basic attack tidak usah ada fx impact nya"

Sebelumnya tiap hero/mini boss punya blok ``IMPACT FX <NAMA>`` di jalur
serangan dasar yang memanggil ``notify_melee_impact`` /
``notify_projectile_impact``. Satu panggilan itu menyalakan SATU PAKET:
flash + shockwave + serpihan + screen shake + hit-stop 0.03-0.08 s.
Pada combat ramai tumpukan additive-nya membuat FX kedap-kedip dan
menutupi sprite.

Kontrak baru:
  * serangan dasar (melee maupun proyektil) -> NOL impact FX,
    NOL hit-stop, NOL screen shake;
  * SKILL tetap punya impact FX penuh (tidak boleh ikut hilang).

Test ini menjalankan kode yang sebenarnya diubah:
``_entity.Hero._do_attack``, loop proyektil ``_entity.Hero.update``, dan
``bosses.base_boss.Boss.update``.

Jalankan:  python3 tools/test_basic_attack_no_impact_fx.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import _core                                           # noqa: F401,E402
import _entity as E                                    # noqa: E402
import heroes                                          # noqa: E402
from bosses.base_boss import Boss                      # noqa: E402
from heroes import combat_feel as FEEL                 # noqa: E402

# 9 hero yang dulu punya blok IMPACT FX di _entity.Hero._do_attack.
HERO_MELEE = ("gornak", "grimjaw", "kaizen", "alchemist", "abaddon",
              "gorath", "nyzrak")
# Hero ranged: serangan dasarnya mendarat lewat proyektil generik.
HERO_RANGED = ("sylara", "razak", "vex", "zephyr", "krobellus")
# Mini boss yang dulu punya blok IMPACT FX di bosses/base_boss.py.
BOSS_TYPES = ("gornak", "thalgryn", "kunkka", "syrentha", "gravewake",
              "gravefang", "nyxara", "vhalzun", "xerathis", "varkul")


def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    FEEL.reset()


def _fxmod(hero_type):
    return heroes._live_fx_module(hero_type)


def _director(hero_type, unit):
    """Pasang director FX untuk unit, kembalikan director-nya."""
    mod = _fxmod(hero_type)
    if mod is None:
        return None, None
    try:
        mod.reset_all()
    except Exception:
        pass
    try:
        mod.attach(unit)
    except Exception:
        pass
    d = getattr(unit, "_%s_fx" % hero_type[:2], None)
    if d is None:
        for name in dir(unit):
            if name.endswith("_fx") and name.startswith("_"):
                cand = getattr(unit, name, None)
                if cand is not None and hasattr(cand, "stats"):
                    d = cand
                    break
    return mod, d


def _impact_count(mod, unit):
    """Jumlah ImpactFX aktif di director unit.

    5 director (abaddon, alchemist, krobellus, varkul, xerathis) tidak
    punya ``stats()``, jadi fallback ke list ``impacts`` langsung.
    """
    if mod is None:
        return 0
    try:
        d = mod.director_for(unit)
    except Exception:
        return 0
    if d is None:
        return 0
    st = getattr(d, "stats", None)
    if callable(st):
        try:
            return int(st().get("impacts", 0))
        except Exception:
            pass
    return len(getattr(d, "impacts", ()) or ())


def _mk_hero(hero_type, x=200.0, y=200.0):
    h = E.Hero(hero_type, "blue", x=x, y=y)
    h.alive = True
    h.attack_timer = 0
    h.damage = max(10, int(getattr(h, "damage", 10) or 10))
    return h


def _mk_target(x=240.0, y=200.0):
    t = E.Hero("grimjaw", "red", x=x, y=y)
    t.alive = True
    t.hp = t.max_hp = 100000
    return t


# ══════════════════════════════════════════════════════════════════════
# 1. SUMBER: tidak ada lagi panggilan impact FX di jalur serangan dasar
# ══════════════════════════════════════════════════════════════════════
def test_sumber_tidak_memanggil_impact_fx_di_serangan_dasar():
    ent = open(os.path.join(ROOT, "_entity.py"), encoding="utf-8").read()
    bb = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               encoding="utf-8").read()
    assert "notify_melee_impact(" not in ent.replace(
        "# Sembilan blok `IMPACT FX <HERO>` (notify_melee_impact)", ""), \
        "_entity.py masih memanggil notify_melee_impact"
    for src, nama in ((ent, "_entity.py"), (bb, "base_boss.py")):
        for token in ("_gfx.notify_melee_impact", "_gjfx.notify_melee_impact",
                      "_abfx.notify_melee_impact", "_kzfx.notify_melee_impact",
                      "_syfx2.notify_melee_impact", "_rfx.notify_melee_impact",
                      "_afx.notify_melee_impact", "_nzfx.notify_melee_impact",
                      "_tfx.notify_melee_impact", "_kfx.notify_melee_impact",
                      "_gwfx.notify_melee_impact", "_gfvfx.notify_melee_impact",
                      "_syfx.notify_melee_impact"):
            assert token not in src, "%s masih memanggil %s" % (nama, token)
    # base_boss tidak boleh memanggil impact FX sama sekali lagi
    assert "notify_melee_impact(" not in bb.replace(
        "# 19 blok `IMPACT FX <BOSS>` (notify_melee_impact /", "").replace(
        "# notify_projectile_impact) yang dulu berdiri di sini", ""), \
        "base_boss.py masih memanggil notify_melee_impact"
    assert "notify_projectile_impact(" not in bb.replace(
        "# notify_projectile_impact) yang dulu berdiri di sini", ""), \
        "base_boss.py masih memanggil notify_projectile_impact"


# ══════════════════════════════════════════════════════════════════════
# 2. RUNTIME: serangan dasar MELEE hero -> nol impact / hit-stop / shake
# ══════════════════════════════════════════════════════════════════════
def test_serangan_dasar_melee_hero_tanpa_impact_fx():
    for hero_type in HERO_MELEE:
        _clear_feel()
        h = _mk_hero(hero_type)
        h.range = 60
        h.is_melee_hero = True
        mod, _d = _director(hero_type, h)
        tgt = _mk_target(h.x + 40, h.y)
        h.target = tgt
        hp0 = tgt.hp

        h._do_attack()

        assert tgt.hp < hp0, "%s: damage tidak masuk" % hero_type
        assert _impact_count(mod, h) == 0, \
            "%s: serangan dasar memicu %d impact FX" % (
                hero_type, _impact_count(mod, h))
        assert FEEL.HITSTOP.frames == 0, \
            "%s: serangan dasar memicu hit-stop" % hero_type
        assert FEEL.SHAKE.shake_strength == 0.0, \
            "%s: serangan dasar memicu screen shake" % hero_type
        if mod is not None:
            try:
                mod.reset_all()
            except Exception:
                pass
    _clear_feel()


# ══════════════════════════════════════════════════════════════════════
# 3. RUNTIME: proyektil serangan dasar -> nol impact FX
#    proyektil SKILL -> impact FX TETAP ADA
# ══════════════════════════════════════════════════════════════════════
def _run_until_projectile_hits(h, mod, max_frames=400):
    for _ in range(max_frames):
        if not any(p.get("alive") for p in h.projectiles):
            return True
        h.update([], [], [])
    return False


def test_proyektil_serangan_dasar_tanpa_impact_fx():
    for hero_type in HERO_RANGED:
        _clear_feel()
        h = _mk_hero(hero_type)
        h.range = 200
        mod, _d = _director(hero_type, h)
        tgt = _mk_target(h.x + 150, h.y)
        h.target = tgt
        hp0 = tgt.hp

        # proyektil serangan dasar (is_skill=False)
        h._spawn_projectile(60)
        assert h.projectiles[-1].get("is_skill") is False, \
            "%s: proyektil basic attack salah ditandai is_skill" % hero_type
        _run_until_projectile_hits(h, mod)

        assert tgt.hp < hp0, "%s: damage proyektil tidak masuk" % hero_type
        assert _impact_count(mod, h) == 0, \
            "%s: proyektil basic attack memicu %d impact FX" % (
                hero_type, _impact_count(mod, h))
        assert FEEL.HITSTOP.frames == 0, \
            "%s: proyektil basic attack memicu hit-stop" % hero_type
        if mod is not None:
            try:
                mod.reset_all()
            except Exception:
                pass
    _clear_feel()


def test_proyektil_skill_tetap_punya_impact_fx():
    """Impact FX tidak boleh ikut hilang untuk SKILL."""
    ada = 0
    for hero_type in HERO_RANGED:
        _clear_feel()
        h = _mk_hero(hero_type)
        h.range = 200
        mod, _d = _director(hero_type, h)
        if mod is None or not hasattr(mod, "notify_projectile_impact"):
            continue
        tgt = _mk_target(h.x + 150, h.y)
        h.target = tgt

        h._spawn_skill_projectile(tgt)
        assert h.projectiles[-1].get("is_skill") is True, \
            "%s: proyektil skill tidak ditandai is_skill" % hero_type
        _run_until_projectile_hits(h, mod)

        n = _impact_count(mod, h)
        if n > 0:
            ada += 1
        try:
            mod.reset_all()
        except Exception:
            pass
    _clear_feel()
    assert ada > 0, \
        "tidak ada satu pun proyektil skill yang memicu impact FX"


# ══════════════════════════════════════════════════════════════════════
# 4. RUNTIME: serangan dasar MINI BOSS -> nol impact FX
# ══════════════════════════════════════════════════════════════════════
def _mk_boss(boss_type, tgt):
    """Boss siap serang: entrance selesai, smart AI sudah lazy-init.

    Update pemanasan (tanpa pengukuran) diperlukan karena atribut smart
    AI (``q_timer``, ``morph_buff_active``, ``active_skill_timer``, ...)
    baru dibuat saat ``_smart_ai_*`` pertama kali jalan.
    """
    b = Boss(boss_type)
    b.alive = True
    b.hp = b.max_hp = 100000
    b.x, b.y = 200.0, 200.0
    b.range = 200
    b.entrance_timer = 0
    b.stun_timer = 0
    b.update([tgt], [], [])
    # Kunci semua cooldown skill: update yang diukur hanya boleh
    # menjalankan SERANGAN DASAR, supaya skill FX tidak ikut terhitung.
    for k in ("q_timer", "w_timer", "e_timer", "r_timer",
              "ability_timer", "ability2_timer"):
        setattr(b, k, 99999)
    b.timer = 0
    return b


def test_serangan_dasar_boss_tanpa_impact_fx():
    diuji = 0
    for boss_type in BOSS_TYPES:
        _clear_feel()
        try:
            probe = Boss(boss_type)
        except Exception:
            continue
        del probe
        tgt = _mk_target(260.0, 200.0)
        tgt.team = "blue"
        try:
            b = _mk_boss(boss_type, tgt)
        except Exception:
            continue
        mod, _d = _director(boss_type, b)
        _clear_feel()
        hp0 = tgt.hp

        b.update([tgt], [], [])

        # Jaga supaya test tidak vacuous: boss HARUS benar-benar
        # menyerang (target ketemu + damage masuk).
        assert b.target is tgt, "%s: boss tidak mendapat target" % boss_type
        assert tgt.hp < hp0, "%s: serangan dasar boss tidak masuk" % boss_type
        diuji += 1

        assert _impact_count(mod, b) == 0, \
            "%s: serangan dasar boss memicu %d impact FX" % (
                boss_type, _impact_count(mod, b))
        assert FEEL.HITSTOP.frames == 0, \
            "%s: serangan dasar boss memicu hit-stop" % boss_type
        assert FEEL.SHAKE.shake_strength == 0.0, \
            "%s: serangan dasar boss memicu screen shake" % boss_type
        if mod is not None:
            try:
                mod.reset_all()
            except Exception:
                pass
    _clear_feel()
    assert diuji >= 8, "hanya %d boss yang teruji" % diuji


# ══════════════════════════════════════════════════════════════════════
# 5. SKILL FX TETAP HIDUP (jangan sampai ikut terbuang)
# ══════════════════════════════════════════════════════════════════════
def test_skill_masih_punya_impact_fx():
    ada = 0
    for boss_type in ("thalgryn", "kunkka", "syrentha", "gravewake"):
        _clear_feel()
        try:
            b = Boss(boss_type)
        except Exception:
            continue
        b.alive = True
        b.x, b.y = 300.0, 300.0
        mod, _d = _director(boss_type, b)
        if mod is None or not hasattr(mod, "notify_skill_impact"):
            continue
        mod.notify_skill_cast(b, "q")
        mod.notify_skill_impact(b, b.x + 40, b.y, 120, "q")
        if _impact_count(mod, b) > 0:
            ada += 1
        try:
            mod.reset_all()
        except Exception:
            pass
    _clear_feel()
    assert ada > 0, "skill FX ikut hilang - notify_skill_impact tidak jalan"


if __name__ == "__main__":
    gagal = 0
    for name in sorted(k for k in list(globals()) if k.startswith("test_")):
        fn = globals()[name]
        if not callable(fn):
            continue
        try:
            fn()
            print("PASS %s" % name)
        except AssertionError as exc:
            gagal += 1
            print("FAIL %s: %s" % (name, exc))
        except Exception as exc:                      # pragma: no cover
            gagal += 1
            print("ERROR %s: %s: %s" % (name, type(exc).__name__, exc))
    _clear_feel()
    if gagal:
        print("\n%d test gagal" % gagal)
        sys.exit(1)
    print("\nSemua test 'serangan dasar tanpa impact FX' lolos")
    sys.exit(0)
