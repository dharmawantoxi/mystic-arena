# Mystic Arena — port `main.py` ke Godot 4

Proyek native untuk **application shell** Mystic Arena. Buka `project.godot`
dengan **Godot 4.7.2 Standard** (bukan .NET), lalu tekan **F6** pada
`scenes/Main.tscn` atau **F5** untuk menjalankan proyek.

> **Batas migrasi:** `main.py` adalah loop/orkestrator, bukan seluruh game.
> Port ini menggantikannya dengan scene, state machine, input, audio dan
> lifecycle native Godot. Combat, hero, boss, tower, map renderer, save slot,
> top-up dan Play Games belum diport. Tombol Play tanpa adapter menampilkan
> **Mode integrasi**, bukan pertandingan pura-pura. Kode Python tetap utuh.

## Menjalankan

Dari root repositori:

```bash
# satu kali: salin font/gambar/audio dan ekspor metadata 54 level
python3 tools/prepare_godot_main.py

# impor aset native, lalu jalankan
godot --path godot_rebuild --editor --import
godot --path godot_rebuild

# alternatif tanpa PATH: gunakan path binary Godot Anda
```

Tidak membutuhkan pygame, Python runtime, plugin .NET, atau GDExtension.
Python hanya dipakai alat persiapan/tes. Jika binary bernama `godot4`, ganti
perintah di atas. Font/gambar sudah disertakan; audio yang hilang tidak
menghentikan aplikasi. Jalankan alat persiapan setelah mengubah aset sumber.

## Struktur

| Berkas | Tanggung jawab |
|---|---|
| `scenes/Main.tscn`, `scripts/Main.gd` | Root scene dan orkestrator pengganti `main()` |
| `scripts/core/AppState.gd` | Transisi splash → menu → game ↔ pause |
| `scripts/core/FixedClock.gd` | Simulasi 60 Hz, clamp 250 ms, maksimal 4 catch-up |
| `scripts/core/GestureTracker.gd` | Tap, double tap, long press, drag, scroll, fling |
| `scripts/core/GameSettings.gd` | Preferensi audio/FPS di `user://godot_settings.cfg` |
| `scripts/core/LevelCatalog.gd` | Metadata level dan urutan next-level |
| `scripts/audio/AudioDirector.gd` | BGM, ambient, 32 voice SFX, fade dan pause background |
| `scripts/ui/` | Splash, menu, pause, HUD, pengaturan dan diagnostik |
| `scripts/ports/GameplayPort.gd` | Kontrak integrasi gameplay native |
| `tests/run_all.gd` | Regresi headless dengan adapter gameplay/cloud palsu |

## Kontrol

- Klik/sentuh untuk memilih level dan berinteraksi dengan arena.
- **Esc / Back / II:** pause atau lanjut. Konfirmasi sebelum kembali/keluar.
- **Tahan II 450 ms:** diagnostik; **F8 / FPS:** mode ringkas/detail.
- **Q/W/E/R**, **H**, serta tombol layar: diteruskan ke gameplay adapter.
- **G/F, T, C, B, D:** tahan tactical; pelepasan semua sumber diperlukan
  sebelum perintah berakhir. Pause/background membatalkan semua hold.
- **Space / SKIP:** lewati cinematic yang dilaporkan adapter.
- **F7/F9/F10/F11:** permintaan review rig diteruskan ke adapter; renderer
  review Python sendiri belum termasuk port ini.
- `MYSTIC_FORCE_TOUCH=1`, `MYSTIC_DEBUG=1`, atau `-- --debug` untuk pengujian.

## Menghubungkan gameplay

1. Buat scene gameplay native dengan root `Control` dan script
   `extends GameplayPort` (atau script turunan kelas tersebut).
2. Implementasikan `combat_ready() -> true`, `simulation_step()` dan metode
   input yang dibutuhkan. Jangan memakai `_physics_process()` kedua untuk
   combat: `Main` memanggil `simulation_step()` pada timestep tetap.
3. Pilih scene itu di properti **Game Scene** pada root `Main.tscn`.
4. Gunakan sinyal `next_level_requested`, `replay_requested`,
   `menu_requested`, `pause_requested`; jangan mengganti scene tree sendiri.
5. Implementasikan `hold_begin/end` dan `release_all_holds` jika memakai
   tactical command. `configure(level, replay)` menerima pilihan pemain.

`Main.cloud_service_path` dapat menunjuk node native yang memiliki `poll()`.
Ini hanya titik integrasi, **bukan** implementasi Google Play Games/cloud save.
Tanpa service tersebut aplikasi berjalan lokal tanpa menjanjikan sinkronisasi.

## Tes

```bash
python3 tools/prepare_godot_main.py --check
python3 godot_rebuild/tests/validate_project.py
python3 tools/test_godot_main_prepare.py
godot --headless --path godot_rebuild --editor --import
godot --headless --path godot_rebuild --script res://tests/run_all.gd
godot --headless --path godot_rebuild --quit-after 180
```

Dengan gdtoolkit 4.5.0:

```bash
gdparse $(find godot_rebuild -name '*.gd')
gdlint $(find godot_rebuild -name '*.gd')
gdformat --check $(find godot_rebuild -name '*.gd')
```

CI `.github/workflows/godot-rebuild.yml` menjalankan persiapan aset, guardrail
sumber, lint, impor, regresi, serta boot scene utama dengan Godot 4.7.2.
Tes memakai adapter palsu hanya untuk verifikasi kontrak; bukan gameplay.

Lihat [catatan migrasi dan batas parity](../docs/GODOT_MAIN_MIGRATION.md)
dan [hasil verifikasi serta batas pengujian](../docs/GODOT_MAIN_VERIFICATION.md).

## Ekspor Android (belum diverifikasi perangkat)

Preset **Android** tersedia dengan orientasi landscape dari `project.godot`,
ARM64, min SDK 24, target SDK 36, dan application ID versi Pygame. Instal JDK 17,
Android SDK serta export templates Godot 4.7.2 melalui editor. Konfigurasikan
keystore debug/release lokal, lalu Export Project. Jangan mengubah application ID
untuk update aplikasi yang sudah terbit. Kredensial tidak disimpan di repo.
Preset ini belum menghasilkan atau memvalidasi APK/AAB di lingkungan pengerjaan.
