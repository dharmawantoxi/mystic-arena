# ================================
# mobile/platform_utils.py
# Deteksi platform + setup layar Android (scaling, safe area, orientasi)
# ================================

import os
import sys

# ═══════════════════════════════════════════════════════
# HINT SDL - HARUS diset SEBELUM pygame.init()
#
# SDL_RENDER_DRIVER=opengles2
#     Paksa scaling 720p -> layar HP dikerjakan GPU. Kalau SDL
#     jatuh ke renderer "software", CPU yang menskalakan tiap
#     frame dan game langsung tidak playable (splash pun berat).
#
# SDL_HINT_RENDER_SCALE_QUALITY=0
#     0 = nearest (paling murah). Default "linear" memaksa
#     penyaringan bilinear saat upscale - mahal di GPU lemah.
#
# SDL_HINT_FRAMEBUFFER_ACCELERATION=1
#     Minta framebuffer berakselerasi bila tersedia.
# ═══════════════════════════════════════════════════════
os.environ.setdefault("SDL_RENDER_DRIVER", "opengles2")
os.environ.setdefault("SDL_HINT_RENDER_SCALE_QUALITY", "0")
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "0")
os.environ.setdefault("SDL_HINT_FRAMEBUFFER_ACCELERATION", "1")

import pygame

# ═══════════════════════════════════════════════════════
# RESOLUSI LOGIS
# Semua kode game lama memakai koordinat absolut 1280x720.
# Kita TIDAK mengubahnya. Sebagai gantinya kita render ke
# permukaan logis 1280x720 lalu SDL yang men-scale ke layar HP
# (pygame.SCALED = scaling di GPU, hampir gratis).
# ═══════════════════════════════════════════════════════
LOGICAL_WIDTH = 1280
LOGICAL_HEIGHT = 720


# ═══════════════════════════════════════════════════════
# DETEKSI ANDROID
# ═══════════════════════════════════════════════════════
def _detect_android():
    if "ANDROID_ARGUMENT" in os.environ:      # dipasang python-for-android
        return True
    if "ANDROID_PRIVATE" in os.environ:
        return True
    if hasattr(sys, "getandroidapilevel"):    # CPython resmi di Android
        return True
    return False


IS_ANDROID = _detect_android()
IS_DESKTOP = not IS_ANDROID

# Dipaksa lewat env var untuk uji coba layout HP di PC:
#     MYSTIC_FORCE_TOUCH=1 python main.py
FORCE_TOUCH = os.environ.get("MYSTIC_FORCE_TOUCH", "0") == "1"
TOUCH_MODE = IS_ANDROID or FORCE_TOUCH


# ═══════════════════════════════════════════════════════
# JEMBATAN KE API ANDROID (opsional, tidak wajib ada)
# ═══════════════════════════════════════════════════════
def keep_screen_on(enable=True):
    """Cegah layar mati saat main (butuh permission WAKE_LOCK)."""
    if not IS_ANDROID:
        return False
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        WindowManager = autoclass("android.view.WindowManager$LayoutParams")
        activity = PythonActivity.mActivity

        def _run():
            if enable:
                activity.getWindow().addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
            else:
                activity.getWindow().clearFlags(
                    WindowManager.FLAG_KEEP_SCREEN_ON)

        activity.runOnUiThread(_run)
        return True
    except Exception as exc:                       # pragma: no cover
        print("[MOBILE] keep_screen_on gagal:", exc)
        return False


def enable_immersive_mode():
    """Sembunyikan status bar & navigation bar (fullscreen game)."""
    if not IS_ANDROID:
        return False
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        View = autoclass("android.view.View")
        activity = PythonActivity.mActivity

        flags = (View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                 | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                 | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                 | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                 | View.SYSTEM_UI_FLAG_FULLSCREEN
                 | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)

        def _run():
            activity.getWindow().getDecorView().setSystemUiVisibility(flags)

        activity.runOnUiThread(_run)
        return True
    except Exception as exc:                       # pragma: no cover
        print("[MOBILE] immersive mode gagal:", exc)
        return False


def get_device_info():
    """Info perangkat untuk overlay debug / laporan bug."""
    info = {
        "platform": "android" if IS_ANDROID else sys.platform,
        "python": sys.version.split()[0],
        "pygame": pygame.version.ver,
        "sdl": ".".join(str(v) for v in pygame.get_sdl_version()),
        "model": "-",
        "android_release": "-",
        "api_level": "-",
    }
    if IS_ANDROID:
        try:
            from jnius import autoclass
            Build = autoclass("android.os.Build")
            VERSION = autoclass("android.os.Build$VERSION")
            info["model"] = "%s %s" % (Build.MANUFACTURER, Build.MODEL)
            info["android_release"] = VERSION.RELEASE
            info["api_level"] = str(VERSION.SDK_INT)
        except Exception:
            pass
    return info


def vibrate(ms=25):
    """Getar pendek sebagai feedback tombol (butuh permission VIBRATE)."""
    if not IS_ANDROID:
        return False
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        vib = PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
        if vib is not None and vib.hasVibrator():
            vib.vibrate(int(ms))
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════
# SETUP LAYAR
# ═══════════════════════════════════════════════════════
_display_state = {
    "surface": None,          # permukaan yang benar-benar dipresentasikan
    "render": None,           # permukaan yang digambari game (bisa sama)
    "mode": "scaled_vsync",
    "full": None,             # permukaan display seutuhnya (bisa > 1280)
    "game_offset": (0, 0),    # posisi area main di dalam permukaan penuh
    "window_size": (LOGICAL_WIDTH, LOGICAL_HEIGHT),
    "scale": 1.0,
    "offset": (0, 0),
}

# ═══════════════════════════════════════════════════════
# MODE TAMPILAN
#
# scaled_vsync : set_mode(720p, SCALED|FULLSCREEN, vsync=1)
#                SDL yang menskalakan ke layar HP (idealnya GPU).
# scaled       : sama, tanpa vsync. Coba kalau vsync bikin tersendat.
# native       : jendela seukuran layar asli; game menggambar ke
#                surface 720p terpisah lalu kita sendiri yang
#                men-scale sekali per frame. Dipakai kalau SCALED
#                justru jatuh ke software renderer.
#
# Mode tersimpan di <folder tulis>/display_mode.txt supaya pilihan
# di layar diagnostik ikut terpakai saat start berikutnya.
# ═══════════════════════════════════════════════════════
# Urutan tombol GANTI MODE.
# Catatan lapangan: walaupun benchmark memberi angka flip lebih kecil
# untuk "scaled", pemain melaporkan FPS NYATA lebih tinggi dengan
# "scaled_vsync" (vsync mencegah frame setengah jadi dan antrean
# tampilan yang menumpuk). Pengalaman nyata menang atas mikro-benchmark,
# jadi scaled_vsync dijadikan default.
DISPLAY_MODES = ("scaled_vsync", "scaled", "native")


def _mode_file():
    return os.path.join(get_writable_dir(), "display_mode.txt")


def load_display_mode():
    env = os.environ.get("MYSTIC_DISPLAY_MODE")
    if env in DISPLAY_MODES:
        return env
    try:
        with open(_mode_file()) as fh:
            mode = fh.read().strip()
        if mode in DISPLAY_MODES:
            return mode
    except Exception:
        pass
    return "scaled_vsync"


def save_display_mode(mode):
    try:
        with open(_mode_file(), "w") as fh:
            fh.write(mode)
        return True
    except Exception:
        return False


def _gambar_panel_samping(surface, panel):
    """
    Latar panel kanan: dinding batu bergaya peta.

    Digambar SEKALI saat layar dibuat. Isi dinamis (tombol, combo,
    daftar hero) digambar di atasnya tiap frame oleh mobile/sidepanel.py,
    yang menyimpan salinan latar ini untuk menghapus jejak frame lalu.
    """
    tinggi = surface.get_height()
    dasar = (16, 14, 24)
    batu_gelap = (26, 23, 38)
    batu = (34, 30, 48)
    garis = (58, 50, 78)
    emas = (150, 120, 60)

    pygame.draw.rect(surface, dasar, panel)

    bh = 34
    bw = max(28, panel.width // 4)
    for i, y in enumerate(range(-bh, tinggi + bh, bh)):
        geser = (bw // 2) if (i % 2) else 0
        for x in range(panel.x - bw, panel.right + bw, bw):
            r = pygame.Rect(x + geser + 1, y + 1, bw - 2, bh - 2).clip(panel)
            if r.width <= 0 or r.height <= 0:
                continue
            pygame.draw.rect(surface, batu if (i + x) % 3 else batu_gelap, r)
            pygame.draw.rect(surface, garis, r, 1)

    # gradasi gelap di sisi kiri panel supaya menyatu dengan arena
    for i in range(20):
        a = 1.0 - (i / 20.0)
        warna = (int(dasar[0] * a), int(dasar[1] * a), int(dasar[2] * a))
        gx = panel.x + i
        pygame.draw.line(surface, warna, (gx, 0), (gx, tinggi))

    # bingkai emas pemisah arena
    pygame.draw.line(surface, emas, (panel.x + 1, 0),
                     (panel.x + 1, tinggi), 2)


def create_display(vsync=True, mode=None):
    """
    Kembalikan permukaan yang HARUS digambari game (render surface).

    Untuk mode scaled_* nilainya sama dengan permukaan display.
    Untuk mode native, ini surface 720p terpisah dan `present()`
    yang menyalinnya ke layar.
    """
    mode = mode or load_display_mode()
    if mode not in DISPLAY_MODES:
        mode = "scaled_vsync"

    if mode == "native":
        flags = pygame.FULLSCREEN if TOUCH_MODE else 0
        surface = pygame.display.set_mode((0, 0) if TOUCH_MODE else
                                          (LOGICAL_WIDTH, LOGICAL_HEIGHT),
                                          flags)
        # PENTING: buffer render dibuat TANPA kanal alpha
        # (mask alpha = 0). Kalau permukaan tujuan punya kanal alpha,
        # SDL memakai blitter generik per-piksel yang di ARM bisa
        # ~200x lebih lambat. XRGB8888 membuka jalur cepat.
        _masks = (0x00FF0000, 0x0000FF00, 0x000000FF, 0)
        try:
            from mobile import blitwatch
            if blitwatch.enabled():
                render = blitwatch.WatchedSurface(
                    (LOGICAL_WIDTH, LOGICAL_HEIGHT), 0, 32, _masks)
                print("[DISPLAY] blitwatch AKTIF (pelacak alpha blit)")
            else:
                render = pygame.Surface(
                    (LOGICAL_WIDTH, LOGICAL_HEIGHT), 0, 32, _masks)
        except Exception:
            render = pygame.Surface(
                (LOGICAL_WIDTH, LOGICAL_HEIGHT), 0, 32, _masks)
    else:
        flags = pygame.SCALED
        if TOUCH_MODE:
            flags |= pygame.FULLSCREEN
        want_vsync = 1 if (vsync and mode == "scaled_vsync") else 0

        # ═══ LAYAR PENUH TANPA STRETCH & TANPA TERPOTONG ═══
        # Layar HP uji 2436x1080 (rasio 2,256), game 1280x720
        # (rasio 1,778). Kalau permukaannya tetap 16:9, SDL memberi
        # bar hitam di kiri-kanan selebar 258 px fisik masing-masing.
        #
        # Tiga cara mengisinya, dan hanya satu yang benar:
        #   - regangkan  -> gambar jadi gepeng   (ditolak)
        #   - perbesar   -> peta terpotong        (ditolak)
        #   - PERLEBAR PERMUKAAN -> tidak ada yang berubah bentuk
        #
        # Yang dipakai: permukaan display dibuat selebar rasio layar
        # (mis. 1624x720), lalu game diberi SUBSURFACE 1280x720 tepat
        # di tengahnya. Seluruh kode game tetap memakai koordinat
        # 1280x720 - tidak ada satu baris pun logika yang berubah,
        # jadi tidak ada risiko regresi gameplay. Sisa ruang kiri-kanan
        # diisi panel hiasan yang digambar SEKALI (0 ms per frame).
        lebar_penuh = LOGICAL_WIDTH
        try:
            if TOUCH_MODE:
                info = pygame.display.Info()
                rasio = info.current_w / float(max(1, info.current_h))
                usul = int(round(LOGICAL_HEIGHT * rasio))
                # dibatasi supaya tidak konyol di layar sangat lebar,
                # dan digenapkan ke bilangan genap
                lebar_penuh = max(LOGICAL_WIDTH, min(2200, usul))
                lebar_penuh -= lebar_penuh % 2
        except Exception:
            lebar_penuh = LOGICAL_WIDTH

        def _pasang(lebar):
            try:
                return pygame.display.set_mode(
                    (lebar, LOGICAL_HEIGHT), flags, vsync=want_vsync)
            except pygame.error:
                return pygame.display.set_mode(
                    (lebar, LOGICAL_HEIGHT), flags)

        try:
            surface = _pasang(lebar_penuh)
        except Exception as exc:
            print("[DISPLAY] lebar %d ditolak (%s) - kembali ke %d"
                  % (lebar_penuh, exc, LOGICAL_WIDTH))
            lebar_penuh = LOGICAL_WIDTH
            surface = _pasang(LOGICAL_WIDTH)

        # ═══ TATA LETAK ASIMETRIS ═══
        # Seluruh ruang sisa dikumpulkan di KANAN, bukan dibagi dua.
        # Alasannya konkret: popup upgrade hero butuh 260-300 px.
        # Dibagi dua (172+172) popup tidak muat dan tetap menutupi
        # peta - masalah yang justru ingin diselesaikan. Dikumpulkan
        # jadi satu, panelnya 344 px dan popup muat utuh.
        #
        # Keuntungan tambahan yang tidak disengaja: area main jadi
        # rata kiri di (0,0), sehingga koordinat game dan koordinat
        # layar penuh SAMA PERSIS. Tidak perlu translasi apa pun untuk
        # sentuhan - satu ruang koordinat untuk peta dan panel.
        sisa = max(0, surface.get_width() - LOGICAL_WIDTH)
        _display_state["full"] = surface
        _display_state["game_offset"] = (0, 0)
        _display_state["panel"] = None

        if sisa >= 120:      # di bawah ini panel terlalu sempit, tidak berguna
            try:
                render = surface.subsurface(
                    (0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT))
                _display_state["panel"] = pygame.Rect(
                    LOGICAL_WIDTH, 0, sisa, LOGICAL_HEIGHT)
                _gambar_panel_samping(surface,
                                      _display_state["panel"])
                print("[DISPLAY] layar penuh %dx%d, area main %dx%d, "
                      "panel kanan %d px"
                      % (surface.get_width(), surface.get_height(),
                         LOGICAL_WIDTH, LOGICAL_HEIGHT, sisa))
            except (ValueError, pygame.error) as exc:
                print("[DISPLAY] subsurface gagal (%s) - pakai layar utuh"
                      % exc)
                render = surface
        else:
            render = surface
            if sisa:
                print("[DISPLAY] sisa %d px terlalu sempit untuk panel"
                      % sisa)

        # ═══ BUFFER RENDER JALUR CEPAT ═══
        # Kalau jalur alpha SDL sudah terbukti menang (fastblit.AKTIF,
        # ditentukan oleh benchmark), game menggambar ke buffer RAM
        # yang blit alpha-nya dialihkan ke blitter SDL, lalu buffer itu
        # disalin sekali per frame ke layar. Biaya salinan terukur
        # 0,95 ms; penghematannya puluhan milidetik.
        try:
            from mobile import fastblit
            if fastblit.AKTIF and fastblit.tersedia():
                render = fastblit.buat_buffer(LOGICAL_WIDTH, LOGICAL_HEIGHT,
                                              surface.get_masks()[:3] + (0,))
                # Buffer RAM menggantikan subsurface: area main
                # kembali ke koordinat 0,0 dan panel samping tidak
                # dipakai pada jalur ini.
                _display_state["game_offset"] = (0, 0)
                print("[DISPLAY] buffer render jalur cepat AKTIF "
                      "(alpha lewat blitter SDL)")
        except Exception as exc:
            print("[DISPLAY] buffer jalur cepat gagal: %s" % exc)

    _display_state["mode"] = mode
    _display_state["render"] = render
    # True hanya kalau render adalah buffer RAM terpisah yang harus
    # disalin ke layar oleh present(). Subsurface TIDAK termasuk.
    # Ditentukan eksplisit, bukan disimpulkan: subsurface JUGA
    # "render is not surface" tetapi TIDAK boleh disalin ke induknya.
    _display_state["render_is_buffer"] = bool(
        mode != "native" and render is not surface
        and _display_state.get("panel") is None)
    _refresh_display_metrics(surface)

    if IS_ANDROID:
        enable_immersive_mode()
        keep_screen_on(True)

    print("[DISPLAY] mode=%s window=%s render=%s scale=%.3f"
          % (mode, _display_state["window_size"], render.get_size(),
             _display_state["scale"]))
    return render


def _refresh_display_metrics(surface):
    """Hitung skala & offset letterbox dari ukuran jendela nyata."""
    try:
        win_w, win_h = pygame.display.get_window_size()
    except Exception:
        win_w, win_h = surface.get_size()

    scale = min(win_w / LOGICAL_WIDTH, win_h / LOGICAL_HEIGHT)
    off_x = (win_w - LOGICAL_WIDTH * scale) * 0.5
    off_y = (win_h - LOGICAL_HEIGHT * scale) * 0.5

    _display_state["surface"] = surface
    _display_state["window_size"] = (win_w, win_h)
    _display_state["scale"] = scale
    _display_state["offset"] = (off_x, off_y)


def get_render_surface():
    return _display_state["render"]


def get_full_surface():
    """Permukaan display seutuhnya (termasuk panel samping)."""
    return _display_state.get("full") or _display_state["render"]


def get_game_offset():
    return _display_state.get("game_offset", (0, 0))


def get_panel_rect():
    """Rect panel kanan pada permukaan penuh, atau None kalau tidak ada."""
    return _display_state.get("panel")


def panel_popup_pos(w, h, atas=12):
    """
    Posisi popup di dalam panel kanan, atau None kalau tidak muat.

    Dipakai popup upgrade/build supaya tidak lagi menutupi peta.
    Kalau layar terlalu sempit (mis. tablet 4:3), kembalikan None dan
    popup memakai posisi lamanya - jadi perangkat apa pun tetap jalan.
    """
    p = _display_state.get("panel")
    if p is None or w > p.width - 8:
        return None
    x = p.x + (p.width - w) // 2
    y = max(atas, min(p.height - h - 12, (p.height - h) // 2))
    return (x, y)


# ═══ PEMBAGIAN ZONA PANEL KANAN ═══
# Panel dibagi jadi empat jalur tetap supaya isinya tidak pernah
# saling menimpa. Angkanya relatif terhadap sisi atas panel:
#
#     0 ..  76   tombol JEDA
#    84 .. 176   STATUS (emas, level, wave)
#   186 .. 346   daftar HERO (maksimal 3 baris)
#   356 .. 521   popup terpilih (panel upgrade hero, 165 px)
#   530 .. 720   notifikasi + umpan pembunuhan
#
# Dulu popup ditempel ke sisi bawah panel dan menimpa umpan
# pembunuhan - terlihat sebagai potongan teks yang muncul dari balik
# panel upgrade.
ZONA_POPUP_Y = 356
ZONA_BAWAH_H = 190


def panel_pos_bawah(w, h, sisakan=None):
    """
    Posisi popup di jalur khusus popup (lihat pembagian zona di atas).

    Namanya tetap `panel_pos_bawah` supaya pemanggil lama tidak perlu
    diubah, tetapi posisinya kini SLOT TETAP, bukan menempel ke dasar
    panel.
    """
    p = _display_state.get("panel")
    if p is None or w > p.width - 8:
        return None
    x = p.x + (p.width - w) // 2
    y = p.y + ZONA_POPUP_Y
    # kalau panelnya pendek, dorong ke atas seperlunya
    if y + h > p.bottom - ZONA_BAWAH_H:
        y = max(p.y + 8, p.bottom - ZONA_BAWAH_H - h)
    return (x, y)


def get_mode():
    return _display_state["mode"]


def present():
    """Tampilkan frame. Ganti semua pemanggilan pygame.display.flip()."""
    if _display_state["mode"] == "native":
        src = _display_state["render"]
        dst = _display_state["surface"]
        scale = _display_state["scale"]
        off = _display_state["offset"]
        tw = max(1, int(LOGICAL_WIDTH * scale))
        th = max(1, int(LOGICAL_HEIGHT * scale))

        buf = _display_state.get("scale_buf")
        if buf is None or buf.get_size() != (tw, th):
            buf = pygame.Surface((tw, th)).convert()
            _display_state["scale_buf"] = buf
            dst.fill((0, 0, 0))
        pygame.transform.scale(src, (tw, th), buf)
        dst.blit(buf, (int(off[0]), int(off[1])))
    elif _display_state.get("render_is_buffer"):
        # Mode scaled_* dengan buffer render TERPISAH di RAM
        # (dipakai jalur cepat alpha): salin 1:1 ke permukaan layar,
        # SDL yang menskalakan saat flip.
        #
        # PENTING: syaratnya harus penanda eksplisit, bukan
        # `src is not dst`. Saat panel samping aktif, render adalah
        # SUBSURFACE dari layar - menyalinnya ke induknya sendiri
        # memicu "Surfaces must not be locked during blit".
        src = _display_state["render"]
        dst = _display_state["surface"]
        if src is not None and dst is not None and src is not dst:
            dst.blit(src, (0, 0))
    pygame.display.flip()


def pointer_to_logical(pos):
    """
    Koordinat penunjuk (mouse / sentuh sintesis) -> koordinat logis.

    Mode scaled_* : SDL SUDAH menerjemahkannya -> kembalikan apa adanya.
    Mode native   : koordinatnya piksel jendela -> perlu dipetakan.
    """
    if _display_state["mode"] == "native":
        return window_to_logical(pos[0], pos[1])
    # Mode scaled_*: SDL sudah menerjemahkan ke koordinat permukaan
    # display. Kalau permukaan itu lebih lebar dari area main (panel
    # samping aktif), offset area main harus dikurangi supaya
    # koordinatnya kembali ke ruang 1280x720 yang dipakai seluruh
    # kode game dan tombol HUD.
    # Area main rata kiri di (0,0), jadi koordinat game = koordinat
    # layar penuh. Panel kanan cukup dikenali dari x >= LOGICAL_WIDTH.
    return (float(pos[0]), float(pos[1]))


def window_to_logical(x, y):
    """
    Konversi koordinat piksel jendela -> koordinat logis 1280x720.

    Dipakai HANYA untuk event FINGER (koordinatnya ternormalisasi
    dan TIDAK ikut ditranslasi pygame.SCALED). Event mouse hasil
    sintesis SDL sudah otomatis dalam koordinat logis.
    """
    scale = _display_state["scale"] or 1.0
    off_x, off_y = _display_state["offset"]
    return ((x - off_x) / scale, (y - off_y) / scale)


def finger_to_logical(fx, fy):
    """Event FINGER memberi x,y ternormalisasi 0..1 terhadap jendela."""
    win_w, win_h = _display_state["window_size"]
    return window_to_logical(fx * win_w, fy * win_h)


def get_scale():
    return _display_state["scale"]


def get_window_size():
    return _display_state["window_size"]


# ═══════════════════════════════════════════════════════
# SAFE AREA (poni / punch hole / gesture bar)
# ═══════════════════════════════════════════════════════
_SAFE_MARGIN_LOGICAL = 28  # px logis di kiri-kanan saat fullscreen HP


def get_safe_area():
    """
    Rect (x, y, w, h) dalam koordinat logis yang aman dari poni
    dan gesture bar. Taruh tombol HUD di dalam rect ini.
    """
    if not TOUCH_MODE:
        return pygame.Rect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)
    m = _SAFE_MARGIN_LOGICAL
    return pygame.Rect(m, 10, LOGICAL_WIDTH - 2 * m, LOGICAL_HEIGHT - 20)


# ═══════════════════════════════════════════════════════
# PENYIMPANAN (save file harus di folder privat app)
# ═══════════════════════════════════════════════════════
def get_writable_dir():
    """
    Folder tempat menyimpan save game.
    Android : /data/data/<package>/files  (selalu bisa ditulis)
    Desktop : folder game
    """
    if IS_ANDROID:
        path = os.environ.get("ANDROID_PRIVATE") or os.environ.get(
            "ANDROID_APP_PATH")
        if path:
            return path
        return os.path.expanduser("~")
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
