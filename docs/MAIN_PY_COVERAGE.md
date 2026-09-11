# Peta cakupan `main.py` → Godot

**Apa ini:** audit blok-per-blok `main.py` (652 baris — entry point Android /
touchscreen-first) terhadap port Godot di `godot/`. Dipakai untuk menjawab
"bagian `main.py` mana yang sudah pindah" tanpa menebak dari nama berkas.

**Cara baca:** setiap baris = blok pygame dengan rentang baris di `main.py`,
padanannya di Godot, dan statusnya.

| Status | Arti |
|---|---|
| ✅ PORTED | Perilaku diport dan **dikunci tes** (`MainEntryParityTest` atau tes lain yang disebut) |
| 🟡 PARSIAL | Ada padanannya, tapi sebagian perilaku belum ada / belum diuji |
| ❌ BELUM | Tidak ada padanan di Godot |
| ⚪ N/A | Kode pygame-nya mati, khusus engine pygame, atau mengimpor modul yang sudah tidak ada di repo |

Replay headless: `godot/tests/MainEntryParityTest.tscn`. Peta cakupan
`_core.py`: [CORE_PY_COVERAGE.md](CORE_PY_COVERAGE.md); `_entity.py`:
[ENTITY_PY_COVERAGE.md](ENTITY_PY_COVERAGE.md); `_render.py`:
[RENDER_PY_COVERAGE.md](RENDER_PY_COVERAGE.md); `_system.py`:
[SYSTEM_PY_COVERAGE.md](SYSTEM_PY_COVERAGE.md); status paritas umum:
[GODOT_PARITY.md](GODOT_PARITY.md).

> **Catatan penting:** `main.py` **tidak bisa dijalankan** di repo ini. Ia
> masih mengimpor `settings`, `game`, `menu`, `game_settings`, dan
> `sound_manager` (`:61-67`, `:253-268`) yang tidak pernah ada di riwayat
> repositori — isinya sudah melebur ke `_core.py` / `_system.py` saat
> konsolidasi modul. Yang diport ke Godot karena itu adalah **perilaku yang
> tertulis di berkas ini** (konstanta loop, urutan boot, cabang siklus hidup),
> bukan hasil menjalankannya. Sesuai aturan migrasi (`MIGRASI_1_1.md`),
> `main.py` sendiri tidak disentuh.

---

## 1. Boot — audio, layar, patch performa (`:22-67`, `:157-217`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `pygame.mixer.pre_init(44100, -16, 2, 1024)` (`:25-30`) — buffer kecil = latensi rendah | — | ⚪ N/A (konfigurasi mixer SDL; Godot mengatur audio lewat `AudioStreamPlayer` + `project.godot`) |
| `perf.install_all(is_android=plat.TOUCH_MODE)` (`:38`) → `auto_detect_quality` (Android = LOW, desktop = HIGH, `mobile/perf.py:861-871`) | `AppShell._detect_quality()` + `AppShell._ready()` | ✅ (FASE 27; `MainEntryParityTest` mengunci Android/iOS → `low`, lain → `high`, dan `TARGET_FPS` 30/60) |
| `debug_mod.install_crash_handler()` (`:48`) → `crash_log.txt` di direktori writable (`mobile/debug.py:427-450`) | `AppShell.write_crash_log()` + sesi boot (`user://crash_log.txt`) | 🟡 PARSIAL — arsip log + rotasi 256 KB diport dan dikunci; `sys.excepthook` tidak ada padanannya karena Godot tidak punya exception hook global (lihat §4) |
| `plat.create_display(vsync=True)` — SCALED, koordinat tetap 1280×720 (`:56`) | `project.godot` `window/size/viewport_width=1280`, `viewport_height=720`, `stretch/mode="canvas_items"`, `window/vsync/vsync_mode=1` | ✅ |
| `SoundManager.load_all()` + `play_bgm('bgm_battle.wav', loop=True, fade_ms=3000)` + `play_ambient('ambient_forest', volume_mult=0.8)` (`:160-164`) — SEBELUM menu dibuat | `AudioManager` (24 SFX + 7 suara tempur) + `AppShell._start_boot_audio()` | ✅ (FASE 27; sebelumnya BGM baru bunyi saat `start_level`, jadi menu utama diam — kini boot memutar `bgm_battle.wav` fade 3 dtk + ambient 0.8) |
| Buat ulang buffer render setelah benchmark menentukan `Quality.cheap_alpha` / `fastblit` (`:196-215`) | — | ⚪ N/A (jalur blit SDL tidak ada di Godot) |
| `audio_mod.init()` — 7 suara tempur terpisah dari SoundManager (`:217`) | `AudioManager.COMBAT_SFX` + anggaran 4/frame (`_process`, paritas `combat_audio.new_frame()`) | ✅ |
| Banner boot `MYSTIC ARENA - MOBILE BUILD` + device/android/save/input/quality (`:279-291`) | `AppShell._print_boot_banner()` | ✅ (kolom tanpa padanan engine — API level Android, versi SDL — diganti info setara: versi Godot, `OS.get_model_name()`, nama server tampilan, direktori `user://`) |

## 2. Mesin state `SPLASH → MENU → GAME → PAUSE` (`:71-72`, `:461-613`)

| Blok | Padanan Godot | Status |
|---|---|---|
| Konstanta `STATE_*` + `current_state` (`:71-72`, `:274`) | `ControllerRouter.current_state()` (FASE 24) — splash → menu/PAUSE → game, dipakai routing gamepad | 🟡 PARSIAL: **tidak ada satu variabel kanonik**; Main/MainMenu/TouchHUD masing-masing membaca kondisi yang sama lewat `MainMenu.is_open()`, `MainMenu.state`, dan `GameManager.in_menu`. Sengaja tidak dibuatkan aksesor kedua di `AppShell` supaya tidak drift dari `ControllerRouter` |
| Splash: `splash.update/draw` lalu `is_done()` → `STATE_MENU` (`:492-501`) | `scenes/ui/SplashScreen.gd` + `Main._maybe_show_splash()` (FASE 27) | ✅ — **sebelum FASE 27 node ini yatim** (tidak ada di `main.tscn` dan tidak pernah di-`preload`), jadi Godot melompat langsung ke menu. Kini ia menutupi menu saat boot dan klik/tombol apa pun hanya melewatinya; **dilewati di headless** (`--quit-after N` mengukur frame, bukan detik) |
| Menu → match: `Game(screen, level_number=...)` (`:514-521`) + `perf.clear_text_caches()` | `Main._on_menu_play()` → `GameManagerConnector.start_match()` | ✅ (`GameManager.start_level`, tanpa cache teks) |
| GAME: `sim` catch-up + `game.update()` + `hud.draw` (`:525-560`) | `Main._process` + `_physics_process` unit + `TouchHUD` (anak HUD paling atas) | ✅ |
| Transisi akhir match: `next_level_requested` / `replay_requested` / `return_to_menu_requested` (`:563-588`) | `GameManager.next_level()` / `restart_match()` / `return_to_menu()` + `Main._on_menu_main_menu()` | ✅ (FASE 4d) |
| PAUSE: gambar frame terakhir + menu pause (`:590-613`) | `Main._toggle_pause()` + `MainMenu.open_pause()` + `Main._apply_menu_coverage()` | ✅ |

## 3. Langkah simulasi tetap (`:298-343`, `:525-560`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `FIXED_DT_MS = 1000/60` (`:331`) | `project.godot` `physics/common/physics_ticks_per_second=60` | ✅ |
| `MAX_CATCHUP = 4` — diturunkan dari 8 untuk mencegah "spiral kematian" di HP (`:332`) | `project.godot` `physics/common/max_physics_steps_per_frame=4` (nilai bawaan engine = 8) | ✅ (FASE 27; `AppShell._check_loop_policy()` memperingatkan kalau diubah, `MainEntryParityTest` mengunci angkanya) |
| `while sim_acc >= FIXED_DT_MS and sim_steps < MAX_CATCHUP` + sisa akumulator dibelah dua saat mentok (`:528-548`) | Mesin langkah tetap SceneTree (`physics_ticks_per_second` + `max_physics_steps_per_frame`) | 🟡 Godot membuang sisa waktu berdasarkan `physics/common/physics_jitter_fix`, bukan rumus "setengah" main.py — deviasi mesin, tidak ada padanan yang bisa diuji headless |

## 4. Penjaga frame + log error (`:78-105`, `:536-559`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `try/except` di sekitar `game.update()` & `game.draw()` — satu frame gagal tidak menutup aplikasi (`:536-559`) | Ditangani engine: error di `_process`/`_physics_process` mencetak `SCRIPT ERROR` lalu frame berikutnya tetap jalan | ⚪ N/A (bukan dead code di pygame, tapi padanannya adalah perilaku engine Godot) |
| `_log_frame_error(kind)` — traceback rate-limited 2 dtk ke stdout **dan** `crash_log.txt` (`:87-105`) | `AppShell.write_crash_log()` (tulis ke `user://crash_log.txt`) | 🟡 PARSIAL: arsip + rotasi diport, pembungkus rate-limited tidak (tidak ada pemanggil di Godot — engine yang menangani errornya; menulis logger tanpa pemanggil = dead code) |

## 5. Layar diagnostik & benchmark (`:183-215`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `bootcheck_mod.should_show()` (`MYSTIC_BOOTCHECK=1`) → layar info tampilan + benchmark + penghitung sentuhan + "matikan selamanya" (`:186-190`) | — | ❌ BELUM — layar ini mengukur jalur blit SDL (`fastblit`/`blitwatch`/`colorkey`) yang tidak ada di Godot; yang tersisa (info tampilan) sudah ada di banner boot `AppShell` |
| `diag_mod.run_all(screen)` — info tampilan + `apply_device_profile` (`:192`) | — | ❌ BELUM — profiling perangkat Godot setara `Performance`/`--verbose`, bukan modul game |

## 6. Panel kanan (`:222-247`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `SidePanel(get_font)` + `daftarkan(side)` — aktif hanya kalau layar lebih lebar dari 16:9 (`:222-225`) | `MobileLayout.has_side_panel()` (`SIDE_PANEL_MIN_LEFTOVER 120`) + `scenes/ui/SidePanel.gd` (anak pertama HUD) | ✅ |
| `_gambar_panel(g)` — panel digambar SEBELUM game supaya popup tidak tertutup (`:227-247`) | Urutan anak HUD: `SidePanel` → `TacticalBar` → … → `TouchHUD` (terakhir) | ✅ (FASE 23) |
| Penjaga "klik di panel jangan tembus ke peta" — `side.hit_test` sebelum `hud.hit_test`, dan sentuhan panel tetap diteruskan ke `Game.handle_click` (`:417-431`) | `SidePanel.hit_test` + `Main._apply_touch_action` + `TacticalBar` | ✅ (FASE 18/23) |

## 7. Input sentuh, keyboard, HUD (`:342-459`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `touch.update()` + `touch.collect()` + `dispatch_to_menu/game` (`:342`, `:401`, `:461-476`) | `pointing/emulate_mouse_from_touch=true` (`project.godot`) + `TouchHUD._input` (mouse saja, aksi ganda kalau dua jalur) | 🟡 PARSIAL: multi-sentuh, `claimed`, dan gestur tahan/lepas per id sentuhan tidak diport; tombol taktis memakai `button_down`/`button_up` |
| Tahan tombol jeda → buka overlay debug (`:409-416`) | — | ❌ BELUM (butuh deteksi tahan; tombol FPS TouchHUD tetap env-gated `MYSTIC_DEBUG=1`) |
| `held_tac` — perintah taktis aktif selama sentuhan ditahan (`:404`, `:446-457`) | `TacticalBar` (`button_down`/`button_up`) + `Main._tactical_release_all()` | ✅ (FASE 18, dikunci `TacticalInputParityTest`) |
| Keyboard `F8` overlay FPS, `ESC` pause/menu, KEYUP rute ke game (`:368-386`) | `Main._on_key` / `_on_key_release` | ✅ |
| `hud.sync(game, current_state, cine)` tiap frame (`:399`) | `TouchHUD.sync_from_match()` (matriks 7 kunci `HudLayout.TOUCH_VISIBILITY`) | ✅ (FASE 23) |
| `debug.update/draw` overlay 4 mode + grafik (`:614-617`) | `scenes/ui/FpsCounter.gd` (overlay minimal, `_system.FPSCounter`) | 🟡 PARSIAL — 4 mode + grafik `mobile/debug.py` belum diport (disebut status terbuka di `GODOT_PARITY.md`) |
| `plat.vibrate(15/30)` feedback tombol (`:414`, `:421`) | — | ❌ BELUM (getar Android; belum ada padanan di Godot) |

## 8. Siklus hidup Android (`:75-76`, `:128-155`, `:346-366`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `APP_BG` → `touch.cancel()` + lepas semua hold taktis (`:350-360`) | `Main._notification(NOTIFICATION_APPLICATION_PAUSED)` → `_tactical_release_all()` | ✅ (FASE 18) |
| `_handle_background()` — `mixer.pause()` + `music.pause()`, tidur sampai `APP_FG`, lalu `unpause()` (`:128-155`) | `AppShell._notification` PAUSED/RESUMED → `AudioManager.pause_bgm/pause_ambient` | ✅ (FASE 27; **sebelumnya tidak ada padanan sama sekali** — musik terus berbunyi saat app di-minimize. Tidur sambil menunggu tidak diport: Godot menahan loop sendiri) |
| Penjaga "jangan hidupkan audio kalau pemain sedang di menu PAUSE" | `AppShell._on_app_foreground()` (cek `get_tree().paused` / `GameManager.is_paused`) | ✅ (FASE 27, dikunci tes) |

## 9. Cloud save + batas FPS (`:387-395`, `:620-645`)

| Blok | Padanan Godot | Status |
|---|---|---|
| `_cloud_mgr.poll()` tiap frame di semua state (`:387-395`) | — | ⚪ N/A (plugin Play Games belum diport; di luar scope yang sama dengan `SaveManager`, lihat `SaveSlotParityTest`) |
| `clock.tick(limit)` — setting pemain hanya boleh MENURUNKAN di perangkat sentuh, selain itu `Quality.target_fps` (`:620-645`) | `AppShell.resolve_fps_limit()` / `apply_fps_limit()` → `Engine.max_fps` | ✅ (FASE 27; sebelumnya `GameManager.apply_fps_limit` menulis `Engine.max_fps` mentah, jadi slider SETTINGS bisa melangkahi pembatas 30 FPS preset LOW) |
| `adaptive.update(clock.get_fps())` — jendela 90, turun < 26 FPS, naik > 52 FPS, cooldown 180/300 frame (`:645`, `mobile/perf.py:877-911`) | `AppShell._update_adaptive_quality()` + `_apply_quality()` | ✅ (FASE 27; tangga high↔medium↔low, cooldown, dan penulisan ulang batas FPS dikunci tes. Konsumennya HANYA batas FPS: rasio partikel/kabut preset pygame belum punya padanan — `SparkField.particle_ratio` tetap 1.0 dan itu dikunci `RenderFxParityTest`) |
| `pygame.quit()` + `sys.exit()` (`:647-648`) | `get_tree().quit()` (harness tes) / tombol QUIT menu | ✅ |

---

## Temuan

1. **`main.py` tidak bisa dijalankan** — impor `settings`, `game`, `menu`,
   `game_settings`, `sound_manager` (`:61-67`, `:253-268`) mengarah ke modul
   yang sudah melebur ke `_core.py`/`_system.py`. README (`python main.py`)
   karena itu usang. Port Godot mengambil perilakunya dari teks sumber, bukan
   dari menjalankannya, dan **tidak menyentuh berkas pygame**.
2. **Tiga celah nyata yang ditutup FASE 27:** (a) BGM/ambient tidak pernah
   diputar sebelum match (menu utama diam, beda dengan pygame yang memutarnya
   di boot); (b) `SplashScreen.gd` yatim — Godot tidak pernah menampilkan
   splash; (c) tidak ada pembekuan audio saat aplikasi ke latar.
3. **Kebijakan loop tidak pernah disetel** — pembatas kejaran Godot masih nilai
   bawaan engine (8 langkah) sementara pygame menurunkannya ke 4 dengan alasan
   yang terukur. Kini ditulis di `project.godot` dan dikunci tes.
4. **Yang sengaja tidak diport:** layar bootcheck/diagnostics (mengukur jalur
   blit SDL), getar haptik, 4 mode overlay debug, dan multi-sentuh penuh —
   semuanya tercatat di tabel di atas dengan alasannya.
