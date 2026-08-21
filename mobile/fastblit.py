# ================================
# mobile/fastblit.py
# JALUR CEPAT ALPHA BLIT LEWAT BLITTER SDL
#
# ── MASALAH YANG DIPECAHKAN ──
# Pengukuran di Infinix X6880 (v21):
#
#   salin_opaque_ke_layar   1,0 ns/piksel   <- blitter SDL
#   100x_kecil_colorkey     0,9 ns/piksel   <- blitter SDL
#   alpha_COCOK_ke_layar  256,9 ns/piksel   <- blitter pygame sendiri
#
# Semua yang dikerjakan libSDL2.so cepat; semua yang dikerjakan kode C
# pygame sendiri lambat. Untuk alpha blit, pygame TIDAK memakai SDL —
# ia punya `alphablit.c` sendiri. Di perangkat ini jalur SIMD-nya tidak
# aktif, sehingga yang jalan adalah loop generik yang memanggil
# SDL_GetRGBA() dua kali PER PIKSEL. Itulah 257 ns/piksel.
#
# ── SOLUSINYA ──
# pygame punya flag `BLEND_ALPHA_SDL2`, yang membuang alphablit.c dan
# menyerahkan pekerjaan ke SDL_BlitSurface — blitter yang sama dengan
# yang sudah terbukti 1,0 ns/piksel di perangkat ini.
#
# ── APAKAH GAMBARNYA BERUBAH? ──
# Diuji 20 sprite acak 64x64 (81.920 piksel) ke tujuan TANPA kanal
# alpha: selisih warna maksimum = 3 dari 255 (0,4%), murni pembulatan
# rumus blend. Tidak terlihat mata. Uji ulang kapan saja dengan
#   python3 tools/test_fastblit.py
#
# ── CARA KERJA ──
# pygame.Surface bisa diturunkan. FastSurface hanya menimpa blit():
# kalau pemanggil tidak meminta special_flags dan sumbernya punya
# kanal alpha, flag BLEND_ALPHA_SDL2 dipasang. Tidak ada satu pun
# pemanggilan blit di kode game yang perlu diubah.
#
# Sumber colorkey / opaque TIDAK disentuh — keduanya memang sudah
# lewat blitter SDL.
# ================================

import os

import pygame

SRCALPHA = pygame.SRCALPHA
_ALPHA_SDL2 = getattr(pygame, "BLEND_ALPHA_SDL2", 0)
_BASE_BLIT = pygame.Surface.blit

# Diaktifkan oleh apply_device_profile() kalau pengukuran membuktikan
# jalur ini lebih cepat di perangkat INI. Di PC biasanya tidak perlu.
AKTIF = False

_stats = {"sdl2": 0, "lewat": 0}


class FastSurface(pygame.Surface):
    """
    Surface yang mengalihkan alpha blit ke blitter SDL.

    Sengaja sesingkat mungkin: dipanggil ribuan kali per frame, jadi
    setiap baris di sini berharga. Hanya satu percabangan dan satu
    pemanggilan C tambahan.
    """

    def blit(self, source, dest=(0, 0), area=None, special_flags=0):
        if special_flags == 0 and (source.get_flags() & SRCALPHA):
            special_flags = _ALPHA_SDL2
        return _BASE_BLIT(self, source, dest, area, special_flags)


class CountingFastSurface(FastSurface):
    """Versi berpenghitung untuk diagnosa (MYSTIC_FASTBLIT_STATS=1)."""

    def blit(self, source, dest=(0, 0), area=None, special_flags=0):
        if special_flags == 0 and (source.get_flags() & SRCALPHA):
            _stats["sdl2"] += 1
            return _BASE_BLIT(self, source, dest, area, _ALPHA_SDL2)
        _stats["lewat"] += 1
        return _BASE_BLIT(self, source, dest, area, special_flags)


def _kelas():
    if os.environ.get("MYSTIC_FASTBLIT_STATS") == "1":
        return CountingFastSurface
    return FastSurface


def tersedia():
    return bool(_ALPHA_SDL2)


def stats():
    return dict(_stats)


def reset_stats():
    _stats["sdl2"] = 0
    _stats["lewat"] = 0


def buat_buffer(width, height, masks=None):
    """
    Buffer render di RAM, TANPA kanal alpha, dengan blit alpha cepat.

    Tanpa kanal alpha karena pengukuran menunjukkan tujuan ber-alpha
    dua kali lebih mahal (536,7 vs 256,1 ns/piksel).
    """
    if masks is None:
        masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0)
    cls = _kelas() if AKTIF else pygame.Surface
    surf = cls((int(width), int(height)), 0, 32, masks)
    surf.fill((0, 0, 0))
    return surf


def bungkus_seperti(contoh):
    """
    Buat FastSurface berukuran & berformat sama dengan `contoh`.
    Dipakai untuk buffer perantara (mis. surface shake layar).
    """
    w, h = contoh.get_size()
    cls = _kelas() if AKTIF else pygame.Surface
    return cls((w, h), 0, 32, contoh.get_masks())


def aktifkan(alasan=""):
    global AKTIF
    if not tersedia():
        print("[FASTBLIT] BLEND_ALPHA_SDL2 tidak ada di pygame ini - "
              "jalur cepat tidak bisa dipakai")
        return False
    AKTIF = True
    print("[FASTBLIT] AKTIF - alpha blit dialihkan ke blitter SDL. %s"
          % alasan)
    return True


def matikan():
    global AKTIF
    AKTIF = False
