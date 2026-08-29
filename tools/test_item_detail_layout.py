"""Cek layout popup detail: semua info SEMUA item harus muat tanpa
dipotong (tidak boleh ada ellipsis '…' dari pemotongan kolom)."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
import _core  # noqa: E402 (font nyata)
from hero_items import (ItemShopUI, ITEM_CATALOG,  # noqa: E402
                        _build_item_mechanics)
from _core import get_font  # noqa: E402

W = ItemShopUI.DETAIL_W
H = ItemShopUI.DETAIL_H
pad = 22
text_w = W - pad * 2
line_h = 21

desc_f = get_font(19, "body_medium")
mf = get_font(17, "body_medium")
flav_f = get_font(16, "body_medium")

problems = []
for sid, data in ITEM_CATALOG.items():
    y = 112            # mulai konten
    limit = H - 44     # sisa untuk petunjuk bawah

    # 1) deskripsi + label
    y += 22
    desc_lines = ItemShopUI._wrap_text(
        ItemShopUI._localized_desc(data), desc_f, text_w)
    desc_needed = 112 + 22 + len(desc_lines) * 23
    if desc_needed > limit:
        problems.append(f"{sid}: DESKRIPSI kepotong")
    y = min(desc_needed, limit)

    # 2) kolom mekanik (sama persis dengan _draw_detail_popup)
    mech = _build_item_mechanics(data)
    if mech and y < limit - 40:
        y += 22
        col_w = (text_w - 26) // 2
        heights = [0, 0]
        avail = limit - y
        clipped = False
        for kind, text in mech:
            lines = ([text] if kind == "header"
                     else ItemShopUI._wrap_text(text, mf, col_w))
            h = len(lines) * line_h
            ci = 0 if heights[0] <= heights[1] else 1
            if heights[ci] + h > avail:
                other = 1 - ci
                if heights[other] + h <= avail:
                    ci = other
                else:
                    clipped = True
                    break
            heights[ci] += h
        if clipped:
            problems.append(f"{sid}: STAT & EFEK kepotong (… dibutuhkan)")
        y += max(heights)

    # 3) riwayat
    flavor = data.get("flavor")
    if flavor and y < limit - 30:
        y += 22
        flav_lines = ItemShopUI._wrap_text(flavor, flav_f, text_w)
        if y + len(flav_lines) * 21 > limit:
            problems.append(f"{sid}: RIWAYAT kepotong")

if problems:
    print("PROBLEM LAYOUT:")
    for p in problems:
        print("  -", p)
    sys.exit(1)

print(f"LAYOUT OK - info lengkap SEMUA {len(ITEM_CATALOG)} item muat "
      f"tanpa potongan (popup {W}x{H})")
