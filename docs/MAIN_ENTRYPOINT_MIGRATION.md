# Migrasi `main.py` ke Godot

`main.py` (737 baris) adalah **entry point** Pygame versi Android/touchscreen: mixer pre-init, display, state machine `splash → menu → game ↔ pause`, loop fixed-timestep dengan catch-up, penanganan lifecycle Android, panel kanan, overlay debug/review, dan banner startup. Tidak ada kelas di dalamnya — 4 fungsi, 7 assign modul, 1 guard `__main__`, dan 23 impor.

Port shell-nya sudah tersebar di layer-layer sebelumnya: `app/app.gd` memegang state machine + transisi level, `scripts/settings/frame_rate_limit_runtime.gd` memegang clamp FPS, `scripts/settings/adaptive_quality_runtime.gd` memegang preset kualitas, `scripts/platform/mobile_platform.gd`, `scripts/input/touch_gesture_runtime.gd`, `scripts/ui/touch_hud_layout.gd`, `scripts/ui/side_panel.gd` dan `scripts/audio/combat_audio.gd` memegang sisi mobile-nya. Layer **9cn** menutup sisanya: **seluruh 35 simbol diklasifikasikan eksplisit**, ditambah tiga hal yang belum punya rumah native sama sekali — log frame error ber-rate-limit, banner startup, dan dua konstanta loop (`MAX_CATCHUP`, mixer rate) yang sebelumnya memakai default engine.

Sumber kebenaran: `godot_rebuild/tests/main_source_oracle.py` (AST, karena `main.py` memanggil `pygame.init()` saat import). Fixture: `tests/fixtures/main_source.json`. Suite native: `tests/main_shell_checks.gd`.

## 1. Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Baris `main.py` | 737 |
| Kelas | 0 |
| Fungsi | 4 (`_log_frame_error`, `_cinematic_active`, `_handle_background`, `main`) |
| Assign modul | 7 (+1 guard `__main__`) |
| Impor | 23 |
| Simbol terklasifikasi | **35** (23 impor + 4 fungsi + 7 assign + guard) |
| State | 4 (`splash`, `menu`, `game`, `pause`) |
| Keybinding dev | 6 (F7, F8, F9, F10, F11, ESC) |
| Baris banner startup | 8 |

| Kind | Jumlah | Arti |
| --- | --- | --- |
| `ported` | 13 | punya padanan native dengan token hidup |
| `folded` | 11 | perilakunya hidup di modul native lain (mis. `main` → `app/app.gd`) |
| `baked` | 3 | digantikan engine (`pygame`, `perf`, `screen`) |
| `data` | 1 | konstanta tunable (`_FRAME_ERR_COOLDOWN`) |
| `deviation` | 7 | alat dev Android/opt-in yang tidak diport (D5, D6) |

## 2. Klasifikasi simbol

| Simbol | Kind | Target native | Token bukti |
| --- | --- | --- | --- |
| `os` | folded | `scripts/app/frame_error_log.gd` | `FileAccess.open(` |
| `sys` | folded | `app/app.gd` | `get_tree().quit()` |
| `pygame` | baked | — | digantikan scene tree + engine |
| `mobile.platform_utils` | ported | `scripts/platform/mobile_platform.gd` | `static func is_touch_mode()` |
| `mobile.perf` | baked | — | hot-patch font/blit tidak ada padanannya; preset kualitas di `adaptive_quality` |
| `mobile.touch` | ported | `scripts/input/touch_gesture_runtime.gd` | `func touch_down(` |
| `mobile.hud` | ported | `scripts/ui/touch_hud_layout.gd` | `static func action_intent(` |
| `mobile.debug` | deviation | — | overlay opt-in `MYSTIC_DEBUG` (D5) |
| `mobile.diagnostics` | deviation | — | layar self-test digantikan suite native (D6) |
| `mobile.bootcheck` | deviation | — | layar diagnostik `MYSTIC_BOOTCHECK` (D6) |
| `mobile.combat_audio` | ported | `scripts/audio/combat_audio.gd` | `func new_frame()` |
| `mobile.sidepanel` | ported | `scripts/ui/side_panel.gd` | `func is_active()` |
| `mobile.kaizen_review` | deviation | — | sheet review F9 (D5) |
| `mobile.vex_review` | deviation | — | sheet review F10 (D5) |
| `mobile.grimjaw_review` | deviation | — | sheet review F11 (D5) |
| `mobile.sylara_review` | deviation | — | sheet review F7 (D5) |
| `_core` | ported | `scripts/data/core_settings.gd` | `DATA_PATH` |
| `storage_paths.SAVE_DIR` | folded | `scripts/match/save_slot_store.gd` | `const PATH_TEMPLATE` |
| `settings.TITLE` | folded | `scripts/data/core_settings.gd` | `DATA_PATH` |
| `game.Game` | folded | `scenes/prototype/PrototypeMatch.tscn` | `[node name="PrototypeMatch"` |
| `menu.Menu` | folded | `scenes/menu/MainMenu.tscn` | `[node name="MainMenu"` |
| `splash_screen.SplashScreen` | ported | `scenes/splash/SplashScreen.tscn` | `[node name="SplashScreen"` |
| `_render.get_font` | ported | `scripts/ui/rebuild_theme.gd` | `static func create_theme(` |
| `_log_frame_error` | ported | `scripts/app/frame_error_log.gd` | `func record(` |
| `_cinematic_active` | ported | `scenes/prototype/prototype_screen.gd` | `celebration_active` |
| `_handle_background` | folded | `app/app.gd` | `NOTIFICATION_APPLICATION_PAUSED` |
| `main` | folded | `app/app.gd` | `func _install_screen(` |
| `adaptive` | ported | `scripts/settings/adaptive_quality_runtime.gd` | `func update_fps(` |
| `screen` | baked | — | viewport menggantikan surface render |
| `STATE_SPLASH..STATE_PAUSE` | ported | `app/app.gd` | `_install_screen(SPLASH)` |
| `APP_BG` | folded | `app/app.gd` | `NOTIFICATION_APPLICATION_FOCUS_OUT` |
| `APP_FG` | folded | `app/app.gd` | `NOTIFICATION_APPLICATION_PAUSED` |
| `_FRAME_ERR_LAST` | ported | `scripts/app/frame_error_log.gd` | `var last_written` |
| `_FRAME_ERR_COOLDOWN` | data | `scripts/app/frame_error_log.gd` | `const COOLDOWN_SECONDS := 2.0` |
| `__main__` | folded | `project.godot` | `run/main_scene=` |

## 3. Yang diport di layer ini

| Bagian | Perilaku sumber yang dipertahankan |
| --- | --- |
| `FrameErrorLog` (`scripts/app/frame_error_log.gd`) | header `[FRAME ERROR:<kind>]`, seksi `\n===== <stamp> =====\n`, append ke `crash_log.txt`, rate-limit **2,0 s per kind** — termasuk quirk sumber: entri pertama pada `t = 0.0` ikut tertahan karena `0.0 - 0.0 < 2.0` |
| `StartupReport` (`scripts/app/startup_report.gd`) | 8 baris banner: rule 60 karakter, `MYSTIC ARENA - MOBILE BUILD`, device, android + API, save dir, `TOUCH`/`MOUSE/KEYBOARD`, quality |
| `app/app.gd` | mencetak banner sekali di `_ready()`, mencatat kegagalan konfigurasi sesi (`"boot"`) sebelum fallback ke menu — sebelumnya gagal senyap |
| `project.godot` | `physics/common/max_physics_steps_per_frame=4` (= `MAX_CATCHUP`) dan `audio/driver/mix_rate=44100` (= `pygame.mixer.pre_init(frequency=44100)`) |

`FIXED_DT_MS = 1000/60` sudah setara `physics_ticks_per_second=60`; clamp FPS pemain (`fps_limit` → `Quality.target_fps` → `min(...)` di touch mode) sudah ada di `frame_rate_limit_runtime.resolve_limit()`.

## 4. Deviasi terdokumentasi

| Kode | Hal | Deviasi | Alasan |
| --- | --- | --- | --- |
| D1 | `_log_frame_error` | hanya mencatat pesan yang **dipanggil eksplisit**; tidak ada `try/except` per frame | GDScript tidak bisa menangkap error runtime; engine tetap hidup tanpa guard, jadi yang diport adalah rate-limiter, format, dan berkas log |
| D2 | timestamp log | panggilan live memakai jam lokal (`get_datetime_dict_from_system`), timestamp injeksi dianggap UTC | Python `time.strftime` = waktu lokal; UTC membuat tes deterministik |
| D3 | banner `android: %s (API %s)` | API level diisi `-` | GDScript tidak mengekspos API level numerik; release string tetap dari `OS.get_version()` |
| D4 | mixer | `size=-16`, `channels=2`, `buffer=1024` tidak punya padanan setting | buffer/latensi diatur driver Godot; `mix_rate` 44100 dipin |
| D5 | `mobile.debug` + 4 sheet review | tidak diport | alat dev opt-in (`MYSTIC_DEBUG`, F7–F11), nol perilaku pemain di build rilis |
| D6 | `mobile.diagnostics`, `mobile.bootcheck` | tidak diport | layar self-test/bootcheck khusus Android-dev; perannya digantikan suite native headless |
| D7 | clamp catch-up | Godot membuang sisa waktu setelah `max_physics_steps_per_frame` | sumber menyisakan setengah akumulator (`sim_acc = min(sim_acc * 0.5, ...)`); mesin tidak mengekspos akumulator, efek pemain sama: simulasi melambat, tidak spiral |
| D8 | `game.Game` / `menu.Menu` / `settings` | modulnya tidak ada di snapshot repo, jadi impornya dead | perilaku kelasnya sudah diport sebagai scene (layer lain) dan konstanta `TITLE` hidup di core settings |

## 5. Cara menjalankan

```bash
python3 godot_rebuild/tests/main_source_oracle.py --write   # tulis fixture AST main.py
python3 godot_rebuild/tests/main_source_oracle.py           # cek sinkron + token hidup
python3 godot_rebuild/tests/validate_project.py             # blok 9cn
godot --headless --script tests/run_all.gd                  # suite native (PC/CI)
```

`tests/main_shell_checks.gd` memverifikasi format header/seksi/timestamp, perilaku cooldown (termasuk quirk `t=0.0` dan independensi antar-kind), append + drop berkas, `reset()`, 8 baris banner dari template sumber, `input_mode`, `collect()` live, `max_physics_steps_per_frame == MAX_CATCHUP`, `mix_rate == 44100`, urutan state, wiring `app.gd`, dan peta keybinding dev.

## 6. Status paritas

Terbukti: seluruh 35 simbol punya klasifikasi eksplisit dan token hidup (atau alasan baked/deviation), banner startup identik baris-per-baris dengan template sumber, semantik cooldown log sama dengan `_log_frame_error`, dan dua konstanta loop (`MAX_CATCHUP`, mixer rate) kini dipin di `project.godot`. Belum terbukti: perilaku frame nyata di perangkat (logcat, latensi mixer, pemulihan lifecycle Android) dan tampilan visual — keduanya butuh run Godot + screenshot/seed state sama di PC dan hardware Android. Validator statis dan fixture **bukan** bukti paritas visual.
