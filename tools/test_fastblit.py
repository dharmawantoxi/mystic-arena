"""
tools/test_fastblit.py

Membuktikan bahwa jalur cepat alpha (BLEND_ALPHA_SDL2) TIDAK mengubah
tampilan game.

Kenapa perlu diuji seketat ini
──────────────────────────────
Jalur cepat memakai blitter SDL, bukan blitter alpha milik pygame.
Rumus blend-nya sedikit berbeda dalam pembulatan. Kalau selisihnya
besar, gaya grafik akan berubah - dan itu tidak boleh terjadi.

Yang diuji
──────────
  1. Sprite acak penuh (semua nilai alpha 0-255) ke tujuan TANPA
     kanal alpha - inilah kondisi nyata di game: buffer render dan
     layar sama-sama XRGB8888.
  2. Sprite dengan alpha tepi lembut (anti-alias), kondisi paling
     rawan terlihat.
  3. Sprite opaque - harus lewat jalur biasa, tidak disentuh.
  4. FastSurface benar-benar mengembalikan hasil yang sama dengan
     blit manual ber-flag.

Jalankan:  python3 tools/test_fastblit.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((320, 240))

from mobile import fastblit                              # noqa: E402

MASKS_OPAQUE = (0x00FF0000, 0x0000FF00, 0x000000FF, 0)
MASKS_ALPHA = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
UKURAN = 96


def sprite_acak(rng):
    s = pygame.Surface((UKURAN, UKURAN), pygame.SRCALPHA, 32, MASKS_ALPHA)
    for x in range(UKURAN):
        for y in range(UKURAN):
            s.set_at((x, y), (rng.randrange(256), rng.randrange(256),
                              rng.randrange(256), rng.randrange(256)))
    return s


def sprite_tepi_lembut(rng):
    """Lingkaran dengan tepi anti-alias - kasus paling rawan terlihat."""
    s = pygame.Surface((UKURAN, UKURAN), pygame.SRCALPHA, 32, MASKS_ALPHA)
    cx = cy = UKURAN / 2.0
    r = UKURAN * 0.42
    warna = (rng.randrange(256), rng.randrange(256), rng.randrange(256))
    for x in range(UKURAN):
        for y in range(UKURAN):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d > r + 1.5:
                a = 0
            elif d < r - 1.5:
                a = 255
            else:
                a = int(255 * (r + 1.5 - d) / 3.0)
            s.set_at((x, y), warna + (a,))
    return s


def sprite_opaque(rng):
    s = pygame.Surface((UKURAN, UKURAN), 0, 32, MASKS_OPAQUE)
    s.fill((rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    return s


def banding(nama, pembuat, ulang=8, pakai_kelas=False):
    rng = random.Random(12345)
    beda_maks = 0
    beda_total = 0
    piksel = 0

    for _ in range(ulang):
        src = pembuat(rng)
        dasar = pygame.Surface((UKURAN, UKURAN), 0, 32, MASKS_OPAQUE)
        dasar.fill((rng.randrange(256), rng.randrange(256),
                    rng.randrange(256)))

        acuan = dasar.copy()
        acuan.blit(src, (0, 0))                       # jalur pygame biasa

        if pakai_kelas:
            uji = fastblit.FastSurface((UKURAN, UKURAN), 0, 32, MASKS_OPAQUE)
            uji.blit(dasar, (0, 0))
            uji.blit(src, (0, 0))                     # lewat FastSurface
        else:
            uji = dasar.copy()
            uji.blit(src, (0, 0), None, pygame.BLEND_ALPHA_SDL2)

        for x in range(0, UKURAN, 2):
            for y in range(0, UKURAN, 2):
                a = acuan.get_at((x, y))
                b = uji.get_at((x, y))
                d = max(abs(a[i] - b[i]) for i in range(3))
                beda_maks = max(beda_maks, d)
                beda_total += d
                piksel += 1

    rata = beda_total / max(1, piksel)
    print("  %-34s beda maks %3d/255   rata-rata %.3f"
          % (nama, beda_maks, rata))
    return beda_maks


def main():
    if not fastblit.tersedia():
        print("BLEND_ALPHA_SDL2 tidak ada di pygame ini.")
        return 1

    print("Selisih warna antara blit pygame biasa dan jalur cepat SDL.")
    print("Ambang lulus: maks 4/255 (1,6%) - di bawah ambang terlihat mata.\n")

    hasil = []
    hasil.append(banding("sprite acak (alpha 0-255)", sprite_acak))
    hasil.append(banding("tepi lembut (anti-alias)", sprite_tepi_lembut))
    hasil.append(banding("lewat FastSurface", sprite_acak,
                         pakai_kelas=True))

    print()
    # sprite opaque harus TIDAK disentuh -> identik sempurna
    beda_opaque = banding("sprite opaque (harus 0)", sprite_opaque,
                          pakai_kelas=True)

    print()
    gagal = [d for d in hasil if d > 4] + ([1] if beda_opaque != 0 else [])
    if gagal:
        print("HASIL: GAGAL - selisih melewati ambang.")
        return 1
    print("HASIL: LULUS. Jalur cepat tidak mengubah tampilan "
          "(maks %d/255 = %.1f%%)." % (max(hasil), max(hasil) / 255 * 100))
    return 0


if __name__ == "__main__":
    sys.exit(main())
