# Rilis ke Google Play (Fase 6)

Panduan dari commit → AAB → Play Console. Pipeline build sudah jadi:
`.github/workflows/build-android-godot.yml`. Dokumen ini untuk bagian yang
**hanya bisa dikerjakan manusia** (Play Console, aset store, review).

---

## 1. Yang sudah siap di repo

| Hal | Status | Detail |
|---|---|---|
| Preset export Android (AAB) | ✅ | `godot/export_presets.cfg` — `gradle_build/export_format=1` (AAB), arm64-v8a, landscape, package `io.github.dharmawantoxi.mysticarena` (SAMA dengan buildozer, jadi Play mengenali app yang sama & save player tidak hilang) |
| CI build | ✅ | tag `vX.Y.Z` → AAB ditandatangani + GitHub Release; manual → APK debug (sideload) atau AAB verifikasi. Gerbang mutu: bebas script error, `apksigner verify`, `targetSdkVersion >= 36` |
| targetSdk 36 | ✅ | CI pakai **Godot 4.7.2** karena template Android-nya `DEFAULT_TARGET_SDK_VERSION = 36` (verifikasi: `platform/android/export/export_plugin.cpp` tag 4.7-stable). Template 4.3 hanya 34 — ditolak Play sejak 2026-08-31 |
| Renderer Android | ✅ | `project.godot`: `renderer/rendering_method.mobile="mobile"` (override platform). Forward+ **tidak didukung Android**; Mobile mendukung semua fitur 2D yang dipakai (lighting/CanvasModulate, glow, shader canvas_item, 2D HDR) dan otomatis jatuh ke OpenGL ES 3.0 di perangkat tanpa Vulkan (`fallback_to_opengl3` default true) → minSdk 24, jangkauan HP sama seperti versi pygame (minapi 24) |
| Ikon | ✅ | `godot/assets/android/` — launcher 192px + adaptive 432px (foreground dari `assets/icon.png` master dalam safe zone 264px, background solid #1A1030). Ikon store 512×512 = `assets/icon.png` (sudah ukuran resmi Play) |
| Suara | ✅ | `godot/assets/sounds/` di-gitignore (duplikat 15 MB); CI menyalin dari `assets/sounds/` **sebelum** export — kalau build lokal, jalankan converter dulu (lihat `godot/README.md`). Converter sekaligus **meluruskan ekstensi** 8 berkas yang bernama `.wav` padahal isinya Ogg Vorbis (7) / MP3 (1): Godot memilih importer dari ekstensi, importer WAV menolak Ogg (`Not a WAV file`) dan SFX-nya senyap di HP |
| Ikon item | ✅ | `godot/assets/items/` **ikut repo** (33 PNG ±3 MB, disinkronkan converter dari `assets/items/`) supaya ikon ITEM FORGE asli tampil di semua lingkungan (editor, export lokal, debug run, AAB). Tanpa berkasnya game tetap jalan — ikon mundur ke badge warna prosedural (`ItemIcons.gd`) |
| Presplash (boot splash) | ✅ | `assets/presplash.png` (1280×720) disalin ke `godot/assets/presplash.png` (di-gitignore) dan dipakai `application/boot_splash/image`; `boot_splash/bg_color` #0B0A12 = `android.presplash_color` buildozer. Exporter Godot memaksa berkas mentahnya ikut PCK **hanya kalau ada saat export** (`get_forced_export_files`) — langkah "Salin aset biner (gitignored)" di CI yang menjaminnya |
| Keystore | ✅ | Reuse secret lama (`KEYSTORE_BASE64` dkk) — **jangan pernah ganti keystore** setelah Play App Signing aktif (app tidak bisa di-update lagi dengan kunci lain) |

## 2. Build AAB

```bash
# versi release 1.0.0 -> version code 10000, AAB, GitHub Release otomatis
git tag v1.0.0
git push origin v1.0.0
```

Atau manual: **Actions → "Build Android (Godot)" → Run workflow**
(`debug` = APK sideload; `release` = AAB verifikasi pralaju).

- AAB di **Artifacts** run tersebut (retensi 90 hari).
- Version code formula: `major*10000 + minor*100 + patch`
  (`v1.2.3` → 10203). Code hanya boleh NAIK di Play — jangan pernah
  reuse/nurunkan.
- Gerbang CI menolak build kalau: ada `SCRIPT ERROR`/`Parse Error` di log,
  `apksigner verify` gagal, package salah, atau `targetSdkVersion < 36`.

Kenapa 4.7.2 hanya untuk export (bukan semua CI)? `godot-check.yml` pin
**4.3** = versi minimum feature project (`config/features`), sedangkan
export butuh template termutakhir untuk targetSdk 36. Dua-duanya valid:
project boleh dijalankan engine ≥ 4.3.

## 3. Play Console — sekali saja (setup awal)

1. **Akun developer**: $25 sekali (https://play.google.com/console).
   Kalau app pygame sudah punya akun + app, skip ke 3.3.
2. **Create app**:
   - Nama: `Mystic Arena`
   - Package: `io.github.dharmawantoxi.mysticarena` (harus sama, tidak bisa
     diubah nanti)
   - Bahasa: Indonesia
3. **App signing**:
   - Pilih **"Play App Signing"** + **upload keystore = keystore lama**
     (yang sama dengan `KEYSTORE_BASE6`). Play membuat kunci sendiri dan
     menyimpan keystore kita di vault Google — build CI tetap ditandatangani
     keystore lama, Play membubuhkan kunci keduanya otomatis.
4. **Aset store** (sebelum submit production):
   | Aset | Ukuran | Sumber |
   |---|---|---|
   | Ikon | 512×512 | `assets/icon.png` — sudah siap, upload langsung |
   | Feature graphic | 1024×500 | **TODO** — belum ada di repo. Buat dari `assets/logo.png` (1024², ambil strip tengah 1024×500) atau desain baru |
   | Screenshot phone (landscape) | ≥ 320px sisi pendek | jalankan AAB-debug di HP → `adb exec-out screencap -p > shot.png`. Minimal: menu utama, pertempuran, layar menang |
   | Screenshot tablet (landscape) | ≥ 1280×720 | sama, di tablet/resolusi tinggi |
   | Deskripsi singkat | 80 karakter | "MOBA turn-based 54 level: bangun menara, level hero, kalahkan 216 boss." |
   | Deskripsi penuh | 4000 karakter | salin bagian "Fitur" README.md |
5. **Content rating (IARC)**: kekerasan fantasi ringan (iklan in-app tidak
   ada). Jawab: violence = fantasy/cartoon, tidak ada konten bertema dewasa,
   tanpa pembelian real-money (belum ada IAP).
6. **Data safety form**: game **tidak mengumpulkan data apa pun**
   (save = JSON lokal di perangkat; tidak ada analytics). Permission yang
   diminta: `INTERNET` (cadangan untuk cloud save/Play Games di masa depan —
   tulis "jangan dipakai saat ini"), `VIBRATE`, `WAKE_LOCK`,
   `ACCESS_NETWORK_STATE`.
7. **Targeting**: 17+ (hasil IARC) — sesuaikan kalau jawaban IARC berbeda.

## 4. Rilis (per versi)

```
AAB dari Actions  →  Play Console → Production → Create new release
  → isi version code (otomatis terbaca dari AAB)
  → pilih track: Internal testing → Closed testing → Production
  → "Review" → "Roll out"
```

- **Internal testing** selalu duluan: tambah HP sendiri, unduh dari tautan
  testing, main 1 level penuh (menu → level 1 → menang → level 2), cek
  suara, landscape, dan save.
- Rollout bertahap (10% → 50% → 100%) lewat **staged rollout** supaya
  crash yang baru bisa di-rollback cepat.
- Pantau **Vitals** (crash rate < 1.0%, ANR < 0.2%) beberapa hari setelah
  rollout penuh.

## 5. Update berikutnya

1. Naik versi di `godot/export_presets.cfg`? **Tidak perlu** — CI menambal
   `version/name` + `version/code` dari tag.
2. `git tag v1.1.0 && git push origin v1.1.0` → AAB baru → repeat §4.
3. Catatan: kalau Google menaikkan target API tahunan (biasanya 31 Agustus),
   naikkan `GODOT_VERSION` di `build-android-godot.yml` ke versi Godot yang
   template-nya sudah menarget API itu (pola sama: cek konstanta
   `DEFAULT_TARGET_SDK_VERSION` di `export_plugin.cpp` tag tersebut).

## 6. Troubleshooting

| Gejala | Penyebab / perbaikan |
|---|---|
| CI: `Unable to open Android 'build-tools' directory` | build-tools 36 belum terpasang; step `Paket Android` harus sukses dulu (cek log `sdkmanager`) |
| CI: `targetSdkVersion=34 < 36` | Godot yang dipakai bukan 4.7.2 (template lama); cek `GODOT_VERSION` — jangan turunkan |
| CI: `package salah` | `package/unique_name` di `export_presets.cfg` berubah — kembalikan `io.github.dharmawantoxi.mysticarena` |
| AAB di HP: layar hitam | cek `godot/README.md` bagian "F5 cuma layar hitam" (6 penyebab sudah pernah terjadi) |
| AAB di HP: game sunyi | langkah "Salin aset biner (gitignored)" tidak jalan / build lokal tanpa converter; cek isi `assets/sounds/` di dalam AAB (`unzip -l MysticArena.aab | grep sounds`) |
| AAB di HP: sebagian SFX sunyi (klik UI, `victory`, ambient forest) | salinan audio masih berekstensi `.wav` padahal kontainernya Ogg/MP3 — log runtime memuat `Not a WAV file. File should start with 'RIFF', but found 'OggS'`. Jalankan ulang `python3 tools/convert_to_godot.py --assets`: ekstensi diluruskan dan salinan basi dibuang |
| AAB: ikon item cuma kotak warna | build lama sebelum `godot/assets/items/` ikut repo (33 PNG di-commit); build ulang dari commit terbaru. Untuk checkout lama: `python3 tools/convert_to_godot.py --assets` lalu build ulang |
| AAB: splash pembuka bawaan Godot | `godot/assets/presplash.png` tidak ada saat export, jadi tidak ikut PCK; log runtime memuat "Non-existing or invalid boot splash" |
| Play: "app targets API level too low" | AAB dibangun dari template lama (< 4.7) — build ulang dengan CI terbaru |
| Play: "signature mismatch" | keystore di CI bukan keystore yang di-register di Play Console; pastikan secret `KEYSTORE_BASE64` tidak pernah berganti |
