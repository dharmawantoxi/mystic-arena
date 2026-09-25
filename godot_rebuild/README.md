# Mystic Arena — Godot Rebuild

**Proyek baru, native GDScript. Target editor: Godot 4.7.2 standard, Windows 11.**

Ini implementasi fondasi tahap 1, **bukan migrasi seluruh game**. Tidak menggunakan scene, script, generator, GDExtension, atau plugin Godot dari migrasi sebelumnya. Python hanya menjadi referensi untuk pekerjaan migrasi berikutnya.

## Buka di Windows (tanpa membuat scene/script manual)

1. Ambil folder ini beserta seluruh isinya dari perubahan repo.
2. Buka **Godot 4.7.2 → Project Manager → Import**.
3. Pilih **`godot_rebuild/project.godot`**. Jangan memilih proyek migrasi lama.
4. Klik **Import & Edit**, tunggu import font selesai.
5. Tekan **F5**. Main scene sudah diatur ke `app/App.tscn`.
6. Klik **Buka arena percobaan**.

Tidak memerlukan Python, pip, converter, addon, atau C++ untuk menjalankan client ini. Font yang dibutuhkan sudah disertakan. Export template belum diperlukan untuk menjalankan lewat editor.

### Kontrol

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

**Penanda hijau bukan hero hasil porting.** Bentuk peta, lane, slot dan base adalah ilustrasi placeholder baru; bukan data navigasi level Python. Tidak ada damage, wave, reward, atau kondisi menang/kalah pada tahap ini.

## Yang sudah diimplementasikan

- Proyek mandiri: Compatibility, viewport 1280 × 720, stretch `canvas_items` + `keep`.
- Menu dengan theme, font lokal, tombol, fokus keyboard dan artwork prosedural baru.
- `App` sebagai pengendali perpindahan screen; aktivasi ganda dalam frame yang sama dijaga.
- Arena placeholder untuk mencoba seleksi dan perintah gerak.
- Simulasi demonstrasi dengan 60 physics tick/detik, terpisah dari render/UI.
- Pause/resume, restart, kembali ke menu, cleanup screen, dan pause saat kehilangan fokus.
- Adapter input mouse/touch; event mouse sintetis tidak menggandakan command touch.
- Lokasi data development terpisah (`MysticArenaRebuildDev`). **Belum ada kode yang membaca/menulis save.**
- Validator statis, runner tes native Godot, script PowerShell untuk Windows, dan workflow CI baru.

## Yang belum dimigrasikan

Hero/skill/animasi produksi, minion, combat, tower/upgrade, castle/nexus, wave, AI, ekonomi, item, boss, 54 level, progression, UI produksi, audio, save/migrasi save, cloud, pembayaran, Android export dan optimasi perangkat. Jangan menggunakan sandbox ini sebagai build pengganti game yang sudah rilis.

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
scripts/simulation/
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
  run_windows.ps1             Import + tes native di Windows
```

Font disalin dari `assets/fonts/` di root repo, bukan dari hasil migrasi lama. Lisensi/distribusi font tetap perlu ikut audit aset sebelum rilis. Semua script memakai path `res://` di dalam proyek ini; sumber Python tidak diimpor saat runtime.

## Pengujian

### Status validasi pada pembuatan awal

- **Lulus:** 107 pemeriksaan statis referensi file, konfigurasi, nama node unik, isolasi proyek, dan aturan dasar simulasi. Validator juga diuji untuk menolak frekuensi physics salah dan font hilang.
- **Lulus:** parsing, lint, dan format GDScript menggunakan `gdtoolkit 4.5.0`.
- **Lulus:** syntax tiga scene TSCN diperiksa menggunakan parser independen `godot-parser 0.1.7` (bukan engine Godot).
- **Belum dijalankan:** engine import, runner native, pengujian GUI/resize secara visual, Windows nyata, touchscreen dan Android.

Engine belum tersedia di sandbox pembuatan; unduhan binary resmi gagal pada koneksi TLS ke host aset GitHub. Karena itu, keberadaan runner/CI **bukan** klaim bahwa runtime sudah lulus. Parser pihak ketiga tidak memeriksa seluruh tipe/API engine atau scene runtime. Jalankan pemeriksaan native berikut atau tunggu hasil workflow setelah perubahan dipush sebelum menganggap fondasi ini terverifikasi penuh.

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

### Cakupan tes native yang disiapkan

- State terpisah antar instance, satuan gerak per tick, 600 langkah simulasi.
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
```

Untuk parser/linter, pasang `gdtoolkit==4.5.0` dalam virtualenv terpisah. Tidak perlu memasangnya di komputer pemain.

Workflow **Godot Rebuild (native, fresh project)** pada `.github/workflows/godot-rebuild.yml` hanya memeriksa proyek baru. Ia tidak menjalankan converter atau tes migrasi lama. Workflow menjalankan guardrail, import dengan engine 4.7.2, tes native, dan menyimpan log. Workflow baru belum dijalankan pada penyusunan awal; akan terpicu oleh push/PR yang menyentuh path terkait.

## Pemeriksaan visual singkat

1. F5 menampilkan judul Mystic Arena dan tombol arena/keluar.
2. Resize ke rasio berbeda: tampilan tetap proporsional, letterbox diperbolehkan.
3. Buka arena; pilih penanda, klik kanan, pastikan marker bergerak.
4. Klik panel HUD: penanda tidak hilang seleksinya karena klik tembus.
5. Esc: angka tick harus berhenti; Lanjutkan: angka tick maju lagi.
6. Alt+Tab: arena pause ketika kehilangan fokus.
7. Restart mengembalikan penanda ke posisi awal tanpa seleksi.
8. Kembali ke menu, ulangi. Periksa Debugger untuk error dan Remote tree untuk screen sisa.

## Langkah pengembangan berikutnya

Setelah fondasi lulus runtime: inventaris data level pertama dan kontrak stat/satuan → lane asli dan minion → combat kecil yang teruji → satu pertandingan utuh → perluasan sistem dan konten. Lihat [rencana lengkap](../docs/RENCANA_MIGRASI_GODOT_DARI_NOL.md).

Jangan mengedit game Python atau mengaktifkan converter lama untuk membuat proyek ini berjalan. Jika menemukan error, simpan pesan lengkap beserta versi Godot dan langkah reproduksi, lalu perbaiki di proyek baru.
