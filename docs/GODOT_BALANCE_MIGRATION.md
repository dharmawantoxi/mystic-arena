# Migrasi `hero_balance.py` → Godot (`godot_rebuild/`)

Status: **native GDScript, tanpa Python saat runtime**. Melanjutkan migrasi
`main.py` (#377), `_core.py` (#378), `_entity.py` (#379), `_render.py` (#380),
`_system.py` (#381), dan `hero_archetypes.py` (#382). Python tetap menjadi
oracle kalibrasi; port ini **tidak** membuat angka balance baru.

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| Konstanta/saklar balance | `scripts/core/HeroBalance.gd` + `data/hero_balance.json` | Bobot DPS/EHP, target rasio, blend, compress, clamp multiplier, guard harga/meta, paritas sekolah/sel, jangkar pool, fixpoint, dan catch-up starter. |
| `metrics`, `hero_target`, `stat_multipliers` | `HeroBalance.metrics()`, `hero_target()`, `stat_multipliers()` | DPS basic+skill, EHP armor/MR, budget, target rasio arketipe, guard harga, pembagian sumbu HP/damage/skill. |
| `resolve_catalog` | `HeroBalance.resolve_catalog()` | Paritas sel, jangkar multiplier, paritas sekolah per kelas boss, tabel multiplier final + dbg. Input katalog mentah 222 hero. |
| `pristine_boss_stats`, `apply_to_catalog` | `HeroBalance.pristine_boss_stats()`, `apply_to_catalog()` | Baseline 216 boss dibaca ulang agar idempoten; starter sengaja tidak ditulis ke katalog toko. |
| `_pool_mean_rescale`, `_final_fixpoint` | `HeroBalance.pool_mean_rescale()`, `final_fixpoint()` | Jangkar rata-rata DPS/EHP pool dan koreksi akhir parity sekolah/sel dengan rumus audit. |
| `calibrate_boss_resistances` | `HeroBalance.calibrate_boss_resistances()` | Kalibrasi armor/MR per kelas boss: zero-mean modifier, grid skala, penalti baseline, laporan rasio magic/fisik. |
| `starter_level_factor`, `starter_catchup`, `starter_catchup_stats`, `boss_unlocks_for_purchases` | Metode dengan nama sama | Catch-up 6 starter meluruh terhadap jumlah hero unlock dan level; dipasang saat unit dibuat, bukan dibake ke toko. |
| `_eff_dps`, `_final_power`, `school_mod` | `eff_dps()`, `final_power()`, `school_mod()` | DPS efektif vs armor/MR boss, skor power audit 0.8 DPS + 0.2 EHP, modifier sekolah opsional. |
| `round`, `statistics.median/fmean` | `py_round()`, `py_round_n()`, `median()`, `mean()` | Pembulatan half-to-even dan statistik pool diuji terhadap baterai oracle Python. |

## Arsitektur runtime

```
CoreData
  ├── archetypes: HeroArchetypes
  └── balance: HeroBalance
        ├── constants + pristine_boss_stats (kontrak fail-closed)
        ├── resolve_catalog / apply_to_catalog / calibrate (native, diuji parity)
        └── starter_catchup* + boss_unlocks_for_purchases

MatchModel.buy_hero / EntityAI._buy_hero
  └── boss_unlocks_for_purchases(purchased_heroes)
        └── BattleUnit.setup_hero(..., boss_unlocks)
              └── starter catch-up hanya untuk 6 starter, saat unit dibuat

MenuView / CoreData.hero()
  └── angka katalog final hasil bake Python (starter tetap angka dasar)
```

- Katalog hero final di `core_data.json` tetap hasil `prepare_godot_core.py`
  yang memanggil `hero_balance.apply_to_catalog()` asli. Native `HeroBalance`
  dapat menghitung ulang katalog yang sama dan dikunci parity, tetapi runtime
  tidak menjalankan kalibrasi penuh tiap load agar deterministik dan murah.
- `CoreData.valid()` menolak kontrak balance yang hilang/rusak, sehingga game
  tidak diam-diam berjalan tanpa catch-up atau dengan baseline yang salah.
- Catch-up starter bergantung state pemain. Karena itu toko/preview menampilkan
  angka dasar, sedangkan bonus diberikan saat `BattleUnit.setup_hero()`.
- `MatchModel` dan AI merah memakai jumlah unlock dari roster yang sama:
  entri non-starter dihitung, duplikat tetap dihitung seperti Python.

## Kontrak data & tooling

```bash
# Setelah mengubah hero_balance.py, hero_archetypes.py, atau katalog hero/boss:
python3 tools/prepare_godot_core.py
python3 tools/prepare_godot_archetypes.py
python3 tools/prepare_godot_balance.py
python3 tools/prepare_godot_balance.py --check
python3 tools/test_godot_balance_prepare.py
```

`prepare_godot_balance.py` mengimpor modul balance murni (tanpa pygame),
memakai katalog mentah yang sama dengan `prepare_godot_core.py`, lalu:

1. menjalankan `apply_to_catalog()` Python asli dan memverifikasi hasilnya
   cocok dengan `core_data.json` (stat final + `__bal`);
2. menulis `godot_rebuild/data/hero_balance.json`: saklar, konstanta,
   6 starter, dan 216 pristine boss;
3. menulis `godot_rebuild/tests/fixtures/hero_balance_parity.json`: katalog
   mentah, tabel multiplier, stat final, metrik, laporan parity/jangkar/fixpoint,
   grid catch-up, kasus unlock, kalibrasi resistansi, helper numerik, fixpoint
   cell-band, dan varian resolve.

Fixture membedakan `resolve_table` (hasil `resolve_catalog()` sebelum anchor
pool/fixpoint) dari `table` (hasil akhir di `LAST["table"]`). Di Python,
`apply_to_catalog()` menyimpan dict multiplier yang sama ke `__bal`, sehingga
anchor/fixpoint memutasi tabel debug secara in-place. Native menguji kedua tahap
terhadap oracle yang sesuai, bukan membandingkan hasil antara tahap yang berbeda.

`--check` membandingkan byte secara deterministik (JSON sort-key) dan tidak
menulis apa pun. Hash sumber bergeser, katalog core basi, cakupan kurang, atau
nilai non-finite membuat gate gagal. SHA-256 kontrak saat migrasi:
`21f081a432de`.

## Integrasi CI

- Path filter `godot-check.yml` dan `godot-rebuild.yml` mencakup `hero_balance.py`
  serta tool prepare/test balance.
- Kedua workflow menjalankan `prepare_godot_balance.py --check` dan
  `test_godot_balance_prepare.py` setelah kontrak core/archetypes siap.
- `validate_project.py` memeriksa modul, hash, cakupan 216/6, konstanta sumber,
  wiring CoreData/BattleUnit/MatchModel/EntityAI, dan gate CI.
- `run_all.gd` memanggil `HeroBalanceParityTest.run()` untuk membandingkan
  runtime GDScript dengan oracle Python dan menguji catch-up runtime.

## Batasan yang jujur

- Tidak ada rebalance baru. Semua angka tetap berasal dari `hero_balance.py`
  dan katalog sumber; port hanya memindahkan kalkulator dan mengunci parity.
- Catch-up runtime diterapkan setelah kompensasi melee native dan hanya untuk
  starter. Ini sengaja tidak menyalin efek samping `_entity.Hero` yang memanggil
  `starter_catchup_stats` untuk semua hero lalu mereset base stat non-starter ke
  angka katalog mentah. Fungsi helper sendiri tetap parity dengan Python.
- Atribut item `magic_only` tetap berbasis role seperti `hero_items.py`, terpisah
  dari sekolah damage dan balance.
- `ENABLE_REBUDGET` dan beberapa saklar lain diekspor apa adanya mengikuti
  sumber; sebagian bersifat desain/audit dan tidak semua menjadi cabang runtime
  baru di port ini.
- Verifikasi headless tidak membuktikan piksel GPU, perangkat Android, audio,
  Play Games, top-up produksi, atau signing keystore. Lihat
  `GODOT_BALANCE_VERIFICATION.md` untuk hasil uji aktual.
