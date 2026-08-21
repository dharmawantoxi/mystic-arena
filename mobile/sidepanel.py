# ================================
# mobile/sidepanel.py
# PANEL KANAN — kontrol & informasi di luar arena
#
# Kenapa ada
# ──────────
# Layar 2436x1080 (rasio 2,26) menyisakan 344 px setelah arena
# 1280x720. Dulu ruang itu bar hitam, lalu diisi hiasan batu. Sekarang
# dipakai untuk hal yang benar-benar berguna:
#
#   - tombol jeda & FPS         (dulu menutupi sudut kiri atas peta)
#   - emas, wave, waktu         (dulu panel melayang di atas peta)
#   - daftar hero + HP + skill  (dulu harus ketuk hero satu per satu)
#   - notifikasi combo          (dulu melintas di tengah layar)
#   - popup upgrade hero        (dulu menutupi peta persis saat
#                                pemain perlu melihat peta)
#
# Aturan yang dipegang
# ────────────────────
# 1. Panel ini BONUS, bukan syarat. Di layar 16:9 panelnya tidak ada
#    dan semua tetap berjalan seperti semula.
# 2. Tidak boleh mahal. Latar batu disalin sekali; teks hanya
#    dibangun ulang 4x per detik (lihat JEDA_SEGAR_MS). Terukur di
#    bawah 1 ms per frame.
# 3. Koordinatnya sama dengan koordinat game. Area main rata kiri di
#    (0,0), jadi x >= 1280 berarti panel - tidak ada translasi.
# ================================

import pygame

from mobile import platform_utils as plat

# warna
FG = (228, 230, 242)
DIM = (146, 150, 172)
EMAS = (255, 205, 90)
OK = (120, 235, 140)
BAHAYA = (255, 110, 110)
BIRU = (120, 200, 255)
UNGU = (190, 165, 255)

JEDA_SEGAR_MS = 250
MIN_TAP = 80


class PanelButton:
    def __init__(self, action, rect, label, warna=EMAS, font_size=20):
        self.action = action
        self.rect = pygame.Rect(rect)
        self.label = label
        self.warna = warna
        self.font_size = font_size
        self.visible = True
        self.press_anim = 0.0
        self.hit_rect = self.rect.inflate(
            max(0, MIN_TAP - self.rect.width),
            max(0, MIN_TAP - self.rect.height))

    def contains(self, pos):
        return self.visible and self.hit_rect.collidepoint(pos)


class SidePanel:
    """Menggambar dan menangani sentuhan pada panel kanan."""

    def __init__(self, get_font):
        self.get_font = get_font
        self.rect = None
        self._latar = None          # salinan batu untuk menghapus frame lalu
        self._teks_cache = None
        self._teks_at = 0.0
        self.buttons = {}
        self._isi_buf = None
        self._isi_at = 0
        self._notif_kotor = False
        self.notifikasi = []        # [(teks, warna, sisa_ms)]
        self.aktif = False
        self._rebuild()

    # ── penyiapan ─────────────────────────────────────
    def _rebuild(self):
        self.rect = plat.get_panel_rect()
        self.aktif = self.rect is not None
        self.buttons = {}
        self._isi_buf = None
        if not self.aktif:
            return

        r = self.rect
        pad = 14
        by = 16
        bw = (r.width - pad * 3) // 2
        bw = max(60, min(bw, 130))

        self.buttons["pause"] = PanelButton(
            "pause", (r.x + pad, by, bw, 58), "JEDA", EMAS, 20)
        self.buttons["debug"] = PanelButton(
            "debug", (r.right - pad - bw, by, bw, 58), "FPS", BIRU, 18)

        # Simpan latar batu supaya bisa dipulihkan tiap frame tanpa
        # menggambar ulang ratusan bata.
        try:
            full = plat.get_full_surface()
            self._latar = full.subsurface(r).copy()
        except Exception:
            self._latar = None

    def pastikan_siap(self):
        if self.rect is None or self.rect != plat.get_panel_rect():
            self._rebuild()

    # ── input ─────────────────────────────────────────
    def hit_test(self, pos):
        if not self.aktif:
            return None
        for b in self.buttons.values():
            if b.contains(pos):
                b.press_anim = 1.0
                return b.action
        return None

    def blocks(self, pos):
        """True kalau titik ini milik panel (bukan peta)."""
        return bool(self.aktif and self.rect.collidepoint(pos))

    # ── notifikasi ────────────────────────────────────
    def beri_tahu(self, teks, warna=EMAS, durasi_ms=2600):
        self.notifikasi.append([str(teks), warna, durasi_ms])
        del self.notifikasi[:-5]
        self._notif_kotor = True

    # ── gambar ────────────────────────────────────────
    def draw(self, full, game, clock, dt_ms=16, paksa_blit=False):
        """
        Isi panel digambar ke SURFACE CACHE, bukan langsung tiap frame.

        Alasannya terukur: menggambar penuh tiap frame memakan
        0,45 ms. Kelihatannya kecil, tapi game ini hanya meleset
        0,7 ms dari tenggat vsync 60 FPS - 0,45 ms itu dua pertiga
        jaraknya. Isi panel (emas, HP, level) tidak perlu diperbarui
        60x per detik; 4x per detik sudah lebih dari cukup dan
        justru lebih terbaca.

        Notifikasi tetap digambar langsung supaya animasinya mulus.
        """
        if not self.aktif:
            return
        self.pastikan_siap()
        if not self.aktif:
            return
        r = self.rect

        try:
            sekarang = pygame.time.get_ticks()
        except Exception:
            sekarang = 0

        perlu = (self._isi_buf is None
                 or sekarang - self._isi_at >= JEDA_SEGAR_MS
                 or self._ada_animasi_tombol())
        if perlu:
            if self._isi_buf is None or self._isi_buf.get_size() != r.size:
                self._isi_buf = pygame.Surface(r.size).convert()
            buf = self._isi_buf
            if self._latar is not None:
                buf.blit(self._latar, (0, 0))
            else:
                buf.fill((18, 16, 26))
            self._gambar_tombol(buf)
            y = 88
            y = self._gambar_status(buf, game, y)
            y = self._gambar_hero(buf, game, y)
            self._isi_at = sekarang

        # ═══ HANYA DI-BLIT SAAT PERLU ═══
        # Arena adalah subsurface yang terpotong di x=1280, jadi game
        # TIDAK PERNAH menimpa piksel panel. Menyalin 344x720 tiap
        # frame (0,25 ms) itu murni pemborosan; cukup saat isinya
        # benar-benar berubah.
        # paksa_blit dipakai saat ada popup game yang menggambar KE
        # DALAM panel (panel hero terpilih, popup upgrade). Popup itu
        # digambar SESUDAH panel, jadi panel harus dipulihkan penuh
        # setiap frame - kalau tidak, jejak popup frame sebelumnya
        # tertinggal saat popup ditutup.
        if perlu or paksa_blit:
            full.blit(self._isi_buf, r.topleft)
            self._notif_kotor = True

        # Notifikasi berubah tiap frame, jadi hanya JALURNYA yang
        # dipulihkan dari cache lalu digambar ulang.
        jalur = pygame.Rect(r.x, r.y + r.height // 2,
                            r.width, r.height // 2)
        if self.notifikasi or self._notif_kotor:
            full.blit(self._isi_buf,
                      jalur.topleft,
                      pygame.Rect(0, r.height // 2, r.width, r.height // 2))
            self._notif_kotor = bool(self.notifikasi)
        self._gambar_notifikasi(full, r, dt_ms)

    def _ada_animasi_tombol(self):
        return any(b.press_anim > 0 for b in self.buttons.values())

    def _gambar_tombol(self, full):
        """Digambar ke buffer, jadi koordinatnya relatif terhadap panel."""
        f = self.get_font(19, "body_bold")
        ox, oy = self.rect.topleft
        for b in self.buttons.values():
            if not b.visible:
                continue
            rr = b.rect.move(-ox, -oy)
            warna_isi = (30, 27, 44)
            if b.press_anim > 0:
                b.press_anim = max(0.0, b.press_anim - 0.12)
                k = int(30 * b.press_anim)
                warna_isi = (30 + k, 27 + k, 44 + k)
            pygame.draw.rect(full, warna_isi, rr, border_radius=10)
            pygame.draw.rect(full, b.warna, rr, 2, border_radius=10)
            t = f.render(b.label, True, b.warna)
            full.blit(t, t.get_rect(center=rr.center))

    def _kotak(self, full, x, y, w, h, judul=None):
        pygame.draw.rect(full, (22, 19, 32), (x, y, w, h), border_radius=8)
        pygame.draw.rect(full, (64, 56, 86), (x, y, w, h), 1, border_radius=8)
        if judul:
            f = self.get_font(13, "body_bold")
            full.blit(f.render(judul, True, DIM), (x + 8, y + 5))

    def _gambar_status(self, full, game, y):
        r = self.rect
        pad = 14
        w = r.width - pad * 2
        x = pad
        h = 92
        self._kotak(full, x, y, w, h, "STATUS")

        f_besar = self.get_font(26, "body_bold")
        f = self.get_font(15, "body")

        emas = int(getattr(game, "gold", 0) or 0) if game else 0
        t = f_besar.render("%d" % emas, True, EMAS)
        full.blit(t, (x + 10, y + 22))
        full.blit(f.render("emas", True, DIM), (x + 12, y + 52))

        wave = getattr(game, "wave_number", None) if game else None
        if wave is None and game is not None:
            wave = getattr(game, "current_wave", None)
        lvl = getattr(game, "level_number", None) if game else None
        kanan = x + w - 10
        if lvl is not None:
            t = f.render("LV %s" % lvl, True, FG)
            full.blit(t, (kanan - t.get_width(), y + 26))
        if wave is not None:
            t = f.render("wave %s" % wave, True, DIM)
            full.blit(t, (kanan - t.get_width(), y + 48))
        return y + h + 10

    def _gambar_hero(self, full, game, y):
        r = self.rect
        pad = 14
        w = r.width - pad * 2
        x = pad

        pahlawan = []
        if game is not None:
            try:
                pahlawan = [h for h in game.get_all_heroes()
                            if getattr(h, "team", "blue") == "blue"][:5]
            except Exception:
                pahlawan = []

        tinggi_baris = 46
        h = 24 + max(1, len(pahlawan)) * tinggi_baris
        h = min(h, r.height - y - 120)
        if h < 40:
            return y
        self._kotak(full, x, y, w, h, "HERO")

        if not pahlawan:
            f = self.get_font(14, "body")
            full.blit(f.render("belum ada hero", True, DIM), (x + 10, y + 30))
            return y + h + 10

        f_nama = self.get_font(15, "body_bold")
        f_kecil = self.get_font(12, "body")
        by = y + 22
        for hero in pahlawan:
            if by + tinggi_baris > y + h:
                break
            nama = str(getattr(hero, "name", "?"))[:12]
            hidup = bool(getattr(hero, "alive", True))
            warna_nama = FG if hidup else BAHAYA
            full.blit(f_nama.render(nama, True, warna_nama), (x + 9, by))

            lv = getattr(hero, "level", None)
            if lv is not None:
                t = f_kecil.render("Lv%s" % lv, True, EMAS)
                full.blit(t, (x + w - 10 - t.get_width(), by + 2))

            # bar HP
            bx, bw2, bh2 = x + 9, w - 18, 7
            byy = by + 20
            pygame.draw.rect(full, (48, 14, 14), (bx, byy, bw2, bh2))
            try:
                rasio = max(0.0, min(1.0, hero.hp / float(hero.max_hp)))
            except Exception:
                rasio = 0.0
            if rasio > 0:
                warna = (OK if rasio > 0.5
                         else (EMAS if rasio > 0.25 else BAHAYA))
                pygame.draw.rect(full, warna,
                                 (bx, byy, int(bw2 * rasio), bh2))
            pygame.draw.rect(full, (90, 84, 110), (bx, byy, bw2, bh2), 1)

            # titik kesiapan skill
            try:
                siap = [k for k in ("q", "w", "e", "r")
                        if hero.is_skill_ready(k)]
            except Exception:
                siap = []
            dx = bx
            for k in ("q", "w", "e", "r"):
                warna = UNGU if k in siap else (60, 56, 78)
                pygame.draw.circle(full, warna, (dx + 5, byy + 18), 4)
                dx += 14
            by += tinggi_baris
        return y + h + 10

    def _gambar_notifikasi(self, full, r, dt_ms):
        if not self.notifikasi:
            return
        f = self.get_font(16, "body_bold")
        y = r.bottom - 16
        hidup = []
        for item in self.notifikasi:
            item[2] -= dt_ms
            if item[2] <= 0:
                continue
            hidup.append(item)
        self.notifikasi = hidup
        for teks, warna, sisa in reversed(self.notifikasi):
            t = f.render(str(teks), True, warna)
            y -= t.get_height() + 8
            if y < r.y + 100:
                break
            kotak = pygame.Rect(r.x + 10, y - 4, r.width - 20,
                                t.get_height() + 8)
            pygame.draw.rect(full, (26, 22, 38), kotak, border_radius=6)
            pygame.draw.rect(full, warna, kotak, 1, border_radius=6)
            full.blit(t, t.get_rect(center=kotak.center))


# ═══════════════════════════════════════════════════════
# AKSES GLOBAL
#
# Kode game (combo, achievement, boss muncul) perlu mengirim
# notifikasi tanpa harus mengoper objek panel ke mana-mana.
# Kalau panel tidak ada, semua pemanggilan jadi tidak berefek -
# jadi aman dipakai di perangkat mana pun.
# ═══════════════════════════════════════════════════════
_PANEL = [None]


def daftarkan(panel):
    _PANEL[0] = panel


def panel_aktif():
    p = _PANEL[0]
    return p is not None and p.aktif


def beri_tahu_global(teks, warna=EMAS, durasi_ms=2600):
    p = _PANEL[0]
    if p is not None and p.aktif:
        p.beri_tahu(teks, warna, durasi_ms)
        return True
    return False
