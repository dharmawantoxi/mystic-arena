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

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
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
            with open("Setup", "w") as fh:
                fh.write(setup_file)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = PygameCERecipe()
