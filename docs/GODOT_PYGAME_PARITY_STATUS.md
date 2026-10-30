# Status parity Godot ↔ Pygame

**Tanggal audit:** 2026-10-30  
**Sumber kebenaran:** Pygame Android/mobile di root repository.  
**Target port yang diaudit:** `godot_rebuild/` (proyek Godot aktif).  
**Kesimpulan:** parity penuh **belum tercapai dan belum boleh diklaim**.

Dokumen ini menggantikan rencana migrasi, handoff status, dan work-log lama. Ini adalah satu-satunya ringkasan status parity; kontrak teknis per sistem dan runbook tetap terpisah. Semua koreksi untuk parity harus dilakukan di Godot, bukan dengan mengubah Pygame agar cocok dengan port.

Dokumen status/historis yang dihapus karena duplikat atau usang: `AUDIT_ULANG_DARI_AWAL.md`, `RENCANA_MIGRASI_GODOT_DARI_NOL.md`, `STATUS_GODOT_REBUILD.md`, `PETA_SISA_MIGRASI.md`, `HERO_MIGRATION_PROGRESS.md`, `CARA_CONVERT_TANPA_HAPUS_PYGAME.md`, dan `PLAYSTORE_RELEASE.md`. Dokumen kontrak dan runbook yang masih dipakai tidak dihapus; dua runbook lama yang menunjuk proyek `godot/` diberi label LEGACY.

## Batas bukti audit

Audit ini membandingkan implementasi dan tes yang ada pada checkout `main` (`0c5eca4`) serta mencatat hasil tes runtime terakhir yang tersedia dari PR #348. Ia **bukan** sertifikasi build Android atau pixel-diff lengkap: checkout saat audit ini tidak memiliki executable Godot maupun Pygame terpasang, dan belum tersedia pasangan screenshot Godot/Pygame dari keadaan game yang sama.

Di repository ada ratusan tes native dan source oracle yang mengeksekusi atau merekam perilaku Pygame. Oracle data/domain dan draw-operation dapat membuktikan angka, urutan, teks, geometri, warna, serta hit-test tertentu. Itu tidak otomatis membuktikan tampilan akhir GPU, semua state gameplay, atau seluruh perangkat identik. Beberapa skrip lama di `tools/test_godot_*_parity.py` masih menunjuk proyek historis `godot/`; skrip tersebut bukan validasi untuk proyek aktif `godot_rebuild/` dan tidak dihitung sebagai bukti parity proyek aktif.

## Definisi target: parity seluruh game, bukan visual saja

Koreksi ruang lingkup terbaru: **semua hal yang pemain alami di Pygame Android/mobile harus berperilaku sama di Godot**. Gambar yang sama saja tidak cukup; begitu pula aturan numerik yang sama saja. Matriks di bawah menjadi cakupan wajib audit/port:

| Sub-sistem | Yang wajib sama | Status berdasarkan bukti yang tersedia |
|---|---|---|
| Simulasi pertandingan | Tick order, gerak, targeting, damage/mitigasi, cooldown/status, proyektil, death/reward, wave/spawn, ekonomi, transaksi, menang/kalah, dan aturan RNG/replay yang memengaruhi hasil. | Banyak aturan domain memiliki source oracle/replay; parity semua kombinasi dan satu kampanye produksi penuh belum terbukti. Suite native terakhir masih memiliki kegagalan yang dicatat di bawah. |
| Konten | Semua level 1–54, tema/map, minion, tower, hero/skill, boss/miniboss, item, unlock dan harga. | Katalog besar tersedia dan sebagian diuji terhadap sumber; tersedianya data/registry tidak membuktikan semua konten playable dan setara. README proyek masih menandai level 2–54 sebagai eksperimental. |
| AI dan perintah | Policy/rekrutmen/build/upgrade/item/shield, target choice, auto-cast/skill priority, tactical commands, serta perilaku kedua tim pada keadaan sama. | Komponen native dan source tests tersedia, tetapi interaksi keseluruhan dalam pertandingan penuh belum disertifikasi per level/roster. |
| Alur UI | Boot/menu, slot/progres, pilih level, hero shop, settings, help/credits, match HUD, shop/forge, pause, hasil, reward/unlock, retry/replay dan navigasi/back. | Ada coverage UI dan beberapa tes interaksi; suite native terakhir masih gagal pada kelompok menu, hasil/progres, dan input. Belum ada replay lengkap semua alur dari awal sampai akhir. |
| Input Android/mobile | Hitbox dan koordinat sentuh, tap/hold/drag, multi-touch, jeda/back, focus/background/resume, orientation, aspect ratio, safe area, haptics dan respons kontrol. | Sebagian aturan memiliki oracle/tes otomatis; uji end-to-end pada perangkat Android fisik dan seluruh ukuran/orientasi belum ada. |
| Presentasi dan audio | Sprite/map, animasi, layer/order, font, ukuran/posisi HUD, efek, transisi, musik/SFX, volume/mute dan timing. | Banyak aset/operasi gambar source-backed, tetapi belum ada pasangan screenshot/video/audio runtime untuk menyatakan hasilnya identik. |
| Save dan layanan | Slot, progression, achievement/reward, cloud sync/conflict, top-up/pembelian dan pemulihan data. | Godot memiliki jalur data/fitur tersendiri. Impor berkas slot Pygame ada sebagai domain + oracle + suite native dan kini punya tombol di panel save (lihat bagian *Impor save Pygame*), tetapi belum diuji pada perangkat Android nyata. Kesetaraan format penuh, cloud lintas engine dan alur pembayaran end-to-end belum terbukti. |
| Distribusi Android | Build bersih, install/upgrade, lifecycle OS, renderer GPU, performa/memori/thermal dan audio pada perangkat yang didukung. | Belum ada hasil sertifikasi pada perangkat nyata yang membuktikan parity Pygame Android ↔ Godot Android. |

Tidak akan mengubah aturan, UI, atau data Pygame agar tes Godot lulus. Jika ada selisih, sumber Pygame menentukan hasil yang benar; perbaikan dilakukan di `godot_rebuild/`. Untuk render lintas vendor GPU, targetkan perangkat/resolusi referensi yang ditetapkan; jangan menyamakan hasil satu screenshot dengan parity keseluruhan.

## Temuan utama

| Area | Yang sudah dibandingkan/dites | Yang masih kurang |
|---|---|---|
| Data dan aturan domain | Banyak katalog dan aturan numerik memiliki source oracle serta replay native. Cakupannya terlihat di `godot_rebuild/tests/` dan kontrak sistem. | Katalog lengkap bukan bukti semua 54 level dapat dimainkan dengan perilaku dan alur produksi yang sama. README Godot menyebut level 2–54 sebagai mode uji eksperimental; kampanye penuh/balance final belum lulus parity end-to-end. |
| HUD dan dock mobile | Layout dock punya oracle Pygame; geometri, teks, warna, tombol, dan hit-test dibandingkan. Popup kastil/upgrade ditambahkan lewat PR #348 dengan pemeriksaan geometri dan tes tap scene. | Belum ada render screenshot berpasangan untuk memastikan hasil font, anti-alias, clipping, layering, dan scaling sama pada runtime. Tes geometri tidak membuktikan kesamaan piksel. |
| Kontrol dan overlay | Ada tes native/source untuk banyak jalur input, popup, pause, touch, serta transaksi UI. | Suite native kini lulus tanpa kegagalan pada grup input/tactical, lifecycle shield, menu/render, hasil/progres dan projectile; triase 23 kegagalan sebelumnya dicatat di bawah. Bukti ini tetap headless, bukan screenshot/piksel. |
| Seni, animasi, dan efek | Banyak aset dibake dari sumber Pygame; draw-operation dan urutan layer memiliki oracle. | Belum ada pixel-diff end-to-end. Rasterizer, blending alpha, font metrics, dan backend renderer Godot dapat berbeda dari Pygame meskipun parameter/komposisi sumber sama. Efek runtime dan semua state animasi belum dibuktikan identik melalui screenshot/video. |
| 54 level dan sesi penuh | Katalog level serta sejumlah aturan level mempunyai tes sumber. | Prototipe Godot masih mengidentifikasi level 2–54 sebagai eksperimental; match panjang, progression, seluruh kombinasi boss/minion, dan keseimbangan belum dibuktikan setara dalam permainan penuh. |
| Android/perangkat | Ada implementasi serta tes otomatis untuk sebagian logika touch/mobile dan adaptive quality. | Belum ada bukti ekspor dan run terverifikasi pada perangkat Android fisik untuk resolusi/safe-area, multitouch, lifecycle background, renderer GPU, audio, performa, dan thermal. |
| Save, cloud, pembayaran | Godot memiliki modul dan penyimpanan pengembangan sendiri; lihat kontrak terkait. Impor slot Pygame (`scripts/match/pygame_save_import.gd`) direplay terhadap 11 berkas slot sumber lewat oracle read-only, dan tombol impor di panel save diuji headless dengan klik sungguhan. | Belum ada uji pada perangkat Android nyata (salinan berkas ke `user://` masih langkah manual). Kesetaraan cloud antar-engine dan alur pembayaran end-to-end belum terbukti. File progres Godot tetap terpisah dari save Pygame sampai impor dijalankan. |

### Hasil runtime terakhir yang diketahui

Tes native Godot 4.7.2 headless terakhir yang jumlah pemeriksaannya tercatat (branch `arena/a5ab95fe-mystic-arena`, commit `f4e840b`, [run 41019560561](https://github.com/dharmawantoxi/mystic-arena/actions/runs/41019560561)) menjalankan 1.505.443 pemeriksaan (147 di antaranya suite impor slot Pygame: 112 domain + 35 scene) dan melaporkan **0 kegagalan** serta tanpa `SCRIPT ERROR`. Sebelumnya run PR #348 menjalankan 1.505.221 pemeriksaan dengan **23 kegagalan**; seluruhnya sudah ditriase dan diperbaiki, dan penyebabnya dicatat di tabel triase di bawah.

Run native terbaru untuk lapisan 9bt adalah commit `0411b28` ([run 41030476536](https://github.com/dharmawantoxi/mystic-arena/actions/runs/41030476536)) dan lulus tanpa kegagalan; jumlah pemeriksaannya tidak terbaca dari artefak di lingkungan kerja ini, jadi angka 1.505.443 di atas tetap merujuk run `f4e840b`.

Validator statis terakhir yang tersedia lulus **21.827 pemeriksaan**. Itu berbeda dari tes native dan tidak menggantikan bukti runtime, screenshot, perangkat, atau audio.

#### Triase 23 kegagalan tes native sebelumnya

| Gejala | Akar masalah | Perbaikan |
|---|---|---|
| Suite painter, level-stat, tactical, controller, touch, popup gagal berantai; tiga `SCRIPT ERROR: Invalid access of index '0'` | Sumber memulai pertandingan dengan roster hero kosong (`Game.heroes = []`; Kaizen hanya dimiliki, disummon lewat `try_buy_hero`), sedangkan suite lama membaca `player_hero_ids[0]`/`player_roster()[0]` yang kosong. Suite yang error berhenti di tengah sehingga sisa pemeriksaannya tidak pernah jalan. | Suite memanggil transaksi nyata `PrototypeBattle.buy_player_hero("kaizen")` sebelum memakai hero, dan fixture touch menyummon hero merah di spawn merah untuk gestur follow. |
| `MainMenu buttons match the source two-button row...` | `SourceUiButton` menggambar label sendiri, tetapi teks native yang tak terlihat tetap menaikkan minimum size sehingga tinggi menjadi 53 px dan tombol SETTINGS melebar ke 507 px karena label hasil lokalisasi. | Teks native tombol memakai ukuran font netral; rect sumber 300×50 / 360×50 kini dipertahankan. Bukti tata letak juga mengikuti `fit`/origin viewport, bukan asumsi 1:1. |
| `Muted labels use TEXT_DIM`, `The menu eyebrow uses CYAN` | Suite masih mengharapkan menu eksperimental lama (8 dim + cyan). Sumber 9bv18 dan validator statis menetapkan 6 TEXT_DIM, 1 GOLD, 0 CYAN. | Suite diselaraskan dengan palet sumber 9bv18. |
| `Shield scene lifecycle does not leak nodes` | Baseline suite ini diambil saat app masih di dalam match karena suite popup sebelumnya berhenti akibat error indeks; hitungan akhir (menu) lalu terlihat seperti kebocoran 161 node. | Kebocoran kini dilaporkan sebagai census path node, dan baseline valid setelah suite popup selesai. |
| `Retry records its independent minion kill`, `Defeat retry accumulates totals...` | Restart membangun world baru tanpa hero hidup, sehingga kill pada percobaan kedua tidak pernah terjadi. | Fixture level-stat menyummon starter pada setiap world baru. |

Catatan penting untuk triase berikutnya: `SCRIPT ERROR` di tengah suite menghentikan fungsi suite tanpa mencetak `FAIL`, sehingga pemeriksaan sisanya hilang tanpa terlihat gagal. Karena itu bandingkan jumlah `PASS: ... checks` antar-run: penurunan jumlah pemeriksaan adalah sinyal regresi yang tidak tertangkap daftar `FAIL`. Anotasi CI kini juga menyertakan baris `at: file:line` dari setiap `SCRIPT ERROR`.

## Impor save Pygame (lapisan domain, 30 Oktober 2026)

Pemain Pygame tidak bisa membuka progresnya di Godot karena format simpanannya berbeda. Langkah pertama migrasi data kini ada: `godot_rebuild/scripts/match/pygame_save_import.gd` membaca **salinan** berkas slot Pygame (`slot_1.json`…`slot_3.json`) yang diletakkan di direktori `user://` Godot, memetakannya ke envelope slot native, lalu menulisnya lewat `SaveSlotStore` (envelope berversi, rename atomik, notifikasi cloud). Berkas Pygame tidak pernah dibuka langsung dari direktori Android lama dan tidak pernah diubah.

Bukti yang ada:

* `godot_rebuild/tests/pygame_save_import_source_oracle.py` menjalankan `SaveManager` asli dari AST (jam tetap, tanpa Pygame/cloud) terhadap 11 berkas slot: profil lengkap, save lama tanpa metadata, angka berbentuk float, ID hero asing/duplikat, level di luar 1–54, `level_stats` rusak, kesulitan asing, gold negatif, gold bukan angka, JSON terpotong, dan JSON yang bukan objek. Fixture: `tests/fixtures/pygame_save_import_source.json`.
* Suite native `tests/pygame_save_import_checks.gd` membandingkan hasil impor dengan fixture itu, termasuk jalur tulis nyata ke `user://` (slot terisi tidak ditimpa tanpa izin, slot kosong/4 ditolak, sumber hilang/JSON rusak ditolak tanpa menulis apa pun, berkas sumber tetap utuh).
* `validate_project.py` menjaga agar oracle tetap dijalankan CI dan agar modul impor hanya menulis lewat lapisan slot native.
* Suite native menambah 147 pemeriksaan (112 domain + 35 scene): total run `f4e840b` menjadi 1.505.443 pemeriksaan, 0 kegagalan, tanpa `SCRIPT ERROR`.
* Suite scene `tests/pygame_save_import_scene_checks.gd` (35 pemeriksaan) menjalankan alur tombol impor di panel save — konfirmasi, batal, tanpa berkas, slot terimpor, slot rusak ditolak, impor ulang, kartu slot serta level/difficulty ikut menyegarkan, pembersihan node — tanpa menyentuh save pengguna.

Perbedaan yang disengaja beserta alasannya:

| Kasus | Pygame (`_system.py::SaveManager`) | Godot | Alasan dan acceptance criteria |
|---|---|---|---|
| Berkas rusak/terpotong atau JSON bukan objek | `load()` menelan error dan mengembalikan `get_empty_save()`; slot tampak kosong, dan penyimpanan berikutnya menimpa berkas rusak itu | Impor ditolak (`invalid_json`/`not_a_save`), slot tujuan tidak disentuh | Kehilangan progres tidak boleh terjadi diam-diam saat migrasi. Diterima jika: tidak ada berkas ditulis saat penolakan, alasan penolakan bisa ditampilkan, dan pemain dapat mencoba berkas lain. Suite mengecek slot tetap kosong setelah setiap penolakan. |
| Nilai yang tidak bisa direpresentasikan envelope native: ID hero tak dikenal, hero non-boss di `unlocked_bosses`, level di luar 1–54, entri `level_stats` tidak lengkap/`wins > total_attempts`, `run_difficulty` asing | Disimpan apa adanya; `get_level_stats` mengembalikan entri mentah | Nilai yang bermasalah dibuang **satu per satu** dan dilaporkan di `report` (`dropped_heroes`, `dropped_bosses`, `dropped_levels`, `dropped_level_stats`, `dropped_duplicates`, `rejected_difficulty`, `clamped_last_level`); sisanya tetap diimpor | `LevelProgressStore._valid` menolak seluruh berkas bila satu nilai tidak sah, jadi tanpa sanitasi satu ID rusak akan membuang seluruh profil. Diterima jika: gold/level/skor/harga yang sah tetap identik dengan sumber dan setiap pembuangan terlihat di laporan. |
| `meta_gold` negatif atau bukan angka | Diterima apa adanya (saldo bisa negatif/string) | Seluruh impor ditolak (`corrupt_meta_gold`) | Ekonomi native mengasumsikan saldo bilangan bulat ≥ 0; menebak-nebak nilai mata uang lebih berbahaya daripada menolak. Diterima jika: tidak ada slot ditulis dan laporan menyebut `corrupt_meta_gold`. |
| Entri `level_stats` rusak | `get_level_stats` mengembalikan entri mentah tanpa validasi | `LevelStats.get_level_stats` memvalidasi dan jatuh ke `empty_stats()` | Sudah menjadi keputusan kontrak level-stat; impor ikut aturan itu agar statistik pertandingan berikutnya tidak memakai entri cacat. Bukti: kasus `broken_stats` di fixture mencatat balikan mentah Pygame (`{"best_score": 5}`) dan Godot menghasilkan entri kosong. |
| `replay_reward_counts` | Tidak ada di save Pygame | Slot hasil impor mulai dengan ledger kosong; `import_source: "pygame"` menandai asal slot | Ledger hadiah replay adalah fitur Godot; level yang sudah selesai tetap dianggap selesai. Diterima jika: slot hasil impor lolos `LevelProgressStore._valid` dan tidak ada hadiah replay ganda yang diklaim otomatis. |
| `slot_last_played` saat impor | `save()` selalu mencap waktu sekarang | Impor memakai jalur `SaveSlotStore.save_state`, jadi mencap waktu impor; `slot_created` dari berkas sumber dipertahankan | Mengikuti semantik "menyimpan = bermain sekarang" milik sumber. Diterima jika: `slot_created` sumber tidak hilang dan kartu slot menampilkan waktu impor. |

Jalur pemain sekarang: salin `slot_N.json` menjadi `user://pygame_slot_N.json`, buka panel save dari menu, tekan **IMPORT**, lalu konfirmasi. Panel menampilkan hasil per slot (`Slot 1 imported: Level 4 · Hero Gold 7250`, `Slot 2 refused: invalid_json`) dan kartu slot menyegarkan diri. Panel tetap request-only; menu yang membaca berkas, memanggil impor, dan menulis slot.

Yang **belum** ada dan tidak diklaim: salinan berkas masih langkah manual (belum ada tombol "pilih berkas" Android/SAF), belum ada uji impor pada perangkat Android nyata, kesetaraan cloud antar-engine, dan alur pembayaran/top-up. Sampai uji perangkat ada, baris "Save dan layanan" tetap belum setara.

## Screenshot Android nyata sebagai oracle tata letak (30 Oktober 2026)

Pengguna mengirim dua tangkapan dari APK Pygame di HP: `docs/screenshots/android-2026-10-30/menu.jpg` dan `match.jpg`, keduanya **2436×1080**. Ini bukti pertama dari perangkat nyata, jadi sekarang dipakai sebagai oracle, bukan lagi tebakan dari kode.

Yang terbukti dari gambar (skala **1,5**, permukaan logis **1624×720**, arena 1280, dock kanan **344 px** — cocok `platform_utils.create_display` + `mobile/sidepanel.py`):

| Elemen | Sumber (logis) | Terukur di screenshot |
|---|---|---|
| Panel kanan | `panel_rect(1624)` = (1280, 0, 344, 720) | tepat 1280..1624; mortar bata tiap 34 px |
| Tombol PAUSE | (1294, 14, 58, 58), cincin emas | 1294..1352 × 14..72 |
| Kotak STATUS | (1294, 84, 316, 96) | 1294..1610 × 84..179,5 |
| Kotak HEROES (0 hero) | (1294, 190, 316, 64) | 1294..1610 × 190..253 |
| Kotak TACTICAL | (1294, 264, 316, 210) | 1294..1610 × 264..474 |
| 5 tombol tactical | 304×32 mulai y=288, langkah 38 | 290..317, 328..355, 366..393, 404..431, 442..469 (isi abu `(46,45,50)` = disabled) |
| Menu CONTINUE / PLAY | (320, 311, 300, 50) & (660, 311, 300, 50) | x 320 / 660, y 311,5, tinggi 48,5 |
| Menu tumpukan 6 tombol | x=460, w=360, h=50, mulai y=364, langkah 53 | bingkai atas 364, 417, 470, 523, 576, 629 |

`tools/measure_android_screenshot.py` (Pillow, manual, bukan CI) menghitung ulang angka itu dan menulis `godot_rebuild/tests/fixtures/android_screenshot_reference.json`: setiap elemen berisi `expect` (angka tata letak sumber) dan `measured` (hasil ukur gambar). Selisih terbesar 2 px; skrip berhenti dengan error bila ada yang melebihi 3 px.

Perbaikan yang dipaksa bukti ini di `godot_rebuild/`:

* **Bingkai menu dulu diperbesar & ditengahkan.** `menu_backdrop.cover_rect()` memakai *cover* (`maxf`) sehingga pada 1624×720 latar 1280×720 dinaikkan 27 % lalu dipotong atas-bawah, dan `main_menu.gd` menengahkan bingkai (`origin.x = 172`). Akibatnya tombol HERO SHOP akan berada di x=632, bukan 460 seperti di HP. Sekarang `arena_rect()` menempelkan bingkai di kiri pada 1:1 (hanya mengecil bila permukaan lebih kecil, dan *letterbox* vertikal pada layar tinggi), dan `MainMenu.tscn` memakai `SOURCE_BUTTON_RECTS` sebagai satu-satunya sumber angka tombol.
* **Strip batu kanan tidak ada di menu.** Sumber mengecat dinding batu sekali ke sisa lebar permukaan (`_gambar_panel_samping`) sebelum layar apa pun digambar, jadi menu pun berlatar batu di 344 px kanan. Godot kini punya `scripts/ui/panel_stone.gd` (angka bata, gradasi, garis emas) + `scripts/ui/panel_backdrop.gd` untuk menu; `side_panel.gd` tetap memakai angka yang sama untuk dock pertandingan.
* **Kabut menu menembus dock.** Lapisan kabut 1500 px dulu digambar melewati batas arena; kini dipotong ke 1280×720 (`_blit_clipped`), sama seperti blit sumber ke subsurface arena.

### Bobot font panel kanan (layer 9bv19, 30 Oktober 2026)

Audit panel kanan menemukan satu selisih nyata di luar geometri: **bobot font**. Sumber memanggil `get_font(size, "body_bold")` untuk judul kotak, angka gold, "LV n", nama hero dan label tactical (`mobile/sidepanel.py`), dan `_render._STYLE_FONT_MAP` memetakan `body_bold` ke **Barlow-Bold**; teks lain memakai `body` (Barlow-Regular). Port sebelumnya menggambar **semua** teks dengan `get_theme_default_font()` (Barlow-Regular) dan mengukur lebarnya juga dengan font itu, sehingga `bold: true` di layout diabaikan.

Perbaikannya di `godot_rebuild/`:

* `side_panel_layout.gd` kini menulis `style` pada setiap entri teks (`"body"` / `"body_bold"`) dan menerima dua callable pengukur: `build(snapshot, panel, measure, measure_bold)`. Tiga keputusan yang bergantung pada lebar memakai pengukur bold, sama seperti sumber yang mengukur teks dengan font yang ia gambar: batas 55 % untuk mengecilkan gold 22 → 18, "LV n" rata kanan, dan label tactical di tengah tombol.
* `side_panel.gd` menggambar tiap entri dengan `SourceFonts.for_style(entry["style"])` (modul 9bv17) dan menyediakan `_measure` (Barlow-Regular) + `_measure_bold` (Barlow-Bold). Tidak ada lagi `get_theme_default_font()` di panel ini.
* Oracle `side_panel_source_oracle.py` sekarang merekam `style` dan `size` dari font yang benar-benar dipakai `SidePanel.render`, jadi fixture memuat 90 string (56 `body_bold`, 34 `body`) dengan bobot yang berasal dari sumber, bukan dari tebakan port. Suite native membandingkan teks, warna, posisi, ukuran **dan** style per string.

Dampak lebar yang terukur (TTF yang sama, Pillow):

| String | Ukuran | Regular | Bold | Delta |
|---|---|---|---|---|
| `TACTICAL COMMANDS (HOLD)` | 13 | 167 px | 175 px | +8 |
| `ATTACK DMG DEALER [D]` | 13 | 145 px | 150 px | +5 |
| `STATUS` | 13 | 46 px | 49 px | +3 |
| `1,106` | 22 | 45 px | 47 px | +2 |
| `ABADDONTHERION` | 15 | 124 px | 125 px | +1 |

Karena itu teks rata kanan dan label tactical yang di tengah bergeser 1–3 px dibanding port lama; geometri kotak, tombol dan hit-test tidak berubah (dikunci oleh pemeriksaan native bahwa jumlah teks dan `y_after_tactical` tetap sama untuk kedua pengukur).

Deviasi yang disengaja: sumber menggambar tombol tactical **dua kali** (gambar kedua meninggalkan busur aksen), dan itu tidak ditiru. Efek visualnya sisa goresan; port hanya menggambar satu kali.

Yang **belum** dibuktikan: font sungguhan baru diverifikasi lewat metrik TTF di luar Godot; tidak ada executable Godot di lingkungan kerja ini, jadi hasil render, hinting, dan anti-alias Barlow-Bold pada runtime masih harus dilihat pengguna di PC/perangkat.

### Membandingkan capture Godot dari PC (layar sentuh)

Perangkat uji pengguna (PC dengan layar sentuh) memenuhi `DisplayServer.is_touchscreen_available()`, jadi jalur mobile aktif dan dock 344 px ikut tampil bila permukaan logisnya 1624×720 — bukan hanya di HP.

1. Jalankan dengan permukaan yang sama seperti HP. **Default jendela run sekarang sudah 1624×720** (`window_width_override`/`window_height_override` di `project.godot`), jadi F5 dari editor langsung memberi kanvas logis 1624×720; basis desain tetap 1280×720 dan build ekspor tetap 1280×720. Untuk run di luar editor atau bila ukuran jendela belum ikut: `godot --path godot_rebuild --resolution 1624x720`. Proyek memakai `canvas_items` + `expand`, jadi kanvas logis = ukuran jendela ÷ skala; jendela 1920×1080 justru menghasilkan kanvas 1280×720 tanpa dock, sedangkan 1624×720 atau 2436×1080 menghasilkan 1624×720.
2. Rekam tanpa border jendela: `godot --path godot_rebuild --resolution 1624x720 --write-movie C:/shots/menu.png --quit-after 90`. Movie writer Godot menulis deret PNG seukuran jendela; pakai frame terakhir.
3. Bandingkan dengan oracle HP: `python tools/measure_android_screenshot.py --compare C:/shots/menu.png --kind menu` dan `--kind match` untuk dock. Skrip mengukur capture itu dengan pipeline yang sama seperti capture HP, mencetak delta per elemen, dan gagal bila ada yang melebihi 3 px (default `--tolerance 3`).
4. `--self-test` membuktikan pipeline tidak bergeser antarsesi: fixture harus bisa dibuat ulang byte-per-byte dari dua capture HP, dan tata letak yang sama harus tetap terbaca pada resolusi lain (uji pada capture setengah resolusi, toleransi +1 px karena highlight 1 px terkuantisasi).

Batas verifikasi lewat PC: `is_touchscreen_available()` bukan `OS.has_feature("android")`. Geometri dock/menu jadi bisa diuji di PC, tetapi cabang khusus Android (misalnya `world.level_intro_state(OS.has_feature("android"))`, lifecycle aplikasi, dan ekspor APK) tetap butuh perangkat atau emulator.

Yang **belum** diklaim: pasangan screenshot Godot pada perangkat yang sama belum direkam (tidak ada perangkat/emulator di lingkungan kerja ini), jadi perbandingan saat ini satu arah — geometri Godot diverifikasi terhadap angka hasil ukur Pygame lewat `tests/android_layout_checks.gd`, bukan pixel-diff. Aturan dock tetap: dock hanya dibuat bila sisa lebar ≥ 120 px (`platform_utils`), jadi pada viewport 16:9 (1280×720) memang tidak ada dock, dan pada 2436×1080 ada.

## Acceptance criteria untuk menyatakan parity

1. Gunakan build Pygame Android sebagai oracle; jangan mengubahnya demi port.
2. Rekam screenshot Pygame dan Godot dari **seed, level, state, resolusi viewport, skala, dan waktu simulasi yang sama**. Uji minimal 1280×720, 16:9, serta satu ultrawide Android yang benar-benar dipakai; catat kapan dock aktif menurut aturan sumber.
3. Bandingkan alur visual utama: menu, pertandingan, HUD/dock, seleksi hero/struktur, shop/forge, pause, intro/efek, menang/kalah, dan settings. Simpan pasangan screenshot dan pixel-diff/overlay untuk setiap gap.
4. Rekam urutan input yang sama (tap, hold, drag, multi-touch, keyboard/controller bila tersedia) dan bandingkan hasil state/domain, bukan hanya tampilan.
5. Selesaikan atau jelaskan setiap kegagalan tes native; tidak ada kegagalan parity yang belum ditriase.
6. Validasi ekspor dan interaksi pada perangkat Android nyata sebelum mengklaim parity Android.

Perbedaan yang disengaja harus dicatat per kasus beserta alasan dan acceptance criteria; jangan menandainya sebagai "sama" hanya karena tes statis lulus.

## Rujukan aktif

- Proyek/tes Godot: [`godot_rebuild/README.md`](../godot_rebuild/README.md), [`godot_rebuild/tests/`](../godot_rebuild/tests/).
- Sumber mobile Pygame: [`mobile/sidepanel.py`](../mobile/sidepanel.py), [`mobile/platform_utils.py`](../mobile/platform_utils.py), [`mobile/hud.py`](../mobile/hud.py), serta `_core.py`, `_render.py`, `_entity.py`, `_system.py`.
- Kontrak domain yang tetap dipakai: [`godot_rebuild/MATCH_CONTRACT.md`](../godot_rebuild/MATCH_CONTRACT.md), [`godot_rebuild/AI_CONTRACT.md`](../godot_rebuild/AI_CONTRACT.md), dan kontrak combat/upgrade di folder yang sama.
