# AIPlayer — target paritas penuh, implementasi bertahap

## Status paket

**Belum port AIPlayer lengkap. Jangan merge sebagai pengganti lawan sementara.**
Target yang disepakati: AIPlayer lengkap beserta roster dan item dependensinya,
bukan pembatasan diam-diam ke Kaizen. Scene pertandingan masih memakai defender
lama dan pasangan Kaizen gratis. Tidak ada transaksi ekonomi otomatis baru di scene;
adapter upgrade/shield red sudah tersedia untuk panggilan domain eksplisit; seluruh suite lama tetap dijalankan.

Sumber read-only: `_entity.py::AIPlayer`, konstanta `_core.py`,
`Game.update` (pemanggilan AI setelah loop entity), `levels/level_data.py`,
registry hero dan `hero_items.py`. Tidak mengimpor runtime Python ke Godot.

## Implementasi saat ini

`ai_policy.gd` memisahkan jadwal dan urutan keputusan dari adapter aksi domain.
Belum dihubungkan ke scene. Callback aksi hanya menandai berhasil/tidak; callback
kontrol hero harus dipanggil sekali setiap tick, bahkan saat belum waktunya berpikir.

- Timer awal 90 tick, tidak langsung memakai interval elite.
- Brain `min(1, (max(1, level)-1)/19)`.
- Elite nol sampai level 20, kemudian `min(1, (level-20)/(max(21, count)-20))`;
  jumlah level default 54. Tidak bergantung pada flag enemy scaling.
- Reset timer `max(8, int(90*(1-0.65*brain)-22*elite))`.
- Budget `1 + round(2*elite)` memakai ties-to-even Python, bukan round Godot.
- Loop aksi berhenti saat aksi tidak berhasil. Urutan setiap langkah:
  build → beli hero → upgrade hero → item → upgrade tower → regen shield →
  castle shield → upgrade nexus.
- Build gate gold **150**, berbeda dari debit build **100** pada adapter nanti.
- Roll memakai `< min(0.98, base+0.45*elite)`, tanpa roll shield.
  Tidak menggambar RNG pada cabang yang tidak eligible atau sesudah sukses.
- Hero count mencakup hero mati; tower count hanya tower hidup milik AI.
  Regen shield memakai semua tower hidup termasuk tower max level.

## Pool, draft dan reserve native

`ai_draft.gd` memakai `data/ai/recruitment.json`: **222 entri metadata**
(6 starter + 216 boss), **54 konfigurasi level**. Ini hanya ID, harga summon,
flag boss, urutan boss per level dan titik asal spawn; **bukan 222 kit playable**.
Data diambil dari kedua definisi `get_all_hero_types` final, modul boss/balance
asli dan konfigurasi level asli. Harga unlock menu tidak dipakai untuk summon.

- Pool iterasi level 1 sampai level sebelum sekarang, urutan mini-boss dari
  dictionary sumber lalu true boss; boss valid dideduplikasi sebelum starter.
  Source-level adalah kemunculan pertama. Config hilang dilewati. Setiap rebuild
  pool mengganti source-level map agar level sebelumnya tidak bocor.
- Draft memeriksa seluruh tipe owned, termasuk hero mati/respawning. Fondasi
  starter uniform; boss pertama uniform dari level sumber terbaru; boss berikutnya
  memakai bobot `max(1, source_level)`. Bila boss habis, pilih starter tersisa.
- Target tetap selama available, **tidak reroll** karena gold kurang. Harga dibaca
  dari catalog, fallback HERO_TYPES, lalu 400. Target tidak available dipilih ulang;
  available kosong dan pembelian sukses membersihkan target+harga reserve.
- Reserve = `max(0, target_cost)` bila target ada, selain itu nol. Nonhero boleh
  belanja tepat pada `gold == cost + reserve`, tidak pada satu gold di bawahnya.
  Reserve sudah diterapkan pada build tower, upgrade tower/nexus/hero dan kedua
  pembelian shield nyata per kandidat; item dan pemilihan prioritas kandidat masih pending.
- `try_buy` menerima roster tipe authoritative, snapshot gold, dan callback
  **sinkron/atomik** `(hero_type, cost, position) -> bool`. Callback wajib
  memvalidasi ulang wallet/capacity, spawn kit benar, debit, lalu tambah roster;
  tidak boleh await, partial mutation, atau mengubah draft secara reentrant.
  Policy tidak menyimpan wallet/roster duplikat. Counter bertambah dan target
  dibersihkan hanya setelah callback sukses.
- Offset spawn mengikuti sumber: `(1120, 130 + owned_count*40 - 40)`;
  hero pertama Y=90, berbeda dari Kaizen merah gratis di scene lama (Y=130).
  Batas 5 hero milik `_ai_step`, bukan `_try_buy_hero`, sesuai Python.
- **Ekstensi defensif native:** callback gagal (misalnya kapasitas) mengembalikan
  false tanpa membersihkan target/reserve/counter. Python langsung membangun Hero
  tanpa return-false adapter. Tes kegagalan ini bukan klaim cabang sumber identik.
- RNG instance dapat di-seed dan picker bisa diinjeksi. Kandidat, bobot dan
  batas interval weighted sama; **stream seed Godot tidak diklaim identik Python**.

## Roster 222 — 222 kit native, 0 pending

Metadata dan baseline konstruktor `data/ai/hero_combat_stats.json` tetap
mencakup seluruh 222 ID. Baseline angka **bukan** bukti playable. Registry
`scripts/data/hero_roster.gd` kini mengizinkan **222 kit** yang punya handler,
source oracle dan tes native; **0 pending**. Daftar tepat dengan harga, recipe
dan bukti per hero: [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md).

- Enam starter: Kaizen, Thorne, Grimjaw, Sylara, Vex, Zephyr.
- Enam puluh enam boss dengan recipe tersendiri (termasuk Gornak, Morgath,
  Drakar, Abaddon, Alchemist, level 1–20). Basic Morgath tetap beam/hit instan;
  bukan projectile generik.
- 150 boss berbagi `BossHeroSkills._fallback_cast` **di sumber asli**. Oracle
  per ID mencatat dispatch nyata, QWER, cooldown, attack, level/upgrade,
  respawn serta combat Hero/Tower. Native memakai allowlist tertutup, tidak
  menjadikannya fallback bagi boss lain yang memiliki recipe berbeda.
- **0 pending.** ID di luar registry tetap ditolak dengan `kit`, saldo/roster
  tidak berubah, draft/reserve tetap. Tidak ada substitusi Kaizen atau shared kit.

Adapter `ai_recruitment.gd` tetap meneruskan draft ke transaksi sinkron
`prototype_battle.gd::_buy_ai_hero`, memakai registry/world/ledger nyata.
Oracle pembelian kini **666 transaksi** (222 × harga−1/tepat/+1), ID/posisi/
capacity/ownership dan double debit diuji. Offset first spawn Y90 tetap,
sementara Kaizen gratis red scene Y130 tetap dan tidak dihitung pembelian.
Scene tidak menyalakan AIPlayer atau pembelian otomatis.

Harga upgrade boss adalah 1,6× starter (Lv1→2 **480 G**), diuji per ID,
level 1–15 dan reserve ±1 dengan hero hidup/mati. Source damage tanpa source/
school tetap netral, berbeda dari skill yang eksplisit membawa school hero.
Mitigasi/reflect/shield, tidak memberi stun palsu pada tower, anti-heal serta
Shadow Realm/burn akhir durasi dikunci dengan objek sumber nyata.

CI Godot 4.7.2 hijau pada main `8119e31`
([run 36329618088](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36329618088)),
semua suite lama tetap. Target 222 tercapai (PR #292 sudah merge).
Catatan batch dan pesan
kelanjutan: [HERO_MIGRATION_PROGRESS.md](HERO_MIGRATION_PROGRESS.md).
Item/Forge player-side sudah dipindahkan bertahap di layer 5f–5f-4; belum
ada panel Forge terpisah untuk hero AI di sumber. AIPlayer penuh, rebalance dan
art final tetap belum selesai.

## Build tower lawan: transaksi domain nyata, belum dijadwalkan scene

`ai_build.gd::try_build` mem-port `_try_build_tower` secara eksplisit, dengan
slot kosong red diambil dari `world.slots` authoritative. Pemilihan slot uniform
lalu jenis archer/cannon/ice/mage berbobot 0,35/0,25/0,20/0,20; picker sinkron
bisa diinjeksi untuk tes, pilihan di luar kandidat ditolak. **Gate policy 150 G**
tetap pada `_ai_step`/`ai_policy.gd`, tidak diterapkan sebagai harga: transaksi
build adalah **100 G + reserve draft terkini** untuk eligibility, debit **100 G**.
Tidak ada draw picker bila slot kosong tidak ada atau saldo di bawah threshold.
Counter `total_built` bertambah sekali setelah transaksi berhasil, tidak di
world atau saat gagal. Tidak ada controller otomatis baru.

`prototype_battle.gd::_build_tower_for` memvalidasi team, slot canonical/owner,
lane, posisi, okupansi, jenis, saldo/reserve, kapasitas, ID registry dan hasil
match sebelum spawn lalu debit sekali via ledger yang sama. Wrapper build lama
tetap Archer tanpa reserve (UI blue tidak diubah; sisi merah milik AIPlayer).
Lv1 non-Archer **bukan** resource Lv2: sumber membuat Archer Lv1 lalu mengubah
`tower_type` dan memanggil `_apply_level_stats`; tabel jenis lain tidak punya
Lv1 sehingga HP 2000, shield 800, damage 20, range 180, CD 35 dan efek 0
jatuh ke Archer Lv1, tetapi identitas, muzzle, dan jenis proyektil mengikuti
jenis pilihan. Native menduplikasi definisi Archer Lv1 **per instance** lalu
mengubah hanya `id`, `display_name`, `tower_path`. Resource `.tres` bersama
tetap utuh. Upgrade Lv1 AI tetap mencoba cannon terlebih dahulu tanpa melihat
jenis build, sehingga misalnya Ice Lv1 dapat menjadi Cannon Lv2 (175 G).

`ai_build_source_oracle.py` mengeksekusi AST AIPlayer dan Tower sumber tanpa
import game/pygame: 96 attempt untuk slot 0/1/3, empat path, reserve 0/400,
threshold ±, 8 batas sampling dan empat stat/tembakan/upgrade Lv1. CI menjalankan
oracle baru lewat `validate_project.py` agar perubahan tetap hanya dalam
`godot_rebuild/`; runner native menguji slot/registry/ledger/proyektil/upgrade
nyata serta kegagalan transaksi. Stream seed RNG Godot tidak disamakan dengan
Python; tes mengunci kandidat, bobot, batas dan draw yang diperlukan saja.

## Upgrade lawan: transaksi domain nyata, per kandidat

`ai_upgrades.gd` menjalankan upgrade tower, nexus dan hero red melalui domain
`prototype_battle.gd`, memakai ledger match yang sama, bukan saldo salinan.
Fungsi internal `_upgrade_*_for` menerima tim dan reserve; wrapper UI lama tetap
**blue-only**, tanpa parameter tim dari command/UI. Quote harga publik tetap blue.

- Validasi match berjalan, ID/tipe, tim 0/1, pemilik, level yang diharapkan, harga
  dan `gold >= cost + max(0, reserve)` sebelum mutation/debit. Tower harus tercatat
  pada slot milik timnya; nexus harus sama dengan nexus authoritative tim.
- `try_tower` Lv1 mencoba **cannon → ice → archer → mage**, bukan acak, dan berhenti
  setelah sukses. Lv2+ mempertahankan path. HP/shield pulih penuh sesuai sumber;
  cooldown, regen timer, projectile dan target tidak direset oleh upgrade.
- Upgrade nexus mempertahankan rumus HP sumber dan rasio paid shield; kapasitas
  free shield tidak diskala lewat jalur paid. Counter bertambah tepat sekali.
- Upgrade hero red **termasuk mati/respawning**, sesuai `_try_upgrade_hero` Python.
  HP, alive, cooldown dan respawn timer tidak berubah; hanya level/stat. Wrapper
  blue tetap menolak hero mati sebagaimana kontrak UI sebelumnya.
- Adapter membaca `draft.reserve()` setiap permintaan: tidak memakai harga draft
  yang dicache saat adapter dibuat. Counter baru nol pada instance match berikutnya.
- `try_tower_priority`/`try_hero_priority` memilih kandidat dengan **urutan
  kills descending stabil** (tie memakai urutan asli: tower urutan slot/world,
  hero urutan roster). Godot `sort_custom` tidak stabil, jadi tie dipecah oleh
  indeks awal. Kandidat yang tidak terjangkau dilewati, pemindaian lanjut ke
  kandidat berikutnya, dan berhenti pada sukses pertama — sama seperti sumber.
  Tower kandidat = tower red hidup Lv<6; hero kandidat = hero red Lv<15
  termasuk mati/respawning. Policy scheduler dan wiring scene belum aktif.
  Tidak menambahkan sorting berdasarkan angka kills palsu atau team kill total.
- **Atribusi kills sumber:** `Hero.kills` hanya bertambah lewat
  `Game._process_hero_kill` — pukulan terakhir dari hero musuh nyata (bukan
  korban sendiri, bukan tower/minion/burn/castle), tanpa popup. `Tower.kills`
  ada di sumber tetapi **tidak pernah di-increment** oleh game Python, sehingga
  prioritas tower nyata jatuh ke urutan asli; native meniru itu (nilai tetap 0).
- Method internal bukan command UI. Pause dicegah oleh session yang tidak
  mengeksekusi command/tick; tidak ada loop background atau timer baru.

## Shield berbayar per kandidat

`ai_shields.gd` memakai transaksi world untuk Regen Shield (tower Lv4–6) dan
Castle Shield (sesudah wave 10, tanpa gate Lv4). `try_regen_priority` memakai
semua tower red hidup yang eligible (termasuk Lv6), diurutkan kills descending
stabil dan berhenti pada pembelian pertama yang berhasil. Keduanya 850 G + reserve
untuk eligibility saldo, debit hanya 850. Tidak ada roll RNG atau increment
counter upgrade. Flag per instance, regen/damage, upgrade dan refund mengikuti
metode sumber; lihat [SHIELD_CONTRACT.md](SHIELD_CONTRACT.md). Scene belum
memanggil AI shield otomatis dan belum memiliki tombol purchase shield.

## Oracle dan tes

`tests/ai_source_oracle.py` mengeksekusi AST metode Python asli: init, brain,
elite, update dan step. Dependensi aksi diganti probe; ini bukan bukti transaksi,
kontrol hero atau roster lengkap. Fixture mencakup 52 trace jadwal 200 tick,
batas round tepat pada elite 0.25/0.75 (count 24), level clamp, step gagal,
dan 486 skenario prioritas/RNG. Tes native membandingkan scalar JSON numerik
sebagai integer/float, tidak membandingkan array Variant numerik secara langsung.
Delapan oracle lama tetap berjalan; oracle policy, draft, upgrade, shield dan build AI ditambahkan.

`ai_draft_source_oracle.py` mengeksekusi init, pool, choose, buy dan reserve asli.
Hero constructor diganti receipt (bukan kit); picker mencatat candidate order dan
weights, weighted sampling memakai `random.choices` Python asli. Tes mengunci
seluruh level 1–55, level nonpositif/di luar katalog, roster mati, exact payment,
draft menunggu, stale target, perubahan level, pool habis, source-level pertama,
metadata tidak valid/duplikat, harga fallback dan default, offset spawn, counter,
serta reserve. Tes native memakai ledger `MatchEconomy` nyata melalui adapter
receipt; tidak ada scene/entity combat yang dibuat oleh adapter tes ini.

CI dipicu pula oleh perubahan boss_data, hero_balance dan hero_archetypes agar
metadata summon tidak tertinggal. `--write` oracle hanya menulis metadata/fixture
native; Python sumber tidak diubah. Oracle tanpa flag hanya membandingkan.

`ai_upgrade_source_oracle.py` mengeksekusi `_try_upgrade_tower_new`,
`_try_upgrade_nexus`, `_try_upgrade_hero`, `_ai_reserve` dan metode entity asli.
122 kasus tower, 58 nexus (free/paid shield), 58 Kaizen (hidup/mati), mencakup
threshold reserve ±1, level maksimal dan path. Kaizen memakai stub inventory
kosong oracle sebelumnya. Tes native memakai world, resource dan ledger nyata,
bukan receipt. Tes tambahan menolak owner/team/ID/type/stale/path/dead/finished,
menguji reserve berubah, non-double-debit, counter dan gate UI blue tetap sama.
Tidak membuktikan upgrade hero dengan item atau kit hero selain Kaizen.

`ai_priority_source_oracle.py` mengeksekusi `_try_upgrade_tower_new`,
`_try_activate_regen_shield` dan `_try_upgrade_hero` dengan banyak kandidat:
16 kasus tower (tie, kills acak, Lv1 path, reserve 0/400, gold nol dan gold
yang hanya cukup untuk kandidat berikutnya), 3 urutan regen shield dan 3 urutan
upgrade hero. Urutan tower dibaca dari list sumber yang disortir in-place;
urutan shield/hero direkonstruksi dari panggilan berulang karena listnya lokal.
`ai_priority_checks.gd` mengulang skenario itu pada world/ledger nyata dan
menguji atribusi kill hero (killer musuh, korban, self-kill, killer bukan hero)
serta `Tower.kills` yang tetap nol.
CI Godot 4.7.2 branch `arena/01a0e398-mystic-arena` (PR draft #293) hijau:
**1.174.376 native checks**, static lokal 5580 PASS.

## Rencana port item AI (hasil survei sumber, dikerjakan per lapisan)

Survei `hero_items.py` (4.133 baris, read-only) untuk `_try_buy_item`
(`_entity.py` ~6474). Urutan kerja yang disarankan, satu commit per lapisan:

1. [x] **Metadata katalog** → `data/ai/item_catalog.json` dari `ITEM_CATALOG`
   (33 item, `ITEM_FLAT_COST = 4500`, `MAX_ITEM_SLOTS = 6`, flag `melee_only`/
   `magic_only`, kategori). Oracle wajib mengeksekusi konstanta sumber (katalog
   memakai nama `CATEGORY_*`, `ast.literal_eval` gagal).
   `ai_item_source_oracle.py` meng-exec hanya assignment konstanta yang
   direferensikan `ITEM_CATALOG` (tanpa import pygame); hasilnya diverifikasi
   terhadap `data/ai/item_catalog.json` oleh `validate_project.py` dan
   `ai_item_checks.gd`. Metadata mencatat juga `drops_on_death`; harga per item
   dibaca dari katalog (Astral Codex 6000, bukan flat 4500).
2. [x] **Suggestion** `suggest_item_for_hero` + `is_magic_hero`: pool per role
   (tank/bruiser/fighter, marksman/assassin, mage/trickster atau magic,
   fallback), melee `range <= 80` menyisipkan `cleave_axe` di depan dan
   `holy_rapier` di belakang, ranged hanya `holy_rapier` di belakang; item
   owned dilewati; filter `melee_only`/`magic_only`. Catatan: `is_magic_hero`
   mengecualikan "anti-mage" dan memakai 18 kata kunci role.
   `scripts/match/hero_items.gd` memuat katalog + keempat pool + gate. Oracle
   merekam 29 role untuk `is_magic_hero`, 26 kasus saran dan 22 urutan beli
   penuh (drain sampai `None`); `ai_item_checks.gd` mengulang drain yang sama.
   `range <= 0` memakai fallback sumber 100 (jadi ranged), `Anti-Mage` memakai
   pool mage tetapi seluruh item `magic_only` terfilter.
3. [x] **Inventory slot** `HeroItemInventory.add/remove/count/has/used_slots`
   (6 slot, gate melee/magic). Perhatian: `add` memanggil `_on_item_changed`
   yang menghitung ulang `max_hp` (`get_max_hp`) dan `apply_heal_amp`; kalau
   stat belum diport, ini **wajib** ditulis sebagai batasan eksplisit, bukan
   diklaim parity. `clear_on_death` menghapus `holy_rapier` permanen.
   `scripts/match/hero_item_inventory.gd` + `HeroState.items` (gate role/range
   di-refresh di `apply_level_stats`, bukan referensi balik ke hero supaya tidak
   ada siklus RefCounted). **BATASAN EKSPLISIT: tidak ada parity stat.**
   `_on_item_changed` (max HP = `base_hp * hp_mult` + hp/hp_pct item, heal amp
   Abyss Breaker, reset timer pasif/aktif di `clear_on_death`) TIDAK diport:
   beli/jatuhkan item hanya mengisi slot, `max_hp`/`hp` hero tidak berubah.
   Oracle merekam `max_hp`/`hp`/`heal_calls` sumber per operasi (7 kasus, term.
   duplikat item, slot penuh, `remove` -1/6, range 0 lolos gate melee) supaya
   selisihnya terlihat; `ai_item_checks.gd` menegaskan HP hero tetap dan bahwa
   sumber menaikkan max HP.
4. [x] **Adapter AI** `ai_items.gd::try_buy`: kandidat = hero red **hidup** dengan
   slot kosong, urut `(kills, level)` descending (Python `sort` stabil,
   tuple key), `gold >= cost + reserve`, debit lewat ledger match, tanpa
   counter khusus di sumber.
   `candidates()` memecah tie dengan indeks roster (sort_custom Godot tidak
   stabil); `try_buy_priority()` melanjutkan kandidat berikutnya saat gold
   kurang, persis seperti sumber. Debit lewat
   `prototype_battle._buy_item_for` (eligibilitas → equip → `economy.spend` +
   event `hero_item`, atomik, harga dari metadata katalog). Oracle menjalankan
   `AIPlayer._try_buy_item` nyata (stub modul `hero_items` + inventori sumber)
   untuk 9 kasus: tie kills/level, hero mati, slot penuh, skip owned, item 6000
   yang tak terbeli lalu kandidat lebih murah, dan reserve 400 yang memblokir
   belanja 4500. Adapter **tidak** menambah counter apa pun.
5. Stat effects, pasif/aura/aktif, Forge UI dan `update_auras` adalah fase
   terpisah yang jauh lebih besar; jangan digabung ke commit adapter.
   - [x] **5a. Agregasi stat murni** → getter port di
     `hero_item_inventory.gd` (`sum_stat`, bonus damage/hp/hp_pct/armor/
     hp_regen, `get_max_hp`, attack speed, lifesteal, crit, cleave, CDR,
     spell vamp, skill amp, evasion, move speed, heal amp, slow resist,
     range bonus, true strike, reflect, gale AS, empower strike, block,
     armor shred, on-attack chain, bash, veil/guard/rend). Katalog kini
     membawa `stats` numerik + blok `passive`/`block`/`on_attack`/`bash`/
     `active` (kunci presentasi tetap di luar). Oracle merekam 25 loadout ×
     28 getter + empower/charge; `validate_project.py` menuntut setiap nama
     getter sumber ada di rebuild.
     **Batasan historis 5a (ditutup oleh 5b–5e):** getter belum dikonsumsi
     combat saat agregasi murni; `_on_item_changed` dan penerapan HP/heal amp
     belum ada pada tahap 5a, sehingga beli item belum mengubah `max_hp`/`hp`.
     Timer (`blood_frenzy`/`ghost`/`thorn`/`gale`/`veil`/`guard`/`rend`/
     `aura_*`) dan callback combat juga baru diaktifkan pada sub-layer berikutnya;
     status finalnya dicatat pada 5b–5e di bawah.
   - [x] **5b.** Penerapan stat HP saat equip/level: `HeroState.recalc_item_stats`
     (port `Hero._recalc_item_stats`), `apply_item_change` (port
     `_on_item_changed`: recalc + `apply_heal_amp(amp, 999999)`),
     `apply_heal_amp` + field `heal_amp_*` di `unit_state.gd` (sumber
     `_core.py:900`), heal amp dikonsumsi `heal_hp` setelah anti-heal (urutan
     setter sumber), dan `apply_level_stats` diakhiri recalc seperti sumber.
     `_buy_item_for` memanggil `apply_item_change()` setelah equip sukses.
     Oracle: 5 urutan equip/drop/level dengan `_recalc_item_stats`/
     `_apply_level_stats`/`upgrade`/`apply_heal_amp` sumber nyata.
     **Batasan 5b ditutup oleh 5b-2/5b-3/5b-4/5b-5.** Semua getter stat item
     (HP/heal amp, attack speed, range bonus, move speed, slow resist, armor,
     shred, damage amp, evasion, true strike, skill amp, CDR, spell vamp) kini
     dikonsumsi jalur combat nyata; konsumennya hidup di `DamageRules`/`HeroState`/`prototype_battle`.
     Catatan deviasi yang tersisa: blind (aura Solar Brand) belum punya setter
     di sumber, jadi sengaja tidak diport.
   - [x] **5b-2.** Stat serangan/gerak dikonsumsi: `HeroState.eff_attack_cd`
     membagi `base_cd` dengan `items.get_attack_speed_mult()` sebelum pembagi
     attack-slow Ice, `HeroState.eff_attack_range` menambah bonus reach
     (gerbang ranged tetap di inventaris), `HeroState.eff_speed` mem-port
     `TowerDebuffMixin._eff_speed` (slow gerak + `move_speed_pct` Tempest Vane
     + stun), dan `prototype_battle.apply_slow` menerapkan `slow_resist` Abyss
     Breaker sebelum penyimpanan strongest-wins. Oracle `stat_consumption`
     mengeksekusi `Hero._eff_attack_cd`/`_eff_attack_range`,
     `TowerDebuffMixin._eff_speed`/`apply_slow` nyata untuk 9 kasus item.
   - [x] **5b-4.** Evasion + true strike di jalur hit nyata:
     `prototype_battle._deliver_hit` meng-override jalur damage dengan gerbang
     `Hero.take_damage` (`_is_physical_hit`: hanya `normal`/`projectile` dan
     bukan magic; `_school` sumber = `resolve_damage_school`, yang membaca
     `dmg_school` penyerang lebih dulu, jadi sekolah masuk yang dipakai).
     Evasion (Monarch Wings) milik DEFENDER, true strike (Sundering Cudgel)
     milik PENYERANG. Hit melee yang miss tidak lagi menjalankan
     `on_basic_attack_hit`, sesuai urutan sumber (proc mengikuti hit yang
     mendarat). Blind (aura Solar Brand) tidak punya setter di sumber mana pun,
     jadi di luar scope. Oracle `evasion` mengeksekusi `_is_physical_hit`
     sumber + `get_evasion`/`has_true_strike` inventaris nyata untuk 7 kasus;
     tes native memutar ulang tiap kasus lewat `_deliver_hit` nyata dengan RNG
     item ter-seed. Jebakan yang sempat merah di CI: item evasion harus
     dipasang di defender, bukan penyerang.
   - [x] **5b-6.** Blind Scorched Earth: `UnitState.apply_miss_chance`
     (sumber `TowerDebuffMixin.apply_miss_chance`, terkuat menang, durasi
     melebar me-refresh keduanya) + `blind_amount`/`blind_timer` yang ikut
     `tick_item_debuffs()`; aura Solar Brand kini membaca nilai `blind` katalog
     dan memanggilnya untuk unit di dalam radius; gerbang evasion memakai
     aturan sumber `miss_chance = max(evasion, blind penyerang)` pada satu
     undian, dan true strike menembus keduanya. Oracle `miss_chance`
     mengeksekusi setter sumber untuk 5 urutan x 2 nilai evasion; tes native
     memutar ulang stacking, laju miss empiris, true strike, dan decay.
   - [x] **5b-5.** Skill amp/CDR/spell vamp: `HeroState.skill_damage` menerapkan
     amp Astral Codex sebelum faktor skill-down menara Mage;
     `HeroState.cdr_cooldown` mem-port potongan Octarine Core dari `cast_skill`
     (karena semua gerbang skill mensyaratkan `cd <= 0`, `max(0, after -
     added * cdr)` sumber menyusut jadi `cd_max * (1 - cdr)`) dan dipakai di
     empat titik penetapan cooldown Q/W/E/R sehingga jalur pemain dan AI
     keduanya kena; `spell_vamp_heal` menyetel `hp` langsung (tanpa `heal_hp`,
     jadi heal amp tidak ikut) dan dipanggil sekali per cast sukses dari
     auto-cast AI serta empat wrapper blue. Oracle `spell_power`
     mengeksekusi getter `Hero.skill_damage` sumber untuk 6 kasus.
   - [x] **5e-3.** Miasma pada minion memakai `definition.max_hp` (sumber
     `minion.max_hp`) sehingga racun memakai damage % Max HP, bukan lantai 6;
     `_hero_enemy_list()` tetap null-safe untuk unit tanpa `max_hp`.
   - [x] **5b-3.** Debuff item di sisi TARGET: `UnitState.apply_armor_shred`
     (Corroder) + `apply_damage_amp` (Soul Rend) mengikuti setter sumber
     (terkuat menang, durasi lebih panjang me-refresh keduanya, target mati
     diabaikan) dan `tick_item_debuffs()` mem-port potongan item dari
     `_tick_tower_debuffs` (decrement per tick, amount dibersihkan di tick
     terakhir); `prototype_battle` men-decay seluruh unit sekali per tick.
     `DamageRules.effective_armor` = armor definisi + armor item hero - shred,
     `DamageRules.item_aware_amount` = mitigasi sekolah lalu damage amp Soul
     Rend, dipakai `_damage_amount`. Bus `battle_item_effects` mendaratkan
     keduanya ke unit nyata. Oracle `item_debuffs` mengeksekusi tiga setter
     sumber untuk 10 urutan; tes native memutar ulang setiap op, menguji decay
     dan membuktikan armor Steel Aegis menurunkan hit fisik sementara
     shred/amp menaikkannya lagi.
   - [x] **5b+.** Kematian hero: `prototype_battle._on_hero_death` memanggil
     `items.clear_on_death()` seperti cabang mati `Hero.take_damage`
     (`_entity.py:4742`). Sumber TIDAK menghitung ulang max HP di cabang itu
     dan Holy Rapier tidak punya stat HP, jadi rebuild juga tidak; oracle
     mengunci 3 kasus (slot sesudah mati, flag `dropped`, max HP sebelum =
     sesudah) dan native membunuh hero nyata lewat hook match (atribusi kill
     tetap 1, item lain tetap di slot).
   - [x] **5c-1.** Mesin waktu timer: `hero_item_inventory.tick_timers(dt)`
     memindah bagian timer murni dari `HeroItemInventory.update` (27 atribut
     yang di-decrement sumber, `blood_frenzy_timer`/`blood_frenzy_cd`/
     `last_damage_timer`, reset `rend_target` saat `rend_timer <= 0`, dan
     pengisian `empower_charge` Runic Gavel). Oracle mengeksekusi `update`
     sumber nyata (stub `_tick_miasma`/`_fx_notify`, `enemies=None`) untuk 4
     kasus dan merekam seluruh timer per tick; `validate_project.py`
     menuntut setiap atribut timer sumber punya field di rebuild.
   - [x] **5c-2.** Setengah auto-trigger `HeroItemInventory.update` +
     `notify_damage_taken` + pemanggilan `tick_timers` dari loop match:
     `hero_item_inventory.tick_auto(dt, enemies, effects, rng)` menjalankan
     seluruh Tier II/III/paket-magic auto-trigger (Blood Frenzy, Bulwark,
     Veil, Chains, Soul Rend, Overwhelm, Static Charge tick zap, Thornmail,
     Arctic Blast, Gale Leap, Brand Burst, Arcane Nova, Energy Blast, Hex,
     Discord Field, Vitality Pact, Spectral Form) dan HP regen (termasuk
     Leviathan out-of-combat); efek didispatch lewat bus `ItemEffects` ke
     `prototype_battle._battle_item_effects` (damage via `_deliver_hit`,
     stun ke `HeroState.stun_timer`, silence/burn/slow ke field
     `UnitState` yang sudah ada). `notify_damage_taken(damage, source_id,
     ...)` me-reset `last_damage_timer` Leviathan, menggulir peluang proc
     Static Charge dan memantulkan Thornmail lewat bus terpisah. Hook
     `_tick_hero_items` dipanggil dari `minion_battle._tick_hero` (tanpa
     menambah baris: satu komentar digabung); `_notify_item_damage`
     dipanggil dari `_deliver_hit` (satu baris komentar diganti). Oracle
     meng-exec `update` dan `notify_damage_taken` sumber nyata dengan
     `_EffectStub` untuk 18 skenario auto-trigger dan 5 skenario notify;
     native mereproduksi skenario yang sama lewat bus `_TestItemFx` dan
     menguji tick Leviathan regen di world nyata. `minion_battle.gd`
     tetap 1000 baris.
     **Batasan 5c-2:** `armor_shred` masih dicatat di bus tanpa state
     target; efek posisi Gale Pike menggeser `position` tanpa collision.
     Sudah menyusul: aura + `update_auras` (5d), on-hit proc
     `on_basic_attack_hit`/`_on_hit_common`/`on_ranged_attack_hit` (5e), dan
     Miasma/Polycephaly (5e-2).
   - [x] **5d.** Aura & `update_auras` (armor/AS/guard block/armor reduction,
     Scorched Earth ke menara/boss).
   - [x] **5e.** Proc on-hit/chain/miasma (`_on_hit_common`, ranged variant).
   - [x] **5e-2.** Miasma (% Max HP per tick, clamp 6..cap, refresh
     max-damage/max-timer/min-tick, reset 30 tick) + Polycephaly (ranged-only,
     2 musuh terdekat dalam 200 px, 70% damage magic + Miasma); Soul Rend crit
     sudah ada sejak 5e. Registry Miasma per inventaris (sumber: registry
     module-level per id(target)), jadi dua pemilik bisa menumpuk racun pada
     target yang sama; `UnitState` belum punya `max_hp`, jadi racun ke minion
     jatuh ke lantai 6 damage/tick.
   - [x] **5f.** Forge shop (transaksi `_try_buy`/`_try_drop`/
     `_resolve_shop_target`/antrian `pending_forge_items`): target tersimpan ->
     terseleksi -> hero hidup pertama -> hero pertama; gerbang katalog/gold/
     slot (antrian ikut dihitung)/role; hero hidup langsung memakai item, hero
     mati mengantre dan pesanan dikirim saat respawn; drop tanpa refund.
     Panel ItemShopUI (gambar + input) dan i18n belum port — pesan memakai kunci
     `tr()` sumber sebagai `status`.
   - [x] **5f-2.** Panel ITEM FORGE (state + routing klik): `item_shop_ui.gd`
     mem-port `get_item_class`/`_build_shop_pages`/`CLASS_ITEM_ORDER` (6 halaman,
     grid 4x2, tab PHYSICAL/MAGIC/TANK), state `item_shop_open`/`itemshop_page`/
     `itemshop_inspect_item`, dan kosakata tombol `handle_item_shop_click`
     (`itemshop_close`, `_hero_`, `_page_`, `_buy_`, `_slot_`, `_card_`, popup
     detail menelan klik, klik luar panel menutup). Data tampilan chip/kartu/tab
     tersedia untuk Control; geometri pygame, font/warna dan i18n tetap di luar.
   - [x] **5f-3.** Control panel ITEM FORGE (`item_forge_panel.gd`): menggambar
     chip hero ("BELI UNTUK n"), tab kelas, grid kartu 4x2 dengan tombol BELI per
     kartu, baris slot pembeli (klik kiri = inspeksi, klik kanan = drop) dan
     popup detail; semua tekanan tombol dikembalikan lewat kosakata
     `handle_click` yang sama. Layout memakai container Godot, bukan rect
     pygame; string Indonesia di `SHOP_TEXT` menggantikan `tr()` sumber.
     Terpasang di HUD PrototypeMatch dengan toggle "Item Forge [I]".
   - [x] **5f-4.** Wiring input overlay Forge di scene: klik kiri di luar
     kartu menutup toko, klik kanan di background menutup toko, klik di luar
     popup detail hanya menutup popup, dan klik kosong di kartu tetap tertahan
     agar tidak memilih arena. Right-click slot tetap drop tanpa bubbling ke
     overlay. `forge_scene_checks.gd` menguji perilaku ini lewat scene nyata;
     CI Godot 4.7.2 hijau pada **run 36734583489** dengan **1.185.776 native
     checks**, `validate_project.py` **5968 static checks**.
   - [x] **6a.** Kontrol hero AI setiap tick (`ai_hero_control.gd`): port
     `_control_heroes` (auto-cast lewat `try_auto_cast` yang sama dengan pemain,
     penanda `skill_timer == 0`, counter `total_skills_cast` dari kenaikan
     `active_skill_timer`) dan `_assign_hero_lane` (ancaman per lane dari minion
     hidup, tie -> TOP, minion musuh TERDEKAT secara Euclidean di lane itu ->
     x-nya + y lane, taman `x=600`, fallback tower terdekat dengan standoff 60).
     `destination_auto` membatalkan tujuan AI begitu musuh masuk aggro range 250
     (tujuan manual tetap ditaati). Kontrol dijalankan di `step_tick` tetapi
     masih di balik flag `ai_hero_control_enabled` (default mati) sampai
     pengontrol AI tersambung ke scene.
   - [x] **6b.** Pembungkus jadwal (`ai_controller.gd`): port `AIPlayer.update`
     (kontrol hero setiap tick, berpikir hanya saat `think_timer` habis, aksi
     `1 + round(2*elite)`, berhenti pada prioritas pertama yang gagal) plus
     diagnostik per tick dan passthrough `_ai_reserve` dari draft. Disambungkan
     ke `prototype_battle.step_tick` lewat flag `ai_enabled`; `_ai_perform_step`
     adalah seam pemindaian prioritas dan untuk sementara melaporkan "tidak ada
     aksi" sehingga belum ada transaksi ekonomi saat scene masih memakai
     defender sementara.
   - [x] **6c.** Pemindaian prioritas nyata: `_ai_perform_step` memanggil
     `ai_policy.choose_step(_ai_state(), _ai_attempt, ai_controller.draw)`,
     sehingga urutan sumber (build -> beli hero -> upgrade hero -> item ->
     upgrade tower -> regen shield -> castle shield -> upgrade nexus) berjalan
     di atas adapter nyata dan ledger yang sama; `_step_defender` mundur selama
     `ai_enabled` dan setiap undian memakai RNG ter-seed milik controller.
     Aksi nexus gagal begitu nexus merah hancur.
   - [x] **6d.** AI nyata mengambil alih pertandingan: `set_ai_enabled()` menjadi
     satu sakelar yang memarkir defender sementara (dan menyalakan kontrol hero)
     sementara AI memiliki sisi merah; `reset_ai(seed)` membangun ulang keadaan
     AI seperti `Game.reset()` membuat `AIPlayer` baru (jam berpikir, counter
     adapter, counter skill hero, draft persisten) dan menyemai ulang aliran
     controller/build/draft dari seed pertandingan `AI_MATCH_SEED`. Sesi
     prototipe menyalakannya setelah `setup_arena()`, jadi setiap pertandingan
     bisa direproduksi. Jalur pause tetap tertutup karena tick sesi berhenti
     (PROCESS_MODE_PAUSABLE): uji scene memastikan jam, jadwal dan dompet AI
     tidak bergerak saat pause, dan setiap layar hasil restart memakai AI baru
     dengan seed yang sama.
   - [x] **6e.** Defender sementara dibuang: `_step_defender()` (tiga pembelian
     Archer terjadwal) beserta `defender_enabled`/`_defender_built`, call-site
     di `step_tick()` dan baris `defender_enabled = not enabled` dihapus, jadi
     `set_ai_enabled()`/`ai_enabled` adalah satu-satunya sakelar sisi merah:
     dengan sakelar mati tidak ada transaksi merah sama sekali (uji menuntut
     `spent[1] == 0` dan `ai_build.total_built == 0`). Uji domain/layar (cannon,
     ice, mage, nexus, prototype, scene checks, run_all) tidak lagi menparkir
     defender; blok skirmish `cannon_checks` sekarang membuktikan AI nyata
     membangun tower merah di atas ledger yang sama.
   - [x] **6f.** Skenario AI yang menggantung ditutup di `prototype_checks.gd`:
     `_hero_red_retreat` (retreat hero merah + heal 3.0/tick di radius 100 px
     nexus sendiri, hanya 0.15/tick di luar base walau tetap menyerang, keluar
     retreat di rasio 0.80, dan lane order AI membatalkannya seperti `move_to`
     sumber) serta `_hero_out_of_lane` (hunt map-wide 900 px: musuh lane lain di
     dalam aggro 250 menarik hero keluar dari lane order, dan hunt memilih musuh
     terdekat lintas-lane). Catatan penting: `_try_auto_cast` sumber mengisi
     `hero.target` (port: `hero.target_id` lewat gate skill), sehingga uji
     lane-order wajib menaruh ancaman di luar `skill_range` 100 px.
   - [x] **7a.** Castle AI naik level otomatis mengikuti wave: port
     `Game._auto_scale_ai_castle` (`_core.py:1856`, dipanggil dari
     `update_waves`) — wave ≥4/7/10/13 menaikkan nexus merah ke level 2/3/4/5
     **gratis** (sumber `Castle.upgrade` tidak menyentuh gold; pemain tetap
     membayar nexus-nya sendiri). Dipanggil di cabang `batch.started` `step_tick`
     persis sebelum spawn batch, memakai `NexusUpgrades.LEVELS`. Helper baru
     `_apply_nexus_stats(nexus, target)` juga menggantikan jalur upgrade berbayar,
     jadi HP baru = `int(new_max*ratio) + (new_max-old_max) + 500` di-cap
     `new_max`, damage/range/cooldown ikut level, dan rasio shield terjaga.
     Oracle sebelumnya men-stub fungsi ini — sekarang `castle_auto_scale`
     meng-exec `Castle.upgrade`/`_apply_level_stats` dan
     `Game._auto_scale_ai_castle` asli untuk wave 1-30 + kasus shield 50%
     (fixture `match_source.json` diregenerasi lewat `--write`, +222 baris).

   - [x] **7b.** Jitter spawn minion: port empat statement
     `Minion.__init__` (`_entity.py`): offset acak `random.uniform(-8, 8)`
     pada x dan y setelah penempatan waypoint, lalu offset lane Y
     `-20/0/20` yang sudah diterapkan `spawn_unit`. Diterapkan di jalur
     spawn wave (`_spawn_match_minion`) dengan stream ter-seed
     (`SPAWN_SEED`) supaya pertandingan yang di-restart replay — aliran
     Python tidak direproduksi; `spawn_unit` laboratorium tetap eksak
     untuk tes kontrak yang menaruh unit manual. Dua situs `Minion(...)`
     lain (`_core.py:8814`/`:8822`) adalah summon yang menyusul bersama
     layer boss. Oracle `minion_spawn_offsets` meng-exec slice asli lima
     statement; native `_spawn_jitter` memutar ulang baris fixture,
     60 spawn dua tim/tiga lane, hero bebas jitter, dan replay dua world.

   - [x] **7c.** Difficulty lawan + level config: `LEVEL_1` dari
     `levels/level_data.py` kini data nyata (`data/levels/level_1.json`,
     ditulis oracle; `validate_project.py` menuntut file itu sama dengan
     section `level_one` fixture). Aturan `Game.reset` diport apa adanya:
     hanya `"hard"` yang menyalakan enemy scaling dan mengalikan
     `enemy_hp_mult/damage/speed` level dengan 1.15/1.10/1.0 (nilai lain,
     termasuk yang tak dikenal, tetap 1.0). Blok minion merah
     `Game.update_waves` menjadi `_enemy_scaled_definition`: `int()`
     memotong hp/damage di atas tier nexus, speed dikali float, hp ikut
     max baru; sisi biru tidak pernah terskala. Tiga statement
     castle-start `Game.reset` juga diport (`_apply_castle_start_levels`):
     biru naik ke `starting_castle_level`, merah hanya ke
     `castle_start_level` saat scaling aktif, gratis lewat jalur
     `Castle.upgrade` yang tidak menyentuh ledger. Selector difficulty di
     UI masih belum ada (sumber pun memilihnya di settings screen).
     Oracle `enemy_scaling` menjalankan `Minion.__init__` asli (MINION_TYPES
     asli + stub mixin) untuk easy/normal/hard/unknown di tier nexus 1 dan
     4, plus baris castle-start (config asli + sintetis 3/2); native
     `_enemy_scaling` memutar ulang semuanya termasuk ledger nol.

## Batas baris file GDScript: dicabut (paritas lebih penting)

`gdlint` bawaan membatasi 1000 baris per file (`max-file-lines`). Mulai sesi ini
batas itu **dicabut** untuk file yang menampung logika paritas:
`scripts/combat/minion_battle.gd` dan `scripts/match/hero_item_inventory.gd`
memakai direktif `# gdlint:disable=max-file-lines` (dan
`max-public-methods` untuk inventaris), seperti yang sudah dipakai
`tests/ai_item_checks.gd`. Alasan: batas itu sempat memaksa logika combat
disembunyikan ke file lain dan membuat edit harus "line-neutral"; port paritas
Pygame → Godot tidak boleh dikorbankan demi batas lint. Yang tetap dijaga:
`gdformat`/`gdlint`/`gdparse` bersih, fixture oracle tetap diregenerasi lewat
oracle (bukan edit tangan) dan tetap di bawah 20k baris.

## Dependensi yang wajib selesai sebelum integrasi penuh

- [x] Roster enam starter dan seluruh boss yang eligible dari level sebelumnya:
  222 kit native dengan oracle/tes telah lulus, 0 pending (lihat manifest).
  Marker prosedural bukan bukti tampilan final.
- [x] Policy pool terurut boss lalu starter, deduplikasi, source-level pertama; tidak
  memasukkan boss level saat ini. Draft starter pertama acak, boss pertama dari
  level terbaru, berikutnya berbobot source-level; tipe owned termasuk hero mati.
- [x] Policy target draft persisten sampai terbeli, reserve harga; jangan mengganti target
  hanya karena kurang gold. Hapus target ketika available kosong atau pembelian sukses.
- [x] Transaksi red memakai ledger yang sama, reserve pada seluruh belanja non-hero,
  tanpa bonus gold. Hero spawn `RED_BASE_X-60, RED_BASE_Y+30+(count*40-40)`.
- [x] Build slot acak; jenis archer/cannon/ice/mage berbobot .35/.25/.20/.20;
  hanya adapter per aksi, belum terhubung ke scene.
- [x] Upgrade tower kills descending stabil; Lv1 path cannon/ice/archer/mage.
- [x] Transaksi upgrade tower/nexus/hero red per kandidat dengan live reserve;
  hero mati tetap eligible, batas level sumber, ledger dan counter nyata.
- [x] Urutan kandidat upgrade hero/tower kills descending dan atribusi kills sumber.
- [x] Item/inventory/stat effects/forge dan suggestion role+range; kandidat hidup
  dengan slot kosong, kills lalu level descending; reserve dipatuhi.
  Lapisan 1-4 + 5a + 5b/5b+/5b-2/5b-3 + 5c-1/5c-2 + 5d + 5e/5e-2 + 5f/5f-2/5f-3/5f-4
  selesai: katalog 33 item, saran role+range, inventaris 6 slot, adaptor beli
  AI di ledger, SELURUH penerapan stat item (HP/heal amp, attack speed, range
  bonus, move speed, slow resist, armor, armor shred, damage amp, evasion,
  true strike, skill amp, CDR, spell vamp), timer pasif/aktif, aura, proc
  on-hit, Miasma/Polycephaly (termasuk pada minion), dan Forge shop + panel UI.
  Tidak ada sub-layer item yang tersisa. Dua catatan yang dulu ditulis sebagai
  "deviasi" sudah dikoreksi lewat pembacaan sumber: kandidat item AI yang
  hidup-saja MEMANG perilaku sumber (`_entity.py:6488` menyaring `alive`), dan
  blind sudah diport di 5b-6 (`apply_miss_chance` + aura Scorched Earth).
  Sisa catatan jujur: panel Forge adalah UI sisi pemain di sumber juga (tidak
  ada panel untuk hero AI), dan efek posisi Gale Pike menggeser `position`
  tanpa collision, sama seperti sumber.
- [x] Regen shield Lv4+ termasuk tower Lv6 dan castle shield per kandidat:
  eligibility/cost/debit, live reserve, regen/damage, upgrade dan refund sumber.
- [x] Prioritas kandidat Regen Shield kills descending stabil.
- [x] Kontrol hero setiap tick: jalur auto-cast bersama pemain, skill counter
  berdasarkan perubahan active timer; lane ancaman maksimum (tie top/mid/bot),
  minion terdekat secara Euclidean, destination auto; fallback tower terdekat
  dengan offset 60. Jangan mengganti prioritas target dengan urutan x. (6a +
  fixture `hero_control`; hunt lintas-lane dan retreat hero merah diuji di 6f.)
- [x] Integrasi scene/session setelah entity loop tanpa double auto-cast,
  seeded RNG yang bisa diuji (bukan klaim stream identik Python), pause/reset/hasil.
  (6d; `prototype_session` memakai `set_ai_enabled(true)` + `AI_MATCH_SEED`.)
- [x] Ganti assertion defender lama hanya setelah perilakunya benar-benar diganti;
  pertahankan suite dan invariant wallet/slot/replay. (6e; skenario merah tanpa
  sakelar AI kini dituntut tetap tanpa transaksi.)
- [ ] Runtime CI hijau untuk setiap tahap dan uji integrasi penuh sebelum ready PR.

Tidak mengklaim parity item, roster, AI lawan playable, balance, visual atau
perangkat fisik dari tes policy ini.

## Status sesi `arena/01a0e3e4-mystic-arena` (PR draft #294)

Selesai: port item AI lapisan 1-4, satu commit per lapisan, basis main f1d34ed.

1. `data/ai/item_catalog.json` (33 item, flat 4500, 6 slot, kategori, flag
   `melee_only`/`magic_only`/`drops_on_death`) + `ai_item_source_oracle.py`
   yang meng-exec konstanta sumber (bukan `ast.literal_eval`).
2. `scripts/match/hero_items.gd`: `is_magic_hero` (18 kata kunci, anti-mage
   dikecualikan) + `suggest_item_for_hero` (4 pool role, sisipan cleave/rapier,
   skip owned, gate melee/magic).
3. `scripts/match/hero_item_inventory.gd` + `HeroState.items`: slot,
   `add/remove/count/has/used_slots/owned`, `clear_on_death` menghapus rapier.
   **Batasan: tanpa stat effects** (lihat langkah 3 di atas).
4. `scripts/match/ai_items.gd` + `prototype_battle._buy_item_for`: kandidat
   hidup ber-slot kosong, `(kills, level)` descending stabil, reserve draft
   hidup, debit ledger nyata, tanpa counter baru.

Oracle: `ai_item_source_oracle.py` (katalog + stats, 29 role magic, 26 saran,
22 urutan pool penuh, 7 skrip operasi inventori, 9 kasus `_try_buy_item` nyata,
25 loadout stat, 5 stat_application, 3 death, 4 timer-only, 18 auto-trigger,
5 notify_damage, 6 miasma, 8 forge). Native: `ai_item_checks.gd` terdaftar di
`run_all.gd`.
CI Godot 4.7.2 run 36468688990 hijau untuk lapisan 6b (commit `987ff13`):
**1.179.197 native checks**, static lokal 5747 PASS; `gdlint`/`gdformat`/`gdparse`
bersih; `minion_battle.gd` dan `hero_item_inventory.gd` tepat 1000 baris (batas lama)
(fixture 11.615 baris, masih di bawah 20k).
CI Godot 4.7.2 run 36477994234 hijau untuk lapisan 6c (commit `efd3129`):
**1.179.226 native checks**, static lokal 5765 PASS; `gdlint`/`gdformat`/`gdparse`
bersih; `minion_battle.gd` dan `hero_item_inventory.gd` tetap tepat 1000 baris
dan fixture tidak berubah.
CI Godot 4.7.2 run 36482247766 hijau untuk lapisan 6d (commit `6d9a49f`):
**1.179.241 native checks**, static lokal 5768 PASS; `gdlint`/`gdformat`/`gdparse`
bersih; `minion_battle.gd` dan `hero_item_inventory.gd` tetap tepat 1000 baris
dan fixture tidak berubah (lapisan ini tidak menyentuh oracle).
CI Godot 4.7.2 run 36508998487 hijau untuk lapisan 6e (commit `5e98734`, push):
**1.179.249 native checks**, static lokal 5768 PASS; fixture 11.959 baris dan tidak berubah.
CI Godot 4.7.2 run 36520788435 hijau untuk lapisan 5b-6 (commit `4345115`, push,
setelah dua run merah: 36519780447 gagal karena `blind_miss_chance` mengetik
`HeroState` yang tidak dideklarasikan di `ai_item_checks.gd` — sekarang
`World.HeroState`; lint 1917c9a gagal karena direktif `max-public-methods`
tertimpa saat mencabut batas baris): **1.179.392 native checks**, static lokal
5771 PASS.
CI Godot 4.7.2 run 36516328470 hijau untuk lapisan 5b-4 (commit `a8c39c0`, push,
setelah run 36515759673 merah karena uji menaruh item evasion di penyerang):
**1.179.332 native checks**, static lokal 5771 PASS.
CI Godot 4.7.2 run 36516994267 hijau untuk lapisan 5b-5 (commit `ccf8a74`, push):
**1.179.363 native checks**, static lokal 5771 PASS.
CI Godot 4.7.2 run 36518120579 hijau untuk lapisan 5e-3 (commit `91b7bf0`, push,
setelah run 36517663936 merah karena uji memakai stub fx yang tidak mengirim
damage): **1.179.365 native checks**.
CI Godot 4.7.2 run 36512974862 hijau untuk lapisan 5b-2 (commit `10db2c7`, push):
**1.179.293 native checks**, static lokal 5768 PASS; `minion_battle.gd` tetap
1000 baris, fixture 12.191 baris (regenerasi lewat oracle, bukan edit tangan).
CI Godot 4.7.2 run 36513763224 hijau untuk lapisan 5b-3 (commit `39c7d60`, push):
**1.179.316 native checks**, static lokal 5771 PASS; `minion_battle.gd` tetap
1000 baris dan fixture di bawah 20k.
CI Godot 4.7.2 run 36510010594 hijau untuk lapisan 6f (commit `81e4faa`, push):
**1.179.249 native checks**, static lokal 5768 PASS. Uji 6f sempat merah di run
36509433010 (`FAIL: the AI lane order overrides the retreat`): ancaman uji berada
di dalam `skill_range` 100 px sehingga auto-cast bersama mengisi `hero.target`
(perilaku sumber `_try_auto_cast`), jadi lane order memang tidak jalan — setup
uji diperbaiki (ancaman di 400 px), commit di-amend, lalu hijau.
CI Godot 4.7.2 run 36527889355 hijau untuk lapisan 7a (commit `d43a92a`, push):
**1.179.516 native checks**, static lokal 5774 PASS; `gdformat`/`gdlint`/`gdparse`
bersih; fixture `match_source.json` 1.871 baris (+222 dari section
`castle_auto_scale`, diregenerasi lewat `match_source_oracle.py --write`;
angka 12.345 yang sempat ditulis di sini adalah salah hitung).
CI Godot 4.7.2 run 36530426529 hijau untuk lapisan 7b (commit `39b92ab`, push,
setelah run 36529605635 merah karena `lane_offsets == [-20, 0, 20]`
membandingkan array JSON float dengan int secara ketat — sekarang elemen
dibandingkan satu per satu): **1.179.721 native checks**, static lokal 5777
PASS; fixture `match_source.json` 1.980 baris (+109 dari section
`minion_spawn_offsets`).
CI Godot 4.7.2 run 36533751518 hijau untuk lapisan 7c (commit `3554c56`, push,
setelah run 36532872047 merah karena baris nexus 4 membandingkan minion biru
tier-1 dengan baseline sebelum tier nexus — sekarang baseline diambil dari
baris nexus 1): **1.179.765 native checks**, static lokal 5792 PASS; fixture
`match_source.json` 2.181 baris (+201 dari section `enemy_scaling`/`level_one`),
data baru `data/levels/level_1.json`.
Catatan panel: `_clear()` melepas lalu membebaskan node lama segera (tanpa
`queue_free`) supaya baris yang dibangun ulang langsung bisa dihitung dan tidak
ada node yatim saat proses keluar; `press()` menunda redraw hanya saat panel ada
di dalam tree (membebaskan Button yang sedang mengirim sinyal = crash). Popup
detail menelan klik lain (sesuai sumber), jadi tutup popup dulu sebelum menekan
slot/kartu.

Koreksi yang perlu diingat: metadata katalog awalnya memetakan NAMA konstanta
`CATEGORY_*` -> id kategori, sehingga validasi kategori per item selalu gagal
di native (33 FAIL). Sekarang `categories` di-key oleh id kategori dengan nilai
nama konstanta sumber, dan `validate_project.py` menuntut kunci itu sama dengan
himpunan kategori yang benar-benar dipakai.

Status sesi `arena/01a0eacd-mystic-arena` (PR draft #300, basis main `5e5f32a`):
6e (`5e98734`) membuang defender sementara dan 6f (`81e4faa`) menutup skenario
retreat/heal hero merah + hunt lintas-lane; keduanya hijau di CI (lihat run di
atas). Tidak ada sisa kode defender di `godot_rebuild/` — satu-satunya sakelar
sisi merah adalah `set_ai_enabled()`/`ai_enabled`.
Lapisan **7a** (`d43a92a`) menutup satu celah paritas nyata di sisi scene: castle
AI dulu tidak pernah naik level sendiri karena oracle men-stub
`_auto_scale_ai_castle`; sekarang jadwal sumber wave ≥4/7/10/13 → level 2/3/4/5
gratis dijalankan di `step_tick` dan diuji ulang per baris fixture. Kandidat
lanjutan yang belum dikerjakan (dipilih sesuai kedekatan ke sumber): boss hero AI
yang tampil di pertandingan dan sisa perilaku scene Python yang belum diport —
PR tetap draft sampai ada perintah pemilik repo.
Lapisan **7b** (`39b92ab`) memindahkan jitter spawn wave (uniform ±8 px lalu
offset lane) dengan stream ter-seed, jadi replay pertandingan tetap identik;
klaim lama "jitter spawn belum ada" di `MATCH_CONTRACT.md` sudah dikoreksi.
Lapisan **7c** (`3554c56`) memindahkan level-1 config ke data nyata dan
menjalankan aturan difficulty sumber (hard = 1.15/1.10/1.0), enemy scaling
minion merah, serta castle-start level biru/merah dari config.
Celah berikutnya yang tersisa di dokumen itu: kondisi boss/level/unlock asli
dan sebagian besar sistem produksi.
Status akhir sesi ini: **tidak ada sisa sub-layer item**. 5b-2/5b-3/5b-4/5b-5
dan 5e-3 semuanya hijau di CI. Berikutnya hanya kalau pemilik repo memerintahkan
pekerjaan baru (mis. boss hero AI atau kandidat item AI yang mati), dan PR tetap
draft sampai ada perintah merge. Undian 6c/6d memakai
`ai_controller.draw()`; adapter build/draft memakai RNG ter-seed dari seed
pertandingan yang sama. Catatan 6a: `towers` diteruskan eksplisit karena daftar
struktur native juga memuat nexus, sedangkan sumber hanya menyusuri `all_towers`.
Catatan alur sesi: repo pernah ter-clone ulang sehingga riwayat lokal tertinggal
dari remote — selalu `git fetch origin arena/01a0eacd-mystic-arena` dan reset ke
FETCH_HEAD sebelum commit baru; amend + push ulang hanya untuk memperbaiki CI
merah pada lapisan yang sama. Catatan 5f: `forge.gd` hanya
menganggap roster tim pemain (BLUE), dan kandidat AI tetap hidup-saja lewat
`_buy_item_for`.
Catatan runtime 5e-2: `_hero_enemy_list()` harus memakai `unit.get("max_hp")`
(null-safe) karena `UnitState` belum punya `max_hp`; akses langsung
`unit.max_hp` mematikan seluruh scene battle.

## Entity boss mini/true (layer 8a–8f, paritas kondisi match)

Port `bosses/base_boss.py` (±8 ribu baris) dimulai dengan memecahnya per lapisan.
Lapisan **8a** (`d50c86c`) memindahkan **inti entity tanpa spawn**:
`scripts/match/boss_state.gd` (subclass `UnitState`) memuat seluruh skalar
`Boss.__init__` (name/title/class, hp/damage/speed/range/attack cooldown/radius/
gold, ability + ability2 true boss, armor/MR/`resist_profile`, `damage_reduction`,
`max_damage_per_hit`, entrance timer, warna), `apply_scaling`, aturan tenacity
slow/atk_slow, store debuff `TowerDebuffMixin`, potongan stun 45%,
`eff_speed`/`eff_ability_damage`, dan ekor numerik `take_damage` (blind +
true strike, amp/shred item, mitigasi sekolah, resilience, cap anti-burst, flag
`defeated`, clear debuff). Nilai `-1` dari `take_damage` = early return sumber
(blind miss), bukan damage.

Stat **216 tipe boss** dirender `tests/boss_core_source_oracle.py` ke
`data/bosses/boss_stats.json` dari `bosses/boss_data.py` + `hero_archetypes`;
oracle mengeksekusi AST metode Boss nyata (termasuk property `speed`/
`ability_damage` dan kelas `TowerDebuffMixin`), dengan stub hanya untuk
audio/credit damage. Fixture: 216 baris stats, 18 scaling, 54 snapshot debuff,
192 damage, 48 blind, 6 defeat; `tests/boss_core_checks.gd` dijalankan
`run_all.gd` dan `validate_project.py` menuntut fixture + data tidak drift.

Lapisan **8b** (`fed2c6a`) memindahkan kondisi match boss yang sebelumnya
masih kosong: `_roll_mini_boss_schedule` (sample wave unik; Easy 20–40,
Normal/Hard 11–30), pending FIFO dan `_try_spawn_pending_mini_boss`, spawn
mini/true lewat `BossState` + scaling hard, trigger true boss saat event
`red_towers_destroyed >= 6`, serta counter tower merah yang baru di-commit
setelah pemeriksaan trigger pada tick yang sama. Reward gold/score boss,
daftar `bosses_defeated_this_match`, `unlocked_bosses`, dan free hero list saat
menang juga sudah ada di `prototype_battle.gd`. `match_source_oracle.py`
sekarang mengeksekusi metode/blok sumber asli untuk jadwal, queue, trigger,
reward dan unlock; `boss_match_checks.gd` menjalankan kontrak native.

Lapisan **8c** (`67d83e6`) memindahkan perilaku gameplay dasar boss:
`BossState` menyimpan path/waypoint, target/facing, movement cache, attack lock
serta sequence/cooldown; `prototype_battle.gd` menjalankan susur lane/chase,
target terdekat, basic hit physical dan cleave pada tick match. Boss mendapat ID
unik di registry sehingga hero, daftar aggro/skill/item dan `_deliver_hit` dapat
menargetnya tanpa memasukkannya ke jalur minion atau memberi reward dua kali.
`boss_motion_source_oracle.py` mengeksekusi AST metode `Boss` asli untuk waypoint,
facing, chase dan cleave; fixture JSON dibuat dengan `--write`, lalu
`boss_motion_checks.gd` menguji gerak, cooldown, target, damage, cleave,
registry, death dan reward-once.

Lapisan **8d** (`61184e0`) memindahkan ability/smart AI slice awal: `BossState`
menyimpan timer Q/W/E/R, active skill, rage/defense, Morgath Flux/clones,
blink/Mana Void, true-boss heal, serta damage/shield/cooldown dari source data.
`boss_ai.gd` menjalankan generic ability dan recipe Gornak, Morgath, Drakar,
dan Abaddon; `prototype_battle.gd` menurunkan cooldown/active-skill timer dan
memanggil dispatcher pada active boss. `boss_ability_source_oracle.py`
mengeksekusi AST cast/smart-AI asli untuk 18 kasus pada commit awal; fixture
dibuat dengan `--write`, `boss_ability_checks.gd` menguji parity native, dan
`validate_project.py` menuntut fixture tidak drift.

Sub-layer **8d-1** (`6ac3bc5`, run
[36742827535](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36742827535))
menambah dispatch smart AI Alchemist yang dipakai match, dengan prioritas
R/E/W/Q, timer dan active-skill window, Chemical Rage (rage/damage/heal),
Greevil's Greed AOE/kill-heal, Unstable Concoction AOE/slow, dan Acid Spray.
Commit lanjutan `1b21813` menambah Malzareth: Death Pulse, Shadow Word,
Nether Blast dan Void; commit `7cfdf7f` menambah Akashari: Sonic Scream,
Scream of Pain, Shadow Strike dan Scream; commit `937fa7e` menambah
Vorenmarr: Chaos Storm, Shadow Word, Rain of Fire dan Chaos Bolt; commit
`2b3ba1e` menambah Nyxarath: Requiem, Presence, Necromastery dan Shadowraze,
termasuk state buff/aura dan knockback source; `3057043` menambah Thalgryn:
Replicate, Morph, Waveform dan Adaptive Strike, termasuk state Morph dan
perpindahan Waveform; commit `a82b3be` menambah Syrentha: Song of the Siren,
Mirror Image, Enchanting Song dan Riptide, termasuk state eksplisit
`mirror_buff_active`/`mirror_buff_timer`, buff damage `int(base_damage * 1.4)`,
heal 12%/10% max HP, attack lock 150/120 tick, slow 0.8/0.7/0.5 dan gelombang
Riptide (line maksimum 250, lebar 70); commit `27f73f1` menambah Gravewake:
Ravage, Kraken Shell, Tidebringer dan Anchor Smash, termasuk state eksplisit
`shell_active`/`shell_timer`, radius nearby 180, AOE Tidebringer 120 yang
berpusat pada target hidup (posisi boss sebagai fallback), heal 12%/10% max HP,
attack lock 90/60 tick, slow 0.5 selama 180 tick, knockback 18px dan line
Anchor Smash (maksimum 200, lebar 60); commit `8858530` menambah Kunkka:
Torrent, Ghost Ship, X Marks the Spot dan Tide Bringer, termasuk state eksplisit
`rum_buff_active`/`rum_buff_timer` dan `x_mark_target_id`/`x_mark_timer`,
cooldown literal 720/480/300/240 yang di-hardcode boss ini, burst X Marks 120
tick (`skill_w_damage` dalam radius 120 dari mark + attack lock 60), rum buff
480 tick dengan damage `int(base_damage * 1.3)`, lintasan Ghost Ship 300×80,
line Tide Bringer 250×70, Torrent 200 berpusat target dengan attack lock 120
dan knockback 20px, serta heal 20%/15% max HP. Oracle AST mengeksekusi metode
Python asli untuk empat skenario per boss — lima untuk Kunkka karena burst
X Marks turun satu tick kemudian, mengikuti preseden flux tick Morgath; commit
`c23b6b7` menambah Razak: Firestorm, Firefly, Flame cone dan Molotov, dengan
gerbang jarak source (R saat 3+ enemy dalam 180, E saat 120 < dist < 260 dengan
dash `min(110, max(40, dist - 50))` lalu AOE 80 dari posisi BARU, W saat
dist <= 220 dengan AOE 95 di sekitar target + attack lock 45, Q saat
dist <= 260 dengan AOE 75 di sekitar target + slow 0.35 selama 120 tick) tanpa
state buff baru; commit `fcca743` menambah Kenshiro: Supremacy, Assault, Gale
dan Swiftslash, dengan helper L9 `_init_l9_timers`/`_tick_l9_timers`/`_l9_stats`/
`_l9_target`/`_l9_aoe`, gerbang source (R saat 3+ enemy dalam 200 + HP < 0.5
dengan AOE 190, W saat HP < 0.55 dengan dash `min(d, 90)` + hit closest, E saat
2+ enemy dalam 200 dengan AOE 150, Q saat dist < 140 dengan hit closest) dan
active window 70/45/55/35 tick; commit `3ccd59c` menambah Khazan: Vanishing
Execution, Spin Carnage, Leap Smash dan Chained Blade, dengan gerbang source
(R saat 2+ enemy dalam 210 + HP < 0.45 dengan AOE 210, E saat 3+ enemy dalam
210 dengan AOE 160, W saat dist > 120 dengan dash `min(d, 110)` lalu AOE 90 dari
posisi BARU, Q saat dist < 150 dengan hit closest) dan active window 75/60/50/40
tick; commit `32d03b5` menambah Wiro, Naraka, Krognarr, Raz, Vraskhan (5 boss L9,
fixture 87); commit `655fba4`+`cb760ef` menambah 41 boss L9 tersisa
(Aurethzar, Aeralith, Aurex, Nyxareva, Thalakryon, Aurelix, Aurelyssa, Vargrath,
Nazulmor, Kaeldris, Pyraklos, Velmyrth, Solvarin, Azureth, Luminar, Solara,
Pyraethis, Auroth, Morvein, Thorvak, Yamako, Ignirus, Leoric, Shirotaka,
Seiryukong, Kaelthorn, Solvanth, Xyrael, Nyxareth, Cryssalia, Kaelthar,
Morkhaera, Aurelion, Akahime, Nyxthrael, Sylvantheros, Vaelindra, Astraelion,
Morvaenthir, Thornvaegrim, Morthraxis) dengan fix heal/dash+AOE/low_target,
fixture 251. Commit `cd68825`+`b10e666` menambah final 17 non-L9
(ancient_apparition, ignis_drachorn, vhorethzir, vaerith, xirthalis,
vhyssarion, khalros, gorath, varkul, xerathis, nyzrak, zharok, pyrenth,
vokrahn, nyxara, gravefang, vhalzun) dengan state dragon_form, vortex,
shield, shukuchi, timelapse, arcane_buff, lifesteal dll; fixture menjadi
319 kasus (79 boss) dan native replay mengunci parity source. CI final
Godot 4.7.2 hijau pada run
[37020039663](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37020039663):
**1.198.332 native checks**; `validate_project.py` **5968 static checks**.

Lapisan **8e** (`c635a06`) memindahkan clock gameplay entrance/enrage:
`BossState` memajukan `anim_time`/`pulse`, menahan seluruh gerak/serangan/heal/
ability selama `entrance_timer` positif (mini 120 tick, true 180 tick), lalu
menerapkan transisi enrage sekali pada HP 40% mini atau 50% true. Modifier speed,
damage dan attack cooldown mengikuti source, termasuk floor cooldown; `enrage_pulse`
dan percepatan timer pada tick animasi genap juga dipertahankan. Oracle AST
`boss_clock_source_oracle.py` menulis fixture dengan `--write`, native
`boss_clock_checks.gd` menguji entrance, mini/true threshold, slow interaction,
one-shot transition dan gate pada match prototype.

Lapisan **8f** (`8c8787f`) memindahkan **presentasi intro/death boss saja**.
`BossState` menyediakan `entrance_presentation_state()` untuk parity aura dan
announcement; `prototype_battle.gd` menahan snapshot death FX setelah
`active_boss` dihapus, men-tick-nya secara independen sebelum cleanup registry,
dan menghitung screen shake deterministik. `prototype_view.gd` merender body,
HUD/health, entrance aura/text, enrage/true-boss aura, death flash/sparks dan
shake. `boss_presentation_source_oracle.py` mengeksekusi metode Python asli dan
menulis fixture; `boss_presentation_checks.gd` menguji entrance parity, payload
death, retirement registry dan tick FX independen.

Sistem produksi serta sisa perilaku scene/AI yang belum dipindahkan masih
belum dikerjakan. Forge player scene sudah mencakup transaksi, panel dan
background input; tidak ada panel Forge terpisah untuk hero AI di sumber.
Jangan mengklaim parity seluruh pertandingan Python.
CI Godot 4.7.2 terbaru hijau pada sub-layer `8d-1`
(final 17 non-L9 code [37020039663](https://github.com/dharmawantoxi/mystic-arena/actions/runs/37020039663));
**1.198.332 native checks**; `validate_project.py` 5968 static;
`gdformat`/`gdlint`/`gdparse` bersih.

> Pesan siap-salin: lanjutkan di branch `arena/01a0fa38-mystic-arena` (PR
> selalu draft; jangan merge tanpa perintah "merge now"). Layer **8a**
> (`d50c86c`) memindahkan inti entity + data 216 boss; layer **8b**
> (`fed2c6a`, run 36569775154) memindahkan jadwal/spawn mini–true boss,
> counter tower merah, reward dan daftar unlock; layer **8c** (`67d83e6`,
> run 36705062244) memindahkan movement, target, basic physical attack,
> cooldown/facing, cleave dan death registry tanpa reward ganda; layer **8d**
> (`61184e0`, run 36710717265) memindahkan ability/smart AI slice awal,
> generic ability, active-skill/cooldown clocks, dan true-boss heal; sub-layer
> **8d-1** (`6ac3bc5` + `1b21813` + `7cfdf7f` + `937fa7e` + `2b3ba1e` +
> `3057043` + `a82b3be` + `27f73f1` + `8858530` + `c23b6b7` + `fcca743` + `3ccd59c` + `32d03b5` + `655fba4` + `cb760ef` + `cd68825` + `b10e666`, code run 37020039663)
> menambah smart AI Alchemist, Malzareth, Akashari, Vorenmarr, Nyxarath,
> Thalgryn, Syrentha, Gravewake, Kunkka, Razak, Kenshiro, Khazan, Wiro, Naraka,
> Krognarr, Raz, Vraskhan, 41 boss L9 tersisa dan final 17 non-L9
> (ancient_apparition, ignis_drachorn, vhorethzir, vaerith, xirthalis,
> vhyssarion, khalros, gorath, varkul, xerathis, nyzrak, zharok, pyrenth,
> vokrahn, nyxara, gravefang, vhalzun); fixture oracle/native replay kini
> 319 kasus (79 boss);
> layer **8e** (`c635a06`, run 36716265830) memindahkan entrance/enrage clock
> dan gate gameplay; layer **8f** (`8c8787f`, run 36725358545) memindahkan
> presentasi intro/death boss saja, termasuk entrance aura/text, death
> flash/sparks dan screen shake. Berikutnya sistem produksi, lalu sisa
> perilaku scene/AI. Satu sub-layer per commit; pipeline gdformat -> gdlint -> gdparse ->
> validate_project.py -> commit -> push -> gh run watch.
> Sumber read-only: _core.py, _entity.py, bosses/, levels/, hero_items.py,
> minions/. Hanya ubah godot_rebuild.
