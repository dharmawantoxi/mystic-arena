# ================================
# mobile/blitwatch.py
# Pelacak alpha-blit besar YANG BERJALAN DI HP
#
# Alpha blit di ARM ~222 ns/piksel (lihat diagnostics). Modul ini
# memasang Surface turunan sebagai buffer render, mencatat blit
# ber-alpha yang besar beserta lokasi kodenya, lalu overlay debug
# menampilkan 3 tersangka teratas langsung di layar.
#
# Hanya aktif di mode tampilan "native" (di situ buffer render
# dibuat oleh kita sendiri sehingga bisa disubkelaskan) dan hanya
# ketika perangkat terdeteksi lambat untuk alpha blit.
# ================================

import collections
import os
import traceback

import pygame

STATS = collections.Counter()      # lokasi -> piksel per frame (akumulatif)
FRAMES = [0]
MIN_PX = 8000                      # abaikan blit kecil
SAMPLE = 1                         # 1 = catat semua


class WatchedSurface(pygame.Surface):
    """Surface asli + pencatat blit ber-alpha berukuran besar."""

    def blit(self, source, dest=(0, 0), area=None, special_flags=0):
        try:
            if area is not None:
                w, h = area[2], area[3]
            else:
                w, h = source.get_size()
            if w * h >= MIN_PX:
                if (source.get_flags() & pygame.SRCALPHA) or \
                        source.get_alpha() is not None:
                    fr = traceback.extract_stack(limit=2)[0]
                    STATS["%s:%d %s" % (os.path.basename(fr.filename),
                                        fr.lineno, fr.name)] += w * h
        except Exception:
            pass
        return super().blit(source, dest, area, special_flags)


def new_frame():
    FRAMES[0] += 1


def top(n=3):
    """[(lokasi, piksel/frame, perkiraan ms di HP), ...]"""
    f = max(1, FRAMES[0])
    out = []
    for key, px in STATS.most_common(n):
        per = px / f
        out.append((key, per, per * 222e-9 * 1000))
    return out


def total_ms():
    f = max(1, FRAMES[0])
    return sum(STATS.values()) / f * 222e-9 * 1000


def reset():
    STATS.clear()
    FRAMES[0] = 0


def enabled():
    env = os.environ.get("MYSTIC_BLITWATCH")
    if env == "1":
        return True
    if env == "0":
        return False
    try:
        from mobile.perf import Quality
        return not Quality.cheap_alpha     # otomatis di HP lambat
    except Exception:
        return False
