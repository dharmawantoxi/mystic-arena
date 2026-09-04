# ================================
# mobile/perf.py
# Optimasi performa lintas-file TANPA mengubah 60.000 baris kode lama.
#
# Isinya 4 hal:
#   1. install_font_cache()  - cache objek Font + cache hasil .render()
#   2. SurfacePool           - pakai ulang Surface(SRCALPHA) sementara
#   3. Quality               - preset kualitas (LOW/MEDIUM/HIGH) + auto
#   4. FrameTimer            - ukur ms update vs draw untuk overlay debug
#
# Kenapa ini penting di Android:
#   - CPU HP ~3-5x lebih lambat dari PC untuk kode Python murni.
#   - Game ini menggambar SEMUA sprite secara vektor tiap frame.
#   - Profil di PC menunjukkan 2 pemborosan besar:
#       * pygame.font.Font(None, 18) dibuat ULANG tiap frame
#         (buka file font dari disk 4x per frame!)
#       * font.render() teks statis dipanggil ulang tiap frame
#     Keduanya hilang total dengan install_font_cache().
# ================================

import gc
import time
from collections import OrderedDict

import pygame

# ═══════════════════════════════════════════════════════
# 1. CACHE FONT + CACHE TEKS
# ═══════════════════════════════════════════════════════

_ORIG_FONT_CLASS = pygame.font.Font
_ORIG_SYSFONT = pygame.font.SysFont

_font_instances = {}
_TEXT_CACHE_LIMIT = 1500

_stats = {
    "font_created": 0,
    "font_reused": 0,
    "text_rendered": 0,
    "text_cached": 0,
    "surf_pool_hit": 0,
    "surf_pool_new": 0,
}


class CachedFont(_ORIG_FONT_CLASS):
    """Font dengan cache hasil render. Drop-in, API sama persis."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text_cache = OrderedDict()

    def render(self, text, antialias=True, color=(255, 255, 255),
               background=None, **kwargs):
        # Argumen tak biasa (wraplength dsb.) -> lewati cache, biar aman
        if kwargs:
            _stats["text_rendered"] += 1
            return super().render(text, antialias, color, background,
                                  **kwargs)

        key = (text, bool(antialias),
               tuple(color) if not isinstance(color, (int, str)) else color,
               tuple(background) if isinstance(background, (tuple, list))
               else background,
               self.get_bold(), self.get_italic(), self.get_underline())

        cached = self._text_cache.get(key)
        if cached is not None:
            self._text_cache.move_to_end(key)
            _stats["text_cached"] += 1
            return cached

        surf = super().render(text, antialias, color, background)
        try:
            if pygame.display.get_init() and pygame.display.get_surface():
                if not Quality.use_colorkey_sprites:
                    surf = surf.convert_alpha()
                else:
                    # ══ PERUBAHAN TERBESAR UNTUK HP ══
                    # Diukur di Infinix X6880:
                    #   100 blit kecil ber-alpha  = 106,05 ms
                    #   100 blit kecil colorkey   =   0,41 ms  (257x)
                    # Setiap potong teks yang di-blit (angka damage,
                    # label, HUD, menu) kena biaya itu. Teks disimpan
                    # sebagai sprite colorkey; tepinya jadi keras,
                    # tetapi terbaca dan ratusan kali lebih murah.
                    surf = to_colorkey_sprite(surf)
        except Exception:
            pass
        _stats["text_rendered"] += 1

        self._text_cache[key] = surf
        if len(self._text_cache) > _TEXT_CACHE_LIMIT:
            self._text_cache.popitem(last=False)
        return surf


def _cached_font_factory(path_or_none, size=None, **kwargs):
    """Pengganti pygame.font.Font: objek Font dipakai ulang."""
    if size is None:
        size = 20
    try:
        size = int(size)
    except Exception:
        size = 20
    key = ("file", path_or_none, size, tuple(sorted(kwargs.items())))
    font = _font_instances.get(key)
    if font is None:
        font = CachedFont(path_or_none, size, **kwargs)
        _font_instances[key] = font
        _stats["font_created"] += 1
    else:
        _stats["font_reused"] += 1
    return font


def _cached_sysfont(name, size, bold=False, italic=False):
    """Pengganti pygame.font.SysFont, tetap mengembalikan CachedFont."""
    key = ("sys", name, int(size), bool(bold), bool(italic))
    font = _font_instances.get(key)
    if font is not None:
        _stats["font_reused"] += 1
        return font
    try:
        path = pygame.font.match_font(name, bold=bold, italic=italic)
    except Exception:
        path = None
    if path:
        font = CachedFont(path, int(size))
        font.set_bold(bold)
        font.set_italic(italic)
    else:
        font = _ORIG_SYSFONT(name, size, bold, italic)
    _font_instances[key] = font
    _stats["font_created"] += 1
    return font


_font_patch_installed = False


def install_font_cache():
    """
    Pasang cache font global. WAJIB dipanggil SEBELUM modul game
    di-import, karena sebagian modul membuat font saat import.
    """
    global _font_patch_installed
    if _font_patch_installed:
        return
    if not pygame.font.get_init():
        pygame.font.init()
    pygame.font.Font = _cached_font_factory
    pygame.font.SysFont = _cached_sysfont
    _font_patch_installed = True
    print("[PERF] Font cache aktif (Font + render di-cache).")


def clear_text_caches():
    """Kosongkan cache teks (dipanggil saat ganti level / memori sesak)."""
    for font in _font_instances.values():
        cache = getattr(font, "_text_cache", None)
        if cache is not None:
            cache.clear()
    gc.collect()


def font_cache_stats():
    return dict(_stats)


# ═══════════════════════════════════════════════════════
# 2. SURFACE POOL
#    Alokasi Surface(SRCALPHA) tiap frame = alokasi memori + GC.
#    Ada ~1.400 pemakaian SRCALPHA di kode ini.
# ═══════════════════════════════════════════════════════
class SurfacePool:
    """Pakai-ulang surface sementara berdasar ukuran."""

    def __init__(self, max_per_size=6):
        self._pool = {}
        self._max = max_per_size

    def get(self, width, height, clear=True):
        width = max(1, int(width))
        height = max(1, int(height))
        bucket = self._pool.get((width, height))
        if bucket:
            surf = bucket.pop()
            _stats["surf_pool_hit"] += 1
            if clear:
                surf.fill((0, 0, 0, 0))
            return surf
        _stats["surf_pool_new"] += 1
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        try:
            if pygame.display.get_init() and pygame.display.get_surface():
                surf = surf.convert_alpha()
        except Exception:
            pass
        return surf

    def release(self, surf):
        if surf is None:
            return
        key = surf.get_size()
        bucket = self._pool.setdefault(key, [])
        if len(bucket) < self._max:
            bucket.append(surf)

    def clear(self):
        self._pool.clear()


POOL = SurfacePool()


# ═══════════════════════════════════════════════════════
# 2b. OVERLAY WARNA SOLID (di-cache)
#     Pola "buat Surface layar penuh -> fill -> blit" muncul di
#     belasan tempat dan dijalankan TIAP FRAME. Surface-nya selalu
#     sama; yang berubah cuma alpha. Jadi cukup dibuat sekali.
# ═══════════════════════════════════════════════════════
_overlay_cache = {}
_OVERLAY_CACHE_MAX = 6      # surface layar penuh = 3,5 MB/entri!


def darken(target, alpha):
    """
    Gelapkan seluruh permukaan - setara blit persegi hitam beralpha,
    tapi TANPA surface tambahan.

    Diukur pada 1280x720:
        alokasi + fill + blit  : 1,10 ms
        blit surface di-cache  : 0,35 ms
        darken() (fill BLEND)  : 0,17 ms   <-- ini
    """
    a = max(0, min(255, int(alpha)))
    if a <= 0:
        return
    k = 255 - a
    target.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)


def flash(target, alpha, color=(255, 255, 255)):
    """Kilat terang seukuran layar tanpa surface tambahan (additive)."""
    a = max(0, min(255, int(alpha)))
    if a <= 0:
        return
    r, g, b = color[:3]
    target.fill((r * a // 255, g * a // 255, b * a // 255),
                special_flags=pygame.BLEND_RGB_ADD)


def solid_overlay(width, height, rgb, alpha=255):
    """
    Surface polos berwarna dengan alpha yang sudah dipanggang.
    Untuk area KECIL. Untuk overlay layar penuh pakai darken()/flash()
    - jauh lebih cepat dan tidak memakan RAM.
    """
    a = ((max(0, min(255, int(alpha))) + 4) // 8) * 8
    key = (int(width), int(height), tuple(rgb[:3]), a)
    surf = _overlay_cache.get(key)
    if surf is None:
        surf = pygame.Surface((int(width), int(height)), pygame.SRCALPHA)
        surf.fill((rgb[0], rgb[1], rgb[2], a))
        if len(_overlay_cache) >= _OVERLAY_CACHE_MAX:
            _overlay_cache.clear()
        _overlay_cache[key] = surf
    return surf


_static_cache = {}


def cached_render(key, width, height, draw_func):
    """
    Cache hasil gambar statis (vignette, gradien, dsb).

        surf = perf.cached_render(("vignette", w, h), w, h, gambar)
        surf.set_alpha(a)
        target.blit(surf, (0, 0))

    `draw_func(surface)` hanya dipanggil sekali per key.
    """
    surf = _static_cache.get(key)
    if surf is None:
        surf = pygame.Surface((int(width), int(height)), pygame.SRCALPHA)
        draw_func(surf)
        _static_cache[key] = surf
    return surf


def blit_overlay(dst, overlay, rect=None, pos=(0, 0)):
    """
    Blit overlay transparan HANYA pada kotak yang perlu.

    Blit alpha dihitung per piksel; membatasi areanya adalah cara
    paling ampuh mempercepatnya di HP. `rect` adalah kotak (dalam
    koordinat overlay) yang benar-benar berisi gambar.
    """
    if rect is None:
        dst.blit(overlay, pos)
        return
    rect = pygame.Rect(rect).clip(overlay.get_rect())
    if rect.width <= 0 or rect.height <= 0:
        return
    dst.blit(overlay, (pos[0] + rect.x, pos[1] + rect.y), rect)


# ═══════════════════════════════════════════════════════
# PENYERAGAM FORMAT SURFACE
#
# alphablit.c pygame-ce hanya memakai blitter SIMD/NEON kalau
# Rmask/Gmask/Bmask SUMBER sama persis dengan TUJUAN:
#
#     src->BytesPerPixel == 4 && dst->BytesPerPixel == 4 &&
#     src->Rmask == dst->Rmask && ... && pg_HasSSE_NEON()
#
# Kalau tidak cocok -> alphablit() generik per-piksel (lambat).
# Kode game membuat ~1.500 Surface(SRCALPHA) dengan format bawaan
# pygame, yang belum tentu sama dengan format layar Android.
#
# install_surface_format_fix() mengganti pygame.Surface dengan
# pabrik yang otomatis memakai mask layar untuk setiap permintaan
# SRCALPHA -> syarat SIMD terpenuhi tanpa mengubah satu pun
# pemanggilan di kode lama.
# ═══════════════════════════════════════════════════════
_ORIG_SURFACE = pygame.Surface
_matched_masks = None
_surface_patch_installed = False


def display_alpha_masks(screen=None):
    """(R, G, B, A) untuk surface alpha yang cocok dengan layar."""
    try:
        surf = screen or pygame.display.get_surface()
        if surf is None:
            return None
        r, g, b, a = surf.get_masks()
        if not a:
            # layar tanpa kanal alpha -> pakai byte sisa untuk alpha
            used = r | g | b
            a = (~used) & 0xFFFFFFFF
            if a == 0:
                a = 0xFF000000
        return (r, g, b, a)
    except Exception:
        return None


def matched_alpha_surface(width, height):
    """Surface SRCALPHA dengan format yang memicu jalur SIMD."""
    if _matched_masks:
        return _ORIG_SURFACE((int(width), int(height)), pygame.SRCALPHA,
                             32, _matched_masks)
    return _ORIG_SURFACE((int(width), int(height)), pygame.SRCALPHA)


def _surface_factory(size, flags=0, depth=0, masks=None):
    # Hanya permintaan SRCALPHA tanpa mask eksplisit yang diseragamkan.
    if (masks is None and _matched_masks
            and (flags & pygame.SRCALPHA) and depth in (0, 32)):
        return _ORIG_SURFACE(size, flags, 32, _matched_masks)
    if masks is not None:
        return _ORIG_SURFACE(size, flags, depth, masks)
    if depth:
        return _ORIG_SURFACE(size, flags, depth)
    return _ORIG_SURFACE(size, flags)


def install_surface_format_fix(screen=None):
    """
    Samakan format SEMUA Surface(SRCALPHA) dengan format layar.
    Dipanggil otomatis kalau benchmark menemukan mask tidak cocok.
    """
    global _matched_masks, _surface_patch_installed
    masks = display_alpha_masks(screen)
    if not masks:
        return False
    _matched_masks = masks
    if not _surface_patch_installed:
        pygame.Surface = _surface_factory
        _surface_patch_installed = True
    print("[PERF] Format surface diseragamkan ke mask layar %s "
          "-> syarat jalur SIMD/NEON terpenuhi" % (masks,))
    return True


COLORKEY = (255, 0, 255)

# ═══════════════════════════════════════════════════════
# ANGGARAN KONVERSI PER FRAME
#
# Mengubah sprite jadi colorkey = satu operasi per-piksel. Di HP uji
# ~256 ns/piksel, jadi sprite hero 100x140 (14.000 piksel) = 3,6 ms
# SEKALI konversi. Kalau posenya berubah terus, konversi berulang
# jadi LEBIH MAHAL daripada untungnya - persis yang terjadi di v19
# (entity 273 ms untuk 11 unit).
#
# Dua pengaman:
#   1. konversi hanya untuk sprite yang sudah dipakai >= 2 kali
#      (terbukti dipakai ulang)  -> lihat should_convert()
#   2. maksimal N konversi per frame
# ═══════════════════════════════════════════════════════
MAX_CONVERT_PER_FRAME = 2
_convert_budget = [MAX_CONVERT_PER_FRAME]
_convert_stats = {"done": 0, "skipped": 0}


def new_frame_budget():
    """Panggil sekali per frame (dari main loop)."""
    _convert_budget[0] = MAX_CONVERT_PER_FRAME


def can_convert():
    """True kalau masih ada jatah konversi di frame ini."""
    if _convert_budget[0] > 0:
        _convert_budget[0] -= 1
        _convert_stats["done"] += 1
        return True
    _convert_stats["skipped"] += 1
    return False


def convert_stats():
    return dict(_convert_stats)


def to_colorkey_sprite(surf, bg=(0, 0, 0)):
    """
    Ubah surface ber-alpha menjadi surface COLORKEY (tanpa kanal alpha).

    Kenapa: di ARM tanpa SIMD, blit per-piksel-alpha ~244 ns/piksel,
    sedangkan blit colorkey memakai jalur cepat (RLE) yang ~25x lebih
    murah. Piksel semi-transparan dikomposit ke `bg` lebih dulu, jadi
    tepiannya jadi keras - dapat diterima untuk gaya pixel-art dan
    hanya dipakai di perangkat lambat.
    """
    w, h = surf.get_size()
    out = None
    try:
        # Jalur terbaik: ambang alpha lewat mask (kode C, cepat).
        # Piksel dengan alpha <= 127 (bayangan lembut, tepi halus)
        # menjadi transparan penuh; sisanya disalin apa adanya.
        mask = pygame.mask.from_surface(surf, 127)
        out = mask.to_surface(setsurface=surf, unsetcolor=COLORKEY)
    except Exception:
        out = None
    if out is None:
        out = pygame.Surface((w, h))
        out.fill(COLORKEY)
        out.blit(surf, (0, 0))
    try:
        out = out.convert()
    except Exception:
        pass
    out.set_colorkey(COLORKEY, pygame.RLEACCEL)
    return out


def clear_static_caches():
    _static_cache.clear()
    _overlay_cache.clear()
    POOL.clear()


# ═══════════════════════════════════════════════════════
# 3. PRESET KUALITAS
#    Modul gambar bisa membaca flag ini untuk melewati efek berat.
#    Contoh pemakaian di kode gambar:
#        from mobile.perf import Quality
#        if Quality.particles:
#            ...gambar partikel...
# ═══════════════════════════════════════════════════════
LOW, MEDIUM, HIGH = "low", "medium", "high"

# ── Saklar anti-aliasing global ──────────────────────────
# pygame.draw.aacircle jauh lebih mahal daripada draw.circle dan
# dipakai puluhan kali per unit di 57 berkas renderer. Daripada
# mengedit semuanya, cukup tukar fungsinya saat kualitas LOW.
_ORIG_AACIRCLE = getattr(pygame.draw, "aacircle", None)


def _apply_aa_switch(use_aa):
    if _ORIG_AACIRCLE is None:
        return
    if use_aa:
        if pygame.draw.aacircle is not _ORIG_AACIRCLE:
            pygame.draw.aacircle = _ORIG_AACIRCLE
    else:
        if pygame.draw.aacircle is _ORIG_AACIRCLE:
            pygame.draw.aacircle = pygame.draw.circle


class _Quality:
    def __init__(self):
        self.level = HIGH
        # ══ PROPERTI PERANGKAT ══
        # Diukur SEKALI oleh apply_device_profile() dan TIDAK boleh
        # ditimpa oleh apply(); preset kualitas mengatur efek, bukan
        # kemampuan perangkat.
        self.cheap_alpha = True        # True = alpha blit murah (PC)
        # Sprite colorkey membuat tepi jadi KERAS (mask ambang 127),
        # jadi hanya dipakai kalau alpha benar-benar tak terjangkau.
        # Begitu jalur cepat SDL aktif, tepi lembut dikembalikan.
        self.use_colorkey_sprites = False
        self.max_alpha_px = 1_000_000
        self.colorkey_gain = 1.0       # colorkey vs alpha, hasil ukur
        self.sprite_cache = False      # cache sprite unit (colorkey)
        self._particle_ratio = 1.0     # nilai dasar (tanpa beban combat)
        self.apply(HIGH)

    @property
    def particle_ratio(self):
        """Rasio partikel EFEKTIF = preset kualitas x beban combat.

        Beban combat dikelola oleh governor (set_fx_load / fx_load):
        saat banyak hero bertarung sekaligus, semua modul FX otomatis
        menurunkan jumlah partikel tanpa perlu diubah satu per satu.
        """
        return self._particle_ratio * fx_load()

    @particle_ratio.setter
    def particle_ratio(self, value):
        self._particle_ratio = float(value)

    def apply(self, level):
        self.level = level
        low = level == LOW
        med = level == MEDIUM

        # Efek yang boleh dimatikan tanpa merusak gameplay
        self.particles = not low
        self.particle_ratio = 0.35 if low else (0.65 if med else 1.0)
        self.fog = not low
        self.shadows = True
        self.soft_shadows = not (low or med)
        self.glow = not low
        self.screen_shake = True
        self.aa_circles = not low          # pakai draw.circle biasa saat LOW
        # Cache sprite minion: SUDAH DIUKUR TERNYATA LEBIH LAMBAT
        # (60 minion: 0,66 ms tanpa cache vs 1,07 ms dengan cache),
        # karena renderer minion memang sudah murah sementara alokasi
        # + blit surface tambahan justru mahal. Biarkan False.
        # Detail: mobile/spritecache.py
        # ── ALPHA BLIT MAHAL? ──
        # Diisi otomatis oleh apply_device_profile() dari hasil
        # benchmark di HP. Kalau True: JANGAN pernah blit surface
        # ber-alpha seukuran layar; pakai darken()/fill() atau
        # gambar langsung tanpa transparansi.

        self.floating_decor = not low
        self.max_damage_numbers = 8 if low else (16 if med else 32)
        self.target_fps = 30 if low else 60

        _apply_aa_switch(self.aa_circles)

    def __repr__(self):
        return "<Quality %s>" % self.level


Quality = _Quality()


# ═══════════════════════════════════════════════════════
# GOVERNOR BEBAN FX COMBAT (anti slow-motion saat banyak hero)
#
# Setiap hero "live FX" (heroes/*_fx.py) menggambar partikel, trail,
# ring, dan glow sendiri tiap frame. Ketika banyak hero bertarung
# sekaligus, biaya draw naik LINEAR dengan jumlah hero dan alpha-blit
# kecil menumpuk -> FPS ambruk -> loop ber-clock.tick() melambat dan
# game terasa slow-motion. Selain itu glow/ring additive yang menumpuk
# menutupi sprite hero.
#
# Governor menghitung "beban" (jumlah hero FX yang aktif) sekali per
# frame, lalu menurunkan intensitas FX global supaya total pekerjaan
# tetap terbatas. fx_load() dibaca oleh Quality.particle_ratio, jadi
# SEMUA modul FX ikut menyesuaikan tanpa diubah satu pun.
# ═══════════════════════════════════════════════════════
_FX_LOAD = 1.0
_FX_LOAD_SMOOTH = 0.35     # seberapa cepat beban menyusul perubahan
_FX_BASE_HEROES = 1.5      # jumlah hero FX yang masih boleh intensitas penuh
_FX_LOAD_MIN = 0.20        # lantai intensitas (FX tidak pernah mati total)
_FX_LOAD_EXP = 1.1         # makin besar = turun lebih agresif saat 3+ hero


def set_fx_load(n_active):
    """Panggil SEKALI per frame dengan jumlah hero FX yang sedang aktif.

    Semakin banyak hero yang aktif -> intensitas FX global diturunkan
    (partikel lebih sedikit, lapisan FX diselingi antar-frame) supaya
    frame tetap murah dan FX tidak menumpuk menutupi hero.

    Dugaan lapangan: saat pemain meletakkan 5 hero starter (zephyr,
    grimjaw, kaizen, vex, sylara) sekaligus, governor lama (base 3,
    eksponen 0.5) hanya turun ke sekitar 0.78 — tidak cukup. Base 2 +
    eksponen 0.75 membuat 5 hero aktif turun ke sekitar 0.55, dan 8+ hero
    menyentuh lantai 0.22 tanpa pernah menghilangkan FX.
    """
    global _FX_LOAD
    try:
        n_active = max(0, int(n_active or 0))
    except Exception:
        n_active = 0
    if n_active <= _FX_BASE_HEROES:
        target = 1.0
    else:
        target = max(_FX_LOAD_MIN,
                     (_FX_BASE_HEROES / n_active) ** _FX_LOAD_EXP)
    _FX_LOAD += (target - _FX_LOAD) * _FX_LOAD_SMOOTH


def fx_load():
    """Faktor intensitas FX global (0..1). 1.0 = normal."""
    return _FX_LOAD


def reset_fx_load():
    """Kembalikan intensitas FX ke normal (ganti level / keluar match)."""
    global _FX_LOAD
    _FX_LOAD = 1.0


# ═══════════════════════════════════════════════════════
# PROFIL PERANGKAT DARI HASIL BENCHMARK
#
# Temuan lapangan (Infinix X6880 / Cortex-A53, Android 15):
#     blit layar penuh ber-alpha = 204 ms   (di PC 0,35 ms)
#     pygame.draw.circle 200x    = 1 ms     (normal)
# pygame-ce 2.4.1 tidak punya blitter NEON untuk ARM, jadi alpha
# blit jatuh ke loop C generik per-piksel: ~222 ns/piksel.
#
# Konsekuensinya SATU overlay layar penuh = 6 frame terlewat.
# Jadi kalau perangkat terdeteksi seperti ini, semua efek berbasis
# "surface transparan besar" harus dimatikan.
# ═══════════════════════════════════════════════════════
def apply_device_profile(bench):
    """Terima dict hasil diagnostics.run_benchmark(), sesuaikan Quality."""
    if not bench:
        return Quality.level
    full = bench.get("blit_penuh_alpha")
    if full is None:
        return Quality.level

    px = 1280 * 720
    ns_per_px = full * 1e6 / px

    if full > 30:            # >30 ms untuk satu layar penuh
        Quality.apply(LOW)
        Quality.cheap_alpha = False
        # berapa piksel alpha yang muat dalam 8 ms per frame
        Quality.max_alpha_px = max(20000, int(8.0 / (ns_per_px / 1e6)))
        print("[PERF] Alpha blit MAHAL di perangkat ini "
              "(%.0f ms layar penuh = %.0f ns/piksel)." % (full, ns_per_px))
        print("[PERF] -> mode hemat-alpha: overlay layar penuh, vignette, "
              "glow, dan aura dimatikan. Anggaran %d piksel alpha/frame."
              % Quality.max_alpha_px)
    else:
        Quality.cheap_alpha = True
        Quality.max_alpha_px = 1_000_000

    # ═══ JALUR CEPAT: alpha lewat blitter SDL ═══
    # Kalau BLEND_ALPHA_SDL2 terbukti minimal 2x lebih cepat daripada
    # alpha blit bawaan pygame, seluruh gambar dialihkan ke sana.
    # Selisih warnanya 3/255 (uji tools/test_fastblit.py) - tidak
    # terlihat, dan gaya grafik sama sekali tidak berubah.
    efektif = full           # biaya nyata satu layar penuh alpha, ms
    try:
        from mobile import fastblit
        a_layar = bench.get("alpha_COCOK_ke_layar") or full
        s2 = bench.get("SDL2alpha_ke_layar")
        if s2 and a_layar and s2 * 2.0 < a_layar:
            fastblit.aktifkan("%.0f ms -> %.0f ms untuk satu layar penuh "
                              "(%.0fx)" % (a_layar, s2, a_layar / s2))
            efektif = s2
        elif s2:
            print("[PERF] BLEND_ALPHA_SDL2 tidak membantu (%.1f vs %.1f ms)"
                  % (s2, a_layar))
    except Exception as exc:
        print("[PERF] gagal menilai jalur cepat: %s" % exc)

    # ═══ KEPUTUSAN MODE HEMAT (KOREKSI v23) ═══
    # v22 menyalakan seluruh efek begitu jalur cepat aktif. Itu SALAH
    # dan terukur di perangkat:
    #
    #     v21 hemat:ON   e.hero   2 ms (1 hero)
    #     v22 hemat:off  e.hero 294 ms (3 hero) = 98 ms per hero
    #
    # Penyebabnya bukan efeknya saja. `cheap_alpha` juga mengatur
    # kuantisasi kunci cache sprite hero (heroes/__init__.py:
    # `_q = 1 if cheap_alpha else 2`). Menyalakannya membuat jumlah
    # kunci berlipat, cache hero meleset terus, dan setiap meleset
    # berarti render penuh + get_bounding_rect + smoothscale.
    #
    # Jadi ambangnya sekarang berdasar ANGGARAN FRAME, bukan tebakan:
    # satu overlay layar penuh tidak boleh melebihi 5 ms (15% dari
    # frame 33 ms @30 FPS). Di HP uji jalur cepat memberi 14,9 ms -
    # jauh lebih baik dari 203 ms, tapi masih terlalu mahal untuk
    # menyalakan semua efek. Mode hemat tetap ON.
    ANGGARAN_OVERLAY_MS = 5.0
    Quality.cheap_alpha = efektif <= ANGGARAN_OVERLAY_MS
    ns_efektif = efektif * 1e6 / px
    Quality.max_alpha_px = max(20000, int(8.0 / (ns_efektif / 1e6)))
    print("[PERF] biaya alpha efektif %.1f ms/layar (%.0f ns/piksel) "
          "-> mode hemat %s, anggaran %d piksel alpha/frame"
          % (efektif, ns_efektif,
             "MATI" if Quality.cheap_alpha else "AKTIF",
             Quality.max_alpha_px))

    # ═══ TEPI LEMBUT DIKEMBALIKAN ═══
    # Konversi colorkey memakai mask ambang 127: piksel setengah
    # transparan dipaksa jadi penuh atau hilang, sehingga tepi sprite
    # dan teks menjadi bergerigi. Itu harga yang dulu terpaksa dibayar
    # karena alpha 257 ns/piksel.
    #
    # Dengan jalur cepat 16 ns/piksel, satu sprite hero 120x160
    # hanya 0,3 ms. Menghemat 0,29 ms per hero tidak sebanding dengan
    # merusak tepi gambar - apalagi grafik asli adalah prioritas.
    try:
        from mobile import fastblit
        _cepat = fastblit.AKTIF
    except Exception:
        _cepat = False
    Quality.use_colorkey_sprites = (not Quality.cheap_alpha) and not _cepat
    print("[PERF] sprite colorkey (tepi keras): %s"
          % ("DIPAKAI" if Quality.use_colorkey_sprites
             else "tidak - tepi lembut dipertahankan"))

    # Seberapa untung memakai sprite colorkey di perangkat ini?
    # (dihitung SETELAH apply() supaya tidak tertimpa)
    # Untung-rugi colorkey dihitung terhadap biaya alpha EFEKTIF
    # (yaitu lewat jalur cepat kalau aktif), bukan terhadap alpha
    # lama yang sudah tidak dipakai.
    a = bench.get("100x_kecil_SDL2alpha") or bench.get("100x_blit_kecil")
    ck = bench.get("100x_blit_kecil_colorkey")
    if a and ck and ck > 0:
        Quality.colorkey_gain = a / ck
        Quality.sprite_cache = (Quality.colorkey_gain >= 4.0
                                and not Quality.cheap_alpha)

        # ═══ CACHE MINION: MATIKAN KALAU JALUR CEPAT AKTIF ═══
        # Terukur di perangkat, bukan diperkirakan:
        #     v21 cache minion ON : e.minion 54 ms / 14 unit = 3,9 ms
        #     v22 cache minion off: e.minion  5 ms / 40 unit = 0,13 ms
        # Renderer minion memang sudah murah; alokasi surface + blit
        # tambahan dari cache justru lebih mahal daripada menggambar
        # ulang. Cache hero TETAP hidup (dikelola heroes/__init__.py)
        # karena di sana untungnya terbalik: 98 ms -> 2 ms per hero.
        try:
            from mobile import fastblit
            if fastblit.AKTIF:
                Quality.sprite_cache = False
                print("[PERF] cache sprite MINION dimatikan - terukur "
                      "lebih cepat tanpa cache saat jalur cepat aktif "
                      "(0,13 vs 3,9 ms per unit)")
        except Exception:
            pass
        print("[PERF] blit kecil: alpha %.2f ms vs colorkey %.2f ms "
              "(%.1fx) -> cache sprite unit %s"
              % (a, ck, Quality.colorkey_gain,
                 "AKTIF" if Quality.sprite_cache else "mati"))
    return Quality.level


def auto_detect_quality(is_android):
    """
    Tebakan awal kualitas. Di Android default MEDIUM; kalau RAM kecil
    atau CPU sedikit -> LOW. Pemain tetap bisa mengubah di menu Settings.
    """
    if not is_android:
        Quality.apply(HIGH)
        return Quality.level
    # Di Android mulai dari LOW: lebih baik 30 FPS stabil sejak
    # detik pertama, lalu pemain menaikkan sendiri di Settings,
    # daripada pengalaman pertama yang patah-patah.
    Quality.apply(LOW)
    return LOW


class AdaptiveQuality:
    """
    Turunkan kualitas otomatis kalau FPS rata-rata jeblok,
    naikkan lagi kalau lancar. Cegah 'lag spiral' di HP kentang.
    """

    def __init__(self, enabled=True, low_fps=26, high_fps=52, window=90):
        self.enabled = enabled
        self.low_fps = low_fps
        self.high_fps = high_fps
        self.window = window
        self._samples = []
        self._cooldown = 0

    def update(self, fps):
        if not self.enabled:
            return
        if self._cooldown > 0:
            self._cooldown -= 1
            return
        self._samples.append(fps)
        if len(self._samples) < self.window:
            return
        avg = sum(self._samples) / len(self._samples)
        self._samples.clear()

        if avg < self.low_fps and Quality.level != LOW:
            Quality.apply(LOW if Quality.level == MEDIUM else MEDIUM)
            self._cooldown = 180
            print("[PERF] FPS %.1f -> turunkan kualitas ke %s"
                  % (avg, Quality.level))
        elif avg > self.high_fps and Quality.level != HIGH:
            Quality.apply(HIGH if Quality.level == MEDIUM else MEDIUM)
            self._cooldown = 300
            print("[PERF] FPS %.1f -> naikkan kualitas ke %s"
                  % (avg, Quality.level))


# ═══════════════════════════════════════════════════════
# 4. PENGUKUR WAKTU FRAME
# ═══════════════════════════════════════════════════════
class PhaseTimer:
    """
    Pengukur fase yang sangat ringan (dipakai DI DALAM Game.draw).

        from mobile.perf import PHASES
        PHASES.mark("map")      # tutup fase sebelumnya, buka "map"
        ...
        PHASES.end()            # tutup fase terakhir

    Hasil rata-rata dibaca overlay debug -> kelihatan di layar HP
    bagian mana yang memakan waktu.
    """

    def __init__(self, smooth=0.9):
        self.avg = {}
        self.order = []
        self._name = None
        self._t0 = 0.0
        self.enabled = True

    def mark(self, name):
        if not self.enabled:
            return
        now = time.perf_counter()
        if self._name is not None:
            ms = (now - self._t0) * 1000.0
            prev = self.avg.get(self._name)
            self.avg[self._name] = ms if prev is None else prev * 0.9 + ms * 0.1
        if name not in self.order:
            self.order.append(name)
        self._name = name
        self._t0 = now

    def end(self):
        self.mark(None)
        self._name = None

    def top(self, n=6):
        items = sorted(self.avg.items(), key=lambda kv: -kv[1])[:n]
        return items


PHASES = PhaseTimer()


class FrameTimer:
    """Ukur ms untuk tiap fase frame: event / update / draw / flip."""

    def __init__(self, smooth=0.9):
        self.smooth = smooth
        self.marks = {}
        self.avg = {}
        self._t0 = None
        self._phase = None

    def start(self, phase):
        now = time.perf_counter()
        if self._phase is not None:
            self._close(now)
        self._phase = phase
        self._t0 = now

    def _close(self, now):
        ms = (now - self._t0) * 1000.0
        self.marks[self._phase] = ms
        prev = self.avg.get(self._phase, ms)
        self.avg[self._phase] = prev * self.smooth + ms * (1 - self.smooth)

    def stop(self):
        if self._phase is not None:
            self._close(time.perf_counter())
            self._phase = None

    def report(self):
        return dict(self.avg)


# ═══════════════════════════════════════════════════════
# PEMASANGAN SEKALIGUS
# ═══════════════════════════════════════════════════════
def install_all(is_android=False, adaptive=True):
    """Panggil sekali di awal main.py, sebelum import modul game."""
    install_font_cache()
    auto_detect_quality(is_android)
    print("[PERF] Preset kualitas: %s (target %d FPS)"
          % (Quality.level, Quality.target_fps))
    return AdaptiveQuality(enabled=adaptive)
