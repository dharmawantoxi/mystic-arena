[app]

# ═══════════════════════════════════════════════════════
# IDENTITAS APLIKASI
# GANTI package.domain dengan domain Anda (dibalik).
# applicationId final = <package.domain>.<package.name>
#   contoh: com.rezastudio.mysticarena
# Nilai ini TIDAK BISA diubah setelah rilis di Play Store!
# ═══════════════════════════════════════════════════════
title = Mystic Arena
package.name = mysticarena
package.domain = com.gantidomainanda

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
# JANGAN tambah INTERNET kalau game tidak butuh jaringan.
# ═══════════════════════════════════════════════════════
android.permissions = android.permission.VIBRATE,android.permission.WAKE_LOCK

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
android.allow_backup = True

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

# Opsional: matikan logcat spam dari SDL
android.logcat_filters = *:S python:D SDL:D

[buildozer]
log_level = 2
warn_on_root = 1
