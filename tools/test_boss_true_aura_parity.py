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

Karena itu ``godot/scenes/boss/Boss.gd::_draw()`` memakai 1 cakram inti +
6 cincin ``draw_arc`` yang tidak saling menimpa. Test ini:

  1. membaca konstanta aura langsung dari Boss.gd (bukan menyalinnya),
  2. memodelkan profil alpha hasil gambar Godot,
  3. membandingkannya dengan surface pygame yang sungguh-sungguh dirender,
  4. memastikan model "8 draw_circle bertumpuk" MEMANG gagal — supaya tidak
     ada yang "menyederhanakan" kode Godot kembali ke sana.

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
    m = re.search(r"^const %s\s*:?=\s*([0-9.]+)" % re.escape(name), src, re.M)
    if not m:
        raise AssertionError("konstanta %s tidak ada di Boss.gd" % name)
    return cast(m.group(1))


def pygame_profile(radius, pulse, color=(140, 100, 220)):
    """Profil alpha pygame di sepanjang sumbu x dari pusat."""
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
    """Model gambar Boss.gd: cakram inti + cincin draw_arc (tidak menimpa)."""
    aura_r = radius + margin
    prof = [0.0] * (int(aura_r) + 3)
    inner_r = aura_r - (rings - 1) * step
    inner_a = (rings - 1) * step * alpha_step * pulse / 255.0
    for d in range(len(prof)):
        if d <= inner_r:
            prof[d] = inner_a
    for i in range(1, rings - 1):
        r_off = aura_r - i * step
        a = (aura_r - r_off) * alpha_step * pulse / 255.0
        for d in range(len(prof)):
            if r_off - step < d <= r_off:
                prof[d] = a
    return [round(x * 255) for x in prof]


def stacked_circle_profile(radius, pulse, rings, step, margin, alpha_step):
    """Model port NAIF: 8 draw_circle Godot yang saling mem-blend."""
    aura_r = radius + margin
    prof = [0.0] * (int(aura_r) + 3)
    for i in range(rings):
        r_off = aura_r - i * step
        a = (aura_r - r_off) * alpha_step * pulse / 255.0
        if a <= 0:
            continue
        for d in range(len(prof)):
            if d <= r_off:
                prof[d] = prof[d] + a * (1.0 - prof[d])
    return [round(x * 255) for x in prof]


def save_shot(path, radius=26, pulse=0.7, color=(140, 100, 220)):
    """Tulis PNG perbandingan: pygame vs port naif vs port Boss.gd."""
    aura_r = radius + 15
    cell = aura_r * 3
    img = pygame.Surface((cell * 3, cell + 26), pygame.SRCALPHA)
    img.fill((18, 16, 26, 255))
    profiles = [
        ("pygame (acuan)", pygame_profile(radius, pulse, color)),
        ("naif: 8 draw_circle", stacked_circle_profile(
            radius, pulse, 8, 2.0, 15.0, 5.0)),
        ("Boss.gd: cakram+cincin", godot_profile(
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


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    src = open(BOSS_GD, encoding="utf-8").read()

    print("Konstanta aura dibaca dari godot/scenes/boss/Boss.gd")
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
    #   * pygame.draw.circle radius r menutup d < r (bukan d <= r), jadi pita
    #     bisa bergeser satu piksel;
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

    print("\nKode Boss.gd memakai draw_arc, bukan tumpukan draw_circle")
    draw_body = src[src.index("func _draw() -> void:"):]
    draw_body = draw_body[:draw_body.index("\nstatic func ")]
    check("ada draw_arc (cincin tidak menimpa)", "draw_arc(" in draw_body)
    check("draw_circle dipakai maksimal 1x (cakram inti)",
          draw_body.count("draw_circle(") <= 1,
          "%d kali" % draw_body.count("draw_circle("))
    check("hanya untuk boss_class true", 'boss_class != "true"' in draw_body)

    if "--shot" in sys.argv:
        pygame.font.init()
        save_shot(os.path.join(ROOT, "tools", "boss_true_aura_parity.png"))

    print("\n%d OK, %d FAIL" % (_pass, _fail))
    return 1 if _fail else 0


if __name__ == "__main__":
    sys.exit(main())
