[app]

# ═══════════════════════════════════════════════════════
# IDENTITAS APLIKASI
# applicationId final = <package.domain>.<package.name>
#   = io.github.dharmawantoxi.mysticarena
# Berbasis username GitHub (dharmawantoxi) — unik sedunia, tidak
# perlu punya domain sungguhan.
# Nilai ini TIDAK BISA diubah setelah rilis di Play Store — Google
# Play Games Saved Games mengikat snapshot ke applicationId ini;
# mengubahnya berarti save cloud pemain tidak akan ditemukan lagi.
# ═══════════════════════════════════════════════════════
title = Mystic Arena
package.name = mysticarena
package.domain = io.github.dharmawantoxi

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,otf,wav,ogg,mp3,json,txt
# p4a-recipes ikut dikecualikan supaya tarball vendored pygame-ce
# (14 MB, bahan build - bukan kode game) tidak pernah ikut terkemas
# ke dalam APK, apa pun aturan ekstensi di atas.
source.exclude_dirs = tools,tests,docs,.github,.buildozer,bin,__pycache__,.git,p4a-recipes
source.exclude_patterns = main_desktop_legacy.py,smoke_test.py,*.spec.bak

# version.code dinaikkan TIAP upload ke Play Console
version = 1.0.0
android.numeric_version = 1

# ═══════════════════════════════════════════════════════
# DEPENDENSI PYTHON
#   pygame-ce -> dibangun dari resep lokal p4a-recipes/pygame-ce
#   pyjnius   -> supaya mobile/platform_utils.py bisa panggil API
#                Android (getar, keep-screen-on, immersive mode)
#   android   -> modul helper bawaan p4a
# ═══════════════════════════════════════════════════════
requirements = python3,pygame-ce,pyjnius,android

# ⚠ VERSI PYTHON DIKUNCI DI LUAR BERKAS INI
# p4a develop memakai Python 3.14; pygame-ce 2.4.1 hanya mendukung
# 3.8-3.12. Versi dipaksa lewat variabel lingkungan (buildozer.spec
# tidak punya opsi untuk ini):
#     export VERSION_python3=3.11.9
#     export VERSION_hostpython3=3.11.9
# Sudah diatur otomatis di .github/workflows/build-android.yml dan
# tools/build_apk.sh. Kalau menjalankan `buildozer` manual, pakai
# skrip itu — jangan panggil buildozer langsung.

# ═══════════════════════════════════════════════════════
# CLOUD SAVE (Google Play Games Saved Games / Snapshots)
#   - android.add_src       : CloudSaveBridge.java (bridge Python↔Java)
#   - android.gradle_dependencies : Play Games Services v2 SDK.
#     Setelah PLAY CONSOLE disiapkan (Saved Games ON + APP_ID),
#     buildozer otomatis menaruh meta-data APP_ID lewat
#     tools/p4a_hooks.py (dibaca dari env MYSTIC_GAMES_PROJECT_ID
#     atau file android_games_app_id.txt).
#   - Kalau APP_ID belum diisi, fitur cloud NONAKTIF (tidak crash).
# ═══════════════════════════════════════════════════════
android.add_src = %(source.dir)s/src
# ⚠ VERSI DIPIN, BUKAN "+"
# Dengan "+", Gradle mengambil versi TERBARU play-services-games-v2
# SETIAP build (maven-metadata berubah-ubah). Rilis baru Google bisa
# mengubah hasil resolusi dependensi tanpa satu pun perubahan kode —
# build yang kemarin hijau tiba-tiba merah, dan gagal build di CI yang
# cuma ~50 detik mustahil didiagnosa tanpa log lengkap.
# 22.0.0 adalah versi yang dipakai build-build sukses terakhir
# (rilis Google 29 Juli 2026). Naikkan DENGAN SENGAJA kalau memang
# ingin pindah versi, lalu uji dulu.
android.gradle_dependencies = com.google.android.gms:play-services-games-v2:22.0.0
# Play Games v2 memakai library AndroidX (transitif) — wajib dinyalakan
# supaya Gradle tidak gagal dengan "Dependency requires AndroidX".
android.enable_androidx = True

# ═══════════════════════════════════════════════════════
# TAMPILAN
# ═══════════════════════════════════════════════════════
orientation = landscape
fullscreen = 1
android.presplash_color = #0B0A12
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# ═══════════════════════════════════════════════════════
# PERMISSION (sedikit = review Play Store lebih mudah)
#   VIBRATE   -> feedback tombol skill
#   WAKE_LOCK -> layar tidak mati saat menonton cinematic
#   INTERNET + ACCESS_NETWORK_STATE
#             -> Cloud Save Google Play Games (upload/download save
#                ke akun Google). Google Play Games memerlukan izin
#                jaringan.
#   (Izin storage TIDAK dipakai lagi — fitur save lokal ke folder
#    Download sudah dihapus; save hanya lewat Google Play Games.)
# ═══════════════════════════════════════════════════════
android.permissions = android.permission.VIBRATE,android.permission.WAKE_LOCK,android.permission.INTERNET,android.permission.ACCESS_NETWORK_STATE

# ═══════════════════════════════════════════════════════
# TARGET ANDROID
#   api 36   -> WAJIB untuk submission baru mulai 31 Agustus 2026
#   minapi 24 -> Android 7.0, mencakup >98% perangkat aktif
#   arch: WAJIB ada arm64-v8a (64-bit).
#         armeabi-v7a (HP 32-bit lama) SENGAJA dimatikan dulu: tiap
#         arch dikompilasi terpisah, jadi 2 arch = 2x waktu build.
#         Aktifkan lagi menjelang rilis dengan:
#             android.archs = arm64-v8a
# ═══════════════════════════════════════════════════════
android.api = 36
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

# ═══════════════════════════════════════════════════════
# SAVE — HANYA Google Play Games (Android Auto Backup DIMATIKAN)
# Fitur save lokal (export/import ke folder Download) dan Android
# Auto Backup (Google Drive) sudah dihapus. Satu-satunya mekanisme
# save/restore pemain adalah Google Play Games Saved Games
# (mobile/cloud_save.py + CloudSaveBridge.java).
#
# android.allow_backup = False  -> Android TIDAK menyalin data app
# (termasuk folder saves/ working copy) ke Google Drive. Ini penting
# supaya setelah install ulang, slot working copy benar-benar kosong
# dan dialog "restore dari cloud" (Google Play Games) yang muncul —
# bukan data Drive yang mungkin lebih lama.
# ═══════════════════════════════════════════════════════
android.allow_backup = False

# aab untuk Play Store, apk untuk uji manual
android.release_artifact = aab
android.debug_artifact = apk

# ═══════════════════════════════════════════════════════
# PYTHON-FOR-ANDROID
# Resep pygame-ce ada di folder p4a-recipes/ (resep bawaan p4a
# masih menunjuk pygame 2.1.0 yang ditandai broken).
#
# ⚠ VERSI P4A DIKUNCI — JANGAN DIHAPUS
# Buildozer default-nya meng-clone cabang `master` python-for-android
# TANPA pin. Cabang master p4a sudah DIBEKUKAN upstream di commit
# 58d21141 (rilis v2026.05.09); pengembangan pindah ke `develop`.
# Tanpa pin eksplisit:
#   - kalau upstream menghapus/memindahkan `master`, clone baru di CI
#     gagal total dan build mati di menit pertama;
#   - kalau `master` digerakkan lagi, build berubah tanpa kita ubah
#     apa pun (pernah terjadi: default Python p4a develop naik ke 3.14
#     dan merusak kompilasi pygame-ce).
# p4a.commit memaksa `git reset --hard` ke commit ini setiap build,
# jadi hasil clone lama (cache) maupun clone baru selalu identik.
# ═══════════════════════════════════════════════════════
p4a.bootstrap = sdl2
p4a.branch = master
p4a.commit = 58d21141f17c889bf8585f5665921d72028f8831
p4a.local_recipes = ./p4a-recipes
p4a.hook = tools/p4a_hooks.py

# Opsional: matikan logcat spam dari SDL
android.logcat_filters = *:S python:D SDL:D

[buildozer]
log_level = 2
warn_on_root = 1
