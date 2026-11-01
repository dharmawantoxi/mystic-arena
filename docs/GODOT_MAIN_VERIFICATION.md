# Verifikasi port entry point Godot

Tanggal: 2026-11-01.

| Pemeriksaan | Hasil |
|---|---|
| Persiapan aset dan metadata | 54 level; 32 berkas aset; `--check` lulus |
| Guardrail proyek/sumber | 73 pemeriksaan lulus |
| Alat persiapan Python | 2 tes unittest lulus |
| `gdparse` | 18 berkas GDScript lulus |
| `gdlint` | Tidak ada masalah |
| `gdformat --check` | Seluruh berkas sesuai |
| Runtime native headless | 92 pemeriksaan lulus, 0 kegagalan |
| Boot scene utama headless | Splash → menu berjalan; proses keluar normal |
| Diff hygiene | `git diff --check` lulus |

## Lingkungan uji lokal

Engine uji dikompilasi dari source resmi Godot tag `4.7.2-stable`, target
Linux headless tanpa GPU/audio backend. Versi engine melaporkan
`4.7.2.stable.custom_build`. Binary rilis official tidak dapat diunduh di
sandbox karena host redirect unduhan berada di luar allowlist jaringan.
Karena target uji bukan editor binary, uji runtime memakai cache kelas dan
`application/run/main_loop_type` sementara di `.godot/` (tidak masuk Git).
Scene utama diuji lewat konfigurasi proyek normal, tanpa override tersebut.

Tes native menjalankan scene `Main.tscn` yang sebenarnya dan adapter palsu,
meliputi: state splash/menu/game/pause; kesetaraan tick 30/60 FPS; batas
catch-up; gesture; kepemilikan tombol dan hold G/F; pause/background;
cloud polling; replay/next/return; level terakhir; pengaturan; safe-area HUD;
BGM/ambient/SFX serta aset audio hilang. Uji juga memeriksa tidak ada error
script serta menjalankan pembersihan stream/node sebelum suite selesai.

Boot atau penghentian suite cepat dengan backend audio Dummy dapat menghasilkan
peringatan playback audio belum sempat dibersihkan oleh server audio saat
engine langsung keluar. Ini bukan error script; pembersihan stream dan
pembebasan node sudah diuji dengan memberi engine beberapa frame selesai.

## Belum diverifikasi lokal

- `--editor --import` dan `--script` memakai **binary Standard official**:
  konfigurasi dan perintah sudah disiapkan di CI, tetapi belum dijalankan
  pada binary editor official di sandbox.
- Rendering visual/GPU, audio yang terdengar, input perangkat Android nyata,
  signing, dan ekspor APK/AAB. Preset Android tersedia tetapi bukan bukti
  build perangkat sudah lulus.
- Parity gameplay, ekonomi, save/cloud dan seluruh konten Python. Lihat
  [batas migrasi](GODOT_MAIN_MIGRATION.md).

CI `Godot main.py migration` menggunakan binary Standard official 4.7.2 dan
memperlakukan error impor/runtime sebagai kegagalan. Hasil workflow tersebut
harus dilihat pada commit/PR terkait, bukan diasumsikan lulus dari catatan lokal.
