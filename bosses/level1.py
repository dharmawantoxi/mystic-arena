"""
bosses/level1.py - Semua boss Level 1

Gabungan dari 4 file terpisah:
  - gornak               (mini boss)
  - morgath              (mini boss)
  - drakar               (mini boss)
  - abaddon              (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace aslinya TIDAK diubah isinya; hanya
referensi antar-simbol yang diberi prefix.

KECUALI gornak: namespace-nya adalah Pixel Masterwork v2 + Skill FX v2.1
(Thorne bar: ramp 4-5 band, selout, tuft, specular cluster, dither,
FX world-space lewat _fx_scale). Regresi: tools/test_gornak_masterwork.py,
audit: tools/_audit_gornak_v2.py, sheet: tools/_shot_gornak_masterwork.py.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True

# ====================================================================
# GORNAK (ANTI-MAGE) - Mini Boss  ·  PROCEDURAL MASTERWORK RIG
# ====================================================================
import math
import pygame

try:                     # pass cahaya bersama; opsional supaya file boss
    import lighting as _lighting          # tetap bisa di-load sendiri
except Exception:        # pragma: no cover
    _lighting = None


class _NS_gornak:
    """Namespace gornak - Anti-Mage mini boss (PIXEL MASTERWORK v3).

    Renderer 100% prosedural (tanpa PNG, sprite sheet, atau image.load).
    Ditulis ulang penuh dari v2: rig, animasi, ayunan pedang, proyektil,
    dan seluruh FX skill.

    Yang berubah di v3
    ------------------
    * RENDER. Satu sistem ramp 5-band (``_RAMP``) memasok SEMUA material,
      jadi nilai kulit/baja/kain/bilah tidak pernah lagi saling tabrak.
      Setiap bidang digambar dengan pola yang sama: core gelap -> body ->
      plane cahaya -> selout sisi bayangan -> specular cluster 1-2 px.
      Hierarki nilai dikunci: MATA > permata ungu > mata-bilah > pelat >
      kulit > kain.
    * BILAH. Bukan lagi tiga poligon inset (yang terbaca sebagai jarum
      putih), tapi bilah asimetris sungguhan: punggung gelap, badan mid,
      MATA bilah 1 px terang di sisi potong, fuller ungu, hamon dither,
      guard + pommel. Terbaca sebagai senjata di 1x maupun di kartu.
    * ANIMASI. Kurva serangan baru (anticipation -> tebas -> HOLD ->
      follow-through) plus gerak sekunder: kepala, jenggot, mohawk, cape,
      dan loincloth semuanya tertinggal dari badan (lag) alih-alih ikut
      kaku.
    * SWING. ``_draw_crescent_slash`` sekarang menyapu DUA pita: bilah
      depan (busur besar) dan bilah belakang (cross-cut), keduanya dibuat
      dari trail ujung bilah yang sebenarnya, jadi tidak pernah lepas dari
      senjata.
    * PROYEKTIL. Bolt Mana Break v3: kepala panah runcing berorientasi
      arah terbang, inti 3 lapis, dua pecahan yang mengorbit spiral,
      after-image ter-kuantisasi (stamp, bukan garis mulus), lalu impact
      retak + serpihan.
    * FX SKILL. Q/W/E/R ditulis ulang dengan bahasa yang sama: telegraph
      -> aktivasi -> steady, semuanya world-space lewat ``_fx_scale``
      (E = 100 px dunia, R = 180 px dunia di CASTER).

    Kontrak yang TIDAK berubah (dipakai gameplay & tes regresi):
      * ``draw_gornak(surface, boss, x, y)`` entry point tunggal.
      * telapak dipatok di ``GROUND_DY``; bilah pose-driven; FX lahir dari
        ``_tip_screen``; portrait LOD membuang FX arena.
      * ``SKILL_DUR`` sinkron dengan AI boss & skill hero.

    Regresi: tools/test_gornak_masterwork.py
    Sheet  : tools/_shot_gornak_masterwork.py
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _STATIC_SURFACES = {}

    # ── SKALA BADAN ───────────────────────────────────────────────
    # Rujukan keluarga (diukur dari render, alpha>=100):
    #   boss 1x : morgath H82/W120, abaddon H122/W150
    #   hero    : kaizen 75x83, grimjaw 74x79, vex 75x83, sylara 77x90
    # SCALE memperbesar rig, LIFT memindahkan jangkar ke bawah supaya
    # pipeline HD hero menormalkan tingginya SAMA seperti hero lain.
    SCALE = 1.32
    LIFT = 4
    # Telapak dalam RUANG LOKAL; garis tanah dunia diturunkan dari sini
    # supaya bayangan, rune tanah, dan telapak tidak pernah saling lepas.
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT        # ~ 54

    # Buffer rig: dibatasi dari extents TERUKUR semua pose (idle/walk/
    # attack/surge/ward/void/blink, dua LOD) + margin. Buffer sekecil
    # mungkin karena outline siluet meng-copy-nya 4-5x per frame.
    RIG_W, RIG_H = 176, 160
    RIG_OX, RIG_OY = 74, 96

    # Bidang acuan pass cahaya (lighting.py): kotak TETAP di dalam buffer,
    # bukan bbox per frame - kalau ikut bbox, arah cahaya bergeser tiap
    # ganti pose dan terbaca sebagai lampu berkedip.
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)

    # Durasi status skill (frame) - HARUS sama dengan active_skill_timer
    # yang diisi AI boss (bosses/base_boss.py) dan skill hero
    # (hero_skills/_bundle.py). Dikunci tools/test_gornak_masterwork.py.
    SKILL_DUR = {"q": 40, "w": 25, "e": 60, "r": 90}

    # Penanda "sedang di-render ke canvas hero" (lane).
    class _HERO_LANE:
        v = False

    PALETTE = {
        # ── Kulit sawo matang berdebu (5 band + 1 hot) ──────────────
        "skin_darkest": (30, 15, 10),
        "skin_dark": (78, 40, 23),
        "skin_mid": (148, 88, 48),
        "skin_light": (203, 145, 92),
        "skin_shine": (238, 190, 138),
        "skin_high": (252, 224, 186),

        # ── Mohawk (ungu sihir) ────────────────────────────────────
        "hair_darkest": (22, 7, 36),
        "hair_dark": (50, 17, 82),
        "hair_mid": (104, 43, 156),
        "hair_light": (162, 100, 216),
        "hair_shine": (218, 174, 252),

        # ── Jenggot & alis ─────────────────────────────────────────
        "beard_darkest": (20, 11, 11),
        "beard_dark": (42, 24, 21),
        "beard_mid": (74, 45, 36),
        "beard_light": (112, 74, 56),

        # ── Kain jubah / loincloth ─────────────────────────────────
        "robe_darkest": (11, 6, 20),
        "robe_dark": (30, 18, 50),
        "robe_mid": (58, 36, 90),
        "robe_light": (98, 66, 140),
        "robe_edge": (154, 118, 196),

        # ── Baja "spellbreaker" ────────────────────────────────────
        "armor_darkest": (7, 6, 12),
        "armor_dark": (26, 24, 37),
        "armor_mid": (76, 72, 99),
        "armor_light": (140, 134, 167),
        "armor_shine": (208, 204, 234),

        # ── Bilah silver-biru + garis temper ───────────────────────
        # Hierarki nilai: mata > permata > mata-bilah > pelat > bilah.
        "blade_darkest": (18, 18, 30),
        "blade_dark": (36, 34, 52),
        "blade_mid": (96, 100, 128),
        "blade_light": (164, 170, 196),
        "blade_shine": (212, 218, 242),
        "blade_hamon": (168, 196, 236),
        "blade_edge": (188, 204, 236),

        # ── Kulit tan & kuningan paku ──────────────────────────────
        "leather_dark": (46, 28, 17),
        "leather_mid": (88, 55, 33),
        "leather_light": (134, 91, 56),
        "brass_dark": (94, 66, 23),
        "brass_mid": (172, 132, 51),
        "brass_light": (230, 202, 116),

        # ── Aura anti-sihir (FX utama) ─────────────────────────────
        "magic_void": (36, 7, 70),
        "magic_darkest": (24, 5, 44),
        "magic_dark": (58, 19, 108),
        "magic_mid": (130, 55, 200),
        "magic_light": (186, 111, 241),
        "magic_hot": (221, 161, 255),
        "magic_shine": (245, 210, 255),
        "magic_core": (255, 236, 255),

        # ── Mata menyala (nilai TERTINGGI di seluruh sprite) ───────
        "eye_dark": (56, 17, 76),
        "eye_mid": (182, 92, 222),
        "eye_light": (242, 182, 255),
        "eye_glow": (255, 236, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (4, 2, 8),
        "white": (255, 255, 255),
    }

    # Ramp 5 band: (core, dark, body, light, shine). SATU tabel supaya
    # setiap bidang di badan memakai tangga nilai yang sama - itu yang
    # membuat pixel-art terbaca "satu tangan", bukan tempelan.
    _RAMP = {
        "skin": ("skin_darkest", "skin_dark", "skin_mid", "skin_light",
                 "skin_shine"),
        "armor": ("armor_darkest", "armor_dark", "armor_mid", "armor_light",
                  "armor_shine"),
        "robe": ("robe_darkest", "robe_dark", "robe_mid", "robe_light",
                 "robe_edge"),
        "leather": ("shadow_deep", "leather_dark", "leather_mid",
                    "leather_light", "brass_light"),
        "blade": ("blade_darkest", "blade_dark", "blade_mid", "blade_light",
                  "blade_shine"),
        "hair": ("hair_darkest", "hair_dark", "hair_mid", "hair_light",
                 "hair_shine"),
        "magic": ("magic_darkest", "magic_dark", "magic_mid", "magic_light",
                  "magic_hot"),
        "brass": ("shadow_deep", "brass_dark", "brass_mid", "brass_light",
                  "white"),
    }

    def _band(ramp, i):
        """Warna band ke-i (0=core .. 4=shine) dari ramp bernama."""
        keys = _NS_gornak._RAMP[ramp]
        return _NS_gornak.PALETTE[keys[max(0, min(4, int(i)))]]

    # ==================================================================
    # PRIMITIF HELPER (mendukung warna alpha lewat surface sementara)
    # ==================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gornak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius,
                               width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gornak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_gornak._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = max(1, int(width))
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 6
            h = abs(ey - sy) + width * 4 + 6
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), width)
            surface.blit(temp, (min_x, min_y))
            return
        if _NS_gornak.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color[:3], (sx, sy), (ex, ey))
                return
            except Exception:
                pass
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    def _poly(surface, color, points):
        if not points or len(points) < 3:
            return
        color = _NS_gornak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(temp, color,
                                [(p[0] - min_x, p[1] - min_y) for p in points])
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], (rx, ry, rw, rh), width)

    def _rect(surface, color, rect):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], (rx, ry, rw, rh))

    # ==================================================================
    # V3 FX VOCABULARY (world-space + pixel-art)
    # ==================================================================
    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_gornak._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _static(key, builder):
        surf = _NS_gornak._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_gornak._STATIC_SURFACES[key] = surf
        return surf

    def _fx_scale(boss):
        """Faktor skala efek skill.

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek ikut menyusut. Dengan faktor ini efek digambar
        lebih besar di canvas sehingga ukurannya DI LAYAR setara boss
        asli (world-space). Boss asli (tanpa _render_scale) = 1.0.
        """
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_r):
        """Radius canvas untuk ``world_r`` piksel dunia."""
        return max(1, int(round(float(world_r) * _NS_gornak._fx_scale(boss))))

    def _world_to_local(boss, x, y, wx, wy):
        """Titik dunia -> ruang gambar renderer (clamp ke canvas)."""
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

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_gornak._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_gornak._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_gornak._aaline(
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
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_gornak._aaline(surface, (*color, alpha), p0, p1, thick)

    _SEAL_N = 32               # segmen rim segel arcane
    _SEAL_CACHE = {}

    def _seal_plate(radius, fs, nodes, star, teeth, ab):
        """Bagian STATIS segel (rim bergerigi, gigi radial, bintang-poligon,
        simpul kristal) di-bake sekali per (radius, fs) lalu di-blit.

        Alasan: tiap garis ber-alpha di _aaline bikin satu temp surface;
        40 segmen per frame = mahal. Yang benar-benar bergerak hanya sapuan
        cahaya, dan itu cuma beberapa segmen -> digambar live di atas plate.
        """
        p = _NS_gornak.PALETTE
        key = (int(radius), round(float(fs), 2), nodes, star, bool(teeth), ab)
        cache = _NS_gornak._SEAL_CACHE
        got = cache.get(key)
        if got is not None:
            return got
        pad = int(10 * fs) + 6
        c = int(radius) + pad
        size = c * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        rim, hot, core = p["magic_light"], p["magic_hot"], p["magic_shine"]
        # Alpha di-bake ke dalam plate (di-bucket) supaya blit-nya TIDAK
        # perlu set_alpha: per-pixel-alpha + surface-alpha memaksa jalur
        # blit lambat di SDL (1.16 ms vs 0.07 ms untuk plate 534x534).
        k_a = ab / 255.0
        n = _NS_gornak._SEAL_N
        thick = max(1, int(1.5 * fs))
        prev = None
        for i in range(n + 1):
            k = i % n
            ang = k * math.tau / n
            rr = radius + (_NS_gornak._hash01(k * 3 + 1) - 0.5) * 1.4
            q = (c + math.cos(ang) * rr, c + math.sin(ang) * rr)
            if prev is not None:
                pygame.draw.line(surf, (*rim, int(205 * k_a)), prev, q,
                                 thick)
                # garis kedua tipis di dalam: batas AOE jadi "dua tarikan
                # pena", bukan satu lingkaran vektor
                pygame.draw.line(
                    surf, (*p["magic_mid"], int(120 * k_a)),
                    (c + (prev[0] - c) * 0.94, c + (prev[1] - c) * 0.94),
                    (c + (q[0] - c) * 0.94, c + (q[1] - c) * 0.94), 1)
            prev = q
            if teeth and k % 5 == 0:
                ln = (3 + (3 if k % 10 == 0 else 0)) * fs
                pygame.draw.line(surf, (*rim, int(175 * k_a)), q,
                                 (c + math.cos(ang) * (rr + ln),
                                  c + math.sin(ang) * (rr + ln)), 1)
        pts = []
        for i in range(nodes):
            ang = -math.pi / 2 + i * math.tau / nodes
            pts.append((c + math.cos(ang) * radius,
                        c + math.sin(ang) * radius))
        # Tali bintang-poligon sengaja DIPOTONG: hanya pangkalnya yang
        # digambar, jadi terbaca sebagai kurung sudut segel di tepi -
        # bukan sangkar kawat yang menutupi badan.
        for i in range(nodes):
            q = pts[i]
            r2 = pts[(i * star) % nodes]
            dxc, dyc = r2[0] - q[0], r2[1] - q[1]
            for a0, b0 in ((0.0, 0.15), (0.85, 1.0)):
                pygame.draw.line(
                    surf, (*rim, int(120 * k_a)),
                    (q[0] + dxc * a0, q[1] + dyc * a0),
                    (q[0] + dxc * b0, q[1] + dyc * b0), 1)
        for i in range(nodes):
            q = pts[i]
            na = math.atan2(q[1] - c, q[0] - c)
            _NS_gornak._shard(surf, q[0], q[1], na, int(7 * fs),
                              max(2, int(2 * fs)), hot, int(235 * k_a),
                              core=core)
        if len(cache) > 24:
            cache.clear()
        cache[key] = surf
        return surf

    def _arcane_seal(surface, cx, cy, radius, phase, alpha, fs=1.0,
                     nodes=7, star=3, rim=None, hot=None, core=None,
                     spin=1.0, teeth=True):
        """Segel arcane: pengganti 'lingkaran vektor' penanda AOE.

        Batas AOE tetap terbaca persis di ``radius`` (jitter <= 1 px, jadi
        gameplay tidak berbohong), tapi bentuknya bukan lingkaran halus:
        rim bergerigi hasil hash, gigi radial seperti skala jam matahari,
        simpul kristal, dan bintang-poligon di dalamnya - satu bahasa
        bentuk dengan _shard milik Gornak. Sapuan cahaya berputar
        mengelilingi rim supaya segel terasa hidup.
        """
        p = _NS_gornak.PALETTE
        alpha = _NS_gornak._alpha(alpha)
        if alpha <= 0 or radius < 6:
            return
        ab = max(48, min(255, int(round(alpha / 48.0)) * 48))
        plate = _NS_gornak._seal_plate(int(radius), fs, nodes, star, teeth,
                                       ab)
        c = plate.get_width() // 2
        surface.blit(plate, (int(cx) - c, int(cy) - c))
        # Sapuan cahaya: hanya beberapa segmen, digambar live.
        hot = hot or p["magic_hot"]
        rim = rim or p["magic_light"]
        n = _NS_gornak._SEAL_N
        head = (phase * spin * 0.16) % 1.0
        thick = max(1, int(1.5 * fs))
        for j in range(3):
            t0 = head - j / float(n)
            k = int(round(t0 * n)) % n
            f0 = 1.0 - j / 3.0
            a0 = _NS_gornak._alpha(alpha * (0.35 + 0.65 * f0))
            if a0 <= 0:
                continue
            pq = []
            for kk in (k, k + 1):
                ang = (kk % n) * math.tau / n
                rr = radius + (_NS_gornak._hash01((kk % n) * 3 + 1) - .5) * 1.4
                pq.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
            # pygame.draw.line langsung (bukan _aaline): sapuan ini nyaris
            # opak, jadi tidak perlu temp surface per segmen.
            pygame.draw.line(surface, (*(hot if f0 > 0.5 else rim), a0),
                             (int(pq[0][0]), int(pq[0][1])),
                             (int(pq[1][0]), int(pq[1][1])),
                             thick + (1 if f0 > 0.66 else 0))

    def _rune_orbit(surface, cx, cy, radius, phase, alpha, fs=1.0,
                    count=12, spin=1.0, color=None, core=None):
        """Barisan rune yang mengorbit (pengganti cincin dalam)."""
        p = _NS_gornak.PALETTE
        if alpha <= 0 or radius < 3:
            return
        color = color or p["magic_mid"]
        core = core or p["magic_light"]
        for i in range(count):
            ang = phase * spin + i * math.tau / count
            _NS_gornak._shard(surface, cx + math.cos(ang) * radius,
                              cy + math.sin(ang) * radius,
                              ang + math.pi / 2, int(5 * fs),
                              max(1, int(2 * fs)), color, alpha, core=core)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_gornak._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_gornak._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_gornak._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bergerigi (pixel-art fur/kain)."""
        if not spine:
            return spine
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
                d = depth * (0.55 + 0.45 * _NS_gornak._hash01(
                    i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _dither_dots(surface, color, points, alpha=70):
        """Checkerboard 50% 1-px (band dither klasik)."""
        a = _NS_gornak._alpha(alpha)
        col = (*_NS_gornak._clamp(color)[:3], a)
        for x, y in points:
            ix, iy = int(x), int(y)
            if (ix + iy) & 1:
                _NS_gornak._rect(surface, col, (ix, iy, 1, 1))

    def _shard(surface, cx, cy, ang, length, width, color, alpha,
               core=None):
        """Serpihan kristal mana: belah ketupat runcing searah ``ang``.

        Dipakai proyektil, impact, dan debris ayunan - bentuk yang sama
        di semua tempat supaya FX Gornak punya "bahasa" visual sendiri.
        """
        if alpha <= 0 or length <= 1:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        pts = [(cx + ca * length, cy + sa * length),
               (cx + nx * width, cy + ny * width),
               (cx - ca * length * 0.45, cy - sa * length * 0.45),
               (cx - nx * width, cy - ny * width)]
        _NS_gornak._poly(surface, (*color, _NS_gornak._alpha(alpha)),
                         [(int(px), int(py)) for px, py in pts])
        if core:
            _NS_gornak._aaline(
                surface, (*core, _NS_gornak._alpha(alpha)),
                (int(cx - ca * length * 0.3), int(cy - sa * length * 0.3)),
                (int(cx + ca * length * 0.8), int(cy + sa * length * 0.8)), 1)

    def _ribbon(surface, path, widths, color, alpha):
        """Pita tebal-tipis dari daftar titik (trail ujung bilah)."""
        if len(path) < 3 or alpha <= 0:
            return
        left, right = [], []
        for i, (px, py) in enumerate(path):
            if i == 0:
                dx, dy = path[1][0] - px, path[1][1] - py
            elif i == len(path) - 1:
                dx, dy = px - path[-2][0], py - path[-2][1]
            else:
                dx = path[i + 1][0] - path[i - 1][0]
                dy = path[i + 1][1] - path[i - 1][1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            w = widths[i]
            left.append((px + nx * w, py + ny * w))
            right.append((px - nx * w, py - ny * w))
        _NS_gornak._poly(surface, (*color, _NS_gornak._alpha(alpha)),
                         [(int(a), int(b)) for a, b in left + right[::-1]])

    def _skill_progress(boss, skill):
        dur = float(_NS_gornak.SKILL_DUR.get(skill, 40) or 40)
        timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        return max(0.0, min(1.0, 1.0 - timer / dur))

    def _clamp_fx_xy(boss, x, y, px, py):
        """Jaga FX di dalam canvas hero (rumus = _canvas_size_for)."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(px), int(py)
        scale = float(scale) or 1.0
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 12
        ox, oy = px - x, py - y
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    # ==================================================================
    # KOORDINAT TARGET (kompensasi scale untuk jalur hero offscreen)
    # ==================================================================
    def _target_position(boss, x, y):
        """Posisi target dalam ruang jangkar (x, y) renderer ini."""
        target = getattr(boss, "target", None)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        if target is not None and getattr(target, "alive", True):
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 120.0 / scale * getattr(boss, "direction", 1)),
                int(y))

    # ==================================================================
    # CONTROLLER ANIMASI  (state, fase, timing, delta-time, jendela hit)
    # ==================================================================
    # Batas fase = fraksi 0..1 dari DURASI SERANGAN (bukan dari waktu pose
    # yang sudah dilengkungkan _attack_curve). Batasnya sengaja jatuh
    # PERSIS di patahan kurva, jadi nama fase, grip bilah, dan sudut
    # bilah tidak pernah berbeda satu frame.
    ATTACK_ANTICIPATION_END = 0.16      # counter-motion kecil ke belakang
    ATTACK_WINDUP_END = 0.30            # bilah di atas kepala + TAHAN
    ATTACK_SWING_END = 0.46             # tebasan turun (paling cepat)
    ATTACK_IMPACT_END = 0.60            # HOLD impact -> freeze 1-2 frame
    ATTACK_FOLLOW_END = 0.80            # follow-through
    #: jendela di mana bilah secara geometris menyapu depan badan
    ATTACK_ACTIVE_WINDOW = (0.36, 0.62)
    #: puncak benturan (dipakai FX untuk memicu spark "di udara")
    ATTACK_IMPACT_FRAME = 0.53

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.16),
        ("WINDUP",       0.16, 0.30),
        ("SWING",        0.30, 0.46),
        ("IMPACT",       0.46, 0.60),
        ("FOLLOW",       0.60, 0.80),
        ("RECOVERY",     0.80, 1.00),
    )

    #: Prioritas state. Angka besar menang; DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "SKILL": 50,
        "SPECIAL": 55,
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: Aktifkan untuk melihat hitbox/hurtbox/jangkauan/state di arena
    #: (jalur boss 1:1). Untuk lane hero, overlay yang sama tersedia di
    #: heroes/gornak_fx.DEBUG_CHARACTER.
    DEBUG_CHARACTER = False

    def attack_phases_order():
        """Urutan nama fase (dipakai test & alat audit)."""
        return tuple(name for name, _a, _b in _NS_gornak.ATTACK_PHASES)

    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1 (None di luar serangan)."""
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_gornak.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _resolve_anim_state(boss, attacking, phase):
        """Tentukan state animasi yang DIINGINKAN frame ini."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_gnk_hurt_frames", 0)) > 0:
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
        """Rect hitbox ayunan (ruang permukaan) saat jendela hit aktif.

        Dipakai overlay debug dan alat audit; return None di luar jendela
        hit supaya tidak pernah terlihat seperti "pedang menembus tembok".
        """
        if not getattr(boss, "_gnk_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        scale = _NS_gornak._fx_scale(boss)
        reach = int(58 * scale)
        top = int(cy - 34 * scale)
        h = int(64 * scale)
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    def _update_gnk_attack_anim(boss):
        """ANIMATION CONTROLLER Gornak - state, fase, timing, delta-time.

        Dulu fungsi ini cuma menghitung timer untuk pose serangan. Sekarang
        ia satu-satunya sumber kebenaran untuk SEMUA state karakter, dan
        lapisan hidup (heroes/gornak_fx) serta alat uji membacanya dari
        sini, jadi badan dan efek tidak mungkin berbeda fase:

        * ``_gnk_dt``              delta-time nyata (detik, dijepit)
        * ``_gnk_attack_active``   serangan sedang berjalan   (nama lama)
        * ``_gnk_attack_frame``    frame ke-n dalam serangan   (nama lama)
        * ``_gnk_attack_progress`` 0..1 sepanjang serangan     (nama lama)
        * ``_gnk_attack_raw``      progress sebelum kurva      (nama lama)
        * ``_gnk_attack_phase``    ANTICIPATION/.../RECOVERY
        * ``_gnk_hit_active``      True hanya di jendela hit aktif
        * ``_gnk_frame_duration``  lama 1 langkah simulasi (untuk HUD)
        * ``_gnk_state`` / ``_gnk_state_prev`` / ``_gnk_state_time``
        * ``_gnk_hurt_frames``     sisa frame respons kena damage

        Semua nama lama dipertahankan supaya renderer, skill, dan
        tools/_audit_gornak_v2.py tidak perlu diubah.
        """
        G = _NS_gornak

        # ── delta time nyata (dipakai FX & transisi state) ───────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                          # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_gnk_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._gnk_last_ms = now
        boss._gnk_dt = dt

        # ── timeline serangan ───────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 38)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gnk_previous_timer", 0))
        active = bool(getattr(boss, "_gnk_attack_active", False))

        # Serangan dikenali dari DUA hal: lompatan timer ke atas (cooldown
        # dipasang saat attack mendarat) dan detak jam (satu siklus penuh
        # timer turun ke 0). Yang kedua menjaga animasi tetap jalan untuk
        # pemanggil yang mengisi timer manual (alat preview / tes).
        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._gnk_attack_active = True
            boss._gnk_attack_frame = 0
            boss._gnk_attack_manual = False
            active = True
        elif active and timer > 0:
            boss._gnk_attack_frame = int(getattr(boss, "_gnk_attack_frame",
                                                 0)) + 1
            boss._gnk_attack_manual = False
        elif timer <= 0:
            if active and not getattr(boss, "_gnk_attack_manual", False) \
                    and int(getattr(boss, "_gnk_attack_progress", 0.0)) > 0.0:
                # Ada yang mengaktifkan serangan TANPA menyentuh timer
                # (alat audit, preview kartu, test). Itu bukan serangan
                # engine: hormati, tandai manual, dan jangan dimatikan di
                # sini - yang mematikan ya pemanggilnya sendiri.
                boss._gnk_attack_manual = True
                active = True
            elif not getattr(boss, "_gnk_attack_manual", False):
                boss._gnk_attack_active = False
                boss._gnk_attack_frame = 0
                active = False
            if not active:
                boss._gnk_attack_active = False
                boss._gnk_attack_frame = 0

        boss._gnk_previous_timer = timer
        frame = int(getattr(boss, "_gnk_attack_frame", 0)) if active else 0
        span = max(1, cooldown - 1)
        boss._gnk_attack_frame = frame
        boss._gnk_frame_duration = dt
        if bool(getattr(boss, "_gnk_attack_manual", False)) and active:
            # Alat preview / tes menggerakkan ``_gnk_attack_progress``
            # sendiri (tanpa timeline timer). Jangan dilawan: biarkan angka
            # pemanggil yang dipakai, dan tetap turunkan fase + jendela hit
            # darinya supaya pose, FX, dan debug membaca sumber yang sama.
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_gnk_attack_progress", 0.0))))
            boss._gnk_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._gnk_attack_progress = progress

        # ── fase + jendela hit ──────────────────────────────────────
        if not getattr(boss, "_gnk_attack_active", False):
            # pemanggil sudah mematikan serangannya -> lupa status manual
            boss._gnk_attack_active = False
            boss._gnk_attack_manual = False
            active = False
        phase = G.attack_phase(progress) if active else "NONE"
        boss._gnk_attack_phase = phase
        lo, hi = G.ATTACK_ACTIVE_WINDOW
        boss._gnk_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ──────────────────────────────
        hurt = int(getattr(boss, "_gnk_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10                       # flash baru -> minimal 10 frame
        boss._gnk_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── state machine ber-prioritas ─────────────────────────────
        want = G._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_gnk_state", None)
        if cur is None:
            boss._gnk_state = want
            boss._gnk_state_prev = want
            boss._gnk_state_time = 0.0
        elif want != cur:
            cur_p = G.ANIM_STATES.get(cur, 0)
            new_p = G.ANIM_STATES.get(want, 0)
            stime = float(getattr(boss, "_gnk_state_time", 0.0))
            # DEATH mengunci; state lain boleh direbut prioritas yang
            # sama/lebih tinggi, atau yang lebih rendah kalau state lama
            # sudah selesai (mencegah pose tersangkut).
            if cur != "DEATH" and (new_p >= cur_p or stime > 0.08):
                boss._gnk_state_prev = cur
                boss._gnk_state = want
                boss._gnk_state_time = 0.0
            else:
                boss._gnk_state_time = stime + dt
        else:
            boss._gnk_state_time = float(getattr(boss, "_gnk_state_time",
                                                 0.0)) + dt

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_gnk_last_x"):
            boss._gnk_last_x = cur_x
            boss._gnk_last_y = cur_y
            boss._moving_cached = False
            return False
        moved = abs(cur_x - boss._gnk_last_x) + abs(cur_y - boss._gnk_last_y)
        boss._gnk_last_x = cur_x
        boss._gnk_last_y = cur_y
        moving = moved > 0.3
        # Nama sama dengan hero lain (kaizen/zephyr/dll) supaya state
        # machine dan cache sprite cukup satu konvensi.
        boss._moving_cached = moving
        return moving

    # ==================================================================
    # POSE STATE - satu sumber kebenaran untuk rig DAN semua FX
    # ==================================================================
    ACTIONS = ("idle", "walk", "attack", "surge", "ward", "void")

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN anchor FX agar sinkron.

        Murni/tanpa efek samping: boleh dipanggil ulang oleh fungsi efek.
        """
        active_skill = getattr(boss, "active_skill", None)
        if active_skill == "e":
            action = "ward"
        elif active_skill == "r":
            action = "void"
        elif active_skill == "q":
            action = "surge"
        elif active_skill == "w":
            action = "blink"
        elif (getattr(boss, "_gnk_attack_active", False)
              or getattr(boss, "timer", 0) >
              getattr(boss, "attack_cooldown", 40) - 15):
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 2.0
        ap = 0.0
        if action == "attack":
            raw = max(0.0, min(1.0, float(getattr(boss, "_gnk_attack_progress",
                                                  0.0))))
            ap = _NS_gornak._attack_curve(raw)
            boss._gnk_attack_raw = raw
        return action, phase, ap

    # ── Tinggi badan dalam RUANG LOKAL (y=0 = garis pinggang, + ke bawah)
    # Krist mohawk -37 .. telapak +44. Setelah SCALE 1.32 + LIFT: ~107 px,
    # cukup untuk mini boss tapi wajah tetap di bawah HP bar boss.
    HEAD_Y = -24
    SHOULDER_Y = -14
    SHOULDER_FRONT = (12, SHOULDER_Y)
    SHOULDER_BACK = (-11, SHOULDER_Y - 1)

    # ── Kunci fase ayunan (dipakai grip, sudut, DAN pita slash) ────────
    _SWING_WIND = 0.24          # puncak wind-up (bilah di atas kepala)
    _SWING_HIT = 0.80           # frame impact (bilah menyapu bawah-depan)

    def _attack_curve(ap):
        """Remap progres mentah (0..1) -> waktu pose (0..1), MONOTON naik.

        Yang membuat animasi serangan 2D terasa murah bukan jumlah frame,
        tapi tidak adanya: (a) anticipation yang jelas, (b) HOLD satu-dua
        frame di impact, (c) follow-through yang tidak langsung ditarik
        balik. Kurva v3 memberi ketiganya dengan kontras laju ~10x antara
        tebasan dan hold.

        Batas segmen jatuh PERSIS di _SWING_WIND / _SWING_HIT supaya tabel
        grip & sudut tidak pernah "patah" di tengah transisi.
        """
        if ap <= 0.0:
            return 0.0
        if ap >= 1.0:
            return 1.0
        w = _NS_gornak._SWING_WIND
        h = _NS_gornak._SWING_HIT
        if ap < 0.30:                       # anticipation: angkat lalu tahan
            t = ap / 0.30
            return w * (t ** 0.85)
        if ap < 0.46:                       # tebasan: dipercepat
            # Eksponen > 1 = MULUS dari puncak tahan lalu MENGGILAS di
            # tengah. Dengan < 1 (v3 lama) frame pertama tebasan justru
            # melompat ~32 px dari pose yang sedang ditahan, dan itu
            # terbaca sebagai glitch, bukan bobot. Sekarang lajunya naik
            # terus sampai tepat sebelum IMPACT HOLD, jadi ayunannya
            # "memukul masuk" ke freeze.
            t = (ap - 0.30) / 0.16
            return w + (h - w - 0.02) * (t ** 1.25)
        if ap < 0.60:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.46) / 0.14
            return h - 0.02 + 0.02 * t
        t = (ap - 0.60) / 0.40              # follow-through -> siap
        return h + (1.0 - h) * (t ** 0.80)

    def _portrait_blade_angle(back=False):
        """Sudut bilah mode portrait: rapat ke badan, ujung menukik turun.

        HeroPortraits meng-crop bbox lalu men-scale-nya ke kartu, jadi
        figur yang LEBAR (bilah terentang) justru terKECIL di kartu yang
        sama. Dengan bilah ditarik masuk, bbox menyempit dan figur
        ter-render lebih besar - wajah & zirah akhirnya terbaca.
        """
        return -0.78 if back else 0.95

    def _blade_angle(phase, action, ap=0.0, back=False):
        """Sudut bilah (rad). tip = grip + (sin a * L, cos a * L).

        a = 0 menunjuk LURUS KE BAWAH, a = pi/2 lurus ke depan, a = pi
        lurus ke atas. Bilah belakang memakai tanda berlawanan sehingga
        dua senjata selalu membentuk gunting, bukan sejajar.
        """
        s = math.sin(phase * 1.72)
        if action == "attack":
            w = _NS_gornak._SWING_WIND
            h = _NS_gornak._SWING_HIT
            if ap < w:                       # angkat ke atas-belakang
                u = ap / w
                return (2.05 + 0.85 * u, -0.80 - 2.05 * u)[back]
            if ap < h:                       # tebasan turun ke depan
                u = (ap - w) / (h - w)
                return (2.90 - 2.28 * u, -2.85 + 1.90 * u)[back]
            u = (ap - h) / (1.0 - h)         # recovery -> siap
            return (0.62 + 1.43 * u, -0.95 + 0.15 * u)[back]
        if action == "surge":                # Q: tusukan mana mendatar
            return (1.45, -1.42)[back]
        if action == "ward":                 # E: dua bilah tegak = garda
            return (3.02, -3.02)[back]
        if action == "void":                 # R: kedua bilah dibuka ke atas
            return (2.40, -2.40)[back]
        if action == "blink":
            return (0.62, -0.62)[back]
        if action == "walk":
            return (2.05 + s * 0.14, -0.80 - s * 0.14)[back]
        # Siap: bilah DEPAN diagonal ke depan-atas, bilah belakang menukik
        # ke belakang-bawah. Asimetris supaya kepala & dada tetap subjek,
        # tapi lebar siluet (W/H ~1.1) tetap terjaga. Nilai ini juga titik
        # awal/akhir ayunan -> tidak pernah ada frame "snap".
        w = math.sin(phase * 0.5) * 0.05
        return (2.05 + w, -0.80 - w)[back]

    def _front_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan depan (bilah utama), ruang lokal."""
        rest = _NS_gornak.SHOULDER_Y + 16                    # = 2
        if compact:
            return (12, rest + 2)
        if action == "attack":
            w = _NS_gornak._SWING_WIND
            h = _NS_gornak._SWING_HIT
            if ap < w:
                e = (ap / w) ** 0.9
                return (int(15 - 13 * e), int(rest - 26 * e))
            if ap < h:
                u = (ap - w) / (h - w)
                return (int(2 + 20 * u), int(rest - 26 + 32 * u))
            u = (ap - h) / (1.0 - h)
            return (int(22 - 7 * u), int(rest + 6 - 4 * u))
        if action == "surge":
            return (21, rest + 3)
        if action == "ward":
            return (14, rest - 9)
        if action == "void":
            return (19, rest - 15)
        if action == "blink":
            return (16, rest - 2)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(15 + s * 3), int(rest - s * 2))
        return (15, rest + int(math.sin(phase * 0.62)))

    def _back_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan belakang (bilah pendek, grip terbalik)."""
        rest = _NS_gornak.SHOULDER_Y + 17                    # = 3
        if compact:
            return (-13, rest + 3)
        if action == "attack":
            w = _NS_gornak._SWING_WIND
            h = _NS_gornak._SWING_HIT
            if ap < w:
                e = (ap / w) ** 0.9
                return (int(-19 - 6 * e), int(rest - 25 * e))
            if ap < h:
                u = (ap - w) / (h - w)
                return (int(-25 + 13 * u), int(rest - 25 + 27 * u))
            u = (ap - h) / (1.0 - h)
            return (int(-12 - 7 * u), int(rest + 2 - 1 * u))
        if action == "surge":
            return (-21, rest - 3)
        if action == "ward":
            return (-20, rest - 11)
        if action == "void":
            return (-21, rest - 14)
        if action == "blink":
            return (-20, rest - 1)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(-19 + s * 3), int(rest + s * 2))
        return (-19, rest + int(math.sin(phase * 0.62 + 1.1)))

    def _elbow(a, b, bend):
        """Siku 2-tulang: titik tengah + offset tegak lurus.

        Membuat lengan selalu tersambung (tidak pernah "lepas" seperti
        sticker) dan lengkungannya bisa diarahkan per sisi.
        """
        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        return (int(mx + (-dy / ln) * bend), int(my + (dx / ln) * bend))

    def _arm_chain(shoulder, grip, phase, action, ap=0.0, back=False):
        """(elbow, blade_angle) - siku dari lengan, sudut dari tabel pose."""
        elbow = _NS_gornak._elbow(shoulder, grip, 5.0 if back else -4.5)
        return elbow, _NS_gornak._blade_angle(phase, action, ap, back)

    def _blade_len(action, back=False):
        """Panjang bilah - sumber LEBAR utama siluet dual-wield."""
        if back:
            return 28 if action == "attack" else 25
        if action == "attack":
            return 40
        if action == "surge":
            return 42
        if action in ("ward", "void"):
            return 38
        return 36

    def _head_bob(action, phase, ap):
        """Offset kepala (dx, dy) ruang lokal.

        Yang membuat rig terasa hidup bukan jumlah sendi, tapi kepala yang
        TIDAK merekat mati ke torso: mengangguk saat langkah, menunduk
        saat ayunan, dan bergoyang halus saat idle.
        """
        if action == "walk":
            return (-int(round(math.sin(phase * 1.72) * 1.4)),
                    -1 - int(round(abs(math.sin(phase * 1.15)) * 1.2)))
        if action == "attack":
            k = math.sin(ap * math.pi)
            return (int(round(k * 2.6)), -int(round(k * 1.6)))
        if action == "void":
            return (-1, -3)
        if action == "ward":
            return (0, -1)
        if action == "surge":
            return (2, 0)
        return (int(round(math.sin(phase * 0.31) * 0.9)),
                int(round(math.sin(phase * 0.62 + 0.8) * 0.8)))

    def _rig_shift(action, phase, ap):
        """(lean, root_y) badan; kaki TIDAK ikut bergeser (menapak)."""
        lean = 0
        root_y = int(math.sin(phase * 0.62) * 1.2)
        if action == "walk":
            lean = int(math.sin(phase * 1.72) * 2)
            root_y -= int(abs(math.sin(phase * 1.15)) * 2.5)
        elif action == "attack":
            # Berat badan pindah ke depan saat tebasan lalu ditarik balik.
            k = math.sin(ap * math.pi)
            lean = int(k * 6)
            root_y += int(k * 2)
        elif action == "surge":
            lean = 3
            root_y -= 1
        elif action in ("void", "ward"):
            root_y -= 2
        elif action == "blink":
            lean = 1
            root_y -= 1
        return lean, root_y

    def _s(v):
        """Ukuran ruang lokal (lebar garis, radius) -> piksel layar."""
        return max(1, int(round(v * _NS_gornak.SCALE)))

    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar: skala, arah hadap, bob/lean.

        Semua bagian tubuh dan semua titik jangkar efek (ujung bilah,
        pergelangan tangan) melewati fungsi ini, jadi ukuran boleh diubah
        lewat satu angka tanpa membuat efek lepas dari badan.
        """
        f = 1 if facing >= 0 else -1
        k = _NS_gornak.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy - _NS_gornak.LIFT + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = _NS_gornak._rig_shift(action, phase, ap)
        return _NS_gornak._local_to_screen(x, y, facing, lean, root_y, lx, ly)

    def _tip_local(action, phase, ap=0.0, back=False):
        """Ujung bilah dalam ruang lokal (rig & FX pakai angka yang sama)."""
        grip = (_NS_gornak._back_grip_local(action, ap, phase) if back
                else _NS_gornak._front_grip_local(action, ap, phase))
        shoulder = (_NS_gornak.SHOULDER_BACK if back
                    else _NS_gornak.SHOULDER_FRONT)
        _, angle = _NS_gornak._arm_chain(shoulder, grip, phase, action, ap,
                                         back)
        L = _NS_gornak._blade_len(action, back)
        return (int(grip[0] + math.sin(angle) * L),
                int(grip[1] + math.cos(angle) * L))

    def _tip_screen(boss, x, y, back=False):
        action, phase, ap = _NS_gornak._resolve_pose(boss)
        # FX selalu memakai pose yang sama dengan badan (lihat
        # _resolve_pose yang murni), jadi bolt/proc tidak pernah lepas.
        return _NS_gornak._local(boss, x, y, action, phase, ap,
                                 *_NS_gornak._tip_local(action, phase, ap,
                                                        back))

    # ==================================================================
    # LAPISAN FX HIDUP (heroes/gornak_fx)
    # ==================================================================
    #: Modul FX layar (diisi malas). False = percobaan gagal -> jalur canvas.
    _LIVE_MOD = None

    def _live_module():
        """Muat ``heroes.gornak_fx`` sekali; None kalau tidak tersedia.

        Impor dilakukan DI SINI (bukan di kepala modul) supaya modul boss
        besar tidak menarik paket hero saat build hanya-butuh-renderer, dan
        supaya karakter FX bisa di-matikan lewat satu flag tanpa merusak
        jalur render.
        """
        NS = _NS_gornak
        if NS._LIVE_MOD is None:
            try:
                from heroes import gornak_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "GORNAK_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup Gornak bisa dipakai (dipakai tooling)."""
        return _NS_gornak._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini.

        Return ``(mod, owned)``:
          * ``mod``   - modulnya (None = jangan gambar lapisan hidup),
          * ``owned`` - True kalau efek ayunan/bolt sudah diambil alih
            lapisan hidup, jadi renderer boleh melewati salinan di-canvas.

        ``want_draw`` True pada jalur BOSS (draw dipanggil tiap frame,
        tidak lewat cache sprite). Pada jalur HERO penggambaran dilakukan
        heroes/__init__.py (``_LIVE_FX_HEROES``) supaya lapisan tetap hidup
        walau sprite sedang di-cache - di sini hanya dipasang penanda
        "diambil alih" agar tidak ada efek yang digambar dua kali.
        """
        NS = _NS_gornak
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ==================================================================
    # ENTRY POINT
    # ==================================================================
    def draw_gornak(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan mengikuti kontrak render order proyek:

            GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD ->
            WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
            SKILL FX -> IMPACT FX -> DEBUG

        Trail ayunan, partikel, proyektil Mana Break, impact, screen shake
        dan hit-stop hidup di ``heroes/gornak_fx.py`` (lapisan layar 1:1,
        di luar sprite cache). Semua nama publik lama tetap ada; kalau
        modul FX tidak dimuat, renderer kembali menggambar semuanya
        di-canvas (jalur fallback).
        """
        NS = _NS_gornak
        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer, dan _finish_hd_sprite sudah menambah
        # rim/terminator -> pass di sini dilewati (lihat _draw_gnk_rig_at).
        hero_lane = hasattr(boss, "_render_scale")
        NS._HERO_LANE.v = hero_lane
        NS._update_gnk_attack_anim(boss)
        action, phase, ap = NS._resolve_pose(boss, NS._detect_moving(boss))
        boss._gnk_pose_action = action
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = NS._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                 / 8.0))
        # Jalur boss digambar tiap frame TANPA cache -> lapisan hidup
        # dipicu dari sini. Jalur lane sudah dipicu heroes/__init__.
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero Shop
        #    terisi wajah & material, bukan lingkaran efek.
        if not portrait:
            NS._draw_anti_magic_field(surface, x, y, phase, skill)
            if skill != "r":
                # Saat ULT, segel void menutupi rune tanah -> tidak perlu
                # digambar (hemat di frame paling berat).
                NS._draw_ground_rune(surface, x, y, phase, skill)
            if skill == "q":
                NS._draw_manabreak_ground(surface, boss, x, y, timer, phase)
            elif skill == "w":
                NS._draw_blink_ground(surface, boss, x, y, timer, phase)
            elif skill == "r":
                NS._draw_manavoid_ground(surface, boss, x, y, timer, phase)
            if not owned:
                NS._draw_cast_shockwave(surface, boss, x, y, skill, timer)

        # ── Karakter
        if action == "blink":
            NS._draw_gnk_blink(surface, boss, x, y, timer, portrait, flash)
        else:
            if not portrait:
                NS._draw_shadow(surface, x, y + NS.GROUND_DY)
            NS._draw_gnk_rig_at(surface, x, y, facing, phase, action, ap,
                                portrait, flash)
            if action == "attack" and not portrait and not owned:
                # Pita ayunan di-canvas HANYA kalau lapisan hidup tidak
                # mengambil alih. Canvas lane di-smoothscale, jadi pita
                # di sana terbaca lembek; trail layar memakai histori
                # posisi bilah yang sebenarnya pada resolusi 1:1.
                NS._draw_crescent_slash(surface, x, y, facing, phase, ap)
            elif action == "walk" and not portrait:
                # Debu langkah: dua kepul kecil tepat saat telapak mendarat,
                # jadi bobot badan terasa menekan tanah (bukan karakter
                # meluncur di atas lantai).
                NS._draw_footfall_dust(surface, x, y, facing, phase)

        # ── Foreground FX
        if not portrait:
            if skill == "q":
                if not owned:
                    NS._draw_manabreak_foreground(surface, boss, x, y, timer,
                                                  phase)
            elif skill == "e":
                NS._draw_counterspell_foreground(surface, boss, x, y, timer,
                                                 phase)
            elif skill == "r":
                NS._draw_manavoid_foreground(surface, boss, x, y, timer,
                                             phase)

        # ── Lapisan hidup bagian ATAS + debug
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_gnk_debug(surface, boss, x, y, action, owned)

    # ==================================================================
    # DEBUG OVERLAY  (DEBUG_CHARACTER = True)
    # ==================================================================
    def _draw_gnk_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state/frame, FPS, jumlah partikel.

        Tidak menyentuh gameplay: semua angka dibaca dari state yang sudah
        ada, dan overlay digambar PALING AKHIR supaya tidak pernah tertutup.
        """
        NS = _NS_gornak
        import pygame as _pg

        # ── hurtbox = lingkaran radius unit ─────────────────────────
        r = max(6, int(getattr(boss, "radius", 16) * 0.9 * NS.SCALE))
        _pg.draw.rect(surface, (80, 170, 255, 150),
                      _pg.Rect(int(x) - r, int(y) - r - 8, r * 2, r * 2), 1)

        # ── jangkauan serangan ──────────────────────────────────────
        rng = max(10, int(getattr(boss, "range", 60) * NS.SCALE * 0.9))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        _pg.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                      (int(x) + int(rng * f), int(y)), 1)
        _pg.draw.rect(surface, (255, 210, 60, 110),
                      _pg.Rect(int(x + rng * f) - 5, int(y) - 7, 10, 14), 1)

        # ── hitbox ayunan (hanya saat jendela hit aktif) ─────────────
        hb = NS._swing_hitbox(boss, x, y)
        if hb is not None:
            _pg.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            _pg.draw.rect(surface, (255, 70, 70, 60), hb)

        # ── tabrakan proyektil milik lapisan hidup ──────────────────
        if owned:
            try:
                mod = NS._LIVE_MOD
                for p in mod.projectiles_for(boss):
                    rr = max(3, int(p.hit_radius))
                    _pg.draw.circle(surface, (255, 120, 255, 170),
                                    (int(p.sx), int(p.sy)), rr, 1)
            except Exception:
                pass

        # ── panel teks ──────────────────────────────────────────────
        fps = getattr(boss, "_gnk_fps", None)
        if fps is None:
            boss._gnk_fps = 60.0
            fps = 60.0
        else:
            dt = float(getattr(boss, "_gnk_dt", 1.0 / 60.0))
            inst = 1.0 / dt if dt > 0 else 60.0
            boss._gnk_fps = fps + (inst - fps) * 0.1
            fps = boss._gnk_fps
        state = getattr(boss, "_gnk_state", "IDLE")
        phase = getattr(boss, "_gnk_attack_phase", "NONE")
        frames = int(getattr(boss, "_gnk_attack_frame", 0))
        prog = float(getattr(boss, "_gnk_attack_progress", 0.0))
        hurt = int(getattr(boss, "_gnk_hurt_frames", 0))
        atk_cd = int(getattr(boss, "attack_cooldown", 38))
        timer = int(getattr(boss, "timer", 0))
        skill = getattr(boss, "active_skill", None) or "-"
        s_timer = int(getattr(boss, "active_skill_timer", 0))
        npart = 0
        try:
            npart = int(NS._LIVE_MOD.total_particles()) if NS._LIVE_MOD \
                else 0
        except Exception:
            npart = 0
        lines = (
            "GORNAK  %.0f fps" % fps,
            "state %s (prev %s) %.2fs" % (state,
                                          getattr(boss, "_gnk_state_prev",
                                                  "-"),
                                          float(getattr(boss, "_gnk_state_time",
                                                        0.0))),
            "action %s  phase %s" % (action, phase),
            "atk frame %d/%d  prog %.2f  hit %s" % (
                frames, max(1, atk_cd - 1), prog,
                "ON" if getattr(boss, "_gnk_hit_active", False) else "off"),
            "timer %d  hurt %d" % (timer, hurt),
            "skill %s  %d  live %s" % (skill, s_timer,
                                       "on" if owned else "canvas"),
            "particles %d  dt %.1fms" % (npart,
                                         float(getattr(boss, "_gnk_dt",
                                                       1.0 / 60.0)) * 1000.0),
        )
        fnt = _pg.font.SysFont("consolas,monospace", 10)
        w0 = int(x) - 96
        y0 = int(y) - int(140 * NS.SCALE) - 10 * len(lines)
        box = _pg.Rect(w0 - 3, y0 - 2, 200, 12 * len(lines) + 4)
        bg = _pg.Surface(box.size, _pg.SRCALPHA)
        bg.fill((6, 4, 12, 150))
        surface.blit(bg, box.topleft)
        for i, t in enumerate(lines):
            txt = fnt.render(t, True, (255, 226, 150))
            surface.blit(txt, (box.x + 3, box.y + 1 + i * 12))

    def _draw_cast_shockwave(surface, boss, x, y, skill, timer):
        """Gelombang kejut 12 frame pertama SETIAP skill (world-space).

        Satu "tanda baca" yang sama untuk Q/W/E/R: pemain langsung tahu
        sebuah skill baru saja keluar, tanpa harus membaca efeknya dulu.
        """
        if skill not in _NS_gornak.SKILL_DUR:
            return
        age = _NS_gornak.SKILL_DUR[skill] - timer
        if not (0 <= age < 12):
            return
        p = _NS_gornak.PALETTE
        st = age / 12.0
        fs = _NS_gornak._fx_scale(boss)
        a = _NS_gornak._alpha(235 * (1 - st) ** 1.4)
        rr = int((16 + st * 52) * fs)
        gy = y + _NS_gornak.GROUND_DY
        _NS_gornak._ellipse(surface, (*p["magic_mid"], a),
                            (x - rr, gy - rr // 3, rr * 2,
                             max(4, rr * 2 // 3)), 2)
        _NS_gornak._ellipse(surface, (*p["magic_shine"], a),
                            (x - rr // 2, gy - rr // 6, rr,
                             max(3, rr // 3)), 1)
        for i in range(6):
            ang = i * math.tau / 6 + st * 1.2
            _NS_gornak._shard(
                surface, x + math.cos(ang) * rr * 0.9,
                gy + math.sin(ang) * rr * 0.3, ang,
                int(6 * fs * (1 - st)) + 2, max(1, int(2 * fs)),
                p["magic_light"], a, core=p["magic_shine"])
        _NS_gornak._spark_star(
            surface, x, gy - 4, int(10 * fs * (1 - st)), p["magic_hot"], a,
            spikes=8, rot=st * 1.4, core=p["magic_shine"])

    def _draw_gnk_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit murah.

        Mode portrait Hero Shop memakai kanvas kecil (160x160) dan
        meng-crop dari bbox: kalau badan digambar dengan anchor di
        pinggang, bilah depan yang panjang melewati tepi kanan dan
        TERPOTONG. Jadi di mode itu konten dipusatkan pada bbox-nya
        sendiri; jalur boss (1x) tidak berubah sama sekali.
        """
        buf = pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                             pygame.SRCALPHA)
        _NS_gornak._draw_gnk_rig(buf, _NS_gornak.RIG_OX, _NS_gornak.RIG_OY,
                                 facing, phase, action, ap, detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 246, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Aturan pass cahaya: dipasang di SINI hanya kalau sprite ini TIDAK
        # akan dilewatkan ke heroes._finish_hd_sprite (yang memasang pass
        # yang sama):
        #   * boss 1x (tanpa _render_scale)             -> pasang di sini
        #   * lane hero (punya _render_scale)           -> jangan (dobel)
        #   * Hero Shop (portrait, tanpa _render_scale) -> pasang di sini
        if _lighting is not None and not _NS_gornak._HERO_LANE.v:
            _lighting.apply_to_rig(
                buf, rim_add=(32, 26, 46), shade_mul=160,
                box=_NS_gornak.GRAD_BOX if not detail else None)
        ox = int(x) - _NS_gornak.RIG_OX
        oy = int(y) - _NS_gornak.RIG_OY
        if detail:                      # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet 4 arah: bagian tetap terpisah saat unit bertumpuk.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))
        return buf

    # Pose tunggal (dipakai tool debug/preview).
    def _draw_gnk_idle(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "idle", 0.0, False)

    def _draw_gnk_walk(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)) * 2.0,
                                    "walk", 0.0, False)

    def _draw_gnk_attack(surface, boss, x, y, ap=0.5):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "attack", ap, False)

    def _draw_gnk_blink(surface, boss, x, y, timer, portrait, flash):
        """Blink: after-image RIG YANG SAMA + disolusi serpihan di kaki."""
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1) or 1
        phase = float(getattr(boss, "pulse", 0.0))
        if progress < 0.30:
            alpha_t = 1.0 - progress / 0.30
        elif progress < 0.68:
            alpha_t = 0.14
        else:
            alpha_t = (progress - 0.68) / 0.32

        if not portrait:
            _NS_gornak._draw_shadow(surface, x, y + _NS_gornak.GROUND_DY)

        rig, ax, ay = _NS_gornak._compose_outline(x, y, facing, phase, "blink",
                                                  0.0, portrait)
        if progress < 0.80:
            for i in (3, 2, 1):
                rig.set_alpha(_NS_gornak._alpha(80 * alpha_t / i))
                surface.blit(rig, (x - ax - facing * i * 8, y - ay + i))
        rig.set_alpha(_NS_gornak._alpha(70 + 185 * min(1.0, alpha_t)))
        surface.blit(rig, (x - ax, y - ay))
        rig.set_alpha(255)

        if not portrait:
            gy = y + _NS_gornak.GROUND_DY
            for i in range(9):
                t = (phase * 0.5 + i * 0.111) % 1.0
                gx = x + int(math.sin(i * 1.7) * (10 + t * 18))
                a = _NS_gornak._alpha(200 * (1 - t) * alpha_t)
                if a <= 0:
                    continue
                _NS_gornak._shard(surface, gx, gy - int(t * 16),
                                  -math.pi / 2 + math.sin(i * 2.1) * 0.5,
                                  4 + int((1 - t) * 4), 2, p["magic_light"],
                                  a, core=p["magic_shine"])

    def _compose_outline(x, y, facing, phase, action, ap, detail):
        """Rig + outline gelap 1 px sebagai SATU surface (perlu untuk
        after-image blink yang mengatur alpha sendiri).

        Return ``(surface, anchor_x, anchor_y)``: titik dalam surface yang
        jatuh tepat di dunia ``(x, y)``.
        """
        buf = pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                             pygame.SRCALPHA)
        _NS_gornak._draw_gnk_rig(buf, _NS_gornak.RIG_OX, _NS_gornak.RIG_OY,
                                 facing, phase, action, ap, detail)
        pad = 1
        out = pygame.Surface((_NS_gornak.RIG_W + pad * 2,
                              _NS_gornak.RIG_H + pad * 2), pygame.SRCALPHA)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        # Selout: outline gelap hanya sisi bayangan (kanan-bawah relatif
        # hadap). Key light kiri-atas (lighting.LIGHT_DIR = (-1, -1));
        # sisi cahaya dibiarkan bersih - rim 1 px ada di _draw_gnk_rimlight.
        sx = 1 if facing >= 0 else -1
        for dx, dy in ((sx, 0), (0, 1), (sx, 1)):
            out.blit(edge, (pad + dx, pad + dy))
        out.blit(buf, (pad, pad))
        return out, _NS_gornak.RIG_OX + pad, _NS_gornak.RIG_OY + pad

    # ==================================================================
    # BONE RIG 2D BERLAPIS
    # ==================================================================
    def _draw_gnk_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """Seluruh badan dihitung dari sendi, urutan belakang -> depan.

        ``cx, cy`` = anchor (pusat boss / garis pinggul).
        """
        p = _NS_gornak.PALETTE
        f = 1 if facing >= 0 else -1
        lean, root_y = _NS_gornak._rig_shift(action, phase, ap)

        def pt(dx, dy):
            """Sendi badan (ikut bob/lean)."""
            return _NS_gornak._local_to_screen(cx, cy, f, lean, root_y, dx, dy)

        def ptg(dx, dy):
            """Sendi terpatok tanah (telapak kaki tidak ikut bob)."""
            return _NS_gornak._local_to_screen(cx, cy, f, lean, 0, dx, dy)

        def poly(color, coords, outline=True):
            pts = [pt(dx, dy) for dx, dy in coords]
            if outline:
                _NS_gornak._poly(surface, p["shadow_deep"],
                                 [(qx + f, qy + 1) for qx, qy in pts])
            _NS_gornak._poly(surface, color, pts)
            return pts

        def poly_free(color, pts, outline=True):
            if outline:
                _NS_gornak._poly(surface, p["shadow_deep"],
                                 [(qx + f, qy + 1) for qx, qy in pts])
            _NS_gornak._poly(surface, color, pts)

        def dot(color, dx, dy, r, outline=True):
            sx, sy = pt(dx, dy)
            rr = _NS_gornak._s(r)
            if outline:
                _NS_gornak._aacircle(surface, p["shadow_deep"],
                                     (sx + f, sy + 1), rr + 1)
            _NS_gornak._aacircle(surface, color, (sx, sy), rr)

        def limb(a, b, width, base, light=None):
            aa, bb = pt(*a), pt(*b)
            w = _NS_gornak._s(width)
            _NS_gornak._aaline(surface, p["shadow_deep"],
                               (aa[0] + f, aa[1] + 1),
                               (bb[0] + f, bb[1] + 1), w + 2)
            _NS_gornak._aaline(surface, base, aa, bb, w)
            if light:
                off = -1 if f > 0 else 1
                _NS_gornak._aaline(surface, light, (aa[0] + off, aa[1] - 1),
                                   (bb[0] + off, bb[1] - 1),
                                   max(1, _NS_gornak._s(width // 3)))

        breath = math.sin(phase * 0.62)
        stride = (math.sin(phase * 1.72) if action == "walk" else 0.0)
        ward = action == "ward"
        void = action == "void"
        surge = action == "surge"

        portrait = bool(detail)
        front_grip = _NS_gornak._front_grip_local(action, ap, phase,
                                                  compact=portrait)
        back_grip = _NS_gornak._back_grip_local(action, ap, phase,
                                                compact=portrait)
        front_elbow, front_angle = _NS_gornak._arm_chain(
            _NS_gornak.SHOULDER_FRONT, front_grip, phase, action, ap)
        back_elbow, back_angle = _NS_gornak._arm_chain(
            _NS_gornak.SHOULDER_BACK, back_grip, phase, action, ap, back=True)
        if portrait:
            front_angle = _NS_gornak._portrait_blade_angle(False)
            back_angle = _NS_gornak._portrait_blade_angle(True)

        # 1. Jubah belakang - memberi kedalaman pada siluet
        _NS_gornak._draw_gnk_cape_back(surface, pt, poly_free, f, phase,
                                       action, ap)

        # 2. Kaki - telapak dipatok di GROUND_DY
        _NS_gornak._draw_gnk_legs(surface, pt, ptg, poly_free, f, phase,
                                  action, stride)

        # 3. Tangan + bilah belakang (di balik badan)
        _NS_gornak._draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                 action, ap, _NS_gornak.SHOULDER_BACK,
                                 back_elbow, back_grip, back_angle,
                                 _NS_gornak._blade_len(action, True),
                                 back=True)

        # 4. Torso + harness + pelat spellbreaker
        _NS_gornak._draw_gnk_torso(surface, pt, poly_free, dot, f, phase,
                                   breath, ward, void)

        # 5. Sabuk, loincloth, rantai besi
        _NS_gornak._draw_gnk_belt(surface, pt, poly_free, dot, f, phase,
                                  action, stride)

        # 6. Pauldron bertingkat
        _NS_gornak._draw_gnk_pauldrons(surface, pt, poly_free, dot, f, phase,
                                       breath)

        # 7. Leher + kepala (rahang, jenggot kepang, mohawk)
        _NS_gornak._draw_gnk_head(surface, pt, poly_free, dot, f, phase,
                                  action, ap, ward, void)

        # 8. Tangan + bilah depan (paling depan)
        _NS_gornak._draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase,
                                 action, ap, _NS_gornak.SHOULDER_FRONT,
                                 front_elbow, front_grip, front_angle,
                                 _NS_gornak._blade_len(action), back=False,
                                 ward=ward, void=void, surge=surge)

        # 9. Rim light ungu - sinyal warna tema
        _NS_gornak._draw_gnk_rimlight(surface, pt, f, phase, ward, void)

        # 10. Pass material portrait-only
        if detail:
            _NS_gornak._draw_gnk_masterwork_details(surface, pt, f, phase,
                                                    action)
            _NS_gornak._draw_gnk_weave(surface, pt, f)

    # ==================================================================
    # BAGIAN TUBUH
    # ==================================================================
    # Prinsip di 720p: yang dibaca hanya NILAI (terang/gelap) dan SILUET,
    # bukan garis halus. Tiap bagian dibatasi 3 nilai + 1 aksen, dan garis
    # penanda (otot, jahitan) hanya muncul di pass portrait.
    # ==================================================================

    def _draw_gnk_cape_back(surface, pt, poly_free, f, phase, action, ap=0.0):
        """Half-mantle kulit di punggung: MEMBINGKAI badan, tidak
        melebarinya. Tepi bawah robek dan berayun dengan LAG terhadap
        badan (sway mengikuti phase, bukan pose) - itu yang membuat kain
        terasa punya berat sendiri.
        """
        p = _NS_gornak.PALETTE
        sway = int(math.sin(phase * 1.05) * 2)
        if action == "walk":
            sway -= 2 + int(math.sin(phase * 1.72) * 2)
        elif action == "attack":
            # Follow-through: mantel terlempar ke belakang saat menebas.
            sway -= 2 + int(math.sin(ap * math.pi) * 3)
        elif action in ("void", "ward"):
            sway -= 1
        hem_spine = [(-22 + sway, 10), (-17 + sway, 17), (-11 + sway, 9),
                     (-6 + sway, 16), (0, 7)]
        tuft = _NS_gornak._tuft_points(hem_spine, depth=2.2, min_len=4.0,
                                       seed=11)
        outer = [(-15, -19), (-19, -6)] + tuft + [(4, -8), (2, -19)]
        poly_free(p["robe_darkest"], [pt(*q) for q in outer])
        inner = [(-14, -17), (-17, -6), (-20 + sway, 8), (-15 + sway, 14),
                 (-10 + sway, 8), (-5 + sway, 13), (0, 6), (3, -8), (1, -17)]
        poly_free(p["robe_dark"], [pt(*q) for q in inner], outline=False)
        # Lipatan: satu bidang mid + satu bidang light, arah jatuh sama.
        poly_free(p["robe_mid"], [pt(-13, -15), pt(-9, -14),
                                  pt(-11 + sway, 6), pt(-15 + sway, 5)],
                  outline=False)
        poly_free(p["robe_light"], [pt(-9, -12), pt(-12 + sway, 1),
                                    pt(-9 + sway, 7), pt(-6, -6)],
                  outline=False)
        # Rim 1 px di tepi robek: sobekan terbaca sebagai KAIN, bukan lubang.
        hem = [(-16 + sway, 9), (-12 + sway, 15), (-8 + sway, 8),
               (-4 + sway, 14), (0, 6)]
        for i in range(len(hem) - 1):
            _NS_gornak._aaline(surface, p["robe_edge"], pt(*hem[i]),
                               pt(*hem[i + 1]), 1)
        # Dither 50% di sisi bayangan jubah (1 px).
        dots = [pt(-18 + sway, 6), pt(-16 + sway, 10), pt(-14 + sway, 13),
                pt(-12 + sway, 8), pt(-10 + sway, 12), pt(-8 + sway, 7)]
        _NS_gornak._dither_dots(surface, p["robe_darkest"], dots, 110)

    def _draw_gnk_legs(surface, pt, ptg, poly_free, f, phase, action, stride):
        """Dua kaki berotot: paha -> pelindung lutut -> greave -> boot.

        Paha & betis sengaja GELAP dengan satu garis tepi terang di sisi
        cahaya; kalau blok tulang kering dibuat pucat, kedua kaki menyatu
        dengan loincloth jadi satu tiang di skala hero.
        """
        p = _NS_gornak.PALETTE
        hip_y = 4
        ground = _NS_gornak.FEET_DY
        for side in (-1, 1):
            if action == "walk":
                dx = int(stride * 8) * side
                lift = int(max(0.0, -stride * side) * 4)
            elif action == "attack":
                dx = 8 if side > 0 else -7
                lift = 0
            elif action in ("surge", "void"):
                dx = 7 if side > 0 else -7
                lift = 0
            else:
                dx = 4 if side > 0 else -6
                lift = 0
            front = side > 0
            hip_x = side * 7
            knee_x = hip_x + int(dx * 0.55) + side
            foot_x = hip_x + dx + side * 2
            knee_y = (hip_y + ground) // 2 - lift
            fy = ground - lift
            # Paha: core -> body -> plane cahaya
            poly_free(p["skin_darkest"], [pt(hip_x - 6, hip_y),
                                          pt(hip_x + 5, hip_y),
                                          pt(knee_x + 4, knee_y),
                                          pt(knee_x - 5, knee_y)])
            poly_free(p["skin_dark"] if front else p["skin_darkest"],
                      [pt(hip_x - 5, hip_y + 1), pt(hip_x + 4, hip_y + 1),
                       pt(knee_x + 3, knee_y - 1), pt(knee_x - 4, knee_y - 1)],
                      outline=False)
            if front:
                poly_free(p["skin_mid"], [pt(hip_x - 4, hip_y + 2),
                                          pt(hip_x + 1, hip_y + 2),
                                          pt(knee_x - 1, knee_y - 4),
                                          pt(knee_x - 3, knee_y - 4)],
                          outline=False)
            # Pembungkus kain di paha (senada loincloth -> kaki menyatu
            # dengan badan, bukan dua tabung terpisah)
            poly_free(p["robe_dark"], [pt(hip_x - 6, hip_y + 7),
                                       pt(hip_x + 5, hip_y + 7),
                                       pt(hip_x + 5, hip_y + 13),
                                       pt(hip_x - 6, hip_y + 13)])
            if front:
                poly_free(p["robe_mid"], [pt(hip_x - 4, hip_y + 8),
                                          pt(hip_x + 2, hip_y + 8),
                                          pt(hip_x + 2, hip_y + 12),
                                          pt(hip_x - 4, hip_y + 12)],
                          outline=False)
                _NS_gornak._aaline(surface, p["robe_edge"],
                                   pt(hip_x - 4, hip_y + 13),
                                   pt(hip_x + 2, hip_y + 13), 1)
            # Pelindung lutut
            poly_free(p["armor_darkest"], [pt(knee_x - 4, knee_y - 3),
                                           pt(knee_x + 4, knee_y - 3),
                                           pt(knee_x + 4, knee_y + 3),
                                           pt(knee_x - 4, knee_y + 3)])
            poly_free(p["armor_mid"] if front else p["armor_dark"],
                      [pt(knee_x - 3, knee_y - 2), pt(knee_x + 2, knee_y - 2),
                       pt(knee_x + 2, knee_y + 2), pt(knee_x - 3, knee_y + 2)],
                      outline=False)
            if front:
                _NS_gornak._aacircle(surface, p["armor_shine"],
                                     pt(knee_x - 1, knee_y - 1), 1)
            # Betis gelap + satu garis tepi cahaya
            poly_free(p["armor_dark"], [pt(knee_x - 4, knee_y + 2),
                                        pt(knee_x + 4, knee_y + 2),
                                        ptg(foot_x + 4, fy - 7),
                                        ptg(foot_x - 4, fy - 7)])
            if front:
                poly_free(p["armor_mid"], [pt(knee_x - 3, knee_y + 3),
                                           pt(knee_x + 1, knee_y + 3),
                                           ptg(foot_x + 1, fy - 8),
                                           ptg(foot_x - 3, fy - 8)],
                          outline=False)
                _NS_gornak._aaline(surface, p["armor_light"],
                                   pt(knee_x - 2, knee_y + 4),
                                   ptg(foot_x - 2, fy - 7), 1)
                dots = []
                for k in range(4):
                    t = (k + 0.5) / 4.0
                    gx = knee_x + (foot_x - knee_x) * t + 2
                    gy = (knee_y + 3) + (fy - 8 - (knee_y + 3)) * t
                    dots.append(ptg(gx, gy) if gy > knee_y + 6 else pt(gx, gy))
                _NS_gornak._dither_dots(surface, p["armor_darkest"], dots, 90)
            # Boot gelap + kap kuningan, sol DATAR di garis tanah
            toe = 4 if f > 0 else -4
            poly_free(p["leather_dark"], [ptg(foot_x - 5, fy - 7),
                                          ptg(foot_x + 5, fy - 7),
                                          ptg(foot_x + toe + 2, fy - 2),
                                          ptg(foot_x + toe, fy),
                                          ptg(foot_x - toe, fy),
                                          ptg(foot_x - 6, fy - 3)])
            poly_free(p["leather_mid"], [ptg(foot_x - 4, fy - 6),
                                         ptg(foot_x + 4, fy - 6),
                                         ptg(foot_x + toe + 1, fy - 3),
                                         ptg(foot_x - 5, fy - 3)],
                      outline=False)
            # Garis break terang di pergelangan: tanpa ini paha-celana-boot
            # jadi satu kolom cokelat dan kaki "hilang" di skala hero.
            _NS_gornak._aaline(surface, p["leather_light"],
                               ptg(foot_x - 5, fy - 7),
                               ptg(foot_x + 4, fy - 7), 1)
            _NS_gornak._aaline(surface, p["brass_mid"],
                               ptg(foot_x + toe - 1, fy - 4),
                               ptg(foot_x + toe + 2, fy - 2), 2)
            if lift <= 0:
                _NS_gornak._aaline(surface, p["shadow_deep"],
                                   ptg(foot_x - 5, fy + 1),
                                   ptg(foot_x + 5, fy + 1), 2)
            else:
                _NS_gornak._aaline(surface, (*p["shadow"], 80),
                                   ptg(foot_x - 4, _NS_gornak.FEET_DY),
                                   ptg(foot_x + 4, _NS_gornak.FEET_DY), 2)

    def _draw_gnk_torso(surface, pt, poly_free, dot, f, phase, breath, ward,
                        void):
        """Dada bidang (V-taper) + pelat spellbreaker + permata rune ungu.

        Pelat baja dipertahankan di armor_mid/light (bukan mid saja):
        kalau senilai kulit, seluruh badan jadi satu blob cokelat di
        skala hero. Permata ungu = "sinyal warna" tema, sama seperti api
        Grimjaw / void cyan Vex.
        """
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        twist = int(math.sin(phase * 1.05))
        poly_free(p["skin_darkest"], [pt(-14 + twist, sh - 1),
                                      pt(13 + twist, sh - 1), pt(10, 4),
                                      pt(-11, 4)])
        poly_free(p["skin_dark"], [pt(-12 + twist, sh), pt(12 + twist, sh),
                                   pt(9, 3), pt(-10, 3)], outline=False)
        poly_free(p["skin_mid"], [pt(-10 + twist, sh + 1),
                                  pt(9 + twist, sh + 1), pt(7, -2),
                                  pt(-8, -2)], outline=False)
        # Pektoral: satu blok terang di dada DEPAN + bayangan di bawahnya.
        poly_free(p["skin_light"], [pt(1 + twist, sh + 2),
                                    pt(9 + twist, sh + 2),
                                    pt(8, sh + 8), pt(0, sh + 8)],
                  outline=False)
        poly_free(p["skin_dark"], [pt(0 + twist, sh + 8), pt(9, sh + 8),
                                   pt(8, sh + 10), pt(-1, sh + 10)],
                  outline=False)
        _NS_gornak._aaline(surface, p["skin_shine"], pt(2 + twist, sh + 3),
                           pt(8 + twist, sh + 3), 1)
        # Garis tengah + perut (nilai, bukan outline)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(twist, sh + 3),
                           pt(0, 2), 1)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(-5, -2), pt(5, -2), 1)
        _NS_gornak._aaline(surface, p["skin_dark"], pt(-4, 1), pt(4, 1), 1)
        # Harness kulit diagonal - satu jalur tipis (versi 5 px jadi palang)
        _NS_gornak._aaline(surface, p["leather_dark"], pt(12 + twist, sh),
                           pt(-9, 3), 3)
        _NS_gornak._aaline(surface, p["leather_light"], pt(12 + twist, sh),
                           pt(-9, 3), 1)
        # Pelat spellbreaker: SATU bentuk gelap, tepi atas terang, satu
        # permata. Garis silang + tiga rune (versi lama) di 720p hanya
        # terbaca sebagai noda lavender.
        poly_free(p["armor_darkest"], [pt(-12, sh + 1), pt(-1, sh + 2),
                                       pt(0, -5), pt(-11, -6)])
        poly_free(p["armor_mid"], [pt(-11, sh + 2), pt(-2, sh + 3),
                                   pt(-1, -5), pt(-10, -6)], outline=False)
        poly_free(p["armor_light"], [pt(-10, sh + 3), pt(-4, sh + 4),
                                     pt(-4, -3), pt(-9, -4)], outline=False)
        _NS_gornak._aaline(surface, p["armor_shine"], pt(-11, sh + 3),
                           pt(-2, sh + 4), 2)
        _NS_gornak._aaline(surface, p["armor_darkest"], pt(-1, sh + 3),
                           pt(0, -5), 1)
        hot = 0.40 + (0.60 if (ward or void) else 0.0)
        a = _NS_gornak._alpha(150 + 105 * hot *
                              (0.72 + 0.28 * math.sin(phase * 2.2)))
        gemx, gemy = pt(-6, sh + 5)
        _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (gemx, gemy), 3)
        _NS_gornak._aacircle(surface, p["magic_hot"], (gemx, gemy), 2)
        _NS_gornak._rect(surface, p["magic_shine"], (gemx - 1, gemy - 1, 2, 2))
        # Cincin kuningan di ujung harness (satu nilai saja sudah terbaca)
        dot(p["brass_dark"], -1, -7, 2)
        dot(p["brass_mid"], -1, -7, 1)

    def _draw_gnk_belt(surface, pt, poly_free, dot, f, phase, action, stride):
        """Sabuk + gesper berlian ungu, loincloth, rantai lempengan besi."""
        p = _NS_gornak.PALETTE
        sway = int(math.sin(phase * 1.1) * 2)
        if action == "walk":
            sway += int(stride * 2)
        poly_free(p["leather_dark"], [pt(-12, 1), pt(12, 1), pt(12, 7),
                                      pt(-12, 7)])
        poly_free(p["leather_mid"], [pt(-11, 2), pt(11, 2), pt(11, 6),
                                     pt(-11, 6)], outline=False)
        _NS_gornak._aaline(surface, p["leather_light"], pt(-11, 2), pt(11, 2),
                           1)
        for bx in (-8, -3, 7):
            _NS_gornak._aacircle(surface, p["brass_mid"], pt(bx, 4), 1)
        poly_free(p["armor_darkest"], [pt(-3, 0), pt(4, 0), pt(4, 8),
                                       pt(-3, 8)])
        poly_free(p["armor_light"], [pt(-2, 1), pt(3, 1), pt(3, 6), pt(-2, 6)],
                  outline=False)
        _NS_gornak._aacircle(surface, p["magic_hot"], pt(0, 4), 2)
        _NS_gornak._aacircle(surface, p["magic_shine"], pt(0, 4), 1)
        # Loincloth bertepi robek. Sengaja sempit (lebar 12, panjang 20):
        # versi lebar mengubah kedua kaki jadi satu tiang ungu.
        hem = [(4 + sway, 18), (1 + sway, 24), (-2, 18), (-3, 24),
               (-6, 18), (-8 + sway, 22), (-10 + sway, 16)]
        tuft = _NS_gornak._tuft_points(hem, depth=1.8, min_len=3.5, seed=3)
        outer = [(-8, 7), (3, 7)] + tuft
        poly_free(p["robe_darkest"], [pt(*q) for q in outer])
        inner = [(-7, 8), (2, 8), (3 + sway, 17), (0 + sway, 21), (-2, 17),
                 (-4, 21), (-7 + sway, 15)]
        poly_free(p["robe_dark"], [pt(*q) for q in inner], outline=False)
        poly_free(p["robe_mid"], [pt(-3, 9), pt(3, 9), pt(3 + sway, 18),
                                  pt(0, 22), pt(-3 + sway, 17)],
                  outline=False)
        _NS_gornak._aaline(surface, p["robe_edge"], pt(-6, 9),
                           pt(-8 + sway, 20), 1)
        # Rantai lempengan pemutus sihir
        for i in range(3):
            yy = 9 + i * 4
            _NS_gornak._aaline(surface, p["armor_shine"], pt(9, yy),
                               pt(11 + int(sway * 0.3), yy + 3), 1)
            _NS_gornak._aacircle(surface, p["armor_light"], pt(10, yy + 1), 1)
        # Kantong kulit
        poly_free(p["leather_dark"], [pt(-13, 8), pt(-8, 8), pt(-7, 15),
                                      pt(-13, 15)])
        poly_free(p["leather_mid"], [pt(-12, 9), pt(-9, 9), pt(-8, 14),
                                     pt(-12, 14)], outline=False)

    def _draw_gnk_pauldrons(surface, pt, poly_free, dot, f, phase, breath):
        """Pauldron baja bertingkat + duri + permata ungu di sisi depan."""
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        for side, scale in ((-1, 0.80), (1, 1.0)):
            sx = side * 15
            sy = sh - 2 - int(breath if side > 0 else 0)
            w = max(4, int(7 * scale))
            h = max(3, int(5 * scale))
            poly_free(p["armor_darkest"], [pt(sx - w, sy - h + 2),
                                           pt(sx + w, sy - h),
                                           pt(sx + w + 1, sy + 2),
                                           pt(sx, sy + h),
                                           pt(sx - w - 1, sy + 2)])
            poly_free(p["armor_mid"] if side > 0 else p["armor_dark"],
                      [pt(sx - w + 1, sy - h + 3), pt(sx + w - 1, sy - h + 3),
                       pt(sx + w, sy), pt(sx, sy + h - 2), pt(sx - w, sy)],
                      outline=False)
            # Sisi JAUH dibiarkan gelap; cahaya & permata tema ditaruh di
            # sisi DEPAN, searah key light.
            lit = p["armor_light"] if side > 0 else p["armor_dark"]
            poly_free(lit, [pt(sx - w + 2, sy - h + 4),
                            pt(sx - 1, sy - h + 4),
                            pt(sx - 1, sy - 1),
                            pt(sx - w + 2, sy - 1)], outline=False)
            if side > 0:
                _NS_gornak._aaline(surface, p["armor_shine"],
                                   pt(sx - w + 2, sy - h + 4),
                                   pt(sx + w - 1, sy - h + 3), 1)
                # Specular cluster 1-2 px (bukan gradien).
                hx, hy = pt(sx - 2, sy - h + 3)
                _NS_gornak._rect(surface, p["armor_shine"], (hx, hy, 2, 1))
                _NS_gornak._rect(surface, p["white"], (hx, hy, 1, 1))
            spike = sy - h - (4 if side > 0 else 3)
            poly_free(p["armor_darkest"], [pt(sx - 2, sy - h + 1),
                                           pt(sx + 1, spike),
                                           pt(sx + 3, sy - h + 1)])
            poly_free(p["armor_light"] if side > 0 else p["armor_mid"],
                      [pt(sx - 1, sy - h + 1), pt(sx + 1, spike + 1),
                       pt(sx + 2, sy - h + 1)], outline=False)
            _NS_gornak._aacircle(surface, p["brass_mid"],
                                 pt(sx + side * 4, sy + 2), 1)
            if side > 0:
                _NS_gornak._aacircle(surface, p["magic_mid"],
                                     pt(sx - 3, sy - 1), 2)
                _NS_gornak._rect(surface, p["magic_shine"],
                                 (pt(sx - 3, sy - 1)[0],
                                  pt(sx - 3, sy - 1)[1], 1, 1))

    def _draw_gnk_head(surface, pt, poly_free, dot, f, phase, action, ap,
                       ward, void):
        """KEPALA sebagai SUBJEK gambar.

        Aturan yang dipakai: tempurung kepala BESAR (proporsi heroik,
        bukan realistis - di 65 px badan, kepala kecil selalu jadi blob),
        satu massa rambut solid alih-alih helaian, bidang wajah TERANG
        menghadap depan-atas, dan mata sebagai nilai tertinggi di seluruh
        sprite. Semua detail lain di kepala dijaga agar tidak menyamai
        kecerahan mata; kalau bilah atau permata lebih terang, pandangan
        pemain jatuh ke sana dan kepala kehilangan perannya.
        """
        p = _NS_gornak.PALETTE
        bx, by = _NS_gornak._head_bob(action, phase, ap)
        hy = _NS_gornak.HEAD_Y + by
        hx = bx + (1 if action in ("attack", "surge") else 0)
        sh = _NS_gornak.SHOULDER_Y
        lag = math.sin(phase * 1.05 - 0.8)          # rambut & jenggot telat

        def H(dx, dy):
            return pt(hx + dx, hy + dy)

        # ── Leher & trapezius (digambar lebih dulu = di belakang rahang)
        poly_free(p["skin_darkest"], [pt(-7, sh + 1), pt(7, sh + 1),
                                      H(6, 8), H(-5, 8)])
        poly_free(p["skin_dark"], [pt(-5, sh), pt(5, sh), H(5, 8), H(-4, 8)],
                  outline=False)

        # ── Mohawk: SATU massa bergerigi, berayun telat terhadap badan
        drift = int(round(lag * 1.6))
        crest = [(-8, -7), (-7, -14), (-5, -9), (-2, -17),
                 (1, -10), (4, -16), (7, -9), (9, -13), (10, -6)]
        crest = [(qx + (drift if qy < -8 else 0), qy) for qx, qy in crest]
        poly_free(p["hair_darkest"],
                  [H(*q) for q in crest] + [H(10, -2), H(-8, -2)])
        inner = [(qx, qy + 3) if qy < -8 else (qx, qy) for qx, qy in crest]
        poly_free(p["hair_dark"],
                  [H(*q) for q in inner] + [H(9, -3), H(-7, -3)],
                  outline=False)
        poly_free(p["hair_mid"], [H(-5, -7), H(-2, -13), H(1, -8), H(4, -12),
                                  H(7, -7), H(7, -3), H(-5, -3)],
                  outline=False)
        for tipx, tipy in ((-7 + drift, -13), (-2 + drift, -16),
                           (4 + drift, -15), (9 + drift, -12)):
            _NS_gornak._aaline(surface, p["hair_light"], H(tipx, tipy + 4),
                               H(tipx, tipy), 1)
            _NS_gornak._rect(surface, p["hair_shine"],
                             (H(tipx, tipy)[0], H(tipx, tipy)[1], 1, 1))

        # ── Tempurung kepala (3 nilai + bidang wajah)
        poly_free(p["skin_darkest"], [H(-9, -8), H(3, -10), H(9, -7),
                                      H(11, 0), H(9, 7), H(2, 10),
                                      H(-6, 8), H(-9, 0)])
        poly_free(p["skin_dark"], [H(-8, -7), H(3, -9), H(8, -6), H(10, 0),
                                   H(8, 6), H(2, 9), H(-5, 7), H(-8, 0)],
                  outline=False)
        poly_free(p["skin_mid"], [H(-6, -7), H(3, -8), H(8, -5), H(9, 0),
                                  H(7, 6), H(1, 8), H(-5, 5)],
                  outline=False)
        poly_free(p["skin_light"], [H(0, -6), H(8, -4), H(10, 1), H(7, 7),
                                    H(0, 7)], outline=False)
        poly_free(p["skin_shine"], [H(4, 2), H(9, 2), H(8, 5), H(4, 5)],
                  outline=False)
        _NS_gornak._rect(surface, p["skin_high"],
                         (H(7, 3)[0], H(7, 3)[1], 2, 1))

        # ── Circlet kuningan + permata rune (di DAHI, tidak menutup mata)
        poly_free(p["brass_dark"], [H(-9, -6), H(10, -5), H(10, -3),
                                    H(-9, -4)])
        _NS_gornak._aaline(surface, p["brass_mid"], H(-8, -5), H(9, -4), 1)
        _NS_gornak._rect(surface, p["brass_light"],
                         (H(3, -5)[0], H(3, -5)[1], 1, 1))
        gx, gy = H(9, -4)
        _NS_gornak._aacircle(surface, p["magic_mid"], (gx, gy), 2)
        _NS_gornak._rect(surface, p["magic_hot"], (gx, gy - 1, 1, 2))

        # ── Bayangan alis: satu pita gelap membuat mata "cekung"
        poly_free(p["skin_darkest"], [H(0, -3), H(10, -2), H(10, 0),
                                      H(0, -1)], outline=False)

        # ── MATA: nilai tertinggi di sprite (halo -> iris -> kilat inti)
        glow = 1.0 if (ward or void) else (0.78 + 0.22 * math.sin(phase * 2.4))
        # Dua rongga TERPISAH: kalau soket saling bersentuhan setelah
        # SCALE, dua mata terbaca sebagai satu pita terang (visor helm).
        for ex in (2, 8):
            _NS_gornak._rect(surface, p["eye_dark"],
                             (H(ex, -1)[0], H(ex, -1)[1], 3, 4))
            _NS_gornak._aacircle(surface,
                                 (*p["magic_light"],
                                  _NS_gornak._alpha(110 * glow)),
                                 (H(ex, 1)[0] + 1, H(ex, 1)[1]), 2)
            _NS_gornak._rect(surface, p["eye_mid"],
                             (H(ex, 0)[0], H(ex, 0)[1], 3, 2))
            _NS_gornak._rect(surface, p["eye_light"],
                             (H(ex, 0)[0], H(ex, 0)[1], 2, 1))
            _NS_gornak._rect(surface, p["eye_glow"],
                             (H(ex, 0)[0], H(ex, 0)[1], 1, 1))

        # ── Hidung & mulut (nilai, bukan garis halus)
        _NS_gornak._aaline(surface, p["skin_dark"], H(10, 2), H(11, 4), 1)
        _NS_gornak._aaline(surface, p["beard_darkest"], H(4, 6), H(9, 6), 1)

        # ── Jenggot kepang: dua untai + cincin kuningan, ikut lag
        bl = int(round(lag * 1.2))
        poly_free(p["beard_darkest"], [H(-2, 7), H(9, 7), H(10, 11),
                                       H(6 + bl, 17), H(3, 12),
                                       H(1 + bl, 15), H(-3, 10)])
        poly_free(p["beard_mid"], [H(-1, 8), H(8, 8), H(9, 11),
                                   H(5 + bl, 15), H(3, 12),
                                   H(2 + bl, 13), H(-2, 10)], outline=False)
        poly_free(p["beard_dark"], [H(-1, 8), H(3, 8), H(3, 11),
                                    H(1 + bl, 13), H(-2, 10)], outline=False)
        poly_free(p["beard_light"], [H(4, 9), H(8, 9), H(8, 11),
                                     H(5 + bl, 13)], outline=False)
        _NS_gornak._aaline(surface, p["beard_light"], H(2, 8), H(8, 9), 1)
        for rx, ry in ((5 + bl, 14), (2 + bl, 13)):
            _NS_gornak._aacircle(surface, p["brass_dark"], H(rx, ry), 2)
            _NS_gornak._aacircle(surface, p["brass_mid"], H(rx, ry), 1)

        # ── Kuncir samping (mengunci siluet sisi belakang kepala)
        poly_free(p["hair_dark"], [H(-8, -4), H(-5, -3), H(-4, 5),
                                   H(-7 + drift, 11), H(-10, 4)])
        poly_free(p["hair_mid"], [H(-7, -3), H(-5, -2), H(-5, 5),
                                  H(-7 + drift, 9)], outline=False)

    def _draw_gnk_rimlight(surface, pt, f, phase, ward, void):
        """Rim light ungu tipis di tepi yang menghadap cahaya.

        Semua hero masterwork punya "sinyal" warna di tepian (Grimjaw api,
        Vex void cyan, Kaizen angin biru) sehingga terbaca saat unit
        bertumpuk. Gornak memakai ungu anti-sihir; 1 px saja, tapi di
        posisi yang tepat (puncak krist, tepi pelat, sabuk, ujung boot).
        """
        p = _NS_gornak.PALETTE
        sh = _NS_gornak.SHOULDER_Y
        hy = _NS_gornak.HEAD_Y
        pulse = 1.0 if (ward or void) else (0.72 + 0.28 * math.sin(phase * 1.8))
        a = _NS_gornak._alpha(150 * pulse)
        col = (*p["magic_light"], a)
        _NS_gornak._aaline(surface, col, pt(-8, hy - 10), pt(3, hy - 11), 1)
        _NS_gornak._aaline(surface, col, pt(-11, sh + 1), pt(-11, -5), 1)
        _NS_gornak._aaline(surface, (*p["magic_hot"], a), pt(-12, 1),
                           pt(12, 1), 1)
        # Kaki: garis harus jatuh DI ATAS tulang kering, bukan di celah
        # antara dua kaki (versi lama menyisakan garis ungu melayang).
        for kx, fx in ((10, 13), (-11, -15)):
            _NS_gornak._aaline(surface, col, pt(kx, 26), pt(fx, 36), 1)
            _NS_gornak._aacircle(surface, col, pt(fx, 40), 1)

    def _draw_gnk_arm(surface, pt, poly_free, dot, limb, f, phase, action, ap,
                      shoulder, elbow, grip, blade_angle, blade_len,
                      back=False, ward=False, void=False, surge=False):
        """Lengan 2-tulang + bracer + bilah.

        Bayangan antar-bagian cukup +2 px; outline luar sudah memberi
        pemisah, jadi tidak perlu tebal.
        """
        p = _NS_gornak.PALETTE
        base = p["skin_dark"] if back else p["skin_mid"]
        high = p["skin_mid"] if back else p["skin_light"]
        limb(shoulder, elbow, 6 if back else 7, base, high)
        limb(elbow, grip, 5 if back else 6, base, high)
        # Balutan kulit di lengan atas: memecah bidang coklat polos jadi
        # dua massa (deltoid / biseps) tanpa menambah siluet.
        sxa, sya = shoulder
        exa, eya = elbow
        dxa, dya = exa - sxa, eya - sya
        dla = math.hypot(dxa, dya) or 1.0
        uxa, uya = dxa / dla, dya / dla
        pxa, pya = -uya, uxa
        wrapw = 2.6 if back else 3.2
        wrapc = p["leather_dark"] if back else p["leather_mid"]
        for u, thick in ((0.40, 1.6), (0.66, 1.2)):
            wcx = sxa + dxa * u
            wcy = sya + dya * u
            poly_free(p["skin_darkest"] if back else wrapc,
                      [pt(wcx + pxa * wrapw, wcy + pya * wrapw),
                       pt(wcx - pxa * wrapw, wcy - pya * wrapw),
                       pt(wcx - pxa * wrapw + uxa * thick,
                          wcy - pya * wrapw + uya * thick),
                       pt(wcx + pxa * wrapw + uxa * thick,
                          wcy + pya * wrapw + uya * thick)], outline=False)
        if not back:
            # Kilau 1 px di sisi atas deltoid.
            dot(p["skin_shine"],
                sxa + dxa * 0.22 + uya * 1.8,
                sya + dya * 0.22 - uxa * 1.8, 1, outline=False)
        # Bracer besi: satu blok di tengah lengan bawah
        bx = int(elbow[0] * 0.4 + grip[0] * 0.6)
        by = int(elbow[1] * 0.4 + grip[1] * 0.6)
        poly_free(p["armor_darkest"], [pt(bx - 3, by - 3), pt(bx + 3, by - 3),
                                       pt(bx + 3, by + 3), pt(bx - 3, by + 3)])
        poly_free(p["armor_mid"] if back else p["armor_light"],
                  [pt(bx - 2, by - 2), pt(bx + 1, by - 2),
                   pt(bx + 1, by + 2), pt(bx - 2, by + 2)], outline=False)
        if not back:
            _NS_gornak._rect(surface, p["armor_shine"],
                             (pt(bx - 2, by - 2)[0], pt(bx - 2, by - 2)[1],
                              2, 1))
        # Telapak + buku jari: tanpa ini bilah terlihat "menempel" di dada
        dot(p["skin_darkest"], *grip, 3 if back else 4)
        dot(high, *grip, 2 if back else 3)
        if not back:
            kx, ky = pt(grip[0] + 1, grip[1] - 2)
            _NS_gornak._aacircle(surface, p["skin_shine"], (kx, ky), 2)
        _NS_gornak._draw_gnk_blade(surface, pt, f, grip, blade_angle,
                                   blade_len, phase, action, back=back,
                                   ward=ward, void=void, surge=surge)

    def _draw_gnk_blade(surface, pt, f, grip, angle, length, phase, action,
                        back=False, ward=False, void=False, surge=False):
        """Bilah "spellbreaker" ASIMETRIS - dihitung dari grip + sudut.

        Bentuknya sengaja tidak simetris: punggung tebal & gelap,
        MATA BILAH tipis & terang di sisi potong, fuller ungu di tengah.
        Versi lama memakai tiga poligon inset sehingga terbaca sebagai
        jarum putih; dengan punggung gelap, senjata jadi punya arah dan
        tebasan langsung terbaca ke mana bilah menghadap.
        """
        p = _NS_gornak.PALETTE
        s, c = math.sin(angle), math.cos(angle)
        n_x, n_y = c, -s                              # normal = sisi potong
        segs = 6
        curve = 4.5 if not back else 2.8
        w0 = 3.4 if not back else 2.5
        w1 = 0.7

        spine, edge, mid, backline = [], [], [], []
        for i in range(segs + 1):
            t = i / segs
            bend = curve * (t * t)
            cxp = grip[0] + s * length * t + n_x * bend
            cyp = grip[1] + c * length * t + n_y * bend
            w = w0 * (1.0 - t) + w1 * t
            backline.append((cxp - n_x * w * 0.55, cyp - n_y * w * 0.55))
            spine.append((cxp, cyp))
            mid.append((cxp + n_x * w * 0.28, cyp + n_y * w * 0.28))
            edge.append((cxp + n_x * w * 0.62, cyp + n_y * w * 0.62))

        def S(seq):
            return [pt(int(round(qx)), int(round(qy))) for qx, qy in seq]

        s_back, s_spine, s_mid, s_edge = (S(backline), S(spine), S(mid),
                                          S(edge))
        full = s_edge + s_back[::-1]
        _NS_gornak._poly(surface, p["shadow_deep"],
                         [(q[0] + f, q[1] + 1) for q in full])
        _NS_gornak._poly(surface, p["blade_darkest"], full)
        # Punggung gelap -> badan -> pita mata terang (3 nilai, tanpa gradien)
        _NS_gornak._poly(surface, p["blade_dark"], s_back + s_spine[::-1])
        _NS_gornak._poly(surface, p["blade_mid"], s_spine + s_mid[::-1])
        _NS_gornak._poly(surface, p["blade_light"], s_mid + s_edge[::-1])
        # MATA BILAH: satu garis 1 px paling terang di sisi potong
        for i in range(len(s_edge) - 1):
            _NS_gornak._aaline(surface, p["blade_shine"], s_edge[i],
                               s_edge[i + 1], 1)
        # Hamon: dither 1 px sepanjang badan bilah
        _NS_gornak._dither_dots(surface, p["blade_hamon"], s_mid[1:], 150)

        # Fuller / rune penyedot mana - menyala saat menyerang & skill
        hot = 0.30 + (0.70 if (ward or void or surge or action == "attack")
                      else 0.0)
        glow_a = _NS_gornak._alpha(160 * hot *
                                   (0.8 + 0.2 * math.sin(phase * 2.2)))
        if not back:
            for i in range(len(s_spine) - 1):
                _NS_gornak._aaline(surface, (*p["magic_light"], glow_a),
                                   s_spine[i], s_spine[i + 1], 1)

        # Cross-guard + gagang kulit + pommel kuningan
        g1 = pt(int(grip[0] - c * 4), int(grip[1] + s * 4))
        g2 = pt(int(grip[0] + c * 4), int(grip[1] - s * 4))
        _NS_gornak._aaline(surface, p["shadow_deep"], (g1[0] + f, g1[1] + 1),
                           (g2[0] + f, g2[1] + 1), 4)
        _NS_gornak._aaline(surface, p["armor_dark"], g1, g2, 3)
        _NS_gornak._aaline(surface, p["armor_light"], g1, g2, 1)
        butt = pt(int(grip[0] - s * 6), int(grip[1] - c * 6))
        gx, gy = pt(*grip)
        _NS_gornak._aaline(surface, p["leather_dark"], (gx, gy), butt, 4)
        _NS_gornak._aaline(surface, p["leather_light"], (gx, gy), butt, 1)
        _NS_gornak._aacircle(surface, p["brass_dark"], butt, 2)
        _NS_gornak._aacircle(surface, p["brass_mid"], butt, 1)

        # Ujung: glint + inti ungu (titik lahir semua FX Q / slash)
        tip = s_spine[-1]
        _NS_gornak._aacircle(surface, (*p["magic_hot"], glow_a), tip, 2)
        if not back and len(s_edge) > 3:
            gl = s_edge[2]
            _NS_gornak._rect(surface, p["blade_shine"],
                             (gl[0] - 1, gl[1] - 1, 2, 1))
            _NS_gornak._rect(surface, p["white"], (gl[0], gl[1] - 1, 1, 1))
        if (ward or void or surge) and not back:
            _NS_gornak._spark_star(
                surface, tip[0], tip[1], 7, p["magic_hot"],
                _NS_gornak._alpha(glow_a * 0.85), spikes=6,
                rot=phase * 1.6, core=p["magic_shine"])

    # ==================================================================
    # PORTRAIT LOD - material tambahan (Hero Shop / panel)
    # ==================================================================
    def _draw_gnk_weave(surface, pt, f):
        """Tenun kain & grain kulit - HANYA portrait LOD.

        Dither 1-px seperti ini jadi noise setelah jalur hero
        men-smoothscale sprite ke 0.7-0.8, jadi dibatasi ke mode detail.
        """
        p = _NS_gornak.PALETTE
        for i in range(9):
            wx, wy = pt(-8 + (i % 4) * 4, 8 + (i // 4) * 4)
            _NS_gornak._rect(surface, (*p["robe_light"], 90), (wx, wy, 1, 1))
        for i in range(7):
            x0, y0 = -12 + i * 4, -12 + (i % 3) * 6
            _NS_gornak._rect(surface, (*p["skin_shine"], 70),
                             (pt(x0, y0)[0], pt(x0, y0)[1], 1, 1))

    def _draw_gnk_masterwork_details(surface, pt, f, phase, action):
        """Detail frekuensi tinggi; di skala arena hanya jadi noise, jadi
        hanya dinyalakan saat portrait."""
        p = _NS_gornak.PALETTE
        hx = 1 if f > 0 else -1
        cy = _NS_gornak.HEAD_Y
        # Serat di DALAM massa mohawk (bukan helai lepas di atas siluet):
        # garis nilai terang mengikuti arah tumbuh duri.
        crest = ((-7, -13, -8, -8), (-2, -16, -3, -10),
                 (4, -15, 3, -9), (9, -12, 8, -7))
        for i, (ax, ay, bx2, by2) in enumerate(crest):
            sway = int(math.sin(phase * 1.4 + i) * 1.0)
            _NS_gornak._aaline(surface, p["hair_shine"],
                               pt(hx + ax + sway, cy + ay + 1),
                               pt(hx + bx2, cy + by2), 1)
            _NS_gornak._aaline(surface, p["hair_dark"],
                               pt(hx + ax + sway + 1, cy + ay + 2),
                               pt(hx + bx2 + 1, cy + by2), 1)
        # Serat jenggot
        for i in range(4):
            _NS_gornak._aaline(surface, p["beard_mid"],
                               pt(hx - 1 + i * 2, cy + 9),
                               pt(hx + i * 2, cy + 15), 1)
        # Alis tebal
        _NS_gornak._aaline(surface, p["beard_darkest"], pt(hx + 1, cy - 2),
                           pt(hx + 9, cy - 1), 1)
        # Grain kulit pada bahu & dada
        for i in range(10):
            dx = -9 + (i % 5) * 4
            dy = -17 + (i // 5) * 8
            _NS_gornak._aaline(surface, (*p["skin_shine"], 110), pt(dx, dy),
                               pt(dx + 1, dy), 1)
        # Otot leher
        _NS_gornak._aaline(surface, p["skin_dark"], pt(hx - 4, -18),
                           pt(hx - 1, -15), 1)
        # Jahitan jubah & loincloth
        for yy in (8, 13, 18):
            _NS_gornak._aaline(surface, (*p["robe_edge"], 150), pt(-15, yy),
                               pt(-10, yy + 1), 1)
        for xx in (-5, 0, 5):
            _NS_gornak._aaline(surface, (*p["robe_light"], 120), pt(xx, 8),
                               pt(xx + 1, 23), 1)
        # Tato rune anti-sihir di lengan/dada
        for i in range(4):
            _NS_gornak._aaline(surface, (*p["magic_light"], 140),
                               pt(-12 + i * 2, -13 + i * 6),
                               pt(-10 + i * 2, -11 + i * 6), 1)
        # Ukiran pelat & paku pauldron
        _NS_gornak._aaline(surface, (*p["armor_shine"], 165), pt(-9, -15),
                           pt(0, -14), 1)
        for sx, sy in ((13, -22), (15, -19), (11, -18), (-13, -21)):
            _NS_gornak._aacircle(surface, (*p["armor_shine"], 150),
                                 pt(sx, sy), 1)
        # Garis hamon bilah depan
        for i in range(5):
            t = i / 5
            _NS_gornak._aaline(surface, (*p["blade_hamon"], 170),
                               pt(15 + int(t * 12), 8 + int(t * 12)),
                               pt(16 + int(t * 12), 9 + int(t * 12)), 1)

    def _draw_footfall_dust(surface, x, y, facing, phase):
        """Kepul debu di tapak yang mendarat (deterministik dari phase)."""
        p = _NS_gornak.PALETTE
        contact = abs(math.sin(phase * 1.15))
        if contact > 0.72:
            return
        gy = y + _NS_gornak.GROUND_DY
        k = _NS_gornak._s
        for side in (-1, 1):
            for i in range(3):
                t = (contact + i * 0.3) % 1.0
                a = _NS_gornak._alpha(150 * (1.0 - t) * (0.72 - contact))
                if a <= 0:
                    continue
                px = x + side * k(7 + i * 2 + t * 5) + facing * k(t * 4)
                py = gy - k(t * 5)
                _NS_gornak._aacircle(surface, (*p["robe_edge"], a), (px, py),
                                     max(1, k(2 - t)))
                _NS_gornak._rect(surface, (*p["white"], a // 2),
                                 (px, py, 1, 1))

    # ==================================================================
    # EFEK DASAR - selalu ditundukkan pada karakter
    # ==================================================================
    def _draw_shadow(surface, x, y):
        """Bayangan kontak tunggal yang lembut (base_boss menggambar satu
        lagi; ini dipertipis supaya tidak jadi dua piringan hitam)."""
        p = _NS_gornak.PALETTE
        K = _NS_gornak.SCALE
        bw, bh = int(60 * K), int(18 * K)

        def _build():
            sh = pygame.Surface((bw, bh), pygame.SRCALPHA)
            for w, h, a in ((int(42 * K), int(10 * K), 70),
                            (int(30 * K), int(7 * K), 90),
                            (int(18 * K), int(4 * K), 110)):
                _NS_gornak._ellipse(sh, (0, 0, 0, a),
                                    (bw // 2 - w // 2, bh // 2 - h // 2, w, h))
            _NS_gornak._ellipse(sh, (*p["magic_darkest"], 60),
                                (int(6 * K), int(3 * K), int(48 * K),
                                 int(12 * K)))
            for side in (-1, 1):
                fx = bw // 2 + int(side * 9 * K)
                _NS_gornak._ellipse(sh, (0, 0, 0, 130),
                                    (fx - int(5 * K), int(bh * 0.62),
                                     int(10 * K), int(4 * K)))
            return sh

        sh = _NS_gornak._static(("gnk_shadow", bw, bh), _build)
        surface.blit(sh, (int(x) - bw // 2, int(y) - bh // 2))

    def _draw_anti_magic_field(surface, x, y, phase, skill):
        """Cahaya lembut MENEMPEL badan + serpihan mana mengorbit siluet."""
        p = _NS_gornak.PALETTE
        pulse = 1.0 if skill else math.sin(phase * 0.7) * 0.25 + 0.72
        K = _NS_gornak.SCALE
        gw, gh = int(80 * K), int(96 * K)
        cx, cy = int(40 * K), int(50 * K)

        def _build():
            glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
            for rx, ry, col, a in ((int(30 * K), int(38 * K),
                                    "magic_darkest", 78),
                                   (int(23 * K), int(30 * K), "magic_dark",
                                    96),
                                   (int(16 * K), int(22 * K), "magic_mid",
                                    120)):
                _NS_gornak._ellipse(glow, (*p[col], a),
                                    (cx - rx, cy - ry, rx * 2, ry * 2))
            _NS_gornak._ellipse(glow, (*p["magic_light"], 70),
                                (cx - int(16 * K), cy - int(22 * K),
                                 int(32 * K), int(44 * K)), 1)
            return glow

        glow = _NS_gornak._static(("gnk_aura", gw, gh), _build)
        glow.set_alpha(_NS_gornak._alpha(255 * pulse))
        surface.blit(glow, (int(x) - cx, int(y) - cy + 8))

        # Serpihan (bukan bulatan): bahasa bentuk yang sama dengan FX skill.
        n = 6
        for i in range(n):
            ang = ((phase * 0.35 + i / n) % 1.0) * math.tau
            r = _NS_gornak._s(20) + int(math.sin(phase * 1.3 + i * 2) * 3)
            sx = x + int(math.cos(ang) * r * 1.25)
            sy = y + 2 + int(math.sin(ang) * r * 0.8)
            a = _NS_gornak._alpha(120 + 80 * math.sin(phase * 3 + i))
            _NS_gornak._shard(surface, sx, sy, ang + math.pi / 2, 4, 2,
                              p["magic_mid"], a, core=p["magic_shine"])

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Sigil rune di bawah kaki - kecil TAPI terang (heksagram + tick)."""
        p = _NS_gornak.PALETTE
        pulse = math.sin(phase * 1.1) * 0.25 + 0.75
        gy = y + _NS_gornak.GROUND_DY
        bright = 1.15 if skill else 0.95
        rw, rh = _NS_gornak._s(22), _NS_gornak._s(6)
        _NS_gornak._ellipse(surface,
                            (*p["magic_darkest"],
                             _NS_gornak._alpha(150 * pulse * bright)),
                            (x - rw, gy - rh, rw * 2, rh * 2), 2)
        rw2, rh2 = _NS_gornak._s(15), _NS_gornak._s(4)
        _NS_gornak._ellipse(surface,
                            (*p["magic_mid"],
                             _NS_gornak._alpha(140 * pulse * bright)),
                            (x - rw2, gy - rh2, rw2 * 2, rh2 * 2), 1)
        # Heksagram datar (dua segitiga) - bacaan "rune", bukan cincin polos
        a_tri = _NS_gornak._alpha(120 * pulse * bright)
        for rot in (0.0, math.pi / 3):
            pts = []
            for i in range(3):
                ang = phase * 0.22 + rot + i * math.tau / 3
                pts.append((x + int(math.cos(ang) * rw2 * 1.18),
                            gy + int(math.sin(ang) * rh2 * 1.18)))
            for i in range(3):
                _NS_gornak._aaline(surface, (*p["magic_light"], a_tri),
                                   pts[i], pts[(i + 1) % 3], 1)
        t0, t1 = _NS_gornak._s(18), _NS_gornak._s(24)
        ty0, ty1 = _NS_gornak._s(5), _NS_gornak._s(6)
        for i in range(6):
            ang = phase * 0.4 + i * math.tau / 6
            _NS_gornak._aaline(
                surface,
                (*p["magic_light"], _NS_gornak._alpha(170 * pulse * bright)),
                (x + int(math.cos(ang) * t0), gy + int(math.sin(ang) * ty0)),
                (x + int(math.cos(ang) * t1), gy + int(math.sin(ang) * ty1)),
                1)
        _NS_gornak._aacircle(surface,
                             (*p["magic_shine"],
                              _NS_gornak._alpha(200 * pulse)),
                             (int(x), int(gy)), 2)
        if skill in ("e", "r"):
            ew, eh = _NS_gornak._s(26), _NS_gornak._s(7)
            _NS_gornak._ellipse(
                surface, (*p["magic_hot"], _NS_gornak._alpha(120 * pulse)),
                (x - ew, gy - eh, ew * 2, eh * 2), 1)

    # ==================================================================
    # SWING ATTACK - dua pita dari trail UJUNG BILAH yang sebenarnya
    # ==================================================================
    def _draw_crescent_slash(surface, x, y, facing, phase, progress):
        """Cross-slash dual blade.

        Pita dibangun dari posisi ujung bilah pada beberapa waktu pose ke
        belakang, jadi busur SELALU menempel di senjata (tidak pernah ada
        "serpihan" yang mengambang di samping badan seperti versi busur
        titik-melayang). Bilah belakang ikut menyapu dengan pita lebih
        kecil dan arah berlawanan -> terbaca sebagai gunting, bukan satu
        tebasan yang digandakan.
        """
        if progress < 0.20 or progress > 0.99:
            return
        p = _NS_gornak.PALETTE
        lean, root_y = _NS_gornak._rig_shift("attack", phase, progress)
        hit = _NS_gornak._SWING_HIT

        def scr(lx, ly):
            return _NS_gornak._local_to_screen(x, y, facing, lean, root_y,
                                               lx, ly)

        def tip_at(ap, back):
            return scr(*_NS_gornak._tip_local("attack", phase,
                                              max(0.0, min(1.0, ap)), back))

        if progress < 0.28:
            fade = (progress - 0.20) / 0.08
        elif progress <= hit:
            fade = 1.0
        else:
            fade = max(0.0, 1.0 - (progress - hit) / 0.17)
        if fade <= 0.02:
            return

        steps = 9
        for back in (True, False):
            span = 0.24 if back else 0.28
            wmax = 3.6 if back else 6.4
            path = [tip_at(progress - span + span * (i / (steps - 1)), back)
                    for i in range(steps)]
            widths = [wmax * ((i / (steps - 1)) ** 1.25) + 0.4
                      for i in range(steps)]
            a = _NS_gornak._alpha((190 if back else 235) * fade)
            _NS_gornak._ribbon(surface, path, [w * 1.45 for w in widths],
                               p["magic_darkest"], int(a * 0.42))
            _NS_gornak._ribbon(surface, path, widths, p["magic_mid"],
                               int(a * 0.92))
            _NS_gornak._ribbon(surface, path, [w * 0.42 for w in widths],
                               p["magic_shine"], a)
            # Tepi depan pita: 1 px paling terang = arah gerak terbaca
            for i in range(steps - 3, steps - 1):
                _NS_gornak._aaline(surface, (*p["magic_core"], a),
                                   path[i], path[i + 1], 1)
            # Speed line di dalam busur (pixel-art motion smear)
            if not back:
                for k in range(3):
                    i0 = 2 + k * 2
                    q0, q1 = path[i0], path[min(steps - 1, i0 + 3)]
                    _NS_gornak._aaline(
                        surface, (*p["magic_light"], _NS_gornak._alpha(a * .6)),
                        q0, q1, 1)

        # ── IMPACT: bintang + gelombang + serpihan yang beterbangan
        if hit - 0.10 <= progress <= hit + 0.10:
            hold = 1.0 - abs((progress - hit) / 0.10)
            tip = tip_at(progress, False)
            a = _NS_gornak._alpha(245 * hold)
            _NS_gornak._spark_star(surface, tip[0], tip[1],
                                   int(9 + 6 * hold), p["magic_hot"], a,
                                   spikes=8, rot=progress * 4.0,
                                   core=p["white"])
            wr = int(9 + hold * 12)
            _NS_gornak._ellipse(
                surface, (*p["magic_shine"], _NS_gornak._alpha(180 * hold)),
                (tip[0] - wr, tip[1] - wr // 3, wr * 2,
                 max(3, wr * 2 // 3)), 1)
            for i in range(5):
                ang = -1.9 + i * 0.62 + math.sin(progress * 9 + i) * 0.15
                d = 6 + hold * 12
                _NS_gornak._shard(
                    surface, tip[0] + math.cos(ang) * d,
                    tip[1] + math.sin(ang) * d, ang,
                    5 + int(hold * 5), 2, p["magic_light"], a,
                    core=p["magic_core"])

    # ==================================================================
    # SKILL Q - MANA BREAK (world-space, 3 fase)
    # Telegraph & charge di ujung bilah -> bolt panah -> impact retak.
    # ==================================================================
    def _draw_manabreak_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH: serpihan mana disedot MASUK ke ujung bilah."""
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.34:
            return
        t = progress / 0.34
        fs = _NS_gornak._fx_scale(boss)
        tx, ty = _NS_gornak._tip_screen(boss, x, y)
        r = int((4 + t * 9) * fs)
        # Halo bertingkat (murah: lingkaran penuh mengecil)
        for k in range(r + 3, 0, -1):
            a = _NS_gornak._alpha(200 * (r + 3 - k) / (r + 3) * (0.4 + t))
            _NS_gornak._aacircle(surface, (*p["magic_dark"], a), (tx, ty), k)
        for col, rr in (("magic_mid", r), ("magic_light", max(1, r - 2)),
                        ("magic_shine", max(1, r - 4))):
            _NS_gornak._aacircle(surface, p[col], (tx, ty), rr)
        # Serpihan konvergen: terbang MASUK, bukan berputar-putar
        for i in range(7):
            ang = phase * 1.4 + i * math.tau / 7
            d = (26 - t * 18 + (i % 3) * 5) * fs
            sx = tx + math.cos(ang) * d
            sy = ty + math.sin(ang) * d * 0.9
            _NS_gornak._shard(surface, sx, sy, ang + math.pi,
                              int(7 * fs), max(1, int(2 * fs)),
                              p["magic_light"],
                              _NS_gornak._alpha(210 * (0.35 + t)),
                              core=p["magic_shine"])
        # Cincin pengunci + chevron ke arah target
        aim = _NS_gornak._target_position(boss, x, y)
        ang = math.atan2(aim[1] - ty, aim[0] - tx)
        for k in range(2):
            rr = int((18 - t * 10 + k * 7) * fs)
            _NS_gornak._dashed_ring(
                surface, tx, ty, rr, p["magic_light"],
                _NS_gornak._alpha(200 * (1 - t) * (1 - k * 0.25)),
                phase * 2 + k, segments=8, thick=2, span=0.55, squash=0.85)
        for k in range(3):
            d = (14 + k * 11) * fs * (1.0 - t * 0.4)
            _NS_gornak._chevron(
                surface, tx + math.cos(ang) * d, ty + math.sin(ang) * d,
                ang, int(7 * fs), p["magic_hot"],
                _NS_gornak._alpha(220 * (0.4 + t)), width=2)
        _NS_gornak._spark_star(
            surface, tx, ty, int((8 + t * 6) * fs), p["magic_hot"],
            _NS_gornak._alpha(210 * t), spikes=8, rot=phase * 3,
            core=p["magic_shine"])

    def _draw_manabreak_foreground(surface, boss, x, y, timer, phase):
        """PROYEKTIL v3: kepala panah kristal + after-image ter-stempel.

        Perubahan dari v2: bolt tidak lagi sekadar deret lingkaran yang
        makin kecil (terbaca seperti gelembung). Sekarang ada bentuk
        KEPALA yang berorientasi arah terbang, dua pecahan yang mengorbit
        spiral di belakangnya, dan after-image yang di-stempel pada jarak
        tetap (bukan garis mulus) - ciri khas pixel-art projectile.
        """
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress <= 0.30:
            return
        t = (progress - 0.30) / 0.70
        fs = _NS_gornak._fx_scale(boss)
        sx, sy = _NS_gornak._tip_screen(boss, x, y)
        tx, ty = _NS_gornak._target_position(boss, x, y)
        ang = math.atan2(ty - sy, tx - sx)
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        bx, by = int(sx + (tx - sx) * t), int(sy + (ty - sy) * t)

        # ── After-image: stempel serpihan pada jarak tetap di belakang
        for i in range(1, 8):
            tt = t - i * 0.052
            if tt <= 0:
                break
            px = sx + (tx - sx) * tt
            py = sy + (ty - sy) * tt
            a = _NS_gornak._alpha(215 - i * 26)
            ln = max(2, int((9 - i) * fs))
            _NS_gornak._shard(surface, px, py, ang, ln,
                              max(1, int((4 - i * 0.4) * fs)),
                              p["magic_dark"], a)
            _NS_gornak._shard(surface, px, py, ang, int(ln * 0.7),
                              max(1, int((2.6 - i * 0.28) * fs)),
                              p["magic_mid"], a, core=p["magic_light"])

        # ── Dua pecahan mengorbit spiral (memberi rasa "berputar cepat")
        for k in (0, 1):
            sp = phase * 7.0 + t * 26 + k * math.pi
            off = math.sin(sp) * 7 * fs
            fx2 = bx - ca * 8 * fs + nx * off
            fy2 = by - sa * 8 * fs + ny * off
            _NS_gornak._shard(surface, fx2, fy2, ang + math.cos(sp) * 0.8,
                              int(7 * fs), max(1, int(2 * fs)),
                              p["magic_hot"], 225, core=p["magic_core"])

        # ── Kepala bolt: 3 lapis nilai + glint berputar
        for col, ln, wd in (("magic_darkest", 19, 7), ("magic_mid", 16, 5),
                            ("magic_hot", 12, 3), ("magic_core", 7, 2)):
            _NS_gornak._shard(surface, bx, by, ang, int(ln * fs),
                              max(1, int(wd * fs)), p[col], 245)
        _NS_gornak._spark_star(surface, bx, by, int(10 * fs), p["magic_shine"],
                               230, spikes=6, rot=phase * 6 + t * 4,
                               core=p["white"])

        # ── Impact: kilat putih -> cincin patah -> retak -> debris
        if t > 0.84:
            st = (t - 0.84) / 0.16
            radius = int((11 + st * 28) * fs)
            a = _NS_gornak._alpha(245 * (1 - st))
            _NS_gornak._aacircle(surface, (*p["white"], a), (tx, ty),
                                 max(1, int(8 * fs * (1 - st))))
            _NS_gornak._dashed_ring(surface, tx, ty, radius + 2,
                                    p["magic_darkest"], a, st * 3,
                                    segments=9, thick=max(2, int(3 * fs)),
                                    span=0.62, squash=1.0)
            _NS_gornak._dashed_ring(surface, tx, ty, max(3, radius - 5),
                                    p["magic_hot"], a, -st * 4,
                                    segments=7, thick=2, span=0.5,
                                    squash=1.0)
            _NS_gornak._spark_star(
                surface, tx, ty, int(17 * fs * (1 - st)), p["magic_hot"], a,
                spikes=8, rot=st * 2, core=p["white"])
            for i in range(8):
                a2 = i * math.pi / 4 + st * 0.5
                _NS_gornak._jagged_crack(
                    surface, tx, ty, a2, int((18 + st * 16) * fs),
                    (p["magic_darkest"], p["magic_hot"]), a, i + 3, width=2)
                _NS_gornak._shard(
                    surface, tx + math.cos(a2) * radius * 0.8,
                    ty + math.sin(a2) * radius * 0.8, a2,
                    int(8 * fs * (1 - st)) + 2, max(1, int(2 * fs)),
                    p["magic_light"], a, core=p["magic_core"])

    # ==================================================================
    # SKILL W - BLINK (world-space departure / arrival)
    # ==================================================================
    def _draw_blink_ground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        gy = y + _NS_gornak.GROUND_DY
        if progress < 0.5:
            t = progress / 0.5
            r = int((10 + t * 15) * fs)
            a = _NS_gornak._alpha(240 * (1 - t))
        else:
            t = (progress - 0.5) / 0.5
            r = int((24 - t * 12) * fs)
            a = _NS_gornak._alpha(240 * t)
        if a <= 0:
            return
        _NS_gornak._ellipse(surface, (*p["magic_dark"], a),
                            (x - r - 3, gy - (r + 3) // 3, (r + 3) * 2,
                             max(3, (r + 3) // 2)), 1)
        _NS_gornak._ellipse(surface, (*p["magic_mid"], a),
                            (x - r, gy - r // 3, r * 2, max(3, r // 2)), 2)
        _NS_gornak._ellipse(surface, (*p["magic_hot"], a),
                            (x - r // 2, gy - r // 6, r, max(2, r // 4)), 2)
        _NS_gornak._dashed_ring(
            surface, x, gy, r + int(6 * fs), p["magic_light"], a,
            phase * 3, segments=9, thick=2, span=0.5, squash=0.42)
        if progress >= 0.5:
            r2 = int((24 + t * 14) * fs)
            a2 = _NS_gornak._alpha(200 * (1 - t))
            _NS_gornak._ellipse(surface, (*p["magic_shine"], a2),
                                (x - r2, gy - r2 // 3, r2 * 2,
                                 max(3, r2 // 2)), 1)
            _NS_gornak._spark_star(
                surface, x, gy - 6, int(12 * fs * (1 - t)), p["magic_hot"],
                a2, spikes=8, rot=t * 2, core=p["magic_shine"])
        for i in range(7):
            ang = phase * 2 + i * math.tau / 7
            _NS_gornak._shard(surface, x + math.cos(ang) * (r + 3),
                              gy + math.sin(ang) * max(1, r // 4),
                              -math.pi / 2, 4, 1, p["magic_shine"], a)

    # ==================================================================
    # SKILL E - COUNTERSPELL (AOE 100 px dunia)
    # Telegraph ring tepat 100 + kubah heksagon + rune orbit.
    # ==================================================================
    def _draw_counterspell_foreground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        grow = 1.0
        if progress < 0.16:
            grow = 0.55 + (progress / 0.16) * 0.45
        elif progress > 0.86:
            grow = 1.0 - (progress - 0.86) / 0.14 * 0.35
        fade = 1.0 - max(0.0, (progress - 0.9)) * 8
        a_main = _NS_gornak._alpha(225 * fade)

        # ── TELEGRAPH: ring jangkauan TEPAT 100 px dunia
        wr = _NS_gornak._ring_r(boss, 100)
        _NS_gornak._arcane_seal(surface, x, y, wr, phase,
                                _NS_gornak._alpha(235 * fade), fs,
                                nodes=7, star=3, spin=1.0)
        _NS_gornak._rune_orbit(
            surface, x, y,
            max(4, int(wr * (0.70 + 0.06 * math.sin(phase * 3)))),
            -phase * 0.9, _NS_gornak._alpha(175 * fade), fs, count=8)
        if progress < 0.28:
            # Segel mengunci: pecahan kristal jatuh ke dalam, bukan
            # lingkaran yang mengecil.
            conv = 1.0 - progress / 0.28
            for i in range(7):
                ang = i * math.tau / 7 + progress * 4
                d = wr * (0.30 + 0.72 * conv)
                _NS_gornak._shard(
                    surface, x + math.cos(ang) * d, y + math.sin(ang) * d,
                    ang + math.pi, int(11 * fs * conv + 3),
                    max(2, int(3 * fs)), p["magic_shine"],
                    _NS_gornak._alpha(215 * conv), core=p["white"])
        for i in range(4):
            ang = i * math.pi / 2 + phase * 0.4
            _NS_gornak._chevron(
                surface, x + math.cos(ang) * wr * 0.82,
                y + math.sin(ang) * wr * 0.82,
                ang + math.pi, int(10 * fs), p["magic_hot"], a_main, width=2)

        # ── AKTIVASI: kubah heksagon memeluk badan
        rx = int(_NS_gornak._s(24) * grow * max(1.0, fs * 0.55))
        ry = int(_NS_gornak._s(33) * grow * max(1.0, fs * 0.55))
        cx0, cy0 = int(x), int(y) - 3
        breath = math.sin(phase * 2.4) * 1.2 * fs
        pts = []
        for i in range(6):
            ang = -math.pi / 2 + i * math.tau / 6 + phase * 0.25
            pts.append((cx0 + int(math.cos(ang) * (rx + breath)),
                        cy0 + int(math.sin(ang) * (ry + breath))))
        x0 = min(q[0] for q in pts) - 4
        y0 = min(q[1] for q in pts) - 4
        w = max(q[0] for q in pts) - x0 + 8
        h = max(q[1] for q in pts) - y0 + 8
        fill = pygame.Surface((max(4, w), max(4, h)), pygame.SRCALPHA)
        sh = [(q[0] - x0, q[1] - y0) for q in pts]
        _NS_gornak._poly(fill, (*p["magic_darkest"],
                                _NS_gornak._alpha(64 * grow)), sh)
        _NS_gornak._poly(fill, (*p["magic_dark"],
                                _NS_gornak._alpha(72 * grow)),
                         sh[1:-1] + [sh[0]])
        surface.blit(fill, (x0, y0))
        for i in range(6):
            q, r2 = pts[i], pts[(i + 1) % 6]
            _NS_gornak._aaline(surface, (*p["magic_mid"], a_main), q, r2, 2)
            _NS_gornak._aaline(surface, (*p["magic_shine"], a_main), q, r2, 1)
            # Simpul heksagon = serpihan kristal, bukan bulatan
            na = math.atan2(q[1] - cy0, q[0] - cx0)
            _NS_gornak._shard(surface, q[0], q[1], na, 6, 3, p["magic_hot"],
                              a_main, core=p["white"])
        if progress < 0.20:
            _NS_gornak._spark_star(
                surface, x, y - 8, int(14 * fs * (1 - progress / 0.20)),
                p["magic_hot"], a_main, spikes=8, rot=progress * 5,
                core=p["white"])
        # ── STEADY: rune mote mengorbit tepat di ring 100
        for i in range(8):
            ang = phase * 1.3 + i * math.tau / 8
            mx = x + math.cos(ang) * wr
            my = y + math.sin(ang) * wr
            _NS_gornak._shard(surface, mx, my, ang + math.pi / 2,
                              int(5 * fs), max(1, int(2 * fs)),
                              p["magic_light"], a_main, core=p["magic_shine"])

    # ==================================================================
    # SKILL R - MANA VOID (AOE 180 px dunia di CASTER)
    # Telegraph 180 -> corong sedot -> implosi -> asap void.
    # ==================================================================
    def _draw_manavoid_ground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        wr = _NS_gornak._ring_r(boss, 180)
        gy = y + _NS_gornak.GROUND_DY
        a = _NS_gornak._alpha(220 * min(1.0, progress * 3))
        # Telegraph ring TEPAT 180 px dunia di caster (= AOE gameplay).
        _NS_gornak._arcane_seal(surface, x, y, wr, phase, a, fs,
                                nodes=9, star=2, spin=-1.0)
        # Kawah void di tanah: busur pecah, bukan elips penuh yang
        # menggelapkan seluruh badan.
        _NS_gornak._dashed_ring(
            surface, x, gy, int(wr * 0.52), p["magic_darkest"],
            _NS_gornak._alpha(a * 0.7), phase * 0.4, segments=6,
            thick=max(2, int(3 * fs)), span=0.52, squash=0.34)
        _NS_gornak._dashed_ring(
            surface, x, gy, int(wr * 0.34), p["magic_dark"],
            _NS_gornak._alpha(a * 0.55), -phase * 0.6, segments=3,
            thick=2, span=0.46, squash=0.34)
        if progress < 0.55:
            t = progress / 0.55
            for i in range(5):
                ang = i * math.tau / 5 + 0.2
                _NS_gornak._jagged_crack(
                    surface, x, gy, ang, int(wr * 0.38 * t),
                    (p["magic_darkest"], p["magic_hot"]),
                    _NS_gornak._alpha(190 * t), i + 5, width=2)
            for i in range(4):
                ang = i * math.pi / 2 + phase * 0.3
                _NS_gornak._chevron(
                    surface, x + math.cos(ang) * wr * 0.78,
                    y + math.sin(ang) * wr * 0.78,
                    ang + math.pi, int(12 * fs), p["magic_hot"],
                    _NS_gornak._alpha(210 * t), width=2)
            # Puing tanah tersedot ke pusat
            for i in range(7):
                ang = phase * 0.8 + i * math.tau / 7
                d = wr * (0.85 - t * 0.55) * (0.7 + 0.3 * ((i % 3) / 2.0))
                _NS_gornak._shard(
                    surface, x + math.cos(ang) * d,
                    gy + math.sin(ang) * d * 0.32, ang + math.pi,
                    int(8 * fs), max(1, int(2 * fs)), p["magic_mid"],
                    _NS_gornak._alpha(200 * t), core=p["magic_light"])

    def _draw_manavoid_foreground(surface, boss, x, y, timer, phase):
        p = _NS_gornak.PALETTE
        duration = _NS_gornak.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gornak._fx_scale(boss)
        action = "void"
        wr = _NS_gornak._ring_r(boss, 180)
        cx, cy = int(x), int(y) - 4          # inti void di CASTER
        aim = _NS_gornak._target_position(boss, x, y)

        if progress < 0.22:
            # AKTIVASI: pilar 3 lapis (tinggi di-clamp) + shockwave
            t = progress / 0.22
            a = _NS_gornak._alpha(240 * (1 - t * 0.25))
            ph = min(int(100 * fs), 240)
            for col, w, mul in (("magic_darkest", 18, 1.0),
                                ("magic_mid", 10, 0.85),
                                ("magic_shine", 4, 0.55)):
                ww = max(2, int(w * fs * (1.1 - t * 0.3)))
                hh = int(ph * mul)
                _NS_gornak._ellipse(surface, (*p[col], a),
                                    (cx - ww, cy - hh, ww * 2, hh + 8))
            _NS_gornak._spark_star(
                surface, cx, cy - int(20 * fs), int(18 * fs * (1 - t)),
                p["magic_hot"], a, spikes=8, rot=t * 3, core=p["white"])
            rr = int(wr * (0.25 + t * 0.75))
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (cx, cy), rr, 3)

        if progress < 0.50:
            t = progress / 0.5
            # Corong sedot: mana target -> dada; bilah jadi konduktor
            chest = _NS_gornak._local(boss, x, y, action, phase, 0.0,
                                      0, _NS_gornak.SHOULDER_Y + 4)
            for back in (False, True):
                grip = (_NS_gornak._back_grip_local(action, 0.0, phase) if back
                        else _NS_gornak._front_grip_local(action, 0.0, phase))
                hx, hy = _NS_gornak._local(boss, x, y, action, phase, 0.0,
                                           *grip)
                _NS_gornak._aaline(surface,
                                   (*p["magic_dark"],
                                    _NS_gornak._alpha(150 * t)),
                                   (hx, hy), (cx, cy), max(2, int(3 * fs)))
                _NS_gornak._aaline(surface,
                                   (*p["magic_mid"],
                                    _NS_gornak._alpha(200 * t)),
                                   (hx, hy), (cx, cy), max(1, int(2 * fs)))
            for i in range(5):
                tt = (phase * 0.7 + i / 5.0) % 1.0
                mx = int(aim[0] + (chest[0] - aim[0]) * tt)
                my = int(aim[1] + (chest[1] - aim[1]) * tt
                         - math.sin(tt * math.pi) * 7 * fs)
                aa = _NS_gornak._alpha(210 * (1 - abs(tt - 0.5) * 1.2) * t)
                if aa > 0:
                    ang = math.atan2(chest[1] - aim[1], chest[0] - aim[0])
                    _NS_gornak._shard(surface, mx, my, ang, int(6 * fs),
                                      max(1, int(2 * fs)), p["magic_light"],
                                      aa, core=p["magic_shine"])
            core = int((6 + t * 8) * fs)
            for r in range(core + 2, 0, -1):
                aa = _NS_gornak._alpha(235 * (core + 2 - r) / (core + 2))
                _NS_gornak._aacircle(surface, (*p["magic_darkest"], aa),
                                     (cx, cy), r)
            _NS_gornak._aacircle(surface, p["magic_mid"], (cx, cy), core)
            _NS_gornak._aacircle(surface, p["magic_hot"], (cx, cy),
                                 max(1, core - 3))
        elif progress < 0.68:
            # IMPLOSI
            t = (progress - 0.50) / 0.18
            intensity = math.sin(t * math.pi)
            r = int((22 + t * 30) * fs)
            a = _NS_gornak._alpha(240 * intensity)
            _NS_gornak._aacircle(surface, (*p["magic_darkest"], a), (cx, cy),
                                 r + 3, 4)
            _NS_gornak._aacircle(surface, (*p["magic_dark"], a), (cx, cy),
                                 r, 3)
            _NS_gornak._aacircle(surface, (*p["magic_mid"], a), (cx, cy),
                                 max(1, r - 6), 2)
            _NS_gornak._aacircle(surface, (*p["magic_shine"], a), (cx, cy),
                                 max(1, int(r * 0.35)))
            _NS_gornak._spark_star(
                surface, cx, cy, int(20 * fs * intensity), p["magic_hot"], a,
                spikes=10, rot=t * 4, core=p["white"])
            for i in range(12):
                ang = i * math.tau / 12
                d = min(wr, r + 8 * fs)
                _NS_gornak._shard(surface, cx + math.cos(ang) * d * 0.85,
                                  cy + math.sin(ang) * d * 0.72, ang,
                                  int(10 * fs * intensity) + 2,
                                  max(1, int(2 * fs)), p["magic_hot"], a,
                                  core=p["magic_core"])
        else:
            # SISA: asap void naik
            t = (progress - 0.68) / 0.32
            for i in range(10):
                tt = (phase * 0.5 + i * 0.1) % 1.0
                px = cx + int(math.sin(phase * 1.4 + i) * (14 + i) * fs)
                py = cy - int(tt * 30 * fs)
                a = _NS_gornak._alpha(200 * (1 - t) * (1 - tt))
                if a > 0:
                    _NS_gornak._aacircle(surface, (*p["magic_dark"], a),
                                         (px, py), max(1, int(3 * fs)))
                    _NS_gornak._aacircle(surface, (*p["magic_mid"], a),
                                         (px, py), max(1, int(2 * fs)))
                    _NS_gornak._rect(surface, (*p["magic_shine"], a),
                                     (px, py, 1, 1))
        # Rim violet di badan (badan tetap subjek)
        rim = _NS_gornak._alpha(110 * min(1.0, progress * 3))
        rw = int(_NS_gornak._s(15) * max(1.0, fs * 0.5))
        rh = int(_NS_gornak._s(21) * max(1.0, fs * 0.5))
        _NS_gornak._ellipse(surface, (*p["magic_light"], rim),
                            (int(x) - rw, int(y) - rh - _NS_gornak.LIFT,
                             rw * 2, rh * 2 + _NS_gornak._s(2)), 1)


# ====================================================================
# MORGATH (ARC WARDEN) - Mini Boss
# ====================================================================
import math
import pygame


class _NS_morgath:
    """Namespace morgath - Arc Warden mini boss (ranged lightning caster).

    PIXEL MASTERWORK V2 + SKILL FX V2.1 (standar Thorne v2 / Gornak v2):

    * SATU bone rig 2D berlapis, ~1.5x di resolusi native. Ukuran arena
      otomatis ternormalisasi pipeline hero (heroes/__init__.py) - yang
      naik adalah KEPADATAN detail, bukan ukuran layar. Jalur mini boss
      (tanpa _render_scale) di-fit ke paritas keluarga lewat BOSS_FIT
      supaya hierarki boss (abaddon > gornak > morgath) tetap terkunci.
    * Disiplin pixel-art: ramp 4-5 band hue-shift, selout sisi bayangan,
      siluet bergerigi (hem cape/skirt via _tuft_points), specular
      cluster 1-2 px, dither band 50%, key light kiri-atas.
    * Anatomi baru: hood berlipat + orb kristal 5-band + shard orbit +
      antena arc; cuirass + pauldron rivet + gorget; grimoire di sabuk;
      SENJATA KHAS: arc staff "Tempus" tertanam (finial kristal melayang).
    * Animasi: foot solver, cape/staff/tassel inertia, idle hidup,
      serang multi-keyframe dengan frame IMPACT + smear berlapis.
    * Skill Q/W/E/R world-space lewat _fx_scale (1/_render_scale, cap
      2.6): 3 fase (telegraph / aktivasi / steady), E = 90 px dunia,
      R clone = +/-60 px dunia, W pool di target, Q jalur ke target.
    * Aura/mist/bayangan/dome di-cache (_static); FX di-clamp ke canvas.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _STATIC_SURFACES = {}

    # ── SKALA BADAN ───────────────────────────────────────────────
    # Koordinat lokal x1.5 dari rig lama. SCALE = px native per unit
    # lokal; SATU skala untuk semua jalur (boss 1x, lane hero native,
    # portrait) - sama seperti Thorne/Gornak v2. heroes/__init__.py
    # mengukur jalur boss lalu menormalkan lane, jadi yang dikunci di
    # sini adalah UKURAN ARENA: badan padat ~103 px, di bawah gornak
    # 119 (kontrak keluarga gornak >= 1.05x morgath) dan jauh di atas
    # rig v1 (~55 px).
    SCALE = 0.74
    K_BOSS = 0.74     # kompatibilitas nama: jalur boss = skala penuh
    # LIFT = jarak dunia (px) jangkar -> badan ke bawah, supaya
    # wajah (orb) tidak tertutup HP bar boss (y-r-15..y-r-7).
    LIFT = 4
    # Hem jubah dalam RUANG LOKAL; garis tanah dunia diturunkan dari
    # sini supaya bayangan/rune/hem tidak pernah saling lepas.
    FEET_DY = 60
    GROUND_DY = int(round(FEET_DY * K_BOSS)) - LIFT        # = 42

    # Buffer rig native (dibatasi extents semua pose + margin 4 px;
    # dikunci tools/test_morgath_masterwork.py + audit).
    RIG_W, RIG_H = 154, 117
    RIG_OX, RIG_OY = 77, 68

    # Bidang acuan cahaya TETAP (arah lampu tidak boleh bergeser antar
    # pose = lampu berkedip; kotak tetap juga menjaga cache gradien).
    GRAD_BOX = (RIG_OX - 30, RIG_OY - 47, 62, 90)

    # Durasi visual skill (frame) - mengikuti active_skill_timer yang
    # diisi base_boss.py & hero_skills/_bundle.py (q=50 w=40 e=90 r=60).
    SKILL_DUR = {"q": 50, "w": 40, "e": 90, "r": 60}

    # Sendi dalam RUANG LOKAL (y=0 jangkar, + ke bawah).
    WAIST_Y = -12
    SHOULDER_Y = -33
    SHOULDER_FRONT = (15, SHOULDER_Y)
    SHOULDER_BACK = (-16.5, SHOULDER_Y - 1.5)
    ORB_CENTER = (3, -46.5)
    ORB_R = 13.5
    CROWN_Y = -66

    # Muzzle beam = telapak cast di puncak thrust (beam lahir dari
    # TELAPAK, bukan angka lepas - dikunci test).
    MOR_MUZZLE = (40.5, -22.5)

    # Titik tancap arc staff (kaki staff menapak di tanah).
    STAFF_BASE = (-22, 60)

    # Penanda "render ke canvas hero" (lane) + skala aktif + skill
    # aktif. Dipasang per-frame oleh draw_morgath.
    class _MOR_LANE:
        v = False

    class _MOR_K:
        v = 0.74          # = SCALE: satu skala untuk semua jalur

    class _MOR_SKILL:
        v = None

    PALETTE = {
        # Robe / cloak (dark purple, hue-shift ke biru-violet di bayangan)
        "robe_darkest": (10, 6, 22),
        "robe_dark": (28, 18, 50),
        "robe_mid": (56, 38, 94),
        "robe_light": (98, 70, 150),
        "robe_edge": (152, 112, 204),

        # Armor plating (dark blue-steel, highlight dingin)
        "armor_darkest": (7, 11, 24),
        "armor_dark": (24, 38, 62),
        "armor_mid": (54, 82, 116),
        "armor_light": (106, 144, 184),
        "armor_shine": (178, 208, 238),

        # Gold trim (hue-shift: bayangan cokelat, highlight hangat)
        "gold_dark": (72, 52, 18),
        "gold_mid": (158, 122, 52),
        "gold_light": (228, 192, 108),
        "gold_shine": (255, 234, 168),

        # Crystal orb (bright cyan-blue, material utama sihir)
        "orb_darkest": (4, 14, 38),
        "orb_dark": (18, 52, 124),
        "orb_mid": (58, 126, 214),
        "orb_light": (128, 196, 250),
        "orb_hot": (198, 232, 254),
        "orb_shine": (240, 250, 255),

        # Lightning/arc (electric blue-white)
        "arc_darkest": (13, 27, 74),
        "arc_dark": (38, 86, 184),
        "arc_mid": (88, 156, 236),
        "arc_light": (176, 216, 252),
        "arc_hot": (228, 244, 255),
        "arc_shine": (255, 255, 255),

        # Flux purple (accent W)
        "flux_darkest": (24, 7, 44),
        "flux_dark": (62, 24, 106),
        "flux_mid": (128, 58, 196),
        "flux_light": (188, 128, 238),
        "flux_hot": (224, 178, 255),

        # Skin (hands/face edges) - shadowed violet
        "skin_darkest": (32, 27, 50),
        "skin_dark": (72, 62, 96),
        "skin_mid": (126, 112, 156),
        "skin_light": (176, 162, 206),

        # Arc staff (dark wood + steel + crystal finial)
        "staff_dark": (34, 24, 44),
        "staff_mid": (72, 52, 86),
        "staff_light": (122, 96, 150),

        # Grimoire / leather
        "leather_dark": (40, 26, 34),
        "leather_mid": (84, 56, 66),
        "leather_light": (136, 100, 110),
        "page_light": (214, 200, 186),

        # Ground rune
        "rune_dark": (13, 23, 56),
        "rune_mid": (56, 104, 194),
        "rune_light": (146, 196, 252),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 2, 8),
        "white": (255, 255, 255),
    }

    # ================================================================
    # PRIMITIF HELPER (alpha aman lewat surface sementara)
    # ================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _mix(a, b, t):
        t = max(0.0, min(1.0, float(t)))
        return _NS_morgath._clamp((
            a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t))

    def _hash01(seed):
        """Pseudo-random deterministik 0..1 (aman untuk cache sprite)."""
        h = int(seed) * 2654435761 & 0xFFFFFFFF
        h ^= h >> 16
        return (h & 0xFFFF) / 65535.0

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morgath._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_morgath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy),
                                     radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morgath._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = max(1, int(width))
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 6
            h = abs(ey - sy) + width * 4 + 6
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), width)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_morgath._clamp(color)
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
        color = _NS_morgath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)

    def _rect(surface, color, rect):
        color = _NS_morgath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect)

    def _static(key, builder):
        """Ambil/bangun surface statis (alokasi hanya saat cache miss)."""
        surf = _NS_morgath._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_morgath._STATIC_SURFACES[key] = surf
        return surf

    def _dither_rows(surface, x0, x1, y0, rows, color, w=1, seed=0):
        """Pita dither 50%: baris titik selang-seling (klasik pixel-art)."""
        for r in range(rows):
            y = int(y0) + r
            for x in range(int(x0) + ((r + seed) % 2), int(x1), 2):
                _NS_morgath._rect(surface, color, (x, y, w, w))

    def _jagged_line(surface, color, start, end, jitter=4, segments=6,
                     width=2):
        """Garis petir zigzag deterministik (nama publik lama)."""
        color = _NS_morgath._clamp(color)
        prev = start
        for i in range(1, segments + 1):
            t = i / segments
            bx = int(start[0] + (end[0] - start[0]) * t)
            by = int(start[1] + (end[1] - start[1]) * t)
            if i < segments:
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = max(1.0, math.hypot(dx, dy))
                perp_x = -dy / length
                perp_y = dx / length
                jit = (math.sin(t * 12 + start[0]) - 0.5) * jitter * 2
                bx += int(perp_x * jit)
                by += int(perp_y * jit)
            pygame.draw.line(surface, color, prev, (bx, by), width)
            prev = (bx, by)

    # ------------------------------------------------------------------
    # FX helper primitives (standar Thorne v2.1 / Gornak v2)
    # ------------------------------------------------------------------
    def _fx_scale(boss):
        """Kompensasi efek world-space: 1/_render_scale, cap 2.6."""
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam cache."""
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _world_to_local(boss, x, y, wx, wy):
        """Titik DUNIA -> ruang gambar renderer (clamp ke canvas).

        Hero dirender ke canvas di pusat lalu di-scale _render_scale:
        1 px canvas = _render_scale px dunia. Boss asli (tanpa
        _render_scale) digambar langsung di dunia -> titik apa adanya.
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
            return _NS_morgath._world_to_local(boss, x, y,
                                               target.x, target.y)
        scale = getattr(boss, "_render_scale", None)
        if scale:
            rng = int(getattr(boss, "range", 130) or 130)
            half = max(120, int(rng / float(scale)) + 40)
            dist = min(250 / float(scale), half - 20)
        else:
            dist = 250
        return int(x + dist * getattr(boss, "direction", 1)), int(y)

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6,
                    rot=0.4, core=None):
        """Bintang spike selang-seling untuk impact/aktivasi."""
        if alpha <= 0 or size <= 0:
            return
        alpha = max(0, min(255, int(alpha)))
        for k in range(spikes):
            ang = rot + k * math.tau / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_morgath._aaline(surface, (*color, alpha),
                                (int(cx), int(cy)),
                                (int(cx + math.cos(ang) * ln),
                                 int(cy + math.sin(ang) * ln * .82)),
                                2 if k % 2 == 0 else 1)
        if core:
            _NS_morgath._aacircle(surface, (*core, alpha),
                                  (int(cx), int(cy)),
                                  max(1, int(size * .28)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Panah telegraph '>' menghadap arah ``ang``."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px_, py_ = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for side in (-1, 1):
            _NS_morgath._aaline(
                surface, (*color, max(0, min(255, int(alpha)))),
                (int(cx + px_ * side * size * .55 - ca * size * .5),
                 int(cy + py_ * side * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin rune putus-putus yang berputar (marker AOE)."""
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
            _NS_morgath._aaline(surface, (*color, alpha), p0, p1, thick)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah zigzag deterministik dengan seam menyala."""
        if alpha <= 0 or length <= 0:
            return
        x0, y0, a = float(cx), float(cy), float(ang)
        pts = [(x0, y0)]
        for i in range(4):
            a += (_NS_morgath._hash01(seed * 17 + i * 31) - .5) * .75
            seg = length / 4.0
            x0 += math.cos(a) * seg
            y0 += math.sin(a) * seg * .55
            pts.append((x0, y0))
        alpha = max(0, min(255, int(alpha)))
        for i in range(len(pts) - 1):
            _NS_morgath._aaline(surface, (*colors[0], alpha),
                                pts[i], pts[i + 1], width + 2)
            _NS_morgath._aaline(surface, (*colors[1], alpha),
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
                             _NS_morgath._hash01(seed + i * 31 + j * 7))
                out.append((px_ + nx_ * d, py_ + ny_ * d))
            out.append((bx, by))
        return out



    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morgath(surface, boss, x, y):
        """Entry point untuk Boss.draw() sekaligus heroes.render_hero()."""
        # Beam-only pass (hero): body sudah di-blit ter-scale oleh
        # heroes/__init__.py; di sini hanya beam yang digambar, pada
        # koordinat & skala dunia = identik dengan versi mini boss.
        if getattr(boss, "_beam_pass_only", False):
            _NS_morgath._draw_mor_beam_pass(surface, boss, x, y)
            return

        # Jalur hero (lane): heroes/__init__ men-set _render_scale, dan
        # _finish_hd_sprite sudah menambah rim/terminator -> pass cahaya
        # di _draw_mor_rig_at dilewati (supaya tidak dobel).
        _NS_morgath._MOR_LANE.v = hasattr(boss, "_render_scale")
        _NS_morgath._MOR_K.v = _NS_morgath.SCALE
        _NS_morgath._MOR_SKILL.v = getattr(boss, "active_skill", None)
        _NS_morgath._update_mor_attack_anim(boss)
        action, pulse, ap = _NS_morgath._resolve_mor_pose(
            boss, _NS_morgath._detect_moving(boss))
        boss._mor_pose_action = action
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = _NS_morgath._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                          / 8.0))

        # ── Latar. Dibuang total saat portrait supaya auto-crop Hero
        #    Shop terisi wajah & material (orb), bukan lingkaran efek.
        if not portrait:
            _NS_morgath._draw_arc_aura(surface, x, y, pulse)
            gy = _NS_morgath._ground_dy()
            _NS_morgath._draw_ground_rune(surface, x, y + gy,
                                          pulse, active_skill)
            if active_skill == "q":
                _NS_morgath._draw_sparkwraith_ground(surface, boss, x, y,
                                                     skill_timer, pulse)
            elif active_skill == "w":
                _NS_morgath._draw_flux_ground(surface, boss, x, y,
                                              skill_timer, pulse)
            elif active_skill == "e":
                _NS_morgath._draw_magneticfield_ground(surface, boss, x, y,
                                                       skill_timer, pulse)
            elif active_skill == "r":
                _NS_morgath._draw_tempest_ground(surface, boss, x, y,
                                                 skill_timer, pulse)
            # AKTIVASI: gelombang kejut + bintang saat skill dilepas
            _NS_morgath._draw_skill_activation(surface, boss, x, y,
                                               active_skill, skill_timer,
                                               pulse)

        # ── Karakter (SATU rig masterwork; hem dipatok di garis tanah)
        if not portrait:
            _NS_morgath._draw_shadow(surface, x, y + _NS_morgath._ground_dy())
        _NS_morgath._draw_mor_rig_at(surface, x, y, facing, pulse, action,
                                     ap, portrait, flash)

        # Beam petir lahir dari telapak cast (MOR_MUZZLE). Skip saat beam
        # digambar terpisah langsung di layar skala 1.0 (heroes/__init__).
        if action == "attack" and not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(
                surface, boss, x, y, _NS_morgath._mor_progress(boss))

        # Tempest Double clones
        if active_skill == "r":
            _NS_morgath._draw_tempest_clone(surface, boss, x, y,
                                            skill_timer, pulse)

        # Foreground FX
        if active_skill == "q":
            _NS_morgath._draw_sparkwraith_foreground(surface, boss, x, y,
                                                     skill_timer, pulse)
        elif active_skill == "w":
            _NS_morgath._draw_flux_foreground(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "e":
            _NS_morgath._draw_magneticfield_foreground(surface, boss, x, y,
                                                       skill_timer, pulse)
        elif active_skill == "r":
            _NS_morgath._draw_tempest_foreground(surface, boss, x, y,
                                                 skill_timer, pulse)

    def _ground_dy():
        """Offset garis tanah pada ruang gambar aktif (canvas/world)."""
        k = _NS_morgath._MOR_K.v
        return int(round(_NS_morgath.FEET_DY * k
                         - _NS_morgath.LIFT * k / _NS_morgath.K_BOSS))

    def _lift_now():
        return _NS_morgath.LIFT * _NS_morgath._MOR_K.v / _NS_morgath.K_BOSS

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mor_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mor_previous_timer", 0))
        active = bool(getattr(boss, "_mor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mor_attack_active = True
            boss._mor_attack_frame = 0
            # Kunci arah + posisi target saat serangan dimulai (beam
            # terbang lurus ke titik yang SAMA selama animasi).
            boss._mor_attack_dir = int(getattr(boss, "direction", 1))
            _t = getattr(boss, "target", None)
            if _t is not None and getattr(_t, "alive", True):
                boss._mor_attack_target = (
                    int(_t.x) - int(getattr(boss, "x", 0)),
                    int(_t.y) - int(getattr(boss, "y", 0)))
            else:
                tx, ty = _NS_morgath._target_position(
                    boss, getattr(boss, "x", 0), getattr(boss, "y", 0))
                boss._mor_attack_target = (
                    int(tx) - int(getattr(boss, "x", 0)),
                    int(ty) - int(getattr(boss, "y", 0)))
            active = True
        elif active and timer > 0:
            boss._mor_attack_frame = int(getattr(boss, "_mor_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mor_attack_active = False
            boss._mor_attack_frame = 0
            active = False

        boss._mor_previous_timer = timer
        boss._mor_attack_progress = (
            min(1.0, getattr(boss, "_mor_attack_frame", 0)
                / max(1, cooldown - 1)) if active else 0.0)

    def _detect_moving(boss):
        if not hasattr(boss, "_mor_last_x"):
            boss._mor_last_x = boss.x
            boss._mor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mor_last_x)
        dy = abs(boss.y - boss._mor_last_y)
        boss._mor_last_x = boss.x
        boss._mor_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _mor_progress(boss):
        # LIVE dari attack_timer (bukan counter frame yang cuma naik
        # saat renderer dipanggil) - beam live tetap mulus 60fps.
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mor_attack_active", False):
            return max(0.0, min(1.0, (cd - 1 - t)
                                  / max(1.0, float(cd - 1))))
        return 0.0

    def _mor_attack_curve(ap):
        """Progres mentah 0..1 -> waktu pose 0..1, MONOTON naik.

        Sama seperti kurva Gornak: anticipation jelas, HOLD di impact,
        follow-through yang tidak ditarik balik. 0.35 = puncak charge,
        0.55 = beam mulai mengalir (pose 0.77, telapak sudah di muzzle).
        """
        if ap <= 0.0:
            return 0.0
        if ap < 0.45:                       # charge: tarik bahu, diperlambat
            t = ap / 0.45
            return 0.35 * (t ** 0.7)
        if ap < 0.62:                       # thrust: sangat cepat
            t = (ap - 0.45) / 0.17
            return 0.35 + 0.55 * (t ** 0.5)
        if ap < 0.80:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.62) / 0.18
            return 0.90 + 0.06 * t
        t = (ap - 0.80) / 0.20              # release -> siap
        return 0.96 + 0.04 * (t ** 0.8)

    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose.

        Keyframe: (progress, bob, lean, hand_x, hand_y, flare, tremble)
          0.00  rest      : tangan di sisi badan
          0.14  wind-up   : badan turun, tangan tarik belakang
          0.35  tension   : gemetar 1 px, node telapak charge penuh
          0.62  thrust    : tangan terdorong tercepat (smear aktif)
          0.90  IMPACT    : HOLD di muzzle (burst bintang di FX)
          0.96  release   : follow-through
          1.00  recover   : kembali istirahat
        """
        keys = (
            (0.00, 0, 0.0, 22.5, -10.5, 1.00, 0),
            (0.14, 3, -3.0, 16.5, -16.5, 1.00, 0),
            (0.35, 4, -4.5, 10.5, -19.5, 1.15, 1),
            (0.62, -1, 2.5, 34.5, -21.0, 1.25, 0),
            (0.90, 2, 4.5, 40.5, -22.5, 1.30, 0),
            (0.96, 1, 2.0, 40.5, -22.5, 1.15, 0),
            (1.00, 0, 0.0, 22.5, -10.5, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)          # smoothstep
                vals = tuple(a + (b - a) * t
                             for a, b in zip(k0[1:6], k1[1:6]))
                flare = k0[5] + (k1[5] - k0[5]) * t
                tremble = 1 if (k0[6] and t < 0.9) else 0
                return {"bob": int(round(vals[0])), "lean": vals[1],
                        "hand": (vals[2], vals[3]),
                        "flare": flare, "tremble": tremble}
        return {"bob": 0, "lean": 0.0, "hand": (22.5, -10.5),
                "flare": 1.0, "tremble": 0}

    def _resolve_mor_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN jangkar FX agar sinkron."""
        skill = getattr(boss, "active_skill", None)
        if skill == "q":
            action = "point"
        elif skill == "w":
            action = "channel"
        elif skill == "e":
            action = "erect"
        elif skill == "r":
            action = "ascend"
        elif (getattr(boss, "_mor_attack_active", False)
              or getattr(boss, "timer", 0) >
              getattr(boss, "attack_cooldown", 40) - 15):
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 2.0
        ap = 0.0
        if action == "attack":
            ap = _NS_morgath._mor_attack_curve(_NS_morgath._mor_progress(boss))
        return action, phase, ap

    def _cast_hand_local(action, ap, phase):
        """Telapak tangan depan (pe cast) dalam ruang lokal."""
        if action == "attack":
            pose = _NS_morgath._attack_pose(ap)
            return pose["hand"]
        bob = math.sin(phase * 0.9)
        if action == "point":                    # Q: menunjuk, summon wraith
            return (33.0, -39.0 + bob)
        if action == "channel":                  # W: kedua tangan menyalurkan
            return (22.5, -4.5 + bob)
        if action == "erect":                    # E: merentang mendirikan field
            return (30.0, 1.5)
        if action == "ascend":                   # R: mengangkat memanggil double
            return (16.5, -48.0)
        if action == "walk":
            return (19.5 + math.sin(phase * 2.0) * 3.0, -10.5)
        return (22.5, -10.5 + bob)               # idle: tangan di sisi badan

    def _back_hand_local(action, ap, phase):
        bob = math.sin(phase * 0.9 + 0.6)
        if action == "attack":
            return (-25.5, -4.5)
        if action == "channel":
            return (-22.5, -4.5 + bob)
        if action == "erect":
            return (-30.0, 1.5)
        if action == "ascend":
            return (-18.0, -46.5)
        if action == "walk":
            return (-19.5 - math.sin(phase * 2.0) * 3.0, -7.5)
        return (-22.5, -7.5 + bob)

    def _mor_elbow(a, b, bend):
        """Sendi siku: titik tengah digeser tegak-lurus sepanjang `bend`."""
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(1.0, math.hypot(dx, dy))
        return (mx - dy / length * bend, my + dx / length * bend)

    def _mor_shift(action, phase, ap):
        """(lean_x, root_y) - lean geser badan atas; root = napas pada
        bagian ATAS hem (hem/telapak tetap dipatok di garis tanah)."""
        bob = math.sin(phase * 0.9) * 2.0
        lean, root = 0.0, bob
        if action == "walk":
            root = -abs(math.sin(phase * 2.0)) * 2.4
            lean = math.sin(phase) * 1.2
        elif action == "attack":
            pose = _NS_morgath._attack_pose(ap)
            lean, root = pose["lean"], 0.0
        elif action == "ascend":
            root = -4.5 - bob
        return lean, root

    def _muzzle_offset_world():
        """(dx, dy) dunia dari jangkar ke muzzle (facing=+1).
        Beam selalu digambar di ruang dunia (skala 1.0)."""
        k = _NS_morgath.K_BOSS
        return (int(round(_NS_morgath.MOR_MUZZLE[0] * k)),
                int(round(-_NS_morgath.LIFT
                          + _NS_morgath.MOR_MUZZLE[1] * k)))

    def _skill_hand_world(boss, x, y, skill):
        """Posisi telapak cast DUNIA untuk stance skill (nama publik
        lama dipertahankan - FX canvas pakai _skill_hand_canvas)."""
        action = {"q": "point", "w": "channel", "e": "erect",
                  "r": "ascend"}.get(skill, "idle")
        phase = float(getattr(boss, "pulse", 0.0))
        hx, hy = _NS_morgath._cast_hand_local(action, 0.0, phase)
        f = getattr(boss, "direction", 1) or 1
        k = _NS_morgath.K_BOSS
        return (int(x + hx * f * k),
                int(y - _NS_morgath.LIFT + hy * k))

    def _skill_hand_canvas(boss, x, y, skill):
        """Posisi telapak cast pada ruang gambar aktif (canvas/world)."""
        action = {"q": "point", "w": "channel", "e": "erect",
                  "r": "ascend"}.get(skill, "idle")
        phase = float(getattr(boss, "pulse", 0.0))
        hx, hy = _NS_morgath._cast_hand_local(action, 0.0, phase)
        f = getattr(boss, "direction", 1) or 1
        k = _NS_morgath._MOR_K.v
        return (int(x + hx * f * k),
                int(y - _NS_morgath._lift_now() + hy * k))

    # ------------------------------------------------------------
    # POSE ROUTERS (wrapper tipis, kompatibel tool preview lama)
    # ------------------------------------------------------------
    def _draw_mor_idle(surface, boss, x, y):
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)), "idle", 0.0, False)

    def _draw_mor_walk(surface, boss, x, y):
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)) * 2.0, "walk", 0.0, False)

    def _draw_mor_attack(surface, boss, x, y):
        progress = _NS_morgath._mor_progress(boss)
        _NS_morgath._draw_mor_rig_at(
            surface, x, y, getattr(boss, "direction", 1) or 1,
            float(getattr(boss, "pulse", 0.0)), "attack",
            _NS_morgath._mor_attack_curve(progress), False)
        if not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(surface, boss, x, y,
                                                    progress)

    def _draw_mor_beam_pass(surface, boss, x, y):
        """Gambar HANYA beam pada koordinat dunia (skala 1.0)."""
        _NS_morgath._update_mor_attack_anim(boss)
        _NS_morgath._draw_lightning_projectile(
            surface, boss, x, y, _NS_morgath._mor_progress(boss))



    # ============================================================
    # RIG RENDER
    # ============================================================
    def _rig_buffer(facing, phase, action, ap=0.0, detail=False):
        """Buffer rig pada skala aktif (native/hero atau BOSS_FIT)."
        Dipakai _draw_mor_rig_at DAN _draw_tempest_clone."""
        k = _NS_morgath._MOR_K.v
        bw = max(2, int(round(_NS_morgath.RIG_W * k / _NS_morgath.SCALE)))
        bh = max(2, int(round(_NS_morgath.RIG_H * k / _NS_morgath.SCALE)))
        box = (int(round(_NS_morgath.RIG_OX * k / _NS_morgath.SCALE)),
               int(round(_NS_morgath.RIG_OY * k / _NS_morgath.SCALE)))
        buf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        _NS_morgath._draw_mor_rig(buf, box[0], box[1], facing, phase,
                                  action, ap, detail)
        return buf, box

    def _draw_mor_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0):
        """Rig -> buffer -> outline gelap 1 px -> satu blit (pola Gornak).

        Buffer ukurannya mengikuti skala aktif: native (hero/portrait)
        atau BOSS_FIT (mini boss 1x) - outline selalu tajam 1 px.
        Mode portrait Hero Shop memusatkan konten pada bbox-nya sendiri.
        """
        k = _NS_morgath._MOR_K.v
        buf, box = _NS_morgath._rig_buffer(facing, phase, action, ap,
                                           detail)
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 240, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
        # Pass cahaya hanya kalau sprite ini TIDAK dilewatkan ke
        # heroes._finish_hd_sprite (jalur lane sudah memberi
        # rim+terminator - dipasang dua kali jadi dobel).
        if _lighting is not None and not _NS_morgath._MOR_LANE.v:
            gb = tuple(int(round(v * k / _NS_morgath.SCALE))
                       for v in _NS_morgath.GRAD_BOX)
            _lighting.apply_to_rig(
                buf, rim_add=(30, 34, 52), shade_mul=160,
                box=gb if not detail else None)
        ox = int(x) - box[0]
        oy = int(y) - box[1]
        if detail:                       # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet (4 arah) - acuan keluarga masterwork.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        surface.blit(buf, (ox, oy))
        return buf

    def _draw_mor_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """Satu bone rig 2D berlapis: cape -> staff -> lengan belakang ->
        boots -> rok jubah -> torso -> sabuk+grimoire -> pauldron
        belakang -> kepala -> lengan cast -> pauldron depan -> FX.
        Semua titik lewat pt()/ptg() supaya ukuran cukup diubah dari
        SATU konstanta SCALE (atau K_BOSS di jalur mini boss)."""
        P = _NS_morgath.PALETTE
        k = _NS_morgath._MOR_K.v
        f = 1 if facing >= 0 else -1
        lean, root = _NS_morgath._mor_shift(action, phase, ap)
        lift = _NS_morgath._lift_now()
        tremble = 0.0
        if action == "attack":
            pose = _NS_morgath._attack_pose(ap)
            if pose["tremble"]:
                tremble = (_NS_morgath._hash01(int(phase * 13.7) % 1024)
                           - 0.5) * 1.2

        def pt(dx, dy):
            """Bagian yang ikut napas/lean/tremble (badan atas)."""
            return (int(cx + (dx * f + (lean + tremble) * f) * k),
                    int(cy - lift + (dy + root) * k))

        def ptg(dx, dy):
            """Bagian yang DIPATOK ke tanah (hem jubah, staff, telapak)."""
            return (int(cx + (dx * f + lean * f) * k),
                    int(cy - lift + dy * k))

        def _w(v):
            return max(1, int(round(v * k / _NS_morgath.SCALE)))

        # ---- bagian tubuh, belakang -> depan ----
        _NS_morgath._mor_draw_cape(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_staff(surface, pt, ptg, _w, f, phase,
                                    action, ap)
        _NS_morgath._mor_draw_arm_back(surface, pt, _w, f, phase, action,
                                       ap)
        if action == "walk":
            _NS_morgath._mor_draw_boots(surface, ptg, _w, f, phase)
        _NS_morgath._mor_draw_skirt(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_torso(surface, pt, _w, f, phase, action)
        _NS_morgath._mor_draw_belt(surface, ptg, _w, f, phase, action)
        _NS_morgath._mor_draw_pauldron(surface, pt, _w, f, phase,
                                       back=True)
        _NS_morgath._mor_draw_head(surface, pt, _w, f, phase, action, ap)
        _NS_morgath._mor_draw_arm_cast(surface, pt, _w, f, phase, action,
                                       ap)
        if action == "attack":
            _NS_morgath._draw_attack_smear(surface, pt, _w, f, ap)
            _NS_morgath._draw_attack_impact(surface, pt, _w, f, ap, phase)
        _NS_morgath._mor_draw_pauldron(surface, pt, _w, f, phase,
                                       back=False)
        _NS_morgath._draw_rig_ambient(surface, pt, _w, f, phase, action)
        if detail:
            _NS_morgath._mor_draw_masterwork_details(surface, pt, _w, f,
                                                     phase, action)

    # ------------------------------------------------------------
    # BAGIAN TUBUH (ruang lokal: y=0 jangkar, + ke bawah; +x = depan)
    # ------------------------------------------------------------
    def _mor_draw_cape(surface, ptg, _w, f, phase, action):
        """Cape besar mengalir di belakang; hem bergerigi (_tuft_points)
        + dither band + rim cahaya kiri-atas (secondary motion)."""
        P = _NS_morgath.PALETTE
        sway = math.sin(phase * 0.8) * 3.0
        if action == "walk":
            sway += math.sin(phase * 1.5) * 3.0
        elif action == "ascend":
            sway -= 4.0                       # jubah berkibar saat naik
        lag = math.sin(phase * 0.55 + 0.7) * 1.5     # overshoot lembut

        def cp(dx, dy):
            # sway membesar ke arah hem (bawah), nol di bahu
            grow = max(0.0, (dy + 33.0) / 93.0)
            return ptg(dx - f * (sway + lag) * grow, dy)

        # Spine hem (dasar) + siluet bergerigi deterministik
        hem = [(-46, 52), (-40, 57), (-31, 59.5), (-21, 60)]
        tuft = _NS_morgath._tuft_points(hem, depth=3.0, min_len=5.5,
                                        seed=7)
        panel = [(-13.5, -34.5), (13.5, -34.5), (19.5, -21),
                 (15, 0), (6, 24), (-2, 44), (-8, 56)]
        panel += tuft
        panel += [(-34, 56), (-45, 46), (-50, 30), (-52, 8),
                  (-49, -16), (-36, -30), (-24, -34.5)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [cp(x + 1, y + 1) for x, y in panel])
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [cp(x, y) for x, y in panel])
        # Bidang tengah
        mid = [(-9, -33), (11, -33), (15, -20), (12, -2),
               (5, 20), (-2, 40), (-9, 54), (-24, 52),
               (-33, 44), (-30, 10), (-22, -16)]
        _NS_morgath._poly(surface, P["robe_dark"],
                          [cp(x, y) for x, y in mid])
        # Panel cahaya kiri-atas (key light)
        _NS_morgath._poly(surface, P["robe_mid"],
                          [cp(x, y) for x, y in
                           [(-24, -34), (-36, -30), (-48, -14),
                            (-49, 6), (-44, 20), (-33, 26),
                            (-26, 10), (-20, -14)]])
        # Garis lipatan (3 nada gelap -> mid)
        for i, tone in enumerate(("robe_darkest", "robe_darkest",
                                  "robe_mid", "robe_mid")):
            bx = -30 + i * 9
            pygame.draw.line(surface, P[tone], cp(bx, -8 + i * 3),
                             cp(bx - 4, 46 - i), _w(1))
        # Dither band 50% di transisi panel tengah
        y0 = -6.0
        _NS_morgath._dither_rows(surface, cp(-14, y0)[0],
                                 cp(4, y0)[0], cp(0, y0)[1],
                                 2, P["robe_mid"], w=_w(1), seed=1)
        # Rim cahaya di siluet atas (sisi terang)
        for a, b in (((-13.5, -34.5), (-24, -34.5)),
                     ((-24, -34.5), (-36, -30)),
                     ((-36, -30), (-48, -14))):
            _NS_morgath._aaline(surface, P["robe_edge"], cp(*a), cp(*b),
                                _w(1))
        # Tepi depan tertangkap cahaya orb
        _NS_morgath._aaline(surface, P["robe_light"], cp(15, -30),
                            cp(17, -14), _w(1))
        _NS_morgath._aaline(surface, P["robe_mid"], cp(17, -14),
                            cp(11, 10), _w(1))

    def _mor_draw_staff(surface, pt, ptg, _w, f, phase, action, ap):
        """ARC STAFF 'Tempus' - senjata khas: shaft kayu-ungu 3-band
        tertanam di tanah, collar emas, finial bulan sabit + kristal
        melayang. Grip = tangan belakang (staff ikut pose = inertia)."""
        P = _NS_morgath.PALETTE
        hand = _NS_morgath._back_hand_local(action, ap, phase)
        gx, gy = pt(*hand)
        sway = math.sin(phase * 2.0) * 2.2 if action == "walk" else 0.0
        bx, by = ptg(_NS_morgath.STAFF_BASE[0] + sway,
                     _NS_morgath.STAFF_BASE[1])
        # Selout sisi bayangan lalu shaft 3-band
        _NS_morgath._aaline(surface, P["shadow_deep"],
                            (gx + _w(1), gy + _w(1)),
                            (bx + _w(1), by + _w(1)), _w(5.6))
        _NS_morgath._aaline(surface, P["staff_dark"], (gx, gy), (bx, by),
                            _w(4.6))
        _NS_morgath._aaline(surface, P["staff_mid"], (gx, gy), (bx, by),
                            _w(3.0))
        _NS_morgath._aaline(surface, P["staff_light"], (gx, gy),
                            (gx + (bx - gx) * 0.42, gy + (by - gy) * 0.42),
                            _w(1))
        # Serat kayu (2 goresan pendek)
        for tt in (0.30, 0.55):
            px_ = gx + (bx - gx) * tt
            py_ = gy + (by - gy) * tt
            _NS_morgath._aaline(surface, P["staff_dark"],
                                (int(px_ - _w(1.2)), int(py_)),
                                (int(px_ + _w(1.2)), int(py_ + _w(2))),
                                _w(1))
        # Collar emas
        for tt in (0.26, 0.60):
            px_ = gx + (bx - gx) * tt
            py_ = gy + (by - gy) * tt
            _NS_morgath._aaline(surface, P["gold_dark"],
                                (int(px_), int(py_)),
                                (int(px_ + _w(0.4)), int(py_ + _w(0.4))),
                                _w(5.4))
            _NS_morgath._aaline(surface, P["gold_mid"],
                                (int(px_), int(py_)),
                                (int(px_ + _w(0.4)), int(py_ + _w(0.4))),
                                _w(3.0))
            _NS_morgath._aaline(surface, P["gold_light"],
                                (int(px_ - _w(0.8)), int(py_)),
                                (int(px_ - _w(0.4)), int(py_ + _w(0.4))),
                                _w(1))
        # Sepatu kaki staff (flare kecil menapak)
        _NS_morgath._ellipse(surface, P["armor_dark"],
                             (bx - _w(4.5), by - _w(1.4), _w(9), _w(3)), 0)
        _NS_morgath._aaline(surface, P["armor_mid"],
                            (bx - _w(3.2), by - _w(0.4)),
                            (bx + _w(3.2), by - _w(0.4)), _w(1))
        # ── Finial: bulan sabit + kristal melayang ──
        bob = math.sin(phase * 1.6) * 1.4
        fx, fy = gx + _w(1.5), gy - _w(9.0) + _w(bob * 0.4)
        for r_, col, w_ in ((_w(4.6), P["gold_dark"], _w(1.6)),
                            (_w(3.4), P["gold_mid"], _w(1.4)),
                            (_w(2.2), P["gold_light"], _w(1))):
            _NS_morgath._aacircle(surface, col, (int(fx), int(fy)), r_, w_)
        # Kristal kecil (5 band, warna inti ikut skill)
        skill = _NS_morgath._MOR_SKILL.v
        core_col = {"w": P["flux_light"], "e": P["arc_hot"],
                    "r": P["white"], "q": P["arc_light"]}.get(
                        skill, P["orb_light"])
        cx_, cy_ = int(fx), int(fy - _w(4.6 + bob * 0.3))
        _NS_morgath._aacircle(surface, P["orb_dark"], (cx_, cy_), _w(2.8))
        _NS_morgath._aacircle(surface, P["orb_mid"], (cx_, cy_), _w(2.0))
        _NS_morgath._aacircle(surface, core_col, (cx_, cy_), _w(1.2))
        _NS_morgath._rect(surface, P["orb_shine"],
                          (cx_ - _w(1.0), cy_ - _w(1.0), _w(0.8), _w(0.8)))
        # Glow redup di sekitar kristal saat skill aktif
        if skill:
            _NS_morgath._aacircle(surface,
                                  (*core_col, 60), (cx_, cy_), _w(4.2))

    def _mor_morph_shoulder_chain(shoulder, hand, bend):
        elbow = _NS_morgath._mor_elbow(shoulder, hand, bend)
        return elbow

    def _mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                    base, edge, dim=False):
        """Lengan berjubah: dua segmen meruncing + cuff emas + elbow pad."""
        P = _NS_morgath.PALETTE
        sh, el, hd = pt(*shoulder), pt(*elbow), pt(*hand)

        def seg(a, b, w_a, w_b, color):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = max(1.0, math.hypot(dx, dy))
            px, py = -dy / L, dx / L
            pts = [(a[0] + px * w_a, a[1] + py * w_a),
                   (b[0] + px * w_b, b[1] + py * w_b),
                   (b[0] - px * w_b, b[1] - py * w_b),
                   (a[0] - px * w_a, a[1] - py * w_a)]
            _NS_morgath._poly(surface, color,
                              [(int(qx), int(qy)) for qx, qy in pts])

        if not dim:
            seg((sh[0] + 1, sh[1] + 1), (el[0] + 1, el[1] + 1),
                _w(4.6), _w(3.8), P["shadow_deep"])
        seg(sh, el, _w(4.4), _w(3.6), base)
        seg(el, hd, _w(3.6), _w(2.9), base)
        # Garis tepi terang di sisi atas lengan
        _NS_morgath._aaline(surface, edge, sh, hd, _w(1))
        # Elbow pad (lingkaran kecil armor)
        ep = pt(*elbow)
        _NS_morgath._aacircle(surface, P["armor_dark"], ep, _w(2.2))
        _NS_morgath._aacircle(surface, P["armor_mid"], ep, _w(1.4))
        # Manset emas di pergelangan
        ex, ey = el[0] + (hd[0] - el[0]) * 0.8, el[1] + (hd[1] - el[1]) * 0.8
        wx, wy = el[0] + (hd[0] - el[0]) * 0.97, el[1] + (hd[1] - el[1]) * 0.97
        _NS_morgath._aaline(surface, P["gold_dark"],
                            (int(ex), int(ey)), (int(wx), int(wy)), _w(4.4))
        _NS_morgath._aaline(surface, P["gold_mid"],
                            (int(ex), int(ey)), (int(wx), int(wy)), _w(2.6))

    def _mor_draw_arm_back(surface, pt, _w, f, phase, action, ap):
        """Lengan belakang: lebih redup; menggenggam arc staff."""
        P = _NS_morgath.PALETTE
        shoulder = _NS_morgath.SHOULDER_BACK
        hand = _NS_morgath._back_hand_local(action, ap, phase)
        elbow = _NS_morgath._mor_morph_shoulder_chain(shoulder, hand, -4.5)
        _NS_morgath._mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                                P["robe_darkest"], P["robe_dark"], dim=True)
        # Gauntlet grip + node redup
        hp = pt(*hand)
        _NS_morgath._aacircle(surface, P["armor_dark"], hp, _w(3.6))
        _NS_morgath._aacircle(surface, P["armor_mid"], hp, _w(2.6))
        _NS_morgath._rect(surface, P["armor_shine"],
                          (hp[0] - _w(0.8), hp[1] - _w(0.8),
                           _w(0.9), _w(0.9)))
        glow = 1.0 if action == "attack" else 0.5
        _NS_morgath._aacircle(surface, P["arc_dark"], hp,
                              _w(2.6 * glow), _w(1))
        if action == "attack" and ap < 0.4:
            _NS_morgath._aacircle(surface, P["arc_mid"], hp, _w(1.6),
                                  _w(1))

    def _mor_draw_boots(surface, ptg, _w, f, phase):
        """FOOT SOLVER: ujung sepatu mengintip dari hem saat walk;
        telapak terangkat bergantian + debu tapak + shadow kontak."""
        P = _NS_morgath.PALETTE
        FE = _NS_morgath.FEET_DY
        ph = phase * 2.0
        for side, sxo in ((0, 12.0), (1, -10.0)):
            s = math.sin(ph + side * math.pi)
            lift = max(0.0, s) * 4.2
            sx = sxo + math.cos(ph + side * math.pi) * 1.5
            toe = [(sx - 4.5, FE - 6 - lift), (sx + 6, FE - 6 - lift),
                   (sx + 7.5, FE - lift), (sx - 4.5, FE - lift)]
            _NS_morgath._poly(surface, P["armor_dark"],
                              [ptg(x, y) for x, y in toe])
            _NS_morgath._poly(surface, P["armor_mid"],
                              [ptg(x, y) for x, y in
                               [(sx - 2.5, FE - 5.5 - lift),
                                (sx + 5, FE - 5.5 - lift),
                                (sx + 6.5, FE - 1 - lift),
                                (sx - 2.5, FE - 1 - lift)]])
            _NS_morgath._aaline(surface, P["armor_shine"],
                                ptg(sx - 1.5, FE - 5 - lift),
                                ptg(sx + 3.5, FE - 5 - lift), _w(1))
            # Bayangan kontak (hanya saat menapak)
            if lift < 1.2:
                bpx, bpy = ptg(sx + 1, FE)
                _NS_morgath._ellipse(surface, (*P["shadow"], 90),
                                     (bpx - _w(5), bpy - _w(1),
                                      _w(10), _w(2)), 0)
            # Debu saat menapak (silang nol dari atas ke bawah)
            if 0.15 < (ph + side * math.pi) % math.tau < 0.55:
                dpx, dpy = ptg(sx - 1.5, FE - 1)
                _NS_morgath._aacircle(surface, (*P["robe_edge"], 90),
                                      (dpx - _w(1.5), dpy), _w(1.2))
                _NS_morgath._aacircle(surface, (*P["robe_edge"], 60),
                                      (dpx + _w(1.5), dpy - _w(1)), _w(1))



    def _mor_draw_skirt(surface, ptg, _w, f, phase, action):
        """Rok jubah A-line; hem bergigi/scallop DIPATOK di FEET_DY
        (tidak melayang) + tabard rune arc + pita hem emas."""
        P = _NS_morgath.PALETTE
        FE = _NS_morgath.FEET_DY
        hem_sway = math.sin(phase * 1.7) * 1.8 if action == "walk" else 0.0

        def sp(dx, dy):
            return ptg(dx + f * hem_sway * max(0.0, dy / FE), dy)

        # Hem bergerigi deterministik (siluet pixel-art)
        hem_spine = [(-26, 55), (-17, 60), (-8, 60), (0, 60),
                     (9, 60), (18, 60), (27, 56)]
        tuft = _NS_morgath._tuft_points(hem_spine, depth=2.6, min_len=5,
                                        seed=23)
        skirt = [(-15, -12), (15, -12), (22, 0), (28, 18), (32, 40)]
        skirt += tuft
        skirt += [(-28, 40), (-24, 14), (-15, -4)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [sp(x + 1, y + 1) for x, y in skirt])
        _NS_morgath._poly(surface, P["robe_mid"],
                          [sp(x, y) for x, y in skirt])
        # Bidang depan lebih terang (puncak jubah ke depan)
        front = [(-9, -11), (15, -11), (20, 2), (25, 20),
                 (28, 40), (24, 50), (16, 54), (8, 55), (0, 55),
                 (-6, 50), (-4, 26), (-7, 2)]
        _NS_morgath._poly(surface, P["robe_light"],
                          [sp(x, y) for x, y in front])
        # Sisi belakang masuk bayangan
        back = [(-9, -11), (-7, 2), (-4, 26), (-6, 50),
                (-16, 52), (-24, 48), (-27, 38), (-22, 14), (-14, -2)]
        _NS_morgath._poly(surface, P["robe_dark"],
                          [sp(x, y) for x, y in back])
        # Dither band 50% di panel belakang
        _NS_morgath._dither_rows(surface, sp(-20, 30)[0], sp(-6, 30)[0],
                                 sp(0, 30)[1], 2, P["robe_darkest"],
                                 w=_w(1), seed=2)
        # Lipatan vertikal meruncing ke pinggang
        for fx, tone in ((-3, "robe_mid"), (8, "robe_edge"),
                         (-14, "robe_darkest"), (18, "robe_mid")):
            _NS_morgath._aaline(surface, P[tone], sp(fx, -6),
                                sp(fx * 1.7, FE - 4), _w(1))
        # Tabard tengah: pita logam gelap + trim emas + rune arc
        tab = [(-6, -11), (6, -11), (7.5, 20), (4.5, 44), (0, 48),
               (-4.5, 44), (-7.5, 20)]
        _NS_morgath._poly(surface, P["armor_darkest"],
                          [sp(x, y) for x, y in tab])
        _NS_morgath._aaline(surface, P["gold_mid"], sp(-6, -10),
                            sp(-7.5, 20), _w(1))
        _NS_morgath._aaline(surface, P["gold_mid"], sp(-7.5, 20),
                            sp(-4.5, 44), _w(1))
        _NS_morgath._aaline(surface, P["gold_mid"], sp(6, -10),
                            sp(7.5, 20), _w(1))
        _NS_morgath._aaline(surface, P["gold_mid"], sp(7.5, 20),
                            sp(4.5, 44), _w(1))
        # Rune arc di tabard - warnanya ikut skill aktif (badan bereaksi)
        skill = _NS_morgath._MOR_SKILL.v
        rune_col = {"w": P["flux_light"], "e": P["arc_hot"],
                    "r": P["white"], "q": P["arc_light"]}.get(
                        skill, P["arc_mid"])
        rune = [(0, 18), (4.5, 24), (0, 30), (-4.5, 24)]
        _NS_morgath._poly(surface, P["arc_dark"], [sp(x, y) for x, y in rune])
        _NS_morgath._poly(surface, rune_col,
                          [sp(x * 0.7, 24 + (y - 24) * 0.7)
                           for x, y in rune])
        dot = sp(0, 24)
        _NS_morgath._rect(surface, P["arc_hot"],
                          (dot[0], dot[1], _w(1.2), _w(1.2)))
        # Pita hem emas redup + titik rune
        _NS_morgath._aaline(surface, P["gold_dark"], sp(-26, 52),
                            sp(27, 52), _w(1))
        for i in range(-3, 4):
            rx = i * 8
            _NS_morgath._rect(surface, P["rune_mid"],
                              (sp(rx, 52)[0], sp(rx, 52)[1],
                               _w(1), _w(1)))

    def _mor_draw_torso(surface, pt, _w, f, phase, action):
        """Cuirass dada: pelat baja-biru 5-band + trim emas + keystone
        arc menyala + dither band transisi ke skirt."""
        P = _NS_morgath.PALETTE
        breath = math.sin(phase * 0.9) * 1.1
        bw = 1.0 + breath * 0.05

        def tp(dx, dy):
            if dy > -34:                     # lebar napas hanya di dada
                dx *= bw
            return pt(dx, dy)

        chest = [(-15, -34), (15, -34), (18, -21), (14, -8),
                 (-14, -8), (-18, -21)]
        _NS_morgath._poly(surface, P["armor_dark"],
                          [tp(x + 1, y + 1) for x, y in chest])
        _NS_morgath._poly(surface, P["armor_mid"],
                          [tp(x, y) for x, y in chest])
        # Pelat dada kiri-kanan (nada terang menangkap cahaya atas-kiri)
        _NS_morgath._poly(surface, P["armor_light"],
                          [tp(x, y) for x, y in
                           [(-13.5, -33), (-1.5, -33), (-1.5, -15),
                            (-6, -18), (-12, -21)]])
        _NS_morgath._poly(surface, P["armor_light"],
                          [tp(x, y) for x, y in
                           [(1.5, -33), (13.5, -33), (12, -21),
                            (6, -18), (1.5, -15)]])
        # Specular cluster kiri-atas (1-2 px disengaja, bukan gradien)
        _NS_morgath._poly(surface, P["armor_shine"],
                          [tp(x, y) for x, y in
                           [(-10.5, -31.5), (-3, -31.5), (-3, -24),
                            (-9, -25.5)]])
        _NS_morgath._rect(surface, P["armor_shine"],
                          (tp(-10.5, -31.5)[0], tp(-10.5, -31.5)[1],
                           _w(1), _w(1)))
        _NS_morgath._poly(surface, P["armor_shine"],
                          [tp(x, y) for x, y in
                           [(3, -31.5), (10.5, -31.5), (9, -25.5),
                            (3, -24)]])
        # Garis tengah + jahitan pelat
        _NS_morgath._aaline(surface, P["armor_darkest"], tp(0, -33),
                            tp(0, -9), _w(1))
        _NS_morgath._aaline(surface, P["armor_darkest"], tp(-15, -19.5),
                            tp(15, -19.5), _w(1))
        # Dither band 50% di tepi bawah cuirass (transisi armor-skirt)
        _NS_morgath._dither_rows(surface, tp(-11, -10)[0],
                                 tp(11, -10)[0], tp(0, -10)[1],
                                 2, P["armor_darkest"], w=_w(1), seed=3)
        # Keystone arc di ulu hati (ikon faksi: sumber petir) - menyala
        # mengikuti skill aktif (badan bereaksi ke state skill)
        skill = _NS_morgath._MOR_SKILL.v
        key_col = {"w": P["flux_light"], "e": P["arc_hot"],
                   "r": P["white"], "q": P["arc_light"]}.get(
                       skill, P["arc_mid"])
        key = [(0, -28.5), (4.5, -24), (0, -18), (-4.5, -24)]
        _NS_morgath._poly(surface, P["arc_dark"],
                          [tp(x, y) for x, y in key])
        _NS_morgath._poly(surface, key_col,
                          [tp(x * 0.7, -24 + (y + 24) * 0.3)
                           for x, y in key])
        hot = tp(0, -24)
        _NS_morgath._rect(surface, P["arc_hot"],
                          (hot[0], hot[1], _w(1.2), _w(1.2)))
        if skill:
            _NS_morgath._aacircle(surface, (*key_col, 70),
                                  (hot[0], hot[1]), _w(4.5))
        # Kerah gorget: pita emas gelap di leher
        collar = [(-12, -35.5), (12, -35.5), (15, -33), (-15, -33)]
        _NS_morgath._poly(surface, P["gold_dark"],
                          [tp(x, y) for x, y in collar])
        _NS_morgath._aaline(surface, P["gold_light"], tp(-10.5, -34.5),
                            tp(10.5, -34.5), _w(1))

    def _mor_draw_belt(surface, ptg, _w, f, phase, action):
        """Sabuk pinggang + gesper + GRIMOIRE berantai di pinggul +
        dua rumbai (inertia/secondary motion)."""
        P = _NS_morgath.PALETTE
        band = [(-16.5, -13.5), (16.5, -13.5), (16.5, -6), (-16.5, -6)]
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [ptg(x, y) for x, y in band])
        _NS_morgath._aaline(surface, P["gold_mid"], ptg(-16.5, -12),
                            ptg(16.5, -12), _w(1))
        _NS_morgath._aaline(surface, P["gold_dark"], ptg(-16.5, -6),
                            ptg(16.5, -6), _w(1))
        # Gesper arc
        buck = [(0, -15), (4.5, -10.5), (0, -6), (-4.5, -10.5)]
        _NS_morgath._poly(surface, P["gold_mid"],
                          [ptg(x, y) for x, y in buck])
        c = ptg(0, -10.5)
        _NS_morgath._rect(surface, P["arc_light"],
                          (c[0], c[1], _w(1), _w(1)))
        # ── Grimoire: buku sihir berantai di pinggul belakang ──
        sway = math.sin(phase * 1.3) * 1.5
        if action == "walk":
            sway += math.sin(phase * 2.0) * 2.4
        bx0 = -22.0 + f * sway * 0.4
        # rantai dari sabuk
        _NS_morgath._aaline(surface, P["gold_dark"], ptg(-14, -6),
                            ptg(bx0, 2), _w(1))
        book = [(bx0 - 4, 1), (bx0 + 4, 1), (bx0 + 4.5, 8),
                (bx0, 12), (bx0 - 4.5, 8)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [ptg(x + 1, y + 1) for x, y in book])
        _NS_morgath._poly(surface, P["leather_dark"],
                          [ptg(x, y) for x, y in book])
        _NS_morgath._poly(surface, P["leather_mid"],
                          [ptg(x, y) for x, y in
                           [(bx0 - 2.5, 1.5), (bx0 + 2.5, 1.5),
                            (bx0 + 3, 7.5), (bx0, 10.5), (bx0 - 3, 7.5)]])
        # halaman + rune
        _NS_morgath._aaline(surface, P["page_light"], ptg(bx0, 1.5),
                            ptg(bx0, 10.5), _w(1))
        rp = ptg(bx0, 5)
        _NS_morgath._rect(surface, P["flux_light"],
                          (rp[0], rp[1], _w(1), _w(1)))
        # pojok logam + gesper buku
        _NS_morgath._rect(surface, P["gold_mid"],
                          (ptg(bx0 - 4, 1)[0], ptg(bx0 - 4, 1)[1],
                           _w(1.2), _w(1.2)))
        _NS_morgath._rect(surface, P["gold_mid"],
                          (ptg(bx0 + 2.8, 1)[0], ptg(bx0 + 2.8, 1)[1],
                           _w(1.2), _w(1.2)))
        # ── Rumbai: mengayun saat walk, menggantung saat idle ──
        for hx in (-9, 9):
            ex = hx + f * sway
            _NS_morgath._aaline(surface, P["gold_dark"], ptg(hx, -6),
                                ptg(ex, 18), _w(1))
            bead = ptg(ex, 19.5)
            _NS_morgath._aacircle(surface, P["gold_light"], bead,
                                  _w(2.1))
            dot = ptg(ex - 0.6, 18.9)
            _NS_morgath._rect(surface, P["gold_shine"],
                              (dot[0], dot[1], _w(1), _w(1)))

    def _mor_draw_pauldron(surface, pt, _w, f, phase, back=False):
        """Pelat bahu berlapis 3 + rivet + stud arc: sumber siluet
        'penuh' ke samping (selout sisi bayangan)."""
        P = _NS_morgath.PALETTE
        breath = math.sin(phase * 0.9) * 0.75
        if back:
            cx0, cy0 = -18.0, -36.0 + breath * 0.5
            sizes = ((9.75, 6.0), (11.25, 6.75))
            base, top = P["armor_dark"], P["armor_mid"]
            edge = P["armor_mid"]
        else:
            cx0, cy0 = 18.0, -37.5 + breath * 0.5
            sizes = ((10.5, 6.75), (12.75, 7.5), (14.25, 8.25))
            base, top = P["armor_mid"], P["armor_light"]
            edge = P["gold_mid"]
        for i, (rx, ry) in enumerate(sizes):
            ox = cx0 - i * 1.5
            oy = cy0 + i * 4.8
            plate = [(ox - rx, oy + ry * 0.4), (ox - rx * 0.7, oy - ry),
                     (ox + rx * 0.4, oy - ry * 0.9),
                     (ox + rx, oy - ry * 0.2),
                     (ox + rx * 0.8, oy + ry * 0.6), (ox, oy + ry)]
            _NS_morgath._poly(surface, P["armor_darkest"],
                              [pt(x + 1.2, y + 1.2) for x, y in plate])
            _NS_morgath._poly(surface, base if i else P["armor_darkest"],
                              [pt(x, y) for x, y in plate])
            _NS_morgath._poly(surface, top,
                              [pt(x, y) for x, y in
                               [(ox - rx * 0.6, oy - ry * 0.7),
                                (ox + rx * 0.2, oy - ry * 0.6),
                                (ox + rx * 0.5, oy - ry * 0.1),
                                (ox - rx * 0.4, oy - ry * 0.2)]])
            if i == len(sizes) - 1:
                _NS_morgath._aaline(surface, edge,
                                    pt(ox - rx + 1.5, oy + ry * 0.5),
                                    pt(ox + rx * 0.4, oy + ry * 0.7),
                                    _w(1))
        # Rivet (dither dots) + specular cluster
        for i in range(3):
            rx_ = cx0 - 3 + i * 3
            rp = pt(rx_, cy0 + 1.5 + i * 4.0)
            _NS_morgath._rect(surface, P["armor_shine"],
                              (rp[0], rp[1], _w(1), _w(1)))
        sp_ = pt(cx0 + (3.0 if not back else -1.5), cy0 - 3.0)
        _NS_morgath._rect(surface, P["armor_shine"],
                          (sp_[0], sp_[1], _w(1.2), _w(1.2)))
        # Paku arc kecil di pelat teratas
        stud = pt(cx0 + (3.0 if not back else -1.5), cy0 - 3.0)
        _NS_morgath._aacircle(surface, P["arc_light"], stud, _w(1.6))
        _NS_morgath._aacircle(surface, P["arc_shine"], stud, _w(0.8))

    def _mor_draw_head(surface, pt, _w, f, phase, action, ap):
        """Hood dalam + ORB KRISTAL 5-band (focal point PALING terang)
        + shard orbit + antena arc + mahkota diadem."""
        P = _NS_morgath.PALETTE
        ox, oy = _NS_morgath.ORB_CENTER
        hover = math.sin(phase * 1.3) * 0.75
        skill = _NS_morgath._MOR_SKILL.v
        core_col = {"w": P["flux_light"], "e": P["arc_hot"],
                    "r": P["white"], "q": P["arc_light"]}.get(
                        skill, P["orb_hot"])

        # --- Antena arc (sirip logam) dari sisi hood -----------------
        # Puncak dijaga supaya rel <= CY-62 (4 px LIFT + 0.8 skala):
        # tidak boleh menyentuh HP bar boss (y-r-15..y-r-7).
        fin_f = [(7.5, -61.5), (15, -72), (19.5, -71), (13.5, -60)]
        fin_b = [(-9, -61.5), (-15, -71), (-12, -72), (-4.5, -63)]
        _NS_morgath._poly(surface, P["armor_dark"],
                          [pt(x, y) for x, y in fin_b])
        _NS_morgath._poly(surface, P["armor_mid"],
                          [pt(x, y) for x, y in fin_f])
        _NS_morgath._rect(surface, P["armor_shine"],
                          (pt(10.5, -71)[0], pt(10.5, -71)[1],
                           _w(1.2), _w(1.2)))
        tip_f, tip_b = pt(17.25, -72.2), pt(-13.5, -72.0)
        _NS_morgath._rect(surface, core_col if skill else P["arc_light"],
                          (tip_f[0], tip_f[1], _w(1.8), _w(1.8)))
        _NS_morgath._rect(surface, P["arc_mid"],
                          (tip_b[0], tip_b[1], _w(1.5), _w(1.5)))
        # Tell charge: percikan melompat antar ujung antena
        if (action == "attack" and 0.02 < ap < 0.9) or skill:
            a = _NS_morgath._alpha(min(1.0, ap / 0.3) * 230) \
                if action == "attack" else 200
            _NS_morgath._jagged_line(surface, (*P["arc_hot"], a),
                                     tip_b, tip_f, jitter=_w(3), segments=4,
                                     width=_w(1.4))
            _NS_morgath._jagged_line(surface, (*P["arc_light"], a),
                                     pt(-13.5, -71.5),
                                     pt(17.25, -70.5),
                                     jitter=_w(2), segments=4, width=_w(1))

        # --- Hood luar ------------------------------------------------
        hood = [(-16.5, -34.5), (-21, -45), (-17, -57), (-9, -64),
                (0, -66), (9, -64), (17, -57), (20, -45),
                (16.5, -36), (9, -31.5), (-9, -31.5)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [pt(x + 1, y + 1) for x, y in hood])
        _NS_morgath._poly(surface, P["robe_dark"],
                          [pt(x, y) for x, y in hood])
        # Volume sisi terang (cahaya depan-atas / kiri-atas)
        _NS_morgath._poly(surface, P["robe_mid"],
                          [pt(x, y) for x, y in
                           [(-4.5, -63), (7.5, -61.5), (15, -54),
                            (18, -43.5), (13.5, -37.5), (6, -57)]])
        _NS_morgath._poly(surface, P["robe_light"],
                          [pt(x, y) for x, y in
                           [(0, -64.5), (7.5, -61.5), (12, -55.5),
                            (3, -58.5)]])
        # Lipatan hood
        for lx, tone in ((-12, "robe_darkest"), (-6, "robe_darkest"),
                         (12, "robe_edge")):
            _NS_morgath._aaline(surface, P[tone], pt(lx, -55.5),
                                pt(lx + f * 1.5, -39), _w(1))
        # Puncak hood menukik ke depan
        peak = [(-3, -66), (4.5, -67.5), (10.5, -63), (3, -64.5)]
        _NS_morgath._poly(surface, P["robe_mid"],
                          [pt(x, y) for x, y in peak])
        # Mahkota diadem emas di puncak
        _NS_morgath._aaline(surface, P["gold_dark"], pt(-12, -61.5),
                            pt(0, -66), _w(1.4))
        _NS_morgath._aaline(surface, P["gold_dark"], pt(0, -66),
                            pt(12, -61.5), _w(1.4))
        _NS_morgath._rect(surface, P["gold_shine"],
                          (pt(0, -66)[0], pt(0, -66)[1],
                           _w(1.2), _w(1.2)))

        # --- Lubang wajah: gelap pekat, jadi orb menonjol --------------
        hole = [(-9, -57), (9, -57), (12, -45), (9, -39),
                (-7.5, -40.5), (-10.5, -46.5)]
        _NS_morgath._poly(surface, P["shadow_deep"],
                          [pt(x, y) for x, y in hole])
        _NS_morgath._poly(surface, P["robe_darkest"],
                          [pt(x, y) for x, y in
                           [(-9, -57), (9, -57), (10.5, -51),
                            (-9, -52.5)]])

        # --- ORB kristal (nilai TERTINGGI di seluruh sprite) ----------
        oc = pt(ox, oy + hover)
        orad = _NS_morgath.ORB_R
        pulse = math.sin(phase * 2.2) * 0.5 + 0.5
        # Halo lembut (dua lingkaran alpha - murah)
        _NS_morgath._aacircle(surface, (*P["orb_dark"], 46), oc,
                              _w(orad + 7.5))
        _NS_morgath._aacircle(surface, (*P["orb_mid"], 60), oc,
                              _w(orad + 3))
        # Cangkang kristal (5 band)
        _NS_morgath._aacircle(surface, P["orb_dark"], oc, _w(orad))
        _NS_morgath._aacircle(surface, P["orb_mid"], oc, _w(orad - 2.2))
        # Bayangan kristal: pita gelap bawah-kanan (selout internal)
        low = (oc[0] + _w(2.2), oc[1] + _w(3.0))
        _NS_morgath._aacircle(surface, P["orb_darkest"], low,
                              _w(orad - 6.75))
        _NS_morgath._aacircle(surface, P["orb_dark"], low,
                              _w(orad - 9.0))
        # Facet lines (2 goresan halus, kristal bersegi)
        _NS_morgath._aaline(surface, P["orb_darkest"], oc,
                            (oc[0] - _w(7), oc[1] - _w(7)), _w(1))
        _NS_morgath._aaline(surface, P["orb_darkest"],
                            (oc[0] + _w(6), oc[1] + _w(6)),
                            (oc[0] + _w(3), oc[1] + _w(9)), _w(1))
        # Pusaran energi: dua busur orbit (ikuti phase)
        for i in range(2):
            ang = phase * 2.4 + i * math.pi
            sx = math.cos(ang) * (orad - 5.25)
            sy = math.sin(ang) * (orad - 5.25) * 0.55
            p1 = pt(ox + sx, oy + hover + sy)
            p2 = pt(ox + sx * 0.4, oy + hover + sy * 0.4 - 2.25)
            _NS_morgath._aaline(surface, P["orb_light"], p1, p2, _w(2))
        # Inti panas: denyut dengan phase (flare saat skill aktif)
        flare = 1.0 + (0.8 if skill else 0.0) * pulse
        core = (oc[0], oc[1] - _w(2.25))
        _NS_morgath._aacircle(surface, core_col, core,
                              _w(3.9 * flare + pulse))
        _NS_morgath._aacircle(surface, P["orb_shine"], core,
                              _w(2.1 + pulse * 0.75))
        # Glint kaca kiri-atas (specular cluster, bukan gradien)
        _NS_morgath._rect(surface, P["orb_shine"],
                          (oc[0] - _w(6), oc[1] - _w(6.75),
                           _w(1.8), _w(1.8)))
        _NS_morgath._rect(surface, P["white"],
                          (oc[0] - _w(4.5), oc[1] - _w(7.5),
                           _w(1), _w(1)))
        # Pecahan rune mengorbit orb (4 shard + glint)
        for i in range(4):
            ang = phase * 1.6 + i * (math.pi / 2.0)
            rx = math.cos(ang) * (orad + 6.75)
            ry = math.sin(ang) * (orad + 6.75) * 0.6
            shp = pt(ox + rx, oy + hover + ry)
            s = _w(1.8)
            _NS_morgath._poly(surface, P["arc_light"],
                              [(shp[0], shp[1] - s), (shp[0] + s, shp[1]),
                               (shp[0], shp[1] + s), (shp[0] - s, shp[1])])
            _NS_morgath._rect(surface, P["arc_shine"],
                              (shp[0] - _w(0.6), shp[1] - _w(0.6),
                               _w(0.9), _w(0.9)))
        # Ring flare tipis saat ultimate
        if skill == "r":
            _NS_morgath._dashed_ring(surface, oc[0], oc[1],
                                     _w(orad + 9), P["arc_hot"],
                                     180, phase * 3, segments=8,
                                     thick=_w(1.4), span=0.5)

        # --- Bibir hood menangkap cahaya orb ---------------------------
        _NS_morgath._aaline(surface, P["robe_light"], pt(-7.5, -40.5),
                            pt(9, -40.5), _w(1))
        _NS_morgath._aaline(surface, P["robe_edge"], pt(9, -40.5),
                            pt(12, -46.5), _w(1))

    def _mor_draw_arm_cast(surface, pt, _w, f, phase, action, ap):
        """Lengan cast depan: pose-driven; telapak = muzzle beam.
        Node sihir di telapak menyala sesuai skill (badan bereaksi)."""
        P = _NS_morgath.PALETTE
        shoulder = _NS_morgath.SHOULDER_FRONT
        hand = _NS_morgath._cast_hand_local(action, ap, phase)
        elbow = _NS_morgath._mor_morph_shoulder_chain(shoulder, hand, 5.25)
        _NS_morgath._mor_sleeve(surface, pt, _w, f, shoulder, elbow, hand,
                                P["robe_dark"], P["robe_mid"], dim=False)

        hp = pt(*hand)
        # Gauntlet
        _NS_morgath._aacircle(surface, P["armor_dark"], hp, _w(4.2))
        _NS_morgath._aacircle(surface, P["armor_mid"], hp, _w(3.2))
        _NS_morgath._aacircle(surface, P["armor_light"], hp, _w(2.0))
        _NS_morgath._aacircle(surface, P["armor_shine"],
                              (hp[0] - _w(0.9), hp[1] - _w(0.9)),
                              _w(1.1))

        # Node sihir di telapak: ukuran mengikuti pose + skill
        skill = _NS_morgath._MOR_SKILL.v
        if skill == "w":
            node_col, glow_col = P["flux_light"], P["flux_mid"]
        elif skill == "r":
            node_col, glow_col = P["white"], P["arc_hot"]
        elif skill == "e":
            node_col, glow_col = P["arc_hot"], P["arc_mid"]
        else:
            node_col, glow_col = P["arc_hot"], P["arc_mid"]
        if action == "attack":
            charge = 1.0 if ap >= 0.9 else min(1.0, ap / 0.35)
            node_r = 3.0 + 4.5 * charge
        elif action in ("point", "channel", "ascend"):
            node_r = 4.5
        elif action == "erect":
            node_r = 3.3
        else:
            node_r = 2.4
        pulse = math.sin(phase * 4.0) * 0.5 + 0.5
        nr = node_r + pulse * 0.9
        _NS_morgath._aacircle(surface, (*glow_col, 70), hp, _w(nr + 4.5))
        _NS_morgath._aacircle(surface, P["arc_dark"], hp, _w(nr))
        _NS_morgath._aacircle(surface, P["arc_mid"], hp, _w(nr - 1.5))
        _NS_morgath._aacircle(surface, node_col, hp, _w(nr - 3.3))
        _NS_morgath._aacircle(surface, P["arc_shine"], hp,
                              _w(max(1, nr - 5.1)))
        # Mini fork berdenyut saat charge penuh / stance skill
        if (action == "attack" and ap >= 0.35) or action in ("point",
                                                             "ascend"):
            for i in range(3):
                ang = phase * 5.0 + i * math.pi * 2.0 / 3.0
                tip = pt(hand[0] + math.cos(ang) * 9.0,
                         hand[1] + math.sin(ang) * 9.0)
                _NS_morgath._jagged_line(surface, P["arc_hot"], hp, tip,
                                         jitter=2.25, segments=2,
                                         width=_w(1.4))



    # ------------------------------------------------------------
    # ATTACK FX (smear berlapis + frame IMPACT)
    # ------------------------------------------------------------
    def _draw_attack_smear(surface, pt, _w, f, ap):
        """Smear dorong 3-band dari tangan tarik -> muzzle (jendela
        thrust) + leading edge terang di telapak sekarang."""
        if not (0.35 <= ap <= 0.92):
            return
        P = _NS_morgath.PALETTE
        t = max(0.0, min(1.0, (ap - 0.35) / 0.45))
        fade = int(200 * math.sin(min(1.0, t * 1.4) * math.pi * 0.5))
        hand = _NS_morgath._cast_hand_local("attack", ap, 0.0)
        hx, hy = hand
        # Band dari belakang tangan ke telapak sekarang (tapered)
        x0, x1 = hx - 30.0, hx + 1.5
        for seg in range(12):
            s0, s1 = seg / 12.0, (seg + 1) / 12.0
            wx = 0.5 + math.sin(s0 * math.pi) * 0.5        # taper
            y0 = hy - 9.0 * wx + math.sin(s0 * 14.0 + f * 3) * 1.2
            y1 = hy - 9.0 * (0.5 + math.sin(s1 * math.pi) * 0.5) \
                + math.sin(s1 * 14.0 + f * 3) * 1.2
            a0 = pt(x0 + (x1 - x0) * s0, y0)
            a1 = pt(x0 + (x1 - x0) * s1, y1)
            _NS_morgath._aaline(surface,
                                (*P["arc_darkest"], int(fade * 0.6)),
                                a0, a1, _w(7))
            _NS_morgath._aaline(surface, (*P["arc_mid"], fade), a0, a1,
                                _w(4))
            _NS_morgath._aaline(surface, (*P["arc_light"], fade), a0, a1,
                                _w(2))
        # Core terang di sepanjang poros + glint berjalan
        a0 = pt(x0, hy - 2.0)
        a1 = pt(x1, hy - 2.0)
        _NS_morgath._aaline(surface, (*P["arc_hot"], fade), a0, a1, _w(1))
        gx = pt(hx + 2.0, hy - 2.0)
        _NS_morgath._rect(surface, P["white"],
                          (gx[0], gx[1], _w(1.4), _w(1.4)))

    def _draw_attack_impact(surface, pt, _w, f, ap, phase):
        """Frame IMPACT: bintang 8-spike + shockwave ganda + forks +
        serpihan di muzzle (jendela HOLD 0.86..0.98)."""
        if not (0.86 <= ap <= 0.98):
            return
        P = _NS_morgath.PALETTE
        t = max(0.0, min(1.0, (ap - 0.86) / 0.12))
        fade = int(235 * (1 - t))
        mx, my = pt(*_NS_morgath.MOR_MUZZLE)
        _NS_morgath._spark_star(surface, mx, my, _w(15 * (1 - t * 0.5)),
                                P["arc_shine"], fade, spikes=8,
                                rot=0.25, core=P["white"])
        for k, rr in enumerate((_w(9 + t * 22), _w(5 + t * 13))):
            _NS_morgath._aacircle(
                surface, (*P["arc_light" if k == 0 else "arc_hot"],
                          fade), (mx, my), rr, _w(1.4))
        for i in range(4):
            ang = i * math.pi / 2.0 + phase * 0.4
            tip = (mx + math.cos(ang) * _w(16 * (1 - t * 0.4)),
                   my + math.sin(ang) * _w(10 * (1 - t * 0.4)))
            _NS_morgath._jagged_line(surface, P["arc_hot"], (mx, my), tip,
                                     jitter=2.0, segments=3, width=_w(1))
        # Serpihan batu/energi (deterministik)
        for i in range(5):
            ang = -2.8 + i * 0.45
            d0 = _w(10 + t * (24 + i * 5))
            cxx = mx + math.cos(ang) * d0
            cyy = my + math.sin(ang) * d0 * 0.7 + t * t * _w(26)
            _NS_morgath._aacircle(surface, P["arc_darkest"],
                                  (int(cxx), int(cyy)), _w(1.6))
            _NS_morgath._aacircle(surface, P["arc_dark"],
                                  (int(cxx - _w(0.5)), int(cyy - _w(0.5))),
                                  _w(0.9))

    # ------------------------------------------------------------
    # AMBIENT LIFE (idle/walk) + PORTRAIT LOD
    # ------------------------------------------------------------
    def _draw_rig_ambient(surface, pt, _w, f, phase, action):
        """Idle hidup: mote naik, percik antena; walk: debu belakang."""
        P = _NS_morgath.PALETTE
        if action == "walk":
            for i in range(3):
                t = (phase * 0.2 + i / 3.0) % 1.0
                mx = -f * (24 + i * 10) - int(t * 12)
                my = 50 - t * 24
                p = pt(mx, my)
                _NS_morgath._aacircle(surface,
                                      (*P["robe_edge"], int(100 * (1 - t))),
                                      p, _w(1.4))
            return
        # mote sihir naik dari hem
        for i in range(3):
            t = (phase * 0.16 + i / 3.0) % 1.0
            mx = math.sin(phase + i * 2.1) * (24 + i * 6)
            my = 36 - t * 110
            p = pt(mx, my)
            _NS_morgath._rect(surface, (*P["arc_mid"], int(140 * (1 - t))),
                              (p[0], p[1], _w(1.2), _w(1.2)))
            _NS_morgath._rect(surface, (*P["arc_hot"], int(110 * (1 - t))),
                              (p[0], p[1], _w(0.8), _w(0.8)))
        # percik antena sesekali (deterministik, aman cache; jitter di
        # ruang lokal lewat _w supaya profil skala boss/lane identik;
        # puncak dijaga <= CY-62 agar tidak menyentuh HP bar boss)
        if int(phase * 3.0) % 8 < 2 and action in ("idle",):
            t0 = pt(-13.5, -70.5)
            t1 = pt(17.25, -70.5)
            _NS_morgath._jagged_line(surface, (*P["arc_light"], 160),
                                     t0, t1, jitter=_w(2), segments=4,
                                     width=_w(1))

    def _mor_draw_masterwork_details(surface, pt, _w, f, phase, action):
        """Micro-detail khusus portrait LOD (Hero Shop)."""
        P = _NS_morgath.PALETTE
        # jahitan hood (tick silang)
        for i in range(4):
            xx = -9 + i * 5
            _NS_morgath._aaline(surface, P["robe_edge"], pt(xx, -60 + i),
                                pt(xx + 2, -57 + i), _w(1))
            _NS_morgath._aaline(surface, P["robe_edge"], pt(xx + 2, -60 + i),
                                pt(xx, -57 + i), _w(1))
        # facet kristal ekstra
        _NS_morgath._aaline(surface, P["orb_light"],
                            pt(3 - 5, -46.5 - 5), pt(3 + 5, -46.5 - 5),
                            _w(1))
        # goresan pauldron + kilau rivet
        for a in (-0.7, -0.2, 0.3):
            _NS_morgath._aaline(surface, P["armor_mid"], pt(-24, -36),
                                pt(-24 - math.cos(a) * 9,
                                   -36 + math.sin(a) * 9), _w(1))
        _NS_morgath._aaline(surface, P["armor_mid"], pt(24, -38),
                            pt(24 + 7, -41), _w(1))
        # serat jubah hem
        for i in range(6):
            _NS_morgath._aaline(surface,
                                P["robe_edge"] if i % 2 else P["robe_mid"],
                                pt(-24 + i * 9, 52),
                                pt(-22 + i * 9, 60 - (i % 3)), _w(1))
        # halaman grimoire
        _NS_morgath._aaline(surface, P["page_light"], pt(-23, 3),
                            pt(-21, 10), _w(1))
        # rune staff
        for i in range(3):
            _NS_morgath._rect(surface, P["gold_shine"],
                              (pt(-23 + i * 2, -20 + i * 14)[0],
                               pt(-23 + i * 2, -20 + i * 14)[1],
                               _w(1), _w(1)))
        # kilau campuran khusus portrait (warna BARU = LOD lebih kaya)
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["orb_light"], P["white"],
                                             .4),
                            pt(1, -58), pt(7, -56), _w(1))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["gold_light"], P["white"],
                                             .5),
                            pt(-11, -61.5), pt(0, -64), _w(1))
        # skala material portrait (masing-masing mix = warna unik baru)
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["orb_mid"], P["orb_hot"],
                                             .45),
                            pt(-5, -52), pt(5, -52), _w(1))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["robe_light"],
                                             P["robe_edge"], .55),
                            pt(-13, -47), pt(-9, -44), _w(1))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["armor_light"], P["white"],
                                             .3),
                            pt(13, -41), pt(18, -39), _w(1))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["gold_mid"],
                                           P["gold_shine"], .4),
                          (pt(9, -47)[0], pt(9, -47)[1], _w(1), _w(1)))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["arc_mid"], P["white"], .35),
                          (pt(-13, -68)[0], pt(-13, -68)[1],
                           _w(1), _w(1)))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["flux_mid"], P["white"], .4),
                          (pt(13, -68)[0], pt(13, -68)[1],
                           _w(1), _w(1)))
        _NS_morgath._aaline(surface,
                            _NS_morgath._mix(P["staff_mid"],
                                             P["staff_light"], .5),
                            pt(-27, 2), pt(-25, 10), _w(1))
        _NS_morgath._rect(surface,
                          _NS_morgath._mix(P["leather_light"],
                                           P["gold_mid"], .45),
                          (pt(5, 12)[0], pt(5, 12)[1], _w(1), _w(1)))

    # ============================================================
    # LIGHTNING PROJECTILE (basic attack) — BOLT MEWAH v2.3
    # ============================================================
    def _glow_sprite(radius=24):
        """Bloom radial prosedural (cache statis per ukuran, tanpa
        image.load)."""
        key = "morgath_bolt_glow_%d" % int(radius)

        def build():
            r = int(radius)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            c = r + 1
            for rr, k, al in ((r, "arc_dark", 36),
                              (int(r * .68), "arc_mid", 64),
                              (int(r * .44), "arc_light", 104),
                              (int(r * .22), "arc_hot", 168)):
                _NS_morgath._aacircle(s, (*_NS_morgath.PALETTE[k], al),
                                      (c, c), rr)
            return s
        return _NS_morgath._static(key, build)

    def _draw_lightning_projectile(surface, boss, x, y, progress):
        """Bolt petir mewah dari telapak (v2.3) — bukan garis polos:
        chord 3-lapis morph per-frame dengan offset heliks + echo arc
        menyambar kembali + ghost chord dobel-eksposur + pulse energi
        berjalan + mach rings + corona berputar + ranting letik +
        trail after-image hollow + mote bara berwarna + bloom radial
        + percik las di telapak + glint orbit + benturan berlapis
        (scorch, ring ganda + ring tunda, bintang 8, garis radial,
        fork jagged, serpihan berekor). 100% prosedural &
        deterministik per-frame."""
        if progress < 0.55:
            return

        # ═══ KOMPENSASI SCALE HERO ═══
        # Beam digambar di ruang dunia skala 1.0 (beam pass hero &
        # jalur boss). _render_scale mungkin tersisa di-set; kompensasi
        # tetap dipasang supaya panggilan langsung (tool preview) juga
        # identik dengan versi mini boss.
        inv = 1.0 / max(0.3, float(getattr(boss, "_render_scale", 1.0)
                                   or 1.0))

        def W(w):
            return max(1, int(math.ceil(w * inv)))

        def _A(a):
            return _NS_morgath._alpha(a * min(1.4, inv))

        def R(r):
            return max(1, int(round(r * inv)))

        def clamp_xy(px, py):
            # efek tidak boleh lolos dari canvas cache (clamp kontrak)
            return (max(0, min(surface.get_width() - 1, int(px))),
                    max(0, min(surface.get_height() - 1, int(py))))

        def blit_glow(gx, gy, alpha, grow=1.0):
            r = max(8, int(round(24 * grow * inv)))
            spr = _NS_morgath._glow_sprite(r)
            spr.set_alpha(_A(alpha))
            surface.blit(spr, (int(gx - r - 1), int(gy - r - 1)))
            spr.set_alpha(255)

        facing = getattr(boss, "_mor_attack_dir", None)
        if facing is None:
            facing = boss.direction
        if hasattr(boss, "_mor_attack_target"):
            scl = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            ox, oy = boss._mor_attack_target
            tx, ty = int(x + ox / scl), int(y + oy / scl)
        else:
            tx, ty = _NS_morgath._target_position(boss, x, y)

        # Lahir dari TELAPAK cast rig (MOR_MUZZLE) di semua skala render
        mdx, mdy = _NS_morgath._muzzle_offset_world()
        start_x = x + facing * int(round(mdx * inv))
        start_y = y + int(round(mdy * inv))

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        ph = float(getattr(boss, "pulse", 0.0))
        P = _NS_morgath.PALETTE

        dx = bx - start_x
        dy = by - start_y
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length

        def chord_pt(s):
            return (int(start_x + dx * s), int(start_y + dy * s))

        # ═══ 0) BLOOM RADIAL (telapak + kepala) ═══
        blit_glow(bx, by, 205)
        blit_glow(start_x, start_y, 145, grow=0.6)

        # ═══ 1) GHOST CHORD (dobel-eksposur, offset tegak lurus) ═══
        # Echo samar seluruh bentuk chord, digeser sedikit — memberi
        # kedalaman listrik (2 citra sekaligus) sebelum chord utama.
        goff = -1.6 * inv
        for i in range(1, 8):
            s0 = (i - 1) / 7
            s1 = i / 7
            a0 = (start_x + dx * s0 + nx * goff,
                  start_y + dy * s0 + ny * goff)
            a1 = (start_x + dx * s1 + nx * goff,
                  start_y + dy * s1 + ny * goff)
            _NS_morgath._aaline(surface, (*P["arc_darkest"], _A(70)),
                                (int(a0[0]), int(a0[1])),
                                (int(a1[0]), int(a1[1])), W(1))

        # ═══ 2) ECHO ARC — leader menyambar balik ke chord ═══
        # 2 busur petir melompat keluar lalu menyambung kembali ke
        # jalur utama (sisi kiri/kanan), khas sambaran listrik asli.
        for k in range(2):
            s_a = 0.22 + 0.36 * k
            s_b = s_a + 0.20
            p_a = chord_pt(s_a)
            p_b = chord_pt(s_b)
            side = 1.0 if (k + int(progress * 26)) % 2 == 0 else -1.0
            bulge = (9.0 + k * 4.0) * inv * side
            m1 = (start_x + dx * (s_a + 0.07) + nx * bulge,
                  start_y + dy * (s_a + 0.07) + ny * bulge)
            m2 = (start_x + dx * (s_a + 0.13) + nx * bulge * 0.55,
                  start_y + dy * (s_a + 0.13) + ny * bulge * 0.55)
            pts = [p_a, (int(m1[0]), int(m1[1])),
                   (int(m2[0]), int(m2[1])), p_b]
            for li, (key, al, w) in enumerate(
                    (("arc_dark", 120, W(2)), ("arc_light", 190, W(1)))):
                for j in range(1, len(pts)):
                    _NS_morgath._aaline(surface, (*P[key], _A(al)),
                                        pts[j - 1], pts[j], w)

        # ═══ 3) CHORD UTAMA: polyline berliku morph hidup ═══
        segs = 7
        pts0 = [(start_x, start_y)]
        for i in range(1, segs + 1):
            s0 = (i - 1) / segs
            s1 = i / segs
            sm = (s0 + s1) / 2
            off = (math.sin(sm * 9.5 + ph * 2.1 + progress * 13.7)
                   + math.sin(sm * 23.0 - ph * 1.3 + progress * 21.3) * .45)
            off *= (4.8 if i % 2 else 3.4) * inv
            ex = start_x + dx * s1
            ey = start_y + dy * s1
            if i == segs:
                ex, ey = bx, by
            pts0.append((int(start_x + dx * sm + nx * off),
                         int(start_y + dy * sm + ny * off)))
            pts0.append((int(ex), int(ey)))
        # 3 lapis pita: lebar menirus + offset heliks antar lapis
        for li, (key, base_w, al) in enumerate(
                (("arc_dark", 5, 130), ("arc_mid", 3, 210),
                 ("arc_light", 1, 245))):
            off = li * 0.9 * inv
            prev = (pts0[0][0] + int(nx * off), pts0[0][1] + int(ny * off))
            for j in range(1, len(pts0)):
                s = (j - 1) / (len(pts0) - 1)
                w = max(1, int(round(base_w * (1.0 - 0.72 * s) * inv)))
                p = (pts0[j][0] + int(nx * off), pts0[j][1] + int(ny * off))
                _NS_morgath._aaline(surface, (*P[key], _A(al)), prev, p, w)
                prev = p
        # Inti menyala di 40% ujung dekat kepala (fokus benturan)
        for j in range(max(0, len(pts0) - 3), len(pts0) - 1):
            _NS_morgath._aaline(surface, (*P["arc_hot"], 255),
                                pts0[j], pts0[j + 1], W(1))

        # ═══ 4) PULSE ENERGI BERJALAN (menyusul kepala) ═══
        # Pita putih menyala berjalan dari telapak menuju kepala 1.6x
        # lebih cepat — ledakan energi di sepanjang lintasan.
        s_band = min(1.0, t * 1.6)
        for k in range(2):
            s_b0 = max(0.0, s_band - 0.045)
            s_b1 = s_band + 0.02
            c0 = (start_x + dx * s_b0 + nx * (0.6 - k) * inv,
                  start_y + dy * s_b0 + ny * (0.6 - k) * inv)
            c1 = (start_x + dx * s_b1 + nx * (0.6 - k) * inv,
                  start_y + dy * s_b1 + ny * (0.6 - k) * inv)
            _NS_morgath._aaline(surface,
                                (*P["arc_shine" if k == 0 else "arc_hot"],
                                 _A(200)),
                                (int(c0[0]), int(c0[1])),
                                (int(c1[0]), int(c1[1])), W(2 - k))
        cxp, cyp = clamp_xy(start_x + dx * s_band, start_y + dy * s_band)
        _NS_morgath._rect(surface, (*P["white"], 255),
                          (cxp, cyp, W(2), W(2)))

        # ═══ 5) RANTING LETIK MENYIMPANG (sisi selang-seling) ═══
        for k, s in ((2, 0.26), (3, 0.46), (4, 0.66)):
            side = 1 if (k + int(progress * 20)) % 2 == 0 else -1
            ax = int(start_x + dx * s)
            ay = int(start_y + dy * s)
            bx2 = int(ax + nx * side * (8 + k) * inv + dx * .12 * inv)
            by2 = int(ay + ny * side * (8 + k) * inv + dy * .12 * inv)
            _NS_morgath._jagged_line(surface, (*P["arc_dark"], _A(150)),
                                     (ax, ay), (bx2, by2),
                                     jitter=2.5 * inv, segments=2,
                                     width=W(2))
            _NS_morgath._jagged_line(surface, (*P["arc_hot"], _A(220)),
                                     (ax, ay), (bx2, by2),
                                     jitter=1.5 * inv, segments=2,
                                     width=W(1))

        # ═══ 6) MACH RINGS (wake kecepatan di belakang kepala) ═══
        # Cincin tipis membesar makin jauh di belakang kepala bolt.
        for g in (1, 2, 3):
            gt = max(0.02, t - 0.045 * g)
            gx, gy = chord_pt(gt)
            _NS_morgath._aacircle(surface,
                                  (*P["arc_mid"], _A(95 - g * 22)),
                                  (gx, gy), R(6 + g * 3), W(1))

        # ═══ 7) TRAIL AFTER-IMAGE HOLLOW + MOTE BARA ═══
        for g in (3, 2, 1):
            gt = max(0.0, t - 0.055 * g)
            gx = int(start_x + dx * gt)
            gy = int(start_y + dy * gt)
            ga = _A(62 - g * 13)
            _NS_morgath._aacircle(surface, (*P["arc_dark"], ga),
                                  (gx, gy), R(4 + g))
            _NS_morgath._aacircle(surface, (*P["arc_mid"], ga + 30),
                                  (gx, gy), R(5 + g), W(1))
        # Mote bara listrik berjatuhan (2 warna, berekor 2 px)
        for i in range(7):
            mt = (0.14 + 0.11 * i
                  + _NS_morgath._hash01(i + int(progress * 30)) * 0.1)
            mt = max(0.0, min(1.0, mt))
            mx = start_x + dx * mt
            my = start_y + dy * mt + (t - mt) * 16 * inv
            key = "arc_mid" if i % 2 == 0 else "flux_light"
            cx0, cy0 = clamp_xy(mx, my)
            _NS_morgath._rect(surface, (*P[key], _A(165)),
                              (cx0, cy0, W(1), W(2)))

        # ═══ 8) KEPALA BOLT: flare 5 lapis + corona + paku + glint ═══
        for radius, key, al in ((10, "arc_darkest", 80),
                                (7, "arc_dark", 140),
                                (5, "arc_mid", 205),
                                (3, "arc_light", 255),
                                (2, "arc_hot", 255)):
            _NS_morgath._aacircle(surface, (*P[key], _A(al)),
                                  (bx, by), R(radius))
        cx0, cy0 = clamp_xy(bx, by)
        _NS_morgath._rect(surface, (*P["white"], 255),
                          (cx0, cy0, W(1), W(1)))
        # Corona 6 paku berputar (2 jagged + 4 lurus, ujung menyala)
        # Semua ujung di luar disk flare kepala (r<=10) supaya tetap
        # putih menyala, tidak tertelan pita gelap flare.
        for i in range(6):
            ang = ph * 2.0 + i * math.pi / 3 + progress * 4.0
            ln = (15.0 if i % 3 == 0 else (13.0 if i % 2 == 0 else 11.0))
            ln *= inv
            px2 = int(math.cos(ang) * ln)
            py2 = int(math.sin(ang) * ln * 0.8)
            sx2 = bx + int(math.cos(ang) * 3 * inv)
            sy2 = by + int(math.sin(ang) * 3 * inv)
            if i % 3 == 0:
                _NS_morgath._jagged_line(surface, P["arc_hot"],
                                         (sx2, sy2), (bx + px2, by + py2),
                                         jitter=1.8 * inv, segments=2,
                                         width=W(1))
            else:
                _NS_morgath._aaline(surface, (*P["arc_hot"], _A(175)),
                                    (sx2, sy2), (bx + px2, by + py2), W(1))
            cx2, cy2 = clamp_xy(bx + px2, by + py2)
            _NS_morgath._rect(surface, (*P["arc_shine"], _A(220)),
                              (cx2, cy2, W(1), W(1)))
        # Dua paku cahaya silang berputar halus di inti
        for i in range(2):
            ga = ph * 2.5 + i * math.pi / 2 + progress * 4.0
            hx = int(math.cos(ga) * 5 * inv)
            hy = int(math.sin(ga) * 4 * inv)
            _NS_morgath._aaline(surface, (*P["arc_hot"], _A(210)),
                                (bx - hx, by - hy), (bx + hx, by + hy),
                                W(1))
        # Glint orbit 3 titik cahaya memutar
        for i in range(3):
            ga = ph * 5.0 + i * math.pi * 2 / 3 + progress * 6.0
            gx = bx + math.cos(ga) * 5.5 * inv
            gy = by + math.sin(ga) * 4.0 * inv
            gx, gy = clamp_xy(gx, gy)
            _NS_morgath._rect(surface, (*P["arc_shine"], _A(235)),
                              (int(gx), int(gy), W(1), W(1)))

        # ═══ 9) PERCIK LAS DI TELAPAK (menyala sepanjang flight) ═══
        # 3 busur kecil menyembur dari muzzle, panjang berkedip-kedip.
        flick = 0.6 + 0.4 * _NS_morgath._hash01(int(progress * 24))
        for i in range(3):
            ang = -0.9 + i * 0.55 + ph * 0.7
            ln = (4 + i * 2.5) * flick * inv
            _NS_morgath._aaline(surface, (*P["arc_hot"], _A(190)),
                                (start_x, start_y),
                                (int(start_x + math.cos(ang) * ln),
                                 int(start_y + math.sin(ang) * ln)),
                                W(1))
        # Bintang pelepasan saat bolt lahir
        if t < 0.25:
            mt2 = t / 0.25
            _NS_morgath._spark_star(surface, start_x, start_y,
                                    int((4 + 6 * (1 - mt2)) * inv),
                                    P["arc_shine"], _A(int(235 * (1 - mt2))),
                                    spikes=6, rot=0.3 + ph, core=P["white"])

        # ═══ 11) BENTURAN BERLAPIS (t > 0.88) ═══
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int((10 + st * 26) * inv)
            alpha = _A(230 * (1 - st))
            # scorch glow di titik benturan
            blit_glow(tx, ty, int(150 * (1 - st)), grow=1.5)
            # ring ganda + ring tunda (micro-ring menyusul)
            _NS_morgath._aacircle(surface, (*P["arc_darkest"], alpha),
                                  (tx, ty), R(radius + 3), W(3))
            _NS_morgath._aacircle(surface, (*P["arc_mid"], alpha),
                                  (tx, ty), R(radius), W(2))
            _NS_morgath._aacircle(surface, (*P["arc_shine"], alpha),
                                  (tx, ty), R(max(1, radius - 6)), W(1))
            st2 = max(0.0, st - 0.35) / 0.65
            _NS_morgath._aacircle(
                surface, (*P["arc_hot"], _A(200 * (1 - st2))),
                (tx, ty), R(max(1, int(radius * 0.55))), W(1))
            _NS_morgath._spark_star(surface, tx, ty,
                                    int((9 + st * 15) * inv),
                                    P["arc_shine"], int(225 * (1 - st)),
                                    spikes=8, rot=0.5, core=P["white"])
            # 8 garis radial lurus
            for i in range(8):
                ang = i * math.pi / 4 + progress * 2.0
                ex = int(tx + math.cos(ang) * radius * 1.05 * inv)
                ey = int(ty + math.sin(ang) * radius * 0.8 * inv)
                _NS_morgath._aaline(surface, (*P["arc_hot"], alpha),
                                    (tx, ty), (ex, ey), W(1))
            # 4 fork jagged di antara garis radial
            for i in range(4):
                ang = (i + 0.5) * math.pi / 2 + progress * 2.0
                ex = int(tx + math.cos(ang) * radius * 1.25 * inv)
                ey = int(ty + math.sin(ang) * radius * 0.95 * inv)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (tx, ty), (ex, ey),
                                         jitter=2.0 * inv, segments=2,
                                         width=W(1))
            # 8 serpihan deterministik berekor
            for i in range(8):
                a = 0.7 + i * 0.72 + _NS_morgath._hash01(i * 5) * 0.6
                r = (7 + st * 24) * inv
                dx2 = math.cos(a) * r
                dy2 = math.sin(a) * r * 0.55 - st * st * 8 * inv
                cx2, cy2 = clamp_xy(tx + dx2, ty + dy2)
                _NS_morgath._rect(surface, (*P["arc_light"], alpha),
                                  (cx2, cy2, W(1), W(1)))
                cx3, cy3 = clamp_xy(tx + dx2 * 0.6, ty + dy2 * 0.6)
                _NS_morgath._rect(surface, (*P["arc_mid"], alpha),
                                  (cx3, cy3, W(1), W(1)))



    # ============================================================
    # SHADOW / ARC AURA / GROUND RUNE (static cached)
    # ============================================================
    def _draw_shadow(surface, x, y):
        """Bayangan mengikuti lebar hem rig (cached - dibangun sekali)."""
        def build():
            shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
            for radius in range(13, 0, -1):
                alpha = max(0, (13 - radius) * 15)
                pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                    (13 - radius, 13 - radius,
                                     104 + radius * 2, radius * 2))
            pygame.draw.ellipse(shadow, (2, 5, 12, 190), (8, 7, 114, 12))
            return shadow
        shadow = _NS_morgath._static("shadow", build)
        surface.blit(shadow, (x - 65, y - 13))

    def _draw_arc_aura(surface, x, y, phase):
        """Aura elektrik biru di belakang boss (cached) + sparkle &
        busur petir deterministik."""
        P = _NS_morgath.PALETTE
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        def build():
            aura = pygame.Surface((280, 240), pygame.SRCALPHA)
            for radius in range(105, 8, -5):
                # Falloff ^4: alpha >= 100 hanya di r <= ~25 px canvas,
                # SELALU di dalam siluet badan di kedua jalur (boss 0.6x
                # maupun lane native 1.38x) - mask pengukuran pipeline
                # (_BODY_ALPHA_THRESHOLD=100) melihat badan, bukan aura.
                f = max(0.0, 1.0 - radius / 105.0)
                alpha = _NS_morgath._alpha(255 * f ** 4)
                if alpha > 0:
                    _NS_morgath._aacircle(aura,
                                          (*P["arc_darkest"], alpha),
                                          (140, 120), radius)
            for radius in range(66, 8, -4):
                f = max(0.0, 1.0 - radius / 66.0)
                alpha = _NS_morgath._alpha(230 * f ** 4)
                if alpha > 0:
                    _NS_morgath._aacircle(aura, (*P["arc_dark"], alpha),
                                          (140, 120), radius)
            return aura
        aura = _NS_morgath._static("arc_aura", build)
        if pulse < 0.92:
            faded = aura.copy()
            faded.set_alpha(int(255 * pulse))
            surface.blit(faded, (x - 140, y - 120))
        else:
            surface.blit(aura, (x - 140, y - 120))

        # Floating electric sparkles (deterministik per phase; alpha di
        # bawah ambang 100 supaya tidak ikut terukur sebagai badan).
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r = 48 + int(math.sin(phase + i) * 18)
            sx = x + int(math.cos(angle) * r)
            sy = y - 8 + int(math.sin(angle) * r * 0.5)
            alpha = _NS_morgath._alpha(72 + math.sin(phase * 4 + i) * 20)
            pygame.draw.rect(surface, (*P["arc_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*P["arc_hot"], alpha), (sx, sy, 1, 1))

        # Busur petir sesekali antar sparkle (frame-gated deterministik)
        arc_frame = int(phase * 3) % 8
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 0.4 + k * math.pi / 6
                a2 = phase * 0.4 + (k + 3) * math.pi / 6
                r = 48
                p1 = (x + int(math.cos(a1) * r),
                      y - 8 + int(math.sin(a1) * r * 0.5))
                p2 = (x + int(math.cos(a2) * r),
                      y - 8 + int(math.sin(a2) * r * 0.5))
                _NS_morgath._jagged_line(surface, (*P["arc_light"], 88),
                                         p1, p2, jitter=4.5, segments=5,
                                         width=1)

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Rune lingkaran biru - rapat di bawah hem jubah (cached).
        Tidak boleh lebih lebar/lebih terang dari badan."""
        P = _NS_morgath.PALETTE
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75

        def build():
            ring = pygame.Surface((112, 38), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*P["arc_darkest"], 190),
                                (4, 13, 104, 20), 2)
            pygame.draw.ellipse(ring, (*P["arc_dark"], 200),
                                (12, 16, 88, 14), 1)
            pygame.draw.ellipse(ring, (*P["arc_mid"], 150),
                                (26, 18, 60, 10), 1)
            return ring
        ring = _NS_morgath._static("ground_rune", build)
        surface.blit(ring, (x - 56, y - 19))

        # Rune spokes (pendek, di dalam cincin - dinamis murah)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = x + int(math.cos(angle) * 28)
            y1 = y + int(math.sin(angle) * 6)
            x2 = x + int(math.cos(angle) * 46)
            y2 = y + int(math.sin(angle) * 10)
            pygame.draw.line(surface, (*P["arc_dark"], 190),
                             (x1, y1), (x2, y2), 1)

        if skill:
            col = {"w": P["flux_mid"], "e": P["arc_hot"],
                   "r": P["arc_shine"], "q": P["arc_light"]}.get(
                       skill, P["arc_hot"])
            pygame.draw.ellipse(surface,
                                (*col, _NS_morgath._alpha(150 * pulse)),
                                (x - 44, y - 14, 88, 28), 1)

    # ============================================================
    # AKTIVASI SKILL (shared): shockwave + bintang + mote
    # ============================================================
    def _draw_skill_activation(surface, boss, x, y, skill, timer, phase):
        """Gelombang kejut aktivasi (12 frame pertama tiap skill)."""
        if skill not in _NS_morgath.SKILL_DUR:
            return
        dur = _NS_morgath.SKILL_DUR[skill]
        age = dur - timer
        if not (0 <= age < 12):
            return
        P = _NS_morgath.PALETTE
        fs = _NS_morgath._fx_scale(boss)
        st = age / 12.0
        a = _NS_morgath._alpha(235 * (1 - st))
        col = {"q": P["arc_light"], "w": P["flux_light"],
               "e": P["arc_hot"], "r": P["arc_shine"]}.get(skill,
                                                           P["arc_light"])
        gy = y + _NS_morgath._ground_dy()
        rr = int((24 + st * 70) * fs)
        rr = min(rr, _NS_morgath._ring_r(boss, 96, surface))
        _NS_morgath._aacircle(surface, (*col, a), (x, gy), rr, 2)
        _NS_morgath._aacircle(surface, (*P["white"], a),
                              (x, gy), max(1, rr // 2), 1)
        _NS_morgath._spark_star(surface, x, gy,
                                int((14 - st * 6) * fs), col,
                                int(210 * (1 - st)), spikes=6, rot=0.35,
                                core=P["white"])
        for i in range(6):
            ang = i * math.pi / 3 + st * 2.0
            mx = x + math.cos(ang) * rr * 0.6
            my = gy + math.sin(ang) * rr * 0.3 - st * 18 * fs
            _NS_morgath._rect(surface, (*col, a), (int(mx), int(my),
                                                   2, 2))



    # ============================================================
    # SKILL Q: SPARK WRAITH (homing electric orb)
    # 3 fase: TELEGRAPH (chevron ke target) -> AKTIVASI (vortex di
    # telapak) -> FLIGHT (trail berlapis + glint) + IMPACT bintang.
    # ============================================================
    def _draw_sparkwraith_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH: chevron berbaris menuju target + splat marker."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        if progress > 0.25:
            return
        fade = int(210 * (0.25 - progress) / 0.25)
        sx, sy = _NS_morgath._skill_hand_canvas(boss, x, y, "q")
        tx, ty = _NS_morgath._target_position(boss, x, y)
        ang = math.atan2(ty - sy, tx - sx)
        dist = math.hypot(tx - sx, ty - sy)
        # garis pandu putus-putus
        for i in range(int(dist // (12 * fs)) + 1):
            t0 = i * 12 * fs
            p0 = (sx + math.cos(ang) * t0, sy + math.sin(ang) * t0)
            p1 = (sx + math.cos(ang) * (t0 + 6 * fs),
                  sy + math.sin(ang) * (t0 + 6 * fs))
            _NS_morgath._aaline(surface, (*P["arc_dark"], fade),
                                p0, p1, 1)
        # chevron berbaris (marching)
        for i in range(6):
            tt = ((phase * 0.35 + i / 6.0) % 1.0)
            cx_ = sx + math.cos(ang) * tt * dist
            cy_ = sy + math.sin(ang) * tt * dist
            _NS_morgath._chevron(surface, cx_, cy_, ang, 9 * fs,
                                 P["arc_light"], fade, width=2)
        # splat marker di target (2 ring putus-putus berlawanan)
        _NS_morgath._dashed_ring(surface, tx, ty, 13 * fs, P["arc_mid"],
                                 fade, phase * 2, segments=8, thick=2,
                                 span=0.5)
        _NS_morgath._dashed_ring(surface, tx, ty, 19 * fs, P["arc_light"],
                                 fade, -phase * 1.6, segments=10, thick=2,
                                 span=0.4)

    def _draw_sparkwraith_foreground(surface, boss, x, y, timer, phase):
        """AKTIVASI vortex + FLIGHT mewah + IMPACT."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        tx, ty = _NS_morgath._target_position(boss, x, y)

        if progress < 0.4:
            # ── AKTIVASI: vortex 2 lengan spiral berlawanan + droplet ──
            t = min(1.0, progress / 0.25)
            cx_, cy_ = _NS_morgath._skill_hand_canvas(boss, x, y, "q")
            for arm in range(2):
                for step in range(14):
                    s_t = step / 14.0
                    ang = (phase * 3.0 * (1 if arm == 0 else -1)
                           + arm * math.pi + s_t * math.pi * 2.6)
                    s_r = int(20 * (1 - s_t) * t * fs)
                    px_ = cx_ + math.cos(ang) * s_r
                    py_ = cy_ + math.sin(ang) * s_r
                    _NS_morgath._rect(
                        surface,
                        (*P["arc_light" if arm == 0 else "arc_mid"],
                         _NS_morgath._alpha(200 * (1 - s_t) * t)),
                        (int(px_), int(py_), 2, 2))
            for i in range(6):
                ang = phase * 4 + i * math.pi / 3
                d = (8 + t * 10) * fs
                _NS_morgath._aacircle(
                    surface, (*P["arc_hot"], int(200 * t)),
                    (int(cx_ + math.cos(ang) * d),
                     int(cy_ + math.sin(ang) * d)), max(1, int(2 * fs)))
            _NS_morgath._spark_star(surface, cx_, cy_, int(12 * t * fs),
                                    P["arc_shine"], int(220 * t),
                                    spikes=6, rot=phase, core=P["white"])
            for i in range(3):
                ang = phase * 6 + i * 2.1
                tip = (cx_ + math.cos(ang) * (12 + t * 8) * fs,
                       cy_ + math.sin(ang) * (12 + t * 8) * fs)
                _NS_morgath._jagged_line(surface, P["arc_light"],
                                         (cx_, cy_), tip, jitter=2,
                                         segments=3, width=1)
            return

        # ── FLIGHT: orb menuju target (kurva) + trail 2-tone + glint ──
        t = (progress - 0.4) / 0.5
        t = min(1.0, t)
        start_x, start_y = _NS_morgath._skill_hand_canvas(boss, x, y, "q")
        mid_x = (start_x + tx) / 2
        mid_y = min(start_y, ty) - 45 * fs
        bx = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x
                 + t ** 2 * tx)
        by = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y
                 + t ** 2 * ty)

        # trail berlapis 2-tone
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px_ = int((1 - trail_t) ** 2 * start_x
                      + 2 * (1 - trail_t) * trail_t * mid_x
                      + trail_t ** 2 * tx)
            py_ = int((1 - trail_t) ** 2 * start_y
                      + 2 * (1 - trail_t) * trail_t * mid_y
                      + trail_t ** 2 * ty)
            alpha = _NS_morgath._alpha(240 - i * 28)
            size = max(1, int((12 - i) * fs))
            _NS_morgath._aacircle(surface, (*P["arc_darkest"], alpha),
                                  (px_, py_), size)
            _NS_morgath._aacircle(surface, (*P["arc_dark"], alpha),
                                  (px_, py_), max(1, size - int(2 * fs)))
            _NS_morgath._aacircle(surface, (*P["arc_mid"], alpha),
                                  (px_, py_), max(1, size - int(4 * fs)))
        # kepala orb terang + aura
        for r in range(14, 4, -2):
            alpha = _NS_morgath._alpha(90 * (14 - r) / 14)
            _NS_morgath._aacircle(surface, (*P["arc_light"], alpha),
                                  (bx, by), int(r * fs))
        _NS_morgath._aacircle(surface, P["arc_darkest"], (bx, by),
                              int(11 * fs))
        _NS_morgath._aacircle(surface, P["arc_dark"], (bx, by),
                              int(9 * fs))
        _NS_morgath._aacircle(surface, P["arc_mid"], (bx, by),
                              int(6 * fs))
        _NS_morgath._aacircle(surface, P["arc_light"], (bx, by),
                              int(4 * fs))
        _NS_morgath._aacircle(surface, P["arc_shine"], (bx, by),
                              int(2 * fs))
        pygame.draw.rect(surface, P["white"], (bx, by, 1, 1))
        # glint orbit di ujung orb
        for i in range(2):
            ga = phase * 6 + i * math.pi
            gx = bx + int(math.cos(ga) * 6 * fs)
            gy = by + int(math.sin(ga) * 6 * fs)
            pygame.draw.rect(surface, P["white"], (gx, gy, 1, 1))
        # tendril listrik berputar
        for i in range(5):
            angle = phase * 6 + i * math.pi * 2 / 5
            tip = (bx + math.cos(angle) * 15 * fs,
                   by + math.sin(angle) * 15 * fs)
            _NS_morgath._jagged_line(surface, P["arc_hot"], (bx, by),
                                     tip, jitter=3, segments=3, width=1)

        # IMPACT
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int((21 + st * 40) * fs)
            radius = min(radius, _NS_morgath._ring_r(boss, 120, surface))
            alpha = _NS_morgath._alpha(240 * (1 - st))
            _NS_morgath._aacircle(surface, (*P["arc_darkest"], alpha),
                                  (tx, ty), radius + 4, 3)
            _NS_morgath._aacircle(surface, (*P["arc_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_morgath._aacircle(surface, (*P["arc_light"], alpha),
                                  (tx, ty), max(1, radius - 8), 2)
            _NS_morgath._spark_star(surface, tx, ty,
                                    int((10 + st * 16) * fs), P["arc_shine"],
                                    int(230 * (1 - st)), spikes=8, rot=0.3,
                                    core=P["white"])
            for i in range(10):
                angle_s = i * math.pi / 5
                ex_ = tx + int(math.cos(angle_s) * radius)
                ey_ = ty + int(math.sin(angle_s) * radius * 0.7)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (tx, ty), (ex_, ey_),
                                         jitter=3, segments=4, width=1)

    # ============================================================
    # SKILL W: FLUX (purple debuff pool at target)
    # 3 fase: TELEGRAPH (ring konvergen) -> AKTIVASI (pilar ungu) ->
    # STEADY (pool berlapis + rune ring berputar + mote/ember naik).
    # ============================================================
    def _draw_flux_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH + pool berlapis di target (world-space)."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        tx, ty = _NS_morgath._target_position(boss, x, y)
        pool_r = 38
        r = int(pool_r * fs)

        if progress < 0.3:
            # ── TELEGRAPH: 3 ring konvergen + chevron ke dalam ──
            t = progress / 0.3
            fade = int(200 * (1 - t * 0.4))
            for i in range(3):
                rr = int((pool_r + (70 - pool_r) * (1 - t)
                          + i * 9) * fs)
                _NS_morgath._aacircle(surface, (*P["flux_mid"], fade),
                                      (tx, ty), rr, 2)
            for i in range(4):
                ang = phase * 1.2 + i * math.pi / 2
                cxp = tx + math.cos(ang) * (r + 14 * fs)
                cyp = ty + math.sin(ang) * (r + 14 * fs) * 0.5
                _NS_morgath._chevron(surface, cxp, cyp,
                                     ang + math.pi, 8 * fs,
                                     P["flux_light"], fade, width=2)
            return

        if r > 3:
            # pool berlapis: rim panas + alpha pool
            _NS_morgath._ellipse(
                surface, (*P["flux_hot"], 120),
                (tx - r - 3, ty - (r + 3) // 3,
                 (r + 3) * 2, (r + 3) * 2 // 3), 2)
            _NS_morgath._ellipse(surface, (*P["flux_darkest"], 240),
                                 (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            _NS_morgath._ellipse(surface, (*P["flux_dark"], 220),
                                 (tx - r + 3, ty - r // 3 + 2,
                                  r * 2 - 6, r * 2 // 3 - 4))
            _NS_morgath._ellipse(surface, (*P["flux_mid"], 180),
                                 (tx - r + 8, ty - r // 3 + 4,
                                  r * 2 - 16, r * 2 // 3 - 8))
            # rune ring ganda berlawanan arah
            _NS_morgath._dashed_ring(surface, tx, ty, r + 7, P["flux_light"],
                                     200, phase * 2.2, segments=10,
                                     thick=2, span=0.55, squash=0.5)
            _NS_morgath._dashed_ring(surface, tx, ty, r + 14, P["flux_mid"],
                                     160, -phase * 1.7, segments=12,
                                     thick=1, span=0.45, squash=0.5)

    def _draw_flux_foreground(surface, boss, x, y, timer, phase):
        """AKTIVASI pilar ungu + STEADY tendril/mote/ember naik."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        tx, ty = _NS_morgath._target_position(boss, x, y)
        r = int(38 * fs)

        # ── AKTIVASI: pilar cahaya 3-lapis + bintang + shockwave ──
        if progress < 0.45:
            t = min(1.0, progress / 0.3)
            top = int(ty - min(110 * fs, 230) * (0.5 + 0.5 * (1 - t)))
            for wd, col, al in ((26, P["flux_dark"], 110),
                                (16, P["flux_mid"], 150),
                                (7, P["flux_light"], 200)):
                _NS_morgath._aaline(surface, (*col, int(al * (1 - t))),
                                    (tx, top), (tx, ty), wd)
            _NS_morgath._spark_star(surface, tx, ty,
                                    int(26 * (1 - t * 0.4)), P["flux_hot"],
                                    int(230 * (1 - t)), spikes=8, rot=0.3,
                                    core=P["white"])
            for k, rmax in ((0, 90), (1, 60)):
                rr = int((16 + t * rmax) * fs)
                _NS_morgath._aacircle(
                    surface,
                    (*P["flux_light" if k == 0 else "flux_hot"],
                     int((210 if k == 0 else 140) * (1 - t))),
                    (tx, ty), rr, 2)
            return

        # ── STEADY: tendril + mote + ember naik + core mendidih ──
        for i in range(8):
            wisp_t = (phase * 0.7 + i * 0.15) % 1.0
            angle = i * math.pi / 4 + phase * 0.3
            wx = tx + int(math.cos(angle) * r * 0.6)
            wy_base = ty + int(math.sin(angle) * r * 0.3)
            wy = wy_base - int(wisp_t * 45 * fs)
            alpha = _NS_morgath._alpha(230 * (1 - wisp_t))
            _NS_morgath._aacircle(surface, (*P["flux_dark"], alpha),
                                  (wx, wy), int(7 * fs))
            _NS_morgath._aacircle(surface, (*P["flux_mid"], alpha),
                                  (wx, wy - 1), int(5 * fs))
            _NS_morgath._aacircle(surface, (*P["flux_light"], alpha),
                                  (wx, wy - 1), int(2 * fs))
            _NS_morgath._rect(surface, (*P["flux_hot"], alpha),
                              (wx, wy - 1, 1, 1))
        # mote & ember naik dari pool
        for i in range(10):
            rise_t = (phase * 0.5 + i * 0.1) % 1.0
            angle = i * math.pi * 2 / 10 + phase * 0.4
            sp_r = r * (0.4 + (i % 3) * 0.25)
            sx = tx + int(math.cos(angle) * sp_r)
            sy = ty + int(math.sin(angle) * sp_r * 0.4) - int(rise_t * 30 * fs)
            alpha = _NS_morgath._alpha(200 * (1 - rise_t))
            if alpha > 0:
                _NS_morgath._rect(surface, (*P["flux_light"], alpha),
                                  (sx, sy, 2, 2))
                _NS_morgath._rect(surface, (*P["flux_hot"], alpha),
                                  (sx, sy, 1, 1))
        # central bubbling core
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for cr in range(8, 0, -1):
            alpha = _NS_morgath._alpha(220 * (8 - cr) / 8 * core_pulse)
            _NS_morgath._aacircle(surface, (*P["flux_mid"], alpha),
                                  (tx, ty), int(cr * fs))
        _NS_morgath._aacircle(surface, P["flux_light"], (tx, ty),
                              int(3 * fs))
        _NS_morgath._aacircle(surface, P["flux_hot"], (tx, ty),
                              int(1 * fs))

    # ============================================================
    # SKILL E: MAGNETIC FIELD (dome shield, range = 90 px dunia)
    # 3 fase: TELEGRAPH (ring 90 dunia) -> AKTIVASI (dome bangkit) ->
    # STEADY (kubah 4 lapis + hex grid + spark berputar).
    # ============================================================
    def _dome_static():
        """Kubah statis (cached): 4 lapis busur + hex grid + rim dots."""
        P = _NS_morgath.PALETTE
        dome = pygame.Surface((300, 150), pygame.SRCALPHA)
        center = (150, 148)
        r = 140
        for layer_i, (thickness, col) in enumerate((
                (5, P["arc_dark"]), (3, P["arc_mid"]),
                (2, P["arc_light"]), (1, P["arc_hot"]))):
            arc_rect = pygame.Rect(center[0] - r + layer_i * 3,
                                   center[1] - r + layer_i * 3,
                                   (r - layer_i * 3) * 2,
                                   (r - layer_i * 3) * 2)
            pygame.draw.arc(dome, col, arc_rect, math.pi, math.tau,
                            thickness)
        # hex grid dalam kubah
        for h_row in range(5):
            for h_col in range(-5, 6):
                grid_x = center[0] + h_col * 14 + (h_row % 2) * 7
                grid_y = center[1] - 6 - h_row * 12
                dist = math.hypot(grid_x - center[0],
                                  grid_y - center[1])
                if dist < r - 10:
                    pygame.draw.rect(dome, (*P["arc_mid"], 150),
                                     (grid_x - 1, grid_y - 1, 3, 3), 1)
        # rim dots statis
        for i in range(14):
            ang = math.pi + (i / 13.0) * math.pi
            ax = center[0] + int(math.cos(ang) * r)
            ay = center[1] + int(math.sin(ang) * r)
            pygame.draw.rect(dome, P["arc_hot"], (ax, ay, 2, 2))
            pygame.draw.rect(dome, P["arc_shine"], (ax, ay, 1, 1))
        return dome

    def _draw_magneticfield_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH: ring jangkauan TEPAT 90 px dunia + ring konvergen
        + chevron kardinal + rune ring berputar."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        gy = y + _NS_morgath._ground_dy()
        r = _NS_morgath._ring_r(boss, 90, surface)
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # ring jangkauan tebal + inner (selalu, semua fase)
        for i, (rr, col) in enumerate(((r, P["arc_mid"]),
                                       (r - int(5 * fs), P["arc_light"]))):
            _NS_morgath._aacircle(surface, (*col,
                                            int((250 - i * 50) * pulse)),
                                  (x, gy), max(1, rr), 2)
        # rune ring berputar
        _NS_morgath._dashed_ring(surface, x, gy, r + 4, P["arc_hot"],
                                 int(190 * pulse), phase * 1.6,
                                 segments=12, thick=2, span=0.5,
                                 squash=0.45)

        if progress < 0.25:
            # ── TELEGRAPH: ring konvergen mengecil ke 90 + chevron ──
            t = progress / 0.25
            fade = int(210 * (1 - t * 0.5))
            for i in range(2):
                rr = int((90 + (128 - 90) * (1 - t) + i * 8) * fs)
                rr = min(rr, _NS_morgath._ring_r(boss, 132, surface))
                _NS_morgath._aacircle(surface, (*P["arc_light"], fade),
                                      (x, gy), rr, 1)
            for i in range(4):
                ang = i * math.pi / 2 + math.pi / 4
                cxp = x + math.cos(ang) * r
                cyp = gy + math.sin(ang) * r * 0.45
                _NS_morgath._chevron(surface, cxp, cyp, ang, 9 * fs,
                                     P["arc_hot"], fade, width=2)
        elif progress < 0.4:
            # ── AKTIVASI: shockwave ganda + bintang ──
            t = (progress - 0.25) / 0.15
            fade = int(230 * (1 - t))
            _NS_morgath._spark_star(surface, x, gy, int(30 * (1 - t * 0.4)),
                                    P["arc_shine"], fade, spikes=8,
                                    rot=0.3, core=P["white"])
            for k, rmax in ((0, 100), (1, 74)):
                rr = int((r + t * rmax * fs * 0.4) * 0.9)
                _NS_morgath._aacircle(
                    surface,
                    (*P["arc_light" if k == 0 else "arc_hot"], fade),
                    (x, gy), rr, 2)

    def _draw_magneticfield_foreground(surface, boss, x, y, timer, phase):
        """STEADY: kubah besar di atas boss (static cached, scaled)."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        gy = y + _NS_morgath._ground_dy()
        r = _NS_morgath._ring_r(boss, 90, surface)
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        build_t = 1.0
        if progress < 0.4:
            build_t = max(0.0, (progress - 0.2) / 0.2)   # dome bangkit
            if build_t <= 0:
                return

        dome = _NS_morgath._static("e_dome", _NS_morgath._dome_static)
        dome = pygame.transform.smoothscale(
            dome, (max(2, r * 2), max(2, int(r * build_t))))
        dome.set_alpha(int(150 + 80 * pulse))
        surface.blit(dome, (x - r, gy - int(r * build_t)))

        # spark berputar di permukaan kubah (deterministik)
        for i in range(6):
            ang = phase * 1.5 + i * math.pi / 3
            arc_angle = math.pi * (0.1 + (i / 6.0) * 0.8)
            ax = x + int(math.cos(math.pi + arc_angle) * r * build_t)
            ay = gy + int(math.sin(math.pi + arc_angle) * r * build_t)
            _NS_morgath._rect(surface, (*P["arc_hot"], 240),
                              (ax, ay, 2, 2))
            _NS_morgath._rect(surface, (*P["arc_shine"], 255),
                              (ax, ay, 1, 1))

        # busur petir acak di dalam kubah (frame-gated deterministik)
        arc_frame = int(phase * 4) % 5
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 2 + k * 1.7
                a2 = phase * 2 + k * 1.7 + 1.5
                aa1 = math.pi * (0.15 + ((math.sin(a1) + 1) / 2) * 0.7)
                aa2 = math.pi * (0.15 + ((math.sin(a2) + 1) / 2) * 0.7)
                p1 = (x + int(math.cos(math.pi + aa1) * r * build_t),
                      gy + int(math.sin(math.pi + aa1) * r * build_t))
                p2 = (x + int(math.cos(math.pi + aa2) * r * build_t),
                      gy + int(math.sin(math.pi + aa2) * r * build_t))
                _NS_morgath._jagged_line(surface, P["arc_hot"], p1, p2,
                                         jitter=4, segments=6, width=1)

    # ============================================================
    # SKILL R: TEMPEST DOUBLE (ultimate; clone di +/-60 px dunia)
    # 3 fase: TELEGRAPH (ring kembar + retakan) -> AKTIVASI (pilar
    # cahaya + burst radial) -> STEADY (2 ghost clone + tether +
    # ember + wisp spiral).
    # ============================================================
    def _draw_tempest_ground(surface, boss, x, y, timer, phase):
        """TELEGRAPH + twin rune ring di posisi clone (+/-60 dunia)."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        facing = getattr(boss, "direction", 1) or 1
        gy = y + _NS_morgath._ground_dy()
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        off = 60 * fs

        # ── TELEGRAPH: retakan zigzag + ring konvergen + chevron ──
        if progress < 0.3:
            t = progress / 0.3
            fade = int(210 * (1 - t * 0.4))
            for side in (-1, 1):
                cxp = int(x + facing * side * off)
                # retakan tanah menuju titik clone (deterministik)
                crack_ang = 0.0 if (facing * side) > 0 else math.pi
                _NS_morgath._jagged_crack(
                    surface, x, gy, crack_ang,
                    int(58 * fs), (P["flux_dark"], P["flux_mid"]),
                    fade, seed=5 + side, width=3)
                _NS_morgath._jagged_crack(
                    surface, x, gy, crack_ang,
                    int(40 * fs), (P["flux_mid"], P["flux_hot"]),
                    int(fade * 0.8), seed=9 + side, width=1)
                rr = int((24 + (1 - t) * 14) * fs)
                _NS_morgath._aacircle(surface, (*P["flux_light"], fade),
                                      (cxp, gy), rr, 2)
                for i in range(3):
                    ang = -side * facing * math.pi / 2 + i * 0.5
                    cxx = cxp + math.cos(ang) * (rr + 10 * fs)
                    cyy = gy + math.sin(ang) * (rr + 10 * fs) * 0.45
                    _NS_morgath._chevron(surface, cxx, cyy,
                                         math.atan2(gy - cyy, x - cxx),
                                         7 * fs, P["flux_hot"], fade,
                                         width=2)

        # twin rune ring di posisi clone (steady)
        for side in (-1, 1):
            cxp = int(x + facing * side * off)
            r = int((34 + math.sin(phase * 2 + side) * 4) * fs)
            alpha = _NS_morgath._alpha(240 * pulse)
            _NS_morgath._aacircle(surface, (*P["flux_mid"], alpha),
                                  (cxp, gy), r, 2)
            _NS_morgath._dashed_ring(surface, cxp, gy, r + 5,
                                     P["flux_light"], int(200 * pulse),
                                     phase * 2.4 * side, segments=10,
                                     thick=2, span=0.5, squash=0.45)

    def _draw_tempest_clone(surface, boss, x, y, timer, phase):
        """Ghost duplicate x2 di +/-60 px dunia + tether listrik."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        facing = getattr(boss, "direction", 1) or 1
        if progress < 0.35:
            return
        spawn_t = min(1.0, (progress - 0.35) / 0.25)
        alpha_val = int(215 * spawn_t)

        for side in (-1, 1):
            cxp, cyp = _NS_morgath._world_to_local(
                boss, x, y,
                float(getattr(boss, "x", x)) + facing * side * 60,
                float(getattr(boss, "y", y)))
            buf, box = _NS_morgath._rig_buffer(facing, phase * 1.3,
                                               "idle", 0.0, False)
            tint = pygame.Surface(buf.get_size(), pygame.SRCALPHA)
            tint.fill((110, 150, 235, 255))
            buf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            buf.set_alpha(alpha_val)
            w = max(1, int(buf.get_width() * fs))
            h = max(1, int(buf.get_height() * fs))
            if fs != 1.0:
                buf = pygame.transform.smoothscale(buf, (w, h))
            surface.blit(buf, (int(cxp - box[0] * fs),
                               int(cyp - box[1] * fs)))
            # ring kecil di kaki clone
            _NS_morgath._ellipse(
                surface, (*P["flux_mid"], 140),
                (int(cxp - 20 * fs), int(cyp + 24 * fs - 2),
                 int(40 * fs), int(5 * fs)), 1)

        # tether listrik caster <-> clone (frame-gated deterministik)
        arc_frame = int(phase * 6) % 4
        if arc_frame < 2:
            for side in (-1, 1):
                cxp, cyp = _NS_morgath._world_to_local(
                    boss, x, y,
                    float(getattr(boss, "x", x)) + facing * side * 60,
                    float(getattr(boss, "y", y)))
                _NS_morgath._jagged_line(surface, P["arc_hot"],
                                         (x, y - 15),
                                         (cxp, cyp - 30 * fs),
                                         jitter=9, segments=8, width=2)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (x, y - 15),
                                         (cxp, cyp - 30 * fs),
                                         jitter=7, segments=8, width=1)

    def _draw_tempest_foreground(surface, boss, x, y, timer, phase):
        """AKTIVASI pilar + burst petir radial + aftermath bara."""
        P = _NS_morgath.PALETTE
        dur = _NS_morgath.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / dur))
        fs = _NS_morgath._fx_scale(boss)
        facing = getattr(boss, "direction", 1) or 1
        gy = y + _NS_morgath._ground_dy()

        if progress < 0.45:
            # ── AKTIVASI: pilar cahaya 4 lapis + shockwave ganda ──
            t = min(1.0, progress / 0.3)
            top = int(y - min(120 * fs, 250) * (0.55 + 0.45 * (1 - t)))
            for wd, col, al in ((34, P["arc_darkest"], 120),
                                (22, P["flux_mid"], 150),
                                (12, P["arc_mid"], 190),
                                (4, P["white"], 220)):
                _NS_morgath._aaline(surface, (*col, int(al * (1 - t))),
                                    (x, top), (x, y - 10), wd)
            _NS_morgath._spark_star(surface, x, y - 10,
                                    int(34 * (1 - t * 0.4)), P["arc_shine"],
                                    int(235 * (1 - t)), spikes=8, rot=0.3,
                                    core=P["white"])
            for k, rmax in ((0, 130), (1, 92)):
                rr = int((20 + t * rmax) * fs)
                _NS_morgath._aacircle(
                    surface,
                    (*P["arc_light" if k == 0 else "flux_light"],
                     int((220 if k == 0 else 150) * (1 - t))),
                    (x, y - 10), rr, 2)
            # burst petir radial (12 bolt)
            burst_r = int((44 + t * 60) * fs)
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.5
                end_x = x + int(math.cos(angle) * burst_r)
                end_y = y - 15 + int(math.sin(angle) * burst_r * 0.8)
                alpha = _NS_morgath._alpha(200 * (1 - t))
                _NS_morgath._jagged_line(surface, P["arc_darkest"],
                                         (x, y - 15), (end_x, end_y),
                                         jitter=6, segments=6, width=4)
                _NS_morgath._jagged_line(surface, P["arc_mid"],
                                         (x, y - 15), (end_x, end_y),
                                         jitter=6, segments=6, width=2)
                _NS_morgath._jagged_line(surface, P["arc_shine"],
                                         (x, y - 15), (end_x, end_y),
                                         jitter=4, segments=6, width=1)
                pygame.draw.rect(surface, (*P["white"], alpha),
                                 (end_x, end_y, 2, 2))
            for r_ in range(15, 0, -1):
                alpha = _NS_morgath._alpha(220 * (1 - t) * (15 - r_) / 15)
                _NS_morgath._aacircle(surface, (*P["arc_light"], alpha),
                                      (x, y - 15), int(r_ * fs))
        else:
            # ── STEADY/aftermath: bara naik + wisp spiral + glint orbit ──
            t = (progress - 0.45) / 0.55
            for i in range(16):
                rise_t = (phase * 0.7 + i * 0.06) % 1.0
                angle = i * math.pi * 2 / 16 + phase * 0.3
                r_sp = (52 + math.sin(phase + i) * 12) * fs
                rx = x + int(math.cos(angle) * r_sp)
                ry = y + 12 + int(math.sin(angle) * r_sp * 0.4) \
                    - int(rise_t * 30 * fs)
                alpha = _NS_morgath._alpha(210 * (1 - t)
                                           * (1 - rise_t * 0.5))
                if alpha > 0:
                    _NS_morgath._rect(surface, (*P["arc_light"], alpha),
                                      (rx, ry, 2, 2))
                    _NS_morgath._rect(surface, (*P["arc_shine"], alpha),
                                      (rx, ry, 1, 1))
            # wisp spiral 2 lengan
            for arm in range(2):
                for j in range(9):
                    a = phase * 2.2 + arm * math.pi + j * 0.38
                    rr = (24 + j * 7.5) * fs
                    al = int(150 * (1 - j / 9) * (1 - t * 0.4))
                    _NS_morgath._aacircle(
                        surface, (*P["flux_light"], al),
                        (int(x + math.cos(a) * rr),
                         int(y - 12 + math.sin(a) * rr * 0.55)), 2)
            # glint orbit di sekitar caster
            for i in range(3):
                a = phase * 1.1 + i * math.pi * 2 / 3
                rr = (40 + math.sin(phase * 1.7 + i) * 8) * fs
                _NS_morgath._rect(
                    surface, (*P["white"],
                              _NS_morgath._alpha(190 * (1 - t * 0.3))),
                    (int(x + math.cos(a) * rr),
                     int(y - 10 + math.sin(a) * rr * 0.5), 2, 2))
            # denyut pusat
            _NS_morgath._aacircle(
                surface,
                (*P["arc_hot"],
                 _NS_morgath._alpha(170 * math.sin(phase * 3) * 0.5 + 90)),
                (x, y - 10), int((28 + 6 * math.sin(phase * 3)) * fs))
            _NS_morgath._aacircle(
                surface, (*P["white"],
                          _NS_morgath._alpha(200 * math.sin(phase * 3)
                                             * 0.5 + 100)),
                (x, y - 10), int((12 + 4 * math.sin(phase * 3)) * fs))
# DRAKAR (AXE) - Mini Boss HD (Redesigned)
# ====================================================================
import math
import pygame


class _NS_drakar:
    """Namespace drakar — PIXEL MASTERWORK v3 (TRUE PIXEL-ART REWRITE).

    Rewrite penuh renderer _NS_drakar di bosses/level1.py.
    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.

    Upgrade dari v2:
    - RENDER   : badan digambar di kanvas art 120x120 lalu di-upscale 3x
                 nearest-neighbor -> piksel chunky konsisten (grid 3px),
                 selout gelap 8-arah, ramp hue-shift 5-6 band, war paint,
                 janggut kepang + cincin emas, pauldron berduri, kapak
                 double-bit besar yang berotasi penuh.
    - ANIMASI  : keyframe 5 fase untuk swing (windup -> apex hold ->
                 SLAM smear -> impact freeze + getar -> recover ease-out),
                 walk cycle dengan stride + lift kaki, idle napas dua
                 lapis + ember nafas kontinu, helix spin 4 putaran.
    - SWING    : trail tebasan diambil LANGSUNG dari path kepala kapak
                 (sampling keyframe mundur) -> smear menempel bilah,
                 leading edge putih panas + bintang percikan di ujung.
    - PROJECTILE: gelombang kejut tebasan (blood wave) meluncur maju dari
                 titik impact + serpihan balistik (chip) bergravitasi +
                 ember; murni visual, disimpan di boss._drk_projs.
    - SKILL FX : bahasa visual chunky-pixel baru untuk Q/W/E/R dengan 3
                 fase (aktivasi / steady / fade), semua world-space via
                 _fx_scale (kompensasi _render_scale, cap 2.6).
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # kulit crimson: shadow bergeser ungu, highlight bergeser oranye
        "skin_darkest": (52, 14, 28), "skin_dark": (108, 30, 36),
        "skin_mid": (172, 55, 42), "skin_light": (222, 100, 62),
        "skin_shine": (248, 150, 98), "skin_rim": (255, 198, 142),
        "hair_darkest": (10, 6, 14), "hair_dark": (32, 22, 32),
        "hair_mid": (64, 46, 54), "hair_light": (104, 80, 86),
        "leather_darkest": (24, 12, 8), "leather_dark": (58, 33, 18),
        "leather_mid": (99, 63, 36), "leather_light": (146, 102, 62),
        "armor_darkest": (16, 13, 20), "armor_dark": (44, 40, 52),
        "armor_mid": (88, 82, 98), "armor_light": (146, 138, 155),
        "armor_shine": (208, 202, 216),
        "blade_darkest": (20, 16, 26), "blade_dark": (58, 53, 70),
        "blade_mid": (120, 113, 134), "blade_light": (190, 183, 202),
        "blade_shine": (243, 240, 252),
        "blood_darkest": (46, 4, 16), "blood_dark": (112, 12, 26),
        "blood_mid": (188, 22, 38), "blood_light": (238, 54, 58),
        "blood_hot": (255, 102, 88), "blood_shine": (255, 182, 158),
        "rage_darkest": (64, 10, 10), "rage_dark": (146, 28, 16),
        "rage_mid": (224, 56, 28), "rage_light": (255, 112, 58),
        "rage_hot": (255, 184, 118),
        "eye_dark": (84, 28, 10), "eye_mid": (208, 92, 18),
        "eye_light": (255, 182, 58), "eye_glow": (255, 242, 182),
        "rune_dark": (34, 8, 12), "rune_mid": (150, 30, 32),
        "rune_light": (235, 74, 62),
        "gold_dark": (98, 66, 22), "gold_mid": (184, 138, 46),
        "gold_light": (240, 204, 96),
        "ember_dark": (142, 42, 10), "ember_mid": (224, 92, 20),
        "ember_light": (255, 172, 52), "ember_hot": (255, 222, 124),
        "bone_dark": (150, 140, 124), "bone_light": (216, 206, 188),
        "shadow": (0, 0, 0), "shadow_deep": (4, 2, 3),
        "white": (255, 255, 255),
    }

    # ── Konstanta rig ────────────────────────────────────────────────
    PIX = 2                    # 1 piksel art = 2 piksel native
    ART_W, ART_H = 120, 120    # kanvas art low-res
    BODY_W, BODY_H = 360, 360  # kanvas native (tetap 360; art dipusatkan)
    # Art (ART_W*PIX = 240 px) ditempel di dalam kanvas 360 pada offset ini.
    # Dipilih supaya telapak kaki art (y=100) tetap mendarat di garis tanah
    # native y+114 seperti sebelumnya -> SEMUA offset FX tanah tidak berubah,
    # hanya badannya yang mengecil ke proporsi keluarga mini boss.
    ART_OX, ART_OY = 60, 100
    ART_FY = 43                # art y yang sejajar dengan titik jangkar boss
    ANCHOR_DY = 58             # koreksi garis tanah 114 -> 56 (lihat draw_drakar)
    BODY_OX, BODY_OY = 180, 186
    AXE_LEN = 17               # jarak tangan depan -> pusat kepala kapak (art px)
    _RIG_SCALE = 1.0           # proporsi keluarga mini boss (dulu 1.5x)
    _STATIC_SURFACES = {}
    _DRK_TX = {}
    _DRK_ART = None            # buffer badan art-space
    _DRK_FIN = None            # buffer art-space + outline
    _DRK_SHADE = None          # gradien shading native (multiply)
    _DRK_SCL = None            # buffer art hasil upscale PIX x
    _DRK_OUT = None            # buffer native hasil komposit

    # ── Util dasar ───────────────────────────────────────────────────
    def _static(key, builder):
        surf = _NS_drakar._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_drakar._STATIC_SURFACES[key] = surf
        return surf

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(alpha))))

    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_drakar._clamp(
            (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t))

    def _hash01(i):
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = _NS_drakar._rgba(color, color[3])
        else:
            color = _NS_drakar._clamp(color)
        pygame.draw.circle(surface, color, (int(center[0]), int(center[1])),
                           max(1, int(radius)), width)

    def _aaline(surface, color, start, end, width=1):
        if len(color) == 4:
            color = _NS_drakar._rgba(color, color[3])
        else:
            color = _NS_drakar._clamp(color)
        pygame.draw.line(surface, color, start, end, max(1, int(width)))

    def _poly(surface, color, points):
        if len(points) >= 3:
            pygame.draw.polygon(surface, _NS_drakar._clamp(color), points)

    def _fx_scale(boss):
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    # ── Primitif FX chunky (grid 3px) ────────────────────────────────
    def _blk(surface, color, alpha, x, y, s=3):
        """Blok piksel world-space, di-snap ke grid 3px."""
        if alpha <= 0:
            return
        px = (int(x) // 3) * 3
        py = (int(y) // 3) * 3
        pygame.draw.rect(surface, _NS_drakar._rgba(color, alpha),
                         (px, py, max(1, int(s)), max(1, int(s))))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang percikan: ray blok chunky melangkah keluar."""
        if alpha <= 0 or size <= 0:
            return
        B = _NS_drakar
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            steps = max(2, int(ln / 4))
            for st in range(steps):
                t = (st + 1) / float(steps)
                bx = cx + math.cos(ang) * ln * t
                by = cy + math.sin(ang) * ln * t * 0.8
                B._blk(surface, color, alpha * (1.0 - t * 0.5), bx, by,
                       4 if (k % 2 == 0 and t < 0.6) else 3)
        if core:
            B._blk(surface, core, alpha, cx - 3, cy - 3, 7)
            B._blk(surface, B.PALETTE["white"], alpha, cx - 1, cy - 1, 3)

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Chevron '>' chunky menghadap sudut ang."""
        if alpha <= 0 or size <= 0:
            return
        B = _NS_drakar
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        for s in (-1, 1):
            steps = max(2, int(size / 3))
            for st in range(steps):
                t = st / float(steps)
                bx = cx + ca * size * t + px * s * size * 0.6 * (1 - t) - ca * size * 0.5
                by = cy + sa * size * t + py * s * size * 0.6 * (1 - t) - sa * size * 0.5
                B._blk(surface, color, alpha, bx, by, max(2, width))

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus chunky: tiap segmen = deret blok di busur."""
        if alpha <= 0 or radius <= 1:
            return
        B = _NS_drakar
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            blocks = max(2, int(radius * span / max(3, thick) * 0.45))
            for bl in range(blocks):
                a = a0 + (math.pi * 2 / segments * span) * bl / blocks
                bx = cx + math.cos(a) * radius
                by = cy + math.sin(a) * radius * squash
                B._blk(surface, color, alpha, bx, by, max(2, thick))

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah zigzag chunky 2 lapis (gelap + panas)."""
        if alpha <= 0 or length <= 0:
            return
        B = _NS_drakar
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(4):
            a += (B._hash01(seed * 7 + i * 13) - .5) * .9
            seg = length / 4.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .5
            pts.append((x, y))
        for i in range(len(pts) - 1):
            steps = max(2, int(length / 4 / 4))
            for st in range(steps):
                t = st / float(steps)
                bx = pts[i][0] + (pts[i+1][0] - pts[i][0]) * t
                by = pts[i][1] + (pts[i+1][1] - pts[i][1]) * t
                fade = 1.0 - (i + t) / 4.0 * 0.6
                B._blk(surface, colors[0], alpha * fade, bx - 1, by - 1,
                       width + 2)
                B._blk(surface, colors[1], alpha * fade, bx, by, width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Titik jumbai bergerigi di sepanjang spine (rambut/bulu)."""
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
                d = depth * (0.55 + 0.45 * _NS_drakar._hash01(i*7 + j*13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _drk_glow(radius, color, peak=190):
        """Tekstur glow radial (cache) untuk blit aditif."""
        key = (int(radius), color, int(peak))
        if key not in _NS_drakar._DRK_TX:
            r = max(2, int(radius))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            fmax = peak / 255.0
            for rad in range(r, 0, -2):
                t = 1.0 - rad / float(r)
                f = (t ** 1.8) * fmax
                pygame.draw.circle(
                    s, (int(color[0]*f), int(color[1]*f), int(color[2]*f), 255),
                    (r, r), rad)
            _NS_drakar._DRK_TX[key] = s
        return _NS_drakar._DRK_TX[key]

    # ═════════════════════════════════════════════════════════════════
    #  RIG v3 — pose keyframe (art px, selalu menghadap kanan)
    # ═════════════════════════════════════════════════════════════════
    def _drk_kf(action, phase, prog=0.0, spin=0.0):
        """Kunci pose: tangan depan (art px), sudut haft, offset badan.

        Swing 5 fase: windup (coil) -> apex hold (quiver) -> SLAM
        (ease-in kubik, sapuan 3.6 rad) -> impact freeze (getar
        teredam) -> recover (ease-out kembali ke idle).
        """
        if action == "attack":
            p = max(0.0, min(1.0, prog))
            if p < 0.16:                       # ── ANTICIPATION
                t = p / 0.16
                te = t * t * (3 - 2 * t)
                return {"hand": (76 - 12*te, 66 - 12*te),
                        "ang": -1.15 - 1.25*te,
                        "bdx": -3.0*te, "bdy": -1.0*te, "fury": te}
            if p < 0.34:                       # ── APEX HOLD + QUIVER
                t = (p - 0.16) / 0.18
                q = math.sin(p * 150.0) * 0.6 * t
                return {"hand": (64 + q, 54 - 1.5*t + q*0.5),
                        "ang": -2.40 - 0.15*t + q*0.04,
                        "bdx": -3.0, "bdy": -1.0 - 0.5*t, "fury": 1.0}
            if p < 0.47:                       # ── SLAM (smear)
                t = (p - 0.34) / 0.13
                te = t * t * t
                return {"hand": (64 + 7*te, 54 + 10*te),
                        "ang": -2.55 + 3.60*te,
                        "bdx": -3.0 + 10.0*te, "bdy": -1.5 + 2.5*te,
                        "fury": 1.0}
            if p < 0.62:                       # ── IMPACT FREEZE + getar
                t = (p - 0.47) / 0.15
                vib = math.sin(t * 28.0) * (1.0 - t)
                return {"hand": (71 + vib*0.7, 64),
                        "ang": 1.05 + vib*0.05,
                        "bdx": 7.0 + vib*0.6, "bdy": 1.0, "fury": 1.0 - t*0.5}
            t = (p - 0.62) / 0.38              # ── RECOVER (follow through)
            te = 1 - (1 - t) ** 2
            return {"hand": (71 + 5*te, 64 + 2*te),
                    "ang": 1.05 - 2.20*te,
                    "bdx": 7.0 - 7.0*te, "bdy": 1.0 - 1.0*te,
                    "fury": 0.5 - t*0.5}
        if action == "helix":
            return {"hand": (60 + math.cos(spin)*9.0, 63 + math.sin(spin)*3.5),
                    "ang": spin, "bdx": 0.0, "bdy": 2.0, "fury": 1.0}
        if action == "walk":
            stride = math.sin(phase * 2.0)
            return {"hand": (73, 64 + abs(stride) * 1.0),
                    "ang": -0.55 + stride * 0.12,
                    "bdx": 1.5, "bdy": abs(stride) * 1.0, "fury": 0.0}
        # idle: napas dua lapis; kapak rehat di bahu kanan (tidak
        # menutupi wajah)
        bob = math.sin(phase * 0.5) * 1.6
        return {"hand": (76, 66 + bob * 0.6),
                "ang": -1.15 + math.sin(phase * 0.5 + 1.2) * 0.06,
                "bdx": 0.0, "bdy": bob * 0.5, "fury": 0.0}

    # ── painter part (art px) ────────────────────────────────────────
    def _AF(A, key, x, y, w=1, h=1):
        A.fill(_NS_drakar.PALETTE[key], (int(x), int(y), max(1, int(w)),
                                         max(1, int(h))))

    def _art_arm(A, x0, y0, x1, y1, w, tone):
        """Lengan chunky: deret blok sepanjang garis dengan siku menekuk."""
        B = _NS_drakar
        mx = (x0 + x1) * 0.5
        my = (y0 + y1) * 0.5 + 2.5      # siku turun sedikit
        pts = []
        for seg in ((x0, y0, mx, my), (mx, my, x1, y1)):
            for st in range(5):
                t = st / 4.0
                pts.append((seg[0] + (seg[2]-seg[0])*t,
                            seg[1] + (seg[3]-seg[1])*t))
        dark, mid, lit = tone
        for (px, py) in pts:
            B._AF(A, dark, px - w*0.5 - 0.5, py - w*0.5 - 0.5, w + 1, w + 1)
        for (px, py) in pts:
            B._AF(A, mid, px - w*0.5, py - w*0.5, w, w)
        if lit:
            for (px, py) in pts[::2]:
                B._AF(A, lit, px - w*0.5, py - w*0.5, max(1, w-1), 1)

    def _art_fist(A, x, y):
        B = _NS_drakar
        B._AF(A, "skin_darkest", x - 2.5, y - 2.5, 5, 5)
        B._AF(A, "skin_dark", x - 2, y - 2, 4, 4)
        B._AF(A, "skin_mid", x - 1.5, y - 1.5, 2, 2)
        B._AF(A, "leather_darkest", x - 2, y + 0.5, 4, 1)

    def _art_leg(A, hx, hy, front, lift, shift):
        """Kaki: paha kulit -> shin -> boot kulit berbulu + toe cap besi."""
        B = _NS_drakar
        x = hx + shift
        y = hy - lift
        skin = ("skin_mid", "skin_light") if front else ("skin_dark", "skin_mid")
        boot = ("leather_dark", "leather_mid") if front else \
               ("leather_darkest", "leather_dark")
        # paha
        B._AF(A, "skin_darkest", x - 3.5, hy - 1, 8, 5)
        B._AF(A, skin[0], x - 3, hy - 1, 7, 4)
        B._AF(A, skin[1], x - 2, hy - 1, 3, 2)
        # shin
        B._AF(A, "skin_darkest", x - 3, hy + 3, 7, 5 - lift * 0.5)
        B._AF(A, skin[0], x - 2.5, hy + 3, 6, 4 - lift * 0.5)
        # boot bulu
        B._AF(A, "leather_darkest", x - 4, y + 7, 10, 6)
        B._AF(A, boot[0], x - 3.5, y + 7.5, 9, 5)
        B._AF(A, boot[1], x - 3, y + 8, 5, 2)
        # bulu atas boot (jumbai)
        for i in range(4):
            fx = x - 3.5 + i * 2.4
            fh = 1 + int(B._hash01(int(fx) * 7 + (3 if front else 11)) * 2)
            B._AF(A, "hair_mid" if front else "hair_dark", fx, y + 6 - fh + 1,
                  2, fh + 1)
        # toe cap besi ke depan
        B._AF(A, "armor_darkest", x + 4, y + 10, 4, 3)
        B._AF(A, "armor_mid" if front else "armor_dark", x + 4, y + 10, 3, 2)
        if front:
            B._AF(A, "armor_shine", x + 4, y + 10, 1, 1)
        # strap
        B._AF(A, "leather_darkest", x - 4, y + 9, 10, 1)
        B._AF(A, "gold_mid" if front else "gold_dark", x - 1, y + 9, 1, 1)

    def _art_waist(A, dx, dy):
        """Sabuk + buckle tengkorak emas + loincloth robek."""
        B = _NS_drakar
        x = 60 + dx * 0.5
        y = 73 + dy * 0.5
        B._AF(A, "leather_darkest", x - 10, y, 20, 4)
        B._AF(A, "leather_dark", x - 9, y, 18, 3)
        B._AF(A, "leather_mid", x - 8, y, 7, 1)
        for sx in (-7, 7):
            B._AF(A, "armor_dark", x + sx, y + 1, 2, 2)
            B._AF(A, "armor_light", x + sx, y + 1, 1, 1)
        # buckle tengkorak
        B._AF(A, "gold_dark", x - 3, y - 1, 6, 5)
        B._AF(A, "gold_mid", x - 2, y, 4, 3)
        B._AF(A, "gold_light", x - 2, y, 2, 1)
        B._AF(A, "leather_darkest", x - 1.5, y + 1, 1, 1)
        B._AF(A, "leather_darkest", x + 0.5, y + 1, 1, 1)
        # loincloth: flap depan dengan hem robek + noda darah
        B._AF(A, "leather_darkest", x - 5, y + 4, 10, 7)
        B._AF(A, "leather_dark", x - 4, y + 4, 8, 6)
        B._AF(A, "leather_mid", x - 3, y + 4, 4, 4)
        for i in range(5):
            hx = x - 5 + i * 2
            hh = 1 + (i % 2)
            B._AF(A, "leather_darkest", hx, y + 10, 2, hh)
        B._AF(A, "blood_dark", x + 1, y + 7, 2, 2)
        B._AF(A, "blood_mid", x + 1, y + 7, 1, 1)

    def _art_torso(A, dx, dy, breath, rage=False, hunger=False):
        """Torso barbarian masif: pecs, abs, scar, war paint, strap."""
        B = _NS_drakar
        x = 60 + dx
        y = 55 + dy - breath * 0.5
        skin = "skin_mid"
        # siluet dasar (taper bahu -> pinggang)
        rows = ((0, -14, 14), (1, -14, 14), (2, -14, 14), (3, -13.5, 13.5),
                (4, -13, 13), (5, -13, 13), (6, -12.5, 12.5), (7, -12, 12),
                (8, -12, 12), (9, -11.5, 11.5), (10, -11, 11), (11, -10.5, 10.5),
                (12, -10, 10), (13, -9.5, 9.5), (14, -9, 9), (15, -8.5, 8.5),
                (16, -8.5, 8.5), (17, -8, 8), (18, -8, 8), (19, -8, 8))
        for (ry, x0, x1) in rows:
            B._AF(A, "skin_darkest", x + x0 - 0.5, y + ry, x1 - x0 + 1, 1)
        for (ry, x0, x1) in rows:
            B._AF(A, "skin_dark", x + x0, y + ry, x1 - x0, 1)
        for (ry, x0, x1) in rows[1:]:
            B._AF(A, skin, x + x0 + 1.5, y + ry, x1 - x0 - 3, 1)
        # key light kiri-atas: band terang sisi kiri
        for (ry, x0, x1) in rows[1:12]:
            B._AF(A, "skin_light", x + x0 + 2, y + ry, 3.5, 1)
        # pecs
        B._AF(A, "skin_light", x - 9, y + 3, 8, 4)
        B._AF(A, "skin_light", x + 1, y + 3, 8, 4)
        B._AF(A, "skin_shine", x - 8, y + 3, 4, 1)
        B._AF(A, "skin_shine", x + 2, y + 3, 3, 1)
        B._AF(A, "skin_darkest", x - 0.5, y + 2, 1, 6)
        B._AF(A, "skin_dark", x - 9, y + 7, 8, 1)
        B._AF(A, "skin_dark", x + 1, y + 7, 8, 1)
        # abs 2x3
        for r in range(3):
            ay = y + 9 + r * 3
            B._AF(A, "skin_dark", x - 5, ay + 2, 10, 1)
            B._AF(A, "skin_light", x - 4, ay, 3.5, 1)
            B._AF(A, "skin_light", x + 1.5, ay, 3.5, 1)
        B._AF(A, "skin_darkest", x - 0.5, y + 9, 1, 9)
        # scar diagonal lama
        for i in range(4):
            B._AF(A, "skin_rim", x + 3 + i * 1.5, y + 2 + i, 1.5, 1)
        # war paint tulang: 3 cakar diagonal dada kiri
        for k in range(3):
            for i in range(4):
                B._AF(A, "bone_light" if i < 3 else "bone_dark",
                      x - 11 + k * 2.6 + i, y + 3.2 + i * 1.4, 1.6, 1.2)
        # strap bahu kanan -> pinggang kiri + stud emas
        for st in range(9):
            t = st / 8.0
            sx = x + 11 - 20 * t
            sy = y + 1 + 17 * t
            B._AF(A, "leather_darkest", sx - 1.7, sy - 0.5, 3.6, 2.4)
            B._AF(A, "leather_dark", sx - 1.2, sy - 0.2, 2.6, 1.6)
        for st in (0.15, 0.5, 0.85):
            sx = x + 11 - 20 * st
            sy = y + 1 + 17 * st
            B._AF(A, "gold_mid", sx - 0.6, sy, 1.4, 1.4)
            B._AF(A, "gold_light", sx - 0.6, sy, 0.9, 0.9)
        # crest rune di sternum: menyala saat rage / battle hunger
        if rage or hunger:
            B._AF(A, "rune_dark", x - 1.6, y + 7.4, 4, 4)
            B._AF(A, "rune_light", x - 0.6, y + 7.9, 2, 3)
            B._AF(A, "rage_hot", x, y + 8.7, 1, 1)
        else:
            B._AF(A, "rune_dark", x - 1, y + 7.7, 2.5, 3)
            B._AF(A, "rune_mid", x - 0.4, y + 8.4, 1.2, 1.5)
        # trap otot leher
        B._AF(A, "skin_dark", x - 8, y - 1.5, 6, 2)
        B._AF(A, "skin_dark", x + 2, y - 1.5, 6, 2)
        B._AF(A, "skin_light", x - 7, y - 1.5, 3, 1)

    def _art_pauldron(A, cx, cy):
        """Pauldron besi berduri: plat membulat menempel sudut bahu."""
        B = _NS_drakar
        # duri (pendek, dari mahkota plat)
        for (sx, sy, ex, ey) in ((cx - 3, cy, cx - 6.5, cy - 5),
                                 (cx + 0.5, cy - 1, cx + 0.2, cy - 6.5),
                                 (cx + 4, cy, cx + 6.5, cy - 5)):
            steps = 4
            for st in range(steps):
                t = st / float(steps - 1)
                w = 2.2 - t * 1.5
                px = sx + (ex - sx) * t
                py = sy + (ey - sy) * t
                B._AF(A, "armor_darkest", px - w/2 - 0.4, py - 0.4, w + 0.8, 1.7)
                B._AF(A, "armor_dark", px - w/2, py, w, 1)
            B._AF(A, "armor_light", ex, ey, 1, 1)
        # plat membulat: baris bertumpuk melebar lalu menyempit
        rows = ((0, -3.5, 3.5), (1, -4.5, 4.5), (2, -5.5, 5.5), (3, -6, 6),
                (4, -6, 6), (5, -5.5, 5.5), (6, -5, 5))
        for (ry, x0, x1) in rows:
            B._AF(A, "armor_darkest", cx + x0 - 0.6, cy + ry, x1 - x0 + 1.2, 1.2)
        for (ry, x0, x1) in rows:
            B._AF(A, "armor_dark", cx + x0, cy + ry, x1 - x0, 1)
        for (ry, x0, x1) in rows[1:5]:
            B._AF(A, "armor_mid", cx + x0 + 1, cy + ry, x1 - x0 - 2.6, 1)
        B._AF(A, "armor_light", cx - 3.5, cy + 1.4, 4, 1.6)
        B._AF(A, "armor_shine", cx - 2.6, cy + 1.6, 1.6, 0.9)
        # lame bawah + rivet
        B._AF(A, "armor_darkest", cx - 4.5, cy + 7, 9.5, 2.2)
        B._AF(A, "armor_dark", cx - 4, cy + 7, 8.5, 1.6)
        for rx in (-3, 0.5, 4):
            B._AF(A, "armor_darkest", cx + rx, cy + 3, 1.3, 1.3)
            B._AF(A, "armor_shine", cx + rx, cy + 3, 0.7, 0.7)

    def _art_head(A, dx, dy, phase, fury=0.0, hunger=False):
        """Kepala: mane liar, brow berat, mata bara, janggut kepang."""
        B = _NS_drakar
        x = 60 + dx
        y = 39 + dy
        blink = (math.sin(phase * 0.5 + 2.3) > 0.985)
        # mane rambut liar tersapu ke belakang (kiri)
        mane = ((x - 16, y + 3, 5, 4), (x - 13, y, 6, 5), (x - 9, y - 3, 7, 5),
                (x - 4, y - 4, 8, 4), (x + 3, y - 3, 6, 3))
        for (mx, my, mw, mh) in mane:
            B._AF(A, "hair_darkest", mx - 0.5, my - 0.5, mw + 1, mh + 1)
        for (mx, my, mw, mh) in mane:
            B._AF(A, "hair_dark", mx, my, mw, mh)
        B._AF(A, "hair_mid", x - 8, y - 2, 8, 2)
        B._AF(A, "hair_mid", x - 13, y + 1, 5, 2)
        B._AF(A, "hair_light", x - 6, y - 2, 4, 1)
        B._AF(A, "hair_light", x - 11, y + 1.4, 2.6, 0.9)
        B._AF(A, "hair_mid", x + 3, y - 2.4, 4, 1.4)
        # jumbai runcing belakang (sway pelan)
        sw = math.sin(phase * 0.5) * 1.2
        for k in range(3):
            tx = x - 15 - k * 2 + sw * (0.4 + k * 0.3)
            ty = y + 4 + k * 2.6
            B._AF(A, "hair_darkest", tx - 1, ty, 4 - k, 2)
            B._AF(A, "hair_dark", tx, ty, 3 - k, 1)
        # tengkorak
        B._AF(A, "skin_darkest", x - 6.5, y, 13.5, 14)
        B._AF(A, "skin_dark", x - 6, y + 0.5, 12.5, 13)
        B._AF(A, "skin_mid", x - 5, y + 1, 11, 11)
        B._AF(A, "skin_light", x - 4.5, y + 1, 10, 3)
        B._AF(A, "skin_shine", x - 3, y + 1.4, 4, 1)
        # war paint garis tulang vertikal melewati mata kanan
        B._AF(A, "bone_light", x + 3.6, y + 0.5, 1.4, 3.4)
        B._AF(A, "bone_dark", x + 3.6, y + 7, 1.4, 2.6)
        # brow berat (tipis tapi gelap)
        B._AF(A, "skin_darkest", x - 5, y + 4, 11, 1.2)
        # mata: bara oranye besar; menyala saat fury
        if not blink:
            B._AF(A, "skin_darkest", x - 4.6, y + 5.2, 3.4, 2.4)
            B._AF(A, "eye_mid", x - 4, y + 5.4, 2.2, 1.8)
            B._AF(A, "eye_light", x - 3.4, y + 5.4, 1.2, 1.2)
            B._AF(A, "skin_darkest", x + 1.4, y + 5.2, 3.8, 2.6)
            B._AF(A, "eye_mid", x + 2, y + 5.4, 2.6, 2)
            B._AF(A, "eye_light", x + 2.6, y + 5.4, 1.6, 1.4)
            B._AF(A, "eye_glow", x + 3, y + 5.4, 0.9, 0.9)
            if fury > 0.4 or hunger:
                B._AF(A, "eye_glow", x + 2, y + 4.8, 2.6, 1)
                B._AF(A, "eye_glow", x - 4, y + 4.8, 2.2, 1)
        else:
            B._AF(A, "skin_darkest", x - 4.4, y + 5.8, 3, 1)
            B._AF(A, "skin_darkest", x + 1.6, y + 5.8, 3.4, 1)
        # hidung + nostril flare
        B._AF(A, "skin_dark", x - 0.6, y + 6.6, 2.2, 2.6)
        B._AF(A, "skin_light", x - 0.2, y + 6.8, 1, 1.2)
        B._AF(A, "skin_darkest", x + 1.2, y + 8.4, 0.9, 0.9)
        # anting emas telinga kiri
        B._AF(A, "skin_dark", x - 7.4, y + 5.6, 2, 3)
        B._AF(A, "gold_mid", x - 7.8, y + 8.4, 1.4, 2)
        B._AF(A, "gold_light", x - 7.8, y + 8.4, 0.8, 1)
        # janggut kepang besar + 2 cincin emas (ramp 4 tone agar terbaca)
        bx = x + 0.5
        by = y + 10
        B._AF(A, "hair_darkest", bx - 6.5, by, 13, 5)
        B._AF(A, "hair_darkest", bx - 5, by + 5, 10, 4)
        B._AF(A, "hair_darkest", bx - 3, by + 9, 6, 4)
        B._AF(A, "hair_darkest", bx - 1.5, by + 13, 3, 3)
        B._AF(A, "hair_dark", bx - 5.5, by + 0.5, 11, 4)
        B._AF(A, "hair_dark", bx - 4, by + 5, 8, 3.6)
        B._AF(A, "hair_dark", bx - 2.2, by + 9, 4.4, 3.4)
        B._AF(A, "hair_mid", bx - 4.5, by + 1, 8, 2.6)
        B._AF(A, "hair_mid", bx - 3, by + 5.5, 5.4, 2.2)
        B._AF(A, "hair_mid", bx - 1.6, by + 9.4, 3, 2)
        B._AF(A, "hair_light", bx - 3.4, by + 1.4, 4.4, 1)
        B._AF(A, "hair_light", bx - 2, by + 6, 2.4, 0.9)
        # tekstur helai vertikal
        for i in range(4):
            B._AF(A, "hair_darkest", bx - 4 + i * 2.4, by + 1.5, 0.9, 3)
        # kumis
        B._AF(A, "hair_dark", bx - 5, by - 1.2, 4, 1.4)
        B._AF(A, "hair_dark", bx + 1.4, by - 1.2, 4, 1.4)
        # cincin emas kepang
        B._AF(A, "gold_dark", bx - 2.4, by + 4.4, 5, 1.6)
        B._AF(A, "gold_mid", bx - 1.8, by + 4.6, 3.6, 1.2)
        B._AF(A, "gold_light", bx - 1.2, by + 4.6, 1.4, 0.8)
        B._AF(A, "gold_dark", bx - 1.8, by + 8.6, 3.8, 1.4)
        B._AF(A, "gold_mid", bx - 1.2, by + 8.8, 2.6, 1)

    def _art_axe(A, hx, hy, ang, blood=0.0, rage=False):
        """Kapak double-bit besar: haft kayu berbungkus kulit, pommel
        emas, dua bilah crescent berlapis 4 band + edge shine, spike
        atas, rune bilah menyala saat rage."""
        B = _NS_drakar
        ca, sa = math.cos(ang), math.sin(ang)
        pxv, pyv = -sa, ca                     # tegak lurus haft
        cxh = hx + ca * B.AXE_LEN              # pusat kepala kapak
        cyh = hy + sa * B.AXE_LEN

        def L(u, v):
            return (cxh + ca * u + pxv * v, cyh + sa * u + pyv * v)

        # ── haft ──
        pom = (hx - ca * 8, hy - sa * 8)
        steps = 9
        for st in range(steps + 1):
            t = st / float(steps)
            qx = pom[0] + (cxh - pom[0]) * t
            qy = pom[1] + (cyh - pom[1]) * t
            B._AF(A, "leather_darkest", qx - 1.6, qy - 1.6, 3.2, 3.2)
        for st in range(steps + 1):
            t = st / float(steps)
            qx = pom[0] + (cxh - pom[0]) * t
            qy = pom[1] + (cyh - pom[1]) * t
            B._AF(A, "leather_dark", qx - 1.1, qy - 1.1, 2.2, 2.2)
            if st % 2 == 0:
                B._AF(A, "leather_mid", qx - 1.1, qy - 1.1, 1.2, 1.2)
        # pommel emas
        B._AF(A, "gold_dark", pom[0] - 2.2, pom[1] - 2.2, 4.6, 4.6)
        B._AF(A, "gold_mid", pom[0] - 1.6, pom[1] - 1.6, 3.4, 3.4)
        B._AF(A, "gold_light", pom[0] - 1, pom[1] - 1, 1.6, 1.6)

        # ── collar besi di bawah kepala ──
        cx2, cy2 = L(-4.5, 0)
        B._AF(A, "armor_darkest", cx2 - 2.4, cy2 - 2.4, 5, 5)
        B._AF(A, "armor_mid", cx2 - 1.6, cy2 - 1.6, 3.4, 3.4)
        B._AF(A, "armor_shine", cx2 - 1, cy2 - 1, 1.2, 1.2)

        # ── dua bilah crescent (double-bit): cheek gelap, edge terang ──
        base = ((-4, 1.5), (-7, 4.5), (-6.5, 9), (-1, 11.5),
                (5, 9.5), (6, 4.5), (3.5, 1.5))
        for s in (1, -1):
            pts = [L(u, v * s) for (u, v) in base]
            cxm = sum(p[0] for p in pts) / len(pts)
            cym = sum(p[1] for p in pts) / len(pts)

            def inset(f):
                return [(cxm + (p[0]-cxm)*f, cym + (p[1]-cym)*f) for p in pts]

            B._poly(A, B.PALETTE["blade_darkest"], pts)
            B._poly(A, B.PALETTE["blade_dark"], inset(0.88))
            B._poly(A, B.PALETTE["blade_mid"], inset(0.70))
            B._poly(A, B.PALETTE["blade_dark"], inset(0.38))
            # edge band terang + shine di busur pemotong
            e0 = L(-6.5, 9 * s)
            e1 = L(-1, 11.5 * s)
            e2 = L(5, 9.5 * s)
            pygame.draw.line(A, B.PALETTE["blade_light"],
                             (int(e0[0]), int(e0[1])), (int(e1[0]), int(e1[1])), 2)
            pygame.draw.line(A, B.PALETTE["blade_light"],
                             (int(e1[0]), int(e1[1])), (int(e2[0]), int(e2[1])), 2)
            pygame.draw.line(A, B.PALETTE["blade_shine"],
                             (int(e0[0]), int(e0[1])), (int(e1[0]), int(e1[1])), 1)
            pygame.draw.line(A, B.PALETTE["blade_shine"],
                             (int(e1[0]), int(e1[1])), (int(e2[0]), int(e2[1])), 1)
            # notch bekas tempur di edge
            nx, ny = L(1.5, 10.4 * s)
            B._AF(A, "blade_darkest", nx - 0.8, ny - 0.8, 1.6, 1.6)
            # rune bilah
            rx, ry = L(-1, 5.5 * s)
            if rage:
                B._AF(A, "rune_light", rx - 1.4, ry - 0.5, 3, 1)
                B._AF(A, "rune_light", rx - 0.5, ry - 1.4, 1, 3)
                B._AF(A, "rage_hot", rx - 0.5, ry - 0.5, 1, 1)
            else:
                B._AF(A, "rune_mid", rx - 1, ry - 0.4, 2.2, 0.9)
                B._AF(A, "rune_dark", rx - 0.4, ry - 1, 0.9, 2.2)
            # darah di edge saat swing
            if blood > 0.05:
                for i in range(3):
                    bt = 0.2 + i * 0.3
                    bx = e0[0] + (e2[0]-e0[0]) * bt
                    by = e0[1] + (e2[1]-e0[1]) * bt
                    if B._hash01(i * 17 + s * 5) < blood + 0.3:
                        B._AF(A, "blood_mid", bx - 0.8, by - 0.8, 1.8, 1.8)
                        B._AF(A, "blood_light", bx - 0.4, by - 0.4, 0.9, 0.9)
        # spike atas (kecil, runcing)
        t0 = L(2, 0)
        t1 = L(7.5, 0)
        for st in range(5):
            t = st / 4.0
            w = 2.0 - t * 1.6
            qx = t0[0] + (t1[0]-t0[0]) * t
            qy = t0[1] + (t1[1]-t0[1]) * t
            B._AF(A, "blade_dark", qx - w/2 - 0.4, qy - w/2 - 0.4, w + 0.8, w + 0.8)
            B._AF(A, "blade_light", qx - w/2, qy - w/2, w, w)
        B._AF(A, "blade_shine", t1[0] - 0.6, t1[1] - 0.6, 1.2, 1.2)

    def _draw_drk_art(A, action, phase, prog=0.0, spin=0.0, rage=False,
                      hunger=False, callb=False):
        """Kompositor badan penuh di kanvas art 120x120 (hadap kanan)."""
        B = _NS_drakar
        kf = B._drk_kf(action, phase, prog, spin)
        hx, hy = kf["hand"]
        ang = kf["ang"]
        bdx, bdy = kf["bdx"], kf["bdy"]
        fury = kf.get("fury", 0.0)
        ca, sa = math.cos(ang), math.sin(ang)
        back_hand = (hx - ca * 5, hy - sa * 5)

        # kaki (planted; walk = stride + lift)
        if action == "walk":
            st = math.sin(phase * 2.0)
            B._art_leg(A, 53, 76, False, max(0.0, -st) * 2.2, -st * 4.5)
            B._art_leg(A, 67, 76, True, max(0.0, st) * 2.2, st * 4.5)
        elif action == "helix":
            B._art_leg(A, 51, 76, False, 1.0, math.cos(spin) * 2.0)
            B._art_leg(A, 69, 76, True, 1.0, -math.cos(spin) * 2.0)
        else:
            B._art_leg(A, 53, 76, False, 0.0, bdx * 0.3)
            B._art_leg(A, 67, 76, True, 0.0, bdx * 0.5)
        # lengan belakang (di bawah torso)
        B._art_arm(A, 49 + bdx, 57 + bdy, back_hand[0], back_hand[1], 3,
                   ("skin_darkest", "skin_dark", None))
        # pinggang + loincloth
        B._art_waist(A, bdx, bdy)
        # torso
        breath = math.sin(phase * 0.5 + 0.9) if action == "idle" else 0.0
        B._art_torso(A, bdx, bdy, breath, rage=rage, hunger=hunger)
        # pauldron bahu belakang (duduk di atas garis bahu)
        B._art_pauldron(A, 46 + bdx, 53 + bdy)
        # kepala
        B._art_head(A, bdx * 1.1, bdy * 1.2, phase, fury=fury, hunger=hunger)
        # kapak (di atas kepala/torso, di bawah lengan depan)
        blood = fury if action == "attack" and prog > 0.4 else 0.0
        B._art_axe(A, hx, hy, ang, blood=blood, rage=rage or hunger)
        # kepalan belakang di haft
        B._art_fist(A, back_hand[0], back_hand[1])
        # bahu depan bare + armband emas
        x0, y0 = 71 + bdx, 56 + bdy
        B._AF(A, "skin_darkest", x0 - 3.5, y0 - 3, 8, 7)
        B._AF(A, "skin_mid", x0 - 3, y0 - 2.5, 7, 6)
        B._AF(A, "skin_light", x0 - 2.5, y0 - 2, 4, 3)
        B._AF(A, "skin_shine", x0 - 2, y0 - 1.6, 2, 1)
        # lengan depan
        B._art_arm(A, x0, y0 + 1, hx, hy, 4,
                   ("skin_darkest", "skin_mid", "skin_light"))
        # armband emas di bicep depan
        abx = x0 + (hx - x0) * 0.3
        aby = y0 + 1 + (hy - y0 - 1) * 0.3
        B._AF(A, "gold_dark", abx - 2.4, aby - 1.6, 5, 3)
        B._AF(A, "gold_mid", abx - 2, aby - 1.2, 4, 2)
        B._AF(A, "gold_light", abx - 1.6, aby - 1.2, 1.6, 1)
        # kepalan depan
        B._art_fist(A, hx, hy)
        # glint armor saat berserker's call
        if callb:
            gl = int(phase * 6) % 3
            gx, gy = ((46, 53), (60, 74), (71, 55))[gl]
            B._AF(A, "white", gx, gy, 1.4, 1.4)
            B._AF(A, "armor_shine", gx - 1, gy, 3.4, 1)
            B._AF(A, "armor_shine", gx, gy - 1, 1, 3.4)

    # ── pipeline: art -> outline -> scale 3x -> shade -> flash ──────
    def _drk_body_surface(mode, facing, phase_q, prog_q, flash=0, **kwargs):
        B = _NS_drakar
        if B._DRK_ART is None:
            B._DRK_ART = pygame.Surface((B.ART_W, B.ART_H), pygame.SRCALPHA)
            B._DRK_FIN = pygame.Surface((B.ART_W, B.ART_H), pygame.SRCALPHA)
        A = B._DRK_ART
        F = B._DRK_FIN
        A.fill((0, 0, 0, 0))
        F.fill((0, 0, 0, 0))

        rage = bool(kwargs.get("rage_mode") or kwargs.get("battlehunger"))
        hunger = bool(kwargs.get("battlehunger"))
        callb = bool(kwargs.get("berserk_call"))
        if mode == "attack":
            B._draw_drk_art(A, "attack", phase_q, prog=prog_q, rage=rage,
                            hunger=hunger, callb=callb)
        elif mode == "walk":
            B._draw_drk_art(A, "walk", phase_q, rage=rage, hunger=hunger,
                            callb=callb)
        elif mode == "helix":
            spin = prog_q * math.pi * 8
            B._draw_drk_art(A, "helix", phase_q, prog=prog_q, spin=spin,
                            rage=True, hunger=hunger, callb=callb)
        else:
            B._draw_drk_art(A, "idle", phase_q, rage=rage, hunger=hunger,
                            callb=callb)

        # selout: outline gelap 8 arah di art-space
        mask = pygame.mask.from_surface(A, 40)
        oc = (26, 8, 16, 255) if not rage else (54, 12, 10, 255)
        osurf = mask.to_surface(setcolor=oc, unsetcolor=(0, 0, 0, 0))
        for (ox, oy) in ((-1, 0), (1, 0), (0, -1), (0, 1),
                         (-1, -1), (1, -1), (-1, 1), (1, 1)):
            F.blit(osurf, (ox, oy))
        F.blit(A, (0, 0))

        # hurt flash (art-space, murah)
        if flash > 0:
            w = int(235 * min(1.0, flash / 8.0))
            if w > 0:
                wht = mask.to_surface(
                    setcolor=(w, int(w * 0.92), int(w * 0.82), 255),
                    unsetcolor=(0, 0, 0, 0))
                F.blit(wht, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # upscale nearest PIX× -> piksel chunky, lalu tempel di kanvas native
        aw, ah = B.ART_W * B.PIX, B.ART_H * B.PIX
        scl = pygame.transform.scale(F, (aw, ah), B._DRK_SCL) \
            if B._DRK_SCL is not None else pygame.transform.scale(F, (aw, ah))
        B._DRK_SCL = scl
        out = B._DRK_OUT
        if out is None:
            out = pygame.Surface((B.BODY_W, B.BODY_H), pygame.SRCALPHA)
            B._DRK_OUT = out
        out.fill((0, 0, 0, 0))
        out.blit(scl, (B.ART_OX, B.ART_OY))

        # gradien shading vertikal (cache)
        if B._DRK_SHADE is None:
            sh = pygame.Surface((B.BODY_W, B.BODY_H), pygame.SRCALPHA)
            for yy in range(B.BODY_H):
                v = int(255 - 52 * (yy / float(B.BODY_H)))
                pygame.draw.line(sh, (v, v, v, 255), (0, yy), (B.BODY_W, yy))
            B._DRK_SHADE = sh
        out.blit(B._DRK_SHADE, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # ember bara kontinu (native res) — badan selalu "bernafas api"
        emb_seed = phase_q * 0.53 + prog_q * 1.7
        for k in range(3):
            tt = (emb_seed + k * 0.37) % 1.0
            if tt >= 0.85:
                continue
            ex = 180 + math.sin(phase_q * 1.3 + k * 2.1 + prog_q * 5) * 18
            ey = 182 - tt * 12
            c = B.PALETTE["ember_mid"] if k % 2 == 0 else B.PALETTE["ember_light"]
            pygame.draw.rect(out, (*c, 255), (int(ex), int(ey), 2, 2))
            pygame.draw.rect(out, (*B.PALETTE["ember_hot"], 255),
                             (int(ex) + 1, int(ey) + 1, 1, 1))
        return out

    # ── grip export (dipakai trail & tools; koordinat native) ────────
    def _compute_two_handed_grip(cx, cy, facing, phase, action,
                                 attack_progress=0, spin_angle=0):
        B = _NS_drakar
        prog = attack_progress
        if action == "helix":
            kf = B._drk_kf("helix", phase, prog, spin_angle)
        else:
            kf = B._drk_kf(action, phase, prog, spin_angle)
        hx, hy = kf["hand"]
        ang = kf["ang"]
        ca, sa = math.cos(ang), math.sin(ang)

        def cvt(px_, py_):
            return (cx + facing * (px_ - 60) * B.PIX,
                    cy + (py_ - B.ART_FY) * B.PIX)

        head = cvt(hx + ca * B.AXE_LEN, hy + sa * B.AXE_LEN)
        return {"axe_head": head, "axe_angle": ang,
                "pommel": cvt(hx - ca * 8, hy - sa * 8),
                "front_hand": cvt(hx, hy),
                "back_hand": cvt(hx - ca * 5, hy - sa * 5)}

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                    * getattr(boss, "direction", 1)), int(y))

    # ═════════════════════════════════════════════════════════════════
    #  SWING ATTACK — trail smear dari path kapak + impact burst
    # ═════════════════════════════════════════════════════════════════
    def _draw_axe_slash_trail(surface, boss, cx, cy, progress):
        """Trail tebasan v3: sampling keyframe mundur -> quad smear yang
        MENEMPEL pada path kepala kapak, ramp darah -> leading edge
        putih panas + bintang percikan di bilah."""
        B = _NS_drakar
        if progress < 0.36 or progress > 0.74:
            return
        facing = int(getattr(boss, "_drk_attack_dir",
                             getattr(boss, "direction", 1))) or 1
        phase = float(getattr(boss, "pulse", 0.0))
        # kekuatan trail: penuh di slam+impact, luruh saat recover
        if progress < 0.62:
            strength = min(1.0, (progress - 0.36) / 0.06)
        else:
            strength = max(0.0, 1.0 - (progress - 0.62) / 0.12)
        if strength <= 0:
            return
        # sampel path kepala kapak mundur (8 titik rapat ~100° busur SLAM)
        heads = []
        for k in range(8):
            pk = progress - k * 0.011
            if pk < 0.345:
                break
            g = B._compute_two_handed_grip(cx, cy, facing, phase, "attack", pk)
            heads.append(g["axe_head"])
        if len(heads) < 3:
            return
        # crescent solid: strip antara path luar & path yang ditarik ke
        # pivot ayunan — tanpa bowtie, ramp darah dari luar ke dalam
        pivot = (cx, cy - 26)
        n = len(heads)

        def strip(pull_out, pull_in, tail):
            outer = []
            inner = []
            for k, (hx0, hy0) in enumerate(heads[:tail]):
                fo = pull_out * (1.0 + k * 0.05)
                fi = pull_in * (1.0 + k * 0.07)
                outer.append((hx0 + (pivot[0]-hx0)*fo, hy0 + (pivot[1]-hy0)*fo))
                inner.append((hx0 + (pivot[0]-hx0)*fi, hy0 + (pivot[1]-hy0)*fi))
            return outer + inner[::-1]

        a = B._alpha(235 * strength)
        B._poly(surface, B.PALETTE["blood_darkest"], strip(-0.06, 0.44, n))
        B._poly(surface, B.PALETTE["blood_dark"], strip(-0.03, 0.36, n))
        B._poly(surface, B.PALETTE["blood_mid"], strip(0.0, 0.27, max(3, n - 2)))
        B._poly(surface, B.PALETTE["blood_light"],
                strip(0.02, 0.15, max(3, n - 5)))
        # leading edge putih panas
        hx, hy = heads[0]
        x1, y1 = heads[min(2, len(heads) - 1)]
        pygame.draw.line(surface, B.PALETTE["blood_hot"],
                         (int(hx), int(hy)), (int(x1), int(y1)), 5)
        pygame.draw.line(surface, B.PALETTE["blood_shine"],
                         (int(hx), int(hy)), (int(x1), int(y1)), 2)
        B._spark_star(surface, hx, hy, 13 * strength,
                      B.PALETTE["blood_light"], 235 * strength,
                      spikes=4, rot=progress * 9,
                      core=B.PALETTE["blood_hot"])

    def _draw_impact_burst(surface, boss, cx, cy, progress):
        """Ledakan impact: shock ellipse chunky + retak tanah + debu."""
        B = _NS_drakar
        t = max(0.0, min(1.0, (progress - 0.47) / 0.15))
        intensity = math.sin(t * math.pi)
        if intensity <= 0:
            return
        fs = B._fx_scale(boss)
        facing = int(getattr(boss, "direction", 1)) or 1
        ix = cx + int(48 * facing)
        iy = cy + int(72)
        # shock ellipse ganda
        rr = int((14 + t * 34) * fs)
        pygame.draw.ellipse(surface,
                            B._rgba(B.PALETTE["rage_mid"], 220 * intensity),
                            (ix - rr, iy - rr // 3, rr * 2, max(4, rr * 2 // 3)), 3)
        rr2 = int(rr * 0.6)
        pygame.draw.ellipse(surface,
                            B._rgba(B.PALETTE["rage_hot"], 190 * intensity),
                            (ix - rr2, iy - rr2 // 3, rr2 * 2, max(3, rr2 * 2 // 3)), 2)
        # bintang percikan di titik hantam
        B._spark_star(surface, ix, iy - 24, int(22 * fs * intensity),
                      B.PALETTE["blood_light"], 230 * intensity,
                      spikes=6, rot=progress * 4, core=B.PALETTE["rage_hot"])
        # retak tanah
        for i in range(4):
            angc = math.pi * (0.75 + 0.5 * B._hash01(i * 31)) \
                if facing < 0 else math.pi * (-0.25 + 0.5 * B._hash01(i * 31))
            B._jagged_crack(surface, ix, iy, angc * 0.3 + i * 1.5,
                            int(34 * fs * (0.5 + t * 0.5)),
                            (B.PALETTE["shadow_deep"], B.PALETTE["rage_dark"]),
                            190 * intensity, seed=i * 7 + 3)
        # debu naik
        for i in range(5):
            dt_ = (t + i * 0.17) % 1.0
            dx_ = ix + int(math.sin(i * 2.4) * 20 * fs)
            dy_ = iy - int(dt_ * 26)
            B._blk(surface, B.PALETTE["leather_mid"],
                   150 * intensity * (1 - dt_), dx_, dy_, 4 - int(dt_ * 2))

    # ═════════════════════════════════════════════════════════════════
    #  PROJECTILE VISUAL — gelombang tebasan + chip balistik + ember
    # ═════════════════════════════════════════════════════════════════
    def _drk_spawn_wave(boss, facing, fs):
        projs = getattr(boss, "_drk_projs", None)
        if projs is None:
            projs = boss._drk_projs = []
        projs.append({"k": "wave", "age": 0, "life": 15,
                      "x": 42.0 * facing * fs, "y": 52.0,
                      "vx": 8.5 * facing * fs, "d": facing})
        for i in range(6):
            a = -0.4 - _NS_drakar._hash01(i * 13) * 1.6
            sp = (2.5 + _NS_drakar._hash01(i * 7) * 3.5) * fs
            projs.append({"k": "chip", "age": 0, "life": 20,
                          "x": 46.0 * facing * fs, "y": 62.0,
                          "vx": math.cos(a) * sp * facing,
                          "vy": math.sin(a) * sp * 1.6,
                          "c": "armor_mid" if i % 3 else "blood_mid"})
        for i in range(4):
            projs.append({"k": "ember", "age": 0, "life": 18,
                          "x": (36.0 + i * 7) * facing * fs, "y": 48.0,
                          "vx": (0.5 + _NS_drakar._hash01(i * 5)) * facing,
                          "vy": -1.6 - _NS_drakar._hash01(i * 9) * 1.4})

    def _drk_spawn_gibs(boss, ox, oy, fs):
        """Serpihan darah eksekusi Culling Blade (world offset dari boss)."""
        projs = getattr(boss, "_drk_projs", None)
        if projs is None:
            projs = boss._drk_projs = []
        for i in range(10):
            a = math.pi * 2 * i / 10 + _NS_drakar._hash01(i * 3) * 0.5
            sp = (2.0 + _NS_drakar._hash01(i * 11) * 4.0) * fs
            projs.append({"k": "chip", "age": 0, "life": 24,
                          "x": ox, "y": oy - 20,
                          "vx": math.cos(a) * sp,
                          "vy": math.sin(a) * sp - 2.5,
                          "c": "blood_mid" if i % 2 else "blood_light"})

    def _drk_step_projectiles(boss):
        projs = getattr(boss, "_drk_projs", None)
        if not projs:
            return
        alive = []
        for p in projs:
            p["age"] += 1
            p["x"] += p.get("vx", 0.0)
            p["y"] += p.get("vy", 0.0)
            if p["k"] == "chip":
                p["vy"] = p.get("vy", 0.0) + 0.55
                if p["y"] > 112:            # mendarat di tanah
                    p["y"] = 112
                    p["vy"] = 0.0
                    p["vx"] = p.get("vx", 0.0) * 0.5
            elif p["k"] == "wave":
                p["vx"] *= 0.97
            if p["age"] <= p["life"]:
                alive.append(p)
        boss._drk_projs = alive

    def _drk_draw_projectiles(surface, boss, x, y):
        projs = getattr(boss, "_drk_projs", None)
        if not projs:
            return
        B = _NS_drakar
        for p in projs:
            fade = 1.0 - p["age"] / float(p["life"])
            px = x + p["x"]
            py = y + p["y"]
            if p["k"] == "wave":
                # crescent darah vertikal meluncur maju, menyusut
                h = 56.0 * (0.55 + 0.45 * fade)
                d = p["d"]
                for i in range(9):
                    t = i / 8.0
                    yy = py - h / 2 + h * t
                    bulge = (1 - (2 * t - 1) ** 2) * 13 * d
                    a = 240 * fade
                    B._blk(surface, B.PALETTE["blood_darkest"], a * 0.8,
                           px + bulge - 8 * d, yy, 5)
                    B._blk(surface, B.PALETTE["blood_mid"], a,
                           px + bulge - 4 * d, yy, 5)
                    B._blk(surface, B.PALETTE["blood_hot"], a,
                           px + bulge, yy, 4)
                    if 0.2 < t < 0.8:
                        B._blk(surface, B.PALETTE["blood_shine"], a,
                               px + bulge + 3 * d, yy + 1, 2)
                # ember ekor
                B._blk(surface, B.PALETTE["ember_light"], 200 * fade,
                       px - 16 * d, py - 5, 3)
                B._blk(surface, B.PALETTE["ember_mid"], 160 * fade,
                       px - 25 * d, py + 7, 3)
            elif p["k"] == "chip":
                sz = 4 if p["age"] < p["life"] * 0.6 else 3
                B._blk(surface, B.PALETTE["shadow_deep"], 200 * fade,
                       px + 1, py + 1, sz)
                B._blk(surface, B.PALETTE[p.get("c", "armor_mid")],
                       230 * fade, px, py, sz)
            else:  # ember
                B._blk(surface, B.PALETTE["ember_mid"], 210 * fade, px, py, 3)
                if fade > 0.5:
                    B._blk(surface, B.PALETTE["ember_hot"], 230 * fade,
                           px + 1, py + 1, 1)

    # ═════════════════════════════════════════════════════════════════
    #  STATE / DETEKSI
    # ═════════════════════════════════════════════════════════════════
    def _update_drk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_drk_previous_timer", 0))
        active = bool(getattr(boss, "_drk_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._drk_attack_active = True
            boss._drk_attack_frame = 0
            boss._drk_attack_dir = int(getattr(boss, "direction", 1))
            boss._drk_wave_fired = False
            active = True
        elif active and timer > 0:
            boss._drk_attack_frame = int(getattr(boss, "_drk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._drk_attack_active = False
            boss._drk_attack_frame = 0
            active = False
        boss._drk_previous_timer = timer
        boss._drk_attack_progress = (
            min(1.0, getattr(boss, "_drk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0)

    def _detect_moving(boss):
        if not hasattr(boss, "_drk_last_x"):
            boss._drk_last_x = boss.x
            boss._drk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._drk_last_x)
        dy = abs(boss.y - boss._drk_last_y)
        boss._drk_last_x = boss.x
        boss._drk_last_y = boss.y
        return dx + dy > 0.3

    # ═════════════════════════════════════════════════════════════════
    #  LAPISAN WORLD: shadow / aura / ring / mist
    # ═════════════════════════════════════════════════════════════════
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan kontak dither: mengecil saat lift, dasar menapak."""
        w0, h0 = 150, 40
        w = max(60, w0 - lift * 8)
        h = max(15, h0 - lift * 3)
        s = pygame.Surface((w0, h0), pygame.SRCALPHA)
        off_x = (w0 - w) // 2
        off_y = h0 - h
        pygame.draw.ellipse(s, (0, 0, 0, 70),
                            (off_x + 2, off_y + 2, max(1, w - 4), max(1, h - 4)))
        pygame.draw.ellipse(s, (0, 0, 0, 120),
                            (off_x + w // 6, off_y + h // 6,
                             max(1, w - w // 3), max(1, h - h // 3)))
        # tepi dither chunky
        for i in range(10):
            a = i * math.pi * 2 / 10
            ex = w0 // 2 + int(math.cos(a) * (w // 2 - 3))
            ey = off_y + h // 2 + int(math.sin(a) * (h // 2 - 2))
            if i % 2 == 0:
                pygame.draw.rect(s, (0, 0, 0, 46), ((ex // 3) * 3, (ey // 3) * 3, 3, 3))
        surface.blit(s, (x - w0 // 2, y - h0 // 2))

    def _draw_rage_aura(surface, x, y, phase):
        """Genangan panas gelap di tanah + heat blob aditif berdenyut."""
        B = _NS_drakar

        def build_aura():
            s = pygame.Surface((390, 260), pygame.SRCALPHA)
            for r in range(120, 0, -3):
                a = int(42 * (120 - r) / 120)
                pygame.draw.ellipse(s, (*B.PALETTE["rage_darkest"], a),
                                    (195 - r, 130 - r // 2, r * 2, r))
            return s

        aura = B._static("rage_aura_v3", build_aura)
        aura.set_alpha(min(255, int(190 + 55 * math.sin(phase * 1.5))))
        surface.blit(aura, (x - 195, y - 50))

    def _draw_ground_ring(surface, boss, x, y, phase, skill):
        """Cincin rune tanah chunky: dash ganda + 4 glyph blok berputar."""
        B = _NS_drakar
        fs = B._fx_scale(boss)
        r = int(65 * fs)
        pulse = 0.7 + 0.3 * math.sin(phase * 2)
        alpha = B._alpha(175 * pulse)
        B._dashed_ring(surface, x, y, r, B.PALETTE["rune_dark"], alpha,
                       phase * 0.3, segments=12, thick=3, squash=0.4)
        B._dashed_ring(surface, x, y, int(r * 0.72), B.PALETTE["rune_mid"],
                       int(alpha * 0.75), -phase * 0.5, segments=8, thick=3,
                       squash=0.4)
        # 4 glyph blok (rune mini 2x2 + tip)
        for i in range(4):
            angg = phase * 0.25 + i * math.pi / 2
            gx = x + math.cos(angg) * r * 0.88
            gy = y + math.sin(angg) * r * 0.35
            B._blk(surface, B.PALETTE["rune_mid"], alpha, gx - 3, gy - 3, 3)
            B._blk(surface, B.PALETTE["rune_light"], alpha, gx, gy - 6, 3)
            B._blk(surface, B.PALETTE["rune_light"], alpha, gx, gy, 3)
            B._blk(surface, B.PALETTE["rage_hot"], alpha * pulse, gx, gy - 3, 3)

    def _draw_rage_mist(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Bara + asap naik dari tubuh (chunky, 3 ukuran)."""
        B = _NS_drakar
        count = 12 if intense else 7
        for i in range(count):
            t = (phase * 0.3 + i * 0.145) % 1.0
            px = cx + math.sin(phase + i * 1.7) * 21 + \
                (facing * t * 12 if trail else 0)
            py = cy - t * 42
            alpha = B._alpha(190 * (1 - t))
            if i % 3 == 0:      # asap gelap besar
                B._blk(surface, B.PALETTE["rage_darkest"], alpha * 0.7,
                       px - 2, py - 2, 6)
            B._blk(surface, B.PALETTE["ember_dark"] if i % 2 else
                   B.PALETTE["ember_mid"], alpha, px, py, 4 - int(t * 2))
            if t < 0.45:
                B._blk(surface, B.PALETTE["ember_light"], alpha, px + 1, py + 1, 2)

    # ═════════════════════════════════════════════════════════════════
    #  SKILL FX — W COUNTER HELIX (spin AOE)
    # ═════════════════════════════════════════════════════════════════
    def _draw_drk_helix_fx(surface, boss, x, y, timer, phase):
        """Helix v3: smear crescent ganda mengikuti spin + ghost blade
        afterimage + chip darah terbang radial."""
        B = _NS_drakar
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        spin = progress * math.pi * 8
        bob = int(math.sin(progress * math.pi) * -7)
        fs = B._fx_scale(boss)
        radius = int(100 * fs)
        cxs, cys = x, y + bob - 10
        # dua lengan smear (offset pi) + ghost afterimage
        for ghost in range(3):
            g_spin = spin - ghost * 0.42
            g_alpha = (1.0, 0.55, 0.28)[ghost]
            for arm in range(2):
                a0 = g_spin + arm * math.pi
                steps = 13
                pts = []
                for i in range(steps):
                    a = a0 - math.pi * 0.55 * i / (steps - 1)
                    pts.append((cxs + math.cos(a) * radius,
                                cys + math.sin(a) * radius * 0.55))
                for i in range(steps - 1):
                    fade = (1 - i / float(steps)) * g_alpha
                    al = B._alpha(235 * fade)
                    if al <= 8:
                        continue
                    w = max(3, int((12 - i * 0.7) * (1.0 if ghost == 0 else 0.6)))
                    B._blk(surface, B.PALETTE["blood_dark"], al,
                           pts[i][0] - 2, pts[i][1] + 2, w + 2)
                    B._blk(surface, B.PALETTE["blood_mid"], al,
                           pts[i][0], pts[i][1], w)
                    if i < 4 and ghost == 0:
                        B._blk(surface, B.PALETTE["blood_hot"], al,
                               pts[i][0] + 1, pts[i][1] - 2, max(2, w - 4))
                # tip bilah menyala (hanya ghost 0)
                if ghost == 0:
                    tipx, tipy = pts[0]
                    B._blk(surface, B.PALETTE["blade_shine"], 255, tipx, tipy, 4)
                    B._blk(surface, B.PALETTE["white"], 255, tipx + 1, tipy + 1, 2)
        # chip darah terbang keluar radial
        for i in range(10):
            a = spin * 0.6 + i * math.pi / 5
            rr = radius * (0.5 + ((progress * 3 + i * 0.13) % 1.0) * 0.8)
            px = cxs + math.cos(a) * rr
            py = cys + math.sin(a) * rr * 0.55
            al = B._alpha(210 * (1 - progress * 0.4))
            B._blk(surface, B.PALETTE["blood_mid"], al, px, py, 3)
            if i % 2 == 0:
                B._blk(surface, B.PALETTE["blood_light"], al, px + 1, py + 1, 2)

    def _draw_counterhelix_ground(surface, boss, x, y, timer, phase):
        """Ground W: shock ring mengembang + spatter darah di tanah."""
        B = _NS_drakar
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        gy = y + 114
        # aktivasi: bintang + flash ellipse
        if progress < 0.12:
            t = progress / 0.12
            B._spark_star(surface, x, gy, int(26 * fs), B.PALETTE["blood_light"],
                          220 * (1 - t), spikes=8, rot=phase * 2,
                          core=B.PALETTE["blood_hot"])
        # ring dash ganda mengembang
        r = int((72 + progress * 60) * fs)
        alpha = B._alpha(235 * (1 - progress * 0.55))
        B._dashed_ring(surface, x, gy, r, B.PALETTE["blood_dark"], alpha,
                       phase * 0.9, segments=14, thick=4, squash=0.4)
        B._dashed_ring(surface, x, gy, int(r * 0.8), B.PALETTE["blood_mid"],
                       int(alpha * 0.8), -phase * 1.2, segments=10, thick=3,
                       squash=0.4)
        # spatter darah menempel tanah
        for i in range(12):
            a = i * math.pi / 6 + 0.4
            rr = r * (0.35 + B._hash01(i * 7) * 0.55)
            px = x + math.cos(a) * rr
            py = gy + math.sin(a) * rr * 0.4
            B._blk(surface, B.PALETTE["blood_darkest"], alpha, px - 1, py + 1, 4)
            B._blk(surface, B.PALETTE["blood_mid"], alpha, px, py, 3)

    # ═════════════════════════════════════════════════════════════════
    #  SKILL FX — Q BATTLE HUNGER (rage buff)
    # ═════════════════════════════════════════════════════════════════
    def _draw_battlehunger_ground(surface, boss, x, y, timer, phase):
        """Ground Q: rune circle molten + retakan magma + ember."""
        B = _NS_drakar
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        tx, ty = x, y + 108
        # aktivasi
        if progress < 0.14:
            t = progress / 0.14
            rr = int(84 * fs * t)
            pygame.draw.ellipse(surface,
                                B._rgba(B.PALETTE["blood_dark"], 230 * (1 - t * 0.4)),
                                (tx - rr, ty - rr // 3, rr * 2, max(4, rr * 2 // 3)), 3)
            B._spark_star(surface, tx, ty, int(24 * fs), B.PALETTE["rage_light"],
                          210 * (1 - t), spikes=8, rot=phase,
                          core=B.PALETTE["rage_hot"])
        # piringan molten
        r = int(80 * fs * min(1.0, progress * 4))
        if r > 4:
            for off, ck, am in ((0, "blood_darkest", 1.0), (5, "rage_darkest", 0.9),
                                (10, "rage_dark", 0.75)):
                pygame.draw.ellipse(
                    surface, B._rgba(B.PALETTE[ck], B._alpha(215 * am)),
                    (tx - r + off, ty - r // 3 + off // 2,
                     max(1, r * 2 - off * 2), max(2, r * 2 // 3 - off)))
            # retakan magma radial berdenyut
            beat = 0.55 + 0.45 * abs(math.sin(phase * 2.4))
            for i in range(6):
                a = i * math.pi / 3 + 0.25
                B._jagged_crack(surface, tx, ty, a, int(52 * fs),
                                (B.PALETTE["blood_darkest"], B.PALETTE["rage_mid"]),
                                175 * beat * min(1.0, progress * 3), seed=i * 9 + 5)
            # dash ring rune berputar
            B._dashed_ring(surface, tx, ty, int(r * 0.9), B.PALETTE["rune_mid"],
                           B._alpha(190 * beat), phase * 0.5, segments=10,
                           thick=3, squash=0.38)
            # ember naik dari piringan
            for i in range(8):
                t2 = (phase * 0.5 + i * 0.125) % 1.0
                mx = tx + math.sin(phase + i * 2.2) * r * 0.5
                my = ty - t2 * 34 * fs
                B._blk(surface, B.PALETTE["ember_mid"], 175 * (1 - t2), mx, my,
                       3 if i % 2 else 2)

    def _draw_battlehunger_foreground(surface, boss, x, y, timer, phase):
        """Foreground Q: pilar api rage spiral + heartbeat ring ganda +
        glyph darah melayang."""
        B = _NS_drakar
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        if progress < 0.03:
            return
        # pilar spiral api mengelilingi badan
        for i in range(6):
            a0 = phase * 1.1 + i * math.pi / 3
            for seg in range(5):
                t = (phase * 0.6 + i * 0.31 + seg * 0.2) % 1.0
                sy = y + 84 - t * 150 * fs
                sx = x + math.cos(a0 + t * 2.6) * (34 + t * 10) * fs
                al = B._alpha(215 * (1 - t))
                sz = 5 - int(t * 3)
                B._blk(surface, B.PALETTE["rage_darkest"], al * 0.7,
                       sx - 2, sy - 2, sz + 3)
                B._blk(surface, B.PALETTE["rage_mid"], al, sx, sy, sz)
                if t < 0.5:
                    B._blk(surface, B.PALETTE["rage_hot"], al, sx + 1, sy + 1,
                           max(1, sz - 2))
        # heartbeat: dua denyut ring cepat lalu jeda (khas rage)
        beat_t = (phase * 1.4) % 1.0
        for bo in (0.0, 0.18):
            bt = beat_t - bo
            if 0.0 <= bt < 0.34:
                br = int((26 + bt * 150) * fs)
                al = B._alpha(230 * (1 - bt / 0.34))
                pygame.draw.ellipse(surface, B._rgba(B.PALETTE["blood_mid"], al),
                                    (x - br, y - 18 - br // 2, br * 2, br), 3)
                pygame.draw.ellipse(surface, B._rgba(B.PALETTE["rage_hot"], al),
                                    (x - br + 4, y - 16 - br // 2,
                                     max(2, br * 2 - 8), max(2, br - 4)), 2)
        # glyph darah melayang (blok rune kecil)
        for i in range(4):
            t = (phase * 0.35 + i * 0.25) % 1.0
            gx = x + math.sin(phase * 0.8 + i * 1.9) * 52 * fs
            gy = y + 30 - t * 120 * fs
            al = B._alpha(220 * (1 - t))
            B._blk(surface, B.PALETTE["rune_mid"], al, gx - 3, gy, 3)
            B._blk(surface, B.PALETTE["rune_light"], al, gx, gy - 3, 3)
            B._blk(surface, B.PALETTE["rune_light"], al, gx, gy + 3, 3)
            B._blk(surface, B.PALETTE["rage_hot"], al, gx, gy, 3)

    # ═════════════════════════════════════════════════════════════════
    #  SKILL FX — E BERSERKER'S CALL (roar taunt)
    # ═════════════════════════════════════════════════════════════════
    def _draw_berserkerscall_ground(surface, boss, x, y, timer, phase):
        """Ground E: hentakan debu + ring raung bergerigi + chevron
        taunt konvergen (musuh 'ditarik')."""
        B = _NS_drakar
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        gy = y + 114
        # hentakan awal: debu ellipse
        if progress < 0.18:
            t = progress / 0.18
            rr = int(46 * fs * t)
            pygame.draw.ellipse(surface,
                                B._rgba(B.PALETTE["leather_mid"], 190 * (1 - t * 0.5)),
                                (x - rr, gy - rr // 3, rr * 2, max(4, rr * 2 // 3)), 3)
            B._spark_star(surface, x, gy, int(18 * fs), B.PALETTE["rage_light"],
                          200 * (1 - t), spikes=6, rot=phase)
        if progress > 0.12:
            t = (progress - 0.12) / 0.88
            r = int((60 + t * 130) * fs)
            al = B._alpha(235 * (1 - t))
            # ring raung bergerigi (radius bergelombang)
            for i in range(20):
                a = i * math.pi / 10 + phase * 0.2
                wob = 1.0 + 0.1 * math.sin(a * 5 + phase * 3)
                px = x + math.cos(a) * r * wob
                py = gy + math.sin(a) * r * 0.4 * wob
                B._blk(surface, B.PALETTE["blood_dark"], al, px - 1, py + 1, 5)
                B._blk(surface, B.PALETTE["blood_mid"], al, px, py, 4)
                B._blk(surface, B.PALETTE["rage_hot"], al * 0.8, px + 1, py - 1, 2)
            # chevron taunt: menunjuk KE DALAM, bergerak masuk
            pull = (phase * 0.9) % 1.0
            for i in range(8):
                a = i * math.pi / 4 + 0.35
                rr2 = r * (1.15 - pull * 0.5)
                cxp = x + math.cos(a) * rr2
                cyp = gy + math.sin(a) * rr2 * 0.4
                B._chevron(surface, cxp, cyp, a + math.pi, int(11 * fs),
                           B.PALETTE["blood_light"], al, width=3)

    def _draw_berserkerscall_foreground(surface, boss, x, y, timer, phase):
        """Foreground E: gelombang raung dari kepala (3 busur bertumpuk)
        + glint armor + partikel ludah/bara."""
        B = _NS_drakar
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        facing = int(getattr(boss, "direction", 1)) or 1
        hx = x + 6 * facing
        hy = y - 58
        if progress < 0.25:
            # charge: kepala menyala + glow membesar
            t = progress / 0.25
            g = B._drk_glow(int((20 + t * 22) * fs), B.PALETTE["rage_mid"],
                            140 + int(60 * t))
            surface.blit(g, (hx - g.get_width() // 2, hy - g.get_height() // 2),
                         special_flags=pygame.BLEND_RGBA_ADD)
            for i in range(6):
                a = i * math.pi / 3 + phase * 2
                px = hx + math.cos(a) * (26 * fs * (1 - t))
                py = hy + math.sin(a) * (20 * fs * (1 - t))
                B._blk(surface, B.PALETTE["ember_light"], 220 * t, px, py, 3)
        else:
            # gelombang raung: 3 busur konsentris ke segala arah
            t = (progress - 0.25) / 0.75
            for wave in range(3):
                wt = t - wave * 0.14
                if wt <= 0:
                    continue
                wr = int(wt * 190 * fs)
                al = B._alpha(235 * (1 - wt))
                if al <= 6:
                    continue
                blocks = 22
                for i in range(blocks):
                    a = i * math.pi * 2 / blocks
                    wob = 1.0 + 0.08 * math.sin(a * 6 + phase * 4)
                    px = hx + math.cos(a) * wr * wob
                    py = hy + math.sin(a) * wr * 0.72 * wob
                    B._blk(surface, B.PALETTE["blood_dark"], al * 0.8,
                           px - 2, py + 2, 5)
                    B._blk(surface, B.PALETTE["blood_mid"], al, px, py, 4)
                    if wave == 0:
                        B._blk(surface, B.PALETTE["rage_hot"], al, px + 1, py - 1, 2)
            # spark "!!" di atas kepala
            B._spark_star(surface, hx, hy - 26 * fs, int(12 * fs * (1 - t)),
                          B.PALETTE["ember_hot"], 220 * (1 - t), spikes=4,
                          rot=phase * 3)

    # ═════════════════════════════════════════════════════════════════
    #  SKILL FX — R CULLING BLADE (execute)
    # ═════════════════════════════════════════════════════════════════
    def _draw_cullingblade_ground(surface, boss, x, y, timer, phase):
        """Ground R: telegraph crosshair konvergen di target ->
        kawah + retakan saat eksekusi."""
        B = _NS_drakar
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        tx, ty = B._target_position(boss, x, y)
        if progress < 0.4:
            # TELEGRAPH: ring dash mengecil + crosshair X berkedip
            t = progress / 0.4
            r = int((95 - t * 40) * fs)
            al = B._alpha(210 * min(1.0, t * 3))
            B._dashed_ring(surface, tx, ty, r, B.PALETTE["blood_mid"], al,
                           -phase * 1.4, segments=8, thick=4, squash=0.42)
            blink = 0.6 + 0.4 * math.sin(phase * 6)
            for (dx_, dy_) in ((1, 1), (1, -1)):
                for st in range(6):
                    d = (st + 2) * 6 * fs
                    B._blk(surface, B.PALETTE["blood_light"], al * blink,
                           tx + dx_ * d, ty + dy_ * d * 0.5, 4)
                    B._blk(surface, B.PALETTE["blood_light"], al * blink,
                           tx - dx_ * d, ty - dy_ * d * 0.5, 4)
            B._blk(surface, B.PALETTE["blood_hot"], al * blink, tx - 2, ty - 2, 5)
            # chevron konvergen
            for i in range(6):
                a = i * math.pi / 3 + phase * 0.7
                B._chevron(surface, tx + math.cos(a) * r * 1.1,
                           ty + math.sin(a) * r * 0.45, a + math.pi,
                           int(11 * fs), B.PALETTE["blood_light"], al, width=3)
        else:
            # KAWAH eksekusi
            t = (progress - 0.4) / 0.6
            r = int((60 + t * 42) * fs)
            al = B._alpha(235 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, B._rgba(B.PALETTE["blood_darkest"], al),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, B._rgba(B.PALETTE["blood_dark"], al),
                                (tx - r + 7, ty - r // 3 + 5,
                                 max(1, r * 2 - 14), max(2, r * 2 // 3 - 10)))
            for i in range(7):
                a = i * math.pi * 2 / 7 + 0.3
                B._jagged_crack(surface, tx, ty, a, int(56 * fs),
                                (B.PALETTE["blood_darkest"], B.PALETTE["blood_mid"]),
                                185 * (1 - t), seed=i * 11 + 7)

    def _draw_cullingblade_foreground(surface, boss, x, y, timer, phase):
        """Foreground R: charge bilah -> X-slash raksasa putih-panas ->
        hujan darah; spawn gib chip balistik saat momen eksekusi."""
        B = _NS_drakar
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = B._fx_scale(boss)
        tx, ty = B._target_position(boss, x, y)
        if progress < 0.4:
            boss._drk_r_fired = False
            # charge glow pada kapak
            t = progress / 0.4
            facing = int(getattr(boss, "direction", 1)) or 1
            g0 = B._compute_two_handed_grip(x, y, facing,
                                            float(getattr(boss, "pulse", 0.0)),
                                            "idle")
            ax_, ay_ = g0["axe_head"]
            g = B._drk_glow(int((14 + t * 20) * fs), B.PALETTE["blood_mid"],
                            120 + int(100 * t))
            surface.blit(g, (int(ax_) - g.get_width() // 2,
                             int(ay_) - g.get_height() // 2),
                         special_flags=pygame.BLEND_RGBA_ADD)
            for i in range(5):
                a = phase * 3 + i * math.pi * 2 / 5
                px = ax_ + math.cos(a) * 18 * fs * (1 - t)
                py = ay_ + math.sin(a) * 14 * fs * (1 - t)
                B._blk(surface, B.PALETTE["blood_light"], 220 * t, px, py, 3)
        elif progress < 0.65:
            # X-SLASH raksasa
            t = (progress - 0.4) / 0.25
            if not getattr(boss, "_drk_r_fired", False):
                boss._drk_r_fired = True
                B._drk_spawn_gibs(boss, tx - x, ty - y, fs)
            intensity = math.sin(t * math.pi)
            slash_len = int((100 + t * 40) * fs)
            for (dx_, dy_) in ((1, 0.62), (1, -0.62)):
                p1 = (tx - dx_ * slash_len, ty - dy_ * slash_len)
                p2 = (tx + dx_ * slash_len, ty + dy_ * slash_len)
                for thick, ck, am in ((17, "blood_darkest", 0.6),
                                      (13, "blood_dark", 0.85),
                                      (9, "blood_mid", 1.0),
                                      (5, "blood_hot", 1.0),
                                      (2, "blood_shine", 1.0)):
                    al = B._alpha(255 * intensity * am)
                    if al <= 0:
                        continue
                    pygame.draw.line(surface, B._rgba(B.PALETTE[ck], al),
                                     p1, p2, thick)
            # core putih + bintang
            g = B._drk_glow(int(34 * fs), B.PALETTE["blood_hot"],
                            int(200 * intensity))
            surface.blit(g, (tx - g.get_width() // 2, ty - g.get_height() // 2),
                         special_flags=pygame.BLEND_RGBA_ADD)
            B._blk(surface, B.PALETTE["white"], 255 * intensity, tx - 3, ty - 3, 7)
            B._spark_star(surface, tx, ty, int(32 * fs * intensity),
                          B.PALETTE["blood_light"], 230 * intensity,
                          spikes=8, rot=phase * 4, core=B.PALETTE["white"])
        else:
            # hujan darah + sisa X memudar
            t = (progress - 0.65) / 0.35
            for i in range(12):
                fall = (phase * 0.5 + i * 0.13) % 1.0
                rx = tx + math.sin(phase + i * 1.8) * 54 * fs
                ry = ty - 30 + fall * 58 * fs
                al = B._alpha(215 * (1 - t) * (1 - fall * 0.5))
                B._blk(surface, B.PALETTE["blood_dark"], al, rx, ry, 3)
                B._blk(surface, B.PALETTE["blood_mid"], al, rx, ry + 3, 2)
            for (dx_, dy_) in ((1, 0.62), (1, -0.62)):
                sl = int(60 * fs)
                al = B._alpha(140 * (1 - t))
                pygame.draw.line(surface, B._rgba(B.PALETTE["blood_dark"], al),
                                 (tx - dx_ * sl, ty - dy_ * sl),
                                 (tx + dx_ * sl, ty + dy_ * sl), 4)
                pygame.draw.line(surface, B._rgba(B.PALETTE["blood_mid"], al),
                                 (tx - dx_ * sl, ty - dy_ * sl),
                                 (tx + dx_ * sl, ty + dy_ * sl), 2)

    # ═════════════════════════════════════════════════════════════════
    #  ENTRY POINT
    # ═════════════════════════════════════════════════════════════════
    def draw_drakar(surface, boss, x, y):
        B = _NS_drakar
        # Garis tanah rig ini ada di y+114 (warisan kanvas 3x). Boss lain
        # menapak sekitar y+56, jadi seluruh gambar (badan DAN efek tanah,
        # semuanya relatif terhadap y) digeser satu kali di sini supaya
        # kaki, bayangan, HP bar, dan label sejajar dengan keluarga.
        y = int(y) - B.ANCHOR_DY
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = B._detect_moving(boss)
        B._update_drk_attack_anim(boss)
        attacking = (getattr(boss, "_drk_attack_active", False)
                     or getattr(boss, "timer", 0) >
                     getattr(boss, "attack_cooldown", 40) - 15)
        fs = B._fx_scale(boss)
        B._drk_step_projectiles(boss)

        # ── lapisan tanah ──
        B._draw_rage_aura(surface, x, y, pulse)
        B._draw_ground_ring(surface, boss, x, y + 114, pulse, active_skill)

        if active_skill == "q":
            B._draw_battlehunger_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            B._draw_counterhelix_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            B._draw_berserkerscall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            B._draw_cullingblade_ground(surface, boss, x, y, skill_timer, pulse)

        # flash aktivasi universal (12 frame pertama tiap skill)
        if active_skill in ("q", "w", "e", "r"):
            dur = {"q": 90, "w": 45, "e": 60, "r": 60}[active_skill]
            age = dur - skill_timer
            if 0 <= age < 12:
                st = age / 12.0
                a = int(235 * (1 - st))
                rr = int((16 + st * 52) * fs)
                gy = y + 114
                pygame.draw.ellipse(surface, B._rgba(B.PALETTE["rage_light"], a),
                                    (x - rr, gy - rr // 3, rr * 2,
                                     max(4, rr * 2 // 3)), 2)
                B._spark_star(surface, x, gy, int(20 * fs),
                              B.PALETTE["rage_light"], a, spikes=8, rot=pulse,
                              core=B.PALETTE["rage_hot"])

        # ── pose & badan ──
        facing = int(getattr(boss, "direction", 1)) or 1
        cd = max(2, int(getattr(boss, "attack_cooldown", 46)))
        t_now = int(getattr(boss, "timer", 0))
        atk_p = max(0.0, min(1.0, (cd - 1 - t_now) / float(cd - 1))) \
            if attacking else 0.0
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        ox, oy = B.BODY_OX, B.BODY_OY

        body_kw = {}
        if active_skill == "q":
            body_kw["battlehunger"] = True
        if active_skill == "w":
            body_kw["helix_active"] = True
        if active_skill == "e":
            body_kw["berserk_call"] = True
        if getattr(boss, "rage_active", False):
            body_kw["rage_mode"] = True

        def _blit_body(spr):
            img = spr if facing > 0 else pygame.transform.flip(spr, True, False)
            surface.blit(img, (x - ox, y - oy))

        if active_skill == "w":
            p = max(0.0, min(1.0, 1 - skill_timer / 45.0))
            lift_h = int(math.sin(p * math.pi) * 7)
            B._draw_shadow(surface, x, y + 120, lift_h)
            B._draw_rage_mist(surface, x, y + 90, pulse, intense=True)
            B._draw_drk_helix_fx(surface, boss, x, y, skill_timer, pulse)
            _blit_body(B._drk_body_surface("helix", facing, pulse, p, flash,
                                           **body_kw))
        elif attacking:
            # lunge world-space selaras keyframe badan
            if atk_p < 0.16:
                t2 = atk_p / 0.16
                lunge = -int(t2 * 8) * facing
                lift = -int(t2 * 4)
            elif atk_p < 0.34:
                lunge = -8 * facing
                lift = -4
            elif atk_p < 0.47:
                t2 = (atk_p - 0.34) / 0.13
                te = t2 * t2 * t2
                lunge = int(-8 + te * 30) * facing
                lift = int(-4 + te * 8)
            elif atk_p < 0.62:
                t2 = (atk_p - 0.47) / 0.15
                shake = int(math.sin(t2 * 30) * 4 * (1 - t2))
                lunge = (22 + shake) * facing
                lift = 4
            else:
                t2 = (atk_p - 0.62) / 0.38
                te = 1 - (1 - t2) ** 2
                lunge = int(22 * (1 - te)) * facing
                lift = int(4 * (1 - te))
            B._draw_shadow(surface, x + lunge, y + 120, max(0, -lift))
            B._draw_rage_mist(surface, x + lunge, y + 90, pulse, intense=True)
            _blit_body(B._drk_body_surface("attack", facing, pulse, atk_p,
                                           flash, **body_kw))
            B._draw_axe_slash_trail(surface, boss, x + lunge, y + lift, atk_p)
            if 0.47 <= atk_p <= 0.62:
                B._draw_impact_burst(surface, boss, x + lunge, y + lift, atk_p)
                if atk_p >= 0.50 and not getattr(boss, "_drk_wave_fired", True):
                    boss._drk_wave_fired = True
                    B._drk_spawn_wave(boss, facing, fs)
        elif moving:
            phase = pulse * 2.0
            bob = int(abs(math.sin(phase * 2.0)) * 5)
            sway = int(math.sin(phase) * 3)
            B._draw_shadow(surface, x + sway, y + 120, bob // 2)
            B._draw_rage_mist(surface, x + sway, y + 90, phase, trail=True,
                              facing=facing)
            _blit_body(B._drk_body_surface("walk", facing, phase, 0.0, flash,
                                           **body_kw))
        else:
            bob_i = int(math.sin(pulse * 0.5) * 5)
            B._draw_shadow(surface, x, y + 120, max(0, -bob_i))
            B._draw_rage_mist(surface, x, y + 90, pulse)
            _blit_body(B._drk_body_surface("idle", facing, pulse, 0.0, flash,
                                           **body_kw))

        # nafas bara aditif kontinu (badan hidup + variasi warna halus);
        # BLEND_RGB_ADD: tidak menambah alpha -> bbox badan tetap rapat
        gpeak = 46 + int(26 * math.sin(pulse * 2.1))
        g = B._drk_glow(30, B.PALETTE["ember_mid"], max(8, gpeak))
        surface.blit(g, (x + 10 * facing - 30, y - 66 - 30),
                     special_flags=pygame.BLEND_RGB_ADD)

        # ── projectile visual (wave/chip/ember) ──
        B._drk_draw_projectiles(surface, boss, x, y)

        # ── overlay status ──
        if getattr(boss, "rage_active", False):
            g = B._drk_glow(70, B.PALETTE["rage_mid"],
                            60 + int(18 * math.sin(pulse * 3)))
            surface.blit(g, (x - 70, y - 90),
                         special_flags=pygame.BLEND_RGB_ADD)
            g2 = B._drk_glow(11, B.PALETTE["rage_light"], 110)
            surface.blit(g2, (x + 9 * facing - 11, y - 62),
                         special_flags=pygame.BLEND_RGB_ADD)
        if getattr(boss, "defense_boost", False):
            for i in range(4):
                a = pulse * 2.6 + i * 1.6
                sx = x + math.sin(a) * 30
                sy = y - 30 + math.cos(a * 1.3) * 34
                al = 150 + int(80 * math.sin(a * 2))
                B._blk(surface, B.PALETTE["armor_shine"], al, sx, sy, 3)
                B._blk(surface, B.PALETTE["white"], al, sx + 1, sy + 1, 1)

        # ── foreground skill ──
        if active_skill == "q":
            B._draw_battlehunger_foreground(surface, boss, x, y, skill_timer,
                                            pulse)
        elif active_skill == "e":
            B._draw_berserkerscall_foreground(surface, boss, x, y, skill_timer,
                                              pulse)
        elif active_skill == "r":
            B._draw_cullingblade_foreground(surface, boss, x, y, skill_timer,
                                            pulse)

class _NS_abaddon:
    """Namespace abaddon - PIXEL MASTERWORK v3 + Skill FX v3 (TRUE BOSS).

    Abaddon, Lord of Avernus: penunggang berhud di atas tungganjan
    hantu api cyan, bilah energi besar, dan empat skill (Q Mist Coil,
    W Aphotic Shield, E Darkness Gale, R Death Sever).

    Ditulis ulang penuh dari v2:
      * RIG. Kuda + penunggang dibangun sebagai rig pixel-art chunky
        berlapis: bayangan -> base api -> kuda (kaki jauh -> badan ->
        kaki dekat) -> cape -> penunggang (kaki jauh, torso, pauldron,
        hood, lengan + pedang) -> highlight -> mata. Satu buffer rig +
        outline gelap 4 arah.
      * ANIMASI. Controller state machine ber-prioritas (IDLE/WALK/RUN/
        CHARGE/CAST/SKILL/SPECIAL/HIT/HURT/DEATH) dengan delta-time
        nyata, 6 fase serangan (anticipation -> windup -> swing ->
        impact -> follow -> recovery), jendela hit aktif, respons hurt,
        dan impact satu kali per ayunan.
      * SWING. Bilah berotasi pada busur terdefinisi (sudut fungsi
        pose), jendela hit aktif, trail dibangun dari posisi UJUNG
        BILAH yang tersimpan (histori), impact flash, screen shake,
        hit-stop (lapisan hidup heroes/abaddon_fx memicu impact di
        frame benturan; fallback canvas menggambar versinya sendiri).
      * PROYEKTIL. 3 kelas dengan lifecycle penuh (spawn -> travel ->
        trail -> hit -> impact -> destroy), bentuk chunky ber-arah
        (bukan lingkaran polos): Mist Coil (orb + puing spiral +
        after-image terkuantisasi), Darkness Gale (dinding angin
        crescent), Death Sever (busur pita tebal + serpihan).
      * SKILL. Lifecycle telegraph -> charge -> release -> travel ->
        impact -> after-effect. W kini perisai PELAT HEKSAAGON
        berputar, bukan lingkaran besar. Bentuk: cincin putus-putus,
        chevron, serpihan, bintang, retakan tanah - satu bahasa bentuk.
      * GAME FEEL. hit-stop 0.03-0.08 s + screen shake meluruh lewat
        bus heroes/combat_feel (lapisan hidup).
      * DEBUG_CHARACTER. overlay hurtbox, hitbox ayunan, jangkauan,
        hit proyektil, state/frame/progress/skill/partikel/FPS.
      * PERFORMANCE. buffer rig + outline cache, plate tanah statis
        per skill, sprite api cache, partikel & proyektil dibatasi.

    Kontrak yang TIDAK berubah (gameplay + tes regresi):
      * ``draw_abaddon(surface, boss, x, y)`` - entry point tunggal.
      * ``SKILL_DUR`` sinkron dengan AI boss (30/90/40/60).
      * ``_ab_projectiles`` (di-park hero lane), ``_ab_coil_spawned``,
        ``_ab_gale_spawned``, ``_ab_sever_spawned``,
        ``_ab_attack_active``, ``_ab_attack_frame``,
        ``_ab_attack_progress``, ``_ab_prev_timer``, ``_ab_last_x``.

    Regresi: tools/test_abaddon_masterwork.py
    Audit  : tools/_audit_abaddon_v2.py
    Sheet  : tools/_shot_abaddon_max.py
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _STATIC_SURFACES = {}

    # Durasi status skill (frame) - HARUS sama dengan active_skill_timer
    # yang diisi AI boss (bosses/base_boss.py) dan skill hero
    # (hero_skills/_bundle.py).
    SKILL_DUR = {"q": 30, "w": 90, "e": 40, "r": 60}

    # Batas fase = fraksi 0..1 dari durasi serangan.
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.18),
        ("WINDUP",       0.18, 0.34),
        ("SWING",        0.34, 0.52),
        ("IMPACT",       0.52, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )
    #: jendela di mana bilah secara geometris menyapu depan badan
    ATTACK_ACTIVE_WINDOW = (0.36, 0.60)
    #: puncak benturan (FX impact + hit-stop dipicu di sini)
    ATTACK_IMPACT_FRAME = 0.56

    #: Prioritas state animasi. Angka besar menang; DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "SKILL": 50,
        "SPECIAL": 55,
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: Aktifkan untuk melihat hitbox/hurtbox/jangkauan/state di arena.
    DEBUG_CHARACTER = False

    # Buffer rig: extents terukur semua pose + margin. Anchor (0,0) =
    # pusat badan kuda; +x = arah hadap, +y = ke bawah.
    RIG_W, RIG_H = 224, 196
    RIG_OX, RIG_OY = 112, 82
    SHADOW_Y = 58          # bayangan kontak (ruang lokal)
    FLAME_Y = 46           # garis base api tunggangan (ruang lokal)
    SWORD_LEN = 46         # panjang tangan -> ujung bilah

    # ── HD Color Palette - dark purple / cyan flame (konsisten v2) ────
    PALETTE = {
        # Cape / cloth - deep purple
        "cape_darkest":   (18,   8,  32),
        "cape_dark":      (35,  20,  62),
        "cape_mid":       (60,  38, 105),
        "cape_light":     (95,  70, 155),
        "cape_high":      (140, 115, 195),
        "cape_shine":     (185, 165, 225),
        # Armor - dark purple/black dengan trim emas
        "armor_darkest":  (12,   8,  22),
        "armor_dark":     (28,  20,  48),
        "armor_mid":      (55,  42,  85),
        "armor_light":    (95,  78, 130),
        "armor_high":     (150, 130, 180),
        # Gold trim
        "gold_darkest":   (65,  42,  10),
        "gold_dark":      (115, 85,  25),
        "gold_mid":       (175, 140, 45),
        "gold_light":     (225, 190, 85),
        "gold_shine":     (250, 225, 145),
        # Horse body - dark blue-purple
        "horse_darkest":  (10,  15,  30),
        "horse_dark":     (25,  35,  60),
        "horse_mid":      (50,  70, 105),
        "horse_light":    (85, 115, 155),
        "horse_high":     (135, 170, 200),
        # Cyan flame / mist - warna tanda tangan
        "flame_darkest":  (5,   45,  55),
        "flame_dark":     (15,  95, 115),
        "flame_mid":      (40, 170, 185),
        "flame_light":    (95, 230, 235),
        "flame_bright":   (160, 250, 250),
        "flame_hot":      (215, 255, 255),
        "flame_white":    (240, 255, 255),
        # Sword blade - cyan energy
        "blade_darkest":  (30,  55,  70),
        "blade_dark":     (60, 120, 145),
        "blade_mid":      (110, 190, 210),
        "blade_light":    (170, 235, 240),
        "blade_shine":    (220, 250, 250),
        # Purple magic (skill)
        "magic_darkest":  (20,   5,  50),
        "magic_dark":     (55,  25, 115),
        "magic_mid":      (105, 60, 180),
        "magic_light":    (165, 120, 225),
        "magic_bright":   (210, 175, 250),
        "magic_hot":      (240, 220, 255),
        # Eye glow
        "eye_dark":       (30,  90, 100),
        "eye_mid":        (90, 200, 205),
        "eye_bright":     (170, 245, 245),
        "eye_hot":        (230, 255, 255),
        # Abu / debu
        "ash_dark":       (58,  52,  72),
        "ash_mid":        (96,  88, 112),
        "ash_light":      (140, 132, 160),
        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   4,   8),
        "outline":        (4,   4,  10),
        "white":          (255, 255, 255),
    }

    # ==================================================================
    # PRIMITIF HELPER
    # ==================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _hash01(i):
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_abaddon._clamp((a[0] + (b[0] - a[0]) * t,
                                   a[1] + (b[1] - a[1]) * t,
                                   a[2] + (b[2] - a[2]) * t))

    def _static(key, builder):
        surf = _NS_abaddon._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_abaddon._STATIC_SURFACES[key] = surf
        return surf

    def _fx_scale(boss):
        """Skala FX world-space untuk lane hero (canvas dikecilkan)."""
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_r):
        return max(1, int(round(float(world_r) * _NS_abaddon._fx_scale(boss))))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_abaddon._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_abaddon.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_abaddon._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = max(1, int(width))
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 6
            h = abs(ey - sy) + width * 4 + 6
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), width)
            surface.blit(temp, (min_x, min_y))
            return
        if _NS_abaddon.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color[:3], (sx, sy), (ex, ey))
                return
            except Exception:
                pass
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    def _poly(surface, color, points):
        if not points or len(points) < 3:
            return
        color = _NS_abaddon._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(
                temp, color,
                [(int(p[0] - min_x), int(p[1] - min_y)) for p in points])
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3],
                            [(int(px), int(py)) for px, py in points])

    def _ellipse(surface, color, rect, width=0):
        color = _NS_abaddon._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], (rx, ry, rw, rh), width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_abaddon._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], (rx, ry, rw, rh),
                         border_radius=border_radius)

    # ==================================================================
    # FX VOCABULARY (bahasa bentuk yang sama di semua efek)
    # ==================================================================
    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_abaddon._aaline(
                surface, (*color, _NS_abaddon._alpha(alpha)),
                (int(cx), int(cy)),
                (int(cx + math.cos(ang) * ln),
                 int(cy + math.sin(ang) * ln * 0.8)),
                2 if k % 2 == 0 else 1)
        if core:
            _NS_abaddon._aacircle(surface,
                                  (*core, _NS_abaddon._alpha(alpha)),
                                  (int(cx), int(cy)),
                                  max(1, int(size * 0.3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_abaddon._aaline(
                surface, (*color, _NS_abaddon._alpha(alpha)),
                (int(cx + px * s * size * 0.55 - ca * size * 0.5),
                 int(cy + py * s * size * 0.55 - sa * size * 0.5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=0.92):
        """Cincin PUTUS-PUTUS chunky yang berputar (marker AOE/rune)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_abaddon._aaline(surface, (*color,
                                          _NS_abaddon._alpha(alpha)),
                                p0, p1, thick)

    def _shard(surface, cx, cy, ang, length, width, color, alpha,
               core=None):
        """Serpihan kristal: belah ketupat runcing searah ``ang``."""
        if alpha <= 0 or length <= 1:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        pts = [(cx + ca * length, cy + sa * length),
               (cx + nx * width, cy + ny * width),
               (cx - ca * length * 0.45, cy - sa * length * 0.45),
               (cx - nx * width, cy - ny * width)]
        _NS_abaddon._poly(surface,
                          (*color, _NS_abaddon._alpha(alpha)),
                          [(int(px), int(py)) for px, py in pts])
        if core:
            _NS_abaddon._aaline(
                surface, (*core, _NS_abaddon._alpha(alpha)),
                (int(cx - ca * length * 0.3), int(cy - sa * length * 0.3)),
                (int(cx + ca * length * 0.8), int(cy + sa * length * 0.8)),
                1)

    def _ribbon(surface, path, widths, color, alpha):
        """Pita tebal-tipis dari daftar titik (trail ujung bilah)."""
        if len(path) < 3 or alpha <= 0:
            return
        left, right = [], []
        for i, (px, py) in enumerate(path):
            if i == 0:
                dx, dy = path[1][0] - px, path[1][1] - py
            elif i == len(path) - 1:
                dx, dy = px - path[-2][0], py - path[-2][1]
            else:
                dx = path[i + 1][0] - path[i - 1][0]
                dy = path[i + 1][1] - path[i - 1][1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            w = widths[i]
            left.append((px + nx * w, py + ny * w))
            right.append((px - nx * w, py - ny * w))
        _NS_abaddon._poly(surface,
                          (*color, _NS_abaddon._alpha(alpha)),
                          [(int(a), int(b)) for a, b in left + right[::-1]])

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus menjadi tepi bergerigi (pixel-art kain)."""
        if not spine:
            return spine
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
                d = depth * (0.55 + 0.45 * _NS_abaddon._hash01(
                    i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _dither_dots(surface, color, points, alpha=70):
        """Checkerboard 50% 1-px (band dither klasik)."""
        a = _NS_abaddon._alpha(alpha)
        if a <= 0:
            return
        col = (*_NS_abaddon._clamp(color)[:3], a)
        for x, y in points:
            ix, iy = int(x), int(y)
            if (ix + iy) & 1:
                _NS_abaddon._rect(surface, col, (ix, iy, 1, 1))

    # -- sprite api cyan yang di-cache (dipakai puluhan titik/frame) ----
    _FLAME_CACHE = {}

    def _flame_sprite(size, alpha):
        """Sprite api cyan per (size, alpha//8) - dibangun sekali."""
        key = (size, alpha)
        spr = _NS_abaddon._FLAME_CACHE.get(key)
        if spr is None:
            r = size + 4
            f = pygame.Surface((r * 2, r * 2 + 4), pygame.SRCALPHA)
            cx0, cy0 = r, r + 2
            p = _NS_abaddon.PALETTE
            _NS_abaddon._aacircle(f, (*p["flame_darkest"], alpha // 3),
                                  (cx0, cy0), size + 3)
            _NS_abaddon._aacircle(f, (*p["flame_dark"], alpha // 2),
                                  (cx0, cy0), size + 1)
            _NS_abaddon._aacircle(f, (*p["flame_mid"], alpha), (cx0, cy0),
                                  size)
            _NS_abaddon._aacircle(f, (*p["flame_light"], alpha),
                                  (cx0, cy0 - 1), max(1, size - 2))
            _NS_abaddon._aacircle(f, (*p["flame_bright"], alpha),
                                  (cx0, cy0 - 2), max(1, size - 4))
            if size > 3:
                _NS_abaddon._aacircle(f, (*p["flame_hot"], alpha),
                                      (cx0, cy0 - 3), max(1, size - 6))
            spr = f
            _NS_abaddon._FLAME_CACHE[key] = spr
        return spr

    def _draw_flame(surface, x, y, size, alpha):
        """Blit sprite api cyan (cache) di (x, y)."""
        s = max(1, int(size))
        a = max(0, min(255, int(alpha))) // 8 * 8
        if a <= 8:
            return
        spr = _NS_abaddon._flame_sprite(s, a)
        surface.blit(spr, (int(x) - (s + 4), int(y) - (s + 6)))

    # ==================================================================
    # KOORDINAT TARGET (kompensasi scale untuk lane hero offscreen)
    # ==================================================================
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        if target is not None and getattr(target, "alive", True):
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 200.0 / scale * getattr(boss, "direction", 1)),
                int(y))

    # ==================================================================
    # CONTROLLER ANIMASI (state, fase, timing, delta-time, jendela hit)
    # ==================================================================
    def attack_phases_order():
        """Urutan nama fase (dipakai test & alat audit)."""
        return tuple(name for name, _a, _b in _NS_abaddon.ATTACK_PHASES)

    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1 (None di luar)."""
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_abaddon.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _resolve_anim_state(boss, active, phase, moving, skill):
        """State animasi yang DIINGINKAN frame ini (ber-prioritas)."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_ab_hurt_frames", 0)) > 0:
            return "HURT"
        if skill == "r":
            return "SPECIAL"
        if skill:
            return "SKILL"
        if active:
            if phase in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if phase in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if moving:
            return ("RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2
                    else "WALK")
        return "IDLE"

    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (ruang permukaan) saat jendela hit aktif."""
        if not getattr(boss, "_ab_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        scale = _NS_abaddon._fx_scale(boss)
        reach = int(56 * scale)
        top = int(cy - 42 * scale)
        h = int(72 * scale)
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    def _update_attack_anim(boss):
        """ANIMATION CONTROLLER Abaddon - satu sumber kebenaran.

        Menulis:
          * ``_ab_dt``              delta-time nyata (detik, dijepit)
          * ``_ab_attack_active``   serangan sedang berjalan  (nama lama)
          * ``_ab_attack_frame``    frame ke-n dalam serangan  (nama lama)
          * ``_ab_attack_progress`` 0..1 sepanjang serangan   (nama lama)
          * ``_ab_attack_phase``    ANTICIPATION/.../RECOVERY
          * ``_ab_hit_active``      True hanya di jendela hit aktif
          * ``_ab_hurt_frames``     sisa frame respons kena damage
          * ``_ab_state`` / ``_ab_state_prev`` / ``_ab_state_time``
          * ``_ab_swing_seq``       id unik per ayunan (untuk FX impact)

        Serangan dikenali dari lompatan timer ke atas (cooldown dipasang
        saat attack mendarat) plus detak jam; pemanggil yang menggerakkan
        ``_ab_attack_progress`` sendiri (alat preview/tes) dihormati via
        mode ``_ab_attack_manual``.
        """
        # ── delta time nyata ──────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                          # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_ab_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._ab_last_ms = now
        boss._ab_dt = dt

        # ── timeline serangan ─────────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 43)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ab_prev_timer", 0))
        active = bool(getattr(boss, "_ab_attack_active", False))
        manual = bool(getattr(boss, "_ab_attack_manual", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._ab_attack_active = True
            boss._ab_attack_frame = 0
            boss._ab_attack_manual = False
            boss._ab_swing_seq = int(getattr(boss, "_ab_swing_seq", 0)) + 1
            active = True
        elif active and timer > 0:
            boss._ab_attack_frame = int(getattr(boss, "_ab_attack_frame",
                                                0)) + 1
            boss._ab_attack_manual = False
        elif timer <= 0:
            if active and not manual and \
                    float(getattr(boss, "_ab_attack_progress", 0.0)) > 0.0:
                boss._ab_attack_manual = True
            else:
                boss._ab_attack_active = False
                boss._ab_attack_frame = 0
                boss._ab_attack_manual = False
                active = False
        boss._ab_prev_timer = timer

        frame = int(getattr(boss, "_ab_attack_frame", 0)) if active else 0
        span = max(1, cooldown - 1)
        if active and bool(getattr(boss, "_ab_attack_manual", False)):
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_ab_attack_progress", 0.0))))
            boss._ab_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
        boss._ab_attack_progress = progress

        phase = _NS_abaddon.attack_phase(progress) if active else "NONE"
        boss._ab_attack_phase = phase
        lo, hi = _NS_abaddon.ATTACK_ACTIVE_WINDOW
        boss._ab_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ────────────────────────────────
        hurt = int(getattr(boss, "_ab_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10
        boss._ab_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── state machine ber-prioritas ───────────────────────────────
        moving = bool(getattr(boss, "_ab_moving_cached", False))
        skill = getattr(boss, "active_skill", None)
        want = _NS_abaddon._resolve_anim_state(boss, active, phase, moving,
                                               skill)
        cur = getattr(boss, "_ab_state", None)
        if cur is None:
            boss._ab_state = want
            boss._ab_state_prev = want
            boss._ab_state_time = 0.0
        elif want != cur:
            cur_p = _NS_abaddon.ANIM_STATES.get(cur, 0)
            new_p = _NS_abaddon.ANIM_STATES.get(want, 0)
            stime = float(getattr(boss, "_ab_state_time", 0.0))
            if cur != "DEATH" and (new_p >= cur_p or stime > 0.08):
                boss._ab_state_prev = cur
                boss._ab_state = want
                boss._ab_state_time = 0.0
            else:
                boss._ab_state_time = stime + dt
        else:
            boss._ab_state_time = float(getattr(boss, "_ab_state_time",
                                                0.0)) + dt

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_ab_last_x"):
            boss._ab_last_x = cur_x
            boss._ab_last_y = cur_y
            boss._ab_moving_cached = False
            return False
        moved = abs(cur_x - boss._ab_last_x) + abs(cur_y - boss._ab_last_y)
        boss._ab_last_x = cur_x
        boss._ab_last_y = cur_y
        moving = moved > 0.3
        boss._ab_moving_cached = moving
        return moving

    # ==================================================================
    # POSE - satu sumber kebenaran untuk rig, trail, DAN lapisan hidup
    # ==================================================================
    # Kunci pose: 0 = siap (bilah carried), 0.30 = puncak wind-up
    # (di atas kepala), 0.62 = frame impact (menyapu depan-bawah),
    # 1.0 = kembali siap.
    _SW_REST = 0.95
    _SW_WIND = 3.02
    _SW_HIT = 1.04
    _POSE_WIND = 0.30
    _POSE_HIT = 0.62

    def _attack_curve(ap):
        """Progres mentah 0..1 -> waktu pose 0..1 (MONOTON naik).

        Memberi: (a) anticipation jelas, (b) HOLD wind-up, (c) tebasan
        yang dipercepat, (d) HOLD impact 1-2 frame, (e) follow-through
        meluruh - kontras laju ~10x antara tebasan dan hold.
        """
        if ap <= 0.0:
            return 0.0
        if ap >= 1.0:
            return 1.0
        w = _NS_abaddon._POSE_WIND
        h = _NS_abaddon._POSE_HIT
        if ap < 0.18:                       # anticipation: angkat bilah
            t = ap / 0.18
            return w * (t ** 0.85)
        if ap < 0.34:                       # WINDUP HOLD (di atas kepala)
            return w
        if ap < 0.52:                       # tebasan: dipercepat
            t = (ap - 0.34) / 0.18
            return w + (h - w) * (t ** 1.30)
        if ap < 0.62:                       # IMPACT HOLD (nyaris beku)
            return h
        t = (ap - 0.62) / 0.38              # follow-through -> siap
        return h + (1.0 - h) * (t ** 0.80)

    def _sword_angle(pose):
        """Sudut bilah (rad). tip = hand + (sin a * L, cos a * L).

        a = 0 ke bawah, a = pi/2 ke depan, a = pi ke atas.
        """
        if pose <= _NS_abaddon._POSE_WIND:
            t = pose / _NS_abaddon._POSE_WIND
            return (_NS_abaddon._SW_REST +
                    (_NS_abaddon._SW_WIND - _NS_abaddon._SW_REST) * t)
        if pose <= _NS_abaddon._POSE_HIT:
            t = ((pose - _NS_abaddon._POSE_WIND) /
                 (_NS_abaddon._POSE_HIT - _NS_abaddon._POSE_WIND))
            return (_NS_abaddon._SW_WIND +
                    (_NS_abaddon._SW_HIT - _NS_abaddon._SW_WIND) * t)
        t = (pose - _NS_abaddon._POSE_HIT) / (1.0 - _NS_abaddon._POSE_HIT)
        return _NS_abaddon._SW_HIT + \
            (_NS_abaddon._SW_REST - _NS_abaddon._SW_HIT) * t

    def _pose(boss, x, y, ap_override=None):
        """Hitung seluruh pose rig dalam SATU tempat (murni).

        ``ap_override`` mengganti progress serangan (dipakai trail yang
        menyampling pose ke belakang). Return dict dengan semua angka
        yang dibutuhkan rig, trail, dan lapisan hidup:

        facing, phase, action, ap, pose, sword_angle, skill, skill_p,
        lunge, lean, bob, gallop, hurt, active, trailing, hot, swing_id,
        hand (x, y dunia), tip (x, y dunia).
        """
        phase = float(getattr(boss, "pulse", 0.0))
        facing = int(getattr(boss, "direction", 1)) or 1
        active_skill = getattr(boss, "active_skill", None)
        attacking = bool(getattr(boss, "_ab_attack_active", False))
        hurt = int(getattr(boss, "_ab_hurt_frames", 0)) > 0
        moving = bool(getattr(boss, "_ab_moving_cached", False))

        if not getattr(boss, "alive", True):
            action = "death"
        elif active_skill:
            action = active_skill
        elif attacking:
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        ap = (max(0.0, min(1.0, float(getattr(boss, "_ab_attack_progress",
                                             0.0))))
              if attacking else 0.0)
        if ap_override is not None:
            ap = max(0.0, min(1.0, float(ap_override)))
        pose = _NS_abaddon._attack_curve(ap) if attacking else 0.0

        dur = float(_NS_abaddon.SKILL_DUR.get(action, 40) or 40) \
            if action in _NS_abaddon.SKILL_DUR else 40.0
        timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        skill_p = (max(0.0, min(1.0, 1.0 - timer / dur))
                   if action in _NS_abaddon.SKILL_DUR else 0.0)

        # ── offset badan ──────────────────────────────────────────────
        lunge = 0
        lean = 0
        bob = 0
        gallop = phase * 1.5
        if action == "walk":
            gallop = phase * 2.2
            bob = int(abs(math.sin(gallop)) * 3)
            lean = int(math.sin(gallop) * 2)
        elif action == "attack":
            k = math.sin(min(1.0, ap / 0.62) * math.pi)
            lunge = int(k * 7)
            lean = int(k * 6) - (4 if ap < 0.34 else 0)
        elif action == "q":
            lean = 2
            lunge = int(math.sin(skill_p * math.pi) * 3)
        elif action == "w":
            lean = -2
        elif action == "e":
            lunge = int(math.sin(skill_p * math.pi) * 14)
            lean = 4
            gallop = phase * 3.2
        elif action == "r":
            if skill_p < 0.55:
                lean = -4
                lunge = -2
            else:
                k = min(1.0, (skill_p - 0.55) / 0.18)
                lunge = int(math.sin(k * math.pi) * 10)
                lean = int(k * 8)
        if hurt:
            lean -= 5
            bob = 1

        # ── sudut bilah per aksi ──────────────────────────────────────
        if action == "attack":
            sword_angle = _NS_abaddon._sword_angle(pose)
        elif action == "q":
            sword_angle = 1.35 + math.sin(phase * 2.0) * 0.04
        elif action == "w":
            sword_angle = 0.55 + math.sin(phase * 1.4) * 0.03
        elif action == "e":
            sword_angle = 1.5 + math.sin(phase * 2.4) * 0.05
        elif action == "r":
            if skill_p < 0.55:
                sword_angle = 2.95 - skill_p * 0.1
            else:
                k = min(1.0, (skill_p - 0.55) / 0.18)
                sword_angle = 2.95 + (0.9 - 2.95) * (k ** 0.9)
        elif action == "death":
            sword_angle = 1.25
        elif action == "walk":
            sword_angle = _NS_abaddon._SW_REST + \
                math.sin(phase * 0.62) * 0.05 + math.sin(gallop) * 0.04
        else:
            sword_angle = _NS_abaddon._SW_REST + \
                math.sin(phase * 0.62) * 0.06

        # ── tangan + ujung bilah (dunia) ──────────────────────────────
        # hand lokal (28, -22); ikut lunge + lean + bob
        hx = 28 + lean
        hy = -22 + bob
        tip_lx = hx + math.sin(sword_angle) * _NS_abaddon.SWORD_LEN
        tip_ly = hy + math.cos(sword_angle) * _NS_abaddon.SWORD_LEN
        f = 1 if facing >= 0 else -1
        hand = (int(x + (hx + lunge) * f), int(y + hy))
        tip = (int(x + (tip_lx + lunge) * f), int(y + tip_ly))

        # ── flag trail & impact ───────────────────────────────────────
        trailing = False
        hot = False
        swing_id = None
        if action == "attack":
            trailing = 0.34 <= ap < 0.70
            swing_id = int(getattr(boss, "_ab_swing_seq", 0))
        if action == "r" and skill_p >= 0.55:
            # penanda lepas R: seq negatif unik per skill instance
            if not getattr(boss, "_ab_r_released", False):
                boss._ab_r_released = True
                boss._ab_release_seq = int(getattr(boss, "_ab_release_seq",
                                                   1)) + 1
            trailing = 0.55 <= skill_p < 0.80
            hot = True
            swing_id = -int(getattr(boss, "_ab_release_seq", 1))
        if action != "r" and getattr(boss, "_ab_r_released", False):
            boss._ab_r_released = False

        return {
            "facing": facing,
            "phase": phase,
            "action": action,
            "ap": ap,
            "pose": pose,
            "sword_angle": sword_angle,
            "skill": active_skill,
            "skill_p": skill_p,
            "lunge": lunge,
            "lean": lean,
            "bob": bob,
            "gallop": gallop,
            "hurt": hurt,
            "active": action == "attack",
            "trailing": trailing,
            "hot": hot,
            "swing_id": swing_id,
            "hand": hand,
            "tip": tip,
        }

    def _swing_tip(boss, x, y):
        """Untuk lapisan hidup (heroes/abaddon_fx): keadaan tebasan.

        Return dict kecil dengan angka dunia yang perlu direkam layar:
        tip dunia, progress, jendela trail, flag impact, id ayunan.
        """
        p = _NS_abaddon._pose(boss, x, y)
        impact_frame = _NS_abaddon.ATTACK_IMPACT_FRAME
        if p["action"] == "r":
            # sweep R: progress sweep 0..1 + frame impact sweep
            sp = p["skill_p"]
            impact_frame = 0.55 + 0.18 * 0.85
            p_ap = max(0.0, min(1.0, (sp - 0.55) / 0.18))
        else:
            p_ap = p["ap"]
        return {
            "active": p["active"] or (p["action"] == "r"
                                      and p["skill_p"] >= 0.55),
            "ap": p_ap,
            "tip_x": p["tip"][0],
            "tip_y": p["tip"][1],
            "trailing": p["trailing"],
            "hot": p["hot"],
            "swing_id": p["swing_id"],
            "impact_frame": impact_frame,
        }

    # ==================================================================
    # LAPISAN FX HIDUP (heroes/abaddon_fx)
    # ==================================================================
    _LIVE_MOD = None

    def _live_module():
        """Muat ``heroes.abaddon_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_abaddon
        if NS._LIVE_MOD is None:
            try:
                from heroes import abaddon_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "ABADDON_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup Abaddon bisa dipakai (tooling)."""
        return _NS_abaddon._live_module() is not None

    # ==================================================================
    # RIG: buffer -> outline 4 arah -> satu blit
    # ==================================================================
    def _draw_rig_at(surface, x, y, p, flash=0):
        """Rig -> buffer -> (hurt flash) -> outline gelap -> blit.

        Buffer sekecil mungkin karena outline menyalinnya 4x per frame.
        """
        B = _NS_abaddon
        buf = pygame.Surface((B.RIG_W, B.RIG_H), pygame.SRCALPHA)
        B._draw_rig(buf, B.RIG_OX, B.RIG_OY, p)
        if flash > 0:
            w = int(235 * min(1.0, flash / 8.0))
            if w > 0:
                lit = buf.copy()
                lit.fill((255, 250, 245, 0),
                         special_flags=pygame.BLEND_RGBA_MAX)
                lit.set_alpha(w)
                buf.blit(lit, (0, 0))
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        ox = int(x) - B.RIG_OX
        oy = int(y) - B.RIG_OY
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))

    def _draw_rig(surface, ox, oy, p):
        """Seluruh badan dari sendi, urutan belakang -> depan.

        (ox, oy) = posisi anchor dunia di dalam buffer.
        """
        B = _NS_abaddon
        p_ = B.PALETTE
        f = 1 if p["facing"] >= 0 else -1
        dx = p["lunge"] * f
        dy = p["bob"]
        phase = p["phase"]
        action = p["action"]
        gallop = p["gallop"]
        galloping = action == "walk"

        def L(lx, ly):
            """Lokal -> buffer (+lunge/+bob)."""
            return (ox + int(lx * f + dx), oy + int(ly + dy))

        def poly(color, coords, outline=True):
            pts = [L(a, b) for a, b in coords]
            if outline:
                B._poly(surface, p_["outline"],
                        [(qx + f, qy + 1) for qx, qy in pts])
            B._poly(surface, color, pts)

        def poly_free(color, pts, outline=True):
            """Poligon dengan titik sudah dalam ruang buffer."""
            if outline:
                B._poly(surface, p_["outline"],
                        [(qx + f, qy + 1) for qx, qy in pts])
            B._poly(surface, color, pts)

        # ══ 1. KAKI JAUH (lebih gelap, di balik badan kuda) ═══════════
        B._draw_ab_legs(surface, L, p_, f, gallop, galloping, near=False)

        # ══ 2. EKOR API (di balik badan) ═════════════════════════════
        tail_sway = math.sin(phase * 1.3) * 3
        for i in range(6):
            t = i / 5.0
            tx = -44 - t * 30 + math.sin(phase * 1.6 + i * 1.2) * (2 + t * 3)
            ty = -6 + t * 10 + tail_sway * t
            s = max(1, int(5 - t * 3.4))
            B._draw_flame(surface, L(tx, ty)[0], L(tx, ty)[1], s,
                          int(225 * (1 - t * 0.55)))

        # ══ 3. BADAN KUDA (3 nilai + garis punggung) ═════════════════
        body_outer = [
            (-46, -4), (-42, -12), (-30, -18), (-12, -21), (10, -21),
            (26, -17), (38, -10), (45, -2), (46, 8), (41, 16), (28, 20),
            (6, 22), (-16, 21), (-36, 17), (-44, 9),
        ]
        poly(p_["horse_darkest"], body_outer)
        poly(p_["horse_dark"], [
            (-43, -3), (-39, -10), (-28, -15), (-11, -18), (9, -18),
            (24, -14), (35, -8), (42, -1), (43, 7), (38, 14), (26, 17),
            (5, 19), (-15, 18), (-33, 14), (-41, 8),
        ], outline=False)
        poly(p_["horse_mid"], [
            (-34, -8), (-28, -12), (-12, -14), (8, -14), (22, -11),
            (32, -6), (34, 0), (30, 9), (20, 13), (0, 14), (-20, 13),
            (-32, 8),
        ], outline=False)
        # garis punggung (terang) - cahaya jatuh di atas
        B._aaline(surface, p_["horse_light"], L(-30, -16), L(24, -15), 2)
        B._aaline(surface, p_["horse_high"], L(-24, -17), L(14, -17), 1)
        # bayangan perut
        B._aaline(surface, p_["horse_darkest"], L(-24, 19), L(22, 18), 2)

        # ══ 4. LEHER + KEPALA KUDA ═══════════════════════════════════
        neck = [(24, -16), (33, -12), (51, -34), (54, -27), (38, -7)]
        poly(p_["horse_darkest"], neck)
        poly(p_["horse_dark"], [(26, -14), (33, -11), (49, -31), (51, -26),
                                (37, -8)], outline=False)
        poly(p_["horse_mid"], [(28, -13), (33, -10), (47, -29), (48, -26),
                               (36, -9)], outline=False)
        head = [(42, -42), (48, -47), (59, -43), (63, -36), (61, -29),
                (52, -27), (44, -32)]
        poly(p_["horse_darkest"], head)
        poly(p_["horse_dark"], [(44, -41), (49, -45), (58, -42),
                                (61, -36), (59, -30), (51, -28), (45, -32)],
             outline=False)
        poly(p_["horse_mid"], [(46, -40), (50, -43), (57, -41), (59, -36),
                               (57, -31), (50, -29), (46, -32)],
             outline=False)
        # telinga
        poly(p_["horse_darkest"], [(46, -47), (50, -46), (48, -53)])
        # garis mulut + hidung
        B._aaline(surface, p_["horse_darkest"], L(52, -28), L(60, -31), 1)
        B._aaline(surface, p_["horse_darkest"], L(62, -33), L(62, -31), 2)
        # mata kuda menyala
        eye_pulse = 0.75 + 0.25 * math.sin(phase * 2.0)
        ex, ey = L(53, -37)
        B._aacircle(surface, p_["shadow_deep"], (ex, ey), 2)
        B._aacircle(surface, (*p_["eye_dark"],
                              int(200 * eye_pulse)), (ex, ey), 2)
        B._aacircle(surface, p_["eye_bright"], (ex, ey), 1)
        B._aacircle(surface, p_["eye_hot"], (ex, ey), 1)

        # ══ 5. PUNGGUNG API (sepanjang leher) ════════════════════════
        for i in range(5):
            t = i / 4.0
            mx = 27 + t * 24
            my = -15 - t * 20
            s = max(1, int(4 - t * 2))
            B._draw_flame(surface, L(mx, my)[0], L(mx, my)[1], s,
                          int(200 * (1 - t * 0.4)))

        # ══ 6. KAKI DEKAT ════════════════════════════════════════════
        B._draw_ab_legs(surface, L, p_, f, gallop, galloping, near=True)

        # ══ 7. SELIMUT SADDLE ════════════════════════════════════════
        poly(p_["cape_darkest"], [(-14, -21), (12, -21), (10, -12),
                                  (-16, -12)])
        poly(p_["cape_dark"], [(-12, -19), (10, -19), (9, -14), (-14, -14)],
             outline=False)
        B._aaline(surface, p_["gold_dark"], L(-14, -12), L(10, -12), 2)
        B._aaline(surface, p_["gold_mid"], L(-13, -12), L(9, -12), 1)

        # ══ 8. CAPE (di belakang penunggang) ═════════════════════════
        B._draw_ab_cape(surface, L, p_, f, phase, p)

        # ══ 9. KAKI PENUNGGANG (jauh, di balik torso) ════════════════
        knee_f = 6 + (2 if action == "attack" else 0)
        poly(p_["armor_darkest"], [(0, -22), (6, -22), (knee_f + 2, -12),
                                   (knee_f - 3, -12)])
        B._aaline(surface, p_["armor_dark"], L(2, -20), L(knee_f, -14), 3)
        # sepatu jauh (gantung di sisi kuda)
        poly(p_["armor_darkest"], [(knee_f - 3, -12), (knee_f + 3, -12),
                                   (knee_f + 5, -4), (knee_f - 1, -4)])

        # ══ 10. TORSO PENUNGGANG ═════════════════════════════════════
        torso = [(-14, -48), (13, -48), (16, -36), (12, -18), (-11, -18),
                 (-16, -36)]
        poly(p_["armor_darkest"], torso)
        poly(p_["armor_dark"], [(-12, -46), (11, -46), (14, -36),
                                (10, -20), (-9, -20), (-14, -36)],
             outline=False)
        poly(p_["armor_mid"], [(-9, -43), (9, -43), (11, -36),
                               (7, -24), (-7, -24), (-11, -36)],
             outline=False)
        # bidang dada (cahaya dari depan-atas)
        poly(p_["armor_light"], [(2, -43), (10, -43), (11, -36),
                                 (5, -30)], outline=False)
        poly(p_["armor_high"], [(3, -42), (8, -42), (9, -38), (4, -35)],
             outline=False)
        # V-trim emas
        B._aaline(surface, p_["gold_dark"], L(-10, -45), L(0, -26), 2)
        B._aaline(surface, p_["gold_dark"], L(10, -45), L(0, -26), 2)
        B._aaline(surface, p_["gold_mid"], L(-9, -44), L(0, -27), 1)
        B._aaline(surface, p_["gold_mid"], L(9, -44), L(0, -27), 1)
        # permata dada cyan
        gem_x, gem_y = L(0, -32)
        pulse_g = 0.7 + 0.3 * math.sin(phase * 2.4)
        B._aacircle(surface, p_["shadow_deep"], (gem_x, gem_y), 4)
        B._aacircle(surface, p_["flame_darkest"], (gem_x, gem_y), 3)
        B._aacircle(surface, (*p_["flame_mid"], int(230 * pulse_g)),
                    (gem_x, gem_y), 3)
        B._aacircle(surface, p_["flame_bright"], (gem_x, gem_y), 2)
        B._rect(surface, p_["flame_hot"], (gem_x, gem_y - 1, 1, 1))
        # sabuk + gesper emas
        belt = [L(-13, -19), L(11, -19), L(11, -15), L(-13, -15)]
        B._poly(surface, p_["cape_darkest"], belt)
        B._poly(surface, p_["cape_dark"],
                [L(-12, -18), L(10, -18), L(10, -16), L(-12, -16)])
        buckle = [L(-3, -19), L(3, -19), L(3, -15), L(-3, -15)]
        B._poly(surface, p_["gold_dark"], buckle)
        B._poly(surface, p_["gold_mid"],
                [L(-2, -18), L(2, -18), L(2, -16), L(-2, -16)])

        # ══ 11. PAULDRON BELAKANG ════════════════════════════════════
        poly(p_["armor_darkest"], [(-20, -50), (-12, -50), (-11, -42),
                                   (-19, -42)])
        poly(p_["armor_dark"], [(-19, -49), (-13, -49), (-12, -44),
                                (-18, -44)], outline=False)
        poly(p_["armor_darkest"], [(-18, -50), (-15, -56), (-14, -50)])

        # ══ 12. LERENG + HOOD (kepala = subjek gambar) ═══════════════
        B._aaline(surface, p_["armor_darkest"], L(-4, -50), L(5, -50), 5)
        # hood luar (ungu dalam)
        hood = [(-13, -54), (-10, -66), (-4, -70), (5, -70), (11, -65),
                (14, -54), (12, -46), (4, -42), (-6, -42), (-13, -47)]
        poly(p_["cape_darkest"], hood)
        hood2 = [(-11, -54), (-8, -64), (-3, -67), (4, -67), (9, -63),
                 (12, -54), (10, -47), (3, -44), (-5, -44), (-11, -49)]
        poly(p_["cape_dark"], hood2, outline=False)
        poly(p_["cape_mid"], [(-9, -56), (-6, -62), (0, -64), (6, -62),
                              (9, -55), (7, -50), (-7, -50)], outline=False)
        # rongga wajah gelap
        face = [(-3, -58), (8, -58), (9, -49), (4, -45), (-4, -47),
                (-5, -53)]
        B._poly(surface, p_["shadow_deep"], [L(*q) for q in face])
        # alis helm emas
        B._aaline(surface, p_["gold_dark"], L(-8, -56), L(10, -56), 2)
        B._aaline(surface, p_["gold_mid"], L(-7, -56), L(9, -56), 1)
        # mata menyala - nilai tertinggi di sprite
        eye_p = 0.8 + 0.2 * math.sin(phase * 2.0)
        for eoff in (0, 5):
            gx, gy = L(0 + eoff, -52)
            B._rect(surface, p_["shadow_deep"], (gx - 1, gy - 1, 4, 3))
            B._aacircle(surface, (*p_["eye_dark"], int(120 * eye_p)),
                        (gx + 1, gy), 3)
            B._rect(surface, p_["eye_mid"], (gx, gy, 3, 2))
            B._rect(surface, p_["eye_bright"], (gx, gy, 2, 1))
            B._rect(surface, p_["eye_hot"], (gx, gy, 1, 1))
        # tanduk helm (melengkung ke atas-belakang)
        for s0, s1, s2 in (((-8, -64), (-12, -68), (-15, -71)),
                           ((10, -66), (14, -69), (17, -71))):
            a0, a1, a2 = L(*s0), L(*s1), L(*s2)
            B._aaline(surface, p_["armor_darkest"], a0, a1, 3)
            B._aaline(surface, p_["armor_darkest"], a1, a2, 2)
            B._aaline(surface, p_["armor_mid"], a0, a1, 1)
            B._draw_flame(surface, a2[0], a2[1], 2, 190)
        # wisp api kecil dari puncak hood
        B._draw_flame(surface, L(1, -70)[0], L(1, -70)[1], 3, 180)

        # ══ 13. LANGAN REINS (lengan + tali ke kepala kuda) ══════════
        shoulder_b = L(-14, -44)
        elbow_b = L(-20, -36)
        hand_b = L(-24, -30)
        B._aaline(surface, p_["shadow_deep"],
                  (shoulder_b[0] + f, shoulder_b[1] + 1),
                  (elbow_b[0] + f, elbow_b[1] + 1), 7)
        B._aaline(surface, p_["armor_darkest"], shoulder_b, elbow_b, 6)
        B._aaline(surface, p_["armor_dark"], shoulder_b, elbow_b, 4)
        B._aaline(surface, p_["armor_mid"], elbow_b, hand_b, 5)
        B._aaline(surface, p_["armor_light"], elbow_b, hand_b, 2)
        B._aacircle(surface, p_["armor_darkest"], hand_b, 4)
        B._aacircle(surface, p_["armor_mid"], hand_b, 2)
        # tali reins: lengkung 2 segmen ke mulut kuda
        mx = (hand_b[0] + L(56, -30)[0]) // 2
        my = (hand_b[1] + L(56, -30)[1]) // 2 + 3
        B._aaline(surface, p_["cape_darkest"], hand_b, (mx, my), 1)
        B._aaline(surface, p_["cape_darkest"], (mx, my), L(56, -30), 1)

        # ══ 14. LANGAN PEDANG (lengan 2-tulang) ══════════════════════
        shoulder_f = L(15, -44)
        # siku: titik tengah + bengkok; hand sudah termasuk lunge/lean
        hand_l = L(28 + p["lean"], -22 + p["bob"])
        mid_x = (shoulder_f[0] + hand_l[0]) // 2
        mid_y = (shoulder_f[1] + hand_l[1]) // 2
        ddx = hand_l[0] - shoulder_f[0]
        ddy = hand_l[1] - shoulder_f[1]
        dlen = math.hypot(ddx, ddy) or 1.0
        elbow_f = (int(mid_x + (-ddy / dlen) * 5),
                   int(mid_y + (ddx / dlen) * 5))
        B._aaline(surface, p_["shadow_deep"],
                  (shoulder_f[0] + f, shoulder_f[1] + 1),
                  (elbow_f[0] + f, elbow_f[1] + 1), 8)
        B._aaline(surface, p_["armor_darkest"], shoulder_f, elbow_f, 7)
        B._aaline(surface, p_["armor_dark"], shoulder_f, elbow_f, 5)
        B._aaline(surface, p_["armor_mid"], elbow_f, hand_l, 6)
        B._aaline(surface, p_["armor_light"], elbow_f, hand_l, 3)
        B._aaline(surface, p_["armor_high"], elbow_f, hand_l, 1)
        # bracer
        bx = int(elbow_f[0] * 0.4 + hand_l[0] * 0.6)
        by = int(elbow_f[1] * 0.4 + hand_l[1] * 0.6)
        B._poly(surface, p_["armor_darkest"],
                [(bx - 3, by - 3), (bx + 3, by - 3), (bx + 3, by + 3),
                 (bx - 3, by + 3)])
        B._poly(surface, p_["armor_light"],
                [(bx - 2, by - 2), (bx + 1, by - 2), (bx + 1, by + 2),
                 (bx - 2, by + 2)])
        # tangan
        B._aacircle(surface, p_["armor_darkest"], hand_l, 4)
        B._aacircle(surface, p_["armor_mid"], hand_l, 3)
        B._aacircle(surface, p_["armor_high"],
                    (hand_l[0] - 1, hand_l[1] - 1), 2)

        # ══ 15. PEDANG (bilah energi chunky asimetris) ═══════════════
        B._draw_ab_sword(surface, hand_l, p["sword_angle"], p, f, phase)

        # ══ 16. PAULDRON DEPAN (di atas lengan) ══════════════════════
        poly(p_["armor_darkest"], [(12, -52), (22, -52), (23, -44),
                                   (12, -44)])
        poly(p_["armor_dark"], [(13, -51), (21, -51), (22, -46),
                                (13, -46)], outline=False)
        poly(p_["armor_mid"], [(14, -50), (20, -50), (21, -47),
                               (14, -47)], outline=False)
        # duri 3x naik
        for i in range(3):
            sx = 13 + i * 4
            poly(p_["armor_darkest"], [(sx, -52), (sx + 2, -59 - i),
                                       (sx + 4, -52)])
            B._aaline(surface, p_["armor_light"], L(sx + 1, -52),
                      L(sx + 2, -58 - i), 1)
        B._aaline(surface, p_["gold_dark"], L(12, -52), L(22, -52), 2)
        B._aaline(surface, p_["gold_mid"], L(13, -52), L(21, -52), 1)
        # permata pauldron
        B._aacircle(surface, p_["flame_darkest"], L(18, -47), 2)
        B._aacircle(surface, p_["flame_bright"], L(18, -47), 1)

        # ══ 17. RIM LIGHT + SPECULAR (1 px, posisi kunci) ════════════
        rim = 0.65 + 0.35 * math.sin(phase * 1.8)
        ra = int(150 * rim)
        B._aaline(surface, (*p_["flame_light"], ra), L(-11, -46),
                  L(-13, -22), 1)
        B._aaline(surface, (*p_["flame_light"], ra), L(-13, -54),
                  L(-6, -66), 1)
        B._aaline(surface, (*p_["flame_bright"], ra), L(12, -51),
                  L(21, -51), 1)
        # kilau pelat dada (spekular cluster 1-2 px)
        spec = [L(5, -41), L(8, -41), L(8, -40), L(5, -40)]
        B._poly(surface, (*p_["armor_high"], 200), spec)
        B._rect(surface, p_["white"], (spec[0][0], spec[0][1], 1, 1))

    # ==================================================================
    # BAGIAN TUBUH (fungsi terpisah untuk kejelasan)
    # ==================================================================
    def _draw_ab_legs(surface, L, p_, f, gallop, galloping, near):
        """Empat kaki tunggangan: paha -> lutut -> larut ke api.

        Kaki JAUH (near=False) lebih gelap & ber-offset -10% agar
        kedalaman terbaca; saat gallop kaki berselang-seling (scissor).
        """
        B = _NS_abaddon
        hips = ((30, 0.0, 1), (-30, math.pi, 1), (22, 0.55, 0),
                (-22, math.pi + 0.55, 0))
        for hip_x, off, is_near in hips:
            if is_near != (1 if near else 0):
                continue
            base = p_["horse_dark"] if near else p_["horse_darkest"]
            hi = p_["horse_mid"] if near else p_["horse_dark"]
            if galloping:
                s = math.sin(gallop + off)
                kx = int(s * 7)
                lift = int(max(0.0, math.sin(gallop + off + 1.1)) * 4)
            else:
                s = math.sin(gallop + off) * 0.6
                kx = int(s)
                lift = 0
            hip = L(hip_x, 12)
            knee = L(hip_x + kx * 0.55, 26 - lift)
            hoof_x = hip_x + kx
            hoof_y = 38 - lift
            # paha
            w = 6 if near else 5
            B._aaline(surface, p_["outline"], (hip[0] + f, hip[1] + 1),
                      (knee[0] + f, knee[1] + 1), w + 2)
            B._aaline(surface, base, hip, knee, w)
            B._aaline(surface, hi, hip, knee, max(1, w - 3))
            # betis larut ke api (3 blob memudar)
            for i in range(3):
                t = (i + 1) / 3.0
                fx = L(hoof_x, hoof_y - 8 + t * 10)[0]
                fy = L(hoof_x, hoof_y - 8 + t * 10)[1]
                s2 = max(1, int(4 - t * 2.4))
                B._draw_flame(surface, fx, fy, s2,
                              int(215 * (1 - t * 0.5)))

    def _draw_ab_cape(surface, L, p_, f, phase, p):
        """Jubah ungu mengalir ke belakang, tepi robek (tuft).

        Sway mengikuti fase + aksi (lag ringan terhadap badan).
        """
        action = p["action"]
        sway = int(math.sin(phase * 1.05) * 3)
        if action == "walk":
            sway -= 2 + int(math.sin(p["gallop"]) * 2)
        elif action == "attack":
            sway -= 2 + int(math.sin(p["ap"] * math.pi) * 3)
        elif action == "e":
            sway -= 4
        hem_spine = [(-18 + sway, -6), (-26 + sway, 4), (-30 + sway, 14),
                     (-26 + sway, 20), (-18 + sway, 14), (-12 + sway, 18)]
        tuft = _NS_abaddon._tuft_points(hem_spine, depth=2.4, min_len=4.0,
                                        seed=17)
        outer = [(-13, -46), (-22, -30), (-24 + sway, -8)] + \
            [(a - 4, b) for a, b in tuft] + [(-10, -10), (-11, -44)]
        pts = [L(a, b) for a, b in outer]
        _NS_abaddon._poly(surface, p_["cape_darkest"], pts)
        inner = [(-13, -44), (-19, -30), (-21 + sway, -6),
                 (-24 + sway, 6), (-20 + sway, 14), (-14 + sway, 12),
                 (-11, -6), (-12, -42)]
        _NS_abaddon._poly(surface, p_["cape_dark"],
                          [L(a, b) for a, b in inner])
        # lipatan (2 bidang nilai)
        fold1 = [(-16, -30), (-14, -28), (-17 + sway, -4),
                 (-20 + sway, -5)]
        _NS_abaddon._poly(surface, p_["cape_mid"],
                          [L(a, b) for a, b in fold1])
        fold2 = [(-14, -26), (-13, -24), (-15 + sway, 2),
                 (-18 + sway, 1)]
        _NS_abaddon._poly(surface, p_["cape_light"],
                          [L(a, b) for a, b in fold2])
        # rim di tepi robek
        hem = [(-22 + sway, 8), (-26 + sway, 16), (-24 + sway, 19),
               (-18 + sway, 15)]
        for i in range(len(hem) - 1):
            _NS_abaddon._aaline(surface, p_["cape_high"], L(*hem[i]),
                                L(*hem[i + 1]), 1)

    def _draw_ab_sword(surface, hand, angle, p, f, phase):
        """Bilah energi chunky ASIMETRIS dari tangan.

        Punggung gelap, badan mid, MATA bilah 1 px terang di sisi
        potong, fuller menyala saat menyerang/skill, guard emas +
        pommel dengan permata cyan. Saat R release: bilah menyala ungu.
        """
        B = _NS_abaddon
        p_ = B.PALETTE
        hot = p["hot"]
        L = B.SWORD_LEN
        s, c = math.sin(angle), math.cos(angle)
        nx, ny = c, -s          # normal = sisi potong
        # warna bilah: cyan normal, ungu saat R release
        if hot:
            cols = (p_["magic_darkest"], p_["magic_dark"], p_["magic_mid"],
                    p_["magic_light"], p_["magic_bright"])
        else:
            cols = (p_["blade_darkest"], p_["blade_dark"],
                    p_["blade_mid"], p_["blade_light"], p_["blade_shine"])
        c_dark, c_body, c_mid, c_light, c_edge = cols
        segs = 6
        curve = 4.5
        w0 = 4.2
        w1 = 0.9
        backline, spine, midline, edgeline = [], [], [], []
        for i in range(segs + 1):
            t = i / segs
            bend = curve * (t * t)
            cx = hand[0] + s * L * t + nx * bend
            cy = hand[1] + c * L * t + ny * bend
            w = w0 * (1.0 - t) + w1 * t
            backline.append((cx - nx * w * 0.55, cy - ny * w * 0.55))
            spine.append((cx, cy))
            midline.append((cx + nx * w * 0.28, cy + ny * w * 0.28))
            edgeline.append((cx + nx * w * 0.62, cy + ny * w * 0.62))

        def S(seq):
            return [(int(qx), int(qy)) for qx, qy in seq]

        s_back, s_spine, s_mid, s_edge = (S(backline), S(spine), S(midline),
                                          S(edgeline))
        full = s_edge + s_back[::-1]
        B._poly(surface, p_["outline"],
                [(qx + f, qy + 1) for qx, qy in full])
        B._poly(surface, c_dark, full)
        B._poly(surface, c_body, s_back + s_spine[::-1])
        B._poly(surface, c_mid, s_spine + s_mid[::-1])
        B._poly(surface, c_light, s_mid + s_edge[::-1])
        # mata bilah: 1 px paling terang di sisi potong
        for i in range(len(s_edge) - 1):
            B._aaline(surface, c_edge, s_edge[i], s_edge[i + 1], 1)
        # fuller menyala (selalu sedikit; terang saat swing/skill)
        active_glow = p["active"] or p["skill"] in ("q", "r")
        glow_a = int((170 if active_glow else 90) *
                     (0.8 + 0.2 * math.sin(phase * 2.2)))
        glow_col = p_["magic_light"] if hot else p_["flame_light"]
        for i in range(len(s_spine) - 1):
            B._aaline(surface, (*glow_col, glow_a), s_spine[i],
                      s_spine[i + 1], 1)
        # hamon dither di badan bilah
        dots = [s_mid[i] for i in range(1, len(s_mid))]
        B._dither_dots(surface, glow_col, dots, int(glow_a * 0.5))

        # guard emas (tegak lurus bilah di tangan)
        g1 = (int(hand[0] + nx * 6), int(hand[1] + ny * 6))
        g2 = (int(hand[0] - nx * 6), int(hand[1] - ny * 6))
        B._aaline(surface, p_["shadow_deep"], (g1[0] + f, g1[1] + 1),
                  (g2[0] + f, g2[1] + 1), 5)
        B._aaline(surface, p_["gold_dark"], g1, g2, 4)
        B._aaline(surface, p_["gold_mid"], g1, g2, 2)
        # gagang + pommel
        butt = (int(hand[0] - s * 7), int(hand[1] - c * 7))
        B._aaline(surface, p_["cape_darkest"], hand, butt, 5)
        B._aaline(surface, p_["gold_dark"], hand, butt, 2)
        B._aacircle(surface, p_["gold_dark"], butt, 3)
        B._aacircle(surface, p_["gold_light"], butt, 2)
        B._aacircle(surface, p_["flame_bright"], butt, 1)
        # ujung: glint + kilau (titik lahir semua FX)
        tip = s_spine[-1]
        B._aacircle(surface, (*p_["flame_hot"], glow_a), tip, 2)
        B._rect(surface, p_["flame_white"], (tip[0], tip[1] - 1, 2, 1))
        if active_glow:
            B._spark_star(surface, tip[0], tip[1], 6, glow_col,
                          int(glow_a * 0.8), spikes=6, rot=phase * 1.6,
                          core=p_["flame_white"])

    # ==================================================================
    # LAPISAN TANAH (di luar buffer: bayangan, aura, base api, rune)
    # ==================================================================
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan kontak REAKTIF + cache.

        Tekstur dibangun SEKALI; saat badan terangkat (lift > 0)
        mengecil, DASAR tetap menapak tanah (bawah tidak bergeser).
        """
        B = _NS_abaddon

        def _build():
            w, h = 130, 24
            sh = pygame.Surface((w, h), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 16)
                pygame.draw.ellipse(
                    sh, (0, 0, 0, alpha),
                    (w // 2 - 50 - radius, h // 2 - radius,
                     100 + radius * 2, radius * 2))
            pygame.draw.ellipse(sh, (5, 45, 55, 70),
                                (w // 2 - 40, h // 2 - 5, 80, 10))
            return sh

        sh = B._static(("ab_shadow",), _build)
        s = 1.0 - min(0.30, abs(lift) * 0.03)
        if s < 0.999:
            sh = pygame.transform.smoothscale(
                sh, (int(130 * s), int(24 * s)))
        w, h = sh.get_size()
        surface.blit(sh, (int(x) - w // 2, int(y) + 12 - h))

    def _draw_dark_aura(surface, x, y, phase, skill):
        """Aura gelap ungu/cyan latar - gradien cache, denyut set_alpha."""
        B = _NS_abaddon
        pulse = 1.0 if skill else math.sin(phase * 0.4) * 0.25 + 0.75

        def _build1():
            aura = pygame.Surface((220, 200), pygame.SRCALPHA)
            for radius in range(88, 5, -4):
                alpha = int((88 - radius) * 1.2)
                if alpha > 0:
                    B._aacircle(aura, (*B.PALETTE["cape_darkest"],
                                       min(255, alpha)), (110, 100),
                                radius)
            return aura

        def _build2():
            aura = pygame.Surface((160, 140), pygame.SRCALPHA)
            for radius in range(64, 5, -3):
                alpha = int((64 - radius) * 0.7)
                if alpha > 0:
                    B._aacircle(aura, (*B.PALETTE["flame_darkest"],
                                       min(255, alpha)), (80, 70), radius)
            return aura

        a1 = B._static(("ab_aura1",), _build1)
        a1.set_alpha(int(pulse * 235))
        surface.blit(a1, (int(x) - 110, int(y) - 100))
        a2 = B._static(("ab_aura2",), _build2)
        a2.set_alpha(int(pulse * 235))
        surface.blit(a2, (int(x) - 80, int(y) - 70))

    def _draw_flame_base(surface, x, y, phase, p):
        """Base api cyan di bawah tunggangan (pad cache + blob hidup)."""
        B = _NS_abaddon
        p_ = B.PALETTE
        intense = p["action"] in ("attack", "e", "r", "q", "walk")
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        gy = y + B.FLAME_Y

        def _build_pad():
            pad = pygame.Surface((170, 44), pygame.SRCALPHA)
            for radius in range(42, 3, -4):
                alpha = int((42 - radius) * 2.0)
                if alpha > 0:
                    pygame.draw.ellipse(
                        pad, (*p_["flame_darkest"], min(255, alpha)),
                        (85 - radius * 2, 22 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            return pad

        pad = B._static(("ab_mist_pad",), _build_pad)
        pad.set_alpha(int(200 * pulse * min(1.4, strength)))
        surface.blit(pad, (int(x) - 85, int(gy) - 14))
        # bara naik (6 titik)
        for i, off in enumerate((-40, -24, -8, 8, 24, 40)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = x + off + int(math.sin(phase + i) * 3)
            sy = gy + 6 - int(t * 26)
            alpha = max(0, min(255, int(225 * (1 - t) * strength)))
            if alpha > 12:
                B._draw_flame(surface, sx, sy, max(1, 4 - int(t * 3)),
                              alpha)
        # orb api mengorbit (5 titik)
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 30 + int(math.sin(phase + i * 1.3) * 4)
            sx = x + int(math.cos(angle) * r)
            sy = gy + int(math.sin(angle) * 7)
            B._draw_flame(surface, sx, sy, 3, 215)
        # jejak belakang saat bergerak
        if p["action"] == "walk":
            for i in range(5):
                sx = x - (i + 1) * 14 * p["facing"]
                sy = gy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                if alpha > 12:
                    B._draw_flame(surface, sx, sy, max(2, 4 - i), alpha)

    def _rune_plate(skill):
        """Plate rune tanah STATIS per skill (cache)."""
        p_ = _NS_abaddon.PALETTE

        def _build():
            s = pygame.Surface((160, 52), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*p_["cape_dark"], 140), (5, 12, 150, 30),
                                3)
            pygame.draw.ellipse(s, (*p_["flame_dark"], 170), (25, 16, 110, 22),
                                2)
            for i in range(10):
                angle = i * math.pi / 5
                x1 = 80 + int(math.cos(angle) * 38)
                y1 = 27 + int(math.sin(angle) * 8)
                x2 = 80 + int(math.cos(angle) * 68)
                y2 = 27 + int(math.sin(angle) * 12)
                pygame.draw.line(s, (*p_["flame_bright"], 150),
                                 (x1, y1), (x2, y2), 1)
            if skill:
                hot = p_["magic_bright"] if skill == "r" \
                    else p_["flame_hot"]
                pygame.draw.ellipse(s, (*hot, 90), (15, 10, 130, 34), 1)
            return s

        return _NS_abaddon._static(("ab_rune", skill), _build)

    def _draw_ground_runes(surface, x, y, phase, skill):
        """Sigil rune di bawah tunggangan (plate cache + sapuan live)."""
        B = _NS_abaddon
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        gy = y + B.FLAME_Y + 12
        plate = B._rune_plate(skill)
        plate.set_alpha(int(205 * pulse))
        surface.blit(plate, (int(x) - 80, int(gy) - 26))
        # sapuan cahaya: 3 tick terang berputar (murah)
        a = _NS_abaddon._alpha(170 * pulse)
        for i in range(3):
            angle = phase * 0.6 + i * math.pi * 2 / 3
            x1 = x + int(math.cos(angle) * 40)
            y1 = gy + int(math.sin(angle) * 8)
            x2 = x + int(math.cos(angle) * 70)
            y2 = gy + int(math.sin(angle) * 13)
            B._aaline(surface, (*B.PALETTE["flame_bright"], a),
                      (x1, y1), (x2, y2), 2)
            B._aaline(surface, (*B.PALETTE["flame_white"], a),
                      (x1, y1), (x2, y2), 1)

    # ==================================================================
    # SWING TRAIL - pita dari trail UJUNG BILAH yang sebenarnya
    # ==================================================================
    def _draw_swing_trail(surface, boss, x, y, p):
        """Fallback canvas: pita 3 lapis + leading edge + impact.

        Pita dibangun dari posisi ujung bilah pada beberapa waktu pose
        ke belakang, jadi busur SELALU menempel di senjata.
        """
        B = _NS_abaddon
        p_ = B.PALETTE
        ap = p["ap"]
        if p["action"] != "attack" or not p["trailing"]:
            return
        if ap < 0.36:
            fade = (ap - 0.30) / 0.06
        elif ap <= 0.62:
            fade = 1.0
        else:
            fade = max(0.0, 1.0 - (ap - 0.62) / 0.16)
        if fade <= 0.02:
            return
        steps = 12
        path = []
        for i in range(steps):
            ai = max(0.30, ap - 0.26 * (1.0 - i / (steps - 1)))
            path.append(B._pose(boss, x, y, ap_override=ai)["tip"])
        widths = [7.5 * ((i / (steps - 1)) ** 1.25) + 0.5
                  for i in range(steps)]
        B._ribbon(surface, path, [w * 1.5 for w in widths],
                  p_["flame_darkest"], int(190 * fade * 0.5))
        B._ribbon(surface, path, widths, p_["flame_mid"],
                  int(235 * fade * 0.9))
        B._ribbon(surface, path, [w * 0.4 for w in widths],
                  p_["flame_bright"], int(235 * fade))
        # leading edge 1 px (arah gerak terbaca)
        for i in range(steps - 3, steps - 1):
            B._aaline(surface, (*p_["flame_white"], int(245 * fade)),
                      path[i], path[i + 1], 1)
        # speed line di dalam busur
        for k in range(2):
            i0 = 2 + k * 3
            i1 = min(steps - 1, i0 + 4)
            B._aaline(surface, (*p_["flame_hot"], int(170 * fade)),
                      path[i0], path[i1], 1)
        # IMPACT: bintang + cincin chunky + serpihan
        if 0.50 <= ap <= 0.64:
            hold = max(0.0, 1.0 - abs(ap - 0.56) / 0.08)
            if hold > 0:
                tx, ty = path[-1]
                B._spark_star(surface, tx, ty, int(10 + 7 * hold),
                              p_["flame_hot"], int(235 * hold), spikes=8,
                              rot=ap * 4, core=p_["white"])
                B._dashed_ring(surface, tx, ty, int(10 + hold * 14),
                               p_["flame_light"], int(190 * hold),
                               ap * 3, segments=10, thick=2, squash=0.55)
                for i in range(5):
                    ang = -1.8 + i * 0.62 + math.sin(ap * 9 + i) * 0.15
                    d = 6 + hold * 12
                    B._shard(surface, tx + math.cos(ang) * d,
                             ty + math.sin(ang) * d, ang,
                             5 + int(hold * 4), 2, p_["flame_light"],
                             int(220 * hold), core=p_["flame_white"])

    def _draw_sever_trail(surface, boss, x, y, p):
        """Fallback canvas: pita ungu Death Sever saat release."""
        B = _NS_abaddon
        p_ = B.PALETTE
        sp = p["skill_p"]
        if p["action"] != "r" or not (0.55 <= sp < 0.80):
            return
        k = (sp - 0.55) / 0.25
        fade = 1.0 if k < 0.6 else max(0.0, 1.0 - (k - 0.6) / 0.4)
        if fade <= 0.02:
            return
        steps = 12
        path = []
        for i in range(steps):
            si = max(0.55, sp - 0.22 * (1.0 - i / (steps - 1)))
            path.append(B._pose(boss, x, y)["tip"] if si == sp else
                        _NS_abaddon._pose_at_skill(boss, x, y, si)["tip"])
        widths = [8.5 * ((i / (steps - 1)) ** 1.25) + 0.5
                  for i in range(steps)]
        B._ribbon(surface, path, [w * 1.5 for w in widths],
                  p_["magic_darkest"], int(200 * fade * 0.55))
        B._ribbon(surface, path, widths, p_["magic_mid"],
                  int(235 * fade * 0.9))
        B._ribbon(surface, path, [w * 0.4 for w in widths],
                  p_["magic_bright"], int(235 * fade))
        for i in range(steps - 3, steps - 1):
            B._aaline(surface, (*p_["flame_white"], int(245 * fade)),
                      path[i], path[i + 1], 1)
        if 0.68 <= sp <= 0.80:
            hold = max(0.0, 1.0 - abs(sp - 0.72) / 0.08)
            if hold > 0:
                tx, ty = path[-1]
                B._spark_star(surface, tx, ty, int(12 + 8 * hold),
                              p_["magic_bright"], int(240 * hold),
                              spikes=8, rot=sp * 5, core=p_["white"])

    def _pose_at_skill(boss, x, y, sp):
        """Pose dengan progress skill dipaksa (untuk trail R)."""
        # trik: set sementara active_skill_timer yang sesuai
        action = "r"
        dur = float(_NS_abaddon.SKILL_DUR["r"])
        timer = int(round((1.0 - sp) * dur))
        saved = getattr(boss, "active_skill_timer", 0)
        boss.active_skill_timer = timer
        try:
            return _NS_abaddon._pose(boss, x, y)
        finally:
            boss.active_skill_timer = saved

    # ==================================================================
    # PROJECTILE (canvas fallback) - lifecycle penuh, bentuk chunky
    # ==================================================================
    class MistCoilProjectile(object):
        """Q - orb mist yang mengejar target (fallback canvas)."""

        def __init__(self, sx, sy, tx, ty, speed=6.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            self.rot = 0.0

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.rot += 0.55
            dx = self.tx - self.x
            dy = self.ty - self.y
            d = math.hypot(dx, dy)
            if d < self.speed + 4:
                self.x, self.y = self.tx, self.ty
                self.alive = False
                return
            self.x += dx / d * self.speed
            self.y += dy / d * self.speed
            if self.age % 2 == 0:
                self.trail.append((int(self.x // 3) * 3,
                                   int(self.y // 3) * 3))
                if len(self.trail) > 8:
                    self.trail.pop(0)

        def draw(self, surface, phase):
            B = _NS_abaddon
            P = B.PALETTE
            if not self.alive and self.age > 6:
                return
            # after-image terkuantisasi (stamp persegi, bukan garis)
            n = len(self.trail)
            for i, (tx, ty) in enumerate(self.trail):
                a = B._alpha(110 * (i + 1) / max(1, n))
                if a <= 4:
                    continue
                s = 3 + (n - i)
                B._rect(surface, (*P["magic_dark"], a),
                        (tx - s // 2, ty - s // 2, s, s))
                B._aacircle(surface, (*P["magic_mid"], a), (tx, ty),
                            max(1, s // 3))
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            # ekor spike arah gerak
            ang = math.atan2(self.ty - self.y, self.tx - self.x)
            for off in (-4, 0, 4):
                nx, ny = -math.sin(ang), math.cos(ang)
                B._aaline(surface, (*P["magic_light"], 160),
                          (px - math.cos(ang) * 14 + nx * off,
                           py - math.sin(ang) * 14 + ny * off),
                          (px - math.cos(ang) * 30 + nx * off,
                           py - math.sin(ang) * 30 + ny * off), 2)
            # inti berlapis
            B._aacircle(surface, (*P["magic_darkest"], 185), (px, py), 10)
            B._aacircle(surface, (*P["magic_dark"], 220), (px, py), 8)
            B._aacircle(surface, (*P["magic_mid"], 240), (px, py), 6)
            B._aacircle(surface, (*P["flame_mid"], 240), (px, py), 4)
            B._aacircle(surface, (*P["flame_bright"], 250), (px, py), 3)
            B._aacircle(surface, P["flame_hot"], (px, py), 2)
            B._rect(surface, P["flame_white"], (px - 1, py - 1, 2, 2))
            # puing mengorbit spiral
            for k in range(2):
                oa = self.rot * 1.4 + k * math.pi
                ox = px + math.cos(oa) * 9
                oy = py + math.sin(oa) * 7
                B._aacircle(surface, (*P["magic_light"], 200), (ox, oy), 2)
                B._aacircle(surface, P["flame_hot"], (ox, oy), 1)

    class DarknessGaleProjectile(object):
        """E - dinding angin gelap menjalar ke depan (fallback canvas)."""

        def __init__(self, sx, sy, direction, max_dist=250):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = int(direction) or 1
            self.max_dist = max_dist
            self.speed = 11.0
            self.alive = True
            self.age = 0
            self.max_age = 24
            self.rot = 0.0

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.rot += 0.4
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive and self.age > 3:
                return
            B = _NS_abaddon
            P = B.PALETTE
            t = self.age / self.max_age
            fade = 1.0 - t * 0.5
            px, py = int(self.x), int(self.y)
            d = self.direction
            # 9 balok vertikal membentuk busur (chunky, bukan lingkaran)
            for i in range(9):
                tt = i / 8.0
                yy = py - 17 + tt * 34
                bow = (1.0 - abs(tt - 0.5) * 2) ** 1.6
                xx = px - d * int(6 + bow * 12)
                a = B._alpha(235 * fade * (0.45 + 0.55 * bow))
                w = int(3 + bow * 3)
                B._rect(surface, (*P["magic_darkest"], B._alpha(a * 0.85)),
                        (xx - w // 2, yy - 3, w, 7))
                B._rect(surface, (*P["magic_mid"], a),
                        (xx - w // 2 + 1, yy - 2, max(1, w - 2), 5))
                if bow > 0.55:
                    B._rect(surface, (*P["flame_light"], B._alpha(a * 0.9)),
                            (xx - w // 2 + 1, yy - 1, max(1, w - 2), 2))
            # leading edge
            for i in range(7):
                tt = i / 6.0
                yy = py - 14 + tt * 28
                bow = (1.0 - abs(tt - 0.5) * 2) ** 1.6
                xx = px + d * int(2 + bow * 2)
                B._rect(surface, (*P["flame_bright"],
                                  B._alpha(235 * fade * bow)),
                        (xx - 1, yy - 1, 3, 3))
            # streak ke belakang
            for off in (-8, 0, 8):
                B._aaline(surface, (*P["magic_dark"], B._alpha(190 * fade)),
                          (px - d * 18, py + off), (px - d * 44, py + off + 2),
                          3)
                B._aaline(surface, (*P["magic_light"],
                                    B._alpha(140 * fade)),
                          (px - d * 16, py + off),
                          (px - d * 38, py + off + 2), 1)
            # ujung menyala
            B._spark_star(surface, px + d * 5, py, int(7 * fade + 3),
                          P["flame_light"], B._alpha(220 * fade), spikes=4,
                          rot=self.rot, core=P["flame_white"])

    class DeathSeverWave(object):
        """R - busur bulan sabit ungu raksasa (fallback canvas)."""

        def __init__(self, sx, sy, direction, max_dist=200):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = int(direction) or 1
            self.max_dist = max_dist
            self.speed = 9.0
            self.alive = True
            self.age = 0
            self.max_age = 22
            self.rot = 0.0

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.rot += 0.3
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            B = _NS_abaddon
            P = B.PALETTE
            t = self.age / self.max_age
            fade = 1.0 - t * 0.4
            px, py = int(self.x), int(self.y)
            d = self.direction
            R = 24
            a0 = self.rot * 0.5
            # pita 4 lapis (gelap -> terang -> inti panas)
            for w, col, am in ((15, P["magic_darkest"], 0.75),
                               (10, P["magic_mid"], 0.95),
                               (5, P["magic_bright"], 1.0),
                               (2, P["flame_hot"], 1.0)):
                prev = None
                for i in range(13):
                    tt = i / 12.0
                    ang = a0 + (tt - 0.5) * 1.9
                    ex = px + math.cos(ang) * R * 0.4 * d
                    ey = py + math.sin(ang) * R
                    q = (int(ex), int(ey))
                    if prev is not None:
                        B._aaline(surface, (*col, B._alpha(235 * fade * am)),
                                  prev, q, w)
                    prev = q
            # serpihan berputar di belakang busur
            for i in range(6):
                sa = a0 + 1.15 + B._hash01(i * 5) * 0.5
                sr = R * (0.6 + 0.5 * B._hash01(i * 9))
                sx = px + math.cos(sa) * sr * 0.4 * d
                sy = py + math.sin(sa) * sr
                B._shard(surface, sx, sy, sa + math.pi / 2, 6, 2,
                         P["magic_light"], B._alpha(210 * fade))
            # inti putih di pucuk
            for tt in (0.0, 1.0):
                ang = a0 + (tt - 0.5) * 1.9
                tx = px + math.cos(ang) * R * 0.4 * d
                ty = py + math.sin(ang) * R
                B._aacircle(surface, (*P["flame_white"],
                                      B._alpha(255 * fade)), (tx, ty), 2)

    # ------------------------------------------------------------------
    # spawn + manajemen proyektil (nama list lama: _ab_projectiles)
    # ------------------------------------------------------------------
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        for pr in boss._ab_projectiles:
            pr.update()
            pr.draw(surface, phase)
        boss._ab_projectiles = [pr for pr in boss._ab_projectiles
                                if pr.alive or pr.age < 8]

    def _spawn_mist_coil(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        tx, ty = _NS_abaddon._target_position(boss, x, y)
        sx = x + 26 * boss.direction
        sy = y - 10
        boss._ab_projectiles.append(
            _NS_abaddon.MistCoilProjectile(sx, sy, tx, ty, speed=6.5))

    def _spawn_darkness_gale(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(
            _NS_abaddon.DarknessGaleProjectile(sx, sy, boss.direction))

    def _spawn_death_sever(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(
            _NS_abaddon.DeathSeverWave(sx, sy, boss.direction))

    # ==================================================================
    # SKILL FX - canvas fallback (lapisan hidup menggambar versi 1:1)
    # ==================================================================
    def _draw_skill_canvas(surface, boss, x, y, p, phase):
        """Semua FX skill di-canvas; dipanggil hanya saat tidak owned."""
        B = _NS_abaddon
        action = p["action"]
        sp = p["skill_p"]
        fs = B._fx_scale(boss)
        tx, ty = B._target_position(boss, x, y)
        p_ = B.PALETTE
        if action == "q":
            # telegraph: cincin kabut menutup di target
            if sp < 0.42:
                t = sp / 0.42
                r = int((26 - t * 18) * (0.6 + 0.4 * t) * fs)
                a = B._alpha(185 * (0.5 + 0.5 * t))
                B._dashed_ring(surface, tx, ty, max(2, r), p_["magic_mid"],
                               a, phase * 2.2, segments=10, thick=3,
                               squash=0.5)
                for i in range(6):
                    ang = phase * 2.4 + i * math.pi / 3
                    rr = max(2, r * (1.25 - t * 0.9))
                    B._aacircle(surface, (*p_["magic_light"], a),
                                (tx + math.cos(ang) * rr,
                                 ty + math.sin(ang) * rr * 0.5), 2)
            elif sp < 0.62:
                t = (sp - 0.42) / 0.20
                k = 1.0 - t
                B._spark_star(surface, tx, ty, int(20 * k + 6) ,
                              p_["flame_bright"], B._alpha(240 * k),
                              spikes=8, rot=phase * 3, core=p_["white"])
            elif sp < 1.0:
                # kabut menguap dari titik mendarat (after-effect)
                t = (sp - 0.62) / 0.38
                a = B._alpha(140 * (1 - t))
                for i in range(6):
                    ang = i * math.pi / 3 + phase * 0.5
                    rr = 8 + t * 22 + B._hash01(i * 3) * 8
                    B._rect(surface, (*p_["magic_dark"], B._alpha(a * 0.8)),
                            (tx + math.cos(ang) * rr - 3,
                             ty + math.sin(ang) * rr * 0.5 - 2, 6, 4))
                    B._rect(surface, (*p_["magic_mid"], B._alpha(a * 0.6)),
                            (tx + math.cos(ang) * rr - 2,
                             ty + math.sin(ang) * rr * 0.5 - 1, 4, 3))
                if sp >= 0.95:
                    # residu: cincin kecil memudar di titik mendarat
                    rt = (sp - 0.95) / 0.05
                    ar = B._alpha(110 * (1 - rt))
                    B._dashed_ring(surface, tx, ty, max(2, int(6 * fs)),
                                   p_["magic_mid"], ar, phase * 3.0,
                                   segments=6, thick=2, squash=0.5)
            # charge glow di ujung bilah
            if 0.10 < sp < 0.50:
                tipx, tipy = p["tip"]
                glow = math.sin(phase * 4) * 0.3 + 0.7
                B._aacircle(surface, (*p_["magic_dark"], 170), (tipx, tipy),
                            int(12 * glow * fs))
                B._aacircle(surface, (*p_["magic_mid"], 215), (tipx, tipy),
                            int(8 * glow * fs))
                B._aacircle(surface, (*p_["flame_bright"], 235),
                            (tipx, tipy), int(5 * glow * fs))
                B._aacircle(surface, p_["flame_hot"], (tipx, tipy),
                            max(1, int(3 * glow * fs)))
        elif action == "e":
            # dash: gust horizontal + chevron konvergen
            a = B._alpha(215 * min(1.0, sp * 4))
            for i in range(5):
                t = (sp * 1.4 + i * 0.17) % 1.0
                xx = x - p["facing"] * (10 + t * 46 * fs)
                yy = y - 26 + i * 13
                aa = B._alpha(210 * (1 - t))
                B._aaline(surface, (*p_["magic_dark"], B._alpha(aa * 0.8)),
                          (xx, yy),
                          (xx - p["facing"] * 14, yy + 2), 4)
                B._aaline(surface, (*p_["flame_light"], B._alpha(aa * 0.9)),
                          (xx, yy), (xx - p["facing"] * 10, yy + 2), 1)
            if sp < 0.6:
                pull = (phase * 1.1) % 1.0
                for i in range(4):
                    cxp = x - p["facing"] * (18 + pull * 26 + i * 8)
                    cyp = y - 20 + i * 14
                    for s in (-1, 1):
                        B._aaline(surface, (*p_["magic_light"],
                                            B._alpha(180 * (1 - sp))),
                                  (cxp - p["facing"] * 5, cyp + s * 5),
                                  (cxp + p["facing"] * 6, cyp), 2)
            # jejak gust di tanah
            gy = y + 52
            for i in range(6):
                t = (phase * 0.8 + i * 0.16) % 1.0
                xx = x - p["facing"] * (10 + t * 50 * fs)
                aa = B._alpha(150 * (1 - t) * sp)
                B._aaline(surface, (*p_["ash_mid"], aa), (xx, gy),
                          (xx - p["facing"] * 10, gy + 1), 2)
        elif action == "r":
            if sp < 0.55:
                # TELEGRAPH: cincin dash mengecil + crosshair + chevron
                t = sp / 0.55
                r = int((58 - t * 26) * fs)
                a = B._alpha(215 * min(1.0, t * 3))
                B._dashed_ring(surface, tx, ty, max(2, r), p_["magic_mid"],
                               a, -phase * 2.6, segments=10, thick=4,
                               squash=0.5)
                B._dashed_ring(surface, tx, ty, max(2, int(r * 0.66)),
                               p_["magic_bright"], B._alpha(a * 0.8),
                               phase * 3.2, segments=6, thick=2,
                               squash=0.5)
                blink = 0.55 + 0.45 * math.sin(phase * 7)
                for (sx2, sy2) in ((1, 1), (1, -1)):
                    for st in range(5):
                        dd = (st + 2) * 8
                        B._rect(surface, (*p_["magic_light"],
                                          B._alpha(a * blink)),
                                (tx + sx2 * dd, ty + sy2 * dd * 0.5 - 2,
                                 5, 4))
                        B._rect(surface, (*p_["magic_light"],
                                          B._alpha(a * blink)),
                                (tx - sx2 * dd, ty - sy2 * dd * 0.5 - 2,
                                 5, 4))
                B._rect(surface, (*p_["magic_hot"], B._alpha(a * blink)),
                        (tx - 3, ty - 3, 6, 5))
                for i in range(6):
                    ang = i * math.pi / 3 + phase * 0.8
                    cr = max(4, r * (1.18 - t * 0.25))
                    cxp = tx + math.cos(ang) * cr
                    cyp = ty + math.sin(ang) * cr * 0.5
                    for s in (-1, 1):
                        B._aaline(surface, (*p_["magic_bright"],
                                            B._alpha(a * 0.9)),
                                  (cxp - math.cos(ang) * 5,
                                   cyp - math.sin(ang) * 2 + s * 5),
                                  (cxp + math.cos(ang) * 7,
                                   cyp + math.sin(ang) * 3.5), 2)
            else:
                # LEDAKAN: flash + gelombang ungu + retakan + abu
                t = (sp - 0.55) / 0.45
                k = 1.0 - t
                if t < 0.4:
                    B._spark_star(surface, tx, ty,
                                  int((30 + t * 60) * (1 - t / 0.4 * 0.5)),
                                  p_["magic_bright"],
                                  B._alpha(250 * (1 - t / 0.4)),
                                  spikes=10, rot=phase * 4,
                                  core=p_["white"])
                r = int((14 + t * 74) * fs)
                B._dashed_ring(surface, tx, ty, max(2, r), p_["magic_dark"],
                               B._alpha(225 * k), t * 4.0, segments=14,
                               thick=5, squash=0.48)
                B._dashed_ring(surface, tx, ty, max(2, int(r * 0.7)),
                               p_["magic_bright"], B._alpha(185 * k),
                               -t * 5.2, segments=10, thick=3,
                               squash=0.48)
                # retakan bergerigi
                for i in range(6):
                    a2 = i * math.pi / 3 + 0.3
                    x0, y0 = tx, ty
                    for j in range(3):
                        a2 += (B._hash01(i * 7 + j) - 0.5) * 0.7
                        ln = 20 * (j + 1) / 3 * (0.5 + t * 0.7)
                        x1 = x0 + math.cos(a2) * ln
                        y1 = y0 + math.sin(a2) * ln * 0.5
                        B._aaline(surface, (*p_["magic_darkest"],
                                           B._alpha(200 * k)),
                                  (x0, y0), (x1, y1), 3)
                        B._aaline(surface, (*p_["magic_mid"],
                                           B._alpha(150 * k)),
                                  (x0, y0), (x1, y1), 1)
                        x0, y0 = x1, y1
                # abu ungu melayang
                for i in range(8):
                    f2 = (phase * 0.35 + i * 0.125) % 1.0
                    ax = tx + math.sin(phase + i * 2.0) * 30
                    ay = ty - f2 * 44
                    B._rect(surface, (*p_["magic_mid"],
                                      B._alpha(190 * k * (1 - f2))),
                            (ax - 2, ay - 2, 4, 4))
        elif action == "w":
            B._draw_ab_w_shield(surface, boss, x, y, sp, phase, fs)

    def _draw_ab_w_shield(surface, boss, x, y, sp, phase, fs):
        """W APHOTIC SHIELD - perisai PELAT HEKSAAGON (bukan lingkaran).

        Cahaya TERTARIK masuk ke inti gelap (afotik = penyerap cahaya);
        6 pelat berputar, simpul sudut, rune heksagon di tanah.
        """
        B = _NS_abaddon
        p_ = B.PALETTE
        scale = min(1.0, sp / 0.15) if sp < 0.15 else 1.0
        fade_out = 1.0 if sp < 0.85 else max(0.0, (1.0 - sp) / 0.15)
        if fade_out <= 0.02:
            return
        cx, cy = int(x), int(y - 14)
        R = int(36 * scale * fs)
        if R < 3:
            return
        pulse = 0.82 + 0.18 * math.sin(phase * 2.0)
        base_a = B._alpha(235 * pulse * fade_out)
        spin = phase * 0.35
        # 6 pelat heksagon (setiap sisi = satu pelat chunky berlapis)
        for i in range(6):
            a0 = spin + i * math.pi / 3
            a1 = a0 + math.pi / 3 * 0.82
            p0 = (cx + math.cos(a0) * R, cy + math.sin(a0) * R)
            p1 = (cx + math.cos(a1) * R, cy + math.sin(a1) * R)
            B._aaline(surface, (*p_["flame_dark"],
                                B._alpha(base_a * 0.7)), p0, p1, 7)
            B._aaline(surface, (*p_["flame_mid"],
                                B._alpha(base_a * 0.9)), p0, p1, 4)
            B._aaline(surface, (*p_["flame_bright"], base_a), p0, p1, 2)
            B._aacircle(surface, (*p_["flame_hot"], base_a), p0, 3)
            B._rect(surface, (*p_["flame_white"], base_a),
                    (int(p0[0]) - 1, int(p0[1]) - 1, 2, 2))
        # inti gelap (penyerap cahaya)
        B._aacircle(surface, (*p_["shadow_deep"],
                             B._alpha(190 * fade_out)), (cx, cy),
                    int(R * 0.55))
        B._dashed_ring(surface, cx, cy, max(2, int(R * 0.62)),
                       p_["flame_mid"], B._alpha(140 * pulse * fade_out),
                       -spin * 1.6, segments=8, thick=2, squash=1.0)
        # cahaya tertariK masuk (ditaran ke dalam)
        for i in range(6):
            ang = -phase * 0.9 + i * math.pi / 3
            rr = R * (1.35 - ((phase * 0.25 + i * 0.166) % 1.0) * 0.35)
            a = B._alpha(200 * fade_out)
            ox = cx + math.cos(ang) * rr
            oy = cy + math.sin(ang) * rr
            B._aacircle(surface, (*p_["flame_light"], a), (ox, oy), 2)
            B._rect(surface, (*p_["flame_white"], B._alpha(a * 0.8)),
                    (int(ox) - 1, int(oy) - 1, 2, 2))
        # rune heksagon di tanah
        if sp < 0.9:
            gy = y + 48
            for i in range(6):
                a0 = -spin + i * math.pi / 3
                a1 = a0 + math.pi / 3 * 0.7
                B._aaline(surface, (*p_["flame_dark"],
                                    B._alpha(130 * fade_out)),
                          (x + math.cos(a0) * 40 * fs,
                           gy + math.sin(a0) * 16 * fs),
                          (x + math.cos(a1) * 40 * fs,
                           gy + math.sin(a1) * 16 * fs), 3)
        # flash aktivasi (10 frame pertama)
        if sp < 0.10:
            t = sp / 0.10
            B._spark_star(surface, x, y - 14, int(16 * (1 - t) * fs),
                          p_["flame_hot"], B._alpha(230 * (1 - t)),
                          spikes=8, rot=t * 3, core=p_["flame_white"])

    # ==================================================================
    # DEATH - hantu yang menguap
    # ==================================================================
    def _draw_death(surface, boss, x, y, p, owned, mod):
        B = _NS_abaddon
        t = int(getattr(boss, "_ab_death_t", 0))
        boss._ab_death_t = t + 1
        k = min(1.0, t / 40.0)
        if k >= 1.0:
            # bara terakhir yang padam
            if t % 4 == 0:
                B._draw_flame(surface, x + (B._hash01(t) - 0.5) * 30,
                              y + 20, 2, 120)
            return
        fade = int(255 * (1 - k))
        buf = pygame.Surface((B.RIG_W, B.RIG_H), pygame.SRCALPHA)
        B._draw_rig(buf, B.RIG_OX, B.RIG_OY, p)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        edge.set_alpha(int(fade * 0.7))
        buf.set_alpha(fade)
        ox = int(x) - B.RIG_OX
        oy = int(y) - B.RIG_OY - int(k * 14)
        surface.blit(edge, (ox, oy))
        surface.blit(buf, (ox, oy))
        # bara tersebar
        for i in range(6):
            tt = (p["phase"] * 0.4 + i * 0.17) % 1.0
            B._draw_flame(surface,
                          x + math.sin(p["phase"] + i * 1.9) * (10 + tt * 30),
                          y + 30 - tt * 50 - int(k * 14),
                          max(1, int(4 - tt * 3)),
                          int(200 * (1 - tt) * (1 - k)))

    # ==================================================================
    # DEBUG OVERLAY (DEBUG_CHARACTER = True)
    # ==================================================================
    def _draw_debug(surface, boss, x, y, p, owned):
        """Hitbox, hurtbox, jangkauan, state/frame, FPS, jumlah partikel.

        Tidak menyentuh gameplay: semua angka dibaca dari state yang
        sudah ada; overlay digambar PALING AKHIR.
        """
        B = _NS_abaddon
        import pygame as _pg
        # hurtbox = lingkaran radius unit
        r = max(8, int(getattr(boss, "radius", 42) * 0.9))
        _pg.draw.rect(surface, (80, 170, 255, 150),
                      _pg.Rect(int(x) - r, int(y) - r, r * 2, r * 2), 1)
        # jangkauan serangan
        rng = max(10, int(getattr(boss, "range", 50)))
        f = p["facing"]
        _pg.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                      (int(x) + rng * f, int(y)), 1)
        _pg.draw.rect(surface, (255, 210, 60, 110),
                      _pg.Rect(int(x) + rng * f - 5, int(y) - 7, 10, 14), 1)
        # hitbox ayunan (hanya saat jendela hit aktif)
        hb = B._swing_hitbox(boss, x, y)
        if hb is not None:
            _pg.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            _pg.draw.rect(surface, (255, 70, 70, 60), hb)
        # tabrakan proyektil milik lapisan hidup
        mod = B._live_module()
        if owned and mod is not None:
            try:
                for pr in mod.projectiles_for(boss):
                    _pg.draw.circle(surface, (255, 120, 255, 170),
                                    (int(pr.x), int(pr.y)),
                                    max(3, int(getattr(pr, "radius", 8))), 1)
            except Exception:
                pass
        # fps (exponential moving average)
        fps = getattr(boss, "_ab_fps", None)
        if fps is None:
            boss._ab_fps = 60.0
            fps = 60.0
        else:
            dt = float(getattr(boss, "_ab_dt", 1.0 / 60.0))
            inst = 1.0 / dt if dt > 0 else 60.0
            boss._ab_fps = fps + (inst - fps) * 0.1
            fps = boss._ab_fps
        state = getattr(boss, "_ab_state", "IDLE")
        phase_name = getattr(boss, "_ab_attack_phase", "NONE")
        frames = int(getattr(boss, "_ab_attack_frame", 0))
        prog = float(getattr(boss, "_ab_attack_progress", 0.0))
        atk_cd = int(getattr(boss, "attack_cooldown", 43))
        timer = int(getattr(boss, "timer", 0))
        skill = getattr(boss, "active_skill", None) or "-"
        s_timer = int(getattr(boss, "active_skill_timer", 0))
        npart = nproj = 0
        try:
            if mod is not None:
                npart = int(mod.total_particles())
                nproj = len(mod.projectiles_for(boss))
        except Exception:
            pass
        lines = (
            "ABADDON  %.0f fps" % fps,
            "state %s (prev %s) %.2fs" % (state,
                                          getattr(boss, "_ab_state_prev",
                                                  "-"),
                                          float(getattr(
                                              boss, "_ab_state_time", 0.0))),
            "action %s  phase %s" % (p["action"], phase_name),
            "atk frame %d/%d  prog %.2f  hit %s" % (
                frames, max(1, atk_cd - 1), prog,
                "ON" if getattr(boss, "_ab_hit_active", False) else "off"),
            "timer %d  hurt %d" % (timer,
                                   int(getattr(boss, "_ab_hurt_frames", 0))),
            "skill %s  %d  live %s" % (skill, s_timer,
                                       "on" if owned else "canvas"),
            "particles %d  projectiles %d  dt %.1fms" % (
                npart, nproj,
                float(getattr(boss, "_ab_dt", 1.0 / 60.0)) * 1000.0),
        )
        try:
            fnt = _pg.font.SysFont("consolas,monospace", 10)
        except Exception:                          # pragma: no cover
            fnt = _pg.font.Font(None, 12)
        w0 = int(x) - 100
        y0 = int(y) - 150 - 12 * len(lines)
        box = _pg.Rect(w0 - 3, y0 - 2, 205, 12 * len(lines) + 4)
        bg = _pg.Surface(box.size, _pg.SRCALPHA)
        bg.fill((6, 4, 12, 150))
        surface.blit(bg, box.topleft)
        for i, t in enumerate(lines):
            txt = fnt.render(t, True, (180, 240, 245))
            surface.blit(txt, (box.x + 3, box.y + 1 + i * 12))

    # ==================================================================
    # ENTRY POINT
    # ==================================================================
    def draw_abaddon(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan mengikuti kontrak render order proyek:

            GROUND FX -> SHADOW -> BODY/ARMOR/HEAD -> WEAPON ->
            ATTACK TRAIL -> PROJECTILE -> SKILL FX -> IMPACT FX -> DEBUG

        Trail tebasan, proyektil, partikel, impact, hit-stop, dan screen
        shake hidup di ``heroes/abaddon_fx.py`` (lapisan layar 1:1, di
        luar sprite cache). Kalau modul FX tidak tersedia, renderer
        kembali menggambar semuanya di-canvas (jalur fallback).
        """
        NS = _NS_abaddon
        x = int(x)
        y = int(y)
        pulse = float(getattr(boss, "pulse", 0.0))
        NS._update_attack_anim(boss)
        NS._detect_moving(boss)
        active_skill = getattr(boss, "active_skill", None)
        p = NS._pose(boss, x, y)

        # ── lapisan hidup (pasang / tick ground) ──────────────────────
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        mod = None if portrait else NS._live_module()
        owned = False
        if mod is not None:
            try:
                if hero_lane:
                    mod.attach(boss)
                else:
                    mod.draw_ground_layer(surface, boss, x, y)
                owned = bool(mod.owns(boss))
            except Exception:
                mod = None
                owned = False

        if not getattr(boss, "alive", True):
            NS._draw_death(surface, boss, x, y, p, owned, mod)
            return

        f = p["facing"]
        # ── Lapisan tanah ─────────────────────────────────────────────
        NS._draw_dark_aura(surface, x, y, pulse, active_skill)
        NS._draw_flame_base(surface, x, y, pulse, p)
        if active_skill != "r":
            NS._draw_ground_runes(surface, x, y, pulse, active_skill)
        lift = 0
        if p["action"] == "e":
            lift = int(math.sin(p["skill_p"] * math.pi) * 4)
        NS._draw_shadow(surface, x + p["lunge"] * f, y + NS.SHADOW_Y, lift)

        # ── Karakter (buffer rig + hurt flash + outline) ──────────────
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        NS._draw_rig_at(surface, x, y, p, flash)

        # ── Trail tebasan (canvas fallback) ───────────────────────────
        if p["trailing"] and not owned:
            if p["active"]:
                NS._draw_swing_trail(surface, boss, x, y, p)
            else:
                NS._draw_sever_trail(surface, boss, x, y, p)

        # ── Skill FX (canvas) + spawn proyektil ───────────────────────
        # Telegraph / charge / release / after-effect digambar di-canvas
        # di KEDUA lane (paritas Gornak v3: FX skill bagian dari pose,
        # ikut cache lane dengan kompensasi _fx_scale). Lapisan hidup
        # hanya menambah yang harus 60 fps: proyektil, partikel,
        # impact, trail, hit-stop + shake (dijadwalkan via on_cast).
        if active_skill:
            sp = p["skill_p"]
            if not owned:
                if active_skill == "q" and 0.30 < sp < 0.40 and \
                        not getattr(boss, "_ab_coil_spawned", False):
                    NS._spawn_mist_coil(boss, x, y)
                    boss._ab_coil_spawned = True
                if active_skill != "q" or sp < 0.2 or sp > 0.9:
                    boss._ab_coil_spawned = False
                if active_skill == "e" and 0.30 < sp < 0.40 and \
                        not getattr(boss, "_ab_gale_spawned", False):
                    NS._spawn_darkness_gale(boss, x, y)
                    boss._ab_gale_spawned = True
                if active_skill != "e" or sp < 0.2 or sp > 0.9:
                    boss._ab_gale_spawned = False
                if active_skill == "r" and 0.55 < sp < 0.68 and \
                        not getattr(boss, "_ab_sever_spawned", False):
                    NS._spawn_death_sever(boss, x, y)
                    boss._ab_sever_spawned = True
                if active_skill != "r" or sp < 0.4 or sp > 0.9:
                    boss._ab_sever_spawned = False
            NS._draw_skill_canvas(surface, boss, x, y, p, pulse)

        # ── Proyektil (canvas fallback; hero lane di-park) ────────────
        if not owned:
            NS._manage_projectiles(boss, surface, pulse)

        # ── Lapisan hidup bagian ATAS (jalur boss) ────────────────────
        if mod is not None and not hero_lane:
            try:
                mod.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── Overlay debug ─────────────────────────────────────────────
        if NS.DEBUG_CHARACTER:
            NS._draw_debug(surface, boss, x, y, p, owned)

    # ==================================================================
    # Aliases kompatibilitas lama
    # ==================================================================
    def draw_boss(surface, boss, x, y):
        _NS_abaddon.draw_abaddon(surface, boss, x, y)

# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_gornak(surface, boss, x, y):
    """Entry point gornak."""
    return _NS_gornak.draw_gornak(surface, boss, x, y)

def draw_morgath(surface, boss, x, y):
    """Entry point morgath."""
    return _NS_morgath.draw_morgath(surface, boss, x, y)

def draw_drakar(surface, boss, x, y):
    """Entry point drakar."""
    return _NS_drakar.draw_drakar(surface, boss, x, y)

def draw_abaddon(surface, boss, x, y):
    """Entry point abaddon."""
    return _NS_abaddon.draw_abaddon(surface, boss, x, y)
