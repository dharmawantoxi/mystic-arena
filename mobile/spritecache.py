# ================================
# mobile/spritecache.py
# Cache sprite unit (minion) - optimasi terbesar untuk gelombang ramai
#
# MASALAH
#   Tiap minion digambar ULANG DARI NOL setiap frame: puluhan
#   pygame.draw.* per unit. 4 minion saja = +3,5 ms/frame di PC;
#   satu gelombang 20 minion bisa 15-20 ms di PC dan 3-4x lipat di HP.
#
# IDE
#   Renderer minion HANYA membaca atribut lokal (radius, direction,
#   walk_cycle, attack_anim_timer, hp, dst) - TIDAK membaca posisi
#   dunia. Jadi hasil gambarnya bisa dipakai ulang: unit dengan
#   kondisi yang sama menghasilkan gambar yang sama persis.
#
#   Kunci cache dibulatkan (anim_time dibagi ANIM_BUCKET) sehingga:
#     - unit sejenis dengan pose sama -> 1 render dipakai bersama
#     - pose diperbarui tiap ANIM_BUCKET frame (default 2)
#
# HASIL PENGUKURAN (PENTING - BACA DULU)
#   Kebenaran : LULUS. tools/test_spritecache.py membuktikan hasil
#               lewat cache IDENTIK piksel-per-piksel dengan gambar
#               langsung untuk 80 kombinasi tipe/tim/arah/gerak.
#   Kecepatan : TIDAK menguntungkan untuk minion.
#                 10 minion : 0,15 ms tanpa cache | 0,31 ms dengan
#                 30 minion : 0,33 ms tanpa cache | 0,66 ms dengan
#                 60 minion : 0,66 ms tanpa cache | 1,07 ms dengan
#               Renderer minion ternyata sudah murah (~11 mikrodetik
#               per unit); alokasi surface + blit tambahan justru
#               lebih mahal daripada menggambar ulang.
#
#   => Karena itu Quality.sprite_cache = False secara default.
#      Modul ini dipertahankan karena berguna untuk entitas yang
#      JAUH lebih mahal per unit (mis. sprite hero/boss bila nanti
#      dibuat versi yang tidak bergantung posisi dunia), dan sebagai
#      alat ukur. Aktifkan dengan MYSTIC_SPRITE_CACHE=1 lalu ukur
#      sendiri dengan tools/bench_minions.py.
# ================================

import os
from collections import OrderedDict

import pygame

from mobile.perf import Quality

ANIM_BUCKET = 2          # berapa frame satu pose dipakai ulang
MAX_ENTRIES = 320        # batas jumlah sprite tersimpan
HP_BUCKETS = 8

_cache = OrderedDict()
_stats = {"hit": 0, "miss": 0, "bypass": 0, "evict": 0}


def enabled():
    env = os.environ.get("MYSTIC_SPRITE_CACHE")
    if env == "1":
        return True
    if env == "0":
        return False
    # Quality.sprite_cache diisi apply_device_profile() berdasarkan
    # hasil ukur colorkey vs alpha DI PERANGKAT ITU SENDIRI.
    return bool(getattr(Quality, "sprite_cache", False))


def stats():
    out = dict(_stats)
    out["entries"] = len(_cache)
    total = out["hit"] + out["miss"]
    out["hit_rate"] = (out["hit"] / total) if total else 0.0
    return out


def clear():
    _cache.clear()


def _minion_key(minion_type, m):
    """Semua atribut yang MEMENGARUHI gambar harus masuk kunci."""
    hp_max = getattr(m, "max_hp", 1) or 1
    return (
        minion_type,
        getattr(m, "team", ""),
        int(getattr(m, "nexus_level", 1)),
        int(getattr(m, "radius", 10)),
        int(getattr(m, "direction", 1)),
        bool(getattr(m, "is_moving", False)),
        int(getattr(m, "walk_cycle", 0)) // ANIM_BUCKET,
        int(getattr(m, "anim_time", 0)) // ANIM_BUCKET,
        int(getattr(m, "attack_anim_timer", 0)),
        int(getattr(m, "hurt_flash_timer", 0)) > 0,
        int(getattr(m, "slow_timer", 0)) > 0,
        int(getattr(m, "spawn_anim", 0)) // ANIM_BUCKET,
        int(getattr(m, "hp", 1) / hp_max * HP_BUCKETS),
        len(getattr(m, "slash_effects", ()) or ()),
    )


def _bbox(radius):
    """Kotak gambar yang cukup longgar untuk senjata, aura, dan HP bar."""
    r = max(6, int(radius))
    left = 3 * r + 26
    right = 3 * r + 26
    top = 4 * r + 46
    bottom = 2 * r + 26
    return left, right, top, bottom


def render_minion_cached(minion_type, renderer, surface, minion, x, y):
    """
    Gambar minion lewat cache. Kembalikan True kalau tertangani,
    False kalau pemanggil harus menggambar seperti biasa.
    """
    if not enabled():
        _stats["bypass"] += 1
        return False

    try:
        key = _minion_key(minion_type, minion)
    except Exception:
        _stats["bypass"] += 1
        return False

    entry = _cache.get(key)
    if entry is not None:
        _cache.move_to_end(key)
        sprite, off_x, off_y = entry
        _stats["hit"] += 1
        surface.blit(sprite, (x - off_x, y - off_y))
        return True

    left, right, top, bottom = _bbox(getattr(minion, "radius", 10))
    width = left + right
    height = top + bottom

    sprite = pygame.Surface((width, height), pygame.SRCALPHA)
    try:
        renderer(sprite, minion, left, top)
    except Exception:
        # Renderer tidak cocok dengan cache -> jangan pakai cache lagi
        _stats["bypass"] += 1
        return False

    # Di perangkat dengan alpha blit mahal, simpan sebagai sprite
    # COLORKEY: blitnya memakai jalur cepat (RLE), ~25x lebih murah
    # daripada per-piksel-alpha, dan juga lebih murah daripada
    # menggambar ulang ~370 panggilan draw per unit.
    if not Quality.cheap_alpha:
        try:
            from mobile.perf import to_colorkey_sprite
            sprite = to_colorkey_sprite(sprite)
        except Exception:
            pass

    _cache[key] = (sprite, left, top)
    _stats["miss"] += 1
    if len(_cache) > MAX_ENTRIES:
        _cache.popitem(last=False)
        _stats["evict"] += 1

    surface.blit(sprite, (x - left, y - top))
    return True
