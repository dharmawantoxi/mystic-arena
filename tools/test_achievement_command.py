"""Uji achievement rework + command ATTACK DAMAGE DEALER (headless).

Yang diuji:
  T1  Damage tracking: hero.damage_dealt terakumulasi saat hero
      menyerang hero/minion/boss (source= hero).
  T2  Achievement HERO KILL HERO: pukulan terakhir hero biru pada
      hero merah -> achievement + kills.
  T3  Achievement hero kill MINI BOSS & TRUE BOSS.
  T4  Achievement lama (wave/gold/kill minion/combo/first blood)
      TIDAK pernah muncul lagi.
  T5  Kill oleh tower/minion (source bukan hero) TIDAK dihitung.
  T6  Command ATTACK DAMAGE DEALER: semua hero biru mengunci
      follow_target ke hero musuh dengan damage_dealt terbesar.
  T7  Notifikasi dihapus: add_notification & beri_tahu_global
      no-op, achievement tetap tampil di map (queue popup).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import _core  # noqa: E402,F401 (alias legacy, pecah circular import)
from game import Game  # noqa: E402
from _entity import Hero, Minion  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402

screen = pygame.display.set_mode((1280, 720))
g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None

# Pemanasan singkat supai sistem siap.
for _ in range(30):
    g.update()

LAMA = {"first_blood", "10_kills", "50_kills", "100_kills", "250_kills",
        "combo_5", "combo_10", "combo_20", "wave_5", "wave_10",
        "wave_20", "gold_1000", "gold_5000"}

# ── T1: damage tracking ────────────────────────────────────
# Hero biru di-summon manual (di awal level pemain belum memilih).
h1 = Hero("kaizen", "blue", 400, 360)
h2 = Hero("sylara", "blue", 420, 380)
g.heroes += [h1, h2]
musuh = Hero("thorne", "red", 500, 360)
g.ai.heroes.append(musuh)
d0 = h1.damage_dealt
musuh.take_damage(120, "blue", source=h1)
assert h1.damage_dealt >= d0 + 120, \
    f"damage_dealt tidak tercatat: {h1.damage_dealt} (dari {d0})"
print(f"T1 OK  - damage_dealt {d0} -> {h1.damage_dealt}")

# ── T2: hero kill hero ─────────────────────────────────────
musuh.take_damage(99999, "blue", source=h1)
for _ in range(3):
    g.update()
assert not musuh.alive
assert h1.kills == 1, f"kills hero: {h1.kills}"
assert g.hero_kill_count == 1
assert "hero_kill_1" in g.achievements_unlocked, \
    g.achievements_unlocked
# Popup achievement tampil di map (queue renderer, bukan panel)
assert g.effects.achievement.queue or \
    g.effects.achievement.current
print("T2 OK  - HERO SLAYER tercatat & popup di map")

# ── T3: hero kill mini boss & true boss ────────────────────
lane = g.map_renderer.get_lane_path("mid")
for cls, expect, label in ((Boss("gornak", lane), "miniboss_kill_1",
                            "MINI BOSS"),
                           (Boss("abaddon", lane), "trueboss_kill_1",
                            "TRUE BOSS")):
    g.active_boss = cls
    cls.entrance_timer = 0
    while cls.alive:
        cls.take_damage(99999, "blue", source=h1)
    assert getattr(cls, "_killed_by", None) is h1
    # Gameplay ter-pause selama animasi kematian boss aktif -
    # tunggu sampai blok kematian benar-benar diproses game.
    for _ in range(1200):
        g.update()
        if g.active_boss is None:
            break
    assert expect in g.achievements_unlocked, \
        f"{label}: {g.achievements_unlocked}"
    g.active_boss = None
print(f"T3 OK  - MINI BOSS & TRUE BOSS Slayer tercatat "
      f"(kills hero={h1.kills})")
assert h1.kills >= 3

# ── T4: achievement lama tidak muncul ──────────────────────
g.gold = 99999
g.wave_number = 20
for _ in range(30):
    g.update()
assert not (LAMA & g.achievements_unlocked), \
    f"achievement lama masih muncul: {LAMA & g.achievements_unlocked}"
print("T4 OK  - achievement wave/gold/kill/combo tidak muncul")

# ── T5: kill tanpa hero (tower) tidak dihitung ─────────────
m_kredit = getattr(g, "hero_kill_count", 0)
m2 = Hero("kaizen", "red", 500, 360)
g.ai.heroes.append(m2)
m2.take_damage(99999, "blue", source=None)   # tanpa source (tower)
for _ in range(3):
    g.update()
assert not m2.alive
assert g.hero_kill_count == m_kredit, \
    f"kill tanpa hero dihitung: {g.hero_kill_count}"
print("T5 OK  - kill oleh tower/minion tidak dihitung")

# ── T6: command ATTACK DAMAGE DEALER ───────────────────────
dealer1 = Hero("vex", "red", 700, 300)
dealer2 = Hero("zephyr", "red", 720, 320)
g.ai.heroes += [dealer1, dealer2]
# dealer2 memberi damage terbanyak ke unit biru
h2.take_damage(80, "red", source=dealer2)
assert dealer2.damage_dealt > dealer1.damage_dealt
g.tactical.cooldown = 0
ok = g.tactical.command_attack_damage_dealer()
assert ok, "command gagal dijalankan"
hidup = [h for h in g.heroes if h.alive]
assert hidup, "tidak ada hero biru hidup"
assert all(h.follow_target is dealer2 for h in hidup), \
    [(h.name, h.follow_target) for h in hidup]
print(f"T6 OK  - {len(hidup)} hero fokus ke {dealer2.name} "
      f"(damage terbanyak)")

# Konstanta command terdaftar (tombol panel diuji lengkap di
# tools/test_sidepanel.py - perlu panggung layar 1624x720).
from tactical_commands import TacticalCommand  # noqa: E402
assert TacticalCommand.ATTACK_DAMAGE_DEALER == "attack_damage_dealer"
print("T6b OK - konstanta command terdaftar (tombol: test_sidepanel)")

# ── T7: notifikasi no-op ───────────────────────────────────
from mobile import sidepanel as sp  # noqa: E402
assert sp.beri_tahu_global("tes") is False
assert sp.catat_kill_global("A", "B") is False
g.ui.add_notification("tes notifikasi")
comp = getattr(g.ui, "notification_component", None)
if comp is not None:
    assert comp.messages == [], comp.messages
print("T7 OK  - notifikasi no-op (panel diisi command saja)")

print("\nSEMUA TES LULUS ✓")
