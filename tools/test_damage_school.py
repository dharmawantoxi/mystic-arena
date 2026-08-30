#!/usr/bin/env python3
"""Regresi SPLIT PHYSICAL vs MAGIC (damage school) - Mystic Arena.

Menguji:
  1. hero_archetypes: catalog terisi + fallback aman + override dmg_type
  2. Hero: dmg_school diambil dari katalog, basic attack melee meneruskan
     sekolah ke target
  3. Boss: armor menahan fisik, magic_resist menahan sihir (di atas
     resilience 20/30% yang lama, di bawah anti-burst cap)
  4. Tower: armor kecil menahan fisik, magic lolos
  5. Minion: armor/magic_resist per jenis + interaksi armor_shred
  6. Interaksi lama TIDAK berubah: Wind Wall (proyektil fisik dipantulkan,
     proyektil sihir tembus), Sylara Windrun, damage 'fire' kebal armor
  7. resolve_damage_school: source=None + context hanya untuk target hero

Jalankan:  python3 tools/test_damage_school.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import _core                                   # noqa: F401  (hindari
import _entity as E                             # circular import)
import hero_archetypes
from bosses.base_boss import Boss


PASS = []


def check(cond, msg):
    if not cond:
        raise AssertionError("GAGAL: %s" % msg)
    PASS.append(msg)


# ── 1. katalog arketipe ────────────────────────────────────────────
def test_catalog():
    arche = hero_archetypes.ARCHETYPES
    check(len(arche) >= 200, "katalog punya %d hero (>=200)" % len(arche))
    for ht in ("kaizen", "grimjaw", "thorne", "sylara"):
        check(hero_archetypes.school_of(ht) == "physical",
              "%s = physical" % ht)
    for ht in ("vex", "zephyr", "morgath", "gornak"):
        check(hero_archetypes.school_of(ht) == "magic",
              "%s = magic" % ht)
    # hero baru tanpa entri -> fisik (tidak pernah kebal armor)
    check(hero_archetypes.school_of("boss_yang_belum_ada") == "physical",
          "hero tanpa entri -> fallback physical")
    # override manual di hero_unlock menang
    check(hero_archetypes.school_of(
        "kaizen", {"dmg_type": "MAGIC"}) == "magic",
        "override dmg_type manual menang")
    unknown_types = [
        ht for ht in arche if ht not in (
            "kaizen", "grimjaw", "sylara", "vex", "thorne", "zephyr")
        and not str(ht).islower()]
    check(not unknown_types,
          "key hero_type semua lowercase: %s" % unknown_types[:5])


# ── 2. Hero membaca sekolah ───────────────────────────────────────
def _mk_hero(hero_type, team="blue", x=100.0, y=100.0):
    E.set_damage_school(None)
    return E.Hero(hero_type, team, x=x, y=y)


def test_hero_school():
    k = _mk_hero("kaizen")
    m = _mk_hero("vex")
    check(k.dmg_type == "PHYSICAL" and k.dmg_school == "physical",
          "Kaizen hero: dmg_school=physical")
    check(m.dmg_type == "MAGIC" and m.dmg_school == "magic",
          "Vex hero: dmg_school=magic")

    class Dummy:
        alive = True
        team = "red"
        x, y = 140.0, 100.0
        hp = 10 ** 9
        max_hp = 10 ** 9
        radius = 10
        items = None

        def __init__(self):
            self.hits = []

        def take_damage(self, dmg, team, damage_type="normal",
                        source=None, school=None):
            self.hits.append((dmg, damage_type, school))

    for hero, want in ((k, "physical"), (m, "magic")):
        d = Dummy()
        hero.target = d
        hero.attack_timer = 0
        hero.skill_timer = 0
        hero.no_attack_timer = 0
        hero.projectiles.clear()
        hero.update([], [], [])
        if getattr(hero, "is_melee_hero", False):
            check(d.hits and d.hits[0][2] == want,
                  "basic attack melee %s -> school=%s" % (hero.name, want))
        else:
            # ranged: damage dibawa projectile, cek sekolah yang ikut
            # dibawa proyektilnya (dipakai saat mengenai target).
            pr = [p for p in hero.projectiles if p.get("alive")
                  and p["target"] is d]
            check(pr and pr[0]["school"] == want,
                  "basic attack ranged %s -> projectile school=%s" % (
                      hero.name, want))


# ── 3. Boss: armor vs magic_resist ────────────────────────────────
def _mk_boss(boss_type="gornak", hp=None):
    b = Boss(boss_type)
    if hp:
        b.max_hp = hp
        b.hp = hp
    return b


def test_boss_mitigation():
    b = _mk_boss()
    b.max_damage_per_hit = 10 ** 9          # matikan cap untuk uji ini
    armor, mr, res = b.armor, b.magic_resist, b.damage_reduction
    check(armor > 0 and 0 < mr < 1,
          "gornak punya armor=%s magic_resist=%s" % (armor, mr))

    start = b.hp
    b.take_damage(1000, "blue", damage_type="normal", school="physical")
    got_phys = start - b.hp
    b.hp = start
    b.take_damage(1000, "blue", damage_type="normal", school="magic")
    got_magic = start - b.hp

    exp_phys = int(round(round(1000 * (1 - armor * 0.06 /
                                       (1 + armor * 0.06)), 0)
                         * (1 - res)))
    exp_magic = int(round(round(1000 * (1 - mr), 0) * (1 - res)))
    check(abs(got_phys - exp_phys) <= 1,
          "fisik vs boss = %d (harapan %d, armor %d%%)" % (
              got_phys, exp_phys, round(armor * 0.06 /
                                        (1 + armor * 0.06) * 100)))
    check(abs(got_magic - exp_magic) <= 1,
          "sihir vs boss = %d (harapan %d, MR %d%%)" % (
              got_magic, exp_magic, round(mr * 100)))
    check(got_phys != got_magic,
          "armor & MR menghasilkan mitigasi BERBEDA per sekolah")

    # tanpa sekolah -> persis perilaku lama (hanya resilience)
    b.hp = start
    b.take_damage(1000, "red")
    check(start - b.hp == int(1000 * (1 - res)),
          "damage tanpa sekolah (boss/menara) = perilaku lama")

    # 'fire' tidak boleh ikut mitigasi sekolah
    b.hp = start
    b.take_damage(1000, "blue", damage_type="fire", school=None)
    check(start - b.hp == int(1000 * (1 - res)),
          "damage api: hanya resilience (paritas lama)")


def test_boss_anti_burst_still_wins():
    b = _mk_boss()
    b.hp = b.max_hp
    b.take_damage(10 ** 7, "blue", school="magic")
    check(b.hp >= b.max_hp - b.max_damage_per_hit,
          "cap anti-burst tetap membatasi satu pukulan (%d HP)" %
          b.max_damage_per_hit)


# ── 4/5. Tower & Minion ───────────────────────────────────────────
def test_tower_and_minion():
    t = E.Tower("archer", "red", 200, 200)
    check(t.armor > 0, "tower punya armor=%s" % t.armor)

    def pool(u):
        # shield menyerap duluan -> ukur total pool
        return u.hp + getattr(u, "shield", 0)

    hpp = pool(t)
    t.take_damage(100, "blue", damage_type="normal", school="physical")
    got_p = hpp - pool(t)
    t.take_damage(100, "blue", damage_type="normal", school="magic")
    got_m = hpp - got_p - pool(t)
    check(got_p < got_m,
          "tower: fisik %d < sihir %d (armor menahan fisik saja)" % (
              got_p, got_m))

    m = E.Minion("troll", "red", "mid")
    check(m.armor > 0, "troll minion armor=%s" % m.armor)
    hpp = m.hp
    m.take_damage(100, "blue", school="physical")
    got_p = hpp - m.hp
    m.hp = hpp
    m.take_damage(100, "blue", school="magic")
    got_m = hpp - m.hp
    check(got_p < got_m,
          "troll: fisik %d < sihir %d" % (got_p, got_m))

    u = E.Minion("undead", "red", "mid")
    check(u.armor == 0 and u.magic_resist > 0,
          "undead: armor 0, MR %s (rentan fisik, tahan sihir)" %
          u.magic_resist)

    # armor_shred Corroder harus mengurangi armor efektif minion
    g = E.Minion("troll", "red", "mid")
    g.armor_shred_amount = 2.0
    hpp = g.hp
    g.take_damage(100, "blue", school="physical")
    shred_p = hpp - g.hp
    g2 = E.Minion("troll", "red", "mid")
    hpp = g2.hp
    g2.take_damage(100, "blue", school="physical")
    check(shred_p > (hpp - g2.hp),
          "armor_shred Corroder bikin damage fisik lebih besar "
          "(%d vs %d)" % (shred_p, hpp - g2.hp))


# ── 6. interaksi lama tidak berubah ───────────────────────────────
def test_interactions_preserved():
    k = _mk_hero("kaizen")
    k._wind_wall_timer = 60

    class T:
        alive = True
        team = "red"
        x, y = 100.0, 100.0
        hp = 1000
        max_hp = 1000
        radius = 10
        items = None

        def __init__(self):
            self.hits = []

        def take_damage(self, dmg, team, damage_type="normal",
                        source=None, school=None):
            self.hits.append((dmg, school))

    hp_before = k.hp
    k.take_damage(200, "red", damage_type="projectile", school="physical")
    check(k.hp == hp_before, "Wind Wall memantulkan proyektil FISIK")
    k.take_damage(200, "red", damage_type="projectile", school="magic")
    check(k.hp < hp_before, "Wind Wall TIDAK memantulkan proyektil SIHIR")

    s = _mk_hero("sylara")
    s._windrun_active = True
    hp_before = s.hp
    import random
    random.seed(1)
    s.take_damage(50, "red", damage_type="normal", school="magic")
    check(s.hp < hp_before, "Windrun tidak menolak damage sihir")

    # fire (cannon tower) tetap kebal armor-shred seperti dulu
    check(E.resolve_damage_school("fire", None, None) is None,
          "damage 'fire' tidak punya sekolah (mitigasi armor tidak ikut)")
    check(E.resolve_damage_school("normal", None, None,
                                  target_is_hero=False) is None,
          "source=None & tanpa context -> sekolah None (paritas lama)")


def test_context_scope():
    """Context hanya berlaku untuk target hero, bukan menara."""
    v = _mk_hero("vex")

    class TowerLike:
        alive = True
        team = "red"
        x, y = 100.0, 100.0
        hp = 1000
        max_hp = 1000
        armor = 10
        magic_resist = 0.0
        shield = 0
        no_damage_timer = 0

        def __init__(self):
            self.schools = []

        def take_damage(self, dmg, team, damage_type="normal",
                        source=None, school=None):
            self.schools.append(
                E.resolve_damage_school(damage_type, source, school,
                                        target_is_hero=False))

    E.set_damage_school(v)
    t = TowerLike()
    t.take_damage(50, "blue")
    check(t.schools == [None],
          "skill hero tanpa source tidak mengubah damage ke menara")
    E.set_damage_school(None)
    check(E.get_damage_school() is None, "context bisa dimatikan")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("  ok  %-32s (%d assert)" % (
            fn.__name__, len(PASS)))
    print("\n%d pemeriksaan lolos - split PHYSICAL/MAGIC aktif." % len(PASS))
