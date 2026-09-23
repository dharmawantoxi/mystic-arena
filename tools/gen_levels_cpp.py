#!/usr/bin/env python3
"""Transpile levels/level_data.py -> C++ GDExtension (godot++).

    python3 tools/gen_levels_cpp.py           # regenerasi
    python3 tools/gen_levels_cpp.py --check   # CI: berkas ter-commit harus identik

Bagian dari migrasi `levels/` -> godot++ (FASE 34). Pola yang sama dengan
`tools/gen_hero_skills_cpp.py` (hero_skills -> MysticHeroSkills): C++ TIDAK
ditulis/diterjemahkan tangan, melainkan dibangkitkan dari AST Python yang
menjadi sumber kebenaran, jadi angka di `levels_processor.cpp` selalu sama
dengan `levels/level_data.py`.

Yang dibangkitkan:

  godot/gdext/mystic_levels/src/levels_processor.h
  godot/gdext/mystic_levels/src/levels_processor.cpp

Isi C++-nya dua bagian:

  1. TABEL POD (`static const`, trivially destructible) — 54 baris level +
     54 array mini boss. Sengaja BUKAN `static Dictionary`/`static Array`:
     Variant statis di GDExtension didestruksi saat `dlclose`, setelah engine
     melepas allocator-nya, dan itu crash klasik saat exit. Tabel POD tidak
     punya destructor, jadi tidak ada urutan-teardown yang bisa salah.
  2. BUILDER + 5 fungsi API publik `levels/__init__.py` (all_levels,
     get_level_config, get_level_count, is_level_unlocked, get_next_level).
     Dictionary dibangun per panggilan dari tabel (~1 mikrodetik per level);
     caching katalog dilakukan di GDScript (LevelDBLoader), bukan di C++.

Skema field TIDAK di-hardcode di generator: kunci, urutan kunci, dan tipe
nilainya dibaca dari AST, jadi menambah level baru (atau field baru) cukup
dengan mengubah `levels/level_data.py` lalu menjalankan generator ini.

Kontrak data yang ditegakkan generator (gagal keras, bukan diam-diam):

  * tiap level punya kunci yang SAMA dengan URUTAN yang sama — Dictionary
    Godot mempertahankan urutan insert (dipakai diff manusia + fixture
    paritas), jadi skema campuran tidak bisa dibangkitkan setia;
  * `level_number` unik — `get_level_config` Python mengembalikan kecocokan
    PERTAMA, duplikat akan menjadi bug senyap;
  * tiap `LEVEL_*` yang didefinisikan masuk `ALL_LEVELS` — level yang lupa
    di-append tidak akan pernah muncul di menu (komentar "CARA TAMBAH LEVEL
    BARU" di kepala level_data.py menyebut langkah itu eksplisit);
  * nilai hanya boleh literal int/float/str/None/dict{int|str -> str}.
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "levels" / "level_data.py"
OUT_H = ROOT / "godot" / "gdext" / "mystic_levels" / "src" / "levels_processor.h"
OUT_CPP = ROOT / "godot" / "gdext" / "mystic_levels" / "src" / "levels_processor.cpp"

CLASS = "MysticLevels"
LIBRARY = "mystic_levels"

# ══════════════════════════════════════════════════════════
#  Baca AST level_data.py
# ══════════════════════════════════════════════════════════


class LevelError(Exception):
    """Data level_data.py tidak memenuhi kontrak generator."""


def parse_levels():
    """Ambil (nama -> dict literal) untuk LEVEL_* dan urutan ALL_LEVELS."""
    source = SRC.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SRC))

    tables = {}
    order = []
    lines = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id.startswith("LEVEL_") and isinstance(node.value, ast.Dict):
            try:
                tables[target.id] = ast.literal_eval(node.value)
            except ValueError as exc:
                raise LevelError(
                    "%s:%d — %s bukan literal murni (generator menolak "
                    "menghitung ekspresi; pakai angka/teks langsung atau "
                    "perluas tools/gen_levels_cpp.py)" % (SRC.name, node.lineno, target.id)
                ) from exc
            lines[target.id] = node.lineno
        elif target.id == "ALL_LEVELS" and isinstance(node.value, (ast.List, ast.Tuple)):
            for elt in node.value.elts:
                if not isinstance(elt, ast.Name):
                    raise LevelError(
                        "%s:%d — ALL_LEVELS harus daftar nama LEVEL_*" % (SRC.name, node.lineno))
                order.append(elt.id)

    if not tables:
        raise LevelError("tidak ada LEVEL_* di %s" % SRC)
    if not order:
        raise LevelError("ALL_LEVELS tidak ditemukan di %s" % SRC)
    missing = [name for name in order if name not in tables]
    if missing:
        raise LevelError("ALL_LEVELS merujuk definisi yang tidak ada: %s" % ", ".join(missing))
    orphan = [name for name in tables if name not in order]
    if orphan:
        raise LevelError(
            "LEVEL_* didefinisikan tapi tidak masuk ALL_LEVELS (level tidak akan "
            "muncul di menu): %s" % ", ".join(sorted(orphan, key=_level_sort_key)))
    return tables, order, lines


def _level_sort_key(name):
    tail = name.split("_", 1)[1]
    return (0, int(tail)) if tail.isdigit() else (1, 0)


# ══════════════════════════════════════════════════════════
#  Skema: kunci + tipe (dibaca dari data, bukan hardcode)
# ══════════════════════════════════════════════════════════

KIND_INT = "int"
KIND_FLOAT = "float"
KIND_STR = "str"
KIND_NIL = "nil"
KIND_INT_OPT = "int?"
KIND_STR_OPT = "str?"
KIND_MINI = "mini_bosses"


def _value_kind(key, value, level_name):
    if value is None:
        return KIND_NIL
    if isinstance(value, bool):
        raise LevelError("%s.%s — bool tidak didukung (Python bool == int, "
                         "satu sumber ambiguitas)" % (level_name, key))
    if isinstance(value, int):
        return KIND_INT
    if isinstance(value, float):
        return KIND_FLOAT
    if isinstance(value, str):
        return KIND_STR
    if isinstance(value, dict):
        for wave, boss in value.items():
            if not isinstance(wave, (int, str)) or isinstance(wave, bool):
                raise LevelError("%s.%s — kunci wave %r bukan int/str"
                                 % (level_name, key, wave))
            if not isinstance(boss, str):
                raise LevelError("%s.%s — nama boss %r bukan str"
                                 % (level_name, key, boss))
        return KIND_MINI
    raise LevelError("%s.%s — tipe %s tidak didukung generator (perluas "
                     "tools/gen_levels_cpp.py)" % (level_name, key, type(value).__name__))


_NULLABLE_BASE = {KIND_INT_OPT: KIND_INT, KIND_STR_OPT: KIND_STR}
_NULLABLE_KIND = {KIND_INT: KIND_INT_OPT, KIND_STR: KIND_STR_OPT}


def _split_kind(kind):
    """(base, nullable) — base None berarti selalu None."""
    if kind in _NULLABLE_BASE:
        return _NULLABLE_BASE[kind], True
    if kind == KIND_NIL:
        return None, True
    return kind, False


def _join_kind(base, nullable, key, level_name):
    if base is None:
        return KIND_NIL
    if not nullable:
        return base
    if base not in _NULLABLE_KIND:
        raise LevelError("%s — field %s kadang None kadang %s; kolom nullable "
                         "hanya didukung untuk int/str (tulis nilainya eksplisit "
                         "di semua level)" % (level_name, key, base))
    return _NULLABLE_KIND[base]


def build_schema(levels):
    """Kunci berurutan + kind per kunci (kind nullable kalau campur None)."""
    keys = list(levels[0][1].keys())
    kinds = {}
    for name, row in levels:
        row_keys = list(row.keys())
        if row_keys != keys:
            raise LevelError(
                "%s punya skema berbeda.\n  level 1 : %s\n  %-9s: %s\n"
                "Urutan kunci ikut menentukan urutan Dictionary Godot, jadi "
                "generator menuntut skema seragam (samakan field-nya lalu "
                "jalankan ulang tools/gen_levels_cpp.py)."
                % (name, keys, name, row_keys))
        for key in keys:
            base, nullable = _split_kind(_value_kind(key, row[key], name))
            if key not in kinds:
                kinds[key] = _join_kind(base, nullable, key, name)
                continue
            prev_base, prev_nullable = _split_kind(kinds[key])
            if prev_base is not None and base is not None and prev_base != base:
                raise LevelError(
                    "%s — field %s punya dua tipe: %s dan %s. Kolom POD cuma "
                    "satu; samakan penulisannya di level_data.py (mis. always "
                    "`1.05`, bukan campuran `1` dan `1.05`)."
                    % (name, key, prev_base, base))
            merged_base = base if prev_base is None else prev_base
            kinds[key] = _join_kind(merged_base, prev_nullable or nullable, key, name)
    return keys, kinds


def validate(levels, keys):
    seen = {}
    for name, row in levels:
        number = row.get("level_number")
        if not isinstance(number, int) or isinstance(number, bool):
            raise LevelError("%s — level_number harus int, dapat %r" % (name, number))
        if number in seen:
            raise LevelError("level_number %d dipakai %s dan %s — "
                             "get_level_config mengembalikan yang PERTAMA, jadi "
                             "satunya tidak akan pernah terpilih"
                             % (number, seen[number], name))
        seen[number] = name
        if not isinstance(row.get("mini_bosses"), dict):
            raise LevelError("%s — mini_bosses wajib ada (jadwal mini boss "
                             "dibaca Main._roll_mini_boss_schedule)" % name)


# ══════════════════════════════════════════════════════════
#  Emisi C++
# ══════════════════════════════════════════════════════════

BANNER = (
    "// ═══ GENERATED — JANGAN SUNTING TANGAN ═══\n"
    "// Sumber    : levels/level_data.py\n"
    "// Generator : tools/gen_levels_cpp.py (AST Python -> C++, bukan terjemahan tangan)\n"
    "// Regenerasi: python3 tools/gen_levels_cpp.py\n"
    "// Cek CI    : python3 tools/gen_levels_cpp.py --check\n"
    "// Desain    : docs/AUDIT_ULANG_DARI_AWAL.md\n"
)


_SIMPLE_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def c_string(text):
    """Literal string C++ (berkas tetap ASCII-murni).

    Byte non-ASCII ditulis sebagai escape OKTAL, bukan `\\xNN`: escape heks
    C rakus (menelan semua digit heks berikutnya, jadi `"\\xE2" "80"` bisa
    salah baca), sedangkan escape oktal berhenti di 3 digit. `String(const
    char*)` godot-cpp membaca UTF-8, jadi byte apa adanya sudah benar.
    """
    out = ['"']
    for ch in text:
        if ch in _SIMPLE_ESCAPES:
            out.append(_SIMPLE_ESCAPES[ch])
        elif 0x20 <= ord(ch) <= 0x7E:
            out.append(ch)
        else:
            for byte in ch.encode("utf-8"):
                out.append("\\%03o" % byte)
    out.append('"')
    return "".join(out)


def cpp_float(value):
    """Literal double yang round-trip bit-eksak (repr Python = shortest)."""
    text = repr(float(value))
    if "." not in text and "e" not in text and "E" not in text and text not in ("inf", "-inf", "nan"):
        text += ".0"
    return text


def emit_header(keys, kinds, level_count):
    h = []
    h.append("#ifndef MYSTIC_LEVELS_PROCESSOR_H")
    h.append("#define MYSTIC_LEVELS_PROCESSOR_H")
    h.append("")
    h.append(BANNER.rstrip("\n"))
    h.append("//")
    h.append("// Port levels/level_data.py (%d level, %d field) ke Godot C++ GDExtension." % (level_count, len(keys)))
    h.append("// API = persis ekspor levels/__init__.py: ALL_LEVELS, get_level_config,")
    h.append("// get_level_count, is_level_unlocked, get_next_level.")
    h.append("")
    h.append("#include <godot_cpp/classes/ref_counted.hpp>")
    h.append("#include <godot_cpp/core/class_db.hpp>")
    h.append("#include <godot_cpp/variant/array.hpp>")
    h.append("#include <godot_cpp/variant/dictionary.hpp>")
    h.append("#include <godot_cpp/variant/string.hpp>")
    h.append("#include <godot_cpp/variant/variant.hpp>")
    h.append("#include <cstdint>")
    h.append("")
    h.append("namespace godot {")
    h.append("")
    h.append("class %s : public RefCounted {" % CLASS)
    h.append("    GDCLASS(%s, RefCounted);" % CLASS)
    h.append("")
    h.append("public:")
    h.append("    // ── API publik (paritas levels/__init__.py) ──")
    h.append("    static Array all_levels();")
    h.append("    static Variant get_level_config(int64_t level_number);")
    h.append("    static int64_t get_level_count();")
    h.append("    static bool is_level_unlocked(int64_t level_number, const Array &completed_levels);")
    h.append("    static Variant get_next_level(int64_t current_level);")
    h.append("")
    h.append("    // ── helper (dipakai loader + harness paritas; juga di-bind) ──")
    h.append("    // Baris katalog ke-`index` sebagai Dictionary segar (urutan kunci = urutan")
    h.append("    // literal dict Python). Index di luar jangkauan -> Dictionary kosong.")
    h.append("    static Dictionary build_row(int64_t index);")
    h.append("    // Indeks baris untuk level_number, -1 kalau tidak ada (scan linear =")
    h.append("    // paritas loop `for lvl in ALL_LEVELS` di get_level_config Python).")
    h.append("    static int64_t row_index(int64_t level_number);")
    h.append("    // `needle in haystack` semantik Python (== numerik int/float), BUKAN")
    h.append("    // Array.has() Godot yang strict-tipe (hash_compare).")
    h.append("    static bool py_contains(const Array &haystack, const Variant &needle);")
    h.append("    // Tanda tangan katalog: bukti lib termuat + tabelnya generasi yang sama.")
    h.append("    static String catalog_signature();")
    h.append("")
    h.append("protected:")
    h.append("    static void _bind_methods();")
    h.append("};")
    h.append("")
    h.append("} // namespace godot")
    h.append("")
    h.append("#endif // MYSTIC_LEVELS_PROCESSOR_H")
    h.append("")
    return "\n".join(h)


def struct_fields(keys, kinds):
    """(nama field C++, deklarasi, komentar) per kunci Python."""
    fields = []
    for key in keys:
        kind = kinds[key]
        if kind == KIND_INT or kind == KIND_INT_OPT:
            fields.append((key, "int64_t %s;" % key, "int"))
        elif kind == KIND_FLOAT:
            fields.append((key, "double %s;" % key, "float"))
        elif kind == KIND_STR or kind == KIND_STR_OPT:
            fields.append((key, "const char *%s;" % key, "str"))
        elif kind == KIND_MINI:
            fields.append((key, "const MiniBossSlot *%s;" % key, "dict"))
            fields.append((key + "_count", "int64_t %s_count;" % key, "dict"))
        elif kind == KIND_NIL:
            continue  # tidak butuh kolom: builder selalu menulis Variant()
        if kind in (KIND_INT_OPT, KIND_STR_OPT):
            fields.append(("has_" + key, "bool has_%s;" % key, "None"))
    return fields


def emit_row_literal(row, keys, kinds):
    parts = []
    for key in keys:
        kind = kinds[key]
        value = row[key]
        if kind == KIND_NIL:
            continue
        if kind == KIND_INT:
            parts.append("%d" % value)
        elif kind == KIND_FLOAT:
            parts.append(cpp_float(value))
        elif kind == KIND_STR:
            parts.append(c_string(value))
        elif kind == KIND_INT_OPT:
            parts.append("0" if value is None else "%d" % value)
            parts.append("false" if value is None else "true")
        elif kind == KIND_STR_OPT:
            parts.append("nullptr" if value is None else c_string(value))
            parts.append("false" if value is None else "true")
        elif kind == KIND_MINI:
            parts.append("kMini%d" % row["level_number"])
            parts.append("%d" % len(value))
    return ", ".join(parts)


def emit_builder(keys, kinds):
    out = []
    out.append("Dictionary %s::build_row(int64_t index) {" % CLASS)
    out.append("    if (index < 0 || index >= kLevelCount) {")
    out.append("        return Dictionary();")
    out.append("    }")
    out.append("    const LevelRow &r = kLevels[index];")
    out.append("    Dictionary d;")
    for key in keys:
        kind = kinds[key]
        if kind == KIND_INT:
            out.append('    d["%s"] = (int64_t)r.%s;' % (key, key))
        elif kind == KIND_FLOAT:
            out.append('    d["%s"] = r.%s;' % (key, key))
        elif kind == KIND_STR:
            out.append('    d["%s"] = String(r.%s);' % (key, key))
        elif kind == KIND_INT_OPT:
            out.append("    if (r.has_%s) {" % key)
            out.append('        d["%s"] = (int64_t)r.%s;' % (key, key))
            out.append("    } else {")
            out.append('        d["%s"] = Variant(); // Python: None' % key)
            out.append("    }")
        elif kind == KIND_STR_OPT:
            out.append("    if (r.%s != nullptr) {" % key)
            out.append('        d["%s"] = String(r.%s);' % (key, key))
            out.append("    } else {")
            out.append('        d["%s"] = Variant(); // Python: None' % key)
            out.append("    }")
        elif kind == KIND_NIL:
            out.append('    d["%s"] = Variant(); // Python: None di SEMUA level' % key)
        elif kind == KIND_MINI:
            out.append("    {")
            out.append("        Dictionary %s;" % key)
            out.append("        for (int64_t i = 0; i < r.%s_count; i++) {" % key)
            out.append("            // Kunci wave = STRING: kunci objek JSON selalu string, jadi")
            out.append("            // levels.json (backend GDScript) dan pemakai Godot memakai \"10\",")
            out.append("            // bukan int 10 seperti di Python. URUTAN insert dipertahankan")
            out.append("            // (Dictionary Godot ordered) — level 3 memang 25, 10, 17.")
            out.append("            %s[String(r.%s[i].wave)] = String(r.%s[i].boss);" % (key, key, key))
            out.append("        }")
            out.append('        d["%s"] = %s;' % (key, key))
            out.append("    }")
    out.append("    return d;")
    out.append("}")
    return out


def emit_py_contains():
    """`x in list` semantik Python — dipakai is_level_unlocked + harness A/B."""
    out = []
    out.append("bool %s::py_contains(const Array &haystack, const Variant &needle) {" % CLASS)
    out.append("    // Python `x in list` memakai ==, jadi 1 cocok dengan 1.0. Array.has()")
    out.append("    // Godot memakai hash_compare yang MEMBEDAKAN tipe (variant.cpp:3309) —")
    out.append("    // itu sebabnya save hasil JSON.parse_string (SEMUA angka jadi float,")
    out.append("    // json.cpp:341) membuat `3 in [3.0]` false di GDScript naif dan level")
    out.append("    // tampak terkunci lagi setelah restart.")
    out.append("    for (int64_t i = 0; i < haystack.size(); i++) {")
    out.append("        bool valid = false;")
    out.append("        Variant equal;")
    out.append("        Variant::evaluate(Variant::OP_EQUAL, haystack[i], needle, equal, valid);")
    out.append("        if (valid && bool(equal)) {")
    out.append("            return true;")
    out.append("        }")
    out.append("        // valid == false: pasangan tipe tanpa evaluator == (mis. bool vs")
    out.append("        // int). Python menganggap True == 1; deviasi itu dicatat di")
    out.append("        // docs/AUDIT_ULANG_DARI_AWAL.md dan tidak terjadi di produksi (save Godot")
    out.append("        // hanya menyimpan int/float). Tidak pernah error/crash di sini.")
    out.append("    }")
    out.append("    return false;")
    out.append("}")
    return out


def emit_is_level_unlocked(keys, kinds):
    """is_level_unlocked — kolom syarat dibaca dari skema, bukan hardcode."""
    unlock_key = None
    for key in keys:
        if kinds[key] in (KIND_INT_OPT, KIND_STR_OPT, KIND_INT, KIND_STR, KIND_NIL) \
                and "unlock" in key:
            unlock_key = key
            break
    out = []
    out.append("bool %s::is_level_unlocked(int64_t level_number, const Array &completed_levels) {" % CLASS)
    out.append("    int64_t index = row_index(level_number);")
    out.append("    if (index < 0) {")
    out.append("        return false; // Python: `if not config: return False`")
    out.append("    }")
    if unlock_key is None:
        out.append("    // level_data.py tidak punya kolom syarat unlock -> semua terbuka.")
        out.append("    (void)completed_levels;")
        out.append("    return true;")
    elif kinds[unlock_key] == KIND_NIL:
        out.append("    // %s == None di SEMUA level -> `required is None` -> selalu terbuka." % unlock_key)
        out.append("    (void)completed_levels;")
        out.append("    return true;")
    else:
        out.append("    const LevelRow &r = kLevels[index];")
        if kinds[unlock_key] == KIND_INT_OPT:
            out.append("    if (!r.has_%s) {" % unlock_key)
            out.append("        return true; // Python: required is None -> selalu terbuka")
            out.append("    }")
            out.append("    return py_contains(completed_levels, Variant((int64_t)r.%s));" % unlock_key)
        elif kinds[unlock_key] == KIND_STR_OPT:
            out.append("    if (r.%s == nullptr) {" % unlock_key)
            out.append("        return true; // Python: required is None -> selalu terbuka")
            out.append("    }")
            out.append("    return py_contains(completed_levels, Variant(String(r.%s)));" % unlock_key)
        elif kinds[unlock_key] == KIND_INT:
            out.append("    // %s tidak pernah None di data hari ini -> tidak ada cabang terbuka." % unlock_key)
            out.append("    return py_contains(completed_levels, Variant((int64_t)r.%s));" % unlock_key)
        else:
            out.append("    return py_contains(completed_levels, Variant(String(r.%s)));" % unlock_key)
    out.append("}")
    return out


def emit_catalog_signature(keys, kinds):
    """Tanda tangan katalog murah — bukti lib termuat berisi tabel yang sama."""
    mini_key = None
    for key in keys:
        if kinds[key] == KIND_MINI:
            mini_key = key
            break
    out = []
    out.append("String %s::catalog_signature() {" % CLASS)
    out.append("    // Ringkasan murah untuk harness: jumlah level + nomor pertama/terakhir +")
    out.append("    // total slot mini boss. Bukan hash kriptografis — tujuannya membuktikan")
    out.append("    // lib yang termuat memuat tabel generasi yang sama dengan data repo.")
    out.append("    int64_t mini_total = 0;")
    if mini_key is not None:
        out.append("    for (int64_t i = 0; i < kLevelCount; i++) {")
        out.append("        mini_total += kLevels[i].%s_count;" % mini_key)
        out.append("    }")
    out.append("    String sig = String::num_int64(kLevelCount) + \":\";")
    out.append("    if (kLevelCount > 0) {")
    out.append("        sig += String::num_int64(kLevels[0].level_number) + \"-\"")
    out.append("             + String::num_int64(kLevels[kLevelCount - 1].level_number);")
    out.append("    }")
    out.append("    sig += \":\" + String::num_int64(mini_total);")
    out.append("    return sig;")
    out.append("}")
    return out


def emit_cpp(levels, keys, kinds, lines):
    level_count = len(levels)
    cpp = []
    cpp.append(BANNER.rstrip("\n"))
    cpp.append('#include "levels_processor.h"')
    cpp.append("")
    cpp.append("using namespace godot;")
    cpp.append("")
    cpp.append("namespace {")
    cpp.append("")
    cpp.append("// Satu slot mini boss. Kunci wave STRING (lihat komentar build_row).")
    cpp.append("struct MiniBossSlot {")
    cpp.append("    const char *wave;")
    cpp.append("    const char *boss;")
    cpp.append("};")
    cpp.append("")
    cpp.append("// Baris katalog. Kolom = kunci level_data.py (skema dibaca generator dari")
    cpp.append("// AST, jadi field baru di Python otomatis jadi kolom baru di sini).")
    cpp.append("// POD murni: tidak ada Variant statis (aman terhadap urutan teardown lib).")
    cpp.append("struct LevelRow {")
    for _name, decl, _note in struct_fields(keys, kinds):
        cpp.append("    %s" % decl)
    cpp.append("};")
    cpp.append("")

    # Array mini boss per level (nama = kMini<level_number>, dipakai literal baris).
    for name, row in levels:
        mini = row["mini_bosses"]
        number = row["level_number"]
        cpp.append("// %s mini_bosses (%d slot) — %s:%d" % (name, len(mini), SRC.name, lines[name]))
        if not mini:
            cpp.append("const MiniBossSlot *const kMini%d = nullptr;" % number)
            cpp.append("")
            continue
        cpp.append("const MiniBossSlot kMini%d[] = {" % number)
        items = ["    {%s, %s}," % (c_string(str(wave)), c_string(boss)) for wave, boss in mini.items()]
        cpp.extend(items)
        cpp.append("};")
        cpp.append("")

    cpp.append("// %d level — urutan = ALL_LEVELS di %s." % (level_count, SRC.name))
    cpp.append("const LevelRow kLevels[] = {")
    for name, row in levels:
        cpp.append("    // %s (%s:%d)" % (name, SRC.name, lines[name]))
        cpp.append("    {%s}," % emit_row_literal(row, keys, kinds))
    cpp.append("};")
    cpp.append("")
    cpp.append("const int64_t kLevelCount = %d;" % level_count)
    cpp.append("")
    cpp.append("} // namespace")
    cpp.append("")

    cpp.extend(emit_builder(keys, kinds))
    cpp.append("")
    cpp.append("Array %s::all_levels() {" % CLASS)
    cpp.append("    // ALL_LEVELS Python: list %d dict. Array dibangun segar tiap panggilan;" % level_count)
    cpp.append("    // cache katalog dipegang LevelDBLoader.gd (satu kali per backend).")
    cpp.append("    Array out;")
    cpp.append("    out.resize(kLevelCount);")
    cpp.append("    for (int64_t i = 0; i < kLevelCount; i++) {")
    cpp.append("        out[i] = build_row(i);")
    cpp.append("    }")
    cpp.append("    return out;")
    cpp.append("}")
    cpp.append("")
    cpp.append("int64_t %s::row_index(int64_t level_number) {" % CLASS)
    cpp.append("    for (int64_t i = 0; i < kLevelCount; i++) {")
    cpp.append("        if (kLevels[i].level_number == level_number) {")
    cpp.append("            return i;")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    return -1;")
    cpp.append("}")
    cpp.append("")
    cpp.append("Variant %s::get_level_config(int64_t level_number) {" % CLASS)
    cpp.append("    // Python: return None kalau tidak ketemu -> Variant() (NIL).")
    cpp.append("    int64_t index = row_index(level_number);")
    cpp.append("    if (index < 0) {")
    cpp.append("        return Variant();")
    cpp.append("    }")
    cpp.append("    return build_row(index);")
    cpp.append("}")
    cpp.append("")
    cpp.append("int64_t %s::get_level_count() {" % CLASS)
    cpp.append("    return kLevelCount; // len(ALL_LEVELS)")
    cpp.append("}")
    cpp.append("")
    cpp.extend(emit_py_contains())
    cpp.append("")
    cpp.extend(emit_is_level_unlocked(keys, kinds))
    cpp.append("")
    cpp.append("Variant %s::get_next_level(int64_t current_level) {" % CLASS)
    cpp.append("    int64_t next_level = current_level + 1;")
    cpp.append("    if (next_level > kLevelCount) {")
    cpp.append("        return Variant(); // Python: None (sudah level terakhir)")
    cpp.append("    }")
    cpp.append("    if (row_index(next_level) < 0) {")
    cpp.append("        return Variant(); // Python: config level berikutnya tidak ada")
    cpp.append("    }")
    cpp.append("    return Variant(next_level);")
    cpp.append("}")
    cpp.append("")
    cpp.extend(emit_catalog_signature(keys, kinds))
    cpp.append("")
    cpp.append("void %s::_bind_methods() {" % CLASS)
    bindings = [
        ("all_levels", []),
        ("get_level_config", ["level_number"]),
        ("get_level_count", []),
        ("is_level_unlocked", ["level_number", "completed_levels"]),
        ("get_next_level", ["current_level"]),
        ("build_row", ["index"]),
        ("row_index", ["level_number"]),
        ("py_contains", ["haystack", "needle"]),
        ("catalog_signature", []),
    ]
    for method, args in bindings:
        d_args = ", ".join(['"%s"' % method] + ['"%s"' % a for a in args])
        cpp.append('    ClassDB::bind_static_method("%s", D_METHOD(%s), &%s::%s);'
                   % (CLASS, d_args, CLASS, method))
    cpp.append("}")
    cpp.append("")
    return "\n".join(cpp)


# ══════════════════════════════════════════════════════════
#  Driver
# ══════════════════════════════════════════════════════════


def generate(check=False):
    tables, order, lines = parse_levels()
    levels = [(name, tables[name]) for name in order]
    keys, kinds = build_schema(levels)
    validate(levels, keys)

    header_text = emit_header(keys, kinds, len(levels))
    cpp_text = emit_cpp(levels, keys, kinds, lines)

    if check:
        stale = []
        for path, text in ((OUT_H, header_text), (OUT_CPP, cpp_text)):
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            if old != text:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            for rel in stale:
                print("[gen_levels_cpp] BASI: %s != hasil transpile levels/level_data.py" % rel)
            print("[gen_levels_cpp] regenerasi: python3 tools/gen_levels_cpp.py")
            return 1
        print("[gen_levels_cpp] PASS: levels_processor.h/.cpp ter-commit == hasil transpile "
              "(%d level, %d field, %d baris cpp)"
              % (len(levels), len(keys), cpp_text.count("\n") + 1))
        return 0

    OUT_H.parent.mkdir(parents=True, exist_ok=True)
    OUT_H.write_text(header_text, encoding="utf-8")
    OUT_CPP.write_text(cpp_text, encoding="utf-8")
    print("[gen_levels_cpp] wrote %s (%d baris)"
          % (OUT_H.relative_to(ROOT), header_text.count("\n") + 1))
    print("[gen_levels_cpp] wrote %s (%d baris, %d level, skema %d field: %s)"
          % (OUT_CPP.relative_to(ROOT), cpp_text.count("\n") + 1, len(levels), len(keys),
             ", ".join("%s=%s" % (k, kinds[k]) for k in keys)))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Transpile levels/level_data.py -> C++ GDExtension (godot++)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 kalau levels_processor.h/.cpp ter-commit basi")
    args = ap.parse_args()
    try:
        sys.exit(generate(check=args.check))
    except LevelError as exc:
        print("[gen_levels_cpp] GAGAL: %s" % exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
