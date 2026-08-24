"""
tools/test_sidepanel.py

Uji regresi panel kanan (mobile/sidepanel.py) untuk dua bug yang
dilaporkan pemain:

1. ISI PANEL MUNCUL DI LUAR GAMEPLAY
   Panel kanan dulu menggambar STATUS/HEROES juga di splash screen
   (gold 0, "No heroes") karena draw() tidak peduli game-nya ada
   atau tidak. Sekarang: di luar gameplay (splash/menu) panel
   kembali ke latar batu polos dan semua tombol disembunyikan.

2. TOMBOL COMMAND "MENEMBUS" KLIK PANEL YANG MENIMPANYA
   Tombol tactical (GATHER, PROTECT TOWER, ...) dulu punya hit box
   MIN_TAP=80 px pada tombol setinggi 32 px - area sentuhnya menutupi
   tombol tetangga DAN wilayah popup (upgrade tower/build/panel hero)
   yang digambar di atasnya. Klik upgrade tower jadi "tembus" ke
   tombol command di baliknya. Sekarang:
     - hit box tactical diberi bantalan kecil (3 px) sehingga tidak
       saling menutupi;
     - saat popup game menutupi panel, hit_test() hanya mengizinkan
       tombol JEDA - sisanya dilewati supaya klik sampai ke popup;
     - tombol yang tidak digambar (belum sempat digambar, layar
       menang/kalah, ruang tidak cukup) tidak bisa ditekan.

Jalankan:  python3 tools/test_sidepanel.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "1")

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((1624, 720))

from mobile import platform_utils as plat                # noqa: E402
from mobile import sidepanel as P                        # noqa: E402

GAGAL = []


def cek(nama, kondisi):
    penanda = "OK  " if kondisi else "GAGAL"
    print("  [%s] %s" % (penanda, nama))
    if not kondisi:
        GAGAL.append(nama)


# ═══ PANGGUNG: layar 1624x720 dengan panel kanan 344 px ═══
PANEL = pygame.Rect(1280, 0, 344, 720)
FULL = pygame.Surface((1624, 720))
plat._display_state["panel"] = PANEL
plat._display_state["full"] = FULL
plat._gambar_panel_samping(FULL, PANEL)          # latar batu (sekali)


class FakeHero:
    def __init__(self, nama="Kai"):
        self.name = nama
        self.team = "blue"
        self.alive = True
        self.level = 3
        self.hp = 90
        self.max_hp = 120

    def is_skill_ready(self, k):
        return k == "q"


class FakeBoss:
    alive = True


class FakeGame:
    """Game semu dengan atribut yang dibaca panel & main.py."""

    def __init__(self):
        self.state = "playing"
        self.gold = 250
        self.wave_number = 3
        self.level_number = 1
        self.enemy_scaling_enabled = False
        self.blue_base = type("B", (), {"shield_active": False})()
        self.heroes = [FakeHero("Kai"), FakeHero("Zia")]
        self.active_boss = FakeBoss()          # biar 4 tombol tampil
        self.popup_target = None
        self.build_popup_slot = None
        self.selected_hero = None

    def get_all_heroes(self):
        return list(self.heroes)


def get_font(size, kind="body"):
    return pygame.font.Font(None, size)


def pusat(rect):
    return (rect.x + rect.width // 2, rect.y + rect.height // 2)


def area_panel():
    return FULL.subsurface(PANEL).copy()


def sama_pixel(a, b):
    """
    Bandingkan dua surface per-piksel (tepat, via byte string).
    Catatan: `surface == surface` di pygame TIDAK menjamin per-piksel
    (bisa False walau semua piksel sama), jadi bandingkan sendiri.
    """
    if a is None or b is None or a.get_size() != b.get_size():
        return False
    return (pygame.image.tostring(a, "RGBA")
            == pygame.image.tostring(b, "RGBA"))


def main():
    panel = P.SidePanel(get_font)
    P.daftarkan(panel)
    game = FakeGame()

    print("\n1. SPLASH (game=None): panel harus kosong")
    panel.draw(FULL, None, None, 16)
    cek("semua tombol disembunyikan",
        all(not b.visible for b in panel.buttons.values()))
    cek("hit_test splash -> None",
        panel.hit_test(pusat(panel.rect.inflate(-40, -100)), game=None) is None)
    latar = area_panel()
    cek("isi buffer dibuang", panel._isi_buf is None)
    cek("notifikasi di luar gameplay dibuang",
        (panel.beri_tahu("seharusnya hilang"),
         panel.notifikasi == [])[1])
    panel.catat_kill("Tower", "Goblin")
    cek("kill feed di luar gameplay dibuang", panel.kill_feed == [])

    print("\n2. GAMEPLAY: isi panel tampil & tombol bisa ditekan")
    panel.draw(FULL, game, None, 16)
    cek("gold/level/wave tergambar (panel tidak polos)",
        not sama_pixel(area_panel(), latar))
    for k in ("pause", "gather", "protect_tower", "protect_castle",
              "attack_boss"):
        cek("tombol %s visible" % k, panel.buttons[k].visible)

    # 4 tombol command terlihat -> posisi final dari draw, bukan
    # placeholder (placeholder-nya dibuat di asumsi 5 hero).
    g_rect = panel.buttons["gather"].rect
    cek("posisi tactical dari draw nyata (bukan placeholder 436)",
        g_rect.y < 430)

    print("\n3. TIDAK ADA TOMBOL YANG MENELAN KLIK TETANGGANYA")
    for k in ("gather", "protect_tower", "protect_castle", "attack_boss"):
        hasil = panel.hit_test(pusat(panel.buttons[k].rect), game=game)
        cek("tengah %s -> '%s'" % (k, k), hasil == k)

    print("\n4. POPUP TOWER TERBUKA: klik harus sampai ke popup,")
    print("   bukan tembus ke command di baliknya")
    game.popup_target = object()          # popup upgrade tower (300x360)
    panel.draw(FULL, game, None, 16)      # gambar ulang dgn popup terbuka
    for k in ("gather", "protect_tower", "protect_castle", "attack_boss"):
        hasil = panel.hit_test(pusat(panel.buttons[k].rect), game=game)
        cek("tengah %s saat popup terbuka -> None" % k, hasil is None)
    cek("tombol JEDA tetap hidup saat popup terbuka",
        panel.hit_test(pusat(panel.buttons["pause"].rect), game=game)
        == "pause")
    # Titik yang dulu (bug) ditelan command: tengah popup tower di
    # panel ada di jalur tombol command.
    hasil = panel.hit_test((1452, 420), game=game)
    cek("klik di area popup (1452,420) tidak jadi command",
        hasil is None)
    game.popup_target = None

    print("\n5. BUILD POPUP TERBUKA")
    game.build_popup_slot = {"x": 100, "y": 100}
    for k in ("gather", "protect_tower"):
        hasil = panel.hit_test(pusat(panel.buttons[k].rect), game=game)
        cek("tengah %s saat build popup -> None" % k, hasil is None)
    game.build_popup_slot = None

    print("\n6. PANEL HERO TERPILIH TERBUKA")
    game.selected_hero = FakeHero("Kai")
    for k in ("gather", "protect_castle"):
        hasil = panel.hit_test(pusat(panel.buttons[k].rect), game=game)
        cek("tengah %s saat panel hero -> None" % k, hasil is None)
    cek("tombol JEDA tetap hidup saat panel hero terbuka",
        panel.hit_test(pusat(panel.buttons["pause"].rect), game=game)
        == "pause")
    game.selected_hero = None

    print("\n7. LAYAR MENANG: command disembunyikan & tidak bisa ditekan")
    game.state = "victory"
    panel.draw(FULL, game, None, 16)
    cek("tactical hidden saat victory",
        all(not panel.buttons[k].visible
            for k in ("gather", "protect_tower", "protect_castle",
                      "attack_boss")))
    for k in ("gather", "protect_tower"):
        hasil = panel.hit_test(pusat(panel.buttons[k].rect), game=game)
        cek("tengah %s saat victory -> None" % k, hasil is None)
    cek("STATUS/HEROES masih tampil (masih dalam gameplay)",
        not sama_pixel(area_panel(), latar))
    game.state = "playing"

    print("\n8. KEMBALI KE SPLASH: panel bersih kembali ke batu polos")
    panel.draw(FULL, None, None, 16)
    cek("panel = latar batu (tanpa isi game)",
        sama_pixel(area_panel(), latar))
    cek("tombol JEDA juga hilang di splash",
        panel.hit_test(pusat(panel.buttons["pause"].rect), game=None) is None)

    print("\n9. KOMPATIBILITAS LAMA: hit_test tanpa argumen game")
    panel.draw(FULL, game, None, 16)       # mainkan lagi
    hasil = panel.hit_test(pusat(panel.buttons["gather"].rect))
    cek("hit_test(pos) lama tetap menjawab", hasil == "gather")

    print()
    if GAGAL:
        print("GAGAL: %d uji tidak lulus: %s" % (len(GAGAL), "; ".join(GAGAL)))
        return 1
    print("Semua uji panel kanan lulus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
