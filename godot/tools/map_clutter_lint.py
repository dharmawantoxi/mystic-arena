#!/usr/bin/env python3
"""map_clutter_lint — cegah port Godot menggambar readout yang tidak ada di
peta pygame.

Kenapa ada: dua kali port menambahkan teks/bar di atas arena yang TIDAK
pernah digambar pygame, dan keduanya menutupi peta:

  * bar HP kastil 84x7 + pip level di atas nexus (`Nexus._draw_overlays`) —
    pygame hanya menggantung crest armor + bar SHIELD 60x6 di atas kastil
    (`_entity.py::Castle._draw_castle_shield` + `Castle._draw_hp_bar`, dan
    `_draw_hp_bar` itu satu-satunya menggambar shield, BUKAN HP);
  * baris "medan: n hero . n minion . n boss . n fps" (node FieldStatus) dan
    "difficulty: ... . gold x..." (DifficultyLabel) di bawah badge LEVEL/WAVE
    — pygame tidak punya kedua baris itu; HUD-nya chip emas + badge + banner.

Keduanya DIHAPUS (permintaan user 2026-09-13: "castle HP menghalangi map",
"hapus info di bawah level & wave"). Linter ini yang menjaga supaya tidak
balik lagi: angka HP/isi medan selalu godaan murah untuk "dibantu" dengan
teks di layar, padahal di pygame angka-angka itu hidup di panel popup
(tab NEXUS / tab menara ShopPanel), bukan di atas peta.

Aturan yang dijaga (root = folder project Godot, default `godot`):
  1. scenes/base/Nexus.gd : badan `func _draw_overlays` TIDAK menyentuh
     `hp`/`max_hp` (tidak ada bar HP kastil), DAN tetap menggambar bar
     SHIELD di y=-80 + label "SHIELD n%" + crest armor.
  2. scenes/**: nama node/fungsi readout medan yang sudah dihapus tidak boleh
     muncul lagi (FieldStatus, DifficultyLabel, _refresh_field) — termasuk di
     .tscn, karena node itu dulu hidup di HUD.tscn.
  3. (opsional, hanya kalau sumber pygame ikut ter-checkout) sumber
     `_entity.py`: `Castle._draw_hp_bar` memang hanya berisi shield — aturan
     1 adalah cermin pygame, bukan selera. Kalau `Castle` di pygame sampai
     menambah bar HP, linter ini yang menyuruh port ikut menimbang ulang.

Usage: python3 godot/tools/map_clutter_lint.py [godot]
Exit 0 = bersih, 1 = ada readout yang menutupi peta.
"""
import os
import re
import sys

SCENES_SUBDIR = "scenes"

# (regex, pesan) yang TIDAK boleh ada di badan _draw_overlays Nexus.gd.
NEXUS_FORBIDDEN = [
    (r"\bhp\b(?::\s*int)?", "HP kastil dibaca di overlay — pygame tidak "
                              "menggambar HP di atas peta"),
    (r"\bmax_hp\b", "bar HP kastil dibaca (max_hp) — pygame tidak menggambar "
                    "HP di atas peta"),
    (r"\bhp_ratio\b", "rasio HP kastil digambar (hp_ratio) — hapus, cukup "
                      "shield"),
    (r"\bdraw_circle\b", "pip level kastil (draw_circle) — tidak ada di "
                          "pygame; satu-satunya lingkaran nexus adalah "
                          "bayangan kaki di _draw(), bukan _draw_overlays()"),
]

# Yang HARUS tetap ada di badan _draw_overlays Nexus.gd: padanan persis
# `_draw_castle_shield` + `_draw_hp_bar` (_entity.py:1892-1946).
NEXUS_REQUIRED = [
    (r"ArmorCrestScript\.draw", "crest armor `_draw_castle_shield`"),
    (r"-80\.0", "bar SHIELD di y-80 (`_draw_hp_bar`)"),
    (r"60\.0", "bar SHIELD lebar 60 px"),
    (r"SHIELD %d%%", "label 'SHIELD n%'"),
    (r"body_bold", "label 10 px Barlow-Bold (get_font(10, 'body_bold'))"),
]

# Nama readout medan yang sudah dihapus — dilarang muncul di seluruh scenes/.
REMOVED_READOUTS = [
    (r"\bFieldStatus\b", "baris 'medan: ...' di bawah badge LEVEL/WAVE"),
    (r"\bDifficultyLabel\b", "baris 'difficulty: ...' di bawah badge"),
    (r"func _refresh_field\b", "penghitung unit medan per frame"),
    (r"_draw_castle_bars\b", "blok HP nexus tengah-atas arena"),
]


def _func_body(text: str, name: str) -> str:
    """Badan fungsi GDScript (indentasi tab) dari `func name` sampai func next."""
    start = text.find("func %s(" % name)
    if start < 0:
        start = text.find("func %s (" % name)
    if start < 0:
        return ""
    rest = text[start:]
    m = re.search(r"\nfunc ", rest[1:])
    return rest[:m.start() + 1] if m else rest


def _iter_files(root: str):
    for dirpath, _dirs, files in os.walk(os.path.join(root, SCENES_SUBDIR)):
        for fn in files:
            if fn.endswith((".gd", ".tscn", ".tres")):
                yield os.path.join(dirpath, fn)


def check_nexus(root: str) -> list:
    path = os.path.join(root, "scenes", "base", "Nexus.gd")
    if not os.path.isfile(path):
        return ["%s: tidak ditemukan" % path]
    with open(path, encoding="utf-8") as fh:
        body = _func_body(fh.read(), "_draw_overlays")
    if not body:
        return ["%s: func _draw_overlays hilang" % path]
    # Komentar dokumen (baris `#`) bukan gambar — jangan kena larangan hanya
    # karena menjelaskan apa yang TIDAK digambar lagi.
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.strip().startswith("#"))
    errors = []
    for pattern, why in NEXUS_FORBIDDEN:
        if re.search(pattern, code):
            errors.append("%s: %s -> %s" % (path, pattern, why))
    for pattern, what in NEXUS_REQUIRED:
        if not re.search(pattern, code):
            errors.append("%s: kehilangan %s (%s)" % (path, what, pattern))
    return errors


def check_removed(root: str) -> list:
    errors = []
    for path in sorted(_iter_files(root)):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for pattern, why in REMOVED_READOUTS:
            for i, line in enumerate(text.splitlines(), 1):
                if line.strip().startswith("#"):
                    continue  # catatan historis boleh menyebut nama lamanya
                if re.search(pattern, line):
                    errors.append("%s:%d: %s (%s)"
                                  % (path, i, pattern, why))
    return errors


def check_pygame_contract(root: str) -> list:
    """`Castle._draw_hp_bar` pygame hanya berisi shield — cermin aturan 1."""
    candidates = [os.path.join(root, os.pardir, "_entity.py"),
                  os.path.join("_entity.py")]
    src = next((p for p in candidates if os.path.isfile(p)), None)
    if src is None:
        return []          # sumber pygame tidak di-checkout: bukan kegagalan
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    # `_draw_hp_bar` adalah method pygame (indentasi spasi) — diambil dengan
    # regex sendiri sampai `def `/`class ` berikutnya.
    m = re.search(r"\n    def _draw_hp_bar\(.*?(?=\n    def |\nclass |\Z)",
                  text, re.S)
    if not m:
        return ["%s: Castle._draw_hp_bar tidak ditemukan (pygame berubah?)" % src]
    body = m.group(0)
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.strip().startswith("#"))
    errors = []
    if "shield" not in code:
        errors.append("%s: _draw_hp_bar tidak lagi menggambar shield — "
                      "port Godot perlu ditimbang ulang" % src)
    if re.search(r"\bself\.hp\b", code):
        errors.append("%s: _draw_hp_bar KINI membaca self.hp (HP kastil "
                      "digambar di peta) — Nexus.gd harus ikut, dan aturan 1 "
                      "linter ini perlu diperbarui" % src)
    return errors


def main(argv: list) -> int:
    root = argv[1] if len(argv) > 1 else "godot"
    errors = check_nexus(root) + check_removed(root) \
        + check_pygame_contract(root)
    if errors:
        for e in errors:
            print("FAIL  %s" % e)
        print("\n%d masalah: readout di atas peta harus mengikuti pygame " \
              "(HP/isi medan ada di panel, bukan di arena)." % len(errors))
        return 1
    print("OK — tidak ada readout HP/medan yang menutupi peta "
          "(Nexus: crest + bar SHIELD saja; HUD tanpa FieldStatus/"
          "DifficultyLabel)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
