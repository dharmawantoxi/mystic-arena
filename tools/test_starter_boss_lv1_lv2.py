#!/usr/bin/env python3
"""Regresi: starter hero + mini boss & true boss LEVEL 1 dan LEVEL 2.

Mengunci lima bug yang pernah lolos ke main. Semuanya kelas bug yang
TIDAK terlihat dari layar (tertelan `except Exception`, atau cuma muncul
di match KEDUA), jadi harus dijaga tes.

 1. **Hit-stop bocor antar match** (`_core.Game.reset`).
    `heroes/combat_feel.HITSTOP` itu singleton MODUL. Kalau match lama
    berakhir saat hit-stop aktif, sisa frame beku terbawa ke match baru;
    `Game.update()` memanggil `should_freeze_frame()` paling awal lalu
    `return`, sehingga frame pertama match baru dibuang diam-diam -
    reward kematian tower hilang, `red_towers_destroyed` tidak naik, dan
    TRUE BOSS bisa tidak pernah spawn.

 2. **`SwingTrail.draw` Gornak salah tempel** (`heroes/gornak_fx.py`).
    Isinya kode `Particle.draw` (`self.max_life`, `self.pos`, ...) yang
    tidak ada di SwingTrail -> AttributeError tiap kali trail digambar.
    Ditambah kelas `SwingTrail`/`ParticleSystem` terdefinisi 3x, jadi
    versi dokumentasi (sector-arc v3) tertimpa versi lama.

 3. **`_debug_font` NameError** (`bosses/level2.py`, Alchemist).
    Dipanggil sebagai nama bebas di dalam kelas namespace -> panel debug
    true boss level 2 tidak pernah tampil.

 4. **`morvaeth2` tidak terindeks** (`bosses/_boss_index.py`).
    `draw_morvaeth` ada di level25 DAN level42; generator membuang yang
    kedua, jadi mini boss level 42 render KOSONG (tak terlihat).

 5. **`reset_all` Grimjaw tanpa `global`** (`heroes/grimjaw_fx.py`).
    `_LAST_TICK_MS = None` cuma bikin variabel lokal -> jam frame tidak
    pernah direset antar match.

Jalankan:  python3 tools/test_starter_boss_lv1_lv2.py
      atau python3 -m pytest tools/test_starter_boss_lv1_lv2.py -q
"""
import ast
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# Jangan menulis save ke dalam repo saat tes berjalan.
import tempfile                                         # noqa: E402

os.environ.setdefault(
    "MYSTIC_SAVE_DIR",
    os.path.join(tempfile.gettempdir(), "mystic_test_saves"))

import pygame                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import _core                                           # noqa: E402
from _core import Game                                 # noqa: E402
from _entity import Tower                              # noqa: E402
from heroes import (BOSS_RENDERERS, HERO_RENDERERS,     # noqa: E402
                    _ProbeEntity, render_hero)
from heroes import combat_feel as FEEL                  # noqa: E402
from levels import get_level_config                     # noqa: E402

STARTER = ("kaizen", "grimjaw", "sylara", "thorne", "vex", "zephyr")
SKILLS = (None, "q", "w", "e", "r")


def _scope():
    """(mini, true) untuk level 1 & 2 - dibaca dari level_data, bukan hardcode."""
    mini, true = [], []
    for lvl in (1, 2):
        cfg = get_level_config(lvl)
        mini += list(cfg["mini_bosses"].values())
        true.append(cfg["true_boss"])
    return mini, true


MINI, TRUE = _scope()


# ══════════════════════════════════════════════════════════════════════
# BUG 1 - hit-stop bocor antar match -> true boss tidak spawn
# ══════════════════════════════════════════════════════════════════════
def _fresh_game(level=1):
    g = Game(pygame.display.set_mode(
        (_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT)), level_number=level)
    for nm in ("level_intro", "boss_intro"):
        o = getattr(g, nm, None)
        if o is not None and hasattr(o, "handle_skip"):
            try:
                o.handle_skip(key=pygame.K_SPACE)
            except Exception:
                pass
    return g


def _kill_red_towers(g, n):
    for i in range(n):
        g.towers.append(Tower(900 + i * 10, 200 + i * 10, "red"))
    g.update()
    for t in [t for t in g.towers if t.team == "red"]:
        t.hp = 0
        t.alive = False
    g.update()


def test_reset_membersihkan_bus_game_feel():
    """Match baru WAJIB mulai tanpa sisa hit-stop/shake match lama."""
    FEEL.hit_stop(0.08)
    FEEL.shake(9.0, 0.5, forward_to_camera=False)
    assert FEEL.HITSTOP.active, "prekondisi: hit-stop memang aktif"

    _fresh_game()                       # Game.reset() harus mengosongkan bus

    assert not FEEL.HITSTOP.active, (
        "hit-stop match lama terbawa ke match baru -> frame pertama "
        "dibuang, reward tower hilang, true boss bisa gagal spawn")
    assert FEEL.SHAKE.amount == 0.0, "shake match lama ikut terbawa"


def test_true_boss_tetap_spawn_walau_match_lama_berakhir_saat_hitstop():
    """Regresi utama: 6 tower merah hancur -> true boss level 1 spawn."""
    FEEL.hit_stop(0.08)                 # match sebelumnya berhenti saat freeze
    g = _fresh_game(1)
    _kill_red_towers(g, 6)
    assert g.red_towers_destroyed >= 6, (
        "counter tower merah = %d; frame reward tertelan hit-stop sisa"
        % g.red_towers_destroyed)
    for _ in range(3):
        g.update()
    assert g.true_boss_spawned, "true boss level 1 tidak spawn"
    assert g.active_boss is not None
    assert g.active_boss.boss_type == get_level_config(1)["true_boss"]


def test_kurang_dari_6_tower_belum_spawn():
    FEEL.reset()
    g = _fresh_game(1)
    _kill_red_towers(g, 5)
    for _ in range(3):
        g.update()
    assert not g.true_boss_spawned, "true boss spawn padahal baru 5 tower"


# ══════════════════════════════════════════════════════════════════════
# BUG 2 - SwingTrail Gornak: definisi ganda + draw() salah tempel
# ══════════════════════════════════════════════════════════════════════
def _toplevel_defs(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    names = {}
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.setdefault(node.name, []).append(node.lineno)
    return names


def test_gornak_fx_tanpa_definisi_ganda():
    """Kelas yang terdefinisi 2x = versi pertama mati diam-diam."""
    dupes = {n: ln for n, ln in _toplevel_defs(
        os.path.join(ROOT, "heroes", "gornak_fx.py")).items() if len(ln) > 1}
    assert not dupes, "definisi ganda di gornak_fx.py: %s" % dupes


def test_gornak_swing_trail_bisa_digambar():
    """draw() harus memakai atribut SwingTrail, bukan atribut Particle."""
    from heroes import gornak_fx as F
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    trail = F.SwingTrail()
    for i in range(10):
        trail.push((100 + i * 4, 150), (140 + i * 6, 110 - i * 3),
                   (98 + i * 4, 154), (132 + i * 6, 120 - i * 3))
        trail.update(1.0 / 60.0)
    trail.draw(surf)                    # dulu: AttributeError max_life
    assert surf.get_bounding_rect(min_alpha=4).width > 0, \
        "trail ayunan Gornak tidak menggambar apa pun"


def test_gornak_swing_trail_versi_v3_yang_terpakai():
    """Yang aktif harus implementasi sector-arc (docs/AUDIT_ULANG_DARI_AWAL.md)."""
    from heroes import gornak_fx as F
    for attr in ("MAX_TURN_DOT", "ARC_STEP", "MAX_SWEEP"):
        assert hasattr(F.SwingTrail, attr), (
            "SwingTrail aktif bukan versi v3 (kurang %s) - "
            "kemungkinan tertimpa definisi lama" % attr)
    assert callable(getattr(F.SwingTrail, "_ang_delta", None))


# ══════════════════════════════════════════════════════════════════════
# BUG 3 - overlay debug boss level 1 & 2 tidak boleh melempar exception
# ══════════════════════════════════════════════════════════════════════
def _boss_ns(name):
    import importlib
    for mod, ns in (("bosses.level1", "_NS_" + name),
                    ("bosses.level2", "_NS_" + name)):
        m = importlib.import_module(mod)
        obj = getattr(m, ns, None)
        if obj is not None:
            return obj
    return None


def test_debug_overlay_boss_lv1_lv2_aman():
    """DEBUG_CHARACTER=True tidak boleh bikin renderer error/blank."""
    from bosses.base_boss import Boss
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)
    path = [(100, 300), (400, 300), (800, 300)]
    checked = 0
    for name in MINI + TRUE:
        NS = _boss_ns(name)
        if NS is None or not hasattr(NS, "DEBUG_CHARACTER"):
            continue
        renderer = BOSS_RENDERERS.get(name)
        assert renderer is not None, "renderer %s hilang" % name
        old = NS.DEBUG_CHARACTER
        NS.DEBUG_CHARACTER = True
        try:
            boss = Boss(name, path)
            for skill in SKILLS:
                boss.active_skill = skill
                boss.active_skill_timer = 50 if skill else 0
                boss.timer = 12
                surf.fill((0, 0, 0, 0))
                renderer(surf, boss, 450, 350)      # tak boleh melempar
            checked += 1
        finally:
            NS.DEBUG_CHARACTER = old
    assert checked, "tidak ada boss level 1/2 dengan overlay debug diuji"


def test_alchemist_debug_font_lewat_namespace():
    """`_debug_font` harus diakses via NS, bukan nama bebas (NameError)."""
    NS = _boss_ns("alchemist")
    assert NS is not None and callable(getattr(NS, "_debug_font", None))
    src = ast.parse(open(os.path.join(ROOT, "bosses", "level2.py"),
                         encoding="utf-8").read())
    for node in ast.walk(src):
        if (isinstance(node, ast.FunctionDef)
                and node.name == "_draw_alch_debug"):
            seg = ast.dump(node)
            assert "'_debug_font'" not in seg or "attr='_debug_font'" in seg, \
                "_draw_alch_debug masih memanggil _debug_font sebagai nama bebas"
            return
    raise AssertionError("_draw_alch_debug tidak ditemukan")


# ══════════════════════════════════════════════════════════════════════
# BUG 4 - setiap tipe boss WAJIB punya renderer (kalau tidak: invisible)
# ══════════════════════════════════════════════════════════════════════
def test_semua_tipe_boss_terindeks():
    from bosses._boss_index import BOSS_INDEX
    from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
    wanted = list(MINI_BOSS_TYPES) + list(TRUE_BOSS_TYPES)
    missing = sorted(t for t in wanted if t not in BOSS_INDEX)
    assert not missing, (
        "%d tipe boss tanpa entri indeks -> render KOSONG di game: %s "
        "(jalankan: python tools/gen_boss_index.py)"
        % (len(missing), ", ".join(missing)))


def test_boss_bernama_mirip_punya_renderer_berbeda():
    """morvaeth (lv25) dan morvaeth2 (lv42) harus dua fungsi berbeda."""
    from bosses._boss_index import BOSS_INDEX
    a, b = BOSS_INDEX.get("morvaeth"), BOSS_INDEX.get("morvaeth2")
    assert a and b, "morvaeth/morvaeth2 hilang dari indeks"
    assert a[0] != b[0], "keduanya menunjuk modul yang sama: %s" % (a,)


# ══════════════════════════════════════════════════════════════════════
# BUG 5 - reset_all modul FX wajib benar-benar mereset jam frame
# ══════════════════════════════════════════════════════════════════════
def test_reset_all_fx_memakai_global():
    """Tanpa `global`, `_LAST_TICK_MS = None` cuma variabel lokal."""
    import importlib
    broken = []
    for mod in ("grimjaw_fx", "kaizen_fx", "sylara_fx", "vex_fx"):
        m = importlib.import_module("heroes." + mod)
        fn = getattr(m, "reset_all", None)
        if fn is None:
            continue
        tree = ast.parse(open(m.__file__, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "reset_all":
                body = ast.dump(node)
                writes = "_LAST_TICK_MS" in body
                globals_ = any(isinstance(n, ast.Global)
                               and "_LAST_TICK_MS" in n.names
                               for n in ast.walk(node))
                if writes and not globals_:
                    broken.append(mod)
    assert not broken, (
        "reset_all menulis _LAST_TICK_MS tanpa `global` di: %s"
        % ", ".join(broken))


# ══════════════════════════════════════════════════════════════════════
# ASAP: render semua unit dalam scope di seluruh state
# ══════════════════════════════════════════════════════════════════════
def _probe(name, boss_like=False):
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)
    for skill in SKILLS:
        for atk in (0, 10, 25, 44):
            for facing in (1, -1):
                e = _ProbeEntity(name, 450, 350)
                e.facing = e.direction = facing
                e.attack_timer = e.timer = atk
                e.active_skill = skill
                e.active_skill_timer = 40 if skill else 0
                e.pulse = 1.2
                if boss_like:
                    e.boss_class = "true" if name in TRUE else "mini"
                surf.fill((0, 0, 0, 0))
                render_hero(name, surf, e, 450, 350)
    surf.fill((0, 0, 0, 0))
    render_hero(name, surf, _ProbeEntity(name, 450, 350), 450, 350)
    rect = surf.get_bounding_rect(min_alpha=8)
    assert rect.width > 2 and rect.height > 2, \
        "%s render KOSONG (tak terlihat di game)" % name


def test_starter_hero_render_semua_state():
    for h in STARTER:
        assert h in HERO_RENDERERS, "starter %s tidak terdaftar" % h
        _probe(h)


def test_mini_boss_lv1_lv2_render_semua_state():
    for b in MINI:
        _probe(b, boss_like=True)


def test_true_boss_lv1_lv2_render_semua_state():
    for b in TRUE:
        _probe(b, boss_like=True)


def test_kecepatan_fx_tidak_tergantung_jumlah_unit():
    """BUG #6: FX tidak boleh maju N kali lebih cepat untuk N unit.

    ``draw_ground_layer()`` dipanggil sekali per unit, dan di dalamnya
    memanggil ``tick()``. Padahal ``tick()`` melangkahkan SELURUH
    director sekaligus. Tanpa guard "frame yang sama", 4 Razak di layar
    membuat partikel/trail-nya maju ~4x lebih cepat dan habis sebelum
    waktunya -- terlihat sebagai FX berkedip/putus saat ramai.

    Guard-nya adalah ``now == _LAST_TICK_MS`` di ``tick()``; dulu hanya
    kaizen/sylara/vex yang punya. Test ini memakai jam palsu supaya
    "satu frame" terdefinisi pasti, bukan bergantung kecepatan mesin.
    """
    import importlib

    from heroes import combat_feel as feel

    modul = ("razak", "gornak", "grimjaw", "gorath", "alchemist",
             "zephyr", "kaizen")
    real_ticks = pygame.time.get_ticks
    surf = pygame.Surface((640, 480), pygame.SRCALPHA)
    try:
        for nama in modul:
            M = importlib.import_module("heroes.%s_fx" % nama)
            if not hasattr(M, "draw_ground_layer"):
                continue
            maju = {}
            for n_unit in (1, 4):
                clock = {"ms": 100000}
                pygame.time.get_ticks = lambda: clock["ms"]
                M.reset_all()
                feel.reset()
                units = []
                for i in range(n_unit):
                    u = _ProbeEntity(nama, 100.0 + i * 40, 100.0)
                    u.boss_class = "mini"
                    if hasattr(M, "attach"):
                        M.attach(u)
                    units.append(u)
                d0 = M.director_for(units[0])
                t0 = d0.time
                for _ in range(20):          # 20 frame, tiap frame +16 ms
                    clock["ms"] += 16
                    for u in units:
                        M.draw_ground_layer(surf, u, u.x, u.y)
                maju[n_unit] = d0.time - t0
            if maju[1] <= 0.0:
                continue                     # modul tak maju via jalur ini
            rasio = maju[4] / maju[1]
            assert rasio < 1.25, (
                "%s: 4 unit membuat FX maju %.2fx lebih cepat "
                "(1 unit=%.3fs, 4 unit=%.3fs) -- guard frame-sama di "
                "tick() hilang" % (nama, rasio, maju[1], maju[4]))
    finally:
        pygame.time.get_ticks = real_ticks
        for nama in modul:
            try:
                importlib.import_module("heroes.%s_fx" % nama).reset_all()
            except Exception:
                pass
        feel.reset()


def main():
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print("OK  - %s" % name)
    print("\nHASIL: LULUS %d tes (starter + mini/true boss level 1 & 2)."
          % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
