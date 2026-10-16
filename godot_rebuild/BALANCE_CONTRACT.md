# Kontrak Balance (layer 9b)

Dokumen ini merekam **baseline balance terukur** katalog hero dan doktrin
untuk setiap perubahan angka berikutnya. Dibuka oleh permintaan pengguna
"rebalance" (2026-10-16); sebelum layer ini tidak ada baseline yang dipaku CI.

## Doktrin

1. **Audit mengukur, bukan opini.** Satu-satunya alat ukur adalah
   `tools/balance_audit.py` milik proyek sendiri (rumus identik dengan yang
   menjadi dasar `hero_balance.py` — "kalau tidak, lolos test tidak berarti
   apa-apa"). Mode `--ingame` = angka final setelah balance pass (yang
   dirasakan pemain); mode `--static` = data mentah `bosses/boss_data.py`.
2. **Sumber Python read-only.** `hero_balance.py`, `boss_data.py`, `_core.py`
   tidak pernah diedit dari sisi rebuild. Katalog native (`data/heroes/*.tres`)
   memaku nilai pasca-balance sumber dan dijaga oracle kit 222.
3. **Baseline dipaku CI.** `tests/balance_baseline_source_oracle.py`
   menjalankan audit `--ingame` secara headless (stub pygame MagicMock via
   PYTHONPATH — tanpa engine/display), memaku snapshot metrik persis ke
   `tests/fixtures/balance_baseline_ingame.json`, dan suite native
   `tests/balance_baseline_checks.gd` (terdaftar di `run_all.gd`) memaku nilai
   yang sama dari sisi Godot. Fixture tidak boleh diedit manual; regenerasi
   hanya lewat oracle.
4. **Rebalance = pergerakan metrik yang disengaja.** Setiap slice rebalance
   berikutnya wajib: (a) menyebut metrik target yang bergerak dan alasannya,
   (b) menerapkan perubahan HANYA di lapisan native (data `.tres` + oracle
   kit-nya, atau lapisan override runtime eksplisit bila paritas sumber harus
   tetap terlihat), (c) regenerate baseline fixture lewat oracle, dan
   (d) melampirkan angka audit sebelum/sesudah di PETA.

## Baseline terukur (snapshot 2026-10-16, `--ingame`, n=222 hero / 216 boss hero)

| Metrik | Nilai | Target alat | Status |
|---|---|---|---|
| corr(HP, DPS) | 0.535 | <= 0.80 | sehat (trade-off arketipe nyata) |
| identity spread | 1.64x | >= 1.20 | sehat |
| school ratio (mini/true) | 1.000 / 1.001 | 0.90..1.15 | sehat |
| boss pref (p90/p10) | 1.49 | >= 1.20 | sehat ("bawa hero sesuai lawan" terasa) |
| price spread in-band | 1.89x | <= 2.20 | sehat |
| pool power delta (DPS/EHP) | 1.000 / 1.000 | max 0.12 | redistribusi, bukan buff/nerf global |
| starter gap | 5.67x | (informasional; 8.51x sebelum pass) | membaik |
| violations audit | **[]** | kosong | **sehat** |

Sel identity grid (power): MAGIC|CARRY 0.84 (n=11), MAGIC|FIGHTER 0.84 (n=82),
MAGIC|TANK 1.02 (n=25), PHYSICAL|CARRY 1.19 (n=10), PHYSICAL|FIGHTER 1.18
(n=49), PHYSICAL|TANK 1.38 (n=39). Balance pass: 216 hero, hp_mult
0.7189..1.3868, dmg_mult 0.5851..2.0474; saklar `hero_balance.py`:
`ENABLE_REBUDGET=True`, `ENABLE_SCHOOL_MOD=False`, `ENABLE_STARTER_CATCHUP=True`.

Kesimpulan layer 9b: **tidak ada pelanggaran terukur di katalog produksi** —
karena itu tidak ada angka hero/boss yang diubah. Sel terpanas
(PHYSICAL|TANK 1.38) masih di dalam penerimaan pass 2026-08-30 (spread
identity 1.6x adalah target yang dikejar pass itu).

## Catatan yang tetap berlaku

- **Troll lab** (`COMBAT_CONTRACT.md`): regen 0.6 HP/tick (36 HP/detik) di
  lab duel adalah paritas sumber yang SENGAJA; jangan diubah diam-diam. Duel
  cepat untuk uji kill pakai Goblin/Orc. Perubahan angka lab hanya lewat
  doktrin di atas.
- Rebalance produksi (di luar baseline sehat ini) membutuhkan arahan desain
  eksplisit pengguna: kandidat yang bisa diukur ulang kapan saja lewat audit
  yang sama (mis. starter gap, sel grid terpanas, band harga tertentu).

## Regenerasi baseline

```sh
python godot_rebuild/tests/balance_baseline_source_oracle.py   # tulis fixture
python godot_rebuild/tests/validate_project.py                 # drift pin
```

Oracle membuat stub pygame-nya sendiri di direktori temp (tidak butuh pygame
terpasang, tidak butuh display); CI menjalankannya sebagai baris terdaftar di
`godot-rebuild.yml` sesudah `boss_shake_sites_source_oracle.py`.
