#!/usr/bin/env python3
"""Regresi untuk pass cahaya bersama (lighting.py).

Pass ini dipasang di SATU choke point (heroes._finish_hd_sprite) supaya
berlaku untuk semua hero, dan dipasang sendiri oleh renderer boss yang
menggambar langsung ke layar (saat ini Gornak). Yang diuji:

  1. pass benar-benar mengubah sprite (bukan no-op karena guard/exception)
     dan perubahannya TERARAH: sisi kiri-atas lebih terang dari kanan-bawah;
  2. alpha sprite tidak boleh berubah (outline HD & colorkey mobile
     bergantung padanya) dan ukuran/pad anchor tetap;
  3. tidak ada rim DOBEL di jalur hero (boss-only pass harus dilewati saat
     heroes/__init__ sudah mengerjakan pass yang sama);
  4. cache gradien tidak tumbuh tanpa batas;
  5. biaya pass masih masuk budget mobile;
  6. kill switch (HD_LIGHTING_ENABLED / lighting di-import gagal) Aman.

Jalankan:  python3 tools/test_hero_lighting.py
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
import _core                                          # noqa: F401 (shim)
import heroes
import lighting
from heroes import _ProbeEntity, render_hero, clear_hero_sprite_cache

FAMILY = ("kaizen", "thorne", "sylara", "zephyr", "grimjaw", "vex", "gornak")


def hero_sprite(name, size=340):
    c = size // 2
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    h = _ProbeEntity(name, c, c)
    h.pulse = 1.35
    h.direction = 1
    h.team = "blue"
    clear_hero_sprite_cache()
    render_hero(name, canvas, h, c, c)
    return canvas


def lum(px):
    return 0.299 * px.r + 0.587 * px.g + 0.114 * px.b


def corner_deltas(before, after):
    """Delta luminance rata-rata pass cahaya di dua sudut (cahaya, bayangan).

    Diukur sebagai SELISIH sebelum/sesudah. Luminance absolut tidak membuktikan
    arah cahaya: sprite punya artnya sendiri (pedang Kaizen yang terang ada di
    kanan-bawah) dan itu menenggelamkan efek pass ~16% sepenuhnya.
    """
    box = after.get_bounding_rect(min_alpha=200)
    if box.width <= 8 or box.height <= 8:
        return 0.0, 0.0
    ax, ay = abs(lighting.LIGHT_DIR[0]), abs(lighting.LIGHT_DIR[1])
    span = (box.width - 1) * ax + (box.height - 1) * ay
    if span <= 0:
        return 0.0, 0.0
    lit, shade = [], []
    for y in range(box.top, box.bottom):
        for x in range(box.left, box.right):
            pa, pb = before.get_at((x, y)), after.get_at((x, y))
            if pa.a < 200 or pb.a < 200:
                continue
            t = 1.0 - (((x - box.left) * ax + (y - box.top) * ay) / span)
            d = lum(pb) - lum(pa)
            # Pita lebar (0.62 / 0.38), bukan ujung ekstrem: sprite ini
            # serong (pedang, jubah, cincin tanah), jadi sudut bbox sering
            # kosong atau justru cuma piksel outline - itu bikin uji
            # "gelap di kanan-bawah" gagal untuk figur seperti Thorne.
            if t > 0.62:
                lit.append(d)
            elif t < 0.38:
                shade.append(d)
    if not lit or not shade:
        return 0.0, 0.0
    return sum(lit) / len(lit), sum(shade) / len(shade)

def test_lighting_changes_every_family_sprite():
    assert heroes.HD_LIGHTING_ENABLED is True
    heroes.HD_LIGHTING_ENABLED = False
    off = {n: hero_sprite(n) for n in FAMILY}
    heroes.HD_LIGHTING_ENABLED = True
    on = {n: hero_sprite(n) for n in FAMILY}

    for n in FAMILY:
        a, b = off[n], on[n]
        assert a.get_size() == b.get_size(), "ukuran sprite berubah"
        changed = 0
        total = 0
        for y in range(0, a.get_height(), 2):
            for x in range(0, a.get_width(), 2):
                pa, pb = a.get_at((x, y)), b.get_at((x, y))
                if pa.a < 100:
                    continue
                total += 1
                if abs(lum(pa) - lum(pb)) > 3 or pa.a != pb.a:
                    changed += 1
        assert total > 200, n
        assert 0.10 < changed / total < 0.95, \
            f"{n}: pass cahaya mengubah {changed}/{total} px - " \
            "terlalu kecil (tidak terpasang) atau terlalu besar (merusak)"


def test_light_is_directional_and_alpha_safe():
    """Cahaya harus PUNYA ARAH (terang di kiri-atas, gelap di kanan-bawah),
    dan alpha tidak boleh disentuh (outline HD & colorkey mobile
    bergantung padanya)."""
    heroes.HD_LIGHTING_ENABLED = False
    off = {n: hero_sprite(n) for n in FAMILY}
    heroes.HD_LIGHTING_ENABLED = True
    for n in FAMILY:
        lit_d, shade_d = corner_deltas(off[n], hero_sprite(n))
        # Relatif, bukan mutlak: yang dijanjikan pass ini adalah sisi
        # CAHAYA lebih terang daripada sisi BAYANGAN (bukan bahwa tiap sisi
        # wajib naik/turun - band rim juga menambah terang di tepi).
        assert lit_d > shade_d + 2.0, (
            f"{n}: cahaya tidak terarah (lit {lit_d:+.1f} vs shade {shade_d:+.1f})")

    # alpha identik sebelum/sesudah pass
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(surf, (200, 120, 60, 255), (8, 8, 48, 48))
    pygame.draw.circle(surf, (90, 40, 120, 180), (32, 32), 20)
    before_bytes = pygame.image.tobytes(surf, "RGBA")
    alphas = [surf.get_at((x, y)).a for y in range(64) for x in range(64)]
    lighting.apply(surf)
    after_alphas = [surf.get_at((x, y)).a for y in range(64) for x in range(64)]
    assert alphas == after_alphas, "pass cahaya mengubah alpha sprite"
    assert pygame.image.tobytes(surf, "RGBA") != before_bytes


def test_hero_path_gets_exactly_one_lighting_pass():
    """Gornak TIDAK boleh dapat rim dua kali di lane, dan tidak boleh nol
    di Hero Shop (HeroPortraits tidak memanggil _finish_hd_sprite)."""
    import bosses.level1 as L
    from types import SimpleNamespace

    calls = {"n": 0}
    real = lighting.apply

    def counting(surface, *a, **k):
        calls["n"] += 1
        return real(surface, *a, **k)

    lighting.apply = counting
    lighting.apply_to_rig.__globals__["apply"] = counting
    try:
        # (a) lane hero: pass hanya dari _finish_hd_sprite
        calls["n"] = 0
        hero_sprite("gornak")
        lane_calls = calls["n"]
        # (b) boss 1x: pass hanya dari renderer boss
        calls["n"] = 0
        canvas = pygame.Surface((320, 320), pygame.SRCALPHA)
        boss = SimpleNamespace(boss_type="gornak", boss_class="mini",
                               x=160.0, y=160.0, direction=1, facing=1,
                               pulse=1.3, timer=0, attack_cooldown=38,
                               active_skill=None, active_skill_timer=0,
                               target=None, hurt_flash_timer=0, alive=True,
                               radius=30, is_retreating=False)
        L.draw_gornak(canvas, boss, 160, 160)
        boss_calls = calls["n"]
        # (c) Hero Shop portrait: tidak ada _finish_hd_sprite sama sekali
        calls["n"] = 0
        shop = pygame.Surface((160, 160), pygame.SRCALPHA)
        fake = SimpleNamespace(boss_type="gornak", boss_class="mini",
                               x=80.0, y=90.0, direction=1, facing=1,
                               pulse=0.5, timer=0, attack_cooldown=38,
                               active_skill=None, active_skill_timer=0,
                               target=None, hurt_flash_timer=0, alive=True,
                               radius=16, is_retreating=False,
                               _portrait_hd=True)
        L.draw_gornak(shop, fake, 80, 90)
        shop_calls = calls["n"]
    finally:
        lighting.apply = real
        lighting.apply_to_rig.__globals__["apply"] = real

    assert boss_calls >= 1, "jalur boss tidak menjalankan pass cahaya"
    assert shop_calls >= 1, "Hero Shop tidak menjalankan pass cahaya"
    assert lane_calls >= 1, "jalur lane tidak menjalankan pass cahaya"
    # Yang mencegah rim DOBEL: renderer boss menandai "ini canvas hero"
    # dari keberadaan _render_scale, lalu melewati pass-nya sendiri.
    flags = []
    real_apply = lighting.apply_to_rig

    def spy(surface, *a, **k):
        import bosses.level1 as _L
        flags.append(_L._NS_gornak._HERO_LANE.v)
        return real_apply(surface, *a, **k)

    lighting.apply_to_rig = spy
    try:
        hero_sprite("gornak")                      # lane: pass dari HD saja
        lane_flag = flags[-1] if flags else None
        flags.clear()
        canvas = pygame.Surface((320, 320), pygame.SRCALPHA)
        from types import SimpleNamespace
        L.draw_gornak(canvas, SimpleNamespace(
            boss_type="gornak", boss_class="mini", x=160.0, y=160.0,
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=38,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=30,
            is_retreating=False), 160, 160)
        boss_flag = flags[-1] if flags else None
    finally:
        lighting.apply_to_rig = real_apply
    assert lane_flag is True, ("jalur lane tidak ditandai sebagai hero-path "
                              "-> rim bisa dobel 2 px")
    assert boss_flag is False, "jalur boss malah dilewati -> boss tanpa cahaya"
    # di lane, renderer boss harus MENYERAHKE pass ke _finish_hd_sprite:
    # dua rim 1 px bertumpuk = karakter berbingkai gelap 2 px.
    hero_lane = hero_sprite("gornak")
    heroes.HD_LIGHTING_ENABLED = False
    clear_hero_sprite_cache()
    plain = hero_sprite("gornak")
    heroes.HD_LIGHTING_ENABLED = True
    diff = sum(1 for y in range(0, hero_lane.get_height(), 3)
               for x in range(0, hero_lane.get_width(), 3)
               if hero_lane.get_at((x, y)).a > 200
               and abs(lum(hero_lane.get_at((x, y)))
                       - lum(plain.get_at((x, y)))) > 3)
    assert diff > 60, "lane hero tidak terlihat berubah - pass mati?"


def test_gradient_cache_is_bounded_and_cheap():
    lighting.reset_gradient_cache()
    surf = pygame.Surface((80, 80), pygame.SRCALPHA)
    pygame.draw.rect(surf, (180, 140, 90, 255), (10, 10, 60, 60))
    for _ in range(300):
        lighting.apply(surf)
    assert len(lighting._SIZE_CACHE) <= 64, len(lighting._SIZE_CACHE)
    t0 = time.perf_counter()
    for _ in range(400):
        lighting.apply(surf)
    ms = (time.perf_counter() - t0) / 400 * 1000
    # 80x80: satu blit MULT + satu ADD + dua contour mask. Budget < 0,35 ms.
    assert ms < 0.35, f"lighting.apply {ms:.3f} ms - kemahalan per frame"


def test_kill_switch_and_missing_module():
    """Kualitas boleh dimatikan di HP低端 tanpa membuat render gagal."""
    real = heroes.HD_LIGHTING_ENABLED
    try:
        heroes.HD_LIGHTING_ENABLED = False
        sprite = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(sprite, (150, 110, 70, 255), (8, 8, 54, 54))
        out, pad = heroes._finish_hd_sprite(sprite, "blue")
        assert pad == 1 and out.get_width() == 72
        # modul hilang -> apply_to_rig diam-diam mengembalikan sprite utuh
        saved = lighting._lighting if hasattr(lighting, "_lighting") else None
        import bosses.level1 as L
        old = L._lighting
        try:
            L._lighting = None
            c = pygame.Surface((240, 240), pygame.SRCALPHA)
            from types import SimpleNamespace
            b = SimpleNamespace(boss_type="gornak", boss_class="mini",
                                x=120.0, y=120.0, direction=1, facing=1,
                                pulse=1.3, timer=0, attack_cooldown=38,
                                active_skill=None, active_skill_timer=0,
                                target=None, hurt_flash_timer=0, alive=True,
                                radius=30, is_retreating=False)
            L.draw_gornak(c, b, 120, 120)
            assert c.get_bounding_rect(min_alpha=100).height > 60, \
                "tanpa lighting.py boss harus tetap tergambar"
        finally:
            L._lighting = old
            if saved is not None:
                lighting._lighting = saved
    finally:
        heroes.HD_LIGHTING_ENABLED = real


if __name__ == "__main__":
    test_lighting_changes_every_family_sprite()
    test_light_is_directional_and_alpha_safe()
    test_hero_path_gets_exactly_one_lighting_pass()
    test_gradient_cache_is_bounded_and_cheap()
    test_kill_switch_and_missing_module()
    print("OK - pass cahaya: terpasang di 7 hero, terarah, alpha & anchor "
          "utuh, tidak dobel di lane, cache terbatas, budget ok")
