# ================================
# tools/gen_boss_index.py
# Membuat bosses/_boss_index.py : peta {nama_boss: "levelN"}
#
# Kenapa perlu?
#   heroes/__init__.py dulu MENG-IMPORT ke-54 berkas bosses/level*.py
#   saat start hanya untuk mencari fungsi draw_*(). Itu ±4 MB kode
#   Python yang di-parse di HP -> waktu buka lama & RAM boros.
#   Dengan indeks statis ini, modul boss diimpor HANYA saat boss-nya
#   benar-benar digambar.
#
# Jalankan ulang setiap kali menambah/mengganti boss:
#     python tools/gen_boss_index.py
# ================================
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOSS_DIR = os.path.join(ROOT, "bosses")
OUT = os.path.join(BOSS_DIR, "_boss_index.py")

RE_DRAW = re.compile(r"^def\s+(draw_[A-Za-z0-9_]+)\s*\(", re.M)


def main():
    index = {}
    collisions = []

    files = sorted(
        (f for f in os.listdir(BOSS_DIR)
         if re.fullmatch(r"level\d+\.py", f)),
        key=lambda f: int(re.findall(r"\d+", f)[0]))

    for fname in files:
        mod = fname[:-3]
        with open(os.path.join(BOSS_DIR, fname), encoding="utf-8") as fh:
            src = fh.read()
        for func in RE_DRAW.findall(src):
            if func == "draw_boss":
                continue
            boss = func[len("draw_"):]
            if boss in index and index[boss][0] != mod:
                collisions.append((boss, index[boss][0], mod))
                continue
            index[boss] = (mod, func)

    lines = [
        '"""',
        "bosses/_boss_index.py - DIBUAT OTOMATIS oleh tools/gen_boss_index.py",
        "",
        "Peta nama boss -> (nama modul, nama fungsi draw).",
        "Dipakai heroes/__init__.py untuk impor malas (lazy import),",
        "supaya aplikasi tidak memuat 54 modul boss saat start.",
        "",
        "JANGAN diedit manual - jalankan ulang generatornya.",
        '"""',
        "",
        "BOSS_INDEX = {",
    ]
    for boss in sorted(index):
        mod, func = index[boss]
        lines.append('    "%s": ("%s", "%s"),' % (boss, mod, func))
    lines.append("}")
    lines.append("")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print("[gen] %d boss terindeks dari %d berkas -> %s"
          % (len(index), len(files), os.path.relpath(OUT, ROOT)))
    if collisions:
        print("[gen] PERINGATAN nama ganda (dipakai yang pertama):")
        for boss, first, other in collisions:
            print("      %s: %s vs %s" % (boss, first, other))
    return 0


if __name__ == "__main__":
    sys.exit(main())
