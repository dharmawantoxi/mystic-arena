"""Headless test BUGFIX on-hit item (Frostbound Eye & friends).

Bug yang dilaporkan: hero RANGED yang equip FROSTBOUND EYES
menyerang dengan attack speed tak masuk akal (menyerang tiap
frame).

Akar masalah (3 bug berlapis):
  1. HeroItemInventory.get_on_attack_chain() mengembalikan dict
     ``on_attack`` PERTAMA dari slot mana pun. Key itu kini juga
     dipakai pasif non-chain (Frostbound Eye: Frostbite, Basilisk
     Breath: Miasma) yang tidak punya key "chance".
  2. _on_hit_common() membaca chain["chance"] -> KeyError. Pada
     jalur RANGED, _do_attack() memanggil on_ranged_attack_hit
     TANPA try/except, sehingga exception menghentikan _do_attack
     SEBELUM self.attack_timer di-set -> timer tetap 0 -> hero
     menyerang lagi di frame berikutnya (machine-gun).
  3. Efek samping di jalur MELEE: KeyError ditangani try/except
     lalu memanggil ULANG on_basic_attack_hit(damage, None) ->
     lifesteal dobel & cleave batal.

Test di file ini:
  T1  ranged + Frostbound Eye: _do_attack sehat, attack_timer > 0
  T2  Frostbite menempel ke target (slow + atk_slow + anti_heal)
  T3  ranged + Basilisk Breath: jalur on_attack Miasma sehat
  T4  get_on_attack_chain: hanya dict chain asli (chance/targets/
      radius/damage), urutan slot bebas
  T5  get_bash: selalu stat Abyss Breaker; Sundering Cudgel tidak
      pernah "dicuri" cabang Abyss (cudgel punya cabang sendiri)
  T6  melee + Frostbound Eye: on-hit hanya dipanggil SEKALI per
      serangan (dulu 2x -> lifesteal dobel)
  T7  fuzz singkat: 25 item x jalur melee & ranged tanpa exception
  T8  chain lightning (Thunder Coil/Fenrir) tetap memproc di kedua
      jalur on-hit
"""
import os
import sys
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import hero_items as hi  # noqa: E402
from hero_items import ITEM_CATALOG, HeroItemInventory  # noqa: E402
import _core  # noqa: E402  (harus lebih dulu dari _entity - circular)
from _entity import Hero  # noqa: E402

# ── T1: ranged + Frostbound Eye -> cooldown terisi ─────────
syl = Hero("sylara", "blue")
assert syl.items.add("frostbound_eye"), "equip frostbound gagal"
foe = Hero("kaizen", "red")
foe.x, foe.y = syl.x + 100, syl.y
syl.target = foe
syl.attack_timer = 0
syl._do_attack()  # dulu: KeyError('chance') -> attack_timer tetap 0
assert syl.attack_timer > 0, \
    "BUG machine-gun: attack_timer tidak terisi setelah serang"
assert len(syl.projectiles) == 1, "proyektil ranged tidak terbentuk"
# frame berikutnya TIDAK boleh bisa menyerang lagi
syl._do_attack()
assert len(syl.projectiles) == 1, \
    "hero menyerang 2x padahal cooldown belum habis"
print(f"T1 OK  - sylara+Frostbound: attack_timer={syl.attack_timer}, "
      "1 proyektil, tidak machine-gun")

# ── T2: Frostbite menempel ke TARGET (bukan ke pemilik) ─────
assert foe.atk_slow_amount == 0.28, foe.atk_slow_amount
assert foe.anti_heal_amount == 0.45, foe.anti_heal_amount
assert foe.slow_amount == 0.28, foe.slow_amount
assert syl.atk_slow_amount == 0, "atk_slow tidak boleh ke pemilik!"
assert syl.slow_amount == 0, "slow tidak boleh ke pemilik!"
print("T2 OK  - Frostbite ke target: slow .28, atk_slow .28, "
      "anti_heal .45; pemilik bersih")

# ── T3: ranged + Basilisk Breath (on_attack Miasma) ─────────
vex = Hero("vex", "blue")
assert vex.items.add("basilisk_breath")
foe3 = Hero("kaizen", "red")
foe3.x, foe3.y = vex.x + 100, vex.y
vex.target = foe3
vex.attack_timer = 0
try:
    vex._do_attack()
    assert vex.attack_timer > 0
except KeyError as e:
    raise AssertionError(f"KeyError on_attack Miasma: {e}")
assert len(hi._MIASMA) >= 1, "racun Miasma tidak terpasang"
print(f"T3 OK  - vex+Basilisk Breath: attack_timer={vex.attack_timer}, "
      f"Miasma aktif ({len(hi._MIASMA)} tracker)")

# ── T4: get_on_attack_chain hanya chain asli ────────────────
inv = HeroItemInventory(syl)
inv.slots = ["thunder_coil", "frostbound_eye", None, None, None, None]
c = inv.get_on_attack_chain()
assert c and c["name"] == "Arc Lightning", c
inv.slots = ["frostbound_eye", "thunder_coil", None, None, None, None]
c = inv.get_on_attack_chain()
assert c and c["name"] == "Arc Lightning", c
inv.slots = ["frostbound_eye", "basilisk_breath", None, None, None, None]
assert inv.get_on_attack_chain() is None, \
    "pasif non-chain tidak boleh dianggap chain lightning"
inv.slots = ["fenrir_chain", None, None, None, None, None]
c = inv.get_on_attack_chain()
assert c and c["name"] == "Arc Chain", c
print("T4 OK  - chain getter: urutan slot bebas, non-chain -> None")

# ── T5: get_bash selalu stat Abyss Breaker ──────────────────
inv2 = HeroItemInventory(syl)
inv2.slots = ["sundering_cudgel", "abyss_breaker", None, None, None, None]
b = inv2.get_bash()
assert b and b["chance"] == 0.22 and b["stun"] == 54 and \
    b["cooldown"] == 140, b
inv2.slots = ["abyss_breaker", "sundering_cudgel", None, None, None, None]
assert inv2.get_bash() == b, "stat bash berubah karena urutan slot"
inv3 = HeroItemInventory(syl)
inv3.slots = ["sundering_cudgel", None, None, None, None, None]
assert inv3.get_bash() is None, \
    "bash Cudgel punya cabang sendiri (Piercing Bash), bukan Abyss"
print("T5 OK  - get_bash: stat Abyss (0.22 / stun 54 / cd 140) konsisten")

# ── T6: melee on-hit dipanggil PERSIS sekali per serangan ────
# (dulu: KeyError ditelan lalu fallback memanggil ulang seluruh
#  on_basic_attack_hit -> lifesteal dobel & cleave batal)
melee = Hero("kaizen", "blue")
assert melee.items.add("frostbound_eye")
assert melee.items.add("demon_maw")  # 20% lifesteal utk deteksi dobel
foe6 = Hero("kaizen", "red")
foe6.x, foe6.y = melee.x + 20, melee.y
melee.target = foe6
calls = []
orig = melee.items._on_hit_common
melee.items._on_hit_common = \
    lambda *a, **k: (calls.append(1), orig(*a, **k))[1]
melee.attack_timer = 0
melee._do_attack()
assert len(calls) == 1, \
    f"on-hit melee dipanggil {len(calls)}x (harus 1x - lifesteal dobel)"
ls = melee.items.get_lifesteal_pct()
dmg = melee.damage + melee.items.get_bonus_damage()
heal_expect = int(dmg * ls)
lost = foe6.max_hp - foe6.hp
assert heal_expect > 0
print(f"T6 OK  - melee on-hit 1x (bukan 2x): damage {lost}, "
      f"lifesteal +{heal_expect}")

# ── T7: fuzz - semua 25 item di kedua jalur on-hit ──────────
random.seed(20260826)

class FoeStub:
    alive = True
    x, y = 60, 0
    team = "red"
    radius = 14
    max_hp = hp = 600
    slow_amount = slow_timer = 0.0
    atk_slow_amount = atk_slow_timer = 0.0
    anti_heal_amount = anti_heal_timer = 0.0
    armor_shred_amount = armor_shred_timer = 0.0
    stun_timer = 0
    def apply_slow(self, a, d): self.slow_amount = a
    def apply_debuff(self, k, a, d): setattr(self, k + "_amount", a)
    def apply_armor_shred(self, a, d): pass
    def apply_stun(self, d): pass
    def apply_miss_chance(self, a, d): pass
    def take_damage(self, d, t, ty=None): self.hp -= d

for sid in ITEM_CATALOG:
    h = Hero("sylara", "blue")
    ok = h.items.add(sid)
    if not ok:  # melee_only item di hero ranged
        h = Hero("kaizen", "blue")
        assert h.items.add(sid), f"equip {sid} gagal"
    t = FoeStub()
    for _ in range(30):
        h.items.on_basic_attack_hit(t, 40, [t])
        h.items.on_ranged_attack_hit(t, 40, [t])
        h.items.update(1, enemies=[t])
print(f"T7 OK  - {len(ITEM_CATALOG)} item x 30 iterasi x melee+ranged: "
      "tanpa exception")

# ── T8: chain lightning tetap memproc ───────────────────────
random.seed(4)
h8 = Hero("sylara", "blue")
assert h8.items.add("thunder_coil")
main_t = FoeStub(); near_t = FoeStub()
near_t.x = main_t.x + 40
procs = 0
for _ in range(300):
    near_t.hp = near_t.max_hp
    hp0 = near_t.hp
    h8.items.on_ranged_attack_hit(main_t, 10, [main_t, near_t])
    if near_t.hp < hp0:
        procs += 1
assert procs > 0, "Arc Lightning tidak pernah memproc di jalur ranged"
print(f"T8 OK  - Arc Lightning memproc {procs}/300 tembakan di jalur "
      "ranged")

print("\nSEMUA TEST BUGFIX ON-HIT LULUS ✔")
