#!/usr/bin/env bash
# ================================
# tools/build_apk.sh
# Build APK/AAB di komputer sendiri dengan konfigurasi yang SAMA
# persis seperti GitHub Actions.
#
#   ./tools/build_apk.sh            -> APK debug
#   ./tools/build_apk.sh release    -> AAB release
# ================================
set -euo pipefail

# ═══════════════════════════════════════════════════════
# KUNCI VERSI PYTHON — JANGAN DIHAPUS
#
# python-for-android develop memakai Python 3.14, sedangkan
# pygame-ce 2.4.1 hanya mendukung 3.8-3.12 dan berkas _sdl2-nya
# dihasilkan Cython 3.0.0 yang belum mengenal 3.13/3.14.
# Tanpa dua baris ini, build gagal saat mengompilasi
# src_c/_sdl2/sdl2.c.
#
# p4a membaca VERSION_<nama_recipe>. python3 dan hostpython3
# WAJIB versi yang sama (hostpython3 memeriksanya).
# ═══════════════════════════════════════════════════════
export VERSION_python3=3.11.9
export VERSION_hostpython3=3.11.9

MODE="${1:-debug}"

echo "══════════════════════════════════════════════"
echo " Mystic Arena — build Android ($MODE)"
echo " python3     : $VERSION_python3"
echo " hostpython3 : $VERSION_hostpython3"
grep -E "^(android\.archs|android\.api|version) " buildozer.spec || true
grep -E '^\s+version = ' p4a-recipes/pygame-ce/__init__.py || true
echo "══════════════════════════════════════════════"

if [ "$MODE" = "release" ]; then
    : "${P4A_RELEASE_KEYSTORE:?Set dulu P4A_RELEASE_KEYSTORE dan kawan-kawannya}"
    buildozer -v android release
else
    buildozer -v android debug
fi

echo
echo "Hasil ada di folder bin/:"
ls -lh bin/ 2>/dev/null || echo "  (kosong — build gagal?)"
