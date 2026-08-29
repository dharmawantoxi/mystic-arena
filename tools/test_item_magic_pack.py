"""Headless test paket MAGIC (7 item atribut Magic).

Mengetes tiap mekanik dengan Hero ASLI (vex = Mage):
  - Semuanya magic_only: ditolak hero fisik, diterima hero magic
  - Sage Scepter   : stat skill_amp teragregasi
  - Fulgur Scepter : Energy Blast -> 300 magic dmg ke target + CD
  - Hex Idol       : Hexcraft -> stun + silence target + CD
  - Rift Veil      : Discord Field -> musuh kena +15% damage 6 dtk
  - Vital Stone    : Vitality Pact -> heal 25% Max HP saat kritis
  - Vine Rod       : Entangle -> root (slow total) on-hit + CD
  - Spectral Charm : Spectral Form -> evasion 1.0 saat HP kritis
  - Toko           : 5 halaman, halaman 4-5 berisi paket magic
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import hero_items as hi  # noqa: E402
from hero_items import (ITEM_CATALOG, ITEM_SHOP_ORDER, ITEMS_PER_PAGE,  # noqa: E402
                        ItemShopUI, is_magic_hero,
                        suggest_item_for_hero)
from _entity import Hero  # noqa: E402

MAGIC = ["sage_scepter", "fulgur_scepter", "hex_idol", "rift_veil",
         "vital_stone", "vine_rod", "spectral_charm"]


class FoeStub:
    """Musuh sederhana untuk tes auto-trigger."""

    def __init__(self, x=60, y=0):
        self.x = x
        self.y = y
        self.alive = True
        self.team = "red"
        self.radius = 14
        self.max_hp = self.hp = 2000
        self.slow_amount = 0.0
        self.stun_timer = 0
        self.dmg_amp_amount = 0.0
        self.debuffs = []
        self.taken = []

    def take_damage(self, d, t, ty="normal"):
        amp = 1.0 + (self.dmg_amp_amount if self.dmg_amp_amount else 0.0)
        self.hp -= int(round(d * (1.0 if ty == "ignore" else amp)))
        self.taken.append(d)

    def apply_slow(self, a, d):
        self.slow_amount = a

    def apply_stun(self, d):
        self.stun_timer = d

    def apply_debuff(self, k, a, d, **kw):
        self.debuffs.append((k, a, d))

    def apply_damage_amp(self, a, d):
        self.dmg_amp_amount = a


def _boss_hero(sid):
    """Hero vex magic dengan item terpasang, siap update()."""
    h = Hero("vex", "blue")
    assert h.items.add(sid), f"equip {sid} gagal di hero magic"
    return h


# ── T1: semua paket magic - magic_only & field lengkap ─────
for sid in MAGIC:
    d = ITEM_CATALOG[sid]
    for k in ("name", "cost", "icon", "color", "glow", "stats",
              "desc", "desc_en", "flavor", "category"):
        assert k in d, f"{sid} kurang field {k}"
    assert d.get("magic_only") is True, f"{sid} tidak magic_only"
    icon = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "assets", "items", d["icon"])
    assert os.path.exists(icon), f"ikon {sid} tidak ada"
    # Hero fisik ditolak
    kz = Hero("kaizen", "blue")
    assert not kz.items.add(sid), f"{sid} dipakai hero fisik?!"
print("T1 OK  - 7 item magic: field lengkap, ikon ada, fisik ditolak")

# ── T2: Sage Scepter - skill amp stat ──────────────────────
h = _boss_hero("sage_scepter")
assert abs(h.items.get_skill_amp() - 0.15) < 1e-9
assert abs(h.items.get_spell_vamp() - 0.08) < 1e-9
assert abs(h.items.get_cooldown_reduction() - 0.08) < 1e-9
print("T2 OK  - Sage Scepter: amp .15, vamp .08, CDR .08")

# ── T3: Fulgur Scepter - Energy Blast ──────────────────────
h = _boss_hero("fulgur_scepter")
foe = FoeStub()
h.target = foe
h.items.update(1, enemies=[foe])
act = ITEM_CATALOG["fulgur_scepter"]["active"]
assert foe.taken == [act["damage"]], f"blast salah: {foe.taken}"
assert h.items.fulgur_cd == act["cooldown"], "CD blast tidak aktif"
h.items.update(1, enemies=[foe])
assert len(foe.taken) == 1, "blast retrigger saat CD"
print("T3 OK  - Fulgur Scepter: 300 magic dmg + CD 18 dtk")

# ── T4: Hex Idol - Hexcraft ────────────────────────────────
h = _boss_hero("hex_idol")
foe = FoeStub()
h.target = foe
h.items.update(1, enemies=[foe])
act = ITEM_CATALOG["hex_idol"]["active"]
assert foe.stun_timer == act["stun"], "hex tidak men-stun"
kinds = [k for k, _, _ in foe.debuffs]
assert "skill_down" in kinds, "hex tidak men-silence skill"
assert h.items.hex_cd == act["cooldown"]
print("T4 OK  - Hex Idol: stun 2.5 dtk + silence + CD 30 dtk")

# ── T5: Rift Veil - Discord Field ──────────────────────────
h = _boss_hero("rift_veil")
h.x, h.y = 50, 50  # dekatkan ke posisi musuh (radius 320)
e1, e2 = FoeStub(60, 80), FoeStub(80, 60)
h.items.update(1, enemies=[e1, e2])
act = ITEM_CATALOG["rift_veil"]["active"]
assert abs(e1.dmg_amp_amount - act["damage_amp"]) < 1e-9
assert abs(e2.dmg_amp_amount - act["damage_amp"]) < 1e-9
assert h.items.rift_cd == act["cooldown"]
print("T5 OK  - Rift Veil: 2 musuh kena +15% damage + CD 20 dtk")

# ── T6: Vital Stone - Vitality Pact ────────────────────────
h = _boss_hero("vital_stone")
h.hp = int(h.max_hp * 0.20)
hp0 = h.hp
h.items.update(1, enemies=[FoeStub(900, 900)])
act = ITEM_CATALOG["vital_stone"]["active"]
expect = int(h.max_hp * act["heal_pct"])
assert h.hp - hp0 >= expect - 1, f"heal pact salah ({h.hp - hp0})"
assert h.items.pact_cd == act["cooldown"]
print("T6 OK  - Vital Stone: heal 25% Max HP saat kritis + CD 45 dtk")

# ── T7: Vine Rod - Entangle root on-hit ────────────────────
h = _boss_hero("vine_rod")
foe = FoeStub()
h.items.on_basic_attack_hit(foe, 50, [foe])
act = ITEM_CATALOG["vine_rod"]["on_attack"]
assert foe.slow_amount == 1.0, "root tidak menerapkan slow total"
assert h.items.vine_cd == act["cooldown"], "CD root tidak aktif"
foe.slow_amount = 0.0
h.items._on_hit_common(foe, 50, [foe])
assert foe.slow_amount == 0.0, "root retrigger saat CD"
print("T7 OK  - Vine Rod: root 1 dtk per pukulan (CD 9 dtk)")

# ── T8: Spectral Charm - Spectral Form evasion 1.0 ────────
h = _boss_hero("spectral_charm")
assert h.items.get_evasion() == 0.0, "evasion keliru saat normal"
h.hp = int(h.max_hp * 0.25)
h.items.update(1, enemies=[FoeStub(900, 900)])
assert h.items.ghost_timer == ITEM_CATALOG[
    "spectral_charm"]["active"]["duration"]
assert h.items.get_evasion() == 1.0, "Spectral Form tidak 100% evade"
h.items.clear_on_death()
assert h.items.ghost_timer == 0 and h.items.ghost_cd == 0
print("T8 OK  - Spectral Charm: kebal fisik saat kritis, reset mati")

# ── T9: Toko - 6 halaman: PHYSICAL x2, MAGIC x2, TANK x2 ───
from hero_items import (SHOP_PAGES, SHOP_PAGE_META, get_item_class,
                        CLASS_PHYSICAL, CLASS_MAGIC, CLASS_TANK)
pages = ItemShopUI._page_count()
assert pages == 6, f"toko harus 6 halaman, ada {pages}"
assert len(ITEM_SHOP_ORDER) == len(ITEM_CATALOG) == 33
# Meta halaman: 2 halaman tiap kelas, berurutan PHYSICAL→MAGIC→TANK
cls_seq = [m[0] for m in SHOP_PAGE_META]
assert cls_seq == [CLASS_PHYSICAL, CLASS_PHYSICAL,
                   CLASS_MAGIC, CLASS_MAGIC,
                   CLASS_TANK, CLASS_TANK], cls_seq
# Kelas tidak tercampur dalam satu halaman
for page in SHOP_PAGES:
    assert len({get_item_class(s) for s in page}) == 1, \
        f"halaman campur kelas: {page}"
# Semua item paket MAGIC berada di 2 halaman MAGIC (indeks 2 & 3)
magic_pages = set(SHOP_PAGES[2]) | set(SHOP_PAGES[3])
assert set(MAGIC) <= magic_pages
assert SHOP_PAGES[3] == ["vine_rod", "spectral_charm"], SHOP_PAGES[3]
# Komposisi jumlah item per kelas
counts = {c: 0 for c in (CLASS_PHYSICAL, CLASS_MAGIC, CLASS_TANK)}
for sid in ITEM_CATALOG:
    counts[get_item_class(sid)] += 1
assert counts == {CLASS_PHYSICAL: 14, CLASS_MAGIC: 10,
                  CLASS_TANK: 9}, counts
print("T9 OK  - toko 6 halaman: PHYSICAL 14, MAGIC 10, TANK 9; "
      "kelas tidak tercampur")

# ── T10: AI menyarankan paket magic ke hero magic ─────────
got = suggest_item_for_hero(Hero("vex", "blue"), set())
assert got in ("astral_codex",) + tuple(MAGIC), f"saran aneh: {got}"
kz = Hero("kaizen", "blue")
pool = set()
for _ in range(40):
    s = suggest_item_for_hero(kz, pool)
    if s is None:
        break
    pool.add(s)
assert not (pool & set(MAGIC)), "AI fisik disarankan item MAGIC ONLY"
print("T10 OK - AI: mage disarankan paket magic, fisik tidak pernah")

print("\nSEMUA TEST PAKET MAGIC LULUS ✓")
