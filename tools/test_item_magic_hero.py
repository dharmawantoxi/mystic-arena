"""Headless test item atribut MAGIC: Astral Codex.

Mengetes:
  - integritas katalog (field lengkap, magic_only, ikon di disk)
  - is_magic_hero(): role magic dikenali, fisik & Anti-Mage ditolak
  - gate magic_only di inventory add() + toko _try_buy
  - getter stat baru get_skill_amp() (cap 0.5)
  - Arcane Nova: trigger >=2 musuh dekat -> damage + silence + CD
  - Skill Amp via Hero ASLI: property skill_damage naik 25%
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import hero_items as hi  # noqa: E402
from hero_items import (HeroItemInventory, ITEM_CATALOG,  # noqa: E402
                        ITEM_SHOP_ORDER, CATEGORY_INFO,
                        is_magic_hero, suggest_item_for_hero)

SID = "astral_codex"

# ── T1: integritas katalog ─────────────────────────────────────────
data = ITEM_CATALOG[SID]
assert SID in ITEM_SHOP_ORDER, "astral_codex belum ada di shop order"
assert data["category"] in CATEGORY_INFO, "kategori belum terdaftar"
for k in ("name", "cost", "icon", "color", "glow", "stats", "active",
          "desc", "desc_en", "flavor", "category"):
    assert k in data, f"kurang field {k}"
assert data.get("magic_only") is True, "harus magic_only"
assert data["stats"].get("skill_amp", 0) > 0, "harus punya skill_amp"
icon_path = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "assets", "items", data["icon"])
assert os.path.exists(icon_path), "ikon astral_codex.png tidak ada"
assert pygame.image.load(icon_path).get_width() >= 256, "ikon < 256px"
print("T1 OK  - katalog Astral Codex lengkap + ikon 256px di disk")


# ── T2: is_magic_hero() ────────────────────────────────────────────
class FakeHero:
    def __init__(self, name, role="", rng=40):
        self.name = name
        self.role = role
        self.level = 3
        self.color = (90, 160, 255)
        self.alive = True
        self.range = rng
        self.team = "blue"
        self.damage = 35
        self.base_hp = 800
        self.max_hp = 800
        self.hp = 800
        self.x = 100
        self.y = 100
        self.items = HeroItemInventory(self)


assert is_magic_hero(FakeHero("Vex", "Mage"))
assert is_magic_hero(FakeHero("Zephyr", "Mage/Trickster"))
assert is_magic_hero(FakeHero("Vhaerith", "Boss/Magic"))
assert is_magic_hero(FakeHero("S", "Boss/Frost Sorcerer"))
assert is_magic_hero(FakeHero("W", "Boss/Warlock"))
assert is_magic_hero(FakeHero("C", "True Boss/Cosmic Mage"))
assert not is_magic_hero(FakeHero("Kaizen", "Assassin"))
assert not is_magic_hero(FakeHero("Thorne", "Bruiser"))
assert not is_magic_hero(FakeHero("AM", "Boss/Anti-Mage")), \
    "Anti-Mage bukan hero magic"
assert not is_magic_hero(FakeHero("NoRole", ""))
print("T2 OK  - is_magic_hero: mage/sorcerer/warlock diterima, "
      "fisik & Anti-Mage ditolak")

# ── T3: gate magic_only di inventory.add() ─────────────────────────
mage = FakeHero("Vex", "Mage")
assert mage.items.add(SID), "hero magic harus bisa memakai kodex"
assert mage.items.has(SID)

fighter = FakeHero("Grimjaw", "Fighter")
assert not fighter.items.add(SID), "hero fisik TIDAK boleh memakai"
assert not fighter.items.has(SID)

# Slot tidak termakan saat penambahan ditolak
assert fighter.items.used_slots() == 0
print("T3 OK  - add(): magic diterima, fisik ditolak, slot utuh")

# ── T4: getter skill amp (cap 0.5) ────────────────────────────────
assert abs(mage.items.get_skill_amp() - 0.25) < 1e-9
# Dobel (kalau 2 slot) harus ke-cap 0.5
mage.items.add(SID)
assert mage.items.get_skill_amp() == 0.5, "skill amp tidak ke-cap"
print("T4 OK  - get_skill_amp 0.25, ke-cap 0.5 saat dobel")

# ── T5: Arcane Nova trigger (damage + silence + cooldown) ──────────
class FakeEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True
        self.team = "red"
        self.taken = []
        self.debuffs = []

    def take_damage(self, dmg, team=None, dtype="normal"):
        self.taken.append(dmg)

    def apply_debuff(self, kind, amount, duration, **kw):
        self.debuffs.append((kind, amount, duration))

    def apply_slow(self, amount, duration):
        self.debuffs.append(("slow", amount, duration))


nova_mage = FakeHero("Vex", "Mage")
nova_mage.items.add(SID)
e1 = FakeEnemy(140, 100)   # dalam radius 260
e2 = FakeEnemy(100, 180)   # dalam radius 260
far = FakeEnemy(900, 900)  # di luar radius
nova_mage.items.update(1, enemies=[e1, e2, far])
act = ITEM_CATALOG[SID]["active"]
assert nova_mage.items.arcane_cd == act["cooldown"], "CD tidak ter-set"
assert e1.taken == [act["damage"]] and e2.taken == [act["damage"]]
assert not far.taken, "musuh jauh tidak boleh kena"
kinds = [d[0] for d in e1.debuffs]
assert "skill_down" in kinds, "silence (skill_down) tidak terpasang"
# Tidak boleh retrigger saat CD masih berjalan
nova_mage.items.update(1, enemies=[e1, e2])
assert len(e1.taken) == 1, "Nova retrigger saat CD masih jalan"
print("T5 OK  - Arcane Nova: 2 musuh kena 150 dmg + silence, CD aktif")

# ── T6: AI suggest - kodex diprioritaskan untuk hero magic ─────────
# (Vex/Zephyr adalah mage RANGED: rng=130 supaya tidak dikira melee)
sg = suggest_item_for_hero(FakeHero("Vex", "Mage", rng=130), set())
assert sg == SID, f"AI mage harus disarankan kodex dulu, dapat {sg}"
sg2 = suggest_item_for_hero(FakeHero("Vex", "Mage", rng=130), {SID})
# Pool mage kini diisi paket MAGIC duluan: setelah kodex, prioritas
# berikutnya adalah Fulgur Scepter.
assert sg2 == "fulgur_scepter", f"fallback mage aneh: {sg2}"
# Hero fisik tidak pernah disarankan item magic_only
pool_hit = set()
for _ in range(60):
    fh = FakeHero("Kaizen", "Assassin")
    s = suggest_item_for_hero(fh, pool_hit)
    pool_hit.add(s)
    if len(pool_hit) > 14:
        break
assert SID not in pool_hit, "hero fisik disarankan item MAGIC ONLY"
print("T6 OK  - AI: mage diprioritaskan kodex, fisik tidak pernah")

# ── T7: Hero ASLI - Skill Amp mengalikan skill_damage ──────────────
from _entity import Hero  # noqa: E402

vex = Hero("vex", "blue")
assert is_magic_hero(vex), "Vex harus dikenali sebagai hero magic"
base_sd = vex.skill_damage
assert base_sd > 0
assert vex.items.add(SID), "Vex gagal memakai Astral Codex"
amped = vex.skill_damage
expect = int(round(base_sd * 1.25))
assert amped >= expect - 1, f"skill amp tidak bekerja: {amped} < {expect}"
assert amped > base_sd
# CDR & spell vamp ikut teragregasi
assert abs(vex.items.get_cooldown_reduction() - 0.18) < 1e-9
assert abs(vex.items.get_spell_vamp() - 0.12) < 1e-9

# Hero fisik asli tetap ditolak
kaizen = Hero("kaizen", "blue")
assert not kaizen.items.add(SID), "Kaizen (Assassin) boleh memakai?!"
assert kaizen.items.get_skill_amp() == 0
print("T7 OK  - Hero asli: skill_damage Vex +25%, Kaizen ditolak")

print("\nSEMUA TEST ASTRAL CODEX LULUS ✓")
