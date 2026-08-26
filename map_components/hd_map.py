"""
map_components/hd_map.py - HD MAP RENDERING (gaya sprite HD Thorne)
══════════════════════════════════════════════════════════════════

Peta kini dirender dengan pendekatan yang sama seperti upgrade
hero Thorne (code-based -> sprite HD, lihat docs/thorne_before_
after.png): render resolusi tinggi dengan tepi HALUS (feathered),
shading gradient kaya, lalu di-smoothscale ke ukuran tampil.

Teknik:
  1. TERRAIN HD  — permukaan "dilukis" per-piksel: value noise 2
     oktaf + blend diagonal radiant/dire yang HALUS (bukan garis
     keras 16px) + stroke detail rumput/abu. Dibangun di
     160x90 (murah) -> 320x180 -> smoothscale ke 1280x720.
  2. OBJEK 2x    — sungai, lane, dekorasi, toko, & dinding
     dirender di canvas 2560x1440 memakai KODE ART ASLI
     (koordinat + ukuran surface di-skalakan 2x lewat patch
     pygame.draw/Surface sementara), lalu smoothscale ke
     1280x720 -> SEMUA tepi anti-aliased (efek feather seperti
     sprite HD Thorne), bevel & retakan glow jadi halus kaya.
  3. LIGHTMAP    — shading skala besar (gradien diagonal +
     mottling) dari pipeline sprite (sprite_tiles.apply_light).

Semua layer DETERMINISTIK per tema (lane/dekorasi di-generate
dengan seed tetap), jadi hasil di-cache: tema pertama per sesi
±0,25 s, tema sama berikutnya hanya ±5 ms (blit cache).

Fallback berjenjang: HD gagal -> pipeline sprite 1x -> pipeline
lama. Matikan HD: MYSTIC_MAP_HD=0 (sprite 1x).
"""
import math
import random

import pygame

from map_components.palettes import TILE_SIZE  # noqa: F401 (referensi)


# ═══════════════════════════════════════════════
# VALUE NOISE (untuk terrain dilukis)
# ═══════════════════════════════════════════════

def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class _ValueNoise:
    """Value noise 2D deterministik (grid kecil, interp smooth)."""

    def __init__(self, seed, gw, gh):
        rng = random.Random(seed)
        self.g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
        self.gw, self.gh = gw, gh

    def at(self, x, y):
        gx = x * (self.gw - 1)
        gy = y * (self.gh - 1)
        x0 = int(gx)
        y0 = int(gy)
        x1 = min(x0 + 1, self.gw - 1)
        y1 = min(y0 + 1, self.gh - 1)
        fx = _smoothstep(gx - x0)
        fy = _smoothstep(gy - y0)
        a = self.g[y0][x0]
        b = self.g[y0][x1]
        c = self.g[y1][x0]
        d = self.g[y1][x1]
        return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def _mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def _shade(c, f):
    return tuple(int(max(0, min(255, ch * f))) for ch in c[:3])


# ═══════════════════════════════════════════════
# 1. TERRAIN HD (dilukis per-piksel)
# ═══════════════════════════════════════════════

def _build_hd_terrain(theme, W, H):
    """Terrain HD: noise halus + blend radiant/dire mulus + stroke."""
    tname = theme.get("name", "Forest")
    seed = zlib_crc32(tname)
    sw, sh = 160, 90           # basis (murah per-piksel)
    sw2, sh2 = 320, 180        # detail stroke

    rg1 = theme["radiant_grass_1"][:3]
    rg2 = theme["radiant_grass_2"][:3]
    rg3 = theme["radiant_grass_3"][:3]
    rg4 = theme["radiant_grass_4"][:3]
    de1 = theme["dire_earth_1"][:3]
    de2 = theme["dire_earth_2"][:3]
    de3 = theme["dire_earth_3"][:3]
    d_burnt = theme["dire_burnt"][:3]
    d_ash = theme["dire_ash"][:3]

    rad_mid = _mix(rg2, rg3, 0.5)
    dir_mid = _mix(de2, de3, 0.5)

    n1 = _ValueNoise(seed, 7, 4)        # mottling besar
    n2 = _ValueNoise(seed + 7919, 16, 9)  # detail menengah

    surf = pygame.Surface((sw, sh))
    for y in range(sh):
        yn = y / (sh - 1)
        for x in range(sw):
            xn = x / (sw - 1)
            # Garis pemisah radiant/dire (persis logika lama,
            # threshold_y = 200 + 320*x/1280 pada 1280x720)
            thr = 200.0 / H + (320.0 / H) * xn
            d = (yn - thr) / (60.0 / H)   # -1 dire .. +1 radiant
            s = _smoothstep(d * 0.5 + 0.5)
            base = _mix(dir_mid, rad_mid, s)
            n = 0.62 * n1.at(xn, yn) + 0.38 * n2.at(xn, yn)
            f = 0.88 + 0.26 * n
            surf.set_at((x, y), _shade(base, f))

    big = pygame.transform.smoothscale(surf, (sw2, sh2))

    # ── Stroke detail (di 320x180; jadi goresan empuk setelah
    #    di-upscale — kesan kuas/cat, bukan piksel) ──
    rng = random.Random(seed + 104729)
    for _ in range(650):
        x = rng.randrange(sw2)
        y = rng.randrange(sh2)
        xn = x / sw2
        yn = y / sh2
        thr = 200.0 / H + (320.0 / H) * xn
        if yn > thr + 0.05:  # sisi radiant: rumput
            c = _mix(rg3, rg4, rng.random())
            dx = 1 if rng.random() < 0.5 else -1
            pygame.draw.line(big, c, (x, y), (x + dx, y - 1), 1)
        elif yn < thr - 0.05:  # sisi dire: abu/char
            c = _mix(d_ash, d_burnt, rng.random() * 0.8)
            pygame.draw.line(big, c, (x, y),
                             (x + rng.choice((-1, 0, 1)),
                              y + rng.choice((0, 1))), 1)
    # Sedikit highlight terang (cahaya) di kedua sisi
    for _ in range(220):
        x = rng.randrange(sw2)
        y = rng.randrange(sh2)
        xn = x / sw2
        yn = y / sh2
        thr = 200.0 / H + (320.0 / H) * xn
        if yn > thr + 0.06:
            c = _mix(rg4, (255, 255, 255), 0.15)
        elif yn < thr - 0.06:
            c = _mix(de3, (255, 255, 255), 0.12)
        else:
            continue
        pygame.draw.rect(big, c, (x, y, 1, 1))

    return pygame.transform.smoothscale(big, (W, H))


# ═══════════════════════════════════════════════
# 2. OBJEK 2x (supersample -> smoothscale = feather)
# ═══════════════════════════════════════════════

class _Scaled2D:
    """Konteks: skala SEMUA koordinat pygame.draw sebesar Sx
    selama active; code art asli dipanggil dengan koordinat 1x
    -> output Sx di canvas 2x.

    Hanya fungsi pygame.draw yang di-patch (module attribute —
    aman). Layer yang blit surface internal (glow kristal/bunga)
    ditangani terpisah: sprite 1x di-upscale ke 2x lalu di-blit
    (efek feather sama). Dikembalikan apa adanya saat keluar.
    """

    def __init__(self, s=2):
        self.s = int(s)
        self._saved = {}

    def __enter__(self):
        S = self.s
        import pygame as pg

        def sp(pt):
            return (int(pt[0] * S), int(pt[1] * S))

        d = pg.draw
        self._saved = {
            "rect": d.rect, "line": d.line, "lines": d.lines,
            "polygon": d.polygon, "circle": d.circle,
            "ellipse": d.ellipse, "arc": d.arc,
            "aaline": d.aaline,
        }

        def rect(surf, color, r, *a, **kw):
            rr = (int(r[0] * S), int(r[1] * S),
                  int(r[2] * S), int(r[3] * S))
            if a and a[0]:
                a = (max(1, int(a[0] * S)),) + a[1:]
            if kw.get("border_radius"):
                kw["border_radius"] = max(1, int(kw["border_radius"] * S))
            return self._saved["rect"](surf, color, rr, *a, **kw)

        def line(surf, color, p1, p2, w=1):
            return self._saved["line"](
                surf, color, sp(p1), sp(p2),
                max(1, int(w * S)) if w else 1)

        def lines(surf, color, closed, pts, w=1):
            return self._saved["lines"](
                surf, color, closed, [sp(p) for p in pts],
                max(1, int(w * S)) if w else 1)

        def polygon(surf, color, pts, w=0):
            return self._saved["polygon"](
                surf, color, [sp(p) for p in pts],
                max(1, int(w * S)) if w else 0)

        def circle(surf, color, center, radius, w=0):
            return self._saved["circle"](
                surf, color, sp(center), int(radius * S),
                max(1, int(w * S)) if w else 0)

        def ellipse(surf, color, r, w=0):
            rr = (int(r[0] * S), int(r[1] * S),
                  int(r[2] * S), int(r[3] * S))
            return self._saved["ellipse"](
                surf, color, rr, max(1, int(w * S)) if w else 0)

        def arc(surf, color, r, a0, a1, w=1):
            rr = (int(r[0] * S), int(r[1] * S),
                  int(r[2] * S), int(r[3] * S))
            return self._saved["arc"](
                surf, color, rr, a0, a1, max(1, int(w * S)) if w else 1)

        def aaline(surf, color, p1, p2):
            return self._saved["aaline"](
                surf, color, sp(p1), sp(p2))

        d.rect = rect
        d.line = line
        d.lines = lines
        d.polygon = polygon
        d.circle = circle
        d.ellipse = ellipse
        d.arc = arc
        d.aaline = aaline
        return self

    def __exit__(self, exc_type, exc, tb):
        import pygame as pg
        for k, v in self._saved.items():
            setattr(pg.draw, k, v)
        return False


def _band_polygon(points, width):
    """Poligon pita mulus sepanjang daftar titik (lebar `width`)."""
    if len(points) < 2:
        return None
    left, right = [], []
    n = len(points)
    for i, (x, y) in enumerate(points):
        px, py = points[max(0, i - 1)]
        qx, qy = points[min(n - 1, i + 1)]
        dx, dy = qx - px, qy - py
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        left.append((x + nx * width / 2.0, y + ny * width / 2.0))
        right.append((x - nx * width / 2.0, y - ny * width / 2.0))
    return left + right[::-1]


def _hd_river(surf, river_points, theme):
    """Sungai HD: pita mulus + riak + glow (bukan grid tile 16px)."""
    r_deep = theme["river_deep"][:3]
    r_mid = theme["river_mid"][:3]
    r_light = theme["river_light"][:3]
    r_glow = theme["river_glow"][:3]
    r_foam = theme["river_foam"][:3]

    # Pita tepi (mid) lalu inti (deep)
    for color, w in ((r_mid, 46), (_mix(r_deep, r_mid, 0.35), 40),
                     (r_deep, 32)):
        poly = _band_polygon(river_points, w)
        if poly:
            pygame.draw.polygon(surf, color, poly)
            for end in (river_points[0], river_points[-1]):
                pygame.draw.circle(surf, color,
                                   (int(end[0]), int(end[1])),
                                   int(w / 2))

    # Riak: garis pendek searah aliran
    n = len(river_points)
    for i in range(4, n - 4, 5):
        x, y = river_points[i]
        px, py = river_points[i - 3]
        qx, qy = river_points[i + 3]
        dx, dy = qx - px, qy - py
        L = math.hypot(dx, dy) or 1.0
        dx, dy = dx / L, dy / L
        hsh = (i * 2654435761) % 100
        off = ((hsh % 9) - 4) * 1.2
        nx, ny = -dy, dx
        x1 = x + dx * 2 + nx * off
        y1 = y + dy * 2 + ny * off
        c = _mix(r_mid, r_light,
                 0.55 + 0.4 * ((hsh // 7) % 10) / 10.0)
        pygame.draw.line(surf, c, (x1, y1),
                         (x1 + dx * 6, y1 + dy * 6), 1)

    # Glow rune statis (animasi glow per-frame tetap di
    # DynamicRenderer; yang ini aksen redup di peta statis)
    for i in range(8, n, 16):
        if (i * 2654435761) % 100 < 55:
            continue
        x, y = river_points[i]
        glow = pygame.Surface((12, 12), pygame.SRCALPHA)
        for r in (6, 5, 4, 3):
            pygame.draw.circle(glow, (*r_glow, 26 + (6 - r) * 12),
                               (6, 6), r)
        pygame.draw.circle(glow, (*r_foam, 160), (6, 6), 1)
        # blit tidak ikut patch 2x -> scale manual (dipanggil
        # dari konteks 2x)
        surf.blit(pygame.transform.smoothscale(glow, (24, 24)),
                  (int((x - 6) * 2), int((y - 6) * 2)))


def _hd_lane(surf, lane_points, theme):
    """Lane HD: pita mulus + kerikil batu terpisah + retakan glow
    (gaya lukisan, bukan grid slab 16px berulang)."""
    ps1 = theme["path_stone_1"][:3]
    ps2 = theme["path_stone_2"][:3]
    ps3 = theme["path_stone_3"][:3]
    ps4 = theme["path_stone_4"][:3]
    p_moss = theme["path_moss"][:3]
    p_crack = theme["path_crack"][:3]
    rmid = _mix(ps2, ps3, 0.5)

    # Pita: outline gelap -> badan -> sorotan tengah
    for color, w in ((ps1, 46), (_mix(ps1, ps2, 0.4), 43),
                     (rmid, 38), (_mix(rmid, ps3, 0.45), 30)):
        poly = _band_polygon(lane_points, w)
        if poly:
            pygame.draw.polygon(surf, color, poly)
            for end in (lane_points[0], lane_points[-1]):
                pygame.draw.circle(surf, color,
                                   (int(end[0]), int(end[1])),
                                   int(w / 2))

    # Kerikil: satu per tile (posisi & variasi deterministik,
    # mengikuti layout lama)
    drawn = set()
    for lx, ly in lane_points:
        for dy in range(-21, 22, 16):
            for dx in range(-21, 22, 16):
                tx = ((lx + dx) // 16) * 16
                ty = ((ly + dy) // 16) * 16
                if (tx, ty) in drawn:
                    continue
                if math.hypot(tx + 8 - lx, ty + 8 - ly) > 25:
                    continue
                drawn.add((tx, ty))
                cx, cy = tx + 8, ty + 8
                hsh = (tx * 31 + ty * 17) % 97
                sw = 10 + hsh % 4
                sh = 7 + (hsh // 5) % 3
                # Bayangan + badan + sorotan atas (batu 3D)
                pygame.draw.ellipse(
                    surf, _mix(ps1, rmid, 0.25),
                    (cx - sw // 2, cy - sh // 2 + 1, sw + 1, sh + 1))
                pygame.draw.ellipse(surf, _mix(ps2, ps3, 0.35),
                                    (cx - sw // 2, cy - sh // 2,
                                     sw, sh))
                pygame.draw.ellipse(surf, _mix(ps3, ps4, 0.35),
                                    (cx - sw // 2 + 1, cy - sh // 2,
                                     sw - 2, sh // 2))
                # Retakan cahaya tema (glow) — aksen identitas
                if (tx + ty) % 7 == 0:
                    pygame.draw.line(surf, p_crack,
                                     (cx - 4, cy - 1), (cx + 4, cy + 2), 1)
                    pygame.draw.line(
                        surf, _mix(p_crack, (255, 255, 255), 0.5),
                        (cx - 2, cy), (cx + 2, cy + 1), 1)
                # Lumut
                if hsh % 11 == 0:
                    pygame.draw.ellipse(surf, p_moss,
                                        (cx - 2, cy - 1, 5, 3))

    # Batu pinggir lane (kode lama; kini anti-aliased via 2x)
    from map_components.static_renderer import StaticRenderer
    for i in range(0, len(lane_points), 6):
        lx, ly = lane_points[i]
        if i < len(lane_points) - 1:
            nx, ny = lane_points[i + 1]
            ddx, ddy = nx - lx, ny - ly
            length = math.hypot(ddx, ddy)
            if length > 0:
                px, py = -ddy / length, ddx / length
                for side in (1, -1):
                    bx = int(lx + px * side * 23)
                    by = int(ly + py * side * 23)
                    if 5 < bx < 1275 and 5 < by < 715:
                        StaticRenderer._draw_lane_border_stone(
                            surf, bx, by, theme)


def _build_hd_objects(mr, W, H):
    """Render semua objek peta di canvas 2x, lalu smoothscale ke
    1x -> SEMUA tepi anti-aliased (feather, gaya sprite HD).

    - Sungai & lane: art VEKTOR HD (pita mulus + batu terpisah),
      digambar dengan pygame.draw di-patch 2x.
    - Dinding/toko/terrain details/dressing boss: kode art ASLI
      (murni draw call) lewat patch 2x.
    - Dekorasi: sprite 1x dari DecorSpriteCache di-upscale 2x
      (art-nya blit glow internal; upscale memberi feather sama).
    """
    from map_components.static_renderer import StaticRenderer
    from map_components.decoration_renderer import DecorationRenderer
    from map_components.shop_renderer import ShopRenderer
    from map_components.sprite_tiles import DecorSpriteCache

    # WAJIB SRCALPHA: canvas objek transparan, hanya objek yang
    # digambar yang ikut ke hasil (terrain HD ada di bawahnya).
    big = pygame.Surface((W * 2, H * 2), pygame.SRCALPHA)
    big.fill((0, 0, 0, 0))
    with _Scaled2D(2):
        StaticRenderer.draw_terrain_details(
            big, W, H, mr.theme)
        _hd_river(big, mr.river_points, mr.theme)
        for lane in (mr.top_lane_points, mr.mid_lane_points,
                     mr.bot_lane_points):
            _hd_lane(big, lane, mr.theme)
    # Dekorasi (urutan painter sama; sprite 1x -> 2x upscale)
    decor = DecorSpriteCache(mr.theme)
    decor.blit_all_scaled(big, mr, 2)
    # Sisanya: murni draw call -> ikut supersample 2x
    with _Scaled2D(2):
        DecorationRenderer._draw_true_boss_decorations(big, mr)
        ShopRenderer.draw(big, mr.radiant_shop_pos,
                          mr.dire_shop_pos)
        StaticRenderer.draw_border_wall(big, W, H, mr.theme)
    return pygame.transform.smoothscale(big, (W, H))


# ═══════════════════════════════════════════════
# 3. CACHE PER TEMA + ENTRY POINT
# ═══════════════════════════════════════════════

_HD_CACHE = {}
_HD_MAX = 3  # tema: (terrain + objects + lightmap) ~11 MB/tema


def zlib_crc32(s):
    import zlib
    return zlib.crc32(s.encode("utf-8"))


def get_hd_layers(mr):
    """Return dict layer ter-cache (terrain/objects/light) per tema.

    Layout lane/dekorasi deterministik per ukuran peta, jadi satu
    cache per tema dipakai ulang untuk semua level tema itu.
    """
    from map_components.sprite_tiles import MapTileSprites
    W, H = mr.map_width, mr.map_height
    tname = mr.theme.get("name", "Forest")
    key = (tname, W, H)
    hit = _HD_CACHE.get(key)
    if hit is not None:
        # sentuh LRU
        _HD_CACHE.pop(key)
        _HD_CACHE[key] = hit
        return hit

    tiles = MapTileSprites(mr.theme)  # reuse cache lightmap
    tname2 = tname
    pair = MapTileSprites._lightmap_lru.get((tname2, W, H))
    if pair is None:
        pair = tiles._make_lightmap(W, H)
        MapTileSprites._lightmap_lru[(tname2, W, H)] = pair
        while len(MapTileSprites._lightmap_lru) > 3:
            MapTileSprites._lightmap_lru.pop(
                next(iter(MapTileSprites._lightmap_lru)))

    layers = {
        "terrain": _build_hd_terrain(mr.theme, W, H),
        "objects": _build_hd_objects(mr, W, H),
        "light": pair,
    }
    _HD_CACHE[key] = layers
    while len(_HD_CACHE) > _HD_MAX:
        _HD_CACHE.pop(next(iter(_HD_CACHE)))
    return layers


def render_hd_static_map(mr):
    """Entry: peta statis HD (gaya sprite HD Thorne)."""
    W, H = mr.map_width, mr.map_height
    layers = get_hd_layers(mr)

    surf = layers["terrain"].copy()
    surf.blit(layers["objects"], (0, 0))
    # Lightmap (shading skala besar)
    surf.blit(layers["light"][0], (0, 0),
              special_flags=pygame.BLEND_RGB_MULT)
    surf.blit(layers["light"][1], (0, 0),
              special_flags=pygame.BLEND_RGB_ADD)
    return surf
