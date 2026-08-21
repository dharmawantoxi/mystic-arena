"""
p4a-recipes/pygame-ce/__init__.py

Resep python-for-android untuk pygame-ce (Community Edition).

═══════════════════════════════════════════════════════════════
KENAPA VERSINYA DIKUNCI DI 2.4.1 — JANGAN DINAIKKAN SEMBARANGAN
═══════════════════════════════════════════════════════════════
pygame-ce 2.5.0 ke atas berpindah ke sistem build **meson-python**
(`build-backend = 'mesonpy'` di pyproject.toml).

python-for-android memasang paket dengan `pip install .`, dan pip
menuruti pyproject.toml itu -> meson dijalankan sebagai **native
build**, bukan cross build. Meson lalu mengompilasi berkas uji
dengan clang NDK (menghasilkan biner ARM) dan mencoba
menjalankannya di runner x86_64, sehingga gagal:

    ERROR: Could not invoke sanity test executable:
    [Errno 8] Exec format error: .../sanitycheckc.exe

pygame-ce **2.4.1** adalah rilis terakhir yang memakai setup.py
(tidak punya pyproject.toml), sehingga jalur klasik p4a — meng-
generate berkas `Setup` dari `buildconfig/Setup.Android.SDL2.in` —
tetap berfungsi. Ini juga pendekatan yang dipakai resep `pygame`
bawaan p4a.

Efek ke game ini: **tidak ada**. Satu-satunya API 2.5+ yang dipakai
kode adalah `pygame.draw.aacircle`, dan seluruh 231 pemakaiannya
sudah dijaga `HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")`
dengan fallback ke `pygame.draw.circle` — yang justru lebih cepat
di HP.

Kalau suatu saat ingin memakai 2.5+, jalurnya adalah menulis ulang
resep ini sebagai subclass `MesonRecipe` milik p4a (yang menulis
berkas cross-file meson), plus menyediakan SDL2 lewat pkg-config.
Itu pekerjaan riset tersendiri — jangan dicoba menjelang rilis.
"""

import os
from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory

# Penanda resep. WAJIB dinaikkan setiap kali isi resep ini berubah.
# Nilainya ditanam ke dalam paket pygame yang terpasang dan bisa
# dibaca di HP lewat layar diagnostik (pygame.version.P4A_MARK),
# sehingga selalu jelas apakah tambalan benar-benar ikut dikompilasi.
RECIPE_MARK = "r22-neonforce+O3"


class PygameCERecipe(CompiledComponentsPythonRecipe):
    version = "2.4.1"
    url = ("https://files.pythonhosted.org/packages/source/p/pygame-ce/"
           "pygame-ce-{version}.tar.gz")

    name = "pygame-ce"
    site_packages_name = "pygame"

    depends = [
        "sdl2",
        "sdl2_image",
        "sdl2_mixer",
        "sdl2_ttf",
        "setuptools",
        "jpeg",
        "png",
    ]

    call_hostpython_via_targetpython = False   # butuh setuptools host
    install_in_hostpython = False

    def should_build(self, arch):
        """
        SELALU bangun ulang pygame.

        python-for-android melewati kompilasi paket yang sudah ada di
        site-packages. Karena cache GitHub Actions memulihkan hasil
        pasang dari build sebelumnya, tambalan di resep ini berkali-kali
        TIDAK pernah masuk APK - dan hasil pengukuran di HP terlihat
        "tidak berubah sama sekali" sehingga hipotesis yang benar pun
        ikut tervonis salah.

        Tambahan waktu ~6-8 menit per build. Jauh lebih murah daripada
        satu putaran uji yang menyesatkan.
        """
        return True

    def _patch_neon_runtime_check(self):
        """
        Paksa jalur SIMD/NEON aktif di arm64.

        Bukti dari perangkat uji (Infinix X6880, aarch64, Android 15):
            blit_penuh_alpha      236,23 ms
            blit_alpha_mask_SAMA  235,65 ms   <- menyamakan mask tidak
                                                 membantu sama sekali

        Artinya syarat format sudah benar, tetapi gerbang RUNTIME
        di alphablit.c gagal:

            #if PG_ENABLE_SSE_NEON
            if ((pg_HasSSE_NEON()) && (src != dst)) { ...SIMD... }

        pg_HasSSE_NEON() memanggil SDL_HasNEON(), yang pada beberapa
        build SDL di Android mengembalikan false untuk aarch64 karena
        memeriksa HWCAP_NEON (nama ARMv7) alih-alih HWCAP_ASIMD.

        Semua CPU ARMv8-A WAJIB punya NEON, jadi pada arm64 pemeriksaan
        itu aman diganti dengan `return 1`.
        """
        # ── KOREKSI v21 ──
        # Ternyata pemeriksaan NEON ADA DI DUA TEMPAT, bukan satu:
        #
        #   src_c/simd_shared.h            -> pg_HasSSE_NEON()
        #                                     dipakai alphablit.c
        #   src_c/simd_surface_fill_sse2.c -> _pg_HasSSE_NEON()
        #                                     dipakai surface_fill.c
        #
        # v20 hanya menambal yang pertama, jadi jalur fill/blend tetap
        # memakai SDL_HasNEON(). Sekarang SEMUA berkas src_c disapu.
        needle = "return SDL_HasNEON();"
        patched = ("return 1; /* p4a: ARMv8-A selalu punya NEON, "
                   "SDL_HasNEON() bisa false-negative di Android */")

        hits = []
        for root, _dirs, files in os.walk("src_c"):
            # jangan sentuh header pihak ketiga (sse2neon.h dsb)
            if os.path.basename(root) == "include":
                continue
            for fn in files:
                if not fn.endswith((".c", ".h")):
                    continue
                p = join(root, fn)
                try:
                    with open(p) as fh:
                        src = fh.read()
                except OSError:
                    continue
                if needle not in src:
                    continue
                n = src.count(needle)
                with open(p, "w") as fh:
                    fh.write(src.replace(needle, patched))
                hits.append("%s (%dx)" % (p, n))

        if hits:
            print("[pygame-ce] TAMBALAN NEON: %s -> dipaksa true"
                  % ", ".join(hits))
        else:
            print("[pygame-ce] PERINGATAN: pola SDL_HasNEON tidak "
                  "ditemukan sama sekali - tambalan NEON TIDAK jalan")
        self._neon_patch_report = hits

    def _inject_probe(self):
        """
        Tanam pemeriksa waktu-kompilasi ke dalam sumber.

        Tambalan runtime v20 (`pg_HasSSE_NEON() -> return 1`) TIDAK
        mengubah apa pun. Kemungkinan besar karena seluruh blok SIMD
        dibuang oleh praprosesor:

            #if PG_ENABLE_SSE_NEON
            if (pg_HasSSE_NEON() ...) { ...SIMD... }
            #endif

        Kalau PG_ENABLE_SSE_NEON bernilai 0, menambal fungsinya sia-sia
        karena kode pemanggilnya tidak ikut dikompilasi - dan tidak ada
        satu pun pesan galat yang muncul. #warning di bawah memaksa
        kompilator MELAPORKAN nilai sebenarnya ke log build.
        """
        probe = (
            "\n/* p4a probe - jangan dihapus */\n"
            "#if defined(__aarch64__)\n"
            "#warning \"P4A-CHECK aarch64=1\"\n"
            "#else\n"
            "#warning \"P4A-CHECK aarch64=0\"\n"
            "#endif\n"
            "#if defined(PG_ENABLE_ARM_NEON) && PG_ENABLE_ARM_NEON\n"
            "#warning \"P4A-CHECK ARM_NEON=1\"\n"
            "#else\n"
            "#warning \"P4A-CHECK ARM_NEON=0\"\n"
            "#endif\n"
            "#if PG_ENABLE_SSE_NEON\n"
            "#warning \"P4A-CHECK SSE_NEON=1 (jalur SIMD IKUT dikompilasi)\"\n"
            "#else\n"
            "#warning \"P4A-CHECK SSE_NEON=0 (jalur SIMD DIBUANG)\"\n"
            "#endif\n"
        )
        path = join("src_c", "alphablit.c")
        try:
            with open(path) as fh:
                src = fh.read()
        except OSError:
            return
        if "P4A-CHECK" in src:
            return
        anchor = '#include "simd_blitters.h"'
        if anchor not in src:
            print("[pygame-ce] jangkar probe tidak ditemukan")
            return
        src = src.replace(anchor, anchor + probe, 1)
        with open(path, "w") as fh:
            fh.write(src)
        print("[pygame-ce] PROBE dipasang di alphablit.c "
              "-> cari 'P4A-CHECK' di log build")

    def _stamp_marker(self, arch):
        """
        Tempelkan penanda ke dalam paket pygame yang TERPASANG.

        Kenapa: berkali-kali kita mengira sebuah tambalan resep sudah
        masuk APK padahal p4a melewati kompilasi pygame karena paketnya
        sudah ada di site-packages hasil cache. Dengan penanda ini,
        layar diagnostik di HP bisa menyebutkan persis versi resep yang
        benar-benar dikompilasi - tidak ada lagi tebak-tebakan.
        """
        path = join("src_py", "version.py")
        try:
            with open(path) as fh:
                src = fh.read()
        except OSError:
            print("[pygame-ce] src_py/version.py tidak ada - "
                  "penanda dilewati")
            return
        if "P4A_MARK" in src:
            return
        extra = (
            "\n\n# ── ditambahkan oleh resep p4a Mystic Arena ──\n"
            "P4A_MARK = %r\n"
            "P4A_ARCH = %r\n"
            "P4A_NEON_PATCH = %r\n"
            "P4A_CFLAGS = %r\n"
        ) % (RECIPE_MARK, arch.arch,
             getattr(self, "_neon_patch_report", []),
             getattr(self, "_cflags_report", ""))
        with open(path, "a") as fh:
            fh.write(extra)
        print("[pygame-ce] PENANDA dipasang: pygame.version.P4A_MARK = %s"
              % RECIPE_MARK)

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            if arch.arch in ("arm64-v8a", "x86_64"):
                self._patch_neon_runtime_check()
            else:
                self._neon_patch_report = []
            self._inject_probe()
            template_path = join("buildconfig", "Setup.Android.SDL2.in")
            with open(template_path) as fh:
                setup_template = fh.read()

            env = self.get_recipe_env(arch)
            env["ANDROID_ROOT"] = join(self.ctx.ndk.sysroot, "usr")

            png = self.get_recipe("png", self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), ".libs")
            png_inc_dir = png.get_build_dir(arch)

            jpeg = self.get_recipe("jpeg", self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)

            sdl_mixer_includes = ""
            for inc in self.get_recipe("sdl2_mixer",
                                       self.ctx).get_include_dirs(arch):
                sdl_mixer_includes += "-I%s " % inc

            sdl_image_includes = ""
            for inc in self.get_recipe("sdl2_image",
                                       self.ctx).get_include_dirs(arch):
                sdl_image_includes += "-I%s " % inc

            # Template 2.4.1 memakai 5 placeholder:
            #   sdl_includes, sdl_ttf_includes, sdl_image_includes,
            #   sdl_mixer_includes, freetype_includes
            # Modul _freetype sudah dikomentari di template, jadi
            # freetype/harfbuzz tidak perlu ada. Path -L untuk png &
            # jpeg dititipkan lewat sdl_includes (seperti resep p4a).
            setup_file = setup_template.format(
                sdl_includes=(
                    " -I" + join(self.ctx.bootstrap.build_dir, "jni", "SDL",
                                 "include")
                    + " -I" + png_inc_dir
                    + " -I" + jpeg_inc_dir
                    + " -L" + join(self.ctx.bootstrap.build_dir, "libs",
                                   str(arch))
                    + " -L" + png_lib_dir
                    + " -L" + jpeg_lib_dir
                    + " -L" + arch.ndk_lib_dir_versioned),
                sdl_ttf_includes="-I" + join(self.ctx.bootstrap.build_dir,
                                             "jni", "SDL2_ttf"),
                sdl_image_includes=sdl_image_includes,
                sdl_mixer_includes=sdl_mixer_includes,
                freetype_includes="",
            )
            # ═══════════════════════════════════════════════
            # BUANG MODUL _sdl2.*  (INI YANG MEMBUAT BUILD LOLOS)
            #
            # Kelima berkas src_c/_sdl2/*.c adalah hasil generate
            # **Cython 3.0.0**, dan hanya berkas itulah yang gagal
            # dikompilasi: isinya penuh API CPython yang sudah
            # dihapus (tp_print 50x, _PyLong_AsByteArray 46x,
            # _PyGen_Send, Py_OptimizeFlag, ...). Modul C pygame
            # yang ditulis tangan tidak bermasalah.
            #
            # Game ini TIDAK memakai pygame._sdl2 sama sekali
            # (0 rujukan), dan pygame/__init__.py hanya mengimpornya
            # pada build statis (cabang `pygame_static`), bukan pada
            # build normal. Jadi modul-modul ini aman dibuang, dan
            # build jadi lebih cepat + kebal terhadap masalah versi
            # Cython/Python.
            #
            # Kalau suatu saat butuh pygame._sdl2 (mis. pygame.Window
            # atau controller API baru), hapus blok ini dan pastikan
            # memakai pygame-ce >= 2.5.6 dengan resep MesonRecipe.
            # ═══════════════════════════════════════════════
            kept, skipped = [], []
            for line in setup_file.splitlines():
                if line.startswith("_sdl2."):
                    skipped.append(line.split()[0])
                    kept.append("# [p4a] dilewati (Cython, tak dipakai): "
                                + line)
                else:
                    kept.append(line)
            setup_file = "\n".join(kept) + "\n"

            from pythonforandroid.logger import info
            info("pygame-ce: modul dilewati -> %s" % ", ".join(skipped))

            with open("Setup", "w") as fh:
                fh.write(setup_file)

            # Penanda ditulis PALING AKHIR supaya laporan tambalan &
            # CFLAGS sudah terisi.
            self._stamp_marker(arch)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"

        # ═══════════════════════════════════════════════
        # OPTIMISASI KOMPILATOR - JANGAN DIHAPUS
        #
        # Blitter pygame (alphablit.c, surface_fill.c,
        # simd_blitters_sse2.c) adalah loop per-piksel yang isinya
        # makro + intrinsik. Tanpa -O2/-O3, sse2neon.h berubah dari
        # instruksi NEON tunggal menjadi pemanggilan fungsi biasa
        # dengan bolak-balik ke stack -> jalur "SIMD" jadi lebih
        # lambat daripada loop generik.
        #
        # Ditaruh di AKHIR string supaya menang atas -O apa pun yang
        # sudah ada sebelumnya (clang memakai flag -O terakhir).
        # ═══════════════════════════════════════════════
        extra = "-O3 -DNDEBUG -fno-math-errno -funroll-loops"
        if arch.arch == "arm64-v8a":
            # Paksa makro dari baris perintah. Header pygame hanya
            # menyalakannya lewat `#if !defined(PG_ENABLE_ARM_NEON) &&
            # defined(__aarch64__)`; kalau karena satu dan lain hal
            # cabang itu tidak jalan, SELURUH jalur SIMD hilang tanpa
            # pesan galat apa pun. Semua CPU ARMv8-A punya NEON, jadi
            # menyalakannya paksa selalu aman di arm64-v8a.
            extra += " -DPG_ENABLE_ARM_NEON=1"
        env["CFLAGS"] = (env.get("CFLAGS", "") + " " + extra).strip()
        self._cflags_report = env["CFLAGS"]

        print("[pygame-ce] CFLAGS FINAL = %s" % env["CFLAGS"])
        return env


recipe = PygameCERecipe()
