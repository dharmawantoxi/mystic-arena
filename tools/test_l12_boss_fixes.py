#!/usr/bin/env python3
"""Uji regresi perbaikan: starter hero + mini/true boss Level 1-2.

Mengunci bug yang ditemukan audit 2026-09-02:
  1. Razak deadlock kiting (prefer_distance > range -> boss diam di
     zona 55..60 dan tidak pernah menyerang).
  2. Dispatch smart-AI hanya di dalam range -> skill gap-close/utility
     (Abaddon E, Gornak W, Razak E, Khalros E, Gorath E) tidak pernah
     menyala (dead branch).
  3. Buff self-damage hero boss (Drakar Q, Alchemist E, Gorath Q,
     Dragon Form/Blood, Nyxarath W, Syrentha E, Thalgryn E) memakai
     damage base level 1 dan reset ke base level 1 -> damage turun
     permanen setelah buff habis.
  4. Hero razak/khalros/gorath tidak punya registry skill
     (BossHeroSkills._SKILL_REGISTRY) -> semua skill jatuh ke
     fallback generik.
  5. Renderer morvaeth2 (mini boss level 42) tidak terindeks
     (215/216) -> body generic.
  6. Mini boss enemy (Boss) memakai multiplier enrage 1.25 di
     _get_boss_stats padahal frenzy mini = 1.20.
  7. _try_spawn_pending_mini_boss bisa membuang boss mati yang
     reward-nya belum diproses (game speed > 1).
  8. Overlay debug Alchemist memanggil _debug_font tanpa namespace
     (NameError -> teks debug tidak pernah tampil).

Jalankan: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
          python3 tools/test_l12_boss_fixes.py
"""
import inspect
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "0")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import _core  # noqa: E402
from _core import Game  # noqa: E402
from _entity import Hero, Minion, Tower, Castle  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402
from bosses import boss_data  # noqa: E402
from bosses._boss_index import BOSS_INDEX  # noqa: E402
from hero_skills import get_skill_handler  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL {name}" + (f"  ({detail})" if detail else ""))


class Dummy:
    """Dummy enemy yang bisa dijadikan target boss/hero."""

    def __init__(self, x, y, hp=10 ** 9, team="blue"):
        self.x = float(x)
        self.y = float(y)
        self.alive = True
        self.team = team
        self.hp = hp
        self.max_hp = hp
        self.radius = 20
        self.damage = 5
        self.attack_cooldown = 100
        self.timer = 0
        self.range = 120
        self.attack_timer = 0
        self.hits = []

    def take_damage(self, dmg, team, **kw):
        self.hp -= dmg
        self.hits.append(dmg)

    def apply_slow(self, amount, duration):
        pass


def dummy_boss(bt, x, y):
    b = Boss(bt, None)
    b.x = float(x)
    b.y = float(y)
    b.entrance_timer = 0
    b.direction = -1
    b.waypoint_index = -1
    return b


def fresh_game(level):
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


# ── 1. Razak deadlock kite ──────────────────────────────────────
def test_razak_kite_deadlock():
    b = dummy_boss("razak", 600, 300)
    t = Dummy(600 - 58, 300)
    skill_taunts = set()
    for _ in range(900):
        b.update([t], [], [])
        s = getattr(b, "active_skill", None)
        if s:
            skill_taunts.add(s)
    attack_total = sum(t.hits)
    check("razak attack saat jarak 58 (deadlock hilang)",
          len(t.hits) > 0, f"hits={len(t.hits)} damage={attack_total}")
    check("razak cast skill saat jarak 58",
          bool(skill_taunts), f"skills={sorted(skill_taunts)}")


# ── 2. Smart AI gap-close menyala di luar range ─────────────────
def _boss_sees_skill(bt, dist, expect, frames=1500):
    b = dummy_boss(bt, 600, 300)
    t = Dummy(600 - dist, 300)
    seen = set()
    for _ in range(frames):
        b.update([t], [], [])
        s = getattr(b, "active_skill", None)
        if s:
            seen.add(s)
        if expect in seen:
            return True, sorted(seen)
    return expect in seen, sorted(seen)


def test_smart_ai_gap_close():
    cases = [
        ("abaddon", "e", 140),
        ("gornak", "w", 150),
        ("razak", "e", 180),
        ("khalros", "e", 160),
        ("gorath", "e", 140),
    ]
    for bt, key, dist in cases:
        ok, seen = _boss_sees_skill(bt, dist, key)
        check(f"{bt} smart AI {key.upper()} menyala di luar range",
              ok, f"skills={seen}")


# ── 3. Buff hero tidak menghilangkan multiplier level ───────────
def _hero_cast(ht, key, level=4):
    h = Hero(ht, "blue", 400, 300)
    h.level = level
    h._apply_level_stats()
    e = Dummy(400 + 60, 300, team="red")
    units = [e]
    towers = []
    bases = [Castle(_core.BLUE_BASE_X, _core.BLUE_BASE_Y, "blue")]
    casted = h.cast_skill(units, towers, bases, key)
    return h, e, casted, units, towers, bases


def test_buff_keeps_level_scaling():
    cases = [
        ("drakar", "q", 1.5, 320),     # Battle Hunger rage
        ("alchemist", "e", 1.5, 380),  # Chemical Rage
        ("gorath", "q", 1.4, 320),     # Bloodrage (baru)
    ]
    for ht, key, mult, frames in cases:
        h, e, casted, units, towers, bases = _hero_cast(ht, key)
        lvl = _core.HERO_LEVELS[h.level]["dmg_mult"]
        base = int(h.base_damage * lvl)
        want_buffed = int(base * mult)
        check(f"{ht} {key} buff = damage level saat ini x{mult}",
              casted and h.damage == want_buffed,
              f"dmg={h.damage} want={want_buffed} (base lvl1={_core.get_all_hero_types()[ht]['damage']})")
        for _ in range(frames):
            h.skills.update_timers(units, towers, bases)
        check(f"{ht} {key} reset ke damage level (bukan base lvl1)",
              h.damage == base and not getattr(h, "rage_active", False),
              f"dmg={h.damage} want={base}")


# ── 4. Registry skill hero razak/khalros/gorath ─────────────────
def test_l2_boss_hero_skill_registry():
    from hero_skills._bundle import _NS_boss_hero_skills as NSB  # noqa
    reg = NSB.BossHeroSkills._SKILL_REGISTRY
    for ht in ("razak", "khalros", "gorath"):
        recipe = reg.get(ht)
        check(f"{ht} terdaftar di _SKILL_REGISTRY",
              recipe is not None and len(recipe) == 4, f"{recipe}")
        if recipe:
            for key, mname in recipe.items():
                check(f"{ht}.{key} -> {mname} ada",
                      callable(getattr(
                          NSB.BossHeroSkills, mname, None)))
    # cast nyata: tiap hero bisa cast Q/W/E/R tanpa fallback
    for ht, key in [("razak", "q"), ("razak", "r"),
                    ("khalros", "w"), ("gorath", "r")]:
        h, e, casted, units, towers, bases = _hero_cast(ht, key)
        check(f"{ht} hero cast {key} berhasil",
              casted and h.active_skill == key,
              f"active={h.active_skill} dmg_dealt={sum(e.hits)}")


# ── 5. Renderer morvaeth2 terindeks ─────────────────────────────
def test_morvaeth2_renderer():
    entry = BOSS_INDEX.get("morvaeth2")
    check("morvaeth2 terindeks di _boss_index.py", entry is not None,
          f"{entry}")
    missing = [k for k in list(boss_data.MINI_BOSS_TYPES)
               + list(boss_data.TRUE_BOSS_TYPES) if k not in BOSS_INDEX]
    check("semua boss terindeks (216/216)", not missing,
          f"missing={missing}")
    if entry:
        import importlib
        mod = importlib.import_module("bosses." + entry[0])
        fn = getattr(mod, entry[1], None)
        b = dummy_boss("morvaeth2", 300, 300)
        surf = pygame.Surface((460, 460), pygame.SRCALPHA)
        try:
            fn(surf, b, 230, 230)
            ok = True
        except Exception as exc:
            ok = False
            detail = f"{type(exc).__name__}: {exc}"
        check("draw_morvaeth2 render tanpa exception", ok,
              detail if not ok else "")


# ── 6. Enrage multiplier mini boss 1.20 ────────────────────────
def test_mini_enrage_mult():
    b = dummy_boss("gornak", 600, 300)
    b.is_enraged = True
    stats = b._get_boss_stats()
    raw = boss_data.get_all_boss_types()["gornak"]
    q = stats.get("skill_q_damage", raw.get("skill_q_damage"))
    check("mini boss enrage = x1.20 pada damage skill",
          q == int(raw["skill_q_damage"] * 1.20),
          f"q={q} raw={raw['skill_q_damage']}")

    t = dummy_boss("abaddon", 600, 300)
    t.is_enraged = True
    ts = t._get_boss_stats()
    traw = boss_data.get_all_boss_types()["abaddon"]
    check("true boss enrage = x1.25 pada damage skill",
          ts.get("skill_q_damage") == int(traw["skill_q_damage"] * 1.25),
          f"q={ts.get('skill_q_damage')} raw={traw['skill_q_damage']}")


# ── 7. Pending mini boss tidak dibuang ──────────────────────────
def test_pending_mini_boss_preserved():
    g = fresh_game(1)
    b = dummy_boss("gornak", 600, 300)
    b.alive = False
    b.defeated = True          # belum diproses reward/unlock
    g.active_boss = b
    g.pending_mini_bosses = [(99, "morgath")]
    g._try_spawn_pending_mini_boss()
    check("boss mati-belum-diproses tetap jadi active_boss",
          g.active_boss is b,
          f"active={g.active_boss}")
    g._process_boss_kill(b)
    # setelah diproses manual, boss berikutnya boleh menyusul
    g.active_boss = None
    g._try_spawn_pending_mini_boss()
    check("mini boss antrean menyusul setelah boss diproses",
          g.active_boss is not None
          and g.active_boss.boss_type == "morgath")


# ── 8. Overlay debug Alchemist ──────────────────────────────────
def test_alchemist_debug_overlay():
    import bosses.level2 as L
    NS = L._NS_alchemist
    src = inspect.getsource(NS._draw_alch_debug)
    check("overlay debug memakai _NS_alchemist._debug_font()",
          "_NS_alchemist._debug_font()" in src)
    from types import SimpleNamespace
    b = SimpleNamespace(
        boss_type="alchemist", boss_class="true", x=230.0, y=230.0,
        direction=1, facing=1, pulse=1.2, timer=0, attack_cooldown=50,
        active_skill="q", active_skill_timer=30, target=None,
        _render_scale=1.0, hurt_flash_timer=0, alive=True, radius=30,
        hp=20000, max_hp=20000, rage_active=False, defense_boost=False)
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    NS.DEBUG_CHARACTER = True
    try:
        L.draw_alchemist(surf, b, 230, 230)
        ok = True
        detail = ""
    except Exception as exc:
        ok = False
        detail = f"{type(exc).__name__}: {exc}"
    finally:
        NS.DEBUG_CHARACTER = False
    check("draw_alchemist mode debug tanpa exception", ok, detail)


def main():
    test_razak_kite_deadlock()
    test_smart_ai_gap_close()
    test_buff_keeps_level_scaling()
    test_l2_boss_hero_skill_registry()
    test_morvaeth2_renderer()
    test_mini_enrage_mult()
    test_pending_mini_boss_preserved()
    test_alchemist_debug_overlay()
    print(f"\nHASIL: {PASS} PASS, {FAIL} FAIL")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
