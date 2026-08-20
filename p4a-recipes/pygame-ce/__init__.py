"""
p4a-recipes/pygame-ce/__init__.py

Resep python-for-android untuk pygame-ce (Community Edition).

Kenapa resep lokal?
  Resep `pygame` bawaan p4a masih menunjuk pygame 2.1.0 dan ditandai
  "broken" oleh maintainer. pygame-ce 2.5.x sudah punya berkas
  buildconfig/Setup.Android.SDL2.in yang siap dipakai lintas-kompilasi.

Cara menaikkan versi:
  1. Ubah `version` di bawah ke rilis pygame-ce terbaru yang stabil.
  2. Hapus cache: rm -rf .buildozer/android/platform/build-*
  3. buildozer android debug
"""

from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


class PygameCERecipe(CompiledComponentsPythonRecipe):
    version = "2.5.3"
    url = ("https://github.com/pygame-community/pygame-ce/archive/"
           "refs/tags/{version}.tar.gz")

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

            setup_file = setup_template.format(
                sdl_includes=(
                    " -I" + join(self.ctx.bootstrap.build_dir, "jni", "SDL",
                                 "include")
                    + " -L" + join(self.ctx.bootstrap.build_dir, "libs",
                                   str(arch))
                    + " -L" + png_lib_dir
                    + " -L" + jpeg_lib_dir
                    + " -L" + arch.ndk_lib_dir_versioned),
                sdl_ttf_includes="-I" + join(self.ctx.bootstrap.build_dir,
                                             "jni", "SDL2_ttf"),
                sdl_image_includes=sdl_image_includes,
                sdl_mixer_includes=sdl_mixer_includes,
                jpeg_includes="-I" + jpeg_inc_dir,
                png_includes="-I" + png_inc_dir,
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
