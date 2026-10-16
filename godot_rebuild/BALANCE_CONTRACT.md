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
| starter gap | 5.67x (sumber) / **3.97x produksi native** (S1) | <= 4.0x (arahan 2026-10-16) | **tercapai via override 9c** |
| violations audit | **[]** | kosong | **sehat** |

Sel identity grid (power, sumber): MAGIC|CARRY 0.84 (n=11), MAGIC|FIGHTER 0.84 (n=82),
MAGIC|TANK 1.02 (n=25), PHYSICAL|CARRY 1.19 (n=10), PHYSICAL|FIGHTER 1.18
(n=49), PHYSICAL|TANK 1.38 (n=39) — produksi native sesudah S2: **1.25**. Balance pass: 216 hero, hp_mult
0.7189..1.3868, dmg_mult 0.5851..2.0474; saklar `hero_balance.py`:
`ENABLE_REBUDGET=True`, `ENABLE_SCHOOL_MOD=False`, `ENABLE_STARTER_CATCHUP=True`.

Kesimpulan layer 9b: **tidak ada pelanggaran terukur di katalog produksi** —
karena itu tidak ada angka hero/boss yang diubah. Sel terpanas
(PHYSICAL|TANK 1.38) masih di dalam penerimaan pass 2026-08-30 (spread
identity 1.6x adalah target yang dikejar pass itu).

## Lapisan override native (layer 9c) — mekanisme rebalance

Permintaan "rebalance" (2026-10-16) dijawab dua lapis: baseline terukur (9b,
di atas) dan **mekanisme perubahan angka** (`scripts/data/balance_overrides.gd`):

- Satu-satunya permukaan native tempat deviasi rebalance yang disengaja dari
  katalog paritas-sumber boleh hidup. Tabel produksi `HERO_OVERRIDES`
  **KOSONG by decision**: audit `--ingame` melaporkan nol pelanggaran di
  semua target yang ditegakkan alat; deviasi band prosa (MAGIC|CARRY dan
  MAGIC|FIGHTER power 0.84 — satu tick di bawah lantai prosa 0.85;
  PHYSICAL|TANK 1.38 di atas cap prosa 1.25) adalah trade yang DITERIMA pass
  balance sumber 2026-08-30 (spread identity 1.6x adalah hasil yang dikejar
  pass itu sendiri). Menggerakkan angka pool tanpa arahan playtest = opini,
  bukan pengukuran.
- Kontrak entri: `"damage_mult"` (default 1.0) dan `"hp_mult"` (default 1.0)
  per hero id, plus `"reason"` WAJIB (metrik yang bergerak + alasan). Reader
  murni menolak nilai non-numerik, <= 0, dan non-finite kembali ke 1.0.
- Titik aplikasi: HANYA spawn produksi — `prototype_battle.
  _spawn_production_hero` (4 call site: dua Kaizen awal, purchase biru,
  purchase merah/AI) merutekan `spawn_hero` lalu menerapkan multiplier pada
  `base_hp`/`base_damage` sebelum `apply_level_stats()` ulang (kurva level
  ikut mengalikan, hp spawn penuh). Lab tempur (`minion_battle.gd::
  spawn_hero` langsung) TETAP di jalur paritas sumber — nilai QA lab tidak
  boleh bergeser oleh rebalance produksi.
- Dengan tabel kosong, wrapper adalah no-op yang dibuktikan suite
  `balance_override_layer_checks.gd` (spawn terute == spawn langsung, stat
  `.tres` utuh); suite yang sama menolak entri tanpa reason dan memaku
  tabel kosong — entri pertama harus mengupdate suite + baseline + PETA
  dengan angka sebelum/sesudah secara sengaja.

## Rebalance terarah (arahan pengguna 2026-10-16) — entri override aktif

Fixture 9b `balance_baseline_ingame.json` TIDAK berubah: override native tidak
terlihat oleh audit sumber. Angka "depois" dihitung dengan rumus audit yang
sama (`dps = base_damage*60/cd + skill_base*60/skill_cd`) di atas baris
hero audit, dipaku di suite native + `validate_project.py`.

| Slice | Entri | Antes | Depois | Bukti |
|---|---|---|---|---|
| S1 starter catch-up | kaizen/thorne/grimjaw/sylara/vex/zephyr `damage_mult 1.5` | starter avg dps 85.7, gap 5.67x | starter avg dps 122.5, gap **3.97x** (<= 4.0x) | `balance_override_layer_checks.gd`: spawn produksi Kaizen damage 45 -> 68, lab tetap 45 |
| S2 nerf PHYSICAL\|TANK | 39 hero sel PHYSICAL\|TANK `damage_mult 0.85` | power sel 1.38 (avg dps 646.2, ehp 3069) | power sel **1.25** (avg dps 571.0, ehp tetap); spread 1.47x, corr 0.484, school 1.045/1.094, price 1.85x, pool dps 0.972 — violations tetap [] | suite: spawn produksi Akaroth damage 320 -> 272 |

Titik aplikasi (revisi S1): tabel hanya diterapkan bila dunia dibuka oleh
alur match playable — `app.gd` memanggil `PrototypeSession.
enable_balance_overrides()` (set `Prototype.balance_overrides_enabled = true`)
sebelum `setup_arena`. Dunia yang dibangun langsung (lab tempur, suite
paritas-sumber, oracle) membiarkan flag mati sehingga fixture sumber Python
(mis. `ai_upgrade` damage Kaizen 45) tetap valid; suite override membuktikan
keduanya (flag mati -> 45, flag hidup -> 68).

Pemilihan S1: multiplier hanya menggerakkan porsi auto-attack (skill tidak
dikalikan, cermin `HeroState.apply_level_stats`), jadi 1.42 (estimasi linear
penuh) tidak cukup; sapuan 0.01 memberi 1.45 -> 4.12x, 1.49 -> 4.00x (tepi),
1.5 -> 3.97x. Dipilih multiplier bulat terkecil yang lolos: **1.5**. HP starter
tidak disentuh. Damage produksi: kaizen 68, thorne 62, grimjaw 63, sylara 86,
vex 65, zephyr 51.

Pemilihan S2: rumus power sel audit (`0.8*avg_dps/med_dps +
0.2*avg_ehp/med_ehp`) dihitung ulang di atas baris hero audit dengan
multiplier seragam pada sel (damage -> porsi auto-attack, hp -> ehp linear):
damage_mult 0.90 -> 1.29, 0.88 -> 1.28, 0.86 -> 1.26, **0.85 -> 1.25**;
hp_mult sendirian butuh 0.5 (corr jatuh ke -0.03); campuran (0.9/0.8,
0.88/0.9) tidak lebih kecil. Sel lain bergeser <= 0.01 (MAGIC|CARRY 0.84 ->
0.85). Tabel baseline 9b di atas tetap angka sumber; angka produksi native
adalah kolom "Depois".

## Catatan yang tetap berlaku

- **Troll lab** (`COMBAT_CONTRACT.md`): regen 0.6 HP/tick (36 HP/detik) di
  lab duel adalah paritas sumber yang SENGAJA; jangan diubah diam-diam. Duel
  cepat untuk uji kill pakai Goblin/Orc. Perubahan angka lab hanya lewat
  doktrin di atas.
- Rebalance produksi (di luar baseline sehat ini) membutuhkan arahan desain
  eksplisit pengguna; arahan 2026-10-16 (S1 starter gap) sudah terpasang di
  tabel di atas. Kandidat lain diukur ulang lewat audit yang sama.

## Regenerasi baseline

```sh
python godot_rebuild/tests/balance_baseline_source_oracle.py   # tulis fixture
python godot_rebuild/tests/validate_project.py                 # drift pin
```

Oracle membuat stub pygame-nya sendiri di direktori temp (tidak butuh pygame
terpasang, tidak butuh display); CI menjalankannya sebagai baris terdaftar di
`godot-rebuild.yml` sesudah `boss_shake_sites_source_oracle.py`.
