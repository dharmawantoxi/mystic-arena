# ============================================================================
# heroes/combat_feel.py
# ----------------------------------------------------------------------------
# BUS GAME-FEEL — SATU sumber kebenaran untuk hit-stop & screen-shake.
#
# Kenapa modul ini ada?
# ---------------------------------------------------------------------------
# Hit-stop dan screen-shake adalah state GLOBAL: kalau tiap karakter punya
# salinan sendiri, (a) hit-stop bisa menumpuk jadi patah-patah saat dua hero
# memukul di frame yang sama, (b) ``Game.update`` harus tahu semua modul FX
# yang pernah dibuat orang, dan (c) satu-satunya jalur shake yang benar ke
# kamera (``EffectManager``) jadi dobel.  Modul ini memegang tunggal itu;
# modul FX per karakter (``zephyr_fx``, ``gornak_fx``, ...) hanya
# MEMINTA efeknya lewat API di bawah.
#
# Aturan pakai
# ---------------------------------------------------------------------------
#   * ``Game.update()``           -> ``should_freeze_frame()`` tiap langkah
#   * modul FX karakter ``tick()``-> ``dt = combat_feel.tick()``  (bus yang
#     menghitung delta-time nyata DAN meredam shake; dipanggil berkali-kali
#     dalam satu frame tetap aman — lihat ``tick``)
#   * benturan / skill           -> ``hit_stop(s)`` + ``shake(a, b)``
#
# 100% prosedural: tidak ada aset eksternal, tidak ada pygame.image /
# pygame.mixer di sini.  Modul ini sengaja TIDAK menggambar apa pun.
# ============================================================================

import pygame

#: Master switch hit-stop global (dimatikan = game tak pernah beku).
HIT_STOP_ENABLED = True

#: Jendela hit-stop yang diizinkan (detik). Di luar ini dibuang.
HIT_STOP_MIN = 0.03
HIT_STOP_MAX = 0.08

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Batas delta-time yang diterima (anti lonjakan saat alt-tab / loading).
DT_MIN = 1.0 / 240.0
DT_MAX = 1.0 / 20.0


# ============================================================================
# 1. SCREEN SHAKE — trauma-based, meredam bertahap
# ============================================================================

class ScreenShake:
    """Guncangan layar dengan peluruhan berurutan (bukan sentakan konstan).

    ``amount`` = kekuatan efektif saat ini; makin lama makin kecil, jadi
    guncangan "mengendap" alih-alih berhenti mendadak.  Nilai final
    diteruskan ke ``EffectManager`` milik game agar kamera hanya digoyang
    satu kali per frame, apa pun jumlah karakter yang minta shake.
    """

    def __init__(self):
        self.shake_strength = 0.0
        self.shake_duration = 0.0
        self._max_duration = 0.0001
        self.enabled = True
        #: ambang minimum supaya layar tidak bergetar demi hal tak penting
        #: DITINGKATKAN 0.4->1.0 untuk kurangi noisy shake Q/W
        self.threshold = 1.0

    # ------------------------------------------------------------------
    def add(self, strength, duration=0.22):
        """Minta guncangan. Yang lebih kuat menang, yang lebih lama menang."""
        if not self.enabled:
            return
        strength = float(strength)
        duration = max(0.0, float(duration))
        if strength <= 0.0 or duration <= 0.0:
            return
        if strength <= self.shake_strength and \
                duration <= self.shake_duration:
            return
        self.shake_strength = max(self.shake_strength, strength)
        self.shake_duration = max(self.shake_duration, duration)
        self._max_duration = max(self._max_duration, self.shake_duration)

    # ------------------------------------------------------------------
    def update(self, dt):
        """Majukan peluruhan. Panggil SEKALI per frame (lihat ``tick``)."""
        if self.shake_duration <= 0.0:
            self.shake_strength = 0.0
            return
        self.shake_duration -= dt
        if self.shake_duration <= 0.0:
            self.shake_duration = 0.0
            self.shake_strength = 0.0
            self._max_duration = 0.0001

    # ------------------------------------------------------------------
    @property
    def amount(self):
        """Kekuatan efektif sekarang (sudah teredam sesuai sisa umur)."""
        if self.shake_duration <= 0.0 or self.shake_strength <= 0.0:
            return 0.0
        return self.shake_strength * (self.shake_duration
                                      / max(0.0001, self._max_duration))

    def offset(self):
        """(dx, dy) acak untuk overlay/debug; kamera resmi tetap EffectManager."""
        from random import uniform
        amt = self.amount
        if amt <= self.threshold:
            return (0, 0)
        return (uniform(-amt, amt), uniform(-amt, amt))

    def clear(self):
        self.shake_strength = 0.0
        self.shake_duration = 0.0
        self._max_duration = 0.0001


# ============================================================================
# 2. HIT STOP — pembekuan singkat supaya pukulan terasa berbobot
# ============================================================================

class HitStop:
    """Freeze 0.03 - 0.08 detik saat benturan berat mendarat.

    Simulasi game memakai langkah tetap 1/60 s, jadi durasi detik
    dikonversi ke jumlah LANGKAH SIMULASI yang dilewati.  Frame GAMBAR
    tetap jalan -> partikel & flash benturan tetap terlihat bergerak
    pelan (slow-mo), itu yang bikin pukulan terasa "nendang".
    """

    MIN_SECONDS = HIT_STOP_MIN
    MAX_SECONDS = HIT_STOP_MAX
    MAX_FRAMES = 5

    def __init__(self):
        self.frames = 0
        self.total = 0

    def trigger(self, seconds=0.045):
        """Minta hit-stop; durasi dijepit ke rentang aman."""
        if not HIT_STOP_ENABLED:
            return
        try:
            seconds = float(seconds)
        except (TypeError, ValueError):
            return
        seconds = max(self.MIN_SECONDS, min(self.MAX_SECONDS, seconds))
        frames = max(1, int(round(seconds / FIXED_DT)))
        frames = min(self.MAX_FRAMES, frames)
        if frames > self.frames:
            self.frames = frames
            self.total = frames

    def consume_frame(self):
        """True = langkah simulasi ini harus dibekukan."""
        if self.frames > 0:
            self.frames -= 1
            return True
        self.total = 0
        return False

    @property
    def active(self):
        return self.frames > 0

    @property
    def progress(self):
        """0 (baru) -> 1 (selesai). Dipakai overlay debug & slow-mo FX."""
        if self.total <= 0:
            return 1.0
        return 1.0 - (self.frames / float(self.total))

    def clear(self):
        self.frames = 0
        self.total = 0


# ============================================================================
# 3. SINGLETON GLOBAL
# ============================================================================

HITSTOP = HitStop()
SHAKE = ScreenShake()


# ============================================================================
# 4. API PUBLIK
# ============================================================================


def hit_stop(seconds=0.045):
    """Minta hit-stop global (dijepit ke 0.03 - 0.08 s di dalam)."""
    HITSTOP.trigger(seconds)


def shake(strength=5.0, duration=0.22, forward_to_camera=True):
    """Goyangkan layar - DIKURANGI untuk hilangkan noisy shake.

    ``forward_to_camera`` -> nilai yang sama diteruskan ke
    ``EffectManager.shake_screen`` milik game, karena kamera dunia
    dialah yang benar-benar meng-offset blit.  Setting
    ``screen_shake_enabled`` sudah ditegakkan di sana (via
    ``ScreenShake.enabled`` yang di-sync dari GameSettings), jadi tidak
    perlu dicek ulang di sini.
    """
    # HANYA shake >=4.0 (R / heavy) yang diizinkan, Q/W 2-3 diabaikan
    # Skala kekuatan 50% + durasi 70% untuk kurangi patah
    try:
        s = float(strength)
    except Exception:
        return
    if s < 4.0:
        return
    s = s * 0.5
    d = max(0.0, float(duration)) * 0.7
    SHAKE.add(s, d)
    if not forward_to_camera:
        return
    try:
        import __main__
        game = getattr(__main__, "game_instance", None)
        if game is not None and getattr(game, "effects", None) is not None:
            game.effects.shake_screen(s * 0.5)
    except Exception:
        pass


def should_freeze_frame():
    """Dipanggil ``Game.update``: True kalau langkah simulasi dibekukan."""
    if not HIT_STOP_ENABLED:
        HITSTOP.frames = 0
        return False
    return HITSTOP.consume_frame()


_FRAME_MS = None
_FRAME_DT = 0.0


def frame_dt():
    """Delta-time NYATA (detik) untuk frame gambar yang sedang berjalan.

    Bus yang menghitung dt dari jam SDL DAN meredam shake — keduanya
    SEKALI per frame.  Dipanggil beberapa karakter dalam satu frame
    (mis. Zephyr + Gornak) tetap benar: pemanggil kedua mendapat nilai
    dt yang sama, tanpa membuat shake meluruh dua kali cepat.

    ``0.0`` hanya muncul pada panggilan pertama (belum ada frame acuan);
    pemanggil boleh memakainya sebagai tanda "lewati update frame ini".
    """
    global _FRAME_MS, _FRAME_DT
    now = pygame.time.get_ticks()
    if _FRAME_MS is None:
        _FRAME_MS = now
        _FRAME_DT = 0.0
        return 0.0
    dt_ms = now - _FRAME_MS
    if dt_ms > 0:
        _FRAME_MS = now
        _FRAME_DT = max(DT_MIN, min(DT_MAX, dt_ms / 1000.0))
        SHAKE.update(_FRAME_DT)
    return _FRAME_DT


def fx_dt():
    """dt untuk FX karakter: diperlambat saat hit-stop (slow-motion).

    Saat beku, partikel TIDAK berhenti total — cuma melambat — supaya
    flash & serpihan benturan masih terlihat bergerak.  Itu yang membuat
    hit-stop terbaca sebagai "bobot", bukan "frame drop".
    """
    dt = frame_dt()
    if dt > 0.0 and HITSTOP.active:
        dt *= 0.18
    return dt


#: Nama lama tetap hidup (dipakai modul karakter & tooling).
tick = frame_dt


def amount():
    """Kekuatan shake efektif sekarang (untuk HUD/debug)."""
    return SHAKE.amount


def reset():
    """Kosongkan seluruh state game-feel (ganti level / keluar match)."""
    global _FRAME_MS, _FRAME_DT
    HITSTOP.clear()
    SHAKE.clear()
    _FRAME_MS = None
    _FRAME_DT = 0.0


def sync_settings():
    """Sinkronkan flag shake dari GameSettings (dipanggil Game saat init)."""
    try:
        from _core import GameSettings
        SHAKE.enabled = bool(GameSettings().screen_shake_enabled)
    except Exception:
        pass


def stats():
    """Ringkas state bus — dipakai overlay debug karakter."""
    return {
        "hitstop_frames": HITSTOP.frames,
        "hitstop_total": HITSTOP.total,
        "shake": SHAKE.amount,
    }
