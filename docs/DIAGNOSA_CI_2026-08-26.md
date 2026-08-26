# Diagnosa kegagalan Build Android — 26 Agustus 2026

Run yang gagal: **32929959544** (workflow_dispatch, main @ `8e6363ad`,
jenis build debug). Langkah **"Build APK debug"** mati hanya **53 detik**
setelah mulai (04:23:51 → 04:24:44 UTC). Sebagai pembanding, run sukses
sebelumnya (32925781010, 03:15 UTC) menyelesaikan langkah yang sama —
termasuk kompilasi ulang pygame-ce dan Gradle — dalam **2 menit 28 detik**.

Pesan yang terlihat di akhir log hanyalah:

```
# Command failed: [... pythonforandroid.toolchain apk ...]
# Buildozer failed to execute the last command
# The error might be hidden in the log above this error
```

Error aslinya memang tersembunyi puluhan ribu baris di atasnya, dan log
mentah run itu tidak bisa diambil lewat tooling yang tersedia saat ini.
Dokumen ini mencatat apa yang BISA dipastikan dari luar, dan perbaikan
yang sudah dilakukan.

## Fakta yang terverifikasi

| Fakta | Sumber |
|---|---|
| Run 03:15 sukses dan run 04:22 gagal memakai **kode yang sama untuk keperluan build** (beda hanya sprite Thorne + `_core.py`/`heroes/_bundle.py` — tidak ada perubahan `buildozer.spec`, resep p4a, workflow, atau `src/`) | `git diff 2131412c..8e6363ad` |
| Run gagal memulihkan cache yang **disimpan run sukses** (cache id 7000643429, diakses 04:22:42) | Actions caches API |
| Perintah yang gagal adalah `pythonforandroid.toolchain apk ...` (tahap pengemasan), artinya `p4a create` sempat lolos | baris `# Command failed` di log |
| Kematian di detik ke-≈50 = masih di fase unduhan/resolusi, bukan kompilasi (kompilasi pygame saja ≈60–100 detik) | perbandingan durasi langkah |

## Titik rapuh yang ditemukan (dan sekarang diperbaiki)

Build ini mengunduh ulang beberapa hal **setiap kali build**, dan salah
satunya hampir pasti penyebab kegagalan 50-detik tersebut (gangguan
singkat jaringan/CDN sudah cukup untuk mematikan seluruh build):

1. **Tarball pygame-ce diunduh ulang dari PyPI setiap build.**
   Langkah "Paksa p4a merakit ulang" sengaja menghapus
   `packages/pygame-ce*`, dan p4a hanya mencoba ulang unduhan 5x
   (jeda 1/2/4/8 detik) sebelum menyerah — total ≈40 detik, cocok
   dengan waktu kematian run ini. Fase ini terjadi di perintah
   `p4a create`.
   → **Diperbaiki:** tarball resmi 2.4.1 sekarang disimpan di repo
   (`p4a-recipes/pygame-ce/pygame-ce-2.4.1.tar.gz`, sha256
   `70a84aa1…db9cf0` diverifikasi p4a). Resep menyalinnya kalau berkas
   unduhan tidak ada; jaringan hanya dipakai sebagai jalan terakhir.

2. **`play-services-games-v2:+` mengambil versi terbaru Google setiap
   build.** Rilis baru Google (terakhir v22.0.0, 29 Juli 2026) bisa
   mengubah hasil resolusi Gradle tanpa perubahan kode apa pun, dan
   kegagalan resolusi dependensi juga terjadi di fase `apk`/Gradle.
   → **Diperbaiki:** dipin ke `22.0.0` (versi yang dipakai build-build
   sukses terakhir) di `buildozer.spec`.

3. **python-for-android tidak dipin.** Buildozer default-nya meng-clone
   cabang `master` p4a. Cabang itu kini **dibekukan upstream** di commit
   `58d21141` (rilis v2026.05.09, 10 Mei 2026) sementara pengembangan
   pindah ke `develop` — yang per 24–25 Agustus 2026 baru saja mendapat
   perombakan besar tahap instalasi paket (PR #3366/#3368). Kalau suatu
   saat `master` dihapus/digeser upstream, clone baru di CI gagal total.
   → **Diperbaiki:** `p4a.branch = master` + `p4a.commit =
   58d21141…` di `buildozer.spec`; buildozer melakukan
   `git reset --hard` ke commit itu setiap build sehingga clone lama
   (dari cache) dan clone baru selalu identik.

## Yang BELUM bisa diperbaiki dari sini (butuh akses ke file workflow)

Token bot tidak punya izin `workflows`, jadi `.github/workflows/
build-android.yml` tidak bisa diubah. Dua perubahan di bawah sangat
disarankan dan tinggal tempel:

### A. Buang error asli ke Summary saat build gagal

Tanpa ini, setiap kegagalan memaksa membuka log mentah puluhan ribu
baris. Tambahkan langkah ini tepat sesudah langkah "Build APK debug":

```yaml
      - name: Diagnosa kegagalan build
        if: failure()
        shell: bash
        run: |
          {
            echo "### Diagnosa kegagalan build"
            echo ""
            echo "| | |"
            echo "|---|---|"
            echo "| p4a checkout | \`$(git -C .buildozer/android/platform/python-for-android log -1 --format='%h %ad %s' 2>/dev/null || echo 'tidak ada')\` |"
            echo "| sisa disk | \`$(df -h . | tail -1 | awk '{print $4}')\` |"
            echo "| dist | \`$(ls -d .buildozer/android/platform/build-*/dists/* 2>/dev/null | tr '\n' ' ' || echo '(tidak ada)')\` |"
            echo ""
            echo '#### Error yang terdeteksi (grep)'
            echo '```'
            grep -n -m 30 -E "\[ERROR\]|BuildInterruptingException|Traceback|Exception:|FAILED:|error:|Could not|FAILURE:|Download failed" build.log \
              | cut -c1-400 || echo "(pola error tidak ditemukan)"
            echo '```'
            echo ""
            echo '#### 150 baris terakhir build.log'
            echo '```'
            tail -150 build.log | cut -c1-400
            echo '```'
          } >> $GITHUB_STEP_SUMMARY 2>/dev/null || true
          tail -80 build.log 2>/dev/null || true
```

Hasilnya terbaca di tab **Summary** run — tidak perlu mengunduh log.

### B. Cache Gradle (`~/.gradle`)

`~/.gradle` tidak ikut di-cache, sehingga distribusi Gradle + semua
dependensi Maven (AndroidX, Play Games, dsb.) diunduh ulang setiap
build — ini juga titik gagal yang mungkin. Tambahkan path
`~/.gradle/wrapper` dan `~/.gradle/caches` ke daftar `path:` kedua
langkah cache (restore & save).

## Kalau build masih gagal setelah perbaikan ini

1. Terapkan bagian A di atas, jalankan ulang, baca Summary.
2. Perhatikan baris pertama yang mengandung `[ERROR]` atau
   `Download failed` — itu hampir pasti error aslinya.
3. Bila errornya unduhan (PyPI/Google Maven/Gradle), jalankan ulang
   sekali; gangguan CDN biasanya sementara. Dengan tarball vendored,
   sisi pygame-ce sudah kebal.
