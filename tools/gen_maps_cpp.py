#!/usr/bin/env python3
"""Transpile map_components/_bundle.py -> C++ GDExtension (godot++).

    python3 tools/gen_maps_cpp.py           # regenerasi
    python3 tools/gen_maps_cpp.py --check   # CI: berkas ter-commit harus identik

Bagian dari migrasi `map_components/` -> godot++ (FASE 35). Pola yang sama
dengan `tools/gen_levels_cpp.py` (levels -> MysticLevels): DATA dibangkitkan
dari AST Python yang menjadi sumber kebenaran, LOGIKA di-emit verbatim oleh
emitter dan dikunci fixture perilaku + cek struktural
(`tools/test_godot_map_data_parity.py`).

Yang dibangkitkan:

  godot/gdext/mystic_maps/src/maps_processor.h
  godot/gdext/mystic_maps/src/maps_processor.cpp

Cakupan (4 modul non-render; renderer pygame.draw.* tetap via bake Fase 3):

  1. palettes.py  -> kTileSize + tabel kPalettes (53 konstanta warna).
  2. themes.py    -> 54 tabel tema (skema UNION 77 kunci, urutan kunci per
     tema dipertahankan) + get_theme (fallback forest) + theme_names.
  3. PathGenerator -> make_curved_path + generate_lanes + generate_river.
     Waypoint dibaca dari AST (ekspresi Const/map_w/map_h/Add/Sub/FloorDiv),
     smoothness per panggilan ikut dari AST (top 10, mid 8, bot 10, river 10).
  4. DecorationGenerator.generate_all -> generate_decorations + replika
     CPython `random` (MT19937 + init_by_array; seed 42) + helper validasi.

Desain C++:

  * TABEL POD (`static const`, trivially destructible) — bukan `static
    Dictionary`: Variant statis di GDExtension didestruksi saat `dlclose`
    (crash klasik). Dictionary dibangun segar per panggilan; cache katalog
    dipegang MapDBLoader.gd.
  * Nilai tuple warna Python -> `Color(r/255, g/255, b/255)` (r8 round-trip
    bit-eksak); list 3 warna -> PackedColorArray; titik (int,int) -> Vector2.

Kontrak data yang ditegakkan generator (gagal keras, bukan diam-diam):

  * tiap *_THEME literal murni; tiap yang didefinisikan masuk THEMES dan
    sebaliknya (orphan/missing = level tidak akan pernah terasa temanya);
  * kind per kunci konsisten di SELURUH tema, kecuali campuran COLOR4/NIL
    (hanya `ambient_tint`: None di forest);
  * nilai tema hanya str/bool/int/tuple-3-int/tuple-4-int/list-3-tuple;
  * palet hanya tuple-3-int (+ TILE_SIZE int);
  * ekspresi waypoint hanya bentuk yang didukung (lihat _emit_coord).
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "map_components" / "_bundle.py"
OUT_H = ROOT / "godot" / "gdext" / "mystic_maps" / "src" / "maps_processor.h"
OUT_CPP = ROOT / "godot" / "gdext" / "mystic_maps" / "src" / "maps_processor.cpp"

CLASS = "MysticMaps"
LIBRARY = "mystic_maps"

# ══════════════════════════════════════════════════════════
#  Baca AST _bundle.py
# ══════════════════════════════════════════════════════════


class MapError(Exception):
    """Data map_components/_bundle.py tidak memenuhi kontrak generator."""


def parse_bundle():
    """Ambil palet, tema+urutan THEMES, dan node PathGenerator dari AST."""
    source = SRC.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SRC))

    palettes = []       # [(nama, nilai, lineno)] — urutan sumber
    themes = {}         # NAMA_THEME -> dict literal
    theme_lines = {}
    order = []          # [(kunci_thm, NAMA_THEME)] — urutan THEMES
    pathgen = None      # ast.ClassDef PathGenerator
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            nid = node.targets[0].id
            if nid.endswith("_THEME") and isinstance(node.value, ast.Dict):
                try:
                    themes[nid] = ast.literal_eval(node.value)
                except ValueError as exc:
                    raise MapError(
                        "%s:%d — %s bukan literal murni (generator menolak "
                        "menghitung ekspresi)" % (SRC.name, node.lineno, nid)
                    ) from exc
                theme_lines[nid] = node.lineno
            elif nid == "THEMES" and isinstance(node.value, ast.Dict):
                for key, val in zip(node.value.keys, node.value.values):
                    if not isinstance(val, ast.Name):
                        raise MapError(
                            "%s:%d — THEMES harus memetakan nama -> NAMA_THEME"
                            % (SRC.name, node.lineno))
                    order.append((ast.literal_eval(key), val.id))
            elif nid.isupper() and not nid.startswith("_"):
                try:
                    value = ast.literal_eval(node.value)
                except (ValueError, SyntaxError):
                    continue  # bukan konstanta data (abaikan)
                if isinstance(value, (tuple, int)) and not isinstance(value, bool):
                    palettes.append((nid, value, node.lineno))
        elif isinstance(node, ast.ClassDef) and node.name == "_NS_generators":
            for sub in node.body:
                if isinstance(sub, ast.ClassDef) and sub.name == "PathGenerator":
                    pathgen = sub
    if not themes:
        raise MapError("tidak ada *_THEME di %s" % SRC)
    if not order:
        raise MapError("THEMES tidak ditemukan di %s" % SRC)
    missing = [name for _, name in order if name not in themes]
    if missing:
        raise MapError("THEMES merujuk definisi yang tidak ada: %s" % ", ".join(missing))
    orphan = [name for name in themes if name not in [n for _, n in order]]
    if orphan:
        raise MapError("*_THEME didefinisikan tapi tidak masuk THEMES: %s" % ", ".join(sorted(orphan)))
    if pathgen is None:
        raise MapError("_NS_generators.PathGenerator tidak ditemukan di %s" % SRC)
    return palettes, themes, order, theme_lines, pathgen


# ══════════════════════════════════════════════════════════
#  Skema tema: union 77 kunci + kind per kunci
# ══════════════════════════════════════════════════════════

KIND_STR = "str"
KIND_BOOL = "bool"
KIND_INT = "int"
KIND_COLOR3 = "color3"
KIND_COLOR4 = "color4"
KIND_COLORLIST = "colorlist3"
KIND_NIL = "nil"


def _theme_value_kind(key, value, theme_name):
    if value is None:
        return KIND_NIL
    if isinstance(value, bool):
        return KIND_BOOL
    if isinstance(value, int):
        return KIND_INT
    if isinstance(value, str):
        return KIND_STR
    if isinstance(value, tuple):
        if len(value) == 3 and all(isinstance(c, int) for c in value):
            return KIND_COLOR3
        if len(value) == 4 and all(isinstance(c, int) for c in value):
            return KIND_COLOR4
        raise MapError("%s.%s — tuple %r bukan warna RGB/RGBA int"
                       % (theme_name, key, value))
    if isinstance(value, list):
        if len(value) == 3 and all(
                isinstance(c, tuple) and len(c) == 3
                and all(isinstance(x, int) for x in c) for c in value):
            return KIND_COLORLIST
        raise MapError("%s.%s — list %r bukan list-3-warna" % (theme_name, key, value))
    raise MapError("%s.%s — tipe %s tidak didukung generator"
                   % (theme_name, key, type(value).__name__))


def build_schema(ordered_themes):
    """(kunci union urutan first-seen, kind per kunci).

    Berbeda dengan levels (skema SERAGAM 17 field), 54 tema map TIDAK seragam:
    HAUNTED punya 22 kunci ekstra dan kehilangan 8 kunci has_*. C++ menyimpan
    entri per tema (bukan struct kolom), jadi skema union + urutan per tema
    adalah representasi yang setia — `theme.get(k, default)` di konsumen
    Python tetap bermakna sama karena kunci yang hilang memang tidak ada.
    """
    keys = []
    kinds = {}
    for const_name, _key, row in ordered_themes:
        for key, value in row.items():
            kind = _theme_value_kind(key, value, const_name)
            if key not in kinds:
                keys.append(key)
                kinds[key] = kind
                continue
            prev = kinds[key]
            if prev == kind:
                continue
            # Satu-satunya campuran yang diizinkan: COLOR4/NIL (ambient_tint:
            # None hanya di forest). Kolom POD per-entri membawa kind-nya
            # sendiri, jadi campuran ini tidak butuh kolom has_*.
            if sorted((prev, kind)) == [KIND_COLOR4, KIND_NIL]:
                kinds[key] = KIND_COLOR4
                continue
            raise MapError(
                "%s — kunci %s punya dua kind: %s dan %s. Samakan tipenya di "
                "map_components/_bundle.py atau perluas tools/gen_maps_cpp.py"
                % (const_name, key, prev, kind))
    return keys, kinds


def validate_palettes(palettes):
    tile = [p for p in palettes if p[0] == "TILE_SIZE"]
    if len(tile) != 1 or not isinstance(tile[0][1], int):
        raise MapError("TILE_SIZE harus tepat satu konstanta int")
    for name, value, lineno in palettes:
        if name == "TILE_SIZE":
            continue
        if not (isinstance(value, tuple) and len(value) == 3
                and all(isinstance(c, int) and 0 <= c <= 255 for c in value)):
            raise MapError("%s:%d — palet %s = %r bukan tuple RGB 0-255"
                           % (SRC.name, lineno, name, value))


# ══════════════════════════════════════════════════════════
#  Waypoint PathGenerator dari AST
# ══════════════════════════════════════════════════════════


def _coord_to_cpp(node):
    """Ekspresi koordinat waypoint -> string C++ (int64).

    Bentuk yang didukung (SEMUANYA yang ada di generate_lanes/generate_river
    hari ini — bentuk lain ditolak keras supaya waypoint baru tidak lolos
    diam-diam jadi angka yang salah):
      Const int, Name map_w/map_h, BinOp Add/Sub/FloorDiv, UnaryOp -Const.
    `// 2` menjadi `/ 2`: SAMA karena map_w/map_h selalu positif (ukuran
    layar); floor == trunc di wilayah non-negatif.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return str(node.value)
    if isinstance(node, ast.Name) and node.id in ("map_w", "map_h"):
        return node.id
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) \
            and isinstance(node.operand, ast.Constant):
        return "(-%s)" % _coord_to_cpp(node.operand)
    if isinstance(node, ast.BinOp):
        left = _coord_to_cpp(node.left)
        right = _coord_to_cpp(node.right)
        if isinstance(node.op, ast.Add):
            return "(%s + %s)" % (left, right)
        if isinstance(node.op, ast.Sub):
            return "(%s - %s)" % (left, right)
        if isinstance(node.op, ast.FloorDiv) and right == "2":
            return "(%s / 2)" % left
    raise MapError("ekspresi waypoint tak didukung: %s (perluas _coord_to_cpp "
                   "di tools/gen_maps_cpp.py)" % ast.dump(node))


def parse_paths(pathgen):
    """(lanes, river): lanes = [(nama, [(x,y) cpp], smoothness)] urutan kode.

    Nama lane (top/bot/mid) + urutan return dibaca dari AST generate_lanes,
    bukan hardcode: `top = make([...], smoothness=10)` -> ("top", ..., 10),
    `return top, mid, bot` -> urutan emit. generate_river -> satu list.
    """
    lanes = []
    lane_return = None
    river = None
    for item in pathgen.body:
        if not (isinstance(item, ast.FunctionDef) and item.name == "generate_lanes"):
            continue
        for stmt in ast.walk(item):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                    and isinstance(stmt.targets[0], ast.Name) \
                    and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if len(call.args) != 1 or not isinstance(call.args[0], ast.List):
                    continue
                smooth = None
                for kw in call.keywords:
                    if kw.arg == "smoothness" and isinstance(kw.value, ast.Constant):
                        smooth = kw.value.value
                if not isinstance(smooth, int):
                    raise MapError("generate_lanes.%s — smoothness harus int literal"
                                   % stmt.targets[0].id)
                pts = []
                for elt in call.args[0].elts:
                    if not (isinstance(elt, ast.Tuple) and len(elt.elts) == 2):
                        raise MapError("generate_lanes.%s — waypoint bukan tuple-2"
                                       % stmt.targets[0].id)
                    pts.append((_coord_to_cpp(elt.elts[0]), _coord_to_cpp(elt.elts[1])))
                lanes.append((stmt.targets[0].id, pts, smooth))
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Tuple):
                lane_return = []
                for elt in stmt.value.elts:
                    if not isinstance(elt, ast.Name):
                        raise MapError("generate_lanes — return harus tuple nama lane")
                    lane_return.append(elt.id)
    for item in pathgen.body:
        if not (isinstance(item, ast.FunctionDef) and item.name == "generate_river"):
            continue
        for stmt in ast.walk(item):
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                smooth = None
                for kw in call.keywords:
                    if kw.arg == "smoothness" and isinstance(kw.value, ast.Constant):
                        smooth = kw.value.value
                if not isinstance(smooth, int):
                    raise MapError("generate_river — smoothness harus int literal")
                pts = []
                for elt in call.args[0].elts:
                    pts.append((_coord_to_cpp(elt.elts[0]), _coord_to_cpp(elt.elts[1])))
                river = (pts, smooth)
    if not lanes or lane_return is None or river is None:
        raise MapError("gagal mem-parsing generate_lanes/generate_river dari AST")
    lane_names = [name for name, _, _ in lanes]
    if sorted(lane_return) != sorted(lane_names):
        raise MapError("return generate_lanes %s != lane yang didefinisikan %s"
                       % (lane_return, lane_names))
    by_name = {name: (pts, smooth) for name, pts, smooth in lanes}
    return [(name, by_name[name][0], by_name[name][1]) for name in lane_return], river


# ══════════════════════════════════════════════════════════
#  Emisi C++
# ══════════════════════════════════════════════════════════

BANNER = (
    "// ═══ GENERATED — JANGAN SUNTING TANGAN ═══\n"
    "// Sumber    : map_components/_bundle.py (palettes, themes, generators)\n"
    "// Generator : tools/gen_maps_cpp.py (AST Python -> C++, bukan terjemahan tangan)\n"
    "// Regenerasi: python3 tools/gen_maps_cpp.py\n"
    "// Cek CI    : python3 tools/gen_maps_cpp.py --check\n"
    "// Desain    : docs/MAPS_GODOTPP.md\n"
)

KIND_CPP = {
    KIND_STR: "KIND_STR",
    KIND_BOOL: "KIND_BOOL",
    KIND_INT: "KIND_INT",
    KIND_COLOR3: "KIND_COLOR3",
    KIND_COLOR4: "KIND_COLOR4",
    KIND_COLORLIST: "KIND_COLORLIST",
    KIND_NIL: "KIND_NIL",
}

_SIMPLE_ESCAPES = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def c_string(text):
    """Literal string C++ ASCII-murni (oktal untuk non-ASCII, seperti levels)."""
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


def emit_header(theme_count, key_count):
    h = []
    h.append("#ifndef MYSTIC_MAPS_PROCESSOR_H")
    h.append("#define MYSTIC_MAPS_PROCESSOR_H")
    h.append("")
    h.append(BANNER.rstrip("\n"))
    h.append("//")
    h.append("// Port map_components/_bundle.py (%d tema, %d kunci union, PathGenerator +"
             % (theme_count, key_count))
    h.append("// DecorationGenerator) ke Godot C++ GDExtension. API = permukaan modul")
    h.append("// palettes/themes/generators: konstanta palet, get_theme, make_curved_path,")
    h.append("// generate_lanes, generate_river, generate_decorations.")
    h.append("")
    h.append("#include <godot_cpp/classes/ref_counted.hpp>")
    h.append("#include <godot_cpp/core/class_db.hpp>")
    h.append("#include <godot_cpp/variant/array.hpp>")
    h.append("#include <godot_cpp/variant/color.hpp>")
    h.append("#include <godot_cpp/variant/dictionary.hpp>")
    h.append("#include <godot_cpp/variant/packed_color_array.hpp>")
    h.append("#include <godot_cpp/variant/packed_vector2_array.hpp>")
    h.append("#include <godot_cpp/variant/string.hpp>")
    h.append("#include <godot_cpp/variant/variant.hpp>")
    h.append("#include <godot_cpp/variant/vector2.hpp>")
    h.append("#include <cstdint>")
    h.append("")
    h.append("namespace godot {")
    h.append("")
    h.append("class %s : public RefCounted {" % CLASS)
    h.append("    GDCLASS(%s, RefCounted);" % CLASS)
    h.append("")
    h.append("public:")
    h.append("    // ── palettes.py ──")
    h.append("    static int64_t tile_size();")
    h.append("    static Dictionary palettes();")
    h.append("    // ── themes.py ──")
    h.append("    static Array theme_names();")
    h.append("    static int64_t theme_count();")
    h.append("    static Dictionary get_theme(const String &theme_name);")
    h.append("    static Dictionary all_themes();")
    h.append("    static String catalog_signature();")
    h.append("    // ── generators.py: PathGenerator ──")
    h.append("    static PackedVector2Array make_curved_path(const PackedVector2Array &waypoints, int64_t smoothness);")
    h.append("    static Dictionary generate_lanes(int64_t map_w, int64_t map_h);")
    h.append("    static PackedVector2Array generate_river(int64_t map_w, int64_t map_h);")
    h.append("    // ── generators.py: DecorationGenerator ──")
    h.append("    static Dictionary generate_decorations(int64_t map_w, int64_t map_h,")
    h.append("        const PackedVector2Array &lane_points, const PackedVector2Array &river_points,")
    h.append("        const Array &shop_positions);")
    h.append("")
    h.append("    // ── helper (dipakai loader + harness paritas; juga di-bind) ──")
    h.append("    // Tema ke-`index` sebagai Dictionary segar (urutan kunci = urutan literal")
    h.append("    // dict Python tema itu). Index di luar jangkauan -> Dictionary kosong.")
    h.append("    static Dictionary build_theme(int64_t index);")
    h.append("    // Indeks tema untuk nama, -1 kalau tidak ada (scan linear = paritas")
    h.append("    // THEMES.get; get_theme memakai forest untuk -1).")
    h.append("    static int64_t theme_index(const String &theme_name);")
    h.append("")
    h.append("protected:")
    h.append("    static void _bind_methods();")
    h.append("};")
    h.append("")
    h.append("} // namespace godot")
    h.append("")
    h.append("#endif // MYSTIC_MAPS_PROCESSOR_H")
    h.append("")
    return "\n".join(h)


# ── Replika CPython random (di-emit verbatim; dikunci fixture perilaku) ──
# Spike pra-migrasi membuktikan: `random.seed(42)` CPython memakai
# init_by_array([42]) — BUKAN init_genrand(42) — sehingga std::mt19937(42)
# menghasilkan stream yang SALAH (2746317213 vs 1608637542 di draw pertama).
# Lima stream (getrandbits/randint/choice/uniform/random) diverifikasi
# bit-eksak vs CPython 3.11 sebelum generator ini ditulis.

MT_CODE = r"""
// ═══ Replika CPython `random` (dipakai DecorationGenerator) ═══
// MT19937 manual + init_by_array untuk seed int — std::mt19937(seed) SALAH
// untuk keperluan ini (spike: draw pertama 1608637542 vs 2746317213 Python).
// getrandbits/randbelow/randint/choice meniru Modules/_randommodule.c +
// Lib/random.py (_randbelow: rejection sampling, k = bit_length).
struct PyMt {
    static const int N = 624;
    static const int M = 397;
    uint32_t mt[624];
    int mti;

    void init_genrand(uint32_t s) {
        mt[0] = s;
        for (mti = 1; mti < N; mti++) {
            mt[mti] = (1812433253UL * (mt[mti - 1] ^ (mt[mti - 1] >> 30)) + (uint32_t)mti);
            mt[mti] &= 0xffffffffUL;
        }
    }

    void init_by_array(const uint32_t *init_key, int key_length) {
        init_genrand(19650218UL);
        int i = 1;
        int j = 0;
        int k = (N > key_length ? N : key_length);
        for (; k; k--) {
            mt[i] = (mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525UL)) + init_key[j] + (uint32_t)j;
            mt[i] &= 0xffffffffUL;
            i++;
            j++;
            if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
            if (j >= key_length) { j = 0; }
        }
        for (k = N - 1; k; k--) {
            mt[i] = (mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941UL)) - (uint32_t)i;
            mt[i] &= 0xffffffffUL;
            i++;
            if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
        }
        mt[0] = 0x80000000UL;
    }

    void seed_int(uint32_t n) {
        const uint32_t key[1] = { n };
        init_by_array(key, 1);
    }

    uint32_t genrand_int32() {
        static const uint32_t mag01[2] = { 0x0UL, 0x9908b0dfUL };
        if (mti >= N) {
            int kk;
            for (kk = 0; kk < N - M; kk++) {
                uint32_t y = (mt[kk] & 0x80000000UL) | (mt[kk + 1] & 0x7fffffffUL);
                mt[kk] = mt[kk + M] ^ (y >> 1) ^ mag01[y & 0x1UL];
            }
            for (; kk < N - 1; kk++) {
                uint32_t y = (mt[kk] & 0x80000000UL) | (mt[kk + 1] & 0x7fffffffUL);
                mt[kk] = mt[kk + (M - N)] ^ (y >> 1) ^ mag01[y & 0x1UL];
            }
            uint32_t y = (mt[N - 1] & 0x80000000UL) | (mt[0] & 0x7fffffffUL);
            mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ mag01[y & 0x1UL];
            mti = 0;
        }
        uint32_t y = mt[mti++];
        y ^= (y >> 11);
        y ^= (y << 7) & 0x9d2c5680UL;
        y ^= (y << 15) & 0xefc60000UL;
        y ^= (y >> 18);
        return y;
    }

    // getrandbits(k), k <= 32 — persis _randommodule.c.
    uint32_t getrandbits(int k) {
        int words = (k + 31) / 32;
        uint64_t r = 0;
        for (int i = 0; i < words; i++) {
            r = (r << 32) | genrand_int32();
        }
        r >>= words * 32 - k;
        return (uint32_t)r;
    }

    // _randbelow(n) — Lib/random.py: k = bit_length, rejection loop.
    uint32_t randbelow(uint32_t n) {
        int k = 0;
        for (uint32_t t = n; t; t >>= 1) {
            k++;
        }
        uint32_t r = getrandbits(k);
        while (r >= n) {
            r = getrandbits(k);
        }
        return r;
    }

    // randint(a, b) = randrange(a, b+1) = _randbelow(b-a+1)+a.
    int64_t randint(int64_t a, int64_t b) {
        return a + (int64_t)randbelow((uint32_t)(b - a + 1));
    }

    // choice(seq) = seq[_randbelow(len(seq))] — indeksnya saja.
    int64_t choice_idx(int64_t n) {
        return (int64_t)randbelow((uint32_t)n);
    }
};
"""


def emit_entry_literal(key, kind, value, colorlist_index):
    """Satu ThemeEntry C++: {kunci, kind, v0..v3, string, list_idx}."""
    if kind == KIND_STR:
        return '{"%s", KIND_STR, 0, 0, 0, 0, %s, -1}' % (key, c_string(value))
    if kind == KIND_BOOL:
        return '{"%s", KIND_BOOL, %d, 0, 0, 0, nullptr, -1}' % (key, 1 if value else 0)
    if kind == KIND_INT:
        return '{"%s", KIND_INT, %d, 0, 0, 0, nullptr, -1}' % (key, value)
    if kind == KIND_COLOR3:
        r, g, b = value
        return '{"%s", KIND_COLOR3, %d, %d, %d, 0, nullptr, -1}' % (key, r, g, b)
    if kind == KIND_COLOR4:
        r, g, b, a = value
        return '{"%s", KIND_COLOR4, %d, %d, %d, %d, nullptr, -1}' % (key, r, g, b, a)
    if kind == KIND_COLORLIST:
        return '{"%s", KIND_COLORLIST, 0, 0, 0, 0, nullptr, %d}' % (key, colorlist_index)
    if kind == KIND_NIL:
        return '{"%s", KIND_NIL, 0, 0, 0, 0, nullptr, -1}' % key
    raise MapError("kind tak dikenal: %s" % kind)


def emit_cpp(palettes, ordered_themes, theme_lines, lanes, river):
    cpp = []
    cpp.append(BANNER.rstrip("\n"))
    cpp.append('#include "maps_processor.h"')
    cpp.append("")
    cpp.append("#include <cmath>")
    cpp.append("#include <cstddef>")
    cpp.append("#include <cstdint>")
    cpp.append("#include <vector>")
    cpp.append("")
    cpp.append("using namespace godot;")
    cpp.append("")
    cpp.append("namespace {")
    cpp.append("")
    cpp.append("// ── palettes.py ──")
    cpp.append("struct PalEntry {")
    cpp.append("    const char *name;")
    cpp.append("    int32_t r, g, b;")
    cpp.append("};")
    cpp.append("")
    tile_size = [v for n, v, _ in palettes if n == "TILE_SIZE"][0]
    colors = [(n, v, ln) for n, v, ln in palettes if n != "TILE_SIZE"]
    cpp.append("const PalEntry kPalettes[] = {")
    for name, (r, g, b), lineno in colors:
        cpp.append('    {"%s", %d, %d, %d}, // %s:%d' % (name, r, g, b, SRC.name, lineno))
    cpp.append("};")
    cpp.append("const int64_t kPaletteCount = %d;" % len(colors))
    cpp.append("const int64_t kTileSize = %d; // TILE_SIZE — %s" % (tile_size, SRC.name))
    cpp.append("")
    cpp.append("// ── themes.py ──")
    cpp.append("// Skema UNION: tiap tema menyimpan entrinya sendiri (urutan = urutan")
    cpp.append("// literal dict Python tema itu) karena 54 tema TIDAK berskema seragam")
    cpp.append("// (HAUNTED punya 22 kunci ekstra, kehilangan 8 kunci has_*).")
    cpp.append("enum ThemeKind : uint8_t {")
    cpp.append("    KIND_STR = 0,")
    cpp.append("    KIND_BOOL = 1,")
    cpp.append("    KIND_INT = 2,")
    cpp.append("    KIND_COLOR3 = 3,")
    cpp.append("    KIND_COLOR4 = 4,")
    cpp.append("    KIND_COLORLIST = 5,")
    cpp.append("    KIND_NIL = 6,")
    cpp.append("};")
    cpp.append("")
    cpp.append("struct ThemeEntry {")
    cpp.append("    const char *key;")
    cpp.append("    uint8_t kind;")
    cpp.append("    int32_t v0, v1, v2, v3; // BOOL/INT: v0; COLOR3: v0..v2; COLOR4: v0..v3")
    cpp.append("    const char *s;          // STR (nullptr selain itu)")
    cpp.append("    int32_t list;           // COLORLIST: indeks ke kColorLists (-1 selain itu)")
    cpp.append("};")
    cpp.append("")

    # Tabel list warna partikel: 2 per tema (radiant, dire), urutan tema.
    cpp.append("// Daftar warna partikel (particle_colors_radiant/dire): 9 int per list,")
    cpp.append("// 2 list per tema, urutan = urutan THEMES.")
    cpp.append("const int32_t kColorLists[][9] = {")
    list_idx = 0
    for const_name, key, row in ordered_themes:
        for list_key in ("particle_colors_radiant", "particle_colors_dire"):
            triples = row[list_key]
            flat = ", ".join("%d, %d, %d" % t for t in triples)
            cpp.append("    {%s}, // %s.%s (#%d)" % (flat, key, list_key, list_idx))
            list_idx += 1
    cpp.append("};")
    cpp.append("")

    list_cursor = 0
    for i, (const_name, key, row) in enumerate(ordered_themes):
        cpp.append("// %s (%s:%d) — %d kunci" % (const_name, SRC.name, theme_lines[const_name], len(row)))
        cpp.append("const ThemeEntry kTheme%d[] = {" % i)
        for tkey, value in row.items():
            kind = _theme_value_kind(tkey, value, const_name)
            idx = -1
            if kind == KIND_COLORLIST:
                idx = list_cursor
                list_cursor += 1
            cpp.append("    %s," % emit_entry_literal(tkey, kind, value, idx))
        cpp.append("};")
        cpp.append("")

    cpp.append("// Urutan = THEMES di %s." % SRC.name)
    cpp.append("const char *const kThemeNames[] = {")
    for _const_name, key, _row in ordered_themes:
        cpp.append("    %s," % c_string(key))
    cpp.append("};")
    cpp.append("const ThemeEntry *const kThemes[] = {")
    for i in range(len(ordered_themes)):
        cpp.append("    kTheme%d," % i)
    cpp.append("};")
    cpp.append("const int64_t kThemeEntryCounts[] = {")
    for _const_name, _key, row in ordered_themes:
        cpp.append("    %d," % len(row))
    cpp.append("};")
    cpp.append("const int64_t kThemeCount = %d;" % len(ordered_themes))
    forest_idx = [i for i, (_, key, _) in enumerate(ordered_themes) if key == "forest"]
    if len(forest_idx) != 1:
        raise MapError("kunci tema 'forest' (fallback get_theme) harus tepat satu")
    cpp.append("const int64_t kForestIndex = %d; // THEMES.get(nama, FOREST_THEME)" % forest_idx[0])
    cpp.append("")

    # ── replika random + helper dekor ──
    cpp.append(MT_CODE.strip("\n"))
    cpp.append("")
    cpp.append("// ═══ Helper DecorationGenerator (port generate_all + validator) ═══")
    cpp.append("// Urutan draw RNG, ambang jarak, dan jumlah attempt = persis")
    cpp.append("// _bundle.py; dicek struktural tools/test_godot_map_data_parity.py dan")
    cpp.append("// dikunci perilaku oleh fixture map_data.json.")
    cpp.append("static double lane_threshold_y(int64_t x, int64_t map_w, int64_t map_h) {")
    cpp.append("    // threshold_y = 200 + (map_h - 400) * x / map_w — perkalian int")
    cpp.append("    // eksak lalu SATU pembulatan divisi, persis urutan Python.")
    cpp.append("    return 200.0 + (double)((map_h - 400) * x) / (double)map_w;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool is_radiant(int64_t x, int64_t y, int64_t map_w, int64_t map_h) {")
    cpp.append("    return (double)y > lane_threshold_y(x, map_w, map_h) + 20.0;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool is_dire(int64_t x, int64_t y, int64_t map_w, int64_t map_h) {")
    cpp.append("    return (double)y < lane_threshold_y(x, map_w, map_h) - 20.0;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool too_close_to_lane(const PackedVector2Array &lane_points, int64_t x, int64_t y, double min_dist) {")
    cpp.append("    for (int64_t i = 0; i < lane_points.size(); i++) {")
    cpp.append("        const Vector2 p = lane_points[i];")
    cpp.append("        if (std::hypot((double)x - (double)p.x, (double)y - (double)p.y) < min_dist) {")
    cpp.append("            return true;")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    return false;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool too_close_to_river(const PackedVector2Array &river_points, int64_t x, int64_t y, double min_dist) {")
    cpp.append("    for (int64_t i = 0; i < river_points.size(); i++) {")
    cpp.append("        const Vector2 p = river_points[i];")
    cpp.append("        if (std::hypot((double)x - (double)p.x, (double)y - (double)p.y) < min_dist) {")
    cpp.append("            return true;")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    return false;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool too_close_to_base(int64_t x, int64_t y, int64_t map_w, int64_t map_h) {")
    cpp.append("    // BUG ASLI DIREPLIKA: suku kedua = map_h - 120 - (map_h - y) = y - 120,")
    cpp.append("    // jadi lingkaran pertama berpusat di (120, 120) — sudut kiri-atas —")
    cpp.append("    // BUKAN di base Radiant (120, map_h-120). Jangan \"diperbaiki\": paritas")
    cpp.append("    // berarti dekor Python dan C++ lolos filter yang SAMA.")
    cpp.append("    if (std::hypot((double)(x - 120), (double)(map_h - 120 - (map_h - y))) < 120.0) {")
    cpp.append("        return true;")
    cpp.append("    }")
    cpp.append("    if (std::hypot((double)(x - (map_w - 120)), (double)(y - 120)) < 120.0) {")
    cpp.append("        return true;")
    cpp.append("    }")
    cpp.append("    return false;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool too_close_to_shop(const Array &shop_positions, int64_t x, int64_t y, double min_dist) {")
    cpp.append("    for (int64_t i = 0; i < shop_positions.size(); i++) {")
    cpp.append("        const Vector2 p = shop_positions[i];")
    cpp.append("        if (std::hypot((double)x - (double)p.x, (double)y - (double)p.y) < min_dist) {")
    cpp.append("            return true;")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    return false;")
    cpp.append("}")
    cpp.append("")
    cpp.append("static bool is_valid_spot(const PackedVector2Array &lane_points,")
    cpp.append("        const PackedVector2Array &river_points, const Array &shop_positions,")
    cpp.append("        int64_t map_w, int64_t map_h, int64_t x, int64_t y, double min_lane) {")
    cpp.append("    if (too_close_to_lane(lane_points, x, y, min_lane)) {")
    cpp.append("        return false;")
    cpp.append("    }")
    cpp.append("    if (too_close_to_river(river_points, x, y, 25.0)) {")
    cpp.append("        return false;")
    cpp.append("    }")
    cpp.append("    if (too_close_to_base(x, y, map_w, map_h)) {")
    cpp.append("        return false;")
    cpp.append("    }")
    cpp.append("    if (too_close_to_shop(shop_positions, x, y, 70.0)) {")
    cpp.append("        return false;")
    cpp.append("    }")
    cpp.append("    return true;")
    cpp.append("}")
    cpp.append("")
    cpp.append("// Opsi random.choice generate_all — urutan = urutan kemunculan di _bundle.py.")
    cpp.append("// (Oracle membandingkan sekuens literal ini dengan AST Python.)")
    cpp.append("static const int64_t kChDarkTreeSize[] = { 16, 20, 24 };")
    cpp.append("static const int64_t kChDarkTreeVariant[] = { 0, 0, 1, 1, 2 };")
    cpp.append("static const int64_t kChDeadTreeSize[] = { 14, 18, 22 };")
    cpp.append("static const char *const kChRuinVariant[] = { \"pillar\", \"arch\", \"wall\" };")
    cpp.append("static const char *const kChBoneType[] = { \"skull\", \"rib\", \"skeleton\" };")
    cpp.append("static const int32_t kChMushDire[][3] = { { 140, 30, 30 }, { 100, 20, 60 }, { 80, 40, 80 } };")
    cpp.append("static const int32_t kChMushRadiant[][3] = { { 60, 80, 150 }, { 100, 60, 130 }, { 140, 50, 100 } };")
    cpp.append("static const int64_t kChRockSize[] = { 12, 16, 20 };")
    cpp.append("static const int64_t kChBushSize[] = { 12, 16 };")
    crystal_l = [v for n, v, _ in palettes if n == "CRYSTAL_BLUE_L"][0]
    cpp.append("static const int32_t kChFlower[][3] = { { %d, %d, %d }, { 150, 100, 200 },"
               % crystal_l)
    cpp.append("        { 100, 200, 150 }, { 255, 200, 100 } }; // [0] = CRYSTAL_BLUE_L palettes.py")
    cpp.append("static const int64_t kChLandmark[] = { 0, 1, 2, 3 };")
    cpp.append("")
    cpp.append("static Color rgb(int32_t r, int32_t g, int32_t b) {")
    cpp.append("    return Color((float)r / 255.0f, (float)g / 255.0f, (float)b / 255.0f);")
    cpp.append("}")
    cpp.append("")
    cpp.append("static void push_point(Array &out, int64_t x, int64_t y) {")
    cpp.append("    Array e; e.resize(2); e[0] = x; e[1] = y; out.push_back(e);")
    cpp.append("}")
    cpp.append("")
    cpp.append("} // namespace")
    cpp.append("")

    # ── builder tema + palet ──
    cpp.append("static void push_theme_entry(Dictionary &d, const ThemeEntry &e) {")
    cpp.append('    const String key(e.key);')
    cpp.append("    switch (e.kind) {")
    cpp.append("        case KIND_STR: d[key] = String(e.s); break;")
    cpp.append("        case KIND_BOOL: d[key] = (e.v0 != 0); break;")
    cpp.append("        case KIND_INT: d[key] = (int64_t)e.v0; break;")
    cpp.append("        case KIND_COLOR3: d[key] = rgb(e.v0, e.v1, e.v2); break;")
    cpp.append("        case KIND_COLOR4:")
    cpp.append("            d[key] = Color((float)e.v0 / 255.0f, (float)e.v1 / 255.0f,")
    cpp.append("                    (float)e.v2 / 255.0f, (float)e.v3 / 255.0f);")
    cpp.append("            break;")
    cpp.append("        case KIND_COLORLIST: {")
    cpp.append("            PackedColorArray cols;")
    cpp.append("            cols.resize(3);")
    cpp.append("            for (int64_t i = 0; i < 3; i++) {")
    cpp.append("                cols[i] = rgb(kColorLists[e.list][i * 3],")
    cpp.append("                        kColorLists[e.list][i * 3 + 1], kColorLists[e.list][i * 3 + 2]);")
    cpp.append("            }")
    cpp.append("            d[key] = cols;")
    cpp.append("            break;")
    cpp.append("        }")
    cpp.append("        case KIND_NIL: d[key] = Variant(); break; // Python: None")
    cpp.append("    }")
    cpp.append("}")
    cpp.append("")
    cpp.append("int64_t %s::tile_size() {" % CLASS)
    cpp.append("    return kTileSize;")
    cpp.append("}")
    cpp.append("")
    cpp.append("Dictionary %s::palettes() {" % CLASS)
    cpp.append("    Dictionary d;")
    cpp.append("    for (int64_t i = 0; i < kPaletteCount; i++) {")
    cpp.append("        d[String(kPalettes[i].name)] = rgb(kPalettes[i].r, kPalettes[i].g, kPalettes[i].b);")
    cpp.append("    }")
    cpp.append("    return d;")
    cpp.append("}")
    cpp.append("")
    cpp.append("Dictionary %s::build_theme(int64_t index) {" % CLASS)
    cpp.append("    if (index < 0 || index >= kThemeCount) {")
    cpp.append("        return Dictionary();")
    cpp.append("    }")
    cpp.append("    Dictionary d;")
    cpp.append("    for (int64_t i = 0; i < kThemeEntryCounts[index]; i++) {")
    cpp.append("        push_theme_entry(d, kThemes[index][i]);")
    cpp.append("    }")
    cpp.append("    return d;")
    cpp.append("}")
    cpp.append("")
    cpp.append("int64_t %s::theme_index(const String &theme_name) {" % CLASS)
    cpp.append("    for (int64_t i = 0; i < kThemeCount; i++) {")
    cpp.append("        if (theme_name == String(kThemeNames[i])) {")
    cpp.append("            return i;")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    return -1;")
    cpp.append("}")
    cpp.append("")
    cpp.append("Array %s::theme_names() {" % CLASS)
    cpp.append("    Array out;")
    cpp.append("    out.resize(kThemeCount);")
    cpp.append("    for (int64_t i = 0; i < kThemeCount; i++) {")
    cpp.append("        out[i] = String(kThemeNames[i]);")
    cpp.append("    }")
    cpp.append("    return out;")
    cpp.append("}")
    cpp.append("")
    cpp.append("int64_t %s::theme_count() {" % CLASS)
    cpp.append("    return kThemeCount;")
    cpp.append("}")
    cpp.append("")
    cpp.append("Dictionary %s::get_theme(const String &theme_name) {" % CLASS)
    cpp.append("    // THEMES.get(theme_name, FOREST_THEME) — selalu Dictionary segar")
    cpp.append("    // (Python mengembalikan objek live yang BISA dimutasi; tidak ada")
    cpp.append("    // konsumen Godot yang memutasi — diaudit saat migrasi).")
    cpp.append("    const int64_t index = theme_index(theme_name);")
    cpp.append("    return build_theme(index < 0 ? kForestIndex : index);")
    cpp.append("}")
    cpp.append("")
    cpp.append("Dictionary %s::all_themes() {" % CLASS)
    cpp.append("    Dictionary d;")
    cpp.append("    for (int64_t i = 0; i < kThemeCount; i++) {")
    cpp.append("        d[String(kThemeNames[i])] = build_theme(i);")
    cpp.append("    }")
    cpp.append("    return d;")
    cpp.append("}")
    cpp.append("")
    cpp.append("String %s::catalog_signature() {" % CLASS)
    cpp.append('    // "<jumlah>:<awal>-<akhir>:<total entri>" — bukti lib memuat tabel')
    cpp.append("    // generasi yang sama dengan data repo.")
    cpp.append("    int64_t total = 0;")
    cpp.append("    for (int64_t i = 0; i < kThemeCount; i++) {")
    cpp.append("        total += kThemeEntryCounts[i];")
    cpp.append("    }")
    cpp.append('    String sig = String::num_int64(kThemeCount) + ":";')
    cpp.append("    if (kThemeCount > 0) {")
    cpp.append('        sig += String(kThemeNames[0]) + "-" + String(kThemeNames[kThemeCount - 1]);')
    cpp.append("    }")
    cpp.append('    sig += ":" + String::num_int64(total);')
    cpp.append("    return sig;")
    cpp.append("}")

    # ── PathGenerator ──
    cpp.append("")
    cpp.append("PackedVector2Array %s::make_curved_path(const PackedVector2Array &waypoints, int64_t smoothness) {" % CLASS)
    cpp.append("    // Catmull-Rom — port make_curved_path: urutan operasi double SAMA")
    cpp.append("    // persis (t3 = t*t*t, bukan t2*t), lalu int() = trunc ke nol.")
    cpp.append("    if (waypoints.size() < 2) {")
    cpp.append("        return waypoints; // Python: objek SAMA; di sini salinan (deviasi)")
    cpp.append("    }")
    cpp.append("    std::vector<Vector2> pts;")
    cpp.append("    pts.reserve((size_t)waypoints.size() + 2);")
    cpp.append("    pts.push_back(waypoints[0]);")
    cpp.append("    for (int64_t i = 0; i < waypoints.size(); i++) {")
    cpp.append("        pts.push_back(waypoints[i]);")
    cpp.append("    }")
    cpp.append("    pts.push_back(waypoints[waypoints.size() - 1]);")
    cpp.append("    PackedVector2Array out;")
    cpp.append("    for (size_t i = 0; i + 3 < pts.size(); i++) { // range(len(pts) - 3)")
    cpp.append("        const Vector2 p0 = pts[i];")
    cpp.append("        const Vector2 p1 = pts[i + 1];")
    cpp.append("        const Vector2 p2 = pts[i + 2];")
    cpp.append("        const Vector2 p3 = pts[i + 3];")
    cpp.append("        for (int64_t step = 0; step < smoothness; step++) {")
    cpp.append("            const double t = (double)step / (double)smoothness;")
    cpp.append("            const double t2 = t * t;")
    cpp.append("            const double t3 = t * t * t;")
    cpp.append("            const double x = 0.5 * ((2.0 * (double)p1.x) +")
    cpp.append("                    (-(double)p0.x + (double)p2.x) * t +")
    cpp.append("                    (2.0 * (double)p0.x - 5.0 * (double)p1.x + 4.0 * (double)p2.x - (double)p3.x) * t2 +")
    cpp.append("                    (-(double)p0.x + 3.0 * (double)p1.x - 3.0 * (double)p2.x + (double)p3.x) * t3);")
    cpp.append("            const double y = 0.5 * ((2.0 * (double)p1.y) +")
    cpp.append("                    (-(double)p0.y + (double)p2.y) * t +")
    cpp.append("                    (2.0 * (double)p0.y - 5.0 * (double)p1.y + 4.0 * (double)p2.y - (double)p3.y) * t2 +")
    cpp.append("                    (-(double)p0.y + 3.0 * (double)p1.y - 3.0 * (double)p2.y + (double)p3.y) * t3);")
    cpp.append("            out.append(Vector2((float)(int32_t)x, (float)(int32_t)y));")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    out.append(waypoints[waypoints.size() - 1]);")
    cpp.append("    return out;")
    cpp.append("}")

    def emit_waypoints(var, pts):
        cpp.append("    PackedVector2Array %s;" % var)
        for x, y in pts:
            cpp.append("    %s.append(Vector2((float)(%s), (float)(%s)));" % (var, x, y))

    cpp.append("")
    cpp.append("Dictionary %s::generate_lanes(int64_t map_w, int64_t map_h) {" % CLASS)
    for name, pts, _smooth in lanes:
        emit_waypoints("lane_" + name, pts)
    cpp.append("    Dictionary d;")
    for name, _pts, smooth in lanes:
        cpp.append('    d["%s"] = make_curved_path(lane_%s, %d);' % (name, name, smooth))
    cpp.append("    return d;")
    cpp.append("}")
    cpp.append("")
    cpp.append("PackedVector2Array %s::generate_river(int64_t map_w, int64_t map_h) {" % CLASS)
    emit_waypoints("pts", river[0])
    cpp.append("    return make_curved_path(pts, %d);" % river[1])
    cpp.append("}")

    # ── DecorationGenerator.generate_all ──
    cpp.append("")
    cpp.append("Dictionary %s::generate_decorations(int64_t map_w, int64_t map_h," % CLASS)
    cpp.append("        const PackedVector2Array &lane_points, const PackedVector2Array &river_points,")
    cpp.append("        const Array &shop_positions) {")
    cpp.append("    // Port generate_all: seed 42 -> 14 loop -> random.seed() akhir (no-op")
    cpp.append("    // yang TIDAK direplika: state RNG lokal per panggilan, efek globalnya")
    cpp.append("    // tak teramati dari output). TILE_SIZE = kTileSize.")
    cpp.append("    PyMt rng;")
    cpp.append("    rng.seed_int(42);")
    cpp.append("    const int64_t TS = kTileSize;")
    cpp.append("    const int64_t nx = map_w / TS - 3;")
    cpp.append("    const int64_t nx2 = map_w / TS - 2;")
    cpp.append("    const int64_t ny = map_h / TS - 3;")
    cpp.append("    const int64_t ny2 = map_h / TS - 2;")
    cpp.append("    Array dark_trees; Array dead_trees; Array gravestones;")
    cpp.append("    Array crystals_blue; Array crystals_red; Array ancient_ruins;")
    cpp.append("    Array bones; Array mushrooms_dark; Array rocks_mossy;")
    cpp.append("    Array dark_bushes; Array glow_flowers; Array spike_traps;")
    cpp.append("    Array torch_stones; Array boss_landmarks;")
    cpp.append("    // ─── DARK TREES (radiant) — 45 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 45; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(2, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(2, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_radiant(x, y, map_w, map_h)) {")
    cpp.append("            const int64_t size = kChDarkTreeSize[rng.choice_idx(3)];")
    cpp.append("            const int64_t variant = kChDarkTreeVariant[rng.choice_idx(5)];")
    cpp.append("            Array e; e.resize(4); e[0] = x; e[1] = y; e[2] = size; e[3] = variant;")
    cpp.append("            dark_trees.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── DEAD TREES (dire) — 35 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 35; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(2, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(2, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_dire(x, y, map_w, map_h)) {")
    cpp.append("            const int64_t size = kChDeadTreeSize[rng.choice_idx(3)];")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;")
    cpp.append("            dead_trees.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── GRAVESTONES (dire) — 12 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 12; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_dire(x, y, map_w, map_h)) {")
    cpp.append("            push_point(gravestones, x, y);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── BLUE CRYSTALS (radiant) — 15 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 15; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_radiant(x, y, map_w, map_h)) {")
    cpp.append("            const int64_t size = rng.randint(8, 14);")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;")
    cpp.append("            crystals_blue.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── RED CRYSTALS (dire) — 12 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 12; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_dire(x, y, map_w, map_h)) {")
    cpp.append("            const int64_t size = rng.randint(6, 12);")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;")
    cpp.append("            crystals_red.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── ANCIENT RUINS — 10 attempt, min_lane 60 ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 10; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 60.0)) {")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y;")
    cpp.append("            e[2] = String(kChRuinVariant[rng.choice_idx(3)]);")
    cpp.append("            ancient_ruins.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── BONES (dire) — 15 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 15; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_dire(x, y, map_w, map_h)) {")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y;")
    cpp.append("            e[2] = String(kChBoneType[rng.choice_idx(3)]);")
    cpp.append("            bones.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── DARK MUSHROOMS — 25 attempt (warna ikut sisi) ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 25; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)) {")
    cpp.append("            const int64_t pick = rng.choice_idx(3);")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y;")
    cpp.append("            if (is_dire(x, y, map_w, map_h)) {")
    cpp.append("                e[2] = rgb(kChMushDire[pick][0], kChMushDire[pick][1], kChMushDire[pick][2]);")
    cpp.append("            } else {")
    cpp.append("                e[2] = rgb(kChMushRadiant[pick][0], kChMushRadiant[pick][1], kChMushRadiant[pick][2]);")
    cpp.append("            }")
    cpp.append("            mushrooms_dark.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── MOSSY ROCKS — 20 attempt (batas -2, bukan -3) ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 20; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(2, nx2) * TS;")
    cpp.append("        const int64_t y = rng.randint(2, ny2) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)) {")
    cpp.append("            const int64_t size = kChRockSize[rng.choice_idx(3)];")
    cpp.append("            const bool has_moss = is_radiant(x, y, map_w, map_h);")
    cpp.append("            Array e; e.resize(4); e[0] = x; e[1] = y; e[2] = size; e[3] = has_moss;")
    cpp.append("            rocks_mossy.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── DARK BUSHES (radiant) — 20 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 20; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(2, nx2) * TS;")
    cpp.append("        const int64_t y = rng.randint(2, ny2) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_radiant(x, y, map_w, map_h)) {")
    cpp.append("            const int64_t size = kChBushSize[rng.choice_idx(2)];")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;")
    cpp.append("            dark_bushes.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── GLOWING FLOWERS (radiant) — 20 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 20; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_radiant(x, y, map_w, map_h)) {")
    cpp.append("            const int64_t pick = rng.choice_idx(4);")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y;")
    cpp.append("            e[2] = rgb(kChFlower[pick][0], kChFlower[pick][1], kChFlower[pick][2]);")
    cpp.append("            glow_flowers.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── SPIKE TRAPS (dire) — 8 attempt ───")
    cpp.append("    for (int64_t attempt = 0; attempt < 8; attempt++) {")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)")
    cpp.append("                && is_dire(x, y, map_w, map_h)) {")
    cpp.append("            push_point(spike_traps, x, y);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── BOSS LANDMARKS — while <30, maks 240 attempt, min_lane 74 ───")
    cpp.append("    int64_t landmark_attempts = 0;")
    cpp.append("    while (boss_landmarks.size() < 30 && landmark_attempts < 240) {")
    cpp.append("        landmark_attempts++;")
    cpp.append("        const int64_t x = rng.randint(3, nx) * TS;")
    cpp.append("        const int64_t y = rng.randint(3, ny) * TS;")
    cpp.append("        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 74.0)) {")
    cpp.append("            const int64_t variant = kChLandmark[rng.choice_idx(4)];")
    cpp.append("            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = variant;")
    cpp.append("            boss_landmarks.push_back(e);")
    cpp.append("        }")
    cpp.append("    }")
    cpp.append("    // ─── TORCH STONES (border, tanpa RNG) ───")
    cpp.append("    for (int64_t x = 120; x < map_w - 80; x += 200) {")
    cpp.append("        push_point(torch_stones, x, 32);")
    cpp.append("        push_point(torch_stones, x, map_h - 32);")
    cpp.append("    }")
    cpp.append("    for (int64_t y = 120; y < map_h - 80; y += 200) {")
    cpp.append("        push_point(torch_stones, 32, y);")
    cpp.append("        push_point(torch_stones, map_w - 32, y);")
    cpp.append("    }")
    cpp.append("    // Urutan kunci = urutan literal `data` generate_all Python.")
    cpp.append("    Dictionary d;")
    for cat in ("dark_trees", "dead_trees", "gravestones", "crystals_blue",
                "crystals_red", "ancient_ruins", "bones", "mushrooms_dark",
                "rocks_mossy", "dark_bushes", "glow_flowers", "spike_traps",
                "torch_stones", "boss_landmarks"):
        cpp.append('    d["%s"] = %s;' % (cat, cat))
    cpp.append("    return d;")
    cpp.append("}")

    # ── bindings ──
    cpp.append("")
    cpp.append("void %s::_bind_methods() {" % CLASS)
    bindings = [
        ("tile_size", []),
        ("palettes", []),
        ("theme_names", []),
        ("theme_count", []),
        ("get_theme", ["theme_name"]),
        ("all_themes", []),
        ("catalog_signature", []),
        ("make_curved_path", ["waypoints", "smoothness"]),
        ("generate_lanes", ["map_w", "map_h"]),
        ("generate_river", ["map_w", "map_h"]),
        ("generate_decorations", ["map_w", "map_h", "lane_points", "river_points", "shop_positions"]),
        ("build_theme", ["index"]),
        ("theme_index", ["theme_name"]),
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
    palettes, themes, order, theme_lines, pathgen = parse_bundle()
    validate_palettes(palettes)
    ordered_themes = [(const, key, themes[const]) for key, const in order]
    keys, kinds = build_schema(ordered_themes)
    lanes, river = parse_paths(pathgen)

    header_text = emit_header(len(ordered_themes), len(keys))
    cpp_text = emit_cpp(palettes, ordered_themes, theme_lines, lanes, river)

    if check:
        stale = []
        for path, text in ((OUT_H, header_text), (OUT_CPP, cpp_text)):
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            if old != text:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            for rel in stale:
                print("[gen_maps_cpp] BASI: %s != hasil transpile map_components/_bundle.py" % rel)
            print("[gen_maps_cpp] regenerasi: python3 tools/gen_maps_cpp.py")
            return 1
        print("[gen_maps_cpp] PASS: maps_processor.h/.cpp ter-commit == hasil transpile "
              "(%d tema, %d kunci union, %d baris cpp)"
              % (len(ordered_themes), len(keys), cpp_text.count("\n") + 1))
        return 0

    OUT_H.parent.mkdir(parents=True, exist_ok=True)
    OUT_H.write_text(header_text, encoding="utf-8")
    OUT_CPP.write_text(cpp_text, encoding="utf-8")
    print("[gen_maps_cpp] wrote %s (%d baris)"
          % (OUT_H.relative_to(ROOT), header_text.count("\n") + 1))
    print("[gen_maps_cpp] wrote %s (%d baris, %d tema, %d kunci union)"
          % (OUT_CPP.relative_to(ROOT), cpp_text.count("\n") + 1,
             len(ordered_themes), len(keys)))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Transpile map_components/_bundle.py -> C++ GDExtension (godot++)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 kalau maps_processor.h/.cpp ter-commit basi")
    args = ap.parse_args()
    try:
        sys.exit(generate(check=args.check))
    except MapError as exc:
        print("[gen_maps_cpp] GAGAL: %s" % exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
