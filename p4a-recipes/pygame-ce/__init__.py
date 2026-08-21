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

from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


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
        path = "src_c/simd_shared.h"
        try:
            with open(path) as fh:
                src = fh.read()
        except OSError:
            return
        needle = "return SDL_HasNEON();"
        if needle not in src:
            print("[pygame-ce] pola SDL_HasNEON tidak ditemukan - "
                  "lewati tambalan")
            return
        patched = ("return 1; /* p4a: ARMv8-A selalu punya NEON, "
                   "SDL_HasNEON() bisa false-negative di Android */")
        src = src.replace(needle, patched, 1)
        with open(path, "w") as fh:
            fh.write(src)
        print("[pygame-ce] TAMBALAN: pg_HasSSE_NEON() dipaksa true "
              "-> blitter NEON dipakai")

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            if arch.arch in ("arm64-v8a", "x86_64"):
                self._patch_neon_runtime_check()
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

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = PygameCERecipe()
