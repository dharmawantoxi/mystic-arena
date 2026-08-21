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
    """Jalankan fn() n kali, kembalikan ms rata-rata."""
    fn()                      # pemanasan
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000.0


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
    Ukur biaya operasi dasar DI HP INI. Semua angka dalam ms.

    Patokan kasar HP kelas menengah yang SEHAT:
        flip                 < 3 ms
        fill layar penuh     < 2 ms
        blit layar penuh     < 3 ms
        200x draw.circle     < 6 ms
    Kalau flip sendiri sudah > 10 ms -> scaling jatuh ke software.
    """
    w, h = screen.get_size()
    n = 12 if quick else 40

    plain = pygame.Surface((w, h))
    plain_conv = plain.convert()
    alpha = pygame.Surface((w, h), pygame.SRCALPHA)
    alpha.fill((0, 0, 0, 120))
    alpha_conv = alpha.convert_alpha()
    small = pygame.Surface((64, 64), pygame.SRCALPHA)
    small.fill((255, 255, 255, 180))
    small_conv = small.convert_alpha()

    res = {}
    res["flip"] = _t(pygame.display.flip, n)
    res["fill_layar"] = _t(lambda: screen.fill((10, 10, 20)), n)
    res["fill_BLEND(darken)"] = _t(
        lambda: screen.fill((120, 120, 120),
                            special_flags=pygame.BLEND_RGB_MULT), n)
    res["blit_penuh_polos"] = _t(lambda: screen.blit(plain, (0, 0)), n)
    res["blit_penuh_convert"] = _t(lambda: screen.blit(plain_conv, (0, 0)), n)
    res["blit_penuh_alpha"] = _t(lambda: screen.blit(alpha, (0, 0)), n)
    res["blit_penuh_alpha_conv"] = _t(
        lambda: screen.blit(alpha_conv, (0, 0)), n)

    def _blit_small():
        for i in range(100):
            screen.blit(small, (i * 3 % 900, i * 5 % 500))

    def _blit_small_conv():
        for i in range(100):
            screen.blit(small_conv, (i * 3 % 900, i * 5 % 500))

    # ══ UJI KUNCI ══
    # Kalau permukaan TUJUAN punya kanal alpha, SDL memakai blitter
    # generik per-piksel (lambat). Kalau tujuannya XRGB8888 (tanpa
    # alpha), SDL bisa memakai jalur yang jauh lebih cepat.
    # Kita ukur keduanya supaya tahu harus pakai yang mana.
    try:
        noalpha = pygame.Surface((w, h), 0, 32,
                                 (0x00FF0000, 0x0000FF00, 0x000000FF, 0))
        res["blit_alpha_KE_noalpha"] = _t(
            lambda: noalpha.blit(alpha, (0, 0)), n)
        res["_dst_alpha_mask"] = screen.get_masks()[3]
    except Exception as exc:
        print("[DIAG] uji noalpha gagal: %s" % exc)

    # ══ UJI PENENTU ══
    # alphablit.c memakai jalur SIMD hanya kalau Rmask/Gmask/Bmask
    # sumber SAMA PERSIS dengan tujuan. Kita buat surface dengan mask
    # layar lalu ukur; kalau ini jauh lebih cepat, penyebabnya
    # ketidakcocokan format - dan itu bisa kita perbaiki di kode.
    try:
        dm = screen.get_masks()
        matched = pygame.Surface((w, h), pygame.SRCALPHA, 32,
                                 (dm[0], dm[1], dm[2], 0xFF000000))
        matched.fill((10, 20, 30, 120))
        res["blit_alpha_mask_SAMA"] = _t(
            lambda: screen.blit(matched, (0, 0)), n)
        res["_src_masks"] = matched.get_masks()
        res["_dst_masks"] = dm
        print("[DIAG] mask layar  = %s" % (dm,))
        print("[DIAG] mask sumber = %s" % (matched.get_masks(),))
    except Exception as exc:
        print("[DIAG] uji mask sama gagal: %s" % exc)

    res["100x_blit_kecil"] = _t(_blit_small, n)
    res["100x_blit_kecil_conv"] = _t(_blit_small_conv, n)

    # Sprite colorkey: jalur blit tanpa kanal alpha. Inilah yang
    # menentukan apakah cache sprite unit menguntungkan.
    try:
        from mobile.perf import to_colorkey_sprite
        small_ck = to_colorkey_sprite(small)

        def _blit_small_ck():
            for i in range(100):
                screen.blit(small_ck, (i * 3 % 900, i * 5 % 500))

        res["100x_blit_kecil_colorkey"] = _t(_blit_small_ck, n)
    except Exception as exc:
        print("[DIAG] uji colorkey gagal: %s" % exc)

    def _circles():
        for i in range(200):
            pygame.draw.circle(screen, (200, 100, 50),
                               (i * 6 % 1200, i * 11 % 700), 12)

    res["200x_draw.circle"] = _t(_circles, n)

    def _rects():
        for i in range(200):
            pygame.draw.rect(screen, (60, 80, 160),
                             (i * 6 % 1200, i * 11 % 700, 30, 20))

    res["200x_draw.rect"] = _t(_rects, n)

    def _newsurf():
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))

    res["alokasi_surface_penuh"] = _t(_newsurf, max(4, n // 3))

    print("═══════════ DIAG: BENCHMARK (ms) ═══════════")
    for k, v in res.items():
        print("[DIAG] %-24s = %7.2f ms" % (k, v))

    # ── kesimpulan otomatis ──
    verdict = []
    if res["flip"] > 10:
        verdict.append("PRESENTASI LAMBAT: flip() %.1f ms. Scaling 720p "
                       "kemungkinan dikerjakan CPU, bukan GPU." % res["flip"])
    if res["blit_penuh_alpha"] > res["blit_penuh_alpha_conv"] * 1.6:
        verdict.append("FORMAT PIKSEL TIDAK COCOK: blit alpha %.1f ms vs "
                       "%.1f ms setelah convert_alpha() -> pakai convert."
                       % (res["blit_penuh_alpha"],
                          res["blit_penuh_alpha_conv"]))
    ms = res.get("blit_alpha_mask_SAMA")
    if ms and res["blit_penuh_alpha"] > ms * 3:
        verdict.append("PENYEBAB DITEMUKAN: blit alpha dengan mask warna "
                       "SAMA %.0f ms vs %.0f ms (beda mask) = %.0fx. "
                       "Jalur SIMD/NEON pygame hanya aktif kalau mask "
                       "cocok -> semua surface akan disamakan formatnya."
                       % (ms, res["blit_penuh_alpha"],
                          res["blit_penuh_alpha"] / ms))
    arch = RESULTS.get("display", {}).get("arch")
    if arch and arch not in ("aarch64", "arm64", "x86_64"):
        verdict.append("APK BERJALAN 32-BIT (%s): pygame-ce hanya "
                       "mengompilasi blitter NEON untuk arm64. Bangun "
                       "ulang dengan android.archs = arm64-v8a saja."
                       % arch)

    ck = res.get("100x_blit_kecil_colorkey")
    ab = res.get("100x_blit_kecil")
    if ck and ab and ck * 3 < ab:
        verdict.append("SPRITE COLORKEY MENANG: 100 blit kecil %.1f ms "
                       "(alpha) vs %.1f ms (colorkey) = %.1fx -> cache "
                       "sprite unit diaktifkan."
                       % (ab, ck, ab / ck))

    na = res.get("blit_alpha_KE_noalpha")
    if na is not None and res["blit_penuh_alpha"] > na * 2:
        verdict.append("SOLUSINYA KETEMU: blit ke surface TANPA kanal "
                       "alpha %.0f ms vs %.0f ms ke layar. Game akan "
                       "menggambar ke buffer tanpa alpha."
                       % (na, res["blit_penuh_alpha"]))
    if res["blit_penuh_alpha"] > 30:
        verdict.append("ALPHA BLIT SANGAT MAHAL: %.0f ms untuk satu layar "
                       "penuh (~%.0f ns/piksel). Semua efek overlay "
                       "transparan dimatikan otomatis."
                       % (res["blit_penuh_alpha"],
                          res["blit_penuh_alpha"] * 1e6 / (1280 * 720)))
    if res["200x_draw.circle"] > 12:
        verdict.append("CPU GAMBAR LAMBAT: 200 lingkaran %.1f ms -> turunkan "
                       "preset kualitas / kurangi efek."
                       % res["200x_draw.circle"])
    if res["alokasi_surface_penuh"] > 4:
        verdict.append("ALOKASI SURFACE MAHAL: %.1f ms per surface layar "
                       "penuh -> hindari bikin surface tiap frame."
                       % res["alokasi_surface_penuh"])
    if not verdict:
        verdict.append("Operasi dasar terlihat normal. Kalau game tetap "
                       "lambat, penyebabnya jumlah panggilan gambar per "
                       "frame (lihat overlay debug: draw ms).")

    print("═══════════ DIAG: KESIMPULAN ═══════════")
    for v in verdict:
        print("[DIAG] * " + v)
    print("════════════════════════════════════════")

    # Kalau blit dengan mask sama jauh lebih cepat, seragamkan format
    # SEMUA surface alpha supaya jalur SIMD/NEON pygame terpakai.
    try:
        ms = res.get("blit_alpha_mask_SAMA")
        if ms and res.get("blit_penuh_alpha", 0) > ms * 3:
            from mobile.perf import install_surface_format_fix
            install_surface_format_fix(screen)
    except Exception as exc:
        print("[DIAG] gagal menyeragamkan format: %s" % exc)

    # Terapkan profil kualitas berdasar kemampuan NYATA perangkat
    try:
        from mobile.perf import apply_device_profile
        apply_device_profile(res)
    except Exception as exc:
        print("[DIAG] gagal menerapkan profil: %s" % exc)

    RESULTS["bench"] = res
    RESULTS["verdict"] = verdict
    screen.fill((0, 0, 0))
    return res


def should_run():
    if os.environ.get("MYSTIC_BENCH") == "1":
        return True
    if os.environ.get("MYSTIC_BENCH") == "0":
        return False
    return plat.IS_ANDROID          # otomatis di HP


def run_all(screen):
    try:
        log_display_info(screen)
        if should_run():
            run_benchmark(screen)
    except Exception as exc:                       # jangan sampai crash
        print("[DIAG] gagal: %s: %s" % (type(exc).__name__, exc))
