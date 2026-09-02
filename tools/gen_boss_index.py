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


def _boss_types_by_level():
    """{nomor_level: {tipe_boss, ...}} dari levels/level_data.py.

    Dipakai untuk memecah tabrakan nama fungsi: dua level bisa sama-sama
    punya `def draw_morvaeth()`, tapi boss_data membedakan tipenya
    (`morvaeth` di level 25, `morvaeth2` di level 42). Tanpa peta ini
    tipe kedua tidak pernah masuk indeks, dan boss-nya render KOSONG.
    """
    sys.path.insert(0, ROOT)
    out = {}
    try:
        from levels import ALL_LEVELS
    except Exception as exc:                       # pragma: no cover
        print("[gen] PERINGATAN: levels tidak terbaca (%s); "
              "tabrakan nama tidak bisa dipecah." % exc)
        return out
    for cfg in ALL_LEVELS:
        num = cfg.get("level_number")
        types = set(cfg.get("mini_bosses", {}).values())
        true_boss = cfg.get("true_boss")
        if true_boss:
            types.add(true_boss)
        out.setdefault(num, set()).update(types)
    return out


def main():
    index = {}
    collisions = []
    unresolved = []

    files = sorted(
        (f for f in os.listdir(BOSS_DIR)
         if re.fullmatch(r"level\d+\.py", f)),
        key=lambda f: int(re.findall(r"\d+", f)[0]))

    level_types = _boss_types_by_level()

    for fname in files:
        mod = fname[:-3]
        lvl = int(re.findall(r"\d+", fname)[0])
        owned = level_types.get(lvl, set())
        with open(os.path.join(BOSS_DIR, fname), encoding="utf-8") as fh:
            src = fh.read()
        for func in RE_DRAW.findall(src):
            if func == "draw_boss":
                continue
            boss = func[len("draw_"):]
            if boss in index and index[boss][0] != mod:
                # Nama fungsi sudah dipakai modul lain. Cari tipe boss
                # MILIK LEVEL INI yang belum terindeks dan namanya sama
                # plus akhiran angka -> itulah varian (`morvaeth2`) yang
                # selama ini hilang dari indeks.
                alias = sorted(
                    t for t in owned
                    if t not in index
                    and re.fullmatch(re.escape(boss) + r"\d+", t))
                if alias:
                    index[alias[0]] = (mod, func)
                    collisions.append(
                        (boss, index[boss][0], mod, alias[0]))
                else:                              # pragma: no cover
                    unresolved.append((boss, index[boss][0], mod))
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
        print("[gen] nama fungsi ganda - dipetakan ke tipe boss level-nya:")
        for boss, first, other, alias in collisions:
            print("      %s: %s vs %s -> %s dipakai untuk %s"
                  % (boss, first, other, other, alias))
    if unresolved:                                 # pragma: no cover
        print("[gen] PERINGATAN nama ganda TAK TERPECAHKAN "
              "(boss kedua akan render kosong!):")
        for boss, first, other in unresolved:
            print("      %s: %s vs %s" % (boss, first, other))

    # Jaring pengaman: setiap tipe di boss_data WAJIB ada di indeks,
    # kalau tidak boss-nya render kosong di dalam game.
    try:
        from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
        wanted = list(MINI_BOSS_TYPES) + list(TRUE_BOSS_TYPES)
        missing = [t for t in wanted if t not in index]
        if missing:
            print("[gen] PERINGATAN %d tipe boss TIDAK terindeks: %s"
                  % (len(missing), ", ".join(sorted(missing))))
        else:
            print("[gen] OK - semua %d tipe boss di boss_data terindeks."
                  % len(wanted))
    except Exception as exc:                       # pragma: no cover
        print("[gen] boss_data tidak terbaca: %s" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
