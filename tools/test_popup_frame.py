"""
tools/test_popup_frame.py

Memastikan SEMUA popup (tower, castle/nexus, hero shop, item forge)
beserta TOMBOLNYA berada di dalam frame layar - tidak ada rect yang
"muncul di luar frame" sehingga tidak bisa ditekan.

Latar belakang
──────────────
Dua kelompok bug menyebabkan popup/tombol keluar dari frame:

  1. Di layar TANPA panel kanan (rasio <= ~16:9.5: tablet, desktop,
     HP 16:9), popup tower/castle/build yang tidak muat di atas target
     digeser ke BAWAH target tanpa pengecekan tepi bawah layar. Tower di
     lane tengah (y ± 300-450) mendorong bawah popup menembus tepi
     bawah layar - tombol upgrade/sell jadi tak terlihat & tak bisa
     ditekan.
  2. Tombol X (close) hero shop & item forge digambar MENEMPEL di sudut
     atas panel (panel_y - 15 / py - 14). Karena panel hampir menempel
     ke tepi atas layar, X ikut keluar dari frame.

Yang diperiksa
──────────────
  - untuk tiap popup: semua rect di game.ui_buttons berada di dalam
    surface penuh (0..w, 0..h)
  - klik di pusat tiap tombol memberi reaksi perubahan state
    (tombol noop wajar dikecualikan, lihat NOOP_SENGAJA)
  - dijalankan untuk layar 21:9 (ada panel), 20:9 (panel sempit),
    dan 16:9 / sempit (tanpa panel)

Jalankan:  python3 tools/test_popup_frame.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LAYAR = [
    ("21:9 (panel kanan)", 2436, 1080),
    ("20:9 (panel sempit)", 2340, 1080),
    ("16:9 (tanpa panel)", 1920, 1080),
    ("15.5:9 sempit (tanpa panel)", 1720, 1080),
]

# Satu process per layar: driver SDL "dummy" tidak bisa membuat dua
# renderer dalam satu process (kesalahan "failed to create renderer").
WORKER = r'''
import os, sys
sys.path.insert(0, __ROOT__)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "1")
os.environ.setdefault("MYSTIC_BENCH", "0")
os.environ.setdefault("MYSTIC_BOOTCHECK", "0")
os.environ.setdefault("MYSTIC_DISPLAY_MODE", "scaled")

import pygame
pygame.init()
W, H = __W__, __H__

from mobile import platform_utils as plat
from mobile import perf

class _Info:
    current_w, current_h = W, H

asli = pygame.display.Info
pygame.display.Info = lambda: _Info()
try:
    perf.install_all(is_android=False)
    screen = plat.create_display(vsync=False, mode="scaled")
finally:
    pygame.display.Info = asli

from _core import Game, BLUE_BASE_X, BLUE_BASE_Y
from _entity import Hero, Tower

g = Game(screen, level_number=1)
import __main__
__main__.game_instance = g
for nm in ("level_intro", "boss_intro"):
    o = getattr(g, nm, None)
    if o is not None and hasattr(o, "handle_skip"):
        try:
            o.handle_skip(key=pygame.K_SPACE)
        except Exception:
            pass
g.gold = 99999
g.heroes.append(Hero("grimjaw", "blue", 300, 380))
for _ in range(10):
    g.update()

# Tower di lane tengah (y=360) = kasus terburuk untuk posisi popup
# di layar tanpa panel.
g.towers = [Tower(400, 360, "blue", "outer", "mid")]

full = plat.get_full_surface()
FW, FH = full.get_size()

def state_key(g):
    # id(...) dipakai supaya pergantian target pembelian item forge
    # (chip BUY FOR) juga ikut terukur.
    return (g.gold, g.popup_target is not None, g.build_popup_slot,
            g.shop_open, g.item_shop_open, g.selected_hero is not None,
            id(getattr(g, "itemshop_target_hero", None)),
            getattr(g, "itemshop_inspect_item", None),
            getattr(g.blue_base, "level", None),
            getattr(g.blue_base, "shield", None),
            getattr(g, "itemshop_page", None))

def reset_ui(g):
    g.close_popup()
    g.close_build_popup()
    g.shop_open = False
    g.item_shop_open = False
    g.selected_hero = None
    # popup detail item bersifat modal (klik di bawahnya ditahan) -
    # harus ditutup dulu supaya tombol kartu lain bisa diuji.
    g.itemshop_inspect_item = None

def buka(g, jenis):
    reset_ui(g)
    if jenis == "tower":
        t = g.towers[0]
        g.handle_click((int(t.x), int(t.y)), 1)
        return g.popup_target is not None
    if jenis == "castle":
        g.handle_click((int(BLUE_BASE_X), int(BLUE_BASE_Y)), 1)
        return g.popup_target is not None
    if jenis == "heroshop":
        hx, hy = g.map_renderer.dire_shop_pos
        g.handle_click((int(hx), int(hy)), 1)
        return g.shop_open
    if jenis == "forge":
        rx, ry = g.map_renderer.radiant_shop_pos
        g.handle_click((int(rx), int(ry)), 1)
        return g.item_shop_open
    return False

# Tombol yang memang tidak mengubah state saat ditekan (sudah aktif /
# slot kosong sengaja diabaikan) - bukan kegagalan.
NOOP_SENGAJA = {
    "shop_tab_starter", "shop_tab_boss", "itemshop_page_0",
    "popup_upgrade_path_archer",   # tower uji memang tipe archer
    "itemshop_hero_0",             # hero yang memang sudah jadi target
    # slot item kosong sengaja diabaikan (lihat handle_item_shop_click)
    "itemshop_slot_0", "itemshop_slot_1", "itemshop_slot_2",
    "itemshop_slot_3", "itemshop_slot_4", "itemshop_slot_5",
}

gagal = []
for jenis, prefix in (("tower", "popup_"), ("castle", "popup_"),
                      ("heroshop", "shop_"), ("forge", "itemshop_")):
    if not buka(g, jenis):
        gagal.append("%s: popup tidak terbuka" % jenis)
        continue
    g.draw()
    # 1) semua rect tombol harus di dalam surface penuh
    for k, r in sorted(g.ui_buttons.items()):
        if not k.startswith(prefix):
            continue
        if not (r.left >= 0 and r.top >= 0
                and r.right <= FW and r.bottom <= FH):
            gagal.append("%s: tombol '%s' %s di luar frame %dx%d"
                         % (jenis, k, r, FW, FH))
    # 2) klik pusat tombol harus bereaksi
    for nama_t in sorted(k for k in g.ui_buttons
                         if k.startswith(prefix)):
        buka(g, jenis)
        g.draw()
        r = g.ui_buttons.get(nama_t)
        if r is None:
            continue
        before = state_key(g)
        g.handle_click(r.center, 1)
        after = state_key(g)
        if before != after or nama_t in NOOP_SENGAJA:
            continue
        gagal.append("%s: tombol '%s' (pusat %s) tidak bereaksi"
                     % (jenis, nama_t, r.center))

if gagal:
    print("GAGAL (%dx%d, panel=%s):" % (W, H, plat.get_panel_rect()))
    for s in gagal:
        print("  -", s)
    sys.exit(1)
print("LULUS (%dx%d, panel=%s): semua popup & tombol di dalam frame."
      % (W, H, plat.get_panel_rect()))
sys.exit(0)
'''


def main():
    semua = []
    for judul, w, h in LAYAR:
        kode = (WORKER
                .replace("__ROOT__", repr(ROOT))
                .replace("__W__", str(w))
                .replace("__H__", str(h)))
        proc = subprocess.run(
            [sys.executable, "-c", kode],
            capture_output=True, text=True, cwd=ROOT)
        stdout_lines = (proc.stdout or "").strip().splitlines()
        baris = stdout_lines[-1] if stdout_lines else "(tanpa keluaran)"
        detail = [s for s in stdout_lines if s.startswith("  -")]
        if proc.returncode != 0:
            stderr_lines = (proc.stderr or "").strip().splitlines()
            if stderr_lines:
                detail.append("stderr: %s" % stderr_lines[-1])
        status = "OK  " if proc.returncode == 0 else "FAIL"
        print("%s %s: %s" % (status, judul, baris))
        for d in detail:
            print("    %s" % d)
        if proc.returncode != 0:
            semua.append("%s (%d masalah)" % (judul, max(1, len(detail))))
    print()
    if semua:
        print("HASIL: GAGAL")
        for s in semua:
            print("  -", s)
        return 1
    print("HASIL: LULUS. Semua popup (tower, castle, hero shop, item "
          "forge) beserta tombolnya berada di dalam frame di semua "
          "tata letak.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
