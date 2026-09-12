#!/usr/bin/env python3
"""Jalankan levels_processor.cpp (C++) di luar engine, bandingkan dengan Python.

    python3 tools/test_levels_cpp_selftest.py            # compile + jalankan
    python3 tools/test_levels_cpp_selftest.py --binary /tmp/levels_selftest
                                                         # pakai binary yang ada

Butuh compiler C++ saja: TIDAK butuh godot-cpp, TIDAK butuh engine Godot,
TIDAK butuh pygame. Yang dijalankan adalah `levels_processor.cpp` hasil
`tools/gen_levels_cpp.py` APA ADANYA (di-include langsung oleh
godot/gdext/mystic_levels/selftest/levels_selftest.cpp), dengan Variant/Array/
Dictionary/String ditiru godot_stub.hpp memakai semantik engine 4.3 yang
dibaca dari sumbernya. Jadi satu-satunya yang tidak terverifikasi di sini adalah
lapisan binding godot-cpp — itu ranah LevelDataGdextParityTest di engine.

Kenapa perlu (dan bukan cuma tools/test_godot_level_data_parity.py):
  * parity tool membandingkan DATA dengan mem-parse literal .cpp (statis).
    Self-test ini MENGEKSEKUSI kodenya, jadi logika helper ikut terkunci:
    scan row_index, `not config -> False`, `required None -> True`, batas
    get_next_level, dan Variant::evaluate(OP_EQUAL) di py_contains.
  * Jalan dalam ±2 detik di mesin mana pun yang punya compiler — termasuk
    sebelum build godot-cpp yang ±10 menit di CI, jadi regresi data ketahuan
    lebih awal dan lebih murah.

Perutean argumen MENIRU LevelDBLoader.gd, bukan "semua kasus dikirim ke C++":
  * get_level_config: int + float BULAT (Godot memangkas float->int64 saat
    mengonversi argumen, dan Python `3 == 3.0` -> cocok). Float tidak bulat
    (3.5) dan non-angka (str/bool/nil) TIDAK dikirim — loader menurunkannya ke
    LevelDB.gd supaya semantik Python tetap utuh.
  * get_next_level: HANYA int (loader memeriksa typeof == TYPE_INT) supaya
    Python get_next_level(3.0) -> 4.0 tetap float.
  * is_level_unlocked / py_contains: apa adanya, termasuk completed_levels
    berisi float (save hasil JSON.parse_string) dan string.
Kasus yang tidak dirutekan dicatat sebagai "dilewati (jalur GDScript)" supaya
jumlahnya terlihat, bukan hilang diam-diam.

CI: dipanggil .github/workflows/godot-gdext.yml (langkah sebelum build lib).
Di workflow itu compiler dijamin ada; kalau tidak ada, tool ini GAGAL (bukan
skip) — godot-check.yml sengaja tidak memanggilnya.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

# Baterai kasus dipakai bersama dengan parity tool + fixture engine: satu sumber,
# tiga pemutar (statis, engine GDScript, C++ di luar engine).
import test_godot_level_data_parity as parity  # noqa: E402
from levels import level_data as oracle  # noqa: E402  (oracle: modul pygame asli)

SELFTEST_DIR = ROOT / "godot/gdext/mystic_levels/selftest"
FIXTURE_JSON = ROOT / "godot/tests/fixtures/level_data.json"
GENERATED_CPP = ROOT / "godot/gdext/mystic_levels/src/levels_processor.cpp"
STUB_HPP = SELFTEST_DIR / "godot_stub.hpp"

LABEL = "levels_cpp_selftest"

_checks = 0
_failures = []


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[%s] FAIL: %s" % (LABEL, message))


def section(title):
    print("[%s] %s" % (LABEL, title))


# ══════════════════════════════════════════════════════════
#  Penyandian teks (harus sama persis dengan Variant::to_text di stub)
# ══════════════════════════════════════════════════════════

def render(value, mini_keys_as_text=False):
    """Nilai Python -> teks Variant yang dicetak levels_selftest.cpp."""
    if value is None:
        return "nil:null"
    if isinstance(value, bool):
        return "bool:true" if value else "bool:false"
    if isinstance(value, int):
        return "int:%d" % value
    if isinstance(value, float):
        return "float:%.17g" % value
    if isinstance(value, str):
        return "str:%s" % value
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            rendered_key = render(str(key) if mini_keys_as_text else key)
            parts.append("%s=%s" % (rendered_key, render(item)))
        return "dict:{" + ",".join(parts) + "}"
    if isinstance(value, (list, tuple)):
        return "array:[" + ",".join(render(item) for item in value) + "]"
    raise AssertionError("tipe tak terduga: %r" % (value,))


def render_row(row):
    """Baris katalog Python -> teks yang dicetak C++.

    Satu-satunya beda yang diizinkan (sama seperti levels.json + fixture):
    kunci mini_bosses jadi string karena kunci Dictionary Godot di sini memang
    String (JSON object tidak bisa berkunci int). Nilai + URUTAN tetap.
    """
    out = {}
    for key, value in row.items():
        if key == "mini_bosses":
            out[key] = {str(wave): boss for wave, boss in value.items()}
        else:
            out[key] = value
    return render(out)


def arg_text(pair):
    """Pasangan bertipe (kind, value) dari baterai -> teks argumen stdin."""
    kind, value = pair
    if kind == "nil":
        return "nil"
    if kind == "bool":
        return "bool:true" if value else "bool:false"
    if kind == "int":
        return "int:%d" % value
    if kind == "float":
        return "float:%.17g" % value
    if kind == "str":
        return "str:%s" % value
    if kind == "list":
        return "[" + ",".join(arg_text(item) for item in value) + "]"
    raise AssertionError("kind tak dikenal: %s" % kind)


def decode(pair):
    """Pasangan bertipe -> nilai Python (untuk memanggil oracle)."""
    kind, value = pair
    if kind == "nil":
        return None
    if kind == "list":
        return [decode(item) for item in value]
    return value


def is_integral(pair):
    kind, value = pair
    if kind == "int":
        return True
    if kind == "float":
        return float(value) == float(int(value))
    return False


# ══════════════════════════════════════════════════════════
#  Compile + jalankan
# ══════════════════════════════════════════════════════════

def find_compiler():
    for name in ("g++", "clang++", "c++"):
        path = shutil.which(name)
        if path:
            return path
    return None


def compile_selftest(compiler, out_path):
    cmd = [compiler, "-std=c++17", "-O0",
           "-I", str(SELFTEST_DIR), "-I", str(SELFTEST_DIR / "shim"),
           "-o", str(out_path), str(SELFTEST_DIR / "levels_selftest.cpp")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc, cmd


def run_binary(binary, commands):
    """Kirim semua perintah lewat stdin, kembalikan {id: hasil}."""
    stdin = "".join("%s\t%s%s\n" % (cid, cmd, ("" if not args else "\t" + "\t".join(args)))
                    for cid, cmd, args, _expected, _note in commands)
    proc = subprocess.run([str(binary)], input=stdin, capture_output=True, text=True,
                          timeout=120)
    if proc.returncode != 0:
        raise RuntimeError("levels_selftest keluar %d: %s" % (proc.returncode,
                                                              proc.stderr[-2000:]))
    results = {}
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        cid, _, value = line.partition("\t")
        results[cid] = value
    return results


# ══════════════════════════════════════════════════════════
#  Daftar perintah: (id, cmd, args, expected_text, note)
# ══════════════════════════════════════════════════════════

def build_commands(catalog):
    commands = []
    skipped = []

    def add(cid, cmd, args, expected, note=""):
        commands.append((cid, cmd, args, expected, note))

    # ── permukaan katalog ──
    add("count", "count", [], render(oracle.get_level_count()), "len(ALL_LEVELS)")
    add("signature", "signature", [], render(parity.catalog_signature(catalog)),
        "bukti tabel generasi sama")
    add("bind", "bind", [], "nil:null", "_bind_methods() tersentuh (alamat method)")
    add("all_size", "all_levels_size", [], render(len(catalog)), "Array all_levels()")
    for index, row in enumerate(catalog):
        expected = render_row(row)
        add("row:%02d" % index, "row", ["int:%d" % index], expected,
            "build_row(%d)" % index)
        add("allrow:%02d" % index, "all_row", ["int:%d" % index], expected,
            "all_levels()[%d] (urutan + isi)" % index)
        add("rowidx:%d" % row["level_number"], "row_index",
            ["int:%d" % row["level_number"]], "int:%d" % index,
            "row_index(%d)" % row["level_number"])
    for index in (len(catalog), -1, 9999):
        add("row_oob:%d" % index, "row", ["int:%d" % index], "dict:{}",
            "build_row di luar jangkauan -> Dictionary kosong")
        add("allrow_oob:%d" % index, "all_row", ["int:%d" % index], "nil:null",
            "all_levels() di luar jangkauan -> NIL")
    for missing in (0, -1, len(catalog) + 1, 9999):
        add("rowidx_missing:%d" % missing, "row_index", ["int:%d" % missing],
            "int:-1", "row_index(%d) tidak ada -> -1" % missing)

    # ── get_level_config ──
    for index, pair in enumerate(parity.CONFIG_INPUTS):
        cid = "config:%02d" % index
        if not is_integral(pair):
            skipped.append((cid, "config", pair,
                            "loader menurunkan ke LevelDB.gd (_int_key null)"))
            continue
        got = oracle.get_level_config(decode(pair))
        expected = "nil:null" if got is None else render_row(got)
        add(cid, "config", [arg_text(pair)], expected,
            "get_level_config(%r)" % (decode(pair),))

    # ── get_next_level ──
    for index, pair in enumerate(parity.NEXT_INPUTS):
        cid = "next:%02d" % index
        if pair[0] != "int":
            skipped.append((cid, "next", pair,
                            "loader: typeof != TYPE_INT -> LevelDB.gd (float tetap float)"))
            continue
        expected = render(oracle.get_next_level(decode(pair)))
        add(cid, "next", [arg_text(pair)], expected,
            "get_next_level(%r)" % (decode(pair),))

    # ── is_level_unlocked ──
    for index, case in enumerate(parity.UNLOCK_CASES):
        # Catatan opsional di UNLOCK_CASES (dua entri terakhir polos).
        level, completed_pairs = case[0], case[1]
        note = case[2] if len(case) > 2 else ""
        completed = [decode(pair) for pair in completed_pairs]
        expected = render(bool(oracle.is_level_unlocked(level, completed)))
        add("unlock:%02d" % index, "unlock",
            ["int:%d" % level, arg_text(("list", list(completed_pairs)))],
            expected, "is_level_unlocked(%d, %r)%s"
            % (level, completed, (" — " + note) if note else ""))

    # ── py_contains: oracle Python `needle in haystack` ──
    for index, case in enumerate(parity.CONTAINS_CASES):
        haystack_pairs, needle_pair, note = case
        haystack = decode(("list", list(haystack_pairs)))
        needle = decode(needle_pair)
        expected = render(bool(needle in haystack))
        add("contains:%02d" % index, "contains",
            [arg_text(("list", list(haystack_pairs))), arg_text(needle_pair)],
            expected, "%r in %r — %s" % (needle, haystack, note))

    # ── deviasi yang DISENGAJA (bukan oracle Python) ──
    # Python True == 1; Variant::evaluate(OP_EQUAL) tidak punya evaluator untuk
    # BOOL vs INT (variant_op.cpp), jadi kedua backend Godot menjawab False.
    # Harapan dibaca dari fixture (sumber yang sama dengan engine test), bukan
    # dihitung ulang di sini: docs/LEVELS_GODOTPP.md + deviation_battery.
    fixture = json.loads(FIXTURE_JSON.read_text(encoding="utf-8"))
    for index, case in enumerate(fixture["deviation_battery"]):
        haystack_pairs, needle_pair, expected_bool, note = case
        expect(len(parity.DEVIATION_CASES) == len(fixture["deviation_battery"]),
               "jumlah kasus deviasi fixture != DEVIATION_CASES")
        add("deviation:%02d" % index, "contains",
            [arg_text(("list", [tuple(pair) for pair in haystack_pairs])),
             arg_text(tuple(needle_pair))],
            render(bool(expected_bool)), note)

    return commands, skipped


def compare(results, commands):
    seen = set()
    for cid, cmd, _args, expected, note in commands:
        got = results.get(cid)
        seen.add(cid)
        if got is None:
            expect(False, "%s (%s): tidak ada balasan dari levels_selftest" % (cid, cmd))
            continue
        if got.startswith("error:"):
            expect(False, "%s (%s): %s" % (cid, cmd, got))
            continue
        expect(got == expected,
               "%s (%s)%s: C++ %s != Python %s"
               % (cid, cmd, (" — " + note) if note else "", got, expected))
    for cid in results:
        if cid not in seen:
            expect(False, "balasan tak diminta dari levels_selftest: %s" % cid)


# ══════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--binary", default="",
                        help="pakai binary yang sudah dicompile (lewati langkah build)")
    parser.add_argument("--keep", action="store_true",
                        help="jangan hapus binary sementara (untuk debug)")
    args = parser.parse_args()

    for path in (SELFTEST_DIR / "levels_selftest.cpp", STUB_HPP, GENERATED_CPP):
        expect(path.exists(), "%s tidak ada" % path.relative_to(ROOT))
    if _failures:
        return 1

    catalog = list(oracle.ALL_LEVELS)
    commands, skipped = build_commands(catalog)
    ids = [command[0] for command in commands]
    expect(len(set(ids)) == len(ids), "id perintah kembar: %s"
           % sorted({i for i in ids if ids.count(i) > 1}))
    section("oracle levels/level_data.py: %d level, %d perintah C++, %d kasus "
            "dilewati (dirutekan loader ke GDScript)"
            % (len(catalog), len(commands), len(skipped)))

    temp_dir = ""
    binary = args.binary
    if binary:
        expect(Path(binary).exists(), "--binary %s tidak ada" % binary)
        if _failures:
            return 1
    else:
        compiler = find_compiler()
        expect(compiler is not None,
               "compiler C++ tidak ditemukan (g++/clang++/c++) — tool ini "
               "sengaja GAGAL, bukan skip: jalankan di job yang punya compiler "
               "(godot-gdext.yml) atau pasang build-essential")
        if _failures:
            return 1
        temp_dir = tempfile.mkdtemp(prefix="levels_selftest_")
        binary = os.path.join(temp_dir, "levels_selftest")
        proc, cmd = compile_selftest(compiler, binary)
        expect(proc.returncode == 0,
               "compile gagal (%s):\n%s" % (" ".join(cmd), proc.stderr[-4000:]))
        if _failures:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 1
        section("compile OK: %s (%d perintah, ±%d KB)"
                % (os.path.basename(compiler), len(commands),
                   os.path.getsize(binary) // 1024))

    try:
        results = run_binary(binary, commands)
    except Exception as exc:  # noqa: BLE001 - laporan apa adanya ke CI
        expect(False, "menjalankan levels_selftest gagal: %s" % exc)
        results = {}
    compare(results, commands)

    for cid, cmd, pair, reason in skipped:
        print("[%s]   dilewati %s %s(%r): %s"
              % (LABEL, cid, cmd, decode(pair), reason))

    if temp_dir and not args.keep:
        shutil.rmtree(temp_dir, ignore_errors=True)
    elif temp_dir:
        print("[%s] binary disimpan: %s" % (LABEL, binary))

    if _failures:
        print("\n[%s] FAIL: %d kegagalan dari %d cek" % (LABEL, len(_failures), _checks))
        return 1
    print("\n[%s] PASS: %d cek — levels_processor.cpp dijalankan di luar engine "
          "(%d baris katalog x %d field + 4 helper + py_contains + %d deviasi "
          "terdokumentasi)" % (LABEL, _checks, len(catalog), len(catalog[0]),
                               len(parity.DEVIATION_CASES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
