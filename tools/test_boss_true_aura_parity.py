#!/usr/bin/env python3
"""Regresi: aura TRUE BOSS Godot harus sama profil alpha-nya dengan pygame.

Sumber kebenaran: ``bosses/base_boss.py::Boss._draw_true_boss_aura`` (:6351)

    pulse  = sin(self.pulse) * 0.3 + 0.7
    aura_r = radius + 15
    for r_off in range(aura_r, aura_r - 15, -2):
        alpha = max(0, min(255, int((aura_r - r_off) * 5 * pulse)))
        pygame.draw.circle(aura_surf, (*color, alpha), center, r_off)

JEBAKAN yang dikunci test ini: ``pygame.draw.circle`` TIDAK mem-blend, ia
MENIMPA piksel di surface SRCALPHA. Delapan lingkaran itu menghasilkan gradien
BERPITA (tiap piksel memakai alpha lingkaran terkecil yang menutupinya), bukan
tumpukan yang makin pekat. ``CanvasItem.draw_circle()`` Godot sebaliknya
MEM-BLEND — port naif "8 draw_circle" membuat pusat aura ~3x lebih pekat.

Sejak FASE 32 aura ini tidak lagi digambar ``Boss._draw()`` langsung,
melainkan dibangun ``godot/scripts/render/BossOverlay.gd`` sebagai op ``band``
(anulus alpha rata: ``inner < d <= outer``) yang diraster ``draw_arc`` lebar
``outer - inner`` — jadi pita-pita itu tidak pernah saling menimpa. Test ini:

  1. membaca konstanta aura langsung dari BossOverlay.gd (bukan menyalinnya),
  2. memodelkan profil alpha hasil gambar Godot (band -> draw_arc),
  3. membandingkannya dengan surface pygame yang sungguh-sungguh dirender,
  4. memastikan model "8 draw_circle bertumpuk" MEMANG gagal — supaya tidak
     ada yang "menyederhanakan" kode Godot kembali ke sana,
  5. memeriksa struktur BossOverlay.gd: pita dipakai untuk kedua aura ISI
     (ability + true boss) dan aura true boss hanya menyala untuk kelas true.

Oracle lengkap seluruh lapisan overlay (termasuk piksel round-trip per
skenario) ada di ``tools/test_boss_draw_parity.py``.

Jalankan: python3 tools/test_boss_true_aura_parity.py
"""
import math
import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERLAY_GD = os.path.join(ROOT, "godot", "scripts", "render", "BossOverlay.gd")
BOSS_GD = os.path.join(ROOT, "godot", "scenes", "boss", "Boss.gd")

_pass = 0
_fail = 0


def check(name, cond, detail=""):
    global _pass, _fail
    if cond:
        _pass += 1
        print("  OK   %s" % name)
    else:
        _fail += 1
        print("  FAIL %s %s" % (name, ("- " + detail) if detail else ""))


def gd_const(src, name, cast=float):
    m = re.search(r"^const %s\s*:?[^=\n]*=\s*([0-9.]+)" % re.escape(name),
                  src, re.M)
    if not m:
        raise AssertionError("konstanta %s tidak ada di BossOverlay.gd" % name)
    return cast(m.group(1))


def pygame_profile(radius, pulse, color=(140, 100, 220)):
    """Profil alpha pygame di sepanjang sumbu x dari pusat (render asli)."""
    aura_r = radius + 15
    surf = pygame.Surface((aura_r * 3, aura_r * 3), pygame.SRCALPHA)
    for r_off in range(aura_r, aura_r - 15, -2):
        a = max(0, min(255, int((aura_r - r_off) * 5 * pulse)))
        if a > 0:
            pygame.draw.circle(surf, (*color, a),
                               (aura_r * 3 // 2, aura_r * 3 // 2), r_off)
    c = aura_r * 3 // 2
    return [surf.get_at((c + d, c))[3] for d in range(aura_r + 3)]


def godot_profile(radius, pulse, rings, step, margin, alpha_step):
    """Model BossOverlay.gd: `filled_aura_bands` -> op band -> draw_arc.

    Cermin ``radial_profile``: pita menutup ``inner < d <= outer``, dan pita
    paling dalam (``ri = 0``) menutup pusat. Tidak ada penumpukan alpha.
    """
    aura_r = radius + margin
    prof = [0] * (int(aura_r) + 3)
    radii, alphas = [], []
    for i in range(1, int(rings)):
        r_off = aura_r - int(step * float(i))
        if r_off <= 0:
            continue
        a = max(0, min(255, int((aura_r - r_off) * alpha_step * pulse)))
        if a <= 0:
            continue
        radii.append(r_off)
        alphas.append(a)
    for i, outer in enumerate(radii):
        inner = radii[i + 1] if i + 1 < len(radii) else 0
        for d in range(len(prof)):
            if d <= outer and (d > inner or inner <= 0):
                prof[d] = alphas[i]
    return prof


def stacked_circle_profile(radius, pulse, rings, step, margin, alpha_step):
    """Model port NAIF: 8 draw_circle Godot yang saling mem-blend."""
    aura_r = radius + margin
    prof = [0.0] * (int(aura_r) + 3)
    for i in range(int(rings)):
        r_off = aura_r - i * step
        a = (aura_r - r_off) * alpha_step * pulse / 255.0
        if a <= 0:
            continue
        for d in range(len(prof)):
            if d <= r_off:
                prof[d] = prof[d] + a * (1.0 - prof[d])
    return [int(round(x * 255)) for x in prof]


def save_shot(path, radius=26, pulse=0.7, color=(140, 100, 220)):
    """Tulis PNG perbandingan: pygame vs port naif vs port BossOverlay.gd."""
    aura_r = radius + 15
    cell = aura_r * 3
    img = pygame.Surface((cell * 3, cell + 26), pygame.SRCALPHA)
    img.fill((18, 16, 26, 255))
    profiles = [
        ("pygame (acuan)", pygame_profile(radius, pulse, color)),
        ("naif: 8 draw_circle", stacked_circle_profile(
            radius, pulse, 8, 2.0, 15.0, 5.0)),
        ("BossOverlay: pita band", godot_profile(
            radius, pulse, 8, 2.0, 15.0, 5.0)),
    ]
    font = pygame.font.SysFont(None, 16)
    for idx, (label, prof) in enumerate(profiles):
        ox = idx * cell
        cx, cy = ox + cell // 2, 26 + cell // 2
        # gambar ulang dari profil alpha (radial), supaya yang tampil benar-benar
        # angka yang diuji, bukan gambar terpisah
        for d in range(len(prof) - 1, 0, -1):
            a = prof[d]
            if a > 0:
                pygame.draw.circle(img, (*color, a), (cx, cy), d)
        # badan boss (biar terlihat aura ada DI BAWAH badan)
        pygame.draw.circle(img, (60, 45, 90, 255), (cx, cy), radius)
        pygame.draw.circle(img, (200, 180, 255, 255), (cx, cy), radius, 2)
        img.blit(font.render(label, True, (235, 235, 245)), (ox + 8, 6))
        img.blit(font.render("alpha pusat %d/255" % prof[0], True,
                             (150, 200, 150) if idx != 1 else (235, 130, 120)),
                 (ox + 8, 26 + cell - 20))
    pygame.image.save(img, path)
    print("shot -> %s" % path)


def gd_func(src, name):
    """Ambil badan satu `static func` (sampai func/komentar berikutnya)."""
    i = src.index("static func %s(" % name)
    j = len(src)
    for m in re.finditer(r"^static func \w+\(", src[i + 10:], re.M):
        j = min(j, i + 10 + m.start())
    return src[i:j]


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    src = open(OVERLAY_GD, encoding="utf-8").read()

    print("Konstanta aura dibaca dari godot/scripts/render/BossOverlay.gd")
    rings = int(gd_const(src, "AURA_RINGS"))
    step = gd_const(src, "AURA_STEP")
    margin = gd_const(src, "AURA_MARGIN")
    alpha_step = gd_const(src, "AURA_ALPHA_STEP")
    pulse_speed = gd_const(src, "PULSE_SPEED")

    check("AURA_RINGS = 8 (range(aura_r, aura_r-15, -2))", rings == 8, str(rings))
    check("AURA_STEP = 2", step == 2.0, str(step))
    check("AURA_MARGIN = 15 (radius + 15)", margin == 15.0, str(margin))
    check("AURA_ALPHA_STEP = 5", alpha_step == 5.0, str(alpha_step))
    check("PULSE_SPEED = 6 rad/s (0.1/frame x 60 fps)", pulse_speed == 6.0,
          str(pulse_speed))

    print("\nProfil alpha vs pygame (beberapa fase denyut & radius)")
    # Toleransi = 1 langkah alpha + 1. Dua sumber beda yang sah:
    #   * pygame.draw.circle radius r menutup d < r (bukan d <= r), jadi tepi
    #     pita bisa bergeser satu piksel;
    #   * pygame memakai int() (pemotongan), model Godot membulatkan.
    for radius in (22, 26, 30):
        for phase in (0.0, math.pi * 0.5, math.pi, math.pi * 1.5):
            pulse = math.sin(phase) * 0.3 + 0.7
            ref = pygame_profile(radius, pulse)
            got = godot_profile(radius, pulse, rings, step, margin, alpha_step)
            n = min(len(ref), len(got))
            worst = max(abs(got[d] - ref[d]) for d in range(n))
            tol = math.ceil(alpha_step * step * pulse) + 1
            check("r=%d fase=%.2f: beda <= 1 langkah (%d)" % (radius, phase, tol),
                  worst <= tol, "beda maks %d" % worst)
            check("r=%d fase=%.2f: alpha pusat sama" % (radius, phase),
                  abs(got[0] - ref[0]) <= 1, "godot %d vs pygame %d" % (got[0], ref[0]))
            check("r=%d fase=%.2f: tepi luar transparan" % (radius, phase),
                  got[n - 1] == 0 and ref[n - 1] == 0)

    print("\nPort naif (8 draw_circle bertumpuk) HARUS gagal")
    for radius in (22, 26):
        pulse = 0.7
        ref = pygame_profile(radius, pulse)
        bad = stacked_circle_profile(radius, pulse, rings, step, margin, alpha_step)
        check("r=%d: draw_circle bertumpuk jauh lebih pekat" % radius,
              bad[0] >= ref[0] * 2, "naif %d vs pygame %d" % (bad[0], ref[0]))

    print("\nStruktur BossOverlay.gd (pita, bukan tumpukan cakram)")
    bands = gd_func(src, "filled_aura_bands")
    check("filled_aura_bands menghasilkan op band", '"k": "band"' in bands)
    check("pita punya inner/outer (ri/ro)", '"ri": inner' in bands
          and '"ro": outer' in bands)
    check("kedua aura ISI memakai pita yang sama (ability + true boss)",
          "filled_aura_bands(" in gd_func(src, "ability_aura_ops")
          and "filled_aura_bands(" in gd_func(src, "true_aura_ops"))
    ex = gd_func(src, "exec")
    band_branch = ex[ex.index('"band":'):ex.index('"rect":')]
    check("band digambar draw_arc (cincin tidak menimpa)",
          "draw_arc(" in band_branch)
    check("draw_circle di cabang band hanya untuk pusat (inner <= 0)",
          band_branch.count("draw_circle(") == 1
          and "inner <= 0.0" in band_branch)
    check("aura enrage tetap cincin GARIS (ring, width 2)",
          '"k": "ring"' in gd_func(src, "enrage_aura_ops")
          and int(gd_const(src, "ENRAGE_RING_W")) == 2)
    under = gd_func(src, "underlay_ops")
    check("aura true boss hanya untuk kelas true",
          "if is_true(state):" in under
          and "true_aura_ops(state)" in under)
    check("urutan lapisan: ability -> enrage -> true -> bayangan -> debuff",
          under.index("ability_aura_ops") < under.index("enrage_aura_ops")
          < under.index("true_aura_ops") < under.index("shadow_ops")
          < under.index("debuff_ops"))
    boss_src = open(BOSS_GD, encoding="utf-8").read()
    check("Boss.gd tidak lagi menggambar aura sendiri",
          "draw_arc(" not in boss_src and "draw_circle(" not in boss_src)
    check("Boss.gd mendelegasikan overlay ke BossOverlay",
          "BossOverlay.exec(" in boss_src
          and "BossOverlay.underlay_ops(" in boss_src)

    if "--shot" in sys.argv:
        pygame.font.init()
        save_shot(os.path.join(ROOT, "tools", "boss_true_aura_parity.png"))

    print("\n%d OK, %d FAIL" % (_pass, _fail))
    return 1 if _fail else 0


if __name__ == "__main__":
    sys.exit(main())
