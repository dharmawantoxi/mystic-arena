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
    """Namespace grimjaw - PIXEL MASTERWORK v2 (rewrite penuh renderer).

    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.

    Apa yang naik dibanding versi lama
    ----------------------------------
    1. RIG ~1.5x LEBIH BESAR di resolusi native (telapak di y=+70, puncak
       mane api y=-92). Pipeline hero (heroes/__init__.py) mengukur badan
       lalu men-scale agar tinggi di layar tetap ~70 px, jadi memperbesar
       rig TIDAK memperbesar hero di arena - melainkan memberi ~2.1 px
       native per px layar: cluster, ramp, dan muka tetap tajam setelah
       smoothscale + lighting + outline pass.
    2. DISIPLIN PIXEL-ART: tiap material maksimal 4-5 nilai ramp dengan
       hue-shift (bayangan kulit didorong dingin, highlight hangat; bayangan
       api didorong merah-ungu), selout (outline gelap hanya di sisi
       bayangan kanan-bawah), siluet mane bergerigi via _tuft_points
       (hash deterministik, aman untuk cache), specular sebagai cluster
       1-2 px yang disengaja, dither band di perut. Key light kiri-atas,
       konsisten dengan lighting.py (LIGHT_DIR = (-1, -1)).
    3. ANATOMI: mane api 3 lapis volume + 9 lick ber-pita, mask putih
       juggernaut 5 band ber-strip darah + grille + taring, dada V-taper
       dengan sash merah + harness X kulit, sabuk + gesper emas + tasset
       3 pelat, kaki bertulang dengan shin guard baja ber-rivet + boot
       3 band, pauldron baja berlapis ber-duri, dan flame scimitar
       melengkung pose-driven dengan pommel emas + quillon + ember.
    4. ANIMASI: foot-solver jalan (telapak menapak/terangkat, lutut ikut
       naik, bayangan kontak per telapak, debu saat menapak), inersia
       mane (crest tertinggal dari akselerasi + flare saat serang),
       idle hidup (napas, blink, flicker api, ember naik, snarl),
       timeline serang 7 keyframe dengan frame IMPACT tersendiri
       (squash, bintang 6-8 spike, shockwave, 5 serpihan) + smear sabit
       3-band yang menempel di jalur pedang.
    5. SKILL FX v2 (world-space, setingkat Thorne v2.1): semua efek
       dikompensasi _render_scale via _fx_scale (cap 2.6) sehingga
       cincin/telegraph tidak ikut mengecil bersama sprite cache. Tiap
       skill 3 fase: AKTIVASI (shockwave/pilar cahaya + bintang), STEADY
       (aura berlapis + partikel + ring berputar), TELEGRAPH yang mudah
       dibaca (ring konvergen, chevron berbaris, retakan tanah). Badan
       ikut bereaksi: blade menyala incandescent saat crit/omnislash,
       mata mask berubah hijau saat healing ward. Surface statis
       (aura/mist/ground glow) dibangun sekali lalu di-cache; semua
       radius di-clamp ke dalam canvas.
    """

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _SCRATCH_POOL = {}
    _OMNI_BUF = {}

    # Durasi visual skill (frame @60fps) — renderer memakai ini untuk
    # progress FX, BUKAN timer gameplay (lihat hero_skills GrimjawSkills).
    SKILL_VISUAL_DURATION = {"q": 180, "w": 90, "e": 60, "r": 90}

    # ---------------------------------------------------------------------------
    # HD Color Palette - "Masterwork v2"
    # Semua kunci lama dipertahankan (renderer/test lain memakai), nilai
    # dituning ke ramp pixel-art 4-5 band dengan hue-shift; beberapa
    # kunci baru untuk material baru.
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - tanned; bayangan dingin (cokelat-ungu), highlight hangat
        "skin_darkest":   ( 92,  56,  48),
        "skin_dark":      (142,  88,  62),
        "skin_mid":       (196, 138,  96),
        "skin_light":     (228, 178, 128),
        "skin_high":      (252, 216, 172),

        # Hair / mane - flame mane; bayangan merah-ungu dingin
        "hair_darkest":   ( 76,  26,  24),
        "hair_dark":      (140,  52,  24),
        "hair_mid":       (200,  96,  34),
        "hair_light":     (238, 152,  58),
        "hair_high":      (255, 198,  96),
        "hair_shine":     (255, 226, 140),

        # MASK - white juggernaut, 5 band
        "mask_shadow":    (128, 122, 116),
        "mask_dark":      (182, 176, 168),
        "mask_mid":       (222, 218, 206),
        "mask_light":     (244, 242, 232),
        "mask_shine":     (255, 255, 250),
        "mask_line":      ( 96,  90,  82),

        # BLOOD STRIPES
        "blood_darkest":  ( 92,  12,  14),
        "blood_dark":     (148,  22,  26),
        "blood_mid":      (204,  40,  44),
        "blood_light":    (242,  74,  76),
        "blood_bright":   (255, 118, 118),

        # Armor leather
        "armor_darkest":  ( 34,  20,  13),
        "armor_dark":     ( 68,  40,  23),
        "armor_mid":      (112,  66,  37),
        "armor_light":    (160, 102,  58),
        "armor_high":     (206, 148,  88),

        # Red cloth (sash / loincloth / skirt)
        "red_darkest":    ( 64,  14,  18),
        "red_dark":       (108,  22,  28),
        "red_mid":        (164,  38,  42),
        "red_light":      (208,  62,  66),
        "red_bright":     (244, 102, 104),

        # Gold
        "gold_darkest":   ( 74,  44,  12),
        "gold_dark":      (134,  88,  22),
        "gold_mid":       (198, 148,  44),
        "gold_light":     (238, 198,  88),
        "gold_shine":     (255, 234, 150),
        "gold_engrave":   (255, 212, 124),

        # Metal - cool steel (kontras dingin vs api hangat)
        "metal_darkest":  ( 24,  20,  26),
        "metal_dark":     ( 54,  50,  58),
        "metal_mid":      (104,  96, 104),
        "metal_light":    (164, 156, 164),
        "metal_shine":    (222, 218, 224),

        # FIRE BLADE - ramp api 5 band + core
        "fire_darkest":   ( 84,  18,   6),
        "fire_dark":      (162,  42,  12),
        "fire_mid":       (232, 104,  22),
        "fire_light":     (248, 172,  54),
        "fire_hot":       (255, 228, 122),
        "fire_core":      (255, 250, 235),
        "ember":          (255, 188,  92),

        # Healing (green - Healing Ward)
        "heal_darkest":   ( 20,  58,  26),
        "heal_dark":      ( 50, 132,  60),
        "heal_mid":       (104, 212, 114),
        "heal_light":     (164, 248, 174),
        "heal_core":      (234, 255, 234),

        # Rage / omnislash (red-hot)
        "rage_dark":      ( 96,  20,  16),
        "rage_mid":       (180,  44,  28),
        "rage_light":     (240,  96,  52),
        "rage_bright":    (255, 150,  96),

        # Misc
        "shadow":         (  0,   0,   0),
        "shadow_deep":    (  5,   3,   8),
        "white":          (255, 255, 255),
        "eye_glow":       (255,  46,  46),
        "dark_eye":       ( 24,   5,  10),
        # boot swatches (retained)
        "boot_darkest":   ( 18,  14,  16),
        "boot_dark":      ( 42,  30,  28),
        "boot_mid":       ( 78,  52,  42),
        "boot_light":     (120,  82,  60),
        "cloth_stitch":   ( 72,  22,  26),
    }

    # ------------------------------------------------------------------
    # Surface statis (bayangan / mist / aura / ground glow) dibangun
    # SEKALI lalu dipakai ulang - tidak ada alokasi surface per frame.
    # ------------------------------------------------------------------
    _STATIC_SURFACES = {}

    def _static(key, builder):
        surf = _NS_grimjaw._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_grimjaw._STATIC_SURFACES[key] = surf
        return surf

    def _scratch(w, h):
        """Surface sementara POOL (fill 0 lalu pakai) - menggantikan
        alokasi Surface per-primitif di jalur alpha. Ribuan alokasi per
        frame dulunya menambah ~0.3-0.5 ms; pool dikosongkan bila > 24
        ukuran (tidak pernah membengkak di cache)."""
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
        # - tanpa genexpr/max/min yang dulu menghabiskan ~10% frame rig.
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
        return tuple(max(0, min(255, int(c))) for c in color)
    def _mix(a, b, t):
        """Blend linear dua warna (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_grimjaw._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grimjaw._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = _NS_grimjaw._scratch(radius * 2 + 4, radius * 2 + 4)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
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
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = _NS_grimjaw._scratch(w, h)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_grimjaw._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = _NS_grimjaw._scratch(w, h)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_grimjaw._clamp(color)
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
        color = _NS_grimjaw._clamp(color)
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

    def _target_position(hero, x, y):
        target = getattr(hero, "target", None)
        if target is not None and getattr(target, "alive", True):
            return _NS_grimjaw._world_to_local(hero, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(hero, "_render_scale", None)
        dist = 60 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(hero, "direction", 1)), int(y)

    # ------------------------------------------------------------------
    # SKILL FX PRIMITIVES (pass mewah v2 - world-space)
    # ------------------------------------------------------------------
    def _fx_scale(hero):
        """Faktor skala efek skill.

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek (cincin, retakan, partikel) ikut menyusut sampai
        ~45%. Dengan faktor ini efek digambar lebih besar di canvas
        sehingga ukurannya DI LAYAR setara boss asli (world-space).
        Boss asli (tanpa _render_scale) = 1.0. Cap 2.6 menjaga efek
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

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_grimjaw._aaline(surface, (*color, alpha),
                                (int(cx), int(cy)),
                                (int(cx + math.cos(ang) * ln),
                                 int(cy + math.sin(ang) * ln * .8)),
                                2 if k % 2 == 0 else 1)
        if core:
            _NS_grimjaw._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_grimjaw._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_grimjaw._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_grimjaw._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55      # perspektif tanah
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_grimjaw._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_grimjaw._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi api/bulu bergerigi (pixel-art).

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

    # ---------------------------------------------------------------------------
    # SKILL FX PRIMITIVES v3 (rich pass — dipinjam dari kosakata Thorne/Gorath
    # dan diadaptasi ke tema api Grimjaw: rune sigil, band arc, nova petal,
    # shard kristal, dither disk, beam 3-lapis, energy arc, glint orbit).
    # Semua deterministik (hash) dan tanpa alokasi surface berlebih.
    # ---------------------------------------------------------------------------
    def _rgba(color, alpha):
        """Warna RGBA ter-clamp untuk pemanggilan pygame.draw langsung."""
        return (*_NS_grimjaw._clamp(color), max(0, min(255, int(alpha))))

    def _dpoly(surface, color, alpha, points):
        """Polygon RGBA fast-path: langsung blend ke canvas SRCALPHA."""
        if len(points) < 3 or alpha <= 0:
            return
        pts = [(int(px), int(py)) for px, py in points]
        pygame.draw.polygon(surface, _NS_grimjaw._rgba(color, alpha), pts)

    def _arc_band(surface, cx, cy, rx, ry, a0, a1, color, alpha,
                  width=2, segments=14):
        """Arc elips ringan tanpa alokasi surface (rim / band cahaya)."""
        if alpha <= 0 or rx <= 1 or ry <= 1:
            return
        col = _NS_grimjaw._rgba(color, alpha)
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
        col = _NS_grimjaw._rgba(color, alpha)
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
            _NS_grimjaw._rune_glyph(surface, gx, gy,
                                    max(2, int(size * (.8 + .35 * depth))),
                                    i * 3 + seed + int(phase * 2),
                                    col, int(alpha * depth), rot=a + math.pi / 2)
            if i % 2 == 0:
                pygame.draw.circle(
                    surface, _NS_grimjaw._rgba(ramp[2], alpha * .75 * depth),
                    (int(gx), int(gy)), 1)

    def _shard_glint(surface, x, y, color, alpha, size=3, core=False):
        """Kilau silang 4 arah 1px untuk ujung shard / pole anchor."""
        if alpha <= 0:
            return
        col = _NS_grimjaw._rgba(color, alpha)
        xi, yi = int(x), int(y)
        s = max(1, int(size))
        pygame.draw.line(surface, col, (xi - s, yi), (xi + s, yi), 1)
        pygame.draw.line(surface, col, (xi, yi - s), (xi, yi + s), 1)
        if core:
            pygame.draw.circle(
                surface, _NS_grimjaw._rgba(_NS_grimjaw.PALETTE["white"], alpha),
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
        _NS_grimjaw._dpoly(surface, ramp[0], alpha,
                           [base_l, base_r, sho_r, tip, sho_l])
        _NS_grimjaw._dpoly(surface, ramp[1], alpha,
                           [base_l, P(0, 3), P(0, -h * .8), sho_l])
        _skill_outlined_line(surface, sho_r, tip, 1, ramp[2], int(alpha * .9))
        _skill_outlined_line(surface, base_r, sho_r, 1, ramp[2], int(alpha * .7))
        pygame.draw.line(surface,
                         _NS_grimjaw._rgba(ramp[3], min(255, alpha + 30)),
                         P(-w * .5, -h * .35), P(-w * .2, -h * .6), 1)
        if glint:
            _NS_grimjaw._shard_glint(surface, tip[0], tip[1], ramp[3],
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
                surface, _NS_grimjaw._rgba(ramp[2], min(255, alpha + 40)),
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
            jx = (_NS_grimjaw._hash01(seed * 13 + i * 7) - .5) * wobble * 2
            jy = (_NS_grimjaw._hash01(seed * 29 + i * 11) - .5) * wobble * 2
            pts.append((x0 + (x1 - x0) * t + jx, y0 + (y1 - y0) * t + jy))
        pts.append((x1, y1))
        dark = _NS_grimjaw.PALETTE["shadow_deep"]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            ai, bi = (int(a[0]), int(a[1])), (int(b[0]), int(b[1]))
            pygame.draw.line(surface, _NS_grimjaw._rgba(dark, alpha * .45),
                             ai, bi, width + 2)
            pygame.draw.line(surface, _NS_grimjaw._rgba(color, alpha),
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
            _NS_grimjaw._dpoly(surface, ramp[1], int(alpha * .55), [p0, p1, p2])
            q0 = (cx + math.cos(a0) * r_in * .9,
                  cy + math.sin(a0) * r_in * .9 * squash)
            q1 = (cx + math.cos(a) * r_out * .74,
                  cy + math.sin(a) * r_out * .74 * squash)
            q2 = (cx + math.cos(a1) * r_in * .9,
                  cy + math.sin(a1) * r_in * .9 * squash)
            _NS_grimjaw._dpoly(surface, ramp[0], alpha, [q0, q1, q2])

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
                tw = _NS_grimjaw._hash01(seed * 31 + r * 13 + c * 7
                                         + int(phase * 3))
                a = int(alpha * (.45 + .55 * tw))
                if a <= 0:
                    continue
                pygame.draw.rect(
                    surface, _NS_grimjaw._rgba(color, a),
                    (int(cx + x), int(cy + ty), cell, cell))

    def _orbit_glints(surface, cx, cy, rx, ry, phase, n, color, alpha,
                      hot=None):
        """Titik kilau orbit elips (mengelilingi caster/target)."""
        if alpha <= 0 or n < 1:
            return
        for i in range(n):
            a = phase + i * math.tau / n
            px = int(cx + math.cos(a) * rx)
            py = int(cy + math.sin(a) * ry)
            _NS_grimjaw._aacircle(surface, (*color, alpha), (px, py), 2)
            if hot:
                _NS_grimjaw._aacircle(surface, (*hot, min(255, alpha)), (px, py), 1)

    def _draw_glow_orb(surface, cx, cy, r, ramp, alpha, core=True):
        """Orb glow berlapis 3 nilai: halo -> mid -> hot + inti putih."""
        if alpha <= 0 or r < 1:
            return
        _NS_grimjaw._aacircle(surface, (*ramp[0], int(alpha * .55)), (cx, cy), r)
        _NS_grimjaw._aacircle(surface, (*ramp[1], alpha), (cx, cy),
                              max(1, int(r * .72)))
        _NS_grimjaw._aacircle(surface, (*ramp[2], min(255, alpha + 30)), (cx, cy),
                              max(1, int(r * .45)))
        if core:
            _NS_grimjaw._aacircle(surface, (*ramp[2], min(255, alpha + 60)),
                                  (cx, cy), max(1, int(r * .24)))
            _NS_grimjaw._aacircle(surface, p_white := _NS_grimjaw.PALETTE["white"],
                                  (cx, cy), max(1, int(r * .12)))

    def _draw_rune_ring(surface, cx, cy, radius, phase, ramp, alpha,
                        n=8, squash=.6, width=2, seed=4):
        """Cincin rune putus-putus berputar (gabungan dashed ring + sigil)."""
        _NS_grimjaw._dashed_ring(surface, cx, cy, radius, ramp[0], int(alpha * .8),
                                 phase, segments=n * 2, thick=width, span=.4,
                                 squash=squash)
        _NS_grimjaw._sigil_ring(surface, cx, cy, radius * .82, -phase * .6, ramp,
                                int(alpha * .8), n=n, squash=squash, seed=seed,
                                size=max(3, int(radius * .055)))

    def _skill_progress(skill, timer):
        """Progress 0..1 skill FX dari countdown active_skill_timer.

        Durasi visual dipakai dari SKILL_VISUAL_DURATION (q=180, w=90,
        e=60, r=90) — bukan timer gameplay (yang bisa jauh lebih
        panjang, mis. W=360)."""
        dur = float(_NS_grimjaw.SKILL_VISUAL_DURATION.get(skill, max(1, timer or 1)))
        return max(0.0, min(1.0, 1.0 - float(timer) / dur))

    def _skill_steady(progress, tail=5.0, floor=.25):
        """Amplop fade akhir skill: plateau 1.0 lalu melandai ke floor."""
        return max(floor, min(1.0, (1.0 - progress) * tail + .3))

    def _aoe_marks(surface, cx, cy, radius, color, alpha, phase=0.0,
                   squash=1.0, ticks=12, tick_len=None, corner=True,
                   inner=False):
        """Marker AOE ANGULAR — pengganti ring/cincin kontinu.

        Menandai radius gameplay tanpa menggambar lingkaran: deretan
        ``tick`` pendek radial tepat di keliling ``radius`` + 4 bracket
        sudut di posisi diagonal (viewfinder).  Sudut FIXED
        (deterministik) sehingga radius dunia tetap terverifikasi;
        hidupnya dari pulse alpha + panjang tick yang bernapas.
        ``inner=True`` membuat tick mengarah keluar->ke dalam (untuk
        ring konvergen \"incoming\")."""
        if alpha <= 0 or radius < 4:
            return
        if tick_len is None:
            tick_len = max(6, int(radius * 0.10))
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase * 2.2))
        lo, hi = (radius - tick_len, radius) if not inner else (radius, radius + tick_len)
        for i in range(ticks):
            a = i * math.tau / ticks
            ca, sa = math.cos(a), math.sin(a)
            ox = cx + ca * hi
            oy = cy + sa * hi * squash
            ix = cx + ca * lo
            iy = cy + sa * lo * squash
            al = int(alpha * (0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase * 1.3 + i))))
            _skill_outlined_line(surface, (ix, iy), (ox, oy), 2, color, max(8, al))
        if corner:
            L = max(6, int(radius * 0.13))
            for a in (math.pi / 4, 3 * math.pi / 4,
                      5 * math.pi / 4, 7 * math.pi / 4):
                ca, sa = math.cos(a), math.sin(a)
                ta, tb = -sa, ca          # arah tangensial / normal
                txa, tya = ca, sa         # arah radial keluar
                px = cx + ca * radius
                py = cy + sa * radius * squash
                al = int(alpha * (0.7 + 0.3 * pulse))
                # siku: garis radial (keluar) + garis tangensial
                _skill_outlined_line(
                    surface, (px, py), (px + txa * L, py + tya * L * squash),
                    2, color, al)
                _skill_outlined_line(
                    surface, (px, py), (px + ta * L, py + tb * L * squash),
                    2, color, al)

    # ---------------------------------------------------------------------------
    # State detection helpers
    # ---------------------------------------------------------------------------
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
        """Track melee attack animation timeline."""
        cooldown = max(2, int(getattr(hero, "attack_cooldown", 40)))
        timer = int(getattr(hero, "timer", 0))
        previous = int(getattr(hero, "_gj_prev_timer", -1))
        active = bool(getattr(hero, "_gj_attack_active", False))

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
            hero._gj_attack_active = True
            hero._gj_crit_active = random.random() < 0.25
            active = True

        if active and timer <= 0:
            hero._gj_attack_active = False
            hero._gj_crit_active = False
            active = False

        hero._gj_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        hero._gj_attack_frame = max(0, cooldown - timer) if active else 0
        hero._gj_attack_progress = (
            min(1.0, hero._gj_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )

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

        attacking = (
            getattr(hero, "_gj_attack_active", False)
            or getattr(hero, "timer", 0) > getattr(hero, "attack_cooldown", 40) - 15
        )

        # Q = Blade Fury, W = Healing Ward, E = Critical Strike, R = Omnislash
        # (sesuai hero_skills/grimjaw_skills.py)
        is_blade_fury = active_skill == "q"
        is_healing_ward = active_skill == "w"
        is_crit_buff = active_skill == "e"
        is_omnislash = active_skill == "r"

        # Badan ikut bereaksi ke state skill (kwarg ke rig):
        #  fury  -> mane & ember mengembang
        #  ward  -> mata mask hijau + rim penyembuh
        #  crit  -> blade incandescent + trail bara merah
        #  omni  -> blade white-hot merah + flicker rage
        fury = is_blade_fury
        ward = is_healing_ward
        crit = is_crit_buff
        omni = is_omnislash

        # Portraits deliberately contain only the character rig.  Auras and
        # arena-sized skill effects would force the auto-crop to shrink the
        # mask, mane and armor detail.
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

        # Body lunge: sedikit ditarik ke belakang saat wind-up, lalu
        # menerjang maju dan mencapai puncaknya TEPAT saat pedang mendarat
        # (ATTACK_SWING_END). Rig v2 ~1.4x lebih lebar dari v1.
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

        if not portrait:
            # Fire slash arc (mengikuti jalur ujung pedang yang sama)
            _NS_grimjaw._draw_fire_slash_arc(surface, x + lunge, y,
                                             hero.direction, progress, crit,
                                             hero.pulse)

            # Impact flash: a bright hit-pop + shockwave ring at the moment
            # the blade connects, so EVERY attack has a satisfying impact.
            _NS_grimjaw._draw_impact_flash(surface, x + lunge, y,
                                           hero.direction, progress, crit)

            # Critical strike burst
            if crit and 0.56 < progress < 0.82:
                _NS_grimjaw._draw_critical_strike_burst(surface, x + lunge, y,
                                            hero.direction, progress)


    def _draw_grimjaw_blade_fury(surface, hero, x, y, timer, phase):
        """Blade Fury - spinning with fire rings."""
        spin_phase = phase * 6
        bob = int(math.sin(spin_phase) * -1)
        # Direction flips rapidly to simulate spinning
        facing = 1 if int(spin_phase * 2) % 2 == 0 else -1

        _NS_grimjaw._draw_shadow(surface, x, y + 72)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 56, phase * 2, intense=True)
        _NS_grimjaw._draw_grimjaw_body(surface, x, y + bob, facing, phase, "spin",
                           spin_phase=spin_phase, fury=True)


    def _draw_grimjaw_omnislash(surface, hero, x, y, timer, phase):
        """Omnislash - hero teleports rapidly with dramatic pose."""
        # Body flickers between poses
        flicker_phase = phase * 8
        offset_x = int(math.sin(flicker_phase) * 4)
        offset_y = int(math.cos(flicker_phase * 1.3) * 3)

        _NS_grimjaw._draw_shadow(surface, x, y + 72)
        _NS_grimjaw._draw_fire_mist(surface, x, y + 56, phase, intense=True)

        # Draw ghost trails behind current position: full-rig afterimages
        # in different slash poses, so the teleport reads as a storm of
        # overlapping Grimjaw cuts rather than one blurred sticker.
        for i in range(4):
            ghost_alpha = 45 + i * 28
            gx = x - int(math.sin(flicker_phase - i * 0.5) * 24)
            gy = y + int(math.cos(flicker_phase - i * 0.5) * 8)
            ghost_ap = max(0.05, 0.85 - i * 0.22)
            _NS_grimjaw._draw_grimjaw_ghost(surface, gx, gy,
                                            hero.direction, phase,
                                            ghost_alpha, ghost_ap)

        # Main body (with attack pose). Rig omnislash di-cache per
        # bucket fase (12/s): konten rig hanya berubah lewat fase
        # (mane/blade/trail), sementara jitter teleport (offset_x/y)
        # tetap live di blit. Pipeline hero sendiri sudah
        # mengkuantisasi frame skill; cache ini memangkas ~1.4 ms dari
        # frame R tanpa mengubah pembacaan badai tebasan.
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


    # Buffer afterimage R (omnislash): di-cache per (facing, pose bucket).
    # Pose ghost deterministik per indeks trail, jadi tiap pose cukup
    # dihitung SEKALI - tanpa re-render rig penuh 4x per frame.
    _GHOST_BUF = {}

    def _draw_grimjaw_ghost(surface, cx, cy, facing, phase, alpha,
                            attack_progress=0.6):
        """Full-rig afterimage of Grimjaw for the omnislash trail.

        Renders the complete layered bone rig (mane, mask, blade, armor)
        into a transparent buffer at reduced alpha so the teleport leaves
        real body afterimages instead of crude rectangle stickers.
        Buffer 220x220 di-cache per (facing, bucket pose) - afterimage
        sengaja memakai fase mane statis (fase=1.0): tekstur jejak tetap,
        posisinya yang bergeser antar frame.
        """
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
            # Crop ke bbox konten (di-cache bersama buffer): blit ghost
            # hanya area berisi piksel - 40% lebih murah per afterimage,
            # visual identik.
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


    # ===================================================================
    # BODY RENDERING - HD detailed Juggernaut (masterwork v2)
    # ===================================================================
    def _draw_grimjaw_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0, spin_phase=0, detail=False,
                           fury=False, ward=False, crit=False, omni=False):
        """Thin wrapper that keeps the historical signature so the idle/walk/
        attack/blade-fury/omnislash entry points continue to work and now
        route every frame through the single layered bone rig (rig v2,
        ~1.5x resolusi native)."""
        _NS_grimjaw._draw_grimjaw_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, spin_phase, detail,
            fury=fury, ward=ward, crit=crit, omni=omni)


    # -------------------------------------------------------------------
    # Pose helpers (deterministic - shared by rig + skill FX anchors)
    # -------------------------------------------------------------------
    # ═══ TIMELINE BASIC ATTACK (dipakai bersama rig + FX tebasan) ═══
    # Satu sumber kebenaran supaya pedang, lengan, crescent api, dan
    # impact flash tidak pernah lagi bergerak ke arah yang berlawanan.
    ATTACK_WINDUP_END = 0.25    # pedang selesai diangkat ke atas-belakang
    ATTACK_SWING_END = 0.62     # tebasan mendarat di depan-bawah
    # Sudut (radian, 0 = lurus ke bawah, positif = ke depan, negatif = ke
    # belakang) tempat tebasan MULAI dan BERAKHIR.  Nilainya MENGECIL
    # (-2.30 -> -5.35) karena ayunannya lewat ATAS kepala: atas-belakang
    # -> lurus atas -> depan-atas -> depan-bawah.  Kalau sudut membesar
    # (perilaku lama: -1.55 -> +1.35) pedang justru lewat BAWAH dan ujung
    # pedang NAIK di akhir ayunan, sehingga tebasan terbaca "dari bawah
    # ke atas".
    ATTACK_ARC_START = -2.30
    ATTACK_ARC_SWEEP = -3.05    # -2.30 + (-3.05) = -5.35 == +0.93 rad
    ATTACK_ARC_END = ATTACK_ARC_START + ATTACK_ARC_SWEEP

    def _blade_angle(phase, action, attack_progress=0.0, spin_phase=0.0):
        """Radian dari garis lurus-bawah: 0 = blade menunjuk ke bawah;
        +pi/2 = menunjuk lurus ke depan; negatif = wind-up ke belakang.

        Basic attack SELALU berputar ke arah negatif (mengecil): pedang
        diangkat ke atas-belakang kepala lalu menebas TURUN ke depan.
        """
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < _NS_grimjaw.ATTACK_WINDUP_END:
                # Wind-up: angkat pedang ke atas-belakang kepala.
                t = ap / _NS_grimjaw.ATTACK_WINDUP_END
                t = 1.0 - (1.0 - t) ** 2
                return -0.55 - t * 1.75
            if ap < _NS_grimjaw.ATTACK_SWING_END:
                # Tebasan: lewat atas kepala lalu turun ke depan-bawah.
                t = ((ap - _NS_grimjaw.ATTACK_WINDUP_END) /
                     (_NS_grimjaw.ATTACK_SWING_END -
                      _NS_grimjaw.ATTACK_WINDUP_END))
                t = t ** 1.35                      # akselerasi ke benturan
                return (_NS_grimjaw.ATTACK_ARC_START +
                        _NS_grimjaw.ATTACK_ARC_SWEEP * t)
            # Recovery: dari depan-bawah kembali ke pose jaga (tanpa
            # mengayun balik ke atas - itu yang bikin tebasan tampak naik).
            if ap >= 1.0:
                # Persis 0.12 = sudut blade idle (phase 0): frame akhir
                # serang identik piksel-dengan-piksel dengan pose jaga
                # (loop closure tanpa pop antar frame).
                return 0.12
            t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
                 (1.0 - _NS_grimjaw.ATTACK_SWING_END))
            t = t * t * (3.0 - 2.0 * t)
            # 0.933 - 0.813 = 0.12 = sudut blade idle (phase 0).
            return (_NS_grimjaw.ATTACK_ARC_END + 2.0 * math.pi) - t * 0.813
        if action == "spin":
            return spin_phase * 0.5 + math.sin(phase * 1.2) * 0.06
        if action == "walk":
            return 0.08 + math.sin(phase * 1.72) * 0.10
        return 0.12 + math.sin(phase * 0.5) * 0.05

    def _blade_grip_local(action, attack_progress=0.0, phase=0.0):
        """Posisi gagang/pegangan blade (ruang lokal, forward = +x).

        Rig v2: koordinat keyframe ~1.5x versi lama supaya pegangan
        menempel pada tangan rig yang lebih besar.
        """
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < _NS_grimjaw.ATTACK_WINDUP_END:
                t = ap / _NS_grimjaw.ATTACK_WINDUP_END
                return (14 + int(6 * t), 1 - int(28 * t))      # (14,1) -> (20,-27)
            if ap < _NS_grimjaw.ATTACK_SWING_END:
                t = ((ap - _NS_grimjaw.ATTACK_WINDUP_END) /
                     (_NS_grimjaw.ATTACK_SWING_END -
                      _NS_grimjaw.ATTACK_WINDUP_END))
                if t < 0.45:
                    # Tangan tetap tinggi sambil memutar lewat atas kepala.
                    u = t / 0.45
                    return (20 + int(16 * u), -27 + int(6 * u))
                # Bagian terakhir tebasan: tangan turun mengikuti pedang.
                u = (t - 0.45) / 0.55
                u = u * u
                return (36 + int(3 * u), -21 + int(30 * u))    # -> (39, 9)
            t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
                 (1.0 - _NS_grimjaw.ATTACK_SWING_END))
            return (39 - int(22 * t), 9 - int(6 * t))          # -> (17, 3) pose jaga
        if action == "spin":
            return (26, -4)
        if action == "walk":
            return (17 + int(math.sin(phase * 1.72) * 3), 3)
        return (17, 3)

    def _blade_len(action):
        return 52 if action != "attack" else 58

    def _blade_len_ap(action, attack_progress=0.0):
        """Panjang bilah per progres serang.

        58 px saat wind-up/tebas, menyusut ke 52 (panjang pose jaga)
        selama recovery, sehingga frame akhir serang = frame idle
        persis (loop closure tanpa pop).
        """
        if action != "attack":
            return 52
        ap = max(0.0, min(1.0, attack_progress))
        if ap < _NS_grimjaw.ATTACK_SWING_END:
            return 58
        t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
             (1.0 - _NS_grimjaw.ATTACK_SWING_END))
        return 58 - int(6 * t)

    def _front_arm_elbow(attack_progress=0.0):
        """Siku lengan pedang selama basic attack (ruang lokal).

        Dihitung dari keyframe (rig v2, ~1.5x versi lama): saat tangan
        terangkat tinggi di atas kepala (wind-up) offset tetap membuat
        siku "menciut" ke bahu dan lengan tampak patah. Keyframe ini
        menjaga panjang upper arm dan forearm ~19 px di setiap pose.
        """
        ap = max(0.0, min(1.0, attack_progress))
        if ap < _NS_grimjaw.ATTACK_WINDUP_END:
            t = ap / _NS_grimjaw.ATTACK_WINDUP_END
            return (11 + int(25 * t), 11 - int(28 * t))        # (11,11) -> (36,-18)
        if ap < _NS_grimjaw.ATTACK_SWING_END:
            t = ((ap - _NS_grimjaw.ATTACK_WINDUP_END) /
                 (_NS_grimjaw.ATTACK_SWING_END -
                  _NS_grimjaw.ATTACK_WINDUP_END))
            if t < 0.45:
                u = t / 0.45
                return (36 - int(2 * u), -18 + int(15 * u))    # -> (35, -3)
            u = (t - 0.45) / 0.55
            return (35 + int(2 * u), -3 - int(3 * u))          # -> (36, -6)
        t = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
             (1.0 - _NS_grimjaw.ATTACK_SWING_END))
        # endpoint (12,11) = siku idle (grip (17,3) -> (17-5, 3+8))
        return (36 - int(24 * t), -6 + int(17 * t))            # -> (12, 11)

    def _blade_tip_local(phase, action, attack_progress=0.0, spin_phase=0.0):
        """Posisi ujung blade (ruang lokal) - dipakai sebagai anchor FX."""
        a = _NS_grimjaw._blade_angle(phase, action, attack_progress, spin_phase)
        gx, gy = _NS_grimjaw._blade_grip_local(action, attack_progress, phase)
        L = _NS_grimjaw._blade_len_ap(action, attack_progress)
        return (int(gx + math.sin(a) * L), int(gy + math.cos(a) * L))

    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose badan.

        Keyframe: (progress, bob, lean, flare, tremble)
          0.00  rest      : pose jaga
          0.12  wind-up   : badan turun & mundur, pedang diangkat
          0.26  tension   : gemetar 1 px, mane mengembang
          0.42  strike    : ayunan tercepat (smear aktif)
          0.55  IMPACT    : squash maksimum (bintang/shockwave di FX)
          0.72  follow    : rebound overshoot
          1.00  recover   : kembali ke pose jaga
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
                t = t * t * (3 - 2 * t)          # smoothstep
                bob = k0[1] + (k1[1] - k0[1]) * t
                lean = k0[2] + (k1[2] - k0[2]) * t
                flare = k0[3] + (k1[3] - k0[3]) * t
                tremble = 1 if (k0[4] and t < 0.9) else 0
                return {"bob": int(round(bob)), "lean": int(round(lean)),
                        "flare": flare, "tremble": tremble}
        return {"bob": 0, "lean": 1, "flare": 1.0, "tremble": 0}

    # ===================================================================
    # MASTERWORK RIG v2 - bone rig 2D berlapis (setara Thorne v2)
    # ===================================================================
    def _draw_grimjaw_elite(surface, cx, cy, facing, phase, action,
                            attack_progress=0.0, spin_phase=0.0,
                            detail=False, fury=False, ward=False,
                            crit=False, omni=False):
        """Rig masterwork v2 - berserker flame-blade, 100% prosedural.

        Semua koordinat lokal: (0,0) = jangkar pinggul, x maju (facing),
        y ke bawah. Telapak menapak di +70. Skala rig ~1.5x versi lama
        (pipeline hero otomatis menormalkan ukuran akhir di arena).

        Disiplin pixel-art:
          * ramp 4-5 band per material dengan hue-shift
          * selout: outline gelap hanya di sisi bayangan (+f, +1)
          * siluet mane bergerigi via _tuft_points (hash deterministik)
          * specular cluster 1-2 px yang disengaja
          * dither band di perut
          * key light kiri-atas (konsisten lighting.py LIGHT_DIR (-1,-1))
        """
        p = _NS_grimjaw.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        spin = action == "spin"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72) if walk else 0.0
        breath = math.sin(phase * 0.78)

        # ═══ 1. GERAK BADAN: root / lean / sway / mane lag ═══
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
            t_rec = ((ap - _NS_grimjaw.ATTACK_SWING_END) /
                     (1.0 - _NS_grimjaw.ATTACK_SWING_END))
            t_rec = max(0.0, min(1.0, t_rec))
            # tilt mane kembali 0 saat pulih (idle = 0) -> tanpa pop
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

        def pt(dx, dy):
            return (int(cx + dx * f + off_x), int(cy + dy + root_y))

        def poly(color, coords, selout=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if selout:
                _NS_grimjaw._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_grimjaw._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_grimjaw._aaline(surface, p["shadow_deep"],
                                (aa[0] + f, aa[1] + 1),
                                (bb[0] + f, bb[1] + 1), width + 3)
            _NS_grimjaw._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_grimjaw._aaline(surface, light,
                                    (aa[0] + off, aa[1] - 1),
                                    (bb[0] + off, bb[1] - 1),
                                    max(1, width // 3))

        def dot(color, dx, dy, r, outline=True):
            x, y = pt(dx, dy)
            if outline:
                _NS_grimjaw._aacircle(surface, p["shadow_deep"],
                                      (x + f, y + 1), r + 1)
            _NS_grimjaw._aacircle(surface, color, (x, y), r)

        # ═══ 2. MANE API BELAKANG (volume + lick, dengan inersia) ═══
        flare = 1.0
        if attack:
            flare = _NS_grimjaw._attack_pose(ap)["flare"]
        if spin:
            flare = 1.12
        if fury:
            flare *= 1.10 + 0.05 * math.sin(phase * 3)
        if crit or omni:
            flare *= 1.06
        _NS_grimjaw._draw_elite_flame_mane(surface, pt, poly, f, phase,
                                           action, crest_tilt, flare)

        # ═══ 3. LENGAN BELAKANG (tangan bebas, tinju) ═══
        rear_shoulder = (-13, -24)
        if attack:
            # selama recovery kembali ke pose idle (tanpa pop)
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
        limb(rear_shoulder, rear_elbow, 9, p["skin_dark"], p["skin_mid"])
        limb(rear_elbow, rear_hand, 8, p["skin_mid"], p["skin_high"])
        dot(p["skin_darkest"], *rear_hand, 5)
        dot(p["skin_mid"], *rear_hand, 4)
        rhx, rhy = pt(*rear_hand)
        _NS_grimjaw._aacircle(surface, p["skin_high"],
                              (rhx - f, rhy - 2), 2, False)
        # knuckles
        for kn in (-2, 0, 2):
            _NS_grimjaw._rect(surface, p["skin_dark"],
                              (int(rhx + f * 2) + kn - 1, int(rhy) + 2, 2, 2))

        # ═══ 4. WAR-SKIRT BELAKANG (di belakang kaki) ═══
        skirt_sway = int(math.sin(phase * 0.9 + 1.2) * 3)
        poly(p["red_darkest"], [(-16, 6), (16, 6), (14 + skirt_sway, 34),
             (6, 42), (0, 39), (-6, 43), (-14 + skirt_sway, 33)])
        poly(p["red_dark"], [(-14, 8), (14, 8), (12 + skirt_sway, 30),
             (5, 37), (0, 34), (-5, 38), (-12 + skirt_sway, 29)], False)
        _NS_grimjaw._aaline(surface, p["red_mid"], pt(-6, 10),
                            pt(-8 + skirt_sway, 33), 1)
        _NS_grimjaw._aaline(surface, p["red_mid"], pt(6, 10),
                            pt(8 + skirt_sway, 32), 1)

        # ═══ 5. KAKI: paha + shin guard + boot (foot solver) ═══
        front_step = int(stride * 8) if walk else 0
        rear_step = -front_step
        if attack:
            # lunge maju runtuh kembali ke stance jaga saat recovery
            front_step += int(ap * 8 * (1.0 - t_rec))
            rear_step -= int(ap * 4 * (1.0 - t_rec))
        stride_vel = math.cos(phase * 1.72) if walk else 0.0
        front_lift = int(max(0.0, stride_vel) * 10) if walk else 0
        rear_lift = int(max(0.0, -stride_vel) * 10) if walk else 0
        for side, step, boot, lift in ((-1, rear_step, p["boot_dark"], rear_lift),
                                       (1, front_step, p["boot_mid"], front_lift)):
            hipx = side * 10
            tx = hipx + int(step * 0.3)
            kx = side * 12 + int(step * 0.5)
            fx = side * 13 + step
            # paha (skin 3 band, lutut ikut naik => knee-bend)
            poly(p["skin_darkest"], [(tx - 7, 6), (tx + 7, 6),
                 (kx + 6, 30 - lift), (kx - 6, 30 - lift)])
            poly(p["skin_dark"], [(tx - 6, 7), (tx + 6, 7),
                 (kx + 5, 29 - lift), (kx - 5, 29 - lift)], False)
            _NS_grimjaw._aaline(surface, p["skin_light"],
                                pt(tx - f * 3, 8), pt(kx - f * 3, 28 - lift), 2)
            # shin guard baja (4 band + rivet)
            poly(p["metal_darkest"], [(kx - 7, 30 - lift), (kx + 7, 30 - lift),
                 (kx + 8, 52 - lift), (kx - 7, 52 - lift)])
            poly(p["metal_dark"], [(kx - 6, 31 - lift), (kx + 6, 31 - lift),
                 (kx + 7, 51 - lift), (kx - 6, 51 - lift)], False)
            poly(p["metal_mid"], [(kx - 4, 33 - lift), (kx + 3, 33 - lift),
                 (kx + 4, 49 - lift), (kx - 4, 49 - lift)], False)
            _NS_grimjaw._aaline(surface, p["metal_light"],
                                pt(kx - f * 4, 34 - lift),
                                pt(kx - f * 4, 48 - lift), 1)
            # gold knee cap + ankle cuff
            _NS_grimjaw._aaline(surface, p["gold_dark"],
                                pt(kx - 6, 33 - lift), pt(kx + 6, 33 - lift), 2)
            _NS_grimjaw._aaline(surface, p["gold_mid"],
                                pt(kx - 6, 32 - lift), pt(kx + 6, 32 - lift), 1)
            _NS_grimjaw._aaline(surface, p["gold_dark"],
                                pt(kx - 7, 49 - lift), pt(kx + 7, 49 - lift), 1)
            _NS_grimjaw._aaline(surface, p["gold_mid"],
                                pt(kx - 7, 48 - lift), pt(kx + 7, 48 - lift), 1)
            _NS_grimjaw._aacircle(surface, p["gold_light"],
                                  pt(kx - f * 2, 33 - lift), 1, False)
            # boot 3 band + toe
            poly(boot, [(fx - 8, 50 - lift), (fx + 7, 50 - lift),
                 (fx + 9, 68 - lift), (fx - 9, 68 - lift)], False)
            _NS_grimjaw._rect(surface, p["boot_darkest"],
                              (pt(fx, 66 - lift)[0] - 8, pt(fx, 66 - lift)[1], 16, 4))
            _NS_grimjaw._rect(surface, p["boot_light"],
                              (pt(fx, 51 - lift)[0] - 8, pt(fx, 51 - lift)[1], 15, 2))
            toe = 6 * f
            foot = pt(fx + (4 if f > 0 else -4), 68 - lift)
            _NS_grimjaw._aaline(surface, p["shadow_deep"],
                                (foot[0] - toe, foot[1] + 1),
                                (foot[0] + toe, foot[1] + 1), 4)
            _NS_grimjaw._aaline(surface, p["boot_light"],
                                (foot[0] - toe, foot[1]),
                                (foot[0] + toe, foot[1]), 2)
            # bayangan kontak tanah (per telapak) + debu saat menapak
            if lift == 0:
                planted = (not walk) or abs(stride_vel) < 0.55
                if planted:
                    _NS_grimjaw._ellipse(
                        surface, (*p["shadow_deep"], 60),
                        (pt(fx, 70)[0] - 15, pt(fx, 70)[1], 30, 7))
            if walk and lift == 0 and abs(stride_vel) < 0.35:
                fdx, fdy = pt(fx - 6, 69)
                for k in range(3):
                    _NS_grimjaw._aacircle(
                        surface, (*p["fire_mid"], max(20, 110 - k * 30)),
                        (fdx - k * 5 * f, fdy - k * 2), max(1, 3 - k))

        # ═══ 6. TORSO: dada V-taper + sash + harness ═══
        poly(p["skin_darkest"], [(-16, -28), (16, -28), (13, -6),
             (11, 10), (-11, 10), (-13, -6)])
        poly(p["skin_dark"], [(-14, -26), (14, -26), (11, -5),
             (10, 9), (-10, 9), (-11, -5)], False)
        poly(p["skin_mid"], [(-12, -24), (12, -24), (9, -4),
             (8, 8), (-8, 8), (-9, -4)], False)
        # key light kiri-atas: pita terang sisi atas-kiri
        poly(p["skin_light"], [(-12, -25), (-2, -26), (4, -24),
             (1, -14), (-9, -15)], False)
        # pec + sternum lines
        _NS_grimjaw._aaline(surface, p["skin_darkest"], pt(0, -20),
                            pt(0, 6), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(-8, -14),
                            pt(-1, -12), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(1, -12),
                            pt(8, -14), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(-7, -2),
                            pt(7, -2), 1)
        _NS_grimjaw._aaline(surface, p["skin_dark"], pt(-6, 5),
                            pt(6, 5), 1)
        # dither band (belly) - tekstur klasik yang selamat dari downscale
        for i in range(5):
            for j in range(2):
                if (i + j) % 2 == 0:
                    _NS_grimjaw._rect(surface, p["skin_darkest"],
                                      (int(cx + (-6 + i * 3) * f + off_x),
                                       int(cy + 2 + j * 4 + root_y), 1, 1))
        # sash merah diagonal (3 band + tepi darah)
        poly(p["red_darkest"], [(-15, -25), (-9, -28), (13, 8),
             (11, 12), (-15, -3)])
        poly(p["red_dark"], [(-13, -24), (-8, -26), (11, 7),
             (9, 10)], False)
        _NS_grimjaw._aaline(surface, p["red_light"], pt(-11, -24),
                            pt(9, 8), 1)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(-14, -23),
                            pt(-12, -25), 1)
        # harness X kulit (diagonal berlawanan) + studs + buckle
        _NS_grimjaw._aaline(surface, p["armor_darkest"], pt(13, -25),
                            pt(-11, 9), 5)
        _NS_grimjaw._aaline(surface, p["armor_mid"], pt(12, -25),
                            pt(-11, 8), 3)
        off = -1 if f > 0 else 1
        _NS_grimjaw._aaline(surface, p["armor_light"], pt(12 + off, -26),
                            pt(-11 + off, 7), 1)
        for i in range(3):
            t = 0.25 + i * 0.25
            sx = int(13 + (-11 - 13) * t)
            sy = int(-25 + (9 + 25) * t)
            _NS_grimjaw._aacircle(surface, p["gold_mid"], pt(sx, sy), 1)
        _NS_grimjaw._rect(surface, p["gold_dark"],
                          (pt(11, -27)[0] - 2, pt(11, -27)[1] - 2, 5, 5))
        _NS_grimjaw._rect(surface, p["gold_mid"],
                          (pt(11, -27)[0] - 1, pt(11, -27)[1] - 1, 3, 3))
        # sternum medallion
        dot(p["gold_darkest"], 0, -16, 4)
        dot(p["gold_dark"], 0, -16, 3)
        dot(p["gold_mid"], 0, -16, 2)
        _NS_grimjaw._aacircle(surface, p["gold_shine"], pt(-f, -17), 1, False)

        # ═══ 7. SABUK + gesper emas + studs ═══
        poly(p["armor_darkest"], [(-13, 8), (13, 8), (13, 14), (-13, 14)])
        poly(p["red_darkest"], [(-12, 9), (12, 9), (12, 13), (-12, 13)], False)
        for bx in (-9, -5, 5, 9):
            _NS_grimjaw._aacircle(surface, p["gold_dark"], pt(bx, 11), 1, False)
            _NS_grimjaw._aacircle(surface, p["gold_mid"], pt(bx, 10), 1, False)
        dot(p["gold_darkest"], 0, 11, 4)
        dot(p["gold_dark"], 0, 11, 3)
        dot(p["gold_mid"], 0, 11, 2)
        _NS_grimjaw._aacircle(surface, p["gold_light"], pt(-f, 10), 1, False)

        # ═══ 8. LOINCLOTH DEPAN + hem bergerigi (tuft) ═══
        cloth_sway = int(math.sin(phase * 1.1) * 3)
        hem_spine = [(-10, 12), (-9, 22), (-5, 30 + cloth_sway),
                     (0, 34 + cloth_sway), (5, 29 + cloth_sway),
                     (9, 22), (10, 12)]
        hem = _NS_grimjaw._tuft_points(hem_spine, depth=3.0, min_len=5, seed=9)
        poly(p["red_darkest"], [(-10, 12)] + hem)
        poly(p["red_dark"], [(-8, 14), (-7, 22), (-4, 28 + cloth_sway),
             (0, 31 + cloth_sway), (4, 27 + cloth_sway), (7, 21), (8, 14)], False)
        poly(p["red_mid"], [(-4, 15), (4, 15), (4 + cloth_sway, 25),
             (0, 29), (-3 + cloth_sway, 24), (-4, 20)], False)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(-3, 16),
                            pt(1 + cloth_sway, 27), 1)

        # ═══ 9. HIP TASSETS (3 pelat per sisi, rivet emas) ═══
        for side in (-1, 1):
            hx = side * 13
            for i, (y0, y1, tip) in enumerate(((9, 18, 22),
                                               (10, 17, 20),
                                               (11, 16, 18))):
                dx = (2 - i)
                poly(p["armor_darkest"], [(hx - 4 - dx, y0), (hx + 3 - dx, y0),
                     (hx + 2 - dx, y1), (hx - 1, tip),
                     (hx - 5 - dx, y1)], False)
                poly(p["armor_dark"], [(hx - 3 - dx, y0 + 1), (hx + 2 - dx, y0 + 1),
                     (hx + 1 - dx, y1 - 1), (hx - 1, tip - 1)], False)
                _NS_grimjaw._aacircle(surface, p["gold_dark"],
                                      pt(hx - 1, tip), 1, False)
                _NS_grimjaw._aacircle(surface, p["gold_light"],
                                      pt(hx - 1, tip - 1), 1, False)

        # ═══ 10. PAULDRON baja berlapis + duri + rivet ═══
        for side in (-1, 1):
            sx = side * 16
            poly(p["metal_darkest"], [(sx - 8, -34), (sx + 8, -34),
                 (sx + 9, -24), (sx, -19), (sx - 9, -24)])
            poly(p["metal_dark"], [(sx - 7, -33), (sx + 7, -33),
                 (sx + 8, -25), (sx, -21), (sx - 8, -25)], False)
            poly(p["metal_mid"], [(sx - 5, -32), (sx + 5, -32),
                 (sx + 5, -26), (sx, -23), (sx - 5, -26)], False)
            # gold rim
            poly(p["gold_dark"], [(sx - 8, -24), (sx + 8, -24),
                 (sx + 3, -20), (sx - 3, -20)], False)
            _NS_grimjaw._aaline(surface, p["gold_mid"],
                                pt(sx - 7, -24), pt(sx + 7, -24), 1)
            # duri
            poly(p["metal_darkest"], [(sx - 3, -34), (sx - 1, -45),
                 (sx + 1, -34)])
            poly(p["metal_mid"], [(sx - 2, -34), (sx - 1, -43),
                 (sx + 1, -33)], False)
            poly(p["metal_darkest"], [(sx + 2, -34), (sx + 4, -42),
                 (sx + 6, -34)])
            _NS_grimjaw._aacircle(surface, p["metal_shine"], pt(sx - 3, -30), 1, False)
            # plate seams + rivets
            _NS_grimjaw._aaline(surface, p["metal_darkest"],
                                pt(sx - 7, -29), pt(sx + 7, -29), 1)
            _NS_grimjaw._aaline(surface, p["metal_darkest"],
                                pt(sx - 6, -26), pt(sx + 6, -26), 1)
            _NS_grimjaw._aaline(surface, p["metal_light"],
                                pt(sx - 6, -30), pt(sx + 6, -30), 1)
            for rx in (-5, -2, 2, 5):
                _NS_grimjaw._aacircle(surface, p["metal_darkest"],
                                      pt(sx + rx, -22), 1, False)
                _NS_grimjaw._aacircle(surface, p["metal_shine"],
                                      pt(sx + rx, -23), 1, False)

        # ═══ 11. LEHER ═══
        poly(p["skin_darkest"], [(-6, -32), (6, -32), (8, -26), (-8, -26)])
        poly(p["skin_mid"], [(-4, -31), (4, -31), (5, -27), (-5, -27)], False)

        # ═══ 12. LENGAN DEPAN (lengan blade) ═══
        grip = _NS_grimjaw._blade_grip_local(action, ap, phase)
        front_shoulder = (12, -24)
        if attack:
            front_elbow = _NS_grimjaw._front_arm_elbow(ap)
        elif walk:
            front_elbow = (grip[0] - 5, grip[1] + 7 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 5, grip[1] + 8)
        limb(front_shoulder, front_elbow, 9, p["skin_dark"], p["skin_mid"])
        limb(front_elbow, grip, 8, p["skin_mid"], p["skin_high"])
        # bracer baja di siku
        exx, exy = pt(*front_elbow)
        _NS_grimjaw._rect(surface, p["metal_darkest"],
                          (int(exx - 5), int(exy - 4), 11, 9), border_radius=2)
        _NS_grimjaw._rect(surface, p["metal_mid"],
                          (int(exx - 4), int(exy - 3), 9, 7), border_radius=2)
        _NS_grimjaw._aaline(surface, p["gold_mid"],
                            (int(exx - 4), int(exy + 3)), (int(exx + 5), int(exy + 3)), 1)
        dot(p["skin_darkest"], *grip, 5)
        dot(p["skin_mid"], *grip, 4)
        _NS_grimjaw._aacircle(surface, p["skin_high"],
                              pt(grip[0] - 1, grip[1] - f), 2, False)

        # ═══ 13. FLAME BLADE + smear + spin trail ═══
        angle = _NS_grimjaw._blade_angle(phase, action, ap, spin_phase)
        length = _NS_grimjaw._blade_len_ap(action, ap)
        hot = crit or omni

        # Smear ayunan: crescent 3-band mengikuti jalur ujung pedang
        if attack and 0.30 < ap < 0.88:
            _NS_grimjaw._draw_blade_swing_trail(surface, cx, cy, f, phase, ap)

        # Blade Fury: lingkaran api yang berputar + ghost blade
        if spin:
            _NS_grimjaw._draw_spin_flame_sweep(surface, cx, cy, f, spin_phase,
                                               phase)

        _NS_grimjaw._draw_elite_flame_blade(
            surface, pt, f, grip, angle, length, phase, detail,
            hot=hot, omni=omni)

        # ═══ 14. MASK JUGGENAUR + kepala ═══
        _NS_grimjaw._draw_elite_mask(surface, pt, poly, dot, f, phase,
                                     action, ap, detail, ward=ward,
                                     crit=crit)

        # ═══ 15. FRONGE + side locks mane ═══
        _NS_grimjaw._draw_elite_mane_front(surface, pt, poly, f, phase,
                                           action, crest_tilt)

        if detail:
            _NS_grimjaw._draw_grimjaw_masterwork_details(
                surface, pt, poly, f, phase, action)

    # -------------------------------------------------------------------
    # Flame mane (back crest) - volume ber-tuft + lick ber-pita
    # -------------------------------------------------------------------
    def _draw_elite_flame_mane(surface, pt, poly, f, phase, action,
                               crest_tilt=0.0, flare=1.0):
        p = _NS_grimjaw.PALETTE
        wave = int(math.sin(phase * 1.2) * 2)
        # Spine siluet mane; tepi luar digergaji (_tuft_points, hash).
        spine = [(-15, -32), (-23, -42), (-27, -56), (-23, -70),
                 (-14, -82), (-4, -88), (6, -87), (16, -79),
                 (23, -65), (25, -49), (19, -36), (10, -30), (-8, -29)]
        outer = _NS_grimjaw._tuft_points(spine, depth=4.5, min_len=8, seed=11)

        def shrink(points, s):
            base = (0, -48)
            out = []
            for x, y in points:
                out.append((int(base[0] + (x - base[0]) * s),
                            int(base[1] + (y - base[1]) * s)))
            return out

        # 5 lapisan volume: selout terluar -> core api paling dalam
        poly(p["hair_darkest"], outer)
        poly(p["hair_dark"], shrink(outer, 0.82), False)
        poly(p["hair_mid"], shrink(outer, 0.62), False)
        poly(p["fire_dark"], shrink(outer, 0.44), False)
        poly(p["fire_mid"], shrink(outer, 0.26), False)

        # Lick api: 9 helai, 4 band, flicker + inersia (crest_tilt)
        licks = [
            (-22, -58, -30, -74, 5),
            (-16, -72, -20, -90, 6),
            (-8, -82, -9, -100, 6),
            (0, -88, 1, -108, 7),
            (8, -84, 10, -100, 6),
            (16, -74, 20, -88, 5),
            (22, -58, 30, -72, 4),
            (24, -46, 32, -56, 3),
            (-24, -46, -32, -54, 3),
        ]
        for i, (bx, by, tx, ty, wd) in enumerate(licks):
            tw = (wave if bx > 0 else -wave) + int(crest_tilt * 46)
            ty2 = ty + int(abs(wave) * 0.4) - int(crest_tilt * 30 * (i / 4))
            flick = int(math.sin(phase * 4.2 + i * 1.3) * 2)
            tx2 = tx + tw + flick
            ty2 = ty2 + (flick if i % 2 else -flick)
            ln = math.hypot(tx2 - bx, ty2 - by) * flare
            tx3 = bx + (tx2 - bx) * flare
            ty3 = by + (ty2 - by) * flare
            poly(p["hair_darkest"], [(bx - wd, by), (tx3, ty3),
                 (bx + wd, by)])
            poly(p["fire_dark"], [(bx - wd + 1, by), (tx3, ty3),
                 (bx + wd - 1, by)], False)
            poly(p["fire_mid"], [(bx - wd // 2, by), (tx3, ty3),
                 (bx + wd // 2, by)], False)
            _NS_grimjaw._aaline(surface, p["fire_light"], pt(bx - 1, by),
                                pt(tx3, ty3), 1)
            _NS_grimjaw._rect(surface, p["fire_hot"],
                              (pt(tx3, ty3)[0] - 1, pt(tx3, ty3)[1] - 1, 2, 2))

    # -------------------------------------------------------------------
    # Front fringe + side locks
    # -------------------------------------------------------------------
    def _draw_elite_mane_front(surface, pt, poly, f, phase, action,
                               crest_tilt=0.0):
        p = _NS_grimjaw.PALETTE
        wave = int(math.sin(phase * 1.2) * 2)
        fringe = [(-8, -64, -10, -56), (-3, -66, -4, -57),
                  (3, -66, 3, -57), (8, -64, 10, -56)]
        for i, (sx, sy, ex, ey) in enumerate(fringe):
            wig = wave if i % 2 else -wave
            poly(p["hair_darkest"], [(sx - 2, sy), (sx + 2, sy),
                 (ex + wig, ey)], False)
            poly(p["hair_mid"], [(sx - 1, sy), (sx + 1, sy),
                 (ex + wig, ey)], False)
            _NS_grimjaw._aaline(surface, p["hair_light"], pt(sx, sy),
                                pt(ex + wig, ey), 1)
        for side in (-1, 1):
            sway = int(math.sin(phase * 1.0 + side) * 2)
            sx = side * 13
            poly(p["hair_darkest"], [(sx - 2, -52), (sx + 2, -52),
                 (sx + 5 * side + sway, -40), (sx + 2 * side, -36),
                 (sx - 1 * side, -43)], False)
            poly(p["fire_dark"], [(sx - 1, -50), (sx + 1, -50),
                 (sx + 4 * side + sway, -41), (sx + 1 * side, -38)], False)
            _NS_grimjaw._aaline(surface, p["hair_mid"],
                                pt(sx, -49), pt(sx + 4 * side + sway, -40), 1)

    # -------------------------------------------------------------------
    # White juggernaut mask - 5 band, strip darah, grille, mata
    # -------------------------------------------------------------------
    def _draw_elite_mask(surface, pt, poly, dot, f, phase, action, ap,
                         detail=False, ward=False, crit=False):
        p = _NS_grimjaw.PALETTE
        eyes_glow = action in ("attack", "spin") or ap > 0.35 or crit
        eye_col = p["heal_light"] if ward else p["eye_glow"]
        poly(p["mask_shadow"], [(-9, -66), (0, -72), (9, -66),
             (12, -58), (12, -48), (9, -40), (5, -36),
             (0, -34), (-5, -36), (-9, -40), (-12, -48), (-12, -58)])
        poly(p["mask_dark"], [(-8, -64), (0, -70), (8, -64),
             (10, -57), (10, -48), (8, -41), (4, -37),
             (0, -35), (-4, -37), (-8, -41), (-10, -48), (-10, -57)], False)
        poly(p["mask_mid"], [(-6, -62), (0, -67), (6, -62),
             (8, -55), (8, -47), (6, -40), (3, -37),
             (0, -36), (-3, -37), (-6, -40), (-8, -47), (-8, -55)], False)
        # key light: pita terang sisi kiri-atas
        poly(p["mask_light"], [(-6, -61), (-1, -65), (3, -63),
             (5, -55), (4, -46), (1, -39), (-3, -38), (-6, -45),
             (-7, -54)], False)
        _NS_grimjaw._aacircle(surface, p["mask_shine"], pt(-f * 4, -62), 2)
        # specular cluster kecil
        _NS_grimjaw._aacircle(surface, p["mask_shine"], pt(-f * 6, -56), 1)

        # Forehead crest: emblem emas diamond
        poly(p["gold_darkest"], [(-2, -67), (2, -67), (3, -62),
             (0, -60), (-3, -62)])
        poly(p["gold_mid"], [(-1, -66), (1, -66), (2, -62),
             (0, -61), (-2, -62)], False)
        _NS_grimjaw._aacircle(surface, p["gold_shine"], pt(0, -63), 1)

        # Brow ridge
        _NS_grimjaw._aaline(surface, p["mask_shadow"], pt(-9, -55),
                            pt(-3, -58), 2)
        _NS_grimjaw._aaline(surface, p["mask_shadow"], pt(9, -55),
                            pt(3, -58), 2)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(-9, -56),
                            pt(-4, -59), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(9, -56),
                            pt(4, -59), 1)
        # Nose bridge
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(0, -62),
                            pt(0, -44), 1)
        # Blood stripes: tebal tengah (dengan drip) + 2 slash tipis
        poly(p["blood_darkest"], [(-1, -69), (2, -69), (2, -40),
             (1, -36), (-1, -40)])
        poly(p["blood_dark"], [(0, -68), (1, -68), (1, -41),
             (0, -38)], False)
        poly(p["blood_mid"], [(0, -42), (1, -42), (1, -38), (0, -38)], False)
        _NS_grimjaw._aaline(surface, p["blood_light"], pt(1, -66),
                            pt(1, -42), 1)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(-8, -62),
                            pt(-4, -47), 2)
        _NS_grimjaw._aaline(surface, p["blood_mid"], pt(-7, -61),
                            pt(-4, -48), 1)
        _NS_grimjaw._aaline(surface, p["blood_dark"], pt(8, -62),
                            pt(4, -47), 2)
        _NS_grimjaw._aaline(surface, p["blood_mid"], pt(7, -61),
                            pt(4, -48), 1)

        # Mata: socket angular + glow (blink saat idle)
        blink = (action == "idle" and math.sin(phase * 0.9 + 1.3) > 0.985)
        for ex in (-6, 6):
            # BUGFIX lama: poly() memakai pt() pada semua koordinat,
            # jadi ini WAJIB offset LOKAL (pusat mata di lokal -52).
            poly(p["dark_eye"], [(ex - f * 2, -55), (ex + f * 3, -54),
                 (ex + f * 2, -49), (ex - f * 3, -50)], False)
            x, y = pt(ex, -52)
            if blink and not eyes_glow:
                _NS_grimjaw._aaline(surface, p["mask_line"],
                                    (x - f * 2, y), (x + f * 2, y), 1)
            else:
                r = 2 if eyes_glow else 1
                _NS_grimjaw._aacircle(surface, eye_col, (x, y), r)
                if eyes_glow:
                    _NS_grimjaw._aacircle(surface, p["white"], (x - f, y - 1), 1)
        # Mouth grille: jaw line + teeth bars
        _NS_grimjaw._aaline(surface, p["shadow"], pt(-5, -39), pt(5, -39), 3)
        for tx in (-4, -1, 2, 4):
            _NS_grimjaw._aaline(surface, p["shadow"], pt(tx, -39),
                                pt(tx, -36), 2)
            _NS_grimjaw._aaline(surface, p["mask_light"], pt(tx, -39),
                                pt(tx, -38), 1)
        _NS_grimjaw._aaline(surface, p["mask_shadow"], pt(-6, -35),
                            pt(6, -35), 1)
        # snarl mark (scar)
        if detail:
            _NS_grimjaw._aaline(surface, p["mask_line"], pt(6, -45),
                                pt(9, -42), 1)

    # -------------------------------------------------------------------
    # Curved flame blade - pose-driven, 4 band + core + licks
    # -------------------------------------------------------------------
    def _draw_elite_flame_blade(surface, pt, f, grip, angle, length, phase,
                                detail, hot=False, omni=False):
        p = _NS_grimjaw.PALETTE
        s = math.sin(angle)
        c = math.cos(angle)
        segs = 6
        centers = []
        for i in range(segs + 1):
            t = i / segs
            curve = 11.0 * (t * t)
            centers.append((grip[0] + s * length * t + c * curve,
                            grip[1] + c * length * t - s * curve))
        n_x, n_y = c, -s
        left, right = [], []
        for i, (x, y) in enumerate(centers):
            t = i / segs
            wd = 5.5 * (1.0 - t) + 1.2 * t
            left.append((x + n_x * wd, y + n_y * wd))
            right.append((x - n_x * wd, y - n_y * wd))
        outline = left + right[::-1]

        grip_s = pt(*grip)

        def scr(p_local):
            return pt(*p_local)

        flat = [scr(o) for o in outline]
        _NS_grimjaw._poly(surface, p["shadow_deep"],
                          [(x + f, y + 1) for x, y in flat])
        _NS_grimjaw._poly(surface, p["fire_darkest"], flat)
        # Bright gradient of fire layers, shrinking toward the grip so the
        # blade stays a vivid orange flame instead of a dark silhouette.
        # hot (crit/omnislash): ramp didorong ke incandescent.
        mix = _NS_grimjaw._mix
        l1 = mix(p["fire_dark"], p["fire_light"], 0.55) if hot else p["fire_dark"]
        l2 = mix(p["fire_mid"], p["fire_hot"], 0.5) if hot else p["fire_mid"]
        l3 = mix(p["fire_light"], p["fire_core"], 0.5) if hot else p["fire_light"]
        for shrink, col in ((0.0, l1), (0.12, l2), (0.26, l3)):
            pts = []
            for (x, y) in flat:
                dx = (x - grip_s[0]) * shrink
                dy = (y - grip_s[1]) * shrink
                pts.append((int(x - dx), int(y - dy)))
            _NS_grimjaw._poly(surface, col, pts)
        # Hot core line (merah saat omnislash)
        core_col = p["rage_bright"] if omni else p["fire_hot"]
        core_in = p["white"] if hot else p["fire_core"]
        core = [scr(q) for q in centers]
        for i in range(len(core) - 1):
            _NS_grimjaw._aaline(surface, core_col, core[i], core[i + 1], 2)
            _NS_grimjaw._aaline(surface, core_in, core[i], core[i + 1], 1)
        # Leading-edge highlight
        edge = [scr(q) for q in left]
        for i in range(len(edge) - 1):
            _NS_grimjaw._aaline(surface, p["fire_hot"], edge[i],
                                edge[i + 1], 1)
            _NS_grimjaw._aaline(surface, p["white"], edge[i], edge[i + 1], 1)

        # Flickering flame licks shed from the convex edge
        flick = math.sin(phase * 3.1) * 2.0
        n_licks = 5 if hot else 4
        for i, t in enumerate((0.16, 0.38, 0.60, 0.80, 0.94)):
            if i >= 4 and not hot:
                continue
            ci = centers[int(t * segs)]
            lic = 5 + int((1.0 - t) * 7) + int(math.sin(phase * 4 + i) * 2)
            ex = ci[0] + n_x * (lic + flick)
            ey = ci[1] + n_y * (lic + flick)
            _NS_grimjaw._poly(surface, p["fire_dark"], [
                pt(ci[0] - n_x * 2, ci[1] - n_y * 2),
                pt(ci[0] + n_x * 2, ci[1] + n_y * 2),
                pt(ex, ey)])
            _NS_grimjaw._poly(surface, p["fire_light"], [
                pt(ci[0] - n_x * 1, ci[1] - n_y * 1),
                pt(ci[0] + n_x * 1, ci[1] + n_y * 1),
                pt(ex - n_x * 1, ey - n_y * 1)])
            _NS_grimjaw._aacircle(surface, p["fire_hot"],
                                  pt(ex, ey), 1)

        gx, gy = grip_s
        # Pommel (behind the hand, opposite the blade) + wrapped grip
        pommel = pt(grip[0] - s * 6, grip[1] - c * 6)
        _NS_grimjaw._aacircle(surface, p["gold_darkest"], pommel, 4)
        _NS_grimjaw._aacircle(surface, p["gold_dark"], pommel, 3)
        _NS_grimjaw._aacircle(surface, p["gold_light"], pommel, 1)
        for i in range(3):
            wx = gx - s * (1 + i * 3.2)
            wy = gy - c * (1 + i * 3.2)
            _NS_grimjaw._aacircle(surface, p["armor_darkest"],
                                  (int(wx), int(wy)), 4)
            _NS_grimjaw._aacircle(surface, p["armor_mid"],
                                  (int(wx - s * .8), int(wy - c * .8)), 2)
        # Crossguard: gold quillon bar
        for col, wd in ((p["gold_darkest"], 6), (p["gold_dark"], 4),
                        (p["gold_mid"], 2)):
            _NS_grimjaw._aaline(surface, col,
                                pt(grip[0] - n_x * 7, grip[1] - n_y * 7),
                                pt(grip[0] + n_x * 7, grip[1] + n_y * 7), wd)
        _NS_grimjaw._aacircle(surface, p["gold_light"],
                              pt(grip[0] + n_x * 7, grip[1] + n_y * 7), 1)
        _NS_grimjaw._aacircle(surface, p["gold_light"],
                              pt(grip[0] - n_x * 7, grip[1] - n_y * 7), 1)

        # Ember particles + hot core (banyak saat hot)
        pulse = math.sin(phase * 1.4) * 0.3 + 0.7
        tip = scr(centers[-1])
        n_embers = 5 if hot else 3
        for i in range(n_embers):
            t = (phase * 0.7 + i * 0.2) % 1.0
            ex = tip[0] + int(math.sin(phase * 5 + i) * 4)
            ey = tip[1] - int(t * 18)
            alpha = max(0, int(200 * (1.0 - t) * pulse))
            if alpha > 0:
                col = p["rage_bright"] if omni else p["fire_light"]
                _NS_grimjaw._aacircle(
                    surface, (*col, alpha), (ex, ey), 2)
                _NS_grimjaw._aacircle(
                    surface, (*p["fire_hot"], alpha), (ex, ey), 1)
        _NS_grimjaw._aacircle(surface, core_in, tip, 2)
        _NS_grimjaw._aacircle(surface, p["white"], tip, 1)

    # -------------------------------------------------------------------
    # Portrait-only LOD pass (extra material detail; arena LOD stays cheap)
    # -------------------------------------------------------------------
    def _draw_grimjaw_masterwork_details(surface, pt, poly, f, phase, action):
        p = _NS_grimjaw.PALETTE
        # serat mane (shine)
        for i in range(7):
            bx = -12 + i * 4
            by = -60
            tx = bx - 2 - int(math.sin(phase + i) * 2)
            ty = by - 16 - i
            _NS_grimjaw._aaline(surface, p["hair_shine"], pt(bx, by),
                                pt(tx, ty), 1)
        # crack mask halus
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(-7, -50),
                            pt(-3, -54), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(-3, -54),
                            pt(1, -47), 1)
        _NS_grimjaw._aaline(surface, p["mask_line"], pt(4, -58),
                            pt(8, -52), 1)
        # jahitan loincloth
        for i in range(3):
            yy = 16 + i * 5
            _NS_grimjaw._aaline(surface, p["cloth_stitch"],
                                pt(-3, yy), pt(3, yy), 1)
        # engraving pauldron
        for side in (-1, 1):
            _NS_grimjaw._aaline(surface, p["gold_engrave"],
                                pt(side * 14, -30), pt(side * 19, -31), 1)
            _NS_grimjaw._aaline(surface, p["gold_engrave"],
                                pt(side * 13, -26), pt(side * 18, -26), 1)
        _NS_grimjaw._aacircle(surface, p["gold_engrave"], pt(0, 11), 1)
        # seam sabuk
        for i in range(3):
            _NS_grimjaw._aaline(surface, p["armor_high"],
                                pt(-10 + i * 7, 9), pt(-7 + i * 7, 13), 1)
        # ember naik (portrait lebih kaya)
        for i in range(4):
            t = (phase * 0.35 + i / 4.0) % 1.0
            dx = -10 + i * 6 + int(math.sin(phase * 1.3 + i) * 2)
            dy = 14 - int(t * 60)
            _NS_grimjaw._aacircle(surface,
                                  (*p["ember"], int(180 * (1 - t))),
                                  pt(dx, dy), 1)

    # -------------------------------------------------------------------
    # Smear ayunan: crescent 3-band mengikuti jalur ujung pedang
    # -------------------------------------------------------------------
    def _draw_blade_swing_trail(surface, cx, cy, f, phase, ap):
        """Smear api 3-band: titik-titik di sepanjang posisi ujung pedang
        PADA progress sebelumnya (dihitung dari fungsi pose yang sama
        dengan rig), sehingga kepala smear SELALU menempel di pedang.
        """
        p = _NS_grimjaw.PALETTE
        steps = 10
        span = min(0.20, max(0.03, ap - _NS_grimjaw.ATTACK_WINDUP_END))
        fade = 1.0
        if ap > _NS_grimjaw.ATTACK_SWING_END:
            fade = max(0.0, 1.0 - (ap - _NS_grimjaw.ATTACK_SWING_END) / 0.30)
        if fade <= 0.01:
            return
        for i in range(steps):
            s = (i + 1) / steps
            p_back = ap - span * (1.0 - s)
            tipx, tipy = _NS_grimjaw._blade_tip_local(phase, "attack", p_back)
            ax = int(cx + tipx * f)
            ay = int(cy + tipy)
            taper = 0.30 + 0.70 * s
            alpha = int((40 + 200 * (s ** 1.6)) * fade)
            if alpha <= 0:
                continue
            base = 13
            _NS_grimjaw._aacircle(surface, (*p["fire_darkest"], alpha // 2),
                                  (ax, ay), max(1, int(base * taper)))
            _NS_grimjaw._aacircle(surface, (*p["fire_mid"], alpha),
                                  (ax, ay), max(1, int(base * taper * 0.62)))
            _NS_grimjaw._aacircle(surface, (*p["fire_light"], alpha),
                                  (ax, ay), max(1, int(base * taper * 0.36)))
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], alpha),
                                  (ax, ay), max(1, int(base * taper * 0.20)))
        # leading edge di posisi pedang sekarang
        tipx, tipy = _NS_grimjaw._blade_tip_local(phase, "attack", ap)
        hx, hy = int(cx + tipx * f), int(cy + tipy)
        for radius, col, al in ((16, "fire_dark", 110),
                                (11, "fire_mid", 170),
                                (7, "fire_light", 215),
                                (4, "fire_hot", 255)):
            _NS_grimjaw._aacircle(surface, (*p[col], int(al * fade)),
                                  (hx, hy), max(1, radius))
        _NS_grimjaw._aacircle(surface, (*p["white"], int(210 * fade)),
                              (hx, hy), max(1, int(2 * fade + 1)))

    # -------------------------------------------------------------------
    # Spin flame sweep (Blade Fury): cincin api berputar + ghost blade
    # -------------------------------------------------------------------
    def _draw_spin_flame_sweep(surface, cx, cy, f, spin_phase, phase):
        p = _NS_grimjaw.PALETTE
        # tiga cincin api selang-seling arah rotasi
        for k, (r0, spd, col) in enumerate(((52, 1.0, p["fire_mid"]),
                                            (42, -1.4, p["fire_light"]),
                                            (62, 0.7, p["fire_dark"]))):
            alpha = 150 - k * 30
            for i in range(7):
                a = spin_phase * spd + i * math.tau / 7
                px = int(cx + math.cos(a) * r0)
                py = int(cy - 4 + math.sin(a) * r0 * 0.62)
                _NS_grimjaw._aacircle(surface, (*p["fire_darkest"], alpha // 2),
                                      (px, py), 4)
                _NS_grimjaw._aacircle(surface, (*col, alpha), (px, py), 2)
                _NS_grimjaw._aacircle(surface, (*p["fire_hot"], alpha),
                                      (px, py), 1)
        # ghost blade di belakang putaran (2 posisi)
        for back, alpha in ((0.45, 70), (0.9, 40)):
            a_back = (spin_phase - back) * 0.5
            g = _NS_grimjaw._blade_grip_local("spin")
            L = _NS_grimjaw._blade_len("spin")
            s, c = math.sin(a_back), math.cos(a_back)
            x0 = int(cx + (g[0]) * f)
            y0 = int(cy + g[1])
            x1 = int(cx + (g[0] + s * L) * f)
            y1 = int(cy + g[1] + c * L)
            _NS_grimjaw._aaline(surface, (*p["fire_dark"], alpha),
                                (x0, y0), (x1, y1), 8)
            _NS_grimjaw._aaline(surface, (*p["fire_mid"], alpha),
                                (x0, y0), (x1, y1), 5)
            _NS_grimjaw._aaline(surface, (*p["fire_light"], alpha),
                                (x0, y0), (x1, y1), 2)
        # radial ember sparks
        for i in range(6):
            a = spin_phase + i * math.tau / 6
            t = (phase * 0.6 + i * 0.1667) % 1.0
            r = 24 + t * 34
            ex = int(cx + math.cos(a) * r)
            ey = int(cy - 4 + math.sin(a) * r * 0.62)
            alpha = int(210 * (1.0 - t))
            _NS_grimjaw._aacircle(surface, (*p["fire_dark"], alpha), (ex, ey), 2)
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], alpha), (ex, ey), 1)
        # spin shockwave: ring berdenyut di pinggang
        ring_t = (spin_phase % math.tau) / math.tau
        ring_r = int(26 + ring_t * 16)
        ring_alpha = int(150 * (1.0 - ring_t))
        _NS_grimjaw._aacircle(surface, (*p["fire_mid"], ring_alpha),
                              (int(cx), int(cy)), ring_r, 1)
        _NS_grimjaw._aacircle(surface, (*p["fire_hot"], ring_alpha),
                              (int(cx), int(cy)), max(1, ring_r - 3), 1)

    # ===================================================================
    # FLOATING EFFECTS (statis di-cache: dibangun SEKALI)
    # ===================================================================
    def _draw_fire_mist(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Orange fire mist beneath floating Grimjaw (base di-cache)."""
        p = _NS_grimjaw.PALETTE
        strength = 1.5 if intense else 1.0

        def build_mist():
            mist = pygame.Surface((170, 52), pygame.SRCALPHA)
            for radius in range(38, 4, -4):
                alpha = int((38 - radius) * 2.8)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*p["fire_dark"], min(255, alpha)),
                        (85 - radius * 2, 26 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            return mist
        mist = _NS_grimjaw._static("mist", build_mist)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        if pulse < .9:
            mist.set_alpha(int(255 * pulse))
            surface.blit(mist, (cx - 85, cy - 16))
            mist.set_alpha(255)
        else:
            surface.blit(mist, (cx - 85, cy - 16))

        # Rising fire wisps
        for i, offset in enumerate((-26, -10, 10, 26)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 4)
            sy = cy + 6 - int(t * 30)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_grimjaw._aacircle(surface, (*p["fire_darkest"], alpha), (sx, sy), 5)
            _NS_grimjaw._aacircle(surface, (*p["fire_dark"], alpha), (sx, sy - 1), 4)
            _NS_grimjaw._aacircle(surface, (*p["fire_mid"], alpha), (sx, sy - 2), 3)
            _NS_grimjaw._aacircle(surface, (*p["fire_light"], min(255, alpha)),
                                  (sx, sy - 3), 2)
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], min(255, alpha)),
                                  (sx, sy - 3), 1)

        # Orbiting fire embers
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 28 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_grimjaw._aacircle(surface, p["fire_dark"], (sx, sy), 3)
            _NS_grimjaw._aacircle(surface, p["fire_light"], (sx, sy), 2)
            _NS_grimjaw._aacircle(surface, p["fire_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_grimjaw._aacircle(surface, (*p["fire_mid"], alpha),
                                      (sx, sy), max(2, 5 - i))

    def _draw_shadow(surface, x, y):
        """Ground shadow (cached - dibangun sekali)."""
        def build():
            shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
            for radius in range(14, 0, -1):
                alpha = max(0, (14 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (14 - radius, 15 - radius, 122 + radius * 2, radius * 2))
            pygame.draw.ellipse(
                shadow, (*_NS_grimjaw.PALETTE["fire_darkest"], 50),
                (10, 6, 130, 14))
            return shadow
        surface.blit(_NS_grimjaw._static("shadow", build), (x - 75, y - 15))

    def _draw_fire_aura(surface, x, y, phase):
        """Large background fire aura (cached)."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75

        def build():
            aura = pygame.Surface((240, 220), pygame.SRCALPHA)
            for radius in range(90, 6, -5):
                alpha = int((90 - radius) * 1.0)
                if alpha > 0:
                    _NS_grimjaw._aacircle(
                        aura, (*_NS_grimjaw.PALETTE["fire_darkest"], min(255, alpha)),
                        (120, 110), radius)
            return aura
        aura = _NS_grimjaw._static("fire_aura", build)
        if pulse < .9:
            aura.set_alpha(int(255 * pulse))
            surface.blit(aura, (x - 120, y - 110))
            aura.set_alpha(255)
        else:
            surface.blit(aura, (x - 120, y - 110))

    def _draw_rage_aura(surface, x, y, phase):
        """Aura merah panas saat Omnislash aktif (cached)."""
        pulse = math.sin(phase * 0.8) * 0.3 + 0.7

        def build():
            aura = pygame.Surface((280, 260), pygame.SRCALPHA)
            for radius in range(105, 6, -5):
                alpha = int((105 - radius) * 1.3)
                if alpha > 0:
                    _NS_grimjaw._aacircle(
                        aura, (*_NS_grimjaw.PALETTE["rage_dark"], min(255, alpha)),
                        (140, 130), radius)
            return aura
        aura = _NS_grimjaw._static("rage_aura", build)
        aura.set_alpha(int(255 * pulse))
        surface.blit(aura, (x - 140, y - 130))
        aura.set_alpha(255)

    def _draw_fire_platform(surface, x, y, phase, skill):
        """Fire circle pattern on the ground (base cached)."""
        p = _NS_grimjaw.PALETTE
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75

        def build():
            ring = pygame.Surface((190, 58), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*p["fire_dark"], 150),
                                (6, 12, 178, 36), 3)
            pygame.draw.ellipse(ring, (*p["fire_mid"], 180),
                                (32, 19, 126, 22), 2)
            return ring
        ring = _NS_grimjaw._static("platform", build)
        surface.blit(ring, (x - 95, y - 29))

        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = x + int(math.cos(angle) * 26)
            y1 = y + int(math.sin(angle) * 5)
            x2 = x + int(math.cos(angle) * 70)
            y2 = y + int(math.sin(angle) * 12)
            pygame.draw.line(surface, (*p["fire_light"], 170),
                             (x1, y1), (x2, y2), 1)

        if skill:
            color = p["rage_light"] if skill == "r" else \
                (p["heal_light"] if skill == "w" else p["fire_hot"])
            pygame.draw.ellipse(surface, (*color, int(130 * pulse)),
                                (x - 78, y - 23, 156, 46), 2)

    # ===================================================================
    # BASIC ATTACK - FIRE SLASH ARC + IMPACT
    # ===================================================================
    def _draw_fire_slash_arc(surface, x, y, facing, progress, crit=False,
                             phase=0.0):
        """Fire slash crescent selama basic attack - ATAS -> BAWAH.

        v2: titik crescent dihitung dari posisi ujung pedang SEBENARNYA
        (fungsi pose yang sama dengan rig), jadi kepala crescent SELALU
        menempel di pedang dan ekornya memudar ke atas-belakang.
        """
        p0 = _NS_grimjaw.ATTACK_WINDUP_END - 0.02
        p1 = _NS_grimjaw.ATTACK_SWING_END
        if progress < p0 or progress > 0.92:
            return

        travel = (progress - p0) / (p1 - p0)
        travel = max(0.0, min(1.0, travel))
        travel = travel ** 1.35

        # Setelah tebasan selesai, crescent utuh memudar perlahan.
        fade = 1.0
        if progress > p1:
            fade = 1.0 - (progress - p1) / (0.92 - p1)
        fade = max(0.0, min(1.0, fade))
        if fade <= 0.0:
            return

        arc_scale = 1.25 if crit else 1.0
        p = _NS_grimjaw.PALETTE
        steps = 16
        for i in range(steps):
            s = (i + 1) / steps          # 0 = ekor (atas), 1 = kepala (depan-bawah)
            p_back = p0 + (progress - p0) * (1.0 - s)
            tipx, tipy = _NS_grimjaw._blade_tip_local(phase, "attack", p_back)
            arc_x = int(x + tipx * (1 if facing >= 0 else -1))
            arc_y = int(y + tipy)
            # Alpha & ketebalan membesar ke arah kepala crescent.
            taper = 0.35 + 0.65 * (s ** 1.7)
            alpha = min(255, max(0, int((30 + 225 * (s ** 1.6)) * fade)))
            if alpha <= 0:
                continue
            base = 11 if crit else 10

            _NS_grimjaw._aacircle(surface, (*p["fire_darkest"], alpha // 2),
                                  (arc_x, arc_y), max(1, int(base * taper)))
            _NS_grimjaw._aacircle(surface, (*p["fire_dark"], alpha),
                                  (arc_x, arc_y), max(1, int(base * taper * 0.78)))
            _NS_grimjaw._aacircle(surface, (*p["fire_mid"], alpha),
                                  (arc_x, arc_y), max(1, int(base * taper * 0.58)))
            _NS_grimjaw._aacircle(surface, (*p["fire_light"], alpha),
                                  (arc_x, arc_y), max(1, int(base * taper * 0.40)))
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], alpha),
                                  (arc_x, arc_y), max(1, int(base * taper * 0.24)))

        # Nyala di kepala crescent (ujung pedang saat ini)
        tipx, tipy = _NS_grimjaw._blade_tip_local(phase, "attack", progress)
        hx = int(x + tipx * (1 if facing >= 0 else -1))
        hy = int(y + tipy)
        head_a = fade * (0.5 + 0.5 * travel)
        for radius, col, al in ((17, "fire_dark", 110),
                                (12, "fire_mid", 170),
                                (8, "fire_light", 215),
                                (4, "fire_hot", 255)):
            _NS_grimjaw._aacircle(surface, (*p[col], int(al * head_a)),
                                  (hx, hy), max(1, int(radius * arc_scale)))
        _NS_grimjaw._aacircle(surface, (*p["white"], int(200 * head_a)),
                              (hx, hy), max(1, int(2 * arc_scale)))

    def _draw_impact_flash(surface, x, y, facing, progress, crit=False):
        """Bright hit-pop + shockwave ring when the blade connects.

        v2: titik benturan = posisi pendaratan ujung pedang rig v2
        (depan-bawah, x=+86), waktu = sekitar ATTACK_SWING_END.
        """
        p = _NS_grimjaw.PALETTE
        if progress < 0.48 or progress > 0.84:
            return
        t = (progress - 0.48) / 0.36
        t = max(0.0, min(1.0, t))
        intensity = math.sin(math.pi * (t ** 0.75))

        tip_x = x + (86 if crit else 82) * facing
        tip_y = y + (44 if crit else 42)

        # Shockwave ring expanding outward
        ring_r = int(5 + intensity * (26 if crit else 20))
        _NS_grimjaw._aacircle(surface, (*p["fire_dark"], int(140 * intensity)),
                              (tip_x, tip_y), ring_r, 2)
        _NS_grimjaw._aacircle(surface, (*p["fire_hot"], int(180 * intensity)),
                              (tip_x, tip_y), max(1, ring_r - 3), 1)

        # Central flash
        for radius, color, alpha in ((16, "fire_dark", 90),
                                     (11, "fire_mid", 160),
                                     (6, "fire_light", 220),
                                     (3, "fire_hot", 255)):
            _NS_grimjaw._aacircle(surface, (*p[color], int(alpha * intensity)),
                                  (tip_x, tip_y), radius)
        _NS_grimjaw._aacircle(surface, p["fire_core"], (tip_x, tip_y),
                              max(1, int(3 * intensity)))
        _NS_grimjaw._aacircle(surface, p["white"], (tip_x, tip_y),
                              max(1, int(2 * intensity)))

        # Radial spark streaks
        for i in range(6):
            angle = (i * math.pi / 3) + progress * 2.0
            r0 = int(7 * intensity)
            r1 = int((18 if crit else 14) * intensity)
            sx = tip_x + int(math.cos(angle) * r0)
            sy = tip_y + int(math.sin(angle) * r0)
            ex = tip_x + int(math.cos(angle) * r1)
            ey = tip_y + int(math.sin(angle) * r1)
            _NS_grimjaw._aaline(surface,
                                (*p["fire_hot"], int(220 * intensity)),
                                (sx, sy), (ex, ey), 1)

        # Serpihan batu (deterministik) - frame IMPACT
        if 0.05 < t < 0.6:
            st = t / 0.6
            for i in range(5):
                a = 0.6 + i * 0.55 + _NS_grimjaw._hash01(i * 3) * 0.5
                r = int((10 + st * 34) * (1 if facing >= 0 else 1))
                dx = int(math.cos(a) * r) * facing
                dy = int(math.sin(a) * r * 0.6) + int(st * st * 10)
                al = int(200 * (1 - st))
                _NS_grimjaw._poly(surface, (*p["metal_dark"], al), [
                    (tip_x + dx, tip_y + dy - 3),
                    (tip_x + dx + 3, tip_y + dy),
                    (tip_x + dx, tip_y + dy + 3)])
                _NS_grimjaw._poly(surface, (*p["metal_light"], al), [
                    (tip_x + dx, tip_y + dy - 1),
                    (tip_x + dx + 2, tip_y + dy),
                    (tip_x + dx, tip_y + dy + 1)])

    def _draw_critical_strike_burst(surface, x, y, facing, progress):
        """Critical strike burst effect - extra sparkle (di titik pendaratan)."""
        p = _NS_grimjaw.PALETTE
        burst_x = x + 70 * facing
        burst_y = y + 40

        t = (progress - 0.56) / 0.26
        t = max(0.0, min(1.0, t))

        # 4-pointed star burst
        star_r = int(7 + t * 18)
        alpha = int(255 * (1 - t))

        for angle_deg in (0, 45, 90, 135):
            angle = math.radians(angle_deg)
            ox1 = burst_x + int(math.cos(angle) * star_r)
            oy1 = burst_y + int(math.sin(angle) * star_r)
            ox2 = burst_x - int(math.cos(angle) * star_r)
            oy2 = burst_y - int(math.sin(angle) * star_r)

            _NS_grimjaw._aaline(surface, (*p["fire_dark"], alpha),
                                (ox1, oy1), (ox2, oy2), 4)
            _NS_grimjaw._aaline(surface, (*p["fire_light"], alpha),
                                (ox1, oy1), (ox2, oy2), 2)
            _NS_grimjaw._aaline(surface, (*p["fire_hot"], alpha),
                                (ox1, oy1), (ox2, oy2), 1)

        # Central bright core
        core_alpha = int(255 * (1 - t))
        _NS_grimjaw._aacircle(surface, (*p["fire_light"], core_alpha),
                              (burst_x, burst_y), 5)
        _NS_grimjaw._aacircle(surface, (*p["fire_hot"], core_alpha),
                              (burst_x, burst_y), 3)
        _NS_grimjaw._aacircle(surface, p["fire_core"], (burst_x, burst_y),
                              max(1, int(2 + (1 - t))))

        # sparkles orbit
        for i in range(6):
            angle = i * math.pi / 3 + progress * 5
            dist = 26 + int(math.sin(progress * 8 + i) * 5)
            px = burst_x + int(math.cos(angle) * dist)
            py = burst_y + int(math.sin(angle) * dist)
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], alpha), (px, py), 2)
            _NS_grimjaw._aacircle(surface, p["white"], (px, py), 1)

    # ===================================================================
    # SKILL Q: BLADE FURY (spin AOE, 180 frame)
    # ===================================================================
    def _draw_blade_fury_ground(surface, hero, x, y, timer, phase):
        """Telegraph + steady ground Blade Fury (world-space, v3).

        Ring jangkauan = skill_range (70 dunia) dikonversi ke px canvas
        lewat _render_scale supaya pas dengan AOE gameplay.  Layer:
        dither disk tanah -> rim ganda presisi -> sigil rune berputar ->
        ring konvergen "incoming" -> chevron kardinal -> nova burst saat
        aktivasi -> retakan radial (jagged) -> push ring ganda -> orb
        pusat berdenyut.  Aktivasi: pilar api 4-lapis + shockwave ganda +
        spark star.
        """
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("q", timer)
        steady = _NS_grimjaw._skill_steady(progress)
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        fs = _NS_grimjaw._fx_scale(hero)
        gy = y + 58

        spin_range = int(getattr(hero, "skill_range", 70) or 70)
        rng = _NS_grimjaw._ring_r(hero, spin_range, surface)
        fire_ramp = (p["fire_light"], p["fire_mid"], p["fire_hot"])

        # ── AKTIVASI: pilar api 4-lapis + spark star + nova (tanpa lingkaran) ──
        if progress < 0.16:
            t = progress / 0.16
            top = int(y - min(150 * fs, 260) * (0.55 + 0.45 * (1 - t)))
            for wd, col, al in ((30, p["fire_darkest"], 95),
                                (18, p["fire_dark"], 145),
                                (8, p["fire_mid"], 205),
                                (3, p["fire_hot"], 245)):
                _NS_grimjaw._aaline(surface, (*col, int(al * (1 - t))),
                                    (x, top), (x, y), max(1, int(wd * fs * .4)))
            _NS_grimjaw._spark_star(surface, x, y, int(34 * (1 - t * .5)),
                                    p["fire_hot"], int(245 * (1 - t)),
                                    10, rot=phase, core=p["white"])
            _NS_grimjaw._nova(surface, x, y, int(8 * fs),
                              int((40 + 70 * t) * fs), 8, phase * .2,
                              (p["fire_light"], p["fire_dark"]),
                              int(215 * (1 - t)))
            # burst radial pendek (pengganti shockwave bulat)
            for k in range(6):
                a = phase + k * math.pi / 3
                rl = int((26 + t * (70 * fs)) * (1 if k % 2 else .62))
                ca, sa = math.cos(a), math.sin(a)
                _NS_grimjaw._aaline(surface, (*p["fire_hot"], int(210 * (1 - t))),
                                    (x, y), (x + ca * rl, y + sa * rl * .7), 2)

        # ── STEADY: dither disk tanah + marker AOE bersudut ──
        _NS_grimjaw._dither_disk(surface, x, gy, int(rng * .62), int(rng * .2),
                                 p["fire_darkest"],
                                 int((70 + 40 * pulse) * steady),
                                 phase=phase, seed=13)
        _NS_grimjaw._ellipse(surface, (*p["fire_darkest"], int(90 + 40 * pulse)),
                             (int(x - rng * 0.55), int(gy - rng * 0.16),
                              int(rng * 1.1), int(rng * 0.32)), 0)
        # marker perimeter (bracket + tick, bukan cincin)
        _NS_grimjaw._aoe_marks(surface, x, y, rng, p["fire_light"],
                               int(130 + 55 * pulse), phase,
                               ticks=16, tick_len=max(8, int(rng * .12)))
        _NS_grimjaw._aoe_marks(surface, x, y, max(6, rng - int(6 * fs)),
                               p["fire_hot"], int(105 + 45 * pulse), -phase,
                               ticks=12, corner=False,
                               tick_len=max(6, int(rng * .07)))
        # rune glyph menyebar (bukan sigil ring) — angular, deterministik
        for i in range(8):
            a = i * math.tau / 8
            gx = x + math.cos(a) * rng * 0.72
            gy = gy + math.sin(a) * rng * 0.34
            _NS_grimjaw._rune_glyph(surface, int(gx), int(gy),
                                    max(3, int(4.6 * fs)), i + int(phase * 2),
                                    fire_ramp[i % 2],
                                    int(120 * steady), rot=a + math.pi / 2)
        # retakan api radial (5, deterministik)
        for i in range(5):
            ang = i * math.tau / 5 + 0.4
            _NS_grimjaw._jagged_crack(surface, x, gy, ang,
                                      int((24 + (i % 3) * 9) * fs),
                                      (p["fire_darkest"], p["fire_mid"]),
                                      int(145 * steady), seed=i + 51, width=2)
        # ring konvergen: tick mengarah ke dalam (telegraph "incoming")
        conv = max(12, int(rng * (1 - (progress % .28) * 3.2)))
        _NS_grimjaw._aoe_marks(surface, x, y, conv, p["fire_hot"],
                               int(160 + 70 * pulse), phase,
                               ticks=10, corner=False, inner=True,
                               tick_len=max(6, int(conv * .12)))
        # chevron kardinal menunjuk ke dalam
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _NS_grimjaw._chevron(
                surface,
                x + math.cos(da) * rng * 0.62,
                y + math.sin(da) * rng * 0.55,
                da + math.pi, max(9, int(rng * 0.11)), p["fire_light"],
                int(190 * steady), 3)
        # orb pusat berdenyut + ember orbit
        _NS_grimjaw._draw_glow_orb(surface, x, y, int(6 + 3 * pulse),
                                   (p["fire_dark"], p["fire_mid"], p["fire_hot"]),
                                   int(200 + 45 * pulse))
        _NS_grimjaw._orbit_glints(surface, x, y, int(rng * .5), int(rng * .2),
                                  phase * 1.6, 6, p["fire_light"],
                                  int(130 * steady), hot=p["fire_hot"])

    def _draw_blade_fury_rings(surface, x, y, phase):
        """Fire rings spinning around character during Blade Fury (v3).

        Tiga cincin api elips selang-seling arah + trailing ember; setiap
        titik memakai ban warna hangat (darkest->hot) sehingga terbaca
        sebagai piringan api berputar, bukan titik-titik kosong.
        """
        p = _NS_grimjaw.PALETTE
        ring_specs = ((34, 3, p["fire_darkest"]), (43, -1.5, p["fire_dark"]),
                      (52, 1.1, p["fire_mid"]))
        for ring_i, (ring_radius, spin_dir, base_col) in enumerate(ring_specs):
            ring_phase = phase * 3 * spin_dir + ring_i * 2.1
            for i in range(14):
                angle = ring_phase + i * math.tau / 14
                px = x + int(math.cos(angle) * ring_radius)
                py = y + int(math.sin(angle) * ring_radius * 0.42)
                # trailing ember (semakin dekat ke belakang semakin redup)
                trail_ang = angle - 0.22
                tx = x + int(math.cos(trail_ang) * ring_radius)
                ty = y + int(math.sin(trail_ang) * ring_radius * 0.42)
                _NS_grimjaw._aacircle(surface, (*base_col, 150),
                                      (tx, ty), 3 if i % 2 else 2)
                _NS_grimjaw._aacircle(surface, p["fire_hot"], (px, py), 2)
                _NS_grimjaw._aacircle(surface, p["fire_light"], (px, py), 1)
        # arc-rim elips tipis di pinggang (3 band, blur-nya api)
        _NS_grimjaw._arc_band(surface, x, y + 4, 58, 22, phase,
                              phase + math.pi * 1.3, p["fire_light"], 90, 1, 22)
        _NS_grimjaw._arc_band(surface, x, y + 4, 45, 17, -phase * 1.4,
                              -phase * 1.4 + math.pi * 1.2, p["fire_dark"], 70, 1, 18)

    def _draw_fire_particles_orbit(surface, x, y, phase):
        """Fire particles orbiting during spinning (v3)."""
        p = _NS_grimjaw.PALETTE
        for i in range(16):
            p_phase = phase * 4 + i * 0.5
            p_angle = p_phase
            p_dist = 34 + int(math.sin(p_phase * 2) * 12)
            px = x + int(math.cos(p_angle) * p_dist)
            py = y + int(math.sin(p_angle) * p_dist * 0.5)
            # inti partikel + ekor (garis pendek ke arah gerak orbit)
            lead_ang = p_angle + 0.5
            tx = x + int(math.cos(lead_ang) * (p_dist - 7))
            ty = y + int(math.sin(lead_ang) * (p_dist - 7) * 0.5)
            _NS_grimjaw._aaline(surface, (*p["fire_dark"], 120),
                                (tx, ty), (px, py), 1)
            _NS_grimjaw._aacircle(surface, p["fire_dark"], (px, py), 3 if i % 3 else 2)
            _NS_grimjaw._aacircle(surface, p["fire_hot"], (px, py), 2)
            _NS_grimjaw._aacircle(surface, p["fire_core"], (px, py), 1)

    # ===================================================================
    # SKILL W: HEALING WARD (visual 90 frame)
    # ===================================================================
    def _draw_healing_ward_ground(surface, hero, x, y, timer, phase):
        """Ground layer of healing ward (world-space, v3).

        Ring jangkauan = radius heal 100 dunia, dikonversi lewat
        _render_scale.  Layer: dither disk hijau -> rim ganda presisi ->
        sigil rune penyembuh berputar -> dashed ring -> ring konvergen
        telegraph -> orbit cross motes -> glow orb pusat.  Aktivasi:
        shockwave hijau + spark star + nova petal penyembuh.
        """
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("w", timer)
        steady = _NS_grimjaw._skill_steady(progress)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        fs = _NS_grimjaw._fx_scale(hero)
        rng = _NS_grimjaw._ring_r(hero, 100, surface)
        gy = y + 58
        heal_ramp = (p["heal_light"], p["heal_mid"], p["heal_core"])

        # ── AKTIVASI: burst radial + bintang + nova (tanpa lingkaran) ──
        if progress < 0.18:
            t = progress / 0.18
            # burst radial pendek (pengganti shockwave bulat)
            for k in range(6):
                a = phase * .5 + k * math.pi / 3
                rl = int((26 + t * (70 * fs)) * (1 if k % 2 else .62))
                ca, sa = math.cos(a), math.sin(a)
                _NS_grimjaw._aaline(
                    surface, (*p["heal_light"], int(215 * (1 - t))),
                    (x, y), (x + ca * rl, y + sa * rl * .7), 2)
            _NS_grimjaw._spark_star(surface, x, y, int(28 * (1 - t * .5)),
                                    p["heal_light"], int(240 * (1 - t)),
                                    8, rot=phase, core=p["heal_core"])
            _NS_grimjaw._nova(surface, x, y, int(6 * fs),
                              int((36 + 60 * t) * fs), 8, phase * .3,
                              (p["heal_light"], p["heal_dark"]),
                              int(200 * (1 - t)))

        # ── STEADY: dither disk + marker AOE bersudut + rune menyebar ──
        _NS_grimjaw._dither_disk(surface, x, gy, int(rng * .5), int(rng * .2),
                                 p["heal_darkest"],
                                 int((55 + 30 * pulse) * steady),
                                 phase=phase, seed=17)
        _NS_grimjaw._ellipse(surface, (*p["heal_darkest"], int(80 + 30 * pulse)),
                             (int(x - rng * 0.55), int(gy - rng * 0.15),
                              int(rng * 1.1), int(rng * 0.30)), 0)
        # marker perimeter (bracket + tick, bukan cincin)
        _NS_grimjaw._aoe_marks(surface, x, y, rng, p["heal_mid"],
                               int(125 + 55 * pulse), phase,
                               ticks=16, tick_len=max(8, int(rng * .12)))
        _NS_grimjaw._aoe_marks(surface, x, y, max(6, rng - int(6 * fs)),
                               p["heal_light"], int(105 + 45 * pulse), -phase,
                               ticks=12, corner=False,
                               tick_len=max(6, int(rng * .07)))
        # rune glyph menyebar (bukan sigil ring) — angular, deterministik
        for i in range(8):
            a = i * math.tau / 8
            gx = x + math.cos(a) * rng * 0.72
            gy = gy + math.sin(a) * rng * 0.34
            _NS_grimjaw._rune_glyph(surface, int(gx), int(gy),
                                    max(3, int(4.6 * fs)), i + int(phase * 2),
                                    heal_ramp[i % 2],
                                    int(120 * steady), rot=a + math.pi / 2)
        # ring konvergen: tick mengarah ke dalam (telegraph awal)
        if progress < 0.4:
            t = progress / 0.4
            conv = max(12, int(rng * (1 - t * 0.75)))
            _NS_grimjaw._aoe_marks(surface, x, y, conv, p["heal_light"],
                                   int(180 * (1 - t) + 60), phase,
                                   ticks=10, corner=False, inner=True,
                                   tick_len=max(6, int(conv * .12)))
        # orbit cross motes
        _NS_grimjaw._orbit_glints(surface, x, y, int(rng * .56), int(rng * .2),
                                  -phase * 1.1, 8, p["heal_mid"],
                                  int(120 * steady), hot=p["heal_light"])
        # glow orb pusat
        _NS_grimjaw._draw_glow_orb(surface, x, y, int(6 + 3 * pulse),
                                   (p["heal_dark"], p["heal_mid"], p["heal_light"]),
                                   int(150 + 60 * pulse))

    def _draw_healing_ward_totem(surface, hero, x, y, timer, phase):
        """Green healing totem beside Grimjaw + pilar cahaya aktivasi (v3)."""
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("w", timer)
        facing = getattr(hero, "direction", 1)
        fs = _NS_grimjaw._fx_scale(hero)
        wx = x + int(52 * fs * (1 if facing >= 0 else -1))
        wy = y + int(34 * fs)
        green_ramp = (p["heal_darkest"], p["heal_mid"], p["heal_light"],
                      p["heal_core"])

        # ── AKTIVASI: pilar cahaya 4-lapis + bintang + nova ──
        if progress < 0.2:
            t = progress / 0.2
            top = wy - int(min(120 * fs, 250) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((28, p["heal_dark"], 100),
                                (17, p["heal_mid"], 150),
                                (8, p["heal_light"], 210),
                                (3, p["heal_core"], 245)):
                _NS_grimjaw._aaline(surface, (*col, int(al * (1 - t))),
                                    (wx, int(top)), (wx, wy), max(1, int(wd * fs * .4)))
            _NS_grimjaw._spark_star(surface, wx, wy, int(24 * (1 - t * .5)),
                                    p["heal_light"], int(235 * (1 - t)),
                                    8, rot=phase, core=p["heal_core"])
            _NS_grimjaw._nova(surface, wx, wy, int(5 * fs),
                              int((30 + 48 * t) * fs), 6, phase * .4,
                              (p["heal_light"], p["heal_dark"]),
                              int(190 * (1 - t)))

        # Base (stone 3 band)
        _NS_grimjaw._rect(surface, p["shadow"], (wx - 8, wy + 8, 16, 6))
        _NS_grimjaw._rect(surface, (72, 48, 36), (wx - 8, wy + 7, 16, 6), border_radius=1)
        _NS_grimjaw._rect(surface, (112, 78, 56), (wx - 7, wy + 7, 14, 5), border_radius=1)
        _NS_grimjaw._rect(surface, (152, 108, 82), (wx - 6, wy + 7, 12, 3))
        # Pole (dark wood + binding)
        _NS_grimjaw._rect(surface, p["armor_darkest"], (wx - 3, wy - 8, 6, 16))
        _NS_grimjaw._rect(surface, p["armor_dark"], (wx - 3, wy - 8, 5, 16))
        _NS_grimjaw._rect(surface, p["armor_mid"], (wx - 2, wy - 8, 3, 14))
        for band_y in (wy - 4, wy + 3):
            _NS_grimjaw._rect(surface, p["gold_dark"], (wx - 4, band_y, 8, 1))
            _NS_grimjaw._rect(surface, p["gold_mid"], (wx - 4, band_y, 6, 1))
        pulse = math.sin(phase) * 0.3 + 0.7

        def build_glow():
            glow = pygame.Surface((44, 44), pygame.SRCALPHA)
            for r in range(18, 0, -1):
                alpha = min(255, max(0, int(150 - r * 8)))
                if alpha > 0:
                    pygame.draw.circle(glow, (*p["heal_mid"], alpha), (22, 22), r)
            return glow
        glow = _NS_grimjaw._static("heal_glow", build_glow)
        glow.set_alpha(int(160 + 80 * pulse))
        surface.blit(glow, (wx - 22, wy - 12 - 22))
        glow.set_alpha(255)

        # Orb: crystal shard faset (bukan bulat polos) + core + glint
        _NS_grimjaw._crystal_shard(surface, wx, wy - 12, int(5 * fs),
                                   int(13 * fs), math.pi * .5, green_ramp,
                                   int(230 * pulse), glint=1)
        _NS_grimjaw._aacircle(surface, p["heal_darkest"], (wx, wy - 12), 8)
        _NS_grimjaw._aacircle(surface, p["heal_mid"], (wx - 1, wy - 13), 5)
        _NS_grimjaw._aacircle(surface, p["heal_light"], (wx - 1, wy - 13), 4)
        _NS_grimjaw._rect(surface, p["heal_core"], (wx - 1, wy - 13, 2, 2))
        _NS_grimjaw._rect(surface, p["white"], (wx - 1, wy - 13, 1, 1))
        # rune ring kecil + glint orbit
        _NS_grimjaw._sigil_ring(surface, wx, wy - 14, int(15 * fs), phase * 1.4,
                                (p["heal_light"], p["heal_mid"], p["heal_core"]),
                                int(170 * pulse), n=6, squash=.6, seed=33,
                                size=max(2, int(3 * fs)))
        _NS_grimjaw._orbit_glints(surface, wx, wy - 12, int(13 * fs),
                                  int(12 * fs), phase * 2.2, 4,
                                  p["heal_light"], int(190 * pulse),
                                  hot=p["heal_core"])

        # Floating + heal symbols (cross naik)
        for i in range(4):
            sym_phase = phase * 2 + i * 1.5
            sym_y_offset = int((sym_phase * 3) % 16)
            sym_alpha = min(255, max(0, 220 - sym_y_offset * 14))
            if sym_alpha > 0:
                sym_x = wx + int(math.sin(sym_phase) * 6)
                sym_y = wy - 16 - sym_y_offset
                _NS_grimjaw._rect(surface, (*p["heal_light"], sym_alpha),
                                  (sym_x - 1, sym_y - 4, 2, 9))
                _NS_grimjaw._rect(surface, (*p["heal_light"], sym_alpha),
                                  (sym_x - 4, sym_y - 1, 9, 2))

    def _draw_heal_aura(surface, x, y, phase):
        """Heal aura around Grimjaw when Healing Ward active (cached, v3)."""
        p = _NS_grimjaw.PALETTE
        pulse = math.sin(phase) * 0.3 + 0.7

        def build():
            aura = pygame.Surface((130, 130), pygame.SRCALPHA)
            for r in range(56, 20, -3):
                alpha = min(255, max(0, int((56 - r) * 4)))
                if alpha > 0:
                    pygame.draw.circle(aura, (*p["heal_mid"], alpha),
                                       (65, 65), r, 2)
            return aura
        aura = _NS_grimjaw._static("heal_aura", build)
        aura.set_alpha(int(150 + 70 * pulse))
        surface.blit(aura, (x - 65, y - 65))
        aura.set_alpha(255)

        # Ground ring particles (cross + sparkle)
        for i in range(14):
            angle = i * math.pi / 7 + phase
            rx = x + int(math.cos(angle) * 44)
            ry = y + int(math.sin(angle) * 16) + 24
            _NS_grimjaw._aacircle(surface, p["heal_light"], (rx, ry), 2 if i % 2 else 1)
            _NS_grimjaw._rect(surface, p["heal_core"], (rx, ry, 1, 1))
            # ekor energi pendek
            _NS_grimjaw._aaline(surface, (*p["heal_mid"], 150),
                                (rx, ry), (rx + int(math.cos(angle) * 8), ry), 1)

        # Rising + symbols around body
        for i in range(7):
            phase_i = (phase * 1.5 + i * 0.3) % 1.0
            angle = i * math.pi / 3.5
            px = x + int(math.cos(angle) * 30)
            py = y + 24 - int(phase_i * 52)
            alpha = int(220 * (1 - phase_i))
            if alpha > 0:
                _NS_grimjaw._rect(surface, (*p["heal_light"], alpha),
                                  (px - 1, py - 4, 2, 9))
                _NS_grimjaw._rect(surface, (*p["heal_light"], alpha),
                                  (px - 4, py - 1, 9, 2))
        # orbit glints mengelilingi badan
        _NS_grimjaw._orbit_glints(surface, x, y - 10, 34, 40, phase * 1.3, 5,
                                  p["heal_mid"], int(110 + 60 * pulse),
                                  hot=p["heal_core"])

    # ===================================================================
    # SKILL E: CRITICAL STRIKE (buff 60 frame visual)
    # ===================================================================
    def _draw_crit_telegraph(surface, hero, x, y, timer, phase):
        """Telegraph Critical Strike (world-space, v3): cone 60 dunia di
        arah hadap + chevron berbaris + retakan + dither disk + orb di
        ujung cone (posisi pendaratan)."""
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("e", timer)
        if progress > 0.5:
            return
        facing = getattr(hero, "direction", 1)
        fs = _NS_grimjaw._fx_scale(hero)
        pulse = math.sin(phase * 6) * 0.5 + 0.5
        fade = 1.0 - progress / 0.5
        gy = y + 56
        rage_ramp = (p["rage_light"], p["rage_mid"], p["rage_bright"])

        # dither disk tanah di area cone
        rng = _NS_grimjaw._ring_r(hero, 60, surface)
        ox = int(x + rng * 0.55 * (1 if facing >= 0 else -1))
        _NS_grimjaw._dither_disk(surface, ox, gy, int(rng * .5), int(rng * .14),
                                 p["rage_dark"], int(90 * fade * pulse),
                                 phase=phase, seed=21)
        # ellipse cone di depan
        _NS_grimjaw._ellipse(surface, (*p["fire_darkest"], int(120 * fade * pulse)),
                             (int(ox - rng * 0.55), int(gy - rng * 0.14),
                              int(rng * 1.1), int(rng * 0.28)), 0)
        # marker AOE bersudut di ujung cone (bukan cincin)
        _NS_grimjaw._aoe_marks(surface, ox, y, rng, p["fire_light"],
                               int(140 * fade * pulse + 40), phase,
                               ticks=12, tick_len=max(8, int(rng * .1)),
                               corner=False)
        # arc-rim cone depan
        _NS_grimjaw._arc_band(surface, ox, y, int(rng * .9), int(rng * .34),
                              -1.1, 1.1, p["fire_hot"], int(120 * fade * pulse),
                              2, 16)
        # chevron berbaris menuju depan
        for i in range(4):
            t = (i / 4 + phase * 0.5) % 1.0
            _NS_grimjaw._chevron(surface,
                                 x + facing * rng * (0.25 + 0.66 * t),
                                 y + 8, 0.0 if facing > 0 else math.pi,
                                 15, p["fire_hot"], int(210 * fade), 3)
        # retakan api di tanah (deterministik)
        for i in range(6):
            ang = (0.28 + i * 0.42) * (1 if facing > 0 else -1)
            _NS_grimjaw._jagged_crack(
                surface, x + facing * 18, gy, ang,
                int((22 + (i % 3) * 9) * fs),
                (p["fire_darkest"], p["fire_mid"]), int(160 * fade),
                seed=i + 21, width=2)
        # orb pendaratan (glow + nova tip) di ujung cone
        _NS_grimjaw._draw_glow_orb(surface, ox, y + 4, int(8 * fs),
                                   rage_ramp, int(170 * fade * pulse))
        _NS_grimjaw._nova(surface, ox, y + 4, int(4 * fs), int(16 * fs), 8,
                          phase * .5, (p["fire_hot"], p["fire_dark"]),
                          int(120 * fade * pulse))

    def _draw_crit_steady(surface, hero, x, y, timer, phase):
        """Steady Critical Strike (v3): glint orbit di blade, rune ring
        merah, sigil ring badan, mote bara + energy arc naik — blade di
        badan sudah menyala incandescent (kwarg crit)."""
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("e", timer)
        fs = _NS_grimjaw._fx_scale(hero)
        facing = getattr(hero, "direction", 1)
        pulse = math.sin(phase * 5) * 0.5 + 0.5
        rage_ramp = (p["rage_light"], p["rage_mid"], p["rage_bright"])

        # AKTIVASI: bintang + shockwave + nova
        if progress < 0.15:
            t = progress / 0.15
            tipx, tipy = _NS_grimjaw._blade_tip_local(0.0, "idle", 0.0)
            hx, hy = int(x + tipx * facing), int(y + tipy)
            _NS_grimjaw._spark_star(surface, hx, hy, int(26 * (1 - t * .4)),
                                    p["fire_hot"], int(240 * (1 - t)),
                                    9, rot=phase, core=p["white"])
            # burst radial pendek (pengganti shockwave bulat)
            for k in range(6):
                a = phase + k * math.pi / 3
                rl = int((16 + t * int(80 * fs)) * (1 if k % 2 else .6))
                ca, sa = math.cos(a), math.sin(a)
                _NS_grimjaw._aaline(
                    surface, (*p["fire_light"], int(200 * (1 - t))),
                    (hx, hy), (hx + ca * rl, hy + sa * rl * .7), 2)
            _NS_grimjaw._nova(surface, hx, hy, int(5 * fs),
                              int((26 + 40 * t) * fs), 8, phase * .4,
                              (p["fire_hot"], p["rage_dark"]),
                              int(200 * (1 - t)))
            return

        # glint orbit mengelilingi blade (4 titik + energy arc)
        tipx, tipy = _NS_grimjaw._blade_tip_local(0.0, "idle", 0.0)
        hx, hy = int(x + tipx * facing), int(y + tipy)
        _NS_grimjaw._orbit_glints(surface, hx, hy, 20, 20, phase * 3.0, 4,
                                  p["fire_hot"], int(200 + 40 * pulse),
                                  hot=p["white"])
        _NS_grimjaw._energy_arc(surface, x, y - 12, hx, hy, 5,
                                p["fire_light"], int(110 + 60 * pulse),
                                width=1, wobble=4.5)
        # rune ring + sigil => marker angular + rune glyph di sekeliling badan
        _NS_grimjaw._aoe_marks(surface, x, y - 6, int(52 * fs),
                               p["rage_mid"], int(120 + 60 * pulse), -phase * 1.3,
                               ticks=10, corner=False, tick_len=max(6, int(52 * fs * .1)))
        _NS_grimjaw._aoe_marks(surface, x, y - 6, int(60 * fs),
                               p["rage_light"], int(120 + 50 * pulse), phase * .9,
                               ticks=12, corner=True, tick_len=max(8, int(60 * fs * .12)))
        for i in range(8):
            a = phase * .9 + i * math.tau / 8
            _NS_grimjaw._rune_glyph(
                surface, int(x + math.cos(a) * 60 * fs),
                int(y - 6 + math.sin(a) * 60 * fs * .56),
                max(3, int(4 * fs)), i * 3 + int(phase * 2),
                rage_ramp[i % 2], int(120 + 50 * pulse), rot=a + math.pi / 2)
        # mote bara naik
        for i in range(9):
            t = (phase * 0.35 + i / 9) % 1.0
            mx = x + int(math.sin(i * 2.2) * 36 * fs)
            my = y + 26 - int(t * 76 * fs)
            _NS_grimjaw._aacircle(surface,
                                  (*p["rage_bright"], int(190 * (1 - t))),
                                  (mx, my), 2 if i % 2 else 1)
            _NS_grimjaw._aacircle(surface, p["fire_hot"], (mx, my), 1)

    # ===================================================================
    # SKILL R: OMNISLASH (90 frame)
    # ===================================================================
    def _draw_omnislash_ground(surface, hero, x, y, timer, phase):
        """Ground Omnislash (world-space, v3): retakan api radial + ring
        berputar + sigil rune + dither disk + glow lantai + nova."
        """
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("r", timer)
        steady = _NS_grimjaw._skill_steady(progress)
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        fs = _NS_grimjaw._fx_scale(hero)
        gy = y + 58
        rng = _NS_grimjaw._ring_r(hero, 80, surface)
        rage_ramp = (p["rage_light"], p["rage_mid"], p["rage_bright"])

        # ── AKTIVASI: pilar cahaya 4-lapis + shockwave ganda + nova ──
        if progress < 0.18:
            t = progress / 0.18
            top = int(y - min(140 * fs, 260) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((34, p["rage_dark"], 110),
                                (20, p["rage_mid"], 155),
                                (9, p["rage_light"], 210),
                                (3, p["fire_hot"], 235)):
                _NS_grimjaw._aaline(surface, (*col, int(al * (1 - t))),
                                    (x, top), (x, y), max(1, int(wd * fs * .4)))
            # burst radial (pengganti shockwave bulat)
            for k, rmax in ((0, int(130 * fs)), (1, int(92 * fs))):
                rr = int((16 + t * rmax))
                for kk in range(6):
                    a = phase * .4 + kk * math.pi / 3
                    rl = rr * (1 if kk % 2 else .6)
                    ca, sa = math.cos(a), math.sin(a)
                    _NS_grimjaw._aaline(
                        surface,
                        (*((p["rage_bright"] if k == 0 else p["fire_hot"])),
                         int((225 if k == 0 else 150) * (1 - t))),
                        (x, y), (x + ca * rl, y + sa * rl * .7), 2)
            _NS_grimjaw._spark_star(surface, x, y, int(34 * (1 - t * .4)),
                                    p["fire_hot"], int(235 * (1 - t)),
                                    10, rot=.3, core=p["white"])
            _NS_grimjaw._nova(surface, x, y, int(9 * fs),
                              int((44 + 70 * t) * fs), 8, phase * .2,
                              (p["rage_bright"], p["rage_dark"]),
                              int(215 * (1 - t)))

        # ── STEADY: dither disk + marker AOE bersudut + rune menyebar ──
        _NS_grimjaw._dither_disk(surface, x, gy, int(rng * .64), int(rng * .22),
                                 p["rage_dark"], int((70 + 40 * pulse) * steady),
                                 phase=phase, seed=31)
        _NS_grimjaw._ellipse(surface, (*p["rage_dark"], int(95 + 40 * pulse)),
                             (int(x - rng * 0.55), int(gy - rng * 0.15),
                              int(rng * 1.1), int(rng * 0.30)), 0)
        # marker perimeter (bracket + tick, bukan cincin)
        _NS_grimjaw._aoe_marks(surface, x, y, rng, p["rage_light"],
                               int(120 + 60 * pulse), phase,
                               ticks=16, tick_len=max(8, int(rng * .12)))
        _NS_grimjaw._aoe_marks(surface, x, y, max(6, rng - int(7 * fs)),
                               p["fire_hot"], int(105 + 45 * pulse), -phase,
                               ticks=12, corner=False,
                               tick_len=max(6, int(rng * .07)))
        # rune glyph api menyebar (bukan sigil ring) — angular
        for i in range(10):
            a = phase * .55 + i * math.tau / 10
            gx = x + math.cos(a) * rng * 0.8
            gy = gy + math.sin(a) * rng * 0.34
            _NS_grimjaw._rune_glyph(surface, int(gx), int(gy),
                                    max(3, int(4.5 * fs)), i + int(phase * 2),
                                    rage_ramp[i % 2],
                                    int(115 * steady), rot=a + math.pi / 2)
        # retakan api radial (6, deterministik)
        for i in range(6):
            ang = i * math.pi * 2 / 6 + 0.35
            _NS_grimjaw._jagged_crack(surface, x, gy, ang,
                                      int((30 + (i % 3) * 11) * fs),
                                      (p["rage_dark"], p["rage_mid"]),
                                      int(150 * steady), seed=i + 31, width=2)
        # denyut pusat (glow orb) + ember orbit
        _NS_grimjaw._draw_glow_orb(surface, x, y, int(8 + 3 * pulse),
                                   rage_ramp, int(150 + 70 * pulse))
        _NS_grimjaw._orbit_glints(surface, x, y, int(rng * .56), int(rng * .2),
                                  phase * 1.5, 8, p["fire_hot"],
                                  int(130 * steady), hot=p["rage_bright"])

    def _draw_omnislash_slashes(surface, hero, x, y, timer, phase):
        """Multiple fire slashes emanating from Grimjaw (v3): 7 streak
        radial + core flash + nova + orbit shard (crystal) + ember column."
        """
        p = _NS_grimjaw.PALETTE
        rage_ramp = (p["rage_dark"], p["rage_mid"], p["rage_light"],
                     p["rage_bright"])
        slash_count = 7
        for i in range(slash_count):
            slash_phase = phase * 4 + i * 0.6
            pt_t = (slash_phase % 2) / 2
            if pt_t > 0.7:
                continue
            angle = i * math.pi * 2 / slash_count + phase * 0.3
            dist = 42 + int(pt_t * 34)
            slash_x = int(x + math.cos(angle) * dist)
            slash_y = int(y + math.sin(angle) * dist * 0.8)
            alpha = min(255, max(0, int(255 * (1 - pt_t))))
            slash_len = 30
            end_x = int(math.cos(angle) * slash_len)
            end_y = int(math.sin(angle) * slash_len * 0.8)
            # beam 3-lapis (jalur panas, tanpa alokasi surface)
            _NS_grimjaw._beam3(surface, (slash_x, slash_y),
                               (slash_x + end_x, slash_y + end_y),
                               8, (p["fire_mid"], p["fire_darkest"],
                                   p["fire_hot"]), alpha)
            _NS_grimjaw._aacircle(surface, (*p["white"], alpha),
                                  (slash_x + end_x, slash_y + end_y), 2)

        # orbit shards (mini cristal quill)
        for i in range(6):
            a = phase * 2.6 + i * math.tau / 6
            r = 58 + int(math.sin(phase * 2 + i) * 8)
            sx = int(x + math.cos(a) * r)
            sy = int(y + math.sin(a) * r * 0.55)
            _NS_grimjaw._crystal_shard(surface, sx, sy, 3,
                                       int(9 + (i % 3) * 3), a + math.pi / 2,
                                       rage_ramp, 190, glint=1 if i % 2 == 0 else 0)

        # Central nova + core flash
        core_pulse = math.sin(phase * 6) * 0.3 + 0.7
        _NS_grimjaw._nova(surface, x, y, int(6 * core_pulse),
                          int((20 + 26 * core_pulse)), 8, phase * .3,
                          (p["fire_hot"], p["rage_dark"]),
                          int(190 * core_pulse))
        _NS_grimjaw._aacircle(surface, (*p["fire_hot"], int(180 * core_pulse)),
                              (x, y), int(9 * core_pulse))
        _NS_grimjaw._aacircle(surface, p["fire_core"], (x, y), int(4 * core_pulse))
        # ember column naik
        for i in range(6):
            t = (phase * .35 + i / 6.0) % 1.0
            mx = x + int(math.sin(i * 2.1) * 22)
            my = y + int(20 * (1 - t) - t * 60)
            _NS_grimjaw._aacircle(surface,
                                  (*p["rage_bright"], int(180 * (1 - t))),
                                  (mx, my), 2 if i % 2 else 1)

    def _draw_omnislash_target(surface, hero, x, y, timer, phase):
        """Target-lock indicator (v3): garis putus ke target + chevron +
        cincin target presisi + sigil rune + glint orbit + energy arc."
        """
        p = _NS_grimjaw.PALETTE
        progress = _NS_grimjaw._skill_progress("r", timer)
        steady = _NS_grimjaw._skill_steady(progress)
        pulse = math.sin(phase * 6) * 0.5 + 0.5
        tx, ty = _NS_grimjaw._target_position(hero, x, y)
        if (tx, ty) == (x, y):
            return
        ang = math.atan2(ty - y, tx - x)
        dist = math.hypot(tx - x, ty - y)
        rage_ramp = (p["rage_light"], p["rage_mid"], p["rage_bright"])
        # dashed line (energi zigzag di atas garis putus biasa)
        for i in range(0, 12, 2):
            t1 = i / 12
            t2 = min(1.0, (i + 0.7) / 12)
            _skill_outlined_line(
                surface,
                (x + (tx - x) * t1, y + (ty - y) * t1 - 6),
                (x + (tx - x) * t2, y + (ty - y) * t2 - 6),
                2, p["rage_light"], 190)
        _NS_grimjaw._energy_arc(surface, x, y - 6, tx, ty - 6, 97,
                                p["fire_hot"], int(120 * steady),
                                width=1, wobble=4.0)
        # chevron menuju target (berdenyut)
        for i in range(3):
            t = (i / 3 + phase * 0.6) % 1.0
            _NS_grimjaw._chevron(surface,
                                 x + (tx - x) * t, y + (ty - y) * t - 6,
                                 ang, 13, p["fire_hot"],
                                 int(160 + 80 * pulse * (1 - t)), 3)
        # marker target ANGULAR (bukan cincin) + glint orbit (target-lock)
        _NS_grimjaw._aoe_marks(surface, tx, ty - 6, 20, p["rage_light"],
                               int(150 + 60 * pulse), phase,
                               ticks=10, corner=True,
                               tick_len=max(6, int(20 * .16)))
        _NS_grimjaw._aoe_marks(surface, tx, ty - 6, 12, p["fire_hot"],
                               int(180 + 50 * pulse), -phase,
                               ticks=8, corner=False,
                               tick_len=max(5, int(12 * .2)))
        # rune glyph menyebar (bukan sigil ring)
        for i in range(6):
            a = phase * 1.2 + i * math.tau / 6
            _NS_grimjaw._rune_glyph(surface,
                                    int(tx + math.cos(a) * 26),
                                    int(ty - 6 + math.sin(a) * 26 * .6),
                                    max(2, int(3 * 1.0)), i + int(phase * 2),
                                    rage_ramp[i % 2],
                                    int(150 * steady), rot=a + math.pi / 2)
        _NS_grimjaw._orbit_glints(surface, tx, ty - 6, 28, 28, phase * 2.4, 4,
                                  p["fire_hot"], int(170 * steady),
                                  hot=p["white"])
        # crosshair
        for da in (0, math.pi / 2, math.pi, -math.pi / 2):
            _NS_grimjaw._aaline(
                surface, (*p["fire_hot"], 170),
                (int(tx + math.cos(da) * 6), int(ty - 6 + math.sin(da) * 4)),
                (int(tx + math.cos(da) * 16), int(ty - 6 + math.sin(da) * 10)), 2)

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

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
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
                     segments=10, thick=3, span=0.6, squash=.92):
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

            p = _NS_sylara.PALETTE
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
            p = _NS_sylara.PALETTE

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
        boss._sy_attack_progress = (
            min(1.0, boss._sy_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


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
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sylara._detect_moving(boss)
        _NS_sylara._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

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
        progress = getattr(boss, "_sy_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Check if we should power-shot (during Q)
        powered = getattr(boss, "active_skill", None) == "q"

        # Spawn arrow at release (mid-late in animation)
        release_start = 0.55 if powered else 0.5
        release_end = 0.65 if powered else 0.6

        # Basic attack TIDAK spawn renderer projectile - pakai sistem
        # generic (_entity.py) yang homing & terarah saja supaya tidak
        # ada efek ganda. Renderer arrow hanya saat skill aktif.
        active_skill = getattr(boss, "active_skill", None)
        if (active_skill is not None
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
                                     boss.pulse, "attack", progress,
                                     powered=powered, detail=portrait_hd, **sf)
        if not portrait_hd:
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
        attack = action == "attack"
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
        if attack:
            # 7-keyframe: rest -> wind-up -> tension -> full draw -> IMPACT
            # release -> follow-through -> rest (loop-closure).
            if ap < 0.12:
                t = ap / 0.12
                t = t * t * (3 - 2 * t)
                draw_amt = 0.22 * t
                grip = (19 - int(t * 1), -14 - int(t * 2))
                tilt = .30 - t * .10
            elif ap < 0.26:
                t = (ap - 0.12) / 0.14
                t = t * t * (3 - 2 * t)
                draw_amt = 0.22 + 0.48 * t
                grip = (18 - int(t * 2), -16 - int(t * 2))
                tilt = .20 - t * .10
            elif ap < 0.42:
                t = (ap - 0.26) / 0.16
                t = t * t * (3 - 2 * t)
                draw_amt = 0.70 + 0.30 * t
                grip = (16 - int(t * 1), -18)
                tilt = .10 - t * .06
            elif ap < 0.52:
                t = (ap - 0.42) / 0.10
                draw_amt = 1.0
                grip = (15, -18)
                tilt = .04
            elif ap < 0.58:
                t = (ap - 0.52) / 0.06
                draw_amt = max(0.0, 1.0 - t * 1.6)
                grip = (15 + int(t * 4), -18 + int(t * 4))
                tilt = .04
            elif ap < 0.72:
                t = (ap - 0.58) / 0.14
                t = t * t * (3 - 2 * t)
                draw_amt = 0.0
                grip = (19 - int(t * 1), -14 + int(t * 2))
                tilt = .04 + t * .18
            else:
                t = (ap - 0.72) / 0.28
                t = t * t * (3 - 2 * t)
                draw_amt = 0.0
                grip = (18 - int(t * 1), -12 + int(t * 7))
                tilt = .22 + t * .04
        elif windrun:
            draw_amt = 0.0
            grip = (13, -2)
            tilt = 1.25
        else:
            draw_amt = 0.0
            grip = (17, -5 + int(wave))
            tilt = .26 + wave * .05

        # lengan belakang (penarik tali) digambar sebelum busur
        nock = _NS_sylara._bow_nock(grip, tilt, draw_amt)
        if attack and draw_amt > 0.05:
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
        for i in range(12):
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
        dist = math.hypot(tx - sx, ty - 6 - sy) or 1.0
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
        for i in range(10):
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
    """Kaizen - PIXEL MASTERWORK v3 + SKILL FX / SWING / PROJECTILE rewrite.

    Standar Thorne v2 + Grimjaw v2.1/v3, 100% prosedural (tanpa PNG /
    sprite-sheet / image.load).

    - Rig native ~1.5x (bbox idle ~160x170). Ukuran di arena TIDAK berubah:
      pipeline hero menormalkan tinggi; yang naik adalah kepadatan detail.
    - Disiplin pixel-art: ramp 4-5 band hue-shift, selout, siluet bergerigi
      (_tuft_points), specular cluster, dither, key light kiri-atas.
    - Animasi: foot solver, inersia rambut/scarf, idle hidup, serangan
      7-keyframe iai + smear ujung-bilah + frame IMPACT.
    - Skill FX world-space (_fx_scale / _ring_r) dengan 3 fase jelas.
    - Projectile crescent 3-lapis + trail pita + burst kematian.
    - Semua nama & signature publik lama dipertahankan.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    _STATIC_SURFACES = {}
    _SCRATCH_POOL = {}
    SKILL_VISUAL_DURATION = {"q": 60, "w": 90, "e": 60, "r": 100}
    BLADE_LEN = 62
    ATTACK_WINDUP_END = 0.28
    ATTACK_SWING_END = 0.72
    ATTACK_IMPACT = 0.54

    def _static(key, builder):
        surf = _NS_kaizen._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_kaizen._STATIC_SURFACES[key] = surf
        return surf

    def _scratch(w, h):
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

    PALETTE = {
        # Skin - ramp 5 band, hue-shift hangat ke highlight
        "skin_darkest":   (135,  85,  60),
        "skin_dark":      (185, 130,  95),
        "skin_mid":       (220, 170, 135),
        "skin_light":     (240, 200, 165),
        "skin_high":      (250, 220, 190),

        # Hair - ramp 5 band, bayangan dingin ke ungu-cokelat
        "hair_darkest":   ( 30,  20,  15),
        "hair_dark":      ( 55,  35,  25),
        "hair_mid":       ( 85,  55,  35),
        "hair_light":     (120,  80,  55),
        "hair_shine":     (155, 110,  75),

        # Outfit - indigo dingin (bayangan mengarah ungu, cahaya ke sian)
        "cloth_darkest":  ( 15,  20,  40),
        "cloth_deep":     (  8,  12,  30),
        "cloth_dark":     ( 30,  45,  85),
        "cloth_mid":      ( 55,  80, 145),
        "cloth_light":    ( 90, 130, 200),
        "cloth_high":     (140, 180, 235),

        # Scarf/sash - biru terang
        "scarf_deep":     ( 22,  42,  96),
        "scarf_dark":     ( 40,  70, 140),
        "scarf_mid":      ( 75, 120, 200),
        "scarf_light":    (130, 175, 240),
        "scarf_high":     (185, 215, 255),

        # Pants / hakama
        "pants_dark":     ( 20,  30,  60),
        "pants_mid":      ( 40,  55, 105),
        "pants_light":    ( 70,  95, 155),

        # Leather belt/straps
        "leather_dark":   ( 55,  35,  20),
        "leather_mid":    ( 95,  65,  40),
        "leather_light":  (140, 100,  65),

        # Sword - katana (ramp baja dingin + specular)
        "steel_darkest":  ( 40,  50,  65),
        "steel_dark":     ( 90, 105, 125),
        "steel_mid":      (155, 170, 190),
        "steel_light":    (210, 220, 235),
        "steel_shine":    (245, 250, 255),

        # Handle wrap (ito berlian merah)
        "wrap_dark":      ( 55,  20,  25),
        "wrap_mid":       (110,  40,  50),
        "wrap_light":     (165,  70,  85),

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130,  40),
        "gold_light":     (230, 195,  90),

        # Saya (sarung lacquer merah-delima)
        "saya_dark":      ( 58,  14,  22),
        "saya_mid":       (104,  27,  39),
        "saya_light":     (150,  46,  58),
        "saya_shine":     (205,  96, 100),

        # Wind - sian/putih (FX utama)
        "wind_darkest":   ( 30,  60, 110),
        "wind_dark":      ( 55, 110, 175),
        "wind_mid":       (110, 175, 230),
        "wind_light":     (175, 220, 250),
        "wind_bright":    (215, 240, 255),
        "wind_white":     (245, 252, 255),
        "wind_pale":      (232, 246, 255),
        "wind_deep":      ( 16,  40,  82),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       (200, 150,  50),
        "eye_iris_light": (240, 200, 100),
        "eye_pupil":      ( 15,  15,  20),
        "eye_glow":       (150, 225, 255),

        # Misc
        "ink":            ( 24,  26,  40),
        "cord_dark":      (120,  30,  40),
        "cord_mid":       (190,  55,  65),
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }

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
        return tuple(max(0, min(255, int(c))) for c in color)

    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_kaizen._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaizen._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = _NS_kaizen._scratch(radius * 2 + 4, radius * 2 + 4)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
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

    def _draw_wind_arc(surface, cx, cy, radius, start_angle, end_angle,
                       color, width=2, segments=12):
        points = []
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            points.append((cx + math.cos(angle) * radius,
                           cy + math.sin(angle) * radius))
        for i in range(len(points) - 1):
            _NS_kaizen._aaline(surface, color, points[i], points[i + 1], width)

    def _draw_wind_swirl(surface, cx, cy, size, phase, color=None, alpha=200):
        if color is None:
            color = _NS_kaizen.PALETTE["wind_bright"]
        col = (*color, alpha) if len(color) == 3 else color
        for i in range(2):
            angle_start = phase * 0.8 + i * math.pi
            angle_end = angle_start + math.pi * 1.2
            _NS_kaizen._draw_wind_arc(surface, cx, cy, size, angle_start,
                                      angle_end, col, width=1, segments=6)

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

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
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
        for s in (-1, 1):
            _NS_kaizen._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
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
        """Sabit terisi (proyektil + smear) - poligon 2 busur."""
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
        """Marker AOE ANGULAR — pengganti ring/cincin kontinu.

        Menandai radius gameplay tanpa menggambar lingkaran: deretan
        ``tick`` pendek radial tepat di keliling ``radius`` + 4 bracket
        sudut di posisi diagonal (viewfinder).  Sudut FIXED
        (deterministik) sehingga radius dunia tetap terverifikasi;
        hidupnya dari pulse alpha + panjang tick yang bernapas.
        ``inner=True`` membuat tick mengarah keluar->ke dalam (untuk
        telegraph konvergen "incoming").
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
            _skill_outlined_line(surface, (ix, iy), (ox, oy), 2, color, max(8, al))
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

    # ---------------------------------------------------------------------------
    # PROJECTILE - Steel Wind Slash (crescent 3-lapis + pita trail + burst)
    # ---------------------------------------------------------------------------
    class WindSlashProjectile:
        """Crescent wind slash - trail pita 3-lapis + sabit terisi + glint."""

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
            # ── burst kematian ──
            if not self.alive:
                t = max(0.0, 1.0 - self.dead_frames / 8.0)
                if t <= 0:
                    return
                px, py = int(self.x), int(self.y)
                _NS_kaizen._spark_star(surface, px, py, int(18 * t + 4),
                                       p["wind_pale"], int(230 * t), 8,
                                       rot=phase * 2.4, core=p["white"])
                _NS_kaizen._aacircle(surface, (*p["wind_light"], int(160 * t)),
                                     (px, py), int(10 + 16 * (1 - t)), 2)
                _NS_kaizen._aacircle(surface, (*p["wind_mid"], int(120 * t)),
                                     (px, py), int(6 + 10 * (1 - t)))
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
        """Smear iai: jejak ujung bilah di progress sebelumnya (3-band).

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
        _NS_kaizen._aacircle(surface, (*p["white"], int(220 * fade)),
                             (hx, hy), max(1, int(2 * fade + 1)))
        if impact > 0.15:
            _NS_kaizen._spark_star(surface, hx, hy, int(10 + 14 * impact),
                                   p["wind_pale"], int(240 * impact * fade),
                                   6, rot=0.4, core=p["white"])

    def draw_kaizen(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaizen._detect_moving(boss)
        _NS_kaizen._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_kz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )
        gale = active_skill == "w"
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

    def _draw_kaizen_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False, gale=False,
                           storm=False):
        """Hand-authored pixel-art rig memakai primitive pygame saja.

        Disiplin v2 (standar Thorne): ramp 4-5 band hue-shift, selout
        (outline hanya sisi bayangan), siluet bergerigi, specular cluster,
        dither band, key light kiri-atas. Anchor telapak = +62.
        """
        p = _NS_kaizen.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        stride = math.sin(phase * 1.7)
        # Whole-body root motion: breathing, planted walk bounce, then a
        # compressed wind-up / explosive attack lunge (7 keyframe pose).
        root_y = int(math.sin(phase * .72) * .9)
        sway = int(math.sin(phase * .8) * 3.5) * f if not (walk or attack) else 0
        pose = None
        lean = 0
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 3)
            lean = 5 * f
        elif attack:
            pose = _NS_kaizen._attack_pose(attack_progress)
            lean = int(pose["lean"] * .9) * f
            root_y += int(pose["bob"] * .8)
        # Tremble frame (tension keyframe): badan bergetar 1 px.
        tremble = 0
        if pose is not None and pose.get("tremble"):
            tremble = 1 if (_NS_kaizen._hash01(int(phase * 61)) > .5) else -1

        def pt(dx, dy):
            return (int(cx + dx * f + lean + sway + tremble),
                    int(cy + dy + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                # Selout: outline gelap HANYA di sisi bayangan (kanan-bawah
                # relatif hadap); sisi cahaya bersih + rim 1 px di akhir.
                _NS_kaizen._poly(surface, p["shadow_deep"],
                                  [(x_ + f, y_ + 1) for x_, y_ in pts])
            _NS_kaizen._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_kaizen._aaline(surface, p["shadow_deep"], aa, bb, width + 3)
            _NS_kaizen._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_kaizen._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        # ── inersia rambut & kain: fase tertunda dari gerak badan ──
        # (secondary motion: ujung kain selalu tertinggal dari akselerasi)
        move_amp = 7 if (walk or attack) else 3
        hair_wave = int(math.sin(phase * 1.25 - .7) * move_amp)
        scarf_wave = int(math.sin(phase * 1.45 - .9) * (move_amp + 1))
        band_wave = int(math.sin(phase * 1.6 - 1.1) * (move_amp - 1))
        scarf_boost = 18 if (walk or attack) else 6

        # ── back hair: ponytail besar bergerigi + 7 lock runcing ──
        tail_root = (-9, -52)
        spine = [(-9, -54), (-16, -62 + hair_wave // 2),
                 (-28, -66 + hair_wave), (-44, -60 + hair_wave),
                 (-52, -42 + hair_wave), (-50, -26 + hair_wave)]
        mass = _NS_kaizen._tuft_points(spine, depth=5.0, min_len=8.0, seed=11)
        mass = mass + [(-30, -46 + hair_wave), (-14, -44), (-7, -46)]
        mass_pts = [pt(dx, dy) for dx, dy in mass]
        _NS_kaizen._poly(surface, p["shadow_deep"],
                          [(x_ + f, y_ + 1) for x_, y_ in mass_pts])
        _NS_kaizen._poly(surface, p["hair_darkest"], mass_pts)
        inner_spine = [(-11, -56), (-18, -64 + hair_wave // 2),
                       (-28, -66 + hair_wave), (-38, -56 + hair_wave),
                       (-43, -40 + hair_wave), (-42, -28 + hair_wave)]
        _NS_kaizen._poly(surface, p["hair_dark"],
                          [pt(dx, dy) for dx, dy in inner_spine] +
                          [pt(-26, -46 + hair_wave), pt(-11, -46)])
        locks = [(-24, -68, -52, -76), (-26, -62, -62, -64),
                 (-28, -56, -64, -46), (-26, -50, -58, -30),
                 (-22, -46, -46, -18), (-25, -66, -40, -76),
                 (-19, -70, -30, -80)]
        for i, (mx_, my_, ex_, ey_) in enumerate(locks):
            wave = int(hair_wave * (0.7 + (i % 3) * .35))
            shape = [tail_root, (mx_, my_ + wave), (ex_, ey_ + wave),
                     (mx_ - 3, my_ + 7 + wave), (-11, -46)]
            poly(p["hair_darkest"], shape)
            inner = [(-12, -51), (mx_, my_ + 2 + wave),
                     (ex_ + 4, ey_ + 2 + wave), (mx_ + 1, my_ + 6 + wave)]
            poly(p["hair_dark"], inner, False)
            a_, b_ = pt(mx_ + 2, my_ + 2 + wave), pt(ex_ + 5, ey_ + 2 + wave)
            _NS_kaizen._aaline(surface, p["hair_mid"], a_, b_, 1)
        # specular cluster pada gelombang rambut (1-2 px, disengaja)
        sp = pt(-33, -63 + hair_wave)
        _NS_kaizen._aacircle(surface, p["hair_light"], sp, 2)
        _NS_kaizen._aacircle(surface, p["hair_shine"], (sp[0] + 1, sp[1] - 1), 1)

        # ── hachimaki tails: pita kecil di belakang kepala, inersia cepat ──
        for k, (drop, ln) in enumerate(((-2, -24), (3, -18))):
            wv = band_wave + k * 2
            poly(p["scarf_dark"], [(-12, -78 + k * 2), (-19, -77 + wv // 2),
                 (-26 - scarf_boost // 2, -73 + drop + wv),
                 (-31 - scarf_boost // 2, -71 + drop + wv),
                 (-24, -68 + drop + wv), (-15, -73)])
            _NS_kaizen._aaline(surface, p["scarf_mid"], pt(-20, -76 + wv // 3),
                               pt(-28 - scarf_boost // 2, -71 + drop + wv), 1)

        # ── scarf tails behind torso: SATU ekor ramping mengalir ke
        # bawah-belakang (inersia), terpisah dari pauldron ──
        poly(p["scarf_deep"], [(-8, -32), (-15, -29),
             (-24 - scarf_boost, -20 + scarf_wave),
             (-30 - scarf_boost, -8 + scarf_wave),
             (-22, -2 + scarf_wave // 2), (-14, -16)])
        poly(p["scarf_dark"], [(-10, -29), (-17, -25),
             (-27 - scarf_boost, -14 + scarf_wave),
             (-27 - scarf_boost, -4 + scarf_wave),
             (-20, 0 + scarf_wave // 2), (-13, -14)], False)
        poly(p["scarf_mid"], [(-12, -26), (-18, -21),
             (-25 - scarf_boost, -11 + scarf_wave),
             (-21, -3 + scarf_wave // 2), (-14, -12)], False)
        _NS_kaizen._aaline(surface, p["scarf_light"], pt(-14, -23),
                           pt(-25 - scarf_boost, -7 + scarf_wave), 1)

        # ── lacquered saya behind hip (3 band + kojiri emas + sageo) ──
        limb((-10, 8), (-46, 44), 10, p["saya_dark"], None)
        _NS_kaizen._aaline(surface, p["saya_mid"], pt(-10, 7), pt(-46, 43), 7)
        _NS_kaizen._aaline(surface, p["saya_light"], pt(-12, 5), pt(-48, 41), 2)
        _NS_kaizen._aaline(surface, p["saya_shine"], pt(-13, 4), pt(-24, 15), 1)
        # sageo (tali pembalut) melilit + kojiri (ujung) emas
        for t in (.3, .55, .8):
            sx_ = -10 + (-36) * t
            sy_ = 8 + 36 * t
            _NS_kaizen._aaline(surface, p["cord_mid"],
                               pt(sx_ - 3, sy_ + 2), pt(sx_ + 3, sy_ - 2), 2)
        _NS_kaizen._aacircle(surface, p["gold_dark"], pt(-46, 44), 4)
        _NS_kaizen._aacircle(surface, p["gold_mid"], pt(-47, 43), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"],
                             (pt(-47, 43)[0] - 1, pt(-47, 43)[1] - 1), 1)

        # ── legs: true split stance + foot solver ──
        # v2: kaki yang melangkah terangkat (lutut + telapak naik dari
        # fase stride), telapak tumpuan menapak dan memicu debu.
        leg_phase = stride if walk else 0.0
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 13) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 13) if walk else 0
        rear_foot = (-15 - int(leg_phase * 7),
                     60 - int(abs(leg_phase) * 3) - rear_lift)
        front_foot = (17 + int(leg_phase * 8), 60 - front_lift)
        for hip, knee, foot, shade, lift in (
                ((-9, 16), (-15, 38), rear_foot, p["pants_dark"], rear_lift),
                ((11, 16), (16, 37), front_foot, p["pants_mid"], front_lift)):
            # Knee rises with the lift so the thigh folds up to meet the
            # raised shin (proper knee-bend, no gap between segments).
            knee = (knee[0], knee[1] - lift)
            poly(shade, [hip, (hip[0] + 9, hip[1]),
                         (knee[0] + 7, knee[1]), (foot[0] + 6, foot[1] - 8),
                         (foot[0] - 6, foot[1] - 8),
                         (knee[0] - 6, knee[1])])
            # kyahan (pelindung tulang kering) + tabi
            poly((204, 211, 216), [(foot[0] - 5, foot[1] - 15),
                 (foot[0] + 5, foot[1] - 15), (foot[0] + 6, foot[1] - 6),
                 (foot[0] - 6, foot[1] - 6)], False)
            _NS_kaizen._aaline(surface, (160, 170, 178),
                               pt(foot[0] - 4, foot[1] - 11),
                               pt(foot[0] + 5, foot[1] - 11), 1)
            poly(p["leather_dark"], [(foot[0] - 7, foot[1] - 6),
                 (foot[0] + 9, foot[1] - 6), (foot[0] + 11, foot[1]),
                 (foot[0] - 7, foot[1])])
            # sandal: sol + tali
            _NS_kaizen._aaline(surface, p["leather_mid"],
                               pt(foot[0] - 5, foot[1] - 4),
                               pt(foot[0] + 7, foot[1] - 4), 1)
            _NS_kaizen._aaline(surface, p["leather_light"],
                               pt(foot[0] - 3, foot[1] - 5),
                               pt(foot[0] - 1, foot[1] - 1), 1)
            _NS_kaizen._aacircle(surface, p["leather_light"],
                                 pt(foot[0] + 2, foot[1] - 8), 1)

        # ── hakama: panel lebar berlipat + hem bergerigi + dither ──
        hem_r = [(-24, 14), (-6, 18), (2, 34), (-18, 38), (-30, 30)]
        hem_r = [(dx, dy) for dx, dy in
                 _NS_kaizen._tuft_points(hem_r, 3.4, 7.0, seed=21)]
        poly(p["pants_dark"], hem_r)
        hem_f = [(0, 18), (20, 14), (31, 26), (26, 38), (8, 40), (2, 34)]
        hem_f = [(dx, dy) for dx, dy in
                 _NS_kaizen._tuft_points(hem_f, 3.4, 7.0, seed=33)]
        poly(p["pants_mid"], hem_f)
        poly(p["pants_light"], [(4, 20), (17, 17), (24, 27), (18, 34),
                                (9, 34)], False)
        # lipatan pleat (garis gelap vertikal)
        for dx in (-13, 3, 8, 17):
            _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(dx, 14),
                               pt(dx + (2 if dx > 0 else -2), 33), 1)
        # dither band klasik di batas light/mid hakama depan
        _NS_kaizen._dither_dots(surface, p["pants_light"], pt(6, 24),
                                pt(20, 22), step=3, alpha=170)

        # ── torso: open jacket + dada + harness ──
        # jok bahu depan: KECIL, hanya menutupi sendi lengan
        poly(p["cloth_darkest"], [(6, -36), (19, -33), (24, -26),
             (20, -19), (9, -21), (4, -28)])
        poly(p["cloth_darkest"], [(-20, -32), (-2, -38), (22, -34),
             (30, -18), (26, 4), (12, 14), (-14, 10), (-24, -12)])
        poly(p["cloth_deep"], [(-20, -26), (-14, -29), (-16, 6),
             (-24, -10)], False)
        # panel kain belakang (kiri) + lipatan
        poly(p["cloth_dark"], [(-18, -30), (-4, -34), (-4, 8), (-14, 6),
             (-22, -14)], False)
        poly(p["cloth_mid"], [(-16, -28), (-6, -31), (-7, 5), (-14, 3),
             (-19, -12)], False)
        # dada terbuka (kulit) + shading plane
        poly(p["skin_dark"], [(-1, -27), (13, -28), (17, -14),
             (11, 6), (1, 7)], False)
        poly(p["skin_mid"], [(1, -25), (11, -26), (13, -13),
             (9, 3), (2, 4)], False)
        poly(p["skin_light"], [(3, -23), (9, -23), (10, -14),
             (6, -2), (3, -6)], False)
        # specular cluster dada + dither sisi bayangan
        _NS_kaizen._aacircle(surface, p["skin_high"], pt(5, -20), 2)
        _NS_kaizen._dither_dots(surface, p["skin_dark"], pt(1, 4),
                                pt(10, 1), step=2, alpha=130)
        # collar cross (lapihan jaket bertemu di dada)
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(-2, -32), pt(12, 4), 5)
        _NS_kaizen._aaline(surface, p["cloth_mid"], pt(-2, -32), pt(12, 4), 3)
        _NS_kaizen._aaline(surface, p["cloth_high"], pt(-2, -33), pt(12, 4), 1)
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(-6, -31), pt(4, 6), 4)
        _NS_kaizen._aaline(surface, p["scarf_dark"], pt(-6, -31), pt(4, 6), 2)
        # sabuk kulit diagonal (X harness) + jahitan
        _NS_kaizen._aaline(surface, p["leather_dark"], pt(-16, -28), pt(14, 6), 6)
        _NS_kaizen._aaline(surface, p["leather_mid"], pt(-16, -28), pt(14, 6), 4)
        _NS_kaizen._aaline(surface, p["leather_light"], pt(-16, -29), pt(14, 6), 1)
        for t in (.25, .5, .75):
            bx_ = -16 + 30 * t
            by_ = -28 + 34 * t
            _NS_kaizen._aaline(surface, p["leather_light"],
                               pt(bx_ - 2, by_ - 1), pt(bx_ + 2, by_ + 1), 1)
        # braided obi + knot belakang + wrap emas
        _NS_kaizen._aaline(surface, p["ink"], pt(-18, 11), pt(22, 9), 7)
        _NS_kaizen._aaline(surface, p["scarf_dark"], pt(-18, 10), pt(22, 8), 4)
        for dx in range(-14, 21, 5):
            _NS_kaizen._aaline(surface, p["scarf_mid"], pt(dx - 1, 6),
                               pt(dx + 1, 12), 1)
        _NS_kaizen._aaline(surface, p["gold_dark"], pt(-18, 11), pt(22, 10), 2)
        for dx in range(-12, 20, 7):
            _NS_kaizen._aacircle(surface, p["gold_mid"], pt(dx, 8), 1)
        # knot obi belakang + ujung tali
        poly(p["scarf_dark"], [(-18, 6), (-26, 8), (-24, 16), (-17, 14)])
        poly(p["scarf_mid"], [(-19, 8), (-24, 9), (-23, 13), (-19, 12)], False)

        # ── pauldron baja berlapis (bahu pedang) + sode belakang ──
        # Baja abu-abu dingin: hue-nyapisah dari scarf indigo di belakangnya.
        pauldron = [(11, -32), (29, -30), (36, -22), (32, -13),
                    (23, -9), (13, -14)]
        poly(p["steel_darkest"], pauldron)
        poly(p["steel_dark"], [(13, -30), (26, -28), (32, -22),
             (29, -15), (22, -12), (14, -16)], False)
        for i in range(3):
            yy = -27 + i * 4
            _NS_kaizen._aaline(surface, p["steel_mid"],
                               pt(14, yy), pt(29 - i * 2, yy + 2), 1)
        # rim emas tepi atas + rivet + specular cluster
        _NS_kaizen._aaline(surface, p["gold_dark"], pt(10, -29), pt(36, -21), 3)
        _NS_kaizen._aaline(surface, p["gold_mid"], pt(11, -30), pt(35, -22), 1)
        for rx, ry in ((16, -25), (24, -23), (30, -18)):
            _NS_kaizen._aacircle(surface, p["steel_light"], pt(rx, ry), 1)
        _NS_kaizen._aacircle(surface, p["steel_shine"], pt(16, -26), 2)
        _NS_kaizen._aacircle(surface, p["white"],
                             (pt(16, -26)[0] - 1, pt(16, -26)[1] - 1), 1)
        # sode kecil di bahu belakang (2 lame)
        for i in range(2):
            poly(p["steel_dark"] if i else p["steel_darkest"],
                 [(-18, -30 + i * 4), (-10, -28 + i * 4),
                  (-11, -23 + i * 4), (-19, -25 + i * 4)], i == 0)
            _NS_kaizen._aaline(surface, p["steel_mid"],
                               pt(-17, -27 + i * 4), pt(-12, -26 + i * 4), 1)

        # ── jacket piping + crest angin kecil ──
        _NS_kaizen._aaline(surface, p["cloth_high"], pt(-17, -19),
                           pt(-15, 4), 1)
        for yy in (-14, -7, 0):
            _NS_kaizen._aaline(surface, p["scarf_light"],
                               pt(-19, yy), pt(-15, yy + 1), 1)
        _NS_kaizen._draw_wind_arc(surface, *pt(-8, -8), 6, .3, 4.4,
                                   p["wind_mid"], 1, 7)

        # ── rear arm / bracer ──
        if attack and pose is not None:
            hx_, hy_ = pose["hand"]
            rear_hand = (-4 + int(hx_ * .2), -6 - int(-hy_ * .12))
        else:
            rear_hand = (-22, 6)
        if walk:
            rear_hand = (-22 - int(stride * 4), 6 + int(abs(stride) * 1))
        limb((-16, -28), (-28, -14), 9, p["cloth_dark"], p["cloth_light"])
        # sleeve fold
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(-24, -18),
                           pt(-20, -12), 2)
        limb((-28, -12), rear_hand, 7, p["skin_dark"], p["skin_light"])
        # bracer kulit + strap
        _NS_kaizen._aaline(surface, p["leather_dark"], pt(-26, -10),
                           pt(rear_hand[0] + 2, rear_hand[1] - 2), 5)
        _NS_kaizen._aaline(surface, p["leather_mid"], pt(-26, -10),
                           pt(rear_hand[0] + 2, rear_hand[1] - 2), 3)
        rhx, rhy = pt(*rear_hand)
        _NS_kaizen._rect(surface, p["wrap_dark"], (rhx - 5, rhy - 5, 10, 10), 2)
        _NS_kaizen._aaline(surface, p["wrap_light"], (rhx - 4, rhy - 2),
                           (rhx + 4, rhy + 1), 1)
        _NS_kaizen._aaline(surface, p["gold_mid"], (rhx - 4, rhy + 3),
                           (rhx + 4, rhy + 3), 1)

        # ── neck and three-quarter head (leher pendek: dagu -51,
        # lilitan scarf mulai -50 -> leher nyaris tak terlihat).
        # PENTING: poly leher berhenti di -40 karena digambar SETELAH
        # torso; kalau lebih panjang, dia menimpa kain torso di bawah
        # collar dan muncul kolom kulit palsu. ──
        poly(p["skin_dark"], [(-6, -50), (8, -50), (8, -40), (-6, -40)])
        face = [(-12, -63), (-10, -80), (-4, -92), (8, -94),
                (15, -87), (18, -75), (15, -62), (8, -53), (0, -51), (-8, -55)]
        poly(p["skin_dark"], face)
        poly(p["skin_mid"], [(-9, -66), (-7, -79), (-3, -88),
             (6, -90), (12, -85), (14, -75), (12, -64), (6, -56), (0, -54),
             (-6, -57)], False)
        poly(p["skin_light"], [(0, -84), (7, -85), (11, -80),
             (10, -72), (5, -68), (1, -72)], False)
        _NS_kaizen._aacircle(surface, p["skin_high"], pt(6, -80), 2)
        # hidung, alis, mata (blink), parut, mulut
        poly(p["skin_light"], [(12, -72), (19, -69), (12, -66)], False)
        _NS_kaizen._aaline(surface, p["hair_darkest"], pt(3, -74), pt(12, -72), 2)
        blink = (math.sin(phase * .53) > .985) or \
                (math.sin(phase * .31 + 1.7) > .99)
        if blink:
            _NS_kaizen._aaline(surface, p["skin_darkest"], pt(7, -68),
                               pt(12, -68), 1)
        else:
            _NS_kaizen._rect(surface, p["eye_white"],
                             (pt(7, -70)[0], pt(7, -70)[1], 5, 3))
            _NS_kaizen._rect(surface, p["eye_iris"],
                             (pt(9, -70)[0], pt(9, -70)[1], 2, 3))
            _NS_kaizen._aacircle(surface, p["eye_pupil"], pt(10, -69), 1)
            _NS_kaizen._aacircle(surface,
                                 p["eye_glow"] if storm else p["eye_iris_light"],
                                 pt(9, -70), 1)
        _NS_kaizen._aaline(surface, (120, 48, 47), pt(-1, -62), pt(9, -52), 1)
        _NS_kaizen._aaline(surface, p["skin_darkest"], pt(6, -57), pt(11, -58), 1)
        _NS_kaizen._aacircle(surface, p["gold_light"], pt(-11, -64), 2)

        # ── hair cap + mahkota runcing: hanya menutup di ATAS ikat kepala
        # (poni bergerigi y=-75..-80) supaya wajah -50..-74 tetap terbaca ──
        crown = [(-15, -72), (-15, -82), (-11, -94), (-5, -102),
                 (-1, -93), (5, -100), (9, -90), (14, -92),
                 (12, -82), (16, -80),
                 (13, -76), (6, -79), (2, -75), (-3, -79),
                 (-7, -76), (-11, -78)]
        poly(p["hair_darkest"], crown)
        poly(p["hair_dark"], [(-12, -74), (-12, -82), (-8, -92),
             (-4, -97), (0, -91), (4, -95), (7, -88), (11, -87),
             (10, -81), (12, -79), (7, -77), (2, -77), (-3, -77),
             (-7, -76), (-10, -77)], False)
        _NS_kaizen._aaline(surface, p["hair_mid"], pt(-4, -88), pt(1, -93), 1)
        _NS_kaizen._aacircle(surface, p["hair_light"], pt(4, -89), 2)
        # topknot chonmage + wrap tinta
        poly(p["hair_darkest"], [(-10, -96), (-2, -104), (6, -106),
             (10, -100), (4, -94), (-4, -92)])
        poly(p["hair_dark"], [(-7, -96), (-1, -101), (5, -101),
             (7, -98), (1, -95)], False)
        _NS_kaizen._rect(surface, p["ink"],
                         (pt(-4, -98)[0], pt(-4, -98)[1], 4, 3))
        _NS_kaizen._aacircle(surface, p["hair_light"], pt(-2, -100), 1)
        # hachimaki band + manik angin (menyala saat storm)
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(-11, -78),
                           pt(14, -76), 5)
        _NS_kaizen._aaline(surface, p["scarf_mid"], pt(-10, -79),
                           pt(14, -77), 2)
        _NS_kaizen._aaline(surface, p["scarf_high"], pt(-9, -80),
                           pt(6, -79), 1)
        bead_col = p["wind_bright"] if storm else p["wind_dark"]
        _NS_kaizen._aacircle(surface, bead_col, pt(9, -78), 2)
        _NS_kaizen._aacircle(surface,
                             p["wind_pale"] if storm else p["wind_light"],
                             (pt(9, -78)[0] - 1, pt(9, -78)[1] - 1), 1)
        if storm:
            _NS_kaizen._spark_star(surface, *pt(9, -78), 6, p["wind_pale"],
                                   int(150 + 70 * math.sin(phase * 4)), 4,
                                   rot=phase, core=p["white"])

        # Scarf collar: trapesium yang TAPER mengikuti rahang di atas
        # (14 px = selebar dagu) lalu melebar natural ke dada/bahu di
        # bawah - seperti scarf dililit, bukan blok kolom.
        poly(p["scarf_deep"], [(-7, -50), (10, -50), (13, -41),
             (0, -36), (-11, -39), (-12, -44)])
        poly(p["scarf_dark"], [(-5, -48), (8, -48), (10, -41),
             (-1, -37), (-9, -40), (-10, -43)], False)
        # lipatan wrap diagonal (tekstur kain lilit)
        _NS_kaizen._aaline(surface, p["scarf_deep"], pt(-8, -42), pt(6, -44), 1)
        # tepi atas terang (key light kiri-atas)
        _NS_kaizen._aaline(surface, p["scarf_light"], pt(-4, -49), pt(6, -49), 1)

        # ── front arm + katana (pose-driven via _attack_pose) ──
        if attack and pose is not None:
            hand = pose["hand"]
            k_angle = pose["angle"]
            flare = pose["flare"]
        else:
            flare = 1.0
            if walk:
                hand = (36, -6 + int(stride * 3))
                k_angle = 0.46 + math.sin(phase * 1.7) * 0.06
            else:
                hand = (34, -2 + int(math.sin(phase * .72) * 1.2))
                k_angle = 0.34 + math.sin(phase * .72) * .03
        limb((18, -28), (30, -12), 9, p["cloth_dark"], p["cloth_light"])
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(26, -18),
                           pt(29, -12), 2)
        limb((30, -10), hand, 7, p["skin_dark"], p["skin_light"])
        # forearm wrap merah (2 band)
        mx_, my_ = (30 + hand[0]) // 2, (-10 + hand[1]) // 2
        _NS_kaizen._aaline(surface, p["wrap_dark"], pt(mx_ - 1, my_ - 1),
                           pt(hand[0] - 3, hand[1] - 2), 6)
        _NS_kaizen._aaline(surface, p["wrap_mid"], pt(mx_ - 1, my_ - 1),
                           pt(hand[0] - 3, hand[1] - 2), 4)
        for t in (.35, .7):
            wx_ = int(30 + (hand[0] - 30) * t)
            wy_ = int(-10 + (hand[1] + 10) * t)
            _NS_kaizen._aaline(surface, p["wrap_light"],
                               pt(wx_ - 2, wy_), pt(wx_ + 2, wy_ - 2), 1)
        hx, hy = pt(*hand)
        _NS_kaizen._rect(surface, p["wrap_dark"], (hx - 5, hy - 5, 10, 10), 2)
        _NS_kaizen._aaline(surface, p["wrap_light"], (hx - 4, hy - 2),
                           (hx + 4, hy + 1), 1)

        glow = 0.0
        smear = 0.0
        if attack:
            glow = max(glow, .55 + .45 * math.sin(attack_progress * math.pi))
            # smear aktif di jendela strike 0.3..0.72 (puncak ~0.5)
            smear = max(0.0, 1.0 - abs(attack_progress - .5) / .22)
        if gale:
            glow = max(glow, .5)
        if storm:
            glow = max(glow, .65)
        _NS_kaizen._draw_elite_katana(
            surface, cx + lean + sway + tremble, cy + root_y, facing, hand,
            k_angle, phase, attacking=attack, glow=glow, flare=flare,
            smear=smear, progress=attack_progress)

        # ── secondary motion / contact feedback ──
        if walk:
            # Dust appears only near footfall (|stride| close to one), while
            # speed lines trail opposite the facing direction.
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx_, fy_ = pt(planted[0], planted[1])
                alpha = int(150 * contact)
                for i in range(4):
                    _NS_kaizen._aacircle(
                        surface, (*p["wind_mid"], max(15, alpha - i * 24)),
                        (fx_ - f * (4 + i * 4), fy_ - i % 2), max(1, 3 - i // 2))
            for i in range(3):
                sy_ = cy - 10 + i * 13 + root_y
                _NS_kaizen._aaline(surface, (*p["wind_light"], 95 - i * 18),
                                   (cx - f * (36 + i * 9), sy_),
                                   (cx - f * (18 + i * 7), sy_ - 1), 1)
        elif attack:
            ap_ = max(0.0, min(1.0, attack_progress))
            impact = max(0.0, 1.0 - abs(ap_ - .52) / .16)
            if impact > 0:
                ix, iy = pt(70, -4)
                # IMPACT: bintang 6-8 spike + shockwave elips + serpihan
                _NS_kaizen._spark_star(surface, ix, iy,
                                       int(10 + 16 * impact), p["wind_pale"],
                                       int(235 * impact), 6, rot=.4,
                                       core=p["white"])
                _NS_kaizen._ellipse(
                    surface, (*p["wind_bright"], int(150 * impact)),
                    (ix - int(26 * impact), iy - int(7 * impact),
                     int(52 * impact), int(14 * impact)), 2)
                for i in range(5):
                    ang = -1.3 + i * .5
                    length = 8 + int(impact * (12 + i % 2 * 6))
                    _NS_kaizen._aaline(surface,
                                       (*p["wind_white"], int(220 * impact)),
                                       (ix, iy),
                                       (ix + math.cos(ang) * length * f,
                                        iy + math.sin(ang) * length),
                                       1 if i % 2 else 2)
        else:
            # ── v2: aura angin berputar + daun angin (idle showcase) ──
            aura_r = 44 + int(math.sin(phase * .9) * 4)
            for k in range(2):
                _NS_kaizen._draw_wind_arc(
                    surface, cx, cy - 8, aura_r + k * 8,
                    phase * (0.55 + k * .35),
                    phase * (0.55 + k * .35) + 4.4,
                    (*p["wind_mid"], 30 - k * 12), 1, 12)
            # orbiting bright wisps tracing the aura
            for i in range(3):
                a = phase * 1.1 + i * math.tau / 3
                wx_ = cx + int(math.cos(a) * aura_r)
                wy_ = cy - 8 + int(math.sin(a) * aura_r * .55)
                _NS_kaizen._aacircle(surface, (*p["wind_bright"], 150),
                                     (wx_, wy_), 1)
            # drifting wind leaves (daun angin) - teardrop kecil berputar
            for i in range(4):
                t = (phase * .11 + i / 4.0) % 1.0
                lx = cx + int(math.sin(phase * 1.3 + i * 1.7) * (28 + i * 6))
                ly = cy + 30 - int(t * 96)
                la = phase * .8 + i * 2.4
                ca_, sa_ = math.cos(la), math.sin(la)
                tip = (int(lx + ca_ * 4), int(ly + sa_ * 4))
                b1 = (int(lx - sa_ * 2), int(ly + ca_ * 2))
                b2 = (int(lx + sa_ * 2), int(ly - ca_ * 2))
                _NS_kaizen._poly(surface, (*p["wind_mid"], 110),
                                 [tip, b1, b2])
                _NS_kaizen._poly(surface, (*p["wind_bright"], 80),
                                 [tip, (int(lx + sa_ * 1), int(ly - ca_ * 1)),
                                  (int(lx - sa_ * 1), int(ly + ca_ * 1))])
            # Quiet idle motes make breathing visible without obscuring face.
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx2 = cx + int(math.sin(phase + i * 2.1) * (24 + i * 5))
                my2 = cy + 38 - int(t * 86)
                _NS_kaizen._aacircle(surface,
                                     (*p["wind_bright"], int(110 * (1 - t))),
                                     (mx2, my2), 1)

        # ── gale / storm body reaction (v2.1) ──
        if gale and not attack:
            pulse_ = .6 + .4 * math.sin(phase * 2.2)
            _NS_kaizen._draw_wind_arc(surface, cx, cy - 10, 52,
                                      phase * .9, phase * .9 + 3.6,
                                      (*p["wind_bright"], int(60 * pulse_)), 2, 12)
            _NS_kaizen._draw_wind_arc(surface, cx, cy - 10, 44,
                                      -phase * 1.2, -phase * 1.2 + 2.8,
                                      (*p["wind_light"], int(80 * pulse_)), 1, 10)
        if storm:
            # mata + bead + tepi jaket berpendar saat ultimate
            gl = int(120 + 80 * math.sin(phase * 3.4))
            _NS_kaizen._aaline(surface, (*p["eye_glow"], min(255, gl)),
                               pt(7, -70), pt(12, -70), 2)
            _NS_kaizen._aaline(surface, (*p["wind_light"], int(gl // 2)),
                               pt(-17, -18), pt(-15, 3), 1)

        # ── rim-light: sinyal angin biru di tepi yang menghadap cahaya ──
        # `pt()` sudah membalik tanda saat facing -1, jadi cukup pakai dx
        # positif (tepi depan). Key light kiri-atas konsisten lighting.py.
        pulse2 = 0.72 + 0.28 * math.sin(phase * 1.8)
        rim_a = int(150 * pulse2)
        rim_col = (*p["wind_light"], rim_a)
        rim_hot = (*p["wind_white"], int(205 * pulse2))
        # puncak rambut & mahkota
        _NS_kaizen._aaline(surface, rim_col, pt(1, -80), pt(4, -71), 1)
        _NS_kaizen._aaline(surface, rim_col, pt(4, -71), pt(11, -68), 1)
        _NS_kaizen._aaline(surface, rim_hot, pt(2, -77), pt(5, -72), 1)
        # tepi atas pauldron - kilau ganda
        _NS_kaizen._aaline(surface, rim_col, pt(11, -29), pt(36, -21), 1)
        _NS_kaizen._aaline(surface, rim_hot, pt(14, -28), pt(24, -25), 1)
        # tepi depan torso & jaket
        _NS_kaizen._aaline(surface, rim_col, pt(22, -18), pt(19, 6), 1)
        # tepi depan paha & boot depan (ikut naik saat kaki terangkat)
        _NS_kaizen._aaline(surface, rim_col, pt(13, 34 - front_lift),
                           pt(17, 55 - front_lift), 1)
        _NS_kaizen._aacircle(surface, rim_hot, pt(17, 58 - front_lift), 1)
        # glint gagang katana hanya saat diam
        if not attack:
            _NS_kaizen._aacircle(surface, rim_hot, pt(30, -4), 1)

        if detail:
            # Portrait-only micro-detail. At arena scale these marks would
            # collapse into noise, so LOD keeps them out of gameplay cache.
            for i in range(6):
                _NS_kaizen._aaline(
                    surface, p["hair_light"],
                    pt(-18 - i * 3, -66 + i * 3),
                    pt(-32 - i * 3, -70 + i * 5), 1)
            # Face planes, lower eyelid and lip highlight
            _NS_kaizen._aaline(surface, p["skin_high"],
                               pt(3, -86), pt(8, -83), 1)
            _NS_kaizen._aaline(surface, p["skin_darkest"],
                               pt(4, -64), pt(11, -62), 1)
            _NS_kaizen._aaline(surface, p["skin_light"],
                               pt(7, -56), pt(12, -57), 1)
            # bulu mata + kelopak bawah
            _NS_kaizen._aaline(surface, p["ink"], pt(12, -71), pt(13, -68), 1)
            # Fine textile weave and hakama hem stitching
            for yy in (-16, -9, -2):
                _NS_kaizen._aaline(surface, p["cloth_light"],
                                   pt(-13, yy), pt(-8, yy + 2), 1)
            for xx in (-14, -6, 8, 16):
                _NS_kaizen._aacircle(surface, p["scarf_light"],
                                      pt(xx, 32), 1)
            # Engraved pauldron fan + reflected rivet glints
            for a in (-.7, -.2, .3):
                _NS_kaizen._aaline(surface, p["steel_mid"], pt(18, -18),
                                   pt(18 + math.cos(a) * 7,
                                      -18 + math.sin(a) * 7), 1)
            _NS_kaizen._aacircle(surface, p["wind_white"], pt(20, -22), 1)
            # serat saya + emboss manik hachimaki
            _NS_kaizen._aaline(surface, p["saya_shine"], pt(-20, 14),
                               pt(-30, 24), 1)
            _NS_kaizen._aacircle(surface, p["wind_white"], pt(9, -79), 1)
            # uap napas kecil
            _NS_kaizen._aacircle(surface, (*p["wind_pale"], 120), pt(20, -58), 2)
            _NS_kaizen._aacircle(surface, (*p["wind_pale"], 70), pt(24, -61), 1)

    def _draw_elite_katana(surface, cx, cy, facing, hand, angle, phase,
                           attacking=False, glow=0.0, flare=1.0, smear=0.0,
                           progress=0.0):
        """Katana masterwork: sori, hamon, kissaki, tsuba 4-lobe, ito, smear.

        smear: jejak ujung-bilah (bukan ghost poligon kaku) supaya kepala
        trail menempel di kissaki. wind-up (smear~0) menampilkan bilah bersih.
        """
        p = _NS_kaizen.PALETTE
        f = 1 if facing >= 0 else -1
        hx, hy = cx + hand[0] * f, cy + hand[1]
        length = _NS_kaizen.BLADE_LEN
        A = angle if f > 0 else math.pi - angle
        ux, uy = math.cos(A), math.sin(A)
        tx, ty = hx + ux * length, hy + uy * length
        px, py = -uy, ux

        # smear DULU (di bawah bilah)
        if attacking and smear > 0.05:
            _NS_kaizen._draw_katana_swing_trail(
                surface, cx, cy, f, phase, progress)
            # sabit 3-band tambahan di jendela IMPACT (px putih sian)
            start = A - 1.15 * max(0.6, flare)
            for radius, color, width in (
                    (64, (*p["wind_dark"], int(80 * smear)), 5),
                    (61, (*p["wind_light"], int(160 * smear)), 3),
                    (58, (*p["wind_white"], int(230 * smear)), 1)):
                _NS_kaizen._draw_wind_arc(surface, hx, hy, radius,
                                          start, A + .22, color, width, 14)

        # tsuka + kashira
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
        _NS_kaizen._aacircle(surface, p["gold_mid"], (int(ex) - f, int(ey) - 1), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"],
                             (int(ex) - f - 1, int(ey) - 2), 1)

        # blade sori
        mx, my = hx + ux * 34 + px * 3.2, hy + uy * 34 + py * 3.2
        blade = [(hx + px * 3.4, hy + py * 3.4),
                 (mx + px * 2.4, my + py * 2.4),
                 (tx + px * 1.2, ty + py * 1.2),
                 (tx + px * .4, ty + py * .4),
                 (mx - px * 1.1, my - py * 1.1),
                 (hx - px * 2.2, hy - py * 2.2)]
        _NS_kaizen._poly(surface, p["shadow_deep"],
                          [(x_ + f, y_ + 1) for x_, y_ in blade])
        _NS_kaizen._poly(surface, p["steel_dark"], blade)
        _NS_kaizen._aaline(surface, p["steel_darkest"],
                           (hx + px * 2.6, hy + py * 2.6),
                           (tx + px * 1.0, ty + py * 1.0), 1)
        _NS_kaizen._aaline(surface, p["steel_mid"],
                           (hx, hy), (mx + px * .4, my + py * .4), 2)
        _NS_kaizen._aaline(surface, p["steel_light"],
                           (hx + px * 2.6, hy + py * 2.6),
                           (int(tx), int(ty)), 1)
        _NS_kaizen._aaline(surface, p["steel_shine"],
                           (hx + px * 3, hy + py * 3),
                           (tx + px * 1.6, ty + py * 1.6), 1)
        _NS_kaizen._aaline(surface, p["steel_shine"],
                           (int(tx), int(ty)),
                           (int(tx - ux * 5 + px * 2.2),
                            int(ty - uy * 5 + py * 2.2)), 1)
        hamon = []
        for i in range(1, 9):
            t = i / 9.0
            wave = math.sin(i * math.pi * .72 + phase * .2) * .9
            hamon.append((hx + ux * length * t + px * wave,
                          hy + uy * length * t + py * wave))
        if len(hamon) > 1:
            pygame.draw.aalines(surface, p["wind_mid"], False, hamon)
        _NS_kaizen._aacircle(surface, p["steel_shine"], (int(tx), int(ty)), 2)

        # tsuba 4-lobe
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
                _NS_kaizen._aaline(surface, (*p["wind_white"], min(255, ga - 40)),
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
            _NS_kaizen._aacircle(surface, (*p["wind_dark"], alpha), (sx, sy), 6)
            _NS_kaizen._aacircle(surface, (*p["wind_mid"], alpha), (sx, sy - 2), 4)
            _NS_kaizen._aacircle(surface, (*p["wind_bright"], min(255, alpha)),
                                 (sx, sy - 4), 1)

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
                                      (*p["wind_bright"], int(70 * pulse_)), 2, 10)

    def _draw_shadow(surface, x, y):
        def build():
            shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
            for radius in range(13, 0, -1):
                alpha = max(0, (13 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (13 - radius, 13 - radius, 104 + radius * 2, radius * 2))
            pygame.draw.ellipse(shadow,
                                (*_NS_kaizen.PALETTE["wind_darkest"], 40),
                                (10, 5, 110, 13))
            return shadow
        surface.blit(_NS_kaizen._static("shadow", build), (x - 65, y - 13))

    def _draw_swordsman_rim_light(surface, x, y, phase):
        pulse = .72 + math.sin(phase * 1.3) * .16

        def build():
            halo = pygame.Surface((116, 128), pygame.SRCALPHA)
            for radius, alpha in ((50, 9), (38, 14), (26, 20)):
                _NS_kaizen._aacircle(halo, (*_NS_kaizen.PALETTE["wind_dark"],
                                             int(alpha)), (58, 64), radius)
            _NS_kaizen._aaline(halo, (*_NS_kaizen.PALETTE["wind_mid"], 38),
                               (38, 76), (16, 85), 2)
            _NS_kaizen._aaline(halo, (*_NS_kaizen.PALETTE["wind_light"], 34),
                               (73, 74), (104, 60), 1)
            return halo
        halo = _NS_kaizen._static("rim_halo", build)
        old_a = halo.get_alpha()
        halo.set_alpha(int(255 * pulse))
        surface.blit(halo, (x - 58, y - 64))
        halo.set_alpha(old_a if old_a is not None else 255)

    def _draw_wind_aura(surface, x, y, phase):
        def build():
            aura = pygame.Surface((240, 216), pygame.SRCALPHA)
            for radius in range(96, 6, -4):
                alpha = int((96 - radius) * 1.0)
                if alpha > 0:
                    _NS_kaizen._aacircle(aura,
                                          (*_NS_kaizen.PALETTE["wind_darkest"],
                                           min(255, alpha)),
                                          (120, 108), radius)
            return aura
        aura = _NS_kaizen._static("wind_aura", build)
        pulse = .7 + .3 * math.sin(phase * 0.4)
        old_a = aura.get_alpha()
        aura.set_alpha(int(255 * pulse))
        surface.blit(aura, (x - 120, y - 108))
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
            pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_dark"], 150),
                                (5, 14, 180, 36), 4)
            pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_mid"], 180),
                                (28, 20, 134, 24), 2)
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
            # skill-active: tick kardinal (bukan cincin amateur)
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
        for i in range(8):
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

        # footprint ticks along the wall base (angular, not a ring)
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

        _NS_kaizen._aoe_marks(surface, x, y + 30, int(rng), p["wind_light"],
                              int(130 + 55 * pulse), phase,
                              ticks=16, tick_len=max(8, int(rng * .12)))
        _NS_kaizen._aoe_marks(surface, x, y + 30, max(6, int(rng) - int(6 * fs)),
                              p["wind_mid"], int(105 + 45 * pulse), -phase,
                              ticks=12, corner=False,
                              tick_len=max(6, int(rng * .07)))
        conv = max(12, int(rng * (1 - (progress % .28) * 3.2)))
        _NS_kaizen._aoe_marks(surface, x, y + 30, conv, p["wind_pale"],
                              int(160 + 70 * pulse), phase,
                              ticks=10, corner=False, inner=True,
                              tick_len=max(6, int(conv * .12)))
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _NS_kaizen._chevron(
                surface,
                x + math.cos(da) * rng * .4,
                y + 30 + math.sin(da) * rng * .34,
                da + math.pi, max(8, int(rng * .08)), p["wind_light"], 190, 3)
        _NS_kaizen._aacircle(surface, (*p["wind_bright"], int(200 + 40 * pulse)),
                  (x, y + 30), int((5 + 3 * pulse) * fs))
        for da in (0, math.pi / 2):
            _NS_kaizen._aaline(surface, (*p["wind_light"], 150),
                               (x - math.cos(da) * 14, y + 30 - math.sin(da) * 9),
                               (x + math.cos(da) * 14, y + 30 + math.sin(da) * 9), 1)


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

        for i in range(10):
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

    def draw_boss(surface, boss, x, y):
        _NS_kaizen.draw_kaizen(surface, boss, x, y)


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
            dist = math.sqrt(dx * dx + dy * dy) or 1
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
        for i in range(10):
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


    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
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
                     segments=10, thick=3, span=0.6, squash=.92):
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
        for i in range(8):
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

        # ── AKTIVASI: pilar cahaya + shockwave ganda + bintang ──
        if progress < 0.18:
            t = progress / 0.18
            # 100*fs aman di dalam canvas cache (margin _canvas_size_for)
            top = int(cy - min(100 * fs, 240) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((30, p["rage_dark"], 110),
                                (18, p["rage_mid"], 150),
                                (8, p["rage_light"], 200)):
                _NS_thorne._aaline(surface, (*col, int(al * (1 - t))),
                                   (cx, top), (cx, cy), wd)
            _NS_thorne._aaline(surface, (*p["quill_shine"], int(200 * (1 - t))),
                               (cx, top), (cx, cy), 3)
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
        for i in range(8):
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
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # Rig v2 membesarkan koordinat lokal lama.  Pipeline hero akan
    # mengukur badan dan men-scale kembali ke ukuran arena normal; yang
    # naik adalah kepadatan piksel/detail native.
    RIG_SCALE = 1.52

    # Durasi visual diselaraskan dengan hero_skills/vex_skills.py.
    SKILL_VISUAL_DURATION = {"q": 40, "w": 100, "e": 60, "r": 80}

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


    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
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
                     segments=10, thick=3, span=0.6, squash=.92):
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
                                 phase * 2.8, segments=8, thick=2, span=.40)
            _NS_vex._dashed_ring(surface, px, py, 18, p["void_mid"], 125,
                                 -phase * 1.7, segments=10, thick=1, span=.28)
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
                                p["void_hot"], 240, spikes=4,
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
                for i in range(8):
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
                                     phase * 2.8, segments=8, thick=2,
                                     span=.42)
                _NS_vex._dashed_ring(surface, px, py, 22,
                                     p["astral_mid"], 115,
                                     -phase * 1.6, segments=10, thick=1,
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
                                    spikes=4, rot=self.angle, core=p["white"])


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
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vex._detect_moving(boss)
        _NS_vex._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

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
        if attack and 0.26 < ap < 0.86:
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
        for i in range(10):
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

        for i in range(10):
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
        for i in range(13):
            t1 = i / 12.0
            wob = math.sin(phase * 3.0 + i * .8) * 3.2 * fs
            pts.append((sx + dx * t1 + nx * wob, sy + dy * t1 + ny * wob))
        beam_a = int((120 + 70 * pulse) * steady)
        for i in range(12):
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
        for i in range(12):
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
        for i in range(8):
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
        for i in range(10):
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

        # ── AKTIVASI: pilar 4-lapis + shockwave triple + nova ──
        if progress < .20:
            t = progress / .20
            height = int(min(150 * fs, 240) * (1.0 - .35 * t))
            top = max(2, y - height)
            for wd, col, al in ((36, p["void_darkest"], 100),
                                (24, p["void_dark"], 145),
                                (12, p["void_mid"], 205),
                                (5, p["void_hot"], 245)):
                _NS_vex._aaline(surface, (*col, int(al * (1 - t))),
                                (x, top), (x, gy),
                                max(1, int(wd * fs * .42)))
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
            for i in range(8):
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

        for i in range(10):
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
    SKILL_VISUAL_DURATION = {"q": 240, "w": 180, "e": 180, "r": 240}

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

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
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
                     segments=10, thick=3, span=0.6, squash=.92):
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
            for i in range(8):
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
                ta = phase * .42 + i * .9
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
                          spikes=6, rot=phase * 2.1,
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
            for i in range(8):
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
                for i in range(12):
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
                                segments=12, thick=3)
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
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["q"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        tx_, ty_ = _NS_zephyr._target_position(boss, x, y)
        rng = _NS_zephyr._ring_r(boss, 60, surface)

        # 12 thorn spines around ring
        for i in range(12):
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
        for i in range(8):
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
        fs = _NS_zephyr._fx_scale(boss)
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
                                segments=8, thick=2)
        for i in range(6):
            a_ = phase*.7 + i*math.tau/6
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                 (int(x + math.cos(a_)*(radius-5)),
                                  int(y+31 + math.sin(a_)*radius*.30)), 1)

    def _draw_shadow_realm(surface, boss, x, y, timer, phase):
        """W foreground: glass dome + pilar cahaya 3-lapis + rune ring ganda."""
        p = _NS_zephyr.PALETTE
        fs = _NS_zephyr._fx_scale(boss)
        dur = _NS_zephyr.SKILL_VISUAL_DURATION["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        envelope = min(1.0, progress*5.0, (1.0-progress)*5.0)
        rng = _NS_zephyr._ring_r(boss, 100, surface)

        # ACTIVATION pillar of light (first 20%)
        if progress < .20:
            t = progress / .20
            pil_h = min(int(120 * t * fs), rng)
            for layer, (col_, pal_) in enumerate(
                    ((p["magic_dark"], 80), (p["magic_mid"], 130),
                     (p["magic_bright"], 200))):
                lw = max(1, (6-layer*2))
                _NS_zephyr._aaline(surface,
                                   (*col_, int(pal_*(1-t))),
                                   (x, y), (x, y-pil_h), lw)
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
        for i in range(8):
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
        for i in range(10):
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

        # ACTIVATION: pillar burst
        if progress < .12:
            t = progress / .12
            for layer, (col_, pal_) in enumerate(
                    ((p["magic_dark"], 90), (p["magic_mid"], 140),
                     (p["magic_bright"], 210), (p["magic_hot"], 250))):
                lw = max(1, 8-layer*2)
                pil = min(int(100*t*fs), rng)
                _NS_zephyr._aaline(surface, (*col_, int(pal_*(1-t))),
                                   (x, y), (x, y-pil), lw)
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
        for i in range(8):
            a_ = phase*.5 + i*math.tau/8
            cx__ = int(x + math.cos(a_)*radius*.72)
            cy__ = int(y+31 + math.sin(a_)*radius*.22)
            _NS_zephyr._chevron(surface, cx__, cy__,
                                a_ + math.pi, int(9*fs),
                                p["rune_light"],
                                int(140 + math.sin(phase*2+i)*40), 2)

        # Rune dots orbiting
        for i in range(10):
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
        for i in range(24):
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

        # Pilar cahaya (ACTIVE phase) — 4 layers, clamped height
        if envelope > .05:
            pil = min(int(90*envelope*fs), rng-4)
            for layer, (col_, pal_) in enumerate(
                    ((p["magic_dark"], 80), (p["magic_mid"], 120),
                     (p["magic_bright"], 180), (p["magic_hot"], 230))):
                lw = max(1, 7-layer*2)
                _NS_zephyr._aaline(surface,
                                   (*col_, int(pal_*envelope)),
                                   (x, y), (x, y-pil), lw)
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
        bedlam_on    = (active_skill == "r")
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
