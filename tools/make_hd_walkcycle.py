#!/usr/bin/env python3
"""Bake walk cycle 6-frame untuk hero HD (kaizen / thorne / zephyr).

Gaya Kingdom Wars: unit berjalan dengan siklus kaki nyata (contact ->
passing -> contact -> passing -> stride -> recoil), bukan 2 pose yang
di-cross-fade.

Sumber
──────
assets/heroes/_raw/<hero>_walkcycle_raw.png   strip AI 2x3 (latar putih)

Keluaran (RGBA transparan, trim + de-fringe)
───────
assets/heroes/<hero>_walk_0..5.png            6 frame siklus jalan
docs/<hero>_walkcycle_preview.png             contact sheet untuk inspeksi

Alur
────
1. Latar putih dibuang dengan flood-fill dari tepi (bagian terang di
   DALAM karakter tetap aman).
2. Slice grid: connected-component besar dikelompokkan per baris; komponen
   yang menyatu dipecah di "lembah" profil kolom foreground.
3. Trim tiap frame, buang fringe putih (un-mix), simpan.
4. Validasi: 6 frame, tinggi konsisten, frame saling berbeda, orientasi
   menghadap kanan (dicheck silang dgn walk_0 lama).

Run:  python3 tools/make_hd_walkcycle.py [--hero kaizen|thorne|zephyr|all]
"""
from __future__ import print_function

import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEROES = os.path.join(ROOT, "assets", "heroes")
DOCS = os.path.join(ROOT, "docs")
RAW = os.path.join(HEROES, "_raw")

FRAMES = 6
MIN_COMP_PX = 3000          # komponen lebih kecil dianggap noise
HEIGHT_TOL = 0.30           # toleransi beda tinggi antar frame
# Ambang "latar putih": terang + rendah saturasi.
BG_LUMA = 232
BG_SAT = 26


# ---------------------------------------------------------------------
# Background removal (flood-fill dari tepi -> hanya latar terang nyambung)
# ---------------------------------------------------------------------
def _is_bg_rgb(arr):
    lum = arr.mean(axis=2)
    sat = arr.max(axis=2) - arr.min(axis=2)
    return (lum > BG_LUMA) & (sat < BG_SAT)


def remove_white_bg(im):
    """Kembalikan array RGBA dengan latar putih tepi jadi alpha 0."""
    rgb = np.asarray(im.convert("RGB")).astype(np.uint8)
    h, w = rgb.shape[:2]
    bg_test = _is_bg_rgb(rgb.astype(int))

    # Seed: semua piksel latar yang menyentuh tepi gambar.
    seeds = np.zeros((h, w), bool)
    seeds[0, :] = bg_test[0, :]
    seeds[-1, :] = bg_test[-1, :]
    seeds[:, 0] = bg_test[:, 0]
    seeds[:, -1] = bg_test[:, -1]
    bg = ndimage.binary_propagation(seeds, mask=bg_test)

    fg = ~bg
    # Tutup lubang kecil & buang noise sekecil titik.
    fg = ndimage.binary_closing(fg, structure=np.ones((5, 5)))
    fg = ndimage.binary_opening(fg, structure=np.ones((3, 3)))

    alpha = (fg * 255).astype(np.uint8)
    # Erode 1px + un-mix warna supaya halo putih tepi tidak ikut ke
    # frame final (terlihat jelas setelah smoothscale ke 110 px).
    alpha = ndimage.grey_erosion(alpha, size=(3, 3))
    soft = ndimage.grey_dilation(alpha, size=(3, 3))
    edge = ndimage.grey_dilation(alpha, size=(5, 5)) > 0
    alpha = np.where(edge & (alpha == 0), (soft // 2).astype(np.uint8), alpha)

    out = np.dstack([rgb, alpha])
    return _defringe(out)


def _defringe(rgba):
    """Un-mix putih di piksel semi transparan: c = (c - (1-a)*255) / a."""
    a = rgba[..., 3].astype(np.float32) / 255.0
    rgb = rgba[..., :3].astype(np.float32)
    semi = (a > 0.02) & (a < 0.98)
    af = a[..., None]
    fixed = (rgb - (1.0 - af) * 255.0) / np.maximum(af, 1e-4)
    rgb = np.where(semi[..., None], np.clip(fixed, 0, 255), rgb)
    rgba = rgba.copy()
    rgba[..., :3] = rgb.astype(np.uint8)
    return rgba


# ---------------------------------------------------------------------
# Slicing grid 2x3
# ---------------------------------------------------------------------
def _big_components(fg_mask):
    lab, n = ndimage.label(fg_mask)
    if n == 0:
        return []
    sizes = ndimage.sum(fg_mask, lab, range(1, n + 1))
    boxes = ndimage.find_objects(lab)
    out = []
    for i in range(n):
        if sizes[i] >= MIN_COMP_PX:
            sl = boxes[i]
            out.append((sl[1].start, sl[1].stop, sl[0].start, sl[0].stop))
    return out


def _valley_split(fg_mask, x0, x1, y0, y1, parts):
    """Pecah span [x0,x1) jadi `parts` potong di lembah foreground."""
    prof = fg_mask[y0:y1, x0:x1].mean(axis=0)
    w = len(prof)
    bounds = []
    for k in range(1, parts):
        lo = int(w * k / parts - w * 0.12)
        hi = int(w * k / parts + w * 0.12)
        lo = max(lo, 1); hi = min(hi, w - 1)
        seg = prof[lo:hi]
        if len(seg) == 0:
            bounds.append(x0 + int(w * k / parts))
            continue
        bounds.append(x0 + lo + int(np.argmin(seg)))
    cuts = [x0] + bounds + [x1]
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]


def slice_cells(rgba):
    """Kembalikan list 6 (x0, x1, y0, y1) urut frame 0..5."""
    h, w = rgba.shape[:2]
    fg = rgba[..., 3] > 40
    comps = _big_components(fg)
    if not comps:
        raise RuntimeError("tidak ada komponen karakter ditemukan")

    # Kelompokkan 2 baris berdasarkan pusat-y (grid 2x3).
    cy = [(b[2] + b[3]) / 2.0 for b in comps]
    cy_all = np.array(sorted(cy))
    # split terbesar antar pusat-y berurutan
    order = np.argsort(cy_all)
    gaps = np.diff(cy_all)
    if len(gaps) and gaps.max() > 40:
        split = (cy_all[order][np.argmax(gaps)] + cy_all[order][np.argmax(gaps) + 1]) / 2.0
    else:
        split = h / 2.0

    rows = [[b for b, c in zip(comps, cy) if c < split],
            [b for b, c in zip(comps, cy) if c >= split]]

    cells = []
    for ri, row in enumerate(rows):
        if not row:
            raise RuntimeError("baris %d kosong" % ri)
        row.sort(key=lambda b: b[0])
        x_lo = min(b[0] for b in row)
        x_hi = max(b[1] for b in row)
        y_lo = min(b[2] for b in row)
        y_hi = max(b[3] for b in row)
        if len(row) == 3:
            spans = [(b[0], b[1]) for b in row]
        else:
            # Ada komponen menyatu -> pecah di lembah profil kolom.
            spans = _valley_split(fg, x_lo, x_hi, y_lo, y_hi, 3)
        if len(spans) != 3:
            raise RuntimeError("baris %d menghasilkan %d span" % (ri, len(spans)))
        for sx0, sx1 in spans:
            cells.append((sx0, sx1, y_lo, y_hi))
    if len(cells) != FRAMES:
        raise RuntimeError("hasil slice %d sel (harus %d)" % (len(cells), FRAMES))
    return cells


def trim_alpha(rgba, pad=2):
    ys, xs = np.where(rgba[..., 3] > 12)
    if len(xs) == 0:
        return rgba
    x0, x1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + 1 + pad)
    y0, y1 = max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + 1 + pad)
    return rgba[y0:y1, x0:x1]


# ---------------------------------------------------------------------
# Validasi
# ---------------------------------------------------------------------
def mask_iou(a, b):
    """IoU dua alpha-mask (array bool) setelah disamakan ukurannya."""
    ha = a.shape[0]; hb = b.shape[0]
    H = 128
    ia = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize(
        (max(8, int(a.shape[1] * H / ha)), H), Image.BILINEAR)) > 110
    ib = np.asarray(Image.fromarray((b * 255).astype(np.uint8)).resize(
        (max(8, int(b.shape[1] * H / hb)), H), Image.BILINEAR)) > 110
    # samakan lebar
    W = max(ia.shape[1], ib.shape[1])
    def wpad(m):
        if m.shape[1] < W:
            off = np.zeros((H, W), bool); off[:, :m.shape[1]] = m
            return off
        return m[:, :W]
    ia, ib = wpad(ia), wpad(ib)
    inter = (ia & ib).sum()
    union = (ia | ib).sum()
    return inter / max(1, union)


def process_hero(hero, save=True):
    raw_path = os.path.join(RAW, "%s_walkcycle_raw.png" % hero)
    if not os.path.exists(raw_path):
        raise RuntimeError("raw strip tidak ada: %s" % raw_path)
    im = Image.open(raw_path)
    rgba = remove_white_bg(im)
    cells = slice_cells(rgba)

    frames = []
    for (x0, x1, y0, y1) in cells:
        cell = rgba[y0:y1, x0:x1]
        cell = trim_alpha(cell)
        frames.append(cell)

    report = {"hero": hero, "frames": []}

    # --- validasi tinggi konsisten ---
    heights = [f.shape[0] for f in frames]
    hmed = float(np.median(heights))
    bad = [i for i, hh in enumerate(heights)
           if abs(hh - hmed) / hmed > HEIGHT_TOL]
    if bad:
        raise RuntimeError("tinggi frame %s menyimpang dari median %.0f"
                           % (bad, hmed))

    # --- orientasi: korelasi silang dgn walk_0 LAMA (ground truth) ---
    # Referensi asli dipakai kalau ada (file lama bisa sudah tertimpa
    # hasil bake sebelumnya). Flip hanya kalau buktinya kuat: margin
    # besar DAN IoU absolut di atas baseline pose-beda (~0.45).
    old_path = os.path.join(RAW, "%s_walk_0_orig.png" % hero)
    if not os.path.exists(old_path):
        old_path = os.path.join(HEROES, "%s_walk_0.png" % hero)
    flipped = False
    if os.path.exists(old_path):
        old = np.asarray(Image.open(old_path).convert("RGBA"))
        old_m = old[..., 3] > 110
        iou_norm = max(mask_iou(f[..., 3] > 110, old_m) for f in frames)
        iou_flip = max(mask_iou(f[:, ::-1][..., 3] > 110, old_m)
                       for f in frames)
        flipped = (iou_flip > iou_norm + 0.06) and (iou_flip > 0.45)
        report["iou_norm"] = round(float(iou_norm), 3)
        report["iou_flip"] = round(float(iou_flip), 3)
        report["flipped"] = flipped
        if max(iou_norm, iou_flip) < 0.40:
            print("  ! PERINGATAN: kemiripan dgn aset lama rendah "
                  "(%.3f) - kemungkinan off-model" % max(iou_norm, iou_flip))
    if flipped:
        frames = [f[:, ::-1] for f in frames]

    # --- frame harus benar2 berbeda (bukan 6x pose sama) ---
    base = frames[0]
    for i in range(1, FRAMES):
        iou = mask_iou(frames[i][..., 3] > 110, base[..., 3] > 110)
        if iou > 0.985:
            raise RuntimeError("frame %d identik dgn frame 0 (IoU %.3f)"
                               % (i, iou))

    # --- simpan ---
    outs = []
    for i, f in enumerate(frames):
        dst = os.path.join(HEROES, "%s_walk_%d.png" % (hero, i))
        if save:
            Image.fromarray(f, "RGBA").save(dst, optimize=True)
        outs.append(dst)
        report["frames"].append(
            {"file": os.path.basename(dst), "w": f.shape[1], "h": f.shape[0],
             "opaque_pct": round(float((f[..., 3] > 200).mean() * 100), 1)})

    # --- contact sheet untuk inspeksi manual ---
    if save:
        try:
            H = 200
            tiles = []
            for f in frames:
                imf = Image.fromarray(f, "RGBA")
                s = H / imf.size[1]
                tiles.append(imf.resize((max(1, int(imf.size[0] * s)), H),
                                        Image.LANCZOS))
            Wt = sum(t.size[0] for t in tiles) + 10 * (FRAMES + 1)
            sheet = Image.new("RGBA", (Wt, H + 20), (24, 26, 34, 255))
            x = 10
            for t in tiles:
                sheet.paste(t, (x, 10), t)
                x += t.size[0] + 10
            sheet.save(os.path.join(DOCS, "%s_walkcycle_preview.png" % hero))
        except Exception as e:
            print("  ! contact sheet gagal: %s" % e)

    return report


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    heroes = args or ["kaizen", "thorne", "zephyr"]
    ok = True
    for hero in heroes:
        try:
            rep = process_hero(hero)
            print("[%s] OK" % hero)
            for k in ("iou_norm", "iou_flip", "flipped"):
                if k in rep:
                    print("   %s = %s" % (k, rep[k]))
            for fr in rep["frames"]:
                print("   %(file)-24s %(w)4dx%(h)4d opaque=%(opaque_pct)5.1f%%"
                      % fr)
        except Exception as e:
            ok = False
            print("[%s] GAGAL: %s" % (hero, e))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
