#!/usr/bin/env python3
"""Oracle paritas localization.py -> godot/scripts/utils/Localization.gd.

    python3 tools/test_godot_localization_parity.py                  # verifikasi
    python3 tools/test_godot_localization_parity.py --write-fixture  # sengaja perbarui

TIDAK butuh pygame dan TIDAK butuh Godot: modul lokalisasi keduanya murni
data + string, jadi seluruh permukaan bisa dibandingkan di mesin apa pun
dalam hitungan milidetik. Yang dikerjakan:

  1. Tabel GDScript DIBACA dari berkasnya (bukan disalin di sini) lalu
     dibandingkan kunci-per-kunci dengan `localization._TEXT`,
     `LANGUAGES`, `LANGUAGE_LABELS`, dan bahasa bawaan Python. Drift satu
     spasi/tanda baca pun gagal di sini, bukan saat game dijalankan.
  2. Audit placeholder: setiap template hanya boleh memakai `{nama}` polos
     (tanpa format spec / konversi / posisional) — itulah subset yang
     diimplementasikan `MysticLocalization._py_format`, dan audit ini yang
     menjaga subset itu tetap cukup.
  3. Baterai `tr()` dievaluasi dengan localization.py ASLI (setiap kunci x
     setiap bahasa + kasus tepi: kunci tak dikenal, nilai hilang, nilai
     berlebih, bahasa invalid, label fallback) dan ditulis ke
     `godot/tests/fixtures/localization.json` untuk diputar ulang
     `godot/tests/LocalizationParityTest.tscn` di CI (engine betulan).
  4. Closed-world kunci: setiap `tr_text("...")` / `loc("...")` di
     godot/**/*.gd harus ada di tabel (typo kunci di sisi Godot ketahuan
     tanpa menjalankan engine), dan kunci yang belum punya pemakai
     dilaporkan apa adanya.

Regenerasi fixture HANYA bila localization.py berubah — pygame tidak pernah
disetel mengikuti Godot (aturan docs/MIGRASI_1_1.md).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GD_PATH = ROOT / "godot/scripts/utils/Localization.gd"
FIXTURE = ROOT / "godot/tests/fixtures/localization.json"

import localization  # noqa: E402  (oracle: modul pygame asli)

# ══════════════════════════════════════════════════════════
#  Pembaca tabel GDScript
# ══════════════════════════════════════════════════════════

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
_STRING_LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
_KEY_VALUE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*(.+?)\s*,?\s*$')
_OPEN_NESTED = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*\{\s*$')
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _unescape(raw: str) -> str:
    out = []
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "\\":
            if i + 1 >= len(raw):
                raise AssertionError("Escape GDScript terpotong: %r" % raw)
            nxt = raw[i + 1]
            if nxt not in _ESCAPES:
                raise AssertionError(
                    "Escape GDScript tak dikenal '\\%s' di %r — perbarui "
                    "parser oracle ini kalau Localization.gd memang "
                    "memakainya" % (nxt, raw))
            out.append(_ESCAPES[nxt])
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _strip_comment(line: str) -> str:
    """Buang komentar `#` di luar string literal (untuk hitung kurung)."""
    out = []
    in_str = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
                out.append(c)
            elif c == "#":
                break
            else:
                out.append(c)
        i += 1
    return "".join(out)


def _scan_code(code: str):
    """Hitung kurung DI LUAR string literal -> (opened, closed, has_bracket).

    Kurung di dalam teks (`"{count} antrean"`) tidak boleh dihitung sebagai
    struktur, jadi pemindaian ini sadar string + escape.
    """
    opened = closed = 0
    has_bracket = False
    in_str = False
    i = 0
    while i < len(code):
        c = code[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
        elif c in "{[":
            opened += 1
            has_bracket = True
        elif c in "}]":
            closed += 1
        i += 1
    return opened, closed, has_bracket


def _logical_lines(lines, start: int):
    """Gabungkan continuasi `\` GDScript jadi satu baris logis.

    Menghasilkan (text, depth_sebelum_baris) mulai `start` sampai kurung
    seimbang lagi (blok const Dictionary/Array selesai). Baris yang isinya
    hanya komentar dilewati.
    """
    depth = 0
    buf = ""
    started = False
    for idx in range(start, len(lines)):
        piece = lines[idx].rstrip()
        continued = piece.endswith("\\")
        if continued:
            piece = piece[:-1].rstrip()
        code = _strip_comment(piece).strip()
        if not code and not continued:
            continue
        buf = (buf + " " + code) if buf else code
        if continued:
            continue
        opened, closed, has_bracket = _scan_code(buf)
        if has_bracket:
            started = True
        yield buf, depth
        depth += opened - closed
        buf = ""
        if started and depth <= 0:
            return
    raise AssertionError("Blok const GDScript tidak pernah tertutup")


def _find_const(lines, name: str) -> int:
    pat = re.compile(r"^const\s+%s\b" % re.escape(name))
    for i, line in enumerate(lines):
        if pat.match(line.strip()) or pat.match(line):
            return i
    raise AssertionError("const %s tidak ditemukan di Localization.gd" % name)


def _literals_only(expr: str, where: str) -> str:
    """Nilai harus concatenation literal string murni (`"a" + "b"`)."""
    rest = expr.strip()
    if rest.endswith(","):
        rest = rest[:-1].strip()
    pieces = []
    pos = 0
    while pos < len(rest):
        m = _STRING_LITERAL.match(rest, pos)
        if m:
            pieces.append(_unescape(m.group(1)))
            pos = m.end()
            while pos < len(rest) and rest[pos].isspace():
                pos += 1
            if pos < len(rest) and rest[pos] == "+":
                pos += 1
                while pos < len(rest) and rest[pos].isspace():
                    pos += 1
            continue
        raise AssertionError(
            "Nilai %s bukan literal string murni: %r — oracle hanya bisa "
            "membaca tabel statis (tanpa ekspresi/%/pemanggilan fungsi)"
            % (where, rest))
    if not pieces:
        raise AssertionError("Nilai %s kosong: %r" % (where, expr))
    return "".join(pieces)


def _key_of(expr: str, where: str) -> str:
    m = re.match(r'\s*"((?:[^"\\]|\\.)*)"\s*$', expr)
    if not m:
        raise AssertionError("Kunci %s bukan literal string: %r" % (where, expr))
    return _unescape(m.group(1))


def parse_flat_dict(lines, name: str) -> dict:
    """`const X := {"a": "b", ...}` -> dict (satu tingkat)."""
    start = _find_const(lines, name)
    out = {}
    for text, depth in _logical_lines(lines, start):
        body = text.strip()
        if depth == 0:
            continue
        if body in ("}", "},"):
            continue
        m = _KEY_VALUE.match(body)
        if not m:
            raise AssertionError(
                "Baris tak terduga di const %s: %r" % (name, body))
        out[_unescape(m.group(1))] = _literals_only(m.group(2), "%s.%s"
                                                   % (name, m.group(1)))
    return out


def parse_nested_dict(lines, name: str) -> dict:
    """`const X := {"id": {...}, "en": {...}}` -> dict of dict."""
    start = _find_const(lines, name)
    out = {}
    current = None
    for text, depth in _logical_lines(lines, start):
        body = text.strip()
        if depth == 0:
            continue
        if depth == 1:
            m = _OPEN_NESTED.match(body)
            if m:
                current = _unescape(m.group(1))
                out[current] = {}
                continue
            if body in ("}", "},"):
                current = None
                continue
            raise AssertionError(
                "Baris tingkat-1 tak terduga di const %s: %r" % (name, body))
        if depth == 2:
            if body in ("}", "},"):
                continue
            m = _KEY_VALUE.match(body)
            if not m or current is None:
                raise AssertionError(
                    "Baris tingkat-2 tak terduga di const %s: %r" % (name, body))
            key = _unescape(m.group(1))
            if key in out[current]:
                raise AssertionError("Kunci ganda %s.%s" % (current, key))
            out[current][key] = _literals_only(
                m.group(2), "%s.%s.%s" % (name, current, key))
            continue
        raise AssertionError("Kedalaman %d tak terduga di const %s: %r"
                             % (depth, name, body))
    return out


def parse_list(lines, name: str) -> list:
    start = _find_const(lines, name)
    joined = ""
    for text, _depth in _logical_lines(lines, start):
        joined = text
        break
    m = re.search(r"\[(.*)\]", joined)
    if not m:
        raise AssertionError("const %s bukan array literal: %r" % (name, joined))
    return [_unescape(x) for x in _STRING_LITERAL.findall(m.group(1))]


def parse_scalar(lines, name: str) -> str:
    start = _find_const(lines, name)
    m = re.search(r'^const\s+%s\s*:=\s*(.+)$' % re.escape(name),
                  lines[start].strip())
    if not m:
        raise AssertionError("const %s tidak terbaca: %r" % (name, lines[start]))
    return _literals_only(m.group(1), name)


# ══════════════════════════════════════════════════════════
#  Audit placeholder (subset str.format yang diport)
# ══════════════════════════════════════════════════════════

_FIELD = re.compile(r"\{([^{}]*)\}")

## Nilai contoh per placeholder — dipakai baterai tr() fixture. Placeholder
## baru yang tidak ada di sini membuat oracle GAGAL (bukan menebak nilai),
## supaya kasus uji selalu mencerminkan pemanggil pygame sungguhan.
SAMPLE_VALUES = {
    "hero": "Kaizen",
    "item": "Moon Shard",
    "items": "Moon Shard, Dead Edge",
    "count": 3,
    "page": 2,
}


def placeholders(template: str) -> list:
    """Nama field `{nama}` dalam template, apa adanya (duplikat dilepas)."""
    seen = []
    for field in _FIELD.findall(template):
        if field not in seen:
            seen.append(field)
    return seen


def audit_placeholders(table: dict) -> dict:
    used = {}
    for lang, entries in table.items():
        for key, template in entries.items():
            fields = placeholders(template)
            for field in fields:
                if not _IDENTIFIER.match(field):
                    raise AssertionError(
                        "Placeholder %s.%s = %r bukan `{nama}` polos. "
                        "MysticLocalization._py_format hanya mengimplementasi "
                        "subset itu (lihat header Localization.gd) — pakai "
                        "nama polos atau perluas _py_format + oracle ini."
                        % (lang, key, field))
                if field not in SAMPLE_VALUES:
                    raise AssertionError(
                        "Placeholder baru {%s} di %s.%s belum punya nilai "
                        "contoh di SAMPLE_VALUES oracle" % (field, lang, key))
            if "{{" in template or "}}" in template:
                raise AssertionError(
                    "Escape kurung ({{ / }}) di %s.%s belum dipakai tabel "
                    "pygame — kalau memang perlu, kunci perilakunya di "
                    "oracle + LocalizationParityTest" % (lang, key))
            used[key] = fields
    return used


# ══════════════════════════════════════════════════════════
#  Baterai tr() dari localization.py ASLI
# ══════════════════════════════════════════════════════════

def kind_of(value) -> str:
    """Tipe Python untuk encoder fixture (JSON Godot tidak mempertahankannya)."""
    if isinstance(value, bool):
        return "bool"
    if value is None:
        return "null"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


def encode_values(values: dict) -> list:
    """[(nama, tipe, nilai)] — JSON Godot mengubah semua angka jadi float
    (dan bool/null punya `str()` yang beda), jadi tipe Python aslinya ikut
    disimpan supaya harness Godot bisa membangun kembali Dictionary yang
    setara (pola yang sama dipakai fixture `hero_items`)."""
    return [[name, kind_of(value), value] for name, value in values.items()]


def sample_for(fields: list) -> dict:
    return {name: SAMPLE_VALUES[name] for name in fields}


def build_fixture() -> dict:
    table = localization._TEXT
    used = audit_placeholders(table)

    tr_cases = []
    for lang in localization.LANGUAGES:
        for key, template in table[lang].items():
            values = sample_for(used[key])
            localization.set_language(lang)
            out = localization.tr(key, **values)
            tr_cases.append({
                "lang": lang,
                "key": key,
                "values": encode_values(values),
                "out": out,
            })

    # ── kasus tepi (semua dievaluasi localization.py asli) ──
    edge_cases = []

    def edge(lang, key, values, note):
        localization.set_language(lang)
        edge_cases.append({
            "lang": lang,
            "key": key,
            "values": encode_values(values),
            "out": localization.tr(key, **values),
            "note": note,
        })

    edge("id", "kunci_tak_ada", {}, "kunci tak dikenal -> kunci mentah")
    edge("en", "kunci_tak_ada", {}, "kunci tak dikenal -> kunci mentah")
    edge("id", "queued", {}, "nilai hilang (KeyError) -> template mentah")
    edge("en", "forge_delivered", {"hero": "Kaizen"},
         "sebagian nilai hilang -> template mentah")
    edge("id", "dead", {"hero": "Kaizen"}, "nilai berlebih diabaikan")
    edge("en", "language", {"count": 3, "page": 9}, "tanpa placeholder")
    edge("id", "queued_item_count", {"count": 0}, "count 0 tetap disisipkan")
    edge("en", "shop_page_label", {"page": 12}, "page dua digit")

    # Kunci yang hanya ada di satu bahasa harus jatuh ke "id"
    # (localization.py:94-96). Dibangun di atas salinan tabel, bukan dengan
    # mengubah modul pygame.
    only_id_key = None
    for key in table["id"]:
        if key not in table["en"]:
            only_id_key = key
            break
    fallback_cases = []
    if only_id_key is not None:  # pragma: no cover - tabel sekarang simetris
        localization.set_language("en")
        fallback_cases.append({
            "lang": "en",
            "key": only_id_key,
            "values": [],
            "out": localization.tr(only_id_key),
            "note": "kunci hanya ada di id -> fallback tabel id",
        })

    # ── set_language / get_language / label ──
    set_language_cases = []
    for candidate in ["id", "en", "invalid", "", "ID", "en-US", None]:
        got = localization.set_language(candidate)
        set_language_cases.append({
            "in": candidate,
            "out": got,
            "active": localization.get_language(),
        })

    label_cases = []
    for active in localization.LANGUAGES:
        localization.set_language(active)
        label_cases.append({"lang": None, "active": active,
                            "out": localization.get_language_label()})
        label_cases.append({"lang": active, "active": active,
                            "out": localization.get_language_label(active)})
    localization.set_language("id")
    for unknown in ["invalid", "fr", ""]:
        label_cases.append({"lang": unknown, "active": "id",
                            "out": localization.get_language_label(unknown)})

    localization.set_language("id")
    return {
        "generated_from": "localization.py (oracle) — jangan edit tangan",
        "default_language": "id",
        "languages": list(localization.LANGUAGES),
        "labels": dict(localization.LANGUAGE_LABELS),
        "key_order": {lang: list(table[lang]) for lang in table},
        "text": {lang: dict(table[lang]) for lang in table},
        "placeholders": used,
        "tr_cases": tr_cases,
        "edge_cases": edge_cases,
        "fallback_cases": fallback_cases,
        "set_language_cases": set_language_cases,
        "label_cases": label_cases,
        "format_cases": build_format_cases(),
        "py_str_cases": build_py_str_cases(),
        "initial_language": "id",
    }


def build_format_cases() -> list:
    """Semantik `template.format(**values)` + cabang except localization.tr.

    Dievaluasi dengan Python ASLI (bukan ditebak), termasuk bentuk yang
    membuat Python melempar KeyError/ValueError sehingga localization.tr
    mengembalikan template mentah. `MysticLocalization._py_format` harus
    menghasilkan kolom `out` yang sama.
    """
    raw = [
        ("{hero} membeli {item}!", {"hero": "Kaizen", "item": "Moon Shard"},
         "dua placeholder berurutan"),
        ("+{count} antrean", {"count": 3}, "satu placeholder int"),
        ("+{count} antrean", {"count": 0}, "nol tetap disisipkan"),
        ("HAL {page}", {"page": 12}, "page dua digit"),
        ("DIMILIKI: {count}", {"count": 3, "hero": "Kaizen"},
         "nilai berlebih diabaikan"),
        ("MATI", {}, "tanpa placeholder"),
        ("", {}, "template kosong"),
        ("(ketuk: info  •  tahan/kanan: drop)", {}, "spasi ganda + bullet"),
        ("MATI — pembelian baru dikirim setelah respawn", {}, "em dash"),
        ("{hero} membeli {item}!", {"hero": "Kaizen"},
         "nilai hilang -> KeyError -> template mentah"),
        ("{count}", {}, "placeholder tunggal tanpa nilai"),
        ("{a}-{b}-{a}", {"a": "x", "b": "y"}, "placeholder berulang"),
        ("{{literal}}", {}, "escape kurung -> {literal}"),
        ("100% {hero}", {"hero": "Kaizen"}, "persen bukan placeholder"),
        ("{x", {"x": 1}, "kurung buka tak tertutup -> ValueError -> mentah"),
        ("a}b", {}, "kurung tutup tunggal -> ValueError -> mentah"),
        ("{hero:>}x", {}, "format spec tidak dipakai tabel ini"),
        ("{count}", {"count": 1.5}, "float desimal"),
        ("{count}", {"count": 3.0}, "float bulat -> 3.0 (bukan 3)"),
        ("{flag}", {"flag": True}, "bool Python -> True"),
        ("{v}", {"v": None}, "None -> None"),
    ]
    cases = []
    for template, values, note in raw:
        try:
            out = template.format(**values)
        except (KeyError, ValueError):
            out = template  # cabang except localization.tr:99-100
        cases.append({
            "template": template,
            "values": encode_values(values),
            "out": out,
            "note": note,
        })
    return cases


def build_py_str_cases() -> list:
    """`str()` Python untuk nilai yang disisipkan placeholder.

    Godot membuang ".0" float bulat dan menulis bool/null berbeda, jadi
    `MysticLocalization._py_str` mengoreksinya — kolom `out` di bawah adalah
    keluaran `str()` Python sungguhan.
    """
    values = [3, 0, -7, 3.0, 1.5, 0.0, -2.25, True, False, None, "Kaizen",
              "", "MATI — pembelian"]
    return [{"kind": kind_of(v), "in": v, "out": str(v)} for v in values]


# ══════════════════════════════════════════════════════════
#  Perbandingan tabel GDScript vs localization.py
# ══════════════════════════════════════════════════════════

def check_gdscript(fixture: dict) -> None:
    if not GD_PATH.exists():
        raise AssertionError("Port Godot hilang: %s" % GD_PATH)
    lines = GD_PATH.read_text(encoding="utf-8").splitlines()

    gd_default = parse_scalar(lines, "DEFAULT_LANGUAGE")
    if gd_default != fixture["default_language"]:
        raise AssertionError(
            "DEFAULT_LANGUAGE GDScript %r != bahasa bawaan pygame %r"
            % (gd_default, fixture["default_language"]))
    if gd_default != localization._LANGUAGE:
        raise AssertionError(
            "DEFAULT_LANGUAGE GDScript %r != _LANGUAGE awal localization.py %r"
            % (gd_default, localization._LANGUAGE))

    gd_languages = parse_list(lines, "LANGUAGES")
    if gd_languages != list(localization.LANGUAGES):
        raise AssertionError(
            "LANGUAGES GDScript %r != localization.LANGUAGES %r (urutan "
            "dipakai cycler bahasa _core.py:7297-7303)"
            % (gd_languages, list(localization.LANGUAGES)))

    gd_labels = parse_flat_dict(lines, "LANGUAGE_LABELS")
    if gd_labels != dict(localization.LANGUAGE_LABELS):
        raise AssertionError(
            "LANGUAGE_LABELS berbeda:\n  GDScript: %r\n  pygame  : %r"
            % (gd_labels, dict(localization.LANGUAGE_LABELS)))

    gd_text = parse_nested_dict(lines, "TEXT")
    if set(gd_text) != set(localization._TEXT):
        raise AssertionError(
            "Bahasa di tabel GDScript %r != pygame %r"
            % (sorted(gd_text), sorted(localization._TEXT)))
    diffs = []
    for lang, entries in localization._TEXT.items():
        gd_entries = gd_text.get(lang, {})
        if list(gd_entries) != list(entries):
            missing = [k for k in entries if k not in gd_entries]
            extra = [k for k in gd_entries if k not in entries]
            diffs.append("urutan/kunci %s berbeda (kurang=%s lebih=%s)"
                         % (lang, missing, extra))
            continue
        for key, template in entries.items():
            if gd_entries[key] != template:
                diffs.append("%s.%s:\n    GDScript: %r\n    pygame  : %r"
                             % (lang, key, gd_entries[key], template))
    if diffs:
        raise AssertionError("Tabel teks Localization.gd != localization.py:\n  "
                             + "\n  ".join(diffs))

    # API permukaan: nama fungsi yang harus ada di port.
    source = GD_PATH.read_text(encoding="utf-8")
    for func in ("set_language", "get_language", "get_language_label",
                 "tr_text", "is_english", "has_text", "languages",
                 "language_labels", "text_table"):
        if not re.search(r"^static func %s\(" % func, source, re.M):
            raise AssertionError("static func %s() hilang dari Localization.gd"
                                 % func)
    if re.search(r"^static func tr\(", source, re.M):
        raise AssertionError(
            "Localization.gd mendefinisikan `tr` — bentrok dengan method "
            "native Object.tr() (TranslationServer). Pakai tr_text().")
    print("[oracle] tabel GDScript == localization.py: %d bahasa, %d kunci, "
          "%d label" % (len(gd_text), len(gd_text["id"]), len(gd_labels)))


## Pemanggil teks di Godot: `MysticLocalization.tr_text("kunci")` dan pintasan
## per-panel `_loc("kunci")` / `loc("kunci")` (mis. ShopPanel._loc, yang
## membungkus tr_text supaya situs pemanggil tidak memanjang dua baris).
## Ketiganya diaudit — tanpa pola kedua, kunci salah ketik di jalur pintasan
## lolos tanpa suara dan cuma kelihatan sebagai teks mentah di layar.
TEXT_CALL_PATTERN = r'(?:\btr_text|\b_?loc)\(\s*"([^"]+)"'


def check_call_sites(fixture: dict) -> None:
    """Setiap kunci yang dipakai kode Godot harus ada di tabel (closed world)."""
    known = set(fixture["text"]["id"])
    used = {}
    pattern = re.compile(TEXT_CALL_PATTERN)
    for path in sorted((ROOT / "godot").rglob("*.gd")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("godot/tests/"):
            continue  # harness memang memanggil kunci sengaja-tak-ada
        if path == GD_PATH:
            continue  # contoh pemakaian di header bukan pemanggil
        # Komentar dibuang: contoh `tr_text("...")` di dokumentasi bukan
        # pemanggil sungguhan.
        code = "\n".join(_strip_comment(line)
                         for line in path.read_text(encoding="utf-8")
                         .splitlines())
        for key in pattern.findall(code):
            used.setdefault(key, []).append(rel)
    unknown = {k: v for k, v in used.items() if k not in known}
    if unknown:
        raise AssertionError(
            "Kunci tr_text()/loc() tak dikenal di kode Godot (typo?): %s"
            % json.dumps(unknown, ensure_ascii=False))
    silent = sorted(known - set(used))
    print("[oracle] pemakai tr_text()/loc() di Godot: %s"
          % (", ".join(sorted(used)) or "-"))
    print("[oracle] kunci diport tapi belum ada pemakainya di Godot (%d): %s"
          % (len(silent), ", ".join(silent)))


# ══════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixture", action="store_true",
                        help="tulis ulang godot/tests/fixtures/localization.json")
    args = parser.parse_args()

    fixture = build_fixture()
    check_gdscript(fixture)
    check_call_sites(fixture)

    payload = json.dumps(fixture, indent=2, ensure_ascii=False,
                         sort_keys=True) + "\n"
    if args.write_fixture:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(payload, encoding="utf-8")
        print("[oracle] fixture ditulis: %s (%d kasus tr, %d kasus tepi)"
              % (FIXTURE.relative_to(ROOT), len(fixture["tr_cases"]),
                 len(fixture["edge_cases"])))
        return 0

    if not FIXTURE.exists():
        raise AssertionError(
            "Fixture hilang: %s — jalankan "
            "`python3 tools/test_godot_localization_parity.py --write-fixture`"
            % FIXTURE.relative_to(ROOT))
    current = FIXTURE.read_text(encoding="utf-8")
    if current != payload:
        stored = json.loads(current)
        stale = [section for section in fixture
                 if section != "generated_from"
                 and stored.get(section) != fixture[section]]
        raise AssertionError(
            "Fixture localization.json basi terhadap localization.py "
            "(seksi: %s) — regenerasi: python3 tools/%s --write-fixture"
            % (", ".join(stale) or "format/urutan", Path(__file__).name))
    print("[oracle] fixture segar: %d kunci x %d bahasa, %d kasus tr, "
          "%d kasus tepi, %d kasus format, %d kasus str(), "
          "%d kasus set_language, %d kasus label"
          % (len(fixture["text"]["id"]), len(fixture["languages"]),
             len(fixture["tr_cases"]), len(fixture["edge_cases"]),
             len(fixture["format_cases"]), len(fixture["py_str_cases"]),
             len(fixture["set_language_cases"]), len(fixture["label_cases"])))
    print("Localization parity: OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print("FAIL: %s" % exc)
        sys.exit(1)
