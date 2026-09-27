# Checkpoint migrasi setelah PR #285 — 166/222, BELUM selesai

**166 dari 222 hero target selesai; 56 masih pending.**
Target tetap semua 222 kit, tidak dikurangi. PR #285 (batch 1–6, 164 kit) sudah
merge ke `main` sebagai commit 50b7c07. Progres sesi ini disimpan di branch
`arena/01a0e1d4-mystic-arena` dengan PR draft baru dari branch itu.
**Jangan merge tanpa perintah pengguna.**

**Sinkronisasi GitHub:** batch 7 (Krobellus 1500G, Vhalzun 1200G — level sumber 5)
di-commit dan di-push ke `arena/01a0e1d4-mystic-arena`; CI Godot 4.7.2 untuk batch
ini berjalan pada push tersebut (angka checks final diisi setelah run selesai).
Baseline sebelumnya: 413735 checks hijau run 36302839552 (164 playable).
Static lokal sekarang **4531 checks PASS** (termasuk guard manifest 166/56).

Daftar tepat **semua 164 selesai dan semua 58 belum selesai**, harga summon,
level sumber, handler, oracle/native test dan recipe yang menjadi blocker:
[HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md). Manifest mesin:
[`data/ai/hero_migration_status.json`](data/ai/hero_migration_status.json).
Registry: `scripts/data/hero_roster.gd`; transaksi menolak semua pending tanpa
debit/substitusi. Metadata/baseline angka 222 bukan bukti kit playable.

## Batch yang telah lulus

| Batch | Hero selesai dalam batch | Total / sisa | CI Godot 4.7.2 |
|---|---|---|---|
| Baseline PR #283 | Kaizen, Thorne, Grimjaw, Sylara | 4 / 218 | Baseline diterima |
| 1 | Vex, Zephyr | 6 / 216 | [50.666 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36295879312) |
| 2 | Gornak, Morgath, Drakar, Abaddon | 10 / 212 | [95.314 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36296265931) |
| 3 | 150 ID shared-source eksplisit (lihat daftar) | 160 / 62 | [340.054 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36297544475) |
| 4 | Alchemist | 161 / 61 | [358.305 checks, c029d50](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36298034563) |
| 5 | Ancient Apparition (800G), Nyzrak (850G) | 163 / 59 | [lint fixed, then 413735](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| 6 | Ignis Drachorn (850G) | 164 / 58 | [413735 checks](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36302839552) |
| 7 | Krobellus (1500G), Vhalzun (1200G) — level 5 | **166 / 56** | run branch `arena/01a0e1d4-mystic-arena` (lihat `gh run list`) |

Semua suite lama tetap dijalankan. Oracle sumber, source-contract, static
validation (**4.531 checks** lokal, termasuk guard manifest 166/56), gdparse,
gdlint dan gdformat juga lulus lokal untuk 94 file `.gd`. Engine sandbox tidak
dapat diunduh (TLS ke release-assets/CDN gagal), sehingga import dan seluruh tes
engine dijalankan di workflow Godot resmi yang sudah ada. **Bukan klaim engine
lokal, GPU, perangkat fisik atau visual final teruji.**

## Apa yang diport dan dikunci oleh tes

- **Vex (420 G):** Q orb/line, W burst/slow dan moving ring DOT (30 < r ≤ 55),
  E prison 150 tick/stun max/pulsa 10, R AOE 180/2,5×. Magic homing basic.
- **Zephyr (420 G):** Q fixed-origin trap 240 tick, W heal + immunity 180,
  E curse DOT, R Bedlam. Magic homing basic. Burn diproses sebelum timer realm
  habis, sehingga tick aktif terakhir tetap immune.
- **Gornak:** blink berhenti 60px dari target; counterspell AOE/stun; mana void.
  **Morgath:** basic beam/hit instan adalah pengecualian sumber, bukan arrow;
  flux DOT dan clone mengikuti target/timer sumber. **Drakar:** rage reset ke
  damage katalog, bukan level aktif; execute strictly <30%; flag defense tidak
  diberi mitigasi rekaan. **Abaddon:** heal bukan shield baru; dash 80px tetap
  dapat melewati target sebagaimana sumber.
- **150 boss shared-source:** sumber sendiri tidak mempunyai entry recipe untuk
  ID-ID ini dan benar-benar dispatch ke `BossHeroSkills._fallback_cast`.
  Oracle merekam jalur itu **per ID**, menjalankan QWER, exact cooldown/recast,
  melee/homing, upgrade level 1–15, respawn dan pembelian asli. Allowlist eksplisit
  dikunci CI; **tidak ada fallback native untuk 61 recipe yang belum diport**.
- **Alchemist (750 G):** target-centered W100/slow, E rage 360 + heal 15%,
  R200/heal 100 per kill nyata. Uji zero/multiple kill, radius, anti-heal,
  timer expiry saat upgrade, attack, respawn, summon dan upgrade.
- **Interaksi:** oracle memakai Hero Thorne dan Tower asli, bukan hanya receipt
  HP. Sekolah/source attribution, mitigasi, reflect, shield, dan tower yang
  tidak mempunyai `attack_timer` diuji. Skill tanpa source/school di Python
  tetap **netral**, tidak otomatis memakai sekolah caster.
- **Krobellus (1500 G, level 5):** Exorcism radial 150 ×1,5; Silence radial 120
  ×1,0 + attack clock `max(…,75)`; Siphon single-target ×1,3 + heal
  `int(0,5×skill)`; Crypt radial 200 ×2,5 + heal `int(0,15×max_hp)`.
- **Vhalzun (1200 G, level 5):** Death Pulse radial 130 ×1,5; Heartstopper radial
  150 ×1,0 + clock 60; Reaper's Scythe single-target ×1,8 tanpa heal; Ghost Shroud
  radial 150 ×1,4 + heal `int(0,18×max_hp)`. Override visual sumber
  `BOSS_HERO_VISUAL_DURATION["vhalzun"] = 60/80/60/100` dipertahankan; Krobellus
  tetap default 60/90/60/100 karena `_trigger_*_cooldown` berjalan SETELAH body
  recipe (nilai timer di dalam recipe selalu tertimpa).
- **Level 5 dikunci oleh:** edge radius tepat per slot (r−1/r/r+1, sumbu x dan y,
  arah negatif), gate reach `max(skill_range,140)` = 260 Krobellus / 500 Vhalzun
  pada reach−1/reach/reach+1, retarget saat target mati, target jauh yang tetap
  dipertahankan, recast tepat di tick 220/240/420/900 (gagal di tick −1), heal
  lewat setter HP sumber (cap dulu, lalu anti-heal 0,5 dan 1,0), serangan ranged
  homing, respawn, level 1–15 dengan harga boss 1,6× (Lv1→2 = 480 G), dan penolakan
  ID pending `kunkka` 900 G tanpa debit. Kedua ID **tidak** masuk kelompok
  150 `_fallback_cast` (dicek native terhadap `source_shared_boss_ids.gd`).
- **Ekonomi:** 483 pembelian sumber (161 × harga−1/tepat/+1). Boss upgrade
  **1,6×** starter: Lv1→2 **480 G**; threshold reserve ±1, hero hidup/mati,
  saldo, registry dan clock diuji. Anti-heal mengikuti HP setter: cap dahulu,
  baru potong kenaikan HP. Resource bersama tidak dimutasi.

## Yang tidak berubah

Hanya `godot_rebuild/` diubah; Python asli read-only. Kaizen gratis kedua tim,
defender scene lama, UI/scene scheduler lama tetap. Tidak ada AIPlayer penuh,
item/forge, desain ulang balance, pembelian AI otomatis atau art final. Marker
hero/proyektil tetap prosedural sederhana. “Playable” di sini adalah kit/domain
native tervalidasi, bukan semua fitur pertandingan Python sudah bermigrasi.

## Sisa dan blocker tepat

**56 boss** mempunyai empat recipe khusus yang belum diport dan belum memiliki
oracle/native test per perilakunya. Metode Q/W/E/R untuk masing-masing ID
tercantum di [daftar status](HERO_ROSTER_STATUS.md#belum-selesai--56-id-dan-recipe-yang-menjadi-blocker).
Blocker implementasi: sisa 56 recipe (level 6 dst) belum diport; level 5 sudah
selesai (batch 7). Tidak ada klaim 222 playable.

Sisa per level sumber (56 ID): level 6 → `gravewake` 1000, `kunkka` 900,
`syrentha` 1100, `thalgryn` 1200; level 7 → `akashari`, `malzareth`, `nyxarath`,
`vorenmarr`; level 9 → `kenshiro`, `khazan`, `naraka`, `wiro`; level 10 →
`aurethzar`, `krognarr`, `raz`, `vraskhan`; level 11 → `aeralith`, `aurex`,
`nyxareva`, `thalakryon`; level 12 → `aurelix`, `aurelyssa`, `nazulmor`,
`vargrath`; level 13 → `kaeldris`, `pyraklos`, `solvarin`, `velmyrth`; level 14 →
`azureth`, `luminar`, `pyraethis`, `solara`; level 15 → `auroth`, `morvein`,
`thorvak`, `yamako`; level 16 → `ignirus`, `leoric`, `seiryukong`, `shirotaka`;
level 17 → `kaelthorn`, `nyxareth`, `solvanth`, `xyrael`; level 18 → `aurelion`,
`cryssalia`, `kaelthar`, `morkhaera`; level 19 → `akahime`, `nyxthrael`,
`sylvantheros`, `vaelindra`; level 20 → `astraelion`, `morthraxis`,
`morvaenthir`, `thornvaegrim`.

Lanjut berdasarkan level sumber:
1. **Batch 8 = level 6**: Kunkka, Gravewake, Syrentha, Thalgryn. Kunkka/Gravewake
   melee physical; Syrentha/Thalgryn ranged. Thalgryn `skill_cooldown_max` 300
   (bukan 220/240) — jangan menyamakan cooldown antar hero.
2. Perhatikan recipe yang mengubah posisi/summon (Thalgryn morph/replicate,
   Vorenmarr golem, Yamako wood golem, Shiro taka shadow clones): audit dulu apa
   yang benar-benar dikonsumsi sumber; jangan menambah unit/efek yang tidak ada
   di Python.
3. Jangan memasukkan ID level 6+ ke handler 150 shared-source: source mereka
   mempunyai recipe registry sendiri.
4. Per batch: oracle → handler/state/resource → native combat/transactions →
   semua oracle lama + static/parser/lint/format → CI import + run_all → update
   jumlah/manifest/dokumentasi. Jangan melanjutkan batch kalau masih gagal.

## Menjalankan validasi

```sh
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
# Seluruh oracle lama/new yang berakhiran source_oracle.py:
for t in godot_rebuild/tests/*source_oracle.py; do python "$t" || exit; done
# Oracle kelompok 150 juga dijalankan otomatis oleh validate_project.py:
python godot_rebuild/tests/source_shared_boss_oracle.py
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd')
gdformat --check $(find godot_rebuild -name '*.gd')
# Dengan Godot 4.7.2 tersedia:
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

Parser/lint menggunakan `gdtoolkit==4.5.0`. Oracle `--write` hanya menulis artefak
native; setelah membangkitkan daftar GDScript lakukan gdformat. Jangan mengedit
fixture manual untuk meloloskan hasil yang berbeda dari sumber.

## Pesan siap-salin untuk sesi berikutnya

> Lanjutkan migrasi 222 hero dari snapshot checkpoint Arena terbaru (PR #285
> sudah merge ke main sebagai 50b7c07) pada branch sesi
> arena/01a0e1d4-mystic-arena + PR draft dari branch itu. Saat ini 166/222 kit
> native teruji (6 starter + Gornak, Morgath, Drakar, Abaddon, Alchemist +
> Ancient Apparition, Nyzrak, Ignis Drachorn + Krobellus, Vhalzun + 150 ID
> shared-handler), tersisa 56 (level sumber 6 dst).
> CI baseline 413735 checks (Godot 4.7.2) run 36302839552; static lokal 4531 PASS.
> Baca godot_rebuild/AI_CONTRACT.md, SHIELD_CONTRACT.md, HERO_CONTRACT.md,
> HERO_MIGRATION_PROGRESS.md, HERO_ROSTER_STATUS.md dan manifest
> data/ai/hero_migration_status.json. Lanjut batch level 6 (Kunkka 900G,
> Gravewake 1000G, Syrentha 1100G, Thalgryn 1200G) lalu level 7 dst sesuai
> manifest; lanjut otomatis setelah tiap batch lulus. Hanya ubah godot_rebuild/;
> Python asli read-only. Jangan memakai kit generik pengganti: 56 pending
> mempunyai recipe khusus.
> Pertahankan skill, serangan, cooldown, lifecycle, school/source dan harga
> (upgrade boss 1,6×), dengan source oracle dan tes native tiap perilaku.
> Jalankan semua tes lama, static, parser/lint/format dan CI Godot 4.7.2;
> perbaiki sebelum lanjut. Pending harus tetap ditolak tanpa debit/substitusi.
> Kaizen gratis dan defender scene tetap; tanpa item/forge, AIPlayer penuh,
> rebalance atau art final. Pakai branch sesi Arena yang ditetapkan dan PR draft,
> jangan merge. Update daftar/jumlah tiap batch. Jika konteks habis, simpan
> progres teruji, daftar tepat pending beserta blocker dan pesan lanjutan;
> jangan mengurangi target atau klaim 222 selesai.
