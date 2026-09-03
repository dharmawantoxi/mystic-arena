#!/usr/bin/env python3
"""Regresi: tidak boleh ada lagi PILAR CAHAYA yang menutupi karakter.

Latar belakang
--------------
Banyak skill menggambar "kolom cahaya" vertikal 4-lapis setinggi
70-200 px yang dilabuhkan tepat di sumbu badan caster, lalu di-blit ke
lapisan DEPAN sprite. Akibatnya karakter hilang ditelan cahaya setiap
kali skill di-cast.

Kriteria yang dipakai (objektif, bisa diuji):
    Sebuah pilar DIHAPUS jika dan hanya jika ia dilabuhkan di x/y caster
    itu sendiri -- sehingga menutupi sprite.
Pilar yang dilabuhkan di tempat lain SENGAJA DIPERTAHANKAN:
totem, ring yang mengorbit, posisi target, titik tumbukan.

Efek saudara dalam blok yang sama (nova / spark star / shockwave /
cincin rune) juga dipertahankan -- yang dibuang hanya kolom cahayanya.

Test ini memindai SUMBER, bukan hasil render: ia mencari idiom gambar
"garis/rect vertikal dari `top` ke badan" yang merupakan tanda tangan
pilar. Kalau ada yang muncul lagi, test ini gagal dan menyebut
file:barisnya.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ("heroes", "bosses")

# Tanda tangan pilar: dua ujung garis dengan x IDENTIK, salah satunya
# variabel bernama top/pil/hgt (ujung atas kolom), ujung lainnya badan.
PAT_PILLAR_LINE = re.compile(
    r"\(\s*(?P<ax>[A-Za-z_]\w*)\s*,\s*(?P<atop>top|pil\w*|pil_h|hgt|height)\s*\)"
    r"\s*,\s*"
    r"\(\s*(?P=ax)\s*,\s*(?P<ay>y|cy|gy|y\s*[-+]\s*\d+)\s*\)"
)
PAT_PILLAR_LINE_REV = re.compile(
    r"\(\s*(?P<ax>[A-Za-z_]\w*)\s*,\s*(?P<ay>y|cy)\s*\)\s*,\s*"
    r"\(\s*(?P=ax)\s*,\s*(?P<atop>y\s*-\s*pil\w*|y-pil\w*)\s*\)"
)
# Rect tipis-tinggi: (x - w//2, top, w, gy - top)
PAT_PILLAR_RECT = re.compile(
    r"\(\s*\w+\s*-\s*w\s*//\s*2\s*,\s*top\s*,\s*w\s*,\s*\w+\s*-\s*top\s*\)"
)
# Helper bernama _pillar yang dipanggil dengan jangkar di badan.
PAT_PILLAR_HELPER = re.compile(
    r"self\._pillar\s*\(\s*surface\s*,\s*x\s*,\s*y"
)

PATTERNS = (
    ("garis vertikal top->badan", PAT_PILLAR_LINE),
    ("garis vertikal badan->y-pil", PAT_PILLAR_LINE_REV),
    ("rect tipis-tinggi", PAT_PILLAR_RECT),
    ("pemanggilan self._pillar di (x, y)", PAT_PILLAR_HELPER),
)

FAILURES = []


def _scan(path):
    rel = os.path.relpath(path, ROOT)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            for label, pat in PATTERNS:
                if pat.search(line):
                    FAILURES.append(f"{rel}:{lineno}: {label} -> {line.strip()}")


def test_tidak_ada_pilar_cahaya_di_caster():
    scanned = 0
    for d in SCAN_DIRS:
        base = os.path.join(ROOT, d)
        for name in sorted(os.listdir(base)):
            if not name.endswith(".py"):
                continue
            _scan(os.path.join(base, name))
            scanned += 1
    assert scanned > 50, f"hanya {scanned} file dipindai -- path salah?"
    assert not FAILURES, (
        "Pilar cahaya yang menutupi karakter muncul lagi:\n  "
        + "\n  ".join(FAILURES)
    )


# ── Pilar yang SENGAJA dipertahankan harus tetap ada ──────────────────
# Kalau salah satu ini hilang, berarti penghapusan sudah kelewat batas
# dan memakan efek yang bukan pilar-caster.
KEPT = (
    # Grimjaw W: pilar di TOTEM (wx = x + 52*fs), bukan di badan.
    ("heroes/_bundle.py", "Green healing totem"),
    # Vex Q: pilar di orb ujung tongkat (sx, sy), bukan di badan.
    ("heroes/_bundle.py", "pilar cahaya di ujung staff"),
    # Vex R: pilar astral di posisi TARGET (tx, ty).
    ("heroes/_bundle.py", "pilar astral"),
    # Razak R: 8 pilar MENGORBIT di 0.62*R, bukan di badan.
    ("heroes/razak_fx.py", "8 pilar mengorbit"),
    # Zharok R: pilar api MENGORBIT (Burning Army).
    ("heroes/zharok_fx.py", "Pilar api vertikal mengorbit"),
)


def test_pilar_non_caster_masih_ada():
    missing = []
    for rel, needle in KEPT:
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        if needle not in src:
            missing.append(f"{rel}: penanda '{needle}' hilang")
    assert not missing, (
        "Pilar non-caster ikut terhapus (scope kelewat batas):\n  "
        + "\n  ".join(missing)
    )


# ── Efek saudara harus tetap hidup ────────────────────────────────────
# Yang dibuang hanya kolom cahayanya; nova/bintang/shockwave tetap.
SIBLINGS = (
    ("heroes/_bundle.py", "_draw_omnislash_ground", "_spark_star"),
    ("heroes/_bundle.py", "_draw_warpath_effect", "_skill_outlined_circle"),
    ("heroes/_bundle.py", "_draw_blade_fury_ground", "_nova"),
    ("heroes/_bundle.py", "_draw_essence_flux_ground", "_skill_outlined_circle"),
    ("heroes/gornak_fx.py", "_draw_r", "ring_surface"),
    ("heroes/ignis_drachorn_fx.py", "_front_r", "ring_surface"),
)


def _func_body(src, fname):
    m = re.search(r"def %s\b.*?(?=\n    def |\nclass |\Z)" % re.escape(fname),
                  src, re.S)
    return m.group(0) if m else ""


def test_efek_saudara_tetap_ada():
    cache = {}
    missing = []
    for rel, fname, needle in SIBLINGS:
        path = os.path.join(ROOT, rel)
        if path not in cache:
            with open(path, encoding="utf-8", errors="replace") as fh:
                cache[path] = fh.read()
        body = _func_body(cache[path], fname)
        if not body:
            missing.append(f"{rel}: fungsi {fname} tidak ditemukan")
        elif needle not in body:
            missing.append(f"{rel}::{fname}: '{needle}' hilang")
    assert not missing, (
        "Efek saudara ikut terhapus:\n  " + "\n  ".join(missing)
    )


if __name__ == "__main__":
    tests = [
        test_tidak_ada_pilar_cahaya_di_caster,
        test_pilar_non_caster_masih_ada,
        test_efek_saudara_tetap_ada,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except AssertionError as exc:
            failed += 1
            print("FAIL  %s\n%s" % (t.__name__, exc))
    print("\n%d/%d lolos" % (len(tests) - failed, len(tests)))
    sys.exit(1 if failed else 0)
