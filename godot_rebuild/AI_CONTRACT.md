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
Tidak ada item/forge, AIPlayer penuh, rebalance atau art final.

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
tetap Archer tanpa reserve (UI blue dan defender sementara red tidak diubah).
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
     **Batasan 5a:** tidak ada yang mengonsumsi getter ini di combat;
     `_on_item_changed` belum diport sehingga beli item tetap tidak mengubah
     `max_hp`/`hp`; seluruh timer (`blood_frenzy`/`ghost`/`thorn`/`gale`/
     `veil`/`guard`/`rend`/`aura_*`) ada tapi inert, jadi cabang yang
     bergantung timer selalu tertutup; `update()`,
     `notify_damage_taken()`, `on_basic_attack_hit()`, `_on_hit_common()`,
     `on_ranged_attack_hit()` dan `update_auras()` belum diport.
   - [x] **5b.** Penerapan stat HP saat equip/level: `HeroState.recalc_item_stats`
     (port `Hero._recalc_item_stats`), `apply_item_change` (port
     `_on_item_changed`: recalc + `apply_heal_amp(amp, 999999)`),
     `apply_heal_amp` + field `heal_amp_*` di `unit_state.gd` (sumber
     `_core.py:900`), heal amp dikonsumsi `heal_hp` setelah anti-heal (urutan
     setter sumber), dan `apply_level_stats` diakhiri recalc seperti sumber.
     `_buy_item_for` memanggil `apply_item_change()` setelah equip sukses.
     Oracle: 5 urutan equip/drop/level dengan `_recalc_item_stats`/
     `_apply_level_stats`/`upgrade`/`apply_heal_amp` sumber nyata.
     **Batasan 5b:** hanya HP/heal amp yang diterapkan. Damage/armor/crit/AS/
     evasion/lifesteal dst. belum dikonsumsi jalur serangan karena
     `minion_battle.gd` berada di batas 1000 baris (perlu bedah tanpa tambah
     baris); `heal_amp_timer` belum dikurangi per tick; `clear_on_death` sudah dipanggil dari hook
     kematian match (lihat 5b+).
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

## Dependensi yang wajib selesai sebelum integrasi penuh

- [x] Roster enam starter dan seluruh boss yang eligible dari level sebelumnya:
  222 kit native dengan oracle/tes telah lulus, 0 pending (lihat manifest).
  Marker prosedural bukan bukti tampilan final.
- [x] Policy pool terurut boss lalu starter, deduplikasi, source-level pertama; tidak
  memasukkan boss level saat ini. Draft starter pertama acak, boss pertama dari
  level terbaru, berikutnya berbobot source-level; tipe owned termasuk hero mati.
- [x] Policy target draft persisten sampai terbeli, reserve harga; jangan mengganti target
  hanya karena kurang gold. Hapus target ketika available kosong atau pembelian sukses.
- [ ] Transaksi red memakai ledger yang sama, reserve pada seluruh belanja non-hero,
  tanpa bonus gold. Hero spawn `RED_BASE_X-60, RED_BASE_Y+30+(count*40-40)`.
- [x] Build slot acak; jenis archer/cannon/ice/mage berbobot .35/.25/.20/.20;
  hanya adapter per aksi, belum terhubung ke scene.
- [x] Upgrade tower kills descending stabil; Lv1 path cannon/ice/archer/mage.
- [x] Transaksi upgrade tower/nexus/hero red per kandidat dengan live reserve;
  hero mati tetap eligible, batas level sumber, ledger dan counter nyata.
- [x] Urutan kandidat upgrade hero/tower kills descending dan atribusi kills sumber.
- [ ] Item/inventory/stat effects/forge dan suggestion role+range; kandidat hidup
  dengan slot kosong, kills lalu level descending; reserve dipatuhi.
  Lapisan 1-4 + 5a selesai (metadata katalog 33 item termasuk `stats` numerik,
  `suggest_item_for_hero`/`is_magic_hero`, slot `HeroItemInventory`, adapter
  `ai_items.gd::try_buy` + transaksi ledger, agregasi stat murni); sisa 5b-5f
  (penerapan stat, timer pasif/aktif, aura, proc on-hit, Forge UI).
- [x] Regen shield Lv4+ termasuk tower Lv6 dan castle shield per kandidat:
  eligibility/cost/debit, live reserve, regen/damage, upgrade dan refund sumber.
- [x] Prioritas kandidat Regen Shield kills descending stabil.
- [ ] Kontrol hero setiap tick: jalur auto-cast bersama pemain, skill counter
  berdasarkan perubahan active timer; lane ancaman maksimum (tie top/mid/bot),
  minion terdekat secara Euclidean, destination auto; fallback tower terdekat
  dengan offset 60. Jangan mengganti prioritas target dengan urutan x.
- [ ] Integrasi scene/session setelah entity loop tanpa double auto-cast,
  seeded RNG yang bisa diuji (bukan klaim stream identik Python), pause/reset/hasil.
- [ ] Ganti assertion defender lama hanya setelah perilakunya benar-benar diganti;
  pertahankan suite dan invariant wallet/slot/replay.
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
CI Godot 4.7.2 run 36455247721 hijau untuk lapisan 5f-2 (commit `de04849`):
**1.179.060 native checks**, static lokal 5711 PASS; `gdlint`/`gdformat`/`gdparse`
bersih; `minion_battle.gd` dan `hero_item_inventory.gd` tepat 1000 baris
(fixture 11.496 baris, masih di bawah 20k).

Koreksi yang perlu diingat: metadata katalog awalnya memetakan NAMA konstanta
`CATEGORY_*` -> id kategori, sehingga validasi kategori per item selalu gagal
di native (33 FAIL). Sekarang `categories` di-key oleh id kategori dengan nilai
nama konstanta sumber, dan `validate_project.py` menuntut kunci itu sama dengan
himpunan kategori yang benar-benar dipakai.

Berikutnya: Control yang menggambar panel ITEM FORGE (geometri/font/i18n) di
atas state 5f-2, lalu kontrol hero per tick dan integrasi scene. Catatan 5f: `forge.gd` hanya
menganggap roster tim pemain (BLUE), dan kandidat AI tetap hidup-saja lewat
`_buy_item_for`.
Catatan runtime 5e-2: `_hero_enemy_list()` harus memakai `unit.get("max_hp")`
(null-safe) karena `UnitState` belum punya `max_hp`; akses langsung
`unit.max_hp` mematikan seluruh scene battle.

> Pesan siap-salin: Lanjutkan di branch arena/01a0e3e4-mystic-arena (PR draft
> #294, basis main f6c4342). Lapisan 5c-2 sudah di-commit: setengah auto-trigger
> `update()` + `notify_damage_taken` + tick wiring. Berikutnya langkah 5d: port
> `update_auras` (armor/AS/guard/armor reduction aura sekutu + Scorched Earth),
> lalu 5e proc on-hit (crit/lifesteal/cleave/chain/bash/miasma/vine) dan 5f
> Forge UI + `drops_on_death`. Satu commit per lapisan, oracle exec sumber
> asli + fixture --write, tes native + validate_project.py. Sumber read-only:
> hero_items.py dan _entity.py. Hanya ubah godot_rebuild/; minion_battle.gd
> tetap 1000 baris; jangan merge tanpa perintah pengguna.
