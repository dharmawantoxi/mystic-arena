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

    def _clamp(color):
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
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
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
        color = _NS_grimjaw._clamp(color)
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

        # Main body (with attack pose)
        _NS_grimjaw._draw_grimjaw_body(surface, x + offset_x, y + offset_y,
                           hero.direction, phase, "attack", 0.6,
                           detail=False, omni=True)


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
        buf = _NS_grimjaw._GHOST_BUF.get(key)
        if buf is None:
            if len(_NS_grimjaw._GHOST_BUF) > 24:
                _NS_grimjaw._GHOST_BUF.clear()
            buf = pygame.Surface((220, 220), pygame.SRCALPHA)
            _NS_grimjaw._draw_grimjaw_elite(
                buf, 110, 118, f, 1.0, "attack", q, 0.0, False)
            _NS_grimjaw._GHOST_BUF[key] = buf
        buf.set_alpha(alpha)
        surface.blit(buf, (int(cx) - 110, int(cy) - 118))
        buf.set_alpha(255)


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
        steps = 12
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
            _NS_grimjaw._aacircle(surface, (*p["fire_dark"], alpha),
                                  (ax, ay), max(1, int(base * taper * 0.75)))
            _NS_grimjaw._aacircle(surface, (*p["fire_mid"], alpha),
                                  (ax, ay), max(1, int(base * taper * 0.55)))
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
            faded = mist.copy()
            faded.set_alpha(int(255 * pulse))
            surface.blit(faded, (cx - 85, cy - 16))
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
            faded = aura.copy()
            faded.set_alpha(int(255 * pulse))
            surface.blit(faded, (x - 120, y - 110))
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
        faded = aura.copy()
        faded.set_alpha(int(255 * pulse))
        surface.blit(faded, (x - 140, y - 130))

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
        """Telegraph + steady ground Blade Fury (world-space).

        Ring jangkauan = skill_range (70 dunia) dikonversi ke px canvas
        lewat _render_scale supaya pas dengan AOE gameplay; ring
        konvergen mengecil ke pusat membaca "spin incoming".
        """
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 180.0))
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        fs = _NS_grimjaw._fx_scale(hero)
        gy = y + 58

        spin_range = int(getattr(hero, "skill_range", 70) or 70)
        rng = _NS_grimjaw._ring_r(hero, spin_range, surface)

        # ── AKTIVASI: shockwave ganda + bintang ──
        if progress < 0.14:
            t = progress / 0.14
            for k, rmax in ((0, int(95 * fs)), (1, int(68 * fs))):
                r = int((22 + t * rmax) * (1 if k else 1))
                alpha = int((235 if k == 0 else 165) * (1 - t))
                _skill_outlined_circle(surface, (x, y), r, 3,
                                       p["fire_hot"] if k == 0 else p["fire_light"],
                                       alpha)
            _NS_grimjaw._spark_star(surface, x, y, int(30 * (1 - t * .5)),
                                    p["fire_hot"], int(240 * (1 - t)),
                                    8, rot=phase, core=p["white"])

        # ── STEADY: ellipse tanah (cached feel) + ring konvergen ──
        _NS_grimjaw._ellipse(surface, (*p["fire_darkest"], int(90 + 40 * pulse)),
                             (int(x - rng * 0.55), int(gy - rng * 0.16),
                              int(rng * 1.1), int(rng * 0.32)), 0)
        _skill_outlined_circle(surface, (x, y), rng, 4,
                               p["fire_light"], int(110 + 50 * pulse))
        _NS_grimjaw._dashed_ring(surface, x, y, int(rng * 0.88),
                                 p["fire_mid"], int(130 + 60 * pulse),
                                 phase * 1.2, segments=12, thick=3, span=.3)
        # ring konvergen: mengecil ke pusat (telegraph "incoming")
        conv = rng * (1 - progress * 0.80)
        _skill_outlined_circle(surface, (x, y), max(12, int(conv)), 3,
                               p["fire_hot"], int(150 + 70 * pulse))
        # chevron kardinal menunjuk ke dalam
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _NS_grimjaw._chevron(
                surface,
                x + math.cos(da) * rng * 0.62,
                y + math.sin(da) * rng * 0.55,
                da + math.pi, max(9, int(rng * 0.11)), p["fire_light"], 190, 3)
        # orb pusat berdenyut
        _NS_grimjaw._aacircle(surface,
                              (*p["fire_hot"], int(200 + 40 * pulse)),
                              (x, y), int(5 + 3 * pulse))

    def _draw_blade_fury_rings(surface, x, y, phase):
        """Fire rings spinning around character during Blade Fury."""
        p = _NS_grimjaw.PALETTE
        for ring_i in range(2):
            ring_phase = phase * 3 + ring_i * 1.5
            ring_radius = 34 + ring_i * 9
            # Ring is horizontal ellipse (ground-level)
            for i in range(12):
                angle = ring_phase + i * math.tau / 12
                px = x + int(math.cos(angle) * ring_radius)
                py = y + int(math.sin(angle) * ring_radius * 0.4)
                _NS_grimjaw._aacircle(surface, p["fire_darkest"], (px, py), 5)
                _NS_grimjaw._aacircle(surface, p["fire_dark"], (px, py), 3)
                _NS_grimjaw._aacircle(surface, p["fire_mid"], (px, py), 2)
                _NS_grimjaw._aacircle(surface, p["fire_light"], (px, py), 1)

    def _draw_fire_particles_orbit(surface, x, y, phase):
        """Fire particles orbiting during spinning."""
        p = _NS_grimjaw.PALETTE
        for i in range(14):
            p_phase = phase * 4 + i * 0.5
            p_angle = p_phase
            p_dist = 34 + int(math.sin(p_phase * 2) * 12)

            px = x + int(math.cos(p_angle) * p_dist)
            py = y + int(math.sin(p_angle) * p_dist * 0.5)

            _NS_grimjaw._aacircle(surface, p["fire_dark"], (px, py), 3)
            _NS_grimjaw._aacircle(surface, p["fire_hot"], (px, py), 2)
            _NS_grimjaw._aacircle(surface, p["fire_core"], (px, py), 1)

    # ===================================================================
    # SKILL W: HEALING WARD (visual 90 frame)
    # ===================================================================
    def _draw_healing_ward_ground(surface, hero, x, y, timer, phase):
        """Ground layer of healing ward (world-space).

        Ring jangkauan = radius heal 100 dunia, dikonversi lewat
        _render_scale; ring konvergen di 30% pertama = telegraph.
        """
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 90.0))
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        fs = _NS_grimjaw._fx_scale(hero)
        rng = _NS_grimjaw._ring_r(hero, 100, surface)
        gy = y + 58

        # ── AKTIVASI: shockwave hijau + bintang ──
        if progress < 0.18:
            t = progress / 0.18
            for k, rmax in ((0, int(100 * fs)), (1, int(72 * fs))):
                r = int((20 + t * rmax))
                alpha = int((230 if k == 0 else 160) * (1 - t))
                _skill_outlined_circle(surface, (x, y), r, 3,
                                       p["heal_light"] if k == 0 else p["heal_mid"],
                                       alpha)
            _NS_grimjaw._spark_star(surface, x, y, int(28 * (1 - t * .5)),
                                    p["heal_light"], int(240 * (1 - t)),
                                    8, rot=phase, core=p["heal_core"])

        # ── STEADY: lingkaran penyembuh 2 lapis + rune berputar ──
        _NS_grimjaw._ellipse(surface, (*p["heal_darkest"], int(80 + 30 * pulse)),
                             (int(x - rng * 0.55), int(gy - rng * 0.15),
                              int(rng * 1.1), int(rng * 0.30)), 0)
        _skill_outlined_circle(surface, (x, y), rng, 4,
                               p["heal_mid"], int(120 + 50 * pulse))
        _NS_grimjaw._dashed_ring(surface, x, y, int(rng * 0.86),
                                 p["heal_light"], int(130 + 60 * pulse),
                                 phase * 0.9, segments=10, thick=3, span=.5)
        # rune dots berputar
        for i in range(8):
            a = phase * 0.35 + i * math.pi / 4
            px = x + int(math.cos(a) * (rng - 8))
            py = y + int(math.sin(a) * (rng * 0.5 - 5))
            _NS_grimjaw._aacircle(surface,
                                  (*p["heal_core"], int(220 * pulse)), (px, py), 3)
            _NS_grimjaw._rect(surface, p["white"], (px, py, 1, 1))
        # ring konvergen (telegraph awal)
        if progress < 0.4:
            t = progress / 0.4
            conv = rng * (1 - t * 0.75)
            _skill_outlined_circle(surface, (x, y), max(12, int(conv)), 3,
                                   p["heal_light"], int(180 * (1 - t) + 60))

    def _draw_healing_ward_totem(surface, hero, x, y, timer, phase):
        """Green healing totem beside Grimjaw + pilar cahaya aktivasi."""
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 90.0))
        facing = getattr(hero, "direction", 1)
        fs = _NS_grimjaw._fx_scale(hero)
        wx = x + int(52 * fs * (1 if facing >= 0 else -1))
        wy = y + int(34 * fs)

        # ── AKTIVASI: pilar cahaya 4-lapis + bintang (clamped) ──
        if progress < 0.2:
            t = progress / 0.2
            top = wy - int(min(110 * fs, 240) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((26, p["heal_dark"], 100),
                                (15, p["heal_mid"], 150),
                                (7, p["heal_light"], 210)):
                _NS_grimjaw._aaline(surface, (*col, int(al * (1 - t))),
                                    (wx, int(top)), (wx, wy), wd)
            _NS_grimjaw._spark_star(surface, wx, wy, int(22 * (1 - t * .5)),
                                    p["heal_light"], int(235 * (1 - t)),
                                    6, rot=phase, core=p["heal_core"])

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
        # Glowing orb on top (4 band + core)
        pulse = math.sin(phase) * 0.3 + 0.7

        def build_glow():
            glow = pygame.Surface((44, 44), pygame.SRCALPHA)
            for r in range(18, 0, -1):
                alpha = min(255, max(0, int(150 - r * 8)))
                if alpha > 0:
                    pygame.draw.circle(glow, (*p["heal_mid"], alpha), (22, 22), r)
            return glow
        glow = _NS_grimjaw._static("heal_glow", build_glow)
        faded = glow.copy()
        faded.set_alpha(int(160 + 80 * pulse))
        surface.blit(faded, (wx - 22, wy - 12 - 22))

        _NS_grimjaw._aacircle(surface, p["heal_darkest"], (wx, wy - 12), 8)
        _NS_grimjaw._aacircle(surface, p["heal_dark"], (wx, wy - 12), 7)
        _NS_grimjaw._aacircle(surface, p["heal_mid"], (wx - 1, wy - 13), 5)
        _NS_grimjaw._aacircle(surface, p["heal_light"], (wx - 1, wy - 13), 4)
        _NS_grimjaw._rect(surface, p["heal_core"], (wx - 1, wy - 13, 2, 2))
        _NS_grimjaw._rect(surface, p["white"], (wx - 1, wy - 13, 1, 1))
        # glint orbit
        for i in range(4):
            a = phase * 2.2 + i * math.pi / 2
            gx = int(wx + math.cos(a) * 12)
            gy = int(wy - 12 + math.sin(a) * 12)
            _NS_grimjaw._aacircle(surface, (*p["heal_light"], 200), (gx, gy), 1)

        # Floating + heal symbols
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
        """Heal aura around Grimjaw when Healing Ward active (cached)."""
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
        faded = aura.copy()
        faded.set_alpha(int(150 + 70 * pulse))
        surface.blit(faded, (x - 65, y - 65))

        # Ground ring particles
        for i in range(14):
            angle = i * math.pi / 7 + phase
            rx = x + int(math.cos(angle) * 38)
            ry = y + int(math.sin(angle) * 14) + 22
            _NS_grimjaw._aacircle(surface, p["heal_light"], (rx, ry), 2)
            _NS_grimjaw._rect(surface, p["heal_core"], (rx, ry, 1, 1))

        # Rising + symbols around body
        for i in range(6):
            phase_i = (phase * 1.5 + i * 0.3) % 1.0
            angle = i * math.pi / 3
            px = x + int(math.cos(angle) * 30)
            py = y + 24 - int(phase_i * 48)
            alpha = int(220 * (1 - phase_i))
            if alpha > 0:
                _NS_grimjaw._rect(surface, (*p["heal_light"], alpha),
                                  (px - 1, py - 4, 2, 9))
                _NS_grimjaw._rect(surface, (*p["heal_light"], alpha),
                                  (px - 4, py - 1, 9, 2))

    # ===================================================================
    # SKILL E: CRITICAL STRIKE (buff 60 frame visual)
    # ===================================================================
    def _draw_crit_telegraph(surface, hero, x, y, timer, phase):
        """Telegraph Critical Strike (world-space): cone 60 dunia di arah
        hadap + chevron berbaris + retakan api di tanah."""
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 60.0))
        if progress > 0.5:
            return
        facing = getattr(hero, "direction", 1)
        fs = _NS_grimjaw._fx_scale(hero)
        pulse = math.sin(phase * 6) * 0.5 + 0.5
        fade = 1.0 - progress / 0.5
        gy = y + 56

        # ellipse cone di depan
        rng = _NS_grimjaw._ring_r(hero, 60, surface)
        ox = int(x + rng * 0.55 * (1 if facing >= 0 else -1))
        _NS_grimjaw._ellipse(surface, (*p["fire_darkest"], int(120 * fade * pulse)),
                             (int(ox - rng * 0.55), int(gy - rng * 0.14),
                              int(rng * 1.1), int(rng * 0.28)), 0)
        _skill_outlined_circle(surface, (ox, y), rng, 3,
                               p["fire_light"], int(140 * fade * pulse + 40))
        # chevron berbaris menuju depan
        for i in range(3):
            t = (i / 3 + phase * 0.5) % 1.0
            _NS_grimjaw._chevron(surface,
                                 x + facing * rng * (0.3 + 0.62 * t),
                                 y + 8, 0.0 if facing > 0 else math.pi,
                                 14, p["fire_hot"], int(210 * fade), 3)
        # retakan api di tanah (deterministik)
        for i in range(5):
            ang = (0.3 + i * 0.45) * (1 if facing > 0 else -1) + math.pi / 2 * (0 if facing > 0 else 1)
            _NS_grimjaw._jagged_crack(
                surface, x + facing * 18, gy, ang,
                int((20 + (i % 3) * 8) * fs),
                (p["fire_darkest"], p["fire_mid"]), int(150 * fade),
                seed=i + 21, width=2)

    def _draw_crit_steady(surface, hero, x, y, timer, phase):
        """Steady Critical Strike: glint orbit di blade, rune ring merah,
        mote naik - blade di badan sudah menyala incandescent (kwarg crit)."""
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 60.0))
        fs = _NS_grimjaw._fx_scale(hero)
        facing = getattr(hero, "direction", 1)
        pulse = math.sin(phase * 5) * 0.5 + 0.5

        # AKTIVASI: bintang + shockwave
        if progress < 0.15:
            t = progress / 0.15
            tipx, tipy = _NS_grimjaw._blade_tip_local(0.0, "idle", 0.0)
            hx, hy = int(x + tipx * facing), int(y + tipy)
            _NS_grimjaw._spark_star(surface, hx, hy, int(24 * (1 - t * .4)),
                                    p["fire_hot"], int(240 * (1 - t)),
                                    7, rot=phase, core=p["white"])
            r = int((16 + t * int(70 * fs)))
            _skill_outlined_circle(surface, (hx, hy), r, 3,
                                   p["fire_light"], int(200 * (1 - t)))
            return

        # glint orbit mengelilingi blade (3 titik)
        tipx, tipy = _NS_grimjaw._blade_tip_local(0.0, "idle", 0.0)
        hx, hy = int(x + tipx * facing), int(y + tipy)
        for i in range(3):
            a = phase * 3.0 + i * math.tau / 3
            gx = int(hx + math.cos(a) * 16)
            gy = int(hy + math.sin(a) * 16)
            _NS_grimjaw._aacircle(surface, (*p["fire_hot"], 220), (gx, gy), 2)
            _NS_grimjaw._aacircle(surface, p["white"], (gx, gy), 1)
        # rune ring merah kecil di sekeliling badan
        _NS_grimjaw._dashed_ring(surface, x, y - 6, int(52 * fs),
                                 p["rage_mid"], int(120 + 60 * pulse),
                                 -phase * 1.3, segments=8, thick=2, span=.45)
        # mote bara naik
        for i in range(7):
            t = (phase * 0.35 + i / 7) % 1.0
            mx = x + int(math.sin(i * 2.2) * 34 * fs)
            my = y + 26 - int(t * 70 * fs)
            _NS_grimjaw._aacircle(surface,
                                  (*p["rage_bright"], int(190 * (1 - t))),
                                  (mx, my), 2 if i % 2 else 1)

    # ===================================================================
    # SKILL R: OMNISLASH (90 frame)
    # ===================================================================
    def _draw_omnislash_ground(surface, hero, x, y, timer, phase):
        """Ground Omnislash (world-space): retakan api radial + ring
        berputar + glow lantai."""
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 90.0))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        fs = _NS_grimjaw._fx_scale(hero)
        gy = y + 58
        rng = _NS_grimjaw._ring_r(hero, 80, surface)

        # ── AKTIVASI: pilar cahaya 4-lapis + shockwave ganda + bintang ──
        if progress < 0.18:
            t = progress / 0.18
            top = int(y - min(110 * fs, 240) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((34, p["rage_dark"], 110),
                                (20, p["rage_mid"], 155),
                                (9, p["rage_light"], 210),
                                (3, p["fire_hot"], 235)):
                _NS_grimjaw._aaline(surface, (*col, int(al * (1 - t))),
                                    (x, top), (x, y), wd)
            for k, rmax in ((0, int(120 * fs)), (1, int(86 * fs))):
                r = int((16 + t * rmax))
                _skill_outlined_circle(surface, (x, y), r, 3,
                                       p["rage_bright"] if k == 0 else p["fire_hot"],
                                       int((225 if k == 0 else 150) * (1 - t)))
            _NS_grimjaw._spark_star(surface, x, y, int(32 * (1 - t * .4)),
                                    p["fire_hot"], int(235 * (1 - t)),
                                    8, rot=.3, core=p["white"])

        # ── STEADY: glow lantai + ring + retakan radial ──
        _NS_grimjaw._ellipse(surface, (*p["rage_dark"], int(95 + 40 * pulse)),
                             (int(x - rng * 0.55), int(gy - rng * 0.15),
                              int(rng * 1.1), int(rng * 0.30)), 0)
        _skill_outlined_circle(surface, (x, y), rng, 4,
                               p["rage_light"], int(120 + 60 * pulse))
        _NS_grimjaw._dashed_ring(surface, x, y, int(rng * 0.85),
                                 p["fire_hot"], int(140 + 60 * pulse),
                                 phase * 1.4, segments=10, thick=3, span=.32)
        _NS_grimjaw._dashed_ring(surface, x, y, int(rng * 0.6),
                                 p["rage_bright"], int(110 + 50 * pulse),
                                 -phase * 1.1, segments=8, thick=2, span=.4)
        # retakan api radial (5)
        for i in range(5):
            ang = i * math.pi * 2 / 5 + 0.35
            _NS_grimjaw._jagged_crack(surface, x, gy, ang,
                                      int((28 + (i % 3) * 10) * fs),
                                      (p["rage_dark"], p["rage_mid"]), 150,
                                      seed=i + 31, width=2)
        # denyut pusat
        _NS_grimjaw._aacircle(surface,
                              (*p["rage_bright"], int(150 * pulse)),
                              (x, y), int(18 + 5 * pulse))
        _NS_grimjaw._aacircle(surface,
                              (*p["fire_hot"], int(210 * pulse)),
                              (x, y), int(8 + 3 * pulse))

    def _draw_omnislash_slashes(surface, hero, x, y, timer, phase):
        """Multiple fire slashes emanating from Grimjaw (retune rig v2):
        8 streak radial + core flash + orbit shards."""
        p = _NS_grimjaw.PALETTE
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
            _NS_grimjaw._aaline(surface, (*p["fire_darkest"], alpha),
                                (slash_x, slash_y),
                                (slash_x + end_x, slash_y + end_y), 7)
            _NS_grimjaw._aaline(surface, (*p["fire_dark"], alpha),
                                (slash_x, slash_y),
                                (slash_x + end_x, slash_y + end_y), 5)
            _NS_grimjaw._aaline(surface, (*p["fire_mid"], alpha),
                                (slash_x, slash_y),
                                (slash_x + end_x, slash_y + end_y), 3)
            _NS_grimjaw._aaline(surface, (*p["fire_hot"], alpha),
                                (slash_x, slash_y),
                                (slash_x + end_x, slash_y + end_y), 2)
            _NS_grimjaw._aaline(surface, (*p["fire_core"], alpha),
                                (slash_x, slash_y),
                                (slash_x + end_x, slash_y + end_y), 1)
            _NS_grimjaw._aacircle(surface, (*p["white"], alpha),
                                  (slash_x + end_x, slash_y + end_y), 2)

        # orbit shards (mini blade quill)
        for i in range(6):
            a = phase * 2.6 + i * math.tau / 6
            r = 58 + int(math.sin(phase * 2 + i) * 8)
            sx = int(x + math.cos(a) * r)
            sy = int(y + math.sin(a) * r * 0.55)
            _NS_grimjaw._aaline(surface, (*p["fire_mid"], 190),
                                (sx, sy), (sx - int(math.cos(a) * 12),
                                           sy - int(math.sin(a) * 7)), 3)
            _NS_grimjaw._aaline(surface, (*p["fire_hot"], 220),
                                (sx, sy), (sx - int(math.cos(a) * 9),
                                           sy - int(math.sin(a) * 5)), 1)

        # Central bright flash
        core_pulse = math.sin(phase * 6) * 0.3 + 0.7
        _NS_grimjaw._aacircle(surface, (*p["fire_hot"], int(180 * core_pulse)),
                              (x, y), int(9 * core_pulse))
        _NS_grimjaw._aacircle(surface, p["fire_core"], (x, y), int(4 * core_pulse))

    def _draw_omnislash_target(surface, hero, x, y, timer, phase):
        """Target-lock indicator: garis putus ke target + cincin + chevron."""
        p = _NS_grimjaw.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 90.0))
        pulse = math.sin(phase * 6) * 0.5 + 0.5
        tx, ty = _NS_grimjaw._target_position(hero, x, y)
        if (tx, ty) == (x, y):
            return
        ang = math.atan2(ty - y, tx - x)
        dist = math.hypot(tx - x, ty - y)
        # dashed line
        for i in range(0, 12, 2):
            t1 = i / 12
            t2 = min(1.0, (i + 0.7) / 12)
            _skill_outlined_line(
                surface,
                (x + (tx - x) * t1, y + (ty - y) * t1 - 6),
                (x + (tx - x) * t2, y + (ty - y) * t2 - 6),
                2, p["rage_light"], 190)
        # chevron menuju target (berdenyut)
        for i in range(3):
            t = (i / 3 + phase * 0.6) % 1.0
            _NS_grimjaw._chevron(surface,
                                 x + (tx - x) * t, y + (ty - y) * t - 6,
                                 ang, 13, p["fire_hot"],
                                 int(160 + 80 * pulse * (1 - t)), 3)
        # cincin target
        _skill_outlined_circle(surface, (tx, ty - 6), 20, 3,
                               p["rage_light"], int(150 + 60 * pulse))
        _skill_outlined_circle(surface, (tx, ty - 6), 12, 2,
                               p["fire_hot"], int(180 + 50 * pulse))
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
    """Namespace sylara - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

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

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),

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
    # PROJECTILE SYSTEM - Wind Arrow
    # ---------------------------------------------------------------------------
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

            # Trail - wind wisps
            trail_intensity = 2 if self.powered else 1
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12) * trail_intensity
                alpha = min(255, alpha)
                r = max(1, (7 if self.powered else 5) - (len(self.trail) - i))
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha), (tx, ty), r + 2)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_light"], min(255, alpha // 2)),
                          (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                if self.powered:
                    # Powershot - large glowing green arrow
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], 150), (px, py), 18)
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], 200), (px, py), 12)

                    # Large arrow shaft
                    length = 22
                    tip_x = px + ca * length
                    tip_y = py + sa * length
                    tail_x = px - ca * length
                    tail_y = py - sa * length

                    # Glow shaft
                    _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_bright"], 220),
                            (tail_x, tail_y), (tip_x, tip_y), 5)
                    _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_white"], 240),
                            (tail_x, tail_y), (tip_x, tip_y), 3)
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["white"],
                            (tail_x, tail_y), (tip_x, tip_y), 1)

                    # Arrowhead
                    perp_x = -sa * 6
                    perp_y = ca * 6
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_bright"], [
                        (tip_x + ca * 8, tip_y + sa * 8),
                        (tip_x + perp_x, tip_y + perp_y),
                        (tip_x - perp_x, tip_y - perp_y),
                    ])
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_white"], [
                        (tip_x + ca * 7, tip_y + sa * 7),
                        (tip_x + perp_x * 0.6, tip_y + perp_y * 0.6),
                        (tip_x - perp_x * 0.6, tip_y - perp_y * 0.6),
                    ])
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["white"],
                              (int(tip_x + ca * 7), int(tip_y + sa * 7)), 2)

                    # Wind spiral around powershot
                    for i in range(5):
                        a = phase * 3 + i * math.pi * 2 / 5
                        r = 12
                        sx = px + math.cos(a) * r
                        sy = py + math.sin(a) * r
                        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], 180),
                                  (int(sx), int(sy)), 2)
                else:
                    # Normal arrow
                    length = 14
                    tip_x = px + ca * length
                    tip_y = py + sa * length
                    tail_x = px - ca * length
                    tail_y = py - sa * length

                    # Glow
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], 100), (px, py), 8)
                    _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], 130), (px, py), 5)

                    # Arrow shaft
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["arrow_shaft_d"],
                            (tail_x, tail_y), (tip_x, tip_y), 3)
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["arrow_shaft"],
                            (tail_x, tail_y), (tip_x, tip_y), 2)
                    _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wood_shine"],
                            (tail_x, tail_y), (tip_x, tip_y), 1)

                    # Arrowhead
                    perp_x = -sa * 3
                    perp_y = ca * 3
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_head_d"], [
                        (tip_x + ca * 5, tip_y + sa * 5),
                        (tip_x + perp_x, tip_y + perp_y),
                        (tip_x - perp_x, tip_y - perp_y),
                    ])
                    _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_head"], [
                        (tip_x + ca * 4, tip_y + sa * 4),
                        (tip_x + perp_x * 0.6, tip_y + perp_y * 0.6),
                        (tip_x - perp_x * 0.6, tip_y - perp_y * 0.6),
                    ])
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["white"],
                              (int(tip_x + ca * 4), int(tip_y + sa * 4)), 1)

                    # Fletching (feathers)
                    for f_off in (2, -2):
                        fp_x = -sa * f_off
                        fp_y = ca * f_off
                        _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_feather_d"], [
                            (tail_x, tail_y),
                            (tail_x + ca * 4, tail_y + sa * 4),
                            (tail_x + ca * 3 + fp_x, tail_y + sa * 3 + fp_y),
                        ])
                        _NS_sylara._poly(surface, _NS_sylara.PALETTE["arrow_feather"], [
                            (tail_x + ca * 1, tail_y + sa * 1),
                            (tail_x + ca * 4, tail_y + sa * 4),
                            (tail_x + ca * 3 + fp_x * 0.7,
                             tail_y + sa * 3 + fp_y * 0.7),
                        ])


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
            # Swirling trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 14)
                # Spiral around trail
                spiral_off = math.sin(phase * 3 + i * 0.5) * 3
                perp = self.angle + math.pi / 2
                sx = tx + math.cos(perp) * spiral_off
                sy = ty + math.sin(perp) * spiral_off
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_light"], alpha),
                          (int(sx), int(sy)), 3)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                          (int(sx), int(sy)), 1)

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                # Glow
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], 130), (px, py), 10)
                _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], 170), (px, py), 7)

                # Arrow with binding energy
                length = 14
                tip_x = px + ca * length
                tip_y = py + sa * length
                tail_x = px - ca * length
                tail_y = py - sa * length

                _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wood_dark"],
                        (tail_x, tail_y), (tip_x, tip_y), 3)
                _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wind_bright"],
                        (tail_x, tail_y), (tip_x, tip_y), 2)
                _NS_sylara._aaline(surface, _NS_sylara.PALETTE["wind_white"],
                        (tail_x, tail_y), (tip_x, tip_y), 1)

                # Vine wraps spiraling around
                for i in range(4):
                    t = i / 4.0
                    spiral_a = phase * 6 + i * math.pi / 2
                    spiral_r = 4
                    cx = px + ca * (t - 0.5) * length
                    cy = py + sa * (t - 0.5) * length
                    perp = self.angle + math.pi / 2
                    sx = cx + math.cos(perp) * math.cos(spiral_a) * spiral_r
                    sy = cy + math.sin(perp) * math.cos(spiral_a) * spiral_r
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["wind_bright"],
                              (int(sx), int(sy)), 2)
                    _NS_sylara._aacircle(surface, _NS_sylara.PALETTE["wind_white"],
                              (int(sx), int(sy)), 1)

                # Arrowhead
                perp_x = -sa * 4
                perp_y = ca * 4
                _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_dark"], [
                    (tip_x + ca * 6, tip_y + sa * 6),
                    (tip_x + perp_x, tip_y + perp_y),
                    (tip_x - perp_x, tip_y - perp_y),
                ])
                _NS_sylara._poly(surface, _NS_sylara.PALETTE["wind_bright"], [
                    (tip_x + ca * 5, tip_y + sa * 5),
                    (tip_x + perp_x * 0.6, tip_y + perp_y * 0.6),
                    (tip_x - perp_x * 0.6, tip_y - perp_y * 0.6),
                ])


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
            _NS_sylara._draw_wind_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        # Q = Focus Fire, W = Windrun, E = Shackle Shot, R = Powershot
        # (sesuai hero_skills/sylara_skills.py)
        if active_skill == "e":
            _NS_sylara._draw_shackle_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_sylara._draw_focus_fire_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sylara._draw_windrun_ground(surface, boss, x, y, skill_timer, pulse)

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
    def _draw_sylara_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x, y + 48)
            _NS_sylara._draw_floating_wind(surface, x, y + 35, boss.pulse)
        _NS_sylara._draw_sylara_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_sylara_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x + sway, y + 48)
            _NS_sylara._draw_floating_wind(surface, x + sway, y + 35, phase,
                                           trail=True, facing=boss.direction)
        _NS_sylara._draw_sylara_body(
            surface, x + sway, y - bob, boss.direction, phase, "walk",
            detail=getattr(boss, "_portrait_hd", False))


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
            _NS_sylara._draw_shadow(surface, x + recoil, y + 48)
            _NS_sylara._draw_floating_wind(surface, x + recoil, y + 35,
                                           boss.pulse, intense=True)
        _NS_sylara._draw_sylara_body(surface, x + recoil, y, boss.direction,
                                     boss.pulse, "attack", progress,
                                     powered=powered, detail=portrait_hd)
        if not portrait_hd:
            _NS_sylara._draw_bow_release_flash(surface, x + recoil, y,
                                               boss.direction, progress)


    def _draw_sylara_windrun(surface, boss, x, y, timer):
        """Fast dash pose during windrun."""
        phase = boss.pulse * 3.0
        bob = int(abs(math.sin(phase * 2)) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_sylara._draw_shadow(surface, x, y + 48)
            _NS_sylara._draw_windrun_trail(surface, x, y, boss.direction, phase)
        _NS_sylara._draw_sylara_body(
            surface, x, y - bob, boss.direction, phase, "windrun",
            detail=getattr(boss, "_portrait_hd", False))


    # ===================================================================
    # BODY RENDERING - HD Wind Ranger
    # ===================================================================
    def _draw_sylara_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, powered=False, detail=False):
        """Renderer tubuh Sylara kualitas maksimum, 100% procedural.

        Dibangun sebagai bone rig 2D berlapis seperti Kaizen/Thorne
        Masterwork: cape hijau per-panel yang beranimasi, quiver berisi
        anak panah, korset kulit ber-strap, hood runcing dengan rambut
        merah menyembul, dan busur recurve yang posenya dihitung dari
        sendi (grip, nock, tarikan tali). Tidak ada PNG, sprite sheet,
        ataupun image.load.
        """
        _NS_sylara._draw_sylara_elite(
            surface, cx, cy, facing, phase, action, attack_progress,
            powered=powered, detail=detail)


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
    RIG_W, RIG_H = 156, 136
    RIG_OX, RIG_OY = 66, 62


    def _draw_sylara_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, powered=False, detail=False):
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

        lean = (3 if walk else 0) * f
        if windrun:
            lean = 7 * f
        root_y = int(math.sin(phase * .72) * .7)
        # v2 (animasi): perpindahan berat badan saat idle — goyang kiri-kanan.
        sway = int(math.sin(phase * .8) * 3) * f if not (walk or attack or windrun) else 0
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if windrun:
            root_y += 2 - int(abs(math.sin(phase * 2.0)) * 2)
        if attack:
            lean = int(math.sin(ap * math.pi) * 3) * f
            root_y += int(math.sin(ap * math.pi) * 1.5)

        def pt(dx, dy):
            return (int(cx + dx * f + lean + sway), int(cy + dy + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                _NS_sylara._poly(surface, p["shadow_deep"],
                                 [(x + f, y + 1) for x, y in pts])
            _NS_sylara._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_sylara._aaline(surface, p["shadow_deep"], aa, bb, width + 3)
            _NS_sylara._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_sylara._aaline(surface, light,
                                   (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, width // 3))

        wave = math.sin(phase * 1.15)
        wave2 = math.sin(phase * 1.45 + .8)
        # angin: cape & rambut terhempas lebih jauh saat bergerak/menembak
        gust = 0
        if walk:
            gust = 6
        elif windrun:
            gust = 16
        elif attack:
            gust = int(4 + 5 * math.sin(ap * math.pi))

        # ═══ CAPE: panel gelap sempit di punggung + tepi robek ═══
        cw = int(wave * 3)
        cw2 = int(wave2 * 2)
        poly(p["cloak_darkest"], [
            (-3, -34), (-8, -35),
            (-15 - gust, -24 + cw), (-20 - gust, -8 + cw),
            (-17 - int(gust * .8), 6 + cw2), (-11, 18 + cw2),
            (-4, 14), (-2, 0)])
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
            if ap < .45:
                t = ap / .45
                draw_amt = t * t * (3 - 2 * t)
                grip = (19 - int(t * 2), -14)
                tilt = .30 - t * .26
            elif ap < .58:
                t = (ap - .45) / .13
                draw_amt = max(0.0, 1.0 - t * 1.4)
                grip = (17 + int(t * 2), -14)
                tilt = .04
            else:
                t = (ap - .58) / .42
                draw_amt = 0.0
                grip = (19 - int(t * 3), -14 + int(t * 4))
                tilt = .04 + t * .40
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
                _NS_sylara._aacircle(surface,
                                     (*p["wind_light"], int(110 * (1 - t))),
                                     (mx, my), 1)

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
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sylara._aacircle(aura, (*_NS_sylara.PALETTE["wind_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_wind_platform(surface, x, y, phase, skill):
        """Wind circle platform with leaf pattern."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_mid"], 180),
                            (20, 14, 90, 16), 2)

        # Swirling wind streaks
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_sylara.PALETTE["wind_light"], 170),
                             (x1, y1), (x2, y2), 1)

        # Small leaves around ring
        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_sylara.PALETTE["wind_bright"], 200), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_bow_release_flash(surface, x, y, facing, progress):
        """Flash when releasing arrow."""
        # Flash occurs at release moment
        if progress < 0.55 or progress > 0.75:
            return
        t = (progress - 0.55) / 0.2
        intensity = math.sin(t * math.pi)

        flash_x = x + 22 * facing
        flash_y = y - 8

        alpha = int(200 * intensity)
        radius = int(4 + intensity * 12)

        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 4)
        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                  (flash_x, flash_y), radius)
        _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], alpha),
                  (flash_x, flash_y), radius // 2)

        # Small streaks
        for i in range(4):
            angle = progress * 5 + i * math.pi / 2
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                    (flash_x, flash_y), (ex, ey), 1)


    # ===================================================================
    # SKILL Q: POWERSHOT (charging)
    # ===================================================================
    def _draw_powershot_charge(surface, boss, x, y, timer, phase):
        """Charging aura around boss."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        facing = boss.direction

        # Line indicator to target (tegas: titik terang lebih besar + outline)
        tx, ty = _NS_sylara._target_position(boss, x, y)
        for i in range(0, 100, 5):
            alpha = int(100 + math.sin(phase * 3 + i * 0.2) * 70)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha // 2),
                      (x + int((tx - x) * i / 100) + 1,
                       y + int((ty - y) * i / 100) - 7), 2)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha),
                      (x + int((tx - x) * i / 100),
                       y + int((ty - y) * i / 100) - 8), 1)

        # Charging particles converging
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 30 - int(progress * 20)  # converge
            px = x + 22 * facing + int(math.cos(angle) * r)
            py = y - 8 + int(math.sin(angle) * r)
            alpha = int(200 * progress)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha), (px, py), 2)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], alpha), (px, py), 1)


    # ===================================================================
    # SKILL W: WINDRUN
    # ===================================================================
    def _draw_windrun_ground(surface, boss, x, y, timer, phase):
        """Ground effect during windrun."""
        facing = boss.direction
        # Speed lines on ground (tegas: stroke gelap + garis terang)
        for i in range(6):
            off = (i - 3) * 6
            sx = x - facing * 20
            sy = y + 30 + off
            ex = sx - facing * 40
            alpha = 200 - i * 20
            _skill_outlined_line(surface, (sx, sy), (ex, sy), 1,
                                 _NS_sylara.PALETTE["wind_bright"], alpha)


    def _draw_windrun_trail(surface, x, y, facing, phase):
        """After-image trail behind Sylara during windrun."""
        for i in range(5):
            offset = (i + 1) * 8 * facing
            alpha = 180 - i * 30
            # Ghost silhouette
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_dark"], alpha // 2),
                      (x - offset, y - 10), 14)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_mid"], alpha),
                      (x - offset, y - 5), 10)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_light"], alpha),
                      (x - offset, y - 8), 6)

        # Wind swirls around Sylara
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 25
            px = x + int(math.cos(angle) * r)
            py = y - 5 + int(math.sin(angle) * r * 0.5)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], 200), (px, py), 3)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], 220), (px, py), 1)

        # Horizontal speed streaks
        for i in range(6):
            sy = y + (i - 3) * 6
            sx = x - facing * 20
            ex = sx - facing * 30
            alpha = 200 - i * 15
            _NS_sylara._aaline(surface, (*_NS_sylara.PALETTE["wind_light"], alpha),
                    (sx, sy), (ex, sy), 1)


    # ===================================================================
    # SKILL E: SHACKLE SHOT
    # ===================================================================
    def _draw_shackle_ground(surface, boss, x, y, timer, pulse):
        """Line indicator to target for shackle shot."""
        tx, ty = _NS_sylara._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 150))

        # Dashed line indicator (tegas: stroke gelap + garis terang)
        steps = 20
        for i in range(steps):
            if i % 2 == 0:
                t1 = i / steps
                t2 = (i + 1) / steps
                x1 = x + (tx - x) * t1
                y1 = y + (ty - y) * t1 - 5
                x2 = x + (tx - x) * t2
                y2 = y + (ty - y) * t2 - 5
                _skill_outlined_line(surface, (x1, y1), (x2, y2), 2,
                                     _NS_sylara.PALETTE["wind_bright"], 170)

        # Spawn shackle projectile at start
        if not getattr(boss, "_sy_shackle_spawned", False):
            _NS_sylara._spawn_shackle(boss, x, y)
            boss._sy_shackle_spawned = True
        if timer < 5:
            boss._sy_shackle_spawned = False


    # ===================================================================
    # SKILL R: FOCUS FIRE (ultimate)
    # ===================================================================
    def _draw_focus_fire_ground(surface, boss, x, y, timer, phase):
        """Ground rune for focus fire."""
        progress = max(0.0, min(1.0, 1 - timer / 180))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(40 + progress * 15)

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Dark outline first (tegas di atas terrain terang)
        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_dark"], int(150 * pulse)),
                            (3, 3, radius * 2 + 14, radius + 14), 5)
        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_mid"], int(190 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_sylara.PALETTE["wind_bright"], int(220 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runic marks
        for i in range(6):
            a = phase * 0.5 + i * math.pi / 3
            px = cx + int(math.cos(a) * (radius - 3))
            py = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.circle(ring, (*_NS_sylara.PALETTE["wind_white"], 240), (px, py), 3)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_focus_fire_effect(surface, boss, x, y, timer, phase):
        """Rapid arrow volley animation."""
        progress = max(0.0, min(1.0, 1 - timer / 180))

        # Fire arrows in bursts
        fire_interval = 8  # every 8 frames
        if not hasattr(boss, "_sy_focus_last_shot"):
            boss._sy_focus_last_shot = -100

        if progress > 0.2 and progress < 0.9:
            if timer % fire_interval == 0 and boss._sy_focus_last_shot != timer:
                _NS_sylara._spawn_focus_fire_volley(boss, x, y)
                boss._sy_focus_last_shot = timer

        if progress < 0.2:
            boss._sy_focus_last_shot = -100

        # Energy aura around boss (channeling)
        for i in range(10):
            angle = phase * 3 + i * math.pi / 5
            r = 25 + int(math.sin(phase * 2 + i) * 5)
            px = x + int(math.cos(angle) * r)
            py = y - 10 + int(math.sin(angle) * r * 0.6)
            alpha = int(200 + math.sin(phase * 2 + i) * 55)
            alpha = max(0, min(255, alpha))
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_bright"], alpha), (px, py), 3)
            _NS_sylara._aacircle(surface, (*_NS_sylara.PALETTE["wind_white"], alpha), (px, py), 1)

        # Wind spirals
        for i in range(3):
            angle_start = phase * 2 + i * math.pi * 2 / 3
            _NS_sylara._draw_wind_arc(surface, x, y - 10, 30, angle_start,
                           angle_start + math.pi * 1.4,
                           (*_NS_sylara.PALETTE["wind_bright"], 200), width=2, segments=10)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_sylara.draw_sylara(surface, boss, x, y)

# ====================================================================
# kaizen.py
# ====================================================================
class _NS_kaizen:
    """Namespace kaizen - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Yasuo inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin
        "skin_darkest":   (135,  85,  60),
        "skin_dark":      (185, 130,  95),
        "skin_mid":       (220, 170, 135),
        "skin_light":     (240, 200, 165),
        "skin_high":      (250, 220, 190),

        # Hair (dark brown)
        "hair_darkest":   ( 30,  20,  15),
        "hair_dark":      ( 55,  35,  25),
        "hair_mid":       ( 85,  55,  35),
        "hair_light":     (120,  80,  55),
        "hair_shine":     (155, 110,  75),

        # Outfit - blue/dark
        "cloth_darkest":  ( 15,  20,  40),
        "cloth_dark":     ( 30,  45,  85),
        "cloth_mid":      ( 55,  80, 145),
        "cloth_light":    ( 90, 130, 200),
        "cloth_high":     (140, 180, 235),

        # Scarf/sash - brighter blue
        "scarf_dark":     ( 40,  70, 140),
        "scarf_mid":      ( 75, 120, 200),
        "scarf_light":    (130, 175, 240),
        "scarf_high":     (185, 215, 255),

        # Pants - darker
        "pants_dark":     ( 20,  30,  60),
        "pants_mid":      ( 40,  55, 105),
        "pants_light":    ( 70,  95, 155),

        # Leather belt/straps
        "leather_dark":   ( 55,  35,  20),
        "leather_mid":    ( 95,  65,  40),
        "leather_light":  (140, 100,  65),

        # Sword - katana
        "steel_darkest":  ( 40,  50,  65),
        "steel_dark":     ( 90, 105, 125),
        "steel_mid":      (155, 170, 190),
        "steel_light":    (210, 220, 235),
        "steel_shine":    (245, 250, 255),

        # Handle wrap
        "wrap_dark":      ( 55,  20,  25),
        "wrap_mid":       (110,  40,  50),
        "wrap_light":     (165,  70,  85),

        # Gold accents
        "gold_dark":      ( 95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),

        # Wind - light cyan/white
        "wind_darkest":   ( 30,  60, 110),
        "wind_dark":      ( 55, 110, 175),
        "wind_mid":       (110, 175, 230),
        "wind_light":     (175, 220, 250),
        "wind_bright":    (215, 240, 255),
        "wind_white":     (245, 252, 255),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       (200, 150,  50),
        "eye_iris_light": (240, 200, 100),
        "eye_pupil":      ( 15,  15,  20),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaizen._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
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
        color = _NS_kaizen._clamp(color)
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
        color = _NS_kaizen._clamp(color)
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
        color = _NS_kaizen._clamp(color)
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
            return _NS_kaizen._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 150 * (float(scale) if scale is not None else 1.0)
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
            _NS_kaizen._aaline(surface, color, points[i], points[i + 1], width)


    def _draw_wind_swirl(surface, cx, cy, size, phase, color=None, alpha=200):
        """Small wind swirl."""
        if color is None:
            color = _NS_kaizen.PALETTE["wind_bright"]
        col = (*color, alpha) if len(color) == 3 else color
        for i in range(3):
            angle_start = phase * 0.8 + i * math.pi * 2 / 3
            angle_end = angle_start + math.pi * 1.2
            _NS_kaizen._draw_wind_arc(surface, cx, cy, size, angle_start, angle_end,
                           col, width=1, segments=8)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Steel Wind Slash (Q ranged projectile)
    # ---------------------------------------------------------------------------
    class WindSlashProjectile:
        """Crescent wind slash projectile (Steel Wind)."""
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
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha), (tx, ty), r + 2)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Glow behind slash
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], 100), (px, py), 16)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], 150), (px, py), 11)

                # Crescent slash shape - perpendicular to travel direction
                perp = self.angle + math.pi / 2
                arc_radius = 14
                # Draw crescent as thick arc
                for offset in range(-2, 3):
                    width = 3 - abs(offset)
                    if width <= 0:
                        continue
                    if offset == 0:
                        color = _NS_kaizen.PALETTE["wind_white"]
                    elif abs(offset) == 1:
                        color = _NS_kaizen.PALETTE["wind_bright"]
                    else:
                        color = _NS_kaizen.PALETTE["wind_light"]
                    _NS_kaizen._draw_wind_arc(surface, px, py, arc_radius + offset,
                                   perp - 1.1, perp + 1.1,
                                   color, width=width, segments=10)

                # Tips of crescent - sharp points
                tip1_x = px + math.cos(perp - 1.1) * arc_radius
                tip1_y = py + math.sin(perp - 1.1) * arc_radius
                tip2_x = px + math.cos(perp + 1.1) * arc_radius
                tip2_y = py + math.sin(perp + 1.1) * arc_radius
                _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["wind_white"],
                          (int(tip1_x), int(tip1_y)), 2)
                _NS_kaizen._aacircle(surface, _NS_kaizen.PALETTE["wind_white"],
                          (int(tip2_x), int(tip2_y)), 2)

                # Speed lines
                for i in range(3):
                    offset = (i - 1) * 5
                    sx1 = px - math.cos(self.angle) * (8 + i * 2) + math.cos(perp) * offset
                    sy1 = py - math.sin(self.angle) * (8 + i * 2) + math.sin(perp) * offset
                    sx2 = sx1 - math.cos(self.angle) * 6
                    sy2 = sy1 - math.sin(self.angle) * 6
                    _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], 180),
                            (sx1, sy1), (sx2, sy2), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
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
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kz_prev_timer", -1))
        active = bool(getattr(boss, "_kz_attack_active", False))

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
            boss._kz_attack_active = True
            active = True

        if active and timer <= 0:
            boss._kz_attack_active = False
            active = False

        boss._kz_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
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
        boss._kz_projectiles = [p for p in boss._kz_projectiles if p.alive or p.dead_frames < 8]


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
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._kz_projectiles.append(proj)


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_kaizen(surface, boss, x, y):
        """Entry point for Boss.draw()."""
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

        # ---------- Background layers ----------
        # Portrait LOD intentionally omits arena-sized aura/platform. This
        # lets auto-crop fill the portrait with Kaizen's face and materials
        # instead of shrinking him to include a 180 px effect circle.
        if not portrait_hd:
            _NS_kaizen._draw_swordsman_rim_light(surface, x, y - 10, pulse)
            _NS_kaizen._draw_wind_aura(surface, x, y, pulse)
            _NS_kaizen._draw_wind_platform(
                surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_kaizen._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizen._draw_sweep_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizen._draw_tornado_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_kaizen._draw_kaizen_attack(surface, boss, x, y)
        elif moving:
            _NS_kaizen._draw_kaizen_walk(surface, boss, x, y)
        else:
            _NS_kaizen._draw_kaizen_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        if not portrait_hd:
            _NS_kaizen._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_kaizen._draw_dash_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaizen._draw_wind_wall(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizen._draw_sweep_effect(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizen._draw_tornado(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_kaizen_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x, y + 48)
            _NS_kaizen._draw_floating_wind(surface, x, y + 35, boss.pulse)
        _NS_kaizen._draw_kaizen_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_kaizen_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x + sway, y + 48)
            _NS_kaizen._draw_floating_wind(
                surface, x + sway, y + 35, phase, trail=True,
                facing=boss.direction)
        _NS_kaizen._draw_kaizen_body(
            surface, x + sway, y - bob, boss.direction, phase, "walk",
            detail=getattr(boss, "_portrait_hd", False))


    def _draw_kaizen_attack(surface, boss, x, y):
        progress = getattr(boss, "_kz_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn wind slash projectile at mid-swing (ranged variant)
        range_val = getattr(boss, "range", 150)
        is_ranged = range_val > 80

        if is_ranged:
            if 0.45 < progress < 0.55 and not getattr(boss, "_kz_proj_spawned", False):
                _NS_kaizen._spawn_wind_slash(boss, x, y)
                boss._kz_proj_spawned = True
            if progress < 0.15 or progress > 0.9:
                boss._kz_proj_spawned = False

        # Slight step forward during swing
        step = int(math.sin(progress * math.pi) * 3) * boss.direction
        if not getattr(boss, "_portrait_hd", False):
            _NS_kaizen._draw_shadow(surface, x + step, y + 48)
            _NS_kaizen._draw_floating_wind(
                surface, x + step, y + 35, boss.pulse, intense=True)
        _NS_kaizen._draw_kaizen_body(
            surface, x + step, y, boss.direction, boss.pulse,
            "attack", progress, getattr(boss, "_portrait_hd", False))


    # ===================================================================
    # BODY RENDERING - HD samurai
    # ===================================================================
    def _draw_kaizen_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, detail=False):
        """Renderer tubuh Kaizen kualitas maksimum, 100% procedural.

        Dibangun sebagai bone rig 2D berlapis: setiap pose mengubah lean,
        langkah, sendi tangan, arah katana, rambut, dan scarf. Tidak ada PNG,
        sprite sheet, ataupun image.load. Efek skill lama tetap kompatibel.
        """
        _NS_kaizen._draw_kaizen_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail)


    def _draw_kaizen_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False):
        """Hand-authored pixel-art rig memakai primitive pygame saja."""
        p = _NS_kaizen.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        stride = math.sin(phase * 1.7)
        lean = (3 if walk else 0) * f
        # Whole-body root motion: breathing, planted walk bounce, then a
        # compressed wind-up / explosive attack lunge. Because every layer
        # uses pt(), hair, face, armor and limbs remain attached to the rig.
        root_y = int(math.sin(phase * .72) * .7)
        # v2 (animasi): perpindahan berat badan saat idle — badan bergoyang
        # ke kiri-kanan (bukan sekadar naik-turun nafas), memberi kesan hidup.
        sway = int(math.sin(phase * .8) * 3) * f if not (walk or attack) else 0
        if walk:
            root_y -= int(abs(math.sin(phase * 1.7)) * 2)
        if attack:
            ap = max(0.0, min(1.0, attack_progress))
            lean = int(math.sin(ap * math.pi) * 7) * f
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean + sway), int(cy + dy + root_y))

        def poly(color, points, outline=True):
            pts = [pt(dx, dy) for dx, dy in points]
            if outline:
                _NS_kaizen._poly(surface, p["shadow_deep"],
                                  [(x + f, y + 1) for x, y in pts])
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

        # ── back hair: seven independently animated, tapered locks ──
        hair_wave = math.sin(phase * 1.25)
        tail_root = (-7, -34)
        # Broad ponytail mass first, then separate pointed locks. This avoids
        # the "thin broom" silhouette common in primitive-only renderers.
        # v2: ponytail mengibas lebih lebar saat bergerak/menyerang.
        hw = int(hair_wave * (4 if (walk or attack) else 2))
        poly(p["hair_darkest"], [(-5, -35), (-12, -48), (-24, -57 + hw),
             (-21, -48 + hw), (-38, -51 + hw), (-29, -40 + hw),
             (-45, -37 + hw), (-29, -31 + hw), (-41, -22 + hw),
             (-21, -25 + hw), (-11, -30)])
        poly(p["hair_dark"], [(-8, -36), (-14, -46), (-23, -53 + hw),
             (-21, -44 + hw), (-34, -47 + hw), (-27, -38 + hw),
             (-39, -36 + hw), (-25, -32 + hw), (-34, -26 + hw),
             (-18, -28 + hw)], False)
        poly(p["hair_mid"], [(-14, -43), (-22, -49 + hw),
             (-20, -42 + hw), (-31, -43 + hw), (-24, -37 + hw)], False)
        locks = [(-16, -47, -34, -42), (-17, -43, -39, -35),
                 (-16, -39, -38, -27), (-13, -36, -33, -20),
                 (-10, -34, -25, -16), (-15, -46, -29, -51),
                 (-11, -49, -20, -57)]
        for i, (mx, my, ex, ey) in enumerate(locks):
            wave = int(hair_wave * (2 + i % 3))
            shape = [tail_root, (mx, my + wave), (ex, ey + wave),
                     (mx - 2, my + 5 + wave), (-8, -30)]
            poly(p["hair_darkest"], shape)
            inner = [(-8, -34), (mx, my + 1 + wave),
                     (ex + 3, ey + 1 + wave), (mx + 1, my + 4 + wave)]
            poly(p["hair_dark"], inner, False)
            a, b = pt(mx + 1, my + 1 + wave), pt(ex + 4, ey + 1 + wave)
            _NS_kaizen._aaline(surface, p["hair_mid"], a, b, 1)

        # ── scarf tails behind torso ──
        # v2: mengalir lebih jauh & berombak lebih kuat saat bergerak/menyerang.
        scarf_wave = int(math.sin(phase * 1.45) * (5 if (walk or attack) else 3))
        scarf_boost = 13 if (walk or attack) else 0
        poly(p["scarf_dark"], [(-5, -25), (-12, -22),
             (-26 - scarf_boost, -17 + scarf_wave),
             (-39 - scarf_boost, -7 + scarf_wave),
             (-28, -5), (-14, -13)])
        poly(p["scarf_mid"], [(-7, -23), (-15, -20),
             (-29 - scarf_boost, -11 + scarf_wave),
             (-35 - scarf_boost, -8 + scarf_wave), (-24, -7), (-12, -16)],
             False)
        _NS_kaizen._aaline(surface, p["scarf_light"], pt(-12, -20),
                           pt(-31 - scarf_boost, -9 + scarf_wave), 2)

        # ── lacquered saya behind hip ──
        limb((-7, 7), (-31, 29), 7, (104, 27, 39), (190, 62, 70))
        _NS_kaizen._aacircle(surface, p["gold_mid"], pt(-31, 29), 3)

        # ── legs: true split stance, not one floating robe mass ──
        # v2 (animasi): foot-lift bergantian — kaki yang melangkah maju
        # terangkat (lutut + telapak naik), kaki tumpuan tetap menapak.
        # Kecepatan stride menentukan fase swing tiap kaki.
        leg_phase = stride if walk else 0.0
        stride_vel = math.cos(phase * 1.7) if walk else 0.0
        rear_lift = int(max(0.0, -stride_vel) * 9) if walk else 0
        front_lift = int(max(0.0, stride_vel) * 9) if walk else 0
        rear_foot = (-8 - int(leg_phase * 5),
                     40 - int(abs(leg_phase) * 2) - rear_lift)
        front_foot = (11 + int(leg_phase * 6), 40 - front_lift)
        for hip, knee, foot, shade, lift in (
                ((-5, 12), (-9, 27), rear_foot, p["pants_dark"], rear_lift),
                ((6, 12), (9, 26), front_foot, p["pants_mid"], front_lift)):
            # Knee rises with the lift so the thigh folds up to meet the
            # raised shin (proper knee-bend, no gap between segments).
            knee = (knee[0], knee[1] - lift)
            poly(shade, [hip, (hip[0] + 7, hip[1]),
                         (knee[0] + 5, knee[1]), (foot[0] + 4, foot[1] - 5),
                         (foot[0] - 4, foot[1] - 5),
                         (knee[0] - 4, knee[1])])
            # shin wrap / tabi
            poly((204, 211, 216), [(foot[0] - 4, foot[1] - 10),
                 (foot[0] + 4, foot[1] - 10), (foot[0] + 4, foot[1] - 4),
                 (foot[0] - 4, foot[1] - 4)], False)
            poly(p["leather_dark"], [(foot[0] - 5, foot[1] - 4),
                 (foot[0] + 7, foot[1] - 4), (foot[0] + 8, foot[1]),
                 (foot[0] - 5, foot[1])])
            _NS_kaizen._aaline(surface, p["leather_light"],
                               pt(foot[0] - 3, foot[1] - 3),
                               pt(foot[0] + 5, foot[1] - 3), 1)

        # Wide hakama panels keep volume while the feet remain readable.
        poly(p["pants_dark"], [(-12, 5), (0, 7), (-2, 29),
                               (-13, 30), (-17, 22)])
        poly(p["pants_mid"], [(0, 7), (12, 5), (17, 22),
                              (4, 29), (1, 18)])
        poly(p["pants_light"], [(3, 9), (10, 8), (13, 21),
                                (6, 25)], False)
        for dx in (-8, 5, 12):
            _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(dx, 10),
                               pt(dx + (1 if dx > 0 else -1), 25), 1)

        # ── torso: asymmetric open jacket + leather harness ──
        poly(p["cloth_darkest"], [(-13, -17), (7, -20), (15, -10),
             (12, 9), (2, 14), (-12, 8), (-16, -6)])
        poly(p["cloth_mid"], [(-11, -15), (-2, -18), (-1, 10),
                              (-10, 7), (-13, -5)], False)
        poly(p["skin_dark"], [(-2, -18), (7, -18), (10, -9),
                              (5, 8), (-1, 9)], False)
        poly(p["skin_mid"], [(0, -16), (6, -16), (8, -8),
                             (4, 5), (0, 7)], False)
        _NS_kaizen._aaline(surface, p["leather_dark"], pt(-10, -14),
                           pt(10, 5), 5)
        _NS_kaizen._aaline(surface, p["leather_light"], pt(-10, -14),
                           pt(10, 5), 1)
        # braided obi
        _NS_kaizen._aaline(surface, p["gold_dark"], pt(-13, 7), pt(13, 7), 5)
        for dx in range(-10, 11, 4):
            _NS_kaizen._aaline(surface, p["gold_light"], pt(dx - 1, 5),
                               pt(dx + 1, 9), 1)

        # Layered steel-and-lacquer pauldron on the sword shoulder. Separate
        # lames, rivets and a cold rim turn the upper body into a readable
        # armored silhouette rather than a single blue polygon.
        pauldron = [(7, -18), (13, -20), (19, -15), (18, -8),
                    (13, -5), (8, -9)]
        poly(p["steel_darkest"], pauldron)
        poly(p["cloth_mid"], [(9, -17), (13, -18), (17, -14),
                              (16, -10), (12, -8), (9, -10)], False)
        for i in range(3):
            yy = -15 + i * 3
            _NS_kaizen._aaline(surface, p["cloth_light"],
                               pt(10, yy), pt(17 - i, yy + 1), 1)
        _NS_kaizen._aacircle(surface, p["gold_mid"], pt(12, -15), 2)
        _NS_kaizen._aacircle(surface, p["gold_light"], pt(12, -16), 1)

        # Jacket piping, stitches, and small wind crest.
        _NS_kaizen._aaline(surface, p["cloth_high"], pt(-11, -13),
                           pt(-10, 4), 1)
        for yy in (-9, -4, 1):
            _NS_kaizen._aaline(surface, p["scarf_light"],
                               pt(-12, yy), pt(-9, yy + 1), 1)
        _NS_kaizen._draw_wind_arc(surface, *pt(-5, -5), 4, .3, 4.4,
                                   p["wind_mid"], 1, 7)

        # ── rear arm / bracer ──
        if attack:
            prog = max(0.0, min(1.0, attack_progress))
            rear_hand = (-2 + int(prog * 8), -3)
        else:
            rear_hand = (-14, 5)
        limb((-10, -12), (-16, -2), 7, p["cloth_dark"], p["cloth_light"])
        limb((-16, -2), rear_hand, 6, p["skin_dark"], p["skin_light"])
        rhx, rhy = pt(*rear_hand)
        _NS_kaizen._rect(surface, p["wrap_dark"],
                         (rhx - 4, rhy - 4, 8, 8), 2)
        _NS_kaizen._aaline(surface, p["wrap_light"],
                           (rhx - 3, rhy - 2), (rhx + 3, rhy + 1), 1)
        _NS_kaizen._aaline(surface, p["gold_mid"],
                           (rhx - 3, rhy + 2), (rhx + 3, rhy + 2), 1)

        # ── neck and three-quarter head ──
        poly(p["skin_dark"], [(-3, -23), (5, -23), (5, -16), (-3, -16)])
        face = [(-8, -42), (4, -44), (10, -38), (11, -31),
                (7, -23), (1, -20), (-6, -24), (-10, -33)]
        poly(p["skin_dark"], face)
        poly(p["skin_mid"], [(-6, -40), (3, -42), (8, -37),
             (9, -32), (6, -25), (1, -22), (-4, -25), (-7, -33)], False)
        poly(p["skin_light"], [(1, -40), (6, -37), (7, -33),
                               (3, -29), (-1, -31)], False)
        # nose, eye, brow, scar, mouth
        poly(p["skin_light"], [(8, -35), (13, -33), (8, -31)], False)
        _NS_kaizen._aaline(surface, p["hair_darkest"], pt(2, -36), pt(8, -35), 2)
        _NS_kaizen._rect(surface, p["eye_iris_light"],
                         (pt(6, -34)[0], pt(6, -34)[1], 2, 2))
        _NS_kaizen._aaline(surface, (120, 48, 47), pt(-1, -33), pt(7, -27), 1)
        _NS_kaizen._aaline(surface, p["skin_darkest"], pt(4, -25), pt(8, -26), 1)
        _NS_kaizen._aacircle(surface, p["gold_light"], pt(-8, -27), 2)

        # ── hair cap and crown spikes ──
        poly(p["hair_darkest"], [(-10, -42), (-8, -50), (-3, -47),
             (0, -54), (4, -48), (10, -49), (8, -43), (12, -40),
             (6, -38), (1, -41), (-4, -38), (-9, -34)])
        poly(p["hair_dark"], [(-7, -43), (-6, -48), (-2, -45),
             (0, -51), (3, -46), (7, -47), (6, -42), (9, -40),
             (4, -40), (1, -43), (-4, -40)], False)
        _NS_kaizen._aaline(surface, p["hair_light"], pt(-3, -46), pt(0, -50), 1)
        # Narrow hachimaki under the fringe, with an embossed wind bead.
        _NS_kaizen._aaline(surface, p["cloth_darkest"], pt(-8, -40),
                           pt(8, -39), 4)
        _NS_kaizen._aaline(surface, p["scarf_mid"], pt(-7, -41),
                           pt(8, -40), 2)
        _NS_kaizen._aacircle(surface, p["wind_dark"], pt(5, -40), 2)
        _NS_kaizen._aacircle(surface, p["wind_light"], pt(5, -41), 1)

        # Scarf collar sits above neck and anchors the long tail.
        poly(p["scarf_dark"], [(-10, -24), (-7, -29), (7, -25),
             (10, -20), (5, -16), (-7, -17)])
        poly(p["scarf_mid"], [(-8, -24), (-5, -27), (6, -24),
             (8, -21), (4, -19), (-6, -19)], False)
        _NS_kaizen._aaline(surface, p["scarf_high"], pt(-5, -25), pt(6, -22), 1)

        # ── sword arm and katana, pose-driven ──
        if attack:
            prog = max(0.0, min(1.0, attack_progress))
            if prog < .28:       # wind-up behind head
                t = prog / .28
                hand = (10, -7 - int(t * 8))
                angle = -2.15 + t * .45
            elif prog < .62:     # fast horizontal cut
                t = (prog - .28) / .34
                hand = (12 + int(t * 8), -13 + int(t * 12))
                angle = -1.70 + t * 1.85
            else:                # low recovery
                t = (prog - .62) / .38
                hand = (20 - int(t * 7), -1 + int(t * 10))
                angle = .15 + t * .65
        else:
            hand = (15, 1)
            angle = .72
        elbow = ((hand[0] + 10) // 2, (hand[1] - 10) // 2)
        limb((10, -12), elbow, 8, p["cloth_mid"], p["cloth_high"])
        limb(elbow, hand, 7, p["skin_dark"], p["skin_light"])
        _NS_kaizen._draw_elite_katana(surface, cx + lean + sway, cy, f,
                                      hand, angle, phase, attack)

        # Small wind crest and armor rivets remain legible at 50 px.
        _NS_kaizen._draw_wind_arc(surface, *pt(2, 17), 5, .2, 4.6,
                                   p["wind_light"], 1, 8)
        for dx, dy in ((-10, -9), (-8, -4), (10, -7)):
            _NS_kaizen._aacircle(surface, p["gold_mid"], pt(dx, dy), 1)

        # ── secondary motion / contact feedback ──
        if walk:
            # Dust appears only near footfall (|stride| close to one), while
            # speed lines trail opposite the facing direction.
            contact = max(0.0, abs(stride) - .55) / .45
            if contact > 0:
                planted = rear_foot if stride > 0 else front_foot
                fx, fy = pt(planted[0], planted[1])
                alpha = int(150 * contact)
                for i in range(4):
                    _NS_kaizen._aacircle(
                        surface, (*p["wind_mid"], max(15, alpha - i * 24)),
                        (fx - f * (3 + i * 3), fy - i % 2), max(1, 3 - i // 2))
            for i in range(3):
                sy = cy - 7 + i * 9 + root_y
                _NS_kaizen._aaline(surface, (*p["wind_light"], 95 - i * 18),
                                   (cx - f * (25 + i * 7), sy),
                                   (cx - f * (12 + i * 5), sy - 1), 1)
        elif attack:
            ap = max(0.0, min(1.0, attack_progress))
            impact = max(0.0, 1.0 - abs(ap - .52) / .18)
            if impact > 0:
                ix, iy = pt(47, -3)
                for i in range(6):
                    ang = -1.2 + i * .48
                    length = 5 + int(impact * (8 + i % 2 * 4))
                    _NS_kaizen._aaline(surface,
                                       (*p["wind_white"], int(220 * impact)),
                                       (ix, iy),
                                       (ix + math.cos(ang) * length * f,
                                        iy + math.sin(ang) * length),
                                       1 if i % 2 else 2)
        else:
            # ── v2: aura angin berputar + daun angin (idle showcase) ──
            # Rotating wind aura: faint orbit arcs mengelilingi tubuh.
            aura_r = 30 + int(math.sin(phase * .9) * 3)
            for k in range(2):
                _NS_kaizen._draw_wind_arc(
                    surface, cx, cy - 6, aura_r + k * 6,
                    phase * (0.55 + k * .35),
                    phase * (0.55 + k * .35) + 4.4,
                    (*p["wind_mid"], 30 - k * 12), 1, 12)
            # orbiting bright wisps tracing the aura
            for i in range(3):
                a = phase * 1.1 + i * math.tau / 3
                wx = cx + int(math.cos(a) * aura_r)
                wy = cy - 6 + int(math.sin(a) * aura_r * .55)
                _NS_kaizen._aacircle(surface, (*p["wind_bright"], 150),
                                     (wx, wy), 1)
            # drifting wind leaves (daun angin) — teardrop kecil berputar
            for i in range(4):
                t = (phase * .11 + i / 4.0) % 1.0
                lx = cx + int(math.sin(phase * 1.3 + i * 1.7) * (20 + i * 4))
                ly = cy + 22 - int(t * 68)
                la = phase * .8 + i * 2.4
                ca, sa = math.cos(la), math.sin(la)
                tip = (int(lx + ca * 4), int(ly + sa * 4))
                b1 = (int(lx - sa * 2), int(ly + ca * 2))
                b2 = (int(lx + sa * 2), int(ly - ca * 2))
                _NS_kaizen._poly(surface, (*p["wind_light"], 150),
                                 [tip, b1, b2])
                _NS_kaizen._poly(surface, (*p["wind_bright"], 110),
                                 [tip, (int(lx + sa * 1), int(ly - ca * 1)),
                                  (int(lx - sa * 1), int(ly + ca * 1))])
            # Quiet idle motes make breathing visible without obscuring face.
            for i in range(3):
                t = (phase * .18 + i / 3.0) % 1.0
                mx = cx + int(math.sin(phase + i * 2.1) * (18 + i * 3))
                my = cy + 28 - int(t * 58)
                _NS_kaizen._aacircle(surface,
                                     (*p["wind_bright"], int(110 * (1 - t))),
                                     (mx, my), 1)

        # ── rim-light: sinyal angin biru di tepi yang menghadap cahaya ──
        # v2 (visual): garis 1px warna angin pada tepi depan siluet supaya
        # Kaizen "pop" saat unit bertumpuk (setara rimlight Gornak masterwork).
        # `pt()` sudah membalik tanda saat facing -1, jadi cukup pakai dx
        # positif (tepi depan).
        pulse = 0.72 + 0.28 * math.sin(phase * 1.8)
        rim_a = int(150 * pulse)
        rim_col = (*p["wind_light"], rim_a)
        rim_hot = (*p["wind_white"], int(205 * pulse))
        # puncak rambut & poni (sisi depan mahkota)
        _NS_kaizen._aaline(surface, rim_col, pt(0, -54), pt(4, -47), 1)
        _NS_kaizen._aaline(surface, rim_col, pt(4, -47), pt(10, -45), 1)
        _NS_kaizen._aaline(surface, rim_hot, pt(1, -52), pt(4, -48), 1)
        # tepi atas pauldron (bahu pedang) — kilau ganda
        _NS_kaizen._aaline(surface, rim_col, pt(8, -19), pt(19, -16), 1)
        _NS_kaizen._aaline(surface, rim_hot, pt(10, -19), pt(16, -17), 1)
        # tepi depan torso & jaket
        _NS_kaizen._aaline(surface, rim_col, pt(14, -12), pt(12, 8), 1)
        # tepi depan paha & boot depan (ikut naik saat kaki terangkat)
        _NS_kaizen._aaline(surface, rim_col, pt(9, 26 - front_lift),
                           pt(12, 39 - front_lift), 1)
        _NS_kaizen._aacircle(surface, rim_hot, pt(12, 40 - front_lift), 1)
        # glint kecil pada gagang katana hanya saat diam (saat menyerang
        # gagang sudah menyala lewat glow bilah + afterimage)
        if not attack:
            _NS_kaizen._aacircle(surface, rim_hot, pt(15, 1), 1)

        if detail:
            # Portrait-only micro-detail. At arena scale these marks would
            # collapse into noise, so LOD keeps them out of gameplay cache.
            # Hair fibre groups
            for i in range(5):
                _NS_kaizen._aaline(
                    surface, p["hair_light"],
                    pt(-13 - i * 3, -43 + i * 3),
                    pt(-24 - i * 3, -45 + i * 5), 1)
            # Face planes, lower eyelid and lip highlight
            _NS_kaizen._aaline(surface, p["skin_high"],
                               pt(2, -39), pt(6, -37), 1)
            _NS_kaizen._aaline(surface, p["skin_darkest"],
                               pt(3, -32), pt(8, -31), 1)
            _NS_kaizen._aaline(surface, p["skin_light"],
                               pt(5, -24), pt(8, -25), 1)
            # Fine textile weave and hakama hem stitching
            for yy in (-11, -6, -1):
                _NS_kaizen._aaline(surface, p["cloth_light"],
                                   pt(-9, yy), pt(-5, yy + 2), 1)
            for xx in (-10, -5, 5, 10):
                _NS_kaizen._aacircle(surface, p["scarf_light"],
                                      pt(xx, 24), 1)
            # Engraved pauldron fan and tiny reflected rivet glints
            for a in (-.7, -.2, .3):
                _NS_kaizen._aaline(surface, p["steel_mid"], pt(12, -13),
                                   pt(12 + math.cos(a) * 5,
                                      -13 + math.sin(a) * 5), 1)
            _NS_kaizen._aacircle(surface, p["wind_white"], pt(13, -16), 1)


    def _draw_elite_katana(surface, cx, cy, facing, hand, angle, phase,
                           attacking=False):
        """Procedural katana with curved silhouette, hamon, and slash arc."""
        p = _NS_kaizen.PALETTE
        f = 1 if facing >= 0 else -1
        hx, hy = cx + hand[0] * f, cy + hand[1]
        length = 42
        ux, uy = math.cos(angle) * f, math.sin(angle)
        tx, ty = hx + ux * length, hy + uy * length
        px, py = -uy, ux
        # wrapped grip behind guard
        ex, ey = hx - ux * 12, hy - uy * 12
        _NS_kaizen._aaline(surface, p["shadow_deep"], (hx, hy), (ex, ey), 7)
        _NS_kaizen._aaline(surface, p["wrap_mid"], (hx, hy), (ex, ey), 4)
        for t in (.25, .55, .85):
            wx, wy = hx - ux * 12 * t, hy - uy * 12 * t
            _NS_kaizen._aaline(surface, p["wrap_light"],
                               (wx - px * 2, wy - py * 2),
                               (wx + px * 2, wy + py * 2), 1)
        _NS_kaizen._aaline(surface, p["gold_dark"],
                           (hx - px * 6, hy - py * 6),
                           (hx + px * 6, hy + py * 6), 4)
        _NS_kaizen._aaline(surface, p["gold_light"],
                           (hx - px * 5, hy - py * 5),
                           (hx + px * 5, hy + py * 5), 1)
        # subtly curved blade polygon
        mx, my = hx + ux * 23 + px * 2, hy + uy * 23 + py * 2
        blade = [(hx + px * 3, hy + py * 3),
                 (mx + px * 2, my + py * 2), (tx, ty),
                 (mx - px, my - py), (hx - px * 2, hy - py * 2)]
        _NS_kaizen._poly(surface, p["shadow_deep"],
                          [(x + f, y + 1) for x, y in blade])
        _NS_kaizen._poly(surface, p["steel_dark"], blade)
        _NS_kaizen._aaline(surface, p["steel_shine"],
                           (hx + px * 2, hy + py * 2), (tx, ty), 2)
        # wavy temper line
        hamon = []
        for i in range(1, 8):
            t = i / 8.0
            wave = math.sin(i * math.pi * .72 + phase * .2) * .8
            hamon.append((hx + ux * length * t + px * wave,
                          hy + uy * length * t + py * wave))
        if len(hamon) > 1:
            pygame.draw.aalines(surface, p["wind_mid"], False, hamon)
        _NS_kaizen._aacircle(surface, p["steel_shine"], (int(tx), int(ty)), 2)

        # v2 (visual): kilau spekular yang meluncur di sepanjang bilah —
        # titik cahaya bergerak dari pangkal ke ujung, memberi kesan logam
        # yang hidup walau diam.
        glint_t = (phase * .85) % 1.0
        gx = hx + ux * length * glint_t + px * 1.2
        gy = hy + uy * length * glint_t + py * 1.2
        _NS_kaizen._aacircle(surface, (*p["steel_shine"], 210),
                             (int(gx), int(gy)), 1)
        _NS_kaizen._aacircle(surface, (*p["wind_white"], 160),
                             (int(gx - ux * 3), int(gy - uy * 3)), 1)

        if attacking:
            # v2 (visual): bilah menyala angin saat menyerang — garis cyan
            # terang di sepanjang tepi potong, makin tebal di tengah ayunan.
            _NS_kaizen._aaline(surface, (*p["wind_bright"], 190),
                               (hx + px * 2, hy + py * 2), (tx, ty), 2)
            _NS_kaizen._aaline(surface, (*p["wind_white"], 120),
                               (hx + px * 3, hy + py * 3), (tx, ty), 1)
            # v2 (animasi): afterimage gerak pisau — beberapa siluet katana
            # memudar di belakang ayunan, memunculkan kesan kecepatan slash.
            # Setiap ghost adalah blade utuh (guard + bilah) pada sudut
            # sebelumnya, warnanya makin transparan makin jauh dari pisau.
            for k in (1, 2, 3):
                ga = angle - 0.38 * k
                gux, guy = math.cos(ga) * f, math.sin(ga)
                gtx, gty = hx + gux * length, hy + guy * length
                gpx, gpy = -guy, gux
                gmx = hx + gux * 23 + gpx * 2
                gmy = hy + guy * 23 + gpy * 2
                ghost = [(hx + gpx * 2, hy + gpy * 2),
                         (gmx + gpx, gmy + gpy), (gtx, gty),
                         (gmx - gpx, gmy - gpy),
                         (hx - gpx * 2, hy - gpy * 2)]
                _NS_kaizen._poly(surface, (*p["wind_mid"],
                                           90 - k * 22), ghost)
                _NS_kaizen._poly(surface, (*p["wind_light"],
                                           140 - k * 30), ghost)
            # layered crescent centered on the sword hand
            start = angle - 1.25
            for radius, color, width in ((48, (*p["wind_dark"], 90), 5),
                                         (46, (*p["wind_light"], 170), 3),
                                         (44, (*p["wind_white"], 235), 1)):
                _NS_kaizen._draw_wind_arc(surface, hx, hy, radius,
                                           start, angle + .25,
                                           color, width, 18)






































    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Wind mist beneath floating Kaizen."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaizen.PALETTE["wind_dark"], min(255, alpha)),
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
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha), (sx, sy), 5)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha), (sx, sy - 2), 3)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Small circling wind swirls
        for i in range(3):
            angle = phase * 1.2 + i * math.pi * 2 / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_kaizen._draw_wind_swirl(surface, sx, sy, 4, phase + i,
                             _NS_kaizen.PALETTE["wind_bright"], alpha=200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha),
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
        pygame.draw.ellipse(shadow, (*_NS_kaizen.PALETTE["wind_darkest"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_swordsman_rim_light(surface, x, y, phase):
        """Small code-drawn blue rim light around scarf, katana, and hair."""
        pulse = .72 + math.sin(phase * 1.3) * .16
        halo = pygame.Surface((88, 98), pygame.SRCALPHA)
        for radius, alpha in ((38, 9), (29, 14), (20, 20)):
            _NS_kaizen._aacircle(halo, (*_NS_kaizen.PALETTE["wind_dark"],
                                         int(alpha * pulse)), (44, 49), radius)
        _NS_kaizen._aaline(halo, (*_NS_kaizen.PALETTE["wind_mid"], int(38 * pulse)),
                            (28, 57), (12, 64), 2)
        _NS_kaizen._aaline(halo, (*_NS_kaizen.PALETTE["wind_light"], int(34 * pulse)),
                            (55, 56), (78, 45), 1)
        surface.blit(halo, (x - 44, y - 49))


    def _draw_wind_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_kaizen._aacircle(aura, (*_NS_kaizen.PALETTE["wind_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_wind_platform(surface, x, y, phase, skill):
        """Wind circle platform."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_mid"], 180),
                            (20, 14, 90, 16), 2)

        # Swirling wind streaks
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_kaizen.PALETTE["wind_light"], 170),
                             (x1, y1), (x2, y2), 1)

        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_kaizen.PALETTE["wind_bright"], 200), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    # ===================================================================
    # SKILL Q: DASH / STEEL WIND (already handled with projectile)
    # ===================================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Ground effect during dash."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        # Line indicator from boss to target (tegas: stroke gelap + terang)
        _skill_outlined_line(surface, (x, y + 30), (tx, ty + 20), 3,
                             _NS_kaizen.PALETTE["wind_mid"], 120)
        _skill_outlined_line(surface, (x, y + 30), (tx, ty + 20), 1,
                             _NS_kaizen.PALETTE["wind_bright"], 170)


    def _draw_dash_effect(surface, boss, x, y, timer, phase):
        """Dash trail / speed lines."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Multiple after-images along dash path
        for i in range(6):
            t = i / 5.0
            ix = int(x + (tx - x) * t)
            iy = int(y + (ty - y) * t)
            alpha = int(180 * (1 - progress) * (1 - t * 0.5))

            # Small ghost silhouette
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha // 2), (ix, iy), 12)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha), (ix, iy - 5), 8)
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha), (ix, iy - 3), 4)

        # Speed streaks
        dx = tx - x
        dy = ty - y
        dist = math.sqrt(dx * dx + dy * dy) or 1
        dx /= dist
        dy /= dist
        px = -dy
        py = dx

        for i in range(8):
            off = (i - 4) * 4
            sx = x + px * off
            sy = y + py * off
            ex = sx + dx * 40
            ey = sy + dy * 40
            alpha = int(220 * (1 - progress))
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha),
                    (sx, sy), (ex, ey), 1)


    # ===================================================================
    # SKILL W: WIND WALL
    # ===================================================================
    def _draw_wind_wall(surface, boss, x, y, timer, phase):
        """Vertical wind wall in front of Kaizen."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        facing = boss.direction

        wall_x = x + 40 * facing
        wall_top = y - 45
        wall_bot = y + 35
        wall_height = wall_bot - wall_top

        # Growing wall
        if progress < 0.2:
            t = progress / 0.2
            h = int(wall_height * t)
            wall_top = y + 35 - h
        else:
            pass

        wall_width = 6

        # Base wall shadow (tegas: outline gelap lebar + core terang)
        _NS_kaizen._rect(surface, (*_NS_kaizen.PALETTE["wind_darkest"], 170),
              (wall_x - wall_width - 2, wall_top, wall_width * 2 + 4, wall_bot - wall_top))
        _NS_kaizen._rect(surface, (*_NS_kaizen.PALETTE["wind_mid"], 140),
              (wall_x - wall_width, wall_top, wall_width * 2, wall_bot - wall_top))

        # Wind swirls making up the wall
        for i in range(8):
            swirl_y = wall_top + i * (wall_bot - wall_top) / 8
            offset_x = int(math.sin(phase * 2 + i * 0.7) * 3)
            _NS_kaizen._draw_wind_swirl(surface, wall_x + offset_x, int(swirl_y), 5,
                             phase + i, _NS_kaizen.PALETTE["wind_bright"], alpha=200)

        # Vertical wind streaks
        for i in range(5):
            sx = wall_x + (i - 2) * 3
            streak_start = wall_top + int((phase * 20 + i * 15) % 30)
            streak_end = min(wall_bot, streak_start + 20)
            alpha = 180
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_light"], alpha),
                    (sx, streak_start), (sx, streak_end), 1)
            _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha),
                    (sx + 1, streak_start + 3), (sx + 1, streak_end - 3), 1)

        # Top and bottom energy caps
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], 200),
                  (wall_x, wall_top), 6)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                  (wall_x, wall_top), 3)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], 200),
                  (wall_x, wall_bot), 6)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                  (wall_x, wall_bot), 3)


    # ===================================================================
    # SKILL E: SWEEP (circular AoE at feet)
    # ===================================================================
    def _draw_sweep_ground(surface, boss, x, y, timer, phase):
        """Ground indicator."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        radius = int(35 + progress * 30)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_dark"], int(150 * pulse)),
                            (3, 3, radius * 2 + 14, radius + 14), 5)
        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_mid"], int(190 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_kaizen.PALETTE["wind_bright"], int(170 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_sweep_effect(surface, boss, x, y, timer, phase):
        """Upward sweep - wind uplift."""
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Wind pillars rising in ring
        for i in range(10):
            angle = i * math.pi / 5 + phase * 0.2
            r = 40
            px = x + int(math.cos(angle) * r)
            py = y + 25 + int(math.sin(angle) * r * 0.3)

            # Rising wind pillar
            h = int(30 * math.sin(progress * math.pi))
            if h <= 0:
                continue

            # Wind streak going up
            for seg in range(3):
                sy = py - seg * (h // 3)
                ey = py - (seg + 1) * (h // 3)
                alpha = 200 - seg * 40
                _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha),
                        (px, sy), (px, ey), 2)
                _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha),
                        (px + 1, sy), (px + 1, ey), 1)

            # Top cap
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 220), (px, py - h), 2)

        # Central burst
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], int(120 * (1 - progress))),
                  (x, y + 20), int(20 + progress * 15), 2)


    # ===================================================================
    # SKILL R: TORNADO (ultimate)
    # ===================================================================
    def _draw_tornado_ground(surface, boss, x, y, timer, phase):
        """Ground swirl indicator."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Warning circle at target (tegas: outline gelap + cincin terang)
        _skill_outlined_circle(surface, (tx, ty + 20), 30, 2,
                               _NS_kaizen.PALETTE["wind_dark"], int(150 * pulse))
        _skill_outlined_circle(surface, (tx, ty + 20), 24, 1,
                               _NS_kaizen.PALETTE["wind_mid"], int(185 * pulse))


    def _draw_tornado(surface, boss, x, y, timer, phase):
        """Large tornado at target position."""
        tx, ty = _NS_kaizen._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Tornado grows then holds
        if progress < 0.3:
            grow = progress / 0.3
        else:
            grow = 1.0

        base_y = ty + 25
        top_y = ty - 60
        height = base_y - top_y
        height = int(height * grow)
        top_y = base_y - height

        if height < 5:
            return

        # Tornado shape - narrow at bottom, wide at top
        layers = 12
        for i in range(layers):
            t = i / layers
            layer_y = int(base_y - t * height)
            # Radius grows with height
            radius = int(4 + t * 22)

            # Swirl offset
            swirl_offset = int(math.sin(phase * 3 + t * 6) * 3)
            cx = tx + swirl_offset

            # Draw layer as ellipse (rotating swirl)
            alpha_base = int(180 - t * 40)

            # Outer swirl
            for a_off in range(3):
                angle = phase * 4 + t * 8 + a_off * math.pi * 2 / 3
                wx = cx + int(math.cos(angle) * radius)
                wy = layer_y + int(math.sin(angle) * radius * 0.3)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_dark"], alpha_base),
                          (wx, wy), 3)
                _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha_base),
                          (wx, wy), 2)

            # Ellipse ring outline
            _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_mid"], alpha_base),
                     (cx - radius, layer_y - int(radius * 0.3),
                      radius * 2, int(radius * 0.6)), 1)

            # Bright inner
            if i % 2 == 0:
                _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_bright"], alpha_base),
                         (cx - radius + 2, layer_y - int(radius * 0.3) + 1,
                          radius * 2 - 4, int(radius * 0.6) - 2), 1)

        # Central vertical core
        core_x = tx + int(math.sin(phase * 2) * 2)
        _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                (core_x, top_y + 5), (core_x, base_y - 5), 2)
        _NS_kaizen._aaline(surface, (*_NS_kaizen.PALETTE["wind_bright"], 150),
                (core_x + 1, top_y + 5), (core_x + 1, base_y - 5), 1)

        # Debris/particles swirling
        for i in range(8):
            t = ((phase * 0.3 + i * 0.12) % 1.0)
            py = int(base_y - t * height)
            radius = 5 + t * 22
            angle = phase * 3 + i * math.pi / 4
            px = tx + int(math.cos(angle) * radius)
            alpha = int(220 * (1 - t * 0.5))
            _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], alpha), (px, py), 2)

        # Top opening flare
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_bright"], 150),
                  (tx, top_y), 22, 2)
        _NS_kaizen._aacircle(surface, (*_NS_kaizen.PALETTE["wind_white"], 200),
                  (tx, top_y), 18, 1)

        # Base impact dust
        _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_dark"], 180),
                 (tx - 20, base_y - 4, 40, 10))
        _NS_kaizen._ellipse(surface, (*_NS_kaizen.PALETTE["wind_mid"], 200),
                 (tx - 15, base_y - 3, 30, 8))


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_kaizen.draw_kaizen(surface, boss, x, y)

# ====================================================================
# thorne.py
# ====================================================================
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
    """Namespace vex - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

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

        # Masterwork detail & shadow-face swatches
        "face_dark":      (16, 14, 28),
        "crown_tip":      (235, 255, 250),
        "crown_rim":      (95, 225, 220),
        "orb_satellite":  (155, 245, 235),
        "rune_trace":     (140, 235, 230),
        "robe_weave":     (60, 48, 92),

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
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 250 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


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
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            # Trail - fading void wisps
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(20 + i * 14)
                r = max(1, 6 - (len(self.trail) - i) // 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], alpha), (tx, ty), r + 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha // 2),
                          (tx, ty), r)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha // 2),
                          (tx, ty), max(1, r - 2))

            if self.alive:
                px, py = int(self.x), int(self.y)

                # Soft outer glow
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], 130), (px, py), 14)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], 170), (px, py), 10)

                # Rotating rune particles around orb
                for i in range(4):
                    a = phase * 3 + i * math.pi / 2
                    r = 8 + int(math.sin(phase * 4 + i) * 2)
                    sx = px + int(math.cos(a) * r)
                    sy = py + int(math.sin(a) * r)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], 220),
                              (sx, sy), 2)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_hot"], 240),
                              (sx, sy), 1)

                # Main orb body
                _NS_vex._draw_glow_orb(surface, px, py, 6,
                               _NS_vex.PALETTE["void_dark"], _NS_vex.PALETTE["void_mid"],
                               _NS_vex.PALETTE["void_hot"], _NS_vex.PALETTE["void_white"])

                # Bright core
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (px - 1, py - 1), 1)


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
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Prison bubble stage
            if self.impact_frame >= 0:
                elapsed = self.age - self.impact_frame
                t = min(1.0, elapsed / 60.0)

                # Grow-in phase
                if elapsed < 8:
                    grow = elapsed / 8
                elif elapsed > 50:
                    grow = max(0.0, 1 - (elapsed - 50) / 10)
                else:
                    grow = 1.0

                radius = int(28 * grow)
                if radius < 3:
                    return

                cx, cy = int(self.tx), int(self.ty)

                # Ground rune circle
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_dark"], 150),
                          (cx, cy + 15), radius, 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], 200),
                          (cx, cy + 15), radius - 3, 1)

                # Vertical energy beam column
                for h in range(radius, 0, -2):
                    alpha = int(140 * grow * (h / radius))
                    y_off = int(-h * 1.5)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], alpha),
                              (cx, cy + y_off), 4)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], alpha),
                              (cx, cy + y_off), 2)

                # Bubble sphere
                for r in range(radius, radius - 6, -1):
                    alpha = int(80 * grow)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_bright"], alpha),
                              (cx, cy), r, 1)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], int(60 * grow)),
                          (cx, cy), radius, 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], int(90 * grow)),
                          (cx, cy), radius - 2, 1)

                # Bubble highlight
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_hot"], int(180 * grow)),
                          (cx - radius // 2, cy - radius // 2),
                          max(1, radius // 4))

                # Rune ring rotating around
                _NS_vex._draw_rune_ring(surface, cx, cy, radius - 2, phase * 2,
                                _NS_vex.PALETTE["astral_bright"], alpha=200, segments=8)

                # Rising energy particles inside
                for i in range(6):
                    pt = (phase * 0.4 + i * 0.16) % 1.0
                    py_off = int(-pt * radius * 1.6 + radius * 0.5)
                    px_off = int(math.sin(phase * 2 + i) * (radius // 3))
                    alpha = int(220 * (1 - pt) * grow)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_hot"], alpha),
                              (cx + px_off, cy + py_off), 2)
                    _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                              (cx + px_off, cy + py_off), 1)
                return

            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 15)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_dark"], alpha), (tx, ty), r + 2)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], alpha // 2),
                          (tx, ty), r)

            # Traveling orb - dark void/black hole style
            if self.alive:
                px, py = int(self.x), int(self.y)

                # Glow ring
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_mid"], 200), (px, py), 10)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["astral_light"], 220), (px, py), 7)
                # Black center (portal)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"], (px, py), 5)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["astral_darkest"], (px, py), 3)

                # Rotating rune particles
                for i in range(4):
                    a = phase * 4 + i * math.pi / 2
                    r = 9
                    sx = px + int(math.cos(a) * r)
                    sy = py + int(math.sin(a) * r)
                    _NS_vex._aacircle(surface, _NS_vex.PALETTE["astral_bright"], (sx, sy), 2)
                    _NS_vex._aacircle(surface, _NS_vex.PALETTE["astral_hot"], (sx, sy), 1)


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
            _NS_vex._draw_void_silhouette_glow(surface, x, y - 12, pulse)
            _NS_vex._draw_void_aura(surface, x, y, pulse)
            _NS_vex._draw_void_platform(surface, x, y + 40, pulse, active_skill)

            # ---------- Skill ground effects ----------
            if active_skill == "w":
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
            _NS_vex._draw_shadow(surface, x, y + 48)
            _NS_vex._draw_floating_void(surface, x, y + 35, boss.pulse)
        _NS_vex._draw_vex_body(surface, x, y + bob, boss.direction,
                               boss.pulse, "idle", detail=portrait)


    def _draw_vex_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_vex._draw_shadow(surface, x + sway, y + 48)
            _NS_vex._draw_floating_void(surface, x + sway, y + 35, phase, trail=True,
                               facing=boss.direction)
        _NS_vex._draw_vex_body(surface, x + sway, y - bob, boss.direction,
                               phase, "walk", detail=portrait)


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
            _NS_vex._draw_shadow(surface, x + recoil, y + 48)
            _NS_vex._draw_floating_void(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_vex._draw_vex_body(surface, x + recoil, y, boss.direction, boss.pulse,
                       "attack", progress, detail=portrait)
        if not portrait:
            _NS_vex._draw_orb_release_flash(surface, x + recoil, y, boss.direction, progress)


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
                       attack_progress=0, detail=False):
        """Wrapper agar idle/walk/attack/skill meneruskan setiap frame ke
        satu rig tulang berlapis (bone rig) tanpa mengubah kontrak."""
        _NS_vex._draw_vex_elite(
            surface, cx, cy, facing, phase, action,
            attack_progress, detail)


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
        return int(cx + tx * f), int(cy + ty)


    # -------------------------------------------------------------------
    # The layered bone rig
    # -------------------------------------------------------------------
    def _draw_vex_elite(surface, cx, cy, facing, phase, action,
                        attack_progress=0.0, detail=False):
        p = _NS_vex.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72)
        breath = math.sin(phase * .8)

        lean = int(stride * 2.0 if walk else 0.0)
        if attack:
            lean += int(math.sin(ap * math.pi) * 5.0)
        elif not walk:
            # v2 (animasi): melayang dengan goyangan kiri-kanan saat idle.
            lean = int(math.sin(phase * .8) * 3) * f
        root_y = int(breath * .8)
        if walk:
            root_y -= int(abs(stride) * 2.0)
        if attack:
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_vex._poly(surface, p["shadow_deep"],
                              [(qx + f, qy + 1) for qx, qy in pts])
            _NS_vex._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            _NS_vex._aaline(surface, p["shadow_deep"],
                            (aa[0] + f, aa[1] + 1),
                            (bb[0] + f, bb[1] + 1), width + 3)
            _NS_vex._aaline(surface, base, aa, bb, width)
            if light:
                off = -1 if f > 0 else 1
                _NS_vex._aaline(surface, light,
                                (aa[0] + off, aa[1] - 1),
                                (bb[0] + off, bb[1] - 1),
                                max(1, width // 3))

        def dot(color, dx, dy, r, outline=True):
            x, y = pt(dx, dy)
            if outline:
                _NS_vex._aacircle(surface, p["shadow_deep"],
                                  (x + f, y + 1), r + 1)
            _NS_vex._aacircle(surface, color, (x, y), r)

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

        # Pose-driven diagonal void staff.
        butt = _NS_vex._staff_butt_local(phase, action, ap)
        orb = _NS_vex._orb_tip_local(phase, action, ap)
        grip = _NS_vex._staff_grip_local(phase, action, ap)
        _NS_vex._draw_elite_staff(surface, pt, poly, dot, f, butt, orb,
                                  grip, phase, detail)

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
                          phase, detail):
        p = _NS_vex.PALETTE
        bx, by = pt(*butt)
        ox, oy = pt(*orb)
        _NS_vex._aaline(surface, p["shadow_deep"], (bx + f * 2, by + 1),
                        (ox + f * 2, oy + 1), 7)
        _NS_vex._aaline(surface, p["staff_dark"], (bx, by), (ox, oy), 5)
        _NS_vex._aaline(surface, p["staff_mid"], (bx, by), (ox, oy), 3)
        _NS_vex._aaline(surface, p["staff_light"], (bx, by), (ox, oy), 1)
        _NS_vex._aaline(surface, (*p["rune_mid"], 170),
                        (bx + f, by - 1), (ox + f, oy - 1), 1)
        for t in (.3, .62):
            rx = int(bx + (ox - bx) * t)
            ry = int(by + (oy - by) * t)
            _NS_vex._aacircle(surface, p["armor_darkest"], (rx, ry), 3)
            _NS_vex._aacircle(surface, p["void_bright"], (rx, ry), 1)
        # crescent claw cradle around the orb (tight, hugging the gem)
        for side in (-1, 1):
            prev = (int(bx + (ox - bx) * .9), int(by + (oy - by) * .9))
            for i in range(1, 6):
                t = i / 5.0
                cx2 = ox + side * math.sin(t * math.pi) * 6
                cy2 = oy + (1 - t) * 9 - t * 2
                _NS_vex._aaline(surface, p["staff_dark"], prev,
                                (cx2 + f, cy2), 3)
                _NS_vex._aaline(surface, p["staff_light"], prev,
                                (cx2, cy2), 1)
                prev = (cx2, cy2)
        pulse = .72 + math.sin(phase * 2.5) * .18
        for radius, color, alpha in ((10, p["void_dark"], 50),
                                     (7, p["void_mid"], 105),
                                     (5, p["void_light"], 180)):
            _NS_vex._aacircle(surface, (*color, int(alpha * pulse)),
                              (ox, oy), radius)
        _NS_vex._aacircle(surface, p["void_hot"], (ox, oy), 3)
        _NS_vex._aacircle(surface, p["void_white"], (ox - 1, oy - 1), 2)
        _NS_vex._aacircle(surface, p["white"], (ox - f, oy - 1), 1)
        for i in range(3):
            a = phase * 2 + i * math.tau / 3
            sx = int(ox + math.cos(a) * 9)
            sy = int(oy + math.sin(a) * 9)
            _NS_vex._aacircle(surface, p["orb_satellite"], (sx, sy), 1)


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
    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_void(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Void mist beneath floating Vex."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vex.PALETTE["void_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising void wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], alpha), (sx, sy), 5)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha), (sx, sy - 2), 3)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting rune fragments
        for i in range(4):
            angle = phase * 1.0 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_dark"], (sx, sy), 3)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_mid"], (sx, sy), 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_bright"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 24)
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_mid"], alpha),
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
        pygame.draw.ellipse(shadow, (*_NS_vex.PALETTE["void_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_void_silhouette_glow(surface, x, y, phase):
        """Layered cyan rim light for Vex's tall void-mage silhouette."""
        pulse = .72 + math.sin(phase * 1.4) * .16
        halo = pygame.Surface((104, 116), pygame.SRCALPHA)
        for radius, alpha in ((44, 9), (34, 15), (25, 22)):
            _NS_vex._aacircle(halo, (*_NS_vex.PALETTE["void_dark"],
                                      int(alpha * pulse)), (52, 58), radius)
        _NS_vex._aaline(halo, (*_NS_vex.PALETTE["void_mid"], int(40 * pulse)),
                         (36, 74), (21, 36), 2)
        _NS_vex._aaline(halo, (*_NS_vex.PALETTE["void_mid"], int(34 * pulse)),
                         (68, 57), (86, 32), 1)
        surface.blit(halo, (x - 52, y - 58))


    def _draw_void_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vex._aacircle(aura, (*_NS_vex.PALETTE["void_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_void_platform(surface, x, y, phase, skill):
        """Runic void circle on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_dark"], 180),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_mid"], 200),
                            (20, 14, 90, 16), 2)

        # Runic marks
        for i in range(8):
            angle = phase * 0.2 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 22)
            y1 = 22 + int(math.sin(angle) * 5)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_vex.PALETTE["void_light"], 180),
                             (x1, y1), (x2, y2), 1)

        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.15
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_vex.PALETTE["void_hot"], 220), (sx, sy), 2)

        if skill:
            color = _NS_vex.PALETTE["astral_light"] if skill == "e" else _NS_vex.PALETTE["void_bright"]
            pygame.draw.ellipse(ring, (*color, int(100 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_orb_release_flash(surface, x, y, facing, progress):
        """Flash when arcane orb is released."""
        if progress < 0.4 or progress > 0.7:
            return
        t = (progress - 0.4) / 0.3
        intensity = math.sin(t * math.pi)

        flash_x = x + 26 * facing
        flash_y = y - 20

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
    # SKILL Q: ARCANE ORB (charging)
    # ===================================================================
    def _draw_arcane_orb_charge(surface, boss, x, y, timer, phase):
        """Charging aura around Vex before empowered arcane orb."""
        progress = max(0.0, min(1.0, 1 - timer / 40))
        facing = boss.direction

        # Particles converging to staff tip
        tip_x = x + 26 * facing
        tip_y = y - 20

        for i in range(8):
            angle = phase * 3 + i * math.pi / 4
            r = 25 - int(progress * 15)
            px = tip_x + int(math.cos(angle) * r)
            py = tip_y + int(math.sin(angle) * r)
            alpha = int(200 * progress)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (px, py), 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (px, py), 1)


    # ===================================================================
    # SKILL E: ASTRAL IMPRISONMENT
    # ===================================================================
    def _draw_astral_indicator(surface, boss, x, y, timer, pulse):
        """Target indicator for astral imprisonment."""
        tx, ty = _NS_vex._target_position(boss, x, y)
        # Dashed line (tegas: stroke gelap + garis astral terang)
        for i in range(0, 20, 2):
            t1 = i / 20
            t2 = (i + 1) / 20
            _skill_outlined_line(
                surface,
                (x + (tx - x) * t1, y + (ty - y) * t1 - 8),
                (x + (tx - x) * t2, y + (ty - y) * t2 - 8),
                2, _NS_vex.PALETTE["astral_light"], 170)
        # Circle marker (tegas: outline gelap + cincin terang)
        _skill_outlined_circle(surface, (tx, ty), 22, 2,
                               _NS_vex.PALETTE["astral_mid"], 160)
        _skill_outlined_circle(surface, (tx, ty), 18, 1,
                               _NS_vex.PALETTE["astral_light"], 190)


    def _handle_astral_skill(surface, boss, x, y, timer, phase):
        """Spawns the astral orb once at start."""
        if not getattr(boss, "_vx_astral_spawned", False):
            _NS_vex._spawn_astral_orb(boss, x, y)
            boss._vx_astral_spawned = True
        if timer < 5:
            boss._vx_astral_spawned = False


    # ===================================================================
    # SKILL W: SANITY'S ECLIPSE (spike field)
    # ===================================================================
    def _draw_sanity_eclipse_ground(surface, boss, x, y, timer, phase):
        """Growing dark circle indicator on ground at target."""
        tx, ty = _NS_vex._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        if progress < 0.3:
            # Warning ring growing
            t = progress / 0.3
            radius = int(20 + t * 40)
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            # Tegas: outline gelap pekat + rim terang di dalam
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_darkest"], int(230 * pulse)),
                      (tx, ty + 15), radius + 2, 4)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_dark"], int(190 * pulse)),
                      (tx, ty + 15), radius - 2, 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(170 * pulse)),
                      (tx, ty + 15), radius - 5, 1)
            # Central portal
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"], (tx, ty + 15), 8)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_darkest"], (tx, ty + 15), 5)


    def _draw_sanity_eclipse(surface, boss, x, y, timer, phase):
        """Green spike field explosion."""
        tx, ty = _NS_vex._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        if progress < 0.3:
            # Central portal charging (already drawn on ground)
            # Rising energy inside portal
            for i in range(4):
                t = (phase * 0.6 + i * 0.25) % 1.0
                py = ty + 15 - int(t * 20)
                alpha = int(220 * (1 - t))
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                          (tx, py), 3)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (tx, py), 1)
        else:
            # Spikes erupt outward
            t = (progress - 0.3) / 0.7
            # Base black circle
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"], (tx, ty + 15), 10)

            # Spikes in ring pattern
            num_spikes = 12
            for i in range(num_spikes):
                angle = i * math.pi * 2 / num_spikes + phase * 0.1
                # Spike grows outward and up
                spike_grow = min(1.0, t * 2)
                dist = int(20 + spike_grow * 30)
                base_x = tx + int(math.cos(angle) * dist)
                base_y = ty + 15 + int(math.sin(angle) * dist * 0.4)

                # Spike shooting up
                spike_h = int(20 * spike_grow)
                if spike_h < 3:
                    continue

                _NS_vex._poly(surface, _NS_vex.PALETTE["void_darkest"], [
                    (base_x - 4, base_y + 4),
                    (base_x + 4, base_y + 4),
                    (base_x + 3, base_y - spike_h),
                    (base_x, base_y - spike_h - 3),
                    (base_x - 3, base_y - spike_h),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_dark"], [
                    (base_x - 3, base_y + 3),
                    (base_x + 3, base_y + 3),
                    (base_x + 2, base_y - spike_h + 1),
                    (base_x, base_y - spike_h - 2),
                    (base_x - 2, base_y - spike_h + 1),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_mid"], [
                    (base_x - 2, base_y + 2),
                    (base_x + 2, base_y + 2),
                    (base_x + 1, base_y - spike_h + 3),
                    (base_x, base_y - spike_h - 1),
                    (base_x - 1, base_y - spike_h + 3),
                ])
                # Bright edge
                _NS_vex._aaline(surface, _NS_vex.PALETTE["void_bright"],
                        (base_x, base_y - spike_h + 3),
                        (base_x, base_y + 2), 1)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"],
                          (base_x, base_y - spike_h), 1)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                          (base_x, base_y - spike_h), 1)

            # Inner ring of shorter spikes
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.15
                dist = 12
                base_x = tx + int(math.cos(angle) * dist)
                base_y = ty + 15 + int(math.sin(angle) * dist * 0.4)
                spike_h = int(12 * min(1.0, t * 2))
                if spike_h < 2:
                    continue
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_dark"], [
                    (base_x - 2, base_y + 2),
                    (base_x + 2, base_y + 2),
                    (base_x, base_y - spike_h),
                ])
                _NS_vex._poly(surface, _NS_vex.PALETTE["void_bright"], [
                    (base_x - 1, base_y + 1),
                    (base_x + 1, base_y + 1),
                    (base_x, base_y - spike_h + 1),
                ])

            # Ring shockwave
            ring_r = int(50 + t * 20)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(150 * (1 - t))),
                      (tx, ty + 15), ring_r, 2)


    # ===================================================================
    # SKILL R: ESSENCE FLUX (ultimate burst)
    # ===================================================================
    def _draw_essence_flux_ground(surface, boss, x, y, timer, phase):
        """Ground rune circle."""
        progress = max(0.0, min(1.0, 1 - timer / 80))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        radius = int(35 + progress * 20)

        ring = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_darkest"], int(210 * pulse)),
                            (3, 3, radius * 2 + 14, radius + 14), 5)
        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_dark"], int(210 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(ring, (*_NS_vex.PALETTE["void_mid"], int(230 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runes
        for i in range(6):
            a = phase * 0.5 + i * math.pi / 3
            px = cx + int(math.cos(a) * (radius - 4))
            py = cy + int(math.sin(a) * (radius // 2 - 3))
            pygame.draw.circle(ring, (*_NS_vex.PALETTE["void_hot"], 240), (px, py), 3)
            pygame.draw.circle(ring, _NS_vex.PALETTE["white"], (px, py), 1)

        surface.blit(ring, (x - cx, y + 30 - cy))


    def _draw_essence_flux(surface, boss, x, y, timer, phase):
        """Central burst of star-shaped energy."""
        progress = max(0.0, min(1.0, 1 - timer / 80))

        # Character-centered explosion
        burst_x = x
        burst_y = y - 10

        if progress < 0.35:
            # Charging - concentric rings inward
            t = progress / 0.35
            for i in range(3):
                r = int(50 - t * 30 - i * 8)
                if r > 2:
                    alpha = int(180 * t)
                    _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha),
                              (burst_x, burst_y), r, 2)

            # Central charging orb
            core_r = int(4 + t * 10)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_dark"],
                      (burst_x, burst_y), core_r + 4)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_mid"],
                      (burst_x, burst_y), core_r + 2)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_hot"], (burst_x, burst_y), core_r)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (burst_x, burst_y), core_r // 2)
        else:
            # Explosion phase - star burst
            t = (progress - 0.35) / 0.65

            # Central black hole void
            core_r = int(15 * (1 - t * 0.5))
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["shadow_deep"],
                      (burst_x, burst_y), core_r)
            _NS_vex._aacircle(surface, _NS_vex.PALETTE["void_darkest"],
                      (burst_x, burst_y), core_r - 2)

            # Star burst rays (4 main rays + 4 diagonal)
            num_rays = 8
            for i in range(num_rays):
                angle = i * math.pi / 4 + phase * 0.05
                ray_len = int(30 + t * 50)
                if i % 2 == 0:
                    ray_len = int(ray_len * 1.4)  # cardinal rays longer

                # Ray as elongated triangle
                perp = angle + math.pi / 2
                width = 5 * (1 - t * 0.7)
                if width < 1:
                    width = 1

                tip_x = burst_x + math.cos(angle) * ray_len
                tip_y = burst_y + math.sin(angle) * ray_len
                base_l_x = burst_x + math.cos(perp) * width
                base_l_y = burst_y + math.sin(perp) * width
                base_r_x = burst_x - math.cos(perp) * width
                base_r_y = burst_y - math.sin(perp) * width

                alpha = int(220 * (1 - t))
                _NS_vex._poly(surface, (*_NS_vex.PALETTE["void_dark"], alpha), [
                    (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y),
                ])
                _NS_vex._poly(surface, (*_NS_vex.PALETTE["void_mid"], alpha), [
                    (tip_x, tip_y),
                    (burst_x + math.cos(perp) * width * 0.6,
                     burst_y + math.sin(perp) * width * 0.6),
                    (burst_x - math.cos(perp) * width * 0.6,
                     burst_y - math.sin(perp) * width * 0.6),
                ])
                _NS_vex._poly(surface, (*_NS_vex.PALETTE["void_bright"], alpha), [
                    (tip_x, tip_y),
                    (burst_x + math.cos(perp) * width * 0.3,
                     burst_y + math.sin(perp) * width * 0.3),
                    (burst_x - math.cos(perp) * width * 0.3,
                     burst_y - math.sin(perp) * width * 0.3),
                ])
                _NS_vex._aaline(surface, _NS_vex.PALETTE["white"],
                        (burst_x, burst_y), (tip_x, tip_y), 1)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"],
                          (int(tip_x), int(tip_y)), 1)

            # Shockwave ring
            ring_r = int(20 + t * 60)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_light"], int(180 * (1 - t))),
                      (burst_x, burst_y), ring_r, 2)
            _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], int(150 * (1 - t))),
                      (burst_x, burst_y), ring_r + 3, 1)

            # Debris sparks
            for i in range(12):
                spark_angle = i * math.pi * 2 / 12 + phase * 0.3
                spark_r = int(t * 50)
                sx = burst_x + int(math.cos(spark_angle) * spark_r)
                sy = burst_y + int(math.sin(spark_angle) * spark_r)
                alpha = int(220 * (1 - t))
                _NS_vex._aacircle(surface, (*_NS_vex.PALETTE["void_bright"], alpha), (sx, sy), 2)
                _NS_vex._aacircle(surface, _NS_vex.PALETTE["white"], (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_vex.draw_vex(surface, boss, x, y)

# ====================================================================
# zephyr.py
# ====================================================================
class _NS_zephyr:
    """Namespace zephyr - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Dark Willow inspired (pink/magenta fey)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Warm fey skin — contrast is deliberately strong enough to survive
        # the arena downscale while retaining the reference's porcelain tone.
        "skin_darkest":   ( 83,  38,  52),
        "skin_dark":      (151,  76,  88),
        "skin_mid":       (218, 135, 142),
        "skin_light":     (248, 188, 181),
        "skin_high":      (255, 220, 208),

        # Crimson thorn-crown hair.
        "hair_darkest":   ( 50,   8,  28),
        "hair_dark":      (111,  18,  51),
        "hair_mid":       (181,  38,  78),
        "hair_light":     (232,  82, 123),
        "hair_shine":     (255, 142, 173),
        "hair_tip":       (255, 202, 221),

        # Layered plum/pink gown and fitted corset.
        "dress_darkest":  ( 25,   8,  38),
        "dress_dark":     ( 55,  17,  69),
        "dress_mid":      (108,  35, 112),
        "dress_light":    (166,  63, 148),
        "dress_high":     (220, 112, 188),
        "corset_dark":    ( 20,   7,  31),
        "corset_mid":     ( 59,  20,  70),
        "corset_light":   (124,  54, 130),
        "cloak_darkest":  ( 18,   7,  31),
        "cloak_dark":     ( 48,  19,  69),
        "cloak_mid":      ( 88,  41, 119),
        "cloak_light":    (157,  93, 185),
        "boot_darkest":   ( 19,  10,  30),
        "boot_dark":      ( 48,  25,  61),
        "boot_mid":       ( 91,  49, 104),
        "boot_light":     (174, 111, 178),
        "thread_light":   (240, 150, 210),

        # Moth wings: opaque ink rim plus translucent violet membranes.
        "wing_darkest":   ( 34,  12,  58),
        "wing_dark":      ( 76,  35, 119),
        "wing_mid":       (137,  78, 180),
        "wing_light":     (196, 135, 220),
        "wing_shine":     (244, 198, 250),
        "wing_vein":      ( 92,  45, 135),
        "wing_glass":     (229, 176, 241),

        # Living blackwood staff, amethyst jewel and thorn metal.
        "staff_dark":     ( 29,  15,  38),
        "staff_mid":      ( 72,  41,  70),
        "staff_light":    (133,  90, 126),
        "staff_vine":     (104,  43,  99),
        "staff_glow":     (255, 155, 221),
        "jewel_dark":     ( 80,  12,  73),
        "jewel_mid":      (191,  44, 151),
        "jewel_light":    (255, 159, 220),
        "thorn_dark":     ( 45,  13,  57),
        "thorn_mid":      ( 99,  35, 104),
        "thorn_light":    (190,  80, 161),
        # Retained names are used by established gameplay projectile code.
        "bramble_dark":   ( 45,  13,  57),
        "bramble_mid":    ( 99,  35, 104),
        "bramble_light":  (190,  80, 161),

        # Spell and rune values.
        "magic_darkest":  ( 42,   4,  42),
        "magic_dark":     (103,  13,  86),
        "magic_mid":      (181,  34, 141),
        "magic_light":    (234,  83, 181),
        "magic_bright":   (255, 139, 211),
        "magic_hot":      (255, 203, 238),
        "magic_white":    (255, 244, 252),
        "rune_dark":      ( 70,  22,  92),
        "rune_mid":       (157,  50, 156),
        "rune_light":     (242, 138, 218),

        # Antique gold circlet/corset hardware.
        "gold_dark":      ( 84,  55,  18),
        "gold_mid":       (162, 112,  36),
        "gold_light":     (236, 194,  92),

        # Violet-pink eyes and rose lips; the cool glow echoes the reference
        # while preserving a readable light iris at small arena scale.
        "eye_white":      (255, 236, 230),
        "eye_iris":       (153,  41, 104),
        "eye_iris_light": (255, 157, 211),
        "eye_pupil":      ( 20,   7,  15),
        "lips_dark":      (134,  22,  62),
        "lips_mid":       (218,  69, 119),

        "butterfly_dark": ( 59,  13,  68),
        "butterfly_mid":  (159,  49, 143),
        "butterfly_light":(245, 143, 218),
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   5,  13),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


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
            return _NS_zephyr._world_to_local(boss, x, y,
                                            target.x, target.y)
        # Tanpa target: terbang lurus ke arah hadap.
        scale = getattr(boss, "_render_scale", None)
        dist = 200 * (float(scale) if scale is not None else 1.0)
        return int(x + dist * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------
    def _draw_petal(surface, cx, cy, size, angle, dark, mid, light, shine=None):
        """Draw a small pointed petal (flame-like)."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.3) * size * 0.4
        base_l_y = cy + math.sin(angle + 2.3) * size * 0.4
        base_r_x = cx + math.cos(angle - 2.3) * size * 0.4
        base_r_y = cy + math.sin(angle - 2.3) * size * 0.4

        _NS_zephyr._poly(surface, dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        _NS_zephyr._poly(surface, mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_zephyr._aaline(surface, light, (cx, cy), (tip_x, tip_y), 1)
        if shine:
            _NS_zephyr._aacircle(surface, shine, (int(tip_x), int(tip_y)), 1)


    def _draw_butterfly(surface, cx, cy, size, phase, alpha=255):
        """Small butterfly."""
        wing_flap = math.sin(phase * 4) * 0.4 + 0.6
        ws = int(size * wing_flap)
        if ws < 1:
            ws = 1

        # Wings (4 petals)
        dark_col = (*_NS_zephyr.PALETTE["butterfly_dark"], alpha) if alpha < 255 else _NS_zephyr.PALETTE["butterfly_dark"]
        mid_col = (*_NS_zephyr.PALETTE["butterfly_mid"], alpha) if alpha < 255 else _NS_zephyr.PALETTE["butterfly_mid"]
        light_col = (*_NS_zephyr.PALETTE["butterfly_light"], alpha) if alpha < 255 else _NS_zephyr.PALETTE["butterfly_light"]

        # Upper wings
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx - ws * 2, cy - ws - 1),
            (cx - ws, cy),
        ])
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx + ws * 2, cy - ws - 1),
            (cx + ws, cy),
        ])
        _NS_zephyr._poly(surface, mid_col, [
            (cx, cy),
            (cx - ws * 2 + 1, cy - ws),
            (cx - ws, cy),
        ])
        _NS_zephyr._poly(surface, mid_col, [
            (cx, cy),
            (cx + ws * 2 - 1, cy - ws),
            (cx + ws, cy),
        ])
        # Lower wings (smaller)
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx - ws, cy + ws + 1),
            (cx - ws // 2, cy),
        ])
        _NS_zephyr._poly(surface, dark_col, [
            (cx, cy),
            (cx + ws, cy + ws + 1),
            (cx + ws // 2, cy),
        ])
        # Wing tip highlights
        _NS_zephyr._aacircle(surface, light_col, (cx - ws + 1, cy - ws // 2), 1)
        _NS_zephyr._aacircle(surface, light_col, (cx + ws - 1, cy - ws // 2), 1)

        # Body
        _NS_zephyr._aaline(surface, dark_col, (cx, cy - 1), (cx, cy + 2), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEMS
    # ---------------------------------------------------------------------------
    class MagicBoltProjectile:
        """Pink magic bolt basic attack."""
        def __init__(self, sx, sy, tx, ty, speed=7.5,
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
                    self.tx, self.ty = _NS_zephyr._world_to_local(
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

            # Trail - streaks of pink
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(20 + i * 15)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], alpha), (tx, ty), r + 2)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha // 2),
                          (tx, ty), r)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha // 2),
                          (tx, ty), max(1, r - 2))

            if self.alive:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.angle), math.sin(self.angle)

                # Glow halos
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], 130), (px, py), 14)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], 180), (px, py), 10)

                # Streaking bolt shape - elongated with tapered tail
                length = 12
                for i in range(6):
                    t = i / 5.0
                    bx = px - ca * length * t
                    by = py - sa * length * t
                    r = max(1, int(5 * (1 - t)))
                    if r > 0:
                        alpha = int(240 * (1 - t * 0.6))
                        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha),
                                  (int(bx), int(by)), r + 1)
                        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_light"], alpha),
                                  (int(bx), int(by)), r)
                        _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_hot"], alpha),
                                  (int(bx), int(by)), max(1, r - 1))

                # Bright core
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_white"], (px, py), 3)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"], (px, py), 1)

                # Tiny sparkle particles behind
                for i in range(3):
                    a = phase * 4 + i * math.pi * 2 / 3
                    pr = 4
                    spx = px - ca * 6 + int(math.cos(a) * pr)
                    spy = py - sa * 6 + int(math.sin(a) * pr)
                    _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (spx, spy), 1)


    class CasketProjectile:
        """Casket Curse - flying skull that traps target."""
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
                if self.age - self.impact_frame > 30:
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
                    self.tx, self.ty = _NS_zephyr._world_to_local(
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
            # Impact explosion
            if self.impact_frame >= 0:
                elapsed = self.age - self.impact_frame
                t = elapsed / 30.0

                # Explosion star burst
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], int(200 * (1 - t))),
                          (int(self.tx), int(self.ty)), int(20 + t * 30))
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], int(220 * (1 - t))),
                          (int(self.tx), int(self.ty)), int(15 + t * 25))
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], int(240 * (1 - t))),
                          (int(self.tx), int(self.ty)), int(8 + t * 20))

                # Star rays
                for i in range(8):
                    a = i * math.pi / 4 + phase * 0.1
                    ray_len = int(20 + t * 30)
                    ex = int(self.tx + math.cos(a) * ray_len)
                    ey = int(self.ty + math.sin(a) * ray_len)
                    _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_light"],
                                      int(200 * (1 - t))),
                            (int(self.tx), int(self.ty)), (ex, ey), 2)
                    _NS_zephyr._aaline(surface, (*_NS_zephyr.PALETTE["magic_hot"],
                                      int(220 * (1 - t))),
                            (int(self.tx), int(self.ty)), (ex, ey), 1)

                # Core white flash (early frames)
                if t < 0.4:
                    core_alpha = int(255 * (1 - t / 0.4))
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_white"], core_alpha),
                              (int(self.tx), int(self.ty)),
                              int(10 * (1 - t / 0.4)))
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["white"], core_alpha),
                              (int(self.tx), int(self.ty)),
                              max(1, int(5 * (1 - t / 0.4))))

                # Sparkle dust
                for i in range(10):
                    sa = i * math.pi * 2 / 10 + phase * 0.3
                    sr = int(t * 40)
                    sx = int(self.tx + math.cos(sa) * sr)
                    sy = int(self.ty + math.sin(sa) * sr)
                    alpha = int(200 * (1 - t))
                    _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha),
                              (sx, sy), 2)
                    _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["white"], (sx, sy), 1)
                return

            # Trail - wispy magenta
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 12)
                r = max(1, 4 - (len(self.trail) - i) // 2)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], alpha), (tx, ty), r + 3)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], alpha), (tx, ty), r + 1)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_bright"], alpha // 2),
                          (tx, ty), r)

            # Skull face projectile
            if self.alive:
                px, py = int(self.x), int(self.y)

                # Glow halo
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_dark"], 180), (px, py), 12)
                _NS_zephyr._aacircle(surface, (*_NS_zephyr.PALETTE["magic_mid"], 200), (px, py), 9)

                # Skull shape (small pink/magenta)
                # Skull dome
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_dark"], (px, py), 6)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_mid"], (px, py - 1), 5)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_light"], (px - 1, py - 2), 3)

                # Eye sockets (dark)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["shadow_deep"], (px - 2, py - 1), 1)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["shadow_deep"], (px + 2, py - 1), 1)
                # Glow inside sockets
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (px - 2, py - 1), 1)
                _NS_zephyr._aacircle(surface, _NS_zephyr.PALETTE["magic_hot"], (px + 2, py - 1), 1)

                # Jaw teeth line
                _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["shadow_deep"],
                        (px - 2, py + 3), (px + 2, py + 3), 1)

                # Wispy tendrils behind
                for i in range(3):
                    a = math.pi + self.angle + (i - 1) * 0.3
                    r = 8
                    tx = px + math.cos(a) * r
                    ty = py + math.sin(a) * r
                    _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["magic_mid"],
                            (px, py), (tx, ty), 2)
                    _NS_zephyr._aaline(surface, _NS_zephyr.PALETTE["magic_bright"],
                            (px, py), (tx, ty), 1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
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
        """Track attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zp_prev_timer", -1))
        active = bool(getattr(boss, "_zp_attack_active", False))

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
            boss._zp_attack_active = True
            active = True

        if active and timer <= 0:
            boss._zp_attack_active = False
            active = False

        boss._zp_prev_timer = timer

        # Progres diturunkan LANGSUNG dari timer simulasi, bukan dari
        # penghitung frame gambar. Durasi swing jadi identik di 60 FPS
        # maupun 8 FPS.
        boss._zp_attack_frame = max(0, cooldown - timer) if active else 0
        boss._zp_attack_progress = (
            min(1.0, boss._zp_attack_frame / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        for proj in boss._zp_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._zp_projectiles = [p for p in boss._zp_projectiles
                                if p.alive or p.dead_frames < 8]


    def _spawn_magic_bolt(boss, x, y):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # The bolt starts at the same pose-driven orb the rig renders.
        # Keeping this shared anchor prevents the spell from appearing to
        # emerge from Zephyr's waist after the masterwork staff upgrade.
        sx, sy = _NS_zephyr._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
        tgt = getattr(boss, "target", None)
        proj = _NS_zephyr.MagicBoltProjectile(
            sx, sy, tx, ty, speed=7.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._zp_projectiles.append(proj)


    def _spawn_casket(boss, x, y):
        if not hasattr(boss, "_zp_projectiles"):
            boss._zp_projectiles = []
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        sx, sy = _NS_zephyr._staff_orb_position(
            x, y, facing, float(getattr(boss, "pulse", 0.0)), "attack",
            float(getattr(boss, "_zp_attack_progress", 0.0)))
        tgt = getattr(boss, "target", None)
        proj = _NS_zephyr.CasketProjectile(
            sx, sy, tx, ty, speed=5.5,
            target=tgt, damage=0, team=getattr(boss, "team", None))
        # BUGFIX (orb random pada hero): simpan sumber hero
        # + titik pusat frame gambar agar re-home bisa
        # mengkonversi koordinat dunia -> lokal canvas.
        proj.source, proj.cx, proj.cy = boss, x, y
        boss._zp_projectiles.append(proj)


    # ===================================================================
    # ZEPHYR MASTERWORK — MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_zephyr(surface, boss, x, y):
        """Render Zephyr's procedural masterwork rig.

        The gameplay contract (Q/W/E/R timers, casket projectile and cache
        pipeline) intentionally stays unchanged.  Only the former collection
        of independent body stickers is replaced by one pose-driven rig.
        """
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zephyr._detect_moving(boss)
        _NS_zephyr._update_attack_anim(boss)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_zp_attack_active", False)
            or getattr(boss, "timer", 0) >
            getattr(boss, "attack_cooldown", 42) - 15
        )

        # Portraits deliberately contain only the character rig.  Auras and
        # arena-sized skill effects would force auto-crop to shrink Zephyr's
        # face, gown, wing material, and staff details.
        if not portrait_hd:
            _NS_zephyr._draw_fey_rim_light(surface, x, y - 13, pulse)
            _NS_zephyr._draw_fey_aura(surface, x, y, pulse)
            _NS_zephyr._draw_fey_platform(surface, x, y + 43, pulse,
                                          active_skill)

            if active_skill == "q":
                _NS_zephyr._draw_bramble_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                _NS_zephyr._draw_shadow_realm_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_zephyr._draw_bedlam_ground(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_zephyr._draw_casket_indicator(
                    surface, boss, x, y, skill_timer, pulse)

        if attacking:
            _NS_zephyr._draw_zephyr_attack(surface, boss, x, y)
        elif moving:
            _NS_zephyr._draw_zephyr_walk(surface, boss, x, y)
        else:
            _NS_zephyr._draw_zephyr_idle(surface, boss, x, y)

        if not portrait_hd:
            _NS_zephyr._manage_projectiles(boss, surface, pulse)

            if active_skill == "q":
                _NS_zephyr._draw_bramble_maze(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                _NS_zephyr._draw_shadow_realm(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_zephyr._handle_casket_skill(
                    surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_zephyr._draw_bedlam(
                    surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE ENTRY POINTS
    # ===================================================================
    def _draw_zephyr_idle(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(phase * .78) * 2)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x, y + 47)
            _NS_zephyr._draw_floating_sparkles(surface, x, y + 34, phase)
        _NS_zephyr._draw_zephyr_body(
            surface, x, y + bob, getattr(boss, "direction", 1), phase,
            "idle", detail=portrait_hd)


    def _draw_zephyr_walk(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0)) * 2.0
        stride = math.sin(phase * 1.72)
        bob = int(abs(stride) * 3)
        sway = int(stride * 2)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x + sway, y + 47)
            _NS_zephyr._draw_floating_sparkles(
                surface, x + sway, y + 35, phase, trail=True,
                facing=getattr(boss, "direction", 1))
        _NS_zephyr._draw_zephyr_body(
            surface, x + sway, y - bob, getattr(boss, "direction", 1),
            phase, "walk", detail=portrait_hd)


    def _draw_zephyr_attack(surface, boss, x, y):
        progress = max(0.0, min(1.0,
            float(getattr(boss, "_zp_attack_progress", 0.0))))
        phase = float(getattr(boss, "pulse", 0.0))
        facing = getattr(boss, "direction", 1)
        portrait_hd = bool(getattr(boss, "_portrait_hd", False))

        # The gameplay projectile remains authoritative in _entity.py.  This
        # renderer-only bolt is emitted only while a hero skill is active, so
        # it cannot double the normal ranged attack visual.
        if (getattr(boss, "active_skill", None) is not None
                and .48 < progress < .60
                and not getattr(boss, "_zp_proj_spawned", False)
                and not portrait_hd):
            _NS_zephyr._spawn_magic_bolt(boss, x, y)
            boss._zp_proj_spawned = True
        if progress < .15 or progress > .9:
            boss._zp_proj_spawned = False

        lunge = int(math.sin(progress * math.pi) * 4)
        recoil = -lunge * (1 if facing >= 0 else -1)
        if not portrait_hd:
            _NS_zephyr._draw_shadow(surface, x + recoil, y + 47)
            _NS_zephyr._draw_floating_sparkles(
                surface, x + recoil, y + 34, phase, intense=True,
                facing=facing)
        _NS_zephyr._draw_zephyr_body(
            surface, x + recoil, y, facing, phase, "attack", progress,
            detail=portrait_hd)
        if not portrait_hd:
            _NS_zephyr._draw_cast_flash(surface, x + recoil, y, facing,
                                        progress, phase)


    # ===================================================================
    # MASTERWORK RIG
    # ===================================================================
    def _staff_tip_local(phase, action="idle", attack_progress=0.0):
        """Pose-driven local orb position for Zephyr's thorn staff.

        Reference alignment: the crystal sits beside the face/forward
        shoulder rather than hovering above her head.  The shaft therefore
        reads as a crooked faerie wand in idle, then pulls back into the
        silhouette before thrusting forward for a bolt release.
        """
        wave = math.sin(phase * 1.35) * 1.4
        if action == "attack":
            ap = max(0.0, min(1.0, attack_progress))
            if ap < .40:
                # Wind-up: tuck the orb toward the hair and lift it.
                t = ap / .40
                return (int(42 - 22 * t), int(-19 - 18 * t + wave))
            if ap < .62:
                # Release: an unmistakable forward-pointing wand pose.
                t = (ap - .40) / .22
                return (int(20 + 47 * t), int(-37 + 17 * t + wave))
            # Recovery retains a slight forward reach instead of snapping.
            t = (ap - .62) / .38
            return (int(67 - 24 * t), int(-20 + 3 * t + wave))
        if action == "walk":
            return (int(42 + math.sin(phase * 1.72) * 3),
                    int(-19 + wave))
        return (42, int(-19 + wave))


    def _staff_orb_position(cx, cy, facing, phase=0.0, action="idle",
                            attack_progress=0.0):
        """World/canvas position of the staff orb for spell effects."""
        tx, ty = _NS_zephyr._staff_tip_local(phase, action, attack_progress)
        f = 1 if facing >= 0 else -1
        return int(cx + tx * f), int(cy + ty)


    def _draw_zephyr_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0.0, detail=False):
        """Render the replacement Zephyr masterwork body.

        Every visible material is generated from pygame primitives.  Unlike
        the retired torso/arms/skirt stickers, wings, hair, hands, gown and
        staff share the same `pt()` transform and thus react together to the
        walk, idle and casting pose.
        """
        _NS_zephyr._draw_zephyr_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail)


    def _draw_zephyr_rig(surface, cx, cy, facing, phase, action,
                         attack_progress=0.0, detail=False):
        """Explicit rig alias used by visual tooling and future cosmetics."""
        _NS_zephyr._draw_zephyr_elite(
            surface, cx, cy, facing, phase, action, attack_progress, detail)


    def _draw_zephyr_elite(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False):
        """Layered dark-fey bone rig: crown, moth wings, gown and staff."""
        p = _NS_zephyr.PALETTE
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        stride = math.sin(phase * 1.72)
        breath = math.sin(phase * .78)

        lean = int((3.5 * stride if walk else 0.0) +
                   (math.sin(ap * math.pi) * 7.0 if attack else 0.0))
        # v2 (animasi): perpindahan berat badan saat idle — goyang kiri-kanan.
        if not (walk or attack):
            lean = int(math.sin(phase * .8) * 3) * f
        root_y = int(breath * .9)
        if walk:
            root_y -= int(abs(stride) * 2.5)
        if attack:
            root_y += int(math.sin(ap * math.pi) * 2)

        def pt(dx, dy):
            return (int(cx + dx * f + lean), int(cy + dy + root_y))

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                  [(qx + f, qy + 1) for qx, qy in pts])
            _NS_zephyr._poly(surface, color, pts)
            return pts

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
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

        # ── back layer: wings and animated thorn-hair silhouette ──
        _NS_zephyr._draw_elite_wings(surface, pt, f, phase, action, detail)
        _NS_zephyr._draw_zephyr_crown(surface, pt, f, phase, detail)

        # A long asymmetric mantle makes the fairy readable from a 3/4 angle.
        mantle_wave = int(math.sin(phase * 1.18) * 3)
        mantle_push = 7 if walk or attack else 0
        poly(p["cloak_darkest"], [(-8, -23), (-18, -16),
             (-27 - mantle_push, -2 + mantle_wave),
             (-31 - mantle_push, 19 + mantle_wave), (-21, 15),
             (-10, 4), (-3, -12)])
        poly(p["cloak_dark"], [(-9, -21), (-17, -14),
             (-24 - mantle_push, 0 + mantle_wave),
             (-26 - mantle_push, 14 + mantle_wave), (-18, 10),
             (-8, 0)], False)
        _NS_zephyr._aaline(surface, p["cloak_light"], pt(-13, -17),
                            pt(-25 - mantle_push, 10 + mantle_wave), 1)

        # ── planted legs, tights and ankle boots ──
        # v2 (animasi): foot-lift bergantian saat jalan — kaki melangkah maju
        # terangkat (knee + telapak naik), kaki tumpuan tetap menapak.
        front_step = int(stride * 4) if walk else 0
        rear_step = -front_step
        if attack:
            front_step += int(ap * 5)
            rear_step -= int(ap * 3)
        stride_vel = math.cos(phase * 1.72) if walk else 0.0
        front_lift = int(max(0.0, stride_vel) * 8) if walk else 0
        rear_lift = int(max(0.0, -stride_vel) * 8) if walk else 0
        legs = ((-7, rear_step, p["boot_dark"], p["boot_mid"], rear_lift),
                (7, front_step, p["boot_mid"], p["boot_light"], front_lift))
        for i, (side, step, boot_base, boot_light, lift) in enumerate(legs):
            thigh_x = side + step
            # visible striped tights above the boot (knee rises with lift)
            poly(p["dress_darkest"], [(thigh_x - 5, 15),
                 (thigh_x + 5, 15), (thigh_x + 4, 29 - lift),
                 (thigh_x - 4, 29 - lift)])
            poly(p["dress_mid"], [(thigh_x - 3, 17),
                 (thigh_x + 3, 17), (thigh_x + 2, 28 - lift),
                 (thigh_x - 3, 28 - lift)], False)
            _NS_zephyr._aaline(surface, p["dress_light"],
                                pt(thigh_x - 1, 18), pt(thigh_x - 1, 27 - lift), 1)
            # pointed cuff, heel and toe establish ground contact.
            poly(p["boot_darkest"], [(thigh_x - 6, 27 - lift),
                 (thigh_x + 5, 27 - lift), (thigh_x + 6, 40 - lift),
                 (thigh_x - 5, 40 - lift)])
            poly(boot_base, [(thigh_x - 4, 28 - lift), (thigh_x + 3, 28 - lift),
                 (thigh_x + 4, 38 - lift), (thigh_x - 4, 38 - lift)], False)
            _NS_zephyr._aaline(surface, boot_light,
                                pt(thigh_x - 2, 30 - lift), pt(thigh_x - 1, 37 - lift), 1)
            toe = 4 * f
            foot = pt(thigh_x + (3 if f > 0 else -3), 40 - lift)
            _NS_zephyr._aaline(surface, p["shadow_deep"],
                                (foot[0] - toe, foot[1] + 1),
                                (foot[0] + toe, foot[1] + 1), 4)
            _NS_zephyr._aaline(surface, p["boot_light"],
                                (foot[0] - toe, foot[1]),
                                (foot[0] + toe, foot[1]), 2)

        # ── four independent petal panels of the gown ──
        skirt_wave = math.sin(phase * 1.1) * 2
        for i, (base_x, width, length) in enumerate(
                ((-13, 9, 27), (-4, 10, 31), (5, 10, 29), (14, 8, 24))):
            sway = int(skirt_wave * (1.0 + (i % 2) * .35) +
                       (stride * (i - 1.5) if walk else 0))
            dark = p["dress_darkest"] if i in (0, 3) else p["dress_dark"]
            mid = p["dress_mid"] if i != 1 else p["dress_light"]
            panel = [(base_x - width // 2, 0), (base_x + width // 2, 0),
                     (base_x + width // 2 + sway, length - 5),
                     (base_x + sway, length),
                     (base_x - width // 2 + sway - 2, length - 5)]
            poly(dark, panel)
            inset = [(base_x - width // 2 + 2, 2),
                     (base_x + width // 2 - 2, 2),
                     (base_x + width // 2 - 1 + sway, length - 7),
                     (base_x + sway, length - 3),
                     (base_x - width // 2 + 1 + sway, length - 7)]
            poly(mid, inset, False)
            _NS_zephyr._aaline(surface, p["dress_high"],
                                pt(base_x - 1, 4),
                                pt(base_x + sway, length - 5), 1)
            if i == 1:
                _NS_zephyr._aacircle(surface, p["jewel_light"],
                                      pt(base_x, 13), 1)

        # ── fitted torso, corset and shoulder mantle ──
        poly(p["dress_darkest"], [(-12, -26), (-4, -31), (8, -30),
             (14, -22), (11, 3), (4, 8), (-8, 6), (-13, -5)])
        poly(p["dress_mid"], [(-9, -25), (-3, -28), (7, -28),
             (11, -21), (8, 2), (2, 5), (-6, 4), (-10, -5)], False)
        # armored petal shoulder / collar
        poly(p["cloak_dark"], [(-13, -25), (-17, -31), (-12, -36),
             (-4, -31), (-7, -24)])
        poly(p["cloak_mid"], [(-13, -27), (-15, -31), (-11, -33),
             (-6, -30), (-8, -26)], False)
        poly(p["cloak_dark"], [(8, -29), (15, -33), (20, -28),
             (16, -21), (10, -23)])
        _NS_zephyr._aaline(surface, p["cloak_light"], pt(10, -29),
                            pt(17, -28), 1)

        # Corset is deliberately dark, then laced over high-value purple.
        poly(p["corset_dark"], [(-7, -20), (8, -20), (8, 1),
             (3, 5), (-5, 4), (-8, 0)])
        poly(p["corset_mid"], [(-5, -18), (6, -18), (6, 0),
             (2, 3), (-4, 2), (-6, 0)], False)
        _NS_zephyr._aaline(surface, p["corset_light"], pt(-3, -17),
                            pt(3, 1), 1)
        for j in range(4):
            yy = -15 + j * 4
            _NS_zephyr._aaline(surface, p["rune_light"], pt(-3, yy),
                                pt(3, yy + 2), 1)
            _NS_zephyr._aaline(surface, p["rune_light"], pt(3, yy),
                                pt(-3, yy + 2), 1)
        _NS_zephyr._aaline(surface, p["gold_dark"], pt(-11, 4),
                            pt(11, 4), 4)
        _NS_zephyr._aaline(surface, p["gold_mid"], pt(-10, 4),
                            pt(10, 4), 2)
        buckle = pt(1, 4)
        _NS_zephyr._aacircle(surface, p["gold_light"], buckle, 3)
        _NS_zephyr._aacircle(surface, p["jewel_mid"], buckle, 1)

        # ── pose-driven thorn staff ──
        staff_top = _NS_zephyr._staff_tip_local(phase, action, ap)
        # Crooked wand silhouette from the reference: low near the hip,
        # crystal forward beside Zephyr's shoulder rather than a vertical pole.
        staff_bottom = (2 + int(stride * 2 if walk else 0), 25)
        grip = (int(staff_bottom[0] * .48 + staff_top[0] * .52),
                int(staff_bottom[1] * .48 + staff_top[1] * .52))
        _NS_zephyr._draw_elite_staff(surface, pt, f, staff_bottom, staff_top,
                                     phase, action, detail)

        # ── rear arm first: free hand becomes a casting claw ──
        rear_shoulder = (-8, -22)
        if attack:
            rear_hand = (staff_top[0] - 7, staff_top[1] + 14)
            rear_elbow = (rear_hand[0] - 10, rear_hand[1] + 7)
        elif walk:
            rear_hand = (-14, -3 + int(stride * 5))
            rear_elbow = (-16, -13 - int(stride * 3))
        else:
            rear_hand = (-13, -3 + int(breath * 2))
            rear_elbow = (-17, -14 + int(breath))
        limb(rear_shoulder, rear_elbow, 6, p["cloak_dark"], p["cloak_mid"])
        limb(rear_elbow, rear_hand, 5, p["skin_dark"], p["skin_mid"])
        rhx, rhy = pt(*rear_hand)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], (rhx, rhy), 4)
        _NS_zephyr._aacircle(surface, p["skin_mid"], (rhx, rhy), 3)
        _NS_zephyr._aacircle(surface, p["skin_light"], (rhx - f, rhy - 1), 1)
        # delicate fingers make the spellcasting silhouette legible.
        for finger in (-2, 0, 2):
            _NS_zephyr._aaline(surface, p["skin_light"],
                                (rhx + f, rhy + finger),
                                (rhx + f * 4, rhy + finger - 2), 1)

        # ── head and expressive face ──
        # Neck appears before face and collar to keep proportions grounded.
        poly(p["skin_darkest"], [(-4, -33), (5, -33), (5, -24),
                                  (-3, -23)])
        poly(p["skin_mid"], [(-2, -33), (3, -33), (3, -25),
                              (-1, -24)], False)
        # Face is a 3/4 wedge: cheek and nose sit toward facing direction.
        poly(p["skin_darkest"], [(-10, -52), (2, -57), (11, -51),
             (13, -40), (8, -31), (-2, -29), (-10, -36), (-13, -45)])
        poly(p["skin_dark"], [(-8, -50), (2, -54), (9, -49),
             (10, -40), (6, -33), (-1, -31), (-8, -37), (-10, -45)],
             False)
        poly(p["skin_mid"], [(-5, -49), (2, -52), (7, -48),
             (8, -41), (4, -34), (-1, -33), (-6, -38)], False)
        poly(p["skin_light"], [(0, -50), (5, -48), (6, -42),
             (2, -38), (-2, -40)], False)
        # ear, nose, two bright amber eyes and mischievous mouth.
        _NS_zephyr._aacircle(surface, p["skin_mid"], pt(-9, -42), 3)
        _NS_zephyr._aacircle(surface, p["skin_light"], pt(-10, -43), 1)
        for ex, ey, radius in ((-2, -43, 2), (6, -43, 3)):
            px, py = pt(ex, ey)
            _NS_zephyr._aacircle(surface, p["eye_white"], (px, py), radius)
            _NS_zephyr._aacircle(surface, p["eye_iris"],
                                  (px + f, py), max(1, radius - 1))
            _NS_zephyr._aacircle(surface, p["eye_iris_light"],
                                  (px + f, py - 1), 1)
            _NS_zephyr._aacircle(surface, p["eye_pupil"],
                                  (px + f, py), 1)
            _NS_zephyr._aacircle(surface, p["white"],
                                  (px, py - 1), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"], pt(-5, -47),
                            pt(1, -48), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"], pt(3, -48),
                            pt(10, -47), 1)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], pt(11, -39), 1)
        _NS_zephyr._aaline(surface, p["lips_dark"], pt(3, -34),
                            pt(8, -34), 2)
        _NS_zephyr._aaline(surface, p["lips_mid"], pt(4, -34),
                            pt(7, -34), 1)

        # Fringe overlaps the brow while the crown remains behind it.
        hair_sway = int(math.sin(phase * 1.28) * 2)
        poly(p["hair_darkest"], [(-11, -52), (-7, -62), (1, -65),
             (10, -59), (13, -51), (7, -48), (4, -52), (1, -47),
             (-2, -53), (-6, -48)])
        poly(p["hair_dark"], [(-8, -53), (-5, -60), (1, -62),
             (8, -57), (10, -52), (5, -50), (1, -55), (-3, -50)], False)
        # five irregular bangs avoid a helmet silhouette.
        bangs = [(-7, -56, -8, -47), (-3, -59, -4, -49),
                 (1, -61, 0, -49), (5, -58, 4, -48),
                 (9, -55, 8, -48)]
        for i, (sx, sy, ex, ey) in enumerate(bangs):
            wiggle = hair_sway if i % 2 else -hair_sway
            poly(p["hair_mid"], [(sx - 2, sy), (sx + 2, sy),
                 (ex + wiggle, ey), (ex - 2 + wiggle, ey + 2)], False)
            _NS_zephyr._aaline(surface, p["hair_light"], pt(sx, sy + 1),
                                pt(ex + wiggle, ey), 1)
        _NS_zephyr._aacircle(surface, p["hair_shine"], pt(2, -61), 1)

        # ── front staff arm: grip is derived from staff endpoints ──
        front_shoulder = (8, -22)
        if attack:
            front_elbow = (grip[0] - 5, grip[1] + 8)
        elif walk:
            front_elbow = (grip[0] - 7, grip[1] + 5 + int(stride * 2))
        else:
            front_elbow = (grip[0] - 7, grip[1] + 6)
        limb(front_shoulder, front_elbow, 6, p["cloak_mid"], p["cloak_light"])
        limb(front_elbow, grip, 5, p["skin_dark"], p["skin_light"])
        ghx, ghy = pt(*grip)
        _NS_zephyr._aacircle(surface, p["skin_darkest"], (ghx, ghy), 4)
        _NS_zephyr._aacircle(surface, p["skin_mid"], (ghx, ghy), 3)
        _NS_zephyr._aacircle(surface, p["skin_high"], (ghx - f, ghy - 1), 1)
        # cuff and two rings on the staff hand.
        _NS_zephyr._aaline(surface, p["gold_dark"],
                            pt(front_elbow[0], front_elbow[1]),
                            pt((front_elbow[0] + grip[0]) // 2,
                               (front_elbow[1] + grip[1]) // 2), 4)
        _NS_zephyr._aaline(surface, p["gold_light"],
                            pt(front_elbow[0], front_elbow[1] - 1),
                            pt((front_elbow[0] + grip[0]) // 2,
                               (front_elbow[1] + grip[1]) // 2 - 1), 1)
        _NS_zephyr._aacircle(surface, p["gold_light"],
                              (ghx + f * 2, ghy), 1)

        # foreground side locks and small thorn earrings.
        poly(p["hair_dark"], [(-8, -49), (-13, -45),
             (-17 - hair_sway, -31), (-11, -28), (-5, -39)], False)
        _NS_zephyr._aaline(surface, p["hair_light"], pt(-10, -46),
                            pt(-14 - hair_sway, -32), 1)
        _NS_zephyr._aacircle(surface, p["jewel_light"], pt(-10, -39), 2)
        _NS_zephyr._aacircle(surface, p["jewel_mid"], pt(-10, -39), 1)

        # Clothing runes / body motes are lower-cost in arena and richer in
        # portrait mode.  They are tied to the root transform, not screen.
        for i in range(3 if not detail else 6):
            t = (phase * .22 + i / 6.0) % 1.0
            dx = -22 + i * 8 + int(math.sin(phase * 1.4 + i) * 2)
            dy = 22 - int(t * 58)
            _NS_zephyr._aacircle(surface,
                                  (*p["magic_bright"], int(145 * (1 - t))),
                                  pt(dx, dy), 1 if i % 2 else 2)
        if attack:
            orb_x, orb_y = pt(*staff_top)
            for i in range(6):
                ang = phase * 2.1 + i * math.pi / 3
                r = 7 + int(math.sin(phase + i) * 2)
                _NS_zephyr._aacircle(surface, (*p["magic_hot"], 190),
                                      (orb_x + int(math.cos(ang) * r),
                                       orb_y + int(math.sin(ang) * r)), 1)

        if detail:
            _NS_zephyr._draw_zephyr_masterwork_details(
                surface, pt, f, phase, action)


    def _draw_elite_wings(surface, pt, f, phase, action, detail=False):
        """Two pairs of translucent moth wings with independently moving tips."""
        p = _NS_zephyr.PALETTE
        flap = math.sin(phase * 3.0) * .12 + .88
        if action == "attack":
            flap += .08
        if action == "walk":
            flap += math.sin(phase * 1.72) * .05

        def wing_poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                  [(x + f, y + 1) for x, y in pts])
            _NS_zephyr._poly(surface, color, pts)

        for side in (-1, 1):
            lift = int((1.0 - flap) * 22)
            # Tall upper wing: pointed like a thorned moth leaf.
            upper = [(side * 3, -25), (side * 12, -44 + lift),
                     (side * 28, -61 + lift), (side * 39, -53 + lift),
                     (side * 33, -32), (side * 19, -17), (side * 6, -18)]
            wing_poly(p["wing_darkest"], upper)
            wing_poly((*p["wing_dark"], 220), [
                (side * 5, -25), (side * 14, -43 + lift),
                (side * 27, -57 + lift), (side * 34, -51 + lift),
                (side * 29, -34), (side * 17, -20), (side * 7, -20)],
                False)
            wing_poly((*p["wing_mid"], 165), [
                (side * 7, -25), (side * 17, -42 + lift),
                (side * 27, -53 + lift), (side * 29, -46 + lift),
                (side * 24, -34), (side * 15, -22)], False)
            # Lower wing is shorter, rounder, and has a different cadence.
            low_lift = int(math.sin(phase * 2.2 + side) * 2)
            lower = [(side * 4, -17), (side * 20, -18 + low_lift),
                     (side * 34, -5 + low_lift), (side * 28, 9),
                     (side * 13, 8), (side * 5, -4)]
            wing_poly(p["wing_darkest"], lower)
            wing_poly((*p["wing_dark"], 220), [
                (side * 6, -16), (side * 20, -16 + low_lift),
                (side * 30, -5 + low_lift), (side * 25, 5),
                (side * 14, 5), (side * 7, -4)], False)
            wing_poly((*p["wing_mid"], 150), [
                (side * 8, -14), (side * 20, -12 + low_lift),
                (side * 26, -4 + low_lift), (side * 21, 2),
                (side * 13, 1)], False)

            root = pt(side * 5, -21)
            tips = (pt(side * 28, -56 + lift),
                    pt(side * 31, -8 + low_lift),
                    pt(side * 24, -33 + lift))
            for tx, ty in tips:
                _NS_zephyr._aaline(surface, p["wing_vein"], root, (tx, ty), 2)
                _NS_zephyr._aaline(surface, p["wing_light"],
                                    (root[0] - f, root[1]),
                                    (tx - f, ty), 1)
            # A bright edge catches enough pixels to survive arena scaling.
            edge_a = pt(side * 28, -56 + lift)
            edge_b = pt(side * 34, -51 + lift)
            _NS_zephyr._aaline(surface, p["wing_shine"], edge_a, edge_b, 1)
            if detail:
                for j in range(3):
                    u = .32 + j * .18
                    vx = int(root[0] + (tips[0][0] - root[0]) * u)
                    vy = int(root[1] + (tips[0][1] - root[1]) * u)
                    _NS_zephyr._aacircle(surface, p["wing_glass"], (vx, vy), 1)


    def _draw_zephyr_crown(surface, pt, f, phase, detail=False):
        """Swept crimson petal-hair silhouette from the Zephyr reference.

        The large mass flows backward from the face (negative local X), with
        only a few forward thorns.  This keeps the sprite's 3/4 facing clear
        instead of reading as a symmetric crown pasted above the head.
        """
        p = _NS_zephyr.PALETTE

        def crown_poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_zephyr._poly(surface, p["shadow_deep"],
                                  [(x + f, y + 1) for x, y in pts])
            _NS_zephyr._poly(surface, color, pts)

        # Broad petal mass curves away from the face just like a living fey
        # plume; the outer silhouette remains dense at arena scale.
        crown_poly(p["hair_darkest"], [(-13, -47), (-27, -48),
                   (-35, -57), (-30, -66), (-38, -71), (-24, -74),
                   (-25, -84), (-12, -79), (-6, -91), (3, -78),
                   (12, -70), (16, -59), (11, -50), (3, -54),
                   (-5, -52)])
        crown_poly(p["hair_dark"], [(-11, -49), (-24, -51),
                   (-30, -58), (-25, -64), (-31, -69), (-20, -70),
                   (-20, -78), (-10, -74), (-5, -85), (1, -74),
                   (9, -67), (12, -59), (8, -52), (1, -56)], False)
        crown_poly(p["hair_mid"], [(-15, -52), (-25, -57),
                   (-22, -65), (-14, -68), (-9, -79), (-4, -70),
                   (3, -70), (7, -61), (3, -57)], False)

        # Seven separate locks give the reference's bristling petals genuine
        # secondary motion.  Most lean back; two retain the sharp front rim.
        spikes = [(-13, -54, -32, -62), (-17, -57, -38, -75),
                  (-15, -62, -29, -85), (-9, -65, -15, -90),
                  (-2, -66, -4, -94), (4, -62, 8, -82),
                  (9, -57, 20, -70)]
        for i, (sx, sy, ex, ey) in enumerate(spikes):
            wave = int(math.sin(phase * 1.18 + i * .73) * (1 + i % 3))
            crown_poly(p["hair_darkest"], [(sx - 3, sy + 2),
                       (sx + 3, sy + 2), (ex + wave, ey),
                       (sx + 1, sy - 4)])
            crown_poly(p["hair_mid"], [(sx - 1, sy), (sx + 2, sy),
                       (ex + wave, ey + 4), (sx, sy - 2)], False)
            _NS_zephyr._aaline(surface, p["hair_light"], pt(sx, sy - 1),
                                pt(ex + wave, ey + 4), 1)
            if i in (1, 3, 5):
                _NS_zephyr._aacircle(surface, p["hair_tip"],
                                      pt(ex + wave, ey + 3), 1)

        # A dark thorn circlet and amethyst pins retain the mischievous royal
        # accent without competing with the magenta hair at gameplay scale.
        _NS_zephyr._aaline(surface, p["gold_dark"], pt(-12, -56),
                            pt(11, -58), 3)
        _NS_zephyr._aaline(surface, p["gold_mid"], pt(-11, -57),
                            pt(10, -59), 1)
        for dx in (-7, -1, 6):
            bx, by = pt(dx, -57)
            _NS_zephyr._poly(surface, p["thorn_dark"],
                              [(bx, by), (bx + f * 3, by - 5),
                               (bx + f * 5, by)])
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                  (bx + f, by), 1)
        if detail:
            for dx, dy in ((-24, -60), (-20, -69), (-13, -76),
                           (-6, -82), (2, -73)):
                _NS_zephyr._aaline(surface, p["hair_shine"], pt(dx, dy),
                                    pt(dx + 3, dy - 5), 1)

    def _draw_elite_staff(surface, pt, f, bottom, top, phase, action,
                          detail=False):
        """Living thorn staff whose shaft and crystal are tied to the pose."""
        p = _NS_zephyr.PALETTE
        bx, by = pt(*bottom)
        tx, ty = pt(*top)
        _NS_zephyr._aaline(surface, p["shadow_deep"],
                            (bx + f * 2, by + 1), (tx + f * 2, ty + 1), 8)
        _NS_zephyr._aaline(surface, p["staff_dark"], (bx, by), (tx, ty), 6)
        _NS_zephyr._aaline(surface, p["staff_mid"], (bx - f, by),
                            (tx - f, ty), 4)
        _NS_zephyr._aaline(surface, p["staff_light"], (bx - f * 2, by - 1),
                            (tx - f * 2, ty - 1), 1)

        dx, dy = tx - bx, ty - by
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        # A vine coils around the shaft and terminates in tiny thorns.
        for i in range(5):
            t = .14 + i * .15
            sx, sy = bx + dx * t, by + dy * t
            swirl = math.sin(phase * 1.8 + i * 1.7) * 2.0
            ex, ey = sx + nx * (5 + swirl), sy + ny * (5 + swirl)
            _NS_zephyr._aaline(surface, p["staff_vine"],
                                (int(sx), int(sy)), (int(ex), int(ey)), 2)
            _NS_zephyr._aaline(surface, p["thorn_light"],
                                (int(ex), int(ey)),
                                (int(ex + nx * 3 + dx / length * 2),
                                 int(ey + ny * 3 + dy / length * 2)), 1)
        # Crystal orb: dark halo -> faceted gem -> concentrated white core.
        orb_pulse = .72 + math.sin(phase * 2.5) * .18
        for radius, color, alpha in ((14, p["magic_dark"], 48),
                                     (10, p["magic_mid"], 100),
                                     (7, p["magic_bright"], 180)):
            _NS_zephyr._aacircle(surface, (*color, int(alpha * orb_pulse)),
                                  (tx, ty), radius)
        _NS_zephyr._poly(surface, p["jewel_dark"],
                          [(tx, ty - 7), (tx + f * 6, ty - 1),
                           (tx + f * 2, ty + 7), (tx - f * 5, ty + 2)])
        _NS_zephyr._poly(surface, p["jewel_mid"],
                          [(tx, ty - 5), (tx + f * 4, ty - 1),
                           (tx + f, ty + 5), (tx - f * 3, ty + 1)])
        _NS_zephyr._aaline(surface, p["staff_glow"], (tx, ty - 5),
                            (tx + f * 3, ty + 1), 2)
        _NS_zephyr._aacircle(surface, p["jewel_light"],
                              (tx - f * 2, ty - 2), 2)
        _NS_zephyr._aacircle(surface, p["magic_white"],
                              (tx - f * 2, ty - 3), 1)
        # forked thorn crown around the orb
        for side in (-1, 1):
            _NS_zephyr._aaline(surface, p["thorn_dark"],
                                (tx, ty + 3),
                                (tx + f * side * 7, ty - 8), 3)
            _NS_zephyr._aaline(surface, p["thorn_light"],
                                (tx + f * side, ty + 1),
                                (tx + f * side * 6, ty - 7), 1)
        if detail:
            for i in range(4):
                t = .24 + i * .15
                rx, ry = int(bx + dx * t), int(by + dy * t)
                _NS_zephyr._aacircle(surface, p["rune_light"], (rx, ry), 1)


    def _draw_zephyr_masterwork_details(surface, pt, f, phase, action):
        """Portrait-only material pass: seams, wing spots and jewelry."""
        p = _NS_zephyr.PALETTE
        # fine corset stitching and embroidery on the central petal
        for yy in range(-18, 2, 3):
            _NS_zephyr._aacircle(surface, p["gold_light"], pt(0, yy), 1)
        for i in range(3):
            y = 10 + i * 6
            _NS_zephyr._aaline(surface, p["dress_high"], pt(-3, y),
                                pt(2, y + 3), 1)
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                  pt(3, y + 2), 1)
        # collar rivets and wing-root jewelry
        for dx, dy in ((-11, -25), (11, -24), (-5, -28), (6, -28)):
            _NS_zephyr._aacircle(surface, p["gold_mid"], pt(dx, dy), 1)
        _NS_zephyr._aacircle(surface, p["jewel_light"], pt(-13, -19), 2)
        # face shadow, lashes and a tiny beauty mark retain the reference's
        # mischievous personality when viewed in Hero Shop.
        _NS_zephyr._aaline(surface, p["skin_high"], pt(1, -50),
                            pt(5, -49), 1)
        _NS_zephyr._aaline(surface, p["hair_darkest"], pt(5, -46),
                            pt(10, -47), 1)
        _NS_zephyr._aacircle(surface, p["lips_dark"], pt(8, -37), 1)
        # hem stitch rhythm follows the moving gown rather than screen space.
        hem_phase = int(math.sin(phase * 1.1) * 2)
        for dx in (-12, -6, 0, 6, 12):
            _NS_zephyr._aacircle(surface, p["thread_light"],
                                  pt(dx + hem_phase, 26 + abs(dx) // 5), 1)


    # ===================================================================
    # ARENA AMBIENCE
    # ===================================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((112, 28), pygame.SRCALPHA)
        for radius in range(22, 3, -4):
            alpha = max(0, int((24 - radius) * 4.5))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (56 - radius * 2, 13 - radius // 3,
                                 radius * 4, max(3, radius // 2)))
        pygame.draw.ellipse(shadow, (*_NS_zephyr.PALETTE["magic_dark"], 38),
                            (15, 10, 82, 10))
        surface.blit(shadow, (int(x - 56), int(y - 14)))


    def _draw_fey_rim_light(surface, x, y, phase):
        """Low-alpha silhouette halo kept behind the wing material."""
        p = _NS_zephyr.PALETTE
        pulse = .72 + math.sin(phase * 1.25) * .16
        halo = pygame.Surface((120, 132), pygame.SRCALPHA)
        center = (60, 66)
        for radius, alpha in ((54, 8), (43, 13), (31, 20)):
            _NS_zephyr._aacircle(halo, (*p["magic_dark"], int(alpha * pulse)),
                                  center, radius)
        _NS_zephyr._aaline(halo, (*p["wing_mid"], int(36 * pulse)),
                            (33, 84), (18, 36), 2)
        _NS_zephyr._aaline(halo, (*p["wing_mid"], int(36 * pulse)),
                            (87, 84), (102, 36), 2)
        surface.blit(halo, (int(x - 60), int(y - 66)))


    def _draw_fey_aura(surface, x, y, phase):
        p = _NS_zephyr.PALETTE
        pulse = .72 + math.sin(phase * .55) * .20
        aura = pygame.Surface((164, 142), pygame.SRCALPHA)
        for radius in range(58, 7, -5):
            alpha = int((61 - radius) * 1.15 * pulse)
            if alpha > 0:
                _NS_zephyr._aacircle(aura, (*p["magic_darkest"], alpha),
                                      (82, 67), radius)
        surface.blit(aura, (int(x - 82), int(y - 72)))


    def _draw_fey_platform(surface, x, y, phase, skill=None):
        p = _NS_zephyr.PALETTE
        pulse = .76 + math.sin(phase * 1.2) * .18
        ring = pygame.Surface((142, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*p["magic_dark"], int(160 * pulse)),
                            (4, 12, 134, 25), 3)
        pygame.draw.ellipse(ring, (*p["rune_mid"], int(180 * pulse)),
                            (17, 16, 108, 17), 2)
        pygame.draw.ellipse(ring, (*p["magic_bright"], int(145 * pulse)),
                            (29, 19, 84, 11), 1)
        for i in range(8):
            ang = phase * .7 + i * math.pi / 4
            px = 71 + int(math.cos(ang) * 54)
            py = 25 + int(math.sin(ang) * 9)
            _NS_zephyr._aacircle(ring, p["rune_light"], (px, py), 1)
        if skill:
            pygame.draw.ellipse(ring, (*p["magic_hot"], int(150 * pulse)),
                                (11, 9, 120, 30), 1)
        surface.blit(ring, (int(x - 71), int(y - 24)))


    def _draw_floating_sparkles(surface, cx, cy, phase, trail=False,
                                 facing=1, intense=False):
        p = _NS_zephyr.PALETTE
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((118, 36), pygame.SRCALPHA)
        for radius in range(25, 4, -4):
            alpha = int((27 - radius) * 3.0 * strength)
            pygame.draw.ellipse(mist, (*p["magic_dark"], alpha),
                                (59 - radius * 2, 18 - radius // 3,
                                 radius * 4, max(3, radius // 2)))
        surface.blit(mist, (int(cx - 59), int(cy - 9)))
        for i, offset in enumerate((-23, -10, 4, 18)):
            t = (phase * .48 + i * .23) % 1.0
            sx = int(cx + offset + math.sin(phase + i) * 3)
            sy = int(cy + 5 - t * 31)
            alpha = int(215 * (1 - t) * strength)
            _NS_zephyr._aacircle(surface, (*p["magic_mid"], alpha),
                                  (sx, sy), 3)
            _NS_zephyr._aacircle(surface, (*p["magic_bright"], alpha),
                                  (sx, sy - 1), 1)
        for i in range(2):
            angle = phase * 1.08 + i * math.pi
            bx = int(cx + math.cos(angle) * 24)
            by = int(cy - 6 + math.sin(angle * 1.3) * 8)
            _NS_zephyr._draw_butterfly(surface, bx, by, 3, phase + i)
        if trail:
            f = 1 if facing >= 0 else -1
            for i in range(5):
                alpha = 140 - i * 23
                _NS_zephyr._aacircle(surface, (*p["magic_mid"], alpha),
                                      (int(cx - f * (13 + i * 10)),
                                       int(cy + math.sin(phase + i) * 2)),
                                      max(1, 4 - i // 2))


    def _draw_cast_flash(surface, x, y, facing, progress, phase=0.0):
        if progress < .37 or progress > .72:
            return
        p = _NS_zephyr.PALETTE
        t = (progress - .37) / .35
        intensity = math.sin(t * math.pi)
        fx, fy = _NS_zephyr._staff_orb_position(
            x, y, facing, phase, "attack", progress)
        for radius, color, alpha in ((24, p["magic_dark"], 65),
                                     (16, p["magic_mid"], 150),
                                     (9, p["magic_bright"], 220)):
            _NS_zephyr._aacircle(surface, (*color, int(alpha * intensity)),
                                  (fx, fy), int(radius * intensity) + 1)
        _NS_zephyr._aacircle(surface, p["magic_white"], (fx, fy),
                              max(1, int(3 * intensity)))
        for i in range(6):
            angle = phase * 2.0 + i * math.pi / 3
            ray = int(10 + 18 * intensity)
            ex = fx + int(math.cos(angle) * ray)
            ey = fy + int(math.sin(angle) * ray)
            _NS_zephyr._aaline(surface, (*p["magic_hot"],
                                          int(220 * intensity)),
                                (fx, fy), (ex, ey), 1)


    # ===================================================================
    # SKILL Q — BRAMBLE MAZE
    # ===================================================================
    def _draw_fey_arc(surface, cx, cy, rx, ry, start, end, color,
                      width=1, segments=18):
        """Draw an elliptical procedural arc without relying on image assets."""
        previous = None
        for i in range(segments + 1):
            t = i / float(max(1, segments))
            angle = start + (end - start) * t
            point = (int(cx + math.cos(angle) * rx),
                     int(cy + math.sin(angle) * ry))
            if previous is not None:
                _NS_zephyr._aaline(surface, color, previous, point, width)
            previous = point


    def _draw_bramble_ground(surface, boss, x, y, timer, phase):
        origin = getattr(boss, "_bramble_origin", None)
        if origin:
            tx, ty = _NS_zephyr._world_to_local(boss, x, y,
                                                 origin[0], origin[1])
        else:
            tx, ty = _NS_zephyr._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        radius = int(22 + min(1.0, progress * 3.5) * 34)
        pulse = .7 + math.sin(phase * 3.0) * .2
        _NS_zephyr._ellipse(surface,
                             (*_NS_zephyr.PALETTE["magic_darkest"],
                              int(145 * pulse)),
                             (int(tx - radius), int(ty + 15 - radius * .32),
                              radius * 2, max(4, int(radius * .64))))
        # Tegas: rim gelap pekat + arc rune terang di atas
        _NS_zephyr._ellipse(surface,
                             (*_NS_zephyr.PALETTE["magic_dark"], int(215 * pulse)),
                             (int(tx - radius), int(ty + 15 - radius * .32),
                              radius * 2, max(4, int(radius * .64))), 3)
        _NS_zephyr._draw_fey_arc(surface, tx, ty + 15, radius, int(radius * .32),
                                  phase, phase + math.pi * 1.45,
                                  (*_NS_zephyr.PALETTE["rune_mid"], 215), 2)


    def _draw_bramble_maze(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        origin = getattr(boss, "_bramble_origin", None)
        if origin:
            tx, ty = _NS_zephyr._world_to_local(boss, x, y,
                                                 origin[0], origin[1])
        else:
            tx, ty = _NS_zephyr._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        grow = min(1.0, progress * 4.0)
        fade = min(1.0, (1.0 - progress) * 7.0)
        if grow <= .02:
            return
        ring_r = int(30 + grow * 28)
        for i in range(12):
            angle = i * math.tau / 12.0 + phase * .10
            bx = tx + int(math.cos(angle) * ring_r)
            by = ty + 15 + int(math.sin(angle) * ring_r * .34)
            # The vines lean inward, leaving a readable hostile ring.
            curl = math.sin(phase * 1.8 + i * 1.7) * 4
            tip_x = bx - int(math.cos(angle) * (10 + grow * 10)) + int(curl)
            tip_y = by - int((24 + (i % 3) * 5) * grow)
            px, py = -math.sin(angle) * 4, math.cos(angle) * 4
            _NS_zephyr._poly(surface, p["thorn_dark"], [
                (int(bx + px), int(by + py)), (int(bx - px), int(by - py)),
                (tip_x, tip_y)])
            _NS_zephyr._poly(surface, p["thorn_mid"], [
                (int(bx + px * .62), int(by + py * .62)),
                (int(bx - px * .62), int(by - py * .62)), (tip_x, tip_y)],)
            _NS_zephyr._aaline(surface, p["thorn_light"], (bx, by),
                                (tip_x, tip_y), 1)
            for t in (.32, .58, .80):
                vx = int(bx + (tip_x - bx) * t)
                vy = int(by + (tip_y - by) * t)
                side = -1 if i % 2 else 1
                _NS_zephyr._draw_petal(surface, vx, vy, 5,
                    angle + side * 1.6, p["thorn_dark"], p["thorn_mid"],
                    p["thorn_light"], p["jewel_light"])
            _NS_zephyr._aacircle(surface, p["jewel_mid"], (tip_x, tip_y), 3)
            _NS_zephyr._aacircle(surface, p["jewel_light"],
                                  (tip_x - 1, tip_y - 1), 1)
        alpha = int(205 * fade)
        _NS_zephyr._draw_fey_arc(surface, tx, ty + 15, ring_r + 4,
                                  int((ring_r + 4) * .34), phase,
                                  phase + math.tau, (*p["rune_mid"], alpha), 2)
        _NS_zephyr._draw_fey_arc(surface, tx, ty + 15, ring_r - 5,
                                  int((ring_r - 5) * .34), -phase,
                                  -phase + math.tau, (*p["magic_bright"], alpha), 1)
        for i in range(4):
            t = (phase * .45 + i * .25) % 1.0
            _NS_zephyr._draw_butterfly(surface,
                int(tx + math.sin(phase + i) * (18 + t * 20)),
                int(ty + 10 - t * 28), 3, phase + i,
                alpha=int(220 * (1 - t)))


    # ===================================================================
    # SKILL W — SHADOW REALM
    # ===================================================================
    def _draw_shadow_realm_ground(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 180.0))
        radius = int(34 + min(1.0, progress * 5) * 17)
        _NS_zephyr._ellipse(surface, (*p["magic_darkest"], 155),
                             (x - radius, y + 31 - radius // 3,
                              radius * 2, max(5, radius * 2 // 3)))
        _NS_zephyr._ellipse(surface, (*p["magic_dark"], 215),
                             (x - radius, y + 31 - radius // 3,
                              radius * 2, max(5, radius * 2 // 3)), 3)
        _NS_zephyr._draw_fey_arc(surface, x, y + 31, radius, radius * .32,
                                  phase, phase + math.tau,
                                  (*p["rune_mid"], 225), 2)
        for i in range(6):
            a = phase * .7 + i * math.tau / 6
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                  (int(x + math.cos(a) * (radius - 5)),
                                   int(y + 31 + math.sin(a) * radius * .30)), 1)


    def _draw_shadow_realm(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 180.0))
        envelope = min(1.0, progress * 8.0, (1.0 - progress) * 8.0)
        radius = max(3, int(47 * envelope))
        if radius <= 3:
            return
        cx, cy = x, y - 12
        pulse = .78 + math.sin(phase * 2.6) * .16
        # The realm is a crescent glass dome, not an opaque circle over Zephyr.
        _NS_zephyr._aacircle(surface, (*p["magic_dark"], int(42 * pulse)),
                              (cx, cy), radius)
        for off, alpha, width in ((0, 180, 2), (4, 120, 2), (9, 75, 1)):
            _NS_zephyr._draw_fey_arc(surface, cx, cy, radius - off,
                                      radius - off, .18, math.pi - .18,
                                      (*p["magic_bright"], int(alpha * pulse)),
                                      width, 22)
        _NS_zephyr._draw_fey_arc(surface, cx, cy, radius - 3, radius - 3,
                                  math.pi + .20, math.tau - .20,
                                  (*p["wing_mid"], int(145 * pulse)), 1, 20)
        # glass highlight and drifting petal reflections
        _NS_zephyr._aacircle(surface, p["magic_hot"],
                              (cx - radius // 2, cy - radius // 2), 3)
        for i in range(7):
            a = phase * 2.0 + i * math.tau / 7
            r = radius * (.52 + (i % 2) * .16)
            sx = int(cx + math.cos(a) * r)
            sy = int(cy + math.sin(a) * r)
            _NS_zephyr._aacircle(surface, (*p["wing_shine"], 170),
                                  (sx, sy), 1 if i % 2 else 2)
        _NS_zephyr._draw_fey_arc(surface, cx, cy + 30, radius,
                                  radius * .22, phase, phase + math.pi,
                                  (*p["rune_light"], 190), 1)


    # ===================================================================
    # SKILL E — CASKET CURSE
    # ===================================================================
    def _draw_casket_indicator(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        tx, ty = _NS_zephyr._target_position(boss, x, y)
        sx, sy = _NS_zephyr._staff_orb_position(
            x, y, getattr(boss, "direction", 1), phase)
        # segmented thorn tether makes the target relationship explicit.
        dx, dy = tx - sx, ty - sy
        dist = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / dist, dx / dist
        for i in range(9):
            t1 = i / 9.0
            t2 = min(1.0, (i + .54) / 9.0)
            wobble1 = math.sin(phase * 3 + i) * 3
            wobble2 = math.sin(phase * 3 + i + .6) * 3
            a = (int(sx + dx * t1 + nx * wobble1),
                 int(sy + dy * t1 + ny * wobble1))
            b = (int(sx + dx * t2 + nx * wobble2),
                 int(sy + dy * t2 + ny * wobble2))
            _skill_outlined_line(surface, a, b, 3, p["magic_dark"], 200)
            _skill_outlined_line(surface, a, b, 1, p["magic_bright"], 225)
        _skill_outlined_circle(surface, (tx, ty), 9, 2, p["jewel_mid"], 200)
        _NS_zephyr._aacircle(surface, p["jewel_light"], (tx, ty), 2)


    def _handle_casket_skill(surface, boss, x, y, timer, phase):
        if not getattr(boss, "_zp_casket_spawned", False):
            _NS_zephyr._spawn_casket(boss, x, y)
            boss._zp_casket_spawned = True
        if timer < 5:
            boss._zp_casket_spawned = False


    # ===================================================================
    # SKILL R — BEDLAM
    # ===================================================================
    def _draw_bedlam_ground(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        radius = int(45 + min(1.0, progress * 4) * 20)
        _NS_zephyr._ellipse(surface, (*p["magic_darkest"], 170),
                             (x - radius, y + 31 - radius // 3,
                              radius * 2, max(6, radius * 2 // 3)))
        _NS_zephyr._ellipse(surface, (*p["magic_dark"], 220),
                             (x - radius, y + 31 - radius // 3,
                              radius * 2, max(6, radius * 2 // 3)), 3)
        for i in range(3):
            rr = radius - i * 9
            _NS_zephyr._draw_fey_arc(surface, x, y + 31, rr, rr * .29,
                                      phase * (1.0 + i * .25) + i,
                                      phase * (1.0 + i * .25) + i + math.tau,
                                      (*p["magic_mid"], 190 - i * 38),
                                      2 if i == 0 else 1)
        for i in range(10):
            a = phase * .95 + i * math.tau / 10
            _NS_zephyr._aacircle(surface, p["rune_light"],
                                  (int(x + math.cos(a) * (radius - 4)),
                                   int(y + 31 + math.sin(a) * radius * .28)), 2)


    def _draw_bedlam(surface, boss, x, y, timer, phase):
        p = _NS_zephyr.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / 240.0))
        envelope = min(1.0, progress * 5.0, (1.0 - progress) * 5.0)
        for i in range(6):
            angle = phase * 2.35 + i * math.tau / 6.0
            orbit_r = 43 + int(math.sin(phase * 1.7 + i) * 6)
            dx = int(x + math.cos(angle) * orbit_r)
            dy = int(y - 11 + math.sin(angle) * orbit_r * .42)
            alpha = max(50, min(235, int((174 + math.sin(phase * 2 + i) * 48)
                                         * max(.28, envelope))))
            _NS_zephyr._draw_mini_fairy(surface, dx, dy, phase + i * .33,
                                         alpha,
                                         facing=1 if math.cos(angle) >= 0 else -1)
            # trailing glitter marks the orbit direction.
            for tail in range(3):
                ta = angle - .22 * (tail + 1)
                _NS_zephyr._aacircle(surface,
                    (*p["magic_bright"], max(20, alpha - tail * 55)),
                    (int(x + math.cos(ta) * orbit_r),
                     int(y - 11 + math.sin(ta) * orbit_r * .42)),
                    max(1, 3 - tail))
        # Three discontinuous spell ribbons make the clone circle feel alive.
        for i in range(3):
            _NS_zephyr._draw_fey_arc(surface, x, y - 10,
                                      46 - i * 5, 16 - i * 2,
                                      phase * 1.9 + i * 2.1,
                                      phase * 1.9 + i * 2.1 + 1.52,
                                      (*p["magic_hot"], 190 - i * 38), 1, 13)
        for i in range(12):
            a = phase * 1.4 + i * math.tau / 12
            r = 49 + int(math.sin(phase * 2 + i) * 6)
            _NS_zephyr._aacircle(surface, p["magic_white"],
                                  (int(x + math.cos(a) * r),
                                   int(y - 8 + math.sin(a) * r * .45)), 1)


    def _draw_mini_fairy(surface, cx, cy, phase, alpha, facing=1):
        """Compact masterwork silhouette used by the Bedlam orbit."""
        p = _NS_zephyr.PALETTE
        f = 1 if facing >= 0 else -1
        flap = int(math.sin(phase * 3) * 2)
        for side in (-1, 1):
            _NS_zephyr._poly(surface, (*p["wing_dark"], alpha // 2), [
                (cx + f * 2, cy - 6), (cx + f * side * 11, cy - 16 + flap),
                (cx + f * side * 14, cy - 8), (cx + f * side * 6, cy - 2)])
            _NS_zephyr._aaline(surface, (*p["wing_shine"], alpha // 2),
                                (cx + f * 2, cy - 6),
                                (cx + f * side * 10, cy - 14 + flap), 1)
        _NS_zephyr._poly(surface, (*p["dress_dark"], alpha), [
            (cx - 5, cy - 2), (cx + 5, cy - 2), (cx + 7, cy + 10),
            (cx, cy + 14), (cx - 6, cy + 9)])
        _NS_zephyr._poly(surface, (*p["corset_mid"], alpha), [
            (cx - 3, cy - 3), (cx + 3, cy - 3), (cx + 3, cy + 3),
            (cx - 3, cy + 3)])
        _NS_zephyr._aacircle(surface, (*p["skin_mid"], alpha),
                              (cx + f, cy - 9), 5)
        for i in range(3):
            _NS_zephyr._aaline(surface, (*p["hair_mid"], alpha),
                                (cx + f * (i - 1), cy - 12),
                                (cx + f * (i - 2), cy - 19 - (i % 2) * 2), 2)
        _NS_zephyr._aacircle(surface, (*p["eye_iris_light"], alpha),
                              (cx + f * 2, cy - 9), 1)
        _NS_zephyr._aaline(surface, (*p["staff_light"], alpha),
                            (cx + f * 5, cy + 8), (cx + f * 10, cy - 15), 2)
        _NS_zephyr._aacircle(surface, (*p["jewel_light"], alpha),
                              (cx + f * 10, cy - 16), 2)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_zephyr.draw_zephyr(surface, boss, x, y)
