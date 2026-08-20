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
    "surface": None,
    "window_size": (LOGICAL_WIDTH, LOGICAL_HEIGHT),
    "scale": 1.0,
    "offset": (0, 0),
    "safe_area": (0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT),
}


def create_display(vsync=True):
    """
    Buat jendela/permukaan game.

    Android : fullscreen resolusi asli layar, tetapi surface yang
              dipakai game tetap 1280x720 berkat pygame.SCALED.
              -> Semua koordinat lama tetap valid.
              -> Scaling dilakukan GPU, bukan Python (cepat).
    Desktop : jendela 1280x720 biasa.
    """
    flags = pygame.SCALED

    if TOUCH_MODE:
        flags |= pygame.FULLSCREEN

    try:
        surface = pygame.display.set_mode(
            (LOGICAL_WIDTH, LOGICAL_HEIGHT), flags, vsync=1 if vsync else 0)
    except pygame.error:
        # vsync tidak didukung sebagian device -> ulangi tanpa vsync
        surface = pygame.display.set_mode(
            (LOGICAL_WIDTH, LOGICAL_HEIGHT), flags)

    _refresh_display_metrics(surface)

    if IS_ANDROID:
        enable_immersive_mode()
        keep_screen_on(True)

    return surface


def _refresh_display_metrics(surface):
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
