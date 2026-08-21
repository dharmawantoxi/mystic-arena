# ================================
# mobile/_bench_core.py
# MESIN PENGUKUR v21
#
# Kenapa berkas baru?
#   Benchmark lama mengukur 15 hal tapi layar diagnostik hanya
#   MENAMPILKAN 7 di antaranya. Angka paling menentukan
#   (blit setelah convert, blit ke RAM, fill blend) diukur lalu
#   dibuang. Itu sebabnya tiga putaran uji terakhir tidak
#   menghasilkan kesimpulan baru.
#
# Aturan berkas ini:
#   1. SETIAP angka yang diukur WAJIB punya tempat di layar.
#   2. Setiap angka dinormalkan ke ns/piksel, supaya tes dengan
#      luas berbeda bisa dibandingkan langsung.
#   3. Tes dikelompokkan menurut SIAPA yang mengeksekusinya:
#         [SDL]  = kode di dalam libSDL2.so (dibangun NDK, -O2)
#         [PYG]  = kode C milik pygame (dibangun resep p4a kita)
#      Kalau semua [SDL] normal dan semua [PYG] lambat, penyebabnya
#      ada di cara pygame dikompilasi - bukan di kode game.
# ================================

import time

import pygame

# nama tes -> jumlah piksel yang disentuh satu kali pemanggilan
PIXELS = {}

# Urutan tampil di layar: (judul grup, [nama tes, ...])
GROUPS = []

# Ambang "sehat" dalam ns/piksel (bukan ms) supaya adil untuk semua
# ukuran. Patokan HP kelas menengah:
#   tulis polos (fill/copy)      : 1 - 4 ns/piksel
#   blend SIMD (NEON)            : 2 - 8 ns/piksel
#   blend generik C              : 40 - 120 ns/piksel
#   blend generik + SDL_GetRGBA  : 150 - 300 ns/piksel   <- yang kita lihat
NS_SEHAT = 8.0
NS_CURIGA = 40.0


def ns_per_px(res, name):
    px = PIXELS.get(name, 0)
    if not px:
        return None
    v = res.get(name)
    if v is None:
        return None
    return v * 1e6 / px


def _measure(fn, target_ms=50.0, max_iter=300):
    """
    Ukur fn() dengan jumlah iterasi ADAPTIF.

    Tes lama memakai n=12 tetap. Untuk operasi 235 ms itu berarti
    2,8 detik untuk satu baris - layar diagnostik jadi terasa hang
    dan jumlah tes terpaksa dibatasi. Dengan iterasi adaptif, tes
    mahal dijalankan sekali dan tes murah ratusan kali, sehingga
    ketelitiannya seragam tanpa membuang waktu.
    """
    fn()                                   # pemanasan
    t0 = time.perf_counter()
    fn()
    satu = (time.perf_counter() - t0) * 1000.0
    if satu <= 0.0:
        satu = 0.005
    n = int(max(1, min(max_iter, target_ms / satu)))
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n * 1000.0


def bench(res, name, fn, px=0, target_ms=50.0):
    try:
        res[name] = _measure(fn, target_ms)
    except Exception as exc:
        print("[DIAG] %s gagal: %s: %s" % (name, type(exc).__name__, exc))
        res[name] = None
    PIXELS[name] = px
    return res.get(name)


def build_surfaces(screen):
    """
    Siapkan permukaan uji dengan format yang DIKENDALIKAN.

    Ini inti dari uji v21: kita ingin membedakan
      - format tidak cocok  -> jalur generik pygame
      - format cocok        -> syarat gerbang SIMD terpenuhi
      - tujuan layar vs RAM -> memori tekstur vs memori biasa
    """
    w, h = screen.get_size()
    dm = screen.get_masks()
    rm, gm, bm = dm[0], dm[1], dm[2]
    am = dm[3] or ((~(rm | gm | bm)) & 0xFFFFFFFF) or 0xFF000000

    S = pygame.Surface
    # pygame.Surface bisa sudah ditambal perf.install_surface_format_fix;
    # pakai pabrik asli kalau ada supaya format uji benar-benar murni.
    try:
        from mobile.perf import _ORIG_SURFACE as S      # noqa: N806
    except Exception:
        pass

    out = {}
    out["w"], out["h"], out["px"] = w, h, w * h
    out["masks"] = dm

    # ── sumber layar penuh ──
    a_cocok = S((w, h), pygame.SRCALPHA, 32, (rm, gm, bm, am))
    a_cocok.fill((30, 60, 90, 120))
    out["a_cocok"] = a_cocok

    a_mentah = S((w, h), pygame.SRCALPHA)          # format bawaan pygame
    a_mentah.fill((30, 60, 90, 120))
    out["a_mentah"] = a_mentah

    o_cocok = S((w, h), 0, 32, (rm, gm, bm, 0))
    o_cocok.fill((30, 60, 90))
    out["o_cocok"] = o_cocok

    # ── tujuan di RAM ──
    out["ram_opaque"] = S((w, h), 0, 32, (rm, gm, bm, 0))
    out["ram_alpha"] = S((w, h), pygame.SRCALPHA, 32, (rm, gm, bm, am))

    # ── sumber kecil 64x64 ──
    k_alpha = S((64, 64), pygame.SRCALPHA, 32, (rm, gm, bm, am))
    k_alpha.fill((255, 255, 255, 180))
    out["k_alpha"] = k_alpha

    k_opaque = S((64, 64), 0, 32, (rm, gm, bm, 0))
    k_opaque.fill((255, 255, 255))
    out["k_opaque"] = k_opaque

    return out


def run(screen):
    """
    Jalankan seluruh matriks pengukuran.
    Kembalikan dict {nama: ms}; PIXELS & GROUPS ikut terisi.
    """
    del GROUPS[:]
    PIXELS.clear()
    res = {}
    s = build_surfaces(screen)
    w, h, PX = s["w"], s["h"], s["px"]
    KPX = 100 * 64 * 64                       # 100 blit 64x64

    scr = screen
    ram_o = s["ram_opaque"]
    ram_a = s["ram_alpha"]

    def rep(dst, src):
        def f():
            dst.blit(src, (0, 0))
        return f

    def rep100(dst, src):
        def f():
            for i in range(100):
                dst.blit(src, (i * 3 % 900, i * 5 % 500))
        return f

    # ═══ GRUP 1: dikerjakan libSDL2.so (pembanding sehat) ═══
    g1 = []
    bench(res, "flip", pygame.display.flip, 0)
    g1.append("flip")
    bench(res, "fill_layar", lambda: scr.fill((10, 10, 20)), PX)
    g1.append("fill_layar")
    bench(res, "salin_opaque_ke_layar", rep(scr, s["o_cocok"]), PX)
    g1.append("salin_opaque_ke_layar")
    bench(res, "salin_opaque_ke_RAM", rep(ram_o, s["o_cocok"]), PX)
    g1.append("salin_opaque_ke_RAM")

    try:
        from mobile.perf import to_colorkey_sprite
        k_ck = to_colorkey_sprite(s["k_alpha"])
        bench(res, "100x_kecil_colorkey", rep100(scr, k_ck), KPX)
        g1.append("100x_kecil_colorkey")
        # nama lama - dipakai apply_device_profile()
        res["100x_blit_kecil_colorkey"] = res["100x_kecil_colorkey"]
    except Exception as exc:
        print("[DIAG] colorkey gagal: %s" % exc)
    GROUPS.append(("[SDL] kode di libSDL2.so - pembanding sehat", g1))

    # ═══ GRUP 2: kode C pygame, jalur SIMD BUKAN alpha-blit ═══
    # Ini penentu apakah pg_HasSSE_NEON() benar-benar bernilai true.
    # fill blend memakai pemeriksa NEON yang BERBEDA (_pg_HasSSE_NEON
    # di simd_surface_fill_sse2.c) dari alpha-blit.
    g2 = []
    bench(res, "fill_BLEND_MULT",
          lambda: scr.fill((120, 120, 120),
                           special_flags=pygame.BLEND_RGB_MULT), PX)
    g2.append("fill_BLEND_MULT")
    bench(res, "fill_BLEND_ADD",
          lambda: scr.fill((3, 3, 3),
                           special_flags=pygame.BLEND_RGB_ADD), PX)
    g2.append("fill_BLEND_ADD")
    bench(res, "blit_BLEND_ADD",
          lambda: scr.blit(s["o_cocok"], (0, 0),
                           special_flags=pygame.BLEND_RGB_ADD), PX)
    g2.append("blit_BLEND_ADD")
    try:
        buf = pygame.Surface((w // 2, h // 2))
        bench(res, "transform.scale",
              lambda: pygame.transform.scale(s["o_cocok"],
                                             (w // 2, h // 2), buf), PX)
        g2.append("transform.scale")
    except Exception as exc:
        print("[DIAG] scale gagal: %s" % exc)
    GROUPS.append(("[PYG] kode C pygame, jalur SIMD non-alpha", g2))

    # ═══ GRUP 3: jalur ALPHA - tersangka utama ═══
    g3 = []
    bench(res, "alpha_COCOK_ke_layar", rep(scr, s["a_cocok"]), PX)
    g3.append("alpha_COCOK_ke_layar")
    bench(res, "alpha_mentah_ke_layar", rep(scr, s["a_mentah"]), PX)
    g3.append("alpha_mentah_ke_layar")
    bench(res, "alpha_COCOK_ke_RAMopaque", rep(ram_o, s["a_cocok"]), PX)
    g3.append("alpha_COCOK_ke_RAMopaque")
    bench(res, "alpha_COCOK_ke_RAMalpha", rep(ram_a, s["a_cocok"]), PX)
    g3.append("alpha_COCOK_ke_RAMalpha")
    try:
        pre = s["a_cocok"].copy()
        pre = pygame.Surface.premul_alpha(pre) if hasattr(
            pygame.Surface, "premul_alpha") else pre
        bench(res, "alpha_PREMULTIPLIED",
              lambda: scr.blit(pre, (0, 0),
                               special_flags=pygame.BLEND_PREMULTIPLIED), PX)
        g3.append("alpha_PREMULTIPLIED")
    except Exception as exc:
        print("[DIAG] premultiplied gagal: %s" % exc)
    bench(res, "100x_kecil_alpha", rep100(scr, s["k_alpha"]), KPX)
    g3.append("100x_kecil_alpha")
    GROUPS.append(("[PYG] jalur ALPHA BLIT - tersangka utama", g3))

    # nama lama supaya apply_device_profile() tetap jalan
    res["blit_penuh_alpha"] = res.get("alpha_mentah_ke_layar")
    res["blit_alpha_mask_SAMA"] = res.get("alpha_COCOK_ke_layar")
    res["blit_alpha_KE_noalpha"] = res.get("alpha_COCOK_ke_RAMopaque")
    res["100x_blit_kecil"] = res.get("100x_kecil_alpha")
    res["blit_penuh_alpha_conv"] = res.get("alpha_COCOK_ke_layar")

    # ═══ GRUP 4: lain-lain ═══
    g4 = []

    def _circles():
        for i in range(200):
            pygame.draw.circle(scr, (200, 100, 50),
                               (i * 6 % 1200, i * 11 % 700), 12)

    bench(res, "200x_draw.circle", _circles, 200 * 452)
    g4.append("200x_draw.circle")

    def _newsurf():
        x = pygame.Surface((w, h), pygame.SRCALPHA)
        x.fill((0, 0, 0, 0))

    bench(res, "alokasi_surface_penuh", _newsurf, PX, target_ms=40.0)
    g4.append("alokasi_surface_penuh")
    GROUPS.append(("lain-lain", g4))

    scr.fill((0, 0, 0))
    return res


def pygame_mark():
    """Penanda resep p4a yang tertanam di paket pygame terpasang."""
    try:
        import pygame.version as v
        return getattr(v, "P4A_MARK", None)
    except Exception:
        return None


def neon_patch_report():
    try:
        import pygame.version as v
        return getattr(v, "P4A_NEON_PATCH", None)
    except Exception:
        return None


def verdict(res):
    """
    Kesimpulan yang MEMBEDAKAN penyebab, bukan sekadar melaporkan
    bahwa sesuatu lambat.
    """
    out = []
    n = lambda k: ns_per_px(res, k)          # noqa: E731

    mark = pygame_mark()
    android = False
    try:
        from mobile import platform_utils as _plat
        android = _plat.IS_ANDROID
    except Exception:
        pass
    if mark is None and android:
        out.append(("BAD",
                    "pygame di APK ini TIDAK punya penanda resep. "
                    "Artinya pygame TIDAK dikompilasi ulang oleh resep "
                    "kita - tambalan apa pun di resep tidak ada di sini."))
    elif mark:
        out.append(("OK", "resep pygame yang terkompilasi: %s" % mark))

    sdl_ok = n("fill_layar")
    pyg_fill = n("fill_BLEND_MULT")
    alpha_cocok = n("alpha_COCOK_ke_layar")
    alpha_ram = n("alpha_COCOK_ke_RAMopaque")

    if sdl_ok is not None and sdl_ok > NS_SEHAT:
        out.append(("BAD",
                    "Bahkan fill polos lambat (%.1f ns/piksel). Masalahnya "
                    "memori/CPU perangkat, bukan pygame." % sdl_ok))

    # ── penentu 1: apakah SIMD/NEON benar-benar hidup? ──
    if pyg_fill is not None:
        if pyg_fill <= NS_SEHAT:
            out.append(("OK",
                        "SIMD/NEON HIDUP: fill blend %.1f ns/piksel. "
                        "pg_HasSSE_NEON() bernilai true - jadi NEON "
                        "BUKAN penyebab lambatnya alpha blit."
                        % pyg_fill))
        elif pyg_fill >= NS_CURIGA:
            out.append(("BAD",
                        "SIMD/NEON MATI: fill blend %.1f ns/piksel "
                        "(sehat < %.0f). Seluruh jalur SIMD pygame tidak "
                        "terpakai -> tambalan NEON + -O3 di resep belum "
                        "berlaku." % (pyg_fill, NS_SEHAT)))
        else:
            out.append(("WARN",
                        "SIMD/NEON meragukan: fill blend %.1f ns/piksel."
                        % pyg_fill))

    # ── penentu 2: alpha blit ──
    if alpha_cocok is not None:
        if alpha_cocok >= NS_CURIGA:
            sebab = "gerbang SIMD alpha-blit tidak terlewati"
            if pyg_fill is not None and pyg_fill <= NS_SEHAT:
                sebab = ("NEON hidup tapi gerbang ALPHA-BLIT tetap gagal "
                         "(cek src!=dst, Amask, BytesPerPixel==4)")
            out.append(("BAD",
                        "ALPHA BLIT LAMBAT: %.0f ns/piksel walau format "
                        "sumber SAMA PERSIS dengan layar -> %s."
                        % (alpha_cocok, sebab)))
        else:
            out.append(("OK",
                        "ALPHA BLIT SEHAT: %.1f ns/piksel -> efek "
                        "transparan boleh dinyalakan lagi." % alpha_cocok))

    # ── penentu 3: layar vs RAM ──
    if alpha_cocok and alpha_ram:
        if alpha_cocok > alpha_ram * 2.0:
            out.append(("OK",
                        "TUJUAN LAYAR yang mahal: alpha ke RAM %.0f vs ke "
                        "layar %.0f ns/piksel (%.1fx). Solusi: gambar ke "
                        "buffer RAM lalu salin sekali per frame."
                        % (alpha_ram, alpha_cocok, alpha_cocok / alpha_ram)))
        else:
            out.append(("WARN",
                        "Menggambar ke RAM TIDAK membantu (%.1f vs %.1f "
                        "ns/piksel) -> biaya ada di kode blit-nya, bukan "
                        "di jenis memori tujuan."
                        % (alpha_ram, alpha_cocok)))

    # ── penentu 4: premultiplied sebagai jalan pintas ──
    pre = n("alpha_PREMULTIPLIED")
    if pre and alpha_cocok and pre * 2.0 < alpha_cocok:
        out.append(("OK",
                    "JALAN PINTAS: BLEND_PREMULTIPLIED %.0f ns/piksel vs "
                    "alpha biasa %.0f (%.1fx). Sprite bisa disimpan "
                    "pra-kali-alpha - hasil visual identik."
                    % (pre, alpha_cocok, alpha_cocok / pre)))

    # ── penentu 5: colorkey ──
    ck = res.get("100x_kecil_colorkey")
    ab = res.get("100x_kecil_alpha")
    if ck and ab and ck > 0:
        out.append(("OK" if ab / ck < 4 else "WARN",
                    "colorkey vs alpha untuk sprite kecil: %.2f ms vs "
                    "%.2f ms = %.1fx" % (ck, ab, ab / ck)))

    if (res.get("flip") or 0) > 10:
        out.append(("WARN",
                    "flip() %.1f ms -> penyajian/scaling 720p ke layar "
                    "dikerjakan CPU." % res["flip"]))
    return out
