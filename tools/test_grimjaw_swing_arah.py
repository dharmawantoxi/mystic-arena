#!/usr/bin/env python3
"""Regresi ARAH TEBASAN basic attack Grimjaw.

Latar belakang
--------------
Basic attack Grimjaw dulu terbaca sebagai ayunan DARI BAWAH KE ATAS:

* sudut pedang justru MEMBESAR (-1.55 -> +1.35 rad) sehingga ujung
  pedang lewat BAWAH badan dan NAIK lagi di akhir ayunan;
* crescent api digambar penuh sejak awal tebasan dengan titik paling
  terang di ujung ATAS-nya (kepala di atas, ekor memudar ke bawah),
  padahal kepala crescent itulah yang dibaca mata sebagai "posisi
  pedang sekarang".

Sesudah perbaikan, pedang diputar ke arah yang BERKURANG
(ATTACK_ARC_START -2.30 -> ATTACK_ARC_END -5.35 rad): diangkat ke
atas-belakang kepala, lewat atas, lalu menebas TURUN ke depan-bawah.
Crescent api pun mengikuti jalur yang sama - kepalanya menempel di
ujung pedang dan ekornya memudar ke atas.

Yang diuji di sini
------------------
1. Geometri pedang  : puncak ayunan ada di paruh PERTAMA tebasan, lalu
                      ujung pedang TURUN terus sampai mendarat di
                      depan-bawah.
2. Crescent api     : kepala + centroid crescent ikut TURUN, bukan naik.
3. Timeline bersama : sudut pedang dan sudut crescent diambil dari
                      konstanta yang sama, jadi keduanya tidak mungkin
                      lagi bergerak berlawanan arah.

Jalankan:  python3 tools/test_grimjaw_swing_arah.py
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame                                             # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
from heroes._bundle import _NS_grimjaw as G               # noqa: E402

FACING = 1
CX, CY = 220, 220
N = 40

# Fallback ke timeline lama kalau konstanta baru belum ada, supaya test
# ini GAGAL karena geometri ayunan (bukan sekadar AttributeError) saat
# kode belum diperbaiki.
WINDUP_END = float(getattr(G, "ATTACK_WINDUP_END", 0.25))
SWING_END = float(getattr(G, "ATTACK_SWING_END", 0.70))


def _swing_samples():
    """(progress, ujung_pedang) di sepanjang fase tebasan."""
    out = []
    p0, p1 = WINDUP_END, SWING_END
    for i in range(N + 1):
        p = p0 + (p1 - p0) * i / N
        out.append((p, G._blade_tip_local(0.0, "attack", p)))
    return out


def _arc_centroid(progress, crit=False):
    """Centroid (_alpha-weighted) layer crescent api saja."""
    surf = pygame.Surface((440, 440), pygame.SRCALPHA)
    G._draw_fire_slash_arc(surf, CX, CY, FACING, progress, crit)
    rect = surf.get_bounding_rect(min_alpha=1)
    if rect.width == 0:
        return None, None
    total = 0
    sy = 0.0
    for y in range(rect.top, rect.bottom):
        for x in range(rect.left, rect.right):
            a = surf.get_at((x, y)).a
            if a:
                total += a
                sy += y * a
    if not total:
        return None, None
    return sy / total - CY, rect


def test_pedang_menebas_dari_atas_ke_bawah():
    """Ujung pedang memuncak di awal tebasan lalu TURUN sampai mendarat."""
    samples = _swing_samples()
    ys = [tip[1] for _, tip in samples]
    apex = min(range(len(ys)), key=lambda i: ys[i])
    apex_pos = apex / float(N)

    # Puncak ayunan (pedang paling tinggi) harus di paruh PERTAMA tebasan.
    assert apex_pos <= 0.5, f"puncak ayunan terlambat: {apex_pos:.2f}"

    # Dari puncak sampai mendarat, ujung pedang harus TURUN terus
    # (y layar membesar) - tidak boleh naik lagi seperti versi lama.
    for i in range(apex, N):
        assert ys[i + 1] >= ys[i] - 1, (
            f"ujung pedang naik lagi di progress {samples[i][0]:.2f}: "
            f"y {ys[i]} -> {ys[i + 1]}")

    # Pendaratan: jauh di bawah puncak, di depan, dan di bawah pusat badan.
    land = G._blade_tip_local(0.0, "attack", SWING_END)
    assert land[1] - ys[apex] >= 40, f"tebasan terlalu dangkal: {land[1] - ys[apex]}"
    assert land[0] > 45, f"pedang tidak mendarat di depan: x={land[0]}"
    assert land[1] > 15, f"pedang tidak mendarat di bawah: y={land[1]}"


def test_crescent_api_mengikuti_pedang():
    """Crescent api ikut TURUN: centroid & tepi bawahnya turun terus."""
    early = WINDUP_END + 0.05
    mid = (WINDUP_END + SWING_END) / 2.0
    late = SWING_END

    c_early, r_early = _arc_centroid(early)
    c_mid, _ = _arc_centroid(mid)
    c_late, r_late = _arc_centroid(late)
    assert None not in (c_early, c_mid, c_late), "crescent tidak tergambar"

    # Centroid crescent TURUN (y membesar) saat tebasan berlangsung.
    assert c_late > c_mid + 20, (
        f"crescent tidak turun: centroid {c_mid:.1f} -> {c_late:.1f}")

    # Tepi bawah crescent merambah ke bawah mengikuti pedang.
    assert r_late.bottom - r_early.bottom >= 40, (
        f"tepi bawah crescent tidak turun: {r_early.bottom} -> "
        f"{r_late.bottom}")

    # Tebasan menyapu lebih dari seperempat putaran penuh.
    assert abs(G.ATTACK_ARC_SWEEP) > math.pi / 2, G.ATTACK_ARC_SWEEP


def test_timeline_rig_dan_fx_sama():
    """Sudut pedang dan sudut crescent berasal dari konstanta yang sama."""
    a_blade = G._blade_angle(0.0, "attack", SWING_END)
    a_arc = G.ATTACK_ARC_END
    assert abs(math.sin(a_blade) - math.sin(a_arc)) < 1e-6
    assert abs(math.cos(a_blade) - math.cos(a_arc)) < 1e-6

    # Arah putaran SELALU negatif: pedang menebas, bukan mengangkat.
    assert G.ATTACK_ARC_SWEEP < 0, G.ATTACK_ARC_SWEEP
    assert G.ATTACK_WINDUP_END < G.ATTACK_SWING_END < 1.0

    # Recovery tidak mengayun balik ke atas (penyebab "bawah ke atas").
    prev_tip = G._blade_tip_local(0.0, "attack", SWING_END)[1]
    for i in range(1, 11):
        p = SWING_END + (1.0 - SWING_END) * i / 10.0
        tip = G._blade_tip_local(0.0, "attack", p)[1]
        assert tip >= prev_tip - 2, f"recovery mengangkat pedang di p={p:.2f}"
        prev_tip = tip


if __name__ == "__main__":
    test_pedang_menebas_dari_atas_ke_bawah()
    test_crescent_api_mengikuti_pedang()
    test_timeline_rig_dan_fx_sama()
    land = G._blade_tip_local(0.0, "attack", SWING_END)
    apex = min(_swing_samples(), key=lambda s: s[1][1])
    print("OK - tebasan Grimjaw ATAS -> BAWAH tervalidasi")
    print(f"     puncak ayunan : y={apex[1][1]} (progress {apex[0]:.2f})")
    print(f"     pendaratan    : x={land[0]}, y={land[1]} "
          f"(depan-bawah, turun {land[1] - apex[1][1]} px)")
