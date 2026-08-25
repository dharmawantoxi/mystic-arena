[app]

# ═══════════════════════════════════════════════════════
# IDENTITAS APLIKASI
# applicationId final = <package.domain>.<package.name>
#   = io.github.dharmawantoxi.mysticarena
# Berbasis username GitHub (dharmawantoxi) — unik sedunia, tidak
# perlu punya domain sungguhan.
# Nilai ini TIDAK BISA diubah setelah rilis di Play Store, dan
# Android Auto Backup diikat ke applicationId ini — mengubahnya
# berarti backup lama pemain tidak akan di-restore!
# ═══════════════════════════════════════════════════════
title = Mystic Arena
package.name = mysticarena
package.domain = io.github.dharmawantoxi

source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,otf,wav,ogg,mp3,json,txt
source.exclude_dirs = tools,tests,docs,.github,.buildozer,bin,__pycache__,.git
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
android.gradle_dependencies = com.google.android.gms:play-services-games-v2:+
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
#   WRITE/READ_EXTERNAL_STORAGE (maxSdkVersion=28)
#             -> HANYA Android 7-9: backup lokal ke folder publik
#                Download/MysticArena (lihat backup_manager.py).
#                Android 10+ memakai MediaStore.Downloads yang TIDAK
#                butuh permission, jadi izin ini tidak pernah muncul
#                di perangkat modern.
#   INTERNET + ACCESS_NETWORK_STATE
#             -> Cloud Save Google Play Games (upload/download save
#                ke akun Google). Google Play Games memerlukan izin
#                jaringan.
# ═══════════════════════════════════════════════════════
android.permissions = android.permission.VIBRATE,android.permission.WAKE_LOCK,android.permission.INTERNET,android.permission.ACCESS_NETWORK_STATE,(name=android.permission.WRITE_EXTERNAL_STORAGE;maxSdkVersion=28),(name=android.permission.READ_EXTERNAL_STORAGE;maxSdkVersion=28)

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
# AUTO BACKUP (Google Drive) — progres selamat dari uninstall
# Save game disimpan di $ANDROID_PRIVATE/saves (lihat
# storage_paths.py) dan di-backup otomatis ke Google Drive milik
# pemain. Saat install ulang / pindah HP dengan akun Google yang
# sama, Android me-restore folder itu SEBELUM game pertama dibuka.
#
# Aturan backup dibatasi HANYA ke folder saves/ — tanpa ini seluruh
# files/ (kode + aset hasil ekstrak p4a) ikut ter-backup dan hampir
# pasti melebihi kuota 25 MB, yang membuat backup GAGAL total.
#   backup_rules.xml            -> Android <= 11 (fullBackupContent)
#   data_extraction_rules.xml   -> Android 12+   (dataExtractionRules)
# ═══════════════════════════════════════════════════════
android.allow_backup = True
android.backup_rules = backup_rules.xml
android.res_xml = data_extraction_rules.xml
# JANGAN pakai android.extra_manifest_application_arguments untuk
# dataExtractionRules di Buildozer 1.5.0: argumennya dikutip sebagai
# teks literal dan membuat AndroidManifest.xml tidak valid. Atribut
# Android 12+ itu ditambahkan oleh p4a.hook di bawah setelah manifest
# dirender oleh python-for-android.

# aab untuk Play Store, apk untuk uji manual
android.release_artifact = aab
android.debug_artifact = apk

# ═══════════════════════════════════════════════════════
# PYTHON-FOR-ANDROID
# Resep pygame-ce ada di folder p4a-recipes/ (resep bawaan p4a
# masih menunjuk pygame 2.1.0 yang ditandai broken).
# ═══════════════════════════════════════════════════════
p4a.bootstrap = sdl2
p4a.local_recipes = ./p4a-recipes
p4a.hook = tools/p4a_hooks.py

# Opsional: matikan logcat spam dari SDL
android.logcat_filters = *:S python:D SDL:D

[buildozer]
log_level = 2
warn_on_root = 1
