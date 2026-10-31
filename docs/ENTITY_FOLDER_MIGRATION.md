# Migrasi `_entity.py` ke Godot

`_entity.py` adalah berkas 6.536 baris di root repo yang berisi **lima modul entity** pygame yang digabung: `tower.py`, `castle.py`, `hero.py`, `minion.py` dan `ai_player.py`, plus prelude pendek berisi kredit damage dan resolusi sekolah damage. Dokumen ini mencatat bagaimana seluruh isinya diklasifikasikan dan dibuktikan di rebuild Godot.

Sumber kebenaran angka: `godot_rebuild/tests/entity_source_oracle.py`. Oracle **mengimpor modul aslinya** (stub `pygame`, namespace `settings.py` dari `_core.py`, stub `_system` dan `_render`) lalu benar-benar mengeksekusi `Tower`, `Castle`, `Minion` dan `Bullet`. Fixture: `tests/fixtures/entity_source.json`.

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `_entity.py` | 6536 |
| Modul gabungan (5 modul + prelude) | 6 |
| Kelas | 7 |
| `def` di kelas | 125 |
| Fungsi top-level | 35 |
| Assign modul (cache/konstanta) | 10 |
| Simbol terklasifikasi | 179 |
| Baris tower / nexus / minion dieksekusi | 21 / 5 / 25 |
| Kasus peluru / sekolah damage | 4 / 7 |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 115 | ada fungsi/konstanta yang benar-benar sama di Godot |
| `bake` | 52 | sumber dieksekusi script bake, hasilnya sprite atlas |
| `folded` | 4 | dijalankan alur modul pengganti tanpa fungsi 1:1 |
| `dead` | 8 | tidak pernah tercapai di pohon pygame |

## 2. Peta lima modul

| Modul | Baris | Kelas | Target Godot |
| --- | --- | --- | --- |
| `prelude (baris 1-18)` | 1–18 (18 baris) | — | `scripts/match/prototype_battle.gd` (`_deliver_hit`) |
| `tower.py` | 19–1385 (1367 baris) | — | `scripts/combat/structure_state.gd` + `siege_battle.gd` + `siege_view.gd` |
| `castle.py` | 1386–3207 (1822 baris) | — | `structure_state.gd` + `prototype_battle._apply_nexus_stats` + `structure_art.gd` |
| `hero.py` | 3208–5388 (2181 baris) | — | `scripts/combat/hero_state.gd` + 40 modul skill/item + bake atlas hero |
| `minion.py` | 5389–5991 (603 baris) | — | `scripts/combat/minion_battle.gd` + `prototype_battle.scaled_minion_definition` |
| `ai_player.py` | 5992–6536 (545 baris) | — | `scripts/match/ai_{policy,controller,build,upgrades,shields,recruitment,items}.gd` |

| Kelas | `def` | Kind | Padanan |
| --- | --- | --- | --- |
| `_DummyBulletTarget` | 1 | `bake` | target palsu untuk bake atlas peluru |
| `Bullet` | 5 | `ported` | `projectile_state.gd` + `siege_battle` impact arm |
| `Tower` | 22 | `ported` | `structure_state.gd` + `siege_battle` + bake tower sheet |
| `Castle` | 18 | `ported` | `structure_state.gd` + `_apply_nexus_stats` + bake castle |
| `Hero` | 48 | `ported` | `hero_state.gd` + arm skill + bake hero/proyektil |
| `Minion` | 13 | `ported` | `minion_battle.gd` + `scaled_minion_definition` |
| `AIPlayer` | 18 | `ported` | AI dipecah per tanggung jawab |

`Hero` mendefinisikan `skill_damage`, `direction`, `timer` dan `attack_cooldown` masing-masing dua kali (pasangan getter/setter `@property`), jadi 125 `def` menjadi 121 method unik — tercatat di `duplicates` fixture.

## 3. Tabel tower (21 baris, hasil eksekusi `Tower._apply_level_stats`)

Kolom **Refund** adalah `transaction_refund`: `Tower.sell_value()` yang dipakai jalur jual `_core.py` (0 di level 1 diganti 50), jadi angkanya sama dengan `sale_refund` di `.tres` setiap level.

| Path | Lv | HP | DMG | Range | CD | Shield | Armor | MR | Upgrade | Refund |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `archer` | 1 | 2000 | 20 | 180 | 35 | 800 | 3 | 0.0 | 175 | 50 |
| `archer` | 2 | 2625 | 33 | 190 | 32 | 1050 | 4 | 0.0 | 325 | 87 |
| `archer` | 3 | 3375 | 50 | 200 | 30 | 1350 | 5 | 0.0 | 550 | 250 |
| `archer` | 4 | 4375 | 72 | 210 | 27 | 1750 | 6 | 0.0 | 850 | 525 |
| `archer` | 5 | 5500 | 98 | 220 | 24 | 2200 | 7 | 0.0 | 1300 | 950 |
| `archer` | 6 | 7000 | 130 | 230 | 22 | 2800 | 8 | 0.0 | 0 | 1600 |
| `cannon` | 2 | 3000 | 42 | 165 | 44 | 1200 | 4 | 0.0 | 325 | 87 |
| `cannon` | 3 | 3750 | 60 | 175 | 40 | 1500 | 5 | 0.0 | 550 | 250 |
| `cannon` | 4 | 4750 | 84 | 185 | 36 | 1900 | 6 | 0.0 | 850 | 525 |
| `cannon` | 5 | 6000 | 116 | 195 | 32 | 2400 | 7 | 0.0 | 1300 | 950 |
| `cannon` | 6 | 7500 | 155 | 210 | 28 | 3000 | 8 | 0.0 | 0 | 1600 |
| `ice` | 2 | 2375 | 20 | 170 | 26 | 950 | 4 | 0.0 | 325 | 87 |
| `ice` | 3 | 3125 | 32 | 180 | 22 | 1250 | 5 | 0.0 | 550 | 250 |
| `ice` | 4 | 4000 | 45 | 190 | 18 | 1600 | 6 | 0.0 | 850 | 525 |
| `ice` | 5 | 5125 | 60 | 200 | 16 | 2050 | 7 | 0.0 | 1300 | 950 |
| `ice` | 6 | 6500 | 78 | 220 | 14 | 2600 | 8 | 0.0 | 0 | 1600 |
| `mage` | 2 | 2125 | 17 | 180 | 20 | 850 | 4 | 0.0 | 325 | 87 |
| `mage` | 3 | 2750 | 26 | 190 | 18 | 1100 | 5 | 0.0 | 550 | 250 |
| `mage` | 4 | 3625 | 39 | 200 | 16 | 1450 | 6 | 0.0 | 850 | 525 |
| `mage` | 5 | 4625 | 55 | 210 | 14 | 1850 | 7 | 0.0 | 1300 | 950 |
| `mage` | 6 | 5875 | 70 | 230 | 12 | 2350 | 8 | 0.0 | 0 | 1600 |

Semua baris di atas dibandingkan dengan `data/structures/<path>_level_<n>.tres` oleh `entity_checks.gd` (HP, damage, range, cooldown, armor, magic resist, kapasitas shield, dan `sale_refund`), jadi katalog `.tres` tidak bisa menyimpang dari `_entity.py`.

Biaya ganti path di level 1 (executed): 
`archer` 175G, `cannon` 175G, `ice` 175G, `mage` 175G.

## 4. Tabel nexus (5 baris, hasil eksekusi `Castle._apply_level_stats`)

| Lv | HP | DMG | Range | CD | Shield aktif | Upgrade | Shield baru |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4000 | 35 | 150 | 45 | 4000 | 500 | 850 |
| 2 | 6000 | 55 | 165 | 40 | 4000 | 900 | 850 |
| 3 | 8500 | 80 | 180 | 35 | 4000 | 1500 | 850 |
| 4 | 11500 | 115 | 195 | 30 | 4000 | 2400 | 850 |
| 5 | 15000 | 160 | 210 | 25 | 4000 | 0 | 850 |

Perhatikan kolom **shield aktif**: `shield_max` lahir dari HP level 1 (`CASTLE_SHIELD_HP_RATIO` = 1.0) dan **tidak** ikut naik saat upgrade gratis; hanya shield yang sudah dibeli yang mengikuti HP baru sambil mempertahankan persentasenya. `entity_checks.gd` mengunci quirk ini.

## 5. Tabel minion (25 baris: 5 tipe × 5 tier nexus)

| Tipe | Nexus | HP | DMG | Speed | CD | Gold | Regen | Armor | MR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dark_rider` | 1 | 280 | 32 | 2.0 | 50 | 65 | 0.0 | 1.0 | 0.05 |
| `dark_rider` | 2 | 336 | 38 | 2.12 | 48 | 78 | 0.0 | 1.0 | 0.05 |
| `dark_rider` | 3 | 392 | 44 | 2.24 | 46 | 91 | 0.0 | 1.0 | 0.05 |
| `dark_rider` | 4 | 476 | 54 | 2.42 | 43 | 110 | 0.0 | 1.0 | 0.05 |
| `dark_rider` | 5 | 560 | 64 | 2.6 | 41 | 130 | 0.0 | 1.0 | 0.05 |
| `goblin` | 1 | 45 | 5 | 1.5 | 45 | 8 | 0.0 | 0.0 | 0.0 |
| `goblin` | 2 | 54 | 6 | 1.59 | 43 | 9 | 0.0 | 0.0 | 0.0 |
| `goblin` | 3 | 62 | 7 | 1.68 | 41 | 11 | 0.0 | 0.0 | 0.0 |
| `goblin` | 4 | 76 | 8 | 1.815 | 39 | 13 | 0.0 | 0.0 | 0.0 |
| `goblin` | 5 | 90 | 10 | 1.95 | 37 | 16 | 0.0 | 0.0 | 0.0 |
| `orc` | 1 | 110 | 13 | 0.95 | 60 | 18 | 0.0 | 0.0 | 0.0 |
| `orc` | 2 | 132 | 15 | 1.007 | 57 | 21 | 0.0 | 0.0 | 0.0 |
| `orc` | 3 | 154 | 18 | 1.064 | 55 | 25 | 0.0 | 0.0 | 0.0 |
| `orc` | 4 | 187 | 22 | 1.1495 | 52 | 30 | 0.0 | 0.0 | 0.0 |
| `orc` | 5 | 220 | 26 | 1.235 | 50 | 36 | 0.0 | 0.0 | 0.0 |
| `troll` | 1 | 320 | 18 | 0.65 | 75 | 45 | 0.6 | 2.0 | 0.05 |
| `troll` | 2 | 384 | 21 | 0.689 | 72 | 54 | 0.72 | 2.0 | 0.05 |
| `troll` | 3 | 448 | 25 | 0.728 | 69 | 62 | 0.84 | 2.0 | 0.05 |
| `troll` | 4 | 544 | 30 | 0.7865 | 65 | 76 | 1.02 | 2.0 | 0.05 |
| `troll` | 5 | 640 | 36 | 0.845 | 62 | 90 | 1.2 | 2.0 | 0.05 |
| `undead` | 1 | 65 | 11 | 0.85 | 60 | 16 | 0.0 | 0.0 | 0.15 |
| `undead` | 2 | 78 | 13 | 0.901 | 57 | 19 | 0.0 | 0.0 | 0.15 |
| `undead` | 3 | 91 | 15 | 0.952 | 55 | 22 | 0.0 | 0.0 | 0.15 |
| `undead` | 4 | 110 | 18 | 1.0285 | 52 | 27 | 0.0 | 0.0 | 0.15 |
| `undead` | 5 | 130 | 22 | 1.105 | 50 | 32 | 0.0 | 0.0 | 0.15 |

Tier 1 adalah `.tres` dasar; tier 2-5 memakai `prototype_battle.scaled_minion_definition` (HP/damage/gold/regen × skala, speed × `1 + (skala-1)·0.3`, cooldown ÷ `1 + (skala-1)·0.2`, armor dan magic resist **tidak** diskalakan).

## 6. Quirk sumber yang dikunci dari hasil eksekusi

| Quirk | Perilaku sumber | Dibuktikan di Godot |
| --- | --- | --- |
| Refund level 1 | `Tower.sell_value()` = 0, lalu `_core` menjual dengan `if sell_val == 0: sell_val = 50` | `data/structures/archer_level_1.tres` sekarang menyatakan `sale_refund = 50` eksplisit; `sell_tower` membayar tepat 50 |
| Refund shield | shield aktif menambah `TOWER_REGEN_SHIELD_COST` sebelum dikali 50% → 425 | `sale_value()` = `sale_refund + 425` |
| Upgrade nexus | HP baru = `min(max, int(max·rasio_lama) + (max-lama) + 500)` | `prototype_battle._apply_nexus_stats` |
| Shield nexus | kapasitas tidak berubah tanpa pembelian | `shield_max` tetap 4000 di level 5 |
| Sekolah damage | `resolve_damage_school` → `None` untuk serangan menara/kastil | `siege_battle._projectile_school` mengembalikan `neutral` |
| Peluru | `BULLET_SPEED` 8, `BULLET_RADIUS` 4, splash cannon 60% | `projectile_state.gd` (`speed` 8.0, `hit_radius` 4.0) + `int(float(shot.damage) * 0.6)` |

## 7. Simbol mati dan duplikat

| Simbol | Baris / alasan |
| --- | --- |
| `_draw_castle_ground` | 1970, dimatikan di sumber (`# disabled`) |
| `_render_castle_lvl6` | 2967, `MAX_NEXUS_LEVEL` = 5 |
| `_draw_center_royal_tower` | 2996, hanya dipanggil lvl6 |
| `class:Castle.get_minion_composition` | tidak ada call-site di pohon pygame |
| `class:Hero.count_enemies_in_range` | tidak ada call-site di pohon pygame |
| `class:Hero.end_damage_scope` | tidak ada call-site di pohon pygame |
| `class:Hero.get_skill_cooldowns` | tidak ada call-site di pohon pygame |
| `class:Minion._get_lane_y` | tidak ada call-site di pohon pygame |

Duplikat (getter/setter `@property`):

- `class:Hero.attack_cooldown` — baris 5333, 5339
- `class:Hero.direction` — baris 5303, 5308
- `class:Hero.skill_damage` — baris 3240, 3261
- `class:Hero.timer` — baris 5312, 5317

## 8. Deviasi yang didokumentasikan

### D1 — 52 simbol `bake` (kastil, badan tower, peluru, hero, minion)

Gambar prosedural pygame tidak diportir baris per baris. `bake/bake_structure_atlas.py`, `bake_bullet_atlas.py`, `bake_hero_atlas.py`, `bake_hero_projectiles.py`, `bake_minion_atlas.py` dan `bake_minion_combat_fx.py` **mengimpor `_entity.py` dan memanggil fungsi sumber yang sama** (`_render_castle_full`, `_get_bullet_sprite`, `hero.draw`, `minion.draw`), lalu memaket hasilnya ke `assets/art/**`. Token klasifikasi untuk baris-baris ini menunjuk baris pemanggilan itu, jadi bukti paritasnya adalah gambar hasil eksekusi kode sumber, bukan rekonstruksi manual.

### D2 — seni kastil level 6 tidak pernah dipakai

`_render_castle_full` punya cabang `else` ke `_render_castle_lvl6`, tetapi `Castle.upgrade` berhenti di `MAX_NEXUS_LEVEL = 5` dan `NEXUS_LEVELS` hanya berisi level 1-5. Jadi `_render_castle_lvl6`, `_draw_center_royal_tower` dan `_draw_castle_ground` ber-`kind` `dead`; atlas yang berhenti di level 5 (`structure_art.castle_name` memakai `clampi(level, 1, 5)`) sudah benar, bukan penyederhanaan.

### D3 — `_DummyBulletTarget` hanya alat bake

Kelas satu method ini tidak pernah dipakai gameplay; `bake_bullet_atlas.py` memakainya sebagai target supaya `Bullet.__init__` bisa dijalankan. Klasifikasinya `bake` dengan token `entity._DummyBulletTarget`.

### D4 — 4 simbol `folded` (konteks sekolah damage)

`set_damage_school`, `get_damage_school` dan `_ACTIVE_HERO` adalah konteks global pygame supaya ~270 call site skill yang tidak mengirim `source=` tetap terhitung sekolahnya. Rebuild tidak butuh konteks global: setiap arm skill mengirim `hero.dmg_school` eksplisit ke `_deliver_hit`, dan `hero_state.gd` menyimpan `dmg_school` per hero. Hasil akhirnya sama (`entity_checks.gd` membandingkan matriks sekolah hasil eksekusi sumber).

## 9. Tabel klasifikasi lengkap (179 simbol)

| Simbol | Kind | Target | Token |
| --- | --- | --- | --- |
| `assign:PAL_OUTLINE_C` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `palette = entity._get_palette(` |
| `assign:_ACTIVE_HERO` | `folded` | `godot_rebuild/scripts/combat/hero_state.gd` | `var dmg_school := "physical"` |
| `assign:_BULLET_SPRITE_CACHE` | `bake` | `godot_rebuild/bake/bake_bullet_atlas.py` | `entity._BULLET_SPRITE_CACHE.clear()` |
| `assign:_CASTLE_SCALED_CACHE` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `assign:_HERO_PROJ_DEAD_AGE` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `hero._draw_projectile(surface, projectile)` |
| `assign:_HERO_PROJ_MAX` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `hero._draw_projectile(surface, projectile)` |
| `assign:_HERO_PROJ_MAX_AGE` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `hero._draw_projectile(surface, projectile)` |
| `assign:_HERO_PROJ_MAX_DIST` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `hero._draw_projectile(surface, projectile)` |
| `assign:_HERO_UI_CACHE` | `bake` | `godot_rebuild/bake/bake_hero_atlas.py` | `hero.draw(surface)` |
| `assign:_TOWER_SPRITE_CACHE` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._TOWER_SPRITE_CACHE` |
| `class:AIPlayer` | `ported` | `godot_rebuild/scripts/match/ai_policy.gd` | `func brain()` |
| `class:AIPlayer.__init__` | `ported` | `godot_rebuild/scripts/match/ai_policy.gd` | `func reset()` |
| `class:AIPlayer._ai_brain` | `ported` | `godot_rebuild/scripts/match/ai_policy.gd` | `func brain()` |
| `class:AIPlayer._ai_elite` | `ported` | `godot_rebuild/scripts/match/ai_policy.gd` | `func elite()` |
| `class:AIPlayer._ai_reserve` | `ported` | `godot_rebuild/scripts/match/ai_controller.gd` | `func reserve(` |
| `class:AIPlayer._ai_step` | `ported` | `godot_rebuild/scripts/match/ai_controller.gd` | `func tick(` |
| `class:AIPlayer._assign_hero_lane` | `ported` | `godot_rebuild/scripts/match/ai_hero_control.gd` | `func assign_hero_lane(` |
| `class:AIPlayer._choose_hero_purchase_target` | `ported` | `godot_rebuild/scripts/match/ai_draft.gd` | `func choose_target(` |
| `class:AIPlayer._control_heroes` | `ported` | `godot_rebuild/scripts/match/ai_hero_control.gd` | `func control_heroes(` |
| `class:AIPlayer._get_hero_pool` | `ported` | `godot_rebuild/scripts/match/ai_draft.gd` | `func hero_pool()` |
| `class:AIPlayer._try_activate_castle_shield` | `ported` | `godot_rebuild/scripts/match/ai_shields.gd` | `func try_castle(` |
| `class:AIPlayer._try_activate_regen_shield` | `ported` | `godot_rebuild/scripts/match/ai_shields.gd` | `func try_regen(` |
| `class:AIPlayer._try_build_tower` | `ported` | `godot_rebuild/scripts/match/ai_build.gd` | `func try_build(` |
| `class:AIPlayer._try_buy_hero` | `ported` | `godot_rebuild/scripts/match/ai_recruitment.gd` | `func try_buy(` |
| `class:AIPlayer._try_buy_item` | `ported` | `godot_rebuild/scripts/match/ai_items.gd` | `func try_buy(` |
| `class:AIPlayer._try_upgrade_hero` | `ported` | `godot_rebuild/scripts/match/ai_upgrades.gd` | `func try_hero(` |
| `class:AIPlayer._try_upgrade_nexus` | `ported` | `godot_rebuild/scripts/match/ai_upgrades.gd` | `func try_nexus(` |
| `class:AIPlayer._try_upgrade_tower_new` | `ported` | `godot_rebuild/scripts/match/ai_upgrades.gd` | `func try_tower(` |
| `class:AIPlayer.update` | `ported` | `godot_rebuild/scripts/match/ai_policy.gd` | `func advance(` |
| `class:Bullet` | `ported` | `godot_rebuild/scripts/combat/projectile_state.gd` | `var hit_radius := 4.0` |
| `class:Bullet.__init__` | `ported` | `godot_rebuild/scripts/combat/projectile_state.gd` | `var speed := 8.0` |
| `class:Bullet._draw_hd_arrow` | `bake` | `godot_rebuild/bake/bake_bullet_atlas.py` | `entity._get_bullet_sprite(` |
| `class:Bullet._on_hit` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _cannon_impact(` |
| `class:Bullet.draw` | `bake` | `godot_rebuild/bake/bake_bullet_atlas.py` | `entity._get_bullet_sprite(` |
| `class:Bullet.update` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _update_projectiles(` |
| `class:Castle` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func can_activate_castle_shield()` |
| `class:Castle.__init__` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `var castle_shield_purchased := false` |
| `class:Castle._apply_level_stats` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _apply_nexus_stats(` |
| `class:Castle._draw_castle_shield` | `ported` | `godot_rebuild/scripts/ui/structure_art.gd` | `func castle_frame(` |
| `class:Castle._draw_hp_bar` | `ported` | `godot_rebuild/scenes/siege/siege_view.gd` | `func _draw_structure_selection(` |
| `class:Castle._find_target` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _structure_target(` |
| `class:Castle._shoot` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func fire_projectile(` |
| `class:Castle._update_castle_shield` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func tick_regen()` |
| `class:Castle.activate_castle_shield` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func activate_castle_shield()` |
| `class:Castle.apply_slow` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | `func apply_slow(` |
| `class:Castle.can_activate_castle_shield` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func can_activate_castle_shield()` |
| `class:Castle.castle_shield_cost` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `const CASTLE_SHIELD_COST` |
| `class:Castle.draw` | `ported` | `godot_rebuild/scenes/siege/siege_view.gd` | `func _draw_structure(` |
| `class:Castle.get_minion_composition` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Castle.set_wave` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func set_wave(` |
| `class:Castle.take_damage` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func apply_hit(` |
| `class:Castle.update` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func step_tick(` |
| `class:Castle.upgrade` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func upgrade_nexus(` |
| `class:Castle.upgrade_cost` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func nexus_upgrade_price(` |
| `class:Hero` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func recalc_item_stats()` |
| `class:Hero.__init__` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func apply_level_stats()` |
| `class:Hero._apply_level_stats` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func apply_level_stats()` |
| `class:Hero._build_name_badge` | `bake` | `godot_rebuild/bake/bake_hero_atlas.py` | `hero.draw(surface)` |
| `class:Hero._collect_onhit_units` | `ported` | `godot_rebuild/scripts/match/battle_item_effects.gd` | `Hero._collect_onhit_units()` |
| `class:Hero._do_attack` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func hero_basic_attack(` |
| `class:Hero._draw_arrow_projectile` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `entity.` |
| `class:Hero._draw_hero_shape` | `bake` | `godot_rebuild/bake/bake_hero_atlas.py` | `hero.draw(surface)` |
| `class:Hero._draw_ice_shard_projectile` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `entity.` |
| `class:Hero._draw_lightning_projectile` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `entity.` |
| `class:Hero._draw_magic_bolt_projectile` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `entity.` |
| `class:Hero._draw_magic_orb_projectile` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `entity.` |
| `class:Hero._draw_projectile` | `bake` | `godot_rebuild/bake/bake_hero_projectiles.py` | `entity.` |
| `class:Hero._eff_attack_cd` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func eff_attack_cd(` |
| `class:Hero._eff_attack_range` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func eff_attack_range()` |
| `class:Hero._find_aggro_target` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func hero_aggro_target(` |
| `class:Hero._find_attack_target` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func hero_basic_attack(` |
| `class:Hero._find_hunt_target` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _hero_pick_target(` |
| `class:Hero._get_all_enemies` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _hero_enemy_list(` |
| `class:Hero._get_base_pos` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _hero_home(` |
| `class:Hero._heal_at_base` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _hero_near_own_base(` |
| `class:Hero._is_near_base` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _hero_near_own_base(` |
| `class:Hero._move_toward` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func move_to(` |
| `class:Hero._passive_heal` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _hero_passive_heal(` |
| `class:Hero._recalc_item_stats` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func recalc_item_stats()` |
| `class:Hero._spawn_projectile` | `ported` | `godot_rebuild/scripts/combat/hero_projectiles.gd` | `static func spawn(` |
| `class:Hero._spawn_skill_projectile` | `ported` | `godot_rebuild/scripts/combat/hero_projectiles.gd` | `static func spawn(` |
| `class:Hero._try_auto_cast` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func try_auto_cast(` |
| `class:Hero.attack_cooldown` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `var attack_cd_base := 0` |
| `class:Hero.boss_type` | `ported` | `godot_rebuild/scripts/data/hero_definition.gd` | `var is_boss_hero` |
| `class:Hero.cast_skill` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func try_auto_cast(` |
| `class:Hero.count_enemies_in_range` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Hero.direction` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `var attack_facing := 1.0` |
| `class:Hero.draw` | `bake` | `godot_rebuild/bake/bake_hero_atlas.py` | `hero.draw(surface)` |
| `class:Hero.end_damage_scope` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Hero.get_skill_cooldowns` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Hero.is_skill_ready` | `ported` | `godot_rebuild/scripts/ui/hero_panel_layout.gd` | `var ready := cooldown <= 0` |
| `class:Hero.move_to` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func set_hero_destination(` |
| `class:Hero.respawn` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _step_hero_respawn(` |
| `class:Hero.skill_damage` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func skill_damage()` |
| `class:Hero.take_damage` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _deliver_hit(` |
| `class:Hero.timer` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `var attack_timer := 0` |
| `class:Hero.update` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _step_one_hero(` |
| `class:Hero.upgrade` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func upgrade()` |
| `class:Hero.upgrade_cost` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func upgrade_cost()` |
| `class:Minion` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func apply_slow(target_id` |
| `class:Minion.__init__` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func scaled_minion_definition(` |
| `class:Minion._distance_to` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func _move_toward(unit` |
| `class:Minion._draw_death_animation` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py` | `minion.draw(` |
| `class:Minion._find_target_smart` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func _select_ai_target(` |
| `class:Minion._get_enemies` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func _find_target(unit` |
| `class:Minion._get_lane_y` | `dead` | — | tidak ada call-site di pohon pygame |
| `class:Minion._move_forward` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func _follow_lane(` |
| `class:Minion._move_toward` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func _move_toward(unit` |
| `class:Minion._spawn_slash_effect` | `bake` | `godot_rebuild/bake/bake_minion_combat_fx.py` | `slash` |
| `class:Minion.apply_slow` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func apply_slow(target_id` |
| `class:Minion.draw` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py` | `minion.draw(` |
| `class:Minion.take_damage` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func apply_hit(` |
| `class:Minion.update` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func step_tick()` |
| `class:Tower` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func activate_regen_shield()` |
| `class:Tower.__init__` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `var regen_shield_active := false` |
| `class:Tower._apply_level_stats` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _build_tower_for(` |
| `class:Tower._draw_regen_indicator` | `ported` | `godot_rebuild/scenes/siege/siege_view.gd` | `func _draw_regen_plus(` |
| `class:Tower._draw_shield_crest` | `ported` | `godot_rebuild/scenes/siege/siege_view.gd` | `StructureArt.crest_frame(14` |
| `class:Tower._draw_tower_body` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `tower_sheet(` |
| `class:Tower._find_target` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _structure_target(` |
| `class:Tower._shoot` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func fire_projectile(` |
| `class:Tower._shoot_archer` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _append_volley_targets(` |
| `class:Tower._shoot_cannon` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _cannon_splash(` |
| `class:Tower._shoot_ice` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _ice_aoe(` |
| `class:Tower._shoot_mage` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func _mage_impact(` |
| `class:Tower._update_regen` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func tick_regen()` |
| `class:Tower.activate_regen_shield` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func activate_regen_shield()` |
| `class:Tower.can_activate_regen_shield` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func can_activate_regen_shield()` |
| `class:Tower.can_upgrade` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func upgrade_price(` |
| `class:Tower.draw` | `ported` | `godot_rebuild/scenes/siege/siege_view.gd` | `func _draw_structure(` |
| `class:Tower.regen_shield_cost` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `const REGEN_SHIELD_COST := 850` |
| `class:Tower.sell_value` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func sale_value()` |
| `class:Tower.take_damage` | `ported` | `godot_rebuild/scripts/combat/siege_battle.gd` | `func apply_hit(` |
| `class:Tower.update` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func step_tick(` |
| `class:Tower.upgrade` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func upgrade_tower(` |
| `class:Tower.upgrade_cost` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func upgrade_price(` |
| `class:_DummyBulletTarget` | `bake` | `godot_rebuild/bake/bake_bullet_atlas.py` | `entity._DummyBulletTarget` |
| `class:_DummyBulletTarget.__init__` | `folded` | `godot_rebuild/bake/bake_bullet_atlas.py` | `entity._DummyBulletTarget` |
| `module:ai_player` | `ported` | `godot_rebuild/scripts/match/ai_policy.gd` | `func brain()` |
| `module:castle` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func can_activate_castle_shield()` |
| `module:hero` | `ported` | `godot_rebuild/scripts/combat/hero_state.gd` | `func recalc_item_stats()` |
| `module:minion` | `ported` | `godot_rebuild/scripts/combat/minion_battle.gd` | `func apply_slow(target_id` |
| `module:prelude` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _deliver_hit(` |
| `module:tower` | `ported` | `godot_rebuild/scripts/combat/structure_state.gd` | `func activate_regen_shield()` |
| `top:_build_armor_crest@534` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._build_armor_crest(` |
| `top:_draw_armor_crest@583` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._build_armor_crest(` |
| `top:_draw_battlement_stone@2268` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_blue_conical_roof@2291` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_castle_gate@2477` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_castle_ground@1970` | `dead` | — | dimatikan di sumber (komentar "disabled") |
| `top:_draw_castle_magic_aura@3172` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_dynamic_effects(` |
| `top:_draw_center_royal_tower@2996` | `dead` | — | hanya dipanggil _render_castle_lvl6 yang tidak tercapai |
| `top:_draw_central_gate_roof@2622` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_central_stone_wall@2423` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_gate_torch@3083` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_dynamic_effects(` |
| `top:_draw_hanging_banner@2808` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_silver_shield_emblem@2708` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_stone_brick@2254` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_stone_corner_tower@2167` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_wall_gold_band@2934` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_wooden_palisade@1985` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_draw_wooden_watchtower@2022` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_get_bullet_sprite@142` | `bake` | `godot_rebuild/bake/bake_bullet_atlas.py` | `entity._get_bullet_sprite(` |
| `top:_get_palette@1404` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `palette = entity._get_palette(` |
| `top:_is_physical_hit@92` | `ported` | `godot_rebuild/scripts/combat/unit_state.gd` | `physical hit misses` |
| `top:_overlay_portcullis@2911` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_full@1950` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_lvl1@1978` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_lvl2@2157` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_lvl3@2580` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_lvl4@2596` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_lvl5@2883` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_castle_full(` |
| `top:_render_castle_lvl6@2967` | `dead` | `godot_rebuild/data/art/structures.json` | `"castles"` |
| `top:_render_dynamic_effects@3062` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_dynamic_effects(` |
| `top:_render_dynamic_effects_direct@3041` | `bake` | `godot_rebuild/bake/bake_structure_atlas.py` | `entity._render_dynamic_effects(` |
| `top:credit_hero_damage@40` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `(attacker as HeroState).damage_dealt += dealt` |
| `top:get_damage_school@87` | `folded` | `godot_rebuild/scripts/combat/hero_projectiles.gd` | `"school": hero.dmg_school` |
| `top:resolve_damage_school@106` | `ported` | `godot_rebuild/scripts/match/prototype_battle.gd` | `func _deliver_hit(` |
| `top:set_damage_school@77` | `folded` | `godot_rebuild/scripts/combat/hero_state.gd` | `var dmg_school := "physical"` |

## 10. Verifikasi

| Langkah | Perintah | Status |
| --- | --- | --- |
| Oracle sumber | `python3 godot_rebuild/tests/entity_source_oracle.py --write` | 179 simbol, 21+5+25 baris tabel, 4 kasus peluru |
| Suite native | `godot_rebuild/tests/entity_checks.gd` (lewat `tests/run_all.gd`) | terdaftar; belum dieksekusi di sandbox (tidak ada binary Godot) |
| Validator statis | `python3 godot_rebuild/tests/validate_project.py` | blok `9cg`; PASS: 22595 static checks |
| Lint GDScript | `gdparse`/`gdlint` (gdtoolkit 4.5.0) | bersih |

Sandbox tidak punya binary Godot, jadi `entity_checks.gd` harus dijalankan di PC/CI. Validator statis **bukan** bukti paritas: ia hanya menjaga inventaris, token klasifikasi, dan kecocokan fixture dengan eksekusi Python.

## 11. Cara regenerasi

```bash
python3 godot_rebuild/tests/entity_source_oracle.py --write  # fixture
python3 godot_rebuild/tests/entity_source_oracle.py --check  # deteksi drift
python3 godot_rebuild/tests/validate_project.py           # guardrail statis
```

