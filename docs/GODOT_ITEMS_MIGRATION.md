# Migrasi `hero_items.py` → Godot (`godot_rebuild/`)

Status: **native GDScript, tanpa Python saat runtime**. Melanjutkan migrasi
`main.py` (#377), `_core.py` (#378), `_entity.py` (#379), `_render.py` (#380),
`_system.py` (#381), `hero_archetypes.py` (#382), dan `hero_balance.py` (#383).
Python tetap menjadi sumber kebenaran/oracle; port ini **tidak** membuat item,
angka, atau aturan toko baru.

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| `ITEM_CATALOG` 33 item, biaya, stat, pasif/aktif | `scripts/core/HeroItems.gd` + `data/hero_items.json` | Kontrak fail-closed, SHA-256 sumber, katalog identik dengan `core_data.json`. |
| `MAX_ITEM_SLOTS`, `ITEM_FLAT_COST` | `UnitInventory.MAX_SLOTS`, kontrak items | 6 slot; biaya flat sumber diekspor apa adanya. |
| `is_magic_hero`, `get_item_class`, override kelas | `HeroItems.is_magic_role()`, `item_class()` | Role-based Magic, Anti-Mage dikecualikan; PHYSICAL/MAGIC/TANK. |
| `CLASS_ITEM_ORDER`, `_build_shop_pages`, `CATEGORY_INFO` | `HeroItems.page_count/page_items/page_meta/class_label/category_*` | 6 halaman kelas: PHYSICAL 14 (1/2+2/2), MAGIC 10, TANK 9. |
| `_FIELD_LABELS`, `_MECH_GROUPS`, `_fmt_mech_value`, `_build_item_mechanics` | `HeroItems.mechanics(item_id, lang)` | Teks mekanik ID/EN, label/grup/persen/frame, format `%g`. |
| `HeroItemInventory` getter/stat/caps | `scripts/core/UnitInventory.gd` | Damage/HP/armor/regen/AS/crit/cleave/CDR/spell-vamp/skill-amp/evasion/move/heal-amp/slow-resist/range/true-strike/reflect/block/shred/chain/bash/veil/guard/rend. |
| Timer/proc auto-trigger | `UnitInventory.state`, `EntityItems.update()` | Blood Frenzy, Last Stand, guard, veil, ghost, gale, thorn, static, empower, regen, cooldown, dan reset kematian. |
| `on_basic_attack_hit`, `_on_hit_common`, `on_ranged_attack_hit` | `EntityItems.on_basic_attack_hit/on_ranged_attack_hit` | Lifesteal/cleave melee; ranged lifesteal saat proyektil dilepas, on-hit common saat mendarat. |
| `roll_crit`, `get_rend_crit`, block/true-strike/evasion | `EntityCombat.hero_pre_damage`, `MatchModel._attack` | Crit max chance/mult, rend, block melee roll + aura guard, true strike, veil/ghost evasion. |
| `_MIASMA`, `_tick_miasma`, `update_auras` | `EntityItems.miasma`, `apply_miasma/tick_miasma/update_auras` | Debuff area periodik, reset aura tiap frame, Scarlet guard, Steel Aegis, Everfrost/Solar/Searbrand ke musuh termasuk minion/boss. |
| `notify_damage_taken` | `EntityItems.notify_damage_taken()` | Thorn/reflect, Last Stand, veil, dan respons damage lain dipanggil dari `BattleUnit._apply_hp_loss`. |
| `suggest_item_for_hero` | `UnitInventory.suggest_for()` | Rekomendasi AI berdasarkan role/range/owned, diuji 33 kasus oracle. |
| `_try_buy`, `_try_drop`, pending forge, `clear_on_death` | `MatchModel.buy_item/drop_item`, `UnitInventory.deliver_pending/clear_on_death` | Gate gold/slot/melee/magic, antre saat mati, kirim saat respawn, drop tanpa refund, hanya Holy Rapier hilang permanen saat mati. |
| `ItemShopUI` paging/target | `CoreGame` + `ArenaView` | Forge memakai halaman kelas 6 halaman dan label target terpilih; bukan salinan pixel-perfect renderer Pygame. |

## Arsitektur runtime

```
CoreData
  ├── archetypes: HeroArchetypes
  ├── balance: HeroBalance
  └── items: HeroItems
        ├── catalog + shop pages + mechanics (kontrak fail-closed)
        └── class/category/role helpers

BattleUnit
  ├── items: UnitInventory (state/timer/getter/proc)
  ├── heal/apply_debuff/cast_skill/kit_skill_damage memakai item modifiers
  └── _apply_hp_loss -> EntityItems.notify_damage_taken

MatchModel.step
  ├── EntityItems.update_auras(self)
  ├── EntityMovement -> EntityItems.update(hero, enemies, model)
  ├── _attack -> crit/rend, ranged lifesteal release, melee on-hit
  └── EntityProjectiles._hit -> on_ranged_attack_hit

CoreGame/ArenaView
  └── ITEM FORGE: halaman kelas, BUY FOR target, buy/drop rules
```

- State item sekarang berada di `UnitInventory.state`; `BattleUnit.item_timer()`
  mendelegasikan ke inventory agar tidak ada dua sumber timer.
- Regen item diterapkan oleh `EntityItems.update()` per frame seperti sumber,
  bukan lewat `BattleUnit.tick_timers()` agar urutan dan bypass heal-mod parity.
- `StatusEffects` mendapat `silence_timer`; `cast_skill()` menolak saat silence.
- `EntityItems.miasma` di-clear saat `MatchModel.clear_unit_refs()` supaya match
  baru tidak membawa debuff match sebelumnya.
- `CoreData.valid()` menolak kontrak items hilang/rusak; game tidak diam-diam
  berjalan tanpa katalog item.

## Kontrak data & tooling

```bash
# Setelah mengubah hero_items.py atau katalog item:
python3 tools/prepare_godot_core.py
python3 tools/prepare_godot_items.py
python3 tools/prepare_godot_items.py --check
python3 tools/test_godot_items_prepare.py
```

`prepare_godot_items.py` mengimpor `hero_items.py` asli dengan stub tipis
`pygame/ui_theme/localization/_core` (HERO_LEVELS dari prepare core), lalu:

1. memverifikasi katalog sumber identik dengan `core_data.json`;
2. menulis `godot_rebuild/data/hero_items.json`: katalog, kelas/override,
   urutan toko, 6 halaman, kategori/label/grup mekanik, slot, biaya flat,
   keyword magic role, dan SHA-256 sumber;
3. menulis `godot_rebuild/tests/fixtures/hero_items_parity.json`: role/class,
   mekanik ID/EN, getter, trigger deterministik, aura, on-hit, dan suggestion.

`--check` membandingkan byte deterministik (JSON sort-key) dan tidak menulis.
Hash sumber bergeser, katalog core basi, cakupan kurang, atau nilai non-finite
membuat gate gagal. Float fixture dinormalisasi 12 desimal untuk stabilitas
lintas CPython; kontrak sumber tetap exact. SHA-256 kontrak saat migrasi:
`8736449a1cad`.

## Integrasi CI

- Path filter `godot-check.yml` dan `godot-rebuild.yml` mencakup `hero_items.py`
  serta tool prepare/test items.
- Kedua workflow menjalankan `prepare_godot_items.py --check` dan
  `test_godot_items_prepare.py` setelah kontrak core siap.
- `validate_project.py` memeriksa modul, hash, cakupan 33/6, konstanta sumber,
  wiring CoreData/BattleUnit/MatchModel/EntityItems, dan gate CI.
- `run_all.gd` memanggil `HeroItemsParityTest.run()` untuk membandingkan runtime
  GDScript dengan oracle Python dan menguji aturan beli/drop/pending/respawn.

## Batasan yang jujur

- Tidak ada rebalance baru. Semua angka/efek berasal dari `hero_items.py`.
- Forge UI native memakai halaman kelas dan target terpilih, tetapi tidak
  menyalin pixel-perfect `HeroItemRenderer`/animasi Pygame. Mekanik item tetap
  tersedia melalui kontrak dan runtime; verifikasi visual GPU belum dilakukan.
- Ranged lifesteal diterapkan saat proyektil dilepas seperti `_entity.py`;
  on-hit ranged hanya common proc saat proyektil mendarat.
- Beberapa efek visual/popup/chain FX disederhanakan ke popup/effect native;
  logika damage/debuff/timer diuji parity, bukan fidelitas piksel.
- Verifikasi headless tidak membuktikan perangkat Android, audio output,
  Play Games, top-up produksi, atau signing keystore. Lihat
  `GODOT_ITEMS_VERIFICATION.md` untuk hasil uji aktual.
