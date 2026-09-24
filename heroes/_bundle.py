"""
heroes/_bundle.py - semua renderer hero

Gabungan dari 6 file:
  - grimjaw.py               namespace _NS_grimjaw
  - sylara.py                namespace _NS_sylara
  - kaizen.py                namespace _NS_kaizen
  - thorne.py                namespace _NS_thorne
  - vex.py                   namespace _NS_vex
  - zephyr.py                namespace _NS_zephyr

Modul dibungkus kelas `_NS_<nama>` supaya simbol bernama
sama tidak saling menimpa.
PALETTE, draw_boss, _draw_torso, _poly dan 24 simbol
lain ada di keenam file dengan isi BERBEDA.

File asli dihapus; nama submodul didaftarkan ke
sys.modules oleh __init__.py, jadi semua baris
`from heroes.<modul> import ...` tetap jalan.
"""
import math
import random
import pygame


# ═══════════════════════════════════════════════════════════════════
# SKILL OUTLINE HELPERS (dipakai semua namespace)
# -----------------------------------------------------------------
# Efek skill digambar langsung ke canvas tanpa outline, jadi garis/
# cincin tipis semi-transparan "tenggelam" di terrain terang. Helper
# di bawah menambahkan stroke gelap di belakang shape terang supaya
# tiap telegraph/indikator skill tetap tegas & jelas di semua map.
# ═══════════════════════════════════════════════════════════════════
_SKILL_OUTLINE = (6, 9, 18)


def _skill_outlined_line(surface, a, b, width, color, alpha):
    """Garis skill: stroke gelap di belakang + garis terang di atas."""
    sx, sy = int(a[0]), int(a[1])
    ex, ey = int(b[0]), int(b[1])
    if alpha <= 0:
        return
    pygame.draw.line(surface, (*_SKILL_OUTLINE, min(255, alpha)),
                     (sx, sy), (ex, ey), width + 2)
    pygame.draw.line(surface, (*color, min(255, alpha)),
                     (sx, sy), (ex, ey), width)


def _skill_outlined_circle(surface, center, radius, width, color, alpha):
    """Cincin skill: stroke gelap di belakang + cincin terang di atas."""
    if alpha <= 0:
        return
    cx, cy = int(center[0]), int(center[1])
    r = int(radius)
    if r <= 0:
        return
    pygame.draw.circle(surface, (*_SKILL_OUTLINE, min(255, alpha)),
                       (cx, cy), r + 1, max(1, width + 2))
    pygame.draw.circle(surface, (*color, min(255, alpha)),
                       (cx, cy), r, max(1, width))


# ====================================================================
# grimjaw.py
# ====================================================================
class _NS_grimjaw:
    """Namespace grimjaw - DOODLE MASTERWORK v4 (rewrite penuh renderer).

    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.

    GAYA BARU: DOODLE / SKETCHBOOK
    ------------------------------
    Renderer lama (pixel-art masterwork v2) diganti penuh dengan bahasa
    gambar "buku sketsa": karakter seolah digambar tangan dengan pulpen
    tinta + spidol + krayon di atas kertas.

    1. GARIS TINTA BERGOYANG (boiling lines). Semua outline digambar
       sebagai polyline yang di-jitter deterministik (hash) lalu
       digambar DUA pass dengan seed berbeda - garis kedua lebih tipis,
       lebih transparan, dan bergeser ~1 px: goresan pensil ganda khas
       sketch. Karena jitter adalah fungsi murni dari pose, sprite cache
       tetap valid; ganti fase animasi = garis "mendidih" seperti animasi
       tangan (12 fase/detik).
    2. ISI SPIDOL BERCELAH KERTAS (coloring-book gap). Fill poligon
       ditarik ke centroid ~1.5 px sebelum diwarnai, sehingga antara
       isi marker dan outline tinta selalu ada celah kertas tipis.
    3. ARSIRAN & SKRIBEL. Bayangan digambar sebagai arsiran pensil
       pendek sejajar + skribel loop (coretan "eee") untuk api dan
       volume; highlight = goresan gel-pen putih.
    4. API DOODLE. Mane api = lidah teardrop ber-outline tinta dengan
       skribel kuning di dalamnya + bara titik/garis; blade api =
       scimitar sketsa dengan lidah api di punggung bilah.
    5. KONTRAK LAMA DIPERTAHANKAN PENUH: geometri bilah
       (``_blade_angle`` / ``_blade_grip_local`` / ``_blade_tip_local``
       + konstanta timeline), controller serangan, jembatan lapisan hidup
       (``_live_module`` / ``_fx_live_owned`` / ``_FX_LIVE``), telegraph
       world-space (``_fx_scale`` cap 2.6 / ``_ring_r``), dan seluruh
       nama simbol publik - sehingga ``heroes/grimjaw_fx.py`` dan
       pipeline sprite-cache bekerja tanpa perubahan.
    """

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _SCRATCH_POOL = {}
    _OMNI_BUF = {}
    _GHOST_BUF = {}

    #: Overlay debug karakter (dipakai heroes/grimjaw_fx.py, default mati).
    DEBUG_CHARACTER = False

    # Durasi visual skill (frame @60fps) - renderer memakai ini untuk
    # progress FX, BUKAN timer gameplay (lihat hero_skills GrimjawSkills).
    SKILL_VISUAL_DURATION = {"q": 118, "w": 59, "e": 39, "r": 59}

    # ------------------------------------------------------------------
    # TIMELINE BASIC ATTACK (kontrak bersama rig + FX + test arah tebasan)
    # ------------------------------------------------------------------
    ATTACK_WINDUP_END = 0.25    # pedang selesai diangkat ke atas-belakang
    ATTACK_SWING_END = 0.62     # tebasan mendarat di depan-bawah
    # 0 = lurus ke bawah, positif = ke depan, negatif = ke belakang.
    # Tebasan SELALU berputar ke arah negatif: atas-belakang -> atas ->
    # depan-atas -> depan-bawah (tidak pernah "dari bawah ke atas").
    ATTACK_ARC_START = -2.30
    ATTACK_ARC_SWEEP = -3.05    # -2.30 + (-3.05) = -5.35 == +0.93 rad
    ATTACK_ARC_END = ATTACK_ARC_START + ATTACK_ARC_SWEEP

    # ------------------------------------------------------------------
    # PALETTE - "doodle sketchbook"
    # Spidol flat + tinta + kertas. Semua kunci lama dipertahankan
    # (heroes/grimjaw_fx.py menyinkronkan warnanya dari sini).
    # ------------------------------------------------------------------
    PALETTE = {
        # Tinta & kertas (material baru gaya doodle)
        "ink":             (20,  17,  23),
        "ink_soft":        (44,  38,  50),
        "paper":           (250, 246, 236),

        # Skin - spidol tan
        "skin_darkest":   (118,  82,  64),
        "skin_dark":      (154, 110,  82),
        "skin_mid":       (192, 146, 106),
        "skin_light":     (222, 182, 140),
        "skin_high":      (243, 214, 176),

        # Hair / mane - krayon api
        "hair_darkest":   (120,  42,  28),
        "hair_dark":      (170,  62,  26),
        "hair_mid":       (220, 108,  34),
        "hair_light":     (243, 156,  54),
        "hair_high":      (252, 198,  92),
        "hair_shine":     (255, 228, 136),

        # MASK - kertas putih digambar pulpen
        "mask_shadow":    (170, 162, 152),
        "mask_dark":      (200, 194, 184),
        "mask_mid":       (230, 226, 216),
        "mask_light":     (246, 244, 236),
        "mask_shine":     (255, 255, 252),
        "mask_line":      (88,  80,  90),

        # BLOOD STRIPES - spidol merah
        "blood_darkest":  (118,  26,  30),
        "blood_dark":     (156,  36,  40),
        "blood_mid":      (196,  48,  52),
        "blood_light":    (224,  76,  76),
        "blood_bright":   (242, 114, 110),

        # Armor leather - krayon cokelat
        "armor_darkest":  (56,  40,  28),
        "armor_dark":     (90,  62,  40),
        "armor_mid":      (126,  88,  52),
        "armor_light":    (166, 120,  72),
        "armor_high":     (202, 152,  96),

        # Red cloth (sash / loincloth / skirt)
        "red_darkest":    (108,  30,  34),
        "red_dark":       (144,  38,  42),
        "red_mid":        (188,  52,  56),
        "red_light":      (218,  76,  78),
        "red_bright":     (240, 110, 108),

        # Gold - spidol kuning
        "gold_darkest":   (118,  78,  24),
        "gold_dark":      (160, 112,  32),
        "gold_mid":       (204, 150,  48),
        "gold_light":     (234, 190,  78),
        "gold_shine":     (252, 226, 132),
        "gold_engrave":   (255, 210, 110),

        # Metal - pensil abu-abu dingin
        "metal_darkest":  (46,  46,  54),
        "metal_dark":     (76,  76,  86),
        "metal_mid":      (114, 114, 124),
        "metal_light":    (158, 158, 168),
        "metal_shine":    (218, 218, 226),

        # FIRE BLADE + FX api - spidol api CERAH (dipakai grimjaw_fx)
        "fire_darkest":   (112,  28,  10),
        "fire_dark":      (166,  48,  14),
        "fire_mid":       (230, 104,  22),
        "fire_light":     (248, 168,  48),
        "fire_hot":       (255, 214, 100),
        "fire_core":      (255, 246, 220),
        "ember":          (255, 178,  84),

        # Healing (green - Healing Ward)
        "heal_darkest":   (28,  74,  36),
        "heal_dark":      (52, 124,  62),
        "heal_mid":       (96, 190, 106),
        "heal_light":     (150, 232, 158),
        "heal_core":      (228, 252, 230),

        # Rage / omnislash (red-hot)
        "rage_dark":      (118,  28,  22),
        "rage_mid":       (186,  48,  34),
        "rage_light":     (238,  96,  56),
        "rage_bright":    (255, 148,  96),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (20,  17,  23),   # = tinta (asap FX jadi tinta)
        "white":          (255, 255, 255),
        "eye_glow":       (255,  64,  48),
        "dark_eye":       (30,  22,  34),
        # boot swatches (retained)
        "boot_darkest":   (38,  32,  36),
        "boot_dark":      (60,  48,  46),
        "boot_mid":       (96,  70,  56),
        "boot_light":     (136,  98,  72),
        "cloth_stitch":   (98,  32,  36),
    }

    #: Warna tinta default (dipakai semua primitif doodle).
    INK = PALETTE["ink"]

    # ------------------------------------------------------------------
    # Surface statis (bayangan / platform / totem) dibangun SEKALI lalu
    # dipakai ulang - tidak ada alokasi surface per frame.
    # ------------------------------------------------------------------
    _STATIC_SURFACES = {}

    def _static(key, builder):
        pool = _NS_grimjaw._STATIC_SURFACES
        surf = pool.get(key)
        if surf is None:
            if len(pool) > 96:            # jaga memori di perangkat kecil
                pool.clear()
            surf = builder()
            pool[key] = surf
        return surf

    def _scratch(w, h):
        """Surface sementara POOL (fill 0 lalu pakai)."""
        pool = _NS_grimjaw._SCRATCH_POOL
        key = (w, h)
        surf = pool.get(key)
        if surf is None:
            if len(pool) > 24:
                pool.clear()
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pool[key] = surf
        surf.fill((0, 0, 0, 0))
        return surf

    def _clamp(color):
        # Fast path: warna palet sudah int valid 0..255 (99% panggilan)
        n = len(color)
        if n == 3:
            r, g, b = color
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                if type(r) is int and type(g) is int and type(b) is int:
                    return color
                return (int(r), int(g), int(b))
        else:
            r, g, b, a = color
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255 \
                    and 0 <= a <= 255:
                if type(r) is int and type(g) is int and type(b) is int \
                        and type(a) is int:
                    return color
                return (int(r), int(g), int(b), int(a))
        if type(color) is tuple and len(color) == 3:
            _r, _g, _b = color
            if (type(_r) is int and type(_g) is int and type(_b) is int
                    and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
                return color
        return tuple(max(0, min(255, int(c))) for c in color)

    def _mix(a, b, t):
        """Blend linear dua warna (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_grimjaw._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache).

        Finalizer integer murah (tanpa sin/floor) - dipanggil ribuan kali
        per render sehingga biaya per panggilan menentukan budget frame.
        """
        x = (int(i) * 0x9E3779B1) & 0xFFFFFFFF
        x ^= x >> 15
        x = (x * 0x85EBCA6B) & 0xFFFFFFFF
        x ^= x >> 13
        return (x & 0xFFFF) / 65536.0

    def _rgba(color, alpha):
        c = _NS_grimjaw._clamp(color)[:3]
        return (c[0], c[1], c[2], max(0, min(255, int(alpha))))

    # ------------------------------------------------------------------
    # Primitif gambar klasik (kompatibilitas alias heroes.grimjaw)
    # ------------------------------------------------------------------
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grimjaw._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if _NS_grimjaw.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_grimjaw._clamp(color)
        pygame.draw.line(surface, color[:3],
                         (int(start[0]), int(start[1])),
                         (int(end[0]), int(end[1])), max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_grimjaw._clamp(color)
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_grimjaw._clamp(color)
        pygame.draw.ellipse(surface, color[:3], rect, width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_grimjaw._clamp(color)
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)

    def _dpoly(surface, color, alpha, points):
        """Polygon semi-transparan (alpha ditulis langsung - flat marker)."""
        if len(points) < 3 or alpha <= 0:
            return
        pygame.draw.polygon(surface, _NS_grimjaw._rgba(color, alpha), points)

    # ===================================================================
    # PRIMITIF DOODLE - inti gaya sketchbook
    # ===================================================================
    def _jit(seed, amp=1.0):
        """Jitter deterministik -amp..+amp dari hash."""
        return (_NS_grimjaw._hash01(seed) - 0.5) * 2.0 * amp

    def _seed_q(phase, salt=0):
        """Kuantisasi fase -> seed stabil (garis mendidih per fase cache)."""
        return int(phase * 3.0) * 131 + int(salt) * 977

    #: Cache array jitter: key (n, seed) -> array. Bucket fase animasi
    #: terbatas (12 idle / lebih kasar saat bertarung), jadi render
    #: berulang pada pose yang sama mengambil array dari cache tanpa
    #: menghitung hash sama sekali.
    _JIT_CACHE = {}

    def _jitters(n, seed, amp=0.82):
        """Array jitter [(normal, tangensial), ...] untuk n vertex.

        Dihitung SEKALI per bentuk lalu dipakai ulang oleh isi marker
        dan outline, serta di-cache lintas frame untuk bucket fase yang
        sama. Amplitudo sengaja kecil (perhalus ala khalros): goresan
        terasa tangan tanpa terlihat kasar.
        """
        key = (n, seed)
        got = _NS_grimjaw._JIT_CACHE.get(key)
        if got is not None:
            return got
        s7 = seed * 131
        s11 = seed * 197
        h01 = _NS_grimjaw._hash01
        two = 2.0 * amp
        tan = 2.0 * amp * 0.36
        out = []
        for i in range(n):
            out.append(((h01(s7 + i * 7) - 0.5) * two,
                        (h01(s11 + i * 11) - 0.5) * tan))
        if len(_NS_grimjaw._JIT_CACHE) > 2048:
            _NS_grimjaw._JIT_CACHE.clear()
        _NS_grimjaw._JIT_CACHE[key] = out
        return out

    def _apply_jitter(pts, js, closed, scale=1.0):
        """Terapkan array jitter tegak-lurus segmen pada polyline.

        ``closed=False`` menjaga endpoint persis supaya anggota badan
        selalu nyambung di sendi meski garis bergoyang.
        """
        n = len(pts)
        m = len(js)
        out = []
        rng = range(n) if closed else range(1, n - 1)
        if not closed and n:
            out.append(pts[0])
        for i in rng:
            x, y = pts[i]
            jn, jt = js[i % m]
            jn *= scale
            jt *= scale
            px, py = pts[i - 1]
            nx, ny = pts[(i + 1) % n]
            dx, dy = nx - px, ny - py
            L = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L, dy / L
            out.append((x - uy * jn + ux * jt, y + ux * jn + uy * jt))
        if not closed and n > 1:
            out.append(pts[n - 1])
        return out

    def _wobble_pts(pts, seed, amp=1.1):
        """Jitter interior polyline tegak-lurus segmen (endpoint persis)."""
        return _NS_grimjaw._apply_jitter(
            pts, _NS_grimjaw._jitters(len(pts), seed, amp), False)

    def _wobble_closed(pts, seed, amp=1.1):
        """Sama dengan _wobble_pts untuk loop tertutup (semua vertex)."""
        return _NS_grimjaw._apply_jitter(
            pts, _NS_grimjaw._jitters(len(pts), seed, amp), True)

    def _subdiv(a, b, step=10.0):
        """Pecah segmen jadi langkah ~step px (bahan wobble garis tinta)."""
        ax, ay = a
        bx, by = b
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / step))
        return [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n)
                for i in range(n + 1)]

    def _ipoints(pts):
        return [(int(x + 0.5), int(y + 0.5)) for x, y in pts]

    #: pygame-ce punya pygame.draw.aacircle - tepi lingkaran halus
    #: (resep "perhalus" khalros: titik/blob bulat tanpa gerigi).
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    def _aacircle(surface, color, center, radius, width=0):
        """Lingkaran anti-aliased; fallback draw.circle bila tak ada.

        Warna ber-alpha digambar lewat surface sementara (aacircle
        murni RGB), meniru idiom _NS_khalros._aacircle.
        """
        color = _NS_grimjaw._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            tmp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                 pygame.SRCALPHA)
            pygame.draw.circle(tmp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(tmp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_grimjaw.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy),
                                     radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _ink_stroke(surface, ink, a, b, width=2, seed=0, alpha=255,
                    passes=1, step=9.0):
        """GARIS TINTA doodle: satu goresan bersih ber-goyangan halus.

        Perhalus ala khalros: tidak ada lagi pass kedua yang melenceng
        (sketchy double stroke) - goresan tunggal lebih smooth; parameter
        ``passes`` dipertahankan demi kompatibilitas pemanggil lama.
        """
        if alpha <= 0:
            return
        pts = _NS_grimjaw._subdiv(a, b, step)
        js = _NS_grimjaw._jitters(len(pts), seed, 0.82)
        w1 = _NS_grimjaw._apply_jitter(pts, js, False)
        pygame.draw.lines(surface, _NS_grimjaw._rgba(ink, alpha), False,
                          _NS_grimjaw._ipoints(w1), max(1, width))

    def _ink_polyline(surface, ink, pts, width=2, seed=0, alpha=255,
                      close=False, passes=1):
        """Outline tinta untuk polyline banyak titik (wobble per vertex).

        Perhalus ala khalros: goresan tunggal; ``passes`` dipertahankan
        demi kompatibilitas pemanggil lama.
        """
        n = len(pts)
        if n < 2 or alpha <= 0:
            return
        js = _NS_grimjaw._jitters(n, seed, 0.82)
        w1 = _NS_grimjaw._apply_jitter(pts, js, close)
        pygame.draw.lines(surface, _NS_grimjaw._rgba(ink, alpha), close,
                          _NS_grimjaw._ipoints(w1), max(1, width))

    def _inset_pts(pts, gap=1.5):
        """Tarik semua vertex ke centroid sejauh `gap` px (celah kertas)."""
        n = float(len(pts))
        cx = sum(p[0] for p in pts) / n
        cy = sum(p[1] for p in pts) / n
        out = []
        for x, y in pts:
            dx, dy = x - cx, y - cy
            L = math.hypot(dx, dy) or 1.0
            k = max(0.0, L - gap) / L
            out.append((cx + dx * k, cy + dy * k))
        return out

    def _marker_poly(surface, fill, pts, seed=0, ink=None, width=2,
                     gap=1.5, alpha=255, fill_alpha=255, close=True,
                     passes=2):
        """Isi spidol + outline tinta dengan celah kertas di antaranya."""
        n = len(pts)
        if n < 3:
            return
        need_ink = ink is not None and alpha > 0
        js = _NS_grimjaw._jitters(n, seed, 1.05) if need_ink else None
        w1 = _NS_grimjaw._apply_jitter(pts, js, close) if js else pts
        if fill is not None and fill_alpha > 0:
            if gap > 0:
                fp = _NS_grimjaw._inset_pts(pts, gap)
                fp = _NS_grimjaw._apply_jitter(fp, js, close, 0.55) \
                    if js else fp
            else:
                fp = pts
            pygame.draw.polygon(surface,
                                _NS_grimjaw._rgba(fill, fill_alpha),
                                _NS_grimjaw._ipoints(fp))
        if need_ink:
            # Perhalus ala khalros: SATU goresan tebal yang bersih
            # (bukan sketsa ganda) - bobot tinta seperti spidol besar.
            pygame.draw.lines(surface, _NS_grimjaw._rgba(ink, alpha), close,
                              _NS_grimjaw._ipoints(w1),
                              width + 1 if width >= 2 else max(1, width))

    def _ink_ellipse(surface, fill, cx, cy, rx, ry, seed=0, ink=None,
                     width=2, rot=0.0, alpha=255, fill_alpha=255, n=11,
                     gap=1.4, passes=2, rwob=0.05):
        """Blob elips doodle: radius di-jitter hash lalu diberi tinta.

        Perhalus ala khalros: blob kecil yang nyaris bulat digambar
        sebagai lingkaran ANTI-ALIASED (`_aacircle`) - mata, kancing,
        medali, dan tetes jadi mulus tanpa gerigi poligon. Blob besar
        tetap wobble (karakter doodlenya ada di sana).
        """
        if rx <= 0.5 or ry <= 0.5:
            return
        if abs(rx - ry) <= 1.0 and abs(rot) < 1e-3 and rx <= 9.0:
            r = max(1, int(rx))
            if fill is not None and fill_alpha > 0:
                _NS_grimjaw._aacircle(surface,
                                      _NS_grimjaw._rgba(fill, fill_alpha),
                                      (cx, cy), r, 0)
            if ink is not None and width > 0 and alpha > 0:
                _NS_grimjaw._aacircle(surface,
                                      _NS_grimjaw._rgba(ink, alpha),
                                      (cx, cy), r + max(1, int(gap)),
                                      max(1, width))
            return
        if n < 11 and max(rx, ry) > 5.0:
            n = 11
        n = max(n, int(min(20, 9 + (rx + ry) * 0.45)))
        ca, sa = math.cos(rot), math.sin(rot)
        pts = []
        for i in range(n):
            t = i / n * math.tau
            w = 1.0 + _NS_grimjaw._jit(seed * 53 + i * 29, rwob)
            x = math.cos(t) * rx * w
            y = math.sin(t) * ry * w
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        _NS_grimjaw._marker_poly(surface, fill, pts, seed, ink, width,
                                 gap, alpha, fill_alpha, True, passes)

    def _tube(surface, a, b, width, fill, ink, seed, alpha=255,
              shade=None):
        """Tabung anggota badan: stroke tinta lebar di bawah + isi marker.

        Wobble isi dibuat lebih kecil dari wobble tinta sehingga tepi
        tinta selalu mengunci isi (tidak pernah bocor keluar).
        """
        if alpha <= 0:
            return
        pts = _NS_grimjaw._subdiv(a, b, 10.0)
        js = _NS_grimjaw._jitters(len(pts), seed, 0.72)
        w_ink = _NS_grimjaw._apply_jitter(pts, js, False)
        pygame.draw.lines(surface, _NS_grimjaw._rgba(ink, alpha), False,
                          _NS_grimjaw._ipoints(w_ink), width + 4)
        w_fill = _NS_grimjaw._apply_jitter(pts, js, False, 0.45)
        pygame.draw.lines(surface, _NS_grimjaw._rgba(fill, alpha), False,
                          _NS_grimjaw._ipoints(w_fill), width)
        if shade is not None:
            # garis arsir tipis di sisi bawah tabung
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L * (width * 0.22), dx / L * (width * 0.22)
            s0 = (a[0] + nx, a[1] + ny)
            s1 = (b[0] + nx, b[1] + ny)
            ws = _NS_grimjaw._apply_jitter(
                _NS_grimjaw._subdiv(s0, s1, 8.0), js, False, 0.6)
            pygame.draw.lines(surface, _NS_grimjaw._rgba(shade, alpha),
                              False, _NS_grimjaw._ipoints(ws),
                              max(1, width // 3))

    def _scribble(surface, color, cx, cy, rx, ry, seed, alpha=150,
                  loops=3, angle=0.0, width=2):
        """Coretan loop "eee" khas doodle - arsiran api / volume / asap."""
        if rx <= 0.5 or ry <= 0.5 or alpha <= 0:
            return
        ca, sa = math.cos(angle), math.sin(angle)
        ph = _NS_grimjaw._jit(seed, 2.2)
        s17, s29 = seed * 17, seed * 29
        h01 = _NS_grimjaw._hash01
        pts = []
        steps = 12
        for i in range(steps + 1):
            t = i / steps
            u = (t - 0.5) * 2.0
            v = math.sin(t * loops * math.tau + ph) * (1.0 - 0.35 * abs(u))
            x = u * rx + (h01(s17 + i) - 0.5) * 1.4
            y = v * ry + (h01(s29 + i) - 0.5) * 1.4
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        pygame.draw.lines(surface, _NS_grimjaw._rgba(color, alpha), False,
                          _NS_grimjaw._ipoints(pts), width)

    def _hatch_patch(surface, color, cx, cy, w, h, seed, alpha=110,
                     gap=4.0, angle=-0.7, width=1):
        """Arsiran pensil pendek sejajar (bayangan doodle)."""
        if alpha <= 0 or w < 3 or h < 3:
            return
        ca, sa = math.cos(angle), math.sin(angle)
        nca, nsa = math.cos(angle + math.pi / 2), math.sin(angle + math.pi / 2)
        rows = max(1, int(h // gap))
        for r in range(rows):
            t = (r + 0.5) * gap - h / 2.0
            L = w * (0.5 + 0.5 * _NS_grimjaw._hash01(seed * 31 + r * 7))
            off = _NS_grimjaw._jit(seed * 17 + r * 3, 1.1)
            x0 = cx + nca * (t + off) - ca * L * 0.5
            y0 = cy + nsa * (t + off) - sa * L * 0.5
            x1 = x0 + ca * L
            y1 = y0 + sa * L
            pygame.draw.line(surface, _NS_grimjaw._rgba(color, alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             width)

    def _doodle_star(surface, cx, cy, r, color, alpha, seed=0, spikes=6,
                     width=2, ink=None, rot=0.0):
        """Bintang kilau gambar-tangan: goresan radial ber-jitter."""
        if alpha <= 0 or r <= 1:
            return
        for i in range(spikes):
            a = rot + i * (math.tau / spikes) + \
                _NS_grimjaw._jit(seed * 13 + i * 7, 0.16)
            r0 = r * (0.15 + 0.12 * _NS_grimjaw._hash01(seed + i * 31))
            r1 = r * (0.72 + 0.42 * _NS_grimjaw._hash01(seed * 7 + i * 17))
            x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
            x1, y1 = cx + math.cos(a) * r1, cy + math.sin(a) * r1
            pygame.draw.line(surface, _NS_grimjaw._rgba(color, alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             width)
        if ink is not None:
            _NS_grimjaw._aacircle(surface, _NS_grimjaw._rgba(ink, alpha),
                                  (cx, cy), max(1, int(r * 0.14)))

    def _poof(surface, cx, cy, r, color, alpha, seed=0, puffs=4,
              width=2, ink=None, fill=None, fill_alpha=60):
        """Awan "poof" doodle: beberapa arc bergoyang membentuk ledakan."""
        if alpha <= 0 or r <= 1:
            return
        for k in range(puffs):
            a = k * (math.tau / puffs) + _NS_grimjaw._jit(seed + k * 5, 0.3)
            rr = r * (0.42 + 0.3 * _NS_grimjaw._hash01(seed * 3 + k * 11))
            px = cx + math.cos(a) * r * 0.55
            py = cy + math.sin(a) * r * 0.5
            _NS_grimjaw._ink_ellipse(surface, fill, px, py, rr, rr * 0.82,
                                     seed * 17 + k, ink, width,
                                     alpha=alpha, fill_alpha=fill_alpha,
                                     n=9, gap=0.0, passes=1)

    def _speed_ticks(surface, color, cx, cy, ang, count, length, alpha,
                     seed=0, width=2, spread=10.0):
        """Garis kecepatan pendek sejajar (membelakangi arah gerak)."""
        if alpha <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nca, nsa = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
        for i in range(count):
            t = (i - (count - 1) / 2.0) * spread
            L = length * (0.55 + 0.45 * _NS_grimjaw._hash01(seed + i * 13))
            j = _NS_grimjaw._jit(seed * 7 + i * 3, 1.5)
            x0 = cx + nca * (t + j)
            y0 = cy + nsa * (t + j)
            x1 = x0 - ca * L
            y1 = y0 - sa * L
            pygame.draw.line(surface, _NS_grimjaw._rgba(color, alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             width)

    def _flame_tongue(surface, base, direction, length, width, seed,
                      fill, inner, ink, alpha=255, bend=0.4,
                      scrib=True, gap=1.1):
        """Satu lidah api doodle: teardrop melengkung + skribel inti."""
        if alpha <= 0 or length < 3:
            return
        bx, by = base
        dx, dy = direction
        nx, ny = -dy, dx
        side = 1.0 if _NS_grimjaw._hash01(seed * 5 + 2) > 0.5 else -1.0
        bend_amt = bend * length * side
        tipx = bx + dx * length + nx * bend_amt
        tipy = by + dy * length + ny * bend_amt
        m1x = bx + dx * length * 0.52 + nx * bend_amt * 0.85
        m1y = by + dy * length * 0.52 + ny * bend_amt * 0.85
        left = (bx + nx * width * 0.5, by + ny * width * 0.5)
        right = (bx - nx * width * 0.5, by - ny * width * 0.5)
        lm = (m1x + nx * width * 0.30, m1y + ny * width * 0.30)
        rm = (m1x - nx * width * 0.30, m1y - ny * width * 0.30)
        pts = [left, lm, (tipx, tipy), rm, right]
        _NS_grimjaw._marker_poly(surface, fill, pts, seed, ink, 2, gap,
                                 alpha, alpha, True, 2 if length >= 18 else 1)
        if scrib and length >= 12:
            _NS_grimjaw._scribble(
                surface, inner,
                (bx + dx * length * 0.34 + nx * bend_amt * 0.45),
                (by + dy * length * 0.34 + ny * bend_amt * 0.45),
                length * 0.22, width * 0.42, seed * 3 + 1,
                min(255, int(alpha * 0.85)), 2, math.atan2(dy, dx), 2)

    def _ember_marks(surface, cx, cy, w, h, seed, color, alpha, count=4,
                     phase=0.0):
        """Bara api doodle naik: titik + garis kecil deterministik."""
        if alpha <= 0:
            return
        for i in range(count):
            t = _NS_grimjaw._hash01(seed * 31 + i * 7)
            rise = (_NS_grimjaw._hash01(seed * 17 + i * 13) +
                    phase * (0.35 + 0.3 * t)) % 1.0
            ex = cx + (t - 0.5) * w
            ey = cy - rise * h
            a = int(alpha * (1.0 - rise * 0.65))
            if _NS_grimjaw._hash01(seed * 11 + i * 3) > 0.5:
                pygame.draw.circle(surface, _NS_grimjaw._rgba(color, a),
                                   (round(ex), round(ey)), 1)
            else:
                pygame.draw.line(surface, _NS_grimjaw._rgba(color, a),
                                 (round(ex), round(ey)),
                                 (round(ex), round(ey - 3)), 1)

    # ===================================================================
    # KOSAKATA FX KELUARGA MASTERWORK (kontrak paritas + test)
    # Versi doodle: bentuk sama, goresan gambar-tangan.
    # ===================================================================
    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik DUNIA -> ruang gambar renderer (canvas cache).

        Saat dirender sebagai HERO (jalur sprite-cache), renderer
        dipanggil di (c, c) = pusat canvas, lalu canvas di-blit dengan
        skala _render_scale: 1 px canvas = _render_scale px dunia.
        Boss asli tidak punya _render_scale -> koordinat apa adanya.
        Hasil di-clamp ke dalam canvas supaya efek tidak terpotong.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(hero, x, y):
        target = getattr(hero, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_grimjaw._world_to_local(hero, x, y,
                                               target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(hero, "_render_scale", None)
        dist = 60 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(hero, "direction", 1)), int(y)

    def _fx_scale(hero):
        """Faktor skala efek skill (world-space), cap 2.6 (kontrak keluarga)."""
        scale = getattr(hero, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(hero, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam canvas."""
        scale = getattr(hero, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=2, rot=0.4,
                    width=2, seed=0):
        """Bintang kilau doodle (kosakata keluarga masterwork)."""
        _NS_grimjaw._doodle_star(surface, cx, cy, size, color, alpha,
                                 seed or int(rot * 97), spikes, width,
                                 rot=rot)

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3,
                 seed=0):
        """Chevron '>' doodle: dua goresan tinta ber-jitter."""
        if alpha <= 0 or size <= 1:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nca, nsa = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
        for s in (-1.0, 1.0):
            jx = nca * size * 0.5 * s + _NS_grimjaw._jit(seed + s, 0.8)
            jy = nsa * size * 0.5 * s + _NS_grimjaw._jit(seed * 3 + s, 0.8)
            a = (cx - ca * size * 0.4 + jx, cy - sa * size * 0.4 + jy)
            b = (cx + ca * size * 0.6 + jx * 0.4, cy + sa * size * 0.6 + jy * 0.4)
            _NS_grimjaw._ink_stroke(surface, _NS_grimjaw._rgba(color, alpha)
                                    [:3], a, b, width, seed + int(s * 7),
                                    alpha, passes=1)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     width=2, dashes=None, seed=0, ry=None, inner=False,
                     tick_len=None):
        """Cincin putus-putus gambar tangan (telegraph AOE).

        dashed=True (default): busur pendek selang-seling. Kalau
        ``tick_len`` diberikan, digambar sebagai deretan tick radial
        (marker angular ala masterwork) - dipakai marker Q yang harus
        tetap di radius DUNIA.
        """
        if alpha <= 0 or radius < 4:
            return
        if tick_len is not None:
            tick_len = max(4, int(tick_len))
            n = int(dashes or 14)
            # marker angular = LINGKARAN penuh (bukan elips gepeng), jadi
            # radius dunia tetap terverifikasi dari segala arah; ry hanya
            # dipakai kalau caller meminta gepeng secara eksplisit.
            ys = 1.0 if ry is None else float(ry) / float(max(1, radius))
            for i in range(n):
                a = i * (math.tau / n) + phase * 0.35
                pulse = 0.55 + 0.45 * math.sin(phase * 2.2 + i)
                r0 = radius - tick_len * pulse if not inner else radius
                r1 = radius if not inner else radius + tick_len * pulse
                x0 = cx + math.cos(a) * r0
                y0 = cy + math.sin(a) * r0 * ys
                x1 = cx + math.cos(a) * r1
                y1 = cy + math.sin(a) * r1 * ys
                pygame.draw.line(surface, _NS_grimjaw._rgba(color, alpha),
                                 (round(x0), round(y0)), (round(x1), round(y1)),
                                 width)
            return
        ry = radius * 0.62 if ry is None else ry
        dashes = int(dashes or 9)
        span = math.tau / dashes
        for i in range(dashes):
            a0 = i * span + phase * 0.8
            a1 = a0 + span * 0.58
            pts = []
            steps = 5
            for k in range(steps + 1):
                a = a0 + (a1 - a0) * k / steps
                wob = 1.0 + _NS_grimjaw._jit(seed * 13 + i * 29 + k, 0.05)
                pts.append((cx + math.cos(a) * radius * wob,
                            cy + math.sin(a) * ry * wob))
            pygame.draw.lines(surface, _NS_grimjaw._rgba(color, alpha),
                              False, _NS_grimjaw._ipoints(pts), width)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      segs=4, width=3):
        """Retakan tanah doodle: zigzag tinta dua lapis."""
        if alpha <= 0 or length < 6:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nca, nsa = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
        pts = [(cx, cy)]
        for i in range(1, segs + 1):
            t = i / float(segs)
            d = _NS_grimjaw._jit(seed * 17 + i * 7, length * 0.10)
            pts.append((cx + ca * length * t + nsa * d,
                        cy + sa * length * t - nca * d))
        cols = colors if isinstance(colors, (tuple, list)) else (colors,)
        for li, col in enumerate(cols):
            pygame.draw.lines(surface, _NS_grimjaw._rgba(col, alpha),
                              False, _NS_grimjaw._ipoints(pts),
                              max(1, width - li))

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bergerigi (hem kain / api).

        Tiap segmen di-sampling lalu diselang-selingi gigi keluar/masuk
        sepanjang normal - deterministik (hash), aman untuk cache.
        """
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by - ay), -(bx - ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            for j in range(n):
                t = (j + 0.5) / n
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 * _NS_grimjaw._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    # ------------------------------------------------------------------
    # Skill progress helpers
    # ------------------------------------------------------------------
    def _skill_progress(skill, timer):
        """Progress 0..1 skill FX dari countdown active_skill_timer."""
        dur = float(_NS_grimjaw.SKILL_VISUAL_DURATION.get(
            skill, max(1, timer or 1)))
        return max(0.0, min(1.0, 1.0 - float(timer) / dur))

    def _skill_steady(progress, tail=5.0, floor=.25):
        """Amplop fade akhir skill: plateau 1.0 lalu melandai ke floor."""
        return max(floor, min(1.0, (1.0 - progress) * tail + .3))

    # ===================================================================
    # STATE HELPERS (kontrak v3 - logika tidak berubah)
    # ===================================================================
    def _detect_moving(hero):
        if not hasattr(hero, "_gj_last_x"):
            hero._gj_last_x = hero.x
            hero._gj_last_y = hero.y
            return False
        dx = abs(hero.x - hero._gj_last_x)
        dy = abs(hero.y - hero._gj_last_y)
        hero._gj_last_x = hero.x
        hero._gj_last_y = hero.y
        moving = dx + dy > 0.3
        hero._moving_cached = moving
        return moving

    def _update_attack_anim(hero):
        """Track melee attack animation timeline.

        Serangan baru dideteksi dari timer NAIK (bukan dari nilai
        puncak) sehingga bekerja pada berapa pun langkah simulasi antar
        frame gambar. Progres diturunkan langsung dari timer simulasi.
        """
        cooldown = max(2, int(getattr(hero, "attack_cooldown", 40)))
        timer = int(getattr(hero, "timer", 0))
        previous = int(getattr(hero, "_gj_prev_timer", -1))
        active = bool(getattr(hero, "_gj_attack_active", False))

        trigger = previous >= 0 and timer > previous

        if trigger:
            hero._gj_attack_active = True
            hero._gj_crit_active = random.random() < 0.25
            active = True

        if active and timer <= 0:
            hero._gj_attack_active = False
            hero._gj_crit_active = False
            active = False

        hero._gj_prev_timer = timer

        hero._gj_attack_frame = max(0, cooldown - timer) if active else 0
        hero._gj_attack_progress = (
            min(1.0, hero._gj_attack_frame / max(1, cooldown - 1))
            if active else 0.0)

    # ------------------------------------------------------------------
    # LAPISAN FX HIDUP (heroes/grimjaw_fx.py)
    # ------------------------------------------------------------------
    _LIVE_MOD = None

    class _LiveFlag:
        """Penanda sederhana yang bisa di-set dari fungsi static."""
        __slots__ = ("v",)

        def __init__(self):
            self.v = False

    #: Dibaca rig: True = smear/impact ayunan sudah diambil alih lapisan
    #: hidup 60fps, jadi canvas tidak menggambarnya dua kali.
    _FX_LIVE = _LiveFlag()

    @staticmethod
    def _live_module():
        """Muat ``heroes.grimjaw_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_grimjaw
        if NS._LIVE_MOD is None:
            try:
                from heroes import grimjaw_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "GRIMJAW_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def _fx_live_owned(hero):
        """True kalau lapisan hidup mengambil alih FX unit ini."""
        try:
            mod = _NS_grimjaw._live_module()
            if mod is None:
                return False
            return bool(mod.owns(hero))
        except Exception:
            return False

    # ===================================================================
    # GEOMETRI BILAH (kontrak: rig + heroes/grimjaw_fx.blade_points)
    # Koordinat lokal: (0,0) = jangkar pinggul, x maju (facing), y ke
    # bawah, telapak +70. Tidak berubah dari v2 supaya trail lapisan
    # hidup tetap menempel PERSIS di pedang doodle.
    # ===================================================================
    def _blade_angle(phase, action, attack_progress=0.0, spin_phase=0.0):
        """Radian dari garis lurus-bawah: 0 = blade menunjuk ke bawah.

        Basic attack SELALU berputar ke arah negatif (mengecil): pedang
        diangkat ke atas-belakang kepala lalu menebas TURUN ke depan.
        """
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < _NS_grimjaw.ATTACK_WINDUP_END:
                t = ap / _NS_grimjaw.ATTACK_WINDUP_END
                t = 1.0 - (1.0 - t) ** 2
                return -0.55 - t * 1.75
            if ap < _NS_grimjaw.ATTACK_SWING_END:
                t = ((ap - _NS_grimjaw.ATTACK_WINDUP_END) /
                     (_NS_grimjaw.ATTACK_SWING_END -
                      _NS_grimjaw.ATTACK_WINDUP_END))
                t = t ** 1.35
                return (_NS_grimjaw.ATTACK_ARC_START +
                        _NS_grimjaw.ATTACK_ARC_SWEEP * t)
            if ap >= 1.0:
                return 0.12
            t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
                 (1.0 - _NS_grimjaw.ATTACK_SWING_END))
            t = t * t * (3.0 - 2.0 * t)
            return (_NS_grimjaw.ATTACK_ARC_END + 2.0 * math.pi) - t * 0.813
        if action == "spin":
            return spin_phase * 0.5 + math.sin(phase * 1.2) * 0.06
        if action == "walk":
            return 0.08 + math.sin(phase * 1.72) * 0.10
        return 0.12 + math.sin(phase * 0.5) * 0.05

    def _blade_grip_local(action, attack_progress=0.0, phase=0.0):
        """Posisi gagang blade (ruang lokal, forward = +x)."""
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < _NS_grimjaw.ATTACK_WINDUP_END:
                t = ap / _NS_grimjaw.ATTACK_WINDUP_END
                return (14 + int(6 * t), 1 - int(28 * t))
            if ap < _NS_grimjaw.ATTACK_SWING_END:
                t = ((ap - _NS_grimjaw.ATTACK_WINDUP_END) /
                     (_NS_grimjaw.ATTACK_SWING_END -
                      _NS_grimjaw.ATTACK_WINDUP_END))
                if t < 0.45:
                    u = t / 0.45
                    return (20 + int(16 * u), -27 + int(6 * u))
                u = (t - 0.45) / 0.55
                u = u * u
                return (36 + int(3 * u), -21 + int(30 * u))
            t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
                 (1.0 - _NS_grimjaw.ATTACK_SWING_END))
            return (39 - int(22 * t), 9 - int(6 * t))
        if action == "spin":
            return (26, -4)
        if action == "walk":
            return (17 + int(math.sin(phase * 1.72) * 3), 3)
        return (17, 3)

    def _blade_len(action):
        return 52 if action != "attack" else 58

    def _blade_len_ap(action, attack_progress=0.0):
        """Panjang bilah per progres serang (loop closure tanpa pop)."""
        if action != "attack":
            return 52
        ap = max(0.0, min(1.0, attack_progress))
        if ap < _NS_grimjaw.ATTACK_SWING_END:
            return 58
        t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
             (1.0 - _NS_grimjaw.ATTACK_SWING_END))
        return 58 - int(6 * t)

    def _front_arm_elbow(attack_progress=0.0):
        """Siku lengan pedang selama basic attack (ruang lokal)."""
        ap = max(0.0, min(1.0, attack_progress))
        if ap < _NS_grimjaw.ATTACK_WINDUP_END:
            t = ap / _NS_grimjaw.ATTACK_WINDUP_END
            return (11 + int(25 * t), 11 - int(28 * t))
        if ap < _NS_grimjaw.ATTACK_SWING_END:
            t = ((ap - _NS_grimjaw.ATTACK_WINDUP_END) /
                 (_NS_grimjaw.ATTACK_SWING_END -
                  _NS_grimjaw.ATTACK_WINDUP_END))
            if t < 0.45:
                u = t / 0.45
                return (36 - int(2 * u), -18 + int(15 * u))
            u = (t - 0.45) / 0.55
            return (35 + int(2 * u), -3 - int(3 * u))
        t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
             (1.0 - _NS_grimjaw.ATTACK_SWING_END))
        return (36 - int(24 * t), -6 + int(17 * t))

    def _blade_tip_local(phase, action, attack_progress=0.0, spin_phase=0.0):
        """Posisi ujung blade (ruang lokal) - anchor FX lapisan hidup."""
        a = _NS_grimjaw._blade_angle(phase, action, attack_progress, spin_phase)
        gx, gy = _NS_grimjaw._blade_grip_local(action, attack_progress, phase)
        L = _NS_grimjaw._blade_len_ap(action, attack_progress)
        return (int(gx + math.sin(a) * L), int(gy + math.cos(a) * L))

    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose badan.

        Keyframe: (progress, bob, lean, flare, tremble)
          0.00 rest / 0.12 wind-up / 0.26 tension / 0.42 strike /
          0.55 IMPACT / 0.72 follow / 1.00 recover
        """
        keys = (
            (0.00,  0,  1, 1.00, 0),
            (0.12,  4, -6, 1.12, 0),
            (0.26,  5, -7, 1.20, 1),
            (0.42, -2,  7, 1.10, 0),
            (0.55,  5,  9, 1.05, 0),
            (0.72,  1,  5, 1.02, 0),
            (1.00,  0,  1, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)
                bob = k0[1] + (k1[1] - k0[1]) * t
                lean = k0[2] + (k1[2] - k0[2]) * t
                flare = k0[3] + (k1[3] - k0[3]) * t
                tremble = 1 if (k0[4] and t < 0.9) else 0
                return {"bob": int(round(bob)), "lean": int(round(lean)),
                        "flare": flare, "tremble": tremble}
        return {"bob": 0, "lean": 1, "flare": 1.0, "tremble": 0}

    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_grimjaw(surface, hero, x, y):
        """Entry point for Hero.draw()."""
        pulse = float(getattr(hero, "pulse", 0.0))
        active_skill = getattr(hero, "active_skill", None)
        skill_timer = int(getattr(hero, "active_skill_timer", 0))
        moving = _NS_grimjaw._detect_moving(hero)
        _NS_grimjaw._update_attack_anim(hero)
        portrait_hd = bool(getattr(hero, "_portrait_hd", False))

        # ═══ LAPISAN FX HIDUP (heroes/grimjaw_fx.py) ═══
        # Penanda ``owned`` memberi tahu rig bahwa smear ayunan + impact
        # pop di-canvas sudah digantikan lapisan 60fps (tidak dobel).
        if not portrait_hd:
            try:
                mod = _NS_grimjaw._live_module()
                if mod is not None:
                    mod.attach(hero)
            except Exception:
                pass
        _NS_grimjaw._FX_LIVE.v = (not portrait_hd) and \
            _NS_grimjaw._fx_live_owned(hero)

        attacking = (
            getattr(hero, "_gj_attack_active", False)
            or getattr(hero, "timer", 0) > getattr(hero, "attack_cooldown", 40) - 15
        )

        # Q = Blade Fury, W = Healing Ward, E = Critical Strike, R = Omnislash
        is_blade_fury = active_skill == "q"
        is_healing_ward = active_skill == "w"
        is_crit_buff = active_skill == "e"
        is_omnislash = active_skill == "r"

        fury = is_blade_fury
        ward = is_healing_ward
        crit = is_crit_buff
        omni = is_omnislash

        # Portrait hanya berisi rig karakter (auto-crop tetap rapat).
        if not portrait_hd:
            # ---------- Background layers ----------
            if omni:
                _NS_grimjaw._draw_rage_aura(surface, x, y, pulse)
            else:
                _NS_grimjaw._draw_fire_aura(surface, x, y, pulse)
            _NS_grimjaw._draw_fire_platform(surface, x, y + 64, pulse, active_skill)

            # ---------- Skill ground effects (world-space) ----------
            if is_healing_ward:
                _NS_grimjaw._draw_healing_ward_ground(surface, hero, x, y, skill_timer, pulse)
            elif is_crit_buff:
                _NS_grimjaw._draw_crit_telegraph(surface, hero, x, y, skill_timer, pulse)
            elif is_omnislash:
                _NS_grimjaw._draw_omnislash_ground(surface, hero, x, y, skill_timer, pulse)
            elif is_blade_fury:
                _NS_grimjaw._draw_blade_fury_ground(surface, hero, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if is_blade_fury:
            _NS_grimjaw._draw_grimjaw_blade_fury(surface, hero, x, y, skill_timer, pulse)
        elif is_omnislash:
            _NS_grimjaw._draw_grimjaw_omnislash(surface, hero, x, y, skill_timer, pulse)
        elif attacking:
            _NS_grimjaw._draw_grimjaw_attack(surface, hero, x, y,
                                             crit=crit, omni=omni)
        elif moving:
            _NS_grimjaw._draw_grimjaw_walk(surface, hero, x, y,
                                           fury=fury, ward=ward, crit=crit,
                                           omni=omni)
        else:
            _NS_grimjaw._draw_grimjaw_idle(surface, hero, x, y,
                                           fury=fury, ward=ward, crit=crit,
                                           omni=omni)

        if not portrait_hd:
            # ---------- Skill foreground effects (world-space) ----------
            if is_blade_fury:
                _NS_grimjaw._draw_blade_fury_rings(surface, x, y + 20, pulse)
                _NS_grimjaw._draw_fire_particles_orbit(surface, x, y, pulse)
            if is_healing_ward:
                _NS_grimjaw._draw_healing_ward_totem(surface, hero, x, y, skill_timer, pulse)
                _NS_grimjaw._draw_heal_aura(surface, x, y, pulse)
            if is_crit_buff:
                _NS_grimjaw._draw_crit_steady(surface, hero, x, y, skill_timer, pulse)
            if is_omnislash:
                _NS_grimjaw._draw_omnislash_slashes(surface, hero, x, y, skill_timer, pulse)
                _NS_grimjaw._draw_omnislash_target(surface, hero, x, y, skill_timer, pulse)

    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_grimjaw_idle(surface, hero, x, y, fury=False, ward=False,
                           crit=False, omni=False):
        bob = int(math.sin(hero.pulse * 0.7) * 3)
        portrait = bool(getattr(hero, "_portrait_hd", False))
        if not portrait:
            _NS_grimjaw._draw_shadow(surface, x, y + 72)
            _NS_grimjaw._draw_fire_mist(surface, x, y + 56, hero.pulse)
        _NS_grimjaw._draw_grimjaw_body(surface, x, y + bob, hero.direction,
                                       hero.pulse, "idle", detail=portrait,
                                       fury=fury, ward=ward, crit=crit,
                                       omni=omni)

    def _draw_grimjaw_walk(surface, hero, x, y, fury=False, ward=False,
                           crit=False, omni=False):
        phase = hero.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 4)
        sway = int(math.sin(phase) * 3)
        portrait = bool(getattr(hero, "_portrait_hd", False))
        if not portrait:
            _NS_grimjaw._draw_shadow(surface, x + sway, y + 72)
            _NS_grimjaw._draw_fire_mist(surface, x + sway, y + 56, phase,
                                        trail=True, facing=hero.direction)
        _NS_grimjaw._draw_grimjaw_body(surface, x + sway, y - bob, hero.direction,
                                       phase, "walk", detail=portrait,
                                       fury=fury, ward=ward, crit=crit,
                                       omni=omni)

    def _draw_grimjaw_attack(surface, hero, x, y, crit=False, omni=False):
        progress = getattr(hero, "_gj_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        crit = crit or getattr(hero, "_gj_crit_active", False)
        portrait = bool(getattr(hero, "_portrait_hd", False))

        # Body lunge: ditarik ke belakang saat wind-up, menerjang maju,
        # puncak TEPAT saat pedang mendarat (ATTACK_SWING_END).
        if progress < _NS_grimjaw.ATTACK_WINDUP_END:
            lunge = int(-3.0 * (progress / _NS_grimjaw.ATTACK_WINDUP_END))
        elif progress < _NS_grimjaw.ATTACK_SWING_END:
            t = ((progress - _NS_grimjaw.ATTACK_WINDUP_END) /
                 (_NS_grimjaw.ATTACK_SWING_END -
                  _NS_grimjaw.ATTACK_WINDUP_END))
            lunge = int(-3.0 + 10.0 * (t ** 1.6))
        else:
            t = ((progress - _NS_grimjaw.ATTACK_SWING_END) /
                 (1.0 - _NS_grimjaw.ATTACK_SWING_END))
            lunge = int(7.0 * (1.0 - t))
        lunge *= hero.direction

        if not portrait:
            _NS_grimjaw._draw_shadow(surface, x + lunge, y + 72)
            _NS_grimjaw._draw_fire_mist(surface, x + lunge, y + 56,
                                        hero.pulse, intense=True)
        _NS_grimjaw._draw_grimjaw_body(surface, x + lunge, y, hero.direction,
                                       hero.pulse, "attack", progress,
                                       detail=portrait, crit=crit, omni=omni)

        # FX tebasan in-canvas (FALLBACK) - dilompati saat lapisan hidup
        # (heroes/grimjaw_fx.py) mengambil alih unit ini.
        if not portrait and not _NS_grimjaw._FX_LIVE.v:
            _NS_grimjaw._draw_fire_slash_arc(surface, x + lunge, y,
                                             hero.direction, progress, crit,
                                             hero.pulse)
            _NS_grimjaw._draw_impact_flash(surface, x + lunge, y,
                                           hero.direction, progress, crit)
            if crit and 0.56 < progress < 0.82:
                _NS_grimjaw._draw_critical_strike_burst(surface, x + lunge, y,
                                            hero.direction, progress)

    def _draw_grimjaw_blade_fury(surface, hero, x, y, timer, phase):
        """Blade Fury - berputar dengan cincin api doodle."""
        spin_phase = phase * 6
        bob = int(math.sin(spin_phase) * -1)
        # Arah hadap berganti cepat = ilusi berputar (rig sisi 2D).
        facing = 1 if int(spin_phase * 2) % 2 == 0 else -1

        _NS_grimjaw._draw_shadow(surface, x, y + 72)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 56, phase * 2, intense=True)
        _NS_grimjaw._draw_grimjaw_body(surface, x, y + bob, facing, phase, "spin",
                           spin_phase=spin_phase, fury=True)

    def _draw_grimjaw_omnislash(surface, hero, x, y, timer, phase):
        """Omnislash - teleport cepat dengan pose dramatis."""
        flicker_phase = phase * 8
        offset_x = int(math.sin(flicker_phase) * 4)
        offset_y = int(math.cos(flicker_phase * 1.3) * 3)

        _NS_grimjaw._draw_shadow(surface, x, y + 72)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 56, phase, intense=True)

        # Afterimage: badai tebasan Grimjaw yang bertumpuk.
        for i in range(4):
            ghost_alpha = 45 + i * 28
            gx = x - int(math.sin(flicker_phase - i * 0.5) * 24)
            gy = y + int(math.cos(flicker_phase - i * 0.5) * 8)
            ghost_ap = max(0.05, 0.85 - i * 0.22)
            _NS_grimjaw._draw_grimjaw_ghost(surface, gx, gy,
                                            hero.direction, phase,
                                            ghost_alpha, ghost_ap)

        # Badan utama (pose serang) di-cache per bucket fase.
        bucket = int(phase * 12) % 12
        key = ("omni_body", hero.direction, bucket)
        entry = _NS_grimjaw._OMNI_BUF.get(key)
        if entry is None:
            if len(_NS_grimjaw._OMNI_BUF) > 16:
                _NS_grimjaw._OMNI_BUF.clear()
            buf = pygame.Surface((240, 240), pygame.SRCALPHA)
            _NS_grimjaw._draw_grimjaw_body(buf, 120, 124, hero.direction,
                                           phase, "attack", 0.6,
                                           detail=False, omni=True)
            box = buf.get_bounding_rect(min_alpha=1)
            if box.width <= 0:
                box = pygame.Rect(0, 0, 240, 240)
            crop = buf.subsurface(box).copy()
            entry = (crop, box)
            _NS_grimjaw._OMNI_BUF[key] = entry
        crop, box = entry
        surface.blit(crop, (int(x + offset_x) - 120 + box.x,
                            int(y + offset_y) - 124 + box.y))

    def _draw_grimjaw_ghost(surface, cx, cy, facing, phase, alpha,
                            attack_progress=0.6):
        """Afterimage rig penuh untuk jejak omnislash (buffer di-cache)."""
        f = 1 if facing >= 0 else -1
        q = max(0.0, min(1.0, round(attack_progress / 0.05) * 0.05))
        key = (f, q)
        entry = _NS_grimjaw._GHOST_BUF.get(key)
        if entry is None:
            if len(_NS_grimjaw._GHOST_BUF) > 24:
                _NS_grimjaw._GHOST_BUF.clear()
            buf = pygame.Surface((220, 220), pygame.SRCALPHA)
            _NS_grimjaw._draw_grimjaw_elite(
                buf, 110, 118, f, 1.0, "attack", q, 0.0, False)
            box = buf.get_bounding_rect(min_alpha=1)
            if box.width <= 0:
                box = pygame.Rect(0, 0, 220, 220)
            crop = buf.subsurface(box).copy()
            entry = (crop, box)
            _NS_grimjaw._GHOST_BUF[key] = entry
        crop, box = entry
        crop.set_alpha(alpha)
        surface.blit(crop, (int(cx) - 110 + box.x, int(cy) - 118 + box.y))
        crop.set_alpha(255)

    def _draw_grimjaw_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0, spin_phase=0, detail=False,
                           fury=False, ward=False, crit=False, omni=False):
        """Wrapper historis - semua pose lewat satu rig doodle."""
        _NS_grimjaw._draw_grimjaw_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, spin_phase, detail,
            fury=fury, ward=ward, crit=crit, omni=omni)

    # ===================================================================
    # DOODLE RIG - satu rig berlapis, semua digambar "tangan"
    # Koordinat lokal: (0,0) = jangkar pinggul, x maju (facing), y ke
    # bawah, telapak +70 (sama dengan v2 supaya jangkar FX & ukuran
    # arena tidak berubah).
    # ===================================================================
    def _draw_grimjaw_elite(surface, cx, cy, facing, phase, action,
                            attack_progress=0.0, spin_phase=0.0,
                            detail=False, fury=False, ward=False,
                            crit=False, omni=False):
        """Rig doodle sketchbook - berserker flame-blade, 100% prosedural.

        Disiplin doodle:
          * outline tinta bergoyang 2 pass (double stroke);
          * isi spidol dengan celah kertas ke centroid;
          * bayangan = arsiran pensil + skribel loop, bukan ramp;
          * highlight = goresan gel-pen putih;
          * api = lidah teardrop ber-tinta + skribel kuning;
          * semua jitter deterministik (hash) -> aman untuk sprite cache.
        """
        p = _NS_grimjaw.PALETTE
        INK = p["ink"]
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        spin = action == "spin"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72) if walk else 0.0
        breath = math.sin(phase * 0.78)
        # Loop closure: frame akhir serang (ap=1.0) adalah pose jaga,
        # jadi wobble-nya harus memakai seed "idle" supaya frame akhir
        # = frame idle piksel-demi-piksel (hanya combat-glow mata beda).
        seed_action = "idle" if (attack and ap >= 0.999) else action
        seed = _NS_grimjaw._seed_q(phase, {"idle": 1, "walk": 2,
                                           "attack": 3, "spin": 4}.get(seed_action, 1))

        # ═══ 1. GERAK BADAN: root / lean / sway / mane lag ═══
        t_rec = 0.0
        crest_tilt = 0.0
        if walk:
            root_y = int(math.sin(phase * 2.0) * 2.5) - 2
            sway = int(math.sin(phase) * 3.0)
            lean = (4 + int(abs(stride) * 2)) * f
            crest_tilt = math.sin(phase + 2.6) * 0.07
        elif attack:
            pose = _NS_grimjaw._attack_pose(ap)
            root_y = pose["bob"]
            sway = 0
            lean = pose["lean"] * f
            t_rec = max(0.0, min(1.0, (ap - _NS_grimjaw.ATTACK_SWING_END) /
                                 (1.0 - _NS_grimjaw.ATTACK_SWING_END)))
            crest_tilt = -pose["lean"] * 0.05 * (1.0 - t_rec)
            if pose["tremble"]:
                sway = 1 if int(phase * 30) % 2 else -1
        elif spin:
            root_y = -2
            sway = 0
            lean = 0
            crest_tilt = math.sin(phase * 3.0) * 0.05
        else:
            root_y = int(breath * 2.2)
            sway = int(math.sin(phase * 0.5) * 2.0)
            lean = int(math.sin(phase * 0.5 + 1.2) * 1.5)
        off_x = lean + sway

        def ptf(dx, dy):
            return (cx + dx * f + off_x, cy + dy + root_y)

        def blob(fill, coords, salt=0, ink=None, width=2, gap=1.5,
                 alpha=255, close=True, passes=2):
            pts = [ptf(dx, dy) for dx, dy in coords]
            _NS_grimjaw._marker_poly(surface, fill, pts, seed + salt,
                                     INK if ink is None else ink, width,
                                     gap, alpha, alpha, close, passes)

        def tube(a, b, width, fill, salt=0, shade=None, alpha=255):
            _NS_grimjaw._tube(surface, ptf(*a), ptf(*b), width, fill, INK,
                              seed + salt, alpha, shade)

        def stroke(a, b, color, width=2, salt=0, alpha=255, passes=2):
            _NS_grimjaw._ink_stroke(surface, color, ptf(*a), ptf(*b),
                                    width, seed + salt, alpha, passes)

        def dot(fill, dx, dy, r, salt=0, alpha=255):
            sc = ptf(dx, dy)
            if r <= 2.6:
                # titik kecil: lingkaran AA halus - wobble tak terbaca
                _NS_grimjaw._aacircle(surface,
                                      _NS_grimjaw._rgba(fill, alpha),
                                      (sc[0], sc[1]), max(1, int(r)))
                return
            _NS_grimjaw._ink_ellipse(surface, fill, sc[0], sc[1], r,
                                     r * 0.92, seed + salt, None, 0,
                                     alpha=alpha, fill_alpha=alpha,
                                     n=9, gap=0.0, passes=0)

        def scrib(color, dx, dy, rx, ry, salt=0, alpha=140, loops=3,
                  angle=0.0, width=2):
            sc = ptf(dx, dy)
            _NS_grimjaw._scribble(surface, color, sc[0], sc[1], rx, ry,
                                  seed + salt, alpha, loops, angle, width)

        # ═══ 2. MANE API BELAKANG (lidah doodle ber-inersia) ═══
        flare = 1.0
        if attack:
            flare = _NS_grimjaw._attack_pose(ap)["flare"]
        if spin:
            flare = 1.12
        if fury:
            flare *= 1.10 + 0.05 * math.sin(phase * 3)
        if crit or omni:
            flare *= 1.06
        _NS_grimjaw._draw_elite_flame_mane(
            surface, ptf, f, phase, action, crest_tilt, flare,
            seed + 900, fury, omni, detail)

        # ═══ 3. LENGAN BELAKANG (tinju) ═══
        rear_shoulder = (-13, -24)
        if attack:
            rear_elbow = (-20 + int(t_rec), -8 + int(2 * t_rec))
            rear_hand = (-24 + int(2 * t_rec), 4 + int(4 * t_rec))
        elif walk:
            rear_elbow = (-20, -6 + int(stride * 5))
            rear_hand = (-24, 8 + int(stride * 7))
        elif spin:
            rear_elbow = (-22, -10)
            rear_hand = (-26, -14)
        else:
            rear_elbow = (-19, -6)
            rear_hand = (-22, 8 + int(breath))
        tube(rear_shoulder, rear_elbow, 9, p["skin_dark"], 101,
             p["skin_darkest"])
        tube(rear_elbow, rear_hand, 8, p["skin_mid"], 102)
        dot(p["skin_dark"], rear_hand[0], rear_hand[1], 5, 103)
        for kn in (-2, 0, 2):                      # buku jari tinta
            stroke((rear_hand[0] + kn * 0.4, rear_hand[1] + 2),
                   (rear_hand[0] + kn * 0.4 + 0.4, rear_hand[1] + 4),
                   INK, 1, 104 + kn, 150, 1)

        # ═══ 4. WAR-SKIRT BELAKANG (hem bergerigi) ═══
        skirt_sway = int(math.sin(phase * 0.9 + 1.2) * 3)
        hem_spine = [(14 + skirt_sway, 32), (6, 41), (0, 38),
                     (-6, 42), (-14 + skirt_sway, 31)]
        hem = _NS_grimjaw._tuft_points(hem_spine, depth=3.5, min_len=6,
                                       seed=9)
        blob(p["red_dark"], [(-16, 6), (16, 6)] + hem, 110, gap=1.3)
        blob(p["red_mid"], [(-13, 8), (13, 8), (10 + skirt_sway, 29),
                            (0, 34), (-10 + skirt_sway, 29)], 111,
             ink=None, gap=0.0, alpha=235, close=True, passes=0)

        # ═══ 5. KAKI: foot solver (menapak / terangkat) ═══
        front_step = int(stride * 8) if walk else 0
        rear_step = -front_step
        if attack:
            front_step += int(ap * 8 * (1.0 - t_rec))
            rear_step -= int(ap * 4 * (1.0 - t_rec))
        if spin:
            front_step, rear_step = 13, -13
        stride_vel = math.cos(phase * 1.72) if walk else 0.0
        front_lift = int(max(0.0, stride_vel) * 10) if walk else 0
        rear_lift = int(max(0.0, -stride_vel) * 10) if walk else 0
        for side, step, lift, salt in ((-1, rear_step, rear_lift, 201),
                                       (1, front_step, front_lift, 202)):
            hip = (side * 10, 6)
            knee = (side * 12 + int(step * 0.5), 30 - lift)
            ankle = (side * 13 + int(step * 0.8), 50 - lift)
            fx = side * 13 + step
            # paha
            tube(hip, knee, 10, p["skin_dark"] if side < 0 else p["skin_mid"],
                 salt, p["skin_darkest"])
            # shin guard baja doodle
            tube(knee, ankle, 8, p["metal_mid"], salt + 1, p["metal_dark"])
            stroke((knee[0] - 5, 31 - lift), (knee[0] + 5, 31 - lift),
                   p["gold_dark"], 3, salt + 2, 210, 1)
            stroke((knee[0] - 4, 33 - lift), (knee[0] + 4, 33 - lift),
                   p["gold_mid"], 1, salt + 3, 190, 1)
            # boot blob + sol + ujung kaki
            boot_fill = p["boot_dark"] if side < 0 else p["boot_mid"]
            blob(boot_fill, [(fx - 8, 50 - lift), (fx + 8, 50 - lift),
                             (fx + 10, 62 - lift), (fx + 12, 67 - lift),
                             (fx + 6, 69 - lift), (fx - 9, 69 - lift)],
                 salt + 4, gap=1.2)
            stroke((fx - 9, 67 - lift), (fx + 12, 67 - lift), INK, 3,
                   salt + 5, 235, 1)
            stroke((fx + 5, 60 - lift), (fx + 11, 66 - lift),
                   p["boot_light"], 2, salt + 6, 190, 1)
            # bayangan kontak + debu saat menapak
            if lift == 0 and (not walk or abs(stride_vel) < 0.55):
                gx, gy = ptf(fx, 71)
                _NS_grimjaw._scribble(surface, INK, gx, gy, 12, 3,
                                      seed + salt + 7, 55, 2, 0, 2)
            if walk and lift == 0 and abs(stride_vel) < 0.35:
                gx, gy = ptf(fx - 6, 69)
                for k in range(2):
                    _NS_grimjaw._doodle_star(
                        surface, gx - k * 5 * f, gy - k * 2, 4 - k,
                        p["fire_mid"], max(30, 120 - k * 40),
                        seed + salt + 8 + k, 4, 1)

        # ═══ 6. TORSO: dada V-taper + sash + harness + medallion ═══
        blob(p["skin_mid"], [(-16, -28), (16, -28), (13, -6), (11, 10),
                             (-11, 10), (-13, -6)], 301)
        scrib(p["skin_dark"], 8, -3, 8, 9, 302, 85, 3, 0.5)     # arsiran sisi jauh
        stroke((-11, -24), (3, -23), p["skin_light"], 4, 303, 120, 1)  # pita cahaya
        stroke((-8, -14), (-1, -12), p["skin_dark"], 1, 304, 160, 1)   # garis pektoral
        stroke((1, -12), (8, -14), p["skin_dark"], 1, 305, 160, 1)
        stroke((0, -20), (0, 4), p["ink_soft"], 1, 306, 110, 1)        # sternum
        stroke((-7, -2), (7, -2), p["skin_dark"], 1, 307, 130, 1)      # abs
        # sash merah diagonal
        blob(p["red_mid"], [(-15, -24), (-8, -27), (14, 9), (11, 13),
                            (-15, -3)], 310, gap=1.2)
        stroke((-12, -24), (10, 8), p["red_light"], 1, 311, 150, 1)
        for i in range(4):                       # jahitan sash
            t = 0.2 + i * 0.2
            sx = -12 + 22 * t
            sy = -23 + 31 * t
            stroke((sx - 1, sy - 1), (sx + 1, sy + 1), p["cloth_stitch"],
                   1, 312 + i, 150, 1)
        # harness X kulit + studs
        tube((13, -25), (-11, 9), 5, p["armor_mid"], 320, p["armor_dark"])
        for i in range(3):
            t = 0.25 + i * 0.25
            dot(p["gold_mid"], 13 - 24 * t, -25 + 34 * t, 1.4, 321 + i)
        # medallion sternum
        dot(p["gold_darkest"], 0, -16, 4.4, 325)
        dot(p["gold_mid"], 0, -16, 3.2, 326)
        dot(p["white"], -1, -17, 1.0, 327, 220)

        # ═══ 7. SABUK + gesper emas ═══
        blob(p["armor_dark"], [(-13, 8), (13, 8), (13, 15), (-13, 15)], 330)
        for bx in (-9, -5, 5, 9):
            dot(p["gold_dark"], bx, 11.5, 1.3, 331 + bx)
        blob(p["gold_mid"], [(0, 8), (4, 11.5), (0, 15), (-4, 11.5)], 335,
             gap=0.9)
        dot(p["gold_shine"], -1, 10.5, 1.0, 336, 220)

        # ═══ 8. LOINCLOTH DEPAN + hem bergerigi ═══
        cloth_sway = int(math.sin(phase * 1.1) * 3)
        hem_spine2 = [(-9, 22), (-5, 30 + cloth_sway), (0, 34 + cloth_sway),
                      (5, 29 + cloth_sway), (9, 22)]
        hem2 = _NS_grimjaw._tuft_points(hem_spine2, depth=3.0, min_len=5,
                                        seed=17)
        blob(p["red_dark"], [(-10, 12), (10, 12)] + hem2, 340, gap=1.2)
        blob(p["red_mid"], [(-7, 14), (7, 14), (5, 24 + cloth_sway),
                            (0, 30 + cloth_sway), (-5, 24 + cloth_sway)],
             341, ink=None, gap=0.0, alpha=225, passes=0)
        stroke((-3, 16), (1 + cloth_sway, 27), p["blood_dark"], 1, 342,
               160, 1)

        # ═══ 9. HIP TASSETS (2 pelat per sisi) ═══
        for side, salt in ((-1, 350), (1, 354)):
            hx = side * 13
            blob(p["armor_dark"], [(hx - 4, 9), (hx + 3, 9), (hx + 2, 18),
                                   (hx - 1, 22), (hx - 5, 18)], salt, gap=1.0)
            blob(p["armor_mid"], [(hx - 3, 10), (hx + 2, 10), (hx + 1, 17),
                                  (hx - 1, 20), (hx - 4, 17)], salt + 1,
                 ink=None, gap=0.0, alpha=220, passes=0)
            dot(p["gold_light"], hx - 1, 20, 1.0, salt + 2, 200)

        # ═══ 10. PAULDRON baja doodle + duri ═══
        for side, salt in ((-1, 501), (1, 505)):
            sx = side * 16
            sc = ptf(sx, -27)
            _NS_grimjaw._ink_ellipse(surface, p["metal_light"], sc[0], sc[1],
                                     8, 7, seed + salt, INK, 2, 0, 255,
                                     255, 14, 1.3, 2)
            _NS_grimjaw._scribble(surface, p["metal_mid"],
                                  sc[0] + 2 * f, sc[1] + 2, 4, 3,
                                  seed + salt + 1, 85, 2, 0.6, 2)
            stroke((sx - 6, -22), (sx + 6, -22), p["gold_mid"], 2, salt + 2,
                   200, 1)
            blob(p["metal_mid"], [(sx - 3, -33), (sx - 2, -42), (sx - 1, -33)],
                 salt + 3, gap=0.8)
            blob(p["metal_mid"], [(sx + 2, -33), (sx + 4, -40), (sx + 5, -33)],
                 salt + 4, gap=0.8)
            dot(p["metal_shine"], sx - 3, -30, 1.0, salt + 5, 210)

        # ═══ 11. LEHER ═══
        blob(p["skin_dark"], [(-6, -33), (6, -33), (7, -26), (-7, -26)], 360)

        # ═══ 12. LENGAN DEPAN (lengan blade) ═══
        grip = _NS_grimjaw._blade_grip_local(action, ap, phase)
        front_shoulder = (12, -24)
        if attack:
            front_elbow = _NS_grimjaw._front_arm_elbow(ap)
        elif walk:
            front_elbow = (grip[0] - 5, grip[1] + 7 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 5, grip[1] + 8)
        tube(front_shoulder, front_elbow, 9, p["skin_mid"], 601,
             p["skin_dark"])
        tube(front_elbow, grip, 8, p["skin_light"], 602)
        # bracer baja di siku
        bx0 = (front_elbow[0] * 0.7 + grip[0] * 0.3,
               front_elbow[1] * 0.7 + grip[1] * 0.3)
        tube(front_elbow, bx0, 9, p["metal_mid"], 603, p["metal_dark"])
        stroke((front_elbow[0] - 4, front_elbow[1] + 3),
               (front_elbow[0] + 5, front_elbow[1] + 3), p["gold_mid"], 1,
               604, 190, 1)

        # ═══ 13. FLAME BLADE + smear + spin sweep ═══
        angle = _NS_grimjaw._blade_angle(phase, action, ap, spin_phase)
        length = _NS_grimjaw._blade_len_ap(action, ap)
        hot = crit or omni

        # Smear ayunan doodle (fallback) - dilompati kalau lapisan hidup
        # (heroes/grimjaw_fx.SwingTrail) sudah menggambar trail 60fps.
        if attack and 0.30 < ap < 0.88 and not _NS_grimjaw._FX_LIVE.v:
            _NS_grimjaw._draw_blade_swing_trail(surface, cx, cy, f, phase, ap)

        if spin:
            _NS_grimjaw._draw_spin_flame_sweep(surface, cx, cy, f,
                                               spin_phase, phase)

        _NS_grimjaw._draw_elite_flame_blade(
            surface, ptf, f, grip, angle, length, phase, detail,
            hot=hot, omni=omni, seed=seed + 700)

        # kepalan tangan menutup gagang
        dot(p["skin_mid"], grip[0], grip[1], 5, 610)
        stroke((grip[0] - 2, grip[1] - 3), (grip[0] + 2, grip[1] - 2),
               p["skin_high"], 2, 611, 200, 1)

        # ═══ 14. MASK JUGGERNAUT + kepala ═══
        _NS_grimjaw._draw_elite_mask(surface, ptf, f, phase, action, ap,
                                     detail, ward=ward, crit=crit,
                                     omni=omni, seed=seed + 800)

        # ═══ 15. Poni + side locks mane ═══
        _NS_grimjaw._draw_elite_mane_front(surface, ptf, f, phase, action,
                                           crest_tilt, seed + 850)

        # ═══ 16. Detail portrait LOD ═══
        if detail:
            _NS_grimjaw._draw_grimjaw_masterwork_details(
                surface, ptf, None, f, phase, action)

        # ═══ 17. Garis kecepatan saat berjalan / bara saat fury ═══
        if walk and abs(stride) > 0.55:
            back = ptf(-22, -16)
            _NS_grimjaw._speed_ticks(
                surface, p["ink_soft"], back[0], back[1],
                math.pi if f > 0 else 0.0, 3, 13, 80, seed + 61, 1, 7.0)
        if fury or omni:
            _NS_grimjaw._ember_marks(surface, cx + f * 6, cy - 55, 30, 26,
                                     seed + 62, p["hair_light"], 150, 3,
                                     phase)
        _NS_grimjaw._ember_marks(surface, cx + f * 2, cy - 58, 26, 22,
                                 seed + 63, p["ember"], 110, 3, phase)

    # -------------------------------------------------------------------
    # Mane api belakang - lidah teardrop doodle
    # -------------------------------------------------------------------
    def _draw_elite_flame_mane(surface, pt, f, phase, action, tilt=0.0,
                               flare=1.0, seed=0, fury=False, omni=False,
                               detail=False):
        """Mane api: 7 lidah doodle mengelilingi puncak kepala.

        Lidah terpanjang di puncak (topi api), memendek ke depan/belakang.
        Inersia: semua lidah diputar ``tilt`` (lag dari akselerasi);
        ``flare`` (fury/crit) memanjangkan lidah.
        """
        p = _NS_grimjaw.PALETTE
        INK = p["ink"]
        tongues = (
            # (base_x, base_y, kemiringan dari vertikal, panjang, lebar)
            (-13, -54, -50, 26, 11),
            (-11, -61, -36, 31, 12),
            (-7,  -66, -20, 35, 13),
            (-2,  -69,  -4, 36, 13),
            (4,   -68,  12, 32, 12),
            (9,   -64,  28, 26, 11),
            (12,  -58,  44, 20, 9),
        )
        if detail:
            tongues = tongues + (
                (-15, -49, -62, 18, 8),
                (14, -53, 56, 16, 8),
            )
        for i, (bx, by, tilt_deg, ln, wd) in enumerate(tongues):
            a = math.radians(tilt_deg) + tilt
            d = (math.sin(a), -math.cos(a))
            ln2 = ln * flare
            fill = p["hair_mid"] if i % 2 == 0 else p["hair_dark"]
            if omni and i % 3 == 0:
                fill = p["rage_mid"]
            base = pt(bx, by)
            _NS_grimjaw._flame_tongue(surface, base, d, ln2, wd,
                                       seed + i * 17, fill,
                                       p["hair_high"], INK)
            if ln >= 30:                    # lidah besar dapat lidah dalam
                inner = (base[0] + d[0] * ln2 * 0.16,
                         base[1] + d[1] * ln2 * 0.16)
                _NS_grimjaw._flame_tongue(
                    surface, inner, d, ln2 * 0.55, wd * 0.5,
                    seed + i * 23 + 5, p["hair_light"], p["hair_shine"],
                    INK, alpha=235, bend=0.5, scrib=False, gap=0.8)
        # bara naik di atas mane
        top = pt(0, -74)
        _NS_grimjaw._ember_marks(surface, top[0], top[1] - 14, 30, 22,
                                 seed + 3, p["hair_light"], 150, 4, phase)

    def _draw_elite_mane_front(surface, pt, f, phase, action, tilt=0.0,
                               seed=0):
        """Poni api kecil menjuntai di dahi mask."""
        p = _NS_grimjaw.PALETTE
        INK = p["ink"]
        fringe = (
            (-7, -68, -34, 12, 7),
            (0, -70, -10, 14, 8),
            (7, -67, 16, 11, 6),
        )
        for i, (bx, by, tilt_deg, ln, wd) in enumerate(fringe):
            a = math.radians(tilt_deg) + tilt * 0.6
            d = (math.sin(a), math.cos(a))      # menjuntai KE BAWAH
            base = pt(bx, by)
            _NS_grimjaw._flame_tongue(
                surface, base, d, ln, wd, seed + i * 13,
                p["hair_mid"] if i != 1 else p["hair_light"],
                p["hair_high"], INK, alpha=245, bend=0.45, gap=0.9)

    # -------------------------------------------------------------------
    # Mask juggernaut doodle - kertas putih + strip darah spidol
    # -------------------------------------------------------------------
    def _draw_elite_mask(surface, pt, f, phase, action, ap=0.0,
                         detail=False, ward=False, crit=False, omni=False,
                         seed=0):
        p = _NS_grimjaw.PALETTE
        INK = p["ink"]
        eyes_glow = action in ("attack", "spin") or ap > 0.35 or crit or omni
        eye_col = p["heal_mid"] if ward else p["eye_glow"]

        # blob mask (kertas putih)
        coords = [(-9, -66), (0, -72), (9, -66), (12, -58), (12, -48),
                  (9, -40), (5, -36), (0, -34), (-5, -36), (-9, -40),
                  (-12, -48), (-12, -58)]
        pts = [pt(dx, dy) for dx, dy in coords]
        _NS_grimjaw._marker_poly(surface, p["mask_light"], pts, seed + 1,
                                 INK, 2, 1.4, 255, 255, True, 2)
        # arsiran lembut sisi jauh + gel-pen kiri-atas
        sc = pt(6, -46)
        _NS_grimjaw._scribble(surface, p["mask_mid"], sc[0], sc[1], 5, 7,
                              seed + 2, 80, 3, 0.4, 2)
        hc = pt(-5, -62)
        _NS_grimjaw._ink_stroke(surface, p["white"], (hc[0] - 3, hc[1]),
                                (hc[0] + 3, hc[1] - 1), 2, seed + 3, 210, 1)
        # tanduk kecil
        for side, salt in ((-1, 4), (1, 6)):
            hxp = [pt(side * 11, -63), pt(side * 15, -71), pt(side * 9, -66)]
            _NS_grimjaw._marker_poly(surface, p["mask_mid"], hxp, seed + salt,
                                     INK, 1, 0.7, 255, 255, True, 1)
        # emblem emas diamond di dahi
        em = [pt(-2, -66), pt(0, -69), pt(2, -66), pt(0, -63)]
        _NS_grimjaw._marker_poly(surface, p["gold_mid"], em, seed + 8,
                                 INK, 1, 0.7, 255, 255, True, 1)
        # alis marah + batang hidung
        for side, salt in ((-1, 9), (1, 10)):
            a = pt(side * 9, -56)
            b = pt(side * 3, -59)
            _NS_grimjaw._ink_stroke(surface, INK, a, b, 2, seed + salt)
        nb0, nb1 = pt(0, -60), pt(0, -46)
        _NS_grimjaw._ink_stroke(surface, p["ink_soft"], nb0, nb1, 1,
                                seed + 11, 170, 1)
        # strip darah spidol (sedikit melebihi tepi mask - khas doodle)
        s0, s1 = pt(-1, -71), pt(1, -37)
        _NS_grimjaw._ink_stroke(surface, p["blood_mid"], s0, s1, 4,
                                seed + 12, 235, 1)
        s0, s1 = pt(0, -68), pt(0, -40)
        _NS_grimjaw._ink_stroke(surface, p["blood_light"], s0, s1, 1,
                                seed + 13, 200, 1)
        for side, salt in ((-1, 14), (1, 15)):
            a = pt(side * 9, -63)
            b = pt(side * 4, -47)
            _NS_grimjaw._ink_stroke(surface, p["blood_dark"], a, b, 3,
                                    seed + salt, 220, 1)
        # tetes darah
        dp = pt(2, -36)
        _NS_grimjaw._ink_ellipse(surface, p["blood_mid"], dp[0], dp[1], 1.4,
                                 1.8, seed + 16, None, 0, alpha=220,
                                 fill_alpha=220, n=8, gap=0.0, passes=0)
        # mata
        blink = (action == "idle" and
                 _NS_grimjaw._hash01(int(phase * 0.9) + 3) > 0.92)
        for ex in (-6, 6):
            ec = pt(ex, -52)
            if blink and not eyes_glow:
                _NS_grimjaw._ink_stroke(surface, INK, (ec[0] - 2, ec[1]),
                                        (ec[0] + 2, ec[1]), 2, seed + 20)
                continue
            fill = eye_col if (eyes_glow or ward) else p["white"]
            _NS_grimjaw._ink_ellipse(surface, fill, ec[0], ec[1], 3, 2.3,
                                     seed + 21 + ex, INK, 1, 0, 255, 250,
                                     10, 0.5, 1)
            if eyes_glow:
                _NS_grimjaw._ink_ellipse(surface, p["white"],
                                         ec[0] - f, ec[1] - 1, 1.0, 1.0,
                                         seed + 22 + ex, None, 0,
                                         alpha=235, fill_alpha=235, n=8,
                                         gap=0.0, passes=0)
            elif ward:
                _NS_grimjaw._ink_ellipse(surface, p["heal_core"],
                                         ec[0], ec[1], 1.0, 1.0,
                                         seed + 23 + ex, None, 0,
                                         alpha=235, fill_alpha=235, n=8,
                                         gap=0.0, passes=0)
            else:
                _NS_grimjaw._ink_ellipse(surface, INK, ec[0] + f, ec[1],
                                         1.2, 1.4, seed + 24 + ex, None, 0,
                                         alpha=255, fill_alpha=255, n=8,
                                         gap=0.0, passes=0)
        # grille rahang: garis tinta + gigi
        j0, j1 = pt(-5, -39), pt(5, -39)
        _NS_grimjaw._ink_stroke(surface, INK, j0, j1, 3, seed + 30)
        for tx in (-4, -1, 2, 4):
            a = pt(tx, -39)
            b = pt(tx, -36)
            _NS_grimjaw._ink_stroke(surface, INK, a, b, 2, seed + 31 + tx)
        # tanda snarl
        if detail:
            a, b = pt(6, -45), pt(9, -42)
            _NS_grimjaw._ink_stroke(surface, p["ink_soft"], a, b, 1,
                                    seed + 36, 170, 1)
            a, b = pt(-9, -44), pt(-11, -41)
            _NS_grimjaw._ink_stroke(surface, p["ink_soft"], a, b, 1,
                                    seed + 37, 170, 1)

    # -------------------------------------------------------------------
    # Flame blade doodle - scimitar sketsa + api di punggung bilah
    # -------------------------------------------------------------------
    def _draw_elite_flame_blade(surface, pt, f, grip, angle, length, phase,
                                detail=False, hot=False, omni=False,
                                seed=0):
        p = _NS_grimjaw.PALETTE
        INK = p["ink"]
        s = math.sin(angle)
        c = math.cos(angle)
        segs = 6
        centers = []
        for i in range(segs + 1):
            t = i / segs
            curve = 11.0 * (t * t)
            centers.append((grip[0] + s * length * t + c * curve,
                            grip[1] + c * length * t - s * curve))
        nx, ny = c, -s
        left, right = [], []
        for i, (x, y) in enumerate(centers):
            t = i / segs
            wd = 6.5 * (1.0 - t) + 2.0 * t
            left.append((x + nx * wd, y + ny * wd))
            right.append((x - nx * wd, y - ny * wd))
        outline = left + right[::-1]
        flat = [pt(o[0], o[1]) for o in outline]

        fill = _NS_grimjaw._mix(p["fire_mid"], p["rage_light"], 0.45) \
            if hot else p["fire_mid"]
        _NS_grimjaw._marker_poly(surface, fill, flat, seed + 11, INK, 2,
                                 1.0, 255, 255, True, 2)
        # inti panas: goresan tebal sepanjang jalur tengah
        core_pts = [pt(x, y) for x, y in centers[1:segs]]
        if len(core_pts) >= 2:
            core_col = p["fire_core"] if hot else p["fire_hot"]
            pygame.draw.lines(surface, _NS_grimjaw._rgba(core_col, 240),
                              False, _NS_grimjaw._ipoints(core_pts), 3)
        # kilau gel-pen dekat ujung
        tipx, tipy = centers[segs - 1]
        g0 = pt(tipx + nx * 3, tipy + ny * 3)
        g1 = pt(tipx + nx * 3 + s * 4, tipy + ny * 3 + c * 4)
        _NS_grimjaw._ink_stroke(surface, p["white"], g0, g1, 1, seed + 13,
                                220, 1)
        # lidah api di punggung bilah (sisi cembung)
        for ci, ln in ((2, 13), (4, 10)):
            bx, by = centers[ci]
            fdx = s * 0.55 + nx * 0.65
            fdy = c * 0.55 + ny * 0.65
            L = math.hypot(fdx, fdy) or 1.0
            base = pt(bx, by)
            _NS_grimjaw._flame_tongue(
                surface, base, (fdx / L, fdy / L), ln * (1.15 if hot else 1.0),
                6.5, seed + ci * 19, p["fire_light"], p["fire_hot"], INK,
                alpha=250, bend=0.55, gap=0.8)
        if hot:
            # bara tambahan + skribel glow
            tip = pt(centers[segs][0], centers[segs][1])
            _NS_grimjaw._ember_marks(surface, tip[0], tip[1], 16, 18,
                                     seed + 15, p["fire_hot"], 190, 3, phase)
            _NS_grimjaw._scribble(surface, p["fire_light"], tip[0], tip[1],
                                  12, 12, seed + 16, 80, 3, 0, 2)
        # gagang: quillon tinta + pommel emas
        q0 = pt(grip[0] + nx * 6, grip[1] + ny * 6)
        q1 = pt(grip[0] - nx * 6, grip[1] - ny * 6)
        _NS_grimjaw._ink_stroke(surface, INK, q0, q1, 2, seed + 17)
        pom = pt(grip[0] - s * 5, grip[1] - c * 5)
        _NS_grimjaw._ink_ellipse(surface, p["gold_mid"], pom[0], pom[1], 3,
                                 3, seed + 18, INK, 1, 0, 255, 255, 10,
                                 0.6, 1)

    # -------------------------------------------------------------------
    # Detail portrait LOD (hatch + jahitan + rivet ekstra)
    # -------------------------------------------------------------------
    def _draw_grimjaw_masterwork_details(surface, pt, poly, f, phase, action):
        p = _NS_grimjaw.PALETTE
        seed = _NS_grimjaw._seed_q(phase, 9)
        # arsiran bayangan torso
        hc = pt(8, -4)
        _NS_grimjaw._hatch_patch(surface, p["skin_dark"], hc[0], hc[1],
                                 14, 22, seed + 1, 105, 4.2, 0.6, 1)
        # arsiran pauldron
        for side in (-1, 1):
            hc = pt(side * 16, -27)
            _NS_grimjaw._hatch_patch(surface, p["metal_dark"], hc[0], hc[1],
                                     10, 8, seed + 2 + side, 90, 3.6, 0.9, 1)
        # jahitan sash (silang)
        for i in range(5):
            t = 0.15 + i * 0.18
            sx, sy = -11 + 22 * t, -22 + 30 * t
            a = pt(sx - 1, sy - 1)
            b = pt(sx + 1, sy + 1)
            _NS_grimjaw._ink_stroke(surface, p["cloth_stitch"], a, b, 1,
                                    seed + 10 + i, 170, 1)
        # jahitan loincloth
        for i in range(3):
            a = pt(-4 + i * 4, 15)
            b = pt(-3 + i * 4, 19)
            _NS_grimjaw._ink_stroke(surface, p["cloth_stitch"], a, b, 1,
                                    seed + 20 + i, 160, 1)
        # stripe perang di lengan depan atas
        a = pt(10, -20)
        b = pt(15, -17)
        _NS_grimjaw._ink_stroke(surface, p["blood_mid"], a, b, 2, seed + 30,
                                190, 1)
        a = pt(10, -16)
        b = pt(15, -13)
        _NS_grimjaw._ink_stroke(surface, p["blood_mid"], a, b, 2, seed + 31,
                                190, 1)
        # gel-pen tambahan: mask & sabuk
        a = pt(-6, -58)
        b = pt(-3, -59)
        _NS_grimjaw._ink_stroke(surface, p["white"], a, b, 1, seed + 32,
                                210, 1)
        a = pt(-11, 9)
        b = pt(-4, 9)
        _NS_grimjaw._ink_stroke(surface, p["gold_shine"], a, b, 1, seed + 33,
                                200, 1)
        # tapak kaki: garis tapak sole
        for side in (-1, 1):
            a = pt(side * 13 - 4, 68)
            b = pt(side * 13 + 2, 68)
            _NS_grimjaw._ink_stroke(surface, p["ink_soft"], a, b, 1,
                                    seed + 40 + side, 150, 1)

    # ===================================================================
    # FX TEBAKAN IN-CANVAS (fallback saat lapisan hidup tidak ada)
    # ===================================================================
    def _draw_blade_swing_trail(surface, cx, cy, f, phase, ap):
        """Ekor komet tinta+api mengikuti jalur ujung pedang."""
        p = _NS_grimjaw.PALETTE
        p0 = max(_NS_grimjaw.ATTACK_WINDUP_END, ap - 0.20)
        steps = 7
        prev = None
        for i in range(steps + 1):
            t = i / steps
            pr = p0 + (ap - p0) * t
            tip = _NS_grimjaw._blade_tip_local(phase, "attack", pr)
            cur = (cx + tip[0] * f, cy + tip[1])
            if prev is not None:
                wgt = 0.30 + 0.70 * t
                alpha = int(205 * wgt)
                wdt = max(2, int(8 * wgt))
                j = _NS_grimjaw._jit(int(pr * 90) + i, 1.2)
                a = (prev[0], prev[1] + j * 0.4)
                b = (cur[0], cur[1] + j * 0.4)
                pygame.draw.line(surface,
                                 _NS_grimjaw._rgba(p["fire_dark"],
                                                   int(alpha * 0.6)),
                                 (round(a[0]), round(a[1])),
                                 (round(b[0]), round(b[1])), wdt)
                pygame.draw.line(surface,
                                 _NS_grimjaw._rgba(p["fire_light"], alpha),
                                 (round(a[0]), round(a[1])),
                                 (round(b[0]), round(b[1])),
                                 max(1, wdt // 2))
            prev = cur

    def _draw_fire_slash_arc(surface, x, y, facing, progress, crit=False,
                             phase=0.0):
        """Sabit tebasan doodle - ATAS -> BAWAH, kepala menempel pedang.

        Titik-titik sabit diambil dari posisi ujung pedang SEBENARNYA
        (fungsi pose yang sama dengan rig) sehingga arah tebasan tidak
        mungkin berlawanan dengan pedang.
        """
        p0 = _NS_grimjaw.ATTACK_WINDUP_END - 0.02
        p1 = _NS_grimjaw.ATTACK_SWING_END
        if progress < p0 or progress > 0.92:
            return
        p = _NS_grimjaw.PALETTE
        fsign = 1 if facing >= 0 else -1
        travel = (progress - p0) / (p1 - p0)
        travel = max(0.0, min(1.0, travel))
        travel = travel ** 1.35
        fade = 1.0
        if progress > p1:
            fade = 1.0 - (progress - p1) / (0.92 - p1)
        fade = max(0.0, min(1.0, fade))
        if fade <= 0.0:
            return
        seed = int(progress * 60) + (3 if crit else 0)
        steps = 14
        pts = []
        for i in range(steps + 1):
            s = (i + 1) / steps       # 0 = ekor (atas), 1 = kepala
            pr = p0 + (progress - p0) * s
            tipx, tipy = _NS_grimjaw._blade_tip_local(phase, "attack", pr)
            pts.append((x + tipx * fsign, y + tipy))
        base = 9 if crit else 8
        for i in range(steps):
            s = (i + 1) / steps
            taper = 0.3 + 0.7 * (s ** 1.6)
            alpha = int((40 + 205 * (s ** 1.5)) * fade)
            if alpha <= 0:
                continue
            a, b = pts[i], pts[i + 1]
            j = _NS_grimjaw._jit(seed + i, 1.4)
            a = (a[0], a[1] + j * 0.5)
            b = (b[0], b[1] + j * 0.5)
            pygame.draw.line(surface,
                             _NS_grimjaw._rgba(p["fire_dark"],
                                               int(alpha * 0.55)),
                             (round(a[0]), round(a[1])),
                             (round(b[0]), round(b[1])),
                             max(2, int(base * taper)))
            pygame.draw.line(surface,
                             _NS_grimjaw._rgba(p["fire_mid"], alpha),
                             (round(a[0]), round(a[1])),
                             (round(b[0]), round(b[1])),
                             max(2, int(base * taper * 0.62)))
            pygame.draw.line(surface,
                             _NS_grimjaw._rgba(p["fire_light"], alpha),
                             (round(a[0]), round(a[1])),
                             (round(b[0]), round(b[1])),
                             max(1, int(base * taper * 0.3)))
        # kepala sabit: bintang doodle di ujung pedang saat ini
        tipx, tipy = _NS_grimjaw._blade_tip_local(phase, "attack", progress)
        hx = x + tipx * fsign
        hy = y + tipy
        head_a = fade * (0.5 + 0.5 * travel)
        arc_scale = 1.25 if crit else 1.0
        _NS_grimjaw._doodle_star(surface, hx, hy, 15 * arc_scale,
                                 p["fire_light"], int(215 * head_a),
                                 seed + 1, 6, 3)
        _NS_grimjaw._doodle_star(surface, hx, hy, 8 * arc_scale,
                                 p["fire_hot"], int(250 * head_a),
                                 seed + 2, 5, 2)
        _NS_grimjaw._ink_ellipse(surface, p["fire_core"], hx, hy, 2.2, 2.2,
                                 seed + 3, None, 0, alpha=int(230 * head_a),
                                 fill_alpha=int(230 * head_a), n=8,
                                 gap=0.0, passes=0)

    def _draw_impact_flash(surface, x, y, facing, progress, crit=False):
        """Pop benturan doodle: bintang + awan poof + garis kecepatan."""
        if not (0.52 < progress < 0.86):
            return
        p = _NS_grimjaw.PALETTE
        t = (progress - 0.52) / 0.34
        env = math.sin(math.pi * t)
        if env <= 0.05:
            return
        fsign = 1 if facing >= 0 else -1
        tipx, tipy = _NS_grimjaw._blade_tip_local(
            0.0, "attack", min(progress, _NS_grimjaw.ATTACK_SWING_END))
        ix = x + tipx * fsign
        iy = y + tipy
        r = (13 if crit else 10) * (0.6 + 0.5 * env)
        alpha = int(235 * env)
        seed = int(progress * 80) + (5 if crit else 0)
        _NS_grimjaw._poof(surface, ix, iy, r * 1.8, p["fire_light"],
                          int(alpha * 0.45), seed, 4, 2, None,
                          p["fire_dark"], 45)
        _NS_grimjaw._doodle_star(surface, ix, iy, r * 1.25,
                                 p["ink"], int(alpha * 0.55), seed + 4,
                                 8, 1)
        _NS_grimjaw._doodle_star(surface, ix, iy, r, p["fire_hot"], alpha,
                                 seed, 7 if crit else 6, 3)
        _NS_grimjaw._doodle_star(surface, ix, iy, r * 0.5, p["fire_core"],
                                 min(255, alpha + 30), seed + 3, 4, 2)
        # garis kecepatan memancar berlawanan arah tebasan
        _NS_grimjaw._speed_ticks(surface, p["ink_soft"],
                                 ix - fsign * 3, iy,
                                 math.pi if fsign > 0 else 0.0, 3, 11,
                                 int(alpha * 0.5), seed + 6, 1, 8.0)

    def _draw_critical_strike_burst(surface, x, y, facing, progress):
        """Ledakan crit doodle: bintang besar + cincin + percik."""
        if not (0.56 < progress < 0.82):
            return
        p = _NS_grimjaw.PALETTE
        t = (progress - 0.56) / 0.26
        env = math.sin(math.pi * t)
        if env <= 0.05:
            return
        fsign = 1 if facing >= 0 else -1
        tipx, tipy = _NS_grimjaw._blade_tip_local(
            0.0, "attack", _NS_grimjaw.ATTACK_SWING_END)
        ix = x + tipx * fsign
        iy = y + tipy
        seed = int(progress * 90)
        r = 16 + 14 * env
        _NS_grimjaw._doodle_star(surface, ix, iy, r * 1.3, p["ink"],
                                 int(140 * env), seed, 8, 2)
        _NS_grimjaw._doodle_star(surface, ix, iy, r, p["gold_light"],
                                 int(240 * env), seed + 1, 8, 4)
        _NS_grimjaw._doodle_star(surface, ix, iy, r * 0.55, p["fire_hot"],
                                 min(255, int(255 * env)), seed + 2, 5, 3)
        _NS_grimjaw._dashed_ring(surface, ix, iy, int(r * 1.15),
                                 p["gold_mid"], int(190 * env),
                                 progress * 6.0, 2, 9, seed + 3)
        for i in range(5):
            a = i * (math.tau / 5) + progress * 3.0
            px = ix + math.cos(a) * r * 1.35
            py = iy + math.sin(a) * r * 1.1
            _NS_grimjaw._doodle_star(surface, px, py, 5, p["gold_shine"],
                                     int(200 * env), seed + 4 + i, 4, 1)

    def _draw_spin_flame_sweep(surface, cx, cy, f, spin_phase, phase):
        """Sapuan api berputar (Blade Fury): arc elips doodle + percik."""
        p = _NS_grimjaw.PALETTE
        seed = int(spin_phase * 4)
        for k in range(3):
            rx = 37 - k * 6
            ry = 13 - k * 2
            a0 = spin_phase * (1.0 if k % 2 == 0 else -1.3) + k * 2.2
            col = p["fire_mid"] if k % 2 == 0 else p["fire_light"]
            pts = []
            steps = 9
            for i in range(steps + 1):
                a = a0 + 2.2 * i / steps
                wob = 1.0 + _NS_grimjaw._jit(seed * 7 + k * 13 + i, 0.05)
                pts.append((cx + math.cos(a) * rx * wob,
                            cy - 8 + math.sin(a) * ry * wob))
            pygame.draw.lines(surface,
                              _NS_grimjaw._rgba(col, 215 - k * 35), False,
                              _NS_grimjaw._ipoints(pts), 3 - k)
        for i in range(4):
            a = spin_phase * 1.5 + i * (math.tau / 4)
            px = cx + math.cos(a) * 34
            py = cy - 8 + math.sin(a) * 11
            _NS_grimjaw._doodle_star(surface, px, py, 4, p["fire_hot"], 220,
                                     seed + 20 + i, 4, 1)

    # ===================================================================
    # LAPISAN AMBIENT (doodle: skribel, arsir, bara)
    # ===================================================================
    def _draw_shadow(surface, x, y):
        """Bayangan kontak: skribel elips tinta (cache statis)."""
        def build():
            s = pygame.Surface((56, 20), pygame.SRCALPHA)
            _NS_grimjaw._scribble(s, _NS_grimjaw.INK, 28, 10, 22, 5, 5,
                                  70, 3, 0.0, 2)
            _NS_grimjaw._hatch_patch(s, _NS_grimjaw.INK, 28, 10, 34, 8, 9,
                                     55, 4.5, 0.0, 1)
            return s
        surf = _NS_grimjaw._static(("dshadow",), build)
        surface.blit(surf, (int(x - 28), int(y - 10)))

    def _draw_fire_mist(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Kabut bara di kaki: skribel asap + bara naik."""
        p = _NS_grimjaw.PALETTE
        q = int(phase * 2) % 8
        seed = q * 37 + (1 if intense else 0)
        col = p["fire_dark"] if intense else \
            _NS_grimjaw._mix(p["fire_dark"], _NS_grimjaw.INK, 0.5)
        alpha = 95 if intense else 70
        n = 3 if (trail or intense) else 2
        for i in range(n):
            ox = _NS_grimjaw._jit(seed + i * 7, 9) - i * 6 * facing \
                - (4 * facing if trail else 0)
            oy = -i * 5 + _NS_grimjaw._jit(seed * 3 + i, 3)
            _NS_grimjaw._scribble(surface, col, cx + ox, cy - 5 + oy,
                                  max(3, 9 - i * 2), 4, seed + i * 13,
                                  max(20, alpha - i * 18), 2, 0.12, 2)
        _NS_grimjaw._ember_marks(surface, cx, cy + 2, 22, 9, seed + 5,
                                 p["fire_mid"] if intense else p["ember"],
                                 80 if intense else 55, 2, phase)

    def _draw_fire_aura(surface, x, y, phase):
        """Halo api samar di belakang badan (skribel besar, cache)."""
        q = int(phase * 2) % 6

        def build(q):
            s = pygame.Surface((150, 190), pygame.SRCALPHA)
            _NS_grimjaw._scribble(s, (230, 104, 22), 75, 95, 62, 76,
                                  q * 11 + 3, 30, 3, 0.0, 2)
            _NS_grimjaw._scribble(s, (166, 48, 14), 75, 95, 46, 60,
                                  q * 17 + 5, 24, 2, 0.4, 2)
            return s
        surf = _NS_grimjaw._static(("daura", q), lambda: build(q))
        surface.blit(surf, (int(x - 75), int(y - 95)))

    def _draw_rage_aura(surface, x, y, phase):
        """Halo rage (omnislash): skribel merah lebih liar."""
        q = int(phase * 3) % 6

        def build(q):
            s = pygame.Surface((160, 200), pygame.SRCALPHA)
            _NS_grimjaw._scribble(s, (186, 48, 34), 80, 100, 66, 80,
                                  q * 13 + 3, 38, 4, 0.2, 2)
            _NS_grimjaw._scribble(s, (118, 28, 22), 80, 100, 50, 64,
                                  q * 19 + 5, 30, 3, 0.7, 2)
            _NS_grimjaw._hatch_patch(s, (118, 28, 22), 80, 100, 90, 120,
                                     q * 7 + 1, 26, 9.0, 0.9, 1)
            return s
        surf = _NS_grimjaw._static(("drage", q), lambda: build(q))
        surface.blit(surf, (int(x - 80), int(y - 100)))

    def _draw_fire_platform(surface, x, y, phase, skill):
        """Sigil tanah doodle: cincin putus-putus + bracket + rune."""
        edge = {"q": (230, 104, 22), "w": (96, 190, 106),
                "e": (204, 150, 48), "r": (186, 48, 34)}.get(skill,
                                                            (255, 178, 84))
        q = int(phase * 2) % 8

        def build(q):
            s = pygame.Surface((96, 48), pygame.SRCALPHA)
            cx, cy = 48, 26
            _NS_grimjaw._dashed_ring(s, cx, cy + 6, 34, edge, 150, q * 0.8,
                                     2, 9, q * 13, ry=11)
            for k in range(4):
                a = k * (math.pi / 2) + math.pi / 4
                x0 = cx + math.cos(a) * 30
                y0 = cy + 6 + math.sin(a) * 10
                x1 = cx + math.cos(a) * 38
                y1 = cy + 6 + math.sin(a) * 13
                pygame.draw.line(s, (*edge, 170), (round(x0), round(y0)),
                                 (round(x1), round(y1)), 2)
            _NS_grimjaw._scribble(
                s, _NS_grimjaw._mix(edge, _NS_grimjaw.INK, 0.35),
                cx, cy + 6, 11, 5, q * 7 + 1, 95, 2, 0.0, 2)
            _NS_grimjaw._ember_marks(s, cx, cy + 8, 44, 8, q * 5 + 2,
                                     edge, 110, 3, q * 0.7)
            return s
        surf = _NS_grimjaw._static(("dplat", skill, q), lambda: build(q))
        surface.blit(surf, (int(x - 48), int(y - 26)))

    def _draw_fire_particles_orbit(surface, x, y, phase):
        """Bara mengorbit badan (Blade Fury)."""
        p = _NS_grimjaw.PALETTE
        seed = int(phase * 5)
        for i in range(5):
            a = phase * 2.4 + i * (math.tau / 5)
            ox = math.cos(a) * 24
            oy = -30 + math.sin(a) * 9
            col = p["fire_light"] if i % 2 else p["fire_hot"]
            px, py = int(x + ox), int(y + oy)
            _NS_grimjaw._doodle_star(surface, px, py, 4, col, 210,
                                     seed + i * 7, 4, 1)
            pygame.draw.line(surface, _NS_grimjaw._rgba(col, 120),
                             (px, py), (px - int(math.cos(a) * 5),
                                        py - int(math.sin(a) * 2)), 1)

    # ===================================================================
    # SKILL FX - telegraph tanah / depan (world-space, doodle)
    # ===================================================================
    def _draw_blade_fury_ground(surface, hero, x, y, timer, phase):
        """Q Blade Fury: marker AOE angular + retakan + spiral."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("q", timer)
        env = _NS_grimjaw._skill_steady(prog)
        if env <= 0.0:
            return
        rng_world = int(getattr(hero, "skill_range", 70) or 70)
        r = _NS_grimjaw._ring_r(hero, rng_world, surface)
        # PENTING: marker angular dipusatkan TEPAT di (x, y) - pipeline
        # dan tooling memverifikasi radius dunia dari titik jangkar.
        cy = y
        seed = int(phase * 7)
        # marker angular: tick radial di radius DUNIA (warm, terbaca)
        _NS_grimjaw._dashed_ring(
            surface, x, cy, r, p["fire_mid"], int(215 * env), phase, 4,
            26, seed, tick_len=max(6, int(r * 0.10)))
        # cincin putus-putus dalam
        _NS_grimjaw._dashed_ring(surface, x, cy, int(r * 0.8),
                                 p["fire_dark"], int(120 * env), phase, 2,
                                 9, seed + 1, ry=int(r * 0.5))
        # hangus: retakan + arsir pusat
        for i in range(3):
            a = i * (math.tau / 3) + 0.4
            _NS_grimjaw._jagged_crack(surface, x, cy, a, r * 0.5,
                                      (p["fire_darkest"], p["fire_dark"]),
                                      int(150 * env), seed + 2 + i, 4, 3)
        _NS_grimjaw._hatch_patch(surface, p["fire_darkest"], x, cy,
                                 int(r * 0.7), 12, seed + 5,
                                 int(55 * env), 5.0, 0.0, 1)
        _NS_grimjaw._scribble(surface, p["fire_mid"], x, cy, r * 0.22,
                              r * 0.09, seed + 6, int(90 * env), 3, 0.0, 2)
        # bracket sudut (viewfinder)
        for k in range(4):
            a = k * (math.pi / 2) + math.pi / 4
            bx = x + math.cos(a) * r * 0.97
            by = cy + math.sin(a) * r * 0.5
            _NS_grimjaw._chevron(surface, bx, by,
                                 a + math.pi if math.cos(a) < 0 else a,
                                 9, p["fire_light"], int(190 * env), 2,
                                 seed + 7 + k)
        # fase aktivasi: cincin konvergen + bintang
        if prog < 0.22:
            t = prog / 0.22
            _NS_grimjaw._dashed_ring(
                surface, x, cy, int(r * (1.0 - 0.55 * t)), p["fire_light"],
                int(210 * (1.0 - t * 0.4)), phase * 2.0, 2, 12, seed + 11,
                tick_len=max(5, int(r * 0.08)), inner=True)
            _NS_grimjaw._doodle_star(surface, x, cy, 16 + int(10 * t),
                                     p["fire_light"], int(200 * (1 - t * 0.5)),
                                     seed + 12, 6, 2)

    def _draw_blade_fury_rings(surface, x, y, phase):
        """Cincin api berputar di depan badan (Blade Fury aktif)."""
        p = _NS_grimjaw.PALETTE
        seed = int(phase * 6)
        for k in range(3):
            rx = 40 - k * 6
            ry = 13 - k * 2
            a0 = phase * (2.2 + k * 0.8) * (1 if k % 2 == 0 else -1)
            col = p["fire_mid"] if k % 2 == 0 else p["fire_light"]
            pts = []
            steps = 10
            for i in range(steps + 1):
                a = a0 + 2.0 * i / steps
                wob = 1.0 + _NS_grimjaw._jit(seed + k * 11 + i, 0.05)
                pts.append((x + math.cos(a) * rx * wob,
                            y + math.sin(a) * ry * wob))
            pygame.draw.lines(surface,
                              _NS_grimjaw._rgba(col, 220 - k * 40), False,
                              _NS_grimjaw._ipoints(pts), 3 - k)
        for i in range(4):
            a = phase * 2.0 + i * (math.tau / 4)
            _NS_grimjaw._doodle_star(
                surface, x + math.cos(a) * 36, y + math.sin(a) * 12,
                4, p["fire_hot"], 220, seed + 30 + i, 4, 1)

    def _draw_healing_ward_ground(surface, hero, x, y, timer, phase):
        """W Healing Ward: cincin hijau + salib doodle + mote naik."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("w", timer)
        env = _NS_grimjaw._skill_steady(prog)
        if env <= 0.0:
            return
        wp = getattr(hero, "_heal_ward_pos", None)
        if wp:
            tx, ty = _NS_grimjaw._world_to_local(hero, x, y, wp[0], wp[1])
        else:
            tx, ty = x, y
        r = _NS_grimjaw._ring_r(hero, 90, surface)
        seed = int(phase * 7)
        _NS_grimjaw._dashed_ring(surface, tx, ty + 6, r, p["heal_mid"],
                                 int(200 * env), phase, 3, 12, seed,
                                 ry=int(r * 0.62))
        # salib doodle di 4 arah
        for k in range(4):
            a = k * (math.pi / 2)
            px = tx + math.cos(a) * r * 0.78
            py = ty + 6 + math.sin(a) * r * 0.42
            _NS_grimjaw._ink_stroke(surface, p["heal_light"],
                                    (px - 4, py), (px + 4, py), 2,
                                    seed + 1 + k, int(190 * env), 1)
            _NS_grimjaw._ink_stroke(surface, p["heal_light"],
                                    (px, py - 4), (px, py + 4), 2,
                                    seed + 5 + k, int(190 * env), 1)
        _NS_grimjaw._ember_marks(surface, tx, ty + 2, int(r * 1.1), 16,
                                 seed + 9, p["heal_light"],
                                 int(160 * env), 4, phase)
        _NS_grimjaw._scribble(surface, p["heal_dark"], tx, ty + 6,
                              r * 0.32, r * 0.12, seed + 10,
                              int(70 * env), 2, 0.0, 2)
        if prog < 0.25:
            _NS_grimjaw._doodle_star(surface, tx, ty + 4, 14, p["heal_core"],
                                     220, seed + 11, 6, 2)

    def _draw_healing_ward_totem(surface, hero, x, y, timer, phase):
        """Totem ward doodle: tiang terukir + daun + glow."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("w", timer)
        env = _NS_grimjaw._skill_steady(prog)
        if env <= 0.05:
            return
        wp = getattr(hero, "_heal_ward_pos", None)
        if wp:
            tx, ty = _NS_grimjaw._world_to_local(hero, x, y, wp[0], wp[1])
        else:
            tx, ty = x, y
        q = int(phase * 2) % 6

        def build(q):
            s = pygame.Surface((48, 88), pygame.SRCALPHA)
            INK = _NS_grimjaw.INK
            # tiang kayu
            _NS_grimjaw._marker_poly(s, p["armor_mid"],
                                     [(16, 82), (32, 82), (29, 24),
                                      (19, 24)], q * 3 + 1, INK, 2, 1.2)
            _NS_grimjaw._hatch_patch(s, p["armor_dark"], 28, 55, 10, 46,
                                     q * 5 + 2, 80, 4.5, 0.2, 1)
            # kepala totem terukir
            _NS_grimjaw._ink_ellipse(s, p["mask_light"], 24, 16, 10, 9,
                                     q * 5 + 3, INK, 2, 0, 255, 255, 12,
                                     1.2, 2)
            pygame.draw.line(s, (*INK, 220), (19, 14), (22, 15), 2)
            pygame.draw.line(s, (*INK, 220), (26, 15), (29, 14), 2)
            pygame.draw.line(s, (*INK, 200), (21, 20), (27, 20), 2)
            # mata hijau menyala (lingkaran AA halus)
            _NS_grimjaw._aacircle(s, (*p["heal_mid"], 235), (22, 15), 2)
            _NS_grimjaw._aacircle(s, (*p["heal_mid"], 235), (26, 15), 2)
            # daun tuft di puncak
            for i, (dx, dy, ln) in enumerate(((-4, -6, 11), (0, -8, 13),
                                              (4, -6, 10))):
                _NS_grimjaw._flame_tongue(
                    s, (24 + dx, 10 + dy), (dx / 8.0, -1.0), ln, 5,
                    q * 7 + i * 5, p["heal_mid"] if i != 1 else p["heal_light"],
                    p["heal_core"], INK, alpha=240, bend=0.5, gap=0.8)
            # glow skribel
            _NS_grimjaw._scribble(s, p["heal_light"], 24, 40, 15, 18,
                                  q * 9 + 3, 60, 3, 0.0, 2)
            # salib kecil di tiang
            pygame.draw.line(s, (*p["heal_light"], 190), (24, 34),
                             (24, 44), 2)
            pygame.draw.line(s, (*p["heal_light"], 190), (20, 39),
                             (28, 39), 2)
            return s
        surf = _NS_grimjaw._static(("dtotem", q), lambda: build(q))
        a = int(255 * min(1.0, env + 0.15))
        surf.set_alpha(a)
        surface.blit(surf, (int(tx - 24), int(ty - 12)))
        surf.set_alpha(255)

    def _draw_heal_aura(surface, x, y, phase):
        """Halo penyembuh: skribel hijau lembut (cache)."""
        q = int(phase * 2) % 6

        def build(q):
            s = pygame.Surface((130, 150), pygame.SRCALPHA)
            _NS_grimjaw._scribble(s, (96, 190, 106), 65, 80, 52, 60,
                                  q * 13 + 7, 38, 3, 0.0, 2)
            _NS_grimjaw._scribble(s, (150, 232, 158), 65, 80, 34, 42,
                                  q * 19 + 3, 30, 2, 0.5, 2)
            return s
        surf = _NS_grimjaw._static(("dheal", q), lambda: build(q))
        surface.blit(surf, (int(x - 65), int(y - 80)))

    def _draw_crit_telegraph(surface, hero, x, y, timer, phase):
        """E Critical Strike (fase cast): chevron konvergen + ring mengecil."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("e", timer)
        if prog > 0.30:
            return
        t = prog / 0.30
        tx, ty = _NS_grimjaw._target_position(hero, x, y)
        ang = math.atan2(ty - (y - 10), tx - x)
        seed = int(phase * 7)
        for i in range(3):
            d = 46 - i * 12 - t * 18
            cxp = x + math.cos(ang) * d
            cyp = y - 10 + math.sin(ang) * d
            _NS_grimjaw._chevron(surface, cxp, cyp, ang, 10 + i * 3,
                                 p["gold_light"], int(200 - 30 * i),
                                 3, seed + i)
        _NS_grimjaw._doodle_star(surface, x, y - 10, int(14 + 6 * t),
                                 p["gold_light"], 160, seed + 3, 5, 2)
        _NS_grimjaw._dashed_ring(surface, x, y - 6, int(30 - 14 * t),
                                 p["gold_mid"], 180, phase, 2, 8, seed + 4)
        _NS_grimjaw._speed_ticks(surface, p["gold_mid"], x, y - 10, ang,
                                 3, 10, int(120 * (1 - t)), seed + 5, 1,
                                 9.0)

    def _draw_crit_steady(surface, hero, x, y, timer, phase):
        """E Critical Strike (steady): cincin gold berdenyut + kilau orbit."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("e", timer)
        env = _NS_grimjaw._skill_steady(prog)
        if env <= 0.0:
            return
        pulse = 0.6 + 0.4 * math.sin(phase * 3)
        r = _NS_grimjaw._ring_r(hero, 26, surface)
        seed = int(phase * 9)
        _NS_grimjaw._dashed_ring(surface, x, y - 8, r, p["gold_light"],
                                 int(190 * env * pulse), phase * 2.0, 2, 8,
                                 seed)
        _NS_grimjaw._dashed_ring(surface, x, y - 8, int(r * 0.7),
                                 p["gold_mid"], int(150 * env), -phase * 1.5,
                                 2, 6, seed + 3, ry=int(r * 0.5))
        for i in range(3):
            a = phase * 2.0 + i * (math.tau / 3)
            _NS_grimjaw._doodle_star(
                surface, x + math.cos(a) * r * 1.1,
                y - 8 + math.sin(a) * r * 0.4, 6, p["gold_shine"],
                int(200 * env), seed + 6 + i, 4, 2)

    def _draw_omnislash_ground(surface, hero, x, y, timer, phase):
        """R Omnislash (tanah): ring besar + tanda X + retakan."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("r", timer)
        env = _NS_grimjaw._skill_steady(prog, 4.0)
        if env <= 0.0:
            return
        r = _NS_grimjaw._ring_r(hero, 80, surface)
        cy = y + 4
        seed = int(phase * 7)
        _NS_grimjaw._dashed_ring(surface, x, cy, r, p["rage_mid"],
                                 int(200 * env), phase, 3, 12, seed,
                                 ry=int(r * 0.5))
        _NS_grimjaw._dashed_ring(surface, x, cy, int(r * 0.55),
                                 p["rage_dark"], int(140 * env), -phase, 2,
                                 8, seed + 1, ry=int(r * 0.3))
        for i in range(4):
            a = i * (math.tau / 4) + phase * 0.6
            px = x + math.cos(a) * r * 0.75
            py = cy + math.sin(a) * r * 0.35
            _NS_grimjaw._ink_stroke(surface, p["rage_light"],
                                    (px - 5, py - 5), (px + 5, py + 5), 2,
                                    seed + 2 + i, int(190 * env), 1)
            _NS_grimjaw._ink_stroke(surface, p["rage_light"],
                                    (px - 5, py + 5), (px + 5, py - 5), 2,
                                    seed + 6 + i, int(190 * env), 1)
        for i in range(5):
            a = i * (math.tau / 5) + 0.3
            _NS_grimjaw._jagged_crack(surface, x, cy, a, r * 0.6,
                                      (p["rage_dark"], p["rage_mid"]),
                                      int(140 * env), seed + 10 + i, 4, 3)

    def _draw_omnislash_slashes(surface, hero, x, y, timer, phase):
        """R Omnislash (depan): tebasan tinta panjang menyilang badai."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("r", timer)
        env = _NS_grimjaw._skill_steady(prog, 4.0)
        if env <= 0.3:
            return
        seed = int(phase * 4)
        for i in range(4):
            a = phase * 7.0 + i * (math.tau / 4)
            L = 76 + 18 * _NS_grimjaw._hash01(seed + i)
            cxp = x + _NS_grimjaw._jit(seed + i * 3, 18)
            cyp = y - 18 + _NS_grimjaw._jit(seed + i * 5, 14)
            dx, dy = math.cos(a), math.sin(a)
            p0 = (cxp - dx * L / 2, cyp - dy * L / 2)
            p1 = (cxp + dx * L / 2, cyp + dy * L / 2)
            alpha = int(210 * env)
            _NS_grimjaw._ink_stroke(surface, _NS_grimjaw.INK, p0, p1, 6,
                                    seed + i * 11, int(alpha * 0.5))
            _NS_grimjaw._ink_stroke(surface, p["rage_light"], p0, p1, 4,
                                    seed + i * 11, alpha, passes=1)
            _NS_grimjaw._ink_stroke(surface, p["rage_bright"], p0, p1, 1,
                                    seed + i * 13,
                                    min(255, alpha + 40), passes=1)
            _NS_grimjaw._doodle_star(surface, p1[0], p1[1], 7, p["fire_hot"],
                                     int(180 * env), seed + i * 17, 4, 2)

    def _draw_omnislash_target(surface, hero, x, y, timer, phase):
        """R Omnislash: crosshair doodle di target."""
        p = _NS_grimjaw.PALETTE
        prog = _NS_grimjaw._skill_progress("r", timer)
        env = _NS_grimjaw._skill_steady(prog, 4.0)
        if env <= 0.0:
            return
        tx, ty = _NS_grimjaw._target_position(hero, x, y)
        pulse = 0.55 + 0.45 * math.sin(phase * 4)
        seed = int(phase * 5)
        alpha = int(210 * env)
        _NS_grimjaw._ink_stroke(surface, p["rage_light"],
                                (tx - 11, ty - 11), (tx + 11, ty + 11), 3,
                                seed + 1, alpha)
        _NS_grimjaw._ink_stroke(surface, p["rage_light"],
                                (tx - 11, ty + 11), (tx + 11, ty - 11), 3,
                                seed + 2, alpha)
        _NS_grimjaw._dashed_ring(surface, tx, ty, 16, p["rage_bright"],
                                 int(200 * env * pulse), phase * 2.0, 2, 8,
                                 seed + 3)
        for k in range(4):
            a = k * (math.pi / 2)
            x0 = tx + math.cos(a) * 19
            y0 = ty + math.sin(a) * 19
            x1 = tx + math.cos(a) * 25
            y1 = ty + math.sin(a) * 25
            pygame.draw.line(surface,
                             _NS_grimjaw._rgba(p["rage_bright"], alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             2)
        _NS_grimjaw._doodle_star(surface, tx, ty, 6, p["rage_bright"],
                                 int(220 * env), seed + 4, 4, 2)

    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_hero(surface, hero, x, y):
        _NS_grimjaw.draw_grimjaw(surface, hero, x, y)
# ====================================================================
# sylara.py
# ====================================================================
class _NS_sylara:
    """Namespace sylara - PIXEL MASTERWORK v2 + Skill FX v2.1.

    Rewrite penuh renderer Sylara (Wind Ranger).  Tetap 100% prosedural:
    tidak ada PNG / sprite-sheet / image.load.

    Yang naik dibanding versi lama
    ------------------------------
    1. RIG ~1.52x LEBIH BESAR di resolusi native (buffer rig 240x210,
       bbox idle >= 130px tinggi).  Pipeline hero (heroes/__init__.py)
       mengukur badan lalu men-scale agar tinggi di layar tetap ~51-70 px,
       jadi memperbesar rig TIDAK memperbesar hero di arena - melainkan
       memberi ~2.4 px native per px layar: cluster, ramp dan muka tetap
       tajam setelah smoothscale + lighting + outline pass.
    2. DISIPLIN PIXEL-ART: ramp 4-5 nilai per material dengan hue-shift
       (bayangan rambut didorong merah-ungu menuju kulit, highlight hijau
       gembira), selout (outline gelap hanya di sisi bayangan), siluet
       cape & rambut bergerigi via _tuft_points (hash deterministik),
       specular sebagai cluster 1-2 px yang disengaja (kilau busur/baja),
       dither band di korset.  Key light kiri-atas, konsisten lighting.py.
    3. ANATOMI: hood hijau runcing dengan rambut merah berkibar, cape
       robek ber-lapis per-panel, quiver anak panah + busur recurve
       pose-driven (grip/nock/tali dihitung dari sendi), korset kulit
       hijau ber-strap, gesper emas, boot kulit 3 band.
    4. ANIMASI: foot-solver jalan (kaki menapak/terangkat, bayangan kontak,
       debu), inersia cape/hair (tertinggal dari akselerasi + flare saat
       serang), idle hidup (napas, blink, daun melayang, flutter busur),
       timeline serang multi-keyframe: wind-up -> release (IMPACT burst +
       smear) -> recovery dengan loop-closure tanpa pop.
     5. SKILL FX khas ranger (bukan Thorne/Drakar): pita angin laminar,
        siklon daun, halo rumput, sulur hidup, fletching, gale tunnel.
        World-space via _fx_scale (cap 2.6). Tiap skill 3 fase. Badan ikut
        bereaksi (busur/cape hijau, afterimage Windrun). Proyektil panah
        angin. Surface statis di-cache; radius di-clamp ke canvas.
    """

    # ---------------------------------------------------------------------------
    # LAPISAN FX HIDUP (heroes/sylara_fx.py)
    # ---------------------------------------------------------------------------
    # Sprite Sylara DI-CACHE oleh pipeline hero (heroes/__init__.py).
    # Semua yang harus bergerak 60 fps sejati - trail ayunan busur,
    # partikel daun/angin, proyektil panah angin, impact, screen shake,
    # hit-stop - TIDAK boleh hidup di dalam canvas itu: hasilnya ikut
    # beku pada kuantisasi pose dan menyusut bersama sprite.
    #
    # Modul ``heroes/sylara_fx.py`` adalah lapisan hidupnya: digambar
    # langsung ke layar pada skala 1:1.  Jembatan di bawah memasang
    # director per unit dan memberi tahu rig bahwa smear/flash di-canvas
    # sudah digantikan, sehingga tidak ada efek yang tergambar dua kali.
    #
    # Jalur HERO lane menggambar lapisannya lewat heroes/__init__.py
    # (``_LIVE_FX_HEROES``); jalur BOSS (draw dipanggil tiap frame, di
    # luar cache) menggambarnya sendiri di ``draw_sylara``.
    _LIVE_MOD = None

    class _LiveFlag:
        """Penanda sederhana yang bisa di-set dari fungsi static."""
        __slots__ = ("v",)

        def __init__(self):
            self.v = False

    #: Dibaca rig: True = trail/flash sudah diambil alih lapisan hidup
    #: 60 fps, jadi canvas tidak menggambarnya dua kali.
    _FX_LIVE = _LiveFlag()

    @staticmethod
    def _live_module():
        """Muat ``heroes.sylara_fx`` sekali; None kalau tidak tersedia.

        Impor dilakukan DI SINI (bukan di kepala modul) supaya bundle
        hero besar tidak menarik paket FX saat build hanya-butuh-
        renderer, dan supaya lapisan FX bisa dimatikan lewat satu flag
        tanpa merusak jalur render (pola yang sama dengan _NS_vex).
        """
        NS = _NS_sylara
        if NS._LIVE_MOD is None:
            try:
                from heroes import sylara_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "SYLARA_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def _fx_live_owned(hero):
        """True kalau lapisan hidup mengambil alih FX unit ini."""
        try:
            mod = _NS_sylara._live_module()
            if mod is None:
                return False
            return bool(mod.owns(hero))
        except Exception:
            return False

    def live_fx_ready():
        """True kalau lapisan hidup Sylara bisa dipakai (dipakai tooling)."""
        return _NS_sylara._live_module() is not None

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # Rig v2 membesarkan koordinat lokal lama (~1.52x). Pipeline hero
    # mengukur badan lalu men-scale kembali ke ukuran arena (~72 px);
    # yang naik adalah kepadatan piksel native, bukan ukuran di layar.
    RIG_SCALE = 1.52
    ATTACK_WINDUP_END = 0.26
    ATTACK_RELEASE_END = 0.58
    ATTACK_IMPACT = 0.52

    # ---------------------------------------------------------------------------
    # HD Color Palette - Wind Ranger inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - fair
        "skin_darkest":   (155, 105,  85),
        "skin_dark":      (210, 160, 130),
        "skin_mid":       (240, 200, 170),
        "skin_light":     (250, 220, 195),
        "skin_high":      (255, 240, 220),

        # Hair (red/orange)
        "hair_darkest":   ( 85,  25,  15),
        "hair_dark":      (145,  50,  25),
        "hair_mid":       (200,  85,  35),
        "hair_light":     (240, 130,  55),
        "hair_shine":     (255, 180,  95),
        "hair_high":      (255, 214, 140),

        # Green outfit - forest green
        "cloth_darkest":  ( 15,  35,  20),
        "cloth_dark":     ( 35,  65,  35),
        "cloth_mid":      ( 60, 105,  55),
        "cloth_light":    ( 95, 150,  80),
        "cloth_high":     (140, 195, 115),

        # Cloak - darker green
        "cloak_darkest":  ( 20,  40,  25),
        "cloak_dark":     ( 40,  75,  40),
        "cloak_mid":      ( 65, 110,  55),
        "cloak_light":    (100, 155,  80),
        "cloak_high":     (148, 198, 118),

        # Hood - similar to cloak
        "hood_darkest":   ( 18,  36,  20),
        "hood_dark":      ( 30,  55,  30),
        "hood_mid":       ( 55,  95,  50),
        "hood_light":     ( 85, 135,  70),

        # Leather (belt, boots, quiver)
        "leather_darkest":( 35,  20,  10),
        "leather_dark":   ( 70,  45,  25),
        "leather_mid":    (110,  75,  45),
        "leather_light":  (155, 110,  70),
        "leather_high":   (198, 150,  96),

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 236, 150),

        # Bow - wood
        "wood_darkest":   ( 45,  25,  15),
        "wood_dark":      ( 85,  55,  30),
        "wood_mid":       (130,  90,  50),
        "wood_light":     (170, 125,  75),
        "wood_shine":     (205, 165, 105),

        # Bowstring
        "string":         (220, 210, 180),
        "string_shine":   (250, 245, 220),

        # Wind - green energy
        "wind_darkest":   ( 20,  60,  25),
        "wind_dark":      ( 50, 120,  50),
        "wind_mid":       (110, 195,  90),
        "wind_light":     (170, 235, 135),
        "wind_bright":    (210, 255, 175),
        "wind_white":     (240, 255, 220),
        "leaf_gold":      (196, 214,  72),
        "leaf_ember":     (236, 168,  58),

        # Arrow
        "arrow_shaft":    (200, 175, 130),
        "arrow_shaft_d":  (140, 110,  70),
        "arrow_head":     (180, 195, 210),
        "arrow_head_d":   (100, 115, 135),
        "arrow_feather":  (140, 200,  95),
        "arrow_feather_d":( 70, 120,  55),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       ( 90, 145,  80),
        "eye_iris_light": (150, 210, 130),
        "eye_pupil":      ( 15,  25,  15),

        # Lips
        "lips_dark":      (155,  70,  75),
        "lips_mid":       (205, 110, 115),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        if type(color) is tuple and len(color) == 3:
            _r, _g, _b = color
            if (type(_r) is int and type(_g) is int and type(_b) is int
                    and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
                return color
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sylara._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_sylara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_sylara._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_sylara._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_sylara._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_sylara._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_sylara._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 250 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Wind visual helpers
    # ---------------------------------------------------------------------------
    def _draw_wind_arc(surface, cx, cy, radius, start_angle, end_angle,
                       color, width=2, segments=12):
        """Curved wind arc."""
        points = []
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius
            points.append((px, py))
        for i in range(len(points) - 1):
            _NS_sylara._aaline(surface, color, points[i], points[i + 1], width)


    def _draw_leaf(surface, cx, cy, size, angle, color_dark, color_mid, color_light):
        """Small floating leaf."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        back_x = cx - ca * size
        back_y = cy - sa * size
        side1_x = cx + math.cos(angle + math.pi / 2) * size * 0.35
        side1_y = cy + math.sin(angle + math.pi / 2) * size * 0.35
        side2_x = cx + math.cos(angle - math.pi / 2) * size * 0.35
        side2_y = cy + math.sin(angle - math.pi / 2) * size * 0.35

        _NS_sylara._poly(surface, color_dark, [
            (tip_x, tip_y), (side1_x, side1_y),
            (back_x, back_y), (side2_x, side2_y),
        ])
        _NS_sylara._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((side1_x + cx) / 2, (side1_y + cy) / 2),
            (back_x, back_y),
            ((side2_x + cx) / 2, (side2_y + cy) / 2),
        ])
        _NS_sylara._aaline(surface, color_light, (back_x, back_y), (tip_x, tip_y), 1)


    # ---------------------------------------------------------------------------
    # SKILL FX v2.1 — WORLD-SPACE PRIMITIVES (setingkat Thorne v2.1 / Grimjaw v2)
    # ---------------------------------------------------------------------------
    # Efek skill digambar langsung ke canvas lalu di-scale _render_scale saat
    # di-blit ke arena -> tanpa kompensasi, cincin/telegraph ikut menyusut
    # sampai ~40% dan nyaris tidak terlihat.  Helper di bawah menggambar efek
    # LEBIH BESAR di canvas (faktor 1/_render_scale, cap 2.6) sehingga ukuran
    # DI LAYAR setara dunia.  Semua radius di-clamp ke dalam canvas cache
    # (_ring_r) supaya efek tidak terpotong di tepi.
    # ---------------------------------------------------------------------------
    SKILL_VISUAL_DURATION = {"q": 180, "w": 180, "e": 150, "r": 60}

    # Cache surface statis (aura / mist / ground glow) — dibangun SEKALI,
    # tanpa alokasi surface per frame.
    _STATIC_SURFACES = {}

    def _static(key, builder):
        surf = _NS_sylara._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_sylara._STATIC_SURFACES[key] = surf
        return surf

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _mix(a, b, t):
        """Blend linear dua warna (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_sylara._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _dither_dots(surface, color, points, alpha=80):
        """Dither band 50% klasik (bertahan setelah downscale)."""
        col = (*color, max(0, min(255, int(alpha))))
        for i, (px, py) in enumerate(points):
            if i % 2 == 0:
                _NS_sylara._aacircle(surface, col, (int(px), int(py)), 1)

    def _attack_pose(ap):
        """Keyframe serangan Sylara: draw -> hold -> IMPACT -> recover.

        0.00 rest -> 0.12 wind-up -> 0.26 tension -> 0.42 full draw
        -> 0.52 IMPACT release -> 0.72 follow-through -> 1.00 rest.
        Return bob/lean/flare/tremble yang dipakai rig dan smear busur.
        """
        keys = (
            (0.00,  0,  0, 1.00, 0),
            (0.12,  2, -4, 1.08, 0),
            (0.26,  3, -6, 1.18, 1),
            (0.42,  1, -5, 1.22, 0),
            (0.52, -2,  8, 1.32, 0),
            (0.72,  1,  3, 1.08, 0),
            (1.00,  0,  0, 1.00, 0),
        )
        ap = max(0.0, min(1.0, float(ap)))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)
                return {
                    "bob": int(round(k0[1] + (k1[1] - k0[1]) * t)),
                    "lean": int(round(k0[2] + (k1[2] - k0[2]) * t)),
                    "flare": k0[3] + (k1[3] - k0[3]) * t,
                    "tremble": 1 if (k0[4] and t < .9) else 0,
                }
        return {"bob": 0, "lean": 0, "flare": 1.0, "tremble": 0}

    # ═══════════════════════════════════════════════════════════════
    # v3 — TIMELINE SERANGAN, AYUNAN BUSUR, DAN ANIMATION CONTROLLER
    # ───────────────────────────────────────────────────────────────
    # Serangan Sylara punya DUA bentuk yang memakai satu timeline:
    #
    #   1. SHOT   — tarik tali -> full draw -> release (jarak jauh).
    #   2. SWING  — sapuan limb busur berbasis BUSUR (arc) saat musuh
    #               terlalu dekat untuk menembak (< SWING_RANGE dunia).
    #
    # Keduanya dipecah jadi enam fase supaya ada bobot & momentum:
    #
    #   ANTICIPATION -> WIND-UP -> SWING -> IMPACT -> FOLLOW -> RECOVERY
    #
    # Nilai di bawah adalah fraksi 0..1 dari durasi satu serangan dan
    # dipakai bersama oleh renderer (pose) maupun lapisan FX hidup
    # (trail, hitbox, release panah) — satu sumber kebenaran.
    # ═══════════════════════════════════════════════════════════════
    ATTACK_ANTICIPATION_END = 0.12   # counter-motion kecil ke belakang
    ATTACK_SWING_END = 0.58          # akhir busur maju (== RELEASE_END)
    ATTACK_IMPACT_END = 0.62         # jendela hit aktif berakhir
    ATTACK_FOLLOW_END = 0.80         # follow-through
    #  (0.80 - 1.00 = RECOVERY, kembali ke pose idle)

    #: Jendela hit aktif (fraksi progress) — dipakai hitbox & FX.
    ATTACK_ACTIVE_WINDOW = (0.42, 0.62)

    #: Frame IMPACT tunggal (lepas tali / puncak benturan sapuan).
    ATTACK_IMPACT_FRAME = 0.52

    #: Jendela perekaman trail senjata (fraksi progress).
    SWING_WINDOW = (0.16, 0.88)

    #: Jarak DUNIA maksimum yang memicu sapuan melee (bukan tembakan).
    SWING_RANGE = 64.0

    #: Pivot bahu (koordinat lokal rig) tempat busur berayun.
    SHOULDER_PIVOT = (4.0, -16.0)

    # Sudut busur ayunan (radian, ruang lokal rig; 0 = lurus ke depan).
    SWING_ARC_START = -1.24          # limb terangkat penuh ke belakang
    SWING_ARC_MID = -0.26            # melewati garis kepala
    SWING_ARC_END = 0.86             # ekstensi maksimum ke depan-bawah

    # Radius pivot -> grip busur per fase: ayunan MEMANJANG saat
    # menghantam lalu memendek lagi (bobot), bukan radius tetap.
    SWING_R_REST = 19.0
    SWING_R_WINDUP = 14.0
    SWING_R_STRIKE = 29.0
    SWING_R_FOLLOW = 24.0

    #: Nama state animasi + prioritas (angka besar menang).
    ANIM_STATES = {
        "IDLE": 0, "WALK": 10, "RUN": 15, "CHARGE": 30, "CAST": 35,
        "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
        "HIT": 60, "HURT": 65, "DEATH": 100,
    }

    #: Overlay debug rig (hitbox / hurtbox / range / state / progress).
    DEBUG_CHARACTER = False

    # ── easing ──────────────────────────────────────────────────────
    def _ease_out(t):
        t = max(0.0, min(1.0, float(t)))
        return 1.0 - (1.0 - t) * (1.0 - t)

    def _ease_in(t):
        t = max(0.0, min(1.0, float(t)))
        return t * t

    def _ease_in_out(t):
        t = max(0.0, min(1.0, float(t)))
        return t * t * (3.0 - 2.0 * t)

    def _lerp(a, b, t):
        return a + (b - a) * t

    # ── AYUNAN BERBASIS BUSUR ───────────────────────────────────────
    def _swing_arc_pose(ap):
        """Pose sapuan limb busur pada progress ``ap`` (0..1).

        Bukan lerp lurus dari pose awal ke pose akhir: grip bergerak
        pada BUSUR polar mengelilingi bahu (sudut + radius berubah
        terpisah), sehingga ayunan punya percepatan, ekstensi saat
        impact, dan follow-through yang melewati titik akhir sedikit
        sebelum mengendap.
        """
        A = _NS_sylara
        ap = max(0.0, min(1.0, float(ap)))
        anti = A.ATTACK_ANTICIPATION_END
        wind = A.ATTACK_WINDUP_END
        swing = A.ATTACK_SWING_END
        impact = A.ATTACK_IMPACT_END
        follow = A.ATTACK_FOLLOW_END

        if ap < anti:                                   # ANTICIPATION
            t = A._ease_out(ap / max(1e-6, anti))
            ang = A._lerp(0.30, A.SWING_ARC_START * 0.34, t)
            rad = A._lerp(A.SWING_R_REST, A.SWING_R_REST - 2.0, t)
            lean, bob, flare = -2.0 * t, 1.0 * t, 1.0 + 0.04 * t
        elif ap < wind:                                 # WIND-UP
            t = A._ease_in_out((ap - anti) / max(1e-6, wind - anti))
            ang = A._lerp(A.SWING_ARC_START * 0.34, A.SWING_ARC_START, t)
            rad = A._lerp(A.SWING_R_REST - 2.0, A.SWING_R_WINDUP, t)
            lean, bob = -2.0 - 3.0 * t, 1.0 - 2.0 * t
            flare = 1.04 + 0.16 * t
        elif ap < swing:                                # SWING (accel)
            t = A._ease_in((ap - wind) / max(1e-6, swing - wind))
            ang = A._lerp(A.SWING_ARC_START, A.SWING_ARC_MID, t)
            rad = A._lerp(A.SWING_R_WINDUP, A.SWING_R_STRIKE, t)
            lean = A._lerp(-5.0, 5.0, t)
            bob = A._lerp(-1.0, 2.0, t)
            flare = 1.20 + 0.14 * t
        elif ap < impact:                               # IMPACT
            t = A._ease_out((ap - swing) / max(1e-6, impact - swing))
            ang = A._lerp(A.SWING_ARC_MID, A.SWING_ARC_END, t)
            rad = A._lerp(A.SWING_R_STRIKE, A.SWING_R_STRIKE + 2.0, t)
            lean = A._lerp(5.0, 8.0, t)
            bob = A._lerp(2.0, 3.0, t)
            flare = 1.34 - 0.06 * t
        elif ap < follow:                               # FOLLOW THROUGH
            t = A._ease_out((ap - impact) / max(1e-6, follow - impact))
            # sedikit melewati sudut akhir (overshoot) lalu balik
            over = A.SWING_ARC_END + 0.20
            ang = A._lerp(over, A.SWING_ARC_END * 0.72, t)
            rad = A._lerp(A.SWING_R_STRIKE + 2.0, A.SWING_R_FOLLOW, t)
            lean = A._lerp(8.0, 3.0, t)
            bob = A._lerp(3.0, 1.0, t)
            flare = 1.28 - 0.20 * t
        else:                                           # RECOVERY
            t = A._ease_in_out((ap - follow) / max(1e-6, 1.0 - follow))
            ang = A._lerp(A.SWING_ARC_END * 0.72, 0.30, t)
            rad = A._lerp(A.SWING_R_FOLLOW, A.SWING_R_REST, t)
            lean = A._lerp(3.0, 0.0, t)
            bob = A._lerp(1.0, 0.0, t)
            flare = A._lerp(1.08, 1.0, t)
        return {"angle": ang, "radius": rad, "lean": lean,
                "bob": bob, "flare": flare}

    def _bow_pose_local(action="idle", ap=0.0, wave=0.0):
        """(grip, tilt, draw_amt) busur di ruang lokal rig.

        Satu sumber kebenaran untuk pose busur: dipakai rig saat
        menggambar DAN oleh lapisan FX hidup untuk menempelkan trail /
        titik lepas panah tepat di senjata (bukan perkiraan).
        """
        A = _NS_sylara
        ap = max(0.0, min(1.0, float(ap)))
        if action == "swing":
            pose = A._swing_arc_pose(ap)
            ang, rad = pose["angle"], pose["radius"]
            px, py = A.SHOULDER_PIVOT
            grip = (px + math.cos(ang) * rad, py + math.sin(ang) * rad)
            # bidang busur tegak lurus lintasan sapuan -> limb memimpin
            return grip, ang + 1.40, 0.0
        if action == "attack":
            # 7-keyframe: rest -> wind-up -> tension -> full draw ->
            # IMPACT release -> follow-through -> rest (loop-closure).
            if ap < 0.12:
                t = A._ease_in_out(ap / 0.12)
                return (19 - t * 1, -14 - t * 2), .30 - t * .10, 0.22 * t
            if ap < 0.26:
                t = A._ease_in_out((ap - 0.12) / 0.14)
                return ((18 - t * 2, -16 - t * 2), .20 - t * .10,
                        0.22 + 0.48 * t)
            if ap < 0.42:
                t = A._ease_in_out((ap - 0.26) / 0.16)
                return ((16 - t * 1, -18), .10 - t * .06, 0.70 + 0.30 * t)
            if ap < 0.52:
                return (15, -18), .04, 1.0
            if ap < 0.58:
                t = (ap - 0.52) / 0.06
                return ((15 + t * 4, -18 + t * 4), .04,
                        max(0.0, 1.0 - t * 1.6))
            if ap < 0.72:
                t = A._ease_in_out((ap - 0.58) / 0.14)
                return (19 - t * 1, -14 + t * 2), .04 + t * .18, 0.0
            t = A._ease_in_out((ap - 0.72) / 0.28)
            return (18 - t * 1, -12 + t * 7), .22 + t * .04, 0.0
        if action == "windrun":
            return (13, -2), 1.25, 0.0
        return (17, -5 + wave), .26 + wave * .05, 0.0

    def _bow_geometry(phase=0.0, action="idle", attack_progress=0.0):
        """Semua titik penting busur (lokal): grip, tilt, tips, nock.

        Ujung limb memakai kurva yang sama dengan ``_draw_elite_bow``
        (u = +-24, v = 8s^2 - 14s^4 - flex) supaya penanda FX benar-benar
        menempel di kayu, bukan mengambang di dekatnya.
        """
        A = _NS_sylara
        wave = math.sin(float(phase) * 1.15)
        grip, tilt, draw_amt = A._bow_pose_local(action, attack_progress,
                                                 wave)
        flex = draw_amt * 0.55
        v_tip = 8.0 - 14.0 - flex * 6.0        # s = 1.0 pada ujung limb
        tip_up = A._bow_point(grip, tilt, 24.0, v_tip)
        tip_low = A._bow_point(grip, tilt, -24.0, v_tip)
        nock = A._bow_nock(grip, tilt, draw_amt)
        (_ux, _uy), (fx, fy) = A._bow_frame(tilt)
        arrow_tip = (nock[0] + fx * 32.0, nock[1] + fy * 32.0)
        return {"grip": grip, "tilt": tilt, "draw": draw_amt,
                "tip_up": tip_up, "tip_low": tip_low, "nock": nock,
                "arrow_tip": arrow_tip}

    def _bow_grip_local(phase=0.0, action="idle", attack_progress=0.0):
        """Titik grip busur (lokal) — dipakai lapisan FX & debug."""
        return _NS_sylara._bow_geometry(phase, action,
                                        attack_progress)["grip"]

    def _bow_tip_local(phase=0.0, action="idle", attack_progress=0.0):
        """Ujung limb ATAS busur (lokal) — ujung 'bilah' saat menyapu."""
        return _NS_sylara._bow_geometry(phase, action,
                                        attack_progress)["tip_up"]

    def _bow_nock_local(phase=0.0, action="idle", attack_progress=0.0):
        """Titik nock/lepas panah (lokal)."""
        return _NS_sylara._bow_geometry(phase, action,
                                        attack_progress)["nock"]

    def _bow_release_local(phase=0.0, attack_progress=0.0):
        """Titik keluar panah (ujung mata panah pada saat release)."""
        return _NS_sylara._bow_geometry(phase, "attack",
                                        attack_progress)["arrow_tip"]

    def _bow_trail_samples(phase, attack_progress, count=10,
                           action="swing", span=0.16):
        """Histori posisi senjata untuk trail: [(base, tip), ...] lokal.

        Sample diambil MUNDUR dari progress sekarang (OLD -> CURRENT)
        sehingga pita selalu mengikuti arah serangan, apa pun arah
        ayunannya.
        """
        A = _NS_sylara
        out = []
        n = max(2, int(count))
        for i in range(n):
            t = attack_progress - span * (1.0 - i / float(n - 1))
            if t < 0.0:
                t = 0.0
            g = A._bow_geometry(phase, action, t)
            out.append((g["grip"], g["tip_up"]))
        return out

    def _draw_bow_swing_trail(surface, pt, phase, attack_progress,
                              alpha_scale=1.0):
        """Pita sapuan busur di CANVAS (fallback tanpa lapisan hidup).

        Dipakai jalur boss / tooling / perangkat tanpa modul FX; kalau
        ``heroes/sylara_fx.py`` aktif, ia menggambar versi 60 fps di
        layar dan fungsi ini dilewati supaya tidak dobel.
        """
        A = _NS_sylara
        p = A.PALETTE
        samples = A._bow_trail_samples(phase, attack_progress, count=9)
        n = len(samples)
        if n < 2:
            return
        for i in range(n - 1):
            f = (i + 1) / float(n)
            a = int(150 * f * f * alpha_scale)
            if a <= 6:
                continue
            (g0, t0), (g1, t1) = samples[i], samples[i + 1]
            m0 = (g0[0] + (t0[0] - g0[0]) * 0.42,
                  g0[1] + (t0[1] - g0[1]) * 0.42)
            m1 = (g1[0] + (t1[0] - g1[0]) * 0.42,
                  g1[1] + (t1[1] - g1[1]) * 0.42)
            A._poly(surface, (*p["wind_dark"], a),
                    [pt(*m0), pt(*t0), pt(*t1), pt(*m1)])
            m0 = (g0[0] + (t0[0] - g0[0]) * 0.74,
                  g0[1] + (t0[1] - g0[1]) * 0.74)
            m1 = (g1[0] + (t1[0] - g1[0]) * 0.74,
                  g1[1] + (t1[1] - g1[1]) * 0.74)
            A._poly(surface, (*p["wind_light"], min(255, int(a * 1.5))),
                    [pt(*m0), pt(*t0), pt(*t1), pt(*m1)])
            A._aaline(surface, (*p["wind_white"], min(255, int(a * 1.7))),
                      pt(*t0), pt(*t1), 2)

    # ── ANIMATION CONTROLLER (state + prioritas + transisi) ─────────
    def _resolve_anim_state(boss, attacking, phase):
        """Tentukan state animasi yang DIINGINKAN frame ini."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_sy_hurt_frames", 0) or 0) > 0:
            return "HURT"
        if getattr(boss, "_powershot_charging", False) and not attacking:
            return "CHARGE"
        skill = getattr(boss, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if attacking:
            if phase in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if phase in ("SWING", "IMPACT"):
                return "SWING" if getattr(boss, "_sy_swing_mode", False) \
                    else "ATTACK"
            return "ATTACK"
        if getattr(boss, "_windrun_active", False):
            return "RUN"
        if getattr(boss, "_moving_cached", False):
            return "RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2 \
                else "WALK"
        return "IDLE"

    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox sapuan (canvas-space) saat jendela hit aktif.

        Return None kalau jendela hit sedang tidak aktif.  Dipakai
        overlay debug dan (opsional) sistem tumbukan.
        """
        if not getattr(boss, "_sy_hit_active", False):
            return None
        f = 1 if getattr(boss, "direction", 1) >= 0 else -1
        reach = 70
        left = cx if f > 0 else cx - reach
        return pygame.Rect(int(left), int(cy - 52), reach, 74)

    def _draw_debug(surface, boss, x, y, state):
        """Overlay debug rig: hurtbox, hitbox, jangkauan, state, timer."""
        A = _NS_sylara
        pygame.draw.rect(surface, (90, 220, 255),
                         pygame.Rect(int(x - 30), int(y - 96), 62, 150), 1)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        reach = int(float(getattr(boss, "range", 130)) / max(0.05, scale))
        pygame.draw.circle(surface, (255, 190, 90), (int(x), int(y)),
                           min(reach, 900), 1)
        swing_r = int(A.SWING_RANGE / max(0.05, scale))
        pygame.draw.circle(surface, (255, 120, 120), (int(x), int(y)),
                           min(swing_r, 900), 1)
        box = A._swing_hitbox(boss, x, y)
        if box is not None:
            pygame.draw.rect(surface, (255, 230, 90), box, 2)
        # penanda ujung busur + titik lepas panah
        f = 1 if getattr(boss, "direction", 1) >= 0 else -1
        rs = A.RIG_SCALE
        ap = float(getattr(boss, "_sy_attack_progress", 0.0))
        action = "swing" if getattr(boss, "_sy_swing_mode", False) \
            else "attack"
        if not getattr(boss, "_sy_attack_active", False):
            action = "idle"
            ap = 0.0
        geo = A._bow_geometry(float(getattr(boss, "pulse", 0.0)),
                              action, ap)
        for key, col in (("tip_up", (120, 255, 150)),
                         ("nock", (255, 255, 120))):
            lx, ly = geo[key]
            pygame.draw.circle(
                surface, col,
                (int(x + lx * rs * f), int(y + ly * rs)), 3, 1)
        # bar progress serangan + indikator state
        bar = pygame.Rect(int(x - 40), int(y - 110), 80, 5)
        pygame.draw.rect(surface, (12, 30, 16), bar)
        pygame.draw.rect(surface, (150, 235, 120),
                         (bar.x, bar.y, int(80 * ap), 5))
        idx = list(A.ANIM_STATES).index(state) \
            if state in A.ANIM_STATES else 0
        pygame.draw.rect(surface, (210, 255, 175),
                         (bar.x, bar.y - 6, 4 + idx * 5, 4))
        # proyektil renderer (kalau ada) — lingkaran tumbukan
        for pr in list(getattr(boss, "_sy_projectiles", []) or []):
            try:
                pygame.draw.circle(surface, (255, 255, 120),
                                   (int(pr.x), int(pr.y)), 5, 1)
            except Exception:
                pass

    def _fx_scale(hero):
        """Faktor kompensasi efek skill.

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek (cincin, retakan, partikel) ikut menyusut sampai
        ~40%.  Dengan faktor ini efek digambar lebih besar di canvas
        sehingga ukurannya DI LAYAR setara boss asli (world-space).
        Boss asli (tanpa _render_scale) = 1.0.  Cap 2.6 menjaga efek
        tetap muat di canvas cache.
        """
        scale = getattr(hero, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(hero, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam canvas.

        Memastikan telegraph tidak keluar dari cache canvas (efek
        terpotong = garis aneh di tepi hero).
        """
        scale = getattr(hero, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=2, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_sylara._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_sylara._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_sylara._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=5, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_sylara._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_sylara._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55      # perspektif tanah
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_sylara._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_sylara._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    # -------------------------------------------------------------------
    # SKILL FX — DRAKAR-STYLE PRIMITIVES (bahasa visual boss Drakar,
    # dipindahkan ke palet angin Sylara):
    #   * crescent tebal berlapis 5-band, ekor memudar + kilau di tip
    #   * spatter piksel (rect 3 ukuran + core hot)
    #   * shockwave tanah 3-ellipse berlapis
    #   * charge orb cincin konsentris -> inti putih
    #   * rune ring: ellipse berlapis + spoke berputar + titik hot
    #   * ghost afterimage 3 lapis + ember naik
    # pygame.draw.* menulis alpha langsung pada surface SRCALPHA, jadi
    # tidak ada surface sementara per primitif (ramah cache-miss).
    # -------------------------------------------------------------------
    def _drk_alpha(alpha):
        return max(0, min(255, int(alpha)))

    def _drk_line(surface, a, b, thick, alpha, hot=True, core=False):
        """Garis berlapis gaya Drakar: outline gelap -> mid -> hot -> shine."""
        p = _NS_sylara.PALETTE
        al = _NS_sylara._drk_alpha(alpha)
        if al <= 0:
            return
        W = max(2, int(thick))
        pygame.draw.line(surface, (*p["wind_darkest"], al), a, b, W + 4)
        pygame.draw.line(surface, (*p["wind_dark"], int(al * .95)), a, b, W + 2)
        pygame.draw.line(surface, (*p["wind_mid"], al), a, b, W)
        pygame.draw.line(surface, (*p["wind_light"], al), a, b, max(1, W - 2))
        if hot:
            pygame.draw.line(surface, (*p["wind_bright"], al), a, b, 2)
        if core:
            pygame.draw.line(surface, (*p["white"], int(al * .9)), a, b, 1)

    def _drk_crescent(surface, cx, cy, radius, start, span, alpha,
                      squash=1.0, thick=9, arms=1):
        """Crescent berputar gaya Counter Helix: ekor memudar + tip kilau."""
        p = _NS_sylara.PALETTE
        steps = 14
        for arm in range(arms):
            a0 = start + arm * math.pi / max(1, arms)
            for k in range(steps):
                t0 = k / float(steps)
                t1 = (k + 1) / float(steps)
                fade = (1.0 - t0) ** 1.4
                al = _NS_sylara._drk_alpha(alpha * fade)
                if al <= 0:
                    continue
                ang0 = a0 + span * t0
                ang1 = a0 + span * t1
                c0 = (cx + math.cos(ang0) * radius,
                      cy + math.sin(ang0) * radius * squash)
                c1 = (cx + math.cos(ang1) * radius,
                      cy + math.sin(ang1) * radius * squash)
                _NS_sylara._drk_line(surface, c0, c1,
                                     thick * (0.4 + 0.6 * fade), al)
            # ujung (tip) menyala — kunci baca Drakar
            ta = a0 + span
            tpx = int(cx + math.cos(ta) * radius)
            tpy = int(cy + math.sin(ta) * radius * squash)
            pygame.draw.circle(surface, (*p["wind_bright"], _NS_sylara._drk_alpha(alpha)),
                               (tpx, tpy), max(2, int(thick * .55)))
            pygame.draw.circle(surface, (*p["white"], _NS_sylara._drk_alpha(alpha * .9)),
                               (tpx, tpy), max(1, int(thick * .28)))

    def _drk_spatter(surface, cx, cy, count, spread, phase, alpha,
                     seed=0, squash=0.62):
        """Spatter piksel radial gaya Drakar (rect 3 ukuran + core hot)."""
        p = _NS_sylara.PALETTE
        for i in range(count):
            ang = phase * 0.35 + i * math.tau / count
            dist = spread * (0.35 + 0.65 * _NS_sylara._hash01(seed + i * 7))
            px = int(cx + math.cos(ang) * dist)
            py = int(cy + math.sin(ang) * dist * squash)
            al = _NS_sylara._drk_alpha(
                alpha * (0.55 + 0.45 * _NS_sylara._hash01(seed + i * 13)))
            if al <= 0:
                continue
            pygame.draw.rect(surface, (*p["wind_dark"], al), (px - 1, py - 1, 3, 3))
            pygame.draw.rect(surface, (*p["wind_mid"], al), (px, py, 2, 2))
            pygame.draw.rect(surface, (*p["wind_bright"], al), (px + 1, py, 1, 1))

    def _drk_shock(surface, cx, cy, radius, alpha, squash=0.62):
        """Shockwave tanah 3 ellipse berlapis (aktivasi skill, gaya Drakar)."""
        p = _NS_sylara.PALETTE
        al = _NS_sylara._drk_alpha(alpha)
        if al <= 0:
            return
        rr = max(4, int(radius))
        ry = max(2, int(rr * squash))
        pygame.draw.ellipse(surface, (*p["wind_darkest"], al),
                            (cx - rr, cy - ry, rr * 2, ry * 2), 4)
        pygame.draw.ellipse(surface, (*p["wind_dark"], int(al * .9)),
                            (cx - rr + 5, cy - ry + 4, rr * 2 - 10, ry * 2 - 8), 3)
        pygame.draw.ellipse(surface, (*p["wind_mid"], int(al * .8)),
                            (cx - rr + 10, cy - ry + 7, rr * 2 - 20, ry * 2 - 14), 2)
        pygame.draw.ellipse(surface, (*p["wind_light"], int(al * .7)),
                            (cx - rr + 14, cy - ry + 9, rr * 2 - 28, ry * 2 - 18), 1)

    def _drk_orb(surface, cx, cy, radius, alpha):
        """Charge orb gaya Culling Blade: cincin konsentris -> inti putih."""
        p = _NS_sylara.PALETTE
        al = _NS_sylara._drk_alpha(alpha)
        if al <= 0:
            return
        r = max(1, int(radius))
        for rr, col, am in ((r, p["wind_darkest"], .65),
                            (r - 1, p["wind_dark"], .85),
                            (r - 2, p["wind_mid"], 1.0),
                            (r - 3, p["wind_light"], 1.0),
                            (r - 4, p["wind_bright"], 1.0)):
            if rr > 0:
                pygame.draw.circle(surface, (*col, int(al * am)), (cx, cy), rr)
        pygame.draw.circle(surface, (*p["white"], al), (cx, cy), max(1, r - 6))

    def _drk_cracks(surface, cx, cy, count, length, phase, alpha,
                    seed=0, squash=0.5):
        """Retakan tanah zigzag 3 lapis (impact / telegraph, gaya Drakar)."""
        p = _NS_sylara.PALETTE
        for i in range(count):
            ang = phase * 0.2 + i * math.tau / count + 0.35
            ln = length * (0.75 + 0.25 * _NS_sylara._hash01(seed + i * 11))
            x, y, a = float(cx), float(cy), ang
            pts = [(x, y)]
            for seg in range(4):
                a += (_NS_sylara._hash01(seed * 7 + seg * 13 + i) - .5) * .7
                x += math.cos(a) * ln / 4.0
                y += math.sin(a) * ln / 4.0 * squash
                pts.append((x, y))
            for k in range(len(pts) - 1):
                al = _NS_sylara._drk_alpha(alpha * (1 - k * 0.15))
                if al <= 0:
                    continue
                pygame.draw.line(surface, (*p["wind_darkest"], al),
                                 pts[k], pts[k + 1], 3)
                pygame.draw.line(surface, (*p["wind_mid"], al),
                                 pts[k], pts[k + 1], 2)
                pygame.draw.line(surface, (*p["wind_bright"], al),
                                 pts[k], pts[k + 1], 1)

    def _drk_rune_ring(surface, cx, cy, rx, ry, phase, alpha, spokes=12):
        """Rune ring gaya ground Drakar: ellipse berlapis + spoke berputar
        + titik hot di ujung spoke."""
        p = _NS_sylara.PALETTE
        al = _NS_sylara._drk_alpha(alpha)
        if al <= 0:
            return
        rx, ry = max(6, int(rx)), max(3, int(ry))
        pygame.draw.ellipse(surface, (*p["wind_darkest"], al),
                            (cx - rx, cy - ry, rx * 2, ry * 2), 4)
        pygame.draw.ellipse(surface, (*p["wind_dark"], int(al * .9)),
                            (cx - rx + 4, cy - ry + 3, rx * 2 - 8, ry * 2 - 6), 3)
        pygame.draw.ellipse(surface, (*p["wind_mid"], int(al * .8)),
                            (cx - rx + 8, cy - ry + 5, rx * 2 - 16, ry * 2 - 10), 2)
        inner = 0.55
        for i in range(spokes):
            a = phase + i * math.tau / spokes
            x1 = cx + math.cos(a) * rx * inner
            y1 = cy + math.sin(a) * ry * inner
            x2 = cx + math.cos(a) * rx
            y2 = cy + math.sin(a) * ry
            pygame.draw.line(surface, (*p["wind_light"], int(al * .85)),
                             (x1, y1), (x2, y2), 2)
            pygame.draw.rect(surface, (*p["wind_bright"], al),
                             (int(x2) - 1, int(y2) - 1, 3, 3))
            pygame.draw.rect(surface, (*p["white"], al), (int(x2), int(y2), 1, 1))

    def _drk_ghost(surface, cx, cy, radius, alpha):
        """Ghost afterimage melingkar 3 lapis (trail, gaya rage-mist Drakar)."""
        p = _NS_sylara.PALETTE
        al = _NS_sylara._drk_alpha(alpha)
        if al <= 0:
            return
        r = max(2, int(radius))
        pygame.draw.circle(surface, (*p["wind_darkest"], int(al * .5)),
                           (cx, cy), r + 3)
        pygame.draw.circle(surface, (*p["wind_dark"], al), (cx, cy), r)
        pygame.draw.circle(surface, (*p["wind_mid"], al), (cx, cy), max(1, r - 3))
        pygame.draw.circle(surface, (*p["wind_bright"], al), (cx, cy), max(1, r - 6))
        pygame.draw.rect(surface, (*p["wind_light"], al), (cx - 1, cy - 1, 3, 3))
        pygame.draw.rect(surface, (*p["white"], al), (cx, cy, 1, 1))

    def _drk_embers(surface, cx, cy, count, phase, alpha,
                    spread=44, rise=46, squash=0.5):
        """Ember naik piksel (rect berlapis) — rage-mist versi angin."""
        p = _NS_sylara.PALETTE
        for i in range(count):
            t = (phase * 0.4 + i * 0.11) % 1.0
            ang = phase * 0.3 + i * math.tau / count
            sx = cx + math.cos(ang) * spread * \
                (0.6 + 0.4 * _NS_sylara._hash01(i * 5))
            sy = cy - int(t * rise) + \
                math.sin(ang) * spread * squash * 0.3
            al = _NS_sylara._drk_alpha(alpha * (1 - t))
            if al <= 0:
                continue
            pygame.draw.rect(surface, (*p["wind_dark"], al),
                             (int(sx) - 1, int(sy) - 1, 3, 3))
            pygame.draw.rect(surface, (*p["wind_mid"], al),
                             (int(sx), int(sy), 2, 2))
            pygame.draw.rect(surface, (*p["wind_bright"], al),
                             (int(sx), int(sy) - 1, 1, 1))

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bergerigi (bulu/roban pixel-art).

        Deterministik (hash) — aman untuk cache.
        """
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by - ay), -(bx - ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            for j in range(n):
                t = (j + 0.5) / n
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 * _NS_sylara._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Wind Arrow
    # ---------------------------------------------------------------------------
    def _drk_mix(c1, c2, t):
        """Lerp warna (gradasi shaft panah mewah)."""
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    def _drk_sparkle(surface, cx, cy, r, alpha, rot=0.0):
        """Kilau bintang 4-sinar + palang diagonal (glint mewah)."""
        p = _NS_sylara.PALETTE
        al = _NS_sylara._drk_alpha(alpha)
        if al <= 0:
            return
        for k in range(4):
            a = rot + k * math.pi / 2
            ex = cx + math.cos(a) * r
            ey = cy + math.sin(a) * r
            pygame.draw.line(surface, (*p["wind_bright"], int(al * .55)),
                             (cx, cy), (ex, ey), 1)
        d = r * 0.45
        pygame.draw.line(surface, (*p["wind_light"], int(al * .8)),
                         (cx - d, cy - d), (cx + d, cy + d), 1)
        pygame.draw.line(surface, (*p["wind_light"], int(al * .8)),
                         (cx - d, cy + d), (cx + d, cy - d), 1)
        pygame.draw.circle(surface, (*p["white"], al),
                           (int(cx), int(cy)), max(1, int(r * 0.30)))

    def _drk_arrow_trail(surface, trail, angle, phase, alpha_scale=1.0,
                         powered=False, bind=False):
        """EKOR COMET MEWAH (bukan lingkaran / garis chevron):
        pita berlapis yang menirus + wisp angin melengkung + kilau
        bintang. bind=True menambah strand vine yang berpilin (E)."""
        n = len(trail)
        if n < 2:
            return
        p = _NS_sylara.PALETTE
        ca, sa = math.cos(angle), math.sin(angle)
        nx, ny = -sa, ca
        wmax = 10.0 if powered else 6.5
        amax = 245 if powered else 210

        # 1) PITA comet: 2 lapis garis menirus (glow luar + ribbon)
        for i in range(1, n):
            t0 = i / float(n)                 # 1 = dekat panah
            fade = t0 ** 1.25
            w = max(0.8, wmax * (0.30 + 0.70 * fade))
            al = _NS_sylara._drk_alpha(amax * fade * alpha_scale)
            if al <= 0:
                continue
            a, b = trail[i - 1], trail[i]
            _NS_sylara._drk_line(surface, a, b, w + 2.2,
                                 int(al * .45), hot=False)
            _NS_sylara._drk_line(surface, a, b, w, al,
                                 hot=(i % 3 == 0), core=(i >= n - 3))

        if bind:
            # 2) Strand vine berpilin AROUND pita (Shackle) — 2 helai
            for side in (-1.0, 1.0):
                pts = []
                for i in range(n):
                    t0 = i / float(max(1, n - 1))
                    x, y = trail[i]
                    wob = math.sin(phase * 3.2 + i * 0.9 +
                                   (math.pi if side > 0 else 0.0))
                    off = wob * (2.0 + 3.2 * t0)
                    pts.append((x + nx * off, y + ny * off))
                for i in range(1, len(pts)):
                    t0 = i / float(max(1, len(pts) - 1))
                    al = _NS_sylara._drk_alpha(
                        185 * (t0 ** 1.1) * alpha_scale)
                    if al <= 0:
                        continue
                    _NS_sylara._drk_line(surface, pts[i - 1], pts[i],
                                         1.7, al, hot=True)
                    if i % 3 == 0:
                        pygame.draw.circle(surface, (*p["wind_white"], al),
                                           (int(pts[i][0]), int(pts[i][1])), 1)
        else:
            # 2) Wisp angin MELENGKUNG (bukan chevron lurus): busur
            #    pendek yang menekuk ke belakang, selang-seling kiri/kanan
            for i in range(1, n, 2):
                t0 = i / float(n)
                fade = t0 ** 1.1
                x, y = trail[i]
                wob = math.sin(phase * 2.4 + i * 0.6) * (2.6 + 3.6 * fade)
                bs = (3.0 + 3.0 * fade) if powered else (2.0 + 2.6 * fade)
                bx = x - ca * bs
                by = y - sa * bs
                mx = (bx + x) * 0.5 + nx * wob * 0.55
                my = (by + y) * 0.5 + ny * wob * 0.55
                tx = x + nx * (wob + 2.6)
                ty = y + ny * (wob + 2.6)
                al = _NS_sylara._drk_alpha(165 * fade * alpha_scale)
                if al <= 0:
                    continue
                _NS_sylara._drk_line(surface, (bx, by), (mx, my),
                                     1.4, int(al * .8))
                _NS_sylara._drk_line(surface, (mx, my), (tx, ty),
                                     1.7, al, hot=True)

        # 3) Kilau bintang di beberapa titik pita (dekat panah)
        for i in range(max(2, n - 6), n, 2):
            t0 = i / float(n)
            if t0 < 0.55:
                continue
            x, y = trail[i]
            _NS_sylara._drk_sparkle(
                surface, x, y, 2.4 + 2.4 * t0,
                int(215 * t0 * alpha_scale), phase + i * 0.7)
            if i % 2 == 0:
                pygame.draw.circle(surface, (*p["leaf_gold"], int(180 * t0)),
                                   (int(x + nx * 3), int(y + ny * 3)), 1)

    def _drk_arrow(surface, px, py, angle, length, phase,
                   charged=False, bind=False):
        """Panah FISIK mewah: shaft gradasi energi (gelap->terang) +
        ridge putih, kepala barbed 3-lapis + glint, fletching berserat
        + nock menyala. charged=Powershot (corona arc + spark orbit),
        bind=Shackle (braid vine + node)."""
        p = _NS_sylara.PALETTE
        ca, sa = math.cos(angle), math.sin(angle)
        nx, ny = -sa, ca

        def T(f, s):
            return (px + ca * f + nx * s, py + sa * f + ny * s)

        L = float(length)
        tip = L * 0.5
        tail = -L * 0.5
        hl = L * 0.30          # kepala
        hw = L * 0.135         # setengah lebar barb
        sw = max(1.1, L * 0.040)   # setengah tebal shaft
        fl = L * 0.30          # panjang fletching
        fw = L * 0.115         # setengah lebar fletching
        neck = tip - hl
        shaft_a = tail + fl * 0.40

        # ── GLOW energi lembut di belakang seluruh badan ──
        _NS_sylara._drk_line(surface, T(shaft_a, 0), T(neck, 0),
                             13, 70, hot=False)
        _NS_sylara._drk_line(surface, T(shaft_a, 0), T(neck, 0),
                             8, 120, hot=False)

        # ── SHAFT gradasi 6 segmen: gelap ekor -> terang ke kepala ──
        segs = 6
        for i in range(segs):
            f0 = shaft_a + (neck - shaft_a) * i / segs
            f1 = shaft_a + (neck - shaft_a) * (i + 1) / segs
            t = i / float(max(1, segs - 1))
            col = _NS_sylara._drk_mix(p["wind_dark"], p["wind_bright"],
                                      t * 0.9)
            pygame.draw.line(surface, (*col, 255), T(f0, 0), T(f1, 0),
                             max(2, int(sw * 2)))
        # outline tipis gelap + ridge putih
        _NS_sylara._aaline(surface, (*p["wind_darkest"], 210),
                           T(shaft_a, -sw - .6), T(neck, -sw - .6), 1)
        _NS_sylara._aaline(surface, (*p["wind_darkest"], 210),
                           T(shaft_a, sw + .6), T(neck, sw + .6), 1)
        _NS_sylara._aaline(surface, (*p["wind_white"], 235),
                           T(shaft_a, 0), T(neck, 0), 1)

        # ── KEPALA barbed 3 lapis (siluet -> isi -> inti terang) ──
        _NS_sylara._poly(surface, p["arrow_head_d"], [
            T(tip, 0),
            T(neck + 1.5, -hw), T(neck + hl * 0.34, -hw * 0.48),
            T(neck + 0.6, 0),
            T(neck + hl * 0.34, hw * 0.48), T(neck + 1.5, hw)])
        _NS_sylara._poly(surface, p["arrow_head"], [
            T(tip - 0.5, 0),
            T(neck + 2.0, -hw * 0.62), T(neck + hl * 0.36, -hw * 0.30),
            T(neck + 1.2, 0),
            T(neck + hl * 0.36, hw * 0.30), T(neck + 2.0, hw * 0.62)])
        _NS_sylara._poly(surface, (*p["wind_light"], 220), [
            T(tip - 1.0, 0),
            T(neck + 2.6, -hw * 0.34), T(neck + 1.8, 0),
            T(neck + 2.6, hw * 0.34)])
        _NS_sylara._aaline(surface, p["white"],
                           T(tip, 0), T(neck + 2.0, 0), 1)
        tp = T(tip, 0)
        _NS_sylara._drk_sparkle(surface, tp[0], tp[1],
                                max(2.2, L * 0.075), 240,
                                phase * 1.5)

        # ── FLETCHING berserat: 2 sayap, siluet -> isi -> garis tepi ──
        for s in (-1.0, 1.0):
            _NS_sylara._poly(surface, p["arrow_feather_d"], [
                T(tail, 0), T(tail + 1.0, s * fw),
                T(tail + fl * 0.30, s * fw * 1.05),
                T(tail + fl * 0.50, s * fw * 0.55),
                T(tail + fl * 0.76, s * fw * 0.92),
                T(tail + fl, 0)])
            _NS_sylara._poly(surface, p["arrow_feather"], [
                T(tail + 1.2, 0), T(tail + 1.8, s * fw * 0.70),
                T(tail + fl * 0.32, s * fw * 0.68),
                T(tail + fl * 0.50, s * fw * 0.34),
                T(tail + fl * 0.76, s * fw * 0.58),
                T(tail + fl * 0.88, 0)])
            _NS_sylara._aaline(surface, (*p["wind_white"], 200),
                               T(tail + 1.4, 0),
                               T(tail + fl * 0.68, s * fw * 0.62), 1)
            # tepi bergerigi (2 notch)
            for k in (0.34, 0.66):
                nf = tail + fl * k
                _NS_sylara._aaline(surface, (*p["wind_white"], 150),
                                   T(nf, s * fw * 0.8),
                                   T(nf + 1.0, s * fw * 0.52), 1)

        # ── NOCK menyala (diamond + orb pulse) ──
        _NS_sylara._poly(surface, (*p["wind_bright"], 235), [
            T(tail - 2.2, 0), T(tail - 1.0, -sw * 0.8),
            T(tail, 0), T(tail - 1.0, sw * 0.8)])
        pygame.draw.circle(surface, (*p["wind_light"], 210),
                           (int(T(tail - 1.5, 0)[0]), int(T(tail - 1.5, 0)[1])), 2)
        pygame.draw.circle(surface, (*p["white"], 255),
                           (int(T(tail - 1.5, 0)[0]), int(T(tail - 1.5, 0)[1])), 1)

        if bind:
            # ── BRAID VINE 2 helai berpilin di sepanjang shaft ──
            for side in (-1.0, 1.0):
                pts = []
                steps = 9
                for i in range(steps):
                    t = i / float(steps - 1)
                    f = shaft_a + (neck - shaft_a) * t
                    a = phase * 6 + t * 4.4 + (math.pi if side > 0 else 0)
                    pts.append(T(f, math.cos(a) * (sw + 2.0)))
                for i in range(1, len(pts)):
                    al = _NS_sylara._drk_alpha(210)
                    _NS_sylara._drk_line(surface, pts[i - 1], pts[i],
                                         1.8, al, hot=True)
                    if i % 2 == 0:
                        pygame.draw.circle(surface, (*p["wind_white"], 235),
                                           (int(pts[i][0]), int(pts[i][1])), 1)

        if charged:
            # ── CORONA: 2 arc energi berputar DI DEPAN panah ──
            _NS_sylara._drk_crescent(
                surface, px, py, L * 0.44, phase * 2.1, 1.7,
                215, squash=1.0, thick=5, arms=2)
            # spark orbit mengelilingi shaft
            for i in range(5):
                a = phase * 2.5 + i * math.tau / 5
                sx, sy = T(0, math.cos(a) * L * 0.30)
                pygame.draw.circle(surface, (*p["wind_bright"], 235),
                                   (int(sx), int(sy)), 2)
                pygame.draw.circle(surface, (*p["white"], 255),
                                   (int(sx), int(sy)), 1)
            # kilau ekstra di ujung
            _NS_sylara._drk_sparkle(surface, px + ca * L * 0.42,
                                    py + sa * L * 0.42,
                                    L * 0.10, 230, -phase * 1.8)


    class WindArrowProjectile:
        """Basic wind arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=9.0, powered=False,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.powered = powered  # Powershot variant
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            # Homing: target/damage/team (visual-only; damage otoritatif
            # ada di hero_skills). Kalau target hidup, kejar tiap frame.
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target yang bergerak (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_sylara._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            max_trail = 18 if self.powered else 8
            if len(self.trail) > max_trail:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            powered = self.powered

            # ── EKOR COMET (pita menirus + wisp melengkung + kilau) ──
            _NS_sylara._drk_arrow_trail(surface, self.trail, self.angle,
                                        phase, powered=powered)

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                if powered:
                    # ═══ POWERSHOT: panah raksasa + orb/rune di belakang,
                    #    corona arc di depan (gaya Culling Blade) ═══
                    bx = px - ca * 18
                    by = py - sa * 18
                    _NS_sylara._drk_orb(surface, int(bx), int(by), 10,
                                        200 + int(25 * math.sin(phase * 5)))
                    _NS_sylara._drk_rune_ring(
                        surface, int(bx), int(by), 15, 15, phase * 2.4,
                        int(130 + 35 * math.sin(phase * 4)), spokes=8)
                    _NS_sylara._drk_arrow(surface, px, py, self.angle,
                                          54, phase, charged=True)
                else:
                    # ═══ PANAH BASIC: panah fisik megah + 2 kilau orbit ═══
                    _NS_sylara._drk_arrow(surface, px, py, self.angle,
                                          46, phase)
                    for i in range(2):
                        a = phase * 4 + i * math.pi
                        sx = px + ca * math.cos(a) * 9
                        sy = py + sa * math.cos(a) * 9
                        _NS_sylara._drk_sparkle(surface, sx, sy, 2.2,
                                                190, phase * 2 + i)


    class ShackleProjectile:
        """Shackle shot - arrow that binds enemies with vines/wind."""
        def __init__(self, sx, sy, tx, ty, speed=8.0,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_sylara._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            # ── EKOR COMET + strand vine berpilin (binding) ──
            _NS_sylara._drk_arrow_trail(surface, self.trail, self.angle,
                                        phase, bind=True)

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                # Orb binding di BELAKANG panah + rune ring
                bx = px - ca * 15
                by = py - sa * 15
                _NS_sylara._drk_orb(surface, int(bx), int(by), 7,
                                    185 + int(25 * math.sin(phase * 6)))
                _NS_sylara._drk_rune_ring(
                    surface, int(bx), int(by), 11, 11, phase * 2.6,
                    int(115 + 35 * math.sin(phase * 5)), spokes=5)

                # Panah fisik besar + braid vine menyala di shaft
                _NS_sylara._drk_arrow(surface, px, py, self.angle,
                                      50, phase, bind=True)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_sy_last_x"):
            boss._sy_last_x = boss.x
            boss._sy_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sy_last_x)
        dy = abs(boss.y - boss._sy_last_y)
        boss._sy_last_x = boss.x
        boss._sy_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track bow attack animation timeline (draw + release)."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sy_prev_timer", -1))
        active = bool(getattr(boss, "_sy_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._sy_attack_active = True
            active = True

        if active and timer <= 0:
            boss._sy_attack_active = False
            active = False

        boss._sy_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._sy_attack_frame = max(0, cooldown - timer) if active else 0
        progress = (
            min(1.0, boss._sy_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )
        boss._sy_attack_progress = progress

        # ═══ v3 — FASE, JENDELA HIT, MODE AYUNAN, STATE MACHINE ═══
        A = _NS_sylara
        if not active:
            phase = "NONE"
        elif progress < A.ATTACK_ANTICIPATION_END:
            phase = "ANTICIPATION"
        elif progress < A.ATTACK_WINDUP_END:
            phase = "WINDUP"
        elif progress < A.ATTACK_SWING_END:
            phase = "SWING"
        elif progress < A.ATTACK_IMPACT_END:
            phase = "IMPACT"
        elif progress < A.ATTACK_FOLLOW_END:
            phase = "FOLLOW"
        else:
            phase = "RECOVERY"
        boss._sy_attack_phase = phase

        lo, hi = A.ATTACK_ACTIVE_WINDOW
        boss._sy_hit_active = bool(active and lo <= progress < hi)

        # Mode ayunan dikunci SAAT serangan dimulai (bukan tiap frame):
        # kalau target menjauh di tengah animasi, pose tidak boleh
        # berganti di tengah jalan — itu yang membuat gerakan patah.
        if trigger or (active and not hasattr(boss, "_sy_swing_mode")):
            tgt = getattr(boss, "target", None)
            close = False
            if tgt is not None and getattr(tgt, "alive", True):
                try:
                    close = math.hypot(float(tgt.x) - float(boss.x),
                                       float(tgt.y) - float(boss.y)) \
                        <= A.SWING_RANGE
                except Exception:
                    close = False
            boss._sy_swing_mode = bool(close)
        if not active:
            boss._sy_swing_mode = False

        # Pose ayunan berbeda total dari pose tembak, jadi kunci cache
        # sprite harus ikut membedakannya (lihat heroes/__init__.py ::
        # _hero_cache_key) — tanpa ini pose bisa tertahan basi.
        boss._pose_variant = 1 if getattr(boss, "_sy_swing_mode",
                                          False) else 0

        # Hitung mundur frame HURT (di-set dari luar lewat
        # ``sylara_fx.notify_hurt`` atau deteksi HP di director).
        hurt = int(getattr(boss, "_sy_hurt_frames", 0) or 0)
        if hurt > 0:
            boss._sy_hurt_frames = hurt - 1

        # ── state machine ber-prioritas ─────────────────────────────
        want = A._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_sy_state", None)
        if cur is None:
            boss._sy_state = want
            boss._sy_state_prev = want
            boss._sy_state_time = 0.0
        else:
            dt = 1.0 / 60.0
            state_time = float(getattr(boss, "_sy_state_time", 0.0))
            if want != cur:
                cur_p = A.ANIM_STATES.get(cur, 0)
                new_p = A.ANIM_STATES.get(want, 0)
                # DEATH mengunci; selain itu prioritas sama/lebih tinggi
                # boleh mengambil alih, atau state lama sudah cukup lama
                # (mencegah pose tersangkut).
                if cur != "DEATH" and (new_p >= cur_p or state_time > 0.08):
                    boss._sy_state_prev = cur
                    boss._sy_state = want
                    boss._sy_state_time = 0.0
                else:
                    boss._sy_state_time = state_time + dt
            else:
                boss._sy_state_time = state_time + dt


    def _manage_projectiles(boss, surface, phase):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        for proj in boss._sy_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._sy_projectiles = [p for p in boss._sy_projectiles if p.alive or p.dead_frames < 8]


    def _spawn_arrow(boss, x, y, powered=False):
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        tx, ty = _NS_sylara._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Arrow spawns from bow position
        sx = x + 22 * facing
        sy = y - 8
        speed = 10.0 if powered else 8.5
        tgt = getattr(boss, "target", None)
        proj = _NS_sylara.WindArrowProjectile(
            sx, sy, tx, ty, speed=speed, powered=powered,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._sy_projectiles.append(proj)


    def _spawn_shackle(boss, x, y):
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        tx, ty = _NS_sylara._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 22 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)
        proj = _NS_sylara.ShackleProjectile(
            sx, sy, tx, ty, speed=8.0,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._sy_projectiles.append(proj)


    def _spawn_focus_fire_volley(boss, x, y):
        """Focus Fire - many arrows homing ke target (fan sangat rapat)."""
        if not hasattr(boss, "_sy_projectiles"):
            boss._sy_projectiles = []
        tx, ty = _NS_sylara._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 22 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)

        # Base angle to target
        base_angle = math.atan2(ty - sy, tx - sx)

        # Fan of 5 arrows - spread DIPERSEMPIT 0.18 -> 0.06 supaya
        # terarah, & SEMUA homing ke target yang sama.
        for i in range(5):
            spread = (i - 2) * 0.06  # angle spread (dulu 0.18)
            angle = base_angle + spread
            ex = sx + math.cos(angle) * 400
            ey = sy + math.sin(angle) * 400
            proj = _NS_sylara.WindArrowProjectile(
                sx, sy, ex, ey, speed=11.0, powered=False,
                target=tgt, damage=0, team=getattr(boss, "team", None))
            # BUGFIX (orb random pada hero): lihat _spawn_arrow.
            proj.source, proj.cx, proj.cy = boss, x, y
            boss._sy_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_sylara(surface, boss, x, y):
        """Entry point for Boss.draw().

        Urutan lapisan mengikuti kontrak render order proyek:

            GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD ->
            WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
            SKILL FX -> IMPACT FX -> DEBUG

        Trail ayunan 60 fps, partikel daun/angin, proyektil panah,
        impact, screen shake, dan hit-stop hidup di
        ``heroes/sylara_fx.py`` (lapisan layar 1:1, di luar sprite
        cache).  Semua nama publik lama tetap ada; kalau modul FX tidak
        dimuat, renderer kembali menggambar semuanya di canvas.
        """
        A = _NS_sylara
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sylara._detect_moving(boss)
        _NS_sylara._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        state = getattr(boss, "_sy_state", "IDLE")

        # Jalur hero (lane): heroes/__init__ men-set _render_scale
        # sebelum memanggil renderer ke canvas, lalu sprite hasilnya
        # DI-CACHE.  Lapisan hidup di sana digambar oleh
        # heroes/__init__ (pre/post), jadi di sini cukup dipasang
        # penanda "diambil alih".  Jalur BOSS (tanpa _render_scale)
        # dipanggil tiap frame -> lapisan hidup digambar di sini.
        hero_lane = hasattr(boss, "_render_scale")
        if not portrait_hd:
            try:
                mod = A._live_module()
                if mod is not None:
                    if hero_lane:
                        mod.attach(boss)
                    else:
                        mod.draw_ground_layer(surface, boss, x, y)
            except Exception:
                pass
        A._FX_LIVE.v = (not portrait_hd) and A._fx_live_owned(boss)

        attacking = (
            getattr(boss, "_sy_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # ---------- Background layers ----------
        # Rim-light hijau lembut memisahkan cape dan rambut merah dari
        # terrain gelap, seperti presentation sprite pada referensi.
        # Portrait LOD sengaja melewati aura/platform seukuran arena agar
        # auto-crop mengisi portrait dengan wajah & material Sylara, bukan
        # lingkaran efek 180 px.
        if not portrait_hd:
            _NS_sylara._draw_ranger_silhouette_glow(surface, x, y - 10, pulse)
            _NS_sylara._draw_wind_aura(surface, x, y, pulse)
            _NS_sylara._draw_wind_platform(surface, x, y + 58, pulse, active_skill)

        # ---------- Skill ground effects ----------
        # Q = Focus Fire, W = Windrun, E = Shackle Shot, R = Powershot
        # (sesuai hero_skills/sylara_skills.py)
        if active_skill == "e":
            _NS_sylara._draw_shackle_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_sylara._draw_focus_fire_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sylara._draw_windrun_ground(surface, boss, x, y, skill_timer, pulse)

        # Aktivasi khas ranger: hembusan daun di kaki (bukan shockwave Drakar).
        if active_skill in ("q", "w", "e", "r") and not portrait_hd:
            age = (_NS_sylara.SKILL_VISUAL_DURATION.get(active_skill, 60)
                   - skill_timer)
            if 0 <= age < 10:
                _NS_sylara._sy_leaf_burst(
                    surface, x, y + 36, age / 10.0,
                    _NS_sylara._fx_scale(boss))

        # ---------- Character body ----------
        if active_skill == "w":
            # Windrun - fast dash pose
            _NS_sylara._draw_sylara_windrun(surface, boss, x, y, skill_timer)
        elif attacking:
            _NS_sylara._draw_sylara_attack(surface, boss, x, y)
        elif moving:
            _NS_sylara._draw_sylara_walk(surface, boss, x, y)
        else:
            _NS_sylara._draw_sylara_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        if not portrait_hd:
            _NS_sylara._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "r":
            _NS_sylara._draw_powershot_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_sylara._draw_focus_fire_effect(surface, boss, x, y, skill_timer, pulse)

        # ---------- LAPISAN FX HIDUP (jalur BOSS) ----------
        # Di jalur lane hero, lapisan ini digambar heroes/__init__.py
        # SETELAH sprite di-blit (sprite-nya ter-cache); di jalur boss
        # draw dipanggil tiap frame, jadi digambar di sini.
        if not portrait_hd and not hero_lane:
            try:
                mod = A._live_module()
                if mod is not None:
                    mod.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ---------- DEBUG ----------
        if A.DEBUG_CHARACTER and not portrait_hd:
            try:
                A._draw_debug(surface, boss, x, y, state)
            except Exception:
                pass


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _skill_flags(boss):
        """State skill aktif -> flag body-reaction (focus/q, wind/w,
        shackle/e, powershot/r)."""
        active_skill = getattr(boss, "active_skill", None)
        return {
            "focus": active_skill == "q",
            "wind": active_skill == "w",
            "shackle": active_skill == "e",
            "powershot": active_skill == "r",
        }

    def _draw_sylara_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        sf = _NS_sylara._skill_flags(boss)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x, y + 64)
            _NS_sylara._draw_floating_wind(surface, x, y + 35, boss.pulse)
        _NS_sylara._draw_sylara_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle",
            detail=getattr(boss, "_portrait_hd", False), **sf)


    def _draw_sylara_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        sf = _NS_sylara._skill_flags(boss)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x + sway, y + 64)
            _NS_sylara._draw_floating_wind(surface, x + sway, y + 35, phase,
                                           trail=True, facing=boss.direction)
        _NS_sylara._draw_sylara_body(
            surface, x + sway, y - bob, boss.direction, phase, "walk",
            detail=getattr(boss, "_portrait_hd", False), **sf)


    def _draw_sylara_attack(surface, boss, x, y):
        A = _NS_sylara
        progress = getattr(boss, "_sy_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Check if we should power-shot (during Q)
        powered = getattr(boss, "active_skill", None) == "q"

        # SWING MODE: musuh terlalu dekat untuk menembak -> sapuan limb
        # busur berbasis busur (arc).  Mode dikunci saat serangan mulai
        # (lihat _update_attack_anim) supaya pose tidak berganti di
        # tengah animasi.
        swing_mode = bool(getattr(boss, "_sy_swing_mode", False))
        action = "swing" if swing_mode else "attack"

        # Spawn arrow at release (mid-late in animation)
        release_start = 0.55 if powered else 0.5
        release_end = 0.65 if powered else 0.6

        # Basic attack TIDAK spawn renderer projectile - pakai sistem
        # generic (_entity.py) yang homing & terarah saja supaya tidak
        # ada efek ganda. Renderer arrow hanya saat skill aktif.
        active_skill = getattr(boss, "active_skill", None)
        if (active_skill is not None and not swing_mode
                and release_start < progress < release_end
                and not getattr(boss, "_sy_arrow_spawned", False)):
            _NS_sylara._spawn_arrow(boss, x, y, powered=powered)
            boss._sy_arrow_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._sy_arrow_spawned = False

        # Slight recoil back on release
        recoil = 0
        if progress > release_start:
            t = (progress - release_start) / (1 - release_start)
            recoil = int(math.sin(t * math.pi) * 2) * -boss.direction

        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_sylara._draw_shadow(surface, x + recoil, y + 64)
            _NS_sylara._draw_floating_wind(surface, x + recoil, y + 35,
                                           boss.pulse, intense=True)
        sf = _NS_sylara._skill_flags(boss)
        _NS_sylara._draw_sylara_body(surface, x + recoil, y, boss.direction,
                                     boss.pulse, action, progress,
                                     powered=powered, detail=portrait_hd, **sf)
        if not portrait_hd:
            # Trail sapuan versi CANVAS hanya dipakai kalau lapisan FX
            # hidup tidak mengambil alih (jalur boss / tanpa modul FX);
            # kalau tidak, pita 60 fps di layar yang menggambarnya.
            lo, hi = A.SWING_WINDOW
            if swing_mode and lo < progress < hi and not A._FX_LIVE.v:
                f = 1 if boss.direction >= 0 else -1
                rs = A.RIG_SCALE
                cxr = x + recoil

                def _pt(dx, dy):
                    return (int(cxr + dx * rs * f), int(y + dy * rs))

                A._draw_bow_swing_trail(surface, _pt, boss.pulse, progress)
            if not swing_mode:
                _NS_sylara._draw_bow_release_flash(surface, x + recoil, y,
                                                   boss.direction, progress)


    def _draw_sylara_windrun(surface, boss, x, y, timer):
        """Fast dash pose during windrun."""
        phase = boss.pulse * 3.0
        bob = int(abs(math.sin(phase * 2)) * 2)
        sf = _NS_sylara._skill_flags(boss)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x, y + 64)
            _NS_sylara._draw_windrun_trail(surface, x, y, boss.direction, phase)
        _NS_sylara._draw_sylara_body(
            surface, x, y - bob, boss.direction, phase, "windrun",
            detail=getattr(boss, "_portrait_hd", False), **sf)


    # ===================================================================
    # BODY RENDERING - HD Wind Ranger
    # ===================================================================
    def _draw_sylara_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, powered=False, detail=False,
                          focus=False, wind=False, shackle=False,
                          powershot=False, crit=False):
        """Renderer tubuh Sylara kualitas maksimum, 100% procedural.

        Dibangun sebagai bone rig 2D berlapis seperti Kaizen/Thorne
        Masterwork: cape hijau per-panel yang beranimasi, quiver berisi
        anak panah, korset kulit ber-strap, hood runcing dengan rambut
        merah menyembul, dan busur recurve yang posenya dihitung dari
        sendi (grip, nock, tarikan tali). Tidak ada PNG, sprite sheet,
        ataupun image.load.

        Kwarg ``focus/wind/shackle/powershot/crit`` membuat badan IKUT
        bereaksi ke state skill (mis. busur & rambut menyala hijau saat
        Focus Fire / Powershot, rantai hijau saat Shackle, afterimage
        saat Windrun).
        """
        _NS_sylara._draw_sylara_elite(
            surface, cx, cy, facing, phase, action, attack_progress,
            powered=powered, detail=detail,
            focus=focus, wind=wind, shackle=shackle,
            powershot=powershot, crit=crit)


    # ===================================================================
    # MASTERWORK RIG - bone rig 2D berlapis (setara Kaizen Masterwork)
    # ===================================================================
    def _bow_frame(tilt):
        """Basis lokal busur: (up, forward) untuk kemiringan `tilt`."""
        return ((math.sin(tilt), -math.cos(tilt)),
                (math.cos(tilt), math.sin(tilt)))


    def _bow_point(grip, tilt, u, v):
        """Titik pada bidang busur: u = sepanjang limb, v = ke depan."""
        (ux, uy), (fx, fy) = _NS_sylara._bow_frame(tilt)
        return (grip[0] + ux * u + fx * v, grip[1] + uy * u + fy * v)


    def _bow_nock(grip, tilt, draw_amt):
        """Posisi nock (tangan penarik) dalam koordinat lokal tubuh."""
        return _NS_sylara._bow_point(grip, tilt, 0.0, -2.0 - draw_amt * 12.0)


    def _draw_elite_bow(surface, pt, f, grip, tilt, draw_amt, phase,
                        powered=False, detail=False):
        """Busur recurve kayu pose-driven: limb melengkung, tali menegang
        mengikuti tarikan, anak panah ternock saat draw_amt > 0."""
        p = _NS_sylara.PALETTE
        bp = _NS_sylara._bow_point
        flex = draw_amt * 0.55

        def limb_points(sign):
            pts = []
            for i in range(7):
                s = i / 6.0
                u = sign * 24.0 * s
                # perut busur maju, ujung recurve menekuk balik
                v = 8.0 * s * s - 14.0 * (s ** 4) - flex * 6.0 * s * s
                pts.append(bp(grip, tilt, u, v))
            return pts

        tips = []
        for sign in (1, -1):
            pts = limb_points(sign)
            tips.append(pts[-1])
            for i in range(len(pts) - 1):
                w = 5 - int(i * 0.6)
                a, b = pts[i], pts[i + 1]
                _NS_sylara._aaline(surface, p["shadow_deep"],
                                   pt(a[0] + 1, a[1] + 1),
                                   pt(b[0] + 1, b[1] + 1), w + 2)
                _NS_sylara._aaline(surface, p["wood_darkest"],
                                   pt(*a), pt(*b), w)
                _NS_sylara._aaline(surface, p["wood_mid"],
                                   pt(*a), pt(*b), max(1, w - 2))
                _NS_sylara._aaline(surface, p["wood_light"],
                                   pt(a[0], a[1] - 1), pt(b[0], b[1] - 1), 1)
                if detail and i % 2 == 0:
                    _NS_sylara._aacircle(surface, p["wood_shine"],
                                         pt(a[0], a[1] - 1), 1)
            # ujung limb dibungkus kulit + ring emas
            tip = pts[-1]
            _NS_sylara._aacircle(surface, p["leather_dark"], pt(*tip), 2)
            _NS_sylara._aacircle(surface, p["gold_mid"], pt(*tip), 1)
            _NS_sylara._aacircle(surface, p["gold_light"],
                                 pt(tip[0], tip[1] - 1), 1)

        # grip kulit + lilitan
        g_a = bp(grip, tilt, 6, 1)
        g_b = bp(grip, tilt, -6, 1)
        _NS_sylara._aaline(surface, p["leather_darkest"], pt(*g_a), pt(*g_b), 6)
        _NS_sylara._aaline(surface, p["leather_mid"], pt(*g_a), pt(*g_b), 4)
        for i in range(4):
            s = -4 + i * 2.8
            w_a = bp(grip, tilt, s, -1)
            w_b = bp(grip, tilt, s + 1.4, 3)
            _NS_sylara._aaline(surface, p["leather_light"],
                               pt(*w_a), pt(*w_b), 1)

        # tali: dua ruas menuju nock
        nock = _NS_sylara._bow_nock(grip, tilt, draw_amt)
        for col, w in ((p["shadow_deep"], 3), (p["string"], 2),
                       (p["string_shine"], 1)):
            _NS_sylara._aaline(surface, col, pt(*tips[0]), pt(*nock), w)
            _NS_sylara._aaline(surface, col, pt(*tips[1]), pt(*nock), w)

        if draw_amt > 0.05:
            _NS_sylara._draw_elite_arrow(surface, pt, nock, tilt, draw_amt,
                                         phase, powered, detail)
        return nock


    def _draw_elite_arrow(surface, pt, nock, tilt, draw_amt, phase,
                          powered=False, detail=False):
        """Anak panah ternock: shaft kayu, mata baja, bulu hijau."""
        p = _NS_sylara.PALETTE
        (_, _), (fx, fy) = _NS_sylara._bow_frame(tilt)
        length = 32
        tip = (nock[0] + fx * length, nock[1] + fy * length)
        _NS_sylara._aaline(surface, p["shadow_deep"],
                           pt(nock[0], nock[1] + 1), pt(tip[0], tip[1] + 1), 4)
        _NS_sylara._aaline(surface, p["arrow_shaft_d"], pt(*nock), pt(*tip), 3)
        _NS_sylara._aaline(surface, p["arrow_shaft"],
                           pt(nock[0], nock[1] - 1), pt(tip[0], tip[1] - 1), 1)
        # mata panah
        head_b = (tip[0] - fx * 8, tip[1] - fy * 8)
        _NS_sylara._poly(surface, p["arrow_head_d"], [
            pt(*tip), pt(head_b[0], head_b[1] - 3), pt(head_b[0], head_b[1] + 3)])
        _NS_sylara._poly(surface, p["arrow_head"], [
            pt(tip[0] - fx, tip[1] - fy),
            pt(head_b[0] + 1, head_b[1] - 2), pt(head_b[0] + 1, head_b[1] + 2)])
        if detail:
            _NS_sylara._aaline(surface, p["white"],
                               pt(tip[0] - fx * 2, tip[1] - fy * 2 - 1),
                               pt(head_b[0] + 2, head_b[1] - 1), 1)
        # fletching
        for side in (-3, 3):
            _NS_sylara._poly(surface, p["arrow_feather_d"], [
                pt(nock[0] + fx * 2, nock[1] + fy * 2),
                pt(nock[0] + fx * 9, nock[1] + fy * 9 + side),
                pt(nock[0] + fx * 9, nock[1] + fy * 9)])
            _NS_sylara._poly(surface, p["arrow_feather"], [
                pt(nock[0] + fx * 3, nock[1] + fy * 3),
                pt(nock[0] + fx * 8, nock[1] + fy * 8 + side * .7),
                pt(nock[0] + fx * 8, nock[1] + fy * 8)])
        if powered or draw_amt > 0.75:
            glow = p["wind_white"] if powered else p["wind_bright"]
            alpha = int(200 * min(1.0, draw_amt))
            for i in range(4):
                gx = tip[0] + fx * (4 + i * 5)
                gy = tip[1] + fy * (4 + i * 5)
                _NS_sylara._aacircle(surface, (*glow, max(30, alpha - i * 45)),
                                     pt(gx, gy), max(1, 3 - i))


    def _draw_sylara_masterwork_details(surface, pt, f):
        """Micro-detail khusus portrait LOD. Di skala arena tanda-tanda ini
        runtuh jadi noise, jadi LOD mengeluarkannya dari cache gameplay."""
        p = _NS_sylara.PALETTE
        # helai rambut halus di pipi & tengkuk
        for i in range(5):
            _NS_sylara._aaline(surface, p["hair_shine"],
                               pt(2 + i * 2, -37 + i),
                               pt(-1 + i * 2, -32 + i), 1)
        for i in range(4):
            _NS_sylara._aaline(surface, p["hair_light"],
                               pt(-8 - i * 3, -28 + i * 2),
                               pt(-13 - i * 3, -22 + i * 2), 1)
        # bulu mata, alis & kilau bibir
        _NS_sylara._aaline(surface, p["hair_darkest"], pt(6, -33), pt(11, -33), 1)
        _NS_sylara._aacircle(surface, p["lips_mid"], pt(10, -26), 1)
        _NS_sylara._aacircle(surface, p["skin_high"], pt(7, -29), 1)
        # jahitan tepi hood
        for i in range(5):
            _NS_sylara._aacircle(surface, p["cloth_high"],
                                 pt(-6 + i * 4, -40 + abs(i - 2)), 1)
        # anyaman korset & rivet sabuk
        for yy in (-14, -10, -6):
            _NS_sylara._aaline(surface, p["cloth_high"],
                               pt(-4, yy), pt(4, yy + 2), 1)
        for xx in (-6, 0, 6):
            _NS_sylara._aacircle(surface, p["gold_light"], pt(xx, 2), 1)
        # serat bulu fletching di quiver + kilau gesper bahu
        for i in range(3):
            _NS_sylara._aaline(surface, p["arrow_feather"],
                               pt(-15 - i * 3, -31 - i * 2),
                               pt(-18 - i * 3, -27 - i * 2), 1)
        _NS_sylara._aacircle(surface, p["gold_light"], pt(-9, -18), 1)
        # tali sepatu & lipatan sarung tangan
        for yy in (26, 31, 36):
            _NS_sylara._aaline(surface, p["leather_light"],
                               pt(7, yy), pt(12, yy), 1)


    # Buffer rig: cukup besar untuk cape, busur terentang, dan speed-line.
    # Native ~1.52x (hip 0,0; kepala ~-76; kaki ~+61) plus bow/cape.
    RIG_W, RIG_H = 240, 210
    RIG_OX, RIG_OY = 100, 95


    def _draw_sylara_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, powered=False, detail=False,
                           focus=False, wind=False, shackle=False,
                           powershot=False, crit=False):
        """Komposisi akhir: rig digambar ke buffer lalu diberi outline gelap
        1 px seperti sprite sheet referensi, baru di-blit ke arena."""
        buf = pygame.Surface((_NS_sylara.RIG_W, _NS_sylara.RIG_H),
                             pygame.SRCALPHA)
        _NS_sylara._draw_sylara_rig(buf, _NS_sylara.RIG_OX, _NS_sylara.RIG_OY,
                                    facing, phase, action, attack_progress,
                                    powered=powered, detail=detail)
        silhouette = buf.copy()
        silhouette.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        ox = int(cx) - _NS_sylara.RIG_OX
        oy = int(cy) - _NS_sylara.RIG_OY
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(silhouette, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))
        # Badan ikut bereaksi ke state skill (bow/hair/cape menyala).
        if focus or wind or shackle or powershot or crit:
            _NS_sylara._draw_sylara_skill_overlay(
                surface, cx, cy, facing, phase, action, attack_progress,
                focus=focus, wind=wind, shackle=shackle,
                powershot=powershot, crit=crit)


    # -------------------------------------------------------------------
    # Skill-state body overlay — badan ikut bereaksi ke skill aktif
    # -------------------------------------------------------------------
    def _draw_sylara_skill_overlay(surface, cx, cy, facing, phase, action,
                                   attack_progress=0.0, focus=False,
                                   wind=False, shackle=False, powershot=False,
                                   crit=False):
        """Glow reaktif di badan saat skill aktif (world-space, ringan).

        Bow/hair/cape menyala hijau (focus/powershot), rantai hijau di
        pergelangan (shackle), afterimage vertigo (wind).  Tetap < 100
        primitif — dibuang otomatis bila tidak ada skill aktif (kondisi di
        _draw_sylara_elite).
        """
        p = _NS_sylara.PALETTE
        f = 1 if facing >= 0 else -1
        rs = _NS_sylara.RIG_SCALE
        pulse = math.sin(phase * 3.2) * 0.5 + 0.5
        bow_x = cx + int(20 * rs * f)
        bow_y = cy - int(8 * rs)

        # Inti glow di sekitar busur + ujung bow (semua skill ranged)
        if focus or powershot or crit:
            _NS_sylara._aacircle(surface,
                                 (*p["wind_bright"], int(120 + 90 * pulse)),
                                 (bow_x, bow_y), int(16 + 4 * pulse))
            _NS_sylara._aacircle(surface,
                                 (*p["wind_mid"], int(90 + 60 * pulse)),
                                 (bow_x, bow_y), int(22 + 5 * pulse))
            # specular di ujung bow — kilau baja
            _NS_sylara._aacircle(surface, p["white"], (bow_x + f * 3, bow_y), 1)
            # rim cahaya hijau di sepanjang bilah cape + rambut
            _NS_sylara._aaline(surface, (*p["wind_mid"], 120),
                               (cx - 6 * f, cy - 34), (cx - 12 * f, cy + 6), 2)
        if focus:
            # tick angin berputar di pergelangan draw-hand
            _NS_sylara._dashed_ring(surface, bow_x, bow_y, int(10 + 3 * pulse),
                                    p["wind_bright"], int(160 + 60 * pulse),
                                    phase * 2.2, segments=6, thick=2, span=.6)
        if powershot:
            # orb charge membesar di ujung busur
            _NS_sylara._aacircle(surface, (*p["wind_bright"], 200),
                                 (bow_x + f * 4, bow_y), int(6 + 3 * pulse))
            _NS_sylara._aacircle(surface, p["white"],
                                 (bow_x + f * 4, bow_y), 2)

        if shackle:
            # anchor ring berputar di pergelangan draw-hand (target &
            # tether sudah digambar di ground telegraph world-space)
            _NS_sylara._dashed_ring(surface, bow_x, bow_y, int(12 + 2 * pulse),
                                    p["wind_light"], int(170 + 50 * pulse),
                                    -phase * 2.6, segments=8, thick=2, span=.5)
            _NS_sylara._dashed_ring(surface, bow_x, bow_y, int(20 + 3 * pulse),
                                    p["wind_bright"], int(110 + 40 * pulse),
                                    phase * 1.2, segments=8, thick=2, span=.4)
            _NS_sylara._aacircle(surface, p["wind_white"],
                                 (bow_x + f * 2, bow_y), 1)

        if wind:
            # afterimage vertigo di sekeliling badan
            for i in range(5):
                r = int(24 + i * 6)
                al = int(60 - i * 8)
                if al > 0:
                    _NS_sylara._aacircle(surface,
                                         (*p["wind_mid"], al),
                                         (cx, cy - 4), r, 1)


    def _draw_sylara_rig(surface, cx, cy, facing, phase, action,
                         attack_progress=0.0, powered=False, detail=False):
        """Rig hand-authored meniru sprite sheet referensi Wind Ranger:
        hood hijau runcing, rambut merah berkibar, cape robek, korset
        kulit-hijau, quiver anak panah, dan busur recurve pose-driven."""
        p = _NS_sylara.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        swing = action == "swing"
        attack = action == "attack" or swing
        windrun = action == "windrun"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.7)

        rs = _NS_sylara.RIG_SCALE
        lean = (3 if walk else 0) * f
        if windrun:
            lean = 7 * f
        root_y = int(math.sin(phase * .72) * .7)
        # v2 (animasi): perpindahan berat badan saat idle — goyang kiri-kanan.
        sway = int(math.sin(phase * .8) * 3) * f if not (walk or attack or windrun) else 0
        flare = 1.0
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if windrun:
            root_y += 2 - int(abs(math.sin(phase * 2.0)) * 2)
        if attack:
            if swing:
                # Sapuan melee: bobot badan mengikuti busur ayunan
                # (anticipation ke belakang -> hentakan ke depan).
                sp = _NS_sylara._swing_arc_pose(ap)
                lean = int(round(sp["lean"])) * f
                root_y += int(round(sp["bob"]))
                flare = sp["flare"]
            else:
                pose = _NS_sylara._attack_pose(ap)
                lean = pose["lean"] * f
                root_y += pose["bob"]
                flare = pose["flare"]
                if pose["tremble"]:
                    lean += (1 if int(phase * 31) % 2 else -1)

        def pt(dx, dy):
            return (int(cx + dx * rs * f + lean + sway), int(cy + dy * rs + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                _NS_sylara._poly(surface, p["shadow_deep"],
                                 [(x + f, y + 1) for x, y in pts])
            _NS_sylara._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            w = max(2, int(round(width * rs)))
            _NS_sylara._aaline(surface, p["shadow_deep"], aa, bb, w + 3)
            _NS_sylara._aaline(surface, base, aa, bb, w)
            if light:
                off = -1 if f > 0 else 1
                _NS_sylara._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, w // 3))

        wave = math.sin(phase * 1.15)
        wave2 = math.sin(phase * 1.45 + .8)
        # angin: cape & rambut terhempas lebih jauh saat bergerak/menembak
        gust = 0
        if walk:
            gust = 6
        elif windrun:
            gust = 16
        elif attack:
            gust = int(4 + 10 * (flare - 1.0) * 8)

        # ═══ CAPE: panel gelap sempit di punggung + tepi robek ═══
        cw = int(wave * 3)
        cw2 = int(wave2 * 2)
        cape_spine = [
            (-8, -35),
            (-15 - gust, -24 + cw), (-20 - gust, -8 + cw),
            (-17 - int(gust * .8), 6 + cw2), (-11, 18 + cw2),
            (-4, 14)]
        cape_tuft = _NS_sylara._tuft_points(cape_spine, depth=3.4, min_len=6, seed=21)
        poly(p["cloak_darkest"], [(-3, -34)] + cape_tuft + [(-2, 0)])
        poly(p["cloak_dark"], [
            (-4, -32), (-8, -33),
            (-13 - gust, -22 + cw), (-17 - gust, -7 + cw),
            (-14 - int(gust * .8), 5 + cw2), (-9, 15 + cw2),
            (-4, 12), (-2, 0)], False)
        poly(p["cloak_mid"], [
            (-6, -29), (-8, -29),
            (-10 - int(gust * .6), -20 + cw), (-11 - gust, -8 + cw),
            (-9, 2 + cw2), (-6, 9 + cw2), (-5, 4)], False)
        # lipatan kain: garis vertikal supaya cape tidak jadi blok datar
        for i, (tx0, ty0, tx1, ty1) in enumerate((
                (-6, -28, -11 - gust, 2 + cw2),
                (-9, -26, -14 - gust, -1 + cw),
                (-12, -20, -16 - gust, 6 + cw2))):
            _NS_sylara._aaline(surface, p["cloak_darkest"],
                               pt(tx0, ty0), pt(tx1, ty1), 1)
        # tepi robek (segitiga bawah) - siluet khas referensi
        for i, (bx, by) in enumerate(((-16, 2), (-12, 8), (-7, 12))):
            tear = int(wave2 * (1 + i))
            poly(p["cloak_darkest"], [
                (bx - int(gust * .5), by + cw2),
                (bx + 5 - int(gust * .5), by + 2 + cw2),
                (bx + 1 - int(gust * .5), by + 11 + tear + cw2)], False)
        _NS_sylara._aaline(surface, p["cloak_light"],
                           pt(-6, -31), pt(-14 - gust, -6 + cw), 1)
        _NS_sylara._aaline(surface, p["cloak_light"],
                           pt(-14 - gust, -6 + cw), pt(-9, 12 + cw2), 1)
        _NS_sylara._aaline(surface, p["cloak_high"],
                           pt(-7, -30), pt(-12 - gust, -10 + cw), 2)
        hx, hy = pt(-16 - gust, 8 + cw2)
        _NS_sylara._rect(surface, p["cloak_high"], (hx, hy, 2, 2))

        # ═══ QUIVER di punggung + anak panah berbulu ═══
        poly(p["leather_darkest"], [(-6, -24), (-13, -30), (-19, -18),
                                    (-12, -8), (-6, -13)])
        poly(p["leather_dark"], [(-7, -24), (-12, -28), (-17, -18),
                                 (-11, -10), (-7, -14)], False)
        poly(p["leather_mid"], [(-9, -24), (-12, -27), (-15, -19),
                                (-11, -13)], False)
        _NS_sylara._aaline(surface, p["leather_light"],
                           pt(-13, -27), pt(-16, -19), 1)
        _NS_sylara._aaline(surface, p["gold_mid"], pt(-8, -22), pt(-16, -21), 2)
        for i, (ax, ay) in enumerate(((-13, -31), (-16, -29), (-10, -32))):
            sway = int(wave * (1 + i % 2))
            _NS_sylara._aaline(surface, p["arrow_shaft_d"],
                               pt(ax, ay), pt(ax - 4, ay - 9 + sway), 2)
            _NS_sylara._poly(surface, p["arrow_feather_d"], [
                pt(ax - 4, ay - 9 + sway), pt(ax - 8, ay - 6 + sway),
                pt(ax - 5, ay - 4 + sway)])
            _NS_sylara._poly(surface, p["arrow_feather"], [
                pt(ax - 4, ay - 9 + sway), pt(ax - 7, ay - 7 + sway),
                pt(ax - 5, ay - 5 + sway)])

        # ═══ RAMBUT BELAKANG: massa merah + helai berkibar ═══
        hw = int(wave * 2) + gust // 3
        poly(p["hair_darkest"], [(1, -42), (-5, -40), (-11 - hw, -33),
                                 (-14 - hw, -23), (-8, -18), (-3, -26),
                                 (-1, -34)])
        poly(p["hair_dark"], [(0, -40), (-4, -38), (-9 - hw, -32),
                              (-11 - hw, -24), (-6, -20), (-2, -27)], False)
        for i, (mx, my, ex, ey) in enumerate(((-5, -37, -14, -33),
                                              (-5, -32, -15, -25),
                                              (-4, -27, -12, -18))):
            sway = int(wave * (1 + i)) + gust // 3
            poly(p["hair_mid"], [(-1, -39), (mx - sway, my - 1),
                                 (ex - sway, ey), (ex - sway + 3, ey + 3),
                                 (mx - sway, my + 5)], False)
            _NS_sylara._aaline(surface, p["hair_light"],
                               pt(mx - sway, my + 1), pt(ex - sway, ey + 1), 1)
        _NS_sylara._aaline(surface, p["hair_shine"],
                           pt(-3, -38), pt(-10 - hw, -30), 1)

        # ═══ KAKI: paha ramping + boot kulit tinggi ═══
        # v2 (animasi): foot-lift bergantian saat jalan — kaki yang melangkah
        # maju terangkat (lutut + telapak naik), kaki tumpuan tetap menapak.
        leg_phase = stride if (walk or windrun) else 0.0
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 9) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 9) if walk else 0
        if windrun:
            rear_foot = (-13 - int(leg_phase * 7), 38)
            front_foot = (14 + int(leg_phase * 8), 38)
        else:
            rear_foot = (-7 - int(leg_phase * 5),
                         40 - int(abs(leg_phase) * 2) - rear_lift)
            front_foot = (9 + int(leg_phase * 6), 40 - front_lift)
        for hip, knee, foot, shade, lift in (
                ((-6, 11), (-9, 26), rear_foot, p["cloth_darkest"], rear_lift),
                ((6, 11), (9, 25), front_foot, p["cloth_dark"], front_lift)):
            knee = (knee[0], knee[1] - lift)
            poly(shade, [hip, (hip[0] + 6, hip[1]),
                         (knee[0] + 4, knee[1]), (foot[0] + 4, foot[1] - 6),
                         (foot[0] - 4, foot[1] - 6), (knee[0] - 4, knee[1])])
            limb(knee, (foot[0], foot[1] - 6), 6,
                 p["leather_dark"], p["leather_mid"])
            # boot: sol + lipatan atas + tali
            poly(p["leather_darkest"], [(foot[0] - 5, foot[1] - 7),
                                        (foot[0] + 5, foot[1] - 7),
                                        (foot[0] + 6, foot[1] - 2),
                                        (foot[0] - 5, foot[1] - 2)])
            poly(p["leather_mid"], [(foot[0] - 4, foot[1] - 6),
                                    (foot[0] + 4, foot[1] - 6),
                                    (foot[0] + 5, foot[1] - 3),
                                    (foot[0] - 4, foot[1] - 3)], False)
            poly(p["leather_darkest"], [(foot[0] - 5, foot[1] - 2),
                                        (foot[0] + 7, foot[1] - 2),
                                        (foot[0] + 8, foot[1] + 1),
                                        (foot[0] - 5, foot[1] + 1)])
            _NS_sylara._aaline(surface, p["leather_light"],
                               pt(foot[0] - 3, foot[1] - 5),
                               pt(foot[0] + 4, foot[1] - 5), 1)
            _NS_sylara._aacircle(surface, p["leather_high"],
                                 pt(foot[0] + 3, foot[1] - 4), 1)
            _NS_sylara._aaline(surface, p["gold_mid"],
                               pt(knee[0] - 3, knee[1] + 1),
                               pt(knee[0] + 3, knee[1] + 1), 1)

        # ═══ ROK/TASSET hijau pendek berlapis ═══
        skirt = int(wave * 2) + gust // 3
        poly(p["cloth_darkest"], [(-8, 4), (8, 4), (10, 13),
                                  (4, 16), (-4, 16), (-9 - skirt, 12)])
        poly(p["cloth_dark"], [(-7, 5), (7, 5), (8, 12),
                               (3, 15), (-3, 15), (-7 - skirt, 11)], False)
        poly(p["cloth_mid"], [(-5, 6), (5, 6), (6, 11), (2, 13),
                              (-3, 13), (-5, 11)], False)
        for i, sx in enumerate((-6, -1, 4)):
            _NS_sylara._aaline(surface, p["cloth_light"],
                               pt(sx, 7), pt(sx - 1 - i, 14), 1)

        # ═══ TORSO: korset hijau + strap kulit + sabuk emas ═══
        poly(p["cloth_darkest"], [(-8, -19), (8, -21), (11, -9),
                                  (8, 5), (-7, 5), (-10, -8)])
        poly(p["cloth_dark"], [(-6, -18), (7, -19), (9, -9),
                               (7, 5), (-6, 5), (-8, -8)], False)
        poly(p["cloth_mid"], [(-4, -16), (6, -17), (8, -9),
                              (6, 3), (-4, 3), (-6, -8)], False)
        poly(p["cloth_light"], [(0, -15), (5, -15), (7, -9),
                                (4, -2), (0, -4)], False)
        poly(p["cloth_high"], [(2, -13), (5, -13), (5, -8), (2, -7)], False)
        # dither band korset — tekstur klasik yang selamat dari downscale
        dpts = [pt(-4 + i * 2, -2 + (i % 3)) for i in range(8)]
        _NS_sylara._dither_dots(surface, p["cloth_darkest"], dpts, 140)
        # dada & garis leher V (ref)
        poly(p["skin_dark"], [(0, -19), (7, -20), (6, -14), (1, -13)], False)
        poly(p["skin_mid"], [(1, -18), (6, -19), (5, -15), (2, -14)], False)
        _NS_sylara._aaline(surface, p["cloth_darkest"], pt(0, -20), pt(4, -13), 2)
        # strap kulit menyilang
        _NS_sylara._aaline(surface, p["leather_darkest"], pt(-9, -17), pt(9, -2), 4)
        _NS_sylara._aaline(surface, p["leather_mid"], pt(-9, -17), pt(9, -2), 2)
        _NS_sylara._aaline(surface, p["leather_light"], pt(-8, -17), pt(8, -3), 1)
        # sabuk + gesper emas
        _NS_sylara._aaline(surface, p["leather_darkest"], pt(-10, 3), pt(10, 3), 6)
        _NS_sylara._aaline(surface, p["leather_dark"], pt(-10, 2), pt(10, 2), 4)
        _NS_sylara._rect(surface, p["gold_dark"], (pt(-3, 0)[0], pt(-3, 0)[1], 7, 6), 1)
        _NS_sylara._rect(surface, p["gold_mid"], (pt(-2, 1)[0], pt(-2, 1)[1], 5, 4), 1)
        _NS_sylara._rect(surface, p["gold_light"], (pt(-1, 2)[0], pt(-1, 2)[1], 2, 2))
        _NS_sylara._aacircle(surface, p["gold_shine"], pt(0, 2), 1)
        # pauldron kulit bahu belakang
        poly(p["leather_dark"], [(-7, -20), (-13, -18), (-14, -12),
                                 (-8, -11)], True)
        poly(p["leather_mid"], [(-8, -19), (-12, -17), (-12, -13),
                                (-9, -12)], False)
        _NS_sylara._aacircle(surface, p["gold_mid"], pt(-11, -15), 2)

        # bayangan leher supaya kepala tidak menyatu dengan torso
        _NS_sylara._aaline(surface, p["cloth_darkest"], pt(1, -22), pt(8, -23), 3)
        _NS_sylara._aaline(surface, p["skin_darkest"], pt(3, -24), pt(8, -25), 2)

        # ═══ POSE BUSUR & LENGAN ═══
        # Pose busur dihitung SATU tempat (_bow_pose_local) supaya rig,
        # trail ayunan, titik lepas panah, dan overlay debug memakai
        # geometri yang identik.  action:
        #   attack  -> 7-keyframe tarik tali (rest -> full draw -> IMPACT)
        #   swing   -> sapuan limb berbasis busur (arc) untuk musuh dekat
        #   windrun -> busur disandang saat dash
        #   idle    -> busur menggantung, ikut napas (wave)
        _pose_action = ("swing" if swing else
                        "attack" if attack else
                        "windrun" if windrun else "idle")
        grip, tilt, draw_amt = _NS_sylara._bow_pose_local(
            _pose_action, ap, wave)

        # lengan belakang (penarik tali) digambar sebelum busur
        nock = _NS_sylara._bow_nock(grip, tilt, draw_amt)
        if swing:
            # Sapuan: lengan belakang menyeimbangkan badan, tertinggal
            # dari busur (follow-through) alih-alih menarik tali.
            _sp = _NS_sylara._swing_arc_pose(ap)
            _sa = _sp["angle"]
            rear_hand = (-9 - math.cos(_sa) * 4.0, 2 - math.sin(_sa) * 5.0)
            elbow = (rear_hand[0] + 2, rear_hand[1] - 7)
        elif attack and draw_amt > 0.05:
            rear_hand = (nock[0], nock[1])
            elbow = (rear_hand[0] - 7, rear_hand[1] + 7)
        elif windrun:
            rear_hand = (-9, 2)
            elbow = (-11, -6)
        else:
            rear_hand = (-8, 4 + int(wave))
            elbow = (-11, -5)
        limb((-6, -15), elbow, 6, p["cloth_dark"], p["cloth_mid"])
        limb(elbow, rear_hand, 5, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_sylara._aacircle(surface, p["leather_darkest"], (rhx, rhy), 3)
        _NS_sylara._aacircle(surface, p["leather_mid"], (rhx, rhy), 2)
        _NS_sylara._aacircle(surface, p["leather_light"], (rhx - f, rhy - 1), 1)

        # ═══ KEPALA: hood runcing, wajah, poni merah ═══
        # dome hood (belakang kepala) sedikit lebih besar dari tengkorak
        poly(p["hood_dark"], [(-1, -44), (5, -48), (13, -46), (16, -39),
                              (14, -32), (8, -28), (-1, -30), (-5, -37)])
        poly(p["hood_mid"], [(0, -43), (5, -46), (12, -44), (14, -38),
                             (12, -33), (7, -30), (0, -31), (-3, -37)], False)
        # puncak hood menjuntai ke belakang (ekor kain)
        peak = int(wave * 2) + gust // 4
        poly(p["hood_darkest"], [(0, -47), (4, -50), (-6, -50 + peak),
                                 (-16 - peak, -43 + peak), (-9, -40)])
        poly(p["hood_mid"], [(0, -46), (3, -48), (-6, -48 + peak),
                             (-13 - peak, -43 + peak), (-7, -40)], False)
        _NS_sylara._aaline(surface, p["hood_light"], pt(-1, -47),
                           pt(-12 - peak, -43 + peak), 1)
        # wajah
        poly(p["skin_dark"], [(2, -41), (12, -42), (15, -35),
                              (14, -28), (5, -26), (1, -33)])
        poly(p["skin_mid"], [(3, -40), (11, -41), (14, -35),
                             (12, -29), (6, -27), (2, -33)], False)
        poly(p["skin_light"], [(5, -39), (10, -39), (12, -34),
                               (9, -31), (5, -32)], False)
        # mata besar bergaya sprite
        ex, ey = pt(9, -34)
        _NS_sylara._rect(surface, p["eye_white"], (ex - 2, ey - 2, 6, 5))
        _NS_sylara._rect(surface, p["eye_iris"], (ex + 1, ey - 2, 3, 5))
        _NS_sylara._rect(surface, p["eye_iris_light"], (ex + 1, ey - 1, 2, 2))
        _NS_sylara._rect(surface, p["eye_pupil"], (ex + 2, ey - 1, 1, 3))
        _NS_sylara._rect(surface, p["white"], (ex + 3, ey - 2, 1, 1))
        blink = (action == "idle" and math.sin(phase * 0.9 + 1.3) > 0.985)
        if blink:
            _NS_sylara._aaline(surface, p["hair_darkest"],
                               (ex - 2, ey), (ex + 4, ey), 2)
        _NS_sylara._aaline(surface, p["hair_darkest"], pt(7, -37), pt(13, -37), 1)
        # hidung + bibir
        _NS_sylara._aacircle(surface, p["skin_darkest"], pt(14, -32), 1)
        _NS_sylara._aaline(surface, p["lips_dark"], pt(11, -28), pt(13, -28), 1)
        # poni merah menyembul dari hood
        poly(p["hair_dark"], [(0, -43), (10, -44), (15, -39), (10, -38),
                              (4, -36), (-1, -38)], False)
        poly(p["hair_mid"], [(1, -42), (9, -43), (13, -39), (7, -38),
                             (2, -37)], False)
        _NS_sylara._aaline(surface, p["hair_shine"], pt(3, -42), pt(11, -41), 1)
        _NS_sylara._aacircle(surface, p["hair_high"], pt(6, -42), 1)
        # brim hood: pita gelap lalu kilau kain, membingkai wajah
        _NS_sylara._aaline(surface, p["hood_darkest"], pt(-2, -43), pt(14, -45), 4)
        _NS_sylara._aaline(surface, p["hood_light"], pt(-1, -45), pt(14, -46), 2)
        _NS_sylara._aaline(surface, p["cloth_high"], pt(0, -45), pt(12, -46), 1)
        _NS_sylara._aacircle(surface, p["gold_mid"], pt(14, -43), 1)
        # helai rambut samping menutupi leher
        side_sway = int(wave * 2)
        poly(p["hair_dark"], [(1, -36), (-4, -35), (-9 - side_sway, -25),
                              (-4, -20), (0, -29)], False)
        _NS_sylara._aaline(surface, p["hair_light"],
                           pt(-1, -34), pt(-7 - side_sway, -24), 1)

        # ═══ LENGAN DEPAN + BUSUR ═══
        if attack:
            bow_hand = (grip[0] - 1, grip[1] + 1)
        elif windrun:
            bow_hand = (grip[0] - 1, grip[1] - 2)
        else:
            bow_hand = (grip[0] - 2, grip[1] + 1)
        f_elbow = ((bow_hand[0] + 6) // 2 + 2, (bow_hand[1] - 14) // 2 + 2)
        limb((6, -15), f_elbow, 6, p["cloth_mid"], p["cloth_light"])
        limb(f_elbow, bow_hand, 5, p["skin_mid"], p["skin_light"])
        # vambrace kulit lengan busur
        _NS_sylara._aaline(surface, p["leather_dark"],
                           pt(f_elbow[0], f_elbow[1]),
                           pt((f_elbow[0] + bow_hand[0]) // 2,
                              (f_elbow[1] + bow_hand[1]) // 2), 4)
        _NS_sylara._aaline(surface, p["leather_light"],
                           pt(f_elbow[0], f_elbow[1] - 1),
                           pt((f_elbow[0] + bow_hand[0]) // 2,
                              (f_elbow[1] + bow_hand[1]) // 2 - 1), 1)
        _NS_sylara._draw_elite_bow(surface, pt, f, grip, tilt, draw_amt,
                                   phase, powered=powered, detail=detail)
        bhx, bhy = pt(*bow_hand)
        _NS_sylara._aacircle(surface, p["leather_darkest"], (bhx, bhy), 3)
        _NS_sylara._aacircle(surface, p["leather_mid"], (bhx, bhy), 2)
        _NS_sylara._aacircle(surface, p["leather_light"], (bhx + f, bhy - 1), 1)

        # ═══ secondary motion: angin, jejak langkah, kilau tarikan ═══
        if walk or windrun:
            speed = 3 if windrun else 2
            for i in range(speed):
                sy = cy - 12 + i * 11 + root_y
                _NS_sylara._aaline(surface, (*p["wind_light"], 120 - i * 30),
                                   (cx - f * (26 + i * 8), sy),
                                   (cx - f * (12 + i * 5), sy - 1), 1)
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx2, fy2 = pt(planted[0], planted[1])
                for i in range(3):
                    _NS_sylara._aacircle(
                        surface, (*p["wind_mid"], max(20, int(140 * contact) - i * 40)),
                        (fx2 - f * (3 + i * 4), fy2 - i % 2), max(1, 3 - i))
        elif attack and draw_amt > .35:
            # energi angin terkumpul di tali saat tarikan penuh
            nx, ny = pt(*nock)
            for i in range(5):
                a = phase * 1.4 + i * math.pi * .4
                r = 4 + int(draw_amt * 7)
                _NS_sylara._aacircle(
                    surface, (*p["wind_bright"], int(190 * draw_amt)),
                    (nx + int(math.cos(a) * r), ny + int(math.sin(a) * r * .8)), 1)
        else:
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx = cx + int(math.sin(phase + i * 2.1) * (16 + i * 4))
                my = cy + 26 - int(t * 54)
                col = p["leaf_gold"] if i % 2 else p["wind_light"]
                _NS_sylara._aacircle(surface,
                                     (*col, int(140 * (1 - t))),
                                     (mx, my), 1 if i % 2 else 2)
            # swatch daun (material unik, selalu tampil di idle)
            _NS_sylara._aacircle(surface, p["leaf_gold"], pt(-18, 8), 1)
            _NS_sylara._aacircle(surface, p["leaf_ember"], pt(16, 6), 1)

        if windrun and not detail:
            for i in range(6):
                a2 = phase * .7 + i * math.pi / 3
                r = 28 + int(math.sin(phase + i) * 6)
                _NS_sylara._aacircle(surface, (*p["wind_bright"], 150),
                                     (cx + int(math.cos(a2) * r),
                                      cy + int(math.sin(a2) * r * .45)), 1)

        if detail:
            _NS_sylara._draw_sylara_masterwork_details(surface, pt, f)



    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Wind mist beneath floating Sylara."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sylara.PALETTE["wind_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising wind wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha), (sx, sy), 5)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha), (sx, sy - 2), 3)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting leaves
        for i in range(3):
            angle = phase * 1.0 + i * math.pi * 2 / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_sylara._draw_leaf(surface, sx, sy, 3, angle,
                       _NS_sylara.PALETTE["cloth_dark"], _NS_sylara.PALETTE["cloth_mid"],
                       _NS_sylara.PALETTE["cloth_light"])

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_sylara.PALETTE["wind_darkest"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_ranger_silhouette_glow(surface, x, y, phase):
        """Subtle green rim light behind Sylara's hood, cape, and bow."""
        pulse = 0.72 + math.sin(phase * 1.25) * 0.15
        halo = pygame.Surface((104, 104), pygame.SRCALPHA)
        center = (52, 52)
        for radius, alpha in ((42, 9), (33, 14), (24, 21)):
            _NS_sylara._aacircle(halo,
                (*_NS_sylara.PALETTE["wind_dark"], int(alpha * pulse)),
                center, radius)
        # Echo the cape and bow line without softening the pixel silhouette.
        _NS_sylara._aaline(halo,
            (*_NS_sylara.PALETTE["wind_mid"], int(34 * pulse)),
            (28, 64), (14, 52), 2)
        _NS_sylara._aaline(halo,
            (*_NS_sylara.PALETTE["wind_mid"], int(30 * pulse)),
            (68, 51), (85, 38), 1)
        surface.blit(halo, (x - 52, y - 52))


    def _draw_wind_aura(surface, x, y, phase):
        """Aura angin besar gaya Drakar: gradien 3 lapis di-cache +
        ember piksel naik (versi hijau dari rage aura)."""
        p = _NS_sylara.PALETTE
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        def build():
            aura = pygame.Surface((220, 190), pygame.SRCALPHA)
            core = (110, 95)
            # Gradien radial LANGSUNG (pygame.draw.circle menulis alpha
            # exact, TIDAK menumpuk seperti blit `_aacircle`) sehingga:
            #  - lapisan warna darkest->dark->mid->light->bright (Drakar)
            #  - alpha < 100 di ATAS kepala -> mask ukuran badan tetap
            #    melihat badan saja (audit v2: tinggi 51.2 px -> fix).
            for radius in range(95, 3, -1):
                t = 1.0 - radius / 95.0
                al = int(190 * t ** 1.35)
                if al <= 0:
                    continue
                if radius > 70:
                    col = p["wind_darkest"]
                elif radius > 48:
                    col = p["wind_dark"]
                elif radius > 28:
                    col = p["wind_mid"]
                elif radius > 12:
                    col = p["wind_light"]
                else:
                    col = p["wind_bright"]
                pygame.draw.circle(aura, (*col, min(255, al)), core, radius)
            pygame.draw.circle(aura, (*p["white"], 120), core, 4)
            return aura
        aura = _NS_sylara._static("sylara_wind_aura_drk", build)
        aura.set_alpha(int(255 * pulse))
        surface.blit(aura, (x - 110, y - 95))
        # Ember piksel naik — kunci "bernafas" gaya rage mist Drakar
        _NS_sylara._drk_embers(surface, x, y + 22, 14, phase, 185,
                               spread=58, rise=54, squash=.6)


    def _draw_wind_platform(surface, x, y, phase, skill):
        """Rune ring tanah gaya Drakar: ellipse berlapis + 12 spoke rune
        berputar + titik hot di ujung spoke."""
        p = _NS_sylara.PALETTE
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((200, 68), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*p["wind_darkest"], 200), (5, 20, 190, 36), 4)
        pygame.draw.ellipse(ring, (*p["wind_dark"], 220), (14, 24, 172, 30), 3)
        pygame.draw.ellipse(ring, (*p["wind_mid"], 230), (30, 28, 140, 22), 2)
        pygame.draw.ellipse(ring, (*p["wind_light"], 190), (46, 30, 108, 18), 1)
        surface.blit(ring, (x - 100, y - 34))

        # Spoke rune berputar (12) + tip hot — signature ground Drakar
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = x + int(math.cos(angle) * 55)
            y1 = y + int(math.sin(angle) * 10)
            x2 = x + int(math.cos(angle) * 88)
            y2 = y + int(math.sin(angle) * 15)
            pygame.draw.line(surface, (*p["wind_light"], 220), (x1, y1), (x2, y2), 2)
            pygame.draw.rect(surface, (*p["wind_bright"], 250),
                             (x2 - 1, y2 - 1, 3, 3))
            pygame.draw.rect(surface, (*p["white"], 255), (x2, y2, 1, 1))

        if skill:
            pygame.draw.ellipse(surface,
                                (*p["wind_bright"], int(130 * pulse)),
                                (x - 78, y - 22, 156, 44), 2)


    def _sy_progress(skill, timer):
        dur = float(_NS_sylara.SKILL_VISUAL_DURATION.get(skill, max(1, timer or 1)))
        return max(0.0, min(1.0, 1.0 - float(timer) / dur))

    def _sy_ribbon(surface, cx, cy, ang, length, phase, color, alpha,
                   waves=2.2, amp=7.0, width=2, fade=True):
        """Pita angin laminar (ciri Sylara): S-curve yang menirus."""
        if alpha <= 0 or length <= 4:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        prev = None
        steps = max(8, int(length / 7))
        for i in range(steps + 1):
            t = i / steps
            along = t * length
            off = math.sin(t * waves * math.pi + phase) * amp * (1.0 - t * 0.35)
            x = cx + ca * along + px * off
            y = cy + sa * along + py * off
            if prev is not None:
                al = int(alpha * (1.0 - t * 0.55 if fade else 1.0))
                w = max(1, int(width * (1.0 - t * 0.6)))
                _NS_sylara._aaline(surface, (*color, al), prev, (x, y), w)
            prev = (x, y)

    def _sy_wind_sheets(surface, x, y, facing, phase, alpha, fs, n=5):
        """Hembusan mendatar di belakang langkah — bahasa dash ranger."""
        p = _NS_sylara.PALETTE
        for i in range(n):
            t = (phase * 0.55 + i / float(n)) % 1.0
            sy = y - 18 + i * 7 * fs + math.sin(phase * 2.1 + i) * 2
            sx = x - facing * (8 + t * 38 * fs)
            ex = sx - facing * (22 + t * 18) * fs
            al = int(alpha * (1.0 - t) * (0.55 + 0.45 * ((i % 2))))
            if al <= 0:
                continue
            _skill_outlined_line(surface, (sx, sy), (ex, sy - 1),
                                 1 if i % 2 else 2, p["wind_bright"], al)

    def _sy_leaf_orbit(surface, cx, cy, radius, phase, count, fs, squash=0.46):
        p = _NS_sylara.PALETTE
        for i in range(count):
            t = (phase * 0.28 + i / float(count)) % 1.0
            a = phase * 0.9 + i * math.tau / count
            r = radius * (0.55 + 0.45 * _NS_sylara._hash01(i * 17))
            lx = cx + math.cos(a) * r
            ly = cy + math.sin(a) * r * squash - t * 10 * fs
            size = max(3.0, (4.5 + (i % 3)) * fs * (1.0 - t * 0.35))
            spin = a + t * 3.0
            dark = p["cloth_dark"] if i % 2 else p["leaf_ember"]
            mid = p["cloth_mid"] if i % 2 else p["leaf_gold"]
            light = p["cloth_light"] if i % 2 else p["wind_bright"]
            _NS_sylara._draw_leaf(surface, lx, ly, size, spin, dark, mid, light)

    def _sy_leaf_burst(surface, cx, cy, t, fs):
        """Ledakan daun saat skill baru keluar (bukan bintang Thorne)."""
        p = _NS_sylara.PALETTE
        n = 10
        for i in range(n):
            a = i * math.tau / n + t * 0.4
            r = (10 + t * 34) * fs * (0.7 + 0.3 * _NS_sylara._hash01(i * 9))
            lx = cx + math.cos(a) * r
            ly = cy + math.sin(a) * r * 0.55
            size = max(3.0, (7 - t * 4) * fs)
            _NS_sylara._draw_leaf(
                surface, lx, ly, size, a + t * 2,
                p["cloth_dark"], p["leaf_gold"], p["wind_white"])

    def _sy_grass_halo(surface, cx, cy, radius, phase, alpha, squash=1.0):
        """Cincin rumput/daun pada radius dunia — telegraph khas hutan.

        ``squash=1`` menjaga sampling lingkaran (tes world-space) kena.
        """
        p = _NS_sylara.PALETTE
        if alpha <= 0 or radius <= 2:
            return
        _skill_outlined_circle(surface, (cx, cy), int(radius), 3,
                               p["wind_mid"], int(alpha * 0.85))
        _skill_outlined_circle(surface, (cx, cy), max(4, int(radius * 0.92)), 1,
                               p["wind_bright"], int(alpha * 0.7))
        blades = max(14, int(radius / 7))
        for i in range(blades):
            a = phase * 0.15 + i * math.tau / blades
            bx = cx + math.cos(a) * radius
            by = cy + math.sin(a) * radius * squash
            sway = math.sin(phase * 2.4 + i) * 3
            tipx = bx + math.cos(a) * 7 + sway
            tipy = by + math.sin(a) * 4 - 5
            col = p["leaf_gold"] if i % 3 == 0 else p["wind_light"]
            _NS_sylara._aaline(surface, (*col, int(alpha)), (bx, by),
                               (tipx, tipy), 2 if i % 2 == 0 else 1)

    def _sy_vine_tether(surface, ax, ay, bx, by, phase, alpha, fs):
        """Tali hidup: sulur berdaun, bukan rantai/rune."""
        p = _NS_sylara.PALETTE
        dx, dy = bx - ax, by - ay
        dist = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / dist, dx / dist
        segs = 16
        prev = None
        for i in range(segs + 1):
            t = i / segs
            wob = math.sin(t * 5.0 + phase * 2.4) * (5.5 * fs)
            px = ax + dx * t + nx * wob
            py = ay + dy * t + ny * wob
            if prev is not None:
                _NS_sylara._aaline(surface, (*p["cloth_darkest"], alpha),
                                   prev, (px, py), max(2, int(4 * fs)))
                _NS_sylara._aaline(surface, (*p["cloth_mid"], alpha),
                                   prev, (px, py), max(1, int(2 * fs)))
                _NS_sylara._aaline(surface, (*p["leaf_gold"], int(alpha * 0.7)),
                                   prev, (px, py), 1)
            if i % 3 == 0:
                side = 1 if i % 6 == 0 else -1
                _NS_sylara._draw_leaf(
                    surface, px + nx * 6 * side, py + ny * 6 * side,
                    max(3.5, 5.0 * fs), math.atan2(ny, nx) + side * 0.6,
                    p["cloth_dark"], p["cloth_mid"], p["leaf_gold"])
            prev = (px, py)

    def _sy_fletch(surface, x, y, ang, size, alpha):
        """Jejak bulu anak panah (bukan chevron Thorne)."""
        p = _NS_sylara.PALETTE
        if alpha <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tip = (x + ca * size, y + sa * size)
        for s in (-1, 1):
            a = (x - ca * size * 0.4 + px * s * size * 0.55,
                 y - sa * size * 0.4 + py * s * size * 0.55)
            _NS_sylara._poly(surface, (*p["arrow_feather_d"], alpha),
                             [tip, a, (x - ca * size * 0.15, y - sa * size * 0.15)])
            _NS_sylara._poly(surface, (*p["arrow_feather"], alpha),
                             [tip,
                              (x + px * s * size * 0.28, y + py * s * size * 0.28),
                              (x + ca * size * 0.35, y + sa * size * 0.35)])

    def _sy_gale_tunnel(surface, ox, oy, tx, ty, progress, alpha, fs):
        """Terowongan angin terkompresi dari busur ke target (Powershot)."""
        p = _NS_sylara.PALETTE
        dx, dy = tx - ox, ty - oy
        dist = math.hypot(dx, dy) or 1.0
        ang = math.atan2(dy, dx)
        nx, ny = -dy / dist, dx / dist
        reach = dist * min(1.0, 0.35 + progress * 1.1)
        for lane, col, w in ((0.0, p["wind_dark"], 7),
                             (0.0, p["wind_mid"], 4),
                             (0.0, p["wind_bright"], 2)):
            _NS_sylara._sy_ribbon(
                surface, ox, oy, ang, reach, progress * 4.0 + lane,
                col, alpha, waves=1.6, amp=5.0 * fs, width=max(1, int(w * fs)))
        # dinding angin kiri/kanan
        for s in (-1, 1):
            _NS_sylara._sy_ribbon(
                surface, ox + nx * 10 * s * fs, oy + ny * 10 * s * fs,
                ang, reach * 0.92, progress * 3.2 + s,
                p["wind_light"], int(alpha * 0.75),
                waves=2.4, amp=4.0 * fs, width=max(1, int(2 * fs)))
        # fletching ghosts along the tunnel
        for i in range(4):
            t = (i / 4.0 + progress * 0.5) % 1.0
            fx = ox + dx / dist * reach * t
            fy = oy + dy / dist * reach * t
            _NS_sylara._sy_fletch(surface, fx, fy, ang, 9 * fs,
                                  int(alpha * (1.0 - t * 0.5)))

    def _draw_bow_release_flash(surface, x, y, facing, progress):
        """Hembusan daun + getar tali saat anak panah lepas (bukan star-burst)."""
        if progress < 0.42 or progress > 0.80:
            return
        p = _NS_sylara.PALETTE
        t = max(0.0, min(1.0, (progress - 0.42) / 0.30))
        intensity = math.sin(t * math.pi) if t < 0.9 else 0.0
        rs = _NS_sylara.RIG_SCALE
        flash_x = x + int(22 * rs) * facing
        flash_y = y - int(8 * rs)
        alpha = int(210 * intensity)
        # getaran tali: elips mendatar di nock
        for k, col in enumerate((p["wind_mid"], p["wind_bright"], p["wind_white"])):
            rx = int((10 + intensity * 16 - k * 4))
            ry = max(2, int(rx * 0.38))
            _NS_sylara._ellipse(surface, (*col, max(20, alpha - k * 40)),
                                (flash_x - rx, flash_y - ry, rx * 2, ry * 2), 2)
        if 0.50 < progress < 0.68:
            it = (progress - 0.50) / 0.18
            _NS_sylara._sy_leaf_burst(surface, flash_x, flash_y, it, 1.0)
        # smear angin ke arah tembak
        ang = 0.0 if facing > 0 else math.pi
        _NS_sylara._sy_ribbon(surface, flash_x, flash_y, ang,
                              18 + intensity * 28, progress * 6,
                              p["wind_bright"], alpha, waves=1.8, amp=5, width=2)

    def _draw_powershot_charge(surface, boss, x, y, timer, phase):
        """R Powershot — tarikan gale di busur, lalu terowongan angin ke target.

        Bukan X-slash / rune / magma.  3 fase: napas angin, charge terkompresi,
        lepas sebagai gale tunnel + daun tersapu.
        """
        p = _NS_sylara.PALETTE
        progress = _NS_sylara._sy_progress("r", timer)
        fs = _NS_sylara._fx_scale(boss)
        facing = boss.direction
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        tx, ty = _NS_sylara._target_position(boss, x, y)
        rs = _NS_sylara.RIG_SCALE
        bow_x = x + int(22 * rs) * facing
        bow_y = y - int(8 * rs)
        ang = math.atan2(ty - bow_y, tx - bow_x)

        # AKTIVASI: daun meledak dari nock + hembusan pendek
        if progress < 0.22:
            t = progress / 0.22
            _NS_sylara._sy_leaf_burst(surface, bow_x, bow_y, t, fs)
            _NS_sylara._sy_ribbon(surface, bow_x, bow_y, ang,
                                  40 * fs * t, phase,
                                  p["wind_bright"], int(220 * (1 - t)),
                                  waves=2.0, amp=6 * fs, width=3)

        # STEADY: tali bergetar, pita angin menggulung ke nock
        envelope = 1.0 if progress < 0.42 else max(0.0, 1.0 - (progress - 0.42) / 0.2)
        if envelope > 0.05 and progress < 0.55:
            for i in range(5):
                a = ang + math.pi + (i - 2) * 0.22
                _NS_sylara._sy_ribbon(
                    surface, bow_x, bow_y, a,
                    (18 + i * 4) * fs * envelope, phase * 2 + i,
                    p["wind_light"], int((140 + 50 * pulse) * envelope),
                    waves=2.6, amp=4 * fs, width=2)
            # orbit daun kecil di busur
            _NS_sylara._sy_leaf_orbit(surface, bow_x, bow_y, 22 * fs,
                                      phase, 6, fs, squash=0.7)
            _NS_sylara._ellipse(
                surface, (*p["wind_bright"], int(90 + 70 * pulse)),
                (bow_x - int(14 * fs), bow_y - int(7 * fs),
                 int(28 * fs), int(14 * fs)), 2)

        # RELEASE: gale tunnel + sapuan daun di target
        if progress >= 0.38:
            t = min(1.0, (progress - 0.38) / 0.40)
            al = int(220 * (1.0 - max(0.0, progress - 0.78) / 0.22))
            _NS_sylara._sy_gale_tunnel(surface, bow_x, bow_y, tx, ty,
                                       t, max(40, al), fs)
            if progress > 0.55:
                _NS_sylara._sy_leaf_orbit(surface, tx, ty, 26 * fs,
                                          phase * 1.4, 8, fs, squash=0.5)
            if progress > 0.78:
                _NS_sylara._sy_leaf_burst(surface, tx, ty,
                                          (progress - 0.78) / 0.22, fs)

    def _draw_windrun_ground(surface, boss, x, y, timer, phase):
        """W Windrun — siklon daun + halo rumput di radius dunia 70.

        Bukan crescent helix / rune ring Drakar.  Telegraph = cincin rumput
        tepat di 70 px dunia (tetap kebaca tes world-space).
        """
        p = _NS_sylara.PALETTE
        progress = _NS_sylara._sy_progress("w", timer)
        fs = _NS_sylara._fx_scale(boss)
        facing = boss.direction
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        rng = _NS_sylara._ring_r(boss, 70, surface)
        gy = y + 14

        if progress < 0.16:
            t = progress / 0.16
            _NS_sylara._sy_leaf_burst(surface, x, gy, t, fs)
            _NS_sylara._sy_wind_sheets(surface, x, y, facing, phase,
                                       int(230 * (1 - t)), fs, n=6)

        # STEADY: halo rumput di radius dunia + siklon daun
        _NS_sylara._sy_grass_halo(surface, x, gy, rng,
                                  phase, int(150 + 60 * pulse), squash=1.0)
        inner = max(8, int(rng * (0.55 + 0.12 * math.sin(phase * 1.6))))
        _skill_outlined_circle(surface, (x, gy), inner, 2,
                               p["wind_light"], int(110 + 50 * pulse))
        _NS_sylara._sy_leaf_orbit(surface, x, gy, rng * 0.82, phase, 9, fs,
                                  squash=0.42)
        _NS_sylara._sy_wind_sheets(surface, x, y + 8, facing, phase,
                                   int(160 + 40 * pulse), fs, n=6)

        # AKHIR: siklon mengencang, daun tersedot
        if progress > 0.78:
            t = (progress - 0.78) / 0.22
            conv = max(6, int(rng * (1.0 - t * 0.7)))
            _skill_outlined_circle(surface, (x, gy), conv, 3,
                                   p["wind_white"], int(200 * t))
            _NS_sylara._sy_leaf_burst(surface, x, gy, t, fs)

        # TELEGRAPH arah lari: fletching, bukan chevron Thorne
        for i in range(4):
            t = (i / 4.0 + phase * 0.35) % 1.0
            fx = x + facing * rng * (0.25 + 0.7 * t)
            fy = gy + math.sin(phase + i) * 4
            _NS_sylara._sy_fletch(surface, fx, fy,
                                  0.0 if facing > 0 else math.pi,
                                  max(8, int(rng * 0.09)),
                                  int(180 * (1.0 - t * 0.4)))

    def _draw_windrun_trail(surface, x, y, facing, phase):
        """Afterimage dash: lembar angin + daun terseret, bukan ghost orb."""
        p = _NS_sylara.PALETTE
        _NS_sylara._sy_wind_sheets(surface, x, y, facing, phase, 200, 1.0, n=7)
        for i in range(4):
            t = (phase * 0.4 + i / 4.0) % 1.0
            lx = x - facing * (14 + t * 36)
            ly = y - 10 + math.sin(phase * 2 + i) * 8
            _NS_sylara._draw_leaf(
                surface, lx, ly, 6 - t * 2, phase + i,
                p["cloth_dark"], p["leaf_gold"], p["wind_bright"])
        # siluet cape-ish streaks
        for i in range(3):
            ox = x - facing * (10 + i * 11)
            _NS_sylara._aaline(surface, (*p["cloak_mid"], 90 - i * 20),
                               (ox, y - 16), (ox - facing * 16, y + 10), 3)

    def _draw_shackle_ground(surface, boss, x, y, timer, pulse):
        """E Shackle Shot — sulur hidup mengikat target.

        Bukan rantai/rune/reticle.  3 fase: sulur menyembur, mengerat,
        karangan daun menguncup.
        """
        p = _NS_sylara.PALETTE
        progress = _NS_sylara._sy_progress("e", timer)
        fs = _NS_sylara._fx_scale(boss)
        facing = boss.direction
        tx, ty = _NS_sylara._target_position(boss, x, y)
        rs = _NS_sylara.RIG_SCALE
        sx = x + int(20 * rs) * facing
        sy = y - int(6 * rs)
        ang = math.atan2(ty - sy, tx - sx)

        if progress < 0.16:
            t = progress / 0.16
            _NS_sylara._sy_leaf_burst(surface, sx, sy, t, fs)
            _NS_sylara._sy_ribbon(surface, sx, sy, ang, 36 * fs * t, pulse,
                                  p["cloth_light"], int(220 * (1 - t)),
                                  waves=3.0, amp=6 * fs, width=3)

        # STEADY: sulur + karangan di target
        al = int(170 + 50 * math.sin(pulse * 3))
        _NS_sylara._sy_vine_tether(surface, sx, sy, tx, ty - 6, pulse, al, fs)
        wreath = max(8, int(16 * fs))
        _NS_sylara._sy_leaf_orbit(surface, tx, ty - 6, wreath + 6, pulse, 7, fs,
                                  squash=0.85)
        _skill_outlined_circle(surface, (tx, ty - 6), wreath, 2,
                               p["cloth_light"], int(150 + 50 * math.sin(pulse)))

        # fletching along vine (shot reads as an arrow that became a vine)
        for i in range(3):
            t = (i / 3.0 + pulse * 0.3) % 1.0
            fx = sx + (tx - sx) * t
            fy = sy + (ty - 6 - sy) * t
            _NS_sylara._sy_fletch(surface, fx, fy, ang, 8 * fs,
                                  int(160 * (1 - t * 0.4)))

        if progress > 0.78:
            t = (progress - 0.78) / 0.22
            cage = max(5, int((wreath + 22 * fs) * (1.0 - t)))
            _skill_outlined_circle(surface, (tx, ty - 6), cage, 3,
                                   p["leaf_gold"], int(220 * (0.4 + 0.6 * t)))
            _NS_sylara._sy_leaf_burst(surface, tx, ty - 6, t, fs)

        if not getattr(boss, "_sy_shackle_spawned", False):
            _NS_sylara._spawn_shackle(boss, x, y)
            boss._sy_shackle_spawned = True
        if timer < 5:
            boss._sy_shackle_spawned = False

    def _draw_focus_fire_ground(surface, boss, x, y, timer, phase):
        """Q Focus Fire — kipas fletching + spiral angin, bukan rune AOE."""
        p = _NS_sylara.PALETTE
        progress = _NS_sylara._sy_progress("q", timer)
        fs = _NS_sylara._fx_scale(boss)
        pulse = math.sin(phase * 2.2) * 0.25 + 0.75
        world_r = int(getattr(boss, "skill_range", 200) or 200)
        rng = _NS_sylara._ring_r(boss, world_r, surface)
        facing = boss.direction
        gy = y + 40
        ang = 0.0 if facing > 0 else math.pi
        rs = _NS_sylara.RIG_SCALE
        bow_x = x + int(20 * rs) * facing
        bow_y = y - int(8 * rs)

        if progress < 0.14:
            t = progress / 0.14
            _NS_sylara._sy_leaf_burst(surface, bow_x, bow_y, t, fs)
            for k in range(5):
                a = ang + (k - 2) * 0.18
                _NS_sylara._sy_ribbon(surface, bow_x, bow_y, a,
                                      (30 + k * 6) * fs * t, phase + k,
                                      p["wind_bright"], int(220 * (1 - t)),
                                      waves=2.0, amp=5 * fs, width=2)

        # STEADY: spiral angin di kaki + cincin fletching baca-jangkauan
        halo = max(18, int(rng * 0.42))
        _NS_sylara._sy_grass_halo(surface, x, gy, halo, phase,
                                  int(130 + 50 * pulse), squash=1.0)
        # outer readable ring (clamped) of fletch marks — wind-green
        mark_r = max(24, int(rng * 0.62))
        _skill_outlined_circle(surface, (x, y), mark_r, 2,
                               p["wind_mid"], int(110 + 50 * pulse))
        for i in range(5):
            a = phase * 0.4 + i * math.tau / 10
            px = x + math.cos(a) * mark_r
            py = y + math.sin(a) * mark_r * 0.55
            _NS_sylara._sy_fletch(surface, px, py, a + math.pi * 0.5,
                                  max(7, int(10 * fs)),
                                  int(160 + 50 * pulse))
        # pita angin ke arah hadap (volley corridor)
        for k in range(3):
            a = ang + (k - 1) * 0.12
            _NS_sylara._sy_ribbon(
                surface, bow_x, bow_y, a, min(rng * 0.7, 120 * fs),
                phase * 1.6 + k, p["wind_light"],
                int(140 + 40 * pulse), waves=1.8, amp=6 * fs, width=2)
        _NS_sylara._sy_leaf_orbit(surface, x, gy, halo * 0.9, phase, 8, fs)

        if progress > 0.80:
            t = (progress - 0.80) / 0.20
            _NS_sylara._sy_leaf_burst(surface, bow_x, bow_y, t, fs)

        for i in range(4):
            t = (i / 4.0 + phase * 0.45) % 1.0
            fx = x + facing * mark_r * (0.2 + 0.75 * t)
            _NS_sylara._sy_fletch(surface, fx, y + 8, ang,
                                  max(8, int(mark_r * 0.08)),
                                  int(190 * (1.0 - t * 0.35)))

    def _draw_focus_fire_effect(surface, boss, x, y, timer, phase):
        """Q foreground: volley spawn + spiral fletching di busur."""
        p = _NS_sylara.PALETTE
        progress = _NS_sylara._sy_progress("q", timer)
        fs = _NS_sylara._fx_scale(boss)
        facing = boss.direction
        rs = _NS_sylara.RIG_SCALE
        bow_x = x + int(20 * rs) * facing
        bow_y = y - int(8 * rs)

        fire_interval = 8
        if not hasattr(boss, "_sy_focus_last_shot"):
            boss._sy_focus_last_shot = -100
        if 0.2 < progress < 0.9:
            if timer % fire_interval == 0 and boss._sy_focus_last_shot != timer:
                _NS_sylara._spawn_focus_fire_volley(boss, x, y)
                boss._sy_focus_last_shot = timer
        if progress < 0.2:
            boss._sy_focus_last_shot = -100

        # spiral fletching around the bow
        for i in range(6):
            a = phase * 2.8 + i * math.tau / 6
            r = (14 + 4 * math.sin(phase * 2 + i)) * fs
            px = bow_x + math.cos(a) * r
            py = bow_y + math.sin(a) * r * 0.72
            _NS_sylara._sy_fletch(surface, px, py, a + math.pi * 0.5,
                                  7 * fs, 190)
        _NS_sylara._sy_ribbon(
            surface, bow_x, bow_y, 0.0 if facing > 0 else math.pi,
            28 * fs, phase * 3, p["wind_white"], 180,
            waves=2.8, amp=4 * fs, width=2)
        _NS_sylara._sy_leaf_orbit(surface, x, y - 6, 28 * fs, phase, 5, fs,
                                  squash=0.7)


    def draw_boss(surface, boss, x, y):
        _NS_sylara.draw_sylara(surface, boss, x, y)

# ====================================================================
# kaizen.py
# ====================================================================
class _NS_kaizen:
    """Kaizen - DOODLE MASTERWORK (rewrite penuh renderer).

    Bahasa gambar baru: "buku sketsa / doodle sketchbook".
    Sebelumnya pixel-art masterwork; sekarang karakter digambar tangan
    dengan pulpen tinta + spidol + krayon di atas kertas.

    Disiplin doodle (paritas dengan namespace _NS_grimjaw):
      1. GARIS TINTA BERGOYANG (boiling lines) - outline digambar sebagai
         polyline yang di-jitter deterministik (hash segmen murni dari
         pose) sehingga sprite cache tetap valid; ganti fase animasi =
         garis "mendidih".
      2. ISI SPIDOL BERCELAH KERTAS (coloring-book gap) - fill poligon
         ditarik ke centroid ~1.5 px sehingga selalu ada celah kertas
         tipis antara isi marker dan outline.
      3. ARSIRAN & SKRIBEL - bayangan = arsiran pensil pendek sejajar +
         skribel loop (coretan "eee") untuk angin & volume; highlight =
         goresan gel-pen putih.
      4. ANGIN DOODLE - lidah teardrop ber-outline tinta + skribel inti,
         bintang kilau gambar-tangan, awan "poof" bergoyang.
      5. KATANA DOODLE - bilah sketsa dengan sori camber, hamon bergoyang,
         tsuba 4-lobe, ito berlian, glint gel-pen.

    KONTRAK LAMA DIPERTAHANKAN PENUH:
      * geometri bilah (_katana_angle / _katana_tip_local / _target_position
        / _world_to_local + konstanta timeline), controller serangan
        (_update_attack_anim / _attack_pose), jembatan lapisan hidup
        (_live_module / _fx_live_owned / _FX_LIVE), telegraph world-space
        (_fx_scale cap 2.6 / _ring_r / _skill_progress), dan seluruh nama
        simbol publik daftar heroes/_EXTRA['kaizen'] - sehingga
        heroes/kaizen_fx.py & pipeline sprite-cache bekerja tanpa perubahan.

    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    _STATIC_SURFACES = {}
    _SCRATCH_POOL = {}
    SKILL_VISUAL_DURATION = {"q": 39, "w": 59, "e": 39, "r": 66}
    BLADE_LEN = 62
    ATTACK_WINDUP_END = 0.28
    ATTACK_SWING_END = 0.72
    ATTACK_IMPACT = 0.54

    # ── jembatan ke lapisan FX hidup (heroes/kaizen_fx.py) ──────────
    _LIVE_MOD = None

    class _LiveFlag:
        """Penanda sederhana yang bisa di-set dari fungsi static."""
        __slots__ = ("v",)

        def __init__(self):
            self.v = False

    #: Dibaca rig: True = smear/ayunan sudah diambil alih lapisan hidup
    #: 60fps, jadi canvas tidak menggambarnya dua kali.
    _FX_LIVE = _LiveFlag()

    @staticmethod
    def _live_module():
        """Muat ``heroes.kaizen_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_kaizen
        if NS._LIVE_MOD is None:
            try:
                from heroes import kaizen_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "KAIZEN_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def _fx_live_owned(hero):
        """True kalau lapisan hidup mengambil alih FX unit ini."""
        try:
            mod = _NS_kaizen._live_module()
            if mod is None:
                return False
            return bool(mod.owns(hero))
        except Exception:
            return False

    def _static(key, builder):
        surf = _NS_kaizen._STATIC_SURFACES.get(key)
        if surf is None:
            if len(_NS_kaizen._STATIC_SURFACES) > 96:
                _NS_kaizen._STATIC_SURFACES.clear()
            surf = builder()
            _NS_kaizen._STATIC_SURFACES[key] = surf
        return surf

    def _scratch(w, h):
        """Surface sementara POOL (fill 0 lalu pakai)."""
        pool = _NS_kaizen._SCRATCH_POOL
        key = (int(w), int(h))
        surf = pool.get(key)
        if surf is None:
            if len(pool) > 24:
                pool.clear()
            surf = pygame.Surface(key, pygame.SRCALPHA)
            pool[key] = surf
        surf.fill((0, 0, 0, 0))
        return surf

    # ------------------------------------------------------------------
    # PALETTE - "doodle sketchbook" (spidol flat + tinta + kertas)
    # ------------------------------------------------------------------
    PALETTE = {
        # Tinta & kertas (material baru gaya doodle)
        "ink":            (20,  17,  22),
        "ink_soft":       (44,  38,  54),
        "paper":          (250, 246, 236),

        # Skin - spidol tan hangat
        "skin_darkest":   (120,  84,  66),
        "skin_dark":      (158, 114,  86),
        "skin_mid":       (196, 150, 112),
        "skin_light":     (226, 186, 146),
        "skin_high":      (246, 218, 182),

        # Hair - spidol cokelat gelap (malam dingin di bayangan)
        "hair_darkest":   (30,  24,  22),
        "hair_dark":      (52,  42,  34),
        "hair_mid":       (86,  68,  50),
        "hair_light":     (128, 102,  70),
        "hair_shine":     (176, 140,  96),
        "hair_high":      (216, 176, 120),

        # Outfit - indigo doodle (bayangan ungu, cahaya sian)
        "cloth_darkest":  (16,  20,  32),
        "cloth_deep":     (22,  28,  46),
        "cloth_dark":     (38,  50,  86),
        "cloth_mid":      (62,  84, 134),
        "cloth_light":    (102, 138, 194),
        "cloth_high":     (154, 194, 234),

        # Scarf/sash - biru terang spidol
        "scarf_deep":     (24,  46, 102),
        "scarf_dark":     (46,  76, 148),
        "scarf_mid":      (84, 130, 206),
        "scarf_light":    (136, 182, 242),
        "scarf_high":     (188, 220, 255),

        # Pants / hakama
        "pants_dark":     (26,  36,  66),
        "pants_mid":      (46,  60, 110),
        "pants_light":    (80, 102, 162),

        # Leather belt / harness
        "leather_dark":   (64,  42,  26),
        "leather_mid":    (106,  72,  44),
        "leather_light":  (152, 106,  68),

        # Sword - katana (pensil baja dingin + specular gel-pen)
        "steel_darkest":  (42,  46,  56),
        "steel_dark":     (76,  82,  94),
        "steel_mid":      (126, 134, 148),
        "steel_light":    (184, 190, 202),
        "steel_shine":    (230, 236, 246),

        # Handle wrap (ito berlian merah)
        "wrap_dark":      (64,  22,  28),
        "wrap_mid":       (118,  42,  52),
        "wrap_light":     (176,  72,  84),

        # Gold accents
        "gold_dark":      (106,  72,  24),
        "gold_mid":       (168, 126,  44),
        "gold_light":     (226, 186,  82),
        "gold_shine":     (250, 222, 132),

        # Saya (sarung lacquer merah-delima)
        "saya_dark":      (64,  16,  24),
        "saya_mid":       (114,  30,  44),
        "saya_light":     (162,  50,  62),
        "saya_shine":     (214, 104, 108),

        # Wind - sian doodle (FX utama)
        "wind_deep":      (18,  40,  82),
        "wind_darkest":   (34,  64, 116),
        "wind_dark":      (58, 112, 176),
        "wind_mid":       (112, 178, 230),
        "wind_light":     (176, 222, 250),
        "wind_bright":    (216, 242, 255),
        "wind_white":     (246, 252, 255),
        "wind_pale":      (232, 246, 255),

        # Eye
        "eye_white":      (248, 252, 255),
        "eye_iris":       (206, 152,  54),
        "eye_iris_light": (244, 202, 104),
        "eye_pupil":      (18,  18,  22),
        "eye_glow":       (160, 228, 255),

        # Misc
        "cord_dark":      (128,  32,  42),
        "cord_mid":       (194,  56,  66),
        "shadow":         (0,   0,   0),
        "shadow_deep":    (20,  17,  22),   # = tinta (drop shadow jadi tinta)
        "white":          (255, 255, 255),
    }

    #: Warna tinta default (dipakai semua primitif doodle).
    INK = PALETTE["ink"]

    def _clamp(color):
        n = len(color)
        if n == 3:
            r, g, b = color
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                if type(r) is int and type(g) is int and type(b) is int:
                    return color
                return (int(r), int(g), int(b))
        else:
            r, g, b, a = color
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255 \
                    and 0 <= a <= 255:
                if type(r) is int and type(g) is int and type(b) is int \
                        and type(a) is int:
                    return color
                return (int(r), int(g), int(b), int(a))
        if type(color) is tuple and len(color) == 3:
            _r, _g, _b = color
            if (type(_r) is int and type(_g) is int and type(_b) is int
                    and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
                return color
        return tuple(max(0, min(255, int(c))) for c in color)

    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_kaizen._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = (int(i) * 0x9E3779B1) & 0xFFFFFFFF
        x ^= x >> 15
        x = (x * 0x85EBCA6B) & 0xFFFFFFFF
        x ^= x >> 13
        return (x & 0xFFFF) / 65536.0

    def _rgba(color, alpha):
        c = _NS_kaizen._clamp(color)[:3]
        return (c[0], c[1], c[2], max(0, min(255, int(alpha))))

    # ------------------------------------------------------------------
    # Primitif gambar klasik (kompatibilitas + dipakai anggota FX)
    # ------------------------------------------------------------------
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaizen._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = _NS_kaizen._scratch(radius * 2 + 4, radius * 2 + 4)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_kaizen.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaizen._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = _NS_kaizen._scratch(w, h)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_kaizen._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = _NS_kaizen._scratch(w, h)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_kaizen._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = _NS_kaizen._scratch(rw + 4, rh + 4)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_kaizen._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = _NS_kaizen._scratch(rw + 4, rh + 4)
            pygame.draw.rect(temp, color, (2, 2, rw, rh),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)

    # ===================================================================
    # PRIMITIF DOODLE - inti gaya sketchbook
    # ===================================================================
    def _jit(seed, amp=1.0):
        return (_NS_kaizen._hash01(seed) - 0.5) * 2.0 * amp

    def _seed_q(phase, salt=0):
        return int(phase * 3.0) * 131 + int(salt) * 977

    _JIT_CACHE = {}

    def _jitters(n, seed, amp=0.82):
        key = (n, seed)
        got = _NS_kaizen._JIT_CACHE.get(key)
        if got is not None:
            return got
        s7 = seed * 131
        s11 = seed * 197
        h01 = _NS_kaizen._hash01
        two = 2.0 * amp
        tan = 2.0 * amp * 0.36
        out = []
        for i in range(n):
            out.append(((h01(s7 + i * 7) - 0.5) * two,
                        (h01(s11 + i * 11) - 0.5) * tan))
        if len(_NS_kaizen._JIT_CACHE) > 2048:
            _NS_kaizen._JIT_CACHE.clear()
        _NS_kaizen._JIT_CACHE[key] = out
        return out

    def _apply_jitter(pts, js, closed, scale=1.0):
        n = len(pts)
        m = len(js)
        out = []
        rng = range(n) if closed else range(1, n - 1)
        if not closed and n:
            out.append(pts[0])
        for i in rng:
            x, y = pts[i]
            jn, jt = js[i % m]
            jn *= scale
            jt *= scale
            px, py = pts[i - 1]
            nx, ny = pts[(i + 1) % n]
            dx, dy = nx - px, ny - py
            L = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L, dy / L
            out.append((x - uy * jn + ux * jt, y + ux * jn + uy * jt))
        if not closed and n > 1:
            out.append(pts[n - 1])
        return out

    def _wobble_pts(pts, seed, amp=1.1):
        return _NS_kaizen._apply_jitter(
            pts, _NS_kaizen._jitters(len(pts), seed, amp), False)

    def _wobble_closed(pts, seed, amp=1.1):
        return _NS_kaizen._apply_jitter(
            pts, _NS_kaizen._jitters(len(pts), seed, amp), True)

    def _subdiv(a, b, step=10.0):
        ax, ay = a
        bx, by = b
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / step))
        return [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n)
                for i in range(n + 1)]

    def _ipoints(pts):
        return [(int(x + 0.5), int(y + 0.5)) for x, y in pts]

    def _ink_stroke(surface, ink, a, b, width=2, seed=0, alpha=255,
                    passes=1, step=9.0):
        """GARIS TINTA doodle: satu goresan bersih ber-goyangan halus."""
        if alpha <= 0:
            return
        pts = _NS_kaizen._subdiv(a, b, step)
        js = _NS_kaizen._jitters(len(pts), seed, 0.82)
        w1 = _NS_kaizen._apply_jitter(pts, js, False)
        pygame.draw.lines(surface, _NS_kaizen._rgba(ink, alpha), False,
                          _NS_kaizen._ipoints(w1), max(1, width))

    def _ink_polyline(surface, ink, pts, width=2, seed=0, alpha=255,
                      close=False, passes=1):
        n = len(pts)
        if n < 2 or alpha <= 0:
            return
        js = _NS_kaizen._jitters(n, seed, 0.82)
        w1 = _NS_kaizen._apply_jitter(pts, js, close)
        pygame.draw.lines(surface, _NS_kaizen._rgba(ink, alpha), close,
                          _NS_kaizen._ipoints(w1), max(1, width))

    def _inset_pts(pts, gap=1.5):
        n = float(len(pts))
        cx = sum(p[0] for p in pts) / n
        cy = sum(p[1] for p in pts) / n
        out = []
        for x, y in pts:
            dx, dy = x - cx, y - cy
            L = math.hypot(dx, dy) or 1.0
            k = max(0.0, L - gap) / L
            out.append((cx + dx * k, cy + dy * k))
        return out

    def _marker_poly(surface, fill, pts, seed=0, ink=None, width=2,
                     gap=1.5, alpha=255, fill_alpha=255, close=True,
                     passes=2):
        n = len(pts)
        if n < 3:
            return
        need_ink = ink is not None and alpha > 0
        js = _NS_kaizen._jitters(n, seed, 1.05) if need_ink else None
        w1 = _NS_kaizen._apply_jitter(pts, js, close) if js else pts
        if fill is not None and fill_alpha > 0:
            if gap > 0:
                fp = _NS_kaizen._inset_pts(pts, gap)
                fp = _NS_kaizen._apply_jitter(fp, js, close, 0.55) \
                    if js else fp
            else:
                fp = pts
            pygame.draw.polygon(surface,
                                _NS_kaizen._rgba(fill, fill_alpha),
                                _NS_kaizen._ipoints(fp))
        if need_ink:
            pygame.draw.lines(surface, _NS_kaizen._rgba(ink, alpha), close,
                              _NS_kaizen._ipoints(w1),
                              width + 1 if width >= 2 else max(1, width))

    def _ink_ellipse(surface, fill, cx, cy, rx, ry, seed=0, ink=None,
                     width=2, rot=0.0, alpha=255, fill_alpha=255, n=11,
                     gap=1.4, passes=2, rwob=0.05):
        if rx <= 0.5 or ry <= 0.5:
            return
        if abs(rx - ry) <= 1.0 and abs(rot) < 1e-3 and rx <= 9.0:
            r = max(1, int(rx))
            if fill is not None and fill_alpha > 0:
                _NS_kaizen._aacircle(surface,
                                     _NS_kaizen._rgba(fill, fill_alpha),
                                     (cx, cy), r, 0)
            if ink is not None and width > 0 and alpha > 0:
                _NS_kaizen._aacircle(surface,
                                     _NS_kaizen._rgba(ink, alpha),
                                     (cx, cy), r + max(1, int(gap)),
                                     max(1, width))
            return
        if n < 11 and max(rx, ry) > 5.0:
            n = 11
        n = max(n, int(min(20, 9 + (rx + ry) * 0.45)))
        ca, sa = math.cos(rot), math.sin(rot)
        pts = []
        for i in range(n):
            t = i / n * math.tau
            w = 1.0 + _NS_kaizen._jit(seed * 53 + i * 29, rwob)
            x = math.cos(t) * rx * w
            y = math.sin(t) * ry * w
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        _NS_kaizen._marker_poly(surface, fill, pts, seed, ink, width,
                                gap, alpha, fill_alpha, True, passes)

    def _tube(surface, a, b, width, fill, ink, seed, alpha=255,
              shade=None):
        """Tabung anggota badan: stroke tinta lebar di bawah + isi marker."""
        if alpha <= 0:
            return
        pts = _NS_kaizen._subdiv(a, b, 10.0)
        js = _NS_kaizen._jitters(len(pts), seed, 0.72)
        w_ink = _NS_kaizen._apply_jitter(pts, js, False)
        pygame.draw.lines(surface, _NS_kaizen._rgba(ink, alpha), False,
                          _NS_kaizen._ipoints(w_ink), width + 4)
        w_fill = _NS_kaizen._apply_jitter(pts, js, False, 0.45)
        pygame.draw.lines(surface, _NS_kaizen._rgba(fill, alpha), False,
                          _NS_kaizen._ipoints(w_fill), width)
        if shade is not None:
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L * (width * 0.22), dx / L * (width * 0.22)
            s0 = (a[0] + nx, a[1] + ny)
            s1 = (b[0] + nx, b[1] + ny)
            ws = _NS_kaizen._apply_jitter(
                _NS_kaizen._subdiv(s0, s1, 8.0), js, False, 0.6)
            pygame.draw.lines(surface, _NS_kaizen._rgba(shade, alpha),
                              False, _NS_kaizen._ipoints(ws),
                              max(1, width // 3))

    def _scribble(surface, color, cx, cy, rx, ry, seed, alpha=150,
                  loops=3, angle=0.0, width=2):
        """Coretan loop "eee" khas doodle - arsiran angin / volume / asap."""
        if rx <= 0.5 or ry <= 0.5 or alpha <= 0:
            return
        ca, sa = math.cos(angle), math.sin(angle)
        ph = _NS_kaizen._jit(seed, 2.2)
        s17, s29 = seed * 17, seed * 29
        h01 = _NS_kaizen._hash01
        pts = []
        steps = 12
        for i in range(steps + 1):
            t = i / steps
            u = (t - 0.5) * 2.0
            v = math.sin(t * loops * math.tau + ph) * (1.0 - 0.35 * abs(u))
            x = u * rx + (h01(s17 + i) - 0.5) * 1.4
            y = v * ry + (h01(s29 + i) - 0.5) * 1.4
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        pygame.draw.lines(surface, _NS_kaizen._rgba(color, alpha), False,
                          _NS_kaizen._ipoints(pts), width)

    def _hatch_patch(surface, color, cx, cy, w, h, seed, alpha=110,
                     gap=4.0, angle=-0.7, width=1):
        """Arsiran pensil pendek sejajar (bayangan doodle)."""
        if alpha <= 0 or w < 3 or h < 3:
            return
        ca, sa = math.cos(angle), math.sin(angle)
        nca, nsa = math.cos(angle + math.pi / 2), math.sin(angle + math.pi / 2)
        rows = max(1, int(h // gap))
        for r in range(rows):
            t = (r + 0.5) * gap - h / 2.0
            L = w * (0.5 + 0.5 * _NS_kaizen._hash01(seed * 31 + r * 7))
            off = _NS_kaizen._jit(seed * 17 + r * 3, 1.1)
            x0 = cx + nca * (t + off) - ca * L * 0.5
            y0 = cy + nsa * (t + off) - sa * L * 0.5
            x1 = x0 + ca * L
            y1 = y0 + sa * L
            pygame.draw.line(surface, _NS_kaizen._rgba(color, alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             width)

    def _doodle_star(surface, cx, cy, r, color, alpha, seed=0, spikes=6,
                     width=2, ink=None, rot=0.0):
        """Bintang kilau gambar-tangan: goresan radial ber-jitter."""
        if alpha <= 0 or r <= 1:
            return
        for i in range(spikes):
            a = rot + i * (math.tau / spikes) + \
                _NS_kaizen._jit(seed * 13 + i * 7, 0.16)
            r0 = r * (0.05 + 0.12 * _NS_kaizen._hash01(seed + i * 31))
            r1 = r * (0.70 + 0.42 * _NS_kaizen._hash01(seed * 7 + i * 17))
            x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
            x1, y1 = cx + math.cos(a) * r1, cy + math.sin(a) * r1
            pygame.draw.line(surface, _NS_kaizen._rgba(color, alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             width)
        if ink is not None:
            _NS_kaizen._aacircle(surface, _NS_kaizen._rgba(ink, alpha),
                                 (cx, cy), max(1, int(r * 0.14)))

    def _poof(surface, cx, cy, r, color, alpha, seed=0, puffs=4,
              width=2, ink=None, fill=None, fill_alpha=60):
        """Awan "poof" doodle: beberapa arc bergoyang membentuk ledakan."""
        if alpha <= 0 or r <= 1:
            return
        for k in range(puffs):
            a = k * (math.tau / puffs) + _NS_kaizen._jit(seed + k * 5, 0.3)
            rr = r * (0.42 + 0.3 * _NS_kaizen._hash01(seed * 3 + k * 11))
            px = cx + math.cos(a) * r * 0.55
            py = cy + math.sin(a) * r * 0.5
            _NS_kaizen._ink_ellipse(surface, fill, px, py, rr, rr * 0.82,
                                    seed * 17 + k, ink, width,
                                    alpha=alpha, fill_alpha=fill_alpha,
                                    n=9, gap=0.0, passes=1)

    def _speed_ticks(surface, color, cx, cy, ang, count, length, alpha,
                     seed=0, width=2, spread=10.0):
        """Garis kecepatan pendek sejajar (membelakangi arah gerak)."""
        if alpha <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nca, nsa = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
        for i in range(count):
            t = (i - (count - 1) / 2.0) * spread
            L = length * (0.55 + 0.45 * _NS_kaizen._hash01(seed + i * 13))
            j = _NS_kaizen._jit(seed * 7 + i * 3, 1.5)
            x0 = cx + nca * (t + j)
            y0 = cy + nsa * (t + j)
            x1 = x0 - ca * L
            y1 = y0 - sa * L
            pygame.draw.line(surface, _NS_kaizen._rgba(color, alpha),
                             (round(x0), round(y0)), (round(x1), round(y1)),
                             width)

    def _wind_tongue(surface, base, direction, length, width, seed,
                     fill, inner, ink, alpha=255, bend=0.4,
                     scrib=True, gap=1.1):
        """Satu lidah angin doodle (wind teardrop) - paritas lidah api."""
        if alpha <= 0 or length < 3:
            return
        bx, by = base
        dx, dy = direction
        nx, ny = -dy, dx
        side = 1.0 if _NS_kaizen._hash01(seed * 5 + 2) > 0.5 else -1.0
        bend_amt = bend * length * side
        tipx = bx + dx * length + nx * bend_amt
        tipy = by + dy * length + ny * bend_amt
        m1x = bx + dx * length * 0.52 + nx * bend_amt * 0.85
        m1y = by + dy * length * 0.52 + ny * bend_amt * 0.85
        left = (bx + nx * width * 0.5, by + ny * width * 0.5)
        right = (bx - nx * width * 0.5, by - ny * width * 0.5)
        lm = (m1x + nx * width * 0.30, m1y + ny * width * 0.30)
        rm = (m1x - nx * width * 0.30, m1y - ny * width * 0.30)
        pts = [left, lm, (tipx, tipy), rm, right]
        _NS_kaizen._marker_poly(surface, fill, pts, seed, ink, 2, gap,
                                alpha, alpha, True, 2 if length >= 18 else 1)
        if scrib and length >= 12:
            _NS_kaizen._scribble(
                surface, inner,
                (bx + dx * length * 0.34 + nx * bend_amt * 0.45),
                (by + dy * length * 0.34 + ny * bend_amt * 0.45),
                length * 0.22, width * 0.42, seed * 3 + 1,
                min(255, int(alpha * 0.85)), 2, math.atan2(dy, dx), 2)

    def _ember_marks(surface, cx, cy, w, h, seed, color, alpha, count=4,
                     phase=0.0):
        """Mote angin doodle naik: titik + garis kecil deterministik."""
        if alpha <= 0:
            return
        for i in range(count):
            t = _NS_kaizen._hash01(seed * 31 + i * 7)
            rise = (_NS_kaizen._hash01(seed * 17 + i * 13) +
                    phase * (0.35 + 0.3 * t)) % 1.0
            ex = cx + (t - 0.5) * w
            ey = cy - rise * h
            a = int(alpha * (1.0 - rise * 0.65))
            if _NS_kaizen._hash01(seed * 11 + i * 3) > 0.5:
                pygame.draw.circle(surface, _NS_kaizen._rgba(color, a),
                                   (round(ex), round(ey)), 1)
            else:
                pygame.draw.line(surface, _NS_kaizen._rgba(color, a),
                                 (round(ex), round(ey)),
                                 (round(ex), round(ey - 3)), 1)

    # ------------------------------------------------------------------
    # Koordinat dunia -> ruang gambar
    # ------------------------------------------------------------------
    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_kaizen._world_to_local(boss, x, y, target.x, target.y)
        scale = getattr(boss, "_render_scale", None)
        dist = 150 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)

    def _fx_scale(boss):
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_px, surface=None):
        """Radius dunia (px) -> px canvas. E/R telegraph pakai ini."""
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        if surface is not None:
            margin = min(surface.get_width(), surface.get_height()) // 2 - 10
            r = min(r, margin)
        return int(max(4, r))

    def _skill_progress(boss, skill, timer):
        dur = float(_NS_kaizen.SKILL_VISUAL_DURATION.get(
            skill, max(1, timer or 1)))
        return max(0.0, min(1.0, 1.0 - float(timer) / max(1.0, dur)))
    def _draw_wind_arc(surface, cx, cy, radius, start_angle, end_angle,
                       color, width=2, segments=12):
        points = []
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            points.append((cx + math.cos(angle) * radius,
                           cy + math.sin(angle) * radius))
        for i in range(len(points) - 1):
            _NS_kaizen._aaline(surface, color, points[i], points[i + 1],
                               width)

    def _draw_wind_swirl(surface, cx, cy, size, phase, color=None, alpha=200):
        if color is None:
            color = _NS_kaizen.PALETTE["wind_bright"]
        col = (*color, alpha) if len(color) == 3 else color
        for i in range(2):
            angle_start = phase * 0.8 + i * math.pi
            angle_end = angle_start + math.pi * 1.2
            _NS_kaizen._draw_wind_arc(surface, cx, cy, size, angle_start,
                                      angle_end, col, width=1, segments=6)

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=2, rot=0.4,
                    core=None):
        """Bintang doodle: goresan gel-pen + tinta di bawahnya."""
        if alpha <= 0 or size <= 0:
            return
        # underline tinta (sketchy) di belakang sinar terang
        if alpha > 60:
            for k in range(spikes):
                ang = rot + k * math.pi * 2 / spikes
                ln = size * (1.0 if k % 2 == 0 else 0.58)
                _NS_kaizen._aaline(
                    surface, _NS_kaizen._rgba(_NS_kaizen.PALETTE["ink"], 90),
                    (cx, cy),
                    (cx + math.cos(ang) * ln, cy + math.sin(ang) * ln * .8), 1)
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes + \
                _NS_kaizen._jit(size * 3 + k * 7, 0.10)
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_kaizen._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_kaizen._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        if alpha > 60:
            for s in (-1, 1):
                _NS_kaizen._aaline(
                    surface, _NS_kaizen._rgba(_NS_kaizen.PALETTE["ink"],
                                              int(alpha * 0.4)),
                    (int(cx + px * s * size * .55 - ca * size * .5),
                     int(cy + py * s * size * .55 - sa * size * .5)),
                    (int(tipx), int(tipy)), width + 2)
        for s in (-1, 1):
            _NS_kaizen._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=5, thick=3, span=0.6, squash=.92):
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_kaizen._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_kaizen._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_kaizen._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_kaizen._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    def _dither_dots(surface, color, a, b, step=3, alpha=210):
        if alpha <= 0:
            return
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        if ln <= 0:
            return
        steps = max(2, int(ln / step))
        for i in range(0, steps, 2):
            t = i / steps
            x, y = a[0] + dx * t, a[1] + dy * t
            _NS_kaizen._rect(surface, (*color, alpha),
                             (int(x), int(y) + (i % 4 == 2), 1, 1))
            if i + 1 < steps:
                t2 = (i + 1) / steps
                x2, y2 = a[0] + dx * t2, a[1] + dy * t2
                _NS_kaizen._rect(surface, (*color, alpha),
                                 (int(x2) + 1, int(y2) + 1 - (i % 4 == 2), 1, 1))

    def _filled_crescent(surface, cx, cy, ang, r_outer, r_inner, span, color,
                         segments=8):
        """Sabit terisi (proyektil + smear) - poligon 2 busur doodle."""
        if r_outer <= 1:
            return
        perp = ang + math.pi / 2
        pts = []
        n = max(4, int(segments))
        for i in range(n + 1):
            a = perp - span + (2 * span) * i / n
            pts.append((cx + math.cos(a) * r_outer,
                        cy + math.sin(a) * r_outer))
        ri = max(1.0, r_inner)
        for i in range(n + 1):
            a = perp + span - (2 * span) * i / n
            pts.append((cx + math.cos(a) * ri,
                        cy + math.sin(a) * ri))
        _NS_kaizen._poly(surface, color, pts)

    def _energy_arc(surface, cx, cy, radius, start, sweep, color, alpha, width=2,
                    segments=10):
        if alpha <= 0 or radius <= 1:
            return
        _NS_kaizen._draw_wind_arc(surface, cx, cy, radius, start, start + sweep,
                                  (*color, alpha), width, segments)

    def _aoe_marks(surface, cx, cy, radius, color, alpha, phase=0.0,
                   squash=1.0, ticks=12, tick_len=None, corner=True,
                   inner=False):
        """Marker AOE ANGULAR - tick radial + bracket, doodle-outlined.

        Geometry identik dengan versi pixel-art (tick tepat di radius
        dunia sehingga tes world-space tetap hijau); gaya digambar dengan
        garis ber-outline tinta agar menguat di terrain terang.
        """
        if alpha <= 0 or radius < 4:
            return
        if tick_len is None:
            tick_len = max(6, int(radius * 0.10))
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase * 2.2))
        lo, hi = ((radius - tick_len, radius) if not inner
                  else (radius, radius + tick_len))
        for i in range(ticks):
            a = i * math.tau / ticks
            ca, sa = math.cos(a), math.sin(a)
            ox = cx + ca * hi
            oy = cy + sa * hi * squash
            ix = cx + ca * lo
            iy = cy + sa * lo * squash
            al = int(alpha * (0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase * 1.3 + i))))
            _skill_outlined_line(surface, (ix, iy), (ox, oy), 2, color,
                                 max(8, al))
        if corner:
            L = max(6, int(radius * 0.13))
            for a in (math.pi / 4, 3 * math.pi / 4,
                      5 * math.pi / 4, 7 * math.pi / 4):
                ca, sa = math.cos(a), math.sin(a)
                ta, tb = -sa, ca
                txa, tya = ca, sa
                px = cx + ca * radius
                py = cy + sa * radius * squash
                al = int(alpha * (0.7 + 0.3 * pulse))
                _skill_outlined_line(
                    surface, (px, py), (px + txa * L, py + tya * L * squash),
                    2, color, al)
                _skill_outlined_line(
                    surface, (px, py), (px + ta * L, py + tb * L * squash),
                    2, color, al)

    # -------------------------------------------------------------------
    # PROJECTILE - Steel Wind Slash (crescent 3-lapis + pita trail + burst)
    # -------------------------------------------------------------------
    class WindSlashProjectile:
        """Crescent wind slash - trail pita + burst kematian (doodle)."""

        def __init__(self, sx, sy, tx, ty, speed=8.0,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            self.angle = math.atan2(ty - sy, tx - sx)

        def update(self):
            if not self.alive:
                self.dead_frames += 1
                return
            self.age += 1
            if self.target is not None and getattr(self.target, "alive", False):
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_kaizen._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y), self.angle))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            p = _NS_kaizen.PALETTE
            # ── burst kematian (awan poof + bintang doodle) ──
            if not self.alive:
                t = max(0.0, 1.0 - self.dead_frames / 8.0)
                if t <= 0:
                    return
                px, py = int(self.x), int(self.y)
                _NS_kaizen._doodle_star(surface, px, py, int(18 * t + 4),
                                        p["wind_pale"], int(230 * t), 8,
                                        width=2, rot=phase * 2.4)
                _NS_kaizen._aacircle(surface, (*p["wind_light"], int(160 * t)),
                                     (px, py), int(10 + 16 * (1 - t)), 2)
                _NS_kaizen._poof(surface, px, py, int(16 * t + 4),
                                 p["wind_mid"], int(120 * t), seed=41,
                                 width=2, fill=p["wind_light"],
                                 fill_alpha=int(70 * t))
                return

            # ── pita trail 3-lapis (titik + sabit mini) ──
            n = len(self.trail)
            for i, item in enumerate(self.trail):
                tx, ty = item[0], item[1]
                ang = item[2] if len(item) > 2 else self.angle
                k = i / max(1, n - 1) if n > 1 else 1.0
                alpha = int(28 + 140 * k)
                r = max(1, int(3 + 7 * k))
                _NS_kaizen._aacircle(surface, (*p["wind_dark"], alpha // 2),
                                     (tx, ty), r + 3)
                _NS_kaizen._aacircle(surface, (*p["wind_mid"], alpha),
                                     (tx, ty), r)
                if i % 2 == 0:
                    _NS_kaizen._filled_crescent(
                        surface, tx, ty, ang, r + 4, r * 0.35, 0.85,
                        (*p["wind_light"], alpha), segments=5)

            px, py = int(self.x), int(self.y)
            _NS_kaizen._aacircle(surface, (*p["wind_dark"], 110), (px, py), 20)
            _NS_kaizen._aacircle(surface, (*p["wind_mid"], 160), (px, py), 13)

            # sabit terisi 3 band
            _NS_kaizen._filled_crescent(
                surface, px, py, self.angle, 20, 9, 1.15,
                (*p["wind_dark"], 160), segments=8)
            _NS_kaizen._filled_crescent(
                surface, px, py, self.angle, 17, 8, 1.10,
                (*p["wind_mid"], 200), segments=8)
            _NS_kaizen._filled_crescent(
                surface, px, py, self.angle, 14, 7, 1.05,
                (*p["wind_light"], 230), segments=7)
            _NS_kaizen._draw_wind_arc(
                surface, px, py, 16, self.angle + math.pi / 2 - 1.1,
                self.angle + math.pi / 2 + 1.1,
                p["wind_white"], width=2, segments=10)

            perp = self.angle + math.pi / 2
            for sgn, rot_k in ((-1.1, 2.1), (1.1, -1.7)):
                tipx = px + math.cos(perp + sgn) * 16
                tipy = py + math.sin(perp + sgn) * 16
                _NS_kaizen._aacircle(surface, p["wind_white"],
                                     (int(tipx), int(tipy)), 2)
                _NS_kaizen._spark_star(surface, tipx, tipy, 5, p["wind_pale"],
                                       200, 4, rot=phase * rot_k)

            for i in range(3):
                offset = (i - 1) * 5
                sx1 = px - math.cos(self.angle) * (8 + i * 2) + math.cos(perp) * offset
                sy1 = py - math.sin(self.angle) * (8 + i * 2) + math.sin(perp) * offset
                sx2 = sx1 - math.cos(self.angle) * 8
                sy2 = sy1 - math.sin(self.angle) * 8
                _NS_kaizen._aaline(surface, (*p["wind_bright"], 190),
                                   (sx1, sy1), (sx2, sy2), 1)

    # -------------------------------------------------------------------
    # ANIMATION
    # -------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_kz_last_x"):
            boss._kz_last_x = boss.x
            boss._kz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kz_last_x)
        dy = abs(boss.y - boss._kz_last_y)
        boss._kz_last_x = boss.x
        boss._kz_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving

    def _update_attack_anim(boss):
        """Track attack animation timeline (timer naik = swing baru)."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kz_prev_timer", -1))
        active = bool(getattr(boss, "_kz_attack_active", False))
        trigger = previous >= 0 and timer > previous
        if trigger:
            boss._kz_attack_active = True
            active = True
        if active and timer <= 0:
            boss._kz_attack_active = False
            active = False
        boss._kz_prev_timer = timer
        boss._kz_attack_frame = max(0, cooldown - timer) if active else 0
        boss._kz_attack_progress = (
            min(1.0, boss._kz_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )

    def _manage_projectiles(boss, surface, phase):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_kz_projectiles"):
            boss._kz_projectiles = []
        for proj in boss._kz_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._kz_projectiles = [
            p for p in boss._kz_projectiles if p.alive or p.dead_frames < 8]

    def _spawn_wind_slash(boss, x, y):
        # Lapisan FX hidup (heroes/kaizen_fx.py) memiliki proyektil unit
        # ini: jalur canvas TIDAK boleh menumpuk sabit yang tidak pernah
        # digambar/di-update (_manage_projectiles ikut dilewati).
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_kz_projectiles"):
            boss._kz_projectiles = []
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx = x + 24 * facing
        sy = y - 8
        tgt = getattr(boss, "target", None)
        proj = _NS_kaizen.WindSlashProjectile(
            sx, sy, tx, ty, speed=8.0,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._kz_projectiles.append(proj)

    def _katana_angle(phase, action, progress=0.0):
        if action == "attack":
            return _NS_kaizen._attack_pose(progress)["angle"]
        if action == "walk":
            return 0.46 + math.sin(phase * 1.7) * 0.06
        return 0.34 + math.sin(phase * 0.72) * 0.03

    def _attack_pose(ap):
        """Interpolasi keyframe serang iai -> dict pose.

        Hand sudah dalam ruang gambar (idle ~ (34,-2)).
        Sudut wind-up < 0 < sudut IMPACT (diaudit test).
        """
        keys = (
            #  p, bob, lean, hx,  hy,  angle, flare, tremble
            (0.00,  0,  1,  32, -26,  0.34, 1.00, 0),
            (0.12,  8, -8,  18, -62, -2.35, 1.12, 0),
            (0.28,  9, -9,  15, -65, -2.62, 1.22, 1),
            (0.46, -4, 11,  44, -14,  0.98, 1.10, 0),
            (0.54,  9, 12,  47,  -8,  0.72, 1.05, 0),
            (0.74,  2,  6,  42, -18,  0.48, 1.00, 0),
            (1.00,  0,  1,  32, -26,  0.34, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)
                vals = tuple(a + (b - a) * t for a, b in zip(k0[1:6], k1[1:6]))
                flare = k0[6] + (k1[6] - k0[6]) * t
                tremble = 1 if (k0[7] and t < 0.9) else 0
                return {
                    "bob": int(round(vals[0])), "lean": int(round(vals[1])),
                    "hand": (int(round(vals[2])), int(round(vals[3]))),
                    "angle": vals[4],
                    "flare": flare, "tremble": tremble,
                }
        return {"bob": 0, "lean": 1, "hand": (32, -26), "angle": 0.34,
                "flare": 1.0, "tremble": 0}

    def _katana_tip_local(phase, action, progress=0.0):
        """Ujung katana dalam ruang lokal (hadap kanan)."""
        L = _NS_kaizen.BLADE_LEN
        if action == "attack":
            pose = _NS_kaizen._attack_pose(progress)
            hx, hy = pose["hand"]
            A = pose["angle"]
            return (hx + math.cos(A) * L, hy + math.sin(A) * L)
        if action == "walk":
            stride = math.sin(phase * 1.7)
            hx, hy = 36, -6 + int(stride * 3)
            A = 0.46 + math.sin(phase * 1.7) * 0.06
            return (hx + math.cos(A) * L, hy + math.sin(A) * L)
        hx, hy = 34, -2 + int(math.sin(phase * .72) * 1.2)
        A = 0.34 + math.sin(phase * .72) * .03
        return (hx + math.cos(A) * L, hy + math.sin(A) * L)

    def _draw_katana_swing_trail(surface, cx, cy, f, phase, ap):
        """Smear iai doodle: jejak ujung bilah di progress sebelumnya.

        Kepala smear SELALU menempel di ujung katana sekarang.
        Aktif di jendela strike; wind-up tetap bersih.
        """
        p = _NS_kaizen.PALETTE
        if ap < 0.30 or ap > 0.88:
            return
        steps = 10
        span = min(0.22, max(0.04, ap - _NS_kaizen.ATTACK_WINDUP_END))
        fade = 1.0
        if ap > _NS_kaizen.ATTACK_SWING_END:
            fade = max(0.0, 1.0 - (ap - _NS_kaizen.ATTACK_SWING_END) / 0.16)
        if fade <= 0.01:
            return
        impact = max(0.0, 1.0 - abs(ap - _NS_kaizen.ATTACK_IMPACT) / 0.16)
        # goresan tinta tipis di bawah pita (garis kecepatan doodle)
        for i in range(steps):
            s = (i + 1) / steps
            p_back = ap - span * (1.0 - s)
            tipx, tipy = _NS_kaizen._katana_tip_local(phase, "attack", p_back)
            ax = int(cx + tipx * f)
            ay = int(cy + tipy)
            taper = 0.28 + 0.72 * s
            alpha = int((50 + 200 * (s ** 1.5)) * fade)
            if alpha <= 0:
                continue
            base = 12 + int(6 * impact)
            _NS_kaizen._aacircle(surface, (*p["wind_dark"], alpha // 2),
                                 (ax, ay), max(1, int(base * taper)))
            _NS_kaizen._aacircle(surface, (*p["wind_mid"], alpha),
                                 (ax, ay), max(1, int(base * taper * 0.62)))
            _NS_kaizen._aacircle(surface, (*p["wind_light"], alpha),
                                 (ax, ay), max(1, int(base * taper * 0.36)))
            _NS_kaizen._aacircle(surface, (*p["wind_white"], alpha),
                                 (ax, ay), max(1, int(base * taper * 0.18)))
        tipx, tipy = _NS_kaizen._katana_tip_local(phase, "attack", ap)
        hx, hy = int(cx + tipx * f), int(cy + tipy)
        for radius, col, al in ((16, "wind_dark", 120),
                                (11, "wind_mid", 180),
                                (7, "wind_light", 220),
                                (4, "wind_white", 255)):
            _NS_kaizen._aacircle(surface, (*p[col], int(al * fade)),
                                 (hx, hy), max(1, radius))
        _NS_kaizen._doodle_star(surface, hx, hy, int(6 + 6 * fade),
                                p["wind_white"], int(220 * fade),
                                seed=int(ap * 100), spikes=5, width=2)
        if impact > 0.15:
            _NS_kaizen._spark_star(surface, hx, hy, int(10 + 14 * impact),
                                   p["wind_pale"], int(240 * impact * fade),
                                   6, rot=0.4, core=p["white"])
    # -------------------------------------------------------------------
    # ENTRY PUNCT + DRAW DISPATCH (kontrak hero pipeline)
    # -------------------------------------------------------------------
    def draw_kaizen(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaizen._detect_moving(boss)
        _NS_kaizen._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        # ═══ LAPISAN FX HIDUP (heroes/kaizen_fx.py) ═══
        if not portrait_hd:
            try:
                mod = _NS_kaizen._live_module()
                if mod is not None:
                    mod.attach(boss)
            except Exception:
                pass
        _NS_kaizen._FX_LIVE.v = (not portrait_hd) and \
            _NS_kaizen._fx_live_owned(boss)

        attacking = (
            getattr(boss, "_kz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )
        storm = active_skill == "r"

        if not portrait_hd:
            _NS_kaizen._draw_swordsman_rim_light(surface, x, y - 12, pulse)
            if storm:
                _NS_kaizen._draw_storm_aura(surface, x, y, pulse)
            else:
                _NS_kaizen._draw_wind_aura(surface, x, y, pulse)
            _NS_kaizen._draw_wind_platform(
                surface, x, y + 58, pulse, active_skill)

        if active_skill == "q":
            _NS_kaizen._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizen._draw_sweep_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizen._draw_tornado_ground(surface, boss, x, y, skill_timer, pulse)

        if attacking:
            _NS_kaizen._draw_kaizen_attack(surface, boss, x, y)
        elif moving:
            _NS_kaizen._draw_kaizen_walk(surface, boss, x, y)
        else:
            _NS_kaizen._draw_kaizen_idle(surface, boss, x, y)

        if not portrait_hd:
            _NS_kaizen._manage_projectiles(boss, surface, pulse)

        if active_skill == "q":
            _NS_kaizen._draw_dash_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaizen._draw_wind_wall(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizen._draw_sweep_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizen._draw_tornado(surface, boss, x, y, skill_timer, pulse)

    def draw_boss(surface, boss, x, y):
        _NS_kaizen.draw_kaizen(surface, boss, x, y)

    def _draw_kaizen_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2.5)
        gale = getattr(boss, "active_skill", None) == "w"
        storm = getattr(boss, "active_skill", None) == "r"
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x, y + 62)
            _NS_kaizen._draw_floating_wind(surface, x, y + 46, boss.pulse,
                                           gale=gale)
        _NS_kaizen._draw_kaizen_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle",
            detail=getattr(boss, "_portrait_hd", False),
            gale=gale, storm=storm)

    def _draw_kaizen_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        gale = getattr(boss, "active_skill", None) == "w"
        storm = getattr(boss, "active_skill", None) == "r"
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x + sway, y + 62)
            _NS_kaizen._draw_floating_wind(
                surface, x + sway, y + 46, phase, trail=True,
                facing=boss.direction, gale=gale)
        _NS_kaizen._draw_kaizen_body(
            surface, x + sway, y - bob, boss.direction, phase, "walk",
            detail=getattr(boss, "_portrait_hd", False),
            gale=gale, storm=storm)

    def _draw_kaizen_attack(surface, boss, x, y):
        progress = getattr(boss, "_kz_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        gale = getattr(boss, "active_skill", None) == "w"
        storm = getattr(boss, "active_skill", None) == "r"

        range_val = getattr(boss, "range", 150)
        is_ranged = range_val > 80

        if is_ranged:
            if 0.45 < progress < 0.55 and not getattr(boss, "_kz_proj_spawned", False):
                _NS_kaizen._spawn_wind_slash(boss, x, y)
                boss._kz_proj_spawned = True
            if progress < 0.15 or progress > 0.9:
                boss._kz_proj_spawned = False
            if 0.45 < progress < 0.62:
                fs = _NS_kaizen._fx_scale(boss)
                mx = x + 52 * boss.direction
                my = y - 6
                fade = 1.0 - abs(progress - 0.52) / 0.12
                _NS_kaizen._spark_star(surface, mx, my, int(16 * fs),
                                       _NS_kaizen.PALETTE["wind_pale"],
                                       int(235 * fade), 6, rot=progress * 6,
                                       core=_NS_kaizen.PALETTE["white"])
                _NS_kaizen._aacircle(
                    surface, (*_NS_kaizen.PALETTE["wind_bright"], int(170 * fade)),
                    (mx, my), int(20 * fs), 2)

        step = int(math.sin(progress * math.pi) * 4) * boss.direction
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x + step, y + 62)
            _NS_kaizen._draw_floating_wind(
                surface, x + step, y + 46, boss.pulse, intense=True,
                gale=gale)
        _NS_kaizen._draw_kaizen_body(
            surface, x + step, y, boss.direction, boss.pulse,
            "attack", progress, getattr(boss, "_portrait_hd", False),
            gale=gale, storm=storm)

    def _draw_kaizen_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, detail=False, gale=False,
                          storm=False):
        _NS_kaizen._draw_kaizen_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail,
            gale, storm)

    # -------------------------------------------------------------------
    # RIG DOODLE - satu rig berlapis, semua digambar "tangan"
    # -------------------------------------------------------------------
    def _draw_kaizen_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False, gale=False,
                           storm=False):
        """Rig doodle sketchbook - wind blades samurai, 100% prosedural.

        Disiplin doodle:
          * outline tinta bergoyang (boiling lines) - jitter murni pose;
          * isi spidol dengan celah kertas ke centroid;
          * bayangan = arsiran pensil + skribel loop, bukan ramp;
          * highlight = goresan gel-pen putih;
          * angin = lidah teardrop ber-tinta + skribel sian + bintang doodle;
          * semua jitter deterministik (hash) -> aman untuk sprite cache.
        """
        p = _NS_kaizen.PALETTE
        INK = p["ink"]
        inkk = p["ink_soft"]
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        pose = _NS_kaizen._attack_pose(ap) if attack else None
        stride = math.sin(phase * 1.7) if walk else 0.0
        breath = math.sin(phase * 0.78)

        # Loop closure: pose ap=0.0 dan ap=1.0 identik, dan seed untuk
        # satu action tetap (hanya ganti fase), jadi frame serang terakhir
        # = frame serang pertama piksel-demi-piksel (10-progress -> 9 unik).
        seed = _NS_kaizen._seed_q(phase, {"idle": 1, "walk": 2,
                                          "attack": 3}.get(action, 1))

        # ═══ 1. GERAK BADAN: root / lean / sway ═══
        root_y = 0
        lean = 0
        tremble = 0
        sway = int(math.sin(phase * 0.5) * 2.0)
        bob_cloth = 0
        if walk:
            root_y = int(math.sin(phase * 2.0) * 2.5) - 2
            sway = int(math.sin(phase) * 3.0)
            lean = (4 + int(abs(stride) * 2)) * f
        elif attack:
            root_y = pose["bob"]
            sway = 0
            lean = pose["lean"] * f
            if pose["tremble"]:
                tremble = 1 if int(phase * 30) % 2 else -1
        else:
            root_y = int(breath * 2.2)
            sway = int(math.sin(phase * 0.5) * 2.0)
            lean = int(math.sin(phase * 0.5 + 1.2) * 1.5)
        off_x = lean + sway + tremble

        def ptf(dx, dy):
            return (cx + dx * f + off_x, cy + dy + root_y)

        def blob(fill, coords, salt=0, ink=None, width=2, gap=1.5,
                 alpha=255, close=True, passes=2):
            pts = [ptf(dx, dy) for dx, dy in coords]
            _NS_kaizen._marker_poly(surface, fill, pts, seed + salt,
                                    INK if ink is None else ink, width,
                                    gap, alpha, alpha, close, passes)

        def tube(a, b, width, fill, salt=0, shade=None, alpha=255):
            _NS_kaizen._tube(surface, ptf(*a), ptf(*b), width, fill, INK,
                             seed + salt, alpha, shade)

        def stroke(a, b, color, width=2, salt=0, alpha=255, passes=1):
            _NS_kaizen._ink_stroke(surface, color, ptf(*a), ptf(*b),
                                   width, seed + salt, alpha, passes)

        def dot(fill, dx, dy, r, salt=0, alpha=255):
            sc = ptf(dx, dy)
            if r <= 2.6:
                _NS_kaizen._aacircle(surface,
                                     _NS_kaizen._rgba(fill, alpha),
                                     (int(sc[0]), int(sc[1])), max(1, int(r)))
                return
            _NS_kaizen._ink_ellipse(surface, fill, sc[0], sc[1], r,
                                    r * 0.92, seed + salt, None, 0,
                                    alpha=alpha, fill_alpha=alpha,
                                    n=9, gap=0.0, passes=0)

        def scrib(color, dx, dy, rx, ry, salt=0, alpha=140, loops=3,
                  angle=0.0, width=2):
            sc = ptf(dx, dy)
            _NS_kaizen._scribble(surface, color, sc[0], sc[1], rx, ry,
                                 seed + salt, alpha, loops, angle, width)

        def hatch(color, dx, dy, w, h, salt=0, alpha=110, angle=-0.7,
                  gap=4.0, width=1):
            sc = ptf(dx, dy)
            _NS_kaizen._hatch_patch(surface, color, sc[0], sc[1], w, h,
                                    seed + salt, alpha, gap, angle, width)

        def fdot(color, dx, dy, r, alpha=210, salt=0, width=2):
            sc = ptf(dx, dy)
            _NS_kaizen._doodle_star(surface, sc[0], sc[1], r, color, alpha,
                                    seed + salt, 5, width)

        # ═══ 2. RAMBUT & SAYA BELAKANG + pita scarf ═══
        hair_wave = int(math.sin(phase * 1.25 - .7) * 3)
        # gumpal rambut kompak di belakang tengkorak
        blob(p["hair_darkest"],
             [(-3, -80 + hair_wave), (-12, -86 + hair_wave),
              (-22, -86 + hair_wave), (-28, -79 + hair_wave),
              (-29, -68 + hair_wave), (-24, -60 + hair_wave),
              (-16, -58 + hair_wave), (-8, -66 + hair_wave),
              (-4, -74 + hair_wave)], 11)
        blob(p["hair_dark"],
             [(-8, -78 + hair_wave), (-16, -84 + hair_wave),
              (-24, -82 + hair_wave), (-26, -74 + hair_wave),
              (-22, -66 + hair_wave), (-14, -64 + hair_wave)],
             12, ink=None, gap=0.0, alpha=235, passes=0)
        scrib(p["hair_shine"], -19, -76 + hair_wave, 10, 5, 13, 90, 2, 0.6, 2)
        # dua lock ponytail terjumbai
        for salt, tail in ((14, [(-17, -60), (-30, -50), (-35, -34),
                                 (-27, -46), (-13, -54)]),
                           (15, [(-13, -66), (-26, -52), (-27, -30),
                                 (-21, -44), (-9, -58)])):
            blob(p["hair_darkest"], tail, salt)
            stroke((tail[1][0], tail[1][1]), (tail[2][0], tail[2][1]),
                   p["hair_shine"], 1, salt + 9, 130, 1)

        # pita scarf tipis mengalir di belakang bahu
        scarf_wave = int(math.sin(phase * 1.45 - .9) * 5)
        blob(p["scarf_deep"],
             [(-8, -52), (-16, -46), (-25, -38 + scarf_wave),
              (-30, -22 + scarf_wave), (-24, -10 + scarf_wave),
              (-16, -22), (-9, -34)], 21, gap=1.2)
        stroke((-16, -46), (-29, -24 + scarf_wave), p["scarf_high"], 1,
               22, 170, 1)

        # saya (sarung lacquer pendek) - doodle
        tube((-9, 8), (-40, 28), 8, p["saya_mid"], 31, p["saya_dark"])
        stroke((-11, 6), (-40, 25), p["saya_light"], 1, 32, 200, 1)
        stroke((-12, 5), (-39, 24), p["saya_shine"], 1, 33, 150, 1)
        dot(p["gold_dark"], -41, 28, 3, 34)
        dot(p["gold_mid"], -42, 27, 2, 35)

        # plat bahu belakang (di belakang semuanya, kiri-atas)
        blob(p["steel_dark"], [(-22, -42), (-15, -51), (-5, -51),
                               (0, -44), (-6, -37), (-17, -36)], 41)
        blob(p["steel_mid"], [(-18, -42), (-13, -48), (-5, -48),
                              (-2, -42), (-7, -38), (-15, -37)], 42,
             ink=None, gap=0.0, alpha=235, passes=0)
        stroke((-17, -44), (-8, -48), p["steel_light"], 1, 43, 180, 1)
        dot(p["steel_shine"], -11, -45, 1, 44, 220)

        # ═══ 3. TORSO - jaket tertutup, kerah V, obi, strap ═══
        blob(p["cloth_deep"], [(-20, -46), (-8, -54), (14, -51),
                               (20, -36), (18, -12), (8, 4),
                               (-16, 4), (-22, -18)], 51)
        blob(p["cloth_dark"], [(-17, -42), (-7, -49), (12, -47),
                               (17, -34), (15, -14), (7, 4),
                               (-14, 3), (-18, -18)], 52,
             ink=None, gap=0.0, alpha=235, passes=0)
        blob(p["cloth_mid"], [(-15, -40), (-7, -45), (2, -45),
                              (3, -18), (-5, 1), (-13, 0),
                              (-15, -18)], 53, ink=None, gap=0.0,
             alpha=235, passes=0)
        # piping cahaya di sisi terang (gel-pen)
        stroke((-14, -24), (-12, 2), p["cloth_high"], 1, 54, 190, 1)
        stroke((13, -44), (19, -36), p["cloth_high"], 1, 55, 170, 1)
        # kerah V kecil di leher
        blob(p["skin_mid"], [(0, -46), (8, -48), (6, -42),
                             (1, -41), (-2, -43)], 56, ink=None,
             gap=0.0, alpha=235, passes=0)
        stroke((1, -44), (8, -46), p["ink_soft"], 1, 57, 150, 1)
        # strap diagonal dada
        stroke((-3, -40), (16, -10), p["leather_dark"], 2, 58, 220, 1)
        stroke((-2, -39), (15, -11), p["leather_mid"], 1, 59, 180, 1)
        # obi
        blob(p["saya_dark"], [(-15, 4), (23, 6), (25, 15), (-13, 15)], 61)
        blob(p["wrap_dark"], [(-14, 6), (23, 8), (23, 13), (-14, 12)],
             62, ink=None, gap=0.0, alpha=235, passes=0)
        stroke((-8, 8), (17, 10), p["wrap_light"], 1, 63, 190, 1)
        # plat bahu depan sisi pedang (kecil)
        blob(p["cloth_darkest"], [(12, -45), (20, -40), (18, -28),
                                  (11, -30), (8, -38)], 64)
        stroke((13, -42), (19, -37), p["cloth_high"], 1, 65, 180, 1)

        # ═══ 4. KEPALA + LEHER + KERAH + WAJAH ═══
        blob(p["skin_dark"], [(1, -58), (10, -58), (12, -50),
                              (6, -47), (-1, -50)], 71)
        # kerah scarf menutup leher
        blob(p["scarf_deep"], [(-8, -52), (11, -52), (14, -45),
                               (0, -39), (-11, -43), (-12, -48)], 72)
        blob(p["scarf_dark"], [(-6, -50), (9, -50), (11, -45),
                               (-1, -41), (-9, -43), (-10, -46)], 73,
             ink=None, gap=0.0, alpha=235, passes=0)
        stroke((-5, -50), (8, -50), p["scarf_light"], 1, 74, 190, 1)
        stroke((-4, -51), (7, -51), p["scarf_high"], 1, 75, 210, 1)

        # wajah ¾ depan, kompak, dua mata jelas
        face = [(-9, -84), (-2, -87), (8, -86), (14, -82),
                (16, -74), (15, -66), (11, -59), (4, -56),
                (-4, -57), (-9, -63), (-11, -74)]
        blob(p["skin_mid"], face, 81)
        blob(p["skin_dark"],
             [(9, -56), (14, -61), (16, -68), (14, -74), (11, -71),
              (10, -63)], 82, ink=None, gap=0.0, alpha=235, passes=0)
        stroke((-7, -82), (9, -80), p["skin_light"], 2, 83, 175, 1)
        hatch(p["skin_dark"], 12, -63, 5, 9, 84, 90, 0.6, 3)
        # garis hidung / rahang
        stroke((15, -71), (16, -63), p["ink_soft"], 1, 85, 150, 1)
        stroke((16, -62), (10, -60), p["ink"], 1, 86, 180, 1)

        # mata: dua sapuan tinta + iris + specular
        def eye(ax):
            exs, eys = ptf(ax, -67)
            _NS_kaizen._aacircle(surface, p["eye_white"],
                                 (int(exs), int(eys)), 3)
            _NS_kaizen._aacircle(surface, p["white"],
                                 (int(exs), int(eys) - 1), 1)
            _NS_kaizen._aacircle(surface, p["eye_iris"],
                                 (int(exs) - 1, int(eys)), 2)
            _NS_kaizen._aacircle(surface, p["eye_pupil"],
                                 (int(exs) - 1, int(eys)), 1)
            # specular iris: piksel eksak di tepi bawah mata (di bawah
            # hachimaki sehingga pasti terbaca) supaya swatch iris_light
            # selalu hadir di render idle.
            surface.set_at((int(exs), int(eys) + 2),
                           (*p["eye_iris_light"], 255))
            _NS_kaizen._aacircle(surface, p["eye_iris_light"],
                                 (int(exs) - 2, int(eys) - 1), 1)
            # goresan tinta alis di atas mata
            stroke((ax - 1, -73), (ax + 3 + (3 if ax > 0 else -3), -74),
                   INK, 1, 91 + ax, 190, 1)
        eye(-2)
        eye(9)
        # hachimaki di dahi; mata tetap terlihat di bawah
        blob(p["scarf_deep"], [(-11, -78), (16, -76), (17, -71),
                               (4, -68), (-12, -70)], 95)
        blob(p["scarf_dark"], [(-9, -76), (14, -74), (15, -71),
                               (4, -70), (-10, -71)], 96,
             ink=None, gap=0.0, alpha=235, passes=0)
        stroke((-8, -75), (13, -73), p["scarf_light"], 1, 97, 190, 1)
        bead = ptf(4, -74)
        _NS_kaizen._aacircle(surface, p["gold_dark"],
                             (int(bead[0]), int(bead[1])), 3)
        _NS_kaizen._aacircle(surface, p["gold_mid"],
                             (int(bead[0]), int(bead[1])), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"],
                             (int(bead[0]) - 1, int(bead[1]) - 1), 1)
        # pita hachimaki berkibar
        band_wave = int(math.sin(phase * 1.6 - 1.1) * 3)
        for k, (drop, ln) in enumerate(((-2, 16), (3, 12))):
            wv = band_wave + k * 3
            blob(p["scarf_dark"],
                 [(-11, -77 + k * 2), (-17, -76 + wv // 2),
                  (-28, -70 + drop + wv), (-32, -67 + drop + wv),
                  (-25, -64 + drop + wv), (-17, -70)], 98 + k, gap=1.2)
            stroke((-17, -74 + wv // 2), (-30, -67 + drop + wv),
                   p["scarf_mid"], 1, 100 + k, 170, 1)

        # topknot kecil & bersih
        blob(p["hair_darkest"], [(-1, -87), (2, -91), (6, -88),
                                 (4, -84), (0, -85)], 103)
        dot(p["hair_shine"], 1, -89, 1, 104, 200)

        # ═══ 5. KAKI + HAKAMA (foot solver) ═══
        leg_phase = stride if walk else 0.0
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 11) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 11) if walk else 0
        rear_foot = (-13 - int(leg_phase * 6),
                     60 - int(abs(leg_phase) * 3) - rear_lift)
        front_foot = (15 + int(leg_phase * 6), 60 - front_lift)
        # hem hakama belakang bergerigi
        back_hem = [(-27, 12), (-8, 14), (0, 33), (-16, 40), (-30, 28)]
        hem_b = _NS_kaizen._tuft_points(back_hem, 2.4, 4.5, seed=21)
        blob(p["pants_dark"], hem_b, 111, gap=1.2)
        # hem hakama depan bergerigi
        front_hem = [(-2, 16), (23, 12), (32, 25), (25, 39), (4, 42),
                     (-2, 34)]
        hem_f = _NS_kaizen._tuft_points(front_hem, 2.4, 4.5, seed=33)
        blob(p["pants_mid"], hem_f, 112)
        blob(p["pants_light"], [(2, 18), (20, 15), (27, 27), (20, 36),
                                (6, 36)], 113, ink=None, gap=0.0,
             alpha=235, passes=0)
        # lipatan hakama (garis tinta)
        for dx in (-14, 2, 8, 17):
            stroke((dx, 14), (dx + (2 if dx > 0 else -2), 32),
                   p["ink_soft"], 1, 114 + dx, 120, 1)
        hatch(p["pants_light"], 12, 25, 14, 10, 116, 100, -0.7, 4)

        for hip, knee, foot, shade, lift, salt in (
                ((-11, 20), (-11, 36), rear_foot, p["pants_dark"],
                 rear_lift, 121),
                ((11, 20), (11, 35), front_foot, p["pants_mid"],
                 front_lift, 131)):
            knee = (knee[0], knee[1] - lift)
            # tabung kaki
            tube(hip, (knee[0], knee[1]), 10, shade, salt, p["pants_dark"])
            tube((knee[0], knee[1]), (foot[0], foot[1] - 6), 8,
                 p["pants_mid"], salt + 1)
            # tabi sock (kyahan) - terang + warna swatch (204,211,216)
            sock_fill = (204, 211, 216) if foot is front_foot else (176, 184, 196)
            sock0 = (foot[0], foot[1] - 14)
            sock1 = (foot[0] + 1, foot[1] - 6)
            blob(sock_fill, [(foot[0] - 5, foot[1] - 14),
                             (foot[0] + 5, foot[1] - 14),
                             (foot[0] + 6, foot[1] - 5),
                             (foot[0] - 6, foot[1] - 5)], salt + 2)
            stroke((foot[0] - 4, foot[1] - 10), (foot[0] + 5, foot[1] - 10),
                   p["white"], 1, salt + 3, 200, 1)
            # sandal (geta) datar
            blob(p["leather_dark"], [(foot[0] - 7, foot[1] - 5),
                 (foot[0] + 9, foot[1] - 5), (foot[0] + 11, foot[1]),
                 (foot[0] - 7, foot[1])], salt + 4)
            stroke((foot[0] - 5, foot[1] - 3), (foot[0] + 7, foot[1] - 3),
                   p["leather_mid"], 1, salt + 5, 180, 1)
            # garis telapak yang menapak (uji telapak +60)
            stroke((foot[0] - 5, foot[1]), (foot[0] + 9, foot[1]),
                   INK, 2, salt + 6, 235, 1)

        # ═══ 6. LENGAN DEPAN + KATANA ═══
        if attack and pose is not None:
            hand = pose["hand"]
            k_angle = pose["angle"]
            flare = pose["flare"]
        else:
            flare = 1.0
            if walk:
                hand = (34, -6 + int(stride * 3))
                k_angle = 0.42 + math.sin(phase * 1.7) * 0.06
            else:
                hand = (33, -2 + int(math.sin(phase * .72) * 1.1))
                k_angle = 0.34 + math.sin(phase * .72) * .03
        tube((14, -40), (24, -22), 9, p["cloth_dark"], 141, p["cloth_darkest"])
        tube((24, -22), hand, 7, p["skin_dark"], 142, p["skin_darkest"])
        mx_, my_ = (24 + hand[0]) // 2, (-22 + hand[1]) // 2
        stroke((mx_ - 1, my_ - 1), (hand[0] - 3, hand[1] - 2),
               p["wrap_dark"], 5, 143, 220, 1)
        for t in (.35, .7):
            wx_ = int(24 + (hand[0] - 24) * t)
            wy_ = int(-22 + (hand[1] + 22) * t)
            stroke((wx_ - 2, wy_), (wx_ + 2, wy_ - 2), p["wrap_light"],
                   1, 144 + int(t * 10), 180, 1)
        # kepalan tangan menutup tsuka
        dot(p["skin_mid"], hand[0], hand[1], 5, 150)
        stroke((hand[0] - 2, hand[1] - 3), (hand[0] + 2, hand[1] - 2),
               p["skin_high"], 2, 151, 200, 1)

        glow = 0.0
        smear = 0.0
        if attack:
            glow = max(glow, .55 + .45 * math.sin(ap * math.pi))
            smear = max(0.0, 1.0 - abs(ap - .5) / .22)
        if gale:
            glow = max(glow, .5)
        if storm:
            glow = max(glow, .65)
        _NS_kaizen._draw_elite_katana(
            surface, cx + off_x, cy + root_y, facing, hand,
            k_angle, phase, attacking=attack, glow=glow, flare=flare,
            smear=smear, progress=attack_progress)

        # ═══ 7. GERAK / REAKSI BADAN / RIM ═══
        if walk:
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx_, fy_ = ptf(planted[0], planted[1])
                alpha = int(140 * contact)
                for i in range(3):
                    _NS_kaizen._aacircle(
                        surface, _NS_kaizen._rgba(p["wind_mid"],
                                                  max(15, alpha - i * 30)),
                        (int(fx_ - f * (4 + i * 4)), int(fy_ - i % 2)),
                        max(1, 3 - i // 2))
            for i in range(2):
                sy_ = cy - 8 + i * 16 + root_y
                _NS_kaizen._aaline(surface,
                                   (*p["wind_light"], 80 - i * 22),
                                   (cx - f * (40 + i * 8), sy_),
                                   (cx - f * (20 + i * 6), sy_ - 1), 1)
        elif attack:
            impact = max(0.0, 1.0 - abs(ap - .54) / .16)
            if impact > 0.08:
                tip = _NS_kaizen._katana_tip_local(phase, "attack", ap)
                ix, iy = ptf(tip[0], tip[1])
                _NS_kaizen._spark_star(surface, ix, iy,
                                       int(10 + 16 * impact), p["wind_pale"],
                                       int(230 * impact), 6, rot=.4,
                                       core=p["white"])
                _NS_kaizen._poof(surface, ix, iy, int(10 + 12 * impact),
                                 p["wind_mid"], int(120 * impact), seed=161,
                                 width=2, fill=p["wind_light"],
                                 fill_alpha=int(60 * impact))
        else:
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx2 = cx + int(math.sin(phase + i * 2.1) * (26 + i * 5))
                my2 = cy + 38 - int(t * 84)
                _NS_kaizen._aacircle(
                    surface, (*p["wind_bright"], int(100 * (1 - t))),
                    (mx2, my2), 1)

        if gale and not attack:
            pulse_ = .6 + .4 * math.sin(phase * 2.2)
            _NS_kaizen._draw_wind_arc(surface, cx, cy - 6, 42,
                                      phase * .9, phase * .9 + 3.2,
                                      (*p["wind_bright"], int(55 * pulse_)),
                                      2, 10)
        if storm:
            gl = int(110 + 70 * math.sin(phase * 3.4))
            _NS_kaizen._aaline(surface, (*p["eye_glow"], min(255, gl)),
                               ptf(7, -70), ptf(12, -70), 2)
            _NS_kaizen._aaline(surface, (*p["wind_light"], int(gl // 2)),
                               ptf(-14, -12), ptf(-13, 4), 1)
            _NS_kaizen._spark_star(surface, *bead, 5, p["wind_pale"],
                                   int(110 + 60 * math.sin(phase * 4)), 4,
                                   rot=phase, core=p["white"])

        # rim light: hanya beberapa goresan gel-pen di tepi terang
        pulse2 = 0.72 + 0.28 * math.sin(phase * 1.8)
        rim_a = int(130 * pulse2)
        rim_col = (*p["wind_light"], rim_a)
        rim_hot = (*p["wind_white"], int(180 * pulse2))
        _NS_kaizen._aaline(surface, rim_col, ptf(12, -80), ptf(15, -70), 1)
        _NS_kaizen._aaline(surface, rim_hot, ptf(13, -79), ptf(14, -73), 1)
        _NS_kaizen._aaline(surface, rim_col, ptf(15, -38), ptf(20, -20), 1)
        _NS_kaizen._aaline(surface, rim_col, ptf(15, 35 - front_lift),
                           ptf(16, 54 - front_lift), 1)
        _NS_kaizen._aacircle(surface, rim_hot, ptf(16, 57 - front_lift), 1)

        # ═══ 8. PORTRAIT LOD (micro-detail, keluar dari cache gameplay) ═══
        if detail:
            for i in range(3):
                _NS_kaizen._ink_stroke(
                    surface, p["hair_shine"],
                    ptf(-10 - i * 3, -82 + i * 2),
                    ptf(-20 - i * 3, -84 + i * 4), 1, seed + 200 + i, 140)
            dot(p["skin_high"], 1, -61, 1, 210, 200)
            dot(p["skin_light"], 5, -57, 1, 211, 200)
            dot(p["wind_bright"], 14, -66, 1, 212, 220)
            stroke((-13, -28), (-12, -4), p["cloth_light"], 1, 213, 180, 1)
            _NS_kaizen._aacircle(surface, p["white"], bead, 1)
            for a in (-.8, -.3, .2):
                _NS_kaizen._ink_stroke(
                    surface, p["steel_mid"], ptf(-14, -48),
                    ptf(-14 + math.cos(a) * 6, -48 + math.sin(a) * 6),
                    1, seed + 220 + int(a * 10), 150)
            stroke((-17, 7), (-29, 19), p["saya_shine"], 1, 230, 170, 1)
            hatch(p["hair_shine"], -20, -78 + hair_wave, 12, 8, 231, 90,
                  0.4, 3)
    def _draw_elite_katana(surface, cx, cy, facing, hand, angle, phase,
                           attacking=False, glow=0.0, flare=1.0, smear=0.0,
                           progress=0.0):
        """Katana doodle: sori, hamon bergoyang, kissaki, tsuba 4-lobe, ito.

        Geometri bilah identik dengan versi pixel-art (tip mengunci
        ``_katana_tip_local``), hanya cara menggambar yang diubah ke
        bahasa sketsa: isi spidol baja + outline tinta + gel-pen shine +
        hamon garis bergoyang + glint berjalan.  Kalau lapisan FX hidup
        memiliki unit ini, jejak ujung-bilah di layar 60fps digambar
        OLEHNYA; canvas hanya menyisakan sabit pose (anchor di tangan).
        """
        p = _NS_kaizen.PALETTE
        INK = p["ink"]
        f = 1 if facing >= 0 else -1
        hx, hy = cx + hand[0] * f, cy + hand[1]
        length = _NS_kaizen.BLADE_LEN
        A = angle if f > 0 else math.pi - angle
        ux, uy = math.cos(A), math.sin(A)
        tx, ty = hx + ux * length, hy + uy * length
        px, py = -uy, ux
        seed = _NS_kaizen._seed_q(phase, 71)

        # smear DULU (di bawah bilah).  Lapisan hidup menggambar sabit
        # 60fps kalau owns() -> canvas tidak dobel.
        if attacking and smear > 0.05:
            if not _NS_kaizen._FX_LIVE.v:
                _NS_kaizen._draw_katana_swing_trail(
                    surface, cx, cy, f, phase, progress)
            start = A - 1.15 * max(0.6, flare)
            for radius, color, width, al in (
                    (64, p["wind_dark"], 5, 80),
                    (61, p["wind_light"], 3, 160),
                    (58, p["wind_white"], 1, 230)):
                _NS_kaizen._draw_wind_arc(surface, hx, hy, radius,
                                          start, A + .22,
                                          (*color, int(al * smear)),
                                          width, 14)

        # tsuka (gagang) + kashira
        ex, ey = hx - ux * 16, hy - uy * 16
        _NS_kaizen._aaline(surface, p["shadow_deep"], (hx, hy), (ex, ey), 9)
        _NS_kaizen._aaline(surface, p["wrap_mid"], (hx, hy), (ex, ey), 6)
        for t in (.22, .5, .78):
            wx, wy = hx - ux * 16 * t, hy - uy * 16 * t
            _NS_kaizen._aaline(surface, p["wrap_dark"],
                               (wx - px * 2.6, wy - py * 2.6),
                               (wx + px * 2.6, wy + py * 2.6), 2)
            _NS_kaizen._aaline(surface, p["wrap_light"],
                               (wx - px * 1.4, wy - py * 1.4),
                               (wx + px * 1.4, wy + py * 1.4), 1)
        _NS_kaizen._aacircle(surface, p["gold_dark"], (int(ex), int(ey)), 3)
        _NS_kaizen._aacircle(surface, p["gold_mid"],
                             (int(ex) - f, int(ey) - 1), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"],
                             (int(ex) - f - 1, int(ey) - 2), 1)

        # blade sori - isi spidol baja
        mx, my = hx + ux * 34 + px * 3.2, hy + uy * 34 + py * 3.2
        blade = [(hx + px * 3.4, hy + py * 3.4),
                 (mx + px * 2.4, my + py * 2.4),
                 (tx + px * 1.2, ty + py * 1.2),
                 (tx + px * .4, ty + py * .4),
                 (mx - px * 1.1, my - py * 1.1),
                 (hx - px * 2.2, hy - py * 2.2)]
        _NS_kaizen._marker_poly(surface, p["steel_dark"], blade, seed,
                                INK, 2, 1.2, 255, 255, True, 2)
        # garis tinta tepi baja (kulit gelap sisi bawah)
        _NS_kaizen._ink_stroke(surface, p["steel_darkest"],
                               (hx + px * 2.6, hy + py * 2.6),
                               (tx + px * 1.0, ty + py * 1.0), 1, seed + 1, 200)
        # badai kilau gel-pen: mid -> light -> shine
        _NS_kaizen._ink_stroke(surface, p["steel_mid"],
                               (hx, hy), (mx + px * .4, my + py * .4),
                               2, seed + 2, 220)
        _NS_kaizen._ink_stroke(surface, p["steel_light"],
                               (hx + px * 2.6, hy + py * 2.6),
                               (int(tx), int(ty)), 1, seed + 3, 230)
        _NS_kaizen._ink_stroke(surface, p["steel_shine"],
                               (hx + px * 3, hy + py * 3),
                               (tx + px * 1.6, ty + py * 1.6), 1, seed + 4, 255)
        _NS_kaizen._ink_stroke(surface, p["steel_shine"],
                               (int(tx), int(ty)),
                               (int(tx - ux * 5 + px * 2.2),
                                int(ty - uy * 5 + py * 2.2)), 1, seed + 5, 220)
        # hamon bergoyang (garis gelombang di badan bilah)
        hamon = []
        for i in range(1, 9):
            t = i / 9.0
            wave = math.sin(i * math.pi * .72 + phase * .2) * .9
            hamon.append((hx + ux * length * t + px * wave,
                          hy + uy * length * t + py * wave))
        if len(hamon) > 1:
            pygame.draw.aalines(surface, p["wind_mid"], False, hamon)
        _NS_kaizen._aacircle(surface, p["steel_shine"], (int(tx), int(ty)), 2)

        # tsuba 4-lobe doodle
        _NS_kaizen._aacircle(surface, p["shadow_deep"], (int(hx), int(hy)), 6)
        _NS_kaizen._aacircle(surface, p["gold_dark"], (int(hx), int(hy)), 5)
        _NS_kaizen._aacircle(surface, p["gold_mid"], (int(hx), int(hy)), 4)
        for k in range(4):
            aa = A + k * math.pi / 2 + math.pi / 4
            _NS_kaizen._aacircle(surface, p["gold_light"],
                                 (int(hx + math.cos(aa) * 3.4),
                                  int(hy + math.sin(aa) * 3.4)), 1)
        _NS_kaizen._aacircle(surface, p["steel_shine"],
                             (int(hx) - 1, int(hy) - 2), 1)
        _NS_kaizen._aaline(surface, p["steel_light"],
                           (hx + ux * 4 + px * 3, hy + uy * 4 + py * 3),
                           (hx + ux * 4 - px * 2, hy + uy * 4 - py * 2), 2)

        # glint berjalan di bilah
        glint_t = (phase * .85) % 1.0
        gx = hx + ux * length * glint_t + px * 1.6
        gy = hy + uy * length * glint_t + py * 1.6
        _NS_kaizen._aacircle(surface, (*p["steel_shine"], 210),
                             (int(gx), int(gy)), 1)
        _NS_kaizen._aacircle(surface, (*p["wind_white"], 160),
                             (int(gx - ux * 3), int(gy - uy * 3)), 1)

        if glow > 0.05:
            ga = int(150 + 90 * glow)
            _NS_kaizen._aaline(surface, (*p["wind_bright"], min(255, ga)),
                               (hx + px * 3, hy + py * 3),
                               (tx + px * 1.2, ty + py * 1.2), 2)
            if glow > 0.5:
                _NS_kaizen._aaline(surface,
                                   (*p["wind_white"], min(255, ga - 40)),
                                   (hx + px * 4, hy + py * 4),
                                   (tx + px * 2, ty + py * 2), 1)
                _NS_kaizen._spark_star(surface, tx, ty, 7, p["wind_pale"],
                                       int(170 * glow), 4, rot=phase * 1.3,
                                       core=p["white"])

        if attacking:
            _NS_kaizen._aaline(surface, (*p["wind_bright"], 190),
                               (hx + px * 2, hy + py * 2), (tx, ty), 2)
            _NS_kaizen._aaline(surface, (*p["wind_white"], 120),
                               (hx + px * 3, hy + py * 3), (tx, ty), 1)

    # -------------------------------------------------------------------
    # FX AMBIENT / GROUND (doodle)
    # -------------------------------------------------------------------
    def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False, gale=False):
        p = _NS_kaizen.PALETTE
        strength = 1.5 if intense else 1.0

        def build_mist():
            mist = pygame.Surface((170, 56), pygame.SRCALPHA)
            for radius in range(40, 4, -4):
                alpha = int((40 - radius) * 2.6)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*p["wind_dark"], min(255, alpha)),
                        (85 - radius * 2, 28 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            return mist

        mist = _NS_kaizen._static("mist", build_mist)
        old_a = mist.get_alpha()
        mist.set_alpha(int(200 * (0.8 + 0.2 * math.sin(phase))))
        surface.blit(mist, (cx - 85, cy - 16))
        mist.set_alpha(old_a if old_a is not None else 255)

        for i, offset in enumerate((-28, -10, 10, 28)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 4)
            sy = cy + 6 - int(t * 30)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            # lidah angin doodle naik + scribble sian
            _NS_kaizen._wind_tongue(
                surface, (sx, sy), (0.0, -1.0), 8, 4, 300 + i,
                p["wind_mid"], p["wind_bright"], p["ink_soft"],
                alpha=alpha, bend=0.5, scrib=True, gap=0.8)

        for i in range(3):
            angle = phase * 1.2 + i * math.pi * 2 / 3
            r = 28 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_kaizen._draw_wind_swirl(surface, sx, sy, 5, phase + i,
                                        p["wind_bright"], alpha=200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_kaizen._aacircle(surface, (*p["wind_mid"], alpha),
                                     (sx, sy), max(2, 6 - i))

        if gale:
            pulse_ = .6 + .4 * math.sin(phase * 2.4)
            _NS_kaizen._draw_wind_arc(surface, cx, cy + 6, 44,
                                      phase * .8, phase * .8 + 3.4,
                                      (*p["wind_bright"], int(70 * pulse_)),
                                      2, 10)

    def _draw_shadow(surface, x, y):
        def build():
            shadow = pygame.Surface((132, 30), pygame.SRCALPHA)
            for radius in range(13, 0, -1):
                alpha = max(0, (13 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (13 - radius, 13 - radius, 104 + radius * 2, radius * 2))
            pygame.draw.ellipse(shadow,
                                (*_NS_kaizen.PALETTE["wind_darkest"], 40),
                                (10, 5, 110, 13))
            # arsiran doodle di bawah telapak
            for i in range(4):
                px_ = 20 + i * 24
                pygame.draw.line(shadow, (*_NS_kaizen.PALETTE["ink"], 70),
                                 (px_, 22), (px_ + 10, 24), 1)
            return shadow
        surface.blit(_NS_kaizen._static("shadow", build), (x - 66, y - 15))

    def _draw_swordsman_rim_light(surface, x, y, phase):
        def build():
            surf = pygame.Surface((56, 96), pygame.SRCALPHA)
            ry = int(24 + 10 * (0.5 + 0.5 * math.sin(phase)))
            for r in range(min(28, 12), 4, -2):
                alpha = int((min(28, 12) - r) * 7)
                if alpha > 0:
                    pygame.draw.ellipse(surf,
                                        (*_NS_kaizen.PALETTE["wind_mid"],
                                         min(255, alpha)),
                                        (28 - r * 2, 48 - r, r * 4, r * 2))
            return surf
        rim = _NS_kaizen._static("rim_light", build)
        pulse = .7 + .3 * math.sin(phase * 0.6)
        old_a = rim.get_alpha()
        rim.set_alpha(int(255 * pulse))
        surface.blit(rim, (x - 28, y - 48))
        rim.set_alpha(old_a if old_a is not None else 255)

    def _draw_wind_aura(surface, x, y, phase):
        def build():
            aura = pygame.Surface((220, 210), pygame.SRCALPHA)
            for radius in range(88, 6, -5):
                alpha = int((88 - radius) * 0.9)
                if alpha > 0:
                    _NS_kaizen._aacircle(aura,
                                         (*_NS_kaizen.PALETTE["wind_dark"],
                                          min(255, alpha)),
                                         (110, 105), radius)
            return aura
        aura = _NS_kaizen._static("wind_aura", build)
        pulse = .68 + .28 * math.sin(phase * 0.4)
        old_a = aura.get_alpha()
        aura.set_alpha(int(255 * pulse))
        surface.blit(aura, (x - 110, y - 100))
        aura.set_alpha(old_a if old_a is not None else 255)

    def _draw_storm_aura(surface, x, y, phase):
        def build():
            aura = pygame.Surface((260, 230), pygame.SRCALPHA)
            for radius in range(104, 6, -5):
                alpha = int((104 - radius) * 0.9)
                if alpha > 0:
                    _NS_kaizen._aacircle(aura,
                                         (*_NS_kaizen.PALETTE["wind_deep"],
                                          min(255, alpha)),
                                         (130, 115), radius)
            return aura
        aura = _NS_kaizen._static("storm_aura", build)
        pulse = .55 + .45 * math.sin(phase * 1.1)
        old_a = aura.get_alpha()
        aura.set_alpha(int(255 * pulse))
        surface.blit(aura, (x - 130, y - 115))
        aura.set_alpha(old_a if old_a is not None else 255)

    def _draw_wind_platform(surface, x, y, phase, skill):
        def build():
            ring = pygame.Surface((190, 64), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_dark"], 70),
                                (5, 14, 180, 36), 3)
            pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_mid"], 90),
                                (28, 20, 134, 24), 1)
            # goresan arsir di tepi lingkar (doodle)
            for i in range(4):
                a = i * math.tau / 8
                x0 = 95 + math.cos(a) * 82
                y0 = 32 + math.sin(a) * 15
                x1 = 95 + math.cos(a) * 90
                y1 = 32 + math.sin(a) * 17
                pygame.draw.line(ring, (*_NS_kaizen.PALETTE["ink_soft"], 60),
                                 (x0, y0), (x1, y1), 1)
            return ring
        ring = _NS_kaizen._static("platform", build)
        surface.blit(ring, (x - 95, y - 32))
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            x1 = x + int(math.cos(angle) * 28)
            y1 = y + int(math.sin(angle) * 6)
            x2 = x + int(math.cos(angle) * 78)
            y2 = y + int(math.sin(angle) * 15)
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_light"],
                                          int(170 * pulse)), (x1, y1), (x2, y2), 1)
        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = x + int(math.cos(angle) * 72)
            sy = y + int(math.sin(angle) * 13)
            _NS_kaizen._aacircle(surface,
                                 (*_NS_kaizen.PALETTE["wind_bright"], 200),
                                 (sx, sy), 2)
        if skill:
            col = _NS_kaizen.PALETTE["wind_light"]
            al = int(140 * pulse)
            for ang in (0.0, math.pi * 0.5, math.pi, math.pi * 1.5):
                ca, sa = math.cos(ang), math.sin(ang)
                _NS_kaizen._aaline(
                    surface, (*col, al),
                    (x + int(ca * 62), y + int(sa * 11)),
                    (x + int(ca * 78), y + int(sa * 15)), 2)

    # ===================================================================
    # SKILL Q: STEEL WIND / DASH
    # ===================================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = _NS_kaizen._skill_progress(boss, "q", timer)
        pulse = math.sin(phase * 5) * .5 + .5
        fs = _NS_kaizen._fx_scale(boss)

        _skill_outlined_line(surface, (x, y + 40), (tx, ty + 30), 5,
                             p["wind_mid"], 130)
        _skill_outlined_line(surface, (x, y + 40), (tx, ty + 30), 2,
                             p["wind_light"], 160 + int(50 * pulse))
        ang = math.atan2(ty - y, tx - x)
        for i in range(6):
            t = (i / 6 + phase * .45) % 1.0
            _NS_kaizen._chevron(surface,
                                x + (tx - x) * t, y + (ty - y) * t + 34,
                                ang, max(7, int(14 * fs)), p["wind_light"],
                                int(210 * (1 - progress * .45)), 3)
        mark_r = max(10, int(16 * fs))
        _NS_kaizen._aoe_marks(surface, tx, ty + 30, mark_r, p["wind_light"],
                              int(150 + 60 * pulse), phase,
                              ticks=8, tick_len=max(6, int(8 * fs)),
                              squash=.85)

    def _draw_dash_effect(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = _NS_kaizen._skill_progress(boss, "q", timer)
        fs = _NS_kaizen._fx_scale(boss)
        fade = 1.0 - progress
        ang = math.atan2(ty - y, tx - x)

        if progress < 0.28:
            t = progress / 0.28
            bx = x + math.cos(ang) * 30
            by = y - 8 + math.sin(ang) * 14
            burst_r = int((18 + t * 22) * fs)
            _NS_kaizen._aoe_marks(surface, bx, by, burst_r, p["wind_light"],
                                  int(200 * (1 - t)), phase,
                                  ticks=10, corner=False,
                                  tick_len=max(6, int(10 * fs)))
            _NS_kaizen._spark_star(surface, bx, by,
                                   int((14 + 16 * (1 - t)) * fs),
                                   p["wind_pale"], int(240 * (1 - t)), 6,
                                   rot=phase, core=p["white"])
            _NS_kaizen._filled_crescent(
                surface, bx, by, ang, int(22 * fs), int(10 * fs), 1.1,
                (*p["wind_mid"], int(180 * (1 - t))), segments=7)

        for i in range(7):
            t = i / 6.0
            ix = int(x + (tx - x) * t)
            iy = int(y + (ty - y) * t)
            alpha = int(190 * fade * (1 - t * 0.45))
            _NS_kaizen._filled_crescent(
                surface, ix, iy, ang, int(14 * fs), int(6 * fs), 0.95,
                (*p["wind_light"], int(alpha * 0.7)), segments=5)
            ca, sa = math.cos(ang), math.sin(ang)
            _NS_kaizen._aaline(surface, (*p["wind_mid"], alpha),
                               (ix - ca * 10, iy - sa * 8),
                               (ix + ca * 16, iy + sa * 10), 2)

        dx = tx - x
        dy = ty - y
        dist = math.sqrt(dx * dx + dy * dy) or 1
        dx, dy = dx / dist, dy / dist
        px, py = -dy, dx
        for i in range(4):
            off = (i - 4) * 5
            sx = x + px * off
            sy = y + py * off + 6
            ex = sx + dx * (36 + (i % 3) * 10) * fs
            ey = sy + dy * (36 + (i % 3) * 10) * fs
            _NS_kaizen._aaline(surface, (*p["wind_light"], int(220 * fade)),
                               (sx, sy), (ex, ey), 1)
        _skill_outlined_line(surface, (x, y + 42), (tx, ty + 32), 2,
                             p["wind_light"], int(130 * fade))

    def _draw_wind_wall(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        progress = _NS_kaizen._skill_progress(boss, "w", timer)
        facing = boss.direction
        fs = _NS_kaizen._fx_scale(boss)
        pulse = math.sin(phase * 2.4) * .5 + .5

        wall_x = x + int(52 * fs) * facing
        wall_top = y - int(58 * fs)
        wall_bot = y + int(44 * fs)

        if progress < 0.18:
            t = progress / 0.18
            vis = 0.45 + 0.55 * t
            _skill_outlined_line(surface, (wall_x - 34, y + 46),
                                 (wall_x + 34, y + 46), 3,
                                 p["wind_mid"], int(170 * vis))
            for i in range(4):
                _NS_kaizen._chevron(surface, wall_x, y + 12 - i * 16,
                                    -math.pi / 2, 12,
                                    p["wind_light"], int(210 * vis), 2)
            for s in (-1, 1):
                _skill_outlined_line(
                    surface, (wall_x + s * 18, y + 46),
                    (wall_x + s * 18, y + 34), 2, p["wind_light"], int(200 * vis))
                _skill_outlined_line(
                    surface, (wall_x + s * 18, y + 46),
                    (wall_x + s * 6, y + 46), 2, p["wind_light"], int(200 * vis))
            return

        if progress < 0.38:
            t = (progress - 0.18) / 0.2
            h = int((wall_bot - wall_top) * t)
            wt = wall_bot - h
            burst = 1 - t
            _NS_kaizen._aoe_marks(surface, wall_x, y + 40,
                                  int((20 + 28 * t) * fs), p["wind_light"],
                                  int(210 * burst), phase,
                                  ticks=8, corner=False, squash=.5,
                                  tick_len=max(6, int(10 * fs)))
            _NS_kaizen._spark_star(surface, wall_x, y + 30,
                                   int(24 * fs * burst + 4), p["wind_pale"],
                                   int(235 * burst), 8, rot=phase,
                                   core=p["white"])
        else:
            wt = wall_top

        wall_width = int(8 * fs)
        _NS_kaizen._rect(surface, (*p["wind_deep"], 180),
              (wall_x - wall_width - int(3 * fs), wt,
               int(wall_width * 2 + 6 * fs), wall_bot - wt))
        _NS_kaizen._rect(surface, (*p["wind_mid"], 160),
              (wall_x - wall_width, wt,
               int(wall_width * 2), wall_bot - wt))
        _NS_kaizen._aaline(surface, (*p["wind_light"], 190),
                           (wall_x - wall_width // 2, wt + 4),
                           (wall_x - wall_width // 2, wall_bot - 4), 2)
        _NS_kaizen._aaline(surface, (*p["wind_white"], 140),
                           (wall_x - wall_width // 2 + 1, wt + 6),
                           (wall_x - wall_width // 2 + 1, wall_bot - 6), 1)

        for i in range(4):
            swirl_y = wt + i * (wall_bot - wt) / 4
            offset_x = int(math.sin(phase * 2 + i * 0.7) * 4)
            _NS_kaizen._draw_wind_swirl(surface, wall_x + offset_x,
                                        int(swirl_y), 6,
                                        phase + i, p["wind_light"], alpha=210)

        span_h = max(1, wall_bot - wt - 20)
        for i in range(4):
            sx = wall_x + (i - 2) * 4
            streak_start = wt + int((phase * 20 + i * 15) % span_h)
            streak_end = min(wall_bot, streak_start + 22)
            _NS_kaizen._aaline(surface, (*p["wind_light"], 190),
                               (sx, streak_start), (sx, streak_end), 1)

        for s in (-1, 0, 1):
            bx = wall_x + s * int(22 * fs)
            _skill_outlined_line(surface, (bx, y + 46), (bx, y + 34),
                                 2, p["wind_light"], int(140 + 50 * pulse))
        _skill_outlined_line(surface, (wall_x - int(28 * fs), y + 46),
                             (wall_x + int(28 * fs), y + 46), 2,
                             p["wind_mid"], int(130 + 40 * pulse))

        for i in range(5):
            t = (phase * .3 + i / 5) % 1.0
            mx = wall_x + math.sin(i * 2.4 + phase) * 18 * fs
            my = wall_bot - t * (wall_bot - wt)
            _NS_kaizen._aacircle(surface, (*p["wind_light"], int(200 * (1 - t))),
                                 (int(mx), int(my)), 2 if i % 2 else 1)
        for i in range(3):
            a = phase * 1.5 + i * math.tau / 3
            gr = 40 * fs + math.sin(phase * 2 + i) * 5
            _NS_kaizen._aacircle(surface, (*p["wind_light"], 200),
                                 (int(wall_x + math.cos(a) * gr * .6),
                                  int(y - 8 + math.sin(a) * gr * .5)), 2)

        cap_a = int(190 + 50 * pulse)
        _NS_kaizen._spark_star(surface, wall_x, wt, 9, p["wind_light"],
                               cap_a, 4, rot=phase * .7)
        _NS_kaizen._aacircle(surface, (*p["wind_white"], 210),
                             (wall_x, wt), 3)
        _NS_kaizen._spark_star(surface, wall_x, wall_bot, 7,
                               p["wind_light"], cap_a, 4, rot=-phase * .5)
        _NS_kaizen._aacircle(surface, (*p["wind_mid"], 180),
                             (wall_x, wall_bot), 4)

    def _draw_sweep_ground(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        progress = _NS_kaizen._skill_progress(boss, "e", timer)
        pulse = math.sin(phase * 4.5) * .5 + .5
        fs = _NS_kaizen._fx_scale(boss)
        rng = _NS_kaizen._ring_r(boss, 100, surface)
        if progress < 0.4:
            t = progress / 0.4
            rr = int(12 * fs + t * rng)
            _NS_kaizen._aoe_marks(surface, x, y + 24, max(8, rr),
                                  p["wind_pale"], int(200 * (1 - t * .6)),
                                  phase, ticks=12, corner=False,
                                  tick_len=max(6, int(12 * fs)))
            _NS_kaizen._spark_star(surface, x, y + 24,
                                   int(24 * fs * (1 - t * .5)),
                                   p["wind_pale"], int(240 * (1 - t)), 8,
                                   rot=phase, core=p["white"])
            _NS_kaizen._ellipse(surface, (*p["wind_dark"], int(120 * (1 - t))),
                                (x - int(40 * fs), y + 18, int(80 * fs), 16), 0)
            _NS_kaizen._filled_crescent(
                surface, x, y + 10, phase * 2.2, int(28 * fs + t * 20),
                int(12 * fs), 1.2, (*p["wind_mid"], int(170 * (1 - t))), 7)

        for i in range(5):
            angle = i * math.pi / 5 + phase * 0.2
            px = x + int(math.cos(angle) * rng)
            py = y + 28 + int(math.sin(angle) * rng * 0.32)
            h = int(42 * math.sin(progress * math.pi))
            if h <= 0:
                continue
            for seg in range(2):
                sy = py - seg * (h // 2)
                ey = py - (seg + 1) * (h // 2)
                alpha = 200 - seg * 40
                _NS_kaizen._aaline(surface, (*p["wind_light"], alpha),
                                   (px, sy), (px, ey), 2)
                if seg == 0:
                    _NS_kaizen._aaline(surface, (*p["wind_white"], alpha),
                                       (px + 1, sy), (px + 1, ey), 1)
            _NS_kaizen._aacircle(surface, (*p["wind_white"], 220),
                                 (px, py - h), 2)

        for i in range(6):
            a = -phase * 1.3 + i * math.tau / 6
            mx = x + math.cos(a) * rng * .8
            my = y + 28 + math.sin(a) * rng * .32
            _NS_kaizen._aacircle(surface, (*p["wind_light"], int(110 + 50 * pulse)),
                                 (int(mx), int(my)), 2)
    def _draw_sweep_effect(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        progress = _NS_kaizen._skill_progress(boss, "e", timer)
        fs = _NS_kaizen._fx_scale(boss)
        pulse = math.sin(phase * 3) * .5 + .5
        rng = _NS_kaizen._ring_r(boss, 100, surface)

        if progress < 0.4:
            t = progress / 0.4
            rr = int(12 * fs + t * rng)
            _NS_kaizen._aoe_marks(surface, x, y + 24, max(8, rr),
                                  p["wind_pale"], int(200 * (1 - t * .6)),
                                  phase, ticks=12, corner=False,
                                  tick_len=max(6, int(12 * fs)))
            _NS_kaizen._spark_star(surface, x, y + 24,
                                   int(24 * fs * (1 - t * .5)),
                                   p["wind_pale"], int(240 * (1 - t)), 8,
                                   rot=phase, core=p["white"])
            _NS_kaizen._ellipse(surface, (*p["wind_dark"], int(120 * (1 - t))),
                                (x - int(40 * fs), y + 18, int(80 * fs), 16), 0)
            _NS_kaizen._filled_crescent(
                surface, x, y + 10, phase * 2.2, int(28 * fs + t * 20),
                int(12 * fs), 1.2, (*p["wind_mid"], int(170 * (1 - t))), 7)

        for i in range(5):
            angle = i * math.pi / 5 + phase * 0.2
            px = x + int(math.cos(angle) * rng)
            py = y + 28 + int(math.sin(angle) * rng * 0.32)
            h = int(42 * math.sin(progress * math.pi))
            if h <= 0:
                continue
            for seg in range(2):
                sy = py - seg * (h // 2)
                ey = py - (seg + 1) * (h // 2)
                alpha = 200 - seg * 40
                _NS_kaizen._aaline(surface, (*p["wind_light"], alpha),
                                   (px, sy), (px, ey), 2)
                if seg == 0:
                    _NS_kaizen._aaline(surface, (*p["wind_white"], alpha),
                                       (px + 1, sy), (px + 1, ey), 1)
            _NS_kaizen._aacircle(surface, (*p["wind_white"], 220),
                                 (px, py - h), 2)

        for i in range(6):
            a = -phase * 1.3 + i * math.tau / 6
            mx = x + math.cos(a) * rng * .8
            my = y + 28 + math.sin(a) * rng * .32
            _NS_kaizen._aacircle(surface, (*p["wind_light"], int(110 + 50 * pulse)),
                                 (int(mx), int(my)), 2)

    def _draw_tornado_ground(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = _NS_kaizen._skill_progress(boss, "r", timer)
        pulse = math.sin(phase * 4) * .5 + .5
        fs = _NS_kaizen._fx_scale(boss)
        rng = _NS_kaizen._ring_r(boss, 150, surface)

        _NS_kaizen._aoe_marks(surface, x, y + 30, int(rng), p["wind_mid"],
                              int(110 + 50 * pulse), phase,
                              ticks=16, tick_len=max(8, int(rng * .10)))
        _NS_kaizen._aoe_marks(surface, x, y + 30, max(8, int(rng * .92)),
                              p["wind_light"], int(100 + 40 * pulse), -phase,
                              ticks=12, corner=False,
                              tick_len=max(6, int(rng * .07)))

        conv = max(10, int(((1 - progress) * 34 + 10) * fs))
        _NS_kaizen._aoe_marks(surface, tx, ty + 26, conv, p["wind_pale"],
                              int(150 + 70 * pulse), phase,
                              ticks=8, corner=True, inner=True,
                              tick_len=max(6, int(8 * fs)), squash=.85)
        for i in range(4):
            ang = i * math.pi * 2 / 4 + .35
            _NS_kaizen._jagged_crack(surface, tx, ty + 30, ang,
                                     int((18 + (i % 3) * 8) * fs),
                                     (p["wind_deep"], p["wind_dark"]),
                                     int(120 + 60 * pulse),
                                     seed=i + 2, width=2)
        for da in (0, math.pi * 2 / 3, math.pi * 4 / 3):
            _NS_kaizen._chevron(
                surface,
                tx + math.cos(da) * 44 * fs,
                ty + 26 + math.sin(da) * 30 * fs,
                da + math.pi, max(8, int(10 * fs)), p["wind_light"], 200, 3)

    def _draw_tornado(surface, boss, x, y, timer, phase):
        p = _NS_kaizen.PALETTE
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = _NS_kaizen._skill_progress(boss, "r", timer)
        fs = _NS_kaizen._fx_scale(boss)
        pulse = math.sin(phase * 3) * .5 + .5

        if progress < 0.34:
            grow = progress / 0.34
        else:
            grow = 1.0
        fade = 1.0 if progress < 0.86 else max(0.0, 1 - (progress - 0.86) / 0.14)

        if 0.2 < progress < 0.45:
            t = (progress - 0.2) / 0.25
            base_y = ty + 26
            top = int(base_y - min(90 * fs, 230) * (0.5 + 0.5 * (1 - t)))
            for wd, col, al in ((26, p["wind_deep"], 90),
                                (15, p["wind_mid"], 140),
                                (7, p["wind_light"], 200)):
                _NS_kaizen._aaline(surface, (*col, int(al * (1 - t) * fade)),
                                   (tx, top), (tx, base_y), wd)
            _NS_kaizen._aaline(surface,
                               (*p["wind_pale"], int(190 * (1 - t) * fade)),
                               (tx, top), (tx, base_y), 2)
            burst_r = int((14 + t * 84) * fs)
            _NS_kaizen._aoe_marks(surface, tx, base_y, burst_r, p["wind_light"],
                                  int(180 * (1 - t) * fade), phase,
                                  ticks=10, corner=False,
                                  tick_len=max(6, int(12 * fs)))
            _NS_kaizen._spark_star(surface, tx, base_y,
                                   int(28 * (1 - t * .4) * fs),
                                   p["wind_pale"], int(235 * (1 - t) * fade),
                                   8, rot=.3, core=p["white"])

        base_y = ty + 26
        full_h = min(96 * fs, 230)
        height = int(full_h * grow)
        top_y = base_y - height
        if height < 5:
            return

        layers = 5
        for i in range(layers):
            t = i / layers
            layer_y = int(base_y - t * height)
            radius = int((6 + t * 24) * fs)
            swirl_offset = int(math.sin(phase * 3 + t * 6) * 3)
            cx_ = tx + swirl_offset
            alpha_base = int((180 - t * 40) * fade)
            angle = phase * 4 + t * 8
            wx = cx_ + int(math.cos(angle) * radius)
            wy = layer_y + int(math.sin(angle) * radius * 0.3)
            _NS_kaizen._aacircle(surface, (*p["wind_mid"], alpha_base),
                                 (wx, wy), 3)
            _NS_kaizen._ellipse(surface, (*p["wind_mid"], alpha_base),
                                (cx_ - radius, layer_y - int(radius * 0.3),
                                 radius * 2, int(radius * 0.6)), 1)
            if i % 2 == 0:
                _NS_kaizen._ellipse(surface, (*p["wind_light"], alpha_base),
                                    (cx_ - radius + 2, layer_y - int(radius * 0.3) + 1,
                                     max(2, radius * 2 - 4), max(2, int(radius * 0.6) - 2)), 1)

        for arm in range(2):
            for j in range(4):
                a = phase * 2.4 + arm * math.pi + j * .75
                rr = (10 + j * (26 * fs / 4))
                al = int(150 * (1 - j / 4) * fade)
                _NS_kaizen._aacircle(surface, (*p["wind_light"], al),
                                     (int(tx + math.cos(a) * rr),
                                      int(base_y - j / 4 * height +
                                          math.sin(a) * rr * .3)), 2)

        core_x = tx + int(math.sin(phase * 2) * 2)
        _NS_kaizen._aaline(surface, (*p["wind_white"], int(200 * fade)),
                           (core_x, top_y + 5), (core_x, base_y - 5), 2)
        _NS_kaizen._aaline(surface, (*p["wind_light"], int(160 * fade)),
                           (core_x + 1, top_y + 5), (core_x + 1, base_y - 5), 1)

        for i in range(5):
            t = ((phase * 0.3 + i * 0.18) % 1.0)
            py_ = int(base_y - t * height)
            radius = 6 + t * 26 * fs
            angle = phase * 3 + i * math.pi / 2.5
            px_ = tx + int(math.cos(angle) * radius)
            alpha = int(220 * (1 - t * 0.5) * fade)
            _NS_kaizen._aacircle(surface, (*p["wind_white"], alpha), (px_, py_), 2)

        _NS_kaizen._spark_star(surface, tx, top_y, 6, p["wind_pale"],
                               int(160 * fade), 4, rot=phase * 1.8)

        _NS_kaizen._ellipse(surface, (*p["wind_dark"], int(180 * fade)),
                            (tx - int(24 * fs), base_y - 5, int(48 * fs), 12))
        _NS_kaizen._ellipse(surface, (*p["wind_mid"], int(200 * fade)),
                            (tx - int(18 * fs), base_y - 4, int(36 * fs), 9))
        _NS_kaizen._aacircle(surface, (*p["wind_pale"], int(150 * fade * pulse)),
                             (tx, base_y - 3), int((7 + 3 * pulse) * fs))

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by - ay), -(bx - ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            for j in range(n):
                t = (j + 0.5) / n
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 * _NS_kaizen._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

class _NS_thorne:
    """Namespace thorne - PIXEL MASTERWORK v2 (rewrite penuh renderer).

    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.

    Apa yang naik dibanding versi lama
    ----------------------------------
    1. RIG ~1.5x LEBIH BESAR di resolusi native.  Pipeline hero
       (heroes/__init__.py) mengukur badan lalu men-scale agar tinggi
       di layar tetap ~51 px, jadi memperbesar rig TIDAK memperbesar
       hero di arena - melainkan memberi ~2.4 px native per px layar:
       cluster, ramp warna dan muka tetap terbaca setelah smoothscale.
    2. DISIPLIN PIXEL-ART: tiap material maksimal 4-5 nilai ramp,
       siluet punggung bergerigi (tuft bulu, bukan polos), selout
       (outline gelap hanya di sisi bayangan), specular sebagai
       cluster kecil yang disengaja, dither band tipis di perut.
    3. HUE-SHIFT: bayangan bulu didorong dingin (cokelat-ungu),
       highlight didorong hangat (amber) sehingga volume terbaca
       sebagai cahaya, bukan tumpukan pita datar. Key light kiri-atas,
       konsisten dengan lighting.py (LIGHT_DIR = (-1, -1)).
    4. ANATOMI: punuk raksasa + kipas quill ber-pita (crimson ->
       amber -> ivory), kepala boar underbite dengan 2 taring
       melengkung, pauldron baja ber-rivet, sabuk + gesper emas,
       rok vest sobek, mace flanged dengan duri dan specular.
    5. ANIMASI: foot-solver jalan (telapak menapak / terangkat,
       debu saat menapak), quill inertia (crest tertinggal dari
       akselerasi badan), blink + sniff + ear-twitch + dengus saat
       idle, timeline serang 7 keyframe dengan frame IMPACT
       tersendiri (squash, bintang, shockwave, serpihan batu).
    """

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - "Masterwork v2" (hue-shifted, pixel-art ramps)
    # Semua kunci lama dipertahankan agar renderer/panggilan lain tetap jalan;
    # nilai saja yang dituning ulang + beberapa kunci baru.
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Fur / skin - boar brown; bayangan dingin, highlight amber
        "fur_darkest":    ( 30,  18,  12),
        "fur_dark":       ( 66,  40,  26),
        "fur_mid":        (118,  74,  40),
        "fur_light":      (166, 112,  58),
        "fur_high":       (204, 150,  86),
        "fur_rim":        (232, 186, 118),

        # Belly / lighter skin
        "belly_dark":     (142,  98,  58),
        "belly_mid":      (186, 140,  88),
        "belly_light":    (222, 178, 122),

        # Snout - pinkish tan
        "snout_dark":     (148,  82,  62),
        "snout_mid":      (198, 120,  92),
        "snout_light":    (232, 162, 132),

        # Quills - signature: crimson -> amber -> ivory
        "quill_darkest":  ( 70,  34,  12),
        "quill_dark":     (134,  78,  18),
        "quill_mid":      (206, 148,  38),
        "quill_light":    (244, 200,  72),
        "quill_shine":    (255, 234, 128),
        "quill_tip":      (255, 250, 206),
        "quill_root":     (172,  62,  26),

        # Tusks / claws - ivory dengan alur
        "tusk_dark":      (168, 140, 100),
        "tusk_mid":       (220, 198, 158),
        "tusk_light":     (248, 238, 210),
        "tusk_groove":    (138, 108,  74),

        # Armor - cool steel (kontras dingin vs bulu hangat)
        "armor_darkest":  ( 24,  28,  40),
        "armor_dark":     ( 56,  66,  86),
        "armor_mid":      (104, 120, 146),
        "armor_light":    (160, 178, 206),
        "armor_shine":    (216, 232, 250),

        # Leather - straps, belt, grip
        "leather_darkest":( 28,  17,  10),
        "leather_dark":   ( 62,  38,  20),
        "leather_mid":    (100,  64,  34),
        "leather_light":  (142,  96,  54),

        # Cloth - vest perang olive (dipendamkan agar quill menonjol)
        "cloth_dark":     ( 28,  50,  24),
        "cloth_mid":      ( 58,  92,  44),
        "cloth_light":    ( 94, 136,  68),

        # Club - wood
        "wood_dark":      ( 52,  32,  18),
        "wood_mid":       ( 94,  62,  32),
        "wood_light":     (138,  98,  56),

        # Gold accents
        "gold_dark":      ( 96,  68,  20),
        "gold_mid":       (180, 136,  44),
        "gold_light":     (238, 202,  92),

        # Green - snot/goo (viscous nose)
        "goo_darkest":    ( 26,  48,  12),
        "goo_dark":       ( 58, 102,  24),
        "goo_mid":        (110, 170,  50),
        "goo_light":      (166, 218,  90),
        "goo_bright":     (214, 246, 140),

        # Rage - warpath
        "rage_dark":      ( 88,  18,  12),
        "rage_mid":       (172,  40,  24),
        "rage_light":     (232,  82,  48),
        "rage_bright":    (255, 138,  84),

        # Eyes - amber furnace
        "eye_white":      (250, 244, 222),
        "eye_iris":       (226, 130,  26),
        "eye_iris_light": (255, 196,  72),
        "eye_pupil":      ( 18,  10,   4),

        # Misc
        "shadow":         (  0,   0,   0),
        "shadow_deep":    (  5,   7,  15),
        "white":          (255, 255, 255),
    }

    # ------------------------------------------------------------------
    # Surface statis (bayangan / mist / aura) dibangun SEKALI lalu
    # dipakai ulang - tidak ada alokasi surface per frame.
    # ------------------------------------------------------------------
    _STATIC_SURFACES = {}

    def _static(key, builder):
        surf = _NS_thorne._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_thorne._STATIC_SURFACES[key] = surf
        return surf


    def _clamp(color):
        if type(color) is tuple and len(color) == 3:
            _r, _g, _b = color
            if (type(_r) is int and type(_g) is int and type(_b) is int
                    and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
                return color
        return tuple(max(0, min(255, int(c))) for c in color)


    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_thorne._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))


    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thorne._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_thorne.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_thorne._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_thorne._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_thorne._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_thorne._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_thorne._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 150 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ------------------------------------------------------------------
    # Quill helpers
    # ------------------------------------------------------------------
    def _draw_quill(surface, base_x, base_y, length, angle, thickness=2,
                    dark=None, mid=None, light=None, tip=None):
        """Quill kecil (proyektil / ornamen) - murah, 3 band."""
        if dark is None:
            dark = _NS_thorne.PALETTE["quill_darkest"]
        if mid is None:
            mid = _NS_thorne.PALETTE["quill_dark"]
        if light is None:
            light = _NS_thorne.PALETTE["quill_light"]
        if tip is None:
            tip = _NS_thorne.PALETTE["quill_tip"]

        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = base_x + ca * length
        tip_y = base_y + sa * length
        # Perpendicular for thickness
        px = -sa * thickness
        py = ca * thickness

        # Dark base triangle
        _NS_thorne._poly(surface, dark, [
            (base_x + px, base_y + py),
            (base_x - px, base_y - py),
            (tip_x, tip_y),
        ])
        # Mid layer (narrower)
        _NS_thorne._poly(surface, mid, [
            (base_x + px * 0.6, base_y + py * 0.6),
            (base_x - px * 0.6, base_y - py * 0.6),
            (tip_x - ca * 1, tip_y - sa * 1),
        ])
        # Light streak
        _NS_thorne._aaline(surface, light,
                (base_x + px * 0.2, base_y + py * 0.2),
                (tip_x - ca * 1, tip_y - sa * 1), 1)
        # Tip highlight
        _NS_thorne._aacircle(surface, tip, (int(tip_x), int(tip_y)), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------------------
    class QuillProjectile:
        """Sharp quill flying through the air."""
        def __init__(self, sx, sy, tx, ty, speed=9.0, spread_angle=0):
            self.x = float(sx)
            self.y = float(sy)
            dx = tx - sx
            dy = ty - sy
            base_angle = math.atan2(dy, dx)
            self.angle = base_angle + spread_angle
            # Travel in own direction (fan spread)
            self.tx = sx + math.cos(self.angle) * 500
            self.ty = sy + math.sin(self.angle) * 500
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.max_life = 60

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            if self.age > self.max_life:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail 2-tone (band lebar + inti) - terbaca setelah downscale
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_dark"], alpha), (tx, ty), 4)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["quill_mid"], alpha), (tx, ty), 2)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # The quill itself (lebih panjang & banded agar terbaca
                # setelah downscale pipeline hero)
                _NS_thorne._draw_quill(surface, px, py, 23, self.angle, thickness=3)
                # glint berputar di ujung (kilau hidup saat terbang)
                ga = self.age * 1.1
                gx = px + math.cos(self.angle) * 23 + math.cos(ga) * 3
                gy = py + math.sin(self.angle) * 23 + math.sin(ga) * 3
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["quill_shine"],
                                     (int(gx), int(gy)), 1)


    class GooProjectile:
        """Green viscous goo blob (Viscous Nose)."""
        def __init__(self, sx, sy, tx, ty, speed=5.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)
            self.impact_frame = -1

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            if self.impact_frame >= 0:
                if self.age - self.impact_frame > 20:
                    self.alive = False
                return

            # Homing tiap frame ke target selama masih terbang (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_thorne._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 8:
                self.impact_frame = self.age
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 15:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Impact splatter
            if self.impact_frame >= 0:
                t = (self.age - self.impact_frame) / 20.0
                radius = int(8 + t * 24)
                alpha = int(220 * (1 - t))
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_dark"], alpha),
                          (int(self.tx), int(self.ty)), radius + 3)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], alpha),
                          (int(self.tx), int(self.ty)), radius)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_light"], alpha),
                          (int(self.tx), int(self.ty)), radius // 2)
                # Splatter drops
                for i in range(7):
                    a = i * math.pi * 3.5 + phase
                    sr = radius * 1.35
                    sx = int(self.tx + math.cos(a) * sr)
                    sy = int(self.ty + math.sin(a) * sr)
                    _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], alpha), (sx, sy), 4)
                    _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_bright"], alpha), (sx, sy), 1)
                return

            # Trail - dripping goo
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12)
                r = max(1, 6 - (len(self.trail) - i) // 2)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_dark"], alpha), (tx, ty), r + 1)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_mid"], alpha), (tx, ty), r)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["goo_light"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive and self.impact_frame < 0:
                px, py = int(self.x), int(self.y)
                # Main goo blob - irregular shape
                wobble = math.sin(self.age * 0.5) * 1

                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_darkest"], (px, py), 11)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_dark"], (px, py), 10)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"], (px - 1, py - 1), 7)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_light"], (px - 2, py - 2), 4)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_bright"], (px - 3, py - 3), 2)

                # Drip below
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_dark"],
                          (px + int(wobble), py + 8), 4)
                _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"],
                          (px + int(wobble), py + 8), 2)

                # Front splatter chunks
                for i in range(3):
                    a = self.angle + (i - 1) * 0.4
                    dr = 13 + i
                    sx = px + int(math.cos(a) * dr)
                    sy = py + int(math.sin(a) * dr)
                    _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_mid"], (sx, sy), 3)
                    _NS_thorne._aacircle(surface, _NS_thorne.PALETTE["goo_bright"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_th_last_x"):
            boss._th_last_x = boss.x
            boss._th_last_y = boss.y
            return False
        dx = abs(boss.x - boss._th_last_x)
        dy = abs(boss.y - boss._th_last_y)
        boss._th_last_x = boss.x
        boss._th_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_th_prev_timer", -1))
        active = bool(getattr(boss, "_th_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._th_attack_active = True
            active = True

        if active and timer <= 0:
            boss._th_attack_active = False
            active = False

        boss._th_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._th_attack_frame = max(0, cooldown - timer) if active else 0
        boss._th_attack_progress = (
            min(1.0, boss._th_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        for proj in boss._th_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._th_projectiles = [p for p in boss._th_projectiles if p.alive or p.dead_frames < 8]


    def _spawn_goo(boss, x, y):
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        tx, ty = _NS_thorne._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Goo dari moncong (anchor rig v2)
        sx = x + 38 * facing
        sy = y - 30
        tgt = getattr(boss, "target", None)
        proj = _NS_thorne.GooProjectile(
            sx, sy, tx, ty, speed=5.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._th_projectiles.append(proj)


    def _spawn_quill_spray(boss, x, y):
        """Fire a burst of quills from back."""
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        tx, ty = _NS_thorne._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # From back (opposite of facing)
        sx = x - 16 * facing
        sy = y - 30

        # Fan of 7 quills
        for i in range(7):
            spread = (i - 3) * 0.15
            boss._th_projectiles.append(
                _NS_thorne.QuillProjectile(sx, sy, tx, ty, speed=9.0, spread_angle=spread))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_thorne(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thorne._detect_moving(boss)
        _NS_thorne._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_th_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        warpath_active = active_skill == "r"
        bristleback_active = active_skill == "w"

        # ---------- Background layers ----------
        # Portrait LOD sengaja menghilangkan aura/platform seukuran arena agar
        # auto-crop mengisi portrait dengan wajah & material Thorne, bukan
        # lingkaran efek 260 px.
        if not portrait_hd:
            if warpath_active:
                _NS_thorne._draw_rage_aura(surface, x, y, pulse)
            else:
                _NS_thorne._draw_dust_aura(surface, x, y, pulse)
            _NS_thorne._draw_ground_platform(surface, x, y + 60, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_thorne._draw_viscous_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorne._draw_quill_spray_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_thorne._draw_thorne_attack(surface, boss, x, y, warpath_active,
                                           bristleback_active)
        elif moving:
            _NS_thorne._draw_thorne_walk(surface, boss, x, y, warpath_active,
                                         bristleback_active)
        else:
            _NS_thorne._draw_thorne_idle(surface, boss, x, y, warpath_active,
                                         bristleback_active)

        # ---------- Projectiles ----------
        if not portrait_hd:
            _NS_thorne._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_thorne._draw_viscous_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thorne._draw_bristleback_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thorne._handle_quill_spray_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thorne._draw_warpath_effect(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES  (anchor telapak = +64; ground FX mengikuti)
    # ===================================================================
    def _draw_thorne_idle(surface, boss, x, y, warpath=False, bristle=False):
        bob = int(math.sin(boss.pulse * 0.7) * 2.5)
        if not getattr(boss, "_portrait_hd", False):
            _NS_thorne._draw_shadow(surface, x, y + 66)
            _NS_thorne._draw_floating_dust(surface, x, y + 52, boss.pulse, warpath=warpath)
        _NS_thorne._draw_thorne_body(surface, x, y + bob, boss.direction, boss.pulse,
                          "idle", warpath=warpath, bristle=bristle,
                          detail=getattr(boss, "_portrait_hd", False))


    def _draw_thorne_walk(surface, boss, x, y, warpath=False, bristle=False):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_thorne._draw_shadow(surface, x + sway, y + 66)
            _NS_thorne._draw_floating_dust(surface, x + sway, y + 52, phase, trail=True,
                               facing=boss.direction, warpath=warpath)
        _NS_thorne._draw_thorne_body(surface, x + sway, y - bob, boss.direction, phase,
                          "walk", warpath=warpath, bristle=bristle,
                          detail=getattr(boss, "_portrait_hd", False))


    def _draw_thorne_attack(surface, boss, x, y, warpath=False, bristle=False):
        progress = getattr(boss, "_th_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Langkah maju saat ayunan (rig v2 lebih lebar dari sebelumnya)
        step = int(math.sin(progress * math.pi) * 7) * boss.direction
        if not getattr(boss, "_portrait_hd", False):
            _NS_thorne._draw_shadow(surface, x + step, y + 66)
            _NS_thorne._draw_floating_dust(surface, x + step, y + 52, boss.pulse, intense=True,
                               warpath=warpath)
        _NS_thorne._draw_thorne_body(surface, x + step, y, boss.direction, boss.pulse,
                          "attack", progress, warpath=warpath, bristle=bristle,
                          detail=getattr(boss, "_portrait_hd", False))


    # ===================================================================
    # BODY RENDERING - HD boar-porcupine warrior (masterwork pixel-art)
    # ===================================================================
    def _draw_thorne_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, warpath=False, detail=False,
                          bristle=False):
        """Dialihkan ke rig masterwork v2 (lihat _draw_thorne_elite)."""
        _NS_thorne._draw_thorne_elite(
            surface, cx, cy, facing, phase, action, attack_progress,
            detail=detail, warpath=warpath, bristle=bristle)


    # ===================================================================
    # MASTERWORK PRIMITIVES
    # ===================================================================
    def _draw_elite_quill(surface, bx, by, angle, length, width,
                          root, mid, light, tip, wave=0.0, outline=True,
                          shine=None):
        """Quill ber-pita 4 band: pangkal, root berwarna, mid, light,
        ujung ivory + streak specular di sisi kiri-atas.

        Versi v2: band lebih lebar & tegas (tetap terbaca setelah
        downscale pipeline hero), outline hanya di sisi bayangan
        (kanan-bawah) = selout pixel-art klasik.
        """
        a = angle + wave
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa * width, ca * width
        # titik sepanjang poros
        p1 = (bx + ca * length * .34, by + sa * length * .34)
        p2 = (bx + ca * length * .62, by + sa * length * .62)
        p3 = (bx + ca * length * .86, by + sa * length * .86)
        p4 = (bx + ca * length, by + sa * length)
        if outline:
            # selout: offset 1 px ke kanan-bawah (sisi bayangan)
            _NS_thorne._poly(surface, _NS_thorne.PALETTE["shadow_deep"], [
                (bx + px + 1, by + py + 1), (bx - px + 1, by - py + 1),
                (p4[0] + 1, p4[1] + 1)])
        # band pangkal
        _NS_thorne._poly(surface, root, [
            (bx + px, by + py), (bx - px, by - py),
            (p1[0] - px * .55, p1[1] - py * .55), (p1[0] + px * .55, p1[1] + py * .55)])
        # band mid
        _NS_thorne._poly(surface, mid, [
            (p1[0] + px * .55, p1[1] + py * .55), (p1[0] - px * .55, p1[1] - py * .55),
            (p2[0] - px * .45, p2[1] - py * .45), (p2[0] + px * .45, p2[1] + py * .45)])
        # band light
        _NS_thorne._poly(surface, light, [
            (p2[0] + px * .45, p2[1] + py * .45), (p2[0] - px * .45, p2[1] - py * .45),
            (p3[0] - px * .3, p3[1] - py * .3), (p3[0] + px * .3, p3[1] + py * .3)])
        # ujung ivory
        _NS_thorne._poly(surface, tip, [
            (p3[0] + px * .3, p3[1] + py * .3), (p3[0] - px * .3, p3[1] - py * .3),
            p4])
        # streak specular sisi atas-kiri (konsisten arah cahaya)
        if shine is None:
            shine = _NS_thorne.PALETTE["quill_shine"]
        _NS_thorne._aaline(surface, shine,
                (p1[0] - px * .45, p1[1] - py * .45),
                (p3[0] - px * .2, p3[1] - py * .2), 1)


    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bulu bergerigi (pixel-art fur).

        Tiap segmen di-sampling lalu diselang-selingi gigi keluar/masuk
        sepanjang normal - deterministik (hash), aman untuk cache.
        """
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by - ay), -(bx - ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            for j in range(n):
                t = (j + 0.5) / n
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 * _NS_thorne._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out


    def _draw_elite_club(surface, cx, cy, facing, hand, angle, phase,
                         attacking=False, warpath=False):
        """Mace flanged masterwork: gagang kayu 3-band + serat, grip
        kulit ber-wrap, pommel emas, collar baja, kepala bola flanged
        dengan duri dan specular cluster kiri-atas."""
        p = _NS_thorne.PALETTE
        f = 1 if facing >= 0 else -1
        A = angle if f > 0 else math.pi - angle
        ca, sa = math.cos(A), math.sin(A)
        hx, hy = cx + hand[0] * f, cy + hand[1]
        gx, gy = hx - ca * 9, hy - sa * 9            # pommel end
        head_x, head_y = hx + ca * 40, hy + sa * 40  # pusat kepala

        # ── gagang: shadow selout + 3 band kayu ──
        _NS_thorne._aaline(surface, p["shadow_deep"], (int(gx) + f, int(gy) + 1),
                           (int(head_x) + f, int(head_y) + 1), 8)
        _NS_thorne._aaline(surface, p["wood_dark"], (gx, gy), (head_x, head_y), 7)
        _NS_thorne._aaline(surface, p["wood_mid"], (gx, gy), (head_x, head_y), 4)
        _NS_thorne._aaline(surface, p["wood_light"], (gx, gy - 1),
                           (head_x - ca * 6, head_y - sa * 6), 1)
        # serat kayu (grain ticks)
        for gr in (0.30, 0.52):
            tx, ty = hx + ca * (40 * gr - 8), hy + sa * (40 * gr - 8)
            _NS_thorne._aaline(surface, p["wood_dark"],
                               (tx - sa * 3, ty + ca * 3),
                               (tx + sa * 3, ty - ca * 3), 2)
        # ── grip kulit + pommel emas ──
        for i in range(3):
            wx, wy = hx - ca * (2 + i * 3.4), hy - sa * (2 + i * 3.4)
            _NS_thorne._aacircle(surface, p["leather_darkest"],
                                 (int(wx), int(wy)), 4)
            _NS_thorne._aacircle(surface, p["leather_mid"],
                                 (int(wx - ca * .8), int(wy - sa * .8)), 2)
        _NS_thorne._aacircle(surface, p["gold_dark"], (int(gx), int(gy)), 4)
        _NS_thorne._aacircle(surface, p["gold_mid"], (int(gx), int(gy)), 3)
        _NS_thorne._aacircle(surface, p["gold_light"], (int(gx - 1), int(gy - 1)), 1)

        # ── collar baja di pangkal kepala ──
        perp = (-sa, ca)
        cxx, cyy = hx + ca * 27, hy + sa * 27
        _NS_thorne._poly(surface, p["armor_darkest"], [
            (cxx - perp[0] * 7, cyy - perp[1] * 7),
            (cxx + perp[0] * 7, cyy + perp[1] * 7),
            (cxx + ca * 6 + perp[0] * 7, cyy + sa * 6 + perp[1] * 7),
            (cxx + ca * 6 - perp[0] * 7, cyy + sa * 6 - perp[1] * 7)])
        _NS_thorne._poly(surface, p["armor_dark"], [
            (cxx - perp[0] * 5, cyy - perp[1] * 5),
            (cxx + perp[0] * 5, cyy + perp[1] * 5),
            (cxx + ca * 6 + perp[0] * 5, cyy + sa * 6 + perp[1] * 5),
            (cxx + ca * 6 - perp[0] * 5, cyy + sa * 6 - perp[1] * 5)])

        # ── kepala: bola baja ber-flange ──
        # glow hangat saat mid-swing
        if attacking:
            _NS_thorne._aacircle(surface,
                                 (*(p["rage_bright"] if warpath else p["quill_shine"]), 60),
                                 (int(head_x), int(head_y)), 17)
        # 4 flange (sirip mace) bergantian gelap/terang
        for k, (da, ln) in enumerate(((0.62, 13), (-0.62, 13),
                                      (1.55, 11), (-1.55, 11))):
            fa = A + da
            bx2, by2 = head_x + math.cos(fa) * 9, head_y + math.sin(fa) * 9
            tx2, ty2 = head_x + math.cos(fa) * (9 + ln), head_y + math.sin(fa) * (9 + ln)
            sx2, sy2 = -math.sin(fa) * 5, math.cos(fa) * 5
            _NS_thorne._poly(surface, p["shadow_deep" if k % 2 else "armor_darkest"], [
                (bx2 + sx2, by2 + sy2), (bx2 - sx2, by2 - sy2), (tx2, ty2)])
            _NS_thorne._poly(surface, p["armor_dark" if k % 2 else "armor_mid"], [
                (bx2 + sx2 * .7, by2 + sy2 * .7), (bx2 - sx2 * .7, by2 - sy2 * .7),
                (tx2, ty2)])
            _NS_thorne._aaline(surface, p["armor_light"],
                               (bx2 - sx2 * .5, by2 - sy2 * .5), (tx2, ty2), 1)
        # bola inti
        _NS_thorne._aacircle(surface, p["armor_darkest"], (int(head_x), int(head_y)), 11)
        _NS_thorne._aacircle(surface, p["armor_dark"], (int(head_x), int(head_y)), 10)
        _NS_thorne._aacircle(surface, p["armor_mid"],
                             (int(head_x - 1), int(head_y - 1)), 8)
        _NS_thorne._aacircle(surface, p["armor_light"],
                             (int(head_x - 2), int(head_y - 3)), 5)
        # band tengah kepala
        _NS_thorne._aaline(surface, p["armor_dark"],
                           (head_x - perp[0] * 9, head_y - perp[1] * 9),
                           (head_x + perp[0] * 9, head_y + perp[1] * 9), 2)
        # duri baja menghadap depan + 1 belakang
        for da, ln in ((0.0, 16), (0.55, 12), (-0.55, 12),
                       (1.05, 10), (-1.05, 10), (math.pi, 9)):
            _NS_thorne._draw_elite_quill(
                surface, head_x, head_y, A + da, ln, 3,
                p["armor_darkest"], p["armor_dark"],
                p["armor_light"], p["armor_shine"])
        # specular cluster kiri-atas + titik kilau putih
        _NS_thorne._aacircle(surface, p["armor_shine"],
                             (int(head_x - 4), int(head_y - 5)), 2)
        if attacking:
            _NS_thorne._aacircle(surface, p["white"],
                                 (int(head_x - 4), int(head_y - 6)), 1)


    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose.

        Keyframe: (progress, bob, lean, hand_x, hand_y, club_angle,
                   flare, tremble)
          0.14  wind-up   : club diangkat belakang, badan turun
          0.30  tension   : gemetar 1 px, quill mengembang
          0.48  strike    : ayunan tercepat (smear aktif)
          0.54  IMPACT    : squash maksimum + bintang + serpihan
          0.72  follow    : rebound overshoot
          1.00  recover   : kembali ke pose istirahat
        """
        keys = (
            (0.00,  0,  1,  30,   4, 0.30, 1.00, 0),
            (0.14,  6, -6,  16, -26, -2.62, 1.14, 0),
            (0.30,  7, -7,  13, -28, -2.86, 1.20, 1),
            (0.48, -3,  8,  34,  18,  0.92, 1.10, 0),
            (0.54,  7,  9,  31,  23,  0.74, 1.06, 0),
            (0.72,  1,  5,  30,  12,  0.44, 1.00, 0),
            (1.00,  0,  1,  30,   4, 0.30, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)          # smoothstep
                vals = tuple(
                    a + (b - a) * t for a, b in zip(k0[1:6], k1[1:6]))
                flare = k0[6] + (k1[6] - k0[6]) * t
                tremble = 1 if (k0[7] and t < 0.9) else 0
                return {
                    "bob": int(round(vals[0])), "lean": int(round(vals[1])),
                    "hand": (int(round(vals[2])), int(round(vals[3]))),
                    "angle": vals[4],
                    "flare": flare, "tremble": tremble,
                }
        return {"bob": 0, "lean": 1, "hand": (30, 4), "angle": 0.30,
                "flare": 1.0, "tremble": 0}


    def _draw_thorne_masterwork_details(surface, pt, f):
        """Micro-detail khusus portrait LOD. Di skala arena tanda-tanda ini
        runtuh menjadi noise, jadi LOD mengeluarkannya dari cache gameplay."""
        p = _NS_thorne.PALETTE
        # barb ticks pada crest quill (pita punya kait kecil)
        for i in range(7):
            _NS_thorne._aaline(surface, p["quill_light"],
                               pt(-8 - i * 3, -52 - i),
                               pt(-13 - i * 3, -56 - i), 1)
        # serat bulu dada mengikuti bentuk
        for i in range(6):
            _NS_thorne._aaline(surface,
                               p["fur_high"] if i % 2 else p["fur_light"],
                               pt(-8 + i * 4, -14 + (i % 3)),
                               pt(-6 + i * 4, -4 + (i % 3)), 1)
        # kerut moncong & alur taring
        _NS_thorne._aaline(surface, p["snout_light"], pt(24, -41), pt(31, -39), 1)
        _NS_thorne._aaline(surface, p["tusk_groove"], pt(25, -33), pt(29, -45), 1)
        _NS_thorne._aaline(surface, p["tusk_groove"], pt(33, -31), pt(37, -42), 1)
        # jahitan strap (pola silang) + anyaman sabuk
        for i in range(4):
            xx = -24 + i * 12
            _NS_thorne._aaline(surface, p["leather_light"],
                               pt(xx, -22 + i), pt(xx + 3, -19 + i), 1)
            _NS_thorne._aaline(surface, p["leather_light"],
                               pt(xx + 3, -22 + i), pt(xx, -19 + i), 1)
        for xx in (-16, -8, 8, 16):
            _NS_thorne._aacircle(surface, p["leather_light"], pt(xx, 25), 1)
        # goresan pauldron + kilau rivet (bahu belakang)
        for a in (-.7, -.2, .3):
            _NS_thorne._aaline(surface, p["armor_mid"], pt(-26, -26),
                               pt(-26 - math.cos(a) * 6, -26 + math.sin(a) * 6), 1)
        _NS_thorne._aacircle(surface, p["armor_shine"], pt(-31, -24), 1)
        _NS_thorne._aacircle(surface, p["gold_light"], pt(2, 25), 1)
        # highlight cakar kaki depan + bantalan telapak
        _NS_thorne._aaline(surface, p["tusk_light"], pt(18, 66), pt(26, 66), 1)
        _NS_thorne._aacircle(surface, p["fur_darkest"], pt(19, 61), 2)
        _NS_thorne._aacircle(surface, p["fur_darkest"], pt(25, 61), 2)
        # uap napas kecil dari moncong
        _NS_thorne._aacircle(surface, (*p["fur_light"], 120), pt(45, -36), 2)
        _NS_thorne._aacircle(surface, (*p["fur_light"], 70), pt(48, -38), 1)
        # kilau campuran khusus portrait (warna baru = LOD lebih kaya)
        _NS_thorne._aaline(surface,
                           _NS_thorne._mix(p["tusk_light"], p["white"], .4),
                           pt(24, -46), pt(29, -45), 1)
        _NS_thorne._aaline(surface,
                           _NS_thorne._mix(p["fur_high"], p["fur_rim"], .5),
                           pt(-16, -41), pt(-4, -43), 1)
        _NS_thorne._aacircle(surface,
                             _NS_thorne._mix(p["gold_light"], p["white"], .5),
                             pt(-15, 25), 1)
        _NS_thorne._aacircle(surface,
                             _NS_thorne._mix(p["armor_shine"], p["white"], .5),
                             pt(-24, -30), 1)


    def _draw_thorne_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False, warpath=False,
                           bristle=False):
        """Rig masterwork v2 - boar-porcupine pixel-art, 100% prosedural.

        Semua koordinat lokal: (0,0) = jangkar pinggul, x maju (facing),
        y ke bawah. Telapak menapak di +64. Skala rig ~1.5x versi lama
        (pipeline hero otomatis menormalkan ukuran akhir di arena).
        """
        p = _NS_thorne.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.7) if walk else 0.0
        breath = math.sin(phase * 0.75)

        # ═══ 1. GERAK BADAN: root / lean / sway / quill lag ═══
        crest_tilt = 0.0
        if walk:
            root_y = int(math.sin(phase * 2.0) * 2.5) - 2
            sway = int(math.sin(phase) * 3.0)
            lean = (4 + int(abs(stride) * 2)) * f
            crest_tilt = math.sin(phase + 2.6) * 0.07
            pose = {"hand": (30 + int(math.sin(phase + math.pi) * 5),
                             4 + int(abs(math.sin(phase)) * 2)),
                    "angle": 0.38 + math.sin(phase + math.pi) * 0.12,
                    "flare": 1.0, "tremble": 0}
        elif attack:
            pose = _NS_thorne._attack_pose(ap)
            root_y = pose["bob"]
            sway = 0
            lean = pose["lean"] * f
            crest_tilt = -pose["lean"] * 0.045
            if pose["tremble"]:
                sway = 1 if int(phase * 30) % 2 else -1
        else:
            root_y = int(breath * 2.2)
            sway = int(math.sin(phase * 0.5) * 2.0)
            lean = int(math.sin(phase * 0.5 + 1.2) * 1.5)
            pose = {"hand": (30, 4 + int(breath * 1.5)),
                    "angle": 0.30 + breath * 0.04,
                    "flare": 1.0 + 0.03 * breath, "tremble": 0}
        flare = pose["flare"]
        if bristle:
            # crest berdiri lebih tegak + berdenyut saat duri aktif
            flare *= 1.1 + .05 * math.sin(phase * 3)
        off_x = lean + sway

        def pt(dx, dy):
            return (int(cx + dx * f + off_x), int(cy + dy + root_y))

        def poly(color, points, selout=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if selout:
                _NS_thorne._poly(surface, p["fur_darkest"],
                                 [(x + f, y + 1) for x, y in pts])
            _NS_thorne._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_thorne._aaline(surface, p["fur_darkest"], aa, bb, width + 3)
            _NS_thorne._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_thorne._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        def qa(angle):
            return angle if f > 0 else math.pi - angle

        wave = math.sin(phase * 1.25)

        # ═══ 2. PALET CREST (swap rage saat warpath / emas saat bristle) ═══
        if warpath:
            c_root, c_mid, c_light = p["rage_mid"], p["rage_light"], p["rage_bright"]
            b_root, b_mid, b_light = p["rage_dark"], p["rage_dark"], p["rage_mid"]
            f_root, f_mid, f_light = p["rage_mid"], p["rage_bright"], p["quill_tip"]
        else:
            c_root, c_mid, c_light = p["quill_root"], p["quill_mid"], p["quill_light"]
            b_root, b_mid, b_light = p["quill_darkest"], p["quill_dark"], p["quill_mid"]
            f_root, f_mid, f_light = p["quill_mid"], p["quill_light"], p["quill_tip"]
        c_tip = p["quill_tip"]
        if bristle and not warpath:
            # Bristleback aktif: duri "bercitra" menyala emas (sangat terbaca).
            mix = _NS_thorne._mix
            c_root = mix(c_root, p["gold_mid"], .55)
            c_mid = mix(c_mid, p["gold_light"], .55)
            c_light = mix(c_light, p["quill_shine"], .5)
            b_root = mix(b_root, p["gold_dark"], .5)
            b_mid = mix(b_mid, p["gold_mid"], .5)
            b_light = mix(b_light, p["gold_light"], .5)
            f_root = mix(f_root, p["gold_light"], .5)
            f_mid = mix(f_mid, p["quill_shine"], .5)
            f_light = p["quill_shine"]
            c_tip = p["quill_shine"]

        # ═══ 3. CREST LAPISAN BELAKANG (mengisi siluet kipas) ═══
        back = ((-28, -20, -2.70, 36, 5), (-32, -28, -2.50, 44, 6),
                (-33, -36, -2.28, 50, 6), (-31, -43, -2.05, 53, 6),
                (-26, -49, -1.82, 54, 6), (-19, -54, -1.58, 53, 6),
                (-11, -57, -1.34, 49, 5), (-3, -58, -1.10, 43, 5),
                (5, -56, -0.86, 36, 5))
        for i, (rx, ry, ang, ln, wd) in enumerate(back):
            w = wave * .035 * (1 + i % 3) + crest_tilt
            _NS_thorne._draw_elite_quill(
                surface, *pt(rx - 3, ry + 4),
                qa(ang - .10), (ln + 6) * flare, wd,
                b_root, b_mid, b_light, b_light, wave=w)

        # ═══ 4. EKOR kecil ber-tuft ═══
        tail_w = math.sin(phase * (2.4 if walk else 0.9)) * 0.25
        _NS_thorne._draw_elite_quill(
            surface, *pt(-33, 14), qa(math.pi - .35 + tail_w), 17, 3,
            p["fur_darkest"], p["fur_dark"], p["fur_mid"], p["fur_light"],
            wave=tail_w * .3)

        # ═══ 5. LENGAN BELAKANG (di belakang torso) ═══
        if attack:
            rear_hand = (2 + int(ap * 10), -6 + int(ap * 8))
        elif walk:
            rear_hand = (-22 + int(stride * 7), 16)
        else:
            rear_hand = (-24, 16 + int(breath * 1.5))
        r_shoulder, r_elbow = (-18, -22), (-26, -3)
        limb(r_shoulder, r_elbow, 13, p["fur_dark"], p["fur_light"])
        limb(r_elbow, rear_hand, 11, p["fur_mid"], p["fur_high"])
        rhx, rhy = pt(*rear_hand)
        _NS_thorne._aacircle(surface, p["fur_darkest"], (rhx, rhy), 8)
        _NS_thorne._aacircle(surface, p["fur_dark"], (rhx, rhy), 7)
        _NS_thorne._aacircle(surface, p["fur_mid"], (rhx - 1, rhy - 2), 4)
        for c in (-4, 0, 4):
            _NS_thorne._poly(surface, p["tusk_mid"],
                             [(rhx + c - 1, rhy + 5), (rhx + c + 2, rhy + 5),
                              (rhx + c + 1, rhy + 8)])
        # vambrace baja berlapis + duri siku + rivet
        _NS_thorne._aaline(surface, p["fur_darkest"], pt(-27, -10), pt(-22, 2), 12)
        _NS_thorne._aaline(surface, p["armor_darkest"], pt(-27, -10), pt(-22, 2), 10)
        _NS_thorne._aaline(surface, p["armor_dark"], pt(-27, -10), pt(-22, 2), 7)
        _NS_thorne._aaline(surface, p["armor_mid"], pt(-26, -11), pt(-22, -1), 3)
        _NS_thorne._aacircle(surface, p["armor_light"], pt(-26, -8), 1)
        _NS_thorne._aacircle(surface, p["armor_light"], pt(-24, -2), 1)
        _NS_thorne._draw_elite_quill(
            surface, *pt(-26, -8), qa(math.pi - .55), 11, 2,
            p["armor_darkest"], p["armor_dark"],
            p["armor_light"], p["armor_shine"])

        # ═══ 6. KAKI: haunch + lutut + telapak 3-cakar (foot solver) ═══
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 12) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 12) if walk else 0
        rear_foot = (-16 - int(stride * 8), 64 - rear_lift)
        front_foot = (18 + int(stride * 9), 64 - front_lift)

        for hip, knee, foot, shade, lift, planted in (
                ((-16, 26), (-18, 44), rear_foot, p["fur_darkest"], rear_lift,
                 walk and rear_lift == 0),
                ((10, 26), (16, 44), front_foot, p["fur_dark"], front_lift,
                 walk and front_lift == 0)):
            knee = (knee[0], knee[1] - lift)
            hx0, hy0 = hip
            # haunch (paha boar besar)
            poly(shade, [(hx0 - 13, hy0 - 12), (hx0 + 11, hy0 - 13),
                         (hx0 + 13, hy0 + 6), (hx0 + 2, hy0 + 13),
                         (hx0 - 12, hy0 + 10)], False)
            _NS_thorne._poly(
                surface, p["fur_mid"] if shade == p["fur_dark"] else p["fur_dark"],
                [pt(hx0 - 9, hy0 - 10), pt(hx0 + 7, hy0 - 11),
                 pt(hx0 + 8, hy0 - 2), pt(hx0 - 7, hy0 - 1)])
            # paha -> lutut -> telapak
            poly(shade, [hip, (hip[0] + 10, hip[1] + 2), (knee[0] + 7, knee[1]),
                         (foot[0] + 6, foot[1] - 8), (foot[0] - 7, foot[1] - 8),
                         (knee[0] - 6, knee[1] - 2)])
            limb(knee, (foot[0], foot[1] - 7), 11, p["fur_mid"], p["fur_light"])
            # tuft lutut
            _NS_thorne._aaline(surface, p["fur_dark"],
                               pt(knee[0] - 4, knee[1] + 2), pt(knee[0] - 7, knee[1] + 6), 2)
            # telapak besar + 3 cakar + dew claw
            poly(p["fur_darkest"], [(foot[0] - 11, foot[1] - 7), (foot[0] + 11, foot[1] - 7),
                                    (foot[0] + 13, foot[1] + 2), (foot[0] - 11, foot[1] + 2)])
            poly(p["fur_dark"], [(foot[0] - 10, foot[1] - 6), (foot[0] + 10, foot[1] - 6),
                                 (foot[0] + 11, foot[1]), (foot[0] - 10, foot[1])], False)
            for claw in (-7, 0, 7):
                poly(p["tusk_mid"], [(foot[0] + claw, foot[1] + 1),
                                     (foot[0] + claw + 4, foot[1] + 1),
                                     (foot[0] + claw + 3, foot[1] + 5)], False)
                _NS_thorne._aaline(surface, p["tusk_light"],
                                   pt(foot[0] + claw + 1, foot[1] + 2),
                                   pt(foot[0] + claw + 3, foot[1] + 4), 1)
            poly(p["tusk_dark"], [(foot[0] - 13, foot[1] - 5),
                                  (foot[0] - 9, foot[1] - 6),
                                  (foot[0] - 10, foot[1] - 1)], False)
            # bayangan kontak tanah
            if planted or not walk:
                _NS_thorne._ellipse(
                    surface, (*p["shadow_deep"], 70),
                    (*pt(foot[0] - 12, foot[1] + 1), 24, 7))
            # debu saat telapak menapak (walk)
            if walk and planted and abs(stride_vel) > 0.4:
                fdx, fdy = pt(foot[0] - 8, foot[1] + 1)
                for k in range(3):
                    _NS_thorne._aacircle(
                        surface, (*p["fur_mid"], max(20, 110 - k * 30)),
                        (fdx - k * 5 * f, fdy - k * 2), max(1, 3 - k))

        # ═══ 7. TORSO: punuk besar + tepi bulu bergerigi ═══
        spine_back = ((-24, 26), (-33, 10), (-37, -10), (-33, -30),
                      (-22, -44), (-6, -48), (10, -41))
        jagged = _NS_thorne._tuft_points(spine_back, depth=4.5, seed=11)
        outline_pts = ([(int(x), int(y)) for x, y in jagged] +
                       [(18, -30), (24, -14), (25, 2), (20, 20), (8, 29),
                        (-8, 30)])
        pts = [pt(x, y) for x, y in outline_pts]
        # selout: outline gelap hanya di sisi bayangan (kanan-bawah)
        _NS_thorne._poly(surface, p["fur_darkest"],
                         [(x + f, y + 1) for x, y in pts])
        _NS_thorne._poly(surface, p["fur_dark"], pts)
        # band mid (2/3 atas-kiri)
        poly(p["fur_mid"], [
            (-30, 22), (-36, 6), (-34, -12), (-29, -28), (-19, -40),
            (-5, -44), (8, -38), (12, -26), (4, -18), (-10, -16),
            (-22, -2), (-26, 10)], False)
        # band light (topi punuk)
        poly(p["fur_light"], [
            (-27, -22), (-20, -38), (-6, -43), (6, -37), (9, -28),
            (0, -22), (-14, -19)], False)
        # specular punuk + rim 1 px kiri-atas
        _NS_thorne._aaline(surface, p["fur_high"], pt(-18, -40), pt(-2, -43), 3)
        _NS_thorne._aaline(surface, p["fur_rim"], pt(-14, -43), pt(-4, -44), 1)
        # serat bulu (strokes ikut bentuk)
        for i in range(5):
            dx = -22 + i * 7
            _NS_thorne._aaline(surface, p["fur_light"],
                               pt(dx, -18 - i % 2), pt(dx + 2, -8 - i % 2), 1)
        for i in range(4):
            dx = -24 + i * 9
            _NS_thorne._aaline(surface, p["fur_darkest"],
                               pt(dx, 2 + i), pt(dx + 1, 10 + i), 1)
        # dada / perut terang
        poly(p["belly_dark"], [(6, -6), (20, -8), (23, 4), (16, 16),
                               (4, 16), (1, 6)], False)
        poly(p["belly_mid"], [(9, -4), (18, -5), (20, 4), (14, 13),
                              (5, 12), (4, 4)], False)
        _NS_thorne._aaline(surface, p["belly_light"], pt(9, -2), pt(16, -2), 1)
        # dither band perut (tekstur pixel-art klasik)
        for i in range(4):
            _NS_thorne._aacircle(surface, p["belly_light"],
                                 pt(8 + i * 4, 8 + i % 2), 1)
        # AO bawah sabuk & bawah kepala
        _NS_thorne._aaline(surface, (*p["fur_darkest"], 110),
                           pt(-22, 17), pt(20, 15), 5)
        _NS_thorne._poly(surface, (*p["fur_darkest"], 90), [
            pt(10, -32), pt(22, -26), pt(20, -18), pt(10, -22)])

        # strap kain menyilang X (war straps) + jahitan
        _NS_thorne._aaline(surface, p["cloth_dark"], pt(-28, -22), pt(20, 4), 8)
        _NS_thorne._aaline(surface, p["cloth_mid"], pt(-28, -22), pt(20, 4), 5)
        _NS_thorne._aaline(surface, p["cloth_light"], pt(-27, -23), pt(19, 3), 1)
        _NS_thorne._aaline(surface, p["cloth_dark"], pt(16, -32), pt(-24, 8), 8)
        _NS_thorne._aaline(surface, p["cloth_mid"], pt(16, -32), pt(-24, 8), 5)
        _NS_thorne._aaline(surface, p["cloth_light"], pt(15, -33), pt(-23, 7), 1)
        for i in range(5):
            t = 0.12 + i * 0.19
            sx1, sy1 = -28 + 48 * t, -22 + 26 * t
            _NS_thorne._aacircle(surface, p["cloth_light"], pt(sx1, sy1 - 3), 1)

        # ═══ 8. SABUK + GESPER EMAS + POUCH ═══
        poly(p["leather_darkest"], [(-24, 18), (22, 16), (25, 27),
                                    (10, 33), (-10, 33), (-25, 28)])
        poly(p["leather_dark"], [(-23, 19), (21, 17), (23, 25),
                                 (9, 30), (-9, 30), (-23, 26)], False)
        _NS_thorne._aaline(surface, p["leather_light"], pt(-21, 19), pt(20, 17), 1)
        _NS_thorne._rect(surface, p["gold_dark"], (*pt(-5, 20), 13, 12), 2)
        _NS_thorne._rect(surface, p["gold_mid"], (*pt(-4, 21), 11, 10), 2)
        _NS_thorne._rect(surface, p["gold_light"], (*pt(-2, 23), 6, 5), 1)
        _NS_thorne._aacircle(surface, p["white"], pt(2, 24), 1)
        poly(p["leather_dark"], [(-20, 22), (-10, 21), (-9, 32), (-14, 34),
                                 (-21, 30)], False)
        _NS_thorne._aaline(surface, p["leather_mid"], pt(-19, 24), pt(-11, 23), 1)
        _NS_thorne._aacircle(surface, p["gold_mid"], pt(-15, 26), 2)
        _NS_thorne._aacircle(surface, p["gold_light"], pt(-15, 25), 1)

        # ═══ 9. ROK VEST sobek (torn war skirt) ═══
        poly(p["cloth_dark"], [(-6, 28), (20, 26), (26, 38), (21, 45),
                               (16, 38), (11, 46), (5, 39), (-1, 47),
                               (-6, 38)])
        poly(p["cloth_mid"], [(-4, 29), (18, 27), (23, 36), (18, 41),
                              (13, 35), (8, 42), (3, 36), (-3, 42),
                              (-5, 35)], False)
        _NS_thorne._aaline(surface, p["cloth_light"], pt(-2, 30), pt(17, 28), 1)
        _NS_thorne._aaline(surface, p["cloth_dark"], pt(2, 32), pt(4, 40), 1)
        _NS_thorne._aaline(surface, p["cloth_dark"], pt(12, 31), pt(14, 37), 1)
        for xx in (0, 6, 12, 18):
            _NS_thorne._aacircle(surface, p["cloth_light"], pt(xx, 44 - xx % 6), 1)

        # ═══ 10. BUNDLE QUIIL CADANGAN di pinggul belakang ═══
        for k in range(3):
            _NS_thorne._draw_elite_quill(
                surface, *pt(-26 - k * 2, 14), qa(-1.9 - k * 0.14), 20 - k * 2, 2,
                c_root, c_mid, c_light, c_tip, wave=wave * .015)
        _NS_thorne._aaline(surface, p["leather_dark"], pt(-29, 12), pt(-23, 11), 3)

        # ═══ 11. PAULDRON baja ber-rivet (bahu belakang) ═══
        poly(p["armor_darkest"], [(-10, -30), (-22, -32), (-32, -24),
                                  (-31, -12), (-21, -7), (-12, -14)])
        poly(p["armor_dark"], [(-12, -28), (-21, -29), (-28, -22),
                               (-27, -13), (-19, -10), (-13, -15)], False)
        poly(p["armor_mid"], [(-14, -26), (-20, -27), (-24, -21),
                              (-22, -15), (-16, -16)], False)
        _NS_thorne._aaline(surface, p["armor_light"], pt(-16, -26), pt(-23, -21), 1)
        _NS_thorne._aaline(surface, p["armor_light"], pt(-13, -18), pt(-19, -13), 1)
        for a in (-0.85, -0.45, -0.05):
            _NS_thorne._draw_elite_quill(
                surface, *pt(-30 - math.cos(a) * 2, -18 + math.sin(a) * 4),
                qa(a - 1.35), 10, 2,
                p["armor_darkest"], p["armor_dark"],
                p["armor_light"], p["armor_shine"])
        _NS_thorne._aacircle(surface, p["gold_mid"], pt(-24, -22), 2)
        _NS_thorne._aacircle(surface, p["gold_light"], pt(-24, -23), 1)
        _NS_thorne._aacircle(surface, p["armor_shine"], pt(-15, -25), 1)

        # ═══ 12. CREST UTAMA ber-pita (pangkal menimpa punuk) ═══
        crest = ((-26, -20, -2.72, 34, 6), (-30, -27, -2.52, 42, 7),
                 (-32, -35, -2.30, 48, 7), (-30, -42, -2.06, 51, 7),
                 (-25, -48, -1.82, 52, 7), (-18, -53, -1.58, 50, 7),
                 (-10, -56, -1.34, 46, 6), (-2, -57, -1.10, 40, 6),
                 (6, -55, -0.88, 34, 5))
        for i, (rx, ry, ang, ln, wd) in enumerate(crest):
            w = wave * .045 * (1 + i % 3) + crest_tilt
            _NS_thorne._draw_elite_quill(
                surface, *pt(rx, ry), qa(ang), ln * flare, wd,
                c_root, c_mid, c_light, c_tip, wave=w)
        # ridge bulu tempat quill tumbuh
        _NS_thorne._aaline(surface, p["fur_darkest"],
                           pt(-28, -18), pt(-22, -46), 7)
        _NS_thorne._aaline(surface, p["fur_dark"],
                           pt(-27, -19), pt(-22, -44), 4)
        # kilau pita quill (menghadap cahaya kiri-atas)
        _NS_thorne._aaline(surface, p["quill_shine"], pt(-32, -34), pt(-30, -44), 1)

        # ═══ 13. KEPALA BOAR: dome, alis, mata, moncong, rahang ═══
        poly(p["fur_darkest"], [(-6, -52), (6, -57), (18, -52), (25, -42),
                                (23, -30), (12, -25), (0, -30), (-6, -40)])
        poly(p["fur_dark"], [(-4, -51), (6, -55), (16, -50), (22, -41),
                             (20, -31), (11, -27), (1, -31), (-4, -40)], False)
        poly(p["fur_mid"], [(-2, -49), (6, -52), (14, -48), (18, -40),
                            (16, -33), (9, -29), (2, -32), (-2, -40)], False)
        poly(p["fur_light"], [(2, -50), (9, -50), (13, -44), (10, -36),
                              (4, -38), (1, -44)], False)
        # telinga kecil (twitch periodik)
        ear_twitch = 2 if (phase % 6.283) < 0.35 else 0
        poly(p["fur_darkest"], [(-4, -52), (-10, -62 - ear_twitch), (2, -55)], False)
        poly(p["snout_dark"], [(-4, -53), (-8, -59 - ear_twitch), (0, -55)], False)
        # alis berat menggantung (angry brow)
        poly(p["fur_darkest"], [(2, -46), (16, -47), (18, -41), (4, -40)], False)
        # mata: socket besar + iris amber + glint + blink
        ex, ey = pt(11, -42)
        _NS_thorne._rect(surface, p["fur_darkest"], (ex - 2, ey - 2, 9, 6))
        if warpath:
            _NS_thorne._rect(surface, p["rage_bright"], (ex, ey - 1, 6, 4))
            _NS_thorne._rect(surface, p["rage_light"], (ex + 1, ey, 3, 2))
            _NS_thorne._aacircle(surface, (*p["rage_bright"], 90), (ex + 2, ey), 6)
        elif (phase % 6.283) < 0.16:
            _NS_thorne._rect(surface, p["fur_dark"], (ex, ey + 1, 6, 2))
        else:
            _NS_thorne._rect(surface, p["eye_iris"], (ex, ey - 1, 6, 4))
            _NS_thorne._rect(surface, p["eye_iris_light"], (ex + 1, ey - 1, 4, 2))
            _NS_thorne._rect(surface, p["eye_pupil"], (ex + 3, ey, 2, 2))
            _NS_thorne._rect(surface, p["eye_white"], (ex + 1, ey - 1, 1, 1))
        # moncong besar + cuping (sniff periodik)
        sniff = 1 if 0.8 < (phase % 6.283) < 1.4 else 0
        poly(p["snout_dark"], [(20, -44), (34, -43), (42, -36), (39, -27),
                               (28, -24), (20, -31)])
        poly(p["snout_mid"], [(21, -43), (33, -42), (39, -35), (37, -28),
                              (28, -26), (21, -31)], False)
        _NS_thorne._aaline(surface, p["snout_light"], pt(23, -41), pt(32, -40), 1)
        _NS_thorne._aacircle(surface, p["fur_darkest"], pt(38, -36 + sniff), 3)
        _NS_thorne._aacircle(surface, p["snout_dark"], pt(37, -37 + sniff), 1)
        _NS_thorne._aacircle(surface, p["snout_light"], pt(36, -39), 1)
        # rahang underbite + deretan gigi bawah
        poly(p["snout_dark"], [(19, -30), (33, -29), (31, -22), (18, -23)], False)
        poly(p["snout_mid"], [(20, -29), (31, -28), (30, -24), (19, -25)], False)
        for tx in (21, 26, 31):
            poly(p["tusk_mid"], [(tx, -26), (tx + 3, -26), (tx + 2, -21)], False)
        # taring besar melengkung (bezier, ivory 3-band + selout)
        for bx, by, cxp, cyp, tx2, ty2, wid in (
                (23, -25, 30, -34, 31, -48, 6),
                (30, -24, 37, -32, 39, -44, 5)):
            x0, y0, x1, y1, x2, y2 = bx, by, cxp, cyp, tx2, ty2
            for tt in (0.0, 0.5):
                # titik pada kurva quadratic di tt dan tt+0.5
                axx = x0 + (x1 - x0) * tt
                ayy = y0 + (y1 - y0) * tt
                bxx = x1 + (x2 - x1) * tt
                byy = y1 + (y2 - y1) * tt
                nxx, nyy = axx + (bxx - axx) * .5, ayy + (byy - ayy) * .5
                tt2 = tt + 0.5
                ax2 = x0 + (x1 - x0) * tt2
                ay2 = y0 + (y1 - y0) * tt2
                bx3 = x1 + (x2 - x1) * tt2
                by3 = y1 + (y2 - y1) * tt2
                nx2, ny2 = ax2 + (bx3 - ax2) * .5, ay2 + (by3 - ay2) * .5
                w0 = wid * (1.0 - tt * 0.5)
                w1 = max(1.6, wid * (1.0 - tt2 * 0.5))
                dx_ = nx2 - nxx
                dy_ = ny2 - nyy
                dl = math.hypot(dx_, dy_) or 1.0
                nx_, ny_ = -dy_ / dl, dx_ / dl
                _NS_thorne._poly(surface, p["shadow_deep"], [
                    pt(nxx + nx_ * w0 + f, nyy + ny_ * w0 + 1),
                    pt(nxx - nx_ * w0 + f, nyy - ny_ * w0 + 1),
                    pt(nx2 - nx_ * w1 + f, ny2 - ny_ * w1 + 1),
                    pt(nx2 + nx_ * w1 + f, ny2 + ny_ * w1 + 1)])
                _NS_thorne._poly(surface, p["tusk_dark"], [
                    pt(nxx + nx_ * w0, nyy + ny_ * w0),
                    pt(nxx - nx_ * w0, nyy - ny_ * w0),
                    pt(nx2 - nx_ * w1, ny2 - ny_ * w1),
                    pt(nx2 + nx_ * w1, ny2 + ny_ * w1)])
                _NS_thorne._poly(surface, p["tusk_mid"], [
                    pt(nxx + nx_ * w0 * .55, nyy + ny_ * w0 * .55),
                    pt(nxx - nx_ * w0 * .3, nyy - ny_ * w0 * .3),
                    pt(nx2 - nx_ * w1 * .3, ny2 - ny_ * w1 * .3),
                    pt(nx2 + nx_ * w1 * .55, ny2 + ny_ * w1 * .55)])
                _NS_thorne._aaline(surface, p["tusk_light"],
                                   pt(nxx - nx_ * w0 * .45, nyy - ny_ * w0 * .45),
                                   pt(nx2 - nx_ * w1 * .45, ny2 - ny_ * w1 * .45), 1)
            _NS_thorne._aacircle(surface, p["tusk_light"], pt(x2, y2), 2)
            _NS_thorne._aacircle(surface, p["snout_dark"], pt(bx, by + 1), 2)
        # wart pipi (ciri khas boar)
        _NS_thorne._aacircle(surface, p["snout_dark"], pt(9, -32), 2)
        _NS_thorne._aacircle(surface, p["snout_dark"], pt(5, -30), 1)

        # ═══ 14. CREST MAHKOTA pendek di kepala ═══
        front = ((4, -52, -1.30, 18, 4), (0, -54, -1.55, 21, 4),
                 (-4, -54, -1.80, 21, 4), (-8, -52, -2.05, 19, 4))
        for i, (rx, ry, ang, ln, wd) in enumerate(front):
            _NS_thorne._draw_elite_quill(
                surface, *pt(rx, ry), qa(ang + crest_tilt * .5), ln * flare, wd,
                f_root, f_mid, f_light, c_tip, wave=wave * .02)

        # ═══ 15. LENGAN DEPAN + MACE ═══
        hand = pose["hand"]
        angle = pose["angle"]
        elbow = ((hand[0] + 12) // 2 + 3, (hand[1] - 16) // 2 + 4)
        limb((8, -24), elbow, 13, p["fur_dark"], p["fur_high"])
        limb(elbow, hand, 11, p["fur_mid"], p["fur_light"])
        hx2, hy2 = pt(*hand)
        _NS_thorne._aacircle(surface, p["fur_darkest"], (hx2, hy2), 8)
        _NS_thorne._aacircle(surface, p["fur_mid"], (hx2 - 1, hy2 - 1), 6)
        _NS_thorne._aacircle(surface, p["fur_high"], (hx2 - 2, hy2 - 3), 3)
        for c in (-4, 0, 4):
            _NS_thorne._aacircle(surface, p["fur_light"], (hx2 + c, hy2 - 5), 2)
        _NS_thorne._poly(surface, p["tusk_mid"],
                         [(hx2 + 2, hy2 - 7), (hx2 + 6, hy2 - 6), (hx2 + 5, hy2 - 2)])
        _NS_thorne._aaline(surface, p["cloth_dark"], (hx2 - 6, hy2 - 1), (hx2 - 1, hy2 - 2), 4)
        _NS_thorne._aaline(surface, p["cloth_mid"], (hx2 - 6, hy2 - 2), (hx2 - 1, hy2 - 3), 2)

        # smear ayunan (digambar sebelum mace agar tertimpa kepala mace)
        if attack and .30 < ap < .80:
            t = max(0.0, min(1.0, (ap - .30) / .5))
            _NS_thorne._draw_club_swing_trail(surface, *pt(8, -24), f, angle,
                                              t * .8)
        _NS_thorne._draw_elite_club(surface, cx + off_x, cy + root_y, f,
                                    hand, angle, phase, attack, warpath)

        # ═══ 16. FX: impact star / shockwave / serpihan / mote ═══
        if attack and .46 < ap < .66:
            t = max(0.0, min(1.0, (ap - .46) / .2))
            A = angle if f > 0 else math.pi - angle
            ix = cx + off_x + f * hand[0] + math.cos(A) * 44
            iy = cy + root_y + hand[1] + math.sin(A) * 44
            fade = int(230 * (1 - t))
            for k in range(6):
                ang = k * math.pi / 3 + 0.4
                ln = (10 + (k % 2) * 8) * (1 - t * .5)
                _NS_thorne._aaline(surface,
                                   (*p["quill_shine"], fade), (int(ix), int(iy)),
                                   (int(ix + math.cos(ang) * ln),
                                    int(iy + math.sin(ang) * ln * .8)),
                                   2 if k % 2 == 0 else 1)
            _NS_thorne._aacircle(surface, (*p["white"], fade), (int(ix), int(iy)),
                                 max(1, int(5 * (1 - t))))
            r = int(14 + t * 34)
            _NS_thorne._ellipse(surface, (*p["quill_mid"], int(150 * (1 - t))),
                                (int(ix - r), int(cy + root_y + 58 - r // 3),
                                 r * 2, r * 2 // 3), 3)
            for k in range(5):
                ang = -2.6 + k * 0.5
                d0 = 12 + t * (28 + k * 6)
                cxx = ix + math.cos(ang) * d0
                cyy = iy + math.sin(ang) * d0 + t * t * 26
                _NS_thorne._aacircle(surface, p["fur_darkest"],
                                     (int(cxx), int(cyy)), 2)
                _NS_thorne._aacircle(surface, p["fur_dark"],
                                     (int(cxx) - 1, int(cyy) - 1), 1)
        elif walk:
            # debu belakang kaki
            for i in range(3):
                t = (phase * .2 + i / 3.0) % 1.0
                mx = cx + off_x - f * (30 + i * 9) - int(t * 10)
                my = cy + root_y + 56 - int(t * 16)
                _NS_thorne._aacircle(surface, (*p["fur_high"], int(100 * (1 - t))),
                                     (mx, my), 1)
        else:
            # mote bulu melayang (idle)
            for i in range(3):
                t = (phase * .16 + i / 3.0) % 1.0
                mx = cx + off_x + int(math.sin(phase + i * 2.1) * (24 + i * 4))
                my = cy + root_y + 30 - int(t * 74)
                _NS_thorne._aacircle(surface, (*p["fur_high"], int(110 * (1 - t))),
                                     (mx, my), 1)
            # dengusan napas dari moncong
            if 4.1 < (phase % 6.283) < 4.8:
                gx, gy = pt(44, -36)
                _NS_thorne._aacircle(surface, (*p["fur_light"], 110), (gx + 2, gy), 2)
                _NS_thorne._aacircle(surface, (*p["fur_light"], 70), (gx + 6, gy - 2), 1)

        # ═══ 17. WARPATH: bara mengorbit + rembes di ujung quill ═══
        if warpath and not detail:
            for i in range(7):
                a2 = phase * .7 + i * math.pi * 2 / 7
                r = 42 + int(math.sin(phase * 1.3 + i) * 7)
                ox = cx + off_x + int(math.cos(a2) * r)
                oy = cy + root_y - 12 + int(math.sin(a2) * r * .5)
                _NS_thorne._aacircle(surface, (*p["rage_bright"], 150), (ox, oy), 2)
                _NS_thorne._aacircle(surface, (*p["quill_shine"], 90), (ox, oy), 1)
            for i in range(3):
                t = (phase * .3 + i / 3.0) % 1.0
                ex2 = cx + off_x - f * (10 + i * 9)
                ey2 = cy + root_y - 66 + int(t * 56)
                _NS_thorne._aacircle(surface, (*p["rage_light"], int(160 * (1 - t))),
                                     (ex2, ey2), 2)

        if detail:
            _NS_thorne._draw_thorne_masterwork_details(surface, pt, f)


    def _draw_club_swing_trail(surface, cx, cy, facing, current_angle, t):
        """Smear ayunan mace: sabit 3 band + leading edge terang.

        Hanya aktif saat ayunan turun (sudut > -1.2 rad); lengkung
        dimulai dari pose wind-up (-2.7 rad) sampai sudut sekarang.
        """
        if current_angle < -1.2:
            return
        fade = int(190 * (1 - t * 0.8))
        if fade < 25:
            return
        _NS_thorne._draw_arc_pair(surface, cx, cy, 30, 62,
                                  -2.7, current_angle, facing, fade)


    def _draw_arc_pair(surface, cx, cy, inner_r, outer_r, a_start, a_end,
                       facing, fade):
        """Sabit smear ter-taper 3 band + inti terang + leading edge."""
        p = _NS_thorne.PALETTE
        segments = 14
        if facing < 0:
            a_start, a_end = math.pi - a_start, math.pi - a_end

        def ring(r0, r1, color, taper=False):
            pts = []
            for i in range(segments + 1):
                tt = i / segments
                ang = a_start + (a_end - a_start) * tt
                rw = r1 if not taper else r0 + (r1 - r0) * (1 - tt)
                pts.append((cx + math.cos(ang) * rw,
                            cy + math.sin(ang) * rw))
            for i in range(segments, -1, -1):
                tt = i / segments
                ang = a_start + (a_end - a_start) * tt
                rw = r0 if not taper else r0 * (1 - tt * .6)
                pts.append((cx + math.cos(ang) * rw,
                            cy + math.sin(ang) * rw))
            _NS_thorne._poly(surface, color, pts)

        ring(inner_r, outer_r, (*p["quill_dark"], int(fade * .45)), taper=True)
        ring(inner_r + 10, outer_r - 4, (*p["quill_mid"], int(fade * .7)))
        ring(inner_r + 18, outer_r - 12, (*p["quill_light"], max(20, fade - 70)))
        # inti terang mengikuti radius tengah
        r_core = (inner_r + outer_r) * 0.5
        for i in range(segments):
            ang = a_start + (a_end - a_start) * ((i + 0.5) / segments)
            _NS_thorne._aacircle(surface, (*p["quill_shine"], fade),
                                 (int(cx + math.cos(ang) * r_core),
                                  int(cy + math.sin(ang) * r_core)), 1)
        # leading edge paling terang di sudut sekarang
        lx, ly = math.cos(a_end), math.sin(a_end)
        _NS_thorne._aaline(surface, (*p["quill_shine"], min(255, fade + 40)),
                           (int(cx + lx * (inner_r + 4)), int(cy + ly * (inner_r + 4))),
                           (int(cx + lx * (outer_r - 2)), int(cy + ly * (outer_r - 2))), 2)



    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_dust(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False, warpath=False):
        """Debu / kabut bulu di kaki Thorne (versi rig v2)."""
        strength = 1.5 if intense else 1.0
        dust_color = _NS_thorne.PALETTE["rage_dark"] if warpath else _NS_thorne.PALETTE["fur_dark"]
        base = _NS_thorne.PALETTE["rage_light"] if warpath else _NS_thorne.PALETTE["fur_mid"]

        def build_mist():
            mist = pygame.Surface((170, 52), pygame.SRCALPHA)
            for radius in range(42, 4, -5):
                alpha = int((42 - radius) * 2.6)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*dust_color, min(255, alpha)),
                        (85 - radius * 2, 26 - radius // 3,
                         radius * 4, max(4, radius // 2)))
            return mist
        mist = _NS_thorne._static(("mist", dust_color), build_mist)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        if pulse < .9:
            faded = mist.copy()
            faded.set_alpha(int(255 * pulse))
            surface.blit(faded, (cx - 85, cy - 16))
        else:
            surface.blit(mist, (cx - 85, cy - 16))

        # Rising dust wisps
        for i, offset in enumerate((-32, -12, 12, 32)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 4)
            sy = cy + 6 - int(t * 26)
            alpha = max(0, min(255, int(180 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_thorne._aacircle(surface, (*base, alpha), (sx, sy), 5)
            _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["fur_high"], alpha), (sx, sy - 2), 3)

        # Loose quills orbiting
        for i in range(3):
            angle = phase * 0.9 + i * math.pi * 2 / 3
            r = 33 + int(math.sin(phase + i * 1.3) * 7)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_thorne._draw_quill(surface, sx, sy, 7, angle, thickness=2)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 15 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 120 - i * 22)
                _NS_thorne._aacircle(surface, (*_NS_thorne.PALETTE["fur_mid"], alpha),
                          (sx, sy), max(2, 6 - i))


    def _draw_shadow(surface, x, y):
        """Bayangan tanah (cached - dibangun sekali)."""
        def build():
            shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
            for radius in range(14, 0, -1):
                alpha = max(0, (14 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (14 - radius, 15 - radius, 122 + radius * 2, radius * 2))
            pygame.draw.ellipse(
                shadow, (*_NS_thorne.PALETTE["fur_darkest"], 55),
                (10, 6, 130, 14))
            return shadow
        surface.blit(_NS_thorne._static("shadow", build), (x - 75, y - 15))


    def _draw_dust_aura(surface, x, y, phase):
        """Aura debu cokelat besar (background, cached)."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75

        def build():
            aura = pygame.Surface((260, 230), pygame.SRCALPHA)
            for radius in range(100, 6, -5):
                alpha = int((100 - radius) * 1.0)
                if alpha > 0:
                    _NS_thorne._aacircle(
                        aura, (*_NS_thorne.PALETTE["fur_darkest"], min(255, alpha)),
                        (130, 115), radius)
            return aura
        aura = _NS_thorne._static("dust_aura", build)
        if pulse < .9:
            faded = aura.copy()
            faded.set_alpha(int(255 * pulse))
            surface.blit(faded, (x - 130, y - 115))
        else:
            surface.blit(aura, (x - 130, y - 115))


    def _draw_rage_aura(surface, x, y, phase):
        """Aura rage merah saat warpath (cached)."""
        pulse = math.sin(phase * 0.8) * 0.3 + 0.7

        def build():
            aura = pygame.Surface((300, 270), pygame.SRCALPHA)
            for radius in range(115, 6, -5):
                alpha = int((115 - radius) * 1.4)
                if alpha > 0:
                    _NS_thorne._aacircle(
                        aura, (*_NS_thorne.PALETTE["rage_dark"], min(255, alpha)),
                        (150, 135), radius)
            return aura
        aura = _NS_thorne._static("rage_aura", build)
        faded = aura.copy()
        faded.set_alpha(int(255 * pulse))
        surface.blit(faded, (x - 150, y - 135))


    def _draw_ground_platform(surface, x, y, phase, skill):
        """Cincin tanah + quill kecil tertanam (versi rig v2)."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75

        def build():
            ring = pygame.Surface((195, 62), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*_NS_thorne.PALETTE["fur_darkest"], 185),
                                (8, 15, 179, 34), 3)
            pygame.draw.ellipse(ring, (*_NS_thorne.PALETTE["fur_dark"], 205),
                                (30, 20, 135, 24), 2)
            return ring
        ring = _NS_thorne._static("platform", build)
        surface.blit(ring, (x - 97, y - 31))

        # Small quills embedded around ring
        for i in range(5):
            angle = phase * 0.2 + i * math.pi / 5
            sx = x + int(math.cos(angle) * 82)
            sy = y + int(math.sin(angle) * 15)
            _NS_thorne._draw_quill(surface, sx, sy, 7,
                        angle + math.pi / 2, thickness=1)

        if skill:
            color = _NS_thorne.PALETTE["rage_light"] if skill == "r" else _NS_thorne.PALETTE["quill_light"]
            pygame.draw.ellipse(surface, (*color, int(130 * pulse)),
                                (x - 88, y - 26, 176, 52), 2)


    # ===================================================================
    # SKILL FX PRIMITIVES (pass mewah v2.1)
    # ------------------------------------------------------------------
    def _fx_scale(boss):
        """Faktor skala efek skill.

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek (cincin, retakan, duri) ikut menyusut sampai
        ~40%. Dengan faktor ini efek digambar lebih besar di canvas
        sehingga ukurannya DI LAYAR setara boss asli (world-space).
        Boss asli (tanpa _render_scale) = 1.0.
        """
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))


    def _spark_star(surface, cx, cy, size, color, alpha, spikes=2, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_thorne._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_thorne._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))


    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_thorne._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)


    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=5, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_thorne._aaline(surface, (*color, alpha), p0, p1, thick)


    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_thorne._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55      # perspektif tanah
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_thorne._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_thorne._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)


    # ===================================================================
    # SKILL Q: VISCOUS NOSE
    # ===================================================================
    def _draw_viscous_ground(surface, boss, x, y, timer, phase):
        """Jalur asam mewah: band lebar 2-lapis, gelembung bergerak,
        chevron berbaris ke target, dan splat marker di ujung."""
        p = _NS_thorne.PALETTE
        tx, ty = _NS_thorne._target_position(boss, x, y)
        pulse = math.sin(phase * 5) * .5 + .5

        # band asam lebar (fade in-out di sepanjang jalur)
        steps = 16
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            a0 = (x + (tx - x) * t0, y + (ty - y) * t0 + 6)
            a1 = (x + (tx - x) * t1, y + (ty - y) * t1 + 6)
            fade = int(95 + 70 * math.sin(t0 * math.pi))
            _skill_outlined_line(surface, a0, a1, 8,
                                 p["goo_mid"], fade)
        # gelembung asam naik-turun sepanjang jalur
        for i in range(6):
            t = (i / 6 + phase * .22) % 1.0
            bx = x + (tx - x) * t
            by = y + (ty - y) * t + 6
            r = 2 + int(2 * math.sin(phase * 6 + i) ** 2)
            _NS_thorne._aacircle(surface, (*p["goo_dark"], 150), (int(bx), int(by)), r + 1)
            _NS_thorne._aacircle(surface, (*p["goo_bright"], 170), (int(bx), int(by)), max(1, r - 1))
        # chevron berbaris menuju target
        ang = math.atan2(ty - y, tx - x)
        for i in range(4):
            t = (i / 4 + phase * .35) % 1.0
            _NS_thorne._chevron(surface,
                                x + (tx - x) * t, y + (ty - y) * t + 6,
                                ang, 14, p["goo_bright"], 210, 3)
        # splat marker di target: 2 cincin + crosshair
        _skill_outlined_circle(surface, (tx, ty + 6), 27, 3, p["goo_light"],
                               int(140 + 60 * pulse))
        _skill_outlined_circle(surface, (tx, ty + 6), 15, 2, p["goo_bright"],
                               int(170 + 60 * pulse))
        for da in (0, math.pi / 2, math.pi, -math.pi / 2):
            _NS_thorne._aaline(
                surface, (*p["goo_light"], 160),
                (int(tx + math.cos(da) * 9), int(ty + 6 + math.sin(da) * 6)),
                (int(tx + math.cos(da) * 23), int(ty + 6 + math.sin(da) * 12)), 2)


    def _draw_viscous_charge(surface, boss, x, y, timer, phase):
        """Charge goo di moncong: vortex 2 arc berlawanan + droplet orbit
        + core 3-band; spit: bintang + ring + kipasan droplet."""
        p = _NS_thorne.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 40))
        facing = boss.direction
        snout_x = x + 40 * facing
        snout_y = y - 36

        if progress < 0.4:
            # Charging up: vortex
            t = progress / 0.4
            radius = int(4 + t * 9)
            pulse = math.sin(phase * 5) * .25 + .75
            _NS_thorne._dashed_ring(surface, snout_x, snout_y, radius + 7,
                                    p["goo_mid"], int(190 * pulse),
                                    -phase * 2.4, segments=3, thick=2, span=.5)
            _NS_thorne._dashed_ring(surface, snout_x, snout_y, radius + 12,
                                    p["goo_light"], int(120 * pulse),
                                    phase * 1.7, segments=4, thick=1, span=.45)
            _NS_thorne._aacircle(surface, (*p["goo_dark"], int(210 * pulse)),
                      (snout_x, snout_y), radius + 3)
            _NS_thorne._aacircle(surface, (*p["goo_mid"], int(230 * pulse)),
                      (snout_x, snout_y), radius)
            _NS_thorne._aacircle(surface, (*p["goo_bright"], int(240 * pulse)),
                      (snout_x - 1, snout_y - 1), max(1, radius // 2))
            # droplet orbit cepat
            for i in range(4):
                a = phase * 3.2 + i * math.pi / 2
                dr = radius + 6
                _NS_thorne._aacircle(surface, (*p["goo_light"], 200),
                                     (int(snout_x + math.cos(a) * dr),
                                      int(snout_y + math.sin(a) * dr * .7)), 2)
            # Drip below
            _NS_thorne._aacircle(surface, p["goo_mid"],
                      (snout_x, snout_y + radius + 3), 2)

        elif progress < 0.5:
            # Spit! Spawn projectile once
            if not getattr(boss, "_th_goo_spawned", False):
                _NS_thorne._spawn_goo(boss, x, y)
                boss._th_goo_spawned = True
            # Muzzle burst: bintang + ring + kipasan droplet
            _NS_thorne._spark_star(surface, snout_x, snout_y, 17,
                                   p["goo_bright"], 235, 6, rot=phase)
            _NS_thorne._aacircle(surface, (*p["goo_light"], 210), (snout_x, snout_y), 9)
            _NS_thorne._aacircle(surface, (*p["goo_mid"], 160), (snout_x, snout_y), 14, 2)
            for i in range(7):
                a = -1.1 + i * .34
                dx = math.cos(a) * (12 + i % 2 * 5) * facing
                dy = math.sin(a) * 10
                _NS_thorne._aacircle(surface, (*p["goo_light"], 220),
                                     (int(snout_x + dx), int(snout_y + dy)), 2)
        else:
            boss._th_goo_spawned = False


    # ===================================================================
    # SKILL W: BRISTLEBACK (defensive spike aura)
    # ===================================================================
    def _draw_bristleback_effect(surface, boss, x, y, timer, phase):
        """BRISTLEBACK mewah: aura dasar + rune ring ganda berlawanan,
        shockwave aktivasi, duri 2 baris (luar panjang + dalam pendek),
        kubah shimmer, mote emas naik, glint orbit."""
        p = _NS_thorne.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2.4) * .5 + .5
        fs = _NS_thorne._fx_scale(boss)
        cx, cy = x, y - 16
        gy = y + 30

        # ── aura dasar (cached) paling belakang ──
        def build():
            aura = pygame.Surface((180, 180), pygame.SRCALPHA)
            for radius in range(74, 14, -4):
                alpha = int((74 - radius) * 3)
                pygame.draw.circle(aura, (*p["quill_shine"], min(255, alpha)),
                                   (90, 90), radius, 2)
            return aura
        aura = _NS_thorne._static("bristle_aura", build)
        faded = aura.copy()
        faded.set_alpha(int(160 + 60 * pulse))
        surface.blit(faded, (x - 90, y - 90))

        # glow lantai emas
        _NS_thorne._ellipse(surface, (*p["gold_dark"], int(70 + 40 * pulse)),
                            (int(cx - 80 * fs), int(gy - 12),
                             int(160 * fs), 26), 0)

        # ── rune ring ganda, berputar berlawanan arah ──
        _NS_thorne._dashed_ring(surface, cx, cy, int(78 * fs), p["gold_mid"],
                                int(120 + 60 * pulse), phase * .8,
                                segments=10, thick=3, span=.58)
        _NS_thorne._dashed_ring(surface, cx, cy, int(62 * fs), p["quill_shine"],
                                int(90 + 50 * pulse), -phase * 1.1 + .3,
                                segments=8, thick=2, span=.5)

        # ── duri 2 baris berdenyut (luar 18 panjang, dalam 12 pendek) ──
        for ri, (n, base_r, tip_r0, wdt) in enumerate((
                (18, int(48 * fs), int(66 * fs), 4),
                (12, int(34 * fs), int(47 * fs), 3))):
            ro = 0.0 if ri == 0 else math.pi / n
            for i in range(n):
                ang = ro + i * math.pi * 2 / n + \
                    phase * (0.25 if ri == 0 else -0.35)
                tip_r = tip_r0 + int(math.sin(phase * 3 + i * 1.7 + ri) * 4 * fs)
                bx = cx + math.cos(ang) * base_r
                by = cy + math.sin(ang) * base_r * .72
                tx = cx + math.cos(ang) * tip_r
                ty = cy + math.sin(ang) * tip_r * .72
                _NS_thorne._aaline(surface, p["gold_dark"], (bx, by), (tx, ty), wdt + 2)
                _NS_thorne._aaline(surface, p["quill_mid"], (bx, by), (tx, ty), wdt)
                _NS_thorne._aaline(surface, p["quill_light"],
                                   (bx, by),
                                   (tx - (tx - bx) * .25, ty - (ty - by) * .25),
                                   max(1, wdt - 2))
                _NS_thorne._aacircle(surface, p["quill_shine"], (int(tx), int(ty)), 2)
                if (i + ri) % 3 == 0:
                    _NS_thorne._aacircle(surface, p["white"], (int(tx), int(ty)), 1)

        # ── kubah shimmer: 2 arc atas berkelip ──
        for k, rr in enumerate((int(58 * fs), int(50 * fs))):
            a0, a1 = math.pi * 1.08 + k * .1, math.pi * 1.92 - k * .1
            steps = 10
            for j in range(steps):
                aa0 = a0 + (a1 - a0) * j / steps
                aa1 = a0 + (a1 - a0) * (j + 1) / steps
                flick = .5 + .5 * math.sin(phase * 6 + j * 1.3 + k * 2)
                _NS_thorne._aaline(
                    surface, (*p["quill_shine"], int(90 + 70 * flick)),
                    (cx + math.cos(aa0) * rr, cy + math.sin(aa0) * rr * .9),
                    (cx + math.cos(aa1) * rr, cy + math.sin(aa1) * rr * .9), 2)

        # ── mote emas naik + glint orbit ──
        for i in range(4):
            t = (phase * .32 + i / 8) % 1.0
            mx = cx + math.sin(i * 2.4) * 60 * fs
            my = cy + 30 - t * 90 * fs
            _NS_thorne._aacircle(surface, (*p["gold_light"], int(190 * (1 - t))),
                                 (int(mx), int(my)), 2 if i % 2 else 1)
        for i in range(5):
            a = phase * 1.6 + i * math.pi * 2 / 5
            gr = 70 * fs + math.sin(phase * 2 + i) * 6
            _NS_thorne._aacircle(surface, (*p["white"], 200),
                                 (int(cx + math.cos(a) * gr),
                                  int(cy + math.sin(a) * gr * .6)), 1)

        # ── aktivasi: shockwave ganda + bintang ──
        if progress < 0.22:
            t = progress / 0.22
            for k, rmax in ((0, 90), (1, 66)):
                r = int((20 + t * rmax) * fs)
                alpha = int((230 if k == 0 else 160) * (1 - t))
                _skill_outlined_circle(
                    surface, (cx, cy), r, 3,
                    p["quill_shine"] if k == 0 else p["gold_light"], alpha)
            _NS_thorne._spark_star(surface, cx, cy, int(26 * (1 - t * .5)),
                                   p["quill_shine"], int(240 * (1 - t)),
                                   8, rot=phase, core=p["white"])


    # ===================================================================
    # SKILL E: QUILL SPRAY
    # ===================================================================
    def _draw_quill_spray_ground(surface, boss, x, y, timer, phase):
        """Telegraph Quill Spray mewah: ring jangkauan + tick berputar +
        ring KONVERGEN mengecil ke pusat + chevron kardinal + orb."""
        p = _NS_thorne.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 60))
        pulse = math.sin(phase * 4.5) * .5 + .5
        # Radius gameplay dikonversi ke px canvas lewat _render_scale
        # (hero) supaya telegraph pas dengan jangkauan asli.
        scale = getattr(boss, "_render_scale", None)
        rng = 100 / float(scale) if scale else 100.0

        # ring jangkauan utama (outline tebal)
        _skill_outlined_circle(surface, (x, y), int(rng), 4,
                               p["quill_shine"], int(110 + 50 * pulse))
        # tick ring berputar di dalamnya
        _NS_thorne._dashed_ring(surface, x, y, int(rng * .9), p["quill_light"],
                                int(130 + 60 * pulse), phase * 1.1,
                                segments=12, thick=3, span=.3)
        # ring konvergen: mengecil ke pusat saat mendekati tembakan
        conv = rng * (1 - progress * .82)
        _skill_outlined_circle(surface, (x, y), max(12, int(conv)), 3,
                               p["quill_shine"], int(160 + 70 * pulse))
        # chevron kardinal menunjuk ke dalam
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _NS_thorne._chevron(
                surface,
                x + math.cos(da) * rng * .62,
                y + math.sin(da) * rng * .55,
                da + math.pi, max(8, int(rng * .1)), p["quill_light"], 190, 3)
        # orb pusat berdenyut + crosshair kecil
        _NS_thorne._aacircle(surface, (*p["quill_shine"], int(200 + 40 * pulse)),
                             (x, y), int(5 + 3 * pulse))
        for da in (0, math.pi / 2):
            _NS_thorne._aaline(surface, (*p["quill_light"], 150),
                               (x - math.cos(da) * 12, y - math.sin(da) * 8),
                               (x + math.cos(da) * 12, y + math.sin(da) * 8), 1)


    def _handle_quill_spray_skill(surface, boss, x, y, timer, phase):
        """Rentetan quill: streak konvergen saat menyiap, muzzle star +
        ring di punggung setiap voli, glow + dashed ring selang-seling."""
        p = _NS_thorne.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 60))
        fs = _NS_thorne._fx_scale(boss)
        facing = getattr(boss, "direction", 1)
        backx = x - 16 * facing
        backy = y - 34

        if not hasattr(boss, "_th_spray_last"):
            boss._th_spray_last = -100
        fired = (0.3 < progress < 0.9 and timer % 6 == 0
                 and boss._th_spray_last != timer)
        if fired:
            _NS_thorne._spawn_quill_spray(boss, x, y)
            boss._th_spray_last = timer
            # muzzle burst di punggung
            _NS_thorne._spark_star(surface, backx, backy, int(15 * fs),
                                   p["quill_shine"], 235, 7, rot=phase)
            _skill_outlined_circle(surface, (backx, backy), int(22 * fs), 2,
                                   p["quill_light"], 180)
        if progress < 0.2:
            boss._th_spray_last = -100

        # persiapan: streak konvergen ke punggung + glow denyut
        if progress < 0.35:
            pulse = math.sin(phase * 5) * .5 + .5
            for i in range(6):
                a = i * math.pi * 2 / 6 + phase * .9
                r0 = int((40 + 14 * pulse) * fs)
                r1 = int(16 * fs)
                _NS_thorne._aaline(
                    surface, (*p["quill_light"], 120),
                    (backx + math.cos(a) * r0, backy + math.sin(a) * r0 * .7),
                    (backx + math.cos(a) * r1, backy + math.sin(a) * r1 * .7), 2)
            _NS_thorne._aacircle(surface, (*p["quill_shine"], int(160 * pulse)),
                                 (backx, backy), int((20 + 8 * pulse) * fs), 2)

        # selama rentetan: body glow + dashed ring berlawanan jarum jam
        if 0.3 < progress < 0.9:
            alpha = int(150 + math.sin(phase * 5) * 60)
            alpha = max(0, min(255, alpha))
            _NS_thorne._aacircle(surface, (*p["quill_light"], alpha),
                                 (x, y - 20), int(44 * fs), 3)
            _NS_thorne._dashed_ring(surface, x, y - 20, int(56 * fs),
                                    p["quill_shine"], 140, -phase * 2.2,
                                    segments=8, thick=2, span=.4)


    # ===================================================================
    # SKILL R: WARPATH (self-buff with rage aura)
    # ===================================================================
    def _draw_warpath_effect(surface, boss, x, y, timer, phase):
        """WARPATH ultimate mewah: aktivasi pilar cahaya + shockwave ganda,
        retakan magma radial, cincin aura 3-lapis, mahkota api 2-ring,
        kolom bara, wisp spiral, dan denyut pusat."""
        p = _NS_thorne.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 120))
        pulse = math.sin(phase * 3) * .5 + .5
        fs = _NS_thorne._fx_scale(boss)
        cx, cy = x, y - 16
        gy = y + 42

        # ── AKTIVASI: shockwave ganda + bintang (TANPA pilar cahaya) ──
        # Pilar cahaya 4-lapis setinggi 100 px di (cx, cy) DIBUANG:
        # kolom itu menutupi badan Thorne selama Warpath di-cast.
        if progress < 0.18:
            t = progress / 0.18
            for k, rmax in ((0, 120), (1, 86)):
                r = int((16 + t * rmax) * fs)
                _skill_outlined_circle(
                    surface, (cx, cy), r, 3,
                    p["rage_bright"] if k == 0 else p["quill_shine"],
                    int((220 if k == 0 else 150) * (1 - t)))
            _NS_thorne._spark_star(surface, cx, cy, int(30 * (1 - t * .4)),
                                   p["quill_shine"], int(235 * (1 - t)),
                                   8, rot=.3, core=p["white"])

        # ── retakan magma radial (7 crack zigzag + seam inti terang) ──
        for i in range(7):
            ang = i * math.pi * 2 / 7 + .35
            _NS_thorne._jagged_crack(surface, cx, gy, ang,
                                     int((46 + (i % 3) * 14) * fs),
                                     (p["rage_dark"], p["rage_mid"]), 140,
                                     seed=i + 3, width=3)
        seam = int(120 + 110 * pulse)
        for i in range(0, 7, 3):
            ang = i * math.pi * 2 / 7 + .35
            _NS_thorne._jagged_crack(surface, cx, gy, ang,
                                     int((30 + (i % 3) * 12) * fs),
                                     (p["rage_mid"], p["rage_bright"]), seam,
                                     seed=i + 3, width=1)
        # glow lantai hangat
        _NS_thorne._ellipse(surface, (*p["rage_dark"], 95),
                            (int(cx - 90 * fs), int(gy - 12),
                             int(180 * fs), 24), 0)

        # ── cincin aura 3-lapis + ring emas kontras ──
        for r in range(3):
            radius = int((44 + r * 12 + math.sin(phase * 2 + r) * 5) * fs)
            alpha = int((160 - r * 40) * (0.7 + 0.3 * pulse))
            if alpha > 0:
                _NS_thorne._aacircle(surface, (*p["rage_light"], alpha),
                                     (cx, cy), radius, 2)
        _NS_thorne._aacircle(surface, (*p["quill_shine"], int(60 + 40 * pulse)),
                             (cx, cy), int(34 * fs), 2)

        # ── mahkota api 2 ring (10 api luar + 7 api dalam, core emas) ──
        for ring_i, (n, r0, scale_flame) in enumerate(((10, 44, 1.0), (7, 30, .72))):
            for i in range(n):
                ang = i * math.pi * 2 / n + phase * (.5 if ring_i else .8)
                r = r0 * fs
                px = cx + math.cos(ang) * r
                py = cy + math.sin(ang) * r * .68
                for h in range(3):
                    fy = py - h * 7 - int((phase * 26 + i * 3) % 20)
                    alpha = int(210 * (1 - h / 3))
                    rad = max(1, int((4 - h) * scale_flame))
                    _NS_thorne._aacircle(surface, (*p["rage_bright"], alpha),
                                         (int(px), int(fy)), rad)
                    _NS_thorne._aacircle(surface, (*p["quill_shine"], alpha),
                                         (int(px), int(fy)), max(1, 2 - h // 2))

        # ── kolom bara naik (sway per-ember) ──
        for i in range(4):
            t = (phase * .3 + i / 8) % 1.0
            ex = cx + math.sin(i * 2.1 + phase) * (14 + i * 5) * fs * .5
            ey = cy + 24 - t * 110 * fs
            _NS_thorne._aacircle(surface, (*p["rage_bright"], int(200 * (1 - t))),
                                 (int(ex), int(ey)), 2 if i % 2 else 1)

        # ── wisp spiral 2 lengan ──
        for arm in range(2):
            for j in range(9):
                a = phase * 2.2 + arm * math.pi + j * .38
                rr = (16 + j * 5) * fs
                al = int(150 * (1 - j / 9))
                _NS_thorne._aacircle(surface, (*p["rage_light"], al),
                                     (int(cx + math.cos(a) * rr),
                                      int(cy + math.sin(a) * rr * .55)), 2)

        # ── denyut pusat ──
        _NS_thorne._aacircle(surface, (*p["rage_bright"], int(180 * pulse)),
                             (cx, cy), int((20 + 5 * pulse) * fs))
        _NS_thorne._aacircle(surface, (*p["quill_shine"], int(220 * pulse)),
                             (cx, cy), int((9 + 3 * pulse) * fs))


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_thorne.draw_thorne(surface, boss, x, y)# ====================================================================
# vex.py
# ====================================================================
class _NS_vex:
    """Namespace vex - PIXEL MASTERWORK v2 + Skill FX v3.0.

    Rewrite visual Vex mengikuti standar Thorne v2 / v2.1: tetap
    100% prosedural (tanpa PNG, sprite-sheet, atau ``image.load``),
    rig native ~1.5× lebih besar lalu dinormalisasi pipeline hero,
    ramp material 4-5 band dengan hue-shift, selout, dither band,
    specular cluster, animasi pose-driven, dan skill FX world-space
    memakai kompensasi ``1/_render_scale`` supaya telegraph/ring tidak
    ikut mengecil bersama sprite cache.
    """

    # ---------------------------------------------------------------------------
    # LAPISAN FX HIDUP (heroes/vex_fx.py)
    # ---------------------------------------------------------------------------
    # Sprite Vex DI-CACHE oleh pipeline hero.  Semua yang harus bergerak
    # 60 fps sejati - arc ayunan staff, partikel void, proyektil serpihan,
    # spike crystal W, kurungan astral E, ledakan Essence Flux R, impact,
    # shake, hit-stop - karena itu TIDAK boleh hidup di dalam canvas:
    # hasilnya ikut beku pada kuantisasi pose dan menyusut bersama sprite.
    #
    # Modul ``heroes/vex_fx.py`` adalah lapisan hidupnya: digambar langsung
    # ke layar pada skala 1:1.  Jembatan di bawah memasang director per
    # unit dan memberi tahu rig bahwa smear ayunan di-canvas sudah
    # digantikan, sehingga tidak ada efek yang tergambar dua kali.
    #
    # Jalur HERO lane menggambar lapisannya lewat heroes/__init__.py
    # (``_LIVE_FX_HEROES``); jalur BOSS (draw dipanggil tiap frame, tidak
    # lewat cache) menggambarnya sendiri di ``draw_vex``.
    _LIVE_MOD = None

    class _LiveFlag:
        """Penanda sederhana yang bisa di-set dari fungsi static."""
        __slots__ = ("v",)

        def __init__(self):
            self.v = False

    #: Dibaca rig: True = smear ayunan sudah diambil alih lapisan hidup
    #: 60fps, jadi canvas tidak menggambarnya dua kali.
    _FX_LIVE = _LiveFlag()

    @staticmethod
    def _live_module():
        """Muat ``heroes.vex_fx`` sekali; None kalau tidak tersedia.

        Impor dilakukan DI SINI (bukan di kepala modul) supaya bundle
        hero besar tidak menarik paket FX saat build hanya-butuh-
        renderer, dan supaya lapisan FX bisa dimatikan lewat satu flag
        tanpa merusak jalur render (pola yang sama dengan _NS_kaizen).
        """
        NS = _NS_vex
        if NS._LIVE_MOD is None:
            try:
                from heroes import vex_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "VEX_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def _fx_live_owned(hero):
        """True kalau lapisan hidup mengambil alih FX unit ini.

        Dipakai untuk memutuskan apakah smear ayunan + orb di-canvas
        masih perlu digambar (fallback) atau sudah digantikan lapisan
        layar.
        """
        try:
            mod = _NS_vex._live_module()
            if mod is None:
                return False
            return bool(mod.owns(hero))
        except Exception:
            return False

    def live_fx_ready():
        """True kalau lapisan hidup Vex bisa dipakai (dipakai tooling)."""
        return _NS_vex._live_module() is not None

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # Rig v2 membesarkan koordinat lokal lama.  Pipeline hero akan
    # mengukur badan dan men-scale kembali ke ukuran arena normal; yang
    # naik adalah kepadatan piksel/detail native.
    RIG_SCALE = 1.52

    # Durasi visual diselaraskan dengan hero_skills/vex_skills.py.
    SKILL_VISUAL_DURATION = {"q": 30, "w": 66, "e": 39, "r": 52}

    # Surface statis (aura/mist/platform/shadow) dibangun sekali lalu
    # dipakai ulang; animasi hanya mengubah alpha/overlay ringan.
    _STATIC_SURFACES = {}

    # Timeline serangan: wind-up -> tension -> release -> IMPACT -> recover.
    ATTACK_WINDUP_END = 0.28
    ATTACK_IMPACT = 0.56
    ATTACK_SWING_END = 0.66

    # ---------------------------------------------------------------------------
    # HD Color Palette - Outworld Destroyer inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - ashen/void gray (barely visible under hood)
        "skin_darkest":   ( 25,  30,  45),
        "skin_dark":      ( 50,  60,  75),
        "skin_mid":       ( 80,  90, 110),
        "skin_light":     (110, 125, 145),

        # Robe / cloak - dark purple/black
        "robe_darkest":   ( 10,   8,  25),
        "robe_dark":      ( 25,  20,  45),
        "robe_mid":       ( 45,  35,  75),
        "robe_light":     ( 75,  60, 115),
        "robe_high":      (110,  90, 155),

        # Armor plating - blackish purple with slight sheen
        "armor_darkest":  (  8,  10,  20),
        "armor_dark":     ( 20,  25,  40),
        "armor_mid":      ( 45,  50,  75),
        "armor_light":    ( 80,  90, 120),
        "armor_shine":    (135, 150, 190),

        # Void energy - teal/cyan glow (primary)
        "void_darkest":   (  8,  40,  50),
        "void_dark":      ( 20,  85, 100),
        "void_mid":       ( 45, 165, 175),
        "void_light":     ( 95, 225, 220),
        "void_bright":    (155, 245, 235),
        "void_hot":       (200, 255, 245),
        "void_white":     (235, 255, 250),
        "void_edge":      (120, 255, 236),
        "void_green":     ( 60, 235, 150),
        "void_gold":      (232, 210, 118),
        "void_gold_hot":  (255, 240, 196),
        "void_magma":     (236,  72,  80),


        # Masterwork detail & shadow-face swatches
        "face_dark":      (16, 14, 28),
        "crown_tip":      (235, 255, 250),
        "crown_rim":      (95, 225, 220),
        "orb_satellite":  (155, 245, 235),
        "rune_trace":     (140, 235, 230),
        "robe_weave":     (60, 48, 92),
        "robe_dither":    (34, 28, 58),
        "armor_rim":      (170, 190, 220),


        # Astral purple - E skill (imprisonment)
        "astral_darkest": ( 25,   8,  50),
        "astral_dark":    ( 60,  25, 110),
        "astral_mid":     (115,  55, 190),
        "astral_light":   (175, 110, 235),
        "astral_bright":  (215, 165, 250),
        "astral_hot":     (240, 220, 255),

        # Eye - glowing teal
        "eye_glow":       (155, 245, 235),
        "eye_bright":     (220, 255, 250),

        # Staff wood/metal
        "staff_dark":     ( 15,  20,  30),
        "staff_mid":      ( 40,  45,  60),
        "staff_light":    ( 75,  85, 105),
        "staff_shine":    (125, 145, 170),


        # Gold trim / runes
        "rune_dark":      ( 30,  75,  85),
        "rune_mid":       ( 60, 155, 165),
        "rune_light":     (140, 235, 230),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        if type(color) is tuple and len(color) == 3:
            _r, _g, _b = color
            if (type(_r) is int and type(_g) is int and type(_b) is int
                    and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
                return color
        return tuple(max(0, min(255, int(c))) for c in color)


    def _static(key, builder):
        """Ambil/bangun surface statis (cache miss saja)."""
        surf = _NS_vex._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_vex._STATIC_SURFACES[key] = surf
        return surf


    def _mix(a, b, t):
        """Blend linear dua warna RGB."""
        t = max(0.0, min(1.0, float(t)))
        return _NS_vex._clamp((
            a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t))


    def _hash01(seed):
        """Pseudo-random deterministik 0..1, aman untuk cache sprite."""
        h = int(seed) * 2654435761 & 0xFFFFFFFF
        h ^= h >> 16
        return (h & 0xFFFF) / 65535.0


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vex._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_vex.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vex._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_vex._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_vex._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_vex._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).

        Hasil di-clamp ke dalam canvas (ukurannya mengikuti
        ``range``, lihat _canvas_size_for) supaya efek tidak
        terpotong di tepi canvas.
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        # Clamp ke dalam canvas - rumus half sama dengan
        # _canvas_size_for di heroes/__init__.py (jaga agar tetap sinkron).
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_vex._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: proyeksikan jarak dunia ke ruang canvas, lalu clamp
        # seperti _world_to_local agar tidak keluar dari cache canvas.
        scale = getattr(boss, "_render_scale", None)
        if scale:
            rng = int(getattr(boss, "range", 130) or 130)
            half = max(120, int(rng / float(scale)) + 40)
            dist = min(250 / float(scale), half - 20)
        else:
            dist = 250
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # FX helper primitives (setingkat Thorne v2.1)
    # ---------------------------------------------------------------------------
    def _fx_scale(hero):
        """Kompensasi efek world-space: 1/_render_scale, cap 2.6."""
        scale = getattr(hero, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))


    def _ring_r(hero, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam cache."""
        scale = getattr(hero, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))


    def _spark_star(surface, cx, cy, size, color, alpha, spikes=2, rot=0.4,
                    core=None):
        """Bintang spike selang-seling untuk impact/aktivasi."""
        if alpha <= 0 or size <= 0:
            return
        alpha = max(0, min(255, int(alpha)))
        for k in range(spikes):
            ang = rot + k * math.tau / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_vex._aaline(surface, (*color, alpha),
                            (int(cx), int(cy)),
                            (int(cx + math.cos(ang) * ln),
                             int(cy + math.sin(ang) * ln * .82)),
                            2 if k % 2 == 0 else 1)
        if core:
            _NS_vex._aacircle(surface, (*core, alpha),
                              (int(cx), int(cy)), max(1, int(size * .28)))


    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Panah telegraph menghadap arah ``ang``."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px_, py_ = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for side in (-1, 1):
            _NS_vex._aaline(
                surface, (*color, max(0, min(255, int(alpha)))),
                (int(cx + px_ * side * size * .55 - ca * size * .5),
                 int(cy + py_ * side * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)


    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=5, thick=3, span=0.6, squash=.92):
        """Cincin rune putus-putus yang berputar."""
        if alpha <= 0 or radius <= 1:
            return
        alpha = max(0, min(255, int(alpha)))
        for i in range(segments):
            a0 = phase + i * math.tau / segments
            a1 = a0 + math.tau / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_vex._aaline(surface, (*color, alpha), p0, p1, thick)


    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan zigzag deterministik dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x0, y0, a = float(cx), float(cy), float(ang)
        pts = [(x0, y0)]
        for i in range(4):
            a += (_NS_vex._hash01(seed * 17 + i * 31) - .5) * .75
            seg = length / 4.0
            x0 += math.cos(a) * seg
            y0 += math.sin(a) * seg * .55
            pts.append((x0, y0))
        alpha = max(0, min(255, int(alpha)))
        for i in range(len(pts) - 1):
            _NS_vex._aaline(surface, (*colors[0], alpha),
                            pts[i], pts[i + 1], width + 2)
            _NS_vex._aaline(surface, (*colors[1], alpha),
                            pts[i], pts[i + 1], width)


    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi siluet bergerigi deterministik."""
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / max(1.0, min_len)))
            nx_, ny_ = (by - ay), -(bx - ax)
            ln = math.hypot(nx_, ny_) or 1.0
            nx_, ny_ = nx_ / ln, ny_ / ln
            for j in range(n):
                t = (j + 0.5) / n
                px_, py_ = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 *
                             _NS_vex._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px_ + nx_ * d, py_ + ny_ * d))
                else:
                    out.append((px_ - nx_ * d * .45, py_ - ny_ * d * .45))
            out.append((bx, by))
        return out


    def _draw_arc_pair(surface, cx, cy, rx, ry, start, end, color,
                       alpha=180, width=2, segments=24):
        """Arc elips ringan untuk dome/ring (tanpa alokasi surface)."""
        if rx <= 0 or ry <= 0 or alpha <= 0:
            return
        prev = None
        span = end - start
        for i in range(segments + 1):
            a = start + span * i / segments
            pt = (int(cx + math.cos(a) * rx),
                  int(cy + math.sin(a) * ry))
            if prev is not None:
                _NS_vex._aaline(surface, (*color, alpha), prev, pt, width)
            prev = pt


    # ---------------------------------------------------------------------------
    # SKILL FX v3 PRIMITIVES — glyph rune, sigil ring, crystal shard,
    # energy arc, nova, dither disk, chain link, orbit glint, arc band.
    # Semua fast-path pygame.draw (tanpa alokasi surface per segmen)
    # supaya FX tetap cache-miss friendly di ukuran fx_scale 2.6x.
    # ---------------------------------------------------------------------------
    def _rgba(color, alpha):
        """Warna RGBA ter-clamp untuk pemanggilan pygame.draw langsung."""
        return (*_NS_vex._clamp(color), max(0, min(255, int(alpha))))

    def _dpoly(surface, color, alpha, points):
        """Polygon RGBA fast-path: langsung blend ke canvas SRCALPHA."""
        if len(points) < 3 or alpha <= 0:
            return
        pts = [(int(px), int(py)) for px, py in points]
        pygame.draw.polygon(surface, _NS_vex._rgba(color, alpha), pts)

    def _arc_band(surface, cx, cy, rx, ry, a0, a1, color, alpha,
                  width=2, segments=14):
        """Arc elips ringan tanpa alokasi surface (pengganti _draw_arc_pair
        untuk jalur panas: accretion band, kubah kaca, rim lensing)."""
        if alpha <= 0 or rx <= 1 or ry <= 1:
            return
        col = _NS_vex._rgba(color, alpha)
        prev = None
        span = a1 - a0
        for i in range(segments + 1):
            a = a0 + span * i / segments
            pt = (int(cx + math.cos(a) * rx), int(cy + math.sin(a) * ry))
            if prev is not None:
                pygame.draw.line(surface, col, prev, pt, max(1, width))
            prev = pt

    def _rune_glyph(surface, x, y, size, kind, color, alpha, rot=0.0):
        """Mikro-rune prosedural (5 varian, 1-3 goresan): wajik, palang,
        siku ganda, segitiga, silang — bata penyusun cincin sigil."""
        if alpha <= 0 or size < 2:
            return
        col = _NS_vex._rgba(color, alpha)
        ca, sa = math.cos(rot), math.sin(rot)

        def P(dx, dy):
            return (int(x + (dx * ca - dy * sa) * size),
                    int(y + (dx * sa + dy * ca) * size))

        k = int(kind) % 5
        if k == 0:      # wajik
            pygame.draw.polygon(surface, col,
                                [P(-.5, 0), P(0, -.6), P(.5, 0), P(0, .6)])
        elif k == 1:    # palang + titik
            pygame.draw.line(surface, col, P(-.5, 0), P(.5, 0), 1)
            pygame.draw.circle(surface, col, P(0, -.45), 1)
        elif k == 2:    # siku ganda
            pygame.draw.line(surface, col, P(-.45, -.35), P(-.1, .35), 1)
            pygame.draw.line(surface, col, P(.1, -.35), P(.45, .35), 1)
        elif k == 3:    # segitiga
            pygame.draw.polygon(surface, col, [P(-.5, .4), P(.5, .4), P(0, -.5)])
        else:           # silang
            pygame.draw.line(surface, col, P(-.4, -.4), P(.4, .4), 1)
            pygame.draw.line(surface, col, P(.4, -.4), P(-.4, .4), 1)

    def _sigil_ring(surface, cx, cy, radius, phase, ramp, alpha,
                    n=8, squash=.6, seed=0, size=5):
        """Cincin sigil 3/4-view: deretan rune mengorbit sambil berputar.
        Glyph sisi depan (sin>0) lebih besar & terang — kedalaman palsu
        tanpa surface ekstra. ramp = (bright, mid, hot)."""
        if alpha <= 0 or radius < 5:
            return
        for i in range(n):
            a = phase + i * math.tau / n
            depth = .55 + .45 * (math.sin(a) * .5 + .5)
            gx = cx + math.cos(a) * radius
            gy = cy + math.sin(a) * radius * squash
            col = ramp[1] if depth < .82 else ramp[0]
            _NS_vex._rune_glyph(surface, gx, gy,
                                max(2, int(size * (.8 + .35 * depth))),
                                i * 3 + seed + int(phase * 2),
                                col, int(alpha * depth), rot=a + math.pi / 2)
            if i % 2 == 0:
                pygame.draw.circle(
                    surface, _NS_vex._rgba(ramp[2], alpha * .75 * depth),
                    (int(gx), int(gy)), 1)

    def _shard_glint(surface, x, y, color, alpha, size=3, core=False):
        """Kilau silang 4 arah 1px untuk ujung shard / pole anchor."""
        if alpha <= 0:
            return
        col = _NS_vex._rgba(color, alpha)
        xi, yi = int(x), int(y)
        s = max(1, int(size))
        pygame.draw.line(surface, col, (xi - s, yi), (xi + s, yi), 1)
        pygame.draw.line(surface, col, (xi, yi - s), (xi, yi + s), 1)
        if core:
            pygame.draw.circle(
                surface, _NS_vex._rgba(_NS_vex.PALETTE["white"], alpha),
                (xi, yi), 1)

    def _crystal_shard(surface, bx, by, w, h, ang, ramp, alpha, glint=0):
        """Shard kristal faset: siluet gelap 5 titik, faset kiri key-light,
        rim kanan (selout terang), specular 1px, ujung menyala.
        ramp = (dark, mid, bright, hot)."""
        if alpha <= 0 or h < 3:
            return
        ca, sa = math.cos(ang), math.sin(ang)

        def P(dx, dy):
            return (int(bx + dx * ca - dy * sa), int(by + dx * sa + dy * ca))

        base_l, base_r = P(-w, 3), P(w, 3)
        sho_l, sho_r = P(-w * .45, -h * .55), P(w * .45, -h * .55)
        tip = P(0, -h)
        _NS_vex._dpoly(surface, ramp[0], alpha,
                       [base_l, base_r, sho_r, tip, sho_l])
        _NS_vex._dpoly(surface, ramp[1], alpha,
                       [base_l, P(0, 3), P(0, -h * .8), sho_l])
        _skill_outlined_line(surface, sho_r, tip, 1, ramp[2], int(alpha * .9))
        _skill_outlined_line(surface, base_r, sho_r, 1, ramp[2], int(alpha * .7))
        pygame.draw.line(surface,
                         _NS_vex._rgba(ramp[3], min(255, alpha + 30)),
                         P(-w * .5, -h * .35), P(-w * .2, -h * .6), 1)
        if glint:
            _NS_vex._shard_glint(surface, tip[0], tip[1], ramp[3],
                                 int(alpha * .8), max(2, w), core=True)

    def _beam3(surface, a, b, width, ramp, alpha):
        """Beam 3-lapis: stroke gelap -> badan mid -> inti hot.
        ramp = (body_mid, halo_dark, core_hot)."""
        if alpha <= 0:
            return
        _skill_outlined_line(surface, a, b, width + 2, ramp[1], int(alpha * .55))
        _skill_outlined_line(surface, a, b, width, ramp[0], alpha)
        if width >= 2:
            pygame.draw.line(
                surface, _NS_vex._rgba(ramp[2], min(255, alpha + 40)),
                (int(a[0]), int(a[1])), (int(b[0]), int(b[1])),
                max(1, width - 2))

    def _energy_arc(surface, x0, y0, x1, y1, seed, color, alpha,
                    width=1, wobble=5.0):
        """Busur energi zigzag deterministik (hash seed) + under-glow."""
        if alpha <= 0:
            return
        pts = [(x0, y0)]
        for i in range(1, 4):
            t = i / 4.0
            jx = (_NS_vex._hash01(seed * 13 + i * 7) - .5) * wobble * 2
            jy = (_NS_vex._hash01(seed * 29 + i * 11) - .5) * wobble * 2
            pts.append((x0 + (x1 - x0) * t + jx, y0 + (y1 - y0) * t + jy))
        pts.append((x1, y1))
        dark = _NS_vex.PALETTE["shadow_deep"]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            ai, bi = (int(a[0]), int(a[1])), (int(b[0]), int(b[1]))
            pygame.draw.line(surface, _NS_vex._rgba(dark, alpha * .45),
                             ai, bi, width + 2)
            pygame.draw.line(surface, _NS_vex._rgba(color, alpha),
                             ai, bi, width)

    def _nova(surface, cx, cy, r_in, r_out, petals, rot, ramp, alpha,
              squash=.82):
        """Ledakan nova: kelopak polygon runcing — lapis gelap penuh +
        lapis hot inset. ramp = (main, under)."""
        if alpha <= 0 or petals < 3:
            return
        span = math.tau / petals
        for i in range(petals):
            a = rot + i * span
            a0, a1 = a - span * .3, a + span * .3
            p0 = (cx + math.cos(a0) * r_in, cy + math.sin(a0) * r_in * squash)
            p1 = (cx + math.cos(a) * r_out, cy + math.sin(a) * r_out * squash)
            p2 = (cx + math.cos(a1) * r_in, cy + math.sin(a1) * r_in * squash)
            _NS_vex._dpoly(surface, ramp[1], int(alpha * .55), [p0, p1, p2])
            q0 = (cx + math.cos(a0) * r_in * .9,
                  cy + math.sin(a0) * r_in * .9 * squash)
            q1 = (cx + math.cos(a) * r_out * .74,
                  cy + math.sin(a) * r_out * .74 * squash)
            q2 = (cx + math.cos(a1) * r_in * .9,
                  cy + math.sin(a1) * r_in * .9 * squash)
            _NS_vex._dpoly(surface, ramp[0], alpha, [q0, q1, q2])

    def _dither_disk(surface, cx, cy, rx, ry, color, alpha,
                     phase=0.0, seed=0):
        """Disk ground dither checkerboard — shading pixel-art murah;
        grid dibatasi (<=8x16) sehingga aman di fx_scale 2.6x."""
        if alpha <= 0 or rx < 4 or ry < 3:
            return
        cell = max(2, min(int(rx / 8.0), int(ry / 3.0)) or 2)
        rows = max(2, min(8, int(ry * 2 // cell)))
        for r in range(rows):
            ty = -ry + (2 * r + 1) * ry / rows
            hw = rx * math.sqrt(max(0.0, 1.0 - (ty / ry) ** 2))
            cols = max(1, min(16, int(hw * 2 // cell)))
            for c in range(cols):
                if (r + c) % 2:
                    continue
                x = -hw + (2 * c + 1) * hw / cols
                tw = _NS_vex._hash01(seed * 31 + r * 13 + c * 7
                                     + int(phase * 3))
                a = int(alpha * (.45 + .55 * tw))
                if a <= 0:
                    continue
                pygame.draw.rect(
                    surface, _NS_vex._rgba(color, a),
                    (int(cx + x), int(cy + ty), cell, cell))

    def _chain_link(surface, x, y, ang, w, h, color, alpha):
        """Mata rantai astral: batang rotasi ber-stroke gelap + inti
        lubang gelap — tether skill E."""
        if alpha <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        x0, y0 = int(x - ca * w), int(y - sa * w)
        x1, y1 = int(x + ca * w), int(y + sa * w)
        pygame.draw.line(
            surface, _NS_vex._rgba(_NS_vex.PALETTE["shadow_deep"], alpha * .8),
            (x0, y0), (x1, y1), h + 2)
        pygame.draw.line(surface, _NS_vex._rgba(color, alpha),
                         (x0, y0), (x1, y1), h)
        pygame.draw.line(
            surface,
            _NS_vex._rgba(_NS_vex.PALETTE["astral_darkest"], alpha),
            (int(x - ca * w * .5), int(y - sa * w * .5)),
            (int(x + ca * w * .5), int(y + sa * w * .5)), max(1, h - 2))

    def _orbit_glints(surface, cx, cy, rx, ry, phase, n, color, alpha,
                      hot=None):
        """Titik kilau mengorbit elips dengan ekor 1px (kedalaman depan)."""
        if alpha <= 0:
            return
        hot = hot or _NS_vex.PALETTE["white"]
        for i in range(n):
            a = phase + i * math.tau / n
            depth = .6 + .4 * (math.sin(a) * .5 + .5)
            gx = int(cx + math.cos(a) * rx)
            gy = int(cy + math.sin(a) * ry)
            al = int(alpha * depth)
            tx = int(cx + math.cos(a - .35) * rx * .93)
            ty = int(cy + math.sin(a - .35) * ry * .93)
            pygame.draw.line(surface, _NS_vex._rgba(color, al * .6),
                             (tx, ty), (gx, gy), 1)
            pygame.draw.circle(surface, _NS_vex._rgba(color, al), (gx, gy), 2)
            pygame.draw.circle(surface, _NS_vex._rgba(hot, al), (gx, gy), 1)


    # ---------------------------------------------------------------------------
    # Void visual helpers
    # ---------------------------------------------------------------------------


    def _draw_glow_orb(surface, cx, cy, radius, color_dark, color_mid,
                       color_hot, color_white=None):
        """Draw a soft glowing orb with layered halo."""
        if color_white is None:
            color_white = _NS_vex.PALETTE["white"]

        # Outer halo
        _NS_vex._aacircle(surface, (*color_dark, 100), (cx, cy), radius + 6)
        _NS_vex._aacircle(surface, (*color_mid, 150), (cx, cy), radius + 3)
        # Body
        _NS_vex._aacircle(surface, color_mid, (cx, cy), radius)
        _NS_vex._aacircle(surface, color_hot, (cx, cy), max(1, radius - 2))
        _NS_vex._aacircle(surface, color_white, (cx - 1, cy - 1), max(1, radius - 4))


    def _draw_rune_ring(surface, cx, cy, radius, phase, color, alpha=200,
                        segments=8):
        """Rotating rune ring."""
        for i in range(segments):
            a = phase * 0.5 + i * math.pi * 2 / segments
            px = cx + int(math.cos(a) * radius)
            py = cy + int(math.sin(a) * radius)
            _NS_vex._aacircle(surface, (*color, alpha), (px, py), 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_hot"], alpha), (px, py), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------------------
    class ArcaneOrbProjectile:
        """Basic teal arcane orb attack."""
        def __init__(self, sx, sy, tx, ty, speed=6.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1
            # Homing tiap frame ke target (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_vex._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 18:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            p = _NS_vex.PALETTE
            # Trail comet berlapis: spline outline + core memudar + serbuk samping.
            trail = list(self.trail[-18:])
            if len(trail) >= 2:
                for i in range(1, len(trail)):
                    t = i / max(1, len(trail) - 1)
                    a = int(35 + 150 * t)
                    w = max(1, int(1 + 4 * t))
                    _skill_outlined_line(surface, trail[i - 1], trail[i],
                                         w, p["void_mid"], a)
            for i, (tx_, ty_) in enumerate(trail):
                t = (i + 1) / max(1, len(trail))
                alpha = int(35 + 155 * t)
                r = max(1, int(2 + 5 * t))
                _NS_vex._aacircle(surface, (*p["void_darkest"], alpha // 2),
                                  (tx_, ty_), r + 4)
                _NS_vex._aacircle(surface, (*p["void_mid"], alpha),
                                  (tx_, ty_), r)
                _NS_vex._aacircle(surface, (*p["void_bright"], alpha),
                                  (tx_, ty_), max(1, r - 3))
                if i % 4 == 0:
                    side = self.angle + math.pi / 2
                    _NS_vex._aacircle(surface, (*p["void_hot"], alpha),
                                      (tx_ + int(math.cos(side) * 5 * t),
                                       ty_ + int(math.sin(side) * 5 * t)), 1)

            if not self.alive:
                fade = max(0.0, 1.0 - self.dead_frames / 8.0)
                if fade > 0:
                    cx_, cy_ = int(self.x), int(self.y)
                    _NS_vex._nova(surface, cx_, cy_, int(8 * fade),
                                  int(24 * fade), 6, phase * 1.8,
                                  (p["void_bright"], p["void_dark"]),
                                  int(215 * fade))
                    _NS_vex._spark_star(surface, cx_, cy_, int(20 * fade),
                                        p["void_bright"], int(210 * fade),
                                        spikes=8, rot=phase * 1.8,
                                        core=p["void_hot"])
                return

            px, py = int(self.x), int(self.y)
            # Forward smear + inti garis (arah tetap terbaca).
            bx = px - int(math.cos(self.angle) * 20)
            by = py - int(math.sin(self.angle) * 20)
            fx = px + int(math.cos(self.angle) * 9)
            fy = py + int(math.sin(self.angle) * 9)
            _skill_outlined_line(surface, (bx, by), (fx, fy), 5,
                                 p["void_bright"], 125)
            _skill_outlined_line(surface,
                                 (px - int(math.cos(self.angle) * 10),
                                  py - int(math.sin(self.angle) * 10)),
                                 (fx, fy), 2, p["void_hot"], 220)

            # Halo rune: dashed kontra-rotasi + 2 glyph + 2 bintang orbit.
            _NS_vex._dashed_ring(surface, px, py, 12, p["void_bright"], 210,
                                 phase * 2.8, segments=4, thick=2, span=.40)
            _NS_vex._dashed_ring(surface, px, py, 18, p["void_mid"], 125,
                                 -phase * 1.7, segments=5, thick=1, span=.28)
            for i in range(2):
                a = phase * 3 + i * math.pi
                rr = 10 + int(math.sin(phase * 4 + i) * 2)
                _NS_vex._rune_glyph(surface,
                                    px + math.cos(a) * rr,
                                    py + math.sin(a) * rr,
                                    3, i + int(phase * 2),
                                    p["void_bright"], 215, rot=a)
                a2 = a + math.pi / 2
                rr2 = 10 + int(math.sin(phase * 4 + i + 1) * 2)
                _NS_vex._spark_star(surface,
                                    px + int(math.cos(a2) * rr2),
                                    py + int(math.sin(a2) * rr2), 5,
                                    p["void_bright"], 210, spikes=4,
                                    rot=a2, core=p["void_hot"])

            # Badan orb faset + crescent specular kiri-atas + titik putih.
            _NS_vex._draw_glow_orb(surface, px, py, 8,
                                   p["void_dark"], p["void_mid"],
                                   p["void_hot"], p["void_white"])
            _NS_vex._arc_band(surface, px, py, 6, 6,
                              math.pi * .75, math.pi * 1.35,
                              p["void_white"], 235, 1, 6)
            _NS_vex._aacircle(surface, p["white"], (px - 2, py - 2), 1)
            _NS_vex._spark_star(surface, fx, fy, 7,
                                p["void_hot"], 240, spikes=2,
                                rot=self.angle, core=p["white"])


    class AstralOrbProjectile:
        """Astral Imprisonment purple orb - travels then creates bubble prison."""
        def __init__(self, sx, sy, tx, ty, speed=7.0,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            # BUGFIX (trail skill menempel permanen di hero): hitung
            # mundur frame setelah kematian. age dibekukan saat mati,
            # jadi filter pembersihan memakai counter ini, bukan age.
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            self.impact_frame = -1
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                # BUGFIX: age dibekukan setelah mati; tanpa counter
                # ini filter `p.alive or p.age < 8` tidak pernah
                # membuang projectile yang mati dengan age < 8 ->
                # trail skill tergambar permanen di canvas hero
                # (menempel, ikut bergerak bersama hero).
                self.dead_frames += 1
                return
            self.age += 1

            if self.impact_frame >= 0:
                # Prison bubble stays for a while
                if self.age - self.impact_frame > 60:
                    self.alive = False
                return

            # Homing tiap frame ke target selama terbang (terarah)
            if self.target is not None and getattr(self.target, 'alive', False):
                # BUGFIX (orb random pada hero): re-home lama menulis
                # koordinat DUNIA target ke tx/ty yang hidup dalam
                # ruang canvas renderer -> arah kacau. Konversi
                # lewat _world_to_local (source/cx/cy diisi saat
                # spawn; boss asli tanpa _render_scale = perilaku lama).
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_vex._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.impact_frame = self.age
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 16:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            p = _NS_vex.PALETTE
            # ── Tahap sangkar: aftermath mewah setelah impact ──
            if self.impact_frame >= 0:
                elapsed = self.age - self.impact_frame
                if elapsed < 8:
                    grow = elapsed / 8
                elif elapsed > 50:
                    grow = max(0.0, 1 - (elapsed - 50) / 10)
                else:
                    grow = 1.0
                radius = int(34 * grow)
                if radius < 3:
                    return
                cx_, cy_ = int(self.tx), int(self.ty)
                pulse = .78 + .22 * math.sin(phase * 3.0)
                # Footprint rune + tick + sigil ring.
                _skill_outlined_circle(surface, (cx_, cy_ + 15), radius, 3,
                                       p["astral_mid"], int(150 * grow))
                _NS_vex._dashed_ring(surface, cx_, cy_ + 15, radius + 6,
                                     p["astral_bright"],
                                     int(180 * pulse * grow),
                                     phase * 1.7, segments=10, thick=2,
                                     span=.35)
                _NS_vex._sigil_ring(surface, cx_, cy_ + 15, radius - 4,
                                    -phase * 1.1,
                                    (p["astral_bright"], p["astral_mid"],
                                     p["astral_hot"]),
                                    int(150 * grow), n=6, squash=.4,
                                    seed=23, size=3)
                for i in range(4):
                    a = i * math.pi / 2 + phase * .25
                    _NS_vex._chevron(surface,
                                     cx_ + math.cos(a) * (radius + 9),
                                     cy_ + 15 + math.sin(a) * (radius + 9) * .72,
                                     a + math.pi, 8, p["astral_hot"],
                                     int(170 * grow), 2)
                # Kolom energi vertikal 3-lapis.
                top = max(3, cy_ - int(radius * 1.8))
                for wd, col, al in ((16, p["astral_dark"], 80),
                                    (8, p["astral_mid"], 130),
                                    (3, p["astral_bright"], 205)):
                    _NS_vex._aaline(surface, (*col, int(al * pulse * grow)),
                                    (cx_, top), (cx_, cy_ + radius // 2), wd)
                # Sangkar kaca: kubah glass + bar rune vertikal.
                _NS_vex._aacircle(surface, (*p["astral_dark"], int(55 * grow)),
                                  (cx_, cy_), radius)
                _NS_vex._arc_band(surface, cx_, cy_, radius, radius,
                                  .18, math.pi - .18,
                                  p["astral_bright"],
                                  int(210 * pulse * grow), 2, 16)
                _NS_vex._arc_band(surface, cx_, cy_, radius - 5, radius - 5,
                                  math.pi + .25, math.tau - .25,
                                  p["astral_light"],
                                  int(150 * pulse * grow), 1, 14)
                for i in range(5):
                    a = phase * .4 + i * math.tau / 5
                    depth = .55 + .45 * (math.sin(a) * .5 + .5)
                    bx_ = int(cx_ + math.cos(a) * radius * .9)
                    by_ = int(cy_ + math.sin(a) * radius * .34)
                    h = int(radius * (.75 + .3 * depth))
                    _skill_outlined_line(
                        surface, (bx_, by_ + radius // 3), (bx_, by_ - h),
                        2, p["astral_bright"] if depth > .8 else p["astral_mid"],
                        int(200 * pulse * depth * grow))
                _NS_vex._dashed_ring(surface, cx_, cy_, radius - 2,
                                     p["astral_hot"], int(175 * pulse * grow),
                                     -phase * 1.9, segments=9, thick=1,
                                     span=.42)
                _NS_vex._aacircle(surface, (*p["astral_hot"], int(180 * grow)),
                                  (cx_ - radius // 2, cy_ - radius // 2),
                                  max(1, radius // 5))
                if elapsed < 14:
                    _NS_vex._spark_star(surface, cx_, cy_,
                                        int((22 - elapsed) * grow),
                                        p["astral_bright"], int(230 * grow),
                                        spikes=8, rot=phase, core=p["white"])
                # Partikel energi naik di dalam sangkar.
                for i in range(4):
                    pt = (phase * 0.4 + i * 0.125) % 1.0
                    py_off = int(-pt * radius * 1.6 + radius * 0.5)
                    px_off = int(math.sin(phase * 2 + i) * (radius // 3))
                    alpha = int(220 * (1 - pt) * grow)
                    _NS_vex._aacircle(surface, (*p["astral_hot"], alpha),
                                      (cx_ + px_off, cy_ + py_off), 2)
                    _NS_vex._aacircle(surface, p["white"],
                                      (cx_ + px_off, cy_ + py_off), 1)
                return

            # ── Tahap terbang: pita astral + orb black-hole berrune ──
            trail = list(self.trail[-16:])
            if len(trail) >= 2:
                for i in range(1, len(trail)):
                    t = i / max(1, len(trail) - 1)
                    _skill_outlined_line(surface, trail[i - 1], trail[i],
                                         max(1, int(1 + 3 * t)),
                                         p["astral_light"], int(55 + 150 * t))
            for i, (tx_, ty_) in enumerate(trail):
                t = (i + 1) / max(1, len(trail))
                alpha = int(35 + 165 * t)
                r = max(1, int(2 + 4 * t))
                _NS_vex._aacircle(surface, (*p["astral_dark"], alpha // 2),
                                  (tx_, ty_), r + 3)
                _NS_vex._aacircle(surface, (*p["astral_light"], alpha),
                                  (tx_, ty_), r)
                if i % 3 == 0:
                    _NS_vex._aacircle(surface, p["white"], (tx_, ty_), 1)

            if self.alive:
                px, py = int(self.x), int(self.y)
                bx = px - int(math.cos(self.angle) * 18)
                by = py - int(math.sin(self.angle) * 18)
                fx = px + int(math.cos(self.angle) * 8)
                fy = py + int(math.sin(self.angle) * 8)
                _skill_outlined_line(surface, (bx, by), (fx, fy), 4,
                                     p["astral_bright"], 140)
                _NS_vex._dashed_ring(surface, px, py, 15,
                                     p["astral_bright"], 210,
                                     phase * 2.8, segments=4, thick=2,
                                     span=.42)
                _NS_vex._dashed_ring(surface, px, py, 22,
                                     p["astral_mid"], 115,
                                     -phase * 1.6, segments=5, thick=1,
                                     span=.28)
                _NS_vex._aacircle(surface, (*p["astral_mid"], 205), (px, py), 12)
                _NS_vex._aacircle(surface, (*p["astral_light"], 220), (px, py), 8)
                _NS_vex._aacircle(surface, p["shadow_deep"], (px, py), 5)
                _NS_vex._aacircle(surface, p["astral_darkest"], (px, py), 3)
                _NS_vex._aacircle(surface, p["astral_hot"], (px - 2, py - 2), 2)
                for i in range(2):
                    a = phase * 4 + i * math.pi
                    rr = 10 + int(math.sin(phase * 3.4 + i) * 2)
                    _NS_vex._rune_glyph(surface,
                                        px + math.cos(a) * rr,
                                        py + math.sin(a) * rr,
                                        3, i * 2 + int(phase * 2),
                                        p["astral_bright"], 220, rot=a)
                    a2 = a + math.pi / 2
                    rr2 = 10 + int(math.sin(phase * 3.4 + i + 1) * 2)
                    _NS_vex._spark_star(surface,
                                        px + int(math.cos(a2) * rr2),
                                        py + int(math.sin(a2) * rr2), 5,
                                        p["astral_bright"], 220, spikes=4,
                                        rot=a2, core=p["astral_hot"])
                _NS_vex._spark_star(surface, fx, fy, 7,
                                    p["astral_hot"], 245,
                                    spikes=2, rot=self.angle, core=p["white"])


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_vx_last_x"):
            boss._vx_last_x = boss.x
            boss._vx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vx_last_x)
        dy = abs(boss.y - boss._vx_last_y)
        boss._vx_last_x = boss.x
        boss._vx_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving


    def _update_attack_anim(boss):
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vx_prev_timer", -1))
        active = bool(getattr(boss, "_vx_attack_active", False))

        # ═══ PERBAIKAN v21 - SWING TERLIHAT TIDAK NATURAL ═══
        # attack_timer adalah hitung MUNDUR: di-set ke attack_cooldown
        # saat menyerang, lalu berkurang 1 tiap langkah simulasi.
        #
        # Deteksi lama mensyaratkan fungsi ini - yang dipanggil dari
        # DRAW - melihat timer tepat pada nilai puncaknya. Itu hanya
        # terjadi kalau 1 frame gambar = 1 langkah simulasi, yaitu di
        # 60 FPS. Dengan fixed timestep di HP, satu frame gambar
        # mencakup 4-12 langkah simulasi, sehingga nilai puncak tidak
        # pernah terlihat -> animasi swing nyaris tidak pernah dipicu
        # dan yang tampak hanya potongan pose acak.
        #
        # Serangan baru = timer NAIK. Itu benar untuk berapa pun
        # jumlah langkah simulasi yang terlewat antar-gambar.
        trigger = previous >= 0 and timer > previous

        if trigger:
            boss._vx_attack_active = True
            active = True

        if active and timer <= 0:
            boss._vx_attack_active = False
            active = False

        boss._vx_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._vx_attack_frame = max(0, cooldown - timer) if active else 0
        boss._vx_attack_progress = (
            min(1.0, boss._vx_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_vx_projectiles"):
            boss._vx_projectiles = []
        for proj in boss._vx_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._vx_projectiles = [p for p in boss._vx_projectiles
                                if p.alive or p.dead_frames < 8]


    def _spawn_arcane_orb(boss, x, y):
        if not hasattr(boss, "_vx_projectiles"):
            boss._vx_projectiles = []
        tx, ty = _NS_vex._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Orb spawns from the pose-driven staff tip (shared with the rig).
        sx, sy = _NS_vex._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_vx_attack_progress", 0.0)))
        tgt = getattr(boss, "target", None)
        proj = _NS_vex.ArcaneOrbProjectile(
            sx, sy, tx, ty, speed=6.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._vx_projectiles.append(proj)


    def _spawn_astral_orb(boss, x, y):
        if not hasattr(boss, "_vx_projectiles"):
            boss._vx_projectiles = []
        tx, ty = _NS_vex._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx, sy = _NS_vex._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_vx_attack_progress", 0.0)))
        tgt = getattr(boss, "target", None)
        proj = _NS_vex.AstralOrbProjectile(
            sx, sy, tx, ty, speed=7.0,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._vx_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_vex(surface, boss, x, y):
        """Entry point for Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan mengikuti kontrak render order proyek:

            GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD ->
            WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
            SKILL FX -> IMPACT FX -> DEBUG

        Arc ayunan staff, partikel void, proyektil serpihan, spike
        crystal W, kurungan astral E, ledakan Essence Flux R, impact,
        screen shake, dan hit-stop hidup di ``heroes/vex_fx.py``
        (lapisan layar 1:1, di luar sprite cache).  Semua nama publik
        lama tetap ada; kalau modul FX tidak dimuat, renderer kembali
        menggambar semuanya di-canvas (jalur fallback).
        """
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vex._detect_moving(boss)
        _NS_vex._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer ke canvas, lalu sprite hasilnya DI-CACHE.
        # Lapisan hidup di sana digambar oleh heroes/__init__ (pre/post),
        # jadi di sini cukup dipasang penanda "diambil alih" supaya tidak
        # ada efek yang tergambar dua kali.  Jalur BOSS (tanpa
        # _render_scale) draw dipanggil tiap frame -> lapisan hidup
        # digambar sendiri di sini.
        hero_lane = hasattr(boss, "_render_scale")
        if not portrait_hd:
            try:
                mod = _NS_vex._live_module()
                if mod is not None:
                    if hero_lane:
                        mod.attach(boss)
                    else:
                        mod.draw_ground_layer(surface, boss, x, y)
            except Exception:
                pass
        _NS_vex._FX_LIVE.v = (not portrait_hd) and \
            _NS_vex._fx_live_owned(boss)

        attacking = (
            getattr(boss, "_vx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # Portraits deliberately contain only the character rig.  Auras and
        # arena-sized skill effects would force the auto-crop to shrink the
        # crown, hood, robe material, and staff orb.
        if not portrait_hd:
            # ---------- Background layers ----------
            # Cyan rim-light keeps the crown, shoulder spikes, and staff orb
            # legible against dark terrain while preserving pixel edges.
            _NS_vex._draw_void_silhouette_glow(surface, x, y - 20, pulse)
            _NS_vex._draw_void_aura(surface, x, y, pulse)
            _NS_vex._draw_void_platform(surface, x, y + 62, pulse, active_skill)

            # ---------- Skill ground effects ----------
            if active_skill == "q":
                _NS_vex._draw_arcane_orb_telegraph(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                _NS_vex._draw_sanity_eclipse_ground(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_vex._draw_essence_flux_ground(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_vex._draw_astral_indicator(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_vex._draw_vex_attack(surface, boss, x, y)
        elif moving:
            _NS_vex._draw_vex_walk(surface, boss, x, y)
        else:
            _NS_vex._draw_vex_idle(surface, boss, x, y)

        if not portrait_hd:
            # ---------- Projectiles ----------
            _NS_vex._manage_projectiles(boss, surface, pulse)

            # ---------- Skill foreground effects ----------
            if active_skill == "q":
                _NS_vex._draw_arcane_orb_charge(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_vex._handle_astral_skill(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                _NS_vex._draw_sanity_eclipse(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_vex._draw_essence_flux(surface, boss, x, y, skill_timer, pulse)

            # ---------- LAPISAN FX HIDUP (jalur BOSS) ----------
            # Di jalur lane hero, lapisan ini digambar heroes/__init__.py
            # SETELAH sprite di-blit (sprite-nya ter-cache); di jalur boss
            # draw dipanggil tiap frame, jadi digambar di sini.
            if not hero_lane:
                try:
                    mod = _NS_vex._live_module()
                    if mod is not None:
                        mod.draw_live_layer(surface, boss, x, y)
                except Exception:
                    pass


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_vex_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_vex._draw_shadow(surface, x, y + 72)
            _NS_vex._draw_floating_void(surface, x, y + 54, boss.pulse)
        _NS_vex._draw_vex_body(surface, x, y + bob, boss.direction,
                               boss.pulse, "idle", detail=portrait,
                               skill_state=getattr(boss, "active_skill", None))


    def _draw_vex_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_vex._draw_shadow(surface, x + sway, y + 72)
            _NS_vex._draw_floating_void(surface, x + sway, y + 54, phase, trail=True,
                               facing=boss.direction)
        _NS_vex._draw_vex_body(surface, x + sway, y - bob, boss.direction,
                               phase, "walk", detail=portrait,
                               skill_state=getattr(boss, "active_skill", None))


    def _draw_vex_attack(surface, boss, x, y):
        progress = getattr(boss, "_vx_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        portrait = bool(getattr(boss, "_portrait_hd", False))

        # Basic attack TIDAK spawn renderer projectile (pakai generic
        # _entity.py yang homing & terarah). Arcane orb renderer hanya
        # saat skill aktif.
        if (getattr(boss, "active_skill", None) is not None
                and 0.5 < progress < 0.6
                and not getattr(boss, "_vx_proj_spawned", False)
                and not portrait):
            _NS_vex._spawn_arcane_orb(boss, x, y)
            boss._vx_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._vx_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        if not portrait:
            _NS_vex._draw_shadow(surface, x + recoil, y + 72)
            _NS_vex._draw_floating_void(surface, x + recoil, y + 54, boss.pulse, intense=True)
        _NS_vex._draw_vex_body(surface, x + recoil, y, boss.direction, boss.pulse,
                       "attack", progress, detail=portrait,
                       skill_state=getattr(boss, "active_skill", None))
        if not portrait:
            _NS_vex._draw_orb_release_flash(surface, x + recoil, y, boss.direction, progress, boss.pulse)
            _NS_vex._draw_staff_impact_flash(surface, x + recoil, y,
                                             boss.direction, progress, boss.pulse)


    # ===================================================================
    # BODY RENDERING - HD void mage
    # ===================================================================

    # ===================================================================
    # MASTERWORK RIG - bone rig 2D berlapis (setara Kaizen/Thorne/Zephyr)
    #
    # Mengganti seluruh set "body-part sticker" lama (cloak, lower_robe,
    # torso, idle/attack arms, arm_segment, hand, staff, head_crown,
    # body_particles) dengan SATU rig pose-driven: crown void menyala
    # dengan ujung cyan, hood berwajah shadow dengan celah mata menyala,
    # pauldron spiky, robe robek yang mengambang, dan staff surgawi yang
    # posisi orb dihitung dari sendi sehingga Arcane Orb / Astral
    # Imprisonment muncul dari ujung staff (bukan pinggang). Semua 100%
    # primitif pygame - tanpa PNG, sprite sheet, ataupun image.load.
    # ===================================================================
    def _draw_vex_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0, detail=False, skill_state=None):
        """Wrapper agar idle/walk/attack/skill meneruskan setiap frame ke
        satu rig tulang berlapis (bone rig) tanpa mengubah kontrak."""
        _NS_vex._draw_vex_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, detail, skill_state)


    # -------------------------------------------------------------------
    # Pose helpers (deterministic; dipakai rig + anchor skill)
    # -------------------------------------------------------------------
    def _orb_tip_local(phase, action="idle", attack_progress=0.0):
        """Posisi ujung orb staff (ruang lokal, forward = +x).

        Menyambungkan staff ke sendi: saat wind-up orb ditarik ke
        belakang/atas, saat release didorong ke depan, recovery kembali.
        """
        wave = math.sin(phase * 1.3) * 1.5
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < .38:
                t = ap / .38
                return (int(26 - 12 * t), int(-40 - 14 * t + wave))
            if ap < .62:
                t = (ap - .38) / .24
                return (int(14 + 38 * t), int(-54 + 18 * t + wave))
            t = (ap - .62) / .38
            return (int(52 - 20 * t), int(-36 + 4 * t + wave))
        if action == "walk":
            return (int(32 + math.sin(phase * 1.72) * 3),
                    int(-44 + wave))
        return (32, int(-44 + wave))


    def _staff_butt_local(phase, action="idle", attack_progress=0.0):
        ox, oy = _NS_vex._orb_tip_local(phase, action, attack_progress)
        return (int(ox - 30), int(oy + 40))


    def _staff_grip_local(phase, action="idle", attack_progress=0.0):
        ox, oy = _NS_vex._orb_tip_local(phase, action, attack_progress)
        bx, by = _NS_vex._staff_butt_local(phase, action, attack_progress)
        return (int(bx + (ox - bx) * .5), int(by + (oy - by) * .5))


    def _staff_orb_position(cx, cy, facing, phase=0.0, action="idle",
                            attack_progress=0.0):
        """Posisi orb (ruang dunia/canvas) untuk efek skill."""
        tx, ty = _NS_vex._orb_tip_local(phase, action, attack_progress)
        f = 1 if facing >= 0 else -1
        rs = _NS_vex.RIG_SCALE
        return int(cx + tx * rs * f), int(cy + ty * rs)


    def _attack_pose(ap):
        """Keyframe serangan Vex: lengan/staff, badan, dan impact.

        0.00 rest -> 0.18 wind-up -> 0.32 tension -> 0.48 release
        -> 0.56 IMPACT -> 0.76 follow-through -> 1.00 rest.
        Return bob/lean/flare/tremble yang dipakai rig dan FX smear.
        """
        keys = (
            (0.00,  0,  0, 1.00, 0),
            (0.18, -4, -6, 1.12, 0),
            (0.32, -6, -8, 1.24, 1),
            (0.48,  0, 10, 1.16, 0),
            (0.56,  5, 13, 1.30, 0),
            (0.76,  1,  6, 1.08, 0),
            (1.00,  0,  0, 1.00, 0),
        )
        ap = max(0.0, min(1.0, float(ap)))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)
                return {
                    "bob": int(round(k0[1] + (k1[1] - k0[1]) * t)),
                    "lean": int(round(k0[2] + (k1[2] - k0[2]) * t)),
                    "flare": k0[3] + (k1[3] - k0[3]) * t,
                    "tremble": 1 if (k0[4] and t < .9) else 0,
                }
        return {"bob": 0, "lean": 0, "flare": 1.0, "tremble": 0}


    # -------------------------------------------------------------------
    # The layered bone rig
    # -------------------------------------------------------------------
    def _draw_vex_elite(surface, cx, cy, facing, phase, action,
                        attack_progress=0.0, detail=False, skill_state=None):
        p = _NS_vex.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72)
        breath = math.sin(phase * .8)
        rs = _NS_vex.RIG_SCALE
        overcharge = skill_state in ("q", "w", "r")
        astralized = skill_state == "e"

        # Root/secondary motion: idle float, foot/hem contact saat walk,
        # dan 7-keyframe attack dengan frame IMPACT.
        lean = int(stride * 3.0 if walk else 0.0)
        root_y = int(breath * 1.2)
        flare = 1.0
        if attack:
            pose = _NS_vex._attack_pose(ap)
            lean = pose["lean"] * f
            root_y += pose["bob"]
            flare = pose["flare"]
            if pose["tremble"]:
                lean += (1 if int(phase * 31) % 2 else -1)
        elif walk:
            root_y -= int(abs(stride) * 2.5)
        else:
            lean = int(math.sin(phase * .8) * 3.0) * f
        if overcharge:
            flare *= 1.10 + math.sin(phase * 2.4) * .04
        if astralized:
            root_y -= int(2 + math.sin(phase * 2.0))

        def pt(dx, dy):
            return (int(cx + dx * rs * f + lean),
                    int(cy + dy * rs + root_y))

        def sw(v):
            return max(1, int(round(v * rs)))

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_vex._poly(surface, p["shadow_deep"],
                              [(qx + sw(.8) * f, qy + sw(.7)) for qx, qy in pts])
            _NS_vex._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            w = sw(width)
            _NS_vex._aaline(surface, p["shadow_deep"],
                            (aa[0] + sw(1) * f, aa[1] + sw(.8)),
                            (bb[0] + sw(1) * f, bb[1] + sw(.8)), w + sw(3))
            _NS_vex._aaline(surface, base, aa, bb, w)
            if light:
                off = -sw(.8) if f > 0 else sw(.8)
                _NS_vex._aaline(surface, light,
                                (aa[0] + off, aa[1] - sw(.7)),
                                (bb[0] + off, bb[1] - sw(.7)),
                                max(1, w // 3))

        def dot(color, dx, dy, r, outline=True):
            x, y = pt(dx, dy)
            rr = sw(r)
            if outline:
                _NS_vex._aacircle(surface, p["shadow_deep"],
                                  (x + sw(1) * f, y + sw(.8)), rr + sw(1))
            _NS_vex._aacircle(surface, color, (x, y), rr)

        # Tattered back-cape flare (balances the staff silhouette).
        cape_wave = int(math.sin(phase * .8) * 2)
        poly(p["robe_darkest"], [(-12, -16), (-4, -18), (-6, -2),
             (-10 + cape_wave, 12), (-16, 26), (-22 + cape_wave, 34),
             (-26, 26), (-24, 12), (-20 + cape_wave, -2)])
        poly(p["robe_dark"], [(-11, -14), (-5, -16), (-7, -2),
             (-11 + cape_wave, 10), (-16, 22), (-20 + cape_wave, 28),
             (-23, 22), (-21, 10), (-18 + cape_wave, -2)], False)
        _NS_vex._aaline(surface, p["robe_light"], pt(-19, 0),
                        pt(-23 + cape_wave, 24), 1)
        _NS_vex._aaline(surface, (*p["void_dark"], 160),
                        pt(-21, 6), pt(-25 + cape_wave, 26), 1)

        # Dark crown flames behind the hood.
        _NS_vex._draw_elite_crown(surface, pt, poly, dot, f, phase,
                                  action, back=True, detail=detail)

        # Rear arm (free claw) behind the torso.
        rear_shoulder = (-11, -14)
        if attack:
            rear_elbow = (-16, -2)
            rear_hand = (-17, 9)
        elif walk:
            rear_elbow = (-16, int(stride * 4))
            rear_hand = (-17, 9 + int(stride * 5))
        else:
            rear_elbow = (-16, 0)
            rear_hand = (-17, 9 + int(breath * 2))
        limb(rear_shoulder, rear_elbow, 6, p["robe_dark"], p["robe_mid"])
        limb(rear_elbow, rear_hand, 5, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_vex._aacircle(surface, p["skin_darkest"], (rhx, rhy), 4)
        _NS_vex._aacircle(surface, p["skin_mid"], (rhx, rhy), 3)
        _NS_vex._aacircle(surface, p["skin_light"], (rhx - f, rhy - 1), 1)
        for finger in (-2, 0, 2):
            _NS_vex._aaline(surface, p["skin_light"],
                            (rhx + f, rhy + finger),
                            (rhx + f * 5, rhy + finger - 3), 1)

        # Tattered floating robe / ghost tail (no legs).
        tail_wave = int(math.sin(phase * .9) * 2)
        poly(p["robe_darkest"], [(-15, -8), (15, -8),
             (16 + tail_wave, 10), (13, 24), (7, 36),
             (2 + tail_wave, 44), (-3, 46), (-8, 38),
             (-13, 24), (-16 + tail_wave, 10)])
        poly(p["robe_dark"], [(-13, -6), (13, -6),
             (13 + tail_wave, 10), (10, 22), (5, 33),
             (0, 40), (-5, 34), (-9, 22),
             (-13 + tail_wave, 10)], False)
        poly(p["robe_mid"], [(-9, -4), (9, -4),
             (8 + tail_wave, 8), (6, 18), (2, 28),
             (-1, 33), (-4, 27), (-7, 16),
             (-9 + tail_wave, 8)], False)
        _NS_vex._aaline(surface, p["robe_weave"], pt(-5, 0),
                        pt(-4 + tail_wave, 20), 1)
        _NS_vex._aaline(surface, p["robe_weave"], pt(5, 0),
                        pt(4 + tail_wave, 20), 1)
        _NS_vex._aaline(surface, p["robe_light"], pt(-13, -4),
                        pt(-15 + tail_wave, 10), 1)
        _NS_vex._aaline(surface, p["robe_high"], pt(-9, -2),
                        pt(-11 + tail_wave, 8), 1)
        for i in range(7):
            tx = -12 + i * 4
            ty = 30 + int(math.sin(phase * 1.2 + i) * 2)
            ln = 8 + (i % 3) * 3
            poly(p["robe_darkest"], [(tx - 2, 26), (tx + 2, 26),
                 (tx + 1, ty + ln), (tx - 1, ty + ln)], False)
            _NS_vex._aacircle(surface, (*p["void_dark"], 150),
                              pt(tx, ty + ln), 1)
        # glowing runes down the robe front
        for i, off in enumerate((-7, 0, 7)):
            gx, gy = off, 14
            _NS_vex._aaline(surface, (*p["void_mid"], 200),
                            pt(gx, gy - 4), pt(gx, gy + 4), 1)
            _NS_vex._aacircle(surface, p["void_hot"], pt(gx, gy), 2)

        # Spectral greaves / hover foot solver.  Vex tetap melayang,
        # tetapi dua sabaton bayangan punya fase menapak/terangkat agar
        # walk terbaca sebagai langkah, bukan sticker translation.
        front_step = int(stride * 6) if walk else 0
        rear_step = -front_step
        if attack:
            front_step += int(ap * 6)
            rear_step -= int(ap * 3)
        stride_vel = math.cos(phase * 1.72) if walk else 0.0
        front_lift = int(max(0.0, stride_vel) * 8) if walk else 0
        rear_lift = int(max(0.0, -stride_vel) * 8) if walk else 0
        for side, step, lift, base_col in ((-1, rear_step, rear_lift, p["robe_dark"]),
                                           ( 1, front_step, front_lift, p["robe_mid"])):
            hx = side * 7 + int(step * .25)
            kx = side * 9 + int(step * .55)
            fx = side * 12 + step
            # upper spectral shin behind the robe slit
            poly(p["shadow_deep"], [(hx - 4, 13), (hx + 4, 13),
                 (kx + 4, 30 - lift), (kx - 4, 30 - lift)], False)
            poly(base_col, [(hx - 3, 14), (hx + 3, 14),
                 (kx + 3, 29 - lift), (kx - 3, 29 - lift)], False)
            # angular sabaton with bright toe cluster
            poly(p["armor_darkest"], [(kx - 6, 30 - lift),
                 (kx + 6, 30 - lift), (fx + 9, 42 - lift),
                 (fx + 2, 47 - lift), (fx - 8, 42 - lift)], False)
            poly(p["armor_mid"], [(kx - 4, 32 - lift),
                 (kx + 4, 32 - lift), (fx + 6, 41 - lift),
                 (fx + 1, 44 - lift), (fx - 5, 41 - lift)], False)
            _NS_vex._aaline(surface, p["armor_rim"],
                            pt(kx - 3, 32 - lift), pt(fx + 2, 42 - lift),
                            max(1, sw(1)))
            _NS_vex._aacircle(surface, p["void_hot"], pt(fx + 4, 41 - lift),
                              max(1, sw(1)), False)
            if lift == 0:
                foot = pt(fx, 48)
                _NS_vex._ellipse(surface, (*p["void_darkest"], 56),
                                  (foot[0] - sw(15), foot[1] - sw(2),
                                   sw(30), sw(6)), 0)
                if walk and abs(stride_vel) < .45:
                    for k in range(3):
                        _NS_vex._aacircle(
                            surface, (*p["void_mid"], 110 - k * 28),
                            (foot[0] - f * (k + 1) * sw(5),
                             foot[1] - k * sw(2)), max(1, sw(2 - k * .35)))

        # Torso armor with central void gem.
        poly(p["armor_darkest"], [(-13, -18), (13, -18),
             (12, 8), (5, 14), (-5, 14), (-12, 8)])
        poly(p["armor_dark"], [(-11, -16), (11, -16),
             (10, 6), (4, 12), (-4, 12), (-10, 6)], False)
        poly(p["armor_mid"], [(-8, -13), (8, -13),
             (7, 4), (3, 9), (-3, 9), (-7, 4)], False)
        _NS_vex._aaline(surface, p["armor_light"], pt(-11, -16),
                        pt(-10, 4), 1)
        _NS_vex._aaline(surface, p["armor_shine"], pt(-9, -15),
                        pt(-2, -15), 1)
        _NS_vex._aaline(surface, p["shadow_deep"], pt(-6, -15),
                        pt(0, -2), 2)
        _NS_vex._aaline(surface, p["shadow_deep"], pt(6, -15),
                        pt(0, -2), 2)
        gem_pulse = math.sin(phase * 1.5) * .3 + .7
        dot(p["armor_darkest"], 0, 2, 5, False)
        _NS_vex._aacircle(surface, (*p["void_dark"], int(200 * gem_pulse)),
                          pt(0, 2), 4)
        _NS_vex._aacircle(surface, (*p["void_mid"], int(235 * gem_pulse)),
                          pt(0, 2), 3)
        _NS_vex._aacircle(surface, p["void_hot"], pt(0, 1), 2)
        _NS_vex._aacircle(surface, p["white"], pt(0, 1), 1)

        # Pixel-art dither band & specular clusters (key light kiri-atas).
        for i, (dx_, dy_) in enumerate(((-8, -9), (-4, -6), (2, -10),
                                        (6, -5), (-1, 7), (5, 5))):
            col = p["robe_dither"] if i % 2 else p["armor_light"]
            _NS_vex._aacircle(surface, col, pt(dx_, dy_), max(1, sw(.8)), False)
        _NS_vex._aaline(surface, p["armor_shine"], pt(-8, -13),
                        pt(-1, -14), max(1, sw(1)))
        if overcharge or astralized:
            glow_col = p["astral_bright"] if astralized else p["void_gold"]
            _NS_vex._aacircle(surface, (*glow_col, 110), pt(0, 2), sw(9))
            _NS_vex._aaline(surface, glow_col, pt(-6, -15), pt(0, 0),
                            max(1, sw(1)))
            _NS_vex._aaline(surface, glow_col, pt(6, -15), pt(0, 0),
                            max(1, sw(1)))

        # Spiky pauldrons (armor plating with rising spike + rune).
        for side in (-1, 1):
            sx = side * 14
            poly(p["armor_darkest"], [(sx - 6, -20), (sx + 6, -20),
                 (sx + 7, -10), (sx, -6), (sx - 7, -10)])
            poly(p["armor_dark"], [(sx - 5, -19), (sx + 5, -19),
                 (sx + 6, -11), (sx, -8), (sx - 6, -11)], False)
            poly(p["armor_mid"], [(sx - 3, -18), (sx + 3, -18),
                 (sx + 4, -12), (sx, -10), (sx - 4, -12)], False)
            poly(p["armor_darkest"], [(sx - 2, -20), (sx, -33),
                 (sx + 2, -20)])
            _NS_vex._aaline(surface, p["armor_shine"],
                            pt(sx - 1, -20), pt(sx, -30), 1)
            _NS_vex._aacircle(surface, (*p["void_bright"], 180),
                              pt(sx, -13), 1)

        # Neck.
        poly(p["skin_darkest"], [(-4, -18), (4, -18), (4, -10), (-3, -10)])
        poly(p["skin_mid"], [(-2, -18), (3, -18), (3, -11), (-2, -11)],
             False)

        # Pose-driven diagonal void staff + multi-keyframe smear.
        butt = _NS_vex._staff_butt_local(phase, action, ap)
        orb = _NS_vex._orb_tip_local(phase, action, ap)
        grip = _NS_vex._staff_grip_local(phase, action, ap)
        # Smear ayunan di-canvas adalah FALLBACK: kalau lapisan hidup
        # (heroes/vex_fx.py) sudah mengambil alih unit ini, arc staff-nya
        # digambar di layar 1:1 dari histori posisi NYATA (lebih mulus,
        # tidak ikut mengecil & beku bersama cache sprite).  Tanpa modul
        # FX - potret, tooling, build minimal - jalur canvas ini tetap
        # jalan, jadi tidak ada visual yang hilang.
        if attack and 0.26 < ap < 0.86 and not _NS_vex._FX_LIVE.v:
            _NS_vex._draw_staff_smear(surface, cx + lean, cy + root_y,
                                      f, phase, ap, astralized or overcharge)
        _NS_vex._draw_elite_staff(surface, pt, poly, dot, f, butt, orb,
                                  grip, phase, detail, glow=overcharge or astralized)

        # Front staff arm: the fist is derived from the pose-driven grip.
        front_shoulder = (11, -14)
        if attack:
            front_elbow = (grip[0] - 6, grip[1] + 6)
        elif walk:
            front_elbow = (grip[0] - 7, grip[1] + 5 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 7, grip[1] + 6)
        limb(front_shoulder, front_elbow, 6, p["robe_mid"], p["robe_light"])
        limb(front_elbow, grip, 5, p["skin_dark"], p["skin_light"])
        ghx, ghy = pt(*grip)
        _NS_vex._aacircle(surface, p["skin_darkest"], (ghx, ghy), 4)
        _NS_vex._aacircle(surface, p["skin_mid"], (ghx, ghy), 3)

        # Hooded head with shadowed face + glowing eye slit.
        _NS_vex._draw_elite_hood(surface, pt, poly, dot, f, phase,
                                 action, ap, detail)

        # Bright front crown flames (cyan tips).
        _NS_vex._draw_elite_crown(surface, pt, poly, dot, f, phase,
                                  action, back=False, detail=detail)

        # Badan ikut bereaksi ke skill: crest/staff/gem menyala saat buff.
        if overcharge or astralized:
            glow_col = p["astral_bright"] if astralized else p["void_gold"]
            hot_col = p["astral_hot"] if astralized else p["void_hot"]
            for i, (bx, by, tx, ty) in enumerate(((-11, -42, -14, -57),
                                                  (-5, -48, -5, -65),
                                                  (1, -52, 2, -70),
                                                  (8, -44, 12, -58))):
                wig = int(math.sin(phase * 2.1 + i) * 2 * flare)
                _NS_vex._aaline(surface, (*glow_col, 190),
                                pt(bx, by), pt(tx + wig, ty), max(1, sw(2)))
                _NS_vex._aacircle(surface, hot_col, pt(tx + wig, ty), sw(1), False)
            # little orbital glints around chest crest
            for i in range(4):
                a = phase * 2.6 + i * math.pi / 2
                _NS_vex._aacircle(surface, (*hot_col, 210),
                                  (pt(0, -8)[0] + int(math.cos(a) * sw(10)),
                                   pt(0, -8)[1] + int(math.sin(a) * sw(5))), sw(1))

        if detail:
            _NS_vex._draw_vex_masterwork_details(
                surface, pt, poly, dot, f, phase, action)


    # -------------------------------------------------------------------
    # Void-flame crown
    # -------------------------------------------------------------------
    def _draw_elite_crown(surface, pt, poly, dot, f, phase, action,
                          back=False, detail=False):
        """Void-flame crown: connected burning crest hugging the hood."""
        p = _NS_vex.PALETTE
        if back:
            # Solid void volume behind the hood so the flames never float.
            poly(p["void_darkest"], [(-15, -24), (-17, -34), (-12, -44),
                 (0, -50), (12, -44), (17, -34), (15, -24), (8, -18),
                 (-8, -18)])
            poly(p["void_dark"], [(-12, -26), (-14, -34), (-10, -42),
                 (0, -47), (10, -42), (14, -34), (12, -26), (6, -20),
                 (-6, -20)], False)
            poly(p["void_mid"], [(-8, -28), (-10, -34), (-7, -40),
                 (0, -44), (7, -40), (10, -34), (8, -28), (4, -22),
                 (-4, -22)], False)
            return
        # ONE connected flaming crest silhouette (bukan jarum terpisah):
        # gelombang api menyapu ke belakang dengan 4 puncakan berlekuk.
        crest = [(-16, -26), (-18, -34), (-13, -40), (-11, -48),
                 (-8, -41), (-5, -52), (-2, -43), (1, -56), (4, -44),
                 (7, -50), (9, -40), (13, -44), (15, -34), (16, -26),
                 (10, -20), (-10, -20)]
        sway = int(math.sin(phase * 1.1) * 1)

        def lift(q):
            return (q[0] + (sway if q[1] < -40 else 0), q[1])

        poly(p["void_darkest"], [lift(q) for q in crest])

        def inner(scale):
            out = []
            for x, y in crest:
                out.append((int(x * scale), int(-28 + (y + 28) * scale)))
            return out

        poly(p["void_dark"], inner(0.82), False)
        poly(p["void_mid"], inner(0.62), False)
        poly(p["void_light"], inner(0.40), False)
        # flame licks on the two tallest notches + bright beads
        for tx, ty in ((-5, -52), (1, -56)):
            x, y = pt(tx + sway, ty)
            _NS_vex._aacircle(surface, p["crown_tip"], (x, y), 1)
        # side horns curving out from the temples
        for side in (-1, 1):
            poly(p["void_darkest"], [(side * 14, -30), (side * 24, -27),
                 (side * 20, -22), (side * 13, -24)])
            poly(p["void_mid"], [(side * 15, -28), (side * 22, -26),
                 (side * 18, -24)], False)
        _NS_vex._aaline(surface, p["crown_rim"], pt(-12, -31),
                        pt(6, -33), 1)


    # -------------------------------------------------------------------
    # Diagonal void staff
    # -------------------------------------------------------------------
    def _draw_elite_staff(surface, pt, poly, dot, f, butt, orb, grip,
                          phase, detail, glow=False):
        p = _NS_vex.PALETTE
        rs = _NS_vex.RIG_SCALE
        sw = lambda v: max(1, int(round(v * rs)))
        bx, by = pt(*butt)
        ox, oy = pt(*orb)
        # Selout + 4-band shaft, key light kiri-atas.
        _NS_vex._aaline(surface, p["shadow_deep"],
                        (bx + f * sw(2), by + sw(1)),
                        (ox + f * sw(2), oy + sw(1)), sw(7))
        _NS_vex._aaline(surface, p["staff_dark"], (bx, by), (ox, oy), sw(5))
        _NS_vex._aaline(surface, p["staff_mid"], (bx - f, by), (ox - f, oy), sw(3))
        _NS_vex._aaline(surface, p["staff_light"],
                        (bx - f * sw(1), by - sw(.5)),
                        (ox - f * sw(1), oy - sw(.5)), sw(1))
        _NS_vex._aaline(surface, (*p["rune_mid"], 190),
                        (bx + f, by - sw(1)), (ox + f, oy - sw(1)), sw(1))
        # Rune collars on shaft.
        for t in (.22, .42, .64, .82):
            rx = int(bx + (ox - bx) * t)
            ry = int(by + (oy - by) * t)
            _NS_vex._aacircle(surface, p["armor_darkest"], (rx, ry), sw(3))
            _NS_vex._aacircle(surface, p["armor_mid"], (rx - f, ry - 1), sw(2))
            _NS_vex._aacircle(surface, p["void_bright"], (rx - f, ry - 1), sw(1))
        # Crescent claw cradle around the orb (larger v2 silhouette).
        for side in (-1, 1):
            prev = (int(bx + (ox - bx) * .88), int(by + (oy - by) * .88))
            for i in range(1, 7):
                t = i / 6.0
                cx2 = ox + side * math.sin(t * math.pi) * sw(7)
                cy2 = oy + (1 - t) * sw(11) - t * sw(3)
                _NS_vex._aaline(surface, p["staff_dark"], prev,
                                (cx2 + f, cy2), sw(3))
                _NS_vex._aaline(surface, p["staff_shine"], prev,
                                (cx2, cy2), sw(1))
                prev = (cx2, cy2)
        pulse = .74 + math.sin(phase * 2.5) * .20
        glow_boost = 1.45 if glow else 1.0
        for radius, color, alpha in ((14, p["void_dark"], 58),
                                     (10, p["void_mid"], 118),
                                     (7, p["void_light"], 192),
                                     (4, p["void_bright"], 230)):
            _NS_vex._aacircle(surface, (*color, min(255, int(alpha * pulse * glow_boost))),
                              (ox, oy), sw(radius))
        # Faceted orb core + specular cluster.
        _NS_vex._poly(surface, p["void_darkest"], [
            (ox, oy - sw(6)), (ox + f * sw(6), oy - sw(1)),
            (ox + f * sw(2), oy + sw(7)), (ox - f * sw(6), oy + sw(2))])
        _NS_vex._poly(surface, p["void_mid"], [
            (ox, oy - sw(4)), (ox + f * sw(4), oy - sw(1)),
            (ox + f, oy + sw(5)), (ox - f * sw(4), oy + sw(1))])
        _NS_vex._aacircle(surface, p["void_hot"], (ox - f, oy - sw(1)), sw(3))
        _NS_vex._aacircle(surface, p["void_white"], (ox - f * sw(2), oy - sw(2)), sw(2))
        _NS_vex._aacircle(surface, p["white"], (ox - f * sw(2), oy - sw(3)), sw(1))
        # Glint orbit di ujung projectile anchor.
        for i in range(4 if glow else 3):
            a = phase * (2.2 if glow else 2.0) + i * math.tau / (4 if glow else 3)
            rr = sw(11 if glow else 9)
            sx = int(ox + math.cos(a) * rr)
            sy = int(oy + math.sin(a) * rr)
            _NS_vex._aacircle(surface, p["orb_satellite"], (sx, sy), sw(1))
            if glow and i % 2 == 0:
                _NS_vex._aacircle(surface, p["white"], (sx, sy), sw(1))


    # -------------------------------------------------------------------
    # Hooded head + shadowed face
    # -------------------------------------------------------------------
    def _draw_elite_hood(surface, pt, poly, dot, f, phase, action, ap,
                         detail):
        p = _NS_vex.PALETTE
        poly(p["robe_darkest"], [(-11, -46), (0, -52), (11, -46),
             (15, -34), (14, -22), (7, -16), (0, -14),
             (-7, -16), (-14, -22), (-15, -34)])
        poly(p["robe_dark"], [(-9, -44), (0, -49), (9, -44),
             (12, -34), (11, -24), (6, -19), (0, -17),
             (-6, -19), (-11, -24), (-12, -34)], False)
        poly(p["robe_mid"], [(-6, -42), (0, -46), (6, -42),
             (8, -34), (7, -26), (2, -21), (-2, -21),
             (-7, -26), (-8, -34)], False)
        peak = int(math.sin(phase * 1.1) * 2)
        poly(p["robe_darkest"], [(0, -51), (4, -54),
             (-8, -53 + peak), (-16, -46 + peak), (-8, -44)])
        _NS_vex._aaline(surface, p["robe_light"], pt(-12, -34),
                        pt(-7, -17), 1)
        _NS_vex._aaline(surface, p["robe_high"], pt(-10, -42),
                        pt(-13, -30), 1)
        # shadowed void face
        poly(p["face_dark"], [(-7, -38), (0, -41), (7, -38),
             (9, -30), (7, -24), (0, -22), (-7, -24), (-9, -30)])
        # glowing cyan eye SLIT (brighter while attacking)
        glow = action in ("attack",) or ap > .35
        ex, ey = pt(0, -30)
        _NS_vex._aacircle(surface, (*p["void_dark"], 140), (ex, ey), 5)
        _NS_vex._aaline(surface, p["eye_glow"], pt(-4, -30), pt(4, -30), 3)
        _NS_vex._aaline(surface, p["void_hot"], pt(-3, -30), pt(3, -30), 1)
        if glow:
            _NS_vex._aaline(surface, p["eye_bright"], pt(-2, -30),
                            pt(2, -30), 1)
            _NS_vex._aacircle(surface, p["white"], (ex - f, ey - 1), 1)
        _NS_vex._aaline(surface, p["robe_darkest"], pt(-3, -24),
                        pt(3, -24), 2)


    # -------------------------------------------------------------------
    # Portrait-only LOD pass (extra material detail; arena LOD stays cheap)
    # -------------------------------------------------------------------
    def _draw_vex_masterwork_details(surface, pt, poly, dot, f, phase,
                                     action):
        p = _NS_vex.PALETTE
        for i in range(4):
            _NS_vex._aaline(surface, p["crown_rim"],
                            pt(-12 + i * 8, -29),
                            pt(-12 + i * 8, -34 - (i % 2) * 5), 1)
        for yy in (-40, -35, -30):
            _NS_vex._aacircle(surface, p["robe_light"], pt(-9, yy), 1)
            _NS_vex._aacircle(surface, p["robe_light"], pt(9, yy), 1)
        for i in range(4):
            y = 4 + i * 6
            _NS_vex._aaline(surface, p["robe_mid"], pt(-6, y),
                            pt(6, y + 2), 1)
        for t in (.3, .62):
            ox, oy = _NS_vex._orb_tip_local(phase, action)
            bx, by = _NS_vex._staff_butt_local(phase, action)
            rx = int(bx + (ox - bx) * t)
            ry = int(by + (oy - by) * t)
            _NS_vex._aacircle(surface, p["rune_trace"], pt(rx, ry), 1)
        for i in range(4):
            t = (phase * .4 + i / 4.0) % 1.0
            dx = -10 + i * 6 + int(math.sin(phase * 1.3 + i) * 2)
            dy = 10 - int(t * 48)
            _NS_vex._aacircle(surface,
                              (*p["void_bright"], int(180 * (1 - t))),
                              pt(dx, dy), 1)
    # -------------------------------------------------------------------
    # Attack smear / impact FX (body-scale, not baked projectiles)
    # -------------------------------------------------------------------
    def _draw_staff_smear(surface, cx, cy, facing, phase, ap, overcharged=False):
        """Smear berlapis mengikuti ujung staff pada keyframe sebelumnya."""
        p = _NS_vex.PALETTE
        fade = 1.0
        if ap > _NS_vex.ATTACK_SWING_END:
            fade = max(0.0, 1.0 - (ap - _NS_vex.ATTACK_SWING_END) / .26)
        if fade <= .02:
            return
        span = min(.22, max(.04, ap - _NS_vex.ATTACK_WINDUP_END))
        layers = (
            (p["void_dark"], 13, 70),
            (p["void_mid"], 9, 130),
            (p["void_light"], 5, 190),
            (p["void_hot"] if overcharged else p["void_bright"], 3, 235),
        )
        for i in range(5):
            t = (i + 1) / 10.0
            p_back = max(0.0, ap - span * (1.0 - t))
            hx, hy = _NS_vex._staff_orb_position(cx, cy, facing, phase,
                                                  "attack", p_back)
            taper = .35 + .65 * (t ** 1.8)
            for col, radius, alpha in layers:
                _NS_vex._aacircle(surface, (*col, int(alpha * fade * t)),
                                  (hx, hy), max(1, int(radius * taper)))
        hx, hy = _NS_vex._staff_orb_position(cx, cy, facing, phase,
                                              "attack", ap)
        _NS_vex._spark_star(surface, hx, hy, int(14 * fade),
                            p["void_bright"], int(210 * fade),
                            spikes=6, rot=phase, core=p["void_white"])


    def _draw_staff_impact_flash(surface, x, y, facing, progress, phase=0.0):
        """Frame IMPACT: shockwave kecil + bintang di ujung orb staff."""
        if progress < .48 or progress > .70:
            return
        p = _NS_vex.PALETTE
        t = 1.0 - abs(progress - _NS_vex.ATTACK_IMPACT) / .14
        t = max(0.0, min(1.0, t))
        hx, hy = _NS_vex._staff_orb_position(x, y, facing, phase,
                                              "attack", progress)
        rr = int(8 + 24 * t)
        _skill_outlined_circle(surface, (hx, hy), rr, 3,
                               p["void_light"], int(190 * t))
        _NS_vex._spark_star(surface, hx, hy, int(18 + 16 * t),
                            p["void_bright"], int(235 * t),
                            spikes=8, rot=phase * 1.7, core=p["white"])
        for i in range(7):
            a = phase * .5 + i * math.tau / 7
            r = int(16 + 22 * t)
            sx = int(hx + math.cos(a) * r)
            sy = int(hy + math.sin(a) * r * .82)
            _NS_vex._aacircle(surface, (*p["void_hot"], int(200 * t)), (sx, sy), 2)
            _NS_vex._aacircle(surface, p["white"], (sx, sy), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_void(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Void mist beneath Vex (base mist cached, motes live)."""
        p = _NS_vex.PALETTE
        strength = 1.45 if intense else 1.0

        def build_mist():
            mist = pygame.Surface((170, 58), pygame.SRCALPHA)
            for radius in range(40, 4, -4):
                alpha = int((40 - radius) * 2.35)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*p["void_dark"], min(255, alpha)),
                        (85 - radius * 2, 30 - radius // 3,
                         radius * 4, max(4, radius // 2)),
                    )
            pygame.draw.ellipse(mist, (*p["astral_dark"], 36),
                                (22, 24, 126, 14), 1)
            return mist

        mist = _NS_vex._static("vex_mist_v2", build_mist)
        pulse = math.sin(phase * 1.0) * 0.22 + 0.78
        if pulse < .96:
            faded = mist.copy()
            faded.set_alpha(int(255 * pulse * min(1.0, strength)))
            surface.blit(faded, (cx - 85, cy - 24))
        else:
            surface.blit(mist, (cx - 85, cy - 24))

        # Rising motes/embers, deterministic phase offsets.
        n = 7 if intense else 5
        for i in range(n):
            t = (phase * 0.36 + i / float(n)) % 1.0
            sx = cx - 34 + i * (68 // max(1, n - 1)) + int(math.sin(phase + i) * 5)
            sy = cy + 8 - int(t * 44)
            alpha = max(0, min(255, int(210 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_vex._aacircle(surface, (*p["void_dark"], alpha), (sx, sy), 5)
            _NS_vex._aacircle(surface, (*p["void_mid"], alpha), (sx, sy - 2), 3)
            _NS_vex._aacircle(surface, (*p["void_bright"], alpha), (sx, sy - 3), 1)

        # Orbiting rune fragments around the hover base.
        for i in range(5):
            angle = phase * .92 + i * math.tau / 5
            r = 30 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_vex._aacircle(surface, p["void_dark"], (sx, sy), 3)
            _NS_vex._aacircle(surface, p["void_mid"], (sx, sy), 2)
            _NS_vex._aacircle(surface, p["void_bright"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 135 - i * 24)
                _NS_vex._aacircle(surface, (*p["void_mid"], alpha),
                                  (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow (cached)."""
        p = _NS_vex.PALETTE
        def build_shadow():
            shadow = pygame.Surface((150, 34), pygame.SRCALPHA)
            for radius in range(15, 0, -1):
                alpha = max(0, (15 - radius) * 14)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (15 - radius, 17 - radius, 120 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*p["void_darkest"], 64),
                                (11, 8, 128, 14))
            return shadow
        surface.blit(_NS_vex._static("vex_shadow_v2", build_shadow),
                     (x - 75, y - 17))


    def _draw_void_silhouette_glow(surface, x, y, phase):
        """Layered cyan rim light behind the taller v2 silhouette."""
        p = _NS_vex.PALETTE
        def build_halo():
            halo = pygame.Surface((168, 190), pygame.SRCALPHA)
            for radius, alpha in ((70, 8), (54, 14), (39, 22)):
                _NS_vex._aacircle(halo, (*p["void_dark"], alpha),
                                  (84, 95), radius)
            _NS_vex._aaline(halo, (*p["void_mid"], 38), (57, 118), (29, 58), 3)
            _NS_vex._aaline(halo, (*p["void_mid"], 34), (110, 92), (139, 48), 2)
            return halo
        halo = _NS_vex._static("vex_silhouette_halo_v2", build_halo)
        pulse = int(170 + math.sin(phase * 1.4) * 42)
        halo.set_alpha(pulse)
        surface.blit(halo, (x - 84, y - 95))


    def _draw_void_aura(surface, x, y, phase):
        """Large background aura (cached base)."""
        p = _NS_vex.PALETTE
        def build_aura():
            aura = pygame.Surface((250, 220), pygame.SRCALPHA)
            for radius in range(96, 7, -5):
                alpha = int((96 - radius) * .95)
                if alpha > 0:
                    _NS_vex._aacircle(aura, (*p["void_darkest"], min(255, alpha)),
                                      (125, 110), radius)
            return aura
        aura = _NS_vex._static("vex_aura_v2", build_aura)
        pulse = math.sin(phase * .42) * .22 + .78
        faded = aura.copy()
        faded.set_alpha(int(255 * pulse))
        surface.blit(faded, (x - 125, y - 110))


    def _draw_void_platform(surface, x, y, phase, skill):
        """Runic void circle on ground (cached base + rotating runes)."""
        p = _NS_vex.PALETTE
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        def build_platform():
            ring = pygame.Surface((190, 64), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*p["void_dark"], 170),
                                (7, 15, 176, 34), 3)
            pygame.draw.ellipse(ring, (*p["void_mid"], 190),
                                (30, 20, 130, 24), 2)
            pygame.draw.ellipse(ring, (*p["astral_dark"], 80),
                                (48, 23, 94, 18), 1)
            return ring
        ring = _NS_vex._static("vex_platform_v2", build_platform)
        surface.blit(ring, (x - 95, y - 32))

        for i in range(5):
            angle = phase * 0.22 + i * math.tau / 10
            x1 = x + int(math.cos(angle) * 34)
            y1 = y + int(math.sin(angle) * 8)
            x2 = x + int(math.cos(angle) * 72)
            y2 = y + int(math.sin(angle) * 15)
            pygame.draw.line(surface, (*p["void_light"], 170),
                             (x1, y1), (x2, y2), 1)
        for i in range(4):
            angle = phase * .35 + i * math.pi / 2
            sx = x + int(math.cos(angle) * 71)
            sy = y + int(math.sin(angle) * 15)
            pygame.draw.circle(surface, (*p["void_hot"], 220), (sx, sy), 2)

        if skill:
            color = (p["astral_light"] if skill == "e" else
                     (p["void_magma"] if skill == "r" else p["void_bright"]))
            pygame.draw.ellipse(surface, (*color, int(120 * pulse)),
                                (x - 78, y - 24, 156, 48), 2)


    def _draw_orb_release_flash(surface, x, y, facing, progress, phase=0.0):
        """Flash when arcane orb is released."""
        if progress < 0.4 or progress > 0.7:
            return
        t = (progress - 0.4) / 0.3
        intensity = math.sin(t * math.pi)

        flash_x, flash_y = _NS_vex._staff_orb_position(
            x, y, facing, phase, "attack", progress)

        alpha = int(200 * intensity)
        radius = int(6 + intensity * 16)

        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                  (flash_x, flash_y), max(1, radius // 4))

        # Small streaks
        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_vex._aaline(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                    (flash_x, flash_y), (ex, ey), 1)


    # ===================================================================
    # SKILL FX v3.0 — VOID ASTRAL CINEMATIC (world-space, 3 fase)
    # -------------------------------------------------------------------
    # Standar rewrite (setara disiplin rig masterwork):
    #   * 100% primitif pygame — tanpa PNG / sprite sheet / image.load.
    #   * Ramp 4-5 band + selout gelap di tiap telegraph supaya tetap
    #     terbaca di terrain terang maupun gelap.
    #   * 3 fase per skill: AKTIVASI (burst/pilar) -> STEADY (loop hidup:
    #     rune berputar, shard faset, mote, accretion) -> RELEASE
    #     (konvergen + fade). Semua deterministik dari (progress, phase).
    #   * Radius gameplay dikompensasi 1/_render_scale (lihat _ring_r):
    #     W tetap 60 px dunia, R tetap 180 px dunia di semua ukuran cache.
    # ===================================================================
    def _skill_progress(skill, timer):
        dur = float(_NS_vex.SKILL_VISUAL_DURATION.get(skill, max(1, timer or 1)))
        return max(0.0, min(1.0, 1.0 - float(timer) / dur))

    def _skill_steady(progress, tail=5.0, floor=.25):
        """Amplop fade akhir skill: plateau 1.0 lalu melandai ke floor."""
        return max(floor, min(1.0, (1.0 - progress) * tail + .3))


    # ===================================================================
    # SKILL Q: ARCANE ORB — arcane conduit + portal collapse
    # ===================================================================
    def _draw_arcane_orb_telegraph(surface, boss, x, y, timer, phase):
        """Q ground FX v3: aperture iris di ujung staff, conduit beam
        beralir energi (3 lapis + filament + paket + rune node), dan
        portal collapse di target (iris petals + sigil + bracket)."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("q", timer)
        steady = _NS_vex._skill_steady(progress)
        facing = getattr(boss, "direction", 1)
        sx, sy = _NS_vex._staff_orb_position(x, y, facing, phase, "idle", 0.0)
        tx, ty = _NS_vex._target_position(boss, x, y)
        pulse = math.sin(phase * 4.0) * .5 + .5

        # ── AKTIVASI: aperture iris + pilar cahaya di ujung staff ──
        if progress < .20:
            t = progress / .20
            rr = int((14 + 58 * t) * fs)
            _skill_outlined_circle(surface, (sx, sy), rr, 3,
                                   p["void_light"], int(220 * (1 - t)))
            if int(phase * 24) % 2 == 0:
                _skill_outlined_circle(surface, (sx, sy),
                                       max(4, int(rr * .55)), 2,
                                       p["void_hot"], int(205 * (1 - t)))
            _NS_vex._spark_star(surface, sx, sy,
                                int(26 * fs * (1 - t * .4)),
                                p["void_bright"], int(245 * (1 - t)),
                                spikes=8, rot=phase, core=p["white"])
            top = max(3, sy - int(min(100 * fs, 220)))
            for wd, col, al in ((22, p["void_dark"], 85),
                                (12, p["void_mid"], 130),
                                (5, p["void_hot"], 210)):
                _NS_vex._aaline(surface, (*col, int(al * (1 - t))),
                                (sx, top), (sx, sy), max(1, int(wd * fs * .45)))

        # ── STEADY: conduit beam 12 segmen + filament + paket energi ──
        dx, dy = tx - sx, ty - sy
        dist = math.hypot(dx, dy) or 1.0
        ang = math.atan2(dy, dx)
        nx, ny = -dy / dist, dx / dist
        pts = []
        for i in range(6):
            t1 = i / 12.0
            wob = math.sin(phase * 3.0 + i * .8) * 3.2 * fs
            pts.append((sx + dx * t1 + nx * wob, sy + dy * t1 + ny * wob))
        beam_a = int((120 + 70 * pulse) * steady)
        for i in range(6):
            _NS_vex._beam3(surface, pts[i], pts[i + 1], 2,
                           (p["void_light"], p["void_dark"], p["void_hot"]),
                           beam_a)
        for sgn in (-1, 1):
            for i in range(0, 11, 3):
                a_ = (pts[i][0] + nx * sgn * 5 * fs,
                      pts[i][1] + ny * sgn * 5 * fs)
                b_ = (pts[i + 2][0] + nx * sgn * 5 * fs,
                      pts[i + 2][1] + ny * sgn * 5 * fs)
                _skill_outlined_line(surface, a_, b_, 1,
                                     p["void_dark"], int(85 * steady))
        for k in range(3):
            t = (progress * 1.7 + k / 3.0) % 1.0
            wob = math.sin(phase * 3.0 + k * 2.1) * 3 * fs
            ex = int(sx + dx * t + nx * wob)
            ey = int(sy + dy * t + ny * wob)
            _NS_vex._aacircle(surface, (*p["void_hot"], int(230 * steady)),
                              (ex, ey), max(1, int(2.5 * fs)))
            _NS_vex._aacircle(surface, p["white"], (ex, ey), 1)
        for i, tt in enumerate((.25, .5, .75)):
            _NS_vex._rune_glyph(surface, sx + dx * tt, sy + dy * tt,
                                max(3, int(5 * fs)),
                                i * 2 + int(phase * 2),
                                p["void_bright"],
                                int((150 + 70 * pulse) * steady), rot=ang)
        for i in range(4):
            tt = ((i + 1) / 5.0 + phase * .28) % 1.0
            _NS_vex._chevron(surface, sx + dx * tt, sy + dy * tt, ang,
                             max(8, int(10 * fs)), p["void_hot"],
                             int((175 + 55 * pulse) * steady), 2)

        # ── TELEGRAPH: portal collapse di target ──
        targ_r = max(12, int(22 * fs))
        _NS_vex._ellipse(surface, (*p["void_darkest"], int(82 * steady)),
                         (int(tx - targ_r * 1.3), int(ty + 12 - targ_r * .32),
                          int(targ_r * 2.6), int(targ_r * .64)), 0)
        _skill_outlined_circle(surface, (tx, ty), targ_r + 5, 3,
                               p["void_mid"], int(150 * steady))
        _skill_outlined_circle(surface, (tx, ty), targ_r, 4,
                               p["void_light"],
                               int((130 + 60 * pulse) * steady))
        _NS_vex._dashed_ring(surface, tx, ty, targ_r + 11,
                             p["void_bright"], int((160 + 60 * pulse) * steady),
                             -phase * 1.1, segments=8, thick=2, span=.42)
        _NS_vex._sigil_ring(surface, tx, ty, targ_r - int(4 * fs),
                            phase * 1.3,
                            (p["void_bright"], p["void_mid"], p["void_hot"]),
                            int(160 * steady), n=6, squash=.55, seed=3,
                            size=max(3, int(4.5 * fs)))
        # Iris petals konvergen — diafragma menutup ke pusat portal.
        conv = (targ_r + 26 * fs) * (1.0 - (progress % .33) * 2.2)
        if conv > targ_r * .35:
            for i in range(6):
                a = phase * .9 + i * math.tau / 6
                bx_ = tx + math.cos(a) * conv
                by_ = ty + math.sin(a) * conv * .8
                tipx = tx + math.cos(a) * conv * .45
                tipy = ty + math.sin(a) * conv * .45 * .8
                ex_ = -math.sin(a) * max(2, int(3 * fs))
                ey_ = math.cos(a) * max(2, int(3 * fs)) * .8
                _NS_vex._dpoly(surface, p["void_hot"], int(125 * steady),
                               [(bx_ - ex_, by_ - ey_),
                                (bx_ + ex_, by_ + ey_), (tipx, tipy)])
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _skill_outlined_line(
                surface,
                (tx + math.cos(da) * (targ_r + 6),
                 ty + math.sin(da) * (targ_r + 6) * .8),
                (tx + math.cos(da) * (targ_r + 13 * fs),
                 ty + math.sin(da) * (targ_r + 13 * fs) * .8),
                2, p["void_bright"], int(150 * steady))
        _NS_vex._draw_glow_orb(surface, tx, ty, max(3, int(5 * fs)),
                               p["void_dark"], p["void_mid"], p["void_hot"],
                               p["white"])
        gy = y + int(60 * fs)
        if gy < surface.get_height():
            _NS_vex._aacircle(surface, (*p["void_bright"], int(110 * steady)),
                              (x, y), max(2, int(6 * fs)))


    def _draw_arcane_orb_charge(surface, boss, x, y, timer, phase):
        """Q foreground FX v3: aperture rune di staff, mote konvergen
        berekor radial, busur energy acak, dan release star."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("q", timer)
        steady = _NS_vex._skill_steady(progress)
        facing = getattr(boss, "direction", 1)
        tip_x, tip_y = _NS_vex._staff_orb_position(x, y, facing, phase,
                                                   "attack", .52)
        pulse = math.sin(phase * 5.0) * .5 + .5

        # Mote konvergen: titik + ekor radial menuju ujung staff.
        for i in range(6):
            t = (progress + i / 12.0 + phase * .08) % 1.0
            a = phase * 3.2 + i * math.tau / 12
            r = (38 - 24 * progress) * fs * (0.75 + 0.25 *
                                             _NS_vex._hash01(i * 19))
            px = int(tip_x + math.cos(a) * r)
            py = int(tip_y + math.sin(a) * r * .82)
            alpha = int((120 + 110 * pulse) * (1.0 - t * .45) * steady)
            _NS_vex._aacircle(surface, (*p["void_mid"], alpha),
                              (px, py), max(1, int(3 * fs)))
            _NS_vex._aacircle(surface, (*p["void_hot"], alpha),
                              (px, py), max(1, int(1.4 * fs)))
            tail = max(2, int(4 * fs))
            pygame.draw.line(
                surface, _NS_vex._rgba(p["void_bright"], alpha * .7),
                (px, py),
                (int(px + (tip_x - px) * tail / max(1.0, r)),
                 int(py + (tip_y - py) * tail / max(1.0, r))), 1)
        # Aperture: sigil ring kontra-rotasi + dashed ganda.
        _NS_vex._sigil_ring(surface, tip_x, tip_y, int(20 * fs),
                            -phase * 1.5,
                            (p["void_bright"], p["void_mid"], p["void_hot"]),
                            int(175 * steady), n=5, squash=.9, seed=7,
                            size=max(2, int(3.4 * fs)))
        _NS_vex._dashed_ring(surface, tip_x, tip_y, int(22 * fs),
                             p["void_bright"], int((170 + 45 * pulse) * steady),
                             phase * 1.7, segments=9, thick=2, span=.45)
        _NS_vex._dashed_ring(surface, tip_x, tip_y, int(13 * fs),
                             p["void_hot"], int((150 + 50 * pulse) * steady),
                             -phase * 1.4, segments=7, thick=1, span=.55)
        # Busur energy sesekali melompat dari mote ke orb.
        for i in range(3):
            if _NS_vex._hash01(i * 53 + int(phase * 9)) > .62:
                a = phase * 3.2 + i * math.tau / 3
                r = 26 * fs
                _NS_vex._energy_arc(surface,
                                    tip_x + math.cos(a) * r,
                                    tip_y + math.sin(a) * r * .82,
                                    tip_x, tip_y, i + int(phase * 9),
                                    p["void_bright"], int(190 * steady),
                                    width=1, wobble=4 * fs)
        if progress > .42:
            t = min(1.0, (progress - .42) / .24)
            _NS_vex._spark_star(surface, tip_x, tip_y,
                                int((18 + 18 * t) * fs),
                                p["void_light"], int(230 * (1 - t * .35)),
                                spikes=8, rot=phase * 2.0,
                                core=p["void_white"])


    # ===================================================================
    # SKILL E: ASTRAL IMPRISONMENT — rantai astral + sangkar collapsar
    # ===================================================================
    def _draw_astral_indicator(surface, boss, x, y, timer, pulse):
        """E ground FX v3: rantai astral staff->target (mata rantai +
        sag + pulsa), footprint rune circle, crosshair, bracket, dan
        pilar aktivasi dengan hujan rune."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("e", timer)
        steady = _NS_vex._skill_steady(progress)
        tx, ty = _NS_vex._target_position(boss, x, y)
        sx, sy = _NS_vex._staff_orb_position(
            x, y, getattr(boss, "direction", 1), pulse, "attack", .45)
        dx, dy = tx - sx, ty - sy
        dist = math.hypot(dx, dy) or 1.0
        ang = math.atan2(dy, dx)
        wave = math.sin(pulse * 4.5) * .5 + .5

        # ── AKTIVASI: pilar astral + hujan rune + star ──
        if progress < .18:
            t = progress / .18
            h = int(min(130 * fs, 230) * (1 - .25 * t))
            top = max(3, ty - h)
            for wd, col, al in ((24, p["astral_dark"], 95),
                                (14, p["astral_mid"], 145),
                                (6, p["astral_bright"], 210)):
                _NS_vex._aaline(surface, (*col, int(al * (1 - t))),
                                (tx, top), (tx, ty + int(16 * fs)),
                                max(1, int(wd * fs * .42)))
            for i in range(3):
                ry = ty - h * (.35 + .55 * _NS_vex._hash01(i * 37))
                _NS_vex._rune_glyph(
                    surface,
                    tx + int((_NS_vex._hash01(i * 41) - .5) * 12 * fs),
                    int(ry), max(2, int(3.5 * fs)), i * 3 + 1,
                    p["astral_bright"], int(235 * (1 - t)),
                    rot=pulse + i)
            _NS_vex._spark_star(surface, tx, ty,
                                int(28 * fs * (1 - t * .3)),
                                p["astral_bright"], int(245 * (1 - t)),
                                spikes=8, rot=pulse, core=p["astral_hot"])

        # ── STEADY: rantai mata-rantai dengan sag sinus ──
        links = 9
        link_pts = []
        nx_, ny_ = -dy / dist, dx / dist
        for i in range(links + 1):
            t1 = i / float(links)
            sag = math.sin(t1 * math.pi) * 6 * fs
            wob = math.sin(pulse * 3.3 + i * .8) * 3 * fs
            link_pts.append((sx + dx * t1 + nx_ * (wob + sag),
                             sy + dy * t1 + ny_ * (wob + sag)))
        for i in range(links):
            mx = (link_pts[i][0] + link_pts[i + 1][0]) * .5
            my = (link_pts[i][1] + link_pts[i + 1][1]) * .5
            la = math.atan2(link_pts[i + 1][1] - link_pts[i][1],
                            link_pts[i + 1][0] - link_pts[i][0])
            _NS_vex._chain_link(surface, mx, my, la,
                                max(4, int(6 * fs)), max(2, int(3 * fs)),
                                p["astral_light"],
                                int((160 + 55 * wave) * steady))
            if i % 3 == 0:
                _NS_vex._aacircle(surface, (*p["astral_hot"],
                                            int(220 * steady)),
                                  (int(mx), int(my)), 1)
        for i in range(2):
            t = (i * .5 + pulse * .5) % 1.0
            _NS_vex._aacircle(surface, p["white"],
                              (int(sx + dx * t), int(sy + dy * t)), 1)
        for i in range(3):
            t = (i / 3.0 + pulse * .44) % 1.0
            _NS_vex._chevron(surface, sx + dx * t, sy + dy * t,
                             ang, int(12 * fs), p["astral_hot"],
                             int(190 * steady), 2)

        # ── TELEGRAPH: footprint penjara + sigil + crosshair + bracket ──
        r = max(12, int(30 * fs))
        _skill_outlined_circle(surface, (tx, ty), r, 3, p["astral_mid"],
                               int(180 * steady))
        _skill_outlined_circle(surface, (tx, ty), max(3, r - int(8 * fs)), 2,
                               p["astral_light"], int(205 * steady))
        _NS_vex._dashed_ring(surface, tx, ty, r + int(8 * fs),
                             p["astral_bright"],
                             int((165 + 50 * wave) * steady),
                             pulse * 1.2, segments=10, thick=2, span=.42)
        _NS_vex._sigil_ring(surface, tx, ty, r - int(4 * fs), pulse * .9,
                            (p["astral_bright"], p["astral_mid"],
                             p["astral_hot"]),
                            int(150 * steady), n=6, squash=.55, seed=11,
                            size=max(3, int(4.5 * fs)))
        conv = int((r + 40 * fs) * (1.0 - (progress % .28) * 2.7))
        if conv > r:
            _skill_outlined_circle(surface, (tx, ty), conv, 2,
                                   p["astral_hot"], int(130 * steady))
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _skill_outlined_line(
                surface,
                (tx + math.cos(da) * (r + 2),
                 ty + math.sin(da) * (r + 2) * .8),
                (tx + math.cos(da) * (r + 13 * fs),
                 ty + math.sin(da) * (r + 13 * fs) * .8),
                2, p["astral_hot"], int(190 * steady))
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            _skill_outlined_line(
                surface,
                (tx + math.cos(a) * (r + 9 * fs),
                 ty + math.sin(a) * (r + 9 * fs) * .8),
                (tx + math.cos(a) * (r + 16 * fs),
                 ty + math.sin(a) * (r + 16 * fs) * .8),
                2, p["astral_light"], int(140 * steady))


    def _handle_astral_skill(surface, boss, x, y, timer, phase):
        """E foreground FX v3: sangkar kaca collapsar — bar rune vertikal
        depan/belakang, kubah glass, shard orbit, mote naik, anchor flare."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("e", timer)
        if (not getattr(boss, "_skip_renderer_projectiles", False)
                and not getattr(boss, "_vx_astral_spawned", False)):
            _NS_vex._spawn_astral_orb(boss, x, y)
            boss._vx_astral_spawned = True
        if timer < 5:
            boss._vx_astral_spawned = False

        tx, ty = _NS_vex._target_position(boss, x, y)
        envelope = min(1.0, progress * 6.0, (1.0 - progress) * 4.0 + .35)
        radius = max(4, int(34 * fs * envelope))
        pulse = .78 + math.sin(phase * 2.4) * .18
        if radius <= 4:
            return

        # ── FOOTPRINT: rune circle di dasar sangkar ──
        _NS_vex._ellipse(surface, (*p["astral_darkest"], int(48 * pulse)),
                         (int(tx - radius * 1.05), int(ty + radius * .28),
                          int(radius * 2.1), int(radius * .7)), 0)
        _NS_vex._dashed_ring(surface, tx, ty + radius * .42,
                             int(radius * 1.05), p["astral_mid"],
                             int(140 * pulse), phase * .8, segments=10,
                             thick=2, span=.4)
        _NS_vex._sigil_ring(surface, tx, ty + radius * .42,
                            int(radius * .8), -phase * .7,
                            (p["astral_bright"], p["astral_mid"],
                             p["astral_hot"]),
                            int(150 * pulse), n=6, squash=.4, seed=5,
                            size=max(2, int(3 * fs)))

        # ── BAR RUNE (belakang kubah -> kubah -> bar depan) ──
        def _cage_bar(a):
            depth = .55 + .45 * (math.sin(a) * .5 + .5)
            bx = int(tx + math.cos(a) * radius * .92)
            by = int(ty + math.sin(a) * radius * .36)
            h = int(radius * (.8 + .3 * depth))
            col = p["astral_bright"] if depth > .8 else p["astral_mid"]
            al = int(200 * pulse * depth)
            _skill_outlined_line(surface,
                                 (bx, by + int(radius * .38)),
                                 (bx, by - h), 2, col, al)
            _NS_vex._aacircle(surface, (*p["astral_hot"], al), (bx, by - h), 1)
            _NS_vex._aacircle(surface, (*p["astral_light"], al),
                              (bx, by + int(radius * .38)), 1)

        for i in range(7):
            a = phase * .45 + i * math.tau / 7
            if math.sin(a) < 0:
                _cage_bar(a)

        # ── KUBAH GLASS: isi + 2 band arc + dashed equator ──
        _NS_vex._aacircle(surface, (*p["astral_dark"], int(52 * pulse)),
                          (tx, ty), radius)
        _NS_vex._arc_band(surface, tx, ty, radius, radius,
                          .18, math.pi - .18, p["astral_bright"],
                          int(200 * pulse), 2, 20)
        _NS_vex._arc_band(surface, tx, ty, radius - 4, radius - 4,
                          math.pi + .2, math.tau - .2, p["astral_mid"],
                          int(150 * pulse), 1, 18)
        _NS_vex._dashed_ring(surface, tx, ty, radius - 2, p["astral_bright"],
                             int(180 * pulse), phase * 1.8, segments=10,
                             thick=2, span=.35)

        for i in range(7):
            a = phase * .45 + i * math.tau / 7
            if math.sin(a) >= 0:
                _cage_bar(a)

        # ── SHARD ORBIT + MOTE NAIK + ANCHOR FLARE ──
        for i in range(5):
            a = phase * 1.6 + i * math.tau / 5
            depth = .6 + .4 * (math.sin(a) * .5 + .5)
            _NS_vex._crystal_shard(
                surface,
                tx + math.cos(a) * radius * .8,
                ty + math.sin(a) * radius * .3 - radius * .35,
                max(2, int(2.2 * fs)), int((7 + 5 * depth) * fs * envelope),
                .5 + .2 * math.sin(phase + i),
                (p["astral_darkest"], p["astral_mid"], p["astral_bright"],
                 p["astral_hot"]),
                int(190 * pulse * depth))
        for i in range(4):
            t = (phase * .38 + i / 8.0) % 1.0
            mx = tx + int(math.sin(phase * 2 + i) * radius * .42)
            my = ty + int(radius * .45) - int(t * radius * 1.3)
            _NS_vex._aacircle(surface,
                              (*p["astral_hot"], int(210 * (1 - t) * pulse)),
                              (mx, my), max(1, int(2 * fs)))
            _NS_vex._aacircle(surface, p["white"], (mx, my), 1)
        _NS_vex._shard_glint(surface, tx, ty - radius, p["astral_hot"],
                             int(200 * pulse), max(2, int(3 * fs)))
        _NS_vex._shard_glint(surface, tx, ty + int(radius * .45),
                             p["astral_light"], int(130 * pulse),
                             max(2, int(2 * fs)))


    # ===================================================================
    # SKILL W: SANITY'S ECLIPSE — gerhana void + mahkota kristal
    # ===================================================================
    def _draw_sanity_eclipse_ground(surface, boss, x, y, timer, phase):
        """W ground FX v3: disk dither + ring 60 px dunia presisi, rune
        kontra-rotasi, retakan zigzag, chevron masuk, dan GERHANA —
        disc void menutup corona seiring progress."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("w", timer)
        steady = _NS_vex._skill_steady(progress)
        pulse = math.sin(phase * 3.0) * .5 + .5
        rng = _NS_vex._ring_r(boss, 60, surface)
        gy = y + int(56 * fs)

        # ── AKTIVASI: ground slam ellipse + shockwave ganda + star ──
        if progress < .18:
            t = progress / .18
            _NS_vex._ellipse(surface, (*p["void_mid"], int(70 * (1 - t))),
                             (int(x - rng * .8 * t - 6),
                              int(gy - rng * .22),
                              int(rng * 1.6 * t + 12),
                              int(rng * .44 * t + 6)), 0)
            for k, mul in enumerate((1.0, .68)):
                rr = int((14 + rng * mul * t))
                _skill_outlined_circle(
                    surface, (x, y), rr, 3,
                    p["void_light"] if k == 0 else p["void_mid"],
                    int((225 if k == 0 else 160) * (1 - t)))
            _NS_vex._spark_star(surface, x, y,
                                int(30 * fs * (1 - t * .35)),
                                p["void_bright"], int(245 * (1 - t)),
                                spikes=8, rot=phase, core=p["white"])

        # ── STEADY: disk dither + ring presisi + rune kontra ──
        _NS_vex._dither_disk(surface, x, gy, int(rng * .66), int(rng * .2),
                             p["void_darkest"],
                             int((70 + 35 * pulse) * steady),
                             phase=phase, seed=17)
        _NS_vex._ellipse(surface,
                         (*p["void_darkest"], int((60 + 30 * pulse) * steady)),
                         (int(x - rng * .68), int(gy - rng * .18),
                          int(rng * 1.36), int(rng * .36)), 0)
        _skill_outlined_circle(surface, (x, y), rng, 4,
                               p["void_light"],
                               int((130 + 60 * pulse) * steady))
        _NS_vex._dashed_ring(surface, x, y, int(rng * .86),
                             p["void_bright"],
                             int((155 + 45 * pulse) * steady),
                             phase * 1.25, segments=12, thick=3, span=.36)
        _NS_vex._sigil_ring(surface, x, gy, int(rng * .58), -phase * .8,
                            (p["void_bright"], p["void_mid"], p["void_hot"]),
                            int((125 + 45 * pulse) * steady), n=8,
                            squash=.34, seed=9, size=max(2, int(3.6 * fs)))

        # ── GERHANA: "matahari hitam" melayang di atas caster — corona
        # void ditutup disc shadow seiring progress (diamond ring flare).
        if progress > .10:
            ec_y = y - int(118 * fs)
            r_e = max(9, int(15 * fs))
            cov = min(1.0, (progress - .10) / .5)
            for k, (rr_, al) in enumerate((
                    (r_e + 7, 55), (r_e + 3, 100), (r_e + 1, 150))):
                _NS_vex._aacircle(surface,
                                  (*p["void_darkest" if k == 0 else
                                    "void_dark" if k == 1 else "void_mid"],
                                   int(al * steady)),
                                  (x, ec_y), rr_)
            # Rim corona tegas (selout gelap + garis terang).
            _skill_outlined_circle(surface, (x, ec_y), r_e + 2, 1,
                                   p["void_light"], int(160 * steady))
            # Sinar corona pendek 6 arah saat gerhana menutup.
            if cov > .35:
                for i in range(6):
                    a = i * math.tau / 6 + .3
                    _NS_vex._aaline(
                        surface, (*p["void_mid"], int(105 * steady)),
                        (int(x + math.cos(a) * (r_e + 4)),
                         int(ec_y + math.sin(a) * (r_e + 4) * .9)),
                        (int(x + math.cos(a) * (r_e + 11)),
                         int(ec_y + math.sin(a) * (r_e + 11) * .9)), 1)
            _NS_vex._aacircle(surface, (*p["void_light"],
                                        int((120 + 60 * pulse) * steady)),
                              (x, ec_y), max(2, r_e - 2))
            # Occluder bergeser masuk lalu menutup penuh (diamond ring).
            off = (1.0 - cov) * 2.0 * r_e
            _NS_vex._aacircle(surface, p["shadow_deep"],
                              (int(x + off), ec_y), int(r_e * .94))
            _NS_vex._aacircle(surface, p["shadow"],
                              (int(x + off), ec_y), max(2, int(r_e * .7)))
            if .3 < cov < .95:
                _NS_vex._shard_glint(surface, x - r_e, ec_y - r_e * .3,
                                     p["void_bright"], int(220 * steady),
                                     max(2, int(3 * fs)), core=True)

        # ── TELEGRAPH: ring konvergen + chevron masuk + retakan ──
        conv = max(10, int(rng * (1.0 - (progress % .25) * 3.1)))
        _skill_outlined_circle(surface, (x, y), conv, 3,
                               p["void_hot"],
                               int((150 + 60 * pulse) * steady))
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _NS_vex._chevron(surface,
                             x + math.cos(da) * rng * .68,
                             y + math.sin(da) * rng * .56,
                             da + math.pi, max(9, int(10 * fs)),
                             p["void_hot"], int(190 * steady), 3)
        for i in range(5):
            ang = i * math.tau / 5 + .25
            _NS_vex._jagged_crack(surface, x, gy, ang,
                                  int((22 + (i % 3) * 8) * fs),
                                  (p["void_darkest"], p["void_mid"]),
                                  int((130 + 40 * pulse) * steady),
                                  i + 41, width=2)


    def _draw_sanity_eclipse(surface, boss, x, y, timer, phase):
        """W foreground FX v3: portal inti accretion mini, mahkota kristal
        faset 2 baris (rotasi lambat + specular), mote jiwa tersedot
        spiral masuk, dan glint orbit."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("w", timer)
        steady = _NS_vex._skill_steady(progress)
        pulse = math.sin(phase * 4.2) * .5 + .5
        rng = _NS_vex._ring_r(boss, 60, surface)
        gy = y + int(56 * fs)
        ramp = (p["void_darkest"], p["void_mid"], p["void_bright"],
                p["void_hot"])

        # Portal core dengan accretion mini.
        _NS_vex._aacircle(surface, (*p["shadow_deep"], 230), (x, gy),
                          int(13 * fs))
        _NS_vex._aacircle(surface, (*p["void_darkest"], 220), (x, gy),
                          int(9 * fs))
        _NS_vex._aacircle(surface, (*p["void_mid"], int(120 + 40 * pulse)),
                          (x, gy), int(5 * fs))
        _NS_vex._arc_band(surface, x, gy, int(16 * fs), int(6 * fs),
                          math.pi * 1.05, math.tau * .98,
                          p["void_mid"], int(150 + 40 * pulse), 1, 12)

        # Mahkota kristal: 2 baris shard faset, tumbuh lalu berputar pelan.
        spike_grow = min(1.0, max(0.0, (progress - .12) / .30))
        rows = ((14, rng * .96, 24), (9, rng * .58, 15))
        for count, rad, height_base in rows:
            for i in range(count):
                ang = phase * (0.18 if count == 14 else -0.22) \
                    + i * math.tau / count
                bx = x + math.cos(ang) * rad
                by = gy + math.sin(ang) * rad * .34
                h = int((height_base + (i % 4) * 4) * fs * spike_grow)
                if h < 3:
                    continue
                _NS_vex._crystal_shard(
                    surface, bx, by,
                    max(2, int((4 if count == 14 else 3) * fs)), h,
                    .18 * math.sin(ang * 2 + i), ramp,
                    int((160 + 55 * pulse) * steady),
                    glint=1 if i % 4 == 0 else 0)
        # Mote jiwa spiral masuk — tersedot ke portal.
        for i in range(5):
            t = (phase * .34 + i / 10.0) % 1.0
            ang = _NS_vex._hash01(i * 29) * math.tau + phase * .5 + t * 1.2
            rr = rng * (.85 - .75 * t)
            mx = int(x + math.cos(ang) * rr)
            my = int(gy + math.sin(ang) * rr * .34 - t * 10 * fs)
            alpha = int(215 * (1 - t) * steady)
            pygame.draw.line(
                surface, _NS_vex._rgba(p["void_bright"], alpha * .5),
                (mx, my),
                (int(mx + math.cos(ang + .8) * 5),
                 int(my + math.sin(ang + .8) * 2)), 1)
            _NS_vex._aacircle(surface, (*p["void_bright"], alpha),
                              (mx, my), max(1, int(2 * fs)))
            if i % 3 == 0:
                _NS_vex._aacircle(surface, p["white"], (mx, my), 1)
        _NS_vex._orbit_glints(surface, x, y, int(rng * .55), int(rng * .28),
                              phase * 2.4, 6, p["void_hot"],
                              int(200 * steady), hot=p["white"])


    # ===================================================================
    # SKILL R: ESSENCE FLUX — event horizon + accretion (ultimate)
    # ===================================================================
    def _draw_essence_flux_ground(surface, boss, x, y, timer, phase):
        """R ground FX v3: ring ultimate 180 px dunia presisi (rim ganda
        magma+gold), rune gold berputar, retakan magma, chevron masuk,
        bracket kompas, dan pilar aktivasi 4-lapis."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("r", timer)
        steady = _NS_vex._skill_steady(progress)
        pulse = math.sin(phase * 2.8) * .5 + .5
        rng = _NS_vex._ring_r(boss, 180, surface)
        gy = y + int(58 * fs)

        # ── AKTIVASI: shockwave triple + nova (TANPA pilar cahaya) ──
        # Pilar 4-lapis setinggi 150 px dari (x, gy) ke (x, top) DIBUANG:
        # kolom itu menutupi badan Vex selama Essence Flux di-cast.
        if progress < .20:
            t = progress / .20
            for k, mul in enumerate((1.0, .58, .30)):
                rr = int((18 + rng * mul * t))
                _skill_outlined_circle(
                    surface, (x, y), rr, 4,
                    p["void_magma"] if k == 0 else
                    (p["void_hot"] if k == 1 else p["void_gold"]),
                    int((235 if k == 0 else
                         (165 if k == 1 else 130)) * (1 - t)))
            _NS_vex._spark_star(surface, x, y,
                                int(38 * fs * (1 - t * .25)),
                                p["void_hot"], int(250 * (1 - t)),
                                spikes=10, rot=phase, core=p["white"])
            _NS_vex._nova(surface, x, y, int(10 * fs),
                          int((46 + 60 * t) * fs), 8, phase * .2,
                          (p["void_magma"], p["void_gold"]),
                          int(210 * (1 - t)))

        # ── STEADY: rim ganda presisi + rune gold + dashed kontra ──
        _skill_outlined_circle(surface, (x, y), rng, 5,
                               p["void_magma"],
                               int((110 + 55 * pulse) * steady))
        _skill_outlined_circle(surface, (x, y), max(6, rng - int(7 * fs)), 2,
                               p["void_gold"],
                               int((120 + 50 * pulse) * steady))
        _NS_vex._dashed_ring(surface, x, y, int(rng * .84),
                             p["void_hot"],
                             int((150 + 60 * pulse) * steady),
                             phase * 1.5, segments=10, thick=3, span=.30)
        _NS_vex._dashed_ring(surface, x, y, int(rng * .58),
                             p["astral_bright"],
                             int((125 + 45 * pulse) * steady),
                             -phase * 1.0, segments=8, thick=2, span=.42)
        _NS_vex._sigil_ring(surface, x, gy, int(rng * .95), phase * .5,
                            (p["void_gold_hot"], p["void_gold"],
                             p["void_hot"]),
                            int((130 + 50 * pulse) * steady), n=10,
                            squash=.3, seed=13,
                            size=max(3, int(4.2 * fs)))
        # TELEGRAPH: ring konvergen besar + bracket kompas gold.
        conv = max(18, int(rng * (1.0 - (progress % .28) * 2.6)))
        _skill_outlined_circle(surface, (x, y), conv, 3,
                               p["void_hot"],
                               int((135 + 55 * pulse) * steady))
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            a0 = da - .12
            _NS_vex._arc_band(surface, x, y, rng + int(10 * fs),
                              int((rng + int(10 * fs)) * .3),
                              a0, a0 + .24, p["void_gold"],
                              int(150 * steady), 2, 4)
        for i in range(6):
            ang = i * math.tau / 6 + .18
            ln = int((42 + (i % 3) * 18) * fs)
            _NS_vex._jagged_crack(surface, x, gy, ang, ln,
                                  (p["shadow_deep"], p["void_magma"]),
                                  int((150 + 45 * pulse) * steady),
                                  i + 71, width=3)
        for i in range(6):
            a = phase * .55 + i * math.tau / 6
            _NS_vex._chevron(surface,
                             x + math.cos(a) * rng * .62,
                             y + math.sin(a) * rng * .50,
                             a + math.pi, max(10, int(12 * fs)),
                             p["void_hot"], int(170 * steady), 3)


    def _draw_essence_flux(surface, boss, x, y, timer, phase):
        """R foreground FX v3: black hole ber-photon-ring, piringan
        accretion miring (band gold+magma depan/belakang), arc lensing,
        nova + ray burst, wisps spiral, ember column, dan glint orbit."""
        p = _NS_vex.PALETTE
        fs = _NS_vex._fx_scale(boss)
        progress = _NS_vex._skill_progress("r", timer)
        steady = _NS_vex._skill_steady(progress)
        pulse = math.sin(phase * 5.0) * .5 + .5
        rng = _NS_vex._ring_r(boss, 180, surface)
        envelope = min(1.0, progress * 5.0, (1.0 - progress) * 3.0 + .45)
        cx_ = x
        cy_ = y - int(8 * fs)

        # ── ACCRETION BAND BELAKANG (terlihat di atas core) ──
        disc_r = int((30 + 14 * pulse) * fs * max(.55, envelope))
        _NS_vex._arc_band(surface, cx_, cy_, disc_r, disc_r * .34,
                          math.pi + .25, math.tau - .25,
                          p["void_gold"], int(150 * envelope), 2, 14)
        _NS_vex._arc_band(surface, cx_, cy_, int(disc_r * .8),
                          int(disc_r * .3),
                          math.pi + .35, math.tau - .35,
                          p["void_magma"], int(120 * envelope), 1, 12)

        # ── WISPS SPIRAL (di belakang inti — stream accretion) ──
        # ── WISPS SPIRAL + EMBER COLUMN + GLINT ORBIT ──
        for arm in (0, math.pi):
            prev = None
            for j in range(9):
                t = j / 8.0
                a = arm + phase * 1.9 + t * math.tau * .82
                r = (16 + t * min(rng * .42, 95 * fs))
                px = int(cx_ + math.cos(a) * r)
                py = int(cy_ - int(4 * fs) + math.sin(a) * r * .46
                         - t * 42 * fs)
                if prev:
                    _skill_outlined_line(surface, prev, (px, py), 1,
                                         p["void_bright"],
                                         int(125 * (1 - t) * envelope))
                prev = (px, py)
                if j % 4 == 0:
                    _NS_vex._aacircle(
                        surface,
                        (*p["void_hot"], int(170 * (1 - t) * envelope)),
                        (px, py), max(1, int(2 * fs)))

        # ── INTI BLACK HOLE: disc hitam pekat + photon ring ganda ──
        core_r = int((16 + 7 * pulse) * fs * max(.5, envelope))
        _NS_vex._aacircle(surface, (*p["shadow_deep"], 240), (cx_, cy_),
                          core_r + 3)
        _NS_vex._aacircle(surface, (*p["void_darkest"], 230), (cx_, cy_),
                          core_r)
        # Horizon: pusat HITAM total (opaque), cahaya hanya di rim.
        _NS_vex._aacircle(surface, p["shadow_deep"], (cx_, cy_),
                          max(2, core_r - 3))
        _skill_outlined_circle(surface, (cx_, cy_), max(3, core_r - 1), 2,
                               p["void_hot"], int(225 * envelope))
        _skill_outlined_circle(surface, (cx_, cy_), core_r + 2, 1,
                               p["void_gold"], int(200 * envelope))

        # ── ACCRETION BAND DEPAN (menyilang bawah core) ──
        _NS_vex._arc_band(surface, cx_, cy_, disc_r, disc_r * .34,
                          .25, math.pi - .25,
                          p["void_gold_hot"], int(200 * envelope), 2, 14)
        _NS_vex._arc_band(surface, cx_, cy_, int(disc_r * .82),
                          int(disc_r * .3),
                          .35, math.pi - .35,
                          p["void_magma"], int(170 * envelope), 2, 12)
        for i in range(3):
            a = .8 + i * .7 + phase * .9
            gx_ = int(cx_ + math.cos(a) * disc_r)
            gy_ = int(cy_ + math.sin(a) * disc_r * .34)
            _NS_vex._aacircle(surface, p["void_gold_hot"], (gx_, gy_), 1)

        # ── ARC LENSING tipis di atas & bawah ──
        _NS_vex._arc_band(surface, cx_, cy_, int(disc_r * 1.5),
                          int(disc_r * .55),
                          math.pi + .5, math.tau - .5,
                          p["void_light"], int(95 * envelope), 1, 12)
        _NS_vex._arc_band(surface, cx_, cy_, int(disc_r * 1.5),
                          int(disc_r * .55),
                          .5, math.pi - .5,
                          p["void_light"], int(95 * envelope), 1, 12)

        # ── NOVA + RAY BURST setelah aktivasi ──
        if progress > .18:
            t = min(1.0, (progress - .18) / .50)
            _NS_vex._nova(surface, cx_, cy_, int(disc_r * .9),
                          int((34 + t * 66) * fs), 8, phase * .08,
                          (p["void_magma"], p["void_gold"]),
                          int(180 * (1 - t * .55) * envelope))
            for i in range(4):
                angle = i * math.tau / 8 + phase * .08
                ray_len = int((34 + t * 70) * fs *
                              (1.25 if i % 2 == 0 else .85))
                # Ray mulai dari tepi core agar disc black hole tetap
                # pekat — bukan dari pusatnya.
                ox = cx_ + math.cos(angle) * (core_r + 2)
                oy = cy_ + math.sin(angle) * (core_r + 2) * .9
                tip = (cx_ + math.cos(angle) * ray_len,
                       cy_ + math.sin(angle) * ray_len * .82)
                alpha = int(190 * (1 - t * .58) * envelope)
                _skill_outlined_line(surface, (int(ox), int(oy)),
                                     (int(tip[0]), int(tip[1])),
                                     max(2, int(4 * fs)),
                                     p["void_magma"], alpha)
                if i % 2 == 0:
                    _NS_vex._aacircle(surface, (*p["void_hot"], alpha),
                                      (int(tip[0]), int(tip[1])), 2)

        for i in range(5):
            t = (phase * .32 + i / 10.0) % 1.0
            a = i * math.tau / 10 + math.sin(phase * .5) * .12
            r = min(rng * .55, 100 * fs) * (.35 + .65 *
                                            _NS_vex._hash01(i * 23))
            px = int(x + math.cos(a) * r)
            py = int(y + math.sin(a) * r * .32 + 40 * fs - t * 92 * fs)
            alpha = int(195 * (1 - t) * envelope)
            col = p["void_magma"] if i % 3 == 0 else (
                p["void_gold"] if i % 3 == 1 else p["void_bright"])
            _NS_vex._aacircle(surface, (*col, alpha), (px, py),
                              max(1, int(2 * fs)))
            if i % 4 == 0:
                _NS_vex._aacircle(surface, p["white"], (px, py), 1)
        _NS_vex._orbit_glints(
            surface, x, y - int(4 * fs),
            int(min(rng * .72, 130 * fs)),
            int(min(rng * .72, 130 * fs) * .42),
            phase * 1.35, 12, p["void_hot"], int(200 * steady),
            hot=p["void_gold_hot"])


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_vex.draw_vex(surface, boss, x, y)

# ====================================================================
# zephyr.py
# ====================================================================
# ====================================================================
# zephyr.py  —  PIXEL MASTERWORK v2  (Zephyr "Dark Willow" Fey Mage)
# ====================================================================
class _NS_zephyr:
    """Namespace zephyr - PIXEL MASTERWORK v2.

    Rewrite penuh renderer Zephyr.  Tetap 100% prosedural (tanpa
    PNG / sprite-sheet / image-load).

    Rig native ~168 × 192 px (1.55× vs v1 ~106 × 114).  Pipeline
    heroes/__init__.py mengukur badan lalu men-scale agar tinggi final
    tetap ~51–70 px di arena — rig lebih besar hanya menaikkan
    resolusi efektif (kepadatan detail), bukan ukuran layar.

    Disiplin pixel-art
    ──────────────────
    1.  Ramp 4–5 nilai per material dengan hue-shift (bayangan dingin,
        highlight hangat).
    2.  Selout — outline gelap hanya di sisi bayangan; sisi cahaya +
        rim 1 px.
    3.  Siluet bergerigi — thorn-crown di-generate _tuft_points().
    4.  Specular cluster 1–2 px pada baja / kristal / emas.
    5.  Dither band di area perut / corset.
    6.  Key light kiri-atas konsisten dengan lighting.py.

    Skill FX (world-space, 3 fase tiap skill)
    ──────────────────────────────────────────
    Q Bramble Maze   — ring duri + chevron menuju trap + burst aktivasi
    W Shadow Realm   — pilar cahaya + kubah kaca + rune ring ganda
    E Casket Curse   — tether thorn + reticle target + burst impact
    R Bedlam         — pilar 4-lapis + ring konvergen + retakan zigzag
                       + 6 fairy orbit dengan trail glitter

    Setiap efek dikompensasi 1/_render_scale (_fx_scale, cap 2.6)
    sehingga radius di layar setara dunia, tidak mengecil bersama
    sprite cache.  Surface statis (aura/mist/shadow) di-cache sekali.
    """

    # ---------------------------------------------------------------
    # Compatibility flag
    # ---------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ═══════════════════════════════════════════════════════════════
    # ATTACK / SWING TIMELINE
    # ───────────────────────────────────────────────────────────────
    # Serangan Zephyr adalah AYUNAN TONGKAT berbasis busur, bukan
    # perpindahan lurus dari titik A ke titik B.  Timeline dipecah
    # jadi enam fase supaya ayunannya punya bobot & momentum:
    #
    #   ANTICIPATION -> WINDUP -> SWING -> IMPACT -> FOLLOW -> RECOVERY
    #
    # Nilai di bawah adalah fraksi 0..1 dari durasi satu serangan.
    # ═══════════════════════════════════════════════════════════════
    ATTACK_ANTICIPATION_END = 0.16   # counter-motion kecil ke belakang
    ATTACK_WINDUP_END  = 0.34        # tongkat terangkat penuh ke belakang
    ATTACK_SWING_END   = 0.52        # busur maju selesai
    ATTACK_IMPACT_END  = 0.60        # jendela hit aktif berakhir
    ATTACK_FOLLOW_END  = 0.80        # follow-through
    #  (0.80 - 1.00 = RECOVERY, kembali ke pose idle)

    #: Jendela hit aktif (fraksi progress) — dipakai hitbox & FX.
    ATTACK_ACTIVE_WINDOW = (0.44, 0.60)

    #: Frame IMPACT tunggal (puncak benturan).
    ATTACK_IMPACT_FRAME = 0.54

    # Busur ayunan dalam koordinat polar lokal, relatif pivot bahu.
    # (dipertahankan sebagai nama publik lama; nilainya kini benar-
    #  benar dipakai sebagai sudut busur, bukan angka mati)
    ATTACK_ARC_START   = -1.18   # sudut tongkat saat wind-up penuh
    ATTACK_ARC_SWEEP   = -0.62   # sudut tengah busur (melewati kepala)
    ATTACK_ARC_END     = 0.00    # sudut saat ekstensi maksimum ke depan

    #: Pivot bahu (lokal) tempat tongkat berputar.
    STAFF_PIVOT = (8, -24)

    # ── PANJANG LENGAN (skeleton) ───────────────────────────────────
    # Lengan Zephyr punya panjang TETAP.  Sebelumnya posisi tangan
    # diambil langsung dari ujung tongkat, sehingga lengan "melar"
    # 2-3x saat ayunan (bahu->siku 16 px -> 35 px, bahu->tangan
    # belakang 24 px -> 79 px) dan bar lengan menembus badan.
    ARM_UPPER = 15.0        # bahu -> siku
    ARM_FORE = 13.0         # siku -> tangan
    ARM_REACH = 27.4        # (ARM_UPPER + ARM_FORE) * 0.98, tak pernah lurus

    #: Radius tongkat per fase (rest, windup, impact, follow).
    STAFF_R_REST   = 36.0
    STAFF_R_WINDUP = 26.0
    STAFF_R_STRIKE = 68.0
    STAFF_R_FOLLOW = 62.0

    #: Nama state animasi + prioritas (angka besar menang).
    ANIM_STATES = {
        "IDLE": 0, "WALK": 10, "RUN": 15, "CHARGE": 30, "CAST": 35,
        "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
        "HIT": 60, "HURT": 65, "DEATH": 100,
    }

    # Durasi visual (frames) — renderer memakai ini, bukan gameplay timer
    SKILL_VISUAL_DURATION = {"q": 158, "w": 118, "e": 118, "r": 158}

    # ---------------------------------------------------------------
    # HD Color Palette — Dark Willow / fey mage, ramp 4-5 band
    # ---------------------------------------------------------------
    PALETTE = {
        # ── Skin: warm ivory, bayangan dingin keungu-unguan ──────────
        "skin_darkest":   ( 77,  32,  48),
        "skin_dark":      (143,  68,  84),
        "skin_mid":       (213, 128, 138),
        "skin_light":     (248, 186, 180),
        "skin_high":      (255, 222, 210),

        # ── Hair: crimson-to-magenta thorn crown, 5 band ─────────────
        "hair_darkest":   ( 48,   6,  24),
        "hair_dark":      (108,  16,  48),
        "hair_mid":       (178,  36,  76),
        "hair_light":     (230,  78, 120),
        "hair_shine":     (255, 138, 172),
        "hair_tip":       (255, 200, 220),

        # ── Gown: layered plum → deep purple, 5 band ────────────────
        "dress_darkest":  ( 22,   7,  34),
        "dress_dark":     ( 52,  16,  66),
        "dress_mid":      (104,  32, 108),
        "dress_light":    (162,  60, 146),
        "dress_high":     (218, 108, 186),

        # ── Corset: charcoal-plum, lace lapis ───────────────────────
        "corset_dark":    ( 18,   6,  29),
        "corset_mid":     ( 56,  18,  68),
        "corset_light":   (120,  50, 128),

        # ── Cloak/mantle: night-violet ───────────────────────────────
        "cloak_darkest":  ( 16,   6,  29),
        "cloak_dark":     ( 44,  17,  66),
        "cloak_mid":      ( 84,  38, 116),
        "cloak_light":    (152,  90, 182),

        # ── Boots: dark plum → mid ───────────────────────────────────
        "boot_darkest":   ( 17,   8,  28),
        "boot_dark":      ( 44,  22,  58),
        "boot_mid":       ( 88,  46, 102),
        "boot_light":     (170, 108, 175),
        "thread_light":   (238, 148, 208),

        # ── Moth wings: ink rim + translucent violet membranes ───────
        "wing_darkest":   ( 30,  10,  54),
        "wing_dark":      ( 72,  32, 116),
        "wing_mid":       (132,  74, 176),
        "wing_light":     (192, 130, 218),
        "wing_shine":     (242, 196, 250),
        "wing_vein":      ( 88,  42, 132),
        "wing_glass":     (226, 172, 240),

        # ── Staff: blackwood + vine thorns ───────────────────────────
        "staff_dark":     ( 26,  13,  36),
        "staff_mid":      ( 68,  38,  68),
        "staff_light":    (128,  86, 122),
        "staff_vine":     (100,  40,  96),
        "staff_glow":     (255, 152, 220),

        # ── Crystal orb: amethyst 4-band ────────────────────────────
        "jewel_dark":     ( 76,  10,  70),
        "jewel_mid":      (188,  42, 148),
        "jewel_light":    (255, 156, 218),

        # ── Thorns: dark bark ────────────────────────────────────────
        "thorn_dark":     ( 42,  12,  54),
        "thorn_mid":      ( 96,  32, 102),
        "thorn_light":    (186,  76, 158),

        # ── Bramble (alias — gameplay projectile code uses these) ────
        "bramble_dark":   ( 42,  12,  54),
        "bramble_mid":    ( 96,  32, 102),
        "bramble_light":  (186,  76, 158),

        # ── Magic / runes: hot-pink → white ─────────────────────────
        "magic_darkest":  ( 40,   4,  40),
        "magic_dark":     (100,  12,  84),
        "magic_mid":      (178,  32, 138),
        "magic_light":    (232,  80, 178),
        "magic_bright":   (255, 136, 210),
        "magic_hot":      (255, 200, 236),
        "magic_white":    (255, 242, 252),
        "rune_dark":      ( 66,  20,  88),
        "rune_mid":       (154,  48, 152),
        "rune_light":     (240, 134, 216),

        # ── Gold hardware ────────────────────────────────────────────
        "gold_dark":      ( 82,  52,  16),
        "gold_mid":       (158, 108,  34),
        "gold_light":     (234, 192,  90),

        # ── Eyes and face ────────────────────────────────────────────
        "eye_white":      (255, 234, 228),
        "eye_iris":       (150,  38, 102),
        "eye_iris_light": (255, 154, 210),
        "eye_pupil":      ( 18,   6,  14),
        "lips_dark":      (130,  20,  60),
        "lips_mid":       (215,  66, 118),

        # ── Bedlam fairy accent ──────────────────────────────────────
        "butterfly_dark": ( 56,  12,  66),
        "butterfly_mid":  (156,  46, 140),
        "butterfly_light":(244, 140, 216),

        # ── Utility ──────────────────────────────────────────────────
        "shadow":         (  0,   0,   0),
        "shadow_deep":    (  4,   4,  12),
        "white":          (255, 255, 255),
    }

    # ---------------------------------------------------------------
    # Cache surfaces statis (dibangun sekali, tanpa alokasi per-frame)
    # ---------------------------------------------------------------
    _STATIC_SURFACES = {}
    _GHOST_BUF = {}     # cache afterimage bedlam

    # ---------------------------------------------------------------
    # Low-level drawing primitives
    # ---------------------------------------------------------------
    def _clamp(color):
        if type(color) is tuple and len(color) == 3:
            _r, _g, _b = color
            if (type(_r) is int and type(_g) is int and type(_b) is int
                    and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
                return color
        return tuple(max(0, min(255, int(c))) for c in color)

    def _static(key, builder):
        surf = _NS_zephyr._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_zephyr._STATIC_SURFACES[key] = surf
        return surf

    def _hash01(seed):
        """Deterministik pseudo-random [0,1] dari integer seed."""
        h = int(seed) * 2654435761 & 0xFFFFFFFF
        h ^= h >> 16
        return (h & 0xFFFF) / 65535.0

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zephyr._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_zephyr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_zephyr._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_zephyr._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_zephyr._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_zephyr._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)

    # ---------------------------------------------------------------
    # World-space helpers
    # ---------------------------------------------------------------
    def _world_to_local(boss, x, y, wx, wy):
        """Konversi titik koordinat DUNIA -> ruang gambar renderer.

        BUGFIX (orb/ring "random" pada hero): saat dirender sebagai
        HERO (heroes/__init__.py, jalur sprite-cache), renderer
        dipanggil di (c, c) = PUSAT CANVAS, bukan koordinat dunia.
        Canvas lalu di-scale _render_scale saat di-blit ke posisi
        hero, sehingga 1 px canvas = _render_scale px dunia. Titik
        dunia (wx, wy) jadi (x + (wx - hero.x) / scale, ...).

        Boss asli tidak punya _render_scale (digambar langsung di
        koordinat dunia) -> dikembalikan apa adanya (perilaku lama).
        """
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_zephyr._world_to_local(boss, x, y,
                                              target.x, target.y)
        scale = getattr(boss, "_render_scale", None)
        dist = 200 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)

    # ---------------------------------------------------------------
    # FX helper primitives  (setingkat Thorne v2.1 / Grimjaw v2)
    # ---------------------------------------------------------------
    def _fx_scale(hero):
        """Faktor kompensasi efek world-space.

        Hero dirender ke canvas kecil lalu di-scale _render_scale ke
        arena.  Efek (cincin, retakan, dll.) harus dikali 1/_render_scale
        agar ukuran di layar = world-px; cap 2.6 supaya efek muat
        di canvas cache.
        """
        scale = getattr(hero, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(hero, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke tepi canvas."""
        scale = getattr(hero, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=2, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_zephyr._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_zephyr._aacircle(surface, (*core, alpha),
                                 (int(cx), int(cy)), max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px_, py_ = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_zephyr._aaline(
                surface, (*color, alpha),
                (int(cx + px_ * s * size * .55 - ca * size * .5),
                 int(cy + py_ * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=5, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_zephyr._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_zephyr._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_zephyr._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_zephyr._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bergerigi (thorn / pixel-art).

        Deterministik (hash) — aman untuk cache.
        """
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx_, ny_ = (by - ay), -(bx - ax)
            ln = math.hypot(nx_, ny_) or 1.0
            nx_, ny_ = nx_ / ln, ny_ / ln
            for j in range(n):
                t = (j + 0.5) / n
                px_, py_ = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 *
                             _NS_zephyr._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px_ + nx_ * d, py_ + ny_ * d))
                else:
                    out.append((px_ - nx_ * d * 0.45, py_ - ny_ * d * 0.45))
            out.append((bx, by))
        return out

    def _draw_fey_arc(surface, cx, cy, rx, ry, start, end, color,
                      width=2, segments=24):
        """Partial ellipse arc — fey aura / dome / ground ring."""
        if rx <= 0 or ry <= 0:
            return
        span = end - start
        if abs(span) < 0.01:
            return
        step = span / segments
        prev = None
        for i in range(segments + 1):
            a = start + i * step
            pt = (int(cx + math.cos(a) * rx),
                  int(cy + math.sin(a) * ry))
            if prev:
                _NS_zephyr._aaline(surface, color, prev, pt, width)
            prev = pt

    # ---------------------------------------------------------------
    # State helpers
    # ---------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_zp_last_x"):
            boss._zp_last_x = boss.x
            boss._zp_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zp_last_x)
        dy = abs(boss.y - boss._zp_last_y)
        boss._zp_last_x = boss.x
        boss._zp_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving

    def _update_attack_anim(boss):
        """ANIMATION CONTROLLER Zephyr — state, fase, timing, delta-time.

        Menggantikan pelacak serangan lama yang hanya menghitung timer.
        Sekarang ada:

        * ``_zp_dt``              delta-time nyata (detik, dijepit)
        * ``_zp_attack_active``   serangan sedang berjalan  (legacy)
        * ``_zp_attack_frame``    frame ke-n dalam serangan  (legacy)
        * ``_zp_attack_progress`` 0..1 sepanjang serangan     (legacy)
        * ``_zp_attack_phase``    ANTICIPATION/WINDUP/SWING/IMPACT/
                                  FOLLOW/RECOVERY
        * ``_zp_hit_active``      True hanya di jendela hit aktif
        * ``_zp_state``           state animasi ber-prioritas
        * ``_zp_state_prev``      state sebelumnya (untuk transisi)
        * ``_zp_state_time``      lama state sekarang (detik)

        Semua nama lama dipertahankan supaya kode pemanggil (renderer,
        skill, tooling) tidak perlu diubah.
        """
        # ── delta time nyata (untuk FX & transisi) ──────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                              # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_zp_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._zp_last_ms = now
        boss._zp_dt = dt

        # ── timeline serangan ───────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zp_prev_timer", -1))
        active = bool(getattr(boss, "_zp_attack_active", False))

        trigger = previous >= 0 and timer > previous
        if trigger:
            boss._zp_attack_active = True
            boss._zp_swing_started = False
            active = True
        if active and timer <= 0:
            boss._zp_attack_active = False
            active = False

        boss._zp_prev_timer = timer
        frame = max(0, cooldown - timer) if active else 0
        boss._zp_attack_frame = frame
        progress = (min(1.0, frame / max(1, cooldown - 1))
                    if active else 0.0)
        boss._zp_attack_progress = progress

        # ── fase serangan ───────────────────────────────────────────
        Z = _NS_zephyr
        if not active:
            phase = "NONE"
        elif progress < Z.ATTACK_ANTICIPATION_END:
            phase = "ANTICIPATION"
        elif progress < Z.ATTACK_WINDUP_END:
            phase = "WINDUP"
        elif progress < Z.ATTACK_SWING_END:
            phase = "SWING"
        elif progress < Z.ATTACK_IMPACT_END:
            phase = "IMPACT"
        elif progress < Z.ATTACK_FOLLOW_END:
            phase = "FOLLOW"
        else:
            phase = "RECOVERY"
        boss._zp_attack_phase = phase

        lo, hi = Z.ATTACK_ACTIVE_WINDOW
        boss._zp_hit_active = bool(active and lo <= progress < hi)

        # ── state machine ber-prioritas ─────────────────────────────
        want = _NS_zephyr._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_zp_state", "IDLE")
        state_time = float(getattr(boss, "_zp_state_time", 0.0))
        if want != cur:
            cur_p = Z.ANIM_STATES.get(cur, 0)
            new_p = Z.ANIM_STATES.get(want, 0)
            # DEATH mengunci; selain itu state boleh diambil alih oleh
            # prioritas yang sama/lebih tinggi, atau kalau state lama
            # sudah berjalan cukup lama (mencegah pose tersangkut).
            if cur != "DEATH" and (new_p >= cur_p or state_time > 0.08):
                boss._zp_state_prev = cur
                boss._zp_state = want
                boss._zp_state_time = 0.0
            else:
                boss._zp_state_time = state_time + dt
        else:
            boss._zp_state_time = state_time + dt
        if not hasattr(boss, "_zp_state"):
            boss._zp_state = want
            boss._zp_state_prev = want
            boss._zp_state_time = 0.0

    def _resolve_anim_state(boss, attacking, phase):
        """Tentukan state animasi yang DIINGINKAN frame ini."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_zp_hurt_frames", 0)) > 0:
            return "HURT"
        skill = getattr(boss, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if attacking:
            if phase in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if phase in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if getattr(boss, "_moving_cached", False):
            return "RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2 \
                else "WALK"
        return "IDLE"

    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (canvas-space) saat jendela hit aktif.

        Dipakai debug overlay dan sistem tumbukan opsional.  Return
        None kalau jendela hit sedang tidak aktif.
        """
        if not getattr(boss, "_zp_hit_active", False):
            return None
        f = 1 if getattr(boss, "direction", 1) >= 0 else -1
        reach = 76
        left = cx if f > 0 else cx - reach
        return pygame.Rect(int(left), int(cy - 58), reach, 78)

    # ---------------------------------------------------------------
    # STATIC SURFACE BUILDERS  (cached, no per-frame allocation)
    # ---------------------------------------------------------------
    def _draw_shadow(surface, x, y):
        def build():
            s = pygame.Surface((128, 32), pygame.SRCALPHA)
            for r in range(26, 3, -4):
                a = max(0, int((27 - r) * 5))
                pygame.draw.ellipse(
                    s, (0, 0, 0, a),
                    (64 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)))
            pygame.draw.ellipse(
                s, (*_NS_zephyr.PALETTE["magic_dark"], 36),
                (16, 11, 96, 12))
            return s
        surf = _NS_zephyr._static("shadow_zp", build)
        surface.blit(surf, (int(x - 64), int(y - 16)))

    def _draw_fey_rim_light(surface, x, y, phase):
        """Silhouette halo behind wings — cached, pulsing alpha only."""
        p = _NS_zephyr.PALETTE
        def build():
            s = pygame.Surface((148, 156), pygame.SRCALPHA)
            ctr = (74, 78)
            for r, a in ((64, 9), (52, 14), (38, 22)):
                _NS_zephyr._aacircle(s, (*p["magic_dark"], a), ctr, r)
            _NS_zephyr._aaline(s, (*p["wing_mid"], 38),
                               (42, 100), (22, 44), 2)
            _NS_zephyr._aaline(s, (*p["wing_mid"], 38),
                               (106, 100), (126, 44), 2)
            return s
        surf = _NS_zephyr._static("rim_zp", build)
        pulse = int(180 + math.sin(phase * 1.25) * 48)
        surf.set_alpha(pulse)
        surface.blit(surf, (int(x - 74), int(y - 78)))

    def _draw_fey_aura(surface, x, y, phase):
        """Subtle magic aura on the ground — cached, alpha-pulsed."""
        p = _NS_zephyr.PALETTE
        def build():
            s = pygame.Surface((192, 156), pygame.SRCALPHA)
            c = (96, 78)
            for r, col, a in ((72, p["magic_darkest"], 55),
                              (56, p["magic_dark"],    80),
                              (36, p["magic_mid"],     38)):
                _NS_zephyr._ellipse(s, (*col, a),
                                    (c[0]-r, c[1]-r//4, r*2, r//2))
            return s
        surf = _NS_zephyr._static("aura_zp", build)
        alpha = int(170 + math.sin(phase * .55) * 48)
        surf.set_alpha(alpha)
        surface.blit(surf, (int(x - 96), int(y - 10)))

    def _draw_fey_platform(surface, x, y, phase, skill=None):
        """Hovering magic ring platform under feet — cached."""
        p = _NS_zephyr.PALETTE
        sk_key = "platform_zp_" + (skill or "none")
        def build():
            s = pygame.Surface((180, 64), pygame.SRCALPHA)
            cx, cy = 90, 32
            # primary ring
            _NS_zephyr._ellipse(s, (*p["magic_darkest"], 110),
                                (cx-54, cy-16, 108, 32))
            _NS_zephyr._ellipse(s, (*p["magic_dark"], 160),
                                (cx-54, cy-16, 108, 32), 3)
            # inner rune ring
            _NS_zephyr._ellipse(s, (*p["rune_dark"], 90),
                                (cx-40, cy-12, 80, 24))
            _NS_zephyr._ellipse(s, (*p["rune_mid"], 140),
                                (cx-40, cy-12, 80, 24), 2)
            # 8 rune dots
            for i in range(4):
                a = i * math.pi / 4
                rx, ry = int(cx + math.cos(a) * 46), int(cy + math.sin(a) * 14)
                _NS_zephyr._aacircle(s, p["rune_light"], (rx, ry), 2)
            return s
        surf = _NS_zephyr._static(sk_key, build)
        alpha = int(188 + math.sin(phase * .88) * 40)
        surf.set_alpha(alpha)
        surface.blit(surf, (int(x - 90), int(y - 32)))

    def _draw_floating_sparkles(surface, x, y, phase, trail=False,
                                facing=1, intense=False):
        """Motes that rise around Zephyr — lightweight."""
        p = _NS_zephyr.PALETTE
        n = 5 if not intense else 8
        for i in range(n):
            t = (phase * .24 + i / float(n)) % 1.0
            dx = int(math.sin(phase * 1.6 + i * 2.09) * (18 + i * 3))
            dy = int(-t * 54)
            alpha = max(0, int(210 * (1.0 - t)))
            col = p["magic_bright"] if i % 2 else p["rune_light"]
            r = 1 if i % 3 else 2
            _NS_zephyr._aacircle(surface, (*col, alpha),
                                 (x + dx, y + dy), r)
        if trail:
            for i in range(3):
                _NS_zephyr._aacircle(
                    surface, (*p["magic_hot"], 90),
                    (int(x - facing * (8 + i * 4)),
                     int(y + 8 - i * 4)), max(1, 2 - i))

    def _draw_cast_flash(surface, x, y, facing, progress, phase):
        """Kilatan orb di ujung tongkat saat fase SWING -> FOLLOW."""
        Z = _NS_zephyr
        p = Z.PALETTE
        lo = Z.ATTACK_SWING_END - 0.10
        hi = Z.ATTACK_FOLLOW_END
        if lo < progress < hi:
            t = (progress - lo) / (hi - lo)
            alpha = int(230 * (1.0 - t * t))
            tip = Z._staff_orb_position(
                x, y, facing, phase, "attack", progress)
            r = int(11 + t * 8)
            Z._aacircle(surface, (*p["magic_dark"], alpha // 3),
                        tip, r + 5)
            Z._aacircle(surface, (*p["magic_mid"], int(alpha * .7)),
                        tip, r)
            Z._aacircle(surface, (*p["magic_hot"], alpha),
                        tip, max(1, r - 4))
            # 6-spike star burst
            Z._spark_star(surface, tip[0], tip[1],
                          r + 8, p["magic_light"], alpha,
                          spikes=3, rot=phase * 2.1,
                          core=p["magic_white"])

    # ---------------------------------------------------------------
    # ZEPHYR v2 MASTERWORK RIG  —  _draw_zephyr_elite
    # ---------------------------------------------------------------
    def _ease_out(t):
        """Ease-out kuadratik — cepat di awal, mendarat halus."""
        t = max(0.0, min(1.0, t))
        return 1.0 - (1.0 - t) * (1.0 - t)

    def _ease_in(t):
        """Ease-in kuadratik — pelan di awal (antisipasi)."""
        t = max(0.0, min(1.0, t))
        return t * t

    def _ease_in_out(t):
        """Smoothstep."""
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    def _staff_arc_pose(attack_progress):
        """Sudut + radius tongkat pada busur ayunan.

        Mengembalikan ``(angle_rad, radius)`` relatif ``STAFF_PIVOT``.
        Interpolasi dilakukan dalam ruang POLAR, sehingga ujung tongkat
        benar-benar menyapu sebuah BUSUR — bukan meluncur lurus dari
        pose awal ke pose akhir.
        """
        Z = _NS_zephyr
        ap = max(0.0, min(1.0, attack_progress))

        a_rest = 0.0555                    # sudut pose istirahat
        r_rest = Z.STAFF_R_REST

        if ap < Z.ATTACK_ANTICIPATION_END:
            # ANTICIPATION — tarikan kecil berlawanan arah ayunan
            t = Z._ease_in(ap / Z.ATTACK_ANTICIPATION_END)
            return (a_rest + 0.22 * t, r_rest - 3.0 * t)

        if ap < Z.ATTACK_WINDUP_END:
            # WIND-UP — tongkat terangkat ke belakang-atas
            t = Z._ease_in_out(
                (ap - Z.ATTACK_ANTICIPATION_END) /
                (Z.ATTACK_WINDUP_END - Z.ATTACK_ANTICIPATION_END))
            a0, r0 = a_rest + 0.22, r_rest - 3.0
            return (a0 + (Z.ATTACK_ARC_START - a0) * t,
                    r0 + (Z.STAFF_R_WINDUP - r0) * t)

        if ap < Z.ATTACK_SWING_END:
            # SWING — busur maju melewati atas kepala, radius memanjang
            t = (ap - Z.ATTACK_WINDUP_END) / \
                (Z.ATTACK_SWING_END - Z.ATTACK_WINDUP_END)
            te = Z._ease_out(t)
            # dua sub-busur (start -> sweep -> end) supaya lintasan
            # melengkung, tidak sekadar berputar rata
            if te < 0.5:
                k = te / 0.5
                ang = Z.ATTACK_ARC_START + \
                    (Z.ATTACK_ARC_SWEEP - Z.ATTACK_ARC_START) * k
            else:
                k = (te - 0.5) / 0.5
                ang = Z.ATTACK_ARC_SWEEP + \
                    (Z.ATTACK_ARC_END - Z.ATTACK_ARC_SWEEP) * k
            rad = Z.STAFF_R_WINDUP + \
                (Z.STAFF_R_STRIKE - Z.STAFF_R_WINDUP) * te
            return (ang, rad)

        if ap < Z.ATTACK_IMPACT_END:
            # IMPACT — tahan sebentar di ekstensi maksimum (bobot)
            t = (ap - Z.ATTACK_SWING_END) / \
                (Z.ATTACK_IMPACT_END - Z.ATTACK_SWING_END)
            return (Z.ATTACK_ARC_END + 0.06 * t,
                    Z.STAFF_R_STRIKE + 2.0 * math.sin(t * math.pi))

        if ap < Z.ATTACK_FOLLOW_END:
            # FOLLOW-THROUGH — momentum membawa ujung turun ke depan
            t = Z._ease_out(
                (ap - Z.ATTACK_IMPACT_END) /
                (Z.ATTACK_FOLLOW_END - Z.ATTACK_IMPACT_END))
            return (Z.ATTACK_ARC_END + 0.06 + 0.30 * t,
                    Z.STAFF_R_STRIKE +
                    (Z.STAFF_R_FOLLOW - Z.STAFF_R_STRIKE) * t)

        # RECOVERY — kembali ke pose istirahat
        t = Z._ease_in_out(
            (ap - Z.ATTACK_FOLLOW_END) / (1.0 - Z.ATTACK_FOLLOW_END))
        a0 = Z.ATTACK_ARC_END + 0.36
        return (a0 + (a_rest - a0) * t,
                Z.STAFF_R_FOLLOW + (r_rest - Z.STAFF_R_FOLLOW) * t)

    def _staff_tip_local(phase, action="idle", attack_progress=0.0):
        """Posisi lokal ujung (orb) tongkat untuk pose saat ini.

        Untuk ``action == "attack"`` posisi diambil dari busur ayunan
        (:meth:`_staff_arc_pose`) sehingga gerakannya melengkung dan
        punya momentum.  Idle & walk memakai sway halus.
        """
        Z = _NS_zephyr
        wave = math.sin(phase * 1.35) * 1.6
        if action == "attack":
            ang, rad = Z._staff_arc_pose(attack_progress)
            px, py = Z.STAFF_PIVOT
            return (int(px + math.cos(ang) * rad),
                    int(py + math.sin(ang) * rad + wave * 0.5))
        if action == "walk":
            return (int(44 + math.sin(phase * 1.72) * 4),
                    int(-22 + wave))
        # idle: gentle sway
        return (int(44 + math.sin(phase * .92) * 2), int(-22 + wave))

    def _staff_grip_local(phase, action="idle", attack_progress=0.0):
        """Posisi lokal genggaman tangan pada batang tongkat."""
        tx, ty = _NS_zephyr._staff_tip_local(phase, action,
                                             attack_progress)
        bx, by = _NS_zephyr._staff_bottom_local(phase, action,
                                                attack_progress)
        return (int(bx * .46 + tx * .54), int(by * .46 + ty * .54))

    def _staff_bottom_local(phase, action="idle", attack_progress=0.0):
        """Posisi lokal pangkal tongkat (ikut berayun saat menyerang)."""
        if action == "attack":
            ang, _rad = _NS_zephyr._staff_arc_pose(attack_progress)
            px, py = _NS_zephyr.STAFF_PIVOT
            # pangkal berada di sisi berlawanan pivot -> counter-rotate
            back = 22.0
            return (int(px - math.cos(ang) * back),
                    int(py - math.sin(ang) * back + 30))
        if action == "walk":
            return (int(2 + math.sin(phase * 1.72) * 2), 28)
        return (2, 28)

    # ── SKELETON LENGAN: IK 2-tulang + genggaman terjangkau ─────────
    def _solve_arm(shoulder, target, l1=None, l2=None, bend=1.0):
        """IK 2-tulang: kembalikan ``(elbow, hand)`` dengan panjang TETAP.

        ``target`` adalah posisi tangan yang diinginkan.  Kalau target
        di luar jangkauan (``l1 + l2``) tangan DIJEPIT ke lingkaran
        jangkauan — lengan tidak pernah melar.  ``bend`` menentukan
        arah tekukan siku (+1 = siku di bawah garis bahu->tangan).

        Semua koordinat lokal (pra-mirror), y ke bawah.
        """
        Z = _NS_zephyr
        l1 = Z.ARM_UPPER if l1 is None else float(l1)
        l2 = Z.ARM_FORE if l2 is None else float(l2)
        sx, sy = float(shoulder[0]), float(shoulder[1])
        vx, vy = float(target[0]) - sx, float(target[1]) - sy
        d = math.hypot(vx, vy)
        if d < 1e-4:
            vx, vy, d = 0.0, 1.0, 1.0
        ux, uy = vx / d, vy / d

        reach = (l1 + l2) * 0.995
        floor_ = abs(l1 - l2) + 0.75
        d = max(floor_, min(reach, d))
        hand = (sx + ux * d, sy + uy * d)

        # hukum kosinus -> proyeksi siku pada sumbu bahu->tangan
        a = (d * d + l1 * l1 - l2 * l2) / (2.0 * d)
        a = max(-l1, min(l1, a))
        h = math.sqrt(max(0.0, l1 * l1 - a * a))
        # perp(u) = (-uy, ux) menunjuk "ke bawah" saat u menunjuk kanan
        ex = sx + ux * a + (-uy) * h * bend
        ey = sy + uy * a + (ux) * h * bend
        return (int(round(ex)), int(round(ey))), \
               (int(round(hand[0])), int(round(hand[1])))

    def _staff_hand_local(phase, action="idle", attack_progress=0.0,
                          shoulder=(9, -24), prefer=0.42, lowest=0.0):
        """Titik pegangan pada BATANG tongkat yang masih terjangkau.

        Tangan wajib menempel di batang (bukan melayang), jadi alih-alih
        menarik lengan ke ujung tongkat, kita cari titik di batang yang
        jaraknya dari bahu <= ``ARM_REACH`` dan PALING DEKAT dengan
        genggaman ideal ``prefer`` (0 = pangkal, 1 = ujung).  Pencarian
        dua arah supaya tidak pernah tersangkut di pangkal.
        """
        Z = _NS_zephyr
        bx, by = Z._staff_bottom_local(phase, action, attack_progress)
        tx, ty = Z._staff_tip_local(phase, action, attack_progress)
        sx, sy = shoulder
        reach = Z.ARM_REACH
        prefer = max(lowest, min(1.0, float(prefer)))

        def at(tt):
            return (bx + (tx - bx) * tt, by + (ty - by) * tt)

        def dist(tt):
            px, py = at(tt)
            return math.hypot(px - sx, py - sy)

        if dist(prefer) <= reach:
            px, py = at(prefer)
            return (int(round(px)), int(round(py))), prefer

        # menyebar keluar dari genggaman ideal, dua arah sekaligus
        step = 0.02
        k = 1
        nearest_t, nearest_d = prefer, dist(prefer)
        while k * step <= 1.0:
            for tt in (prefer - k * step, prefer + k * step):
                if tt < lowest or tt > 1.0:
                    continue
                dd = dist(tt)
                if dd <= reach:
                    px, py = at(tt)
                    return (int(round(px)), int(round(py))), tt
                if dd < nearest_d:
                    nearest_t, nearest_d = tt, dd
            k += 1
        # seluruh batang di luar jangkauan -> titik terdekat;
        # _solve_arm yang menjepitnya ke lingkaran jangkauan
        px, py = at(nearest_t)
        return (int(round(px)), int(round(py))), nearest_t

    def _arm_pose_local(phase, action="idle", attack_progress=0.0):
        """Pose kedua lengan untuk frame ini.

        Return ``(front_shoulder, front_elbow, front_hand,
        rear_shoulder, rear_elbow, rear_hand, grip_t)``.  Dipakai
        renderer dan debug overlay supaya keduanya tak pernah beda.
        """
        Z = _NS_zephyr
        fs = (9, -24)
        rs = (-9, -24)

        # Genggaman bergeser sepanjang batang mengikuti fase: ditarik
        # mendekat saat wind-up (lengan menekuk), terentang saat strike.
        # Interpolasi HALUS (smoothstep) — kalau memakai tangga per fase,
        # tangan melompat belasan piksel di batas fase.
        if action == "attack":
            keys = ((0.00, 0.40), (Z.ATTACK_WINDUP_END, 0.33),
                    (Z.ATTACK_SWING_END, 0.53), (Z.ATTACK_IMPACT_END, 0.52),
                    (Z.ATTACK_FOLLOW_END, 0.47), (1.00, 0.42))
            ap = max(0.0, min(1.0, float(attack_progress)))
            prefer = keys[-1][1]
            for (a0, v0), (a1, v1) in zip(keys, keys[1:]):
                if ap <= a1:
                    span = max(1e-6, a1 - a0)
                    u = max(0.0, min(1.0, (ap - a0) / span))
                    u = u * u * (3.0 - 2.0 * u)          # smoothstep
                    prefer = v0 + (v1 - v0) * u
                    break
        else:
            prefer = 0.50

        hand_t, t = Z._staff_hand_local(phase, action, attack_progress,
                                        shoulder=fs, prefer=prefer)
        fe, fh = Z._solve_arm(fs, hand_t, bend=1.0)
        # tangan belakang menopang batang sedikit di bawah tangan depan
        rear_t, _ = Z._staff_hand_local(phase, action, attack_progress,
                                        shoulder=rs,
                                        prefer=max(0.0, t - 0.20))
        re_, rh = Z._solve_arm(rs, rear_t, bend=1.0)
        return fs, fe, fh, rs, re_, rh, t

    def _staff_orb_position(cx, cy, facing, phase=0.0, action="idle",
                            attack_progress=0.0):
        """World/canvas position of the staff orb for spell effects."""
        tx, ty = _NS_zephyr._staff_tip_local(phase, action, attack_progress)
        f = 1 if facing >= 0 else -1
        return int(cx + tx * f), int(cy + ty)

    # ── SWING TRAIL (canvas-space, deterministik dari progress) ─────
    def _staff_trail_samples(phase, attack_progress, count=10,
                             step=0.021):
        """Histori posisi tongkat: [(grip, tip), ...] dari lama -> baru.

        Sample diturunkan dari progress serangan (bukan disimpan per
        frame) sehingga hasilnya DETERMINISTIK — aman untuk sprite
        cache dan tidak pernah bocor memori.
        """
        Z = _NS_zephyr
        out = []
        floor_ = Z.ATTACK_ANTICIPATION_END + 0.02
        for i in range(count, 0, -1):
            ap = attack_progress - step * i
            if ap <= floor_:
                continue
            tip = Z._staff_tip_local(phase, "attack", ap)
            grip = Z._staff_grip_local(phase, "attack", ap)
            out.append((grip, tip))
        out.append((Z._staff_grip_local(phase, "attack", attack_progress),
                    Z._staff_tip_local(phase, "attack", attack_progress)))
        return out

    def _draw_staff_swing_trail(surface, pt, phase, attack_progress):
        """Slash trail prosedural yang mengikuti arah ayunan.

        Pita dibangun dari pasangan (grip, tip) beberapa posisi terakhir
        lalu digambar tiga lapis:

          1. badan gelap selebar penuh   (massa / bobot)
          2. inti panas separuh lebar    (energi)
          3. tepi keras 2 px di ujung    (hard edge pixel-art)

        Warnanya me-ramp dari dingin (sample tua) ke panas (sample
        baru) sehingga arah ayunan terbaca jelas.  Ditutup crescent
        terang di ujung terdepan + percikan piksel.
        """
        Z = _NS_zephyr
        p = Z.PALETTE
        ap = max(0.0, min(1.0, attack_progress))
        if ap < Z.ATTACK_WINDUP_END - 0.04 or ap > 0.88:
            return
        samples = Z._staff_trail_samples(phase, ap)
        n = len(samples)
        if n < 2:
            return

        # kekuatan trail memuncak tepat di jendela hit
        peak = 1.0 - min(1.0, abs(ap - Z.ATTACK_IMPACT_FRAME) / 0.34)
        peak = max(0.18, peak)

        ramp_body = (p["magic_darkest"], p["magic_dark"], p["magic_mid"])
        ramp_core = (p["magic_mid"], p["magic_light"], p["magic_bright"])

        # Pita hanya menempati SEPERTIGA LUAR tongkat -> crescent tipis
        # di jalur ujung, bukan kipas lebar yang menutupi badan.
        def edges(sample):
            (gx, gy), (tx, ty) = sample
            ix = gx + (tx - gx) * 0.46
            iy = gy + (ty - gy) * 0.46
            ox = gx + (tx - gx) * 1.06
            oy = gy + (ty - gy) * 1.06
            return (int(ix), int(iy)), (int(ox), int(oy))

        for i in range(n - 1):
            t = (i + 1) / float(n)
            fade = (t ** 1.6) * peak
            i0, o0 = edges(samples[i])
            i1, o1 = edges(samples[i + 1])
            pi0, po0 = pt(*i0), pt(*o0)
            pi1, po1 = pt(*i1), pt(*o1)

            band = min(2, int(t * 3))
            a_body = int(112 * fade)
            if a_body > 4:
                Z._poly(surface, (*ramp_body[band], a_body),
                        [pi0, po0, po1, pi1])
            a_core = int(168 * fade)
            if a_core > 6:
                m0 = (int(pi0[0] + (po0[0] - pi0[0]) * .52),
                      int(pi0[1] + (po0[1] - pi0[1]) * .52))
                m1 = (int(pi1[0] + (po1[0] - pi1[0]) * .52),
                      int(pi1[1] + (po1[1] - pi1[1]) * .52))
                Z._poly(surface, (*ramp_core[band], a_core),
                        [m0, po0, po1, m1])
            a_edge = int(240 * fade)
            if a_edge > 8:
                Z._aaline(surface, (*p["magic_hot"], a_edge), po0, po1, 2)

        # crescent terang tipis di tepi terdepan
        if n >= 4:
            lead = []
            inner = []
            for s in samples[-4:]:
                i_, o_ = edges(s)
                lead.append(pt(*o_))
                inner.append(pt(int(i_[0] + (o_[0] - i_[0]) * .70),
                                int(i_[1] + (o_[1] - i_[1]) * .70)))
            Z._poly(surface, (*p["magic_white"], int(120 * peak)),
                    lead + list(reversed(inner)))

        # percikan piksel di ujung busur (chunky, bukan gradien)
        tipx, tipy = pt(*samples[-1][1])
        for k in range(5):
            h = Z._hash01(int(ap * 997) + k * 31)
            ang = -1.4 + h * 2.8
            dist = 6 + int(h * 13)
            Z._aacircle(surface,
                        (*p["magic_white"], int(220 * peak)),
                        (tipx + int(math.cos(ang) * dist),
                         tipy + int(math.sin(ang) * dist)),
                        1 if k % 2 else 2)

    # ── Main elite body renderer ────────────────────────────────────
    def _draw_zephyr_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False,
                           bedlam=False):
        """Full Zephyr v2 rig: crown → wings → gown → staff → face."""
        p = _NS_zephyr.PALETTE
        f = 1 if facing >= 0 else -1
        walk   = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride    = math.sin(phase * 1.72)
        breath    = math.sin(phase * .78)
        hair_sway = int(math.sin(phase * 1.18) * 2.5)

        # Root motion
        lean = 0
        if walk:
            lean = int(3.8 * stride * f)
        elif attack:
            lean = int(math.sin(ap * math.pi) * 8.0 * f)
        else:
            lean = int(math.sin(phase * .8) * 3.5) * f
        root_y = int(breath * 1.1)
        if walk:
            root_y -= int(abs(stride) * 3.0)
        if attack:
            root_y += int(math.sin(ap * math.pi) * 2.5)

        # ── transform helpers ───────────────────────────────────────
        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, coords, outline=True):
            pts_ = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                 [(qx + f, qy + 1) for qx, qy in pts_])
            _NS_zephyr._poly(surface, color, pts_)
            return pts_

        def limb(a_, b_, width, base, light=None):
            aa, bb = pt(*a_), pt(*b_)
            _NS_zephyr._aaline(surface, p["shadow_deep"],
                               (aa[0] + f, aa[1] + 1),
                               (bb[0] + f, bb[1] + 1), width + 3)
            _NS_zephyr._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_zephyr._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        # ── back layers: wings and thorn-crown silhouette ───────────
        _NS_zephyr._draw_elite_wings(surface, pt, f, phase, action,
                                     detail, bedlam)
        _NS_zephyr._draw_zephyr_crown(surface, pt, f, phase, detail)

        # ── Long asymmetric night-violet mantle ─────────────────────
        mantle_wave = int(math.sin(phase * 1.18) * 3.5)
        mp = 9 if (walk or attack) else 0
        poly(p["cloak_darkest"],
             [(-9, -26), (-20, -18),
              (-30 - mp, -2 + mantle_wave),
              (-34 - mp, 22 + mantle_wave),
              (-22, 17), (-11, 5), (-3, -14)])
        poly(p["cloak_dark"],
             [(-10, -24), (-18, -16),
              (-26 - mp, 0 + mantle_wave),
              (-28 - mp, 16 + mantle_wave),
              (-19, 12), (-9, 2)], False)
        _NS_zephyr._aaline(surface, p["cloak_light"],
                           pt(-14, -19), pt(-27 - mp, 12 + mantle_wave), 1)

        # ── Foot solver — planted boots with knee lift ──────────────
        front_step = int(stride * 5.0) if walk else 0
        rear_step  = -front_step
        if attack:
            front_step += int(ap * 6)
            rear_step  -= int(ap * 4)
        stride_vel   = math.cos(phase * 1.72) if walk else 0.0
        front_lift   = int(max(0.0, stride_vel) * 10) if walk else 0
        rear_lift    = int(max(0.0, -stride_vel) * 10) if walk else 0

        legs = ((-8, rear_step,  p["boot_dark"],  p["boot_mid"],   rear_lift),
                ( 8, front_step, p["boot_mid"],   p["boot_light"], front_lift))
        for side_, step_, boot_base, boot_lgt, lift_ in legs:
            thigh_x = side_ + step_
            # Tights above boot (knee rises with lift)
            poly(p["dress_darkest"],
                 [(thigh_x - 5, 16), (thigh_x + 5, 16),
                  (thigh_x + 4, 32 - lift_), (thigh_x - 4, 32 - lift_)])
            poly(p["dress_mid"],
                 [(thigh_x - 3, 18), (thigh_x + 3, 18),
                  (thigh_x + 2, 31 - lift_), (thigh_x - 3, 31 - lift_)],
                 False)
            _NS_zephyr._aaline(surface, p["dress_light"],
                               pt(thigh_x - 1, 19),
                               pt(thigh_x - 1, 30 - lift_), 1)
            # Boot cuff, heel, toe
            poly(p["boot_darkest"],
                 [(thigh_x - 7, 30 - lift_), (thigh_x + 6, 30 - lift_),
                  (thigh_x + 7, 44 - lift_), (thigh_x - 6, 44 - lift_)])
            poly(boot_base,
                 [(thigh_x - 5, 31 - lift_), (thigh_x + 4, 31 - lift_),
                  (thigh_x + 5, 42 - lift_), (thigh_x - 5, 42 - lift_)],
                 False)
            _NS_zephyr._aaline(surface, boot_lgt,
                               pt(thigh_x - 2, 33 - lift_),
                               pt(thigh_x - 1, 41 - lift_), 1)
            # Contact shadow under planted foot
            toe = 4 * f
            foot = pt(thigh_x + (3 if f > 0 else -3), 44 - lift_)
            _NS_zephyr._aaline(surface, p["shadow_deep"],
                               (foot[0] - toe, foot[1] + 1),
                               (foot[0] + toe, foot[1] + 1), 4)
            _NS_zephyr._aaline(surface, p["boot_light"],
                               (foot[0] - toe, foot[1]),
                               (foot[0] + toe, foot[1]), 2)

        # ── Gown: 4 independent petal panels ───────────────────────
        skirt_wave = math.sin(phase * 1.1) * 2.5
        for i, (bx_, bw_, bl_) in enumerate(
                ((-15, 10, 30), (-5, 11, 34), (6, 11, 32), (16, 9, 26))):
            sway = int(skirt_wave * (1.0 + (i % 2) * .35) +
                       (stride * (i - 1.5) if walk else 0))
            dark = p["dress_darkest"] if i in (0, 3) else p["dress_dark"]
            mid  = p["dress_mid"] if i != 1 else p["dress_light"]
            panel = [(bx_ - bw_ // 2, 0), (bx_ + bw_ // 2, 0),
                     (bx_ + bw_ // 2 + sway, bl_ - 5),
                     (bx_ + sway, bl_),
                     (bx_ - bw_ // 2 + sway - 2, bl_ - 5)]
            poly(dark, panel)
            inset = [(bx_ - bw_ // 2 + 2, 2),
                     (bx_ + bw_ // 2 - 2, 2),
                     (bx_ + bw_ // 2 - 1 + sway, bl_ - 7),
                     (bx_ + sway, bl_ - 3),
                     (bx_ - bw_ // 2 + 1 + sway, bl_ - 7)]
            poly(mid, inset, False)
            _NS_zephyr._aaline(surface, p["dress_high"],
                               pt(bx_ - 1, 5), pt(bx_ + sway, bl_ - 5), 1)
            if i == 1:
                _NS_zephyr._aacircle(surface, p["jewel_light"],
                                     pt(bx_, 14), 1)
        # Dither band at hem (pixel-art texture)
        for di in range(6):
            _NS_zephyr._aacircle(surface,
                                 (*p["dress_high"],
                                  int(110 + math.sin(phase * 1.1 + di) * 30)),
                                 pt(-10 + di * 4,
                                    32 + (di % 2) * 2), 1)

        # ── Fitted torso + corset + shoulder pauldrons ──────────────
        poly(p["dress_darkest"],
             [(-13, -28), (-5, -34), (9, -32),
              (15, -24), (12, 4), (5, 9), (-9, 7), (-14, -6)])
        poly(p["dress_mid"],
             [(-10, -27), (-4, -31), (8, -30),
              (12, -23), (9, 3), (3, 6), (-7, 5), (-11, -6)], False)
        poly(p["dress_high"],
             [(-5, -27), (4, -30), (8, -27),
              (8, -18), (5, -10), (1, -6)], False)
        # Dither band across torso (highlight warmth left-side)
        for di in range(5):
            yy = -24 + di * 6
            alpha_d = 180 - di * 20
            _NS_zephyr._aacircle(surface,
                                 (*p["dress_light"], alpha_d),
                                 pt(-4 + di, yy), 1)
        # Pauldron (left shoulder)
        poly(p["cloak_dark"],
             [(-14, -27), (-19, -34), (-14, -39),
              (-5, -34), (-8, -27)])
        poly(p["cloak_mid"],
             [(-14, -29), (-17, -34), (-13, -36),
              (-7, -33), (-9, -29)], False)
        _NS_zephyr._aaline(surface, p["cloak_light"],
                           pt(-17, -34), pt(-14, -39), 1)
        # Pauldron (right shoulder)
        poly(p["cloak_dark"],
             [(9, -31), (16, -36), (22, -30),
              (18, -22), (11, -24)])
        poly(p["cloak_mid"],
             [(10, -30), (15, -34), (20, -29),
              (17, -24), (12, -26)], False)
        _NS_zephyr._aaline(surface, p["cloak_light"],
                           pt(11, -31), pt(18, -30), 1)
        # Corset — deliberately dark charcoal-plum
        poly(p["corset_dark"],
             [(-8, -22), (9, -22), (9, 2),
              (4, 6), (-6, 5), (-9, 1)])
        poly(p["corset_mid"],
             [(-6, -20), (7, -20), (7, 1),
              (3, 4), (-5, 3), (-7, 1)], False)
        _NS_zephyr._aaline(surface, p["corset_light"],
                           pt(-4, -19), pt(4, 2), 1)
        # Lace crosshatch
        for j in range(5):
            yy = -17 + j * 4
            _NS_zephyr._aaline(surface, p["rune_light"],
                               pt(-4, yy), pt(4, yy + 2), 1)
            _NS_zephyr._aaline(surface, p["rune_light"],
                               pt(4, yy), pt(-4, yy + 2), 1)
        # Belt & buckle
        _NS_zephyr._aaline(surface, p["gold_dark"], pt(-12, 5), pt(12, 5), 4)
        _NS_zephyr._aaline(surface, p["gold_mid"],  pt(-11, 5), pt(11, 5), 2)
        bkl = pt(1, 5)
        _NS_zephyr._aacircle(surface, p["gold_light"], bkl, 3)
        _NS_zephyr._aacircle(surface, p["jewel_mid"],  bkl, 1)

        # ── Rear arm (free / casting hand) ─────────────────────────
        rear_shoulder = (-9, -24)
        if attack:
            # Tangan belakang MENOPANG batang (dua tangan), bukan
            # melayang di ujung tongkat: panjang lengan tetap.
            (_fs, _fe, _fh, rear_shoulder, rear_elbow,
             rear_hand, _gt) = _NS_zephyr._arm_pose_local(phase, action, ap)
        elif walk:
            rear_hand  = (-15, -4 + int(stride * 6))
            rear_elbow = (-18, -15 - int(stride * 3))
        else:
            rear_hand  = (-14, -4 + int(breath * 2.5))
            rear_elbow = (-18, -16 + int(breath))
        limb(rear_shoulder, rear_elbow, 7, p["cloak_dark"], p["cloak_mid"])
        limb(rear_elbow, rear_hand, 6, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], (rhx, rhy), 5)
        _NS_zephyr._aacircle(surface, p["skin_mid"],     (rhx, rhy), 4)
        _NS_zephyr._aacircle(surface, p["skin_light"],   (rhx-f, rhy-1), 1)
        for finger in (-2, 0, 2, 4):
            _NS_zephyr._aaline(surface, p["skin_light"],
                               (rhx + f, rhy + finger),
                               (rhx + f * 5, rhy + finger - 2), 1)

        # ── Head and face ───────────────────────────────────────────
        poly(p["skin_darkest"],
             [(-5, -36), (6, -36), (6, -27), (-4, -26)])
        poly(p["skin_mid"],
             [(-2, -36), (3, -36), (3, -28), (-1, -27)], False)
        # 3/4 face wedge — fuller shape (v2: slightly larger)
        poly(p["skin_darkest"],
             [(-11, -56), (2, -62), (13, -54),
              (15, -42), (10, -33), (-2, -31),
              (-11, -38), (-14, -48)])
        poly(p["skin_dark"],
             [(-9, -54), (2, -58), (11, -51),
              (12, -42), (7, -35), (-1, -33),
              (-9, -39), (-11, -47)], False)
        poly(p["skin_mid"],
             [(-6, -52), (2, -55), (8, -50),
              (9, -43), (5, -37), (0, -35),
              (-7, -40)], False)
        poly(p["skin_light"],
             [(0, -53), (6, -51), (7, -44),
              (3, -40), (-2, -42)], False)
        # Specular cluster (key-light upper-left)
        _NS_zephyr._aacircle(surface, p["skin_high"],   pt(-1, -52), 2)
        _NS_zephyr._aacircle(surface, p["skin_high"],   pt(2,  -54), 1)
        # Ear
        _NS_zephyr._aacircle(surface, p["skin_mid"],    pt(-10, -45), 3)
        _NS_zephyr._aacircle(surface, p["skin_light"],  pt(-11, -46), 1)
        # Eyes (two visible from 3/4)
        for ex_, ey_, er_ in ((-2, -46, 2), (7, -46, 3)):
            ox, oy = pt(ex_, ey_)
            _NS_zephyr._aacircle(surface, p["eye_white"], (ox, oy), er_)
            _NS_zephyr._aacircle(surface, p["eye_iris"],  (ox+f, oy), max(1,er_-1))
            _NS_zephyr._aacircle(surface, p["eye_iris_light"], (ox+f, oy-1), 1)
            _NS_zephyr._aacircle(surface, p["eye_pupil"], (ox+f, oy), 1)
            _NS_zephyr._aacircle(surface, p["white"],     (ox, oy-1), 1)
        # Blink
        if int(phase * 3.7) % 37 == 0 and not attack:
            bx, by = pt(7, -46)
            _NS_zephyr._aaline(surface, p["hair_darkest"],
                               (bx-3, by), (bx+3, by), 2)
        # Eyebrows
        _NS_zephyr._aaline(surface, p["hair_darkest"],
                           pt(-5, -50), pt(1, -51), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"],
                           pt(3, -51), pt(11, -50), 1)
        # Nose tip
        _NS_zephyr._aacircle(surface, p["skin_darkest"], pt(12, -42), 1)
        # Lips
        _NS_zephyr._aaline(surface, p["lips_dark"],
                           pt(4, -37), pt(9, -37), 2)
        _NS_zephyr._aaline(surface, p["lips_mid"],
                           pt(5, -37), pt(8, -37), 1)
        # Hair fringe — covers brow
        poly(p["hair_darkest"],
             [(-12, -55), (-8, -66), (1, -70),
              (11, -63), (14, -54), (8, -51),
              (5, -56), (1, -50), (-2, -56), (-7, -51)])
        poly(p["hair_dark"],
             [(-9, -56), (-6, -63), (1, -67),
              (9, -60), (11, -55), (5, -53),
              (1, -58), (-3, -53)], False)
        # Five irregular bangs (secondary motion)
        bangs = [(-8, -59, -9, -51), (-4, -63, -5, -53),
                 (1, -65, 0, -53), (6, -62, 5, -52),
                 (10, -58, 9, -52)]
        for bi, (sx_, sy_, ex_, ey_) in enumerate(bangs):
            wiggle = hair_sway if bi % 2 else -hair_sway
            poly(p["hair_mid"],
                 [(sx_ - 2, sy_), (sx_ + 2, sy_),
                  (ex_ + wiggle, ey_),
                  (ex_ - 2 + wiggle, ey_ + 2)], False)
            _NS_zephyr._aaline(surface, p["hair_light"],
                               pt(sx_, sy_ + 1),
                               pt(ex_ + wiggle, ey_), 1)
        _NS_zephyr._aacircle(surface, p["hair_shine"], pt(2, -64), 1)

        # ── Thorn staff ─────────────────────────────────────────────
        staff_top    = _NS_zephyr._staff_tip_local(phase, action, ap)
        if attack:
            staff_bottom = _NS_zephyr._staff_bottom_local(phase, action, ap)
        else:
            staff_bottom = (2 + int(stride * 2 if walk else 0), 28)
        _NS_zephyr._draw_elite_staff(surface, pt, f,
                                     staff_bottom, staff_top,
                                     phase, action, detail,
                                     glow=bedlam)

        # ── ATTACK TRAIL (tepat di atas senjata) ────────────────────
        if attack:
            _NS_zephyr._draw_staff_swing_trail(surface, pt, phase, ap)

        # ── Front staff arm ─────────────────────────────────────────
        # Genggaman digeser sepanjang batang sampai terjangkau, lalu
        # siku dihitung IK -> panjang lengan KONSTAN di semua frame.
        front_shoulder = (9, -24)
        if attack:
            (front_shoulder, front_elbow, grip,
             _rs, _re, _rh, _gt) = _NS_zephyr._arm_pose_local(
                phase, action, ap)
        else:
            (front_shoulder, front_elbow, grip,
             _rs, _re, _rh, _gt) = _NS_zephyr._arm_pose_local(
                phase, action, ap)
            if walk:
                front_elbow = (front_elbow[0], front_elbow[1]
                               + int(stride * 2))
        limb(front_shoulder, front_elbow, 7, p["cloak_mid"], p["cloak_light"])
        limb(front_elbow, grip, 6, p["skin_dark"], p["skin_light"])
        ghx, ghy = pt(*grip)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], (ghx, ghy), 5)
        _NS_zephyr._aacircle(surface, p["skin_mid"],     (ghx, ghy), 4)
        _NS_zephyr._aacircle(surface, p["skin_high"],    (ghx-f, ghy-1), 1)
        # Gold cuff and rings on staff hand
        _NS_zephyr._aaline(surface, p["gold_dark"],
                           pt(front_elbow[0], front_elbow[1]),
                           pt((front_elbow[0]+grip[0])//2,
                              (front_elbow[1]+grip[1])//2), 4)
        _NS_zephyr._aaline(surface, p["gold_light"],
                           pt(front_elbow[0], front_elbow[1]-1),
                           pt((front_elbow[0]+grip[0])//2,
                              (front_elbow[1]+grip[1])//2 - 1), 1)
        _NS_zephyr._aacircle(surface, p["gold_light"], (ghx+f*2, ghy), 1)

        # ── Side locks and thorn earrings ───────────────────────────
        poly(p["hair_dark"],
             [(-9, -52), (-14, -48),
              (-18 - hair_sway, -34), (-12, -30), (-6, -41)], False)
        _NS_zephyr._aaline(surface, p["hair_light"],
                           pt(-11, -49),
                           pt(-15 - hair_sway, -35), 1)
        _NS_zephyr._aacircle(surface, p["jewel_light"], pt(-11, -42), 2)
        _NS_zephyr._aacircle(surface, p["jewel_mid"],   pt(-11, -42), 1)

        # ── Bedlam glow: staff and corset flare magenta ─────────────
        if bedlam:
            otx, oty = pt(*staff_top)
            pulse = .8 + math.sin(phase * 3.2) * .2
            _NS_zephyr._aacircle(surface,
                                 (*p["magic_bright"], int(80 * pulse)),
                                 (otx, oty), int(22 * pulse))
            _NS_zephyr._aacircle(surface,
                                 (*p["magic_hot"], int(130 * pulse)),
                                 (otx, oty), int(12 * pulse))
            # Corset lace glows
            for j in range(5):
                yy = -17 + j * 4
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_light"], int(90 * pulse)),
                                     pt(-4 + j, yy), 1)

        # ── Floating motes ──────────────────────────────────────────
        n_motes = 4 if not detail else 8
        for i in range(n_motes):
            t = (phase * .22 + i / float(n_motes)) % 1.0
            dx_ = -24 + i * 9 + int(math.sin(phase * 1.4 + i) * 3)
            dy_ = 24 - int(t * 62)
            _NS_zephyr._aacircle(
                surface, (*p["magic_bright"], int(150 * (1 - t))),
                pt(dx_, dy_), 1 if i % 2 else 2)

        # ── Attack orb orbiting particles ───────────────────────────
        if attack:
            orb_x, orb_y = pt(*staff_top)
            for i in range(4):
                ang_ = phase * 2.2 + i * math.pi / 4
                r_   = 8 + int(math.sin(phase + i) * 2)
                _NS_zephyr._aacircle(surface, (*p["magic_hot"], 200),
                                     (orb_x + int(math.cos(ang_) * r_),
                                      orb_y + int(math.sin(ang_) * r_)), 1)

        # ── Impact burst at mid-swing ───────────────────────────────
        if attack and abs(ap - _NS_zephyr.ATTACK_IMPACT_FRAME) < 0.07:
            orb_x, orb_y = pt(*staff_top)
            t = 1.0 - abs(ap - _NS_zephyr.ATTACK_IMPACT_FRAME) / 0.07
            _NS_zephyr._spark_star(
                surface, orb_x, orb_y, int(30 * t),
                p["magic_bright"], int(245 * t), spikes=8,
                rot=phase, core=p["magic_white"])
            _NS_zephyr._aacircle(surface,
                                 (*p["magic_hot"], int(210 * t)),
                                 (orb_x, orb_y), int(9 * t))
            # kilat benturan: cincin tipis + pecahan busur
            _NS_zephyr._aacircle(surface,
                                 (*p["magic_white"], int(160 * t)),
                                 (orb_x, orb_y), int(20 + 10 * (1 - t)), 2)
            for k in (-1, 0, 1):
                a_ = -0.5 + k * 0.55
                _NS_zephyr._aaline(
                    surface, (*p["magic_hot"], int(200 * t)),
                    (orb_x + int(math.cos(a_) * 10 * f),
                     orb_y + int(math.sin(a_) * 10)),
                    (orb_x + int(math.cos(a_) * (22 + 8 * t) * f),
                     orb_y + int(math.sin(a_) * (22 + 8 * t))), 2)

        # ── Portrait detail pass ────────────────────────────────────
        if detail:
            _NS_zephyr._draw_zephyr_masterwork_details(
                surface, pt, f, phase, action)

    # ── Wings ───────────────────────────────────────────────────────
    def _draw_elite_wings(surface, pt, f, phase, action, detail=False,
                          bedlam=False):
        """Two pairs of translucent moth wings — v2: larger + richer."""
        p = _NS_zephyr.PALETTE
        flap = math.sin(phase * 3.2) * .14 + .86
        if action == "attack":
            flap += .10
        if action == "walk":
            flap += math.sin(phase * 1.72) * .06

        bedlam_glow = bedlam

        def wing_poly(color, coords, outline=True):
            pts_ = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                 [(x + f, y + 1) for x, y in pts_])
            _NS_zephyr._poly(surface, color, pts_)

        for side in (-1, 1):
            lift = int((1.0 - flap) * 26)
            # Upper wing (tall, thorned moth)
            upper = [(side*3, -28), (side*14, -50+lift),
                     (side*32, -70+lift), (side*44, -60+lift),
                     (side*37, -36), (side*22, -20), (side*7, -21)]
            wing_poly(p["wing_darkest"], upper)
            wing_poly((*p["wing_dark"], 220), [
                (side*5, -28), (side*16, -48+lift),
                (side*31, -65+lift), (side*38, -57+lift),
                (side*32, -37), (side*20, -22), (side*8, -23)], False)
            wing_poly((*p["wing_mid"], 165), [
                (side*8, -28), (side*20, -47+lift),
                (side*30, -61+lift), (side*32, -52+lift),
                (side*26, -37), (side*16, -25)], False)
            # Glass highlight patches
            if detail or bedlam_glow:
                wing_poly((*p["wing_glass"], 80), [
                    (side*16, -42+lift), (side*26, -52+lift),
                    (side*24, -45+lift), (side*14, -36)], False)

            # Lower wing (rounder cadence)
            low_lift = int(math.sin(phase * 2.4 + side) * 2.5)
            lower = [(side*5, -20), (side*24, -21+low_lift),
                     (side*39, -6+low_lift), (side*32, 11),
                     (side*15, 10), (side*6, -4)]
            wing_poly(p["wing_darkest"], lower)
            wing_poly((*p["wing_dark"], 220), [
                (side*7, -19), (side*23, -19+low_lift),
                (side*34, -5+low_lift), (side*28, 7),
                (side*15, 7), (side*8, -3)], False)
            wing_poly((*p["wing_mid"], 150), [
                (side*9, -17), (side*22, -14+low_lift),
                (side*30, -3+low_lift), (side*24, 4),
                (side*15, 3)], False)

            # Veins
            root_ = pt(side*5, -24)
            tips_ = (pt(side*32, -64+lift),
                     pt(side*35, -9+low_lift),
                     pt(side*26, -37+lift))
            for tx_, ty_ in tips_:
                _NS_zephyr._aaline(surface, p["wing_vein"],
                                   root_, (tx_, ty_), 2)
                _NS_zephyr._aaline(surface, (*p["wing_shine"], 160),
                                   root_, (tx_, ty_), 1)
                # Solid specular pixel at each vein tip (key-light left-top)
                _NS_zephyr._aacircle(surface, p["wing_shine"],
                                     (tx_, ty_), 1)

            # Bedlam pulse overlay
            if bedlam_glow:
                bx_, by_ = pt(side*22, -48+lift)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_light"], 70),
                                     (bx_, by_), 12)
                _NS_zephyr._aacircle(surface,
                                     (*p["wing_shine"], 100),
                                     (bx_, by_), 6)

    # ── Crown ───────────────────────────────────────────────────────
    def _draw_zephyr_crown(surface, pt, f, phase, detail=False):
        """Crimson thorn crown — v2: denser spikes, secondary motion."""
        p = _NS_zephyr.PALETTE

        def crown_poly(color, coords, outline=True):
            pts_ = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                 [(x + f, y + 1) for x, y in pts_])
            _NS_zephyr._poly(surface, color, pts_)

        # Main crown mass
        crown_poly(p["hair_darkest"],
                   [(-14, -50), (-30, -52),
                    (-38, -62), (-32, -72), (-41, -78),
                    (-26, -82), (-28, -94), (-14, -88),
                    (-7, -102), (2, -88), (13, -80),
                    (18, -66), (13, -54), (4, -58), (-6, -55)])
        crown_poly(p["hair_dark"],
                   [(-12, -52), (-26, -55),
                    (-33, -62), (-27, -68), (-34, -74),
                    (-22, -76), (-23, -84), (-12, -78),
                    (-6, -92), (1, -78), (10, -72),
                    (13, -63), (9, -55), (1, -59)], False)
        crown_poly(p["hair_mid"],
                   [(-16, -56), (-27, -62),
                    (-24, -70), (-16, -73), (-11, -84),
                    (-4, -74), (4, -74), (8, -66), (4, -60)],
                   False)

        # 9 individual spikes with secondary motion
        spikes = [
            (-14, -57, -34, -68), (-18, -61, -42, -80),
            (-16, -67, -32, -92), (-10, -70, -18, -96),
            (-3,  -72, -5, -100), ( 5,  -68,  9, -88),
            (10,  -62, 22, -76),  (14,  -57, 26, -66),
            (-22, -72, -44, -84),
        ]
        for si, (sx_, sy_, ex_, ey_) in enumerate(spikes):
            wave_ = int(math.sin(phase * 1.18 + si * .73) * (1 + si % 3))
            crown_poly(p["hair_darkest"],
                       [(sx_ - 4, sy_ + 2), (sx_ + 4, sy_ + 2),
                        (ex_ + wave_, ey_), (sx_ + 1, sy_ - 5)])
            crown_poly(p["hair_mid"],
                       [(sx_ - 1, sy_), (sx_ + 2, sy_),
                        (ex_ + wave_, ey_ + 4), (sx_, sy_ - 2)], False)
            _NS_zephyr._aaline(surface, p["hair_light"],
                               pt(sx_, sy_ - 1),
                               pt(ex_ + wave_, ey_ + 4), 1)
            if si in (1, 3, 5, 7):
                _NS_zephyr._aacircle(surface, p["hair_tip"],
                                     pt(ex_ + wave_, ey_ + 3), 1)

        # Gold circlet and amethyst pins
        _NS_zephyr._aaline(surface, p["gold_dark"],
                           pt(-13, -60), pt(12, -62), 3)
        _NS_zephyr._aaline(surface, p["gold_mid"],
                           pt(-12, -61), pt(11, -63), 1)
        for dx_ in (-8, -1, 7):
            bx_, by_ = pt(dx_, -61)
            _NS_zephyr._poly(surface, p["thorn_dark"],
                             [(bx_, by_), (bx_ + f*4, by_ - 6),
                              (bx_ + f*6, by_)])
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                 (bx_ + f, by_), 1)
        if detail:
            for dx_, dy_ in ((-28, -64), (-22, -74), (-15, -80),
                              (-7, -86), (2, -78)):
                _NS_zephyr._aaline(surface, p["hair_shine"],
                                   pt(dx_, dy_), pt(dx_+3, dy_-6), 1)

    # ── Staff ───────────────────────────────────────────────────────
    def _draw_elite_staff(surface, pt, f, bottom, top, phase, action,
                          detail=False, glow=False):
        """Living thorn staff v2 — larger crystal + vine coils."""
        p = _NS_zephyr.PALETTE
        bx_, by_ = pt(*bottom)
        tx_, ty_ = pt(*top)
        # Shadow
        _NS_zephyr._aaline(surface, p["shadow_deep"],
                           (bx_+f*2, by_+1), (tx_+f*2, ty_+1), 9)
        # Shaft bands (3-tone wood)
        _NS_zephyr._aaline(surface, p["staff_dark"],  (bx_, by_), (tx_, ty_), 7)
        _NS_zephyr._aaline(surface, p["staff_mid"],   (bx_-f, by_), (tx_-f, ty_), 5)
        _NS_zephyr._aaline(surface, p["staff_light"],
                           (bx_-f*2, by_-1), (tx_-f*2, ty_-1), 1)

        # Vine coils
        dx_, dy_ = tx_ - bx_, ty_ - by_
        length_ = max(1.0, math.hypot(dx_, dy_))
        nx_, ny_ = -dy_/length_, dx_/length_
        for i in range(6):
            t_ = .12 + i * .14
            sx_, sy_ = bx_ + dx_*t_, by_ + dy_*t_
            swirl = math.sin(phase * 1.8 + i * 1.7) * 2.5
            ex_, ey_ = sx_ + nx_*(6+swirl), sy_ + ny_*(6+swirl)
            _NS_zephyr._aaline(surface, p["staff_vine"],
                               (int(sx_), int(sy_)), (int(ex_), int(ey_)), 2)
            _NS_zephyr._aaline(surface, p["thorn_light"],
                               (int(ex_), int(ey_)),
                               (int(ex_ + nx_*3 + dx_/length_*2),
                                int(ey_ + ny_*3 + dy_/length_*2)), 1)

        # Crystal orb: halo -> faceted gem -> concentrated core
        orb_pulse = .72 + math.sin(phase * 2.5) * .20
        glow_boost = 1.4 if glow else 1.0
        for radius_, color_, alpha_ in (
                (18, p["magic_dark"],   int(52 * orb_pulse * glow_boost)),
                (13, p["magic_mid"],    int(110 * orb_pulse * glow_boost)),
                ( 8, p["magic_bright"], int(200 * orb_pulse * glow_boost))):
            _NS_zephyr._aacircle(surface, (*color_, min(255, alpha_)),
                                 (tx_, ty_), radius_)
        # Faceted gem body
        _NS_zephyr._poly(surface, p["jewel_dark"],
                         [(tx_, ty_-9), (tx_+f*7, ty_-1),
                          (tx_+f*2, ty_+8), (tx_-f*6, ty_+2)])
        _NS_zephyr._poly(surface, p["jewel_mid"],
                         [(tx_, ty_-6), (tx_+f*5, ty_-1),
                          (tx_+f*1, ty_+6), (tx_-f*4, ty_+1)])
        _NS_zephyr._aaline(surface, p["staff_glow"],
                           (tx_, ty_-6), (tx_+f*4, ty_+1), 2)
        _NS_zephyr._aacircle(surface, p["jewel_light"],  (tx_-f*2, ty_-3), 3)
        _NS_zephyr._aacircle(surface, p["magic_white"],  (tx_-f*2, ty_-4), 1)
        # Forked thorn crown
        for side in (-1, 1):
            _NS_zephyr._aaline(surface, p["thorn_dark"],
                               (tx_, ty_+3),
                               (tx_+f*side*8, ty_-10), 3)
            _NS_zephyr._aaline(surface, p["thorn_light"],
                               (tx_+f*side, ty_+1),
                               (tx_+f*side*7, ty_-8), 1)
        if detail:
            for i in range(5):
                t_ = .20 + i * .14
                rx_, ry_ = int(bx_+dx_*t_), int(by_+dy_*t_)
                _NS_zephyr._aacircle(surface, p["rune_light"], (rx_, ry_), 1)

    # ── Portrait detail pass ────────────────────────────────────────
    def _draw_zephyr_masterwork_details(surface, pt, f, phase, action):
        """Portrait-only: seams, wing spots and jewelry."""
        p = _NS_zephyr.PALETTE
        # Corset gold stitching
        for yy in range(-20, 3, 3):
            _NS_zephyr._aacircle(surface, p["gold_light"], pt(0, yy), 1)
        # Hem embroidery
        for i in range(4):
            y_ = 11 + i * 6
            _NS_zephyr._aaline(surface, p["dress_high"],
                               pt(-3, y_), pt(2, y_+3), 1)
            _NS_zephyr._aacircle(surface, p["jewel_light"], pt(3, y_+2), 1)
        # Collar rivets and wing root jewelry
        for dx_, dy_ in ((-12, -27), (12, -26), (-6, -30), (7, -30)):
            _NS_zephyr._aacircle(surface, p["gold_mid"], pt(dx_, dy_), 1)
        _NS_zephyr._aacircle(surface, p["jewel_light"], pt(-14, -21), 2)
        # Face detail: lashes, beauty mark, cheek flush
        _NS_zephyr._aaline(surface, p["skin_high"],  pt(1, -53), pt(6, -52), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"],
                           pt(6, -49), pt(11, -50), 1)
        _NS_zephyr._aacircle(surface, p["lips_dark"], pt(9, -40), 1)
        # Hem stitch rhythm
        hem_p = int(math.sin(phase * 1.1) * 2)
        for dx_ in (-12, -6, 0, 6, 12):
            _NS_zephyr._aacircle(surface, p["thread_light"],
                                 pt(dx_+hem_p, 28 + abs(dx_)//5), 1)

    # ---------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------
    class MagicBoltProjectile:
        """Pink magic bolt basic attack — v2: richer trail + glint."""
        def __init__(self, sx, sy, tx, ty, speed=7.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                self.dead_frames += 1
                return
            self.age += 1
            if self.target is not None and getattr(self.target, 'alive', False):
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_zephyr._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 16:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            p = _NS_zephyr.PALETTE
            # Two-tone trail
            for i, (tx_, ty_) in enumerate(self.trail):
                alpha_ = int(20 + i * 15)
                r_ = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_dark"], alpha_), (tx_, ty_), r_+2)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_mid"], alpha_//2), (tx_, ty_), r_)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_bright"], alpha_//2),
                                     (tx_, ty_), max(1, r_-2))
            if self.alive:
                px_, py_ = int(self.x), int(self.y)
                ca_, sa_ = math.cos(self.angle), math.sin(self.angle)
                # Halos
                _NS_zephyr._aacircle(surface, (*p["magic_dark"], 130),
                                     (px_, py_), 14)
                _NS_zephyr._aacircle(surface, (*p["magic_mid"], 180),
                                     (px_, py_), 10)
                # Elongated bolt
                for i in range(7):
                    t_ = i / 6.0
                    bx_ = px_ - ca_ * 14 * t_
                    by_ = py_ - sa_ * 14 * t_
                    r_  = max(1, int(5 * (1-t_)))
                    al_ = int(240 * (1-t_*.6))
                    _NS_zephyr._aacircle(surface,
                                         (*p["magic_mid"], al_),
                                         (int(bx_), int(by_)), r_+1)
                    _NS_zephyr._aacircle(surface,
                                         (*p["magic_light"], al_),
                                         (int(bx_), int(by_)), r_)
                    _NS_zephyr._aacircle(surface,
                                         (*p["magic_hot"], al_),
                                         (int(bx_), int(by_)), max(1,r_-1))
                # Core + glint at tip
                _NS_zephyr._aacircle(surface, p["magic_white"], (px_, py_), 3)
                _NS_zephyr._aacircle(surface, p["white"],       (px_, py_), 1)
                # Glint orbit at tip
                for i in range(4):
                    ang_ = phase * 5.0 + i * math.pi / 2
                    gr_ = 5
                    gpx_ = px_ + int(math.cos(ang_) * gr_)
                    gpy_ = py_ + int(math.sin(ang_) * gr_)
                    _NS_zephyr._aacircle(surface,
                                         (*p["magic_bright"], 200),
                                         (gpx_, gpy_), 1)

    class CasketProjectile:
        """Casket Curse — flying skull with layered trail + glint."""
        def __init__(self, sx, sy, tx, ty, speed=5.5,
                     target=None, damage=0, team=None):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.dead_frames = 0
            self.trail = []
            self.target = target
            self.damage = damage
            self.team = team
            self.impact_frame = -1
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                self.dead_frames += 1
                return
            self.age += 1
            if self.impact_frame >= 0:
                if self.age - self.impact_frame > 30:
                    self.alive = False
                return
            if self.target is not None and getattr(self.target, 'alive', False):
                src = getattr(self, "source", None)
                if src is not None:
                    self.tx, self.ty = _NS_zephyr._world_to_local(
                        src, self.cx, self.cy,
                        self.target.x, self.target.y)
                else:
                    self.tx = float(self.target.x)
                    self.ty = float(self.target.y)
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                self.angle = math.atan2(dy, dx)
            if dist < self.speed + 4:
                self.impact_frame = self.age
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 18:
                self.trail.pop(0)
            self.x += (dx/dist) * self.speed
            self.y += (dy/dist) * self.speed

        def draw(self, surface, phase):
            p = _NS_zephyr.PALETTE
            if self.impact_frame >= 0:
                elapsed = self.age - self.impact_frame
                t_ = elapsed / 30.0
                # Star burst impact
                _NS_zephyr._spark_star(surface,
                                       int(self.tx), int(self.ty),
                                       int(28 + t_*20),
                                       p["magic_light"],
                                       int(220*(1-t_)), spikes=8,
                                       rot=phase*0.1,
                                       core=p["magic_white"])
                for r_, col_, al_ in (
                        (int(22+t_*32), p["magic_dark"],   int(200*(1-t_))),
                        (int(16+t_*26), p["magic_mid"],    int(220*(1-t_))),
                        (int( 9+t_*22), p["magic_bright"], int(240*(1-t_)))):
                    _NS_zephyr._aacircle(surface, (*col_, al_),
                                         (int(self.tx), int(self.ty)), r_)
                # Dust sparks
                for i in range(6):
                    sa_ = i * math.pi * 2 / 12 + phase*0.3
                    sr_ = int(t_ * 46)
                    sx_, sy_ = (int(self.tx + math.cos(sa_)*sr_),
                                int(self.ty + math.sin(sa_)*sr_))
                    _NS_zephyr._aacircle(surface,
                                         (*p["magic_bright"], int(200*(1-t_))),
                                         (sx_, sy_), 2)
                return

            # Two-tone trail
            for i, (tx_, ty_) in enumerate(self.trail):
                alpha_ = int(30 + i * 12)
                r_ = max(1, 4 - (len(self.trail)-i)//2)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_dark"], alpha_), (tx_, ty_), r_+3)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_mid"], alpha_),  (tx_, ty_), r_+1)
                _NS_zephyr._aacircle(surface,
                                     (*p["magic_bright"], alpha_//2),
                                     (tx_, ty_), r_)

            if self.alive:
                px_, py_ = int(self.x), int(self.y)
                # Halos
                _NS_zephyr._aacircle(surface, (*p["magic_dark"], 180),
                                     (px_, py_), 13)
                _NS_zephyr._aacircle(surface, (*p["magic_mid"], 200),
                                     (px_, py_), 10)
                # Skull: dome
                _NS_zephyr._aacircle(surface, p["magic_dark"],  (px_, py_), 7)
                _NS_zephyr._aacircle(surface, p["magic_mid"],   (px_, py_-1), 6)
                _NS_zephyr._aacircle(surface, p["magic_light"], (px_-1, py_-2), 3)
                # Eye sockets with glow
                for ex_ in (-2, 2):
                    _NS_zephyr._aacircle(surface, p["shadow_deep"],
                                         (px_+ex_, py_-1), 1)
                    _NS_zephyr._aacircle(surface, p["magic_hot"],
                                         (px_+ex_, py_-1), 1)
                # Jaw
                _NS_zephyr._aaline(surface, p["shadow_deep"],
                                   (px_-2, py_+4), (px_+2, py_+4), 1)
                # Glint orbit around skull
                for i in range(3):
                    ag_ = phase*4.5 + i * math.tau/3
                    _NS_zephyr._aacircle(surface, p["magic_bright"],
                                         (px_+int(math.cos(ag_)*8),
                                          py_+int(math.sin(ag_)*8)), 1)
                # Tendrils
                for i in range(3):
                    ag_ = math.pi + self.angle + (i-1)*0.3
                    tx__, ty__ = (px_+math.cos(ag_)*9,
                                  py_+math.sin(ag_)*9)
                    _NS_zephyr._aaline(surface, p["magic_mid"],
                                       (px_, py_), (tx__, ty__), 2)
                    _NS_zephyr._aaline(surface, p["magic_bright"],
                                       (px_, py_), (tx__, ty__), 1)

    # ---------------------------------------------------------------
    # Projectile management
    # ---------------------------------------------------------------
    def _manage_projectiles(boss, surface, phase):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        for proj in boss._zp_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._zp_projectiles = [p_ for p_ in boss._zp_projectiles
                                 if p_.alive or p_.dead_frames < 8]

    def _spawn_magic_bolt(boss, x, y):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        tx_, ty_ = _NS_zephyr._target_position(boss, x, y)
        facing_ = getattr(boss, "direction", 1)
        sx_, sy_ = _NS_zephyr._staff_orb_position(
            x, y, facing_,
            float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
        tgt = getattr(boss, "target", None)
        proj = _NS_zephyr.MagicBoltProjectile(
            sx_, sy_, tx_, ty_, speed=7.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._zp_projectiles.append(proj)

    def _spawn_casket(boss, x, y):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        tx_, ty_ = _NS_zephyr._target_position(boss, x, y)
        facing_ = getattr(boss, "direction", 1)
        sx_, sy_ = _NS_zephyr._staff_orb_position(
            x, y, facing_,
            float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
        tgt = getattr(boss, "target", None)
        proj = _NS_zephyr.CasketProjectile(
            sx_, sy_, tx_, ty_, speed=5.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._zp_projectiles.append(proj)

    # ---------------------------------------------------------------
    # SKILL FX  —  world-space, 3 phases per skill
    # ---------------------------------------------------------------

    # ── Q — BRAMBLE MAZE ─────────────────────────────────────────────
    def _draw_bramble_ground(surface, boss, x, y, timer, phase):
        """Q ground telegraph: converging rings + thorn burst."""
        p = _NS_zephyr.PALETTE
        fs = _NS_zephyr._fx_scale(boss)
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["q"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        tx_, ty_ = _NS_zephyr._target_position(boss, x, y)
        rng = _NS_zephyr._ring_r(boss, 60, surface)

        # ACTIVATION burst (first ~15 % of duration)
        if progress < .15:
            t = progress / .15
            burst_r = int(rng * t)
            al = int(255 * (1-t) * 1.3)
            _NS_zephyr._spark_star(surface, tx_, ty_,
                                   int(28*(1-t*0.5)),
                                   p["thorn_light"], min(255, al),
                                   spikes=8, rot=phase,
                                   core=p["magic_white"])
            _NS_zephyr._aacircle(surface, (*p["magic_mid"], al),
                                 (tx_, ty_), burst_r, 4)

        # STEADY: dashed ring at trap + converging ring
        outer_al = int(180 + math.sin(phase * 2.2) * 40)
        _NS_zephyr._dashed_ring(surface, tx_, ty_+16, rng,
                                p["thorn_mid"], outer_al, phase,
                                segments=6, thick=3)
        conv_r = int(rng * (1.0 - (progress % .25) * 4))
        _NS_zephyr._aacircle(surface, (*p["magic_dark"], 90),
                             (tx_, ty_+16), max(2, conv_r), 2)
        _NS_zephyr._ellipse(surface, (*p["thorn_dark"], 100),
                            (tx_-rng, ty_+16-rng//4, rng*2, rng//2))
        _NS_zephyr._ellipse(surface, (*p["thorn_mid"], 160),
                            (tx_-rng, ty_+16-rng//4, rng*2, rng//2), 3)

        # Chevron row toward trap
        dist_ = math.hypot(tx_-x, ty_-y)
        ang_  = math.atan2(ty_-y, tx_-x)
        for ci in range(3):
            frac = (ci+1) / 4.0
            cx__, cy__ = (int(x + math.cos(ang_)*dist_*frac),
                          int(y + math.sin(ang_)*dist_*frac))
            pal = int(140 + math.sin(phase*2 + ci) * 40)
            _NS_zephyr._chevron(surface, cx__, cy__, ang_,
                                int(12*fs), p["thorn_light"], pal, 2)

    def _draw_bramble_maze(surface, boss, x, y, timer, phase):
        """Q foreground: thorn ring spines + thorn motes rising."""
        p = _NS_zephyr.PALETTE
        fs = _NS_zephyr._fx_scale(boss)
        tx_, ty_ = _NS_zephyr._target_position(boss, x, y)
        rng = _NS_zephyr._ring_r(boss, 60, surface)

        # 12 thorn spines around ring
        for i in range(6):
            ang_ = phase * .6 + i * math.tau / 12
            rx_, ry_ = (int(tx_ + math.cos(ang_)*rng),
                        int(ty_ + 16 + math.sin(ang_)*rng*.34))
            tlen = int((8 + _NS_zephyr._hash01(i*7)*6) * fs)
            a_out = ang_ + math.pi * .5
            ex_, ey_ = (int(rx_ + math.cos(a_out)*tlen),
                        int(ry_ + math.sin(a_out)*tlen))
            al = int(200 + math.sin(phase*2+i)*40)
            _NS_zephyr._aaline(surface, (*p["thorn_mid"], al),
                               (rx_, ry_), (ex_, ey_), 2)
            _NS_zephyr._aacircle(surface, p["thorn_light"],
                                 (ex_, ey_), 1)

        # Rising thorn motes
        for i in range(4):
            t = (phase * .30 + i / 8.0) % 1.0
            mr = rng * (.5 + _NS_zephyr._hash01(i*13) * .5)
            ang_ = _NS_zephyr._hash01(i*17) * math.tau
            mx_ = int(tx_ + math.cos(ang_) * mr)
            my_ = int(ty_ + 16 + math.sin(ang_) * mr * .34 - t*28*fs)
            al = max(0, int(200 * (1-t)))
            _NS_zephyr._aacircle(surface, (*p["thorn_light"], al),
                                 (mx_, my_), max(1, int(2*fs)))

        # Inner glow rune ring (slow rotation)
        _NS_zephyr._dashed_ring(surface, tx_, ty_+16, int(rng*.62),
                                p["rune_mid"], 160, -phase*0.4,
                                segments=8, thick=2)

    # ── W — SHADOW REALM ─────────────────────────────────────────────
    def _draw_shadow_realm_ground(surface, boss, x, y, timer, phase):
        """W ground: expanding ground ring."""
        p = _NS_zephyr.PALETTE
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        rng = _NS_zephyr._ring_r(boss, 100, surface)
        radius = int(34 + min(1.0, progress*5) * rng*.5)

        _NS_zephyr._ellipse(surface, (*p["magic_darkest"], 155),
                            (x-radius, y+31-radius//3,
                             radius*2, max(5, radius*2//3)))
        _NS_zephyr._ellipse(surface, (*p["magic_dark"], 215),
                            (x-radius, y+31-radius//3,
                             radius*2, max(5, radius*2//3)), 3)

        # Rune ring rotating
        _NS_zephyr._dashed_ring(surface, x, y+31, radius,
                                p["rune_mid"], 180, phase*.7,
                                segments=4, thick=2)
        for i in range(6):
            a_ = phase*.7 + i*math.tau/6
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                 (int(x + math.cos(a_)*(radius-5)),
                                  int(y+31 + math.sin(a_)*radius*.30)), 1)

    def _draw_shadow_realm(surface, boss, x, y, timer, phase):
        """W foreground: glass dome + rune ring ganda (tanpa pilar)."""
        p = _NS_zephyr.PALETTE
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        envelope = min(1.0, progress*5.0, (1.0-progress)*5.0)
        rng = _NS_zephyr._ring_r(boss, 100, surface)

        # ACTIVATION: bintang saja — pilar cahaya DIBUANG.
        # Kolom 3-lapis setinggi 120 px di (x, y) menutupi badan Zephyr
        # selama W di-cast.
        if progress < .20:
            t = progress / .20
            _NS_zephyr._spark_star(surface, x, y, int(26*t),
                                   p["magic_bright"], int(240*t),
                                   spikes=8, rot=phase, core=p["magic_white"])

        radius = max(3, int(rng * envelope * .47))
        if radius <= 3:
            return
        cx_, cy_ = x, y - 14
        pulse_ = .78 + math.sin(phase*2.6) * .16

        # Glass dome crescent
        _NS_zephyr._aacircle(surface, (*p["magic_dark"], int(44*pulse_)),
                             (cx_, cy_), radius)
        for off_, al_, wd_ in ((0, 180, 2), (4, 120, 2), (9, 75, 1)):
            _NS_zephyr._draw_fey_arc(surface, cx_, cy_,
                                     radius-off_, radius-off_,
                                     .18, math.pi-.18,
                                     (*p["magic_bright"], int(al_*pulse_)),
                                     wd_, 22)
        _NS_zephyr._draw_fey_arc(surface, cx_, cy_,
                                 radius-3, radius-3,
                                 math.pi+.20, math.tau-.20,
                                 (*p["wing_mid"], int(145*pulse_)), 1, 20)

        # Dual rune rings (opposite rotation) — STEADY signature
        _NS_zephyr._dashed_ring(surface, cx_, cy_, radius-2,
                                p["rune_mid"], int(180*pulse_), phase*1.1,
                                segments=10, thick=2)
        _NS_zephyr._dashed_ring(surface, cx_, cy_, radius-8,
                                p["magic_mid"], int(140*pulse_), -phase*0.8,
                                segments=8, thick=2)

        # Glass highlight + petal reflections
        _NS_zephyr._aacircle(surface, p["magic_hot"],
                             (cx_-radius//2, cy_-radius//2), 3)
        for i in range(4):
            a_ = phase*2.0 + i*math.tau/8
            r_ = radius*(.52 + (i%2)*.16)
            _NS_zephyr._aacircle(surface, (*p["wing_shine"], 170),
                                 (int(cx_+math.cos(a_)*r_),
                                  int(cy_+math.sin(a_)*r_)), 1 if i%2 else 2)

        # Ground ring arc
        _NS_zephyr._draw_fey_arc(surface, cx_, cy_+30, radius,
                                 radius*.22, phase, phase+math.pi,
                                 (*p["rune_light"], 190), 1)

    # ── E — CASKET CURSE ─────────────────────────────────────────────
    def _draw_casket_indicator(surface, boss, x, y, timer, phase):
        """E: thorn tether to target + reticle + activation burst."""
        p = _NS_zephyr.PALETTE
        fs = _NS_zephyr._fx_scale(boss)
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["e"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        tx_, ty_ = _NS_zephyr._target_position(boss, x, y)
        sx_, sy_ = _NS_zephyr._staff_orb_position(
            x, y, getattr(boss, "direction", 1),
            phase, "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))

        # ACTIVATION burst
        if progress < .12:
            t = progress / .12
            _NS_zephyr._spark_star(surface, tx_, ty_,
                                   int(22*(1-t*.5)),
                                   p["jewel_light"], int(240*(1-t)),
                                   spikes=6, rot=phase*2.0,
                                   core=p["magic_white"])

        # Thorn tether (segmented wobble)
        dx_, dy_ = tx_-sx_, ty_-sy_
        dist_ = max(1.0, math.hypot(dx_, dy_))
        nx_, ny_ = -dy_/dist_, dx_/dist_
        for i in range(5):
            t1 = i / 10.0
            t2 = min(1.0, (i+.55)/10.0)
            w1 = math.sin(phase*3 + i)*3.5
            w2 = math.sin(phase*3 + i + .6)*3.5
            a_ = (int(sx_ + dx_*t1 + nx_*w1),
                  int(sy_ + dy_*t1 + ny_*w1))
            b_ = (int(sx_ + dx_*t2 + nx_*w2),
                  int(sy_ + dy_*t2 + ny_*w2))
            al = int(190 + math.sin(phase*2 + i)*40)
            _NS_zephyr._aaline(surface, (*p["thorn_dark"], al+20),
                               a_, b_, 3)
            _NS_zephyr._aaline(surface, (*p["magic_bright"], al),
                               a_, b_, 1)

        # Reticle at target (two rings + cross)
        targ_r = int(12*fs)
        _NS_zephyr._aacircle(surface, (*p["jewel_mid"], 200),
                             (tx_, ty_), targ_r, 2)
        _NS_zephyr._aacircle(surface, (*p["jewel_light"], 160),
                             (tx_, ty_), max(1, targ_r-4), 2)
        for ang_ in (0, math.pi/2):
            ca_, sa_ = math.cos(ang_), math.sin(ang_)
            _NS_zephyr._aaline(surface, (*p["jewel_light"], 200),
                               (int(tx_-ca_*targ_r), int(ty_-sa_*targ_r)),
                               (int(tx_+ca_*targ_r), int(ty_+sa_*targ_r)), 1)
        # Glint orbiting reticle
        for i in range(4):
            a_ = phase*3.5 + i*math.pi/2
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                 (int(tx_+math.cos(a_)*(targ_r+3)),
                                  int(ty_+math.sin(a_)*(targ_r+3))), 1)

    def _handle_casket_skill(surface, boss, x, y, timer, phase):
        if not getattr(boss, "_zp_casket_spawned", False):
            _NS_zephyr._spawn_casket(boss, x, y)
            boss._zp_casket_spawned = True
        if timer < 5:
            boss._zp_casket_spawned = False

    # ── R — BEDLAM ───────────────────────────────────────────────────
    def _draw_bedlam_ground(surface, boss, x, y, timer, phase):
        """R ground: expanding rings + ground cracks + radial chevrons."""
        p = _NS_zephyr.PALETTE
        fs = _NS_zephyr._fx_scale(boss)
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        rng = _NS_zephyr._ring_r(boss, 80, surface)
        radius = int(45 + min(1.0, progress*4)*rng*.5)

        # Ground ellipse rings
        _NS_zephyr._ellipse(surface, (*p["magic_darkest"], 170),
                            (x-radius, y+31-radius//3,
                             radius*2, max(6, radius*2//3)))
        _NS_zephyr._ellipse(surface, (*p["magic_dark"], 220),
                            (x-radius, y+31-radius//3,
                             radius*2, max(6, radius*2//3)), 3)
        for i in range(3):
            rr_ = radius - i*11
            _NS_zephyr._draw_fey_arc(surface, x, y+31, rr_, rr_*.29,
                                     phase*(1.0+i*.25)+i,
                                     phase*(1.0+i*.25)+i+math.tau,
                                     (*p["magic_mid"], 190-i*38),
                                     2 if i==0 else 1)

        # ACTIVATION: bintang saja — pilar cahaya DIBUANG.
        # Kolom 4-lapis setinggi 100 px di (x, y) menutupi badan Zephyr
        # selama Bedlam di-cast.
        if progress < .12:
            t = progress / .12
            _NS_zephyr._spark_star(surface, x, y, int(34*t),
                                   p["magic_bright"], int(255*t),
                                   spikes=8, rot=phase, core=p["magic_white"])

        # 5 radial ground cracks (jagged, deterministik)
        for ci in range(5):
            ang_ = ci * math.tau/5 + phase*.12
            _NS_zephyr._jagged_crack(surface, x, y+16, ang_,
                                     int(radius*.7),
                                     (p["magic_dark"], p["magic_mid"]),
                                     int(160 + math.sin(phase*2+ci)*40),
                                     ci*19+7, 2)

        # Converging ring (reads "incoming")
        conv_r = int(rng * (1.0 - (progress % .20)*5))
        if conv_r > 2:
            _NS_zephyr._aacircle(surface, (*p["magic_light"], 110),
                                 (x, y+16), conv_r, 2)

        # Radial chevrons at ground level
        for i in range(4):
            a_ = phase*.5 + i*math.tau/8
            cx__ = int(x + math.cos(a_)*radius*.72)
            cy__ = int(y+31 + math.sin(a_)*radius*.22)
            _NS_zephyr._chevron(surface, cx__, cy__,
                                a_ + math.pi, int(9*fs),
                                p["rune_light"],
                                int(140 + math.sin(phase*2+i)*40), 2)

        # Rune dots orbiting
        for i in range(5):
            a_ = phase*.95 + i*math.tau/10
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                 (int(x + math.cos(a_)*(radius-5)),
                                  int(y+31 + math.sin(a_)*radius*.28)), 2)

    def _draw_bedlam(surface, boss, x, y, timer, phase):
        """R foreground: 6 fairy orbit + dual spell ribbons + pilar."""
        p = _NS_zephyr.PALETTE
        fs = _NS_zephyr._fx_scale(boss)
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        envelope = min(1.0, progress*5.0, (1.0-progress)*5.0)
        rng = _NS_zephyr._ring_r(boss, 80, surface)

        # 6 fairy orbit with trail
        for i in range(6):
            angle_ = phase*2.35 + i*math.tau/6.0
            orbit_r = int((46 + math.sin(phase*1.7+i)*7) * fs)
            dx_ = int(x + math.cos(angle_)*orbit_r)
            dy_ = int(y - 12 + math.sin(angle_)*orbit_r*.42)
            al_ = max(50, min(235,
                     int((174 + math.sin(phase*2+i)*48)
                         * max(.28, envelope))))
            _NS_zephyr._draw_mini_fairy(surface, dx_, dy_,
                                       phase + i*.33, al_,
                                       facing=1 if math.cos(angle_)>=0 else -1)
            # Glitter trail
            for tail in range(4):
                ta_ = angle_ - .20*(tail+1)
                _NS_zephyr._aacircle(surface,
                    (*p["magic_bright"], max(20, al_-tail*50)),
                    (int(x + math.cos(ta_)*orbit_r),
                     int(y - 12 + math.sin(ta_)*orbit_r*.42)),
                    max(1, 3-tail))

        # Spell ribbons (3, discontinuous)
        for i in range(3):
            _NS_zephyr._draw_fey_arc(surface, x, y-10,
                                     int((46-i*5)*fs),
                                     int((18-i*2)*fs*.56),
                                     phase*1.9 + i*2.1,
                                     phase*1.9 + i*2.1 + 1.52,
                                     (*p["magic_hot"], 190-i*38), 1, 14)

        # Outer orbit glints (24 pts)
        for i in range(12):
            a_ = phase*1.4 + i*math.tau/24
            r_ = int((52 + math.sin(phase*2+i)*6)*fs)
            _NS_zephyr._aacircle(surface, p["magic_white"],
                                 (int(x + math.cos(a_)*r_),
                                  int(y-8 + math.sin(a_)*r_*.44)), 1)

        # STEADY: dual rune rings counter-rotating
        _NS_zephyr._dashed_ring(surface, x, y-8,
                                int(rng*.88), p["rune_mid"],
                                int(160*envelope), phase*0.9,
                                segments=12, thick=2)
        _NS_zephyr._dashed_ring(surface, x, y-8,
                                int(rng*.68), p["magic_mid"],
                                int(130*envelope), -phase*0.7,
                                segments=9, thick=2)

        # Pilar cahaya (ACTIVE phase) DIBUANG — kolom 4-lapis setinggi
        # 90 px di (x, y) menutupi badan Zephyr selama Shadow Realm
        # aktif. Inti denyut di kaki tetap hidup.
        if envelope > .05:
            # Pulsing core
            _NS_zephyr._aacircle(surface,
                                 (*p["magic_white"], int(200*envelope)),
                                 (x, y), int(5*envelope*fs))

    # ── Mini fairy (orbit) ─────────────────────────────────────────
    def _draw_mini_fairy(surface, cx_, cy_, phase, alpha, facing=1):
        """Compact masterwork silhouette used by Bedlam orbit."""
        p = _NS_zephyr.PALETTE
        f_ = 1 if facing >= 0 else -1
        flap = int(math.sin(phase*3)*2)
        for side in (-1, 1):
            _NS_zephyr._poly(surface, (*p["wing_dark"], alpha//2), [
                (cx_+f_*2, cy_-7),
                (cx_+f_*side*13, cy_-18+flap),
                (cx_+f_*side*16, cy_-9),
                (cx_+f_*side*7, cy_-2)])
            _NS_zephyr._aaline(surface, (*p["wing_shine"], alpha//2),
                               (cx_+f_*2, cy_-7),
                               (cx_+f_*side*11, cy_-16+flap), 1)
        _NS_zephyr._poly(surface, (*p["dress_dark"], alpha), [
            (cx_-6, cy_-2), (cx_+6, cy_-2), (cx_+8, cy_+11),
            (cx_, cy_+15), (cx_-7, cy_+10)])
        _NS_zephyr._poly(surface, (*p["corset_mid"], alpha), [
            (cx_-3, cy_-3), (cx_+3, cy_-3),
            (cx_+3, cy_+3), (cx_-3, cy_+3)])
        _NS_zephyr._aacircle(surface, (*p["skin_mid"], alpha),
                             (cx_+f_, cy_-10), 5)
        for i in range(3):
            _NS_zephyr._aaline(surface, (*p["hair_mid"], alpha),
                               (cx_+f_*(i-1), cy_-13),
                               (cx_+f_*(i-2), cy_-21-(i%2)*2), 2)
        _NS_zephyr._aacircle(surface, (*p["eye_iris_light"], alpha),
                             (cx_+f_*2, cy_-10), 1)
        _NS_zephyr._aaline(surface, (*p["staff_light"], alpha),
                           (cx_+f_*5, cy_+8), (cx_+f_*11, cy_-17), 2)
        _NS_zephyr._aacircle(surface, (*p["jewel_light"], alpha),
                             (cx_+f_*11, cy_-18), 2)

    # ---------------------------------------------------------------
    # POSE ENTRY POINTS
    # ---------------------------------------------------------------
    def _draw_zephyr_idle(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(phase*.78)*2.5)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x, y+50)
            _NS_zephyr._draw_floating_sparkles(surface, x, y+36, phase)
        _NS_zephyr._draw_zephyr_body(
            surface, x, y+bob, getattr(boss, "direction", 1),
            phase, "idle", detail=portrait_hd)

    def _draw_zephyr_walk(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0)) * 2.0
        stride = math.sin(phase*1.72)
        bob = int(abs(stride)*3.5)
        sway = int(stride*2.5)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x+sway, y+50)
            _NS_zephyr._draw_floating_sparkles(
                surface, x+sway, y+37, phase, trail=True,
                facing=getattr(boss, "direction", 1))
        _NS_zephyr._draw_zephyr_body(
            surface, x+sway, y-bob, getattr(boss, "direction", 1),
            phase, "walk", detail=portrait_hd)

    def _draw_zephyr_attack(surface, boss, x, y):
        """Pose serangan: ayunan tongkat berbasis busur + FX benturan."""
        Z = _NS_zephyr
        progress = max(0.0, min(1.0,
            float(getattr(boss, "_zp_attack_progress", 0.0))))
        phase = float(getattr(boss, "pulse", 0.0))
        facing = getattr(boss, "direction", 1)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        atk_phase = getattr(boss, "_zp_attack_phase", "NONE")

        # Bolt dilepas tepat pada frame IMPACT (bukan di tengah-tengah
        # gerakan) supaya lesatannya sinkron dengan puncak ayunan.
        if (getattr(boss, "active_skill", None) is not None
                and atk_phase == "IMPACT"
                and not getattr(boss, "_zp_proj_spawned", False)
                and not portrait_hd):
            Z._spawn_magic_bolt(boss, x, y)
            boss._zp_proj_spawned = True
        if progress < .15 or progress > .9:
            boss._zp_proj_spawned = False

        # Lunge mengikuti kurva ayunan: dorongan maju saat SWING,
        # tahan di IMPACT, mundur pelan saat RECOVERY.
        if progress < Z.ATTACK_WINDUP_END:
            lunge = -int(3 * Z._ease_in_out(
                progress / max(1e-4, Z.ATTACK_WINDUP_END)))
        elif progress < Z.ATTACK_IMPACT_END:
            t = (progress - Z.ATTACK_WINDUP_END) / \
                max(1e-4, Z.ATTACK_IMPACT_END - Z.ATTACK_WINDUP_END)
            lunge = int(7 * Z._ease_out(t))
        else:
            t = (progress - Z.ATTACK_IMPACT_END) / \
                max(1e-4, 1.0 - Z.ATTACK_IMPACT_END)
            lunge = int(7 * (1.0 - Z._ease_in_out(t)))
        recoil = lunge * (1 if facing >= 0 else -1)

        if not portrait_hd:
            Z._draw_shadow(surface, x + recoil, y + 50)
            Z._draw_floating_sparkles(
                surface, x + recoil, y + 36, phase, intense=True,
                facing=facing)
        Z._draw_zephyr_body(
            surface, x + recoil, y, facing, phase, "attack", progress,
            detail=portrait_hd)
        if not portrait_hd:
            Z._draw_cast_flash(surface, x + recoil, y, facing,
                               progress, phase)

    # ---------------------------------------------------------------
    # BODY DISPATCH
    # ---------------------------------------------------------------
    def _draw_zephyr_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0.0, detail=False,
                          bedlam=False):
        _NS_zephyr._draw_zephyr_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, detail, bedlam)

    def _draw_zephyr_rig(surface, cx, cy, facing, phase, action,
                         attack_progress=0.0, detail=False):
        """Explicit rig alias used by visual tooling and future cosmetics."""
        _NS_zephyr._draw_zephyr_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, detail)

    # ---------------------------------------------------------------
    # MAIN DRAW ENTRY POINT
    # ---------------------------------------------------------------
    def draw_zephyr(surface, boss, x, y):
        """Render Zephyr — rig prosedural v3 (render + animation + FX).

        Urutan lapisan mengikuti kontrak render order proyek:

            GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD ->
            WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
            SKILL FX -> IMPACT FX

        Trail 60 fps, partikel, projectile gameplay, impact, screen
        shake, dan hit-stop hidup di ``heroes/zephyr_fx.py`` (lapisan
        layar, di luar sprite cache).  Semua nama publik lama tetap.
        """
        Z = _NS_zephyr
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer  = int(getattr(boss, "active_skill_timer", 0))
        moving       = Z._detect_moving(boss)
        Z._update_attack_anim(boss)
        portrait_hd  = bool(getattr(boss, "_portrait_hd", False))
        state        = getattr(boss, "_zp_state", "IDLE")

        attacking = (
            getattr(boss, "_zp_attack_active", False)
            or getattr(boss, "timer", 0) >
            getattr(boss, "attack_cooldown", 42) - 15
        )

        if not portrait_hd:
            Z._draw_fey_rim_light(surface, x, y - 14, pulse)
            Z._draw_fey_aura(surface, x, y, pulse)
            Z._draw_fey_platform(surface, x, y + 46, pulse, active_skill)

            if active_skill == "q":
                Z._draw_bramble_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                Z._draw_shadow_realm_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                Z._draw_bedlam_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                Z._draw_casket_indicator(
                    surface, boss, x, y, skill_timer, pulse)

        if attacking:
            Z._draw_zephyr_attack(surface, boss, x, y)
        elif moving:
            Z._draw_zephyr_walk(surface, boss, x, y)
        else:
            Z._draw_zephyr_idle(surface, boss, x, y)

        if not portrait_hd:
            Z._manage_projectiles(boss, surface, pulse)

            if active_skill == "q":
                Z._draw_bramble_maze(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                Z._draw_shadow_realm(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                Z._handle_casket_skill(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                Z._draw_bedlam(
                    surface, boss, x, y, skill_timer, pulse)

            if Z.DEBUG_CHARACTER:
                Z._draw_debug(surface, boss, x, y, state)

    # ---------------------------------------------------------------
    # DEBUG MODE (canvas-space)
    # ---------------------------------------------------------------
    #: Aktifkan untuk melihat hitbox / hurtbox / state / timer.
    DEBUG_CHARACTER = False

    def _draw_debug(surface, boss, x, y, state):
        """Overlay debug rig: hurtbox, hitbox ayunan, jangkauan, state."""
        Z = _NS_zephyr
        # hurtbox badan (kotak siluet rig)
        pygame.draw.rect(surface, (90, 220, 255),
                         pygame.Rect(int(x - 34), int(y - 104), 70, 156), 1)
        # jangkauan serangan (dalam ruang canvas)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        reach = int(float(getattr(boss, "range", 130)) / max(0.05, scale))
        pygame.draw.circle(surface, (255, 90, 190), (int(x), int(y)),
                           min(reach, 900), 1)
        # hitbox jendela aktif
        box = Z._swing_hitbox(boss, x, y)
        if box is not None:
            pygame.draw.rect(surface, (255, 230, 90), box, 2)
        # penanda ujung tongkat
        tip = Z._staff_orb_position(
            x, y, getattr(boss, "direction", 1),
            float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
        pygame.draw.circle(surface, (120, 255, 150), tip, 4, 1)
        # teks state (tanpa font: bar indikator progress)
        prog = float(getattr(boss, "_zp_attack_progress", 0.0))
        bar = pygame.Rect(int(x - 40), int(y - 118), 80, 5)
        pygame.draw.rect(surface, (30, 10, 40), bar)
        pygame.draw.rect(surface, (255, 140, 220),
                         (bar.x, bar.y, int(80 * prog), 5))
        idx = list(Z.ANIM_STATES).index(state) \
            if state in Z.ANIM_STATES else 0
        pygame.draw.rect(surface, (140, 255, 200),
                         (bar.x, bar.y - 6, 4 + idx * 5, 4))

    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_zephyr.draw_zephyr(surface, boss, x, y)

# ============================================================================
# KAIZEN V1 PIXEL-ART OVERRIDE
# ============================================================================
# The original bundled namespace remains as a compatibility base.  The
# supplied Godot renderer is adapted to pygame in a small subclass so all
# historical imports (`heroes.kaizen`, live FX and portrait tools) continue
# to resolve the same public namespace.
from heroes.kaizen_v1 import install as _install_kaizen_v1
_NS_kaizen = _install_kaizen_v1(_NS_kaizen)
del _install_kaizen_v1

# ============================================================================
# VEX V1 PIXEL-ART OVERRIDE
# ============================================================================
# Same layering as the Kaizen V1 override above: the bundled masterwork
# namespace stays as a compatibility base while Vex's actual render path is
# replaced by the pixel-art V1 renderer (Kaizen-style chibi, void-mage
# identity preserved).
from heroes.vex_v1 import install as _install_vex_v1
_NS_vex = _install_vex_v1(_NS_vex)
del _install_vex_v1
