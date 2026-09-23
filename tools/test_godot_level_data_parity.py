#!/usr/bin/env python3
"""Oracle paritas levels/level_data.py -> Godot (LevelDB.gd + MysticLevels C++).

    python3 tools/test_godot_level_data_parity.py                  # verifikasi
    python3 tools/test_godot_level_data_parity.py --write-fixture  # sengaja perbarui

TIDAK butuh pygame dan TIDAK butuh Godot: `levels/level_data.py` murni data +
empat fungsi helper, jadi seluruh permukaannya bisa dibandingkan di mesin apa
pun dalam hitungan milidetik. Yang dikerjakan:

  1. KATALOG    godot/data/levels.json (sumber backend GDScript) dibandingkan
                dengan ALL_LEVELS Python: jumlah, urutan level, urutan kunci,
                nilai, dan TIPE Python tiap field. Satu-satunya beda yang
                diizinkan: kunci mini_bosses jadi string (kunci objek JSON
                selalu string) — dicatat eksplisit di fixture.
  2. FIELD_KINDS tabel tipe di LevelDB.gd DIBACA dari berkasnya (bukan disalin
                di sini) lalu dibandingkan dengan tipe nilai Python tiap field
                di SEMUA level, dua arah (closed-world): field baru di
                level_data.py yang belum terdaftar = gagal, field terdaftar
                yang sudah tidak ada di data = gagal.
  3. TABEL C++  literal di levels_processor.cpp (struct LevelRow, kMini<N>[],
                kLevels[], kLevelCount) di-parse lalu dibandingkan dengan
                katalog Python. Jadi .cpp yang disunting tangan atau basi
                ketahuan DI SINI, bukan hanya lewat --check generator: dua
                pemeriksaan itu menutup celah yang berbeda (byte-identik vs
                semantik-identik).
  4. BATERAI    get_level_config / get_level_count / is_level_unlocked /
                get_next_level / `x in list` dievaluasi dengan level_data.py
                ASLI (termasuk kasus tepi: level 0/55/-1, unlock_after_level
                None, completed_levels berisi FLOAT dan STRING, urutan
                mini_bosses level 3 yang memang tidak naik) lalu ditulis ke
                godot/tests/fixtures/level_data.json untuk diputar ulang
                LevelDataParityTest (backend GDScript) dan
                LevelDataGdextParityTest (backend C++ + A/B) di engine.
  5. WIRING     BossDB/GameManager/SaveManager memakai loader, setting
                project.godot ada dan default false, entry_symbol .gdextension
                == symbol yang diekspor register_types.cpp, nama berkas
                [libraries] memakai template_debug/template_release (bug FASE
                33: kunci target Godot != nama berkas scons), .gitignore
                menutup bin/ + godot-cpp, dan kedua workflow memanggil
                generator + scene tes fase ini.

  6. SELF-TEST  godot/gdext/mystic_levels/selftest/ (stub Variant/Array/
                Dictionary + harness stdin) ada, TIDAK ikut lib (SConstruct
                hanya Glob("src/*.cpp")), meng-include levels_processor.cpp
                apa adanya (bukan salinan logika), dan mendeklarasikan PERSIS
                method yang di-bind generator (closed-world dua arah). Yang
                mengeksekusinya: tools/test_levels_cpp_selftest.py di
                godot-gdext.yml — paritas logika C++ terkunci sebelum build
                godot-cpp yang ±10 menit.

Regenerasi fixture HANYA bila level_data.py berubah — data pygame tidak pernah
disesuaikan mengikuti Godot (aturan docs/AUDIT_ULANG_DARI_AWAL.md).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LEVELS_JSON = ROOT / "godot/data/levels.json"
LEVELDB_GD = ROOT / "godot/scripts/core/LevelDB.gd"
LOADER_GD = ROOT / "godot/scripts/core/LevelDBLoader.gd"
BOSSDB_GD = ROOT / "godot/scripts/core/BossDB.gd"
GAMEMANAGER_GD = ROOT / "godot/scripts/autoload/GameManager.gd"
SAVEMANAGER_GD = ROOT / "godot/scripts/autoload/SaveManager.gd"
CPP_H = ROOT / "godot/gdext/mystic_levels/src/levels_processor.h"
CPP = ROOT / "godot/gdext/mystic_levels/src/levels_processor.cpp"
REGISTER_CPP = ROOT / "godot/gdext/mystic_levels/src/register_types.cpp"
GDEXT_FILE = ROOT / "godot/addons/mystic_levels/mystic_levels.gdextension"
PROJECT_GODOT = ROOT / "godot/project.godot"
GITIGNORE = ROOT / ".gitignore"
FIXTURE = ROOT / "godot/tests/fixtures/level_data.json"
ADDONS_DIR = ROOT / "godot/addons"
WORKFLOW_CHECK = ROOT / ".github/workflows/godot-check.yml"
WORKFLOW_GDEXT = ROOT / ".github/workflows/godot-gdext.yml"

SETTING = "mystic/levels/use_gdext_levels"
GDEXT_CLASS = "MysticLevels"
ENTRY_SYMBOL = "mystic_levels_library_init"

from levels import level_data as oracle  # noqa: E402  (oracle: modul pygame asli)

_failures = []
_checks = 0


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[level_parity] FAIL: %s" % message)


def section(title):
    print("[level_parity] %s" % title)


# ══════════════════════════════════════════════════════════
#  Oracle Python
# ══════════════════════════════════════════════════════════

def kind_of(value):
    """Tipe Python -> nama yang dipakai fixture (JSON Godot tidak menyimpannya)."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, dict):
        return "dict"
    raise AssertionError("tipe tak dikenal: %r" % (value,))


_NULLABLE_BASE = {"int?": "int", "str?": "str"}
_NULLABLE_KIND = {"int": "int?", "str": "str?"}


def _split_kind(kind):
    """(base, nullable) dari nama kind — base None berarti selalu nil."""
    if kind == "nil":
        return None, True
    if kind in _NULLABLE_BASE:
        return _NULLABLE_BASE[kind], True
    return kind, False


def field_kinds_of(catalog):
    """Kind per field: 'int?' kalau sebagian level None (skema nullable)."""
    kinds = {}
    for row in catalog:
        for key, value in row.items():
            base = None if value is None else kind_of(value)
            nullable = value is None
            if key in kinds:
                prev_base, prev_nullable = _split_kind(kinds[key])
                if base is None:
                    base = prev_base
                elif prev_base is not None and prev_base != base:
                    raise AssertionError("field %s punya dua tipe: %s dan %s"
                                         % (key, prev_base, base))
                nullable = nullable or prev_nullable
            if base is None:
                kinds[key] = "nil"
            elif nullable:
                if base not in _NULLABLE_KIND:
                    raise AssertionError("field %s kadang None kadang %s — kolom "
                                         "nullable hanya didukung int/str"
                                         % (key, base))
                kinds[key] = _NULLABLE_KIND[base]
            else:
                kinds[key] = base
    return kinds


def mini_pairs(row):
    """[(wave_string, boss)] — urutan insert Python dipertahankan."""
    return [[str(wave), boss] for wave, boss in row["mini_bosses"].items()]


def catalog_signature(catalog):
    """Tanda tangan yang juga dihitung MysticLevels::catalog_signature()."""
    mini_total = sum(len(row["mini_bosses"]) for row in catalog)
    if not catalog:
        return "0::0"
    return "%d:%d-%d:%d" % (len(catalog), catalog[0]["level_number"],
                            catalog[-1]["level_number"], mini_total)


# ══════════════════════════════════════════════════════════
#  1. levels.json == ALL_LEVELS
# ══════════════════════════════════════════════════════════

def check_levels_json(catalog):
    section("1. godot/data/levels.json vs ALL_LEVELS")
    if not LEVELS_JSON.exists():
        expect(False, "%s tidak ada — jalankan tools/convert_to_godot.py"
               % LEVELS_JSON.relative_to(ROOT))
        return
    baked = json.loads(LEVELS_JSON.read_text(encoding="utf-8"))
    expect(isinstance(baked, list), "levels.json harus array level")
    if not isinstance(baked, list):
        return
    expect(len(baked) == len(catalog),
           "levels.json punya %d level, level_data.py %d"
           % (len(baked), len(catalog)))
    for i, (row_py, row_json) in enumerate(zip(catalog, baked)):
        tag = "levels.json[%d] (level %s)" % (i, row_py.get("level_number"))
        expect(list(row_json.keys()) == list(row_py.keys()),
               "%s urutan kunci %s != %s" % (tag, list(row_json.keys()),
                                             list(row_py.keys())))
        for key, want in row_py.items():
            got = row_json.get(key)
            if key == "mini_bosses":
                # Satu-satunya normalisasi yang diizinkan: kunci wave jadi
                # string (kunci objek JSON). Nilai + URUTAN wajib sama.
                expect([[str(w), b] for w, b in (got or {}).items()] == mini_pairs(row_py),
                       "%s mini_bosses %s != %s (urutan ikut dikunci)"
                       % (tag, got, mini_pairs(row_py)))
                continue
            expect(kind_of(got) == kind_of(want),
                   "%s.%s tipe JSON %s != Python %s (%r vs %r)"
                   % (tag, key, kind_of(got), kind_of(want), got, want))
            expect(got == want, "%s.%s %r != %r" % (tag, key, got, want))
    print("  %d level x %d field dibandingkan (tipe + urutan kunci)"
          % (len(catalog), len(catalog[0]) if catalog else 0))


# ══════════════════════════════════════════════════════════
#  2. FIELD_KINDS di LevelDB.gd
# ══════════════════════════════════════════════════════════

_GD_FIELD_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*"([a-z?_]+)"\s*,?\s*$')


def strip_gd_literals(text):
    """Buang komentar (#) dan isi literal string GDScript.

    Dipakai untuk memastikan sebuah nama class TIDAK muncul sebagai identifier:
    menyebut "MysticLevels" di dalam string/komentar aman (lib boleh absen),
    menyebutnya sebagai identifier membuat Parse Error saat lib tidak ada.
    """
    out = []
    for line in text.splitlines():
        cleaned = []
        in_string = False
        quote = ""
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    in_string = False
                i += 1
                continue
            if ch in "\"'":
                in_string = True
                quote = ch
                i += 1
                continue
            if ch == "#":
                break
            cleaned.append(ch)
            i += 1
        out.append("".join(cleaned))
    return "\n".join(out)


def strip_cpp_comments(text):
    """Buang komentar // dan /* */ dari sumber C++ (literal string dibiarkan).

    strip_gd_literals() TIDAK boleh dipakai untuk C++: di sana '#' yang memulai
    komentar, dan kutip tunggal (char literal seperti '{') dianggap pembuka
    string sehingga menelan kode. Dipakai check_selftest() supaya identifier
    yang dicari benar-benar ada di KODE, bukan cuma disebut di komentar.
    """
    out = []
    i = 0
    n = len(text)
    in_string = False
    quote = ""
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                in_string = False
            i += 1
            continue
        if ch in "\"'":
            in_string = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def strip_gd_comments(text):
    """Buang komentar GDScript (# ...) tapi PERTAHANKAN literal string.

    Beda dengan strip_gd_literals() yang juga mengosongkan isi string: untuk
    menghitung arity pemanggilan, argumen berupa string harus tetap terlihat
    (`_fail("x")` = 1 argumen; kalau isinya dibuang jadi `_fail()` = 0).
    """
    out = []
    for line in text.splitlines():
        cleaned = []
        in_string = False
        quote = ""
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                cleaned.append(ch)
                if ch == "\\" and i + 1 < len(line):
                    cleaned.append(line[i + 1])
                    i += 2
                    continue
                if ch == quote:
                    in_string = False
                i += 1
                continue
            if ch in "\"'":
                in_string = True
                quote = ch
                cleaned.append(ch)
                i += 1
                continue
            if ch == "#":
                break
            cleaned.append(ch)
            i += 1
        out.append("".join(cleaned))
    return "\n".join(out)


def gd_function_body(text, func_name):
    """Badan `func <name>(...)` (sampai func/kolom-0 berikutnya) dari sumber .gd."""
    lines = text.splitlines()
    start = -1
    for i, line in enumerate(lines):
        if re.match(r"^(static )?func %s\b" % re.escape(func_name), line.strip()) \
                and not line.startswith("\t\t"):
            start = i
            break
    if start < 0:
        return None
    body = [lines[start]]
    for line in lines[start + 1:]:
        if line.strip() and not (line.startswith("\t") or line.startswith(" ")):
            break
        body.append(line)
    return "\n".join(body)


def parse_gd_field_kinds():
    """Baca `const FIELD_KINDS := { ... }` dari LevelDB.gd (bukan disalin)."""
    text = LEVELDB_GD.read_text(encoding="utf-8")
    match = re.search(r"const FIELD_KINDS := \{(.*?)\n\}", text, re.S)
    if not match:
        expect(False, "FIELD_KINDS tidak ditemukan di %s"
               % LEVELDB_GD.relative_to(ROOT))
        return {}
    kinds = {}
    for line in match.group(1).splitlines():
        line = line.split("#", 1)[0]
        if not line.strip():
            continue
        parsed = _GD_FIELD_RE.match(line)
        if not parsed:
            expect(False, "baris FIELD_KINDS tidak bisa diparse: %r" % line.strip())
            continue
        kinds[parsed.group(1)] = parsed.group(2)
    return kinds


def check_field_kinds(catalog):
    section("2. FIELD_KINDS LevelDB.gd vs tipe Python")
    gd_kinds = parse_gd_field_kinds()
    py_kinds = field_kinds_of(catalog)
    expect(set(gd_kinds) == set(py_kinds),
           "FIELD_KINDS tidak closed-world: kurang %s, lebih %s"
           % (sorted(set(py_kinds) - set(gd_kinds)), sorted(set(gd_kinds) - set(py_kinds))))
    for key in sorted(set(gd_kinds) & set(py_kinds)):
        py_kind = py_kinds[key]
        gd_kind = gd_kinds[key]
        if py_kind == "dict":
            # Ejaan GDScript untuk dict wave->nama boss adalah "mini_bosses"
            # (LevelDB._normalize_mini_bosses). Bentuk isinya tetap diaudit:
            # kunci int/str, nilai str — jadi "mini_bosses" bukan celah untuk
            # field dict sembarangan.
            expect(gd_kind == "mini_bosses",
                   "FIELD_KINDS[%s] = %r, seharusnya 'mini_bosses' (tipe Python dict)"
                   % (key, gd_kind))
            for row in catalog:
                for wave, boss in (row.get(key) or {}).items():
                    expect(isinstance(wave, (int, str)) and not isinstance(wave, bool),
                           "%s[%s] kunci wave %r bukan int/str" % (key, row.get("level_number"), wave))
                    expect(isinstance(boss, str),
                           "%s[%s] nilai %r bukan str" % (key, row.get("level_number"), boss))
            continue
        expect(gd_kind == py_kind,
               "FIELD_KINDS[%s] = %r, tipe Python %r" % (key, gd_kind, py_kind))
    # API publik level_data.py harus ada di backend GDScript.
    text = LEVELDB_GD.read_text(encoding="utf-8")
    for name in ("all_levels", "get_level_config", "get_level_count",
                 "is_level_unlocked", "get_next_level", "py_contains"):
        expect(("static func %s(" % name) in text,
               "LevelDB.gd kehilangan `static func %s()` (API levels/__init__.py)" % name)
    # Normalisasi mini_bosses: kunci wave STRING, urutan dipertahankan.
    expect("out[str(wave)] = str(" in text,
           "LevelDB._normalize_mini_bosses harus men-string-kan kunci wave "
           "(paritas levels.json + MysticLevels C++)")
    print("  %d field: %s" % (len(py_kinds),
                              ", ".join("%s=%s" % (k, py_kinds[k]) for k in catalog[0])))


# ══════════════════════════════════════════════════════════
#  3. Tabel C++ (levels_processor.cpp)
# ══════════════════════════════════════════════════════════

_STRUCT_RE = re.compile(r"struct\s+LevelRow\s*\{(.*?)\n\};", re.S)
_STRUCT_FIELD_RE = re.compile(r"^\s*(?:const\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\*?\s*"
                              r"([A-Za-z_][A-Za-z0-9_]*)\s*;\s*(?://.*)?$")
_COUNT_RE = re.compile(r"const\s+int64_t\s+kLevelCount\s*=\s*(\d+)\s*;")
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?$")
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_OCT_RE = re.compile(r"\\([0-7]{1,3})")
_HEX_RE = re.compile(r"\\x([0-9a-fA-F]{2})")


def strip_line_comments(text):
    """Buang komentar // di luar literal string (cukup untuk berkas generated)."""
    out = []
    for line in text.splitlines():
        in_string = False
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                if ch == "\\":
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                    line = line[:i]
                    break
            i += 1
        out.append(line)
    return "\n".join(out)


def unescape_c(literal):
    """Literal string C++ -> str Python (escape yang dipakai generator)."""
    body = literal.strip()
    expect(body.startswith('"') and body.endswith('"'),
           "literal C++ bukan string: %r" % literal[:40])
    body = body[1:-1]
    simple = {"\\n": "\n", "\\t": "\t", "\\r": "\r", '\\"': '"', "\\\\": "\\"}
    out = []
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two in simple:
            out.append(simple[two])
            i += 2
            continue
        if two == "\\x":
            out.append(chr(int(body[i + 2:i + 4], 16)))
            i += 4
            continue
        if body[i] == "\\":
            match = re.match(r"\\([0-7]{1,3})", body[i:])
            if match:
                out.append(chr(int(match.group(1), 8)))
                i += 1 + len(match.group(1))
                continue
            raise AssertionError("escape C++ tak dikenal di %r" % body[i:i + 6])
        out.append(body[i])
        i += 1
    return "".join(out)


def split_top_level(text, seps=","):
    """Pecah teks di separator top-level — hormati literal string dan kurung."""
    parts = []
    depth = 0
    in_string = False
    current = []
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            current.append(ch)
            if ch == "\\":
                if i + 1 < len(text):
                    current.append(text[i + 1])
                    i += 2
                    continue
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            current.append(ch)
        elif ch in "{[(":
            depth += 1
            current.append(ch)
        elif ch in "}])":
            depth -= 1
            current.append(ch)
        elif ch in seps and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    tail = "".join(current)
    if tail.strip():
        parts.append(tail)
    return [p.strip() for p in parts if p.strip()]


def extract_braced_blocks(text):
    """Ambil tiap `{...}` tingkat atas (satu per baris level / per array mini)."""
    blocks = []
    depth = 0
    in_string = False
    start = -1
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                blocks.append(text[start + 1:i])
                start = -1
        i += 1
    return blocks


def eval_token(token):
    token = token.strip()
    if token.startswith('"'):
        return unescape_c(token)
    if token == "true":
        return True
    if token == "false":
        return False
    if token == "nullptr":
        return None
    if _INT_RE.match(token):
        return int(token)
    if _FLOAT_RE.match(token):
        return float(token)
    if _IDENT_RE.match(token):
        return ("ref", token)
    raise AssertionError("token C++ tak dikenal: %r" % token[:60])


def parse_struct_fields(cpp_text):
    match = _STRUCT_RE.search(cpp_text)
    if not match:
        expect(False, "struct LevelRow tidak ditemukan di levels_processor.cpp")
        return []
    fields = []
    for line in match.group(1).splitlines():
        line = line.split("//", 1)[0].strip()
        if not line:
            continue
        parsed = _STRUCT_FIELD_RE.match(line)
        if not parsed:
            expect(False, "field struct LevelRow tidak bisa diparse: %r" % line)
            continue
        fields.append((parsed.group(1), parsed.group(2)))
    return fields


def parse_mini_arrays(cpp_text):
    """{nama: [[wave_str, boss], ...]} dari `const MiniBossSlot kMiniN[] = {...}`."""
    out = {}
    for match in re.finditer(r"const\s+MiniBossSlot\s+(kMini\w+)\s*\[\]\s*=\s*\{(.*?)\n\};",
                             cpp_text, re.S):
        name = match.group(1)
        slots = []
        for block in extract_braced_blocks(match.group(2)):
            parts = split_top_level(block)
            if len(parts) != 2:
                expect(False, "slot mini boss %s bukan pasangan: %r" % (name, block))
                continue
            slots.append([eval_token(parts[0]), eval_token(parts[1])])
        out[name] = slots
    # Level dengan mini_bosses kosong: `const MiniBossSlot *const kMiniN = nullptr;`
    for match in re.finditer(r"const\s+MiniBossSlot\s*\*const\s+(kMini\w+)\s*=\s*nullptr\s*;",
                             cpp_text):
        out[match.group(1)] = []
    return out


def parse_level_rows(cpp_text, fields, minis):
    match = re.search(r"const\s+LevelRow\s+kLevels\s*\[\]\s*=\s*\{(.*?)\n\};", cpp_text, re.S)
    if not match:
        expect(False, "kLevels[] tidak ditemukan di levels_processor.cpp")
        return []
    names = [name for _type, name in fields]
    rows = []
    for block in extract_braced_blocks(match.group(1)):
        tokens = split_top_level(block)
        if len(tokens) != len(fields):
            expect(False, "baris kLevels punya %d nilai, struct LevelRow %d kolom: %r"
                   % (len(tokens), len(fields), block[:120]))
            continue
        values = {}
        for name, token in zip(names, tokens):
            values[name] = eval_token(token)
        rows.append(values)
    # Rakit ulang jadi dict level (urutan kolom = urutan kunci Python).
    out = []
    for values in rows:
        row = {}
        for name in names:
            if name.endswith("_count") or name.startswith("has_"):
                continue
            value = values[name]
            if name + "_count" in values:
                ref = value[1] if isinstance(value, tuple) else None
                slots = minis.get(ref)
                expect(slots is not None, "kolom %s merujuk array mini tak dikenal %r"
                       % (name, value))
                slots = slots or []
                expect(len(slots) == values[name + "_count"],
                       "%s_count %d != isi array %d" % (name, values[name + "_count"], len(slots)))
                row[name] = slots
            elif "has_" + name in values:
                row[name] = value if values["has_" + name] else None
            else:
                row[name] = value
        out.append(row)
    return out


def check_cpp_tables(catalog):
    section("3. Tabel C++ levels_processor.cpp vs level_data.py")
    for path in (CPP, CPP_H):
        expect(path.exists(), "%s tidak ada — jalankan tools/gen_levels_cpp.py"
               % path.relative_to(ROOT))
    if not CPP.exists():
        return
    raw = CPP.read_text(encoding="utf-8")
    expect("GENERATED" in raw.splitlines()[0] or "GENERATED" in raw[:400],
           "levels_processor.cpp kehilangan banner GENERATED (berkas ini hasil "
           "tools/gen_levels_cpp.py, bukan suntingan tangan)")
    cpp_text = strip_line_comments(raw)

    count_match = _COUNT_RE.search(cpp_text)
    expect(count_match is not None, "kLevelCount tidak ditemukan")
    if count_match:
        expect(int(count_match.group(1)) == len(catalog),
               "kLevelCount %s != %d level di level_data.py"
               % (count_match.group(1), len(catalog)))

    fields = parse_struct_fields(cpp_text)
    minis = parse_mini_arrays(cpp_text)
    rows = parse_level_rows(cpp_text, fields, minis)
    expect(len(rows) == len(catalog),
           "kLevels[] punya %d baris, level_data.py %d" % (len(rows), len(catalog)))

    kinds = field_kinds_of(catalog)
    for i, (row_py, row_cpp) in enumerate(zip(catalog, rows)):
        tag = "kLevels[%d] (level %s)" % (i, row_py.get("level_number"))
        expect(list(row_cpp.keys()) == list(row_py.keys()),
               "%s urutan kolom %s != urutan kunci Python %s"
               % (tag, list(row_cpp.keys()), list(row_py.keys())))
        for key, want in row_py.items():
            got = row_cpp.get(key)
            if key == "mini_bosses":
                expect(got == mini_pairs(row_py),
                       "%s.mini_bosses %s != %s (urutan insert dikunci)"
                       % (tag, got, mini_pairs(row_py)))
                continue
            if want is None:
                expect(got is None, "%s.%s harus None (Python), C++ %r" % (tag, key, got))
                continue
            expect(kind_of(got) == kind_of(want),
                   "%s.%s tipe C++ %s != Python %s (%r vs %r)"
                   % (tag, key, kind_of(got), kind_of(want), got, want))
            if kind_of(want) == "float":
                expect(repr(float(got)) == repr(float(want)),
                       "%s.%s double tidak bit-identik: %r vs %r"
                       % (tag, key, got, want))
            else:
                expect(got == want, "%s.%s %r != %r" % (tag, key, got, want))
    # Kolom C++ harus menutup skema Python (tidak ada field yang hilang).
    cpp_keys = [name for name in dict.fromkeys(
        [k for row in rows for k in row])] if rows else []
    expect(set(cpp_keys) == set(kinds),
           "kolom LevelRow %s != field level_data.py %s"
           % (sorted(cpp_keys), sorted(kinds)))

    # Fungsi API: deklarasi di .h, definisi + binding di .cpp (closed-world).
    header = CPP_H.read_text(encoding="utf-8")
    api = ["all_levels", "get_level_config", "get_level_count", "is_level_unlocked",
           "get_next_level", "build_row", "row_index", "py_contains",
           "catalog_signature"]
    for name in api:
        expect(("static" in header and re.search(r"\b%s\s*\(" % name, header)) is not None,
               "levels_processor.h kehilangan deklarasi %s()" % name)
        expect(("%s::%s(" % (GDEXT_CLASS, name)) in cpp_text,
               "levels_processor.cpp kehilangan definisi %s::%s()" % (GDEXT_CLASS, name))
        expect(('D_METHOD("%s"' % name) in cpp_text,
               "_bind_methods() tidak mem-bind %s (method tak terlihat GDScript)" % name)
    # Semantik kunci yang tidak boleh hilang saat generator diubah.
    expect("Variant::evaluate(Variant::OP_EQUAL" in cpp_text,
           "py_contains harus memakai Variant::evaluate(OP_EQUAL) — Array.has() "
           "Godot strict-tipe (hash_compare) dan menolak 3 vs 3.0")
    expect("if (!r.has_unlock_after_level)" in cpp_text
           or "has_unlock" in cpp_text,
           "is_level_unlocked kehilangan cabang `required is None` (level 1)")
    print("  %d baris x %d kolom + %d array mini boss dibandingkan bit-per-bit"
          % (len(rows), len(fields), len(minis)))


# ══════════════════════════════════════════════════════════
#  4. Baterai helper (oracle Python) + fixture
# ══════════════════════════════════════════════════════════

# Input baterai dienkode [kind, nilai]: JSON Godot mengubah SEMUA angka jadi
# float (json.cpp:341), padahal int-vs-float justru yang dikunci fase ini
# (get_next_level(3) -> 4, get_next_level(3.0) -> 4.0).
CONFIG_INPUTS = [
    ("int", -99), ("int", -5), ("int", -1), ("int", 0), ("int", 1), ("int", 2),
    ("int", 3), ("int", 4), ("int", 27), ("int", 28), ("int", 53), ("int", 54),
    ("int", 55), ("int", 56), ("int", 100), ("int", 999),
    ("float", 1.0), ("float", 3.0), ("float", 54.0), ("float", 3.5),
    ("float", 0.5), ("float", -1.0),
]

NEXT_INPUTS = [
    ("int", -99), ("int", -5), ("int", -1), ("int", 0), ("int", 1), ("int", 2),
    ("int", 27), ("int", 52), ("int", 53), ("int", 54), ("int", 55),
    ("int", 100), ("float", 0.0), ("float", 3.0), ("float", 53.0),
    ("float", 54.0), ("float", 3.5),
]

UNLOCK_CASES = [
    # (level, completed_levels, catatan)
    (1, [], "unlock_after_level None -> selalu terbuka"),
    (1, [("int", 5)], "level 1 terbuka apa pun isi save"),
    (2, [], "syarat 1 belum ditamatkan"),
    (2, [("int", 1)], "syarat terpenuhi"),
    (2, [("float", 1.0)], "FLOAT di save (JSON.parse_string) tetap cocok - Python =="),
    (2, [("str", "1")], "string '1' BUKAN 1 (Python: '1' != 1)"),
    (2, [("int", 2)], "level dirinya sendiri tidak membuka dirinya"),
    (2, [("int", 0), ("int", 1), ("int", 5), ("int", 9)], "daftar panjang, syarat di tengah"),
    (3, [("int", 2)], "rantai normal"),
    (3, [("int", 1)], "syarat 2 belum ada"),
    (3, [("int", 1), ("float", 2.0)], "campuran int + float"),
    (27, [("int", 26)], "tengah katalog"),
    (27, [("int", 25), ("float", 26.0), ("int", 30)], "float di tengah daftar"),
    (54, [("int", 53)], "level terakhir"),
    (54, [("float", 53.0)], "level terakhir, save hasil reload (float)"),
    (54, [("int", 1), ("int", 2), ("int", 3)], "syarat 53 belum ada"),
    (0, [], "level tidak ada -> False (Python: not config)"),
    (55, [("int", 54)], "level tidak ada -> False walau syaratnya tamat"),
    (-1, []),
    (999, [("int", 1), ("int", 2), ("int", 3)]),
]

CONTAINS_CASES = [
    ([], ("int", 1), "daftar kosong"),
    ([("int", 1)], ("int", 1), "int cocok int"),
    ([("float", 1.0)], ("int", 1), "float 1.0 cocok int 1 (Python ==)"),
    ([("int", 1)], ("float", 1.0), "int 1 cocok float 1.0"),
    ([("str", "1")], ("int", 1), "string tidak cocok int"),
    ([("int", 1)], ("str", "1"), "int tidak cocok string"),
    ([("int", 0), ("int", 1), ("int", 2)], ("int", 2), "elemen terakhir"),
    ([("int", 2), ("int", 3)], ("int", 1), "tidak ada"),
    ([("nil", None)], ("int", 1), "None != 1"),
    ([("int", 1), ("nil", None)], ("nil", None), "None cocok None"),
    ([("float", 1.5)], ("float", 1.5), "float non-bulat"),
    ([("float", 1.5)], ("int", 1), "1.5 != 1"),
    ([("str", "a"), ("str", "b")], ("str", "b"), "string cocok string"),
    ([("int", 54)], ("int", 54), "nomor level terbesar"),
    ([("float", 53.0)], ("int", 54), "syarat level 54 belum tamat"),
]

# Kasus yang Python dan Godot BEDA dengan sengaja (bool: Python True == 1,
# Godot tidak punya evaluator == untuk bool/int). Yang dikunci: KEDUA backend
# Godot harus SEPAKAT, jadi deviasinya satu dan terdokumentasi.
DEVIATION_CASES = [
    ([("bool", True)], ("int", 1), "bool vs int: Python True == 1 -> True; "
                                   "kedua backend Godot harus False"),
    ([("int", 1)], ("bool", True), "arah sebaliknya, hasil sama"),
]


def build_fixture(catalog):
    kinds = field_kinds_of(catalog)
    rows = []
    for row in catalog:
        types = {}
        values = {}
        for key, value in row.items():
            if key == "mini_bosses":
                types[key] = "dict"
                values[key] = {str(wave): boss for wave, boss in value.items()}
                continue
            types[key] = kind_of(value)
            values[key] = value
        rows.append({
            "keys": list(row.keys()),
            "types": types,
            "values": values,
            "mini_bosses": mini_pairs(row),
        })

    config_battery = []
    for kind, value in CONFIG_INPUTS:
        probe = value if kind == "float" else int(value)
        got = oracle.get_level_config(probe)
        config_battery.append([
            [kind, value],
            "nil" if got is None else "dict",
            None if got is None else got["level_number"],
        ])

    unlock_battery = []
    for case in UNLOCK_CASES:
        level, completed = case[0], case[1]
        note = case[2] if len(case) > 2 else ""
        probe = [decoded for _kind, decoded in completed]
        unlock_battery.append([level, [list(pair) for pair in completed],
                               bool(oracle.is_level_unlocked(level, probe)), note])

    contains_battery = []
    for case in CONTAINS_CASES:
        haystack, needle = case[0], case[1]
        note = case[2] if len(case) > 2 else ""
        probe_list = [decoded for _kind, decoded in haystack]
        contains_battery.append([[list(pair) for pair in haystack], list(needle),
                                 bool(needle[1] in probe_list), note])

    next_battery = []
    for kind, value in NEXT_INPUTS:
        probe = value if kind == "float" else int(value)
        got = oracle.get_next_level(probe)
        next_battery.append([[kind, value],
                             "nil" if got is None else kind_of(got),
                             got])

    deviation_battery = []
    for haystack, needle, note in DEVIATION_CASES:
        deviation_battery.append([[list(pair) for pair in haystack], list(needle),
                                  False, note])

    return {
        "source": {
            "module": "levels/level_data.py",
            "generated_by": "tools/test_godot_level_data_parity.py",
            "level_count": oracle.get_level_count(),
            "catalog_signature": catalog_signature(catalog),
            "field_kinds": kinds,
            "notes": [
                "Semua angka di fixture ini sampai ke Godot sebagai FLOAT "
                "(JSON.parse_string Godot 4.3 tidak punya cabang bilangan bulat "
                "- core/io/json.cpp:341). Karena itu nilai yang TIPEnya penting "
                "dienkode [kind, nilai] dan tiap field katalog membawa peta "
                "`types`; engine test membandingkan nilai secara numerik lalu "
                "memeriksa typeof() terhadap kind yang tercatat.",
                "Kunci mini_bosses adalah STRING (kunci objek JSON) walau Python "
                "memakai int; URUTAN pair-nya dikunci karena Dictionary Godot "
                "ordered dan Main._roll_mini_boss_schedule membaca values() apa "
                "adanya (level 3 memang 25, 10, 17).",
                "deviation_battery bukan oracle Python: itu kasus yang Godot dan "
                "Python memang berbeda (bool), dipakai untuk memastikan backend "
                "C++ dan GDScript SEPAKAT satu sama lain.",
            ],
        },
        "field_order": list(catalog[0].keys()) if catalog else [],
        "catalog": rows,
        "get_level_config_battery": config_battery,
        "get_level_count": oracle.get_level_count(),
        "is_level_unlocked_battery": unlock_battery,
        "py_contains_battery": contains_battery,
        "get_next_level_battery": next_battery,
        "deviation_battery": deviation_battery,
    }


def check_fixture(catalog, write):
    section("4. Baterai helper (level_data.py ASLI) + fixture")
    fixture = build_fixture(catalog)

    # Baterai harus benar-benar membedakan: kalau semua kasus unlock True,
    # tes tidak mengunci apa pun.
    unlocked = sum(1 for row in fixture["is_level_unlocked_battery"] if row[2])
    expect(0 < unlocked < len(fixture["is_level_unlocked_battery"]),
           "baterai is_level_unlocked degenerate (%d/%d True)"
           % (unlocked, len(fixture["is_level_unlocked_battery"])))
    missing = sum(1 for row in fixture["get_level_config_battery"] if row[1] == "nil")
    expect(missing > 0, "baterai get_level_config tidak punya kasus level tak dikenal")
    expect(any(row[1] == "nil" for row in fixture["get_next_level_battery"]),
           "baterai get_next_level tidak punya kasus level terakhir (None)")

    payload = json.dumps(fixture, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    if write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(payload, encoding="utf-8")
        print("  ditulis %s (%d KB)" % (FIXTURE.relative_to(ROOT), len(payload) // 1024))
        return
    if not FIXTURE.exists():
        expect(False, "%s tidak ada — jalankan tools/test_godot_level_data_parity.py "
                      "--write-fixture" % FIXTURE.relative_to(ROOT))
        return
    current = FIXTURE.read_text(encoding="utf-8")
    expect(current == payload,
           "fixture %s BASI (level_data.py berubah tanpa fixture ikut diperbarui) "
           "— jalankan tools/test_godot_level_data_parity.py --write-fixture"
           % FIXTURE.relative_to(ROOT))
    print("  fixture segar: %d level, %d kasus config, %d unlock, %d contains, "
          "%d next" % (len(fixture["catalog"]),
                       len(fixture["get_level_config_battery"]),
                       len(fixture["is_level_unlocked_battery"]),
                       len(fixture["py_contains_battery"]),
                       len(fixture["get_next_level_battery"])))


# ══════════════════════════════════════════════════════════
#  5. Wiring
# ══════════════════════════════════════════════════════════

def parse_gdextension(path):
    """(entry_symbol, {kunci library: nilai}) dari berkas .gdextension."""
    entry = None
    libs = {}
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"')
        if current == "configuration" and key == "entry_symbol":
            entry = value
        elif current == "libraries":
            libs[key] = value
    return entry, libs


def check_gdextension_names(path):
    """Kunci target Godot (debug/release) -> nama berkas scons (template_*).

    Bug FASE 33: `linux.debug.x86_64 = .../libX.linux.debug.x86_64.so` tidak
    pernah dihasilkan SConstruct (scons memakai template_debug/template_release),
    jadi engine tidak pernah memuat lib dan diam-diam jatuh ke GDScript.
    """
    entry, libs = parse_gdextension(path)
    name = path.name
    expect(entry is not None, "%s tidak punya entry_symbol" % name)
    expect(libs, "%s tidak punya [libraries]" % name)
    for key, value in libs.items():
        parts = key.split(".")
        expect(len(parts) >= 2, "%s kunci library aneh: %s" % (name, key))
        target = parts[1] if len(parts) > 1 else ""
        if target == "debug":
            expect("template_debug" in value,
                   "%s %s -> %s (harus berkas template_debug hasil scons)"
                   % (name, key, value))
        elif target == "release":
            expect("template_release" in value,
                   "%s %s -> %s (harus berkas template_release hasil scons)"
                   % (name, key, value))
        expect(value.startswith("res://addons/"),
               "%s %s harus path res://addons/, dapat %s" % (name, key, value))
    return entry


def check_wiring(catalog):
    section("5. Wiring (loader, autoload, project.godot, CI)")
    loader = LOADER_GD.read_text(encoding="utf-8")
    expect('const GDEXT_CLASS := "%s"' % GDEXT_CLASS in loader,
           "LevelDBLoader.GDEXT_CLASS harus %s (nama di register_types.cpp)" % GDEXT_CLASS)
    expect('const SETTING := "%s"' % SETTING in loader,
           "LevelDBLoader.SETTING harus %s" % SETTING)
    expect("ClassDB.class_exists(GDEXT_CLASS)" in loader,
           "LevelDBLoader tidak boleh menyebut MysticLevels sebagai identifier "
           "(Parse Error kalau lib tidak ada) — pakai ClassDB.class_exists")
    expect(GDEXT_CLASS not in strip_gd_literals(loader),
           "LevelDBLoader menyebut %s sebagai IDENTIFIER (di luar string/komentar) "
           "- Parse Error kalau lib GDExt tidak ada" % GDEXT_CLASS)
    expect("LevelDBLoader] GDExtension MysticLevels aktif" in loader,
           "baris pengumuman backend C++ hilang — CI (godot-gdext.yml) "
           "me-require baris ini sebagai bukti jalur native dipakai")
    expect('preload("res://scripts/core/LevelDB.gd")' in loader,
           "LevelDBLoader harus preload LevelDB.gd sebagai fallback")

    register = REGISTER_CPP.read_text(encoding="utf-8")
    expect(("ClassDB::register_class<%s>()" % GDEXT_CLASS) in register,
           "register_types.cpp tidak mendaftarkan %s" % GDEXT_CLASS)
    expect(("GDE_EXPORT %s(" % ENTRY_SYMBOL) in register,
           "register_types.cpp tidak mengekspor %s" % ENTRY_SYMBOL)

    entry = check_gdextension_names(GDEXT_FILE)
    expect(entry == ENTRY_SYMBOL,
           "entry_symbol .gdextension %r != yang diekspor register_types.cpp %r"
           % (entry, ENTRY_SYMBOL))

    # Nama berkas .gdextension lain ikut dijaga (bug yang sama pernah membuat
    # mystic_skills + mystic_lighting tidak pernah termuat).
    for other in sorted(ADDONS_DIR.glob("*/mystic_*.gdextension")):
        if other != GDEXT_FILE:
            check_gdextension_names(other)

    project = PROJECT_GODOT.read_text(encoding="utf-8")
    expect(("%s=false" % SETTING.split("mystic/", 1)[1]) in project,
           "project.godot harus memuat %s=false (default GDScript, produksi "
           "tidak boleh bergantung lib per platform)" % SETTING)

    bossdb = BOSSDB_GD.read_text(encoding="utf-8")
    expect('preload("res://scripts/core/LevelDBLoader.gd")' in bossdb,
           "BossDB.gd harus preload LevelDBLoader.gd")
    expect("levels = LevelDBLoader.all_levels()" in bossdb,
           "BossDB.load_levels() harus mengambil katalog dari LevelDBLoader")
    load_levels = gd_function_body(bossdb, "load_levels")
    expect(load_levels is not None, "BossDB.gd kehilangan func load_levels()")
    if load_levels is not None:
        expect("JSON.parse_string" not in load_levels,
               "BossDB.load_levels() masih parse levels.json sendiri (dua sumber "
               "kebenaran untuk backend - katalog harus lewat LevelDBLoader)")

    game = GAMEMANAGER_GD.read_text(encoding="utf-8")
    for needle in ("LevelDBLoader.get_level_count()", "LevelDBLoader.get_next_level(",
                   "LevelDBLoader.is_level_unlocked("):
        expect(needle in game, "GameManager kehilangan delegasi %s" % needle)
    # Pemeriksaan negatif dijalankan di atas sumber TANPA komentar/string:
    # komentar yang Menjelaskan bug lama tidak boleh dibaca sebagai bug itu.
    expect("SaveManager.is_level_completed(int(required))" not in strip_gd_literals(game),
           "GameManager.is_level_unlocked masih memakai Array.has() strict-tipe "
           "(level terkunci lagi setelah restart)")

    save = SAVEMANAGER_GD.read_text(encoding="utf-8")
    expect("LevelDBScript.py_contains(" in save,
           "SaveManager.is_level_completed harus memakai py_contains (== Python)")
    completed_fn = gd_function_body(save, "is_level_completed")
    expect(completed_fn is not None, "SaveManager.gd kehilangan is_level_completed()")
    if completed_fn is not None:
        body = strip_gd_literals(completed_fn)
        expect(" in completed" not in body,
               "SaveManager.is_level_completed masih memakai `in`/Array.has() "
               "(strict-tipe: 3 tidak akan pernah cocok 3.0 dari save JSON)")
        expect("py_contains(" in body,
               "SaveManager.is_level_completed harus memanggil py_contains")

    ignore = GITIGNORE.read_text(encoding="utf-8")
    for needle in ("godot/addons/mystic_levels/bin/*.so",
                   "godot/gdext/mystic_levels/godot-cpp",
                   "godot/gdext/godot-cpp",
                   "godot/gdext/mystic_levels/.sconsign.dblite"):
        expect(needle in ignore, ".gitignore kehilangan %s" % needle)

    check = WORKFLOW_CHECK.read_text(encoding="utf-8")
    for needle in ("tools/gen_levels_cpp.py --check",
                   "tools/test_godot_level_data_parity.py",
                   "LevelDataParityTest.tscn",
                   "'levels/**'",
                   "'tools/gen_levels_cpp.py'"):
        expect(needle in check, "godot-check.yml kehilangan %s" % needle)
    gdext = WORKFLOW_GDEXT.read_text(encoding="utf-8")
    for needle in ("mystic_levels", "LevelDataGdextParityTest.tscn",
                   "tools/gen_levels_cpp.py --check",
                   "GDExtension MysticLevels aktif",
                   # Self-test C++ di luar engine: murah, jalan SEBELUM build
                   # godot-cpp, jadi regresi tabel/logika gagal cepat.
                   "tools/test_levels_cpp_selftest.py",
                   # Satu checkout godot-cpp dipakai bersama (cache -shared-v1).
                   "godot/gdext/godot-cpp",
                   # entry_symbol .gdextension harus benar-benar diekspor lib.
                   "mystic_levels_library_init",
                   # Regresi: lib terpasang tapi flag false -> tetap GDScript.
                   "LevelDataParityTest.tscn"):
        expect(needle in gdext, "godot-gdext.yml kehilangan %s" % needle)

    # LevelDB.py_equal: penjaga tipe (deviasi bool/int) + perbandingan NILAI
    # untuk tipe yang sama. Bug nyata yang hanya ketahuan di engine
    # (LevelDataParityTest, CI PR ini): cabang terakhir `return false` membuat
    # `None in [1, None]` menjawab false padahal Python true — dan jalur C++
    # (Variant::evaluate OP_EQUAL(NIL, NIL) = AlwaysTrue, variant_op.cpp:522)
    # menjawab true, jadi A/B backend juga akan pecah.
    level_db = LEVELDB_GD.read_text(encoding="utf-8")
    body = gd_function_body(level_db, "py_equal")
    expect(bool(body), "py_equal tidak ditemukan di LevelDB.gd")
    if body:
        expect("if ta != tb:" in body,
               "py_equal harus menolak pasangan beda tipe (deviasi bool/int "
               "Python True == 1 tidak boleh ikut")
        expect(body.rstrip().endswith("return bool(a == b)"),
               "py_equal harus jatuh ke `a == b` untuk tipe yang sama "
               "(NIL/Array/Dictionary deep compare di Godot = nilai di Python); "
               "`return false` di akhir membuat None in [1, None] salah")
        expect("float(a) == float(b)" in body,
               "py_equal harus membandingkan numerik lintas tipe (1 == 1.0)")

    # godot_log_gate.py: lib .so TIDAK ikut repo, jadi langkah "Import project"
    # di godot-check.yml selalu mencetak "Failed loading resource:
    # res://addons/mystic_levels/mystic_levels.gdextension" + "GDExtension
    # dynamic library not found". Tanpa entri allowlist, gate menganggap itu
    # fatal dan SELURUH langkah engine di-skip (kejadian nyata di CI PR ini).
    gate = (ROOT / "godot/tools/godot_log_gate.py").read_text(encoding="utf-8")
    for needle in (r'r"addons/mystic_levels"',
                   r'r"libmystic_levels"',
                   r'r"Failed loading resource.*mystic_levels"'):
        expect(needle in gate, "godot_log_gate.py kehilangan allowlist %s "
                               "(import headless akan gagal tanpa lib)" % needle)
    # Sengaja TIDAK boleh ada entri telanjang: baris FAIL harness level harus
    # tetap terhitung fatal.
    expect('\n    r"mystic_levels",' not in gate,
           "godot_log_gate.py punya allowlist telanjang r\"mystic_levels\" — "
           "terlalu lebar, bisa memaafkan baris kegagalan harness level")

    for scene in (ROOT / "godot/tests/LevelDataParityTest.tscn",
                  ROOT / "godot/tests/LevelDataGdextParityTest.tscn"):
        expect(scene.exists(), "%s tidak ada" % scene.relative_to(ROOT))
    print("  loader + 3 autoload + project.godot + .gitignore + 2 workflow diperiksa")


# ══════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════



def _call_arg_counts(text, name):
    """Jumlah argumen tiap pemanggilan `name(...)` (top-level comma, lintas baris).

    Parser GDScript engine memeriksa arity LINTAS berkas (subclass memanggil
    helper base), gdparse tidak — salah hitung argumen baru ketahuan sebagai
    "Parse Error: Too many arguments" saat scene dimuat di CI. Fungsi ini
    membuat cek itu jalan tanpa engine.
    """
    counts = []
    for match in re.finditer(r"(?<![\w.])%s\s*\(" % re.escape(name), text):
        i = match.end()
        depth = 1
        args = 1
        quote = ""
        while i < len(text) and depth > 0:
            ch = text[i]
            if quote:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    quote = ""
            elif ch in "\"'":
                quote = ch
            elif ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
                if depth == 0:
                    break
            elif ch == "," and depth == 1:
                args += 1
            i += 1
        body = text[match.end():i].strip()
        counts.append(0 if not body else args)
    return counts


def _declared_arity(text, name):
    """Jumlah parameter `func name(...)` (None kalau tidak ada / multi-baris)."""
    match = re.search(r"^\s*func\s+%s\s*\(([^)]*)\)" % re.escape(name), text, re.M)
    if not match:
        return None
    params = [part for part in match.group(1).split(",") if part.strip()]
    return len(params)


def check_test_arity():
    """Setiap panggilan helper di kedua scene tes cocok dengan deklarasinya."""
    base_path = ROOT / "godot/tests/LevelDataParityTest.gd"
    gdext_path = ROOT / "godot/tests/LevelDataGdextParityTest.gd"
    base_text = base_path.read_text(encoding="utf-8")
    gdext_text = gdext_path.read_text(encoding="utf-8")
    # Subclass mewarisi helper base, jadi gabungan keduanya = ruang nama yang
    # boleh dipanggil dari LevelDataGdextParityTest.gd.
    combined = base_text + "\n" + gdext_text

    helpers = ["_fail", "_expect", "_dec", "_dec_list", "_probe_label", "_kind_name",
               "_row_signature", "_canon", "_as_str_array", "_compare_mini_bosses",
               "_expect_kind", "_expect_value", "_compare_str", "_fail_gdext",
               "_load_fixture", "_snapshot", "_restore", "_finish", "_abort",
               "_collect", "_ab_battery"]
    # Komentar dibuang (menyebut "_fail()" di komentar bukan pemanggilan), tapi
    # literal string DIPERTAHANKAN supaya argumen string tetap terhitung.
    scan = {str(base_path): strip_gd_comments(base_text),
            str(gdext_path): strip_gd_comments(gdext_text)}
    for path, text in ((base_path, scan[str(base_path)]),
                       (gdext_path, scan[str(gdext_path)])):
        for name in helpers:
            want = _declared_arity(combined, name)
            if want is None:
                continue
            for got in _call_arg_counts(text, name):
                expect(got == want,
                       "%s: %s() dipanggil dengan %d argumen, deklarasinya %d "
                       "(Parse Error saat scene dimuat — gdparse tidak melihat "
                       "arity lintas berkas)"
                       % (path.relative_to(ROOT), name, got, want))
    print("  arity %d helper di 2 scene tes diperiksa" % len(helpers))




SELFTEST_DIR = ROOT / "godot/gdext/mystic_levels/selftest"
SCONSTRUCT = ROOT / "godot/gdext/mystic_levels/SConstruct"


def check_selftest():
    """6. Harness self-test C++ (jalan tanpa engine/godot-cpp) tetap jujur.

    Yang dikunci di sini bukan hasil eksekusinya (itu tugas
    tools/test_levels_cpp_selftest.py di CI yang punya compiler), melainkan
    tiga sifat yang mudah hilang diam-diam:
      * harness meng-include levels_processor.cpp APA ADANYA — kalau suatu saat
        diganti salinan logika, self-test berhenti menguji kode produksi;
      * stub tidak pernah masuk lib (SConstruct hanya Glob src/*.cpp);
      * daftar method di stub == daftar method yang di-bind generator
        (closed-world dua arah: method baru yang lupa dideklarasikan membuat
        self-test gagal compile, dan deklarasi yatim berarti API yang di-bind
        hilang).
    """
    section("6. self-test C++ di luar engine")
    harness = SELFTEST_DIR / "levels_selftest.cpp"
    stub = SELFTEST_DIR / "godot_stub.hpp"
    for path in (harness, stub, SELFTEST_DIR / "shim/godot_cpp/core/class_db.hpp",
                 SELFTEST_DIR / "shim/godot_cpp/variant/variant.hpp"):
        expect(path.exists(), "%s tidak ada" % path.relative_to(ROOT))
    if not (harness.exists() and stub.exists()):
        return

    harness_text = harness.read_text(encoding="utf-8")
    stub_text = strip_cpp_comments(stub.read_text(encoding="utf-8"))
    expect('#include "../src/levels_processor.cpp"' in harness_text,
           "levels_selftest.cpp harus meng-include ../src/levels_processor.cpp "
           "apa adanya (bukan salinan logika)")
    expect("#ifndef MYSTIC_LEVELS_PROCESSOR_H" in stub_text,
           "godot_stub.hpp harus melewati levels_processor.h lewat guard-nya")

    sconstruct = SCONSTRUCT.read_text(encoding="utf-8")
    expect('Glob("src/*.cpp")' in sconstruct,
           "SConstruct harus mengambil sumber dari src/ saja")
    expect("selftest" not in sconstruct.replace("self-test", ""),
           "SConstruct tidak boleh menarik direktori selftest ke dalam lib")

    cpp_text = CPP.read_text(encoding="utf-8")
    bound = set(re.findall(r'bind_static_method\(\s*"MysticLevels"\s*,\s*D_METHOD\(\s*"([A-Za-z_][A-Za-z0-9_]*)"',
                           cpp_text))
    declared = set(re.findall(r"static\s+[A-Za-z_:<>0-9 ]+?\s([a-z_][A-Za-z0-9_]*)\s*\(",
                              stub_text[stub_text.index("class MysticLevels"):]))
    expect(bool(bound), "tidak ada bind_static_method terbaca di levels_processor.cpp")
    for name in sorted(bound - declared):
        expect(False, "method %s di-bind generator tapi tidak dideklarasikan "
                      "godot_stub.hpp (self-test akan gagal compile)" % name)
    for name in sorted(declared - bound - {"_bind_methods"}):
        expect(False, "godot_stub.hpp mendeklarasikan %s yang tidak di-bind "
                      "levels_processor.cpp (API hilang / nama typo)" % name)
    expect("_bind_methods" in declared,
           "godot_stub.hpp harus mendeklarasikan _bind_methods (disentuh harness)")
    print("  harness + stub + %d shim + %d method di-bind diperiksa"
          % (len(list((SELFTEST_DIR / "shim").rglob("*.hpp"))), len(bound)))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-fixture", action="store_true",
                        help="tulis ulang godot/tests/fixtures/level_data.json")
    args = parser.parse_args()

    catalog = list(oracle.ALL_LEVELS)
    expect(len(catalog) == oracle.get_level_count(),
           "ALL_LEVELS (%d) != get_level_count() (%d)"
           % (len(catalog), oracle.get_level_count()))
    expect(all(isinstance(row, dict) for row in catalog),
           "ALL_LEVELS harus list of dict")
    print("[level_parity] oracle levels/level_data.py: %d level, %d field, "
          "signature %s" % (len(catalog), len(catalog[0]), catalog_signature(catalog)))

    check_levels_json(catalog)
    check_field_kinds(catalog)
    check_cpp_tables(catalog)
    check_fixture(catalog, args.write_fixture)
    check_wiring(catalog)
    check_selftest()
    check_test_arity()

    if _failures:
        print("\n[level_parity] FAIL: %d kegagalan dari %d cek" % (len(_failures), _checks))
        return 1
    print("\n[level_parity] PASS: %d cek (levels/level_data.py ↔ levels.json ↔ "
          "LevelDB.gd ↔ levels_processor.cpp ↔ wiring)" % _checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
