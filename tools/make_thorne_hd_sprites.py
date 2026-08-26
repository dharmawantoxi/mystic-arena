"""One-off: proses render HD Thorne (latar hitam) jadi sprite RGBA transparan.

Baca  assets/heroes/_raw/thorne_<pose>_raw.png
Tulis assets/heroes/thorne_<pose>.png   (RGBA, trimmed, transparan)

Teknik: flood-fill dari tepi membuang piksel gelap yang terhubung ke
border (latar hitam), piksel terang di dalam karakter tetap solid.
Tepi mask di-feather 1px supaya tidak ada garis keras, lalu gambar
di-crop ke bounding box alpha.
"""
import os
from collections import deque

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "assets", "heroes", "_raw")
OUT = os.path.join(ROOT, "assets", "heroes")

DARK_T = 48          # piksel dgn max channel < ini dianggap "gelap"
POSES = ("idle", "walk", "attack")


def remove_background(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    is_dark = lambda r, g, b: max(r, g, b) < DARK_T

    bg = bytearray(w * h)  # 1 = background
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            r, g, b, a = px[x, y]
            if is_dark(r, g, b):
                bg[y * w + x] = 1
                dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            r, g, b, a = px[x, y]
            if is_dark(r, g, b):
                bg[y * w + x] = 1
                dq.append((x, y))

    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                i = ny * w + nx
                if not bg[i]:
                    r, g, b, a = px[nx, ny]
                    if is_dark(r, g, b):
                        bg[i] = 1
                        dq.append((nx, ny))

    # Alpha baru: background -> 0, sisanya 255
    alpha = bytearray(w * h)
    for i in range(w * h):
        alpha[i] = 0 if bg[i] else 255

    # Feather 1px: piksel background yang menempel foreground dapat
    # alpha lembut sesuai terangnya (sisa glow tidak jadi garis keras)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            if bg[i]:
                if (not bg[i - 1]) or (not bg[i + 1]) or \
                   (not bg[i - w]) or (not bg[i + w]):
                    r, g, b, a = px[x, y]
                    alpha[i] = min(255, max(r, g, b) * 3)

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, alpha[y * w + x])

    return im


def main():
    for pose in POSES:
        src = os.path.join(RAW, "thorne_%s_raw.png" % pose)
        dst = os.path.join(OUT, "thorne_%s.png" % pose)
        im = remove_background(Image.open(src))
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
        im.save(dst)
        print("%-10s -> %s  %s" % (pose, dst, im.size))


if __name__ == "__main__":
    main()
