"""
map_components/sprite_tiles.py - SPRITE-BASED MAP RENDERING
══════════════════════════════════════════════════════════

Peta sekarang dirender dengan prinsip yang SAMA dengan ikon
item (assets/items/*.png -> get_icon() di hero_items.py):

  * Setiap elemen (tile terrain, cobblestone, sungai, dinding,
    dekorasi, bangunan toko) dirender SATU KALI ke pygame.Surface
    ter-cache ("sprite"), lalu hanya di-blit ke peta statis.
  * Shading gaya ikon item datang dari dua sumber:
      - LIGHTMAP skala besar (gradien diagonal lembut + blob
        cahaya/gelap besar) yang di-blit sekali ke seluruh peta
        -> kesan permukaan "dilukis", bukan kisi-kisi 16px;
      - bevel 3D + outline + aksen glow (retakan cahaya tema,
        riak sungai) hanya pada "objek" (lane, sungai, dinding)
        yang memang harus terlihat sebagai blok.

Dampak:
  * VISUAL  : tile tidak lagi kotak datar; bevel + gradien +
              glow retakan membuat peta terasa "dipoles" seperti
              ikon item. Semua warna tetap diambil dari palette
              tema, jadi SEMUA tema (54 level) otomatis dapat
              tampilan baru tanpa aset PNG tambahan.
  * PERF    : peta statis dulunya butuh ratusan ribu draw call
              (rect/line/polygon per tile). Sekarang init hanya
              membangun ~30 sprite kecil lalu ribuan blit —
              blit surface kecil adalah operasi termurah di
              pygame. Per-frame tetap 1 blit peta statis (tidak
              berubah), jadi tidak ada biaya frame baru.

Akses:
    from map_components.sprite_tiles import MapTileSprites, DecorSpriteCache
    tiles = MapTileSprites(theme)
    tiles.blit_terrain(surf, w, h)
    ...
Fallback: kalau modul ini error, MapRenderer otomatis pakai
pipeline lama (MYSTIC_LEGACY_MAP=1 memaksakan pipeline lama).
"""
import math
import random
import zlib

import pygame

from map_components.palettes import (
    TILE_SIZE, OUTLINE,
    STONE_DARK, STONE_MID, STONE_LIGHT, STONE_HIGH,
)

T = TILE_SIZE  # 16


# ═══════════════════════════════════════════════
# COLOR HELPERS (gaya ikon item: gradien + bevel)
# ═══════════════════════════════════════════════

def _c3(c):
    """Truncate warna ke 3 kanal (buang alpha)."""
    return (int(c[0]), int(c[1]), int(c[2]))


def mix(c1, c2, t):
    """Blend linear antar dua warna, t = 0..1."""
    a, b = _c3(c1), _c3(c2)
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def shade(c, f):
    """Perbanyak/encerkan warna (f < 1 menggelapkan)."""
    return tuple(int(max(0, min(255, ch * f))) for ch in _c3(c))


def _grad_v(surf, x, y, w, h, top, bottom):
    """Gradien vertikal baris per baris (halus di ukuran kecil)."""
    top, bottom = _c3(top), _c3(bottom)
    if h <= 1:
        pygame.draw.rect(surf, top, (x, y, w, h))
        return
    for i in range(h):
        t = i / (h - 1)
        pygame.draw.line(surf, mix(top, bottom, t),
                         (x, y + i), (x + w - 1, y + i))


def _bevel(surf, rect, top, bottom, hi=0.22, lo=0.24):
    """Bevel 1px gaya ikon: atas terang, bawah gelap, kiri/kanan
    sedikit. Memberi kesan blok 3D halus di atas gradien."""
    x, y, w, h = rect
    pygame.draw.line(surf, mix(top, (255, 255, 255), hi),
                     (x, y), (x + w - 1, y), 1)
    pygame.draw.line(surf, shade(bottom, 1 - lo),
                     (x, y + h - 1), (x + w - 1, y + h - 1), 1)
    pygame.draw.line(surf, mix(top, (255, 255, 255), hi * 0.45),
                     (x, y + 1), (x, y + h - 2), 1)
    pygame.draw.line(surf, shade(bottom, 1 - lo * 0.55),
                     (x + w - 1, y + 1), (x + w - 1, y + h - 2), 1)


def _key_seed(*parts):
    """Seed deterministik per kunci sprite (reproducible art)."""
    return zlib.crc32(repr(parts).encode("utf-8"))


# ═══════════════════════════════════════════════
# TILE SPRITES (terrain / path / river / border)
# ═══════════════════════════════════════════════

class MapTileSprites:
    """Cache sprite tile 16x16 per tema.

    Setiap sprite dibangun SEKALI (gaya ikon item: gradien +
    bevel + highlight) lalu di-blit ribuan kali ke peta statis.
    Kunci cache = nama tema, sehingga level berbeda dengan tema
    sama tidak membangun ulang.
    """

    _global_cache = {}
    _MAX_THEMES = 64

    def __init__(self, theme):
        self.theme = theme
        tname = theme.get("name", "Forest")
        key = tname
        hit = MapTileSprites._global_cache.get(key)
        if hit is not None:
            self.__dict__.update(hit)
            return
        self._build_all()
        self._cache_dict = {
            k: self.__dict__[k] for k in (
                "rad", "dire", "trans", "path", "river",
                "border_v", "border_h", "spike")
        }
        MapTileSprites._global_cache[key] = self._cache_dict
        if len(MapTileSprites._global_cache) > MapTileSprites._MAX_THEMES:
            MapTileSprites._global_cache.pop(
                next(iter(MapTileSprites._global_cache)))

    # ─────────────────────────────────────────
    # BUILDERS
    # ─────────────────────────────────────────

    def _build_all(self):
        th = self.theme
        self._build_terrain(th)
        self._build_path(th)
        self._build_river(th)
        self._build_border(th)

    # ── TERRAIN ──

    def _tile_surf(self):
        return pygame.Surface((T, T))

    def _build_terrain(self, th):
        """Sprite terrain per side.

        Variant index mengikuti distribusi lama:
        radiant: 0=<20 blades, 1=<35 patch, 2=<45 moss, 3=<55 dot
        dire   : 0=<20 lines , 1=<35 ash  , 2=<50 pebble,
                3=<60 chunk, 4=<68 lightdot
        trans  : 0=<30 dash
        (angka di atas = nilai (tx*7+ty*13)%100)

        Tile terrain dibuat DATAR (tanpa gradien/bevel per tile —
        itu yang membuat kesan kisi-kisi 16px). Kekayaan visual
        datang dari LIGHTMAP skala besar (lihat _make_lightmap):
        gradien diagonal lembut + blob cahaya/gelap besar yang
        di-blit sekali ke seluruh peta — persis shading halus
        pada ikon item. Bevel 3D hanya dipakai pada "objek"
        (lane, sungai, dinding) yang memang harus terlihat blok.
        """

        def flat(fill):
            s = self._tile_surf()
            s.fill(fill)
            return s

        # ── Radiant (rumput) ──
        r1, r2 = th["radiant_grass_1"], th["radiant_grass_2"]
        r3 = th["radiant_grass_3"]
        r4 = th["radiant_grass_4"]
        rgh = th["radiant_grass_high"]
        moss = th["radiant_moss"]
        rmid = mix(r2, r3, 0.5)

        s = flat(rmid)  # v0 blades
        for gx, gy in [(2, 8), (7, 9), (12, 8)]:
            pygame.draw.rect(s, mix(rmid, r4, 0.45), (gx, gy, 1, 3))
            pygame.draw.rect(s, r4, (gx, gy, 1, 1))
        pygame.draw.rect(s, mix(r1, rmid, 0.4), (13, 12, 1, 1))
        self.rad = [s]

        s = flat(rmid)  # v1 patch
        pygame.draw.rect(s, mix(r1, rmid, 0.55), (3, 4, 8, 4))
        pygame.draw.rect(s, mix(r1, rmid, 0.3), (3, 4, 8, 1))
        self.rad.append(s)

        s = flat(rmid)  # v2 moss
        pygame.draw.rect(s, moss, (5, 6, 6, 4))
        pygame.draw.rect(s, mix(moss, (255, 255, 255), 0.25), (5, 6, 6, 1))
        self.rad.append(s)

        s = flat(rmid)  # v3 dot
        pygame.draw.rect(s, rgh, (6, 4, 2, 2))
        pygame.draw.rect(s, mix(r4, (255, 255, 255), 0.3), (10, 10, 1, 1))
        self.rad.append(s)

        s = flat(rmid)  # v4 plain (speckle halus)
        pygame.draw.rect(s, mix(rmid, r4, 0.5), (4, 5, 1, 1))
        pygame.draw.rect(s, mix(rmid, r1, 0.5), (11, 9, 1, 1))
        pygame.draw.rect(s, mix(rmid, r4, 0.35), (9, 12, 1, 1))
        self.rad.append(s)

        # ── Dire (tanah) ──
        d2, d3 = th["dire_earth_2"], th["dire_earth_3"]
        d4 = th["dire_earth_4"]
        d_ash, d_burnt = th["dire_ash"], th["dire_burnt"]
        dmid = mix(d2, d3, 0.5)

        s = flat(dmid)  # v0 lines
        pygame.draw.line(s, d_burnt, (2, 6), (10, 8), 1)
        pygame.draw.line(s, d_burnt, (6, 4), (8, 12), 1)
        pygame.draw.line(s, mix(d_burnt, (255, 255, 255), 0.25),
                         (7, 4), (8, 11), 1)
        self.dire = [s]

        s = flat(dmid)  # v1 ash
        pygame.draw.rect(s, d_ash, (3, 5, 5, 3))
        pygame.draw.rect(s, mix(d_ash, (255, 255, 255), 0.2), (3, 5, 5, 1))
        self.dire.append(s)

        s = flat(dmid)  # v2 pebble
        pygame.draw.rect(s, mix(d_ash, d4, 0.4), (5, 9, 2, 2))
        pygame.draw.rect(s, mix(d_ash, d4, 0.4), (10, 4, 2, 2))
        pygame.draw.rect(s, shade(d_ash, 0.7), (6, 9, 1, 1))
        self.dire.append(s)

        s = flat(dmid)  # v3 chunk
        pygame.draw.rect(s, d_burnt, (4, 6, 4, 3))
        pygame.draw.rect(s, d4, (5, 3, 3, 2))
        self.dire.append(s)

        s = flat(dmid)  # v4 lightdot
        pygame.draw.rect(s, d4, (5, 3, 3, 2))
        pygame.draw.rect(s, mix(d4, (255, 255, 255), 0.4), (5, 3, 1, 1))
        self.dire.append(s)

        s = flat(dmid)  # v5 plain (speckle halus)
        pygame.draw.rect(s, d_ash, (4, 7, 1, 1))
        pygame.draw.rect(s, mix(d2, d4, 0.6), (10, 11, 1, 1))
        self.dire.append(s)

        # ── Transition ──
        t1, t2 = th["transition_1"], th["transition_2"]
        tmid = mix(t1, t2, 0.5)
        s = flat(tmid)
        self.trans = [s]
        s2 = flat(tmid)
        pygame.draw.rect(s2, shade(t1, 0.85), (4, 6, 4, 2))
        pygame.draw.rect(s2, mix(t1, t2, 0.5), (10, 10, 1, 1))
        self.trans.append(s2)

    # ── PATH (cobblestone, bevel gaya ikon) ──

    def _build_path(self, th):
        ps1 = th["path_stone_1"]
        ps2 = th["path_stone_2"]
        ps3 = th["path_stone_3"]
        ps4 = th["path_stone_4"]
        self._path_moss = th["path_moss"]
        self._path_crack = th["path_crack"]
        self._path_light = mix(ps3, (255, 255, 255), 0.28)
        self._path_dark = shade(ps2, 0.72)
        self.path = {}

        def slab():
            s = self._tile_surf()
            pygame.draw.rect(s, ps1, (0, 0, T, T))            # outline
            _grad_v(s, 1, 1, T - 2, T - 2, mix(ps3, (255, 255, 255), 0.18),
                     shade(ps2, 0.9))
            pygame.draw.line(s, self._path_light, (1, 1), (14, 1), 1)
            pygame.draw.line(s, mix(ps3, (255, 255, 255), 0.14),
                             (1, 2), (1, 14), 1)
            pygame.draw.line(s, self._path_dark, (1, 14), (14, 14), 1)
            pygame.draw.line(s, shade(ps1, 1.25), (14, 2), (14, 14), 1)
            return s

        def slab_split():
            s = slab()
            pygame.draw.line(s, ps1, (1, 8), (14, 8), 1)      # garis pemisah
            _grad_v(s, 1, 9, T - 2, T - 10, mix(ps3, (255, 255, 255), 0.10),
                     shade(ps2, 0.88))
            pygame.draw.line(s, self._path_light, (1, 9), (14, 9), 1)
            return s

        def slab_quad():
            s = self._tile_surf()
            pygame.draw.rect(s, ps1, (0, 0, T, T))
            for ox, oy in ((1, 1), (9, 1), (1, 9), (9, 9)):
                _grad_v(s, ox, oy, 6, 6, mix(ps3, (255, 255, 255), 0.16),
                        shade(ps2, 0.9))
                pygame.draw.line(s, self._path_light,
                                 (ox, oy), (ox + 5, oy), 1)
                pygame.draw.line(s, self._path_dark,
                                 (ox, oy + 5), (ox + 5, oy + 5), 1)
            return s

        builders = {"slab": slab, "split": slab_split, "quad": slab_quad}

        # 3 slab x crack x moss = 9 sprite path
        for name, build in builders.items():
            for crack in (False, True):
                for moss in (False, True):
                    s = build()
                    if crack:
                        pygame.draw.line(s, self._path_crack,
                                         (3, 4), (10, 7), 1)
                        pygame.draw.line(s,
                                         mix(self._path_crack,
                                             (255, 255, 255), 0.5),
                                         (4, 5), (8, 6), 1)
                        pygame.draw.rect(s,
                                         mix(self._path_crack,
                                             (255, 255, 255), 0.35),
                                         (9, 6, 2, 2))
                    if moss:
                        pygame.draw.rect(s, self._path_moss, (3, 3, 3, 2))
                        pygame.draw.rect(s,
                                         mix(self._path_moss,
                                             (255, 255, 255), 0.3),
                                         (3, 3, 2, 1))
                    self.path[(name, crack, moss)] = s

    # ── RIVER ──

    def _build_river(self, th):
        r_deep = th["river_deep"]
        r_mid = th["river_mid"]
        r_glow = th["river_glow"]
        r_foam = th["river_foam"]

        s = self._tile_surf()
        _grad_v(s, 0, 0, T, T, mix(r_mid, (255, 255, 255), 0.12),
                shade(r_deep, 0.9))
        # riak (posisi lama: grid 4px, (dx+dy)%8==0)
        for ddx, ddy in ((0, 0), (8, 0), (4, 4), (12, 4), (8, 8), (12, 12)):
            pygame.draw.rect(s, r_mid, (ddx, ddy, 2, 2))
            pygame.draw.rect(s, mix(r_mid, (255, 255, 255), 0.35),
                             (ddx, ddy, 1, 1))
        self.river = {"inner": s}

        s = self._tile_surf()
        _grad_v(s, 0, 0, T, T, mix(r_mid, (255, 255, 255), 0.12),
                shade(r_deep, 0.9))
        for ddx, ddy in ((0, 0), (8, 0), (4, 4), (12, 4), (8, 8), (12, 12)):
            pygame.draw.rect(s, r_mid, (ddx, ddy, 2, 2))
        # glow rune (glow gaya ikon item)
        glow = pygame.Surface((12, 12), pygame.SRCALPHA)
        for r in (6, 5, 4, 3, 2):
            pygame.draw.circle(glow, (*_c3(r_glow), 30 + (6 - r) * 14),
                               (6, 6), r)
        pygame.draw.circle(glow, (*_c3(r_foam), 200), (6, 6), 1)
        s.blit(glow, (2, 2))
        self.river["inner_glow"] = s

        s = self._tile_surf()
        _grad_v(s, 0, 0, T, T, r_mid, shade(r_deep, 0.85))
        pygame.draw.line(s, shade(r_deep, 0.8), (0, 0), (15, 0), 1)
        self.river["edge"] = s

    # ── BORDER WALL ──

    def _build_border(self, th):
        def block(w, h):
            s = pygame.Surface((w, h))
            pygame.draw.rect(s, OUTLINE, (0, 0, w, h))
            _grad_v(s, 1, 1, w - 2, h - 2, STONE_MID, STONE_DARK)
            pygame.draw.rect(s, STONE_LIGHT, (1, 1, w - 2, 2))
            pygame.draw.rect(s, STONE_HIGH, (2, 2, 4, 1))
            pygame.draw.line(s, shade(STONE_DARK, 0.8),
                             (1, h - 2), (w - 2, h - 2), 1)
            return s

        self.border_v = block(T, 20)   # atas/bawah
        self.border_h = block(20, T)   # kiri/kanan

        s2 = pygame.Surface((7, 7), pygame.SRCALPHA)
        pygame.draw.polygon(s2, OUTLINE, [(0, 0), (6, 0), (3, 6)])
        pygame.draw.polygon(s2, STONE_MID, [(1, 1), (5, 1), (3, 5)])
        pygame.draw.line(s2, STONE_LIGHT, (3, 1), (3, 4), 1)
        self.spike = s2

    # ─────────────────────────────────────────
    # BLIT (meniru layout pipeline lama 1:1)
    # ─────────────────────────────────────────

    def terrain(self, side, v):
        if side == "radiant":
            if v < 20:
                return self.rad[0]
            if v < 35:
                return self.rad[1]
            if v < 45:
                return self.rad[2]
            if v < 55:
                return self.rad[3]
            return self.rad[4]
        if side == "dire":
            if v < 20:
                return self.dire[0]
            if v < 35:
                return self.dire[1]
            if v < 50:
                return self.dire[2]
            if v < 60:
                return self.dire[3]
            if v < 68:
                return self.dire[4]
            return self.dire[5]
        if v < 30:
            return self.trans[0]
        return self.trans[1]

    def blit_terrain(self, surf, map_w, map_h):
        for ty in range(0, map_h, T):
            for tx in range(0, map_w, T):
                threshold_y = 200 + (map_h - 400) * tx / map_w
                if ty > threshold_y + 20:
                    side = "radiant"
                elif ty < threshold_y - 20:
                    side = "dire"
                else:
                    side = "transition"
                v = (tx * 7 + ty * 13) % 100
                surf.blit(self.terrain(side, v), (tx, ty))

    def blit_river(self, surf, river_points, map_w, map_h):
        rw = 44
        half = rw // 2
        for rx, ry in river_points:
            for dy in range(-half, half, T):
                for dx in range(-half, half, T):
                    tx = ((rx + dx) // T) * T
                    ty = ((ry + dy) // T) * T
                    if tx < 0 or ty < 0 or tx >= map_w or ty >= map_h:
                        continue
                    dist = math.hypot(tx + T // 2 - rx,
                                      ty + T // 2 - ry)
                    if dist > half:
                        continue
                    if dist < half - 6:
                        if (tx * ty) % 137 == 0:
                            spr = self.river["inner_glow"]
                        else:
                            spr = self.river["inner"]
                    else:
                        spr = self.river["edge"]
                    surf.blit(spr, (tx, ty))

        # River banks (dipertahankan: jumlah kecil)
        for i in range(0, len(river_points), 3):
            rx, ry = river_points[i]
            if i < len(river_points) - 1:
                nx, ny = river_points[i + 1]
                ddx, ddy = nx - rx, ny - ry
                length = math.hypot(ddx, ddy)
                if length > 0:
                    px, py = -ddy / length, ddx / length
                    for side in (1, -1):
                        bx = int(rx + px * side * (half + 2))
                        by = int(ry + py * side * (half + 2))
                        if 0 <= bx < map_w and 0 <= by < map_h:
                            pygame.draw.rect(surf, OUTLINE,
                                             (bx - 3, by - 3, 6, 6))
                            pygame.draw.rect(surf, STONE_DARK,
                                             (bx - 3, by - 3, 6, 6))
                            pygame.draw.rect(surf, STONE_MID,
                                             (bx - 2, by - 2, 4, 4))
                            pygame.draw.rect(surf, STONE_LIGHT,
                                             (bx - 2, by - 2, 2, 2))

    def blit_lane(self, surf, lane_points, map_w, map_h):
        lw = 42
        drawn = set()
        for lx, ly in lane_points:
            for dy in range(-lw, lw, T):
                for dx in range(-lw, lw, T):
                    tx = ((lx + dx) // T) * T
                    ty = ((ly + dy) // T) * T
                    if (tx, ty) in drawn:
                        continue
                    dist = math.hypot(tx + T // 2 - lx,
                                      ty + T // 2 - ly)
                    if dist > lw // 2 + 4:
                        continue
                    if tx < 0 or ty < 0 or tx >= map_w or ty >= map_h:
                        continue
                    drawn.add((tx, ty))
                    v = (tx * 3 + ty * 7) % 100
                    name = "slab" if v < 40 else (
                        "split" if v < 70 else "quad")
                    surf.blit(self.path[(name, (tx + ty) % 7 == 0,
                                          v > 85)], (tx, ty))

        # Border stones lane (jumlah kecil, dipertahankan)
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
                        bx = int(lx + px * side * (lw // 2 + 2))
                        by = int(ly + py * side * (lw // 2 + 2))
                        if 5 < bx < map_w - 5 and 5 < by < map_h - 5:
                            StaticRenderer._draw_lane_border_stone(
                                surf, bx, by, self.theme)

    def blit_border(self, surf, map_w, map_h):
        for x in range(0, map_w, T):
            surf.blit(self.border_v, (x, 0))
            surf.blit(self.border_v, (x, map_h - 20))
        for y in range(20, map_h - 20, T):
            surf.blit(self.border_h, (0, y))
            surf.blit(self.border_h, (map_w - 20, y))
        for x in range(30, map_w - 30, 40):
            surf.blit(self.spike, (x - 3, 20))

    # ── LIGHTMAP (shading skala besar, gaya ikon item) ──

    def _make_lightmap(self, map_w, map_h):
        """Bangun lightmap dua lapis (gelap & terang).

        Dibangun di resolusi kecil (64x36) lalu di-smoothscale:
        per-pixel Python murah, hasil transisi SANGAT halus.
        Isi:
          * gradien diagonal lembut — sisi radiant (bawah-kiri)
            lebih terang, sisi dire (atas-kanan) lebih gelap;
          * ~20 blob cahaya/gelap besar (mottling) supaya peta
            terasa "dilukis", bukan kisi-kisi tile.
        Dikombinasikan per-frame-tanpa-biaya: cukup 2 blit
        BLEND_RGB_MULT/ADD SATU KALI saat peta dirender.
        """
        sw, sh = 64, 36
        dark = pygame.Surface((sw, sh))
        bright = pygame.Surface((sw, sh))
        for y in range(sh):
            ty = y / (sh - 1)
            for x in range(sw):
                tx = x / (sw - 1)
                t = tx * 0.45 + (1.0 - ty) * 0.55  # 1 = pojok dire
                base = 255 - int(30 * t)
                dark.set_at((x, y), (base, base, base))
                bright.set_at((x, y), (0, 0, 0))
        tname = self.theme.get("name", "Forest")
        rng = random.Random(_key_seed(tname, "lightmap"))
        for _ in range(20):
            cx = rng.randint(2, sw - 3)
            cy = rng.randint(2, sh - 3)
            r = rng.randint(5, 13)
            amt = rng.randint(9, 22)
            is_dark = rng.random() < 0.55
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    d2 = dx * dx + dy * dy
                    if d2 > r * r:
                        continue
                    px, py = cx + dx, cy + dy
                    if not (0 <= px < sw and 0 <= py < sh):
                        continue
                    f = 1.0 - (d2 ** 0.5) / r
                    f *= f
                    if is_dark:
                        c = dark.get_at((px, py))[0] - int(amt * f)
                        dark.set_at((px, py), (c, c, c))
                    else:
                        add = min(36, int(amt * f * 0.55))
                        c = bright.get_at((px, py))[0] + add
                        bright.set_at((px, py), (c, c, c))
        return (pygame.transform.smoothscale(dark, (map_w, map_h)),
                pygame.transform.smoothscale(bright, (map_w, map_h)))

    _lightmap_lru = {}
    _LIGHTMAP_MAX = 3  # tema: ~16 MB total (2 surface 720p)

    def apply_light(self, surf, map_w, map_h):
        """Aplikasikan lightmap ke permukaan peta (2 blit besar).

        Dipanggil SEKALI saat peta statis dirender — hasil
        shading halus ikut terbake ke cached surface, jadi
        tidak ada biaya per-frame. Lightmap di-cache per tema
        (LRU kecil) supaya retry level tidak membangun ulang.
        """
        tname = self.theme.get("name", "Forest")
        lru = MapTileSprites._lightmap_lru
        key = (tname, map_w, map_h)
        pair = lru.get(key)
        if pair is None:
            pair = self._make_lightmap(map_w, map_h)
            lru[key] = pair
            while len(lru) > MapTileSprites._LIGHTMAP_MAX:
                lru.pop(next(iter(lru)))
        surf.blit(pair[0], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(pair[1], (0, 0), special_flags=pygame.BLEND_RGB_ADD)


# ═══════════════════════════════════════════════
# DECORATION SPRITE CACHE
# ═══════════════════════════════════════════════

class DecorSpriteCache:
    """Render tiap dekorasi SATU KALI jadi sprite ter-cache,
    lalu blit ke posisi aslinya.

    Seni dipakai PERSIS fungsi lama (DecorationRenderer._draw_*)
    sehingga tampilan tidak berubah bentuk — hanya menjadi
    sprite (sama seperti ikon item). Cache per (kind, size,
    variant, tema) dengan seed deterministik supaya art stabil.
    """

    _global_cache = {}
    _MAX = 4096

    def __init__(self, theme):
        self.theme = theme
        self.tname = theme.get("name", "Forest")
        self._local = self._cache()

    # ── util ──

    def _cache(self):
        """Dict cache per tema (dipakai ulang antar level dengan
        tema sama, mis. retry) — LRU maks 4 tema."""
        hit = DecorSpriteCache._global_cache.get(self.tname)
        if hit is None:
            hit = {}
            DecorSpriteCache._global_cache[self.tname] = hit
            if len(DecorSpriteCache._global_cache) > 4:
                DecorSpriteCache._global_cache.pop(
                    next(iter(DecorSpriteCache._global_cache)))
        return hit

    def _build(self, key, box, anchor, draw_one):
        """Bangun sprite: draw_one(surf) menggambar di sekitar
        anchor; hasil di-blit dengan surf_offset = -anchor."""
        loc = self._cache()
        hit = loc.get(key)
        if hit is not None:
            return hit
        w, h = box
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        saved = random.getstate()
        random.seed(_key_seed(self.tname, key))
        try:
            draw_one(surf)
        finally:
            random.setstate(saved)
        if len(loc) > DecorSpriteCache._MAX:
            loc.pop(next(iter(loc)))
        loc[key] = surf
        return surf

    # ── dekorasi per jenis (box, anchor dihitung dari art lama) ──

    # Trees

    def dark_tree(self, size, variant):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 12
        h = size * 3 + 12
        ax, ay = size + 6, int(size * 1.5) + 4
        surf = self._build(
            ("dark_tree", size, variant), (w, h), (ax, ay),
            lambda s: D._draw_dark_trees(s, [(ax, ay, size, variant)]))
        return surf, ax, ay

    def dead_tree(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size + 12
        h = int(size * 1.67) + 12
        ax, ay = w // 2, size + 8
        surf = self._build(
            ("dead_tree", size), (w, h), (ax, ay),
            lambda s: D._draw_dead_trees(s, [(ax, ay, size)], self.theme))
        return surf, ax, ay

    def frozen_tree(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size + 12
        h = int(size * 1.67) + 12
        ax, ay = w // 2, size + 8
        surf = self._build(
            ("frozen_tree", size), (w, h), (ax, ay),
            lambda s: D._draw_frozen_trees(s, [(ax, ay, size)]))
        return surf, ax, ay

    def cactus(self, size, variant):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = 2 * (size // 3 + 5) + 12
        h = int(size * 2.5) + 16
        ax, ay = w // 2, size + 12
        surf = self._build(
            ("cactus", size, variant), (w, h), (ax, ay),
            lambda s: D._draw_cactus(s, [(ax, ay, size, variant)]))
        return surf, ax, ay

    def palm(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = 2 * max(16, size) + 12
        h = int(size * 2.5) + 34
        ax, ay = w // 2, size + 28
        surf = self._build(
            ("palm", size), (w, h), (ax, ay),
            lambda s: D._draw_palm_trees(s, [(ax, ay, size)]))
        return surf, ax, ay

    # Ground objects

    def gravestone(self):
        from map_components.decoration_renderer import DecorationRenderer as D
        w, h, ax, ay = 24, 32, 12, 24
        surf = self._build(
            ("gravestone",), (w, h), (ax, ay),
            lambda s: D._draw_gravestones(s, [(ax, ay)]))
        return surf, ax, ay

    def bone(self, btype):
        from map_components.decoration_renderer import DecorationRenderer as D
        w, h, ax, ay = 24, 24, 12, 13
        surf = self._build(
            ("bone", btype), (w, h), (ax, ay),
            lambda s: D._draw_bones(s, [(ax, ay, btype)]))
        return surf, ax, ay

    def ruin(self, variant):
        from map_components.decoration_renderer import DecorationRenderer as D
        w, h, ax, ay = 32, 32, 16, 28
        surf = self._build(
            ("ruin", variant), (w, h), (ax, ay),
            lambda s: D._draw_ancient_ruins(s, [(ax, ay, variant)]))
        return surf, ax, ay

    def rock(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 12
        h = size * 2 + 8
        ax, ay = size + 6, size + 4
        surf = self._build(
            ("rock", size), (w, h), (ax, ay),
            lambda s: D._draw_rocks(s, [(ax, ay, size, True)],
                                    self.theme))
        return surf, ax, ay

    def rock_nomoss(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 12
        h = size * 2 + 8
        ax, ay = size + 6, size + 4
        surf = self._build(
            ("rock_nm", size), (w, h), (ax, ay),
            lambda s: D._draw_rocks(s, [(ax, ay, size, False)],
                                    self.theme))
        return surf, ax, ay

    def bush(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 16
        h = size * 3 + 8
        ax, ay = size + 5, size * 3 // 2
        surf = self._build(
            ("bush", size), (w, h), (ax, ay),
            lambda s: D._draw_dark_bushes(s, [(ax, ay, size)]))
        return surf, ax, ay

    def mushroom(self, color):
        from map_components.decoration_renderer import DecorationRenderer as D
        w, h, ax, ay = 24, 24, 12, 12
        key = ("mushroom", _c3(color))
        surf = self._build(
            key, (w, h), (ax, ay),
            lambda s: D._draw_mushrooms(s, [(ax, ay, color)]))
        return surf, ax, ay

    def flower(self, color):
        from map_components.decoration_renderer import DecorationRenderer as D
        w, h, ax, ay = 24, 28, 12, 18
        key = ("flower", _c3(color))
        surf = self._build(
            key, (w, h), (ax, ay),
            lambda s: D._draw_glow_flowers(s, [(ax, ay, color)]))
        return surf, ax, ay

    def spike(self):
        from map_components.decoration_renderer import DecorationRenderer as D
        w, h, ax, ay = 24, 20, 12, 16
        surf = self._build(
            ("spike_trap",), (w, h), (ax, ay),
            lambda s: D._draw_spike_traps(s, [(ax, ay)]))
        return surf, ax, ay

    # Crystals

    def crystal_blue(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 20
        h = size * 2 + 20
        ax, ay = size + 10, size + 10
        surf = self._build(
            ("cry_b", size), (w, h), (ax, ay),
            lambda s: D._draw_crystals_blue(s, [(ax, ay, size)]))
        return surf, ax, ay

    def crystal_red(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 20
        h = size * 2 + 20
        ax, ay = size + 10, size + 10
        surf = self._build(
            ("cry_r", size), (w, h), (ax, ay),
            lambda s: D._draw_crystals_red(s, [(ax, ay, size)]))
        return surf, ax, ay

    def crystal_amber(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 20
        h = size * 2 + 20
        ax, ay = size + 10, size + 10
        surf = self._build(
            ("cry_a", size), (w, h), (ax, ay),
            lambda s: D._draw_crystals_amber(s, [(ax, ay, size)]))
        return surf, ax, ay

    def ice_crystal(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = 48
        h = size * 2 + 22
        ax, ay = 24, size * 2 + 12
        surf = self._build(
            ("cry_ice", size), (w, h), (ax, ay),
            lambda s: D._draw_ice_crystals(s, [(ax, ay, size)]))
        return surf, ax, ay

    def dune(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 12
        h = size + 10
        ax, ay = size + 6, size // 2 + 2
        surf = self._build(
            ("dune", size), (w, h), (ax, ay),
            lambda s: D._draw_sand_dunes(s, [(ax, ay, size, False)]))
        return surf, ax, ay

    def snow_drift(self, size):
        from map_components.decoration_renderer import DecorationRenderer as D
        w = size * 2 + 12
        h = size + 10
        ax, ay = size + 6, (size + 10) // 2
        surf = self._build(
            ("snow", size), (w, h), (ax, ay),
            lambda s: D._draw_snow_drifts(s, [(ax, ay, size)]))
        return surf, ax, ay

    # ── Toko (bangunan dirender sekali jadi sprite besar) ──

    def shop(self, kind):
        from map_components.shop_renderer import ShopRenderer
        w, h = 96, 108
        ax, ay = 48, 68
        surf = self._build(
            ("shop", kind), (w, h), (ax, ay),
            lambda s: ShopRenderer._draw_building(s, (ax, ay), kind))
        return surf, ax, ay

    # ── DRAW ALL (mirror DecorationRenderer.draw_all) ──

    def draw_all(self, surf, mr):
        theme = mr.theme

        def blit_at(surf_ax, ax, ay, x, y):
            surf.blit(surf_ax, (x - ax, y - ay))

        if theme.get("has_ancient_ruins"):
            for x, y, variant in mr.ancient_ruins:
                s, ax, ay = self.ruin(variant)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_rocks_mossy"):
            for x, y, size, has_moss in mr.rocks_mossy:
                if has_moss:
                    s, ax, ay = self.rock(size)
                else:
                    s, ax, ay = self.rock_nomoss(size)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_gravestones"):
            s, ax, ay = self.gravestone()
            for x, y in mr.gravestones:
                blit_at(s, ax, ay, x, y)
        if theme.get("has_bones"):
            for x, y, btype in mr.bones:
                s, ax, ay = self.bone(btype)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_dark_bushes"):
            for x, y, size in mr.dark_bushes:
                s, ax, ay = self.bush(size)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_spike_traps"):
            s, ax, ay = self.spike()
            for x, y in mr.spike_traps:
                blit_at(s, ax, ay, x, y)

        # Dead/frozen trees
        if theme.get("has_frozen_trees"):
            for x, y, size in mr.dead_trees:
                s, ax, ay = self.frozen_tree(size)
                blit_at(s, ax, ay, x, y)
        elif theme.get("has_dead_trees"):
            for x, y, size in mr.dead_trees:
                s, ax, ay = self.dead_tree(size)
                blit_at(s, ax, ay, x, y)

        if theme.get("has_dark_trees"):
            for x, y, size, variant in mr.dark_trees:
                s, ax, ay = self.dark_tree(size, variant)
                blit_at(s, ax, ay, x, y)

        if theme.get("has_mushrooms_dark"):
            for x, y, color in mr.mushrooms_dark:
                s, ax, ay = self.mushroom(color)
                blit_at(s, ax, ay, x, y)

        if theme.get("has_crystals_blue"):
            for x, y, size in mr.crystals_blue:
                s, ax, ay = self.crystal_blue(size)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_crystals_red"):
            if theme["name"] == "Desert":
                for x, y, size in mr.crystals_red:
                    s, ax, ay = self.crystal_amber(size)
                    blit_at(s, ax, ay, x, y)
            else:
                for x, y, size in mr.crystals_red:
                    s, ax, ay = self.crystal_red(size)
                    blit_at(s, ax, ay, x, y)

        if theme.get("has_glow_flowers"):
            for x, y, color in mr.glow_flowers:
                s, ax, ay = self.flower(color)
                blit_at(s, ax, ay, x, y)

        # ── Theme-specific ──
        if theme.get("has_cactus"):
            for x, y, size, variant in mr.dark_trees:
                s, ax, ay = self.cactus(size, variant)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_palm_trees"):
            for x, y, size in mr.dark_bushes:
                s, ax, ay = self.palm(size)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_sand_dunes"):
            for x, y, size, _has in mr.rocks_mossy[:12]:
                s, ax, ay = self.dune(size)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_ice_crystals"):
            for x, y, size in mr.crystals_blue[:8]:
                s, ax, ay = self.ice_crystal(size)
                blit_at(s, ax, ay, x, y)
        if theme.get("has_snow_drifts"):
            for x, y, size in mr.dark_bushes:
                s, ax, ay = self.snow_drift(size)
                blit_at(s, ax, ay, x, y)

        # True-boss dressing: sedikit item, digambar langsung
        # (memakai fungsi asli agar art boss tetap persis).
        from map_components.decoration_renderer import DecorationRenderer
        DecorationRenderer._draw_true_boss_decorations(surf, mr)

    def blit_shops(self, surf, mr):
        s, ax, ay = self.shop("item")
        sx, sy = mr.radiant_shop_pos
        surf.blit(s, (sx - ax, sy - ay))
        s, ax, ay = self.shop("hero")
        dx, dy = mr.dire_shop_pos
        surf.blit(s, (dx - ax, dy - ay))
