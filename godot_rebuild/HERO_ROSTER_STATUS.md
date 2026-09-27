# Daftar tepat migrasi hero — 195 playable, 27 pending

Target tetap **222**, bukan selesai. Registry native eksplisit:
`scripts/data/hero_roster.gd`. Manifest mesin: `data/ai/hero_migration_status.json`.
CI Godot 4.7.2: run terakhir hijau 36325917893 (194 playable, 28 pending;
batch 10–15 level 9–13 + perbaikan tes batch 9).

- Enam starter selesai (empat sudah ada sebelum sesi); tiga puluh delapan boss
  recipe khusus selesai (L1×4, Alchemist, AA, Nyzrak, Ignis, L5×2, L6×4, L7×4, L9–L13 ×4);
  150 boss mengikuti jalur `_fallback_cast` yang **benar-benar dipakai sumber**,
  dibuktikan per ID. Ini bukan fallback native untuk boss pending.
- Semua 27 pending mempunyai recipe khusus. Blocker masing-masing: empat
  metode sumber yang tercantum belum diport/diberi source oracle dan tes native.
  Semua ditolak transaksi tanpa debit maupun substitusi; bukan sekadar kurang art.
- “Playable” berarti kit/domain native tervalidasi, bukan AIPlayer otomatis,
  unlock UI lengkap, item/forge atau art final. Scene tetap dua Kaizen gratis
  dan defender lama. Python asli tidak diubah.

## Selesai — 195 ID

| ID | Level sumber (0=starter) | Summon G | Handler native | Oracle + tes native |
|---|---:|---:|---|---|
| `grimjaw` | 0 | 450 | `grimjaw_skills.gd` | `grimjaw_source_oracle.py` / `grimjaw_checks.gd` |
| `kaizen` | 0 | 400 | `minion_battle.gd` | `kaizen_source_oracle.py` / `kaizen_checks.gd` |
| `sylara` | 0 | 380 | `sylara_skills.gd` | `sylara_source_oracle.py` / `sylara_checks.gd` |
| `thorne` | 0 | 500 | `thorne_skills.gd` | `thorne_source_oracle.py` / `thorne_checks.gd` |
| `vex` | 0 | 420 | `vex_skills.gd` | `starter_finish_source_oracle.py` / `starter_finish_checks.gd` |
| `zephyr` | 0 | 420 | `zephyr_skills.gd` | `starter_finish_source_oracle.py` / `starter_finish_checks.gd` |
| `abaddon` | 1 | 700 | `boss_level_one_skills.gd` | `boss_level_one_source_oracle.py` / `boss_level_one_checks.gd` |
| `drakar` | 1 | 600 | `boss_level_one_skills.gd` | `boss_level_one_source_oracle.py` / `boss_level_one_checks.gd` |
| `gornak` | 1 | 500 | `boss_level_one_skills.gd` | `boss_level_one_source_oracle.py` / `boss_level_one_checks.gd` |
| `morgath` | 1 | 550 | `boss_level_one_skills.gd` | `boss_level_one_source_oracle.py` / `boss_level_one_checks.gd` |
| `alchemist` | 2 | 750 | `alchemist_skills.gd` | `alchemist_source_oracle.py` / `alchemist_checks.gd` |
| `ancient_apparition` | 3 | 800 | `boss_level_three_skills.gd` | `boss_level_three_source_oracle.py` / `boss_level_three_checks.gd` |
| `nyzrak` | 3 | 850 | `boss_level_three_skills.gd` | `boss_level_three_source_oracle.py` / `boss_level_three_checks.gd` |
| `ignis_drachorn` | 4 | 850 | `boss_level_four_skills.gd` | `boss_level_four_source_oracle.py` / `boss_level_four_checks.gd` |
| `vhalzun` | 5 | 1200 | `boss_level_five_skills.gd` | `boss_level_five_source_oracle.py` / `boss_level_five_checks.gd` |
| `krobellus` | 5 | 1500 | `boss_level_five_skills.gd` | `boss_level_five_source_oracle.py` / `boss_level_five_checks.gd` |
| `kunkka` | 6 | 900 | `boss_level_six_skills.gd` | `boss_level_six_source_oracle.py` / `boss_level_six_checks.gd` |
| `gravewake` | 6 | 1000 | `boss_level_six_skills.gd` | `boss_level_six_source_oracle.py` / `boss_level_six_checks.gd` |
| `syrentha` | 6 | 1100 | `boss_level_six_skills.gd` | `boss_level_six_source_oracle.py` / `boss_level_six_checks.gd` |
| `thalgryn` | 6 | 1200 | `boss_level_six_skills.gd` | `boss_level_six_source_oracle.py` / `boss_level_six_checks.gd` |
| `akashari` | 7 | 1200 | `boss_level_seven_skills.gd` | `boss_level_seven_source_oracle.py` / `boss_level_seven_checks.gd` |
| `malzareth` | 7 | 1100 | `boss_level_seven_skills.gd` | `boss_level_seven_source_oracle.py` / `boss_level_seven_checks.gd` |
| `nyxarath` | 7 | 1000 | `boss_level_seven_skills.gd` | `boss_level_seven_source_oracle.py` / `boss_level_seven_checks.gd` |
| `vorenmarr` | 7 | 1300 | `boss_level_seven_skills.gd` | `boss_level_seven_source_oracle.py` / `boss_level_seven_checks.gd` |
| `kenshiro` | 9 | 1300 | `boss_level_nine_skills.gd` | `boss_level_nine_source_oracle.py` / `boss_level_nine_checks.gd` |
| `wiro` | 9 | 1300 | `boss_level_nine_skills.gd` | `boss_level_nine_source_oracle.py` / `boss_level_nine_checks.gd` |
| `khazan` | 9 | 1350 | `boss_level_nine_skills.gd` | `boss_level_nine_source_oracle.py` / `boss_level_nine_checks.gd` |
| `naraka` | 9 | 2000 | `boss_level_nine_skills.gd` | `boss_level_nine_source_oracle.py` / `boss_level_nine_checks.gd` |
| `krognarr` | 10 | 1400 | `boss_level_ten_skills.gd` | `boss_level_ten_source_oracle.py` / `boss_level_ten_checks.gd` |
| `raz` | 10 | 1400 | `boss_level_ten_skills.gd` | `boss_level_ten_source_oracle.py` / `boss_level_ten_checks.gd` |
| `vraskhan` | 10 | 1400 | `boss_level_ten_skills.gd` | `boss_level_ten_source_oracle.py` / `boss_level_ten_checks.gd` |
| `aurethzar` | 10 | 2100 | `boss_level_ten_skills.gd` | `boss_level_ten_source_oracle.py` / `boss_level_ten_checks.gd` |
| `aeralith` | 11 | 1450 | `boss_level_eleven_skills.gd` | `boss_level_eleven_source_oracle.py` / `boss_level_eleven_checks.gd` |
| `aurex` | 11 | 1500 | `boss_level_eleven_skills.gd` | `boss_level_eleven_source_oracle.py` / `boss_level_eleven_checks.gd` |
| `nyxareva` | 11 | 1500 | `boss_level_eleven_skills.gd` | `boss_level_eleven_source_oracle.py` / `boss_level_eleven_checks.gd` |
| `thalakryon` | 11 | 2200 | `boss_level_eleven_skills.gd` | `boss_level_eleven_source_oracle.py` / `boss_level_eleven_checks.gd` |
| `aurelix` | 12 | 1550 | `boss_level_twelve_skills.gd` | `boss_level_twelve_source_oracle.py` / `boss_level_twelve_checks.gd` |
| `aurelyssa` | 12 | 1550 | `boss_level_twelve_skills.gd` | `boss_level_twelve_source_oracle.py` / `boss_level_twelve_checks.gd` |
| `vargrath` | 12 | 1600 | `boss_level_twelve_skills.gd` | `boss_level_twelve_source_oracle.py` / `boss_level_twelve_checks.gd` |
| `nazulmor` | 12 | 2300 | `boss_level_twelve_skills.gd` | `boss_level_twelve_source_oracle.py` / `boss_level_twelve_checks.gd` |
| `kaeldris` | 13 | 1650 | `boss_level_thirteen_skills.gd` | `boss_level_thirteen_source_oracle.py` / `boss_level_thirteen_checks.gd` |
| `pyraklos` | 13 | 1700 | `boss_level_thirteen_skills.gd` | `boss_level_thirteen_source_oracle.py` / `boss_level_thirteen_checks.gd` |
| `velmyrth` | 13 | 1700 | `boss_level_thirteen_skills.gd` | `boss_level_thirteen_source_oracle.py` / `boss_level_thirteen_checks.gd` |
| `solvarin` | 13 | 2400 | `boss_level_thirteen_skills.gd` | `boss_level_thirteen_source_oracle.py` / `boss_level_thirteen_checks.gd` |
| `azureth` | 14 | 1700 | `boss_level_fourteen_skills.gd` | `boss_level_fourteen_source_oracle.py` / `boss_level_fourteen_checks.gd` |
| `gorath` | 2 | 750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `khalros` | 2 | 700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `razak` | 2 | 650 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `varkul` | 3 | 750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xerathis` | 3 | 800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `pyrenth` | 4 | 750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vokrahn` | 4 | 850 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zharok` | 4 | 650 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `gravefang` | 5 | 1100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxara` | 5 | 950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vaerith` | 8 | 1200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vhorethzir` | 8 | 1000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vhyssarion` | 8 | 1200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xirthalis` | 8 | 1200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kurogari` | 21 | 2800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morvekhar` | 21 | 3000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nexthyrius` | 21 | 3200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vorgath` | 21 | 2900 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `grimstalker` | 22 | 2950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kryvoxar` | 22 | 3000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `molgravar` | 22 | 3300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vargroth` | 22 | 3100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `drav` | 23 | 3100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `lyrienne` | 23 | 3200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `seraphienne` | 23 | 3400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `valthar` | 23 | 3300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `khalzaredh` | 24 | 3250 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxaroth` | 24 | 3350 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `solareth` | 24 | 3500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `veshtrax` | 24 | 3400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `grimjack` | 25 | 3450 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morvaeth` | 25 | 3500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `okeanora` | 25 | 3600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vulkareth` | 25 | 3550 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `aelyrion` | 26 | 3600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaervosth` | 26 | 3650 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morvyssk` | 26 | 3700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vaelmyrra` | 26 | 3700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kyumirra` | 27 | 3750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morvakhul` | 27 | 3800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxariel` | 27 | 3850 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zarethyr` | 27 | 3800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morthyrax` | 28 | 3950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyrethzalv` | 28 | 3900 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `sanguiveth` | 28 | 4000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xerakhotep` | 28 | 4050 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `ignakhor` | 29 | 4100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kazureth` | 29 | 4200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyrellieth` | 29 | 4000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `sethrakhar` | 29 | 4250 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaelvyrn` | 30 | 4300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxharr` | 30 | 4200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `thorvin` | 30 | 4350 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xaerissa` | 30 | 4400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `celwynn` | 31 | 4500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `ravokkar` | 31 | 4400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `rynvara` | 31 | 4550 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `syrindra` | 31 | 4600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `ghrakmaal` | 32 | 4700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `malzeroth` | 32 | 4600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `selunara` | 32 | 4750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vessyra` | 32 | 4800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `rakzhan` | 33 | 4900 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `sirakzan` | 33 | 4950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `valekris` | 33 | 5000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zharakzuul` | 33 | 4800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `grondmauris` | 34 | 5000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `infrakzaar` | 34 | 5100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xarnathul` | 34 | 5150 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zhyrakaan` | 34 | 5200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaerissa` | 35 | 5300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `lyssarethys` | 35 | 5200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `thorgaruk` | 35 | 5350 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zorathiel` | 35 | 5400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaerinya` | 36 | 5400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxallaria` | 36 | 5500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vhaerinth` | 36 | 5550 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xharokh` | 36 | 5600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kazreth` | 37 | 5700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `varkuthar` | 37 | 5750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xelnarath` | 37 | 5600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zhyvrek` | 37 | 5800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `azkharion` | 38 | 5900 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kyrenzai` | 38 | 5800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `thargoroth` | 38 | 5950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zahkareth` | 38 | 6000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `bhorgathul` | 39 | 6100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morkhelvis` | 39 | 6150 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vorthakul` | 39 | 6200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xaelmoran` | 39 | 6000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `thalryndel` | 40 | 6200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `urgharun` | 40 | 6300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `yhoranth` | 40 | 6350 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zulkhaven` | 40 | 6400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `emberwick` | 41 | 6500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `grimkor` | 41 | 6400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `grondarthul` | 41 | 6550 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xareth` | 41 | 6600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaedrin` | 42 | 6700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaineroth` | 42 | 6600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morvaeth2` | 42 | 6750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vardrok` | 42 | 6800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nixweaver` | 43 | 6900 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxraal` | 43 | 6950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xarnthuul` | 43 | 7000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zyvareth` | 43 | 6800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kagetsuka` | 44 | 7000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `lyrenya` | 44 | 7100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vyraeth` | 44 | 7150 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zorothrax` | 44 | 7200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `akiraze` | 45 | 7300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `brumhar` | 45 | 7350 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `deidara` | 45 | 7200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zorashi` | 45 | 7400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `akaroth` | 46 | 7500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kassadin` | 46 | 7550 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `shimorakh` | 46 | 7600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `sunakage` | 46 | 7400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaizoku_raijin` | 47 | 7700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `korokai` | 47 | 7750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `pyraena` | 47 | 7600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `verdanix` | 47 | 7800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `broggmar` | 48 | 7900 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `cogsworth` | 48 | 7800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `ursath` | 48 | 7950 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `zhaeris` | 48 | 8000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kairenji` | 49 | 8150 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `karzhul` | 49 | 8200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `xerakkuth` | 49 | 8100 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `yomigetsu` | 49 | 8000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `akirakumo` | 50 | 8200 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaelthys` | 50 | 8300 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaoruken` | 50 | 8350 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vaelkorr` | 50 | 8250 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `aurelian` | 51 | 8450 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kaithros` | 51 | 8400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `morvath` | 51 | 8500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `pyrhaan` | 51 | 8400 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `garumenshi` | 52 | 8550 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `nyxaris` | 52 | 8600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `thoraz` | 52 | 8600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `vhaerith` | 52 | 8500 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `dorakai` | 53 | 8650 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `hitokage` | 53 | 8700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `kazuren` | 53 | 8600 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `tsukiyora` | 53 | 8800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `hollowbane` | 54 | 9000 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `obanai` | 54 | 8750 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `sanguire` | 54 | 8700 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |
| `sasori` | 54 | 8800 | `source_shared_boss_skills.gd` | `source_shared_boss_oracle.py` / `source_shared_boss_checks.gd` |

## Belum selesai — 27 ID dan recipe yang menjadi blocker

| ID | Level sumber | Summon G | Metode Q / W / E / R sumber yang belum diport & diuji |
|---|---:|---:|---|
| `luminar` | 14 | 1750 | `_cast_q_luminar_illuminate` / `_cast_w_luminar_blindinglight` / `_cast_e_luminar_wisp` / `_cast_r_luminar_spiritform` |
| `pyraethis` | 14 | 2500 | `_cast_q_pyraethis_icarusdive` / `_cast_w_pyraethis_firespirits` / `_cast_e_pyraethis_sunray` / `_cast_r_pyraethis_supernova` |
| `solara` | 14 | 1800 | `_cast_q_solara_starbreaker` / `_cast_w_solara_celestialhammer` / `_cast_e_solara_luminosity` / `_cast_r_solara_solarguardian` |
| `auroth` | 15 | 1850 | `_cast_q_auroth_ionicedge` / `_cast_w_auroth_ward` / `_cast_e_auroth_consecration` / `_cast_r_auroth_guardian` |
| `morvein` | 15 | 1900 | `_cast_q_morvein_puncture` / `_cast_w_morvein_violentstrike` / `_cast_e_morvein_spectralcharge` / `_cast_r_morvein_phantomform` |
| `thorvak` | 15 | 1950 | `_cast_q_thorvak_seed` / `_cast_w_thorvak_natureswrath` / `_cast_e_thorvak_vengeance` / `_cast_r_thorvak_dryad` |
| `yamako` | 15 | 2600 | `_cast_q_yamako_deepforest` / `_cast_w_yamako_woodcreation` / `_cast_e_yamako_woodgolem` / `_cast_r_yamako_kannon` |
| `ignirus` | 16 | 2000 | `_cast_q_ignirus_searingtorrent` / `_cast_w_ignirus_flameshot` / `_cast_e_ignirus_burstfireball` / `_cast_r_ignirus_vengeance` |
| `leoric` | 16 | 2050 | `_cast_q_leoric_fearlesscharge` / `_cast_w_leoric_sacredhammer` / `_cast_e_leoric_concealblast` / `_cast_r_leoric_immortality` |
| `seiryukong` | 16 | 2700 | `_cast_q_seiryukong_boundless` / `_cast_w_seiryukong_treedance` / `_cast_e_seiryukong_jingusoldiers` / `_cast_r_seiryukong_wukong` |
| `shirotaka` | 16 | 2100 | `_cast_q_shirotaka_hiraishin` / `_cast_w_shirotaka_waterboundary` / `_cast_e_shirotaka_shadowclones` / `_cast_r_shirotaka_paperbomb` |
| `kaelthorn` | 17 | 2150 | `_cast_q_kaelthorn_bravestfighter` / `_cast_w_kaelthorn_justiceblade` / `_cast_e_kaelthorn_defendersassault` / `_cast_r_kaelthorn_chivalryfists` |
| `nyxareth` | 17 | 2800 | `_cast_q_nyxareth_starsplit` / `_cast_w_nyxareth_realworld` / `_cast_e_nyxareth_spacetime` / `_cast_r_nyxareth_astrorealm` |
| `solvanth` | 17 | 2200 | `_cast_q_solvanth_ringpunishment` / `_cast_w_solvanth_gloriouspathway` / `_cast_e_solvanth_laworder` / `_cast_r_solvanth_wrath` |
| `xyrael` | 17 | 2250 | `_cast_q_xyrael_finch` / `_cast_w_xyrael_defiant` / `_cast_e_xyrael_tempest` / `_cast_r_xyrael_lightness` |
| `aurelion` | 18 | 2900 | `_cast_q_aurelion_callcourage` / `_cast_w_aurelion_guardianassault` / `_cast_e_aurelion_kingscommand` / `_cast_r_aurelion_kingssummon` |
| `cryssalia` | 18 | 2300 | `_cast_q_cryssalia_frostshock` / `_cast_w_cryssalia_bitterfrost` / `_cast_e_cryssalia_frostbites` / `_cast_r_cryssalia_coldest` |
| `kaelthar` | 18 | 2350 | `_cast_q_kaelthar_chargingfist` / `_cast_w_kaelthar_quake` / `_cast_e_kaelthar_fistcrack` / `_cast_r_kaelthar_fistbreak` |
| `morkhaera` | 18 | 2400 | `_cast_q_morkhaera_spiritburst` / `_cast_w_morkhaera_airstrike` / `_cast_e_morkhaera_energyimpact` / `_cast_r_morkhaera_ethereal` |
| `akahime` | 19 | 2450 | `_cast_q_akahime_petalbarrage` / `_cast_w_akahime_soulscroll` / `_cast_e_akahime_shadow` / `_cast_r_akahime_higanbana` |
| `nyxthrael` | 19 | 2500 | `_cast_q_nyxthrael_ambush` / `_cast_w_nyxthrael_nightfall` / `_cast_e_nyxthrael_darknightfall` / `_cast_r_nyxthrael_shadowbringer` |
| `sylvantheros` | 19 | 2550 | `_cast_q_sylvantheros_sprout` / `_cast_w_sylvantheros_teleport` / `_cast_e_sylvantheros_treants` / `_cast_r_sylvantheros_wrath` |
| `vaelindra` | 19 | 3000 | `_cast_q_vaelindra_energywave` / `_cast_w_vaelindra_spacering` / `_cast_e_vaelindra_violetrequiem` / `_cast_r_vaelindra_realm` |
| `astraelion` | 20 | 2600 | `_cast_q_astraelion_swordfall` / `_cast_w_astraelion_spiritblade` / `_cast_e_astraelion_forceescape` / `_cast_r_astraelion_zeroreturn` |
| `morthraxis` | 20 | 3100 | `_cast_q_morthraxis_batimpale` / `_cast_w_morthraxis_sanguine` / `_cast_e_morthraxis_phantommob` / `_cast_r_morthraxis_baleful` |
| `morvaenthir` | 20 | 2650 | `_cast_q_morvaenthir_soulfragment` / `_cast_w_morvaenthir_spiritbind` / `_cast_e_morvaenthir_essence` / `_cast_r_morvaenthir_shadowrealm` |
| `thornvaegrim` | 20 | 2700 | `_cast_q_thornvaegrim_bramble` / `_cast_w_thornvaegrim_twistedadvance` / `_cast_e_thornvaegrim_saplingthrow` / `_cast_r_thornvaegrim_grasp` |