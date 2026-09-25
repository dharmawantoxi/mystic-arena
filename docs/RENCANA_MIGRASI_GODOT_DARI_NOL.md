# Mystic Arena → Godot: panduan migrasi manual dari nol

Disusun: 25 September 2026. Referensi sumber: checkout Python/Pygame pada commit `aa19c2ebee5d653741417a3a06c68b62700eeb8c`.

**Dokumen ini adalah rencana baru, bukan kelanjutan migrasi Godot sebelumnya.** Kode, scene, generator, plugin, dan hasil pengujian migrasi lama tidak dijadikan fondasi atau bukti keberhasilan.

**Pembaruan pelaksanaan:** pengguna kemudian meminta implementasi langsung di repo karena keterbatasan waktu. Fondasi baru kini dibuat di [`godot_rebuild/`](../godot_rebuild/README.md), ditargetkan untuk Windows 11 dan Godot 4.7.2. Langkah manual di bawah tetap menjadi acuan, tetapi pengguna tidak perlu membuat ulang file yang sudah disediakan. Status checkpoint: menu/input/pause, minion, dan mode tower/projectile/nexus tier 1 telah diimplementasikan; CI Godot 4.7.2 lulus 1.158 pemeriksaan native pada commit `d09ce35`. Lihat [status implementasi dan handoff](STATUS_GODOT_REBUILD.md). Ini belum migrasi gameplay penuh dan game Python tidak diubah.

## 1. Keputusan dasar

Rekomendasi awal, bisa disesuaikan sebelum mulai:

- Engine: **Godot 4.x stable, edisi standard, GDScript bertipe**. Pilih satu versi patch dan gunakan versi yang sama untuk editor, export template, serta CI. Tidak perlu mengejar versi terbaru di tengah migrasi.
- Jenis game: tetap **2D**. Jangan sekaligus mengubah desain game, balance, atau berpindah ke 3D.
- Target asumsi: Android landscape, dengan desktop untuk pengembangan. Ini mengikuti arah repo saat ini; konfirmasikan OS komputer dan perangkat Android minimum sebelum menyiapkan ekspor.
- Renderer awal: **Compatibility** untuk jangkauan perangkat. Ini pilihan awal, bukan jaminan performa; buktikan lewat build pada perangkat target.
- Ruang arena awal: **1280 × 720**, mengikuti koordinat sumber.
- Simulasi: **60 physics tick/detik**, terpisah dari render.
- Implementasi awal: GDScript native. **Tanpa bridge Python, transpiler, C++, atau GDExtension**. Pertimbangkan kode native hanya jika profiler membuktikan kebutuhan spesifik.
- Lokasi proyek baru: `godot_rebuild/` di dalam repo. Root `res://` adalah folder ini, bukan root repo Python.
- Python tetap utuh sebagai referensi perilaku, data, dan visual. Jangan dihapus setelah demo pertama berhasil.
- Tidak menambahkan fitur baru selama mengejar kesetaraan fitur yang disepakati.

**Strategi:** fondasi → satu pertandingan kecil utuh → sistem lengkap → konten bertahap → visual final → layanan platform → pengujian dan rilis.

Jangan menunggu seluruh hero selesai untuk menguji Android. Sebaliknya, jangan menganggap satu demo yang berjalan sebagai migrasi penuh.

## 2. Temuan pada sumber yang memengaruhi rencana

Ini hasil inspeksi statis, **bukan hasil menjalankan game atau audit menyeluruh terhadap bug**.

| Temuan | Dampak migrasi |
|---|---|
| `main.py` menjalankan update berbasis langkah tetap 60 Hz dengan pembatas catch-up | Memindahkan semua update ke render frame akan mengubah kecepatan permainan. |
| `_core.py` memuat konfigurasi, game, menu, input, dan UI; banyak nama modul lama dibuat lewat alias | Jangan mencari satu file Godot untuk setiap nama import Python atau membuat satu `Game.gd` raksasa. |
| `_entity.py` mencampur entitas, combat, dan visual | Pisahkan state/logika dari tampilan secara sengaja. |
| Literal data berisi 54 level, 162 mini-boss, 54 true-boss, 6 hero dasar, dan 33 item | Angka ini inventaris awal; katalog akhir harus diperiksa lagi setelah registry dan modifier runtime. Boss musuh dan boss sebagai hero bukan entitas dengan stat identik. |
| `get_all_hero_types()` menerapkan `hero_balance.py`, lalu wrapper harga unlock | Menyalin `HERO_TYPES` atau `hero_unlock` mentah saja tidak mempertahankan stat/harga final. |
| Hero, castle, boss, minion, dan peta banyak memakai rendering kode | Menyalin `assets/` tidak memindahkan seluruh tampilan game. |
| Ada `.wav` dengan header Ogg dan MP3 | Periksa format sebenarnya sebelum impor; ubah nama/konversi hanya salinan baru. |
| Ada save tiga slot, Google Play Games, top-up, dan server Python | Migrasi client engine tidak berarti server harus ditulis ulang dalam Godot. |
| Ada dokumentasi, tools, dan workflow Godot lama; tidak ditemukan `project.godot` pada checkout yang diperiksa | Jangan menjalankan workflow/converter lama untuk mengisi proyek baru. Dokumen lama tidak otomatis menggambarkan keadaan proyek baru. |

### Peta sumber → tujuan baru

Nama tujuan di bawah merupakan **usulan yang belum dibuat**.

| Sumber Python yang dibaca | Tujuan Godot baru |
|---|---|
| `main.py` | `App.tscn`, navigasi scene, pause dan lifecycle |
| `_core.py`: konfigurasi, `Game`, ekonomi | resources data, `MatchController.gd`, `EconomySystem.gd`, `WaveSystem.gd` |
| `_core.py`: `Menu`, input, UI, settings | scene `Control`, command input, layanan settings |
| `_entity.py`: `Bullet`, `Tower`, `Castle`, `Hero`, `Minion`, `AIPlayer` | scene entitas + sistem combat dan AI terpisah |
| `levels/level_data.py` | resource level, urutan unlock dan reward |
| `bosses/boss_data.py`, `bosses/base_boss.py`, `bosses/level*.py` | data boss, perilaku khusus, spawn director, visual boss |
| `hero_archetypes.py`, `hero_archetypes.json`, `hero_balance.py` | katalog final yang tervalidasi, aturan archetype dan balance |
| `hero_skills/_bundle.py` | skill dan status effect |
| `hero_items.py` | data item, inventory, modifier stat, toko |
| `tactical_commands.py` | command/hold/release dan prioritas perilaku hero |
| `_render.py`, `map_components/`, `heroes/`, `minions/`, `towers/`, `lighting.py` | visual 2D, animasi, peta, VFX dan lighting |
| `_system.py` | spatial query, audio, save; profiling Godot menggantikan sebagian utilitas performa |
| `ui_theme.py`, `ui_components/`, `localization.py`, `splash_screen.py` | theme, layout, localization, splash |
| `mobile/touch.py`, `mobile/hud.py`, `mobile/sidepanel.py`, `mobile/platform_utils.py` | kontrol sentuh, HUD responsif, safe area dan lifecycle |
| `storage_paths.py`, `_system.py:SaveManager`, `mobile/cloud_save.py`, `src/` | penyimpanan `user://`, adapter migrasi save, integrasi platform baru |
| `server/`, `topup_currency.py`, `topup_voucher.py` | kontrak backend dan client HTTP; server tetap terpisah |

## 3. Aturan agar bug tidak ikut terbawa

1. **Sumber adalah spesifikasi yang harus diperiksa, bukan dianggap bebas bug.** Jika perilaku Python salah, tulis keputusan perbaikannya dan tes perilaku yang diinginkan. Jangan diam-diam mengubahnya ketika porting.
2. Satu tahap harus memiliki hasil nyata dan tes lulus sebelum tahap berikutnya.
3. Pisahkan kesetaraan **data**, **aturan permainan**, **visual**, dan **platform**. Lulus data saja tidak cukup.
4. Mulai dengan bentuk sederhana untuk membuktikan gameplay. Tetapi lakukan percobaan visual satu hero sejak awal agar masalah aset/prosedural tidak ditemukan terlambat.
5. Satu serangan menghasilkan damage dari satu jalur otoritatif. Animasi, suara, partikel, dan HUD hanya menanggapi hasilnya.
6. Jangan mencampur satuan tick, detik, piksel/tick, piksel/detik, dan milidetik tanpa nama/konversi eksplisit.
7. Jangan menerapkan modifier balance, armor, bonus item, atau multiplier level dua kali.
8. Jangan menyembunyikan error dengan fallback yang seolah berhasil. Data wajib yang tidak ada harus terlihat jelas sebagai kegagalan saat development.
9. Jaga ID hero, boss, item, dan level tetap stabil untuk save dan referensi data.
10. Tidak ada optimasi besar sebelum pengukuran; tidak ada perluasan konten saat core combat masih rusak.

## 4. Tahap 0 — Kunci referensi dan ruang lingkup

### Langkah manual

1. Simpan salinan aman repo, aset lokal yang tidak ikut Git, dan save pemain. Backup keystore secara terpisah jika sudah pernah rilis Android. Jangan menaruh save nyata, key, atau kredensial di Git.
2. Jangan menghapus hasil migrasi lama. Cukup jangan dibuka, diimpor, atau dijadikan dependency proyek baru.
3. Pada sesi Arena ini, tetap gunakan branch `arena/01a0d776-mystic-arena`. Tidak perlu membuat atau berpindah branch.
4. Jalankan sumber Python di komputer. Dari root repo:

   ```text
   python -m venv .venv
   ```

   Aktivasi Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   Aktivasi Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

   Kemudian:

   ```text
   python -m pip install pygame-ce
   python main.py
   ```

   Jika terminal memakai `python3`, sesuaikan nama executable. Jika ada dependency lain yang benar-benar dibutuhkan, catat dan pasang berdasarkan error/import sumber; jangan menjalankan converter Godot lama sebagai solusi.
5. Catat versi Python dan pygame-ce yang berhasil. Jika baseline tidak jalan, selesaikan identifikasi masalah baseline dulu; jangan mengklaim hasilnya sebagai acuan tervalidasi.
6. Rekam sesi pendek: menu → pilih level → bangun tower → beli hero → skill → wave/boss → menang/kalah → kembali menu. Rekam juga satu pertandingan yang lebih ramai.
7. Buat daftar fitur. Setiap fitur memiliki kolom: `ID`, sumber Python, perilaku yang diharapkan, status port, tes, dan bukti.
8. Catat bug sumber dalam daftar terpisah: `dipertahankan sementara`, `diperbaiki dengan spesifikasi`, atau `butuh keputusan`.
9. Tetapkan target perangkat, pilihan visual, serta apakah save lama dan rilis Android lama harus tetap kompatibel.

Contoh matriks:

| ID | Fitur | Sumber | Hasil yang wajib | Status |
|---|---|---|---|---|
| C-01 | Damage | `_entity.py`, `hero_archetypes.py` | Formula, rounding, armor/resist sesuai fixture | Belum |
| B-01 | True boss | `_core.py`, tes spawn Python | Counter kehancuran tower benar, spawn satu kali | Belum |
| S-01 | Save slot | `_system.py` | Slot tidak saling menimpa | Belum |
| I-01 | Tactical hold | `tactical_commands.py`, `main.py` | Release/focus loss menghentikan hold | Belum |

**Syarat lulus:** baseline yang bisa dijalankan, daftar fitur lengkap, keputusan ruang lingkup, dan rekaman referensi tersedia. Belum perlu satu baris kode Godot.

## 5. Tahap 1 — Buat proyek Godot yang benar-benar kosong

### Klik dan pengaturan awal

1. Pasang Godot standard versi stable pilihanmu. Catat versi lengkapnya.
2. Buka **Project Manager → Create/New Project**.
3. Nama: `Mystic Arena Rebuild`.
4. Path: `<repo>/godot_rebuild`. Pilih renderer **Compatibility**.
5. Jika tersedia pilihan version-control metadata, pilih tanpa membuat repo Git baru; folder ini sudah berada di dalam repo.
6. Buka **Project → Project Settings**. Nama label dapat sedikit berbeda menurut versi Godot:
   - Display / Window / Size: viewport width `1280`, height `720`.
   - Window override awal: `1280 × 720` atau lebih kecil dengan rasio sama.
   - Stretch Mode: `canvas_items`.
   - Stretch Aspect: `keep` untuk baseline; widescreen diperluas setelah transform input benar.
   - Physics / Common / Physics Ticks Per Second: `60`.
   - Orientasi handheld: landscape sesuai opsi versi yang dipilih.
7. Tambahkan Input Map: `select`, `command_move`, `skill_q`, `skill_w`, `skill_e`, `skill_r`, `pause`, `open_shop`, `cancel_targeting`.
   - Bind Q/W/E/R untuk skill dan Esc untuk pause.
   - Binding mouse/keyboard lain harus mengikuti kontrol sumber yang sudah dicatat; jangan menebak klik kiri/kanan.
   - Touch nantinya mengirim command yang sama, bukan membuat logika combat kedua.
8. Buat folder dasar berikut melalui panel FileSystem. Tidak perlu membuat semua script sekaligus:

   ```text
   godot_rebuild/
     project.godot
     app/
     scenes/
       menu/
       match/
       entities/
       ui/
       effects/
     scripts/
       data/
       simulation/
       entities/
       combat/
       input/
       services/
     data/
       levels/
       heroes/
       bosses/
       towers/
       items/
     assets/
       fonts/
       audio/
       sprites/
       maps/
     tests/
       fixtures/
       scenes/
   ```
9. Buat scene root `Node` bernama `App`; simpan `app/App.tscn`.
10. Tambahkan child `Control` bernama `ScreenRoot`, layout **Full Rect**.
11. Buat `scenes/menu/MainMenu.tscn` dengan root `Control`, Full Rect; isi `CenterContainer → VBoxContainer → Label + Button`. Label judul proyek, button bernama `PlayButton`.
12. Buat `scenes/match/Match.tscn` dengan root `Node2D`. Buat arena sementara dari bentuk sederhana, belum memakai renderer Python.
13. Pasang `App.tscn` sebagai Main Scene. Buat navigasi sederhana dari menu ke match dan kembali; instansiasi scene tampilan sebagai child `ScreenRoot` dan bebaskan scene tampilan sebelumnya. Hubungkan signal tombol ke pengendali navigasi, bukan ke sistem combat.
14. Pastikan scene menu/match tidak tertinggal aktif setelah pindah. Cek tab Remote saat game berjalan.
15. Tambahkan aturan ignore untuk folder baru **ketika proyek dibuat**:

   ```gitignore
   godot_rebuild/.godot/
   godot_rebuild/exports/
   godot_rebuild/android/build/
   ```

   Jangan mengabaikan semua `.uid`/`.import` secara massal: metadata aset dan UID yang diperlukan harus mengikuti kebijakan versi Godot yang dipakai. Jangan commit cache, build, atau signing secret.

**Syarat lulus:** F6 untuk scene yang diuji dan F5 untuk aplikasi berhasil; menu ↔ match 10 kali tanpa node yang terus bertambah, script error, atau input ganda. Resize tidak menggeser klik dari targetnya.

### Pemeriksaan Android paling awal

Pasang export template **versi sama**, lalu Android SDK/JDK sesuai dokumentasi versi Godot terpilih. Buat export preset Android debug, landscape, dan package ID development terpisah agar tidak menimpa aplikasi lama. Ekspor aplikasi kosong dan jalankan pada HP.

Tidak perlu cloud save atau pembayaran pada langkah ini. Tujuannya mendeteksi masalah renderer, template, tooling, instalasi, dan orientasi sebelum terlalu banyak kode dibuat.

## 6. Tahap 2 — Susun arsitektur, satuan, dan kontrak data

### 2A. Pisahkan pemilik tanggung jawab

Gunakan rancangan awal berikut; jangan membuat framework yang lebih rumit dari kebutuhan:

```text
App
└── ScreenRoot
    └── Match
        ├── World (Node2D)
        │   ├── Map
        │   ├── GroundEffects
        │   ├── Entities
        │   ├── Projectiles
        │   └── ForegroundEffects
        ├── MatchController
        └── HUD (CanvasLayer)
```

- `MatchController`: state pertandingan, tick dan urutan sistem.
- `WaveSystem`: jadwal spawn.
- `CombatSystem`: validasi dan resolusi hit.
- `EconomySystem`: gold, beli, jual, upgrade.
- `BossDirector`: aturan spawn boss dan flag satu kali.
- `MatchInput`: ubah input menjadi command; bukan menghitung damage.
- Entitas: ID, team, posisi, state, stat, target.
- Visual entitas: anak node yang membaca state dan event hasil simulasi.
- Layanan lintas scene seperti settings, save, audio boleh menjadi Autoload. Unit, daftar target, dan state pertandingan jangan dijadikan global permanen.

Untuk minion mengikuti lane, mulai dengan `Node2D` dan waypoint eksplisit. Tambahkan `Area2D` untuk seleksi/hitbox bila perlu. Gunakan `CharacterBody2D` hanya jika benar-benar perlu tabrakan fisik. Jangan mengganti aturan pergerakan menjadi navigation mesh sebelum memahami rute sumber.

### 2B. Pilih satuan awal: pertahankan tick sumber

Untuk mengurangi perubahan sekaligus, rekomendasi awal adalah mempertahankan **tick integer** di simulasi dan memanggil satu `step_tick()` dari `_physics_process()` pada 60 Hz.

- Cooldown 180 tick tetap 180 tick; label UI menampilkannya sebagai `180 / 60.0 = 3 detik`.
- Wave interval 1500 tick tetap 1500 tick = 25 detik.
- Speed sumber dalam piksel/tick dipakai satu kali per tick.
- Jangan mengalikan nilai piksel/tick dengan `delta` tanpa mengubah satuan dahulu.
- Render `_process()` hanya untuk tampilan/interpolasi. Jangan mengurangi cooldown atau mengeluarkan damage di sana.
- Pause menghentikan simulasi, tetapi UI resume tetap berjalan. Atur process mode menu pause secara eksplisit.

Jika kelak mengonversi ke detik, lakukan sebagai perubahan terpisah: durasi `tick / 60`, speed dan regen per-tick `× 60`. Jangan konversi jarak/range/HP/gold. Tetapkan aturan pembulatan dan buat tes batas tick sebelum mengganti.

Fixed timestep mengurangi ketergantungan pada render FPS; ia **tidak menjamin** simulasi tetap real-time pada perangkat yang tidak mampu mengejar tick. Ukur kondisi overload dan jangan menggandakan loop catch-up Python di atas physics loop Godot tanpa alasan.

### 2C. Definisikan data

1. Buat resource bertipe untuk definisi level, unit, tower, skill, dan item (`Resource`/`.tres`). Gunakan JSON untuk fixture/snapshot pembanding bila lebih mudah.
2. Data definisi hanya dibaca. HP saat ini, target, cooldown, inventory, dan buff harus menjadi state per instance—bukan mutable shared resource.
3. Gunakan nama satuan eksplisit, misalnya `attack_cooldown_ticks`, `move_speed_px_per_tick`, `attack_range_px`.
4. Simpan `schema_version`, ID stabil, dan asal nilai (mentah atau final).
5. Awalnya masukkan manual **satu level, satu minion, satu tower, satu hero**. Jangan menyalin semua data dulu.
6. Untuk katalog hero, putuskan satu jalur:
   - Rekomendasi awal: snapshot stat katalog final setelah balance, lalu Godot **tidak** mengulang balance pass tersebut.
   - Alternatif kemudian: port algoritma balance dan buktikan keluarannya sama.
7. Tetap audit modifier setelah katalog dibentuk: level hero, buff jenis serangan, equipment, status, dan difficulty. Snapshot katalog bukan otomatis stat final setiap instance.
8. Saat JSON digunakan, validasi tipe numerik, `null`, enum, warna 0–255 vs 0–1, tuple/list, dan key angka. Jadwal `mini_bosses` dengan key integer Python dapat berubah menjadi string JSON; lebih aman simpan daftar `{wave, boss_id}` yang diurutkan.
9. Buat validator: ID unik, referensi ada, angka wajib valid, cooldown/range masuk akal, level dan dependensi unlock tidak putus.

**Syarat lulus:** data contoh termuat tanpa fallback diam-diam; dua entitas dari definisi sama memiliki HP/cooldown independen; 600 tick tanpa pause setara 10 detik simulasi, dalam kapasitas perangkat.

## 7. Tahap 3 — Bangun fondasi arena, gerak, dan seleksi

1. Baca waypoint/lane, posisi base, tower, dan build slot pada sumber. Pisahkan koordinat dunia dari koordinat panel/UI.
2. Buat `Map.tscn` sederhana dengan penanda lane dan slot; tidak perlu dekorasi final.
3. Buat minion placeholder dengan team, ID, HP, speed, dan waypoint index.
4. Spawn satu minion biru dan satu merah. Pastikan arah perjalanan sesuai sumber.
5. Tambahkan pergerakan, berhenti ketika perlu, dan pemilihan target sederhana yang konsisten.
6. Tambahkan seleksi dan command melalui satu adapter input. Gunakan transform viewport/canvas Godot, bukan rumus skala hard-coded yang berbeda di setiap tombol.
7. Klik HUD tidak boleh menembus ke dunia. Terapkan `mouse_filter` dan routing input yang tepat; input dunia hanya diproses jika UI tidak mengonsumsinya.
8. Tetapkan ID dan urutan iterasi entitas yang stabil. Target yang mati/keluar scene harus dilepas dengan aman.

**Syarat lulus:** rute benar pada jendela kecil/besar; seleksi tepat; unit tidak menembus akhir lane, berputar tanpa sebab, atau mengejar target yang sudah dihapus.

## 8. Tahap 4 — Buat combat minimum yang dapat dipercaya

1. Buat stat HP, damage, range, attack cooldown, armor/resist sesuai bagian sumber yang sedang dipindahkan.
2. Tetapkan state dasar: idle, move, attack/windup, recovery, dead. Skill/CC ditambahkan kemudian.
3. Buat request hit dengan field jelas: attacker ID/team, target ID, attack ID, amount, damage school, jenis delivery, dan flags yang diperlukan.
4. Jangan menggabungkan `damage_type` legacy, physical/magic school, dan projectile/melee ke satu enum tanpa memetakan artinya. Baca `resolve_damage_school()` dan call site terkait.
5. Tulis urutan perhitungan **sesuai sumber yang diaudit**, termasuk shield, armor/resist, reduksi khusus boss, cap, on-hit, HP, dan reward. Jangan mengasumsikan urutan yang umum dipakai game lain.
6. Pastikan death dan reward hanya terjadi sekali, walaupun dua serangan mengenai target pada tick yang sama.
7. Tambahkan projectile: hit sekali, umur maksimum, target mati, dan pembersihan node. Jangan membiarkan animasi projectile juga memanggil damage lagi.
8. Tambahkan overlay debug: tick, ID target, HP, cooldown, jumlah entitas, jumlah hit. Overlay bukan dependency gameplay.
9. Uji kasus kecil dengan hasil numerik yang dihitung dari sumber: tanpa armor, armor/resist, shield, serangan fisik/sihir, target mati, dan serangan berbarengan.

**Syarat lulus:** pada input fixture yang sama, HP, hit count, tick attack, death, dan reward sesuai ekspektasi. Mematikan seluruh visual/FX tidak mengubah hasil combat.

## 9. Tahap 5 — Selesaikan satu pertandingan kecil utuh

Ini **vertical slice**: potongan kecil yang bisa dimainkan dari mulai sampai selesai. Bukan seluruh level 1 final.

1. Tambahkan kedua castle/nexus, satu jenis tower, dan satu jenis minion.
2. Tambahkan gold awal, pendapatan pasif, build slot, beli/jual/upgrade tower minimum. Gunakan `compute_starting_gold()` dan `compute_gold_per_second()` sebagai referensi perilaku, bukan hanya konstanta paling atas.
3. Tambahkan jadwal wave serta jeda spawn. Gunakan skenario pendek khusus tes tanpa menimpa data level produksi.
4. Tambahkan satu hero: gerak/target/basic attack dan satu skill yang paling sederhana setelah audit kit. Jangan mulai dari kit paling kompleks hanya karena visualnya menarik.
5. Buat lawan sederhana agar loop dapat dimainkan; AI penuh menyusul.
6. Tambahkan HUD HP/gold/wave, pause/resume, restart, dan hasil menang/kalah.
7. Pastikan kondisi menang/kalah berasal dari aturan sumber; mode debug untuk memicu hasil hanya digunakan saat development.
8. Terapkan cleanup: timer, projectile, target, signal, pending command, audio loop, dan reference pertandingan lama.
9. Tambahkan satu autosave progres percobaan ke lokasi **development**, belum menyentuh save pemain asli.
10. Mainkan, restart, dan kembali menu berulang kali; coba pause saat ada projectile dan skill.

**Syarat lulus:** menu → match → menang/kalah → menu → match baru bekerja minimal 10 siklus; tidak ada reward ganda, state sisa, error debugger, atau peningkatan jumlah node yang tidak terkendali. Build Android slice juga harus bisa dimainkan.

**Checkpoint penting:** bila tahap ini belum stabil, jangan mulai memindahkan puluhan boss.

## 10. Tahap 6 — Lengkapi sistem inti, bukan jumlah konten dulu

Urutan yang disarankan:

1. Seluruh tipe/upgrade tower; shield, regen, debuff, jual, dan slot build.
2. Upgrade castle/nexus, komposisi wave, shield dan aturan ekonominya.
3. Targeting dan AI penuh: prioritas target, bangun/upgrade, beli hero, penggunaan skill, batas jumlah unit, dan difficulty.
4. Hero level, respawn jika ada dalam spesifikasi, batas kepemilikan, dan pergantian hero terpilih.
5. Status effect: durasi, stacking/refresh, stun, slow, silence, damage-over-time, shield dan dispel sesuai kit yang ada.
6. Framework skill: target unit/point/self, validasi range, biaya, cooldown, cancel, channel, projectile/AOE/summon sesuai kebutuhan nyata.
7. Tactical command: tap, hold, release, prioritas terhadap AI, batal ketika mati/pause/focus hilang.
8. Inventory dan item: validasi uang/slot, transaksi beli/jual, stat modifier, on-hit, aura, dan pending delivery bila dipakai sumber.
9. Progression: level unlock, hero unlock, reward menang pertama/replay/kalah dan achievement yang ada dalam inventaris fitur.

Untuk setiap sistem: port satu perilaku → tes positif → tes gagal/batal → tes kombinasi → tes restart. Contoh item: beli berhasil, gold tidak cukup, slot penuh, jual, ganti hero terpilih, pembelian saat hero mati, aura hilang saat pemilik mati.

**Syarat lulus:** semua sistem yang akan dipakai konten punya kontrak dan tes. Tidak ada script hero/item yang mengubah gold atau HP lewat jalur samping tanpa validasi.

## 11. Tahap 7 — Migrasikan konten secara bertahap

### Urutan batch

1. Selesaikan enam hero dasar satu per satu: Kaizen, Grimjaw, Sylara, Thorne, Vex, Zephyr. Urutan pengerjaan boleh berdasarkan kompleksitas, bukan urutan daftar.
2. Lengkapi level 1: mini-boss Gornak, Morgath, Drakar dan true-boss Abaddon menurut konfigurasi aktif sumber.
3. Selesaikan beberapa level representatif dengan tema/skill berbeda.
4. Lanjutkan batch kecil, misalnya 3–5 level, hanya setelah batch sebelumnya lulus.
5. Teruskan sampai 54 level, semua mini/true-boss, varian boss-hero yang tersedia, tower, minion, dan 33 item awal tervalidasi terhadap inventaris final.

### Checklist per hero/boss

- [ ] ID, nama, team dan kategori benar.
- [ ] Stat katalog, scaling, harga, unlock dan role musuh vs hero benar.
- [ ] Basic attack: target, range, school, windup dan cooldown benar.
- [ ] Q/W/E/R: syarat, biaya, cooldown, target, efek dan cancel benar.
- [ ] Perilaku ketika stun/silence/mati/target hilang benar.
- [ ] Interaksi dengan tower, minion, hero, shield dan boss diperiksa.
- [ ] AI dan fase boss yang khusus tidak digantikan oleh stat generik.
- [ ] Death/despawn tidak meninggalkan summon, aura atau reference.
- [ ] Visual/suara penting punya status eksplisit: sementara atau final.

### Regresi khusus yang jangan terlewat

`tools/test_true_boss_spawn.py` mendeskripsikan aturan sumber: true-boss muncul setelah **6 tower merah dihancurkan**, tanpa harus menunggu wave 5. Hitung dari event kematian tower, bukan selisih jumlah tower hidup; AI bisa membangun lagi. Validasi juga satu kali spawn dan boss ID sesuai level. Perubahan timing tick dari sumber harus dicatat jika disengaja.

Gunakan data level aktif untuk jadwal mini-boss, jangan satu jadwal global untuk semua level. Level 1 pada sumber memiliki konfigurasi tersendiri.

**Syarat lulus per batch:** seluruh referensi data valid, smoke test tiap level berhasil memuat/spawn/selesai, dan perilaku khusus yang baru mendapat tes. Kemiripan stat tidak berarti dua boss bisa dianggap sudah terport.

## 12. Tahap 8 — Migrasikan visual dan audio secara terpisah

Lakukan **uji visual satu hero pada tahap awal**, tetapi produksi visual penuh setelah alur simulasi stabil. Targetnya menjaga identitas tampilan tanpa membawa ketergantungan renderer Pygame.

### Pilihan visual

| Pendekatan | Cocok untuk | Risiko |
|---|---|---|
| Gambar ulang procedural dengan `_draw()`, `Polygon2D`, rig 2D | Siluet, rig dan warna dinamis | Banyak kode harus ditulis ulang dan diukur |
| Sprite sheet/atlas dari renderer sumber yang direkam | Pose yang stabil dan ingin mempertahankan tampilan | Memori, jumlah arah/pose, pivot, dan FX dinamis |
| Hybrid | Sprite/rig tubuh + FX Godot terpisah | Perlu kontrak posisi senjata, arah dan timing |

**Rekomendasi: hybrid**, tetapi ini keputusan produksi, bukan asumsi bahwa semua renderer dapat otomatis di-bake. Jika wajib tetap 100% procedural, pilih jalur pertama dan perhitungkan pekerjaan visual yang lebih besar.

### Langkah manual

1. Ambil satu hero representatif. Catat pose, arah, dimensi, pivot kaki, origin senjata, layer dan timing impact.
2. Buat idle, move, attack, hurt/death dan pose skill yang benar-benar diperlukan. Bandingkan dengan rekaman sumber.
3. Pisahkan body, shadow, projectile, aura, trail dan impact. Jangan ikut memanggang projectile ke sprite lalu menggambarnya lagi di scene.
4. Kaitkan animasi/VFX ke tick/event combat, tetapi jangan menjadikan animation finished sebagai satu-satunya penentu damage.
5. Tetapkan urutan render: tanah → efek tanah → unit → projectile/efek atas → HUD. Gunakan z-index/Y-sort sesuai kebutuhan, jangan membiarkan arena menutup UI.
6. Pilih filter texture sesuai jenis aset. Pixel art biasanya nearest; jangan memaksakan filter yang sama untuk seluruh UI dan efek halus.
7. Pindahkan peta/tema; dekorasi tidak boleh mengubah jalur atau hitbox yang sudah lolos tes.
8. Pindahkan UI dengan `Control`, container, anchor dan theme. Jangan menggambar ulang setiap label/tombol dengan `_draw()`.
9. Salin aset yang diperlukan ke `godot_rebuild/assets/`. Catat lisensi dan nama asal. Jangan menganggap gambar review sebagai sprite gameplay siap pakai.
10. Periksa format audio: pada checkout ini `ambient_forest.wav` berheader MP3/ID3; `minion_hit.wav`, `ui_buy.wav`, `ui_click.wav`, `ui_error.wav`, `ui_sell.wav`, `ui_upgrade.wav`, `victory.wav` berheader Ogg. Beri ekstensi benar pada **salinan Godot** dan perbarui manifest/path pemakainya; jangan mengganti sumber Python.
11. Buat bus Master/Music/SFX/UI dan volume yang tersimpan. Batasi suara tempur serentak, tangani pause/background.
12. Setelah satu karakter lulus visual, terapkan pola produksi ke batch lainnya. Simpan aset besar dan hasil capture sementara sesuai aturan penyimpanan repo, jangan commit ribuan gambar review yang tidak digunakan.

**Syarat lulus:** siluet, arah, anchor, timing serangan, readability tim, UI dan suara sesuai referensi/keputusan desain. Tidak ada impact/projectile ganda atau ketergantungan damage pada FPS render.

## 13. Tahap 9 — Input mobile, layout dan lifecycle

1. Semua input desktop/touch harus menghasilkan command permainan yang sama.
2. Petakan touch ID secara terpisah untuk gesture/hold; jangan hanya satu boolean global.
3. Uji tekan dua tombol atau select sambil command, drag melewati UI, release di luar tombol, dan gesture dibatalkan.
4. Hindari event ganda akibat emulasi mouse dari touch. Tentukan satu jalur yang menangani tiap interaksi.
5. Uji targeting skill: preview, konfirmasi, cancel, target mati, pause saat memilih, dan gold/mana berubah sebelum konfirmasi jika relevan.
6. Mulai dari stretch `keep`; lanjutkan desain 18:9/20:9, safe area/notch dan panel samping tanpa mengubah skala dunia secara tidak sengaja.
7. Pada background/focus loss: hentikan input hold, pause sesuai spesifikasi, hentikan suara yang perlu, dan simpan pada batas aman. Jangan mengandalkan callback quit untuk satu-satunya save.
8. Saat resume, jangan mengejar seluruh waktu selama aplikasi berada di background. Reset pending input dan pastikan cooldown mengikuti aturan pause yang disepakati.
9. Android Back membuka pause/kembali secara terkontrol, bukan keluar mendadak dari transaksi atau dialog.
10. Uji pada HP nyata. Emulasi mouse di editor tidak membuktikan multi-touch dan lifecycle Android.

**Syarat lulus:** 10 siklus background/resume, spam tap, cancel gesture, dan pergantian scene tidak membuat skill/tactical hold macet atau pembelian ganda.

## 14. Tahap 10 — Save, kompatibilitas, cloud, dan top-up

### A. Save lokal yang aman

1. Inventaris semua field save sumber: progres level, hero unlock, currency, slot, settings, metadata, penanda reward dan transaksi yang relevan.
2. Buat schema berversi dan validasi batas nilai/ID.
3. Simpan di `user://`, bukan `res://`.
4. Gunakan file sementara + validasi + penggantian file dengan penanganan error dan backup terakhir yang valid.
5. Uji file hilang, kosong, rusak, versi lebih lama/lebih baru, nilai tidak valid, gagal tulis, dan aplikasi ditutup paksa.
6. Bedakan progres permanen dari state pertandingan sementara; jangan menjanjikan resume di tengah pertandingan jika sumber/spesifikasi tidak menyediakannya.

### B. Mengimpor save Python

1. Jika kompatibilitas diperlukan, buat adapter **satu arah**, bukan membaca/menulis file Python langsung dari semua sistem Godot.
2. Backup dahulu, validasi dahulu, lalu tulis format baru. Ulangi impor tanpa menggandakan currency/reward.
3. Berkas private Android lama tidak otomatis berada di `user://` Godot. Tentukan jalur migrasi: update package yang sama dengan adapter storage platform, cloud restore, atau ekspor/impor eksplisit.
4. Untuk meng-update aplikasi terbitan lama, package ID dan identitas signing yang sesuai harus dipertahankan. Build development terpisah tidak membuktikan skenario upgrade tersebut.
5. Uji update di atas versi lama dengan save nyata yang disamarkan; jangan uninstall dahulu karena itu bukan uji update.

### C. Cloud save

`mobile/cloud_save.py` menyatakan Google Play Games Saved Games sebagai sumber progres saat tersedia, dengan lokal sebagai working copy. Jangan diam-diam mengubah kontrak menjadi local-only untuk rilis penuh.

1. Buat interface cloud terlebih dahulu: unavailable, signed-out, loading, success, conflict, error.
2. Gunakan stub offline saat mengembangkan core. Stub bukan implementasi cloud selesai.
3. Implementasikan integrasi Godot/Android baru menggunakan plugin yang kompatibel atau bridge baru; Java/p4a lama tidak otomatis terpasang di Godot.
4. Tentukan konflik antar perangkat secara eksplisit. Jangan memilih semua nilai maksimum karena bisa menggandakan reward atau membatalkan pengeluaran.
5. Uji cancel sign-in, timeout, offline, dua perangkat, account switch, payload rusak, retry, dan restore versi lama.

### D. Top-up/backend

1. Pertahankan backend Python terpisah jika kontraknya sesuai. Audit endpoint di `server/README.md` dan implementasi `server/app.py` sebelum integrasi.
2. Client Godot menggunakan HTTP asynchronous, error/timeout state dan retry terkendali, bukan memblokir loop game.
3. Gunakan sandbox/mock hanya untuk pengujian. Jangan menganggap status sukses dari UI/mock sebagai bukti pembayaran.
4. Server harus memverifikasi pembayaran dan menjaga idempotensi redemption/credit. Client tidak menyimpan server key atau menentukan sendiri pembayaran lunas.
5. Uji webhook/status/redeem berulang, app tutup setelah bayar, koneksi putus, serta klaim ulang dari slot/perangkat lain.
6. Sebelum publikasi, periksa kebijakan pembayaran store yang berlaku untuk barang digital dan negara distribusi. Jangan berasumsi alur Midtrans lama otomatis boleh untuk semua distribusi Play Store.

**Syarat lulus:** tidak ada kehilangan progres, overwrite slot tak sengaja, credit ganda, atau secret dalam client/repo. Fitur platform yang ditunda harus tercatat jelas sebagai scope rilis, bukan diberi status selesai.

## 15. Tahap 11 — Pengujian, regresi, dan performa

Pengujian dimulai sejak tahap 0. Tahap ini menggabungkan semua hasil menjadi bukti kesiapan rilis.

### Lapisan pengujian

| Lapisan | Yang diperiksa |
|---|---|
| Validator data | Kelengkapan ID/referensi, schema, angka, unlock graph |
| Unit test simulasi | Damage, cooldown, ekonomi, stacking, reward, targeting |
| Integration | Skill + item + status, wave + boss, UI command + simulasi |
| Lifecycle | Pause, restart, pindah scene, background, node cleanup |
| Visual/audio | Siluet, timing, layering, resize, missing asset, suara ganda |
| Platform | Android build, touch, storage, upgrade, cloud, top-up |
| Soak/performance | Banyak entitas/FX, match berulang, konsumsi memori dan suhu |

### Perbandingan dengan Python

1. Tulis fixture kecil: data awal, urutan command per tick, dan hasil yang diharapkan.
2. Rekam hasil dari fungsi/simulasi Python yang relevan, setelah memastikan tidak masuk kasus bug yang sudah didokumentasikan.
3. Jalankan fixture yang sama pada Godot. Bandingkan angka penting dan urutan event, bukan hanya screenshot.
4. Uang, unlock, jumlah spawn/hit/death harus exact. Float boleh memakai toleransi **yang ditulis sebelum tes**, bukan dilebarkan sampai lulus.
5. Jangan berharap seed angka yang sama di Python dan Godot menghasilkan RNG identik. Untuk tes kesetaraan, berikan urutan hasil random yang sama atau gunakan algoritma RNG yang sengaja disamakan. Pisahkan RNG gameplay dari RNG visual.
6. Tentukan urutan target/update dan tie-break berdasarkan ID stabil. Perbedaan urutan iterasi dapat mengubah siapa yang mati lebih dulu.
7. Jika perbedaan disengaja, tulis alasan dan expected result baru, jangan tandai otomatis sebagai parity.

Tes Python yang berguna untuk dibaca sebagai spesifikasi antara lain `tools/test_damage_school.py`, `tools/test_damage_school_integration.py`, `tools/test_true_boss_spawn.py`, `tools/test_build_slots.py`, `tools/test_sell_tower.py`, `tools/test_tactical_hold.py`, `tools/test_item_onhit_bugfix.py`, `tools/test_storage_paths.py`, dan `tools/test_cloud_save.py`. Audit cara menjalankan masing-masing; sebagian script mandiri, sebagian memakai pytest. **Tes `test_godot_*` dan generator migrasi lama tidak menjadi fondasi baru.**

Contoh pemeriksaan engine setelah Godot dipasang dan proyek/tes baru dibuat:

```bash
godot --headless --path godot_rebuild --editor --import
# Hanya jika tests/run_all.gd sudah diimplementasikan sebagai runner SceneTree:
godot --headless --path godot_rebuild --script res://tests/run_all.gd
```

Nama executable berbeda menurut instalasi. Runner harus mengembalikan exit code bukan nol saat gagal. Import/parsing sukses saja bukan bukti gameplay benar. Scene test dan tes pada perangkat tetap diperlukan.

### Performa

1. Catat perangkat, renderer, resolusi, preset, versi build, jumlah unit/FX, durasi, FPS dan frame time persentil, memori serta jumlah node.
2. Skenario: idle/menu, wave normal, wave ramai, boss+skill, restart berkali-kali, sesi 15–30 menit pada HP.
3. Target awal yang bisa disepakati: 60 FPS perangkat utama dan 30 FPS minimum low-end. Anggaran frame kira-kira 16,7 ms dan 33,3 ms. Ukur tick simulasi terpisah agar 30 FPS render bukan 30 update game.
4. Profil dahulu: script, physics, render, overdraw, audio, alokasi. Optimalkan bagian yang terbukti mahal.
5. Kandidat optimasi: spatial grid untuk query musuh, kurangi pencarian semua unit untuk setiap unit, cache visual statis, budget FX, atlas, kurangi redraw dan node sementara.
6. Pooling baru dipakai bila churn terbukti mahal; reset seluruh state saat reuse. Jangan membuat pooling baru sebelum lifecycle benar.
7. Ulangi semua tes perilaku setelah optimasi. LOD/quality boleh mengurangi efek, **tidak** mengurangi damage atau frekuensi update AI secara diam-diam.

**Syarat lulus:** tidak ada bug penghambat crash/save/combat/transaksi; performa memenuhi target pada perangkat yang ditetapkan; masalah minor yang tersisa terdokumentasi dan disetujui.

## 16. Tahap 12 — Build final, uji upgrade, dan pergantian versi

1. Buat workflow baru untuk `godot_rebuild/` setelah build lokal stabil. Workflow lama yang memanggil converter/GDExtension tidak boleh membangkitkan isi proyek baru.
2. Pin engine dan export template. CI baru menjalankan validasi data, import, tes simulasi/integrasi headless, lalu export. Build plugin platform jika memang digunakan.
3. Buat desktop build dan Android debug dari checkout bersih. Pastikan aset tidak hanya tersedia karena cache komputer pengembang.
4. Siapkan Android release: package ID produksi, version code meningkat, signing, permission minimal, arsitektur perangkat, target SDK serta kebijakan store yang berlaku saat rilis.
5. Hapus/nonaktifkan debug shop, unlimited gold, mock settlement, cheat shortcut dan log sensitif di release.
6. Gunakan internal/closed testing dahulu. Uji instalasi baru **dan** upgrade aplikasi lama tanpa kehilangan save.
7. Uji offline, sign-in/out, cloud restore, pembelian sandbox, background dan pertandingan panjang pada build release, bukan hanya editor.
8. Siapkan pemulihan: backup save sebelum konversi, schema kompatibel, dan forward-fix bila upgrade bermasalah. Jangan mengandalkan downgrade APK sebagai rollback yang pasti diizinkan.
9. Rilis bertahap dan monitor crash, ANR, corrupt save, masalah input, cloud, serta transaksi.
10. Setelah stabil, perbarui README agar pintu masuk utama jelas menuju proyek baru. Tandai panduan/build Godot lama sebagai arsip atau nonaktifkan secara eksplisit setelah ditinjau.
11. Simpan kode sumber Python sebagai referensi sampai seluruh kriteria selesai terpenuhi. Penghapusan/arsip permanen adalah pekerjaan terpisah.

### Definisi migrasi selesai

- [ ] Semua fitur pada matriks memiliki status teruji atau pengecualian scope yang disetujui.
- [ ] 54 level dan semua konten dalam inventaris final tervalidasi; bukan sekadar file ada.
- [ ] Gameplay berjalan tanpa Python/Pygame di runtime client.
- [ ] Tidak bergantung pada hasil converter, GDExtension, scene, atau plugin migrasi lama.
- [ ] UI, visual, audio, kontrol dan lifecycle memenuhi referensi/keputusan desain.
- [ ] Save baru aman dan jalur migrasi save lama teruji jika diwajibkan.
- [ ] Cloud dan pembayaran benar-benar teruji jika masuk scope rilis.
- [ ] Performa terukur dan lulus pada perangkat minimum.
- [ ] Build dapat dibuat ulang dari checkout bersih dengan instruksi yang tercatat.
- [ ] Rilis terbatas berhasil, masalah kritis nol, dan rencana pemulihan tersedia.

## 17. Cara mengerjakan tanpa kewalahan

Kerjakan satu unit kecil per sesi:

1. Pilih satu fitur dari matriks.
2. Baca implementasi sumber dan tes Python relevan.
3. Tulis input, output, satuan, urutan operasi dan kasus gagal.
4. Implementasikan manual di Godot.
5. Jalankan tes kecil, scene test, lalu pertandingan bila relevan.
6. Catat screenshot/log/angka hasil tanpa data pribadi.
7. Simpan checkpoint di branch kerja setelah lulus. Jika melakukan push dari sesi ini, hanya ke `arena/01a0d776-mystic-arena`.
8. Lanjut ke fitur berikutnya; jangan menggabungkan porting, redesign visual dan rebalance dalam satu perubahan.

### Pekerjaan pertama yang disarankan

**Untuk sesi pertama, cukup tahap 0 dan tahap 1:** baseline Python berjalan, catatan fitur awal tersedia, proyek kosong dibuat, menu ↔ arena placeholder berjalan. Jangan mulai semua hero, boss, C++, cloud, atau pembayaran sekaligus.

Setelah itu lanjut berturut-turut ke satuan/data → gerak → combat → satu pertandingan kecil. Bila ada kegagalan, laporkan tahap, versi Godot, pesan error lengkap, langkah reproduksi dan hasil yang diharapkan. Perbaiki di tahap tersebut sebelum menambah konten.

### Catatan validasi dokumen

Pada penyusunan dokumen ini dilakukan inspeksi sumber, perhitungan entri literal data, pemeriksaan keberadaan proyek, dan pemeriksaan header beberapa aset audio. Game Python, proyek Godot, seluruh suite test, build Android dan layanan backend **belum dijalankan** sebagai bagian dari penyusunan rencana. Target dan checklist di atas adalah kriteria kerja yang harus dibuktikan, bukan klaim pengujian sudah lulus.
