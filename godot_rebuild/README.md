# Mystic Arena — Godot Rebuild

**Proyek Godot native GDScript. Target editor: Godot 4.7.2.**

Pygame Android/mobile di root repository adalah sumber kebenaran untuk parity. Proyek ini masih port bertahap; kelengkapan domain, UI, dan render tidak otomatis berarti parity produksi. Status gap yang berlaku ada di [Status parity Godot ↔ Pygame](../docs/GODOT_PYGAME_PARITY_STATUS.md); jangan gunakan catatan milestone atau handoff lama sebagai status.

## Buka di Windows (tanpa membuat scene/script manual)

1. Ambil folder ini beserta seluruh isinya dari perubahan repo.
2. Buka **Godot 4.7.2 → Project Manager → Import**.
3. Pilih **`godot_rebuild/project.godot`**. Jangan memilih proyek migrasi lama.
4. Klik **Import & Edit**, tunggu import font selesai.
5. Tekan **F5**. Main scene sudah diatur ke `app/App.tscn`. Jendela run default **1624×720** — permukaan logis build Android 2436×1080 — supaya dock kanan 344 px ikut terlihat saat memeriksa parity di PC layar sentuh. Basis desain tetap 1280×720 (`viewport_width/height`) dan build ekspor tetap memakai 1280×720; hanya override jendela editor yang diubah.
6. Klik **Pertandingan awal** untuk prototipe terbaru. Ketiga laboratorium tetap tersedia.

Tidak memerlukan Python, pip, converter, addon, atau C++ untuk menjalankan client ini. Font yang dibutuhkan sudah disertakan. Export template belum diperlukan untuk menjalankan lewat editor.

### Pertandingan awal (baru)

- Subset **level 1 / normal**: mulai dengan 1000 G dan dua nexus, belum ada tower. Gold hanya berlaku dalam pertandingan ini.
- Klik lingkaran slot biru kosong → **Bangun Archer · 100 G**. Tersedia sembilan slot biru dari jalur sumber. Lingkaran merah milik lawan.
- Klik tower biru hidup → **Upgrade Lv.2 · 175 G** (Archer), **Cannon Lv.2 · 175 G**, **Ice Lv.2 · 175 G**, atau **Mage Lv.2 · 175 G** (baris jalur khusus), lalu naik bertahap sampai level 6. Harga berikutnya dan refund selalu ditampilkan; Archer level 5 menembak dua panah, level 6 tiga; Cannon menembak satu peluru splash + burn; Ice menembak satu kristal slow + attack-slow; Mage menembak 2–4 bolt chain debuff.
- Klik nexus biru → **Nexus Lv.2 · 500 G** sampai level 5 (900/1500/2400). Menaikkan HP/damage/range nexus **dan** stat/AI minion biru serta komposisi wave berikutnya; unit lama tidak berubah.
- **Jual** memberi 50 G untuk tier 1, atau refund sesuai tier setelah upgrade. Tidak bisa menjual nexus, tower lawan/mati atau menjual tower yang sama dua kali.
- Wave pertama muncul setelah sekitar 5 detik; unit keluar bertahap setiap 20 tick. Wave berikutnya menunggu timer dan lapangan bersih, bukan selalu muncul ketika countdown mencapai nol.
- Gold pasif bertambah tiap detik; kill memberi reward. HUD menampilkan saldo, wave dan HP/shield nexus. Slot/range preview ditampilkan ketika dipilih.
- **Kaizen biru + merah** (kit prototipe): spawn gratis kedua tim, Q/W/E/R hanya biru, klik-kanan jalan/ikuti hanya biru, hunt `< 900`, push ke nexus lawan, retreat `< 20%` HP, regen pasif, upgrade emas biru, respawn 10 dtk di spawn tim. **Biru dan merah auto-cast R→E→W→Q tiap 20 tick** (sumber v27: default aktif); tombol **Auto-cast** pada hero biru adalah penanda status dan hanya bisa memaksa aktif (sumber v29: tidak bisa dimatikan). QWER manual biru tetap tersedia dan berbagi cooldown dengan auto-cast. Bukan item atau AIPlayer.
- **Lawan default:** scene pertandingan kini memulai AIPlayer native dengan seed replay tetap. AI menjalankan scheduler policy, draft/rekrutmen hero, upgrade, item, shield, serta kontrol hero merah melalui transaksi domain nyata. Tekan **A** atau tombol **AI lawan [A]** di HUD untuk mematikan/mengaktifkan AI; saat dimatikan, pertandingan kembali ke mode lawan terjadwal lama. Ini masih mode QA (bukan balance final), bukan balance produksi.
- Nexus hancur membuka hasil otomatis dan menghentikan simulasi. **Mulai ulang** mereset saldo pertandingan, slot, queue dan hasil; **Menu** kembali ke menu utama. Hasil kini menyimpan reward/progres level 1 dalam file development Godot yang terpisah dari save Python; kegagalan ditampilkan dengan tombol coba lagi.
- Esc/Jeda dan kehilangan fokus menghentikan wave, combat dan income serta membatalkan transaksi tertunda. Lanjutkan secara eksplisit; hasil akhir tidak bisa dilanjutkan.

Detail harga, reset HP/shield dan pola tembak: [kontrak upgrade Archer](UPGRADE_CONTRACT.md) dan [kontrak nexus](NEXUS_CONTRACT.md).

Lihat [kontrak prototipe pertandingan](MATCH_CONTRACT.md) untuk oracle sumber, ledger, transaksi atomik, komposisi wave dan perbedaan yang disengaja. Ini belum seluruh aturan level Python atau build game produksi.

### Tower & nexus (laboratorium)

- Enam Archer level 1 dan dua nexus tersedia sejak awal; mode uji ini tidak memakai build/sell/upgrade.
- Tower/nexus menembakkan projectile. Minion dapat menghancurkan bangunan dan melanjutkan lane menuju nexus musuh.
- Pilih jenis minion serta **Kedua tim / Biru / Merah**, lalu **Kirim wave uji**. Mengirim satu tim membantu menguji siege; ini bukan ekonomi/scheduler produksi.
- Klik bangunan untuk melihat HP, shield dan radius serangan; klik minion untuk melihat stat/target.
- Shield nexus gratis sampai wave uji 10. Setelah wave 10, shield yang belum dibeli mati sesuai aturan sumber; pembelian belum tersedia.
- Nexus hancur menampilkan **BIRU MENANG / MERAH MENANG**, menghentikan simulasi dan mematikan spawn. Hasil belum menyimpan progres.
- Gunakan **Hasil/Jeda → Mulai ulang** atau **Menu**. Esc dan focus loss tetap menjeda simulasi.

Lihat [kontrak siege](SIEGE_CONTRACT.md) untuk urutan armor/shield, regen, projectile, batas kapasitas, dan perbedaan laboratorium dengan game produksi. Archer memakai HP efektif 2000 + shield 800, bukan HP mentah 800.

### Laboratorium minion


- Satu wave Goblin muncul pada awal simulasi: kedua tim, tiga lane.
- Minion mengikuti jalur, mencari musuh, menyerang, kehilangan HP dan mati.
- Klik/ketuk minion untuk melihat HP, cooldown dan target.
- Pilih Goblin/Orc/Troll/Undead/Dark Rider lalu klik **Tambah wave kedua tim**.
- Wave tambahan adalah fasilitas uji, bukan scheduler produksi. Batas 120 unit.
- Esc/Jeda menghentikan seluruh simulasi. Restart membuat dunia baru.
- Base hanya penanda; unit di ujung rute keluar arena, bukan menyerang base. Belum ada menang/kalah.

Lima definisi minion menggunakan stat nexus level 1 dari sumber. Tiga lane berisi **277 titik** yang dibandingkan dengan generator Python. Lihat [kontrak combat dan perbedaan yang disengaja](COMBAT_CONTRACT.md), termasuk regen Troll yang bisa membuat duel seimbang tidak selesai.

### Kontrol mode Uji input

| Aksi | Kontrol |
|---|---|
| Pilih penanda hijau | Klik kiri pada penanda |
| Gerakkan penanda terpilih | Klik kanan di area arena |
| Kontrol sentuh dasar | Ketuk penanda, lalu ketuk tujuan |
| Pause / lanjutkan | Esc atau tombol Jeda / Lanjutkan |
| Restart | Jeda → Mulai ulang arena |
| Kembali ke menu | Tombol Menu atau Jeda → Kembali ke menu |
| Keluar | Tombol Keluar di menu |

Keyboard Tab dan Enter juga dapat digunakan untuk navigasi tombol. Klik panel HUD tidak semestinya diteruskan sebagai command arena. Ketika aplikasi kehilangan fokus, arena dijeda; pemain melanjutkan secara eksplisit. Perintah gerak sementara dibatalkan saat pause/background agar tidak tersisa setelah resume.

**Khusus mode Uji input:** penanda hijau bukan hero hasil porting. Lane/slot di mode ini tetap ilustrasi placeholder. Mode Laboratorium minion yang baru memakai jalur sumber dan combat dasar. Keduanya belum pertandingan penuh.

## Yang sudah diimplementasikan

- Proyek mandiri: Compatibility, viewport 1280 × 720, stretch `canvas_items` + `keep`.
- Menu dengan theme, font lokal, tombol, fokus keyboard dan artwork prosedural baru.
- `App` sebagai pengendali perpindahan screen; aktivasi ganda dalam frame yang sama dijaga.
- Arena placeholder terpisah untuk mencoba seleksi dan perintah gerak.
- Laboratorium combat: tiga lane sumber, lima definisi minion, targeting tier 1, cooldown, regen, damage physical/magic dasar, death dan kredit uji satu kali.
- Inspeksi minion, wave uji manual, cap unit/event dan restart world yang bersih.
- Mode siege: Archer/nexus tier 1, shield/regen, projectile satu hit, inspeksi struktur, wave uji satu/dua tim dan hasil nexus.
- Upgrade Archer level 1–6, volley source dua/tiga panah, expected-level guard dan refund dinamis.
- Jalur Cannon level 2–6: pilihan eksplisit di level 1, muzzle sumber, splash 60% + burn DOT dengan akumulasi float exact.
- Jalur Ice level 2–6: tombol kontekstual level 1, muzzle kristal sumber, slow gerak + attack-slow, AOE slow level 6.
- Jalur Mage level 2–6: baris Paths dua-baris, muzzle kristal sumber, chain 2–4 tanpa refill, skill-down + anti-heal (regen cap-then-scale).
- Upgrade nexus 1–5 dengan scaling/AI minion, komposisi per-tier, dan formula HP/shield sumber.
- Prototipe terpisah: scheduler per-tim, gold lokal, 18 slot, transaksi Archer + nexus, hasil otomatis dan lawan builder terjadwal.
- Oracle wave/income/slot/harga/nexus melalui metode Python asli; ledger/replay/lifecycle teruji.
- Fixture dari metode numerik Tower/Castle/Minion asli; aturan minion dan bangunan tidak dipaksa menjadi satu formula.
- Simulasi demonstrasi dengan 60 physics tick/detik, terpisah dari render/UI.
- Pause/resume, restart, kembali ke menu, cleanup screen, dan pause saat kehilangan fokus.
- Adapter input mouse/touch; event mouse sintetis tidak menggandakan command touch.
- Lokasi data development terpisah (`MysticArenaRebuildDev`). Scene pertandingan awal menyimpan progres ke `user://level_progress_v1.json` setelah hasil; slot save Python tidak disentuh.
- Validator statis, runner tes native Godot, script PowerShell untuk Windows, dan workflow CI baru.

## Batas cakupan dan gap parity

`Pertandingan awal` adalah prototipe/QA, bukan pengganti penuh game Pygame. Katalog atau domain yang tersedia belum membuktikan semua level, UI, render, audio, save/cloud, pembayaran, dan alur Android telah terport serta teruji setara. Daftar gap dan bukti yang tersedia dipusatkan di [Status parity Godot ↔ Pygame](../docs/GODOT_PYGAME_PARITY_STATUS.md). Hindari menyimpulkan parity produksi dari keberadaan resource atau lolosnya validator statis saja.

## Struktur

```text
app/
  App.tscn                    Root aplikasi
  app.gd                      Navigasi dan lifecycle screen
scenes/menu/
  MainMenu.tscn               Menu yang dapat diedit lewat editor
  main_menu.gd               Signal tombol
scenes/match/
  Match.tscn                  Arena, HUD dan menu pause
  match.gd                    Adapter input dan UI pause
  arena_view.gd               Visual placeholder tanpa state gameplay
scenes/combat/
  MinionArena.tscn             Laboratorium minion dan HUD
  combat_screen.gd            Input, inspeksi, wave uji, pause
  minion_view.gd              Presentasi read-only
scenes/siege/
  SiegeArena.tscn             Mode tower & nexus
  siege_screen.gd             UI tim/wave, inspeksi dan hasil
  siege_view.gd               Visual bangunan/projectile read-only
scenes/prototype/
  PrototypeMatch.tscn         Pertandingan awal dengan build/sell dan hasil otomatis
  prototype_screen.gd        HUD/input/pause hasil; bukan UI wave manual
  prototype_view.gd          Slot/range dan view siege read-only
scripts/match/
  archer_upgrades.gd          Katalog resource Archer level 1–6
  nexus_upgrades.gd           Katalog nexus 1–5 + tabel scale/AI
  prototype_battle.gd         World pertandingan terbatas level 1 / normal
  wave_scheduler.gd          Clock, komposisi per-tier dan FIFO spawn
  match_economy.gd            Gold integer, income milli, debit/refund/ledger
  slot_layout.gd             Posisi 18 slot dari sumber
  build_slot.gd              Identitas/ownership dan struktur yang mengisi slot
  save_slot_store.gd         Tiga slot native, migrasi legacy dan kartu slot
  pygame_save_import.gd      Impor salinan slot save Pygame ke slot native
scripts/combat/
  siege_battle.gd             Perluasan combat: bangunan, projectile dan hasil
  structure_state.gd          Shield/regen dan aturan damage struktur
  projectile_state.gd         State hit yang masih dalam perjalanan
  minion_battle.gd            Simulasi deterministik tanpa dependency scene
  unit_state.gd               State tiap unit
  damage_rules.gd             Mitigasi/pembulatan dasar
scripts/data/
  lane_layout.gd              Port jalur dari sumber Python
  minion_definition.gd        Schema Resource stat minion
data/minions/                Lima resource .tres
data/structures/             Archer level 1–6 dan nexus level 1–5 (.tres)
scripts/simulation/
  prototype_session.gd       Command build/sale ID, cancel pause dan seleksi slot
  combat_session.gd          Penghubung physics tick ke world combat
  siege_session.gd           Antrean wave/tim dan batas lifecycle hasil
  sandbox_simulation.gd       Tick dan state penanda percobaan per instance
scripts/ui/
  rebuild_theme.gd            Theme dan helper presentasi
  menu_backdrop.gd            Artwork menu baru
assets/
  fonts/                     Salinan font yang sudah ada di repo Python
  icon.svg                   Ikon baru
tests/
  validate_project.py         Guardrail statis (Python stdlib)
  run_all.gd                  Runner native Godot, exit code nonzero jika gagal
  combat_checks.gd            Fixture, combat, batas unit dan determinisme
  siege_checks.gd             Shield/regen, projectile, siege, result dan replay
  upgrade_checks.gd          Tier/refund/volley/impact/cap dan guard transaksi
  upgrade_scene_checks.gd    UI quote/refund, stale command dan lifecycle
  upgrade_source_oracle.py   Metode asli upgrade/muzzle/volley Archer
  nexus_checks.gd            Tier/HP/shield/scaling/komposisi/AI dan guard
  nexus_scene_checks.gd      UI nexus, stale/pause/focus/result dan lifecycle
  nexus_source_oracle.py     Metode asli Castle/Minion/wave/AI
  prototype_checks.gd        Wave/ledger/transaksi, result dan replay
  match_source_oracle.py      Metode sumber wave/income/slot/build-sale
  structure_source_oracle.py  Metode sumber numerik Tower/Castle/muzzle
  check_source_contract.py    Membandingkan fixture dengan Python asli
  pygame_save_import_source_oracle.py  Arti 11 berkas slot save Pygame
  pygame_save_import_checks.gd         Impor slot Pygame vs fixture sumber
  fixtures/                  Snapshot stat dan 277 titik lane sumber
  run_windows.ps1             Import + tes native di Windows
```

Font disalin dari `assets/fonts/` di root repo, bukan dari hasil migrasi lama. Lisensi/distribusi font tetap perlu ikut audit aset sebelum rilis. Semua script memakai path `res://` di dalam proyek ini; sumber Python tidak diimpor saat runtime.

## Pengujian

### Status validasi (30 Oktober 2026, triase kegagalan native)

- **Suite native lulus penuh:** import engine **Godot 4.7.2** + **1.505.443 pemeriksaan** tanpa kegagalan dan tanpa `SCRIPT ERROR` pada commit `f4e840b` ([run 41019560561](https://github.com/dharmawantoxi/mystic-arena/actions/runs/41019560561)); 147 pemeriksaan di antaranya berasal dari suite impor slot Pygame (112 domain + 35 scene).
- **23 kegagalan run sebelumnya sudah ditriase:** roster hero kosong di awal pertandingan (sumber `Game.heroes = []`), minimum size tombol sumber yang membengkak karena teks native tak terlihat, palet menu 9bv18, dan baseline lifecycle yang tercemar suite yang berhenti karena `SCRIPT ERROR`. Rincian per gejala ada di [status parity](../docs/GODOT_PYGAME_PARITY_STATUS.md).
- **Validator statis:** 22.127 pemeriksaan lulus (`PASS: 22127 static checks`), termasuk guardrail dokumentasi status parity, inventaris folder `bosses/` (61 berkas, 216 bos), `hero_skills/` (2 berkas), `heroes/` (34 berkas, 27 direktor FX live) dan `levels/` (2 berkas, 54 level), bus FX + governor beban combat, migrasi legacy slot save, impor slot Pygame, dan tombol impor di panel save.
- **Tetap belum diverifikasi:** tampilan GPU/screenshot berpasangan, resize secara visual, Windows fisik, touchscreen, Android, audio, dan performa perangkat. CI headless bukan pengganti tes ini.

### Status validasi (25 September 2026, sesi nexus)

- **Checkpoint merged `main`:** import engine **Godot 4.7.2**, **1.905 pemeriksaan** pada commit `7c96c83` ([run 36153883271](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36153883271)), annotation **Native Godot tests**.
- **Sesi baru `arena/01a0d939-mystic-arena`:** **3.418 pemeriksaan** lulus pada commit `4f2cfac` ([run 36157499177](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36157499177)), termasuk suite nexus + seluruh suite lama. Check-run `108145527681`.
- **Jalur Cannon:** **3.713 pemeriksaan** lulus pada commit `81765fd` ([run 36204985361](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36204985361)), termasuk suite Cannon (domain + UI) + seluruh suite lama.
- **Jalur Ice:** **4.035 pemeriksaan** lulus pada commit `3e8ad59` ([run 36207205305](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36207205305)), termasuk suite Ice (domain + UI) + seluruh suite lama.
- **Jalur Mage:** **4.452 pemeriksaan** lulus pada commit `f1b80b9` ([run 36208792355](https://github.com/dharmawantoxi/mystic-arena/actions/runs/36208792355)), termasuk suite Mage (domain + UI) + seluruh suite lama.
- **Lulus lokal:** 667 guardrail statis; kontrak minion/lane/bangunan/wave/income/slot/upgrade Archer plus oracle nexus (tier/HP/shield/scaling/komposisi/AI) terhadap Python; parsing/lint/format GDScript.
- **Belum diverifikasi:** tampilan GPU/screenshot, resize secara visual, Windows fisik, touchscreen, Android dan performa perangkat. CI headless bukan pengganti tes ini.

Unduhan binary di sandbox masih terkendala TLS, tetapi tes runtime berhasil dijalankan pada runner GitHub. Hasil native yang dahulu tertunda pada tahap 1 sekarang sudah ada. Lihat workflow terbaru pada branch untuk hasil perubahan setelah checkpoint tersebut.

### Cara mudah di Windows

Buka PowerShell di folder `godot_rebuild`. Ganti lokasi executable sesuai instalasi kamu (disarankan varian `_console.exe`):

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\run_windows.ps1 -Godot "C:\Tools\Godot_v4.7.2-stable_win64_console.exe"
```

ExecutionPolicy di atas hanya berlaku untuk proses PowerShell tersebut; script tidak mengubah kebijakan Windows secara global. Script akan memeriksa versi engine, mengimpor aset, menjalankan tes, dan berhenti dengan error jika import/tes gagal. Tidak perlu memasang Python untuk tes native ini.

Atau jalankan langsung:

```powershell
$Godot = "C:\Tools\Godot_v4.7.2-stable_win64_console.exe"
& $Godot --headless --path . --editor --import
& $Godot --headless --path . --script res://tests/run_all.gd
```

Pastikan import tidak menampilkan `ERROR` dan runner mengeluarkan `PASS: ... checks`. Exit code saja pada tahap import tidak cukup.

### Cakupan tes native yang sudah dijalankan di CI

- Nexus 1–5: tier/harga, formula HP + bonus 500/cap, shield resize hanya-bila-purchased, `set_wave` 10/11, 25 scaling minion, komposisi 5 tier, 20 kasus AI, queue-tetap-scaling-berubah, guard stale/max/poor/dead/enemy/result, UI nexus/pause/focus/restart.
- Cannon 2–6: pilihan jalur eksplisit, stat/refund 5 tier, muzzle exact 5×2, volley tunggal splash+burn, boundary splash, burn stacking/tick 3-5-4-4, kredit korban, guard path/stale/max/poor/dead/enemy/result, UI pilih-jalur/pause/focus/restart.
- Ice 2–6: tombol kontekstual, stat/refund 5 tier, muzzle kristal exact 5×8, volley tunggal slow, on-hit + AOE L6 tanpa damage, stacking weaker-longer, tick/speed/attack-cd, guard path/stale/max/poor/dead/enemy/result, UI visibilitas/pause/focus/restart.
- Mage 2–6: baris Paths, stat/refund 5 tier, muzzle kristal exact 5×8, chain 2–4 tanpa refill (order/cap/boundary), on-hit + clear-saat-mati, stacking 2 debuff, tick, regen anti-heal, guard path/stale/max/poor/dead/enemy/result, UI baris/pause/focus/restart.
- Archer level 1–6: resource/harga/refund, full heal/shield restore tanpa reset cooldown, resource isolation, 36 source volleys, whole-volley cap, impact/overkill, UI upgrade/stale-level/pause/focus/restart.

- Prototipe: dua trace source 3.800 tick, komposisi wave, 18 slot, 12 skenario income, source build/UI-sale prices, ledger dan backpressure.
- Transaksi: build/sale ganda, stale entity IDs, tower mati, ownership, saldo kurang, pelepasan slot, kill credit, projectile sale cancellation dan hasil freeze.
- Replay prototipe 4.200 tick; tiga lifecycle UI, capture immutable command, pause/focus, scaled mouse/touch adapter, HUD bounds, hasil kedua tim dan restart/cleanup.

- Tower/nexus: stat efektif, 60 fixture shield/armor/reduction, muzzle sumber, cooldown 35 tick, batas regen dan shield wave 10/11.
- Projectile: launch tanpa damage instan, satu impact, target/owner mati, TTL/cap dan kredit satu kali.
- Siege: endpoint menuju nexus, hasil membekukan world, replay deterministik dan tiga siklus UI/pause/restart/hasil.
- Seluruh 277 titik lane dan lima definisi minion dibandingkan fixture sumber Python.
- Damage, pembulatan Python, cooldown tepat 45 tick, tie target stabil, satu death/kredit dan pembersihan ID.
- Regen, cap spawn atomik, keluar rute tanpa reward, event terbatas, dua simulasi identik selama 2.400 tick.
- Tiga siklus laboratorium combat: pause, wave antrean, input berskala, restart, cleanup dan simulasi tanpa render.
- State terpisah antar instance, satuan gerak per tick, 600 langkah simulasi penanda.
- Penolakan gerak tanpa seleksi atau di luar bounds.
- Boot menu, aktivasi tombol Main ganda, satu screen aktif.
- Tick maju saat berjalan dan berhenti saat pause.
- Resume, focus loss, restart, pembebasan instance lama.
- Sepuluh siklus menu → arena → pause → restart → menu tanpa pertumbuhan jumlah node.
- Routing mouse melalui viewport, HUD tidak menembus ke dunia, Escape, touch adapter dan pengabaian mouse sintetis.

Tes touch adapter bukan pengganti tes multi-touch/safe area/lifecycle pada HP. Tes headless juga bukan validasi visual atau performa GPU.

### Pemeriksaan statis (opsional untuk pengembang)

Dari root repo:

```text
python godot_rebuild/tests/validate_project.py
python godot_rebuild/tests/check_source_contract.py
python godot_rebuild/tests/structure_source_oracle.py
python godot_rebuild/tests/match_source_oracle.py
python godot_rebuild/tests/upgrade_source_oracle.py
python godot_rebuild/tests/nexus_source_oracle.py
python godot_rebuild/tests/cannon_source_oracle.py
python godot_rebuild/tests/ice_source_oracle.py
python godot_rebuild/tests/mage_source_oracle.py
python godot_rebuild/tests/kaizen_source_oracle.py
python godot_rebuild/tests/ai_source_oracle.py
python godot_rebuild/tests/ai_draft_source_oracle.py
python godot_rebuild/tests/ai_upgrade_source_oracle.py
python godot_rebuild/tests/ai_shield_source_oracle.py
```

Untuk parser/linter, pasang `gdtoolkit==4.5.0` dalam virtualenv terpisah. Tidak perlu memasangnya di komputer pemain.

Workflow **Godot Rebuild (native, fresh project)** pada `.github/workflows/godot-rebuild.yml` hanya memeriksa proyek baru. Ia tidak menjalankan converter atau tes migrasi lama. Workflow menjalankan guardrail, import dengan engine 4.7.2, tes native, dan menyimpan log. Workflow telah lulus untuk fondasi, minion, tower/projectile/nexus, dan prototipe wave/ekonomi/build-sell. Ia terpicu pada push/PR yang menyentuh proyek baru atau sumber kontrak terkait. Parser pihak ketiga tidak menggantikan hasil engine.

## Pemeriksaan visual singkat

1. F5 menampilkan judul Mystic Arena, Pertandingan awal, Tower & nexus, Laboratorium minion, Uji input, dan Keluar.
2. Pada jendela 1624×720 (default) menu memakai arena 1280 px di kiri + dinding batu 344 px di kanan; pada PC layar sentuh, pertandingan menampilkan dock PAUSE/STATUS/HEROES/TACTICAL. Angkanya bisa diukur dengan `tools/measure_android_screenshot.py --compare <file.png> --kind menu|match`.
3. Resize ke rasio berbeda: tampilan tetap proporsional, letterbox diperbolehkan.
4. Buka **Uji input**; pilih penanda, klik kanan, pastikan marker bergerak.
5. Buka **Laboratorium minion**; pastikan tiga lane terlihat, unit bergerak/menyerang, HP turun; tambah wave dan inspeksi unit.
6. Klik panel HUD: penanda tidak hilang seleksinya karena klik tembus.
7. Esc: angka tick harus berhenti; Lanjutkan: angka tick maju lagi.
8. Alt+Tab: arena pause ketika kehilangan fokus.
9. Restart mengembalikan penanda ke posisi awal tanpa seleksi.
10. Buka **Tower & nexus**, inspeksi bangunan, kirim wave satu tim, amati projectile dan shield/HP.
11. Buka **Pertandingan awal**, pilih slot biru, bangun/jual Archer, amati wave otomatis dan gold. Upgrade Archer dan periksa perubahan harga/refund/HP/shield serta jumlah panah. Pilih nexus biru, upgrade ke level 2+ dan amati HP/shield/komposisi/minion menguat. Pause harus membekukan keduanya; restart mengembalikan 1000 G dan nexus level 1.
12. Kembali ke menu, ulangi. Periksa Debugger untuk error dan Remote tree untuk screen sisa.

## Status roster hero

Registry native mencakup 222 ID hero, dengan tes domain/source untuk kit yang diimplementasikan. Daftar ID dan cakupan per hero: [HERO_ROSTER_STATUS.md](HERO_ROSTER_STATUS.md). Registry/domain coverage bukan klaim bahwa semua kit sudah setara secara visual, playable dalam campaign, atau lulus Android runtime; lihat [status parity](../docs/GODOT_PYGAME_PARITY_STATUS.md).

## Katalog level 1–54 (data, belum 54 level playable)

`data/levels/level_1.json` sampai `level_54.json` kini disalin dari literal
`LEVEL_1`–`LEVEL_54` pada `levels/level_data.py` melalui oracle AST
`tests/level_catalog_source_oracle.py`. `scripts/match/level_catalog.gd`
menyediakan lookup, syarat unlock dan nomor level berikutnya. PrototypeBattle
sekarang menerima `configure_level(n)` **hanya sebelum** `setup_arena()`;
konfigurasi valid memperbarui AI level, multipliers, jadwal boss dan saldo
awal/passive income sesuai level serta difficulty. Ledger awal hanya diganti
sebelum pertandingan/transaksi; ID tak dikenal atau pergantian di tengah match
ditolak tanpa mutasi. `PrototypeSession.configure_level(n, difficulty)` meneruskan pilihan sebelum
node masuk scene tree. Menu playable tetap default level 1; opsi ini baru
tersedia bagi adapter/test yang membuat session secara eksplisit. Oracle
juga memastikan semua 216 referensi boss level ada di katalog native.
Oracle ekonomi mengeksekusi fungsi sumber
read-only dan merekam 162 kombinasi (54 level × 3 difficulty); suite native
menguji seluruh saldo awal/passive income selain katalog, seleksi, penolakan
dan reset AI. Jalankan oracle tanpa
`--write` untuk mendeteksi drift. Menu kini menawarkan 54 konfigurasi dengan
unlock berdasarkan predecessor dan mengunci difficulty sesuai run yang
tersimpan. Level 2–54 adalah **mode uji eksperimental**, bukan parity penuh:
277 titik jalur lane dan 61 titik spline sungai tetap dari sumber Python.
Terrain diagonal + detail memakai **8.091 perintah sumber**, tiga lane
**6.654**, sungai **1.878**, dan border/spike **1.323**; semua layer diraster
sekali per scene/tema. Terrain Python mengambil angka acak visual untuk
speckle, jadi oracle memakainya dengan seed visual terpisah `20260929`;
lingkaran/garis 1px dan edge spike memakai rasterizer Godot sehingga piksel
tepi bisa berbeda dari Pygame. `level_theme_source_oracle.py` menjaga 25
warna untuk 54 tema, sedangkan oracle terrain/river/lane/wall menjaga urutan
perintah sumber tanpa mengimpor Pygame. Laboratorium tidak diubah. Animasi
air, dekorasi, fog, FX, balance dan visual GPU masih perlu validasi.

## Progres level (domain + save pengembangan terpisah)

`scripts/match/level_progress.gd` memindahkan kebijakan reward
`Game._grant_meta_reward`: kalah 0, menang pertama memakai reward level,
replay menang pertama memakai reward replay, replay berikutnya memakai 200
(atau override level), menandai completion dan membuka kunci difficulty
setelah 54 completion. Hasil adalah salinan state tanpa mutasi masukan;
ID level di luar katalog ditolak. Tes native mencakup semua 54 reward level,
replay, loss, dan unlock akhir. `PrototypeBattle.claim_level_result(state)`
menjadi batas hasil match eksplisit dan menolak klaim kedua. Scene memakai
`commit_level_result` agar penulisan development-save mendahului penandaan
klaim. Belum terhubung ke `SaveManager` Python, pembelian permanen atau
auto-unlock boss; jangan membayar reward langsung dari tiap tick.

## Penyimpanan progres pengembangan (belum terhubung ke scene)

`level_progress_store.gd` menyiapkan file **terpisah**
`user://level_progress_v1.json`, bukan slot Python lama. Format dibungkus
versi 1; input yang tidak valid ditolak. Penulisan memakai file sementara dan
backup sebelum mengganti file utama. Bila proses berhenti setelah backup
dibuat, `load_state()` membaca backup dan `recover_backup()` dapat
memulihkannya sebelum menulis lagi. Tes native memakai path
`user://level_progress_test_only.json` dan `user://level_claim_test_only.json`
lalu menghapusnya, tidak menyentuh progres pengguna. World menyediakan
`commit_level_result(path)` yang memuat state, menghitung reward, menyimpan,
dan hanya menandai klaim selesai **setelah write sukses**. Scene pertandingan
awal memanggilnya saat hasil dan menampilkan reward pada overlay. Save rusak
atau backup belum dipulihkan menampilkan kegagalan dan tombol coba lagi;
file lama tidak ditimpa otomatis. Ini **hanya progres development Godot**:
sinkronisasi cloud dan save Python yang berjalan langsung belum ada (impor
salinan slot Pygame dibahas di bagian berikutnya), begitu pula reward
boss/shop permanen dan parity map/theme. Uji juga pada Windows sebelum distribusi.

## Impor slot save Pygame (panel save, oracle, suite scene)

`scripts/match/pygame_save_import.gd` memindahkan arti berkas slot Pygame
(`SAVE_DIR/slot_1.json`…`slot_3.json`) ke envelope slot native. Berkas sumber
tidak dibaca langsung dari direktori Android lama dan tidak pernah diubah:
pemain/QA menyalinnya ke `user://pygame_slot_1.json` (atau nama apa pun), lalu
modul ini memetakan dan menuliskannya lewat `SaveSlotStore.save_state`, jadi
envelope berversi, rename atomik dan notifikasi cloud tetap dipakai.

API: `normalize(source, now)` memetakan dictionary slot Pygame ke state Godot
plus `report` berisi setiap nilai yang dibuang; `preview(source, now)` membuat
ringkasan kartu slot (gold, level tertinggi, jumlah hero/boss, playtime);
`import_file(source_path, slot, template, now, overwrite)` adalah jalur tulis
dan menolak dengan alasan `invalid_slot`, `missing_source`, `invalid_json`,
`not_a_save`, `corrupt_meta_gold`, `slot_occupied` atau `write_failed`. Slot
yang sudah terisi tidak pernah ditimpa tanpa `overwrite = true`.

Aturan yang diikuti dari `_system.py::SaveManager`: backfill 10 kunci default
`load()` (waktu `slot_created`/`slot_last_played` memakai waktu impor bila
hilang), batas level 54, daftar 222 hero di `data/heroes`, field
`LevelStats.INTEGER_FIELDS`, `run_difficulty` `normal`/`hard`, dan penanda
`slot_last_played` saat menyimpan. Ledger `replay_reward_counts` (khusus
Godot) mulai kosong dan state diberi `import_source = "pygame"`.

Perbedaan yang disengaja terhadap Pygame, semuanya dicatat di
[Status parity](../docs/GODOT_PYGAME_PARITY_STATUS.md): berkas rusak/JSON bukan
objek **ditolak** (Pygame diam-diam mengembalikan profil kosong lalu menimpa
berkas itu), nilai yang tidak bisa disimpan envelope native dibuang satu per
satu dan dilaporkan (Pygame menyimpannya apa adanya), dan `meta_gold` negatif
atau bukan angka menolak seluruh impor. Entri `level_stats` rusak mengikuti
kontrak Godot: `get_level_stats` memvalidasi lalu jatuh ke `empty_stats()`.

Bukti: `tests/pygame_save_import_source_oracle.py` menjalankan `SaveManager`
asli dari AST terhadap 11 berkas slot (profil lengkap, save lama, angka float,
hero asing/duplikat, level di luar batas, statistik rusak, kesulitan asing,
gold negatif/string, JSON terpotong, JSON bukan objek) dan menyimpan hasilnya
di `tests/fixtures/pygame_save_import_source.json`. Suite
`tests/pygame_save_import_checks.gd` membandingkan impor dengan fixture itu
termasuk penulisan nyata ke `user://` dan pembersihannya.

### Tombol impor di layar save

Panel slot save kini punya baris **PYGAME SAVE IMPORT**: tombol `IMPORT`
membuka konfirmasi (slot yang cocok akan diganti, berkas Pygame tidak diubah),
lalu menu menjalankan `PygameSaveImport.import_staged_slots()` dan menampilkan
ringkasannya di panel (`Slot 1 imported: Level 4 · Hero Gold 7250`,
`Slot 2 refused: invalid_json`). Panel tetap request-only: ia hanya memancarkan
`import_requested` dan merender laporan; pembacaan berkas, penulisan slot,
`refresh_levels()` dan pemilihan slot tetap milik `MainMenu`/`SaveSlotStore`.
`configure_pygame_import_template()` memberi suite path `user://` terisolasi.

Alurnya diuji headless oleh `tests/pygame_save_import_scene_checks.gd` dengan
klik tombol sungguhan: konfirmasi dan pembatalan, impor tanpa berkas (tidak
menulis apa pun), slot 1 terimpor + slot 2 rusak ditolak tanpa menyentuh save,
kartu slot dan pilihan level/difficulty ikut menyegarkan, impor ulang mengganti
slot yang sama, dan hitungan node kembali ke baseline. **Belum diuji pada
perangkat Android nyata**, jadi migrasi pemain belum boleh diklaim selesai.

## Reset AI tanpa seed

`reset_ai()` tanpa argumen kini menghapus label seed lama dan me-randomize ulang
stream controller, builder, dan draft; level policy serta pool rekrutmen kembali
ke level yang dipilih (default prototipe: 1). `reset_ai(seed)` tetap deterministik.
Tes restart menjaga transisi seed → tanpa seed → seed. Perubahan ini belum
diverifikasi dengan engine Godot di lingkungan ini; jalankan suite native
pada Godot 4.7.2 sebelum menganggapnya lulus runtime.

## AIPlayer native (QA terhubung ke scene)

Policy berpikir/prioritas, pool/draft/reserve, adapter upgrade/shield red per
kandidat, pemilihan kandidat kills descending stabil, atribusi kill sumber,
item/forge, dan kontrol hero tersedia sebagai domain native. Pertandingan awal
menyalakan controller dengan seed replay tetap dan tombol **A** untuk toggle.
Metadata summon mencakup 222 ID dan registry kit native juga mencakup 222 ID,
namun ini belum berarti UI roster produksi atau balance final. Batas parity yang
tersisa dicatat di [AI_CONTRACT.md](AI_CONTRACT.md).

## Status dan gap

Lihat [Status parity Godot ↔ Pygame](../docs/GODOT_PYGAME_PARITY_STATUS.md) untuk temuan, bukti, dan acceptance criteria terkini. Kontrak domain di folder ini menjelaskan aturan dan deviasi per sistem; kontrak bukan pengganti perbandingan runtime/screenshot.

Sumber Pygame tetap read-only selama porting. Jika menemukan perbedaan, catat state, resolusi, langkah reproduksi, versi engine, dan screenshot dari kedua engine; perbaiki di `godot_rebuild/` setelah perilaku sumber terverifikasi.
