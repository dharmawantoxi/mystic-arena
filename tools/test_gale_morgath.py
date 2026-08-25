"""Uji fix bug: projectile attack Morgath hilang saat equip Gale Pike.

Akar masalah: ``_do_attack`` mengisi ``attack_timer`` dengan reload
EFEKTIF (base / attack-speed item), sedangkan renderer boss-hero
(Morgath beam petir) mendeteksi serangan dengan pola
``timer >= attack_cooldown - 1`` memakai ``attack_cooldown`` yang
masih menampilkan nilai BASE. Dengan item AS (Gale Pike +25 AS),
reload efektif 42 -> ~34, jadi ``34 >= 41`` tidak pernah benar ->
animasi serangan / projectile tidak pernah terpicu (HILANG).

Fix: Hero.attack_cooldown jadi property render-facing yang
mengembalikan snapshot reload efektif terakhir (lihat _entity.py).

Sekaligus cek nerf range Gale Pike (130 -> 90).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import _core  # noqa: E402,F401 (daftar alias legacy, pecah circular import)
from hero_items import ITEM_CATALOG  # noqa: E402
from _entity import Hero  # noqa: E402

# ── T1: nerf range Gale Pike ───────────────────────────────
rng = ITEM_CATALOG["gale_pike"]["stats"]["range_bonus"]
assert rng <= 90, f"range_bonus gale_pike masih terlalu besar: {rng}"
print(f"T1 OK  - Gale Pike range_bonus = {rng} (nerf dari 130)")

# ── T2: Morgath + Gale Pike -> cooldown render-facing sinkron ──
m = Hero("morgath", "blue", 400, 400)
assert m.skill_data.get("is_boss_hero"), "morgath harus boss hero"
assert m.range > 80, "morgath ranged (dapat range bonus item)"

base_cd = m.attack_cooldown
m.items.add("gale_pike")
assert m.items.get_attack_speed_mult() > 1.0

# Simulasikan _do_attack: set timer + snapshot efektif.
eff_cd = m._eff_attack_cd(m._base_attack_cd)
m.attack_timer = eff_cd
m._attack_cd_effective = eff_cd
assert eff_cd < base_cd, "item AS harus memperpendek reload"

# Pola deteksi renderer boss (_update_mor_attack_anim):
cooldown_seen = max(2, int(m.attack_cooldown))
timer_seen = int(m.timer)
assert timer_seen >= cooldown_seen - 1, (
    f"renderer tidak mendeteksi serangan: timer={timer_seen} "
    f"vs cooldown={cooldown_seen}")
print(f"T2 OK  - Morgath + Gale Pike: timer={timer_seen} >= "
      f"cooldown-1={cooldown_seen - 1} (beam terpicu; base={base_cd})")

# ── T3: tanpa item tetap sama seperti versi lama ──────────
m2 = Hero("morgath", "blue", 400, 400)
eff2 = m2._eff_attack_cd(m2._base_attack_cd)
m2.attack_timer = eff2
m2._attack_cd_effective = eff2
assert m2.attack_cooldown == m2._base_attack_cd == eff2
print("T3 OK  - tanpa item: attack_cooldown == base == reload")

# ── T4: skill buff AS (Warpath-style) tetap lewat base ─────
m3 = Hero("morgath", "blue", 400, 400)
old = m3.attack_cooldown
m3.attack_cooldown = max(15, int(m3._base_attack_cd / 1.5))  # buff
eff3 = m3._eff_attack_cd(m3._base_attack_cd)
m3.attack_timer = eff3
m3._attack_cd_effective = eff3
m3.attack_cooldown = old  # restore (save/restore skill)
assert m3._base_attack_cd == old
assert m3.attack_timer >= max(2, int(m3.attack_cooldown)) - 1
print("T4 OK  - buff/restore AS skill aman lewat _base_attack_cd")

print("\nSEMUA TES LULUS ✓")
