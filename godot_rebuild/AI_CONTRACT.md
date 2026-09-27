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

## Roster 222 — 164 kit native, 58 recipe khusus pending

Metadata dan baseline konstruktor `data/ai/hero_combat_stats.json` tetap
mencakup seluruh 222 ID. Baseline angka **bukan** bukti playable. Registry
`scripts/data/hero_roster.gd` kini mengizinkan **161 kit** yang punya handler,
source oracle dan tes native. Daftar tepat semua selesai/pending dengan
harga, recipe dan blocker: [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md).

- Enam starter: Kaizen, Thorne, Grimjaw, Sylara, Vex, Zephyr.
- Delapan boss dengan recipe tersendiri: Gornak, Morgath, Drakar, Abaddon,
  Alchemist, Ancient Apparition, Nyzrak, Ignis Drachorn. Audit AST sumber membuktikan keempat
  recipe asli keenam puluh satu boss pending saling berbeda satu sama lain. Basic Morgath tetap beam/hit instan; bukan projectile generik.
- 150 boss berbagi `BossHeroSkills._fallback_cast` **di sumber asli**. Oracle
  per ID mencatat dispatch nyata, QWER, cooldown, attack, level/upgrade,
  respawn serta combat Hero/Tower. Native memakai allowlist tertutup, tidak
  menjadikannya fallback bagi 61 boss lain yang memiliki recipe berbeda.
- **58 pending** tetap ditolak dengan `kit`, saldo/roster tidak berubah,
  draft/reserve tetap. Tidak ada substitusi Kaizen atau shared kit.

Adapter `ai_recruitment.gd` tetap meneruskan draft ke transaksi sinkron
`prototype_battle.gd::_buy_ai_hero`, memakai registry/world/ledger nyata.
Oracle pembelian kini **492 transaksi** (164 × harga−1/tepat/+1), ID/posisi/
capacity/ownership dan double debit diuji. Offset first spawn Y90 tetap,
sementara Kaizen gratis red scene Y130 tetap dan tidak dihitung pembelian.
Scene tidak menyalakan AIPlayer atau pembelian otomatis.

Harga upgrade boss adalah 1,6× starter (Lv1→2 **480 G**), diuji per ID,
level 1–15 dan reserve ±1 dengan hero hidup/mati. Source damage tanpa source/
school tetap netral, berbeda dari skill yang eksplisit membawa school hero.
Mitigasi/reflect/shield, tidak memberi stun palsu pada tower, anti-heal serta
Shadow Realm/burn akhir durasi dikunci dengan objek sumber nyata.

CI Godot 4.7.2 `c029d50`: **358.305 native checks**, semua suite lama tetap.
Target masih 222; batch berikutnya Krobellus + Vhalzun (level 5) dan sisa
menurut level sumber. Catatan batch dan pesan
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
- Ini **per kandidat**, bukan loop pemilihan kandidat. Urutan kills descending
  stabil, atribusi kills sumber, policy scheduler dan wiring scene belum aktif.
  Tidak menambahkan sorting berdasarkan angka kills palsu atau team kill total.
- Method internal bukan command UI. Pause dicegah oleh session yang tidak
  mengeksekusi command/tick; tidak ada loop background atau timer baru.

## Shield berbayar per kandidat

`ai_shields.gd` memakai transaksi world untuk Regen Shield (tower Lv4–6) dan
Castle Shield (sesudah wave 10, tanpa gate Lv4). Keduanya 850 G + reserve
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

## Dependensi yang wajib selesai sebelum integrasi penuh

- [ ] Roster enam starter dan seluruh boss yang eligible dari level sebelumnya:
  baseline angka 222 tersedia; 164 kit native dengan oracle/tes telah lulus,
  58 recipe khusus masih pending (lihat manifest). Marker prosedural bukan
  bukti kit/playability atau tampilan final.
- [x] Policy pool terurut boss lalu starter, deduplikasi, source-level pertama; tidak
  memasukkan boss level saat ini. Draft starter pertama acak, boss pertama dari
  level terbaru, berikutnya berbobot source-level; tipe owned termasuk hero mati.
- [x] Policy target draft persisten sampai terbeli, reserve harga; jangan mengganti target
  hanya karena kurang gold. Hapus target ketika available kosong atau pembelian sukses.
- [ ] Transaksi red memakai ledger yang sama, reserve pada seluruh belanja non-hero,
  tanpa bonus gold. Hero spawn `RED_BASE_X-60, RED_BASE_Y+30+(count*40-40)`.
- [x] Build slot acak; jenis archer/cannon/ice/mage berbobot .35/.25/.20/.20;
  hanya adapter per aksi, belum terhubung ke scene.
- [ ] Upgrade tower kills descending stabil; Lv1 path cannon/ice/archer/mage.
- [x] Transaksi upgrade tower/nexus/hero red per kandidat dengan live reserve;
  hero mati tetap eligible, batas level sumber, ledger dan counter nyata.
- [ ] Urutan kandidat upgrade hero/tower kills descending dan atribusi kills sumber.
- [ ] Item/inventory/stat effects/forge dan suggestion role+range; kandidat hidup
  dengan slot kosong, kills lalu level descending; reserve dipatuhi.
- [x] Regen shield Lv4+ termasuk tower Lv6 dan castle shield per kandidat:
  eligibility/cost/debit, live reserve, regen/damage, upgrade dan refund sumber.
- [ ] Prioritas kandidat Regen Shield kills descending stabil.
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
