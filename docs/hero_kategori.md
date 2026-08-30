# Kategori Hero Mystic Arena — PHYSICAL / MAGIC / TANK

Dibuat otomatis oleh `tools/analyze_hero_archetypes.py` dari data hero di repo (tidak ada angka karangan).

> **Sumber angka:** tabel di bawah dihitung dari DATA MENTAH (`bosses/boss_data.py`). Angka yang DIPAKAI GAME sudah lewat balance pass (`hero_balance.py`, lihat bagian "Balance pass 2026-08-30" di bawah dan `docs/balance_audit.md`) - jadi jangan pakai kolom tier/POWER ini untuk menilai kekuatan hero di dalam game.

> `Tier DPS` = DPS total hero dibanding median sesama kelas boss-nya (S >= 1.45x, A >= 1.20x, B >= 0.90x, C >= 0.65x, D < 0.65x). `POWER` = skor absolut 82% DPS + 18% EHP terhadap p98 pool (starter & hero murah otomatis kecil). `Burst` = porsi DPS yang datang dari skill - makin besar, makin sering kepotong cap anti-burst boss.

## Ringkasan

| Kelas boss | PHYSICAL | MAGIC | TANK | Total |
|---|---|---|---|---|
| Starter | 4 | 2 | 0 | 6 |
| MINI BOSS | 54 | 68 | 40 | 162 |
| TRUE BOSS | 5 | 25 | 24 | 54 |
| **TOTAL** | 63 | 95 | 64 | 222 |

## Cara baca 1 kata (yang ditanya)

- **PHYSICAL** — damage utamanya datang dari *basic attack* (bagian skill < 45% dari total DPS). Biasanya melee (range di-clamp ke 70) atau marksman.
- **MAGIC** — damage utamanya *spell burst* (bagian skill >= 45% dari total DPS) dan/atau kit bertema arcane/elemental (fire, ice, void, necro, storm, dll.).
- **TANK** — bukan tipe damage, tapi gaya main: Effective HP (HP sudah termasuk bonus melee +15% dari BALANCE PASS di _entity.py dan multiplier garis depan 1.25x) ada di persentil >= 72 dengan ketergantungan burst <= 60%. Kategori ini menyerap tipe aslinya — kolom `Tipe dmg` tetap menyimpan PHYSICAL/MAGIC-nya.

## Temuan penting (hasil ukur dari data)

1. **Dulu engine tidak membedakan PHYSICAL vs MAGIC.** Boss hanya punya pengurangan flat — TRUE boss `damage_reduction` 0.30, MINI 0.20 (`bosses/base_boss.py:382`) dan dipakai untuk semua `take_damage`. Tidak ada armor vs magic resist. Yang benar-benar punya interaksi adalah 3 hal: `damage_type='fire'` kebal armor-shred item (`base_boss.py:5142`, `_entity.py:5477`), `damage_type='projectile'` bisa dibanjiri Wind Wall Kaizen (`_entity.py:4301`), dan Mage Tower memangkas skill damage lewat `skill_down_amount` (`_entity.py:3151`).
2. **ANTI-BURST CAP mengubah arti kategori.** TRUE boss memotong satu pukulan maksimal 8% HP (`max_damage_per_hit`, `base_boss.py:386`), MINI 12%. Jadi 21 hero dengan burst ratio >= 50% (skill = sebagian besar DPS-nya) paling banyak kerugiannya vs TRUE boss; 13 hero burst <= 25% (mesin multi-hit) justru paling efisien.
3. **Korelasi HP vs DPS = 0.93 (data mentah, SEBELUM balance pass).** Setelah `_normalize_hero_unlock_stats()` (monotonic running-max per stat), hero mahal hampir selalu menang di DUA stat sekaligus - tidak ada trade-off archetype. Efeknya: kategori TANK berisi hero top-tier (median EHP 2810 vs DPS median 642 adalah pool yang sama), bukan hero murah yang kuat di badan.
4. **152 dari 216 hero boss tidak punya skill sendiri.** `_SKILL_REGISTRY` di `hero_skills/_bundle.py:458` hanya berisi 64 entri; sisanya masuk `_fallback_cast` (damage generik, Q 1.0x / W 1.2x / E 1.5x / R 2.5x). Artinya label MAGIC untuk hero-hero itu masih cosmetic: di lapangan skill mereka hanya angka.

## Implementasi v1 (AKTIF di engine)

Kategori tidak lagi jadi dokumen mati - datanya dipakai runtime:

| Berkas | Peran |
|---|---|
| `hero_archetypes.py` | tabel `hero_type -> {dmg_type, playstyle, tier, power}`; file ini yang dibaca engine. Regenerate lewat tool ini |
| `hero_archetypes.json` | versi data mentah (untuk tools/UI eksternal) |
| `_entity.py` | `Hero.dmg_school`, `resolve_damage_school()`, `Bullet` & proyektil hero membawa `school`, mitigasi di `Tower`/`Minion` |
| `bosses/base_boss.py` | `armor` (12 mini / 18 true) & `magic_resist` (0.10 / 0.20) + penerapannya di `Boss.take_damage` |
| `_core.py` | chip PHY/MAG/TNK di kartu Hero Shop + legenda di header tab |
| `tools/test_damage_school.py` | 36 assert: mitigasi per sekolah, paritas Wind Wall/Windrun/fire, fallback arketype |

Rumus mitigasi (semua di atas `damage_reduction` bawaan, di bawah anti-burst cap):

```
physical: dmg * (1 - armor*0.06/(1 + armor*0.06))   # 12 armor = -42%, 18 = -52%
magic   : dmg * (1 - magic_resist)                  # 10% / 20%
```

Override: tambah kunci `dmg_type` (`PHYSICAL` / `MAGIC`) di `hero_unlock` boss di `bosses/boss_data.py` - menang atas tabel. Override ketahanan boss: kunci `armor` / `magic_resist` di entri boss (golem armor tinggi, mage boss MR tinggi).

Test regresi: `python3 tools/test_damage_school.py` (36 assert) dan `python3 tools/test_damage_school_integration.py` (400 frame Game sungguhan: 2 hero + mini boss).

TODO v2 (sengaja belum dikerjakan):

1. 152 hero boss belum punya recipe skill khusus - sekolah damage baru terasa di basic attack, belum di skill uniknya.
2. Basic attack boss diberi `school=physical` supaya item armor berguna; ability boss masih `None` (perilaku lama).
3. Peluru Mage Tower sengaja masih dihitung FISIK (paritas lama) supaya item armor tidak kehilangan nilai sekaligus.
4. Skill bertema api (Dragon Breath, Flux, dll.) belum di-flag `fire`, jadi belum kebal armor-shred.
5. **Nama hero tabrakan:** `Morvaeth`. Kalau dipakai di UI/ledger, pakailah `hero_type` (key), bukan `name`.

## Rekomendasi per lawanan

| Situasi | Pilihan terbaik | Kenapa (dari data) |
|---|---|---|
| **MINI boss** — cap 12% HP/pukul | Hitokage·TAN, Kazuren·TAN, Kairenji·TAN, Obanai·TAN, Zhaeris·TAN, Kaelthys·TAN | DPS multi-hit, burst rendah: jarang kepotong cap |
| MINI boss — hero burst tinggi (paling terbuang) | Nyxaroth·MAG, Kryvoxar·MAG, Lyrienne·MAG, Thornvaegrim·MAG, Morvaenthir·MAG, Sylvantheros·MAG | lebih dari separuh DPS-nya di-cap, hindari kalau butuh kill cepat |
| **TRUE boss** — cap 8% HP/pukul | Kurosaki Hollowbane·TAN, Kaithros·TAN, Akirakumo·TAN, Yomigetsu·TAN, Kagetsuka·TAN, Zyvareth·TAN | DPS multi-hit, burst rendah: jarang kepotong cap |
| TRUE boss — hero burst tinggi (paling terbuang) | Nyreth'zalvarin·MAG, Zarethyr·MAG, Okeanora·MAG, Nexthyrius·MAG, Molgravar·MAG, Vaelindra·MAG | lebih dari separuh DPS-nya di-cap, hindari kalau butuh kill cepat |
| Dinding untuk menahan aggro | Kurosaki Hollowbane, Kaithros, Akirakumo, Yomigetsu, Tsukiyora, Nyxaris | EHP tertinggi; melee TANK sudah dapat bonus runtime +15% HP, +20% dmg, +18% speed |
| Damage murah per HP (EHP < median) | Veshtrax, Morthyrax, Vorgath, Drav, Valthar, Velmyrth | DPS tinggi dengan badan tipis - rawan, butuh tower di belakangnya |


## Starter Hero

### PHYSICAL (4)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Thorne** | starter | PHYSICAL | PHYSICAL | FIGHTER | B | 11 | 1610 | 38.4 | 65.5 | 14.0 | 18% | ya | Viscous Nose |
| 2 | **Kaizen** | starter | PHYSICAL | PHYSICAL | FIGHTER | A | 9 | 632 | 42.0 | 89.5 | 14.0 | 14% | ya | Wind Slash |
| 3 | **Grimjaw** | starter | PHYSICAL | PHYSICAL | FIGHTER | B | 8 | 920 | 39.6 | 75.0 | 3.7 | 5% | ya | Blade Fury |
| 4 | **Sylara** | starter | PHYSICAL | PHYSICAL | FIGHTER | B | 6 | 470 | 45.0 | 51.9 | 15.8 | 23% | tidak | Focus Fire |

### MAGIC (2)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Vex** | starter | MAGIC | MAGIC | FIGHTER | C | 6 | 520 | 34.0 | 44.3 | 17.3 | 28% | tidak | Arcane Orb |
| 2 | **Zephyr** | starter | MAGIC | MAGIC | FIGHTER | B | 6 | 520 | 27.0 | 54.0 | 14.0 | 21% | tidak | Bramble Maze |

## MINI BOSS

### PHYSICAL (54)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Sirakzan** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | A | 69 | 2818 | 342.0 | 613.6 | 279.8 | 31% | ya | Blade Roll |
| 2 | **Rynvara** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | A | 65 | 2875 | 324.0 | 552.3 | 279.1 | 34% | ya | Primal Rend |
| 3 | **Nixweaver** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | A | 62 | 3150 | 340.0 | 510.0 | 266.2 | 34% | tidak | Trick Bolt |
| 4 | **Kaedrin** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | A | 61 | 3150 | 335.0 | 502.5 | 265.4 | 35% | tidak | Moon Slash |
| 5 | **Ignakhor** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | B | 60 | 2760 | 300.0 | 487.0 | 272.9 | 36% | ya | Furnace Cleave |
| 6 | **Morvaeth** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | B | 60 | 3200 | 340.0 | 485.7 | 264.5 | 35% | tidak | Mirror Slash |
| 7 | **Kazreth** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | B | 58 | 2750 | 305.0 | 457.5 | 277.6 | 38% | tidak | Blood Cleave |
| 8 | **Zahkareth** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | B | 58 | 2900 | 320.0 | 457.1 | 272.5 | 37% | tidak | Tyrant's Smash |
| 9 | **Morvaeth** ◦ | mini | PHYSICAL | PHYSICAL | CARRY | B | 57 | 2415 | 276.0 | 470.5 | 260.4 | 36% | ya | Crimson Slash |
| 10 | **Zul'khaven** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 57 | 3150 | 335.0 | 437.0 | 265.5 | 38% | tidak | Devour Bite |
| 11 | **Khal'zaredh** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 56 | 2415 | 264.0 | 450.0 | 263.2 | 37% | ya | Sand Slash |
| 12 | **Aelyrion** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 56 | 2472 | 276.0 | 448.1 | 263.1 | 37% | ya | Divine Lance |
| 13 | **Grondarthul** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 56 | 3200 | 335.0 | 418.8 | 267.1 | 39% | tidak | Troll Smash |
| 14 | **Vargroth** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 55 | 2300 | 237.6 | 450.0 | 255.2 | 36% | ya | Blood Rend |
| 15 | **Bhor'gathul** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 55 | 3000 | 320.0 | 417.4 | 270.1 | 39% | tidak | Earth Rend |
| 16 | **Mor'khelvis** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 54 | 3050 | 315.0 | 393.8 | 269.1 | 41% | tidak | Stone Rend |
| 17 | **Thargoroth** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 53 | 3100 | 315.0 | 378.0 | 273.6 | 42% | tidak | Primordial Slam |
| 18 | **Kurogari** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 52 | 2185 | 222.0 | 420.5 | 252.7 | 38% | ya | Soul Reap |
| 19 | **Selunara** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 51 | 2450 | 270.0 | 368.2 | 279.2 | 43% | tidak | Moon Arrow |
| 20 | **Kaelvyrn** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 50 | 2450 | 255.0 | 382.5 | 272.5 | 42% | tidak | Gilded Slash |
| 21 | **Ghrakmaal** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 50 | 2700 | 275.0 | 343.8 | 280.6 | 45% | tidak | Earth Shatter |
| 22 | **Kaelthar** | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 48 | 1955 | 223.2 | 380.5 | 241.2 | 39% | ya | Charging Fist |
| 23 | **Morvekhar** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 48 | 2645 | 240.0 | 340.9 | 249.9 | 42% | ya | Soul Cleave |
| 24 | **Sanguiveth** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 48 | 2350 | 250.0 | 357.1 | 271.8 | 43% | tidak | Blood Harvest |
| 25 | **Veshtrax** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 47 | 2150 | 225.0 | 355.3 | 257.7 | 42% | tidak | Sapphire Lunge |
| 26 | **Morvakhul** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | B | 45 | 2350 | 240.0 | 313.0 | 270.8 | 46% | tidak | Cursed Cleave |
| 27 | **Shirotaka** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 44 | 1897 | 201.6 | 343.6 | 226.6 | 40% | ya | Hiraishin |
| 28 | **Kaelthorn** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 44 | 1955 | 206.4 | 335.1 | 221.7 | 40% | ya | Bravest Fighter |
| 29 | **Vorgath** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 43 | 2000 | 210.0 | 300.0 | 257.2 | 46% | tidak | Demonic Gaze |
| 30 | **Drav** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 42 | 2050 | 215.0 | 293.2 | 259.6 | 47% | tidak | Anchor Slam |
| 31 | **Velmyrth** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 40 | 1311 | 165.6 | 332.1 | 207.2 | 38% | ya | Stifling Dagger |
| 32 | **Morvein** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 40 | 1667 | 189.6 | 307.8 | 213.6 | 41% | ya | Puncture |
| 33 | **Leoric** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 40 | 1840 | 187.2 | 290.1 | 216.6 | 43% | ya | Fearless Charge |
| 34 | **Thorvak** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 38 | 1725 | 180.0 | 278.9 | 208.8 | 43% | ya | Seed |
| 35 | **Vraskhan** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 36 | 1495 | 144.0 | 272.7 | 192.3 | 41% | ya | Thorned Assault |
| 36 | **Vargrath** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 35 | 1380 | 156.0 | 265.9 | 195.9 | 42% | ya | Bloodthirst |
| 37 | **Kaeldris** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 35 | 1380 | 156.0 | 265.9 | 195.9 | 42% | ya | Overwhelming |
| 38 | **Raz** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 34 | 1495 | 136.8 | 245.5 | 188.4 | 43% | ya | Overdrive |
| 39 | **Pyraklos** | mini | PHYSICAL | PHYSICAL | FIGHTER | C | 33 | 1438 | 162.0 | 263.0 | 165.8 | 39% | ya | Spear of Mars |
| 40 | **Khazan** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 32 | 1495 | 138.0 | 224.0 | 176.2 | 44% | ya | Chained Blade |
| 41 | **Wiro** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 32 | 1495 | 129.6 | 232.5 | 178.6 | 43% | ya | Wind Cut |
| 42 | **Kenshiro** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 31 | 1495 | 132.0 | 225.0 | 165.0 | 42% | ya | Swift Slash |
| 43 | **Krognarr** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 31 | 1322 | 141.6 | 219.4 | 173.2 | 44% | ya | Stone Strike |
| 44 | **Vaerith** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 29 | 1322 | 134.4 | 208.3 | 153.7 | 42% | ya | Spawn Spiderlings |
| 45 | **Aeralith** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 27 | 1300 | 115.0 | 156.8 | 188.4 | 55% | tidak | Tailwind |
| 46 | **Pyrenth** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 25 | 1265 | 110.4 | 179.2 | 135.1 | 43% | ya | DOOM |
| 47 | **Vokrahn** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 25 | 1495 | 122.4 | 189.7 | 113.1 | 37% | ya | Chaos Bolt |
| 48 | **Gravefang** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 25 | 1495 | 129.6 | 200.8 | 105.4 | 34% | ya | Boulder Smash |
| 49 | **Gravewake** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 24 | 1380 | 129.6 | 192.1 | 91.4 | 32% | ya | Anchor Smash |
| 50 | **Khalros** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 22 | 1208 | 100.8 | 163.6 | 99.7 | 38% | ya | Wild Axes |
| 51 | **Gorath** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 21 | 1288 | 115.2 | 206.7 | 46.4 | 18% | ya | Bloodrage |
| 52 | **Thalgryn** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 20 | 1300 | 108.0 | 147.3 | 87.5 | 37% | tidak | Waveform |
| 53 | **Drakar** | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 19 | 1265 | 96.0 | 142.3 | 75.7 | 35% | ya | Counter Helix |
| 54 | **Varkul** ◦ | mini | PHYSICAL | PHYSICAL | FIGHTER | D | 19 | 1120 | 96.0 | 137.1 | 96.9 | 41% | tidak | Frost Blast |

### MAGIC (68)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Rakzhan** ◦ | mini | MAGIC | MAGIC | CARRY | A | 67 | 2875 | 336.0 | 572.7 | 281.2 | 33% | ya | Ember Jab |
| 2 | **Kazureth** ◦ | mini | MAGIC | MAGIC | CARRY | A | 61 | 2588 | 294.0 | 501.1 | 276.0 | 36% | ya | Thunderclap Flash |
| 3 | **Vyraeth** ◦ | mini | MAGIC | MAGIC | CARRY | B | 60 | 3150 | 340.0 | 485.7 | 264.4 | 35% | tidak | Haunt Bolt |
| 4 | **Grimjack** ◦ | mini | MAGIC | MAGIC | CARRY | A | 59 | 2358 | 270.0 | 511.4 | 261.8 | 34% | ya | Venom Stab |
| 5 | **Lyrenya** ◦ | mini | MAGIC | MAGIC | CARRY | B | 59 | 3200 | 345.0 | 470.5 | 265.3 | 36% | tidak | Vine Whip |
| 6 | **Zorashi** ◦ | mini | MAGIC | MAGIC | CARRY | B | 59 | 3200 | 345.0 | 470.5 | 264.4 | 36% | tidak | Serpent Fang |
| 7 | **Kaervosth** ◦ | mini | MAGIC | MAGIC | CARRY | B | 58 | 2530 | 282.0 | 480.7 | 266.4 | 36% | ya | Storm Slash |
| 8 | **Nyxariel** ◦ | mini | MAGIC | MAGIC | CARRY | B | 58 | 2415 | 282.0 | 480.7 | 269.4 | 36% | ya | Trident Thrust |
| 9 | **Emberwick** ◦ | mini | MAGIC | MAGIC | CARRY | B | 57 | 3100 | 330.0 | 450.0 | 268.1 | 37% | tidak | Fire Lance |
| 10 | **Yh'oranth** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 56 | 3000 | 320.0 | 436.4 | 266.4 | 38% | tidak | Wraith Bolt |
| 11 | **Xarn'thuul** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 56 | 3100 | 335.0 | 437.0 | 264.5 | 38% | tidak | Void Lance |
| 12 | **Grimstalker** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 55 | 2242 | 252.0 | 452.2 | 255.8 | 36% | ya | Toxic Claw |
| 13 | **Morvyssk** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 54 | 2645 | 270.0 | 418.4 | 265.0 | 39% | ya | Acid Splash |
| 14 | **Vhaerinth** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 54 | 2650 | 295.0 | 402.3 | 277.7 | 41% | tidak | Ink Splash |
| 15 | **Varkuthar** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 54 | 2850 | 310.0 | 404.3 | 276.4 | 41% | tidak | Bloodfire Smash |
| 16 | **Nyxallaria** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 53 | 2700 | 300.0 | 391.3 | 279.0 | 42% | tidak | Abyss Bolt |
| 17 | **Zorathiel** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 52 | 2600 | 290.0 | 378.3 | 279.7 | 42% | tidak | Arcane Bolt |
| 18 | **Xharokh** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 52 | 2750 | 305.0 | 381.2 | 276.6 | 42% | tidak | Void Bind |
| 19 | **Astraelion** | mini | MAGIC | MAGIC | FIGHTER | B | 51 | 2185 | 235.2 | 400.9 | 249.9 | 38% | ya | Swordfall |
| 20 | **Infrakzaar** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 51 | 2550 | 285.0 | 371.7 | 281.7 | 43% | tidak | Ember Lance |
| 21 | **Valekris** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 50 | 2350 | 275.0 | 358.7 | 278.5 | 44% | tidak | Wraith Bolt |
| 22 | **Xarnathul** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 50 | 2500 | 280.0 | 350.0 | 280.4 | 44% | tidak | Death Note |
| 23 | **Xaerissa** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 49 | 2300 | 260.0 | 354.5 | 274.1 | 44% | tidak | Silk Thread |
| 24 | **Celwynn** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 49 | 2350 | 260.0 | 339.1 | 279.4 | 45% | tidak | Star Bolt |
| 25 | **Syrindra** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 48 | 2400 | 265.0 | 331.2 | 277.7 | 46% | tidak | Dark Bolt |
| 26 | **Vessyra** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 48 | 2400 | 265.0 | 331.2 | 277.9 | 46% | tidak | Serpent Bite |
| 27 | **Xy'rael** | mini | MAGIC | MAGIC | FIGHTER | B | 47 | 1897 | 216.0 | 368.2 | 236.6 | 39% | ya | Finch |
| 28 | **Seth'rakhaar** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 47 | 2450 | 255.0 | 332.6 | 274.5 | 45% | tidak | Sunforged Chop |
| 29 | **Akahime** | mini | MAGIC | MAGIC | FIGHTER | B | 46 | 2128 | 225.6 | 349.6 | 236.6 | 40% | ya | Petal Barrage |
| 30 | **Morthyrax** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 46 | 2300 | 245.0 | 334.1 | 268.6 | 45% | tidak | Rot Claw |
| 31 | **Thorvin** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 46 | 2600 | 250.0 | 312.5 | 275.5 | 47% | tidak | Ironbound Slam |
| 32 | **Kyumirra** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 45 | 2050 | 230.0 | 313.6 | 267.6 | 46% | tidak | Charm Orb |
| 33 | **Xerakhotep** ◦ | mini | MAGIC | MAGIC | FIGHTER | B | 45 | 2100 | 240.0 | 313.0 | 270.4 | 46% | tidak | Sun Bolt |
| 34 | **Vulkareth** ◦ | mini | MAGIC | MAGIC | FIGHTER | C | 44 | 2350 | 235.0 | 306.5 | 259.2 | 46% | tidak | Ember Fist |
| 35 | **Kryvoxar** ◦ | mini | MAGIC | MAGIC | FIGHTER | C | 43 | 2300 | 205.0 | 273.3 | 257.9 | 49% | tidak | Crystal Shard |
| 36 | **Lyrienne** ◦ | mini | MAGIC | MAGIC | FIGHTER | C | 43 | 2300 | 210.0 | 273.9 | 256.7 | 48% | tidak | Vesper Bolt |
| 37 | **Nyxaroth** ◦ | mini | MAGIC | MAGIC | FIGHTER | C | 43 | 2300 | 215.0 | 274.5 | 260.3 | 49% | tidak | Star Bolt |
| 38 | **Valthar** ◦ | mini | MAGIC | MAGIC | FIGHTER | C | 42 | 2200 | 220.0 | 287.0 | 254.1 | 47% | tidak | Royal Sunder |
| 39 | **Nyxthrael** | mini | MAGIC | MAGIC | FIGHTER | C | 39 | 1750 | 192.0 | 274.3 | 245.7 | 47% | tidak | Ambush |
| 40 | **Morvaenthir** | mini | MAGIC | MAGIC | FIGHTER | C | 39 | 1850 | 190.0 | 247.8 | 248.6 | 50% | tidak | Soul Fragment |
| 41 | **Thornvaegrim** | mini | MAGIC | MAGIC | FIGHTER | C | 39 | 1950 | 186.0 | 253.6 | 248.6 | 50% | tidak | Bramble |
| 42 | **Solara** | mini | MAGIC | MAGIC | FIGHTER | C | 38 | 1552 | 177.6 | 288.3 | 208.0 | 42% | ya | Starbreaker |
| 43 | **Sylvantheros** | mini | MAGIC | MAGIC | FIGHTER | C | 38 | 1800 | 184.0 | 240.0 | 240.6 | 50% | tidak | Sprout |
| 44 | **Aurelyssa** | mini | MAGIC | MAGIC | FIGHTER | C | 37 | 1495 | 148.8 | 281.8 | 195.3 | 41% | ya | Whirlwind |
| 45 | **Auroth** | mini | MAGIC | MAGIC | FIGHTER | C | 37 | 1610 | 182.4 | 270.4 | 207.5 | 43% | ya | Ionic Edge |
| 46 | **Mor'khaera** | mini | MAGIC | MAGIC | FIGHTER | C | 37 | 1750 | 180.0 | 234.8 | 236.1 | 50% | tidak | Spirit Burst |
| 47 | **Cryssalia** | mini | MAGIC | MAGIC | FIGHTER | C | 36 | 1800 | 178.0 | 232.2 | 231.3 | 50% | tidak | Frostshock |
| 48 | **Nyxareva** | mini | MAGIC | MAGIC | FIGHTER | C | 35 | 1288 | 144.0 | 258.4 | 194.3 | 43% | ya | Dark Slash |
| 49 | **Solvanth** | mini | MAGIC | MAGIC | FIGHTER | C | 35 | 1750 | 166.0 | 226.4 | 221.7 | 50% | tidak | Ring Punishment |
| 50 | **Aurex** | mini | MAGIC | MAGIC | FIGHTER | C | 33 | 1357 | 146.4 | 237.7 | 182.8 | 44% | ya | Shield Crash |
| 51 | **Ignirus** | mini | MAGIC | MAGIC | FIGHTER | C | 33 | 1550 | 162.0 | 211.3 | 214.1 | 50% | tidak | Searing Torrent |
| 52 | **Xir'thalis** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 31 | 1495 | 134.4 | 254.5 | 138.3 | 35% | ya | Time Lapse |
| 53 | **Luminar** | mini | MAGIC | MAGIC | FIGHTER | D | 30 | 1300 | 140.0 | 178.7 | 207.5 | 54% | tidak | Illuminate |
| 54 | **Azureth** | mini | MAGIC | MAGIC | FIGHTER | D | 29 | 1250 | 135.0 | 176.1 | 207.2 | 54% | tidak | Arcane Bolt |
| 55 | **Aurelix** | mini | MAGIC | MAGIC | FIGHTER | D | 25 | 1120 | 118.0 | 168.6 | 154.7 | 48% | tidak | Time Bomb |
| 56 | **Akashari** | mini | MAGIC | MAGIC | FIGHTER | D | 23 | 1300 | 105.0 | 150.0 | 136.3 | 48% | tidak | Shadow Strike |
| 57 | **Vhyssarion** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 22 | 1300 | 100.0 | 136.4 | 128.1 | 48% | tidak | Poison Nova |
| 58 | **Nyxara** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 21 | 1300 | 102.0 | 145.7 | 105.4 | 42% | tidak | Nether Blast |
| 59 | **Malzareth** | mini | MAGIC | MAGIC | FIGHTER | D | 21 | 1300 | 100.0 | 136.4 | 112.5 | 45% | tidak | Disruption |
| 60 | **Vorenmarr** | mini | MAGIC | MAGIC | FIGHTER | D | 21 | 1200 | 112.0 | 146.1 | 110.9 | 43% | tidak | Fatal Bonds |
| 61 | **Razak** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 20 | 1265 | 86.4 | 147.3 | 92.0 | 38% | ya | Sticky Napalm |
| 62 | **Nyzrak** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 20 | 1150 | 92.0 | 138.0 | 101.6 | 42% | tidak | Arctic Burn |
| 63 | **Vhalzun** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 20 | 1300 | 97.0 | 132.3 | 114.1 | 46% | tidak | Death Pulse |
| 64 | **Gornak** | mini | MAGIC | MAGIC | FIGHTER | D | 19 | 920 | 90.0 | 161.5 | 84.3 | 34% | ya | Mana Break |
| 65 | **Syrentha** | mini | MAGIC | MAGIC | FIGHTER | D | 19 | 1300 | 95.0 | 129.5 | 102.1 | 44% | tidak | Riptide |
| 66 | **Zharok** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 18 | 1100 | 78.0 | 117.0 | 104.0 | 47% | tidak | Strafe |
| 67 | **Xerathis** ◦ | mini | MAGIC | MAGIC | FIGHTER | D | 17 | 1120 | 84.0 | 114.5 | 89.0 | 44% | tidak | Crystal Nova |
| 68 | **Morgath** | mini | MAGIC | MAGIC | FIGHTER | D | 14 | 820 | 73.0 | 104.3 | 71.2 | 41% | tidak | Spark Wraith |

### TANK (40)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Hitokage** ◦ | mini | TANK | PHYSICAL | TANK | S | 97 | 4485 | 510.0 | 965.9 | 264.2 | 22% | ya | Sunfire Slash |
| 2 | **Kazuren** ◦ | mini | TANK | MAGIC | TANK | S | 95 | 4370 | 498.0 | 943.2 | 266.6 | 22% | ya | Void Slash |
| 3 | **Obanai** ◦ | mini | TANK | PHYSICAL | TANK | S | 91 | 4485 | 510.0 | 869.3 | 264.5 | 23% | ya | Serpent Fang |
| 4 | **Kairenji** ◦ | mini | TANK | PHYSICAL | TANK | S | 90 | 4025 | 462.0 | 875.0 | 266.8 | 23% | ya | Void Slash |
| 5 | **Zhaeris** ◦ | mini | TANK | PHYSICAL | TANK | S | 88 | 3910 | 450.0 | 852.3 | 266.5 | 24% | ya | Shadow Slash |
| 6 | **Kaelthys** ◦ | mini | TANK | PHYSICAL | TANK | S | 86 | 4140 | 480.0 | 818.2 | 266.3 | 25% | ya | Stillwater Slash |
| 7 | **Aurelian** ◦ | mini | TANK | PHYSICAL | TANK | S | 85 | 4255 | 492.0 | 798.7 | 265.6 | 25% | ya | Golden Spear |
| 8 | **Akiraze** ◦ | mini | TANK | PHYSICAL | TANK | S | 81 | 3737 | 420.0 | 753.6 | 266.0 | 26% | ya | Golden Slash |
| 9 | **Thoraz** ◦ | mini | TANK | PHYSICAL | TANK | S | 80 | 4428 | 504.0 | 715.9 | 264.5 | 27% | ya | Mountain Slam |
| 10 | **Akaroth** ◦ | mini | TANK | PHYSICAL | TANK | S | 79 | 3852 | 426.0 | 726.1 | 266.7 | 27% | ya | Crimson Jab |
| 11 | **Xerakkuth** ◦ | mini | TANK | MAGIC | TANK | S | 78 | 3967 | 450.0 | 697.3 | 267.2 | 28% | ya | Venom Sting |
| 12 | **Ur'gharun** ◦ | mini | TANK | PHYSICAL | TANK | S | 76 | 3507 | 390.0 | 699.8 | 267.3 | 28% | ya | Feral Rend |
| 13 | **Broggmar** ◦ | mini | TANK | PHYSICAL | TANK | A | 75 | 4025 | 438.0 | 649.2 | 268.0 | 29% | ya | Cask Smash |
| 14 | **Kaerissa** ◦ | mini | TANK | PHYSICAL | TANK | S | 74 | 2990 | 354.0 | 670.5 | 282.2 | 30% | ya | Blood Stab |
| 15 | **Kaoruken** ◦ | mini | TANK | PHYSICAL | TANK | S | 74 | 3650 | 405.0 | 675.0 | 265.6 | 28% | tidak | Chakra Palm |
| 16 | **Pyrhaan** ◦ | mini | TANK | MAGIC | TANK | S | 74 | 3650 | 405.0 | 675.0 | 266.3 | 28% | tidak | Cinder Fist |
| 17 | **Zhyvrek** ◦ | mini | TANK | PHYSICAL | TANK | S | 72 | 3105 | 360.0 | 645.9 | 275.3 | 30% | ya | Void Slash |
| 18 | **Brumhar** ◦ | mini | TANK | PHYSICAL | TANK | A | 71 | 3852 | 426.0 | 605.1 | 265.2 | 30% | ya | Glacier Chop |
| 19 | **Vor'thakul** ◦ | mini | TANK | PHYSICAL | TANK | A | 70 | 3392 | 390.0 | 604.3 | 268.2 | 31% | ya | Abyss Bolt |
| 20 | **Xareth** ◦ | mini | TANK | PHYSICAL | TANK | A | 70 | 3507 | 390.0 | 604.3 | 266.3 | 31% | ya | Time Bolt |
| 21 | **Korokai** ◦ | mini | TANK | PHYSICAL | TANK | A | 69 | 3350 | 365.0 | 608.3 | 266.6 | 30% | tidak | Mirror Slash |
| 22 | **Sasori** ◦ | mini | TANK | PHYSICAL | TANK | A | 69 | 3950 | 430.0 | 586.4 | 263.8 | 31% | tidak | Puppet Slash |
| 23 | **Zhyrakaan** ◦ | mini | TANK | PHYSICAL | TANK | A | 68 | 2990 | 348.0 | 593.2 | 279.1 | 32% | ya | Phantom Thrust |
| 24 | **Azkharion** ◦ | mini | TANK | PHYSICAL | TANK | A | 68 | 3277 | 372.0 | 576.4 | 274.6 | 32% | ya | Ashen Cleave |
| 25 | **Karzhul** ◦ | mini | TANK | PHYSICAL | TANK | A | 68 | 3550 | 390.0 | 585.0 | 266.0 | 31% | tidak | Fang Ripper |
| 26 | **Dorakai** ◦ | mini | TANK | MAGIC | TANK | A | 68 | 3850 | 420.0 | 572.7 | 264.8 | 32% | tidak | Drum Wave |
| 27 | **Garumenshi** ◦ | mini | TANK | PHYSICAL | TANK | A | 67 | 3800 | 415.0 | 565.9 | 265.2 | 32% | tidak | Toad Strike |
| 28 | **Sanguire Voxthal** ◦ | mini | TANK | MAGIC | TANK | A | 67 | 3850 | 415.0 | 565.9 | 266.9 | 32% | tidak | Blood Bolt |
| 29 | **Kaizoku Raijin** ◦ | mini | TANK | MAGIC | TANK | A | 66 | 3400 | 360.0 | 568.4 | 267.4 | 32% | tidak | Thunder Blade |
| 30 | **Vhaerith** ◦ | mini | TANK | MAGIC | TANK | A | 66 | 3750 | 405.0 | 552.3 | 267.0 | 33% | tidak | Hollow Bolt |
| 31 | **Thorgaruk** ◦ | mini | TANK | PHYSICAL | TANK | A | 65 | 3220 | 360.0 | 533.6 | 280.9 | 34% | ya | Skyfall Axe |
| 32 | **Vaelkorr** ◦ | mini | TANK | MAGIC | TANK | A | 64 | 3550 | 390.0 | 531.8 | 267.1 | 33% | tidak | Thread Lance |
| 33 | **Morvath** ◦ | mini | TANK | PHYSICAL | TANK | A | 64 | 3750 | 415.0 | 518.8 | 264.9 | 34% | tidak | Shark Blade |
| 34 | **Ursath** ◦ | mini | TANK | MAGIC | TANK | A | 63 | 3450 | 360.0 | 514.3 | 267.2 | 34% | tidak | Thorn Roar |
| 35 | **Nyxraal** ◦ | mini | TANK | MAGIC | TANK | B | 61 | 3250 | 345.0 | 492.9 | 265.3 | 35% | tidak | Abyss Thrust |
| 36 | **Kassadin** ◦ | mini | TANK | MAGIC | TANK | B | 60 | 3250 | 350.0 | 477.3 | 265.9 | 36% | tidak | Null Blade |
| 37 | **Shimorakh** ◦ | mini | TANK | MAGIC | TANK | B | 60 | 3400 | 360.0 | 469.6 | 265.1 | 36% | tidak | Shadow Root |
| 38 | **Verdanix** ◦ | mini | TANK | PHYSICAL | TANK | B | 59 | 3450 | 355.0 | 463.0 | 265.8 | 36% | tidak | Nature Bolt |
| 39 | **Zorothrax** ◦ | mini | TANK | MAGIC | TANK | B | 58 | 3300 | 350.0 | 456.5 | 263.7 | 37% | tidak | Rune Bolt |
| 40 | **Vardrok** ◦ | mini | TANK | PHYSICAL | TANK | B | 57 | 3300 | 345.0 | 431.2 | 263.7 | 38% | tidak | King's Chop |

## TRUE BOSS

### PHYSICAL (5)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Ravokkar** ◦ | true | PHYSICAL | PHYSICAL | CARRY | B | 58 | 3100 | 300.0 | 391.3 | 339.8 | 46% | tidak | Quickdraw Barrage |
| 2 | **Seraphienne** ◦ | true | PHYSICAL | PHYSICAL | FIGHTER | B | 56 | 2875 | 270.0 | 383.5 | 303.7 | 44% | ya | Divine Verdict |
| 3 | **Thalakryon** | true | PHYSICAL | PHYSICAL | FIGHTER | C | 40 | 2012 | 174.0 | 296.6 | 196.7 | 40% | ya | Abyssal Bolt |
| 4 | **Naraka** | true | PHYSICAL | PHYSICAL | FIGHTER | C | 39 | 1840 | 162.0 | 276.1 | 209.9 | 43% | ya | Chaos Strike |
| 5 | **Kunkka** | true | PHYSICAL | PHYSICAL | FIGHTER | D | 30 | 1610 | 114.0 | 185.1 | 178.8 | 49% | ya | Tide Bringer |

### MAGIC (25)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Nyxharr** ◦ | true | MAGIC | MAGIC | CARRY | B | 58 | 3000 | 290.0 | 395.5 | 334.2 | 46% | tidak | Spirit Charge |
| 2 | **Malzeroth** ◦ | true | MAGIC | MAGIC | CARRY | B | 58 | 3200 | 310.0 | 387.5 | 337.5 | 46% | tidak | Hex Bolt |
| 3 | **Nyrellieth** ◦ | true | MAGIC | MAGIC | FIGHTER | B | 54 | 2850 | 275.0 | 358.7 | 325.3 | 48% | tidak | Frost Arrow |
| 4 | **Morthraxis** | true | MAGIC | MAGIC | FIGHTER | B | 53 | 2530 | 237.6 | 368.2 | 291.6 | 44% | ya | Bat Impale |
| 5 | **Nyreth'zalvarin** ◦ | true | MAGIC | MAGIC | FIGHTER | B | 52 | 2800 | 265.0 | 331.2 | 321.9 | 49% | tidak | Shadow Chain |
| 6 | **Zarethyr** ◦ | true | MAGIC | MAGIC | FIGHTER | B | 51 | 2750 | 255.0 | 318.8 | 318.6 | 50% | tidak | Astral Bolt |
| 7 | **Okeanora** ◦ | true | MAGIC | MAGIC | FIGHTER | C | 48 | 2650 | 240.0 | 300.0 | 311.4 | 51% | tidak | Tidal Verdict |
| 8 | **Nexthyrius** ◦ | true | MAGIC | MAGIC | FIGHTER | C | 46 | 2350 | 210.0 | 273.9 | 303.7 | 53% | tidak | Chain Hook |
| 9 | **Molgravar** ◦ | true | MAGIC | MAGIC | FIGHTER | C | 45 | 2450 | 220.0 | 264.0 | 305.2 | 54% | tidak | Seismic Slam |
| 10 | **Vaelindra** | true | MAGIC | MAGIC | FIGHTER | C | 43 | 2150 | 190.0 | 259.1 | 286.8 | 52% | tidak | Energy Wave |
| 11 | **Nazulmor** | true | MAGIC | MAGIC | FIGHTER | C | 41 | 2070 | 177.6 | 302.7 | 206.4 | 40% | ya | Typhoon |
| 12 | **Solvarin** | true | MAGIC | MAGIC | FIGHTER | C | 41 | 2128 | 182.4 | 296.1 | 216.0 | 42% | ya | Purification |
| 13 | **Aurelion** | true | MAGIC | MAGIC | FIGHTER | C | 41 | 2100 | 182.0 | 248.2 | 281.8 | 53% | tidak | Call Courage |
| 14 | **Seiryukong** | true | MAGIC | MAGIC | FIGHTER | C | 40 | 2000 | 172.0 | 245.7 | 271.2 | 52% | tidak | Boundless |
| 15 | **Nyxareth** | true | MAGIC | MAGIC | FIGHTER | C | 40 | 2050 | 176.0 | 234.7 | 276.6 | 54% | tidak | Starsplit |
| 16 | **Yamako** | true | MAGIC | MAGIC | FIGHTER | C | 39 | 1950 | 165.0 | 235.7 | 265.5 | 53% | tidak | Deep Forest |
| 17 | **Pyraethis** | true | MAGIC | MAGIC | FIGHTER | C | 38 | 1900 | 160.0 | 218.2 | 259.6 | 54% | tidak | Icarus Dive |
| 18 | **Aureth'zar** | true | MAGIC | MAGIC | FIGHTER | D | 33 | 1650 | 140.0 | 190.9 | 227.6 | 54% | tidak | Marksman |
| 19 | **Ignis Drachorn** | true | MAGIC | MAGIC | FIGHTER | D | 26 | 1610 | 110.4 | 179.2 | 136.1 | 43% | ya | Dragon Breath |
| 20 | **Abaddon** | true | MAGIC | MAGIC | FIGHTER | D | 24 | 1495 | 100.8 | 159.8 | 122.3 | 43% | ya | Mist Coil |
| 21 | **Alchemist** | true | MAGIC | MAGIC | FIGHTER | D | 24 | 1380 | 108.0 | 160.1 | 129.1 | 45% | ya | Acid Spray |
| 22 | **Krobellus** | true | MAGIC | MAGIC | FIGHTER | D | 24 | 1500 | 116.0 | 151.3 | 139.2 | 48% | tidak | Exorcism |
| 23 | **Nyxarath** | true | MAGIC | MAGIC | FIGHTER | D | 24 | 1500 | 106.0 | 144.5 | 150.4 | 51% | tidak | Shadowraze |
| 24 | **Vhoreth'zir** ◦ | true | MAGIC | MAGIC | FIGHTER | D | 24 | 1422 | 116.0 | 145.0 | 155.8 | 52% | tidak | Viper Strike |
| 25 | **Ancient Apparition** | true | MAGIC | MAGIC | FIGHTER | D | 19 | 1300 | 80.0 | 104.3 | 120.1 | 54% | tidak | Ice Vortex |

### TANK (24)

| # | Hero | Kelas boss | Kategori | Tipe dmg | Gaya | Tier DPS | POWER | HP | dmg/serang | Basic DPS | Skill DPS | Burst | Melee | Skill |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Yomigetsu** ◦ | true | TANK | PHYSICAL | TANK | S | 100 | 5750 | 588.0 | 911.2 | 376.2 | 29% | ya | Crescent Slash |
| 2 | **Akirakumo** ◦ | true | TANK | PHYSICAL | TANK | S | 100 | 5980 | 600.0 | 929.8 | 378.0 | 29% | ya | Moonfang Slash |
| 3 | **Kaithros** ◦ | true | TANK | PHYSICAL | TANK | S | 100 | 6210 | 612.0 | 1043.2 | 379.7 | 27% | ya | Ember Slash |
| 4 | **Kurosaki Hollowbane** ◦ | true | TANK | PHYSICAL | TANK | S | 100 | 6900 | 648.0 | 1104.5 | 384.7 | 26% | ya | Getsuga Tensho |
| 5 | **Kagetsuka** ◦ | true | TANK | PHYSICAL | TANK | S | 95 | 5060 | 516.0 | 799.6 | 366.5 | 31% | ya | Crimson Slash |
| 6 | **Zyvareth** ◦ | true | TANK | MAGIC | TANK | S | 93 | 4945 | 504.0 | 781.0 | 364.4 | 32% | ya | Crystal Bolt |
| 7 | **Tsukiyora** ◦ | true | TANK | MAGIC | TANK | S | 92 | 5800 | 530.0 | 722.7 | 383.1 | 35% | tidak | Moon Chakra Blast |
| 8 | **Nyxaris** ◦ | true | TANK | MAGIC | TANK | S | 90 | 5600 | 520.0 | 709.1 | 381.4 | 35% | tidak | Moonfire Shot |
| 9 | **Grimkor** ◦ | true | TANK | PHYSICAL | TANK | S | 85 | 4715 | 480.0 | 681.8 | 360.1 | 35% | ya | Sawblade Spin |
| 10 | **Kyrenzai** ◦ | true | TANK | PHYSICAL | TANK | S | 84 | 4370 | 444.0 | 688.0 | 353.2 | 34% | ya | Kagune Pierce |
| 11 | **Cogsworth** ◦ | true | TANK | PHYSICAL | TANK | A | 83 | 4800 | 470.0 | 640.9 | 374.3 | 37% | tidak | Sky Cannon |
| 12 | **Kaerinya** ◦ | true | TANK | PHYSICAL | TANK | A | 81 | 4140 | 420.0 | 650.8 | 348.3 | 35% | ya | Solar Jab |
| 13 | **Pyraena** ◦ | true | TANK | MAGIC | TANK | A | 81 | 4700 | 460.0 | 627.3 | 372.4 | 37% | tidak | Ember Lance |
| 14 | **Sunakage** ◦ | true | TANK | MAGIC | TANK | A | 80 | 4600 | 450.0 | 613.6 | 370.5 | 38% | tidak | Sand Blade |
| 15 | **Deidara** ◦ | true | TANK | PHYSICAL | TANK | A | 79 | 4500 | 440.0 | 600.0 | 368.5 | 38% | tidak | Clay Bird |
| 16 | **Kaineroth** ◦ | true | TANK | MAGIC | TANK | A | 74 | 4200 | 410.0 | 559.1 | 362.3 | 39% | tidak | Crimson Gaze |
| 17 | **Thal'ryndel** ◦ | true | TANK | MAGIC | TANK | A | 72 | 4000 | 390.0 | 531.8 | 357.9 | 40% | tidak | Lightning Bolt |
| 18 | **Xael'moran** ◦ | true | TANK | MAGIC | TANK | A | 69 | 3900 | 380.0 | 495.7 | 355.6 | 42% | tidak | Cold Snap |
| 19 | **Xel'Narath** ◦ | true | TANK | MAGIC | TANK | B | 66 | 3700 | 360.0 | 469.6 | 350.7 | 43% | tidak | Void Lance |
| 20 | **Lyssarethys** ◦ | true | TANK | MAGIC | TANK | B | 63 | 3500 | 340.0 | 443.5 | 345.7 | 44% | tidak | Heartbreak Lance |
| 21 | **Vaelmyrra** ◦ | true | TANK | PHYSICAL | TANK | B | 61 | 3105 | 294.0 | 435.8 | 315.0 | 42% | ya | Blood Verdict |
| 22 | **Zharakzuul** ◦ | true | TANK | MAGIC | TANK | B | 60 | 3300 | 320.0 | 400.0 | 340.3 | 46% | tidak | Void Lance |
| 23 | **Grondmauris** ◦ | true | TANK | MAGIC | TANK | B | 60 | 3400 | 330.0 | 396.0 | 343.0 | 46% | tidak | Earth Break |
| 24 | **Solareth** ◦ | true | TANK | PHYSICAL | TANK | B | 58 | 2990 | 276.0 | 409.1 | 307.6 | 43% | ya | Solar Cleave |

◦ = hero unlock yang belum punya recipe skill khusus (skill-nya masih `_fallback_cast` generik di `hero_skills/_bundle.py`).


---

## Balance pass 2026-08-30 (yang perlu di-balance, hasil ukur - bukan selera)

Semua aturan di bawah lahir dari angka di atas dan diukur ulang dengan alat
yang sama: `python3 tools/balance_audit.py --ingame` (gate: `--check`).
Balance ditulis di SATU tempat: `_core.get_all_hero_types()` memanggil
`hero_balance.apply_to_catalog()`, jadi toko, preview skill, `Hero`, dan AI
membaca angka final yang sama; data mentah `bosses/boss_data.py` tetap utuh.

| Masalah (terukur) | Yang dilakukan | Hasil (terukur) |
|---|---|---|
| corr(HP,DPS) **0.956** - hero mahal menang di dua sumbu sekaligus | re-budget sesuai gaya main: tank dibayar di EHP, carry di DPS (TARGET_RATIO + STYLE_POWER) | **0.535** - tiap arketipe benar-benar beda pilihan |
| hero MAGIC **1.32x** lebih efektif vs boss mini; fisik cuma jadi pajak | paritas sekolah di DAMAGE EFEKTIF per kelas boss (bukan buff mentah) | **1.000 / 1.001** (mini/true), preferensi per boss tetap **1.49x** |
| PHYSICAL\|TANK 2.0x DPS carry (sel terkuat menang dua sumbu) | paritas per SEL arketipe memakai skor power audit, bukan DPS saja | sebaran power 0.84x..1.38x, spread **1.64x** |
| hero murah <2k gem **2.79x** lebih "worth it" | guard efisiensi biaya (median per band + median pool) | sebaran daya dalam satu harga turun ke **1.89x** |
| starter **8.5x** lebih lemah dari hero unlock | catch-up berbasis jumlah hero unlock & level (meluruh sampai lv 8) | gap **5.67x** (dengan catch-up penuh untuk pemain baru); tetap murah, itu harga 0 gem |
| - | TIDAK ada inflasi: rata-rata DPS & EHP pool dikunci ke angka lama | **1.000x / 1.000x** |

Yang sengaja TIDAK disamakan: armor menara tetap hanya menahan fisik
(`hero_balance.TOWER_PHYS_FACTOR`) supaya "hero fisik dorong tower lebih
cepat" tetap jadi alasan memilihnya; dan `ENABLE_SCHOOL_MOD = False` agar
koreksi tidak dihitung dua kali.

Detail lengkap + cara mengukur ulang: `docs/balance_audit.md` dan
`python3 tools/balance_audit.py --ingame --check` (keluar bukan 0 = ada
regresi balance).
