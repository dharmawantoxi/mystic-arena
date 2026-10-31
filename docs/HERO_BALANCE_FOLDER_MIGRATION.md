# Migrasi `hero_balance.py` ke Godot

`hero_balance.py` adalah **satu-satunya tempat balance hero game dikalibrasi**. Berkas 935 baris ini membaca katalog hero yang disusun `_core.get_all_hero_types()`, menghitung satu triple multiplier per hero (`hp` / `damage` / `skill`) lalu **menulis hasil bulatnya kembali ke katalog** supaya toko, preview skill, dan pertempuran membaca angka yang sama.

Karena seluruh pipeline bersifat *pool-relative* (median DPS/EHP, paritas sel arketipe, jangkar rata-rata pool, paritas sekolah per kelas boss), port ini bukan sekadar penyalinan tabel: seluruh algoritmanya dijalankan ulang di GDScript dan diuji terhadap angka sumber, termasuk pembulatan Python (half-to-even) dan urutan langkah yang menentukan hasil.

Sumber kebenaran: `godot_rebuild/tests/hero_balance_source_oracle.py`. Oracle membangun **katalog asli** (dua definisi `get_all_hero_types`, `bosses/boss_data` asli, `hero_balance` asli), menyimpan baris *pristine* sebelum balance, lalu mengeksekusi `resolve_catalog`, `apply_to_catalog`, jangkar pool, fixpoint rumus audit, dan kalibrasi resist offline. Fixture: `tests/fixtures/hero_balance_source.json` (332 KB). Suite native: `tests/hero_balance_checks.gd`.

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `hero_balance.py` | 935 |
| Seksi | 13 |
| Kelas | 0 (modul fungsional) |
| Fungsi modul | 20 |
| Assign modul | 37 |
| Simbol terklasifikasi | 59 |
| Baris multiplier dieksekusi | 222 (216 boss hero + 6 starter) |
| Baris stat final diverifikasi | 216 boss hero + 6 starter |
| Baris resistan boss | 216 |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 20 | fungsi diport 1:1 ke `scripts/data/hero_balance.gd` |
| `data` | 35 | konstanta/saklar/tabel port verbatim |
| `deviation` | 3 | perilaku sengaja berbeda (D1, D4, D5) |
| `folded` | 1 | impor `statistics` diganti `_mean`/`_median` native |

## 2. Peta seksi

| Seksi | Baris | Baris total | Isi |
| --- | --- | --- | --- |
| `header` | 1–46 | 46 | doktrin + angka sebelum/sesudah balance + peringatan yang dibuang |
| `switches` | 47–55 | 9 | tujuh saklar A/B/C dan paritas |
| `rebudget` | 56–79 | 24 | bobot power, target rasio, bobot gaya main, batas multiplier |
| `guards` | 80–87 | 8 | guard "worth it" (band harga, redaman, meta) |
| `school_mod_constants` | 88–95 | 8 | modifier sekolah ke menara (hanya bila paritas mati) |
| `starter_constants` | 96–104 | 9 | konstanta catch-up + enam starter |
| `metrics` | 105–139 | 35 | `metrics` + `_clamp` / `_median` / `_mean` |
| `targets` | 140–262 | 123 | `hero_target`, `stat_multipliers`, `school_mod`, catch-up starter |
| `parity` | 263–354 | 92 | `_eff_dps`, `_final_power`, `cell_parity_factors` |
| `resolve` | 355–562 | 208 | `pristine_boss_stats`, `resolve_catalog` |
| `calibrate` | 563–690 | 128 | `calibrate_boss_resistances` |
| `anchors` | 691–839 | 149 | `_DBG`, `LAST`, `_pool_mean_rescale`, `_final_fixpoint` |
| `apply` | 840–935 | 96 | `apply_to_catalog` |

## 3. Klasifikasi per simbol

Setiap simbol punya **target + token**; validator statis memastikan token itu benar-benar ada di berkas target.

### 3.1 `header` (1–46)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `import:statistics` | 43 | `folded` | `hero_balance.gd` | `static func _mean(` | fmean/median diganti _mean/_median native |
| `import:hero_archetypes` | 45 | `ported` | `hero_balance.gd` | `const Archetypes = preload("res://scripts/data/hero_archetypes.gd")` | tabel + aritmetika resist diport di layer yang sama |

### 3.2 `switches` (47–55)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `assign:ENABLE_REBUDGET` | 48 | `data` | `hero_balance.gd` | `const ENABLE_REBUDGET := true` | saklar A aktif |
| `assign:ENABLE_SCHOOL_MOD` | 49 | `data` | `hero_balance.gd` | `const ENABLE_SCHOOL_MOD := false` | hanya dipakai kalau paritas mati |
| `assign:ENABLE_STARTER_CATCHUP` | 50 | `data` | `hero_balance.gd` | `const ENABLE_STARTER_CATCHUP := true` | saklar C aktif |
| `assign:SCHOOL_PARITY` | 51 | `data` | `hero_balance.gd` | `const SCHOOL_PARITY := true` | paritas sekolah per kelas boss |
| `assign:CELL_PARITY` | 52 | `data` | `hero_balance.gd` | `const CELL_PARITY := true` | paritas sel arketipe |
| `assign:POOL_MEAN_ANCHOR` | 53 | `data` | `hero_balance.gd` | `const POOL_MEAN_ANCHOR := true` | rata-rata pool dikunci |
| `assign:FINAL_FIXPOINT` | 54 | `data` | `hero_balance.gd` | `const FINAL_FIXPOINT := true` | koreksi akhir rumus audit |

### 3.3 `rebudget` (56–79)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `assign:W_DPS,W_EHP,EHP_PER_HP` | 59 | `data` | `hero_balance.gd` | `const W_DPS := 0.72` | bobot skor power 0.72 / 0.28 |
| `assign:TARGET_RATIO` | 60 | `data` | `hero_balance.gd` | `const TARGET_RATIO: Dictionary = {` | rasio EHP/DPS per gaya main |
| `assign:SCHOOL_RATIO_BONUS` | 63 | `data` | `hero_balance.gd` | `const SCHOOL_RATIO_BONUS: Dictionary = {` | geseran rasio per sekolah |
| `assign:RATIO_BLEND` | 64 | `data` | `hero_balance.gd` | `const RATIO_BLEND := 0.55` | campuran data lama vs target |
| `assign:BUDGET_COMPRESS` | 65 | `data` | `hero_balance.gd` | `const BUDGET_COMPRESS := 0.45` | kompresi budget ke median pool |
| `assign:STYLE_POWER` | 66 | `data` | `hero_balance.gd` | `const STYLE_POWER: Dictionary = {` | bobot power per gaya main |
| `assign:HP_MULT_RANGE` | 72 | `data` | `hero_balance.gd` | `const HP_MULT_RANGE := [0.66, 1.50]` | batas multiplier HP |
| `assign:DMG_MULT_RANGE` | 73 | `data` | `hero_balance.gd` | `const DMG_MULT_RANGE := [0.68, 1.45]` | batas multiplier damage/skill |
| `assign:SCHOOL_PARITY_CAP` | 75 | `data` | `hero_balance.gd` | `const SCHOOL_PARITY_CAP := 1.45` | pengapung paritas sekolah |
| `assign:CELL_PARITY_CAP` | 76 | `data` | `hero_balance.gd` | `const CELL_PARITY_CAP := 1.30` | pengapung paritas sel |
| `assign:POOL_MEAN_TOL_MAX` | 77 | `data` | `hero_balance.gd` | `const POOL_MEAN_TOL_MAX := 0.18` | batas jangkar pool |
| `assign:FINAL_CORR_CAP` | 78 | `data` | `hero_balance.gd` | `const FINAL_CORR_CAP := 1.35` | batas koreksi akhir |

### 3.4 `guards` (80–87)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `assign:COST_BUCKET` | 81 | `data` | `hero_balance.gd` | `const COST_BUCKET := 1000` | lebar band harga |
| `assign:COST_EFF_BAND` | 82 | `data` | `hero_balance.gd` | `const COST_EFF_BAND := [0.78, 1.28]` | band efisiensi harga |
| `assign:COST_EFF_DAMP` | 83 | `data` | `hero_balance.gd` | `const COST_EFF_DAMP := 0.60` | redaman koreksi harga |
| `assign:COST_EFF_MIN_GROUP` | 84 | `data` | `hero_balance.gd` | `const COST_EFF_MIN_GROUP := 8` | ukuran grup minimum |
| `assign:META_EFF_BAND` | 85 | `data` | `hero_balance.gd` | `const META_EFF_BAND := [0.80, 1.25]` | band efisiensi toko meta |
| `assign:META_EFF_DAMP` | 86 | `data` | `hero_balance.gd` | `const META_EFF_DAMP := 0.75` | redaman toko meta |

### 3.5 `school_mod_constants` (88–95)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `assign:TOWER_ARMOR_AT_L3` | 91 | `data` | `hero_balance.gd` | `const TOWER_ARMOR_AT_L3 := 5.0` | armor menara level 3 |
| `assign:ARMOR_FACTOR` | 92 | `data` | `hero_balance.gd` | `const ARMOR_FACTOR := 0.06` | kurva armor (sama dengan hero_archetypes) |
| `assign:TOWER_PHYS_FACTOR` | 93 | `data` | `hero_balance.gd` | `const TOWER_PHYS_FACTOR := 1.0 / (1.0 + TOWER_ARMOR_AT_L3 * ARMOR_FACTOR)` | mitigasi fisik menara |
| `assign:SCHOOL_MOD_CAP` | 94 | `data` | `hero_balance.gd` | `const SCHOOL_MOD_CAP := 1.06` | pengapung modifier sekolah |

### 3.6 `starter_constants` (96–104)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `assign:STARTER_CATCHUP_MAX` | 97 | `data` | `hero_balance.gd` | `const STARTER_CATCHUP_MAX := 1.32` | bonus catch-up maksimum |
| `assign:STARTER_CATCHUP_REF` | 98 | `data` | `hero_balance.gd` | `const STARTER_CATCHUP_REF := 12` | roster penuh = 12 unlock |
| `assign:STARTER_CATCHUP_LV0` | 99 | `data` | `hero_balance.gd` | `const STARTER_CATCHUP_LV0 := 1` | level bonus penuh |
| `assign:STARTER_CATCHUP_LV1` | 100 | `data` | `hero_balance.gd` | `const STARTER_CATCHUP_LV1 := 8` | level bonus habis |
| `assign:STARTER_CATCHUP_DECAY` | 101 | `data` | `hero_balance.gd` | `const STARTER_CATCHUP_DECAY := 0.20` | sisa bonus di level tinggi |
| `assign:STARTER_HEROES` | 102 | `data` | `hero_balance.gd` | `const STARTER_HEROES: Array[String] = [` | enam starter |

### 3.7 `metrics` (105–139)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `func:metrics` | 106 | `ported` | `hero_balance.gd` | `static func metrics(` | — |
| `func:_clamp` | 128 | `ported` | `hero_balance.gd` | `static func _clamp(` | — |
| `func:_median` | 133 | `ported` | `hero_balance.gd` | `static func _median(` | — |
| `func:_mean` | 137 | `ported` | `hero_balance.gd` | `static func _mean(` | — |

### 3.8 `targets` (140–262)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `func:hero_target` | 141 | `ported` | `hero_balance.gd` | `static func hero_target(` | — |
| `func:stat_multipliers` | 185 | `ported` | `hero_balance.gd` | `static func stat_multipliers(` | — |
| `func:school_mod` | 207 | `ported` | `hero_balance.gd` | `static func school_mod(` | — |
| `func:starter_level_factor` | 215 | `ported` | `hero_balance.gd` | `static func starter_level_factor(` | — |
| `func:starter_catchup` | 226 | `ported` | `hero_balance.gd` | `static func starter_catchup(` | — |
| `func:starter_catchup_stats` | 249 | `ported` | `hero_balance.gd` | `static func starter_catchup_stats(` | — |
| `func:boss_unlocks_for_purchases` | 256 | `ported` | `hero_balance.gd` | `static func boss_unlocks_for_purchases(` | — |

### 3.9 `parity` (263–354)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `func:_eff_dps` | 264 | `ported` | `hero_balance.gd` | `static func eff_dps(` | — |
| `func:_final_power` | 280 | `ported` | `hero_balance.gd` | `static func final_power(` | — |
| `func:cell_parity_factors` | 293 | `ported` | `hero_balance.gd` | `static func cell_parity_factors(` | — |

### 3.10 `resolve` (355–562)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `func:pristine_boss_stats` | 355 | `deviation` | `hero_balance.gd` | `static func pristine_boss_stats(` | D1: impor bosses.boss_data -> parameter pristine |
| `func:resolve_catalog` | 384 | `ported` | `hero_balance.gd` | `static func resolve_catalog(catalog: Dictionary, unlocks: int = 0)` | D2: unlock starter jadi argumen |

### 3.11 `calibrate` (563–690)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `func:calibrate_boss_resistances` | 563 | `ported` | `hero_balance.gd` | `static func calibrate_boss_resistances(` | — |

### 3.12 `anchors` (691–839)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `assign:_DBG` | 691 | `deviation` | `—` | `—` | D5: log MYSTIC_DEBUG_BALANCE ke stderr tidak diport |
| `assign:LAST` | 694 | `deviation` | `hero_balance.gd` | `static var last_result: Dictionary = {` | D4: global LAST -> last_result, direset tiap apply |
| `func:_pool_mean_rescale` | 697 | `ported` | `hero_balance.gd` | `static func pool_mean_rescale(` | — |
| `func:_final_fixpoint` | 737 | `ported` | `hero_balance.gd` | `static func final_fixpoint(` | — |

### 3.13 `apply` (840–935)

| Simbol | Baris | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- | --- |
| `func:apply_to_catalog` | 840 | `ported` | `hero_balance.gd` | `static func apply_to_catalog(catalog: Dictionary, pristine: Dictionary = {})` | D3: tanpa try/except, gagal keras |

## 4. Pipeline yang dijalankan ulang

Urutan langkah dipertahankan persis seperti sumber (lihat `PERINGATAN YANG DIBUANG` di header sumber: jangkar rata-rata **sebelum** fixpoint, paritas sekolah **sesudah** normalisasi, paritas diukur pada damage final).

| Langkah | Sumber | Native | Hasil terukur |
| --- | --- | --- | --- |
| statistik pool | inline di `resolve_catalog` | `pool_for()` | median rasio 5,14098 · budget 462,369519 · p50 462,427273 · median DPS 486,624332 · median EHP 2350,0 |
| multiplier per hero | `stat_multipliers` | `stat_multipliers` | 222 triple, mis. gornak 1,2731 / 1,1409 / 1,1409 |
| paritas sel arketipe | `cell_parity_factors` | `cell_parity_factors` | target pool 0,977; 6 faktor sel |
| jangkar rata-rata | loop `fin` | loop `fin` | rata-rata tiap stat = 1,0 (redistribusi) |
| paritas sekolah | loop 8 pass | loop 8 pass | `mini` dan `true` = 1,0 pada fixture (sudah seimbang) |
| jangkar pool | `_pool_mean_rescale` | `pool_mean_rescale` | DPS ×1,093741151 · EHP ×1,089304841 · rata-rata pool 486,1 / 2495,4 |
| koreksi akhir | `_final_fixpoint` | `final_fixpoint` | 1 pass, faktor 0,9998–1,0004 |

Faktor paritas sel yang terkunci:

| Sel | Faktor |
| --- | --- |
| `MAGIC|CARRY` | 0.833 |
| `MAGIC|FIGHTER` | 1.1531 |
| `MAGIC|TANK` | 0.803 |
| `PHYSICAL|CARRY` | 0.8125 |
| `PHYSICAL|FIGHTER` | 1.1685 |
| `PHYSICAL|TANK` | 0.8159 |

## 5. Bukti data yang di-bake

Sisi Godot tidak menghitung balance saat runtime: hasilnya sudah **dibekukan ke data**. Oracle membuktikan kedua arah.

| Data | Jumlah | Bukti |
| --- | --- | --- |
| `data/heroes/*.tres` → `max_hp` / `damage` / `base_skill` | 216 boss hero | sama persis dengan `apply_to_catalog` sisi sumber (`tres_mismatch: []`) |
| `data/heroes/*.tres` starter | 6 hero | sama dengan `starter_catchup_stats(hero, unlocks 0, level 1)` (`starter_gap: []`) |
| `data/bosses/boss_stats.json` `armor` / `magic_resist` | 216 boss | sama dengan `hero_archetypes.BOSS_RESISTANCES` (`data_mismatch: []`) |
| `hero_archetypes.BOSS_RESIST_SCALE` + modifier zero-mean per kelas | 2 kelas | langkah tulis yang sama mereproduksi seluruh 216 baris resist (`scale_mismatch: []`) |

## 6. `hero_archetypes.py` sebagai dependensi

`hero_balance` membaca arketipe dan resistan dari `hero_archetypes`. Karena itu tabelnya ikut diport di layer yang sama ke `scripts/data/hero_archetypes.gd`:

| Data/fungsi | Isi |
| --- | --- |
| `ARCHETYPES` | 222 baris (`MAGIC 120` / `PHYSICAL 102`; `FIGHTER 137` / `TANK 64` / `CARRY 21`; tier S26/A34/B45/C76/D41) |
| `BOSS_RESISTANCES` | 216 baris (armor + magic_resist + profil + kelas) |
| `BOSS_RESIST_BASE` / `_PROFILE_MODS` / `_SCALE` / `_TARGET_RATIO` | 12/0,10 & 18/0,20 · 5 tema · 1,32/1,272 & 1,8 · target 1,0 |
| `get_archetype` / `school_of` | override `dmg_type` manual menang, hero tak dikenal → `derived` fisik |
| `resist_from_profile` / `physical_mitigation` / `get_boss_resistances` | kurva `1 - a·0,06/(1+a·0,06)`, clamp 40 / 0,45, fallback kelas |

## 7. Deviasi terdokumentasi

| # | Simbol | Deviasi | Bukti/uji |
| --- | --- | --- | --- |
| D1 | `pristine_boss_stats` | Python mengimpor `bosses.boss_data` untuk membaca ulang stat mentah; port menerima katalog *pristine* sebagai parameter (data runtime Godot adalah `.tres`, tidak ada modul Python saat runtime). `pristine_boss_stats()` native mengembalikan `{}`. | `hero_balance_checks.gd::_check_apply` (216 baris stat) |
| D2 | `resolve_catalog` | cabang starter membaca `__main__.game_instance.purchased_heroes`; port memakai argumen `unlocks` eksplisit (default 0) | `hero_balance_checks.gd::_check_starters` |
| D3 | `apply_to_catalog` | sumber membungkus `resolve_catalog` dengan `try/except` dan mengembalikan katalog apa adanya bila gagal; GDScript tidak punya padanannya, jadi kegagalan bersifat keras | `hero_balance_checks.gd::_check_apply` |
| D4 | `LAST` | global modul → `static var last_result`, direset tiap `resolve_catalog`/`apply_to_catalog` | `_check_resolve`, `_check_apply` |
| D5 | `_DBG` | log `MYSTIC_DEBUG_BALANCE` ke stderr tidak diport (debug saja) | baris `deviation` di fixture |

Catatan struktur (bukan deviasi perilaku): blok pembangunan pool yang di sumber ditulis inline di dalam `resolve_catalog` diekstrak menjadi `pool_for()` agar bisa diuji sendiri, dan `calibrate_boss_resistances` (jalur tool offline) diuji dengan grid `n_step = 8` alih-alih 25 supaya ringan — skala yang dihasilkan tetap dibandingkan persis dengan eksekusi sumber pada grid yang sama.

## 8. Bukti & sinkronisasi

| Berkas | Isi |
| --- | --- |
| `scripts/data/hero_balance.gd` | port 20 fungsi + 35 konstanta, `last_result` |
| `scripts/data/hero_archetypes.gd` | 222 arketipe + 216 resistan + aritmetika resist |
| `tests/hero_balance_source_oracle.py` | inventaris, klasifikasi 59 simbol, eksekusi pipeline penuh, bukti `.tres`/`boss_stats.json` |
| `tests/fixtures/hero_balance_source.json` | input pristine + 222 multiplier + 216 stat final + pool/paritas/fixpoint + kalibrasi |
| `tests/hero_balance_checks.gd` | replay native seluruh angka di atas |
| `tests/validate_project.py` (blok `9cj`) | fixture == eksekusi Python, token hidup, bukti `.tres` diulang dari validator |
| `.github/workflows/godot-rebuild.yml` | `python godot_rebuild/tests/hero_balance_source_oracle.py --check` |

```bash
python godot_rebuild/tests/hero_balance_source_oracle.py --write
python godot_rebuild/tests/hero_balance_source_oracle.py --check
python godot_rebuild/tests/validate_project.py
```

