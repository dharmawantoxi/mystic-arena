# Migrasi folder `levels/` (Pygame → Godot)

Folder `levels/` adalah folder terkecil di sisi Pygame dan yang paling lebar
dampaknya: **2 modul, 2.354 baris**, tetapi isinya 54 kamus level yang
menentukan scaling musuh, ekonomi pembuka, tier kastil, tema peta, susunan bos,
meta gold, dan rantai unlock.

Kesimpulan audit: **seluruh isi folder sudah diport** — datanya identik kata per
kata di `data/levels/level_1..54.json`, empat helper-nya punya padanan, dan
setiap kunci yang dibaca runtime sudah punya konsumen native. Yang belum adalah
**layar pemilih level** (state `LEVEL_SELECT` di `_core.py`), yang bukan isi
folder ini melainkan lapisan UI.

## 1. Ringkasan status

| Lapisan | Sumber Pygame | Padanan Godot | Status |
|---|---|---|---|
| 54 kamus level | `level_data.py` (`LEVEL_1` … `LEVEL_54`) | `data/levels/level_1..54.json` (JSON identik, 17 kunci/level) | Diport |
| Registry | `ALL_LEVELS` | `LevelCatalog.all_configs()` + `COUNT`/`count()` | Diport |
| Pencarian level | `get_level_config` | `LevelCatalog.get_level_config` | Diport |
| Jumlah level | `get_level_count` | `LevelCatalog.count()` | Diport |
| Gerbang unlock | `is_level_unlocked` | `LevelCatalog.is_level_unlocked` | Diport |
| Level berikutnya | `get_next_level` | `LevelCatalog.get_next_level` | Diport (sentinel −1) |
| Re-export | `__init__.py` (5 nama) | tidak perlu (`preload` eksplisit) | Tidak portabel |
| Konsumen pertandingan | `_core.py` (`Game`) | `prototype_battle.gd`, `prototype_session.gd`, `level_progress.gd`, `level_intro_screen.gd` | Diport |
| Bake statistik bos | `bosses/boss_data.py` memakai kunci wave | `data/bosses/boss_stats.json` (sudah dipanggang) | Diport (input-only) |
| Layar pemilih level | `_draw_level_select` (`LEVEL_SELECT`) | **belum ada** | BELUM |

Angka kunci: 54 level, 17 kunci per level, 54 tema peta (satu per level), 54
multiplier HP berbeda (1,0–1,54), ekonomi datar 1.000 gold / 3.000 / 1.500 / 0,
3 mini bos per level, dan **216 referensi bos = seluruh roster 216 bos, masing-
masing dipakai tepat sekali** (54 bos sejati + 162 mini bos, tanpa tumpang
tindih).

## 2. Inventaris per berkas (2 modul)

| Modul | Baris | Status | Bukti / catatan |
|---|---|---|---|
| `level_data.py` | 2.347 | Diport | 54 kamus `LEVEL_N` + `ALL_LEVELS` + 4 helper; seluruh nilai identik di `data/levels/*.json` |
| `__init__.py` | 7 | Tidak portabel | Hanya `from levels.level_data import (ALL_LEVELS, get_level_config, get_level_count, is_level_unlocked, get_next_level)`; di Godot pemanggil memakai `LevelCatalog` langsung |

## 3. Tujuh belas kunci level dan konsumennya

Setiap level membawa **seluruh 17 kunci** (tidak ada level yang bolong). Kolom
"konsumen native" adalah hasil pemindaian `godot_rebuild/scripts/**/*.gd` pada
saat validasi, jadi tabel ini tidak bisa basi tanpa validator gagal.

| Kunci | Arti | Dibaca sumber | Konsumen native | Status |
|---|---|---|---|---|
| `bgm_track` | musik pertarungan — tidak dibaca runtime | — | — | BELUM (data-only, mati di sumber) |
| `castle_start_level` | tier kastil merah awal (hard saja) | `_core.py` | `prototype_battle.gd` | Diport |
| `description` | teks intro level | `_core.py`, `_entity.py`, `_render.py` (+2) | `achievement_popup.gd`, `item_forge_panel.gd`, `level_intro_screen.gd` | Diport |
| `enemy_damage_mult` | skala damage musuh (hard: ×1.10) | `_core.py`, `_render.py` | `prototype_battle.gd`, `level_intro_screen.gd` | Diport |
| `enemy_hp_mult` | skala HP musuh (hard: ×1.15) | `_core.py`, `_render.py`, `_bundle.py` | `prototype_battle.gd`, `level_intro_screen.gd` | Diport |
| `enemy_speed_mult` | skala kecepatan musuh (tanpa bonus) | `_core.py` | `prototype_battle.gd` | Diport |
| `level_number` | identitas entri; dipakai katalog & intro | `_core.py`, `_entity.py`, `_render.py` (+2) | `level_catalog.gd`, `level_intro_screen.gd` | Diport |
| `map_theme` | tema peta (54 tema, 1 per level) | `_core.py`, `_render.py` | `prototype_battle.gd`, `level_intro_layout.gd`, `level_intro_screen.gd` (+1) | Diport |
| `meta_gold_reward_lose` | meta gold saat kalah — selalu 0, tak dibaca | — | — | BELUM (data-only, mati di sumber) |
| `meta_gold_reward_replay` | meta gold replay (sekali) | `_core.py` | `level_progress.gd` | Diport |
| `meta_gold_reward_win` | meta gold saat menang | `_core.py`, `_render.py` | `level_progress.gd`, `level_intro_screen.gd` | Diport |
| `mini_bosses` | 3 mini bos per level; urutan nilai = urutan spawn | `_core.py`, `_entity.py`, `boss_data.py` (+1) | `prototype_battle.gd` | Diport |
| `name` | judul level di intro/papan skor | `_core.py`, `_entity.py`, `_render.py` (+8) | `boss_state.gd`, `hero_item_inventory.gd`, `item_shop_ui.gd` (+16) | Diport |
| `starting_castle_level` | tier kastil biru awal | `_core.py` | `prototype_battle.gd` | Diport |
| `starting_gold` | gold pembuka pemain | `_core.py`, `_render.py` | `prototype_battle.gd`, `level_intro_screen.gd` | Diport |
| `true_boss` | bos sejati level | `_core.py`, `_entity.py`, `_render.py` (+3) | `prototype_battle.gd`, `level_intro_screen.gd` | Diport |
| `unlock_after_level` | syarat unlock (level sebelumnya) | `_core.py` | `level_catalog.gd` | Diport |

Catatan: `bgm_track` dan `meta_gold_reward_lose` **tidak dibaca siapa pun** di
runtime Pygame (hanya ada di `levels/`), dan di Godot juga tidak. Keduanya tetap
disimpan apa adanya karena itu isi sumber, dan suite mengunci nilainya
(`bgm_battle.wav` dan `0` untuk ke-54 level).

## 4. Empat helper sumber dan padanannya

| Helper sumber | Semantik yang dibaca oracle | Padanan Godot | Status |
|---|---|---|---|
| `get_level_config(n)` | iterasi `ALL_LEVELS`, cocokkan `level_number`, `return None` bila tidak ada | `LevelCatalog.get_level_config(n)` → `{}` bila tidak ada | Diport (sentinel beda) |
| `get_level_count()` | `len(ALL_LEVELS)` | `LevelCatalog.count()` → `COUNT` = 54 | Diport |
| `is_level_unlocked(n, done)` | config tak ada → `False`; `unlock_after_level is None` → `True`; selain itu `required in done` | sama, dengan `completed.has(required)` | Diport |
| `get_next_level(n)` | `n+1 > count` atau config tak ada → `None` | `n+1` bila ada, selain itu `-1` | Diport (sentinel beda) |
| `ALL_LEVELS` | daftar 54 kamus, urut 1..54 | `LevelCatalog.all_configs()` | Diport |

## 5. Tabel 54 level

Kolom multiplier = `enemy_hp_mult` / `enemy_damage_mult` / `enemy_speed_mult`.

| # | Nama | Tema | HP/DMG/SPD | Bos sejati | Mini bos (urutan sumber) | Unlock |
|---|---|---|---|---|---|---|
| 1 | The Fallen Realm | `forest` | 1/1/1 | `abaddon` | gornak, morgath, drakar | — |
| 2 | Wraith Wastes | `desert` | 1.02/1.02/1.02 | `alchemist` | razak, khalros, gorath | 1 |
| 3 | Infernal Depths | `ice` | 1.03/1.03/1.03 | `ancient_apparition` | xerathis, nyzrak, varkul | 2 |
| 4 | Molten Sanctum | `volcanic` | 1.04/1.04/1.04 | `ignis_drachorn` | zharok, pyrenth, vokrahn | 3 |
| 5 | The Haunted Veil | `haunted` | 1.05/1.05/1.05 | `krobellus` | nyxara, gravefang, vhalzun | 4 |
| 6 | Admiral's Cove | `ocean` | 1.06/1.06/1.06 | `kunkka` | gravewake, syrentha, thalgryn | 5 |
| 7 | Shadow Abyss | `abyss` | 1.07/1.07/1.07 | `nyxarath` | malzareth, akashari, vorenmarr | 6 |
| 8 | Nethervenom Expanse | `nethervenom` | 1.08/1.08/1.08 | `vhorethzir` | xirthalis, vhyssarion, vaerith | 7 |
| 9 | Soulforged Expanse | `soulforged` | 1.09/1.09/1.09 | `naraka` | kenshiro, khazan, wiro | 8 |
| 10 | Radiant Expanse | `radiant` | 1.1/1.1/1.1 | `aurethzar` | krognarr, raz, vraskhan | 9 |
| 11 | Abyssal Depths | `abyssal` | 1.11/1.11/1.11 | `thalakryon` | aeralith, aurex, nyxareva | 10 |
| 12 | Eldritch Depths | `eldritch` | 1.12/1.12/1.12 | `nazulmor` | aurelix, aurelyssa, vargrath | 11 |
| 13 | Silver Sanctum | `sanctum` | 1.13/1.13/1.13 | `solvarin` | kaeldris, pyraklos, velmyrth | 12 |
| 14 | Eternal Flame | `eternalflame` | 1.14/1.14/1.14 | `pyraethis` | azureth, luminar, solara | 13 |
| 15 | Primordial Grove | `primordial` | 1.15/1.15/1.15 | `yamako` | auroth, morvein, thorvak | 14 |
| 16 | Celestial Peaks | `celestialpeaks` | 1.16/1.16/1.16 | `seiryukong` | ignirus, leoric, shirotaka | 15 |
| 17 | Cosmic Expanse | `cosmic` | 1.17/1.17/1.17 | `nyxareth` | kaelthorn, solvanth, xyrael | 16 |
| 18 | Royal Citadel | `royal` | 1.18/1.18/1.18 | `aurelion` | cryssalia, kaelthar, morkhaera | 17 |
| 19 | Violet Court | `violet` | 1.19/1.19/1.19 | `vaelindra` | akahime, nyxthrael, sylvantheros | 18 |
| 20 | Crimson Dominion | `crimson` | 1.2/1.2/1.2 | `morthraxis` | astraelion, morvaenthir, thornvaegrim | 19 |
| 21 | The Hollow Veil | `spectral` | 1.21/1.21/1.21 | `nexthyrius` | kurogari, morvekhar, vorgath | 20 |
| 22 | The Sundered Peak | `sundered` | 1.22/1.22/1.22 | `molgravar` | grimstalker, kryvoxar, vargroth | 21 |
| 23 | The Empyrean Executioner | `empyrean` | 1.23/1.23/1.23 | `seraphienne` | drav, lyrienne, valthar | 22 |
| 24 | The Sunborn Herald | `solaris` | 1.24/1.24/1.24 | `solareth` | khalzaredh, nyxaroth, veshtrax | 23 |
| 25 | The Deepborn Oracle | `abysstide` | 1.25/1.25/1.25 | `okeanora` | grimjack, morvaeth, vulkareth | 24 |
| 26 | The Crimson Matriarch | `crimsonmatriarch` | 1.26/1.26/1.26 | `vaelmyrra` | aelyrion, kaervosth, morvyssk | 25 |
| 27 | The Astral Sovereign | `astral` | 1.27/1.27/1.27 | `zarethyr` | kyumirra, morvakhul, nyxariel | 26 |
| 28 | The Forsaken Empress | `shadowchain` | 1.28/1.28/1.28 | `nyrethzalv` | morthyrax, sanguiveth, xerakhotep | 27 |
| 29 | The Frost-Veiled Huntress | `frostveil` | 1.29/1.29/1.29 | `nyrellieth` | ignakhor, kazureth, sethrakhar | 28 |
| 30 | The Shadow of War | `warshade` | 1.3/1.3/1.3 | `nyxharr` | kaelvyrn, thorvin, xaerissa | 29 |
| 31 | The Outlaw King | `outlaw` | 1.31/1.31/1.31 | `ravokkar` | celwynn, rynvara, syrindra | 30 |
| 32 | The Hexbound Sovereign | `hexbound` | 1.32/1.32/1.32 | `malzeroth` | ghrakmaal, selunara, vessyra | 31 |
| 33 | The Voidbound Sovereign | `voidbound` | 1.33/1.33/1.33 | `zharakzuul` | rakzhan, sirakzan, valekris | 32 |
| 34 | The Earthborn | `earthborn` | 1.34/1.34/1.34 | `grondmauris` | infrakzaar, xarnathul, zhyrakaan | 33 |
| 35 | The Heartbane | `heartbane` | 1.35/1.35/1.35 | `lyssarethys` | kaerissa, thorgaruk, zorathiel | 34 |
| 36 | The Sunfist | `sunfist` | 1.36/1.36/1.36 | `kaerinya` | nyxallaria, vhaerinth, xharokh | 35 |
| 37 | The Void Sovereign | `voidwing` | 1.37/1.37/1.37 | `xelnarath` | kazreth, varkuthar, zhyvrek | 36 |
| 38 | The Crimson Devourer | `crimsondevourer` | 1.38/1.38/1.38 | `kyrenzai` | azkharion, thargoroth, zahkareth | 37 |
| 39 | The Elemental Weaver | `elementweave` | 1.39/1.39/1.39 | `xaelmoran` | bhorgathul, morkhelvis, vorthakul | 38 |
| 40 | The Tempest Weaver | `tempest` | 1.4/1.4/1.4 | `thalryndel` | urgharun, yhoranth, zulkhaven | 39 |
| 41 | The Sawmill Warlord | `sawmill` | 1.41/1.41/1.41 | `grimkor` | emberwick, grondarthul, xareth | 40 |
| 42 | The Crow-Eyed | `croweye` | 1.42/1.42/1.42 | `kaineroth` | kaedrin, morvaeth2, vardrok | 41 |
| 43 | The Stormherald | `crystalstorm` | 1.43/1.43/1.43 | `zyvareth` | nixweaver, nyxraal, xarnthuul | 42 |
| 44 | The Eternal Warlord | `eternalwarlord` | 1.44/1.44/1.44 | `kagetsuka` | lyrenya, vyraeth, zorothrax | 43 |
| 45 | The Explosive Artist | `explosiveart` | 1.45/1.45/1.45 | `deidara` | akiraze, brumhar, zorashi | 44 |
| 46 | The Sand Shadow | `sandshadow` | 1.46/1.46/1.46 | `sunakage` | akaroth, kassadin, shimorakh | 45 |
| 47 | The Emberweaver | `emberweaver` | 1.47/1.47/1.47 | `pyraena` | kaizoku_raijin, korokai, verdanix | 46 |
| 48 | The Skyfury | `skyfury` | 1.48/1.48/1.48 | `cogsworth` | broggmar, ursath, zhaeris | 47 |
| 49 | The Moonreaper | `moonreaper` | 1.49/1.49/1.49 | `yomigetsu` | kairenji, karzhul, xerakkuth | 48 |
| 50 | The Moonfang Prince | `moonfang` | 1.5/1.5/1.5 | `akirakumo` | kaelthys, kaoruken, vaelkorr | 49 |
| 51 | The Emberlion Ronin | `emberlion` | 1.51/1.51/1.51 | `kaithros` | aurelian, morvath, pyrhaan | 50 |
| 52 | The Lunar Herald | `lunarherald` | 1.52/1.52/1.52 | `nyxaris` | garumenshi, thoraz, vhaerith | 51 |
| 53 | The Moon-Born Sovereign | `moonborn` | 1.53/1.53/1.53 | `tsukiyora` | dorakai, hitokage, kazuren | 52 |
| 54 | The Substitute Shinigami | `hollowbane` | 1.54/1.54/1.54 | `hollowbane` | obanai, sanguire, sasori | 53 |

## 6. Temuan audit

1. **Kunci wave `mini_bosses` mati di runtime.** `_roll_mini_boss_schedule`
   mengganti wave-nya: easy menyampel 20–40, normal/hard 11–30 (lihat
   `_core.py: roll_mini_boss_schedule`), lalu `zip` ke nilai kamus. Jadi `10/15/17/18/20/25`
   hanya penting sebagai **input bake**: `bosses/boss_data.py` memakai
   `_slot_of_mini_wave(wave)` untuk kurva statistik monoton. Yang bertahan ke
   runtime hanyalah **urutan nilai** (urutan bos). Godot meniru keduanya:
   `_mini_boss_entries()` membaca urutan kamus, `_roll_mini_boss_schedule()`
   menyampel ulang wave 11–30.
2. **Roster bos terpakai habis.** 54 bos sejati + 162 mini bos = 216, persis
   roster `boss_stats.json`, tanpa id yang muncul di dua peran. Suite memeriksa
   tiap id ada di `boss_stats.json` **dan** di atlas hero.
3. **Tema peta lengkap.** 54 level memakai 54 nama tema berbeda, dan semuanya
   ada di `data/levels/theme_palette.json` (54 entri palet) — suite memeriksa
   setiap `map_theme` punya palet native.
4. **Skala kesulitan berlapis.** Nilai level bukan angka final: mode hard
   mengalikan `enemy_hp_mult × 1.15`, `enemy_damage_mult × 1.10`, dan membiarkan
   `enemy_speed_mult` apa adanya (`_core.py:1477-1479`). Godot menulis ulang
   rumus yang sama di `_apply_difficulty()`, dan suite membandingkannya dengan
   data level.
5. **Ekonomi pembuka datar, kurva tetap ada.** Semua level mulai dari 1.000
   gold dan kastil tier 1, tetapi gold pembuka akhir per difficulty/level tetap
   dihitung (`compute_starting_gold`); fixture `level_economy_source.json`
   (162 baris = 54 level × 3 difficulty) mengunci hasilnya.
6. **Rantai unlock sederhana dan seragam**: level 1 `null` (selalu terbuka),
   level n>1 butuh `n-1`.

## 7. Tes dan oracle

| Artefak | Isi |
|---|---|
| `tests/levels_folder_source_oracle.py` | Parser `ast` untuk 2 modul: 54 kamus, `ALL_LEVELS`, 17 kunci, agregat, semantik 4 helper, pembaca runtime per kunci |
| `tests/fixtures/levels_folder_source.json` | 43 KB: seluruh 54 kamus verbatim + agregat + helper + peta pembaca |
| `tests/levels_folder_checks.gd` | Suite native: inventaris, 54 × (deep-equal + 17 kunci + `level_number`), agregat, helper, integritas bos/tema, kunci mati, dan wiring pertandingan (×1.15/×1.10, urutan mini bos, gold pembuka) |
| `tests/level_catalog_source_oracle.py` (lama) | Sudah menjaga 54 JSON = sumber + id bos ada |
| `tests/level_catalog_checks.gd` (lama) | Loader, gerbang unlock, batas level berikutnya, ekonomi 162 baris |
| `tests/validate_project.py` blok `9ca` | Oracle-vs-folder, kewajiban suite, `count()`/`all_configs()`, audit konsumen live, dan laporan ini |

Cara menjalankan:

```
python godot_rebuild/tests/levels_folder_source_oracle.py            # verifikasi
python godot_rebuild/tests/levels_folder_source_oracle.py --write    # tulis fixture
python godot_rebuild/tests/levels_folder_source_oracle.py --readers  # audit konsumen
godot --headless --path godot_rebuild -s tests/run_all.gd            # suite native
python godot_rebuild/tests/validate_project.py                       # statis
```

## 8. DEVIASI yang tercatat

| # | Perilaku | Sumber | Godot | Alasan / risiko |
|---|---|---|---|---|
| 1 | Level tidak ditemukan | `None` | `{}` (Dictionary kosong) | Pemanggil GDScript tidak perlu memeriksa `Variant`; semua jalur memakai `.is_empty()` |
| 2 | Tidak ada level berikutnya | `None` | `-1` | Sama: tipe balik `int` selalu aman |
| 3 | Identitas objek config | kamus modul yang sama dipakai ulang (mutable) | tiap panggilan membaca ulang JSON → objek baru | Mencegah pemanggil merusak katalog; suite membuktikan mutasi hasil tidak bocor. Konsekuensi: `all_configs()` membaca 54 berkas per panggilan (jangan dipanggil per frame) |
| 4 | Tipe daftar completed | `list` bebas | `Array` (bukan `Array[int]`) | Supaya pemanggil bisa memberi `Array[int]` maupun `Array` hasil parse save |
| 5 | `COUNT` | `len(ALL_LEVELS)` saat impor | konstanta 54 | Nilai sumber memang 54; validator memastikan 54 JSON ada dan cocok |
| 6 | Layar pemilih level | `_draw_level_select` + state `LEVEL_SELECT` | belum ada | Dicatat sebagai BELUM, bukan dianggap selesai |

## 9. Status kejujuran

- Yang benar-benar dibuktikan lapisan ini: **data** 54 level identik, **semantik
  empat helper**, **integritas rujukan** (216 bos, 54 tema), **kunci mati**
  terklasifikasi, dan **wiring** ke pertandingan (skala hard, urutan mini bos,
  gold pembuka). Bukan: tampilan layar pemilih level.
- BELUM: layar pemilih level gaya `_draw_level_select` (grid 54 kartu, status
  kunci, pratinjau bos, difficulty hint). Semua **data** yang dibutuhkannya
  sudah tersedia dan beruji (`all_configs()`, `is_level_unlocked`,
  `get_next_level`, `meta_gold_reward_win`, `map_theme`, `true_boss`).
- Belum ada bukti visual/perangkat: tidak ada screenshot Godot, replay input,
  atau uji Android untuk lapisan ini.
