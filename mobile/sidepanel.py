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
                 ikon=None, tap_pad=None):
        self.action = action
        self.rect = pygame.Rect(rect)
        self.label = label
        self.ikon = ikon
        self.warna = warna
        self.font_size = font_size
        self.visible = True
        self.press_anim = 0.0
        # tap_pad=None -> perilaku lama: dilebarkan sampai MIN_TAP
        # (cocok untuk tombol tunggal seperti JEDA).
        # tap_pad=N -> hit box diberi bantalan N px tiap sisi. Dipakai
        # tombol-tombol sempit yang rapat (tactical commands): bantalan
        # MIN_TAP=80 pada tombol setinggi 32 px membuat area sentuhnya
        # menutupi tombol di atas/bawah, sehingga ketukan "tembus" ke
        # tombol lain - atau ke tombol yang lagi tertutup popup.
        if tap_pad is None:
            self.hit_rect = self.rect.inflate(
                max(0, MIN_TAP - self.rect.width),
                max(0, MIN_TAP - self.rect.height))
        else:
            self.hit_rect = self.rect.inflate(tap_pad * 2, tap_pad * 2)

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
        # True hanya saat isi panel memang sedang ditampilkan
        # (dalam gameplay). Notifikasi di luar gameplay tidak
        # disimpan supaya tidak "menunggu" lalu muncul belakangan.
        self.dalam_gameplay = False
        # (id(game), state) terakhir yang digambar - dipakai untuk
        # memaksa isi cache segar saat status game berganti.
        self._kunci_state = None
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

        # Tombol tactical dibuat dinamis di _gambar_tactical karena
        # posisinya bergantung pada tinggi daftar hero. Placeholder
        # dibuat di sini supaya tombolnya SUDAH ADA (dan tidak "hantu")
        # sebelum draw pertama; posisinya akan di-update di draw dan
        # tombolnya baru boleh ditekan setelah benar-benar digambar.
        tac_y_base = 84 + 96 + 10 + 236 + 10  # status + heroes + gap
        tac_btn_h = 32
        tac_gap = 6
        for i, (act, lbl, col) in enumerate([
            ("gather", "GATHER [G]", BIRU),
            ("protect_tower", "PROTECT TOWER [T]", OK),
            ("protect_castle", "PROTECT CASTLE [C]", EMAS),
            ("attack_boss", "ATTACK BOSS [B]", BAHAYA),
            ("attack_damage_dealer", "ATTACK DMG DEALER [D]", UNGU),
        ]):
            by = tac_y_base + i * (tac_btn_h + tac_gap)
            # Placeholder rect - akan di-update di _gambar_tactical.
            # Bantalan sentuh kecil (3 px) supaya hit box tidak menutupi
            # tombol tetangga (jarak antar tombol 38 px).
            tombol = PanelButton(
                act, (r.x + pad + 6, r.y + by, r.width - pad*2 - 12, tac_btn_h),
                lbl, col, 13, tap_pad=3)
            # Sembunyikan sampai digambar sungguhan: posisinya di atas
            # belum final (tergantung jumlah hero), jadi tidak boleh
            # bisa ditekan sebelum draw pertama (hindari "tombol hantu").
            tombol.visible = False
            self.buttons[act] = tombol

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

    def _bersihkan_panel(self, full):
        """
        Kosongkan isi panel (dipakai di luar gameplay: splash, menu).

        Latar batu dipulihkan, semua tombol disembunyikan, cache isi
        dibuang, dan sisa notifikasi/kill feed dibersihkan supaya tidak
        "menunggu" lalu muncul lagi setelah gameplay dimulai.
        """
        r = self.rect
        if self._latar is not None:
            full.blit(self._latar, r.topleft)
        else:
            full.fill((18, 16, 26), r)
        for b in self.buttons.values():
            b.visible = False
        self._isi_buf = None
        self._isi_at = 0.0
        self.notifikasi = []
        self.kill_feed = []
        self._notif_kotor = False
        self.dalam_gameplay = False

    # ── input ─────────────────────────────────────────
    @staticmethod
    def ada_popup_game(game):
        """
        True kalau game punya overlay yang digambar DI ATAS area panel:

          - popup tower/nexus   (popup_target)
          - popup build tower   (build_popup_slot)
          - panel hero terpilih (selected_hero)

        Popup itu menutupi tombol command, jadi ketukan di wilayah
        popup harus sampai ke popup - bukan "tembus" ke tombol command
        yang kebetulan berada di baliknya.
        """
        if game is None:
            return False
        if getattr(game, "popup_target", None) is not None:
            return True
        if getattr(game, "build_popup_slot", None) is not None:
            return True
        hero = getattr(game, "selected_hero", None)
        if hero is not None and getattr(hero, "alive", True):
            return True
        return False

    def hit_test(self, pos, game=None):
        if not self.aktif:
            return None
        popup_terbuka = self.ada_popup_game(game)
        for b in self.buttons.values():
            # Saat popup menutupi panel, hanya tombol JEDA yang boleh
            # merespons (posisinya di jalur atas, tidak kena popup).
            # Tombol command dilewati supaya klik yang sedang menimpa
            # popup (mis. tombol UPGRADE tower) tidak "tembus" ke
            # command di baliknya.
            if popup_terbuka and b.action != "pause":
                continue
            if b.contains(pos):
                b.press_anim = 1.0
                return b.action
        return None

    def blocks(self, pos):
        """True kalau titik ini milik panel (bukan peta)."""
        return bool(self.aktif and self.rect.collidepoint(pos))

    # ── umpan pembunuhan & notifikasi: DIHAPUS (request user) ──
    # Kill feed + kotak notifikasi tidak lagi tampil di panel;
    # zona bawah panel diisi COMMAND saja. Method tetap ada sebagai
    # no-op supaya pemanggil lama (game, _render, tactical) aman.
    def catat_kill(self, pembunuh, korban, tim="blue"):
        """No-op: kill feed dihapus dari panel."""
        return

    def beri_tahu(self, teks, warna=EMAS, durasi_ms=2600):
        """No-op: notifikasi dihapus dari panel (muncul di map)."""
        return

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

        (Notifikasi & kill feed dihapus dari panel - zona bawah
        sekarang dipakai kotak TACTICAL COMMANDS yang lebih tinggi.)
        """
        if not self.aktif:
            return
        self.pastikan_siap()
        if not self.aktif:
            return
        r = self.rect

        # ═══ ISI PANEL HANYA SAAT GAMEPLAY ═══
        # Panel kanan menampilkan STATUS / HERO / TACTICAL COMMANDS.
        # Itu semua informasi IN-GAME. Di splash screen atau menu,
        # game=None sehingga angka-angka itu kosong/menghalu (gold 0,
        # "No heroes") - terlihat seperti bocor dari dalam game.
        # Karena itu di luar gameplay panel dikosongkan: kembali ke
        # latar batu polos dan semua tombol disembunyikan.
        dalam_gp = (game is not None
                    and getattr(game, "state", "playing") in
                    ("playing", "victory", "defeat"))
        if not dalam_gp:
            self.dalam_gameplay = False
            self._bersihkan_panel(full)
            return

        self.dalam_gameplay = True

        # Tombol JEDA selalu hidup selama gameplay (di luar gameplay
        # dia ikut disembunyikan oleh _bersihkan_panel).
        jeda = self.buttons.get("pause")
        if jeda is not None:
            jeda.visible = True

        try:
            sekarang = pygame.time.get_ticks()
        except Exception:
            sekarang = 0

        perlu = (self._isi_buf is None
                 or sekarang - self._isi_at >= JEDA_SEGAR_MS
                 or self._ada_animasi_tombol())
        if not perlu:
            # Ganti isi cache SEKARANG juga saat status game berubah
            # (playing -> victory/defeat, game baru dari menu, dst.).
            # Kalau hanya mengandalkan JEDA_SEGAR_MS, tombol command
            # bisa tetap "hidup" sampai 250 ms setelah layar
            # menang/kalah muncul - lalu bisa ditekan lewat layar
            # overlay yang menggambar di atas peta.
            kunci = (id(game), getattr(game, "state", ""))
            if kunci != self._kunci_state:
                perlu = True
        self._kunci_state = (id(game), getattr(game, "state", ""))
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

        # ═══ NOTIFIKASI & KILL FEED DIHAPUS (request user) ═══
        # Zona bawah panel dulu memuat kotak notifikasi besar
        # (combo/achievement) + umpan pembunuhan. Keduanya tidak
        # lagi digambar: achievement & combo tampil DI MAP, panel
        # kanan diisi COMMAND saja (lihat _gambar_tactical).

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

        # ═══ BARIS KOMPAK SAAT 5 HERO ═══
        # BUG LAMA: begitu hero ke-5 di-summon, kotak HEROES tumbuh
        # ke 232 px (5 x 42) dan mendorong TACTICAL COMMANDS ke y=432.
        # Kotak tactical (172 px) lalu berakhir di 604 - melewati batas
        # aman 592 (di atas zona notifikasi) - sehingga _gambar_tactical
        # MENYEMBUNYIKAN SEMUA tombol command. Panel kanan kelihatan
        # "kehilangan" tactical commands padahal cuma tidak muat.
        # Sekarang tinggi baris menyesuaikan: 4 hero ke bawah tetap
        # 42 px (lega), 5 hero dipadatkan ke 38 px supaya kotak
        # tactical mendapat tempat penuh lagi (412..584, di atas batas).
        tinggi_baris = 38 if (len(pahlawan) >= 5
                              or getattr(self, "_hero_lebih", 0)) else 42
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

    TACTICAL_KEYS = ("gather", "protect_tower", "protect_castle",
                     "attack_boss", "attack_damage_dealer")

    def _tactical_sembunyikan(self):
        """
        Tombol command tidak digambar frame ini -> matikan juga
        area sentuhnya. Kalau tidak, tombol lama (posisinya bahkan
        bisa belum final) tetap "hidup" dan ketukan di mana pun di
        panel bisa tembus ke command - misalnya saat layar menang/
        kalah atau saat panel belum sempat digambar.
        """
        for k in self.TACTICAL_KEYS:
            b = self.buttons.get(k)
            if b is not None:
                b.visible = False

    def _gambar_tactical(self, full, game, y):
        """Tactical command buttons: GATHER, PROTECT TOWER, PROTECT CASTLE, ATTACK BOSS"""
        if game is None:
            self._tactical_sembunyikan()
            return y
        if getattr(game, 'state', '') != 'playing':
            self._tactical_sembunyikan()
            return y

        r = self.rect
        pad = 14
        w = r.width - pad * 2
        x = pad

        # Cek kondisi
        alive_heroes = [h for h in getattr(game, 'heroes', []) if getattr(h, 'alive', False)]
        has_boss = getattr(game, 'active_boss', None) and getattr(game.active_boss, 'alive', False)
        # Hero musuh hidup (untuk ATTACK DMG DEALER)
        _ai = getattr(game, 'ai', None)
        has_enemy_hero = any(getattr(h, 'alive', False)
                             for h in getattr(_ai, 'heroes', []))

        # Hitung tinggi kotak: judul 22 + 5 baris tombol (32+gap).
        # (Zona bawah panel kini kosong - notifikasi & kill feed
        #  DIHAPUS, panel diisi COMMAND saja - request user.)
        btn_h = 32
        gap = 6
        num_btns = 5
        h = 26 + num_btns * (btn_h + gap) - gap
        # Jangan gambar kalau tidak ada ruang (zona bawah)
        if y + h > r.height - 24:
            self._tactical_sembunyikan()
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
            ("attack_damage_dealer", "ATTACK DMG DEALER [D]", UNGU, has_enemy_hero, "Fokus hero musuh damage terbesar"),
        ]

        by = y + 24
        ox, oy = self.rect.topleft

        for action, label, warna, enabled, desc in tactical_defs:
            # Posisi tombol relatif terhadap panel buffer (full), tapi hit_test pakai koordinat layar penuh
            # Jadi kita buat rect di koordinat layar penuh untuk hit_test, lalu convert ke buffer
            screen_rect = pygame.Rect(r.x + x + 6, r.y + by, w - 12, btn_h)
            # Simpan untuk hit_test (pakai koordinat layar)
            # tap_pad=3: bantalan sentuh kecil. Bantalan MIN_TAP=80
            # (24 px ke atas & bawah tombol 32 px) membuat tombol
            # saling menelan klik satu sama lain DAN menelan klik
            # popup yang digambar di atasnya (upgrade tower, dll).
            btn = PanelButton(action, screen_rect, label, warna, 13,
                              tap_pad=3)
            # Hanya di side panel, jika tidak enabled (misal no boss) → hidden / disabled
            # Attack Boss hanya muncul saat ada boss, sesuai permintaan visual sesaat
            btn.visible = bool(enabled)
            self.buttons[action] = btn

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


# ═══ NOTIFIKASI DIHAPUS (request user) ═══
# Fungsi global tetap ada (dipanggil dari banyak tempat) tapi tidak
# lagi menampilkan apa pun di panel - selalu False supaya pemanggil
# tahu tidak ada panel notifikasi yang menerima pesan.
def beri_tahu_global(teks, warna=EMAS, durasi_ms=2600):
    return False


def catat_kill_global(pembunuh, korban, tim="blue"):
    return False
