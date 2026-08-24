"""Uji integrasi in-game: jalankan Game headless dengan hero yang
memakai item TIER II + AI yang membeli item Tier II. Memastikan
tidak ada crash di loop gameplay (update_auras, on-hit, stun, zap,
shred, amp) selama pertarungan berlangsung."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import _core  # noqa: E402,F401 (mendaftarkan alias legacy "game")
from game import Game  # noqa: E402
from hero_items import ITEM_CATALOG  # noqa: E402

TIER2 = {"scarlet_bulwark", "monarch_wings", "corroder", "tempest_vane",
         "fenrir_chain", "sanguine_thorn", "abyss_breaker", "thunder_coil"}

screen = pygame.display.set_mode((1280, 720))
g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None

# Warmup singkat
for _ in range(300):
    g.update()

# Summon 2 hero pemain (melee + ranged) dan pakaikan item Tier II
g.gold = 999999
g.purchased_heroes += ["kaizen", "sylara"]
g.try_buy_hero("kaizen")
g.try_buy_hero("sylara")
assert len(g.heroes) == 2
g.heroes[0].items.add("scarlet_bulwark")
g.heroes[0].items.add("abyss_breaker")
g.heroes[0].items.add("monarch_wings")
g.heroes[1].items.add("sanguine_thorn")
g.heroes[1].items.add("thunder_coil")
g.heroes[1].items.add("corroder")
g.heroes[1].items.add("tempest_vane")

# Dorong hero ke tengah peta supaya bertarung
for h in g.heroes:
    h.x, h.y = 640, 360

# AI kaya supaya membeli item (termasuk Tier II dari suggest pool)
g.ai.gold = 60000

FRAMES = 3000
for i in range(FRAMES):
    g.update()
    g.draw()

# ── Verifikasi ──
all_h = g.get_all_heroes()
owned_t2 = set()
for h in all_h:
    inv = getattr(h, "items", None)
    if inv is None:
        continue
    for s in inv.slots:
        if s in TIER2:
            owned_t2.add(s)
print("hero total:", len(all_h))
print("item Tier II dimiliki (player+AI):", sorted(owned_t2))
assert owned_t2, "tidak ada item Tier II yang terpakai sama sekali"

# Item player masih berfungsi (timer pernah jalan / stat aktif)
inv0 = g.heroes[0].items if g.heroes[0].alive else None
inv1 = g.heroes[1].items if len(g.heroes) > 1 and g.heroes[1].alive else None
print("kaizen hidup:", bool(inv0), "| sylara hidup:", bool(inv1))

# Efek mekanik terlihat selama sim: minimal salah satu trigger pernah
# aktif tidak wajib (probabilistik) - tapi stat getter harus konsisten.
for h in g.heroes:
    if not h.alive:
        continue
    inv = h.items
    assert 0.0 <= inv.get_evasion() <= 0.5
    assert inv.get_attack_speed_mult() >= 1.0
    assert inv.get_max_hp() > 0

print(f"\nIN-GAME OK - {FRAMES} frame pertarungan dengan item "
      f"Tier II tanpa crash ✔")
