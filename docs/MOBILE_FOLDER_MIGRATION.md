# Status migrasi folder `mobile/` (Pygame → Godot)

**Tanggal:** 2026-10-30
**Sumber kebenaran:** `mobile/*.py` di root repo (read-only). Semua perbaikan parity dilakukan di `godot_rebuild/`.
**Kesimpulan:** dari **20 berkas** di `mobile/`, empat modul sudah diport sebelum putaran ini, **dua modul diport pada putaran ini** (`platform_utils.py`, `hud.py` — layer 9bv20/9bv21), lima tidak punya makna di Godot (API internal pygame/SDL), satu baru sebagian, dan sisanya (perkakas diagnostik + overlay pratinjau aset) belum diport.

Dokumen ini menjawab "apa isi folder `mobile/` dan mana yang sudah masuk Godot". Dokumen parity utama tetap [`GODOT_PYGAME_PARITY_STATUS.md`](GODOT_PYGAME_PARITY_STATUS.md).

## Ringkasan per berkas

| Berkas | Isi | Padanan Godot | Status |
|---|---|---|---|
| `platform_utils.py` (648) | Deteksi Android, mode tampilan tersimpan (`scaled_vsync`/`scaled`/`native`), safe area poni/gesture bar, mapping koordinat jendela ↔ logis, posisi popup panel kanan, `vibrate`/`keep_screen_on`/immersive, info perangkat, folder tulis | **BARU:** `scripts/platform/mobile_platform.gd` (layer 9bv20). Dinding batu panel tetap di `scripts/ui/panel_stone.gd`; aturan lebar dock di `scripts/ui/side_panel_layout.gd` | **Diport (layout & aturan)** — dikanonkan `tests/mobile_platform_source_oracle.py` + `tests/mobile_platform_checks.gd`. `present()` = tugas engine (`canvas_items`), immersive = export preset (deviasi terdokumentasi) |
| `sidepanel.py` (741) | Panel kanan: PAUSE, STATUS, HEROES, TACTICAL COMMANDS, hit-test, kadens 250 ms | `scripts/ui/side_panel.gd`, `side_panel_layout.gd`, `side_panel_checks.gd` (9as), bobot font 9bv19 | **Selesai** untuk geometri, teks, warna, enabled, hit-test, kadens |
| `hud.py` (333) | Tombol sentuh: PAUSE/FPS di bawah chip emas (hilang bila dock aktif), SKIP saat cinematic, REPLAY/NEXT LEVEL/MENU saat menang/kalah, BACK, padding 80 px, animasi tekan | **BARU:** `scripts/ui/touch_hud_layout.gd` (layer 9bv21) + `tests/touch_hud_source_oracle.py` + `tests/touch_hud_checks.gd` | **Layout/visibilitas/hit/aksi diport.** Painter (lingkaran, kapsul, glow radial, cincin cooldown) **belum** |
| `touch.py` (308) | Tap/hold 450 ms/drag/fling/double-tap, multi-touch, ambang slop | `scripts/input/touch_gesture_runtime.gd` + `tests/touch_gesture_source_oracle.py` | **Selesai** (oracle kronologis + suite native) |
| `combat_audio.py` (332) | 7 jenis SFX tempur + pemilihan berkas + volume tim | `scripts/audio/combat_audio.gd`, `audio_runtime.gd`, `audio_manager.gd` (9ar) | **Diport**; pemutaran nyata di perangkat belum diuji |
| `cloud_save.py` (781) | Cloud save Play Games lewat `cloud_status.json` yang dipoll | `scripts/match/cloud_save_runtime.gd`, `cloud_save_codec.gd` | **Domain diport**; jembatan platform Android/Play Games belum diuji di perangkat |
| `buildinfo.py` (41) | `BUILD_ID`/`BUILD_DATE` untuk memastikan APK yang diuji benar | — | **Belum** (kecil, belum ada penanda build di Godot) |
| `debug.py` (450) | Overlay debug 4 mode (OFF/RINGKAS/LENGKAP/GRAFIK), tombol FPS, log ke logcat | — | **Belum** |
| `perf.py` (1003) | Cache font + cache hasil `render()`, `SurfacePool`, preset Quality LOW/MEDIUM/HIGH + auto, `FrameTimer`, governor efek | `scripts/ui/render_cache.gd` (cache teks), `scripts/settings/adaptive_quality_*`, `frame_rate_limit_*` | **Sebagian.** `SurfacePool`/`FrameTimer` tidak ada padanan langsung (Godot tidak memakai Surface yang di-*pool*) |
| `spritecache.py` (168) | Cache Surface minion yang digambar ulang tiap frame | — | **N/A.** Di Godot unit digambar sebagai draw call, bukan raster per unit yang perlu di-cache. Bila perlu, jalur native-nya atlas/MultiMesh, bukan port kode ini |
| `fastblit.py` (138) | Jalur cepat alpha blit lewat blitter SDL | — | **N/A** (internal pygame/SDL) |
| `blitwatch.py` (81) | Pelacak alpha-blit besar di HP | — | **N/A** (internal pygame/SDL) |
| `diagnostics.py` (198) | Uji-diri performa: presentasi vs blit vs CPU gambar | — | **Belum.** Padanan yang masuk akal adalah layar benchmark native (`Performance.get_monitor`), bukan port kode pygame |
| `_bench_core.py` (434) | Mesin ukur ns/piksel untuk operasi blit pygame | — | **N/A** (mengukur operasi pygame yang tidak ada di Godot) |
| `bootcheck.py` (401) | Layar diagnostik sebelum game (hitung event sentuh, benchmark, ganti mode tampilan) | — | **Belum** (layar native, bukan port baris per baris) |
| `kaizen_review.py` (204) | Overlay pratinjau lembar aset hero (opt-in, F9) | — | **Belum** — perkakas pengembang, bukan fitur pemain |
| `vex_review.py` (159) | Sama untuk Vex (F10) | — | **Belum** — dev-only |
| `grimjaw_review.py` (158) | Sama untuk Grimjaw (F11) | — | **Belum** — dev-only |
| `sylara_review.py` (157) | Sama untuk Sylara (F7) | — | **Belum** — dev-only |
| `__init__.py` (17) | Docstring paket + urutan instalasi | — | **N/A** (tidak ada kode) |

Hitungan: **4 sudah ada**, **2 diport putaran ini**, **1 sebagian**, **1 N/A-kode kosong**, **5 N/A-internal pygame**, **4 belum (diagnostik/debug)**, **4 belum (dev-only)**.

## Yang diport putaran ini

### 1. `platform_utils.py` → `scripts/platform/mobile_platform.gd` (9bv20)

Fungsi murni yang diport apa adanya, dengan nilai pembanding dari sumber asli:

* `window_scale_offset` — `min(w/1280, h/720)` + offset letterbox. Fixture: 1624×720 → skala 1,0 offset (172, 0); 2436×1080 → 1,5 offset (258, 0); 1024×768 → 0,8 offset (0, 96).
* `window_to_logical` / `finger_to_logical` / `pointer_to_logical` — mode `native` memetakan, `scaled_*` mengembalikan titik apa adanya.
* `safe_area(touch_mode)` — `(28, 10, 1224, 700)` di mode sentuh, `(0, 0, 1280, 720)` di desktop.
* `panel_popup_pos` / `panel_pos_bawah` — jalur popup panel kanan: `(1294, 277)` untuk 316×165, `(1294, 430)` untuk jalur bawah, `null` bila popup lebih lebar dari panel.
* `resolve_display_mode` / `load_display_mode` / `save_display_mode` — env `MYSTIC_DISPLAY_MODE`, lalu `display_mode.txt`, lalu `scaled_vsync`.
* `vibrate`, `keep_screen_on`, `writable_dir`, `device_info` — pembungkus tipis ke `Input.vibrate_handheld`, `DisplayServer.screen_set_keep_on`, `OS.get_user_data_dir`, `OS.get_model_name`/`OS.get_version`.

Deviasi yang disengaja: `enable_immersive_mode()` tidak punya padanan runtime (mode immersive diatur export preset Android Godot), dan `present()` tidak perlu diport karena penskalaan frame dikerjakan `canvas_items`.

### 2. `hud.py` → `scripts/ui/touch_hud_layout.gd` (9bv21)

* `build(safe)` — tujuh tombol dengan rect dan *hit rect* sumber (inflate 24 px lalu lantai 80 px): di mode sentuh PAUSE `(34,158,52,52)` dengan hit `(20,144,80,80)`, FPS `(118,158)`, SKIP `(1082,636,160,58)`, REPLAY `(330,610,165,62)`, NEXT LEVEL `(525,610,200,62)`, MENU `(755,610,165,62)`, BACK `(36,16,104,58)`.
* `sync(...)` — aturan visibilitas sumber: PAUSE hanya saat `playing` tanpa cinematic dan tanpa dock; FPS mengikuti tombol debug dan juga tampil di luar gameplay; SKIP saat cinematic; REPLAY/MENU saat menang/kalah; NEXT LEVEL hanya bila ada level berikutnya; animasi tekan turun 0,12 per sync.
* `hit_test` / `blocks` — urutan terakhir-digambar-menang, tombol tersembunyi tidak menjawab, dan penekanan memicu animasi (kuirk sumber: `blocks()` ikut menganimasikan).
* `action_intent` — padanan `apply_hud_action`: pause/FPS/SKIP/REPLAY/NEXT LEVEL/MENU/BACK + tactical (khusus `protect_tower` hanya meneruskan tower biru yang sedang terpilih).

Kuirk sumber yang dipertahankan: `sync` **tidak pernah** menampilkan BACK (harus dipicu pemanggil lain), dan FPS tetap tampil di layar menu.

## Sisa pekerjaan, urut prioritas

1. **Painter HUD sentuh** (9bv22): lingkaran/kapsul + glow radial + cincin cooldown + label bold, termasuk cabang `Quality.cheap_alpha`, lalu memasang HUD ini di `prototype_screen` hanya saat mode sentuh.
2. **`buildinfo.py` + `debug.py`**: penanda build dan overlay FPS 4 mode (butuh `FrameTimer` yang hilang dari `perf.py`).
3. **Layar diagnostik native**: `bootcheck.py`/`diagnostics.py` sebagai scene benchmark Godot (`Performance.get_monitor`), bukan port pygame.
4. **Overlay pratinjau aset** (4 berkas `*_review.py`): hanya bila memang dipakai untuk review seni di Godot.
5. **Bukti perangkat**: vibrate/keep-screen-on/safe area dan cloud save baru terbukti di kode + oracle; belum ada uji di perangkat Android.

## Bukti

* `python3 godot_rebuild/tests/mobile_platform_source_oracle.py` — menjalankan `platform_utils.py` asli di bawah shim pygame; 6 ukuran jendela, 30 titik jendela + 18 titik jari, 9 titik pointer, 6 kasus popup, 6 kasus mode tampilan.
* `python3 godot_rebuild/tests/touch_hud_source_oracle.py` — menjalankan `TouchHUD` asli; 4 konfigurasi layout, 7 keadaan permainan, 13 kasus hit-test, 33 kasus aksi.
* `python3 godot_rebuild/tests/validate_project.py` — guardrail statis untuk kedua layer.
* Kedua suite native terdaftar di `godot_rebuild/tests/run_all.gd`.

Batas: tidak ada executable Godot di lingkungan kerja ini, jadi suite native dijalankan CI/PC pengguna; yang bisa dibuktikan di sini adalah oracle sumber, port, dan pemeriksaan statis.
