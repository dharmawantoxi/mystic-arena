# Migrasi `_system.py` ke Godot

`_system.py` adalah berkas **1.125 baris** di root repo yang berisi **lima modul sistem** pygame yang digabung: `performance.py`, `fps_counter.py`, `fps_limiter.py`, `sound_manager.py` dan `save_manager.py`, plus prelude dua helper path audio. Dokumen ini mencatat bagaimana seluruh isinya diklasifikasikan dan dibuktikan di rebuild Godot.

Sumber kebenaran: `godot_rebuild/tests/system_source_oracle.py`. Oracle **mengimpor modul aslinya** (stub `pygame` dengan mixer perekam, namespace `settings.py` dari `_core.py`, `storage_paths.SAVE_DIR` sementara dan jam dibekukan di 1700000000) lalu mengeksekusi culler, grid, overlay FPS, governor adaptif lama, seluruh jalur volume/throttle audio dan siklus hidup slot save. Fixture: `tests/fixtures/system_source.json`. Suite native: `tests/system_checks.gd` (dijalankan `run_all.gd`).

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `_system.py` | 1125 |
| Seksi gabungan (prelude + 5 modul) | 6 |
| Kelas | 6 |
| `def` di kelas | 47 |
| Fungsi top-level | 3 |
| Assign modul | 4 |
| Simbol terklasifikasi | 66 |
| Kasus cull dieksekusi | 13 titik batas |
| Kueri grid dieksekusi | 8 (lokal) + 2 (modul global) |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 51 | ada padanan fungsi/konstanta di modul Godot target |
| `data` | 5 | tabel/konstanta data (path audio, grid, jumlah slot) |
| `deviation` | 2 | perilaku sengaja berbeda, didokumentasikan |
| `dead` | 8 | tidak dipakai build yang dikirim (overlay F8 legacy) |
| `folded` | 0 | dijalankan alur modul pengganti tanpa fungsi 1:1 |

## 2. Peta enam seksi

| Seksi | Baris | Baris total | Modul pygame | Target Godot |
| --- | --- | --- | --- | --- |
| `prelude` | 1–28 | 28 | — (prelude path audio) | `scripts/audio/audio_manager.gd` |
| `performance` | 29–188 | 160 | `performance.py` | `scripts/combat/spatial_grid.gd` + `scripts/ui/frustum_cull.gd` |
| `fps_counter` | 189–387 | 199 | `fps_counter.py` | **dead** — hanya `main_desktop_legacy.py` |
| `fps_limiter` | 388–449 | 62 | `fps_limiter.py` | `scripts/settings/adaptive_quality_controller.gd` (governor aktif `mobile/perf.py`) + `frame_rate_limit_runtime.gd` |
| `sound_manager` | 450–731 | 282 | `sound_manager.py` | `scripts/audio/audio_manager.gd` + `combat_audio.gd` |
| `save_manager` | 732–1125 | 394 | `save_manager.py` | `scripts/match/save_slot_store.gd` + `level_stats.gd` + `level_progress_store.gd` |

## 3. Kelas

| Kelas | Baris | `def` | Kind | Modul native |
| --- | --- | --- | --- | --- |
| `FrustumCuller` | 40 | 1 | `ported` | `frustum_cull.gd` |
| `SpatialGrid` | 52 | 4 | `ported` | `spatial_grid.gd` |
| `FPSCounter` | 202 | 6 | `dead` | `—` |
| `AdaptiveQuality` | 400 | 4 | `deviation` | `adaptive_quality_controller.gd` |
| `SoundManager` | 463 | 15 | `ported` | `audio_manager.gd` |
| `SaveManager` | 750 | 17 | `ported` | `save_slot_store.gd` |

## 4. Klasifikasi per simbol

Setiap simbol punya **target + token**; token harus benar-benar ada di berkas target (validator statis memeriksanya).

### 4.1 `prelude` (1–28)

Modul: `data` → `godot_rebuild/scripts/audio/audio_manager.gd` — folder sound + resolver path berkas audio.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `top:_sound_path@21` | `ported` | `audio_manager.gd` | `const ROOT := "res://assets/audio/"` | resolusi berkas audio |
| `assign:_SOUND_DIR` | `data` | `audio_manager.gd` | `const ROOT := "res://assets/audio/"` | folder berkas audio |

### 4.2 `performance` (29–188)

Modul: `ported` → `godot_rebuild/scripts/combat/spatial_grid.gd` — culler + grid + dua helper modul.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:FrustumCuller` | `ported` | `frustum_cull.gd` | `static func is_visible(` | margin 80 px di luar 1280x720 |
| `class:FrustumCuller.is_visible` | `ported` | `frustum_cull.gd` | `static func is_visible(` | predikat cull yang sama |
| `class:SpatialGrid` | `ported` | `spatial_grid.gd` | `func query_range(` | bucket 60 px, satu sel per entitas |
| `class:SpatialGrid.__init__` | `ported` | `spatial_grid.gd` | `func _init(` | cell_size 60 |
| `class:SpatialGrid.clear` | `ported` | `spatial_grid.gd` | `func clear(` | — |
| `class:SpatialGrid.insert` | `ported` | `spatial_grid.gd` | `func insert(` | satu bucket per entitas |
| `class:SpatialGrid.query_range` | `ported` | `spatial_grid.gd` | `func query_range(` | urutan cx-luar, cy-dalam, box lalu jarak kuadrat |
| `top:update_spatial_grid@147` | `ported` | `spatial_grid.gd` | `static func update_spatial_grid(` | hanya minion + hero yang hidup |
| `top:query_enemies_in_range@170` | `ported` | `spatial_grid.gd` | `static func query_enemies_in_range(` | filter musuh di dalam loop kueri |
| `assign:_grid` | `data` | `spatial_grid.gd` | `static var _shared: SpatialGrid` | singleton grid cell_size 60 |

### 4.3 `fps_counter` (189–387)

Modul: `dead` → `—` — hanya dipakai main_desktop_legacy.py; build Android memakai DebugOverlay.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:FPSCounter` | `dead` | `—` | `—` | overlay F8 hanya di entry desktop legacy (bukan build Android) |
| `class:FPSCounter.__new__` | `dead` | `—` | `—` | singleton overlay legacy |
| `class:FPSCounter.__init__` | `dead` | `—` | `—` | state overlay legacy |
| `class:FPSCounter._get_font` | `dead` | `—` | `—` | cache font overlay legacy |
| `class:FPSCounter.toggle` | `dead` | `—` | `—` | tombol F8 hanya ada di entry desktop legacy |
| `class:FPSCounter.update` | `dead` | `—` | `—` | sampel FPS overlay legacy |
| `class:FPSCounter.draw` | `dead` | `—` | `—` | panel FPS legacy |

### 4.4 `fps_limiter` (388–449)

Modul: `deviation` → `godot_rebuild/scripts/settings/adaptive_quality_controller.gd` — varian tick() lama; governor aktif = mobile/perf.py.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:AdaptiveQuality` | `deviation` | `adaptive_quality_controller.gd` | `const COOLDOWN_AFTER_LOWER := 180` | versi tick() 30 sampel ambang 50/35 digantikan governor aktif |
| `class:AdaptiveQuality.__new__` | `ported` | `adaptive_quality_runtime.gd` | `var controller = Controller.new()` | autoload runtime menggantikan singleton |
| `class:AdaptiveQuality._init` | `ported` | `adaptive_quality_runtime.gd` | `func _ready() -> void:` | inisialisasi runtime di _ready |
| `class:AdaptiveQuality.tick` | `ported` | `frame_rate_limit_runtime.gd` | `Engine.max_fps` | pacing pindah ke engine; sampel ke governor aktif |
| `class:AdaptiveQuality.get_fps` | `ported` | `adaptive_quality_runtime.gd` | `func update_fps(fps: float) -> void:` | governor aktif menerima fps dari engine |

### 4.5 `sound_manager` (450–731)

Modul: `ported` → `godot_rebuild/scripts/audio/audio_manager.gd` — BGM + SFX + voice + ambient.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:SoundManager` | `ported` | `audio_manager.gd` | `var master_volume := DEFAULT_MASTER_VOLUME` | single facade: musik, sfx, voice, ambient |
| `class:SoundManager.__new__` | `ported` | `audio_manager.gd` | `var music: AudioStreamPlayer` | autoload Node menggantikan singleton Python |
| `class:SoundManager.__init__` | `ported` | `audio_manager.gd` | `func _ready() -> void:` | mixer disiapkan di _ready |
| `class:SoundManager.load` | `ported` | `audio_manager.gd` | `func _stream(key: String) -> AudioStream:` | stream dimuat dari tabel STREAMS |
| `class:SoundManager.load_all` | `ported` | `audio_manager.gd` | `const STREAMS := {` | daftar berkas tetap menggantikan load_all() |
| `class:SoundManager.play` | `ported` | `audio_manager.gd` | `func play(` | — |
| `class:SoundManager.play_positional` | `ported` | `audio_manager.gd` | `func play_positional(` | — |
| `class:SoundManager.play_bgm` | `ported` | `audio_manager.gd` | `func play_music(key: String) -> void:` | musik loop di player khusus |
| `class:SoundManager.stop_bgm` | `ported` | `audio_manager.gd` | `func stop_all() -> void:` | musik dihentikan bersama kanal lain |
| `class:SoundManager.pause_bgm` | `ported` | `audio_manager.gd` | `func pause_music() -> void:` | stream_paused pada player musik |
| `class:SoundManager.resume_bgm` | `ported` | `audio_manager.gd` | `func resume_music() -> void:` | lanjutkan musik |
| `class:SoundManager.update_bgm_volume` | `ported` | `audio_manager.gd` | `func _apply_mix() -> void:` | mix master*bgm dihitung ulang |
| `class:SoundManager.play_ambient` | `ported` | `audio_manager.gd` | `func play_ambient(` | — |
| `class:SoundManager.stop_ambient` | `ported` | `audio_manager.gd` | `func stop_all() -> void:` | ambient ikut berhenti |
| `class:SoundManager.set_master_volume` | `ported` | `audio_manager.gd` | `func set_mix_volume(` | clamp 0..1 per kanal |
| `class:SoundManager.stop_all` | `ported` | `audio_manager.gd` | `func stop_all(` | — |

### 4.6 `save_manager` (732–1125)

Modul: `ported` → `godot_rebuild/scripts/match/save_slot_store.gd` — tiga slot + metadata + level stats.

| Simbol | Kind | Target | Token | Catatan |
| --- | --- | --- | --- | --- |
| `class:SaveManager` | `ported` | `save_slot_store.gd` | `const SLOT_COUNT := 3` | slot, metadata, migrasi legacy, level stats |
| `class:SaveManager.get_slot_file` | `ported` | `save_slot_store.gd` | `static func slot_path(` | pola slot_%d.json |
| `class:SaveManager.get_current_slot` | `ported` | `save_slot_store.gd` | `func get_current_slot(` | — |
| `class:SaveManager.set_current_slot` | `ported` | `save_slot_store.gd` | `func set_current_slot(` | — |
| `class:SaveManager.ensure_save_dir` | `ported` | `save_slot_store.gd` | `const PATH_TEMPLATE := "user://slot_%d.json"` | user:// sudah ada; tidak perlu makedirs |
| `class:SaveManager.slot_exists` | `ported` | `save_slot_store.gd` | `func slot_exists(` | — |
| `class:SaveManager.migrate_legacy_save` | `ported` | `save_slot_store.gd` | `static func migrate_legacy(` | legacy -> slot 1 tanpa menimpa |
| `class:SaveManager.save` | `ported` | `save_slot_store.gd` | `static func save_state(` | stempel slot_last_played + cloud upload |
| `class:SaveManager.load` | `ported` | `save_slot_store.gd` | `static func load_state(` | backfill field default |
| `class:SaveManager.get_empty_save` | `ported` | `save_slot_store.gd` | `static func empty_state(` | sepuluh field default yang sama |
| `class:SaveManager.delete_slot` | `ported` | `save_slot_store.gd` | `func delete_slot(` | — |
| `class:SaveManager.get_slot_info` | `ported` | `save_slot_store.gd` | `static func slot_info(` | metadata untuk UI slot |
| `class:SaveManager.get_all_slot_info` | `ported` | `save_slot_store.gd` | `static func all_slot_info(` | tiga slot, kosong = {} |
| `class:SaveManager.format_playtime` | `ported` | `save_slot_store.gd` | `func format_playtime(` | — |
| `class:SaveManager.format_last_played` | `ported` | `save_slot_store.gd` | `func format_last_played(` | — |
| `class:SaveManager.get_level_stats` | `ported` | `level_stats.gd` | `static func get_level_stats(` | default tujuh field |
| `class:SaveManager.update_level_stats` | `ported` | `level_stats.gd` | `static func update_level_stats(` | best score/time hanya saat menang |
| `class:SaveManager.format_time` | `ported` | `save_slot_store.gd` | `func format_time(` | — |
| `assign:NUM_SLOTS` | `data` | `save_slot_store.gd` | `const SLOT_COUNT := 3` | tiga slot save |
| `assign:LEGACY_SAVE_FILE` | `data` | `save_slot_store.gd` | `const LEGACY_PATH := ProgressStore.PATH` | progress.json lama -> slot 1 |

## 5. Perilaku yang dieksekusi oracle

### 5.1 Culler (`FrustumCuller`, baris 40–48, seksi `performance`)

`MARGIN` = 80 px, layar acuan 1280x720. Batas inklusif di kedua sisi: entitas pada jarak tepat `margin + radius` **masih** digambar; satu piksel di luarnya tidak.

| x | y | radius | terlihat (pygame) |
| --- | --- | --- | --- |
| 0 | 0 | 30 | True |
| 640 | 360 | 30 | True |
| -109.9 | 0 | 30 | True |
| -110 | 0 | 30 | True |
| -110.1 | 0 | 30 | False |
| 1389.9 | 719 | 30 | True |
| 1390 | 720 | 30 | True |
| 1390.1 | 0 | 30 | False |
| 0 | 820 | 100 | True |
| 0 | 820.1 | 100 | True |
| -1 | -1 | 0 | True |
| -80 | -80 | 0 | True |
| -80.1 | -80 | 0 | False |

### 5.2 Spatial grid (`SpatialGrid`, baris 52–183, seksi `performance`)

`cell_size` = 60; setiap entitas masuk **tepat satu** bucket (sel pusatnya), jadi kueri tidak pernah menduplikasi entitas. Urutan hasil = `cx` luar, `cy` dalam, urutan insert di bucket, dengan prefilter kotak lalu jarak kuadrat.

| Bucket | Entitas |
| --- | --- |
| `-1,0` | m8 |
| `0,0` | m6, m9 |
| `1,1` | m1, m10 |
| `1,2` | m4 |
| `1,3` | m5 |
| `2,1` | m2 |
| `3,1` | m3 |
| `3,3` | m7 |

| x | y | radius | team | hasil (urutan pygame) |
| --- | --- | --- | --- | --- |
| 100 | 100 | 50 | None | m1, m4, m2 |
| 100 | 100 | 50 | blue | m2 |
| 100 | 100 | 50 | red | m1 |
| 100 | 100 | 200 | None | m8, m6, m9, m1, m10, m4, m5, m2, m3, m7 |
| 0 | 0 | 120 | None | m8, m6, m9, m10 |
| -40 | 0 | 60 | None | m8 |
| 240 | 240 | 100 | red | — |
| 700 | 700 | 60 | None | — |

Modul global `update_spatial_grid()` meng-index hanya minion/hero hidup (6 bucket pada fixture), lalu `query_enemies_in_range()` menyaring musuh yang hidup di dalam loop yang sama:

| x | y | radius | team | hasil |
| --- | --- | --- | --- | --- |
| 100 | 100 | 60 | None | m9, m1, m10, m2 |
| 100 | 100 | 120 | red | m6, m9, m1 |

### 5.3 Overlay FPS dan governor adaptif

`FPSCounter`: singleton, riwayat 120 sampel, tampilan diperbarui tiap 10 frame dari 30 sampel terakhir. Fixture: frame 24 → fps 20.0, avg 47.0, min 20.0, max 60.0. Modul ini **dead** untuk build Android (hanya `main_desktop_legacy.py`).

`AdaptiveQuality` (varian `_system.py`): riwayat 30, ambang HIGH 50 / MEDIUM 35, kualitas baru dihitung setelah ≥10 sampel. Hasil eksekusi 36 frame skrip: high, medium. Governor yang benar-benar dipakai game adalah `mobile/perf.py` (ambang 26/52 + cooldown) yang sudah diport ke `adaptive_quality_controller.gd`.

### 5.4 Audio (`SoundManager`, seksi 450–731; kelas di baris 463)

Volume sumber: master 0.9, sfx 0.6, voice 0.5, bgm 0.35, ambient 0.25.

| Nama | Throttle (ms) |
| --- | --- |
| `goblin_spawn` | 200 |
| `minion_death` | 120 |
| `tower_destroyed` | 300 |
| `bullet_hit` | 40 |
| `nexus_hit` | 300 |
| `ui_click` | 50 |

Berkas yang dimuat: **16**; belum ada: bullet_hit.wav. Kategori: ambient_forest=ambient, goblin_spawn=voice (sisanya `sfx`).

| Panggilan | Tick | Jumlah suara setelahnya |
| --- | --- | --- |
| `ui_click` | 0 | 0 |
| `ui_click` | 30 | 0 |
| `ui_click` | 60 | 1 |
| `nexus_hit` | 80 | 1 |
| `nexus_hit` | 200 | 1 |
| `nexus_hit` | 400 | 2 |
| `minion_death` | 400 | 3 |
| `minion_death` | 450 | 3 |

Catatan penting: panggilan pertama pada tick 0 **ditolak** karena `now - last < throttle` dengan `last` bawaan 0 — sumber memang membisu pada milidetik pertama.

| Kanal | Suara | Volume | Loop | Fade (ms) |
| --- | --- | --- | --- | --- |
| 3 | `goblin_spawn.wav` | 0.35 | 0 | 0 |
| 4 | `ui_buy.wav` | 0.42 | 0 | 0 |
| 5 | `ui_buy.wav` | 0.21 | 0 | 0 |
| 6 | `ui_buy.wav` | 0.063 | 0 | 0 |
| 7 | `ui_buy.wav` | 0.1575 | 0 | 0 |

BGM: `bgm_battle.wav` volume 0.245 (master×bgm), loop `-1`, fade 3000 ms. Pause/resume menyalakan flag `bgm_paused` (True → False). Master 0.9 → volume musik 0.315; master 1.5 dijepit ke 1.0. Ambient `ambient_forest` volume 0.14 (master×ambient×0.8), lalu 0.225 setelah master 0.9; `stop_ambient(1200)` memanggil fadeout 1200 ms. `stop_all()` memanggil `mixer.stop()` 1x dan `music.stop()` 1x.

| x | player_x | jarak | main? | falloff | volume akhir (mult) |
| --- | --- | --- | --- | --- | --- |
| 100.0 | 100.0 | 0.0 | True | 1.0 | 1.0 |
| 400.0 | 0.0 | 400.0 | True | 0.5 | 0.5 |
| 760.0 | 0.0 | 760.0 | True | 0.15 | 0.15 |
| 800.0 | 0.0 | 800.0 | True | 0.15 | 0.15 |
| 900.0 | 0.0 | 900.0 | False | 0.0 | 0.0 |
| 200.0 | 0.0 | 200.0 | True | 0.75 | 0.375 |
| 0.0 | 0.0 | 0.0 | True | 1.0 | 1.0 |

### 5.5 Save (`SaveManager`, seksi 732–1125; kelas di baris 750)

3 slot (`slot_1.json`…`slot_3.json`), legacy `progress.json`. Default slot 1; `set_current_slot(2)` → 2, `set_current_slot(9)` tetap 2.

| Helper | Hasil pygame |
| --- | --- |
| `get_empty_save()` | 10 field: unlocked_bosses, purchased_heroes, meta_gold, completed_levels, last_played_level, slot_created, slot_last_played, slot_playtime_seconds, level_stats, run_difficulty |
| `migrate_legacy_save()` | True (kedua kali: False), arsip `progress_backup.json.old` |
| `save()` kunci slot | completed_levels, meta_gold, slot_created, slot_last_played |
| `load()` kunci hasil | completed_levels, last_played_level, level_stats, meta_gold, purchased_heroes, run_difficulty, slot_created, slot_last_played, slot_playtime_seconds, unlocked_bosses |
| `get_slot_info()` | slot 2, gold 123, level tertinggi 2 |
| `get_all_slot_info()` | terisi per slot: [True, True, False] |
| `format_playtime` | 0m, 0m, 1m, 59m, 1h 0m, 1h 1m, 2h 2m |
| `format_last_played` | Never, Just now, 2m ago, 2h ago, 1d ago, 06 Nov 2023, 22 Jul 2023 |
| `format_time` | --:--, 0:05, 1:05, 10:00, 59:59 |

Transaksi level stats (menang/kalah):

| Panggilan | Best score baru | Best time baru | total_attempts | wins | kills | max_combo | playtime |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `stats_loss` | False | False | 1 | 0 | 5 | 7 | 120 |
| `stats_win` | True | True | 2 | 1 | 14 | 11 | 210 |
| `stats_win_worse` | False | False | 3 | 2 | 15 | 11 | 240 |

## 6. Deviasi terdokumentasi

| # | Simbol | Deviasi | Bukti/uji |
| --- | --- | --- | --- |
| D1 | `FrustumCuller.is_visible` | culling diserahkan ke engine Godot (canvas culling); helper sumber tetap diport agar ambang 80 px dapat diuji | `system_checks.gd::_check_cull` (13 titik batas) |
| D2 | `SpatialGrid`, `update_spatial_grid`, `query_enemies_in_range` | grid diport + dites (termasuk urutan), tetapi jalur tempur Godot masih memakai scan langsung; himpunan hasil identik, urutan tie-break bisa berbeda | `system_checks.gd::_check_grid` |
| D3 | `_system.py::AdaptiveQuality` | varian `tick()` (30 sampel, ambang 50/35) tidak dipakai game; governor aktif `mobile/perf.py` (26/52 + cooldown) sudah diport | `adaptive_quality_source_oracle.py`, `adaptive_quality_controller.gd` |
| D4 | `FPSCounter` | overlay F8 hanya ada di `main_desktop_legacy.py`; build Android memakai DebugOverlay/preset Quality | `system_source_oracle.py` (dead) |
| D5 | `SoundManager.load`/`load_all`/`_sound_path` | Godot memakai tabel `STREAMS` + `assets/audio/`; berkas yang hilang dilewati tanpa log per-berkas | `audio_manager.gd::_stream` |
| D6 | `SoundManager.play` | pygame `find_channel(True)` (boleh mencuri kanal) → Godot memakai player `Effects` tunggal + pool 24 kanal tempur; `play_scaled` menerima `category` opsional (`sfx`/`voice`/`ambient`) yang di source dipilih lewat `_sound_categories`, jalur `sfx` tetap `master × sfx × volume_mult` | `audio_manager.gd::play_scaled` |
| D7 | `SaveManager` | `slot_created` dipertahankan dari disk, `get_slot_info` mengembalikan `{}` + `corrupt` (sumber `None`), `slot_exists` juga melihat `.bak`, arsip migrasi `*.migrated` (sumber `progress_backup.json.old`), `ensure_save_dir` tidak perlu untuk `user://` | `save_slot_store.gd` |
| D8 | `update_level_stats` | Godot mengembalikan salinan (`new_stats`) sedangkan sumber memberi dict tersimpan yang bermutasi (aliasing), dan transaksi menolak match dict tak lengkap | `system_checks.gd::_check_stats` |

## 7. Bukti & sinkronisasi

| Berkas | Isi |
| --- | --- |
| `tests/system_source_oracle.py` | inventaris + klasifikasi 66 simbol + eksekusi culler/grid/FPS/governor/audio/save |
| `tests/fixtures/system_source.json` | fixture (inventaris, klasifikasi, cull, grid, fps, adaptive, sound, positional, save) |
| `tests/system_checks.gd` | replay native: token target, cull, urutan grid, throttle/volume, format slot, transaksi stats |
| `scripts/combat/spatial_grid.gd` | port `SpatialGrid` + `update_spatial_grid` + `query_enemies_in_range` |
| `scripts/ui/frustum_cull.gd` | port `FrustumCuller` |
| `scripts/audio/audio_manager.gd` | tambahan `THROTTLE_MS`, `VOICE_VOLUME`, fade, `play_positional`, `stop_all`, pause/resume |
| `tests/validate_project.py` (blok `9ci`) | fixture == eksekusi Python, semua target/token hidup, wiring modul baru |
| `.github/workflows/godot-rebuild.yml` | `python godot_rebuild/tests/system_source_oracle.py --check` |

Sinkronisasi fixture:

```bash
python godot_rebuild/tests/system_source_oracle.py --write   # setelah mengubah oracle
python godot_rebuild/tests/system_source_oracle.py --check   # dipakai CI + validator
python godot_rebuild/tests/validate_project.py               # blok 9ci
```

