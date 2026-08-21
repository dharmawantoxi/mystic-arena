# ================================
# mobile/diagnostics.py
# Uji-diri performa di PERANGKAT NYATA.
#
# Kenapa perlu?
#   Kalau game lambat di HP, penyebabnya bisa 3 hal yang sangat
#   berbeda penanganannya:
#     1. PRESENTASI  - scaling 720p->layar HP jatuh ke software
#        renderer (bukan GPU). Gejala: flip() mahal, semua layar
#        lambat termasuk splash.
#     2. BLIT/FILL   - format piksel surface tidak cocok dengan
#        format layar, jadi setiap blit mengonversi piksel.
#     3. CPU GAMBAR  - memang kebanyakan pygame.draw.* per frame.
#
#   Modul ini mengukur ketiganya langsung di HP lalu mencetak
#   hasilnya ke logcat, sehingga tidak perlu menebak.
#
# Cara pakai:
#   otomatis jalan sekali saat start (±1 detik), atau paksa dengan
#       MYSTIC_BENCH=1
#   Lihat hasilnya:
#       adb logcat -s python:*
# ================================

import os
import time

import pygame

from mobile import platform_utils as plat

RESULTS = {}


def _t(fn, n):
    """Jalankan fn() n kali, kembalikan ms rata-rata (0.0 kalau gagal)."""
    try:
        fn()                  # pemanasan
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        return (time.perf_counter() - t0) / n * 1000.0
    except Exception as exc:
        print("[DIAG] pengukuran gagal: %s: %s" % (type(exc).__name__, exc))
        return 0.0


def log_display_info(screen):
    """Cetak semua yang menentukan cepat/lambatnya presentasi."""
    info = {}
    try:
        info["video_driver"] = pygame.display.get_driver()
    except Exception:
        info["video_driver"] = "?"
    try:
        di = pygame.display.Info()
        info["hw_accel"] = bool(di.hw)
        info["video_mem"] = di.video_mem
        info["desktop"] = "%dx%d" % (di.current_w, di.current_h)
    except Exception:
        pass
    try:
        info["window_size"] = "%dx%d" % pygame.display.get_window_size()
    except Exception:
        pass

    info["surface_size"] = "%dx%d" % screen.get_size()
    info["bitsize"] = screen.get_bitsize()
    info["masks"] = screen.get_masks()
    info["alpha"] = screen.get_alpha()
    flags = screen.get_flags()
    info["SCALED"] = bool(flags & pygame.SCALED)
    info["FULLSCREEN"] = bool(flags & pygame.FULLSCREEN)
    info["OPENGL"] = bool(flags & pygame.OPENGL)
    info["HWSURFACE"] = bool(flags & pygame.HWSURFACE)
    info["DOUBLEBUF"] = bool(flags & pygame.DOUBLEBUF)
    info["scale_factor"] = round(plat.get_scale(), 3)
    # ══ PENENTU JALUR CEPAT NEON ══
    # pygame-ce hanya mengompilasi blitter SIMD kalau __aarch64__
    # terdefinisi. Kalau APK berjalan 32-bit (armv7l), SELURUH SIMD
    # mati -> alpha blit jatuh ke loop C generik.
    import platform as _pf
    import sys as _sys
    info["arch"] = _pf.machine()
    info["bits"] = 64 if _sys.maxsize > 2 ** 32 else 32
    info["simd_mungkin"] = (info["arch"] in ("aarch64", "arm64", "x86_64")
                            and info["bits"] == 64)
    info["env_RENDER_DRIVER"] = os.environ.get("SDL_RENDER_DRIVER", "-")
    info["env_SCALE_QUALITY"] = os.environ.get(
        "SDL_HINT_RENDER_SCALE_QUALITY", "-")

    print("═══════════ DIAG: DISPLAY ═══════════")
    for k, v in info.items():
        print("[DIAG] %-18s = %s" % (k, v))
    RESULTS["display"] = info
    return info


def run_benchmark(screen, quick=True):
    """
    Ukur biaya operasi dasar DI HP INI (mesin: mobile/_bench_core.py).

    v21: seluruh matriks pengukuran dipindah ke _bench_core supaya
    SETIAP angka yang diukur pasti ikut ditampilkan di layar. Versi
    lama mengukur 15 hal tapi hanya menampilkan 7 - angka penentunya
    justru yang dibuang.
    """
    from mobile import _bench_core as bc

    res = bc.run(screen)

    print("\u2550\u2550\u2550\u2550\u2550 DIAG: BENCHMARK v21 \u2550\u2550\u2550\u2550\u2550")
    for judul, keys in bc.GROUPS:
        print("[DIAG] -- %s" % judul)
        for k in keys:
            v = res.get(k)
            if v is None:
                print("[DIAG]    %-26s GAGAL" % k)
                continue
            nsp = bc.ns_per_px(res, k)
            if nsp is None:
                print("[DIAG]    %-26s %8.2f ms" % (k, v))
            else:
                print("[DIAG]    %-26s %8.2f ms  %7.1f ns/piksel"
                      % (k, v, nsp))

    verdict_pairs = bc.verdict(res)
    verdict = ["%s%s" % ("" if lv == "OK" else "! ", txt)
               for lv, txt in verdict_pairs]

    print("\u2550\u2550\u2550\u2550\u2550 DIAG: KESIMPULAN \u2550\u2550\u2550\u2550\u2550")
    for lv, txt in verdict_pairs:
        print("[DIAG] [%-4s] %s" % (lv, txt))
    print("\u2550" * 40)

    # Terapkan profil kualitas berdasar kemampuan NYATA perangkat.
    # CATATAN v21: install_surface_format_fix() TIDAK lagi dipanggil.
    # Pengukuran v19/v20 membuktikan menyamakan mask tidak mengubah
    # apa pun (235,17 vs 236,23 ms), sementara menambal pygame.Surface
    # secara global menambah risiko tanpa manfaat terukur.
    try:
        from mobile.perf import apply_device_profile
        apply_device_profile(res)
    except Exception as exc:
        print("[DIAG] gagal menerapkan profil: %s" % exc)

    RESULTS["bench"] = res
    RESULTS["verdict"] = verdict
    RESULTS["verdict_pairs"] = verdict_pairs
    RESULTS["groups"] = bc.GROUPS
    RESULTS["pygame_mark"] = bc.pygame_mark()
    RESULTS["neon_patch"] = bc.neon_patch_report()
    return res


def should_run():
    if os.environ.get("MYSTIC_BENCH") == "1":
        return True
    if os.environ.get("MYSTIC_BENCH") == "0":
        return False
    return plat.IS_ANDROID          # otomatis di HP


def run_all(screen):
    """
    Info layar + uji-diri. Dibuat SANGAT defensif: kegagalan di sini
    dulu membuat apply_device_profile() tidak pernah jalan, sehingga
    seluruh optimasi perangkat lambat ikut mati (bug v18).
    """
    try:
        log_display_info(screen)
    except Exception as exc:
        print("[DIAG] info layar gagal: %s: %s" % (type(exc).__name__, exc))

    if not should_run():
        return

    res = {}
    try:
        res = run_benchmark(screen)
    except Exception as exc:
        print("[DIAG] benchmark gagal: %s: %s" % (type(exc).__name__, exc))

    # Jaring pengaman: kalau benchmark gagal total, perangkat Android
    # tetap dianggap lambat supaya jalur hemat menyala.
    try:
        from mobile.perf import apply_device_profile, Quality, LOW
        if res:
            apply_device_profile(res)
        elif plat.IS_ANDROID:
            Quality.apply(LOW)
            Quality.cheap_alpha = False
            Quality.sprite_cache = True
            print("[PERF] Benchmark gagal -> paksa mode hemat "
                  "(cheap_alpha=False, sprite_cache=True)")
    except Exception as exc:
        print("[DIAG] profil perangkat gagal: %s: %s"
              % (type(exc).__name__, exc))
