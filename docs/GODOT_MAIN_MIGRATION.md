# Migrasi `main.py` → Godot 4

## Ruang lingkup

Yang dimigrasikan adalah **entry point aplikasi**, bukan sekitar 40 ribu baris
gameplay Python yang diimpornya. `main.py` tetap disimpan sebagai referensi.
Tidak ada Python yang dijalankan di dalam Godot dan tidak ada klaim bahwa
54 pertandingan sudah playable hanya karena metadata levelnya tersedia.

Checkout awal tidak mempunyai `godot/`, `godot_rebuild/`, ataupun `docs/`,
meskipun README dan workflow lama merujuk kepadanya. Proyek baru ditempatkan
di `godot_rebuild/` sesuai lokasi proyek aktif yang disebut dokumentasi lama.
Workflow `godot-rebuild.yml` sebelumnya memanggil puluhan berkas yang tidak
ada; sekarang menguji proyek yang benar-benar tersedia. Workflow port lama
lain tidak diubah dan bukan bukti kelayakan proyek ini.

## Pemetaan

| Python | Godot | Status |
|---|---|---|
| `pygame.init`, display 1280×720 | `project.godot`, `Main.tscn` | Native; viewport keep-aspect, renderer Compatibility |
| `STATE_SPLASH/MENU/GAME/PAUSE` | `AppState.gd` | Transisi eksplisit; tidak ada simulasi saat pause/menu |
| `while running`, `clock.tick` | `_process`, `Engine.max_fps` | Loop milik engine; preferensi FPS tersimpan |
| Akumulator 1/60, clamp 250 ms, cap 4 | `FixedClock.gd` | Konstanta dan residual half-clamp dipertahankan |
| `SplashScreen` | `SplashView.gd` | Logo/teks, 3 detik, skip dengan fade 250 ms |
| `Menu` | `MenuView.gd` | UI native ringkas, bukan seluruh menu Python |
| Touch/mouse gesture | `GestureTracker.gd` | Ambang sama; multi-pointer dan pembatalan eksplisit |
| HUD dan hold tactical | `HudView.gd`, `Main.gd` | Kepemilikan per pointer/key, release saat pause/background |
| `SoundManager`, BGM/ambient | `AudioDirector.gd` | Fade, voice pool, throttle, pause per-stream |
| `APP_BG/FG`, blocking wait | Notifikasi application pause/resume | Non-blocking; kembali foreground tetap pause sampai resume |
| `cloud_save.manager.poll()` | `cloud_service_path` | Hook opsional; plugin/provider belum diport |
| `Game(...)` | `GameplayPort` | Kontrak native; default layar integrasi |
| Replay/next/return | Sinyal port + `Main.gd` | Membuat/mengganti adapter, reset clock dan hold |
| `DebugOverlay`, frame logging | `DebugView`, `Diagnostics` | FPS/state/tick, log error integrasi dibatasi 2 detik |
| `GameSettings` | `GameSettings.gd` | Hanya audio/FPS/debug; file terpisah dari save Python |

## Perbedaan yang disengaja

- Godot menggambar lewat scene tree, bukan `game.draw()` manual. Adapter
  mengatur node visualnya sendiri; tidak ada surface/blit yang dibawa serta.
- Lifecycle tidak melakukan sleep-loop. Saat background, pemrosesan game
  berhenti dan stream audio dipause. Saat kembali, pemain harus melanjutkan.
- Error GDScript tidak dapat ditangkap seperti exception Python. Kesalahan
  adapter tidak ditelan atau diklaim aman untuk diteruskan tanpa batas;
  validasi kontrak, diagnostik integrasi, dan CI log-error digunakansebagai gantinya.
- Safe area dibaca dari DisplayServer pada perangkat sentuh. Layout utama
  tetap 16:9 dengan letterbox; side-panel layar lebar Python belum diport.
- Cache font/blit, benchmark pygame, bootcheck SDL, dan patch performa Python
  tidak relevan sebagai API Godot. Tidak ada klaim hasil benchmark perangkat.
- Preferensi Godot tidak mengimpor/menimpa progres, slot, atau pembelian Python.

## Belum selesai untuk parity game penuh

1. Combat, minion, tower, castle, hero/skill, boss/AI, projectile dan efek.
2. Renderer map/lighting, animasi rig, visual review, dan seluruh popup gameplay.
3. Menu save-slot, unlock/progres, ekonomi, top-up/voucher, dan localization penuh.
4. Google Play Games Saved Games, Java/plugin bridge, dan autentikasi.
5. Side-panel lebar, pengaturan gameplay lengkap, dan profil kualitas adaptif.
6. Ekspor Android teruji di perangkat, keystore/release, serta pengujian GPU/audio.

Sampai item tersebut dikerjakan, hasil ini adalah **fondasi entry point native
yang dapat dijalankan dan diuji**, bukan pengganti APK Pygame untuk produksi.
Tidak ada APK/AAB yang dibuat atau diklaim sudah lulus uji perangkat.

## Aset dan reproduksibilitas

`tools/prepare_godot_main.py` membaca metadata level dengan AST (tanpa pygame),
menyalin font/logo/ikon, dan mengenali isi WAV/Ogg/MP3 agar ekstensi sesuai
importer Godot. Audio salinan di-ignore; sumber dan lisensi tetap di `assets/`.
`--check` memastikan salinan tertrack dan JSON tidak basi. Uji perangkat asli
dan ekspor adalah langkah terpisah setelah gameplay tersedia.
