#!/usr/bin/env python3
"""Self-test maps_processor.cpp di luar engine (butuh g++ saja, tanpa godot-cpp).

    python3 tools/test_maps_cpp_selftest.py

Menyalakan kode C++ hasil tools/gen_maps_cpp.py APA ADANYA lewat stub
Variant (godot/gdext/mystic_maps/selftest), lalu membandingkan balasannya
dengan oracle map_components/_bundle.py ASLI:

  * palet (53 warna + TILE_SIZE), 54 tema (nilai + kind + URUTAN kunci),
    theme_names/theme_index/get_theme fallback,
  * make_curved_path (baterai tepi: <2 waypoint, smoothness 0/1/5/8/10,
    koordinat negatif) + generate_lanes/generate_river (4 ukuran map),
  * generate_decorations (kanonis 1280x720 ala MapRenderer + 800x600 +
    posisi toko non-standar) — replika MT19937 vs `random` CPython.

Pola tools/test_levels_cpp_selftest.py. Sengaja jalan SEBELUM build godot-cpp
di CI: regresi data/logika gagal cepat (±detik) dan murah.
"""
import ast
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gen_maps_cpp as gen

SELFTEST = ROOT / "godot" / "gdext" / "mystic_maps" / "selftest"

_checks = 0
_failures = []


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[maps_selftest] FAIL: %s" % message)


def section(title):
    print("[maps_selftest] ── %s ──" % title)


# ══════════════════════════════════════════════════════════
#  Oracle Python (tanpa pygame: AST + exec generator mandiri)
# ══════════════════════════════════════════════════════════


def load_oracle():
    palettes, themes, order, _lines, _pathgen = gen.parse_bundle()
    ordered = [(const, key, themes[const]) for key, const in order]
    source = gen.SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)
    ns_node = [n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "_NS_generators"][0]
    segment = ast.get_source_segment(source, ns_node)
    gns = {"TILE_SIZE": 16, "CRYSTAL_BLUE_L": (100, 170, 240)}
    import math
    import random
    gns["math"] = math
    gns["random"] = random
    exec(compile(segment, str(gen.SRC), "exec"), gns)
    return palettes, ordered, gns["_NS_generators"]


# ══════════════════════════════════════════════════════════
#  Render perintah + parse balasan teks protokol
# ══════════════════════════════════════════════════════════


def v2_text(pt):
    return "v2:%s,%s" % (pt[0], pt[1])


def v2s_text(pts):
    return "v2s:[%s]" % ",".join(v2_text(p) for p in pts)


def parse_reply(text):
    """Teks protokol -> (kind, nilai) Python. kind: nil/bool/int/float/str/
    color/v2/v2s/pc/array/dict. Gagal keras kalau bentuk tak dikenal."""
    pos = 0

    def peek(n=1):
        return text[pos:pos + n]

    def take(n=1):
        nonlocal pos
        out = text[pos:pos + n]
        pos += n
        return out

    def parse_value():
        nonlocal pos
        for prefix in ("nil:", "bool:", "int:", "float:", "str:", "color:",
                       "v2s:", "v2:", "pc:", "array:", "dict:"):
            if text.startswith(prefix, pos):
                pos += len(prefix)
                return parse_prefixed(prefix[:-1])
        raise ValueError("awalan tak dikenal di %r" % text[pos:pos + 20])

    def parse_prefixed(kind):
        nonlocal pos
        if kind == "nil":
            assert take(4) == "null", text
            return ("nil", None)
        if kind == "bool":
            if text.startswith("true", pos):
                pos += 4
                return ("bool", True)
            assert text.startswith("false", pos), text[pos:pos + 10]
            pos += 5
            return ("bool", False)
        if kind == "int":
            start = pos
            if peek() == "-":
                take()
            while peek().isdigit():
                take()
            return ("int", int(text[start:pos]))
        if kind == "float":
            start = pos
            while peek() and (peek().isdigit() or peek() in ".-+eE"):
                take()
            return ("float", float(text[start:pos]))
        if kind == "str":
            start = pos
            # Nilai str kami tidak mengandung , = ] } (diasert di bawah).
            while peek() and peek() not in ",=]}":
                take()
            return ("str", text[start:pos])
        if kind == "color":
            nums = []
            for i in range(4):
                start = pos
                while peek().isdigit():
                    take()
                nums.append(int(text[start:pos]))
                if i < 3:
                    assert take() == ",", text
            return ("color", tuple(nums))
        if kind == "v2":
            nums = []
            for i in range(2):
                start = pos
                while peek() and (peek().isdigit() or peek() in ".-+eE"):
                    take()
                nums.append(float(text[start:pos]))
                if i < 1:
                    assert take() == ",", text
            return ("v2", tuple(nums))
        if kind in ("v2s", "pc", "array"):
            assert take() == "[", text
            items = []
            if peek() != "]":
                while True:
                    items.append(parse_value())
                    if peek() == ",":
                        take()
                        continue
                    break
            assert take() == "]", text
            return (kind, items)
        if kind == "dict":
            assert take() == "{", text
            pairs = []
            if peek() != "}":
                while True:
                    key = parse_value()
                    assert take() == "=", text
                    pairs.append((key, parse_value()))
                    if peek() == ",":
                        take()
                        continue
                    break
            assert take() == "}", text
            return ("dict", pairs)
        raise AssertionError(kind)

    value = parse_value()
    assert pos == len(text), "sisa tak terparse: %r" % text[pos:pos + 30]
    return value


def compare(exp_kind, exp_val, got, path):
    """Bandingkan satu leaf; got = (kind, nilai) hasil parse_reply."""
    got_kind, got_val = got
    expect(got_kind == exp_kind, "%s: kind %s != %s" % (path, got_kind, exp_kind))
    if got_kind != exp_kind:
        return
    if exp_kind == "v2":
        ok = len(got_val) == 2 and float(exp_val[0]) == got_val[0] \
            and float(exp_val[1]) == got_val[1]
        expect(ok, "%s: v2 %s != %s" % (path, got_val, exp_val))
    elif exp_kind in ("v2s", "pc", "array"):
        expect(len(got_val) == len(exp_val),
               "%s: panjang %d != %d" % (path, len(got_val), len(exp_val)))
        for i, (e, g) in enumerate(zip(exp_val, got_val)):
            compare(e[0], e[1], g, "%s[%d]" % (path, i))
    elif exp_kind == "dict":
        got_keys = [k for k, _ in got_val]
        exp_keys = [k for k, _ in exp_val]
        expect(got_keys == exp_keys, "%s: urutan kunci %s != %s"
               % (path, got_keys[:8], exp_keys[:8]))
        for (ek, ev), (gk, gv) in zip(exp_val, got_val):
            if ek == gk:
                compare(ev[0], ev[1], gv, "%s.%s" % (path, ek[1] if ek[0] == "str" else ek))
    else:
        expect(got_val == exp_val, "%s: %r != %r" % (path, got_val, exp_val))


def py_to_tagged(value):
    """Nilai oracle Python -> (kind, nilai) pembanding."""
    if value is None:
        return ("nil", None)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, float):
        return ("float", value)
    if isinstance(value, str):
        assert not any(c in value for c in ",=]}"), value
        return ("str", value)
    if isinstance(value, tuple) and len(value) in (3, 4) \
            and all(isinstance(c, int) for c in value):
        full = value if len(value) == 4 else value + (255,)
        return ("color", full)
    if isinstance(value, (tuple, list)) and len(value) == 3 \
            and all(isinstance(c, tuple) for c in value):
        return ("pc", [py_to_tagged(c) for c in value])
    raise AssertionError("nilai tak terpeta: %r" % (value,))


def theme_expected(row):
    return ("dict", [(("str", k), py_to_tagged(v)) for k, v in row.items()])


# ══════════════════════════════════════════════════════════
#  Perintah
# ══════════════════════════════════════════════════════════


def build_commands(palettes, ordered, ns):
    PathGenerator = ns.PathGenerator
    DecorationGenerator = ns.DecorationGenerator
    total_entries = sum(len(row) for _, _, row in ordered)
    first, last = ordered[0][1], ordered[-1][1]
    commands = []  # (id, teks_perintah, (kind, nilai) ekspektasi, label)

    def add(cmd_id, text, expected, label):
        commands.append((cmd_id, text, expected, label))

    add("bind", "bind", ("nil", None), "bind methods")
    add("sig", "signature", ("str", "54:%s-%s:%d" % (first, last, total_entries)),
        "catalog_signature")
    add("count", "count", ("int", len(ordered)), "theme_count")
    tile_size = [v for n, v, _ in palettes if n == "TILE_SIZE"][0]
    add("tile", "tile", ("int", tile_size), "tile_size")
    add("names", "names",
        ("array", [("str", key) for _, key, _ in ordered]), "theme_names")
    add("palettes", "palettes",
        ("dict", [(("str", n), ("color", v + (255,)))
                  for n, v, _ in palettes if n != "TILE_SIZE"]), "palettes")
    add("allsize", "all_themes_size", ("int", len(ordered)), "all_themes size")

    for i, (const, key, row) in enumerate(ordered):
        add("theme%02d" % i, "theme\tint:%d" % i, theme_expected(row), const)
    # Di luar jangkauan -> dict kosong.
    add("theme_oob_hi", "theme\tint:99", ("dict", []), "build_theme OOB")
    add("theme_oob_lo", "theme\tint:-1", ("dict", []), "build_theme OOB negatif")

    # get_theme: tiap nama + baterai fallback.
    for _const, key, row in ordered:
        add("get_%s" % key, "theme_by_name\tstr:%s" % key,
            theme_expected(row), "get_theme(%s)" % key)
    forest_row = ordered[0][2]
    for unknown in ("", "FOREST", "Forest ", "hutan", "forestx", "123"):
        add("fb_%s" % (unknown or "empty"), "theme_by_name\tstr:%s" % unknown,
            theme_expected(forest_row), "fallback(%r)" % unknown)
    for i, (_const, key, _row) in enumerate(ordered):
        add("idx_%s" % key, "theme_index\tstr:%s" % key,
            ("int", i), "theme_index(%s)" % key)
    add("idx_unknown", "theme_index\tstr:tidak_ada", ("int", -1), "theme_index OOB")

    # ── make_curved_path ──
    curve_cases = [
        ([], 10), ([(7, 9)], 10), ([(0, 0), (10, 10)], 5),
        ([(0, 0), (100, 50), (200, 40)], 5),
        ([(0, 0), (100, 50), (200, 40)], 1),
        ([(0, 0), (100, 50), (200, 40)], 0),
        ([(0, 0), (100, 50), (200, 40)], 8),
        ([(0, 0), (100, 50), (200, 40)], 10),
        ([(-50, -30), (100, 80), (300, -10)], 5),
        ([(5, 5), (5, 5), (5, 5)], 4),
        ([(i * 37 % 300, i * 53 % 200) for i in range(9)], 7),
    ]
    for n, (wps, smooth) in enumerate(curve_cases):
        exp = PathGenerator.make_curved_path(list(wps), smoothness=smooth)
        exp_tagged = ("v2s", [(("v2", (float(x), float(y)))) for x, y in exp])
        # Passthrough len<2: C++ mengembalikan input float-nya; oracle tuple.
        add("curve%02d" % n, "curve\t%s\tint:%d" % (v2s_text(wps), smooth),
            exp_tagged, "curve case %d (n=%d s=%d)" % (n, len(wps), smooth))

    # ── lanes + river, 4 ukuran ──
    for w, h in ((1280, 720), (800, 600), (1920, 1080), (320, 240)):
        top, mid, bot = PathGenerator.generate_lanes(w, h)
        lanes_exp = ("dict", [
            (("str", "top"), ("v2s", [(("v2", (float(x), float(y)))) for x, y in top])),
            (("str", "mid"), ("v2s", [(("v2", (float(x), float(y)))) for x, y in mid])),
            (("str", "bot"), ("v2s", [(("v2", (float(x), float(y)))) for x, y in bot])),
        ])
        add("lanes_%dx%d" % (w, h), "lanes\tint:%d\tint:%d" % (w, h),
            lanes_exp, "lanes %dx%d (%d/%d/%d titik)"
            % (w, h, len(top), len(mid), len(bot)))
        river = PathGenerator.generate_river(w, h)
        add("river_%dx%d" % (w, h), "river\tint:%d\tint:%d" % (w, h),
            ("v2s", [(("v2", (float(x), float(y)))) for x, y in river]),
            "river %dx%d (%d titik)" % (w, h, len(river)))

    # ── dekor: kanonis MapRenderer + varian ──
    top, mid, bot = PathGenerator.generate_lanes(1280, 720)
    river = PathGenerator.generate_river(1280, 720)
    all_lane = top + bot + mid  # urutan concat MapRenderer.__init__!
    decor_cases = [
        ("canon", 1280, 720, all_lane, river, [(340, 540), (940, 180)]),
        ("small", 800, 600,
         sum([list(PathGenerator.generate_lanes(800, 600)[i]) for i in (0, 2, 1)], []),
         PathGenerator.generate_river(800, 600), [(340, 540), (940, 180)]),
        ("shops", 1280, 720, all_lane, river, [(100, 100), (200, 200)]),
    ]
    for tag, w, h, lane_pts, river_pts, shops in decor_cases:
        gen = DecorationGenerator(w, h, list(lane_pts), list(river_pts), list(shops))
        data = gen.generate_all()
        cats = []
        for cat, entries in data.items():
            items = []
            for entry in entries:
                fields = []
                for field in entry:
                    if isinstance(field, bool):
                        fields.append(("bool", field))
                    elif isinstance(field, int):
                        fields.append(("int", field))
                    elif isinstance(field, str):
                        fields.append(("str", field))
                    elif isinstance(field, tuple):
                        fields.append(("color", field + (255,)))
                    else:
                        raise AssertionError(field)
                items.append(("array", fields))
            cats.append((("str", cat), ("array", items)))
        lane_text = v2s_text(lane_pts)
        river_text = v2s_text(river_pts)
        shops_text = "[%s]" % ",".join(v2_text(s) for s in shops)
        add("decor_%s" % tag,
            "decor\tint:%d\tint:%d\t%s\t%s\t%s" % (w, h, lane_text, river_text, shops_text),
            ("dict", cats),
            "decor %s (%d entri)" % (tag, sum(len(v) for v in data.values())))
    return commands


# ══════════════════════════════════════════════════════════
#  Driver
# ══════════════════════════════════════════════════════════


def find_compiler():
    for cand in ("g++", "c++", "clang++"):
        path = shutil.which(cand)
        if path:
            return path
    raise SystemExit("[maps_selftest] GAGAL: tidak ada compiler C++ (g++/c++/clang++)")


def compile_selftest(compiler, out_path):
    cmd = [compiler, "-std=c++17", "-O0",
           "-I", str(SELFTEST), "-I", str(SELFTEST / "shim"),
           "-o", str(out_path), str(SELFTEST / "maps_selftest.cpp")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    expect(proc.returncode == 0,
           "compile gagal:\n%s" % (proc.stderr[-3000:] if proc.stderr else "?"))
    return proc.returncode == 0


def run_binary(binary, commands):
    payload = "".join("%s\t%s\n" % (cid, text) for cid, text, _, _ in commands)
    proc = subprocess.run([str(binary)], input=payload,
                          capture_output=True, text=True, timeout=300)
    expect(proc.returncode == 0, "selftest exit %d: %s"
           % (proc.returncode, (proc.stderr or "")[-500:]))
    results = {}
    for line in (proc.stdout or "").splitlines():
        if not line.strip():
            continue
        cid, _, reply = line.partition("\t")
        results[cid] = reply
    return results


def main():
    section("oracle Python")
    palettes, ordered, ns = load_oracle()
    print("[maps_selftest] oracle: %d tema, %d kunci union, %d palet"
          % (len(ordered), len({k for _, _, r in ordered for k in r}),
             len([p for p in palettes if p[0] != "TILE_SIZE"])))
    commands = build_commands(palettes, ordered, ns)
    print("[maps_selftest] %d perintah" % len(commands))

    section("compile maps_selftest.cpp")
    binary = Path("/tmp/maps_selftest_fase35")
    if not compile_selftest(find_compiler(), binary):
        print("[maps_selftest] FAIL: %d kegagalan dari %d cek" % (len(_failures), _checks))
        return 1

    section("jalankan + bandingkan")
    results = run_binary(binary, commands)
    for cid, _text, expected, label in commands:
        reply = results.get(cid)
        expect(reply is not None and not reply.startswith("error:"),
               "%s: %s" % (label, reply if reply else "TIDAK ADA BALASAN"))
        if reply is None or reply.startswith("error:"):
            continue
        try:
            got = parse_reply(reply)
        except (ValueError, AssertionError) as exc:
            expect(False, "%s: balasan tak terparse (%s): %s"
                   % (label, exc, reply[:160]))
            continue
        compare(expected[0], expected[1], got, label)

    if _failures:
        print("\n[maps_selftest] FAIL: %d kegagalan dari %d cek" % (len(_failures), _checks))
        return 1
    print("\n[maps_selftest] PASS: %d cek (C++ == oracle _bundle.py)" % _checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
