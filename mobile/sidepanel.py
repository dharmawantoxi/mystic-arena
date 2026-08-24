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
#   - tactical commands         (GATHER, PROTECT TOWER/CASTLE, ATTACK BOSS)
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

# Tinggi zona bawah panel (notifikasi + umpan pembunuhan).
# Diambil dari platform_utils supaya SATU sumber angka: kalau zona
# digeser, popup dan notifikasi ikut bergeser bersama-sama.
try:
    from mobile.platform_utils import ZONA_BAWAH_H as ZONA_BAWAH
except Exception:
    ZONA_BAWAH = 120


class PanelButton:
    def __init__(self, action, rect, label, warna=EMAS, font_size=20,
                 ikon=None):
        self.action = action
        self.rect = pygame.Rect(rect)
        self.label = label
        self.ikon = ikon
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

    ZONA_BAWAH = ZONA_BAWAH

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
        self.notifikasi = []
        self.kill_feed = []        # [(teks, warna, sisa_ms)]
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

        # Hanya tombol JEDA, digambar sebagai IKON (dua batang), bukan
        # tulisan - sesuai bentuk aslinya sebelum panel ada.
        # Tombol FPS dihapus: game sudah lancar dan panel debug justru
        # memakan 4 ms dari 12,5 ms waktu gambar.
        self.buttons["pause"] = PanelButton(
            "pause", (r.x + pad, 14, 58, 58), "", EMAS, 20, ikon="pause")

        # Tactical buttons akan dibuat dinamis di _gambar_tactical,
        # tapi buat placeholder di sini supaya hit_test langsung bisa
        # dipakai sejak frame pertama (sebelum draw pertama).
        # Posisi placeholder akan di-update di draw.
        # Kita buat di koordinat yang kira-kira sama dengan posisi
        # akhirnya (di bawah HEROES).
        tac_y_base = 84 + 96 + 10 + 236 + 10  # status + heroes + gap
        tac_btn_h = 32
        tac_gap = 6
        for i, (act, lbl, col) in enumerate([
            ("gather", "GATHER [G]", BIRU),
            ("protect_tower", "PROTECT TOWER [T]", OK),
            ("protect_castle", "PROTECT CASTLE [C]", EMAS),
            ("attack_boss", "ATTACK BOSS [B]", BAHAYA),
        ]):
            by = tac_y_base + i * (tac_btn_h + tac_gap)
            # Placeholder rect - akan di-update di _gambar_tactical
            self.buttons[act] = PanelButton(
                act, (r.x + pad + 6, r.y + by, r.width - pad*2 - 12, tac_btn_h),
                lbl, col, 13)

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

    # ── umpan pembunuhan ──────────────────────────────
    def catat_kill(self, pembunuh, korban, tim="blue"):
        """
        Baris "Blue Tower >> Goblin" yang dulu melintas di atas peta.

        Disimpan terpisah dari notifikasi supaya keduanya tidak
        berebut tempat: kill feed di tengah panel, notifikasi besar
        (combo/achievement) di bawah.
        """
        warna = BIRU if str(tim).startswith("blue") else BAHAYA
        self.kill_feed.append([str(pembunuh)[:14], str(korban)[:14],
                               warna, 3400])
        del self.kill_feed[:-6]
        self._notif_kotor = True

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
            y = 84
            y = self._gambar_status(buf, game, y)
            y = self._gambar_hero(buf, game, y)
            y = self._gambar_tactical(buf, game, y)
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
        zona_y = r.height - self.ZONA_BAWAH
        if self.notifikasi or self.kill_feed or self._notif_kotor:
            full.blit(self._isi_buf,
                      (r.x, r.y + zona_y),
                      pygame.Rect(0, zona_y, r.width, self.ZONA_BAWAH))
            self._notif_kotor = bool(self.notifikasi or self.kill_feed)
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
            if b.ikon == "pause":
                bw2, bh2, sela = 7, 24, 7
                cx, cy = rr.center
                for dx in (-(sela // 2) - bw2, sela // 2):
                    pygame.draw.rect(full, b.warna,
                                     (cx + dx, cy - bh2 // 2, bw2, bh2),
                                     border_radius=2)
            elif b.label:
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
        h = 96
        self._kotak(full, x, y, w, h, "STATUS")

        f_besar = self.get_font(22, "body_bold")
        f_mid = self.get_font(16, "body_bold")
        f = self.get_font(13, "body")
        f_small = self.get_font(12, "body")

        emas = int(getattr(game, "gold", 0) or 0) if game else 0
        # Format gold to avoid overlap: 1234 -> 1.2K, but keep full if small
        if emas >= 10000:
            emas_str = f"{emas/1000:.1f}K"
        else:
            emas_str = f"{emas:,}"

        # Gold on left, avoid overlap with right side
        t = f_besar.render(emas_str, True, EMAS)
        # Truncate if too wide
        max_gold_w = int(w * 0.55)
        if t.get_width() > max_gold_w:
            # Reduce font
            f_besar_small = self.get_font(18, "body_bold")
            t = f_besar_small.render(emas_str, True, EMAS)
        full.blit(t, (x + 10, y + 22))
        full.blit(f.render("GOLD", True, DIM), (x + 10, y + 46))

        # Mode Tag
        is_hard = getattr(game, "enemy_scaling_enabled", False) if game else False
        mode_str = "HARD [SCALE ON]" if is_hard else "NORMAL [SCALE OFF]"
        mode_col = BAHAYA if is_hard else OK
        full.blit(f_small.render(mode_str, True, mode_col), (x + 10, y + 68))

        wave = getattr(game, "wave_number", None) if game else None
        if wave is None and game is not None:
            wave = getattr(game, "current_wave", None)
        lvl = getattr(game, "level_number", None) if game else None
        kanan = x + w - 10

        # Right side - Level and Wave with proper spacing, no overlap
        ry = y + 24
        if lvl is not None:
            # Shield indicator if active
            try:
                shield_active = False
                if game:
                    shield_active = getattr(game.blue_base, 'shield_active', False)
                if shield_active and wave is not None and wave < 10:
                    lvl_text = f"LV {lvl} [SHIELDED]"
                    t = f_small.render(lvl_text, True, (100, 200, 255))
                else:
                    t = f_mid.render(f"LV {lvl}", True, FG)
            except Exception:
                t = f_mid.render(f"LV {lvl}", True, FG)
            full.blit(t, (kanan - t.get_width(), ry))
            ry += 20

        if wave is not None:
            # Wave with shield warning
            try:
                if wave < 10:
                    wave_str = f"Wave {wave} (Shield)"
                    wave_color = (100, 200, 255)
                else:
                    wave_str = f"Wave {wave}"
                    wave_color = DIM
            except Exception:
                wave_str = f"Wave {wave}"
                wave_color = DIM
            t = f.render(wave_str, True, wave_color)
            full.blit(t, (kanan - t.get_width(), ry))

        return y + h + 10

    def _gambar_hero(self, full, game, y):
        r = self.rect
        pad = 14
        w = r.width - pad * 2
        x = pad

        pahlawan = []
        if game is not None:
            try:
                semua = [h for h in game.get_all_heroes()
                         if getattr(h, "team", "blue") == "blue"]
                # ═══ MAKSIMAL 5 BARIS ═══
                # BUG LAMA: dipotong 3 (semua[:3]) padahal pemain bisa
                # memiliki 5 hero (MAX_HEROES_OWNED = 5) - hero ke-4
                # dan ke-5 tidak pernah muncul di panel walau sudah
                # di-summon. Sekarang semua 5 ditampilkan; barisnya
                # dipadatkan (46 -> 42 px) dan jalur popup/notifikasi
                # di platform_utils digeser supaya tidak bertabrakan.
                pahlawan = semua[:5]
                self._hero_lebih = max(0, len(semua) - 5)
            except Exception:
                pahlawan = []
                self._hero_lebih = 0

        tinggi_baris = 42
        h = 22 + max(1, len(pahlawan)) * tinggi_baris
        if getattr(self, "_hero_lebih", 0):
            h += 14
        h = min(h, 236)
        if h < 40:
            return y
        self._kotak(full, x, y, w, h, "HEROES")

        if not pahlawan:
            f = self.get_font(14, "body")
            full.blit(f.render("No heroes", True, DIM), (x + 10, y + 30))
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
            bx, bw2, bh2 = x + 9, w - 18, 6
            byy = by + 19
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

            # titik kesiapan skill (dinaikkan supaya muat di baris 42)
            try:
                siap = [k for k in ("q", "w", "e", "r")
                        if hero.is_skill_ready(k)]
            except Exception:
                siap = []
            dx = bx
            for k in ("q", "w", "e", "r"):
                warna = UNGU if k in siap else (60, 56, 78)
                pygame.draw.circle(full, warna, (dx + 5, byy + 13), 4)
                dx += 14
            by += tinggi_baris
        if getattr(self, "_hero_lebih", 0) and by + 14 <= y + h:
            f_kecil2 = self.get_font(12, "body")
            full.blit(f_kecil2.render("+%d more" % self._hero_lebih,
                                      True, DIM), (x + 9, by - 2))
        return y + h + 10

    def _gambar_tactical(self, full, game, y):
        """Tactical command buttons: GATHER, PROTECT TOWER, PROTECT CASTLE, ATTACK BOSS"""
        if game is None:
            return y
        if getattr(game, 'state', '') != 'playing':
            return y

        r = self.rect
        pad = 14
        w = r.width - pad * 2
        x = pad

        # Cek kondisi
        alive_heroes = [h for h in getattr(game, 'heroes', []) if getattr(h, 'alive', False)]
        has_boss = getattr(game, 'active_boss', None) and getattr(game.active_boss, 'alive', False)

        # Hitung tinggi kotak: judul 22 + 4 baris tombol (32+gap)
        btn_h = 32
        gap = 6
        num_btns = 4
        h = 26 + num_btns * (btn_h + gap) - gap
        # Jangan gambar kalau tidak ada ruang (zona bawah)
        if y + h > r.height - self.ZONA_BAWAH - 8:
            return y

        self._kotak(full, x, y, w, h, "TACTICAL COMMANDS")

        f_btn = self.get_font(13, "body_bold")
        f_small = self.get_font(11, "body")

        # Definisi tombol
        tactical_defs = [
            ("gather", "GATHER [G]", BIRU, len(alive_heroes) > 0, "Semua hero kumpul & serang bersama"),
            ("protect_tower", "PROTECT TOWER [T]", OK, len(alive_heroes) >= 1, "Min 2 hero lindungi tower"),
            ("protect_castle", "PROTECT CASTLE [C]", EMAS, len(alive_heroes) > 0, "Semua hero lindungi castle"),
            ("attack_boss", "ATTACK BOSS [B]", BAHAYA, has_boss, "Semua hero serang boss"),
        ]

        by = y + 24
        ox, oy = self.rect.topleft

        for action, label, warna, enabled, desc in tactical_defs:
            # Posisi tombol relatif terhadap panel buffer (full), tapi hit_test pakai koordinat layar penuh
            # Jadi kita buat rect di koordinat layar penuh untuk hit_test, lalu convert ke buffer
            screen_rect = pygame.Rect(r.x + x + 6, r.y + by, w - 12, btn_h)
            # Simpan untuk hit_test (pakai koordinat layar)
            self.buttons[action] = PanelButton(action, screen_rect, label, warna, 13)

            # Gambar di buffer (koordinat relatif)
            buf_rect = pygame.Rect(x + 6, by, w - 12, btn_h)

            if not enabled:
                bg = (45, 45, 50)
                border = (80, 80, 85)
                txt_col = (120, 120, 125)
            else:
                # Animasi tekan
                btn_obj = self.buttons.get(action)
                press = getattr(btn_obj, 'press_anim', 0) if btn_obj else 0
                if press > 0:
                    k = int(25 * press)
                    bg = (warna[0]//3 + k, warna[1]//3 + k, warna[2]//3 + k)
                    border = (255, 255, 255)
                    txt_col = (255, 255, 255)
                else:
                    bg = (warna[0]//4, warna[1]//4, warna[2]//4)
                    border = warna
                    txt_col = warna

            pygame.draw.rect(full, bg, buf_rect, border_radius=6)
            pygame.draw.rect(full, border, buf_rect, 2, border_radius=6)

            txt = f_btn.render(label, True, txt_col)
            full.blit(txt, txt.get_rect(center=buf_rect.center))

            by += btn_h + gap

        return y + h + 10

    def _gambar_notifikasi(self, full, r, dt_ms):
        """
        Zona bawah panel, disusun dari bawah ke atas:

            [notifikasi besar]   combo / achievement / killing spree
            [umpan pembunuhan]   Blue Tower >> Goblin

        Keduanya dipisah supaya tidak berebut tempat. Batas atasnya
        dijaga di ZONA_BAWAH agar tidak menabrak panel upgrade hero.
        """
        # kurangi umur
        for daftar in (self.notifikasi, self.kill_feed):
            for item in daftar:
                item[-1] -= dt_ms
        self.notifikasi = [i for i in self.notifikasi if i[-1] > 0]
        self.kill_feed = [i for i in self.kill_feed if i[-1] > 0]
        if not self.notifikasi and not self.kill_feed:
            return

        batas_atas = r.bottom - self.ZONA_BAWAH
        y = r.bottom - 12

        # ── notifikasi besar (paling bawah, paling menonjol) ──
        f = self.get_font(17, "body_bold")
        for teks, warna, sisa in reversed(self.notifikasi):
            t = f.render(str(teks), True, warna)
            y -= t.get_height() + 10
            if y < batas_atas:
                break
            kotak = pygame.Rect(r.x + 10, y - 5, r.width - 20,
                                t.get_height() + 10)
            pygame.draw.rect(full, (26, 22, 38), kotak, border_radius=6)
            pygame.draw.rect(full, warna, kotak, 1, border_radius=6)
            full.blit(t, t.get_rect(center=kotak.center))

        # ── umpan pembunuhan (di atasnya, lebih kecil) ──
        fk = self.get_font(13, "body")
        for pembunuh, korban, warna, sisa in reversed(self.kill_feed):
            baris = "%s  »  %s" % (pembunuh, korban)
            t = fk.render(baris, True, warna)
            y -= t.get_height() + 5
            if y < batas_atas:
                break
            full.blit(t, (r.x + 14, y))


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


def catat_kill_global(pembunuh, korban, tim="blue"):
    p = _PANEL[0]
    if p is not None and p.aktif:
        p.catat_kill(pembunuh, korban, tim)
        return True
    return False
