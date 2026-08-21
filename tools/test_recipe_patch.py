"""
tools/test_recipe_patch.py

Menjalankan penambalan resep p4a terhadap SUMBER pygame-ce ASLI,
di sini, dalam hitungan detik.

Kenapa ada
──────────
Build Android memakan 35-50 menit. Dua kali build gagal karena
kesalahan sepele di resep — sekali karena pemeriksaan NEON hanya
ditambal di satu dari dua berkas, sekali karena satu header berisi
tabel font biner dan bukan UTF-8:

    UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80
    in position 30322

Kesalahan seperti itu tidak boleh lagi ditemukan oleh runner.

Yang diperiksa
──────────────
  1. penambalan NEON kena di KEDUA berkas yang memuat polanya
  2. tidak ada berkas yang rusak / gagal dibaca (termasuk yang biner)
  3. probe #warning tertanam di alphablit.c
  4. src_py/version.py tetap Python yang sah setelah ditempeli penanda
  5. berkas biner tidak berubah satu byte pun

Jalankan:
    python3 tools/test_recipe_patch.py [/path/ke/pygame-ce-2.4.1]

Kalau path tidak diberikan, sumbernya diunduh dari PyPI (±14 MB).
"""

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import types
import urllib.request

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEP = os.path.join(AKAR, "p4a-recipes", "pygame-ce", "__init__.py")
URL = ("https://files.pythonhosted.org/packages/source/p/pygame-ce/"
       "pygame-ce-2.4.1.tar.gz")
BINER = os.path.join("src_c", "SDL_gfx", "SDL_gfxPrimitives_font.h")


def muat_resep():
    """
    Impor modul resep tanpa python-for-android terpasang.

    Resep hanya memakai p4a untuk kelas induk dan satu helper, jadi
    keduanya cukup diganti boneka.
    """
    pfa = types.ModuleType("pythonforandroid")
    recipe_mod = types.ModuleType("pythonforandroid.recipe")
    toolchain_mod = types.ModuleType("pythonforandroid.toolchain")
    logger_mod = types.ModuleType("pythonforandroid.logger")

    class _Recipe:
        def prebuild_arch(self, arch):
            pass

        def get_recipe_env(self, arch):
            return {"CFLAGS": "-target aarch64-linux-android24"}

    recipe_mod.CompiledComponentsPythonRecipe = _Recipe
    toolchain_mod.current_directory = None
    logger_mod.info = print

    sys.modules["pythonforandroid"] = pfa
    sys.modules["pythonforandroid.recipe"] = recipe_mod
    sys.modules["pythonforandroid.toolchain"] = toolchain_mod
    sys.modules["pythonforandroid.logger"] = logger_mod

    import importlib.util
    spec = importlib.util.spec_from_file_location("resep_pygame", RESEP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def siapkan_sumber(arg):
    if arg and os.path.isdir(arg):
        asal = arg
    else:
        cache = os.path.join(tempfile.gettempdir(), "pgce-src")
        asal = os.path.join(cache, "pygame-ce-2.4.1")
        if not os.path.isdir(asal):
            os.makedirs(cache, exist_ok=True)
            tgz = os.path.join(cache, "pygame-ce-2.4.1.tar.gz")
            if not os.path.exists(tgz):
                print("mengunduh sumber pygame-ce 2.4.1 (~14 MB)...")
                urllib.request.urlretrieve(URL, tgz)
            print("membongkar...")
            with tarfile.open(tgz) as tf:
                tf.extractall(cache)
    kerja = tempfile.mkdtemp(prefix="ujiresep-")
    tujuan = os.path.join(kerja, "src")
    shutil.copytree(asal, tujuan)
    return tujuan


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    src = siapkan_sumber(arg)
    mod = muat_resep()
    resep = mod.PygameCERecipe()

    sebelum_biner = None
    p_biner = os.path.join(src, BINER)
    if os.path.exists(p_biner):
        sebelum_biner = hashlib.sha256(open(p_biner, "rb").read()).hexdigest()

    kerja_lama = os.getcwd()
    os.chdir(src)
    gagal = []
    try:
        print("\n── 1. tambalan NEON ──")
        resep._patch_neon_runtime_check()
        hits = getattr(resep, "_neon_patch_report", [])
        if len(hits) != 2:
            gagal.append("tambalan NEON kena %d berkas, seharusnya 2 "
                         "(simd_shared.h + simd_surface_fill_sse2.c)"
                         % len(hits))
        sisa = subprocess.run(
            ["grep", "-rl", "return SDL_HasNEON();", "src_c"],
            capture_output=True, text=True).stdout.strip()
        if sisa:
            gagal.append("masih ada SDL_HasNEON() belum ditambal: %s" % sisa)
        else:
            print("   semua pemeriksaan NEON tertambal")

        print("\n── 2. probe #warning ──")
        resep._cflags_report = "-O3 -DPG_ENABLE_ARM_NEON=1"
        resep._inject_probe()
        ab = open(os.path.join("src_c", "alphablit.c"), "rb").read()
        for pola in (b"P4A-CHECK aarch64", b"P4A-CHECK ARM_NEON",
                     b"P4A-CHECK SSE_NEON"):
            if pola not in ab:
                gagal.append("probe %s tidak tertanam" % pola.decode())
        if not gagal:
            print("   ketiga probe tertanam di alphablit.c")

        print("\n── 3. penanda di version.py ──")

        class _Arch:
            arch = "arm64-v8a"

        resep._stamp_marker(_Arch())
        vp = os.path.join("src_py", "version.py")
        isi = open(vp, encoding="utf-8").read()
        try:
            ast.parse(isi)
            print("   version.py tetap Python yang sah")
        except SyntaxError as e:
            gagal.append("version.py rusak: %s" % e)
        if "P4A_MARK" not in isi:
            gagal.append("P4A_MARK tidak tertulis")
        else:
            for baris in isi.splitlines()[-4:]:
                if baris.strip():
                    print("   %s" % baris)

        print("\n── 4. jalankan dua kali (harus aman diulang) ──")
        resep._patch_neon_runtime_check()
        resep._inject_probe()
        resep._stamp_marker(_Arch())
        isi2 = open(vp, encoding="utf-8").read()
        if isi2.count("P4A_MARK") != 1:
            gagal.append("penanda tertulis ganda saat dijalankan ulang")
        else:
            print("   aman diulang")

        print("\n── 5. berkas biner tidak tersentuh ──")
        if sebelum_biner:
            sesudah = hashlib.sha256(open(p_biner, "rb").read()).hexdigest()
            if sesudah != sebelum_biner:
                gagal.append("%s BERUBAH - penambalan merusak berkas biner"
                             % BINER)
            else:
                print("   %s utuh (%s...)" % (os.path.basename(BINER),
                                              sesudah[:12]))
    finally:
        os.chdir(kerja_lama)
        shutil.rmtree(os.path.dirname(src), ignore_errors=True)

    print()
    if gagal:
        print("HASIL: GAGAL")
        for g in gagal:
            print("  - %s" % g)
        return 1
    print("HASIL: LULUS. Resep aman dijalankan di runner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
