"""Post-process gambar kastil AI (latar hitam) -> sprite RGBA transparan.

Dipakai offline (bukan di runtime game). Alur per file:
1. Kalau PNG sudah punya kanal alpha (latar benar-benar transparan)
   -> hanya auto-crop.
2. Kalau RGB latar hitam -> flood-fill dari tepi gambar: piksel
   "hampir hitam" yang terhubung dengan luar dibuat transparan.
   Area gelap DI DALAM kastil (mis. celah gerbang yang memang harus
   gelap) aman karena tidak terhubung ke tepi latar.
3. Auto-crop ke bounding box objek + margin kecil, resize ke lebar
   target (2-3x ukuran tampil di game supaya tajam), dan sedikit
   feather alpha di tepi.

Hasil: PNG RGBA di folder yang sama (in-place).
"""
import os
import sys
from collections import deque

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASTLE_DIR = os.path.join(HERE, "assets", "castles")

BLACK_THRESHOLD = 26     # max(r,g,b) <= nilai ini dianggap "latar"
MARGIN = 6               # piksel margin di sekitar bbox setelah crop
TARGET_WIDTH = 768       # lebar hasil (dihitung rasio dari gambar asli)


def flood_black_to_alpha(img: Image.Image) -> Image.Image:
    """Buat alpha: piksel hampir-hitam yang terhubung ke tepi -> 0."""
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()

    def is_bg(x, y):
        r, g, b = px[x, y]
        return max(r, g, b) <= BLACK_THRESHOLD

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))

    alpha = Image.new("L", (w, h), 255)
    apx = alpha.load()
    count = 0
    while q:
        x, y = q.popleft()
        apx[x, y] = 0
        count += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                if is_bg(nx, ny):
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))
    if count == 0:
        raise RuntimeError("tidak ada piksel latar hitam terhubung ke tepi")
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def process(path: str) -> str:
    im = Image.open(path)
    has_alpha = "A" in im.getbands()
    transparent_bg = False
    if has_alpha:
        a = im.getchannel("A")
        w0, h0 = im.size
        corners = [a.getpixel(p) for p in
                   ((0, 0), (w0 - 1, 0), (0, h0 - 1), (w0 - 1, h0 - 1))]
        transparent_bg = all(c < 16 for c in corners)

    if has_alpha and transparent_bg:
        rgb = im.convert("RGBA")
        print(f"  {os.path.basename(path)}: sudah transparan, auto-crop saja")
    elif has_alpha:
        rgb = im.convert("RGBA")
        print(f"  {os.path.basename(path)}: alpha tapi latar terisi, "
              "tetap diproses sebagai RGB")
        rgb = flood_black_to_alpha(rgb.convert("RGB"))
    else:
        rgb = flood_black_to_alpha(im)
        print(f"  {os.path.basename(path)}: RGB latar hitam -> flood fill")

    # ── auto-crop ──
    bbox = rgb.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("objek tidak ditemukan (bbox kosong)")
    l, t, r, b = bbox
    l = max(0, l - MARGIN)
    t = max(0, t - MARGIN)
    r = min(rgb.width, r + MARGIN)
    b = min(rgb.height, b + MARGIN)
    rgb = rgb.crop((l, t, r, b))

    # ── resize ke lebar target (jangan diperbesar) ──
    if rgb.width > TARGET_WIDTH:
        scale = TARGET_WIDTH / rgb.width
        rgb = rgb.resize((TARGET_WIDTH, max(1, int(rgb.height * scale))),
                         Image.LANCZOS)

    # ── feather tepi alpha (haluskan potongan) ──
    rgb = rgb.convert("RGBA")
    alpha = rgb.getchannel("A").filter(ImageFilter.GaussianBlur(0.7))
    rgb.putalpha(alpha)

    rgb.save(path)
    print(f"  -> disimpan {os.path.basename(path)} {rgb.size} RGBA")
    return path


def main():
    files = [os.path.join(CASTLE_DIR, f) for f in sorted(os.listdir(CASTLE_DIR))
             if f.lower().endswith(".png") and not f.startswith("_")]
    if not files:
        print("tidak ada file kastil di", CASTLE_DIR)
        sys.exit(1)
    for f in files:
        process(f)
    print("selesai.")


if __name__ == "__main__":
    main()
